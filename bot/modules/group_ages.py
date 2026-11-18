"""The ages of a group of people, said back as the list the person gave.

    my parents are 66 and 70
    how old are they            ->  Your parents are 66 and 70.

    my two kids theyre 4 and 7
    how old are they again      ->  Your kids are 4 and 7.
    how old is my youngest      ->  Your youngest is 4.

Found late in a chat on main `f05d1112`. The store keeps one age for the person in the chat
(`memory["their_age"]`), so a line that gave two kept the first and dropped the rest: `how old are
they again` answered "They are 4.", `how old are my kids` answered "You haven't told me how old
they are.", and a chat with two parents in it said nothing about either. A list of two is not one
number, and it is not nothing.

The reading and the wording live in `bot/memory/groupages.py`, which keeps the list under
`memory["group_ages"]`. This module exists rather than a branch inside
`bot/modules/memory_store.py` because that file is past the world's size cap and cannot be
uploaded (the same reason as `bot/modules/trip_date_said_again.py`).

It answers nothing a chat has not said: with no list in the store it returns None and the line
goes on to the module it went to before this one existed, which is what keeps a first line - where
there is no memory at all - answered as the line it is.
"""
from ..memory import groupages

# Above the store (7000): on this line the store's own answer is either one age out of the list or
# a hedge about a list it could have read. Everything else passes, because the reader fires only
# when the chat holds a list and the line asks for it.
PRIORITY = 7050

# A family question, so the module is read as one of the family specialists: the same label the
# store declares, which is what lets the tie keep the higher PRIORITY.
ANSWERS = ("family-and-parenting",)


def observe(text, memory):
    """Keep the list a line gives (bot/memory/groupages.py)."""
    try:
        groupages.watch(text, memory)
    except Exception:  # noqa: BLE001 - an observer must never lose a turn
        return


def respond(text, memory):
    """The ages the chat holds, said back, or None for every other line."""
    if not isinstance(memory, dict):
        return None
    try:
        return groupages.reply_for(text, memory) or None
    except Exception:  # noqa: BLE001 - a reading that fails answers the line as it did before
        return None


def TAKES_AS_IT_COMES(text, memory):
    """Only on an ask about a list the chat holds, and nowhere else."""
    if not isinstance(memory, dict):
        return False
    try:
        return groupages.asks_for_the_list(text, memory)
    except Exception:  # noqa: BLE001 - a hook that raises claims nothing
        return False
