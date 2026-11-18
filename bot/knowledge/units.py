"""The one table of units: every measure people ask about, converted by meaning.

This is shared knowledge, not a domain: it declares no ENTRIES of its own and
bot/knowledge/__init__.py leaves it out of the domain registry. bot/knowledge/maths.py's
solve() asks it first, so "how many grams in a pound", "20 miles in km", "12 stone in kg",
"how many cups in a litre" and "180 c to f" are all answered by the same table instead of
one regex per question, and every new unit helps every question about it.

A unit is a name, the words people type for it, and how much of the family's base unit it is
(the metre, the gram, the millilitre, the metre per second). A line is answered only when it
names a measure and the unit wanted, in the same family; anything else returns None, so an
ordinary line with a number in it ("I bought 2 pounds of mince") is left to the other
modules. Answers are rounded the way a person says them: "20 miles is about 32.2 km", never
"32.1869".
"""
import math
import re

# Metric first in each family: metric and imperial units are marked in SYSTEM below, so a
# conversion between the two can say "about" and one inside a system can be exact.
UNITS = {
    "length": [
        ("mm", ("mm", "millimetre", "millimetres", "millimeter", "millimeters"), 0.001),
        ("cm", ("cm", "centimetre", "centimetres", "centimeter", "centimeters"), 0.01),
        ("m", ("m", "metre", "metres", "meter", "meters"), 1.0),
        ("km", ("km", "kilometre", "kilometres", "kilometer", "kilometers"), 1000.0),
        ("inch", ("in", "inch", "inches"), 0.0254),
        ("foot", ("ft", "foot", "feet"), 0.3048),
        ("yard", ("yd", "yard", "yards"), 0.9144),
        ("mile", ("mi", "mile", "miles"), 1609.344),
    ],
    "mass": [
        ("mg", ("mg", "milligram", "milligrams"), 0.001),
        ("g", ("g", "gram", "grams", "gramme", "grammes"), 1.0),
        ("kg", ("kg", "kilogram", "kilograms", "kilo", "kilos"), 1000.0),
        ("ounce", ("oz", "ounce", "ounces"), 28.349523125),
        ("pound", ("lb", "lbs", "pound", "pounds"), 453.59237),
        ("stone", ("st", "stone", "stones"), 6350.29318),
    ],
    "volume": [
        ("ml", ("ml", "millilitre", "millilitres", "milliliter", "milliliters"), 1.0),
        ("l", ("l", "litre", "litres", "liter", "liters"), 1000.0),
        ("tsp", ("tsp", "teaspoon", "teaspoons"), 5.0),
        ("tbsp", ("tbsp", "tablespoon", "tablespoons"), 15.0),
        # A dessertspoon is 10 ml and is how British recipes say "a spoon" for sugar or syrup.
        ("dessertspoon", ("dsp", "dessertspoon", "dessertspoons"), 10.0),
        ("cup", ("cup", "cups"), 240.0),
        # A mug is how people who cook without scales measure, and 250 ml is the mug they
        # mean: "how many ml in a mug", "how much does a mug of water weigh".
        ("mug", ("mug", "mugs"), 250.0),
        ("fl oz", ("fl oz", "floz", "fluid ounce", "fluid ounces"), 28.4131),
        ("pint", ("pt", "pint", "pints"), 568.261),
        ("gallon", ("gal", "gallon", "gallons"), 4546.09),
    ],
    "speed": [
        ("km/h", ("kmh", "km/h", "kph", "kilometres an hour", "kilometers an hour",
                  "kilometres per hour", "kilometers per hour"), 1.0),
        ("mph", ("mph", "miles an hour", "miles per hour"), 1.609344),
    ],
    # Time is a family like the others, so "how many minutes in 2 hours" and "90 minutes in
    # hours" are the same table the grams and miles come from. Months and years are left out
    # on purpose: they have no fixed length, and the calendar facts are in maths.FACTS.
    "time": [
        ("second", ("s", "sec", "secs", "second", "seconds"), 1.0),
        ("minute", ("min", "mins", "minute", "minutes"), 60.0),
        ("hour", ("hr", "hrs", "hour", "hours"), 3600.0),
        ("day", ("day", "days"), 86400.0),
        ("week", ("week", "weeks"), 604800.0),
        # A fortnight is an ordinary word for two weeks, and people ask what it is in days.
        ("fortnight", ("fortnight", "fortnights"), 1209600.0),
    ],
    # Land is measured in its own units, and they are not length squared in the asking: an
    # acre, a hectare and a square mile are the words people buy, sell and inherit ground in.
    # The base is the square metre, so "how many square metres in an acre" and "5 acres in
    # hectares" are the same two-number question as the grams and the miles.
    "area": [
        ("sq m", ("sq m", "square metre", "square metres", "square meter", "square meters",
                  "m2", "sqm"), 1.0),
        ("hectare", ("hectare", "hectares"), 10000.0),
        ("sq km", ("sq km", "square kilometre", "square kilometres", "square kilometer",
                   "square kilometers", "km2", "sqkm"), 1000000.0),
        ("sq ft", ("sq ft", "square foot", "square feet", "sqft", "ft2"), 0.09290304),
        ("sq yd", ("sq yd", "square yard", "square yards", "sqyd", "yd2"), 0.83612736),
        ("acre", ("acre", "acres"), 4046.8564224),
        ("sq mile", ("sq mile", "square mile", "square miles", "sqmi", "mi2"),
         2589988.110336),
    ],
}

SYSTEM = {"mm": "metric", "cm": "metric", "m": "metric", "km": "metric", "mg": "metric",
          "second": "metric", "minute": "metric", "hour": "metric", "day": "metric",
          "week": "metric", "fortnight": "metric",
          "g": "metric", "kg": "metric", "ml": "metric", "l": "metric", "tsp": "metric",
          "tbsp": "metric", "km/h": "metric", "inch": "imperial", "foot": "imperial",
          "yard": "imperial", "mile": "imperial", "ounce": "imperial", "pound": "imperial",
          "stone": "imperial", "mph": "imperial", "pint": "imperial", "gallon": "imperial",
          "fl oz": "imperial", "cup": "us",
          "sq m": "metric", "hectare": "metric", "sq km": "metric", "sq ft": "imperial",
          "sq yd": "imperial", "acre": "imperial", "sq mile": "imperial"}

SAID = {"second": "seconds", "minute": "minutes", "hour": "hours", "day": "days",
        "week": "weeks", "fortnight": "fortnights",
        "mm": "mm", "cm": "cm", "m": "metres", "km": "km", "inch": "inches", "foot": "feet",
        "yard": "yards", "mile": "miles", "mg": "mg", "g": "grams", "kg": "kg",
        "ounce": "ounces", "pound": "pounds", "stone": "stone", "ml": "ml", "l": "litres",
        "tsp": "teaspoons", "tbsp": "tablespoons", "dessertspoon": "dessertspoons",
        "cup": "cups", "pint": "pints",
        "gallon": "gallons", "km/h": "km/h", "mph": "mph", "fl oz": "fl oz",
        "sq m": "square metres", "hectare": "hectares", "sq km": "square kilometres",
        "sq ft": "square feet", "sq yd": "square yards", "acre": "acres",
        "sq mile": "square miles"}

SAID_ONE = {"second": "second", "minute": "minute", "hour": "hour", "day": "day",
            "week": "week", "fortnight": "fortnight",
            "inch": "inch", "foot": "foot", "yard": "yard", "mile": "mile", "ounce": "ounce",
            "pound": "pound", "stone": "stone", "cup": "cup", "pint": "pint",
            "gallon": "gallon", "tsp": "teaspoon", "tbsp": "tablespoon",
            "dessertspoon": "dessertspoon", "m": "metre",
            "fl oz": "fluid ounce", "l": "litre", "g": "gram", "km": "km",
            "kg": "kilogram", "ml": "ml", "mm": "mm",
            "mg": "mg", "cm": "cm", "km/h": "km/h", "mph": "mph",
            "sq m": "square metre", "hectare": "hectare", "sq km": "square kilometre",
            "sq ft": "square foot", "sq yd": "square yard", "acre": "acre",
            "sq mile": "square mile"}

# What a cup of these weighs, for the cup questions people actually ask. Cups measure
# volume, so a food's weight is the food's own: this is the one table that can say it, and
# a food added here answers every way of asking about it. Liquids are close to the cup.
GRAMS_PER_CUP = (
    ("icing sugar", 120), ("brown sugar", 220), ("sugar", 200),
    ("flour", 120), ("cornflour", 120), ("oats", 90),
    ("butter", 227), ("margarine", 227),
    ("rice", 185), ("couscous", 175), ("lentils", 190), ("breadcrumbs", 110),
    ("milk", 240), ("water", 240), ("cream", 240), ("yogurt", 245), ("yoghurt", 245),
    ("honey", 340), ("oil", 220), ("jam", 320), ("peanut butter", 260),
    ("grated cheese", 100), ("cheese", 100),
    ("chocolate chips", 170), ("chocolate", 170), ("cocoa", 85),
    ("nuts", 140), ("almonds", 140), ("cashews", 140), ("peanuts", 145), ("walnuts", 100),
    ("raisins", 150), ("pumpkin seeds", 130),
    ("salt", 288), ("baking powder", 190),  # a teaspoon: 6 g salt, 4 g baking powder
)

# What a level spoon weighs, for the things a cook measures by the spoon and never by the cup:
# salt, raising agents, spice. A cup of salt is not a recipe, a teaspoon of it is.
GRAMS_PER_TSP = (
    ("baking powder", 4), ("bicarbonate", 4), ("bicarb", 4), ("baking soda", 4),
    ("yeast", 3), ("salt", 6), ("cinnamon", 2.6), ("paprika", 2.4), ("cumin", 2.1),
    ("turmeric", 2.4), ("cayenne", 1.8), ("spice", 2.5), ("pepper", 2.3),
    ("sugar", 4.2), ("cocoa", 2.5), ("flour", 2.6), ("cornflour", 2.5), ("butter", 4.7),
    ("oil", 4.5), ("honey", 7), ("milk", 5), ("water", 5), ("oats", 3),
)

# What one of a thing weighs, for the questions a recipe asks by the piece rather than by
# the cup: "how many grams in an egg", "how much does an onion weigh". The name is the piece
# a cook counts, so a clove and a bulb, a rasher and a slice, can each be their own row, and
# a food added here answers every way of asking about it. The figures are the usual size of
# what a shop sells, which is what someone standing at a scale wants.
PIECE_GRAMS = (
    ("clove of garlic", 5), ("garlic clove", 5), ("bulb of garlic", 45),
    ("garlic bulb", 45),
    ("slice of bread", 36), ("slice of ham", 20), ("slice of cheese", 20),
    ("slice of bacon", 25), ("rasher", 25),
    ("slice of cake", 60), ("slice of pizza", 100), ("slice of toast", 30),
    ("bread roll", 60), ("crumpet", 60), ("pancake", 40),
    ("chicken breast", 170), ("chicken thigh", 100), ("drumstick", 100),
    ("egg", 55), ("banana", 120), ("apple", 150), ("orange", 140), ("satsuma", 70),
    ("pear", 170), ("peach", 150), ("plum", 70), ("lemon", 100), ("lime", 70),
    ("avocado", 150), ("potato", 170), ("onion", 150), ("carrot", 80), ("tomato", 120),
    ("courgette", 200), ("pepper", 160), ("mushroom", 20), ("aubergine", 250),
    ("cauliflower", 700), ("broccoli", 400),
    ("swede", 900), ("cucumber", 300), ("butternut squash", 1000), ("sweet potato", 200),
    ("cabbage", 900), ("leek", 200), ("parsnip", 150), ("beetroot", 150), ("turnip", 250),
    ("head of celery", 400), ("head of broccoli", 400), ("head of cauliflower", 700),
    ("bunch of grapes", 400), ("punnet of strawberries", 300),
    # a bunch of herbs is a handful of stems, and spring onions are bought by the bunch
    ("bunch of spring onions", 100), ("bunch of spring onion", 100),
    ("bunch of parsley", 30), ("bunch of coriander", 30), ("bunch of mint", 30),
    ("bunch of basil", 30), ("bunch of dill", 20), ("bunch of thyme", 20),
    ("bunch of rosemary", 20), ("bunch of chives", 20), ("bunch of sage", 20),
    ("punnet of cherry tomatoes", 250), ("punnet of raspberries", 300),
    ("lettuce", 300), ("head of lettuce", 300), ("iceberg lettuce", 600), ("round lettuce", 200),
    ("punnet of blueberries", 200), ("fennel bulb", 250), ("red cabbage", 900),
    ("sausage", 60), ("strawberry", 12), ("sprout", 10), ("raspberry", 4),
    # the two a packet is counted by, so "how many biscuits in a packet" and "how many squares
    # in a bar of chocolate" are a division of the two tables rather than a list of their own
    ("biscuit", 10), ("square of chocolate", 10),
)

# The rows above that name a whole thing on the shelf - "a head of broccoli", "a punnet of
# strawberries" - and the same phrase said as a question. "How many grams in a head of broccoli"
# is the weight of one head, but the portion table has a broccoli row, so it answered "about 80 g
# of broccoli each" while "a head of cauliflower" worked: the whole-thing phrases are what tell
# the two apart, and only a headcount said in the line overrules them.
_WHOLE_PIECE = tuple(name for name, _grams in PIECE_GRAMS if " of " in name)

# A dish is not the ingredient counted in its name: "how many grams in an apple pie" is not a
# question about one apple. The same goes for a cup or a litre, which the convert code owns.
_DISH_AFTER = re.compile(
    r"\s+(?:pie|pies|bread|soup|soups|sandwich|sandwiches|curry|curries|salad|salads|sauce|"
    r"sauces|cake|cakes|tart|tarts|crumble|smoothie|smoothies|juice|juices|jam|chutney|toast|"
    r"stew|stews|casserole|risotto|pizza|pizzas|burger|burgers|wrap|wraps|muffin|muffins|"
    r"pancake|pancakes|batter|filling|topping|chips|mash|puree|dip|dressing|mayo|stock|broth|"
    r"crisps|pickle|relish|ketchup|crust|pastry|dough|flour|powder|extract|oil|wine|"
    r"cordial|squash|tea|coffee|milkshake|yoghurt|yogurt)\b")
_MEASURE_AFTER_PIECE = re.compile(
    r"\b(?:in|into)\s+(?:cups?|ml|mls|millilitres?|milliliters?|litres?|liters?|pints?|"
    r"fl\s*oz|fluid ounces?)\b")

# "A head of broccoli", "a bunch of grapes" and "a punnet of strawberries" are one thing on the
# shelf, so the container word belongs to the piece's own name and does not make the line a pack
# question. A tin, a jar or a packet is the opposite: what is inside is many pieces, so those keep
# the piece out and the pack table answers the line.
_WHOLE_THING = re.compile(r"\b(?:heads?|bunch(?:es)?|punnets?)\s+of\s+")
# A piece is only the piece when the line counts it ("an egg", "2 onions"), and never when
# it comes out of a tin, a jar or a loaf: a tin of tomatoes is not a tomato.
_UNCOUNTED = re.compile(
    r"\b(?:tin|tins|can|cans|jar|jars|packet|packets|pack|packs|box|boxes|bag|bags|"
    r"punnet|punnets|bunch|bunches|tub|tubs|carton|cartons|loaf|loaves|head|heads|"
    r"handful|handfuls|scoop|scoops|bottle|bottles)\b")
# A count is any way a cook says how much of a thing: "2", "1.5", "three", "half a",
# "a quarter of", "one and a half". A quarter of an onion is a real amount to ask about, and
# the count scales the piece's own weight.
_COUNT = re.compile(
    r"(?<![\w.])(three[\s-]quarters?|two[\s-]thirds?|half|a\s+half|quarter|a\s+quarter"
    r"|a\s+third"
    r"|(?:one|two|three|four)\s+and\s+a\s+half"
    r"|\d+(?:\.\d+)?|a|an|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"(?:\s+of)?(?:\s+an?)?"
    r"\s+(?:(?:small|large|medium|big|whole|ripe|fresh|cooked|raw)\s+)?$")

# Some foods are only ever measured this way in a kitchen, so the reply says so:
# a cup of cheese is grated cheese, and 100 g of a block would be nearer 113 g.
AS_KITCHEN_SAYS = {"cheese": "grated cheese", "chocolate": "grated chocolate",
                   "cocoa": "cocoa powder"}

# A food answers with a cup's weight only when the line asks how much a cup of it weighs;
# a line asking what is *in* it (protein, sugar, calories) wants a different answer.
_COMPONENT = re.compile(
    r"\bhow (?:much|many)\s+(?:of\s+)?(?:grams?\s+of\s+)?"
    r"(?:sugar|salt|fat|protein|fibre|fiber|carbs?|carbohydrates?|calories|kcal|alcohol|"
    r"caffeine|sodium|calcium|iron|vitamins?)\b")
_WEIGH = re.compile(r"\b(?:weigh|weighs|weight|heavy|heavier)\b")

# "how much sugar is in a teaspoon" is the spoon's question, and the component guard refused it
# as a nutrition question while "how many grams in a teaspoon of sugar" was 4.2 g. The component is
# the whole of what is measured when the measure holds nothing else, so those lines are let past
# the guard; "a cup of tea" and "a can of coke" hold something else and stay nutrition questions.
_COMPONENT_MEASURED = re.compile(
    r"\bhow (?:much|many)\s+(?:of\s+)?(?:grams?\s+of\s+)?"
    r"(?P<component>sugar|salt|fat|protein|fibre|fiber|carbs?|carbohydrates?|calories|kcal|"
    r"alcohol|caffeine|sodium|calcium|iron|vitamins?)"
    r"(?:\s+(?:is|are)(?:\s+there)?)?\s+(?:in|per)\s+(?:a|one|1|an)\s+"
    r"(?:level\s+|heaped\s+)?(?P<measure>teaspoons?|tablespoons?|tbsp|tsp|dessertspoons?|"
    r"spoons?|spoonfuls?|cups?)(?:\s+of\s+(?P<again>[a-z]+))?\s*[?.!]*$")


def _the_component_is_the_whole_measure(clean):
    """True when the component word is all the measure holds: "a teaspoon of sugar"."""
    found = _COMPONENT_MEASURED.search(clean)
    if not found:
        return False
    again = found.group("again")
    if not again:
        return True
    component = found.group("component")
    return again in (component, component + "s")


# A dry food in a cup or a spoon is a weight too, and the weight tables hold it, but the line has
# to ask for a weight in so many words or it may want a pour instead ("how much water for two cups
# of tea"). These are the things people do weigh out, so "how much flour in a cup" is rewritten
# into the question the table reads and answered from the same one table.
_DRY_IN_A_MEASURE = re.compile(
    r"\bhow (?:much|many)\s+(?:of\s+)?(?:grams?\s+of\s+)?"
    r"(?P<food>icing sugar|brown sugar|cocoa powder|cocoa|cornflour|breadcrumbs|peanut butter|"
    r"flour|jam|cream|yoghurt|yogurt|oats|rice|cheese|chocolate)"
    r"(?:\s+(?:is|are)(?:\s+there)?)?\s+(?:in|per)\s+(?:a|one|1|an)\s+"
    r"(?:level\s+|heaped\s+)?(?P<measure>teaspoons?|tablespoons?|tbsp|tsp|dessertspoons?|"
    r"spoons?|spoonfuls?|cups?)(?:\s+of\s+(?P<again>[a-z]+))?\s*[?.!]*$")


def _the_thing_measured_by_itself(clean):
    """The same question written the way the weight tables read it, or None.

    "how much flour in a cup" names no weight, so the tables had no line to read and the answer
    was a shrug while "how many grams in a cup of flour" was 120 g. The food is the whole of what
    the measure holds, so the line is rewritten as a weight question and answered there.
    """
    found = _DRY_IN_A_MEASURE.search(clean)
    if not found:
        # a cup of sugar or a cup of salt is the same question; a spoon of them is not, because
        # the spoon branch above answers it in the words a cook uses ("A teaspoon of sugar is
        # about 4.2 g")
        held = _COMPONENT_MEASURED.search(clean)
        if not held or not held.group("measure").startswith("cup"):
            return None
        if not _the_component_is_the_whole_measure(clean):
            return None
        found = held
    food = found.groupdict().get("food") or found.group("component")
    again = found.group("again")
    # "a spoon of sugar" is that food and no other; "a cup of tea" is a drink, not flour
    if again and again not in (food, food + "s", food.split()[-1]):
        return None
    return f"how many grams in a {found.group('measure')} of {food}"

# What a thing itself weighs, for the questions people ask before a move, a flight or a
# repair: "how much does a suitcase weigh", "how heavy is a washing machine". A shop price
# is no answer to those, which is what the bot used to give. Grams, as the piece table is,
# and the reply turns to kg once a thing is a kilo or more.
OBJECT_GRAMS = (
    ("suitcase", 4000), ("cabin bag", 2500), ("holdall", 1500), ("backpack", 1200),
    ("rucksack", 1200), ("handbag", 800), ("briefcase", 1500),
    ("microwave", 12000), ("kettle", 1000), ("toaster", 1500), ("air fryer", 5000),
    ("slow cooker", 4000), ("washing machine", 70000), ("tumble dryer", 40000),
    ("dishwasher", 45000), ("fridge freezer", 80000), ("fridge", 70000), ("freezer", 40000),
    ("oven", 50000), ("hob", 10000), ("vacuum cleaner", 6000), ("hoover", 6000),
    ("iron", 1200), ("sewing machine", 8000),
    ("laptop", 1500), ("chromebook", 1300), ("tablet", 500), ("ipad", 500), ("phone", 200),
    ("iphone", 200), ("desktop", 8000), ("printer", 8000), ("monitor", 5000),
    ("television", 15000), ("games console", 4000), ("playstation", 4500), ("xbox", 4500),
    ("smart speaker", 700), ("router", 500), ("camera", 600),
    ("bicycle", 12000), ("bike", 12000), ("e-bike", 22000), ("scooter", 12000),
    ("mobility scooter", 40000),
    ("pram", 10000), ("pushchair", 8000), ("wheelchair", 15000), ("car seat", 7000),
    ("car battery", 18000), ("tyre", 8000), ("roof box", 15000), ("caravan", 1200000),
    ("motorhome", 2800000), ("trailer", 300000),
    ("piano", 200000), ("sofa", 50000), ("armchair", 25000), ("mattress", 25000),
    ("wardrobe", 80000), ("desk", 30000), ("dining table", 40000), ("bookshelf", 25000),
    ("chest of drawers", 30000), ("bed", 40000), ("cot", 20000), ("bunk bed", 50000),
    ("coffee table", 20000), ("laundry basket", 3000), ("trampoline", 40000),
    ("greenhouse", 50000),
    ("boiler", 30000), ("radiator", 10000), ("water butt", 20000), ("wheelie bin", 15000),
)

# A thing is only that thing when the line counts it: "a suitcase", "my laptop", "2 bikes".
_COUNTED_THING = re.compile(
    r"(?<![\w.])(?:\d+|a|an|one|two|three|four|five|six|my|your|our|his|her|their|the)\s+$")


def _object_weight(clean):
    """What a whole thing weighs: "how much does a suitcase weigh", "how heavy is a laptop"."""
    if not _WEIGH.search(clean) or re.search(r"\btoo\s+(?:heavy|much)\b", clean):
        return None
    if not re.search(r"\bhow\s+(?:much|heavy|many|big)\b|\bwhat(?:'s| is)?\s+(?:the\s+)?weight\b",
                     clean):
        return None  # "my suitcase is too heavy" is a complaint, not a question about one
    if re.search(r"\b(?:cost|costs|price|prices|worth|sell|selling|buy|buying|allowance|"
                 r"allowed|limit|limits|maximum|max|can)\b", clean):
        return None
    best = None
    for name, grams in OBJECT_GRAMS:
        for words in (name, _many(name)):
            match = re.search(rf"(?<![\w.]){re.escape(words)}(?![\w])"
                              r"(?=\s*(?:$|[,?]|weigh|weighs|heavy|about|is\b))", clean)
            if not match:
                continue
            if not _COUNTED_THING.search(clean[:match.start()]):
                continue
            if best is None or len(name) > len(best[0]):
                best = (name, grams)
    if not best:
        return None
    name, grams = best
    article = "an" if name[0] in "aeiou" else "a"
    return f"{article.capitalize()} {name} is about {_kilos(grams)}."


def _many(name):
    """The words for more than one: "bikes", "washing machines"."""
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("o", "ch", "sh", "s", "x")):
        return name + "es"
    return name + "s"


def _kilos(grams):
    """A weight the way someone says a big thing: 12 kg, 1.5 kg, 200 g."""
    if grams >= 1000:
        return f"{_fmt(grams / 1000)} kg"
    return f"{_fmt(grams)} g"


# How much of a cup a spoon holds, for the same weights at a smaller size.
_SHARE_OF_CUP = {"cup": 1.0, "tbsp": 1 / 16, "tsp": 1 / 48}

# Gas marks and fan ovens, the other two ways British recipes give an oven heat:
# (gas mark, the °C and °F a recipe prints for it). A fan oven runs about 20°C cooler
# than the same setting on a plain one.
GAS_OVEN = ((1, 140, 275), (2, 150, 300), (3, 170, 325), (4, 180, 350), (5, 190, 375),
            (6, 200, 400), (7, 220, 425), (8, 230, 450), (9, 240, 475))
FAN_COOLER = 20


# People pluralise the short form of a unit with an "s": "how many mls in a pint", "how many
# kgs in a stone", "how many ozs in a pound". The spelled-out forms carry their own plural
# ("millilitres"), so only the short ones need it, and a rule is better than seven words added
# to seven lists. Two are left out because the plural is a word of its own: "ins" (innings) and
# "pts" (points, as in a league table), and "mi" never takes one.
_NO_PLURAL = ("in", "pt", "mi")


def _build():
    """{word people type: (family, unit)}, and one regex of every word, longest first."""
    names = {}
    for family, items in UNITS.items():
        for unit, words, _ in items:
            for word in words:
                names[word] = (family, unit)
                if len(word) <= 4 and word.isalpha() and not word.endswith("s") \
                            and word not in _NO_PLURAL:
                    names.setdefault(word + "s", (family, unit))
    pattern = "|".join(re.escape(word) for word in sorted(names, key=len, reverse=True))
    return names, re.compile(r"(?<![\w.])(?:" + pattern + r")(?![\w])")


_NAMES, _UNIT_WORD = _build()
_NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?|a|an|one)(?![\w])")
_TARGET = re.compile(r"(?:to|in|into|as|->|=)\s*$")
_SAY_K = re.compile(r"(\d)\s*k\b")

# People write a measure joined up as often as apart: "200g of flour", "500ml", "1.5kg".
# A unit word never starts a longer word here ("2g" yes, "2gb" no), so a space is put in
# where one was left out and every reading below works on the spaced line.
_JOINED = re.compile(r"(?<=\d)(?=\s*(?:kg|mg|ml|cm|mm|km|oz|lbs|lb|ft|in|st|pt|g|l|"
                     r"m|metres?|meters?)\b)")

# A recipe writes a half as a fraction, and "3/4 cup" is not the number 4.
_FRACTION = {("1", "4"): 0.25, ("1", "2"): 0.5, ("3", "4"): 0.75, ("1", "3"): 1 / 3,
             ("2", "3"): 2 / 3}
_SLASH = re.compile(r"(?<![\w.])(\d)\s*/\s*(\d)(?![\d/])")
_AND_A_HALF = re.compile(r"(?<![\w.])(\d|one|two|three|four|five)\s+and\s+a\s+half\b")
_SAID_WHOLE = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
# "a cup and a half", "two cups and a half": the whole number is in front of the unit.
_UNIT_AND_A_HALF = re.compile(r"(?<![\w.])(?:(?P<count>\d+|an?|one|two|three|four)\s+)?"
                              r"(?P<unit>cups?|tablespoons?|tbsp|teaspoons?|tsp|ounces?|oz|"
                              r"pints?|quarts?|litres?|liters?|sticks?)\s+and\s+a\s+half\b")
# "1 1/2 cups": a whole number and a fraction written together.
_MIXED = re.compile(r"(?<![\w.])(\d+)\s+(\d)\s*/\s*(\d)(?![\d/])")

# Word fractions, which recipes use more often than digits: "half a cup", "a quarter of a".
# A recipe writes the fraction with or without "of a": "three quarters of a cup" and
# "a quarter cup" are the same amount, so the "of a" part is optional throughout.
_WORD_FRACTION = ((re.compile(r"\bthree[\s-]quarters?(?:\s+of)?(?:\s+an?)?\b"), "0.75"),
                  (re.compile(r"\btwo[\s-]thirds?(?:\s+of)?(?:\s+an?)?\b"), "0.67"),
                  (re.compile(r"\b(?:one|an?)[\s-]third(?:\s+of)?(?:\s+an?)?\b"), "0.33"),
                  (re.compile(r"\bhalf(?:\s+of)?(?:\s+an?)?\b"), "0.5"),
                  (re.compile(r"\ban?\s+quarter(?:\s+of)?(?:\s+an?)?\b"), "0.25"))


def _factor(family, unit):
    for name, _, factor in UNITS[family]:
        if name == unit:
            return factor
    return None


def _words(unit):
    for family, items in UNITS.items():
        for name, words, _ in items:
            if name == unit:
                return words
    return ()


def _grams(value):
    """A weight the way a cook says it: whole grams once there are ten or more."""
    rounded = value + 1e-9  # 312.5 g rounds up to 313, the way a cook would write it
    return f"{rounded:,.0f}" if abs(value) >= 10 else f"{value:.1f}".rstrip("0").rstrip(".")


def _fmt(value):
    """A number the way someone would say it: no long tails of decimals."""
    size = abs(value)
    if size >= 1000:
        text = f"{value:,.0f}"
    elif size >= 100:
        text = f"{value:.0f}"
    elif size >= 1:
        text = f"{value:.1f}"
    else:
        text = f"{value:.2f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _value(raw):
    if raw in ("a", "an", "one"):
        return 1.0
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _mentions(clean):
    """Every unit the line names: [(start, end, family, unit)], in the order typed."""
    found = []
    for match in _UNIT_WORD.finditer(clean):
        family, unit = _NAMES[match.group(0)]
        # "in" is the preposition far more often than it is inches, so a bare one only counts
        # as a unit when it follows a number: "20 in to cm" is inches, "my oil in miles" is not.
        if match.group(0) == "in" and _number_before(clean, match.start()) is None:
            continue
        found.append((match.start(), match.end(), family, unit))
    return found


def _number_before(clean, start):
    """The number just before a unit ("20 miles", "a pound"), or None."""
    window = clean[max(0, start - 24):start]
    found = None
    for match in _NUMBER.finditer(window):
        if not window[match.end():].strip():
            found = _value(match.group(1))
    return found


def _say(value, unit, one=None):
    """The unit as it is said: singular only for one."""
    if one if one is not None else value == 1:
        return SAID_ONE.get(unit, SAID.get(unit, unit))
    return SAID.get(unit, unit)


# A count of weeks or days is said the way a diary says it, not as a decimal: a person
# asking "how many weeks in 90 days" wants "12 weeks and 6 days", not "12.9 weeks". Hours,
# minutes and seconds keep their decimals, because half an hour and 1.5 hours are how people
# say those already.
_SPLIT = {"week": ("day", 7.0), "day": ("hour", 24.0)}


def _split_time(result, to_unit):
    """A decimal count of weeks or days as whole units and the rest ("12 weeks and 6 days")."""
    smaller = _SPLIT.get(to_unit)
    if not smaller or abs(result - round(result)) < 1e-9:
        return None
    small_unit, per = smaller
    whole = int(result)
    rest = round((result - whole) * per)
    if rest == 0 or rest >= per:  # rounding can push the rest up to the next whole unit
        return None
    return (f"{whole} {_say(whole, to_unit)} and {rest} "
            f"{_say(rest, small_unit)}")


def _sentence(value, family, from_unit, to_unit, in_phrase=False):
    factor, other = _factor(family, from_unit), _factor(family, to_unit)
    if not factor or not other:
        return None
    result = value * factor / other
    about = "" if SYSTEM.get(from_unit) == SYSTEM.get(to_unit) else "about "
    left = ("one " + _say(1, from_unit)) if value == 1 else _amount_phrase(value, from_unit)
    split = _split_time(result, to_unit) if family == "time" else None
    if split:
        return f"{left[0].upper()}{left[1:]} is {about}{split}."
    said = _cups_phrase(result, to_unit, spoons=family == "mass" and to_unit == "cup")
    amount = f"{about}{said}" if said != f"{_fmt(result)} {_say(result, to_unit, one=False)}" \
        else f"{about}{_fmt(result)} {_say(result, to_unit, one=_fmt(result) == '1')}"
    if in_phrase and value == 1:
        # "There is about 1 cup in one mug", not "There are".
        verb = "is" if abs(result - 1) < 0.06 else "are"
        return f"There {verb} {amount} in {left}."
    return f"{left[0].upper()}{left[1:]} is {amount}."


def _temperature(clean):
    for pattern, wanted, convert in (
        (r"(-?\d+(?:\.\d+)?)\s*(?:degrees?\s*|°\s*)?(?:c|celsius|centigrade)\b"
         r".*?\b(?:in|to|into|as)\s*(?:degrees?\s*)?(?:f|fahrenheit)\b",
         "F", lambda c: c * 9 / 5 + 32),
        (r"(-?\d+(?:\.\d+)?)\s*(?:degrees?\s*|°\s*)?(?:f|fahrenheit)\b"
         r".*?\b(?:in|to|into|as)\s*(?:degrees?\s*)?(?:c|celsius|centigrade)\b",
         "C", lambda f: (f - 32) * 5 / 9),
    ):
        match = re.search(pattern, clean)
        if match:
            value = float(match.group(1))
            source = "°C" if wanted == "F" else "°F"
            if wanted == "C":
                # An oven heat is the one Fahrenheit figure people convert: 350°F is 177°C
                # by arithmetic, but every recipe calls it 180°C at gas mark 4.
                mark, celsius, fahrenheit = min(GAS_OVEN, key=lambda row: abs(row[2] - value))
                if abs(fahrenheit - value) <= 12:
                    return (f"{_fmt(value)}{source} is about {_fmt(convert(value))}°C - gas mark "
                            f"{mark}, which most recipes call {_fmt(celsius)}°C.")
            return f"{_fmt(value)}{source} is {_fmt(convert(value))}°{wanted}."
    return None


# "how do i convert c to f" is the plainest way anyone asks this, and it was a search hedge
# while every spelled version answered: the pattern required the whole word or "degrees c", so a
# bare letter matched nothing. A single bold letter between spaces is a unit and nothing else in
# a conversion line, so it is allowed here - and only here, where the line has no number and the
# two letters are what the ask is made of.
_C_ASKS = re.compile(r"\bcelsius|\bcentigrade|\bdegrees? c\b|°c\b|\bc\b")
_F_ASKS = re.compile(r"\bfahrenheit|\bdegrees? f\b|°f\b|\bf\b")


_BARE_TEMPERATURE = re.compile(
    r"\s*(?:convert\s+)?(?:degrees?\s+)?(?:c|celsius|centigrade|f|fahrenheit)\s+"
    r"(?:to|in|into)\s*(?:degrees?\s+)?(?:c|celsius|centigrade|f|fahrenheit)\s*")


def _temperature_rule(clean):
    """"how do i convert celsius to fahrenheit": the formula, since no number is given."""
    if _NUMBER.search(clean):
        return None
    if not (_HOW_TO.search(clean) or _BARE_TEMPERATURE.fullmatch(clean)):
        return None
    celsius = _C_ASKS.search(clean)
    fahrenheit = _F_ASKS.search(clean)
    if celsius and fahrenheit:
        if celsius.start() < fahrenheit.start():
            return ("Multiply the Celsius by 9, divide by 5 and add 32: 20°C is 68°F. The quick "
                    "way in your head is to double it and add 30, which is close enough for "
                    "the weather.")
        return ("Take away 32, then multiply by 5 and divide by 9: 68°F is 20°C. The quick way "
                "in your head is to take away 30 and halve it.")
    return None


def _mark_for(celsius):
    """The gas mark nearest a temperature in °C, the way a recipe would round it."""
    return min(GAS_OVEN, key=lambda row: abs(row[1] - celsius))


def _oven(clean):
    """Gas marks and fan ovens, so one table answers every way an oven heat is asked for.

    "what gas mark is 200c", "180c in a fan oven" and "gas mark 6 in celsius" all name the
    same oven; plain °C to °F stays in _temperature.
    """
    mark_said = re.search(r"gas\s*mark\s*(\d)", clean)
    fan_asked = bool(re.search(r"\bfan\b", clean))
    gas_asked = bool(re.search(r"\bgas\b", clean))
    number = re.search(r"(-?\d{2,3})\s*(?:degrees?\s*|°\s*)?(c|celsius|centigrade|fan|f|fahrenheit)\b",
                       clean)
    if mark_said:
        mark = int(mark_said.group(1))
        row = next((row for row in GAS_OVEN if row[0] == mark), None)
        if not row:
            return None
        return (f"Gas mark {mark} is {row[1]}°C ({row[2]}°F), or {row[1] - FAN_COOLER}°C "
                f"in a fan oven.")
    if not number and fan_asked and not re.search(r"\b(how long|minutes?|hours?|mins)\b", clean):
        # "what is 180 in a fan oven" names no unit at all: a bare oven heat with the fan in the
        # line is still the same question, as long as the line is asking to convert one.
        bare = re.search(r"(?<![\d.])(\d{2,3})(?![\d.])", clean)
        asking = re.search(r"\b(what|which|how|convert|equivalent|set|change|turn|use)\b", clean)
        if bare and asking and 90 <= float(bare.group(1)) <= 280:
            celsius = float(bare.group(1))
            return (f"{_fmt(celsius)}°C is {_fmt(celsius - FAN_COOLER)}°C in a fan oven, "
                    f"gas mark {_mark_for(celsius)[0]}.")
    if not number:
        return None
    celsius = float(number.group(1))
    fahrenheit = number.group(2) in ("f", "fahrenheit")
    if fahrenheit and (fan_asked or gas_asked):
        # "350f in a fan oven" said "350°C is 330°C in a fan oven, gas mark 9": the oven
        # arithmetic ran on a Fahrenheit figure. Convert first, then say both settings.
        celsius = (celsius - 32) * 5 / 9
        said = f"{number.group(1)}°F is {_fmt(celsius)}°C"
        if fan_asked:
            said += f", or {_fmt(celsius - FAN_COOLER)}°C in a fan oven"
        said += f", gas mark {_mark_for(celsius)[0]}"
        return said + "."
    if number.group(2) == "fan" and gas_asked:
        # "what gas mark is 160 fan": the figure is the fan dial, so the plain oven is hotter,
        # and gas mark 4 is the mark for that. Read as a plain-oven figure it is gas mark 2.
        plain = celsius + FAN_COOLER
        return (f"{_fmt(celsius)}°C on a fan setting is {_fmt(plain)}°C in a plain oven, "
                f"gas mark {_mark_for(plain)[0]}.")
    if gas_asked:
        if re.search(r"\d\s*(?:degrees?\s*|°\s*)?(f|fahrenheit)\b", clean):
            celsius = (celsius - 32) * 5 / 9
            return (f"{number.group(1)}°F is gas mark {_mark_for(celsius)[0]}, and "
                    f"{_fmt(celsius)}°C in a plain oven.")
        return (f"{_fmt(celsius)}°C is gas mark {_mark_for(celsius)[0]}, and "
                f"{_fmt(celsius - FAN_COOLER)}°C in a fan oven.")
    if number.group(2) == "fan":
        plain = celsius + FAN_COOLER
        return (f"{_fmt(celsius)}°C on a fan setting is {_fmt(plain)}°C in a plain oven, "
                f"gas mark {_mark_for(plain)[0]}.")
    if fan_asked:
        return (f"{_fmt(celsius)}°C is {_fmt(celsius - FAN_COOLER)}°C in a fan oven, "
                f"gas mark {_mark_for(celsius)[0]}.")
    return None


def _butter(clean):
    """A stick of butter: a weight cooks name instead of giving grams."""
    if "butter" not in clean or not re.search(r"\bsticks?\b", clean):
        return None
    # "how much is a stick of butter" names no unit and is exactly the question this row is for:
    # with the unit alone as the key it reached the study entries and was told to read a section
    # and say its three points out loud, and "how many sticks of butter in a pound" became diet
    # advice. The ask is a key as much as the unit word is, so a "how much" or "how many" about a
    # stick of butter is this row however the person words the rest of it.
    if not re.search(r"\b(grams?|g|oz|ounces?|cups?|tablespoons?|tbsp|teaspoons?)\b", clean) and not \
            re.search(r"\b(?:how (?:much|many)|what is|whats|what's|weigh\w*)\b", clean):
        return None
    count = re.search(r"(half an?|a|an|one|\d+(?:\.\d+)?)\s+sticks?\b", clean)
    if re.search(r"\bpounds?\b", clean) and not re.search(r"\bcups?\b", clean):
        # Four sticks to the pound is the fact behind "how many sticks of butter in a pound".
        return "There are four sticks of butter in a pound, 450 g, so a stick is a quarter of one."
    if "block" in clean:
        # A block is not a stick and does not hold a whole number of them, so the stick's own
        # weight is not the answer to "how many sticks in a block of butter".
        return ("A stick is 113 g, so a 250 g block is about two and a quarter sticks; butter "
                "sold in sticks is usually four to a 450 g block.")
    said = count.group(1) if count else "a"
    amount = 0.5 if said.startswith("half") else _value(said)
    if amount is None:
        return None
    if re.search(r"\bcups?\b", clean) and not re.search(r"\bgrams?\b|\bg\b", clean):
        return "One stick of butter is half a cup, which is 8 tablespoons or about 113 g."
    if amount == 1:
        return "A stick of butter is about 113 g, which is half a cup or 8 tablespoons."
    if amount == 0.5:
        return "Half a stick of butter is about 57 g, which is 4 tablespoons."
    return f"{_fmt(amount)} sticks of butter is about {_fmt(amount * 113.4)} g."


# The pack people actually buy is the amount they mean: nobody weighs out a tin of tomatoes, so
# the table holds the standard pack size and the container word is what makes it a measure. A
# block or a packet of butter is a block or a packet wherever it is bought, but a tin is a tin
# only for the things that come in one, so the contents have to be named.
PACK_GRAMS = (
    ("chopped tomatoes", 400), ("plum tomatoes", 400), ("tomatoes", 400),
    ("baked beans", 415), ("kidney beans", 400), ("black beans", 400), ("cannellini beans", 400),
    ("beans", 400), ("chickpeas", 400), ("chick peas", 400), ("lentils", 400),
    ("sweetcorn", 340), ("tuna", 145), ("sardines", 120), ("coconut milk", 400),
    ("passata", 680), ("condensed milk", 397), ("butter", 250), ("cream", 300),
    ("honey", 340), ("jam", 340), ("marmalade", 340), ("peanut butter", 340),
    # the rest of the cupboard, because the same question is asked about what fills it: a
    # block of cheese, a tub of ice cream, a bag of flour, a pack of mince.
    ("ice cream", 500), ("cheese", 400), ("cheddar", 400), ("feta", 200),
    ("soup", 400), ("tomato soup", 400), ("peaches", 410), ("pears", 410), ("pineapple", 435),
    ("peas", 400), ("corned beef", 340), ("yogurt", 500), ("yoghurt", 500),
    ("chicken breasts", 500), ("chicken breast", 500), ("mince", 500), ("bacon", 250),
    ("pasta", 500), ("spaghetti", 500), ("penne", 500), ("fusilli", 500), ("macaroni", 500),
    ("sausages", 400),
    ("flour", 1500), ("sugar", 1000), ("rice", 1000),
    ("crisps", 25), ("popcorn", 70), ("biscuits", 200), ("cereal", 375),
    # the bag of greens, which is bought by size and not by the leaf
    ("salad leaves", 200), ("spinach", 200), ("salad", 200), ("carrots", 1000),
    ("chocolate", 100), ("bread", 800), ("potatoes", 2000), ("carrots", 1000),
    ("onions", 1000),
    ("cola", 330), ("coke", 330), ("lemonade", 330),
    # the bathroom and the cupboard, asked as "how many grams in a tube of toothpaste"
    ("toothpaste", 100), ("shampoo", 300), ("conditioner", 250), ("coffee", 200),
    ("grapes", 400), ("olive oil", 500), ("washing up liquid", 500),
    ("ketchup", 460), ("wine", 750), ("beer", 330), ("vinegar", 500),
)
# A tin of tuna or sweetcorn is bought by its gross weight and used after draining, and the
# difference is the bit people are caught out by.
PACK_DRAINED = {"tuna": 112, "sweetcorn": 285, "sardines": 90, "peas": 285,
                "peaches": 220, "pears": 220, "pineapple": 250}
# The things sold by the millilitre in the same pack, so the reply says ml and not g.
PACK_IN_ML = ("coconut milk", "cream", "ice cream", "cola", "coke", "lemonade",
              "shampoo", "conditioner", "olive oil", "washing up liquid", "wine", "beer",
              "vinegar")
_PACK_WORD = re.compile(r"\b(?:tin|tins|can|cans|jar|jars|packet|packets|pack|packs|bag|bags|"
                        r"block|blocks|carton|cartons|tub|tubs|box|boxes|bar|bars|sleeve|sleeves|"
                        r"tube|tubes|loaf|loaves|punnet|punnets|bottle|bottles)\b")
# "How much is a tin of tomatoes" is a price question, so only a size ask makes it a measure.
_PACK_ASK = re.compile(r"\bgrams?\b|\bg\b|\bml\b|\bmls\b|weigh|weighs|weight|ounces?|"
                       r"\boz\b|how\s+(?:big|heavy)|what\s+size|how\s+many\s+(?:grams?|ml|"
                       r"ounces?|oz)\b")


def _pack(clean):
    """A tin, block or carton: the amount people buy instead of weighing it out."""
    if not _PACK_WORD.search(clean) or not _PACK_ASK.search(clean):
        return None
    if re.search(r"\b(?:cost|costs|costing|price|prices|cheap|cheaper|expensive)\b", clean):
        return None  # a price question keeps its price
    best = None
    for name, grams in PACK_GRAMS:
        if not re.search(rf"\b{re.escape(name)}\b", clean):
            continue
        if name == "cream" and "ice cream" in clean:
            continue
        if best is None or len(name) > len(best[0]):
            best = (name, grams)
    if not best:
        return None
    name, grams = best
    container = _PACK_WORD.search(clean).group(0)
    if container.endswith("s"):
        container = container[:-1]
    amount = f"{grams} ml" if name in PACK_IN_ML else _kilos(grams)
    reply = f"A standard {container} of {name} is {amount}"
    drained = PACK_DRAINED.get(name)
    if drained:
        reply += f", about {drained} g once drained"
    return reply + "."


# "How many biscuits in a packet" is a measure question with no unit word in it at all, so the
# conversion table never saw it: the sugar advice answered for the biscuits and the boxing answer
# for the eggs. A packet has a weight and one biscuit has a weight, so the count is the two tables
# divided - a new packet or a new piece then answers the count without a third list to keep in
# step. What the shop counts rather than weighs is a fact, so those few have their own line.
_COUNT_ASK = re.compile(
    r"\bhow many\s+(?P<piece>[a-z][a-z' -]{1,28}?)\s+"
    r"(?:are\s+there\s+|are\s+|do\s+you\s+get\s+|can\s+you\s+get\s+|would\s+you\s+get\s+|"
    r"come\s+|come in|go\s+)?(?:in|into|per|to)\s+(?:a|an|one|1)\s+"
    r"(?P<box>packet|pack|bag|box|tin|can|jar|punnet|tub|block|bar|loaf|sleeve|tube|carton)\b"
    r"(?:\s+of\s+(?P<of>[a-z][a-z' ]{1,45}?))?(?=[,.?!]|$)")
# The count of the goods the shop counts, not the sort of thing a packet weight is given for.
COUNTED_PACKS = {
    "egg": "A box is six or twelve - the box says which, and the twelve is a dozen.",
    "teabag": "A box is usually 80 or 160 tea bags, and a small box of 40 is common too.",
    "tea bag": "A box is usually 80 or 160 tea bags, and a small box of 40 is common too.",
    "gelatine": "A packet is usually 12 sheets, and one sheet sets about 100ml of liquid.",
    "stock cube": "A box is usually 10 or 12 cubes, and one cube makes about 450ml of stock.",
}
# A slice is only counted in a loaf, and a square only in a bar: the container says what the
# piece is made of, which is the half of the question people leave out.
_COUNT_CONTENT = {"slice": ("bread", "slice of bread"), "slices": ("bread", "slice of bread"),
                  "squares": ("chocolate", "square of chocolate"),
                  "square": ("chocolate", "square of chocolate")}
# The words that look like a count and are a weight, a cost or a nutrition question instead.
_NOT_A_COUNT = re.compile(r"^(?:grams?|g|mls?|kilos?|kgs?|litres?|liters?|pints?|ounces?|oz|"
                          r"calories?|kcal|carbs?|sugars?|units?|prices?|costs?|servings?|"
                          r"portions?|people|persons?)\b")


def _singular(name):
    """The one of a food the weight tables are keyed by: "potatoes" -> "potato"."""
    for ending, swap in (("ies", "y"), ("oes", "o"), ("ches", "ch"), ("shes", "sh"),
                         ("ses", "s"), ("es", ""), ("s", "")):
        if name.endswith(ending) and len(name) > len(ending):
            gone = name[: -len(ending)] + swap
            if any(gone in (key, _plural_of(key)) for key, _g in PIECE_GRAMS):
                return gone
    return name.rstrip("s") or name


def _table_grams(name, table):
    """The row for this food in a weight table, singular or plural, or None."""
    best = None
    for key, grams in table:
        if name in (key, _plural_of(key)):
            if best is None or len(key) > len(best[0]):
                best = (key, grams)
    return best


def _pack_count(clean):
    """How many pieces the packet holds, from the packet's weight and one piece's weight."""
    found = _COUNT_ASK.search(clean)
    if not found:
        return None
    piece = " ".join(found.group("piece").split())
    box = found.group("box")
    if _NOT_A_COUNT.match(piece):
        return None
    counted = COUNTED_PACKS.get(piece) or COUNTED_PACKS.get(piece.rstrip("s"))
    if counted:
        return counted
    # "in a bar of chocolate" names the content after the container, and the piece before it is
    # the count: the content is what the packet weights are keyed by.
    words = (found.group("of") or "").split()
    # "in a tin of chopped tomatoes" names the content in more words than the table holds, so the
    # longest run of them that a table knows is the content, and the rest is thrown away.
    for size in range(len(words), 0, -1):
        said = " ".join(words[:size])
        counted = COUNTED_PACKS.get(said) or COUNTED_PACKS.get(_singular(said))
        if counted:
            return counted
    content, name = _COUNT_CONTENT.get(piece, (piece, piece))
    if _COUNT_CONTENT.get(piece):
        singular = name
    else:
        singular = _singular(name)
    packed = _table_grams(content, PACK_GRAMS)
    one = _table_grams(singular, PIECE_GRAMS) or _table_grams(name, PIECE_GRAMS)
    if (not packed or not one) and words:
        # "a packet of digestives" is still a packet of biscuits: the count noun decides what is
        # in the packet whenever the words after "of" name a kind and not a food.
        for size in range(len(words), 0, -1):
            other = " ".join(words[:size])
            if _table_grams(_singular(other), PIECE_GRAMS):
                packed = _table_grams(_singular(other), PACK_GRAMS) or packed
                one = _table_grams(_singular(other), PIECE_GRAMS)
                break
    if not packed or not one or not one[1]:
        return None
    count = int(round(packed[1] / one[1]))
    if count < 2:
        return None
    said = _plural_of(one[0])
    return (f"About {count} {said} in a {box}: a {box} is about {_kilos(packed[1])} and one "
            f"{one[0]} about {_fmt(one[1])}g, so the count moves with the size of both.")


# The loose measures of a kitchen and a bar, none of them a unit: people ask what a knob of
# butter or a glass of wine comes to, and the honest answer is the range the words stand for.
LOOSE = (
    ("knob of butter", "A knob of butter is about 10 g, a scant tablespoon."),
    ("squeeze of lemon", "A squeeze of lemon is about a teaspoon, 5 ml."),
    ("squeeze of lime", "A squeeze of lime is about a teaspoon, 5 ml."),
    ("squeeze of honey", "A squeeze of honey is about a teaspoon, 7 g."),
    ("shot of espresso", "A single shot of espresso is about 25 ml, a double 50 ml."),
    ("shot", "A single shot is 25 ml and a double 50 ml, 25 g and 50 g of a thin liquid."),
    ("glass of wine", "A small glass of wine is 125 ml, a medium 175 ml and a large 250 ml."),
    ("glass of milk", "A glass of milk is about 200 ml, which is roughly 205 g."),
    ("glass of water", "A glass of water is about 200 ml, which is 200 g, and a big one 250 ml."),
    ("mug of tea", "A mug of tea is about 250 ml."),
    ("wedge of lemon", "A wedge of lemon is about 15 g, and gives a teaspoon or two of juice."),
    ("wedge of lime", "A wedge of lime is about 15 g, and gives a teaspoon or two of juice."),
    # A pot is two sizes, so the answer names both rather than guessing which one was meant.
    ("pot of yogurt", "A small pot of yogurt is 150 g and a big one 500 g."),
    ("pot of cream", "A pot of cream is 300 ml, and a small one 150 ml."),
    ("glass of orange juice", "A glass of orange juice is about 200 ml, which takes two or three oranges."),
    ("glass of apple juice", "A glass of apple juice is about 200 ml."),
    ("glass of juice", "A glass of juice is about 200 ml."),
    ("glass of squash", "A glass of squash is about 200 ml, made up with water."),
    ("glass of cola", "A glass of cola is about 200 ml, which is most of a 330 ml can."),
)
_LOOSE_ASK = re.compile(r"\bhow\s+(?:much|many|big)\b|\bgrams?\b|\bg\b|\bml\b|\bmls\b|"
                        r"weigh|weighs|weight|ounces?\b|\boz\b|what\s+size")
# A "glass of wine" is also a units-of-alcohol question and a pregnancy question, and neither
# is asking what it weighs.
_LOOSE_NOT = re.compile(r"\b(?:unit|units|alcohol|drink|drinking|pregnan\w*|calorie\w*|"
                        r"cost|costs|price|prices|cheap|expensive|drunk|drive|driving)\b")
# The same measure said the other way round: "how much water in a glass" is a glass of water.
# The liquid is what the answer depends on, so the vessel only sets the size and the table above
# gives the reply whenever it already knows the drink.
_IN_A_VESSEL = re.compile(
    r"\b(?P<liquid>water|milk|juice|squash|cola|wine)\s+in\s+(?:a|one)\s+"
    # the vessel has to be the end of the name of the thing: "how much water in a glass of
    # squash" is a glass of squash, and "how much milk in a cup of tea" is not 250 ml of milk
    r"(?:(?P<size>small|medium|big|large|tall)\s+)?(?P<vessel>glass|cup|mug|pint)"
    r"(?!\s+of\b)")
_VESSEL_ML = {"glass": 200, "cup": 250, "mug": 250, "pint": 568}


def _in_a_vessel(clean):
    found = _IN_A_VESSEL.search(clean)
    if not found:
        return None
    liquid, vessel = found.group("liquid"), found.group("vessel")
    size = found.group("size")
    if vessel == "glass":
        for phrase, reply in LOOSE:
            if phrase == f"glass of {liquid}":
                return reply
    amount = _VESSEL_ML[vessel]
    if size in ("big", "large", "tall"):
        amount = 250
    return (f"A {vessel} of {liquid} is about {amount} ml"
            + (", which is 200 g" if liquid == "water" and vessel == "glass" else "")
            + ".")


def _loose(clean):
    """A knob, a squeeze, a shot or a glass: the amount the word stands for."""
    if not _LOOSE_ASK.search(clean) or _LOOSE_NOT.search(clean):
        return None
    in_vessel = _in_a_vessel(clean)
    if in_vessel:
        return in_vessel
    best = None
    for phrase, reply in LOOSE:
        if re.search(rf"\b{re.escape(phrase)}\b", clean):
            if best is None or len(phrase) > len(best[0]):
                best = (phrase, reply)
    return best[1] if best else None


# What a liquid weighs for the volume it comes in, the question at the sink and at the till:
# "how much does a litre of water weigh", "a pint of milk in grams". A litre of water is a
# kilogram and a pint of it a pound and a quarter; every other liquid is the same sum with
# its own density, so one table answers all of them.
LIQUID_GRAMS_LITRE = (("milk", 1030), ("cream", 1010), ("honey", 1420), ("oil", 920),
                      ("water", 1000))

# "How many grams of coffee per cup" is a dose, not a question about what fills a cup, and the
# coffee entry knows the spoonful; the cup table must not take it with "it depends what is in a
# cup". A mug is a cup of 250 ml, which is what people mean when they scoop with one.
_PER_CUP = re.compile(r"\bper\s+(?:a\s+|one\s+|each\s+)?(?:cups?|mugs?)\b"
                      r"|\bfor\s+(?:a|one|each|every)\s+(?:cups?|mugs?)\b")


def _liquid_weight(clean):
    """What a volume of a named liquid weighs: "a pint of milk", "a litre of water"."""
    if _PER_CUP.search(clean):
        return None
    if not _asks_for_weight(clean):
        return None
    if re.search(r"\b(?:cost|costs|price|prices|worth|sell|buy|buying|calories|protein)\b", clean):
        return None
    liquid = None
    for name, grams in LIQUID_GRAMS_LITRE:
        if re.search(rf"\b{name}\b", clean):
            liquid = (name, grams)
            break
    if not liquid:
        return None
    millilitres, said = None, ""
    for start, end, family, unit in _mentions(clean):
        if family != "volume" or unit in ("cup", "tbsp", "tsp"):
            continue  # a cup of a thing is the cup table's question, and it knows the food
        value = _number_before(clean, start)
        if value is None:
            continue
        millilitres = value * _factor("volume", unit)
        said = (f"a {SAID_ONE.get(unit, unit)}" if value == 1
                else _amount_phrase(value, unit))
        break
    if millilitres is None:
        if not re.search(r"\bmugs?\b", clean):
            return None
        millilitres, said = 250.0, "a mug"  # a mug is 250 ml, and people do ask this
    grams = millilitres * liquid[1] / 1000.0
    return f"{said[0].upper() + said[1:]} of {liquid[0]} weighs {_mass_said(grams)}."


def _mass_said(grams):
    """A weight said the way someone would: 1 kg, 1.03 kg, 585 g."""
    if grams < 1000:
        return f"{_grams(grams)} g"
    kilos = grams / 1000.0
    text = f"{kilos:.2f}" if kilos < 2 else f"{kilos:,.1f}"
    return f"{text.rstrip('0').rstrip('.')} kg"
# How much of a food to cook for one person. A recipe is written for a number nobody has in
# their kitchen, so the everyday question is "how many potatoes per person", and the useful half
# is a portion, not a conversion. One row per food, in grams or as a count.
# Half a kilo a person is the shop's figure for a bird on the bone: it leaves enough for the
# second helping and the sandwiches after.
BIRD_GRAMS = 500
_BIRDS = ("turkey", "turkeys", "chicken", "chickens", "duck", "ducks", "goose", "geese")

# The portions whose noun is a dish rather than an ingredient: a figure for these is a slice
# somebody already weighed, and a line that says it is making one is asking for the method.
MADE_NOT_MEASURED = frozenset(("the dish", "cake"))

PER_PERSON = (
    (("potato", "potatoes", "new potatoes", "mash"), 250, "g", "potatoes"),
    # A breast or a thigh is meat off the bone; a chicken is a bird, and a bird feeds people on
    # the bone, so the two are separate rows. "How big a chicken for six" answered from the 200 g
    # meat line would say 1.2 kg, which is one small bird for a crowd.
    (("chicken breast", "chicken breasts", "chicken thigh", "chicken thighs", "chicken"),
     200, "g", "chicken"),
    (("mince", "beef mince", "lamb mince"), 150, "g", "mince"),
    (("steak", "steaks"), 200, "g", "steak"),
    (("salmon", "salmon fillet", "salmon fillets"), 150, "g", "salmon"),
    (("fish", "white fish", "cod", "haddock"), 150, "g", "fish"),
    (("meat", "joint", "roast beef", "beef", "lamb", "pork"), 250, "g", "raw meat"),
    # A bird is bought on the bone, so half a kilo a person is the shop's figure: it leaves
    # enough for the second helping and the sandwiches after.
    (("turkey", "turkeys"), BIRD_GRAMS, "g", "turkey"),
    (("duck", "ducks"), BIRD_GRAMS, "g", "duck"),
    (("goose", "geese"), BIRD_GRAMS, "g", "goose"),
    (("ham", "gammon", "gammon joint"), 250, "g", "ham"),
    (("prawns", "prawn", "king prawns"), 150, "g", "prawns"),
    (("cheese", "cheddar"), 50, "g", "cheese"),
    (("sausage", "sausages"), 2, "each", "sausages"),
    (("egg", "eggs"), 2, "each", "eggs"),
    (("salad", "salad leaves", "lettuce", "rocket", "spinach"), 50, "g", "salad leaves"),
    (("couscous", "bulgur", "bulghur"), 60, "g", "couscous"),
    # A grain cooked by guess: it swells to three times its size, so the dry weight looks small
    # next to the plate it fills.
    (("quinoa",), 60, "g", "quinoa"),
    (("lentils", "red lentils", "green lentils", "dal", "dhal"), 75, "g", "dried lentils"),
    (("prawns", "shrimp"), 150, "g", "prawns"),
    # A drink is counted in bottles, not grams: "how many bottles for 60 guests" is the same
    # question about a table for sixty, and half a bottle a head is the usual rule.
    (("wine", "red wine", "white wine", "rose", "prosecco", "fizz", "champagne"), 0.5,
     "bottle", "wine"),
    # Oven chips are sold by the bag and eaten by the plateful: a portion is a plate, not a
    # weight anyone looks up.
    (("chips", "oven chips", "fries", "french fries"), 150, "g", "chips"),
    (("carrot", "carrots"), 1, "each", "carrot"),
    # A buffet is counted in pieces, not weighed: "how many sandwiches for 20 people" is the
    # question before a party, and three each is the figure caterers use for finger food.
    (("sandwich", "sandwiches", "finger sandwiches", "rounds of sandwiches"), 3, "each",
     "sandwiches"),
    (("sausage roll", "sausage rolls"), 3, "each", "sausage rolls"),
    # A quiche is weighed, not sliced: the "each" lines are written for a plural piece ("3
    # sandwiches each"), and a singular one made the total read "twelve slice of quiche".
    (("quiche", "quiches"), 150, "g", "quiche"),
    # Nothing named but "food" and a headcount: "how much food do i need for 30 people" was the
    # weekly-shop answer, which is a plan, not a number. 300 g a head is the same figure the
    # slow-cooker dish uses for one, so the two answers agree.
    (("food", "dish", "casserole", "pasta bake", "curry"), 300, "g", "the dish"),
    # A cake is cut into portions, so the slice the cooks here already weigh is the portion.
    (("cake",), 60, "g", "cake"),
    (("stuffing",), 50, "g", "stuffing"),
    # A gravy jug goes round the table and comes back for more, so this is a ladle each.
    (("gravy",), 150, "ml", "gravy"),
    # Christmas dinner and a cream tea are counted, not weighed.
    (("pigs in blankets", "pig in blankets"), 3, "each", "pigs in blankets"),
    (("scone", "scones"), 2, "each", "scones"),
    (("hummus", "houmous"), 50, "g", "hummus"),
    (("porridge oats", "porridge", "oats"), 50, "g", "porridge oats"),
    (("soup",), 300, "ml", "soup"),
    (("meatballs", "meatball"), 4, "each", "meatballs"),
    (("slices of bread", "slice of bread", "bread"), 2, "each", "slices of bread"),
    # The rest of a roast or a Sunday tea, counted and weighed the way people ask.
    (("sprouts", "brussels sprouts", "brussel sprouts"), 5, "each", "sprouts"),
    (("yorkshire puddings", "yorkshire pudding", "yorkshires"), 2, "each", "yorkshire puddings"),
    (("broccoli",), 80, "g", "broccoli"),
    (("baked beans", "beans"), 150, "g", "baked beans"),
    (("custard",), 100, "ml", "custard"),
    (("coleslaw",), 75, "g", "coleslaw"),
    # A party is counted in pieces off a tray: "how many pizzas for 8 people" and "how many
    # burgers for 25" were the search hedge, and a pizza is cut into eight so three slices is
    # the plate at a table and two burgers is the barbecue figure with a bun and a side.
    (("pizza", "pizzas"), 3, "each", "slices of pizza"),
    (("burger", "burgers"), 2, "each", "burgers"),
    # A mince pie is the pastry, not the mince in the name, so its row is longer and wins the
    # match: "how many mince pies for 20 people" answered "About 150 g of mince each".
    (("mince pie", "mince pies"), 2, "each", "mince pies"),
)

# Two foods the cooking know-how already explains in a cook's own words ("a mugful for two",
# "a 500g packet feeds four or five"), so a plain "how much rice per person" keeps that answer.
# A headcount is the one thing those words cannot do the sum for, though: "im cooking for 8,
# how much rice" is a total, and 8 x 75 g is the part of the answer the person cannot do in
# their head while holding a pan. So these rows count only when the line says how many people.
PER_PERSON_WHEN_COUNTED = (
    (("rice", "basmati", "long grain rice"), 75, "g", "dry rice"),
    (("pasta", "spaghetti", "penne", "fusilli", "macaroni", "tagliatelle"), 100, "g",
     "dry pasta"),
)

# A dish for a table is the portions question with the dish named instead of the food:
# "chilli for 8 people", "spaghetti bolognese for 10 people", "curry for 12 people" were all
# "Got it", while "how much mince for 8 people" and "how much rice for 4 people" answer from the
# allowances below. The person planning a meal for a household says the dish, not its parts, so
# the two allowances that make the dish are read off the one table and added up here.
# The pair is (the dish as people say it, the part that carries the dish, the part beside it).
DISHES_FOR_A_TABLE = (
    (("chilli con carne", "chili con carne", "chilli", "chili", "chilli beef", "chilli mince"),
     ("mince",), ("rice",), True, True),
    (("spaghetti bolognese", "bolognaise", "bolognese", "spag bol"),
     ("mince",), ("spaghetti", "pasta"), True, False),
    (("lasagne", "lasagna"), ("mince",), None, True, False),
    (("shepherds pie", "shepherd's pie", "cottage pie"), ("mince",), ("potato",), False, False),
    (("tarka dal", "dhal", "dal"), ("lentils",), ("rice",), False, True),
    (("curry", "curries", "tikka masala", "korma", "bhuna", "jalfrezi"), ("chicken",), ("rice",),
     False, True),
    (("casserole", "stew"), ("meat",), ("potato",), False, False),
)
# A tin of tomatoes goes with the mince in a chilli or a bolognese, and the count is the one part
# of those two dishes that does not scale by weight: one 400 g tin does four.
_TIN_FOR = 4

# "how much chilli" with no "con carne" is the number of chillies for the heat, not the size of
# the batch: chilli.py answers that one, and "how much chilli for a chilli for 8 people" was
# turned into a kilo of mince here.
_CHILLI_THE_VEGETABLE = re.compile(r"\bhow (?:much|many) (?:red |green |small |big |hot )?"
                                   r"chilli(?:es)?\b")

# "chilli powder", "curry paste", "chilli sauce" and "curry powder" name a spoonful of an
# ingredient, not the dish: "how much chilli powder for four" was answered with a kilo of mince
# once the dish rows were read. The word after the dish decides which it is.
_A_DISH_PART = re.compile(r"\s+(?:powder|powders|sauce|sauces|paste|pastes|oil|flakes|seeds|"
                          r"seasoning|spice|spices|mix|puree|ketchup|granules|extract|essence|"
                          r"leaf|leaves|plant|pepper|peppers)\b")


# The ask, not the clause in front of it. "im making a lasagne for eight, how long does it take"
# names a dish and a headcount and was answered "1.2 kg of mince in all" - the shopping list to a
# question about the clock. A line that asks how long, how soon, what time, when, or in how many
# minutes or hours is owed a time, and the portion of the dish is a different answer.
_A_TIME_IS_THE_ASK = re.compile(
    r"\bhow long\b|\bhow soon\b|\bwhat time\b|\bwhen\b|"
    r"\bhow many (?:hours?|minutes?|mins?|days?)\b")


def _a_dish_for_a_table(clean):
    """How much of a named dish to cook for the number of people the line names."""
    if not isinstance(clean, str) or not clean:
        return None
    if _A_TIME_IS_THE_ASK.search(clean):
        return None
    people = _people_asked(clean)
    if not people or people < 2 or people > 60:
        return None
    said = " ".join(clean.lower().split())
    named = None
    for names, main, side, tomatoes, spice in DISHES_FOR_A_TABLE:
        for name in names:
            found = re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", said)
            if not found:
                continue
            if _A_DISH_PART.match(said[found.end():]):
                continue  # a spoonful of an ingredient, not the dish
            if named is None or len(name) > len(named[0]):
                named = (name, main, side, tomatoes, spice)
    if named is None:
        return None
    _name, main, side, tomatoes, spice = named
    if _name in ("chilli", "chili") and _CHILLI_THE_VEGETABLE.search(said):
        return None
    found = []
    for part in (main, side):
        if not part:
            continue
        allowance = _an_allowance(part)
        if allowance:
            found.append(allowance)
    if not found:
        return None
    each = [f"{amount:g} g of {noun}" for amount, noun in found]
    total = [f"{_a_weight(amount * people)} of {noun}" for amount, noun in found]
    dish = _name
    if len(each) == 1:
        per_head = each[0]
        all_of_it = total[0]
    else:
        per_head = " and ".join(each)
        all_of_it = " and ".join(total)
    reply = f"For {people}, {dish} is about {per_head} each: {all_of_it} in all."
    if tomatoes:
        tins = max(1, round(people / _TIN_FOR))
        tin = "tin" if tins == 1 else "tins"
        reply += f" One 400 g tin of tomatoes does four, so {tins} {tin}."
    if spice:
        reply += " Use a little more spice than the recipe says - a big batch tastes milder."
    return reply


def _an_allowance(names):
    """The per-person allowance for one part of a dish, from the one table of allowances."""
    for foods, amount, kind, noun in PER_PERSON + PER_PERSON_WHEN_COUNTED:
        if kind != "g" or not amount:
            continue
        if any(name in foods for name in names):
            return amount, noun
    return None


def _a_weight(grams):
    """A weight the way a cook says it: kilos past a thousand, with halves kept."""
    if grams >= 1000:
        kilos = round(grams / 100.0) / 10
        return f"{kilos:g} kg"
    return f"{grams:g} g"


# A bag, a tin or a packet is a size, and "how many grams in a bag of pasta for 4" asks how big
# the bag is before it asks how much to cook.
_CONTAINER = re.compile(r"\b(?:bags?|packs?|packets?|tins?|cans?|jars?|boxes?|cartons?)\b")
# A portion question of its own ("how much mince for 4 people") is not a statement that there
# are four people coming, so a count inside one is not carried to the next food.
_AN_ASK = re.compile(r"\bhow (?:much|many|big|large)\b|\bwhat size\b")
# The words that say the figure is replacing an earlier one ("actually make it for 8", "no, 10
# of us"). A count with nobody named beside it is a table only when it is said this way.
CORRECTING = re.compile(r"\b(?:actually|no|nah|sorry|instead|make\s+it|make\s+that|"
                        r"change\s+it|change\s+that|now)\b", re.I)

# A portion question is about feeding people: "per person", "for 8 people", "each of us".
# Bare "each" on its own is not one: "how much does each potato weigh" asks what one weighs,
# and a shopping number is a worse answer than a shrug.
_PEOPLE_WORD = re.compile(r"\b(?:per\s+(?:person|head)|an?\s+person|an?\s+head(?!\s+of\b)|"
                          r"people|persons?|"
                          r"of\s+us|of\s+you|guests|adults?|between\s+us|party|table\s+for|"
                          r"we(?:'re|\s+are)\s+\d{1,3}\b|there\s+are\s+\d{1,3}\b|"
                          r"expecting\s+\d{1,3}\b|"
                          r"each\s+(?:person|head|guest|adult|of\s+us|one)|family\s+of)"
                          # "how many pigs in blankets each" is "per person" with the
                          # person left out, which is how people ask it in a kitchen.
                          r"\b|\beach\b")
# What the number after "for" usually is instead of a table: a length of time, a weight, a
# distance, a number of steps. "a lasagne for six" is a table of six and "i ran for 5 km
# yesterday" is not a table of five, and read as one it put a per-person portion for five in
# front of somebody asking about rice the next day.
# The word before "for" is the other half of it: a dish before it ("a lasagne for six") is a
# table, a pronoun or an oven before it ("i need it for 8", "in the oven for 8") is not.
_BARE_FOR_COUNT = re.compile(
    r"\bfor\s+(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b")
_NOT_A_TABLE_BEFORE = frozenset(("it", "them", "that", "this", "one", "some", "oven"))
NOT_A_TABLE = (
    r"(?!\s*(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|slices?|meals?|"
    r"dinners?|lunches?|kg|kilos?|g|grams?|litres?|liters?|ml|pints?|cans?|tins?|packs?|"
    r"batches?|portions?|servings?|kms?|kilometres?|kilometers?|k|miles?|metres?|meters?|"
    r"m|ft|feet|foot|yards?|steps?|laps?|lengths?|rounds?|times?|degrees?))")


_PEOPLE_COUNT = re.compile(
    r"\b(?:for|between)\s+(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"\s+(?:people|persons?|guests|adults|of\s+us|of\s+you|heads)\b"
    r"|\b(\d{1,2})\s+(?:people|persons?|guests|adults|heads)\b"
    # "a family of five" is the same count said with a word for the people
    r"|\bfamily\s+of\s+(\d|one|two|three|four|five|six|seven|eight|nine|ten)\b"
    # In a kitchen people say "for two", not "for two people", so a bare count is one too -
    # unless the number is a length of time or a weight ("chicken for 20 minutes").
    r"|\bfor\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"\d{1,2})\b"
    + NOT_A_TABLE +
    # The same headcount said as a sentence about the day: "we are 10 on saturday, how much
    # pasta should i cook" is a table of ten, and the total is what it wants. The lookahead is
    # the same one the bare count gets, or "we are 10 minutes in" would be a table of ten.
    r"|\b(?:we(?:'re|\s+are)|there(?:'s|\s+are))\s+"
    r"(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
    + NOT_A_TABLE +
    # "30 of us", "the four of us" and "a party of 30" are the same headcount said three ways.
    r"|\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+of\s+us\b"
    r"|\b(?:party|table|group|booking|buffet)\s+(?:of|for)\s+"
    r"(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
    # "ive got 20 coming on saturday, how much rice should i cook": the people are coming, and
    # the number is the table. Without this the portion answer was per person and never said the
    # total, which is the whole of what a cook with twenty coming cannot work out mid-pan.
    r"|\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a dozen)\s+"
    r"coming\b"
    r"|\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:of\s+us\s+)?"
    r"(?:for|at)\s+(?:dinner|lunch|supper|christmas|the\s+weekend)\b")
# Nutrition, money and units of alcohol are a different question with the same words in it.
# "Buy" is deliberately not one of them: "how much mince should i buy" is the same question as
# "how much mince do i need", and with the word in this list the table stood down and the line
# got nothing at all - the potatoes after a turkey chat went to the roasting times, and the meat
# to a bird that feeds eight, while the twelve at the table were in the chat all along. A line
# that is really about money still says cost, price, spend, budget or shopping, and those stay.
_PORTION_AVOID = re.compile(
    r"\b(?:calories|kcal|carbs?|protein|sugar|fat|fibre|fiber|cost|costs|price|prices|worth|"
    r"budget|alcohol|units|feed|feeds|plant|planting|grow|growing|seeds?|leftover|"
    r"spend|spending|money|pay|paid|shop|shopping|"
    # "salad dressing" and "cheese sauce" hold a food name and ask how much of the sauce,
    # which is a recipe, not a portion of the food the name belongs to. Gravy, soup,
    # coleslaw and cake are no longer in this list: each has its own portion row now, so
    # "how much gravy for 8 people" is the table's question, not a recipe's.
    r"dressing|sauces?|mayo|mayonnaise|stock|dips?|"
    r"cream\s+sauces?|salad\s+cream|chutney|"
    r"left\s+over|weigh|weighs|weight|heavy|boards?|cheeseboards?|platters?|"
    # A pantry ingredient is a spoonful, not a portion: "how much curry powder for four" was
    # "About 300 g of the dish each", because "curry" is in the dish row and in the question at
    # once, and the spoonful is what was asked for. Stock, dressing, sauce and chutney are fenced
    # above for the same reason: the food name is not the thing being measured.
    r"powders?|spices?|seasoning|ground|flakes|granules|extracts?|essence|herbs?)\b")
# A bake has no eggs each. "how many eggs for a cake for 8" was answered "About 2 eggs each, so
# 16 eggs for eight", which is a plate of eggs and not a cake: the eggs in a bake are weighed
# against the flour, and cakes.py answers that count. The portion table only owns the plate.
_BAKING_PORTION = re.compile(
    r"\b(?:cake|cakes|sponge|cupcakes?|batter|meringues?|pavlova|yorkshire|pancakes?|crepes?|"
    r"pastry|dough|loaf|loaves|bread\s+and\s+butter)\b")
# "How many portions in a cake" is a count of portions, not how big one is.
_PORTION_COUNT = re.compile(r"\bhow many (?:portions|servings|slices|pieces|bits|helpings)\b")
# "How much is a portion of salmon" is the same question as "how much salmon per person"
# with the people left unsaid, and a price answer to it is the wrong question answered.
_PORTION_WORD = re.compile(r"\bportions?\b|\bservings?\b")
_SAID_PEOPLE = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
_PEOPLE_VALUE = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                 "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


# The people at the table counted by the groups a line names. "with 4 adults and 3 kids, how
# much mince do i need" is seven people, and every group is a group of people: the adult count
# alone is the wrong table, and it is one of the two ways a real question was answered 600 g
# for four. The same rule reads the two groups in either order ("3 kids and 2 adults").
_TABLE_GROUPS = re.compile(
    r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a dozen)\s+"
    r"(?:adults?|grown[\s-]?ups?|pensioners?|teenagers?|kids?|children|child|toddlers?|"
    r"babies|baby|guests?|people|persons?|heads|of\s+us)\b", re.I)
_GROUP_VALUE = dict(_PEOPLE_VALUE, **{"a dozen": 12})


def people_in_groups(text):
    """How many people the groups named in the line add up to, or None when it names none.

    Every group counts: "4 adults and 3 kids" is seven, "3 kids and 2 adults" is five, and a
    line with one group ("for 4 people", "6 kids") is that group. A child is a person at the
    table too, so the total is what the shopping and the pan are for - the note that children eat
    a little less belongs in the answer, not in a count that quietly leaves them out.
    """
    total = 0
    for raw in _TABLE_GROUPS.findall(str(text or "").lower()):
        count = int(raw) if raw.isdigit() else _GROUP_VALUE.get(raw)
        if count:
            total += count
    return total or None


def _people_asked(clean):
    """How many people the line cooks for, or None when it only says "a person"."""
    if re.search(r"\bbetween\s+us\b", clean):
        return 2  # "how much chicken between us" is dinner for two
    grouped = people_in_groups(clean)
    found = _PEOPLE_COUNT.search(clean)
    if not found:
        return grouped
    raw = next((part for part in found.groups() if part), "")
    said = int(raw) if raw.isdigit() else _PEOPLE_VALUE.get(raw)
    # A group count is the table, and the plain count is only better when it says more: "6
    # coming, 2 of them kids" is a table of six, and the four adults in it are not the table.
    if grouped and (not said or grouped > said):
        return grouped
    return said


def _people_before(memory, statements_only=False, asked_for_an_amount=False):
    """A headcount from the last turn or two: "we are 6 on saturday", then "how much mince".

    The number came one line earlier and the portion question is the same question with the food
    swapped in, so the count comes with it. Only lines that talk about feeding people count:
    "3 pans on the go" and "a bit for 10 minutes" are not a table.

    `statements_only` leaves out a count that came inside an earlier portion question: the
    answer to "how much mince for 4 people" does not make the next line a table of four, and
    "how much rice per person", asked after it, is still the question about one person.

    A correction of the count is read as the count, even though it has no word for the people in
    it: "i want to cook a curry for 4 people" then "actually make it for 8" left the table at
    four, and the portion answer said "About 75 g of dry rice each, so 300 g for four." to
    somebody who had just said eight. The words that make a line a table can sit on either of
    the two lines - the one that named the people or the one that corrected the figure - so the
    test is made over both, and then the newest figure in them is the count.

    A figure with no people word next to it is only a table when it is said as a correction
    (`CORRECTING`): "put it in the oven for 8" and "i need it for 8" are a time and a date, and
    a table of eight they never gave is the one thing a portion must not do.

    A count said as a statement about the table stands for a few turns, not one: "there will be
    nine of us", "how long should it cook for", "my oven is fan assisted", "so its eleven now",
    "should i change the time", "and how much meat should i buy" - and the meat question got a
    table of two, because eleven was three lines back and the two lines read held no count. So
    when the last two lines say nothing, the turns before them are read for a count that still
    stands, and a line that names people with no number ends the search: the subject has moved
    on, and an older table is the one thing a portion must not do. Only a line that asks how much
    or how many reaches back at all - "what size chicken do i need" is a question about the bird,
    not about how many are eating it.
    """
    if not isinstance(memory, dict):
        return None
    try:
        from .. import memory as mem
        lines = mem.last_user(memory, 2)
        earlier = mem.last_user(memory, 6)
    except Exception:
        return None
    if isinstance(lines, str):
        lines = [lines]
    said = [" ".join(str(line or "").lower().split()) for line in lines or []]
    said = [text for text in said if text
            and not (statements_only and _AN_ASK.search(text))]
    # A plan says its headcount as "a lasagne for six" - no word for people in it, but a count
    # of them - and that is how most people say how many they are cooking for.
    for text in reversed(said):
        if not (_PEOPLE_WORD.search(text) or _PEOPLE_COUNT.search(text)) \
                and not CORRECTING.search(text):
            continue
        if not _a_table_without_people(text):
            continue
        found = _people_asked(text)
        if not found and CORRECTING.search(text):
            # "so its eleven now" says the count without naming the people in it.
            found = _a_corrected_figure(text)
        if found:
            return found
    if statements_only or not asked_for_an_amount:
        return None
    # Nothing in the last two lines, so the count may be one said a few turns earlier and
    # still standing.
    older = [" ".join(str(line or "").lower().split()) for line in (earlier or [])][:-2]
    return _a_count_that_still_stands(older)


def _a_count_that_still_stands(older):
    """The newest headcount in the turns before the last two, while it still holds.

    People state a table once and then ask two or three things about the plan around it - the
    time, the oven, the meat - and the count said between those questions is still the table.
    Only a statement is read: a count inside an earlier portion question is an ask, and "how much
    mince for 4 people" three lines back is not a table for the rice that follows it. A line that
    names the people and gives no number ends it, because that is the subject moving on.
    """
    for text in reversed(older):
        if _AN_ASK.search(text):
            continue
        if _PEOPLE_WORD.search(text) or _PEOPLE_COUNT.search(text):
            found = _people_asked(text)
            if found:
                return found
            return None
        if CORRECTING.search(text):
            found = _people_asked(text) or _a_corrected_figure(text)
            if found:
                return found
    return None


_A_FIGURE = re.compile(r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
                       + NOT_A_TABLE)


# A figure in a correction can be the time of day: "its 5 in the afternoon" is not five people.
_A_CLOCK = re.compile(r"\bin the (?:morning|afternoon|evening)\b|\bat night\b|"
                      r"\bo ?clock\b|\b[ap]\.?m\.?\b")


def _a_corrected_figure(text):
    """A bare figure in a line that corrects something: "so its eleven now".

    A correction of the count says the number without a word for the people in it, which is how
    people say it out loud: "oh actually my sister is coming with her two kids so its eleven now".
    The line has to be a correction and the figure has to be a count, so a weight or a time after
    it is not one (`NOT_A_TABLE`): "put it in the oven for 8" is still a time, and "its 5 in the
    afternoon" is a clock.
    """
    if _A_CLOCK.search(text):
        return None
    found = _A_FIGURE.search(text)
    if not found:
        return None
    raw = found.group(1)
    return int(raw) if raw.isdigit() else _PEOPLE_VALUE.get(raw)


def _a_table_without_people(text):
    """True when a line with no word for people still says how many it cooks for.

    "a lasagne for six" is a table; "i need it for 8" and "put it in the oven for 8" are a date
    and a time, and the proof is the word before "for": a dish, not a pronoun or an oven.
    """
    if _PEOPLE_WORD.search(text) or CORRECTING.search(text):
        return True
    found = _BARE_FOR_COUNT.search(text)
    if not found:
        return False
    before = text[:found.start()].split()
    if not before:
        return True  # "im cooking for 8" names no dish, but it is the plan
    return before[-1].strip(".,!?;:").lower() not in _NOT_A_TABLE_BEFORE


def _per_person(clean, memory=None):
    """How much of a food a person gets, when the line asks to cook for a number of people.

    "how many potatoes per person" is not a conversion and holds no measure to convert, so it
    used to get the boiling method or a shrug. The reply gives the portion for one, and the total
    only for a headcount the person actually said: a handed a number they never gave is the one
    thing a portion must not do.
    """
    # A portion is asked for by naming the need as often as by "how much": "i need mince for
    # four people" and "i need potatoes for 6 people" were the composer's "Mince for four
    # people - fair enough. What's stopped it happening so far?" on main `054c0a0`, because
    # only the "how much" shapes were read as the question.
    #
    # Only a need is a question. "i bought 2 pounds of mince" after "how much mince for 4 people"
    # was read as the same ask and answered "About 150 g of mince each, so 900 g for six." to
    # somebody who had said what they already had: a bought weight is a fact, not an ask, so the
    # having and the buying words are out, and the portion table's own `_PORTIONS_ASK` keeps
    # them off the weight path too.
    if not re.search(r"\bhow (?:much|many|big|large)\b|\bwhat size\b|"
                     r"\bi (?:need|want)\b|\bi(?:'?m| am) (?:cooking|making)\b", clean):
        return None
    # A time in the line is a cooking question, not a portion: "how many minutes each side for a
    # steak" is the pan's answer, and the "each" that said so to this row is the side of the
    # meat rather than a person. Nothing else that wants a weight of food puts a time in it.
    if re.search(r"\b(?:minutes?|mins?|hours?|hrs?|seconds?)\b", clean):
        return None
    # "i need a cake for 20 people" wants the tin, not a weight of cake: the cake-size row
    # answers it, and the article is what tells the two needs apart. A bare food is the portion
    # question ("i need mince for four people"); "a cake", "a leg of lamb" and "a big cake for a
    # party" are things to buy or bake, and the figure here would be a weight of cake nobody can
    # act on.
    if re.search(r"\bi (?:need|want)\s+(?:a|an|one|some)\b", clean):
        return None
    if _COMPONENT.search(clean) or _PORTION_AVOID.search(clean):
        return None
    # Only the egg portion, and only for a bake: "how many eggs for a cake" is a weight, but
    # "how many pancakes for 10 people" and "how many yorkshire puddings for 12" are portions
    # the table answers well, and they say no egg at all.
    if _BAKING_PORTION.search(clean) and re.search(r"\begg", clean):
        return None
    people = _people_asked(clean)
    # "we are 8 on saturday", then "how much potato do i need": the count is in the turn
    # before, because the question is the same one with the food swapped in.
    if people is None:
        people = _people_before(
            memory, asked_for_an_amount=bool(re.search(r"\bhow (?:much|many)\b", clean)))
        stated = people is not None and _people_before(memory, statements_only=True) == people
    else:
        stated = True
    if people is None and not _PEOPLE_WORD.search(clean) and not _PORTION_WORD.search(clean):
        # "How many grams in a head of broccoli" weighs one head, and the piece table has that
        # row; only a headcount in the line makes the same food a portion question. "How many
        # people does a head of lettuce serve" says its headcount as a question, so it is a
        # portion line and the whole thing is weighed by the same head.
        for phrase in _WHOLE_PIECE:
            if re.search(rf"\b{re.escape(phrase)}\b", clean):
                return None
    if not _PEOPLE_WORD.search(clean) and people is None and not _PORTION_WORD.search(clean):
        return None
    # "How many portions in a cake" is a count of portions, not the size of one; but "how
    # many slices of bread per person" is a portion, because the people are in the line.
    if _PORTION_COUNT.search(clean) and people is None and not _PEOPLE_WORD.search(clean):
        return None
    best = None
    # The foods whose portion is only worked out for a stated headcount: without one, the
    # cooking know-how says it better than a bare figure can. A line that names the bag or the
    # tin is asking how big that is ("how many grams in a bag of pasta for 4"), so the pack
    # answer keeps it and only the plain "how much for 8 people" is summed here.
    counted = PER_PERSON_WHEN_COUNTED if (stated and not _CONTAINER.search(clean)) else ()
    for names, amount, kind, noun in PER_PERSON + counted:
        for name in names:
            # "how much salad dressing per person" is not a portion of salad.
            if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])"
                         r"(?!\s+(?:dressing|sauce|dip|oil|mayo|mayonnaise|vinaigrette|juice))",
                         clean):
                if best is None or len(name) > len(best[0]):
                    best = (name, amount, kind, noun)
    if not best:
        # A line can ask for the portions without naming the dish ("how many portions do i need
        # for 12 people"), and there was no row to reach: the search hedge. The rule of thumb is
        # what the answer is, and the sum comes once they say what is going on the table.
        if people is not None and stated and _PORTION_WORD.search(clean):
            return ("A main is about 300 g a head, a plate of pasta or rice 75 to 100 g dry and "
                    "a buffet six to eight pieces a guest, so for "
                    f"{_said_people(people)} plan on "
                    f"{_mass_of(300 * people)} of the main dish. Tell me what you are cooking "
                    "and I will do the sum for the shopping.")
        return None
    _name, amount, kind, noun = best
    # A dish is made, not measured: "i want to bake a cake for a party" was answered "About 60 g of
    # cake each." - a portion with nobody in it - and "i want to make a curry for four" "About 300 g
    # of the dish each, so 1.2 kg for four.", where the row that owns the dish has the plan for it.
    # A food with a portion keeps the table, because "i want to make rice for six" is the same
    # question as "how much rice for six people", and so does a line that says "how much"
    # however it is wrapped: "i need to know how much rice for six people".
    if (noun in MADE_NOT_MEASURED
            and re.search(r"\bi (?:need|want)\s+to\b"
                          r"|\bi(?:'?m| am) (?:cooking|making|baking|roasting|prepping)\b", clean)
            and not re.search(r"\bhow (?:much|many|big|large)\b|\bwhat size\b", clean)):
        return None
    # "How big a chicken for six" is a bird on the bone, not 200 g of meat each: the portion of
    # meat is right for a plate and wrong for a whole bird, and the shape of the question says
    # which one is being asked.
    if _name in _BIRDS and re.search(r"\bhow (?:big|large)\b|\bwhat size\b", clean):
        amount, noun = BIRD_GRAMS, _name
    if kind == "each":
        # "slices of bread" is already plural and must not become "slices of breads".
        bunch = noun if noun.endswith("s") or " " in noun else noun + "s"
        said = f"{amount} {bunch}" if amount > 1 else f"1 {noun}"
        if people:
            total = (f"{amount * people:g} {bunch}" if amount > 1
                     else f"{_SAID_PEOPLE.get(people, people)} {bunch}")
            return f"About {said} each, so {total} for {_said_people(people)}."
        if not _PEOPLE_WORD.search(clean):
            return f"A portion is about {said}."
        return f"About {said} each."
    if kind == "bottle":
        per = "half a bottle" if amount == 0.5 else f"{amount:g} bottles"
        if not people:
            return f"Allow about {per} of {noun} a guest."
        bottles = int(math.ceil(amount * people))
        return (f"Allow about {per} of {noun} a guest, so {bottles} "
                f"{'bottle' if bottles == 1 else 'bottles'} for {_said_people(people)}.")
    if kind == "ml":
        if people:
            return (f"About {amount} ml of {noun} each, so "
                    f"{_litres_of(amount * people)} for {_said_people(people)}.")
        if not _PEOPLE_WORD.search(clean):
            return f"A portion of {noun} is about {amount} ml."
        return f"About {amount} ml of {noun} each."
    if people:
        return (f"About {_grams(amount)} g of {noun} each, so "
                f"{_mass_of(amount * people)} for {_said_people(people)}.")
    if not _PEOPLE_WORD.search(clean):
        return f"A portion of {noun} is about {_grams(amount)} g."
    return f"About {_grams(amount)} g of {noun} each."


def _said_people(people):
    """A headcount the way it is said: "for one", "for eight", never "for 1"."""
    return _SAID_PEOPLE.get(people, str(people))


def _mass_of(grams):
    """A scaled-up portion the way a shopper reads it: 1 kg, not 1,000 g."""
    if grams >= 1000:
        kilos = f"{grams / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{kilos} kg"
    return f"{_grams(grams)} g"


def _litres_of(ml):
    """A scaled-up pour the way a jug reads it: 2.4 litres, not 2,400 ml."""
    if ml >= 1000:
        litres = f"{ml / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{litres} litres"
    return f"{ml} ml"


# A land measure on its own is a question about a picture, not a conversion: "how big is an
# acre" has no second unit in it to convert to. The answer is the same fact whichever why it
# is asked, and it is written once here so every land question shares it.
LAND_PLAIN = {
    "acre": "An acre is 4,047 square metres, or 4,840 square yards: a square about 64 metres "
            "on each side, a little under half a hectare, and roughly half a football pitch.",
    "hectare": "A hectare is 10,000 square metres: a square 100 metres on each side, two and a "
               "half acres, or about one and a half football pitches.",
    "sq mile": "A square mile is 2.59 square kilometres, or 640 acres.",
    "sq km": "A square kilometre is a square 1 kilometre on each side: 100 hectares, or about "
             "0.39 of a square mile.",
    "sq m": "A square metre is a square 1 metre on each side, about 10.8 square feet.",
    "sq ft": "A square foot is 144 square inches, or about 0.09 square metres: a square 30cm "
             "on each side.",
    "sq yd": "A square yard is 9 square feet, or about 0.84 square metres: a square 91cm on "
             "each side.",
}

# The ask a size question wears: what is this ground like to stand on, not how many of it.
_LAND_ASK = re.compile(r"\bhow (?:big|large|long|wide)\b|\bsize of\b|\bwhat size\b"
                       r"|\bwhat(?:'s| is)\b|\bhow much (?:land|ground|space)\b")


# A size said as a share of an acre is still a question about a size, and the answer people
# want is a picture of it, not a conversion: "a garden of 0.15 acres, is that big" and "is 0.2
# of an acre a big garden" were both shrugs. The references are things a person has stood on,
# smallest first, so the answer is the nearest one a person can picture.
_AREA_PICTURES = (
    ("parking space", "parking spaces", 12.5),
    ("doubles tennis court", "doubles tennis courts", 260.0),
    ("football pitch", "football pitches", 7140.0),
)
# What a share of a land measure is said as, for the share written in words: "half an acre",
# "a quarter of an acre", "two thirds of an acre".
_WORD_SHARE = (("three quarters", 0.75), ("two thirds", 2 / 3.0), ("three quarters of", 0.75),
               ("two thirds of", 2 / 3.0), ("a third", 1 / 3.0), ("a quarter", 0.25),
               ("a half", 0.5), ("half", 0.5), ("quarter", 0.25), ("third", 1 / 3.0))
# The words that ask for a judgement of size rather than a conversion. A land unit with a
# number or a share on it is the fence: nothing else in the line can reach this.
_A_SIZE_JUDGEMENT = re.compile(
    r"\b(?:big|large|small|huge|tiny|sizeable|decent|reasonable|enough)\b"
    r"|\bhow much (?:land|ground|space)\b|\bis that a lot\b")


def _count_said(ratio):
    """A count of a picture, said the way a person says it: "two", "two and a half".

    Halves are as precise as a picture gets - "2 and a quarter doubles tennis courts" is a
    number nobody says - and the word "about" in front of it covers the rounding.
    """
    whole = int(ratio)
    part = ratio - whole
    if part < 0.25:
        return "%d" % whole
    if part < 0.75:
        return ("%d and a half" % whole) if whole else "half"
    return "%d" % (whole + 1)


def _area_pictures(square_metres):
    """The nearest thing a person has stood on, said as a count: "about two tennis courts"."""
    for name, plural, size in _AREA_PICTURES:
        ratio = square_metres / size
        if ratio < 5 or size == _AREA_PICTURES[-1][2]:
            break
    if ratio < 0.4:
        return "less than half a " + name
    if ratio < 0.75:
        return "about two thirds of a " + name
    if ratio < 1.15:
        return "about a " + name
    if ratio < 1.85:
        return "a bit more than a " + name
    return "about %s %s" % (_count_said(ratio), plural)


def _share_before(clean, start):
    """The count or share of a land measure said before it: 0.15, half, a quarter, 2."""
    text = clean[:start]
    found = re.search(r"(\d+(?:\.\d+)?)\s*(?:of\s+)?(?:an?\s+)?$", text)
    if found:
        return float(found.group(1))
    for word, value in _WORD_SHARE:
        if re.search(r"\b" + re.escape(word) + r"\s*(?:of\s+)?(?:an?\s+)?$", text):
            return value
    return None


def _land_in_pictures(value, unit, clean=""):
    """A number of acres asked *whether it is big*: the size, then the nearest picture of it."""
    table = {name: size for name, _, size in UNITS["area"]}
    square_metres = value * table[unit]
    if square_metres < 1:
        return None
    if abs(value - 1) < 1e-9:
        said = "One " + SAID_ONE[unit]
    elif abs(value - round(value)) < 1e-9:
        said = "%d %s" % (round(value), SAID[unit])
    else:
        said = "%s %s" % (_fmt(value), SAID[unit])
    body = "%s is about %s square metres - %s" % (
        said, _fmt(round(square_metres)), _area_pictures(square_metres))
    # A garden is the thing people are really asking about, and most gardens are far smaller
    # than a quarter of an acre, so the comparison is worth saying once here.
    if square_metres >= 400 and "garden" in clean:
        body += ", which is a generous garden for a house"
    if abs(value - 1) < 1e-9:
        return body + "."      # one acre is the definition itself: the tail would repeat it
    return body + ". " + LAND_PLAIN[unit]


def _land_size(clean, mentions):
    """"how big is an acre": one land measure named, with no number and no second unit."""
    if len(mentions) != 1:
        return None
    start, end, family, unit = mentions[0]
    if family != "area" or unit not in LAND_PLAIN:
        return None
    # "a garden of 0.15 acres, is that big": a count of land with a size judgement on it is a
    # picture question, and it is answered before the no-number rule below.
    if _A_SIZE_JUDGEMENT.search(clean):
        counted = _share_before(clean, start)
        if counted is not None:
            pictured = _land_in_pictures(counted, unit, clean)
            if pictured:
                return pictured
    # "an acre" and "a hectare" are the article, not a count: only a real number makes the
    # line a conversion of some acres rather than a question about one of them.
    before = clean[max(0, start - 14):start]
    if not _LAND_ASK.search(clean):
        return None
    if re.search(r"\d\s*$", before) or re.search(r"\b(?:two|three|four|five|ten|twenty)\s+$",
                                                   before):
        return None
    # "how big is an acre in square feet" names the unit wanted and is the pair's question.
    if _UNIT_WORD.search(clean[end:]) or _TARGET.search(clean[:start].strip()):
        return None
    return LAND_PLAIN[unit]


def _height(clean, mentions):
    """A height typed the way people type it: 5'6, 5ft 6, or 1.8m asked for in feet and inches."""
    if not any(unit in ("cm", "m") for _, _, _, unit in mentions):
        return None
    match = (re.search(r"(\d)\s*(?:'|’|ft|foot|feet)\s*(\d{1,2})\s*(?:\"|''|in|inch|inches)?",
                       clean)
             or re.search(r"(\d)\s*(?:ft|foot|feet)\s+(\d{1,2})\b", clean))
    if not match:
        return _metres_in_feet(clean)
    feet, inches = int(match.group(1)), int(match.group(2))
    if not 2 <= feet <= 8 or inches > 11:
        return None
    total = feet * 12 + inches
    return (f"{feet} feet {inches} is about {round(total * 2.54)} cm, or "
            f"{total * 0.0254:.2f} m.")


_ASKS_FEET = re.compile(r"\b(?:feet|foot|ft|tall)\b")

# How a person states their own height, either way round: "im 1.75 metres", "i am 175cm",
# "my height is 5 foot 9". The number alone is not enough - "the wall is 1.75 m" is a wall.
_SAYS_OWN_HEIGHT = re.compile(
    r"\b(?:i'?m|i am|im|my height is|my height's|my height)\b", re.I)
_HEIGHT_METRES = re.compile(r"(?<![\w.])(\d(?:\.\d{1,2})?)\s*(?:m|metres?|meters?)(?!\w)", re.I)
_HEIGHT_CM = re.compile(r"(?<![\w.])(\d{2,3}(?:\.\d)?)\s*(?:cm|centimetres?|centimeters?)(?!\w)",
                        re.I)
_HEIGHT_FEET = re.compile(
    r"(?<![\w.])([2-7])\s*(?:'|\u2019|ft|foot|feet)\s*(\d{1,2})\s*(?:\"|''|in|inch|inches)?(?!\w)",
    re.I)
_HEIGHT_FEET_WORD = re.compile(r"(?<![\w.])([2-7])\s*(?:ft|foot|feet)\s+(\d{1,2})\b", re.I)
# "im 2 metres from the tv" is a distance and 2 m falls inside the height window: a line that
# says how far or how long something is, and never says "tall", is not a height at all.
_NOT_A_HEIGHT = re.compile(
    r"\b(?:away|from|apart|long|wide|deep|of rope|of wood|of cable|of string|of pipe|of cord)\b",
    re.I)


def _is_a_distance(clean):
    """True when the number is how far or how long, not how tall."""
    return bool(_NOT_A_HEIGHT.search(clean)) and not re.search(r"\btall\b", clean, re.I)


# A stated height is context when the line goes on to ask something else. The human's shape:
# "im 5 foot 2 and i need trousers for work, what do i look for" was answered "5 foot 2 is about
# 157 cm, or 1.57 m." - a true sentence and not the question. The ask word alone is not enough,
# because "im 5 foot 9, what is that in cm" asks about the measure itself, so the few words after
# the ask word are read too.
_ASKS_ELSEWHERE = re.compile(
    r"\b(?:what|which|where|who|whose|should|shall|could|would|can|need|needs|looking for"
    r"|look for|recommend|suggest|ideas|advice|buy|buying|wear|choose|pick|worth|fit|fits)\b",
    re.I)
_A_MEASURE_QUESTION = re.compile(
    r"\b(?:cm|centimetres?|centimeters?|m|metres?|meters?|feet|foot|ft|inches?|inch|tall|height"
    r"|that|this|it|in|convert|converted)\b", re.I)


# A complaint in the line is a question even when it is said without a question word: on main
# `ff33dbb` "i am 5ft 2 and standing all day at work kills my feet" was answered with the
# conversion, because a height and a hurt came in the same breath.
_A_COMPLAINT = re.compile(
    r"\b(?:hurt|hurts|hurting|ache|aches|aching|achy|sore|pain|painful|kills?|killing"
    r"|blister|blisters|swollen|numb|too (?:small|tight|big|long|short|loose)"
    r"|doesn'?t fit|don'?t fit|does not fit|do not fit|rubbed|rubbing)\b", re.I)


# A count asked for is a question about the things counted, not about the measure they are cut
# from: "im boarding out the loft ceiling, 3 by 2 metres, how many sheets" has an "im" and a metre
# measure in it, so it read as the person's own height and was answered "2 m is about 6 foot 7"
# while the plasterboard card that the same words reached never got the line.
_ASKS_HOW_MANY = re.compile(r"\bhow\s+(?:many|much)\s+(?P<thing>[a-z]+)", re.I)
# Sizes people ask for that the unit table does not carry: a horse is 15 hands, a field 40 paces.
# A line that asks a height in those is the measure's own question, so it keeps the conversion -
# "im 4 foot 11 how many hands is that" answered "4 foot 11 is about 150 cm" on main, and a guard
# that read "hands" as a count of things turned it into "I'm listening".
_A_MEASURE_SAID_ANOTHER_WAY = frozenset(("hand", "hands", "pace", "paces", "span", "spans"))


def _asks_something_else(clean):
    """True when a stated height comes with a question about something that is not a measure."""
    if _A_COMPLAINT.search(clean):
        return True
    for match in _ASKS_HOW_MANY.finditer(clean):
        # "how many feet is 2 metres" and "how many grams in a cup" are the measure's own
        # questions, so a unit word keeps the conversion.
        thing = match.group("thing").lower()
        if not _UNIT_WORD.fullmatch(thing) and thing not in _A_MEASURE_SAID_ANOTHER_WAY:
            return True
    for match in _ASKS_ELSEWHERE.finditer(clean):
        tail = " ".join(clean[match.end():].split()[:5])
        if not _A_MEASURE_QUESTION.search(tail):
            return True
    return False


def _own_height(clean):
    """The other number for a height the person states about themselves, or None.

    "im 1.75 metres" -> "1.75 m is about 5 foot 9 (5.7 feet)."
    "im 5 foot 9" -> "5 foot 9 is about 175 cm, or 1.75 m."
    """
    if not _SAYS_OWN_HEIGHT.search(clean):
        return None
    if _is_a_distance(clean):
        return None
    # "im 5 foot 2 and i need trousers for work, what do i look for": the height is a fact about
    # the person, and the question is about trousers. Converting here answered neither.
    if _asks_something_else(clean):
        return None
    metres, said = None, ""
    found = _HEIGHT_METRES.search(clean)
    if found:
        metres, said = float(found.group(1)), f"{found.group(1)} m"
    if metres is None:
        found = _HEIGHT_CM.search(clean)
        if found:
            metres, said = float(found.group(1)) / 100, f"{found.group(1)} cm"
    if metres is not None:
        if not 1.2 <= metres <= 2.2:
            return None
        total = metres / 0.0254
        feet = int(total // 12)
        inches = round(total - feet * 12)
        if inches == 12:
            feet, inches = feet + 1, 0
        return f"{said} is about {feet} foot {inches} ({total / 12:.1f} feet)."
    match = _HEIGHT_FEET.search(clean) or _HEIGHT_FEET_WORD.search(clean)
    if not match:
        return None
    feet, inches = int(match.group(1)), int(match.group(2))
    if inches > 11:
        return None
    cm = round((feet * 12 + inches) * 2.54)
    return (f"{feet} foot {inches} is about {cm} cm, or {cm / 100:.2f} m.")


def _metres_in_feet(clean):
    """A height given in metres or centimetres, asked for in feet and inches.

    Only a height: 1.2 m to 2.2 m covers a child to a tall adult, so a room, a run or a
    length of cable is left to the plain conversion. "1.8m" reaches here as "1.8 m" because
    _JOINED puts the space in, which is why the metre spelling is worth its own branch.
    """
    if not _ASKS_FEET.search(clean):
        return None
    metres, said = None, ""
    found = re.search(r"(?<![\w.])(\d(?:\.\d{1,2})?)\s*(?:m|metres?|meters?)(?!\w)", clean)
    if found:
        metres, said = float(found.group(1)), f"{found.group(1)} m"
    else:
        found = re.search(r"(?<![\w.])(\d{2,3}(?:\.\d)?)\s*(?:cm|centimetres?|centimeters?)"
                          r"(?!\w)", clean)
        if found:
            metres, said = float(found.group(1)) / 100, f"{found.group(1)} cm"
    if metres is None or not 1.2 <= metres <= 2.2:
        return None
    total = metres / 0.0254
    feet = int(total // 12)
    inches = round(total - feet * 12)
    if inches == 12:
        feet, inches = feet + 1, 0
    return f"{said} is about {feet} foot {inches} ({total / 12:.1f} feet)."


def _cup_of_something(clean):
    """Grams in a cup, mug, tablespoon or teaspoon of a dry thing, asked about by name.

    Cups and spoons measure volume, so a dry ingredient's weight depends on what it is;
    GRAMS_PER_CUP holds the weights cooks use, scaled down for the smaller spoons.
    """
    if _PER_CUP.search(clean):
        return None  # "grams of coffee per cup" is a dose, and the coffee entry knows it
    measure, share = "cup", 1.0
    if re.search(r"\bmugs?\b", clean):
        measure, share = "mug", 240 / 250
    elif _names_unit(clean, "tbsp"):
        measure, share = "tablespoon", 16.0
    elif _names_unit(clean, "tsp"):
        measure, share = "teaspoon", 48.0
    elif _names_unit(clean, "dessertspoon"):
        measure, share = "dessertspoon", 24.0
    text = "a " + measure
    if measure in ("tablespoon", "teaspoon", "dessertspoon"):
        spoon = [(food, grams) for food, grams in GRAMS_PER_TSP
                 if re.search(rf"\b{re.escape(food)}\b", clean)]
        if spoon:
            food, grams = max(spoon, key=lambda row: len(row[0]))
            # the table is grams in a teaspoon, so the spoon's own size scales it
            amount = grams * (240.0 / share) / 5.0
            return f"A {measure} of {food} is about {_fmt(amount)} g."
    named = _food_named(clean)
    if named and _asks_for_weight(clean):
        food, grams = named
        amount = grams if share == 1.0 else max(1, round(grams / share))
        said = AS_KITCHEN_SAYS.get(food, food)
        return f"A {measure} of {said} is about {_grams(amount)} g."
    if _WEIGH.search(clean) or re.search(r"\b(grams?|g|oz|ounces?|kg)\b", clean):
        return ("It depends what is in " + text + ": flour is about 120 g, sugar about 200 g, "
                "butter 227 g. By volume a cup is 240 ml, which is 8 fluid ounces.")
    return None


def _handful(clean):
    """A handful, and how many grams of the food in it.

    "How many grams in a handful of almonds" is the everyday version of a serving, and the
    answer is a quarter of a cup of whatever it is: the cup weight this table already holds
    gives the grams. Without a named food there is still a useful figure to give, so the
    reply gives the quarter cup and three weights that show the spread.
    """
    if not re.search(r"\bhandfuls?\b", clean):
        return None
    if not (_asks_for_weight(clean) or re.search(r"\bhow much\b", clean)):
        return None
    # "how much does a handful of almonds cost" is a price question; the price entry is honest
    # about it and grams are not an answer to it.
    if re.search(r"\b(?:cost|costs|costing|price|prices|priced|cheap|cheaper|expensive)\b", clean):
        return None
    food = _food_named(clean)
    if food:
        name, grams_per_cup = food
        said = AS_KITCHEN_SAYS.get(name, name)
        return (f"A handful of {said} is about {_grams(round(grams_per_cup / 4))} g, "
                f"since a handful is roughly a quarter of a cup.")
    stuff = ""
    said_food = re.search(r"\bhandfuls?\s+(?:of\s+)?"
                          r"(?!of\b|it\b|them\b|these\b|those\b|that\b)"
                          r"([a-z]+(?:\s+[a-z]+)?)", clean)
    if said_food:
        # "what is a handful in grams" and "how much does a handful of crisps weigh" put a unit
        # or a verb after the handful: "A handful of in grams is..." is not a sentence, so those
        # words come out and a line left with no food gets the plain three-example answer.
        stuff = " ".join(word for word in said_food.group(1).split() if word not in _NOT_A_FOOD)
    if stuff:
        # A food this table has no cup weight for: the spread is the useful part, because a
        # handful of leaves and a handful of nuts are nowhere near each other.
        return (f"A handful of {stuff} is about a quarter of a cup, but the weight depends on "
                "what is in it: 35 g of nuts against 8 g of spinach.")
    return ("A handful is about a quarter of a cup, which comes to roughly 35 g of nuts, "
            "30 g of raisins or 25 g of crisps.")


# A word after "a handful" that is a unit, a verb or a price, not a food.
_NOT_A_FOOD = frozenset((
    "in", "is", "are", "of", "for", "grams", "gram", "g", "kg", "oz", "ounce", "ounces", "lb",
    "lbs", "cups", "cup", "ml", "litre", "litres", "per", "weight", "weigh", "weighs", "cost",
    "costs", "price", "prices", "each", "person", "people", "portion", "serving", "worth"))


# "Pounds" is money when a figure carries it and the line asks whether that is a lot, dear or
# worth it: "is 4 pounds a lot for a pint of milk" is a price question, and answering it with
# what the milk weighs reads the "pounds" as a weight. The same word is a weight in "5 pounds of
# potatoes" and "a pint of milk in pounds", where nothing in the line is judging a price.
_POUNDS_IS_MONEY = re.compile(
    r"(?:£\s*\d|\b\d+(?:\.\d+)?\s*(?:pounds?|quid|pence|p\b|gbp))"
    r"[^.?!]*?\b(?:a lot|lot for|expensive|cheap|cheaper|cheapest|dear|dearer|overpriced|"
    r"rip.?off|worth it|worth the|too much|reasonable|fair|good price|bad price|a rip|what price)",
    re.I)


def _asks_for_weight(clean):
    """True when the line wants a weight: "how many grams", "what does a cup weigh", "in oz".

    "How much water for two cups of tea" names a food and a cup but wants a pour, not grams,
    so a food's cup weight is only given when the line itself asks for a weight. A figure in
    pounds that the line is judging the price of is money, not a weight, so it asks nothing about
    grams: "is 4 pounds a lot for a pint of milk" wants the price the milk sells at.
    """
    if _POUNDS_IS_MONEY.search(clean):
        return False
    if _WEIGH.search(clean):
        return True
    return bool(re.search(r"\b(?:grams?|g|kg|kilograms?|oz|ounces?|pounds?|lbs?)\b", clean))


def _names_unit(clean, unit):
    """True when the line names this unit, in any of its words."""
    for _, items in UNITS.items():
        for name, words, _ in items:
            if name == unit and any(re.search(rf"\b{re.escape(word)}\b", clean)
                                    for word in words):
                return True
    return False


def _frac(clean):
    """A recipe's fractions as decimals, so "3/4 cup" reads as three quarters of a cup."""
    def unit_and_a_half(match):
        count = match.group("count") or "one"
        whole = _SAID_WHOLE.get(count) or int(count) if count.isdigit() else _SAID_WHOLE[count]
        return f"{whole + 0.5:g} {match.group('unit')}"

    clean = _UNIT_AND_A_HALF.sub(unit_and_a_half, clean)

    def mixed(match):
        value = _FRACTION.get((match.group(2), match.group(3)))
        if not value:
            return match.group(0)
        return f"{int(match.group(1)) + value:g}"

    clean = _MIXED.sub(mixed, clean)
    clean = _AND_A_HALF.sub(lambda m: f"{(_SAID_WHOLE.get(m.group(1)) or int(m.group(1))) + 0.5:g}",
                            clean)
    for word_fraction, value in _WORD_FRACTION:
        clean = word_fraction.sub(value, clean)

    def slash(match):
        value = _FRACTION.get((match.group(1), match.group(2)))
        return f"{value:.4f}".rstrip("0").rstrip(".") if value else match.group(0)

    return _SLASH.sub(slash, clean)


_HOW_TO = re.compile(r"(?:how\s+do\s+i|how\s+to|how\s+can\s+i|how\s+do\s+you|convert|"
                     r"change|work\s+out|turn)\b")


def _rule_sentence(family, from_unit, to_unit):
    """The rule for a conversion asked as a rule: no numbers, so the factor and one example."""
    source = _factor(family, from_unit)
    target = _factor(family, to_unit)
    if not source or not target or abs(source - target) < 1e-9:
        return None
    factor = source / target
    said_from = SAID.get(from_unit, from_unit)
    said_to = SAID.get(to_unit, to_unit)
    # Division reads better than a fraction whenever the answer is smaller: "divide the grams
    # by 28.3" is something a person can do, "multiply the grams by 0.035" is not.
    if factor >= 1:
        rule = f"multiply the {said_from} by {_fmt(factor)}"
    else:
        rule = f"divide the {said_from} by {_fmt(1 / factor)}"
    # The example is the round number that gives at least one of the unit wanted: 10 miles
    # rather than 1 to show the kilometres, but 100 grams to show the ounces.
    amount = 1
    for candidate in (1, 10, 100, 1000, 10000):
        amount = candidate
        if candidate * factor >= 1:
            break
    example = (f"{_fmt(amount)} {_say(amount, from_unit, one=amount == 1)} is "
               f"{_fmt(amount * factor)} {_say(amount * factor, to_unit)}")
    return f"To go from {said_from} to {said_to}, {rule}: {example}."


# The words a line made of nothing but a conversion is allowed to keep once its units are taken
# out: the grammar between them and the ask in front of them.
_BARE_JOIN = frozenset((
    "to", "in", "into", "as", "convert", "converting", "how", "do", "i", "many", "much", "is",
    "are", "there", "and", "the", "a", "an", "what", "s"))


def _is_bare_pair(clean, mentions):
    """True when the line is nothing but two units and the word between them: "km to miles".

    The units are taken out by where they were found, not word by word: a unit can be two words
    ("ml to fl oz", "kin to fluid ounces") and the old word check read "fl" as a stray, so every
    line naming a fluid ounce as one of a bare pair returned None.
    """
    if len(mentions) < 2:
        return False
    rest = clean
    for start, end, _family, _unit in reversed(mentions):
        rest = rest[:start] + " " + rest[end:]
    rest = re.sub(r"\d+(?:\.\d+)?", " ", rest)
    words = re.findall(r"[a-z]+", rest)
    return bool(words) and all(word in _BARE_JOIN for word in words)


# The ounce is two units in one word: 28.35 g of weight and 28.4 ml of liquid. Which one a line
# means is settled by the measure on the other side - "150 ml to oz" is fluid ounces, "150 g to
# oz" is weight - so the family of the other measure picks the sense, whichever side it is on.
# Before this the liquid sense was one special case inside the "how many ounces in a pint"
# branch, so every other shape hedged: "ml to oz", "150 ml to oz", "500 ml to oz", "how do i
# convert ml to oz" and "how do i convert oz to ml" were all a search offer, while "how many oz
# in 500 ml" answered.
def _the_ounce_pair(family, unit, other_family, other_unit):
    """Both sides of a conversion, with a bare ounce read in the other side's family."""
    if unit == "ounce" and other_family == "volume":
        return "volume", "fl oz", other_family, other_unit
    if other_unit == "ounce" and family == "volume":
        return family, unit, "volume", "fl oz"
    if unit == "fl oz" and other_family == "mass":
        return "mass", "ounce", other_family, other_unit
    if other_unit == "fl oz" and family == "mass":
        return family, unit, "mass", "ounce"
    return family, unit, other_family, other_unit


def _how_to_convert(clean, mentions):
    """"how do i convert km to miles" names the two units and no number: give the rule."""
    if not _HOW_TO.search(clean) and not _is_bare_pair(clean, mentions):
        return None
    if _NUMBER.search(clean) or any(_number_before(clean, start) is not None
                                    for start, _end, _f, _u in mentions):
        return None
    for position, (start, _end, family, unit) in enumerate(mentions):
        for other_start, _oend, other_family, other_unit in mentions[position + 1:]:
            family, unit, other_family, other_unit = _the_ounce_pair(
                family, unit, other_family, other_unit)
            if other_family != family or other_unit == unit:
                continue
            return _rule_sentence(family, unit, other_unit)
    return None


# What turns a measure into a plan instead of a conversion, when it comes after the measure:
# "how many days in a week should I run", "how many hours a week can I train", "how many minutes
# a day do I need to stretch", "how many days in a week is healthy". The measure is the object of
# a question about what to do, not the thing being converted.
#
# It is a list of askers rather than a list of allowed tails on purpose: an unseen noun after the
# measure ("3 weeks off work", "6 weeks training", "4 weeks notice") is still a measure taken out
# of something, and main answers those as conversions. Allowlisting the tail dropped five of them.
_ASKING_AFTER_MEASURE = re.compile(
    r"\b(should|shall|can|could|will|would|may|might|must|need|needs|needed|"
    r"do|does|did|don't|doesn't|didn't|have to|has to|had to|ought|supposed to|allowed|"
    r"is it|is that|are there|enough|normal|healthy|safe|too much|too many|until|till)\b")


def _tail_is_about_the_measure(tail):
    """True when the measure is what the line asks about, rather than the object of a plan.

    A measure is nearly always taken out of something - a pound of mince, a metre of fabric,
    a cup of flour, ten minutes of stretching, three weeks off work - so the words after it are
    how a person says what is measured. What does change the question is an asker after the
    measure: "how many days in a week should I run" is a training plan, not a conversion of a
    week into days, so it is left to the modules that read it.
    """
    return not _ASKING_AFTER_MEASURE.search(tail.lower())



# --- a fraction of a cup or a spoon, asked on its own ----------------------
# "what is a third of a cup" is a measure question with no unit to convert to: the answer is the
# amount in the units a cook has in the drawer. The fractions are the ones recipes write, and the
# line is only a question about the measure itself - a food name or a unit to convert to is
# somebody else's line ("how many grams in a cup of rice", "a third of a cup in ml").
_SHARE = re.compile(
    r"\b(?P<word>three[\s-]quarters?|two[\s-]thirds?|one[\s-](?:third|quarter|half)|"
    r"a[\s-](?:third|quarter|half|fifth|sixth)|half|\d\s*/\s*\d)\s*(?:of\s+)?(?:an?\s+)?"
    r"(?P<unit>cups?|tablespoons?|tbsp|teaspoons?|tsp)\b")
_SHARE_VALUE = {"three quarters": 0.75, "three quarter": 0.75, "three-quarters": 0.75,
                "three-quarter": 0.75, "two thirds": 2 / 3, "two third": 2 / 3,
                "two-thirds": 2 / 3, "two-third": 2 / 3, "one third": 1 / 3,
                "one-third": 1 / 3, "one quarter": 0.25, "one-quarter": 0.25,
                "one half": 0.5, "one-half": 0.5, "a third": 1 / 3, "a-third": 1 / 3,
                "a quarter": 0.25, "a-quarter": 0.25, "a half": 0.5, "a-half": 0.5,
                "a fifth": 0.2, "a-fifth": 0.2, "a sixth": 1 / 6, "a-sixth": 1 / 6,
                "half": 0.5}
_SHARE_FRACTION = re.compile(
    r"\b(?:three[\s-]quarters?|two[\s-]thirds?|one[\s-](?:third|quarter|half)|"
    r"a[\s-](?:third|quarter|half|fifth|sixth)|half|\d\s*/\s*\d)\b")
_SHARE_SAID = {"three quarters": "three quarters", "three-quarter": "three quarters",
               "two thirds": "two thirds", "two-third": "two thirds", "one third": "a third",
               "one-quarter": "a quarter", "one half": "half", "half": "half"}
_SHARE_ASK = re.compile(r"\b(?:what\s+is|whats|what's|how\s+much\s+is|how\s+much|"
                        r"how\s+many|how\s+big\s+is)\b")
_NOT_ABOUT_A_MEASURE = re.compile(
    r"\bgrams?\b|\bg\b|\bml\b|\bmillilitres?\b|\bmilliliters?\b|\blitres?\b|\bliters?\b|"
    r"\bounces?\b|\boz\b|\bpounds?\b|\blbs?\b|\bpints?\b|\bquarts?\b|\bcelsius\b|"
    r"\bfahrenheit\b|\bdegrees?\b|\bcalories?\b")


def _share_value(word):
    """The number a fraction word is, or None when it is not a fraction this table knows."""
    if word in _SHARE_VALUE:
        return _SHARE_VALUE[word]
    slash = re.fullmatch(r"(\d)\s*/\s*(\d)", word)
    if slash and int(slash.group(2)):
        return int(slash.group(1)) / int(slash.group(2))
    return None


def _share_name(value):
    """The name a cook would give this fraction, for the lines that write it in digits."""
    for known, name in ((0.25, "a quarter"), (0.5, "half"), (0.75, "three quarters"),
                        (1 / 3, "a third"), (2 / 3, "two thirds"), (0.2, "a fifth"),
                        (1 / 6, "a sixth"), (1 / 8, "an eighth"), (0.125, "an eighth")):
        if abs(value - known) < 0.001:
            return name
    return None


def _share_spoons(value, per):
    """The spoons a fraction of a unit is: whole ones, then the teaspoons left over."""
    spoons = value * per
    whole = int(spoons)
    rest = round((spoons - whole) * 3)
    if rest >= 3:
        whole, rest = whole + 1, 0
    if not whole:
        return "a teaspoon" if rest == 1 else f"{rest} teaspoons"
    said = f"{whole} tablespoon" if whole == 1 else f"{whole} tablespoons"
    if not rest:
        return said
    return said + (" and a teaspoon" if rest == 1 else f" and {rest} teaspoons")


def _share_of_a_measure(clean, tail=True):
    """A fraction of a cup, a tablespoon or a teaspoon, answered in the smaller units."""
    if not _SHARE_ASK.search(clean) or _NOT_ABOUT_A_MEASURE.search(clean):
        return None
    match = _SHARE.search(clean)
    if not match:
        return None
    word = " ".join(match.group("word").split())
    value = _share_value(word)
    if not value:
        return None
    said = _share_name(value) or word
    # "half of a third of a cup" is a fraction of a fraction written in words: the fractions
    # multiply, so the answer is the sixth of a cup that comes out.
    before = _SHARE_FRACTION.findall(clean[:match.start()]) if \
        re.search(r"\bof\s*$", clean[:match.start()]) else []
    if before:
        outer_word = " ".join(before[-1].split())
        outer = _share_value(outer_word)
        if outer:
            value *= outer
            said = f"{_share_name(outer) or outer_word} of {said}"
    unit = match.group("unit")
    # a measure word elsewhere in the line is a second half to the question - "a third of a cup
    # of flour", "half a cup for two people" - and those rows answer it better than this one
    rest = (clean[:match.start()] + " " + clean[match.end():])
    if re.search(r"\b(?:cups?|tablespoons?|tbsp|teaspoons?|tsp)\b", rest):
        return None
    if unit.startswith(("cup",)):
        millilitres = round(value * 240)
        lead = "Half a cup" if said == "half" else f"{said[0].upper()}{said[1:]} of a cup"
        advice = ": spoons are the easy way to cut a cup down." if tail else "."
        return f"{lead} is {_share_spoons(value, 16)}, about {millilitres} ml{advice}"
    said = f"{said[0].upper()}{said[1:]}"
    if unit.startswith(("tablespoon", "tbsp")):
        millilitres = round(value * 15)
        return (f"{said} of a tablespoon is "
                f"{_tsp_phrase(value * 3)}, about {millilitres} ml.")
    millilitres = round(value * 5)
    return f"{said} of a teaspoon is about {millilitres} ml."


def _tsp_phrase(count):
    """A count of teaspoons, rounded the way a cook says it."""
    if abs(count - round(count)) < 0.05:
        whole = round(count)
        return f"{whole} teaspoons" if whole != 1 else "a teaspoon"
    return f"about {round(count, 1)} teaspoons"



# --- a fraction of an hour, and a span of time asked in minutes -------------------
# "what is a quarter of an hour", "how many minutes in an hour and a half" and "what fraction of a
# day is an hour" were all the hourly-pay card ("divide the yearly pay by the hours you are
# actually paid for"), because that row's key holds the words "an hour" and the ask is "what".
# Nothing in any of the three is about money: one asks for the span in minutes, one for the span
# of a mixed quantity, one for the fraction of the unit. All three are read off the same two parts
# - a fraction or a count, and a unit of time - so they are answered here, beside the fractions of
# a cup, rather than by a row per phrasing.
_TIME_SMALLER = {"hour": (60, "minutes"), "minute": (60, "seconds"), "day": (24, "hours"),
                 "week": (7, "days")}
_TIME_ARTICLE = {"hour": "an hour", "minute": "a minute", "day": "a day", "week": "a week"}
_TIME_UNIT = {"hour": "hour", "hours": "hour", "hr": "hour", "hrs": "hour",
              "second": "second", "seconds": "second", "sec": "second", "secs": "second",
              "minute": "minute", "minutes": "minute", "min": "minute", "mins": "minute",
              "day": "day", "days": "day", "week": "week", "weeks": "week"}
_NUMERAL = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
            "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
_DENOMINATOR = {"half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4,
                "fifth": 5, "fifths": 5, "sixth": 6, "sixths": 6, "eighth": 8, "eighths": 8,
                "tenth": 10, "tenths": 10, "twelfth": 12, "twelfths": 12, "twentieth": 20,
                "twentieths": 20, "twenty-fourth": 24, "twenty-fourths": 24}
# A quarter of an hour, three quarters of a day, 0.75 of an hour, .25 of an hour, 3/4 of an hour.
_A_FRACTION = (r"(?:(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d+)"
               r"[\s-]+(?:halves?|thirds?|quarters?|fifths?|sixths?|eighths?|tenths?|twelfths?"
               r"|twentieths?|twenty[\s-]fourths?)"
               r"|half|\d+\s*/\s*\d+|\d*\.\d+)")
_A_TIME_SHARE = re.compile(
    r"(?<![\w.])(?P<word>" + _A_FRACTION + r")\s*(?:of\s+)?(?:an?\s+|one\s+)?"
    r"(?P<unit>hours?|hrs?|minutes?|mins?|days?|weeks?)\b")
# "an hour and a half", "an hour and 20 minutes", "two and a half hours"
_A_MIXED_SPAN = re.compile(
    r"\b(?P<whole>a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s+"
    r"(?P<unit>hours?|hrs?|days?|weeks?)\s+(?:and\s+)?"
    r"(?P<rest>a\s+half|half|(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"fifteen|twenty|thirty|forty|forty five|fifty)\s+(?P<small>minutes?|mins?))\b")
# "half of an hour and a half", "a quarter of an hour and a half": a fraction of a span that is
# itself mixed, so the fraction is of the whole ninety minutes and not of the hour in it.
_A_FRACTION_OF_A_MIXED = re.compile(
    r"(?<![\w.])(?P<word>" + _A_FRACTION + r")\s*(?:of|out\s+of)\s+(?P<span>.+)$")
_A_HALF_SPAN = re.compile(
    r"\b(?P<whole>a|an|one|two|three|four|five|\d+)\s+and\s+a\s+half\s+"
    r"(?P<unit>hours?|hrs?|days?)\b")
# "what fraction of an hour is 20 minutes", "what fraction of a day is an hour"
_A_FRACTION_OF = re.compile(
    r"\b(?:what|which|how\s+much)\s+(?:a\s+)?fraction\s+of\s+(?:an?\s+|one\s+)?"
    r"(?P<unit>hour|day|week|minute)\s+(?:is|of)\s+"
    r"(?P<amount>\d+(?:\.\d+)?|a|an|one)\s*(?P<small>minutes?|mins?|hours?|hrs?|"
    r"seconds?|secs?|days?)\b")
_A_FRACTION_AS = re.compile(
    r"\b(?P<amount>\d+(?:\.\d+)?|a|an|one)\s*"
    r"(?P<small>minutes?|mins?|hours?|hrs?|seconds?|secs?|days?)\s+(?:as\s+)?(?:a\s+)?"
    r"fraction\s+of\s+(?:an?\s+|one\s+)?(?P<unit>hour|day|week|minute)\b")
_A_SPAN_ASK = re.compile(r"\b(?:what\s+is|whats|what's|how\s+much|how\s+many|how\s+long|"
                         r"how\s+big)\b")
# "what fraction of an hour is 20 minutes" asks with the bare "what", and the fraction-of-a-unit
# branch is specific enough to take it. The plain "a quarter of an hour" branch keeps the stricter
# ask, so "what can i make with half an hour" stays a cooking question.
_A_FRACTION_ASK = re.compile(r"\b(?:what(?:s|'s)?|which|how\s+much|how\s+many)\b")
_A_TARGET_UNIT = re.compile(
    r"\b(?:in|to|into)\s+(?:minutes?|mins?|seconds?|secs?|hours?|hrs?|days?|weeks?)\b")
# The unit the answer has to be in, when the line names one: "how many seconds in a quarter of
# an hour" is 900 seconds, and answering it in minutes answers a different question.
_A_UNIT_ASKED = re.compile(
    r"\b(?:how\s+many|how\s+much|in|to|into)\s+(?:a\s+|an\s+|one\s+)?"
    r"(minutes?|mins?|seconds?|secs?|hours?|hrs?|days?|weeks?)\b")
_TIME_SECONDS = {"second": 1, "minute": 60, "hour": 3600, "day": 86400, "week": 604800}
_TIME_PLURAL = {"second": "seconds", "minute": "minutes", "hour": "hours", "day": "days",
                "week": "weeks"}


def _a_fraction_value(word):
    """What a fraction word is worth: "a quarter" 0.25, "three quarters" 0.75, ".75" 0.75."""
    word = " ".join(str(word).replace("-", " ").split()).lower()
    slash = re.fullmatch(r"(\d+)\s*/\s*(\d+)", word.replace(" ", ""))
    if slash and int(slash.group(2)):
        value = int(slash.group(1)) / int(slash.group(2))
        return value if value < 1 else None
    if re.fullmatch(r"\d*\.\d+", word):
        value = float(word)
        return value if value < 1 else None
    parts = word.split()
    if parts == ["half"]:
        return 0.5
    if len(parts) == 2:
        numeral = _NUMERAL.get(parts[0])
        if numeral is None and parts[0].isdigit():
            numeral = int(parts[0])
        denominator = _DENOMINATOR.get(parts[1])
        if numeral and denominator:
            value = numeral / denominator
            return value if value < 1 else None
    return None


def _a_fraction_name(value):
    """The name a person gives a fraction: 1/3 is "a third", 3/4 "three quarters"."""
    name = _share_name(value)
    if name:
        return name
    for numerator, denominator, said in ((1, 7, "a seventh"), (1, 9, "a ninth"),
                                         (2, 7, "two sevenths"), (1, 10, "a tenth"),
                                         (1, 12, "a twelfth"), (1, 24, "a twenty-fourth"),
                                         (5, 6, "five sixths"),
                                         (5, 8, "five eighths"), (3, 8, "three eighths"),
                                         (7, 8, "seven eighths"), (1, 20, "a twentieth")):
        if abs(value - numerator / denominator) < 0.001:
            return said
    return None


def _a_span_amount(amount, name):
    """15 minutes, one minute, 7 and a half minutes."""
    if abs(amount - round(amount)) < 0.0001:
        whole = int(round(amount))
        return f"{whole:,} {name}" if whole != 1 else f"one {name[:-1]}"
    if abs((amount % 1) - 0.5) < 0.0001:
        return f"{int(amount)} and a half {name}"
    return f"{amount:g} {name}"


def _a_number_word(number):
    """Two, three, four: the way a span of time is said out loud."""
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
             8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
    return words.get(int(number), f"{int(number)}")


def _a_share_of_a_unit(value, unit):
    """A quarter of an hour, half an hour, an hour and a half, two and a half hours."""
    article = _TIME_ARTICLE[unit]
    plural = article.split()[-1] + "s"
    if abs(value - 0.5) < 0.0001:
        return f"Half {article}"
    if value > 1 - 0.0001:
        whole = int(value)
        rest = round(value - whole, 4)
        if abs(rest) < 0.0001:
            if whole == 1:
                return article[0].upper() + article[1:]
            return f"{_a_number_word(whole)} {plural}"
        if abs(rest - 0.5) < 0.0001:
            if whole == 1:
                return f"{article[0].upper()}{article[1:]} and a half"
            return f"{_a_number_word(whole)} and a half {plural}"
        if whole == 1:
            # "an hour and a quarter", not "an hour and a quarter of an hour"
            rest_name = _a_fraction_name(rest) or f"{rest:g}"
            return f"{article[0].upper()}{article[1:]} and {rest_name}"
        return f"{_a_number_word(whole)} {plural} and {_a_share_of_a_unit(rest, unit).lower()}"
    name = _a_fraction_name(value) or f"{value:g}"
    if name.startswith("a "):
        return f"A {name[2:]} of {article}"
    if name.startswith("an "):
        return f"An {name[3:]} of {article}"
    return f"{name[0].upper()}{name[1:]} of {article}"


def _a_fraction_of_a_time_unit(clean):
    """The fraction one span is of another: 20 minutes is a third of an hour."""
    for pattern in (_A_FRACTION_OF, _A_FRACTION_AS):
        match = pattern.search(clean)
        if not match:
            continue
        unit = match.group("unit")
        small = _TIME_UNIT.get(match.group("small"))
        amount = match.group("amount")
        count = _NUMERAL.get(amount)
        if count is None and re.fullmatch(r"\d+(?:\.\d+)?", amount):
            count = float(amount)
        per_small = {"hour": {"minute": 60}, "day": {"hour": 24}, "week": {"day": 7},
                     "minute": {"second": 60}}.get(unit, {}).get(small)
        if not count or not per_small:
            continue
        plural = {"minute": "minutes", "hour": "hours", "second": "seconds",
                  "day": "days"}[small]
        said = _a_span_amount(count, plural)
        name = _a_fraction_name(count / per_small)
        if not name:
            # not a fraction anyone says out loud - 22 minutes of an hour - so give the share as
            # a percentage rather than leave the person with nothing
            percent = round(100 * count / per_small)
            return f"{said[0].upper()}{said[1:]} is about {percent}% of {_TIME_ARTICLE[unit]}."
        return f"{said[0].upper()}{said[1:]} is {name} of {_TIME_ARTICLE[unit]}."
    return None


# A whole unit asked on its own is one step down: "how long is an hour" is 60 minutes. The line
# has to be nothing but the ask and the unit, so an hour that is part of a question about
# something else - a rate, a film, a dinner - is left to the row that knows about it.
_A_WHOLE_UNIT = re.compile(
    r"^\s*(?:how\s+long\s+is|how\s+long's|what\s+is|what's|whats)\s+"
    r"(?:an?|one|1)\s+(?P<unit>hours?|days?|weeks?|minutes?)\s*$")


def _the_span_said(span_seconds, unit, clean):
    """The span in the unit the line asked for, or in the next unit down."""
    factor, name = _TIME_SMALLER[unit]
    asked = _A_UNIT_ASKED.search(clean)
    if asked:
        wanted = _TIME_UNIT.get(asked.group(1))
        if wanted and _TIME_SECONDS[wanted] < _TIME_SECONDS[unit]:
            return _a_span_amount(span_seconds / _TIME_SECONDS[wanted], _TIME_PLURAL[wanted])
    return _a_span_amount(span_seconds / (_TIME_SECONDS[unit] / factor), name)


def _a_mixed_parts(match):
    """The whole hours, the leftover as a share of one, and the unit, of a mixed span."""
    unit = _TIME_UNIT[match.group("unit")]
    whole = _NUMERAL.get(match.group("whole"))
    if whole is None:
        whole = float(match.group("whole"))
    if "rest" not in match.groupdict() or match.group("rest").strip() in ("a half", "half"):
        return unit, whole, 0.5
    said_n = _NUMERAL.get(match.group("n"))
    return unit, whole, (said_n if said_n is not None else float(match.group("n"))) / 60


def _a_span_of_time(clean):
    """The span of time the line asks for, in the smaller unit, or the fraction of the unit."""
    if not isinstance(clean, str) or not clean or len(clean) > 200:
        return None
    asks = _A_SPAN_ASK.search(clean)
    target = _A_TARGET_UNIT.search(clean)
    if (not asks and not target and not _A_FRACTION_ASK.search(clean)
            and not _A_FRACTION_AS.search(clean)):
        return None
    # the fraction one span is of another: "what fraction of an hour is 20 minutes"
    if re.search(r"\bfractions?\b", clean):
        said = _a_fraction_of_a_time_unit(clean)
        if said:
            return said
    # a mixed span: "an hour and a half" is 90 minutes, "an hour and 20 minutes" is 80
    # a fraction of a mixed span: "half of an hour and a half" is forty-five minutes, not the
    # ninety the mixed branch would say, and not an hour and a half either
    share = _A_FRACTION_OF_A_MIXED.search(clean)
    if share:
        late = _A_MIXED_SPAN.search(share.group("span")) or _A_HALF_SPAN.search(share.group("span"))
        value = _a_fraction_value(share.group("word"))
        if late and value:
            late_unit, late_whole, late_extra = _a_mixed_parts(late)
            part = (late_whole + late_extra) * value
            return (f"{_a_share_of_a_unit(part, late_unit)} is "
                    f"{_the_span_said(part * _TIME_SECONDS[late_unit], late_unit, clean)}.")
    mixed = _A_MIXED_SPAN.search(clean)
    half_first = _A_HALF_SPAN.search(clean) if not mixed else None
    if mixed or half_first:
        unit, whole, extra = _a_mixed_parts(mixed or half_first)
        if abs(extra - 0.5) < 0.0001:
            said = _a_share_of_a_unit(whole + 0.5, unit)
        else:
            # "an hour and 20 minutes", not "an hour and a third of an hour": the leftover is a
            # count of the smaller unit, which is how the person said it
            plural = _TIME_ARTICLE[unit].split()[-1] + "s"
            head = (_TIME_ARTICLE[unit][0].upper() + _TIME_ARTICLE[unit][1:] if whole == 1
                    else f"{_a_number_word(whole)} {plural}")
            said = f"{head} and {_a_span_amount(extra * 60, 'minutes')}"
        said = said[0].upper() + said[1:]
        return f"{said} is {_the_span_said((whole + extra) * _TIME_SECONDS[unit], unit, clean)}."
    if target:
        return None  # a conversion to a named unit, which the table answers in its own words
    if not asks:
        return None
    whole = _A_WHOLE_UNIT.match(clean)
    if whole:
        unit = _TIME_UNIT[whole.group("unit")]
        return f"{_a_share_of_a_unit(1, unit)} is {_the_span_said(_TIME_SECONDS[unit], unit, clean)}."
    # a fraction of a unit asked on its own: "what is a quarter of an hour"
    match = _A_TIME_SHARE.search(clean)
    if not match:
        return None
    unit = _TIME_UNIT[match.group("unit")]
    value = _a_fraction_value(match.group("word"))
    if not value:
        return None
    if re.match(r"\s*and\s+a\s+half\b", clean[match.end():match.end() + 14]):
        value += 0.5  # "half of an hour and a half" is the half of ninety minutes
    return (f"{_a_share_of_a_unit(value, unit)} is "
            f"{_the_span_said(value * _TIME_SECONDS[unit], unit, clean)}.")


# --- "and half of that", after a fraction of a cup ------------------------
# The kitchen follow-up: "what is a third of a cup" and then "and half of that". The line names
# no measure of its own, so the table had nothing to answer it with and the turn was a "say more
# if it helps". The measure is in the turn before, so the two are read together.
_SHARE_THAT = re.compile(
    r"\b(?P<word>three[\s-]quarters?|two[\s-]thirds?|one[\s-](?:third|quarter|half)|"
    r"a[\s-](?:third|quarter|half|fifth|sixth)|half)\s+(?:of\s+)?(?:that|it|the same)\b")
_SHARE_LEAD = re.compile(r"^(?:and|so|then|ok|okay|what|how|about|much|is|whats|what's)\b")


def _share_carried(clean, memory):
    """A fraction of the measure the last turn was about: "and half of that"."""
    match = _SHARE_THAT.search(clean)
    if not match:
        return None
    rest = clean[:match.start()] + " " + clean[match.end():]
    rest = rest.strip(" ?.!,andso")
    while _SHARE_LEAD.match(rest):
        rest = _SHARE_LEAD.sub("", rest).strip(" ?.!,andso")
    if rest:  # a question with a subject of its own is not this follow-up
        return None
    for turn in reversed(list((memory or {}).get("turns") or [])[-4:]):
        line = str(turn.get("user") or "").strip().lower()
        share = _SHARE.search(line)
        if not share:
            if line:
                return None
            continue
        said = " ".join(match.group("word").split())
        # the turn before already gave the spoons-and-millilitres advice, so this one doesn't
        return _share_of_a_measure("what is " + said + " of " + line[share.start():], tail=False)
    return None


def convert(clean, memory=None):
    """A converted measure as a sentence, or None when the line is not a conversion."""
    reply = _answer(clean, memory)
    if reply:
        return reply
    if memory:
        return (_share_carried(clean, memory) or _carried_weight(clean, memory)
                or _carried_measure(clean, memory)
                or _carried_people(clean, memory))
    return None


# A weight of food on its own says nothing to a cook: "500g of mince" is three portions to one
# person and a week of dinners to another. The portion table above already holds the allowance for
# every food it knows, so a weight the line names is divided by it. Only a line that is asking
# about the food - a portion word, a headcount, or somebody saying what they have bought - is
# answered, so "i bought 2 pounds of mince" still goes where it went before.
_WEIGHT_SAID = re.compile(r"\b(\d+(?:\.\d+)?)\s*(kg|kilo|kilos|kilogram|kilograms|g|gram|"
                          r"grams|gramme|grammes)\b")
# "How long do I have to defrost 500g of mince" is a clock ask, but the "i have" in it is the
# obligation ("have to"), not the amount in hand. The portions table only owns a line that says
# what the person has got, so an "i have to" is not a portion ask: it is the recipe's own time.
_PORTIONS_ASK = re.compile(
    r"\bportions?\b|\bservings?\b|\bserves?\b|\bfeed(?:s|ing)?\b|\benough for\b|"
    r"\bi need\b|\bi've got\b|\bi have\b(?!\s+to\b)|\bi bought\b|\bhow many\b|\bfor how many\b")


_A_COUNT = re.compile(r"\b(\d+)\s+(?:\w+\s+){0,2}?"
                      r"(?P<food>[a-z][a-z' ]*)\b")


def _count_in_a_line(clean):
    """How many portions a counted number of pieces makes: "6 eggs", "12 sausages"."""
    if not _PORTIONS_ASK.search(clean):
        return None
    best = None
    for names, amount, kind, noun in PER_PERSON:
        if kind != "each" or not amount:
            continue
        for name in names:
            found = re.search(rf"\b(\d+)\s+(?:[a-z]+\s+)?{re.escape(name)}(?![\w])", clean)
            if found and (best is None or len(name) > len(best[0])):
                best = (name, int(found.group(1)), amount, noun)
    if not best:
        return None
    _name, count, amount, noun = best
    if count <= 0 or count > 200:
        return None
    portions = count / amount
    halves = round(portions * 2) / 2
    piece = noun if noun.endswith("s") or " " in noun else noun + "s"
    each = "one" if amount == 1 else f"{amount:g}"
    if halves <= 1:
        return (f"{count} {piece} is about one portion: {each} a person is the usual "
                f"allowance.")
    return (f"{count} {piece} is about {halves:g} portions: {each} a person is the usual "
            f"allowance.")


def _portions_in_a_weight(clean):
    """How many people a stated weight of a known food feeds."""
    if not isinstance(clean, str) or not clean:
        return None
    match = _WEIGHT_SAID.search(clean)
    if not match:
        # A count of something the portion table counts in pieces: "i need 6 eggs" is three
        # portions, and it was answered with the goal question the same way a weight was.
        counted = _count_in_a_line(clean)
        if counted:
            return counted
    if match:
        grams = float(match.group(1))
        unit = match.group(2).lower()
    else:
        # "how many portions in a kilo of mince" names no figure, and half a kilo is a figure
        bare = re.search(r"\b(half\s+)?(?:a|an|one)?\s*(kg|kilo|kilos|kilogram|kilograms|"
                         r"gram|grams|gramme|grammes)\b", clean)
        if not bare:
            return None
        grams = 0.5 if bare.group(1) else 1.0
        unit = bare.group(2).lower()
    if unit.startswith(("k", "kilo")):
        grams *= 1000
    if grams < 20 or grams > 20000:
        return None
    # the question has to be about the food, not just carry a number
    if not _PORTIONS_ASK.search(clean):
        return None
    # "how much mince per person" and "how many portions for 8 people" are the portion row's own
    # question, and it sums the headcount the person gave
    if _PORTION_WORD.search(clean) and _PEOPLE_WORD.search(clean):
        return None
    best = None
    for names, amount, kind, noun in PER_PERSON:
        if kind != "g" or not amount:
            continue
        for name in names:
            if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", clean):
                if best is None or len(name) > len(best[0]):
                    best = (name, amount, noun)
    if not best:
        return None
    _name, amount, noun = best
    # said the way the person said it: "1.5 kg of potatoes", never "1500 g of potatoes"
    weight = f"{grams / 1000:g} kg" \
        if unit.startswith(("k", "kilo")) and grams >= 1000 else f"{grams:g} g"
    portions = grams / amount
    if portions < 0.75:
        return (f"{weight} of {noun} is not a full portion on its own: allow about "
                f"{amount:g} g a person.")
    # round to the half portion people actually buy to
    halves = round(portions * 2) / 2
    said = f"{halves:g}".replace(".5", " and a half")
    if halves <= 1:
        return (f"{weight} of {noun} is about one portion: the usual allowance is "
                f"{amount:g} g a person.")
    return (f"{weight} of {noun} is about {said} portions: the usual allowance is "
            f"{amount:g} g a person, so it feeds {said}.")


# --- how many people one whole bird or joint feeds ---------------------------------------
#
# "is one chicken enough for 8" and "how many people does a chicken feed" are the question a
# person asks in the shop, and every one of them was a punt - while "does one chicken feed
# four" reached the hen-keeping card, which answers with layers pellets. A whole bird is one
# fixed size, so what it feeds is a fact worth having: the table holds the bird, the leg and
# the joint with the people one of them feeds, and the line's own headcount decides whether
# the answer is "yes, one", "yes with the sides" or "cook two". A weight in the line scales
# it, because half a kilo a person on the bone is the shop's own figure.
WHOLE_THING_SERVES = (
    # the names the line uses, the size one comes in, the people it feeds, how far it stretches,
    # what to cook instead for a bigger table, the grams a person, how to say that allowance, and
    # what is left on the frame once the roast is carved
    (("chicken", "chickens"), "about 1.8 to 2kg", 4, 6,
     "two 1.5 to 1.8kg birds rather than one big one: they cook evenly and fit a normal tin",
     500, "500g a person on the bone", ", and the picked frame gives another two meals' worth"),
    (("duck", "ducks"), "about 2kg", 4, None, "two birds", 500, "500g a person on the bone", ""),
    (("leg of lamb", "lamb leg", "leg of mutton"), "about 2kg", 6, 8,
     "a leg and a shoulder", 300, "300g a person on the bone", ""),
    (("shoulder of lamb", "lamb shoulder"), "about 1.75kg", 6, 8,
     "a shoulder and a leg", 250, "250g a person on the bone", ""),
    (("gammon joint", "ham joint", "gammon", "whole ham"), "about 1.5kg", 8, 10,
     "two 1kg joints, or a bigger one for sandwiches after", 200, "200g a person",
     ", and the end of it sandwiches the week"),
    (("whole salmon", "side of salmon"), "about 1.5kg", 8, None,
     "two sides, or a side and a couple of fillets", 180, "180g a person", ""),
)
# A cut of the same animal is a different question with the same word in it, and it is the
# portion row's: "is one chicken breast enough for two" and "is one leg of lamb enough" are
# not a whole bird, and the weight of one is not what this table holds.
_A_CUT_NOT_A_BIRD = re.compile(
    r"\b(?:breasts?|thighs?|wings?|drumsticks?|fillets?|nuggets?|strips?|tenders?|mince|"
    r"sausages?|joints?\s+of\s+meat|chops?|steaks?)\b")
# The ask: a table of people, or the question of how many one does.
_FEEDS_ASK = re.compile(
    r"\benough\b|\bfeed(?:s|ing)?\b|\bserves?\b|\bgo(?:es)?\s+round\b|\bhow\s+far\b|"
    r"\bdo\s+for\b|\bhow\s+many\s+(?:people|persons?|of\s+us|adults?|guests?)\b")
# The same words in a question about cooking it, keeping it, what it costs or what is in it.
_NOT_A_TABLE_QUESTION = re.compile(
    r"\b(?:how long|how do i|how to|temperature|oven|roast it|bake|reheat|fridge|freezer|"
    r"freeze|keep|keeps|lasts?|calories|kcal|protein|carbs?|fat|healthy|cost|costs|price|"
    r"cheap|expensive|buy|shopping|shopping list|defrost|thaw|stuffing|recipe|meals?)\b")
# Keeping hens is the other question with "chicken" in it, and it must not be answered with
# the weight of a dinner.
_KEEPING_HENS = re.compile(
    r"\b(?:hens?|coop|run|pellets|layers?|laying|eggs?|broody|cockerel|chicks?|"
    r"feed my|keeping chickens?)\b")
_WHOLE_WEIGHT = re.compile(r"\b(\d+(?:\.\d+)?)\s*(kg|kilo|kilos|kilogram|kilograms)\b")


_PLURAL_BIRDS = "|".join(
    name for names, *_rest in WHOLE_THING_SERVES for name in names if name.endswith("s"))
# "two chickens for 8" and "how many chickens for 20" are the same sum as one bird for a table,
# done the other way round: what one weighs against what the table needs. The count in front of
# the plural is the number being asked about, and "how many" is the number to find.
# the headcounts past twelve, said as words: a shop answer reads "for fourteen" not "for 14"
_PEOPLE_WORD_TO_TWENTY = {13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
                          17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}


def _a_table_word(count):
    """The number of people as words, as far as the table's own words go."""
    return _SAID_PEOPLE.get(count) or _PEOPLE_WORD_TO_TWENTY.get(count) or str(count)


_COUNT_OF_BIRDS = re.compile(
    r"\b(how many|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\d{1,2})\s+"
    r"(?:whole\s+)?(" + _PLURAL_BIRDS + r")\b")


def _birds_for_a_table(clean):
    """How many whole birds a table needs, or whether the number in the line covers it.

    "how many chickens for 20 people" was a punt and "do i need two chickens for 8" was a hedge.
    Both are one sum with the bird's own weight in it, so they are answered by the same row that
    says what one feeds.
    """
    if not isinstance(clean, str) or not clean or len(clean) > 200:
        return None
    found = _COUNT_OF_BIRDS.search(clean)
    if not found:
        return None
    if _NOT_A_TABLE_QUESTION.search(clean) or _KEEPING_HENS.search(clean):
        return None
    wanted = _people_asked(clean)
    if wanted is None:
        return None
    word, name = found.group(1), found.group(2)
    for names, size, feeds, stretch, more, grams_each, allowance, keeps in WHOLE_THING_SERVES:
        if name in names:
            break
    else:
        return None
    meat = names[0]  # the singular, for "10kg of chicken"
    one = grams_each * feeds  # what one of them weighs, from the people it feeds
    said = _a_table_word(wanted)
    needs = -(-wanted * grams_each // one)  # whole birds, rounded up
    if word == "how many":
        kilos = wanted * grams_each / 1000.0
        if needs == 1:
            return (f"For {said} people you want about {kilos:g}kg of {meat} on the bone, and one "
                    f"bird of {size} is enough.")
        return (f"For {said} people you want about {kilos:g}kg of {meat} on the bone: "
                f"{_a_table_word(needs)} birds of {size} each.")
    have = _people_in_a_count(word)
    if not have or have < 2:
        return None
    feeds_had = int(have * one // grams_each)
    many = _a_table_word(have)
    had = "is" if have == 1 else "are"
    kilos = have * one / 1000.0
    if feeds_had == wanted:
        return (f"{many.capitalize()} {name} {had} about {kilos:g}kg on the bone, which is exactly "
                f"enough for {said}.")
    if feeds_had > wanted:
        return (f"{many.capitalize()} {name} {had} about {kilos:g}kg on the bone, enough for "
                f"{_SAID_PEOPLE.get(feeds_had, str(feeds_had))} - so yes for {said}.")
    return (f"{many.capitalize()} {name} feed about "
            f"{_SAID_PEOPLE.get(feeds_had, str(feeds_had))}, so {said} wants "
            f"{_SAID_PEOPLE.get(needs, str(needs))} birds.")


def _people_in_a_count(word):
    """The number a word or a figure says, or None."""
    if not word:
        return None
    if word.isdigit():
        return int(word)
    return _PEOPLE_VALUE.get(word)


def _a_whole_thing_feeds(clean, memory=None):
    """How many people one whole bird, leg or joint feeds.

    "is one chicken enough for 8" was a punt on main, and "does one chicken feed four" was
    the hen-keeping card. One bird is one size, so the answer is a fact with the line's own
    headcount turned into a yes, a yes-with-sides or a "cook two".
    """
    if not isinstance(clean, str) or not clean or len(clean) > 200:
        return None
    if not _FEEDS_ASK.search(clean):
        return None
    if _NOT_A_TABLE_QUESTION.search(clean) or _KEEPING_HENS.search(clean):
        return None
    if _A_CUT_NOT_A_BIRD.search(clean):
        return None
    best = None
    for names, size, feeds, stretch, more, grams_each, allowance, keeps in WHOLE_THING_SERVES:
        for name in names:
            # "one chicken" and "a whole chicken" are one bird; the bare word is not, because
            # "how much chicken for 8 people" is the portion row's question about the meat.
            found = re.search(
                r"\b(?:one|1|a|an|the|single)\s+(?:whole\s+)?(?:\d+(?:\.\d+)?\s*kg\s+)?"
                + re.escape(name) + r"\b"
                r"|\bwhole\s+(?:\d+(?:\.\d+)?\s*kg\s+)?" + re.escape(name) + r"\b", clean)
            if found and (best is None or len(name) > len(best[0])):
                best = (name, size, feeds, stretch, more, grams_each, allowance, keeps)
    if not best:
        return None
    name, size, feeds, stretch, more, grams_each, allowance, keeps = best
    noun = "an " + name if name[0] in "aeiou" else "a " + name
    # A weight in the line is the size the person is actually holding: "is a 2kg chicken
    # enough for 6" is not the same bird as the one in the table, and the shop's half a kilo a
    # person on the bone turns the weight into people.
    weighed = _WHOLE_WEIGHT.search(clean)
    if weighed:
        kilos = float(weighed.group(1))
        grams = kilos * 1000
        feeds = max(1, round(grams / grams_each))
        size = f"{kilos:g}kg"
        stretch = round(feeds * 1.5) if stretch else None
    smaller = _SAID_PEOPLE.get(feeds, str(feeds))
    wanted = _people_asked(clean)
    if wanted is None:
        found = re.search(r"\b(?:feed|feeds|serve|serves|enough for)\s+(\d{1,2}|one|two|three|"
                          r"four|five|six|seven|eight|nine|ten|eleven|twelve)\b", clean)
        wanted = _people_in_a_count(found.group(1)) if found else None
    if wanted is None:
        stretched = f", {_SAID_PEOPLE.get(stretch, str(stretch))} at a stretch with plenty of " \
                   "sides" if stretch else ""
        # the ask is how many it feeds, and "how far does a bird go" is the same question with
        # the second meal implied, so what the frame gives is said here rather than left out
        return (f"One {name}, {size}, feeds {smaller} people{stretched}{keeps}. "
                f"A bigger table is {more}.")
    said = _SAID_PEOPLE.get(wanted, str(wanted))
    if wanted <= feeds:
        return (f"One {name}, {size}, feeds {smaller} people as a roast - so one is enough for "
                f"{said}. Allow {allowance} if you are buying another.")
    if stretch and wanted <= stretch:
        reached = _SAID_PEOPLE.get(stretch, str(stretch))
        return (f"One {name}, {size}, feeds {smaller} comfortably and {reached} at a stretch "
                f"with plenty of sides - so one is enough for {said} if you lay on the sides. "
                f"Otherwise {more}.")
    return (f"One {name}, {size}, feeds {smaller}, so for {said} you want {more}. "
            f"That is the {allowance} figure.")


def _answer(clean, memory=None):
    """The table's own answer to a line that carries its whole question."""
    if not isinstance(clean, str) or not clean or len(clean) > 200:
        return None
    whole = _a_whole_thing_feeds(clean, memory) or _birds_for_a_table(clean)
    if whole:
        return whole
    measured = _the_thing_measured_by_itself(clean)
    if measured:
        # the rewrite is the same question in the tables' own words; it carries no component
        # word before the measure, so it cannot come back through here
        return _answer(measured, memory)
    if _COMPONENT.search(clean) and not _the_component_is_the_whole_measure(clean):
        return None  # what is in a cup of tea is a nutrition question, not a measure one
    # "what is a third of a cup" names no unit to convert to, so there was nothing here to
    # answer it and the line went to a football row, whose key holds the word "cup", and to the
    # price row, whose key holds "how much is". A cook asking that wants the spoons and the
    # millilitres, which is what the smaller units in this table already say.
    share = _share_of_a_measure(clean)
    if share:
        return share
    # "what is a quarter of an hour": the span, the mixed span or the fraction of a unit, none of
    # which is money however much the line looks like "an hour" to the pay row
    span = _a_span_of_time(clean)
    if span:
        return span
    portions = _portions_in_a_weight(clean)
    if portions:
        return portions
    temperature = _oven(clean) or _temperature(clean) or _temperature_rule(clean)
    if temperature:
        return temperature
    butter = _butter(clean)
    if butter:
        return butter
    # "how many grams in a pack of mince for 4 people" asks what to buy for those four, which is
    # a portion with a headcount in it before it is the size of one pack. A number of people in
    # the line is tried as a portion first; a food with no portion figure still falls through to
    # the pack, because the size of the bag is the next best answer to what to buy.
    if _PEOPLE_COUNT.search(clean) or _PEOPLE_WORD.search(clean):
        dish = _a_dish_for_a_table(clean)
        if dish:
            return dish
        portion = _per_person(clean, memory)
        if portion:
            return portion
    pack = _pack(clean)
    if pack:
        return pack
    # "how many biscuits in a packet" is a count of pieces, not a weight: the packet is a
    # container of them, and the two weight tables say how many.
    counted = _pack_count(clean)
    if counted:
        return counted
    loose = _loose(clean)
    if loose:
        return loose
    weight = _object_weight(clean)
    if weight:
        return weight
    piece = _piece_weight(clean)
    if piece:
        return piece
    liquid = _liquid_weight(clean)
    if liquid:
        return liquid
    portion = _per_person(clean, memory)
    if portion:
        return portion
    # "5k" is a run, and a question about it is a question about kilometres.
    clean = _SAY_K.sub(r"\1 km", clean)
    clean = _frac(clean)
    clean = _JOINED.sub(" ", clean)
    handful = _handful(clean)
    if handful:
        return handful
    # A person saying their own height is a measurement with a second number in it, and saying
    # it in metres to a bot that answers in feet is the commonest way it arrives: "im 1.75
    # metres" reached the stock nod ("Thanks for telling me") and "im 175cm" only got the number
    # handed back ("Noted: you're 175cm"). So the line that states a height, without asking
    # anything, gets the other one back before the unit list is even read.
    own = _own_height(clean)
    if own:
        return own
    mentions = _mentions(clean)
    if not mentions:
        return None
    rule = _how_to_convert(clean, mentions)
    if rule:
        return rule
    height = _height(clean, mentions)
    if height:
        return height
    land = _land_size(clean, mentions)
    if land:
        return land

    measured = []
    for start, end, family, unit in mentions:
        value = _number_before(clean, start)
        if value is not None:
            measured.append((value, family, unit, end))

    weighed = _named_ingredient(clean, mentions, measured)
    if weighed:
        return weighed

    # "20 miles in km", "convert 200 g to oz": a measure, then the unit wanted.
    for value, family, unit, end in measured:
        rest = clean[end:]
        for match in _UNIT_WORD.finditer(rest):
            text = match.group(0)
            before = rest[:match.start()]
            if text == "in" or not (_TARGET.search(before)
                                    or re.search(r"how (?:many|much)\s+$", before)):
                continue
            family, unit, to_family, to_unit = _the_ounce_pair(
                family, unit, *_NAMES[text])
            if to_family != family or to_unit == unit:
                continue
            # The unit wanted ends the question: "how many hours is that in a week" names a
            # second measure, so the first pair is not what was asked.
            if _UNIT_WORD.search(rest[match.end():]):
                break
            return _sentence(value, family, unit, to_unit)

    # "how many grams in a pound": the unit wanted comes first, "a" counts as one.
    wanted_match = re.search(r"how (?:many|much)\s+(?P<want>[a-z/'’ ]+?)\s+"
                             r"(?:are there\s+)?(?:in|to|into|is|as)\s+(?P<rest>.+)$", clean)
    if wanted_match:
        want = _named_unit(wanted_match.group("want"))
        source = next(((value, family, unit, end) for value, family, unit, end in measured
                       if end > wanted_match.start("rest")), None)
        # The measure has to be the end of the question, or the line is about something
        # else that happens to name a measure ("how many days in a week should I run").
        if source and not _tail_is_about_the_measure(clean[source[3]:]):
            source = None
        if want and source:
            # "how many ounces in a pint" is a liquid measure; the same rule as everywhere else.
            # The source is often written without a number ("how many ml in an ounce"), so the
            # ounce is read here too rather than only the unit wanted.
            want_family, want_unit, source_family, source_unit = _the_ounce_pair(
                want[0], want[1], source[1], source[2])
            want = (want_family, want_unit)
            source = (source[0], source_family, source_unit, source[3])
        if want and source and want[0] == source[1] and want[1] != source[2]:
            if source[1] == "mass" and source[2] in ("cup", "tbsp", "tsp"):
                return _cup_of_something(clean)
            return _sentence(source[0], source[1], source[2], want[1], in_phrase=True)
        if want and source and want[1] in ("cup", "tbsp", "tsp", "dessertspoon") \
                and source[1] == "volume":
            return _cup_of_something(clean)
    # "how many grams in a cup": a cup of a dry thing is a weight question, not a volume one.
    if re.search(r"\b(cups?|mugs?|tablespoons?|tbsp|teaspoons?|tsp|"
                 r"dessertspoons?|dsp)\b", clean):
        return _cup_of_something(clean)
    return None


# A follow-up that names only the size wanted is the same measure question with a bigger cup:
# "how many grams in a dessertspoon of sugar" and then "and in a tablespoon". The turn before is
# the question, so this rebuilds it with the unit this line names and the table answers that.
# The ask can be said again too ("and how much for 20"), so the ask words are stripped with the
# joining ones, and a joining word can come at the end ("how much for 20 then").
_TRAILING_JOIN = re.compile(r"\s+(?:then|please)\s*$")
_CARRIED_LEAD = re.compile(
    r"^(?:and\s+(?:then\s+|what\s+about\s+|how\s+about\s+)?|what\s+about\s+|"
    r"how\s+about\s+|or\s+|then\s+|also\s+|how\s+much\s+|how\s+many\s+)")
_ASKED_MEASURE = re.compile(r"how\s+(?:many|much)\s+(?P<want>[a-z]+)")
# The words a follow-up may be made of: the unit, the food, and the grammar around them.
_CARRIED_FILLER = frozenset((
    "in", "to", "of", "a", "an", "the", "one", "and", "so", "what", "about", "how", "many",
    "much", "then", "big", "size", "is", "that", "it", "same", "for", "per", "please", "s",
    "gram", "grams", "g", "ml", "mls", "litre", "litres", "ounce", "ounces", "oz", "pound",
    "pounds", "lb", "lbs", "kilo", "kilos", "kilogram", "kilograms", "kg", "cup", "cups",
    "mug", "mugs", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons", "tsp",
    "dessertspoon", "dessertspoons", "dsp", "pint", "pints", "fl", "fluid"))


def _unit_words(text):
    """Every unit word a line names, in the order written."""
    return [(match.group(0), _NAMES[match.group(0)])
            for match in _UNIT_WORD.finditer(text)]


def _bare_measure(text):
    """The unit and food a bare measure phrase names, or None when it says anything more.

    A follow-up is the unit, the food and the grammar between them ("and in a tablespoon",
    "what about a cup of sugar"). A line with a verb or a subject of its own is a new question
    ("and how long does it keep?"), so it is not one.
    """
    text = _CARRIED_LEAD.sub("", str(text or "").strip().lower()).strip(" ?.!,")
    if not text or re.search(r"\d", text):
        return None
    said = _unit_words(text)
    if not said:
        return None
    spare = set(text.replace(",", " ").split())
    spare -= _CARRIED_FILLER
    for word, _ in said:
        spare -= set(word.split())
    food = _food_named(text)
    if food:
        spare -= set(food[0].split())
    if spare:
        return None
    return said, food


def _previous_measure(memory):
    """The measure question the chat is still on, from the turns the memory keeps.

    A chain is the same question asked again ("... and in a tablespoon", "what about a cup"),
    so a bare measure phrase is walked past to reach the question it belongs to. A turn that is
    neither ends the chain: "i need to lose weight" followed by "in grams" is not a conversion.
    """
    for turn in reversed(list((memory or {}).get("turns") or [])[-4:]):
        line = str(turn.get("user") or "").strip().lower()
        if not line:
            return None
        if _answer(line):
            return line
        if _bare_measure(line) is None:
            return None
    return None


# A follow-up that names only a new headcount is the same portion question asked for more
# people: "how much gravy for 8 people" and then "and for 12". The count in the turn before is
# swapped for this one and the portion table answers that.
_CARRIED_PEOPLE = re.compile(
    r"^(?:for\s+)?(?P<count>\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve)(?:\s+(?:people|persons?|guests|adults|heads|of\s+us))?$")


# A count the person corrects - "oh sorry i meant 8 people not 6" - is the headcount the chat
# is on now, and the question that was answered for six wants answering again for eight.
_CORRECTION = re.compile(r"\b(?:i meant|i mean|sorry|actually|no wait|make that|"
                         r"on second thoughts|i said|not\s+\d)")


def _previous_portion(memory):
    """The last portion question in the chat, from the turns the memory keeps."""
    for turn in reversed(list((memory or {}).get("turns") or [])[-3:]):
        line = str(turn.get("user") or "").strip().lower()
        if not line:
            return None
        if _PEOPLE_COUNT.search(line) and _per_person(line):
            return line
        if _bare_measure(line) is None:
            return None  # the chat has moved on to something that is not a portion
    return None


def _carried_people(clean, memory):
    """The portion question the chat is still on, asked for a different number of people."""
    text = str(clean or "").strip().lower()
    if _CARRIED_NOW.match(text.strip(" ?.!,")):
        return _portion_after_correction(memory)
    # The joining words and the ask can both be there, in either order ("and how much for 20",
    # "how much for 20 then"), so they are peeled off one at a time rather than in one pattern.
    for _ in range(3):
        stripped = _TRAILING_JOIN.sub("", _CARRIED_LEAD.sub("", text)).strip(" ?.!,")
        if stripped == text.strip(" ?.!,"):
            break
        text = stripped
    text = text.strip(" ?.!,")
    match = _CARRIED_PEOPLE.match(text)
    if not match:
        return None
    previous = _previous_portion(memory)
    if not previous:
        return None
    found = _PEOPLE_COUNT.search(previous)
    if not found:
        return None
    old = next((group for group in found.groups() if group), None)
    if old is None:
        return None
    # Only the number changes: "for 8 people" becomes "for 12 people", so the food, the measure
    # and the wording of the question are the ones the chat already established.
    rebuilt = previous[:found.start()] + found.group(0).replace(old, match.group("count"), 1) \
        + previous[found.end():]
    return _answer(rebuilt)


# "make it 750g instead" is the portion question again with a different weight, and on main
# `054c0a0` it was answered "20 minutes." after "how much mince for 4 people" (the time row read
# the figure), and "what about 750g" with a shrug. The line names no food at all: the food and the
# headcount are in the turn before, so this only fires when the whole line is a new weight.
_NEW_WEIGHT_THEN = re.compile(
    r"^(?:and\s+|ok\s+|okay\s+|so\s+|but\s+)?(?:(?:can|could)\s+you\s+)?"
    r"(?:(?:make|change|do|set|use)\s+(?:it|that|them|this)\s+(?:to\s+|at\s+|as\s+)?"
    r"|what\s+about\s+|how\s+about\s+|and\s+)?"
    r"(?P<amount>(?:\d+(?:\.\d+)?)\s*(?:kg|kilo|kilos|kilogram|kilograms|g|gram|grams|"
    r"gramme|grammes)|half\s+a\s+(?:kilo|kg)|a\s+(?:kilo|kg)|one\s+(?:kilo|kg))"
    r"(?:\s+(?:instead|then|please|now|of\s+that))?$")


def _carried_weight(clean, memory):
    """The portion question the chat is still on, asked with a different weight."""
    text = " ".join(str(clean or "").lower().split()).strip(" ?.!,")
    match = _NEW_WEIGHT_THEN.match(text)
    if not match:
        return None
    previous = _previous_portion(memory)
    if not previous:
        return None
    found = re.search(r"\b(\d+(?:\.\d+)?)\s*(kg|kilo|kilos|kilogram|kilograms|g|gram|grams|"
                      r"gramme|grammes)\b", match.group("amount"))
    if found:
        grams = float(found.group(1))
        unit = found.group(2)
        if unit.startswith(("k", "kilo")):
            grams *= 1000
    else:
        grams = 500.0 if match.group("amount").startswith("half") else 1000.0
    best = None
    # both tables: rice and pasta have an allowance only when the line counts them, and
    # "make it 500g instead" after "how much rice for 8 people" found no allowance at all
    for names, amount, kind, noun in PER_PERSON + PER_PERSON_WHEN_COUNTED:
        if kind != "g" or not amount:
            continue
        for name in names:
            if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", previous):
                if best is None or len(name) > len(best[0]):
                    best = (name, amount, noun)
    if not best:
        return None
    _name, amount, noun = best
    weight = f"{grams:g} g" if grams < 1000 or "kg" not in match.group("amount") \
        else f"{grams / 1000:g} kg"
    portions = grams / amount
    people = _people_asked(previous)
    halves = round(portions * 2) / 2
    said = f"{halves:g}".replace(".5", " and a half")
    if people and abs(halves - people) < 0.75:
        return (f"{weight} of {noun} is about right for {people}: the usual allowance is "
                f"{amount:g} g a person.")
    if people:
        side = "a little more" if halves > people else "a little less"
        return (f"{weight} of {noun} is about {said} portions, {side} than the {people} you "
                f"asked about: the usual allowance is {amount:g} g a person.")
    if halves <= 1:
        return f"{weight} of {noun} is about one portion: the usual allowance is {amount:g} g a person."
    return (f"{weight} of {noun} is about {said} portions: the usual allowance is "
            f"{amount:g} g a person, so it feeds {said}.")
# "so how much now" says no food and no number: it points back at the question already asked
# and at the count just corrected, and the two together are the portion the person wants.
_CARRIED_NOW = re.compile(
    r"^(?:so |ok |okay |and |but |then )*(?:how much|how many|what about|and)"
    r"(?: of (?:it|that|them|those|these))?(?: now| then| again)?$")


def _names_a_portion_food(line):
    """True when the line names a food the portion table knows, so it is a portion question."""
    for names, _amount, _kind, _noun in PER_PERSON + PER_PERSON_WHEN_COUNTED:
        for name in names:
            if re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", line):
                return True
    return False


def _portion_after_correction(memory):
    """The portion question the chat was on, asked again for the count the person corrected.

    "how much mince do i need" answers for six, then "oh sorry i meant 8 people not 6" is the
    new headcount, and "so how much now" is the first question with the second number. The food
    comes from the question and the number from the correction, which is why this reads the
    turns rather than the line.
    """
    portion = None
    count = None
    for turn in reversed(list((memory or {}).get("turns") or [])[-4:]):
        line = " ".join(str(turn.get("user") or "").lower().split())
        if not line:
            break
        if portion is None and _AN_ASK.search(line) and _names_a_portion_food(line):
            portion = line
            break
        if portion is None and _CORRECTION.search(line):
            found = _people_asked(line)
            if found is not None:
                count = found
                continue
        break
    if portion is None or count is None:
        return None
    found = _PEOPLE_COUNT.search(portion)
    if not found:
        # the question named the food and left the number to the turn before it, which is the
        # number the correction has just changed
        return _answer(f"{portion} for {count} people")
    old = next((group for group in found.groups() if group), None)
    if old is None:
        return None
    rebuilt = portion[:found.start()] + found.group(0).replace(old, str(count), 1) \
        + portion[found.end():]
    return _answer(rebuilt)


def _carried_measure(clean, memory):
    """The measure question the turn before asked, asked again with this line's unit."""
    bare = _bare_measure(clean)
    if bare is None:
        return None
    said, food = bare
    previous = _previous_measure(memory)
    if not previous:
        return None
    want = _ASKED_MEASURE.search(previous)
    if not want:
        return None
    want_family = _named_unit(want.group("want"))
    unit_word, unit = said[-1]
    previous_units = _unit_words(previous)
    source = None
    for word, named in previous_units:
        if want_family is None or named[1] != want_family[1]:
            source = (word, named)
    if not food:
        food = _food_named(previous)
    of_food = (" of " + food[0]) if food else ""
    if want_family and unit[1] == want_family[1] and source:
        # "in grams" asks for the same spoon in the unit it names.
        rebuilt = f"how many {unit_word} in a {source[0]}{of_food}"
    else:
        rebuilt = f"how many {want.group('want')} in a {unit_word}{of_food}"
    return _answer(rebuilt)


_FRACTIONS = {0.25: "a quarter cup", 0.5: "half a cup", 0.75: "three quarters of a cup",
              1 / 3: "a third of a cup", 2 / 3: "two thirds of a cup",
              1.5: "one and a half cups", 2.5: "two and a half cups"}


def _a_or_an(word):
    """The article a word takes: "an hour", "a minute". Half an hour, not half a hour."""
    word = str(word)
    # "an hour" is the one unit here whose vowel is not written: the h is silent
    if word[:1].lower() in "aeiou" or word.lower().startswith("hour"):
        return "an " + word
    return "a " + word


def _amount_phrase(value, unit):
    """An amount as a cook says it: half a cup, three quarters of a cup, 200 grams."""
    if unit in _SHARE_OF_CUP:
        said = _cups_phrase(value, unit)
        if said != f"{_fmt(value)} {_say(value, unit, one=False)}":
            return said
    if value in (0.25, 0.5, 0.75) and unit in SAID_ONE:
        word = {0.25: "a quarter of", 0.5: "half", 0.75: "three quarters of"}[value]
        return f"{word} {_a_or_an(SAID_ONE[unit])}"
    return f"{_fmt(value)} {_say(value, unit)}"


def _cups_phrase(amount, unit, spoons=False):
    """A cup amount as a cook says it: half a cup, not 0.5 cups.

    Under half a cup and off the fractions, a cook weighing a food reaches for a spoon, not
    for a decimal: 50 g of flour is "about 6 1/2 tablespoons", and nobody measures 0.4 of a
    cup. A plain pair of units stays in cups, so "how many cups in a tablespoon"
    does not answer in teaspoons.
    """
    if unit == "cup":
        for value, said in _FRACTIONS.items():
            if abs(amount - value) < 0.06:
                return said
        if abs(amount - 1) < 0.06:
            return "1 cup"
        if spoons and 0 < amount < 0.5:
            spoons = amount * 16
            if spoons < 2:
                return f"{_spoons(spoons * 3)} teaspoons"
            if spoons < 10:
                return f"{_spoons(spoons)} tablespoons"
        if amount >= 0.1:
            amount = round(amount, 1)  # "about 0.6 cups", not 0.59
    return f"{_fmt(amount)} {_say(amount, unit, one=False)}"


def _spoons(count):
    """A number of spoons as a recipe says it: 4, 6, or 1 1/2 when half a spoon matters."""
    nearest = round(count * 2) / 2
    if nearest == int(nearest):
        return str(int(nearest))
    return f"{int(nearest)} 1/2"


# The questions only this table can answer in full: a food whose cup weight it knows, and
# an oven or a stick of butter, which no plain pair of units covers.
_SPECIFIC = re.compile(r"\b(gas mark|fan oven|fan|cooking|recipe|stick of butter|sticks? of butter)\b")


def answers_more_than_a_pair(clean):
    """True when the reply says more than how many of one unit make another.

    A plain pair ("how many grams in an ounce") may already have a hand-written fact with
    a second useful measure in it; a named food or an oven has no such fact and the table
    is the only place that knows the answer.
    """
    if not isinstance(clean, str):
        return False
    if _SPECIFIC.search(clean):
        return True
    return _food_named(clean) is not None


def _food_named(clean):
    """The food this line names, and what a cup of it weighs, the longest name winning.

    "brown sugar" and "sugar" are each a cup of something, and the longer name is the one
    meant, so the table can hold both without one swallowing the other.
    """
    best = None
    for name, grams in GRAMS_PER_CUP:
        if re.search(rf"\b{re.escape(name)}\b", clean):
            if best is None or len(name) > len(best[0]):
                best = (name, grams)
    return best


def _named_ingredient(clean, mentions, measured):
    """A cook's weight and cups of the same ingredient, converted either way.

    "how many cups is 200 g of flour" and "1.5 cups of flour in grams" both need the
    ingredient's weight per cup, which is the one thing a plain volume cannot give.
    """
    food = _food_named(clean)
    if not food:
        return None
    food_name, grams_per_cup = food
    said_food = AS_KITCHEN_SAYS.get(food_name, food_name)
    wanted = [unit for _, _, family, unit in mentions if unit in _SHARE_OF_CUP]
    if not wanted:
        return None
    for value, family, unit, _ in measured:
        if unit in _SHARE_OF_CUP:
            grams = value * grams_per_cup * _SHARE_OF_CUP[unit]
            source = _amount_phrase(value, unit) + f" of {said_food}"
            source = source[0].upper() + source[1:]
            wanted_mass = [u for _, _, fam, u in mentions if fam == "mass"]
            if not wanted_mass:
                continue
            target = wanted_mass[0]
            if target in _SHARE_OF_CUP:
                continue
            amount = grams / _factor("mass", target)
            said = _grams(amount) if target == "g" else _fmt(amount)
            return f"{source} is about {said} {SAID[target]}."
        if family == "mass":
            grams = value * _factor("mass", unit)
            target = wanted[0]
            amount = grams / (grams_per_cup * _SHARE_OF_CUP[target])
            source = _amount_phrase(value, unit) + f" of {said_food}"
            source = source[0].upper() + source[1:]
            return f"{source} is about {_cups_phrase(amount, target, spoons=True)}."
    return None


def _plural_of(name):
    """The words a cook counts more than one of: "onions", "cloves of garlic"."""
    head, _, tail = name.partition(" ")
    if head.endswith("y") and len(head) > 1 and head[-2] not in "aeiou":
        head = head[:-1] + "ies"
    elif head.endswith(("o", "ch", "sh", "s", "x")):
        head += "es"
    else:
        head += "s"
    return head + (" " + tail if tail else "")


def _a(name):
    """The piece with its article: "an egg", "a banana"."""
    return ("an " if name[0] in "aeiou" else "a ") + name


_SAID_COUNT = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}


def _counted_as(word):
    """How many the line counts: "an" is one, "half a" is a half, "a quarter of" a quarter."""
    word = " ".join(word.replace("-", " ").split())
    fractions = {"half": 0.5, "a half": 0.5, "quarter": 0.25, "a quarter": 0.25,
                 "three quarters": 0.75, "a third": 1 / 3, "two thirds": 2 / 3}
    if word in fractions:
        return fractions[word]
    whole_and_a_half = re.fullmatch(r"(one|two|three|four) and a half", word)
    if whole_and_a_half:
        return _SAID_WHOLE[whole_and_a_half.group(1)] + 0.5
    if re.fullmatch(r"\d+(?:\.\d+)?", word):
        return float(word) if "." in word else int(word)
    return _SAID_WHOLE[word]


def _piece_named(clean):
    """The piece this line counts, and what one of it weighs: (name, grams, count) or None.

    Only a counted piece is a piece. "how many grams of pepper" is a spoonful of pepper, not
    a pepper, so the word has to follow a count ("a pepper", "2 onions"); and a tin, a jar or
    a loaf is not the thing loose, so those lines are left alone.
    """
    if _UNCOUNTED.search(_WHOLE_THING.sub("", clean)):
        return None
    if _MEASURE_AFTER_PIECE.search(clean):
        return None
    best = None
    for name, grams in PIECE_GRAMS:
        for words in (name, _plural_of(name)):
            # After a counted piece only the weight question may follow: "an onion", "a banana
            # weigh", "2 onions in grams". "a banana bread" and "an apple pie" are a dish.
            match = re.search(rf"(?<![\w.]){re.escape(words)}(?![\w])"
                              r"(?=\s*(?:$|[,?]|of\b|weigh|weighs|weighed|about|in grams?|in g\b|to grams|is\b))",
                              clean)
            if not match:
                continue
            counted = _COUNT.search(clean[:match.start()])
            if not counted:
                continue
            if best is None or len(name) > len(best[0]):
                best = (name, grams, _counted_as(counted.group(1)))
    return best


def _piece_weight(clean):
    """What one of a food weighs, when the line counts pieces instead of naming a measure.

    "how many grams in an egg", "how much does an onion weigh", "2 onions in grams": the
    weight is the food's own, so it comes from the same kind of table as a cup's weight.
    A line that already converts a measure ("how many grams in a pound of bananas") is a
    conversion, and is left to the code below.
    """
    if not _asks_for_weight(clean):
        return None
    piece = _piece_named(clean)
    if not piece:
        return None
    for start, _end, _family, _unit in _mentions(clean):
        if _number_before(clean, start) is not None:
            return None
    name, grams, count = piece
    # A whole cabbage or squash is a kilo, and a shopper reads that as 1 kg, not 1,000 g.
    amount = _mass_of(grams * count)
    if count == 1:
        return f"{_a(name).capitalize()} is about {amount}."
    said, plural = _count_phrase(count)
    if not plural:
        return f"{said} {_a(name)} is about {amount}."
    return f"{said} {_plural_of(name)} weigh about {amount}."


def _count_phrase(count):
    """How the amount is said, and whether the food is plural: ("Half", False), ("Two", True)."""
    fractions = {0.25: "A quarter of", 1 / 3: "A third of", 0.5: "Half",
                 2 / 3: "Two thirds of", 0.75: "Three quarters of"}
    for share, said in fractions.items():
        if abs(count - share) < 0.01:
            return said, False
    if count != int(count):
        whole = int(count)
        word = "One" if whole == 1 else _SAID_COUNT.get(whole, _fmt(whole))
        return f"{word} and a half", True
    if count in _SAID_COUNT:
        return _SAID_COUNT[count], True
    return _fmt(count), True


def _named_unit(text):
    """The unit a short phrase names ("grams", "cups of flour"), or None."""
    best = None
    for match in _UNIT_WORD.finditer(text):
        if best is None or len(match.group(0)) > best[2]:
            best = _NAMES[match.group(0)] + (len(match.group(0)),)
    return (best[0], best[1]) if best else None
