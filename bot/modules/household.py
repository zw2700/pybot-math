"""Who lives with the person, as a turn of its own.

`bot/memory/household.py` holds the reading and the wording. This module is here because the two
lines it answers are ones the store and the knowledge base both read wrongly:

    its just me and my daughter
      -> "Tell them as soon as it is certain... which room is theirs, where the school is..."
    who lives with us
      -> "You haven't mentioned a place yet."

The first is the move-news card, because the line names a child and the word "just"; the second is
the place reader looking for a town in a line that asks about the household. Neither is a guess a
higher band should keep: the household is the whole of the line, so the claim is this module's.

It sits just above the store's band, which is the band for the facts the chat holds, because the
place reader is in the store and would otherwise answer the ask with a denial.
"""
from ..memory import household

PRIORITY = 7050


def observe(text, memory):
    """File who lives with them, on the chat's own memory."""
    try:
        household.observe(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails files nothing
        return


def respond(text, memory):
    """The household said back, or the ask answered, or None."""
    try:
        return household.answer(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails leaves the line as it was
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but the household."""
    try:
        return bool(household.takes_as_it_comes(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
