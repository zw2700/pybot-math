"""The icing on a cake: how long it keeps, where to keep it, and whether it freezes.

The commonest question about a frosting is not how to make one - it is whether it can be made
tomorrow, whether it survives the fridge and what to do with what is left. Every one of those is
a keeping question about the icing, and the icing is a subject of its own: buttercream is not the
cake, and the numbers are different (a cake keeps 3 days in a tin; a buttercream keeps 3 to 4 days
in a tub in the fridge and 2 months in the freezer).

Why a domain of its own: "frost" is the first four letters of "frosting", and a short key word
matches the start of a longer line word so that "friend" reaches "friends". That made the icing
the wrong kind of frost in three tables at once - the garden's frost cover answered "how do i
store the frosting", the freezer's defrost card answered "can i keep the frosting in the fridge",
and the general cooked-food keeping table answered "how long does frosting last in the fridge".
Each of those rows can be fenced in its own file, and each fence then has to be repeated for the
next row added beside it. Naming the icing as its own subject here is the one change that gives
the icing question an answer of its own, whichever of those rows is next to take the words.

The ask words are the keeping words and never the icing itself, so one row answers all of the
phrasings: "how long does the icing last", "can i keep the frosting in the fridge", "should
buttercream be kept in the fridge", "does the ganache freeze", "can i make the icing the day
before". The bag of icing sugar in the cupboard is not an icing on a cake, and sugar paste and
royal icing set rather than keep soft, so each has its own row or its own fence.
"""
import re

from .lookup import entry

ANSWERS = ("cooking-and-food",)

# The icings and frostings people ask about. "frosting" and "icing" are the same thing said two
# ways, so both are here, and the words that only appear when an icing is meant are here too -
# "buttercream" is a frosting and never anything else.
ICING = ("frosting", "frostings", "icing", "icings", "buttercream", "butter cream", "ganache",
         "cream cheese icing", "cream cheese frosting", "glace icing")

# The keeping ask, in every shape it is asked. These say what is being asked, never what about,
# so the same tuple belongs on every row below.
# The appliance is deliberately not one of these. "How do i stop my freezer frosting up" is a
# line about a freezer that keeps the word "frosting" as its verb, and a keeping ask is what
# says an icing is being kept: the fridge and the freezer are only where it goes.
ICING_KEEP = ("keep", "keeps", "keeping", "kept", "last", "lasts", "lasting", "how long",
              "store", "stores", "stored", "storing", "freeze", "freezes", "frozen",
              "overnight", "room temperature", "ahead", "ahead of time", "day before",
              "night before", "make it the day before", "make ahead", "sit out", "sat out",
              "left out", "out overnight", "shelf life", "still ok", "still good", "gone off",
              "go off", "goes off")

# "Frosting up" is what a freezer does, and the icing row is not about a freezer.
_FROSTING_UP = re.compile(r"\b(?:frosting|frosted|icing|iced) up\b|\bice building up\b", re.I)


def _not_a_freezer_frosting_up(understood):
    """False when the line is a freezer frosting up rather than an icing being kept."""
    line = (understood.get("clean") or understood.get("text") or "")
    return not _FROSTING_UP.search(line)

# What is not the icing on a cake. Icing sugar, sugar paste and a frosting mix are things from a
# packet, and the icing on a cake is not what is being asked about when the sugar is.
NOT_THE_ICING = ("icing sugar", "sugar paste", "frosting mix", "buttercream powder",
                 "powdered sugar", "confectioners sugar", "fondant icing sugar")

# Royal icing and sugar paste set hard rather than keep soft, so the tub in the fridge is the
# wrong answer for them: the fridge is what makes them go sticky.
SET_ICING = ("royal icing", "sugar paste", "writing icing", "piping icing", "ready to roll icing",
             "glace icing", "glacé icing", "fondant", "marzipan")

ENTRIES = [
    # The buttercreams: kept in a tub, not on the cake, and brought back to room temperature
    # before it goes on. This is the same advice the cake plan carries, in the place the question
    # looks for it, so it answers whether or not a cake was mentioned.
    entry("icing-keeps",
          (ICING, ICING_KEEP),
          "Buttercream or ganache keeps 3 to 4 days in a sealed tub in the fridge, or 2 months "
          "in the freezer: thaw it in the fridge overnight and beat it again, because it splits "
          "when it is cold. Cream cheese frosting is the short one at 2 to 3 days, and it does "
          "not freeze well. Keep an iced cake in a tin rather than the fridge, where it sweats.",
          avoid=NOT_THE_ICING,
          guard=_not_a_freezer_frosting_up,
          bias=3),
    # Anything that sets: it wants a cool dry cupboard, not a fridge.
    entry("icing-that-sets",
          (SET_ICING, ICING_KEEP),
          "Royal icing sets hard: keep it in an airtight tub at room temperature for about 2 "
          "weeks, or freeze it for up to 3 months, and cover the surface with cling film "
          "straight away because it starts to crust as soon as it meets the air. Sugar paste "
          "keeps 2 to 3 weeks in a sealed bag, and a drop of water is what revives a dry one. "
          "Neither belongs in the fridge - the damp makes both go sticky.",
          avoid=NOT_THE_ICING,
          bias=3),
]
