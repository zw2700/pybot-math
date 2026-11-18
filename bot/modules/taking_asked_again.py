"""A bare "what can i take" is about the thing the chat is on.

Four words with nothing in them name nothing to take and nothing to take it for, so every reader
of the words alone answered them off the words:

    i keep getting heartburn / is it normal / what can i take
      -> "What are you going to, and how long for? Then I can say what to take and what to leave."
    my back is killing me / what can i take
      -> "Coming into the UK you can bring 4 litres of spirits, 18 litres of wine ... 390 pounds."
    i have a cough / how long will it take to clear up / and what can i take
      -> "What is it for? The list for a night away is nothing like the one for a meeting."

The knowledge base has all three answers; what it cannot do is see the subject of a line that has
none. The reading and the wording live in `bot/memory/taking.py`, which puts the subject of the
chat into the question the entries are keyed on ("what can i take for heartburn") and hands back
the knowledge base's own answer, and answers nothing else.

This module sits above the knowledge base (0) and the small talk (300), because it is those two
that answered the lines above, and below loss (2000), grief (2100) and the safety band, which keep
their turns: a bereavement is not a question about what to take. It returns None on every line
that is not the bare ask with a complaint in the chat.
"""
from ..memory import taking

PRIORITY = 1000  # above the knowledge base and the small talk, below loss, grief and safety


def respond(text, memory):
    """The answer to a bare "what can i take", about the thing the chat is on, or None."""
    return taking.reply_for(text, memory) or None


def takes_as_it_comes(text, memory):
    """Only on the bare ask, and only where the chat has a complaint in it to answer about."""
    try:
        return bool(taking.the_ask_and_the_subject(text, memory))
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False


# The store is above this module (7000) and answers a bare ask out of the words alone - the
# packing question, the duty-free allowance, a hedge about the last answer - so the whole of the
# claim is declared here: on this line, and this line only, the answer about the thing the chat is
# on is the turn. Read by the arbiter (`bot/modules/arbiter.py: DECLARED_AS_IT_COMES`).
TAKES_AS_IT_COMES = takes_as_it_comes
