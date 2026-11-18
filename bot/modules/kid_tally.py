"""The number of children, counted from the children the chat already holds.

`my son is 6` and `and my daughter is 9` are two children with their ages, and `how many children
do i have` after them was answered "You've mentioned your son - how many have you got
altogether?". No line said a number, so the store's count stayed empty, and it answered about the
one child it could see. The children are in the chat all the same.

`bot/memory/kidcount.py` holds the reading and the wording; this module is here so the claim
has a band of its own. It answers only the ask, and only when the store has no number of its own:
every other line, and a chat that said how many, is left to the store exactly as before.
"""
from ..memory import kidcount

# Above the store (7000): the ask for a number is a recall question, and on this one line the
# store's own answer is a hedge about a count it could have read. Everything else passes.
PRIORITY = 7050

# The children are a family question, so the module is read as one of the family specialists:
# the same label the store declares, which is what lets the tie keep the higher PRIORITY.
ANSWERS = ("family-and-parenting",)


def respond(text, memory):
    """The count said back, or None."""
    try:
        return kidcount.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None
