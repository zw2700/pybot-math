"""Land and title: who owns a piece of ground, and how you find out.

The answers lane owns this domain. The rows are here rather than in `home.py` because
`home.py` is where every property line already lands: an append to a file that a dozen other
answers change every day is a merge conflict waiting to happen, and the ground and the
register that records who holds it are a domain of their own, not one more thing about a
kitchen.

The Moon stays out of this row by its own avoid list ("moon", "planet", "space", "orbit",
"satellite"): "who owns the moon" is a space question, and `history.py`'s `moon-landing` keeps it.
"""
from .lookup import entry

# A land question reaches the home topic (the title register is where a property owner starts),
# and the money one (about £3 for the title, and a boundary dispute is a solicitor's bill).
ANSWERS = ("home-and-diy", "money")


ENTRIES = [entry(
    "who-owns-some-land",
    (("who owns", "who owned", "land registry", "title register", "title deeds", "deeds",
      "piece of land", "plot of land", "land next to", "land behind", "field behind",
      "property boundary", "boundary line", "boundary dispute"),
     ("land", "plot", "field", "boundary", "deeds", "register", "property", "garden", "hedge",
      "owns", "owner", "mine", "next door", "neighbour", "neighbors")),
    "In England and Wales the owner is on the title at HM Land Registry: use its Find a property "
    "service, pay about £3, and the title register gives you the owner's name, the price last paid "
    "and the boundaries on a map, without telling them you asked. Scotland is Registers of "
    "Scotland, and Northern Ireland is Land and Property Services. If the plot is unregistered, "
    "the deeds are with the owner or held by the Land Registry, and your council can help you "
    "find out who to ask.",
    avoid=("what is", "what are", "whats", "what does", "meaning", "difference between",
           "define", "explain", "sell", "selling", "sold", "buy land", "buying land",
           "build on", "permission", "planning permission", "mortgage", "stamp duty", "tax",
           "inheritance", "will", "squatter", "adverse possession", "trespass", "fence cost",
           "how much", "cost of",
           # "who owns the moon" is a space question, and "who owns the moon land" is worse: the
           # register is for ground on this planet.
           "moon", "planet", "space", "orbit", "satellite",
           # buying is a different question with a solicitor in it: what the register is for is
           # finding out who owns a plot that is not yours to buy yet.
           "buy a piece of land", "buy some land", "buy land", "buying a piece of land",
           "buying some land", "buying land"),
    # "how do i find my property boundary" went to the card about boundaries with a child,
    # because a boundary line and a boundary for a child are the same word; the property words
    # in this key are what make the tie this row's.
    bias=1)]
