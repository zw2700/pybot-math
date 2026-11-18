"""A thing of theirs in a state that wants doing is asked about, not receipted.

"the grass is long", "the car is dirty", "the windows are filthy", "my shoes are worn out" and
"my coat is tatty" were all answered with the composer's receipt - "Thanks for telling me - I'm
here if you want to dig into any of that" - which says nothing back about the thing the person has
just handed over and asks nothing about it. Dumping the candidates for two of them shows nothing
else proposes anything at all: there is no card for either, though `when should i cut it` two turns
later gets the mowing card. So this is the floor, and the floor was a shrug in better words.

`bot/compose/a_thing_wants_doing.py` reads the shape - `my/our/the <thing> is <state>`, with a
state that wants doing - and stands down for a body part, for a person, for a thing gone wrong or
simply old, and for anything the line says the person feels.

This module sits just above `greeting` (-1000) and below every card, so it only ever speaks where
the bot would otherwise have receipted the line. It asks `greeting.respond` first - the composer
and every reader in it - and stands down unless the answer that came back really is that receipt,
so a card, an entry, a reader of the composer's own and the day pools all keep their turn even
though this module outranks greeting. It writes nothing about the world, so nothing here can be
wrong or go stale, and like the reading it is asked only on a line it recognises.
"""
from ..compose import a_thing_wants_doing, fallback
from . import greeting

# A floor module: above `greeting` (-1000), which is what answers these lines with the receipt, and
# below everything with an answer of its own - `answers` (0), `chat` (300), the store, the topics
# and the safety band. Same slot as `where_it_answers`, which reads other lines: a kind of question
# whose answer is nowhere here, where this one reads a thing in a state that wants doing.
PRIORITY = -999


def _the_thing_and_its_state(text, memory):
    understood = memory.get("understood") or {}
    clean = ((understood.get("clean") if isinstance(understood, dict) else None)
             or " ".join(str(text or "").lower().split()))
    return clean, a_thing_wants_doing.pool(clean, memory)


def respond(text, memory):
    """A question about the thing, or None where the bot already said something about it."""
    clean, pool = _the_thing_and_its_state(text, memory)
    if not pool:
        return None
    # Every reader of the composer's own is asked first: the line is only this module's where the
    # answer that came back is the receipt and nothing else.
    said = greeting.respond(text, memory) or fallback.reply_for(text, memory)
    if not fallback._in_a_pool(said, (fallback.NEUTRAL,)):
        return None
    return fallback._choose(pool, memory, clean)
