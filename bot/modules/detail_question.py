"""A detail the person adds, answered by the question it implies.

The floor answers a line with no question in it by saying it back: "theres eight of us at home"
over a party food answer got "Got it - there's eight of you at home", which is nothing added.
The knowledge base does answer the question such a detail implies ("how much food for eight
people", "what should i know before a trip to rome in september"), so the reply a person gets is
that answer (bot/compose/their_detail.py).

It sits above greeting (-1000) and below nudge (-950), urgent and every card, so only the floor's
own turn is at stake: a module that knows the subject answers first, and a line this cannot read
returns None and leaves the turn exactly as it was.
"""
from ..compose import their_detail

PRIORITY = -997  # above greeting (-1000), below nudge (-950) and every module that knows a subject


def respond(text, memory):
    """The answer to the question the detail implies, or None for the floor to answer as before."""
    return their_detail.reply_for(text, memory)
