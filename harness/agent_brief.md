# Your task: teach PyBot a kind of math word problem

PyBot (this repository) is a chatbot written in plain Python: no weights, no ML, just rules.
`bot/runtime.py` runs every module in `bot/modules/` (highest `PRIORITY` first), and the arbiter
(`bot/modules/arbiter.py`) picks the reply. PyBot also has shared parts you can build on:
`bot/understanding/` (normalising typos, number words, chat-speak), `bot/compose/` (phrasing),
`bot/memory/`.

We are teaching PyBot to solve grade-school math word problems (GSM8K style) **with general
rules**. You are one of several agents working in parallel this round, each on a different kind
of problem.

**This round, your kind of problem is: {cluster_desc}**

{phase_section}

## Your target and how you are scored

- `.mathwork/batch_1.txt` … `.mathwork/batch_{n_batches}.txt`: {n_batches} batches of
  {n_target} problems of your kind that PyBot gets wrong today, no problem in two batches.
  Their questions, gold answers and worked solutions are in `.mathwork/train.jsonl`
  (look them up by `id`). Use the worked solutions to understand the reasoning.
  **Work through the batches in order.** Start with batch 1. When you have solved what general
  rules can solve in it, move on to batch 2 rather than forcing the rest, and so on while time
  allows. A new batch is the honest test of your rules: check how many of it your existing
  rules already solve before you change anything, and note that number in your summary.
  `.mathwork/all_targets.txt` lists every batch together; you are scored on all of it, so a
  change for batch 3 must not break what solved batch 1.
- `.mathwork/breadth_ids.txt`: 400 random training problems. PyBot gets **{breadth_now}** of
  them right today; that number must not go down.
- `.mathwork/chat.jsonl`: 1000 ordinary chat messages. **Not one** of PyBot's replies to them may
  change. A math module that answers "I have 3 kids and 2 dogs" with "5" fails the round.

Commands, all from the repository root. They share a machine-wide lock, so a run may wait for
another agent's run to finish; that is normal.

    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/batch_1.txt     --splits-dir .mathwork --runs-dir .mathwork/runs --tag batch_1
    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/all_targets.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag all
    python3 .mathwork/eval.py --bot . --split train --ids .mathwork/breadth_ids.txt --splits-dir .mathwork --runs-dir .mathwork/runs --tag breadth
    python3 .mathwork/eval.py --bot . --split chat --splits-dir .mathwork --runs-dir .mathwork/runs

Per-item results (reply, module, predicted vs gold) go to `.mathwork/runs/`. For a quick check
of one message: `python3 pybot.py -p "your question" -v`.

How the answer is read: **the last number in PyBot's reply** is its answer. End the reply with
the answer, e.g. "16 - 3 - 4 = 9 eggs are left, and 9 x $2 = $18. She makes $18 a day."
Write whole numbers without decimals.

After you finish, the orchestrator merges your work with the other agents' and keeps it only if
PyBot's score on a **held-out test set** goes up and no chat reply changed. You never see that
test set and must not look for it; doing well on the held-out set is only possible with rules
that generalise.

## Rules

1. **General rules only.** Never match a specific question's wording, names, objects or numbers.
   No lookup tables of questions or answers. A rule should still work if every name, object and
   number in the problem changed. Ask yourself: "would this fire correctly on a problem I have
   not seen?" Prefer solving 15 of your 40 properly to 40 of 40 by special cases. Every patch
   is checked for text copied from the held-out problems, and patches that memorise are rejected.
2. **Answer only when confident.** If the parser does not fully understand a problem, return
   None and let the rest of PyBot reply. A wrong number and a hijacked chat message both cost.
3. **Where code goes.**
   - `bot/modules/word_problem.py`: the module PyBot runs. `PRIORITY = 8500` (below the safety
     band at 9000).
   - `bot/math/`: the shared core (number parsing, quantities, exact arithmetic with
     `fractions.Fraction`, reply wording, the skill registry).
   - `bot/math/skills/{skill_name}.py`: **your** rules for this round. Put your work here.
     Change the shared core only when you must, and keep those changes small and backwards
     compatible: other agents are editing it in parallel, and conflicting edits get dropped.
4. **Python 3.8, standard library only.** No `match`, no `X | Y` types, no third-party packages,
   no network.
5. **Stay in this repository.** Everything you need is in this file and the repository; there
   is no `AGENTS.md` or other instruction file outside it. Do not read, list or search files
   outside it (no parent directories), do not edit `.mathwork/`,
   and do not run git commands: the orchestrator commits your work.
6. **Don't break PyBot.** Every module must import cleanly and `turn()` must never raise. Run the
   chat check before you finish.

You have about {minutes} minutes. When done, reply with a short summary: what you added, your
for each batch you reached: how many your rules solved on first sight and after your changes; breadth before and after, and the chat check result.
