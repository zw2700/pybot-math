"""A hot thing asked how long it takes to cool gets a length of time.

Four cards answered "how long does tea take to cool" and each was wrong on its own word: the
shelf-life card said tea does not go off, the caffeine card said five hours, the picnic cool bag
took the rest. Three more hot things had the same fault: "how long does a hot water bottle take to
cool down" was the five-minute easy walk, "how long does boiled water take to cool for a baby" was
a first labour, and "how long does rice take to cool" was how long rice takes to cook.

Each line is the right topic and the wrong shape, so this is a shape row of its own: the thing and
a cooling phrase together, answered with the minutes the heat takes to come down. It lives in a
file of its own because the rows are keyed on a phrase (a cooling verb) rather than on a food, and
because the per-thing times are the part of this that will keep growing.
"""

from .lookup import entry

ANSWERS = ("cooking", "food-and-drink", "family-and-parenting")

ENTRIES = []

# The minute before the one above: a drink straight off the kettle is too hot to sip, and the
# question is how long it takes to come down. Nothing answered it. The shelf-life card took the
# words ("how long does tea take to cool" was told tea does not go off, it goes stale), the
# caffeine card took the coffee ("how long does coffee take to cool down" got the five-hour
# half-life), and the picnic cool bag took the rest ("how long until my tea is cool enough to
# drink"). The cooling words are asked here with a verb or a "to" so that a cool cupboard, a cool
# bag and cooling a pot of stew before the fridge all stay with their own cards, and the dish
# words are stood down because a pot of soup has a cooling rule of its own.
DRINK_COOLING_NAMES = ("tea", "coffee", "cuppa", "brew", "hot chocolate", "mug", "cup", "drink",
                       "kettle", "teapot")

DRINK_COOLING_ASKS = ("to cool", "takes to cool", "take to cool", "cool down", "cooling down",
                      "cool off", "cooling off", "cool enough", "too hot to drink",
                      "too hot to sip", "cool before drinking", "cool before you drink",
                      "cool before i drink", "let it cool", "let my tea cool", "let my coffee cool",
                      "let the tea cool", "let the coffee cool", "let a cup", "let my cup",
                      "let the cup", "let it cool down")

ENTRIES.append(
    entry("a-drink-cooling", (DRINK_COOLING_NAMES, DRINK_COOLING_ASKS),
          "Five to ten minutes in an ordinary room: a drink comes off the kettle at about 90C "
          "and is comfortable to sip at about 60C, and a splash of cold milk takes it down at "
          "once. A wide mug cools faster than a tall narrow one, and standing the mug in a bowl "
          "of cold water does it in a couple of minutes - stir it and test it with your lip, not "
          "a finger. A lid on the mug keeps the heat in, so take it off if you want it sooner.",
          ask=DRINK_COOLING_ASKS,
          # A pot of soup or stew coming down before the fridge is the food-safety card's
          # question, and it has the times for that; "how long does soup take to cool" was this
          # row's drink answer before these words stood it down.
          avoid=("soup", "stew", "curry", "casserole", "broth", "gravy", "porridge", "chilli",
                 "leftover", "leftovers", "in the fridge", "before the fridge", "freezer",
                 "ice", "iced", "cold brew", "ice cream", "fizzy", "soda", "beer", "wine"),
          bias=6))

# A hot thing that is not a drink takes the same question: "how long does a hot water bottle take
# to cool down" was the five-minute-easy-walk card, "how long does boiled water take to cool for a
# baby" was a first labour (eighteen hours), and "how long does rice take to cool" was how long
# rice takes to cook. Each of those is the right topic and the wrong shape, and the answer each one
# wants is the minutes it takes the heat to come down, so the thing and the cooling phrase together
# are the key here.
HOT_THING_COOLING = ("to cool", "takes to cool", "take to cool", "cool down", "cooling down",
                     "cool off", "cooling off", "cool enough", "too hot", "how long until it is",
                     "how long before it is", "cools", "cool before", "cool for")

ENTRIES.append(
    entry("a-hot-water-bottle-cooling", (("hot water bottle", "hottie", "hot water bottles",
                                          "wheat bag", "heat pack"),
                                         HOT_THING_COOLING),
          "A hot water bottle stays warm for four to six hours under the covers, and it is only "
          "too hot for the first twenty minutes or so. If you want it gentler from the start, "
          "fill it from the hot tap rather than the kettle and wrap it in a towel or a pillowcase "
          "- running it under the cold tap for a few seconds does the same. Never fill it with "
          "boiling water for a child or an older person, and check the stopper and the rubber for "
          "cracks before each winter.",
          ask=HOT_THING_COOLING,
          # "how do i cool a hot water bottle down" asks for the action, and the card that says
          # stand it in a jug of cold water answers that better than a table of times: a how-do-i
          # line is steps, not a length.
          avoid=("cost", "price", "much", "buy", "worth", "last", "lasts", "burst", "leak",
                 "smell", "rubber", "how often", "replace", "how do i cool", "how to cool",
                 "how can i cool", "ways to cool", "make it cooler", "cool it down quickly"),
          bias=6))

ENTRIES.append(
    entry("boiled-water-for-a-feed-cooling", (("boiled water", "kettle water", "water for the "
                                               "formula", "water for a feed", "water for the bottle",
                                               "formula water", "sterilised water"), HOT_THING_COOLING),
          "Make the feed within 30 minutes of boiling: the water should still be at least 70C when "
          "it goes onto the powder, because that is what kills anything in it. Then cool the "
          "bottle under a running cold tap or stand it in a jug of cold water - about 10 to 15 "
          "minutes, and shake a drop onto the inside of your wrist to test it. Water that has been "
          "boiled once and left to cool is fine for drinking, but make a fresh feed rather than "
          "reheating an old one.",
          ask=HOT_THING_COOLING,
          avoid=("bath", "bathwater", "hot water bottle", "washing up", "tap water", "hard water",
                 "filter", "kettle limescale", "descale"),
          bias=6))

ENTRIES.append(
    entry("a-pot-of-rice-cooling", (("rice", "cooked rice", "leftover rice"), HOT_THING_COOLING),
          "Spread the rice out on a tray or a wide plate and it is cool enough for the fridge in "
          "about 20 to 30 minutes - a shallow layer, not a deep pan with the lid on. Get it into "
          "the fridge within the hour, keep it no more than a day, and reheat it once, until it is "
          "steaming hot all through. Rice left standing at room temperature is the one to bin, "
          "because of the spores that survive cooking.",
          ask=HOT_THING_COOLING,
          avoid=("how long to cook", "take to cook", "simmer", "boil", "boiling", "absorption",
                 "cup", "grams", "portion", "water ratio", "rice cooker", "pilau", "risotto"),
          bias=6))

