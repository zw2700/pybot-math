"""The meat a card uses as an ingredient, when the vegetarian version is one word.

Every row in the kitchen is written for everyone, and a row that is about something else can still
name meat in passing: "how do i make gravy" is answered by a card that starts "Whisk the flour into
the meat juices off the heat before adding stock". `cooking.fits_the_diet` drops any card with a
meat word in it, which is right for a card that is *about* the meat - "how do i roast a chicken"
has nothing to offer a vegetarian - and wrong for a card where the meat is the fat in the pan. The
person in `long-chat-05` said they were vegetarian at turn two and asked how to make gravy at turn
ten, and got nothing.

`DAIRY_SWAPS` in `cooking` already does this one layer in: "softened in butter" is served as
"softened in oil" rather than thrown away. This is the same shape at the meat layer, where the swap
is one word and the instruction does not change:

    meat juices                      -> vegetable juices     (the same pan, same deglazing)
    chicken / beef / ham stock       -> vegetable stock       (the same liquid, same amount)
    chicken / beef / ham stock cubes -> vegetable stock cubes

Two things are deliberately not here. Nothing is swapped on a line that names that food itself:
"can i freeze chicken stock" is a question about chicken stock, which is the pot and not the
question of what they eat. And nothing is swapped in a clause already talking about the plant
version, so "vegetable stock instead of chicken stock" keeps both halves.

A card that is really about a cut of meat is not rescued by this: it still says "roast the
chicken" after the swap, and `fits_the_diet` refuses it exactly as before.
"""
import re

from bot.knowledge import cooking

# This module is a helper, not a domain: no rows of its own, so no `ENTRIES`. An empty list is
# here because every module in `bot/knowledge/` has to say what it is - the loader reads
# `ENTRIES` or `ANSWERS` off each one (`tests/test_knowledge_load.py`), so a module with neither
# is one that has been quietly dropped. `notable.py` keeps its rows in a second file and carries
# the same line.
ENTRIES = []

MEAT_IN_A_CARD_SWAPS = (
    (re.compile(r"\bmeat juices\b", re.I), "vegetable juices"),
    (re.compile(r"\b(?:chicken|beef|ham|turkey|lamb|pork|fish)\s+stock\b", re.I),
     "vegetable stock"),
    (re.compile(r"\b(?:chicken|beef|ham|turkey|lamb|pork)\s+stocks?\s+cubes?\b", re.I),
     "vegetable stock cubes"),
)

# The two families this is for, in the words `cooking.avoids` answers with.
MEAT_OR_FISH = ("meat", "fish")


def swapped_out(text, line="", avoided=None):
    """The reply with the meat it uses as an ingredient swapped, or `text` unchanged.

    Only ever called for a person who does not eat meat or fish, and only ever widens what they
    can be served: a card with no meat word in it is untouched, a clause already about the plant
    version is untouched, and a line that named the food keeps the food.
    """
    if not isinstance(text, str) or not text.strip():
        return text
    if avoided is not None and not (set(avoided) & set(MEAT_OR_FISH)):
        return text
    if cooking.PLANT_SAID.search(text):
        # Written for a vegetarian already; there is nothing here to make more vegetarian.
        return text
    said_here = str(line or "").lower()
    for pattern, swap in MEAT_IN_A_CARD_SWAPS:
        if pattern.search(said_here):
            # They named that food, so this card is answering about that food.
            continue
        # The clause splitting is the same one the dairy swaps use, so a sentence that already
        # says "vegetable stock" is left as it is.
        text = cooking._rewritten_outside_swaps(text, pattern, swap)
    return text
