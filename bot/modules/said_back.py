"""A detail given earlier is said back when the person asks for it again.

    its on the outside of the knee, just under the bone          (turn 2)
    and which knee was it          before  the whole iliotibial band card, said again
                                   now     You said: "its on the outside of the knee, just
                                           under the bone"

The reading is `bot/memory/lineback.py`: it only answers the shapes people use to ask for
something said earlier, and only when a line they typed carries the words of the ask. So a
knowledge question is left to the entries, and a recall ask the store answers from a fact it
keeps is left to the store, which says it in the person's own words already.
"""
from ..memory import lineback

# Below the store (7000), which answers the recall asks about a fact it keeps, and above the
# entries (0) and the small talk (300): a line asking for something said earlier is not a
# question about the world, so the card that fits its words answers a question nobody asked.
PRIORITY = 350


def respond(text, memory):
    return lineback.reply_for(text, memory)


# No `TAKES_AS_IT_COMES`: a claim on the line is settled above the bands, and it took turns the
# store already answered from what the person said - "my sister is vegan" / "what did i say my
# sister eats" came back as "my sister is coming to stay next week". The store is above this
# module (7000 to 350), so a fact it keeps is said back in the store's own words.
