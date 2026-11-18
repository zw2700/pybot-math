"""A first line is not receipted for something never said.

Two of the composer's three floor lines say the bot has taken something in ("Got it. Is there
anything you'd like a hand with?", "Thanks for telling me - I'm here if you want to dig into any of
that"). A chat's first line is the one turn where nothing has been said yet, so the receipt claims
a turn that did not happen: thirty of the deck's nine hundred first lines got one of the two.

On the first turn only, a receipt with nothing behind it is replaced by an opener that says nothing
about the line and asks for the thing an answer would start from. This module sits above `greeting`
(-1000) and below every module that answers a line of its own, and it asks greeting what it would
say, so a card, a place named in the answer, an ask for hands and a limit all keep the turn
("the laundry needs doing" keeps the chore card, a fence down in the wind keeps the damage card,
"my glucose is 2.9" keeps the hypo card). The same receipt is right on every later turn, where
there is a turn behind it.
"""
from ..compose import fallback
from ..compose.fallback_data import A_RECEIPT_OF_NOTHING, COLD_OPEN
from . import greeting

# Above greeting (-1000), below every module that answers a line of its own (-999 and up), so an
# opener is only ever given a turn the receipt would otherwise have had.
PRIORITY = -999.5


def _has_a_turn_behind_it(memory):
    for one in (memory.get("turns") or []):
        if isinstance(one, dict) and str(one.get("bot") or "").strip():
            return True
    return False


def respond(text, memory):
    if _has_a_turn_behind_it(memory):
        return None
    try:
        reply = greeting.respond(text, memory)
    except Exception:  # noqa: BLE001 - a reading that fails simply adds no opener
        return None
    if not reply or not A_RECEIPT_OF_NOTHING.search(str(reply)):
        return None
    clean = " ".join(str(text or "").split())
    return fallback._choose(COLD_OPEN, memory, clean)
