"""A line that says where they work is answered with the job the chat already holds.

`bot/memory/workplace.py` reads the line; this module is the turn it is asked on. Priorities:
the general helpful band, above `answers` (0), so a workplace line is not answered by the
pre-school-places card the words "primary school" reach, and below the loss, grief and safety
bands, which must lead on a hard line.
"""
from ..memory import workplace

PRIORITY = 1150


def TAKES_AS_IT_COMES(text, memory):
    """This line is the one to answer as it comes: it says where the person's work is.

    `answers` claims a line whose words reach one of its entries - "primary school" reaches the
    pre-school-places card - and a claim is given up only to a module that says the line is its
    own answer at a higher PRIORITY. This is that module for a workplace line.
    """
    return bool(workplace.the_place_the_person_works(text, memory))


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    return workplace.the_place_the_person_works(text, memory)
