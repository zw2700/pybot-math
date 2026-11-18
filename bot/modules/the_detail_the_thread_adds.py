"""The detail a person drops into a thread, taken up rather than nodded at.

"she doesnt like surprises" while a 70th is being planned, "it was fine for two years" about a
boiler, "ive said no once already" about a boss: the turn after each of those is where the bot
says nothing - "I'm listening - say more if it helps", the line said back, or a search - and the
turn after that, asked as a question, gets a real card. The thread was there all along.

`bot/compose/thread_detail.py` does the reading: three kinds of detail (a limit somebody has, an
attempt already made, a history), and the one question each of them raises. This module sits in
the band `where_it_answers` and `a_day_somebody_else_keeps` use - above greeting's hedge, below
every card - and stands down unless the composer's own reply says nothing about the line, so any
reader that found its own answer keeps the turn.

Nothing here holds a fact, so nothing here can be wrong or go stale.
"""
from ..compose import fallback, thread_detail

PRIORITY = -999  # above greeting (-1000), below nudge (-950), urgent, invitation and every card


def respond(text, memory):
    """Ask the one question the detail raises, or say nothing and let the composer answer."""
    clean = fallback._matchable(fallback._plain((memory.get("understood") or {}).get("clean") or text))
    pool = thread_detail.detail_pool(clean, memory)
    if not pool:
        return None
    said = fallback.reply_for(text, memory)
    if not thread_detail.says_nothing_about_the_line(said, fallback._matchable(text)):
        return None  # the composer has an answer of its own; it keeps the turn
    return fallback._choose(list(pool), memory, fallback._matchable(text))
