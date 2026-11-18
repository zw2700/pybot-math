"""Occasions: what to take when the food is for someone else's do.

A bring-a-dish question is not a cook-a-dinner question. "What can I bring to a picnic" names no
food and no meal, so nothing reached it and it got the shrug; "what can i make for a bake sale"
reached the ten-minute dinners; "what can i bring to a christening" reached what-to-wear; and
"what can i bring to a friends house for dinner" reached the friend who still owes you money. The
occasion is what the ask is about, so the occasion is the key and the hint is what travels, what
can sit out and what to leave at home.

A line that mentions an occasion without asking what to bring or make is not this entry's line:
"i always take a bottle to a picnic" is a statement, and "what should i take to a job interview"
is not food, so both are left to whatever answers them now.
"""
import re

from bot.knowledge.geography import crosses_a_border
from bot.knowledge.lookup import entry

# A domain says which topics it can answer, the same attribute name a reply module declares.
ANSWERS = ("cooking", "food-and-drink")

# The verb half of the key. "bring" and "take" are the same question in British English, and
# "make" and "cook" and "bake" are how people ask what to turn up with.
BRING_WORDS = ("bring", "brings", "bringing", "take", "takes", "taking", "make", "makes",
               "making", "cook", "cooks", "cooking", "bake", "bakes", "baking",
               # "food for a wake" has no bring word in it, and was reaching the condolence
               # card instead of the traybake: the food is what is being asked about.
               "food", "foods")

# The line has to be asking a question: "i always take a bottle to a picnic" mentions both halves
# and wants no advice.
BRING_ASKS = ("what can i bring", "what should i bring", "what do i bring", "what to bring",
              "anything i can bring", "shall i bring", "should i bring", "do i need to bring",
              "what can i take", "what should i take", "what do i take", "what to take",
              "shall i take", "should i take",
              "what can i make", "what should i make", "what do i make", "what to make",
              "shall i make", "should i make",
              "what can i bake", "what should i bake", "what to bake", "should i bake",
              "what can i cook", "what should i cook", "what do i cook", "what to cook",
              "shall i cook", "should i cook",
              "food for", "food to", "what food", "which food",
              # the ask with no question word in it: "can i bring food into the library" and
              # "im bringing some food to a do tonight" ask the same thing as "what food should
              # i bring", and the guard below keeps the border rules out of it
              "bring food", "bringing food", "bring some food", "bring a plate",
              "bring something to eat", "take food", "taking food")

# One row per occasion: the names people give it, then what to turn up with.
BRING_DISH = (
    # A wake is first: it is the one occasion here where the food is for a family in the middle of
    # something, and it needs a plain answer rather than a cheerful one.
    # "Wake" is the verb as well as the occasion - "what can i make to wake me up" was getting
    # the funeral row - so the names here are the occasions people write ("the wake", "for a
    # wake", "funeral tea") and the bare word is not one of them.
    (("the wake", "a wake", "for the wake", "for a wake", "after the wake", "after a wake",
      "at the wake", "at a wake", "funeral", "funeral tea"),
     "Sandwiches, a big pot of soup and a traybake: food that can sit out and be eaten whenever "
     "people arrive, and that reheats for the family afterwards. Take it in a dish you do not "
     "want back, and offer one specific job - pouring tea, washing up - rather than asking what "
     "you can do."),
    (("picnic", "picnics"),
     "Take something that survives a warm car: a frittata cut in wedges, a salad with the dressing "
     "in the bottom of the jar, or cold roast chicken with a bag of ice packs. Flapjacks and fruit "
     "travel better than anything with cream in it."),
    (("barbecue", "barbecues", "bbq", "bbqs", "barbeque", "cookout"),
     "Take something that needs nothing from the grill: a big bowl of slaw, garlic bread, or "
     "halloumi and vegetable skewers if you want something cooked. Ice and a bottle of something "
     "land harder than another bag of crisps."),
    (("potluck", "pot luck", "pot lucks", "bring and share"),
     "Take a dish that holds its heat and needs nothing at the last minute: a tray of roast "
     "vegetables, a big grain salad, or a chilli to plug in. Ask what is already coming first, so "
     "you are not the third pasta bake."),
    (("bake sale", "cake sale", "cake stall", "school fair", "summer fair", "fete", "fayre"),
     "Traybakes cut into squares travel and sell best: brownies, flapjacks or a Victoria sponge "
     "traybake. Write the allergens on a card and take a tin or a box, because a stall always runs "
     "out of somewhere to put things."),
    # The occasions where the ask is about food for a table. A housewarming, a birthday party, an
    # engagement party and a baby shower are on purpose not here: those four are a *present*, and
    # the bot already answers them that way ("ask the host if there is anything they need", the
    # muslins and board books for a baby), so a plate of cheese straws would be a worse answer.
    (("buffet", "buffets", "christening", "christenings", "hen do", "leaving do", "retirement do",
      "naming ceremony", "leaving party", "retirement party"),
     "Cold things that hold for an hour and need no oven: cheese straws, mini quiches, cocktail "
     "sausages, hummus with breadsticks, and a bowl of something green. Two hot trays are plenty, "
     "and everything else can be made the day before."),
    # "for dinner" alone is the shape "what should i take to my friends for dinner" and "to my
    # mums for dinner": the person's name is what varies, so the phrase is the meal, and the
    # carry word guard below is what keeps "what can i cook for dinner" off this row.
    (("dinner party", "dinner parties", "friends house", "friends place", "friend house",
      "their house", "round for dinner", "over for dinner", "for dinner at", "for dinner"),
     "Take a bottle and something for after - a pudding, cheese and biscuits, or a box of "
     "chocolates - so you are not competing for their oven. Ask what they are cooking, then bring "
     "the thing that goes with it."),
)

# "What can i cook for dinner at my mums" is a cooking question with a place in it, not a thing to
# take to someone else's do: the host group needs a bring or a take before it counts.
BRING_HOST_NAMES = ("dinner party", "dinner parties", "friends house", "friends place",
                    "friend house", "their house", "round for dinner", "over for dinner",
                    "for dinner at", "for dinner")
BRING_CARRY_WORDS = ("bring", "brings", "bringing", "take", "takes", "taking",
                     "made", "bought", "picked", "ordered")

# What a line is asking about when it is not asking about food. "should i take my dog to a bbq" and
# "should i take my baby to a bbq" put an occasion next to a bring, so they reached this entry and
# were handed a bowl of slaw. The thing being taken is the subject there, and it is a pet, a person
# or a piece of kit, so the entry steps aside and the line keeps whatever answers it now. The names
# are the phrases people actually write, not the bare nouns: "hot dogs for a bbq" is a dish.
#
# A person is the one case that needs the verb with them. The awkward match is loose, so a bare
# "my friend" also caught "what can i bring to my friends house for dinner" - the dinner-party
# line this entry exists to answer. The guest shape below keeps that line and still steps aside
# for "should i take my friend to a picnic".
BRING_GUESTS = ("take my friend", "bring my friend", "my friend to", "my friend along",
                "my friend come", "bring a friend", "take a friend", "my friend with me",
                "take my partner", "bring my partner", "my partner to", "my partner along",
                "take my husband", "bring my husband", "take my wife", "bring my wife",
                "take my mum", "bring my mum", "take my mother", "bring my mother",
                "take my dad", "bring my dad", "take my father", "bring my father",
                "take my parents", "bring my parents")

# A trip has its own card - the picnic, the hike, the camping kit list - and a bowl of pasta
# salad is not what you carry round a beach or up a hill. "what food should i take to the beach"
# was the picnic card until this row started answering every bring ask, which is what a reviewer
# caught: the words are the journey, not the destination, so "can i bring food to the beach" is
# still somebody asking what to carry, just not what this row carries.
_TRIP = ("beach", "the beach", "road trip", "the park", "park", "walk in the woods", "the woods",
         "mountain", "mountains", "hike", "hiking", "rambling", "long walk", "walk", "camping",
         "campsite", "campervan", "caravan", "day out", "day trip", "journey", "for the journey",
         "car journey", "train journey", "wild swim", "on the river", "up a hill")

BRING_NOT_FOOD = (("my dog", "the dog", "our dog", "my cat", "the cat", "my baby",
                   "the baby", "our baby", "my kids", "my children", "my son", "my daughter",
                   "wheelchair", "buggy", "pushchair", "pram", "car seat",
                   "my phone", "my laptop", "my camera")
                  + BRING_GUESTS + _TRIP)

_NOT_A_DISH = ("how much", "how many", "how often", "how long")

# The host is the other half of this domain. Every hint here is written for a guest - "take "
# something that survives a warm car", "take it in a dish you do not want back" - so a person
# giving the do was being told what to bring to somebody else's. "im hosting a barbecue what
# should i make" was handed the slaw, and "what shall i make for a christening tea" was handed
# the guest buffet when a christening tea is a spread the family puts on together. The host says
# so in words, and those words are the stand-down.
_HOST_OWN = ("im hosting", "i'm hosting", "we're hosting", "were hosting", "im having",
             "i'm having", "we're having", "were having", "im throwing", "i'm throwing",
             "im putting on", "i'm putting on", "im organising", "i'm organising",
             "im organizing", "i'm organizing", "hosting a", "hosting an")

# A make-ask about a spread is also the host's: "what shall i make for a christening tea" and
# "what should i cook for a dinner party" name the meal that is being put on, not a dish to carry.
# A bring or a take in the line puts it back - "what can i bring to a christening tea" is a guest
# offering a plate - and so does an occasion with no spread word in it ("what should i cook for
# the wake", "what can i make for a bake sale").
_MAKE_ASKS = ("shall i make", "should i make", "shall i cook", "should i cook",
              "can i make", "should i bake", "shall i bake")
# ... and the same ask with the food word in front and the person in the "for": "what food should
# i cook for ten kids" is the host's question, and so is "what to cook for 20 people".
_COOKING_ASKS = _MAKE_ASKS + ("can i cook", "to cook for", "to make for", "to bake for",
                              "should i cook for", "what should i cook", "what can i cook",
                              "what to cook", "what should i make", "what can i make",
                              "what to make")
_SPREAD_WORDS = ("tea", "spread", "buffet", "lunch", "dinner", "supper", "brunch")


def _same(word, wanted):
    """One word equals another, allowing a plural: "picnics" is "picnic"."""
    word = str(word).lower().strip("'")
    wanted = str(wanted).lower()
    if word == wanted:
        return True
    return word in (wanted + "s", wanted + "es") or wanted in (word + "s", word + "es")


def _words_of(understood):
    said = understood.get("words") or []
    if not isinstance(said, list):
        said = str(said).split()
    clean = str(understood.get("clean") or "")
    return re.findall(r"[a-z0-9']+", (" ".join(str(word).lower() for word in said) + " "
                                      + clean.lower()))


def what_to_bring(memory, understood):
    """The occasion the line names decides what travels."""
    clean = str(understood.get("clean") or "").lower()
    # A quantity is the crowd table's question: "how much should i bring for 20" is a number of
    # sandwiches, not a choice of dish.
    if any(phrase in clean for phrase in _NOT_A_DISH):
        return None
    words = _words_of(understood)
    # The host's own do: every hint below is written for a guest.
    if any(phrase in clean for phrase in _HOST_OWN):
        return None
    if (any(phrase in clean for phrase in _MAKE_ASKS)
            and any(phrase in clean.split() for phrase in _SPREAD_WORDS)
            and not any(_same(word, carry_word) for word in words
                        for carry_word in ("bring", "take"))):
        return None
    carry = any(_same(word, carry_word) for word in words for carry_word in BRING_CARRY_WORDS)
    # The person is asking where to go, not what to turn up with: "where should i take her for
    # dinner" is a place, and the "for dinner" in it is the evening, not a dish for a host.
    if str(understood.get("wants") or "") == "place":
        return None
    asker = any(phrase in clean for phrase in BRING_ASKS)
    # The dish below is what you carry to somebody else's table; it is not what you cook. "what
    # food should i cook for ten kids" and "what food should i cook for a kids party" are the
    # host's questions - the fish fingers, the cheap party food, the one big oven dish - and this
    # row answered them with the guest's pasta salad, because "what food" is one of its asks. A
    # make word with no bring or take in the line is the host's, and the cooking rows answer it.
    if any(phrase in clean for phrase in _COOKING_ASKS) and not carry:
        return None
    for names, hint in BRING_DISH:
        for name in names:
            if name in BRING_HOST_NAMES and not carry:
                continue
            parts = name.split()
            for start in range(len(words) - len(parts) + 1):
                if all(_same(words[start + offset], parts[offset])
                       for offset in range(len(parts))):
                    return hint
    # No occasion named, and the line asks what to bring or make: the dish to carry is the same
    # answer as for any of them. A food word is in the key, so the ask has to be a bring-or-make
    # ask here, and a present or a border rule is another row's line.
    if (asker and not crosses_a_border(clean)
            and not any(phrase in clean for phrase in _NOT_A_DISH_TO_CARRY + _TRIP)):
        if any(_same(word, food) for word in words for food in GENERIC_FOOD):
            return _ANY_DISH
    return None


# The ask with no occasion in it: "what food should i bring", "what food should i bring into the
# library". Most people never name the do at all, and the dish to carry is the same answer whether
# it is a barbecue, a buffet or somebody else's kitchen - so the food words are in the key, and
# the hint below answers a line that asks what to bring and names no occasion.
GENERIC_FOOD = ("food", "foods", "dish", "dishes", "plate", "plates", "something to eat")

# A food word alone is not this row's line: it still has to be a bring-or-make ask (BRING_ASKS
# above), it must not be a present, and it must not be a rule about a border - "can i bring food
# into the eu" is the customs row's, and "what food should i bring to a job interview" is nobody's.
# A border is not this row's line, and neither is a present or a journey: the border reading is
# shared with travel.py's customs row (`geography.crosses_a_border`), so the two rows cannot
# disagree about "can i bring food into brazil" - one of them had it as an import rule and the
# other as a dish to carry. What is left here is the places and questions that are not a do.
_NOT_A_DISH_TO_CARRY = ("birthday", "birthdays", "housewarming", "house warming", "engagement",
                        "baby shower", "wedding", "christening present", "present", "presents",
                        "gift", "gifts", "interview", "work", "office", "fridge", "freezer",
                        "on the plane", "on a plane", "flight",
                        "through security", "hand luggage", "cabin bag",
                        # a place that does its own food, and a journey with a rule of its own:
                        # "can i bring my own food to a restaurant" and "can i take food on a
                        # ferry" were a dish to carry, which is not what either one asks
                        "restaurant", "restaurants", "cafe", "cafes", "the pub", "takeaway",
                        "ferry", "on the ferry", "on a ferry", "on the train", "on a train",
                        "on the coach", "on the bus")

_ANY_DISH = ("Take something that needs nothing from anyone else's kitchen: a big bowl of pasta "
             "salad, a tray of sausages or a quiche, cheese and crackers, or a traybake cut into "
             "squares. Nothing with cream in it if it will sit out, and take it in a dish you do "
             "not need back. If the host says not to bring anything, take a bottle or something "
             "for after - and ask what is already coming so you are not the third pasta bake.")

OCCASION_NAMES = tuple(name for names, _hint in BRING_DISH for name in names) + GENERIC_FOOD

ENTRIES = [
    entry("bring-dish", (BRING_WORDS, OCCASION_NAMES), what_to_bring, ask=BRING_ASKS,
          avoid=BRING_NOT_FOOD, bias=1),
]
