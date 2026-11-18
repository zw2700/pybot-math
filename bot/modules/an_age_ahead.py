"""An age asked for further ahead is the age the store keeps, moved on.

"my son is 6" then "how old will he be next year" was answered by the store's own card - "You
haven't said - how old will he be next year?" - because the line asks about the conversation the
bot has had rather than about the world, and the store's reading of that claim is the one that
leads the turn. The store keeps one age at one day; a day further ahead is arithmetic on what it
keeps, which no entry and no card can answer.

`bot/memory/aboutthem.py` reads it (`an_age_ahead`), so a child kept in months and a day that names
no length ("next summer", "on his birthday") are left exactly as they were.

Priorities: above the memory store's recall band (7000), because this module's reply is the answer
to the line the store claims, and it declares `CLAIMS_INSTEAD` so the claim is given up only on
the lines where that is true. It sits below the safety band, which must lead on a hard line.
"""
from ..memory import aboutthem

PRIORITY = 7150


def TAKES_AS_IT_COMES(text, memory):
    """This line is the one to answer as it comes: it asks for an age further ahead."""
    return bool(aboutthem.an_age_ahead(text, memory))


def CLAIMS_INSTEAD(text, memory):
    """The store claims this line as about the chat; the answer here is about the child."""
    return bool(aboutthem.an_age_ahead(text, memory))


def respond(text, memory):
    if not isinstance(memory, dict):
        return None
    return aboutthem.an_age_ahead(text, memory) or None
