"""A year of birth told in chat is the age, said the long way.

    i was born in 1990
    how old am i          -> main: "You haven't told me your age yet."

The store has always answered "how old am i" from the age it was told ("You told me you're 34"),
and it reads a figure after "i am" or "i'm". A year of birth is the same fact in other words, and
nothing read it: the person says when they were born, asks their age a turn later, and is told
they never said.

So the year is filed as the age this chat would work out from it, and the store's own answer does
the rest - which is what the person hears in the wording the store already uses, not a second
voice saying the same thing in its own way.

Only the person's own year is taken. Somebody else's ("my son was born in 2015") is a fact about a
person the store keeps, and the readers that answer "how old is my son" own it. A line that gives
both keeps them apart: "i was born in 1990 and im 35" leaves the age it states.
"""

import datetime
import re

# The reply to a line that only says the year they were born. Said the way a friend takes it in:
# the figure it works out to, in this year, and nothing asked back (STYLE.md: a reply that ends on
# a question every time is a form, not a conversation). Main answered "How was it, overall?" - the
# line read as an experience to ask about, which is not a reply to anything in it.
A_BIRTH_YEAR = (
    "Born in {born}, so you turn {turned} this year.",
    "{born}. That makes you {turned} this year.",
    "Noted - {turned} this year, going by {born}.",
)

# "i was born in 1990", "born in june 1990", "i was born 1990". The year has to
# follow "born" closely, so "i was born in a village in 1990" is still the year, and a line about a
# birth that is not theirs ("my daughter was born in 2015") is refused below.
_A_BORN = re.compile(
    r"\b(?:i\s+was\s+born|i\s+am\s+born|im\s+born|born)\b[^0-9]{0,14}\b(1[89]\d\d|20\d\d)\b", re.I)
# The subject of "born" has to be the person chatting: "my son was born in 2015" is his year.
_SOMEONE_ELSE_BORN = re.compile(
    r"\b(?:my|his|her|their|our|your|its)\s+(?:\w+\s+){0,2}?(?:was|were|is|are)\s+born\b", re.I)
# A line that also says the age it is: "i was born in 1990 and im 35" is 35, whatever the sum says.
_ALSO_AN_AGE = re.compile(
    r"\b(?:i\s?m|i\s+am|im|i\s+turned|i\s+will\s+be)\s+(\d{1,3})\b(?!\s*(?:years?\s+(?:ago|from)|"
    r"kg|pounds?|miles?|minutes?|hours?|days?|weeks?|months?))", re.I)


def _today():
    return datetime.date.today()


def _the_store(memory):
    from . import user
    return user(memory)


def _a_slip(clean):
    """True when the line is only the year of birth, with no ask after it."""
    rest = str(clean or "").strip()
    born = _A_BORN.search(rest)
    if born:
        rest = (rest[:born.start()] + " " + rest[born.end():]).strip()
    return not re.search(
        r"\?|\b(?:how|what|when|where|why|who|which|should|can|could|would|do|does|did|is|are|"
        r"will|any)\b", rest, re.I)


def reply(text, memory):
    """The answer to a line that only says the year they were born, or None."""
    said = str(text or "")
    if not said or not _A_BORN.search(said) or _SOMEONE_ELSE_BORN.search(said):
        return None
    if not _a_slip(said) or len(said.split()) > 12:
        return None
    year = memory.get("born_year")
    try:
        year = int(year)
    except (TypeError, ValueError):
        return None
    turned = _today().year - year
    # A line that says both ("i was born in 1990 and im 35") is worked out from the age it said,
    # which `observe` has already filed, so the reply does not contradict the line in front of it.
    try:
        stated = _the_store(memory).get("age")
        if stated is not None and 0 < int(stated) < 130:
            turned = int(stated)
    except Exception:  # noqa: BLE001 - the store is a hint here, never a cost
        pass
    if not 0 < turned < 130:
        return None
    from ..compose import pick
    return pick(tuple(line.format(born=year, turned=turned) for line in A_BIRTH_YEAR), memory, said)


def observe(text, memory):
    """File a year of birth the line gives about the person as the age it works out to."""
    said = str(text or "")
    if not said:
        return
    born = _A_BORN.search(said)
    if not born or _SOMEONE_ELSE_BORN.search(said):
        return
    try:
        year = int(born.group(1))
    except (TypeError, ValueError):
        return
    this_year = _today().year
    if not 1900 <= year <= this_year:
        return
    memory["born_year"] = year
    if _ALSO_AN_AGE.search(said):
        return
    turned = this_year - year
    if not 0 < turned < 130:
        return
    try:
        facts = _the_store(memory)
    except Exception:  # noqa: BLE001 - the store is a hint here, never a cost
        return
    if "age" in facts:
        return
    from . import remember
    remember(memory, "age", turned, said)
