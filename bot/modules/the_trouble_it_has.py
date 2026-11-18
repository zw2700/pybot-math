"""One question back about the thing that is not working, instead of a stall.

"my airpods are not showing up" and "my laptop is slow" are statements of a trouble, and the bot
answers them with "Got it. Is there anything you'd like a hand with?" or a search, which fits any
message at all. The question a friend asks instead is the same one for a boiler, a car and a
laptop - is it every time, and did anything change - and it is a question the bot can ask without
knowing a single fact about the thing.

`bot/compose/a_trouble.py` finds the thing in the person's own words and the question that goes
with it. This module sits in the band `where_it_answers` uses - above greeting's hedge, below
every card - and stands down unless the composer's own reply says nothing about the line.
"""
from ..compose import a_trouble, fallback

PRIORITY = -999  # above greeting (-1000), below nudge (-950), urgent, invitation and every card


def respond(text, memory):
    """Ask about the trouble the person named, or say nothing and let the composer answer."""
    clean = fallback._matchable(fallback._plain((memory.get("understood") or {}).get("clean") or text))
    pool = a_trouble.trouble_pool(clean, memory)
    if not pool:
        return None
    said = fallback.reply_for(text, memory)
    if not a_trouble.says_nothing_about_the_line(said, fallback._matchable(text)):
        return None  # the composer has an answer of its own; it keeps the turn
    return fallback._choose(list(pool), memory, fallback._matchable(text))
