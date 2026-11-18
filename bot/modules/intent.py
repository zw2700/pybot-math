"""The kind of answer the line wants, kept where every module and tool can read it.

The understanding engine reads what the line is about and which question words it carries; this
watches that reading and writes `memory["understood"]["wants"]`: the shape of answer the person is
owed - a time, an amount, a place, a person, a meaning, a yes or no, a pick, steps, options or a
reason (`bot/compose/fit.py` holds the list and the check).

It observes only, and it never replies. It runs at PRIORITY 9500: below `understand.py` (10000),
which writes `memory["understood"]`, and above every other observer (the memory store is 7000), so
the key exists before any module reads the line. A line that asks for no shape of its own - a
greeting, a feeling, a question about the bot itself - leaves `wants` unset rather than guessing,
and a module that does not find the key simply reads the line as it did before.

`bot/compose/clause.py` reads the question out of the clause after the comma ("camping, might
rain, what to pack" is a list, not a verdict) and lifts a reading that the whole line made weak;
a shape the whole line gave is kept.

The shape is kept in `memory["intent_wants"]` too, so the next line can be read against it: a bare
follow-up ("and for brown rice?", "what about once it is up in july") is asking the same kind of
answer about something else, and on its own words it asks for nothing in particular.
"""
from bot.compose import clause, fit, what_it_asks

PRIORITY = 9500


def observe(text, memory):
    """Write `memory["understood"]["wants"]` from this turn's reading, or leave it unset."""
    if not isinstance(memory, dict):
        return
    read = memory.get("understood")
    if not isinstance(read, dict):
        return
    before = memory.get("intent_wants")
    want = what_it_asks.the_shape_it_asks(
        read, clause.shape(read, fit.wants(read, before if isinstance(before, str) else None)))
    # Written every turn, a line with no shape of its own included: two turns later a stale shape
    # would be handed back to a follow-up that leans on the turn in between ("thanks, that helps").
    memory["intent_wants"] = want
    if want:
        read["wants"] = want
    else:
        read.pop("wants", None)
