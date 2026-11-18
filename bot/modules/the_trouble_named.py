"""A thing named as the trouble is the subject of the next turn, so the reply asks which way it is.

"Its the electric thats the problem", "the problem is the car", "its my wifi thats the problem",
"the trouble is the hot water" all reached the intake form - "I'm listening - say more if it
helps", "Got it. Is there anything you'd like a hand with?" - which hands the subject back and
asks for nothing. The pool in `bot/compose/the_trouble_named.py` says the two ways that thing
goes wrong and asks which one it is, because the next step is different for each.

PRIORITY is the floor of the floor: above the greeting band, below every module that gives a
person something to do. A card that already answers a boiler, a leak, a dead car or a council tax
question keeps its turn - "the problem is the council" is a Citizens Advice pointer and "its the
boiler thats the problem" is the plumber line, and a question is only ever better than a shrug, not
better than an answer. A body part, a pet and anything else stay as they were: the pool returns
None for them.
"""
from ..compose import the_trouble_named as pool

# Above greeting (-1000), below the floor modules that give a next step (-999, -998). At -989 it
# outranked the Citizens Advice line and the plumber line, which is a true answer traded for a
# question - the one trade this module must never make.
PRIORITY = -997


def respond(text, memory):
    return pool.reply_for(text, memory)


def TAKES_AS_IT_COMES(text, memory=None):
    """This module read the line whole as a thing named as the trouble, so it takes it as it comes."""
    return respond(text, memory) is not None
