# Word problem skills

`bot.modules.word_problem` (priority 8500) calls `bot.math.solve(text)`.
The shared gate requires a quantitative question, a narrative and at least two
quantities. Statements such as "I have 3 kids and 2 dogs" do not trigger it.

To add a skill, add a Python module under `bot/math/skills/` exposing
`solve(problem)`. Return `(answer, working_text)` only when the entire calculation
is understood, otherwise `None`. Files are tried in alphabetical order, first
successful skill wins. Modules starting with `_` are ignored. Restart the bot
after adding a file. Keep skills independent and conservative.

`problem.text` is the original text with normalized apostrophes/dashes;
`body` and `question` are lowercase, split at the final question cue.
`problem.numbers` contains `Number(value, start, end, raw, kind)` records with
offsets into `text`. `problem.values` provides the values alone.
`read_numbers(text)` and `parse_number(text)` support digits, thousands commas,
money, cardinal words, simple fractions and percentages. Percent values are
ratios (25% is Fraction(1, 4)); ordinal labels are excluded.

Use `fractions.Fraction` throughout; never round intermediate calculations.
`format_number` renders whole numbers without decimals. The engine appends the
final answer after the working so its last number is always the result.
Do not mutate memory, match names/objects from examples, guess operations from
number count alone, or consume quantities a rule cannot explain.

Validate through `bot.runtime.turn`, including arbiter routing, and run the
target, breadth and ordinary-chat evaluations described in `.mathwork/TASK.md`.
