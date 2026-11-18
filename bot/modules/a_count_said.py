"""A count the person reports, read against the count the last answer named.

"how many steps should i do a day" names a figure to aim at ("about 7,000 to 8,000 steps a day"),
and the next thing people do is say how they are doing against it: "i have about 7000 steps". That
line was answered with a search hedge, a receipt or a greeting, because the answer's own figure is
said as a rate ("7,000 to 8,000 steps a day") and a rate is not read as an amount to compare with.

`bot/memory/amounts.py` reads the two counts. This module is the thin part: one line in, one line
out, and it hands the line back (None) whenever the counts are not the same thing said the same
way - a count of something else, a question about an amount, a length that belongs to something
else ("2 hours of meetings"), or an answer naming two figures of that thing.

It answers **only** the turn that reports the count. The turn after it ("how much more do i need",
"is that enough") belongs to the store, which already reads it and keeps its own guards, so
nothing here is kept in `memory` and nothing is claimed twice.
"""

from ..memory import amounts

PRIORITY = 7000


def observe(text, memory):
    """Nothing to keep: the report turn is read from the answer above it, every time."""
    return None


def respond(text, memory):
    """Where the count they reported stands against the answer above it, or None."""
    if not isinstance(text, str):
        return None
    said = amounts.a_count_they_report(text)
    if said is None:
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    last = turns[-1].get("bot") if isinstance(turns, list) and turns else ""
    against = amounts.against_the_last_answer(said, last or "")
    if against is None:
        return None
    return amounts.the_comparison(against)
