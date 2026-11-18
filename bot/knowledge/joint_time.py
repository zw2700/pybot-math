"""A joint asked about by its weight: the roast timetable, not the diet card.

`bot/knowledge/cooking.py`'s `roast-joint` row wants the joint named, either as a cut ("joint of
beef", "leg of lamb") or as the pair ("roast joint"). "How long does a 2 kilo joint take" names
neither: it has a weight, the word "joint" and a time. So it matched no cooking row at all, and
fell to the diet advice, whose key carries a weight word and the word "how".

The row here is that one shape - the bare "joint" with a weight - and nothing else. A line that
names its meat ("how long do i cook a joint of beef for") still goes to `roast-joint`, and the
avoid list keeps a knee out of it, because an aching joint is a body before it is a dinner.

The timetable itself is not copied: `_roast_joint` is asked for the answer it would give a named
joint, so the two rows cannot drift apart. This is its own module rather than an edit to
cooking.py because cooking.py is at the 1 MB file wall.

The answers lane owns this file; pass a line you do not answer rather than guessing.
"""
from bot.knowledge.cooking import JOINT_BEEF, JOINT_PORK, _roast_joint
from bot.knowledge.lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# What `_roast_joint` says when the line names no meat at all: beef and lamb, then pork.
_BOTH = JOINT_BEEF + " " + JOINT_PORK

# A line that names no meat gets the short pork half. The long one puts the crackling's "for the
# first 25 minutes" in a sentence of its own, and a follow-up ("how long does a 3 pound joint
# take in the oven") is answered with the part of the last answer it asks for - which then comes
# back as "25 minutes.", the crackling's time and not the joint's. The figures here are
# JOINT_PORK's, and a test checks them against it.
_PORK_IN_SHORT = "Pork is 30 minutes a 500g at 180C (160C fan) and 70C in the middle."


# A slow cooker is its own timetable, and no oven figure saves it: the line needs the hours, the
# liquid and the temperature it is done at.
_SLOW_COOKER = (
    "A joint up to 2 kilos takes 6 to 8 hours on low, or 4 to 5 on high: stand it on a trivet or a "
    "bed of onion and carrot with 150 to 250ml of stock, and keep the lid on. Pork is done at 70C "
    "inside; a joint you want to pull wants 90C, which is another few hours on low. No crackling in "
    "a slow cooker - finish that under a hot grill.")


# A weight and a meat, with no cut named, is the same question as a bare "joint": "how long do i
# roast a kilo of pork" named no joint at all, so it reached nothing and fell to the honest shrug
# while "how long does a 2 kilo joint take" was answered. The phrase pairs the weight with the
# meat, so a weight on its own ("a kilo of mince", "kilos of potatoes") still matches nothing
# here, and a named cut ("pork chops", "pork belly") keeps its own row.
_WEIGHTS = ("kilo", "kilos", "kg", "kgs", "kilogram", "kilograms", "pound", "pounds")
_MEATS = ("pork", "beef", "lamb", "veal", "mutton", "ham")
# "2kg of beef" is one token ("2kg"), not a number and a unit, so the written figure is spelled
# out for the weights people actually buy: a 1 to 9 of them. "how long does 2kg of beef take" was
# the steak-searing card.
_NUMBERS = ("1", "2", "3", "4", "5", "6", "7", "8", "9")
_BY_WEIGHT = (tuple(weight + " of " + meat for weight in _WEIGHTS for meat in _MEATS)
              + tuple(number + unit + " of " + meat
                      for number in _NUMBERS for unit in ("kg", "kgs", "lb", "lbs", "G")
                      for meat in _MEATS))


def _joint_by_weight(memory, understood):
    """The timetables come from cooking.py, so the two rows cannot drift apart."""
    said = _roast_joint(memory, understood)
    if said == _BOTH:
        return JOINT_BEEF + " " + _PORK_IN_SHORT
    return said

_SLOW_WORDS = ("slow cooker", "slow cook", "slowcooker", "slow-cooker", "crockpot", "crock pot",
               "crock-pot")


# Gammon is the recipe card's ("simmer 20 minutes per 500g, then glaze it in a hot oven"), which
# is the better answer to "how long does a gammon joint take". In a slow cooker there is no
# simmering, so those lines are this row's and the oven ones stand it down. Ham is not in here:
# "how long does a ham joint take" is the pork timetable, which this row already gave.
def _not_a_gammon_in_the_oven(understood):
    words = " ".join(str(w) for w in (understood.get("words") or []))
    if "gammon" not in words:
        return True
    return any(phrase in words for phrase in _SLOW_WORDS)


def _joint_time(memory, understood):
    """One row for every joint time question: the slow cooker has its own hours, the oven its own."""
    words = " ".join(str(w) for w in (understood.get("words") or []))
    if any(phrase in words for phrase in _SLOW_WORDS):
        return _SLOW_COOKER
    return _joint_by_weight(memory, understood)


ENTRIES = [
    # The two timetables are one row on purpose. As two rows, a slow cooker question followed by
    # "how long does a 2 kilo joint take" answered the second with "6 to 8 hours." - the part of
    # the slow cooker answer it asked for - because the last answer was about a joint too.
    entry("joint-time",
          # The bare word "joint" is the whole first group: a weight alone ("a kilo of mince",
          # "kilos of potatoes") must not reach a roasting timetable. The second group is the
          # asking half, because those words say the joint is being cooked rather than eaten.
          # "joint" alone. A shoulder or a brisket is a slow roast and cooking.py's own
          # slow-roast row answers those ("4 to 5 hours" at 150C), so naming them here would
          # take a right answer away and give it the fast timetable; they are in the avoid.
          (("joint", "gammon", "ham") + _BY_WEIGHT,
           ("how long", "time", "roast", "roasting", "oven", "temperature", "cook", "cooking",
            "minutes", "done", "kilos", "kilo", "kg", "kgs", "pounds", "pound", "lbs",
            "slow cooker", "slow cook", "slowcooker", "slow-cooker", "crockpot", "crock pot",
            "crock-pot")),
          _joint_time,
          avoid=(
              # a named cut or joint is the roast-joint row's, which reads the meat better
              "joint of", "roast joint", "leg of", "shoulder of", "beef joint", "pork joint",
              # a bird is a bird, and gammon has its own oven timing - but a gammon joint in a
              # slow cooker was the honest shrug, and this row is the slow cooker's timetable
              # (the guard below keeps the oven question with the recipe card).
              "chicken", "turkey", "duck", "goose", "bird", "mince",
              # a knee is not a dinner, and a slow roast is a different timetable
              "my joint", "joints hurt", "joint pain", "knee", "knees", "hip", "hips",
              "shoulder hurts", "shoulder", "shoulders", "brisket", "briskets",
              "slow roast", "slowly", "low and slow", "overnight", "pulled",
              # a calorie question wants a number, not a timetable
              "calorie", "calories", "kcal", "how many calories",
              # and neither does a price: "how much is a kilo of pork" was answered with the pork
              # timetable once the weight and the meat were enough to reach this row
              "how much is", "how much are", "how much does a kilo", "price", "prices",
              "cost", "costs", "per kilo", "a kilo cost", "cheapest", "cheaper", "offer",
              "on offer", "supermarket", "butcher charge",
              # a frozen joint is a thawing question, a resting one is the resting row's, a
              # joint in the fridge is the keeping row's, and joints that heal are a body
              "defrost", "defrosting", "thaw", "thawing", "frozen", "freeze", "freezer",
              "from frozen", "rest", "resting", "rests", "rested", "keep", "keeps", "keeping",
              "fridge", "ice", "icing", "heal", "healing", "heals", "recover", "recovery"),
          guard=_not_a_gammon_in_the_oven),
]
