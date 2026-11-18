"""Score a PyBot checkout on a split.

    python3 eval.py --bot ../src/pybot --split train --ids my_ids.txt
    python3 eval.py --bot ../src/pybot --split chat --save-baseline   # once, on the untouched bot
    python3 eval.py --bot ../src/pybot --split chat                   # later: what changed?

Each question is one fresh conversation (empty memory, fixed random seed), sent through
bot.runtime.turn exactly as the CLI does. The predicted answer is the LAST number in the
reply; it is correct if it equals the gold number (to 1e-6).

Splits: train and chat live in --splits-dir. test and symbolic live in --hidden-dir, which
only the orchestrator has; for those only the aggregate score is printed or saved.

For chat there is no gold answer: the report is how many replies differ from the saved
baseline (runs-dir/chat_baseline.jsonl), and which modules produced the changed replies.

Only one eval runs at a time on this machine (an flock on EVAL_LOCK): each worker holds
~260 MB, so several agents each starting a pool could eat the RAM. Others queue.
"""
import argparse
import collections
import fcntl
import json
import multiprocessing as mp
import os
import random
import re
import signal
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HIDDEN = {"test", "symbolic"}
TIMEOUT_S = 20
LOCK = os.environ.get("EVAL_LOCK", os.path.join(HERE, "runs", ".eval.lock"))

# A number: optional sign, digits with optional thousands commas, optional decimals.
# "1,000" is one number; "3, 4" is two.
NUMBER = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")

_runtime = None


def last_number(reply):
    found = NUMBER.findall(reply or "")
    if not found:
        return None
    try:
        return float(found[-1].replace(",", ""))
    except ValueError:
        return None


def _freeze_clock():
    """Make every eval see the same instant (2026-11-16 12:00 local).

    PyBot answers some messages from the clock ("what day is it", greetings by time of day),
    so without this a chat reply can change between two runs of the same code just because
    the date or hour did. PyBot reads the time only as datetime.date.today() and
    datetime.datetime.now() on the datetime module, so swapping those two classes on the
    module, before the bot is imported, freezes all of it.
    """
    import datetime as dt
    real_date, real_datetime = dt.date, dt.datetime

    class FrozenDate(real_date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 16)

    class FrozenDateTime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            moment = cls(2026, 11, 16, 12, 0, 0)
            return moment if tz is None else moment.replace(tzinfo=tz)

        @classmethod
        def today(cls):
            return cls(2026, 11, 16, 12, 0, 0)

        @classmethod
        def utcnow(cls):
            return cls(2026, 11, 16, 17, 0, 0)

    dt.date, dt.datetime = FrozenDate, FrozenDateTime


def _init(bot_dir):
    global _runtime
    _freeze_clock()
    sys.path.insert(0, os.path.abspath(bot_dir))
    from bot import runtime
    _runtime = runtime


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _one(row):
    random.seed(row["id"])  # same wording every run, whatever worker gets the item
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(TIMEOUT_S)
    start = time.perf_counter()
    try:
        result = _runtime.turn(row["question"], {})
        reply = " ".join(str(result["reply"]).split())
        module, error = result.get("module"), None
    except _Timeout:
        reply, module, error = "", None, "timeout"
    except Exception as e:  # noqa: BLE001
        reply, module, error = "", None, "%s: %s" % (type(e).__name__, e)
    finally:
        signal.alarm(0)
    pred = last_number(reply)
    gold = row.get("answer")
    correct = gold is not None and pred is not None and abs(pred - gold) < 1e-6
    return {"id": row["id"], "gold": gold, "pred": pred, "correct": correct, "module": module,
            "reply": reply, "error": error, "ms": round((time.perf_counter() - start) * 1000)}


def load_rows(path, ids=None, limit=0):
    with open(path) as f:
        rows = [json.loads(line) for line in f]
    if ids is not None:
        rows = [r for r in rows if r["id"] in ids]
    return rows[:limit] if limit else rows


SLOTS = int(os.environ.get("EVAL_SLOTS", "2"))  # evals at once on this machine; one lock file each


def _slot_paths():
    return [LOCK] + ["%s.%d" % (LOCK, k) for k in range(1, SLOTS)]


def _acquire_slot():
    """Take any free eval slot, waiting if all are busy. Returns the locked fd."""
    fds = []
    for path in _slot_paths():
        if not os.path.exists(path):
            try:
                open(path, "a").close()
            except OSError:
                continue  # a sandbox that cannot create it; the orchestrator does
        fds.append(os.open(path, os.O_RDONLY))
    if not fds:
        sys.exit("no eval lock file at %s" % LOCK)
    start = time.time()
    while True:
        for fd in fds:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            for other in fds:
                if other != fd:
                    os.close(other)
            if time.time() - start > 1:
                print("waited %.0fs for a free eval slot" % (time.time() - start), file=sys.stderr)
            return fd
        time.sleep(1)


def run(bot_dir, rows, workers):
    """Score rows on the checkout at bot_dir, holding the machine-wide eval lock."""
    fd = _acquire_slot()
    try:
        if workers > 1:
            try:
                ctx = mp.get_context("fork")
                with ctx.Pool(workers, initializer=_init, initargs=(bot_dir,),
                              maxtasksperchild=200) as pool:
                    return pool.map(_one, rows, chunksize=4)
            except (OSError, PermissionError) as e:  # e.g. a sandbox that forbids semaphores
                print("process pool unavailable (%s); running serially" % e, file=sys.stderr)
        _init(bot_dir)
        return [_one(r) for r in rows]
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def chat_changes(results, baseline_path):
    with open(baseline_path) as f:
        base = {r["id"]: r for r in map(json.loads, f)}
    return [dict(r, baseline_reply=base[r["id"]]["reply"], baseline_module=base[r["id"]]["module"])
            for r in results if r["id"] in base and r["reply"] != base[r["id"]]["reply"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True, help="path to a PyBot checkout (the dir holding bot/)")
    ap.add_argument("--split", required=True, choices=["train", "test", "symbolic", "chat"])
    ap.add_argument("--ids", help="file with one id per line: score only those")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="latest", help="name for this run's results file")
    ap.add_argument("--splits-dir", default=os.path.join(HERE, "splits"))
    ap.add_argument("--hidden-dir", default=os.path.join(HERE, "hidden"))
    ap.add_argument("--runs-dir", default=os.path.join(HERE, "runs"))
    ap.add_argument("--save-baseline", action="store_true", help="chat split: save replies as the baseline")
    args = ap.parse_args()

    folder = args.hidden_dir if args.split in HIDDEN else args.splits_dir
    path = os.path.join(folder, args.split + ".jsonl")
    if not os.path.exists(path):
        sys.exit("no %s split here" % args.split)
    ids = None
    if args.ids:
        with open(args.ids) as f:
            ids = {line.strip() for line in f if line.strip()}
    rows = load_rows(path, ids, args.limit)
    os.makedirs(args.runs_dir, exist_ok=True)

    t0 = time.time()
    results = run(args.bot, rows, args.workers)
    wall = time.time() - t0
    errors = sum(1 for r in results if r["error"])

    if args.split == "chat":
        base_path = os.path.join(args.runs_dir, "chat_baseline.jsonl")
        if args.save_baseline:
            with open(base_path, "w") as f:
                for r in results:
                    f.write(json.dumps(r) + "\n")
            print("saved chat baseline: %d replies (%.0fs)" % (len(results), wall))
            return
        changed = chat_changes(results, base_path)
        print("chat: %d/%d replies changed vs baseline, %d errors (%.0fs)"
              % (len(changed), len(results), errors, wall))
        for module, n in collections.Counter(r["module"] for r in changed).most_common():
            print("  changed via %-40s %d" % (module, n))
        out = os.path.join(args.runs_dir, "chat_%s.jsonl" % args.tag)
        with open(out, "w") as f:
            for r in changed:
                f.write(json.dumps(r) + "\n")
        print("changed replies written to", out)
        return

    n_correct = sum(r["correct"] for r in results)
    print("%s: %d/%d = %.2f%%  (%d errors/timeouts, %.0fs, %d workers)"
          % (args.split, n_correct, len(results), 100.0 * n_correct / max(1, len(results)), errors,
             wall, args.workers))
    if args.split in HIDDEN:
        return  # aggregate only: no per-item results for hidden splits
    by_module = collections.Counter(r["module"] for r in results)
    for module, n in by_module.most_common(8):
        right = sum(r["correct"] for r in results if r["module"] == module)
        print("  %-40s answered %4d, correct %4d" % (module, n, right))
    out = os.path.join(args.runs_dir, "%s_%s.jsonl" % (args.split, args.tag))
    with open(out, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print("per-item results written to", out)


if __name__ == "__main__":
    main()
