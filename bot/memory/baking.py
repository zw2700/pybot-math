"""A line that names a kind of cake is a question about that cake, not about its vegetable.

"im thinking of baking a cake" then "what about a carrot cake" was answered with green
vegetables, because the word the entries key on is "carrot" and the entry for carrots is a
side dish. The same line about a coffee cake fell to the search hedge, and "what about lemon
drizzle" reached the entry about drizzling a sauce over a joint. The person is still in the
cake they named three words ago: written out as "how do i make a carrot cake" the line
reaches the cake entries, which answer it.

Only an ask takes this route - a report ("i baked a carrot cake") or a taste ("i love carrot
cake") is not a how-to question, and the turn stays with whatever answers a report. Anything
that is not a compound name of a bake has no line here and passes to the entries untouched.
"""

import re

# The bake at the end of the name: "carrot cake", "banana bread", "cheese scones". A lemon
# drizzle is a cake whose name has no bake word in it, so the two fruit drizzles count here.
NAMED_BAKES = re.compile(r"\b(?:lemon|orange)\s+drizzle\b", re.I)

BAKE = re.compile(
    r"\b(cakes?|loaves|loaf|bread|muffins?|cupcakes?|sponge|buns?|scones?|biscuits?"
    r"|traybake|traybakes?|brownies?)\b",
    re.I)

# An ask about a dish, not a statement about one: "what about a carrot cake", "and a banana
# bread?", "can i make ginger cake", "how about lemon drizzle", "what if i made scones".
ASK = re.compile(
    r"^(?:so\s+|ok\s+|okay\s+|and\s+)?"
    r"(?:(?:what|how)\s+about\s+|(?:and|or|plus)\s+|"
    r"(?:can|could|should|shall|would)\s+(?:i|we)\s+(?:make|bake|do|cook)\s+|"
    r"what\s+if\s+(?:i|we)\s+(?:made|make|bake|baked|cooked|cook)\s+)",
    re.I)

# Filler that can sit on the end of the name without being part of it.
TAIL = re.compile(r"\s+(?:instead|too|as well|then|please|later|tonight|now)$", re.I)

# How many words a bake's name has before the bake word: "carrot", "lemon drizzle",
# "red velvet", "coffee and walnut".
LONGEST = 4

NAME_WORD = re.compile(r"^[a-z][a-z'-]*$", re.I)


def _the_name(noun):
    """The name of the bake in the line without the ask around it, or "" when it is not one.

    "a carrot cake" is kept as it stands so the written-out ask reads as English. Words that
    cannot be part of a bake's name - a verb, a place, a clause - take the whole thing out,
    because "how do i make bake it for an hour" is not a question any entry answers.
    """
    words = [word for word in noun.split() if word]
    while words and TAIL.match(" " + words[-1]):
        words.pop()
    if not words:
        return ""
    named = list(words)
    while named and named[0].lower() in ("a", "an", "some", "another"):
        named.pop(0)
    if not named or len(named) > LONGEST:
        return ""
    for word in named:
        if not NAME_WORD.match(word.strip(".,!?;")):
            return ""
    return " ".join(words).strip(".,!?;:").lower()


# A line that says the oven is missing is not the plain "what about a carrot cake" ask. The lack
# belongs to the name, and writing the line out drops it: "can i bake a cake with no oven" became
# "how do i make a cake with no oven", which reaches the tin times and tells a person with no oven
# to bake at 180C, where the kitchen entries answer a missing appliance (the fridge cake, the
# flatbread, the pan). So the line is left to them.
# ...and only for an appliance. A missing ingredient is the row that was already answering:
# "can i bake a cake with no butter" was the equal-weights sponge, and any lack at all stood that
# row down for the plain tin times, which answer a question about butter with an oven temperature
# (breezy-violet, #7653). The appliance words are the kit whose absence the kitchen entries answer.
APPLIANCES = (r"oven|grill|hob|microwave|air\s*fryer|cooker|stove|range|pressure\s*cooker|"
              r"slow\s*cooker|toaster")
LACKS = re.compile(
    r"\b(?:no|without|not\s+got|dont\s+have|don't\s+have|cant\s+use|can't\s+use)"
    r"\s+(?:a\s+|an\s+|any\s+|working\s+|my\s+)?(?:"
    + APPLIANCES + r")\b"
    r"|\b(?:" + APPLIANCES + r")\s+(?:is\s+|has\s+|has\s+gone\s+)?"
    r"(?:broken|gone|died|had\s+it|packed\s+in)\b", re.I)


def written_out(text, memory=None):
    """The line written out as a how-to about the bake it names, or None to leave it alone."""
    if not isinstance(text, str):
        return None
    line = " ".join(text.strip().split())
    if not line or len(line.split()) > 12:
        return None
    asked = ASK.match(line)
    if not asked:
        return None
    rest = line[asked.end():]
    if not (BAKE.search(rest) or NAMED_BAKES.search(rest)):
        return None
    noun = _the_name(rest)
    if not noun:
        return None
    if LACKS.search(noun):
        return None
    if not (BAKE.search(noun) or NAMED_BAKES.search(noun)):
        return None
    return "how do i make " + noun
