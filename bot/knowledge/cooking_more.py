"""The cooking rows that answer "is it done, why did it do that, what is the plan".

The sections of `cooking.py` from "how you tell it is cooked" to the end of that file, in a file
of their own: `cooking.py` is over the publisher's 1 MiB upload limit (1,082,093 bytes) and the
world refuses any PR whose tree carries a file that big, so every lane that touches cooking food
is blocked. The rows are data rather than code and they are the end of the list, so they move as
one block, the same way `cooking_entries.py` and `home_craft.py` hold rows for their files.

Nothing about the rows changed. `cooking.py` imports this file at the end, where these rows used
to stand, and extends its own list with this one, so the entries are the same entries in the same
order. The helpers this block defines (`follow_up`, `first_plan`, `minutes_said`, ...) come back
with it: other modules ask `cooking.follow_up(...)`, so `cooking.py` puts them in its namespace.

This file is imported by `cooking.py`, never the other way round, so the import of `.cooking` is
at module level only for the tables the rows are built from, and every name it asks for is
defined above the point where `cooking.py` imports this file.
"""
import re

from .lookup import (asks_the_kinds, entry, find,
                     says_it_has_gone_off as _says_it_has_gone_off)

from .cooking import (
    CROWD,
    DAIRY,
    DISHES,
    FOOD_CLASSES,
    MEAL_IDEAS,
    MEAL_PHRASES,
    PANTRY,
    PET_WORDS,
    _INGREDIENT_WORDS,
    _SWAP_ASK,
    _a_brew_not_a_dinner,
    _crowd,
    _table_text,
    _excluded,
    _fold,
    _mentions,
    _occasion,
    _sides,
    side_for,
    dish,
    ingredients,
    meal,
    missing,
    negated_ingredients,
    pointed,
    pointed_at_a_food,
    without,
)

# The rows below are built against this list and put back into `cooking.ENTRIES` there.
ENTRIES = []

# --- a side dish with no dish named ----------------------------------------------------------
# "any ideas for a side dish" and "give me some options for a side dish" named no dish, and the
# sides table reads the dish out of the line: with nothing to read, one of those lines got the
# composer's troubleshooting question ("What usually goes wrong? Start there, not with the whole
# list.") and the other a shrug. What is left to say without a dish is the jobs a side can do,
# which is what makes a plate balance, and it is also the shape of the answer: two of the three.
#
# It stands here, above the rows, rather than at the end of the file: this file is the one every
# cooking PR appends to, so a row added at its end collides with the next lane's row on rebase.
A_SIDE_WITH_NO_DISH = (
    "Two of these three, and the plate balances itself: something starchy (new potatoes, rice, "
    "bread), a vegetable cooked hot and quick (greens with butter, roasted carrots, a sharp "
    "salad), and something cool or sharp to cut through it (yoghurt, pickles, a squeeze of "
    "lemon). So a roast takes potatoes and greens, anything in a sauce takes rice or bread and a "
    "salad, and a barbecue takes coleslaw and pickles.")


def _a_side_or_the_three_jobs(memory, understood):
    """The side for the dish the line names, or for the dish the conversation is cooking.

    "any ideas for a side dish" said after "i'm doing a roast chicken on sunday" is asked about
    that bird: the dish is in the conversation rather than in this line, so the sides table is
    asked about the conversation too (`side_for`), and only a line with no dish anywhere gets the
    jobs a side can do.
    """
    return (_sides(memory, understood) or side_for(memory, understood.get("clean") or "")
            or A_SIDE_WITH_NO_DISH)


ENTRIES.append(entry(
    "a-side-dish",
    (("side dish", "side dishes", "sides for", "sides to", "sides with", "a side for"),
     ("what", "which", "any", "idea", "ideas", "options", "suggest", "suggestion",
      "suggestions", "recommend", "recommendation", "give", "something", "serve", "make",
      "need", "want", "help", "pick", "choose")),
    _a_side_or_the_three_jobs,
    # A pain in the side is not a plate, and neither is a side effect: the sides table fences both
    # itself, and so does the row, because a line that names one of them is somebody else's.
    avoid=("side effect", "side effects", "pain", "pain in my side", "stitch", "left side",
           "right side", "whose side", "side of the road", "sleep on")))



# --- how you tell it is cooked ---------------------------------------------------------------
# "How do I know if the fish is cooked" is not a timer question, so the entries above that hold
# the times do not answer it: the answer is what the meat looks and feels like at the moment you
# take it off the heat. These are the meats people ask that about and have no plan for, so they
# share one shape - the food, then the way the question is asked - and one guard list.
#
# The guard list is what keeps the shape from answering the neighbours' questions. A word about
# keeping, going off, being left out or already cooked is a different entry's turn, "how long" is
# the timing entry's, and a pregnancy or a baby is a food-safety question.
COOKED_THROUGH_WORDS = (
    "know", "knowing", "tell", "check", "checking", "done", "cooked", "cooked through",
    "ready", "how can i tell", "how do i tell", "how do you tell", "when is it done",
    "when its done", "internal", "temperature", "temp", "thermometer",
)
NOT_A_DONENESS_QUESTION = (
    "how long", "minutes", "kg", "per 500g", "recipe", "oven temperature", "gas mark",
    "keep", "keeps", "keeping", "kept", "fridge", "freezer", "freeze", "frozen", "defrost",
    "thaw", "reheat", "left out", "overnight", "leftover", "leftovers", "left over", "already",
    "pregnant", "pregnancy", "baby", "babies", "toddler", "child", "children", "kids",
    "food poisoning", "sick", "ill", "off", "gone off", "fresh", "smell", "smells",
    "burnt", "burnt to", "overcooked", "dry", "tough", "rubbery", "recipe", "what can i make",
    # how to cook a thing is the cooking entry's question, not what "done" looks like
    "how do i cook", "how do you cook", "how to cook", "how do i bake", "how to bake",
    "how do i fry", "how to fry", "how do i roast", "how to roast", "how do i grill",
    "how to grill", "how should i cook", "best way to cook",
)

ENTRIES.append(entry(
    "fish-done", (("fish", "cod", "haddock", "hake", "pollock", "sea bass", "tilapia"),
                  COOKED_THROUGH_WORDS),
    "Fish is done when it flakes at its thickest point and has turned from glassy to opaque all "
    "the way through, and a thermometer in the thickest part reads about 60C. Cod or haddock loins "
    "take 10 to 12 minutes at 200C, and a thin fillet 6 to "
    "8. A fork should slide in with no resistance - if the middle still looks see-through, give "
    "it two more minutes rather than serving it early.",
    avoid=NOT_A_DONENESS_QUESTION))

ENTRIES.append(entry(
    "pork-done", (("pork", "pork chop", "pork chops", "chops", "loin", "gammon", "tenderloin"),
                  COOKED_THROUGH_WORDS),
    "Pork is done when the juices run clear where you pierce the thickest part and a thermometer "
    "reads 71C: a chop can keep the faintest blush of pink in the middle and still be safe, but "
    "not wet, jelly-like meat. A 2.5cm chop takes 4 minutes a side in a hot pan and 5 minutes "
    "resting, and a loin joint roasts 25 minutes per 500g at 200C (180C fan).",
    avoid=NOT_A_DONENESS_QUESTION))

ENTRIES.append(entry(
    "lamb-done", (("lamb", "leg of lamb", "lamb chops", "shoulder of lamb", "rack of lamb"),
                  COOKED_THROUGH_WORDS),
    "Lamb is done by temperature in the thickest part: 55C is pink, 60C is medium, 70C is well "
    "done, and it is juiciest if you take it out 5C under and rest it 10 minutes. A leg roasts 25 minutes per "
    "500g at 180C (160C fan) plus 25 minutes on top, and a chop takes 3 minutes a side for pink.",
    avoid=NOT_A_DONENESS_QUESTION))

ENTRIES.append(entry(
    "beef-done", (("beef", "rib of beef", "rib roast", "roast beef", "beef joint"),
                  COOKED_THROUGH_WORDS),
    "Roast beef is 50C rare, 55C medium rare, 60C medium and 70C well done inside, read in the "
    "thickest part; it climbs about 5C while it rests, so pull it out 5C under what you want and "
    "rest it 15 minutes before carving, and at 220C (200C fan) allow 12 minutes per 500g. A steak "
    "is a pan question, not a roast one.",
    avoid=NOT_A_DONENESS_QUESTION))

ENTRIES.append(entry(
    "turkey-done", (("turkey", "turkey crown"), COOKED_THROUGH_WORDS),
    "A turkey is done when the thickest part of the thigh reads 74C and the juices run clear, not "
    "pink, where you pierce it; the breast reads about 70C by then and carries on cooking as it "
    "rests. Without a thermometer, the leg should move freely in its socket and the skin pull "
    "away easily - then rest it 30 minutes under foil.",
    avoid=NOT_A_DONENESS_QUESTION))

ENTRIES.append(entry(
    "swap-dairy",
    # "dairy free" is the same question as "no milk", and it was a shrug: the milk entry keys the
    # word "milk", which a person cutting out dairy never types.
    (("dairy", "dairy free", "dairy-free", "no dairy", "milk free", "milk-free", "without dairy",
      "lactose", "lactose free", "lactose-free", "plant milk", "oat milk", "soya milk",
      "soy milk", "almond milk"),
     _SWAP_ASK + ("how do i make", "how to make", "how can i make", "what can i eat",
                  "cut out", "cutting out")),
    "Every dairy ingredient has a straight swap: unsweetened soya or oat milk in place of milk, "
    "one for one, olive oil or a dairy-free spread for butter, and soya yoghurt for yoghurt. "
    "Where a recipe wants buttermilk, put a tablespoon of lemon juice in 250ml of plant milk and "
    "leave it ten minutes. Soya is the one with as much protein as milk, so pancakes, porridge "
    "and coffee taste least different with it.",
    # a baby's formula and a calcium question are different answers, and a cheese board is not a
    # recipe
    avoid=("formula", "baby", "babies", "newborn", "breastfeeding", "calcium", "cheese board",
           "how much calcium")))

# "is a banana fattening" was a shrug for every food, and "is chocolate fattening" reached the
# seized-chocolate repair: one food is never the reason, and the answer is the same for all of
# them, so the foods are the key and the reply explains the total.
FATTENING_WORDS = ("fattening", "make me fat", "makes me fat", "make you fat", "makes you fat",
                   "put on weight", "gain weight", "fatten", "too fattening", "fatten me")

ENTRIES.append(entry(
    "fattening-food",
    (("banana", "bananas", "potato", "potatoes", "bread", "pasta", "rice", "nuts", "cheese",
      "eggs", "egg", "avocado", "chocolate", "honey", "fruit", "oats", "porridge", "yoghurt",
      "yogurt", "olive oil", "butter", "milk", "smoothie", "smoothies", "juice"),
     FATTENING_WORDS),
    "No single food is fattening - what decides your weight is the total across the day, so a "
    "banana at about 100 calories is a snack, not a cause. The foods blamed most often are the "
    "ones that go down fast and leave you hungry: bread, pasta, rice and juice. Eat them with "
    "protein and vegetables, or in one sitting rather than all day, and they stop being a problem.",
    # a diet, a target weight and a medical question are their own answers
    avoid=("lose weight", "losing weight", "weight loss", "how much should i weigh", "bmi",
           "diabetes", "diabetic", "keto", "fasting", "calories in", "how many calories",
           "allergy", "allergic", "intolerant", "pregnant", "toddler", "baby", "dog", "cat")))
# "what's a good name for a sourdough starter" is asked for the joke, and the joke is the answer.
# Kept here because nothing else in the tree owns a starter, and the feeding questions already
# have their own entries.
ENTRIES.append(entry(
    "starter-name", (("sourdough", "starter", "sourdough starter", "levain"),
                     ("name", "named", "naming", "call it", "call him", "call her", "call my")),
    ("Bread people go straight for the pun - Doughlene, Clint Yeastwood, Bread Pitt, Jane Dough - "
     "and everyone who asks about it wants the joke, so any name with dough, yeast or rise in it "
     "works. The starter does not care, and saying the name out loud once a day is a good reminder "
     "to feed it."),
    # the question has to be asking for a suggestion: "what is my starter called" is a fact
    # about the person's own starter, and another entry answers it
    ask=("should i name", "should we name", "should i call", "should we call",
         "what should i name", "what should i call", "what to name", "what could i name",
         "suggest", "ideas", "idea", "any name", "good name", "nice name", "name for my",
         "name my", "help me name", "help me pick", "recommend", "come up with",
         "think of a name", "how do i name", "rename", "what would you call"),
    # feeding it, reviving it and what went wrong with it are the starter's own answers
    avoid=("feed", "feeding", "not rising", "didnt rise", "died", "hooch", "grey", "mould",
           "mold", "smell", "start", "begin", "first", "day", "wifi", "band", "cat", "dog",
           "discard", "flour", "water ratio"),
    bias=1))
# "how do i stop a pan boiling over" was a shrug: the staple entries refuse the "boil over" words
# (rice that boils over is their fault answer) and the pan question names no staple at all.
ENTRIES.append(entry(
    "pan-boil-over",
    (("pan", "pans", "pot", "pots", "saucepan", "water", "milk", "pasta", "rice", "soup",
      "sauce", "stock", "porridge", "oats", "stew", "custard"),
     ("boil over", "boils over", "boiling over", "boiled over", "overflow", "overflows",
      "spill", "spills", "spilling", "spilled", "spilt", "stop it", "keep it from")),
    "Turn the heat down so it is a steady simmer rather than a rolling boil, and leave the lid "
    "half on. A wooden spoon laid across the top of the pan breaks the bubbles before they reach "
    "the rim, and a splash of oil or a knob of butter in starchy water (pasta, rice) stops the "
    "foam building. Fill the pan no more than two thirds and stir once at the start. Milk and "
    "tomato sauces catch on the base and then spatter, so stir them and keep them low.",
    # what boils over is the pot, not a recipe or a fault in the food
    # a spill on a surface is the cleaning question, not the pan's: "my child spilled milk on the
    # floor" matched "milk" and "spilled" and got this card, while the same line without a
    # child gets the stain card. The surface words do the standing down, not the child words: a
    # milk pan boiling over is the same question whether or not a baby is in the line, and "my
    # baby milk boiled over" is the one line a parent with a bottle on the hob types - with the
    # child words here it went to the bottle-sterilising card instead.
    avoid=("recipe", "how long", "burnt", "stuck", "sticks", "soggy", "kettle", "boiler",
           "central heating", "radiator", "water tank", "egg", "eggs",
           "floor", "floors", "sofa", "carpet", "rug", "cushion",
           "highchair", "bib",
           # what the water landed on decides: a drink spilled into a remote, a phone or a
           # keyboard is a device that is wet now (`technology.wet-gadget`), and "i spilt water
           # on my remote" was told to turn the heat down and lay a wooden spoon across the pan.
           "remote", "remote control", "phone", "mobile", "iphone", "keyboard", "laptop",
           "tablet", "ipad", "kindle", "earbuds", "headphones", "controller", "console",
           "camera", "speaker", "charger", "tv"),
    ask=("boil", "boils", "boiling", "boiled", "overflow", "spill", "spills", "spilling",
         "spilled", "spilt", "stop", "stops", "stopping", "keep", "keeps", "keeping",
         "prevent"),
    # "how do i keep milk from boiling over" reads as cooked food that is kept ("boiling" is a
    # form of the keeping table's "boiled", and "keep" is its ask), and that table carries a
    # bias, so it won the line. A pan that boils over is this row's question whatever else the
    # line says, so it carries one too.
    bias=2))

# --- five method questions people ask by name, and main answered with a shrug -------------
# A roux, whipped cream, a jointed chicken, a lined cake tin and a frittata are the steps
# inside other dishes, so nothing keyed them: the deck asks all five and every one came back
# as "I'm not sure about that one". Caramelised onions has its own entry on main now.
ENTRIES.append(entry(
    "cream-whip",
    (("cream", "double cream", "whipping cream", "single cream"),
     ("whip", "whipping", "whipped", "stiff", "peaks", "hand", "by hand", "overwhipped",
      "split", "grainy")),
    "Cold cream, a cold bowl and a big balloon whisk: whip in a steady circle, keeping the "
    "whisk under the surface so you beat air in rather than flick it over the side. Double "
    "cream takes 2 to 3 minutes by hand and stiffens just as the trails stop disappearing. "
    "Stop a moment before it looks ready, because it goes grainy fast; a splash of milk "
    "whisked in rescues one that has gone too far.",
    # not "cake" or "recipe": "how do i whip cream for a cake" and "... for a trifle recipe" are
    # the commonest way the line is typed, and those two words only ever stood the entry down.
    avoid=("ice cream", "sunburn", "eczema", "skin", "soup", "sauce", "coffee", "tea",
           "freeze", "frozen"),
    ask=("whip", "whipping", "whipped", "peaks", "stiff")))

ENTRIES.append(entry(
    "chicken-joint",
    (("chicken", "whole chicken", "bird"),
     ("joint", "jointing", "portion", "portions", "cut up", "butcher", "eight pieces",
      "legs", "thighs", "breast off")),
    "Take the legs off first: cut through the skin between leg and body, bend the leg back "
    "until the hip joint pops, then cut through the middle of the joint rather than through "
    "bone. Then take the wings off at the shoulder, and cut each breast away from the "
    "backbone, following the ridge with the knife tip. A sharp knife and a pair of kitchen "
    "scissors for the joints do most of the work, and the carcass goes in the pot for stock.",
    avoid=("raw", "undercooked", "pink", "defrost", "freeze", "worth", "buy", "cheapest",
           "welfare"),
    ask=("joint", "jointing", "cut up", "eight pieces", "portions")))

ENTRIES.append(entry(
    "cake-tin-line",
    (("cake tin", "cake tins", "muffin tin", "loaf tin", "sandwich tin", "tin", "muffins",
      "springform", "springform tin", "loose bottom tin"),
     ("grease", "greasing", "line", "lining", "parchment", "greaseproof", "stick", "sticking",
      "comes out", "release", "loosen", "flour", "floured", "dust", "dusting", "prepare",
      "preparing")),
    "Rub the tin with butter or a flavourless oil, then cut a circle of baking parchment for "
    "the base - a square folded into quarters and trimmed to the corner is the quick way - "
    "and grease that too. For muffins and small tins, grease every cup and dust with flour, "
    "or use paper cases. Run a thin knife round the edge the moment it comes out and leave "
    "the cake in the tin for 10 minutes before turning it out.",
    # A stuck pan on the hob is fix-sticking's, and bread tins and pies are their own answers.
    # A fruit cake is the deep-tin answer's, which is why it is held off below instead.
    # A bundt is its own tin: it has no flat base for a paper circle and wants the paste.
    avoid=("roast", "roasting", "hob", "pan", "frying", "wok", "baking tray", "traybake",
           "bread", "loaf of bread", "fruit cake", "christmas cake", "rich fruit",
           "wedding cake", "simnel", "dark fruit", "bundt", "bundt tin",
           "dry", "dried out", "overcooked", "over-cooked", "crumbly", "flat", "didnt rise",
           "didn't rise", "sank", "soggy", "raw", "uncooked", "burnt", "burned"),
    # "should i flour the tin" and "how do i prepare a cake tin" were a nod and the tin-size
    # measurements: the words of the asking are as much a gate as the words of the thing.
    ask=("grease", "greasing", "line", "lining", "parchment", "greaseproof", "stick",
         "sticking", "comes out", "release", "flour", "dust", "prepare", "should i",
         "do i need", "how do i")))

ENTRIES.append(entry(
    "grease-a-tin-or-pan",
    # the other sense of the word: preparing the tin, not getting the fat off a pan. The
    # second half is only ever about preparing it, so a cleaning line cannot reach this row.
    (("pan", "pans", "tin", "tins", "tray", "trays", "mould", "moulds", "ramekin", "ramekins",
      "cake tin", "loaf tin", "muffin tin", "baking tin", "baking tray", "roasting tin",
      "frying pan", "grill pan", "wok", "dish", "loaf"),
     ("grease", "greased", "greasing", "greaseproof", "parchment", "baking paper")),
    "Rub a thin film of butter or flavourless oil all round the inside with a piece of kitchen "
    "paper. A cake tin also wants a dusting of flour, tapped round and the extra tipped out, or "
    "a lining of baking parchment on the base; a pan or a roasting tin wants only the oil, "
    "wiped on while it is cold.",
    avoid=("clean", "cleaning", "wash", "washing", "scrub", "soak", "burnt", "stuck",
           "get off", "get the fat", "grease off", "remove", "degrease", "season",
           "how long", "oven temperature", "temperature", "recipe", "buy",
           # a scratched or unsafe non-stick coating is a safety question, not preparation
           "non stick", "non-stick", "scratched", "scratches", "scratches on", "safe",
           "unsafe", "replace", "coating", "flaking", "peeling", "still ok", "toxic"),
    # a greasing question is not the bread-baking activity card, which keys "baking tray"
    bias=2,
    ask=("grease", "greasing", "non stick", "parchment")))

ENTRIES.append(entry(
    "frittata",
    (("frittata", "Spanish omelette", "spanish tortilla", "omelette for a crowd",
      "tortilla espanola", "tortilla española", "potato tortilla"),
     ("make", "how", "oven", "bake", "pan", "eggs", "filling", "how many eggs", "serve")),
    "Cook the vegetables or potato first in an ovenproof frying pan until soft, then pour over "
    "6 beaten eggs for a 20cm pan, seasoned and with a handful of cheese if you like. Keep it "
    "on a low heat for 3 to 4 minutes until the edges set, then finish it under the grill or "
    "in a 180C oven for 8 to 10 minutes until the middle is just set. It takes 6 eggs to feed "
    "four, and it is good cold the next day.",
    avoid=("frying pan", "non stick", "non-stick", "buy", "best", "pan set"),
    # "how do i make tortillas" is the corn or flour flatbread, not the omelette: the word
    # alone is not enough to tell them apart, so only the Spanish pairing counts.
    ask=("frittata", "spanish omelette", "spanish tortilla", "how many eggs",
         "tortilla espanola", "espanola", "espanol", "potato tortilla")))

# Flatbreads and a lunchbox that stays cold were the other two everyday asks with no entry:
# the first reached nothing at all, the second the general ack.
# One key, six names, and six different breads: a yoghurt dough makes a naan, but a tortilla is
# flour and water rolled thin, a chapati is wholemeal with no raising agent, and a pitta needs
# yeast because its pocket is steam trapped in a proved dough. One recipe under six names sends
# the person out for the wrong flour, so the bread is read off the line.
_FLATBREAD_KINDS = (
    ("tortilla", ("tortilla", "tortillas", "wrap", "wraps", "fajita", "burrito")),
    ("chapati", ("chapati", "chapatis", "chapatti", "roti", "rotis")),
    ("pitta", ("pitta", "pitas", "pita", "pittas")),
)


def _flatbread_answer():
    """The flatbread the line actually names, or the quick yoghurt one when it names none."""
    def answer(memory, understood):
        said = " " + str(understood.get("clean") or "").lower() + " "
        # a tortilla espanola is the potato omelette, not a flatbread
        if "spanish" in said or "espanola" in said or "espanol" in said or "omelette" in said:
            return None
        for name, words in _FLATBREAD_KINDS:
            if any(" " + word + " " in said or said.strip().endswith(" " + word)
                   for word in words):
                return _FLATBREAD_RECIPES[name]
        return _FLATBREAD_RECIPES["quick"]
    return answer


_FLATBREAD_RECIPES = {
    "tortilla": (
        "Plain flour, salt, a little oil or lard and warm water, nothing else: about 250g of "
        "flour to 150ml of warm water and a tablespoon of oil. Knead for two minutes, rest the "
        "dough under a bowl for 20, then roll each one out as thin as you can. Cook in a dry, very "
        "hot pan for about 30 seconds a side - they want speckles, not browning, or they go crisp "
        "instead of foldable. Press the bubble down with a spatula as it puffs and stack them under "
        "a tea towel."),
    "chapati": (
        "Wholemeal flour and water, no raising agent and no yoghurt: about 200g of wholemeal or "
        "atta to 120ml of warm water, a pinch of salt and a smear of oil. Knead for five minutes "
        "until smooth, rest 20 minutes, roll thin, then cook in a dry pan for a minute a side "
        "until it speckles. Hold it over a flame with tongs for a couple of seconds at the end and "
        "it puffs up."),
    "pitta": (
        "Pitta needs yeast, because the pocket is steam trapped inside the dough: 250g of strong "
        "white flour, 150ml of warm water, 5g of instant yeast, 5g of salt and a teaspoon of oil. "
        "Knead, prove an hour until doubled, then roll out about 1cm thick - too thin and there is "
        "no steam to open it. Bake on a tray as hot as the oven goes, 250C, for about five minutes, "
        "and they puff and hollow as they cool."),
    "quick": (
        "Self-raising flour, a pinch of salt and enough yoghurt or water to make a soft dough: "
        "about 250g of flour to 150g of yoghurt, kneaded for a minute and rested for 10. Roll them "
        "thin, then cook each one in a dry, very hot frying pan for a minute a side until it "
        "blisters and puffs. Keep them under a tea towel while you do the rest, and eat them the "
        "same day; they freeze well between sheets of paper."),
}


ENTRIES.append(entry(
    "flatbreads",
    (("flatbread", "flatbreads", "flat bread", "pitta", "pita", "tortilla wraps", "chapati",
      "naan", "tortilla", "tortillas", "corn tortilla", "flour tortilla"),
     ("make", "making", "recipe", "how", "dough", "pan", "quick", "no yeast", "no oven")),
    _flatbread_answer(),
    avoid=("pizza", "shop", "buy", "buying", "freezer aisle", "gluten", "sourdough",
           "bread maker", "breadmaker"),
    ask=("make", "making", "recipe", "dough", "pan", "quick", "no yeast", "no oven")))

ENTRIES.append(entry(
    "lunchbox-cold",
    # A bare "lunch" is how most people say it: "how do i keep my lunch cold at work" and
    # "how do i keep my lunch cool" were both shrugs while "lunchbox" answered.
    (("lunchbox", "lunch box", "packed lunch", "lunch", "lunches", "sandwiches", "salad",
      "bento",
      # "how do i keep my food cold at work" names no lunchbox and no lunch, and the
      # restaurant-complaint row took it on "my food" and "cold": the keeping words are
      # what make this the same question as the lunchbox one
      "keep my food", "keep the food", "food cold", "food cool", "food at work"),
     ("cold", "cool", "cooler", "ice pack", "warm", "hot day", "stay fresh", "safe", "keep")),
    "Freeze a bottle of water or a small ice pack overnight and put it in the bag with the food, "
    "or freeze the sandwich fillings themselves (hummus, cooked chicken, cheese) and let them "
    "thaw by lunchtime. A bag with a lining holds the cold far better than a paper one, and the "
    "food wants to sit against the cold pack rather than next to it. Rice, cooked meat and "
    "dairy are the things to be strict about: over 5C for more than a couple of hours and they "
    "are not worth eating.",
    # "how do i keep a sandwich from going soggy" is about water, not about cold, and the
    # shelf-life answer it used to get ("about 5 days in the salad drawer") was nonsense
    # The reply is about keeping food cold, so a line that asks for it warm is a different
    # question and is answered by the row below: "how do i keep my food warm" took the cold
    # answer (ice packs, freeze the sandwich fillings) on the words "keep" and "warm".
    avoid=("school bag", "uniform", "homework", "kids won't", "refuse to eat", "soggy",
           "went soggy", "gone soggy", "going soggy", "dressing", "dressed", "wet",
           "food warm", "lunch warm", "keep it warm", "keep them warm", "stay warm",
           "still warm", "food hot", "lunch hot", "keep it hot", "hot lunch"),
    ask=("cold", "cool", "cooler", "ice pack", "warm", "hot day", "stay fresh", "safe", "keep")))

ENTRIES.append(entry(
    "lunchbox-hot",
    # The same question as the row above with the temperature the other way round. A flask is
    # the answer to it, and it is a keeping question rather than a cooking one: "how do i keep
    # my food warm", "how do i keep my lunch hot", "how do i keep food hot for lunch".
    (("lunchbox", "lunch box", "packed lunch", "lunch", "lunches", "food", "soup", "stew",
      "curry", "leftovers", "flask", "thermos", "pie", "pasta", "rice"),
     ("warm", "hot", "still warm", "steaming")),
    "Fill a wide-mouth flask with boiling water for five minutes, empty it, then put the food in "
    "steaming hot and it will still be warm at lunchtime; a tea towel round the flask adds an "
    "hour or two. The middle ground is the risky bit, because food between 5C and 63C grows "
    "bacteria, so reheat it until it is steaming just before it goes in and throw away what is "
    "left at the end of the day.",
    # "keep my food cold" and "the drinks cool on a hot day" are the row above, and a chilli or
    # a fever is hot without being a dinner someone wants kept hot.
    avoid=("cold", "cool", "ice", "freezer", "fridge", "hot day", "hot weather", "sunburn",
           "chilli", "chili", "spicy", "hot sauce", "fever", "temperature", "oven", "bake",
           "baking", "roast", "raw", "defrost", "reheat"),
    ask=("warm", "hot", "still warm", "steaming")))


# --- what makes cut fruit and veg go brown ---------------------------------
# The question is the same for an apple, a pear, a potato and an aubergine: an enzyme in the cut
# flesh meets the air. People ask it as "how do i stop ... going brown", "why do ... go brown" and
# "can i eat ... that has gone brown", and every one of those was a shrug or the pan-browning
# answer, which is a different reaction. The fix is one line of advice per kind of produce, and
# every branch says the same thing about safety, because the worry behind the line is whether the
# food has gone off.
_APPLE_BROWN = (
    "Toss the cut pieces in lemon or lime juice, or dip them in lightly salted water for a minute "
    "and pat them dry, and press cling film right onto the cut faces. It is an enzyme in the flesh "
    "meeting the air, nothing to do with going off, so a browned apple is safe - cut the marks off "
    "and eat it.")

_WET_BROWN = (
    "Drop them into a bowl of cold water as you cut them, with a squeeze of lemon if you have one, "
    "and they will stay pale until they are cooked. It is an enzyme in the flesh meeting the air "
    "rather than spoilage, so browned potato or aubergine is safe - trim the marks and carry on.")

_DRY_BROWN = (
    "Keep the cut face covered with cling film or a drop of lemon juice until you cook it, and "
    "wipe rather than wash if it has to wait, as water makes it slimy. The brown marks are only "
    "air on the flesh, so a browned avocado is safe - cut them away and use the rest.")

# A mushroom is not like the rest: it is brown by nature, and an old one is brown for the opposite
# reason, so the colour says nothing and the test is slime and smell. Saying "browning is only air"
# to "are brown mushrooms safe to eat" is confidently wrong about food safety.
_MUSHROOM_BROWN = (
    "A mushroom darkens as it ages, and that on its own is not spoiling - brush it rather than "
    "wash it, keep it in a paper bag in the fridge, and cook it soon. Slime, a sour or fishy smell "
    "or dark wet patches mean it has gone, so bin those.")

_MUSHROOM_SAFE = (
    "Look at the texture, not the colour: a mushroom is fine while it is firm and dry with a "
    "pleasant smell, brown cap or not. Slimy skin, a sour or fishy smell, or dark wet patches mean "
    "bin it, and cooked mushrooms left out for more than two hours go too.")

_CELERY_BROWN = (
    "Stand cut sticks in a jar of cold water in the fridge, or wrap them tight, and they keep their "
    "colour for a week. Brown edges are just air and water loss, so trim them off and the rest is "
    "fine.")

_PRODUCE_BROWN = (
    "It is an enzyme in the cut flesh meeting the air, so the fix is to keep the air off or make it "
    "acid: lemon juice, a bowl of cold salted water, or cling film pressed onto the cut face. Brown "
    "patches are not spoilage - trim them and eat the rest.")

# A line asking whether the browned thing is still safe wants the verdict first, not the trick
# that stops it browning next time: the trick is the second half of that answer.
_BROWN_SAFE_ASKS = re.compile(
    r"\bsafe\b|\bok\b|\bokay\b|\bstill good\b|\bcan i eat\b|\bcan you eat\b|"
    r"\bthrow (it|them|away)\b|\bstill fine\b", re.I)
_BROWN_SAFE = (
    "It is safe: browning is an enzyme in the cut flesh meeting the air, not spoilage, so trim the "
    "marks off and eat the rest. To stop it next time, keep the air off the cut face - lemon or "
    "lime juice, a bowl of cold salted water, or cling film pressed right onto it.")

_MUSHROOM_WORDS = re.compile(r"\bmushrooms?\b", re.I)

_BROWN_KINDS = (
    (("apple", "apples", "pear", "pears"), _APPLE_BROWN),
    (("potato", "potatoes", "aubergine", "aubergines", "eggplant", "parsnip", "parsnips",
      "artichoke", "artichokes", "salsify", "jerusalem artichoke"), _WET_BROWN),
    (("mushroom", "mushrooms", "chestnut mushrooms", "button mushrooms"), _MUSHROOM_BROWN),
    (("avocado", "avocados"), _DRY_BROWN),
    (("celery", "celeriac"), _CELERY_BROWN),
)


def _produce_brown(memory, understood):
    """The cut-and-brown answer for the fruit or vegetable the line names."""
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    mushrooms = _MUSHROOM_WORDS.search(said)
    if _BROWN_SAFE_ASKS.search(said):
        return _MUSHROOM_SAFE if mushrooms else _BROWN_SAFE
    if mushrooms:
        return _MUSHROOM_BROWN
    for names, reply in _BROWN_KINDS:
        if any(" " + name + " " in said for name in names):
            return reply
    return _PRODUCE_BROWN


ENTRIES.append(entry(
    "produce-brown",
    # A browned potato in the pan is the Maillard answer, so "cook", "fry", "roast", "sear" and a
    # hot pan are all out; so is a garden, where a brown leaf is a plant question, and a banana,
    # which browns by ripening rather than by being cut.
    (("apple", "apples", "pear", "pears", "potato", "potatoes", "aubergine", "aubergines",
      "eggplant", "mushroom", "mushrooms", "celery", "parsnip", "parsnips", "artichoke",
      "artichokes", "fruit", "fruits"),
     ("brown", "browning", "going brown", "went brown", "gone brown", "gone black", "gone dark",
      "going black", "going grey", "going gray", "gone grey", "gone gray",
      "turns brown", "turn brown", "turning brown", "go black", "goes black", "went black",
      "go dark", "oxidise", "oxidize", "oxidation", "discolour", "discolor", "keeps browning",
      "stop them going brown")),
    _produce_brown,
    avoid=("tree", "trees", "plant", "plants", "garden", "growing", "grow", "leaf", "leaves",
           "soil", "basil", "lawn", "cook", "cooked", "cooking", "roast", "roasted", "fry",
           "fried", "frying", "sear", "seared", "maillard", "pan", "hot oven", "oven",
           "meat", "chicken", "beef", "bread", "toast", "ripen", "ripe", "ripening", "banana",
           "bananas", "chips", "crisps"),
    # the pan-browning entry already carries potato and browning, and an apple that has gone brown
    # reached the limp-leaves answer on its own; both are scored at 4, so this one has to be
    # nudged to take the line when the line really is about the cut flesh.
    bias=2))

# A wake and a buffet are the two times people cook for a crowd they cannot see: the number is
# asked as "what do i cook" and the holding as "how do i keep it warm", and neither had an
# answer. Both are about the same job, so they sit together here.
WAKE_WORDS = ("for the wake", "at the wake", "the wake", "funeral tea", "after the funeral",
              "funeral reception", "wake food", "wakes")
HOLD_WORDS = ("buffet", "party", "finger food", "sandwiches", "quiche", "sausage rolls",
              "plates", "dishes")
_HOT_HELD = re.compile(r"\bwarm\b|\bhot\b|\bheat\b|\bheating\b|\bstay hot\b", re.I)
_COLD_HELD = re.compile(r"\bcold\b|\bchill\b|\bfresh\b", re.I)
_AHEAD = re.compile(r"\badvance\b|\bahead\b|\bnight before\b|\bday before\b|"
                    r"\bmake ahead\b|\bprepare\b|\bprep\b", re.I)


# A crowd row answers a question about food. "my neighbour keeps having parties" met the words
# "party" and "keeps" and was answered with the holding temperature of a buffet, and the same
# shape turns up in every line about somebody else's evening: "the people upstairs have parties
# every weekend", "the pub is having a party". The party in those lines is other people's noise;
# this row is the food at one. So a crowd row is only an answer when the line names food, says
# what the food has to do ("keep it warm"), gives a count to cater for, or says the party is the
# asker's own. A list of neighbour words would only fix the wordings somebody thought of.
_FOOD_IN_LINE = frozenset(PANTRY) | frozenset(_INGREDIENT_WORDS) | frozenset((
    "food", "foods", "meal", "meals", "dish", "dishes", "cook", "cooking", "eat", "eaten",
    "buffet", "sandwiches", "sandwich", "quiche", "sausage roll", "sausage rolls", "finger food",
    "nibbles", "canapes", "cake", "soup", "plates", "platter", "spread", "catering", "menu",
    "recipe", "recipes", "bake", "baked", "roast", "salad", "cheese", "crisps", "dips",
    "vegetarian", "vegan", "picnic", "barbecue", "bbq", "pudding", "dessert", "starter"))
_FOOD_JOB = re.compile(r"\b(?:warm|hot|cold|chill|fresh|safe|soggy|sitting out|sat out|"
                       r"left out|stand out)\b", re.I)
_OUR_OWN = re.compile(
    r"\b(?:im|i am|i'm|we are|we're|were|my|our|me and|my wife and i)\b[^.]{0,24}"
    r"\b(?:having|throwing|hosting|organis|organiz|putting on|holding|planning)\b"
    r"|\b(?:my|our|the) (?:party|barbecue|bbq|buffet|wake|christening|wedding) (?:food|spread)\b"
    r"|\bfor \d+ (?:people|guests|heads)\b|\bfor \w+ (?:people|guests)\b", re.I)


# A follow-up says "it" instead of naming the food. The food word was in the turn before, so a
# holding verb with a pronoun for its object is the same question: "how do i keep it warm for a
# party", "how do i keep things warm for a party", "how do i keep them cold". Those lines were
# answered with the portions row, because "it" is not a food word and this guard stood the
# holding row down. The verb is what makes it a pronoun about something held - "is it warm in
# spain for a party" stays out, since nothing is being kept.
_A_PRONOUN_HELD = re.compile(
    r"\b(?:keep|keeps|keeping|kept|hold|holds|holding|stay|stays|staying|stand|stands|"
    r"standing|serve|serves|serving|served|leave|leaves|leaving|left|put|puts|putting)\s+"
    r"(?:[a-z']+\s+){0,2}(?:it|them|that|those|these|things|everything)\b[^.]{0,24}"
    r"\b(?:warm|hot|cold|chill|chilled|fresh|safe)\b", re.I)


def _about_the_food(understood):
    """True when a crowd line is about the food: what it is, or what the food has to do."""
    line = " " + " ".join(str(word) for word in (understood.get("words") or ())).lower() + " "
    words = set(re.findall(r"[a-z']+", line))
    if words & _FOOD_IN_LINE:
        return True
    if _OUR_OWN.search(line):
        return True
    if _A_PRONOUN_HELD.search(line):
        return True
    # "how do i keep it warm for 20 people" names no food, but the clock and the count are the
    # question a buffet is served by: the thing being held is the food.
    return bool(_FOOD_JOB.search(line)) and bool(
        re.search(r"\b(?:people|guests|heads|crowd|everyone)\b", line))


def _wake_food(memory, understood):
    """What to put out at a wake: food people can take with one hand."""
    return ("Food that needs no carving and no serving: sandwiches cut small, sausage rolls, a "
            "quiche, a pot of soup kept hot, cut cake, and plenty of tea. Make it the day before, "
            "allow three or four sandwich pieces a head, and ask two people to keep the teapot "
            "going and the plates moving, because that is the job nobody thinks to do.")


def _buffet_holding(memory, understood):
    """Keeping a buffet hot or cold, and how far ahead it can be made."""
    line = " " + " ".join(str(word) for word in (understood.get("words") or ())).lower() + " "
    if _AHEAD.search(line):
        return ("Make sandwiches the night before, wrapped in the fridge, and leave the salad or "
                "tomato out until the morning because it turns the bread wet. Egg, cheese and ham "
                "fillings keep the best; nothing already filled should sit out for more than two "
                "hours.")
    if _COLD_HELD.search(line) and not _HOT_HELD.search(line):
        return ("Cold food wants to stay under 5C: keep the bowls in the fridge until people "
                "arrive, stand them in a bigger bowl of ice, and put out a little at a time. Rice, "
                "cooked meat and dairy are the things to be strict about, and anything out for "
                "more than two hours goes in the bin.")
    return ("Hot food wants to stay above 63C: a slow cooker on low, an oven on its lowest with the "
            "door ajar, or a lidded pan on a trivet, served in small batches so what is out gets "
            "eaten. Cold food wants to stay under 5C. Anything that has sat between the two for "
            "more than two hours is the food that makes people ill, so bin it.")


ENTRIES.append(entry(
    "wake-food",
    ((WAKE_WORDS),
     ("cook", "food", "make", "serve", "bring", "sandwiches", "tea", "catering", "buffet",
      "much", "how many", "feed", "after", "reception")),
    _wake_food, bias=2, guard=_about_the_food,
    # Someone grieving is the loss answer's turn, not the buffet's: only the cooking shapes here.
    # And a baby is not a funeral: "my baby wakes every hour" and "waking for feeds at 8 months"
    # reached this row on the word "wake", which is a verb about a night feed before it is tea
    # after a funeral.
    avoid=("died", "death", "passed away", "grief", "grieving", "miss her", "miss him",
           "sympathy", "condolences", "what do i say", "what to say", "eulogy", "speech",
           "baby", "babies", "newborn", "newborns", "infant", "infants", "toddler", "toddlers",
           "my baby", "night feed", "night feeds", "waking for feeds", "weaning",
           # an age in months is a child even when the line never says "baby": "is it normal for
           # a 9 month old to wake for a feed" is the night-waking question, not a tea.
           "month old", "months old", "week old", "weeks old", "year old", "years old",
           "wake for a feed", "wakes for a feed", "wake for feeds")))

ENTRIES.append(entry(
    "buffet-holding",
    ((HOLD_WORDS),
     ("keep", "warm", "hot", "cold", "chill", "advance", "ahead", "night before", "day before",
      "make ahead", "prepare", "prep", "safe", "left out", "sit out", "stay fresh")),
    _buffet_holding, bias=2, guard=_about_the_food,
    # The food ideas are a different question with the same words: "what can i make for a party"
    # wants a menu, and this one is about the hour before people arrive.
    avoid=("ideas", "idea", "suggest", "suggestions", "what can i make", "what should i make",
           "menu", "cheap", "recipe", "recipes", "how much food", "how many sandwiches",
           "how much do i need", "how many do i need",
           # A sandwich that goes soggy is water, not temperature: "how do i keep a sandwich
           # from going soggy" was answered with a slow cooker holding food at 63C. The wet
           # answers are `soggy-lunch` and the vegetable water row.
           "soggy", "going soggy", "goes soggy", "went soggy", "gone soggy",
           "soggy bottom", "wet", "dressing", "dressed",
           # "how do i keep kids busy at a party" has "keep" and "party" and nothing about food:
           # keeping them busy is the games, and this row answers the temperature of a buffet
           "kids", "kid", "children", "child", "toddlers", "toddler", "games", "game", "play",
           "playing", "activities", "activity", "busy", "entertain", "bored", "occupy",
           # A party next door is noise, not catering: "my neighbour keeps having parties" met
           # "party" and "keeps" and nothing about food, and it was answered with the holding
           # temperature of a buffet. A party somebody else is having is the nuisance letter;
           # a party in the line without food words is somebody looking for the number.
           "neighbour", "neighbours", "neighbor", "neighbors", "next door", "next-door",
           "upstairs", "downstairs", "flat above", "flat below", "loud music", "noise", "noisy",
           "keeps having", "keeps throwing", "every weekend", "all night", "all hours")))
# Most kitchens have these already, so a dish that needs one is not a shopping trip.
STAPLES = frozenset("""garlic onion salt pepper oil butter flour milk stock lemon tomato
cheese bread""".split())

# The pantry ingredients that are meat or fish, for a vegetarian plan.
MEAT_NAMES = frozenset("chicken mince sausage bacon ham tuna salmon prawn".split())

GREEN_NAMES = frozenset("spinach pea broccoli courgette cabbage pepper".split())
GREEN_IN_TEXT = ("spinach", "peas", "pea ", "broccoli", "courgette", "cabbage", "kale",
                 "green bean", "mangetout", "greens")

LIMIT_WORDS = frozenset("""quick quickly fast rush rushed hurry quickish simple easy easier
cheaper cheap basic plain lighter light lightly""".split())
# "nothing too fancy" says what the meal must not be, and "made" and "fancy" as words are both
# too loose to key on ("i fancy a curry" is a want): the phrases are matched in the line.
SIMPLE_PHRASES = ("nothing too fancy", "nothing fancy", "not too fancy", "nothing complicated",
                  "nothing too complicated", "no fuss", "keep it simple", "plain and simple",
                  "nothing special", "nothing flashy", "something plain", "plain food")
# "something spicy" is a narrowing like "something quick": the dish already on the table is the
# answer, with the heat put into it, rather than a shrug.
HEAT_WORDS = frozenset("""spicy spice spicier spicy-hot hotter hottest chilli chillies chili
chillis kick fiery heat""".split())
HEAT_IN_TEXT = ("chilli", "chili", "curry", "cajun", "paprika", "harissa", "hot sauce",
                "spice", "spiced", "curried", "spicy", "ginger", "cumin")
# The pantry names that carry the heat, so a line that refuses the taste refuses them: the dish
# that answers "wont eat anything spicy" is a dish with no chilli in it, and the words below are
# the ones a dish's own text uses to put the heat in.
HEAT_INGREDIENTS = ("chilli", "chili", "chillies", "chillis", "cayenne", "paprika", "harissa",
                    "sriracha", "jalapeno", "tabasco", "chilli powder", "curry powder",
                    "hot sauce", "chilli flakes", "chilli sauce", "cajun")
# A taste word under a refusal is a ban on the taste, not a wish for it: "and the kids wont eat
# anything spicy" sets the heat flag like "something spicy" does, so the dish on the table came
# back with "Add chopped chilli or a pinch of chilli flakes" in it - the one thing the line said
# nobody would eat. "a kid who wont eat anything green" already has this shape in `no_green`.
# Only the little words that join a refusal to its taste may sit between them, so "i dont want it
# bland, something spicy" stays a wish for the heat.
_TASTE_RULED_OUT = re.compile(
    r"\b(?:wont|won't|wouldnt|wouldn't|doesnt|doesn't|dont|don't|didnt|didn't|never|no|"
    r"hates?|hated|dislikes?|disliked|refuses?|refused|not)\b"
    r"(?:\s+(?:eat|eats|eating|to|anything|something|food|foods|stuff|things|thing|meals?|"
    r"dishes|very|too|much|that|this|these|those|so|really|any|all|of|or|and|the|a|an|it|"
    r"them|sort|kind|hot|fan|keen|into|like|likes|at))*"
    r"\s+(?:spicy|spiced|spicier|spice|chilli|chili|chillies|chillis|curry|curried|fiery)\b")
# "hot" alone is the weather, a bath or an oven ("its too hot to cook"), so it only counts as the
# taste when the line says it is food.
_HOT_FOOD_RULED_OUT = re.compile(
    r"\b(?:wont|won't|wouldnt|wouldn't|doesnt|doesn't|dont|don't|didnt|didn't|never|"
    r"hates?|hated|dislikes?|refuses?|refused)\b"
    r"(?:\s+(?:eat|eats|eating|anything|something|very|too|much|that|so|really|any))*"
    r"\s+hot\s+(?:food|foods|stuff|things|sauce|curry|dishes?)\b")
VEG_WORDS = frozenset("vegetarian vegan veggie meatless".split())
# "she doesnt eat meat" is a vegetarian meal asked for without the word.
MEAT_FREE_PHRASES = ("no meat", "without meat", "not eat meat", "doesnt eat meat",
                     "doesn't eat meat", "dont eat meat", "don't eat meat", "off meat",
                     "no fish", "no chicken")
# A dairy ban is a food to keep out of the dish, not a meat-free meal: "and no dairy" on a chicken
# dinner is a chicken dinner without the cheese, and it was read as "no meat", so the plan picked
# a potato hash whose own words offered cheese over the top.
DAIRY_FREE_PHRASES = ("no dairy", "dairy free", "dairy-free", "without dairy", "milk free",
                      "milk-free", "no milk products", "off dairy", "lactose free",
                      "lactose-free")
DAIRY_FOODS = tuple(name for name, kinds in FOOD_CLASSES.items() if "dairy" in kinds)
# Who is coming, and for what: a family word on its own is a chat about the family.
COMING_FOR = ("for dinner", "for tea", "for supper", "for lunch", "coming for", "coming over",
              "coming round", "coming to", "round for", "over for", "having people",
              "having friends", "having guests", "to cook for", "cooking for")
# An event is an occasion on its own ("what should i cook to celebrate"); a person is only an
# occasion when they are coming for something ("my sister is a nurse" is a chat about a sister).
EVENT_WORDS = frozenset("""guests guest party parties buffet crowd birthday anniversary
celebrate celebration""".split())
# The days a household cooks a big meal for, however the line is put.
# A day that matters and a menu being asked for: "ive got my mums 70th next saturday and no idea
# what to cook". The day alone is often a memory ("we always did a lunch for her birthday"), and
# those make no plan, so the ask for the menu is what turns the day into an occasion.
MENU_PHRASES = ("no idea what to cook", "what to cook", "what should i cook", "what to make",
                "what shall i cook", "cook for", "cooking for", "make for")
BIG_DAYS = frozenset("""christmas xmas thanksgiving easter hanukkah diwali ramadan eid""".split())
# An event is an occasion when a meal is being made for it: "im having a party on saturday",
# "christmas dinner for six". "we always did a lunch for her birthday" is a memory, not a menu.
COOKING_FOR = ("having a", "having some", "im making", "i'm making", "were making", "we're making",
               "im cooking", "i'm cooking", "for a", "for the", "for my", "party food", "buffet",
               "celebrat", "hosting", "come over", "coming over")
PEOPLE_WORDS = frozenset("""mum mom dad family friends visitors mother father parents sister
brother inlaws in-laws boyfriend girlfriend""".split())
# "cooking for eight people", "theres 14 of us": a number of mouths is an occasion without a
# person's name. One or two is not: "a quick dinner for two kids" is a small dinner, not a party.
CROWD_PHRASE = re.compile(
    r"\b(?:people|friends|family|guests?|company)\s+(?:coming\s+)?over\b"
    r"|\b(?:for|feeding|there are|there's|theres|we are|we're)\s+"
    r"(?:\d+|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fourteen|fifteen|twenty|"
    r"thirty|a dozen)\b|\b\d+\s+of\s+us\b")
DISLIKE_WORDS = frozenset("""hate hates hated dont don't doesnt doesn't wont won't wouldnt
wouldn't dislike dislikes picky refuse refuses""".split())
# A refusal can be about somebody else's plate: "my daughter refuses tomatoes", "the kids wont eat
# peas". The rule-out answer is about the person typing, so it has to know whose plate it is.
SOMEONE_ELSE = re.compile(
    r"\b(?:my|his|her|our|their|the|one)\s+(?:daughter|son|kid|kids|child|children|boy|girl|"
    r"teenager|husband|wife|partner|mum|mom|dad|father|mother|brother|sister|friend|friends|"
    r"nan|gran|granny|grandma|grandad|grandpa|guest|guests|inlaws|in-laws|other half|"
    r"mother in law|father in law)\b"
    r"|\b(?:he|she|they)\s+(?:wont|won't|doesnt|doesn't|refuses|hates|dislikes|isnt|isn't)\b")


def _about_someone_else(understood):
    """Whether the line rules the food out for somebody who is not the person typing."""
    return bool(SOMEONE_ELSE.search(_clean(understood)))
GREEN_WORDS = frozenset("green greens".split())
# --- a plan kept over a few turns -------------------------------------------
# The fourth line of a cooking conversation is often four words: "something quick please", "and
# no cheese either", "she doesnt eat meat". It names no meal and often no ingredient, so neither
# an entry nor the pantry table can answer it: both read one line at a time. What the earlier
# lines said - the food in the kitchen, the time there is, what the person will not eat, who is
# coming - is kept in memory["meal"], and plan_reply() answers the narrowing line from it. The
# plan lapses once the talk has moved on, so a line about the washing up is never read as a
# request for dinner.

PLAN_LAPSE = 2          # turns of other talk before the plan is forgotten
MINUTES = {             # how long each dish takes, start to plate, from its own text
    "potato-egg-hash": 15, "courgette-mushroom-pasta": 20, "chicken-spinach-cream": 20,
    "frittata": 20, "egg-fried-rice": 10, "cheese-omelette": 8, "mushroom-omelette": 10,
    "courgette-frittata": 20, "ham-omelette": 8, "tomato-pasta": 15, "tuna-pasta": 15,
    "courgette-pasta": 15, "mushroom-pasta": 15, "bacon-pasta": 15, "mac-cheese": 20,
    "pea-pasta": 12, "garlic-spaghetti": 10, "chicken-rice": 30, "leftover-chicken-rice": 10,
    "chicken-potato-tray": 45, "chickpea-curry": 20, "chickpea-spinach": 15, "lentil-soup": 30,
    "dhal": 25, "sausage-potato": 40, "sausage-bean": 30, "bolognese": 35, "cottage-pie": 50,
    "mince-pasta": 25, "salmon-potato": 40, "prawn-pasta": 15, "tuna-potato": 20,
    "bean-quesadilla": 5, "cheese-quesadilla": 5, "toastie": 5, "eggy-bread": 5,
    "pancakes": 20, "shortbread": 30, "banana-pancakes": 10, "banana-smoothie": 2,
    "porridge": 5, "overnight-oats": 480, "apple-crumble": 45, "veg-soup": 30,
    "veg-stirfry": 10, "cheesy-mash": 20, "mince-onion": 25, "onion-omelette": 12,
    "fried-potato-onion": 20, "chicken-onion-curry": 35, "loaded-jacket": 30, "shakshuka": 25,
    "spinach-pasta": 15, "bean-tomato": 20, "tuna-rice": 10, "prawn-rice": 15,
    "lemon-chicken": 45, "mash-cheese": 10, "scrambled-eggs": 5, "mushroom-cream": 10,
}

# The same for the one-ingredient ideas, which are written as a single line each.
PANTRY_MINUTES = {
    "egg": 5, "pasta": 10, "rice": 10, "potato": 50, "chicken": 40, "mince": 25, "sausage": 25,
    "bacon": 15, "ham": 5, "tuna": 15, "salmon": 15, "prawn": 10, "chickpea": 30, "bean": 5,
    "lentil": 25, "cheese": 5, "tomato": 15, "onion": 25, "garlic": 5, "mushroom": 10,
    "spinach": 5, "courgette": 15, "pepper": 10, "carrot": 25, "broccoli": 15, "cabbage": 10,
    "pea": 15, "sweetcorn": 10, "bread": 5, "tortilla": 5, "flour": 25, "milk": 10, "cream": 10,
    "butter": 30, "yoghurt": 2, "lemon": 5, "banana": 10, "apple": 15, "oats": 5,
}

# Dishes that suit company: a plan with guests wants one of these rather than a lone omelette.
# Not named `CROWD`: that is the crowd-size regex the pudding answer reads, and a second CROWD
# here shadowed it, so "a pudding for eight" crashed the pudding entry.
CROWD_DISHES = frozenset(("bolognese", "cottage-pie", "chicken-potato-tray", "chickpea-curry", "dhal",
                   "sausage-bean", "veg-soup", "mac-cheese", "salmon-potato", "lemon-chicken",
                   "apple-crumble", "frittata"))

# Dishes cooked in one pan for one or two: good dinners, not the dish a table is built on.
FOR_ONE = frozenset(("frittata", "courgette-frittata", "cheese-omelette", "mushroom-omelette",
                     "onion-omelette", "ham-omelette", "toastie", "scrambled-eggs",
                     "egg-fried-rice", "bean-quesadilla", "cheese-quesadilla", "eggy-bread",
                     "banana-pancakes", "pancakes", "porridge", "overnight-oats"))

# A soup is a starter: it can feed a table, but it is not the dish a dinner party is built on.
THIN = frozenset(("veg-soup", "lentil-soup"))

# "and a pudding": after a main, the next thing asked for is often the sweet, and the dishes
# for that are the ones nobody wants as dinner.
SWEET_WORDS = frozenset("pudding puddings dessert desserts afters sweet-tooth".split())
# The sweet at the end of a meal, however it is asked for: "and a pudding", "something warm for
# after", "anything to follow".
SWEET_PHRASES = ("something sweet", "something warm for after", "something for after", "for after",
                 "to follow", "after that", "sweet course", "for pudding", "for dessert",
                 "for afters")
SWEET_DISHES = frozenset(("apple-crumble", "pancakes", "shortbread", "banana-pancakes",
                          "banana-smoothie", "porridge", "overnight-oats"))
# Words that make a line a question about a meal. "something", "anything" and "ideas" are not
# among them: they are in "did anything nice happen" and "any ideas for a birthday present".
DINNER_WORDS = frozenset("""dinner tea supper lunch brunch meal meals food cook cooking make made
tonight eat eating""".split())
CHATTER = frozenset("""thanks thank ok okay lol haha yes yeah no nope sure great nice cool
hi hello bye morning night fine""".split())
TECHNIQUE_WORDS = frozenset("""time timing temperature oven degrees gas grill boil boiling roast
roasting fry frying bake baking rest resting cover covered lid stir seasoning""".split())
# A line about baking is about a cake, and a cake is not a dinner: "my daughters birthday cake
# has to survive a two hour drive" is a baking question, and the lemon in it is not a lemon
# chicken.
BAKING_WORDS = frozenset("""cake cakes bake baking baked sponge icing buttercream biscuit
biscuits cookie cookies muffin muffins cupcake cupcakes scone scones pastry loaf bread brownie
brownies tart drizzle frosting""".split())
# The dish a line names is that dish's own question ("an easy curry", "a cheese board"), and the
# dish table and the entries answer it better than a meal picked round it.
DISH_WORDS = frozenset("""curry curries pasta soup soups pie pies stew roast salad sandwich
sandwiches risotto casserole burger pizza traybake omelette frittata macaroni lasagne""".split())
# A meal is asked for in a word about a meal: "an easy curry for someone who has never made one"
# is about a curry, and "which cheeses go on a board for six people" is not a dinner at all.
MEAL_FRAME = frozenset("""dinner tea supper lunch brunch meal meals food cook cooking cooked eat
 eating tonight make pudding dessert
 something anything""".split())
# "what did i say about the lemon drizzle" asks the memory, not the kitchen.
SAID_PHRASES = ("what did i say", "what did i tell", "did i tell you", "what did you say",
                "remind me what", "what have i said", "did i say")
# What a plan can be made of. Used to decide whether a line adds anything to a meal, and
# whether the meal behind a bare "what should i cook" is worth answering.
PLAN_KEYS = ("have", "avoid", "limit", "veg", "vegan", "occasion", "simple", "no_green",
             "sweet", "crowd", "heat", "no_heat")
# A dish that mentions one of these is not for someone who said no to the first name: saying
# "no cheese" rules out the parmesan in the pasta as much as the cheese on top.
AVOID_TEXT = {"cheese": ("cheese", "parmesan", "cheddar", "mozzarella", "feta", "halloumi",
                         "pecorino", "gruyere", "blue cheese"),
              # "no dairy" rules out the cheese and the yoghurt a dish names in its own words, not
              # just the word "dairy": a chicken curry with yoghurt in it was offered to someone
              # who had just said no dairy, and the potato hash under it said "cheese over the top".
              "dairy": tuple(sorted(DAIRY)),
              "milk": ("milk", "cream", "butter", "yoghurt", "yogurt", "creme fraiche"),
              "butter": ("butter",), "egg": ("egg", "eggs"),
              "meat": tuple(sorted(MEAT_NAMES)),
              "fish": ("fish", "tuna", "salmon", "prawn", "anchovy", "cod")}
VEGAN_BAD = ("cheese", "parmesan", "cheddar", "mozzarella", "feta", "halloumi", "milk",
             "cream", "butter", "yoghurt", "yogurt", "egg", "eggs", "honey", "creme fraiche")
# A line about somebody's taste is talk about that person, not a request for a meal: "she likes
# carrots raw funny enough" is a parent telling you how the child eats, and a soup made of the
# carrots she eats raw is the wrong turn. Only a meal word or a time of its own makes it an ask.
PERSON_WORDS = frozenset("""she he her his him they their them son daughter boy girl child
children kid kids toddler baby mum mom mummy daddy husband wife partner friend nan nana grandma
granny grandad niece nephew""".split())
TASTE_WORDS = frozenset("""likes like loves love hates hate hated prefers prefer adores adore
favourite favorite keen fussy refuses refused""".split())
SWAP_PHRASES = ("instead", "substitute", "stand in", "replace", "swap")
METHOD_PHRASES = ("how do i", "how do you", "how should i", "how long", "how much",
                  "what temperature", "how to")


NEW_MEAL_PHRASES = ("what can i cook", "what can i make", "what should i cook",
                    "what should i make", "what can i do with", "meal ideas", "dinner ideas",
                    "any ideas", "what shall i cook")
# A line that says what is in the kitchen says the food is on hand: "ive got mince in the
# fridge", "there are two chicken breasts left over". A line that names a food and then says
# what went wrong with it ("my rice always goes sticky", "my cake sank in the middle") names a
# food too, but that food is the problem, not something to build a meal from, so it starts no
# plan - the fault's own entry answers it and the next line is a new question.
# A crop in the ground is not a larder. "my tomato plants have yellow leaves" says "have" and
# names a food, so the plan read it as "I have tomatoes" and kept a larder that was never there:
# the next line ("its on the tomatoes too") narrowed that plan and got a tomato sauce to a
# question about a sick plant. The food named beside one of these words is the plant growing,
# not something in the fridge, and no meal is planned from it.
# A pot is not here on purpose: "theres a chicken in the pot" is a dinner being cooked, and the
# larder it describes is the one the next line ("what can i make with it") is asking about. The
# crop case does not need the word: "my tomatoes are in pots" names the plant as well, and a
# kitchen's own pot of basil is the herbs row's question.
_GROWING_WORD = frozenset("""plant plants planted planting seedling seedlings seed seeds
    tree trees bush bushes shrub shrubs crop crops allotment allotments garden greenhouse
    growing grow grows grown sow sowed sowing""".split())


def _a_crop_not_a_larder(understood):
    """True when the food the line names is one it is growing rather than one it has in."""
    words = set(_said_words(understood))
    if not words & _GROWING_WORD:
        return False
    if _meal_asked(understood):
        # "what can i make with the courgettes im growing" asks for a meal, and the crop is
        # what to cook with. Only a line that plans nothing is turned down here.
        return False
    return True


STOCK_PHRASES = ("have", "has", "got", "there is", "theres", "there are", "left over",
                 "leftover", "in the fridge", "in the freezer", "in the cupboard",
                 "in the pantry", "in the house", "in my kitchen", "at home")


def _clean(understood):
    return str((understood or {}).get("clean") or "").lower()


def _said_words(understood):
    words = (understood or {}).get("words") or ()
    return [_fold(word) for word in words]


def minutes_said(understood):
    """The time a line gives ("20 mins", "half an hour", "an hour and a half"), in minutes."""
    text = " " + _clean(understood) + " "
    for pattern, unit in ((r"(\d+)\s*(?:mins|min|minutes|minute)\b", 1),
                          (r"(\d+)\s*(?:hrs|hr|hours|hour)\b", 60),
                          (r"(\d+)\s*and\s*a\s*half\s*(?:hours|hour|hrs|hr)\b", 90)):
        found = re.search(pattern, text)
        if found:
            return int(found.group(1)) * unit
    if re.search(r"\bhalf an hour\b", text):
        return 30
    return None


# An allergy is a food to leave out, and it is the one rule that must never be read as an
# ingredient: "plus cheese" after "im allergic to peanuts" is the second thing to avoid, and a
# breakfast built from it is the worst reply the bot can give.
ALLERGY_WORDS = frozenset("allergic allergy allergies intolerant intolerance anaphylactic "
                          "anaphylaxis".split())
ALLERGY_PHRASES = ("cant eat", "can't eat", "cannot eat", "must avoid", "have to avoid",
                   "no nuts at all", "nut free diet")


# A wish is not a larder. "im trying to eat more veg" and "i want to eat less bread" name a
# food, and the ingredient reader rightly finds it, but the fridge is not in that sentence: the
# veg is what they would like more of. Once it was stored as stock, every later question in the
# same chat was answered as though the veg was the thing on the table - "what should i eat for
# protein" came back as a tray of roast vegetables. Only the food a line wants more or less of
# is left out of the store, and only when the wanting verb is beside it, so "i have more veg
# than i know what to do with" is still a fridge with too much in it.
A_WISH_FOR_A_FOOD = re.compile(r"\b(?:eat|eating|ate|get|getting|want|wants|wanted|need|needs|"
                              r"like|likes|try to eat|trying to eat|cut down on|cut back on)"
                              r"\s+(more|less|fewer)\s+(?:of\s+)?([a-z]+)")


def _the_foods_wanted_more_or_less(said_clean, named):
    """The named foods this line only wants more or less of, and so is not stock of."""
    if not named:
        return set()
    wished = set()
    for found in A_WISH_FOR_A_FOOD.finditer(said_clean or ""):
        word = found.group(2).strip(",.")
        name = _INGREDIENT_WORDS.get(word)
        if name is None:
            for ending in ("", "s", "es"):
                name = _INGREDIENT_WORDS.get(_fold(word) + ending)
                if name is not None:
                    break
        if name in named:
            wished.add(name)
    return wished


def _the_foods_wanted_more(said_clean, named):
    """The named foods this line says it wants more of, which a later dish is picked from.

    Only "more": "i want to eat less bread" is a food to keep out of the dish, and a toastie for
    someone cutting down on bread is the wish answered backwards.
    """
    if not named:
        return set()
    more = set()
    for found in A_WISH_FOR_A_FOOD.finditer(said_clean or ""):
        if found.group(1) not in ("more",):
            continue
        word = found.group(2).strip(",.")
        name = _INGREDIENT_WORDS.get(word)
        if name is None:
            for ending in ("", "s", "es"):
                name = _INGREDIENT_WORDS.get(_fold(word) + ending)
                if name is not None:
                    break
        if name in named:
            more.add(name)
    return more


def wants(understood, old=None):
    """What this line says about the meal, read on top of the plan already in `old`.

    Only the things a cook would keep: the food named and ruled out, the time there is, whether
    it has to be meat-free, who is coming, and whether it has to be simple. Everything else in
    the line belongs to the answer and not to the plan.
    """
    context = {key: list(value) if isinstance(value, list) else value
               for key, value in (old or {}).items()}
    words = set(_said_words(understood))
    said_clean = _clean(understood)
    named = list(ingredients(understood))
    refused = list(negated_ingredients(understood))
    if words & ALLERGY_WORDS or any(phrase in said_clean for phrase in ALLERGY_PHRASES):
        # An allergy is a food to keep out of the dish, and it is the one rule never read as an
        # ingredient: "im allergic to peanuts" is not a plan to cook peanuts.
        for name in named:
            if name not in refused:
                refused.append(name)
    if _refuses(understood):
        # "they won't eat mushrooms" names the food to keep out of the dish, not food to cook
        # with: the reading of a refusal is the same whether the line says "wont" or "won't"
        # and whether the ingredient is written as a plural or not.
        for name in named:
            if name not in refused:
                refused.append(name)
    wished = _the_foods_wanted_more_or_less(said_clean, named)
    if wished:
        # A food wished for is not stock, but the one they want more of is still what they would
        # like to eat, so a dish asked for afterwards is picked from it: "im trying to eat more
        # fish" is not a fridge with fish in it, and "what should i cook tonight" should still be
        # a fish dish.
        fancy = None
        for name in sorted(_the_foods_wanted_more(said_clean, named)):
            fancy = context.setdefault("fancy", [])
            if name not in fancy:
                fancy.append(name)
    for name in named:
        if name in refused or name in wished:
            continue
        have = context.setdefault("have", [])
        if name not in have:
            have.append(name)
    for name in refused:
        avoid = context.setdefault("avoid", [])
        if name not in avoid:
            avoid.append(name)
    if context.get("have") and any(phrase in said_clean for phrase in ONLY_PHRASES):
        # "i only have eggs and pasta in": cook with those, don't send them shopping.
        context["only"] = True
    limit = minutes_said(understood)
    if limit is not None:
        context["limit"] = limit
    if words & VEG_WORDS or any(phrase in _clean(understood) for phrase in MEAT_FREE_PHRASES):
        context["veg"] = True
    if any(phrase in said_clean for phrase in DAIRY_FREE_PHRASES):
        # The cheese and the yoghurt are off the table, in the dish's own words as well as on top.
        avoid = context.setdefault("avoid", [])
        for name in DAIRY_FOODS:
            if name not in avoid:
                avoid.append(name)
    if "vegan" in words:
        context["vegan"] = True
    if CROWD_PHRASE.search(said_clean):
        # "im cooking for eight people", "theres 12 of us": a table that size is not answered
        # with a dish for one, so a diet named for part of the table still leaves the main.
        context["crowd"] = True
    if ((context.get("veg") or context.get("vegan")) and not context.get("have")
            and (not context.get("crowd") or _meal_asked(understood))):
        # Nothing on the table and a diet named: the diet is what the dish has to be built
        # around, so a vegetarian dish is allowed to stand on its own the way a pudding is. It
        # invents no food, because the conversation never named any to contradict. For a table
        # of eight the diet statement alone names no dinner ("two of them are vegetarian" is
        # what a share of the dishes must be), but the dish asked for afterwards is the one
        # everyone can eat, so the vegetarians noted get a meat-free main for the whole table.
        context["diet"] = True
    if context.get("veg") and context.get("have"):
        # The meat named a line or two ago is off the table now: "ive got chicken" then "im
        # vegetarian" is a vegetarian dinner, and the chicken in the fridge picks nothing.
        meat = [name for name in context["have"] if name in MEAT_NAMES]
        if meat:
            context["have"] = [name for name in context["have"] if name not in MEAT_NAMES]
            if not context["have"]:
                context.pop("have", None)
                context["diet"] = True     # the diet, not a cupboard, chooses the dish
    # Food on the table: a meal word, something from the kitchen, or somebody coming for a meal.
    # "my mum would have been 70 this week" and "we always did a lunch for her birthday" name an
    # occasion, but not one anybody is cooking for, so they make no plan.
    foodish = (bool(words & DINNER_WORDS) or bool(ingredients(understood))
               or any(phrase in _clean(understood) for phrase in COMING_FOR))
    said_clean = _clean(understood)
    if foodish and (_occasion(said_clean) and any(phrase in said_clean
                                                  for phrase in MENU_PHRASES)
                    or CROWD_PHRASE.search(said_clean) or words & BIG_DAYS
                    or (words & PEOPLE_WORDS
                        and any(phrase in said_clean for phrase in COMING_FOR))
                    or (words & EVENT_WORDS
                        and any(phrase in said_clean for phrase in COOKING_FOR))):
        context["occasion"] = True
    if words & LIMIT_WORDS or any(phrase in said_clean for phrase in SIMPLE_PHRASES):
        context["simple"] = True
    if words & HEAT_WORDS:
        if _a_taste_ruled_out(said_clean):
            # The line refuses the taste, so nothing that carries it goes in: the dish and the
            # ideas are read against the pantry names below, and `_with_heat` adds no heat.
            context["no_heat"] = True
            avoid = context.setdefault("avoid", [])
            for name in HEAT_INGREDIENTS:
                if name not in avoid:
                    avoid.append(name)
        else:
            context["heat"] = True           # "something spicy" on the dish already on the table
    sweet = bool(words & SWEET_WORDS) or any(phrase in _clean(understood) for phrase in SWEET_PHRASES)
    if sweet and not ingredients(understood):
        context["sweet"] = True               # "and a pudding" asks for the sweet, not the main
        context.pop("have", None)             # the chicken in the pot has nothing to do with it
    if words & DISLIKE_WORDS and words & (GREEN_WORDS | {"veg", "vegetables", "veggies"}):
        context["no_green"] = True           # "a kid who wont eat anything green"
    return context


def _fits(names, context):
    """Whether a dish or an idea is allowed by the plan's refusals."""
    names = set(names)
    if names & set(context.get("avoid") or ()):
        return False
    if context.get("veg") and names & MEAT_NAMES:
        return False
    if context.get("no_green") and names & GREEN_NAMES:
        return False
    if context.get("no_heat") and names & set(HEAT_INGREDIENTS):
        return False
    return True


def _text_conflict(dish, context):
    """Whether the dish's own words break a refusal: pasta with parmesan is not "no cheese"."""
    text = (dish.get("text") or "").lower()
    for name in context.get("avoid") or ():
        for word in AVOID_TEXT.get(name, (name,)):
            if word in text:
                return True
    if context.get("vegan") and any(word in text for word in VEGAN_BAD):
        return True
    return False


# "something quick please" with no number in it still sets a time: a quarter of an hour, a
# twenty-minute dinner. Without it a dish table that picks by which ingredients a dish uses
# answers "quick meal with mince?" with the ten-minute onion start of a forty-minute ragù.
QUICK_MINUTES = 20


def _quick_limit(context):
    """The longest a dish may take for this plan: the number they said, or "quick" as twenty."""
    if context.get("limit"):
        return context["limit"]
    return QUICK_MINUTES if context.get("simple") else None


def _quick_enough(minutes, context):
    limit = _quick_limit(context)
    return not (limit and minutes and minutes > limit)


def _score(dish, context):
    """How well a dish answers the plan: what it uses, what it leaves over, and the time."""
    have = set(context.get("have") or ())
    uses = set(dish["uses"])
    minutes = MINUTES.get(dish["id"])
    score = len(uses & have) * 4 - len(have - uses) * 3
    if minutes is not None:
        score -= minutes // 25
        limit = _quick_limit(context)
        if limit and minutes > limit:
            score -= 6                      # honest but not the answer to "something quick"
    if context.get("simple") and minutes is not None:
        score -= max(0, minutes - 20) // 5
    if have and have <= uses:
        score += 4
    if have:
        score -= len(uses - have - STAPLES)
    else:
        score -= len(uses) * 2              # nothing named: the least shopping wins
    if context.get("occasion") and dish["id"] in THIN:
        score -= 6                  # "two of them are vegetarian" is not an answer of soup
    if context.get("occasion") and dish["id"] in FOR_ONE:
        # A frittata or an omelette is a fine dinner and no dinner party: a table that size
        # wants one dish that feeds everybody, not eggs for eight.
        score -= 10
    if context.get("heat"):
        text = (dish.get("text") or "").lower()
        score += 6 if any(word in text for word in HEAT_IN_TEXT) else -2
    if context.get("occasion") and dish["id"] in CROWD_DISHES:
        score += 8
        if (minutes or 0) >= 30:
            score += 4              # company wants the dish with a bit of cooking in it
        elif context.get("limit") is None:
            score -= 2              # a soup for a dinner party is thin
    return score


def _meal_idea_for(name):
    """The meal idea for the same ingredient, for a plan that has to be quick.

    The pantry line is the shortest thing the table can say about an ingredient and it is what
    most lines want, but a roast takes forty minutes: when the line asked for something quick
    and the pantry line is slower than that, the meal idea for the same food is the twenty-
    minute one ("cut it into strips and fry it").
    """
    if name not in PANTRY:
        return None
    words = set(PANTRY[name][0]) | {name}
    for names, idea in MEAL_IDEAS:
        if words & set(names):
            return idea
    return None


def _ideas(context, limit=True):
    """One-ingredient ideas for what is in the plan, in the order the plan mentions it."""
    out = []
    have = list(context.get("have") or ())
    quick = _quick_limit(context) if limit else None
    for name in reversed(have):
        if name not in PANTRY or not _fits((name,), context):
            continue
        idea = PANTRY[name][1]
        if quick and (PANTRY_MINUTES.get(name) or 0) > quick:
            faster = _meal_idea_for(name)
            if faster:
                idea = faster         # the forty-minute one is not "quick", the twenty is
            elif limit:
                continue              # too slow, and there is nothing quicker for this food
        if _mentions(idea, context.get("avoid") or ()) or _text_conflict({"text": idea}, context):
            continue                        # an idea that uses what they said no to
        out.append((name, idea))
    return out


def plan_reply(context, memory=None, skip=()):
    """An answer for the plan, or None when the plan has nothing to work with.

    A dish that uses most of what is in the kitchen comes first; with nothing named, or nothing
    the dishes cover, the one-ingredient ideas for what is in the plan come next. A dish or idea
    the bot has already offered is passed over so the next line gets something new.
    """
    if not context:
        return None
    if not context.get("have") and context.get("fancy"):
        # The only food named was wished for rather than in the kitchen, so the dish is picked
        # from the wish. `have` itself is left alone: everything else in the chat reads it as the
        # cupboard, and a wish answered as a cupboard is what put roast veg on a protein question.
        context = dict(context, have=list(context["fancy"]))
    if context.get("only"):
        ideas = _ideas(context, limit=bool(context.get("limit") or context.get("simple")))
        if ideas:
            return " ".join(idea for _, idea in ideas[:2])
    offered = context.get("offered") or ()
    skip_ids = set(skip) | set(offered if isinstance(offered, (list, tuple, set)) else ())
    scored = []
    for dish in DISHES:
        if dish["id"] in skip_ids or not _fits(dish["uses"], context):
            continue
        if (dish["id"] in SWEET_DISHES) is not bool(context.get("sweet")):
            continue                         # a pudding is not dinner, and dinner is not afters
        have = set(context.get("have") or ())
        # "and a pudding" asks for the sweet course and names no food, so a sweet dish is
        # allowed to stand on its own; a dinner is not, because the kitchen was never described
        # and any dish here would invent what is in it ("and brown rice" is not mince and rice).
        if not have and not context.get("sweet") and not context.get("diet"):
            continue            # nothing named: a dinner dish would invent the food on the table
        if have and not set(dish["uses"]) & have:
            continue            # every word of it is a staple: this is not the food they named
        if have and set(dish["uses"]) - have - STAPLES:
            continue            # a dish that needs a shop is not what is in the kitchen
        if context.get("limit") or context.get("simple"):
            if not _quick_enough(MINUTES.get(dish["id"]), context):
                continue
        if context.get("no_green") and any(word in dish["text"].lower()
                                           for word in GREEN_IN_TEXT):
            continue                         # peas in the rice are still greens to a child
        if context.get("no_heat") and any(word in dish["text"].lower()
                                          for word in HEAT_IN_TEXT):
            continue                         # a curry base is heat to the one who refused it
        if _text_conflict(dish, context):
            continue                         # a refusal covers the cheese in the words too
        scored.append((_score(dish, context), dish))
    if scored:
        scored.sort(key=lambda pair: -pair[0])
        if memory is not None and isinstance(memory.get("meal"), dict):
            memory["meal"].setdefault("offered", []).append(scored[0][1]["id"])
        return _with_heat(scored[0][1]["text"], context)
    ideas = _ideas(context)
    if not ideas:
        ideas = _ideas(context, limit=False)
    if ideas:
        return " ".join(idea for _, idea in ideas[:2])
    return None


def _a_taste_ruled_out(said):
    """True when the line refuses the heat rather than asking for it.

    "and the kids wont eat anything spicy" is the same words as "something spicy" to the heat
    flag, and the dish on the table came back with chilli put into it. "its not spicy enough" is
    the other way round - the line wants more - so a taste word followed by "enough" is a wish
    even with "not" in front of it.
    """
    for pattern in (_TASTE_RULED_OUT, _HOT_FOOD_RULED_OUT):
        for found in pattern.finditer(said or ""):
            after = (said or "")[found.end():found.end() + 12].lower()
            if after.strip().startswith("enough"):
                continue
            return True
    return False


def _with_heat(text, context):
    """The dish, with the heat asked for put into it when its own words have none."""
    if not context.get("heat") or context.get("no_heat"):
        return text                      # nothing asked for, or the taste was refused
    lowered = (text or "").lower()
    if any(word in lowered for word in HEAT_IN_TEXT):
        return text                      # already a curry, a chilli or something spiced
    return (text.rstrip() + " Add chopped chilli or a pinch of chilli flakes with the onion for "
            "the heat - taste at the end and add more if it needs it.")


def plan_recent(memory):
    """The plan still in force, or None once the conversation has moved on."""
    plan = (memory or {}).get("meal")
    if not isinstance(plan, dict):
        return None
    turns = (memory or {}).get("turns") or []
    if len(turns) - int(plan.get("turn") or 0) > PLAN_LAPSE:
        return None
    return plan


def _last_reply(memory):
    """What the bot said last, so a dish already on the table is not put there twice."""
    turns = (memory or {}).get("turns") or []
    if not turns:
        return ""
    return str((turns[-1] or {}).get("bot") or "")


def remembered(understood, memory):
    """What of this line to keep for the next short reply to narrow, or None.

    The plan is written from any line about cooking that says something a cook would keep, and
    it is forgotten after a couple of turns about something else, so "how long do I roast a
    chicken" two turns after a dinner plan is not answered with a sausage traybake.
    """
    if not isinstance(understood, dict):
        return None
    if understood.get("kind") in ("empty", "greeting"):
        return None
    if _says_it_has_gone_off(understood.get("clean")):
        # A food that has gone off is not in the kitchen: "my chicken smells a bit, can i cook it"
        # is the sniff test, and nothing about that chicken is a plan for dinner. It used to be
        # stocked anyway, because naming a food is all this reads, so three spoilage questions in
        # a row left chicken, pork and mince in the plan - and the next one, "my mince smells a
        # bit is it still ok", was answered "mince and tomatoes make a ragu". A plan already on
        # the table is left as it was: this line adds nothing to it.
        return None
    plan = plan_recent(memory)
    words = set(_said_words(understood))
    said = _clean(understood)
    # The reading's own topic, never the conversation's: a meal two lines back is not what makes
    # "did anything nice happen" a food question.
    topic = understood.get("topic_own")
    if words & PET_WORDS and not plan:
        return None                          # "what can i cook for my cat" is not a meal
    if not plan and _a_crop_not_a_larder(understood):
        return None                          # a plant in the ground is not food in the fridge
    food = (topic in ("cooking", "food-and-drink") or bool(words & DINNER_WORDS)
            or bool(ingredients(understood)) or bool(negated_ingredients(understood)))
    if not food and not plan:
        return None                          # not about food, and no plan to add to
    # A line that says what is *not* in the kitchen says just as much about it: "i dont have any
    # rice or pasta in" keeps the plan for the next short line, and the foods it rules out are
    # part of that plan. Reading only the foods it still has left a line that ruled out all of
    # them with no plan at all, so "what can i make for tea" forgot the pasta was gone.
    stocked = (bool(ingredients(understood) or negated_ingredients(understood))
               and understood.get("kind") == "statement"
               and any(phrase in said for phrase in STOCK_PHRASES))
    # "im trying to eat more fish" names the food but says nothing is in the kitchen: it is a
    # wish, and a wish is kept as a wish (see `wants`), so the dish asked for next is a fish one.
    wish = bool(_the_foods_wanted_more(said, list(ingredients(understood))))
    # "what can i cook with pasta" names a dish word, which is normally the entries' question,
    # but it also says what is in the kitchen: the next short line ("something quick please")
    # belongs to it, so the plan is kept even though the entries answer this line.
    asking_with_food = (bool(ingredients(understood))
                        and any(phrase in _clean(understood) for phrase in NEW_MEAL_PHRASES))
    # "how do i cook rice" is a question about the rice, not a meal being planned: the answer is
    # the method, and the line after it ("and brown rice") belongs to the same question rather
    # than to a dish the bot has not put on the table.
    asking_how = (any(phrase in said for phrase in METHOD_PHRASES)
                  and len(ingredients(understood)) == 1
                  and not words & EVENT_WORDS and not CROWD_PHRASE.search(said))
    if not plan and (words & TECHNIQUE_WORDS or asking_how
                     or (not _meal_asked(understood) and not stocked and not asking_with_food
                         and not wish)):
        # "how long do i boil an egg" and "an easy curry for a beginner" start no meal plan.
        # "ive got mince in the fridge" says what is in the kitchen, so the next line can narrow it.
        return None
    new = wants(understood)                  # what this line says, without the plan behind it
    kept = {key: new[key] for key in PLAN_KEYS if key in new}
    if new.get("fancy"):
        kept["fancy"] = new["fancy"]         # a wish is something to keep, not to stock
    if not kept and not food:
        # Talk that is not about food does not keep a plan alive: a meal left three lines back
        # is gone, and the next mention of one starts again.
        return None
    if not plan and kept and set(kept) <= {"veg", "vegan"}:
        # "i dont eat meat" is a fact about them, kept by the memory lane and said back with their
        # name. It starts no meal of its own, so "what do i eat" after it is still their diet -
        # unless the meal was asked for a line ago ("dinner for two tonight" then "we dont eat
        # meat"), in which case it is the rule on the dish that is still to be picked.
        last_ask = set(str(((memory.get("turns") or [{}])[-1] or {}).get("user") or "")
                       .lower().split())
        if not last_ask & DINNER_WORDS:
            return None
    if not plan and not kept and understood.get("kind") != "question":
        # "maybe i will cook her favourite thing" says nothing to keep and asks nothing.
        return None
    if plan and plan.get("have") and _asks_about_a_food_it_has_not_got(understood, plan):
        # The dish on the table is not what the line is about: "and what about the potatoes?"
        # with chicken in the oven is the potatoes' own question, and "and if i havent got any
        # garlic" is the sauce without it. The plan stays as it was, so the next line still
        # narrows the dish and the entries answer the food this one named.
        return plan
    merged = wants(understood, plan)         # the plan with this line laid on top of it
    merged.setdefault("started", len(memory.get("turns") or []))
    merged["turn"] = len(memory.get("turns") or [])    # The dishes already put in front of them are kept, so a narrowing line gets a new one, but
    # only the last few: a plan that ran out of dishes must be allowed to repeat itself.
    offered = [name for name in (merged.get("offered") or ()) if isinstance(name, str)]
    said_last = _last_reply(memory)
    if said_last:
        for dish in DISHES:
            if dish["id"] not in offered and dish["text"] in said_last:
                offered.append(dish["id"])   # the dish they have already been given
    if offered:
        merged["offered"] = offered[-4:]
    allergies = _allergy_names(memory)
    if allergies:
        # What the person cannot eat is never what is in the kitchen, however the line was
        # phrased: "plus cheese" is a second allergy, not a second ingredient.
        gone = [name for name in (merged.get("have") or ())
                if _is_allergy_food(name, allergies)]
        if gone:
            left = [name for name in (merged.get("have") or ()) if name not in gone]
            if left:
                merged["have"] = left
            else:
                merged.pop("have", None)
            avoid = list(merged.get("avoid") or ())
            avoid.extend(name for name in gone if name not in avoid)
            merged["avoid"] = avoid
    return merged


def _allergy_names(memory):
    """The foods the person has said they cannot eat, as the memory lane keeps them."""
    user = (memory or {}).get("user") or {}
    return [str(name).lower() for name in (user.get("allergies") or ()) if str(name).strip()]


def _is_allergy_food(name, allergies):
    """Whether a food is one of the allergies, allowing for "peanut" and "peanuts"."""
    folded = _fold(str(name))
    stem = folded[:4]
    return bool(stem) and any(stem in allergy[:4] or allergy[:4] in folded
                              for allergy in allergies if len(allergy) >= 4)


# A line that asks about a food the dish has nothing to do with: it names something new in the
# kitchen ("and what about the potatoes?") or says there is none of it ("and if i havent got any
# garlic"). The entries answer a food on its own better than a dish picked from the whole table.
_ABOUT_A_FOOD = ("what about", "how about", "what can i do with", "what else with",
                 "instead of", "without")


def _asks_about_a_food_it_has_not_got(understood, plan):
    """Whether this line asks about a food of its own rather than narrowing the dish."""
    named = [name for name in ingredients(understood)
             if name not in (plan.get("have") or ())]
    if len(named) != 1 or set(named) & set(plan.get("avoid") or ()):
        return False
    if set(_said_words(understood)) & DINNER_WORDS:
        return False                         # "and something quick with the potatoes" is the plan
    said = _clean(understood)
    if any(phrase in said for phrase in _ABOUT_A_FOOD):
        return True
    # "havent got any", "if i dont have", "ran out of": the food named is the one missing.
    return bool(ABSENCE.search(said))


ABSENCE = re.compile(r"\b(?:havent|haven't|dont have|don't have|didnt have|didn't have|"
                     r"ran out|run out|out of|got any|no)\b")


def _narrowing(understood, plan=None, longest=10):
    """The plan a short line adds to, or None when the line is not narrowing one.

    Everything a line has to be to continue a plan is checked here once, so the first line of a
    conversation ("whats a quick dinner for two kids who wont eat anything green") and the fifth
    ("and quick") are read the same way. A question about how to cook something, a swap of one
    ingredient for another, a yes-or-no about the pan and a meal question of its own are all
    somebody else's answer, never a narrowing of this one.
    """
    words = set(_said_words(understood))
    if not words or len(words) > longest:
        return None
    if understood.get("kind") in ("empty", "greeting", "thanks"):
        return None
    said = _clean(understood)
    own = understood.get("topic_own")
    if own not in (None, "cooking", "food-and-drink") and not ingredients(understood):
        # "anything cheap for a sofa" is not about dinner, but "and something warm for after"
        # carries the sweet course and belongs to the meal already on the table.
        narrowed = any(key in wants(understood) for key in PLAN_KEYS if key != "simple")
        if not (plan and (narrowed or "limit" in wants(understood))):
            return None
    if words <= CHATTER and not words & DINNER_WORDS:
        return None                          # "thanks", "ok then": nothing to add
    if any(phrase in said for phrase in SWAP_PHRASES):
        return None                          # "can I use cream instead" is a swap
    if any(phrase in said for phrase in WITH_PHRASES):
        # "what can i have with it" after a curry is the sides question, not another dinner: the
        # plan answered it with the same dish back ("That's the one: Curry: ..."), and the entry
        # for what goes alongside knows better.
        return None
    if set(understood.get("asks") or ()) & {"how", "how_long", "how_much", "where", "how_often",
                                            "why"}:
        return None                          # "does that change the time" is about that dish
    if words & TECHNIQUE_WORDS and minutes_said(understood) is None:
        return None
    if "yesno" in set(understood.get("asks") or ()):
        # "should I do the potatoes in with it", "should I add the spinach at the end": a yes or
        # no about the food in front of them is about that pan, not about what to cook.
        if ingredients(understood) or words & {"it", "its", "that", "this", "them", "those"}:
            return None
    if ingredients(understood) and any(phrase in said for phrase in NEW_MEAL_PHRASES):
        return None                          # "what can I cook with chickpeas" is its own ask
    if words & BAKING_WORDS and not words & {"dinner", "tea", "supper", "lunch", "meal"}:
        return None                          # a cake is not a dinner
    if any(phrase in said for phrase in SAID_PHRASES):
        return None                          # "what did i say about the drizzle" is memory
    if (words & PERSON_WORDS and words & TASTE_WORDS
            and not words & DINNER_WORDS and minutes_said(understood) is None):
        return None                          # "she likes carrots raw" is about her, not dinner
    new = wants(understood)
    if new.get("heat") and (plan or {}).get("sweet"):
        # A heat word is not a narrowing of the sweet course: "and a pudding" then "something
        # spicy" put a banana breakfast on the table with a pinch of chilli stirred into it,
        # because a pudding plan lets a breakfast stand as a sweet dish. There is no spicy
        # pudding in the table, so this line narrows nothing.
        return None
    kept = any(key in new for key in PLAN_KEYS if key != "simple")
    kept = (kept or "limit" in new or bool(words & LIMIT_WORDS) or "heat" in new
            or any(phrase in said for phrase in SIMPLE_PHRASES))
    asked = (bool(words & DINNER_WORDS)
             or any(phrase in said for phrase in MEAL_PHRASES
                    if phrase not in BARE_MEAL_NOUNS)
             or _the_bare_ideas_are_about_food(understood, said))
    pointed = any((plan or {}).get(key) for key in PLAN_KEYS)
    # "what should i cook" after "my mum is coming for dinner sunday" adds nothing of its own,
    # but the plan behind it is the whole question: the answer is the one for guests. It has to
    # be a question, though: "maybe i will cook her favourite thing" says what they will do.
    asking = understood.get("kind") == "question" or bool(understood.get("asks"))
    if not kept and not (asked and pointed and asking):
        return None
    return wants(understood, plan)


# A bare "ideas" or "recipes" is not a meal ask on its own: the line says what the ideas are for.
# "give me some ideas for a rainy weekend" in the middle of a cooking talk was read as a narrowing
# of the dish on the table, and the person was handed the leftover chicken again behind "Same as
# before" - the same answer, which is the one thing a question about something else must not get.
BARE_MEAL_NOUNS = ("idea", "ideas", "recipe", "recipes")
# ... unless what the ideas are *for* is food ("ideas for using up chicken", "recipes for
# cabbage"), or the line names nothing beyond the ask at all: "any ideas" after a dish is the ask
# for other ideas for that dish, and the plan on the table is exactly what it is about.
BARE_MEAL_OBJECT = re.compile(r"\b(?:ideas?|recipes?)\s+(?:for|with|using|about|on)\s+(.*)", re.I)
# What the ideas can be for and still be the food in hand: "ideas for using up the rest", "recipes
# for them". Anything else the line names ("a cheap day out", "a rainy weekend") is its own
# subject.
THE_FOOD_IN_HAND = frozenset("it them those these this rest leftover leftovers other left "
                             "using use".split())


def _the_bare_ideas_are_about_food(understood, said):
    """Whether a line asking for "ideas" without a meal word is about the food on the table."""
    if not any(noun in said for noun in BARE_MEAL_NOUNS):
        return False
    if ingredients(understood):
        return True
    named = BARE_MEAL_OBJECT.search(said)
    if named is None:
        return True          # a bare "any ideas": the food in hand is what it is about
    return bool(set(re.findall(r"[a-z']+", named.group(1).lower())) & THE_FOOD_IN_HAND)

# "I only have eggs and pasta in" is a different meal from "I have eggs and pasta in".
ONLY_PHRASES = ("only have", "only got", "only have got", "nothing but", "all i have",
                "all i've got", "all ive got", "just have", "thats all i", "that's all i")
# A line that asks what goes alongside the dish ("what can i have with it", "what goes with
# curry") is about the side, not about what to cook, so it is never a narrowing of the plan.
WITH_PHRASES = ("have with it", "have with that", "eat with it", "goes with", "go with it",
                "serve with it", "serve it with", "served with", "on the side", "alongside",
                "what can i have", "what should i have", "with that meal")
PICK_PHRASES = ("you pick", "you choose", "you decide", "your call", "your choice",
                "up to you", "whatever you think", "whatever you like", "i don't mind",
                "i dont mind", "either is fine", "pick one", "you tell me")


def _idea_on_the_plate(plan, memory):
    """The meal idea the last answer gave, when it was built from an ingredient and not a dish."""
    said = _last_reply(memory)
    if not said:
        return None
    lowered = said.lower()
    for name in plan.get("have") or ():
        for alias in (PANTRY.get(name) or ((),))[0]:
            if alias in lowered:
                return said
    return None


def _chosen(plan):
    """The dish to put forward when they leave the choice to the bot: the last one offered."""
    dishes = {dish["id"]: dish for dish in DISHES}
    for name in reversed(list(plan.get("offered") or ())):
        dish = dishes.get(name)
        if dish and _fits(dish["uses"], plan) and not _text_conflict(dish, plan):
            return dish["text"]
    return None


_A_REACTION = ("nut free diet", "no nuts at all", "no dairy at all", "carry an epipen")


def _an_allergy(understood):
    """Whether the line names an allergy, in any shape the kitchen already reads as one.

    "im allergic to nuts", "she has a nut allergy", "lactose intolerant" and "they cant eat
    dairy" all rule the food out, and the allergy answer is the one that speaks to them: "That
    one has no nut in it anyway, so you're fine" is not a thing to say to somebody who has just
    told you about a reaction.
    """
    said = _clean(understood)
    if set(_said_words(understood)) & ALLERGY_WORDS:
        return True
    # "i cant eat cheese" is a food rule the rule-out row answers well, with the dish's name in it;
    # only the wording that names a reaction sends the line to the allergy answer.
    return any(phrase in said for phrase in _A_REACTION)


def _nothing_to_change(understood, memory):
    """An answer for a line that only rules something out of the dish already on the table.

    "and no cheese either" after a chickpea curry does not need a new dish, and answering it from
    the plain entry says the first answer over again as if none of it had been kept. The line has
    to add nothing but the rule-out: a new food, a time or a pudding is a different meal.
    """
    new = wants(understood)
    if any(key in new for key in PLAN_KEYS if key != "avoid"):
        return None                        # the line asks for something else on the plate
    plan = plan_recent(memory) or {}
    if not plan.get("offered"):
        return None                        # the last answer was a list of dinners, not a dish
    kept = list(new.get("avoid") or ())
    said = _last_reply(memory)
    if not kept or not said:
        return None
    names = f"{' or '.join(kept[:2])}"
    if _an_allergy(understood):
        # An allergy is not a dislike, and the dish on the table is still the dish: the answer
        # names the food back instead of "so you're fine" and instead of a different meal nobody
        # asked for. "i have chicken and spinach" then "i am allergic to milk" was answered with a
        # roast chicken recipe that never mentioned the milk, from a card the line never chose.
        # The food is read off the store-free reader, not off `kept`: a follow-up's `clean` carries
        # the dish's own ingredient in front of the allergy ("chicken im allergic to dairy"), and
        # "leave the chicken out" is the one thing that must not be said.
        banned = sorted(_excluded(_clean(understood)))
        mine = [word for word in _said_words(understood) if word in banned]
        theirs = _about_someone_else(understood)
        in_dish = [word for word in banned if _mentions(said, (word,))]
        who = "theirs" if theirs else "that one"
        if in_dish:
            # The dish really does hold it, so the answer is the dish with that food left out -
            # and it says where the food is, because "leave the milk out" of a cream dish is not
            # something a person can act on by reading the ingredient list.
            left_out = in_dish[0]
            where = " or ".join(mine[:2]) or left_out
            return (f"The {left_out} is where the {where} is, so leave it out of {who} and keep "
                    "the rest the same - and read the label on anything that came in a packet "
                    "before you use it.")
        if mine:
            return (f"There is no {' or '.join(mine[:2])} in that dish as it stands, so it is "
                    f"safe{' for them' if theirs else ''} - just keep the boards and knives clean, "
                    "and read the label on anything that came in a packet before you use it.")
        return None
    if _about_someone_else(understood):
        # "my daughter refuses tomatoes" is not a rule-out for the dish as a whole and it is not
        # about the person typing: answering "so you're fine" tells them about the wrong plate.
        if _mentions(said, kept):
            return f"Then make theirs without the {names} and keep the rest the same - it works."
        return f"That one has no {names} in it anyway, so theirs is fine."
    if _mentions(said, kept):
        # The dish on the table does have it in: the answer is that dish with the food left out,
        # not a different dish that happens to be clean.
        return f"Leave the {names} out of that one and it still works."
    return f"That one has no {names} in it anyway, so you're fine."


# A line that only says "yes, that, thanks" is not asking for another dish: "ok so low heat then"
# after the scrambled-egg advice was answered with a shakshuka, because the heat in the line read
# as a narrowing and the plan looked for something else to offer. The plan stays as it is, and the
# chat says the line back.
ACK_WORDS = frozenset("""ok okay k cool nice great good fine fair sure right true exactly yeah yep
yes no nah thanks thank cheers ta please sorry oh ah mm hmm mmm got get gotcha noted understood
makes sense sounds sound will do try trying then so and but that this it its low high heat slow
quickly gently careful huh righto alright perfect ace brill lovely accepted""".split())


def _only_an_acknowledgement(text):
    """True when the line is a yes, a thanks or an echo of advice, and asks for nothing."""
    words = re.findall(r"[a-z']+", (text or "").lower())
    if not words or len(words) > 7:
        return False
    return all(word in ACK_WORDS for word in words)


# A line that names a sum of money is the money table's question, not this one's. "What can i
# make with 40 pounds for the week", asked two turns after a vegetarian dinner was planned, was
# answered with the roast veg still on the plan: the plan reads "make" and "week" as a cooking
# ask, and the arithmetic the person asked for - £40 over seven days - sat a row away in
# money.py. Only the figure is needed to tell the two apart, and the words people write it in
# are the ones money.py already knows.
A_SUM_OF_MONEY = re.compile(
    r"£\s*[0-9]|\b[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:pounds?|quid|bucks)\b"
    r"|\b(?:tenner|fiver|score)\b"
    r"|\b(?:a|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)\s+(?:pounds?|quid|bucks)\b",
    re.I)


def follow_up(understood, memory):
    """The next line of a cooking conversation that only narrows the dish already on the table."""
    # A line that names a food they cannot have is the record's question, not a narrowing of the
    # dish: after "my son is allergic to nuts" and a dish offered, "what about pesto" must not be
    # answered with a recipe for it.
    if _says_it_has_gone_off(understood.get("clean")):
        # A recipe is no answer to "is this still ok": the food in the plan was fine when the
        # plan was made, and a dish picked from it says nothing about the one in their hand. The
        # entries' sniff test answers this line, and the plan waits for the next one.
        return None
    pointed_food = pointed_at_a_food(understood, memory)
    if pointed_food:
        return pointed_food
    plan = plan_recent(memory)
    if not plan:
        return None
    said = _clean(understood)
    # A line that asks which kinds a thing comes in is a question of its own, and the dish on the
    # table is not its subject: "what types of potato are there" two turns after a dish was named
    # was answered with the plan's next step ("mash the boiled potatoes") for a question about
    # which potatoes exist. The kinds row for the subject the line names answers it.
    if asks_the_kinds(understood):
        return None
    if _only_an_acknowledgement(said):
        return None
    if A_SUM_OF_MONEY.search(said):
        # The sum is the question and the dish on the table is not: a line that names money is
        # money.py's to answer, whatever "make" and "week" sound like in a cooking chat.
        return None
    if _a_brew_not_a_dinner(said):
        # "what about milk first or last" in a tea thread names an ingredient of the last answer,
        # so the plan reads it as "and what about the milk" and picks that food's one idea - a
        # white sauce - for a person asking which goes in the cup first. The order of a thing is
        # the entry's question (bot/knowledge/cooking_entries.py, the brew row), never a dish.
        return None
    if len(said.split()) <= 6 and any(phrase in said for phrase in PICK_PHRASES):
        # "you pick" is not a new meal: it is the one already on the plate, and the plate may
        # hold a one-ingredient idea ("a quick ragù: ...") rather than a dish from the table.
        chosen = _chosen(plan) or _idea_on_the_plate(plan, memory)
        if chosen:
            return chosen
        return None
    if int(plan.get("started") or 0) >= len(memory.get("turns") or []):
        return None                          # the meal asked for by this very line
    context = _narrowing(understood, plan)
    if not context:
        # A wish is the only thing in the plan, so nothing in it points at a dish yet - but the
        # wish is exactly what a bare "what should i cook tonight" is asking about, and the
        # entries would answer with the ten-minute list rather than the fish they said they
        # wanted more of.
        if plan.get("fancy") and not plan.get("have") and _a_bare_meal_ask(understood):
            return plan_reply(dict(plan, have=list(plan["fancy"])), memory)
        return None
    if context.get("sweet") and not (plan.get("have") or plan.get("offered")):
        # A sweet asked for with no meal on the table is the entries' dessert question: after a
        # list of quick dinners, "what about a dessert" wants the dessert list, and one sweet
        # picked from the dish table answers a meal that was never planned.
        return None
    # A line that names a food the plan has not got is asking after that food, not narrowing the
    # dish: "and what about the potatoes?" with chicken thighs in the oven wants the potatoes
    # done, and a dish picked from the whole table ("A traybake: ...") is a different dinner.
    # A food being ruled out ("and no cheese either") is a narrowing, and so is a diet.
    added = [name for name in (context.get("have") or ())
             if name not in (plan.get("have") or ())]
    if added and not (context.get("avoid") or context.get("veg") or context.get("vegan")):
        return None
    # "and no cheese either" on a dish that has no cheese in it is answered by the dish itself,
    # not by the plain entry saying the first answer over again.
    # A wish is not a larder, but it is what they would like to eat, so a dish asked for is the
    # one place it counts as the food on the table. The promoted plan is for this answer only:
    # `memory["meal"]` keeps the wish as a wish, or the next question about protein would be
    # answered with the fish.
    answering = context
    if not context.get("have") and context.get("fancy"):
        answering = dict(context, have=list(context["fancy"]))
    reply = _nothing_to_change(understood, memory) or plan_reply(answering, memory)
    if reply is None:
        return None
    if reply.strip() == str(_last_reply(memory) or "").strip():
        # "what can I do with those" after "i've got pasta and bacon" is a re-ask: the same dish
        # word for word is not an answer to it, and the other ideas for the same food are.
        others = [idea for _, idea in _ideas(answering, limit=False) if idea != reply]
        if others:
            reply = " ".join(others[:2])
    if isinstance(memory.get("meal"), dict):
        offered = context.get("offered") or memory["meal"].get("offered") or []
        context["offered"] = list(offered)[-4:]
        memory["meal"] = context              # the narrowed plan is the one that stands
    return reply


BARE_MEAL_ASK_WORDS = frozenset("""
    what shall should i we you can could do to for now then tonight tonights have eat make cook
    cooking dinner tea supper lunch meal meals something anything a an the some quick easy simple
    """.split())


def _a_bare_meal_ask(understood):
    """Whether the line asks for a dinner and names nothing else: "what should i cook tonight".

    A subject in the line makes it a question of its own - "what should i eat for protein" names
    the protein - and a plan built from a wish is not what it is asking about.
    """
    if ingredients(understood) or set(understood.get("asks") or ()) & {"how", "how_long",
                                                                      "how_much", "why"}:
        return False
    words = set(_said_words(understood))
    if not words or words - BARE_MEAL_ASK_WORDS:
        return False
    return bool(words & {"cook", "make", "cooking", "dinner", "tea", "supper", "lunch", "meal",
                         "eat"})


# A refusal, however the apostrophe is typed and however the words are split: the reading keeps
# "won\u2019t" as two words, so the refusal is read from the line instead of from its tokens.
REFUSAL = re.compile(r"\b(?:won['\u2019]?t|wouldn['\u2019]?t|don['\u2019]?t|doesn['\u2019]?t|"
                     r"didn['\u2019]?t|can['\u2019]?t stand|hates?|hated|dislikes?|refuses?|"
                     r"picky|not eat|no thanks)\b")


def _refuses(understood):
    """Whether the line rules a food out: "they won't eat mushrooms", "she doesnt like onions"."""
    if set(_said_words(understood)) & DISLIKE_WORDS:
        return True
    return bool(REFUSAL.search(_clean(understood)))


# "the best way to cook a jacket potato" asks how to cook the thing it names, and the thing's own
# method row answers that. A plan picked a dish out of the table instead: the jacket potato in a
# hurry was answered "Mash the boiled potatoes with butter and a splash of warm milk", which is
# not a jacket potato at all, and the same for "the best way to cook rice quickly" (an egg fried
# rice idea). The hurry word is how soon they want to eat, not permission to pick a different
# dish, and the line has to ask for *the way*: "something quick for dinner" is still a plan's.
THE_WAY_TO_COOK = re.compile(
    r"\b(?:best|quickest|fastest|easiest|simplest|cheapest|healthiest|healthier|safest|right|"
    r"proper|good|nice) way (?:to|of)\b"
    r"|\bthe way (?:to|of) (?:cook|cooking|make|making|bake|baking|roast|boil|fry|steam)\b")


def _meal_asked(understood):
    """Is this line a meal being asked for, rather than a dish, a bake or two foods?

    A line that names a dish ("an easy curry"), a bake ("a lemon drizzle") or two foods asks a
    question the entries and the dish table answer better, so it starts no plan. So does a line
    that asks the way to cook the one thing it names: that is the method's question.
    """
    said = _clean(understood)
    if THE_WAY_TO_COOK.search(said):
        return False                         # "the best way to cook a jacket potato"
    words = set(_said_words(understood))
    if not words & MEAL_FRAME:
        return False                         # not a meal asked for, whatever else it names
    if words & DISH_WORDS or words & BAKING_WORDS:
        return False
    if words & {"breakfast", "lunch", "brunch"}:
        return False                         # the lunch and breakfast ideas own those meals
    if len(ingredients(understood)) > 1:
        return False
    said = _clean(understood)
    return not any(phrase in said for phrase in SAID_PHRASES)


# The properties a food is asked *about*, rather than asked to be cooked: "is oat milk gluten
# free", "how many calories in rice and chicken", "how long does brown rice take".
#
# A verdict is a property of the food too, and the commonest one there is: "is oat milk ok" and
# "is almond milk ok" name two things from the kitchen (oat milk and milk, almond milk and
# almonds), so the pantry table read them as "what can I make with these" and answered a yes or
# no with a bowl of porridge and a handful of toasted almonds. A question that asks whether the
# thing is good, fine, alright, ok or bad is a fact about it, and no dish answers a fact.
FOOD_PROPERTY = re.compile(
    r"\b(?:gluten|wheat|dairy|lactose|calories|calorie|carbs|carb|protein|fat|fattening|sugar|"
    r"salt|healthy|healthier|safe|vegan|vegetarian|allergy|allergic|coeliac|"
    r"ok|okay|fine|alright|good|bad|worth it)\b", re.I)
# A line that asks for cooking, in the words people use for it, is a meal question however many
# foods it names.
COOK_REQUEST = re.compile(r"\b(?:cook|cooks|cooking|cooked|make|makes|making|bake|recipe|recipes|"
                          r"dinner|teatime|supper|lunch|meal|meals|feed|serve)\b", re.I)


def asks_a_food_fact(understood):
    """Whether the line asks a fact about the food it names instead of asking what to cook.

    "is oat milk gluten free" names two things from the kitchen (oat milk and milk), so the
    pantry table read it as "what can I make with these" and answered with a bowl of porridge;
    the person asked a yes or no, and no dinner idea answers it. Only a question qualifies, and
    only one that names no cooking of its own: "what can i make with chicken and rice" and
    "is chicken and rice a good dinner" keep their meal.
    """
    if not isinstance(understood, dict):
        return False
    said = _clean(understood)
    if not said or COOK_REQUEST.search(said):
        return False
    if not (understood.get("asks") or understood.get("kind") == "question"):
        return False
    if not FOOD_PROPERTY.search(said):
        return False
    # "how long" and "how many" on a food are figures asked for, not a dinner either.
    return True


def first_plan(understood, memory=None):
    """A meal for the first line of a conversation when it says what the meal has to be.

    "whats a quick dinner for two kids who wont eat anything green" names nothing in the kitchen
    and asks no dish by name, so nothing else in the base can answer it: the limits it gives
    (quick, no greens) are enough to pick a dish, and a dish beats a list of ideas.
    """
    plan = plan_recent(memory)
    if plan and int(plan.get("started") or 0) < len(memory.get("turns") or []):
        return None                          # a plan is running, and follow_up() has it
    context = _narrowing(understood, longest=14)
    if not context:
        return None
    if not _meal_asked(understood):
        return None
    if not any(key in context for key in ("limit", "veg", "vegan", "no_green", "occasion",
                                          "simple", "sweet")):
        return None                          # an ingredient on its own is the entries' job
    if set(context) - {"started", "turn"} <= {"veg", "vegan", "diet", "simple", "limit"}:
        # A diet and a time on their own are what the vegetarian and vegan entries answer, and
        # they answer with a list: one dish picked for "vegan friend, any easy main ideas" is a
        # narrower answer than the list, and the list is the one that lets them choose.
        return None
    if _left_to_the_meal_entry(understood, context):
        return None                          # the crowd dish and the ten-minute list are good
    return plan_reply(context)


def _left_to_the_meal_entry(understood, context):
    """True when this module's meal entries already answer the line well.

    A table of people or a birthday gets one big oven dish, and a plain "what should i cook
    tonight" gets the ten-minute list: both are in the base, and a plan should only answer when
    the line says something the entries cannot see.
    """
    text = str(understood.get("clean") or " ".join(str(w).lower()
                                                   for w in (understood.get("words") or [])))
    if _crowd(text) >= 6:
        return True
    if _occasion(text) and any(phrase in text for phrase in
                               ("cook", "dinner", "meal", "make", "eat")):
        return True
    # A sweet asked for on its own is the pudding entry's question when an entry has one: the
    # pudding entries answer it with a list of sweets, and one dish picked out of the dish table
    # is the narrower answer to the same ask ("pudding for afters" was banana pancakes, and
    # "what about a dessert" after a list of dinners). A bare "a pudding" no entry answers is
    # still the plan's, because a shrug is not an answer at all.
    if set(context) - {"started", "turn"} <= {"sweet"}:
        try:
            if find(understood) is not None:
                return True
        except Exception:  # noqa: BLE001 - a stand-down must never cost the turn
            pass
    # A pudding from an empty cupboard is a question about what the cupboard holds, and the
    # entries answer it better than a dish that assumes bananas or apples are in there.
    if set(context) <= {"sweet"} and any(phrase in text for phrase in THIN_CUPBOARD_PHRASES):
        return True
    # Nothing but "quick" or "easy": the ten-minute list answers it without picking a dish.
    if set(context) <= {"simple", "started", "turn"}:
        return True
    return False


# "what pudding can i make with what i have": the cupboard is the question, not the meal.
THIN_CUPBOARD_PHRASES = ("with what i have", "with what i've got", "with what ive got",
                         "what i have in", "in the cupboard", "in the fridge", "in the pantry",
                         "left in the")


# --- getting the seeds out of a chilli ------------------------------------------
# "how do i deseed a chilli" and "should i deseed chillies" were answered with the chilli con
# carne recipe: a chilli named in a line reached the one-pot table, and the word "chilli" alone
# carried the score. This is the preparation question, so the keys are the fruit and the words
# of taking something out of it, and the dish words stand it down.
CHILLI_FRUIT = ("chilli", "chillies", "chili", "chilies", "chile", "jalapeno", "jalapenos",
                "serrano", "birdseye", "scotch bonnet", "habanero", "red chilli", "green chilli",
                # a sweet pepper is seeded the same way, and "how do i remove the seeds from a
                # bell pepper" was a business-loan answer; the seed and pith words still have to
                # be in the line for this key to count, so "how much pepper should i add" is not
                # this entry's line
                "pepper", "peppers", "bell pepper", "bell peppers", "red pepper", "green pepper",
                "sweet pepper", "chilli pepper", "chili pepper")

# The seed words are one question whoever the fruit is: what is left once the seeds are out. The
# way to do it is the fruit's own job, so the reply is a callable and each family gets the method
# that works on it. A chilli is the one where the pith matters, because that is where the heat is.
SEED_FRUIT = CHILLI_FRUIT + ("pomegranate", "pomegranates", "tomato", "tomatoes", "cucumber",
                             "cucumbers", "courgette", "courgettes", "marrow", "pumpkin",
                             "squash", "butternut", "melon", "melons", "watermelon",
                             "aubergine", "eggplant")

_CHILLI_SEEDS = (
    "Cut the stalk off and halve it lengthways, then scrape the seeds and the pale pith out with "
    "the tip of a knife or a teaspoon - that pith is where most of the heat sits, so take it out "
    "too if you want the chilli mild. Slice it on a board, not in your hand, and keep your hands "
    "away from your eyes and your mouth. Wash the board, the knife and your hands in cold water "
    "and soap straight after: the oil that burns is not washed off by rinsing. If your hands do "
    "burn, rub them with oil then wash again, or soak them in milk, not water.")
_POMEGRANATE_SEEDS = (
    "Cut the crown off and score the skin down the ridges, then break it open in a bowl of water "
    "and knock the seeds out with a wooden spoon: the seeds sink, the pith and the membrane float "
    "and you can skim them off. Doing it under water is what stops the juice reaching your shirt, "
    "and it is much quicker than picking them out.")
_TOMATO_SEEDS = (
    "Halve it across the middle, not top to bottom, and squeeze or scoop the seeds out with a "
    "finger or a teaspoon. The jelly round them is the flavour, so keep it if you are cooking; "
    "for a sandwich or a salad, a sieve catches the juice and you can salt the halves and leave "
    "them upside down for ten minutes instead.")
_CUCUMBER_SEEDS = (
    "Halve it lengthways and run a teaspoon down the middle to scoop the watery seeds out - a "
    "grapefruit spoon has the right edge for it. Salt the halves and leave them face down for "
    "fifteen minutes afterwards and the water comes out too, which is what a soggy sandwich is.")
_MELON_SEEDS = (
    "Halve it and scoop the seeds out with a spoon, then rinse the last of the strings off under "
    "the tap. A watermelon is easier cut into wedges and the seeds flicked out with the tip of a "
    "knife, and if you want it neat, cut it in slices and stamp the seeds out with a small round "
    "cutter.")
_SQUASH_SEEDS = (
    "Halve it and scoop the strings and seeds out with a metal spoon, working round the edge "
    "towards the middle. Keep the seeds: rinse them, toss in a little oil and salt and roast "
    "them at 180C for 10 to 15 minutes.")


def _deseed(memory, understood):
    """The seeds out, by the fruit's own method."""
    words = " ".join(understood.get("words") or [])
    for family, reply in ((("pomegranate", "pomegranates"), _POMEGRANATE_SEEDS),
                          (("tomato", "tomatoes"), _TOMATO_SEEDS),
                          (("cucumber", "cucumbers", "courgette", "courgettes", "marrow"),
                           _CUCUMBER_SEEDS),
                          (("melon", "melons", "watermelon"), _MELON_SEEDS),
                          (("pumpkin", "squash", "butternut"), _SQUASH_SEEDS)):
        if any(word in words for word in family):
            return reply
    return _CHILLI_SEEDS


ENTRIES.append(entry(
    "deseed-chilli",
    (SEED_FRUIT,
     ("deseed", "de-seed", "deseeding", "seeds", "seed", "seedless", "membrane", "pith",
      "core", "coring", "take out", "take the seeds out", "remove the seeds", "remove seeds",
      "get rid of the seeds", "less hot", "not so hot", "milder", "mild", "heat")),
    _deseed,
    # the dish, the plant and the shop are not this question
    avoid=("chilli con carne", "con carne", "recipe", "grow", "growing", "plant", "plants",
           "seedling", "sow", "sowing", "germinate", "sauce", "oil", "powder", "flakes",
           "paste", "jam", "pickle", "pickled", "dry", "dried", "freeze", "freezer", "keep",
           "store", "storage", "shelf life", "go off", "best variety", "which chilli",
           "scoville", "how hot is",
           # a seed that is roasted, salted or saved for sowing is not a seed to take out
           "roast", "roasting", "roasted", "toast", "toasted", "salt", "salted", "snack",
           "saving", "save the seeds", "harvest", "collect the seeds"),
    ask=("how do i", "how to", "how can i", "should i", "do i need to", "is it better",
         "deseed", "de-seed", "seeds", "membrane", "pith"),
    # "should i deseed chillies" ties with the chilli con carne recipe, whose second half lists
    # "should i" as a phrase: the recipe scores 5 for "chilli" plus the ask. A question about
    # taking the seeds out is the more specific one, so it carries one more than the tie.
    bias=2))


# "what is umami" and "how do i get umami in food" were shrugs: nothing keyed the word, so the
# one taste people ask about by name had no answer. It explains itself (a plain "what is umami",
# "explain umami") and it carries the everyday sources as well, because the second half of the
# question is always how to get more of it on the plate.
ENTRIES.append(entry(
    "umami",
    (("umami", "the fifth taste", "savoury taste", "savory taste"),
     ("what", "how", "explain", "mean", "get", "add", "more", "boost", "taste", "tasteless",
      "food", "dish", "cook", "put", "sauce", "good", "source", "sources")),
    ("Umami is the savoury taste that makes food taste deep and round rather than just salty: it "
     "comes from glutamates, and the everyday sources are soy sauce, fish sauce, miso, tomato "
     "paste, mushrooms, hard cheese, anchovies, seaweed, stock cubes and slow-cooked meat. It is "
     "what a dish is missing when it is seasoned but still flat, so add a spoon of one of those "
     "rather than more salt, and give it a squeeze of lemon or a splash of vinegar to make it "
     "show. Parmesan, tomato and mushroom together are why a good ragu tastes bigger than its "
     "ingredients."),
    explain=True))

# Which meal it is, before what is in it: "what brunch should i make", "brunch ideas" and the
# snack lines were search punts, and "what should i make for lunch" got the ten-minute-dinner
# list - pasta, at lunchtime. Breakfast, lunch-ideas and supper already have concrete cards
# ("porridge with a spoon of peanut butter and a banana", "a sandwich or wrap with something
# filling"), so this row keeps off them and answers only the slot nothing covers, plus the one
# lunch phrasing that reached the dinner list.
SLOT_IDEAS = (
    ("brunch", (
        "Brunch is one thing on the table people help themselves to: scrambled eggs on toast with "
        "tomatoes and something green, a frittata cut into wedges, or pancakes with fruit and "
        "yoghurt. For more than four, baked eggs in one dish with bread beside it - fried eggs for "
        "eight are cold before the last one is done.")),
    ("lunch", (
        "Two shapes that work: a sandwich with something wet in it - hummus, tuna mayo, leftover "
        "roast - plus fruit, or soup with bread. The real answer is cooking extra at dinner: cold "
        "roast chicken, or lentils with feta, is a five-minute lunch the next day.")),
    ("snack", (
        "One thing with protein and one with fibre holds you until the next meal: apple with "
        "peanut butter, yoghurt with fruit, toast with cheese, or a handful of nuts.")),
)

SLOT_ASKS = ("what should i", "what can i", "what shall i", "what do i", "ideas", "any ideas",
             "suggest", "suggestions", "make", "have", "eat", "cook", "fix", "quick", "easy")


def _one_person_at_this_meal(understood):
    """Whether the line is one person's meal rather than a table to cook for.

    "what shall i make for lunch for four of us" is a table of four, and the shape for one
    person's lunch - a sandwich and a piece of fruit - is not what four people cook. The crowd
    row answers a counted table, so this row stands aside for it. Both the line as typed and the
    reading are asked: the reading puts the first person in ("for four of me"), and a table can
    only be counted off the words that were typed.
    """
    if not understood:
        return True
    for field in ("text", "clean"):
        line = str(understood.get(field) or "").lower()
        if line and _table_text(line):
            return False
    return True


def _a_meal_for_the_slot(memory, understood):
    """A shape for the meal the line names, when it names no food to cook."""
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    for slot, reply in SLOT_IDEAS:
        if " " + slot in text or slot + "s " in text:
            return reply
    return None


ENTRIES.append(entry(
    "meal-idea-for-a-slot",
    ((("brunch", "brunches", "snack", "snacks", "elevenses",
       "what should i make for lunch", "what can i make for lunch",
       "what shall i make for lunch", "what do i make for lunch"), SLOT_ASKS)),
    _a_meal_for_the_slot,
    # dinner and tea stay with the dish cards, and a food named in the line is the food's own
    # recipe or substitute
    avoid=("dinner", "tea", "tonight", "roast", "chicken", "beef", "pork", "lamb", "fish",
           "salmon", "pasta", "rice", "egg", "eggs", "potato", "potatoes", "bread", "cheese",
           "soup", "salad", "cake", "biscuit", "pancake", "porridge", "toast", "hummus",
           "sandwich", "curry", "chilli", "stew", "pie", "pizza", "noodles", "quinoa",
           "how long", "how do i cook", "how do i make", "recipe", "freeze", "leftover",
           "leftovers", "calories", "healthy", "diet", "batch", "pudding", "dessert",
           "birthday", "kids", "toddler", "baby", "weaning", "school lunch", "lunchbox",
           "restaurant", "takeaway", "book", "table for"),
    # one person's meal only: a lunch for a table is the crowd row's question
    guard=_one_person_at_this_meal,
    bias=1))


# --- what goes on top of it -------------------------------------------------------------------
# "What can i put on my toast", "... on my chips", "... on my porridge" all reached the search
# hedge, while the same question about a baked potato had an answer ("Cheese and beans, tuna mayo,
# coleslaw, chilli...") because that one was written into the jacket row and nowhere else. A
# topping is a table of staples rather than a row per question: the staple is the key, the ways of
# asking it are one list, and a new staple is one line in the table.
ON_WORDS = (
    "put on", "to put on", "put on it", "put on them", "what can i put", "what to put",
    "goes on", "go on", "have on", "add to", "add on", "add in",
    "topping", "toppings", "topping ideas", "on top",
)

# What the shape must not take. A recipe, a timing, a keeping or a shopping question belongs to
# its own row, and the dish cards answer "what can i make with", which is a different ask from
# "what can i put on". A question about something that is not a staple at all ("what can i put on
# a burn", "... on a wooden floor") never matches a staple word, so the tables cannot reach it.
NOT_A_TOPPING_ASK = (
    "how long", "how do i cook", "how do you cook", "how to cook", "how do i make",
    "how do you make", "recipe", "from scratch", "calories", "freeze", "frozen", "defrost",
    "keep", "keeps", "keeping", "kept", "fridge", "leftover", "leftovers", "left over",
    "buy", "cheaper", "price", "cost", "substitute", "instead of", "how much", "healthy",
    "diet", "make with", "make from", "batch", "bake", "roast", "boil", "fry", "grill",
    "shop", "supermarket", "brand", "best buy", "how many",
)

# One line per staple: the words people call it, then the answer. The answer names the topping
# that is fastest first and then the ones worth knowing, the way a friend standing in the kitchen
# would answer, and every one of them says what to do rather than what the thing is.
ON_TOPPINGS = (
    ("toast", ("toast",), (
        "Butter first, then something sharp or salty on top: peanut butter and sliced banana, "
        "mashed avocado with salt and lemon, beans with a dash of Worcestershire, or a tin of "
        "sardines on hot toast. Cheese on toast under the grill for 3 minutes is the fastest good "
        "one, and a sliced tomato under the cheese stops it going dry.")),
    ("pasta", ("pasta", "spaghetti", "penne", "macaroni", "fusilli", "tagliatelle", "linguine"), (
        "Something you can stir through in the time the pasta boils: garlic and chilli warmed in "
        "olive oil, a tin of tomatoes simmered 10 minutes with a pinch of sugar, or cream cheese "
        "with lemon zest and black pepper. Keep a mug of the pasta water - a splash of it makes "
        "any of them cling instead of sitting in the bottom of the bowl.")),
    ("rice", ("rice", "basmati", "long grain", "boiled rice"), (
        "Cold cooked rice is best fried: hot oil, an egg, soy sauce and whatever veg is in the "
        "drawer, 4 minutes. On hot rice, a curry or a chilli ladled over it is dinner, and cold "
        "rice with tuna, sweetcorn and mayo is a lunch - the rice wants a day old for either, "
        "because fresh rice steams instead of frying.")),
    ("chips", ("chips", "fries", "french fries"), (
        "Salt and vinegar, gravy, curry sauce, garlic mayo, or cheese and chilli: chip-shop curry "
        "sauce is the one to try if you want the bag to feel like a treat. A fried egg on top "
        "makes it a meal, and mushy peas or a pickled onion cut through the fat.")),
    ("porridge", ("porridge", "oats", "oatmeal"), (
        "Sweet: honey or jam with a spoon of peanut butter, stewed apple with cinnamon, or frozen "
        "berries stirred in while it is hot. Savoury: butter, salt and a poached egg, or grated "
        "cheese and black pepper - porridge is only oats cooked in water or milk, so it takes "
        "either, and the salt is what makes the sweet version taste of something.")),
    ("noodles", ("noodles", "noodle", "ramen"), (
        "A sauce in the time they boil: a spoon of peanut butter, soy sauce, a squeeze of lime and "
        "some chilli; or fry them with an egg and whatever veg you have plus soy sauce. Sesame "
        "oil and sliced spring onion at the end is what makes them taste like the takeaway.")),
    ("couscous", ("couscous",), (
        "Couscous takes a dressing better than it takes a sauce: lemon juice, olive oil, chopped "
        "tomato, cucumber, parsley and feta is a lunch in 10 minutes. It also drinks up the juices "
        "of a stew or roast veg, which is why it is served under them.")),
    ("salad", ("salad", "leaves", "lettuce", "rocket"), (
        "Something sharp, something salty, something crunchy: olive oil and lemon or vinegar, "
        "then salt, then nuts, seeds or croutons. A dressing of 2 parts oil to 1 part vinegar "
        "with a spoon of mustard, shaken in a jar, keeps a week in the fridge.")),
    ("crackers", ("crackers", "cracker", "crispbread", "oatcakes"), (
        "Cheese, chutney and an apple; cream cheese with smoked salmon or cucumber; hummus and "
        "something crunchy; butter and a sliced boiled egg with salt and pepper. Anything soft "
        "wants something crisp on it, and anything dry wants something wet.")),
    ("soup", ("soup",), (
        "A swirl of cream or yogurt loosens a thick soup, and something crisp on top - croutons, "
        "toasted seeds, a handful of crushed crisps - makes it feel finished. A squeeze of lemon "
        "or a splash of vinegar at the end lifts a soup that tastes flat, which is usually what "
        "it is missing rather than salt.")),
    ("pancakes", ("pancakes", "pancake", "crepes", "crepe"), (
        "Lemon and sugar is the classic, and butter with golden syrup or jam works as well "
        "without the fuss. For savoury, fold cheese and ham inside, or put a fried egg on top. "
        "Keep them warm in a low oven and add the topping at the table, so nothing goes soggy.")),
    ("ice-cream", ("ice cream", "icecream", "gelato"), (
        "Hot chocolate sauce, tinned peaches or raspberries with a splash of their juice, crushed "
        "biscuits or toasted nuts, and a pinch of salt on anything caramel. A shot of espresso "
        "over vanilla is affogato, which is the best 30-second pudding there is.")),
    ("yoghurt", ("yoghurt", "yogurt"), (
        "Fruit and a spoon of honey, granola or toasted oats for crunch, and nuts or seeds for "
        "texture; a spoon of peanut butter and a little cocoa makes it taste like dessert. Plain "
        "yoghurt with chopped cucumber, mint, salt and garlic is a dip instead, and it wants "
        "straining first if it is watery.")),
)

for _staple, _words, _reply in ON_TOPPINGS:
    ENTRIES.append(entry("topping-on-" + _staple, (_words, ON_WORDS), _reply,
                         avoid=NOT_A_TOPPING_ASK))
del _staple, _words, _reply
