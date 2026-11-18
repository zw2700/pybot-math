"""Cooking and food: everyday how-tos, timings, fixes and food safety.

The answers lane owns this domain. Everything here is data plus a few small functions:
one Entry per thing people ask about, keyed by the words that identify it (a dish, an
ingredient, a kitchen problem), and phrased the way a good cook would explain it. The
matcher in bot/knowledge/lookup.py finds the entry; bot/modules/answers.py answers.

Timings are for a home oven and say so; fan ovens run about 20C cooler in Celsius
terms, so the entries give both where it matters.

Two kinds of entry sit side by side: a technique ("how long do I boil potatoes") and a dish
("what can I make with potatoes and cheese"). The dish entries are keyed by the thing in the
fridge, so "half a cabbage", "a tin of chickpeas" and "bananas going brown" each reach a
recipe; the general "what shall I cook" entry keeps out of any line that names a food, because
the food's own entry answers it better.
"""
import re

from ..understanding import line_as_read
from .dishes import KEEP_QUALITY_WORDS, PLAN_NAMES
from .keeping_cooked import COOKED_KEEP_ASK, COOKED_KEEP_AVOID, COOKED_KEEPS
from .lookup import (entry, find, kinds_entries, says_it_has_gone_off as _says_it_has_gone_off,
                     TOOTH_OR_GUM)
from .meals import NOT_MINE_ENTRY as _NOT_MINE, says_a_diet as _says_a_diet
# The bake-fault dispatcher and its tables live in their own file: this one is on the
# uploader's size ceiling, and the entry below still reaches the same code.
from .bake_faults import (_BAKE_FAULT, _BAKE_FAULT_FAMILIES, _BAKE_THING,  # noqa: F401
                          _bake_always, _bake_fault)  # noqa: F401
from .prices import a_price_is_judged
from .units import BIRD_GRAMS, people_in_groups
from .cooking_tables import (NOT_WANTED, MEAL_IDEAS, SIDES, SEASONINGS, DIET_VARIANTS, FREEZE_FACTS, FOOD_CALORIES, FOOD_NUTRIENTS, FOOD_CALORIE_MEALS, BAKES, KEEPS, PANTRY, DISHES, RECIPES)  # noqa: F401  (the tables, so the rows below can read them)

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("cooking", "food-and-drink")

# Keeping entries only answer when the line is actually asking. "we keep pasta in the cupboard"
# and "i keep burning the bread" are things people tell you, not questions about storage; the
# shapes below are how the keeping question gets asked. Fridge, freezer and freeze are left out on
# purpose: "we keep our bread in the freezer" is a statement too.
# The small baked things people ask the same clock about. The name carries a table, not a list:
# the keep table further down stands aside on the words of this one, and that list is called
# BAKED_LINE_WORDS so a second BAKED_GOODS cannot quietly shadow this dict. A tray of brownies, a
# tin of biscuits, a batch of muffins: each is one row, because "how long do brownies keep" had no
# answer at all and a batch is the unit people think in. The first value is what to call one, the
# second is how long it keeps and where, the third is one sentence about the freezer.
BREAD_TIP = ("A slice of bread in the tin keeps them soft; 15 seconds in the microwave brings one "
             "back the next day.")
BAKED_GOODS = {
    "brownie": ("Brownies", "4 to 5 days in a sealed tin at room temperature",
                "They freeze for 3 months, cut into squares first.", BREAD_TIP),
    "blondie": ("Blondies", "4 to 5 days in a sealed tin", "They freeze for 3 months.", BREAD_TIP),
    "cookie": ("Cookies", "a week in an airtight tin",
               "The dough freezes for 3 months, shaped and ready to bake from frozen.", BREAD_TIP),
    "biscuit": ("Biscuits", "a week or two in a tin", "A baked tin freezes for 3 months.",
                BREAD_TIP),
    "muffin": ("Muffins", "2 to 3 days in a tin, best the day they are baked",
               "They freeze for 2 months.", BREAD_TIP),
    "flapjack": ("Flapjacks", "a week in a tin", "They freeze for 3 months.", BREAD_TIP),
    # A bought or homemade oat bar is the same traybake as a flapjack, and the keeping table's oats
    # row stands down for "oat bars": without a row here the keeping question fell through to the
    # porridge method and a person asking how long their oat bars keep got a recipe.
    "oat bar": ("Oat bars", "a week in a tin", "They freeze for 3 months.", BREAD_TIP),
    # the same fence stands the oats row down for "oat crackers", and a cracker keeps like the
    # biscuit it is rather than like the bag
    "oat cracker": ("Oat crackers", "a week or two in a tin",
                    "A baked tin freezes for 3 months.", BREAD_TIP),
    "cupcake": ("Cupcakes", "2 to 3 days in a tin, unfrosted",
                "They freeze for 2 months, unfrosted.", BREAD_TIP),
    "doughnut": ("Doughnuts", "only the day you buy them", "They do not freeze well.",
                 "Ten seconds in the microwave brings one back closer to fresh than you would "
                 "think."),
}
BAKED_GOODS_WORDS = ("oat bar", "oat bars", "oat cracker", "oat crackers", "brownie", "brownies", "blondie", "blondies",
                     "cookie", "cookies",
                     "biscuit", "biscuits", "muffin", "muffins", "flapjack", "flapjacks",
                     "cupcake", "cupcakes", "doughnut", "doughnuts", "donut", "donuts")


# The foods a jar holds, as against the glass: "a jar of jam" is the keeping question as well as
# the lid, so the lid answer says how long it keeps afterwards. A bare "jar" is not here, because
# an empty jar is only a jar. One list, read by the lid answer and by the follow-up below: two
# copies drifted apart once already, and the narrower one silently won.
CONTAINER_FOODS = ("jam", "pesto", "pickle", "pickles", "chutney", "marmalade", "ketchup",
                   "mustard", "mayonnaise", "mayo", "salsa", "tahini", "preserve", "preserves",
                   "olives", "gherkins", "relish")


# A jar of something keeps its own fridge life, and the lid question is what brings the jar into
# the conversation: after "how do i open a jar of jam" the line "how long does it last in the
# fridge" is about the jam. No keeping entry can be keyed on that line, because "it" names nothing
# until the turn before is read; so this entry is keyed on the shape of the question and reads the
# container from the last turn, and it stands aside (an empty reply) when no container was named,
# so the food named in the line or the general cooked-food answer has it instead.
# The jars that keep for months once opened, as against the sauces that want eating in a fortnight.
CONTAINER_MONTHS = ("jam", "pickle", "pickles", "chutney", "marmalade", "preserve", "preserves",
                    "olives", "gherkins", "relish", "mustard", "ketchup")


def _container_keep(memory, reading):
    """The keeping sentence for the container named a turn ago, or "" when none was named."""
    turns = (memory or {}).get("turns") or []
    for turn in reversed(turns[-2:]):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        named = [word for word in CONTAINER_FOODS if word in said]
        if named:
            food = named[0].capitalize()
            if named[0] in CONTAINER_MONTHS:
                # "olives keep", "jam keeps": the food names are plural as often as not
                keep = "keep" if food.endswith("s") else "keeps"
                return (f"{food} {keep} for months in the fridge once it is opened, and an opened "
                        "sauce or pesto 1 to 2 weeks. The label's once-opened line beats any "
                        "general rule, so bin it if it smells sharp or the lid bulges.")
            return (f"An opened {named[0]} is best within 1 to 2 weeks, kept in the fridge, and "
                    "the label's once-opened line beats any general rule. Bin it if it smells "
                    "sharp, looks odd or the lid bulges.")
    return ""


def _stuck_jar(memory, reading):
    """The lid answer, with the keeping sentence when the jar holds something worth keeping."""
    line = str((reading or {}).get("text") or (reading or {}).get("clean") or "").lower()
    said = ("Tap the edge of the lid all the way round with the handle of a knife, then grip it "
            "through a rubber glove, a silicone mat or a wide rubber band - the grip is usually "
            "what is missing. If it still will not turn, stand the jar in a bowl of hot water for "
            "two minutes so the metal lid swells, or slide the back of a spoon under the rim to "
            "let air in.")
    if any(word in line for word in CONTAINER_FOODS):
        said += " Once open, jam, pickles and chutney keep for months, an opened sauce 1 to 2 weeks."
    return said


def _baked_keep():
    """The keeping answer for the small baked things, from the row the line names."""
    def reply(memory, reading):
        line = str(reading.get("text") or reading.get("clean") or "").lower()
        for name in sorted(BAKED_GOODS, key=len, reverse=True):
            if name in line:
                label, keeps, frozen, tip = BAKED_GOODS[name]
                return f"{label} keep {keeps}. {frozen} {tip}"
        return ""
    return reply


KEEP_ASK = ("how", "what", "which", "can", "could", "should", "would", "where", "is", "are",
            "does", "do i", "will",
            "worth", "ok", "okay", "safe", "still", "long", "last", "lasts", "store", "storing",
            "stored", "leftover", "leftovers", "left over", "next day", "tomorrow", "reheat",
            "gone off", "go off", "goes off", "going off", "shelf life", "shelf-life")

# A lid that will not turn is a job on the lid, not a keeping question. The keeping key of a jar
# reads "jar" and "open", and "how" is in KEEP_ASK, so the fridge paragraph answered "how do i
# open a tight jar" and "cant get the lid off the jam". Every entry that names a container carries
# these words, so an opening line passes to the entry that turns the lid.
OPEN_ASK = ("open a tight", "open a stuck", "open a stubborn", "get the lid off",
            "get this lid off", "get the cap off", "lid is stuck", "lid stuck",
            "lid wont come off", "lid won't come off", "wont open", "won't open",
            "wont turn", "won't turn", "wont budge", "won't budge", "cant open", "can't open",
            "cannot open", "hard to open", "struggling to open", "stubborn lid", "tight lid",
            "stuck lid", "how do i open", "how to open", "how can i open")

# A fault only means something about cooking when the line is also about food: "too dry" on its own
# can be the weather, the washing or a cough. Every "it went wrong" entry below needs one of these
# words as well as its fault word.
_FOOD = ("sauce", "soup", "stew", "curry", "chilli", "casserole", "gravy", "dish", "dinner",
         "supper", "meal", "food", "cooked", "cook", "cooking", "taste", "tastes", "tasted",
         "made", "make", "fix", "fixing", "came out", "turned out", "went wrong",
         "chicken", "meat", "rice", "pasta", "cake", "bread", "pastry", "potatoes", "stir fry",
         "custard", "mash", "roast", "bake", "baking", "bolognese", "lasagne", "lasagna",
         "risotto", "pie", "cobbler", "traybake", "noodles", "eggs", "fish", "mince", "beef",
         "pork", "lamb", "vegetables", "veg", "pancakes", "porridge", "stock", "broth",
         "salt", "seasoning", "spices", "herbs", "pepper", "marinade", "dressing", "steak",
         "squid", "prawns", "bacon", "sausages", "turkey", "burgers",
         # The dish names the fault answers did not know, so "my ragu is too thin" and "my
         # meatballs are dry" were shrugs. One list, because every fault answer reads it: watery,
         # dry, bland, burnt, salty and hot all reach a dish named here.
         "ragu", "rag\u00f9", "bolognaise", "meatballs", "meatloaf", "tagine", "daal", "dhal",
         "biryani", "paella", "ratatouille", "goulash", "gnocchi", "hummus", "burrito", "katsu",
         "macaroni cheese", "mac and cheese", "waffles", "frittata", "ramen", "quesadilla",
         "cottage pie", "shepherds pie", "shepherd's pie", "fish pie", "quiche", "couscous",
         "pesto", "guacamole", "tapenade", "dip", "dips", "pilaf", "pilau",
         "burger", "hamburger", "falafel", "patty", "patties",
         # The trimmings and the batter: every fault answer reads this list, and without these
         # words "the parsnips burnt", "my stuffing burnt" and "my yorkshire puddings burnt" had
         # no food in them at all, so the burnt row could not match and one of them got a random
         # pancake idea from the pantry instead.
         "parsnip", "parsnips", "carrot", "carrots", "sprouts", "brussels sprouts", "cabbage",
         "kale", "leek", "leeks", "beetroot", "swede", "turnip", "cauliflower", "broccoli",
         "roast potatoes", "roast veg", "stuffing", "dumplings", "yorkshire pudding",
         "yorkshire puddings", "yorkshires", "toad in the hole", "batter", "crepe", "crepes")

# How a fault is said is not a food. "It came out flat" names no subject of its own - the thing
# it is about was named in the line before it - so a taste row that counted "came out" as its
# food word answered the saying alone, and a cake that sank was told to season itself. The rows
# that read a fault ("watery", "dry", "burnt") keep the phrases: "the moussaka came out watery"
# is that row's own question. A taste is something a dish *tastes*, not something it came out.
_A_FAULT_SAID = ("came out", "turned out", "went wrong")
_A_TASTE = tuple(word for word in _FOOD if word not in _A_FAULT_SAID)

# The everyday staples: the plain "how do I cook it" that comes up whatever else people are
# cooking. One row per staple, keyed on the staple's own names, and the entry below wants a
# cooking word as well, so a line that puts the staple on the side ("what goes with rice"),
# asks about what is left of it, or says it went wrong, goes to those entries instead.
def _corn(understood):
    """Sweetcorn, leading with the way the line asks for it.

    The row answered the boil and the grill and nothing else, so "how do i microwave corn on the
    cob" and "can you microwave sweetcorn" were a search punt while the row sat there with the
    wrong method in it. The equipment named in the line is the tell, and the microwave is the way
    most people cook a cob at home.
    """
    said = " " + " ".join(str(word).lower() for word in (understood.get("words") or [])) + " "
    if any(cue in said for cue in (" microwave ", " microwaved ", " microwaving ",
                                   " microwaves ", " micro ")):
        return ("In the microwave a cob takes 3 to 4 minutes on full power for one and 5 to 6 for "
                "two: leave it in its husk, or wrap it in a damp piece of kitchen paper, and turn "
                "it once. It carries on cooking as it stands, so give it a minute before you "
                "butter it. Loose kernels in a covered bowl with a splash of water take 2 to 3 "
                "minutes, stirred halfway.")
    if any(cue in said for cue in (" air fryer ", " airfryer ", " air fried ", " airfry ")):
        return ("In the air fryer rub the cobs with a little oil and give them 10 to 12 minutes at "
                "190C, turning once: the kernels blister at the tips and that is the point. Two "
                "cobs fit in a normal basket; more than that and they steam instead of browning.")
    if any(cue in said for cue in (" grill ", " grilled ", " grilling ", " barbecue ", " bbq ",
                                   " char ", " charred ")):
        return ("Under a hot grill or on the barbecue, 10 to 12 minutes, turning every few "
                "minutes until the kernels start to char in patches - rub them with a little "
                "butter or oil first so they colour rather than dry. Boiled instead, 6 to 8 "
                "minutes in unsalted water; salt toughens it.")
    return ("Boil it in unsalted water for 6 to 8 minutes - salt toughens it - or grill it, "
            "turning it now and then, for 10 to 12 minutes until the kernels start to char. In "
            "the microwave a cob takes 3 to 4 minutes on full power. Butter, salt and pepper, and "
            "it needs nothing else.")


BASICS = (
    (("brown rice",),
     # the rest is in a sentence of its own: a follow-up "how long does brown rice take" is
     # narrowed to a time in the first sentence, and "then 10 minutes off the heat" would be it
     "Brown rice wants more water and longer than white: one mug of rice to two mugs of water, "
     "lid on, 25 to 30 minutes on the lowest heat. Then 10 minutes off the heat before you fork "
     "it through. Rinse it first and don't stir it."),
    # The grains that answer "how do i cook it" but not "how long does it take": couscous, quinoa,
    # barley and bulgur were a shrug on the time question. The time leads, because a time is what
    # was asked for.
    (("quinoa",),
     "Quinoa takes 12 to 15 minutes: one part quinoa to two of water, lid on, simmering, then 5 "
     "minutes off the heat and fork it through. Rinse it first, or it tastes soapy."),
    (("couscous",),
     "Couscous needs no cooking: same volume of boiling water or stock as couscous, cover the bowl "
     "and leave it 5 minutes, then fork it through with a knob of butter and a squeeze of lemon so "
     "it stays loose."),
    (("barley", "pearl barley"),
     "Pearl barley takes 25 to 30 minutes simmered in three times its volume of water or stock, "
     "and whole barley 45 to 60. It is done when a grain squashes between your fingers with no "
     "chalky middle, so taste it rather than time it."),
    (("bulgur", "bulgur wheat"),
     "Bulgur wheat takes 10 to 12 minutes simmered in twice its volume of water, or pour boiling "
     "stock over it, cover and leave it 20 minutes off the heat. Fork it through with a little "
     "olive oil."),
    (("wild rice",),
     "Wild rice is a grass seed rather than a rice, so it takes 40 to 45 minutes in plenty of "
     "boiling water - about three parts water to one of rice - until the grains split and taste "
     "nutty. Drain it and rinse off the starch."),
    (("rice cooker",),
     "Rinse the rice first, then the same one mug of rice to one and a half mugs of water, level "
     "off with the back of a finger and don't go past the line inside the bowl. Let it finish on "
     "its own, leave it on warm for 10 minutes, then fork it through."),
    (("rice", "basmati", "long grain rice", "white rice", "jasmine rice", "rice cooker"),
     "One mug of rice to one and a half mugs of water, lid on, 10 to 12 minutes on the "
     "lowest heat, then 10 minutes off the heat with the lid still on before you fork it "
     "through. Rinse it until the water runs clear first. Don't stir it and don't drain it - "
     "that is what makes it gluey."),
    (("porridge", "oats", "oatmeal", "porridge oats"),
     "50g of oats to 300ml of milk or water per person, with a pinch of salt, stirred over a "
     "medium heat for 4 to 5 minutes. Take it off while it still looks a little loose, because it "
     "thickens as it stands, and stir in a splash more milk if it sets."),
    (("white sauce", "cheese sauce", "bechamel", "béchamel"),
     "About 10 minutes start to finish. Melt 50g of butter, stir in 50g of plain flour and cook "
     "that for a minute, then add 500ml of milk a good splash at a time, whisking each one in "
     "before the next goes in. Simmer it for 5 minutes until it coats the back of a spoon, then "
     "season it. For a cheese sauce, stir in 100g of grated cheddar once it is off the heat."),
    (("mash", "mashed potato"),
     "Use a floury potato like Maris Piper or King Edward, cut into even chunks and boiled in "
     "salted water for 15 to 20 minutes. Drain them, leave them in the colander for a minute to "
     "steam dry, then mash with butter and warm milk - cold milk makes it gluey - and don't use a "
     "food processor."),
    (("vegetables", "veg"),
     "The one rule for vegetables is short and hot: steam or boil them 5 to 7 minutes so "
     "they still have a bite, or roast them at 200C (180C fan) for 25 to 35 minutes in oil "
     "with salt. Cut them to a similar size and they finish together, and salt the water "
     "rather than the pan."),
    # "how do i chop an onion" is a knife question, and the onion row under it answers the pan:
    # "chop it, then soften it in oil" is the one thing the person already knows how to do. The
    # sentence is the method, and it sits above the onion row so the plain cooking question keeps
    # its answer.
    (("chop an onion", "chop onions", "chopping an onion", "chopping onions", "dice an onion",
      "dice onions", "dicing an onion", "dice onions", "slice an onion", "cut an onion",
      "cut up an onion", "prepare an onion"),
     "Halve it top to bottom through the root, lay a half cut side down and slice across it "
     "towards the root, then cut the slices the other way, and it is diced. Leave the root end on "
     "until the last cut, because it holds the layers together. Use the sharpest knife you have "
     "and keep the tip on the board: a blunt knife crushes the cells and releases more of the "
     "sulphur that makes your eyes water."),
    # The everyday jobs in a kitchen are prep jobs, and the same ask comes for every ingredient:
    # "how do i peel a potato", "how do i chop garlic", "how do i cut an avocado". A line like
    # that names the ingredient and the knife, and the cooking rows answered the pan ("chop it,
    # then soften it in oil") or nothing at all. One row per ingredient, keyed on the phrase, so
    # the plain "how long do i boil potatoes" keeps the method it already has.
    (("peel a potato", "peel potatoes", "peeling potatoes", "peel a potato quickly",
      "how do i peel potatoes", "prepare potatoes", "prepare a potato"),
     "Take the skin off in strips with a peeler, working away from you and turning the potato as "
     "you go, then dig any eyes out with the tip of the peeler. Drop them into a bowl of cold "
     "water if they are not going in the pan straight away, because peeled potato goes pink in "
     "the air. Peel floury ones like Maris Piper just before they cook, not the night before."),
    (("chop garlic", "crush garlic", "mince garlic", "chop a garlic clove",
      "prepare garlic", "chop garlic cloves", "peel a garlic clove", "peel garlic cloves"),
     "Lay the clove on the board, put the flat of the knife on top and press down with the heel "
     "of your hand: the skin slips off and the clove is already crushed. Chop it roughly, "
     "sprinkle a pinch of salt on it and drag the flat of the knife over it in circles to turn it "
     "into a paste. Crushed like that it sweetens in the pan; left in chunks it burns."),
    (("peel ginger", "chop ginger", "grate ginger", "prepare ginger", "mince ginger"),
     "Scrape the skin off with the edge of a teaspoon, which follows the knobs better than a "
     "peeler and wastes less of the root. Grate it on the fine side of a grater, or freeze the "
     "knob whole and grate it from frozen, which is quicker and keeps for months. The skin is "
     "thin and edible, so it can stay on if it is going into a curry."),
    (("chop a carrot", "chop carrots", "dice a carrot", "dice carrots", "slice a carrot",
      "slice carrots", "prepare carrots", "prepare a carrot"),
     "Top and tail it, cut it in half lengthways and lay the flat side down so it cannot roll. "
     "For sticks, cut each half into lengths and slice those; for dice, cut the lengths into "
     "batons first, then turn them and slice across. Keep every piece the same size, because "
     "that is what makes them cook at the same rate."),
    (("chop mushrooms", "slice mushrooms", "prepare mushrooms", "cleaning mushrooms",
      "cleaning a mushroom"),
     "Wipe the caps with damp kitchen paper, or rinse them quickly under the tap and dry them on "
     "a tea towel - either works, because a few seconds of water adds nothing a mushroom did not "
     "already have, and only a bowl of soaking water makes them watery. Snap the stalk out level "
     "with the cap and slice straight down through cap and stalk together. Do not crowd the pan - "
     "a crowded pan of mushrooms boils in its own water and never browns."),
    (("cut an avocado", "prepare an avocado", "peel an avocado", "stone an avocado",
      "remove the stone from an avocado", "slice an avocado", "how do i cut an avocado"),
     "Run the knife round the stone from top to bottom, twist the two halves apart, then lever "
     "the stone out with a spoon rather than the knife. Peel the skin back or scoop the flesh out "
     "with a spoon, and slice it while it is still in its shell. Squeeze lemon or lime over it if "
     "it is going to sit, because cut avocado goes brown in the air."),
    (("peel a mango", "cut a mango", "prepare a mango", "slice a mango",
      "how do i cut a mango"),
     "Slice the two cheeks off either side of the flat stone, score the flesh in a grid without "
     "cutting the skin, then push the skin inside out and cut the cubes off it. A peeler and a "
     "knife down the sides of the stone works too and wastes a little more. A ripe mango gives "
     "slightly under your thumb; a hard one is stringy and sour."),
    (("cut up a pineapple", "cut a pineapple", "prepare a pineapple", "peel a pineapple",
      "how do i cut a pineapple", "how do i cut up a pineapple", "slice a pineapple"),
     "Slice the top and the base off flat so it stands up, then cut the skin away in strips from "
     "top to bottom, taking the eyes with it. Cut it into quarters, stand each one up and slice "
     "the core out, then cut the rest into the pieces you want. The core is tough raw but fine "
     "in a smoothie."),
    (("juice a lemon", "juice a lime", "squeeze a lemon", "squeeze a lime", "juice an orange",
      "juice lemons", "squeeze lemons"),
     "Roll it on the worktop with the heel of your hand first to break the cells inside, then cut "
     "it across the middle rather than top to tail. Push a fork into the cut face and squeeze, "
     "turning as you go, and strain out the pips. A lemon at room temperature gives more juice "
     "than one out of the fridge."),
    (("onions", "onion"),
     "Chop it, then soften it in oil on a low heat for 8 to 10 minutes with a pinch of salt: "
     "that is what makes it sweet and golden. A hot pan browns the outside and leaves the "
     "middle raw and sharp, so turn the heat down and give it the time."),
    # `_corn`, because the way a cob is cooked depends on the machine the line names
    (("corn on the cob", "sweetcorn", "corn"), _corn),
    (("butternut squash", "butternut", "squash"),
     "Halve it, scoop out the seeds, rub the cut sides with oil and roast face down at 200C "
     "(180C fan) for 40 to 45 minutes. Cubed it takes 25 to 30 minutes, and it is done when "
     "a knife goes in with no resistance."),
    (("pork chops", "pork chop"),
     "Pat them dry, season, and sear in a hot pan 3 to 4 minutes a side, then rest 5 minutes "
     "- pork is safe slightly pink now, at 70C in the middle. A thick chop also finishes in "
     "the oven at 200C (180C fan) for 10 to 12 minutes."),
    (("fish", "white fish", "cod", "haddock", "salmon fillet", "fillet of fish"),
     # "how long do i bake salmon fillets" wants the clock and "is my cod cooked through" wants
     # the test, and one sentence can carry both: the time is the clause the how-long ask reads
     # first, and the flake test follows it in the same sentence rather than a sentence later.
     "Bake fillets at 200C (180C fan) for 12 to 15 minutes - done when the thickest part flakes "
     "into opaque white, so keep it a minute short rather than a minute long - or fry them skin "
     "side down in a hot pan for 4 minutes, then 2 on the other side."),
    (("potato wedges", "wedges"),
     "Cut them into wedges about 2cm at the thick edge, toss in oil, salt and paprika and roast "
     "at 200C (180C fan) for 25 to 30 minutes, turning once at halfway: they are done when the "
     "edges are deep gold and a knife slides into the thick part. Parboiling 8 minutes first "
     "makes them crisper outside and fluffier in."),
    (("chard", "swiss chard"),
     "Cook the stems first: slice them and fry 4 to 5 minutes, then add the leaves for 2 to 3 "
     "minutes more, because the stems take far longer. A knob of butter, a pinch of salt and a "
     "squeeze of lemon, and the leaves wilt down to almost nothing."),
    (("peppers", "bell peppers", "bell pepper"),
     "Fry sliced peppers in a hot pan with oil for 6 to 8 minutes until the edges soften and "
     "catch a little colour, or roast halves at 200C (180C fan) for 25 minutes. They go sweet "
     "with long cooking and stay crunchy with short cooking, so it depends what you want."),
    (("celery", "celery sticks"),
     "Slice it and soften it in butter for 6 to 8 minutes: that is the base of a soup or a "
     "stew, and it goes sweet rather than stringy. On its own, braise the sticks with stock "
     "and a lid for 20 minutes, or shave them raw into a salad with lemon and salt."),
    (("fennel", "fennel bulb"),
     "Slice it thin and roast at 200C (180C fan) for 25 minutes with oil, salt and a little "
     "lemon - the aniseed goes sweet. Raw and shaved with olive oil, lemon and parmesan it is "
     "a salad in 5 minutes. Cut out the tough core first."),
    (("celeriac",),
     "Peel it thickly, cube it and boil for 15 to 20 minutes, then mash it half and half with "
     "potato - it is wet on its own and needs the potato to hold it. It browns fast once it is "
     "cut, so drop the pieces in water with a squeeze of lemon until they go in the pan; raw and "
     "shredded with mayonnaise, mustard and lemon it is remoulade."),
    (("turnip", "turnips"),
     "Small young turnips only want 10 to 12 minutes boiled, or 25 minutes roasted in wedges "
     "at 200C (180C fan) with oil and honey. Big older ones are woody and bitter, so peel "
     "them well and mash them with potato and butter instead."),
    (("broad beans", "fava beans"),
     "Boil them for 4 to 5 minutes, then pop them out of their skins - the skins are tough and "
     "bitter, and the beans inside are sweet. Small ones can stay in their skins. Dress them "
     "with oil, lemon, mint and a little salt."),
    (("shallots", "shallot"),
     "Slice them and soften in butter for 6 to 8 minutes on a low heat - they are sweeter and "
     "milder than onions, so they need less time and brown faster. Whole, roast them at 200C "
     "(180C fan) for 25 to 30 minutes with oil and a pinch of salt."),
    (("pak choi", "bok choy", "pak choy"),
     "Halve it lengthways and fry cut side down in a hot pan for 2 to 3 minutes, then add a "
     "splash of soy sauce, a little garlic and a lid for 1 minute more. It is done when the "
     "base is tender and the leaves have just wilted, so it takes about 5 minutes in all."),
    (("mange tout", "mangetout", "sugar snap peas", "snow peas"),
     "Stir-fry them in a very hot pan for 2 to 3 minutes, or steam them for 3: they are done "
     "as soon as they are hot through and still squeak when you bite one. Don't boil them, or "
     "the sweetness goes into the water."),
    (("buttermilk", "leftover buttermilk"),
     "Buttermilk is not cooked on its own: it is what makes soda bread rise with bread soda, it "
     "thins a pancake batter, and it tenderises chicken in a marinade for an hour before frying. "
     "It is naturally sour and thick, so in a recipe you can stand in for it with milk and a "
     "squeeze of lemon left for 10 minutes."),
    (("marrow", "vegetable marrow", "marrows"),
     "Roast it in thick rings: peel it, scoop out the seeds, cut 2cm rings, oil and salt them and "
     "give them 30 to 35 minutes at 200C (180C fan) until the edges colour. Or halve it, salt it "
     "and let it drain 20 minutes, then stuff it with mince and rice and bake 45 minutes at 190C "
     "(170C fan) - it is mostly water, so the salt-and-drain is what stops it going to mush."),
    (("chicory", "endive"),
     "Halve it and braise cut side down in butter for 3 to 4 minutes, then add a splash of "
     "stock and a lid for 10 minutes, which takes the bitterness down. Raw, the leaves are a "
     "scoop for a dip, and a little sugar or orange in the pan helps too."),

)

_STAPLE_NAMES = tuple(name for _names, _reply in BASICS for name in _names)

# "how do i cook" is in the learner's key below, and the phrase is the whole of "how do i cook
# potatoes", "how do i cook pasta" and "how do i cook chard": the four-things card then answered a
# hundred lines that name a food, ahead of the row that knows the food. Those lines are the food's
# own question, so the card stands down when the line names one of the things the pantry and the
# staples tables already answer, and keeps the lines it was written for - "how do i learn to
# cook", "where do i start cooking", "how do i cook from scratch", "how do i cook for my family".
# The food names are read from the tables when the line arrives, because they are written below
# this entry.
def _learn_to_cook(memory, understood):
    said = {_fold(str(word).lower()) for word in (understood.get("words") or ())}
    # The tables are folded the same way the line is, and not before _fold is defined, which is
    # further down this file: "how do i cook ribs" arrived as "rib" and the pantry lists "ribs",
    # so 133 of the food names - ribs, carrots, apples, chickpeas, oats, chicken breasts - never
    # fired this stand-down and the beginner's card answered a dish's own question.
    if said & _foods_said():
        return None
    return ("Learn four things and the rest follows: pasta with a sauce, an omelette, a tray of "
            "roasted vegetables, and a one-pot curry or stew. Cook the same one twice in a week "
            "rather than a new one each night, and taste as you go - food that tastes flat "
            "usually wants salt, a squeeze of lemon, or more time in the pan. A cheap "
            "thermometer takes the fear out of chicken and pork.")

# A staple inside a dish is that dish's question. Rice pudding, potato salad, a potato gratin,
# scalloped potatoes, sweet potato, pasta bake and spaghetti bolognese all have their own times
# and their own methods, so the plain staple does not answer for them.
# "rice without a rice cooker" is a question about the pan, not about the machine.
# A staple named in a line that is not asking how to cook it is that line's business: what to
# make with it ("what can i make with half a cabbage" wants a dish, not a method), what to do
# with the rest of it, and who in the house will not eat it. A method given for one of those is
# a confident wrong answer to a question nobody asked.
NOT_A_METHOD = ("make with", "made with", "make using", "use up", "using up", "use it up",
                "what can i", "what should i", "what could i", "hate", "hates", "hated",
                "dislike", "dislikes", "allergic", "allergy", "cant stand", "cannot stand",
                "doesnt like", "does not like", "dont like", "do not like", "wont eat",
                "wont touch", "fussy", "left with", "half a",
                # "i cooked rice yesterday, can i eat it" is a keeping question about a bowl in
                # the fridge, and a staple method is a confident wrong answer to it: the day the
                # person names is what tells the two apart, so the method rows stand down there
                # and keeping.py's own row for the food answers it.
                "yesterday", "yesterdays", "last night", "the day before", "day before",
                "the day after", "day after", "day later", "a day later", "days ago",
                "a couple of days ago", "2 days ago", "two days ago",
                # a game shares its name with a food, and a shot at it is not a pan question:
                # "how do i improve my backhand at squash" was told to halve a butternut squash
                "backhand", "forehand", "racket", "racquet", "tennis court", "squash court",
                "badminton", "volleyball", "netball", "the ball", "cricket")

# The words that make a line a question about whether a crop is ready to pick, rather than about
# cooking it. "how do i know when my onions are ready" is onions in the ground; the harvest row in
# garden.py answers it, so the staple method turns itself down (see `_staple`).
KNOWS_READY = ("know when", "how do i know", "how will i know", "how can i tell",
               "when are they ready", "when are mine ready", "are they ready", "are mine ready",
               "are they done yet", "when do i know")

# The dish word can also be the food the staple is made into or served as: cauliflower rice,
# sushi rice, paella rice, an overnight oats pot, rice krispie cakes, a rice bowl. Each of those
# is its own answer, and a staple method given for one of them is a confident wrong answer.
DISH_BEFORE = frozenset("sweet fried roast roasted baked mashed creamed scalloped glazed "
                        "cauliflower sushi paella overnight egg fried".split())
DISH_AFTER = frozenset("pudding salad bake gratin pie bread cake cakes balls bolognese cheese "
                       "curry soup stew krispie crispy noodle noodles bowl paper wrap sushi "
                       "ball bite finger patty".split())


# The words that make a line a question about cooking the staple rather than a mention of it.
STAPLE_ASK = ("cook", "cooking", "make", "making", "how", "long", "boil", "boiling",
              "time", "much", "ratio", "method", "properly", "instructions", "best way",
              "minutes", "do i", "should i", "recipe")


# The two directions of one question, which need different first sentences: "my soup is too
# thick" wants it thinned, and "how do i thicken my soup" wants it thickened. One reply cannot
# open with both, so the words of the line pick the half (see `_body`).
_BODY_TOO_THICK = (
    "Too thick: add hot stock, milk or just water a splash at a time, stirring, until it pours the "
    "way you want it, then taste it again because thinning takes the salt with it. A spoon of "
    "butter or cream stirred in at the end does the same with more flavour, and a stew that has "
    "cooked down only needs the lid on for ten minutes."
)
_BODY_TOO_THIN = (
    "Simmer it uncovered for 10 minutes to reduce it, or blend a ladleful and stir it back in for "
    "body without flour. A handful of red lentils thickens a soup or stew in 15 minutes; for a "
    "stew, take the lid off for the last half hour."
)


# A complaint about the pot, in the shapes people write it. "How do i make thick soup" has the
# word "thick" and wants the other direction, so a bare "thick" is not enough on its own.
_TOO_THICK_SAID = ("too thick", "so thick", "very thick", "really thick", "is thick", "its thick",
                   "it's thick", "thick and", "stodgy", "claggy", "gluey", "thinner",
                   "less thick", "thin down", "thin it", "make it thinner", "soup thinner",
                   "make my soup thinner")


# A shoulder, a hip and a back are all cuts of meat and all parts of a person, so the meat
# words alone cannot tell "how long should i rest my shoulder" from "how long to rest a
# shoulder of lamb". A body word on its own, with no cut named, is the training question.
_REST_BODY = ("my shoulder", "my knee", "my back", "my hip", "my leg", "my arm", "my neck",
              "injured", "injury", "injuries", "pain", "painful", "hurts", "hurting",
              "sore", "stiff", "stiffness", "sprain", "sprained", "pulled a muscle",
              "after a fall", "physio", "physiotherapist", "gym", "workout", "worked out",
              "exercise", "exercising", "training", "trained", "running", "run", "sports day",
              # a joint is a body part and also a cut of meat, and `joint` sits in the cut list
              # below, so "should i rest my joints" was answered with the four-meat paragraph
              "my joint", "my joints", "joint pain", "aching", "ache", "aches")
_REST_CUT = ("lamb", "pork", "beef", "veal", "venison", "joint", "roast", "brisket",
             "turkey", "chicken", "duck", "goose", "steak", "ribs", "rib", "ham", "gammon",
             "shoulder of", "leg of", "of lamb", "of pork", "of beef", "meat", "wellington")


# The cut phrases that really do name a joint of meat: "my leg of lamb" is both, and the dish
# row for a leg of lamb has the better answer, so these keep the cut in charge.
_REST_CUT_PHRASE = ("of lamb", "of pork", "of beef", "of veal", "shoulder of", "leg of")


def _resting_a_body_part(said):
    """True when the line is about resting a body, not about standing meat."""
    body = any(" " + word + " " in said for word in _REST_BODY)
    cut = any(" " + word + " " in said for word in _REST_CUT)
    # A body word wins outright unless the line names a cut of meat, because "joint" is on both
    # lists: "should i rest my joints" and "how long should i rest a sprained joint" were meat.
    if body and not any(phrase in said for phrase in _REST_CUT_PHRASE):
        return True
    return body and not cut


def _rest_the_meat(memory, understood):
    """How long to rest the meat, unless the dish table already has the rest for this dish.

    `do i need to rest a steak` and `why should i rest a chicken` were answered by the dish rows
    in dishes.py, each with the minutes for that one dish and the reason in the same sentence. A
    four-meat paragraph is a worse answer to a line that names one of them, so this entry turns
    the line down and the dish row answers, the way the roast rows stand down for a rest question.
    """
    from .dishes import ask_kind, reply as dish_reply
    from .lookup import find
    said = " " + " ".join(str(word) for word in ((understood or {}).get("words") or [])) + " "
    if " the rest " in said or " rest of " in said:
        # "what do i do with the rest of the joint" is the leftovers question. The "rest" there
        # is the remainder, not the standing time, and meals.py's use-up row answers it.
        return None
    if _resting_a_body_part(said):
        # "how long should i rest my shoulder" is a training question: a shoulder is a cut of
        # pork and lamb as well as a joint on a person, and the meat words alone cannot tell them
        # apart. A body word with no cut named is never this answer.
        return None
    if ask_kind(understood) == "rest" and dish_reply("rest", memory, understood):
        # The dish table has the minutes for the one dish the line named. Stand down only when
        # its own row is what answers next: "why rest a steak" and "how should i rest a steak"
        # reach nothing but a shrug or the red-meat limit of the day, and the four-meat
        # paragraph is the better answer to both.
        next_row = find(understood, reject=lambda item: item.id == "rest-meat")
        if getattr(next_row, "id", None) == "plan-followup":
            return None
    minutes = ("loosely under foil and off the heat, not back in the oven: 15 to 20 minutes for "
               "a chicken or a turkey, 10 to 20 for a joint of beef, lamb or pork, 5 to 10 for a "
               "steak or chops, and 20 to 30 for a brisket")
    reason = ("standing lets the heat that has built up round the outside move back into the "
              "middle, so the juice stays in the meat when you carve it instead of running out "
              "onto the board")
    if "why" in ((understood or {}).get("asks") or ()):
        # a why line wants the reason first, with the minutes behind it
        return ("Rest it because " + reason + " - " + minutes + ". It stays hot that long under "
                "the foil, so nothing is lost by waiting.")
    return (minutes[0].upper() + minutes[1:] + ". " + reason[0].upper() + reason[1:]
            + ". It stays hot that long under the foil, so nothing is lost by waiting.")


def _body(memory, understood):
    """Which way the pot is wrong, so the reply leads with the fix the person asked for."""
    said = " " + " ".join(_fold(str(word)) for word in (understood.get("words") or [])) + " "
    thickening = "thicken" in said or "thicker" in said or "thickening" in said
    complaining = any(shape in said for shape in _TOO_THICK_SAID)
    if complaining and not thickening:
        return _BODY_TOO_THICK
    return _BODY_TOO_THIN


# A child who will not eat veg, named in this line or in the one just before it: "my son wont eat
# vegetables, hes 4" and then "should i just blend veg into a sauce" are the same question asked
# twice, and a follow-up names the method, not the child, so the key cannot carry the child word.
CHILD_WORDS = (" kid", " kids", " child", " children", " son", " daughter", " toddler", " baby",
               " fussy", " picky", " wont eat", " won't eat", " refuses", " weaning",
               " nursery", " school dinner", " school dinners", " he wont", " she wont")


def _about_a_child(memory, understood):
    """True when the veg question is a parent's, here or in the last few turns."""
    line = " " + ((understood or {}).get("clean") or "") + " "
    if any(word in line for word in CHILD_WORDS):
        return True
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    for turn in reversed(turns[-3:]):
        said = " " + (turn.get("user") or "") + " " if isinstance(turn, dict) else ""
        if any(word in said for word in CHILD_WORDS):
            return True
    return False


KIDS_VEG = ("Keep serving one small piece of veg next to something they already like, without a "
            "fight or a reward: it can take ten tries before a toddler accepts a new one. Roasting "
            "carrots or broccoli in a little oil makes them sweeter, and a dip to dunk turns it "
            "into a game. Grated or blended into what they already eat - carrot in the bolognese, "
            "courgette in a muffin, spinach in a soup - gets the veg in without a standoff.")


ADULT_VEG = ("Put them where you already eat rather than on a separate pile: grated carrot or "
             "courgette in the mince, a handful of spinach stirred into pasta at the end, frozen "
             "peas straight into rice, beans or lentils bulking out a chilli. Frozen and tinned "
             "count, and so does a bag of mixed veg thrown into a tray bake. Aim for one extra "
             "portion at a meal you already have rather than a new meal you have to keep up.")


def _more_veg(memory, understood):
    """The same question from a parent gets the feeding answer, not the adult portions one."""
    if not _about_a_child(memory, understood):
        return ADULT_VEG
    return None if _the_veg_card_was_just_said(memory) else KIDS_VEG


def _the_veg_card_was_just_said(memory):
    """True when the bot's last turn already opened with this card."""
    opening = KIDS_VEG[:40].lower()
    for last in (memory.get("turns") or [])[-2:]:
        if isinstance(last, dict) and opening in (last.get("bot") or "").lower():
            return True
    return False


def _kids_veg(memory, understood):
    """The feeding answer, or nothing when the conversation has no child in it.

    Once the card has been given, saying it again is the repeat STYLE.md forbids: a bare "any
    tips" or "how do i get him to try it" one turn after it is the same question, and the answer
    is the paragraph the person has just read. The row stands down and lets whatever else can
    answer the turn take it - the composer reads the card the person already has.
    """
    if not _about_a_child(memory, understood):
        return None
    return None if _the_veg_card_was_just_said(memory) else KIDS_VEG


def _harvest_crops():
    """The crops with a harvest row, imported where they are used so the two tables stay apart."""
    from .garden import harvest_crops
    return harvest_crops()


def _done_words():
    """The words that make a crop question a pan question, shared with the harvest rows."""
    from .garden import DONE_NOT
    return DONE_NOT


# A portion question and a timing question both start with "how much" or "how many": "how much
# rice do i need for four people" is the portion table's, and "how many minutes per side for pork
# chops" is this row's own. The avoid list used to hold the two bare words, so the timing question
# was stood down as well and got a shrug while the same line with "how long do i cook" in it was
# answered. A how-much ask that names a time or a heat is a method question, so the row keeps it.
_A_HEAT_OR_TIME = re.compile(
    r"\b(minutes?|mins?|minutes'|hours?|hrs?|seconds?|degrees?|celsius|fahrenheit|gas mark|"
    r"temp|temperature|oven)\b|\bhow long\b")
_A_HOW_MUCH = re.compile(r"\bhow (much|many)\b")
# "a side" is a face of the meat once the line names a time ("3 minutes a side"), and the rest of
# the plate when it does not ("what side with steak", "any sides for a roast").
_A_SIDE_SAID = re.compile(r"\bsides?\b")


def _not_a_portion_ask(understood):
    """False when a "how much" line asks an amount, or a "side" line means the plate."""
    text = str(understood.get("clean") or understood.get("norm_text")
               or " ".join(understood.get("words") or [])).lower()
    if _A_HOW_MUCH.search(text) and not _A_HEAT_OR_TIME.search(text):
        return False
    if _A_SIDE_SAID.search(text) and not _A_HEAT_OR_TIME.search(text):
        return False
    return True


def _staple(memory, understood):
    """How to cook the everyday staple the line names, or nothing when it names none."""
    said = [_fold(str(word).lower()) for word in (understood.get("words") or [])]
    joined = " " + " ".join(said) + " "
    for phrase in NOT_A_METHOD:
        if phrase in joined:
            return None
    if any(phrase in joined for phrase in KNOWS_READY):
        # The words that make it a pan question after all: "how do i know when my carrots are
        # done" is a cook asking for the time, and the harvest rows stand down for it (their
        # avoid list carries the same words), so this method has to answer it.
        done = _done_words()
        if not any(" %s " % word in joined for word in done):
            _harvest = _harvest_crops()
            if any(" %s " % crop in joined for crop in _harvest):
                return None
    for names, reply in BASICS:
        for name in names:
            parts = [_fold(piece) for piece in name.split()]
            size = len(parts)
            for start in range(len(said) - size + 1):
                if said[start:start + size] != parts:
                    continue
                before = said[start - 1] if start else ""
                after = said[start + size] if start + size < len(said) else ""
                if before in DISH_BEFORE or after in DISH_AFTER:
                    continue
                # "how do i make a sauce for pasta" wants a sauce, not how to boil pasta:
                # the two sauce rows are named, so a bare sauce word stands this one down
                if name not in ("white sauce", "cheese sauce", "bechamel", "béchamel") and (
                        "sauce" in said or "saucy" in said):
                    continue
                # a guard word counts either side of the staple's name: "lamb chops" puts the
                # cut after the meat, and "onions smell in the fridge" puts the problem after it
                rest = said[:start] + said[start + size:]
                # the row's own name carries the guard, so "onion" and "onions" are one row
                guards = NOT_WANTED.get(names[0], ())
                if name != names[0]:
                    guards = guards + NOT_WANTED.get(name, ())
                # The row's own words are a case it already answers, so a guard that the answer
                # itself says is not a reason to stand it down: the lamb shank row gives the
                # slow cooker time for a shank, and "can i do it in a slow cooker" after "how do
                # i cook a lamb shank" wants that row, not its own "slow cooker" guard.
                own = _fold(reply.lower()) if isinstance(reply, str) else ""
                if _a_guard_said(rest, joined, guards, own):
                    continue
                # A staple whose method depends on the equipment the line names answers as a
                # function of the line; the plain rows are strings and are returned as they are.
                return reply(understood) if callable(reply) else reply
    return None


# An appliance named beside a cut is answered by the two tables together: the dinner ideas stand
# down for it (they hand the cut to the table), so a cut row stood down for the appliance would
# leave the line with no answer at all. "how do i cook a leg of lamb in a slow cooker" was the
# lamb's oven time before these guards fired, and a shrug after.
_AN_APPLIANCE = ("slow cooker", "slow cookers", "crockpot", "crock pot", "air fryer",
                 "pressure cooker", "instant pot", "oven")


def _an_appliance_has_the_line(text):
    """True when an appliance and a cut are both named, so the cut row has to answer."""
    try:
        from . import dishes
    except Exception:  # noqa: BLE001 - the guard is a courtesy, not the row
        return False
    return dishes._names_an_appliance_and_a_cut(text)


def _a_guard_said(rest, joined, guards, own=""):
    """Whether the line carries one of a row's guard words, or one of its guard phrases.

    A single word is read either side of the staple's name ("onions smell in the fridge", "the
    smell of onions"), because it belongs to the staple. A phrase is read across the whole line,
    because its words can sit on both sides of the name: "how many lamb chops per person" has
    "how many" before the name and nothing of it in `rest`. Every phrase in these tables was
    checked one word at a time, so none of them ever fired, and the rows they were written for
    answered lines they were meant to stand down for.
    """
    for guard in guards:
        if " " in guard:
            phrase = _fold(guard)
            if phrase in joined and phrase not in own:
                if guard not in _AN_APPLIANCE or not _an_appliance_has_the_line(joined):
                    return True
        elif guard in rest:
            return True
    return False


def _pancakes(memory, understood):
    """Pancakes, leading with the kind the line asks for.

    "how do i make american pancakes" used to get twelve thin pancakes and the American variant
    as an afterthought, which is the wrong first sentence for that line.
    """
    words = set(understood.get("words") or [])
    if "mix" in words and not words & {"make", "made", "making", "recipe", "batter", "whisk",
                                        "homemade", "from"}:
        # airy-deer's catch: "best pancake mix" and "where to buy pancake mix" are the box in the
        # shop, and "how do i make pancake mix" is the one that wants this batter. Passing lets
        # the shopping side have the packet lines.
        return None
    if words & {"american", "fluffy", "thick", "buttermilk", "scotch"}:
        return ("For a dozen thick American pancakes, whisk 150g plain flour, 2 teaspoons of baking "
                "powder, a tablespoon of sugar, 2 eggs and 250ml milk into a thick batter that "
                "holds its shape, and let it rest 10 minutes. Cook them in a buttered pan on a "
                "medium heat, 2 minutes a side, and turn them once, when bubbles pop and stay open. "
                "The baking powder is what lifts them; for thin pancakes leave it out and use "
                "300ml milk.")
    return ("For about 12 thin pancakes, whisk 100g plain flour, 2 eggs and 300ml milk with a pinch of "
            "salt, then let the batter rest 20 minutes. Cook them in a hot non-stick pan with a little "
            "butter, about a minute a side, until bubbles pop on top and the edges look dry. The rest "
            "is what stops them tearing; American ones want a teaspoon of baking powder and a "
            "thicker batter. Flat ones are a batter that was too thin, or an old raising agent.")


def _pancake_batch(memory, understood):
    """Pancake amounts for the number of people the line names.

    The four-person batter is 200g flour, 3 eggs and 600ml milk, so the rule is 50g of flour, three
    quarters of an egg and 150ml of milk each. "How many pancakes for 10 people" was answered with
    the four-person numbers, which is the wrong amount for the question the person asked.
    """
    people = None
    for number in understood.get("numbers") or []:
        value, unit = number.get("value"), number.get("unit")
        if not isinstance(value, (int, float)) or not 2 <= value <= 40:
            continue
        if unit in (None, "", "people", "person", "persons", "adults", "adult", "kids", "guests",
                    "portions", "servings"):
            people = int(round(value))
            break
    if people is None:
        return ("For four people allow 200g plain flour, 3 eggs and 600ml milk, which makes about "
                "16 thin pancakes; a family with small children is happy on 150g. Cook them a "
                "minute a side in a hot pan until the bubbles pop and the edges look dry.")
    grams = 50 * people
    flour = "%dkg" % (grams // 1000) if grams % 1000 == 0 else (
        "%d and a half kg" % (grams // 1000) if grams > 1000 and grams % 500 == 0
        else "%dg" % grams)
    eggs = 0.75 * people
    whole = int(eggs)
    egg_words = ("%d or %d eggs" % (whole, whole + 1) if 0.4 <= eggs - whole <= 0.6
                 else "%d eggs" % int(round(eggs)))
    millilitres = 150 * people
    if millilitres < 1000:
        milk = "%dml of milk" % millilitres
    elif millilitres % 1000 == 0:
        milk = "%d litres of milk" % (millilitres // 1000)
    else:
        milk = ("%.1f litres of milk" % (millilitres / 1000.0)).replace(".0 litres", " litres")
    return ("For %d people allow %s plain flour, %s and %s, which makes about %d thin pancakes. "
            "Cook them a minute a side in a hot non-stick pan with a little butter, until the "
            "bubbles pop and the edges look dry; for thick American ones add a teaspoon of baking "
            "powder per 200g of flour." % (people, flour, egg_words, milk, 4 * people))


def _sweet_potato(memory, understood):
    """Sweet potato, leading with the method the line asks for.

    The wedges method is the answer to "how do i cook sweet potato", but "how long do i boil sweet
    potato" and "sweet potato mash" want the boiling time first: pointing a boil question at a
    25-minute oven method is a wrong answer, not just a different one.
    """
    words = set(understood.get("words") or [])
    if words & {"boil", "boiled", "boiling", "steam", "steamed", "steaming", "mash", "mashed",
                "puree", "pureed"}:
        return ("Boil peeled chunks for 12 to 15 minutes, until a knife slides in with no "
                "resistance: sweet potato softens faster than white potato, so test it at 10. "
                "Drain and steam it dry for a minute, then mash it with butter and a pinch of salt "
                "and go easy on the milk, because it is wetter than white potato.")
    if words & {"microwave", "microwaved", "microwaving", "quick", "quickly", "fast",
                "fastest", "hurry", "hurried", "hungry", "rush"}:
        # "how do i cook sweet potato in the microwave" was answered with twenty-five minutes in
        # the oven, and "how do i cook sweet potato quickly" with the same: the whole answer for
        # the fastest way was inside the last sentence of the oven method.
        return ("One medium sweet potato, pricked all over with a fork, takes 5 to 8 minutes on "
                "high: give it 5, turn it, then a minute at a time until a knife slides in with no "
                "resistance. Two take 10 to 12 minutes, and chunks for mash take 8. It steams in "
                "there rather than crisping, so give the skin 5 minutes in a hot oven or a dry pan "
                "afterwards if you want it crisp.")
    if words & {"fryer", "airfryer", "airfried"}:
        return ("In the air fryer, wedges cut into 2cm pieces take 15 to 18 minutes at 190C, shaken "
                "once halfway: toss them in a little oil, salt and paprika first and do not crowd "
                "the basket, or they steam instead of crisping. Whole ones take 35 to 40 minutes at "
                "180C, and fries cut thin take 12 to 15 minutes.")
    return ("For wedges, cut them into 2cm pieces, toss them in oil, salt and paprika and roast at "
            "200C (180C fan) for 25 to 30 minutes. Whole, they bake in about 45 minutes at 200C, or "
            "8 minutes in the microwave for one on its own. Boiled for mash, chunks take 12 to 15 "
            "minutes.")

# A pet that has eaten something is a vet question, not a kitchen one, and a dog that has taken the
# chicken out of the fridge is not asking how long to keep it. These words mark the pet, or a line
# already saying the food went down someone, so the cooking entries a pet line can reach share one
# guard instead of each carrying its own copy. The pets domain answers what a pet may eat; when
# nothing there fits, "I don't know" is better than a recipe.
# The bare "ate"/"eaten"/"eating" are not here: a person also eats pink chicken, and "is my
# chicken pink safe to eat" is a food-safety question, not a pet one. The animal words are what
# does the work, and a line with no animal in it was never certainly about a pet.
PET_LINE_WORDS = ("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens", "pet",
                  "pets", "vet", "swallowed", "swallow", "chewed", "choking", "choke",
                  "poisoned", "vomiting")


def _thighs(memory, understood):
    """Chicken thighs, with the lemon-and-potato traybake if that's what they have."""
    words = " ".join(understood.get("words") or [])
    if "lemon" in words or "potato" in words or "potatoes" in words:
        return ("Halve the potatoes, toss everything with oil, lemon slices and salt, and roast at "
                "200C (180C fan) for 35 to 40 minutes, skin side up, until the skin is crisp and the "
                "juices run clear. Squeeze the roasted lemon over before serving.")
    return ("Roast chicken thighs at 200C (180C fan) for 35 to 40 minutes, skin side up and spaced "
            "out, until the skin is crisp and the juices run clear. Salt the skin before they go in "
            "and don't crowd the tray, or they steam instead of crisping.")


def _weight_words(kilos):
    """"0.5" -> "500g", "1.5" -> "1.5kg": how a weight is said out loud."""
    if kilos < 1:
        return f"{int(round(kilos * 1000))}g"
    return f"{kilos:g}kg"
def _legs(memory, understood):
    """A chicken leg is a piece, not a bird: a drumstick and a whole leg take different times, and
    the whole-bird rule (20 minutes per 500g plus 20) is wrong for both.

    The oven time is only right for the oven: a line that names another way of cooking it gets
    that method's time, because "how long to boil chicken legs" was being told to roast them.
    Cooked from frozen takes longer whatever the method, and the follow-up after a method answer
    ("does that change if theyre from frozen") is the same question with one word added."""
    reply = _legs_method(understood)
    words = " ".join(understood.get("words") or [])
    if "frozen" in words or "freezer" in words:
        reply += " From frozen, add about 10 minutes and check at the bone before you serve it."
    return reply


def _legs_method(understood):
    """The time for the way of cooking the line names, the oven when it names none."""
    words = " ".join(understood.get("words") or [])
    small = "drumstick" in words or "drumsticks" in words
    done = ("It is done when the juices at the thickest part run clear and the meat pulls away from "
            "the bone - if you have a thermometer, 74C.")
    if "boil" in words or "boiling" in words or "poach" in words or "poached" in words or \
            "simmer" in words or "simmering" in words:
        return (f"Simmer {'drumsticks' if small else 'the legs'} in salted water for "
                f"{'20 to 25' if small else '25 to 30'} minutes. {done}")
    if "grill" in words or "grilled" in words or "grilling" in words or "barbecue" in words or \
            "barbeque" in words or "bbq" in words:
        return (f"Over medium heat, a {'drumstick' if small else 'leg'} takes about "
                f"{'8 to 10 minutes a side' if not small else '10 minutes a side'}, turning once and "
                f"moving it off the hottest spot if it colours too fast. {done}")
    if "slow" in words or "crockpot" in words or "crock" in words:
        return ("In a slow cooker, legs take 3 to 4 hours on low with a splash of stock or a tin of "
                f"tomatoes; drumsticks are done nearer 2 to 3. {done}")
    if "air" in words:
        return (f"In an air fryer, {'drumsticks' if small else 'legs'} take "
                f"{'20 to 25' if small else '25 to 30'} minutes at 190C, turned once, until the skin "
                f"is crisp. {done}")
    if small:
        return ("Roast drumsticks at 200C (180C fan) for 25 to 30 minutes, skin side up and spaced "
                "out, until the skin is crisp and the juices at the bone run clear. Salt the skin "
                "first, and give them a turn halfway if your oven has a hot spot.")
    return ("A whole chicken leg takes 35 to 40 minutes at 200C (180C fan), skin side up: a "
            "drumstick alone is 25 to 30. It is done when the juices at the thickest part run "
            "clear and the meat pulls away from the bone - if you have a thermometer, 74C. Salt "
            "the skin and don't crowd the tray, or it steams instead of crisping.")


# "chicken tender" is two senses: the piece, which has an oven time, and the texture of the
# meat ("how do i make my chicken tender"), which has none. The plural, or the piece named on
# its own, is the piece; "tender" standing after "my", "so" or "is" is the adjective.
TENDER_ADJECTIVE_BEFORE = frozenset(("my", "so", "really", "very", "more", "most", "too", "not",
                                     "is", "super", "nice", "them", "properly", "and", "are"))


def _tenders_are_a_piece(understood):
    """True when the line asks about the piece, false when it says tender as a texture."""
    words = [w.lower() for w in (understood.get("words") or []) if isinstance(w, str)]
    if "tenders" in words or "strips" in words or "goujons" in words:
        return True
    for i, word in enumerate(words):
        if word == "chicken" and i + 1 < len(words) and words[i + 1] in ("tender", "strip",
                                                                        "goujon"):
            before = words[i - 1] if i else ""
            return before not in TENDER_ADJECTIVE_BEFORE
    # no piece word at all: "how do i cook beef so it is tender" says tender about the meat
    return False


# A chicken tender is a thin piece, so the whole-bird rule (20 minutes per 500g plus 20) is
# nearly an hour too long for it: "how do i cook chicken tenders" was given the time for a 2kg
# bird. Each way of cooking it has its own minutes, the same way a leg's do.
def _tenders_method(memory, understood):
    """The time for the way of cooking the line names, the oven when it names none."""
    words = " ".join(understood.get("words") or [])
    done = ("They are done when the middle is 74C and no pink is left - cut the thickest one "
            "open if you have no thermometer.")
    if "air" in words or "airfryer" in words or "airfryers" in words:
        return ("In an air fryer, chicken tenders take 9 to 10 minutes at 190C in a single layer, "
                "shaken once halfway. " + done)
    if "grill" in words or "grilled" in words or "grilling" in words:
        return ("Under a hot grill, chicken tenders take 4 to 5 minutes a side, turned once. " + done)
    if ("fry" in words or "fried" in words or "frying" in words or "pan" in words
            or "shallow" in words):
        return ("In a frying pan over a medium heat, chicken tenders take 3 to 4 minutes a side, "
                "until golden outside and white in the middle. " + done)
    return ("Chicken tenders are thin, so 10 to 12 minutes in a 200C (180C fan) oven is enough: "
            "spread out on an oiled tray and turned once halfway. " + done)


def _bird_weight(understood):
    """The weight of the bird, in kilos, when the line gives one: "a 1.5kg chicken"."""
    for number in understood.get("numbers") or []:
        value, unit = number.get("value"), number.get("unit")
        if not isinstance(value, (int, float)) or value <= 0:
            continue
        kilos = {"kg": value, "g": value / 1000.0, "lb": value * 0.4536,
                 "oz": value * 0.02835}.get(unit)
        if kilos and 0.4 <= kilos <= 12:
            said = str(number.get("text") or "")
            # The reading keeps the words the person typed, and for "half a kilo" that is the
            # bare "half": read back as "a half bird takes 40 minutes" it says the wrong thing.
            # The weight itself says it right, so it is used unless the words name a unit.
            if not re.search(r"\d|\b(?:kilo\w*|kg|g|lb|lbs|pound|pounds|oz|ounce|ounces)\b",
                             said.lower()):
                said = _weight_words(kilos)
            # "a kilo of pork" is answered "so a kilo one is about 50 minutes": the article is
            # the count, so saying it again after "a" reads as "a a kilo one".
            ours = re.match(r"(?:a|an)\s+(.+)$", said.lower())
            if ours:
                said = ours.group(1)
            return kilos, said
    return None


def _hours_words(hours):
    """18 -> "18 hours", 36 -> "a day and a half", 60 -> "two and a half days"."""
    hours = int(round(hours / 3.0)) * 3
    if hours < 24:
        return f"{hours} hours"
    days, rest = divmod(hours, 24)
    whole = {1: "a day", 2: "two days", 3: "three days", 4: "four days", 5: "five days"}
    half = {1: "a day and a half", 2: "two and a half days", 3: "three and a half days"}
    if rest == 0 and days in whole:
        return whole[days]
    if rest == 12 and days in half:
        return half[days]
    return f"{hours} hours"


def _in_words(minutes):
    """80 -> "1 hour 20 minutes", 100 -> "1 hour 40 minutes", 45 -> "45 minutes"."""
    minutes = int(round(minutes / 5.0)) * 5
    hours, rest = divmod(minutes, 60)
    if not hours:
        return f"{rest} minutes"
    hours_text = f"{hours} hour" + ("" if hours == 1 else "s")
    # "1 hour 40" on its end reads as a figure cut off: the same reply is given on its own as
    # the answer to "how long will it take", and a bare "1 hour 40." there loses its unit.
    return f"{hours_text} {rest} minutes" if rest else hours_text


def _chicken_time(memory, understood):
    """A whole chicken: 20 minutes per 500g plus 20, at 190C, for the weight they gave.

    "Is 4 pounds a lot for a chicken" carries a figure in pounds and asks whether it is dear, so
    the four pounds is money and not the bird: the minutes in the oven answer a question nobody
    asked, and the price row answers this one.
    """
    said_line = str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    if a_price_is_judged(said_line):
        return None
    check = ("Check the thigh reads 74C on a thermometer and the juices run clear, then rest it "
             "for 15 minutes before carving.")
    kilos, said = _bird_weight(understood) or (2.0, "2kg")
    return ("About 20 minutes per 500g plus 20 minutes at 190C (170C fan), so a "
            f"{said} bird takes roughly {_in_words(20 * (kilos / 0.5) + 20)}. " + check)


# What to cook from what is already in the kitchen, keyed by ingredient rather than by
# phrasing: "what can I make with mince", "quick tea with chicken and rice" and
# "I have potatoes and eggs, any ideas" all reach the same table. Each idea is a short
# recipe in the first sentence and the shortcut in the second, in STYLE.md's voice.


# What goes with the main thing on the plate. "Something to go with roast chicken" is one of
# the most asked kitchen questions and it was getting the roast timings instead: the line names a
# dish but asks about the rest of the plate. Ordered most specific first, because "roast chicken"
# has to win over "chicken" and "salmon" over "fish".

# What to put *on* the meat rather than beside it. "What goes with lamb" is the sides table, but
# "what spice goes with lamb" and "seasoning for lamb" were answered with new potatoes and mint -
# the rest of the plate - and "what spice for beef" with a shrug. The line asks about the herbs and
# spices, so the same entry answers with those instead. Ordered most specific first, and read by
# the longest name in the line, the way the sides table is.
# A bare "season" is not enough: a season is episodes, a league and the close season for fishing.
# "what is the close season for fishing" reached this table, read "fish" and answered with lemon
# and dill instead of the rod licence, so the verb is what the season has to be - season a chicken,
# season it, seasoned - and the noun "seasoning" carries the rest.
SEASONING_ASKS = re.compile(
    r"\b(?:spices?|herbs?|seasoning|flavours?|flavors?|rub|marinade)\b"
    r"|\bseason(?:ed)?\s+(?:a|an|the|it|them|my|your|with|before|after|well|up)\b"
    r"|\bhow\s+(?:do|to|should)\s+(?:i|you)\s+season\b"
    r"|\bput\s+on\b")



# "how do i make a dry rub" names no food at all, and the answer is the method: what goes into
# one, in what proportion, and what to leave out. It was the blister card, because "rub" is a
# word a new pair of shoes also needs.
_A_RUB = (
    "A dry rub is salt, sugar, pepper and paprika in roughly equal parts, then whatever else the "
    "food wants - garlic powder, cumin, mustard powder, chilli, dried thyme. About a tablespoon "
    "of rub covers a kilogram of meat: rub it on with a little oil, leave it an hour or overnight "
    "in the fridge, and keep the sugar under a fifth of the mix if it is going on a hot barbecue, "
    "because sugar burns before the meat is done.")


def _a_seasoning(text):
    """The seasoning answer for the food this line names, or None when it names none I know."""
    best = None
    for names, reply in SEASONINGS:
        for name in names:
            if re.search(r"\b" + re.escape(name) + r"\b", text) and (
                    best is None or len(name) > best[0]):
                best = (len(name), reply)
    if best:
        return best[1]
    if re.search(r"\b(?:dry rub|spice rub|make a rub|what goes in a rub|rub recipe)\b", text):
        return _A_RUB
    return None


# The ways a line asks about the rest of the plate rather than about the dish itself.
SIDE_ASKS = re.compile(
    r"\b(?:go|goes|going|went)\s+(?:well\s+|nicely\s+|best\s+)?with\b"
    r"|\b(?:what|which)\s+(?:side|sides)\b"
    r"|\bside\s+(?:dish|dishes|for|to)\b|\bsides\s+(?:for|to|with)\b"
    r"|\bserve\s+(?:it\s+|them\s+|this\s+)?with\b|\bserving\s+with\b"
    r"|\bto\s+serve\s+with\b|\balongside\b|\bon\s+the\s+side\b"
    r"|\bpairs\s+with\b|\bwhat\s+(?:can|should)\s+i\s+(?:have|serve)\s+with\b")

# A plate takes this many people before one pan stops being enough, so only six or more counts as
# a crowd. The small numbers are read as well as the large ones, because the count in the line has to win
# over a phrase that only suggests one: "dinner party for four" matched "dinner party", which
# stands for eight, and the card told a table of four that the dish "feeds eight from one oven".
# Reading it as four also lets a count of three to five reach the meal table at all - "dinner for
# four", "supper for four" and "cooking for four" all reached the store, which said the line back.
_ONES = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine"}
_TEENS = {10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
          15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen"}
_TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy",
         80: "eighty", 90: "ninety"}


def _spelled_counts():
    """Every count a person spells out, from two up to a hundred.

    The written-out numbers used to stop at twenty, so "dinner for thirty people" was not a count
    at all and got the answer for one plate: it is the same question as "for twenty", read the
    way a typed number is read.
    """
    counts = {word: value for words in (_ONES, _TEENS, _TENS) for value, word in words.items()
              if value >= 2}
    for tens, tens_word in _TENS.items():
        for one, one_word in _ONES.items():
            counts[tens_word + " " + one_word] = tens + one
    counts["hundred"] = 100
    counts["a hundred"] = 100
    return counts


_CROWD_NUMBERS = _spelled_counts()
# Longest first, so "thirty five" is read before "thirty".
_CROWD_SPELLED = "|".join(sorted(_CROWD_NUMBERS, key=len, reverse=True))
_CROWD_FOR = re.compile(r"\bfor\s+(" + _CROWD_SPELLED + r")\b")
_CROWD_WITHIN = re.compile(r"\b(" + _CROWD_SPELLED
                           + r")\s+(?:people|of us|adults|guests|coming)\b")
_CROWD_PHRASES = ("for a crowd", "a crowd", "big group", "lots of people", "loads of people",
                  "a dozen",
                  "dinner party", "buffet", "guests", "guest coming", "guests coming",
                  "people coming", "people round", "family over", "the in laws", "in-laws",
                  "entertaining", "everyone is coming", "everyone's coming", "a party",
                  "whole family", "big family", "family dinner", "big dinner", "large family",
                  "extended family",
                  # "im having friends over for dinner" names a table of people without a count:
                  # the company is the number, so it is not a question for a ten-minute dinner.
                  # The hosting shapes only: "i saw my friends over the weekend" is not a table.
                  "having friends", "having people", "friends round", "friends coming",
                  "family round", "family coming", "friends over for", "friends over to",
                  "people over for", "people over to", "mates over", "mates round")
# A birthday or a wake asking for dinner is not a ten-minute dinner either: the question is what
# to cook for several people on a day that matters.
_OCCASIONS = ("birthday", "anniversary", "christening", "wedding", "retirement",
              "graduation", "mother's day", "mothers day", "father's day", "fathers day",
              "christmas", "easter", "thanksgiving", "wake", "funeral", "celebration",
              "special occasion")


# What a number after "for" is when it is not people. "Dinner for 8" is a table and "cook it for
# 20 minutes" is a time, and both say "for <number>": the word after the number is what tells them
# apart. Without this, "what can i eat for 500 calories" was five hundred people to feed and got
# the one-big-oven-dish answer, and every "fry it for 5 minutes" line carried a table of five.
_NOT_A_TABLE = ("minute", "minutes", "min", "mins", "hour", "hours", "hr", "hrs", "second",
                "seconds", "sec", "secs", "calorie", "calories", "cal", "cals", "kcal",
                "kilo", "kilos", "kilogram", "kilograms", "kg", "gram", "grams", "g", "mg",
                "litre", "litres", "liter", "liters", "ml", "oz", "ounce", "ounces", "lb",
                "lbs", "pound", "pounds", "degree", "degrees", "c", "f", "cm", "mm", "inch",
                "inches", "quid", "dollar", "dollars", "euro", "euros", "pence", "pennies",
                "slices", "slice", "pieces", "piece", "tins", "tin", "cans", "can", "spoons",
                "spoon", "tablespoons", "teaspoons")


def _people_after(text, end):
    """True when what follows the count at `end` is not a unit, so the number is people.

    "Dinner for 8" is a table and "cook it for 20 minutes" is a time, and both say "for <number>":
    the word after the number is what tells them apart. Without this, "what can i eat for 500
    calories" was five hundred people to feed and got the one-big-oven-dish answer, and every
    "fry it for 5 minutes" line carried a table of five.
    """
    rest = text[end:].strip().split()
    after = rest[0].strip(".,!?;:").lower() if rest else ""
    return after not in _NOT_A_TABLE


def _crowd(text):
    """How many people the line is cooking for, or 0 when it is an ordinary dinner."""
    text = str(text or "").lower().replace("-", " ")
    numbers = [int(match.group(1)) for match in re.finditer(r"\bfor\s+(\d{1,3})\b", text)
               if _people_after(text, match.end())]
    numbers += [_CROWD_NUMBERS[match.group(1)] for match in _CROWD_FOR.finditer(text)
                if _people_after(text, match.end())]
    # "eight people coming", "ten of us", "twelve guests": the count is in the line even when
    # nobody says "for".
    numbers += [_CROWD_NUMBERS[word] for word in _CROWD_WITHIN.findall(text)]
    # The same count typed as a number: "theres 14 of us for dinner", "12 people coming".
    for count in re.findall(r"\b(\d{1,3})\s+(?:people|of us|adults|guests|coming)\b", text):
        numbers.append(int(count))
    # Every group of people the line names adds up: "with 4 adults and 3 kids" is seven at the
    # table, and counting only the adults put the shopping 600 g short. The reader is the
    # portion maths' own, so a count answers the same whoever asks about it.
    grouped = people_in_groups(text)
    if grouped:
        numbers.append(grouped)
    if numbers:
        return max(numbers)
    if any(phrase in text for phrase in _CROWD_PHRASES):
        return 6
    return 0


# Ways of saying there are people to feed. With a count under six these are still a table
# question when the line asks what to cook: four people at the table is one oven dish, not a
# list of dinners for one. "dinner for four" has none of these, and stays ordinary cooking.
_TABLE_PHRASES = ("people coming", "people round", "people over", "people for dinner",
                  "people to feed", "people to cook for", "of us", "guests coming",
                  "guests for dinner")


# A table named by the people at it, not counted: "i'm cooking for my in laws on sunday" is the
# same dinner-for-a-table question as "i'm cooking for eight", and the reason to ask it is that
# people who are not your household are coming. It is the relation after "for" that says so, so
# a bare "cooking for one" and "cooking for the dog" stay out of it.
_NAMED_TABLE = re.compile(
    r"\b(?:cook|cooking|cooked|make|making|made|bake|baking|hosting|having|feed|feeding)\b"
    r"[^.?!]{0,24}\b(?:for|to)\s+(?:my|our|the|his|her|their)\s+(?:\w+'?s\s+)?"
    r"(?:in\s?laws?|parents?|mums?|moms?|mothers?|dads?|fathers?|folks|familys?|relatives?|"
    r"friends?|neighbou?rs?|guests?|colleagues|workmates|sisters?|brothers?|grandparents?)\b"
    r"|\b(?:my|our)\s+(?:\w+'?s\s+)?(?:in\s?laws?|parents?|mums?|moms?|mothers?|dads?|"
    r"fathers?|folks|familys?|friends?|neighbou?rs?|grandparents?)\b[^.?!]{0,24}"
    r"\b(?:coming|come|round|over|visiting|staying)\b[^.?!]{0,18}"
    r"\b(?:dinner|lunch|tea|supper|meal|eat)\b",
    re.IGNORECASE)


def _named_table(text):
    """True when the line names the people it is cooking for, instead of a number."""
    return bool(_NAMED_TABLE.search(str(text or "")))


def _table_text(text):
    """True when the line is about feeding a table rather than one plate.

    Eight or more is a crowd on the number alone. Four or five is a table only when the line says
    people are coming and asks what to cook - "i have 4 people coming for dinner what should i
    cook" wants the one-dish answer, while "dinner for four" is an ordinary dinner.
    """
    text = str(text or "").lower()
    count = _crowd(text)
    if count >= 6:
        return True
    if not count:
        # "i'm cooking for my in laws on sunday" counts nobody, and is still a table.
        return _named_table(text)
    # Three to five is a table when the line says people or guests are coming round, in either
    # of the two ways the module already knows ("people coming", "dinner party"): the count was
    # read as four and then stood down to the ten-minute list, which is the wrong card for four
    # people somebody is cooking for.
    # "of us" is a table counted by the people at it: "whats a good lunch for 4 of us" and
    # "lunch for 3 of us" are not one person's lunchbox, and with the lunchbox row standing down
    # for them there was nothing else to take the line. It is read here, where the count is
    # known, and not in _CROWD_PHRASES: that list is also the default six for a line with no
    # number, and a table of four counted as six was handed the six-player games.
    if count >= 3 and any(phrase in text for phrase in _CROWD_PHRASES + ("of us",)):
        return True
    if any(phrase in text for phrase in _TABLE_PHRASES) and any(
            word in text for word in ("cook", "cooking", "make", "feed", "serve")):
        return True
    # The ask can be a lunch as readily as a dinner: "whats a good lunch for 4 of us" names no
    # word of cooking at all, and with the lunchbox row standing down for the count of us it
    # reached nothing until the meal itself counted as the ask. Three or more, because "lunch
    # for 2 of us" is a sandwich apiece and not a dish to cook for a table.
    return (count >= 3 and any(phrase in text for phrase in _TABLE_PHRASES)
            and any(word in text for word in ("lunch", "lunches", "meal", "meals", "eat")))


# The verbs that make a table line a cooking question.
_CROWD_VERBS = ("cook", "cooking", "make", "serve", "feed", "dinner", "tea", "supper",
                "lunch", "eat", "eating")

# A table line can also be all nouns: "what food would be easy for twenty people", "easy food
# for twenty people", "what food is easy for a crowd". The count is what makes it a cooking
# question, so a food noun is enough without a verb. Before this, four of those phrasings got
# nothing but a search hedge or a "Got it", while "what should i cook for 20 people" answered.
_CROWD_FOOD = ("food", "foods", "meal", "meals", "dish", "dishes", "buffet", "nibbles",
               "finger food", "spread", "platter", "platters", "menu")

# Not every line with a count and a food noun is a table to cook for: "how much food for 30
# people" is the portions figure (units.py answers it, in kilos), and food poisoning, a food
# bank and the dog's dinner have their own answers.
_CROWD_QUANTITY = ("how much", "how many", "amount", "quantity", "weighs", "weight", "grams",
                   " kg", "kilos", "per head", "per person", "per guest")
_CROWD_NOT_A_MEAL = ("poison", "poisoning", "hygiene", "allergy", "allergic", "reaction",
                     "ill", "sick", "sickness", "waste", "bin", "bins", "food bank",
                     "dog food", "cat food", "pet food", "baby food", "fast food")


def _crowd_ask(clean):
    """True for a how-to line that is really a dinner for a table.

    "how do i cook for a crowd" is a how-to in form and a dinner question in substance: at a
    table of eight the question is what to cook, not which pan to use. A line that only states
    the table ("i have 12 people over for dinner") asks it too, so dinner and tea count here.
    """
    text = str(clean or "").lower()
    if not _table_text(text):
        return False
    if any(word in text for word in _CROWD_VERBS):
        return True
    if any(phrase in text for phrase in _CROWD_NOT_A_MEAL):
        return False
    if any(word in text for word in _CROWD_FOOD):
        return not any(phrase in text for phrase in _CROWD_QUANTITY)
    return False


_CROWD_WORDS = {v: k for k, v in _CROWD_NUMBERS.items()}


def _trays(count):
    """How many trays the table needs, so a table of twelve is not told about eight."""
    if count >= 13:
        return ("two or three trays of it, on the top and middle shelves, or one dish made in "
                "the biggest pot you own")
    if count >= 9:
        return ("two trays of it, on the top and middle shelves and swapped halfway, to feed "
                + _CROWD_WORDS.get(count, str(count)))
    if count and count <= 5:
        # A table of four is one tray with plenty left over, and telling them it "feeds eight"
        # reads as though nobody read the number in the line.
        return ("one tray of it is plenty for " + _CROWD_WORDS.get(count, str(count)))
    if not count:
        # A table named by its people ("cooking for my in laws") carries no number, so claim
        # none: "feeds eight" to two guests reads as though nobody read the line.
        return "which does four to six, so count the potatoes yourself"
    return "which feeds eight from one oven"


def _crowd_meal(banned, occasion, count=0):
    """One dish that scales, for a birthday or a table of eight, instead of a ten-minute dinner."""
    vegetarian = bool({"meat", "chicken", "beef", "pork", "lamb", "mince", "bacon",
                       "sausage", "sausages", "ham", "turkey", "fish", "salmon", "cod",
                       "tuna", "prawn", "prawns"} & banned)
    if vegetarian:
        # "a big lasagne" to a vegetarian is a dish of unknown filling: name the meat-free one
        dish = ("a big mushroom and lentil lasagne or a chickpea and vegetable traybake, made in "
                "the largest dish you own")
        amount = "about 300g of the dish per person"
    else:
        dish = ("a tray of chicken thighs or sausages with halved potatoes, peppers and onions at "
                "200C (180C fan) for 45 minutes")
        amount = "about 200g of meat and a big potato each"
    reply = ("Cook one big oven dish rather than several pans: " + dish + ", " + _trays(count)
             + ". Allow " + amount + ", add a loaf of bread and a bowl of salad, and write the "
             "times down so nothing needs the oven at once.")
    if occasion:
        reply += (" Anything that can be made that morning - a chilli, a stew, a lasagne - just "
                  "gets reheated, which leaves the day free.")
    return reply


def _occasion(text):
    """True when the line is a day that matters: a birthday, a wake, or a "70th"."""
    if any(word in text for word in _OCCASIONS):
        return True
    # "my mums 70th next saturday" names the day by its number, not by the word birthday.
    return bool(re.search(r"\b\d{1,3}(?:st|nd|rd|th)\b", text))


def _crowd_or_any(text, banned):
    """The fallback list, unless the line is a meal for a table or an occasion."""
    if _table_text(text):
        return _crowd_meal(banned, _occasion(text), _crowd(text))
    if _occasion(text) and any(
            phrase in text for phrase in ("what should i cook", "what can i cook",
                                          "what shall i cook", "what to cook", "what to make",
                                          "meal", "dinner", "cook", "no idea")):
        # "it's my mum's 70th birthday, what should I cook" names no ingredient and no number:
        # a ten-minute dinner is the wrong answer to a day like that.
        return _crowd_meal(banned, True, _crowd(text))
    return _any_meal(banned)


# "How many minutes a side for steak" is a timing question that happens to say "a side", and the
# pair row's key holds the phrase "side for": steak, pork chops and chicken were all answered with
# what to serve beside them when they asked how long to cook. A line that asks a time or a heat is
# the timings' question, so the pair row stands down for it.
A_TIME_OR_HEAT_ASK = re.compile(
    r"\b(how many minutes?|how many mins?|how long|how much time|minutes a side|mins a side|"
    r"minutes per side|what temperature|what temp|what heat|gas mark|how do i time)\b")


def _sides(memory, understood):
    """What to put beside the dish a line names, or None when it names none I know."""
    text = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
    # "a pain in my side" and "side effects" are not about the plate.
    if re.search(r"\bpain\b|\bstitch\b|\bside effects?\b|\bleft side\b|\bright side\b", text):
        return None
    # "how many minutes a side for steak" is a time, not the rest of the plate.
    if A_TIME_OR_HEAT_ASK.search(text):
        return None
    # "what spice goes with lamb" is the herbs, not the new potatoes: the same entry, told which
    # of the two questions it is answering.
    if SEASONING_ASKS.search(text):
        seasoned = _a_seasoning(text)
        if seasoned:
            return seasoned
    table = _table_side(text)
    plan = _plan_side(memory, text)
    # The plan names the one dish the line is about, so its side answers first: the table reads
    # the first food word it finds, and a bare "chicken" in it was handing "what goes with a
    # chicken curry" the roast chicken's potatoes. A line whose dish has no plan, or whose plan
    # has no side, falls through to the table.
    if plan:
        return plan[1]
    if table:
        return table[1]
    # A pairing ask about a food with no dish of its own and no side in the table is not a punt:
    # "what goes with cheese", "what goes with penne", "what cheese goes with apple" and "what
    # sauce goes with lentils" were four "I'd rather not guess" lines, and the rule underneath
    # the tables is the answer - fat wants acid, plain starch wants something wet on top, and
    # anything else wants one of each.
    from . import dishes
    if dishes.asks_for_a_side_of_a_food(text):
        return dishes.general_sides(text)
    return None


def plan_side(memory, text):
    """The side the conversation's own dish has, or None: the public face of _plan_side."""
    found = _plan_side(memory, str(text or "").lower())
    return found[1] if found else None


def side_for(memory, text):
    """What to put beside the dish this conversation is cooking, or None.

    A plan's own side comes first. The plans do not all carry one (steak's does not), so the
    sides table is asked about the conversation's own lines as well: a follow-up that says only
    "what can i have with it" has no dish of its own for the table to read.
    """
    side = plan_side(memory, text)
    if side:
        return side
    from . import dishes
    for line in [str(text or "")] + list(dishes.recent_texts(memory))[:3]:
        found = _table_side(line.lower())
        if found:
            return found[1]
    return None


def _table_side(text):
    """The longest name in the sides table this line uses, and its reply."""
    best = None
    for names, reply in SIDES:
        for name in names:
            if re.search(r"\b" + re.escape(name) + r"\b", text) and (
                    best is None or len(name) > best[0]):
                best = (len(name), reply)
    return best


def _plan_side(memory, text):
    """The side for the one dish this line names, with that plan's own name for it.

    One dish, read the way the rest of the kitchen reads a dish (dishes.dish_in), and only that
    dish's plan: walking the plans for the first name found in the line let a bare "chicken" hand
    "what goes with a chicken curry" the roast chicken's potatoes. A dish whose plan has no side
    of its own passes, so the sides table can answer for it instead of another plan's side.
    """
    from . import dishes
    lines = [text]
    if isinstance(memory, dict):
        lines += list(dishes.recent_texts(memory))[:2]
    for line in lines:
        name = dishes.dish_in(line)
        plan = dishes.PLANS.get(name or "")
        if not plan:
            continue
        if not plan.get("sides"):
            return None
        names = [wanted for group in plan.get("names", ()) for wanted in group]
        return (len(name), plan["sides"])
    return None


# The reply when the line asks for meal ideas but does not name anything in the kitchen.
ANY_MEAL = ("Ten-minute dinners: pasta with garlic, chilli and olive oil; eggs on toast; or cold "
            "rice fried with frozen veg, an egg and soy sauce. Tell me what is in the fridge and "
            "I will pick one.")

# Diabetes rules no food out, so there is no ban for the dish table to work around: it changes
# how much of the plate is starch. The ten-minute list is the wrong shape of answer, and the
# health table's plate rule answers a different question (what can I eat at all, not what to
# cook), so cooking for a diabetic guest is its own answer.
DIABETIC_PLATE = (
    "Cook the same sort of dinner as for anyone, with the starchy part smaller and the "
    "vegetables bigger: chicken or fish with two veg, a chilli with beans instead of rice, or an "
    "omelette and salad. Halve the potatoes, rice or pasta rather than cutting them out, go "
    "wholegrain where you can, skip the sugary drinks, and keep pudding small - and ask them "
    "what they usually do rather than guessing.")

DIABETES_WORDS = ("diabetic", "diabetics", "diabetes", "sugar diabetes", "type 1", "type 2",
                  "blood sugar")


def _says_diabetes(text):
    """True when this line, or the conversation before it, named diabetes.

    Coeliac and a nut allergy hold on a follow-up because the ban they spell out is read from
    the last few turns; diabetes spells out no ban, so the words that say it are read the same
    way. "What should i cook for her" after "my sister is diabetic" is the same question.
    """
    folded = " " + re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip() + " "
    return any(" %s " % word in folded for word in DIABETES_WORDS)

# A week is a different question from tonight: it is asked with a shop, a plan or a freezer in
# mind, and answering it with one dinner leaves the person where they started.
PLAN_WEEK = ("Pick four dinners you already cook and plan the week on one list before you shop, "
             "then cook once for two nights: a big chilli or a tray of roast vegetables tonight, "
             "the rest in "
             "a pasta bake or wraps tomorrow, and one night that needs no cooking at all. Put one "
             "double batch in the freezer for the night you are late home, and keep two fallbacks "
             "in the cupboard - pasta and a tin of tomatoes, rice and eggs - for the night the "
             "plan falls apart.")

PLAN_CHEAP = ("Cheap weeks come from the same eight things: rice, pasta, tins of tomatoes, "
              "chickpeas or lentils, onions, carrots, frozen veg and eggs. Pick four dinners you "
              "already cook from those and put them on the fridge: a big chilli or bolognese "
              "stretched with lentils so it eats twice, a tray of roast vegetables with the rest "
              "in a pasta bake, a lentil dhal, and beans on toast. That is about 20 pounds a head "
              "for the week, and nothing in it goes off.")

PLAN_BATCH = ("Cook two big pots on one afternoon and the week is half done: a chilli or "
              "bolognese and a curry or dhal, each cooled and split into portions, then frozen "
              "flat in bags so they thaw in minutes. Cook rice and pasta fresh while a portion "
              "reheats, label the bags with the date, and eat them within three months.")

# A month named in the line does not make it a holiday: "cheap meals for a week in january" is
# the new-year meal plan and "a week in spain in october" is a holiday, and the word that differs
# is a meal word, not a place. So the twelve months stand this row down only when the line names
# nothing to eat, which is the shape of a line that is asking where to go.
MONTHS_SAID = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november"
    r"|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b")
# A line that asks where to go is asking about a place, not a shop - unless the place it names is
# a shop for food: "where can i go for cheap food" came back with this row's eight cheap foods, and
# standing the row down on the phrase alone turned a shopping answer into a search hedge.
GOING_SAID = re.compile(
    r"\bwhere (?:should|can|could|shall|do|to) (?:i|we)? ?(?:go|get|find|shop)\b"
    r"|\bwhere to (?:go|shop)\b|\bweeks? abroad\b")
# The words that say the week is about eating: the plural is undone by _fold, so the singulars
# are enough here.
EATING_WORDS = frozenset("meal dinner cook cooking eat eating food shop shopping menu recipe "
                         "supper lunch tea feed leftover batch portion".split())
PLAN_WORDS = frozenset("batch batches batchcook freezer freeze freezing portion portions".split())
CHEAP_PLAN_WORDS = frozenset("cheap cheapest skint budget broke money afford tight".split())
TONIGHT_WORDS = frozenset("tonight tonite tnite today now".split())

# A hurry is a request for what fits in the time, not a shrug: "i only have 20 minutes to cook"
# and "dinner in 15 minutes" want a dinner that is ready when the clock runs out.
TIME_PHRASES = (("quarter of an hour", 15), ("half an hour", 30), ("an hour", 60))
TIME_WORDS = (("forty five", 45), ("forty", 40), ("thirty", 30), ("twenty five", 25),
              ("twenty", 20), ("eighteen", 18), ("fifteen", 15), ("twelve", 12), ("ten", 10),
              ("five", 5))
# The reply names the minutes the line gave itself: "i only have 20 minutes to cook" was answered
# with "Twenty-five minutes is enough for ...", which reads as if we had moved the deadline. Under
# twenty-five minutes the roast is left out too, because it does not fit in twenty.
TIME_TWENTY = ("Twenty minutes is enough for: a stir-fry, with the rice on before anything else; "
               "pasta with garlic, chilli and a tin of tomatoes; or an omelette with bread and "
               "salad, which is the quickest of the three.")
TIME_SOON = ("Twenty-five minutes is enough for: a stir-fry, with the rice on before anything "
             "else; pasta with garlic, chilli and a tin of tomatoes; an omelette with bread and "
             "salad; or vegetables cut small and roasted 25 minutes at 200C while couscous "
             "steeps in the same time.")
TIME_MIDDLING = ("Half an hour is enough for: chicken pieces or sausages in the oven while the "
                 "potatoes boil, a tray of vegetables cut small roasted with couscous, or pasta "
                 "baked with a tin of tomatoes and cheese. Put the oven on first and the kettle "
                 "second, and with an hour you can leave a chilli or a curry to simmer.")


def _minutes_named(said):
    """How many minutes the line gives itself, or None when it names no time at all."""
    found = re.search(r"\b(\d{1,3})\s*(?:minutes?|mins?)\b", said)
    if found:
        return int(found.group(1))
    for phrase, minutes in TIME_PHRASES:
        if phrase in said:
            return minutes
    for phrase, minutes in TIME_WORDS:
        if re.search(r"\b" + phrase + r"\b", said):
            return minutes
    return None


def _time_budget(memory, understood, text=None):
    """What fits in the minutes the line gives itself, or None when it names no hurry."""
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    said = " ".join(_fold(word) for word in words)
    minutes = _minutes_named(said)
    if minutes is None:
        return None
    if minutes <= 15:
        return ANY_MEAL
    if minutes <= 22:
        return TIME_TWENTY
    if minutes <= 28:
        return TIME_SOON
    if minutes <= 90:
        return TIME_MIDDLING
    return None


# The dishes, not the paragraph: "cheap dinners, no cheese" was answered with a tray of roast
# vegetables and feta, because the money question and the cheese ban were read separately.
CHEAP_DISHES = (
    "a big spag bol with lentils cooked in with the mince",
    "a tray of roast vegetables with couscous and feta",
    "sausages with mash and onion gravy",
    "a chickpea and tomato curry with rice",
    "beans on toast with a poached egg",
)
CHEAP_TAIL = ("Eggs, tins, pasta, rice and frozen veg are where the money goes furthest, and the "
              "mince stretched with lentils does two dinners.")
CHEAP_TAIL_MEATFREE = ("Eggs, tins, pasta, rice and frozen veg are where the money goes furthest, "
                       "and a pot of lentils or beans does two dinners.")


def _cheap_dinners(banned=frozenset()):
    """The cheap dinners, without the ones that name a food the line or the diet ruled out."""
    dishes = [one for one in CHEAP_DISHES
              if not _mentions(one, banned) and not _bans(tuple(one.split()), one, banned)]
    if not dishes:
        dishes = list(CHEAP_DISHES)
    if _mentions(CHEAP_TAIL, banned) or _bans(("mince",), CHEAP_TAIL, banned):
        tail = CHEAP_TAIL_MEATFREE
    else:
        tail = CHEAP_TAIL
    listed = ", ".join(dishes[:-1]) + " or " + dishes[-1]
    return ("Cheap dinners that feed four for about a fiver: " + listed + ". " + tail)


# The protein answer is a list of cheap sources, which is the wrong shape for "is rice and beans a
# complete protein": that line asks whether a pair of plant foods does the whole job, and the
# answer is yes, at any meal of the day. One entry answers both, because both are the same
# question - how to get the protein without meat - asked from either end.
PROTEIN_SOURCES = ("You can get plenty without meat: eggs, milk, cheese and yogurt, a tin of beans "
                   "or chickpeas (about 15g of protein), lentils (about 18g per 100g dry), tofu, "
                   "nuts, seeds and wholegrains. Spread it over the day rather than one meal - "
                   "beans at lunch, eggs or tofu at dinner, yogurt and nuts as a snack - and there "
                   "is no need to count anything.")
PROTEIN_COMPLETE = ("Rice and beans together give all the amino acids the body cannot make itself, "
                    "and so do beans on toast, lentils with rice, and hummus with bread. You do "
                    "not have to pair them at the same meal, either: it is the day's food that "
                    "counts, not one plate, so a peanut butter sandwich and a bean chilli on the "
                    "same day is enough.")


def _protein(memory, understood):
    """Enough protein without meat, or whether a named pair of plant foods is a complete one."""
    text = str((understood or {}).get("clean") or "").lower()
    if re.search(r"\bcomplete\b", text):
        return PROTEIN_COMPLETE
    return PROTEIN_SOURCES
# An apple is the one fruit people bake whole, and the time depends on what kind it is: a Bramley
# collapses and an eater holds its shape. "how long do i bake apples for" was a search hedge, so
# the oven, the pan and the microwave are read from the line and each gets its own minutes.
BAKED_APPLES = ("Baked apples take 25 to 30 minutes at 180C (160C fan, gas 4): core them, score "
                "the skin round the middle so they do not burst, fill the hole with raisins, brown "
                "sugar and a knob of butter, and stand them in a dish with a splash of water so "
                "they do not dry out. A big Bramley needs 35 to 40 minutes and goes to a fluff, "
                "while an eater keeps its shape and is done when a knife slides in with no push.")


# The other fruit people put in the oven are the same question with a different number, and
# "how long do i roast a pear" was a search hedge because only the apple had a row. Halved and
# stoned, cut side up in a dish with sugar and a splash of water, is the method for all of them,
# so the minutes and the test for done are the whole of the difference - and the fruit the person
# named is the one the reply names.
BAKED_FRUIT = {
    "pear": ("Baked pears take 25 to 30 minutes at 180C (160C fan, gas 4): halve them and scoop "
             "the core out with a teaspoon, then sit them cut side up in a dish with a splash of "
             "water, a knob of butter and a spoon of sugar. A firm Conference needs 35 to 40 "
             "minutes and a ripe one 20, and either is done when a knife slides in with no push."),
    "plum": ("Baked plums take 15 to 20 minutes at 180C (160C fan, gas 4): halve them and take "
             "the stones out, sit them cut side up in a dish with a spoon of sugar and a splash "
             "of water. They give off a lot of juice, and that syrup is the best part; a whole "
             "one needs 10 minutes more."),
    "peach": ("Baked peaches and nectarines take 20 to 25 minutes at 180C (160C fan, gas 4): "
              "halve them and take the stones out, cut side up in a dish with a knob of butter "
              "and a spoon of sugar. A ripe one gives to a knife at 20 minutes, and a hard one "
              "needs 10 minutes more and is better poached."),
    "quince": ("Baked quince takes far longer than the softer fruit: about 1 hour 30 minutes at "
               "160C (140C fan, gas 3), halved and cored, cut side up in a dish with sugar and a "
               "splash of water. It goes from pale and hard to pink and soft, and it is done when "
               "a knife goes in with no resistance."),
}

# The pan is the other way round from the oven: the softer the fruit the shorter it takes, and a
# plum falls apart in the time a pear needs to soften at all.
STEWED_FRUIT = {
    "apple": ("Stewed or poached: peel, core and slice them, then simmer in a pan with a spoon "
              "of sugar, a splash of water and a squeeze of lemon for 8 to 10 minutes with the "
              "lid on, until they fall apart. A Bramley takes 5, and an eater holds its shape."),
    "pear": ("Stewed or poached pears: peel, halve and core them, then simmer with a spoon of "
             "sugar, a splash of water and a squeeze of lemon for 10 to 15 minutes with the lid "
             "on, until a knife goes in easily. A firm pear takes the 15, and poaching them whole "
             "in wine or syrup wants 20 to 25."),
    "plum": ("Stewed plums: halve them and take the stones out, then simmer with a spoon of sugar "
             "and a splash of water for 6 to 8 minutes with the lid on, until they slump. They "
             "fall apart quickly, so stop while they still hold their shape."),
    "peach": ("Stewed peaches: halve and stone them, then simmer with a spoon of sugar and a "
              "splash of water for 5 to 8 minutes with the lid on. The skins slip off after a "
              "minute in the hot liquid if you want them off."),
    "quince": ("Stewed quince: peel, quarter and core them, then simmer with sugar and a squeeze "
               "of lemon for 45 minutes to an hour with the lid on, until they turn pink and "
               "soft."),
}

MICROWAVED_FRUIT = {
    "apple": ("In a microwave: core them, stand them in a dish with a centimetre of water, cover "
              "it and give two medium apples 6 to 8 minutes on full power, turning them once. "
              "They go soft rather than brown, so finish them under the grill for 3 minutes if "
              "you want the tops caught."),
    "pear": ("In a microwave: halve and core them, stand them cut side up in a dish with a "
             "centimetre of water, cover it and give two halves 4 to 6 minutes on full power. "
             "They go soft rather than brown, so finish them under the grill for 3 minutes if "
             "you want the tops caught."),
    "plum": ("In a microwave: halve and stone them, stand them in a dish with a centimetre of "
             "water and a spoon of sugar, cover it and give four halves 3 to 4 minutes on full "
             "power. They collapse fast, so check them at 3."),
    "peach": ("In a microwave: halve and stone them, stand them cut side up in a dish with a "
              "centimetre of water, cover it and give two halves 4 to 6 minutes on full power. A "
              "ripe one is done at 4; a hard one is better in the oven than longer in there."),
    "quince": ("A quince will not soften in a microwave - it is too hard and too dry - so give it "
               "the oven, or the pan with sugar and lemon for 45 minutes to an hour."),
}


# A fruit on its way out is still this row's question when the line names the oven: "i have four
# peaches going soft, how long do they need in the oven" wants the minutes, not the case for
# eating a soft one. The soft words were in the avoid list on their own, which stood the row down
# for the very line that was asking it.
_SOFT_FRUIT = re.compile(r"\b(?:going soft|gone soft|soft spot|soft spots|getting soft|"
                         r"turning soft)\b")
_SOFT_FRUIT_WANTS_THE_OVEN = re.compile(
    r"\b(?:oven|bake|baked|baking|roast|roasted|roasting|stew|stewed|stewing|poach|poached|"
    r"poaching|microwave|microwaved|use up|using up|what can i do with|what can i make with|"
    r"what do i do with)\b")


def _a_soft_fruit_is_still_a_cooking_question(understood):
    """False for a soft fruit asked about keeping, true once the line names a way of cooking it."""
    text = str((understood or {}).get("clean") or "").lower()
    return bool(_SOFT_FRUIT_WANTS_THE_OVEN.search(text)) or not _SOFT_FRUIT.search(text)


def _the_baked_fruit(text):
    """Which fruit the line names, reading the ones this row knows before the garden's quince."""
    for name, fruit in (("quince", "quince"), ("nectarine", "peach"), ("peach", "peach"),
                        ("plum", "plum"), ("pear", "pear")):
        if re.search(r"\b" + name + r"(?:es|s)?\b", text):
            return fruit
    return "apple"


def _bake_fruit(memory, understood):
    """The oven time for the fruit named, the pan time for stewed, the minutes in a microwave."""
    text = str((understood or {}).get("clean") or "").lower()
    fruit = _the_baked_fruit(text)
    # boiling a fruit is stewing it, not baking it: 8 to 10 minutes in a pan, not 25 in the oven
    if re.search(r"\b(?:stew|stews|stewed|stewing|boil|boils|boiled|boiling|simmer|simmered|"
                 r"simmering|poach|poached|poaching|puree|pureed)\b", text):
        return STEWED_FRUIT[fruit]
    if re.search(r"\bmicrowave\b", text):
        return MICROWAVED_FRUIT[fruit]
    return BAKED_FRUIT.get(fruit, BAKED_APPLES)


JACKET_BAKE = (
    "Prick it, rub it with oil and salt, and bake at 200C (180C fan) for about an hour for a "
    "medium potato, until a knife slides in with no resistance. The oil and salt are what make "
    "the skin crisp; 8 minutes in the microwave first cuts the oven time to 25.")
JACKET_FILL = (
    "Cheese and beans, tuna mayo, coleslaw, chilli or last night's bolognese: butter and salt "
    "first, then the topping, and back in the oven for 5 minutes if you want the cheese melted. "
    "A wet filling wants something crisp alongside - a pickled onion, a handful of salad.")


def _jacket(understood):
    """The bake is one question and what goes in it is another, and they share an entry."""
    said = str((understood or {}).get("clean") or "").lower()
    if re.search(r"\b(fill|filling|fillings|topping|toppings|goes with|what with|put in|"
                 r"beans|cheese|tuna|coleslaw|chilli)\b", said):
        return JACKET_FILL
    return JACKET_BAKE


JAM_RECIPE = (
    "Weigh the fruit, then add the same weight of sugar and simmer it until it reaches 104 to "
    "105C, which is 10 to 15 minutes of hard boiling: test a drop on a cold plate and if it "
    "wrinkles when you push it, it is ready. Soft fruit needs a squeeze of lemon for pectin, and "
    "the jars go in hot.")
CHUTNEY_RECIPE = (
    "Chutney is fruit or veg with half its weight of sugar and enough vinegar to cover, simmered "
    "down until a spoon drawn across the pan leaves a trail - an hour or two - then potted in hot "
    "jars and left 3 to 4 weeks to mellow. The vinegar is what keeps it, so do not skimp on it.")


def _jam_make(understood):
    """Jam and chutney are the same pan of fruit and sugar with different amounts of vinegar."""
    said = str((understood or {}).get("clean") or "").lower()
    if "chutney" in said or "preserve" in said:
        return CHUTNEY_RECIPE
    return JAM_RECIPE


POACH_FISH = (
    "Poach {fish} in water that is trembling rather than bubbling, about 80C, for 6 to 8 minutes "
    "for a fillet, or 15 to 20 minutes for a whole side in a 120C oven. It is done when a knife "
    "goes into the thick end and the flakes just separate; milk, a bay leaf and a few peppercorns "
    "in the water are what a restaurant poach tastes of.")


def _poach_fish(understood):
    """"haddock poached in milk" is the same method and a different fish, so name the one said."""
    text = str((understood or {}).get("clean") or "").lower()
    for name in ("haddock", "cod", "trout", "salmon"):
        if re.search(r"\b" + name + r"\b", text):
            return POACH_FISH.format(fish=name)
    return POACH_FISH.format(fish="salmon")


MUSHROOM_WASH = (
    "Rinse them quickly under the tap and dry them on a tea towel - mushrooms take on very "
    "little water in a few seconds, and a wipe with damp kitchen paper leaves the grit in the "
    "gills. Do not leave them soaking in a bowl, which is the one thing that does make them "
    "watery, and cook them straight after.")
MUSHROOM_PEEL = (
    "No need: the skin on button, chestnut and portobello mushrooms is thin and it is flavour, so "
    "wipe or rinse them, snap out the stalk if it is woody, and slice. Peel only a field mushroom "
    "with gritty skin or a shiitake with a tough stem, and cut the stem off at the cap rather "
    "than peeling it.")


def _mushroom_wash(understood):
    """Whether to peel is a different question from whether to wash, and they share an entry."""
    said = str((understood or {}).get("clean") or "").lower()
    if re.search(r"\bpeel", said) or re.search(r"\bskin\b", said):
        return MUSHROOM_PEEL
    return MUSHROOM_WASH


def _meal_plan(memory, understood):
    """A week of dinners, a cheap week, or a batch cook, from the same three replies.

    "meal plan for the week" names nothing in the kitchen, so the pantry has nothing to build
    from; what the line wants is the shape of the week. The words that say which shape it wants
    are cheapness and the freezer, and both are read with the turns before this one, because
    "im skint this week" then "what should i plan for dinners" is still a cheap week.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    text = " ".join([str(understood.get("clean") or "").lower()] + _recent_user_turns(memory))
    folded = [_fold(word) for word in words]
    # Cheapness carries over the way "batch" does: "im skint this week" then "what should i plan
    # for dinners" is still a cheap week, and the plan for one is a different list of dinners.
    said = folded + [_fold(word) for word in re.findall(r"[a-z']+", text)]
    # A month with nothing to eat in the line is a holiday: "where should i go for a week in
    # october on a budget" came back with the eight cheap foods. The same line with a meal word
    # in it - "cheap meals for a week in january" - is the meal plan said with a month in it.
    if ((MONTHS_SAID.search(text) or GOING_SAID.search(text))
            and not set(said).intersection(EATING_WORDS)):
        return None
    if any(word in PLAN_WORDS for word in said) or re.search(r"\bfreez|\bbatch", text):
        return PLAN_BATCH
    if any(word in CHEAP_PLAN_WORDS for word in said):
        return PLAN_CHEAP
    return PLAN_WEEK


def _same(word, wanted):
    """One word matches another loosely: eggs/egg, potatoes/potato, minced/mince."""
    return bool(word) and bool(wanted) and (word == wanted or word.startswith(wanted))


_BAKED_GOODS = ("cake", "cakes", "cupcake", "cupcakes", "muffin", "muffins", "bun", "buns",
                "scone", "scones", "brownie", "brownies", "blondie", "blondies", "cookie",
                "cookies", "biscuit", "biscuits", "shortbread", "flapjack", "flapjacks",
                "sponge", "sponges", "loaf", "loaves", "bun loaf", "traybake", "traybakes",
                "cheesecake", "cheesecakes", "madeira", "doughnut", "doughnuts", "donut",
                "donuts", "fruit cake", "victoria sponge")

_NO_SPREAD_RISE = tuple(name for name in _BAKED_GOODS
                        if name not in ("cookie", "cookies", "biscuit", "biscuits", "shortbread"))

_CAKE_NAMES = ("cake", "cakes", "cupcake", "cupcakes", "sponge", "sponges", "loaf cake",
               "victoria sponge", "madeira", "fruit cake", "traybake", "traybakes")
_NO_CAKE_RISE = tuple(name for name in _NO_SPREAD_RISE if name not in _CAKE_NAMES)


_NO_LOAF_RISE = tuple(name for name in _NO_SPREAD_RISE
                      if name not in ("loaf", "loaves", "bun loaf"))


_BAKE_KEEPING = ("keep", "keeps", "keeping", "kept", "last", "lasts", "how long", "freeze",
                 "freezes", "freezer", "fridge", "refrigerate", "store", "storing", "stored",
                 "stays fresh", "stay fresh", "still good", "gone off", "go off", "use by")

# "bake" and "baked" are verbs as often as they are cakes: a pasta bake and a baked potato are not
# a sponge, so the cake answer asks for a named baked good and the bake dishes get their own below.
_BAKED = _BAKED_GOODS + ("baking", "bread", "breadcrumbs", "waffle", "waffles")

_BAKE_NAMES = (("cupcake", "cupcakes"), ("muffin", "muffins"), ("brownie", "brownies"),
               ("cookie", "cookies"), ("biscuit", "biscuits"), ("flapjack", "flapjacks"),
               ("scone", "scones"), ("sponge", "sponges"), ("loaf", "loaves"),
               ("traybake", "traybakes"), ("bread", "bread"), ("cake", "cakes"),
               ("bun", "buns"), ("tart", "tarts"), ("pie", "pies"), ("pastry", "pastry"))


def _the_bake_named(words):
    """(the bake's name, whether it takes "are"), or ("", False) when the line names none.

    The name is the plural one, because "Dry muffin is usually" is not English and "Dry muffins
    are" answers a person holding one just as well. Bread and pastry are mass nouns and keep "is".
    """
    mass = ("bread", "pastry")
    for one, many in _BAKE_NAMES:
        if any(_same(word, many) or _same(word, one) for word in words):
            return (one, False) if one in mass else (many, True)
    return "", False

# A bake or a pie is dry for its own reasons: it went in uncovered, or it stayed in too long.
_BAKE_DISH = ("pasta", "lasagne", "lasagna", "moussaka", "cannelloni", "macaroni",
              "macaroni cheese", "fish pie", "cottage pie", "shepherds pie", "shepherd's pie",
              "quiche", "frittata", "gratin")

# A rice dish that goes dry is the rice answer's: a biryani or a paella names no rice.
_RICE_DISH = ("biryani", "paella", "pilaf", "pilau", "fried rice", "risotto", "couscous")

# A dip or a paste that goes dry wants loosening, not resting under foil.
_DIP_DISH = ("hummus", "houmous", "pesto", "guacamole", "tapenade", "dip", "dips")

# And a sauce is not a roast: "my bolognese is dry", "my curry is dry", "my stew is dry" and "my
# soup is dry" were all told to take it out 5 minutes earlier and rest it under foil. A wet dish
# that has dried out wants liquid back and a lid, which is the opposite instruction.
_SAUCE_DISH = ("bolognese", "bolognaise", "bol", "ragu", "curry", "chilli", "chili", "stew",
               "casserole", "soup", "sauce", "dahl", "dal", "tagine", "goulash", "stroganoff")


# A line that asks the reason wants the cause first, not what to do with the plate: "why is my
# chicken dry" was answered with what to serve with it. The cause is what a cook can change.
def _asks_why(words):
    """True when the line asks the reason: "why", "how come", or "what did i do wrong"."""
    said = " ".join(words)
    return ("why" in words or "howcome" in words or "what did i do wrong" in said
            or "what went wrong" in said or "what am i doing wrong" in said)


def _dry(memory, understood):
    """Dry is a texture fault, and what is dry changes the answer: cake, rice, pastry or meat."""
    text = str(understood.get("clean") or "").lower()
    words = [str(word).lower() for word in (understood.get("words") or [])]
    # A biscuit comes out while the middle still looks soft, so the skewer and the foil below are
    # the wrong tests for one. The biscuit row already has the sentence for dry biscuits, dry
    # cookies and dry shortbread, so this passes and lets the row answer.
    if any(_same(word, wanted) for word in words
           for wanted in ("biscuit", "biscuits", "cookie", "cookies", "shortbread")):
        return None
    rescue = ("Serve it with something wet — gravy, a spoon of yoghurt, a squeeze of lemon and oil — "
              "and next time take it out 5 minutes earlier and rest it under foil. Dry meat or fish is "
              "nearly always overcooked, and resting is what keeps the juice in.")
    # A line that asks the reason wants the reason first: "why is my chicken dry" was answered
    # with what to serve with it, and the cause is the thing a cook can change next time.
    if _asks_why(words):
        rescue = ("Dry meat or fish is nearly always overcooked: it went past the point where the "
                  "juices set, or it was cooked hard and fast without a rest, so the juice ran out "
                  "of it. Take it out 5 minutes earlier next time and rest it under foil, and serve "
                  "this one with something wet - gravy, a spoon of yoghurt, a squeeze of lemon and "
                  "oil.")
    # The dish names here can be two words ("fish pie", "macaroni cheese"), and a line is a list
    # of single words, so the whole line is read for those as well as each word on its own.
    said = " ".join(words)
    # Overcooked pasta is not a bake that dried out: it is starch that gave up, and no amount of
    # sauce and foil brings it back. It was reaching the pasta-bake line because "pasta" is in
    # _BAKE_DISH and "overcooked" is the key.
    if any(word in ("pasta", "spaghetti", "penne", "macaroni", "tagliatelle", "fusilli", "noodles",
                    "noodle", "rice noodles", "udon") for word in words) and any(
                        word in ("overcooked", "over-cooked", "over cooked", "mushy", "soggy")
                        for word in words):
        return ("Overcooked pasta cannot be brought back, but it can be used: drain it, toss it in "
                "oil so it stops sticking, and fold it into a bake, a frittata or a soup where soft "
                "is fine. Next time salt the water properly, take it off a minute before the packet "
                "says, and taste a piece rather than trusting the clock, because a big pan of "
                "boiling water comes back to the boil slowly and the first minute is not cooking.")
    named = any(_same(word, wanted) for word in words for wanted in _BAKE_DISH) or any(
        " " in wanted and wanted in said for wanted in _BAKE_DISH)
    if named and any(
            word in ("bake", "baked", "baking", "oven", "overcooked", "over-cooked", "dry")
            for word in words):
        return ("A bake or a pie dries out when it goes in uncovered or stays in too "
                "long: stir a "
                "splash of milk or a spoon of passata through the sauce, cover it with foil and "
                "give it 10 minutes at 180C to come back. Next time keep a little bechamel back "
                "to pour over the top, and cover it for the first 20 minutes.")
    if any(_same(word, wanted) for word in words for wanted in _BAKED):
        # Gravy on a dry sponge is the wrong answer, so baking gets its own.
        thing, plural = _the_bake_named(words)
        head = ("Dry " + thing + (" are" if plural else " is")) if thing else "A dry bake is"
        return (head + " usually a minute or two too long in the oven, or a little too much "
                "flour. Take it out as soon as a skewer comes out with a crumb on it, weigh the "
                "flour rather than scooping it with a cup, and don't overbeat - and a dry bake is "
                "still good with cream, custard or something wet on it.")
    if any(word in ("rice", "ricecooker") for word in words) or any(
            _same(word, wanted) for word in words for wanted in _RICE_DISH):
        return ("Dry rice means too little water or too long on the heat: add a splash of hot water, "
                "put the lid back on and steam it for 5 minutes on the lowest heat. Next time use one "
                "and a half parts water to one of rice, lid on, 10 minutes, then rest it off the heat.")
    if any(word in _DIP_DISH for word in words):
        return ("Loosen it a spoonful at a time rather than all at once: a splash of cold water and "
                "a squeeze of lemon for hummus, or a little more oil for a pesto, blitzed or stirred "
                "through until it is soft again. A dull, dry taste is usually not enough salt or "
                "acid rather than not enough oil.")
    if any(_same(word, wanted) for word in words for wanted in _SAUCE_DISH):
        return ("A sauce that has gone dry wants liquid back, not less time in the pan: a little "
                "stock, the water the pasta cooked in, a spoon of tinned tomatoes or a splash of "
                "milk, then the lid on and five minutes at a bare simmer. A stew, a "
                "curry or a chilli tightens as it stands, so loosen it at the end rather than "
                "watering it at the start, and keep the heat low enough that it does not catch.")
    if any(_same(word, "pastry") for word in words):
        return ("Dry pastry wants a sprinkle of cold water and a 20 minute rest in the fridge, then roll "
                "it between two sheets of baking paper. Next time keep the fat cold and add water a "
                "tablespoon at a time, because pastry dries out fast once the flour is in.")
    if "safe to eat" in text or "ok to eat" in text or any(
            word in ("safe", "safely", "food-poisoning", "ill") for word in words):
        return ("Dry is a texture problem, not a safety one: if it was cooked through (75C inside, no "
                "pink meat and clear juices) it is fine cold, or reheated once until steaming. " + rescue)
    return rescue


def _bread(memory, understood):
    """One bread method, with the flour the line named: a wholemeal loaf drinks more and rises less."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)
    wholemeal = any(word in ("wholemeal", "wholewheat", "whole") for word in words) or any(
        phrase in said for phrase in ("whole wheat", "whole-wheat", "wholemeal flour"))
    brown = any(word in ("brown", "granary", "malted") for word in words)
    if wholemeal or brown:
        return ("Use 500g of wholemeal flour (or 300g wholemeal flour and 200g strong white "
                "flour, which rises more easily), 7g of dried yeast, 10g of salt and 350ml of warm "
                "water: wholemeal drinks "
                "more and takes longer, so leave it somewhere warm 2 to 3 hours until it has "
                "doubled rather than 1 to 2. Knead 10 minutes, shape it into a tin, leave it 45 "
                "minutes more, then bake at 220C (200C fan) for 35 to 40 minutes and tap the base: "
                "a hollow sound means it is done.")
    return ("Put 500g strong white flour, 7g of dried yeast, 10g of salt and 320ml of warm water in "
            "a bowl, mix it to a sticky dough and knead 10 minutes until it stops tearing. Leave it "
            "somewhere warm 1 to 2 hours until it has doubled, shape it into a tin, leave it another "
            "45 minutes, then bake at 220C (200C fan) for 30 to 35 minutes and tap the base: a "
            "hollow sound means it is done.")


# --- a dish that comes apart -------------------------------------------------------------- #
# "Falls apart" is one complaint with a different cause for every food: a fish breaks up when it
# is wet or moved too soon, a meatball when it has no binder, tofu when it was never pressed, and
# a stew is meant to. The words are in the row's key and the food decides the answer, so the rule
# covers every dish instead of the one somebody happened to write down.
COMING_APART = ("falls apart", "fall apart", "falling apart", "fell apart", "fallen apart",
                "falls to bits", "falling to bits", "fell to bits", "came apart", "coming apart",
                "breaks up", "breaking up", "breaks apart", "breaking apart", "broke up",
                "broken up", "does not hold together", "doesn't hold together",
                "doesnt hold together", "will not hold together", "won't hold together",
                "wont hold together", "not holding together", "disintegrates",
                "disintegrated", "crumbling", "crumbles")

_FISH_NAMES = ("fish", "fillets", "fillet", "white fish", "cod", "haddock", "pollock",
               "hake", "tilapia", "basa", "fish fillet", "fish fillets", "salmon",
               "fishcake", "fishcakes", "fish cake", "fish cakes", "monkfish", "plaice",
               "trout", "sea bass", "bream", "swordfish", "tuna steak")
# A stew, a pulled pork and a slow-cooker joint are supposed to come apart. The words below say
# the dish was meant to break up, so the answer is that nothing has gone wrong.
_COMING_APART_ON_PURPOSE = ("stew", "casserole", "pulled", "slow cooker", "slow cooked",
                            "braise", "braised", "tagine", "goulash", "how long", "until it")
# A soft noodle, a pea or a grain of rice gone mushy is a different fault with its own row, and
# this one would only repeat it.
_MUSHY_OWN_ROW = ("pasta", "spaghetti", "penne", "macaroni", "noodles", "noodle", "rice",
                  "peas", "beans", "lentils", "porridge", "oats", "couscous")


def _falls_apart(memory, understood):
    """A dish that comes apart, answered by the food that came apart.

    The fault is the same few words in every kitchen - falls apart, breaks up, crumbles, will not
    hold together - but the fix is not: fish is dried and left alone in a hot pan, a meatball needs
    something to bind it, tofu needs the water pressed out, a joint coming apart is a joint that is
    done, and a stew is doing what it was asked to. So the entry below is keyed on the fault words
    and on food, and this reads which food the line named.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " " + " ".join(words) + " "
    text = str(understood.get("clean") or "").lower()
    whole = said + " " + text + " "
    why = _asks_why(words)

    def names(*wanted):
        return any(_same(word, one) for word in words for one in wanted)

    if names(*_FISH_NAMES):
        if names("pie", "pies", "fish pie"):
            return ("A fish pie comes apart because the sauce is thin, not because the fish broke: "
                    "make the white sauce thick enough to hold a spoon (about 40g butter and 40g "
                    "flour to 400ml milk) and let the pie stand 10 minutes out of the oven before "
                    "you cut it, so the starch sets. A crumble or a pastry lid that slides off is "
                    "the same fault - too much liquid under the crust.")
        if why:
            return ("A fillet comes apart for two reasons: it went into the pan wet, so it steamed "
                    "instead of sealing, or it was moved before the skin had set. Dry it with "
                    "kitchen paper, get the pan properly hot, lay it in skin side down, press it "
                    "flat for ten seconds and leave it four minutes before you turn it once. A "
                    "fillet that still breaks up was probably overcooked, so take it out the "
                    "moment the thickest part just flakes.")
        return ("Pat the fillet dry with kitchen paper and get the pan properly hot before it goes "
                "in: wet fish on a cool pan steams instead of sealing, and that is what makes it "
                "break up. Lay it in skin side down, press it flat for ten seconds, then leave it "
                "alone for four minutes - it releases itself when the skin has set - turn once and "
                "give it two more, and take it out the moment the thickest part just flakes. "
                "Baking at 200C (180C fan) for 12 to 15 minutes on baking paper is the gentler "
                "way, and a fish stew is meant to break up: stir it in at the end.")

    if names("meatballs", "meatball", "kofta", "koftas", "rissoles", "falafel", "sausage meat",
             "meatloaf", "patties", "patty"):
        return ("Something ground and shaped needs a binder and a rest: one egg and a handful of "
                "breadcrumbs per 500g, mix it just until it holds - overworking makes it springy "
                "- then chill it 20 minutes before it meets the pan, because cold holds together "
                "and warm does not. Sear it in a hot pan without moving it for two minutes a side "
                "so a crust forms, then finish it in a 200C oven rather than turning it again. Too "
                "lean a mince is the other cause: 20% fat is what keeps it in one piece.")

    if names("tofu", "paneer", "halloumi", "tempeh"):
        return ("Press the water out first: wrap the block in a clean tea towel with a weight on it "
                "for 15 minutes, then dust it in cornflour before it goes in the pan. That dry "
                "coat is what holds a crust together, and a hot pan with a little oil that you "
                "leave alone for three minutes does the rest. In a stir-fry, add it last and fold "
                "rather than stir.")

    if names("potatoes", "potato", "mash"):
        return ("Floury potatoes break up and waxy ones hold their shape, so buy the right one: "
                "Maris Piper or King Edward for mash and roast, Charlotte or Jersey Royal for a "
                "salad or a tray of boiled ones. Cut them the same size, cook them from cold "
                "water at a bare simmer rather than a rolling boil, and drain them in a colander "
                "for a minute to steam dry before they go in the oven.")

    if names("dumplings", "dumpling", "gnocchi"):
        return ("A dumpling falls apart when the dough is too wet or the pot is at a rolling boil: "
                "use 100g of suet to 200g of self-raising flour with just enough cold water to "
                "bring it together, drop them onto the stew, put the lid on and keep it at a bare "
                "simmer for 20 minutes without lifting the lid. Gnocchi want the same gentle heat, "
                "and they are done a minute after they float.")

    if names("cake", "cakes", "sponge", "bread", "loaf", "loaves", "pastry", "scone", "scones",
             "biscuit", "biscuits", "cookie", "cookies", "brownie", "brownies", "muffin",
             "muffins", "traybake", "yorkshire pudding", "yorkshires", "burger", "burgers",
             "rice", "peas", "pasta", "noodles", "omelette", "pancake", "pancakes"):
        # Baking, rice, pasta and a burger each have a fault row that names the cause (too much
        # flour, too little water, a cold pan), and a generic "cook it less" answer would be
        # worse than the one that is already there.
        return None

    if names("chicken", "turkey", "lamb", "beef", "pork", "roast", "joint", "shoulder",
             "brisket", "ham", "gammon"):
        return ("Coming apart is how you know it is done: a shoulder, a brisket or a chicken thigh "
                "is ready when it pulls apart with no resistance, and a whole bird is done at 74C "
                "in the thickest part of the thigh. If it is coming apart before it is cooked "
                "through, the heat was too high - turn it down to 150C (130C fan), add a splash of "
                "water to the tin and give it another hour covered, because slow and low is what "
                "turns the connective tissue to gelatine rather than drying the meat out.")

    if names("stew", "casserole", "tagine", "goulash", "braise", "pulled"):
        return ("Nothing has gone wrong: a stew, a braise and a slow-cooked shoulder are meant to "
                "come apart, and that is the sign the connective tissue has turned to gelatine. A "
                "shoulder at 150C takes 3 to 4 hours; if it is coming apart before you want it to, "
                "take it off the heat 20 minutes early and let it sit covered, or lift the pieces "
                "out and reduce the liquid on its own.")

    if any(cue in whole for cue in _COMING_APART_ON_PURPOSE):
        return ("Nothing has gone wrong if it is a stew, a braise or a slow-cooked shoulder: they "
                "are meant to come apart, and that is the connective tissue turning to gelatine. A "
                "shoulder at 150C takes 3 to 4 hours. If it is breaking up before you want it to, "
                "take it off the heat early and let it sit covered.")

    if names(*_MUSHY_OWN_ROW):
        return None

    if why:
        return ("It is nearly always one of two things: it was cooked too long, so what held it "
                "together gave up, or it was turned and moved before it had a crust to hold onto. "
                "Take it off the heat a little earlier next time and leave it alone in the pan "
                "until it releases itself.")
    return ("Handle it less and cook it a little less: food comes apart when it is overcooked, or "
            "when it is moved in the pan before it has sealed. Dry the surface, get the pan hot, "
            "leave it alone until it releases itself, and turn it once. If it is already in "
            "pieces, a bake, a soup or a sauce is the way to serve it rather than a plate.")


_DOUGH_WET = ("wet", "sticky", "slack", "runny", "sloppy", "tacky", "gooey")
# "hard" is left out on purpose: "hard to handle" and "hard to knead" are the wet dough's own
# complaint, not a dry one.
_DOUGH_DRY = ("tight", "stiff", "dry", "firm", "tough", "stretchy", "elastic", "springy",
              "tearing", "tears", "resists", "resist")
_DOUGH_NOT = ("not", "no", "never", "isnt", "isn't", "arent", "aren't", "dont", "don't",
              "doesnt", "doesn't", "wasnt", "wasn't", "cant", "can't", "hardly")


def _dough(memory, understood):
    """A dough's fault has a direction, and too stiff and too wet are fixed opposite ways.

    The last fault named wins, and a `not` in front of it turns it round: "not sticky enough" and
    "isn't wet enough" both want water, and "not dry enough" wants flour.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    direction = ""
    for index, word in enumerate(words):
        negated = any(
            earlier in _DOUGH_NOT or earlier.endswith("n't")
            for earlier in words[max(0, index - 2):index])
        if word in _DOUGH_WET:
            direction = "more flour" if not negated else "more water"
        elif word in _DOUGH_DRY:
            direction = "more water" if not negated else "more flour"
    if direction == "more flour":
        return ("Add flour a spoonful at a time and knead it in before you judge, because a dough "
                "is wettest in the first few minutes: it should cling to your hand and come away "
                "clean. Wetter is better for an open crumb, so stop as soon as it stops running "
                "and keep a little of the water back next time, since flour alone can be 10% "
                "different in how much it drinks.")
    return ("Add water a spoonful at a time and knead a minute after each one: a stiff dough "
            "reads drier than it is, because the flour takes a few minutes to take up what is "
            "already in there, and you only feel the difference after kneading. A bread dough "
            "should be tacky rather than sticky - it clings to your hand but comes away clean - "
            "and it is ready when a piece stretches thin enough to see light through without "
            "tearing. If you overshoot, a spoonful of flour brings it back.")


# Watery is a texture fault, and what is watery decides the fix: a mash, a dip, a pastry case,
# a pan of rice and a sauce each have their own cause. The dish names here are the ones people
# write on their own, and the sauce line stays the fallback for everything else.
_MASH_DISH = ("mash", "mashed potato", "mashed potatoes", "duchess potatoes")
# A "dip" is not one food: a hummus thins from water in the tin, a tzatziki from wet cucumber,
# a pesto from wet leaves, and a plain dip from whatever its base is. They are separate answers
# because the fix is the food, not the word "dip".
_CHICKPEA_WET = ("hummus", "houmous", "humus")
_GREEN_DIP_WET = ("pesto",)
_OLIVE_DIP_WET = ("tapenade",)
_DIP_DISH_WET = ("dip", "dips")
_AVOCADO_WET = ("guacamole", "guac", "avocado", "avocados")
# A pastry case holds a wet filling; pastry on its own is a dough, and a wet dough wants flour.
_PASTRY_WET = ("quiche", "pie", "tart", "flan", "pastry case")
_PASTRY_DOUGH_WET = ("pastry", "shortcrust", "shortcrust pastry", "pie crust")
# A dumpling is not a pan of sauce and it is not a bread dough either: it is shaped wet and
# dropped onto a stew, so a mix that will not hold wants flour and a lid. Without this the row
# read "my dumpling mix is watery" as a stew and told them to take the lid off and simmer it.
_DUMPLING_WET = ("dumpling", "dumplings", "suet", "dumpling mix", "cobbler topping")

_RICE_WET = ("rice", "ricecooker", "biryani", "paella", "pilaf", "pilau")
_RISOTTO_WET = ("risotto", "risotto rice", "arborio")
_COUSCOUS_WET = ("couscous", "bulgur", "bulghur")
# Every name above has to be a word the entry can key on, or the table carries a word that can
# never reach it: _FOOD has no bulgur, avocado, tart, flan, shortcrust, dough or arborio, so
# "my bulgur is watery" and "my avocado is watery" were shrugs with the fix sitting right here.
# The same for the oven dishes and the fried mixes: "my moussaka is watery", "my pastry is too
# wet to roll out" and "my falafel mixture is too wet to hold together" were all shrugs.
_WET_FOOD = ("bulgur", "bulghur", "avocado", "avocados", "guac", "tart", "flans",
             "shortcrust", "dough", "arborio", "rice cooker",
             "moussaka", "cannelloni", "gratin", "macaroni", "lasagne", "lasagna",
             "falafels", "fritter", "fritters", "bhaji", "bhajis", "kofta", "koftas",
             "fishcakes", "fish cakes", "patties", "burger", "burgers",
             # The same rule for the thick and the dressed below: the entry can only answer the
             # names its subject list carries. _FOOD has none of batter, oats, icing, smoothie,
             # yoghurt, dal, lentils or coleslaw, so those lines never reached the fix at all.
             # "oat" alone stays out: "my oat milk is watery" is a drink, not a pan of porridge.
             "batter", "oats", "oatmeal", "grits", "icing", "frosting", "buttercream",
             "ganache", "smoothie", "smoothies", "milkshake", "yoghurt", "yogurt", "raita",
             "tzatziki", "labneh", "dal", "lentils", "lentil", "coleslaw", "slaw", "salad",
             "meatball", "stuffing", "stuffings")
# An oven dish is not a pan of sauce and has no lid to take off: what made it watery is the sauce
# under the top, or vegetables that went in wet. A quiche and a tart are pastry cases, and they
# keep the pastry answer below.
_BAKE_WET = ("lasagne", "lasagna", "moussaka", "cannelloni", "pasta bake", "macaroni cheese",
             "mac and cheese", "fish pie", "cottage pie", "shepherds pie", "shepherd's pie",
             "gratin", "frittata", "traybake")
# Something fried in a mix is not simmered either: a wet mix will not hold together in the pan.
# A sausage meat, a stuffing and a meatloaf are the same fault: they are shaped by hand and they
# have to hold it.
_FRY_MIX_WET = ("falafel", "falafels", "fritter", "fritters", "bhaji", "bhajis", "kofta",
                "koftas", "fishcake", "fishcakes", "fish cake", "fish cakes", "patty", "patties",
                "burger", "burgers", "sausage", "sausages", "sausage meat", "meatloaf",
                "meatballs", "stuffing", "forcemeat")
# A dough is not one dough. Bread wants flour and kneading, pastry wants flour and a rest in the
# fridge, and the pastry answer told a bread dough to chill it.
_BREAD_DOUGH_WET = ("dough", "doughs", "bread dough", "pizza dough",
                    "sourdough", "focaccia", "naan", "ciabatta", "rolls", "buns", "brioche",
                    "bagels", "wholemeal", "pitta")
# A batter is poured, so it wants the right thickness rather than flour on its own.
_BATTER_WET = ("batter", "cake mixture", "sponge mixture", "pancake", "pancakes", "waffles",
               "yorkshire", "yorkshires", "crepe", "crepes", "drop scones")
# Porridge is a breakfast, not a sauce: a loose pan of oats wants less milk next time, not puree.
_PORRIDGE_WET = ("porridge", "oats", "oatmeal", "porridge oats", "oat", "grits")

# The thick and the dressed, not the pan: each of these was told to take the lid off and simmer,
# which is the one thing you cannot do to a bowl of icing or a jug of custard. They are separate
# answers because the fix is the food - icing wants sugar, custard wants heat, a dal wants time
# with the lid off, and a salad wants its water taken out before it is dressed.
_WET_CUSTARD = ("custard", "creme anglaise", "creme patissiere", "creme patisserie",
                "pastry cream")
_WET_ICING = ("icing", "frosting", "buttercream", "ganache", "glaze")
_WET_DRINK = ("smoothie", "smoothies", "milkshake", "milkshakes", "shake", "shakes")
_WET_YOGHURT = ("yoghurt", "yogurt", "raita", "tzatziki", "labneh", "yoghurt dip")
# The words that make it a dip rather than a pot: those lines get the draining answer first.
_WET_DIP_WORDS = ("raita", "tzatziki", "dip", "dips", "cucumber", "mint")
_WET_DAL = ("dal", "dhal", "daal", "lentil", "lentils", "lentil soup", "split peas")
_WET_SLAW = ("coleslaw", "slaw", "salad", "salads")

# A plant milk that looks watery is a carton that has separated, or a homemade one with too much
# water in it - not a pan of anything, so it is not the simmer answer. When the milk is in a dish
# (a curry, a cake, a smoothie) the dish is the subject and keeps its own answer.
_PLANT_MILK = ("oat milk", "oatmilk", "almond milk", "soy milk", "soya milk", "rice milk",
               "cashew milk", "hazelnut milk", "plant milk", "milk alternative", "coconut milk")
_PLANT_MILK_DISH = ("curry", "stew", "soup", "sauce", "cake", "batter", "smoothie", "porridge",
                    "rice pudding", "custard", "ice cream", "coffee", "tea", "chai", "latte")


def _watery(memory, understood):
    """Watery is a texture fault, and what is watery changes the answer: mash, dip, pastry or rice."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)
    # "oat milk" is a drink, not a pan of oats: a food word with "milk" straight after it is the
    # milk, so it is not a food that has gone watery. "my oat milk is watery" was the porridge
    # answer, which tells you to put the pan back on the heat.
    words = [word for word in words if word + " milk" not in said]
    if any(name in said for name in _PLANT_MILK) and not any(
            word in said for word in _PLANT_MILK_DISH):
        return ("A carton of oat, almond or soy milk that pours thin has separated: shake it hard "
                "for half a minute before you open it and it comes back together, and a cheap "
                "barista one holds up better in coffee. Homemade oat milk is thin by nature - "
                "blend 1 part oats to 4 of water, strain it lightly, and add a pinch of salt; it "
                "thickens as it stands in the fridge.")
    named = [names for names in (_MASH_DISH, _CHICKPEA_WET, _GREEN_DIP_WET, _OLIVE_DIP_WET,
                                 _DIP_DISH_WET, _AVOCADO_WET, _BAKE_WET, _FRY_MIX_WET,
                                 _BREAD_DOUGH_WET, _BATTER_WET, _PORRIDGE_WET,
                                 _PASTRY_WET, _PASTRY_DOUGH_WET,
                                 _RICE_WET, _RISOTTO_WET, _COUSCOUS_WET,
                                 _WET_CUSTARD, _WET_ICING, _WET_DRINK, _WET_YOGHURT,
                                 _WET_DAL, _WET_SLAW, _DUMPLING_WET)
             if any(_same(word, wanted) for word in words for wanted in names)
             or any(" " in wanted and wanted in said for wanted in names)]
    if any(names is _MASH_DISH for names in named):
        return ("Mash goes watery when the potatoes come out of wet water or the milk goes in cold: "
                "drain them, put the pan back on a low heat for a minute to steam the rest off, "
                "then mash with warm milk and butter. If it has already gone loose, warm it through "
                "in the pan and stir rather than adding anything - it firms up as the extra water "
                "steams away.")
    if any(names is _CHICKPEA_WET for names in named):
        return ("A hummus goes watery from water or ice going in with the chickpeas, or from too much "
                "lemon: drain the tin well, add a spoon more tahini or a few more chickpeas and "
                "blitz again, and serve it chilled, because it thickens as it sits. Loosen it later "
                "with oil, not water.")
    if any(names is _OLIVE_DIP_WET for names in named):
        return ("Tapenade goes watery from olives that came out of the brine wet, or from too much "
                "oil: drain them, dry them on a tea towel, and pound or pulse them with the capers "
                "and anchovy before the oil goes in. A thin tapenade wants more olives and a few "
                "capers, not less oil, and it firms up in the fridge.")
    if any(names is _GREEN_DIP_WET for names in named):
        return ("Pesto goes watery from basil that was still wet, or from too much oil in one go: "
                "dry the leaves in a tea towel, pound or pulse them with the nuts and cheese first "
                "and add the oil last, a little at a time. A thin pesto in the jar wants more grated "
                "cheese and nuts rather than less oil.")
    if any(names is _DIP_DISH_WET for names in named):
        return ("A dip goes watery from water in the base: drain the tin or squeeze out the grated "
                "vegetable, then thicken it with a spoon of the same solid - chickpeas, yogurt, "
                "cream cheese - and taste it again, because thinning it dilutes the salt and the "
                "acid too.")
    if any(names is _AVOCADO_WET for names in named):
        return ("Guacamole goes watery from over-ripe avocado or too much lime: mash it with a fork "
                "rather than a blender, drain any liquid off and stir in a little more avocado, and "
                "leave the stone in if you are keeping it - it slows the browning, not the water.")
    if any(names is _BAKE_WET for names in named):
        # Not in a pan, no lid: the water came from a thin sauce or veg that went in wet, and the
        # heat that helps is dry heat, not more simmering.
        return ("A bake goes watery when the sauce was thin before it was layered, or the vegetables "
                "still had water in them. Next time drain and squeeze the veg and let the sauce "
                "come to a simmer with a spoon of cornflour slaked in cold water before it goes in. "
                "For this one, give it 10 to 15 minutes uncovered at the same heat, then rest it "
                "10 minutes before you cut it, and the sauce will firm up.")
    if any(names is _DUMPLING_WET for names in named):
        return ("A dumpling mix that is too wet wants plain flour a spoonful at a time until it "
                "stops sticking to the bowl, then shape them with wet hands and drop them onto a "
                "stew that is simmering, put the lid on and give them 20 minutes without lifting "
                "it. Too wet and they spread out into the gravy instead of sitting on top.")
    if any(names is _FRY_MIX_WET for names in named):
        # A fried mix is not simmered: a wet mix falls apart in the oil, and heat cannot dry it.
        return ("A mix that will not hold together is too wet to fry: squeeze grated onion or veg "
                "in a clean tea towel, stir in a spoonful of plain or gram flour, and chill it for "
                "30 minutes so the starch takes up the water. Make sure the oil is properly hot "
                "before the first one goes in - a cool pan is what turns a soft mix into a pancake.")
    if any(names is _BREAD_DOUGH_WET for names in named):
        # A bread dough is the one dough that is not improved by the fridge, so it keeps main's
        # own directional answer: too wet wants flour, and "not wet enough" wants water.
        return _dough(memory, understood)
    if any(names is _BATTER_WET for names in named):
        # A batter is poured, so thin batter is a pan of pale pancakes: it needs the right
        # thickness, not heat.
        return ("A batter that is too wet wants flour, not heat: whisk in a spoonful at a time "
                "until it coats the back of the spoon, then let it rest 20 minutes so the flour "
                "takes up the liquid. Too thin and it will not hold the bubbles, so pancakes come "
                "out pale and flat rather than risen, and a cake will not hold its rise either.")
    if any(names is _PORRIDGE_WET for names in named):
        return ("Porridge that has gone too loose wants a minute more on the heat with the lid off "
                "and a stir, and less milk next time: 40g of oats to 300ml of milk or water is "
                "enough for one, and it thickens as it stands. Do not add more oats once it is "
                "cooking, because they will not soften in time.")
    if any(names is _RISOTTO_WET for names in named):
        return ("Risotto that will not thicken wants more stirring, not more heat: keep it moving "
                "and add the stock a ladle at a time, waiting for each one to be taken up, then beat "
                "in cold butter and grated cheese off the heat at the end - that is what makes it "
                "creamy and loose at the same time.")
    if any(names is _COUSCOUS_WET for names in named):
        return ("Couscous goes watery from too much water: pour it into a wide dish, fork it through "
                "to break up the clumps and leave it uncovered for 5 minutes so the steam escapes. "
                "Next time use the same volume of couscous and boiling water, cover it for 5 "
                "minutes, then fork it with a knob of butter rather than stirring it.")
    if any(names is _PASTRY_WET for names in named):
        return ("A quiche or a pie goes watery when the filling is too wet or the egg is undercooked: "
                "give it 5 to 10 minutes more in a 180C oven and it will set, and next time cook the "
                "vegetables or the fruit down first and let them cool, then blind-bake the case "
                "before the filling goes in.")
    if any(names is _PASTRY_DOUGH_WET for names in named):
        return ("Pastry is a dough, not a filling: if it is wet and sticky, work in a little more "
                "flour a spoon at a time, wrap it and give it 20 minutes in the fridge, and roll it "
                "between two sheets of baking paper rather than dusting it with more flour. Shortcrust "
                "wants about half its weight in fat to flour, and cold hands.")
    if any(names is _RICE_WET for names in named):
        return ("Rice goes watery from too much water or the lid coming off: tip it into a sieve, "
                "then back in the pan with the lid on and 5 minutes on the lowest heat to steam dry. "
                "Next time one and a half parts water to one of rice, lid on, and leave it alone.")
    if any(names is _WET_CUSTARD for names in named):
        return ("Custard that is thin has not had enough heat: stir a teaspoon of cornflour into a "
                "splash of cold milk, whisk it in and give it 2 more minutes on a low heat until it "
                "coats the back of the spoon. It also thickens as it cools, so take it off before "
                "it looks set rather than after.")
    if any(names is _WET_ICING for names in named):
        return ("Icing that is too thin wants icing sugar, a spoon at a time, beaten in until it "
                "holds a soft peak: a teaspoon of water or milk goes a long way, so add that in "
                "drops. A glaze is meant to be thin - it should coat the back of the spoon and run "
                "off in ribbons, which is a different job from icing a cake.")
    if any(names is _WET_DRINK for names in named):
        return ("A thin smoothie or shake wants less liquid and something solid: half a banana, a "
                "spoon of oats or yoghurt, or a handful of frozen fruit, blended again - the fruit "
                "and the ice are what give it body. Pour the milk or juice in last, a splash at a "
                "time, instead of all at the start.")
    if any(names is _WET_YOGHURT for names in named):
        # A pot of yoghurt and a bowl of tzatziki have different causes: one has separated, the
        # other was made with wet vegetables. Both halves are in the reply and the one the line
        # names comes first, because "my yoghurt is watery" is a plain pot while "my raita is
        # watery" is the dip.
        pot = ("A pot of yoghurt that has gone watery has separated, and that is harmless: stir it "
               "back together, or spoon the whey off the top, or strain it through muslin or a "
               "clean tea towel in a sieve for an hour for a thicker pot.")
        dip = ("A yoghurt dip goes watery because the vegetables in it were wet: salt the grated "
               "cucumber or carrot for 10 minutes, squeeze it out in a tea towel, and fold it into "
               "thick yoghurt at the end - a spoon of cream cheese or labneh brings back one that "
               "has already split.")
        if any(word in said for word in _WET_DIP_WORDS):
            return dip + " " + pot
        return pot + " " + dip
    if any(names is _WET_DAL for names in named):
        return ("A thin dal wants the lid off for 10 more minutes, stirring now and then: it "
                "thickens as the lentils break up, and mashing a ladleful against the side of the "
                "pan and stirring it back in thickens it at once. Add water a splash at a time at "
                "the end, because dal sets as it cools.")
    if any(names is _WET_SLAW for names in named):
        return ("A watery salad is nearly always salt pulling the water out of the vegetables: salt "
                "the shredded cabbage or the cucumber for 10 minutes, squeeze it in a clean tea "
                "towel, and dress it just before it goes to the table. Mayo loosened with a splash "
                "of vinegar coats better than a thick spoonful.")
    # "Too wet" and "watery" are not the same fault: a mix or a batter is too wet, and a pan of
    # sauce is too thin. The pan answer is for a sauce, so a wet mix gets the mixing bowl instead
    # of tomato puree, which is what "my cake mixture is too wet" was being told to add.
    # A pan of something is a sauce whatever the word: a bolognese that is "too wet" wants
    # reducing, and it is the pan answer's own case.
    pan_food = any(word in ("sauce", "sauces", "stew", "curry", "chilli", "chili", "gravy", "ragu",
                            "bolognese", "bolognaise", "daal", "dhal", "dal", "tagine", "goulash",
                            "casserole", "cassoulet", "broth", "stock", "soup", "soups", "jus")
                   for word in words)
    thin = pan_food or any(word in ("watery", "runny", "thin", "sloppy", "liquid", "thickens",
                                    "thicken", "reduce", "reduces") for word in words) or any(
        phrase in said for phrase in ("never thickens", "wont thicken", "won't thicken",
                                      "not thickening", "doesnt thicken", "doesn't thicken"))
    if not thin and any(phrase in said for phrase in ("too wet", "a bit wet", "is wet", "went wet",
                                                      "bit wet")):
        # "Too wet" is a texture fault of a mix or a batter, and none of the rows above knows
        # this one: porridge, noodles, a loaf, a cake. The pan answer is the wrong answer to
        # every one of them, so the entry turns the line down (an empty reply) and a lower
        # entry - or the ack - gets the turn, which is worse than a good answer and much
        # better than "stir in a spoon of tomato puree".
        return ""
    return ("Take the lid off and let it simmer for 10 to 15 minutes: most of the water goes off in "
            "the steam. To thicken it properly, stir in a spoon of tomato puree, a handful of red "
            "lentils, or cornflour slaked in cold water, and give it 5 more minutes.")


def _lumpy(memory, understood):
    """Lumps depend on what they're in: mash, custard, porridge and sauce all lump differently."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, "mash") or word in ("potato", "potatoes") for word in words):
        return ("Mash them while they're hot with plenty of butter and warm milk, and beat with a "
                "wooden spoon rather than a fork. Lumps come from cold potatoes or too little fat; "
                "if they're stubborn, push the mash through a sieve or a potato ricer.")
    if any(_same(word, "custard") for word in words):
        return ("Take it off the heat and whisk hard, then push it through a sieve. Custard goes "
                "lumpy when the heat is too high or the eggs go in too fast, so next time pour the "
                "hot milk into the eggs a splash at a time and cook it slowly, stirring.")
    if any(_same(word, "porridge") or _same(word, "oats") for word in words):
        return ("Beat in a splash more milk or water and whisk it hard; porridge lumps come from "
                "dry oats hitting hot liquid too fast. Next time stir the oats into cold liquid and "
                "bring it up slowly, stirring all the time.")
    return ("Whisk it hard with the pan off the heat and push it through a sieve, because lumps "
            "break up far better off the ring. Next time stir the flour into the fat before any "
            "liquid goes in, then add the liquid a splash at a time.")


# "im bored of chicken, what else can i cook", "im sick of pasta": the line names a food to
# rule it out, so an entry answering "how long do i roast that" or "how do i boil that" has
# the ask wrong. The meal table answers with a dish that leaves the food out.
_FREEZE_AVOID = ("make with", "cook with", "do with", "what can i make", "what can i cook", "ideas", "dinner", "tonight", "use up")
_CHEAP_AVOID = ("cheap", "cheap recipe", "cheap recipes", "cheap meal", "budget")
_MEAL_ASK_AVOID = ("cook with", "cooking with", "make with", "do with", "ideas", "idea", "dinner", "tonight", "meal", "meals", "recipes", "recipe")
WANT_SOMETHING_ELSE = ("bored", "bored of", "sick of", "tired of", "fed up", "had enough",
                       "what else", "something else", "anything else", "instead",
                       "other ideas")


_CLUMP_WORDS = ("clump", "clumps", "clumped", "clumping", "lump", "lumps", "stuck", "sticks",
                "sticking", "together", "gluey", "sticky")


_EGG_STORE = ("store", "storing", "stored", "keep", "keeps", "keeping", "last", "lasts",
              "longer", "fridge", "fridged", "freeze", "room", "counter", "cupboard")
_EGG_STORE_TEXT = ("Keep eggs cold and steady: in the fridge, in their carton, pointy end down, "
                   "away from anything strong-smelling, because the shells are porous. Stored that "
                   "way they keep well past their date. ")
_EGG_TEST_TEXT = ("Put a suspect egg in a glass of water: one that lies flat on the bottom is "
                  "fresh, one that stands on end is older but fine, and one that floats is past it. ")


def _eggs(memory, understood):
    """How to store eggs, or how to test one: whichever the line asked about comes first."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(word in ("fresh", "off", "bad", "rotten", "float", "test", "edible", "safe",
                    "date", "dated", "expired", "expiry", "ok", "okay", "fine", "use",
                    "usable", "eat", "eaten", "yesterday", "week", "weeks", "old")
           for word in words) and not any(word in _EGG_STORE for word in words):
        return _EGG_TEST_TEXT + _EGG_STORE_TEXT.strip()
    return _EGG_STORE_TEXT + _EGG_TEST_TEXT.strip()


def _pasta_cook(memory, understood):
    """How to cook pasta, plus the clumping answer when that is what went wrong."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    text = ("Use a big pan of well-salted water, about 10g of salt per litre, and cook the pasta "
            "one minute less than the packet says. Keep a mug of the cooking water: a splash of it "
            "makes any sauce cling to the pasta.")
    if any(word in _CLUMP_WORDS for word in words):
        text += (" Clumping is the pasta sitting still in water that is not deep or hot enough, so "
                 "stir it for the first minute and again every couple of minutes, and leave the "
                 "oil out: it stops the sauce clinging.")
    return text


def _popcorn_make(memory, understood):
    """The pan, the microwave and no oil are three ways to make the same bowl.

    The card carries all three, so the one the line names goes first: "how do i make popcorn in
    the microwave" wanting the pan method first reads as the wrong answer.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    pan = ("Three kernels and a tablespoon of oil in a big lidded pan over medium heat, and when "
           "those three pop, add a single layer of kernels and put the lid back on. Shake the pan "
           "every so often and take it off the heat when the pops slow to one every few seconds, "
           "about 3 minutes for four tablespoons of kernels. Tip it into a bowl, salt it while it "
           "is hot, and leave the lid off so the steam gets away and it stays crisp.")
    microwave = ("Put a quarter of a cup of kernels in a paper bag or a bowl with a plate over it "
                 "and give it 2 to 3 minutes on full power, stopping the moment the pops slow to "
                 "one every few seconds; a bag is the easy way because the steam escapes. Salt it "
                 "while it is hot and leave the lid off the bowl so it stays crisp.")
    dry = ("Dry kernels pop without any oil: shake a single layer of them in a heavy lidded pan "
           "over medium heat, lifting the pan off the ring every few seconds so the bottom does "
           "not scorch, until the pops slow. Or use an air popper, which is the same thing with "
           "the stirring done for you.")
    if any(_same(word, way) for word in words
           for way in ("microwave", "microwaved", "microwaving", "microwaves", "bag", "bags")):
        return microwave + " " + pan if "hob" in words or "pan" in words else microwave
    if any(_same(word, way) for word in words
           for way in ("oil", "air", "popper", "diet", "healthy")):
        return dry
    return pan


def _popcorn_keep(memory, understood):
    """Keeping popcorn is a cupboard question; chewy popcorn is a fault with this batch.

    The card answers both, so the cause goes first when the line is about how the batch came
    out: "my popcorn came out chewy" wants the reason, and "how long does popcorn keep" wants
    the tin.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, fault) for word in words
           for fault in ("chewy", "soggy", "squidgy", "tough", "rubbery")):
        return ("Chewy popcorn was either stale to start with or it did not get hot enough: use "
                "kernels under a year old, keep them in a sealed jar rather than the fridge, and "
                "give the pan a few more seconds after the pops slow to one every few seconds. "
                "Leave the lid off the bowl once it is out, because the steam it sits in is what "
                "turns the rest soft.")
    return ("Kernels keep for about a year in a sealed jar in a cool cupboard, and popped corn goes "
            "soft within a day or two, so an airtight tin is what keeps it crisp. Popcorn that "
            "comes out chewy was stale to start with or did not get hot enough: use kernels under "
            "a year old and give the pan a few more seconds after the pops slow.")


_STEWED_FRUIT = ("apple", "apples", "pear", "pears", "rhubarb", "plum", "plums",
                 "cherry", "cherries", "apricot", "apricots", "berry", "berries",
                 "fruit", "quince", "peach", "peaches")
# Why a stewed fruit stayed hard is the fruit's own business: a Bramley collapses where a Cox
# holds, and rhubarb's stalk decides its five minutes. One sentence, named for the fruit.
_STEWED_WHY = (
    (("apple", "apples"), "apple", "a Bramley collapses to a fluff while a Cox or a Braeburn "
     "holds its shape, so use Bramleys for a sauce, a crumble or a compote"),
    (("pear", "pears"), "pear", "a Conference softens where a Comice is for eating raw, and a "
     "hard pear wants 10 more minutes"),
    (("rhubarb",), "rhubarb", "thin young stalks give way in 5 minutes and thick old ones want "
     "15, so pick the thin ones and add the sugar once they have softened"),
    (("plum", "plums"), "plum", "a ripe plum collapses in 5 minutes and a firm one holds, so "
     "halve them and taste at 5"),
    (("cherry", "cherries"), "cherry", "cherries want 5 to 8 minutes and go from firm to jam "
     "quickly, so take them off while they still hold"),
    (("apricot", "apricots", "peach", "peaches"), "apricot", "a ripe one collapses in 5 minutes "
     "and an underripe one stays firm whatever you do, so halve them and poach them gently"),
    (("berry", "berries"), "berry", "berries want only 2 or 3 minutes and a hard one was "
     "underripe to begin with"),
    (("quince",), "quince", "a quince stays hard for 40 minutes and then turns pink and soft all "
     "at once, so give it the time and taste it"),
)


def _stewed_fruit(words):
    named, why = "fruit", ("a firm one holds its shape where a ripe one collapses, so use the "
                           "ripe ones for a compote")
    for forms, name, reason in _STEWED_WHY:
        if any(_same(word, form) for word in words for form in forms):
            named, why = name, reason
            break
    return ("A stewed %s that stays hard was the fruit rather than the cooking: %s. Give it 10 "
            "more minutes with a splash of water and taste as it goes, because it goes from firm "
            "to pulp quickly once it starts." % (named, why))


def _tough(memory, understood):
    """Chewy food that is meat, squid or a batter each wants a different answer."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, "squid") for word in words):
        return ("Squid is either 2 minutes or 40: flash it in a very hot pan, or stew it slowly with "
                "tomatoes and wine for 40 minutes. Anything in between turns it to rubber.")
    # Stewed fruit is the same word about a different thing: a tough stewed apple was a hard
    # apple, and it is not going to soften in another 30 minutes without turning to pulp. It gets
    # the fruit's own answer, named, because the fruit decides why it stayed hard.
    if (any(_same(word, fruit) for word in words
            for fruit in _STEWED_FRUIT)
            and any(_same(word, way) for word in words
                    for way in ("stewed", "stew", "poached", "compote", "baked", "puree"))):
        return _stewed_fruit(words)
    # Tough meat in a pot is the one case where the fix is more time and not a hotter pan: "my
    # stew is tough" was getting the batter line ("pancakes and batters want a lumpy mix"), which
    # is the wrong pan and the wrong food. This goes before the meat branch because the pot
    # decides the answer, whatever meat is in it.
    if (any(_same(word, pot) for word in words
            for pot in ("stew", "stews", "casserole", "braise", "braised", "braising", "goulash",
                        "hotpot", "tagine", "ragu", "chilli", "chili"))
            and not any(_same(word, fruit) for word in words for fruit in _STEWED_FRUIT)):
        return ("A tough stew is an underdone one rather than an overcooked one: another 30 to 45 "
                "minutes at a bare simmer with the lid on, and top the liquid up if it is running "
                "low. A simmer that is really a boil tightens the meat instead of softening it, so "
                "keep it just trembling and test a piece with a fork - it is ready when it gives "
                "way without resistance.")
    if any(_same(word, meat) for word in words
           for meat in ("steak", "meat", "beef", "pork", "lamb", "chicken", "chop", "chops",
                        "turkey", "sausage", "sausages", "burger", "burgers", "roast", "gammon",
                        "duck", "ribs")):
        if _asks_why(words):
            return ("It went tough from cooking too fast or from not resting: the muscle fibres "
                    "contract and squeeze the juice out, and a cheap cut needs longer at a lower "
                    "heat to break down instead - 2 hours at 160C with liquid in the pan. This "
                    "piece is best sliced thinly across the grain and served with something wet.")
        return ("Slice it thinly across the grain and serve it with something wet; that rescues more "
                "tough meat than anything else. It went tough from cooking too fast or not resting, "
                "so next time go slower: a cheap cut wants 2 hours at 160C with liquid in the pan.")
    # Tough pasta or rice is the opposite fault to tough meat: it is underdone, and more time is
    # the fix. Vegetables of every kind are answered by dishes' own vegetable table, so they are
    # not named here; the batter line below is the last fallback.
    if any(_same(word, starch) for word in words
           for starch in ("pasta", "noodle", "noodles", "rice")):
        return ("Tough here is underdone rather than overcooked: give it 5 more minutes in boiling "
                "water and test it with the tip of a knife, and cut the pieces the same size so they "
                "finish together. A pan that never came back to the boil is the usual reason it is "
                "still hard in the middle when the outside is done.")
    # A tough cake or scone is over-mixed, not undercooked: every stir after the flour goes in starts
    # gluten, and the batter line below would send someone back to the pan for nothing.
    if any(_same(word, bake) for word in words
           for bake in ("cake", "cakes", "sponge", "sponges", "muffin", "muffins", "cupcake",
                        "cupcakes", "scone", "scones", "brownies", "brownie", "bun", "buns",
                        "traybake", "traybakes", "loaf", "loaves")):
        thing, plural = _the_bake_named(words)
        return ("Tough " + thing + (" are" if plural else " is") if thing else "A tough bake is") + (
            " mixed too much or a little too long in the oven, or short of fat. Stir only until "
            "the flour disappears, fold rather than beat, and weigh the butter rather than "
            "eyeballing it, because a sponge wants as much fat as eggs by weight. One that is "
            "already tough is best eaten warm with something wet, or torn up for a trifle.")
    # Pastry goes tough in the other direction from a vegetable: it was worked too much or made
    # too wet, and cooking it longer only makes it worse. The batter line would be nonsense here.
    if any(_same(word, pastry) for word in words
           # bare `dough` is not pastry: a tough bread dough is an over-kneaded loaf, and the
           # bread branch below answers it.
           for pastry in ("pastry", "shortcrust", "shortcrust pastry", "pie crust",
                          "pie", "tart", "quiche", "crumble")):
        return ("Tough pastry is over-worked or too wet: keep the fat cold, rub it in with your "
                "fingertips only until it looks like fine breadcrumbs, add iced water a spoon at a "
                "time and bring it together fast. Shortcrust wants about half its weight in fat to "
                "flour, and 20 minutes in the fridge before it is rolled; roll it between two sheets "
                "of greaseproof so you never stretch it. Pastry that is already baked cannot be "
                "rescued, so serve it with something wet.")
    if any(_same(word, bread) for word in words
           for bread in ("bread", "loaf", "roll", "rolls", "baguette", "pitta", "naan", "bun",
                         "buns", "bagel", "bagels")):
        return ("Tough bread is usually over-kneaded or baked too slowly: knead until the dough "
                "springs back and stops tearing, prove it somewhere warm until it has doubled, and "
                "bake it hot (220C) for the first 10 minutes so it rises before the crust sets. "
                "Bread that has already gone leathery comes back in a hot oven for 5 minutes with a "
                "splash of water in the tin.")
    if any(_same(word, egg) for word in words for egg in ("egg", "eggs", "omelette", "scrambled")):
        # "the eggs went rubbery in the microwave" was getting the pancake-batter answer, which
        # is a different food and a different fix.
        return ("Rubbery eggs have been cooked too long, and in a microwave that happens in seconds: "
                "beat them, give them 30 seconds at a time on medium, stir hard between each go, "
                "and stop while they still look a little wet, because they carry on setting as "
                "they stand. The same rule in a pan - low heat, slow stirring, off the heat early.")
    return ("Rubbery is overcooked, or a batter that was beaten too much: pancakes and batters want "
            "a lumpy mix and a minute less in the pan. It's hard to rescue on the plate, so serve it "
            "with something wet and cook it less next time.")


_BAKE = ("cake", "cakes", "sponge", "bread", "loaf", "buns", "bun", "scones", "scone",
         "muffins", "muffin", "brownies", "brownie", "pancakes", "yorkshire pudding", "biscuits",
         "biscuit", "pastry", "dough", "batter", "pie")


def _salty(memory, understood):
    """A cake that is salty cannot be bulked out with potatoes, so baking has its own answer."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    if any(_same(word, bake) for word in words for bake in _BAKE):
        return ("Baking is the one place salt cannot be cooked out or bulked out: leave it and cut the "
                "salt from whatever goes with it, or add a little more sugar and fat to push it into "
                "the background. Next time weigh the salt with the measuring spoons rather than "
                "shaking it in, and remember salted butter is already about a quarter salt.")
    return ("Don't add water: bulk it out with more of what's already in it — potatoes, rice, tinned "
            "tomatoes, cream or unsalted stock — and finish with a squeeze of lemon. In a soup or "
            "stew, a peeled potato simmered in it for 15 minutes takes up some of the salt too.")


def _scramble(memory, understood):
    """Scrambled eggs that went watery and scrambled eggs that went rubbery are two faults.

    "How do I make scrambled eggs" is neither: with no fault word in the line it is the method.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    # A line that only asks how is the method; a line that says what went wrong is a fault, and a
    # misspelt fault still reads as one because the method answer is not the one a person wants
    # when they tell you their eggs always come out rubbery.
    asks_how = (understood.get("kind") == "question"
                or any(_same(word, "how") for word in words))
    if asks_how and not any(_same(word, fault) for word in words
                            for fault in ("watery", "wet", "sloppy", "rubbery", "rubber", "tough",
                                          "dry", "hard", "overcooked", "chewy", "curdled",
                                          "mushy")):
        return ("Beat 2 or 3 eggs with a pinch of salt, melt a knob of butter in a pan over a low "
                "heat, pour them in and stir slowly with a spatula, pushing the set egg in from the "
                "edges. Take them off while they still look a little wet, after 2 or 3 minutes, "
                "and stir in a little more butter off the heat.")
    if any(_same(word, wet) for word in words for wet in ("watery", "wet", "sloppy")):
        return ("Watery scrambled eggs have been cooked too long: the curds squeeze out their "
                "water as they tighten. Cook them low and slow, stirring, and take them off while "
                "they still look a little loose, then stop the heat with a knob of cold butter or "
                "a spoon of creme fraiche.")
    return ("Rubbery scrambled eggs come from too much heat: cook them low and slow, stirring, and "
            "take them off while they still look slightly wet, because they carry on setting. A "
            "knob of butter at the end stops them going dry.")


# An egg in a pan, an egg in a quiche and an egg in a jug are three different faults with three
# different fixes, and the fault word is the same in all of them: "my omelette is rubbery" was
# reaching the pancake-batter answer, "my frittata is rubbery" the same one, "my quiche is
# rubbery" the tough-pastry answer, and "my creme anglaise is grainy" nothing at all.
_EGG_DISH = ("omelette", "omelet", "omelettes", "omelets", "frittata", "frittatas", "quiche",
             "quiches", "fried egg", "fried eggs", "creme anglaise", "creme patissiere",
             "creme patisserie", "pastry cream", "custard sauce")
_EGG_FAULT = ("rubbery", "rubber", "tough", "leathery", "overcooked", "over cooked",
              "fell apart", "falls apart", "falling apart", "wouldnt fold", "wont fold",
              "split", "splits", "curdled", "grainy", "gritty", "watery", "weeping", "dense",
              "soggy", "lumpy", "chewy")
_EGG_PAN = ("omelette", "omelet", "omelettes", "omelets")
_EGG_FRITTATA = ("frittata", "frittatas")
_EGG_QUICHE = ("quiche", "quiches")
_EGG_FRIED = ("fried egg", "fried eggs")
_EGG_SAUCE = ("creme anglaise", "creme patissiere", "creme patisserie", "pastry cream",
              "custard sauce")


def _egg_fault(memory, understood):
    """A fault in an egg dish, answered by the dish: the pan, the oven or the jug.

    "My omelette fell apart" is not overcooking at all, so the fold has its own answer, and a
    curdled sauce is a temperature problem while a rubbery quiche is simply a minute too long.
    """
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    if not words:
        return None
    said = " ".join(words)

    def named(names):
        return any(name in said for name in names)

    def fault(*names):
        return any(_same(word, name) for word in words
                   for name in names) or any(name in said for name in names)

    if named(_EGG_SAUCE) and fault("grainy", "gritty", "split", "splits", "curdled", "curdles",
                                  "lumpy", "scrambled"):
        return ("A grainy or split creme anglaise has curdled, because the eggs went above about "
                "82C. Take it off the heat at once, whisk in a splash of cold milk to stop it "
                "cooking, then strain it through a sieve and it comes back smooth. Next time cook "
                "it over a low heat, stirring all the time, and pull it off as soon as it coats "
                "the back of the spoon.")
    if named(_EGG_SAUCE):
        return None
    if named(_EGG_QUICHE):
        if fault("rubbery", "rubber", "tough", "dense", "overcooked", "over cooked"):
            return ("A rubbery quiche is a custard that stayed in too long: the filling is firm "
                    "at about 80C, so bake it at 180C for 30 to 35 minutes, until the middle "
                    "still has a slight wobble, and let it cool for 20 minutes, because it firms "
                    "as it stands. Two eggs to 200ml of double cream in a 20cm tin sets soft; "
                    "more egg than that sets like rubber.")
        # A watery or dry quiche already has an answer on the bake and the pastry case, so this
        # only speaks for the set custard, which is the fault nothing else knew.
        return None
    if named(_EGG_FRIED):
        return ("Fried eggs go rubbery when the white sets hard before the yolk is warm: cook "
                "them on a medium heat with a lid on for 2 to 3 minutes, so the top sets in the "
                "steam, and take them out while the yolk still wobbles. On a high heat the white "
                "blisters and toughens long before the yolk is hot.")
    if named(_EGG_FRITTATA) or named(_EGG_PAN):
        if fault("fell apart", "falls apart", "falling apart", "wouldnt fold", "wont fold",
                 "broke", "tears", "tore"):
            return ("An omelette tears when the eggs are too thin for the pan, so use a 20cm pan "
                    "and no more than three eggs, let the base set for 45 seconds before you fold, "
                    "and fold it with a spatula in the pan instead of lifting it out. A frittata "
                    "is finished under the grill and never folded, which is the same dish without "
                    "the part that breaks.")
        if fault("soggy", "watery", "wet"):
            # A frittata or an omelette that will not set is wet vegetables, not heat: the water
            # they hold comes out in the pan and the eggs cannot firm around it.
            return ("An omelette or frittata that stays wet is a vegetable problem: mushrooms, "
                    "courgette, spinach and onion all give out water as they cook. Fry them first, "
                    "on their own, until their water has gone and they are starting to colour, and "
                    "let them cool a little before the eggs go in. A pinch of salt in the beaten "
                    "egg also helps it set.")
        if fault("rubbery", "rubber", "tough", "leathery", "overcooked", "over cooked",
                 "chewy"):
            return ("An omelette goes rubbery from the pan and the clock rather than the eggs: a "
                    "20cm pan on a medium heat, two beaten eggs with a pinch of salt, and pull the "
                    "set edges into the middle for 60 to 90 seconds, then fold and slide it out "
                    "while the top still looks a little wet. A small pan steams it instead of "
                    "setting it, and one more minute is enough to make it leathery.")
        return None
    return None



def _cookies(memory, understood):
    """Cookies that spread too far, and the opposite fault, cookies that never spread at all."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)
    # "my cookies didnt spread" is the other fault: the dough went in as balls and came out as
    # balls, which is too much flour or butter that was too cold, not dough that was too warm.
    if any(phrase in said for phrase in ("didnt spread", "didn't spread", "did not spread",
                                        "not spread", "not spreading", "wont spread",
                                        "won't spread", "stayed in a ball", "stayed in balls",
                                        "too thick", "too small", "didnt flatten",
                                        "didn't flatten", "did not flatten", "stayed round")):
        return ("Cookies that stay in a ball have usually had too much flour or butter that was "
                "too cold: weigh the flour rather than scooping the cup, use soft butter, and "
                "press each ball down to about 1cm with the back of a spoon before it goes in. A "
                "tablespoon of milk or an extra yolk loosens a dry dough, and the oven wants to be "
                "properly hot, 180C (160C fan), so they set before they can spread.")
    return ("Cookies spread when the dough is warm or the butter is too soft: chill the dough 30 "
            "minutes and put it on a cool tray, and leave a good 5cm between them. Too much sugar "
            "or a greased tin makes them spread further, and a fan oven needs 20C less than the "
            "recipe.")


def _chocolate(memory, understood):
    """Melting chocolate in the first place, and rescuing a bowl that has seized."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    # "white" is a kind of chocolate as well as a fault on one: "how do i melt white chocolate" and
    # "white chocolate ganache" are melting questions, so the word only counts as bloom when it is
    # not in front of the word chocolate.
    said = " ".join(words)
    told_apart = re.sub(r"\bwhite\s+(?=chocolate\b)", "", said).split()
    if any(_same(word, fault) for word in told_apart
           for fault in ("bloom", "white", "streak", "streaks", "grey", "gray")):
        return ("White streaks on chocolate are bloom, and it is harmless: either cocoa butter or "
                "sugar has come to the surface because the chocolate got warm and then cool again. "
                "It still tastes the same and it is fine to eat or to melt. To stop it happening, "
                "store it cool and steady, around 15 to 18C, and never in the fridge.")
    # "is white chocolate real chocolate" and "is dark chocolate healthy" are questions about what
    # the stuff is, not about melting it, so they are answered before the method.
    if any(phrase in said for phrase in ("healthy", "good for you", "bad for you",
                                        "better for you", "fattening", "sugar", "calorie",
                                        "calories", "diet")):
        return ("As a treat, chocolate is fine: dark with 70% cocoa or more has the least sugar, so "
                "it is the one to pick if you are watching it, and two squares is a normal "
                "portion. White chocolate is the sweetest of the three because it is cocoa butter, "
                "milk and sugar with no cocoa solids at all.")
    if any(phrase in said for phrase in ("real chocolate", "is it chocolate", "actually chocolate",
                                        "made of", "made from", "contain", "contains",
                                        "what is chocolate", "is white chocolate",
                                        "whats in chocolate", "what's in chocolate")):
        if "white" in words:
            return ("White chocolate is cocoa butter, milk powder and sugar, with no cocoa solids "
                    "at all, which is why it tastes of vanilla and milk rather than of chocolate. "
                    "It is still real chocolate by the labelling rules - at least 20% cocoa butter "
                    "in Europe - just a different thing from dark, and it is the sweetest of the "
                    "three.")
        return ("What most people mean by chocolate is dark: cocoa solids and cocoa butter with "
                "sugar, and the higher the percentage the less sugar there is. Milk chocolate "
                "adds milk powder and more sugar, and white chocolate is cocoa butter, milk and "
                "sugar with no cocoa solids at all.")
    if any(_same(word, "temper") for word in words):
        return ("To temper chocolate, melt two thirds of it in a bowl over barely simmering water "
                "to 45C (or 40C for white), take it off the heat and stir in the rest, chopped, "
                "until it drops to 27C, then warm it gently back to 31C for dark or 29C for milk "
                "and white. That sets it glossy and hard at room temperature. A thermometer earns "
                "its keep; without one, a clean spoon dipped in should set firm in 5 minutes.")
    # "how do i melt chocolate for dipping" is a melting question: only a line that does not ask
    # about melting gets the dipping method
    if (any(_same(word, want) for word in words
            for want in ("dip", "dipped", "dipping", "strawberry", "strawberries"))
            and not any(_same(word, want) for word in words
                        for want in ("melt", "melting", "melted"))):
        return ("Melt it slowly, then dip: dry the fruit first so the chocolate grips, dip about "
                "two thirds of the way in, let the extra drip back into the bowl, and set them on "
                "baking paper in the fridge for 10 minutes to set hard. If the chocolate feels "
                "thin, stir in a handful more chopped chocolate off the heat.")
    if any(_same(word, fault) for word in words
           for fault in ("seize", "seized", "seizing", "grainy", "lumpy", "stiff")):
        return ("Chocolate seizes when even a drop of water gets in, and the fix is more water, "
                "not less: stir in a teaspoon of boiling water at a time, off the heat, until it "
                "goes smooth again. A tablespoon of warm cream does the same and leaves you with "
                "a ganache.")
    return ("Melt chocolate in a bowl over barely simmering water, with the bowl not touching the "
            "water, or in 20-second bursts in the microwave, stirring between them. Keep every "
            "spoon and bowl dry, because a drop of water makes it seize, and take it off while "
            "most of it is melted - the rest will go as you stir.")
_GRAIN_FOOD = ("fudge", "toffee", "caramel", "icing", "frosting", "buttercream", "fondant",
               "praline", "brittle", "tablet", "syrup", "candy", "custard")
_GRAIN_WORD = ("grainy", "gritty", "crystal", "crystals", "crystallised", "crystallized",
               "crystalised", "crystalized", "granular", "sandy", "crunchy", "grain")


def _grainy(memory, understood):
    """Sugar that has set with crystals in it: a fudge, a toffee, a caramel or an icing.

    The cause is the same in every one - sugar stirred once it is boiling, or a single crystal
    from the side of the pan getting back in - but the rescue is not, so it goes by the sweet in
    the line: an icing is sifted and beaten, a fudge is warmed with milk and beaten, and a caramel
    is melted back with a spoonful of water.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]

    def has(*names):
        return any(_same(word, name) for word in words for name in names)

    if has("icing", "frosting", "buttercream", "glaze", "fondant", "drizzle"):
        return ("Grainy icing is undissolved sugar: sift the icing sugar first, then add the "
                "liquid a teaspoon at a time, and if it is already made, beat in a spoonful of "
                "warm milk or a few drops of lemon juice and it goes smooth. Cold liquid and "
                "coarse sugar are what leave the grain, so warm the milk slightly next time and "
                "give it a full minute of beating.")
    if has("fudge", "tablet", "praline", "brittle", "candy"):
        return ("Grainy fudge has sugar crystals in it, which happens when it is stirred while it "
                "boils or a crust of sugar from the pan gets back in. Warm it very gently with two "
                "tablespoons of milk and beat it hard until it is smooth again, or press it out "
                "flat and call it tablet. Next time stir only until the sugar dissolves, then "
                "wipe the pan sides down with a wet pastry brush and leave it to 116C.")
    if has("custard", "creme", "anglaise"):
        # A grainy custard is curdled egg, not sugar, so the rescue is cold milk and a sieve
        return ("Grainy custard has curdled: the eggs got too hot too fast. Take it off the heat "
                "at once, whisk in a splash of cold milk to stop it cooking, then strain it "
                "through a sieve into a jug and it comes back smooth. Next time cook it over a "
                "low heat, stirring all the time, and take it off at about 82C or as soon as it "
                "coats the back of the spoon.")
    if has("toffee", "caramel"):
        return ("Grainy caramel or toffee has crystallised: add a tablespoon of water and warm it "
                "very gently without stirring until the crystals melt, then let it cool slowly. "
                "It crystallises when the sugar is stirred once it is boiling, or when one "
                "crystal from the side of the pan gets back in, so stir only until the sugar has "
                "dissolved and keep the sides of the pan wiped clean.")
    return ("Sugar that sets grainy has crystallised, from stirring once it boils or a crystal "
            "from the pan getting back in. Warm it gently with a tablespoon of water until it "
            "melts back, and next time stir only until the sugar dissolves, wipe the pan sides "
            "with a wet pastry brush, and add a spoonful of golden syrup or a squeeze of lemon "
            "at the start.")



_SUGAR_MAKING = ("caramel", "caramels", "toffee", "praline", "brittle", "fudge", "candy")
_SUGAR_TROUBLE = ("crystallise", "crystallised", "crystallising", "crystallize", "crystallized",
                  "crystallizing", "crystalise", "crystalised", "crystalize", "crystalized",
                  "crystals", "crystal", "grainy", "grain", "crust", "crusty", "seize", "seized")


def _sugar_work(memory, understood):
    """Sugar as a thing you work with: dissolving it, boiling it to caramel, keeping it clear.

    Three questions arrive with the same words. A syrup that will not go clear wants warm water
    and a stir; sugar that has gone grainy wants the crystals melted back and the pan side wiped;
    and "how do i make caramel" is not a fault at all but the cooking itself. The diet answer used
    to take all three, because "how do i" plus "sugar" was enough for it.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]

    def has(*names):
        return any(_same(word, name) for word in words for name in names)

    if has("bitter", "burnt", "burned", "burning", "smoky", "smells"):
        # "get burnt sugar out of a pan" is a pan to clean, not a caramel that went too far: the
        # bitter caramel line ("start again, pull it at the colour of a copper penny") is no use
        # to somebody holding a burnt pan.
        if _burnt_on_the_pan(" ".join(words)):
            return ""
        return ("A bitter caramel has gone past the colour: sugar keeps cooking after it leaves "
                "the heat, so it went from amber to dark before it came off. Start again and pull "
                "it at the colour of a copper penny, and have the cream ready to add off the heat "
                "so it stops at once. One that tastes of the pan is not worth saving.")
    if has("hard", "hardened", "hardens", "block", "solid", "lumps", "lumpy", "stuck",
           "soften", "softens", "softening"):
        return ("Sugar that has set hard has taken up damp and dried out again: put the bag in the "
                "microwave for 10 seconds at a time, or stand a slice of bread or a peeled apple in "
                "the jar overnight, and it breaks up. Keep it in an airtight jar away from the "
                "steam of the kettle, because it is the damp that sets it into a block.")
    if has(*_SUGAR_TROUBLE) and not has("dissolve", "dissolves", "dissolving", "dissolved", "melt",
                                        "melts", "melting", "melted"):
        return ("Sugar crystallises when it is stirred once it is boiling, or when one grain from "
                "the side of the pan drops back in. Melt it back with a tablespoon of water over a "
                "low heat without stirring, and next time stir only until the sugar has dissolved, "
                "wipe the pan sides down with a wet pastry brush, and add a squeeze of lemon or a "
                "spoonful of golden syrup at the start.")
    if (has("syrup", "coffee", "cocktail", "cocktails", "tea", "dissolve", "dissolves",
            "dissolving", "dissolved", "melt", "melts", "melting", "melted")
            or not has(*_SUGAR_MAKING)):
        return ("Sugar dissolves fastest in hot liquid: warm the water or milk first, stir until "
                "the liquid is clear rather than for a set time, and use about 200g of sugar to "
                "100ml of water for a syrup. Caster sugar goes in quicker than granulated and "
                "icing sugar dissolves almost at once. A spoonful of lemon juice or golden syrup "
                "stops a syrup crystallising as it cools.")
    if has("toffee", "toffees", "fudge", "praline", "brittle", "candy"):
        return ("Caramel is the base of all of them, then the temperature sets what you get: "
                "200g sugar in a dry heavy pan, swirled not stirred, to the colour of a copper "
                "penny. Toffee is that plus 60g butter and a splash of cream stirred in off the "
                "heat, cooked on to 150C (hard crack) and poured to set; fudge comes off at 116C "
                "(soft ball), then you beat it in the pan as it cools so it stays smooth instead "
                "of grainy. A sugar thermometer earns its keep here.")
    return ("Caramel is sugar cooked until it changes colour, and nothing else: 200g sugar in "
            "a dry heavy pan over a medium heat, not stirred but swirled, until it is the "
            "colour of a copper penny - then straight off the heat, because it keeps cooking. "
            "For a sauce, add a splash of warm cream off the heat, as it spits. A wet caramel "
            "is 200g sugar with 60ml water and a squeeze of lemon, boiled without stirring.")

def _soup(memory, understood):
    """Making soup, or making a soup that is already made taste of something."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, want) for word in words
           for want in ("better", "flavour", "improve", "boring", "lifeless", "interesting")):
        return ("Add salt first, then a squeeze of lemon or a splash of vinegar: most dull soup is "
                "short of both, not of spice. After that something savoury - a stock cube, a spoon "
                "of miso, a parmesan rind or a knob of butter - and roast the vegetables next time "
                "rather than boiling them.")
    return ("Soften an onion and a carrot in butter with a pinch of salt, add whatever vegetables "
            "or pulses you have and enough stock to cover them, and simmer 20 minutes. Blend it "
            "smooth or leave it chunky, taste it, and finish with salt, pepper and a squeeze of "
            "lemon.")


def _flat(memory, understood):
    """A bake that stayed flat: pancakes, Yorkshire pudding, scones and muffins fail differently."""
    words = [str(word).lower() for word in (understood.get("words") or [])]

    def has(*wanted):
        return any(_same(word, want) for word in words for want in wanted)

    if has("pancake", "pancakes", "batter", "crepe", "crepes"):
        return ("Flat pancakes are usually old baking powder or a batter that was beaten too much: "
                "use a fresh tin, stir until it is just combined, and let the batter rest 10 "
                "minutes before it hits the pan. A properly hot pan matters too - the first one is "
                "always the test.")
    if has("yorkshire", "puddings"):
        return ("Yorkshire puddings want a smoking tin and cold batter: put a little oil in each "
                "hole, heat it in a 220C oven until it shimmers, pour the batter in and don't open "
                "the door for 20 minutes.")
    if has("scon", "scones"):
        return ("Flat scones come from handling: keep the butter cold, rub it in quickly, pat the "
                "dough out rather than rolling it hard, and cut straight down with a sharp cutter so "
                "the edges stay free to rise.")
    return ("Something that came out flat is short of rise, because the baking powder was past "
            "its date, the flour was beaten after it went in, or the oven was not up to heat. "
            "Check the baking powder is in date (about half a teaspoon to 100g of flour), stop "
            "beating once the flour is in, and let the oven come fully up to heat before the tin "
            "goes in.")


_FROM_FROZEN = ("from frozen", "cook it frozen", "cooked from frozen", "without defrosting",
                "without thawing", "no need to defrost", "skip the defrosting",
                "do i have to defrost", "have to defrost", "need to defrost")
# "how long do i have to defrost 500g of mince" carries "have to defrost" and asks for a time: the
# words are the same and the question is not. A timing ask stays a thaw question.
_FROZEN_TIME = ("how long", "how many hours", "how many days", "how many minutes", "overnight",
                "thaw time", "how long does it take", "what temperature", "what temp")
# The shapes that ask whether a thaw can be skipped. "need to defrost something for dinner" names
# nothing and asks nothing, so it is not this entry's line.
# A meal ask: "what can i cook/make from frozen" wants the meal, not the thaw rule.
_FROZEN_WHAT = ("what can i cook", "what can i make", "what can we cook", "what can we make",
                "what should i cook", "what should i make", "what to cook", "meal ideas",
                "what could i cook", "what could i make")
_FROZEN_ASK = ("can i", "could i", "may i", "is it", "should i", "do i", "how do i", "ok to",
               "okay to", "safe to", "fine to", "am i able", "any way to", "is there a way")
# The cuts this answers for, and the verb that goes with each: mince is broken up in the pan, the
# rest are turned. A whole bird or a joint is not in either list - it is too thick to cook through
# from frozen, so those lines keep the thaw times they already had.
_FROZEN_CUTS = (("mince", "beef mince", "lamb mince", "pork mince"), "break it up as it loosens")
# Each cut with the way it leads the sentence, and whether it is one thing: "Bacon can go straight
# into the pan ... cook it", "Chops can ... cook them". A fixed "them" read wrong for bacon, steak
# and liver, and a bare "Chop can go straight in" needed its article - a count noun said on its own
# is a fault in the first sentence of the reply.
_FROZEN_WHOLE = (("sausage", "A sausage", True), ("sausages", "Sausages", False),
                 ("bacon", "Bacon", True), ("chops", "Chops", False), ("chop", "A chop", True),
                 ("steak", "A steak", True), ("steaks", "Steaks", False),
                 ("liver", "Liver", True), ("kidneys", "Kidneys", False))
_FROZEN_ONE = ("{} can go straight into the pan from frozen: cook it a few minutes longer than you "
               "would thawed, turning it so it colours on all sides, and check it is piping hot in "
               "the middle.")
_FROZEN_MANY = ("{} can go straight into the pan from frozen: cook them a few minutes longer than "
                "you would thawed, turning so they colour on all sides, and check they are piping "
                "hot in the middle.")


def _frozen_from_the_bag(understood):
    """Whether the line is "can I cook it from frozen", which is not a question about thaw times.

    The meat is often named in the turn before ("i forgot to defrost the mince") rather than in
    this line, so the freezer words are a key part of the entry and the reply names the cuts that
    are safe and the ones that are not.
    """
    text = " ".join(str(understood.get("clean") or "").lower().split())
    if any(word in text for word in ("turkey", "joint", "whole bird", "roasting")):
        # a bird or a joint keeps its thaw time: it is the answer to "can i cook a turkey from
        # frozen" as much as to "how long does a turkey take"
        return False
    if not any(word in text for word in _FROM_FROZEN):
        return False
    if any(word in text for word in _FROZEN_WHAT):
        # "what can i cook from frozen" is a meal question, and the quick-meal answer it had is
        # better than a yes/no about meat. The entry answers "can i cook *it* from frozen".
        return False
    if any(word in text for word in _FROZEN_TIME):
        # "how long do i have to defrost 500g of mince" asks for a time, not for a yes
        return False
    if any(word in text for word in _FROZEN_ASK):
        return True
    # with no ask in the line, only the words that name the question itself carry it
    return any(word in text for word in ("from frozen", "cooked from frozen", "cook it frozen",
                                         "without defrosting", "without thawing",
                                         "no need to defrost", "skip the defrosting"))


_FROZEN_CUT_WORDS = tuple(_FROZEN_CUTS[0]) + tuple(word for word, _, _ in _FROZEN_WHOLE)


def _frozen_cook_reply(understood):
    text = " ".join(str(understood.get("clean") or "").lower().split())
    words = text.split()
    if not any(cut in words for cut in _FROZEN_CUT_WORDS):
        # "can i just cook it from frozen" names no meat: the cut is in the turn before ("i
        # forgot to defrost the mince"). Naming it back is the whole point of the reply, so the
        # meat the line leans on is read as if it had been said here, and only the cut words
        # are taken from it - "it" leaning on a defrost is not a chop.
        lean = understood.get("leans_on")
        if isinstance(lean, dict):
            subject = str(lean.get("subject") or "").lower().split()
            words = words + [word for word in subject if word in _FROZEN_CUT_WORDS]
    if any(cut in words for cut in _FROZEN_CUTS[0]):
        led = ("Mince can go straight into the pan from frozen: brown it over a high heat, "
               "break it up as it loosens and give it a few extra minutes before the sauce goes in.")
    else:
        said, one = next(((said, one) for word, said, one in _FROZEN_WHOLE if word in words),
                        ("", False))
        if said:
            led = (_FROZEN_ONE if one else _FROZEN_MANY).format(said)
        else:
            led = ("Usually yes for small cuts - mince, sausages, bacon, chops: they can go "
                   "straight into a hot pan or a sauce from frozen, a few minutes longer than "
                   "thawed and piping hot all the way through.")
    return led + (" A whole bird or a big joint is the exception: it has to thaw first, or the "
                  "outside overcooks while the middle stays raw. Do not refreeze it once it has "
                  "started to thaw.")


def _meat_defrost(memory, understood):
    """A whole bird or a big joint needs a day or two; mince and sausages need overnight."""
    text = " ".join(str(understood.get("clean") or "").lower().split())
    if any(word in text for word in _FROZEN_WHAT) and any(
            word in text for word in ("frozen", "freezer")):
        # "what can i cook from frozen" wants a meal, and the meal answer it had on main ("Quick:
        # tuna pasta in 15, a frittata in 20") is better than the thaw times. The entry declines
        # the line so the meal entry below it gets the turn.
        return None
    if _frozen_from_the_bag(understood):
        return _frozen_cook_reply(understood)
    # A small cut named in the line wins over "joint": the composer re-asks a line like "how long
    # does it take to thaw 500g of mince" as "... for the joint?" and the answer has to stay mince.
    small = ("mince", "sausage", "sausages", "chop", "chops", "steak", "steaks", "bacon",
             "liver", "kidney", "kidneys")
    if not any(word in text for word in small) and ("turkey" in text or "bird" in text):
        # The figure first and inside its own sentence: the composer hands a time follow-up the
        # sentence around the figure, and "so a 5kg turkey wants two and a half days: ..." was
        # read back as "So a 5kg turkey wants two."
        kilos, said = _bird_weight(understood) or (None, None)
        time = f"{_hours_words(24 * kilos / 2)}" if kilos else "two and a half days"
        return (f"A turkey wants {time} in the fridge. That is 24 hours for every 2kg: leave it in "
                "its wrapper in a tray on the bottom shelf and never on the worktop, and once it is "
                "thawed cook it within 2 days. A crown thaws in 24 hours.")
    if not any(word in text for word in small) and "joint" in text:
        # The figure the line asked about, so the answer is a time and not a rate: a rate is what
        # "how long for 500g of mince" reads back as if the joint is still the subject.
        kilos, said = _bird_weight(understood) or (None, None)
        hours = f"about {_hours_words(24 * kilos / 2)}" if kilos else "a day for every 2kg"
        # The time the line asked about, not a rate the next line can reuse for something else:
        # "how long does it take to thaw 500g of mince" after this one read back the joint's rate.
        # Short sentences on purpose: a follow-up that names another cut is read by the composer
        # as "the same question with a new amount", and the first sentence is what narrow() hands
        # back, so it has to stand on its own.
        return (f"Give it {hours} in the fridge. A {said or '2kg'} one goes in the night before: "
                "leave it in its wrapper in a tray on the bottom shelf, never on the worktop, and "
                "cook it within 2 days of thawing. A rolled or boned one is quicker than one on the "
                "bone.")
    if not any(word in text for word in small):
        # A follow-up that names no meat at all ("where do i put it", "can i leave it out
        # overnight") stays on the bird or joint it was about, not on mince.
        return ("In the fridge, on a plate on the bottom shelf, never on the worktop or in warm "
                "water. A turkey or a big joint wants a day or two there; mince, sausages and "
                "chops thaw overnight, and the microwave's defrost setting is the shortcut if you "
                "are short of time - cook the meat straight away when you use it.")
    return ("In the fridge, on a plate on the bottom shelf: mince, sausages and chops thaw "
            "overnight. If you are short of time use the microwave's defrost setting and cook the "
            "meat straight away, and never thaw it on the worktop or in warm water.")


def _turkey(memory, understood):
    """A turkey crown and a whole bird take different times, so they get different numbers.

    The weight in the line is the weight the timetable is worked out on: "how long do you cook
    a 4kg turkey" was given the example's figure - "a 5kg bird takes about 3 hours 10" - for a
    bird two pounds lighter, and the two numbers in one answer did not agree.
    """
    said = " ".join([str(word).lower() for word in (understood.get("words") or [])]
                    + [str(understood.get("text") or "").lower()])
    # a line about a crown is the crown's; a plain "how long does a turkey take" is the whole bird,
    # which is what people mean in December and what the crown numbers would undercook by an hour
    if "crown" not in said:
        kilos, weight_said = _bird_weight(understood) or (5.0, "5kg")
        return ("A whole turkey roasts at 180C (160C fan) for 20 minutes per kg plus 70 minutes: a "
                f"{weight_said} bird takes about {_in_words(20 * kilos + 70)}. Cook the stuffing in "
                "a separate tray, because a stuffed bird needs longer and the middle of the "
                "stuffing is the last thing to get hot. Check the thigh at the deepest point, not "
                "the breast, for 74C, and rest it 30 to 45 minutes under foil before carving.")
    return ("Roast a turkey crown at 180C (160C fan) for 20 minutes per 500g plus 20 minutes, until "
            "a thermometer in the thickest part reads 74C, then rest it 30 minutes under foil. Salt "
            "it the night before or push butter under the skin, and cover the top with foil if it "
            "browns too fast.")


def _cut_time(understood, per_kilo, extra, example):
    """The time for the weight the line names, or the worked example when it names none.

    People nearly always say the size - "how long do i cook a 3kg turkey breast" - so the
    timetable is worked out on their own weight rather than the example's.
    """
    weight = _bird_weight(understood)
    if not weight:
        return example
    kilos, said = weight
    return "so a %s one is about %s." % (said, _in_words(kilos * per_kilo + extra))


def _turkey_cut(memory, understood):
    """A turkey cut is not a whole bird: a breast is minutes, not the three hours a bird takes."""
    said = " ".join([str(word).lower() for word in (understood.get("words") or [])]
                    + [str(understood.get("text") or "").lower()])

    def has(*words):
        return any(word in said for word in words)

    # White meat is done at 74C; the dark cuts are better taken to 80C, so each cut carries its
    # own finish line rather than one sentence bolted on the end (a leg that says 80C and then
    # "take it to 74C" is telling a person two different things).
    done = "Take it to 74C in the thickest part and rest it 10 minutes under foil."
    dark = ("Take the thickest part to 80C, where dark meat goes tender rather than tight, and "
            "rest it 10 minutes under foil.")
    if has("spatchcock"):
        return ("A spatchcocked bird is flat, so it roasts fast and even: 200C (180C fan) at 20 "
                "minutes per kg, "
                + _cut_time(understood, 20, 0, "so a 4kg one is about 1 hour 20 minutes.")
                + " " + done)
    if has("wing", "wings"):
        return ("Turkey wings roast at 200C (180C fan) in 25 to 30 minutes, turned once, and they "
                "are done at 74C in the thickest part, so rest them 5 minutes under foil.")
    if has("drumstick", "drumsticks"):
        return ("Turkey drumsticks take 35 to 40 minutes at 200C (180C fan), turned once so the "
                "skin browns all over. " + dark)
    if has("leg", "legs"):
        return ("Turkey legs take 45 to 50 minutes at 190C (170C fan), skin side up, turned once. "
                + dark)
    if has("thigh", "thighs"):
        return ("Boneless turkey thighs take 40 to 45 minutes at 190C (170C fan); bone-in ones "
                "want 10 minutes more. " + dark)
    if has("fillet", "fillets", "steak", "steaks", "scallop", "scallops"):
        return ("Turkey fillets, steaks and escalopes are thin and quick: 20 to 25 minutes at "
                "190C (170C fan), or 8 to 10 minutes in a hot pan. They are done at 74C, so "
                "check one and rest them 5 minutes under foil.")
    # a breast, bone in or rolled: the last of the timetables, because every other cut is a
    # longer word that would also match this one
    boneless = has("boneless", "rolled", "butterflied", "flat")
    if boneless:
        return ("A boneless, rolled turkey breast wants 30 minutes per 500g at 190C (170C fan), "
                + _cut_time(understood, 60, 0, "so a 1.5kg one takes about 1 hour 30 minutes.")
                + " " + done)
    return ("A bone-in turkey breast takes 20 minutes per 500g plus 20 at 190C (170C fan), "
            + _cut_time(understood, 40, 20, "so a 2kg one is about 1 hour 40 minutes.")
            + " " + done)


def _hummus(memory, understood):
    """Hummus, and hummus when there is no tahini in the house."""
    said = " ".join([str(word).lower() for word in (understood.get("words") or [])]
                    + [str(understood.get("text") or "").lower()])
    no_tahini = ("no tahini" in said or "without tahini" in said or "tahini free" in said
                 or "tahini" in said and any(phrase in said for phrase in (
                     "dont have", "don't have", "ran out", "out of", "none", "substitute",
                     "instead of", "replace")))
    if no_tahini:
        return ("Without tahini, blitz the drained tin of chickpeas with the juice of a lemon, a "
                "small garlic clove, a good pinch of salt and 2 tablespoons of olive oil, then "
                "loosen it with iced water a spoon at a time. A spoon of yogurt or a second squeeze "
                "of lemon stands in for the richness the tahini would give.")
    return ("Blitz a drained tin of chickpeas with 2 tablespoons of tahini, the juice of a lemon, a "
            "small garlic clove and half a teaspoon of salt, then loosen it with iced water a spoon "
            "at a time - that is what makes it fluffy. A pinch of bicarbonate of soda in the pan "
            "softens the skins if you boil your own chickpeas.")


# A joint is three timetables, and a pork question must not open with "beef and lamb": the meat
# in the line picks the row, and a line that names none gets the rule that covers them all.
JOINT_BEEF = ("Beef or lamb: 20 minutes at 220C (200C fan) to brown it, then 190C (170C fan) for "
              "15 minutes a 500g for rare, 20 for medium and 25 for well done. The reliable check "
              "is a meat thermometer in the thickest part - 52C rare, 60C medium, 70C well done - "
              "and rest it 20 minutes under foil before carving.")
JOINT_PORK = ("Pork wants 30 minutes a 500g at 180C (160C fan), cooked right through with no pink "
              "in the middle, and crackling needs the oven at 220C (200C fan) for the first 25 "
              "minutes. A meat thermometer in the thickest part should read 70C, then rest the "
              "joint 20 minutes under foil before carving.")
# What turns a line about a joint into a line about keeping it.
GOING_OFF_ASK = ("go off", "goes off", "going off", "gone off", "went off", "shelf life",
                 "use by", "freezer", "fridge", "leftover", "leftovers")
KEEPING_VERB = ("keep", "keeps", "keeping", "kept", "last", "lasts", "freeze", "freezes")
# The words that make the line a line about cooking the joint, whatever it says about keeping it.
IN_THE_OVEN = ("oven", "roast", "roasting", "roasted", "cook", "cooks", "cooking", "cooked",
               "temperature", "gas mark", "how long do i", "how long should i")


def _roast_joint(memory, understood):
    """The joint the line names gets its own timetable first."""
    # A joint that is going off, or being kept, is a keeping question and not a roasting one:
    # "how long till ham goes off" got the 30-minutes-a-500g pork timetable. The same words
    # stand the roast-chicken row down, and the keeping tables answer with the days.
    line = " ".join(str((understood or {}).get("text") or "").lower().split())
    if any(phrase in line for phrase in GOING_OFF_ASK):
        return None
    # A bare keeping verb is not enough on its own: "how long should i keep a pork joint in the
    # oven" is the timetable that asks for, and standing the joint's row down handed it to the
    # red-meat allowance underneath (apt-scissors, #7891).
    if (any(phrase in line for phrase in KEEPING_VERB)
            and not any(word in line for word in IN_THE_OVEN)):
        return None
    words = [str(word).lower() for word in (understood.get("words") or [])]
    pork = ("pork", "pork joint", "leg of pork", "shoulder of pork", "loin of pork",
            "belly pork", "ham", "gammon")
    if any(_same(word, wanted) for word in words for wanted in ("pork", "gammon", "ham")):
        return JOINT_PORK
    if any(_same(word, wanted) for word in words for wanted in ("beef", "lamb", "mutton")):
        return JOINT_BEEF
    return JOINT_BEEF + " " + JOINT_PORK


# A keeping question about a food is the keeping tables' (bot/knowledge/keeping_cooked.py,
# cooking.py's own keep- rows), not how to cook it. "can i freeze cooked mince" was answered
# with how to brown a packet of it, because the food and the word "cook" in "cooked" were
# enough for the how-to row.
KEEPING_SENSE = ("freeze", "freezes", "freezer", "freezing", "frozen", "defrost", "defrosted",
                 "fridge", "refrigerate", "refrigerated", "reheat", "reheated", "reheating",
                 "refreeze", "keep", "keeps", "keeping", "kept", "last", "lasts", "storage",
                 "store", "stored", "storing", "leftover", "leftovers")


# A grainy sauce is the mince's question, not sugar's: "my bolognese came out grainy, not smooth"
# was a shrug, because the sugar row holds the word "grainy" and stands down on meat and pasta.
# Any mince dish goes, named the way people name it.
# "mincemeat" is not one: it is fruit and suet in a jar, with no browning and no pan juice, so
# "why is my mincemeat grainy" (a mince pie, more of it in December) was handed a confident and
# wrong cause by a word that reads like mince. A line that says mincemeat and meat together is a
# mince line, and the meat word is enough for it on its own.
_MINCE_GRAIN_DISH = ("bolognese", "bolognaise", "bol", "ragu", "ragout", "mince", "minced",
                     "chilli", "chili", "con carne", "lasagne", "lasagna",
                     "cottage pie", "shepherds pie", "shepherd's pie", "keema", "meat sauce",
                     "spag bol", "spaghetti bolognese", "taco", "tacos", "taco meat")
_MINCE_GRAIN_WORD = ("grainy", "gritty", "granular", "pellets", "grains")
# The same objection one word up: a mince pie is fruit and suet in pastry, so it has no pan
# juice and no browning to get wrong, and "my mince pies went grainy" was handed the hot-pan
# card. It is the two words together, not "pie" anywhere: a cottage pie and a shepherd's pie are
# mince dishes and real gains, so a bare "pie" cannot go in the entry's avoid list.
_MINCE_PIE_PHRASE = re.compile(r"\bmince ?pies?\b")
# A named bolognese that went grainy already has a fuller answer of its own in dishes.py ("Grainy
# bolognese is the mince rather than the tomato ... a long bare simmer, a sieve"), so this row
# stands down for it and stays for the dishes dishes.py has no word for (a ragu, a chilli, a
# lasagne, a taco, a cottage pie). The one bolognese shape it keeps is "sauce": there the
# split-sauce row takes the line and offers cold cream, which is the wrong fault altogether.
_BOLOGNESE_WORDS = ("bolognese", "bolognaise", "spag bol", "spaghetti bolognese", "bol")


def _mince_grainy(memory, understood):
    """Mince that has gone grainy: the pan was not hot enough, so it boiled instead of browning.

    The cause is the same for a bolognese, a ragu, a chilli and a lasagne, so the answer is one
    and the rescue is in the pot already on the stove.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, sense) for word in words for sense in KEEPING_SENSE):
        return None  # a keeping question about mince belongs to the keeping rows
    if _MINCE_PIE_PHRASE.search(" ".join(words)):
        return None  # a mince pie is fruit and suet: no browning to get wrong
    if (any(_same(word, name) for word in words for name in _BOLOGNESE_WORDS)
            and not any(_same(word, "sauce") for word in words)):
        return None  # dishes.py keeps the fuller answer for a named grainy bolognese
    # The first instruction is written as one, in its own sentence, because the follow-up rows
    # hand the first step of the last answer back to a "how do i stop that": read out of a
    # "next time get the pan hot, brown it, then add the tomatoes", that row found "add the
    # tomatoes" and told the person to do the last thing first.
    return ("A grainy sauce is usually the mince: it went into a pan that was not hot enough, so "
            "it boiled in its own juice instead of browning. Heat a heavy pan until a drop of "
            "water sizzles, then brown the mince in two batches. Leave it alone for 2 to 3 "
            "minutes at a time so it colours before the liquid goes in. For the pot you have, "
            "give it a slow half hour with the lid on, which softens the grains, and stir in a "
            "spoon of butter at the end.")


def _mince(memory, understood):
    """Browning mince, and why mince comes out tough, want different answers."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if any(_same(word, sense) for word in words for sense in KEEPING_SENSE):
        return None  # a keeping question about mince belongs to the keeping rows
    if any(_same(word, tough) for word in words
           for tough in ("tough", "rubbery", "chewy", "dry")):
        return ("Minced meat goes tough and grainy when it is cooked too long or boiled in its own "
                "juice: brown it fast in a hot pan in batches, then add liquid only once it has "
                "coloured. A pinch of bicarb (half a teaspoon per 500g) keeps it soft in a long "
                "bolognese.")
    return ("Brown mince in batches over a high heat and don't stir it much: it should sizzle and "
            "colour, not steam. Pale, grey mince is mince that was crowded in the pan.")


VAGUE = frozenset({"vegetables", "veg"})
# The same words as the pantry keys them, so a pair drops "veg" whichever form reached it.
_VAGUE_KEYS = frozenset({"vegetables", "vegetable", "veg"})


# Food families an eater may name as something they avoid. A group word ("meat", "dairy")
# stands for every food in that family, so "no meat" also rules out chicken and bacon.
MEAT = frozenset("meat chicken beef pork lamb mince bacon sausage sausages ham turkey prawn "
                 "prawns".split())
# Fish is the one food people who say "i don't eat meat" often do eat, so a bare meat ban does
# not confiscate it: it is a family of its own, and a vegetarian or vegan ban carries both. A
# prawn stays in meat as well as shellfish, because a vegetarian does not eat one either.
FISH = frozenset("fish salmon cod tuna".split())
DAIRY = frozenset("dairy milk cheese butter cream yoghurt yogurt".split())

# "no cheese" is a ban on the cheeses, and feta and halloumi are cheeses the dish names by their
# own name: a cheap dinner with feta crumbled over it was offered to someone who had just said no
# cheese, because the reply never says the word "cheese".
CHEESES = frozenset("feta halloumi parmesan mozzarella cheddar gruyere stilton brie camembert "
                    "ricotta paneer pecorino gouda edam wensleydale".split())
EGGS = frozenset("egg eggs".split())
NUTS = frozenset("nut nuts peanut peanuts".split())
# What gluten is, in the words a recipe uses: a coeliac is not avoiding a word, they are
# avoiding bread, pasta and flour, so the family is every everyday food those are made of.
GLUTEN = frozenset("gluten wheat pasta spaghetti bread toast flour couscous noodles barley rye "
                   "bulgur semolina cracker crackers cake biscuit biscuits pastry pitta".split())
# Shellfish is its own family: a prawn is meat to a vegetarian and a shellfish to someone who
# carries an epipen, and a ban on one is not a ban on the other.
SHELLFISH = frozenset("shellfish prawn prawns crab crabs lobster mussels oysters squid clams "
                      "scallops".split())
FAMILIES = {"meat": MEAT, "fish": FISH, "dairy": DAIRY, "egg": EGGS, "nut": NUTS,
            "gluten": GLUTEN, "shellfish": SHELLFISH}
# A vegetarian or a vegan does not eat fish either, and the diet words carry both families.
NO_MEAT_DIET = MEAT | FISH

# A condition said out loud rules out a food the way an allergy does: "im coeliac" is gluten,
# "im lactose intolerant" is dairy. Without this the ack promised to plan around it and the
# next meal was pasta and toast anyway.
CONDITION_BANS = {"coeliac": GLUTEN, "celiac": GLUTEN, "gluten intolerant": GLUTEN,
                  "lactose intolerant": DAIRY}
# "im not coeliac, what can i cook" is the one thing that must not turn the list gluten free: the
# words of a denial are the words of the condition, and the negator in front is what tells them
# apart. Same guard as bot/memory/facts.DENIAL_WORDS, kept here so the knowledge base stays data.
NOT_THIS = re.compile(r"(?:\bnot|\bnon|\bnever|\bno longer|\bn't|\baint|\bain't)\s+"
                      r"(?:really\s+|actually\s+|even\s+)?(?:a\s+|an\s+|any\s+|\bat all\s+)?$")

# "no cheese", "without cheese", "i don't eat cheese", "allergic to nuts", "cheese free".
# The negator has to come from a short, explicit list of ways people refuse a food, so an
# ordinary "not sure about cheese" or "don't have much cheese" does not count.
FOOD = (r"(meat|chicken|beef|pork|lamb|mince|bacon|sausage|sausages|ham|turkey|fish|salmon|"
        r"cod|tuna|prawn|prawns|shellfish|crab|lobster|mussels|oysters|squid|clams|"
        r"dairy|milk|cheese|butter|cream|yoghurt|yogurt|egg|eggs|"
        r"nut|nuts|peanut|peanuts|gluten)")
AVOIDED = re.compile(
    r"\b(?:no|without)\s+(?:(?:any|more|the|any more)\s+)?" + FOOD + r"\b"
    r"|\b(?:dont|don't|do not|doesnt|doesn't|does not|didnt|didn't|did not|cant|can't|"
    r"cannot|wont|won't|will not|wouldnt|wouldn't|refuse|refuses|refused|never)\s+"
    r"(?:eat|eating|have|use|using|cook with|want|touch|order)\s+(?:any\s+)?"
    r"(?:really\s+|usually\s+)?" + FOOD + r"\b"
    r"|\b(?:allergic|allergy|intolerant|intolerance)\s+to\s+" + FOOD + r"\b"
    r"|\b(?:hate|hates|avoid|avoiding|skip|skipping|off|cutting out|cut out)\s+"
    r"(?:the\s+|all\s+)?" + FOOD + r"\b"
    r"|\bnot\s+(?:a fan of|keen on|fussed about)\s+" + FOOD + r"\b"
    # A food said to be missing rather than refused: "i havent got any cheese", "there's no
    # milk left", "we got no rice". Said after an idea, it is a limit on that idea, and the
    # dish that needs it is no answer.
    r"|\b(?:havent|haven't|hasnt|hasn't|hadnt|hadn't)\s+(?:got|any)\s+(?:any\s+)?" + FOOD
    + r"\b"
    r"|\b(?:there\s+is\s+no|there's\s+no|theres\s+no|got\s+no|we\s+have\s+no|i\s+have\s+no)\s+"
    + FOOD + r"\b")
FREEFROM = re.compile(
    r"\b(meat|dairy|milk|cheese|gluten|wheat|nut|nuts|peanut|peanuts|egg|eggs)\s+free\b")
# "a nut allergy", "lactose intolerant" name the family before the problem word.
TROUBLE = re.compile(
    r"\b(nut|nuts|peanut|peanuts|dairy|milk|lactose|egg|eggs)\s+"
    r"(?:allergy|allergies|intolerance|intolerant)\b")


def _said_so_far(understood, memory):
    """The line with the last few turns in front of it, oldest first.

    An exclusion given a turn or two ago still holds ("i'm vegetarian" then "what can I cook"),
    and the order matters: "im coeliac" then "im not coeliac" is a person taking it back, and only
    the later mention should count.
    """
    # The line as the engine read it, not as it was typed: a slip inside the asking word is
    # still the ask ("i need a recipie for shortbread" asks for the method), and every reader of
    # this text matches the words of it.
    line = line_as_read(understood)
    earlier = []
    turns = memory.get("turns")
    if isinstance(turns, list):
        earlier = [str(turn.get("user") or "") for turn in turns[-4:] if isinstance(turn, dict)]
    return " ".join(earlier + [line])

_PEOPLE_AFTER = r"(?:people|persons?|of us|of you|guests|adults|heads|folk|for dinner|for lunch)"
# The words for a count, as a pattern. Not "COUNT_WORDS": a table of that name further down is
# a dict, and the later binding wins for the whole module, so _head_count used to interpolate the
# dict's own text into its regexes and never match a number said in words - "a sunday roast for
# six people" lost its six, and the shopping list told ten people to buy for six.
_COUNT_WORD_SHAPES = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
_COUNT_VALUE = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


# A meatless roast is not a joint. "what do i need to buy for a nut roast" was told to buy 1.5kg
# of raw joint, which is the one thing the person is not buying, and the diet words above only
# catch a line that says "vegetarian" out loud. Naming the meatless roasts is the honest fix.
MEATLESS_ROAST = ("nut roast", "nutroast", "nut wellington", "nut loaf", "lentil roast",
                  "lentil loaf", "bean roast", "chickpea roast", "vegetable roast",
                  "vegetable wellington", "veg roast", "veggie roast", "tofu roast",
                  "tofu wellington", "seitan roast", "halloumi roast", "mushroom wellington",
                  "mushroom roast", "cauliflower roast", "beetroot roast", "vegan roast",
                  "vegetarian roast")


def _head_count(text):
    """The number of people a roast line says, or None when it only has a time in it.

    "my roast chicken needs 10 more minutes" is a timing line: reading its 10 as people is how a
    shopping list once told someone to buy 2.5kg of meat. A number only counts people when people
    are named beside it, or when it closes a "for N" phrase.
    """
    text = str(text or "").lower()
    when = (r"(?:on\s+\w+day|tonight|tomorrow|this weekend|next week|at the weekend|"
            r"this christmas|for christmas)")
    shapes = (rf"\bfor\s+(\d{{1,2}})\s*{_PEOPLE_AFTER}", rf"\bfor\s+({_COUNT_WORD_SHAPES})\s*{_PEOPLE_AFTER}",
              rf"\b(\d{{1,2}})\s*{_PEOPLE_AFTER}", rf"\b({_COUNT_WORD_SHAPES})\s*{_PEOPLE_AFTER}",
              rf"\bfor\s+(\d{{1,2}})\s*{when}", rf"\bfor\s+({_COUNT_WORD_SHAPES})\s*{when}",
              rf"\bfor\s+(\d{{1,2}})\s*(?=[,.!?]|$)", rf"\bfor\s+({_COUNT_WORD_SHAPES})\s*(?=[,.!?]|$)",
              # "we are 9 for christmas dinner" says how many are coming
              rf"\bwe(?:'re| are)\s+(\d{{1,2}})\b", rf"\bwe(?:'re| are)\s+({_COUNT_WORD_SHAPES})\b")
    for shape in shapes:
        found = re.search(shape, text)
        if not found:
            continue
        value = found.group(1)
        number = int(value) if value.isdigit() else _COUNT_VALUE.get(value)
        if number and 2 <= number <= 20:
            return number
    return None


def _roast_shopping(memory, understood):
    """A shopping list for a roast dinner, sized by the people in the line.

    "what do i need to buy for a sunday roast" was a shrug: the dish words were there and the
    buying word was there, but nothing joined them. The amount is the useful half, and it depends
    on what is being roasted, so a bird gets a bird's amount and never the word "joint".
    """
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    people = _head_count(text)
    trimmings = ("potatoes, carrots, parsnips or swede, and something green like cabbage or "
                 "sprouts, plus oil, and stock and flour for the gravy")
    if "turkey" in text or "christmas dinner" in text or "xmas dinner" in text:
        per, bird, timing = BIRD_GRAMS, "turkey", "20 minutes per 500g plus 90"
        if people:
            body = (f"About {people * per / 1000:g}kg of turkey for {people}, at {per}g a person "
                    f"on the bone")
        else:
            body = ("Most people do turkey: about 500g a person on the bone, so a 4kg bird feeds "
                    "eight")
    elif "chicken" in text:
        # A bird feeds people on the bone, and units.BIRD_GRAMS is where the bot keeps that
        # number: 500g a person, so the same chicken asked in three ways gets one amount.
        per, bird, timing = BIRD_GRAMS, "chicken", "20 minutes per 500g plus 20"
        if people:
            body = (f"About {people * per / 1000:g}kg of chicken for {people}, at {per}g a person "
                    f"on the bone")
        else:
            body = (f"About {per}g of chicken a person on the bone, so a 3kg bird feeds six and a "
                    "1.5kg one feeds three")
    else:
        per, bird = 250, ""
        timing = "20 minutes per 500g plus 20"
        if people:
            body = (f"About {people * per / 1000:g}kg of raw joint for {people}, which is 250g a "
                    f"person")
        else:
            body = "For a roast: about 250g of raw joint a person, so 1.5kg feeds six"
    text_out = (f"{body}. Then {trimmings}. For timing, work on {timing} at 200C (180C fan), and "
                "rest it 15 minutes before carving.")
    if not bird:
        text_out += (" Add flour, eggs and milk for Yorkshire puddings, and mint or apple sauce if "
                     "it is lamb or pork.")
    return text_out


# A question about whether a food is vegetarian ("is a croissant vegetarian", "does gelatin count
# as vegetarian") is not this person saying they are one. Reading it as a diet made every reply
# that named the thing being asked about unusable - "are chips vegetarian" lost the answer about
# dripping and "is wine vegetarian" the one about isinglass, because the reply named beef and fish
# and the filter that keeps the food a person refuses out of an answer threw it away. The words
# that open the question are the whole distinction: "im vegetarian" and "ive been vegetarian for
# years" keep their reading, and a question keeps the food.
_DIET_ASKED = re.compile(
    r"\b(?:is|are|was|were|does|do|isnt|isn't|arent|aren't)\s+"
    r"((?:[a-z']+\s+){0,3}?)(?:vegetarian|vegan|veggie|vego)\b", re.I)
# The words between the opening and the diet word say whether a food is being asked about. "are
# chips vegetarian" and "does gelatin count as vegetarian" name the thing; "is there anything
# vegetarian", "is it vegetarian" and "is that ok for a vegetarian" do not, and those stay a diet.
_DIET_ASK_NOT_A_FOOD = frozenset(
    "there anything something any this that it these those he she they him her them my your our "
    "their his its ok okay fine alright safe suitable good bad healthy fine too also still".split())


def _ask_about_the_food(text, at):
    """Whether the diet word at this position is a question about a food, not a diet."""
    for match in _DIET_ASKED.finditer(text[:at]):
        if match.end() <= at and not (_DIET_ASK_NOT_A_FOOD & set(match.group(1).split())):
            return True
    return False


def _excluded(text):
    """The food words a line says to leave out, with group words expanded to their family.

    Any mention of the diet counts, not only "i'm a vegan": "lunch for a vegetarian", "something
    for someone who is vegan" and "a veggie guest" are the same diet, and the food words a person
    states elsewhere in the line still have to be left out. The mentions are then read in the
    order they were said, because the last thing said about a food is the one that holds: "im
    allergic to nuts" and then "im not allergic to nuts" is a person taking it back, not both at
    once. That is also how a condition is read, so a denied allergy and a denied coeliac are the
    same question and get the same answer.
    """
    text = str(text or "").lower().replace("\u2019", "'").replace("-", " ")
    events = []

    def note(position, families, positive=True):
        events.append((position, families, positive))

    for match in re.finditer(r"\b(?:vegetarian|veggie|vego)\b", text):
        if _ask_about_the_food(text, match.start()):
            continue
        note(match.start(), NO_MEAT_DIET, not _denied_at(text, match.start()))
    for match in re.finditer(r"\b(?:vegan|plant based|plantbased)\b", text):
        if _ask_about_the_food(text, match.start()):
            continue
        note(match.start(), NO_MEAT_DIET | DAIRY | EGGS, not _denied_at(text, match.start()))
    # A food named inside a denial is a food they can eat again: "im not allergic to nuts" is the
    # opposite of an allergy, and the words before the match are what tell the two apart.
    for pattern in (AVOIDED, FREEFROM, TROUBLE):
        for match in pattern.finditer(text):
            word = next((part for part in match.groups() if part), "")
            if not word:
                continue
            families = _families_of(word)
            denied = _denied_at(text, match.start())
            note(match.start(), families, not denied)
            # The list the food was said in is a list: the words after it ("peanuts and
            # cheese") and, for "X and Y free", the words before it are read too.
            note(match.start(), _foods_in_list(_list_words(text[match.end():match.end() + 80])),
                 not denied)
            if pattern is FREEFROM:
                note(match.start(),
                     _foods_in_list(_list_words(text[max(0, match.start() - 80):match.start()],
                                              backwards=True)), not denied)
    for condition, foods in CONDITION_BANS.items():
        for match in re.finditer(r"\b" + condition.replace(" ", r"\s+") + r"\b", text):
            note(match.start(), foods, not _denied_at(text, match.start()))
    state = {}
    for _position, families, positive in sorted(events, key=lambda event: event[0]):
        for word in families:
            state[word] = positive
    banned = {word for word, on in state.items() if on}
    # "no cheese" is a ban on the cheeses, and a feta or a halloumi is a cheese the dish names by
    # its own name: a cheap dinner with feta crumbled over it was offered to someone who had just
    # said no cheese, because the reply never says the word "cheese".
    if "cheese" in banned or DAIRY & banned:
        banned.update(CHEESES)
    return banned


# A lactose intolerance is about how much milk sugar is in the portion, so it is not the same
# plate as a dairy allergy or a vegan diet: the words that say it, and the words that say one of
# those instead (which keep the dairy ban as it is).
_LACTOSE_WORDS = ("lactose", "milk sugar", "lactase")
_NOT_LACTOSE_WORDS = ("vegan", "dairy free", "dairy-free", "no dairy", "allergic", "allergy",
                      "anaphyla", "milk protein", "cut out dairy", "give up dairy", "avoid dairy")


def _a_lactose_intolerance(said):
    """True when the words say a lactose intolerance and nothing that is a dairy allergy."""
    if not any(word in said for word in _LACTOSE_WORDS):
        return False
    plain = said.replace("\u2019", "'")
    return not any(word in plain for word in _NOT_LACTOSE_WORDS)


def _record_says_lactose(known):
    """True when one person's record says a lactose intolerance and nothing stronger."""
    if not isinstance(known, dict):
        return False
    said = []
    for key in ("allergies", "diet", "diets", "condition", "conditions"):
        value = known.get(key)
        if isinstance(value, str):
            said.append(value)
        elif isinstance(value, (list, tuple, set)):
            said.extend(str(one) for one in value)
    return _a_lactose_intolerance(" ".join(said).lower().replace("-", " "))


def _their_diet_is_a_lactose_intolerance(memory):
    """True when what the store keeps about this person says a lactose intolerance.

    "my husband is lactose intolerant" then "what can he have" is the same question a turn later,
    and the line itself no longer says the words.
    """
    if not isinstance(memory, dict):
        return False
    known = None
    try:
        import bot.modules.memory_store as _store
        known = _store.user(memory) or {}
    except Exception:
        known = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    return _record_says_lactose(known)


# The words that join a list of foods: "allergic to peanuts and cheese", "gluten and dairy
# free". Only the connectors are skipped, so the reading stops at the first word that is not a
# food and a clause like "i dont eat meat, what can i cook" does not invent a ban on "what".
LIST_JOINERS = frozenset(("and", "or", "plus", "with", "also", "as", "well", "&", "+", ","))
# Every word that names a food or a food family on its own, so a list can be read word by word.
LIST_FOODS = frozenset(FAMILIES) | EGGS | NUTS | GLUTEN | DAIRY | SHELLFISH | FISH | MEAT \
    | CHEESES | frozenset(("lactose",))


def _families_of(word):
    """What one food word rules out: the family it names, or the word itself."""
    if word == "lactose":
        return DAIRY
    if word == "wheat":
        return GLUTEN  # "wheat free" is the same shop as "gluten free"
    return FAMILIES.get(word, {word})


def _foods_in_list(words):
    """The foods a list names, read until something that is not one.

    "allergic to peanuts and cheese" named two foods and only the first was read, and the same
    with "gluten and dairy free" - a coeliac who cannot have milk got one of the two.
    """
    found = set()
    for word in words:
        word = word.strip(".,!?;:'")
        if not word:
            continue
        if word in LIST_JOINERS:
            continue
        if word not in LIST_FOODS:
            break
        found |= _families_of(word)
    return found


def _list_words(text, backwards=False):
    if backwards:
        return list(reversed(re.findall(r"[a-z']+|[&+,]", str(text or "").lower())))
    return re.findall(r"[a-z']+|[&+,]", str(text or "").lower())


def _denied_at(text, start):
    """True when the words just before `start` deny what is said at it ("im not ...")."""
    return bool(NOT_THIS.search(text[max(0, start - 30):start]))


# "Can I eat this?" after they have told us what they avoid. The answer is not a recipe, it is
# a yes or a no about one food, and the store already knows the constraint: the food a person
# names is checked against what they said, so "is satay safe for me" after a peanut allergy is
# a no about peanuts rather than a search hedge. Only the first person counts, because the
# answer is about them.
EAT_ASK = re.compile(
    r"\b(?:can|could|may|should|shall)\s+i\s+(?:eat|have|drink|order|try)\s+(?P<a>[\w ']+)"
    r"|\b(?:is|are)\s+(?P<b>[\w ']+?)\s+(?:ok|okay|fine|alright|safe|allowed)\s+"
    r"(?:for\s+me|for\s+us)\b"
    r"|\bam\s+i\s+(?:ok|okay|fine|alright|safe|allowed)\s+(?:to\s+(?:eat|have|drink)\s+)?"
    r"(?P<c>[\w ']+)"
    r"|\b(?:is|would)\s+(?P<d>[\w ']+?)\s+(?:be\s+)?(?:bad|wrong|a\s+problem)\s+for\s+me\b",
    re.I)

# A dish a person is only considering is the same yes-or-no question as "can I eat this", said
# as a plan: "i was thinking of a satay" a turn after a peanut allergy wants the check, not
# agreement. Only the first person and only the considering words, because a dish they are
# already cooking is the plan table's line ("im making a lasagne tonight").
FANCY_ASK = re.compile(
    r"\b(?:i\s+(?:fancy|fancied|fancying|crave|craved|craving|feel like|quite fancy|"
    r"really fancy|was thinking (?:of|about)|thought (?:i'd|i would|of having|about having)|"
    r"was going to (?:have|make|get)|was planning (?:to have|to make|on))|"
    r"i(?:'m| am)\s+(?:thinking (?:of|about)|craving|feeling like)|"
    r"i(?:'d| would)\s+(?:go for|have|make))\s+", re.I)

# The same question about somebody else: "can she eat pesto", "can my son have cake", "is satay
# ok for him". It is a question about that person's own record, never about the person typing,
# so it is answered from the guest's allergy or condition and from nobody else's.
EAT_ASK_THEM = re.compile(
    r"\b(?:can|could|may|should|shall)\s+(?:he|she|they|him|her|them|it"
    r"|(?:my|our|the)\s+[a-z']+)\s+(?:eat|have|drink|order|try)\s+(?P<a>[\w ']+)"
    r"|\b(?:is|are)\s+(?P<b>[\w ']+?)\s+(?:ok|okay|fine|alright|safe|allowed)\s+for\s+"
    r"(?:him|her|them|(?:my|our|the)\s+[a-z']+)\b"
    r"|\b(?:is|would)\s+(?P<d>[\w ']+?)\s+(?:be\s+)?(?:bad|wrong|a\s+problem)\s+for\s+"
    r"(?:him|her|them|(?:my|our)\s+[a-z']+)\b",
    re.I)

# The foods whose usual recipe is what makes them what they are, with the families they are
# made of. A dish is only here when leaving a family out would leave a different dish: satay is
# peanuts and a croissant is butter, while a caesar salad can be made without anchovy. A food
# with no family at all is one we can say yes about.
MADE_OF = {}
for _names, _families in (
        (("peanut", "peanuts", "satay", "pesto", "marzipan", "baklava", "praline", "nutella", "muesli", "granola",
          "nut roast", "peanut butter", "almond", "almonds", "cashew", "cashews", "walnut",
          "walnuts", "hazelnut", "hazelnuts", "pecan", "pecans", "pistachio", "pistachios"),
         (NUTS,)),
        (("pasta", "spaghetti", "bread", "toast", "noodles", "couscous", "pastry", "cake",
          "biscuit", "biscuits", "cracker", "crackers", "pitta", "flour", "crumpet", "bagel",
          "wrap", "wraps", "barley", "rye", "semolina", "scone", "scones", "pizza", "sandwich",
          # Ordinary soy sauce is brewed with wheat, which is the one that catches people out.
          "soy sauce", "soya sauce"),
         (GLUTEN,)),
        # A cake is flour and butter and egg, and a quiche is pastry, cream and egg: a table that
        # says only "wheat" turns a milk allergy into a confident yes about a cake. These are
        # still not everything a bought one can hold, which is why the yes about them is hedged.
        (("cake", "cakes", "quiche", "quiches"), (GLUTEN, DAIRY, EGGS)),
        (("cheese", "butter", "cream", "milk", "yoghurt", "yogurt", "ice cream", "custard",
          "paneer", "halloumi", "mozzarella"), (DAIRY,)),
        # A plant milk is not milk. The table only knew the word "milk", so "is oat milk ok" after
        # "im allergic to dairy" was answered "no: that is dairy" - and the drink a dairy-free
        # person can have is the one thing the answer must not take off them. The nut milks keep
        # the nut they are made of, because almond milk is still almonds.
        (("oat milk", "soy milk", "soya milk", "rice milk", "coconut milk", "hemp milk",
          "pea milk", "plant milk", "oat drink", "soya drink"), ()),
        (("almond milk", "cashew milk", "hazelnut milk"), (NUTS,)),
        (("croissant",), (GLUTEN, DAIRY)),
        (("chicken", "beef", "steak", "pork", "lamb", "bacon", "ham", "sausage", "sausages",
          "turkey", "mince", "gelatine", "lard"), (MEAT,)),
        (("fish", "salmon", "tuna", "cod"), (FISH,)),
        (("prawn", "prawns", "crab", "crabs", "lobster", "mussels", "oysters", "squid", "clams",
          "scallops", "shellfish"), (MEAT, SHELLFISH)),
        (("egg", "eggs", "mayonnaise", "mayo", "meringue", "omelette"), (EGGS,)),
        # Plain foods that are in none of the families, so a "can I eat this" about one gets a
        # yes rather than a search hedge from someone who has just told us what they avoid.
        (("rice", "potato", "potatoes", "chips", "lentils", "chickpeas", "beans", "quinoa",
          "corn", "tofu", "fruit", "vegetables", "veg", "salad", "broccoli", "carrot",
          # The flours and grains people ask about by name: none of these is wheat, and
          # "is cornflour gluten free" was a shrug while the answer was the table's own.
          "buckwheat", "cornflour", "corn flour", "rice flour", "gram flour", "tamari",
          # The raising agents: a plain baking powder is rice flour and bicarbonate, and
          # "is baking powder gluten free" got the gluten-free cake blend.
          "baking powder", "bicarbonate of soda", "bicarb", "cream of tartar", "yeast",
          "baking soda",
          "carrots", "spinach", "peas", "banana", "bananas", "apple", "apples", "oranges",
          "oats", "porridge", "honey", "fig", "figs", "olive oil", "oil", "salt", "sugar", "tinned tomatoes",
          "tomato", "tomatoes", "onion", "onions", "garlic", "courgette", "courgettes",
          "sweet potato", "sweet potatoes", "squash", "mushrooms"), ()),
):
    for _name in _names:
        MADE_OF[_name] = frozenset().union(*_families)

# How to say what the food is, and what does the same job without it. The first part is the
# whole predicate, because a chicken is meat and not made with it.
FAMILY_SAY = {
    id(NUTS): ("is made with nuts", "sunflower seeds or a spoon of yoghurt give the same crunch"),
    id(GLUTEN): ("is made with wheat flour", "rice, potatoes or a corn pasta do the same job"),
    id(DAIRY): ("is made with milk", "olive oil or a dairy-free spread does the same job"),
    id(EGGS): ("is made with egg", "a spoon of yoghurt where a recipe asks for one does the same"),
    id(MEAT): ("is meat", "chickpeas, lentils or tofu fill the same gap"),
    id(FISH): ("is fish", "chickpeas, lentils or tofu fill the same gap"),
    id(SHELLFISH): ("is shellfish", "chickpeas, lentils or tofu fill the same gap"),
}
# A food that *is* the family ("can i eat eggs" for a vegan) cannot be "made with egg": the
# honest answer is that the food is the thing itself. Gluten is left out on purpose, because
# bread is made with wheat flour rather than being it, and that sentence already reads right.
SELF_SAY = {id(NUTS): "that is nuts", id(DAIRY): "that is dairy", id(EGGS): "that is egg",
            id(MEAT): "that is meat", id(FISH): "that is fish", id(SHELLFISH): "that is shellfish"}
# "i don't eat meat" is the ban people mean differently, and neither a no nor a yes about fish
# is honest: the answer names the split, so a person who does eat fish is not told they cannot.
FISH_SPLIT = ("Fish is the one people mean differently - if you do not eat it either, chickpeas, "
              "lentils or tofu fill the same gap.")

# "What can I eat?" with nothing named is the same question the other way round: the list to
# choose from, not a single food.
# The same question with the "for me" left off: "is pesto ok", "is a beef burger alright", "is the
# pesto safe". On its own that is the food entry's question, and often not about eating at all ("is
# the milk still ok" is the fridge), so it only counts when the store holds something the person
# avoids and the food they name is made of it - then the line can only be about them, and the
# answer is the no. The yes stays with the entries, so a bare ask never claims a food is safe.
EAT_ASK_BARE = re.compile(
    r"\b(?:is|are|was|were)\s+(?P<e>[\w ']+?)\s+(?:ok|okay|fine|alright|safe|allowed)"
    r"\s*[?.!,]*$", re.I)

# "is cheese ok if im lactose intolerant" is the same yes or no as "is cheese ok", said with the
# condition after it rather than before it, and the diet card answered it with a swaps list.
EAT_ASK_IF = re.compile(
    r"\b(?:is|are|was|were)\s+(?P<f>[\w ']+?)\s+(?:ok|okay|fine|alright|safe|allowed)\s+"
    r"(?:if|since|because|as|when|now that)\b", re.I)

EAT_ANY = re.compile(r"\bwhat\s+(?:can|could|should)\s+i\s+(?:eat|have)\b"
                     r"|\bwhat\s+(?:food|foods)\s+can\s+i\s+(?:eat|have)\b", re.I)
# The words a bare "what can I eat" is made of. A line that says more than these is asking for a
# meal rather than for the list ("what can i have for lunch" is the lunch idea's question), so the
# list only answers the line that carries nothing else.
EAT_ANY_WORDS = frozenset("what can could should shall i eat have to now then instead please "
                          "today tonight for a also still tonight really actually at the moment "
                          "me us we just more".split())

# Foods whose bought or restaurant version often has a family in it even though the recipe does
# not need it. This is why allergy advice ends with "read the label": a plain cake needs no nuts
# at all, and plenty of bought ones have them in the icing, the decoration or the same factory.
MAY_HAVE = {}
for _name in ("cake", "cakes", "icing", "biscuits", "biscuit", "cookies", "chocolate", "dessert",
              "desserts", "ice cream", "muesli", "cereal", "granola", "flapjack", "brownie",
              "brownies", "pie", "pastry", "curry", "curries", "salad", "sandwich", "sandwiches",
              "bread", "sauce", "sauces"):
    MAY_HAVE[_name] = NUTS

# What a person's own ban is called when the answer is a yes.
BAN_SAY = ((NUTS, "nuts"), (GLUTEN, "gluten"), (DAIRY, "dairy"), (EGGS, "egg"), (MEAT, "meat"),
           (FISH, "fish"), (SHELLFISH, "shellfish"))
ANY_FAMILY = (NUTS, GLUTEN, DAIRY, EGGS, MEAT, FISH, SHELLFISH)


def _food_named(text):
    """The dish or food a line names that we can answer about, longest phrase first, or None."""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    for size in (2, 1):
        for start in range(len(words) - size + 1):
            phrase = " ".join(words[start:start + size])
            if phrase in MADE_OF:
                return phrase
    return None


def _foods_named(text):
    """Every food the line names that we can answer about, longest phrase first.

    A two-word dish wins over the word inside it ("peanut butter" is not "butter"), so a line
    naming both that dish and another food says so with two entries."""
    words = re.findall(r"[a-z']+", str(text or "").lower())
    found, taken = [], set()
    for size in (2, 1):
        for start in range(len(words) - size + 1):
            if any(at in taken for at in range(start, start + size)):
                continue
            phrase = " ".join(words[start:start + size])
            if phrase in MADE_OF:
                found.append(phrase)
                taken.update(range(start, start + size))
    return found


# A food word ending in "s" that is still one thing: "couscous is made with wheat" is right and
# "couscous are made with wheat" is not. A plural one needs the plural verb, or the answer reads
# like a machine talking: "almonds are made with nuts", "potatoes have no gluten in them".
SINGULAR_IN_S = frozenset("couscous hummus muesli asparagus fish veg molasses".split())


def _is_plural(food):
    word = food.split()[-1]
    if word in SINGULAR_IN_S or word.endswith("ss"):
        return False
    return word.endswith("s")


def _named_as(text, food):
    """The food the way the line named it: "a croissant" keeps its article, "croissant" alone
    stays bare, because the answer is about the thing they pointed at."""
    text = str(text or "").lower()
    for match in re.finditer(r"\b" + r"\s+".join(re.escape(part) for part in food.split()) + r"\b",
                             text):
        # "a peanut butter sandwich": the article belongs to the sandwich, and answering "a
        # peanut butter is made with nuts" talks about a food nobody asked for.
        after = re.match(r"[\s-]+([a-z']+)", text[match.end():])
        if after and after.group(1) in MADE_OF:
            continue
        before = text[:match.start()].rstrip()
        # The words they used to name it belong in the answer: "can i have lactose free milk" is
        # not a question about milk, and "milk has no dairy in it" is a riddle rather than a yes.
        # Whatever they said a food is free of stays in front of it.
        free = re.search(r"([a-z]+)\s+free$", before)
        qualifier = ""
        if free and free.group(1) in FREE_OF:
            qualifier = free.group(1) + " free "
            before = before[:free.start()].rstrip()
        article = re.search(r"([a-z']+)$", before)
        if article and article.group(1) in ("a", "an", "the"):
            return article.group(1) + " " + qualifier + food
        return qualifier + food
    return food


def _bans_for(understood, memory):
    """What this person avoids: the store's own record, plus what the turns said in the first
    person. A guest's allergy is not theirs, so "can i eat satay" after "my son is allergic to
    peanuts" is not a no about the person, and the store keeps the two apart already (the text
    is read here only for what the store has no key for, like "no cheese please")."""
    banned = _bans_from_store(memory) | _excluded(_mine_only(_said_so_far(understood, memory)))
    # Lactose intolerance is not a dairy allergy. The reader that says "no" to a dairy allergy says
    # it here too, so "can i eat cheese if im lactose intolerant" was told that dairy is off the
    # table - and hard cheese is the dairy food most of those people can eat. The word they used is
    # kept next to the family it reaches, so the answer can tell the two apart: the marker means a
    # reply may name dairy, because how much milk sugar is in it is the whole question.
    line = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if any(word in line for word in _NOT_LACTOSE_WORDS):
        # "im lactose intolerant and vegan" is a vegan plate: the line said both, and the stronger
        # of the two is the one that decides
        pass
    elif _a_lactose_intolerance(line) or _their_diet_is_a_lactose_intolerance(memory):
        banned = set(banned) | {"lactose"}
    return banned


# Who a clause is about. A sentence about someone else says nothing about what the person in
# front of us can eat, and their allergy must not come back as the person's own answer.
THIRD_PERSON = re.compile(
    r"^\s*(?:my\s+(?!own\b)[a-z']+|the\s+(?:baby|kid|kids|child|children|little one|dog|cat)|"
    r"he|she|they|his|her|their|hubby|other half|partner's)\b", re.I)


def _mine_only(text):
    """The parts of a line that are about the person themselves, joined back up.

    "im coeliac and my wife is coeliac" is both of them; "my wife is coeliac" is only her, and
    reading her condition as theirs would answer a question about their own dinner with hers.
    """
    parts = [part.strip() for part in re.split(r"(?<=[.!?;])\s+|\s*,\s*|\s+and\s+|\s+but\s+",
                                               str(text or "")) if part.strip()]
    return " ".join(part for part in parts if not THIRD_PERSON.match(part))


def _bans_from_store(memory):
    """What the person themselves avoids, as the store has it, or an empty set.

    The store keeps a person's own allergy, condition and diet apart from a guest's, and a line
    read for food words cannot: "my son is allergic to peanuts" is his allergy, so what he cannot
    eat is not an answer about whether the person can.
    """
    user = memory.get("user") if isinstance(memory, dict) else None
    if not isinstance(user, dict):
        return set()
    return _bans_of(user)


def _bans_of(facts):
    """What one person avoids, from their own record of allergies, condition and diet."""
    banned = set()
    if not isinstance(facts, dict):
        return banned
    for item in facts.get("allergies") or ():
        word = str(item).lower()
        banned.update(FAMILIES.get(word) or {word})
    for item in facts.get("condition") or ():
        said = str(item).lower()
        for condition, foods in CONDITION_BANS.items():
            if condition in said:
                banned.update(foods)
    diet = str(facts.get("diet") or "").lower()
    if diet in ("vegetarian", "veggie", "vego"):
        banned.update(NO_MEAT_DIET)
    elif diet in ("vegan", "plant based", "plantbased"):
        banned.update(NO_MEAT_DIET | DAIRY | EGGS)
    elif diet.startswith("no "):
        word = diet[3:].strip()
        banned.update(FAMILIES.get(word) or {word})
    return banned


def _named_families(banned):
    """The families the person named outright, which is not every family they touch.

    A ban on shellfish reaches the word "prawn", and the word "prawn" is also in the meat family,
    so intersecting the families alone would say a shellfish allergy is a meat one. The name the
    person used is the one that decides."""
    return {family for family, name in BAN_SAY if name in banned}


def _bans_said(banned):
    """The names of what they avoid, in the order the families are listed.

    A ban on meat already covers the shellfish in it, so a person who avoids meat is not also
    told they avoid shellfish: that lists the same food twice and reads like a machine."""
    named = _named_families(banned)
    names = [name for family, name in BAN_SAY if family in named]
    if not names:
        names = [name for family, name in BAN_SAY if family & banned]
    if "meat" in names and "shellfish" in names:
        names.remove("shellfish")
    if "meat" in names and "fish" in names:
        names.remove("fish")  # a vegetarian avoids both, and "meat" already says it once
    return names


# What a "somebody else can't have X" answer calls each family when it names the label to look
# for: "a jar that says nut-free" is the check a person can act on in a shop.
BAN_SAY_NAME = {id(NUTS): "nuts", id(GLUTEN): "gluten", id(DAIRY): "milk",
                id(EGGS): "egg", id(MEAT): "meat", id(FISH): "fish",
                id(SHELLFISH): "shellfish"}

FREE_OF = {id(NUTS): "nut-free", id(GLUTEN): "gluten-free", id(DAIRY): "dairy-free",
           id(EGGS): "egg-free", id(MEAT): "meat-free", id(FISH): "fish-free",
           id(SHELLFISH): "shellfish-free"}


def _the_guest(memory, text):
    """The record of the person the line is about, when the store keeps one, or None.

    A named relation is the guest it names ("can my wife eat pesto" is the wife's record). A line
    that only points with a pronoun means the one guest on record: with two of them there is no
    way to tell which one is meant, and a guess about an allergy is the one guess not worth
    making.
    """
    others = memory.get("others") if isinstance(memory, dict) else None
    if not isinstance(others, list) or not others:
        return None
    low = " ".join(str(text or "").lower().split())
    named = [other for other in others
             if isinstance(other, dict) and other.get("who")
             and re.search(r"\b" + re.escape(str(other["who"]).lower()) + r"\b", low)]
    if len(named) == 1:
        return named[0]
    if named:
        return None
    return others[0] if len(others) == 1 and isinstance(others[0], dict) else None


def _food_may(text):
    """A food we know the bought version of, longest phrase first, or None.

    Chocolate is not something you make at home, so it is not in the recipe table, and "can she
    eat chocolate" is still a label question for a nut allergy.
    """
    words = re.findall(r"[a-z']+", str(text or "").lower())
    for size in (2, 1):
        for start in range(len(words) - size + 1):
            phrase = " ".join(words[start:start + size])
            if phrase in MAY_HAVE:
                return phrase
    return None


def _someones_else_can_eat(match, line, memory):
    """"Can she eat pesto" answered from her record, or None so the entries answer it."""
    guest = _the_guest(memory, line)
    if not guest:
        return None
    if not (guest.get("allergies") or guest.get("condition")):
        return None  # a diet alone is the store's question, and it answers it with a name
    said = " ".join(str(part or "") for part in match.groups() if part)
    food = _food_named(said) or _food_may(said)
    if not food:
        return None
    banned = _bans_of(guest)
    if not banned:
        return None
    if _record_says_lactose(guest) and not any(word in said.lower()
                                               for word in _NOT_LACTOSE_WORDS):
        # her record says a lactose intolerance, so how much milk sugar is in the food is the
        # answer rather than a no: "my wife is lactose intolerant" then "can she have cheese"
        answer = _lactose_answer(food, said)
        if answer:
            return answer
    return _not_for_them(food, banned, guest, said)


def _not_for_them(food, banned, guest, text=""):
    """The answer to "can my wife eat pesto" from her own record.

    Two answers: a plain no when the dish's own recipe has what they avoid, and the label check
    when the bought one often does. A food that is neither keeps the answer the entries give it,
    because "can he eat cake" gets the icing and the decorations from the allergy entry and a
    one-line yes would be the thinner reply.
    """
    named = _named_as(text, food)
    who = str((guest or {}).get("who") or "").strip().lower()
    them = ("your " + who) if who else "them"
    named_here = _named_families(banned)
    hits = [family for family in ANY_FAMILY if family & MADE_OF.get(food, frozenset())
            and family & banned]
    hits.sort(key=lambda family: 0 if family in named_here else 1)
    if hits:
        said = FAMILY_SAY[id(hits[0])][0]
        if _is_plural(food):
            said = re.sub(r"\bis\b", "are", said)
        return ("No: " + named + " " + said + ", so it is off the table for " + them + ". "
                "A pack or a menu that says " + FREE_OF.get(id(hits[0]), "free from it") +
                " is the only check that settles it.")
    may = [family for family in ANY_FAMILY if family & MAY_HAVE.get(food, frozenset())
           and family & banned]
    if not may:
        return None
    family = may[0]
    what = "nuts" if family is NUTS else BAN_SAY_NAME.get(id(family), "it")
    return (named.capitalize() + " can be made without " + what + ", but the bought or "
            "restaurant version often has " + ("them" if what == "nuts" else "it") + " in, so for " +
            them + " the pack or the menu has to say " + FREE_OF.get(id(family), "free from it") +
            ".")


# A follow-up that names a food and nothing else: "what about pesto", "and pesto?", "is bread
# out then", "how about a satay". People do not ask "can my son eat pesto" a second time, they
# point at the dish - and the record of what the guest cannot have is what answers it. The words
# below are the noise around the food (the pointing, the yes-or-no, the little adverbs); a line
# whose words are the food plus only these is a question about that food, and any other word in
# it makes it somebody else's line. Cooking verbs are left out on purpose, so that a statement
# ("i eat pesto") is not read as a question.
_POINTING = frozenset((
    "what", "how", "about", "and", "or", "then", "instead", "also", "so", "but", "just", "please",
    "with", "without", "for", "to", "can", "could", "may", "should", "shall", "would", "will",
    "do", "does", "did", "a", "an", "the", "be", "is", "are", "was", "were", "am", "i", "we",
    "you", "he", "she", "they", "him", "her", "them", "it", "that", "this", "those", "these",
    "ok", "okay", "fine", "alright", "safe", "allowed", "out", "off", "table", "no", "good",
    "wrong", "problem", "any", "some", "still", "too", "as", "well", "me", "my", "our", "us",
    "now", "next", "there", "again", "one", "thing", "things", "either", "neither", "not", "yes",
    "much", "many", "all", "right", "dodgy", "bad", "avoid", "of", "on", "in", "at",
))


_LEAVE_IT_OUT = frozenset((
    "no", "not", "dont", "doesnt", "didnt", "without", "avoid", "skip", "drop", "leave", "hold",
    "minus", "except", "apart",
))


def _foods_a_line_points_at(line):
    """The foods a line is made of, when it is made of nothing else, or none.

    A line of more than seven words is a sentence about something, and a word of its own beyond
    the pointing ("what about **using** pesto") is that sentence, so neither is claimed here."""
    words = re.findall(r"[a-z']+", str(line or "").lower())
    if not words or len(words) > 7:
        return []
    foods = _foods_named(line)
    if not foods:
        may = _food_may(line)
        return [may] if may else []
    spare = set(" ".join(foods).split())
    left = [word for word in words if word not in spare and word not in _POINTING]
    if left:
        return []
    # "and no cheese either" names a food and tells us to leave it out, so the dish on the table
    # without it is the answer and the record has nothing to say: only a line that points at the
    # food asks about it.
    if any(word in _LEAVE_IT_OUT for word in words):
        return []
    return foods


def pointed_at_a_food(understood, memory):
    """A follow-up that names only a food, answered from the condition on file, or None.

    "My son is allergic to nuts" then "what about pesto" is one question, and the answer is the
    no that "can he eat pesto" already gets: the recipe for a pesto is the one thing this line
    must not be answered with. The store keeps the guest and what they cannot have, so the same
    record answers both shapes.

    Only a food whose own recipe is made of what they avoid is claimed here: that is the line
    where the recipe would put the ingredient they cannot have on the plate. A food that is
    merely one a shop often adds it to ("what about cake" for a nut allergy) keeps the entry on
    labels and icing, because a one-line check says less than that does. A line naming two foods
    is a dish ("a peanut butter sandwich") unless exactly one of them is one they cannot have.
    """
    if not isinstance(understood, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "")
    foods = _foods_a_line_points_at(line)
    if not foods:
        return None
    # A guest whose record says what they cannot have is the person the line is about, so their
    # record answers it and the person typing's own allergies are not borrowed for it.
    guest = _the_guest(memory, line)
    guest_bans = _bans_of(guest) if guest else frozenset()
    if guest_bans:
        hits = [food for food in foods if food in MADE_OF and _bans_it(food, guest_bans)]
        return _not_for_them(hits[0], guest_bans, guest, line) if len(hits) == 1 else None
    banned = _bans_for(understood, memory)
    if not _bans_said(banned):
        return None
    hits = [food for food in foods if food in MADE_OF and _bans_it(food, banned)]
    return _one_food_answer(hits[0], banned, line) if len(hits) == 1 else None


def suits_them(understood, memory):
    """A yes or no about one food, from what the person has said they avoid, or None.

    "Can I eat satay?" a turn after a peanut allergy is a question about peanuts, and the store
    holds that, so the reply says no and what to have instead. Only a line that asks in the first
    person, only a food whose recipe is known, and only once they have said what they avoid: an
    ordinary "can i eat raw eggs" is the food entry's question, not this one.
    """
    if not isinstance(understood, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "")
    if EAT_ANY.search(line):
        said_here = [word for word in re.findall(r"[a-z']+", line.lower())
                     if word not in EAT_ANY_WORDS]
        if said_here:
            return None  # "what can i have for lunch" names a meal, and the meal idea answers it
        banned = _bans_for(understood, memory)
        if not _bans_said(banned):
            return None
        return _any_meal(banned)
    about_them = EAT_ASK_THEM.search(line)
    if about_them:
        return _someones_else_can_eat(about_them, line, memory)
    # The same question asked the way people actually ask it a turn later: the food on its own,
    # under the condition that is already on record (see pointed_at_a_food).
    pointed = pointed_at_a_food(understood, memory)
    if pointed:
        return pointed
    banned = _bans_for(understood, memory)
    if not _bans_said(banned):
        return None  # they have said nothing they avoid: no answer of our own to give
    asked = EAT_ASK.search(line) or EAT_ASK_IF.search(line)
    bare = False
    if not asked:
        # "is the milk still ok" asks whether the thing in the fridge has gone off, whatever they
        # avoid, so a line with "still" in it keeps its storage entry.
        if not EAT_ASK_BARE.search(line) or "still" in line.lower():
            return None
        asked = EAT_ASK_BARE.search(line)
        bare = True
    if asked:
        named_foods = _foods_named(asked.group(0))
        if not named_foods:
            return None
        if len(set(named_foods)) > 1:
            # Two foods in one line is usually a dish ("fish and chips"), and the meal entries
            # read it. When one of the two is a food they avoid, though, the answer is still no
            # about that food: "can i eat a peanut butter sandwich" is a question about peanuts.
            named_foods = [food for food in named_foods
                           if _bans_it(food, banned)]
            if not named_foods:
                return None
        return _one_food_answer(named_foods[0], banned, asked.group(0), bare=bare)
    return None


def considered(understood, memory):
    """A dish the person is only thinking of, checked against what they avoid, or None.

    "i was thinking of a satay" is the same question as "can i eat satay" said as a plan, and a
    no is the answer they need. Only a no: a dish they can have is the plan's own answer, and a
    concrete suggestion that respects their ban ("i fancy a chicken curry" -> chickpea curry) is
    a better answer than a check, so this is asked only where no entry answered the line."""
    if not isinstance(understood, dict):
        return None
    line = str(understood.get("clean") or understood.get("text") or "")
    considering = FANCY_ASK.search(line)
    if not considering:
        return None
    banned = _bans_for(understood, memory)
    if not _bans_said(banned):
        return None
    food = _food_they_avoid(_foods_named(line[considering.end():]), banned)
    if food is None:
        return None
    return _one_food_answer(food, banned, line)


# What a line can say a food is free of, and the family each word stands for. A food's own
# recipe is not the whole answer when the line in front of it says what is not in it.
FREE_OF = {"meat": MEAT, "fish": FISH, "dairy": DAIRY, "milk": DAIRY, "lactose": DAIRY,
           "cheese": DAIRY, "gluten": GLUTEN, "wheat": GLUTEN, "nut": NUTS, "nuts": NUTS,
           "peanut": NUTS, "peanuts": NUTS, "egg": EGGS, "eggs": EGGS, "shellfish": SHELLFISH,
           "sugar": frozenset(), "soya": frozenset(), "soy": frozenset()}


def _free_of(text, food):
    """The families the line itself says this food is free of, or nothing.

    "is lactose free milk ok" was a no about dairy for somebody who is lactose intolerant, and
    "is gluten free bread ok" is the same shape: the words in front of the food say what is not in
    it, and an answer that reads only the food's own recipe takes away the one thing they can
    have. Only the word in front counts, because "milk from a lactose free farm" says nothing.
    """
    text = str(text or "").lower().replace("\u2019", "'").replace("-", " ")
    phrase = r"\s+".join(re.escape(part) for part in food.split())
    for match in re.finditer(r"\b([a-z]+)\s+free\s+" + phrase + r"\b", text):
        if match.group(1) in FREE_OF:
            return FREE_OF[match.group(1)]
    for match in re.finditer(phrase + r"\s+(?:is\s+|are\s+)?([a-z]+)\s+free\b", text):
        if match.group(1) in FREE_OF:
            return FREE_OF[match.group(1)]
    return frozenset()


# A yes about a plain food is a claim about the food's own recipe, and a few foods are not
# settled by their recipe: an oat has no gluten in it, but oats are grown and milled next to
# wheat, so ordinary porridge oats are not safe for a coeliac. This file's own gluten-free card
# already says "porridge made with gluten free oats", so "im gluten free / can i have porridge"
# answering "porridge has no gluten in it, so it is fine for you" contradicted it in the next
# turn. The packet is what settles these, and the answer says so.
NOT_SETTLED_BY_THE_RECIPE = {
    "oats": ("With the right packet: an oat has no gluten in it, but oats are grown and milled "
             "next to wheat, so ordinary porridge oats are not safe for a coeliac. The ones "
             "marked gluten free are, and they cost about the same."),
    "porridge": ("With the right packet: an oat has no gluten in it, but oats are grown and "
                 "milled next to wheat, so ordinary porridge oats are not safe for a coeliac. "
                 "The ones marked gluten free are, and they cost about the same."),
    "oatmeal": ("With the right packet: an oat has no gluten in it, but oats are grown and "
                "milled next to wheat, so ordinary porridge oats are not safe for a coeliac. "
                "The ones marked gluten free are, and they cost about the same."),
}


def _bans_it(food, banned):
    """True when a food's usual recipe is made of something the person avoids."""
    return any(family & MADE_OF[food] and family & banned for family in ANY_FAMILY)


def _food_they_avoid(named_foods, banned):
    """The food in the line the ban actually reaches, or None.

    A line can name a safe food beside the one that is not ("a salad with cheese"), and the
    answer is about the food they cannot have."""
    for food in named_foods:
        if _bans_it(food, banned):
            return food
    return None

# How much milk sugar is in the everyday dairy foods. A dairy-free swap is the wrong answer for a
# lactose intolerance: the sugar is what is missing from aged cheese and butter, and it is the
# whole of a glass of milk, so the answer names the level rather than saying no.
LACTOSE_LOW = ("cheese", "butter", "cream")
LACTOSE_HIGH = ("milk", "yoghurt", "yogurt", "ice cream")
_LACTOSE_SAYS = {
    "cheese": ("Yes, usually: ageing eats almost all of the lactose, so a hard cheese such as "
               "cheddar or parmesan is the dairy food most people with a lactose intolerance can "
               "eat without trouble. Soft cheese - brie, cottage cheese, ricotta, mozzarella - "
               "has more of it left, so try a small amount with a meal first."),
    "butter": ("Yes: butter is mostly fat with only a trace of milk sugar left in it, so a normal "
               "spread is fine for most people with a lactose intolerance. Cream and ghee are the "
               "same idea; milk, yoghurt and ice cream are the ones with real lactose in them."),
    "cream": ("Yes, in a small amount: cream has far less lactose than milk, so a spoonful in a "
              "sauce is usually fine. Milk, soft cheese, yoghurt and ice cream are where most of "
              "the lactose is."),
    "milk": ("Not much of it, and not on its own: milk is where most of the lactose is, so a "
             "small glass with a meal is the test, and lactose-free milk is ordinary milk with the "
             "sugar already split - it does the same job in tea, on cereal and in cooking."),
    "yoghurt": ("Often yes: live yoghurt is easier than milk because the cultures do part of the "
                "digesting, so a small pot with a meal is usually fine. A big tub on its own, or "
                "ice cream, is where people notice it."),
    "yogurt": ("Often yes: live yogurt is easier than milk because the cultures do part of the "
               "digesting, so a small pot with a meal is usually fine. A big tub on its own, or "
               "ice cream, is where people notice it."),
    "ice cream": ("Not much of it: ice cream is milk and cream with sugar on top, so it is one of "
                  "the higher ones. A couple of spoons after a meal is a different thing from a "
                  "whole tub, and lactase tablets taken with the first mouthful cover it."),
}


_LACTOSE_FREE_ASK = re.compile(r"lactose[\s-]*free", re.I)


def _lactose_answer(food, text):
    """What a lactose intolerance can have of this food, or None for a food with no milk in it."""
    if _LACTOSE_FREE_ASK.search(str(text or "")):
        # the product itself is the question, and the answer to it is yes
        return ("Yes: lactose-free milk is ordinary milk with the milk sugar already split, so it "
                "does the same job in tea, on cereal and in cooking. There are lactose-free "
                "yoghurts and soft cheeses too, though a hard cheese or butter has almost none "
                "left in it anyway.")
    if food in _LACTOSE_SAYS:
        return _LACTOSE_SAYS[food]
    if DAIRY & MADE_OF.get(food, frozenset()):
        return ("It depends how much milk is in it: milk, soft cheese, yoghurt and ice cream hold "
                "most of the lactose, while a hard cheese or butter has almost none left. Try a "
                "small portion with a meal, and lactose-free milk and lactase tablets are there "
                "for the ones that catch you out.")
    return None


def _one_food_answer(food, banned, text, bare=False):
    """The yes or no about one food, from the families its usual recipe is made of."""
    avoid = _bans_said(banned)
    if "lactose" in banned:
        # "im lactose intolerant" reaches the dairy family, the same as "im allergic to dairy", so
        # this reader was saying "no" to a lactose intolerance too. How much milk sugar is in the
        # food is the question, so that is the answer.
        answer = _lactose_answer(food, text)
        if answer:
            return answer
    made_of = MADE_OF[food] - _free_of(text, food)
    hits = [family for family in ANY_FAMILY if family & made_of and family & banned]
    # The family they named comes before one they only reached through a word inside it.
    named_here = _named_families(banned)
    hits.sort(key=lambda family: 0 if family in named_here else 1)
    if bare and not hits:
        # A bare "is X ok" with nothing of theirs in it is not this reader's line: it belongs to
        # the food entry, which says what the food is for without claiming it is safe for them.
        return None
    if not hits:
        if food in FISH and MEAT in named_here and FISH not in named_here:
            # A bare "i don't eat meat" does not settle fish: plenty of people who say it eat
            # fish, so neither a no nor a yes is honest, and the answer names the split.
            return FISH_SPLIT
        if len(avoid) == 1:
            what = avoid[0]
        else:
            what = ", ".join(avoid[:-1]) + " or " + avoid[-1]
        named = _named_as(text, food)
        if food == "honey" and {"meat", "dairy", "egg"} <= banned:
            # Honey is the plain food a vegan can refuse and a table of families cannot see: no
            # meat, dairy or egg in it, so a confident yes is a claim about somebody's principles
            # rather than about the food. A no would be just as wrong about a vegan who counts it.
            return ("Some vegans avoid honey, so it depends how strict you are - sugar or golden "
                    "syrup does the same job in a recipe.")
        if made_of:
            # A dish is made of more than the families this table lists, and a bought one can
            # hold what the recipe does not: a quiche is pastry, cream and egg, and the shop's
            # can carry nuts. "A quiche has no nuts in it" is a confident claim the table cannot
            # back, and a wrong yes about an allergy is the one thing this answer must not do,
            # so the yes is about the plain dish and the label is named.
            them = "them" if what in ("nuts",) else "it"
            return ("Nothing in " + named + " needs " + what + ", but a bought one can have " +
                    them + " in - check the label.")
        # A food we know the recipe of, made of none of it: the honest answer to "can I eat this"
        # is a yes, and "I'd rather not guess" about plain rice is a worse one.
        if "gluten" in avoid and food in NOT_SETTLED_BY_THE_RECIPE:
            return NOT_SETTLED_BY_THE_RECIPE[food]
        if _is_plural(food):
            return ("Yes: " + named + " have no " + what + " in them, so they are fine for you.")
        return "Yes: " + named + " has no " + what + " in it, so it is fine for you."
    said, swap = FAMILY_SAY[id(hits[0])]
    named = _named_as(text, food)
    if food in hits[0] and id(hits[0]) in SELF_SAY:
        # The food is the family itself ("can i eat eggs" for a vegan, "can i eat peanuts" for a
        # nut allergy), and "eggs are made with egg" is a riddle rather than an answer.
        return ("No: " + SELF_SAY[id(hits[0])] + ", and it is off the table for you. " +
                swap[0].upper() + swap[1:] + ".")
    if _is_plural(food):
        said = re.sub(r"\bis\b", "are", said)
    return ("No: " + named + " " + said + ", and that is off the table for you. " +
            swap[0].upper() + swap[1:] + ".")


def _no_meat_also_means_fish(banned):
    """What a meal idea leaves out when a bare "no meat" is all the person has said.

    The split in suits_them is for a yes/no question about fish. A suggestion is not that: an
    idea that offers tuna to someone who has just said they do not eat meat is worse than the
    idea the split protects, so a meal leaves both families out."""
    return banned | FISH if MEAT & banned else banned


def _bans(names, idea, banned):
    """True when an idea needs, or tells them to add, a food the eater avoids."""
    for name in names:
        if name in banned:
            return True
        if any(part in banned for part in name.split()):
            return True
    text = idea.lower()
    return any(re.search(r"\b" + re.escape(word) + r"\b", text) for word in banned)


# --- a reply that names a food the person does not eat ---------------------------------------
# The bans above are used to choose between things to cook, and the words they cover are the
# short ones a line says out loud ("bacon", "butter"). A reply says them in full ("chopped
# bacon", "a knob of butter", "flaked salmon", "feta"), so the check on a finished reply needs
# the wider list: what a recipe calls a meat, a fish or a dairy.
MEAT_SAYS = MEAT | frozenset(
    "chorizo salami pancetta prosciutto pepperoni steak brisket liver kidney venison duck "
    "goose rabbit pheasant partridge anchovies anchovy sardines mackerel haddock kippers".split())
FISH_SAYS = FISH | frozenset(
    "anchovies anchovy sardines mackerel haddock kipper kippers shellfish prawns crab lobster "
    "mussels oysters squid clams scallops".split())
DAIRY_SAYS = DAIRY | CHEESES | frozenset("mozzarella creme buttermilk ghee".split())
EGG_SAYS = EGGS | frozenset("mayonnaise mayo omelette quiche custard meringue".split())
NUT_SAYS = NUTS | frozenset("almonds almond cashews cashew walnuts walnut pistachios pistachio "
                           "hazelnuts hazelnut pecans pecan brazil marzipan praline satay "
                           "nutella pesto".split())
SHELLFISH_SAYS = SHELLFISH | frozenset("prawn crab lobster mussel oyster squid clam scallop "
                                       "prawns crabs lobsters mussels oysters clams scallops".split())
# The dairy words that can be swapped for something everyone has, so the answer stays an answer
# instead of being thrown away. "peanut butter" and "butter beans" are not dairy, and a butter
# bean is not a butter, so both keep their word.
DAIRY_SWAPS = (
    (re.compile(r"\ba knob of butter\b", re.I), "a little oil"),
    (re.compile(r"\b(?:a|one) spoon of cream\b", re.I), "a spoon of oat cream"),
    (re.compile(r"\bdouble cream\b", re.I), "oat cream"),
    (re.compile(r"\bmashed with butter\b", re.I), "mashed with olive oil"),
    (re.compile(r"\b(?<!peanut )(?<!cocoa )(?<!shea )(?<!apple )(?<!nut )(?<!butter )butter\b"
                r"(?!\s*beans?\b)", re.I), "oil"),
    (re.compile(r"\b(?<!coconut )(?<!oat )(?<!soy )(?<!almond )(?<!plant )(?<!rice )(?<!hemp )"
                r"(?<!butter )(?<!goat )(?<!sheep )milk\b", re.I), "plant milk"),
    # The dairy that a dairy-free cook is told to use as a substitute is the same problem one
    # step along: "in marinades and dressings: sour cream, creme fraiche or buttermilk" answers
    # "what can i use instead of yoghurt" with three things they cannot have.
    (re.compile(r"\bsour cream\b", re.I), "soya yogurt"),
    (re.compile(r"\bcr[eè]me fra[iî]che\b", re.I), "soya cream"),
    # "or buttermilk" in a list, but not the heading "For 250ml of buttermilk:", which is the
    # thing the person is asking to replace.
    (re.compile(r"\bor buttermilk\b", re.I), "or plant milk with a squeeze of lemon"),
    # "one egg becomes 60g of yoghurt" is the vegan substitute card telling a vegan what to buy,
    # so the yoghurt in it is the one swap the card cannot do without.
    (re.compile(r"\b(?<!soya )(?<!soy )(?<!coconut )(?<!plant )(?<!oat )(?<!almond )"
                r"(?<!greek )(?:yoghurt|yogurt)\b", re.I), "soya yoghurt"),
)


# A nut in a reply is usually a substitution, not the dish: the dairy-free card says "oat, soya or
# almond milk", and handing that to a household with a nut allergy is one word away from useful.
# Swapping keeps the card instead of throwing it away.
NUT_SWAPS = (
    (re.compile(r"\balmond milk\b", re.I), "oat milk"),
    (re.compile(r"\balmond flour\b", re.I), "plain flour"),
    (re.compile(r"\bground almonds\b", re.I), "ground seeds"),
    (re.compile(r"\bflaked almonds\b", re.I), "seeds"),
    (re.compile(r"\b(?<!sunflower )(?<!seed )(?<!soya )(?<!olive )peanut butter\b", re.I),
     "sunflower seed butter"),
    (re.compile(r"\bnut butter\b", re.I), "seed butter"),
)


# A dairy word after one of these is not dairy: "coconut milk", "peanut butter" and "butter
# beans" are foods a person avoiding milk can eat, and reading them as the dairy would take a
# good answer away from them.
# Gluten is not checked after the swap, only swapped: "stirred through pasta" and "mashed onto
# toast" are a job a coeliac can still do - with the gluten-free version - where declining the
# card would have left them with a shrug. The word is only swapped when the line itself did not
# name it: someone asking about leftover pasta is asking about pasta.
GLUTEN_WORDS = ("pasta", "toast")
GLUTEN_SWAPS = (
    ("pasta", re.compile(r"\b(?<!free )(?<!free- )pasta\b", re.I), "gluten-free pasta"),
    ("toast", re.compile(r"\b(?<!free )(?<!free- )toast\b", re.I), "gluten-free toast"),
)


# A dairy word after one of these is not dairy: "coconut milk", "peanut butter" and "butter
# beans" are foods a person avoiding milk can eat, and reading them as the dairy would take a
# good answer away from them.
NOT_THE_DAIRY = re.compile(r"\b(?:oat|soy|soya|coconut|almond|plant|rice|hemp|cashew|peanut|"
                           r"shea|cocoa|apple|nut)\s+$", re.I)


# A reply that names the food and tells the person how to be safe with it is doing its job:
# "a bought one can have it in - check the label" is the careful answer about an allergen, and
# reading the word itself as the food served threw it away.
CAUTION_SAID = re.compile(
    r"\b(?:check|read|look at|watch)\s+(?:the\s+)?(?:label|labels|packet|packets|ingredients|"
    r"ingredient list|back of the (?:pack|packet|tin|box|jar)|pesto|chocolate|jar)"
    r"|\bmay contain\b|\ballergen|\bcross[- ]contamination"
    r"|\bask (?:the staff|them|whoever|at the counter|before)" 
    r"|\bcan have (?:it|them) in\b|\bcan (?:sometimes )?carry\b|\bmay have\b"
    r"|\boff the table for\b|\bnot for you\b|\brather not risk\b|\bstay (?:well )?clear\b"
    r"|\b(?:avoid|avoiding|watch out for)\b|\bfree from\b|\b(?:nut|dairy|gluten)[- ]free\b", re.I)

# The plant versions said out loud: a reply that carries these is a reply written for someone who
# does not eat the dairy or the egg, and the dairy words in it are the things being replaced.
PLANT_SAID = re.compile(r"\b(?:vegan|vegetarian|plant based|plant-based|dairy free|dairy-free|"
                        r"egg free|"
                        r"margarine|flax egg|flaxseed|oat milk|soya milk|soy milk|almond milk|"
                        r"oat cream|soya cream|nutritional yeast|aquafaba)\b", re.I)


# A food named to say what replaces it is the answer for someone who does not eat it: a vegan
# cake is "a flax egg for each egg ... margarine for every 100g of butter", and reading those
# words as the dish took the one entry that knows the bake away from the person. The marker has
# to sit against the word, not somewhere in the sentence: "crumble into a sprout and bacon dish
# ... sweet enough without cream" is a bacon dish with a note about the cream.
SWAP_BEFORE = re.compile(r"(?:instead of|in place of|rather than|swap for|substitute for|"
                         r"no need for|without|free of|for (?:each|every|the)|per|"
                         r"flax|chia|linseed|vegan|plant|soya|soy|oat|coconut|almond|nut)\s+"
                         r"(?:\d+\s*(?:g|ml)\s+(?:of\s+)?)?$", re.I)
SWAP_AFTER = re.compile(r"\s*-?\s*(?:free|replacer|substitute|swap)\b", re.I)
SWAP_WINDOW = 34


def _a_swap_not_a_dish(text, at, word):
    """Whether the food at a position in `text` is named to say what replaces it."""
    before = text[max(0, at - SWAP_WINDOW):at]
    after = text[at + len(word):at + len(word) + SWAP_WINDOW]
    return bool(SWAP_BEFORE.search(before) or SWAP_AFTER.match(after))


def _says_a_food(text, words):
    """The foods from `words` a piece of text names, as the words it used.

    A dairy word counts only when it is the dairy: `NOT_THE_DAIRY` steps over "oat milk" and
    "peanut butter", and "butter beans" is a bean.
    """
    found = []
    for word in words:
        for match in re.finditer(r"\b" + re.escape(word) + r"(?:s|es)?\b", text, re.I):
            if word in DAIRY_SAYS and NOT_THE_DAIRY.search(text[:match.start()]):
                continue
            if word == "butter" and re.match(r"\s+beans?\b", text[match.end():], re.I):
                continue  # a butter bean is a bean
            if _a_swap_not_a_dish(text, match.start(), match.group(0)):
                continue  # "a flax egg", "margarine for every 100g of butter": a swap, not a dish
            found.append(word)
            break
    return found


def avoids(memory, understood=None):
    """What the person themselves does not eat, from the store and from the turns.

    A module outside this one answers with a row written for everyone, so it needs the same
    reading of a diet that the meal tables use. Everything here is optional: a memory with no
    store and no line is a person with no bans, which is the answer for every line that is not
    about food.
    """
    if not isinstance(memory, dict):
        return frozenset()
    read = understood if isinstance(understood, dict) else memory.get("understood")
    if not isinstance(read, dict):
        read = {}
    try:
        return frozenset(_bans_for(read, memory))
    except Exception:
        return frozenset()


def _family_of(word):
    """The family a word names, singular or plural: "nuts" is NUTS, "peanuts" is NUTS."""
    word = str(word or "").strip().lower()
    if not word:
        return set()
    for key in (word, word[:-1] if word.endswith("s") else word):
        if key in FAMILIES:
            return set(FAMILIES[key])
    return {word}


def avoids_for_the_one_talked_about(memory):
    """What the person the chat is *about* cannot eat, when that is somebody else.

    avoids() is the person in front of us on purpose: "can i eat satay" after "my son is allergic
    to peanuts" is not a no about them. But a long chat about packing a daughter's lunch is about
    her, and the store keeps her allergies apart (memory["others"]) with the person the chat is
    about already named (memory["person"]). Without this the card for her lunch was checked
    against nobody, and a snack list headed "nuts, fruit, yoghurt" came back to a family who had
    just said nuts are off the table.

    Only allergies: a diet or a condition said about somebody else is theirs to be asked about,
    and a card rewritten free of meat because a guest is vegetarian is answering about the guest.
    """
    if not isinstance(memory, dict):
        return frozenset()
    person = memory.get("person")
    if not isinstance(person, dict):
        return frozenset()
    who = str(person.get("who") or "").strip().lower()
    if not who:
        return frozenset()
    banned = set()
    for record in memory.get("others") or ():
        if not isinstance(record, dict):
            continue
        if str(record.get("who") or "").strip().lower() != who:
            continue
        for item in record.get("allergies") or ():
            banned |= _family_of(item)
        break
    return frozenset(banned)


def _the_banned_words(banned):
    """The recipe words to check a reply against, for what this person avoids."""
    words = set()
    if MEAT & banned or FISH & banned:
        words |= MEAT_SAYS
    if FISH & banned:
        words |= FISH_SAYS
    if DAIRY & banned and "lactose" not in banned:
        # A lactose intolerance is not a dairy allergy: a reply naming cheese is the answer to
        # "can i eat cheese", not a food they said no to.
        words |= DAIRY_SAYS
    if EGGS & banned:
        words |= EGG_SAYS
    # A nut is not a meat and not a dairy, and this is the family with an epipen behind it: a
    # store that says "my daughter is allergic to nuts" must not leave the reply free to name
    # them. Pesto, satay and marzipan are here because that is how a nut arrives unannounced.
    if NUTS & banned:
        words |= NUT_SAYS
    if SHELLFISH & banned:
        words |= SHELLFISH_SAYS
    # Gluten is left out on purpose: the words that carry it are the names of the food itself
    # ("bread", "pasta", "flour"), so a coeliac asking "can i make bread without gluten" says
    # them in the line and the answer has to say them back. That family is answered by the
    # gluten-free readers that already choose between the blends and the bought loaf.
    return frozenset(words)


# The rows whose words name a food somebody does not eat, said again without it. A key is the
# row's own text as it stands, so a row that is reworded stops matching here and the reply is
# handed back unusable rather than served with the food in it, which is the safe way to be wrong.


# A clause that is itself saying the swap is the answer, not a food to fix. The dairy-free card
# opens "Dairy free is easy to cook around: oat, soya or almond milk in place of milk, olive oil
# instead of butter" - a card written for the person - and the dairy swap rewrote it into "in
# place of plant milk, olive oil instead of oil", which is the one reply that needed nothing.
SWAP_CLAUSE = re.compile(r"\b(?:in place of|instead of|rather than|or use|substitute for|"
                         r"swap for|no need for|works too)\b", re.I)


# A reply whose sense is that the food is out is a reply *about* the avoided food, and it is the
# one a vegan most needs: "can i eat eggs" answered "No: that is egg, and it is off the table for
# you. A spoon of yoghurt where a recipe asks for one does the same." Reading the egg in that as a
# fault handed the person a shrug instead. "Since you are not eating meat, I'd leave that out and
# do dhal" is the same shape.
SAYS_THE_FOOD_IS_OUT = re.compile(
    r"off the table|not for you|you (?:cannot|can't|can not|shouldn't|should not) have|"
    r"leave (?:that|it|them|those) out|leave out the|you (?:do not|don't|dont) eat|"
    r"since you (?:are |'re )?(?:not eating|vegan|vegetarian|dairy|gluten)|"
    r"not eating (?:meat|dairy|gluten|eggs)|you avoid|you're avoiding|you are avoiding|"
    r"no meat|without the meat|swap (?:it|that)|there is no egg|that is egg|that's egg|"
    r"that is meat|those are meat|no dairy", re.I)


# A food that is already the gluten-free one: "rice, potatoes or a corn pasta do the same job"
# was rewritten into "a corn gluten-free pasta", which says the same thing twice.
GLUTEN_FREE_ALREADY = re.compile(
    r"\b(?:gluten[- ]free|corn pasta|rice pasta|rice noodles|corn noodles|buckwheat|polenta|"
    r"cornmeal|chickpea pasta|lentil pasta|gram flour|rice flour)\b", re.I)


# A line asking for a replacement names the food it wants to replace, so the food is the card's
# subject and not a fault in it: a vegan asking "what can i use instead of eggs" wants the list of
# substitutes, and the list says eggs.
SUBSTITUTE_ASK = re.compile(
    r"\b(?:instead of|in place of|rather than|substitute|alternative to|replacement for|"
    r"replace|what can i use (?:for|in)|swap (?:it |that )?for|do without|without)\b", re.I)


def _rewritten_outside_swaps(text, pattern, swap, leave=None):
    """`pattern.sub`, on the clauses of `text` that are not already saying the swap."""
    parts = re.split(r"([.!?:]\s+|,\s+)", text)
    for i in range(0, len(parts), 2):
        if not SWAP_CLAUSE.search(parts[i]) and not (leave and leave.search(parts[i])):
            parts[i] = pattern.sub(swap, parts[i])
    return "".join(parts)


def _uncautioned(text, words):
    """The banned words a reply offers, not the ones it warns about.

    An answer about an allergen has to name it: "nothing in the satay needs shellfish, but a
    bought one can have it in - check the label" is the most careful thing the bot says, and
    reading the word "shellfish" as the food served threw it away. A sentence that names the food
    and also tells the person to look at the label, ask, or avoid it is doing the job; a sentence
    that just lists it is not.
    """
    if not CAUTION_SAID.search(text):
        return set(_says_a_food(text, words))
    fresh = set()
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if CAUTION_SAID.search(sentence):
            continue
        fresh |= set(_says_a_food(sentence, words))
    return fresh


def _nut_swapped(text, banned, line):
    """The reply with a nut substitution swapped out, when that settles the whole reply.

    A card that explains what to use instead ("oat, soya or almond milk") is one word away from
    being usable. A card that is *about* the nut ("peanut butter is a decent everyday food ... buy
    one whose only ingredients are peanuts") is not: swapping its first words gave a reply that
    recommended sunflower seed butter and told a peanut-allergic person to buy a jar of peanuts.
    So a swap is kept only when nothing nutty is left afterwards.
    """
    if not (NUTS & banned) or not _a_nut_swap_is_safe(text, line):
        return text
    swapped = text
    for pattern, swap in NUT_SWAPS:
        swapped = _rewritten_outside_swaps(swapped, pattern, swap)
    if swapped == text or names_a_banned_food(swapped, banned, line):
        return text
    return swapped


def _a_nut_swap_is_safe(text, line):
    """A nut named to rule it out, or asked about by name, is not a substitution to rewrite.

    "No: peanut butter is made with nuts, so it is off the table for your son" is the answer, and
    swapping the words inside it gave "sunflower seed butter is made with nuts". A card that
    explains what to use instead ("oat, soya or almond milk") is the one place the word is a
    substitution rather than the subject.
    """
    if SAYS_THE_FOOD_IS_OUT.search(text):
        return False
    return not _says_a_food(str(line or ""), NUT_SAYS)


def fitted_for_the_one_talked_about(reply, banned, line=""):
    """The reply with somebody else's allergen taken out, or None when that cannot be done.

    The bans of a person who is not the one talking only ever *rule a reply out*: nobody asked for
    a card rewritten around a guest's diet, and rewriting one around a guest's allergy turned "ice
    cream is made with milk, so it is off the table for your daughter" into "made with plant
    milk". The one swap that is safe is the nut that sits in a substitution ("oat, soya or almond
    milk"), which is the word the card would have said differently anyway.
    """
    if not isinstance(reply, str) or not reply.strip() or not banned:
        return reply
    text = reply
    # A row with a version of itself written without the food is that version (the office snack
    # list without the nuts), so the veto only fires on what is left after that.
    text = _nut_swapped(DIET_VARIANTS.get(text.strip(), text), banned, line)
    if names_a_banned_food(text, banned, line):
        return None
    return text


def names_a_banned_food(reply, banned, line=""):
    """Whether the reply serves a food somebody in this chat cannot eat."""
    if not isinstance(reply, str) or not reply.strip() or not banned:
        return False
    words = _the_banned_words(banned)
    if not words:
        return False
    said_already = set(_says_a_food(str(line or ""), words))
    said_already |= {word[:-1] for word in said_already if word.endswith("s")}
    left = [word for word in _uncautioned(reply, words)
            if word not in said_already and word[:-1] not in said_already]
    return bool(left)


def fits_the_diet(reply, banned, line=""):
    """The reply, fitted to what this person eats, or None when it cannot be fitted.

    A reply that names a food the person avoids is not an answer to them however good the rest
    of it is: "im vegan" then "what can i do with a cabbage" was answered "fry it in butter", and
    a vegetarian's cabbage was "fried with chopped bacon or smoked sausage". The choosing above
    only reads the rows it picks from, and the rows are written for everyone.

    Three things, in order. A dairy word that has an everyday swap is swapped, because "softened
    in butter" and "softened in oil" are the same instruction - except where the word is not the
    dairy at all ("peanut butter", "butter beans", "coconut milk"). What is left that the person
    cannot eat is then looked for again, and the reply is handed back as unusable - the caller
    tries the row below it rather than serving a food they said no to.

    A food the line itself named is not a fault: a vegetarian asking how to cook bacon for other
    people is asking about bacon, and the answer has to say it. Gluten is not checked here at
    all: its words are the names of the food ("bread", "flour"), so the line and the answer share
    them, and the gluten-free readers already answer that family.
    """
    if not isinstance(reply, str) or not reply.strip() or not banned:
        return reply
    text = reply
    line_words = set(_says_a_food(str(line or ""),
                                 set(_the_banned_words(banned)) | set(GLUTEN_WORDS)))
    if GLUTEN & banned:
        for word, pattern, swap in GLUTEN_SWAPS:
            if word not in line_words:
                text = _rewritten_outside_swaps(text, pattern, swap,
                                                leave=GLUTEN_FREE_ALREADY)
    words = _the_banned_words(banned)
    if not words:
        return text
    if _ask_about_the_food(str(line or "").lower(), len(str(line or ""))):
        # The line asks whether a named food is vegetarian or vegan, and the answer to that is
        # what might be in it: "are chips vegetarian" is answered about beef dripping and "is
        # wine vegetarian" about isinglass, and the filter that keeps a refused food out of an
        # answer must not throw those away. The words are the whole point of the verdict.
        return text
    said_already = set(_says_a_food(str(line or ""), words))
    # "egg" in the line and "eggs" in the answer are the same food: "how long do i boil an egg"
    # names the egg itself, and a reply that says "lower eggs into boiling water" is answering the
    # question rather than naming a food the person avoided. Without this the plural was read as a
    # different food and a vegan asking about boiling an egg got a shrug.
    said_already |= {word[:-1] for word in said_already if word.endswith("s")}
    left = [word for word in _uncautioned(text, words)
            if word not in said_already and word[:-1] not in said_already]
    if not left:
        return text
    # A variant is written to answer everything the person said, so it is only used when the ban
    # it covers is the whole of the ban: the nut-free snack list is not an answer to somebody who
    # is allergic to nuts *and* shellfish, and a card that says "nut-free" there answers half of
    # what they told us. The acknowledgement that names both is the better reply.
    nuts_only = NUTS & banned and not (banned - NUTS)
    if MEAT & banned or FISH & banned or nuts_only:
        # A row can have a version of itself written for the people the row's own words leave
        # out: the cabbage recipe is bacon, the swede is "alongside sausages", the courgette is a
        # pasta dish and the office snack list is nuts. Those are the same job said without the
        # food, and a shrug is a worse answer than the job. The key is the row's exact text, so a
        # family with no variant written for it simply finds nothing here and is handled below.
        text = DIET_VARIANTS.get(text.strip(), text)
    if DAIRY & banned and "lactose" not in banned and not PLANT_SAID.search(text):
        # A reply that already says it is the plant version is written for this person, and the
        # swap rewrites it into nonsense: the dairy-free card says "watch the labels for whey,
        # casein, milk powder and lactose", and swapping there gave "plant milk powder".
        for pattern, swap in DAIRY_SWAPS:
            text = _rewritten_outside_swaps(text, pattern, swap)
    text = _nut_swapped(text, banned, line)
    said = _says_a_food(text, words)
    if PLANT_SAID.search(text):
        # A reply that says it is the vegan or the vegetarian version is written for the person
        # who cannot have the thing: the vegan bake says "60g of yoghurt or half a mashed banana"
        # and "a flax egg ... for each egg", and the dinner-party plan says "beats a meat main".
        # Reading those words as the dish took the entries that know the job away from the person
        # who needs them.
        said = [word for word in said
                if word not in DAIRY_SAYS and word not in EGG_SAYS
                and word not in MEAT_SAYS and word not in FISH_SAYS]
    left = [word for word in said if word not in said_already]
    if not left:
        return text
    if SUBSTITUTE_ASK.search(str(line or "").lower()):
        # The line asks what to use *instead of* the food, so the food is the question rather than
        # a fault in the reply: "im vegan" then "what can i use instead of eggs" is the bananas and
        # the flax, and the dairy in the same card is already swapped by now.
        return text
    if SAYS_THE_FOOD_IS_OUT.search(text):
        # the reply names the food to rule it out, which is the answer to "can i eat eggs"
        return text
    without = _the_card_without_that_sentence(text, left, words)
    if without:
        # The food is one sentence of a card that is otherwise the right answer: fried rice is
        # rice, garlic, ginger and soy with an egg scrambled in at the end, and a vegan gets the
        # card without the egg rather than "that's beyond what I know well".
        return without
    first = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    if not [word for word in _says_a_food(first, words) if word in left or word[:-1] in left]:
        # The food is a mention further down a card about something else: the roast-sides card is
        # the vegetables and the joint is context, and the protein card names meat in its list of
        # sources. Blanking those two turned "what can i have with a roast" and "what can i eat for
        # protein" into a hedge, which is a worse answer than a card whose subject is not the food
        # they refused. A card that is *about* the food says so in its first sentence.
        return text
    return None


def _the_card_without_that_sentence(text, left, words):
    """`text` with the parts that name a food they cannot eat taken out, or None.

    A recipe is one long sentence, so the unit is the clause rather than the sentence: fried rice
    is "heat a little oil, add the cold rice and fry it hard, **then** push it aside and scramble
    an egg in the gap". Taking the egg's clause out leaves the dish, and the person who said they
    are vegan gets the rice instead of "that's beyond what I know well".

    Only when there is a card left: something has to have been dropped, and what stays has to be
    most of the text, or the answer is a fragment rather than a dish.
    """
    bits = re.split(r"([.!?]+\s+|;\s+|,\s+(?:then|and)\s+)", str(text).strip())
    keep = []
    dropped = 0
    for index in range(0, len(bits), 2):
        part = bits[index]
        names = _says_a_food(part, words)
        if [word for word in names if word in left or word[:-1] in left]:
            dropped += 1
            continue
        keep.append(part)
    if not dropped or not keep:
        return None
    if not keep[0].strip(" ,.;:") or keep[0] is not bits[0]:
        # The first clause carries the instruction ("whisk the flour into the meat juices..."),
        # and a card that starts at its second clause starts at "simmer it", with nothing for the
        # "it" to be. A dish that opens with the food they cannot eat has no version here.
        return None
    said = ", ".join(part.strip(" ,.;:").lower() if index else part.strip(" ,;")
                     for index, part in enumerate(keep) if part.strip(" ,.;:"))
    if not said:
        return None
    if len(said) < 40 or len(said) < 0.55 * len(str(text).strip()):
        return None
    said = said[0].upper() + said[1:]
    return said if said.endswith((".", "!", "?")) else said + "."


def _any_meal(banned):
    """The default list, changed only when the line has ruled an everyday dinner out."""
    if GLUTEN & banned:
        # Everything here is gluten free by construction: rice, potatoes and pulses, no bread,
        # pasta or flour. The egg and the cheese go when the same line rules them out too.
        egg = "" if {"egg", "eggs"} & banned else " and an egg"
        cheese = "hummus" if DAIRY & banned else "cheese"
        return ("Ten-minute dinners, all gluten free: rice fried with frozen veg" + egg +
                "; a jacket potato with beans and " + cheese +
                "; or a chickpea and tomato curry with rice. Tell me what is in the fridge and "
                "I will pick one.")
    if {"egg", "eggs"} & banned:
        if DAIRY & banned:
            return ("Ten-minute dinners: a chickpea and tomato curry with rice; pasta with garlic, "
                    "chilli and olive oil; or beans on toast with hummus. Tell me what is in the "
                    "fridge and I will pick one.")
        return ("Ten-minute dinners: a chickpea and tomato curry with rice; pasta with garlic, "
                "chilli and olive oil; or beans on toast with a little cheese or hummus. Tell me "
                "what is in the fridge and I will pick one.")
    if MEAT <= banned:
        return ("Ten-minute dinners: pasta with garlic, chilli and olive oil; a chickpea and "
                "tomato curry with rice; or eggs on toast. Tell me what is in the fridge and I "
                "will pick one.")
    return ANY_MEAL


# Words that say when to cook or how it should feel, never what to cook: a recipe "for tonight"
# or "something quick" is a meal question with no dish in it.
_NOT_A_DISH = frozenset((
    "tonight", "today", "now", "later", "tomorrow", "weekend", "evening", "lunchtime", "noon",
    "quick", "quickly", "fast", "easy", "easier", "simple", "cheap", "cheaper", "healthy",
    "healthier", "nice", "tasty", "good", "new", "different", "something", "anything", "nothing",
    "some", "one", "two", "few", "first", "family", "kids", "friends", "guests", "everyone",
    "vegetarian", "vegan", "gluten", "dairy", "free", "light", "filling", "cosy", "comfort",
))


def _cauliflower_rice(memory, understood):
    """Cauliflower rice, and the low-carb reason people ask for it in the same sentence."""
    words = {_fold(str(word)) for word in (understood.get("words") or [])}
    method = ("Grate or blitz a head of cauliflower into rice-sized bits, wrap it in a tea towel "
              "and squeeze out the water, then fry it in a little oil for 4 to 5 minutes with salt "
              "until it is hot but still has a bite. Do not boil it: that is what makes it soggy. "
              "One head makes four good portions and keeps three days in the fridge.")
    if words & {"carb", "carbs", "keto", "diet", "diabetes", "sugar", "low"}:
        return ("Cauliflower is one of the lowest-carb vegetables there is: about 3g of carbs per "
                "100g, against about 28g in cooked rice, so it works on a low-carb or diabetic "
                "plate. " + method)
    return method


def _recipe_for_unknown_dish(lowered):
    """True for "a recipe for <dish>" where the dish is not food the kitchen knows.

    The meal entry's key admits `recipe`, because "need a cheap recipe with chickpeas" is a
    meal question. It also admits "need a recipe for shortbread", which is a question about
    shortbread and nothing the table can make, so that one gets the honest hedge. An
    ingredient the pantry knows stays a meal question ("recipe with mince", "recipe for beans").
    """
    match = re.search(r"\brecipe\b(?:\s+(?:for|of|to make))?\s+(.*)$", lowered)
    if not match:
        return False
    tail = re.findall(r"[a-z']+", match.group(1))
    if not tail:
        return False
    if any(word in ("idea", "ideas", "meal", "dinner", "tea", "supper") for word in tail):
        return False
    # "whats a quick recipe for tonight" names no dish at all: "quick", "easy" and "tonight" say
    # how and when, not what, so they are dropped before the dish test and an empty tail stays a
    # meal question. Without this the line was a recipe for a dish called "tonight" and got the
    # honest hedge.
    food_words = [word for word in tail if word not in _NOT_A_DISH][:3]
    if not food_words:
        return False
    return all(word not in _INGREDIENT_WORDS and word not in _FOOD for word in food_words)
def _first_sentence(idea):
    """One idea cut to its opening sentence.

    Two ideas side by side have to stay a short answer: "got mince and rice" is two lines of
    cooking, not two paragraphs. The whole idea is still there when it answers on its own.
    """
    parts = re.split(r"(?<=[.!?])\s+", idea.strip(), maxsplit=1)
    return parts[0] if parts else idea


def _leftover(folded, clean):
    """True when the food named has already been cooked: a leftover question, not a recipe."""
    return (any(word in LEFTOVER_WORDS for word in folded)
            or any(phrase in clean for phrase in LEFTOVER_PHRASES))


# Beans that will not soften, and beans with no time to soak, are the two things people write
# about dried pulses. Both are the same entry's question, so the entry reads the line rather
# than three entries guarding each other's lines.
_PULSES_HARD = re.compile(
    r"\b(?:still (?:hard|firm|crunchy|tough|chalky)|not soft(?:ening)?|wont (?:soften|go soft)"
    r"|will not (?:soften|go soft)|never soften|hard after|too hard|too firm|took ages"
    r"|been cooking (?:for )?(?:an|two|2|three|3) hours?)\b")
_PULSES_NO_SOAK = re.compile(
    r"\b(?:without (?:a )?soaking|without a soak|no soak(?:ing)?|skip(?:ped)? the soak"
    r"|skip(?:ping)? soaking|didnt soak|did not soak|forgot to soak|forget to soak"
    r"|no time to soak|havent soaked|have not soaked|not soaked|quick soak|quick-soak"
    r"|in a hurry|short on time|last minute|just cook|straight from the bag"
    r"|without the soak|unsoaked)\b")
# A tin or a jar is not a bag of dried beans: that line is a dish, and another entry has it.
_PULSES_TIN = re.compile(r"\b(?:tinned|canned|jarred|jar|tin|tins|packet|carton)\b"
                         r"|\bcans? of\b")
# A green bean, a runner, a broad bean and a mangetout are vegetables with a four-minute answer,
# and "my green beans are stringy" is dishes.py's. Only the dried pulses are this entry's.
_PULSES_FRESH = re.compile(
    r"\b(?:green|runner|broad|french|string|stringy|snap|mangetout|edamame|pea|peas)\b")
# An appliance does the cooking, and its own card says how: "how do i cook beans in a slow
# cooker" wants the slow cooker's times, not the soaking times. The kidney bean is the exception
# - raw kidney beans in a slow cooker are a safety line, and that one is this entry's.
# A dried bean is not the fresh pod however the line names it: "broad beans" is a fresh vegetable
# for four minutes in salted water, but "do broad beans need soaking" is a bag of them, and the
# soak is the whole question. These words take the fresh reading off the line.
_PULSES_DRIED = re.compile(
    r"\b(?:soak|soaks|soaked|soaking|overnight|quick soak|no soak|dried|dry|bag|bags|packet"
    r"|packets|tinned|tin|canned|can)\b")
_PULSES_APPLIANCE = re.compile(
    r"\b(?:slow cooker|slow cookers|crock ?pot|pressure cooker|pressure cookers|instant pot"
    r"|air fryer|air fryers|multicooker|multi cooker)\b")
_PULSES_KIDNEY = re.compile(r"\b(?:kidney|kidney beans?)\b")


def _pulses(memory, understood):
    """A bag of dried beans wants the soak and the time; a pan that will not soften wants why.

    Old beans and early acid are the two reasons a bean stays hard however long it cooks, and
    "can I skip the soaking" is a different answer again (the two-minute boil and the hour in
    the water), so this reads the line instead of putting all three in one card.
    """
    said = _words_and_text(understood)
    if (_PULSES_FRESH.search(said) and "split peas" not in said
            and not _PULSES_DRIED.search(said)):
        return None     # a green bean is a vegetable: four minutes in salted water, not a soak
    if _PULSES_TIN.search(said) and not _PULSES_HARD.search(said):
        return None     # a tin of beans is a dish: beans on toast, a chilli, a salad
    if _PULSES_APPLIANCE.search(said) and not _PULSES_KIDNEY.search(said):
        return None     # the appliance's own card has the times for its pot
    if _PULSES_HARD.search(said):
        return ("Old beans are usually the reason: a bag that has sat in the cupboard for years "
                "takes twice as long however you cook it. Keep it at a bare simmer with the lid "
                "just off, top it up with hot water, and give it another 20 to 30 minutes with a "
                "half teaspoon of bicarbonate of soda in the pan - and leave the salt, tomato and "
                "vinegar until the beans are soft, because acid early is the other thing that "
                "keeps the skins tough. Hard water does the same, so use filtered water if yours "
                "is very chalky.")
    if _PULSES_NO_SOAK.search(said):
        return ("You can skip the soaking: boil them hard for 2 minutes, take the pan off the "
                "heat and leave it covered for an hour, then simmer as usual - or cook them "
                "straight from the bag for 30 to 45 minutes longer and top up with hot water. "
                "Kidney beans are the one exception: boil them hard for 10 minutes before the "
                "simmer, and never cook them raw in a slow cooker.")
    return ("Dried chickpeas and beans want 8 hours of cold water, then 45 to 60 minutes of hard "
            "simmering; lentils need no soaking at all, just 20 to 30 minutes in the pan. Kidney "
            "beans must be boiled hard for 10 minutes, never slow cooked raw.")


def _lentils(memory, understood):
    """Lentils by colour, because the times and the texture are the whole question."""
    return ("No soaking: rinse and simmer in plenty of water. Red lentils split and go soft in 15 "
            "to 20 minutes, which soups and dal want; green or brown stay whole at 20 to 25; puy "
            "take about 25 and hold their shape in salads. Salt near the end, not at the start, and "
            "taste at 15 minutes: a minute either way is firm against mushy. One mug of dried makes "
            "two cooked, and a bay leaf and half an onion in the water do more for flavour than "
            "anything added later.")


# The shapes that ask for a plan for the week rather than a dish for tonight.
_PLAN_ASK = re.compile(
    r"\b(?:meal plans?|meal planning|planning meals|plan (?:my |the |a )?(?:week|meals)\b"
    r"|meals for the week|weekly meal|food plan|plan a week of meals)")


def _keeps_its_own_name(memory, understood, idea):
    """Whether the line names a food the pantry has a row for under that very word, and the
    dish about to be sent never says it.

    The dish table files the charcuterie together, so "what can I make with chorizo" was
    answered "do a bacon and egg hash" - a dish with no chorizo in it, about a food the person
    had not mentioned - while the pantry held a chorizo idea all along. Ham, kale, hummus and
    bean sprouts went the same way (bacon hash, a spinach frittata, a chickpea curry, beans on
    toast). A food is answered under its own name when the pantry has one for it: the idea for
    the food beats the idea for the group it was filed with.

    Only for a line that names one food, and only when the reply does not say the word: "what
    can I make with chicken breast" is answered about chicken and that is the same food.
    """
    from . import meals

    words = [_fold(word) for word in (understood.get("words") or ())]
    named = []
    for place, word in enumerate(words):
        if _INGREDIENT_WORDS.get(word) != _INGREDIENT_WORDS.get(word, word):
            continue
        name = _INGREDIENT_WORDS.get(word)
        if name and _fold(name) == word and word not in named:
            named.append(word)
        # a two-word name ("pork belly") counts as one food, not as two
        if place + 1 < len(words):
            pair = word + " " + words[place + 1]
            if _INGREDIENT_WORDS.get(pair) and _fold(_INGREDIENT_WORDS[pair]) == pair:
                named.append(pair)
    if len(named) != 1:
        return False
    text = " ".join(words)
    if (any(word in LEFTOVER_WORDS for word in words)
            or any(phrase in text for phrase in LEFTOVER_PHRASES)):
        # A food that is already going over is a use-it-up question, and the dish table is the
        # one that answers it ("old bread" becomes crumbs; a plain bread idea is a loaf they do
        # not have): the food is named, and the idea for naming it is not the answer.
        return False
    if meals._diet_said(memory):
        # a diet said a turn ago has its own answer, and it is the one that names the food as
        # something to leave out: a plain idea about that food is the wrong reply
        return False
    if any(f"{marker} {named[0]}" in text for marker in ("old", "stale", "dry", "yesterday")):
        return False
    if meals._is_the_ruled_out_food(named[0], " ".join(words)):
        # The food is named in order to leave it out: "what can i cook without an onion" reached
        # the onion's own row and was answered with onion soup. The dish table reads the exclusion
        # and has a dinner the line can actually eat, so its idea is the answer and the row for
        # the food is not. The names differ by the group the pantry files them under - the line
        # says "fish" and the table rules out `white fish` - so the word is matched as a form of
        # the food rather than as a spelling.
        return False
    said = [_fold(word) for word in re.findall(r"[a-z']+", idea.lower())]
    return named[0] not in said

# A pet is not a dinner. The pantry keys the food ("rabbit", "guinea pig") and cannot tell the
# animal in the hutch from the one at the butcher's, so "my rabbit ate the leftovers" was given a
# braise and "my rabbit has eaten the leftovers" the same. An animal the line owns, or one that
# has eaten something, is a pet question: the pets rows answer it, and the kitchen stands down.
PET_ANIMALS = ("rabbit", "rabbits", "bunny", "bunnies", "guinea pig", "guinea pigs", "guineapig",
               "hamster", "hamsters", "gerbil", "gerbils", "chinchilla", "chinchillas",
               "degus", "degu", "hedgehog", "hedgehogs", "tortoise", "tortoises", "parrot",
               "parrots", "budgie", "budgies")
_PET_OWNED = ("my ", "our ", "pet ", "the pet ")
_PET_EATING = ("ate", "eaten", "eats", "chewed", "chewing", "nibbled", "nibbling", "got into",
               "stole", "stolen", "swallowed")

# An order question names an ingredient, so every "what about <food>" meal path reads it as "what
# can I make with <food>": in a tea thread the follow-up "what about milk first or last" was
# answered "A white sauce: butter and flour cooked a minute, then milk whisked in". The person is
# asking what goes in first, not what to cook, so the dinner rows stand down on the wording that
# asks for a sequence and leave the line to the row that knows the drink or the dish.
_ORDER_NOT_A_MEAL = ("first or last", "last or first", "first or after", "before or after",
                     "in first", "in last", "go in first", "goes in first", "go in last",
                     "goes in last", "which goes in", "which one goes in", "which first",
                     "in what order", "what order", "order do i", "either way round",
                     "milk first", "milk last")


# The other half of the same subject: a line about the milk that goes in a cup of tea is a drink
# question, and "is oat milk good in tea" was answered with porridge because the dish table read
# the two foods in it (oats and milk) as a pair to cook.
_MILK_IN_TEA_NOT_A_MEAL = ("in tea", "in my tea", "in the tea", "in a cup of tea",
                           "in a mug of tea", "in a brew", "in my brew", "in the brew",
                           "for a cup of tea", "for my tea with milk")


def _a_brew_not_a_dinner(line):
    """True when the line is about the order or the milk of a brew rather than what to cook."""
    low = " " + str(line or "").lower() + " "
    if any(f" {phrase} " in low for phrase in _ORDER_NOT_A_MEAL):
        return True
    if " milk " not in low and not low.startswith(" milk"):
        return False
    return any(f" {phrase} " in low or f" {phrase}." in low
               for phrase in _MILK_IN_TEA_NOT_A_MEAL)


def _an_order_not_a_dinner(line):
    """True when the line asks which thing goes in first rather than what to cook."""
    low = " " + str(line or "").lower() + " "
    return any(f" {phrase} " in low for phrase in _ORDER_NOT_A_MEAL)


# A plant is not a dinner. The pantry keys the food and cannot tell the lemon in the fruit bowl
# from the one in the ground: "i bought a lemon tree" was answered "Lemon and garlic chicken, or
# just a squeeze over the finished dish", an apple tree got the stewed apple and a fig tree the
# figs. The words that put the food in the ground or on the windowsill belong to the garden rows,
# so a line that names one stands this table down - unless it also asks what to cook, because
# "what can i cook with the tomatoes from my plant" is still a dinner.
_PLANT_NOT_A_DINNER = ("tree", "trees", "bush", "bushes", "shrub", "shrubs", "sapling",
                       "saplings", "seedling", "seedlings", "plant", "plants", "potted",
                       "bare root", "bare-root", "root ball", "compost", "greenhouse",
                       "allotment", "windowsill", "window sill", "cuttings", "cutting")
_PLANT_GARDEN_VERB = ("bought", "buy", "buying", "planted", "planting", "grow", "growing",
                      "grew", "repot", "repotted", "died", "dying", "dead", "water", "watering",
                      "feed", "feeding", "prune", "pruning", "sow", "sowing", "sowed",
                      "transplant", "potted on", "flowering", "fruiting")
_PLANT_COOK_ASK = ("cook", "cooks", "cooking", "recipe", "recipes", "make", "makes", "making",
                   "eat", "eating", "dinner", "supper", "lunch", "roast", "bake", "baking",
                   "fry", "boil", "serve", "dish", "meal", "use up", "use them", "use it")


# Where a plant word comes from, it is the source and not the subject: "what can i do with a glut
# of courgettes from the allotment" is a courgette question, and so are the apples off the tree,
# the tomatoes in the greenhouse and the rhubarb from my plot. The preposition (and the
# determiner after it) is what tells the two apart.
_PLANT_SOURCE = re.compile(
    r"\b(?:from|off|out of|in|on|at)\s+(?:the\s+|my\s+|our\s+|a\s+|an\s+|his\s+|her\s+"
    r"|their\s+)?(?:" + "|".join(_PLANT_NOT_A_DINNER) + r")\b")


# A source only makes the food the subject when the line asks what to do with it. "the apples on
# the tree are rotten" names the same source and is a tree question, so the ask is the second half
# of the test.
# A herb bought as a plant is the windowsill's, not the garden's: nobody grows "a herb" outside.
_PLANT_KITCHEN_PLANT = ("herb", "herbs")
# A plant that is carrying the fruit has stopped being the subject: "my fig tree has fruit what do
# i do with them" is the figs in the kitchen, and the bare-root month is no answer to it.
_PLANT_BEARS = ("has fruit", "have fruit", "had fruit", "with fruit", "full of fruit",
                "loaded with fruit", "in fruit", "covered in fruit", "bears fruit",
                "bearing fruit", "producing fruit")
_PLANT_DO_WITH = ("do with", "use", "using", "used up", "glut", "too many", "loads of",
                  "all these", "all this", "all the", "bumper", "plenty of", "left over",
                  "what can i", "what should i", "what do i")


def _the_garden_has_this_plant(line):
    """Whether a garden row takes this line, so the pantry may stand aside for it.

    Asked of the garden's own entries rather than guessed from the words: the plant table stood
    down on any plant word, and where the garden had no row the turn landed on an echo. The
    reading is built here because only the clean line is in hand, which is all the keys need.
    """
    from .garden import ENTRIES as _GARDEN_ENTRIES
    text = str(line or "")
    words = tuple(word for word in re.split(r"[^a-z0-9']+", text.lower()) if word)
    reading = {"clean": text, "text": text, "words": words, "kind": "ask"}
    return find(reading, entries=_GARDEN_ENTRIES) is not None


# A plant that came home from the shop as a bush, a bare-root tree or a pot is not a thing to
# cook, whether or not the garden table has a row that takes the line yet: "i bought a blueberry
# bush" was answered with a blueberry compote when the garden's own table had nothing to say.
# The woody and the bought shapes are the test together, so a named herb in a pot stays the
# kitchen's ("i bought a basil plant") and a tomato glut stays the pantry's.
_PLANT_WOODY = ("tree", "trees", "bush", "bushes", "shrub", "shrubs", "sapling", "saplings",
                "bare root", "bare-root", "root ball", "climber", "climbers", "hedge", "hedges")
_PLANT_PURCHASE = ("bought", "buy", "buying", "picked up", "came home with", "brought home",
                   "arrived", "delivered", "got it home")


def _a_plant_from_the_shop(line):
    """A woody plant that has just been bought: the garden's, even when no row answers yet."""
    low = " " + str(line or "").lower().replace("'", " ") + " "
    return (any(f" {word} " in low for word in _PLANT_WOODY)
            and any(f" {word} " in low for word in _PLANT_PURCHASE))


def _a_plant_not_a_dinner(line):
    """True when the line is about the plant rather than the fruit or the leaf on the plate."""
    low = " " + str(line or "").lower().replace("'", " ") + " "
    if not any(f" {word} " in low for word in _PLANT_NOT_A_DINNER):
        return False
    if (any(f" {word} " in low for word in _PLANT_KITCHEN_PLANT)
            and any(f" {word} " in low for word in ("bought", "buy", "buying", "got", "picked up"))):
        # Buying "a herb plant" is buying a thing to cook with - there is no herb called "herb"
        # to grow. The named herbs keep their growing cards ("i bought a basil plant"), and a
        # herb that is ailing keeps the plant-care card, because that is not a purchase.
        return False
    if any(f" {word} " in low for word in _PLANT_GARDEN_VERB):
        # A garden verb is the garden's question only when the garden has a row for the plant
        # or the line is a bush, a bare-root tree or a pot straight from the shop: standing aside
        # for a row that does not exist is how a pantry answer became an echo.
        return _the_garden_has_this_plant(line) or _a_plant_from_the_shop(line)
    if any(f" {phrase} " in low for phrase in _PLANT_BEARS):
        # The fruit is the subject now, even though no ask word is on the line: the pantry keys
        # the fruit and answers it.
        return False
    # A plant named as where the food came from is the pantry's line still: the subject is the
    # courgette or the apple, and the allotment is only its address. Every plant word being a
    # source is what makes the food the subject; one that is not ("i bought a lemon tree") is
    # the garden's.
    named = sum(low.count(f" {word} ") for word in _PLANT_NOT_A_DINNER)
    asked = (any(f" {word} " in low for word in _PLANT_COOK_ASK)
             or any(f" {word} " in low for word in _PLANT_DO_WITH))
    if named and asked and len(_PLANT_SOURCE.findall(low.replace("  ", " "))) >= named:
        return False
    if any(f" {word} " in low for word in _PLANT_COOK_ASK):
        return False
    # A plant the garden has nothing to say about stays the pantry's: standing aside there left
    # the person with an echo. "i bought a potted parsley", "i bought a blueberry bush" and
    # "i picked up a fig tree" each had a pantry answer and no garden row, so the stand-down was
    # a warm nothing. The garden rows are the test: if none of them takes the line, it is not
    # their question.
    return _the_garden_has_this_plant(line) or _a_plant_from_the_shop(line)


# A feeding question about a hutch pet is the pets table's, not the pantry's. "Can rabbits eat
# lettuce" names two foods, so the table below answered it with a braise and a lettuce idea: the
# animal was read as the dinner. The pantry cannot see the difference between the rabbit in the
# hutch and the one at the butcher's, so the shape of the question decides it - an animal that is
# the one eating, or a food weighed up for it, is not a thing to cook.
_FEEDING_ANIMALS = (r"rabbits?|bunn(?:y|ies)|guinea\s?pigs?|hamsters?|gerbils?|chinchillas?|"
                    r"degus?|hedgehogs?|tortoises?|budgies?|parrots?")
FEEDING_EATS = re.compile(
    r"\b(?:" + _FEEDING_ANIMALS + r")\b(?:\W+\w+){0,3}?\W+(?:eat|eats|eating|have|has|drink|"
    r"drinks|be\s+fed|be\s+given|be\s+allowed|allowed|take|tolerate)\b")
FEEDING_GIVEN = re.compile(
    r"\b(?:feed|feeding|fed|give|giving|gave)\b(?:\W+\w+){0,2}?\W+(?:my|our|the|a|an)?\W*"
    r"(?:" + _FEEDING_ANIMALS + r")\b")
FEEDING_SAFE_FOR = re.compile(
    r"\b(?:safe|ok|okay|fine|bad|good|toxic|poisonous|dangerous|harmful|lethal)\b"
    r"(?:\W+\w+){0,4}?\W+(?:for|to)\b(?:\W+\w+){0,2}?\W+(?:" + _FEEDING_ANIMALS + r")\b")


# A line that is about cooking the animal is the meat, however it is worded: "a good recipe for
# rabbit" is a plate, not a hutch, and "safe to eat" is the shopper's question.
FEEDING_NOT_FOOD = ("recipe", "recipes", "roast", "braise", "casserole", "stew", "fry", "bake",
                    "butcher", "joint", "dinner", "supper", "meal", "chef", "oven", "pan",
                    "sous vide", "marinade", "rub")


def _feeding_ask(line):
    """True when the line asks what an animal may eat, rather than what to cook with it."""
    low = " " + str(line or "").lower() + " "
    if any(word in low for word in FEEDING_NOT_FOOD):
        return False
    return bool(FEEDING_EATS.search(low) or FEEDING_GIVEN.search(low)
                or FEEDING_SAFE_FOR.search(low))


def _pet_not_dinner(line):
    """True when the line is about somebody's pet rather than about what to cook."""
    low = " " + str(line or "").lower() + " "
    animals = [animal for animal in PET_ANIMALS if f" {animal} " in low]
    if not animals:
        return False
    if any(f" {owner}{animal} " in low for animal in animals for owner in _PET_OWNED):
        return True
    # "rabbit ate the leftovers" is a pet too: a dish is not said to eat
    return any(f" {verb} " in low for verb in _PET_EATING)


# The animals in the pantry that are also bought as meat. Main's `_pet_not_dinner` covers the ones
# nobody eats - a hamster, a tortoise, a budgie - and a hutch pet; a duck, a goose, a pigeon, a quail,
# a pheasant and a deer are both, so the possessive alone does not settle them and a word that puts
# the animal in the house does. "My duck is called donald" is not a dinner, and "what can i cook with
# my duck in the room" was answered with duck breast on c955e20.
PET_MEAT_ANIMALS = ("duck", "goose", "gander", "pigeon", "quail", "pheasant", "deer")
PET_HOME = re.compile(
    r"\b(?:in\s+the\s+(?:room|house|home|lounge|living\s+room|front\s+room|kitchen|bedroom|"
    r"garden)|indoors|hutch|cage|coop|aviary|litter\s+tray|is\s+called|named|kept\s+in)\b")
# A word that says the bird or the beast came from a butcher, a shoot or a freezer is the meat.
PET_NOT_FOOD = ("bought", "butcher", "from the shop", "from the market", "farmers market",
                "in the freezer", "frozen", "from the farm shop", "shot", "from a shoot",
                "joint", "breast", "thigh", "leg", "casserole")
# A care question about the animal is not a line about cooking it, and neither is the animal that
# has eaten something: "my rabbit ate the leftovers" has the pets answer and no braise in it.
PET_CARE = ("feed", "feeding", "fed", "food for", "called", "named", "care", "vet", "hutch",
            "litter", "breed", "groom", "sick", "ill", "not eating", "wont eat", "won't eat",
            "ate", "eaten", "eats", "chewed", "chewing", "nibbled", "nibbling", "got into",
            "stole", "stolen", "swallowed")
PET_COOKING_ASK = ("cook", "make", "recipe", "dinner", "tea", "supper", "meal", "roast",
                   "braise", "use up")


def _reads_as_a_pet(line):
    """True when the animal a line names is somebody's own, not the meat on the counter."""
    low = " " + str(line or "").lower() + " "
    if any(marker in low for marker in PET_NOT_FOOD):
        return False
    if _pet_not_dinner(line):
        return True
    owned = any(f"my {animal} " in low or f"our {animal} " in low
                for animal in PET_MEAT_ANIMALS)
    return owned and bool(PET_HOME.search(low))


def _pet_or_meat(line):
    """The answer for a line that names an animal it may own: a pet is not dinner, the meat is.

    "What can i cook with my rabbit in the room" was a braise on main before the pet gate, and a
    shrug after it. The line can mean either, so the reply says which reading it took and then
    gives the pantry's cooking for the meat. None when the line is a care question, an animal that
    has eaten something, or not a line about cooking at all: those have their own answers.
    """
    low = str(line or "").lower()
    if not any(word in low for word in PET_COOKING_ASK):
        return None
    if any(word in low for word in PET_CARE):
        return None
    if not _reads_as_a_pet(low):
        return None
    for name, (aliases, idea) in PANTRY.items():
        if name not in PET_ANIMALS + PET_MEAT_ANIMALS:
            continue
        if f" {name} " not in low and f" {name}s " not in low:
            continue
        meat = str(idea)
        head, _, rest = meat.partition(": ")
        if not rest or not head or head.lower().split()[0] not in name:
            rest = meat
        rest = rest.strip()
        if not rest:
            return None
        return ("That reads as a pet rather than a dinner, and I would keep it off the plate. "
                "If you meant the meat, " + rest[0].lower() + rest[1:])
    return None


def _meal_ideas(memory, understood):
    """Dinner ideas come from bot/knowledge/meals.py, one table of dishes by ingredient.

    This entry stays because the arbiter still routes meal questions here; the crowd and
    occasion paths answer a meal for a table when the table has no dish to offer.
    """
    from . import meals

    words = understood.get("words")
    if not isinstance(words, list):
        words = " ".join(words or ()).split()
    line = str(understood.get("clean") or " ".join(str(word) for word in words))
    text = line
    turns = memory.get("turns")
    if isinstance(turns, list):
        text += " " + " ".join(str(turn.get("user") or "") for turn in turns[-4:]
                               if isinstance(turn, dict))
    if _pet_not_dinner(line):
        # "my rabbit ate the leftovers" is not a braise: the pets rows answer it. A line that does
        # ask what to cook with the animal it owns gets the reading and then the cooking.
        return _pet_or_meat(line)
    if _a_brew_not_a_dinner(line):
        # "what about milk first or last" and "is oat milk good in tea" are the brew, not a
        # dinner idea: the tea-milk row answers both
        return None
    if _PLAN_ASK.search(line.lower()):
        # A plan for the week is a method, not one dish: the useful answer is how to plan, and
        # the dish table would give a single dinner to a question about five of them.
        return ("Pick four dinners you already cook and put them on the fridge, then shop for "
                "just those - one double batch goes in the freezer for the night you are late "
                "home. Keep one night loose for eggs on toast or a takeaway, and plan whatever "
                "spoils first for the day after you shop.")
    if any(word in line.lower() for word in ("dessert", "puddings", "pudding", "afters",
                                             "ice cream", "sweet thing")):
        # A pudding is the end of the dinner, not another dinner: the dessert entry above
        # answers these lines, and a traybake is a reply to a different question.
        return None
    # A food the line only names in order to rule it out ("without an onion", "no pasta",
    # "i dont like mushrooms") is no more use than one they have not got, and the pantry reads
    # every food it knows. The older ban list names only the foods a diet or an allergy is said
    # in, so the food named beside "without" was read as what to cook with, and the idea for it
    # was the answer to a dinner with none of it.
    # A food they are short of is left out of every meal, not only breakfast: "im out of eggs
    # what can i have for dinner" was answered "Scrambled eggs: 3 eggs on a low heat". It is not
    # a diet - the person may eat eggs tomorrow - so it is read for this answer only.
    banned = (frozenset(_no_meat_also_means_fish(_excluded(text)))
              | frozenset(_short_of_food(text))
              | frozenset(negated_ingredients(understood)))
    # A meal for a table, or a day that matters, is the crowd answer: twelve people are not
    # a weeknight pick. Otherwise the dish table answers, and only a line it has no dish for
    # gets the generic list.
    # "for 20 minutes" is a clock, not twenty people: the crowd count reads the line
    # without the times in it.
    table = re.sub(r"\bfor\s+\d{1,3}\s*(?:min|mins|minute|minutes|hour|hours|sec|seconds)\b",
                   " ", text).lower()
    # A line that says who cannot eat what keeps the dish table: one tray of chicken
    # thighs is the wrong answer to a vegetarian dinner party.
    # Only a line that asks for a meal can get the crowd answer: "maybe i will cook her
    # favourite thing", said about someone who has died, is not a request for a traybake.
    asking = str(understood.get("intent") or "") != "news" and (
        str(understood.get("kind") or "") == "question"
        or str(understood.get("intent") or "") in ("question", "request")
        or any(word in line.lower() for word in (
            "what", "idea", "ideas", "something", "suggest", "suggestion", "dinner",
            "dinners", "meal", "meals", "menu", "tea", "supper", "lunch", "cook for",
            "make for", "feed", "recipe", "anything", "any", "need", "want", "party",
            "guests", "everyone")))
    # A table of three to five is still a table when the line says a party or guests rather than
    # only a number: "dinner party for four" was the crowd card with "feeds eight from one oven"
    # in it, and standing it down from the crowd answer sent it to the ten-minute list instead.
    table_count = _crowd(table)
    at_table = asking and not _says_a_diet(line) and (
        table_count >= 6
        or (table_count >= 3
            and any(phrase in line.lower() for phrase in _CROWD_PHRASES))
        or (
            _occasion(table) and any(
                phrase in line.lower() for phrase in ("what should i cook", "what can i cook",
                                                      "what shall i cook", "what to cook",
                                                      "what to make", "meal", "dinner", "cook",
                                                      "no idea"))))
    if at_table:
        return _crowd_or_any(table, banned)
    idea = meals.suggest(memory, understood)
    if idea and banned and _bans((), str(idea), banned):
        # The dish table does not read a diet: "im egg free what can i have for tea" was answered
        # "How about an omelette: whisk two or three eggs...". A dish whose own words name a food
        # they cannot eat is not an idea for them, and the list below reads the diet.
        idea = None
    if idea and _keeps_its_own_name(memory, understood, idea):
        # The food has a row of its own, and the dish was built for the group it was filed
        # with: the own-name idea is the answer, said about the food they named.
        words = understood.get("words")
        if not isinstance(words, list):
            words = " ".join(words or ()).split()
        own = _pantry_idea([str(word) for word in words] + str(
            understood.get("clean") or "").split(), banned, line.lower())
        if own and isinstance(own[1], str) and own[1].strip():
            idea = own[1]
    if idea:
        return idea
    # The dish table has no row for this food, but the pantry below knows a hundred and
    # forty of them: "what can i make with parsnips" is the pantry's roast parsnips, and
    # "with feta" its baked feta, where the generic quick list is worse than either.
    asks_food = (understood.get("topic") in ("cooking", "food-and-drink")
                 or any(phrase in line.lower() for phrase in MEAL_ASK_PHRASES))
    if asks_food:
        from_pantry = meal(understood, banned=banned, memory=memory)
        if (isinstance(from_pantry, str) and from_pantry.strip()
                and not _bans((), from_pantry, banned)):
            return from_pantry
    if meals.unknown_food(understood):
        # A food nobody here knows either: the line is about an ingredient, and a dish
        # picked at random answers a different question.
        return None
    if not banned and re.search(r"\bwithout\b", line.lower()) and not _says_a_diet(line):
        # "what can i make without money" leaves out nothing this kitchen can cook around. The
        # word after "without" can be anything a line is short of, and ten-minute dinners are an
        # answer to a question nobody asked.
        return None
    if _says_diabetes(text):
        # The balance of the plate, not a food to leave out: the dish table has nothing to say
        # about it, so "any dinner ideas" after "my sister is diabetic" was the plain pasta
        # list. Read from the recent turns, so the follow-up gets the same answer as the line
        # that named the condition.
        return DIABETIC_PLATE
    return _any_meal(banned)


def pantry_idea(name):
    """The pantry's own idea for one food, by name, or None.

    Asked by the use-up table in bot/knowledge/meals.py, which has to know whether the idea it is
    about to be beaten by is a dish (a use for the food) or a way of cooking it from raw.
    """
    folded = _fold(str(name or "").lower())
    if not folded:
        return None
    for aliases, idea in PANTRY.values():
        for alias in aliases:
            key = _fold(str(alias).lower())
            if key == folded or key == folded.rstrip("s") or key.rstrip("s") == folded:
                return idea
    return None


def _pantry_idea(words, banned, clean=""):
    """The pantry's idea for the first food the line names, when no meal idea covers it.

    MEAL_IDEAS names forty foods and the pantry a hundred and forty, so "what can I make with
    bananas" or "with cabbage" fell past both and got the default ten-minute list while the
    pantry held a good answer all along. Same shape as the loop above: earliest food in the
    line wins, and an idea the line has ruled out is skipped.

    A name here has to be that name: `_same` reads a prefix as the same word, which is right for
    eggs/egg but made "peanut butter" a pea and "bean sprouts" the beans on toast, so the match
    is the folded word (and `NOT_THIS_FOOD` steps the name aside when a word in front makes it a
    different food).
    """
    found = None
    # Where the name was found and how much of the line it covers, so a longer name wins the same
    # spot: "beef shin" is the braise row, not the steak the word "beef" would give it.
    reached = None
    for name, (aliases, idea) in PANTRY.items():
        if _bans(aliases, idea, banned):
            continue
        if any(phrase in clean for phrase in NOT_THIS_FOOD.get(name, ())):
            continue
        for alias in aliases:
            parts = alias.split()
            for start in range(len(words) - len(parts) + 1):
                if all(_fold(words[start + offset]) == _fold(parts[offset])
                       for offset in range(len(parts))):
                    spot = (start, -len(parts))
                    if reached is None or spot < reached:
                        reached = spot
                        found = (start, idea)
                    break
    return found


def _occasion(text):
    """True when the line is a day that matters: a birthday, a wake, or a "70th"."""
    if any(word in text for word in _OCCASIONS):
        return True
    # "my mums 70th next saturday" names the day by its number, not by the word birthday.
    return bool(re.search(r"\b\d{1,3}(?:st|nd|rd|th)\b", text))


def _crowd_or_any(text, banned):
    """The fallback list, unless the line is a meal for a table or an occasion."""
    if _table_text(text):
        return _crowd_meal(banned, _occasion(text), _crowd(text))
    if _occasion(text) and any(
            phrase in text for phrase in ("what should i cook", "what can i cook",
                                          "what shall i cook", "what to cook", "what to make",
                                          "meal", "dinner", "cook", "no idea")):
        # "it's my mum's 70th birthday, what should I cook" names no ingredient and no number:
        # a ten-minute dinner is the wrong answer to a day like that.
        return _crowd_meal(banned, True, _crowd(text))
    return _any_meal(banned)


ANY_BREAKFAST = ("Porridge with a spoon of peanut butter and a banana, eggs on toast, or yoghurt "
                 "with fruit and oats: any of the three takes under ten minutes and keeps you going "
                 "until lunch. If mornings are rushed, boil an egg the night before and take a "
                 "piece of fruit with it.")

# What a breakfast is made of, and what is in it, so a diet is read against the food rather than
# hand-written into a branch of its own. The branches used to be eggs, dairy and nuts, and
# "im gluten free what can i have for breakfast" fell through all three to the plain answer and
# offered "eggs on toast" - toast is the one thing a coeliac cannot have. A table also composes:
# a vegan coeliac with a nut allergy gets the porridge and the fruit, not a text that suits one.
# `needs` is the food a line has to allow for the idea to be offered.
def _porridge(banned):
    """Porridge, made with what the diet allows.

    Ordinary oats are grown and milled alongside wheat, so a coeliac has to look for oats
    labelled gluten free: the plain line was right for every other diet and handed the one
    person who must not have wheat a bowl of it.
    """
    if GLUTEN & banned:
        # "gluten free oats" is what the box says, so it is what the shopper looks for.
        milk = "oat milk" if DAIRY & banned else "milk"
        return "Porridge made with gluten free oats and " + milk
    if DAIRY & banned:
        return "Porridge made with oat milk and a spoon of jam"
    return "Porridge with a banana and a spoon of jam"


BREAKFAST_CHOICES = (
    # porridge is oats and water: the dairy in it is only ever what it is made with
    (frozenset(), lambda banned: _porridge(banned)),
    # The order is the order the plain answer gives, so a diet that rules out one thing still
    # gets the familiar breakfast: the toast ideas come before the ones nobody thinks of first.
    (EGGS | GLUTEN, "eggs on toast"),
    (GLUTEN | NUTS, "toast with peanut butter"),
    (GLUTEN, "beans on toast"),
    (GLUTEN, "toast with hummus"),
    (DAIRY | GLUTEN, "yoghurt with fruit and oats"),
    (DAIRY, "rice cakes with cheese"),
    (EGGS, "a boiled egg with fruit"),
    (NUTS, "a banana with a handful of nuts"),
)
# "keeps you going until lunch" is the plain answer's own wording, and it costs the follow-up:
# after a breakfast that says "lunch", "and for lunch" shares its only word with the sentence
# that said it and the breakfast is given again. The diet answers say "all morning" instead, so
# the lunch question that comes next reaches the lunch answer.
BREAKFAST_TAIL = (": any of the three takes under ten minutes and keeps you going all morning.")


# "im out of eggs", "we have none left": a food they are short of is not a food they cannot
# eat, and the plain list may name the very thing they have run out of. The shortage is read as
# an exclusion for this turn, which is all a kitchen needs: the list is built without it.
SHORT_OF_ASK = re.compile(r"\b(?:out of|ran out of|run out of|none left|nothing left|"
                          r"short of|outta|havent got|haven't got)\s+")


def _short_of_food(text):
    """The foods a line says they have none of, as opposed to cannot eat."""
    found = set()
    for match in SHORT_OF_ASK.finditer(str(text or "").lower()):
        found |= _foods_in_list(_list_words(str(text).lower()[match.end():match.end() + 60]))
    return found


def _rushed(banned):
    """The second sentence of a diet breakfast, so the answer is two sentences like the plain one.

    One sentence is not only short: "and for lunch" after it was narrowed to the only clause that
    shared a word with the line ("Keeps you going until lunch."), because the sentence-choosing
    in `answers` reads a one-sentence answer differently from a two-sentence one. The plain text
    ends with the egg, and that is the one thing an egg-free person cannot do.
    """
    if not (EGGS & banned):
        return (" If mornings are rushed, boil an egg the night before and take a piece of fruit.")
    return (" If mornings are rushed, put it out the night before and eat it on the way, because "
            "a breakfast you can pick up beats one you skip.")


def _breakfast_ideas(memory, understood):
    """Breakfast for someone who has just said what they cannot eat."""
    text = _said_so_far(understood, memory)
    banned = _no_meat_also_means_fish(_excluded(text))
    # A shortage is not a diet, but it is a food the breakfast cannot name: "im out of eggs" got
    # a list that began with eggs, and the baking-swap card.
    short = _short_of_food(text)
    if not banned and not short:
        return ANY_BREAKFAST
    banned = banned | short
    ideas = []
    for needs, idea in BREAKFAST_CHOICES:
        if needs & banned:
            continue
        ideas.append(idea(banned) if callable(idea) else idea)
        if len(ideas) == 3:
            break
    if not ideas:
        # a line that rules out everything: say what is left rather than name a food twice
        return ("A bowl of fruit and a glass of juice, or a slice of toast with jam if bread is "
                "allowed" + BREAKFAST_TAIL + _rushed(banned))
    if len(ideas) == 1:
        return ideas[0] + BREAKFAST_TAIL + _rushed(banned)
    said = ", ".join(ideas[:-1]) + (" or " if len(ideas) == 2 else ", or ") + ideas[-1]
    return said + BREAKFAST_TAIL + _rushed(banned)




# The packed lunch for someone who has said nothing about what they cannot eat. It is the
# plain entry's own text, kept word for word so the lines with no diet on them read as they
# always have; anyone with a diet gets the same answer read around it (`_lunch_ideas`).
ANY_LUNCH = ("A sandwich or wrap with something filling (cheese, tuna, ham, hummus), fruit, "
             "something crunchy and a drink is a packed lunch in five minutes; cook extra dinner "
             "and take the leftovers in a tub and it is quicker still. Keep anything with meat, "
             "fish, egg or dairy cold until you eat it.")


def _lunch_ideas(memory, understood):
    """A packed lunch for someone who has just said what they cannot eat."""
    words = understood.get("words")
    if not isinstance(words, list):
        words = " ".join(understood.get("words") or []).split()
    text = _said_so_far(understood, memory)
    banned = _no_meat_also_means_fish(_excluded(text))
    if not banned:
        return ANY_LUNCH
    # A filling is usable when none of the foods it is made of is ruled out.
    fillings = [name for name, needs in (("cheese", DAIRY), ("tuna", {"tuna"}),
                                        ("ham", {"ham"}), ("egg", EGGS),
                                        ("hummus", set()), ("avocado", set()),
                                        ("roasted vegetables", set()))
                if not (needs & banned)]
    if "gluten" in banned:
        if fillings:
            return ("For a lunch that is not a sandwich: a rice or potato salad with " +
                    ", ".join(fillings[:3]) + ", fruit and a drink. Cook extra dinner and take the "
                    "leftovers in a tub and it is quicker still. Keep it in a cool bag until lunch.")
        return ("For a lunch that is not a sandwich: cook extra dinner and take the leftovers in a "
                "tub with rice, potatoes or salad, fruit and a drink. Keep it in a cool bag until "
                "lunch.")
    if not fillings:
        return ("Cook extra dinner and take the leftovers in a tub with fruit and something crunchy: "
                "that is a packed lunch in five minutes. Keep it in a cool bag until lunch.")
    reply = ("A sandwich or wrap with " + ", ".join(fillings[:3]) + ", fruit, something crunchy and "
             "a drink is a packed lunch in five minutes. Cook extra dinner and take the leftovers "
             "in a tub and it is quicker still.")
    if banned:
        return reply + " Keep it in a cool bag until lunch."
    return reply + " Keep anything with meat, fish, egg or dairy cold until you eat it."


# What freezes, and what each thing needs: keyed by the food the line names, so "can I freeze
# milk" gets milk's answer rather than a lecture about bags. 3 months is the safe home-freezer
# limit for most things, not the taste limit.
# How long a thing keeps once it is in the freezer, which is a different number from the fridge
# days people ask about. Safe for longer than this; quality is what runs out.
FREEZER_KEEP = ("In the freezer, about 3 months for most things before the quality drops: raw "
                "meat and fish, cooked dishes, soup, stock, bread, cake, cheese and butter. A whole "
                "bird or a joint goes 6 months, blanched veg and fruit 6 to 12, and ice cream 2 to "
                "3. It stays safe long past that, just drier, so write the date on the bag. The "
                "fridge is much shorter: raw meat 1 to 2 days, cooked food 3 to 4.")


FREEZE_ANY = ("Most food freezes well for about 3 months: cool it fast, portion it into bags, press "
              "the air out and write the date on. Defrost in the fridge overnight rather than on the "
              "counter.")


HONEY_BABY = (
    "No honey at all before the first birthday: it can carry botulism spores that a baby's gut is "
    "too young to deal with, and heat does not destroy them, so cooked honey is out too. That "
    "covers honey in porridge, on a dummy or in a homemade cough remedy. From the first birthday it "
    "is fine, so a toddler or an older child can have it.")

HONEY_OLDER = (
    "From the first birthday honey is fine, so a toddler can have it in porridge or a warm drink - "
    "keep the spoon small and brush teeth afterwards, because it is sugar. The one rule is no honey "
    "at all under a year, and that includes cooked honey, because botulism spores survive heat.")


def _honey_age(memory, understood):
    """The age in the line decides which side of the first birthday the answer opens on."""
    text = understood.get("clean") or ""
    if re.search(r"\b(toddlers?|2 year old|3 year old|two year old|three year old)\b", text):
        return HONEY_OLDER
    return HONEY_BABY


_FREEZE_WORD_FORMS = ("freeze", "freezes", "freezing", "frozen", "freezer", "freezers",
                      "freezed", "freezed")
_FREEZE_POINTS_AT = ("it", "this", "that", "these", "those", "them", "the rest", "the other half",
                     "the remainder", "whats left", "what is left", "the spare", "some",
                     "any left", "any spare", "a portion", "the leftovers", "left over",
                     "the whole lot", "the remainder of it")


def _points_at_something(words):
    """True when the line says "freeze it" rather than talking about freezing in general.

    "i can read it fine but freeze when someone talks to me" is a person freezing up, and a
    pointing word in it ("it") would otherwise reach the food answers. A pointer only counts when
    it sits against the freezing word itself - "freeze it", "freezing this", "this freeze", "the
    freezer for it" - and a pointer of two or three words ("the rest", "what is left", "the other
    half") counts as a whole, because those are the words people point with.
    """
    clean = [word.strip(".,!?").replace("'", "").lower() for word in words]
    for at in range(len(clean)):
        for size in (3, 2, 1):
            if " ".join(clean[at:at + size]) not in _FREEZE_POINTS_AT:
                continue
            for step in (-1, -2, size, size + 1):
                i = at + step
                if 0 <= i < len(clean) and clean[i] in _FREEZE_WORD_FORMS:
                    return True
    return False


def _freeze_units(words):
    """Every run of the line's words worth comparing with a food name, up to three words long."""
    units = list(words)
    for size in (2, 3):
        units += [" ".join(words[i:i + size]) for i in range(len(words) - size + 1)]
    return units


def _a_freeze_fact(words):
    """The most specific food freeze fact the words carry, or None."""
    best = None
    for names, fact in FREEZE_FACTS:
        for name in names:
            for at, word in enumerate(_freeze_units(words)):
                if _same(word, name):
                    # a name that is the whole unit beats one that only sits inside it:
                    # "cream cheese" is not the cream row, however the words line up.
                    score = (word == name, len(name.split()), at)
                    if best is None or score > best[0]:
                        best = (score, fact)
    return best[1] if best else None


# A thing frozen by an app, not by a freezer: "i lost my bank card, should i freeze it first"
# is the bank's answer, and a food row that reads "freeze it" as a freezer took that turn away
# from the money card that had been giving it. The words are what can be frozen that is not
# food, and any of them in the line is enough for this row to say nothing.
_NOT_A_FREEZER = frozenset("""
    card cards account accounts subscription subscriptions membership phone credit file
    report reports score payment payments direct debit standing order
""".split())


def _names_one_food(words):
    """The one food name a line carries, or None when it carries two or more.

    "what can i cook with mince and a tin of tomatoes" names two things and is about neither of
    them: the answer for tomatoes (freeze them whole, the skins slip off) is a bad answer to
    "can i freeze the rest" about a ragù, and the plain three-month answer is a true one. Two
    names is a list, so the chat does not name a dish.
    """
    seen = set()
    for names, fact in FREEZE_FACTS:
        for name in names:
            for at, unit in enumerate(_freeze_units(words)):
                if _same(unit, name):
                    seen.add(fact)
                    break
    return next(iter(seen)) if len(seen) == 1 else None


def _the_dish_the_chat_names(memory):
    """The food the person's own last few lines are about, or None: the thing "it" points at.

    "do i need to freeze them" after a line about green beans is a question about beans, and
    "can i freeze it" after bread is bread's question. The line itself names nothing, so the
    dish has to come out of the chat, nearest line first.

    Only the person's lines count. The bot's own reply is where the wrong dish came from: after
    "i have half a bag of potatoes going soft" the reply offered cheese on the mash, and the
    next turn's "could i freeze them" was answered with how to freeze grated cheese. A reply
    also mentions the carcass making stock and the stock answer arrived for a roast chicken.
    """
    try:
        from ..memory import recent
        turns = recent(memory, 4) or ()
    except Exception:
        return None
    for turn in reversed(list(turns)):
        if not isinstance(turn, dict):
            continue
        said = turn.get("user")
        if not isinstance(said, str) or not said.strip():
            continue
        fact = _names_one_food(said.lower().split())
        if fact is not None:
            return fact
    return None


def _freeze_food(memory, understood):
    """The food the line names gets its own answer; a thing named earlier gets that one too."""
    words = understood.get("words")
    if not isinstance(words, list):
        words = " ".join(understood.get("words") or []).split()
    words = [str(word).lower() for word in words]
    if _NOT_A_FREEZER & {word.strip(".,!?\"'") for word in words}:
        # a card, an account, a subscription: someone else's answer
        return None
    fact = _a_freeze_fact(words)
    if fact is not None:
        return fact
    if not _points_at_something(words):
        # no dish in the line and nothing pointed at: this is not a freezing question about a
        # thing, so the row says nothing and a lower one gets the turn
        return None
    earlier = _the_dish_the_chat_names(memory)
    if earlier is not None:
        return earlier
    return FREEZE_ANY


SOYA = frozenset("soya soy soya bean soy bean soya sauce tofu edamame".split())
# The one sentence each family needs when it is said alongside a nut allergy: the Plenty list is
# about nuts, and the reply that answers half of a two-allergen line is the fault being fixed.
ALSO_OUT = {
    "shellfish": "And nothing with shellfish in it either: prawns, crab, lobster, mussels, squid, "
                 "and check sauces and stocks for seafood.",
    "soya": "And nothing with soya in it either: tofu, edamame, soya sauce, and check the label "
            "on bread and chocolate.",
}


def _nut_free(memory, understood):
    """A nut allergy: food that is safe, and the cake question when that is what is cooking."""
    # This card is a nut-free list, and an allergy said in the same breath used to go unanswered:
    # "peanuts and shellfish" got the list and not a word about the shellfish. Each other family
    # gets the one sentence that names what to keep out of it.
    banned = avoids(memory)
    if (GLUTEN | EGGS) & banned:
        # The list itself names pasta and eggs, so for a coeliac or an egg allergy it is the wrong
        # list and the turn goes to whoever answers that.
        return None
    also = [ALSO_OUT[name] for name in ("shellfish",) if FAMILIES[name] & banned]
    if SOYA & banned:
        also.append(ALSO_OUT["soya"])
    turns = memory.get("turns")
    recent = ""
    if isinstance(turns, list):
        recent = " ".join(str(turn.get("user") or "") for turn in turns[-2:]
                          if isinstance(turn, dict)).lower()
    if "cake" in recent or "bake" in recent or "birthday" in recent:
        return ("Then go for a plain chocolate sponge: cocoa, flour, eggs, butter and sugar, no "
                "nuts. Check the chocolate, the icing sugar and any sprinkles for 'may contain "
                "nuts', and keep the tin and worktop clean if the allergy is serious.")
    return ("Plenty: meat, fish, eggs, rice, pasta, potatoes and plain fruit and veg are all "
            "nut-free, so pasta with tomato sauce or roast chicken and potatoes works. Check the "
            "labels on chocolate, muesli, pesto and satay, and anything marked 'may contain "
            "nuts'." + (" " + " ".join(also) if also else ""))


# --- missing ingredients, and what stands in for them ---------------------
# "What can I use instead of X" is one of the most asked kitchen questions. The words below are
# ways of asking for a stand-in rather than for a dish, and the pantry table reads a line naming
# two ingredients as a "what can I make" question, so it has to be held back for these (see
# SUBSTITUTE_PHRASES in meal()).
# The other half of "what can i use instead of": "i have run out of", "i am out of" and "no
# butter left" are the same question, and they were reaching the swap entries only when the line
# also carried one of the ask words above.
# "no butter left" is "none left", not "left": a bare "left" also reads a quantity question
# ("how much yeast is left in a sachet") as the thing having run out.
_HAVE_NONE = ("havent any", "haven't any", "have got none", "have none", "has none", "got none",
              "there is no ", "there's no ", "there are no ", "none in the house",
              "none in the cupboard", "none at home", "none left at home",
              "nothing in the house", "nothing in the cupboard", "nothing in the fridge",
              "theres none", "there's none",
              "have no egg", "have no eggs", "have no milk", "have no butter", "have no yeast",
              "have no cream", "have no buttermilk", "have no cornflour", "have no flour",
              "have no plain flour", "have no baking powder", "have no sugar", "have no cheese",
              "have no rice", "have no onions", "have no bread")
_OUT_ASK = ("out of", "none left", "nothing left", "empty", "what do i do", "what do i use") \
    + _HAVE_NONE

# The bake decides which of the three swaps matters: pancakes need no egg at all, a scone is a
# rubbing-in job, and a brownie is all fat and egg, so one vegan answer for all of them was telling
# a pancake line about a cake.
def _vegan_bake(memory, understood):
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = {_fold(word) for word in words}
    # the folded forms, so "brownies" and "cookies" are the words they are
    if folded & {_fold(one) for one in ("pancake", "pancakes", "crepe", "crepes", "waffle",
                                        "waffles", "drop scone")}:
        return ("Pancakes need no egg at all: 100g of plain flour, a teaspoon of baking powder, a "
                "pinch of salt and 300ml of unsweetened soya or oat milk, whisked and rested 20 "
                "minutes, then cooked in a little oil. The first one always fails, so make it the "
                "cook's. For thicker American ones, add a tablespoon of oil and a teaspoon of "
                "sugar.")
    # A scone and a pastry case are both a rubbing-in job, but they are not the same job: a scone
    # is raised with self-raising flour and cut into rounds, and a tart case is plain flour, cold
    # fat and a rest in the fridge. One answer for both was giving a pastry question a scone recipe.
    if folded & {_fold(one) for one in ("scone", "scones", "drop scone", "drop scones")}:
        return ("Rub 50g of a hard vegan block margarine, or 40ml of neutral oil, into 225g of "
                "self-raising flour, then bring it together with about 120ml of unsweetened soya "
                "milk and a squeeze of lemon. Pat it out, cut the scones and bake at 220C for 12 "
                "to 15 minutes. The block margarine, not a tub spread, is what makes it short.")
    if folded & {_fold(one) for one in ("pastry", "shortcrust", "shortcrust pastry", "pie",
                                        "pie crust", "tart", "tarts", "tart case", "flan",
                                        "quiche", "quiche case")}:
        return ("Vegan shortcrust is the same weights with the fat swapped: 225g plain flour, a "
                "pinch of salt and 100g of a hard vegan block margarine (or 90ml of neutral oil), "
                "rubbed in until it looks like breadcrumbs, then cold water a spoon at a time until "
                "it just comes together. Rest it 30 minutes in the fridge, roll it thin on a floured "
                "board, and blind bake at 190C (170C fan) for 15 minutes for a tart or quiche case. "
                "Brush the top with plant milk rather than egg and it browns just as well.")
    if folded & {_fold(one) for one in ("crumble", "crumbles", "fruit crumble", "cobbler")}:
        return ("Swap the butter and nothing else changes: rub 100g of a hard vegan block "
                "margarine into 200g plain flour with 75g sugar until it looks like breadcrumbs, "
                "scatter it over the fruit and bake at 190C (170C fan) for 35 to 40 minutes, until "
                "the fruit bubbles at the edges and the top is golden.")
    if folded & {_fold(one) for one in ("biscuit", "biscuits", "cookie", "cookies",
                                        "shortbread")}:
        return ("Biscuits are the easiest bake to make vegan: a hard block margarine in place of "
                "the butter at the same weight, and a tablespoon of plant milk if the dough will "
                "not come together. No egg and no raising agent needed, so nothing else changes, "
                "and they keep a day or two less.")
    # A flapjack is oats held together with fat and syrup: there is no egg to replace, so the
    # butter is the only swap, and it was being told "for brownies, two flax eggs...".
    if folded & {_fold(one) for one in ("flapjack", "flapjacks", "oat bar", "oat bars",
                                        "granola bar", "granola bars")}:
        return ("A flapjack needs no egg, so the only swap is the butter: 150g of a hard vegan "
                "block margarine or 120ml of neutral oil with 120g of golden syrup is the sticky "
                "part. Melt them together, stir in 300g of porridge oats, press it into a lined "
                "20cm tin and bake at 180C (160C fan) for 20 to 25 minutes. Let it go completely "
                "cold in the tin or it will crumble when you cut it.")
    # Bread is the one bake with no egg and often no fat at all, so "vegan bread" was being told
    # about flax eggs in a cake. An enriched loaf - banana bread, brioche, a milk loaf - is a cake
    # in a loaf tin and keeps the swaps above.
    if (folded & {_fold(one) for one in ("bread", "loaf", "loaves", "roll", "rolls", "baguette",
                                         "focaccia", "pizza", "pizza dough", "flatbread", "naan")}
            and not folded & {_fold(one) for one in ("banana", "carrot", "courgette", "zucchini",
                                                     "apple", "date", "pumpkin", "lemon", "fruit",
                                                     "soda", "cake", "brioche", "challah")}):
        return ("Ordinary bread is vegan already: flour, water, yeast and salt, with oil or a hard "
                "block margarine where the recipe wants a fat, and sugar feeds the yeast without "
                "leaving any behind. Only an enriched loaf needs a swap - oil for the butter, plant "
                "milk for the milk, and golden syrup for the honey. Check a bought loaf, though: "
                "milk powder and dried egg turn up in cheap sliced bread and in brioche.")
    if folded & {_fold(one) for one in ("brownie", "brownies", "blondie", "blondies")}:
        return ("For brownies, two flax eggs do the job: a tablespoon of ground flaxseed and "
                "three of water each, left five minutes to go gluey. Use an oil-based or vegan "
                "block margarine for the butter and keep the oven 10C lower, because brownies are "
                "meant to come out fudgy and the flax makes them catch sooner.")
    return ("A cake takes three swaps: 60g of yoghurt or half a mashed banana, or a flax egg (a "
            "tablespoon of ground flaxseed and three of water, left five minutes), for each egg; "
            "unsweetened soya or oat milk for the milk; and a block margarine or 80g of neutral oil "
            "for every 100g of butter. Add an extra half teaspoon of baking powder, because the egg "
            "was doing some of the lifting, and give it five minutes longer in the oven. Soya milk "
            "browns best, and a sponge made this way keeps a day less.")


# A line that asks for a bake with no egg, no butter or no milk in it. Every vegan variant below is
# the same question - "how do i make vegan pastry", "a dairy free sponge", "a cake with no eggs" -
# and the recipes in BAKES all use butter or egg, so the dairy one has to stand down for these.
_VEGAN_ASK = ("vegan", "vegans", "plant based", "plant-based", "dairy free", "dairy-free",
              "dairyfree", "egg free", "egg-free", "eggless", "no egg", "no eggs", "no butter",
              "without butter", "no milk", "milk free", "milk-free")


def _asks_vegan(folded):
    """True when the line asks for a bake with no dairy or no egg in it."""
    said = " ".join(folded)
    return any(phrase in said for phrase in _VEGAN_ASK)


# "is oil a good replacement for butter" wanted the same answer as "what can i use instead of
# butter" and got a shrug, because nothing in this gate was the word people write.
_SWAP_ASK = ("instead", "substitute", "swap", "replace", "replacement", "alternative",
             "without",
             "what can i use", "what do i use", "what should i use", "what else can i use",
             "ran out", "run out", "havent got", "haven't got", "dont have", "don't have",
             # A shortage is the same question as a swap: "im out of butter" wants what stands
             # in for butter. The subject is in the phrase because "out of" alone is the oven and
             # the fridge ("how long can butter stay out of the fridge" is a keeping line).
             "im out of", "i'm out of", "were out of", "we're out of", "are out of",
             "im all out",
             "i'm all out", "out of stock of", "none of", "none left", "nothing left",
             "no longer have",
             # A statement of having none is the same question as a swap: the foods it may
             # name are listed in _HAVE_NONE above, off the bare verb.
             *_HAVE_NONE,
             # "egg free cake recipe" and "a cake with no eggs" are the same question as
             # "what can i use instead of eggs", and the scrambled-eggs entry was taking the first.
             "egg free", "egg-free", "eggless", "no egg", "no eggs")

# A step that swaps one ingredient for another is not a "what can I cook" line, whatever else it
# names: "can i use milk instead of cream" is about the cream, not about milk.
SUBSTITUTE_PHRASES = ("instead of", "in place of", "substitute", "swap ", "what can i use",
                      "what do i use", "ran out of", "run out of", "havent got", "haven't got",
                      "dont have", "don't have")

# A dish entry answers "what can I make or cook with this". A line asking how long it keeps, or
# whether it is still safe, is a storage question and belongs to the storage entries, so every dish
# entry stays out of it.
KEEPING = ("keep", "keeps", "keeping", "shelf life", "shelf-life", "last", "lasts",
           "safe", "still ok", "ok to eat",
           "gone off", "went off", "go off", "goes off", "going off", "off", "left out",
           "use by", "days", "how long",
           "reheat", "reheating", "warmed up")

# The words that make "how long" a cooking question rather than a keeping one. A storage entry
# that keys on "how long" has to stay out of these.
COOK_VERBS = ("boil", "boiling", "boiled", "roast", "roasting", "roasted", "steam", "steaming",
              "steamed", "fry", "frying", "fried", "bake", "baking", "baked", "microwave",
              "grill", "grilling", "grilled", "parboil", "poach", "poaching", "simmer",
              "simmering", "air fry", "air-fry", "in the oven", "on the hob", "blanch")

# How long a thing is stored, as opposed to how long it cooks: "how long does lasagne keep in the
# fridge" must not get the oven time. "how long" is left out on purpose, because the oven lines
# are asked that way.
STORAGE = ("keep", "keeps", "keeping", "shelf life", "shelf-life", "fridge", "freezer",
           "freeze", "frozen", "refreeze",
           "refreezing", "reheat", "reheating", "reheated", "last", "lasts",
           "left out", "use by", "gone off", "go off", "goes off", "going off",
           "still ok", "ok to eat", "safe")


# "Can I use X instead of Y" is the other way round from the swaps above, and sometimes the
# answer is no: cornflour will not raise a cake and oil will not make pastry. So the pair gets
# its own verdict, keyed on both ingredients, with the swap phrase required (ask=) so a recipe
# that merely names the two ("cream sauce with yoghurt") is left alone. Read as (what is
# offered, what it replaces).
# Calories in an ordinary portion, one row per food people ask about: (the words people use,
# the subject of the sentence, the portion, the number). A portion, not a brand - "a banana" is
# a medium one, "a slice of bread" a normal supermarket slice - so the reply reads as a sentence.

# What an ordinary portion holds, beside the calories: one row per food, with the grams of
# protein, carbohydrate, sugar, fat and fibre in the portion the row names. One table, so "how
# much protein in an egg", "how many carbs in a banana" and "how much fibre in porridge" are the
# same question about a different column. The values are ordinary supermarket food, cooked where
# it is a food that gets cooked, and rounded to the nearest gram.

# The columns the table has: the words people use for each, and how to say it in the reply.
NUTRIENT_COLUMNS = {
    "protein": ("protein", "protein"),
    "carbs": ("carbs", "carbohydrate"),
    "sugar": ("sugar", "sugar"),
    "fat": ("fat", "fat"),
    "fibre": ("fibre", "fibre"),
    "iron": ("mg", "iron"),
    "calcium": ("mg", "calcium"),
    "potassium": ("mg", "potassium"),
    "salt": ("g", "salt"),
}

# The one sentence that makes a figure useful, for the nutrients where a person has no feel for
# the number: the daily target, so the figure lands somewhere instead of being read and dropped.
NUTRIENT_CONTEXT = {
    "iron": "Women need about 15mg a day and men about 9mg, and the iron in plants and grains "
            "is taken up better with something containing vitamin C.",
    "calcium": "Adults need about 700mg a day.",
    "potassium": "The target is about 3,500mg a day.",
    "salt": "The daily limit is 6g, and bread, cheese and cured meat are where most of it hides.",
}

# The minerals the table carries, per portion. A row without the column has no figure for that
# nutrient, and the line passes rather than being told there is none of it.
_MINERALS = ("iron", "calcium", "potassium", "salt")

# Which column a line asks about. Longer words first, so "carbohydrate" is not read as "carbs"
# and "sugar free" is read as a sugar question rather than a fat one.
_NUTRIENT_WORDS = (
    ("carbohydrates", "carbs"), ("carbohydrate", "carbs"), ("carbs", "carbs"), ("carb", "carbs"),
    ("protein", "protein"), ("proteins", "protein"),
    ("saturated fat", "fat"), ("saturates", "fat"), ("fat", "fat"), ("fats", "fat"),
    ("sugar", "sugar"), ("sugars", "sugar"),
    ("fibre", "fibre"), ("fiber", "fibre"),
    # The minerals are rare words, so they can be key words: the food still has to be in the
    # table for the entry to answer, which is what keeps "how much iron in a shirt" the ironing
    # question and "how much salt should i eat" a daily-limit question.
    ("iron", "iron"), ("calcium", "calcium"), ("potassium", "potassium"),
    ("salt", "salt"), ("salty", "salt"),
)

# The words that ask what is *in* a food rather than how to cook it. A nutrient column is a
# different question about the same food, so an egg asked for its portion must not be told how
# long to boil: "boiled egg calories" and "boiled egg protein" were both the six-to-ten-minute
# answer, because the timing entry matches "egg" and "boiled" and the portion entries match lower.
_NUTRIENT_ASK_WORDS = (tuple(word for word, _column in _NUTRIENT_WORDS)
                       + ("calorie", "calories", "cals", "kcal", "kilocalories", "nutrition"))

# A food named as part of a dish is a different food: "banana bread" is not a banana, and a
# curry with chicken in it is not a portion of chicken. The table counts a food on its own, so a
# dish word, another food from the table in the same line, or a food joined on with "and" or
# "with" all pass to whatever answers next.
_NUTRIENT_DISH = ("bread", "cake", "pie", "tart", "muffin", "sauce", "soup", "sandwich", "wrap",
                  "curry", "salad", "smoothie", "juice", "pudding", "jam", "chips", "butter",
                  "cheese", "cream", "biscuit", "cereal", "porridge", "pasta", "rice", "pizza",
                  "stew", "casserole", "roast", "bake", "baked", "fried", "milkshake",
                  "flapjack", "brownie", "cookie", "pancake", "waffle", "toast", "milk", "sugar",
                  "flour", "crisps", "chocolate", "yoghurt", "yogurt", "egg", "nuts", "peanut",
                  "roll", "rolls", "burger", "burgers", "bun", "buns", "pastry", "puff")
_NUTRIENT_JOIN = ("and", "with", "plus")


# How many of the food the line names: "two eggs" is twice an egg, and "3 eggs" is the same
# question typed in figures. A count of half a is half.
_COUNT_WORDS = {"one": 1, "1": 1, "two": 2, "2": 2, "three": 3, "3": 3, "four": 4, "4": 4,
                "five": 5, "5": 5, "six": 6, "6": 6, "seven": 7, "7": 7, "eight": 8, "8": 8,
                "nine": 9, "9": 9, "ten": 10, "10": 10}


def _plurals(word):
    """A food word with an s on the end, near enough for "two eggs" and "two slices"."""
    if not word.isalpha() or word.endswith("s"):
        return word
    if word.endswith(("ch", "sh", "ss", "x", "z")):
        return word + "es"
    if word in ("potato", "tomato", "hero"):
        return word + "es"
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def _portion_count(words, index):
    """How many of them the line names, from the words just before the food."""
    back = words[max(0, index - 4):index]
    said = " ".join(back)
    if said.endswith("a couple of") or said.endswith("couple of"):
        return 2
    if said.endswith("a few"):
        return 3
    if said.endswith("half a") or said.endswith("half an"):
        return 0.5
    for word in reversed(back):
        if word in _COUNT_WORDS:
            return _COUNT_WORDS[word]
    return 1


def _squashed(word):
    """The word with every run of one letter cut to one, so a doubled letter stops mattering."""
    return re.sub(r"(.)\1+", r"\1", word)


def _one_letter_apart(short, long):
    """Whether the shorter word is the longer one with a single letter taken out."""
    index = 0
    while index < len(short) and short[index] == long[index]:
        index += 1
    return short[index:] == long[index + 1:]


def _the_food_named_by_a_slip(words, table):
    """The one food in the table a word of the line is a slip of, with the number of portions.

    A name followed by a dish word ("a bananna cake") is an ingredient of a dish, and a name
    after a joining word ("chicken and bananna") is one of two foods: neither is this table's.
    """
    for index, word in enumerate(words):
        name = _a_food_word_misspelt(word, table)
        if name is None:
            continue
        before = words[index - 1] if index else None
        after = words[index + 1] if index + 1 < len(words) else None
        if after and (after in _NUTRIENT_DISH or after in _NUTRIENT_JOIN):
            return None
        if before and before in _NUTRIENT_JOIN:
            return None
        return name, _portion_count(words, index)
    return None


def _a_food_word_misspelt(word, names):
    """The name this word is a slip of, or None.

    Food words are the ones people mistype most, and the table is keyed on the dictionary
    spelling: "how much protein in a bananna", "in brocolli" and "in a avacado" all reached the
    punt on main while the same question spelled right was answered with the figure. The
    tolerance is deliberately mean, because a wrong food is a wrong number: the word has to
    start and end like the name, be five letters or more, and be the name with a letter doubled, a
    letter swapped for another, or one letter too many or too few.
    """
    if len(word) < 5 or not word.isalpha():
        return None
    if word in names:
        return None
    squashed = _squashed(word)
    for name in names:
        if " " in name or len(name) < 5 or name[0] != word[0]:
            continue
        if len(name) == len(word):
            if squashed == _squashed(name):
                return name
            # "rich" is one letter off "rice", and "iron rich foods" is not a portion of rice:
            # a swapped letter keeps the last one, so the two words have to end alike as well.
            if name[-1] == word[-1] and sum(one != other for one, other in zip(word, name)) == 1:
                return name
        elif abs(len(name) - len(word)) == 1 and name[-1] == word[-1]:
            shorter, longer = sorted((word, name), key=len)
            if _one_letter_apart(shorter, longer):
                return name
    return None


def _nutrient_food(clean, table):
    """The one food from the table the line names a portion of, or None.

    The longest name wins ("sweet potato" over "potato"), and a line that names two foods, or a
    dish made from one, gets nothing: the table has no portion for a curry.
    """
    matches = [food for food in table
               if re.search(r"(?<![a-z0-9])" + re.escape(food) + r"s?(?![a-z0-9])", clean)]
    words = re.findall(r"[a-z0-9']+", clean)
    if not matches:
        # Nothing is spelled the way the table spells it, so the line may still be about a food
        # with a slip in its name: one word of it one letter away from a name in the table.
        return _the_food_named_by_a_slip(words, table)
    best = max(matches, key=len)
    # "milk" inside "a glass of milk" is the same portion, and so is "potato" inside "sweet
    # potato"; a food that is not part of the winner is a second food, and the table has no
    # portion for two of them together.
    # ...and "biscuits" beside "a digestive biscuit" is that same one food, so the plural of a
    # name counts as part of the winner rather than as a second food.
    if any(food not in best and food.rstrip("s") not in best
           and _plurals(food) not in best for food in matches):
        return None
    parts = best.split()
    for index in range(len(words) - len(parts) + 1):
        chunk = words[index:index + len(parts)]
        if chunk[:-1] != parts[:-1]:
            continue
        # "two eggs" is the egg row: the last word of the name can carry the plural.
        if chunk[-1] != parts[-1] and chunk[-1] != _plurals(parts[-1]):
            continue
        before = words[index - 1] if index else None
        after = words[index + len(parts)] if index + len(parts) < len(words) else None
        if after and (after in _NUTRIENT_DISH or after in _NUTRIENT_JOIN):
            return None
        if before and before in _NUTRIENT_JOIN:
            return None
        return best, _portion_count(words, index)
    return None


def _nutrient_asked(clean):
    """The column of the table the line asks about, or None."""
    for word, column in _NUTRIENT_WORDS:
        if re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean):
            return column
    return None


# The words for a share of a day's protein, biggest first: an adult needs about 50g, so a
# chicken thigh is a half and an egg is a tenth. A whole takeaway pizza is more protein than
# anyone needs in a day, and "about half of a day's" would have been a wrong way to say it;
# the shares stop short of a day and the reply says so in words instead.
_PROTEIN_SHARES = ((0.8, "most"), (0.5, "half"), (0.3, "a third"), (0.22, "a quarter"),
                   (0.18, "a fifth"), (0.08, "a tenth"))


def _grams(value):
    """A number of grams as a person would say it."""
    if value <= 0:
        return None
    if value < 1:
        return "under a gram"
    if float(value) == int(value):
        return "%d" % int(value)
    return ("%.1f" % value).rstrip("0").rstrip(".")


# The amount a line can name is either a count of the row's own thing ("two eggs", which
# _portion_count reads) or a weight ("100g of chicken", "a pint of milk"). The table is written
# one portion at a time, so a line that names its own weight has to be worked out from that
# portion: answering "100g of chicken" with the figure for 150g is a wrong number, not a
# rounding. A weight the row cannot be measured in (a "medium one") is left alone and the
# portion's own figure is used.
_WEIGHT_WORDS = (("kilograms?|kg", 1000.0, "g"), ("grammes?|grams?|g", 1.0, "g"),
                 ("millilitres?|milliliters?|ml", 1.0, "ml"), ("centilitres?|cl", 10.0, "ml"),
                 ("litres?|liters?|l", 1000.0, "ml"), ("pints?", 568.0, "ml"))

# "A bowl of cereal", "a plate of chips": an amount this table cannot work out from its portion.
# No figure is better than the figure for a different amount.
_AMOUNT_ASKED = re.compile(r"\d|\b(?:half|quarter|dozen|pints?|litres?|liters?|bowls?|plates?|"
                           r"glasses?|mugs?|cups?|slices?|pieces?|portions?|servings?|tins?|"
                           r"spoons?|tablespoons?|teaspoons?)\b")


def _portion_size(portion):
    """The figure a row is written for, and its unit: "a 200ml glass" -> (200.0, "ml")."""
    found = re.search(r"(\d+(?:\.\d+)?)\s*(g|ml)\b", str(portion).lower())
    return (float(found.group(1)), found.group(2)) if found else None


def _weight_in_the_line(clean, portion):
    """The weight the line asks about as a multiple of the row's portion, and the words used."""
    base = _portion_size(portion)
    if base is None:
        return None
    for pattern, scale, unit in _WEIGHT_WORDS:
        found = re.search(r"(\d+(?:\.\d+)?)\s*(?:" + pattern + r")\b", clean)
        if found and base[1] == unit:
            return float(found.group(1)) * scale / base[0], found.group(0)
    if base[1] == "ml":
        found = re.search(r"\b(half a pint|a pint|one pint)\b", clean)
        if found:
            many = 0.5 if found.group(1).startswith("half") else 1.0
            return many * 568.0 / base[0], found.group(1)
    return None


def _figure(value):
    """A figure the way a person says it: 2.7, 30, 900."""
    if value >= 10:
        return "%d" % int(round(value))
    return ("%.1f" % value).rstrip("0").rstrip(".")


def _nutrients(memory, understood):
    """What an ordinary portion of the food the line names holds of the nutrient it asks about."""
    clean = (understood.get("clean") or "").lower()
    if not clean:
        return None
    # A nutrient word or a food word typed a letter short gets nowhere, and the reading already
    # repairs it - in `plain`, "the same words with each one repaired in place", which nothing in
    # the knowledge base reads. "how much protien in chicken" was a hedge with the figure one
    # repaired word away. Each word is looked for in the line as typed first, so a line spelt
    # right reads exactly as it did, and the repair is only consulted when that found nothing.
    # The amount stays the line as typed: `plain` says the digits out as words.
    plain = (understood.get("plain") or "").lower()
    if plain == clean:
        plain = ""
    column = _nutrient_asked(clean)
    read = clean
    if column is None and plain:
        column = _nutrient_asked(plain)
        read = plain if column is not None else clean
    if column is None:
        return None
    found = _nutrient_food(read, FOOD_NUTRIENTS)
    if found is None and plain:
        found = _nutrient_food(plain if read == clean else clean, FOOD_NUTRIENTS)
    if found is None:
        return None
    food, count = found
    subject, portion, numbers = FOOD_NUTRIENTS[food]
    if column not in numbers:
        # the food is in the table but not for this nutrient: a pass, not "none of it"
        return None
    value = numbers[column] * count
    # the amount the line names, when the row can be measured against it
    scaled, said_amount = None, None
    if count == 1:
        weighed = _weight_in_the_line(clean, portion)
        if weighed is not None:
            scaled, said_amount = weighed
            if abs(scaled - 1.0) < 0.01:
                scaled = None
        elif _portion_size(portion) is None:
            # "a bowl of cereal" for a row written as "a medium one": an amount this table cannot
            # work out, and no figure is better than the figure for a different amount. An amount
            # word that is the row's own thing ("a slice of bread" for a slice) is not an amount.
            for word in _AMOUNT_ASKED.findall(clean):
                if not word:
                    return None
                if word in portion.lower() or _plurals(word) in portion.lower():
                    continue
                if word in subject.lower() or _plurals(word) in subject.lower():
                    continue
                return None
    said = subject[:1].upper() + subject[1:]
    if count > 1:
        # "two eggs" is twice an egg, so the portion is the count and the subject goes plural.
        # The plural goes on the noun that is being counted, not always the first word: "two
        # chocolate bars", not "two chocolates bar", and "two digestive biscuits". In "a slice of
        # bread" the counted noun is the one before "of".
        pieces = said.split()
        if pieces[0] in ("A", "An"):
            pieces = pieces[1:]
        head = pieces.index("of") - 1 if "of" in pieces else len(pieces) - 1
        pieces[head] = _plurals(pieces[head])
        said = ("%g " % count if count != int(count) else
                {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight",
                 9: "Nine", 10: "Ten"}.get(int(count), str(int(count)))) + " " + " ".join(pieces)
        subject = said
        portion = ""
    name = NUTRIENT_COLUMNS[column][1]
    unit = "mg" if column in ("iron", "calcium", "potassium") else "g"
    plural = count > 1 or food in _CALORIE_PLURAL or subject[:2] not in ("a ", "an", "A ", "An ")
    if scaled:
        # the line asked for its own weight, so that is the subject: "100g of chicken has ..."
        said = said_amount[:1].upper() + said_amount[1:]
        if food not in said.lower():
            said += " of " + food
        value *= scaled
    amount = _figure(value) if value else None
    if amount is None:
        sentence = "%s %s no %s to speak of" % (said, ("have" if plural else "has"), name)
    else:
        sentence = ("%s %s about %s%s of %s" % (said, ("have" if plural else "has"), amount,
                                                unit, name))
    if portion and portion != "one" and not scaled and portion.lower() not in said.lower():
        sentence += " (%s)" % portion
    sentence += "."
    if column == "protein" and value:
        if value >= 50:
            sentence += " That is more protein than an adult needs in a day."
        else:
            for share, word in _PROTEIN_SHARES:
                if value / 50.0 >= share:
                    # "most of a day's protein" is said without a hedge on the number
                    hedge = "" if word == "most" else "about "
                    sentence += (" That is %s%s of a day's protein for an adult."
                                 % (hedge, word))
                    break
    if column in NUTRIENT_CONTEXT:
        sentence += " " + NUTRIENT_CONTEXT[column]
    return sentence

# Two foods on one plate are not two portions: "how many calories in chicken and chips" is the
# meal, and answering with the chips alone (350) or passing on the line is both worse than the
# number for the plate. The longest match in the line wins, so these come before the single foods.

# The plurals, which take "are" rather than "is".
_CALORIE_PLURAL = ("strawberries", "grapes", "chips", "crisps", "peanuts")

# A pizza base is not a pizza: the dough, a base and a homemade one are the ingredients of the
# dish rather than the dish, and the whole-dish rows above have no number for them.
_CALORIE_NOT_A_DISH = ("dough", "base", "bases", "recipe", "homemade", "home made")

# Which line asks about the calories in a named food: the food has to be there, and the ask
# has to be about what is in it.
CALORIE_ASKS = ("calorie", "calories", "cals", "kcal", "kilocalories",
                "how many calories")

# The foods whose own entries already carry a calorie figure, which answer better than a table.
_CALORIE_OWN = ("chicken breast", "chicken breasts")

# A food named as part of a dish is a different food: "banana bread" is not a banana, and a
# sandwich with cheese and tomato in it is neither, so the table (which counts a food on its own)
# has nothing to say about it. A dish word after the food, another food from the table in the same
# line, or a food joined to something with "and" or "with", all pass instead of guessing.
_CALORIE_DISH = ("bread", "cake", "pie", "tart", "muffin", "sauce", "soup", "sandwich", "wrap",
                 "curry", "salad", "smoothie", "juice", "pudding", "jam", "crisps", "chips",
                 "butter", "cheese", "cream", "biscuit", "cereal", "porridge", "pasta", "rice",
                 "pizza", "stew", "casserole", "roast", "bake", "baked", "fried", "milkshake",
                 "flapjack", "brownie", "cookie", "pancake", "waffle", "toast", "milk", "sugar",
                 # "a sausage roll is not a sausage" (nor is a turkey burger a portion of
                 # turkey, or a ham roll two slices of ham): the word after the food decides.
                 "roll", "rolls", "burger", "burgers", "bun", "buns", "pastry", "puff")
_CALORIE_JOIN = ("and", "with", "plus")


def _names_a_food(line):
    """True when a word of the line is a food one of the calorie and nutrient tables holds."""
    lowered = line.lower()
    for table in (FOOD_CALORIES, FOOD_CALORIE_MEALS, FOOD_NUTRIENTS):
        for name in table:
            if name and name in lowered:
                return True
    return False


def _calories(memory, understood):
    """The calories in the food the line names, from FOOD_CALORIES."""
    clean = understood.get("clean") or ""
    # The same repair the nutrient reader uses, made once for the whole line: when no food the
    # tables hold is named in the line as typed, the line with its words repaired is read
    # instead. "how many calories in a bananna" is a hedge with the figure one repaired word
    # away. A line that names a food already reads exactly as it did.
    plain = understood.get("plain") or ""
    if plain and plain != clean and not _names_a_food(clean):
        clean = plain
    if not any(word in clean for word in CALORIE_ASKS):
        return None
    if any(food in clean for food in _CALORIE_OWN):
        return None
    # Read as whole words: "dough" inside "sourdough" turned the sourdough slice down, and the
    # list is of dish words, not of letter runs.
    if any(re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", clean)
           for word in _CALORIE_NOT_A_DISH):
        return None
    words = re.findall(r"[a-z0-9']+", clean)

    def _part_of_a_dish(name):
        """True when the line goes on to name a dish after this one: "chicken soup", "coffee cake".

        The meal table is matched before the ingredient table's own check, so a compound it does
        not hold landed on its first word and gave a confident number for a food nobody asked
        about: "how many calories in chicken soup" was a portion of roast chicken, and "coffee
        cake" was a mug of white coffee. A dish word after the name means this name is an
        ingredient of the dish, so the next candidate is the one to read.
        """
        tail = name.split()[-1]
        for i, word in enumerate(words):
            if word == tail:
                after = words[i + 1] if i + 1 < len(words) else None
                return after in _CALORIE_DISH
        return False

    meal = None
    for dish in sorted(FOOD_CALORIE_MEALS, key=len, reverse=True):
        if _part_of_a_dish(dish):
            continue
        if re.search(r"(?<![a-z0-9])" + re.escape(dish) + r"(?![a-z0-9])", clean):
            meal = dish
            break
    if meal:
        subject, portion, count = FOOD_CALORIE_MEALS[meal]
        said = subject[:1].upper() + subject[1:]
        return f"{said} is about {count} calories ({portion})."
    matches = [food for food in FOOD_CALORIES
               if re.search(r"(?<![a-z0-9])" + re.escape(food) + r"s?(?![a-z0-9])", clean)]
    if not matches:
        # "how many calories in a bananna" is the same slip the nutrient reader now reads: the
        # figure is in the table and the line only has one letter wrong.
        slipped = _the_food_named_by_a_slip(words, FOOD_CALORIES)
        if slipped is None:
            return None
        matches = [slipped[0]]
    best = max(matches, key=len)
    # another food from the table in the same line: "chicken and chips" is not a portion of
    # chips. A name inside the winner is the same portion - "milk" in "a glass of milk" - so the
    # table can carry the short name beside the portioned one.
    if any(food not in best for food in matches):
        return None
    head, tail = best.split()[0], best.split()[-1]
    before = after = None
    for i, word in enumerate(words):
        if word == tail:
            after = words[i + 1] if i + 1 < len(words) else None
            back = i - len(best.split()) + 1
            before = words[back - 1] if back >= 1 else None
    if after and (after in _CALORIE_DISH or after in _CALORIE_JOIN):
        return None
    if before and before in _CALORIE_JOIN:
        return None
    subject, portion, count = FOOD_CALORIES[best]
    said = subject[:1].upper() + subject[1:]
    # "a packet of crisps" is one thing, so the subject decides the verb, not the count.
    verb = "are" if best in _CALORIE_PLURAL and subject[:2] not in ("a ", "an") else "is"
    return f"{said} {verb} about {count} calories ({portion})."


# "How do I make a cake gluten free" and "can i make bread without gluten" were a shrug and a
# hedge on main, and "how do i make gluten free pastry" got the plain wheat shortcrust - gluten,
# to the person who asked for none. Making a dish without gluten is a question about the dish,
# not about one ingredient, because a blend behaves differently from flour: it needs something to
# hold it and it needs a rest. One answer for the bakes, one for the pastry, one for bread, which
# is the one to buy.
GLUTEN_FREE_ASKS = ("gluten free", "gluten-free", "glutenfree", "without gluten", "no gluten",
                    "free from gluten", "wheat free", "wheat-free", "without wheat", "no wheat",
                    "gluten allergy", "coeliacs", "coeliac", "contain gluten",
                    "contains gluten",
                    # the two things people cut out at once are one ask: "a gluten and dairy free
                    # cake" has no "gluten free" in it, so the plain phrase never matched it and the
                    # dairy answer took the line
                    "gluten and dairy free", "dairy and gluten free", "gluten and egg free",
                    "egg and gluten free", "gluten and dairy-free", "dairy-free and gluten-free")

# The dish is the question, so one of these has to be in the line as well: "im gluten free, what
# can i eat" is a meal-ideas line with another answer, and a roux or a sauce is made by its own
# entry (the plain flour method is the right method for a roux, badly wrong though it is here).
GLUTEN_FREE_DISHES = ("make", "making", "made", "bake", "baking", "baked", "cook", "cooking",
                      "recipe", "version", "instead", "cake", "cakes", "sponge", "brownie",
                      "brownies", "cookie", "cookies", "muffin", "muffins", "biscuit",
                      "biscuits", "bread", "loaf", "loaves", "roll", "rolls", "pastry",
                      "shortcrust", "scone", "scones", "pancake", "pancakes", "batter",
                      "flour", "pasta", "spaghetti", "noodles", "macaroni", "lasagne",
                      "how do i", "can i", "how can i")

# The dishes and diets a blend would ruin: a sauce, a gravy and a porridge are made by their own
# entries, the Yorkshire tin answer keeps the hot-fat method, and a coeliac question is about
# reading labels rather than about a bake.
_GLUTEN_FREE_SKIP = ("gravy", "porridge", "sauce", "soup", "curry", "stew", "casserole", "stock",
                     "marinade", "dressing", "coating", "roux", "thicken", "thickening",
                     "yorkshire", "shortbread", "beer", "lager", "ale", "cider", "wine", "what can i eat", "what can i cook",
                     "what should i eat", "what can i have", "meal", "meals", "dinner", "lunch",
                     "snack", "ideas", "what to eat", "taste", "tastes", "tasting", "healthier",
                     "better for you", "good for you", "worth it", "is it bad", "lose weight",
                     # "how do i know if i have coeliac" reached this row on "how do i" alone and
                     # was told how a bake changes: a question about the condition, and about
                     # being tested for it, is not a dish. The disease row answers these.
                     "how do i know", "do i have", "have i got", "diagnosed", "diagnosis",
                     "symptoms", "signs", "blood test", "test for", "contagious", "curable",
                     "cause", "causes", "anaemia", "underactive", "deficiency")


_GLUTEN_MAKING = ("make", "making", "bake", "baking", "cook", "cooking", "recipe", "version",
                  "how do i", "how can i", "how to")


def _gluten_free(memory, understood):
    """How the dish changes when the gluten comes out, and the pastry and the loaf are not one job."""
    clean = understood.get("clean") or ""
    folded = " " + re.sub(r"[^a-z0-9 ]+", " ", clean.lower()) + " "
    # "is bread gluten free" is a fact, not a recipe: the answer is that wheat is what ordinary
    # bread is made of, and a loaf made without it is a different product.
    if (re.match(r"(is|are|does|do|can|should)\b", clean)
            and not any(" %s " % word in folded for word in _GLUTEN_MAKING)):
        return ("Not the ordinary one: wheat flour is what bread, pasta, cakes and most biscuits "
                "are made from, so unless the packet says gluten free it is not. A gluten-free "
                "loaf is a different product rather than the same loaf without something in it, "
                "and check the label for 'may contain wheat' on sauces, stock and chips.")
    if any(" %s " % word in folded for word in ("bread", "loaf", "loaves", "roll", "rolls",
                                                "baguette", "pizza", "naan", "focaccia")):
        return ("Buy this one rather than bake it: a gluten-free loaf needs a batter, not a dough, "
                "plus psyllium or xanthan to stand in for the stretch, and it is the one thing a "
                "shop does better. For a bun or a pizza base, a gluten-free bread flour blend "
                "with a teaspoon of xanthan per 500g and a wet dough, proved in the tin, gets "
                "there.")
    if any(" %s " % word in folded for word in ("pasta", "spaghetti", "penne", "macaroni",
                                                "lasagne", "noodles")):
        return ("Buy it: dried pasta made from corn, rice or buckwheat is the one gluten-free swap "
                "that works, and the fresh gluten-free pasta in the chiller is better still. Cook "
                "it in plenty of salted water and taste a minute before the packet says, because "
                "it goes from firm to mushy quickly, and dress it straight away - it does not "
                "wait like wheat pasta does.")
    if any(" %s " % word in folded for word in ("pastry", "shortcrust", "tart", "pie", "quiche",
                                                "flan", "crust")):
        return ("Gluten-free shortcrust: 200g of a gluten-free plain flour blend with half a "
                "teaspoon of xanthan gum, 100g of cold butter rubbed in, then a beaten egg or a "
                "few spoons of iced water to bring it together. Rest it 30 minutes in the fridge "
                "and roll it between two sheets of baking paper, because it tears. It needs no "
                "blind-bake change: 15 minutes at 190C (170C fan).")
    said = ("A gluten-free bake needs a blend, not one flour: a shop gluten-free plain flour blend "
            "with a quarter teaspoon of xanthan gum per 200g, and a splash more liquid than the "
            "recipe says, because there is no stretch in it to hold water. Let the batter stand "
            "20 minutes before it goes in the oven and it stops tasting gritty. Expect it to "
            "brown faster, so drop the oven 10C and give it five minutes longer.")
    if any(" %s " % word in folded for word in ("dairy", "milk", "butter", "cheese", "yoghurt",
                                                "yogurt", "vegan", "plant")):
        # the dairy half is a straight swap and a short one, so the blend answer carries it too
        said += (" For the dairy, unsweetened soya or oat milk goes in one for one, and a hard "
                 "dairy-free block margarine replaces the butter at the same weight.")
    return said


# A yes/no question about a food's own recipe: "is rice gluten free", "does soy sauce contain
# gluten", "is butter gluten free". The answer is a verdict about that food, not a recipe for it,
# and it comes from the same table every other answer in this file uses - so a food nobody wrote a
# card for still gets an honest yes or no. The ask is only the fact form ("gluten free", "contain
# gluten"); a line that asks to make something without gluten is the blend row's, and a line that
# says the food is already gluten free ("is gluten free bread ok") is the food's own answer.
# The asks that make a food the subject of a fact: "glutten free", "contain gluten", "without
# wheat". A diet said of the person ("im coeliac", "my son has a gluten allergy") is not one of
# them, and on a later line ("what can i do with butter beans" after "im coeliac") it was: the
# diet is carried into the reading, this row claimed the line, declined it, and the bean card on
# main never got its turn.
GLUTEN_FACT_DIET = ("gluten allergy", "coeliacs", "coeliac")
GLUTEN_FACT_ASKS = tuple(
    [ask for ask in GLUTEN_FREE_ASKS if ask not in GLUTEN_FACT_DIET]
    + ["free of gluten", "gluten in it", "have gluten", "has gluten", "contain wheat"])
# Every food the table can answer about, so a new food added above is answerable by itself.
GLUTEN_FACT_FOODS = tuple(sorted(MADE_OF))
# The staples where the swap sentence reads as an answer; on a sauce or a condiment "rice,
# potatoes or a corn pasta do the same job" is advice for the wrong dish.
GLUTEN_FACT_SWAPS = frozenset(
    "bread toast pasta spaghetti noodles couscous pastry cake cakes biscuit biscuits cracker "
    "crackers pitta flour crumpet bagel wrap wraps barley rye semolina scone scones pizza "
    "sandwich".split())
# The one food where the wheat-free version has its own name, and people know it: tamari.
GLUTEN_FACT_NAMED_SWAP = {
    "soy sauce": "Tamari is made without wheat and tastes the same.",
    "soya sauce": "Tamari is made without wheat and tastes the same.",
}


# The foods where the usual shop version has wheat in it even though the food itself is not made
# of it: a sausage is rusk as much as meat, and chips from a chip shop are often dusted with
# flour. A confident "yes" would be wrong for a coeliac, and a recipe is no answer at all, so
# these say what to look at instead.
GLUTEN_FACT_NOT_PLAIN = {
    "sausage": ("Usually not: most sausages have rusk in them, which is bread, so look for the "
                "ones marked gluten free."),
    "sausages": ("Usually not: most sausages have rusk in them, which is bread, so look for the "
                 "ones marked gluten free."),
    "chips": ("Not always: chips from a chip shop are sometimes dusted with flour, so ask there "
              "and read the packet on oven chips."),
}
# A fact about a food is asked as a question. "im coeliac and i miss pasta" has the ask and the
# food in it and is telling us something, not asking whether pasta has gluten: the answer there is
# what to buy instead, and it is the row below that has it. "can i make bread without gluten" is
# a question and is still a how-to, so the making words are read with the food taken out of the
# line: "baking powder" is a food, and "baking" in it is not the verb.
GLUTEN_FACT_OPENING = re.compile(
    r"^\s*(?:is|are|does|do|did|can|could|should|would|will|was|were|has|have)\b", re.I)
GLUTEN_FACT_MAKING = re.compile(
    r"\b(?:make|makes|making|bake|bakes|baking|cook|cooks|cooking|recipe|recipes|how do i|"
    r"how can i|how to|homemade|from scratch)\b", re.I)


def asks_a_gluten_fact(understood):
    """Whether this line, in its own words, asks the yes or no about one food.

    The reading a line gets can carry the last few turns, so "what can i do with butter beans"
    after "im coeliac" reaches the gluten rows on a word it does not say. This is a guard, so the
    row is never even chosen for such a line and the card that answers it keeps its turn.
    """
    if not isinstance(understood, dict):
        return False
    clean = understood.get("clean") or ""
    if not GLUTEN_FACT_OPENING.match(clean):
        return False
    lowered = clean.lower()
    if not any(ask in lowered for ask in GLUTEN_FACT_ASKS):
        return False
    food = _food_named(clean)
    if food is None:
        return False
    return not GLUTEN_FACT_MAKING.search(lowered.replace(food, " "))


def _free_of_gluten_fact(memory, understood):
    """The yes or no about one food, from the families the table says its usual recipe is made of."""
    clean = understood.get("clean") or ""
    if not GLUTEN_FACT_OPENING.match(clean):
        return ""
    food = _food_named(clean)
    if food is None:
        return ""
    if GLUTEN_FACT_MAKING.search(clean.lower().replace(food, " ")):
        return ""
    if food in GLUTEN_FACT_NOT_PLAIN:
        return GLUTEN_FACT_NOT_PLAIN[food]
    # "is gluten free bread ok" is not "is bread gluten free" the other way round: the words in
    # front of the food say it is the free-from version, and that line belongs to the food's own
    # safety answer. This row only answers the fact, so it stands back.
    phrase = r"\s+".join(re.escape(part) for part in food.split())
    if re.search(r"\b(?:[a-z]+)\s+free\s+" + phrase + r"\b", clean.lower()):
        return ""
    named = _named_as(clean, food)
    plural = _is_plural(food)
    if GLUTEN & MADE_OF[food]:
        said = "are made with wheat flour" if plural else "is made with wheat flour"
        reply = "No: " + named + " " + said + ", so it is not gluten free."
        if food in GLUTEN_FACT_NAMED_SWAP:
            return reply + " " + GLUTEN_FACT_NAMED_SWAP[food]
        if food in GLUTEN_FACT_SWAPS:
            swap = FAMILY_SAY[id(GLUTEN)][1]
            return reply + " " + swap[:1].upper() + swap[1:] + "."
        return reply + " The gluten-free one is a different product, so check the label."
    if food in NOT_SETTLED_BY_THE_RECIPE:
        # Oats are the plain food a recipe table cannot settle: the packet is what decides it.
        return NOT_SETTLED_BY_THE_RECIPE[food]
    if plural:
        return ("Yes: " + named + " have no gluten in them. The plain ones are gluten free; "
                "check the packet on flavoured or own-brand versions.")
    return ("Yes: " + named + " has no gluten in it. The plain one is gluten free; check the "
            "packet on flavoured or own-brand versions.")


_SWAP_VERDICTS = (
    (("yoghurt", "yogurt", "greek yoghurt", "greek yogurt"),
     ("cream", "double cream", "single cream", "creme fraiche"),
     "Yes, in anything cold or stirred in at the end: spoon it in off the heat, because yoghurt "
     "splits if it boils. It will not whip and it will not thicken a sauce the way cream does."),
    (("cornflour", "corn starch", "cornstarch"),
     ("plain flour", "self-raising flour", "self raising flour", "flour"),
     "Not in baking: cornflour has no gluten, so a cake or a loaf will not hold or rise. As a "
     "thickener it works, at one tablespoon where the recipe asks for two of plain flour, mixed "
     "into cold liquid first."),
    (("oil", "olive oil", "vegetable oil", "sunflower oil", "rapeseed oil"),
     ("butter", "margarine"),
     "In cakes, yes: use 80g of oil for every 100g of butter, and expect a slightly denser crumb. "
     "Not in pastry or shortbread, and not where you cream butter and sugar for air."),
    (("honey",),
     ("sugar",),
     "Yes, at three-quarters of the weight, and take a tablespoon or two out of the liquid. Bake "
     "10C cooler than the recipe says, because honey browns faster than sugar."),
    (("frozen peas", "frozen sweetcorn", "frozen veg", "frozen vegetables"),
     ("fresh", "fresh peas", "fresh vegetables"),
     "Yes, straight from the bag with no thawing: give them a minute or two longer in the pan. "
     "Frozen peas are sweeter than fresh ones that have sat about."),
    (("stock cube", "stock cubes", "bouillon", "stock powder", "stock pot", "stock pots"),
     ("stock", "chicken stock", "beef stock", "vegetable stock"),
     "Yes: one cube per 500ml of water for a stock-strength base, and half a cube in a small or "
     "already salty dish. Crumble it in rather than dropping it whole."),
    (("margarine",),
     ("butter",),
     "Yes in cakes and biscuits, at the same weight, if it is a block margarine meant for baking. "
     "The soft spread in a tub holds more water and gives a wetter, paler bake."),
    (("bicarbonate of soda", "bicarb", "baking soda"),
     ("baking powder",),
     "Not on its own: bicarbonate is about four times stronger than baking powder and needs an "
     "acid to work. Use a quarter of a teaspoon of bicarbonate with a teaspoon of lemon juice or "
     "vinegar in place of each teaspoon of baking powder."),
    (("evaporated milk",),
     ("cream", "double cream", "single cream"),
     "Yes for cooking, sauces and coffee: it will not whip, but it will not split in a hot sauce "
     "either, so it is the safer one to keep in the cupboard."),
)


# --- what the kitchen can do: a recipe for the oven is no use without one ---------------------
#
# "i've got chicken and rice and no oven" reached the roast-chicken timing answer, which tells
# someone with no oven to roast at 190C. The equipment a line says it lacks travels with it, the
# way a diet does, and an answer that needs that equipment steps aside for one that does not.

# The ways people say an appliance is not in the kitchen.
LACKS = (
    ("oven", ("no oven", "without an oven", "dont have an oven", "don't have an oven", "no ovens",
              "oven is broken", "oven's broken", "ovens broken", "oven doesnt work",
              "oven doesn't work", "just a hob", "only a hob", "hob only", "no cooker",
              "no stove", "only a microwave", "just a microwave", "microwave only",
              "no grill", "without a grill", "only have a microwave", "only got a microwave",
              "just have a microwave", "just got a microwave", "only have the hob",
              "only got a hob", "only have one hob", "no oven at home", "broken oven",
              "oven broke", "oven packed in", "no working oven", "oven isnt working",
              "oven is not working", "oven has broken",
              # the many ways people say the oven has gone, kept one word away from the bare
              # verbs: "my dog died" is not a broken oven, "my oven has died" is
              "oven has packed in", "ovens packed in", "oven packed up", "oven has packed up",
              "oven conked out", "oven has conked out", "oven died", "oven has died",
              "oven is dead", "oven broke down", "oven has broken down", "oven has broke",
              "oven stopped working", "oven has stopped working", "oven is on the blink",
              "oven has gone", "oven is gone", "oven has had it", "oven is knackered",
              "oven not heating", "oven isnt heating", "oven won't heat", "oven wont heat",
              "no oven space", "ova has gone")),
    ("hob", ("no hob", "without a hob", "no cooker", "no stove", "only a microwave",
             "only got a kettle", "only have a kettle", "just a kettle", "only the kettle",
             "just a microwave", "microwave only", "no rings", "no burners",
             "only have a microwave", "only got a microwave", "just have a microwave",
             "only have the microwave")),
    ("microwave", ("no microwave", "without a microwave")),
    ("freezer", ("no freezer", "without a freezer", "no room in the freezer")),
    ("kettle", ("no kettle", "without a kettle")),
)

# What an answer needs to be cooked: the words a method uses for each appliance.
REQUIRES = {
    "oven": ("oven", "roast", "roasting", "roasted", "bake", "baking", "baked", "grill",
             "grilled", "traybake", "tray bake", "casserole", "190c", "200c", "180c", "220c",
             "160c", "170c", "210c", "230c", "fan oven"),
    "hob": ("fry", "fried", "frying", "pan", "simmer", "boil", "boiling", "saucepan", "hob",
            "stir fry", "stir-fry", "poach", "steam", "griddle"),
    "microwave": ("microwave", "microwaved"),
    "freezer": ("freezer", "freeze", "frozen", "defrost"),
}


# The plainest way to say an appliance has gone is "I don't have a hob", and the article is what
# the phrase lists kept losing: "dont have an oven" was listed but "i dont have an oven" with the
# article was not, and "i dont have a microwave" said nothing at all. The heads and the nouns are
# kept apart so every appliance gets every wording, rather than one list per appliance.
LACK_HEADS = ("dont have", "don't have", "do not have", "doesnt have", "doesn't have", "didnt have",
              "didn't have", "havent got", "haven't got", "hasnt got", "hasn't got",
              "have not got", "has not got", "not got", "got no", "no longer have")
LACK_NOUNS = {"oven": ("an oven", "a oven", "oven"), "hob": ("a hob", "hob"),
              "microwave": ("a microwave", "microwave"), "freezer": ("a freezer", "freezer"),
              "kettle": ("a kettle", "kettle")}
LACK_SAID = tuple((name, head + " " + noun)
                  for name, nouns in LACK_NOUNS.items()
                  for head in LACK_HEADS for noun in nouns)

# A thing that hangs on an appliance is not the appliance: "i dont have an oven thermometer" is a
# question about a thermometer, so the oven is not what is missing.
LACK_ATTACHED = ("thermometer", "gloves", "glove", "mitt", "mitts", "tray", "dish", "rack",
                 "shelf", "light", "bulb", "door", "liner", "paper", "foil", "bag", "bags")


def _says_gone(phrases, segments):
    """True when a segment says one of these phrases, unless a word hangs off the appliance."""
    for segment in segments:
        for phrase in phrases:
            for found in re.finditer(re.escape(phrase), segment):
                after = segment[found.end():].strip().split(" ", 1)[0].strip(".,!?;:")
                if after not in LACK_ATTACHED:
                    return True
    return False


def _line(understood):
    """The line as this module reads it: what they typed, and the words it was read into."""
    return (((understood or {}).get("clean") or "") + " "
            + ((understood or {}).get("norm_text") or "")).lower()


def missing(understood):
    """The appliances this line says it does not have."""
    text = _line(understood)
    segments = text.split("|")
    gone = set()
    for name, phrases in LACKS:
        if _says_gone(phrases, segments):
            gone.add(name)
    for name, phrase in LACK_SAID:
        if name not in gone and _says_gone((phrase,), segments):
            gone.add(name)
    return gone


# A sentence that turns the appliance down is not an instruction to use it: "nothing here needs an
# oven", "no oven needed", "a hob alone will do".
TURNS_DOWN = ("no", "not", "without", "nothing", "never", "needs none", "free")

# A decision about the appliance is not an instruction to cook with it: "is it worth repairing my
# broken oven" wants the money rule, and the rule has to name the oven it is about.
DECIDING = ("repair", "repairing", "replace", "replacing", "mend", "mending", "fix", "fixing",
            "service", "servicing", "quote", "quotes", "scrap", "scrapping", "engineer",
            "warranty", "guarantee", "call-out")


def _sentences(text):
    return [one for one in re.split(r"(?<=[.!?;:])\s+|\n+", text) if one.strip()]


def unusable(text, understood):
    """True when this answer tells you to use something the line says it has not got."""
    gone = missing(understood)
    if not gone or not isinstance(text, str) or not text.strip():
        return False
    clean = str(understood.get("clean") or "").lower()
    if any(phrase in clean for phrase in EMPTY_ASK_PHRASES):
        # "theres nothing in for tea" is a line that has ruled out everything, so every food
        # an answer names reads as something the kitchen has not got and the empty-kitchen
        # answer, whose whole point is the shopping list, was thrown away and the line fell
        # back to an acknowledgement. Naming the food is the answer to that line.
        return False
    words = set()
    for name in gone:
        words.update(REQUIRES.get(name, ()))
    for sentence in _sentences(text.lower()):
        for word in words:
            if not re.search(r"\b" + re.escape(word) + r"\b", sentence):
                continue
            if any(one in sentence.split() for one in TURNS_DOWN):
                continue
            if any(one in sentence for one in DECIDING):
                continue
            return True
    return False


# What to cook when the kitchen has no oven: a list of hob-only meals, because that is the meal
# people mean when they say "no oven tho just a hob".
NO_OVEN = (
    "With a hob you can still eat well: pasta with a sauce made in the pan, rice with stir-fried "
    "veg and an egg on top, a one-pan curry of chickpeas or lentils with tomatoes, quesadillas or "
    "toasted sandwiches pressed in a dry pan, or potatoes boiled and then crushed into a pan with "
    "butter and greens. Eggs, tinned fish and beans all cook in a pan in minutes.")

NO_HOB = (
    "With only a microwave you can still eat properly: jacket potatoes (10 minutes, turned once), "
    "rice or pasta cooked in a big bowl of water, porridge, scrambled eggs, steamed frozen veg, "
    "tinned soup or beans, and a poached egg in a mug of water. Give a jacket potato a rub of oil "
    "and salt first and it comes out closer to oven-baked.")

# The oven is mostly missed for baking, and there are cakes that need no oven at all.
NO_BAKING = (
    "You cannot bake without an oven, but a fridge cake needs none: melt 100g butter, 200g "
    "chocolate and 2 tablespoons of golden syrup in a pan, stir in 200g crushed biscuits and a "
    "handful of raisins, press it into a tin and chill it for 2 hours. A cheesecake that sets in "
    "the fridge, tiramisu and lemon posset are the same trick: they set cold, not in the oven.")

# A scone, a pancake and a drop scone are not cakes: they were cooked on a girdle or in a pan long
# before every kitchen had an oven, and the fridge cake was answering "can i make scones with no
# oven" - a different food, since a scone dough pats out and cooks in a pan while anything that
# sets in the fridge is chocolate and crushed biscuits. So the pan bakes get their own answer,
# named for the thing the line asks about, and everything that wants a tin keeps the no-bake one.
_GRIDDLE_DOUGH = ("scone", "scones", "drop scone", "drop scones", "pikelet", "pikelets",
                  "chapati", "chapatis", "chapatti", "chapattis", "roti", "rotis")
_GRIDDLE_BATTER = ("pancake", "pancakes", "crumpet", "crumpets", "pikelet", "pikelets")
_GRIDDLE_WARM = ("wrap", "wraps", "tortilla", "tortillas", "pitta", "pittas", "pita", "pitas")
GRIDDLE_BAKES = re.compile(
    r"\b(?:" + "|".join(_GRIDDLE_DOUGH + _GRIDDLE_BATTER + _GRIDDLE_WARM) + r")\b", re.I)
GRIDDLE_DOUGH = re.compile(r"\b(?:" + "|".join(_GRIDDLE_DOUGH) + r")\b", re.I)
GRIDDLE_BATTER = re.compile(r"\b(?:" + "|".join(_GRIDDLE_BATTER) + r")\b", re.I)

# What will not work on a hob is anything that has to rise and brown in a tin, so each answer ends
# on that, because the next question is always "so what about the birthday cake".
_GRIDDLE_TAIL = ("What will not work on a hob is anything that has to rise and brown in a tin - a "
                 "sponge, a loaf, pastry - and those are the no-bake answers instead.")


def _griddle_answer(said):
    """The pan answer for the bake the line names, because a hob cooks it and a fridge cake is not it."""
    text = str(said or "").lower()
    batter = GRIDDLE_BATTER.search(text)
    if batter:
        return ("A " + batter.group(0).rstrip("s") + " is a pan job as it is: the batter goes into a "
                "hot non-stick pan with a little butter, about a minute a side until bubbles pop and "
                "the edges set. Crumpets want rings in a dry pan on a low heat until the top sets and "
                "the holes stay open. " + _GRIDDLE_TAIL)
    dough = GRIDDLE_DOUGH.search(text)
    if dough:
        # Name the bake the line names, then the pan method once: "A chapati cooks in a heavy pan"
        # reads as a recipe for what they asked, where a scone answer is the wrong dish again.
        name = dough.group(0)
        if name.rstrip("s") not in ("scone", "drop scone", "pikelet"):
            return ("A " + name.rstrip("s") + " cooks in a heavy dry pan, not a tin: the same dough "
                    "made a little thicker and patted out, about 5 minutes a side on a low heat "
                    "with a lid on, until the middle is set and the edges have caught. Scones, "
                    "pikelets and roti are the same trick. " + _GRIDDLE_TAIL)
        return ("A scone cooks in a heavy pan: the same dough made a little thicker and patted out, "
                "in a dry pan on a low heat with a lid on for about 5 minutes a side, until the "
                "middle is set and the edges have caught. Drop scones, pikelets, chapatis and roti "
                "are the same trick on a hot dry pan. " + _GRIDDLE_TAIL)
    warm = re.search(r"\b(?:wrap|wraps|tortilla|tortillas|pitta|pittas|pita|pitas)\b", text)
    named = warm.group(0).rstrip("s") if warm else "wrap"
    other = "and a wrap warms the same way" if named.startswith("pitt") else "and a pitta puffs the same way"
    return ("A " + named + " is warmed rather than baked: 30 seconds a side in a dry hot pan and it "
            "is soft enough to fold, " + other + ". " + _GRIDDLE_TAIL)


# Bread is the one bake with a real no-oven answer, and it is a pan, not a tin. It gets its own
# answer: told as a tail on the fridge cake, "how do i bake bread with no oven" was mostly a
# recipe for something they did not ask for.
NO_OVEN_BREAD = (
    "Bread with no oven is flatbread: flour, water, salt and a little oil, rested 20 minutes, "
    "rolled thin and cooked in a dry hot pan for two minutes a side. The same dough pushed into a "
    "hot oiled frying pan, lid on, turned once, makes a thick loaf that will do for toast.")

# Nothing but a kettle: couscous is the one proper meal it can make, and it is a good one.
NO_KETTLE = (
    "A kettle still makes a real meal out of couscous: put it in a bowl, pour boiling water over "
    "to just cover it, cover the bowl for five minutes, then fork it through with tinned "
    "chickpeas or tuna, chopped tomato, olives and lemon. Overnight oats (soak them in the "
    "fridge), instant porridge, pot noodles and cup soup need nothing more. If you can stretch to "
    "a cheap single-ring hob, it opens up pasta, rice, eggs and tinned soup.")

# An oven but no hob: roast and bake everything in one tray.
NO_OVEN_ONLY = (
    "With an oven and no hob, cook in one tray: chicken thighs or sausages with chopped potato, "
    "onion and pepper, oil, salt and herbs, 40 minutes at 200C (180C fan), turned once. Jacket "
    "potatoes take an hour at the same heat, baked pasta or a tin of tomatoes with butter and "
    "breadcrumbs bakes in 25 minutes, and roasted veg with a drained tin of chickpeas makes a "
    "meal on its own.")

NO_MICROWAVE = (
    "Without a microwave, a pan does the same jobs: reheat rice or leftovers with a splash of water "
    "over a low heat, defrost in the fridge overnight, and cook porridge or scrambled eggs in a "
    "saucepan in about five minutes.")

# Naming what is in the kitchen is how people ask what to make of it, oven or no oven.
LISTING = ("i have", "i've got", "ive got", "i only have", "only have", "only got", "just have",
           "just got", "there's", "theres", "in the fridge", "in my fridge", "in the cupboard",
           "in my cupboard", "sat in")

# The words a line uses when it wants a meal, which a kitchen problem alone does not say.
COOKING_ASKS = ("cook", "cooking", "make", "making", "dinner", "dinners", "supper", "tea",
                "meal", "meals", "eat", "eating", "recipe", "recipes", "idea", "ideas", "food",
                "lunch", "breakfast", "roast", "bake", "baking", "hungry",
                # "i need a dessert for 12 people with no oven" wants the sweet course, and
                # "need" and "want" are how people ask for a thing rather than a meal: without
                # them the no-oven answer was never reached and the question went back as a
                # "what kind of dessert do you usually go for".
                "need", "needs", "want", "wants", "dessert", "desserts", "pudding", "puddings",
                "sweet", "cake", "cakes", "biscuits", "cookies")


# A dessert with no oven is the no-bake answer, not a list of things to cook on the hob: "no oven
# tho just need something i can make ahead" was getting pasta and a one-pan curry, which is
# dinner. "sweet potato" is a vegetable, so it never counts as the sweet course.
SWEET_ASK = re.compile(r"\b(?:desserts?|puddings?|sweets?|biscuits?|cookies?|meringues?"
                       r"|possets?|trifles?|make ahead|make-ahead)\b")
CROWD = re.compile(r"\b(?:[89]|1[0-9]|[2-9][0-9])\b")

# A line that asks for bread rather than for a bake in general.
BREAD = re.compile(r"\b(?:bread|loaf|loaves|flatbread|naan|pitta|pita)\b", re.I)

# ...and a line that names a cake as well as bread is asking about the cake.
CAKEISH = re.compile(r"\b(?:cake|cakes|biscuit|biscuits|cookie|cookies|brownie|brownies|"
                     r"muffin|muffins|scone|scones|meringue|meringues|pastry|pastries|"
                     r"flapjack|flapjacks)\b", re.I)

def _asks_for_sweet(text):
    """Whether the line is asking for the sweet course rather than a meal."""
    text = str(text).lower()
    if "sweet potato" in text:
        return False
    return bool(SWEET_ASK.search(text))


def _no_baking(text):
    """The no-oven answer, with the quantities doubled when the line says how many are coming."""
    said = str(text or "")
    # A scone or a pancake is a griddle bake, not a cold-set one: the pan answer is the true one,
    # and it is given before bread and cakes because a scone is neither.
    if GRIDDLE_BAKES.search(said):
        return _griddle_answer(said)
    if BREAD.search(said) and not CAKEISH.search(said):
        base = NO_OVEN_BREAD
    else:
        base = NO_BAKING + (" " + NO_OVEN_BREAD if BREAD.search(said) else "")
    many = CROWD.search(said)
    if not many:
        return base
    return base + (" For " + many.group() + " people make two tins of it and cut it small, "
                        "or set one big cheesecake in a deep tin and chill it overnight.")


# A pudding for a crowd is the same pudding twice over: "gotta bring a dessert, family do, 12 of
# us" is answered with a crumble, and the useful part is how much of it to make.
PUDDING_IDEAS = (
    "An apple and blackberry crumble is the easiest crowd-pleaser: fruit in a dish, a crumble of "
    "butter, flour and sugar on top, 35 minutes at 180C, and custard. Baked rice pudding and bread "
    "and butter pudding are just as easy and soft enough for anyone who finds chewing hard; Eton "
    "mess takes five minutes if you buy the meringues.")


def _pudding_ideas(memory, understood):
    """The pudding answer, with the quantity worked out when the line says how many are coming."""
    text = str(((understood or {}).get("clean") or "")).lower()
    many = CROWD.search(text)
    if not many:
        return PUDDING_IDEAS
    return PUDDING_IDEAS + (" For " + many.group() + " people make two dishes of it and put the "
                            "custard out in a jug.")


def without(understood):
    """An answer for a line that says the kitchen has no oven or no microwave, or None."""
    gone = missing(understood)
    if not gone:
        return None
    words = (understood or {}).get("words") if isinstance(understood, dict) else None
    text = " ".join(words) if isinstance(words, list) else _line(understood)
    text = str(text).lower()
    asking = any(re.search(r"\b" + re.escape(one) + r"\b", text) for one in COOKING_ASKS)
    listing = any(one in text for one in LISTING)   # "i've got chicken and rice and no oven"
    if not (asking or listing):
        # "no oven tho just a hob" names the kitchen and asks nothing at all, and it was being
        # acknowledged as a remark. In this module a line that names both what is missing and
        # what is there is the what-can-i-cook question, so long as it says nothing else.
        named = any(one in text for one in HAVE_ONE["hob"] + HAVE_ONE["microwave"]
                    + HAVE_ONE["kettle"] + HAVE_ONE["oven"] + ONLY_ONE["hob"]
                    + ONLY_ONE["microwave"] + ONLY_ONE["kettle"])
        if not (named and len(text.split()) <= 8):
            return None
    # A roast is not a no-bake cake: "can i roast a chicken with no oven" got the fridge cake,
    # because "roast" was in the list that sends the line to the no-bake answer. Anything that
    # comes out of a tin - pastry, bread, cakes, biscuits - is the no-bake answer; a roast is
    # dinner, and with no oven it is the hob.
    baking = ("bake", "baking", "cake", "cakes", "bread", "pie", "pastry", "pastries",
              "biscuit", "biscuits", "cookie", "cookies", "meringue", "meringues",
              "yorkshire", "scone", "scones", "loaf", "loaves", "muffin", "muffins",
              "brownies", "flapjack", "flapjacks")
    how = "bake" if any(one in text for one in baking) or _asks_for_sweet(text) else ""
    if "oven" in gone and how == "bake" and "hob" not in gone:
        return _no_baking(text)
    # Nothing in "can i make roti with no oven" is a baking word, so it fell through to the list of
    # hob meals - pasta, a one-pan curry - which is dinner and not what was asked. A pan bake named
    # in the line gets the pan answer whether or not the line says "bake".
    if "oven" in gone and "hob" not in gone and GRIDDLE_BAKES.search(text):
        return _griddle_answer(text)
    have = available(text, gone)
    if "hob" in gone or "hob" not in have:
        if "oven" in have:
            return NO_OVEN_ONLY
        if "microwave" in have:
            return NO_HOB
        return NO_KETTLE
    if "oven" in gone or "oven" not in have:
        return NO_OVEN
    if "microwave" in gone and how != "bake":
        return NO_MICROWAVE
    return None


# The one appliance a line says it has ("i've only got a kettle"), and the ones it names as there
# ("no hob, but the oven works"): what to cook depends on what is left, not on what is missing.
ONLY_ONE = {
    "kettle": ("only got a kettle", "only have a kettle", "only a kettle", "just a kettle",
               "only the kettle"),
    "microwave": ("only have a microwave", "only got a microwave", "only a microwave",
                  "just a microwave", "just have a microwave", "just got a microwave",
                  "microwave only", "only the microwave"),
    "hob": ("only a hob", "just a hob", "only have a hob", "only got a hob", "hob only",
            "only have one hob"),
    "oven": ("only an oven", "only have an oven", "only got an oven", "oven only"),
}
HAVE_ONE = {
    "oven": ("got an oven", "have an oven", "have the oven", "the oven works", "there's an oven",
             "theres an oven", "oven works"),
    "hob": ("got a hob", "have a hob", "there's a hob", "theres a hob", "got a cooker",
            "have a cooker"),
    "microwave": ("got a microwave", "have a microwave", "there's a microwave",
                  "theres a microwave"),
    "kettle": ("got a kettle", "have a kettle", "there's a kettle", "theres a kettle"),
}


def available(text, gone):
    """What the kitchen has, as far as the line says: what it names, else whatever is not gone.

    A thing the line names as gone is not there, however it was named: "i dont have an oven"
    and "i dont have an oven but i have a hob" both reached the oven-and-no-hob answer, because
    the words "have an oven" sit inside "dont have an oven". Naming what is missing leaves the
    rest of a normal kitchen, so dropping the gone one from the named ones is the whole fix.
    """
    text = str(text).lower()
    for name, phrases in ONLY_ONE.items():
        if any(one in text for one in phrases):
            return {name}
    named = {name for name, phrases in HAVE_ONE.items() if any(one in text for one in phrases)}
    named -= set(gone or ())
    if named:
        return named
    return {"oven", "hob", "microwave", "kettle"} - set(gone or ())

def _herbs_keep(memory, understood):
    """A herb that can be saved goes in water; a slimy one is past saving and the reply says so."""
    words = set((understood or {}).get("words") or ())
    clean = " " + ((understood or {}).get("clean") or "") + " "
    if {"slimy", "slime", "rotten", "mouldy", "moldy"} & words or "gone over" in clean:
        return ("A slimy herb is past saving, so bin the slimy stems and pick out the ones that are "
                "still green to use today. It happens when the leaves stay wet: a bag with damp "
                "kitchen paper is right, a wet one sat in a warm fridge is not. Next bunch, stand "
                "the stems in an inch of water with a bag over the top, or freeze what you cannot "
                "use in the next few days.")
    return ("Stand soft herbs in a jar with an inch of water, loosely covered with a bag, or wrap "
            "them in damp kitchen paper in the fridge. Basil hates the cold, so keep that one on "
            "the windowsill instead.")


# --- the words on a recipe, and how much food to allow ---------------------
# Two questions people ask constantly that no per-dish entry answers, because neither names a
# dish: "what does sear mean" and "how many eggs per person". A glossary is one table, keyed by
# the word, so every way of asking about that word reaches the same line; a portion is keyed by
# the food, the way rice-portion and pasta-portion already are.

# The words people meet in a recipe and are too polite to look up.
COOK_WORDS = {
    # "what is a simmer" and "simmer or boil" belong to the simmer-and-boil entry (#1041), which
    # measures them against each other; these are the words nothing else explains.
    "reduce": "Reducing is simmering a sauce uncovered until water boils off and it thickens and "
              "tastes stronger. Watch it at the end - the last two minutes do most of the work.",
    "sear": "Searing is browning meat hard in a hot pan, for flavour and colour, not for cooking "
            "it through. Pat it dry first and leave it alone until it releases by itself.",
    "blanch": "Blanching is a minute or two in boiling water, then straight into cold water: it "
              "sets the colour of green vegetables and loosens tomato and peach skins.",
    "sweat": "Sweating is softening onion or vegetables slowly in a little fat with the lid on, "
             "without colouring them. Low heat, five to ten minutes.",
    "al dente": "Al dente means pasta with a little bite left in the middle: take a minute off "
                "the packet time, taste it, and keep testing.",
    "fold": "Folding is mixing gently with a big spoon, turning the bowl and cutting through, so "
            "you keep the air in whipped egg white or cream.",
    "deglaze": "Deglazing is pouring wine, stock or water into a hot pan after frying and "
               "scraping the brown bits up: that is where the flavour is.",
}


# The words that are also ordinary cooking instructions: "how do i reduce a sauce" is a how-to,
# not a definition, so these only get their line when the line asks what it means. A how-to line
# counts as well when it names the thing the word acts on, which is why each of these has a
# subject list below: "how do i fold in egg whites" is the mixing line, "how do i fold a fitted
# sheet" is not about food at all.
NEEDS_DEFINITION = frozenset(("reduce", "fold", "sear", "sweat"))

# What each word acts on, so a click in a recipe is not read as a click in the body or the house.
WORD_SUBJECT = {
    "reduce": ("sauce", "stock", "gravy", "wine", "juice", "glaze", "syrup", "liquid",
               "broth", "soup", "half", "pan", "thicken", "thickens", "jam", "cream"),
    "fold": ("flour", "egg", "eggs", "white", "whites", "batter", "mixture", "dough",
             "cream", "sugar", "meringue", "ingredient", "ingredients", "pastry", "bowl",
             "spoon", "spatula", "filling", "chocolate"),
    "sear": ("steak", "meat", "beef", "chicken", "fish", "salmon", "pork", "lamb", "tuna",
             "pan", "joint", "roast", "sausage", "tofu", "scallop"),
    "sweat": ("onion", "onions", "shallot", "shallots", "leek", "garlic", "carrot",
              "vegetables", "veg", "celery", "mushroom", "pan", "butter", "fat", "oil"),
    "blanch": ("vegetable", "vegetables", "greens", "bean", "beans", "broccoli", "tomato",
               "tomatoes", "peach", "almond", "almonds", "potato", "potatoes", "chips",
               "spinach", "cauliflower", "cabbage"),
    "deglaze": ("pan", "wine", "stock", "sauce", "bits", "meat", "roast", "gravy"),
}

# "what does searing pain mean" and "how do i reduce my electricity bill" are not glossary
# questions whatever verb they contain. Words rather than phrases where the bare word cannot be
# about food, phrases where it can (a baking sheet is a real thing in a kitchen).
NOT_A_COOKING_LINE = ("pain", "pains", "maths", "math", "percentage", "equation", "fraction",
                      "algebra", "fitted sheet", "bed sheet", "sheets", "towel", "towels",
                      "laundry", "pillow", "duvet", "hands sweating", "sweaty", "armpits",
                      "my hands", "my feet", "fever", "night sweats", "anxious", "anxiety",
                      "nerves", "doctor", "gp appointment", "hospital", "sick", "ill",
                      "temperature of the room", "heating bill", "electricity", "gas bill",
                      # "fold", "sweat" and "sear" are ordinary words elsewhere: a card game, a
                      # folded sheet of paper, a rock face, a relationship. Each of these was a
                      # wrong answer where main declined, and the list costs nothing because a
                      # cooking line that carries the food word still answers.
                      "poker", "cards", "card game", "blackjack", "origami", "folding chair",
                      "folding table", "geology", "tectonic", "fold in the rock",
                      "relationship", "boyfriend", "girlfriend",
                      "belly fat", "my back", "my shoulder",
                      # a glossary of cooking words is not a mail server: "how do i reduce
                      # spam" was answered with a definition, because "reduce" is a cooking
                      # verb too. Nothing in a kitchen line carries these.
                      "spam", "email", "emails", "e-mail", "inbox", "junk mail", "scam",
                      "unsubscribe", "newsletter", "mailbox",
                      # "reduce" is a cooking verb and also how everyone asks about a screen,
                      # a volume or a bill: "how do i reduce the brightness on my phone" was
                      # answered with a definition of reducing a sauce.
                      "brightness", "bright", "brighter", "dim", "dimmer", "screen", "screens",
                      "display", "volume", "louder", "loud", "screen time", "data usage",
                      # "how do i reduce sugar in my diet" was a definition of reducing, because
                      # "reduce" is a cooking verb and "sugar" is a cooking word: the diet in the
                      # line is what says it is not a sauce.
                      "my diet", "diet", "diets", "dieting", "sugar intake", "blood sugar",
                      "less sugar", "down on sugar", "cut out sugar", "sugary", "cravings")

# The shape of a "what does it mean" question.
DEFINITION_WORDS = ("mean", "means", "meaning", "difference", "what is", "what's", "whats",
                    "between", "versus", "vs", "definition")


def _names_a_subject(word, said):
    """True when the line says the food this word acts on, or points at it: "sear it"."""
    if any(subject in said for subject in WORD_SUBJECT.get(word, ())):
        return True
    return any(word + pronoun in said for pronoun in (" it", " them", " this", " these"))


def _cook_word_hit(word, said):
    """Where the line says this word, as (position, the table key), or None."""
    if word in said:
        return said.find(word), word
    stem = word.rstrip("e")
    if len(stem) > 3 and stem in said:
        return said.find(stem), word
    return None


def _cook_word(memory, understood):
    said = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
    # The order the person said them in, but a longer phrase wins over the plain word inside it,
    # so "rolling boil" is not also read as "boil". A word catches its own -ing form too:
    # "deglazing" is the deglaze line.
    found = sorted(hit for hit in (_cook_word_hit(word, said) for word in COOK_WORDS) if hit)
    named = []
    for pos, word in found:
        if any(pos >= other_pos and pos + len(word) <= other_pos + len(other) and word != other
               for other_pos, other in found):
            continue
        named.append(word)
    if not named:
        return None
    if not any(word in said for word in DEFINITION_WORDS):
        # Not a definition question, so this has to be a how-to about the food itself: drop every
        # word whose subject is missing, and pass if that leaves nothing.
        named = [word for word in named
                 if word not in NEEDS_DEFINITION or _names_a_subject(word, said)]
        if not named:
            return None
    if len(named) == 1:
        return COOK_WORDS[named[0]]
    # A line naming two of them is asking for the difference, so both lines come back together.
    return "%s %s" % (COOK_WORDS[named[0]], COOK_WORDS[named[1]])


# A mash that must leave butter or milk out, or that is for a baby, is not the plain method: the
# method starts with salted water and ends with warm milk and butter. Held out of the plain entry
# so the answer that suits those lines is the one that takes them.
_MASH_NOT_THIS = ("without butter", "no butter", "butter free", "without milk", "no milk",
                  "milk free", "dairy free", "dairy-free", "no dairy", "without dairy",
                  "vegan", "baby", "babies", "for my baby", "for a baby", "weaning", "weaned",
                  "toddler", "6 months", "six months", "9 months", "first foods",
                  # "how long" is back in the key for the boiling time, and it is in every
                  # keeping question too: "how long does mashed potato keep in the fridge"
                  # belongs to the keeping entry, not to the method.
                  "keep", "keeps", "keeping", "store", "storing", "storage", "fridge",
                  "freezer", "freeze", "refrigerate", "reheat", "reheated", "leftover",
                  "left over", "last", "lasts", "gone off", "safe",
                  # "how long does" is not a keeping word on its own: it took "how long does it
                  # take to make mash" as well, which is the boiling time this method opens
                  # with. Every keeping line about mash says keep, fridge, last or gone off
                  # anyway, and those are all above.
                  )

# A burger with no beef and no mince in it is a pulses method, not the 20%-fat one.
_NO_MEAT = ("without mince", "no mince", "without beef", "no beef", "without meat", "no meat",
            "meat free", "meat-free", "vegetarian", "veggie", "vegan", "lentil", "lentils",
            "bean", "beans", "chickpea", "chickpeas", "pulse", "pulses")
# --- baking, as a recipe rather than a set of ingredients -----------------------------
# "how do i make chocolate cake" names nothing in the kitchen and asks for weights, a tin and
# a time, so the pantry has nothing to build from and the answer used to be a shrug. These are
# the bakes an ordinary person makes on a wet afternoon, each written as one answer: what it is,
# the weights, the tin, the heat, and how to tell it is done.

# Longest name first, so "chocolate chip cookies" is cookies and "loaf of bread" is bread. The
# aliases are folded the same way the line's words are, or "brownies" (which folds to "browny")
# and "scones" (which folds to "scone") would never meet the name they were written for. Built
# on first use because _fold is defined further down the file.
_BAKE_ALIASES = None


def _bake_aliases():
    global _BAKE_ALIASES
    if _BAKE_ALIASES is None:
        _BAKE_ALIASES = tuple(sorted(
            (([_fold(part) for part in alias.split()], name)
             for name, (aliases, _) in BAKES.items() for alias in aliases),
            key=lambda pair: -len(pair[0])))
    return _BAKE_ALIASES


# A time, a heat or a "how long" is the timing entry's question, not the recipe's.
_TIMING_ASKS = ("how long", "minutes", "temperature", "what temp", "fan", "gas mark", "preheat",
                "how hot")


# A bake whose name is one word the pantry also builds dinners from ("bread", "pastry") is not a
# bake the pantry has to step aside for: "bread and cheese" is still a sandwich question.
_PANTRY_AS_WORDS = None


def _pantry_words():
    global _PANTRY_AS_WORDS
    if _PANTRY_AS_WORDS is None:
        _PANTRY_AS_WORDS = frozenset(_fold(name) for name in PANTRY)
    return _PANTRY_AS_WORDS


def _bake_hits(folded, skip_pantry=False):
    """[(parts, name), ...] for the bakes these words name, longest name first.

    skip_pantry leaves out a name that is one word the pantry also cooks with, so a line naming
    two foods ("bread and cheese") is not read as a request for the bread recipe.
    """
    hits = []
    for parts, name in _bake_aliases():
        if skip_pantry and len(parts) == 1 and parts[0] in _pantry_words():
            continue
        for start in range(len(folded) - len(parts) + 1):
            if folded[start:start + len(parts)] == parts:
                hits.append((parts, name))
                break
    return hits


def _names_a_bake(understood):
    """True when the line names a bake ("banana bread", "brownies"), not a food to cook with."""
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = [_fold(word) for word in words]
    # A bake already in the kitchen is a food to use up, not a recipe to follow: "i have leftover
    # puff pastry, what can i do with it" is the pantry's question. Every bake name here stood
    # the pantry and the dish table down, so the line got no answer at all.
    return any(not _already_baked(folded, parts)
               for parts, _name in _bake_hits(folded, skip_pantry=True))


# A bake someone already has in the kitchen is not a request to make it: "what can i make with
# leftover bread" and "use up stale scones" want something to do with the thing, which is the
# pantry's leftover answer. Only a marker in front of the bake's own name counts, so "i have old
# bananas, what can i bake" and "can i bake bread with leftover milk" still get the recipe.
_ALREADY_BAKED_WORDS = frozenset("leftover leftovers stale old yesterday already".split())
_ALREADY_BAKED_PHRASES = ("use up", "using up", "used up", "left over", "left from",
                          "already made", "got spare", "going stale")


def _already_baked(folded, parts):
    """True when a "leftover"/"stale"/"old" sits just in front of this bake's name."""
    for start in range(len(folded) - len(parts) + 1):
        if folded[start:start + len(parts)] != parts:
            continue
        window = folded[max(0, start - 3):start]
        if any(word in _ALREADY_BAKED_WORDS for word in window):
            return True
        return any(phrase in " ".join(window) for phrase in _ALREADY_BAKED_PHRASES)
    return False


def _bake(memory, understood, text=None):
    """The recipe for the bake the line names and asks about, or None when it names none."""
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = [_fold(word) for word in words]
    if text:
        folded = folded + [_fold(word) for word in str(text).lower().split()]
    said = " ".join(folded)
    if any(phrase in said for phrase in _TIMING_ASKS):
        return None
    if any(phrase in said for phrase in _NO_YEAST):
        # a loaf with no yeast in it is the soda loaf's line, not this yeast recipe's
        return None
    if not (understood.get("asks") or any(word in ("how", "what", "whats", "recipe")
                                          for word in folded)):
        # "i baked brownies yesterday" is telling the bot about a cake, not asking how.
        return None
    if _asks_vegan(folded):
        # Every recipe in BAKES uses butter or egg: a vegan ask is the vegan entry's question, and
        # it was being told to rub cold butter into flour.
        return None
    hits = _bake_hits(folded, skip_pantry=len(ingredients(understood)) > 1)
    if not hits or _already_baked(folded, hits[0][0]):
        # They have the loaf already: the pantry and the leftover answers know what to do with it.
        return None
    return BAKES[hits[0][1]][1]


_NONSTICK_CLEAN = ("clean", "cleaning", "wash", "washing", "scrub", "scouring", "burnt",
                   "stained")
_NONSTICK_KEEP = ("safe", "safety", "still use", "use it", "throw", "bin it", "replace",
                  "replacing", "worn", "bits", "coming off", "flakes", "scratched", "scratches",
                  "scratch", "flaking", "peeling", "coating")


def _non_stick_pan(memory, understood):
    """The sponge for a cleaning line, the verdict first for a "is it still safe" line."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    wants_clean = any(word in said for word in _NONSTICK_CLEAN)
    if not wants_clean and any(word in said for word in _NONSTICK_KEEP):
        return ("Small scratches are fine to keep cooking on. Once it is scratched through to the "
                "metal, or the coating is flaking or peeling into the food, replace the pan: you "
                "do not want flakes of coating in a meal, and a worn pan stops being non-stick "
                "anyway. Until then, keep metal tools, scouring pads and an empty pan on high "
                "heat away from it, because those are what scratch it.")
    return ("Warm water, washing-up liquid and a soft sponge, then dry it with a cloth: no "
            "scouring pad, no wire wool and no metal tools, because a scratch in the coating is "
            "what ruins it. For burnt-on food, simmer a little water in the pan for five minutes "
            "and lift it with a wooden spatula rather than scraping. If the coating is flaking or "
            "peeling, replace the pan - that is not something to cook through.")
# A cup of tea is four things people get wrong in the same order: fresh water, water just off
# the boil, enough time, and taking the bag out before it turns bitter. The other three shapes -
# a pot, iced tea and the cloudy cup - are the same subject and different answers, so one row
# reads the line and picks, the way the coffee fault row does.
TEA_METHOD_TEXT = (
    "Fresh water boiled once, one teabag per mug, three to four minutes and then the bag out: "
    "that is the whole of a good cup, and the milk goes in last. Green tea wants cooler water, "
    "about 80C, for two to three minutes, and black tea wants it just off the boil, three to "
    "five. Bitter tea has steeped too long in water that was too hot, and a mug that tastes of "
    "the last one is a bag left sitting in it.")

TEA_POT_TEXT = (
    "Warm the pot first with a splash of boiling water swirled round and tipped away, then one "
    "teabag or one teaspoon of leaves per cup and one extra for the pot, water just off the "
    "boil, three to four minutes. Take the bags or leaves out before it goes to the table, and a "
    "cosy keeps the second cup hot without stewing it.")

TEA_ICED_TEXT = (
    "Cold brew it: eight teabags to a litre of cold water in the fridge overnight, bags out in "
    "the morning, then lemon and sugar to taste, which has none of the bitterness of a hot brew "
    "cooled down. In a hurry, brew double strength in a mug of boiling water for four minutes, "
    "take the bags out, and pour it over a jug of ice.")

TEA_CLOUDY_TEXT = (
    "Cloudy tea is the minerals in hard water binding with the tannin, and it is harmless to "
    "drink: filter the water, or use bottled, to get it clear, or add a small pinch of "
    "bicarbonate of soda to the pot, which keeps the tannin dissolved. It is not a dirty kettle "
    "and it is not a sign the tea has gone off.")

TEA_FAULT_TEXT = (
    "Green tea wants water at about 80C for 2 to 3 minutes; black tea wants it just off the "
    "boil for 3 to 5. Bitter tea is nearly always tea that steeped too long in water that was "
    "too hot, and sour or stewed tea is a pot left standing on a warmer or in the leaves: "
    "pour it off them and make the next one weaker and shorter.")


# Green tea is the one brew with its own temperature, and the plain method opens with boiling
# water: "how do i make green tea" and "how do i make a cup of green tea with a teabag" got the
# black-tea card the moment the method row took those lines back from the green-tea fact.
TEA_GREEN_TEXT = (
    "Green tea wants water at about 80C rather than boiling, for two to three minutes: boil the "
    "kettle and let it stand for a minute or two, or add a splash of cold water first. Water "
    "straight off the boil makes it bitter, and green tea goes bitter quickly, so pull the bag "
    "out at three minutes and drink it soon after.")

TEA_TWICE_TEXT = (
    "A second cup from the same teabag is weak and mostly colour, but it is harmless: if you "
    "want it stronger, use a fresh bag and pull it out sooner instead. Reuse one within the same "
    "hour at most, and not once it has been sitting in milk.")


# "Tea" is the evening meal as well as the drink, and the request shapes in the row - "can i
# have", "i'll have" - are what a meal question is asked with too: "what can i have for tea" was
# answered with how to brew a cup, while "whats for tea" and "what shall i have for tea" got
# dinner (royal-zipper, #8152 was the drink half of the same row). A line that asks what to have
# for a meal is asking about the plate, whatever the request shape around it.
_ASKS_WHAT_TO_HAVE = re.compile(
    r"\b(?:what|anything|something|whats|what's)\b[^.?!]*\b(?:have|eat|cook|make|do)\b")
_FOR_A_MEAL = re.compile(
    r"\bfor\s+(?:my\s+|our\s+|the\s+|his\s+|her\s+)?"
    r"(?:tea|dinner|lunch|supper|breakfast|brekkie|supper|teatime|tea time)\b")


def _tea_reply(memory, understood):
    """The brewing answer the line asked for: a method, a pot, iced, a cloudy cup, or a fault."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if _FOR_A_MEAL.search(said) and _ASKS_WHAT_TO_HAVE.search(said):
        # "what can i have for tea" is the evening meal: the meal table answers it.
        return None
    words = set(re.findall(r"[a-z']+", said))
    if words & {"iced", "ice"}:
        return TEA_ICED_TEXT
    if words & {"pot", "teapot", "teapots"}:
        return TEA_POT_TEXT
    if words & {"cloudy", "cloudiness", "scum", "murky", "film"}:
        return TEA_CLOUDY_TEXT
    if words & {"green", "greens", "sencha", "matcha", "jasmine"}:
        return TEA_GREEN_TEXT
    if words & {"twice", "again", "reuse", "re-use", "second"}:
        return TEA_TWICE_TEXT
    if words & {"bitter", "sour", "soured", "stewed", "weak", "strong", "stronger", "watery",
                "tastes", "taste", "tasting", "stewing"}:
        return TEA_FAULT_TEXT
    return TEA_METHOD_TEXT


def _rice_time(memory, understood):
    """The time the line asked about: brown and wholegrain rice take twice as long as white.

    The same entry answers two questions - how long it takes, and how much water it wants - so the
    answer opens on the one that was asked. "How long does rice take" used to get the ratio first
    and the minutes in the middle of the paragraph, which is STYLE.md's miss: a good paragraph
    about rice that is not the answer to the question. The brown answer already opened on its time
    (`test_a_brown_rice_question_leads_with_the_brown_rice_time`), and this is the same rule for
    the white one. A water question keeps the water first, because that is what it asked.
    """
    words = set((understood or {}).get("words") or ())
    asks = set((understood or {}).get("asks") or ())
    brown = words & {"brown", "wholegrain", "whole"}
    if brown:
        return ("Brown rice takes 25 to 30 minutes, with a little more water: 1 part rice to 2 "
                "parts water, lid on, low simmer. Let it sit 5 minutes off the heat, still covered, "
                "before you fork it through. White long grain is 1 part rice to 1.5 parts water for "
                "12 minutes, then 10 minutes off the heat. Too much water is what turns rice to "
                "porridge.")
    if asks & {"how_long", "when"}:
        # The minutes first, the ratio after them, for the same reason the brown row does it.
        return ("White long grain takes 10 to 12 minutes on a low simmer with the lid on, then 10 "
                "more off the heat. Use 1 part rice to about 1.5 parts water by volume, or the "
                "fingertip test: water one knuckle above the rice. Brown and wholegrain are the "
                "ones that take longer. Too much water is what turns rice to porridge.")
    return ("Use 1 part rice to about 1.5 parts water by volume for long grain, or the fingertip "
            "test: water one knuckle above the rice, and give it 12 minutes on a low simmer with the "
            "lid on, then 10 more off the heat. Brown and wholegrain rice are the ones that take "
            "longer. Too much water is what turns rice to porridge.")

# The ways a line says the loaf has none of the yeast this answer is about.
_NO_YEAST = ("no yeast", "without yeast", "yeastless", "yeast free", "yeast-free",
             "no need for yeast", "dont need yeast", "don't need yeast")


def _bread_rise_answer():
    """Why a loaf or a dough is slow, worded for the prove the person is actually doing.

    A night in the fridge is a deliberate slow prove - telling that person to find somewhere warm
    undoes it - and "do I need to prove it twice" is a question about the second, shaped prove.
    The time comes first, because that is what was asked; the reason follows it.
    """
    def answer(memory, understood):
        # only this line: a fridge mentioned two turns ago is not this prove
        said = str(understood.get("clean") or " ".join(understood.get("words") or [])).lower()
        # There is no rise to explain when there is no yeast in the loaf: a soda loaf is the
        # no-yeast recipe's line, and proving words cannot apply to it.
        if any(one in said for one in _NO_YEAST):
            return None
        # A sourdough loaf does not rise on warmth and a sachet of yeast: what lifts it is the
        # starter, and "my sourdough is flat" was told to leave it an hour at 25C "until the dough
        # has doubled", which is the advice for a yeasted loaf and never fixes a weak starter.
        if "sourdough" in said or "sour dough" in said or "starter" in said:
            return ("A sourdough loaf rises on the starter, not on warmth alone: a starter that "
                    "doubles in 4 to 6 hours after a feed is strong enough to bake with, and one "
                    "that only bubbles is not, so feed it twice a day for three days first. Then "
                    "give the bulk 4 to 6 hours at room temperature with three or four sets of "
                    "stretch and fold in the first two hours, and shape it with real tension. A "
                    "flat loaf usually wants a stiffer dough and a longer, colder second prove.")
        if "fridge" in said or "overnight" in said or "in the cold" in said:
            return ("A night in the fridge is a slow prove on purpose, not a fault: shape it cold, "
                    "then leave it an hour at room temperature before it goes in the oven. If it "
                    "hasn't risen at all by the morning, the yeast is dead, so check the date.")
        if "twice" in said or "second prove" in said or "second rise" in said or "two proves" in said:
            return ("Yes, twice: the first is done when the dough has doubled, and the second is the "
                    "shaped loaf, about an hour, until it springs back slowly when you poke it. "
                    "Skipping the second gives you a tight, close crumb.")
        if ("wont" in said or "won't" in said or "isnt" in said or "isn't" in said
                or "not rising" in said or "didnt" in said or "didn't" in said
                or "hasnt risen" in said or "stalled" in said):
            return ("Give it another hour somewhere around 25C, until it has doubled, and check the "
                    "water was warm rather than hot and that the yeast is in date. If it still "
                    "hasn't moved at all, the yeast is dead, so start again with fresh yeast.")
        return ("Leave it somewhere around 25C for 1 to 2 hours, until the dough has doubled. Yeast "
                "eats the sugars in the flour and gives off gas, and the stretchy gluten holds it "
                "in bubbles, so warmth and time are the whole job. If it hasn't moved at all, the "
                "yeast is dead, so check the date and use water that's warm rather than hot.")
    return answer



# A bitter cup and a sour one are the same dial turned opposite ways, so they share one entry.
# The first sentence is still the user's own word: "why does my coffee taste sour" was told
# "Bitter coffee is over-extracted" and had to read on to the third sentence for its answer.
_COFFEE_BITTER = (
    "Bitter coffee is over-extracted: grind it coarser, let the water come off the boil for half "
    "a minute, and take it off the grounds sooner - about 4 minutes in a cafetiere, 25 to 30 "
    "seconds for an espresso. Sour is the same dial the other way and wants a finer grind, hotter "
    "water and a little longer. Stale beans and a dirty machine make both, and instant tastes "
    "bitter when it is made with boiling water - let the kettle rest first.")
_COFFEE_SOUR = (
    "Sour coffee is under-extracted: grind it finer, use water just off the boil rather than "
    "boiling, and give it longer on the grounds - about 4 minutes in a cafetiere, 25 to 30 "
    "seconds for an espresso. Bitter is the same dial the other way and wants a coarser grind and "
    "a shorter brew. A sour note that only shows up with milk is usually the milk.")
_COFFEE_BURNT = (
    "A burnt taste is over-extraction or too dark a roast: grind it coarser, let the water come "
    "off the boil for half a minute and shorten the brew, and try a medium roast instead of a "
    "dark one. Scrub the pot and the filter basket too, because old oils go acrid and taste "
    "burnt even with fresh beans.")


def _coffee_fault(memory, understood):
    """The fault the line named, said back to them: sour, burnt or the bitter default."""
    words = set(re.findall(r"[a-z']+", (understood or {}).get("clean") or ""))
    if words & {"sour", "soured", "acidic", "acid", "vinegary"}:
        return _COFFEE_SOUR
    if words & {"burnt", "burned", "burning", "scorched", "scorching"}:
        return _COFFEE_BURNT
    return _COFFEE_BITTER


# The leaves people keep in the fridge door - lettuce, spinach, rocket, a bag of mixed greens -
# are one subject, so the names live in one tuple that two entries share. Keeping the next bag
# crisp and bringing a limp one back are different answers, so they are separate entries:
# whichever way the line leans, the first sentence is the fix it needs.
LEAFY = ("salad", "lettuce", "leaves", "leafy", "greens", "spinach", "rocket", "arugula",
         "watercress", "salad leaves", "mixed leaves", "lambs lettuce")
# A slug, a plant in the garden and a person who is not well are not a bag of leaves: "my baby
# is limp" is a 999 line, so the words that make a line about a body or a bed take it away.
LEAFY_AVOID = ("slug", "slugs", "snail", "pest", "garden", "grow", "growing", "plant", "plants",
               # "baby spinach" is a bag of leaves, so the baby words are the possessive ones;
               # the word alone kept the commonest bag in the shop out of the answer
               # ("babies" cannot be here either: _forms() makes it a form of "baby", and it
               # would veto "baby spinach" the same way)
               "my baby", "the baby", "baby is", "baby has", "a baby", "newborn",
               "child", "children", "toddler",
               "dog", "dogs", "cat", "cats", "puppy", "feel", "feeling", "tired", "exhausted",
               "weak", "unwell", "limp after", "run",
               # "and how long does that take" is a cooking time: the composer puts the subject
               # of the turn before it back on the end ("how long does the spinach take"), so the
               # bare verb goes in too, not just the phrases
               "that take", "does that take", "will that take", "this take", "it take",
               "take", "takes", "taking", "took",
               # "i have a bag of spinach going limp, what can i do with it" is asking for a
               # dish, not for a way to crisp it up: the meal table answers those lines
               "what can i make", "what can i do with", "what should i make", "use up",
               "use it up", "recipe", "recipes", "cook", "cooking", "soup", "pan", "side dish",
               # a drink made from leaves is not a bag of leaves: "how long to infuse loose leaf
               # tea" was answered with five days in the salad drawer, because "leaf" is in this
               # subject and the tea is not
               "tea", "teas", "infuse", "infusing", "infused", "brew", "brewing", "brewed",
               "coffee")

# A pan with a *dish* burnt into it is the dish's question, not the pan's: "i burnt the garlic in
# the pan" was told to simmer bicarbonate in it, and "i burnt the bottom of a pan of rice" was
# told nothing at all, because burnt-pan avoided the word rice and fix-burnt avoided the word
# pan. The cleaning words are what tell the two apart: a line that asks how to get it off wants
# the bicarbonate, and a line that says what it burnt wants the rescue. A pan with nothing named
# burnt in it is still the pan question.
_PAN_DISH = ("rice", "sauce", "soup", "stew", "curry", "porridge", "pasta", "potatoes",
             "eggs", "chicken", "meat", "fish", "mince", "cake", "gravy", "custard", "beans",
             # an omelette, a frittata and a fried egg are dishes named for themselves, and the
             # word "pan" in the line is where they cooked rather than what is burnt: "my
             # omelette stuck to the pan" was the bicarbonate-of-soda cleaning card, and the
             # omelette rows that answer it lost to it on the registry's order alone. The dish
             # words live here so a pan line that names a dish is the dish's, which is what the
             # rest of this list already does for rice, sauce and cake.
             "omelette", "omelettes", "omelet", "omelets", "frittata", "frittatas",
             "scrambled egg", "fried egg", "poached egg", "pancake", "pancakes",
             "lentils", "chilli", "beef", "pork", "lamb", "veg", "vegetables", "noodles",
             "garlic", "onion", "onions", "bread", "steak", "bacon", "sausages", "oats",
             "tomato", "tomatoes", "mushrooms", "cheese", "butter", "oil", "toast")
_PAN_CLEAN = ("clean", "cleaning", "cleaned", "scrub", "scour", "soak", "soaking", "wash",
              "washing", "comes off", "come off", "off the bottom", "off my pan", "off the pan",
              "off the inside", "off the base", "get it off", "gets it off", "still stuck",
              "stuck on", "wont come", "won't come",
              # a tin is cleaned the same way a pan is, and "off the tin" is how people say it:
              # "how do i get the burnt off my cake tin" was answered with butter and flour
              "off the tin", "off my tin", "off the tray", "off my tray", "off the sheet",
              "get the burnt off", "burnt off", "stained")

_BURNT_PAN_REPLY = ("Put an inch of water and two tablespoons of bicarbonate of soda in it and "
                    "simmer for ten minutes, then lift the burnt layer with a wooden spoon: "
                    "almost nothing needs scrubbing after that. Stainless steel and enamel can "
                    "take a vinegar soak instead, but never scour a non-stick pan, since it "
                    "takes the coating off for good.")


# A pan with no dish named burnt in it is the pan's question, so `fix-burnt` hands those lines
# back: "food stuck to the bottom of the pan" has nothing burnt in it, and the rescue below would
# tell the person to treat their dinner as burnt.
_PAN_WORDS = ("pan", "pans", "pot", "pots", "saucepan", "saucepans", "wok", "tray", "trays",
              "casserole", "skillet")

# How a person asks for the burnt layer to come out of the pan: "get burnt milk out of a pan"
# and "get burnt sugar out of a pan" are both the pan's to clean, and the pot keeps the burnt
# dish's answer for a dish that went wrong ("i burnt the sauce in a pan").
_REMOVAL_FROM_A_PAN = ("out of the pan", "out of my pan", "out of a pan", "out of the pot",
                       "out of my pot", "out of a pot", "out of the wok", "out of the saucepan",
                       "out of the casserole", "out of it", "out of there", "get it out",
                       "get the burnt out", "get the burnt off", "get it off")

# Something burnt on a pan and to be got off it: "get burnt milk out of a pan", "how do i get
# burnt milk off the bottom of a pan", "the pan has burnt black on the outside". Each of these is
# a pan to clean, and three different entries were taking them - the oil's, because its key has a
# bare "burnt" beside "pan", the sugar's, because a burnt caramel is its own answer, and the
# burnt dish's. The thing that burnt is not what the person asked about: the pan is.
_BURNT_ON_A_PAN = _REMOVAL_FROM_A_PAN + (
    "off the pan", "off my pan", "off a pan", "off the bottom", "off my bottom", "off the base",
    "off the inside", "off the outside", "burnt on", "burned on", "burnt-on", "burnt black",
    "burned black", "black on the outside", "black on the bottom", "black outside",
    "scorched on the outside", "scorched on the bottom",
    # "how do i get rid of a scorch mark on a pan" names the pan in the middle of the line,
    # not at the end of a "get X off" phrase, and reached the oil-disposal answer.
    "on the pan", "on my pan", "on a pan", "in the pan", "in my pan", "on the saucepan",
    "on the tray", "in the tray", "on the bottom of the pan", "at the bottom of the pan",
    # The line usually says what was burnt and not how to get it off: "i burnt the bottom of a
    # pan" and "i burnt a pan" were both told the fat was past its smoke point, which is a
    # lecture about heat when the job is the soak. A pan named as burnt is the pan's question
    # however the sentence is put together.
    "burnt the bottom of", "burned the bottom of", "burnt a pan", "burned a pan",
    "burnt my pan", "burned my pan", "burnt the pan", "burned the pan", "burn the pan",
    "burnt my saucepan", "burnt the saucepan", "burnt a saucepan", "burned my saucepan",
    "burnt my pot", "burned my pot", "burnt the pot", "burnt a pot", "burnt my wok",
    "burnt the tray", "burnt my tray", "burnt the base of", "burnt a frying pan")


def _burnt_on_the_pan(text):
    """True for a pan with something burnt on it that the person wants off."""
    # "how do i get rid of a scorch mark on a pan" reached the oil-disposal answer through "get
    # rid": a mark on the pan is the pan's job, not the fat's, so a scorch, a stain and a scratch
    # count as burnt on it too.
    return (_says(text, _BURNT_ON_A_PAN)
            and _says(text, ("burnt", "burned", "black", "blackened", "scorched", "scorch",
                             "burn mark", "scorch mark", "scorched on", "stain", "stained",
                             "discoloured", "discolored", "scratch", "scratched")))

_BURNT_DISH_REPLY = ("Take it off the heat and lift out the burnt bits rather than stirring them "
                     "in, because the smoky taste spreads through everything. If it has gone all "
                     "the way through, a splash of stock and something creamy hides a little of "
                     "it, but a properly burnt sauce is better started again.")


# A joint in a tin is not a pot on a hob: "take it off the heat and lift out the burnt bits rather
# than stirring them in" was the answer to "my roast is burnt", and there is nothing to lift out of
# a roast. The meat's own rescue is to carve the burnt edge away and keep the juices off the gravy.
_BURNT_MEAT = ("roast", "joint", "chicken", "turkey", "lamb", "beef", "pork", "gammon", "duck",
               "steak", "sausage", "sausages", "bacon", "ham", "ribs", "brisket", "meatloaf",
               "meatballs", "whole chicken", "thighs", "drumsticks", "wings")
_BURNT_MEAT_REPLY = (
    "Take it out of the tin and carve or cut the black edge away rather than scraping at it, and "
    "taste a slice from the middle before you decide anything, because a joint that caught on one "
    "side is usually fine underneath. Leave the burnt fat and juices in the tin instead of pouring them "
    "into the gravy, and if the middle is still underdone, cover the joint with baking paper and "
    "give it another 10 to 15 minutes at 20C lower. Next time stand it on a rack or a bed of onion "
    "and carrot so it is not sitting in the tin, and cover it loosely once it has browned.")


# A roast potato is not a joint. "the roast potatoes burnt" was told to carve the black edge off
# and keep the burnt juices out of the gravy, because "roast" on its own is a joint word.
_BURNT_VEG = ("potato", "potatoes", "parsnip", "parsnips", "carrot", "carrots", "swede",
              "turnip", "sprouts", "broccoli", "cauliflower", "onion", "onions", "chips",
              "roast veg", "roast vegetables", "vegetables", "veg", "squash", "pumpkin",
              "courgette", "courgettes", "aubergine", "peppers", "beetroot", "sweet potato",
              "sweet potatoes", "leek", "leeks", "kale", "cabbage")
_BURNT_VEG_REPLY = (
    "Cut the black edges off with the corner of a spatula rather than scraping them, toss what is "
    "left in a fresh spoon of oil and give it 10 more minutes at 20C lower: a roast vegetable "
    "catches on the edges long before the middle. Anything black right through goes in the bin, and "
    "a tray that is badly caught is better mashed with butter than carved.")
# Batter catches as batter: a Yorkshire or a toad in the hole is a pan of hot fat and a poured
# mix, so there is nothing to lift the burnt bits out of and nothing to carve.
_BURNT_BATTER = ("yorkshire", "yorkshires", "yorkshire pudding", "yorkshire puddings",
                 "toad in the hole", "batter", "popover", "popovers", "dutch baby")
_BURNT_BATTER_REPLY = (
    "Cut the black tops off rather than scraping them and eat the rest: batter burns because the "
    "fat was smoking before it went in, or the tin sat too high. Next time put the tin on the middle "
    "shelf, get the fat hot but not smoking - a drop of batter should sizzle rather than spit - pour "
    "the batter in cold, and do not open the door for the first 20 minutes.")
# The other half of a burnt dinner: whether it is still all right to eat. "is burnt food bad for
# you", "can you eat burnt food", "does burnt meat cause cancer" and "is charred meat bad for you"
# were the pot's rescue (lift the burnt bits out), a bread card and a punt - none of them answers
# it, and the toast entry's acrylamide sentence is the only place the eating side was written.
_BURNT_EATING_ASK = ("bad for", "bad for you", "bad for me", "harmful", "dangerous",
                     "cancer", "carcinogen", "carcinogenic", "poison", "poisonous", "toxic",
                     "safe to eat", "still eat", "can i eat", "can you eat", "can i still",
                     "ok to eat", "okay to eat", "alright to eat", "healthy", "unhealthy",
                     "does it matter", "is it ok", "is it okay", "is it safe", "is it bad",
                     "is charred", "is burnt food", "burnt food bad", "charred food bad",
                     # the burnt thing named as food rather than as a dish in a pan: "what about
                     # burnt bbq food" was the grill's cleaning card, then the pan's rescue.
                     "burnt food", "burned food", "charred food", "burnt meat", "charred meat",
                     "bbq food", "barbecue food")
_BURNT_EATING_REPLY = (
    "It is not poisonous, and one burnt dinner is nothing to worry about. The black is carbon, plus "
    "acrylamide where the food was starchy - bread, potatoes, chips - and other compounds where it "
    "was meat, and the advice is about habit rather than about a single meal. So scrape the black "
    "off toast and roast potatoes and eat the rest, cut the charred edge off meat, and keep properly "
    "blackened food to the odd occasion rather than most weeks. The fat that drips onto a hot grill "
    "and smokes is best kept off the food: cook a little slower and turn things instead of leaving "
    "them in one spot.")

# The parts of a roast that are not the joint and that main's vegetable list does not name:
# they catch on top, the black comes off with a knife, and there is nothing to carve. "the
# stuffing burnt" and "the crackling burnt" got an echo, because neither word was a food this
# package knew.
_ROAST_PARTS = ("stuffing", "crackling")
_ROAST_PART_REPLY = (
    "Cut the burnt patches away and keep what is underneath - whatever caught on top is usually "
    "fine in the middle, and a black patch comes off with a knife before it goes on the plate. If "
    "what is left is dry, spoon a little stock or gravy over it, and next time put it in later "
    "than the joint, so it gets less time at the heat.")


def _burnt_dish(memory, understood):
    """The burnt dish's rescue, or nothing when the line is really about cleaning the pan.

    A dish named as what burnt is this entry's turnover; a pan on its own, with no dish in it, is
    the burnt-pan entry's line and this one declines so that entry can take it. A joint in a tin
    gets the meat's own rescue, since there is nothing in a roast to lift the burnt bits out of.
    """
    said = " ".join(str((understood or {}).get(k) or "")
                    for k in ("clean", "norm_text", "norm")).lower()
    # Whether the black is bad for the person eating it is the health question,
    # and the rescue below ("lift out the burnt bits") is about a pot still on the
    # heat. It comes before the batter and the vegetables because "are burnt roast
    # potatoes bad for you" names a vegetable and is still the eating question.
    if _says(said, _BURNT_EATING_ASK):
        return _BURNT_EATING_REPLY
    if _says(said, _BURNT_BATTER):
        return _BURNT_BATTER_REPLY
    if (_says(said, _BURNT_VEG)
            and not _says(said, ("chicken", "beef", "lamb", "pork", "turkey", "gammon", "duck",
                                 "steak", "sausage", "sausages", "bacon", "ham", "joint",
                                 "brisket", "meatballs"))):
        return _BURNT_VEG_REPLY
    # The tin comes out of the line before the joint is looked for. "my roast burnt in the oven"
    # and "the roast tin is burnt" both put a vessel word in front of a joint, and the vessel
    # check below sent the first one to the tin's answer (a roast that caught in the oven got
    # nothing at all) and would have sent the second to the meat's.
    without_vessel = _VESSEL_PHRASES.sub(" ", said)
    if _says(without_vessel, _ROAST_PARTS):
        return _ROAST_PART_REPLY
    if (_says(without_vessel, _BURNT_MEAT)
            and not _says(without_vessel, _PAN_WORDS + ("sauce", "gravy", "soup", "stew",
                                                        "curry", "rice"))):
        return _BURNT_MEAT_REPLY
    # A cake tin, a loaf tin or a baking tray is a thing to clean, and its own name carries a
    # bake's word into the food list: "my cake tin has burnt bits stuck to it" was told to take
    # it off the heat and lift the burnt bits out. The vessel comes out before the food is looked
    # for, the way `_bake_burning` already does it, and with no dish left over the line is the
    # tin's (`burnt-tin`).
    baked = _VESSEL_PHRASES.sub(" ", said)
    if _says(baked, _PAN_DISH):
        return _BURNT_DISH_REPLY
    if _says(said, _PAN_WORDS) or _says(baked, _TIN_OR_OVEN):
        return ""
    return _BURNT_DISH_REPLY


# Words that name something being *baked*, as against the tin or the oven it bakes in. A line
# with none of these is not asking about a cake: "the inside of my oven is burnt on", "my baking
# tray is burnt on how do i clean it" and "burnt on grease on the oven door" were all told to lay
# foil over the top, which is the rescue for something still in the oven and going brown. The tin
# and the oven are in the entry's key because a bake question names them, so the gate for this
# reply is whether a bake is named at all.
_BAKE_NOUNS = ("cake", "cakes", "sponge", "loaf", "bread", "buns", "biscuits", "cookies",
               "muffins", "brownies", "cheesecake", "pastry", "pie", "pies", "tart", "tarts",
               "traybake", "scones", "flapjack", "quiche", "yorkshire", "pizza", "madeira",
               "fruit cake", "victoria sponge", "bakewell")
_GRIME_WORDS = ("grease", "greasy", "stuck", "stuck on", "marks", "mark", "stains", "stained",
                "clean", "cleaning", "cleaned", "scrub", "scrubbing", "scour", "soak",
                "soaking", "bicarbonate", "get off", "get it off", "comes off", "wipe",
                "wiping", "washing", "washed")
_TIN_OR_OVEN = ("oven", "tin", "tray", "hob", "grill", "glass", "rack", "shelf", "dish",
                "plate", "pan", "cooker", "door", "inside")


# "a cake tin", "a pie dish", "a muffin tray": the bake's name is in front of the vessel, and the
# vessel is what got burnt on. So the vessel phrase comes out before the bake is looked for.
# "the oven is burnt on", "something baked on the tray": the bake name is missing and the vessel
# is what got black, so this is the cleaning question however the line is worded. Without this the
# bottom words put those lines on the bake answer and they were told to lay foil over the top.
_BURNT_ON = ("burnt on", "burned on", "baked on", "stuck on", "stuck", "black inside",
             "inside of my oven", "black on the inside", "black at the back")

_VESSEL_PHRASES = re.compile(
    r"\b(?:cake|loaf|pie|tart|muffin|bun|biscuit|bread|traybake|flan|roast|toast)\s+"
    r"(?:tins?|trays?|pans?|moulds?|molds?|dishes?|dish|sheets?|cases?|liners?|tins?)\b")


def _words_and_text(understood):
    """The line as one lower-case string, with the word list unquoted and joined by spaces.

    `norm` holds a list, and dropping it in with str() writes the brackets and quotes into the
    text, so "cake tin" came out as "cake', 'tin" and no phrase in it could be read.
    """
    parts = []
    for key in ("clean", "norm_text"):
        parts.append(str((understood or {}).get(key) or ""))
    words = (understood or {}).get("norm")
    if isinstance(words, (list, tuple)):
        parts.append(" ".join(str(word) for word in words))
    else:
        parts.append(str(words or ""))
    return " ".join(parts).lower()


def _says(said, phrases):
    """True when one of these phrases is in the line as whole words.

    Whole words, because "sauce" is not in "saucepan": a saucepan burnt inside was read as a dish
    of sauce and this entry passed the line to fix-burnt, which had nothing for it.
    """
    return re.search(r"\b(?:%s)\b" % "|".join(re.escape(one) for one in phrases), said) is not None


def _burnt_pan(memory, understood):
    """The pan's answer for a pan line, and nothing for a line whose dish is what burnt."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if _says(said, _PAN_CLEAN):
        return _BURNT_PAN_REPLY
    if _says(said, _PAN_DISH):
        return ""       # a dish is burnt, not the pan: fix-burnt has that line
    return _BURNT_PAN_REPLY


# A burnt top on a cake is not a burnt pan of sauce: nothing is stirred, and the answer is the
# oven and the foil. The pot line stays for everything that is actually in a pan.
_BAKED_BURNT = ("cake", "cakes", "sponge", "loaf", "loaves", "bread", "buns", "bun", "scones",
                "scone", "muffins", "muffin", "brownies", "brownie", "biscuits", "biscuit",
                "pastry", "pie", "tart", "quiche", "roast potatoes", "roasties", "chips", "fries")


_TIN_SIZE = ("A 2lb loaf tin is 19 x 11cm for a 900g loaf and a 1lb tin is 15 x 9.5cm for a "
             "450g one; a 20cm round cake tin takes the 4-egg sponge and an 18cm one the 3-egg.")
_TIN_FILL = ("Fill a bread tin two-thirds full and a cake tin three-quarters at most.")
_TIN_LINE = ("Line bread with baking parchment; for a cake, grease the tin and line only the base, "
             "because loose paper at the sides makes the sponge climb rather than rise.")
_TIN_GREASE = ("Rub the inside of the tin all over with butter or a little oil, then dust it with "
               "flour and tip the extra out; a circle of baking paper on the base does the same job.")
_TIN_FRUIT = ("A fruit cake or a Christmas cake wants a deep tin, not a sponge tin: a 20cm round "
              "one for a 2kg mix, lined with a double thickness of parchment and a collar of "
              "paper round the outside, because it bakes for two and a half hours or more.")
# What the line asks for comes first: a tin is three questions in the same words, and a person
# asking how to grease a tin should not have to read two sentences about loaf sizes to find it.
_TIN_GREASE_WORDS = ("grease", "greased", "greasing", "butter the", "dust with flour", "dust it")
_TIN_LINE_WORDS = ("line", "lined", "lining", "parchment", "baking paper", "greaseproof", "paper",
                   "line it", "line the")
_TIN_FRUIT_WORDS = ("fruit cake", "christmas cake", "rich fruit", "wedding cake", "simnel",
                    "dark fruit")


def _tin_answer(memory, understood):
    """Lead with the question the tin was named in: its size, its lining, or a fruit cake's tin."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if any(word in said for word in _TIN_FRUIT_WORDS):
        return " ".join((_TIN_FRUIT, _TIN_SIZE))
    if any(word in said for word in _TIN_LINE_WORDS):
        return " ".join((_TIN_LINE, _TIN_SIZE, _TIN_FILL))
    if any(word in said for word in _TIN_GREASE_WORDS):
        return " ".join((_TIN_GREASE, _TIN_SIZE))
    return " ".join((_TIN_SIZE, _TIN_FILL, _TIN_LINE))


_CAKE_FAULT_WORDS = (
    ("domed", "dome", "domes", "doming", "raised in the middle", "rises in the middle"),
    ("cracked", "cracks", "cracking", "crack", "split on top", "splits on top"),
    ("eggy", "tastes of egg", "taste of egg", "smells of egg", "egg taste", "tasting of egg"),
    ("soggy bottom", "soggy underside", "wet bottom", "soggy base"),
)


def _cake_fault(memory, understood):
    """A dome, a crack, an eggy taste and a soggy bottom are four different mistakes."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    words = said
    if any(word in words for word in _CAKE_FAULT_WORDS[0]):
        return ("A dome is the outside setting before the middle has caught up: bake 10C lower, "
                "170C (150C fan) on the middle shelf, use the tin the recipe names rather than a "
                "smaller one, and stop beating the moment the flour is in. Trim the dome flat with "
                "a bread knife before you fill it, and nobody sees it.")
    if any(word in words for word in _CAKE_FAULT_WORDS[1]):
        return ("A split top is the crust setting while the middle is still rising: lower the oven "
                "10C, put the tin on the middle shelf, and keep the door shut for the first 20 "
                "minutes. Cool it in the tin for 10 minutes, then on a rack, because a cake cooled "
                "in a hot tin goes clammy and splits.")
    if any(word in words for word in _CAKE_FAULT_WORDS[2]):
        return ("An eggy taste is too many eggs for the flour or a bake that stopped a few minutes "
                "short: add a quarter teaspoon of salt and a teaspoon of vanilla or the zest of a "
                "lemon, and give it 5 more minutes, checking with a skewer. The same mix tastes "
                "eggier cold, so try it once it has cooled rather than from the tin.")
    if any(word in words for word in _CAKE_FAULT_WORDS[3]):
        return ("A soggy bottom is underbaked underneath: use a metal tin rather than a ceramic "
                "dish, bake on the middle shelf and not above a tray of water, and give it 5 to 10 "
                "minutes longer with foil over the top once it is brown. A cold filling or a wet "
                "fruit layer under a thick batter does the same thing.")
    # the rise itself: "how do i get cakes to rise evenly"
    return ("An even rise is a level batter and a steady oven: sift the raising agent through the "
            "flour rather than adding it last, spread the batter level with the back of a spoon, "
            "and use a tin that the mix fills by two thirds. Turn the tin once, after 15 minutes, "
            "if your oven browns the back corner first.")


_PASTRY_SHRINK_WORDS = ("shrink", "shrank", "shrunk", "shrinking", "shrinks", "pulled away",
                        "pulls away", "slid down", "slides down", "slumped", "slumps",
                        "slumping", "limp")


def _pastry_fault(memory, understood):
    """A shrunken case and a soggy base are fixed in different places: the chill and the heat."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if any(word in said for word in _PASTRY_SHRINK_WORDS):
        return ("Pastry shrinks when it is stretched into the tin: press it gently into the corners "
                "rather than pulling the sides up, chill the lined case for 20 minutes before it "
                "goes in, and leave the overhang on until after baking, because the spare pastry "
                "holds the sides up while they set.")
    return ("A soggy pastry base wants more heat underneath it and less water in the filling: "
            "blind bake it 5 minutes longer than the recipe says, brush the warm base with beaten "
            "egg white before the filling goes in, and stand the tin on a hot baking sheet so the "
            "heat reaches the pastry rather than stopping at the filling.")


_BAKE_PREVENTION = (
    "Lay a sheet of foil loosely over the top as soon as it starts to colour, and turn the "
    "oven down 10 to 20C (or move the tin a shelf lower): a cake that catches on top is "
    "nearly always an oven running hot, a shelf too high or a dark tin, not the mixture. If "
    "the top is brown and the middle still wobbles, cover it and give it another 10 to 15 "
    "minutes rather than turning the heat up. If the bottom is already black, cut that off, "
    "trim the dark top and serve the rest - and next time check your oven with a thermometer, "
    "since most run 10 to 20C hotter than the dial says.")
_BAKE_BURNT = (
    "Cut or grate the black off once it has cooled, and if only the top is dark the rest is "
    "fine - a dark top on a fruit cake is often just the sugar. If the middle is still wet, "
    "cover the tin loosely with foil and give it another 10 to 15 minutes. Next time move the "
    "oven shelf down one and tent the tin with foil after 20 minutes, because a bake burns on "
    "top while the middle is still wet.")
# A burnt bottom is the other end of the oven from a burnt top, and the foil-over-the-top answer
# is no help with it: the heat came from underneath, so the fix is the shelf up, a sheet or two
# between the tin and the element, and a tin that is not black. "why do my cakes burn on the
# bottom" and "my muffins burn on the bottom" were getting the burnt-sauce card and a one-line
# fragment of the top answer.
_BAKE_BOTTOM = re.compile(r"\b(?:bottom|bottoms|underneath|underside|base of the tin)\b", re.I)
_BAKE_BOTTOM_REPLY = (
    "Lift the shelf up one, slide a baking sheet or two under the tin to take the direct heat and "
    "drop the oven 10C, because a bottom that burns first means too much heat from underneath and "
    "a hot oven burns the base while the middle is still wet. Line a dark or thin tin with baking "
    "paper, and turn the tin if one corner of the oven browns hard. If the top is browning before "
    "the middle is set, lay a sheet of foil loosely over it so the base can catch up. If the "
    "bottom has already caught, cut or grate the black off and eat the rest, and check the oven "
    "once with a thermometer, since most run 10 to 20C hotter than the dial says.")
_BAKE_STOP = re.compile(r"\b(?:stop|stops|prevent|avoid)\b|\bwhy\b", re.I)
_BAKE_DONE = re.compile(r"\b(?:burnt|burned|caught)\b", re.I)


def _bake_burning(memory, understood):
    """A bake still in the oven gets the foil; a burnt bottom gets the heat from underneath.

    "My cake is burnt" is somebody holding the cake, not somebody asking how to stop it
    catching, and the prevention answer made them read four sentences before the one that
    helps. The tense decides: "stop", "why" and "burning" are still the oven question, and
    "burnt", "burned" and "caught" are the rescue. Which end of the bake is burnt decides
    between the foil over the top and the shelf up for the bottom.

    A line with a bake in it is this entry's; a tin, tray, shelf or oven floor that is burnt on
    is the cleaning job, and with no bake named the answer here is a rescue for food nobody is
    holding - "the bottom of my oven is burnt" was told to grate the black off a fruit cake.
    """
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    # burnt grime on a tin or an oven is the cleaning question, and this reply is for something
    # still in the oven going brown. The vessel comes out of the line first, so "my cake tin is
    # burnt on" is read as the tin and not as a cake.
    text = _words_and_text(understood)
    baked = _VESSEL_PHRASES.sub(" ", text)
    if (not _says(baked, _BAKE_NOUNS) and not _says(baked, _BAKED_BURNT)
            and _says(text, _TIN_OR_OVEN)):
        return ""
    if _BAKE_BOTTOM.search(said):
        return _BAKE_BOTTOM_REPLY
    if _BAKE_STOP.search(said) or "burning" in said:
        return _BAKE_PREVENTION
    if _BAKE_DONE.search(said):
        return _BAKE_BURNT
    return _BAKE_PREVENTION


def _burnt(memory, understood):
    """What burned changes the rescue: a pan is lifted off the heat, a bake is cut and covered."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    said = " ".join(words)
    if any(_same(word, bake) for word in words for bake in _BAKED_BURNT) or any(
            " " in bake and bake in said for bake in _BAKED_BURNT):
        return ("A burnt top on a bake is usually saveable: take it out at once, cover the tin loosely "
                "with foil so the middle carries on cooking, and when it is cool cut the black off "
                "with a serrated knife or grate it away - a dark top on a fruit cake is often just "
                "the sugar. Next time move the shelf down one, drop the oven 10C and tent the tin with "
                "foil after 20 minutes, because a bake burns on top while the middle is still wet.")
    if any(word in ("toast", "toaster") for word in words):
        return ("Scrape the black off with a knife and eat the rest: burnt toast is not dangerous, and "
                "a scrape takes the bitter taste with it. Next time set the toaster one notch lower "
                "and stay next to it, because toast goes from golden to black in under a minute.")
    return ("Take it off the heat and lift out the burnt bits rather than stirring them in, because "
            "the smoky taste spreads through everything. If it has gone all the way through, a splash "
            "of stock and something creamy hides a little of it, but a properly burnt sauce is better "
            "started again.")


# Greasy is one word and four different faults: frying oil that was not hot enough, fat left on a
# stew, a roast sitting in its own tin, and a wet filling under pastry. The food in the line picks
# the fix, so a person who says "my chips are greasy" is not told to skim a stew.
_FRIED_GREASY = ("chips", "chip", "fries", "fry", "pakora", "pakoras", "onion rings", "doughnut",
                 "doughnuts", "tempura", "batter", "fried", "sweet potato fries")
_POT_GREASY = ("stew", "curry", "sauce", "soup", "gravy", "chilli", "bolo", "bolognese", "ragu",
               "casserole", "dal", "daal", "stir fry", "stirfry", "stir-fry", "mince")
_MEAT_GREASY = ("roast", "chicken", "steak", "lamb", "pork", "beef", "sausage", "sausages",
                "bacon", "duck", "turkey", "gammon", "burger", "burgers", "meatballs")
_PASTRY_GREASY = ("quiche", "pie", "tart", "pastry", "pastry case", "flan")


def _greasy(memory, understood):
    """Greasy food, with the cause the food actually has."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    said = " ".join(words)
    have = lambda names: (any(_same(word, wanted) for word in words for wanted in names)  # noqa: E731
                          or any(" " in wanted and wanted in said for wanted in names))
    if have(_FRIED_GREASY):
        return ("Greasy fried food means the oil was not hot enough, so the food steamed instead of "
                "sealing and took the fat up like a sponge: 180C for chips and about 190C for a "
                "batter, test it with a cube of bread that should sizzle and go golden in 30 seconds, "
                "and do not crowd the pan, because the temperature drops as soon as it is full. "
                "Drain on a rack or kitchen paper, never on a plate, and salt it the moment it comes out.")
    if any(_same(word, wanted) for word in words
           for wanted in ("roast potatoes", "roasties", "potatoes", "potato", "wedges",
                          "hash browns")) and any(_same(word, wanted) for word in words
                                                  for wanted in ("roast", "roasted", "oven")):
        return ("Greasy roast potatoes mean the oil was not hot enough or the tin was crowded: parboil "
                "them 8 minutes, drain and shake the pan to rough the edges, then roast them in a "
                "thin layer of oil that is already smoking hot at 200C (180C fan), in one layer with "
                "room between them. Cold oil, or a full tin, is what leaves them oily, and a rack "
                "over the tin drains the rest.")
    if have(_PASTRY_GREASY):
        return ("A greasy pastry case is the filling rather than the pastry: cheese in a quiche gives "
                "up its fat, and mince in a pie floats it to the top. Drain the cooked filling in a "
                "sieve over a bowl, thicken it with a spoon of cornflour, and blind-bake the case "
                "first so the fat has somewhere to go; a layer of breadcrumbs on the base soaks up "
                "the rest.")
    if have(_MEAT_GREASY):
        return ("Most of that fat is meant to be there, so spoon it off rather than cook it away: tilt "
                "the tin and take the fat out with a spoon or a bulb baster, keeping a spoonful for "
                "the potatoes, and finish the meat uncovered at a higher heat for the last 10 minutes "
                "so the skin or the outside crisps. Resting it on a rack, not in the tin, keeps it "
                "out of the fat.")
    if have(_POT_GREASY):
        return ("Skim the fat off the top with a spoon, or lay a piece of kitchen paper flat on the "
                "surface and lift it out - that takes the oil and leaves the sauce. A stew that is "
                "still greasy wants the lid off for 10 minutes, and a spoon of something sharp "
                "(lemon, vinegar, tomato puree) cuts through what is left. Next time brown the meat "
                "and pour the fat out of the pan before the liquid goes in.")
    return ("Greasy comes from too much oil or oil that was not hot enough to seal the food: get the "
            "pan properly hot before anything goes in, shake the excess off in a sieve, and drain on "
            "kitchen paper rather than on a plate. In a sauce, skim the fat off the top with a spoon "
            "and finish with a squeeze of lemon.")


# A curdled custard is a broken emulsion's cousin with a different cause: the eggs got hot too
# fast and the protein in them set into grains, so the rescue is a sieve and a cooler pan.
_CUSTARD_NAMES = ("custard", "custards", "creme anglaise", "crème anglaise", "creme patissiere",
                  "crème pâtissière", "pastry cream", "custard tart", "custard tarts",
                  "custard filling", "creme caramel", "crème caramel")


def _split(memory, understood):
    """A split sauce has three different causes: heat, oil added too fast, and butter too hot."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    said = " ".join(words)
    if any(_same(word, name) for word in words for name in _CUSTARD_NAMES) or any(
            " " in name and name in said for name in _CUSTARD_NAMES):
        return ("A curdled custard is the eggs getting hot too fast, so the protein in them sets "
                "into grains: take it off the heat at once, whisk in a spoonful of cold cream or "
                "milk to stop it cooking, then push it through a sieve and it comes back smooth. "
                "Next time pour the hot milk into the beaten eggs a splash at a time, keep the pan "
                "over a low heat, stir all the time, and take it off at 82C, because a custard that "
                "comes to the boil will always curdle.")
    if any(word in ("mayonnaise", "mayo", "aioli", "garlic mayo", "garlic mayonnaise", "remoulade")
           for word in words):
        return ("Mayonnaise splits when the oil goes in faster than the yolk can take it up, so start "
                "again with a clean bowl: an egg yolk, a teaspoon of water and a pinch of salt, then "
                "the oil a drop at a time until it thickens and only then in a thin stream. To rescue "
                "a split one, put a fresh yolk in a clean bowl and whisk the split mayonnaise into it "
                "a spoon at a time - one yolk will bring back up to about a mugful.")
    if any(word in ("hollandaise", "béarnaise", "bearnaise", "butter sauce") for word in words):
        return ("Hollandaise splits when the bowl gets too warm or the butter goes in too hot: take "
                "the bowl off the water at once, add a teaspoon of cold water and whisk hard. If it "
                "will not come back, start a fresh yolk in a clean bowl with a spoon of water and "
                "whisk the split sauce into it a little at a time, off the heat. Next time keep the "
                "water barely trembling and let the melted butter cool for a minute first.")
    return ("A sauce splits when it gets too hot: take it off the heat and whisk in a spoonful of cold "
            "cream or butter to bring it back. Next time, lower the heat and add dairy at the end.")


# Undercooked is the other half of the fault table: a cake wet in the middle, rice still crunchy, a
# potato hard at the centre. What to do about it is the food's own next step, never one line.
_UNDER_BAKE = ("cake", "cakes", "sponge", "muffin", "muffins", "loaf", "loaves", "bread", "buns",
               "bun", "scone", "scones", "brownie", "brownies", "traybake", "yorkshire",
               "yorkshires", "pudding", "puddings", "pie", "tart", "quiche")
_UNDER_BREAD = ("bread", "loaf", "loaves", "sourdough", "bread roll", "bread rolls")
_UNDER_STARCH = ("rice", "couscous", "quinoa", "bulgur", "bulghur", "barley", "lentils", "lentil",
                 "porridge", "oats", "polenta", "pasta", "noodles", "noodle", "spaghetti",
                 "macaroni", "penne", "tagliatelle", "gnocchi", "dumplings", "dumpling")
_UNDER_VEG = ("vegetables", "vegetable", "veg", "greens", "potato", "potatoes", "carrots", "carrot", "parsnips", "parsnip", "swede", "turnip",
              "sprouts", "broccoli", "cauliflower", "cabbage", "beans", "peas", "leeks", "leek",
              "beetroot", "squash", "pumpkin", "courgette", "courgettes", "aubergine")


def _undercooked(memory, understood):
    """What is still hard changes the next step: a bake goes back in the oven, rice wants water."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    said = " ".join(words)
    have = lambda names: (any(_same(word, wanted) for word in words for wanted in names)  # noqa: E731
                          or any(" " in wanted and wanted in said for wanted in names))
    if have(_UNDER_BREAD):
        return ("A doughy loaf has not had long enough in the oven, or it did not prove enough: put it "
                "back in at 200C (180C fan) for 10 minutes, then turn it out and tap the base - a "
                "hollow sound means it is done, a dull thud means it wants 5 more. Next time let it "
                "prove until a poke springs back slowly and bake it to 96C in the middle rather than "
                "trusting the time on the packet.")
    if have(_UNDER_BAKE):
        return ("Put it back in the oven at 160C (140C fan) for 10 minutes with a sheet of foil "
                "loosely over the top, so the middle catches up without the top burning, and test it "
                "again with a skewer: it wants a few damp crumbs, not wet mixture. Next time drop "
                "the oven 10C and give it 5 minutes longer, and check with a skewer before you take "
                "it out - a cake that looks set and wobbles in the middle is not done.")
    if have(_UNDER_STARCH):
        return ("It wants more time and a little more water: a splash of hot water, the lid back on "
                "and 5 minutes on the lowest heat will finish rice, couscous or quinoa. Pasta and "
                "noodles go back into the boiling water for 2 to 3 minutes, and lentils want another "
                "10. Taste a piece rather than looking at the clock, because the packet time assumes "
                "a pan that came back to the boil quickly.")
    if have(_UNDER_VEG):
        return ("Boiled vegetables go hard in the middle when the pieces are different sizes or the "
                "water never got back to a rolling boil: cut them the same size, salt the water, and "
                "give them another 5 minutes, testing with the point of a knife - it should slide in "
                "with no resistance at all. Roast ones want 10 more minutes in a hotter oven, and "
                "parboiling potatoes for 8 minutes before they go in the tin stops the hard centre.")
    return ("It needs a few more minutes rather than more heat: cover it and give it 5, then test it "
            "with a knife or a skewer in the middle, where the heat gets last. A wider, shallower "
            "dish cooks through faster than a deep one.")
# The dip a line names decides the words it gets: houmous thickens in the fridge, tzatziki goes
# thin from a wet cucumber, and a split aioli comes back. Anything else gets the plain advice.
_DIP_FIXES = (
    (("houmous", "hummus", "humous"),
     "Houmous thickens in the fridge, so loosen it with a spoonful of cold water or lemon juice "
     "and a little more oil, taste for salt, and serve it at room temperature."),
    (("tzatziki", "raita", "yogurt dip", "yoghurt dip"),
     "Sit it in a sieve over a bowl for twenty minutes: thin tzatziki or raita is nearly always a "
     "wet cucumber, so squeeze the grated cucumber dry and stir it back in with a pinch of salt."),
    (("aioli", "mayonnaise", "mayo"),
     "A thin mayonnaise takes more oil whisked in slowly; a split one comes back from a fresh "
     "yolk in a clean bowl with the split mixture drizzled in a few drops at a time."),
    (("guacamole",),
     "Guacamole browns where the air gets at it: press cling film right onto the surface, keep "
     "the stone in the bowl if you have one, and a squeeze of lime slows it down. It is still "
     "fine to eat brown."),
    (("salsa",),
     "Drain the chopped tomato in a sieve for ten minutes and salt it at the end: salsa goes "
     "watery from the tomato juice, and a spoonful of tomato puree thickens what is left."),
    (("baba ganoush", "tapenade"),
     "It wants balancing rather than more of anything: a squeeze of lemon and a little olive oil "
     "stirred in slowly will loosen it, and salt and lemon are what it usually lacks."),
)

_DIP_PLAIN = ("A cold dip is put right cold, so leave the pan alone: a spoonful of water or lemon "
              "loosens it, a pinch of salt and twenty minutes in a sieve thickens it, and a little "
              "oil whisked in slowly brings back one that has split.")


OIL_SMOKE_POINTS = (
    ("butter, or clarified butter", "about 150C"),
    ("extra virgin olive oil", "about 180 to 200C"),
    ("a plain or light olive oil", "about 200 to 240C"),
    ("rapeseed, sunflower or vegetable oil", "about 220 to 230C"),
    ("groundnut or rice bran oil", "about 230C"),
)


# A fat that has landed on a person is a scald, not a pan temperature: "hot oil splashed on my
# arm" was answered with "Around 180C for most frying, 170C for chips", which is advice about the
# pan given to somebody who has just been burnt. The body part and a splash word together are the
# line that says so, and health.py's scald row has the twenty minutes of cool water.
_BODY_PART = re.compile(
    r"\b(?:arm|arms|hand|hands|finger|fingers|thumb|thumbs|foot|feet|toe|toes|wrist|wrists|"
    r"leg|legs|chest|tummy|stomach|belly|lap|neck|shoulder|shoulders|eye|eyes|face|skin|"
    r"baby|child|toddler|kid)\b")
_ONTO_A_PERSON = ("splashed", "splashes", "splash", "spat", "spits", "spitting", "spit",
                  "flicked", "jumped out", "pops", "popped", "scalded", "burnt my", "burned my",
                  "burnt me", "burnt himself", "burnt herself", "burned me")


def _a_dish_with_a_heat(text):
    """True when the line names a dish the dish table has an oven heat for."""
    from . import dishes
    plan = dishes.PLANS.get(dishes.dish_in(str(text or "")) or "")
    return bool(isinstance(plan, dict) and plan.get("temp"))


def _fat_has_landed_on_a_person(text):
    """True when the line is about a fat on a body, which is first aid and not the pan."""
    return bool(_BODY_PART.search(text)) and any(word in text for word in _ONTO_A_PERSON)


# What a line has to say for the fat to be the fault: it is smoking, burning, foaming, spitting
# or too hot. The row's key can be reached on its subject alone, and the default answer is about a
# fire, so the fire (or the heat on the way to it) has to be named.
_SOMETHING_IS_WRONG_WITH_THE_PAN = (
    "smoke", "smokes", "smoking", "smoked", "smoky", "smoke point", "smoking point",
    "burnt", "burn", "burns", "burning", "burned", "too hot", "overheat", "overheating",
    "on fire", "caught fire", "in flames", "flaming", "flamed", "black", "spoiled",
    "ruined", "wasted", "not right", "gone wrong", "tastes", "taste", "smell", "smells",
    "stinks", "bubbling", "bubbles", "foam", "foams", "foaming", "foamy",
    "spat", "spits", "spitting", "spattered", "splashed", "jumped out", "popped",
)


def _oil_smoking(memory, understood):
    """Why the fat is smoking, and what to do with the pan and the bottle."""
    understood = understood if isinstance(understood, dict) else {}
    text = str(understood.get("clean") or understood.get("text") or "").lower()
    if _fat_has_landed_on_a_person(text):
        return ""
    # A pan with something burnt on it is the pan's question, not the fat's: "the pan has burnt
    # black on the outside" and "how do i get burnt milk off the bottom of a pan" were both told
    # the fat was past its smoke point, which is a lecture about a fire when the job is a soak.
    if _burnt_on_the_pan(text):
        return ""
    if _says(text, ("smoke point", "smoking point", "smokes at", "smoke at", "smoke too")):
        return ("Every fat has a smoke point: " + "; ".join(
            f"{name} {temp}" for name, temp in OIL_SMOKE_POINTS) +
            ". Above that it is breaking down, so keep the pan under it - a thermometer takes the "
            "guesswork out, and a drop of the oil in a cold pan, brought up slowly, tells you when "
            "it is ready.")
    # Pan first or oil first is the same subject as the heat of the fat, and "when do i put the
    # oil in the pan" was the car's dipstick: a wick of engine oil in an engine that is off.
    # The fat going into water is not the pan at all. "Should i put oil in pasta water" reached
    # the pan-order arm's own words and was told the fat was past its smoke point, because the
    # question is about the pot and the water rather than a hot pan; the pot of water is another
    # row's question, so this one stands down.
    if _says(text, ("in the water", "pasta water", "rice water", "boiling water", "the water for",
                    "water for the pasta", "water for the rice", "in the pot of water",
                    "into the water", "salt water", "salted water", "the pasta water")):
        return ""
    if _says(text, ("put the oil in", "put in the oil", "add the oil", "adding the oil",
                    # people leave the article out: "should i preheat the pan before adding oil"
                    # was a "can't call that one" while the order was sitting in this arm
                    "put oil in", "add oil to", "adding oil", "add oil",
                    "oil go in", "oil goes in", "oil first or the pan", "pan first",
                    "oil in the pan", "oil in a pan", "oil in pan",
                    "hot pan first",
                    # "should the pan be hot before the oil" was a punt: the order is the
                    # question and the words that ask it are the pan and the heat, not "put"
                    "pan be hot", "pan hot before", "before the oil", "before adding the oil",
                    "before adding oil", "hot pan",
                    "pan hot before", "when do i add the oil")):
        return ("Pan first, then the oil: a dry pan heats faster and you can watch the oil for the "
                "heat - it thins and shimmers at about 180C, and a cube of bread turns golden in 30 "
                "seconds. Give the oil 20 seconds before the food goes in. Cold oil in a cold pan "
                "is for rendering fat, not a sear.")
    # "What temperature for chips" is the dish's own heat, not the fat's: this arm claimed every
    # "what temperature for ..." line, so the dish table never got its turn. When the line names a
    # dish that has a heat of its own, and nothing hot in it (no fat, no pan, no fry), the dish
    # answers it.
    if not _says(text, ("oil", "fat", "pan", "fry", "frying", "deep fry", "chip pan",
                         "dripping", "lard", "ghee", "wok")) and _a_dish_with_a_heat(text):
        return ""
    if _says(text, ("how hot", "hot enough", "what temperature", "temperature for", "hot should",
                    "heat of the oil", "temperature does",
                    # the same question with the word left out: "how do i know when the pan is
                    # hot" reaches the row on the key and was then told the fat had passed its
                    # smoke point, which is the answer to a pan that is already too hot
                    "is hot", "is ready", "pan heat", "the heat", "test the heat",
                    "check the heat", "hot oil", "oil is hot", "oil is ready", "fat is hot",
                    "fat is ready", "heat the pan", "heating the pan", "heat the oil",
                    "heating the oil")):
        # The number people want is the oil's own heat, and the bread cube is the thermometer most
        # kitchens have. The smoke points follow, because that is the ceiling on it.
        # The number first, the bread cube as the thermometer most kitchens have, then the ceiling
        # on it. Kept to the two sentences someone will read before the pan overheats.
        return ("Around 180C for most frying, 170C for chips so they cook through before they "
                "colour; with no thermometer a cube of day-old bread turns golden in about 30 "
                "seconds. Heat the oil with nothing in it and fry in small batches so it does not "
                "drop. Stay under the fat's smoke point: "
                + "; ".join(f"{name} {temp}" for name, temp in OIL_SMOKE_POINTS[:1] + OIL_SMOKE_POINTS[2:4])
                + ".")
    # ...and only with a fat named: "where do i put a hot pan" is a question about the surface
    # under it, and there is nothing in it to pour into a bottle. This is the disposal arm''s
    # condition alone - "my pan is smoking" names no fat and is still the pan - so it is a flag
    # rather than a stand-down for the whole row.
    _fat_named = _says(text, ("oil", "fat", "dripping", "lard", "ghee", "grease", "butter"))
    if _fat_named and _says(text, ("down the sink", "down the drain", "down the toilet",
                                   "down the loo", "down the plug hole", "down the plughole")):
        # "can i pour oil down the sink" is a yes or no, and the general disposal arm below
        # answers a where: it opened on the bottle and reached "never down the sink" third. The
        # no is the first word here, and the why is one clause.
        return ("No - never down the sink, the loo or the drain: fat sets hard as it cools and "
                "closes the pipe, and hot water only pushes it further down to block somewhere "
                "worse, which is a plumber's bill. Let it cool, pour it into the bottle or a jar "
                "you were going to bin, and put that in the rubbish; wipe the pan out with kitchen "
                "roll before you wash it.")
    if _fat_named and _says(text, ("throw out", "throw away", "throwing out", "get rid", "getting rid",
                    "dispose", "disposal", "bin it", "bin used", "bin the oil", "recycle",
                    "recycling", "down the sink", "where do i put", "where do i pour",
                    "what to do with",
                    "where does it go", "where can i put", "put used", "pour it", "pour old",
                    # "what do i do with old oil" reached the entry and was answered as a pan
                    # that had smoked: the question is the bottle, and "do with" is the ask.
                    "do with old oil", "do with used oil", "do with the oil", "do with the fat",
                    "do with leftover oil", "what do i do with", "where does it go", "pour it",
                    "pour the oil", "tip it")):
        # "how do i get rid of used cooking oil" was answered with which oil to cook with: the
        # bottle, not the pan, is the question, and the one thing not to do is the sink.
        return ("Let it cool completely, then funnel it back into the bottle it came in or any "
                "screw-top jar you were going to bin, and put that in the rubbish - never down the "
                "sink, because it sets in the drain and it is what makes fatbergs. A small amount "
                "from one pan can be soaked up with kitchen roll and binned; a big batch goes to "
                "the tip, and most councils and some supermarkets take used cooking oil for "
                "recycling. Keep a jar under the sink and pour into it while it is still warm, and "
                "it never gets as far as the drain.")
    if _says(text, ("reuse", "re-use", "again", "second time", "keep the oil", "straining",
                    "strain", "can i use", "can i still use", "still use", "still good",
                    "fine to use", "ok to use", "okay to use", "fry in", "fry with")):
        # the action is the answer, so it leads: "is it safe to reuse oil" was opening with the
        # chemistry and stopping there when the sentence was trimmed as a repeat.
        return ("Let it cool, strain it through a fine sieve or a coffee filter, and use it once "
                "more for something at a lower heat. Oil that has smoked has started to break "
                "down, so it will taste acrid and it will smoke sooner next time; bin it if it "
                "smells bitter or looks dark and sticky.")
    if _says(text, ("foam", "foams", "foamy", "foaming", "foamed", "bubbling up", "bubbles up",
                    "spitting",
                    "spits", "spattered", "spattering")):
        # Foam is water, not heat: the food went in wet, the pan was overcrowded, or the oil has
        # been used too often and its breakdown products are foaming.
        return ("Oil that foams has water in it rather than too much heat: dry the food with kitchen "
                "paper and lower it in gently, cook in two batches so the pan does not drop below "
                "its temperature, and keep the lid or the basket dry. If oil you have already used "
                "a few times foams as soon as anything goes in, it is spent - let it cool, bin it "
                "in a bottle, and start with fresh.")
    # A row that answers a fault falls back on the fault, so the default answer is only for a
    # line that says something is wrong. The key takes two signals and one of them can be a plain
    # subject word: "should i put oil in pasta water" reached the pan-order arm's subject and no
    # arm applied, so it was told the fat was past its smoke point - a lecture about a fire
    # nobody has. Naming the trouble is what earns the fault card; a line that only says where
    # the oil goes is another row's question, or nobody's.
    if not _says(text, _SOMETHING_IS_WRONG_WITH_THE_PAN):
        return ""
    return ("The fat is past its smoke point, so turn the heat down and take the pan off the ring "
            "for a minute rather than carrying on. Open a window or put the extractor on, and once "
            "it has cooled wipe the pan out and start again with fresh fat - the smoked oil has "
            "turned acrid and it will make the food taste of it. Butter and extra virgin olive oil "
            "smoke first (about 150C and 180C), so use a plain vegetable oil or clarified butter "
            "when you want the pan very hot. If it ever actually catches, put a lid or a baking "
            "tray over the pan and turn the heat off - never water.")


def _dip_fault(understood):
    """The one sentence that fixes the dip the line named."""
    text = ((understood or {}).get("clean") or "").lower()
    # Houmous has two opposite faults, so it cannot share one sentence: a thick pot wants
    # loosening, but a watery one wants draining and tahini. The old reply answered both with
    # "loosen it with cold water", which is the wrong way round for half the people who ask.
    if any(name in text for name in ("houmous", "hummus", "humous")):
        if any(word in text for word in ("watery", "too thin", "runny", " thin")):
            return ("Watery houmous usually has too much liquid or not enough tahini: drain the "
                    "chickpeas well, then stir in a spoonful of tahini and a little olive oil and "
                    "chill it for 20 minutes, because it firms up cold. Taste for salt and lemon "
                    "at the end.")
    for names, fix in _DIP_FIXES:
        if any(name in text for name in names):
            return fix
    return _DIP_PLAIN


_SOGGY_BREAD = ("sandwich", "sandwiches", "wrap", "wraps", "roll", "rolls", "baguette", "sub",
                "subs", "ciabatta", "pitta", "pita", "tortilla", "toastie", "butty", "butties",
                "bread", "loaf", "bun", "buns", "brioche", "focaccia", "sourdough")
# The leaves are the other family, and a watery salad is the same water as a watery coleslaw.
_SOGGY_LEAF = ("salad", "salads", "lettuce", "leaves", "coleslaw", "slaw", "pasta salad",
               "greens", "spinach", "rocket", "cucumber", "tomato", "tomatoes")


def _soggy_lunch(memory, understood):
    """A wet sandwich and a wet salad are both water in the wrong place, but not the same fix."""
    words = [str(word).lower() for word in ((understood or {}).get("words") or [])]
    said = " ".join(words)

    def _names(family):
        return (any(_same(word, name) for word in words for name in family)
                or any(" " in name and name in said for name in family))

    if _names(_SOGGY_BREAD):
        return ("A sandwich goes soggy because the wet filling soaks into the bread: butter both "
                "slices right to the edges first, or spread mayonnaise or soft cheese as a "
                "barrier, and keep tomato, cucumber and lettuce in the middle rather than against "
                "the bread. Packed in the morning, the wet things go in a separate tub and are "
                "added at lunchtime, which is the only thing that really works on a hot day.")
    if _names(_SOGGY_LEAF):
        return ("A salad goes soggy because the leaves are still wet or the dressing went on early: "
                "dry them properly in a tea towel or a salad spinner, dress it at the table, and keep "
                "the wet things - tomato, cucumber, dressing - at the bottom of the bowl until you "
                "eat. Salt draws the water out too, so season it in the last minute rather than "
                "ahead.")
    # Nothing named at all - a soggy lunchbox, a lunch that went wet - is water getting in, and
    # the fix is the same either way.
    return ("A packed lunch goes soggy because water gets in from somewhere. Keep the wet things "
            "- tomato, cucumber, dressing, a drink - in their own tub and stand the leaky ones "
            "upright, put a layer of kitchen paper or a lettuce leaf under the bread, and pack the "
            "dry things on top. A leaking drink and a damp fork do more damage than a whole "
            "morning in the bag.")

_BAKE_FOLLOW_SHAPES = ("what did i do wrong", "what went wrong", "why did that happen",
                       "why does that happen", "why did it happen", "what else could it be",
                       "why did they sink", "why did it sink", "why did that sink",
                       "why did some of them sink", "why do they sink", "why does it sink",
                       "how do i stop that next time", "how do i stop it next time",
                       "stop it next time", "what should i do differently",
                       "how do i get it right", "will it happen again", "what do i change",
                       "what could i do differently next time",
                       "can i still use it", "can i still eat it", "can i still use them",
                       "is it still ok", "are they still ok", "how do i use it up",
                       "what do i do with it now")
_NEXT_SHAPES = ("stop", "differently", "next time", "get it right", "happen again",
                "what do i change")
_USE_SHAPES = ("still use", "still eat", "still ok", "use it up", "what do i do with")
_BAKE_KEEP_SHAPES = ("how long does it keep", "how long will it keep", "how long do they keep",
                     "how long will they keep", "how long does it last", "how long will it last",
                     "how long do they last", "how long will they last", "will it keep",
                     "do they keep", "will they last")


def _bake_keep_sentence(bakes):
    """The keeping sentence for the bakes named in these turns, or the cake's when unnamed."""
    said = " ".join(bakes)
    if any(word in said for word in ("scone", "scones", "biscuit", "biscuits", "cookie",
                                     "cookies", "shortbread")):
        return ("Scones and biscuits are at their best the day they are baked and keep 2 days in "
                "a tin; freeze them baked for 2 months and warm them through for 5 minutes at "
                "150C, which brings back most of the crust.")
    if any(word in said for word in ("bread", "loaf", "loaves", "sourdough", "bun", "buns",
                                     "roll", "rolls", "focaccia", "baguette")):
        return ("Bread keeps 2 to 3 days in a paper bag or a bread bin, cut side down, and a "
                "month in the freezer sliced; the fridge is what makes it stale fastest, so "
                "freeze what you will not eat in two days.")
    if "cupcake" in said or "muffin" in said:
        return ("Cupcakes and muffins keep 2 to 3 days in a tin, best the day they are baked, "
                "and they freeze well undecorated for 2 months: defrost them at room "
                "temperature in a single layer.")
    return ("A cake keeps 3 days in a tin, or freezes for 2 months undecorated; a crumbly or "
            "dry one is best eaten in the next day or two, or frozen in slices.")


def _bake_keep(memory, reading):
    """The keeping sentence for the bake named in the last few turns, or "" when none was."""
    line = str((reading or {}).get("text") or (reading or {}).get("clean") or "").lower()
    if not any(shape in line for shape in _BAKE_KEEP_SHAPES):
        return ""
    turns = (memory or {}).get("turns") or []
    for turn in reversed(turns[-3:]):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        if not any(name in said for name in _BAKED):
            continue
        if "cupcake" in said or "muffin" in said:
            return _bake_keep_sentence([said])
        return ""
    return ""


def _bake_follow(memory, reading):
    """The cause, the next-time fix or the rescue for the bake fault named a turn ago, or ""."""
    line = str((reading or {}).get("text") or (reading or {}).get("clean") or "").lower()
    if not any(shape in line for shape in _BAKE_FOLLOW_SHAPES):
        return ""
    turns = (memory or {}).get("turns") or []
    bakes = []
    for turn in reversed(turns[-3:]):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        if any(name in said for name in _BAKED):
            bakes.append(said)
    if not bakes:
        return ""
    family = None
    for said in [line] + bakes:
        for candidate in _BAKE_FAULT_FAMILIES:
            if any(word in said for word in candidate[0]):
                family = candidate
                break
        if family is not None:
            break
    if family is None:
        if any(shape in line for shape in _USE_SHAPES + _BAKE_KEEP_SHAPES):
            return _bake_keep_sentence(bakes)
        return ""
    _, cause, cure, rescue = family
    if any(shape in line for shape in _USE_SHAPES):
        return f"It is still worth eating: {rescue}."
    if any(shape in line for shape in _NEXT_SHAPES):
        if not cause[0].isupper():
            cause = cause[0].upper() + cause[1:]
        return f"Next time, {cure}. {cause}."
    return f"{cause}. {cure[0].upper() + cure[1:]}."


_BREAD_WORDS = ("bread", "loaf", "loaves", "sourdough", "bun", "buns", "roll", "rolls", "baguette",
                "focaccia", "pitta", "pita", "brioche", "ciabatta")
_GUMMY_CAKE = ("Gummy means it needed longer, not a hotter oven: the outside set while the middle "
               "was still wet. Give it another 5 to 10 minutes at the same heat with foil over the "
               "top, and test the centre with a skewer, not the edge.")
_GUMMY_BREAD = ("A gummy loaf is under-baked rather than under-proved: tap the base for a hollow "
                "sound, and if the middle feels heavy put it back for 10 minutes at the same heat. "
                "Next time prove until a floured finger springs back slowly.")


def _gummy(memory, understood):
    """The bake the line names decides the answer: bread sets by its bake, a cake by its batter."""
    clean = (understood.get("clean") or "").lower()
    if any(re.search(r"(?<![a-z])" + word + r"(?![a-z])", clean) for word in _BREAD_WORDS):
        return _GUMMY_BREAD
    return _GUMMY_CAKE





# The list of questions lives in cooking_entries.py: this file was over the world's 1 MB upload
# limit and a list of data is the cheapest thing to move. It is copied back here, in place, so
# everything below sees the entries exactly as it did before.
from .cooking_entries import ENTRIES as _LISTED_ENTRIES
from .cooking_entries import NO_SUGAR as _NO_SUGAR

ENTRIES = list(_LISTED_ENTRIES)


# ---------------------------------------------------------- what kinds a thing comes in
# The shape is read once, in bot/knowledge/lookup.py (`KINDS_WORDS`, `asks_the_kinds`); a subject
# is data here. What was wrong on main: "what kinds of tea are there" was answered with a dinner
# pick, and pasta, oil, honey, milk, beans, lettuce, wine, coffee and yoghurt were answered with a
# search hedge, because the rows that knew the subject knew one of its kinds (brewing a cup,
# frying an egg) and no row knew the question. The ask is for the families a thing comes in.
#
# Only the subjects nothing else answers are here. A subject whose card already names the families
# (potato, apple, rice, cheese, mushroom, onion, tomato, flour, chocolate) keeps that card: it
# answers the shape, and a second answer for the same ask would only be longer.
#
# (the line's subject words, the subject for the row's id, the answer)
_KINDS = (
    (("tea", "teas"), "tea",
     "Black, green, white and oolong are the same leaf, picked and processed differently: black "
     "is fully oxidised and malty, green is steamed or pan-fired and grassy, white is the young "
     "leaf dried, and oolong sits between green and black. Everything else - peppermint, "
     "chamomile, rooibos, fruit - is a herbal infusion rather than tea, so it brews and keeps "
     "differently."),
    (("pasta", "pastas"), "pasta",
     "Long pasta - spaghetti, linguine, tagliatelle - is for thin sauces that coat it. Short "
     "shapes - penne, fusilli, rigatoni - hold chunkier sauces, and the ridges and tubes are there "
     "to catch them. Filled pasta - ravioli, tortellini - is a meal with its sauce inside. Dried "
     "is durum wheat and water; fresh is egg and soft wheat, cooks in two or three minutes, and "
     "is richer. Wholewheat is the same shapes with the bran left in, and takes a minute longer."),
    (("oil", "oils"), "oil",
     "Olive oil splits in two: extra virgin is the cold-pressed first press, peppery and best "
     "raw or for low heat, and ordinary olive oil is refined, plainer and fine for frying. "
     "Rapeseed is the mild all-rounder and the cheapest British one. Sunflower and vegetable oil "
     "are neutral and take high heat, which is what chips and stir-fries want. Sesame is for "
     "flavour, a teaspoon at the end, and coconut oil tastes of coconut. Groundnut oil is the "
     "one restaurants fry in, because it is neutral and stable when hot."),
    (("honey", "honeys"), "honey",
     "It is named for the flower the bees worked: clover and acacia are light and mild, heather "
     "and chestnut are dark and strong, and orange blossom is perfumed. Runny or set is the same "
     "honey - set has simply crystallised, which a warm jug of water undoes. Raw or unfiltered "
     "means it has not been heated, so it is cloudier and tastes more of the flowers. Never give "
     "any honey to a baby under one, because of the botulism risk."),
    (("milk", "milks"), "milk",
     "Cow's milk comes by fat: whole at about 3.5%, semi-skimmed at 1.7% and skimmed at almost "
     "nothing, and the fat is what carries the taste in coffee and sauces. Fresh and UHT are the "
     "same milk, one pasteurised hotter so it keeps for months unopened. Goat's and sheep's are "
     "the other animals, sharper and richer. Plant milks - oat, soya, almond, coconut - are a "
     "different drink, and the barista ones are the ones that do not split in hot coffee."),
    (("bean", "beans"), "bean",
     "Dried or tinned is the first split: dried needs soaking overnight and a hard ten-minute "
     "boil, tinned is cooked and ready. After that it is the bean: kidney is the chilli one, "
     "cannellini and haricot are creamy and white (baked beans are haricot in tomato), black "
     "beans are earthy for Mexican food, and butter beans are the big soft ones. Chickpeas, "
     "lentils and split peas are the same family - pulses - and they cook without soaking."),
    (("lettuce", "lettuces"), "lettuce",
     "Crisphead - iceberg - is the crunchy one that keeps for a week and is mostly water. Cos, "
     "or romaine, is the upright one with a spine, and it is the one for Caesar. Butterhead - "
     "round and little gem - is soft and sweet, and wilts first. Loose-leaf - oakleaf, lollo "
     "rosso, frisée - is the curly one to tear into a bowl. Rocket and spinach are leaves sold "
     "beside it, not lettuce, and they are peppery or earthy rather than crisp."),
    (("wine", "wines"), "wine",
     "Red, white and rosé are about the skin, not the grape: red is fermented on it, white off "
     "it, and rosé briefly on it. Sparkling is a second fermentation for the bubbles, and "
     "fortified - sherry, port, madeira - has spirit added, which is why it keeps for weeks after "
     "opening. The other axis is the grape and where it grew, which is what makes a Chablis lean "
     "and a Chardonnay from a hot place buttery, and a wine dry or sweet."),
    (("coffee", "coffees"), "coffee",
     "Two beans: arabica is the fruity, slightly acidic one in most good coffee, and robusta is "
     "stronger, more bitter and has about twice the caffeine, which is why instant and cheap "
     "espresso blends use it. Roast runs from light, which keeps the fruit and the acidity, to "
     "dark, which tastes of the roast itself. Then it is ground to the brew: fine for espresso, "
     "medium for a filter machine, coarse for a cafetière. Instant is brewed and dried, a "
     "different drink, not a weaker one."),
    (("yoghurt", "yogurt", "yoghurts", "yogurts"), "yoghurt",
     "Natural is milk and cultures and nothing else, and it is what to cook with. Greek is the "
     "same yoghurt strained of its whey, so it is thicker and higher in protein; Greek-style is "
     "thickened with milk powder and is cheaper and sweeter. Set is cultured in the pot and stays "
     "firm, stirred is smooth. Skyr is strained further still, so it is very thick and very high "
     "in protein. Live yoghurt has the cultures still alive, which is the kind that helps an "
     "unsettled stomach."),
)

ENTRIES.extend(kinds_entries(_KINDS))


# The "can I use X instead of Y" verdicts, one entry per pair (see _SWAP_VERDICTS above).

# The pair is matched on both words wherever they sit, so the reverse question ("can i use plain
# flour instead of cornflour") would land here too. It is a different question, answered by the
# swap entry for the ingredient being replaced, so a verdict steps aside when the line offers
# what it replaces: "butter instead of oil" is not the oil-for-butter question.
for _offered, _replaced, _verdict in _SWAP_VERDICTS:
    ENTRIES.append(entry("uses-%s-for-%s" % (_offered[0].replace(" ", "-"),
                                             _replaced[0].replace(" ", "-")),
                         (_offered, _replaced), _verdict, bias=2, ask=_SWAP_ASK,
                         avoid=tuple("%s instead of" % name for name in _replaced)))


# --- keeping food: one table, so every way of asking a food's shelf life agrees ------------
# The reason each food spoils is different, so the reply is written per food, but the question
# is always the same shape: a food (potato, onion, carrot) plus a keeping word ("keep", "last",
# "store", "gone soft", "sprouting", "how long", "mouldy"). A line that only names the food
# ("what can I do with mushrooms") is a meal question and stays with the pantry table.
# "fresh" is not in here on purpose: in a question it is an adjective about the food ("do i need
# fresh eggs for meringue"), not a question about keeping it, and it costs main's egg answer.
# "use up" and "freezer" are out for the same reason - a leftover wants a recipe, and a freezer
# line is about freezing, not storing.
# The freezer, for the cooked-keeping rows in bot/knowledge/keeping_cooked.py. A cooked food
# put in the freezer keeps for a stated time, and every one of those rows says it. Only the
# freezer's own words are here: "how do i defrost cooked chicken" and "how long do i reheat it
# for" are the how-to questions, and answering them with the keeping clock is not an answer.
FREEZER_WORDS = ("freeze", "freezes", "freezer", "frozen", "freezing")

# Cooking a thing that is still frozen is a different question from freezing it once it is cooked,
# and these rows have nothing to say about it: "can i cook chicken from frozen" was answered with
# the cooked chicken's keeping clock, which is about the wrong bird. The words say the food has not
# been thawed yet, so the row stands down and the thaw entry answers.
STILL_FROZEN_WORDS = ("from frozen", "still frozen", "cooked from frozen", "cook it frozen",
                      "without defrosting", "without thawing", "no need to defrost")

# A line that asks how to cook the food is not asking how long cooked food keeps, and a freezer
# word alone does not make it one: "can i cook frozen chicken" is about the raw bird, where main
# answered the chicken's own keeping row. The want rule in `lookup` lets such a line in without any
# of the row's ask words, so the row stands down for a line with a cooking verb in it that never
# says the food is already cooked. A follow-up keeps working: "can i freeze it" after "i cooked a
# big pot of mince" has no cooking verb in it, so the row is still the one that answers.
COOKING_VERBS = re.compile(r"\b(?:cook|cooks|cooking|roast|roasts|roasting|bake|bakes|baking|"
                           r"fry|fries|frying|boil|boils|boiling|simmer|simmering|grill|"
                           r"grilling|steam|steaming)\b")


def _already_cooked_is_the_question(understood):
    """True when the line is about a food that is cooked already, or asks nothing about cooking."""
    text = " ".join(str((understood or {}).get("clean") or "").lower().split())
    if any(word in text for word in COOKED_KEEP_ASK):
        return True
    return not COOKING_VERBS.search(text)

KEEP_WORDS = ("keep", "keeps", "keeping", "shelf life", "shelf-life", "store", "storing",
              # "can i reheat cooked mince" and "reheating leftover chicken" ask the keeping
              # clock, not how to cook it: how many days it keeps and how it goes back hot.
              "reheat", "reheats", "reheating", "reheated",
              "storage", "stored", "last",
              "lasts", "longer", "go off", "goes off", "gone off",
              "going off", "sprout", "sprouts", "sprouting", "soft", "gone soft", "bendy",
              "mouldy", "mould", "moldy", "dried out", "dry out", "wilt", "wilted", "limp",
              "rot", "rotten", "green", "greening", "fridge",
              # the day after, and the date on the pack: "can i eat a jacket potato the next day"
              # and "can i eat cheese past its date" are keeping questions with neither "keep"
              # nor "last" in them
              "next day", "the next day", "tomorrow", "past its date", "past the date",
              "out of date", "once opened", "once open",
              # "are my mushrooms still ok" is how people ask whether they dare eat it, and it
              # has no keeping word in it at all: the food plus one of these is the whole shape.
              # Without them the line reached the dish-plan entry, which had nothing to say
              # about a punnet of mushrooms in the fridge.
              "still ok", "still good", "still fine", "still safe", "still edible",
              "are they ok", "are these ok", "ok to eat", "safe to eat",
              # a food that has turned is a keeping question said by its smell or its taste:
              # "the flour tastes old" and "my flour smells musty" reached a house-damp card and
              # the raw-flour sauce card, and neither row can tell a turned food from a fresh one
              "smell", "smells", "smelling", "smelly", "tastes old", "taste old", "tastes off",
              "tastes funny", "tastes strange", "tasted old", "gone stale", "tastes stale",
              "tastes sour", "smells off", "smells funny", "smells sour", "smells musty")

# A food, the words that name it, and how to keep it. Written as one table because the second
# half of the question - how long, where, why has it gone soft - is the same in every case.

# A pot that has gone mouldy or smells off is not a keeping question, and the keeping number is
# the dangerous direction: "my soup has gone mouldy" was answered "Soup keeps 3 to 4 days in the
# fridge", which invited someone to eat it. Mould in a wet dish sends threads under the surface
# where you cannot see them and heating does not make it safe, so the answer is bin it - the
# opposite of the cheese rule, and the reason this is a row of its own rather than a line in the
# pot row above. Nothing here is keyed on "still ok" or "safe to eat": those carry no sign of
# spoiling, and "is my rice still ok" wants the reheating answer, not the bin.
ENTRIES.append(entry("gone-off-pot",
                     (("soup", "soups", "stew", "stews", "broth", "curry", "curries",
                       "chilli", "casserole", "gravy", "sauce", "sauces", "dahl", "dal",
                       "tagine", "goulash", "leftovers", "yogurt", "yoghurt", "custard",
                       "cream", "rice", "risotto rice", "pasta", "pot", "tub", "batch", "food",
                       "potato", "potatoes", "jacket potato", "boiled potatoes", "spuds",
                       # "my bolognese went mouldy" says the dish by its sauce's name
                       "bolognese", "ragu", "risotto", "chowder", "hotpot", "stock", "stocks"),
                      ("mould", "moulds", "mouldy", "mold", "moldy", "gone off", "gone bad",
                       # a cooked grain, potato or pasta that has turned is slick and slimy
                       # before it smells, and "my rice is slimy" was answered with the calorie
                       # comparison because "slimy" is one letter from "slimming"
                       "slimy", "sliminess", "slick", "smells odd", "smell odd",
                       "gone sour", "smells off", "smells funny", "smells wrong", "smells bad",
                       "smelt off", "tastes off", "tastes funny", "tastes wrong",
                       # "bubbling" is a pot on the heat as often as it is a pot on the turn:
                       # "why is my risotto bubbling" was binned, and a risotto is stirred.
                       "tastes sour", "smelly", "fizzy", "fizzing",
                       "fuzz", "furry", "fuzzy")),
                     "Bin it. Mould, an off smell or a slimy feel in a soup, sauce, stew or a "
                     "cooked grain means threads and bacteria under the surface where you cannot "
                     "see them, and heating it through does not make it safe - the opposite of "
                     "hard cheese. A pot that tastes sharp, fizzes or has bubbles is the same "
                     "answer with no mould showing.",
                     bias=2,
                     # hard cheese keeps its own rule (cut an inch around the mould), a loaf has
                     # a row, and sour cream is a thing you buy rather than something that has
                     # turned
                     # the raw-chicken and raw-meat rows say it better and say it about the
                     # smell that matters ("a sour or ammonia smell, a tacky or slimy feel"), so
                     # this row keeps off them
                     avoid=("cheese", "cheeses", "bread", "loaf", "loaves", "sour cream",
                            # a cream for the skin is not a pot on the hob: "has my shaving
                            # cream gone off" was binned as a stew. The cosmetic row keeps
                            # its own lifetime for these.
                            "hand cream", "body cream", "shaving cream", "nappy cream",
                            "face cream", "facial cream", "eye cream", "spot cream",
                            "eczema cream", "cold cream", "moisturiser", "moisturizer",
                            "sun cream", "suncream", "sunscreen", "sunblock", "lip balm",
                            "lip salve", "aftershave", "toner",
                            # a pot of compost is not a pot on the hob: "why is there mould in
                            # my plant pot" was binned as a stew, and the soil-mould row is the
                            # answer to it
                            "plant", "plants", "houseplant", "house plant", "compost",
                            # NOT "potting": its forms are {pot, potte, potting, pott}, so it
                            # turns this row down for every line with "pot" in it, and "my pot
                            # of curry went mouldy" stopped being binned. The same stem trap as
                            # "ironing" in nutrient-a-day. `potting soil` and `potting compost`
                            # say the same thing without the bare stem.
                            "potting soil", "potting compost", "soil", "seedling", "seedlings",
                            "garden", "terracotta", "saucer",
                            "chicken", "chickens", "meat", "beef", "pork", "lamb", "fish",
                            # a dog or a cat that has gone off its food is a refusal to eat, and
                            # "my dogs gone off his food" was binned as a stew. The pet rows say
                            # when to ring the vet.
                            "dog", "dogs", "puppy", "pup", "pups", "cat", "cats",
                            "kitten", "kittens", "pet", "pets", "vet", "rabbit", "hamster",
                            # "does pasta go off" and "how do i stop food going off" ask how
                            # long it keeps and how to make it last, not whether this pot is
                            # already gone: the shelf life is the keeping tables' answer.
                            "going off", "goes off", "do they go off", "does it go off",
                            "keep food from", "keep from", "prevent", "stop food", "last longer",
                            "make it last", "shelf life", "how long",
                            # "tell me a funny joke about soup" is a joke: "funny" is only a
                            # sign of spoiling next to a smell or a taste word.
                            "joke", "jokes", "comedy",
                            # a bubbling sourdough, a fizzing kombucha and a curdling sauce are
                            # cooking, not spoiling
                            "sourdough", "dough", "starter", "yeast", "prove", "proving",
                            "rise", "rising", "ferment", "fermenting", "kombucha", "kimchi",
                            "brew", "brewing", "curdle", "curdled", "curdling", "separated",
                            "stock cube", "stock cubes", "stock pot", "stockpot",
                            "split", "split sauce", "sauce split",
                            # "gone off" with a person's possessive is appetite, not spoiling:
                            # "my sister has gone off her food since her op" is the one thing
                            # nobody wants answered "Bin it." A pot has no owner.
                            "off her food", "off his food", "off their food",
                            "off our food", "off my food", "off your food",
                            "gone off food", "gone off eating",
                            # "the dog has gone off his food today" is a dog refusing his bowl,
                            # not a pot on the turn: a pet named in the line is the pet's answer.
                            "dog", "dogs", "puppy", "pup", "puppies", "cat", "cats",
                            "kitten", "kittens", "pet", "pets", "vet")))

# The commonest egg keeping question is about the raw ones in the box, and the keeping table's
# single egg answer opened with boiled eggs, so "how long do eggs keep" and "should i keep my eggs
# in the fridge or on the counter" both got a week of boiled eggs. Two entries, one apposite each.
ENTRIES.append(entry("keep-eggs", (("egg", "eggs"), KEEP_WORDS),
                     "Raw eggs keep about three weeks past the date on the box if they have stayed "
                     "cold, so the fridge is the place for them: in their carton on a shelf rather "
                     "than in the door, where the temperature swings. Go by the date and by how "
                     "they smell when you crack one.",
                     bias=1,
                     # a dish made of boiled egg is not a box of raw eggs: "how long does egg
                     # salad keep" was getting three weeks, which is the dangerous direction.
                     avoid=("salad", "sandwich", "sandwiches", "sarnie", "butty", "mayo",
                            "mayonnaise", "cress", "filler",
                            # "is it ok to eat eggs every day" and "are eggs good for you" are
                            # how many a week, not how many weeks in the box, and this row was
                            # answering them with the shelf life.
                            "every day", "everyday", "every morning", "daily", "a day",
                            "per day", "how many",
                            # the "every day" shapes only: a bare "ok to eat" is also how the
                            # date question is asked ("is it ok to eat eggs past the date"), and
                            # that one wants the three weeks in the box.
                            "ok to eat a day", "ok to eat every", "okay to eat every",
                            "fine to eat every", "good for you",
                            "healthy", "cholesterol", "too many", "how often")))
# What people actually put in the fridge is the made dish, and it keeps for days not weeks.
ENTRIES.append(entry("keep-egg-salad", (("egg salad", "egg mayonnaise", "egg mayo",
                                         "egg sandwich", "egg sandwiches", "egg sarnie",
                                         "egg and cress"),
                                        KEEP_WORDS + ("out", "overnight", "tomorrow")),
                     "Egg salad keeps 2 days in the fridge, covered, on a shelf rather than in the "
                     "door, and no more than 2 hours out at room temperature before it should go "
                     "in the bin: mayonnaise and boiled egg together is the part that turns. If it "
                     "has sat out at a picnic since morning, don't risk it.",
                     bias=2))
ENTRIES.append(entry("keep-boiled-eggs", (("egg", "eggs"),
                                          ("boil", "boiled", "boiling", "cooked", "hard boiled",
                                           "shell on", "peeled", "devilled", "deviled")),
                     "Boiled eggs keep about a week in the fridge with the shell on, and 2 to 3 "
                     "days once peeled, in a covered bowl of water. Raw ones in their shells keep "
                     "far longer: about three weeks past the date on the box if they stayed cold.",
                     # "boiled" is the cooking word as well as the keeping word, so this entry
                     # needs the keeping half of the question before it answers: "how long to
                     # boil an egg" is a timer, and the timer entry has that.
                     ask=("keep", "keeps", "keeping", "kept", "last", "lasts", "store", "stored",
                          "fridge", "ok", "safe", "week", "days",
                          # "how long are boiled eggs good for" is this question in the words
                          # most people use, and the timing row took it on "boiled"
                          "good for"),
                     bias=2))


# A food that is already cooked is a leftovers question, not a keeping one: "i have leftover
# boiled potatoes in the fridge" wants the 3-to-4-day reheating rule, not how to store a raw
# potato.
COOKED_WORDS = ("boil", "boiled", "boiling", "cooked", "leftover", "leftovers", "left over",
                "reheat", "reheated", "mashed", "roasted")

# "what can i do with a bag of apples going soft" is a request for a dish, not a shelf-life
# question, and it already has an answer: stewed apple. The keeping reply is now the more
# specific match for the food, so each keeping entry holds out the shapes that hand the food
# over to be cooked with.
USE_UP_WORDS = ("what can i do with", "what do i do with", "what to do with",
                "what can i make with", "what can i cook with", "use up", "use them",
                "using up", "recipe", "recipes", "idea", "ideas")

# "ok and how long in the oven", after a line about apples, is a question about cooking them:
# the food in the line is smaller than the question being asked. A keeping question almost
# never names the oven, so the cooking words take the line away from the shelf-life reply.
COOKING_WORDS = ("oven", "bake", "baking", "baked", "roast", "roasted", "fry", "frying",
                 "grill", "temperature", "minutes", "heat",
                 # "how long do i microwave an apple" was answered with how long apples keep,
                 # because the microwave is a way of cooking the food and not a way of storing
                 # it, and "heat" did not cover the word anyone actually says
                 "microwave", "microwaved", "microwaving", "steam", "steamed", "steaming",
                 "poach", "poached", "poaching")

STORING = ("how do i store", "how should i store", "how do you store", "best way to store",
           "how to store", "storing")

# A date question - "is my butter out of date" - is still a keeping question, and KEEP_WORDS has
# no date words because no row above needed one. Keyed by the food, because these words are only
# wanted where a person says them: "is my potato out of date" is not a sentence anyone says.
KEEP_DATE_WORDS = ("out of date", "past the date", "past its date", "use by", "best before",
                   "still ok", "still good", "still fine")
KEEP_EXTRA_WORDS = {food: KEEP_DATE_WORDS for food in ("butter", "cheese")}

# How to store cheese, and what to do about the mould on it, is `cheese-store`'s question; this
# table is for how long the food keeps, so the row stands down on those words.
MOULD_WORDS = ("mould", "mouldy", "mold", "moldy")
# The words that say a food has already turned, which is the spoilage entry's question and not
# the shelf-life one: "the mince has gone grey" wants to know whether to bin it, not how many
# days raw mince keeps.
_SPOILT_WORDS = ("smell", "smells", "smelly", "smelt", "off", "gone off", "going off", "slimy",
                 "sour", "grey", "gray", "tacky", "separated", "watery", "fizzy", "mould",
                 "mouldy", "mold", "moldy", "pink", "rot", "rotten", "bad", "went bad")

# A curry paste, powder or spice mix is a jar in the cupboard, not a pot on the stove, and its
# keeping question is a different one (months, not days). "curry" is in the pot row's names, so
# the cupboard words hold the row off those lines.
KEEP_STAND_DOWN = {# "how long does garlic breath last" was answered with how long whole bulbs
                   # keep, because "how long" and "last" are the keeping words and "breath" was
                   # not a reason to stand down. A burned clove is the burn row's question too.
                   "garlic": ("breath", "bad breath", "garlic breath", "breathe", "breathing",
                              "smell", "smells", "smelt", "smelled", "stinks", "burn", "burnt",
                              "burned", "burning", "bitter", "black", "went black"),
                   "cheese": STORING + MOULD_WORDS + (
                       # "is my cheese off" is the mould question, and the row that cuts an
                       # inch around it answers better than the number of days does.
                       "off", "is bad", "are bad", "gone bad"),
                   # A pot that has gone mouldy or smells wrong is not asking how many days it
                   # keeps, and the keeping number is the dangerous direction: "my soup has gone
                   # mouldy" was answered "Soup keeps 3 to 4 days in the fridge". The same words
                   # that hold the cheese row off, plus the smell and the signs a person notices.
                   # "my cream smells off", "my mince has gone grey" and "the ham is slimy" are
                   # the spoilage cards next door, which say what to look at and when to bin it.
                   # "how long does sun cream last" and "how long does a cream tea keep" are not
                   # questions about a pot of double cream in the fridge: the cream in them is a
                   # different thing with its own date, so the row stands down for those words.
                   "cream": _SPOILT_WORDS + ("sun cream", "sunscreen", "hand cream", "face cream",
                                             "eye cream", "shaving cream", "moisturiser",
                                             "ice cream", "cream cheese", "cream tea",
                                             "cream cake", "cream cakes", "cream cracker",
                                             "cream crackers", "cream soda", "clotted",
                                             "creme egg", "cream liqueur"),
                   "avocado": _SPOILT_WORDS,
                   "mince": _SPOILT_WORDS,
                   "ham": _SPOILT_WORDS,
                   # "how long does orange juice keep" was this row, because "oranges" is in it
                   # and "juice" is not in any fruit row: squeezed fruit is a different
                   # question with a different number of days, so the row stands down for it.
                   "lemons": ("juice", "juices", "squash", "cordial"),
                   "soup": ("paste", "pastes", "powder", "powders", "spice", "spices",
                            "seasoning", "seasonings", "stock cube", "stock cubes")
                           + MOULD_WORDS + ("moulds",)}

# "how long to melt butter" and "can you toast cheese" carry "how long" like a keeping question
# and want the pan, not the fridge. "grated" is not here on purpose: "how long does grated cheese
# last" is still a shelf-life question.
METHOD_WORDS = ("melt", "melts", "melting", "melted", "toast", "toasted", "toasting")

# "soft" is a keeping word ("why have my potatoes gone soft") and a cooking word ("how do i know
# when potatoes are soft"), so the doneness questions have to be kept off the keeping entries.
# "how long to" was a bare phrase in here, and it took the keeping shape with it ("how long to
# keep potatoes" stopped answering at all), so the cooking verbs are spelled out instead.
DONENESS = ("know when", "know if they are done", "when they are done", "when it is done",
            "how long to cook", "how long to boil", "how long to roast", "how long to bake",
            "how long to microwave", "how long to air fry", "how long to airfry",
            "how long to grill", "how long to fry", "how long to steam", "tender")

# "can i eat green potatoes" is a safety question about solanine, not a shelf-life one, and
# "green" is one of the keeping words: the keeping answer said nothing about eating them.
GREEN_SAFETY_WORDS = ("can i eat", "eat them", "eat green", "safe", "poison", "poisonous",
                      "toxic", "solanine", "solamine")

# A cake is not the fruit it is named after: "how long does a lemon drizzle cake last" got the
# lemon shelf life, because "lemon" and "last" are the whole of that question's words. The baked
# goods are kept in their own answers, so every row of this table stands aside when the line
# names one.
BAKED_LINE_WORDS = ("cake", "cakes", "sponge", "sponges", "drizzle", "muffin", "muffins",
                    "cupcake", "cupcakes", "biscuit", "biscuits", "cookie", "cookies", "scone",
                    "scones", "brownie", "brownies", "loaf", "loaves", "bread", "bun", "buns",
                    "pastry", "pie", "pies", "tart", "tarts", "flapjack", "shortbread",
                    "crumpet", "crumpets", "teacake", "teacakes")

# The general cooked-food table answers what is left over, so any food with a keeping row of its
# own - a carrot, a lemon, a block of butter - must reach that row instead. The names come from
# KEEPS itself rather than from a list kept in step by hand.
# A cooked food keeps like cooked food whatever it was: the words that say the food is cooked,
# and the words that say the line is about keeping it. Both are needed - "how long do i roast
# potatoes" is a cooking time, and only "how long do roast potatoes keep in the fridge" is this
# table's question.
_COOKED_KEEPING = ("cooked", "cook", "boiled", "mashed", "stewed", "roast", "roasted",
                   "leftover", "leftovers", "left over")
# The ask of the cooked-food table. "fridge" is not in it, and it was: "nothing in the fridge what
# can i cook" and "what can i cook with an empty fridge" matched the subject on the loose form of
# "cooked" and the ask on the bare word "fridge", and were handed this keeping table instead of
# anything to cook. A fridge is where cooked food is kept; it is not a way of asking how long it
# keeps, and every keeping question either says keep/last/store or names what it keeps.
_KEEPING_ASK = ("keep", "keeps", "keeping", "store", "stored", "storage",
                "last", "lasts", "still ok", "still good", "gone off", "going off",
                "out of date", "use by", "overnight", "til tomorrow", "till tomorrow")
for _row in ENTRIES:
    if _row.id == "fridge-life":
        _row.avoid = _row.avoid + tuple(_name for _names, _ in KEEPS for _name in _names)
        # A cooked one of those foods is the other way round: it is cooked food, and it keeps
        # like cooked food, not like the raw carrot in the drawer. The keeping rows below hold
        # out COOKED_WORDS for exactly that reason, so this row picks the line up again when the
        # line says cooked - one entry, whatever the food, since the cooked table is one table.
        # The food itself is deliberately not in this key: "how long do i roast potatoes" is a
        # cooking time and "roast potato recipe" is a recipe, and both of those name a cooked
        # food. A line is this table's question when it says the food is cooked AND asks for how
        # long it keeps, and then the cooked table is the answer whatever the food was.
        # Cooked rice has a stricter rule than the rest (24 hours, and cool it fast), and it has
        # its own row, so it is not this table's answer even when the line says cooked.
        # A burnt dinner is not a keeping question: "i burnt the roast, is it still ok" and "the
        # roast is burnt, is it still ok" were given the cooked-food days, because "roast" is a
        # cooked word and "still ok" is the ask. The burnt-food answer says what to do with the
        # black and whether it can be eaten, and this row stands down for it.
        ENTRIES.append(entry("fridge-life-cooked", (_COOKED_KEEPING, _KEEPING_ASK),
                             _row.reply, bias=1,
                             avoid=("rice", "burnt", "burned", "charred", "scorched",
                                    "burnt on", "caught on the bottom")))


# A keeping question is about a food, and "stuff" is what people say when they have not named
# one. "my freezer is full of stuff, whats the oldest thing i can keep" reached the stuffing row,
# because the forms of "stuffing" include "stuff" (the -ing strip with the doubled letter taken
# off it), so a word that names no food put a food in the line. These rows stand down for a line
# like that and leave the question to the answer that names no food of its own, or to a punt.
# Only words that never name a food are here: "things" and "bits" sat in the first draft and
# stood the chicken row down for "some bits of chicken left over".
_A_BLANK_FILLER = re.compile(r"\b(?:stuff|junk|odds and ends)\b")


def _a_food_and_not_a_blank(understood):
    """False when the line says "stuff" where the food should be, and that is all it says."""
    clean = str((understood or {}).get("clean") or "").lower()
    return not _A_BLANK_FILLER.search(clean)


# "Are my mushrooms off" is the keeping question in the words people use most, and it was not
# a keeping question at all: the ask above knew "gone off" and "going off" but not the plain
# "is off" people type, so the line fell through to whatever dish happened to name the food -
# roast potatoes for "are my potatoes off", garlic mushrooms for "are my mushrooms off", carrot
# soup for the carrots. The words here are the bare ones that only a spoilage question says;
# "off the heat" and the rest of the prepositions are held out because a line about keeping a
# food has to keep it, not take it off something.
_OFF_ASK = ("off", "is bad", "are bad", "gone bad", "gone over", "past it", "off yet",
            "already off", "off to eat", "off by now")
# A bare "off" is also a preposition, and the same list the spoilage rows use keeps those lines
# out of the keeping rows: the skin off a fish, the pan off the heat, the day off.
_OFF_THE_THING = ("off the", "off my", "off your", "off his", "off her", "off its", "off them",
                  "off it", "cut off", "cutting off", "chop off", "chopping off", "slice off",
                  "skin off", "take the skin", "fat off", "off the bone", "turn off", "turned off",
                  "switch off", "switched off", "day off", "days off", "time off", "off work",
                  "off sick", "show off", "better off", "worse off", "off the menu",
                  "off the heat", "off the hob", "off the plate", "off the pan", "take it off",
                  "take them off")

# The vegetables whose only other keeping answer is the general "most veg keeps a week" card.
KEEP_AHEAD_OF_THE_GENERAL = frozenset(("courgette", "aubergine", "broccoli", "radish",
                                       "butternut squash", "cabbage"))

for _names, _reply in KEEPS:
    # bias keeps these ahead of the cooking-time entries, which also match "how long" - a
    # potato that is being kept is not a potato that is being boiled.
    # eggs are not in this table any more: raw and boiled eggs keep for such different times
    # that each has its own entry below. The guards stay as they were for everything else.
    _avoid = (STORING if "egg" in _names[0]
              else COOKED_WORDS + USE_UP_WORDS + COOKING_WORDS + DONENESS + METHOD_WORDS
              ) + BAKED_LINE_WORDS
    if _names[0] == "potato":
        _avoid = _avoid + GREEN_SAFETY_WORDS
    _avoid += KEEP_STAND_DOWN.get(_names[0], ()) + KEEP_QUALITY_WORDS + _OFF_THE_THING
    _key = KEEP_WORDS + _OFF_ASK + KEEP_EXTRA_WORDS.get(_names[0], ())
    # bias=2 for the six vegetables added with no row of their own: `veg-keep` names them all
    # and keys the phrase "how long", which scores higher than this row's plain "keep", so
    # "how long do radishes keep" was told "most veg keeps about a week" while the radish row
    # sat one place below it. A row named on the food itself is the more specific answer.
    _bias = 2 if _names[0] in KEEP_AHEAD_OF_THE_GENERAL else 1
    ENTRIES.append(entry("keep-%s" % _names[0], (_names, _key), _reply, avoid=_avoid,
                         bias=_bias, guard=_a_food_and_not_a_blank))

for _names, _reply in COOKED_KEEPS:
    # bias=2: the cooking-time entry for the same food matches "how long" with a phrase and
    # scores higher than a plain word, and a cooked food that is being kept is not being cooked
    # again. ask= keeps every "how long to cook/simmer/fry it" line with the method entry.
    # "how long is cooked bacon good for" is shelf life said plainly: the phrase is here and
    # not in KEEP_WORDS because "is butter good for you" is a health question, and the day's
    # keeping clock is the wrong answer to it. A cooked word has to be in the line as well
    # (ask=COOKED_KEEP_ASK), so the phrase cannot reach those.
    # The freezer words are here rather than in KEEP_WORDS: a raw food in the freezer is a
    # different question (potatoes go black, beans get blanched), and every one of these rows
    # says how long the cooked food freezes for. "can i freeze cooked mince" was answered with
    # how to brown mince, and "can i freeze cooked chicken" with the raw chicken's fridge days.
    ENTRIES.append(entry("cooked-keep-%s" % _names[0],
                         (_names, KEEP_WORDS + ("good for",) + FREEZER_WORDS),
                         _reply,
                         avoid=USE_UP_WORDS + ("raw", "uncooked", "freezer burn") + STILL_FROZEN_WORDS
                         # "shelf life of cooked chicken" is main's chicken-storage row, which
                         # carries the same days: two keeping entries for one food is one too
                         # many, so the newer one holds that phrase out.
                         + ("shelf life", "shelf-life")
                         + COOKED_KEEP_AVOID,
                         bias=2, ask=COOKED_KEEP_ASK,
                         guard=lambda u: _already_cooked_is_the_question(u)
                         and _a_food_and_not_a_blank(u)))


# The cooked and bought things people ask about the day after. These are rows in the same table,
# but their line often says "cooked" or "baked" about the food itself, which the KEEPS guard reads
# as a different question, so they hold out only the shapes that really are one.
KEEPS_COOKED = (
    (("jacket potato", "jacket potatoes", "baked potato", "baked potatoes", "potato skins"),
     "A jacket potato is fine the next day: cool it within an hour, keep it in the fridge covered "
     "and eat it within 2 days, skin and all. Reheat it until it is piping hot right through, or "
     "cut it up and fry it - a foil-wrapped one left on the side overnight goes in the bin."),
    (("coleslaw", "slaw"),
     "Coleslaw keeps 3 days in the fridge once it is opened, and homemade 2, because it is the "
     "mayonnaise that turns. Keep the tub cold and eat it by the date on it, and bin slaw that "
     "smells sharp or has gone watery in the bottom of the tub."),
    (("scone", "scones", "fruit scone", "cheese scone"),
     "Scones are best the day they are made and keep 2 days in a tin, or a day in the fridge. "
     "Sprinkle them with water and give them 3 minutes in a warm oven to bring them back; freeze "
     "them on the day and refresh from frozen, and bin any with green on them."),
    (("sushi", "shop sushi", "sushi box"),
     "Shop sushi is made to be eaten the day you buy it: keep it in the fridge, eat it within 24 "
     "hours and do not leave it out on the side. The rice and the raw fish are what go off, so "
     "bin what is left rather than keeping it for tomorrow."),
    (("tuna", "tinned tuna", "tin of tuna", "canned tuna"),
     "An opened tin of tuna keeps 2 days in the fridge, emptied into a bowl with a lid - left in "
     "the tin it tastes of metal. Eat it cold in a sandwich or flake it through a sauce, and do "
     "not freeze it, because it comes back dry and woolly."),
    (("cooked salmon", "cooked fish", "leftover salmon", "leftover fish", "smoked salmon"),
     "Cooked salmon keeps 2 days in the fridge, covered, and it is better cold in a salad than "
     "reheated, which dries it out. Cool it within an hour of cooking and bin it after 2 days; "
     "smoked salmon keeps 3 days once the pack is open and freezes for a month."),
    (("prawn", "prawns", "cooked prawns", "king prawns"),
     "Cooked prawns keep 2 days in the fridge, in a sealed box away from anything raw, and ones "
     "from the deli counter keep a day less than a sealed pack. Eat them cold or warm them through "
     "in a sauce rather than frying them again, and bin any that smell of ammonia."),
    # The dinner-table leftovers are a shorter keep than the roast that made them, and every one
    # of these was a shrug or the 3 to 4 days of a general cooked-food rule. Gravy and custard
    # especially: both are liquid, both cool slowly in the jug, and 3 to 4 days is too long.
    (("gravy", "gravies", "onion gravy", "leftover gravy", "brandy sauce"),
     "Gravy keeps 2 days in the fridge, less than the meat does, because it is mostly liquid and "
     "it cools slowly in the jug: get it in within 2 hours of making it, standing the jug in a "
     "bowl of cold water if it is still hot. Reheat it until it boils right through, and bin any "
     "that has sat out on the table all evening."),
    (("stuffing", "sage and onion", "forcemeat", "stuffing balls"),
     "Cooked stuffing keeps 2 days in the fridge and it is the leftover to be strict with, because "
     "it has been inside the bird and soaked up the juices: cool it within 2 hours, box it, and "
     "reheat it until it is piping hot right through. Stuffing that never went in the oven is a "
     "different thing and keeps as long as the bread in it."),
    (("custard", "homemade custard", "custard sauce", "creme anglaise"),
     "Homemade custard keeps 2 days in the fridge, in a jug with a lid or a sheet of cling film "
     "pressed onto the surface so no skin forms. Reheat it gently and stir rather than boiling it, "
     "and bin any that has stood on the table through dinner."),
    (("trifle", "trifles", "sherry trifle"),
     "A trifle keeps 2 days in the fridge, and it is the cream and the fruit that turn rather than "
     "the sponge: cover it once it is made and eat it within a day or two. Do not freeze it - the "
     "cream splits and the sponge goes watery."),
)
# "can i reheat gravy" is a keeping question with none of the keeping words in it, so the rows
# whose food is a sauce or a set pudding take the reheat shapes as well as the shelf-life ones.
# "can i do the gravy ahead" and "can i do the stuffing the night before" are keeping questions in
# the doing-it form, and the list held only the making-it form ("make ahead", "make it ahead")
# and "the day before". So the plain "do the X ahead" shape reached nothing and the person got the
# hedge, while "can i do the cake ahead" worked only because cake has a card of its own. "ahead"
# is here as a word and not only in the two phrases for that reason: what follows the food is
# "ahead", "ahead of time" or "the night before", and the food name is already the other half of
# the key. This is the making-ahead frame for every cooked food, not one line's wording.
KEEPS_COOKED_WORDS = KEEP_WORDS + ("reheat", "reheating", "reheated", "heat up", "heated up",
                                  "warm up", "warmed up", "make ahead", "make it ahead",
                                  "do it ahead", "do that ahead", "ahead", "ahead of time",
                                  "in advance", "the day before", "day before", "the night before",
                                  "night before", "keep it warm")
for _names, _reply in KEEPS_COOKED:
    ENTRIES.append(entry("keep-" + _names[0].replace(" ", "-"), (_names, KEEPS_COOKED_WORDS),
                         _reply,
                         bias=1,
                         guard=_a_food_and_not_a_blank,
                         avoid=USE_UP_WORDS + DONENESS + (
                             "how long to cook", "how long to bake", "how long to boil",
                             "how long to fry", "how do i cook", "how do i make", "recipe",
                             "in the oven", "microwave", "air fryer", "temperature")))

# The general cooked-food table is the answer for a food with no keeping row of its own, and the
# rows above are the list of the ones that have one: "how long does stuffing last in the fridge"
# was getting "cooked food keeps 3 to 4 days" while the stuffing row sat one line away. This is
# the same stand-down the raw keeping rows write for themselves further up, written here because
# the cooked table is defined below it.
for _row in ENTRIES:
    if _row.id == "fridge-life":
        _row.avoid = _row.avoid + tuple(_name for _names, _reply in KEEPS_COOKED
                                        for _name in _names)


# --- what can I make with ... ---------------------------------------------
# People often name what is already in the kitchen and ask for a meal. The entries above are
# keyed by a dish or a kitchen problem, so an ingredient list needs its own table: PANTRY maps
# the words people type to the ingredient they mean and to one quick dish for it, and DISHES
# holds the meals that need two or three of them. meal() picks the dish that uses most of what
# the line names, so "eggs and spinach", "spinach, eggs?" and "the spinach in the fridge" all
# reach the frittata; with no dish for the combination it gives one quick idea per ingredient
# instead. It passes when the line names nothing it knows, so the bot says it does not know
# rather than inventing a dish it cannot make.


# The meals that need two or three pantry things, best first. A dish answers every way of
# naming its ingredients.

# A cooked thing left over wants a different answer from a raw one, so a leftover line reads
# these first.
LEFTOVER_IDEAS = {
    # a glut of eggs is a volume question: the dishes that take several at a time answer it, and
    # what to do with the whites and the yolks separately is the rest of it.
    "egg": "Eggs going spare: a frittata or a tortilla takes six or eight at once with whatever "
           "veg is in the fridge, a quiche takes four plus milk and cheese, and meringues or a "
           "pavlova use up whites on their own. Hard boiled, they keep a week and make "
           "sandwiches, or halve them into a salad with mustard and oil.",
    "chicken": "Cooked chicken: shred it into a salad with mayonnaise, lemon and something "
               "crunchy, or stir it through fried rice with soy sauce and peas for a 10-minute "
               "dinner.",
    "potato": "Leftover potatoes: crush them a little and fry them in hot oil until crisp, or "
              "slice them into a frittata with eggs.",
    "pasta": "Leftover pasta: loosen it in a hot pan with a splash of water and a little oil, or "
             "bake it with a spoon of tomato sauce and cheese on top.",
    "salmon": "Leftover salmon: flake it through pasta or a salad with lemon and yoghurt, and "
              "don't reheat it hard or it dries out.",
    "bread": "Stale bread: tear it into croutons fried in oil and garlic, or blitz it into "
             "breadcrumbs and freeze them.",
    "lentil": "Leftover dhal: thin it with a splash of stock into soup, or eat it cold as a dip "
              "with bread and yoghurt.",
    "coconut milk": "Half a tin of coconut milk: simmer it with curry paste and whatever veg you "
                    "have for 10 minutes, or stir it into rice instead of water for a coconut "
                    "rice. It freezes in an ice cube tray for next time.",
    "cream": "Cream or soured cream going spare: stir it into a chilli or curry off the heat so "
             "it does not split, spoon it over baked potatoes or fruit, or let it down with a "
             "squeeze of lemon and use it as a dressing. Soured cream also freezes badly, so use "
             "it rather than keep it.",
    "sprout": "Leftover sprouts: halve them and fry cut side down in butter until they caramelise, "
              "about 8 minutes, or shred them raw into a salad with lemon, oil and toasted nuts.",
    "marrow": "Half a marrow left: scoop out the seeds, stuff it with mince and rice and bake it "
              "45 minutes at 190C (170C fan), or grate it into a curry - the water it gives up "
              "thickens the sauce as it cooks.",
    "buttermilk": "Buttermilk going spare: soda bread takes 284ml, or thin a pancake batter with "
                  "it, or marinate chicken in it for an hour before frying - it tenderises the meat.",
    "hot cross bun": "Buns going stale: butter them and bake them in a bread and butter pudding, "
                     "or halve and toast them under a grill with a little sugar on top.",
    "stuffing": "Leftover stuffing: shape it into balls and fry or roast them 15 minutes at 200C "
                "(180C fan), or press it into a tray and cut it into crisp squares - it is the "
                "best part of the tray, so do not bin it.",
    "porridge": "Leftover porridge: loosen it with milk and reheat it, or beat in an egg and fry "
                "spoonfuls in butter for oat fritters with jam.",
    "bolognese": "Leftover bolognese: bake it with pasta and white sauce, spoon it over a jacket "
                 "potato, or thin it with stock and beans into a soup.",
    "curry": "Leftover curry: reheat it once until piping hot and eat it with rice, or bake it "
             "under a mash topping for a curry pie.",
}

# "what can i make with the leftovers" is a meal question, not a keeping one: the keeping
# entries answer how long they last, and this one answers what to do with them. It is written
# here, after the pantry table, because the foods it must stand down for are the pantry's own:
# a line that names one of them keeps the answer that names it.
_NAMED_FOODS = tuple(sorted({word for aliases, _reply in PANTRY.values() for word in aliases}))

_FOODS_SAID = None


def _foods_said():
    """Every food name the pantry and the staples table know, with its plural undone."""
    global _FOODS_SAID
    if _FOODS_SAID is None:
        _FOODS_SAID = ({_fold(str(word).lower()) for word in _NAMED_FOODS}
                       | {_fold(str(word).lower()) for word in _STAPLE_NAMES})
    return _FOODS_SAID
# The answer for "i have leftovers, what can i make", when the line names no food this kitchen
# has an idea for. A line that does name one gets that food's answer instead: see
# _leftover_meal_reply.
LEFTOVER_SOUP = ("Soup is the easiest use of leftovers: soften an onion, add whatever veg you "
                 "have in order of toughness, cover with stock, simmer 20 minutes and blend or "
                 "leave it chunky - season at the end. Any cooked meat goes in for the last five "
                 "minutes only, and a spoon of something sharp (lemon, mustard, a splash of "
                 "vinegar) is what stops it tasting like a fridge. Whatever you reheat must be "
                 "piping hot all the way through once, and rice that has sat out is the one "
                 "thing to bin.")


def _leftover_meal_reply(memory, understood):
    """Soup for the leftovers nobody named, and the named food's own use when one is named.

    "What can i do with leftover chard" was answered with the soup paragraph above, which is the
    answer to a fridge with odds and ends in it and not to a chard. The food named is asked for
    its own use first; where the pantry's idea for it is a dish, that idea wins in the meal table
    and this row never sees the line.
    """
    from . import meals
    words = understood.get("words") or ()
    if isinstance(words, str):
        words = words.split()
    words = tuple(words) or tuple(str(understood.get("clean") or "").lower().split())
    named = meals.named_food(words, understood)
    if named in LEFTOVER_IDEAS:
        # Mince, chicken, rice and the rest have an idea of their own, and it is a use.
        return LEFTOVER_IDEAS[named]
    if named:
        idea = PANTRY.get(named, (None, ""))[1] if isinstance(PANTRY.get(named), tuple) else ""
        if not meals.idea_is_a_dish(idea):
            said = meals.use_it_up(named)
            if said:
                return said
    return LEFTOVER_SOUP


ENTRIES.append(entry(
    "leftover-meal",
    (("leftovers", "leftover", "left over", "odds and ends", "bits and pieces",
      "left in the fridge"),
     ("make", "made", "cook", "meal", "dinner", "tea", "supper", "soup", "ideas",
      "recipe", "recipes", "what can i", "do with", "use up", "using up", "turn into",
      "throw", "waste")),
    _leftover_meal_reply,
    ask=("how", "what", "can", "could", "any", "ideas", "should", "do i", "i have",
         "need", "got", "have"),
    # A line that names the food keeps the entry that names it: "what can I make with leftover
    # rice" is the rice question, "leftover mince" is the ragù and "half a roast chicken left
    # over" is the chicken one. This entry answers the general "i have leftovers, what can i
    # make", so it stands down for every food the pantry knows, and for the rest bias keeps a
    # named food ahead of it.
    bias=-2,
    # a keeping, freezing or safety question is not the cooking one
    avoid=("how long", "safe", "safely", "fridge", "freezer", "freeze", "frozen", "refreeze",
           "re-freeze", "refroze", "defrost", "defrosted", "thawed", "reheat", "reheated",
           "room temperature", "left out", "gone off", "smell", "smells", "sick", "pregnant",
           "dog", "cat", "bin", "keep") + _NAMED_FOODS))
# The word in front that turns a pantry name into a different food ("bean sprouts").
NOT_THIS_FOOD = {
    "sprout": ("bean sprout", "alfalfa", "mung", "soy sprout", "soya sprout"),
    "bean": ("bean sprout",),
    "butter": ("peanut butter", "peanut", "cocoa butter", "apple butter"),
    "corn": ("sweetcorn", "corned"),
    "cream": ("ice cream", "cream cheese", "cream cracker"),
    # A hot chocolate is a drink: "i fancy a hot chocolate" is not a bag of chocolate and a
    # reason to bake brownies.
    "chocolate": ("hot chocolate",),
    # Powder is not the jug: a spoon of buttermilk powder goes in a dry mix for scones or a
    # pancake batter, and the soda bread answer needs the liquid kind.
    "buttermilk": ("buttermilk powder", "powdered buttermilk"),
    # A rice cake is not a bowl of rice: "can i eat rice cakes every day" was answered with egg
    # fried rice, because the table read "rice" and stopped. The snack has its own row in
    # nutrition.py, so here the pantry name only has to step aside. The other things made of rice
    # are the same: a rice cracker, rice paper, rice vinegar or rice flour is not the grain you
    # boil, and "rice crispy cakes" is a cake to make rather than a bag of rice.
    # "rice pudding" is deliberately NOT here: the pudding has its own recipe row, and fencing the
    # head word out under it made a statement about one ("rice pudding in the slow cooker") fall
    # through to the wrong dish. A dish row's own name outranks the plain rice row anyway.
    # An animal's food is what goes in its bowl, not a dish: "he says theyre rabbit food" is a
    # verdict on the vegetables and got a braise on main, because the table read the animal and
    # stopped. The phrase steps the pantry name aside, so the line is answered by whatever it is
    # really about.
    "rabbit": ("rabbit food", "rabbit pellets"),
    "duck": ("duck food",),
    "chicken": ("chicken food", "chicken pellets"),
    "rice": ("rice cake", "rice cakes", "rice crispy",
             "rice crispies", "rice krispie", "rice krispies", "rice cracker", "rice crackers",
             "rice paper", "rice vinegar", "rice wine", "rice flour", "rice drink"),
}

PLANT_MILKS = ("coconut milk", "oat milk", "soy milk", "almond milk", "rice milk",
               "cashew milk", "coconut cream")

LEFTOVER_WORDS = frozenset("leftover leftovers cooked stale yesterday".split())
# The same thing said with two words, which a word list cannot see.
LEFT_POINTER = ("what's left", "whats left", "what is left", "anything left", "some left",
                "is left", "left over", "leftovers", "use up", "using up")
LEFTOVER_PHRASES = ("left over", "left from", "use up", "using up", "got spare", "spare ",
                    # "what can i do with what's left" is the same question as "leftovers": the
                    # food is already cooked, and the leftover idea is the answer that starts there.
                    "what's left", "whats left", "what is left", "anything left", "some left",
                    "is left", "left of the")

# Words that say an ingredient is already cooked, so a dish whose first step is browning or
# boiling it is the wrong answer: "leftover roast chicken and rice" wants the fried rice, not a
# pan of raw thighs. A dish takes a cooked ingredient only when it says so in "cooked".
COOKED_WORDS = frozenset("""
leftover leftovers cooked roast roasted mashed already precooked pre-cooked yesterday
""".split())

# "leftover roast chicken and rice": the "leftover" belongs to the chicken, not to the rice on
# the other side of the "and", so a look-back stops at a word that joins two ingredients.
JOINERS = frozenset("and or plus with also then &".split())


def _words_just_before(folded, place, reach):
    """The words before an ingredient that still describe it, up to a word that joins things."""
    window = []
    for word in reversed(folded[max(0, place - reach):place]):
        if word in JOINERS:
            break
        window.append(word)
    return window

# The words that make a line a meal question rather than a question about one ingredient.
MEAL_CUES = frozenset("""
make makes made making cook cooking bake baking baked meal meals dinner tea lunch supper brunch snack
idea ideas recipe recipes quick quickish something anything leftover leftovers use eat
""".split())

# The ways people ask what to do with an ingredient without a meal word ("what can I do with
# these", "use up the spinach").
# A meal wanted, said as a want rather than a question: "i fancy something with mince", "i could
# go for a curry". Without these a line with one ingredient fell foul of the "one ingredient is a
# question about that ingredient" guard below, and got nothing at all; the pantry can answer a
# want as well as a "what can I make".
MEAL_WANTS = ("i fancy", "i really fancy", "fancy something", "fancy a ", "could go for",
              "could murder", "in the mood for", "i'd love", "i would love", "i quite fancy",
              "i'd quite like", "i would quite like")

MEAL_PHRASES = MEAL_WANTS + ("what can i do with", "what do i do with", "what to do with", "use up",
                # "something with pasta", "make with leeks", "recipes for cabbage": one named
                # ingredient is enough when the line says it wants a dish made of it.
                "something with", "something quick", "something easy", "make with",
                "cook with", "recipes with", "recipes for", "recipe with", "recipe for",
                "ideas with", "meal with", "dish with", "recipe", "recipes", "idea", "ideas",
                "dinner ideas", "lunch ideas", "meal ideas",
                "what can i make", "what can i cook", "what should i make", "what should i cook",
                "thing to do with", "things to do with", "easiest thing to do with",
                "using up", "any ideas", "got left",
                # "what should I do with the rest of the potatoes" is the same question as
                # "what can I do with it", and people say both.
                "what should i do with", "what should i make", "what should i cook",
                "what else can i do with",
                # A list of what is in the kitchen is a meal question even without a "make":
                # "i only have eggs and potatoes", "ive got mushrooms and cream".
                "i have", "i've got", "ive got", "we have", "we've got", "weve got",
                "only have", "only got", "just have", "just got", "left in the",
                "in the fridge", "in the cupboard",
                "on their way out", "on the way out", "past its best", "past their best",
                "need using", "needs eating", "going over", "starting to go")

# A line that says what somebody brought home is a what-shall-I-do-with-it line: "i bought a
# chicken" and "i picked up some leeks" were a stock ack, and the food is the question. Only
# when the line also names something in the kitchen, so "i bought a car" stays where it is.
BOUGHT_PHRASES = ("i bought", "i've bought", "ive bought", "just bought", "i got a",
                  "i got some", "picked up a", "picked up some", "i brought home",
                  "we bought", "we got a")

# The phrases that ask what to cook, as opposed to saying what is in the kitchen ("i've got two
# cats, pickle and bean"). A line of these can carry a meal question out of another topic; a line
# that only says what it has cannot.
MEAL_ASK_PHRASES = MEAL_WANTS + ("what can i do with", "what do i do with", "what to do with",
                                 "use up", "using up", "any ideas", "ideas", "idea", "got left",
                                 "thing to do with", "things to do with",
                    "easiest thing to do with",
                    # "any ideas" and "what else": a follow-up that asks for ideas without
                    # naming a food is still asking what to cook with the one just named.
                    "what else", "anything else", "something else", "any suggestions",
                    "suggestions",
                    # "going soft", "needs using": the food is on its way out, which is a use-it-up
                    # question even when the line ends there.
                    "going soft", "gone soft", "going off", "on its way out", "needs using",
                    "to use up", "left over", "leftover",
                    # People say it of a bag of things, not one: "mushrooms on their way out",
                    # "the apples past their best". Same question, so the same answer.
                    "on their way out", "on the way out", "past its best", "past their best",
                    "need using", "needs eating", "going over", "starting to go",
                    # A surplus is the same question as a leftover: "i have too much mint",
                    # "i have a lot of mint" and "i have a glut of courgettes" all ask what to
                    # do with a food that is about to go over. The reading of the line does not
                    # always name the food as the subject (mint is also a word for money and for
                    # mint condition), so a line that says too much of something reaches the
                    # food tables on the surplus words alone.
                    "too much", "too many", "a lot of", "lots of", "loads of", "plenty of",
                    "glut of", "overrun with", "spare ")

# Food words strong enough to make a meal question on their own, even when the reading of the
# line missed the cooking topic.
FOOD_CUES = frozenset("""
dinner lunch supper brunch meal meals tea cook cooking bake baking recipe recipes idea ideas
leftover leftovers
""".split())

# A timing or a temperature wants a number, not a meal idea, and so does a question about why
# something went wrong.
NOT_MEAL_ASKS = frozenset("how_long how_much how_often how why".split())

# "How do I use up the spinach" is the same question as "use up the spinach": the "how" is how
# people start it, not a request for a method, and the use-up words are the whole ask. Only a
# line whose sole technique word is that opening "how" is read this way, and only when it says
# use-up: "how long does leftover rice keep" and "how do i reheat chicken" are other rows'
# questions and still stand the table down. bot/knowledge/meals.py reads its leftover row the
# same way, for the same reason.
USE_UP_ASKS = ("use up", "using up", "use it up", "use them up", "use this up",
               "use that up", "use these up", "use those up", "to use up", "uses up",
               "use the rest", "what can i do with", "what do i do with", "what to do with",
               "what can i make with", "what can i cook with", "what should i do with")

# "my four year old will only eat bread and cheese" names bread and cheese, but it is not a
# question about what to cook with them: it is a worry about a child who eats nothing else, and
# a toastie recipe answers the wrong thing. Read as a meal question, `eat` is enough of a cue on
# its own, so the shapes that say someone is *restricted* to a food have to be taken back out.
RESTRICTED_EATING = (
    "only eat", "only eats", "only ate", "only ever eats", "will only eat",
    "will only eats", "only drink", "only drinks", "wont eat", "won't eat",
    "will not eat", "wont touch", "refuses to eat", "refuse to eat", "refuses to touch",
    "eats nothing but", "eat nothing but", "eats hardly anything", "lives on",
    "fussy eater", "picky eater", "is that normal", "is it normal",
)
# A line asking what to use in place of a food wants a substitute, not a dish that needs it
# ("what can i use instead of eggs and milk" is not a request for a cheese omelette).
SUBSTITUTE_WORDS = frozenset("""
substitute substitutes substitution substitutions instead swap swaps swapping replace replaces
replacing replacement alternative alternatives
""".split())
SUBSTITUTE_PHRASES = ("out of", "ran out", "run out", "no more", "none left", "in place of")

# A line with one of these is asking whether something is safe, raw or off, which is a fact the
# knowledge entries answer, not a meal to cook.
PROBLEM_WORDS = frozenset("""
safe safely safety poison poisoning reheat reheated reheating raw undercooked overcooked
overcook undercook mould mouldy mold moldy expired expiry defrost thaw thawed freezer
ill sick stomach allergic allergy date burnt burned
pox chickenpox flu fever cough poorly unwell infection virus covid sore headache migraine
toothache nausea nauseous vomiting diarrhoea rash bleeding pregnant
""".split())

# An illness is not an ingredient: "i have chicken pox and a fever" names the word chicken, but
# the person is not asking what to cook with chicken, and the health answers own those lines.
# "a cold" and "a temperature" are phrases because both words have ordinary cooking senses.
# Things a food is used for that are not eating: crafts, decorations and games.
ACTIVITY_PHRASES = ("easter egg", "easter eggs", "play dough", "playdough", "decorate", "decorating",
                    "dye ", "dyed", "paint the", "painted", "craft", "costume", "trick or treat",
                    "stocking filler", "advent calendar", "science experiment", "volcano")

# A line that says it wants to make the thing itself names the food as the thing being made, not
# as something to cook with. The idea table answered all of these with a dinner: "can i make my own
# yoghurt from milk" was a raita, "can i make my own cheese" an omelette, "can i make my own cream
# cheese" macaroni cheese, "can i make my own butter" a cheese toastie and "can i make my own baked
# beans" a baked potato. The making rows answer them (butter, ice cream, pasta, a soft cheese,
# kefir, ketchup and yoghurt have one), and a food with no making row gets the honest hedge rather
# than a dinner nobody asked for.
MAKING_IT_YOURSELF_PHRASES = ("make my own", "make our own", "making my own", "making our own",
                              "made my own", "made our own", "make it myself",
                              "make them myself", "make it ourselves", "make them ourselves",
                              "make your own", "making your own", "from scratch")

ILLNESS_PHRASES = ("a cold", "my cold", "his cold", "her cold", "got a cold", "a temperature",
                   "runny nose", "sore throat", "feel sick", "feeling sick", "being sick")

# "What do I eat while I'm ill" is a food question, and the food is the plain one. The illness is
# named as a phrase, never as the single word "cold": "is it safe to eat cold rice" is a keeping
# question, not somebody with a cold.
SICK_PHRASES = ("im sick", "i'm sick", "i am sick", "ive been sick", "i've been sick",
                "being sick", "feel sick", "feeling sick", "felt sick", "im ill", "i'm ill",
                "i am ill", "been ill", "feeling ill", "poorly", "unwell", "stomach bug",
                "tummy bug", "sick bug", "food poisoning", "a cold", "my cold", "got a cold",
                "have a cold", "flu", "a temperature", "sore throat", "nauseous", "nausea",
                "throwing up", "vomiting", "hangover", "recovering from", "getting over",
                "no appetite", "lost my appetite", "off my food",
                # naming the bug rather than being ill with it: "how do i avoid cross
                # contamination" is the same prevention question as food poisoning is.
                "cross contamination", "cross-contamination", "contamination",
                # the worry without the name, but with the food in it: "how do i avoid
                # getting ill from food". A bare "get sick" is left out on purpose: it is
                # how an intolerance reads ("i get sick when i eat dairy").
                "ill from food", "sick from food")

# The eating words that make it a question about food rather than a report of being ill.
SICK_EAT_WORDS = ("eat", "eating", "food", "drink", "drinking", "appetite", "meal", "meals",
                  "dinner", "tea", "lunch", "breakfast", "snack", "keep down", "stomach",
                  # the cause rather than the illness: "cross contamination" is a food-safety
                  # word, and the entry's reply reads it as the prevention question.
                  "contamination", "contaminated", "cross contamination")


# Keeping it off the plate is the question before this one. "how do i not get food poisoning on
# holiday" names an illness and eats something ("food" is half of the illness), so the
# what-to-eat-while-ill answer took it and told a person who was not ill yet what to eat when
# they were. A line that asks how to avoid it is a prevention question, and the entry stands
# down on the shape of the ask rather than on a place, so "how do i avoid getting dehydrated"
# named with the same words still reaches whichever entry is about the water.
PREVENTION_ASK = re.compile(
    r"\b(?:avoid|avoiding|prevent|preventing|not\s+get|don'?t\s+get|dont\s+get|never\s+get|"
    r"stop\s+(?:me\s+)?getting|protect\s+(?:myself|yourself|against))\b"
    # Being ill is the thing the line is trying not to be: "how do i defrost a chicken without
    # giving myself food poisoning" is a kitchen question with a worry attached, and it was told
    # to eat toast and crackers. The worry comes in the same shapes as the ones above, only with
    # a verb of giving in place of avoid: "without poisoning everyone", "so we dont all get ill".
    r"|\b(?:without|so\s+(?:i|we|they|he|she)\s+don'?t|so\s+(?:i|we|they|he|she)\s+dont)\s+"
    r"(?:\w+\s+){0,3}?(?:poison\w*|getting\s+ill|get\s+ill|becoming\s+ill|going\s+off)\b")


# A prevention line that names no food and no place is the general question - "how do i avoid
# food poisoning", "how do i avoid food poisoning at home" - and it had no answer at all: the
# travel entry took it and gave street-food advice for a trip abroad, and once that stood down
# the line fell to the search hedge. The four rules below are the answer to it.
AWAY_FROM_HOME = frozenset("""
abroad holiday holidays travelling traveling trip trips camping mexico india egypt thailand
turkey morocco peru kenya bali spain france greece italy portugal america usa canada australia
airport plane flight hotel resort street beach restaurant takeaway abroad
""".split())

# "how do i avoid getting ill from food" is the same question in plainer words.
_SICK_FROM_FOOD = re.compile(r"\b(?:ill|sick)\s+(?:from|off)\s+food\b")

FOOD_SAFETY_RULES = (
    "Four things do most of the work: wash your hands before you cook and after you touch raw "
    "meat; keep raw meat and fish away from anything you eat raw - its own board, the bottom "
    "shelf of the fridge; cook meat right through and reheat leftovers until they are piping "
    "hot; and get anything that should be cold into the fridge within two hours, rice within "
    "the hour. The fridge wants to be 5C or below, and a use-by date only holds while the pack "
    "has stayed cold.")


def _eat_when_ill(memory, understood):
    """What to eat while you are ill: plain, small, and more to drink than you want."""
    text = ((understood or {}).get("clean") or "").lower()
    if PREVENTION_ASK.search(text) or "contamination" in text or _SICK_FROM_FOOD.search(text):
        # How to keep it off the plate, when the line names nothing that has its own answer:
        # a food ("how do i store rice without getting food poisoning") or a trip
        # ("how do i avoid food poisoning on holiday") is that entry's question, not this one.
        if ingredients(understood) or set(_plain_words(text)) & AWAY_FROM_HOME:
            return None
        return FOOD_SAFETY_RULES
    return ("Keep it plain and small: toast, crackers, rice, a banana, clear soup or plain "
            "yoghurt, and sip more than you feel like - little and often beats one big glass. "
            "Go back to proper meals over a day or two, and get advice the same day if you "
            "cannot keep any drink down or you are passing much less urine than usual.")

# A line asking whether something is still all right to eat is a food-safety question, not a
# request for a recipe, and the words for it are phrases rather than single words.
PROBLEM_PHRASES = ("from frozen", "still frozen", "when frozen", "cook it frozen", "is it frozen",
                   "still ok", "ok to eat", "okay to eat", "gone off", "left out", "off the "
                   "counter", "is it ok", "is it safe")

# "theres nothing in", "no food in the house": the same question as a full fridge, asked the
# other way round, and the useful answer is a short shopping list plus what it makes tonight.
EMPTY_PHRASES = ("no food", "nothing to eat", "nothing in the fridge", "nothing in the cupboard",
                 "nothing in the cupboards", "nothing in the kitchen", "bare cupboard",
                 "cupboard is bare", "cupboards are bare", "empty fridge")

# "whats for dinner when theres nothing in": the meal words are already in the line, so the
# vaguer forms are enough here.
EMPTY_ASK_PHRASES = ("nothing in", "nothing left in the", "nothing at all in",
                     "nothing in the house")

# The meal words that make a vague "nothing in" a kitchen line: "theres nothing in for tea" is
# about supper, and "i have nothing in the house to wear" is not. A wardrobe, a letter and a
# dog's bowl all have nothing in them, so the vague forms only count next to one of these.
MEAL_WORDS = frozenset("dinner tea supper lunch eat eating cook cooking food meal meals "
                       "bite takeaway order".split())

# A line about the dog's dinner is not a line about an empty kitchen.
PET_WORDS = frozenset("dog dogs cat cats puppy kitten hamster rabbit pet pets bird".split())

EMPTY_KITCHEN = ("An empty kitchen still makes supper: pasta with a tin of tomatoes and garlic, "
                 "eggs on toast, or rice with a tin of beans and chilli. The shop that fixes it is "
                 "short and cheap: eggs, pasta, rice, tinned tomatoes, a tin of chickpeas or beans, "
                 "onions, frozen peas, cheese, bread and milk. Those cover twenty dinners between "
                 "them, and the frozen and tinned things keep for months.")

_INGREDIENT_WORDS = {}
def _fold(word):
    """A word with its plural undone, so eggs/egg and tomatoes/tomato are one word."""
    word = str(word).lower().replace("\u2019", "'").strip(".,!?;:'\"")
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("es") and word[-3] in "sxzh":
        return word[:-2]
    if len(word) > 2 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _fold_meal_ideas():
    """Fold the older meal-ideas list into PANTRY, so one table answers every way of asking.

    The list at the top of the file and the pantry below hold the same knowledge kept twice: an
    ingredient's fuller idea there, a shorter one here, so the same ingredient was answered one
    way by a pair ("eggs and spinach") and another by a single name ("what can I make with
    eggs"), and an ingredient in neither table fell through to "I don't know" ("got some turkey
    mince in"). Each row joins the pantry row that already answers for it and adds any name the
    pantry did not have; a name that is nobody's yet becomes a row of its own. A name another
    row already answers for is left where it is, so "salmon" stays salmon and never becomes fish.
    """
    # "veg" and "vegetables" were aliases of broccoli, which answers a question about broccoli
    # wrongly: they are the vague word for whatever greens are in. They get a row of their own
    # below; in a pair they are dropped (VAGUE), because "mince and some veg" is one dinner.
    vague = {_fold(word) for word in VAGUE}
    for name in list(PANTRY):
        aliases, idea = PANTRY[name]
        kept = tuple(alias for alias in aliases if _fold(alias) not in vague)
        if kept and kept != tuple(aliases):
            PANTRY[name] = (kept, idea)
    claimed = {}
    for name, (aliases, _idea) in PANTRY.items():
        claimed.setdefault(name, name)
        for alias in aliases:
            claimed.setdefault(_fold(alias), name)
    for names, idea in MEAL_IDEAS:
        group = tuple(name for name in names if _fold(name) in vague)
        solid = tuple(name for name in names if _fold(name) not in vague)
        if group and all(_fold(name) in claimed for name in solid):
            # A row that leads with "vegetables" and lists real greens beside it is the idea for
            # the group word: each green already has its own row, so the idea is the veg row's.
            PANTRY.setdefault(_fold(group[0]), (group, idea))
            for name in names:
                claimed.setdefault(_fold(name), _fold(group[0]))
            continue
        # The row joins the row of the food it leads with, and only that one: a row written as
        # ("fish", "salmon", "cod") is an idea for fish, and folding it into the salmon row made
        # "cod" and "fish" answer "Roast salmon at 200C", which is a different fish. A later name
        # that already has a row of its own keeps it, because that row knows more.
        key = None
        for name in names:
            if _fold(name) in vague:
                continue
            key = claimed.get(_fold(name))
            break
        if key is None:
            key = _fold(names[0])
            alone = tuple(name for name in names
                          if _fold(name) not in claimed or name == names[0])
            PANTRY[key] = (alone, idea)
        else:
            aliases, short = PANTRY[key]
            extra = tuple(name for name in names
                          if _fold(name) not in claimed and _fold(name) not in vague)
            PANTRY[key] = (tuple(aliases) + extra, short)
            # The row keeps the pantry's own wording: the older list holds the same knowledge,
            # and the pantry's is the one the other entries already answer with.
        for name in names:
            claimed.setdefault(_fold(name), key)


_fold_meal_ideas()

for _name, (_aliases, _idea) in PANTRY.items():
    for _alias in _aliases:
        _INGREDIENT_WORDS[_fold(_alias)] = _name


# Every name the pantry answers for, longest first: a two-word name ("turkey mince", "chicken
# thigh") has to be tried before either of its words on their own, or one food counts as two.
_ALIASES_BY_LENGTH = sorted(((tuple(_fold(_alias).split()), _name)
                             for _name, (_aliases, _idea) in PANTRY.items()
                             for _alias in _aliases),
                            key=lambda pair: -len(pair[0]))

# The alias as people write it, because a reply says "frozen spinach" and not "frozen spinac":
# the folded parts are what the matcher sees, the alias is what the answer shows.
_ALIAS_TEXT = {tuple(_fold(_alias).split()): _alias
               for _name, (_aliases, _idea) in PANTRY.items()
               for _alias in _aliases}


# --- the same food in another form -----------------------------------------------------------
#
# "can i use frozen spinach instead" and "tinned tomatoes instead of passata" name one food in a
# different form, not a second food. The pair verdicts above need two foods, so they pass, and the
# pantry table read the line as a dish ("what can i make with spinach"). The adjustment is the
# same whichever food it is - water, salt, heat, time - so the table is per form and the food's
# own word goes into the sentence.
FORMS = (
    ("frozen", ("frozen", "freezer")),
    ("tinned", ("tinned", "canned", "tin of", "can of")),
    ("dried", ("dried", "dry")),
    ("jarred", ("jarred", "jar of")),
    ("fresh", ("fresh",)),
)

# "i havent got fresh tomatoes" is the same question the other way round: what they have run out
# of is the form they named, so the answer is what stands in for it.
OUT_ASKS = ("havent got", "havent", "dont have", "didnt have", "ran out", "run out", "out of",
            "no fresh")
OUT_OF_FRESH = ("Out of fresh {food}, tinned or frozen is the stand-in: tinned is the better one "
                "in a sauce, drained and given 10 minutes to lose the tinny edge, and frozen goes "
                "in straight from the bag for a soup or a stew. Only a salad really wants it fresh.")
# The same question the other way round for every form, not only the fresh one: what they have
# run out of is the form they named, so the answer is what stands in for it. "i havent got any
# tinned tomatoes" was answered "Tinned tomatoes, yes: drain off the liquid...", which is the
# answer to a question they did not ask, and "weve run out of dried lentils" the same.
OUT_OF_FORM = {
    "fresh": OUT_OF_FRESH,
    "tinned": ("Nothing tinned, so the same food in another form stands in: frozen goes in "
               "straight from the bag with 3 or 4 minutes extra, fresh wants adding later than the "
               "tin would and a taste for salt at the end, and dried beans or chickpeas want "
               "soaking overnight and 40 minutes in the pan. For tomatoes, passata, a carton of "
               "chopped ones or a spoon of puree does the tin's job."),
    "frozen": ("Nothing in the freezer, so fresh does the same job: it cooks faster and brings "
               "less liquid, so add it later than the recipe says and taste for salt at the end. "
               "Tinned works in anything simmered, and dried wants soaking first."),
    "dried": ("No dried {food}, so tinned is the stand-in: it is already cooked, so it goes in for "
              "the last 10 minutes rather than at the start, and a tin is roughly what 100g of "
              "dried would have given. Frozen needs no soaking either."),
    "jarred": ("No jar of {food}, so the fresh or frozen version does the job: a jar is drained "
               "and rinsed only because it is salty, so taste at the end and add a little more "
               "salt than you would have. Frozen goes in straight from the bag."),
}


FORM_ADVICE = {
    "frozen": ("Frozen {food}, yes: in a sauce, soup or curry it goes in frozen with 3 or 4 "
               "minutes extra, and anything wet wants thawing and squeezing first or the pan goes "
               "wet. Picked and frozen within hours, it cooks as good as fresh."),
    "tinned": ("Tinned {food}, yes: drain off the liquid, then taste before adding salt, because a "
               "tin is already seasoned, and give beans or chickpeas 10 minutes in a sauce to lose "
               "the tinny edge. Tinned tomatoes blended smooth are passata, and a tin is thinner "
               "than puree, so simmer it down by half to thicken."),
    "dried": ("Dried {food}, yes in anything cooked, at about half the weight of fresh, soaked or "
              "simmered first if it is a pulse or a mushroom and added early so there is time to "
              "soften. Fresh is for the end, where the green taste is the point."),
    "jarred": ("A jar of {food}, yes: drain or rinse before it goes in, and taste at the end, "
               "because a jar is saltier than the same thing cooked from scratch."),
    "fresh": ("Fresh {food} instead of frozen or tinned, yes, but fresh cooks faster and brings "
              "less liquid: add it later than the recipe says and check the salt at the end, "
              "because the tinned and frozen versions carry their own."),
}

# Frozen meat and fish is not the vegetable answer: it is thawed right through, or cooked from
# frozen with longer and slower heat, and the middle is what goes wrong.
FROZEN_MEAT = ("Frozen {food}, yes, but it has to be thawed right through first: overnight in the "
               "fridge on a plate on the bottom shelf, never on the worktop, then cooked as normal. "
               "Straight from the freezer it needs longer and slower, so the middle is done before "
               "the outside dries out. Fish thaws in a few hours and cooks in minutes.")
FROZEN_FRUIT = ("Frozen fruit is picked ripe and frozen within hours, so out of season it beats "
                "the fresh punnets: use it from frozen in a crumble, a smoothie or on porridge, "
                "or half thawed in yoghurt. It goes soft as it thaws, so it will not hold its "
                "shape in a tart; roast it from frozen with a spoon of sugar if you want it whole.")
FRUIT_WORDS = frozenset("""fruit fruits berry berries raspberry raspberries strawberry
    strawberries blueberry blueberries blackberry blackberries cherry cherries plum plums peach
    peaches mango mangoes pineapple banana bananas apple apples rhubarb currant currants
    gooseberry gooseberries""".split())


def _form_word(words, start, span):
    """The form the matched food is sold in: in its own name or just in front of it."""
    for word in words[start:start + span]:
        for form, names in FORMS:
            if word in names:
                return form
    for word in words[max(0, start - 2):start]:
        for form, names in FORMS:
            if word in names:
                return form
    return ""


def _form_swap(memory, understood, text=None):
    """The same food in another form, asked with an "instead"/"what can i use" line, or None."""
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = [_fold(word) for word in words]
    if text:
        folded += [_fold(word) for word in str(text).lower().split()]
    said = " ".join(folded)
    if not any(ask in said for ask in _SWAP_ASK):
        return None
    used = [False] * len(folded)
    first = None
    seen = []
    head = ""
    for parts, name in _ALIASES_BY_LENGTH:
        span = len(parts)
        for start in range(len(folded) - span + 1):
            if any(used[start:start + span]):
                continue
            if all(folded[start + offset] == parts[offset] for offset in range(span)):
                for offset in range(span):
                    used[start + offset] = True
                seen.append(name)
                form = _form_word(folded, start, span)
                if form and first is None:
                    first = (start, span, form, _ALIAS_TEXT.get(parts, " ".join(parts)), name)
                    head = next(names for one, names in FORMS if one == form)
                break
    if first is None:
        # "can i use frozen fruit instead of fresh" names a class the pantry has no row for, and
        # the freezer answers the same way for all of it.
        for index, word in enumerate(folded):
            if word in FRUIT_WORDS and _form_word(folded, index, 1) == "frozen":
                return FROZEN_FRUIT
        return None
    start, span, form, spoken, food = first
    # The key no longer names the foods, so the reply says which ones a form question is asked
    # about: fresh, frozen, tinned or dried is a real choice for those, and not for milk.
    if food not in FORM_FOODS:
        return None
    # A second, different food is the pair verdicts' question ("yoghurt instead of cream"), and
    # this entry would answer it with half an answer. The same food in another form is not:
    # "tinned tomatoes instead of passata" is still a form question, and the tin has its say.
    if any(other != food for other in seen):
        return None
    # "tinned tomatoes" already says the form, and the sentence says it too
    first_word = spoken.split()[0].lower() if spoken.split() else ""
    if first_word and any(first_word == form_word for form_word in head):
        spoken = " ".join(spoken.split()[1:]) or spoken
    # The lack has to come before the food: "frozen peas out of the bag" is about using them,
    # "i havent got frozen peas" is about not having them.
    if any(ask in " ".join(folded[:start + span]) for ask in OUT_ASKS):
        return OUT_OF_FORM[form].format(food=spoken)
    if form == "frozen":
        if food in MEAT:
            return FROZEN_MEAT.format(food=spoken)
        if food in FRUIT_WORDS:
            return FROZEN_FRUIT
    return FORM_ADVICE[form].format(food=spoken)


# "without cheese", "no tomatoes", "off dairy": the ingredient named is the one to leave out,
# so a line that rules something out must not be answered with a dish that needs it.
# The foods a form question is actually asked about: fresh, frozen, tinned or dried is a real
# choice for these and not for a loaf or a jar of curry paste. The reply still reads any pantry
# food, this is only what the key names, so one entry rather than one per food.
FORM_FOODS = ("spinach", "mushroom", "tomato", "pea", "sweetcorn", "bean", "chickpea", "lentil",
              "fish", "salmon", "prawn", "chicken", "mince", "turkey", "bacon", "potato",
              "onion", "carrot", "broccoli", "kale", "cabbage", "cauliflower", "courgette",
              "aubergine", "squash", "pepper", "leek", "apple", "banana", "lemon", "berry",
              "peach", "mango", "fruit", "herb", "herbs", "garlic", "chilli", "ginger",
              "blackberry", "raspberry", "strawberry", "blueberry", "cod", "haddock", "tuna",
              "sardine", "anchovy", "coconut", "date", "fig", "plum", "cherry", "gooseberry",
              "rhubarb", "gooseberries")

# The words those foods answer to, folded the way the line's words are.
_FORM_FOOD_WORDS = tuple(sorted({word
                                 for name in FORM_FOODS
                                 for alias in PANTRY.get(name, ((), ""))[0]
                                 for word in _fold(alias).split()}
                                | set(FORM_FOODS)))

# The form question: a form word, and a line that is asking to swap one form for another. The
# food itself is not in the key: a key that names every food in the pantry makes those words
# common to the whole table and costs the dish entries the rarity that lets them win ("quick
# dinner ideas using tinned tomatoes and pasta" went to the meal ideas instead of the sauce).
# Without the swap wording it is a dish question ("what can i make with fresh tuna"), and
# without a form word it is the pair verdicts' question ("milk instead of cream").
FORM_SWAP_WORDS = ("instead", "swap", "swapping", "substitute", "replace", "out of",
                   "ran out", "run out", "havent got", "havent any", "dont have", "didnt have",
                   "no fresh")
# Bare "canned" is left out of the key: "can" is read as the tinned form, so "can i use milk
# instead of cream" would score here too, and that line is the pair verdicts' question. "can of"
# stays, because the modal is never followed by "of".
ENTRIES.append(entry("form-swap", (tuple(word for _form, names in FORMS for word in names
                                        if word != "canned"),
                                  FORM_SWAP_WORDS),
                     # no bias: where a swap entry of its own exists ("dried herbs instead of
                     # fresh" is the dried-herbs row), that row is the one to answer.
                     _form_swap, ask=_SWAP_ASK,
                     # a keeping question is the KEEPS table's, not this one
                     avoid=("keep", "keeps", "keeping", "store", "storing", "last", "lasts",
                            "gone off", "going off", "mouldy")))


# A food behind one of these words is a food the line has not got, and "no", "without" and "out
# of" were here already. The have/has/had/did family was not, so "i havent got any potatoes" was
# read as potatoes in the house: the potatoes were named as an ingredient and kept in the plan,
# and the dinner built from that kitchen a turn later was a plate of mash. They are the same
# limit as "no potatoes" in the wording people actually use, so they belong in the same list.
NEGATIONS = frozenset("""
without no not except minus avoiding avoid hate hates hateful allergic dislike dont don't
never leave skip skipped out off
stand wont won't refuse refuses sick
havent haven't hasnt hasn't hadnt hadn't didnt didn't
""".split())

# A refusal is often a phrase, and the words that make it one sit two or three back from the
# food: "im not a fan of lentils" and "i cant stand halloumi" were read word by word, the food
# stayed in the pantry, and the idea that came back was a lentil dhal and a plate of halloumi.
RULING_OUT_PHRASES = ("not a fan of", "not a fan", "not keen on", "not fussed about",
                      "cant stand", "can t stand", "cannot stand", "sick of", "tired of",
                      "bored of", "fed up of", "fed up with", "had enough of", "gone off",
                      "allergic to", "instead of", "hate", "hates", "dislike", "dislikes",
                      "loathe", "not into")
REFUSAL_REACH = 6       # how far back from the food a refusal phrase is still about it
# The words that start a new thought, so a refusal in front of them is about another food: "no
# pasta but chicken" keeps the chicken.
CLAUSE_BREAK = frozenset("but though although however except apart besides instead also".split())


def _refused_before(folded, place):
    """True when a phrase in front of the food rules it out ("im not a fan of lentils")."""
    if place <= 0:
        return False
    window = []
    for word in reversed(folded[max(0, place - REFUSAL_REACH):place]):
        if word in CLAUSE_BREAK:
            break
        window.insert(0, word)
    plain = " " + " ".join(window) + " "
    return any((" " + cue + " ") in plain for cue in RULING_OUT_PHRASES)

# What a stated diet rules out. "eggs and spinach, i'm vegan" names its ingredients and then
# says one of them cannot be used, so a dish built on eggs is no answer even though eggs were
# named. The classes are coarse on purpose: a diet question is asked about whole foods.
FOOD_CLASSES = {
    "bacon": ("meat",), "chicken": ("meat",), "ham": ("meat",), "mince": ("meat",),
    "sausage": ("meat",), "prawn": ("shellfish", "fish"), "salmon": ("fish",),
    "tuna": ("fish",), "egg": ("egg",), "butter": ("dairy",), "cheese": ("dairy",),
    "cream": ("dairy",), "milk": ("dairy",), "yoghurt": ("dairy",),
    "bread": ("gluten",), "pasta": ("gluten",), "flour": ("gluten",),
    "tortilla": ("gluten",),
}

DIETS = (
    (("vegan", "plant based", "plantbased", "no animal"),
     ("meat", "fish", "shellfish", "dairy", "egg")),
    (("vegetarian", "veggie", "vego", "no meat"), ("meat", "fish", "shellfish")),
    (("pescetarian", "pescatarian"), ("meat",)),
    (("dairy free", "dairyfree", "lactose", "no dairy", "milk free"), ("dairy",)),
    (("gluten free", "glutenfree", "coeliac", "celiac", "no gluten", "wheat free"),
     ("gluten",)),
)

# The words that carry no food of their own, so a line made only of them and of pantry names is
# a list of what is in the kitchen and nothing else ("potatoes and cheese", "eggs, spinach").
FILLER = frozenset("""
a an the and or plus too also some a bit little half of with without im i am m we us my our
have has got get only just thats that it is are so oh hey hi and its ive weve some more
i'm im you're we're theyre
nah nope yeah yep yeh eh well ok okay hmm hm um umm er erm literally honestly actually
""".split())
# The words above include the things people say before the answer itself ("nah just eggs and
# some rice", "well some eggs and rice", "hmm just some flowers"). They carry no food and no
# refusal, so a line that is one of them plus foods is the list of what is in the kitchen: the
# bot asked "tell me what is in the fridge and I will pick properly", and the answer was being
# handed back to the person ("Got it - nah just eggs and some rice") instead of cooked with.

_DIET_WORDS = frozenset(word for _cues, _ruled in DIETS for _cue in _cues for word in _cue.split())

NEGATION_REACH = 3     # how many words before the ingredient still count as ruling it out
COOKED_REACH = 3       # how far back a "leftover"/"roast"/"mashed" still describes the ingredient

# A negation softened by one of these is not a refusal: "i dont have much cheese" and "im not
# sure about cheese" both still want cheese, and answering them with a list that has none in it
# ignores the only food the line named.
# "just" and "only" are in here for a different reason: "no, just eggs and rice" is the person
# turning down the bot's suggestion and naming what they have, and read as a negation of the eggs
# it answered "No egg then: a spoon of cornflour..." to a full fridge.
SOFTENED = frozenset("much many sure enough lots lot bit little some just only".split())

# A food word with one of these in front of it is part of the day's own object, not something to
# cook: an "easter egg", a "christmas cake" and a "chocolate egg" are answered by the day, not by
# the pantry. It also stops "easter egg ideas for toddlers" coming back as a scrambled egg recipe.
EVENT_HEADS = frozenset("""christmas easter thanksgiving halloween birthday wedding anniversary
christening funeral wake valentine valentines chocolate""".split())


def _renamed_by_an_event(folded, place):
    """True when the word just before the food makes it another thing ("easter egg")."""
    if place == 0:
        return False
    return folded[place - 1] in EVENT_HEADS


# The line read for its ingredients, worked out once for the words: a dozen rows about dishes
# and recipes ask the same question about the same line, so the second ask reads the card.
_READ_FOR_INGREDIENTS = {}
_READ_FOR_INGREDIENTS_KEEP = 4000


def _named_ingredients(understood):
    """Every pantry ingredient the line names, with whether the line rules it out.

    Returns (named, negated): the ingredient names in the order the line names them, and the
    ones a word like "no", "without" or "allergic to" in front of them takes back out again.

    The longest name wins: "turkey mince" is turkey rather than turkey and mince, and a word
    already used by a longer name is not counted twice, so one food in the kitchen gives one
    ingredient instead of two half answers.
    """
    if not isinstance(understood, dict):
        return [], []
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = [_fold(word) for word in words]
    # A slipped food name is still that food: "a chickn recipe", "im lookin for a recipe wiv
    # chickn" and "chickn and broccoli" named no ingredient at all, so "a chickn recipe" got
    # "Thanks for telling me" while "a chicken recipe" got the roast. The engine has already
    # repaired the slips in `plain`, in the same places and the same number of words, so the
    # table is read against the repaired line. It is swapped in place rather than added to the
    # end, because a name in the wrong place reads as a thing somebody ruled out.
    repaired = [_fold(word) for word in str(understood.get("plain") or "").split()]
    if len(repaired) == len(folded) and repaired != folded:
        folded = repaired
    told = _READ_FOR_INGREDIENTS.get(tuple(folded))
    if told is None:
        told = _work_out_ingredients(folded)
        if len(_READ_FOR_INGREDIENTS) >= _READ_FOR_INGREDIENTS_KEEP:
            _READ_FOR_INGREDIENTS.clear()   # a card of lines, not a leak
        _READ_FOR_INGREDIENTS[tuple(folded)] = told
    return list(told[0]), list(told[1])


def _work_out_ingredients(folded):
    """(the ingredients these folded words name, the ones they rule out).

    Every row about a dish or a recipe asks this about the same line, so the answer is worked
    out once for the words and kept (see _named_ingredients). An alias is only looked at when
    its first word is in the line - a 419-alias table against a six-word line is otherwise
    mostly questions with no answer, and this was 14% of a reply.
    """
    used = [False] * len(folded)
    present = set(folded)
    hits = []
    for parts, name in _ALIASES_BY_LENGTH:
        if parts[0] not in present:
            continue
        span = len(parts)
        for start in range(len(folded) - span + 1):
            if any(used[start:start + span]):
                continue
            if all(folded[start + offset] == parts[offset] for offset in range(span)):
                for offset in range(span):
                    used[start + offset] = True
                hits.append((start, name, span))
                break
    named, negated = [], []
    refused_ends = []
    for place, name, span in sorted(hits):
        if name in named:
            continue
        if _renamed_by_an_event(folded, place):
            continue
        named.append(name)
        before = folded[max(0, place - NEGATION_REACH):place]
        ruled = _refused_before(folded, place) or (
                any(word in NEGATIONS for word in before)
                and not any(word in SOFTENED for word in before))
        if not ruled and _on_a_list_already_ruled_out(folded, place, refused_ends):
            # A negation covers the whole list it starts: "i havent got any potatoes or carrots"
            # rules out both. Read one food at a time the second one is past the three words a
            # negation reaches, so the carrots were kept as food in the kitchen while the
            # potatoes were struck off, and the next "what can i cook tonight" planned carrot
            # soup for somebody who had just said they had no carrots.
            ruled = True
        if ruled:
            negated.append(name)
            refused_ends.append(place + span)
    return named, negated


# The words between two foods that make them one list, so the negation on the first covers the
# second. A word of its own between them is not a list, and neither is a clause break: "no
# potatoes but carrots are fine" still cooks with the carrots.
REFUSAL_JOINERS = frozenset("or and nor either plus also both".split())


def _on_a_list_already_ruled_out(folded, place, refused_ends):
    """True when the food at `place` is joined to one the line has already ruled out."""
    for end in refused_ends:
        between = folded[end:place]
        if between and all(word in REFUSAL_JOINERS for word in between):
            return True
    return False


def diet_exclusions(understood):
    """The pantry foods a stated diet rules out ("i'm vegan" rules out eggs, cheese and meat)."""
    if not isinstance(understood, dict):
        return []
    clean = str(understood.get("clean") or "").lower()
    words = understood.get("words") if isinstance(understood.get("words"), (list, tuple)) else None
    folded = [_fold(word) for word in (words or clean.split())]
    classes = set()
    for cues, ruled in DIETS:
        for cue in cues:
            if " " in cue:
                if cue in clean:
                    classes.update(ruled)
                    break
            elif cue in folded:
                classes.update(ruled)
                break
    if not classes:
        return []
    return [name for name, kinds in FOOD_CLASSES.items() if classes.intersection(kinds)]


# An idea for a food that needs nothing a diet rules out, so a line like "rice and no eggs" still
# gets something to cook: these name only their own food, and a word the line ruled out drops
# them the same way it drops a pantry idea.
WITHOUT = {
    "rice": "Fry the cold rice hard with frozen veg and soy sauce, or cook it in stock with a "
            "handful of chopped herbs.",
    "pasta": "Toss the pasta with olive oil, sliced garlic and a little chilli, and keep back a splash "
             "of the cooking water to loosen it.",
    "potato": "Cut the potatoes into wedges, toss with oil and salt, and roast at 200C (180C fan) for 35 "
              "minutes.",
    "potato_wedges": "",
    "bread": "Toast the bread and rub a cut garlic clove over it, then spoon over chopped tomatoes with "
             "olive oil.",
    "spinach": "Wilt the spinach in a hot pan with a little oil, garlic and a grate of nutmeg, 2 minutes.",
    "cabbage": "Shred the cabbage and fry it hard in oil with a pinch of salt until the edges char, 5 "
               "minutes.",
    "chickpea": "Roast a drained tin of chickpeas at 200C (180C fan) for 25 minutes with oil, salt and paprika.",
    "bean": "Fry a drained tin of beans with garlic, cumin and a tin of tomatoes, and simmer 15 minutes.",
    "lentil": "Simmer the lentils with a tin of tomatoes, cumin and stock for 20 minutes.",
    "tomato": "Halve the tomatoes and roast at 200C (180C fan) for 25 minutes with oil, salt and thyme.",
    "mushroom": "Fry the mushrooms hard in oil until they squeak and brown, then finish with garlic and "
                "parsley.",
    "courgette": "Slice the courgette thick, oil and salt it, and grill 4 minutes a side.",
    "pepper": "Roast the pepper halves at 200C (180C fan) for 25 minutes, then peel and dress with oil.",
    "carrot": "Roast the carrot batons at 200C (180C fan) for 30 minutes with oil, salt and cumin.",
    "onion": "Slice the onions thick and cook slowly in oil for 20 minutes until sweet and brown.",
    "banana": "Slice the banana over porridge, or mash it into a batter and fry small pancakes.",
    "apple": "Stew the apple in slices with a splash of water and cinnamon for 8 minutes.",
    "sweetcorn": "Fry a drained tin of sweetcorn in a hot pan with oil, chilli and lime, 5 minutes.",
    "pea": "Simmer the peas 3 minutes and crush them with oil, salt and mint.",
    "garlic": "Warm sliced garlic slowly in oil and spoon it over anything plain.",
    "lemon": "Squeeze the lemon over greens with oil and salt, or steep the zest in hot water for tea.",
    "oats": "Simmer the oats with water or a dairy-free drink for 5 minutes and top with fruit.",
    "egg": "Boil the eggs 7 minutes, cool them, and eat with salt and toast.",
    "milk": "Warm the milk with a spoon of honey and a pinch of cinnamon.",
    "cheese": "Grate the cheese over hot pasta or potatoes with plenty of black pepper.",
    "yoghurt": "Stir the yoghurt into soup off the heat, or spoon it over fruit.",
    "butter": "Melt the butter into hot potatoes or pasta with salt and pepper.",
    "cream": "Stir the cream into a pan of mushrooms off the heat with salt and pepper.",
    "flour": "Mix the flour with water and a pinch of salt into a batter for pancakes.",
}
WITHOUT.pop("potato_wedges")


def _is_food_list(folded, clean):
    """Whether the line is only foods, so the meal question is there with the words left out."""
    named = False
    for word in folded:
        if not word or word in FILLER or word in _DIET_WORDS or word in NEGATIONS:
            continue
        if word in _INGREDIENT_WORDS:
            # "veg" is the vague half of a list, never the list itself: "im veg" is somebody
            # saying what they eat, not a kitchen to build a dinner from, and it was answered
            # with a tray of roast vegetables instead of an "I'll remember that".
            if _INGREDIENT_WORDS[word] not in _VAGUE_KEYS:
                named = True
            continue
        return False
    return named


def ingredients(understood):
    """The pantry ingredients the line names, in the order it names them."""
    named, negated = _named_ingredients(understood)
    kept = [name for name in named if name not in negated]
    # "coconut milk" is one ingredient, not coconut plus milk: a name that is part of a longer
    # name in the same line ("milk" in "coconut milk") would otherwise get an idea of its own,
    # which is how half a tin of coconut milk was answered with a white sauce.
    kept = [name for name in kept
            if not any(name != other and name in other.split() for other in kept)]
    # A word in front can make it a different food: "bean sprouts" are not the Christmas
    # vegetable, and a stir fry of them does not want a butter-and-lid recipe.
    clean = str((understood or {}).get("clean") or "").lower()
    return [name for name in kept
            if not any(phrase in clean for phrase in NOT_THIS_FOOD.get(name, ()))]


def negated_ingredients(understood):
    """The pantry ingredients the line says it has not got ("but no flour", "without cheese")."""
    named, negated = _named_ingredients(understood)
    return [name for name in negated if name in named]


def _mentions(text, names):
    """Whether a reply names one of these pantry ingredients ("150g flour", "grated cheese")."""
    if not names:
        return False
    words = [_fold(word) for word in str(text or "").lower().split()]
    for word in words:
        name = _INGREDIENT_WORDS.get(word)
        if name is None:
            for ending in ("", "s", "es"):
                name = _INGREDIENT_WORDS.get(_fold(word.rstrip(",.")) + ending)
                if name is not None:
                    break
        if name in names:
            return True
    return False


def cooked_ingredients(understood):
    """The ingredients the line says are already cooked ("leftover roast chicken")."""
    words = understood.get("words") if isinstance(understood, dict) else None
    if not isinstance(words, (list, tuple)):
        words = str((understood or {}).get("clean") or "").split()
    folded = [_fold(word) for word in words]
    ready = []
    for place, word in enumerate(folded):
        name = _INGREDIENT_WORDS.get(word)
        if not name or name in ready:
            continue
        if not any(word in COOKED_WORDS
                   for word in _words_just_before(folded, place, COOKED_REACH)):
            continue
        before = folded[max(0, place - NEGATION_REACH):place]
        if any(word in NEGATIONS for word in before):
            continue
        ready.append(name)
    return ready


# What stands in for the meat when the line says they eat none of it. Saying the swap out loud
# is most of the help: "no meat please, what can i cook with chicken" is a person who wants a
# curry, not a lecture, and the rest of the ingredients still make the dish.
# What to cook instead, said without naming the food they have ruled out: main's rule is that a
# reply never says the word back to somebody who has just said they do not eat it.
MEAT_SWAPS = {"chicken": "chickpeas or tofu", "turkey": "chickpeas or lentils",
              "mince": "lentils or chickpeas", "sausage": "chickpeas or halloumi",
              "bacon": "mushrooms and smoked paprika", "ham": "mushrooms",
              "pork": "mushrooms or chickpeas", "lamb": "chickpeas or lentils",
              "beef": "lentils or mushrooms", "steak": "mushrooms or aubergine",
              "chorizo": "smoked paprika and mushrooms",
              "tuna": "chickpeas", "salmon": "chickpeas or tofu", "prawn": "chickpeas",
              "fish": "chickpeas or tofu"}

_VEG_WORDS = frozenset("vegetarian vegetarians veggie veggies vegan vegans".split())

_VEG_PHRASES = ("no meat", "meat free", "meat-free", "without meat", "dont eat meat",
                "don't eat meat", "doesnt eat meat", "does not eat meat", "eat no meat")

# Half the table eats no meat, so the one dish cooked for everybody has to be meat free. The
# count has to be next to the word, or "14 of us and my sister is veggie" would read as all 14.
_VEG_GUESTS = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|some|half|a few"
                         r"|\d+)\b[^.]{0,40}\bveg(?:gie|gies|an|ans|etarian|etarians)\b")

_VEG_DINNER = ("A red lentil dhal is the dinner I would cook: lentils, an onion, garlic, cumin "
               "and a tin of tomatoes simmered 20 minutes, with rice or bread. Or chickpeas and "
               "spinach: fry onion, garlic and spices, add a tin of chickpeas and a tin of "
               "tomatoes, simmer 15 minutes and stir spinach through at the end.")
# The price is only worth saying when money is the question: "what should i cook tonight" from a
# vegetarian is not asking what dinner costs.
_VEG_DINNER_CHEAP = " Both cost about 50p a head."

# "my sister is veggie" says nothing about the person asking: the diet words are about them, so
# the line is not read as a vegetarian's. A count is still a signal ("3 are veggies"), and that
# is what _VEG_GUESTS is for.
_VEG_ELSEWHERE = re.compile(r"\b(?:my|his|her|their|our)\b[^.]{0,30}"
                            r"\b(?:is|are|was|doesn'?t|does not|don'?t|do not|won'?t|will not)\b"
                            r"[^.]{0,30}\bveg")

_SELF_VEG = re.compile(r"\b(?:i'?m|im|i am|we'?re|we are|as a)\b[^.]{0,30}"
                       r"\bveg(?:gie|gies|an|ans|etarian|etarians)\b")


def _plain_words(text):
    """The words of a line, without the comma or full stop a word can carry at the end."""
    return re.findall(r"[a-z']+", str(text).lower())


def _veg_dinner(missing, cheap=False):
    """Two veggie dinners, unless one asks for a food the eater has ruled out.

    Its dhal comes "with rice or bread", and a coeliac reading that has just been told the list
    is gluten free is the one line that must not mention bread. What the two cost is said only
    when the line asked about money.
    """
    if _mentions(_VEG_DINNER, missing):
        return _any_meal(set(missing))
    return _VEG_DINNER + (_VEG_DINNER_CHEAP if cheap else "")


def _diet(folded, clean):
    """'vegan', 'vegetarian' or '': what the line says it, or its guests, can eat."""
    if _VEG_ELSEWHERE.search(clean) and not _SELF_VEG.search(clean):
        return ""
    if any(word in ("vegan", "vegans") for word in folded):
        return "vegan"
    if (any(word in _VEG_WORDS for word in folded)
            or any(phrase in clean for phrase in _VEG_PHRASES)
            or _VEG_GUESTS.search(clean)):
        return "vegetarian"
    return ""


def _recent_user_turns(memory, count=4):
    """What the person typed in the last few turns, oldest first."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return []
    return [str(turn.get("user") or "") for turn in turns[-count:]
            if isinstance(turn, dict)]


def _diet_from_turns(earlier):
    """The diet the eater said a turn or two ago, or "" when they said none."""
    for said in reversed(earlier):
        found = _diet(re.findall(r"[a-z0-9']+", said.lower()), said.lower())
        if found:
            return found
    return ""


# The cues a person's own refusal is said with, as against a bare "no" or "without" in front of
# a food, which the cupboard can be short of as easily as somebody can refuse it.
_BARE_NO_CUES = frozenset(("no", "none", "without", "not", "nothing"))

# The words that follow a food and make it a shortage rather than a refusal: "no flour left",
# "no cheese in the house", "no eggs at all today" (not "no eggs for him").
SHORTAGE_AFTER = frozenset(("left", "house", "home", "cupboard", "fridge", "freezer", "gone",
                            "shop", "shops", "supermarket", "kitchen", "larder", "pantry"))


def _refused_foods(text, families=False):
    """The foods the line says somebody will not eat, from the kitchen's own word list.

    AVOIDED above reads the families that make people ill - meat, dairy, nuts, gluten - and a
    bare "no"/"without" in front of them. The rest of the kitchen is named the same way and was
    not read at all: "my wife hates mushrooms, any ideas for dinner" got mushrooms on toast, and
    "my son wont eat onions what can i cook" got the toddler feeding answer. A refused food is a
    limit on the dinner in exactly the words of an allergy, so the meal picker has to see it.

    Only a cue near the food counts, and only across the little words that join them ("wont eat
    onions", "no more of those tomatoes", "no cheese at all"). "i dont know what to do with
    chicken" is not a ban: "know what to do with" is not one of them.
    """
    said = _fold(str(text or ""))
    # "i'm tired of pasta" and "i'm sick of rice" are refusals, but bare "tired" and "sick" are
    # not: "i am tired, is chicken ok for dinner" is a person with chicken in the fridge. The
    # phrase is what refuses, so it is folded into the plain "no" and the two bare words are not
    # cues at all.
    said = re.sub(r"\b(?:tired|sick|bored)\s+of\b|\bfed\s+up\s+(?:of|with)\b", " no ", said)
    refused = set()
    words = re.findall(r"[a-z']+", said)
    # The refusal is read forwards from the cue, not backwards from each food, so that every food
    # the cue governs is refused: "she wont eat fish or meat" refused the fish and went on to
    # offer chicken thighs, which is the food the same line had just ruled out. "or", "and" and
    # "nor" are what join two foods under one refusal, and the scan stops at the first word that
    # is neither a food, a joiner, nor one of the little words between ("wont eat any of the
    # onions").
    for start, word in enumerate(words):
        if word not in _REFUSAL_CUES:
            continue
        index = start + 1
        while index < len(words):
            here = words[index]
            # The pantry files every name with its plural undone, so the line has to be read the
            # same way: "my husband doesnt eat tomatoes what can i cook" kept its "tomatoes" and
            # the refusal was not seen, while the same words with the ask in front had been
            # rewritten to "tomato" by the reading engine and worked. `_fold` is the kitchen's
            # own plural rule, so potatoes, chillies and berries are read from either side.
            name = _INGREDIENT_WORDS.get(here) or _INGREDIENT_WORDS.get(_fold(here))
            if name:
                # "no flour left" and "no cheese in the house" say the kitchen has none of it,
                # which is the swap table's question and not a person refusing to eat it: the
                # food is followed by the word that makes it a shortage.
                after = words[index + 1:index + 3]
                if word in _BARE_NO_CUES and any(part in SHORTAGE_AFTER for part in after):
                    break
                refused.add(name)
                index += 1
                continue
            if here in FAMILIES:
                # A family name ("meat", "dairy", "gluten") is a diet card's question and not one
                # food's, so it is normally stepped over - but the food after it is still read
                # ("fish or meat"). A caller that has to honour the family, such as the swap
                # table checking that its substitute is not the food just ruled out, asks for it.
                if families:
                    refused.update(DAIRY if here == "lactose" else FAMILIES[here])
                index += 1
                continue
            if here in _REFUSAL_FILLER or here in _REFUSAL_JOINERS:
                index += 1
                continue
            break
    return refused


def refused_foods(understood):
    """The foods a line says somebody at the table will not eat, worked out by the kitchen.

    A reader that has to decide whether the line is about a food ruled out or about the food
    itself asks this, so both are read the same way: "she wont eat cheese what can i cook" is a
    dinner with cheese left out, not a question about cheese.
    """
    if not isinstance(understood, dict):
        return frozenset()
    said = str(understood.get("clean") or understood.get("text") or "")
    return frozenset(_refused_foods(said))


# What a line that asks what to cook says, once the word "eat" has been taken out of it: "my son
# wont eat onions" is the refusal and its substitute, not a dinner asked for, and "eat" is in
# MEAL_CUES for the lines that do ask ("what can i eat tonight").
DINNER_ASK_WORDS = frozenset("""
make makes making cook cooking meal meals dinner tea lunch supper snack idea ideas recipe recipes
something anything
""".split())


# The foods whose absence is never a limit on a dinner: nobody's dinner was going to have flour
# in it, so "no flour left" is the baking question and the no-flour loaf already says what to bake
# instead. Without this the line, which the store rewrites to "what can i make without flour",
# was answered with a potato hash that the flour had nothing to do with.
NOT_A_DINNER_LIMIT = frozenset(("flour",))

# "with no eggs" is the cupboard's absence, not a person's refusal: the line is asking what to
# use instead, which the substitute entry answers. Only a line that names a meal or a pan sends
# it to the dinner picker, and then the dish leaves the food out as it does for a refusal.
AND_NO = ("with no", "with none", "with not much", "with only")

# The meals and the pans that make "with no X" a dinner question rather than a substitute one.
DINNER_NAMED = frozenset("""
dinner dinners tea supper lunch meal meals main cook cooking cooked roast fry fried bake baked
""".split())

# A food the kitchen has none of is a different question: "no cheese in the house what can i
# make" already had a dinner, and "im out of butter" is the swap entries' line. Only a person
# refusing a food is this answer's business.
SHORTAGE_WORDS = ("ran out", "run out", "out of", "none left", "nothing left", "havent got",
                  "haven't got", "dont have", "don't have", "have no", "has no", "not got",
                  "no more", "all gone",
                  "in the house", "in the cupboard", "in the fridge", "in the freezer")


# The meals with an idea card of their own, which already leave out what the person cannot eat:
# "i dont eat cheese, any ideas for a quick lunch" is the packed-lunch answer's line, and a
# single dinner dish is a narrower answer to it.
LUNCH_AND_BREAKFAST = frozenset("lunch lunches breakfast brunch lunchbox lunchboxes".split())


# A person changing one thing in a dish they mean to keep is asking what stands in for it, which
# the substitute entries answer. A dish that has none of the thing in it is no answer at all:
# "no buttermilk, what else can i use" came back as a potato hash, which is a dinner for a line
# about baking. Only "what can i use" needs care, because "what can i use it for" is asking for a
# dish and its "it" is the food in hand.
_STAND_IN_ASK = ("instead", "instead of", "substitute", "substitutes", "sub for", "sub for it",
                 "swap", "swaps", "replace", "replacement", "in place of", "stand in for",
                 "what else can i use", "what else could i use", "what do i use instead")
_STAND_IN_USE = re.compile(
    r"what (?:can|could|do|should) i use(?!\s+(?:it|them|that|this|those|these|leftovers?"
    r"|the rest)\b)")


def asks_for_a_stand_in(understood):
    """True when the line is asking what stands in for a food, not what to cook with it."""
    said = _clean(understood) if not isinstance(understood, dict) else _clean(understood)
    if any(phrase in said for phrase in _STAND_IN_ASK):
        return True
    return bool(_STAND_IN_USE.search(said))


def a_dinner_without(understood, memory=None):
    """A dish for a line that rules a food out and asks what to cook, or None.

    "she wont eat cheese what can i cook" was answered with cheese's calorie figure, and "my wife
    wont eat bread what can i cook" with the loaf's method, which is the one thing they cannot
    use. The refusal is the kitchen's own reading (`refused_foods`), so the two agree on what a
    refusal is, and the dish is the pantry's, so it is the same dinner it picks for an allergy.
    A line that only says the food is refused keeps its substitute answer: nothing is being
    cooked yet, so there is no dish to leave it out of.
    """
    said = _clean(understood)
    if asks_for_a_stand_in(understood):
        # the thing is being changed, not the dinner: see _STAND_IN_ASK above
        return None
    if not _refused_foods(said):
        return None
    if not isinstance(memory, dict):
        memory = {}          # the readers below want a store to look in, never None
    if any(phrase in said for phrase in SHORTAGE_WORDS):
        return None
    if _refused_foods(said) <= NOT_A_DINNER_LIMIT:
        return None          # the baking cupboard, not the dinner: the substitute is the answer
    words = set(_said_words(understood))
    if any(phrase in said for phrase in AND_NO) and not words & DINNER_NAMED:
        # "what can i make with no eggs" is asked at the baking cupboard and wants the substitute
        # (60g of yoghurt, half a banana, flax); a dish of mince and cabbage answers nothing in
        # it. The same food said as a refusal, or with a meal named, is the dinner question.
        return None
    asking = any(phrase in said for phrase in MEAL_ASK_PHRASES)
    if not asking:
        asked = understood.get("asks") if isinstance(understood, dict) else None
        asking = bool(asked) and bool(words & DINNER_ASK_WORDS)
    if not asking:
        return None
    if any(word in said.split() for word in LUNCH_AND_BREAKFAST):
        return None          # those ideas are their own cards, and they respect the exclusion
    cooked = dish(understood, memory) or meal(understood, memory=memory)
    if not (isinstance(cooked, str) and cooked.strip()):
        return None
    return None if unusable(cooked, understood) else cooked


# What a refusal is said with: a plain "no mushrooms", a person who will not eat them, and the
# words somebody uses when they are bored of a food.
_REFUSAL_CUES = frozenset((
    "no", "not", "without", "never", "hate", "hates", "hated", "dislike", "dislikes",
    "refuse", "refuses", "refused", "wont", "won't", "doesnt", "doesn't", "dont", "don't",
    "cant", "can't", "cannot", "avoid", "avoids", "avoids", "off",
    "fussy", "banned", "allergic", "intolerant", "skip", "skipping"))

# "fish or meat", "chicken and bacon": one refusal governs both foods.
_REFUSAL_JOINERS = frozenset(("or", "and", "nor", "plus", "also"))

# The words that may sit between the cue and the food and leave it refused.
_REFUSAL_FILLER = frozenset((
    "eat", "eats", "eating", "have", "has", "having", "use", "uses", "want", "wants",
    # "she doesnt like nuts" and "he does not want any fish" put the feeling word between the
    # refusal and the food, and the reader stopped at it: the line was answered with the nuts
    # card rather than a dinner with none in it.
    "like", "likes", "liked", "love", "loves", "loved", "care", "cares", "keen",
    "the", "any", "more", "much", "really", "at", "all", "a", "an", "this", "that",
    "these", "those", "it", "them", "some", "my", "his", "her", "their", "our", "of",
    "food", "foods", "stuff", "things", "thing", "dish", "dishes", "kind", "sort",
    "me", "us", "him", "her", "to", "for", "with", "is", "are", "was", "were"))


def _dishes_without(banned):
    """The whole meals that have none of the foods in `banned`, the biggest first."""
    banned = {str(name) for name in banned}
    found = []
    for dish in DISHES:
        uses = tuple(dish.get("uses") or ())
        if not uses or any(name in banned for name in uses):
            continue
        if _mentions(dish.get("text") or "", banned):
            continue
        found.append(dish)
    return found


def _best_dish(found, ready=(), missing=(), avoid=(), diet=""):
    """The dish using the most of the ingredients found, so pairs beat single-ingredient ones.

    A dish is skipped when it would cook again something the line already has cooked, unless
    the dish names that ingredient in "cooked", and when its text is in avoid: a follow-up
    about the same food gets the next dish that fits rather than the same words again. With a
    diet, a dish with meat in it is skipped: the line said what it does not eat, so an idea it
    cannot cook is no answer.
    """
    best, best_uses = None, 1        # a dish needs two of them to count as the answer here
    trimmed = None
    for candidate in DISHES:
        uses = candidate["uses"]
        if diet and any(name in MEAT for name in uses):
            continue
        if not all(name in found for name in uses):
            continue
        if candidate.get("text") in avoid:
            continue
        if missing and _mentions(candidate["text"], missing):
            # The dish's own words ask for a food the line has not got. When that food is one of
            # its ingredients it cannot be made at all; when it is only the trimmings (the frittata
            # is spinach and eggs, and offers "cheese on top") the same dish is still the answer
            # with that sentence left off, and one dish with one time keeps the clock follow-up
            # working after it.
            if any(name in uses for name in missing):
                continue
            cut = _without_the_trimmings(candidate["text"], missing)
            if cut and trimmed is None and len(uses) > 1:
                trimmed = dict(candidate, text=cut,
                               without=tuple(sorted(name for name in missing
                                                    if _mentions(candidate["text"], (name,)))))
            continue
        # The same dish can be worded twice ("leek and potato soup" as a dish and as an idea for
        # leeks), so a dish whose own name is in what was just said is left out too.
        if avoid and all(word in _fold(" ".join(avoid)) for word in candidate["id"].split("-")):
            continue
        if any(name in missing for name in uses):
            continue
        keeps = candidate.get("cooked", ())
        if any(name in ready and name not in keeps for name in uses):
            continue
        if len(uses) > best_uses:
            best, best_uses = candidate, len(uses)
    return best or trimmed


SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _served_without(dish):
    """A dish said as itself with the trimmings left off ("A frittata, no cheese: whisk ...")."""
    left_out = " and ".join(dish.get("without") or ())
    text = str(dish.get("text") or "")
    name, colon, method = text.partition(": ")
    if colon and name and not _mentions(name, dish.get("without") or ()):
        return f"{name}, no {left_out}: {method}"
    return f"Without the {left_out}: " + (text[:1].lower() + text[1:] if text else text)


def _without_the_trimmings(text, missing):
    """The same dish with the sentences that offer a food the line has not got left off.

    A dish's own words offer more than its ingredients: "cheese on top is worth it" after the
    method, "serve with crusty bread" at the end. The offer is a sentence at the end, so it comes
    off whole and the method, with its one time, is what is left. A dish whose first sentence asks
    for the food is not this dish at all, and comes back empty for the caller to skip.
    """
    parts = [part.strip() for part in SENTENCE.split(str(text or "").strip()) if part.strip()]
    while len(parts) > 1 and _mentions(parts[-1], missing):
        parts.pop()
    if not parts or _mentions(parts[0], missing):
        return ""
    return " ".join(parts)




def dish(understood, avoid=(), memory=None):
    """The meal that uses most of the ingredients a line names, or None.

    Only for a line naming two or more pantry things: one ingredient on its own is covered by
    the entries, and those say more about it than one dish can. avoid holds what was already
    said, so a follow-up about the same food is not answered with the same words again.
    memory, when given, is read for what the eater ruled out a turn ago, so a dish is not
    cooked for somebody who said "I'm veggie" before naming the mince ("I'm veggie" then
    "mince and potatoes").
    """
    # "whats a good recipe for banana bread" names two foods, and a bread-and-banana dish is not
    # what it asked for: a bake has a recipe of its own.
    if _names_a_bake(understood):
        return None
    return meal(understood, dishes_only=True, avoid=avoid, memory=memory)


# "What should I eat when I'm ill" is a food question with a plain answer, and nothing in the
# knowledge base had it: the line fell through to the search hedge while a stove-and-saucepan
# answer was the thing the person wanted. Registered here because the reply reads the illness
# phrases, and the red flags stay with the health module.
ENTRIES.append(entry(
    "eat-when-ill", (SICK_PHRASES, SICK_EAT_WORDS), _eat_when_ill, bias=1,
    avoid=("blood", "chest pain", "cant breathe", "can't breathe", "short of breath",
           "pregnant", "weeks", "baby", "babies", "toddler", "my son", "my daughter",
           "my mum", "my dad", "my husband", "my wife", "my partner", "child", "children",
           "diarrhoea", "diarrhea", "three days", "four days", "a week", "doctor",
           "hospital", "medicine", "antibiotic", "tests", "why do i", "why am i",
           # a keeping question, not a somebody-who-is-ill question
           "cold rice", "cold chicken", "cold pizza", "left out", "gone off", "ok to eat",
           "safe to eat", "still ok", "is it ok",
           # and a mouth line is a dental one: "my teeth hurt when i have a cold drink" was
           # answered with what to eat when you are ill
           # "does tea with honey help a cold" asks whether a remedy works, not what to eat:
           # the honey-and-cough row names the remedy and answers it, so the does-it-help
           # shapes stand this row down.
           "help a cold", "help my cold", "help the cold", "help a cough", "help my cough",
           "help a sore throat", "help my throat", "does honey", "will honey", "honey help",
           "honey and lemon", "lemon and honey", "honey in warm water",
           #
           # An animal that is being sick is not a person who is: "my cat wont eat and is being
           # sick" and "my rabbit is off her food and being sick" were both told to eat toast
           # and crackers and to watch their urine output. The pet rows answer the animal, and
           # this row stands down for every animal the deck names, whether or not the line
           # remembers to say "my".
           "my cat", "my dog", "my puppy", "my kitten", "my rabbit", "my hamster",
           "my guinea pig", "my parrot", "my budgie", "my tortoise", "my pet", "my puppy",
           "cat", "dog", "puppy", "kitten", "rabbit", "hamster", "guinea pig", "parrot",
           "budgie", "tortoise", "the cat", "the dog", "the puppy", "the kitten",
           ) + TOOTH_OR_GUM))

# "is a potato a vegetable" and "are bananas berries" name food, but they ask what the
# food is; the pantry would read the words as an ingredient list and answer with a recipe.
# The category has to end the question (or be joined by "or") so "what is a good vegetable
# for roasting" is still a cooking question.
_WHAT_IS_IT = re.compile(
    r"\b(?:is|are)\s+(?:a|an)?\s*[a-z]+\s+(?:a|an)?\s*"
    r"(?:fruit|vegetable|berry|berries|tuber|root|grain|pulse)s?\s*(?:\?|$|or\b|,|\.)")

def _reads_as_news(understood, clean=""):
    """True when the line is news of a meal that happened, not a request for one.

    "we had dinner with no potatoes" names a meal word and a food left out, like "dinner with
    no potatoes please", and only the tense tells the two apart. The meal table already reads
    that difference, so its reading is the one used here.
    """
    from . import meals

    return meals.reads_as_news(understood, clean)

# Two foods on either side of an "or" are a choice, not a pair to cook together: "butter or oil"
# and "chicken or lamb" name two things and ask for one of them. The choice words are what says
# so - a line that merely mentions both ("potatoes and carrots", "chicken, then the butter") is
# still one dinner, and the two ideas below are right for it.
_CHOICE_WORDS = ("should i", "shall i", "do i use", "can i use", "could i use", "which",
                 "better", "instead", "rather", "or is", "or would", "or should", "or do i",
                 "what about", "worth using", "go for", "stick to")

# The other half of a choice is not always a food: "butter or oil" and "rice or pasta" pick
# between two things, and oil, water, stock or wine are what a pan is cooked in rather than an
# ingredient of its own, so the pantry has no row for them.
_COOKING_MEDIUM = ("oil|olive oil|water|stock|wine|milk|cream|margarine|ghee|lard|dripping|"
                   "suet|vinegar|lemon|honey|syrup|sugar|salt|pepper|flour|cornflour|"
                   "butter|yoghurt|juice|sauce|gravy|rub|marinade|foil|paper|trays?|tins?")

_ANY_FOOD_TEXT = None


def _any_food_text():
    """Every name the pantry answers to, longest first, as one alternation for the "or" test."""
    global _ANY_FOOD_TEXT
    if _ANY_FOOD_TEXT is None:
        names = sorted({_fold(str(alias)) for aliases, _idea in PANTRY.values()
                        for alias in aliases}, key=len, reverse=True)
        _ANY_FOOD_TEXT = "|".join(re.escape(name) for name in names if name)
    return _ANY_FOOD_TEXT


def _a_choice_of_foods(clean):
    """True when the line puts two foods on either side of an "or" and asks which to use."""
    low = _fold(str(clean or ""))
    if " or " not in low:
        return False
    if not any(word in low for word in _CHOICE_WORDS):
        return False
    foods = _any_food_text()
    if not foods:
        return False
    other = foods + "|" + _COOKING_MEDIUM
    return bool(re.search(r"\b(?:%s)\s+or\s+(?:%s)\b" % (foods, other), low))


def meal(understood, dishes_only=False, text=None, banned=None, diet=None, memory=None,
         avoid=(), pointed_back=False):
    """A meal idea for the ingredients a line names, or None when it names none it knows.

    understood: memory["understood"]. The line has to be a food question ("what can I make
    with...", "any dinner ideas with...", "use up the..."), read as the cooking topic, and it
    has to name at least one ingredient from PANTRY. A dish that uses more of the named
    ingredients wins, so eggs and spinach get the frittata rather than an omelette; without
    one, the line gets a quick idea for each of the first two ingredients it names.

    banned: the foods the eater has ruled out, this turn or in the turns before it. A dish or
    an idea that needs one of them is no answer ("I'm dairy free" then "what can I cook with
    the cheese" must not get cheese on toast). Left out, the line's own words are read for
    them, so "my partner doesnt eat cheese" never gets a cheese dish; a caller that also reads
    the turns before this one passes a wider set.

    diet: "vegetarian" or "vegan" when the eater said so a turn ago ("I'm veggie and skint this
    week" then "any ideas for dinner"). Left out, the line's own words decide.

    memory: the conversation, when the caller has it. What the person said a turn or two ago
    counts here too, so a diet or a food they ruled out is not forgotten the moment the next
    line names that food ("my partner doesnt eat cheese" then "potatoes and cheese").

    """
    if _names_a_bake(understood):
        return None
    if not isinstance(understood, dict):
        return None
    if _says_it_has_gone_off(understood.get("clean")):
        # A food that smells or has gone off is a sniff test, not an ingredient: "my salmon
        # smells is it still alright" and "my leftovers have gone slimy" were both answered with
        # a recipe here, because naming a food is all this table needs to pick a dish.
        return None
    # The line names a dish this kitchen has a recipe for: the dish is the subject and the table
    # below answers foods. "spaghetti bolognese recipe" is the bolognese method, not any pasta
    # dish, and "should i do a spag bol tonight" is that dish. A use-up line keeps the table: a
    # pan of last night's bolognese is a food in the fridge, not a dish to go and make.
    if names_a_dish(understood):
        _said = str(understood.get("clean") or "").lower()
        if not any(word in _said for word in _USE_UP_WORDS):
            return None
    # A line that is choosing a kind of ingredient is not asking what to make with it: "what
    # flour should i use for bread" names two pantry foods and was answered with a pancake
    # recipe. `picking` answers those, and this table stands down.
    from . import picking
    if picking.choosing(understood):
        return None
    shared = " ".join([str(understood.get("clean") or "")]
                      + [str(word) for word in (understood.get("words") or ())])
    # "can rabbits eat lettuce" names two foods and was answered with a braise and a salad: the
    # animal was read as the dinner. A question about what an animal may eat is the pets table's.
    if _feeding_ask(shared):
        return None
    if _pet_not_dinner(shared) or _reads_as_a_pet(shared):
        # A pet is not a joint. When the line asks what to cook it still gets an answer, one that
        # says which reading it took; a care question gets None and keeps its own answer.
        return _pet_or_meat(shared)
    if _a_brew_not_a_dinner(shared):
        # A milk question about a cup of tea names two pantry foods (oats and milk) and was
        # answered with porridge: the brew row in cooking_entries.py is the answer, and no
        # dish this table holds is one.
        return None
    if _a_plant_not_a_dinner(shared):
        # A tree, a bush or a plant is the garden's question, not the pantry's: "i bought a lemon
        # tree" was answered with lemon chicken. The food the line names is still the subject, so
        # a line that asks what to cook keeps its idea.
        return None
    if understood.get("kind") in ("empty", "greeting", "thanks"):
        return None
    words = understood.get("words") or ()
    folded = [_fold(word) for word in words]
    earlier = _recent_user_turns(memory)
    clean_now = str(understood.get("clean") or "").lower()
    whole = " ".join([clean_now] + [str(said).lower() for said in earlier])
    crowd = _crowd_ask(clean_now)
    if (not crowd and earlier
            and any(word in clean_now for word in _CROWD_FOOD + _CROWD_VERBS)):
        # The table is set a turn or two back: "im doing something for my wifes 50th", "about
        # twenty people i think", "what food would be easy". The count is in the conversation,
        # and the question is still the crowd dinner rather than a search hedge.
        crowd = _crowd_ask(whole)
    if banned is None:
        banned = frozenset(_excluded(" ".join(
            [str(understood.get("clean") or ""), " ".join(str(word) for word in words)]
            + earlier)))
    # A food somebody at the table will not eat is a limit on the dinner the same way an
    # allergy or a bare "no" is, and the kitchen's own word list is what reads it: "my wife
    # hates mushrooms, any ideas for dinner" was answered with mushrooms on toast.
    refused = _refused_foods(" ".join([str(understood.get("clean") or "")] + earlier))
    if refused - set(banned):
        banned = frozenset(banned | refused)
    if text is not None:
        # A follow-up read with the topic put back in ("can you remember that?", "what about a
        # 3kg one") names an ingredient only through the context, and the person did not ask
        # what to cook. The pantry answers the line they typed, so it has to name something.
        lower = str(text).lower()
        typed = str(understood.get("text") or "").lower()
        repaired = str(understood.get("plain") or "").lower()
        if repaired and repaired != typed and lower == typed:
            # The caller hands over the line as it was typed, and a food word typed with a
            # slip ("a chickn recipe") is not a word this table knows: the engine has already
            # repaired it, and the repaired line is the one that names the food, so the check
            # below reads it. Only when the text is that same typed line, because a caller
            # that put the context into it is asking about the context, not about a repair.
            lower = repaired
        own = [_fold(word) for word in lower.split()]
        if (not any(word in _INGREDIENT_WORDS for word in own)
                # "theres nothing in for tea" says the kitchen is empty in the words of a
                # line that names no food, which is the line the empty-kitchen answer is
                # for: the pantry used to turn it down and the ack took the turn.
                and not any(phrase in lower for phrase in EMPTY_PHRASES)
                and not any(phrase in lower for phrase in EMPTY_ASK_PHRASES)
                # "what can i do with what's left" names the food in the turn before this one,
                # and the leftover idea answers the line they typed. The use-up ways of asking
                # count too: "what can i do with leftover curry" names a food this table knows
                # by its phrase rather than by a single word, so no word in it is a pantry word,
                # and the row that answers "how do i use up leftover curry" stood down only
                # because the question opened differently.
                and not any(phrase in lower for phrase in LEFT_POINTER + USE_UP_ASKS)
                # ...unless the line brings something else to work with: a table to feed.
                and not crowd):
            return None
    asks = set(understood.get("asks") or ())
    # "how do i cook for a crowd" is a how-to in form and a dinner question in substance: at a
    # table of eight the question is what to cook, not which pan to use. "how do i use up the
    # spinach" is the same shape one size smaller: the only method word is the opening "how"
    # and the line says use-up, so the food is the question.
    if (asks & NOT_MEAL_ASKS and not _crowd_ask(understood.get("clean") or "")
            and not (asks & NOT_MEAL_ASKS == {"how"}
                     and any(phrase in str(understood.get("clean") or "").lower()
                             for phrase in USE_UP_ASKS))):
        return None
    if any(word in PROBLEM_WORDS for word in folded):
        return None
    if any(word in SUBSTITUTE_WORDS for word in folded):
        return None
    clean = str(understood.get("clean") or "").lower()
    if _WHAT_IS_IT.search(clean):
        return None
    if _VEG_GUESTS.search(clean):
        # Somebody else at the table eats no meat ("theres 14 of us and 3 are veggies"), so the
        # one dish cooked for everybody has to be meat free. Only this line counts: a diet
        # stated for a guest is not the asker's own, which is what _diet is for.
        banned = frozenset(banned | MEAT)
    # "Can I use milk instead of cream" names two ingredients, but it is a question about one of
    # them, and a dish built from both answered something else.
    if any(phrase in clean for phrase in SUBSTITUTE_PHRASES):
        return None
    if any(phrase in clean for phrase in PROBLEM_PHRASES):
        return None
    # A line that says what someone will *only* eat is a fussy-eater question, not an
    # ingredients question, whatever food it names.
    if any(phrase in clean for phrase in RESTRICTED_EATING):
        # A line that says somebody will not eat a food is the fussy-eater worry when it is about
        # the eating ("my four year old will only eat bread and cheese"), and a dinner to pick when
        # it is a limit on the dinner and the line asks for one: "my son wont eat onions what can i
        # cook" got the toddler feeding answer, which is about getting a new food tried rather than
        # about the onion in the dinner. The refusal has to name a food and the line has to ask
        # for something to cook for this to be a dinner question.
        if not (any(word in MEAL_CUES for word in folded) and _refused_foods(clean)):
            return None
    if any(phrase in clean for phrase in ILLNESS_PHRASES):
        return None
    # A food named as the raw material for an activity is not dinner: "easter egg ideas for
    # toddlers" and "what can i dye with beetroot" want something to make *with* it, and a plate
    # of scrambled eggs answers the wrong question.
    if any(phrase in clean for phrase in ACTIVITY_PHRASES):
        return None
    if any(phrase in clean for phrase in MAKING_IT_YOURSELF_PHRASES):
        return None                      # the making question, not what to cook with it
    # "there is no food in the house" is the kitchen question asked the other way round. It is
    # checked before the topic, because that line reads as a home question, and the phrases that
    # name food are narrow enough to keep a wardrobe or a pet out of it.
    empty_kitchen = any(phrase in clean for phrase in EMPTY_PHRASES)
    if not empty_kitchen and any(phrase in clean for phrase in EMPTY_ASK_PHRASES):
        # the vague forms need a meal word beside them: see MEAL_WORDS
        empty_kitchen = any(word in MEAL_WORDS for word in folded)
    if empty_kitchen and not any(word in PET_WORDS for word in folded):
        return EMPTY_KITCHEN
    asked = (any(word in MEAL_CUES for word in folded)
             or any(phrase in clean for phrase in MEAL_PHRASES)
             # "what can i feed 20 people" and "what food for a table of twenty" name the table
             # and the food and no meal word at all, and they are the same question
             or crowd)
    bought = any(phrase in clean for phrase in BOUGHT_PHRASES)
    # "i bought a chicken" is its own way of asking what to do with it.
    asked = asked or bought
    asks_what_to_cook = (any(word in MEAL_CUES for word in folded)
                         or any(phrase in clean for phrase in MEAL_ASK_PHRASES))
    named = ingredients(understood)
    # The reading can put a food line in another topic: "half a cabbage" is a fraction before it
    # is a vegetable, and "i bought a whole chicken" is a purchase. When the line names something
    # in the kitchen and asks what to do with it, that is a meal question whatever the topic says.
    if (understood.get("topic") not in ("cooking", "food-and-drink")
            and not any(word in FOOD_CUES for word in folded)
            and not (named and (asks_what_to_cook or bought))
            # "what can i feed 20 people" reads as no topic at all and names no food cue word,
            # and the table is the subject: the count is what makes it a cooking question.
            and not crowd
            and not _is_food_list(folded, clean)):
        # "half a cabbage and some mince" reads as a maths line because of the "half", but a line
        # that is only foods is still the kitchen question.
        return None
    if not (asked or _is_food_list(folded, clean)):
        return None
    # "some veg" is not an ingredient, it is the vague way of saying there are vegetables in:
    # counting it as one half of a pair answered "mince and some veg" with two whole recipes.
    found = [name for name in named if name not in _VAGUE_KEYS
             and name not in VAGUE] or named
    missing = list(negated_ingredients(understood))
    # The foods the line itself turns down, before a diet adds the ones it never named. Only
    # these are a limit the person said out loud: a denied condition ("im not coeliac") reads
    # as the foods it would take away by `diet_exclusions`, and it does not take any away.
    said_no = list(missing)
    # A diet is a ruled-out food that was never named: vegan takes the eggs and the cheese out,
    # so the line gets something built on what is left rather than a dish it cannot eat.
    for name in diet_exclusions(understood):
        if name in found:
            found = [other for other in found if other != name]
        if name not in missing:
            missing.append(name)
    if banned:
        # A food ruled out this turn, or a turn or two ago, is no more use than one they have
        # not got: the idea that needs it is dropped the same way.
        refused_here = [name for name in found
                        if name in banned or any(part in banned for part in name.split())]
        missing.extend(refused_here)
        # A food nobody at the table will eat is not something to cook with either: the line
        # named it to rule it out. Left in `found` it counted as the one ingredient a line has
        # to ask what to cook with, and the dinner question it really is was passed on.
        found = [name for name in found if name not in refused_here]
    diet = diet or _diet(folded, clean) or _diet_from_turns(earlier)
    if not found:
        if any(phrase in clean for phrase in EMPTY_ASK_PHRASES):
            return EMPTY_KITCHEN
        # A table of people with no food named still has an answer: one big oven dish. "im having
        # 12 people over for dinner" and "4 people coming for dinner what should i cook" name no
        # ingredient, and "Got it." is not an answer to either.
        if crowd:
            return _crowd_meal(banned, _occasion(whole), _crowd(whole))
        # "what can i do with what's left" names no food: the food is the one the turns before
        # this one put on the table, and it is already cooked, so the leftover idea is the answer.
        if earlier and any(phrase in clean for phrase in LEFT_POINTER):
            for said in reversed(earlier):
                for name in ingredients({"words": str(said).lower().split(),
                                         "clean": str(said).lower()}):
                    if name in LEFTOVER_IDEAS:
                        return LEFTOVER_IDEAS[name]
        if diet:
            # "im vegetarian and skint, what should i make for dinner" names nothing in the
            # kitchen, so there is no dish to fit; the useful answer is a cheap one that fits
            # what they eat, not a shrug. A table of guests on top of that gets one big dish.
            whole = " ".join([clean] + [said.lower() for said in earlier])
            if _crowd(whole) >= 6 or _occasion(whole):
                return _crowd_meal(banned, _occasion(whole), _crowd(whole))
            return _veg_dinner(set(banned) | set(missing),
                              any(word in CHEAP_PLAN_WORDS for word in _plain_words(whole)))
        # "dinner without potatoes", "dinner with no potatoes please", "no mushrooms for dinner
        # please": the only food the line names is the one it leaves out, so there is nothing to
        # build a dish from and the table passed - a line that plainly asks for a dinner was met
        # with "I'm listening, say more if it helps". A meal word and a food ruled out, with no
        # other food named, is a request for a dinner that leaves that food out, and the default
        # list already knows what to do with what was ruled out. A line about the meal that
        # happened ("we had dinner with no potatoes") is news, and news is not a request.
        if _refused_foods(clean) and banned:
            # Somebody will not eat a food and the line names nothing else to cook with, so the
            # answer is a dinner that has none of it in rather than a shrug: "my son wont eat
            # onions what can i cook" used to get the toddler feeding answer, and "my wife
            # hates mushrooms, any ideas for dinner" the mushrooms on toast she just refused.
            # Only a food *this turn* rules out, or somebody who will not eat one: an allergy or
            # a diet the store already holds is a different card's question ("im coeliac" then
            # "what can i cook" is the gluten-free list, and a single dish answers less of it).
            for dish in _dishes_without(banned):
                if dish.get("text") and dish["text"] not in avoid:
                    return dish["text"]
        if said_no and any(word in MEAL_WORDS for word in folded) \
                and not _reads_as_news(understood, clean):
            return _any_meal(set(banned) | set(said_no))
        return None
    no_meat = bool(diet) or bool(MEAT & set(banned))
    leftover = _leftover(folded, clean)
    if (len(found) == 1
            and not pointed_back
            and not bought
            and not _is_food_list(folded, clean)
            and not any(phrase in clean for phrase in MEAL_PHRASES)
            and not leftover
            and not (no_meat and any(name in MEAT for name in found))):
        # One ingredient with no "what can I do with it" is a question about that ingredient
        # itself ("what's the best way to cook rice"), which the entries answer or honestly pass.
        # Meat and a diet that eats none of it is the exception: what to use instead is the answer.
        # A leftover is the other exception: it is already cooked, and the leftover idea is the
        # only answer that starts from that ("what can i make with leftover roast chicken").
        return None
    swap = ""
    if no_meat:
        # They have meat in and eat none of it, or somebody at the table does not: say what to put
        # in its place, then cook with the rest of what they named rather than sending a recipe
        # they will not make.
        left = [name for name in found if name in MEAT]
        if left:
            meat = left[0]
            instead = MEAT_SWAPS.get(meat, "chickpeas")
            swap = f"{instead[0].upper() + instead[1:]} do the same job in most dishes. "
            # The idea given has to be for what was named as the swap, or the two sentences
            # disagree ("lentils or butter beans..." then a chickpea recipe).
            picked = []
            for word in re.findall(r"[a-z]+", instead):
                name = _INGREDIENT_WORDS.get(_fold(word))
                if name and name not in banned:
                    picked.append(name)
                    break
            # The swap leads, but the rest of the line still counts: "chicken and rice" wants a
            # dish built from the chickpeas and the rice, not from the chickpeas alone.
            found = (picked or ["chickpea"]) + [name for name in found if name not in MEAT]
    best = _best_dish(found, cooked_ingredients(understood), missing, avoid, diet)
    if best is not None:
        if best.get("without"):
            # The same dish, offered without the trimmings the line has not got. It is said as that
            # and not as the dish again, or the second answer reads as the first one repeated.
            return swap + _served_without(best)
        return swap + best["text"]
    if dishes_only:
        return None
    # A leftover is not always answered by the pantry's idea for the food. "Roast beetroot whole
    # and unpeeled at 200C for an hour" is how to cook a beetroot from raw, and the one in the
    # fridge is already cooked and needs a use, not an hour in the oven; the same for "Quinoa:
    # rinse it, simmer 15 minutes". Where the idea names a dish it is a use and stays the answer
    # ("Leek and potato soup", "A 15-minute tomato sauce"), which is what the dish words decide.
    from . import meals
    if (any(word in LEFTOVER_WORDS for word in folded)
            or any(phrase in clean for phrase in LEFTOVER_PHRASES)):
        for name in found:
            row = PANTRY.get(name)
            idea = row[1] if row else ""
            if not idea or _mentions(idea, missing) or idea in avoid:
                continue
            if meals.idea_is_a_dish(idea):
                continue
            # Their own word for it, so a plural stays plural in "Leftover parsnips: ...".
            said_name = name
            for word in re.findall(r"[a-z]+", clean):
                if _fold(word) == _fold(name) or _fold(word) == name:
                    said_name = word
                    break
            use = meals.use_it_up(said_name)
            if use:
                return use
    if not swap and (any(word in LEFTOVER_WORDS for word in folded)
                     or any(phrase in clean for phrase in LEFTOVER_PHRASES)):
        for name in found:
            if name in LEFTOVER_IDEAS and LEFTOVER_IDEAS[name] not in avoid \
                    and not _mentions(LEFTOVER_IDEAS[name], missing):
                if name == "milk" and _mentions(clean, PLANT_MILKS):
                    continue  # coconut, oat, soy and almond milk have their own ideas
                return LEFTOVER_IDEAS[name]
    # An idea that asks for something the line has not got is no answer ("butter and eggs but no
    # flour" must not get shortbread), so it is dropped rather than sent.
    # A line that names two foods and asks to choose between them ("butter or oil", "chicken or
    # lamb") is a pick, and one idea for each is two answers to a question with one: "should i
    # cook onions in butter or oil" got shortbread and onion soup. The pick is answered by the
    # row that knows the pair, and this table passes.
    if _a_choice_of_foods(clean):
        return None
    ideas = [PANTRY[name][1] for name in found[:2]
             if not _mentions(PANTRY[name][1], missing) and PANTRY[name][1] not in avoid]
    if not ideas:
        # Nothing left the line can eat: an idea for what it does have beats an honest shrug,
        # as long as that idea asks for nothing the line ruled out.
        ideas = [WITHOUT[name] for name in found[:2]
                 if name in WITHOUT and not _mentions(WITHOUT[name], missing)
                 and WITHOUT[name] not in avoid]
    said = " ".join(ideas) if ideas else None
    # A follow-up about the same food is not answered with the words just given ("broccoli and
    # cheese" then "what can I make with them" is not the same two ideas a second time).
    if said is not None and said in avoid:
        return None
    return said


def _meal_texts():
    """Every whole-meal answer this table can give, so a follow-up can tell one from an entry."""
    texts = [dish["text"] for dish in DISHES if dish.get("text")]
    for name in PANTRY:
        texts.extend([PANTRY[name][1], LEFTOVER_IDEAS.get(name, ""), WITHOUT.get(name, "")])
    texts.extend([EMPTY_KITCHEN, *EMPTY_ASK_PHRASES])
    return frozenset(text.strip() for text in texts if text)


_MEAL_TEXTS = _meal_texts()
# The method of each, after the dish's name: a dish served without the trimmings it offered says
# its own method, cut short, under a name of its own ("A frittata, no cheese: whisk 6 eggs ...").
_MEAL_METHODS = tuple(text.partition(": ")[2] for text in _MEAL_TEXTS if ": " in text)


def _is_meal_answer(said):
    """True when this reply is one whole meal from this table, with or without its trimmings."""
    said = str(said or "").strip()
    if not said:
        return False
    if said in _MEAL_TEXTS:
        return True
    method = said.partition(": ")[2]
    return len(method) > 40 and any(m.startswith(method) for m in _MEAL_METHODS)


# "How long does that take?" after a meal idea is a question about the answer just given, so the
# time it already stated is the answer. Numbers come out of the reply in words or digits ("ten
# minutes", "1 hour 40"), because the dish lines are written both ways.
_NUMBER_WORD = (r"\d+|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|"
                r"twenty|thirty|forty|fifty|sixty|ninety")
_TIMING = re.compile(
    r"\b(?:%s)(?:\s*(?:to|or|-|and a half)\s*(?:%s))?\s*(?:minutes?|mins?|hours?|hrs?)\b"
    % (_NUMBER_WORD, _NUMBER_WORD), re.I)

# A timing follow-up points back at the answer ("how long does that take", "how long for it").
_BACK_REFERENCE = frozenset("""
that it this those these there them one dish recipe meal dinner supper thing
""".split())
_WORD = re.compile(r"[a-z']+")

# "How long does that keep?" points back at the dish just as "how long does that take" does, but
# the answer is a keeping fact, not the cooking time. These are the words that make the question
# a keeping one; the cooking senses ("how long do i keep it in the oven") are turned down below.
_KEEP_WORDS = frozenset("""
keep keeps keeping kept store stores stored storing fridge freezer freeze frozen last lasts
lasting leftover leftovers
""".split())
# How long a thing keeps is measured in days and weeks as often as in a cooking time, so the
# sentence that answers it is the one with either figure in it.
_KEEP_TIME = re.compile(
    r"%s|\b(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten)\s*"
    r"(?:days?|weeks?|months?|years?)\b" % _TIMING.pattern, re.I)

# The ask a keeping follow-up makes: "how long does that keep", "how many days will it last".
_KEEP_TIME_ASK = re.compile(r"\bhow (?:long|many (?:days?|weeks?|hours?|months?))\b", re.I)

# A keeping question is about the food, never about the pan: "how long do i keep stirring it" and
# "how long does it keep in the oven" are cooking questions with a keeping word in them.
_COOKING_SENSE = frozenset("""
oven pan hob grill microwave boil boiling simmer fry frying stir stirring whisk whisking
roast roasting bake baking cook cooking heat
""".split())

COOKED_KEEPING = ("Once it is cooked, cool it within two hours and keep it covered in the fridge: "
                  "it keeps 3 to 4 days, and you can reheat it once, piping hot all the way "
                  "through. Anything with rice or chicken should go in the fridge straight away "
                  "rather than sit out.")


# A reply that really says how long something keeps, rather than using "keep" for something
# else ("keep stirring", "keep the pan hot"). The figure is what makes it a keeping answer.
_SPEAKS_OF_KEEPING = re.compile(
    r"\b(?:keeps?|keeping|lasts?|lasting|stays? good)\b[^.]{0,60}\b(?:days?|weeks?|months?|years?"
    r"|hours?)\b"
    r"|\b(?:in|into|out of|from) the fridge\b|\bfreez(?:e|es|er|ing)\b"
    r"|\b(?:days?|weeks?)\b[^.]{0,40}\bin the fridge\b", re.I)


def speaks_of_keeping(reply):
    """Whether a reply says how long something keeps, so a keeping line can be answered by it."""
    return bool(isinstance(reply, str) and _SPEAKS_OF_KEEPING.search(reply))


def keeping_ask(understood):
    """True for "how long does a cooked chicken last" - how long it KEEPS, not how long it cooks.

    The words have to ask how long, carry a keeping word, and carry none of the words that put the
    question back in the oven or the pan: "how long do i keep stirring it" is cooking.
    """
    if not isinstance(understood, dict):
        return False
    clean = str(understood.get("clean") or "").lower()
    words = set(_WORD.findall(clean))
    # "roast" is the one word that is a joint of meat as often as it is a verb: "how long does a
    # roast keep" is a keeping question, and the words that only ever name the doing are left to
    # rule this out.
    if not words & _KEEP_WORDS or words & (_COOKING_SENSE - {"roast", "roasting"}):
        return False
    return bool(_KEEP_TIME_ASK.search(clean))


# A dish answer does not always carry its time in figures: "fry onion, garlic, ginger and cumin,
# add the chickpeas and a splash of stock, then wilt the spinach through" is a recipe with nothing
# to keep unless it says so. A step of cooking is what makes the thing on the plate cooked, so the
# cooked-food keeping fact is the answer to "how long will that keep" after one of these too.
# The sentence that states the whole dish's time, rather than one step's: it is the one that
# answers "how long does that take" wherever it sits in the answer.
_TOTAL_TIME = re.compile(
    r"start to finish|from start to finish|in total|altogether|all in\b|in all\b|end to end",
    re.I)

_RECIPE_STEP = re.compile(
    r"\b(?:fry|fries|frying|fried|add|adds|adding|simmer|simmering|bake|baking|roast|"
    r"roasting|boil|boiling|stir|stirring|grill|griddle|wilt|wilted|toss|mash|whisk|"
    r"blend|braise|poach|steam|season|drain|serve)\b", re.I)


def _the_answer_names_a_food(said):
    """Whether the answer names a food the pantry and the staples table know.

    Whole words, folded: the same set the keeping entries are keyed by, so an answer about a dish
    passes and an answer about anything else does not.
    """
    return bool({_fold(word) for word in _WORD.findall(str(said or "").lower())} & _foods_said())


def keeping_followup(understood, memory):
    """The keeping answer for "how long does that keep" after a dish we just gave.

    A meal answer states how long the dish takes, and a keeping question leans on the answer just
    given ("ive got chicken and spinach in the fridge", "how long does that keep"), so the time in
    it was read out as the answer: twenty minutes is how long it takes to cook, not how long it
    keeps. The keeping fact is the same for any cooked dish, so it is what this returns. A line
    that names a food of its own keeps its own entry ("how long does cooked chicken keep").
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    clean = str(understood.get("clean") or "").lower()
    words = set(_WORD.findall(clean))
    if not words & _KEEP_WORDS or words & _COOKING_SENSE:
        return None
    if not _KEEP_TIME_ASK.search(clean):
        # It has to ask how long: "my knee keeps clicking, is that normal" and "can i freeze it"
        # carry a keeping word and point back at the answer, and neither asks this.
        return None
    if not words & _BACK_REFERENCE:
        return None  # a keeping question about a food of its own is the entries' to answer
    for turn in ((memory.get("turns") or [])[-3:] if isinstance(memory.get("turns"), list) else []):
        said = str(turn.get("user") or "").lower() if isinstance(turn, dict) else ""
        if any(name in said for name in _BAKED_GOODS):
            return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    if turns[-1].get("module") != "answers":
        return None
    said = str(turns[-1].get("bot") or "")
    if set(_WORD.findall(said.lower())) & _KEEP_WORDS:
        # The answer just given already said how long it keeps, and trimming it here leaves the
        # conversation without the dish in mind: the next follow-up then gets the whole meal
        # answer again, word for word. So this one keeps its own answer.
        return None
    if not _TIMING.search(said) and not _RECIPE_STEP.search(said):
        return None  # nothing was cooked here to keep
    # A step word is not proof on its own that food was cooked: `add`, `serve`, `season` and
    # `drain` are ordinary English too, so an answer that says "several small things adding up"
    # matched `add` and the answer to "how long will that take to sort out" after it was the
    # cooked-food card. The dish it was about is a food, so the answer has to name one.
    if not _the_answer_names_a_food(said):
        return None
    return COOKED_KEEPING


def timing_followup(understood, memory):
    """The time our own last meal answer gave, when the line only asks how long it takes.

    "i have chickpeas and spinach, what can i make" gets a dish and its time; the next line,
    "how long does that take", is asking about the answer just given rather than about a food
    of its own. The time already in that answer is the reply. Passes on anything that names a
    food we have not just talked about, so "how long do i boil an egg" keeps its own entry.
    """
    if not isinstance(understood, dict) or not isinstance(memory, dict):
        return None
    asks = set(understood.get("asks") or ())
    words = set(understood.get("words") or ())
    clean = str(understood.get("clean") or "").lower()
    if not (asks & {"how_long"} or "how long" in clean or "how many minutes" in clean):
        return None
    if not words & _BACK_REFERENCE:
        # A time question with no food of its own in it leans on the answer just given, whether
        # it says so or not: after the chicken traybake, "how long in the oven" was answered by
        # the whole-bird rule ("20 minutes per 500g plus 20 ... 1 hour 40 for a 2kg bird"), and
        # the dish on the screen said 35 to 40 minutes. A word that names a food still sends the
        # line to its own entry, so "how long do i boil an egg" keeps its answer.
        if {_fold(word) for word in words} & set(_INGREDIENT_WORDS):
            return None
        if {_fold(word) for word in words} & _KEEP_WORDS:
            # The lean is for a cooking time, and "how long" also asks how long a thing keeps.
            # "how long does soup keep" after a chicken traybake was answered with raw chicken's
            # one to two days, because soup names no ingredient and the line pointed at nothing.
            # A keeping question that names its own subject is the store's, so the lean stands
            # down; "how long does that keep" points back and never reaches here.
            return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    last = turns[-1]
    said = str(last.get("bot") or "").strip()
    if last.get("module") != "answers":
        # A reply that says the dish answer again is that answer still on the screen, whichever
        # module fronted it: "no cheese though" after a frittata is answered with "Skip the
        # cheese: A frittata: ...", and "and how long does that take" next is the dish's time,
        # not a new question. Read from the store's own record of the answer just given.
        kept = memory.get("last_answer")
        kept_text = str((kept or {}).get("reply") or "").strip() if isinstance(kept, dict) else ""
        head = kept_text[:40].lower()
        if not kept_text or len(kept_text) < 40 or head not in said.lower():
            return None
        said = kept_text
    # Only a meal idea from this table is a whole dish with a time of its own. An entry's answer
    # is a fact with times inside it ("9 to 10 minutes", "a minute less"), and "how long does
    # that take" is better left to the entries than answered with one of those.
    if not _is_meal_answer(said):
        return None
    # The time that answers this is the one stated for the whole dish, and a good answer says it
    # once: "About 40 minutes start to finish" as the first sentence, or an opening method whose
    # one time is the cook's ("...and simmer covered for 20 minutes"). The closing sentence is the
    # last place to look, not the first - it is often a step's own time, so "One-pan chicken and
    # rice ... simmer covered for 20 minutes. Let it stand 5 minutes" was read as five minutes.
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", said) if part.strip()]
    total = [part for part in sentences if _TOTAL_TIME.search(part)]
    when = None
    for part in total + [part for part in sentences if part not in total]:
        times = {" ".join(found.group(0).lower().split())
                 for found in _TIMING.finditer(part)}
        if len(times) == 1:
            when = times.pop()
            break
    if when is None:
        return None
    said_words = set(_fold(word) for word in _WORD.findall(said.lower()))
    named = [word for word in understood.get("words") or ()
             if _fold(word) in _INGREDIENT_WORDS and _fold(word) not in said_words]
    if named:
        # A food of its own that our answer never mentioned: this is a new question, not a
        # question about the dish we just gave.
        return None
    return "About %s for that one, start to finish." % when


# --- the dishes people actually cook ------------------------------------------
# One table of the meals an ordinary kitchen makes, keyed by the dish rather than by the
# wording: "how do i make chilli", "chilli con carne recipe", "what goes in a bolognese" and
# "how long do i simmer a ragu" are one question. The first sentence is the method with its
# quantities and times, and the second is the thing that most often goes wrong.

_RECIPE_ASK = ("make", "making", "made", "cook", "cooking", "recipe", "recipes", "how", "what goes",
               "ingredients", "from scratch", "method", "proper", "best way", "how long", "simmer",
               "bake", "time", "worth", "should i",
               # "i fancy a curry" is a dish asked for without a question word in it: the want
               # itself is the ask, and it names the dish the method is for. These words are
               # shared with fifty recipe rows, so a word that was rare before must not be here:
               # "fancy" was in one entry's key only, and the meal ideas answer the follow-up
               # "nothing too fancy" by naming that phrase in their own key instead.
               # "love" is not here: "i love curry" is a taste the store says back, and the
               # taste module owns that line now (bot/knowledge/taste.py). Saying what you want
               # to eat is an ask; saying what you like is a fact about you.
               "fancy", "craving", "crave", "mood", "want", "wanting",
               # "i feel like a curry" wants the dish as plainly as "i fancy a curry" does, and
               # the feeling word was the one way of saying it the table did not hold: the line
               # was read as a feeling and answered "Thanks for telling me". A dish still has to
               # be named, so "i feel like a walk" reaches no row.
               "feel like", "feels like", "feeling like", "felt like",
               # the everyday way of asking for one: "whats a good dry rub for chicken" was the
               # "serve it with something wet" fault answer, because no ask word in it was this
               # table's. A dish name is still needed, so "whats a good film" reaches nothing here.
               "whats a good", "what's a good", "whats the best", "what's the best",
               "what is a good", "what is the best",
               # "sandwich filling ideas" asks for one as plainly as "whats a good sandwich
               # filling" does. Only the filling words: a bare "ideas" here took "curry ideas"
               # off the three curries to try and onto the method for one, which is not what
               # ideas are for. The row still needs a dish named, so "gift ideas" reaches nothing.
               "filling ideas", "fillings", "fillings for")

# The dish's own name is an ask for its method. "lasagne", "egg fried rice", "toad in the
# hole": people name a dish and press send, and that was the plainest way of asking for one and
# the only way that reached nothing at all - every row wanted a make-or-cook word as well as the
# dish, so the line fell past the whole table and the bot said "I'm listening". So each row takes
# its own names as ask words too (the names are its key already, so no word becomes common and no
# other row loses a point), and the wrapper below is what keeps every other line of that kind
# where it was.
_RECIPE_ASK_WORDS = re.compile(
    r"(?<![a-z])(?:" + "|".join(re.escape(one) for one in
                                sorted(_RECIPE_ASK, key=len, reverse=True)) + r")(?![a-z])")

# The words that can sit around a dish name and add nothing to it: a dish typed with one of these
# is still the dish on its own, and anything else in the line is a question about the dish rather
# than a request for the method ("lasagne for 8", "vegan lasagne", "lasagne in the air fryer").
_DISH_ON_ITS_OWN_FILLER = frozenset((
    "a", "an", "the", "some", "my", "our", "me", "please", "pls", "plz", "ta", "thanks",
    "thank", "you", "hi", "hello", "hey", "ok", "okay", "oh", "ah", "so", "well", "just",
    "quick", "easy", "simple", "nice", "good", "proper", "some", "and", "then", "for",
    "tonight", "today", "now", "it", "that", "one", "again", "recipe", "recipes"))


def _this_line_only(understood):
    """This turn's line and not the turns before it, lower-cased, for the dish-on-its-own test.

    `_said_so_far` puts the earlier turns in front for the exclusions, and "im vegetarian" then
    "lasagne" would read as a line with two subjects in it.
    """
    words = understood.get("words")
    if isinstance(words, list) and words:
        return " ".join(str(word).lower() for word in words)
    return str(understood.get("clean") or "").lower()


def _names_nothing_but_the_dish(text, names):
    """True when the line is one of these dish names and nothing else that says anything."""
    left = " " + " ".join(str(text or "").lower().split()) + " "
    named = False
    for name in sorted(names, key=len, reverse=True):
        needle = " " + str(name).lower() + " "
        if needle in left:
            left = left.replace(needle, " ")
            named = True
    return named and all(word in _DISH_ON_ITS_OWN_FILLER for word in left.split())


# A dish can be asked for by wanting it rather than by asking about it, and the reading calls
# that a statement of news ("i fancy a curry" is not a question). The want is the ask.
_WANT_PHRASES = re.compile(r"\b(?:fancy|fancied|craving|crave|in the mood for|really want|"
                           r"i want|would love|i'd love|i would love|feel like|feels like|"
                           r"feeling like)\b")

# The want has to be for a thing and not for something to happen. "i want to cancel my gym
# membership" carries the want too, and once a dish has been named it reached that dish's method:
# the swap reading puts the last dish in the line, and the curry came back in answer to a
# question about a gym. A want followed by "to" or a pronoun is about an action, not a dish.
_WANT_ACTION = re.compile(r"\b(?:want|wants|wanting|fancy|fancied|craving|crave|love|loves|"
                          r"feel|feels|feeling)\s+(?:like\s+)?"
                          r"(?:to|it|that|this|you|me|him|her|them|us|if|when|how|why|what)\b")


# A want to cook something is a want for the dish: "i want to make a curry" is the curry's
# method, whatever the wording says the want is about.
_WANT_TO_COOK = re.compile(r"\b(?:want|wants|wanting|fancy|fancied|would love|i'd love|"
                           r"i would love)\s+to\s+(?:make|cook|bake|roast|do|try)\b")


# A want to learn to make something is a want for the method: "i want to learn to make bread"
# reached the wish reading instead, so this row stood down and the dish table answered it with
# beans on toast, because bread is a tag on that dish. "i want to learn how to make curry" was
# read as a revision question and got "test yourself instead of rereading". The learning verb
# sits between the want and the make, which is the one place `_WANT_TO_COOK` above does not look,
# so this one allows the verb in between ("learn to make", "learn how to make", "start making").
_WANT_TO_LEARN_COOK = re.compile(
    r"\b(?:want|wants|wanting|fancy|fancied|would love|i'd love|i would love|would like|"
    r"i'd like|thinking of|planning to|going to|gonna|hope to|hoping to)\b[^.!?]{0,24}?"
    r"\b(?:learn|learning|learnt|learned|start|starting|started|try|trying)\s+"
    r"(?:to\s+|how\s+to\s+)?(?:make|cook|bake|roast)\b")


def _wants_the_dish(text):
    """Whether the want in this line is for a dish ("i fancy a curry") rather than an action."""
    if _WANT_TO_COOK.search(text) or _WANT_TO_LEARN_COOK.search(text):
        return True
    return bool(_WANT_PHRASES.search(text)) and not _WANT_ACTION.search(text)

# The lines that name a dish but ask for something else: the swap for a food they have not got
# ("shortbread without butter"), a diet the method breaks ("dairy free brownies"), another way of
# cooking it ("in the air fryer"), or another day ("reheat chilli", "how do i store scones").
# One guard for the whole table beats 33 `avoid` lists, and each of those lines has its own
# answer on main.
#
# A table is not one of them. "for 8 people" was here, and the guard reads the whole said-so-far
# line, not just this line, so the table sat in the text for the rest of the chat: "can i make
# chilli con carne for 14 people" then "how long does it take" stood the chilli method down and
# the reply was the growing time for chillies, 16 to 20 weeks from seed, to someone cooking
# dinner tonight. The number a table needs is read by the rows that answer amounts ("150 g of
# mince and 75 g of dry rice each, 2.1 kg and 1 kg in all" for that line), and they read it off
# the line itself, so nothing here has to stand down for it.
_RECIPE_NOT_THIS = re.compile(
    # "without" is a swap when an ingredient follows it - "scones without eggs", "pastry without
    # butter" - and it is the same method when what follows is a piece of kit: "how do i make
    # pastry without a food processor" was answered with a search suggestion because this one
    # word stood the pastry method down. A determiner before the word is what tells them apart ("a
    # food processor", "an oven", "my mixer"); an ingredient is said bare or with a quantity
    # ("without eggs", "without any sugar"), so the lookahead spares yeast and the determiners.
    # ...except the heat: an oven or a hob is kit you cannot do without either, and telling
    # someone with no oven to bake at 180C is worse than the hedge it replaced ("how do i make
    # pastry without an oven"). A determiner only spares the swap when what follows it is not
    # the thing that cooks.
    r"\b(?:without(?!\s+(?:(?:any\s+)?yeast|(?:a|an|the|my)\s+"
    r"(?!(?:an?\s+)?(?:oven|grill|hob|stove|range|microwave|air ?fryer|cooker|barbecue|bbq)\b)))"
    r"|dairy[- ]free|gluten[- ]free|egg[- ]free|nut[- ]free|sugar[- ]free|vegan|"
    r"vegetarian|substitute|substitutes|substitution|instead of|swap|swapped|swapping|"
    r"replace|replacing|alternative|reheat|reheated|reheating|leftover|leftovers|store|storing|"
    r"stored|storage|freeze|freezes|freezing|air fryer|slow cooker|pressure cooker|microwave|"
    # a keeping question is about the shelf life, not the method: "how long will guacamole keep"
    # was getting "About 10 minutes start to finish" - the method's own clock, which reads like
    # the answer and is not one
    r"keep|keeps|keeping|kept|last|lasts|lasting|go off|goes off|gone off|safe to eat|edible|"
    r"still good|still ok|still okay|"
    r"how much|how many|"
    # a dish that has gone wrong wants the fix, and every one of those lines has its own
    # answer: "how do i thicken curry sauce" is soup-thick, not the curry method.
    r"thicken|thickening|thickens|runny|watery|lumpy|curdled|curdles|split|splits|"
    r"too salty|too spicy|too sweet|bland|burnt|burning)\b")


# A table of methods answers a line that asks for one ("how do i make scones", "give me a chilli
# recipe") or names the dish and what to do with it ("chilli con carne recipe"). It does not
# answer news ("i made a big chilli tonight and theres loads left"), a feeling ("i love lasagne")
# or a verdict on the last one ("my chilli was too spicy"): those lines ask for the leftovers,
# keeping or seasoning answer, and each of them already has one on main.
_RECIPE_ANSWERS = ("question", "request", "statement")


def _recipe_only_when_asked_for_this(reply, names=(), no_yeast_ok=False):
    """This method, unless the line is not asking for it, wants a swap, or another way.

    no_yeast_ok is for the soda loaf: every other loaf row is a yeast method, and a line that
    says it has no yeast in it cannot use one. names are the row's own dish names, read here to
    tell a dish typed on its own from a line that only names the dish on the way to something
    else, which is a question for another row.
    """
    total = re.split(r"(?<=[.!?])\s+", reply.strip())[0]

    def answer(memory, understood):
        text = _said_so_far(understood, memory)
        alone = _names_nothing_but_the_dish(_this_line_only(understood), names)
        if not alone and not _RECIPE_ASK_WORDS.search(text):
            # The row's ask list now holds the dish's own names, so a line that names the dish
            # comes this far whatever the rest of it says. Every one of those lines was read by
            # another row before this one could reach it, so the make-or-cook word is still what
            # this row needs - except when the line is the dish and nothing else.
            return None
        if _WANT_ACTION.search(text) and not _WANT_TO_COOK.search(text) \
                and not _WANT_TO_LEARN_COOK.search(text):
            # The want in the line is for something to happen, not for the dish: once the swap
            # reading put the last dish back in the line, "i want to cancel my gym membership"
            # reached the curry's method because "want" was the ask word it matched on.
            return None
        if understood.get("intent") not in _RECIPE_ANSWERS and not _wants_the_dish(text) \
                and not alone:
            # A dish on its own is a statement of news by the reading ("lasagne" announces
            # nothing), so it is let through on its shape rather than its kind of line.
            return None
        if not no_yeast_ok and any(one in text for one in _NO_YEAST):
            # the soda loaf: every other loaf row is a yeast method
            return None
        if _RECIPE_NOT_THIS.search(text):
            return None
        # "how long does coleslaw last" and "how long do scones keep" are shelf-life questions
        # about a dish, and the first sentence of a method is the wrong clock for them; the
        # keeping rows answer, or the bot says it does not know rather than how long to boil it.
        line = str(understood.get("clean") or "").lower()
        if _RECIPE_KEEPING.search(line) and not _RECIPE_COOKING.search(line):
            return None
        if understood.get("asks") == ["how_long"]:
            # "how long does it take", with no dish of its own in the line, wants the clock and
            # not the method: the first sentence is the whole dish, start to finish.
            return total
        return reply
    return answer


# "How long does coleslaw last" is a shelf-life question about a dish, and the first sentence of
# a method is the wrong clock for it. Only the words that mean keeping and nothing else are here:
# "green" and "soft" are keeping words too, and "how long does green curry take" is a method line.
_RECIPE_KEEPING = re.compile(
    r"\b(?:keep|keeps|keeping|shelf[ -]life|last|lasts|lasted|store|stores|storing|storage|"
    r"go off|goes off|gone off|past its date|past the date|out of date|next day|tomorrow|"
    r"once opened|once open|mouldy|mould|moldy|mold|use by)\b")
_RECIPE_COOKING = re.compile(
    r"\b(?:cook|cooks|cooking|cooked|boil|boils|boiling|bake|bakes|baking|roast|roasting|"
    r"fry|frying|grill|grilling|steam|steaming|make|makes|making|recipe|prepare|prep|"
    r"assemble|heat|oven|simmer|reheat)\b")


# A recipe is how to make the dish, and a fault in it is a different question with a different
# first sentence: "how do i thicken curry sauce" got the forty-minute curry method, which says
# nothing about the pan in front of the person. So every recipe row stands aside for the
# thickness words, and the fault entries (soup-thick, fix-watery, the curdling ones) take them.
# A method is the pan and a sowing is the garden: "when should i sow salad leaves" is a row in
# the garden's table, and the salad recipe answered it because "should i" is an ask and a salad
# leaf is a dish. Only the words that mean a seed in the ground are here - "plant" and "grow"
# are too common in a kitchen ("plant based", "grow your own with this") to carry the rule.
_RECIPE_GROWING_WORDS = (
    "sow", "sows", "sowing", "sowed", "germinate", "germinating", "seedling", "seedlings",
    "allotment", "veg patch", "vegetable patch", "raised bed", "raised beds",
    "harvest", "harvesting", "crop", "crops", "plant out", "planting out", "thin out",
    "thin the seedlings")

# A dish someone says they are cooking now is an announcement, and the plan row answers it with
# the time, the heat and the one thing to get right ("Spag bol: an hour start to finish, and the
# sauce is worth the last half of it at a bare simmer"). Reading the whole method out to a line
# that only said what it was making is the recipe card for a question nobody asked - "im making a
# spag bol tonight" and "im gonna make a spag bol tnite any tips" both read like a recipe dump.
# So the recipe rows stand down for the first person doing it, which is the shape the plan row
# keys on. A question is untouched: "how do i make spag bol" and "spaghetti bolognese recipe"
# name no first person, and "we are having chilli tonight" is a table telling you the plan, which
# the recipe answers.
ANNOUNCED_DISH = (
    "im making", "i'm making", "im doing", "i'm doing", "im cooking", "i'm cooking",
    "im gonna make", "i'm gonna make", "im going to make", "i'm going to make",
    "im gonna do", "i'm gonna do", "im going to do", "i'm going to do",
    # the matcher reads the words as they were said, with the contraction written out, so each
    # shape is here twice: "im doing a spag bol tonight" is read as "i am doing"...
    "i am making", "i am doing", "i am cooking", "i am gonna make", "i am going to make",
    "i am gonna do", "i am going to do")

# A dish already made is the pot in the fridge, not the method. "stew made yesterday can i have
# it" was answered with "About 2 to 3 hours start to finish. Brown 1kg of chuck steak..." and the
# person had said when they cooked it: the day a dish was made, and the words for what is left of
# it, are the keeping row's question, which answers them with a verdict on that day count. A
# recipe ask never carries one of these - "how do i make a stew", "beef stew recipe" - so the
# recipe rows stand down for a line that points at the pot rather than at the dish.
_A_POT_ALREADY_MADE = re.compile(
    r"\b(?:made|cooked|done|ate|had)\b[^.?!]{0,24}\b(?:yesterday|last night|this morning|"
    r"the night before|the day before|days? ago|\d+ days?)\b"
    r"|\b(?:left ?overs?|left over)\b"
    r"|\b(?:in|been in) the (?:fridge|freezer|pot|tub)\b"
    r"|\bmade (?:on|for) (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)


def _a_made_pot_is_not_its_recipe(understood):
    """True when the recipe row may answer: the line asks for the method of a dish, not the pot."""
    if not isinstance(understood, dict):
        return True
    text = understood.get("norm_text") or understood.get("clean") or ""
    return not _A_POT_ALREADY_MADE.search(str(text))


_RECIPE_FAULT_WORDS = (
    "thicker", "thicken", "thickens", "thickening",
    "thinner", "too thick", "too thin", "watery", "runny", "stodgy", "lumpy",
    "curdled", "curdles", "split", "splits", "too salty", "too spicy", "too sweet",
    "bland", "burnt", "burning")

for _names, _key, _reply, _avoid in RECIPES:
    def _alone(line, _only=tuple(_names)):
        # a dish typed with nothing done to it: see _names_nothing_but_the_dish
        return _names_nothing_but_the_dish(line, _only)

    ENTRIES.append(entry("recipe-" + _key[0].replace(" ", "-"),
                         (_names, _RECIPE_ASK),
                         _recipe_only_when_asked_for_this(
                             _reply, _names, no_yeast_ok=_key[0] == "soda bread"),
                         # the dish's own name is the ask for its method: see _RECIPE_ASK_WORDS
                         ask=tuple(_RECIPE_ASK) + tuple(_names),
                         # the name is one signal and the shape is the second, which is what the
                         # two-position rule wants: a one-word dish ("lasagne") has no other
                         # word to be its own second position.
                         shape=(_alone,),
                         # "bread with no yeast" ties with the prove instructions on words, so
                         # the soda loaf needs the point on its side to take the line. The
                         # sandwich needs the same: the satiety row keys "filling" and carries a
                         # bias of 2, so "whats a good sandwich filling" was answered with pasta
                         # and a tin of tomatoes, and the sandwich row tied it on words.
                         bias=(2 if _key[0] in ("rice and peas", "soda bread")
                               else 1 if _key[0] == "sandwich" else 0),
                         # A recipe is the dish as it is, and a card that says "150g of
                         # sugar" is the wrong answer to "how do i make sugar free banana
                         # bread": the line names the dish with something left out of it, which
                         # the swap and cut-down rows answer. The same words stand the rows
                         # written in cooking_entries.py down.
                         avoid=tuple(_avoid) + _RECIPE_FAULT_WORDS + _RECIPE_GROWING_WORDS
                         + _NO_SUGAR + ANNOUNCED_DISH,
                         # a dish already made is the keeping row's question, not the method
                         guard=_a_made_pot_is_not_its_recipe))
# A dish named in a line is the dish, not the foods it is made of. "spaghetti bolognese recipe"
# was answered with aglio e olio and "should i do a spag bol tonight" with mac and cheese, while
# "how do i make spag bol" got a shrug: the ingredient table reads "spaghetti" as a food to cook
# with and hands back whichever pasta dish it holds, and the dish the person named is not an
# ingredient at all. The recipe table is the list of dishes this kitchen knows by name, so a line
# that names one has a subject of its own, and the tables that answer foods rather than dishes
# (the pantry's ideas, a free evening, a day out) stand down for it.
#
# A food that is also a dish - bread, prawns, sprouts - stays the pantry's: "what can i make with
# prawns" is a use-up question and the ingredient table is the one that answers it.
_USE_UP_WORDS = ("leftover", "leftovers", "left over", "left from", "use up", "using up",
                 "used up", "spare", "stale", "already made", "goes off", "go off",
                 "out of date")
_PANTRY_FOODS = frozenset(
    [_fold(alias) for aliases, _reply in PANTRY.values() for alias in aliases]
    + [_fold(name) for name in PANTRY])


def names_a_dish(understood):
    """The dish a line names from the recipe table, or None when it names no dish.

    The whole line is read, not only the words above MIN_SCORE, because a dish is a subject: the
    alias has to arrive whole ("spag bol" is one dish, not the word "bol"), and a single-word
    alias counts when the line says it and the kitchen holds a recipe for it.
    """
    if not isinstance(understood, dict):
        return None
    words = understood.get("words")
    if not isinstance(words, (list, tuple)):
        words = str(understood.get("clean") or "").split()
    folded = [_fold(word) for word in words if str(word).strip()]
    for aliases, _keys, _body, _avoid in RECIPES:
        for alias in aliases:
            parts = [_fold(part) for part in alias.split()]
            if not parts or " ".join(parts) in _PANTRY_FOODS:
                continue
            if len(parts) == 1:
                hit = parts[0] in folded
            else:
                hit = any(folded[at:at + len(parts)] == parts
                          for at in range(len(folded) - len(parts) + 1))
            if hit:
                return alias
    return None


# --- basics a kitchen asks for by name ---------------------------------------
# Three questions people put in the plainest words: a pastry case baked with nothing in it, a
# pan that has lost its coating, and the fastest way to get a clove out of its skin. Each is a
# method, so each answers the whole line rather than a fault ("why did my pastry shrink" is the
# fault table's, and these stand aside for it).
ENTRIES.append(entry(
    "blind-bake",
    # Every word here is one that other entries already use: the matcher weighs a key word by
    # how rare it is, so a word borrowed from a neighbour's key would quietly cost that entry a
    # point ("skin" belongs to the crispy chicken skin, "baked" to the jacket potato).
    (("pastry", "flan", "pastry case", "pastry base", "pie base", "tart base",
      "pie case", "tart case", "flan case", "blind bake", "blind baking",
      # "should i blind bake a quiche" is this job asked about the dish. It used to be avoided
      # here on the grounds that a quiche recipe answers it better, but the recipe entry needs a
      # make-or-cook word, so the line was a shrug.
      "quiche", "quiches"),
     ("blind", "blind bake", "blind baking", "bake", "baking", "line", "lined", "weights",
      "baking beans", "dry rice", "empty case", "before the filling",
      # "how long do i blind bake pastry" is the clock on this job, not a curtain to measure
      "how long", "how many minutes")),
    ("Line the tin with the pastry, prick the base all over with a fork, then cover it with a "
     "sheet of crumpled parchment and fill that with baking beans or dry rice. Bake at 200C "
     "(180C fan) for 15 minutes, lift the paper and beans out, and give it another 5 minutes to "
     "dry the base before the filling goes in. Blind just means baked empty - the weights stop "
     "the base rising and the sides slumping."),
    # "how long do i blind bake pastry" also fits the curtain-measuring entry (a blind is a
    # curtain, and a time question is a length to it), so this answer carries one point more
    bias=1,
    # a fault on a pastry case is the fault table's answer ("why did my pastry shrink"),
    # and a recipe for pastry itself is the shortcrust question
    avoid=("shrank", "shrink", "shrunk", "soggy", "sunk", "sank", "raw", "burnt", "burned",
           "cracked", "cracking", "crumbly", "falls apart", "how do i make pastry",
           "pastry recipe", "shortcrust", "rough puff", "puff pastry", "choux", "filo",
           "filling", "freeze", "frozen", "keep", "leftover",
           # "how do i make a quiche" is the recipe, which is its own entry: this one keys
           # "quiche" too, so it must not carry a make-or-cook word on the other side
           "make a quiche", "cook a quiche", "quiche recipe", "quiche recipe")))

ENTRIES.append(entry(
    "season-pan",
    (("pan", "pans", "wok", "skillet"),
     ("season", "seasoning", "seasoned", "reseason", "re-season", "cure", "curing",
      "sticking", "sticks", "ruined", "unusable", "lost its coating")),
    ("A pan that sticks has usually lost its thin layer of baked-on oil: scrub it, dry it on the "
     "hob, rub a film of neutral oil over the inside and heat it until it just smokes, then wipe "
     "the surplus off with kitchen paper. Twice more and it is slippery again. That works on "
     "stainless steel, carbon steel and cast iron. A non-stick pan is the exception - once the "
     "coating is scratched through, nothing brings it back, so replace it."),
    ask=("how", "what", "should", "do i", "can", "when", "why", "my"),
    # the cast iron pan and its washing, rust and seasoning are main's own entry, so this one
    # answers the plain pan; seasoning food in a pan is the recipe's business
    avoid=("cast iron", "cast-iron", "carbon steel", "rust", "rusty", "rusts", "dishwasher",
           "chicken", "steak", "salmon", "fish", "meat", "veg", "vegetables", "potatoes",
           "rice", "pasta", "soup", "stew", "curry", "to taste", "salt and pepper",
           "smoking", "smoke", "fire", "alarm", "burnt", "burning")))


# A line that points back at food instead of naming it ("what can i make with them", "what
# should i do with it"). The food is the one a turn or two earlier named, so the pantry answers
# for that food, and it does not serve the same dish it just served.
POINT_BACK = ("with them", "with it", "with those", "with these", "with that",
              "make with them", "make with it", "make with those", "make with these",
              "do with them", "do with it", "do with those", "do with that",
              "use it up", "use them up", "use those up", "use these up", "use that up",
              "use up the rest", "using it up", "using them up", "using those up",
              "using these up", "using that up", "using up the rest",
              "out of them", "out of it", "what about them",
              "what about it", "else can i do with", "else can i make with",
              "else could i do with", "else to do with", "else can i use",
              # A bare ask for ideas, after a turn that named food, is the same follow-up: "i
              # have some kale" then "any ideas" was answered "tell me what you've got so far".
              "any ideas", "any idea", "any other ideas", "any suggestions", "suggestions",
              "what else", "anything else", "something else", "what do you suggest")
# ... but only the bare ask points back. A line that says what the ideas are *for* names its own
# subject, and the food on the table is not it: "any ideas for using up leftover chicken" then
# "any ideas for a cheap day out on saturday" was answered with the chicken again, behind "The one
# I'd go back to:". The phrases above that point with a word ("with them", "use it up") still point
# back whatever follows them, because the pointing word is the object.
POINT_BACK_BARE = frozenset(("any ideas", "any idea", "any other ideas", "any suggestions",
                             "suggestions", "what else", "anything else", "something else",
                             "what do you suggest"))
# A pointing word after the preposition ("any ideas on this", "something else for it") is the
# food again, not a subject of its own. When the object of that preposition is the food in hand or
# the meal it is for - "any ideas for the rest" and "anything else for dinner" after a fridge
# full of chicken - the line is that food's follow-up again, not a new subject, so the fence reads
# the whole object rather than the first letter after the preposition.
THE_FOOD_OR_THE_MEAL = frozenset(("it them those these this rest leftover leftovers left other "
                                 "using use dinner tea supper lunch breakfast meal meals "
                                 "pudding dessert snack").split())
POINT_BACK_OBJECT = re.compile(r"\b(?:for|about|on)\s+(.+)$", re.I)


def _ideas_are_for_something_else(said):
    """Whether a bare ask for ideas or suggestions names a subject of its own."""
    named = POINT_BACK_OBJECT.search(said)
    if named is None:
        return False
    return not (set(re.findall(r"[a-z']+", named.group(1).lower())) & THE_FOOD_OR_THE_MEAL)
# A follow-up that asks what goes *beside* the food is not a question about the food itself:
# pointing it back at the food answered it with the cooking of that food again ("what can i
# serve with it" after chicken got roast chicken thighs a second time, thighs for the breasts
# the person had said).
PAIRING_WORDS = ("goes with", "go with", "to go with", "serve with", "served with",
                 "serve on the side", "on the side", "side dish", "side dishes",
                 "what can i serve", "what should i serve", "what to serve",
                 "pair with", "pair it with", "pairing", "accompany")

# A line that asks for a second idea has already had the first one, so it is only answered when
# the table has a *different* dish for the food: the same one again behind "The one I'd go back
# to" reads canned the second time (cream-orange, leeks over three turns).
SECOND_IDEA = ("what else", "anything else", "something else", "another idea",
               "another one", "any other", "other ideas", "what other")


# The food a turn named may be the wrong subject to point back at: something that is going off,
# out of date, or that made somebody ill is a safety question, not a proposal for dinner.
POINT_BACK_STOP = ("going off", "gone off", "went off", "off the", "use by", "best before",
                   "out of date", "still ok", "ok to eat", "okay to eat", "safe to eat",
                   "mouldy", "moldy", "mould", "mold", "smells", "smelly", "slimy",
                   "defrost", "raw", "undercooked", "allergic", "food poisoning", "vomit",
                   "diarrhoea", "threw up", "sick after", "my cat", "my dog", "the cat",
                   "the dog")


def recent_replies(memory, count=2):
    """The last few replies the bot gave, newest last, so a follow-up is not a repeat."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ()
    said = [str(turn.get("bot") or "") for turn in turns[-count:] if isinstance(turn, dict)]
    return tuple(said[-count:])


def _words_of(text):
    return re.findall(r"[a-z0-9']+", str(text or "").lower())


def _food_before(memory):
    """The words of the nearest earlier turn that named food, or none."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return []
    for turn in reversed(turns[-3:]):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("user") or "")
        if any(phrase in said.lower() for phrase in POINT_BACK_STOP):
            return []
        words = _words_of(said)
        if ingredients({"words": words}):
            return words
    return []


def pointed(memory, understood):
    """The reading a line that points back at earlier food means, or None.

    "what can i make with them" names no food of its own, and a reply built from the words of
    that line alone has none to work with, so it falls back to a list of quick dinners. The food
    is the one the last turn or two named, so the line is read as if it had been said again:
    the earlier food in front of these words. None when the line names its own food, points at
    nothing in the kitchen, or points back at something that is off or unsafe.
    """
    if not isinstance(understood, dict):
        return None
    if ingredients(understood):
        return None
    clean = str(understood.get("clean") or "").lower()
    if not any(phrase in clean for phrase in POINT_BACK):
        return None
    if (not any(phrase in clean for phrase in POINT_BACK if phrase not in POINT_BACK_BARE)
            and _ideas_are_for_something_else(clean)):
        # The line is only a bare ask for ideas, and it says what they are for: that is its own
        # subject, not the food of the turn before.
        return None
    if any(phrase in clean for phrase in PAIRING_WORDS):
        # "what can i serve with it": the food is still the subject, but the question is the
        # thing beside it, and the method for the food alone is not that answer.
        return None
    earlier = _food_before(memory)
    if not earlier:
        return None
    reading = dict(understood)
    reading["words"] = earlier + _words_of(" ".join(understood.get("words") or ()))
    reading["clean"] = " ".join(earlier) + " " + clean
    if any(phrase in clean for phrase in SECOND_IDEA):
        # "and something else", "what else": only a dish that has not been served already.
        reading["new_dish_only"] = True
    return reading
# --- feeding yourself through the week ------------------------------------
# Not a recipe and not a keeping question: how to get dinners out of a fridge on a Tuesday. The
# questions are "how do i meal prep", "what can i batch cook", "how do i stop wasting food", and
# they are answered as a plan rather than as a dish, so every entry here has a key of its own and
# stands down for a line that names a food (the pantry table and the dish entries know that food).
_PLANNED_FOOD = ("chicken", "beef", "pork", "lamb", "mince", "fish", "salmon", "pasta", "rice",
                 "curry", "chilli", "soup", "stew", "bread", "cake", "potato", "potatoes",
                 "courgette", "spinach", "chickpeas", "lentils", "eggs", "cheese", "milk")

ENTRIES.append(entry(
    "meal-prep",
    (("meal prep", "meal-prep", "meals prepped", "prep meals", "prep for the week",
      "prep on sunday", "batch cook", "batch cooking", "batch-cook", "cook ahead",
      "cook once eat twice", "cook once and eat twice"),
     # a key holds two parts: one phrase is one signal (weight 3, below the minimum of 4), so
     # the second part is how the question is asked, not what it is about
     ("how", "what", "should", "can", "start", "begin", "tip", "tips", "help", "want",
      "worth", "week", "weekly", "sunday", "idea", "ideas", "best", "way")),
    ("Cook two big things on one day and portion them: a pot of chilli or bolognese and a tray of "
     "roast veg, then cook rice or pasta fresh on the day. Cool it within two hours, box it in the "
     "portions you will actually eat, and keep three days in the fridge or freeze the rest. Chop "
     "an onion, wash a bag of salad and grate some cheese while you are there and a weekday dinner "
     "takes ten minutes. Cooked rice is the one to freeze on the day, not the next."),
    avoid=("safe", "food safety", "how long", "defrost", "gone off")))

ENTRIES.append(entry(
    "plan-the-week",
    # The week's dinners and the shop that goes with them: "how do i make a shopping list for
    # the week", "what should i cook this week", "meals for the week ahead". A line that asks
    # for a meal plan in so many words is the meal-ideas entry's own line (it answers it with
    # the plan), so this one stands down for it rather than saying it a second way.
    (("shopping list", "food shop", "weekly shop", "the week's shop", "weeks shop",
      "meals for the week", "dinners for the week", "week of dinners", "week of meals",
      "weeknight dinners", "what to cook this week", "cook this week", "food for the week"),
     ("how", "what", "should", "help", "start", "make", "write", "do", "tip", "tips", "idea",
      "ideas", "best", "way")),
    ("Write down five dinners, not seven: three you can cook without thinking, one new one and one "
     "night for leftovers or something from the freezer. Then shop once from that list, plus "
     "breakfast and lunch things, and buy the fresh veg you will use in the first three days. A "
     "plan you can move a night around is the one that survives; a strict seven-day plan usually "
     "gets abandoned by Wednesday."),
    # a line asking which shop is cheapest asks about shops, not about dinners: "whats the
    # cheapest supermarket for a weekly shop" was this plan because "weekly shop" is a key here
    avoid=("diet", "lose weight", "calories", "calorie", "baby", "toddler", "school lunch",
           "meal plan", "meal planning", "weekly meal plan", "airport", "flight",
           "supermarket", "supermarkets", "cheapest", "cheaper", "which shop", "price",
           "prices", "aldi", "lidl", "tesco", "asda", "sainsburys", "sainsbury's", "morrisons",
           "waitrose", "ocado", "iceland", "co-op", "co op"),
    bias=1))

ENTRIES.append(entry(
    "food-waste",
    # The complaint is the same when there is a "so much" in it: "i waste so much food every
    # week" said the amount and the frequency and neither phrase, so the row could not see it and
    # the kitchen bin answered instead ("Most of it is air and packaging: flatten cartons...").
    # The object is food in every phrase below, so the second half can carry the plain verbs.
    (("stop wasting food", "wasting food", "waste food", "food waste", "throw away food",
      "throwing food away", "food going off", "use up food", "reduce waste",
      "waste so much food", "wasting so much food", "waste food every week",
      "so much food goes off", "food goes off before", "throw so much food away",
      "throwing so much food away", "food in the bin", "ends up in the bin"),
     ("how", "what", "should", "can", "stop", "reduce", "avoid", "tips", "tip", "help",
      "way", "ways", "best", "less", "not", "waste", "wasting", "wasted", "throw", "throwing",
      "away", "week", "month", "much")),
    ("Look in the fridge before you go to the shop: see what is left, then plan the next two "
     "dinners around it. Keep the oldest veg at the front of the drawer, freeze bread, milk and "
     "any meat you will not use in two days on the day you buy it, and treat the freezer as a "
     "pause button rather than a cupboard. A weekly \"whatever is left\" soup or frittata uses up "
     "the odds and ends, and a written list stops you buying a third bag of carrots."),
    avoid=("bin", "council", "collection", "compost", "recycling", "smell", "smells")))

# --- halving and doubling a recipe -------------------------------------
# The answer opens with the operation the line asks about: telling someone who asked how to
# double a recipe to "halve every ingredient" answers a question they did not ask.
SCALE_DOWN = (
    "Halve every ingredient and leave the oven temperature alone: the tin goes one size down if "
    "the batter looks thin in it, and start checking five minutes early. Cooking time does not "
    "halve - a smaller cake or loaf takes about two thirds as long - so test it with a skewer "
    "sooner than you think. Halve the raising agent exactly, and if the sum gives you half an "
    "egg, beat one and use half of it.")
SCALE_UP = (
    "Double every ingredient and use a bigger tin rather than a deeper one, so the middle cooks "
    "at the same speed. It takes longer than twice the time is worth assuming: start checking at "
    "the original time and give it another ten or fifteen minutes if the skewer comes out wet. "
    "Salt, spice and raising agent go up by less than double, to taste, and a big batch is better "
    "split between two tins than crammed into one.")
SCALE_UP_WORDS = ("double", "doubling", "doubled", "times two", "scale up", "for 20",
                  "for twenty", "for 30", "for a crowd", "for a big group", "bigger batch")


def _scaling_reply(memory, reading):
    """Halving or doubling, whichever the line asked for."""
    line = str((reading or {}).get("text") or (reading or {}).get("norm") or "").lower()
    words = set(re.findall(r"[a-z']+", line))
    if any(word in words or ((" " in word) and word in line) for word in SCALE_UP_WORDS):
        return SCALE_UP
    # "how do i scale a recipe up" puts the word between: the phrase forms miss it
    if "scale" in words and "up" in words:
        return SCALE_UP
    return SCALE_DOWN


ENTRIES.append(entry(
    "halve-a-recipe",
    # "how do i halve a recipe", "how do i double a recipe", "can i cut a recipe in half" and
    # "how do i scale a recipe down" were a search hedge each, and "how do i cut a recipe in
    # half" reached the half-marathon card because "half" is a race distance as well. The
    # scaling word is the subject, so it does the work, and the second half says what is being
    # scaled.
    (("halve", "halving", "halved", "half the recipe", "cut the recipe in half",
      "cut a recipe in half", "cut this recipe in half", "make half", "half a batch",
      "double", "doubling", "doubled", "double the recipe", "double up", "scale", "scaling",
      "scale down", "scale up", "times two", "times three", "third of the recipe",
      "scale a recipe", "scale up a recipe", "scale down a recipe", "scale the recipe",
      "double a recipe", "halve a recipe", "double the recipe", "halve the recipe",
      "two thirds of the recipe"),
     ("recipe", "recipes", "batch", "ingredients", "quantities", "amounts", "portions",
      "portion", "loaf", "cake", "mixture", "sauce", "soup", "stew", "casserole",
      "bolognese", "traybake", "biscuits", "cookies", "curry", "chilli", "pie", "roast",
      # "can i halve a recipe for two" was the dinner-ideas card and "how do i scale up a
      # recipe for 20 people" was a business one, because "scale up" is also how a company
      # grows: the number of people and the cooking time are what a scaling question says.
      "for two", "for four", "for six", "for eight", "for twelve", "for 20", "for 20 people",
      "for twenty", "for 30", "for a crowd", "for a big group",
      "cooking time", "baking time", "bake time", "oven time")),
    _scaling_reply,
    bias=1,
    # Doubling and halving is a kitchen question: a line about a race, a bill, a dose or a
    # portion of chips is not asking how to scale a recipe.
    avoid=("marathon", "half marathon", "race", "half price", "bill", "bills", "dose",
           "dosage", "paracetamol", "ibuprofen", "tablet", "tablets", "chips", "half a chicken",
           "half a pizza", "wine", "beer", "rent", "mortgage", "salary", "wage")))
ENTRIES.append(entry(
    "cook-for-one",
    # The one-person words are the evidence, not the subject: "on my own" is also how people
    # describe saving for a house or paying off a debt without help, and with "how" in the other
    # half this row took every one of those money lines.
    (("cook", "cooking", "cook for", "meal", "meals", "dinner", "dinners", "recipe", "recipes",
      "food", "eat", "eating"),
     ("for one", "for one person", "for myself", "on my own", "just me", "only me",
      "just for me", "single", "alone")),
    ("Cook two portions and let the second one be tomorrow's lunch or dinner: it is barely more "
     "work and it is the whole trick. Buy the smaller packs where they exist, freeze half a loaf "
     "and half a pack of mince on the day, and keep eggs, tinned tomatoes, pasta, rice and frozen "
     "veg in as the base of a ten-minute dinner. A frying pan and one small pot will do most of "
     "it."),
    # "easy meal ideas for cooking for one" is about cooking for one, not about one dish
    bias=1,
    # "cook" plus "for one" was reaching a dish the line named: "how do i cook a steak for one"
    # was being told to cook two portions. A person who names the dish wants that dish, so the
    # row answers the habit - ideas, worth it, batch, portions, cooking for one - and leaves the
    # method questions to the dish.
    ask=("ideas", "worth", "bother", "should", "plan", "planning", "batch", "portions",
         "portion", "leftovers", "what can i", "what should i", "meal ideas", "meals for",
         "dinner ideas", "recipes for", "cooking for one", "cook for one", "for myself",
         "on my own", "just me", "only me", "just for me", "cook for", "cooking for",
         "eat for", "what to cook", "ideas for"),
    # "on my own" and "just me" are how people describe both halves of a life: a meal for one,
    # moving a wardrobe upstairs without help, and raising two kids. A line that names a thing you
    # carry, fit or clean is not a meal question, and neither is one about the children or the
    # money, so those words take it out of the kitchen.
    avoid=("lonely", "loneliness", "widow", "grief", "died", "bereave",
           "upstairs", "downstairs", "stair", "stairs", "stairwell", "landing", "loft",
           "attic", "cellar", "garage", "gutter", "gutters", "roof",
           "wardrobe", "sofa", "settee", "couch", "furniture", "mattress", "bed frame",
           "bookcase", "bookshelf", "shelving", "shelf", "shelves", "flat pack", "flat-pack",
           "flatpack", "move house", "moving house", "house move", "curtain", "curtains",
           "blind", "blinds", "carpet", "paint", "wall", "walls", "door", "doors",
           "window", "windows", "tile", "tiles", "fence", "shed", "decking", "mower",
           "lawn", "drill", "hook", "hooks", "car", "van", "bike", "bicycle",
           "washing", "laundry", "ironing", "dishes", "washing up", "hoover", "vacuum",
           "cleaning", "washing machine", "dishwasher", "boiler", "radiator", "tap",
           "toilet", "fridge", "freezer", "bin", "bins",
           # raising children and paying for them is not a meal for one either
           "raise", "raising", "child", "children", "kid", "kids",
           "bring up", "bringing up", "single parent", "single mum", "single dad",
           "save money", "saving money", "afford", "rent", "bills", "money",
           # "is it ok to go for a meal on my own" is about eating out alone, and "on my own" is
           # in this row's ask words as well as its key, so a meal in a restaurant was read out as
           # how to cook for one. Eating out alone is opinions' out-on-your-own answer.
           "restaurant", "restaurants", "cafe", "pub", "eat out", "eating out", "meal out",
           "go for a meal", "going out for", "out for dinner", "out for lunch", "takeaway")))

ENTRIES.append(entry(
    "more-vegetables",
    (("eat more veg", "eat more vegetables", "more vegetables", "more veg", "get veg into",
      "vegetables in my diet", "eat veg", "five a day", "more greens",
      "blend veg", "blend vegetables", "blended veg", "blend the veg", "hide veg",
      "hide the veg", "hidden veg", "puree veg", "puree the veg", "puree vegetables",
      "sneak veg", "sneak the veg", "veg into a sauce", "vegetables into a sauce"),
     ("how", "what", "should", "shall", "can", "help", "tips", "tip", "ideas", "way", "ways",
      "best", "want", "need", "get", "eating", "hide", "blend", "sneak", "puree")),
    _more_veg,
    # a child who refuses veg is the feeding answer, and a batch of veg for the freezer is the
    # freezing one: this entry is only about getting more of it into ordinary meals
    avoid=("child", "children", "kids", "kid", "toddler", "baby", "son", "daughter", "fussy",
           "picky", "refuses", "wont eat", "won't eat", "freeze", "freezer", "freezing",
           "frozen", "blanch", "batch cook", "batch cooking")))

ENTRIES.append(entry(
    "freeze-meals",
    (("freeze", "freezing", "frozen", "freezer"),
     ("meal", "meals", "dinner", "dinners", "supper", "batch", "ahead", "well",
      "which food", "what food")),
    ("Stews, curries, chilli, bolognese, soup, lasagne and shepherd's pie all freeze well and come "
     "back the same; cook them a bit under and freeze in portions flat in bags so they thaw fast. "
     "Leave out potatoes cooked in a stew, pasta and rice cooked in it, and add fresh pasta, rice "
     "or a jacket potato on the day. Cool within two hours, label the date, eat within three "
     "months, and defrost in the fridge overnight."),
    avoid=("breast milk", "formula", "baby food", "wedding cake", "cake")))

ENTRIES.append(entry(
    "guests-cheap",
    (("guests", "guest", "party", "crowd", "lots of people", "big meal", "whole family",
      "table full", "people coming"),
     ("cheap", "cheaply", "budget", "save money", "afford", "stretch", "inexpensive",
      "cost", "money")),
    ("One big dish that stretches beats several small ones: a chilli, a curry or a pasta bake with "
     "bread and a big salad, where the cheap starch and veg do the filling and the meat is the "
     "flavour. Chicken thighs, mince, tinned tomatoes, lentils and beans cost far less than "
     "prime cuts or fillets, and a slow-cooked shoulder of pork or lamb feeds a table for very "
     "little. "
     "Ask people to bring the pudding or the drinks and nobody minds."),
    avoid=("restaurant", "takeaway", "wedding", "caterer", "catering")))
# Shellfish that stays shut is a food-safety rule, not a cooking tip, so it has its own entry
# rather than living in a recipe: people ask it while holding the pan.
ENTRIES.append(entry(
    "mussels-unopened",
    (("mussel", "mussels", "clams", "clam", "shellfish", "oysters", "oyster"),
     ("open", "opened", "closed", "unopened", "shut", "eat", "eating", "ok", "okay", "safe",
      "didnt", "didn't", "not", "still", "bin", "throw", "gone off", "cook", "cooking",
      "steam", "steamed", "how long")),
    "Tap each mussel before cooking and bin any that stays open, plus any with a broken shell; "
    "after cooking, bin the ones that stayed shut, because an unopened one was dead before it "
    "went in. Steam the rest in a covered pan with a splash of wine or water for four to five "
    "minutes, and eat them the same day rather than keeping them for tomorrow.",
    # A razor clam is asked for by its own name, and the pantry's clam row has the soak and
    # the steam: "how do i cook razor clams" was answered "Tap each mussel before cooking", a
    # mussel's rule for a shellfish that has no beard to pull.
    avoid=("paint", "shell", "seashell", "shells on the beach", "razor")))


# --- the tail of the list lives in cooking_more.py, for size ----------------------------------
# This file is over the publisher's 1 MiB upload limit and the world refuses any PR whose tree
# carries a file that big, so the sections from "how you tell it is cooked" to the end of the file
# moved to a file of their own: the rows are data, they are the end of the list, and they move as
# one block. The rows are put back here, where they used to stand, so `cooking.ENTRIES` is the same
# rows in the same order; the helpers that block defines come back with them, because other
# modules ask `cooking.follow_up(...)` and `cooking.first_plan(...)` and the tests ask for
# `minutes_said`. A name this file already defines is left as it is.
#
# The names are imported rather than copied, so a checker that reads this file can see where they
# come from and nothing is bound twice: `follow_up` and `first_plan` are what other modules ask
# this file for, `minutes_said` what the tests ask for, and `_clean` and `_said_words` are read by
# `a_dinner_without` below.
from .cooking_more import (ENTRIES as _TAIL_ENTRIES, PLAN_KEYS, asks_a_food_fact,
                           first_plan, follow_up, minutes_said, plan_recent, remembered,
                           wants, _clean, _said_words)

ENTRIES.extend(_TAIL_ENTRIES)
