"""Hill-climb PyBot on GSM8K with rounds of Codex agents.

    python3 orchestrate.py --hours 24            # run (resumes from orch/state.json)
    touch orch/STOP                              # finish the current round, then stop

Each round:
  1. Score the champion on the breadth set plus a fresh sample of train, to learn what fails.
  2. Pick clusters of failing train problems (by the operations in their worked solutions and
     a few keywords) and give each agent one cluster: 40 target problems, in its own git
     worktree of the champion. Round 0 has a single agent that builds the math core.
  3. Run the agents in parallel with `codex exec -s workspace-write` (writes confined to the
     worktree, no network), each with a time limit.
  4. Commit each agent's work, audit it (no 8-word phrases from held-out questions in the
     patch; no commands touching held-out data), and pre-score it on target + breadth.
  5. Merge candidates one at a time, best first, onto the champion. Keep a merge only if it
     applies cleanly, changes no chat reply, does not lower breadth, and raises the test score.
  6. Every few rounds, score GSM-Symbolic (memorisation check). Delete the worktrees.

The champion lives on branch `math` in ../src/pybot. Everything is logged under orch/.
"""
import argparse
import collections
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import eval as ev  # noqa: E402

ROOT = os.path.dirname(HERE)
CHAMPION = os.path.join(ROOT, "src", "pybot")
BRANCH = "math"
ORCH = os.path.join(HERE, "orch")
WT = os.path.join(HERE, "wt")
STATE = os.path.join(ORCH, "state.json")
LOG = os.path.join(ORCH, "log.txt")
SPLITS = os.path.join(HERE, "splits")
HIDDEN = os.path.join(HERE, "hidden")
LOCK = os.path.join(HERE, "runs", ".eval.lock")
BRIEF = os.path.join(HERE, "agent_brief.md")

BOOTSTRAP = """## This is round 0: build the foundation

There is no math support yet. Besides solving your target problems, build the core that later
agents will extend, and keep it simple and documented:

- `bot/modules/word_problem.py` with `PRIORITY = 8500` and `respond(text, memory)` that returns
  a reply or None. It should only fire on messages that look like a math word problem.
- `bot/math/` with: reading numbers (digits, commas, money, percents, number words, fractions),
  exact arithmetic with `fractions.Fraction`, formatting the final answer, and a **skill
  registry**: every file in `bot/math/skills/` defines `solve(problem)` returning
  `(answer, working_text)` or None, and the module tries the skills in turn.
- A short `bot/math/README.md` saying how to add a skill, for the agents who come after you.
- Your own rules in `bot/math/skills/{skill_name}.py`.

Check that PyBot's arbiter actually lets your module's reply through on your target problems
(see the `module` field in `.mathwork/runs/*.jsonl`); the arbiter has many rules."""

EXTEND = """## The math core already exists

Read `bot/math/README.md` and the existing skills in `bot/math/skills/` first. Reuse the core;
add your rules as a new skill. If a problem of your kind is already caught by another skill
that answers it wrongly, fix that carefully without breaking what it solves."""


# ---------------------------------------------------------------- helpers

def log(msg):
    line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def git(args, cwd=None, check=True):
    p = subprocess.run(["git"] + args, cwd=cwd or CHAMPION, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), p.stderr.strip()))
    return p.stdout.strip()


def load_split(name, folder=SPLITS):
    with open(os.path.join(folder, name + ".jsonl")) as f:
        return [json.loads(line) for line in f]


def save_state(state):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, STATE)


def score(bot_dir, rows, workers):
    results = ev.run(bot_dir, rows, workers)
    return results, sum(r["correct"] for r in results)


# ---------------------------------------------------------------- clusters

STEP = re.compile(r"<<([^=>]*)=")


def cluster_of(row):
    """A coarse kind for a train problem: a topic tag plus how many calculation steps."""
    q = row["question"].lower()
    steps = STEP.findall(row["solution"])
    ops = set("".join(steps)) & set("+-*/")
    if "%" in q or "percent" in q:
        tag = "percentages (percent of, % off, % increase)"
    elif re.search(r"\b(half|third|quarter|fourth|fifth|\d+/\d+)\b", q):
        tag = "fractions of a quantity (half, a third, 2/5 of ...)"
    elif re.search(r"\b(per|each|every|an hour|a day|a week|mph|rate)\b", q) and "/" in ops:
        tag = "rates and unit rates (per hour, each, every; dividing)"
    elif re.search(r"\b(times as|twice|more than|less than|fewer than|older than|younger than)\b", q):
        tag = "comparisons (twice as many, 5 more than, 3 years older)"
    elif "$" in q or "cost" in q or "price" in q or "pay" in q:
        tag = "money: totals, change, prices"
    else:
        tag = "counting and totals (combine, remove, group)"
    n = len(steps)
    size = "1-2 steps" if n <= 2 else ("3 steps" if n == 3 else "4+ steps")
    return "%s, %s" % (tag, size)


def pick_targets(state, train, n_agents, round_no, per_batch=40, n_batches=4):
    """[(cluster, [batch, batch, ...])]: disjoint batches of unsolved problems per agent.

    Never-assigned problems come first; problems handed out before but still unsolved fill in
    once a cluster runs out of fresh ones. Every problem handed out is recorded in
    state["assigned_ids"].
    """
    breadth = set(state["breadth_ids"])
    solved = set(state["solved"])
    seen = set(state.setdefault("assigned_ids", []))
    by_cluster = collections.defaultdict(list)
    for r in train:
        if r["id"] in breadth or r["id"] in solved:
            continue
        by_cluster[cluster_of(r)].append(r["id"])
    assigned = state["assigned"]

    def priority(item):
        name, ids = item
        fresh = sum(1 for i in ids if i not in seen)
        steps_rank = 0 if "1-2" in name else (1 if "3 steps" in name else 2)
        return -((fresh + 0.25 * (len(ids) - fresh)) / (1.0 + assigned.get(name, 0))
                 / (1 + steps_rank))

    picks = []
    rng = random.Random(round_no)
    for name, ids in sorted(by_cluster.items(), key=priority)[:n_agents]:
        if len(ids) < 10:
            continue
        fresh = [i for i in ids if i not in seen]
        old = [i for i in ids if i in seen]
        rng.shuffle(fresh)
        rng.shuffle(old)
        chosen = (fresh + old)[:per_batch * n_batches]
        batches = [chosen[k:k + per_batch] for k in range(0, len(chosen), per_batch)]
        picks.append((name, batches))
        assigned[name] = assigned.get(name, 0) + 1
        seen.update(chosen)
    state["assigned_ids"] = sorted(seen)
    return picks


# ---------------------------------------------------------------- audits

WORD = re.compile(r"[a-z0-9']+")


def ngrams(text, n=8):
    words = WORD.findall(text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def build_leak_set():
    held = set()
    for split in ("test", "symbolic"):
        for r in load_split(split, HIDDEN):
            held |= ngrams(r["question"])
    common = set()
    for r in load_split("train"):
        common |= ngrams(r["question"])
    return held - common  # phrases that only occur in held-out questions


# Worktrees live at harness/wt/<name>, so "../.." from one is the harness itself. Codex
# agents look for AGENTS.md instruction files in parent folders by habit; that is allowed.
SUSPECT = re.compile(r"hidden/|(?<![a-z0-9_])test\.jsonl|symbolic\.jsonl|gsm-symbolic|grade.school.math|"
                     r"gsm8k|huggingface\.co|raw\.githubusercontent|\b(curl|wget)\b|pip3? install|"
                     r"git clone|urllib\.request|requests\.get|/proc/1/environ|RUNPOD_API_KEY|"
                     r"harness/(data|hidden|splits|runs|orch)|\.\./\.\./(?!AGENTS\.md\b)", re.I)


def commands_in(log_path):
    """Every shell command string recorded in a codex --json log."""
    found = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("command", "cmd") and isinstance(v, (str, list)):
                    found.append(v if isinstance(v, str) else " ".join(map(str, v)))
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                try:
                    walk(json.loads(line))
                except ValueError:
                    pass
    return found


def audit(diff, log_path, leak_set, own=""):
    problems = []
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    leaked = ngrams(added) & leak_set
    if leaked:
        problems.append("patch contains held-out phrases: %s" % sorted(leaked)[:3])
    commands = commands_in(log_path)
    bad = [c for c in commands if SUSPECT.search(c)]
    # All agents share one unix user on the pod, so nothing but this check keeps one out of
    # another's worktree: any command naming a worktree other than its own is rejected.
    if own:
        base = own.split("-rebase")[0]
        other = re.compile(r"/wt/(?!(%s|%s-rebase)\b)[\w-]+" % (re.escape(own), re.escape(base)))
        bad += [c for c in commands if other.search(c)]
    if bad:
        problems.append("suspicious commands: %s" % [c[:160] for c in bad[:3]])
    return problems


# ---------------------------------------------------------------- agents

def prepare_worktree(name, base, cluster, batches, state, phase, minutes):
    path = os.path.join(WT, name)
    if os.path.exists(path):
        git(["worktree", "remove", "--force", path], check=False)
    git(["branch", "-D", name], check=False)
    git(["worktree", "add", "-q", "-b", name, path, base])
    work = os.path.join(path, ".mathwork")
    os.makedirs(os.path.join(work, "runs"))
    with open(os.path.join(HERE, "eval.py")) as f:
        code = f.read().replace(
            'LOCK = os.environ.get("EVAL_LOCK", os.path.join(HERE, "runs", ".eval.lock"))',
            "LOCK = %r" % LOCK).replace(
            'SLOTS = int(os.environ.get("EVAL_SLOTS", "2"))', "SLOTS = %d" % ev.SLOTS).replace(
            'ap.add_argument("--workers", type=int, default=8)',
            'ap.add_argument("--workers", type=int, default=5)')
    with open(os.path.join(work, "eval.py"), "w") as f:
        f.write(code)
    for split in ("train", "chat"):
        shutil.copy(os.path.join(SPLITS, split + ".jsonl"), work)
    shutil.copy(os.path.join(HERE, "runs", "chat_baseline.jsonl"), os.path.join(work, "runs"))
    for k, batch in enumerate(batches, 1):
        with open(os.path.join(work, "batch_%d.txt" % k), "w") as f:
            f.write("\n".join(batch) + "\n")
    with open(os.path.join(work, "all_targets.txt"), "w") as f:
        f.write("\n".join(i for b in batches for i in b) + "\n")
    with open(os.path.join(work, "breadth_ids.txt"), "w") as f:
        f.write("\n".join(state["breadth_ids"]) + "\n")
    skill = re.sub(r"[^a-z0-9]+", "_", cluster.split("(")[0].lower()).strip("_") + "_" + name.replace("-", "_")
    with open(BRIEF) as f:
        brief = f.read()
    section = (BOOTSTRAP if phase == "bootstrap" else EXTEND).replace("{skill_name}", skill)
    brief = (brief.replace("{phase_section}", section).replace("{cluster_desc}", cluster)
             .replace("{n_target}", str(len(batches[0]))).replace("{n_batches}", str(len(batches)))
             .replace("{skill_name}", skill)
             .replace("{breadth_now}", "%d/400" % state["breadth"]).replace("{minutes}", str(minutes)))
    with open(os.path.join(work, "TASK.md"), "w") as f:
        f.write(brief)
    return path


_next_user = 0


def launch(path, out_dir, name, model, effort):
    # --ignore-user-config drops the user's MCP servers; the --disable flags drop ChatGPT app
    # connectors (Gmail etc.), plugins, browser and computer use. Network is off in the sandbox.
    cmd = ["codex", "exec", "--ignore-user-config", "-m", model,
           "-c", 'model_reasoning_effort="%s"' % effort, "-c", 'web_search="disabled"',
           "-s", "workspace-write", "-C", path, "--json", "--skip-git-repo-check",
           "-o", os.path.join(path, ".mathwork", "final.txt")]
    for feature in ("apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
                    "computer_use", "in_app_browser", "image_generation", "hooks", "tool_suggest",
                    "skill_mcp_dependency_install"):
        cmd += ["--disable", feature]
    cmd.append("Read .mathwork/TASK.md and carry out the task it describes.")
    if os.environ.get("AGENT_SANDBOX") == "unix-user":
        # Approved by the user for the RunPod pod, where Codex's own sandbox (bubblewrap) cannot
        # start in a container. The agent runs without it, as its own unprivileged user: unix
        # permissions keep it out of hidden data, logs, the champion repo and other agents'
        # worktrees, and its shell commands get a dead proxy so downloads fail. Codex's own
        # connection to OpenAI is unaffected. The audit rejects any network command anyway.
        i = cmd.index("-s")
        cmd[i:i + 2] = ["--dangerously-bypass-approvals-and-sandbox"]
        dead = "http://127.0.0.1:9"
        cmd[2:2] = ["-c", "shell_environment_policy.set={%s}" % ",".join(
            '%s="%s"' % (k, dead) for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                                            "http_proxy", "https_proxy", "all_proxy"))]
    users = [u for u in os.environ.get("AGENT_USERS", "").split(",") if u]
    if users:
        # One unix user per running agent (round-robin), so agents cannot touch each other's
        # worktrees. They share one Codex login through a group-readable CODEX_HOME.
        global _next_user
        user = users[_next_user % len(users)]
        _next_user += 1
        subprocess.run(["chown", "-R", "%s:%s" % (user, user), path], check=True)
        os.chmod(path, 0o700)
        cmd = ["sudo", "-u", user, "-H", "--", "env",
               "CODEX_HOME=%s" % os.environ.get("AGENT_CODEX_HOME", "/home/agent/.codex")] + cmd
    out = open(os.path.join(out_dir, name + ".jsonl"), "w")
    err = open(os.path.join(out_dir, name + ".stderr.txt"), "w")
    return subprocess.Popen(cmd, cwd=path, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                            start_new_session=True)


def save_final(path, out_dir, name):
    """Copy an agent's final summary out of its worktree into the round's log folder."""
    src = os.path.join(path, ".mathwork", "final.txt")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(out_dir, name + ".final.txt"))


def wait_all(procs, minutes, deadline=None):
    deadline = deadline or time.time() + minutes * 60
    while any(p.poll() is None for p in procs.values()):
        if time.time() > deadline:
            for name, p in procs.items():
                if p.poll() is None:
                    log("  %s hit the %d-minute limit; stopping it" % (name, minutes))
                    try:
                        os.killpg(p.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            time.sleep(20)
            for p in procs.values():
                if p.poll() is None:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            break
        time.sleep(15)


REBASE_TASK = """# Your task: carry another agent's patch onto the current PyBot

PyBot (this repository) is a rules-only chatbot that is being taught to solve math word
problems. Another agent wrote a patch for this kind of problem: **{cluster}**. Since then,
other patches were merged, and this patch no longer applies cleanly. Your job is to carry it
over, not to write new features.

The patch has been applied as far as git could. These files contain conflict markers
(`<<<<<<<`, `=======`, `>>>>>>>`), also listed in `.mathwork/conflicts.txt`:

{conflicts}

The full original patch is in `.mathwork/patch.diff`. In each conflict, the first side
(between `<<<<<<<` and `=======`) is the current PyBot, which has already been tested and
accepted: **keep everything it does**. The second side is the incoming patch: add what it needs
on top. Usually both sides added different things to the same spot, and the answer is to keep
both. Remove every conflict marker.

Then check, from the repository root (runs may wait on a shared lock; that is normal):

    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/all_targets.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag all
    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/breadth_ids.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag breadth
    python3 .mathwork/eval.py --bot . --split chat --splits-dir .mathwork --runs-dir .mathwork/runs

Targets: the original patch solved **{target}/{n_target}** of `all_targets.txt`; get as close
to that as you can. Breadth must be at least **{breadth}/400**. Chat: **0** changed replies.

Everything you need is in this file and this repository: do not read, list or search anything
outside it (no parent directories, no `AGENTS.md` elsewhere).

Rules: Python 3.8 standard library only; stay in this repository; do not edit `.mathwork/`;
do not run git commands; no new rules beyond what the patch needs to work here. You have about
{minutes} minutes. Reply with a short summary: what conflicted, how you resolved it, and the
three check results.
"""

GENERALIZE_TASK = """# Your task: make PyBot's math rules more general

PyBot (this repository) is a chatbot written in plain Python: no weights, no ML, just rules.
Over the past rounds, many agents taught it to solve grade-school math word problems (GSM8K
style): the shared core is in `bot/math/` (read `bot/math/README.md` first), and each agent
added a skill file in `bot/math/skills/`. Those files were written quickly, one round at a
time, and they contain problem-specific code: hardcoded words and phrasings, narrow regexes,
special cases, and helpers copied between files.

**This round adds no new problem types. Your job is to make existing code more general**, so
it keeps solving what it solves today and is more likely to solve problems nobody has seen.

**Your area: {area}**

You may edit only these files (and create new ones matching these patterns):

{files}

Leave every other file alone: five other agents are working on the other areas in parallel,
and a patch that touches another area is dropped.

## What to do

- Replace hardcoded lists of specific words, names, objects or phrasings with general logic
  (e.g. recognise any noun after a number, not a list of nouns; parse the sentence structure,
  not one wording of it).
- Merge near-duplicate rules and copied helpers into one general version. In a skills area,
  you may put shared helpers in a new module whose name starts with `_` (the registry ignores
  those), for example `bot/math/skills/_{prefix}_common.py`.
- Remove dead code and special cases that the general logic now covers.
- Keep the guard rails: a skill must still return None when it does not fully understand a
  problem. More general must not mean more trigger-happy: a wrong answer, or answering an
  ordinary chat message, costs more than returning None.

## How you are checked

- `.mathwork/all_targets.txt`: **{n_keep}** training problems PyBot solves today. Keep as many
  solved as you can; a few may be lost to a genuinely more general rule, but not many.
- `.mathwork/breadth_ids.txt`: 400 random training problems, **{breadth_now}** solved today;
  must not go down. Gaining some here is the sign your rules generalise.
- `.mathwork/chat.jsonl`: 1000 chat messages; **not one** reply may change.
- Your area's tests in `tests/` must still pass (update them if you merge files; keep the cases).

Commands, from the repository root (they share a machine-wide lock; waiting is normal):

    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/all_targets.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag keep
    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/breadth_ids.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag breadth
    python3 .mathwork/eval.py --bot . --split chat --splits-dir .mathwork --runs-dir .mathwork/runs

Work in small steps and re-check after each one, so you always have a working version.

The orchestrator keeps your patch only if PyBot's score on a **held-out test set** does not go
down, breadth does not go down, and no chat reply changes. You never see that test set and must
not look for it.

## Rules

1. General rules only: never match a specific question's wording, names, objects or numbers.
2. Python 3.8, standard library only. No network.
3. Everything you need is in this file and this repository. **Do not read, list or search
   anything outside this repository** (no parent directories, no `AGENTS.md` elsewhere, no
   home directory). Do not edit `.mathwork/`, and do not run git commands.
4. Every module must import cleanly and `turn()` must never raise.

You have about {minutes} minutes. When done, reply with a short summary: what you generalised,
lines of code before and after in your area, and keep / breadth / chat before and after.
"""

# Areas of the generalisation round: (label, description, file patterns it may touch).
GENERALIZE_AREAS = [
    ("comparisons", "the comparison skills (twice as many, 5 more than, older/younger)",
     ["bot/math/skills/comparisons_*.py", "bot/math/skills/_comparisons*.py",
      "tests/test_comparisons*.py"]),
    ("counting", "the counting-and-totals skills (combine, remove, group)",
     ["bot/math/skills/counting_and_totals_*.py", "bot/math/skills/_counting*.py",
      "tests/test_counting_and_totals*.py"]),
    ("money", "the money skills (totals, change, prices)",
     ["bot/math/skills/money_*.py", "bot/math/skills/_money*.py",
      "tests/test_money*.py"]),
    ("rates", "the rate and unit-rate skills (per hour, each, every)",
     ["bot/math/skills/rates_and_unit_rates_*.py", "bot/math/skills/_rates*.py",
      "tests/test_rates*.py", "tests/test_rate_word_problem.py"]),
    ("fractions", "the fraction-of-a-quantity and percentage skills",
     ["bot/math/skills/fractions_*.py", "bot/math/skills/percentages_*.py",
      "bot/math/skills/_fractions*.py", "bot/math/skills/_percent*.py",
      "tests/test_fractions*.py", "tests/test_percentages*.py"]),
    ("core", "the shared core: number reading, problem parsing, the skill registry and the "
             "word_problem module (not the skill files)",
     ["bot/math/__init__.py", "bot/math/numbers.py", "bot/math/problem.py",
      "bot/math/README.md", "bot/math/_*.py", "bot/modules/word_problem.py",
      "tests/test_word_problem.py", "tests/test_math_core*.py"]),
]


def start_generalize_round(state, args, train, r):
    """A round with no new targets: each agent makes one area of the math code more general.

    Each agent gets a disjoint set of files, a keep set (training problems the champion solves
    now) instead of targets, and the same breadth and chat checks. Its patch is merged with the
    usual gates except that test only has to stay level (see finish_round's allow_equal).
    """
    import fnmatch
    out_dir = os.path.join(ORCH, "round-%02dg" % r)
    os.makedirs(out_dir, exist_ok=True)
    by_id = {x["id"]: x for x in train}
    pool = sorted(set(state["solved"]) - set(state["breadth_ids"]))
    sample = random.Random(5000 + r).sample(pool, min(700, len(pool)))
    res, _ = score(CHAMPION, [by_id[i] for i in sample], args.workers)
    keep = sorted(x["id"] for x in res if x["correct"])
    log("round %dg: generalisation round; keep set %d training problems the champion solves"
        % (r, len(keep)))
    files = git(["ls-files", "bot", "tests"]).split()
    base = git(["rev-parse", "HEAD"])
    agents = {}
    for i, (label, area, patterns) in enumerate(GENERALIZE_AREAS):
        name = "r%02dg-a%d" % (r, i + 1)
        path = prepare_worktree(name, base, "generalise " + label, [keep], state, "extend",
                                args.agent_minutes)
        current = [f for f in files if any(fnmatch.fnmatch(f, p) for p in patterns)]
        lines = sum(1 for f in current if f.endswith(".py")
                    for _ in open(os.path.join(path, f), errors="replace"))
        listing = "\n".join("- `%s`" % p for p in patterns)
        listing += "\n\nToday that is %d files, %d lines of Python." % (len(current), lines)
        with open(os.path.join(path, ".mathwork", "TASK.md"), "w") as f:
            f.write(GENERALIZE_TASK.format(area=area, files=listing, prefix=label,
                                           n_keep=len(keep), breadth_now="%d/400" % state["breadth"],
                                           minutes=args.agent_minutes))
        agents[name] = {"path": path, "cluster": "generalise " + label, "ids": keep, "batches": 1,
                        "patterns": patterns, "lines_before": lines}
        log("round %dg: %s on %s (%d files, %d lines)" % (r, name, label, len(current), lines))
    procs = {n: launch(a["path"], out_dir, n, args.model, args.effort) for n, a in agents.items()}
    return {"r": r, "out_dir": out_dir, "agents": agents, "procs": procs, "bootstrap": False,
            "minutes": args.agent_minutes, "deadline": time.time() + (args.agent_minutes + 5) * 60,
            "base": base, "generalize": True, "n_keep": len(keep)}


def filter_generalize(handle, candidates):
    """Drop generalisation patches that touch files outside their area or lose many keeps."""
    import fnmatch
    kept = []
    for n in candidates:
        a = handle["agents"][n]
        touched = git(["show", "--name-only", "--format=", a["commit"]]).split()
        outside = [f for f in touched if not any(fnmatch.fnmatch(f, p) for p in a["patterns"])]
        stat = git(["show", "--shortstat", "--format=", a["commit"]]).strip()
        a["shortstat"] = stat
        if outside:
            log("  %s: touches files outside its area (%s); dropped" % (n, ", ".join(outside[:5])))
            continue
        if a["target_after"] < handle["n_keep"] * 0.97:
            log("  %s: keeps only %d/%d; dropped" % (n, a["target_after"], handle["n_keep"]))
            continue
        log("  %s: %s" % (n, stat))
        kept.append(n)
    return kept


MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>)( |$)", re.M)


def rebase_patch(n, a, state, args, out_dir, leak_set, extra_worktrees):
    """Have a short Codex session re-apply agent n's patch on the current champion.

    Returns the commit to cherry-pick, or None if the session could not produce a clean,
    audited patch.
    """
    name = n + "-rebase"
    ids = a["ids"]
    batches = [ids[k:k + 40] for k in range(0, len(ids), 40)]
    path = prepare_worktree(name, git(["rev-parse", "HEAD"]), a["cluster"], batches, state,
                            "extend", args.rebase_minutes)
    extra_worktrees.append((name, path))
    subprocess.run(["git", "cherry-pick", "--no-commit", a["commit"]], cwd=path,
                   capture_output=True, text=True)
    conflicted = git(["diff", "--name-only", "--diff-filter=U"], cwd=path, check=False).split()
    work = os.path.join(path, ".mathwork")
    shutil.copy(os.path.join(out_dir, n + ".diff"), os.path.join(work, "patch.diff"))
    with open(os.path.join(work, "conflicts.txt"), "w") as f:
        f.write("\n".join(conflicted) + "\n")
    with open(os.path.join(work, "TASK.md"), "w") as f:
        f.write(REBASE_TASK.format(
            cluster=a["cluster"], conflicts="\n".join("- `%s`" % c for c in conflicted) or "- (none)",
            target=a["target_after"], n_target=len(ids), breadth=state["breadth"],
            minutes=args.rebase_minutes))

    if conflicted:
        proc = launch(path, out_dir, name, args.model, args.effort)
        wait_all({name: proc}, args.rebase_minutes + 3)
        save_final(path, out_dir, name)

    for rel in conflicted:
        full = os.path.join(path, rel)
        if os.path.exists(full):
            with open(full, errors="replace") as f:
                if MARKER.search(f.read()):
                    log("  %s: conflict markers left in %s; dropped" % (name, rel))
                    return None
    git(["add", "-A"], cwd=path)
    if not git(["diff", "--cached", "--name-only"], cwd=path):
        log("  %s: nothing to commit; dropped" % name)
        return None
    git(["commit", "-q", "-m", "%s (rebased): %s" % (n, a["cluster"])], cwd=path)
    commit = git(["rev-parse", "HEAD"], cwd=path)
    diff = git(["show", "--format=", commit], cwd=path)
    with open(os.path.join(out_dir, name + ".diff"), "w") as f:
        f.write(diff)
    problems = audit(diff, os.path.join(out_dir, name + ".jsonl"), leak_set, own=name)
    if problems:
        log("  %s: REJECTED by audit: %s" % (name, "; ".join(problems)))
        return None
    return commit


# ---------------------------------------------------------------- main loop

def setup(args):
    os.makedirs(ORCH, exist_ok=True)
    os.makedirs(WT, exist_ok=True)
    for k in range(ev.SLOTS):
        open(LOCK if k == 0 else "%s.%d" % (LOCK, k), "a").close()
    branches = git(["branch", "--list", BRANCH])
    if not branches:
        git(["checkout", "-q", "-b", BRANCH])
    elif git(["rev-parse", "--abbrev-ref", "HEAD"]) != BRANCH:
        git(["checkout", "-q", BRANCH])
    exclude = os.path.join(git(["rev-parse", "--git-common-dir"]), "info", "exclude")
    exclude = exclude if os.path.isabs(exclude) else os.path.join(CHAMPION, exclude)
    os.makedirs(os.path.dirname(exclude), exist_ok=True)
    with open(exclude, "a+") as f:
        f.seek(0)
        if ".mathwork/" not in f.read():
            f.write("\n.mathwork/\n__pycache__/\n")
    git(["config", "user.name", "pybot-math-orchestrator"])
    git(["config", "user.email", "orchestrator@localhost"])

    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    train = load_split("train")
    breadth_ids = sorted(random.Random(1).sample([r["id"] for r in train], 400))
    state = {"round": 0, "champion": git(["rev-parse", "HEAD"]), "breadth_ids": breadth_ids,
             "solved": [], "assigned": {}, "history": [], "started": time.time()}
    log("scoring the starting champion")
    _, state["test"] = score(CHAMPION, load_split("test", HIDDEN), args.workers)
    by_id = {r["id"]: r for r in train}
    res, state["breadth"] = score(CHAMPION, [by_id[i] for i in breadth_ids], args.workers)
    _, state["symbolic"] = score(CHAMPION, load_split("symbolic", HIDDEN), args.workers)
    log("start: test %d/1319, breadth %d/400, symbolic %d/5000"
        % (state["test"], state["breadth"], state["symbolic"]))
    save_state(state)
    return state


def load_redo_picks(folder):
    """[(cluster, batches)] saved from an earlier run of a round (clusters.txt + aN/batch_k.txt)."""
    picks = []
    with open(os.path.join(folder, "clusters.txt")) as f:
        for line in f:
            m = re.match(r"r\d+-a(\d+) on '([^']+)'", line.strip())
            if not m:
                continue
            k, cluster = m.group(1), m.group(2)
            batches = []
            for j in range(1, 10):
                path = os.path.join(folder, "a" + k, "batch_%d.txt" % j)
                if not os.path.exists(path):
                    break
                with open(path) as b:
                    batches.append([x.strip() for x in b if x.strip()])
            picks.append((cluster, batches))
    return picks


def resume_round(state, args, train, r, names):
    """Rebuild a round whose agents finished but whose merges were interrupted.

    The agents' audited commits were tagged keep/redo-rNN-aK; the champion goes back to the
    state's champion, the candidates are re-scored (no Codex) and handed to finish_round.
    """
    out_dir = os.path.join(ORCH, "round-%02d" % r)
    git(["reset", "-q", "--hard", state["champion"]])
    by_id = {x["id"]: x for x in train}
    breadth_rows = [by_id[i] for i in state["breadth_ids"]]
    agents, candidates = {}, []
    for i, (cluster, batches) in enumerate(load_redo_picks(args.redo_dir)):
        n = "r%02d-a%d" % (r, i + 1)
        if n not in names:
            continue
        commit = git(["rev-parse", "keep/redo-%s^{commit}" % n])
        path = os.path.join(WT, n)
        if os.path.exists(path):
            git(["worktree", "remove", "--force", path], check=False)
        git(["worktree", "add", "-q", "--detach", path, commit])
        ids = [x for b in batches for x in b]
        res, after = score(path, [by_id[x] for x in ids], args.workers)
        _, br = score(path, breadth_rows, args.workers)
        agents[n] = {"path": path, "cluster": cluster, "ids": ids, "batches": len(batches),
                     "exit": 0, "commit": commit, "target_after": after, "breadth": br,
                     "solved_ids": [x["id"] for x in res if x["correct"]]}
        log("  resumed %s at %s: target %d/%d, breadth %d/400"
            % (n, commit[:7], after, len(ids), br))
        if after:
            candidates.append(n)
    return {"r": r, "out_dir": out_dir, "agents": agents, "procs": {}, "bootstrap": False,
            "candidates": candidates}


def start_round(state, args, train, r):
    """Steps 1-3: learn what the champion fails, pick clusters, launch the agents.

    Returns a handle for collect_round. The agents keep running in the background.
    """
    out_dir = os.path.join(ORCH, "round-%02d" % r)
    os.makedirs(out_dir, exist_ok=True)
    by_id = {x["id"]: x for x in train}
    breadth_rows = [by_id[i] for i in state["breadth_ids"]]

    # 1. What does the champion fail? Breadth plus a fresh train sample.
    pool = [x for x in train if x["id"] not in set(state["breadth_ids"])]
    sample = random.Random(1000 + r).sample(pool, args.sample)
    res, _ = score(CHAMPION, breadth_rows + sample, args.workers)
    solved = set(state["solved"])
    for x in res:
        if x["correct"]:
            solved.add(x["id"])
        else:
            solved.discard(x["id"])
    state["solved"] = sorted(solved)

    # 2. Clusters and worktrees, from the champion as it is right now.
    bootstrap = not os.path.exists(os.path.join(CHAMPION, "bot", "math"))
    n_agents = 1 if bootstrap else args.agents
    if getattr(args, "redo_dir", "") and r == args.redo_round:
        picks = load_redo_picks(args.redo_dir)
        log("round %d: redo with the saved clusters and batches from %s" % (r, args.redo_dir))
    else:
        picks = pick_targets(state, train, n_agents, r)
    base = git(["rev-parse", "HEAD"])
    agents = {}
    for i, (cluster, batches) in enumerate(picks):
        name = "r%02d-a%d" % (r, i + 1)
        path = prepare_worktree(name, base, cluster, batches, state,
                                "bootstrap" if bootstrap else "extend", args.agent_minutes)
        ids = [x for b in batches for x in b]
        agents[name] = {"path": path, "cluster": cluster, "ids": ids, "batches": len(batches)}
        log("round %d: %s on '%s' (%d batches, %d problems)"
            % (r, name, cluster, len(batches), len(ids)))

    # 3. Launch them.
    minutes = args.agent_minutes * (2 if bootstrap else 1)
    procs = {n: launch(a["path"], out_dir, n, args.model, args.effort) for n, a in agents.items()}
    return {"r": r, "out_dir": out_dir, "agents": agents, "procs": procs, "bootstrap": bootstrap,
            "minutes": minutes, "deadline": time.time() + (minutes + 5) * 60, "base": base}


def collect_round(handle, state, args, leak_set, train):
    """Step 4: wait for the round's agents, then commit, audit and pre-score their work."""
    agents, out_dir = handle["agents"], handle["out_dir"]
    by_id = {x["id"]: x for x in train}
    breadth_rows = [by_id[i] for i in state["breadth_ids"]]
    wait_all(handle["procs"], handle["minutes"] + 5, handle["deadline"])
    for n, p in handle["procs"].items():
        agents[n]["exit"] = p.returncode
        save_final(agents[n]["path"], out_dir, n)

    candidates = []
    for n, a in agents.items():
        path = a["path"]
        git(["add", "-A"], cwd=path)
        if not git(["status", "--porcelain"], cwd=path):
            log("  %s: no changes (exit %s)" % (n, a["exit"]))
            continue
        git(["commit", "-q", "-m", "%s: %s" % (n, a["cluster"])], cwd=path)
        a["commit"] = git(["rev-parse", "HEAD"], cwd=path)
        diff = git(["show", "--format=", a["commit"]], cwd=path)
        with open(os.path.join(out_dir, n + ".diff"), "w") as f:
            f.write(diff + "\n")
        problems = audit(diff, os.path.join(out_dir, n + ".jsonl"), leak_set, own=n)
        if problems:
            log("  %s: REJECTED by audit: %s" % (n, "; ".join(problems)))
            a["audit"] = problems
            continue
        target_rows = [by_id[i] for i in a["ids"]]
        res, after = score(path, target_rows, args.workers)
        _, br = score(path, breadth_rows, args.workers)
        a.update(target_after=after, breadth=br, solved_ids=[x["id"] for x in res if x["correct"]])
        log("  %s: target %d/%d, breadth %d/400 (champion %d)"
            % (n, after, len(target_rows), br, state["breadth"]))
        if after == 0:
            continue
        candidates.append(n)
    return candidates


def merge_sequential(state, args, agents, candidates, out_dir, leak_set, test_rows, chat_rows,
                     breadth_rows, extra_worktrees, allow_equal=False):
    """Merge candidates one at a time onto the champion, each through every gate."""
    accepted = []
    for n in candidates:
        head = git(["rev-parse", "HEAD"])
        p = subprocess.run(["git", "cherry-pick", agents[n].get("merge_commit", agents[n]["commit"])],
                           cwd=CHAMPION, capture_output=True, text=True)
        if p.returncode != 0:
            git(["cherry-pick", "--abort"], check=False)
            git(["reset", "-q", "--hard", head])
            log("  %s: conflicts with this round's earlier merges; asking an agent to rebase it" % n)
            rebased = rebase_patch(n, agents[n], state, args, out_dir, leak_set, extra_worktrees)
            if not rebased:
                continue
            p = subprocess.run(["git", "cherry-pick", rebased], cwd=CHAMPION,
                               capture_output=True, text=True)
            if p.returncode != 0:
                git(["cherry-pick", "--abort"], check=False)
                git(["reset", "-q", "--hard", head])
                log("  %s: rebased patch still does not apply; dropped" % n)
                continue
            log("  %s: rebased patch applies; checking it" % n)
        chat_res = ev.run(CHAMPION, chat_rows, args.workers)
        changed = ev.chat_changes(chat_res, os.path.join(HERE, "runs", "chat_baseline.jsonl"))
        if changed:
            with open(os.path.join(out_dir, n + ".chat_changes.jsonl"), "w") as f:
                for x in changed:
                    f.write(json.dumps(x) + "\n")
            git(["reset", "-q", "--hard", head])
            log("  %s: changed %d chat replies; reverted" % (n, len(changed)))
            continue
        _, br = score(CHAMPION, breadth_rows, args.workers)
        if br < state["breadth"]:
            git(["reset", "-q", "--hard", head])
            log("  %s: breadth fell to %d/400 once merged; reverted" % (n, br))
            continue
        _, t = score(CHAMPION, test_rows, args.workers)
        if t < state["test"] or (t == state["test"] and not allow_equal):
            git(["reset", "-q", "--hard", head])
            log("  %s: test %d/1319, not above %d; reverted" % (n, t, state["test"]))
            continue
        log("  %s: ACCEPTED. test %d -> %d/1319, breadth %d -> %d/400"
            % (n, state["test"], t, state["breadth"], br))
        state.update(test=t, breadth=br, champion=git(["rev-parse", "HEAD"]))
        # Its targets that passed in its own worktree: don't hand them out again. (The next
        # round's champion sample re-checks a slice of these, in case a later merge broke one.)
        state["solved"] = sorted(set(state["solved"]) | set(agents[n]["solved_ids"]))
        accepted.append(n)
    return accepted


def _pick(cwd, commit):
    """Cherry-pick commit onto cwd's HEAD. True if it applied; on conflict, undo and False."""
    head = git(["rev-parse", "HEAD"], cwd=cwd)
    p = subprocess.run(["git", "cherry-pick", commit], cwd=cwd, capture_output=True, text=True)
    if p.returncode == 0:
        return True
    git(["cherry-pick", "--abort"], cwd=cwd, check=False)
    git(["reset", "-q", "--hard", head], cwd=cwd)
    return False


def _check(bot, args, out_dir, tag, min_breadth):
    """Start check_candidate.py on a checkout; returns the Popen (stdout = one JSON line)."""
    ids = os.path.join(out_dir, "breadth_ids.txt")
    return subprocess.Popen(
        [sys.executable, os.path.join(HERE, "check_candidate.py"), "--bot", bot,
         "--workers", str(args.workers), "--breadth-ids", ids, "--min-breadth", str(min_breadth),
         "--changes-out", os.path.join(out_dir, tag + ".chat_changes.jsonl")],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)


def _result(proc):
    out, _ = proc.communicate()
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"error": "check failed"}


def merge_parallel(state, args, agents, candidates, out_dir, leak_set, test_rows, chat_rows,
                   breadth_rows, extra_worktrees, allow_equal=False):
    """Check every candidate on its own copy of the champion at once, then confirm them together.

    A. Each candidate is applied to its own worktree of the champion (rebased by an agent if it
       conflicts) and all gates run on all of them in parallel; the eval slots bound the load.
    B. The ones that pass alone are applied together onto the champion, best test first.
    C. One confirmation check on the combination. It is kept if chat is unchanged, breadth
       does not fall, and test is at least the best single result. Otherwise the champion is
       reset and the passing candidates are merged one at a time as before.
    """
    base = git(["rev-parse", "HEAD"])
    with open(os.path.join(out_dir, "breadth_ids.txt"), "w") as f:
        f.write("\n".join(state["breadth_ids"]) + "\n")

    # A. Individual checks.
    procs = {}
    for n in candidates:
        a = agents[n]
        name = n + "-check"
        path = os.path.join(WT, name)
        if os.path.exists(path):
            git(["worktree", "remove", "--force", path], check=False)
        git(["worktree", "add", "-q", "--detach", path, base])
        extra_worktrees.append((name, path))
        a["merge_commit"] = a["commit"]
        if not _pick(path, a["commit"]):
            log("  %s: conflicts with the champion; asking an agent to rebase it" % n)
            rebased = rebase_patch(n, a, state, args, out_dir, leak_set, extra_worktrees)
            if not rebased or not _pick(path, rebased):
                log("  %s: could not be rebased; dropped" % n)
                continue
            a["merge_commit"] = rebased
        a["checked_commit"] = a["merge_commit"]
        procs[n] = _check(path, args, out_dir, n, state["breadth"])
    log("  checking %d candidates in parallel: %s" % (len(procs), ", ".join(procs)))
    passing = []
    for n, proc in procs.items():
        res = _result(proc)
        a = agents[n]
        a["check"] = res
        if "error" in res:
            log("  %s: check failed to run; dropped" % n)
        elif res.get("chat_changed"):
            log("  %s: changed %d chat replies; dropped" % (n, res["chat_changed"]))
        elif res.get("breadth", -1) < state["breadth"]:
            log("  %s: breadth %d/400 below %d; dropped" % (n, res.get("breadth", -1), state["breadth"]))
        elif res.get("test", -1) < state["test"] or (res.get("test") == state["test"]
                                                      and not allow_equal):
            log("  %s: test %d/1319, not above %d; dropped" % (n, res.get("test", -1), state["test"]))
        else:
            log("  %s: passes alone: test %d -> %d, breadth %d -> %d"
                % (n, state["test"], res["test"], state["breadth"], res["breadth"]))
            passing.append(n)
    if not passing:
        return []

    # B. Combine, best single test first.
    passing.sort(key=lambda n: -agents[n]["check"]["test"])
    combined = []
    for n in passing:
        if _pick(CHAMPION, agents[n]["merge_commit"]):
            combined.append(n)
            continue
        log("  %s: conflicts with the other passing patches; asking an agent to rebase it" % n)
        rebased = rebase_patch(n, agents[n], state, args, out_dir, leak_set, extra_worktrees)
        if rebased and _pick(CHAMPION, rebased):
            agents[n]["merge_commit"] = rebased
            combined.append(n)
        else:
            log("  %s: left out of the combination" % n)
    if not combined:
        return []

    def accept(names, test, breadth):
        log("  ACCEPTED %s. test %d -> %d/1319, breadth %d -> %d/400"
            % (", ".join(names), state["test"], test, state["breadth"], breadth))
        state.update(test=test, breadth=breadth, champion=git(["rev-parse", "HEAD"]))
        for n in names:
            state["solved"] = sorted(set(state["solved"]) | set(agents[n]["solved_ids"]))
        return names

    first = agents[combined[0]]
    if len(combined) == 1 and first["merge_commit"] == first.get("checked_commit", first["merge_commit"]):
        # The champion is now exactly what was checked in A.
        return accept(combined, first["check"]["test"], first["check"]["breadth"])

    # C. One confirmation check on the combination.
    best = max(agents[n]["check"]["test"] for n in combined)
    res = _result(_check(CHAMPION, args, out_dir, "combined", state["breadth"]))
    log("  combination of %s: %s" % (", ".join(combined), res))
    if (not res.get("chat_changed") and res.get("breadth", -1) >= state["breadth"]
            and res.get("test", -1) >= best):
        return accept(combined, res["test"], res["breadth"])

    log("  the combination does worse than its best part; merging the passing patches one at a time")
    git(["reset", "-q", "--hard", base])
    return merge_sequential(state, args, agents, passing, out_dir, leak_set, test_rows, chat_rows,
                            breadth_rows, extra_worktrees, allow_equal)


def finish_round(state, args, agents, candidates, out_dir, leak_set, test_rows, chat_rows,
                 breadth_rows, r, bootstrap, generalize=False):
    """Steps 5-6: merge candidates through the gates, then bookkeeping."""
    # 5. Merge, best first: checked in parallel then confirmed together, or one at a time.
    candidates.sort(key=lambda n: (-agents[n]["target_after"], -agents[n]["breadth"]))
    extra_worktrees = []
    if getattr(args, "parallel_merge", False) and len(candidates) > 1:
        accepted = merge_parallel(state, args, agents, candidates, out_dir, leak_set, test_rows,
                                  chat_rows, breadth_rows, extra_worktrees, generalize)
    else:
        accepted = merge_sequential(state, args, agents, candidates, out_dir, leak_set, test_rows,
                                    chat_rows, breadth_rows, extra_worktrees, generalize)

    # 6. Memorisation check, bookkeeping, cleanup.
    if accepted and (r % args.symbolic_every == 0 or bootstrap or generalize):
        _, state["symbolic"] = score(CHAMPION, load_split("symbolic", HIDDEN), args.workers)
        log("  symbolic %d/5000 = %.1f%%  (test %.1f%%)"
            % (state["symbolic"], state["symbolic"] / 50.0, state["test"] / 13.19))
    label = "%dg" % r if generalize else r
    state["history"].append({
        "round": label, "generalize": generalize, "time": time.time(), "accepted": accepted, "test": state["test"],
        "breadth": state["breadth"], "symbolic": state.get("symbolic"),
        "agents": {n: {k: v for k, v in a.items() if k not in ("ids", "path", "solved_ids")}
                   for n, a in agents.items()}})
    with open(os.path.join(ORCH, "progress.tsv"), "a") as f:
        f.write("%s\t%s\t%d\t%d\t%s\t%s\n" % (label, time.strftime("%H:%M"), state["test"],
                                              state["breadth"], state.get("symbolic"), ",".join(accepted)))
    for n, a in agents.items():
        git(["worktree", "remove", "--force", a["path"]], check=False)
        git(["branch", "-D", n], check=False)
    for name, path in extra_worktrees:
        git(["worktree", "remove", "--force", path], check=False)
        git(["branch", "-D", name], check=False)
    git(["worktree", "prune"], check=False)
    if not generalize:
        state["round"] = r + 1
    save_state(state)
    log("round %s done: accepted %s; test %d/1319 = %.1f%%"
        % (label, accepted or "nothing", state["test"], state["test"] / 13.19))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--until", default="", help='stop time "YYYY-MM-DD HH:MM" (overrides --hours)')
    ap.add_argument("--max-rounds", type=int, default=1000)
    ap.add_argument("--agents", type=int, default=6)
    ap.add_argument("--agent-minutes", type=int, default=45)
    ap.add_argument("--sample", type=int, default=600, help="train problems scored per round")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--symbolic-every", type=int, default=3)
    ap.add_argument("--rebase-minutes", type=int, default=15)
    ap.add_argument("--redo-dir", default="", help="saved clusters/batches to reuse for --redo-round")
    ap.add_argument("--redo-round", type=int, default=-1)
    ap.add_argument("--other-test", type=int, default=0,
                    help="test score of another run of the redo round; keep whichever is higher")
    ap.add_argument("--other-champion", default="", help="champion commit of that other run")
    ap.add_argument("--generalize-first", action="store_true",
                    help="start with a round that makes the existing math code more general")
    ap.add_argument("--resume-merge", default="",
                    help="comma-separated agents of the current round to merge from their "
                         "keep/redo-* tags instead of running the round's agents")
    ap.add_argument("--parallel-merge", action="store_true",
                    help="check candidates side by side, then confirm them together")
    ap.add_argument("--no-overlap", dest="overlap", action="store_false",
                    help="finish each round's merges before starting the next round")
    ap.add_argument("--model", default="gpt-6.1-sol")
    ap.add_argument("--effort", default="medium", help="codex reasoning effort")
    args = ap.parse_args()

    state = setup(args)
    leak_set = build_leak_set()
    train = load_split("train")
    test_rows = load_split("test", HIDDEN)
    chat_rows = load_split("chat")
    stop_at = (time.mktime(time.strptime(args.until, "%Y-%m-%d %H:%M")) if args.until
               else time.time() + args.hours * 3600)
    def may_start():
        if os.path.exists(os.path.join(ORCH, "STOP")):
            log("STOP file found; not starting another round")
            return False
        if time.time() > stop_at:
            log("time is up; not starting another round")
            return False
        return True

    by_id = {x["id"]: x for x in train}
    breadth_rows = [by_id[i] for i in state["breadth_ids"]]
    r = state["round"]
    if args.generalize_first and may_start():
        handle = start_generalize_round(state, args, train, r)
        candidates = filter_generalize(handle, collect_round(handle, state, args, leak_set, train))
        finish_round(state, args, handle["agents"], candidates, handle["out_dir"], leak_set,
                     test_rows, chat_rows, breadth_rows, r, False, generalize=True)
    if args.resume_merge:
        log("round %d: resuming the interrupted merge of %s" % (r, args.resume_merge))
        handle = resume_round(state, args, train, r, args.resume_merge.split(","))
    else:
        handle = start_round(state, args, train, r) if may_start() else None
    started = 1
    while handle is not None:
        candidates = (handle["candidates"] if "candidates" in handle
                      else collect_round(handle, state, args, leak_set, train))
        nxt = None
        if args.overlap and started < args.max_rounds and may_start():
            # The next round's agents start from the champion as it is now, before this
            # round's merges; conflicts that causes go to the rebase step.
            nxt = start_round(state, args, train, handle["r"] + 1)
            started += 1
        finish_round(state, args, handle["agents"], candidates, handle["out_dir"], leak_set,
                     test_rows, chat_rows, breadth_rows, handle["r"], handle["bootstrap"])
        if getattr(args, "redo_dir", "") and handle["r"] == args.redo_round and args.other_test:
            # Keep whichever version of this round scored higher on test.
            if args.other_test > state["test"]:
                log("redo of round %d reached %d/1319; the other run of it reached %d; "
                    "continuing from that one (%s)"
                    % (handle["r"], state["test"], args.other_test, args.other_champion[:7]))
                git(["reset", "-q", "--hard", args.other_champion])
                _, br = score(CHAMPION, breadth_rows, args.workers)
                state.update(test=args.other_test, breadth=br, champion=args.other_champion)
                save_state(state)
            else:
                log("redo of round %d reached %d/1319, at least the other run's %d; keeping it"
                    % (handle["r"], state["test"], args.other_test))
        if nxt is None and not args.overlap and started < args.max_rounds and may_start():
            nxt = start_round(state, args, train, handle["r"] + 1)
            started += 1
        handle = nxt


if __name__ == "__main__":
    main()
