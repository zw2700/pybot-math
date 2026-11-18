"""A person in a role who keeps doing the same thing has a band of its own.

"my boss keeps moving the goalposts", "my landlord shrugs it off", "the school says thats life"
name no ask, so they reached the pools that fit any message. The reading and the wording live in
`bot/compose/receiving_end.py`; this module is here so the claim has a band just above the greeting
fallback and below the nudge, and so the fallback file - which is over the size the world accepts -
does not have to change. `respond` returns None on every line that is not this turn.
"""
from ..compose import receiving_end

# Above the greeting fallback (-1000) and the bulky-line pool (-999); below the nudge (-950). Only
# a line that fits any message can be taken from, and only when a role is in it.
PRIORITY = -980


def respond(text, memory):
    """The reply to a role that keeps doing it, or None for every other line."""
    understood = memory.get("understood")
    if not isinstance(understood, dict):
        return None
    clean = understood.get("clean") or " ".join(str(text or "").lower().split())
    repaired = understood.get("plain") or clean
    return receiving_end.reply_for(clean, repaired, memory)
