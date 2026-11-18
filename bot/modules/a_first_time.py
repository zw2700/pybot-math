"""A first time is a task, not a first taste.

"how do i give a talk at work" then "ive never done one before" got "I'm listening - say more if it
helps", which is no help at all to somebody standing in front of the thing. This answers it with
the one thing that is true of every first (bot/compose/a_first_time.py), and sits above greeting
(-1000) and below nudge (-950), urgent and every card, so only the floor's turn is at stake.
"""
from ..compose import a_first_time

PRIORITY = -996  # above greeting (-1000), below nudge (-950) and every module that knows a subject


def respond(text, memory):
    """What helps a first time, or None for the floor to answer as before."""
    return a_first_time.reply_for(text, memory)
