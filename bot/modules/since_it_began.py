"""A length asked for is the length the chat already told: "how long have i been at it".

The day a thing began is in the store - "i started running in march", "i moved to leeds two years
ago", "i started a new job last month" - and the ask that wants the length back names nothing of
its own, so every reader of the words alone answered off the words:

    i started running in march                / how long have i been at it  -> "20 minutes."
    i started learning spanish in january     / how long have i been doing it
      -> "About 600 hours of real study to hold a proper conversation in Spanish - around 2 years"
    i moved to leeds two years ago            / how long have i lived here
      -> "I don't know enough to answer that honestly."

The reading and the wording live in `bot/memory/when.py` (`how_long_answer`): today minus the day
the line names, said the way a person says a length, with the day beside it. This module is the
turn it is asked on.

Priorities: the general helpful band, above `answers` (0), so the length the store holds is not
answered by the entry whose words reach it, and below the loss, grief and safety bands, which must
lead on a hard line.
"""
from ..memory import when

PRIORITY = 7500  # above the store's receipt cards, below safety


def TAKES_AS_IT_COMES(text, memory):
    """This line is the one to answer as it comes: it asks for a length the chat already gave."""
    if not isinstance(memory, dict):
        return False
    return bool(when.how_long_answer(text, memory))


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    answer = when.how_long_answer(text, memory)
    return answer or None
