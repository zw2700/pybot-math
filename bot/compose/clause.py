"""The question is the clause after the comma.

People lead with the situation and ask at the end: "camping, might rain, what to pack", "5 foot 2,
trousers for work, what do i look for when buying a pair". The understanding engine already splits
the line - `understood["focus"]` is the clause after the last comma - but the shape of answer is
read from the whole line, and a lead-in can change what that reading looks like: "might rain"
carries an auxiliary, so the line reads as a yes/no, and the person who asked what to pack is owed
a list rather than a verdict.

Two things are read here, and only where the whole-line reading is weak:

- the clause after the comma, when it is a question of its own (`what to pack`, `what do i need`,
  `what do i look for`) and the line is one clause no longer;
- a thing the person has not got ("wedding in september, nothing to wear"), which is the thing they
  are asking for.

A line that already asks for a shape of its own keeps it: this can only lift a reading that came
back as nothing or as a yes/no, never overrule a time, an amount or a place. `bot/modules/intent.py`
calls `shape()` after `fit.wants()`, and the arbiter reads the result as it always has.
"""
import re

from bot.compose import fit

# What to look for is a method, in every spelling people use for it: "what do i look for when
# buying a mattress", "what should i look for in a used car". The verb is not in `WHAT_TO_STEPS`,
# and the line was answered as if it asked nothing.
WHAT_TO_LOOK = re.compile(
    r"\bwhat\s+(?:to|(?:do|should|shall|can|could|must)\s+(?:i|we))\s+(?:need to\s+|"
    r"have to\s+|ought to\s+)?(?:look(?!\s+like\b)(?:\s+(?:out\s+|around\s+)?for)?|"
    r"check(?:\s+for)?|watch\s+out\s+for|ask(?:\s+for)?|avoid)\b", re.I)

# A thing the person has not got is the thing they are asking for: "nothing to wear to a wedding"
# asks for a pick. The verb is what it is about - "nothing to me" is a quarrel, not a question.
NOTHING_TO_A_THING = re.compile(
    r"\bnothing (?:to|for) (?:wear|put on|bring|take|pack|cook|make|eat|have|drink|watch|read|"
    r"give|buy|get|play)\b", re.I)

# A question asked in the clause after the comma opens on one of these, and nothing else does.
_OPENS_A_QUESTION = ("what", "which", "how")

# The shapes a weak reading may be lifted to. A time, an amount, a place, a person, a meaning or a
# reason is never replaced: those were read from the whole line and a lead-in clause cannot ask for
# one of them by accident.
_SHAPES_FROM_A_CLAUSE = ("pick", "options", "steps")


def _said(read):
    return " ".join(str(read.get("clean") or read.get("text") or "").lower().split())


def _focus(read, said):
    """The clause after the last comma, or None when the line is one clause."""
    focus = read.get("focus")
    if isinstance(focus, (list, tuple)):
        focus = " ".join(str(word) for word in focus)
    if not isinstance(focus, str):
        return None
    focus = " ".join(focus.lower().replace("\u2019", "'").split())
    if not focus or focus == said:
        return None
    if len(focus) > 0.85 * max(len(said), 1):
        # the focus is the line with a word or two missing, not a second clause
        return None
    return focus


def the_clause_ask(read):
    """The shape asked in the clause after the comma, or None when the clause asks for none.

    Only the asks a clause can carry on its own are read - "what to cook, wear, pack or buy", "what
    to do", "what do i need", "what do i look for" - so nothing else is invented from it.
    """
    if not isinstance(read, dict):
        return None
    said = _said(read)
    focus = _focus(read, said)
    if focus is None or not focus.startswith(_OPENS_A_QUESTION):
        return None
    focus = " " + focus + " "
    if fit.WHAT_TO_PICK.search(focus):
        return "pick"
    if fit.WHAT_I_NEED.search(focus) or fit.WHAT_YOU_TAKE.search(focus):
        return "options"
    if fit.WHAT_TO_STEPS.search(focus) or fit.WHAT_TO_DO.search(focus) or WHAT_TO_LOOK.search(focus):
        return "steps"
    return None


def shape(read, want):
    """`want`, lifted to the shape the clause after the comma asks, or left alone.

    A shape the whole line already gave - a time, an amount, a place, or a pick, options or steps
    of its own - is kept: the clause is only read where the line came back as nothing or as a
    yes/no a lead-in put there.
    """
    if want in _SHAPES_FROM_A_CLAUSE or want in ("time", "amount", "place", "person", "meaning",
                                                 "reason", "number", "clock", "price"):
        return want
    if not isinstance(read, dict):
        return want
    said = _said(read)
    # "any ideas" has asked for a few, and the pick is one of them: a line that says so keeps the
    # list it asked for.
    if NOTHING_TO_A_THING.search(said) and "list" not in (read.get("asks") or ()):
        return "pick"
    # One clause, so the clause reading has nothing to split: "what do i look for when buying a
    # mattress" asks for the method in the whole line, and the verb is not in `WHAT_TO_STEPS`.
    if WHAT_TO_LOOK.search(" " + said + " "):
        return "steps"
    return the_clause_ask(read) or want
