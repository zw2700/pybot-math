"""The plan of a day, when the thread already holds every part of it.

A day out is said over several turns - a gig on Saturday, three of us, eating first, staying
over, cheap and cheerful - and then somebody asks the obvious question: "so whats the plan for
the day then". No card answers that, because nobody can look up somebody else's day. The order of
a day out is not knowledge either: the hour that cannot move, the meal, the bed. Every constraint
on it was said by the person, so the reply lays the order out, says their own words back, and
names the one hour the bot cannot know instead of guessing it.

This module sits just above greeting's honest hedge and below every light remark and every card,
so it only ever speaks where the bot would otherwise have told the person to go and search. It
asks the composer first and stands down unless the answer really is a hedge, so any reader in
`bot/compose/fallback.py` that has found its own body (a venue's page, a booking, a timetable)
keeps its turn even though this module outranks greeting.

`bot/compose/plan_ask.py` does the reading. Nothing here holds a fact about the world: the order
is cut to the day the thread describes, a train home the same evening is not told to book a room,
a booking that is already made is not made again, and a meal cooked at home is not a day out.
"""
from ..compose import fallback, plan_ask

# The hedge the composer answers with, in the shapes that reach the person. `fallback._is_a_hedge`
# knows most of them; the search-and-call family is read here as well, so a new wording cannot
# leave somebody with "go and search" while this module stands down and says nothing.
SEARCH_ONLY = fallback._is_a_hedge

PRIORITY = -999  # above greeting (-1000), below nudge (-950), urgent, invitation and every card


def respond(text, memory):
    """Lay out the plan the thread holds, or say nothing and let the composer answer as it did."""
    clean = fallback._matchable(fallback._plain((memory.get("understood") or {}).get("clean") or text))
    pool = plan_ask.plan_ask_pool(clean, memory)
    if pool is None:
        return None
    said = fallback.reply_for(text, memory)
    if not SEARCH_ONLY(said or ""):
        return None  # the composer has an answer of its own; it keeps the turn
    return fallback._choose(pool, memory, fallback._matchable(text))
