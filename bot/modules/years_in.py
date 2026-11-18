"""How long they have been at the job they filed, said back as something worth a word.

    im a teacher
    i have been doing it for 10 years

The first turn is answered well. The second was answered by the greeting fallback with "Got it -
you have been doing it for 10 years" - the line said back with a receipt on it. It knows nothing
about the job filed a turn ago and nothing about what ten years means, and it is the whole reply:
no warmth, nothing to say next. Telling someone how long you have stuck at something is a bid to
talk about it, not a fact being filed.

`bot/memory/years_in.py` holds the reading and the wording. This module is the turn it is asked
on: a band above the chat module, so the length is answered as the follow-up it is, and the store's
own readers keep every other line. `respond` returns None on a line it is not about, so a chat
with no job in it, or a line with a feeling or a question in it, is answered as it was before.
"""
from ..memory import years_in

# Above the chat module (300), which answered the length as small talk, and above the knowledge
# base (0), whose entries have nothing to look up for a line that names no subject of its own.
PRIORITY = 1150


def respond(text, memory):
    """The reply for a line that is only how long they have been at their job, else None."""
    if not isinstance(memory, dict):
        return None
    return (years_in.the_years_in_the_doing(text, memory)
            or years_in.the_years_in_their_doing(text, memory) or None)


def takes_as_it_comes(text, memory):
    """This line is a length I read whole, so it is answered as it comes.

    Without the hook the specialist rule hands the turn to the knowledge base: "ive been teaching
    for 20 years" is read as a school line by the word "teaching", the cooking entry declares the
    area too, and an oven-dish card answered it. The claim says what is true - this line is the
    length of the job the chat already filed, and nothing else in it is a subject to look up.
    """
    if not isinstance(memory, dict):
        return False
    return bool(years_in.the_years_in_the_doing(text, memory)
                or years_in.the_years_in_their_doing(text, memory))


TAKES_AS_IT_COMES = takes_as_it_comes
