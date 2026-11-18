"""Run the merge gates on one checkout and print the results as one JSON line.

    python3 check_candidate.py --bot wt/r05-a1-check --workers 8 [--breadth-ids ids.txt] [--skip-test]

Gates, cheapest first, stopping at the first failure unless --all:
  chat     replies to the 1000 chat prompts vs runs/chat_baseline.jsonl (must be 0 changed)
  breadth  correct answers on the breadth ids (the caller compares with the champion)
  test     correct answers on hidden/test.jsonl (aggregate only)

The orchestrator runs several of these at once, one per candidate patch; they share the
machine's eval slots through eval.py's lock files.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval as ev  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--breadth-ids", required=True)
    ap.add_argument("--min-breadth", type=int, default=0, help="stop early below this")
    ap.add_argument("--changes-out", default="", help="write changed chat replies here")
    args = ap.parse_args()

    out = {"bot": args.bot}
    chat = ev.load_rows(os.path.join(HERE, "splits", "chat.jsonl"))
    changed = ev.chat_changes(ev.run(args.bot, chat, args.workers),
                              os.path.join(HERE, "runs", "chat_baseline.jsonl"))
    out["chat_changed"] = len(changed)
    if changed and args.changes_out:
        with open(args.changes_out, "w") as f:
            for x in changed:
                f.write(json.dumps(x) + "\n")
    if changed:
        print(json.dumps(out))
        return

    with open(args.breadth_ids) as f:
        ids = {line.strip() for line in f if line.strip()}
    breadth = ev.load_rows(os.path.join(HERE, "splits", "train.jsonl"), ids)
    out["breadth"] = sum(r["correct"] for r in ev.run(args.bot, breadth, args.workers))
    if out["breadth"] < args.min_breadth:
        print(json.dumps(out))
        return

    test = ev.load_rows(os.path.join(HERE, "hidden", "test.jsonl"))
    out["test"] = sum(r["correct"] for r in ev.run(args.bot, test, args.workers))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
