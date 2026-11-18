"""A pot is not a patch of ground, and the frost question about it is a different one.

`do i need to bring my pots in tonight` was answered with the allotment-rules card: the word `pots`
took the line to the tenancy of a plot and nothing in it was about a plant. `should i bring my pots
inside` was a shrug. The cards that do know about frost answer a *plant in the ground* - water the
soil, cover the tender plants, leave the blackened leaves alone - and the one thing that matters
for a container is the one thing none of them says: a pot freezes from every side, so its roots sit
above the frost line and a night that a border shrugs off can kill a plant in a tub.

So the question is read as the move, not the word: the line has to ask about bringing something in,
moving it, or leaving it out, and only then is a pot or a tender plant what it is about. A plant
that has already frozen is the frost-damage card's question, and a pot that will "survive the
frost" is the watering card's, so both are left alone.
"""

import re

from .lookup import entry

ANSWERS = ("garden-and-plants",)

# What is in a pot, and the tender things people move every autumn. A bare `plant` is not here: the
# borders are plants too, and the frost cards answer those.
_IN_A_POT = ("pots", "pot", "plant pots", "patio pots", "containers", "container", "tubs",
             "tub", "planters", "planter", "hanging baskets", "window boxes", "geraniums",
             "geranium", "pelargoniums", "fuchsias", "begonias", "bedding plants",
             "tender plants", "bay tree", "bay trees", "olive tree", "olive trees",
             "lemon tree", "citrus", "agapanthus", "canna", "cannas", "dahlias",
             "succulents", "houseplants", "house plants")

# The cold, and the moves people make for it.
_THE_COLD_AND_THE_MOVE = ("frost", "frosts", "frosty", "freezing", "freeze", "cold", "cold snap",
                          "tonight", "overnight", "winter", "wintering", "snow", "minus",
                          "bring in", "bring inside", "take in", "move", "moving", "moved",
                          "leave out", "left out", "outside", "indoors", "inside", "shelter",
                          "stay out", "over winter", "in", "in for the winter")

# The ask: a move, a cover, or the night. Without one of these the line is about a plant that has
# already been caught - "my plant pots have frozen" - or about surviving a frost, and those cards
# know their own answer.
_ASK = ("bring in", "bring them in", "bring it in", "bring inside", "bring my", "take in",
        "take them in", "move", "should i move", "leave out", "leave them out", "covered",
        "cover them", "cover my", "tonight", "overnight", "too late", "stay out",
        "over winter", "leave out", "left out", "bring my")

# A plant that has already been through the frost is the damage card's: blackened leaves and soft
# stems are read after the fact, and "leave it alone until spring" is the answer it gives.
_HAS_ALREADY_FROZEN = re.compile(
    r"\b(?:have|has|had|got|been|is|are|was|were)\s+(?:been\s+)?(?:frozen|caught|blackened|dead)\b"
    r"|\bblackened\b|\bdead\b|\bdied\b|\bkilled\b", re.I)


def _the_night_is_still_coming(understood):
    """True while the frost is still ahead of the line, which is when moving a pot is the answer."""
    said = ""
    if isinstance(understood, dict):
        said = str(understood.get("text") or understood.get("clean") or "")
        if not said:
            words = understood.get("words")
            said = " ".join(str(word) for word in words) if isinstance(words, (list, tuple)) else ""
    return not _HAS_ALREADY_FROZEN.search(str(said or ""))


_REPLY = ("Bring them in if you can, because a pot freezes from every side: the roots sit above the "
          "frost line, so a night that a border shrugs off can see off a plant in a tub. If they "
          "are too heavy to move, stand them together against a house wall on pot feet, wrap the "
          "pot rather than the leaves in bubble wrap or a sack, and push them under the eaves - "
          "grouping them and getting them out of the wind does most of the work. A forecast of 2C "
          "or below at ground level is the one to act on, and anything tender left out after that "
          "is worth bringing in for good.")

ENTRIES = [
    entry("a-pot-is-not-a-border",
          (_IN_A_POT, _THE_COLD_AND_THE_MOVE),
          _REPLY,
          # The allotment card was taking "do i need to bring my pots in tonight" on the word
          # `pots`, and a hedge was taking "should i bring my pots inside"; both are on score
          # alone, so the card that reads the ask stands above them.
          bias=3,
          ask=_ASK,
          guard=_the_night_is_still_coming,
          # A pot that has broken, a pot to cook in, a pot of paint and a plant to buy are other
          # questions, and so is a plot.
          avoid=("cracked", "broken", "chip", "chipped", "glaze", "terracotta pot broke",
                 "repot", "repotting", "potting on", "compost", "soil", "saucepan", "casserole",
                 "slow cooker", "paint", "plant pot saucer", "buy", "price", "cheap", "where can i",
                 "allotment", "plot", "tenancy", "greenhouse heater", "heater", "paraffin")),
]
