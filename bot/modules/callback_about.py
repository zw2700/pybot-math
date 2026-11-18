"""Asking after a person the chat already holds: answer with what the chat holds.

The reading and the wording are in `bot/memory/callback.py`. This is the module that offers it,
and it is a module of its own for the reason `theirperson` is one: the shape is a shape, and a
hook in the seed fallback would have to grow a branch for the next one.

PRIORITY 260 puts it above `answers` (0) and below `chat` (300) and `theirperson` (250 is below
it, and both stand down unless the line is their shape). What it can take is the answer to
`how is she doing`, which without it was the last paragraph the chat had already had, headed
"Same as before"; what it cannot take is a line with its own reading.
"""
from ..memory import callback

PRIORITY = 260


# A person the chat holds can be the subject of any of these, and a card that declares the same
# topic answers the follow-up as the thing it already answered (`answers`, 0) unless this module
# scores on the topic too: the topic match is what settles the turn here, not PRIORITY. The
# labels are the understanding engine's own (`bot/understanding/topics.py`), hyphens and all:
# "family and parenting" declares nothing and loses the turn, which is how `my mum is 82` then
# `how is she doing` got the council care-package card instead of the age the chat holds.
ANSWERS = (
    "family-and-parenting",
    "friends-and-relationships",
    "health",
    "work",
    "school-and-study",
    "pets",
)


def respond(text, memory):
    return callback.reply_for(text, memory) or None


def CLAIMS_INSTEAD(text, memory):
    """The ask after a person the chat holds, where a module below claims the follow-up."""
    return callback.claims(text, memory)
