"""An animal somebody keeps is a pet, not a cut of meat.

The pantry answers a staple by name and the storage rows answer a "keep", so the lines about a
kept animal were answered as if it were dinner: "how do i look after a rabbit" got the braise
("a rabbit wants either a long braise or a fast roast"), "what do i feed a rabbit" a method for
cooking one, "how do i keep chickens" the shelf life of cooked chicken, "how do i look after a
duck" the watering of a houseplant, and "how do i look after a goat" a punt.

What makes the line a keeper's is the pair: an animal people keep, and one of the care words that
belongs to keeping it. Each animal has its own basics card - what to house it in, what to feed it
and the one thing a new keeper gets wrong - and the pan words are stood aside so "how do i cook a
rabbit" and "rabbit stew" stay with the kitchen.
"""
import re

from .lookup import entry

# The words a keeper uses about an animal they have taken on or are thinking of taking on.
_KEEPING_ASKS = ("look after", "looking after", "care", "caring", "care for", "keep", "keeping",
                 "own", "owning", "feed", "feeding", "fed", "what to feed", "hutch", "coop",
                 "pen", "shed", "house", "housing", "run", "need", "needs", "new", "starter",
                 "basic", "basics", "setup", "set up", "want", "wants", "getting", "start with",
                 "how many", "how much", "space", "room", "size", "licence", "license",
                 "register", "permit", "as a pet", "a pet", "my pet")

# The kitchen's words, and the illness and money words other rows own, so a kept animal's card is
# only served to a line about keeping it. "how long can i keep chicken in the fridge" is a shelf
# life, and "is my hen sick" is the vet's question, so both stand this table aside.
# Each word is matched whole, not as a piece of a longer one: "licence" holds the letters of
# "lice", "grill" those of "ill", and a plain substring test answered "do i need a licence to
# keep chickens" as if the birds had mites. The money words are matched whole for the same
# reason, so "how much space does a goat need" is a keeper's question while "how much does a
# goat cost" stays with the price rows.
_KEEPING_AVOID = ("cook", "cooking", "cooked", "roast", "roasted", "recipe", "recipes", "curry",
                  "stew", "stews", "braise", "bake", "baked", "grill", "fry", "fried", "raw",
                  "sick", "sickness", "ill", "illness", "unwell", "vet", "dying", "died", "dead",
                  "injury", "injured", "limping", "lice", "mites", "worms", "worming",
                  "price", "cost", "costs", "buy", "buying", "sell", "selling", "worth",
                  "fridge", "freezer", "freeze", "left out", "leftover", "leftovers", "store",
                  "storage", "eating", "eat it", "to eat", "for dinner", "on the menu")

_AVOID = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in _KEEPING_AVOID) + r")\b",
                    re.I)

_ASKS = re.compile(r"\b(?:" + "|".join(re.escape(word) for word in _KEEPING_ASKS) + r")\b",
                   re.I)

def keeping_an_animal(understood):
    """True when the line asks how to keep an animal, rather than how to cook one.

        how do i look after a rabbit   -> a keeper's question, not the braise
        what do i feed a rabbit        -> a keeper's question
        how do i keep chickens         -> not the shelf life of cooked chicken
        how do i cook a rabbit         -> the kitchen keeps this line
        rabbit stew                    -> and this one
        how long can i keep chicken in the fridge -> cooked chicken, not a hen
    """
    if not isinstance(understood, dict):
        return False
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    text = str(said).lower()
    if not text:
        return False
    if _AVOID.search(text):
        return False
    return bool(_ASKS.search(text))


# The animal's name, the card, and the extra words its own row stands aside for: a hen's eggs, a
# duck's confit and a goose at christmas are the kitchen's lines, not the keeper's.
ANIMALS = [
    (("rabbit", "rabbits", "bunny", "bunnies", "doe", "buck"),
     "rabbit-care",
     "A hutch the size of a small shed, not the one in the shop: a rabbit needs a run it can "
     "stand up in and stretch out in, plus a covered sleeping box, and it wants company - two "
     "rabbits, a neutered pair, is kinder than one. Hay all day, a handful of greens, a spoon of "
     "pellets, and water in a bottle rather than a bowl. Handle it every day from the start: a "
     "rabbit that is picked up rarely will scratch to get down.",
     # The pets table already has the rabbit's food card ("Hay is the diet: a pile the size of
     # the rabbit..."), and it answers "what do i feed a rabbit" better than a card about the
     # hutch, so the food asks are left to it.
     ("braise", "braised", "roast", "jointed", "saddle", "bacon", "wine", "stock", "bones",
      "feed", "feeding", "fed", "what to feed", "diet")),
    (("chicken", "chickens", "hen", "hens", "ex battery hens", "ex-battery", "cockerel",
      "rooster", "coop", "hen house", "henhouse"),
     "hen-basics",
     "Three hens is the smallest sensible flock, in a coop with a nest box and a perch each, and "
     "a fox-proof run of about a square metre per hen. Layers' pellets, grit and clean water, and "
     "shut them in at dusk - the fox comes at night, and a hen that is out is a hen that is gone.",
     ("egg", "eggs", "laying", "lay", "lays", "broody", "meat", "breast", "thigh", "skin")),
    (("duck", "ducks", "drake", "drakes"),
     "duck-basics",
     "Ducks want a house to sleep in and water deep enough to dip a whole beak, so a tub they can "
     "climb out of does a pond's job. Layers' pellets and grit, bedding changed often because "
     "they are far messier than hens, and the same shutting in at dusk.",
     ("confit", "pancake", "pancakes", "orange")),
    (("goose", "geese", "gosling", "goslings"),
     "goose-basics",
     "Geese want grass to graze, a shelter they can walk into and a lot of space, and two at the "
     "least. They are good watch animals and very messy, and a gander will chase people in the "
     "breeding season, so keep them away from a path small children use.",
     ("christmas", "foie", "down", "fat")),
    (("goat", "goats", "kid goat", "kid goats", "pygmy goat", "billy", "nanny goat"),
     "goat-basics",
     "Goats are herd animals, so two at the least: one on its own is a distressed goat. They want "
     "a dry shed, a fence they cannot lean on and something to climb, hay and browse all day, a "
     "mineral lick, and their feet trimmed every couple of months.",
     ("milk", "cheese", "curd", "meat", "butter", "yoghurt", "yogurt")),
    (("quail", "quails"),
     "quail-basics",
     "Quails want a hutch or aviary with a solid floor, a deep layer of bedding and somewhere to "
     "hide, and a pair or a small group rather than one. Gamebird crumb with extra calcium for "
     "layers, and a low roof: they fly straight up when startled.",
     ("meat", "roast")),
    (("pigeon", "pigeons", "racing pigeons", "fantails"),
     "pigeon-basics",
     "Pigeons want a loft with perches, a landing board and open sky in front of it, and a pair is "
     "happier than one. A pigeon mix, grit and clean water, and out at the same time each day so "
     "they learn the way home.",
     ("shoot", "shooting", "pest", "roof", "spikes", "poo", "droppings")),
]

# One animal's card is not another animal's answer. "how much space does a goat need" reached
# the rabbit card, because a hutch is a hutch and nothing in the words said which animal was
# meant, so each row stands aside for every other animal's name: the goat's own row takes the
# line, and a keeper who names a rabbit still gets the hutch.
_ALL_NAMES = [name for names, _card, _reply, _extra in ANIMALS for name in names
              # Three letters is too short to fence with: the table matches these as pieces of
              # longer words, so "doe" would stand the goat's card aside on "does" and "hen" on
              # "when". The longer names carry the fence on their own.
              if len(name) > 3]

ENTRIES = [
    entry(card,
          (names, _KEEPING_ASKS),
          reply,
          avoid=_KEEPING_AVOID + tuple(extra) + tuple(
              name for name in _ALL_NAMES if name not in names),
          bias=2,
          guard=keeping_an_animal)
    for names, card, reply, extra in ANIMALS
]
