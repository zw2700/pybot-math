"""A line asking whether the advice will work is answered with what the advice achieves.

"will that work" after a how-to names nothing of its own, and the chat module read it as a nod.
The card the bot had just printed already says what the method achieves ("almost nothing needs
scrubbing after that"), so the reply is that clause with the yes in front of it. The reading and
the wording live in `bot/memory/will_it_work.py`.

The band sits above the small talk (chat.py, 300), which is what answered these lines with a stock
line, and below the memory store and the safety band: a check inside a crisis is never this
module's, and a verdict the store holds ("No: a satay is made with nuts") is said back by
`thread.checking_the_verdict`. It returns None on every line that is not only this check, and on
every card that does not say what it achieves.
"""
from ..memory import will_it_work

# The chatter band, which is where a take on a line is worth anything: a take from under CHATTER
# gives the line up to any card beside it that names the line's own words, and the chat pool for
# this line names "work". Same band as the measure follow-up, which found the same floor.
PRIORITY = 1000


def respond(text, memory):
    """The yes with the card's own account of why, or None."""
    try:
        return will_it_work.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a hook that raises answers nothing
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but the check, and only when the card above says why."""
    try:
        return bool(will_it_work.reply_for(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


TAKES_AS_IT_COMES = takes_as_it_comes
