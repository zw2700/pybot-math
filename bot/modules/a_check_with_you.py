"""A check of a plan against the bot gets the agreement, not a search hedge or a receipt.

"u ok with that", "are you ok with that", "you good with that plan", "does that work for you" -
seven different placeholder landings for one shape (see bot/compose/check_with_you.py). The
person is not asking about the world, so no card can answer it, and a question back ("what would
you like to do?") hands the decision back to someone who has just made it.

It sits at PRIORITY -999: above the greeting band, which is where all seven of those landings
come from, and below every module that knows a subject. So a card, the small talk and every
safety line keep their turn, and only a fallback line is ever replaced.
"""
from ..compose import check_with_you

PRIORITY = -999


def respond(text, memory):
    """The agreement line, or None when this is not a check-with-you question."""
    return check_with_you.answer_for(text, memory)
