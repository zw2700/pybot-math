"""A follow-up that names nothing of its own takes the kind of answer the line above named.

    my order hasnt come        "Book a bulky waste collection with your council - most charge
                                twenty to forty pounds and collect from the doorstep."
    and how long               the hedge ("I'm not sure about that one, sorry - I'd rather not
                                guess. A quick search online will get you a solid answer")

    im on benefits             the Universal Credit card
    can i save anything        the hedge again

The second line is the same *kind* of question as the first line of each pair - how long it takes,
what you are allowed while you claim - and the answer is not in a card, because the card above
answered a question about a different subject. A friend keeps the kind and says what that kind of
thing turns on, or names the one place it is written down, in the same breath.

The reading and the wording live in `bot/compose/kept_nearby.py`. It is deliberately narrow: the
line must lean on what is above it (`and how long`, `what about the cost`), must name no thing of
its own, and the person's own earlier line must be one the table has a kind for. A follow-up that
brings a subject decides its own turn, so it is not this reading's (white-peach's three guards on
#12543: a measure word is a kind of ask, a `how do i ...` is a method and not the kind above it,
and two lines back is only in thread when the line between them leaned on it too).

The band is why this is a module and not a branch in the greeting's hook: **-999**, above the
greeting fallback (-1000) and under every module that has a real answer for the line. It reads the
bot's own last reply to stay in that seat: the turn it replaces is a hedge or a receipt, so the
module stands down when the last reply came from anything but the fallback (`greeting`, `chat`).
That is the same reading the hedge gate made in `bot/modules/greeting.py`, done where a module can
declare its own priority instead of editing the file every other reader hooks into.
"""
from ..compose import fallback, kept_nearby

PRIORITY = -999  # just over the greeting fallback (-1000), under every module with a real answer

# The modules whose reply is the fallback: a hedge, a receipt ("Got it. Is there anything you'd
# like a hand with?"), or the small-day pool. Anything else answered the line itself.
FALLBACK_MODULES = frozenset(("greeting", "chat"))


def _answered_by_the_fallback(memory):
    turns = (memory or {}).get("turns") or []
    if not turns:
        return False
    return str(turns[-1].get("module") or "") in FALLBACK_MODULES


def respond(text, memory):
    """The kind of answer the earlier line named, or None on every other line."""
    try:
        if not _answered_by_the_fallback(memory):
            return None
        nearby = kept_nearby.answer_for(text, memory)
        if not nearby:
            return None
        return fallback._choose(nearby, memory, text)
    except Exception:  # noqa: BLE001 - a reading that raises answers nothing
        return None
