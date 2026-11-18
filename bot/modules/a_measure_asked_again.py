"""A follow-up that asks the measure again is answered from the answer above, not looked up again.

"and how much" after "how much water should i drink a day" reached the alcohol card, because the
three words name nothing and the knowledge base read them as a question of their own. The figure
is in the answer the person just read, so the answer is that sentence of it. The reading and the
wording live in `bot/memory/measure.py`.

This module sits above the knowledge base (0) - the entry that answered these lines was the
knowledge base reading a bare measure as a subject - and below the safety band and the loss and
grief modules, which keep their turns: "and how long" in a chat about a diagnosis is not a
question about a cooking time. It returns None on every line that is not only a measure.
"""
from ..memory import measure

PRIORITY = 1000  # above the knowledge base, below loss (2000), grief (2100) and safety (9000)


def respond(text, memory):
    """The sentence of the answer above that answers the measure again, or None."""
    try:
        return measure.reply_for(text, memory)
    except Exception:  # noqa: BLE001 - a hook that raises answers nothing
        return None


def takes_as_it_comes(text, memory):
    """Only on a line that is nothing but a measure, and only when the answer above has it."""
    try:
        return bool(measure.reply_for(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


# The arbiter reads the declaration by this name, the way every other module that claims a line
# does. The knowledge base claims this one too - a card matched the bare measure's words, which
# is the card about something else - so the module that read the answer above says so itself.
TAKES_AS_IT_COMES = takes_as_it_comes
