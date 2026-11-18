"""The month a person sets out: what comes in, what goes out, and what is left of it.

"im on 1800 a month and rent is 700" is arithmetic, and in the deck on main it reached a card
about the rent being raised or an eviction notice, because `rent` is a word the housing entry
owns; "i take home 1800 and rent is 700" reached the duty-free allowance, off `take home`; and
"we bring in 2400 a month and the mortgage is 900" reached "Got it. Is there anything you'd like
a hand with?". What comes in and what goes out, said together, is a sum, and the reply is the
sum on the person's own figures.

The reading lives in `bot/memory/outgoings.py` and says "" for everything it does not read whole
- arrears, a rent going up, a tax code, an ask, two units in one line - so this module answers
only the lines it read, and passes on every other line.

Priorities: above the answer modules (0) because a card about the rent answers a different
question from the sum of a month, and below the safety band (9000) and the reading of the line
(10000), which must lead on a line of their own.
"""
from ..memory import outgoings

PRIORITY = 8000  # above the answer modules, below safety


def TAKES_AS_IT_COMES(text, memory):
    """This line is the one to answer as it comes: a month said out loud, and the sum of it."""
    if not isinstance(memory, dict):
        return False
    return bool(outgoings.reply_for(text, memory))


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    return outgoings.reply_for(text, memory) or None
