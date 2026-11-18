# Word problem skills

`bot.modules.word_problem` (priority 8500) calls `bot.math.solve(text)`.
The shared gate requires a quantitative question, a narrative and multiple
quantities (including mixed-number components or an implied comparison factor).
Singular events at a stated interval use parsed number spans rather than a
fixed list of event nouns or time units. Statements such as "I have 3 kids and
2 dogs" do not trigger it.

To add a skill, add a Python module under `bot/math/skills/` exposing
`solve(problem)`. Return `(answer, working_text)` only when the entire calculation
is understood, otherwise `None`. Files are tried in alphabetical order, first
successful skill wins. Modules starting with `_` are ignored. A failed import,
reader exception or invalid result is skipped so independent skills still run.
Restart the bot after adding a file. Keep skills independent and conservative.

`problem.text` is the original text with normalized apostrophes/dashes;
`body` and `question` are lowercase, split at the final question cue.
`problem.numbers` contains `Number(value, start, end, raw, kind)` records with
offsets into `text`. `problem.values` provides the values alone.
`read_numbers(text)` and `parse_number(text)` share the exact grammar in
`_number_syntax.py`: signed digits, thousands commas, money, cardinal words,
digit scale coefficients, word and slash fractions, mixed numbers and
percentages. Ordinal spelling supplies general fraction denominators, including
compound denominators. Percent values are ratios (25% is Fraction(1, 4)).
`parse_number` requires a complete valid quantity and rejects malformed
cardinals rather than adding unrelated number words together.

Numeric and compound ordinal labels are excluded. Bare fraction words such as
"third" or "quarter" can also name labels or objects; skills must resolve those
from context. Digit counts of halves or quarters remain separate rather than
being merged into an ambiguous fraction. Source offsets always refer to
`problem.text`, including for signed quantities and written fractions.

Use `fractions.Fraction` throughout; never round intermediate calculations.
`format_number` renders whole numbers without decimals. The engine appends the
final answer after the working so its last number is always the result.
Do not mutate memory, match names/objects from examples, guess operations from
number count alone, or consume quantities a rule cannot explain.

Validate through `bot.runtime.turn`, including arbiter routing, and run the
target, breadth and ordinary-chat evaluations described in `.mathwork/TASK.md`.
