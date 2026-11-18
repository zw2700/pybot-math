# Harness: teaching PyBot grade-school math with Codex agents

This folder is the loop that wrote PyBot's math code (`bot/math/`, `bot/modules/word_problem.py`).
No person wrote those rules: rounds of Codex agents did, and every change was kept or dropped
by the gates below.

| File | What it does |
|---|---|
| `prepare.py` | Builds the fixed splits from the raw downloads in `data/` |
| `orchestrate.py` | Runs the rounds: picks targets, launches agents, audits and merges their patches |
| `eval.py` | Scores a PyBot checkout on a split; the answer is the last number in the reply |
| `check_candidate.py` | Runs the three merge gates on one checkout (used for parallel checks) |
| `agent_brief.md` | The task every agent reads (the generalisation and rebase tasks are in `orchestrate.py`) |
| `remote/` | Setup and run scripts for a RunPod CPU pod |

## Data

`prepare.py` expects these files in `harness/data/` (not included here):

| File | Source |
|---|---|
| `train.jsonl`, `test.jsonl` | GSM8K, [openai/grade-school-math](https://github.com/openai/grade-school-math) |
| `symbolic/main.jsonl` | GSM-Symbolic, [apple/GSM-Symbolic](https://huggingface.co/datasets/apple/GSM-Symbolic) |
| `smoltalk/test.parquet` | [HuggingFaceSwarms/SmolTalkBench](https://huggingface.co/datasets/HuggingFaceSwarms/SmolTalkBench) |

It writes `splits/train.jsonl` and `splits/chat.jsonl`, which agents may read, and
`hidden/test.jsonl` and `hidden/symbolic.jsonl`, which only the orchestrator reads.

## One round

1. Score the current PyBot (the "champion") on 400 fixed training problems ("breadth") plus a
   fresh sample of 600, to see what it gets wrong.
2. Group failing training problems by topic (from their worked solutions) and number of steps.
   Give each of 6 agents one group: 4 batches of 40 problems, problems no agent has seen first.
3. Each agent works for 45 minutes in its own git worktree, with Python 3.8 stdlib only, no
   network, and no access to the test data.
4. Commit and audit each patch: reject it if it contains an 8-word phrase that appears in the
   held-out problems but not in train, or if the agent ran commands touching held-out data,
   other agents' worktrees or the network.
5. Check every patch in parallel, then together. A patch is kept only if **none** of PyBot's
   replies to 1,000 ordinary chat prompts change, breadth does not drop, and the score on the
   **held-out GSM8K test set** goes up. Patches that conflict are carried over by a short
   Codex rebase session.
6. Every few rounds, score GSM-Symbolic (renamed and renumbered test problems) as a
   memorisation check.

Agents only ever see their own training problems, breadth, and the chat prompts. The test
score is used only as a keep-or-drop decision; no agent sees test questions or per-problem
results. Round "10g" was a generalisation round: no new targets, each agent refactored one
area of the math code towards more general rules, and a patch only had to keep test level.

## Running it

```sh
python3 prepare.py                     # once, after downloading the data
python3 orchestrate.py --hours 24 --agents 6 --parallel-merge --no-overlap --effort high
touch orch/STOP                        # finish the current round, then stop
```

It expects a PyBot git checkout at `../src/pybot` and the `codex` CLI on the path. Progress
goes to `orch/log.txt` and `orch/progress.tsv`. `remote/run.sh` is the exact invocation used
for the last part of the run, on a 32-vCPU RunPod CPU pod.

## Result

GSM8K test accuracy went from 12/1319 (0.9%) to 201/1319 (15.2%) over 16 rounds.
GSM-Symbolic tracked test throughout (19.0% at the end), and no chat reply changed.
