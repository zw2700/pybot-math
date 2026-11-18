"""Drink: which bottle goes with the food that is named.

The answers lane owns this domain. A pairing is a fact about a food, not a sentence about a
person, so the key is the word for wine crossed with the words that ask the pairing question,
and the reply is chosen from the food the line names. The cooking domain already holds a
`wine-with-food` row that answers every pairing question with one paragraph on weight ("a light
white with fish or chicken, a fuller red with red meat"); that rule is right when the line names
no food and useless when it names one, because "what wine goes with pizza" wants a bottle. This
domain therefore answers only the lines that name a food or a meal, and returns None otherwise,
so the cooking row keeps the rest.

Nothing here is ageing or priced: the wine is named by grape or region, which does not go out of
date the way a bottle and a price on a shelf does.

The second half is the drink itself. "What does prosecco taste like", "what is a flat white", "is
gin strong" and "what does prosecco go with" are four questions about one thing, so they are one
table keyed by the drink and four rows that read their answer off it. A drink named in a line is
answered about that drink however the line is worded; a line about the machine, the price, the
shelf, the brewing or the shop keeps its own answer.
"""
import re

from .lookup import entry

ANSWERS = ("food-and-drink",)

# One pair per family of food, in the order a line usually names them. The first word that
# appears in the line decides, so the list runs from the most specific food to the least:
# "chicken curry" is a curry, and both words are in the line.
_PAIRS = (
    (("fish", "salmon", "trout", "prawn", "prawns", "seafood", "cod", "haddock", "sushi",
      "shellfish", "mussels", "scallops", "whitebait", "sea bass"),
     "A dry white is the safe pair: Sauvignon Blanc, Picpoul, Albarino or a dry Riesling. "
     "Salmon and trout take a light red such as Pinot Noir just as well."),
    (("curry", "curries", "tikka", "masala", "balti", "thai", "korma", "jalfrezi", "madras",
      "chilli con carne", "tacos", "burrito", "mexican", "salsa", "spicy", "hot wings",
      "indian", "biryani", "kebab", "falafel"),
     "An off-dry Riesling or a Gewurztraminer: a little sweetness cools the heat. Lager or a "
     "pale ale work just as well, and a big oaky red is the one to avoid."),
    (("chinese", "stir fry", "stir-fry", "noodles", "szechuan", "sichuan", "dumplings",
      "spring rolls", "sushi rice"),
     "Riesling or a dry rose, or a pale ale with the fried things: sweetness suits the soy and "
     "the spice, and a heavy red fights both."),
    (("steak", "beef", "lamb", "venison", "game", "burger", "burgers", "casserole", "stew",
      "roast beef", "brisket", "ribs"),
     "A red with some grip: Malbec, Cabernet Sauvignon, Syrah or a Rioja. Lamb likes claret, "
     "and a slow-cooked stew likes the same reds."),
    (("chicken", "turkey", "pork", "veal", "roast chicken", "sausage", "sausages", "ham"),
     "Chicken and pork take either: a Chardonnay or white Burgundy, or a light red such as "
     "Pinot Noir or Grenache. Roast chicken with a red is the usual choice in a pub."),
    (("pasta", "pizza", "lasagne", "lasagna", "bolognese", "ragu", "tomato", "tomatoes",
      "meatballs", "parmigiana"),
     "Sangiovese or Chianti: the acidity in the wine meets the tomato, and a heavy oaky red "
     "tastes flat next to it."),
    (("cheese", "cheeses", "cheddar", "brie", "blue cheese", "stilton"),
     "Match the weight: a crisp white with goat's cheese and a soft rind, a red with cheddar, "
     "and port or a sweet wine with blue."),
    (("chocolate", "dessert", "pudding", "cake", "trifle", "ice cream", "fruit tart"),
     "A wine as sweet as the pudding: port or Banyuls with chocolate, and a sweet Riesling or "
     "Muscat with fruit puddings. A dry red turns bitter next to sugar."),
    (("salad", "vegetarian", "veggie", "quiche", "omelette", "soup", "risotto", "pasta salad"),
     "Sauvignon Blanc, a dry rose or a light red served cool: light food wants a light wine."),
)

# A meal with no food named: "what wine with a roast dinner", "which wine with dinner". The
# weight rule is the right answer here, and it is the one the cooking row gives, so this domain
# gives it too and keeps the answer in one place per line.
_MEALS = ("dinner", "dinner party", "meal", "lunch", "supper", "christmas", "barbecue", "bbq",
          "st patricks", "takeaway", "takeout")

_WEIGHT = ("Match the weight of the food: a dry white with fish or a light starter, a red with red "
           "meat and anything tomatoey, and a touch of sweetness with spicy food. If a bottle is "
           "all you have, a dry rose or a medium red sits happily with most things on the table.")


def _named(text, words):
    """Whether the line names one of these foods, as whole words."""
    for word in words:
        pattern = r"(?<![a-z0-9])" + re.escape(word) + r"(?:s|es)?(?![a-z0-9])"
        if re.search(pattern, text):
            return True
    return False


def _wine_pair(memory, understood):
    """The bottle that goes with the food named, or the weight rule for a meal with no food.

    Returns None when the line names neither, so a bottle to buy, a gift, a unit count and a
    wine stain all stay with the rows that answer them.
    """
    text = (understood or {}).get("clean") or (understood or {}).get("text") or ""
    text = str(text).lower()
    if not text:
        return None
    for foods, answer in _PAIRS:
        if _named(text, foods):
            return answer
    if _named(text, _MEALS):
        return _WEIGHT
    return None


# "red or white with chicken" asks the pairing question without ever saying the word wine, and
# "what should i drink with fish" asks it with "drink". Both are here rather than in a second
# row, so one row owns the whole question.
ENTRIES = [
    entry("wine-with-the-food",
          (("wine", "wines", "red or white", "white or red", "drink with", "drinking with"),
           ("goes with", "go with", "goes down", "pair", "pairs", "pairing", "match", "matches",
            "with", "for", "best", "which", "serve", "serving", "have", "have with",
            "should i have", "bring", "take", "bottle", "red or white", "recommend")),
          _wine_pair,
          # The cooking domain's one-paragraph weight rule answers the same lines, so this row
          # has to outrank it when it is willing to answer; when it declines, that row answers.
          bias=4,
          # A bottle to buy, a price, a gift or a party bottle is the shopping side of wine; the
          # open bottle, the units and the health lines are three other rows; and a wine in the
          # pan is a method, not a pairing.
          avoid=("buy", "buys", "buying", "bought", "cheap", "cheaper", "cheapest", "money",
                 "tenner", "tenners", "value", "spend", "budget", "afford", "supermarket",
                 "shop", "shops", "shopping", "offer", "offers", "deal", "deals", "price",
                 "gift", "present", "birthday", "wedding", "bring to",
                 "open", "opened", "unopened", "keep", "keeps", "keeping", "last", "lasts",
                 "how long", "left over", "leftover", "vinegary", "gone off", "corkscrew",
                 "opener", "fridge", "chill", "chilled", "cold", "temperature", "decant",
                 "units", "unit", "limit", "safe", "too much", "a day", "every day", "week",
                 # a medicine named next to a drink is the alcohol-and-medicine question: "is it
                 # ok to drink with paracetamol" was answered with a wine pairing
                 "paracetamol", "ibuprofen", "painkiller", "painkillers", "antibiotic",
                 "antibiotics", "penicillin", "amoxicillin", "metronidazole", "tablets",
                 "medicine", "medication", "pills", "prescription", "antihistamine",
                 "antidepressant", "statins", "codeine",
                 "pregnant", "alcohol free", "alcohol-free", "non alcoholic", "sober",
                 "hangover", "calories", "good for", "bad for", "health", "healthy",
                 "stain", "stains", "spill", "spilled", "spilt", "sofa", "carpet", "shirt",
                 "cook", "cooks", "cooking", "cooked", "recipe", "recipes", "sauce", "stew",
                 "casserole", "marinate", "marinade", "deglaze", "substitute",
                 "instead of", "glaze", "gravy", "oven", "bake")),

# The module answered the pairings and nothing else, so a drink to make at home was a shrug: "how
# do i make lemonade", "how do i make iced tea" and "how do i froth milk for coffee" were all
# "I don't know enough to answer that honestly", "how do i make mulled wine" was "I'm not sure
# about that one", and "how do i make hot chocolate" reached the cut-the-liquid-sugar card, which
# is an answer about a diet. These four rows make the drink; a bottle to buy, a unit count and a
# machine that has broken each stay with the row that answers them.
entry("lemonade-and-iced-tea",
      # iced tea was in this key until #5072 landed its cold-brew answer, which is the better one:
      # the row went back to lemonade and squash, the two drinks nothing else made.
      # a bare "squash" is the vegetable, and "how do i make a squash" is the roast answer;
      # only the fruit ones in front of it are the drink
      (("lemonade", "homemade lemonade", "cordial", "orange squash", "lemon squash",
        "blackcurrant squash", "lime cordial"),
       ("make", "making", "made", "how do i", "how to", "recipe", "homemade", "from scratch",
        "what goes in")),
      "Squeeze three lemons into 100g of sugar dissolved in 100ml of just-boiled water, top it up "
      "with a litre of cold water and taste it - a pinch of salt makes it taste more of lemon, "
      "not less. A squash is the same drink from a bottle of cordial, and a sprig of mint or a "
      "sliced lemon in the jug is what a pub does. It keeps two days in the fridge.",
      # a bottle to buy, the sugar in a fizzy drink and a stain are three other rows
      avoid=("buy", "buys", "shop", "supermarket", "price", "cost", "offer", "brand",
             "calories", "how much sugar", "healthy", "good for", "bad for", "stain",
             "stains", "spill", "carpet", "fizzy", "coke", "cola",
             "wine", "beer", "gin", "vodka", "cocktail", "pint", "alcohol"),
      bias=2),
entry("mulled-wine",
      (("mulled wine", "gluhwein", "mulled cider", "wassail", "mulled"),
       ("make", "making", "recipe", "homemade", "how do i", "how to", "what goes in")),
      "Warm a bottle of red with two tablespoons of sugar, a sliced orange, a cinnamon stick, two "
      "star anise and four cloves: keep it at a bare shiver for 15 minutes and never let it boil, "
      "which takes the alcohol and the fruit out of it. A splash of brandy at the end makes it "
      "stronger, and mulled cider is the same drink made with cider and no sugar.",
      # the bottle to buy, the units and the alcohol-free question are other rows
      avoid=("buy", "shop", "price", "cost", "gift", "present", "units", "unit", "limit",
             "pregnant", "alcohol free", "alcohol-free", "non alcoholic", "sober", "hangover",
             "how long does it keep"),
      bias=2),
entry("hot-chocolate",
      (("hot chocolate", "hot cocoa", "drinking chocolate", "cocoa"),
       ("make", "making", "recipe", "how do i", "how to", "proper", "best", "what goes in")),
      "Warm 200ml of milk and melt 20g of dark chocolate into it, chopped small, stirring until it "
      "is smooth - a pinch of salt makes it taste more of chocolate, not less. Cocoa powder works "
      "too: a teaspoon each of cocoa and sugar made into a paste with a little cold milk first, so "
      "it does not go lumpy. Keep it under a simmer, because milk that boils tastes cooked.",
      # the calories, the caffeine and a stain are three other answers, and a dairy-free drink is
      # a swap rather than a recipe: "how do i make hot chocolate without milk" wants what to use
      # instead, which the dairy-free row already answers
      avoid=("calories", "calorie", "diet", "lose weight", "caffeine", "sleep", "before bed",
             "stain", "stains", "spill", "buy", "brand", "mug", "healthy", "good for",
             "without milk", "no milk", "dairy free", "dairy-free", "oat milk", "plant milk",
             "almond milk", "soy milk", "vegan", "lactose"),
      bias=2),
# Water hardness is a food-and-drink question and no row answered the health half of it: "is
# hard water bad for you" was answered with the descaling recipe (home.limescale-why keys the
# words "hard water"), and "why is my water hard" was the dry-eye card, because "water" is the
# tear film's word.
entry("hard-water",
      (("hard water", "water is hard", "water hard", "water is so hard", "water so hard",
        "water hardness", "hardness", "water is very hard",
        "hard and soft water", "soft water", "chalky water",
        # Not "limescale in my water": this row held the word and it cost `home.limescale` the
        # answer to "what can i do about limescale", which came back as nothing at all
        # (`tests/test_a_plain_limescale_line_keeps_its_answer.py` is red on main `3ae8d520`
        # because of it, bisected to `51211851`). "hard water" and its own phrases carry every
        # line this row gained, so the word goes back to the row that owns it.
        "minerals in the water", "minerals in my water"),
       ("bad for you", "bad for", "safe", "safely", "ok", "okay", "fine", "drink", "drinking",
        "drank", "harmful", "dangerous", "healthy", "health", "kidney", "kidneys", "stones",
        "skin", "eczema", "dry", "why", "cause", "causes", "softener", "soften", "filter",
        "bottled", "baby", "formula", "milk", "boil", "calcium", "safe to drink")),
      ("Not bad for you: the calcium and magnesium that make water hard are minerals you get from "
       "food anyway, mains water is tested to the same standard whatever its hardness, and the "
       "studies find no link between hard water and kidney stones - some find slightly fewer "
       "stones in hard-water areas. It is hard because it has come through chalk or limestone, "
       "which is why the same country has soft water in the west and hard water in the south "
       "east. What it does do is leave a chalky film on taps, kettles and shower glass, lather "
       "soap and shampoo less so you use more of them, and feel drier on the skin - a filter jug "
       "or a scale reducer is enough for most homes. The one to know about is a baby's bottle: a "
       "water softener swaps the calcium for sodium, so make formula with unsoftened mains water, "
       "boiled once and cooled."),
      # the descaling recipe, the kettle and the appliance are other answers, and so is the water
      # bill or the contract for it
      avoid=("kettle", "kettles", "descale", "descaling", "descales", "scale", "scaled",
             "limescale", "shower", "showerhead", "shower head", "taps", "marks", "stains",
             "iron", "steam iron", "washing machine", "dishwasher", "bill", "bills", "meter",
             "supplier", "account", "contract", "cancel", "standing charge", "swimming",
             "pool", "fish", "aquarium", "pond", "plant", "plants", "garden"),
      bias=1),

# How much milk is in a coffee is a figure people ask for by name - "how much milk in a latte",
# "how much milk is in a cappuccino", "how much milk in a flat white" - and no row held it: the
# milk rows answered the drink's nutrition ("a 200ml glass has about 7g of protein") and a flat
# white reached the house-price row, because "flat" is a flat's word. The answer is the portion
# of milk each drink is built on, which is the same figure for the calories and the shopping.
entry("milk-in-a-coffee",
      (("latte", "cappuccino", "flat white", "mocha", "macchiato", "cortado", "piccolo",
        "latte macchiato",
        # "latte" is being respelled to "late" by the understanding engine's typo map, so the
        # commonest way of asking this line matches only on the respelled word. Reported to
        # #understanding; this row carries the word until that is fixed there.
        "late"),
       # The portion has to be asked for. A bare "milk" let the row take any line that mentions
       # milk beside a respelled "latte" - "i was late for work and had no milk" got the coffee
       # lecture - so the ask is the phrases that ask how much of it there is. Found by
       # plucky-frame on #13381.
       ("ml", "millilitres", "milliliters", "how much milk", "milk goes in",
        "milk in it", "milk in a", "milk in the", "milk in my", "ml of milk", "milk to",
        "ratio",
        "how much of it is milk", "mostly milk", "milk does it have", "ounces of milk",
        "coffee goes in", "coffee in it", "coffee to milk", "how much of it")),
      "Most of the cup is milk: a latte is about five parts steamed milk to one of espresso, so "
      "roughly 200ml of milk and a 60ml double shot in a medium, and 300 to 350ml of milk in a "
      "large. A flat white is the same coffee with about half of that, 100 to 120ml, and a "
      "cappuccino sits between the two at about 150ml - a third of it foam, so ask for it wet if "
      "you want more milk and dry if you want more air. A macchiato or a cortado is a splash, 20 "
      "to 40ml, and a mocha is a latte with chocolate in it.",
      # the calories, the caffeine, the sugar, a machine and the foam are other answers, and a
      # drink to make at home is the method rather than the portion
      avoid=("calorie", "calories", "kcal", "sugar", "caffeine", "decaf", "decaffeinated",
             "diet", "lose weight", "healthy", "good for", "bad for",
             # the count of calories or spoons is another answer, but "how many ml of milk in a
             # latte" is this one, so the count words are named and not the bare "how many"
             "how many calories", "how many kcal", "how many spoons", "how many sugars",
             "price", "cost", "buy", "cheap", "stain", "stains", "spill", "spilt",
             "machine", "froth", "frothing", "foam", "latte art", "recipe", "make a",
             "make one", "make my own", "how do i make", "how to make", "barista",
             # a swap is the substitutes row's question: "can i use milk instead of cream in a
             # latte" is about the cream and not about how much milk the drink holds
             "instead of", "instead", "in place of", "substitute", "substitutes", "swap",
             "replace", "rather than", "out of milk", "ran out"),
      bias=2),

entry("froth-milk",
      (("froth", "frothed", "frothing", "frother", "frothy milk", "milk foam", "steamed milk",
        "microfoam", "foam on my coffee"),
       ("milk", "coffee", "how do i", "how to", "without", "no machine", "jar", "cafetiere",
        "french press", "latte", "cappuccino")),
      "Cold milk in a jar with a lid, shaken hard for 30 seconds and then 30 seconds in the "
      "microwave, gives a real foam with no machine, and a French press pumped up and down 15 "
      "times does the same. Whole milk froths best because the fat holds the bubbles, and stop "
      "heating at about 60 to 65C - past that the foam collapses and the milk tastes scalded.",
      # a machine to buy, clean or descale is another row, and so is the coffee itself
      # "without a machine" is this row's own question, so the fence is the machine's problems and
      # not the word "machine": a bare `machine` here sent "how do i froth milk without a machine"
      # to the buttermilk substitute, which is what a wet ingredient is for.
      avoid=("coffee machine", "my machine", "machine is", "machine not", "machines", "buy",
             "descale", "limescale", "clean", "cleaning", "broken", "not working",
             "coffee shop", "latte art", "stain", "bean", "beans", "grinder"),
      bias=2),

# "what kinds of tea are there" was answered with "Quick: tuna pasta in 15, a frittata in 20" - the
# ten-minute dinners - because "kinds of" is a shape the meal row reads as "what can i make". The
# kinds of a drink is a fact, not a list of dinners, so the drink's own row answers it. The brewing
# row keeps "how do i make green tea" and the differences row keeps a named pair, because this one
# only opens on a question about kinds, types or the choice between them.
entry("tea-types",
      (("tea", "teas", "green tea", "black tea", "white tea", "oolong", "pu erh", "pu-erh",
        "herbal tea", "herbal teas", "rooibos", "camomile", "chamomile", "earl grey",
        "english breakfast", "assam", "darjeeling", "jasmine tea", "peppermint tea",
        "fruit tea", "fruit teas", "infusion", "infusions"),
       ("kinds", "kind", "types", "type", "sorts", "are there", "difference", "differences",
        "different", "which one", "which is", "which should", "which do", "what are",
        "what's the difference", "whats the difference", "choose", "pick", "best",
        "caffeine free", "no caffeine", "without caffeine",
        # "what tea should i drink" is the same question asked as a choice, and it reached a
        # search hedge: the kinds answer, with a pick for each way of drinking it, is the reply
        "should i", "should we", "what should i", "recommend", "recommendation", "what tea")),
      "Nearly all of it is the same leaf at different levels of oxidation: green tea is dried "
      "before it can darken and tastes grassy, black tea is fully oxidised and malty, and oolong "
      "sits between them, roasted and floral. White tea is the young leaf barely processed, light "
      "and sweet, and pu-erh is aged and earthy, an acquired taste. Peppermint, chamomile and "
      "rooibos are infusions of other plants rather than tea, so they have no caffeine and suit "
      "the evening. Everyday picks: English breakfast or Assam if you take milk, Earl Grey for "
      "the citrus, and a plain green or jasmine drunk without milk.",
      # a cup to make, a pot going cloudy and a bag gone bitter are the brewing row's; a limit,
      # a bedtime and a pregnancy are health rows; matcha, chai and bubble tea are drinks of
      # their own; and a biscuit or a cake with it is the baking row.
      avoid=("brew", "brewing", "brewed", "steep", "steeped", "how long", "bitter", "stewed",
             "cloudy", "teabag", "teabags", "tea bag", "tea bags", "kettle", "cuppa",
             "how much", "caffeine", "pregnant", "pregnancy", "baby", "babies", "toddler",
             "child", "sleep", "bedtime", "before bed", "stain", "stains", "spill", "making",
             "make", "recipe", "mug", "cup of", "buy", "price", "brand", "supers",
             "bubble tea", "boba", "chai", "matcha", "coffee", "espresso", "cake", "biscuit",
             "biscuits", "scone", "sugar",
             # a daily amount is a limit rather than a kind, and "is tea bad for you" is the
             # health row's line
             "every day", "a day", "a week", "how many cups", "bad for", "good for",
             "healthy", "health"),
      bias=2),
]

# ---- what a drink tastes like -----------------------------------------------------------
#
# "what does a flat white taste like" and "what does prosecco taste like" were a shrug on main,
# and three lines were worse than a shrug: an americano was told how to fix a machine that tastes
# wrong, an espresso was sold a descaler, and green tea got the brewing times. A taste is a fact
# about the drink, so it is one table keyed by the name people type - the drink decides the
# answer - in the same shape as the music genres and the things put away for the winter.
#
# Each row is (the names, what it is, what it tastes like, what it goes with). The three
# questions are answered off one table so "what is a flat white", "what does a flat white taste
# like" and "what does a flat white go with" cannot give three different accounts of it.
_DRINKS = (
    (("flat white", "flat whites"),
     "A flat white is a double shot of espresso under a thin layer of steamed milk, about 160ml "
     "in the cup.",
     "Strong and milky at once: the coffee is at the front and the milk softens it without hiding "
     "it, and the foam is a thin glossy layer rather than a cap you eat with a spoon.",
     "It is a morning coffee on its own. With food, a plain croissant or a slice of toast beats "
     "anything sweet, because the milk and the sugar fight."),
    (("latte", "lattes", "caffe latte"),
     "A latte is one or two shots of espresso topped up with a lot of steamed milk, in a tall "
     "glass or a big cup.",
     "Milky and mild: the milk is most of the drink and the coffee is a soft bitterness behind it, "
     "with a thin foam on top. Ask for it with an extra shot if you want to taste the coffee.",
     "It is milky enough to drink with breakfast or a sweet thing, and it goes flat with a sharp "
     "lemon cake or anything acidic."),
    (("cappuccino", "cappuccinos", "capuccino"),
     "A cappuccino is an espresso with equal parts steamed milk and thick foam, usually in a "
     "smaller cup than a latte.",
     "It is a third coffee, a third milk and a third foam, so the first sip is dry foam and the "
     "coffee is stronger and shorter than in a latte. In Italy it is a morning drink, not one for "
     "after a meal.",
     "Best with something plain at breakfast - a pastry or a biscuit - and it is the wrong coffee "
     "to sit beside a meal."),
    (("americano", "americanos", "caffe americano", "long black"),
     "An americano is one or two shots of espresso with hot water added, so it is black coffee "
     "made in a cup.",
     "Black and clean, with the coffee's bitterness and no milk to soften it: longer and less "
     "intense than an espresso, because the water thins it. A long black is the same thing with "
     "the water in the cup first, which keeps more of the crema.",
     "It is the coffee for a meal or for a long sit, and the one to order if milk upsets you."),
    (("espresso", "espressos", "expresso", "double espresso", "short black"),
     "An espresso is a small, strong shot of coffee forced through finely ground beans by a "
     "machine, about 25 to 30ml.",
     "Concentrated and bittersweet with a thick crema on top: coffee, caramel and a dry finish, "
     "drunk in two or three sips. It has less caffeine than a mug of filter coffee, not more.",
     "It is the finish to a meal rather than a drink with one, and a small sweet thing beside it "
     "is the Italian way."),
    (("macchiato", "macchiatos", "latte macchiato"),
     "A macchiato is an espresso with a spoonful of milk foam on top. A latte macchiato is the "
     "other way round: a glass of hot milk with a shot poured into it.",
     "An espresso macchiato tastes of the coffee with a soft, slightly sweet top; a latte "
     "macchiato is milky with a coffee layer sitting above it, so the first sip is coffee and the "
     "rest is warm milk.",
     "A macchiato is a two-minute coffee on its own; the latte macchiato is a breakfast drink."),
    (("mocha", "mochas", "caffe mocha", "mocha latte"),
     "A mocha is a latte with chocolate syrup or powder stirred into the espresso before the milk "
     "goes in.",
     "Sweet and chocolatey, coffee second: it is closer to a hot chocolate with a kick than to a "
     "coffee, and the chocolate hides a weak shot. Ask for half the syrup if you want to taste "
     "the coffee at all.",
     "It is a pudding as much as a drink, so it wants no cake beside it."),
    (("filter coffee", "filter", "cafetiere", "french press", "drip coffee", "black coffee"),
     "Filter coffee is ground coffee steeped in hot water and then filtered out, through paper in "
     "a dripper or a metal mesh in a cafetiere.",
     "Cleaner and lighter than an espresso, with the fruit and the acidity of the bean still in "
     "it: it tastes of tea and fruit as much as of coffee, and it goes bitter if it is left to "
     "stew on a hot plate.",
     "It is the drink for a second cup, and it takes milk and food better than an espresso does."),
    (("cold brew", "cold brew coffee"),
     "Cold brew is ground coffee steeped in cold water for 12 to 18 hours and then strained, and "
     "served over ice.",
     "Round and low in acid, sweeter than hot-brewed coffee with almost none of the sharpness, "
     "and it is stronger in caffeine than the same volume of filter coffee because the ratio is "
     "concentrated.",
     "It is a summer drink: neat over ice, or cut with milk like a latte."),
    (("green tea",),
     "Green tea is unfermented tea leaf, brewed at about 80C rather than boiling.",
     "Grassy and light, with a sweetness at the back and a slight bitterness or astringency if it "
     "is left to steep - the leaves keep giving, so a second brew is softer than the first.",
     "It goes with rice, fish and anything light, and it is the drink to have with sushi."),
    (("earl grey", "earl gray", "earl grey tea"),
     "Earl grey is black tea scented with bergamot, the citrus oil from a bitter orange.",
     "Black tea first, then the bergamot on top: floral and perfumed, and it turns soapy if the "
     "milk is heavy or the bag is left in too long.",
     "It wants a slice of lemon rather than milk, and a plain biscuit or a scone."),
    (("matcha", "matcha tea", "matcha latte"),
     "Matcha is green tea leaf ground to a powder and whisked into hot water, so the whole leaf is "
     "drunk rather than steeped and thrown away.",
     "Vegetal and savoury, like spinach and fresh grass, with a bitterness that stays in the "
     "mouth. In a latte the milk turns it sweet and soft, and the colour is the point as much as "
     "the taste.",
     "It is good with anything sweet and milky, and it fights with citrus."),
    (("chai", "chai tea", "chai latte", "masala chai"),
     "Chai is black tea boiled with milk, sugar and whole spices - cardamom, ginger, cinnamon, "
     "cloves - so it is a spiced milky tea rather than tea with a flavour.",
     "Warm and sweet, with the spices arriving after the tea: ginger heat, cardamom and clove "
     "behind the milk. A chai latte in a coffee shop is the same idea with more sugar and foam.",
     "It is a winter drink and it takes a biscuit or something fried and savoury."),
    (("prosecco",),
     "Prosecco is a sparkling white wine from northern Italy, made in a tank rather than in the "
     "bottle, which keeps it cheap and fruity.",
     "Light and fizzy with green apple, pear and a little white flower: it is off-dry rather than "
     "sweet, and the bubbles make it feel fresher and less alcoholic than it is. Drink it young - "
     "it does not improve in the bottle.",
     "It goes with salty and fried things - crisps, olives, fried fish - and with fruit desserts; "
     "it is the wrong glass for a steak."),
    (("champagne", "sparkling wine", "cava", "cremant", "cremant de loire"),
     "Champagne is sparkling wine from the Champagne region of France, fermented a second time in "
     "the bottle, which is what the price pays for. Cava and cremant are made the same way "
     "elsewhere.",
     "Tighter and more yeasty than prosecco: brioche and toast from the time on the lees, with a "
     "sharper acidity and a finer bubble, and the best of it is dry rather than sweet.",
     "It goes with oysters, fried food and salty nuts, and with a roast chicken as well as with a "
     "celebration."),
    (("red wine",),
     "Red wine is wine fermented with the skins of the grapes, which is where the colour and the "
     "tannin come from.",
     "From light and juicy to heavy and drying depending on the grape: the tannin is the grip that "
     "dries your mouth, and it is what makes a young red taste harsh with nothing to eat.",
     "It goes with red meat, stews and hard cheese, and badly with anything vinegary or very "
     "spicy."),
    (("white wine",),
     "White wine is wine fermented without the skins, so it is pale and lower in tannin.",
     "From bone dry and citrusy to sweet and honeyed: the cool-climate ones taste of lemon and "
     "green apple and the warm ones of peach and melon, and oak adds vanilla and butter.",
     "It goes with fish, chicken, salads and soft cheese, and a dry one is the safer glass with "
     "food than a red."),
    (("rose", "rosé", "rose wine", "pink wine"),
     "Rosé is wine that spent a few hours with the red grape skins, enough for the colour and not "
     "for the tannin.",
     "Fresh and dry, usually with strawberry, watermelon and a little citrus, and served cold. The "
     "pale Provencal kind is the driest; the darker, sweeter ones are a different drink.",
     "It goes with salads, grilled vegetables, chicken and anything you would eat outdoors."),
    (("lager", "lagers"),
     "Lager is beer brewed with a bottom-fermenting yeast at a cold temperature and then stored, "
     "which is where the clean taste comes from.",
     "Crisp and cold, lightly bitter and dry at the end, with very little fruit: the point is how "
     "clean it is, which is why it goes with almost everything.",
     "It goes with a curry, fish and chips, pizza and a hot day. The colder it is the less you "
     "taste it, so a good one is served cool rather than iced."),
    (("ipa", "ipas", "india pale ale", "pale ale"),
     "An IPA is a heavily hopped pale ale; the hops were originally there to keep the beer on the "
     "voyage to India.",
     "Bitter and citrusy or piney, with the hop flavour at the front and a long bitter finish. A "
     "hazy New England IPA is softer and fruitier, and a pale ale is the same idea turned down.",
     "It goes with a burger, fried chicken or a strong cheese, and it flattens a delicate fish."),
    (("stout", "stouts", "guinness", "porter"),
     "Stout is a dark beer brewed with roasted barley, which is where the coffee and chocolate "
     "come from.",
     "Roasted and smooth: coffee, dark chocolate and a dry, bitter finish, and the creamy sort is "
     "served on nitrogen so the head is thick and the bubbles are tiny.",
     "It goes with oysters, stews and chocolate, and it is a meal in itself compared with a lager."),
    (("cider", "ciders"),
     "Cider is fermented apple juice. In the UK it is alcoholic and still or sparkling; in the US "
     "the word usually means the cloudy juice.",
     "From bone dry and tannic to sweet and appley: the dry ones taste of the fruit and the skin "
     "and the sweet ones of juice, and the strength varies more than with beer.",
     "It goes with pork, cheese and anything with apple in it, and it is the drink for a pub "
     "garden."),
    (("gin", "gin and tonic"),
     "Gin is a clear spirit distilled with juniper and then other botanicals, and a gin and tonic "
     "is that with tonic water and ice.",
     "Juniper first, then whatever the maker put in - citrus peel, coriander, angelica, sometimes "
     "cucumber or violet. The tonic adds bitterness and sugar, so a G&T tastes of the tonic as "
     "much as the gin.",
     "It goes with olives, salted nuts and fried fish; it is a before-dinner drink."),
    (("whisky", "whiskey", "scotch", "bourbon", "single malt"),
     "Whisky is a spirit distilled from grain and aged in wood, which is where the colour and most "
     "of the flavour come from. Scotch and bourbon are the two most people meet.",
     "From light and honeyed to smoky and medicinal: bourbon is sweeter and tastes of vanilla and "
     "caramel from the new oak, and a peated Scotch of smoke and tar. A drop of water opens it up "
     "rather than diluting it.",
     "It goes with dark chocolate, blue cheese and a fire, and it is not a drink to have with a "
     "meal."),
    (("vodka",),
     "Vodka is a spirit distilled to as close to pure alcohol and water as the law allows, then "
     "cut to strength.",
     "Almost nothing, which is the point: clean and slightly sweet at the front and hot at the "
     "back, with the flavour coming from whatever it is mixed with. A cheap one tastes of the "
     "distillery and a good one of nothing.",
     "It goes with tonic, tomato juice or a martini glass, and with salty things."),
    (("rum",),
     "Rum is distilled from sugar cane or its molasses. The clear kind is unaged; the dark kind is "
     "aged in wood.",
     "Sweet and round, with vanilla, caramel and sometimes a burnt sugar edge; a white rum is "
     "lighter and drier, and an aged one is closer to a whisky in weight.",
     "It goes with lime and ginger beer, and with anything you would put brown sugar on."),
    (("beer", "beers", "a pint of beer", "real ale"),
     "Beer is brewed from grain, usually barley, with hops for bitterness and yeast for the "
     "alcohol.",
     "From light and crisp to dark and roasted, depending on the malt: the hops give the bitterness "
     "and the fruit, the malt gives the sweetness and the colour. Most beer is between 4 and 5.5 "
     "per cent, and served colder than wine.",
     "It goes with fried food, pizza, curry and a hot afternoon, and a hoppy one with a burger."),
    (("coffee", "coffees", "a coffee"),
     "Coffee is the roasted and ground seed of a fruit, brewed with hot water.",
     "Bitter and acidic at once, with the roast on top: darker roasts taste of chocolate and "
     "toast, lighter ones of fruit and citrus, and the bitterness is the part that survives milk "
     "and sugar.",
     "It goes with anything sweet in the morning and with nothing much after a meal, which is why a "
     "small espresso is the usual finish."),
    (("tea", "teas", "a cup of tea", "builder's tea"),
     "Tea is the leaf of one plant, Camellia sinensis, brewed in hot water; how it is processed "
     "decides whether it is black, green or white.",
     "Tannin first: dry and slightly astringent, with the flavour of the leaf behind it, and it goes "
     "bitter if it is left in the water too long. Milk softens the tannin, which is why a strong "
     "tea takes milk and a delicate one does not.",
     "It goes with a biscuit, a slice of cake or a fried breakfast, and it is the drink for bad "
     "news."),
    (("oat milk", "oat drink", "oatly", "oat milk latte"),
     "Oat milk is oats soaked, blended and strained, with an enzyme step that turns some of the "
     "starch to sugar, which is why it is the plant milk that foams.",
     "Oaty and faintly sweet like the milk left at the bottom of a bowl of porridge, with a "
     "creaminess that comes from the oats rather than fat. In coffee the ordinary sort splits and "
     "tastes of cardboard; a barista version has oil added and holds.",
     "It goes with coffee, cereal and anything oaty or banana-flavoured, and it curdles in a "
     "strong acid the way no dairy milk does."),
    (("baileys", "irish cream", "cream liqueur"),
     "Irish cream is whiskey, cream and sugar, homogenised so the cream does not separate - "
     "Baileys is the one everybody means.",
     "Sweet and thick, of whiskey and cream with a chocolate edge: it is a pudding in a glass "
     "rather than a drink, and the alcohol is under the sugar.",
     "It goes over ice, in coffee and over vanilla ice cream. Do not put it in a citrus drink - "
     "the acid splits the cream - and keep the bottle in the fridge once it is open."),
    (("negroni", "negronis"),
     "A negroni is equal parts gin, Campari and sweet vermouth, stirred over ice and poured over "
     "a big cube with a strip of orange peel.",
     "Bitter first, then sweet and herby: the Campari is the grapefruit-and-rhubarb bitterness, "
     "the vermouth is the sweetness behind it, and the gin is the spine rather than the flavour.",
     "It is an aperitivo before dinner rather than a drink with food, and it is strong: about 24 "
     "per cent once mixed, so one is the usual."),
    (("aperol spritz", "spritz", "spritzes", "aperol"),
     "A spritz is three parts prosecco, two parts Aperol and a splash of soda, over ice in a wine "
     "glass with a slice of orange.",
     "Light, fizzy and bittersweet - orange and rhubarb from the Aperol, the wine behind it - and "
     "much weaker than it looks, because most of the glass is ice and prosecco.",
     "It is a drink for a hot afternoon or before dinner. It goes with salty things - olives, "
     "crisps, a bowl of nuts - and nothing sweet."),
    (("kombucha",),
     "Kombucha is sweet tea fermented with a culture of yeast and bacteria, which turns the sugar "
     "into acid and a little alcohol.",
     "Sour and slightly fizzy, like a vinegar you can drink, with the fruit or herb it was brewed "
     "with on top: it is the sourness, not the sweetness, that most people notice first.",
     "It goes with sushi and anything rich, and it is a good stand-in for a beer at lunch."),
)

# How strong each drink is, in the order a bar sells it: a typical figure, not a promise, because
# the same drink comes at different strengths. This is the question a first drink raises - "is gin
# strong", "how strong is prosecco" - and the answer is a number rather than a flavour.
_STRENGTH = {
    "vodka": "About 37.5 to 40 per cent alcohol. A 25ml measure is roughly one unit.",
    "gin": "About 37.5 to 40 per cent alcohol, so a 25ml measure is roughly one unit; a double "
           "with tonic is about two, which is more than a pint of ordinary lager.",
    "rum": "About 37.5 to 40 per cent alcohol, so a 25ml measure is roughly one unit.",
    "whisky": "About 40 per cent alcohol, so a 25ml measure is roughly one unit; cask strength "
              "bottlings go up to 60 per cent and need water.",
    "lager": "About 4 to 4.5 per cent, so a pint is roughly two units. A premium lager or a "
             "strong continental one runs to 5 per cent and more.",
    "ipa": "Usually 5 to 6.5 per cent, so a pint is about three units; a double IPA can be 8 per "
           "cent or more.",
    "ale": "About 4 to 5 per cent, so a pint is roughly two to two and a half units.",
    "stout": "About 4.2 per cent for the usual draught stout, so a pint is about two and a half "
             "units; an imperial stout is a different drink at 9 per cent and up.",
    "beer": "Ordinary draught beer is about 4 per cent and a strong one 5 to 6, so a pint is "
            "roughly two to three units.",
    "cider": "About 4.5 per cent for most, but cider runs from 1.5 per cent to 8 and more, so "
             "check the bottle: a pint of 7.5 per cent cider is nearly four units.",
    "prosecco": "About 11 per cent, so a 125ml glass is roughly 1.4 units - a little less than "
                "the same glass of wine.",
    "champagne": "About 12 per cent, so a 125ml glass is roughly 1.5 units.",
    "white wine": "About 11 to 13 per cent, so a 175ml glass is roughly two units and a large "
                  "250ml glass about three.",
    "rose": "About 11 to 12.5 per cent, so a 175ml glass is roughly two units.",
    "red wine": "About 13 to 14 per cent, so a 175ml glass is roughly 2.3 units - a large glass "
                "is over three. White is usually a little weaker at 11 to 13 per cent, so a red "
                "is stronger, but not by much.",
    "baileys": "About 17 per cent, so a 50ml measure is roughly 0.9 units - and it comes in "
               "measures, not a tumbler, for that reason.",
    "negroni": "About 24 per cent once mixed, since it is a third each of gin, Campari and "
               "vermouth, so a negroni is about 2.2 units.",
    "spritz": "About 8 to 11 per cent, because the prosecco is stretched with soda and ice, so a "
              "large glass is roughly 1.5 units - weaker than a glass of wine.",
    "oat milk": None,
    "coffee": None, "tea": None, "green tea": None, "earl grey": None, "matcha": None,
    "chai": None, "kombucha": None, "flat white": None, "latte": None, "cappuccino": None,
    "americano": None, "espresso": None, "macchiato": None, "mocha": None, "filter coffee": None,
    "cold brew": None,
}
_ITS_STRENGTH = ("strong", "stronger", "strongest", "weaker", "strength", "how strong",
                 "alcohol", "alcohol content", "more alcohol", "less alcohol", "abv", "units",
                 "per cent", "percent", "proof", "get drunk", "drunk")


def _how_strong(memory, reading):
    """How strong the drink named in the line is, when the line asks that rather than the taste."""
    row = _a_drink(reading)
    if row is None:
        return None
    said = str(reading.get("clean") or reading.get("text") or "").lower()
    for name in row[0]:
        if name in said:
            # "how strong is a pint of guinness" names the drink by the brand and the brand has
            # no figure of its own - the row does, under the word for the family of drink. A name
            # people use is never a reason to answer nothing.
            return _STRENGTH.get(name) or _STRENGTH.get(row[0][0])
    return None


# What each of those drinks is asked about. The three questions live in one place so a row can
# answer them without a word list of its own.
# "what does" is deliberately not here: it is the frame of the pairing question as well ("what
# does prosecco go with") and the taste question always says taste as well ("what does prosecco
# taste like"), so the word that carries the question is the word for tasting it.
_ITS_TASTE = ("taste like", "tastes like", "taste of", "tastes of", "taste", "tastes",
              "how does it taste", "what is it like", "like to drink", "whats it like",
              "what's it like", "sweet", "bitter", "fizzy", "flavour", "flavor",
              # "nice" is not a taste word: "something nice for tea" is a dinner ask and
              # "something nice for my mum" is a present, and with "nice" in this group the
              # tea row answered the first of those with how tea tastes. The words a taste
              # question is asked with are in this group; the words a different question is
              # asked with must keep out of it.
              "taste good", "tastes good")
_ITSELF = ("what is", "whats", "what's", "tell me about", "explain", "define", "definition",
           "difference", "compare", "how is it made", "made of")
_GOES_WITH = ("go with", "goes with", "goes in", "pair with", "pairs with", "eat with",
              "have with", "go best", "go well", "match", "drink with", "food with")
# The four questions are not the machine, the price, the bottle shop or the recipe: those are
# other rows and other answers, and a line asking any of them must keep its own.
_NOT_A_TASTE = ("machine", "machines", "descale", "descaling", "grinder", "grind", "beans",
                "bean", "ground", "recipe", "how do i make", "how to make", "how do you make",
                "at home", "barista", "cup", "cups", "mug", "shop", "buy", "sell", "price",
                "prices", "cost", "how much", "cheap", "expensive", "priced", "stock", "shelf",
                "supermarket", "calories", "caffeine", "how many units", "alcohol", "safe",
                "pregnant", "breastfeeding", "bed", "sleep", "before a run", "water", "hydration",
                "stain", "stains", "sugar", "sugars", "addict", "allergy", "allergic",
                "reaction", "heartburn", "acid reflux", "thin", "thinning", "wine stain",
                "corked", "hangover", "bottle", "vintage", "cellar", "keep", "storing", "store",
                "freeze", "open a bottle", "opens", "shelf life", "use by", "date",
                # a drink that tastes of something it should not is the brewing, not the drink
                "tastes wrong", "taste wrong", "tastes off", "tastes funny", "tastes bad",
                "taste bad", "tastes stale", "tastes burnt", "tastes sour", "tastes flat",
                "gone off", "off milk",
                # and "what is a good beer" is a recommendation, not a definition
                "for a beginner", "for beginners", "good one", "good beer", "good wine",
                "best beer", "best wine", "recommend", "suggest", "which one")


_DRINK_NAMES = tuple(name for row in _DRINKS for name in row[0])


# The cup in their hand is a different question from the drink in general: "my coffee tastes
# bitter" and "this tea is stewed" are the brewing, not what coffee or tea is like.
_MY_OWN_CUP = ("my coffee", "my tea", "my drink", "my latte", "my beer", "my wine", "this coffee",
               "this tea", "this beer", "this wine", "the coffee i", "the tea i", "instant")


def _a_drink(reading):
    """The drink named in the line, as its row, or None."""
    said = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    said = re.sub(r"[^a-z0-9' ]+", " ", said)
    if any(" " + phrase + " " in said for phrase in _NOT_A_TASTE):
        return None
    if any(" " + phrase + " " in said for phrase in _MY_OWN_CUP):
        return None
    best = None
    for row in _DRINKS:
        names = row[0]
        for name in names:
            if " " + name + " " in said:
                if best is None or len(name) > best[0]:
                    best = (len(name), row)
    return best[1] if best else None


def _the_drink_taste(memory, reading):
    """What the drink named in the line tastes like."""
    row = _a_drink(reading)
    if row is None:
        return None
    return row[2]


def _the_drink_itself(memory, reading):
    """What the drink is, for the line that asks what it is rather than what it tastes like."""
    row = _a_drink(reading)
    if row is None:
        return None
    said = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    # "what is prosecco like" is the taste question wearing the definition's words
    if " like " in said or said.rstrip().endswith(" like"):
        return row[2]
    return row[1]


def _what_it_goes_with(memory, reading):
    """What to eat with it."""
    row = _a_drink(reading)
    if row is None:
        return None
    return row[3]


# The two-drink questions, answered one pair at a time: a comparison built out of two separate
# taste sentences reads like a shopping list, and the difference is usually one thing.
_DIFFERENCES = {
    ("cappuccino", "latte"):
        "A latte is the milkier of the two: a lot of steamed milk with a thin foam on top, in a "
        "bigger cup. A cappuccino is a third coffee, a third milk and a third foam, in a smaller "
        "cup, so it is drier to drink and tastes more of the coffee.",
    ("flat white", "latte"):
        "A flat white is smaller and stronger: a double shot under a thin, glossy layer of milk. A "
        "latte is mostly milk. Order the flat white for the coffee and the latte for something "
        "mild and long.",
    ("cappuccino", "flat white"):
        "Both are small and strong. The flat white has thinner, glossier milk and no foam cap; the "
        "cappuccino is a third foam, so the first sip is dry and there is less milk under it.",
    ("americano", "espresso"):
        "An americano is an espresso with hot water added: the same coffee, a longer drink, and "
        "much less intense. An espresso is the 25 to 30ml shot on its own, with a thick crema.",
    ("champagne", "prosecco"):
        "Champagne is fermented a second time in the bottle, so it tastes of brioche and toast with "
        "a sharper acidity; prosecco is made in a tank, so it is fruitier, lighter and cheaper. "
        "Both are dry, and prosecco is the easier one to drink.",
    ("ale", "lager"):
        "Lager is fermented cold with a bottom yeast, so it is clean, crisp and lightly bitter. An "
        "ale is fermented warm, so it tastes fruitier and more bitter from the hops.",
    ("ipa", "lager"):
        "An IPA is far hoppier - bitter, citrusy or piney, with a long finish - and usually "
        "stronger. A lager is clean and light, and the point of it is that it tastes of very "
        "little.",
    ("cider", "lager"):
        "Cider is fermented apple juice, so it tastes of fruit and is often sweeter; beer is "
        "brewed from grain, so it tastes of hops and malt. Dry cider is the one closest to a "
        "lager in weight.",
    ("red wine", "white wine"):
        "Red is fermented with the grape skins, which gives it the colour and the tannin that dries "
        "your mouth; white has no skins, so it is lighter in body and tastes of citrus, apple and "
        "stone fruit. Reds suit red meat, whites suit fish and chicken.",
    ("green tea", "black tea", "earl grey"):
        "Green tea is unfermented leaf brewed at about 80C, so it is grassy and light. Black tea is "
        "fully oxidised and brewed boiling, so it is darker and maltier and takes milk; earl grey "
        "is black tea with bergamot oil on it.",
    ("gin", "vodka"):
        "Gin is vodka with juniper and other botanicals distilled in, so it tastes of something. "
        "Vodka is distilled to taste of almost nothing, which is why it is the one you mix.",
    ("whisky", "vodka"):
        "Whisky is grain spirit aged in wood, so it is coloured and tastes of vanilla, caramel or "
        "smoke; vodka is unaged and filtered to be neutral. Whisky is sipped and vodka is usually "
        "mixed.",
    ("matcha", "green tea"):
        "Matcha is green tea leaf ground to a powder and whisked into the water, so you drink the "
        "whole leaf: it is stronger, creamier and more bitter than green tea, which is the leaf "
        "steeped and taken out.",
    ("cappuccino", "flat white", "mocha"):
        "A mocha is a latte with chocolate in it: sweet, and coffee second. A flat white is the "
        "strongest of the milky coffees and a cappuccino is the foamiest.",
}


def _the_difference(memory, reading):
    """Two drinks named in one line: what the difference is."""
    said = " " + str(reading.get("clean") or reading.get("text") or "").lower() + " "
    said = re.sub(r"[^a-z0-9' ]+", " ", said)
    found = []
    for row in _DRINKS:
        for name in row[0]:
            if " " + name + " " in said:
                found.append((said.index(" " + name + " "), row[0][0]))
                break
    found.sort()
    if len(found) < 2:
        return None
    pair = {found[0][1], found[1][1]}
    for names, reply in _DIFFERENCES.items():
        if pair <= set(names):
            return reply
    # a pair this file does not hold: the two accounts, in the order the line names them
    rows = {row[0][0]: row for row in _DRINKS}
    first, second = rows.get(found[0][1]), rows.get(found[1][1])
    if first is None or second is None:
        return None
    return first[1] + " " + second[1]


ENTRIES.append(entry("drink-taste", (_DRINK_NAMES, _ITS_TASTE), _the_drink_taste,
                     avoid=_NOT_A_TASTE, bias=1))
ENTRIES.append(entry("drink-strength", (_DRINK_NAMES, _ITS_STRENGTH), _how_strong,
                     avoid=_NOT_A_TASTE, bias=3))
ENTRIES.append(entry("drink-what-it-is", (_DRINK_NAMES, _ITSELF), _the_drink_itself,
                     avoid=_NOT_A_TASTE, bias=1))
ENTRIES.append(entry("drink-goes-with", (_DRINK_NAMES, _GOES_WITH), _what_it_goes_with,
                     avoid=_NOT_A_TASTE, bias=2))
ENTRIES.append(entry("drink-difference",
                     (_DRINK_NAMES, ("difference between", "difference", "vs", "versus",
                                     "compared")), _the_difference, bias=3))
