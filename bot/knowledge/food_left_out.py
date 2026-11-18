"""A plate left out: the clock, for the line that names no food at all.

"How long can food sit out", "left out of the fridge all night is it ok", "I left my lunch out on
the counter" - the keeping rows in cooking.py answer these for a food that is named ("the chicken
was left out all night is it safe" gets the chicken card, with its own clock) and cannot answer
them when no food is named, because their key is the food. Until this row existed those lines
came back as small talk: the reading heard "left out" as being left out of the group and the
composer said "Loneliness is rough." to somebody asking about their dinner.

So the key here is the state - left out, sat out, out of the fridge, out on the counter - and the
reply is the general rule that holds whatever the food is. A named food is held out in AVOID, so
the food's own card keeps every line it can answer and this row answers only what is left: the
line that says "food", "lunch", "dinner", "leftovers", or nothing but the question.
"""

from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# The state the food is in. Each phrasing is something people actually type for a plate they
# meant to put away.
OUT = ("left out", "left it out", "left them out", "sat out", "out of the fridge",
       "out on the counter", "out on the side", "out on the worktop", "on the worktop",
       "left on the counter", "left on the side", "left on the table", "left on the worktop",
       "out overnight", "left overnight", "in my bag", "in my lunch bag", "in my rucksack")

# How the question is asked, or what was left out in the general words - never a food, because a
# named food is the keeping row's own line.
ASKS = ("is it ok", "is it okay", "is it safe", "still ok", "still fine", "still safe",
        "overnight", "all night", "since this morning", "since last night", "can i eat",
        "can i still eat", "ok to eat", "safe to eat", "should i throw", "throw it away",
        "bin it", "gone off", "how long", "keep it", "reheat",
        "food", "lunch", "dinner", "supper", "tea", "meal", "meals", "leftovers", "plate",
        "takeaway", "my food", "the food", "something")

# A card that knows one food knows that food's clock better than this rule does.
NAMED = ("chicken", "turkey", "beef", "pork", "lamb", "fish", "salmon", "prawns", "prawn",
         "ham", "mince", "sausages", "sausage", "bacon", "rice", "pasta", "milk", "cream",
         "cheese", "butter", "yoghurt", "yogurt", "egg", "eggs", "soup", "stew", "curry",
         "gravy", "cake", "bread", "sandwich", "salad", "pizza", "chips", "mayonnaise",
         "mayo", "custard", "quiche", "sushi", "beans", "peas", "potatoes", "lasagne",
         "lasagna", "casserole", "roast", "stuffing", "pate", "prawn cocktail",
         # a made-up bottle has its own clock: two hours from the powder, one once the baby has
         # started it, whatever the room is like
         "formula", "baby bottle", "baby", "bottle", "breast milk", "breastmilk", "milk powder",
         "powdered milk")

# "left out" is also being left out of the team, and "out on the side" is not a plate.
NOT_FOOD = ("team", "group", "friends", "party", "invited", "feel", "felt", "feeling",
            "at work", "school", "playground", "chat", "wedding", "the lads", "the girls",
            "family", "excluded", "ignored", "laughed at", "mentioned", "conversation",
            "phone", "mobile", "keys", "wallet", "purse", "laptop", "charger", "book",
            "washing", "clothes", "laundry", "dog", "cat", "pet", "bin", "recycling",
            "paint", "tools", "bike", "car keys", "parcel", "post", "rubbish", "bins",
            "battery", "medicines", "tablets", "razor", "bleach", "washing up",
            # freshness.py answers the line that says it was a cooked dish or a takeaway ("we
            # got a takeaway last night and left it out, is it still ok" gets the bin verdict),
            # and that card is better than this rule for it.
            "takeaway", "take away", "cooked", "cooking", "roast", "restaurant", "chinese",
            "kebab", "biryani", "doggy bag", "carry out", "ordered in", "delivery")

ENTRIES = [
    entry("left-out-clock",
          (OUT, ASKS),
          "The clock decides, not the look: two hours at room temperature is the limit, and one "
          "hour if the room is hot. Under that, box it and put it in the fridge and use it in the "
          "next day or two. Over it, bin anything with meat, fish, rice, dairy, eggs or a sauce, "
          "because the bugs that make you ill leave the taste and the smell alone and reheating "
          "does not undo it. Bread, cake, biscuits, jam and fruit are the exceptions and keep on "
          "the counter for days.",
          avoid=NAMED + NOT_FOOD,
          # no nudge: the cards that know a food, or that a dish was cooked, are more precise
          # than this rule and must win wherever they can answer.
          bias=0),
]
