"""Shelf life: the store cupboard, the salad drawer and the salad.

"What can I do with celery" and "how long does celery keep" are the same food and two different
questions. `bot/knowledge/cooking.py` answers the first (one dish per ingredient) and its `KEEPS`
table answers the second for the fresh things in the fridge; this domain is the same kind of
table for the foods that table does not name yet. It is a table, not a mechanism: the key words,
the stand-downs and the `entry` shape are imported from `cooking.py`, so there is one set of
keeping words in the bot and a row here is data.

The rule for a row is the one the table has: reply is concrete, leads with the answer, and gives
the number (how long, how cold, how soon). A line that is not a shelf-life question passes, which
here means the row names the food and a keeping word - "is celery healthy" is a nutrition
question with a different answer, so those words take the line away from the table.
"""
import re

from .cooking import COOKED_WORDS, COOKING_WORDS, KEEP_WORDS, USE_UP_WORDS
from .dishes import KEEP_QUALITY_WORDS
from .lookup import DISH_ASK, PACK_DATE, entry

# The topic ids this domain answers (bot/understanding/topics.py).
ANSWERS = ("cooking", "food-and-drink")

# "Is celery healthy" is a nutrition question, not a shelf-life one: a keeping reply there would
# swap an honest pass for a wrong answer, so a row stands down when the line has one of these.
KEEP_NOT_KEEPING = ("healthy", "unhealthy", "good for you", "bad for you", "fattening",
                    "calories", "carbs", "carbohydrates", "protein", "vitamins", "nutrition",
                    "nutritious", "diet", "dieting", "superfood",
                    # "keep" is the only word a shelf-life question and a sleep question share,
                    # and the row was taking the sleep one: "how long does coffee keep you up" got
                    # the airtight tin. What keeps a person up is the sleep entry's question.
                    "keep me up", "keeps me up", "keep you up", "keeps you up",
                    "keep me awake", "keeps me awake", "keep you awake", "keeps you awake",
                    "awake at night", "stay awake", "cant sleep", "can't sleep")

# A food, the words that name it, and how to keep it. Same shape as KEEPS in cooking.py.
# "How long do oats last" is the bag and "how long does porridge keep" is usually the bowl, and
# the two have different numbers. A line that says porridge without saying oats is asking about
# the made bowl, so it leads with the fridge days; the bag sentence is second for either reading.
OATS_BAG = (
    "Porridge oats keep about 6 months in an airtight jar in a cool, dry cupboard, and a sealed "
    "bag that has stayed dry is still fine a year past the date on it. Ground oats and oat bran "
    "go off sooner, about 3 months, because the oils in them turn: smell the bag, and oats that "
    "smell dusty or taste bitter have gone. Cooked porridge is a keep-two-days food, cooled "
    "quickly and reheated with a splash of milk.")
OATS_COOKED = (
    "Cooked porridge keeps 2 days in the fridge in a covered bowl, and reheat it once with a "
    "splash of milk or water over a low heat, because it sets solid as it cools - the same two "
    "days cooked rice gets, and for the same reason. Dry oats in the bag keep about 6 months in "
    "an airtight jar in a cool, dry cupboard, and longer if the bag stays sealed.")


def _oats_kept(memory, understood):
    """The bowl for "how long does porridge keep", the bag for "how long do oats last"."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if "cooked" in said or "made" in said or ("porridge" in said and "oats" not in said):
        return OATS_COOKED
    return OATS_BAG


ROWS = (
    (("flour", "plain flour", "self raising flour", "self-raising flour", "bread flour"),
     "Flour keeps 6 months in a sealed jar in a cool cupboard and a year in the freezer; wholemeal "
     "and brown flour go off sooner, 3 months, and smell of old paint when they do. Put a bay "
     "leaf in the jar and the weevils leave it alone."),
    (("coffee", "ground coffee", "coffee beans", "instant coffee", "coffee granules"),
     "Ground coffee is at its best in the 2 weeks after opening: keep it in an airtight tin in a "
     "dark cupboard rather than the fridge, which is damp and smells of everything else. Beans "
     "keep a month, and more than a month's worth is better frozen and ground from frozen."),
    (("spices", "spice", "ground spices", "paprika", "cumin", "turmeric", "cinnamon"),
     "Ground spices fade in about 6 months and whole ones last 2 to 3 years: small airtight jars, "
     "away from the hob and the light. Sniff a spoonful - if it smells of nothing it will taste of "
     "nothing, and toasting what is left brings it back a little."),
    (("oil", "olive oil", "cooking oil", "vegetable oil", "sunflower oil", "rapeseed oil"),
     "Oil keeps about a year once opened, often past the date on the bottle if it stays cool and "
     "dark: the cupboard rather than beside the hob, with the cap on. Rancid oil smells of crayons "
     "or old nuts and tastes of them too, so bin it."),
    # The line that names no fruit: "how long does fruit last in the fridge" was a shrug while
    # the berries, apples and melons each had their own row. One sentence with the spread in it
    # answers every fruit that has no row of its own, and a fruit that has one still wins, since
    # a name in the key is worth more than the word "fruit" on its own.
    (("fruit", "fruits"),
     "Most fruit keeps 3 to 7 days in the salad drawer, and it is worth knowing the spread: "
     "berries and ripe stone fruit a day or two, apples, oranges and pears a week or more, and "
     "anything already cut 3 days in a sealed tub. Bananas, whole melons and tomatoes keep their "
     "flavour better out of the fridge."),
    (("celery", "celery sticks", "head of celery", "stick of celery"),
     "A head of celery keeps 2 weeks wrapped in foil in the fridge, which keeps it crisp where a "
     "plastic bag makes it slimy. Limp sticks come back in 20 minutes in iced water, so shave the "
     "dry bottom off first."),
    (("lettuce", "lettuces", "iceberg", "little gem", "romaine"),
     "Lettuce keeps about a week in the fridge: wash and dry the leaves, wrap them in kitchen "
     "paper inside a bag and dress them only at the table, because wet leaves and early dressing "
     "are what wilt a salad. Keep the bag in the salad drawer rather than at the back, where it "
     "freezes; limp leaves come back in iced water for 10 minutes."),
    (("cucumber", "cucumbers"),
     "Cucumber keeps about a week in the fridge, wrapped in a tea towel or a paper bag in the "
     "salad drawer: cling film traps the water and that is what makes it slimy. A soft one is "
     "still fine cooked, and the cut end dries first, so shave that off."),
    (("nuts", "walnuts", "almonds", "cashews", "peanuts", "pine nuts", "pecans"),
     "Nuts keep 3 to 6 months in an airtight jar in a cool cupboard and a year in the freezer; "
     "shelled or chopped ones go rancid sooner, and walnuts and pine nuts fastest. Taste one: a "
     "bitter or soapy taste means the oils have turned, and toasting hides it but does not fix it."),
    (("chocolate", "dark chocolate", "milk chocolate", "chocolate bar"),
     "Chocolate keeps about a year in a cool, dry cupboard, not the fridge, where condensation "
     "brings out a white bloom. The bloom is sugar or fat rather than mould, so it is still fine "
     "to eat; a bar that has been warm goes grey and grainy and is only good for melting."),
    (("bacon", "bacon rashers", "streaky bacon", "smoked bacon"),
     "Bacon keeps about a week in the fridge once the pack is open, sealed in a bag, and 3 "
     "months in the freezer, rashers separated with paper so you can take one at a time. It goes "
     "slimy and smells sharp when it is off; the cure keeps it pink long after that."),
    (("pasta", "dried pasta", "spaghetti", "penne", "macaroni", "fusilli"),
     "Dried pasta keeps about 2 years past the date on the packet in a sealed jar in a cupboard, "
     "and longer if it stays dry. Cooked pasta keeps 3 days in the fridge, tossed with a little "
     "oil so it does not clump, and reheats once in the sauce."),
    # Oats are a dry cupboard food and a cooked breakfast, and the two keep for very different
    # lengths: "how long do oats last" was answered with the porridge method ("simmer 1 part oats
    # to 3 parts liquid"). One row cannot lead with three shelf lives, so there are three.
    # The bag and the bowl keep for very different lengths, so one row answers both and picks its
    # first sentence from the line: "how long does porridge keep" is the made bowl.
    (("oats", "oat", "porridge oats", "rolled oats", "oat groats", "jumbo oats", "oatmeal",
      "oat bran", "porridge"),
     _oats_kept),
    (("overnight oats", "soaked oats", "bircher", "bircher muesli", "overnight porridge"),
     "Overnight oats keep 3 days in the fridge in a lidded jar, and they are better after the "
     "first night than they are after an hour: 40g of oats to about 100ml of milk or yoghurt, "
     "left covered overnight, keeps in the fridge for three breakfasts."),
    # "oatmeal" is the cooked bowl in British English, so it goes with the porridge and not with
    # the dry bag: a fridge question about oatmeal was answered with the cupboard.
    (("porridge", "cooked porridge", "oatmeal", "ready brek"),
     "Cooked porridge keeps 2 days in a lidded tub in the fridge: cool it quickly, then reheat it "
     "with a splash of milk or water and a stir, because cold porridge sets solid. Porridge left "
     "out on the side overnight goes in the bin."),
    (("cereal", "breakfast cereal", "cornflakes", "corn flakes", "muesli", "granola",
      "rice krispies", "weetabix"),
     "An opened box keeps 2 to 3 months in an airtight container and goes soft before it goes "
     "off, so taste rather than sniff it. The date on the box is for the sealed bag inside; "
     "stale cereal comes back crisp in a 150C oven for 5 minutes, spread out on a tray."),
    (("dried fruit", "sultanas", "raisins", "dried apricots", "dates", "prunes", "cranberries"),
     "Dried fruit keeps 6 months in a sealed jar and a year in the fridge, and past that it "
     "hardens rather than spoils. Bring it back in 10 minutes in a bowl of hot water, or leave a "
     "slice of bread in the jar overnight. White crystals on the outside are sugar, not mould."),
    # The made things. The cooked-food table answers all of these with "cooked food keeps 3 to 4
    # days", which is right for a stew and wrong for a mash, a batter, a meringue and a curd: each
    # of these is one or two days, or a week on a shelf, and each goes wrong in its own way.
    (("guacamole", "guac", "avocado dip", "mashed avocado"),
     "Guacamole keeps 1 to 2 days in the fridge in a tub with cling film pressed right onto the "
     "surface, and the lime in it is what slows the browning. Brown on top is oxygen, not rot: "
     "stir it in and it is fine. After two days it tastes flat and watery, so eat it first."),
    (("mashed potato", "mashed potatoes", "mash", "leftover mash"),
     "Mashed potato keeps 2 days in the fridge, less than the potatoes it came from, because the "
     "butter and milk in it turn first. Warm it in a pan with a splash of milk over a low heat "
     "and stir, rather than in the microwave on high, which makes it gluey. It freezes for a "
     "month and comes back a little looser, so beat a knob of butter through it."),
    (("batter", "pancake batter", "crepe batter", "yorkshire pudding batter", "waffle batter"),
     "Batter keeps 1 to 2 days in the fridge in a jug with a lid, and stir it before it goes in "
     "the pan because the flour sinks. One with baking powder in it loses its lift after a day, "
     "so use it the same day for pancakes. Crepe batter is better after half an hour's rest, and "
     "a batter that smells sour or has grey on top goes down the sink."),
    # The pastry-and-cured things. A quiche and a tray of sausage rolls were answered with the
    # recipe (their own cooking question) and smoked salmon with the row for cooked salmon, which
    # is a different food with a different number of days.
    (("quiche", "quiches", "a quiche", "leftover quiche", "savoury tart"),
     "Quiche keeps 3 days in the fridge, covered, and eat it cold or reheat it to piping hot all "
     "the way through rather than warm. A quiche freezes for 2 months, cut in slices and wrapped: "
     "thaw it in the fridge overnight and warm it through. Once the egg custard smells sour or "
     "the top has a sheen of water, it is done."),
    (("sausage rolls", "sausage roll", "leftover sausage rolls"),
     "Sausage rolls keep 2 days in the fridge, in a tub or a paper bag rather than cling film, or "
     "they go soft. Reheat them at 180C for 8 to 10 minutes to get the pastry crisp again, and "
     "eat them hot rather than warm. They freeze well for 2 months unbaked or baked, and the "
     "pastry is what goes first: a soggy bottom means it was wrapped while it was still warm."),
    (("smoked salmon", "smoked salmon slices", "lox"),
     "Smoked salmon keeps 3 days in the fridge once the pack is opened, wrapped tight, and it is "
     "cured rather than cooked so the date on the pack matters more than the days. It freezes for "
     "a month in portions, though the texture goes softer. Eat it within 24 hours once it is out "
     "on a plate, and bin it if it smells sharp or feels tacky."),
    # A pot of chilli already has its row in bot/knowledge/chilli.py (chilli-pot-keep), and the pot
    # is what "how long does a pot of chilli last" was already answered with: no row here.
    (("coconut milk", "tinned coconut milk", "tin of coconut milk", "coconut cream"),
     "An opened tin of coconut milk keeps 4 to 5 days in the fridge in a tub or a jug, and the "
     "thick cream separates to the top, so stir it back in. An unopened tin keeps a year in the "
     "cupboard. Freeze what is left in an ice-cube tray and drop the cubes into a curry."),
    # Meringue is left out on purpose: the meringue table already answers the keeping question
    # ("they keep a week in an airtight tin, and go soft in the fridge"), and a row here also took
    # "how long should i bake them", which is the oven's question after a line about soft meringues.
    (("lemon curd", "curd", "homemade lemon curd"),
     "Lemon curd keeps 2 weeks in a jar in the fridge once it is opened, and homemade curd the "
     "same, though eat homemade within a week if you did not sterilise the jar. It freezes for 3 "
     "months and thaws in the fridge. Curd that has separated, or smells of nail varnish, goes "
     "in the bin - the egg in it is what spoils."),
)

# A keeping row answers a question. "I have half a cucumber going soft" names the food and the
# problem and asks nothing: that is a use-up line with a dish answer of its own, and the problem
# words are what the row has to read past, not what it may fire on. So the key is the keeping
# questions, and a bare "soft" or "limp" only reaches a row through its fix-first entry below.
PROBLEM_ONLY = ("soft", "gone soft", "bendy", "mouldy", "mould", "moldy", "dried out", "dry out",
                "wilt", "wilted", "limp", "rot", "rotten", "green", "greening", "sprout",
                "sprouts", "sprouting")

# "How long does pasta last" and "how long to cook pasta" carry the same two words, so the row
# has to read the question, not just the food: the long-phrase words are in the key, and a line
# that is instructing a pan stands the row down.
LONG_WORDS = ("how long", "how long does", "how long do", "how much longer", "keep for",
              "still ok", "still good", "ok to use", "ok to eat", "out of date", "use by",
              "past its date", "past its best",
              # the day after is a keeping question in the words people use: these rows were
              # missed by "can i eat pasta the day after" as well as the cooked-meat rows were.
              "the day after", "day after", "day later", "a day later", "the following day",
              # "next day" is the same ask in the words people type most, and it reached no keep
              # row: "is it ok to eat chicken the next day" was the lean-protein card and, once
              # that stood down, a shrug, while "is chicken still ok" had the answer all along.
              "next day", "the next day", "day after that", "in the fridge", "out of the fridge")

KEEPING_KEY = tuple(word for word in KEEP_WORDS + LONG_WORDS if word not in PROBLEM_ONLY)

# Cooking the food is not keeping it, and "cook" was not in cooking.py's COOKING_WORDS because no
# entry there needed it: here every row would otherwise take "how long to cook pasta".
COOK_LINE_WORDS = ("cook", "cooking", "cooked through", "boil", "boiling", "minute", "minutes",
                   "al dente", "recipe", "recipes",
                   # "how long does bacon take" is a duration as well, and "take" is what makes
                   # it one: what takes time is the cooking, not the keeping.
                   "take", "takes", "taking",
                   # The rest of the ways a pan is named. "how long should i simmer tomatoes" and
                   # "how long should i simmer a chilli for" both asked the pan and got the drawer
                   # ("Loose in the fridge drawer they keep a week or two"), because the only
                   # cooking verbs in this list were cook and boil. Any verb that names heat is
                   # the cooking question, whatever food it is said about.
                   "simmer", "simmering", "simmered", "fry", "fries", "frying", "fried",
                   "roast", "roasting", "roasted", "bake", "baking", "baked", "grill",
                   "grilling", "grilled", "steam", "steaming", "steamed", "saute", "sauteed",
                   "stir fry", "stir frying", "air fryer", "hob", "sear", "searing",
                   "caramelise", "caramelize", "reduce it", "reduce the")

# "How long does it take?" after a line about nuts is a question about the cake, not about how long
# nuts keep: a bare it/that takes the food from the conversation, and the food is not the subject.
FOLLOW_UP_WORDS = ("it take", "it takes", "does it take", "that take", "will it take",
                   "long does it take", "long will it take", "how long does that take")

# What went wrong, when the line says it. Those lines want the fix first and the week second, so
# a second entry for the food is gated on these words and leads with the recovery.
FLOP_WORDS = ("limp", "limpy", "wilted", "wilting", "soggy", "floppy", "gone soft", "sad")

# "can i still eat slimy mushrooms" asks a verdict, so the card leads with the verdict; "how do i
# stop mushrooms going slimy" asks for the fix, so the card leads with the bag. Same two facts.
_MUSH_VERDICT = ("A little slimy is still fine - it is water, not rot: wipe them and cook them "
                 "soon. A sour smell, brown patches or a sticky feel that stays after wiping means "
                 "bin them, because that is decay and no amount of cooking puts it right.")
_MUSH_FIX = ("A slimy mushroom is a wet one: they are about 90% water and a closed plastic bag "
             "traps the sweat that makes the surface slippery. Tip them into a paper bag in the "
             "fridge, wipe rather than wash them, and cook them soon in a hot dry pan.")
_EATING_WORDS = ("eat", "eaten", "ok", "okay", "safe", "still", "bin", "throw", "throwing",
                 "use", "useable", "usable", "edible", "bad", "off", "risky", "cook with")


def _slimy_mushrooms(memory, understood):
    said = " ".join(str((understood or {}).get(k) or "")
                    for k in ("clean", "norm_text", "text")).lower()
    if any(word in said for word in _EATING_WORDS):
        return _MUSH_VERDICT + " " + _MUSH_FIX
    return _MUSH_FIX + " " + _MUSH_VERDICT


FIX_FIRST = {
    "celery": "Limp celery comes back in 20 minutes in iced water, so shave the dry bottom off "
              "first: a head keeps 2 weeks wrapped in foil in the fridge, which keeps it crisp "
              "where a plastic bag turns it slimy.",
    "lettuce": "Plunge limp lettuce into iced water for 10 minutes and it comes back crisp; dry "
               "the leaves, wrap them in kitchen paper inside a bag in the salad drawer and they "
               "keep about a week. Dress them at the table, since wet leaves and early dressing "
               "are what wilted them in the first place.",
}

# "How long before bed should i stop drinking coffee" is a question about caffeine and sleep,
# not about how long the coffee keeps: the shelf-life rows stand down and the coffee-and-sleep
# answer takes it.
# A medicine keeps its own way, and a line about one is never a shelf-life question about food:
# "my inhaler is out of date" was answered with the dried fruit row, because "dates" is a food in
# that row's key and "date" is in every "out of date" line, so the fruit name answered for the word
# in the question. No keeping row answers a medicine now, and the health entries answer those lines.
KEEP_NOT_MEDICINE = ("inhaler", "inhalers", "tablet", "tablets", "pill", "pills", "medicine",
                     "medicines", "medication", "medications", "prescription", "prescriptions",
                     "insulin", "epipen", "epi pen", "epipens", "eye drops", "eyedrops",
                     "antibiotic", "antibiotics", "paracetamol", "ibuprofen", "painkiller",
                     "painkillers", "calpol", "nurofen", "cough syrup", "antihistamine",
                     "antihistamines", "steroid", "steroids", "vaccine", "jab", "wound dressing",
                     "plasters", "bandage", "ointment", "eye ointment", "contact lens",
                     "contact lenses", "nose drops", "ear drops", "vitamin", "vitamins",
                     "supplement", "supplements", "test strip", "test strips")

KEEP_NOT_SLEEP = ("before bed", "before sleep", "before bedtime", "keep me awake",
                  "keeps me awake", "wake me up", "keeps me up", "last coffee", "last cup",
                  "stop drinking", "stop caffeine", "sleep better", "cant sleep", "can't sleep",
                  "to sleep", "fall asleep")

# A dish made out of the crop is not the crop: "how long does tomato soup keep" was the tomato
# on the counter, and the same line about a mushroom or a leek was the drawer. cooking.py's soup
# row answers the pot, so every row here stands down on a dish word.
DISH_WORDS = ("soup", "soups", "stew", "stews", "broth", "broths", "chowder",
              "minestrone", "casserole", "casseroles", "tagine", "goulash")

# "how long does pasta keep" and "how do i keep pasta warm" are one word and two questions: the
# shelf-life rule is not the pan. The quality words are what tells them apart, so every row here
# stands down on them and cooking.py's `keep-how` entry takes the line.
# A pest is the plant in the ground, not the food in the fridge: "how do i keep slugs off my
# lettuce", "how do i stop snails eating my strawberries" and "something is eating my basil" were
# all answered with how long it keeps in the salad drawer. Anything being grown is the garden's.
GROWING_WORDS = ("slug", "slugs", "snail", "snails", "caterpillar", "caterpillars", "aphid",
                 "aphids", "greenfly", "blackfly", "whitefly", "pests", "pest", "eaten",
                 "eating my", "eating the", "ate my", "holes in", "nibbled", "infestation",
                 "allotment", "greenhouse", "raised bed", "vegetable patch", "veg patch",
                 "in the garden", "my garden", "growing", "grow", "sowed", "sow", "planted",
                 "seedling", "seedlings", "crop", "harvest")

# A mother asking whether a food is safe while she feeds is not asking how long it keeps:
# "is it safe to eat peanuts while breastfeeding" was answered "Nuts keep 3 to 6 months in an
# airtight jar, and a year in the freezer". No row in this table is a feeding answer, so the
# feeding words stand every one of them down and nutrition.py's food-while-breastfeeding,
# family.py's caffeine row and its alcohol row answer those lines.
FEEDING_WORDS = ("breastfeeding", "breast feeding", "breast-feeding", "nursing", "lactating",
                 "chestfeeding", "while im feeding")

_STAND_DOWN = (tuple(COOKED_WORDS) + USE_UP_WORDS + COOKING_WORDS + COOK_LINE_WORDS
               + KEEP_NOT_KEEPING + FOLLOW_UP_WORDS + KEEP_NOT_SLEEP + KEEP_NOT_MEDICINE
               + KEEP_QUALITY_WORDS + GROWING_WORDS + DISH_WORDS + FEEDING_WORDS)

# A row whose reply covers a dried good and its cooked form opens on the dried one, because that
# is what most people mean. A line that names the fridge or the freezer has already said which
# one it means, so those rows stand down there and the cooked answer (cooking.pasta-keep, the
# leftovers rule) takes it: "how long does pasta keep in the fridge" was opening "Dried pasta
# keeps about 2 years past the date on the packet in a sealed jar in a cupboard".
# The words that mean the day on a packet rather than the fruit: "use by" and "best before" are
# printed on a pack, and "the date" and "its date" are what the person is pointing at. None of them
# is a thing you can eat, so the dates row reads them as one rule rather than twenty words.
CALENDAR_DATE = PACK_DATE + ("the date", "its date", "their date", "by date", "dates on",
                             "date said")

# "Dates" the fruit and "a date" with a person are one word with two meanings, and "how long" is in
# every keeping row: "how long should i wait before texting after a first date" was answered "dried
# fruit keeps 6 months in a sealed jar and a year in the freezer". The romance and the diary sense
# of the word stands the fruit row down, and the friends rows answer those lines.
DATING_DATE = ("first date", "second date", "third date", "blind date", "date night",
               "on a date", "out on a date", "a date with", "date tomorrow", "the date went",
               "after a date", "calling after",
               "before texting", "after texting", "texting", "text her", "text him",
               "text them", "asking her out", "asking him out")

ROW_STAND_DOWN = {
    # A smoked salmon is cured and a salmon fillet is raw: the cooked-salmon row is not its row.
    "smoked salmon": ("cooked", "bake", "baked", "roast", "roasted", "fillets"),
    # "fruit" is inside grapefruit, kiwi fruit and fruit cake, and "fruit fly", "fruit bowl" and
    # "fruit tree" are lines of their own: the row is for the drawer, not for a food made with
    # fruit or a plant growing it.
    # "Dates" the fruit and "date" the calendar are one word with two meanings, and the word
    # in "out of date" covered this row's key by itself: "is my butter out of date" and "is my
    # milk past its date" were both told that dried fruit keeps six months in a sealed jar,
    # while keep-butter and keep-milk stood second. A line that says one of these is asking
    # about the date on the packet, not about the fruit, so the fruit row stands down and the
    # food's own row answers it. Only the phrases with the word "date" in them: "use by" and
    # "best before" name no fruit either, but they also do not collide with one.
    "fruit": ("cake", "cakes", "juice", "smoothie", "dried", "tinned", "tin", "can", "jar", "jam",
              "wine", "crumble", "tart", "salad", "chutney", "yoghurt", "yogurt", "grapefruit",
              # a pie is baked, not a fruit in a drawer: this row answered "how long does a
              # fruit pie keep" with "most fruit keeps 3 to 7 days in the salad drawer", and the
              # pie row in dishes.py has the 2 days and the 15-minute reheat.
              "pie", "pies", "pastry",
              "kiwi", "flies", "fly", "bowl", "tree", "trees", "grow", "growing", "plant",
              "plants", "pick", "picking", "ripen", "ripening", "ripe", "buying", "choose",
              "choosing", "healthy", "calories", "sugar", "portion", "portions"),
    "pasta": ("fridge", "refrigerator", "fridge freezer", "freezer", "frozen", "cold",
              "in the fridge", "left in the fridge",
              # "keeps" is an ordinary verb as well as a shelf-life word: "my pasta keeps
              # sticking together" is a pan question and "how do i keep pasta for tomorrow"
              # is a cooked-pasta one, and this row answered both with "dried pasta keeps
              # about 2 years". cooking.pasta-cook and cooking.pasta-keep own those lines.
              "stick", "sticks", "sticking", "stuck", "clump", "clumps", "clumping",
              "for tomorrow", "until tomorrow", "for the next day", "next day", "overnight",
              # the cooked bowl says whether it is still good, and the day alone is in the
              # pan row's avoid: "is pasta still ok tomorrow" is the cooked box, and the
              # ok-shapes are what tell a packet question from a bowl question.
              "ok tomorrow", "okay tomorrow", "still ok tomorrow", "tomorrow ok",
              "ok overnight", "okay overnight", "still ok overnight", "ok the next day",
              "okay the next day",
              # "can i eat pasta the day after" is the cooked bowl too: nobody asks it about a
              # sealed packet, and this row opened "Dried pasta keeps about 2 years" on it while
              # the same question about chicken reached the day-after card.
              "the day after", "day after", "a day after", "day later", "a day later",
              "the following day", "following day", "yesterday", "last night",
              # a sauce is not the pasta it goes on: this row answered "how long does pasta
              # sauce keep" with two years in a cupboard, and cooking.pasta-sauce-keep knows
              # the jar, the carton and the batch.
              "sauce", "pasta sauce", "tomato sauce", "marinara", "passata", "bolognese",
              # a macaroni cheese is a cooked dish wearing a pasta's name: this row answered
              # "how long does macaroni cheese keep" with two years in a cupboard, and the
              # cooked-dish row in cooking_entries knows the 3 to 4 days it really keeps.
              "macaroni cheese", "mac and cheese", "mac n cheese", "cauliflower cheese",
              "cheese sauce", "pasta bake", "lasagne", "cannelloni"),
    # how long to soak oats is a night's soaking and a recipe, and the soaked bowl is the row
    # below it: "how long to soak oats" was being answered with the six-month cupboard.
    # oat milk is a different food from the oats it is made of, and the row was taking it
    "oats": ("to soak", "soak oats", "soaking oats", "soak them", "soaking oats", "oat milk",
             "oatmilk", "oat drink",
             # a thing made of oats keeps like the thing it is, not like the bag: the bag took
             # "how long do oat cakes last" off the cake row and "oat biscuits" off the biscuit's
             "oat cakes", "oatcake", "oatcakes", "oat biscuits", "oat biscuit", "oat bars",
             "oat bar", "oat crackers", "flapjacks", "granola", "muesli", "oatly",
             "porridge pot", "porridge pots"),
    # "how long to soak oats" is the instruction, not the shelf life: the soaked bowl's row is
    # gated on the phrases alone, because "how long do soaked oats keep" is still its question.
    "overnight oats": ("to soak", "how long to soak", "soaking time"),
    # "dates" is the fruit and also the date on the box, and the fruit claimed every "past the
    # date" line: eggs, yogurt, rice and cheese all lost their own keeping answer to the dried
    # fruit card. The stamp words stand this row down, and the singular "the date" is never the
    # fruit - "how long do dates last" and "where should i store dates" carry none of them.
    # The words are CALENDAR_DATE above, the same list the spoilage and nutrition rows read, so
    # "the date on the packet" means the same thing in every module.
    # This key was written twice, first at the top of the dict with the romance and diary senses
    # in it and then here, so the second quietly replaced the first: a dict key said twice keeps
    # only the last one, and the words at the top were dead. "how long should i wait before
    # texting after a first date" was told "dried fruit keeps 6 months in a sealed jar" because
    # the live list knew the date on a packet and not the date with a person.
    "dried fruit": CALENDAR_DATE + DATING_DATE,
    # A dip is also a verb, a dance and a dish you make: "how do i make hummus", "is hummus
    # healthy", "why does guacamole go brown" and "salsa dancing" all have their own answers, and
    # how long the tub keeps is not one of them.
    "houmous": ("make", "making", "recipe", "recipes", "blend", "blitz", "healthy", "healthier",
                "calories", "protein", "good for you", "brown", "browns", "browning",
                "going brown", "stop it going brown", "thick", "thins", "watery", "lumpy",
                "dance", "dancing", "class", "classes", "swim", "swimming", "dip in",
                "dipped", "dipping", "what to dip", "with bread", "with carrots",
                "with crisps", "starter", "party"),
    # "how long do i microwave porridge" and "how long to simmer porridge" are the pan's
    # question, and cooking.py's porridge method has the microwave times in it.
    "porridge": ("microwave", "microwaved", "simmer", "stir", "make", "how long to cook",
                 "how long do i cook"),
    # a car's oil is not a bottle in the cupboard: "how long between oil changes" was answered
    # with a year once opened and rancid smelling of crayons. Anything that names the engine, the
    # dipstick or the change stands this row down, and the cars table answers it.
    "oil": ("oil change", "oil changes", "change the oil", "change my oil", "changing the oil",
            "between oil", "engine", "car", "cars", "van", "dipstick", "mot", "mileage",
            "garage", "mechanic", "gearbox"),
}

# A cooked dish made of the food is a leftovers question with its own answer, so the cooked words
# stand every row down - except a row that already says how long the cooked form keeps. "How long
# does cooked porridge last" had no answer at all while this row knew the number. Such a row
# cannot use the cook words at all, because "cooked" is a form of "cook", so it names the cooking
# question in phrases instead: "how long do i cook oats" is a pan, not a bag.
ROW_COOK_FORMS = {
    "oats": ("how do i cook", "how do you cook", "how long to cook", "how long do i cook",
             "how long should i cook", "cooking time", "cook for", "cook it", "boil", "boiling",
             "simmer", "simmering", "stirring", "microwave", "minute", "minutes", "take",
             "takes", "taking", "recipe", "recipes", "porridge oats to"),
    # The made foods. "Mashed", "cooked" and "boiled" are cooking words, and a cooking word in a
    # keeping row's avoid list is a row that cannot answer for the food it names: that is why the
    # entry build lets a made food out of the cooked stand-down. Making the dish is not keeping it,
    # so each of these lists the words of its own method, and the keeping key does the rest.
    "guacamole": ("make", "making", "recipe", "recipes", "blend", "blitz", "mash it",
                  "dance", "dancing", "dip for", "what to dip"),
    # Reheating is the food-safety question and has its own answer - "piping hot all the way
    # through" - so "can i reheat mashed potato" keeps it, and this row keeps the shelf life.
    "mashed potato": ("make", "making", "recipe", "recipes", "how do i make", "how to make",
                      "lumpy", "gluey", "butter", "cream in", "beat it",
                      "reheat", "reheats", "reheating", "reheated"),
    "batter": ("make", "making", "recipe", "recipes", "how do i make", "how to make",
               "thin", "thick", "lumpy", "mix", "whisk", "rest"),
    "lemon curd": ("make", "making", "recipe", "recipes", "how to make", "set", "setting",
                   "runny", "split", "why is my", "why did my"),
    "quiche": ("make", "making", "recipe", "recipes", "how do i make", "how to make", "bake",
               "baking", "oven", "pastry", "line the tin", "blind bake", "custard"),
    "sausage rolls": ("make", "making", "recipe", "recipes", "how do i make", "how to make",
                      "bake", "baking", "oven", "pastry", "puff", "rough puff"),
    "coconut milk": ("make", "making", "open", "opening", "shake", "separate", "separates",
                     "curdle", "curdles", "thick", "thin"),
}
COOKED_IN_THE_ROW = tuple(ROW_COOK_FORMS)

# "How long do cooked vegetables keep" was answered with "cut vegetables into similar-sized
# pieces, toss them in oil" - the roasting method - and "how long do cooked mushrooms keep" with
# a shrug, because a cooked-food line is a leftovers question and no leftovers row named a
# vegetable. The names here are the cooked forms, so a raw food keeps the row it has: "how long
# does broccoli last" is still broccoli's own answer.
COOKED_VEG_NAMES = ("cooked vegetables", "cooked veg", "leftover vegetables", "leftover veg",
                    "left over vegetables", "left over veg", "roast vegetables", "roast veg",
                    "roasted vegetables", "roasted veg", "roast veggies", "cooked mushrooms",
                    "fried mushrooms", "cooked broccoli", "cooked cauliflower", "cooked carrots",
                    "cooked greens", "cooked cabbage", "cooked courgette", "cooked courgettes",
                    "cooked peppers", "stir fried vegetables", "stir fried veg")

# The cooked word is the subject of this row rather than a sign that the pan came first, so the
# cooking words are held out in phrases: "how long to cook broccoli" is a pan question.
COOKED_VEG_COOK_WORDS = ("how do i cook", "how do you cook", "how long to cook",
                         "how long do i cook", "how long should i cook", "cooking time",
                         "how do i roast", "how long do i roast", "how long in the oven",
                         "oven temperature", "what temperature", "how do i make",
                         "how do i fry", "how long to roast", "how long to boil",
                         "boil them", "boil it", "recipe", "recipes")

COOKED_VEG_REPLY = (
    "Cooked vegetables keep 3 days in the fridge in a covered box, and roast veg 3 to 4 days, "
    "because the oven has already taken the water out of them. Get them in there within 2 hours "
    "of coming off the heat, in a box rather than on a plate, and reheat once, piping hot. "
    "Cooked mushrooms and courgette go first, in 2 days, and anything slimy or sour goes in the "
    "bin, because the bugs that make you ill have no smell.")

# "How do i keep cooked veg warm" and "how do i keep my porridge from sticking" are how-to
# technique questions, not shelf life: the keeping row has the days, not the trick, so it stands
# down and lets the pan answer.
KEEP_TECHNIQUE = ("keep warm", "keeps warm", "keeping warm", "keep it warm", "keep them warm",
                  "keep it hot", "keep them hot", "from sticking", "from going soggy",
                  "from drying", "drying out", "does not stick", "doesnt stick",
                  "moist", "juicy", "tender", "crisp", "crispy",
                  "warm", "hot", "sticking")

COOKED_VEG_STAND_DOWN = tuple(
    word for word in _STAND_DOWN
    if word not in COOKED_WORDS and word not in COOK_LINE_WORDS and word not in COOKING_WORDS)

# "Can I eat chicken the day after" is a keeping question with none of the keeping words in it:
# "the day after" was in no row, and "the next day" only in the rows cooking.py builds, so the
# line with the day in it reached the workout food-timing row ("eat" plus "after") and got carbs
# before a run. The day is the question here and the food is the subject, so this one row takes
# any of the foods people ask it about and gives the fridge rule rather than a timeline each.
_DAY_AFTER = ("the day after", "day after", "a day after", "day later", "a day later",
              "the following day", "following day", "the day later", "two days later",
              "2 days later", "the morning after")

# Only the foods whose own keeping row lives in cooking.py: a food listed here and there halves
# the rarity of the word for both rows, and "how long does pasta last" fell to the cooking-time
# answer the moment "pasta" was listed twice. A food with a row in this module keeps to that row,
# which now takes the same day words through LONG_WORDS.
_DAY_AFTER_FOODS = ("chicken", "rice", "prawn", "prawns", "ham", "beef", "pork", "lamb",
                    "fish", "salmon", "cod", "turkey", "mince", "curry", "stew", "soup",
                    "bolognese", "casserole", "noodles", "couscous", "quiche", "pizza",
                    "sausage", "sausages", "egg", "eggs", "beans", "lentils", "tofu",
                    "shepherds pie", "cottage pie", "lasagne", "leftovers", "leftover")

# The day after a training session, an operation or a night out is a different question, and so is
# a "day after" that is a date on a calendar rather than a plate.
_DAY_AFTER_AVOID = ("workout", "work out", "training", "gym", "run", "running", "exercise",
                    "race", "match", "surgery", "operation", "dentist", "hospital", "vaccine",
                    "jab", "drinking", "drink", "hangover", "night out", "wedding", "funeral",
                    "flight", "interview", "exam", "period", "pill", "morning after pill",
                    "birth", "death", "died", "died", "holiday", "moving", "exam", "results")

# --- a sweet, a pint of milk, and what the freezer does to it -----------------------------------
# "Can I freeze a cheesecake" was a punt, "can i freeze a birthday cake" was the cake recipe, and
# "can i freeze milk" was the card about dairy in pregnancy. Two reasons for the same hole: the
# freezer rows name a cooked *dish* - a stew, a curry, a soup, a lasagne - and a pudding is not
# one of those, while every keeping row that does know the answer stands down on the word
# "freeze" on purpose, because a freezing question is not a shelf life. So the sweets and the
# dairy that people ask about had no row at all. Same shape as the store cupboard above: a food,
# and what the freezer does to it, with the number and the one thing that goes wrong. The cake
# figure is the one the two cake rows in cooking.py already give (2 to 3 months undecorated), so
# the three do not drift apart.
FREEZE_WORDS = ("freeze", "freezes", "freezing", "freezer", "freezers", "frozen",
                "in the freezer", "in a freezer", "in my freezer", "put in the freezer",
                "put it in the freezer", "goes in the freezer", "go in the freezer")

FREEZE_SWEETS = (
    (("cheesecake", "cheesecakes", "baked cheesecake", "new york cheesecake",
      "no bake cheesecake"),
     "Yes, and a cheesecake freezes better than almost any other pudding: slice it first and "
     "wrap each slice, or double-wrap the whole tin, and it keeps 1 to 2 months. Thaw the slices "
     "in the fridge overnight rather than on the side, because a warm thaw makes the cheese weep."),
    (("birthday cake", "sponge cake", "sponge", "victoria sponge", "victoria sandwich",
      "madeira cake", "layer cake", "cake", "cakes"),
     "Yes: cool it completely, leave the icing off, wrap the sponge in two layers and it keeps "
     "2 to 3 months. Thaw it still wrapped in the fridge overnight, then ice it, because a cake "
     "iced before it goes in comes out with the icing stuck to the paper."),
    (("trifle", "trifles"),
     "No, and this is the pudding to eat fresh: jelly weeps, cream splits and the sponge goes "
     "soggy as it thaws, so what comes out is watery at the bottom and grainy on top. Make it the "
     "day before at most and keep it in the fridge."),
    (("panna cotta", "panna cottas"),
     "No: the gelatine weeps as it thaws and the cream sets grainy, so a frozen one never comes "
     "back to that just-set wobble. Make it the day before and keep it in the fridge, where it "
     "holds 2 to 3 days."),
    (("tiramisu", "tiramisus"),
     "It freezes, though it is better fresh: cover the dish and it keeps up to 2 months, then "
     "thaw it in the fridge overnight. Expect the sponge to come back a little wetter and dust "
     "the cocoa on after it thaws, not before."),
    (("custard", "home made custard", "custard sauce"),
     "Yes, in portions for up to 3 months, and cornflour in it is what makes it survive: a plain "
     "egg custard can look watery or grainy once thawed. Thaw it in the fridge and then warm it "
     "gently in a pan, whisking, rather than in the microwave, which splits it."),
    (("chocolate mousse", "mousse", "mousses", "lemon mousse", "chocolate pot",
      "chocolate pots"),
     "Yes, up to 2 months: freeze it in the pots or in a tub with the surface pressed flat, and "
     "thaw it in the fridge for a few hours. A mousse weeps a little as it thaws, so stir it "
     "through before you serve it and nobody can tell."),
    (("milk", "a pint of milk", "semi skimmed milk", "skimmed milk", "whole milk",
      "breast milk", "formula", "goats milk"),
     "Yes, and it keeps about a month in the freezer: pour off a little first, because milk "
     "expands and splits the bottle. Thaw it in the fridge and shake it well, since the fat and "
     "water separate; it is fine for cooking and on cereal, a bit thinner to drink."),
)

FREEZE_SWEET_NAMES = tuple(name for names, _ in FREEZE_SWEETS for name in names)

# A recipe, a nutrition line, a pregnancy line or a shelf life is a different question, and the
# keeping rows already answer the last of those. "Thaw" is the other half of the freezer and it
# belongs to the thaw and refreeze rows, not here.
FREEZE_SWEET_AVOID = ("recipe", "recipes", "how do i make", "how to make", "homemade",
                      "from scratch", "how do i cook", "how long to bake", "cooking time",
                      "healthy", "unhealthy", "fattening", "calories", "good for you",
                      "pregnant", "pregnancy", "breastfeeding", "nursing", "weaning",
                      "allergy", "allergic", "lactose", "how much milk", "ounces",
                      "keep", "keeps", "keeping", "last", "lasts", "use by",
                      "out of date", "past the date", "still ok", "still good",
                      "defrost", "thaw", "thawed", "thawing", "refreeze",
                      # ice cream already has a freezer row of its own, and it is not a question
                      # about freezing something
                      "ice cream", "ice lolly", "ice lollies",
                      # a freezer that has stopped, or food left out of it, is the cold-chain rows'
                      "power cut", "broken", "stopped working", "left out", "out of the freezer")


def _freeze_a_sweet(memory, understood):
    """The freezer answer for the sweet or the milk the line names."""
    said = " " + str((understood or {}).get("clean")
                      or (understood or {}).get("text") or "").lower() + " "
    best = None
    for names, reply in FREEZE_SWEETS:
        for name in names:
            if " %s " % name in said or said.startswith(name + " "):
                if best is None or len(name) > best[0]:
                    best = (len(name), reply)
                break
    return best[1] if best else None


_DAY_AFTER_ENTRY = entry("keep-the-day-after", (_DAY_AFTER_FOODS, _DAY_AFTER),
          "Cooled within two hours and put straight in the fridge, cooked chicken, meat, fish and "
          "pasta keep two days and cooked rice one, and that is the whole rule - the date on the "
          "pack does not stretch it. After that it is a reheat question rather than a keep one: "
          "reheat it once, all the way through, until it is steaming hot, and never reheat rice "
          "twice. Bin anything that smells, feels slimy or was left out overnight.",
          avoid=_DAY_AFTER_AVOID, bias=1)

# --- the sauce is not the pasta it goes on -----------------------------------
# "How long does pasta sauce keep" was answered "Dried pasta keeps about 2 years past the date on
# the packet", and "can i keep pasta sauce for tomorrow" got the cooked-pasta rule, which says
# nothing about the sauce. A recipe answered the freeze question. None of those is a wrong fact
# about sauce; they are answers about another food. A jar, a chilled carton and a batch you made
# keep for three different lengths, so the card picks its first sentence from the line.
PASTA_SAUCE_WORDS = ("pasta sauce", "tomato sauce", "sauce for pasta", "marinara", "passata",
                     "bolognese sauce", "pasta sauce jar", "jar of pasta sauce", "chilli sauce",
                     "tomato and basil sauce", "arrabbiata")
SAUCE_KEEPING_WORDS = ("keep", "keeps", "keeping", "kept", "store", "stores", "storing", "stored",
                       "last", "lasts", "lasting", "how long", "still ok", "still good",
                       "gone off", "go off", "off yet", "next day", "the day after", "tomorrow",
                       "open jar", "opened", "once opened", "leftover", "left over", "batch",
                       "in the fridge", "out of date", "use by",
                       # "can i freeze pasta sauce" went to the recipe, and freezing is the
                       # keeping question with a different length
                       "freeze", "freezes", "freezing", "freezer", "freezers", "frozen")


def _pasta_sauce_keep(memory, understood):
    """Three sauces, three lengths: a bought jar, a chilled carton, and a batch you made.

    A jar is the one people ask about most, so it leads; the batch and the freezer follow in the
    same breath, because the same person usually wants both.
    """
    line = " " + (understood.get("clean") or "") + " "
    if any(word in line for word in (" freeze", " freezer", " frozen", " freezing")):
        return ("Sauce freezes well: cool it quickly, then freeze it in meal-sized portions for "
                "about 3 months, and reheat it once until it is steaming hot. A jar of sauce keeps "
                "5 days in the fridge once it is opened, and sauce you made keeps 3 to 4 days - so "
                "if there is more than you will use, the freezer is the better place for it.")
    if any(word in line for word in (" carton", " cartons", " tub", " fresh pasta sauce",
                                     " chilled sauce", " fresh sauce")):
        return ("A fresh or chilled carton of pasta sauce keeps 3 to 4 days in the fridge once it "
                "is opened, and it is worth transferring it out of the carton into a tub with a "
                "lid. It freezes well in portions for about 3 months; reheat it once, until it is "
                "steaming hot, and bin it if it smells sour or has mould on the surface.")
    if any(word in line for word in (" homemade", " made it", " made my own", " made this",
                                     " batch", " i made", " my own sauce", " left over from",
                                     " from scratch")):
        return ("Sauce you made keeps 3 to 4 days in the fridge in a lidded tub, or 3 months in "
                "the freezer in portions, and it is better for being cooled quickly and put away "
                "while it is still warm rather than left out. Reheat it once, all the way through, "
                "and bin it if it smells sour, fizzes or has mould on top.")
    return ("A jar of pasta sauce keeps 5 days in the fridge once it is opened, with the lid back "
            "on, and until the date on the jar while it is still sealed: the label's use-by is for "
            "the sealed jar, not for the open one. Sauce you made yourself keeps 3 to 4 days, and "
            "either freezes for about 3 months in portions - reheat it once, all the way through.")




# The stand-down above is right for the stamp words and wrong for the one line that is about the
# fruit itself: "can i eat dates past the date" is a dried-dates question, and standing the row
# down left it with the search hedge while it had a keeping answer before. So the fruit's own
# eating words get a row of their own, which no stand-down touches. The explicit stamps stand it
# down instead, because "is it ok to eat dates after the use by" is the use-by line's question.
# The key is the phrases and not the word "dates": the form of that word covers the singular
# "date", so a bare "dates" in the key made the fruit answer "is it ok to eat milk past the date"
# again - the very bug this PR is about. Two phrases are enough to reach a dates question, and a
# line that names another food reaches one at most.
DATES_OWN = entry(
    "keep-dates-own",
    (("eat dates", "dates past", "dates after", "dates last", "store dates", "dates keep",
      "dates go off", "do dates go off", "how long do dates"),
     ("past the date", "past its date", "past their date", "after the date", "out of date",
      "use them up")),
    "Dates keep 6 months in a sealed jar and a year in the fridge, and past the date on the pack "
    "they harden rather than spoil: the soft medjool in a tub go first, and the dry baking ones "
    "last longest. Ten minutes in a bowl of hot water brings a hard one back. White crystals on "
    "the outside are sugar, not mould.",
    bias=1,
    avoid=("use by", "best before", "sell by", "expiry", "expires", "expired", "date on"),
)

# A tub of yoghurt had no keeping row at all, so "can i eat yoghurt past the date" was answered with
# a nutrition card and "can i eat greek yoghurt past the date" with a shrug. It is the commonest pot
# in the fridge and the answer is a number of days, so it gets a row of its own - and the bias is 2
# because the nutrition entries answer the same words ("is it ok to eat yoghurt past the date" was
# the protein card) and the keeping question is the one the line is asking.
YOGHURT = entry(
    "keep-yoghurt",
    (("yoghurt", "yogurt", "greek yoghurt", "greek yogurt", "natural yoghurt", "natural yogurt",
      "plain yoghurt", "plain yogurt"), KEEPING_KEY),
    "An unopened tub keeps about a week past the date on the lid, and once a spoon has been in it "
    "keep it 3 to 5 days - the date is for the sealed pot. Plain yoghurt "
    "that has separated with a little water on top is fine - stir it back in. Bin it if there is "
    "mould on the surface, or if it smells sour or fizzy rather than tangy.",
    bias=2,
    ask=KEEPING_KEY,
    # water on top of a yogurt is a texture question with an answer of its own ("stir it back
    # in"), so this row stands down for it rather than spending the turn on a shelf life
    # `still-yogurt` answers "does yoghurt go off" and "my yogurt smells" with the taste and
    # smell verdicts, so this row stays out of that family: it is the stamped question's row.
    avoid=("go off", "goes off", "gone off", "off", "smell", "smells", "smelly", "sour",
           "mould", "mouldy", "mold", "moldy", "fizzy", "safe", "separated", "separation",
           "separating", "watery", "water on top", "curdled", "lumpy", "runny"),
)

# "Is it ok to eat spinach past the date" was the hedge, "is it ok to eat rice past the date" was the
# calorie card and "is it ok to eat hummus past the date" was the lentils card: none of the three had
# a row for the stamped question. What each did have is a keeping row already - salad-wilt,
# rice-storage, freeze-hummus - and those answers are better for "how do i store spinach" than a
# shelf-life number is. So these three are keyed on the date words alone: the food plus a stamp is
# this row, and every other keeping question about the food goes to the row it already had.
DATE_ASK = ("past the date", "past its date", "past their date", "after the date", "out of date",
            "use by", "use by date", "best before", "ok to eat", "safe to eat", "eat it",
            "eat them", "still ok", "still good")

DATE_ROWS = [
    (("spinach", "baby spinach", "bag of spinach", "spinach leaves"),
     "A bag of spinach keeps about 5 days in the salad drawer and a whole unopened bag a week "
     "longer, and the date on the bag is the day to finish it by rather than a day it is still "
     "good after. Pick out anything slimy before it spreads, don't wash the leaves until you use "
     "them, and a bag that has only gone limp is fine wilted into a curry or an omelette."),
    (("rice", "white rice", "basmati rice", "long grain rice", "brown rice"),
     "Dry rice keeps for years in a sealed jar in a cupboard, and the date on the bag is a "
     "best-before rather than a use-by. Cooked rice is the one to be strict about: cool it within "
     "an hour, box it, and keep it no more than 24 hours in the fridge - reheating does not kill "
     "the spores that grow in rice left warm."),
    # A tub of dip is the hummus question for a different tub: opened, a few days in the fridge,
    # and the date on the lid is for the sealed pot. Guacamole is the short one because avocado
    # browns and sours fastest. On main all three were a shrug, because a dip has no keeping row
    # of its own - "is that dip still ok" is answered by the jar row, which is not the same thing.
    # A tub is asked about in the day words as well as the date ones - "is it tzatziki ok the next
    # day" - and "the next day" belonged to no keeping key, so the tub was a punt and, once the
    # pack-date words reached the bread row, a loaf tip. Only this row takes the day words: for
    # cooked rice and the meats they are another row's question, said better there.
    (("guacamole", "taramasalata", "tarama", "tzatziki", "soured cream dip", "onion dip"),
     "Once opened, a tub of tzatziki or taramasalata keeps about 3 days in the fridge and "
     "guacamole a day or two, because avocado browns and sours fastest: the date on the lid is for "
     "the sealed pot, so judge it by look and smell after that. Press cling film down onto "
     "guacamole to keep the air off it, keep all of them cold, and bin anything that smells sour, "
     "fizzes or has mould.",
     ("next day", "the next day")),
    (("hummus", "houmous", "humous"),
     "Hummus keeps about a week in the fridge in a sealed tub, and 3 to 4 days once a spoon has "
     "been in it: the date on the lid is for the sealed pot, so a couple of days past it is usually "
     "fine. A film of water on top is normal, so stir it in. Bin it if it smells sour or fizzy, or "
     "if there is mould.",
     ("next day", "the next day")),
]

# The cupboard foods that are asked about in every shape - "how long does soy sauce keep", "does
# vinegar go off", "how long do tea bags last" - and that nothing answered: the vinegar, tea,
# soy sauce, peanut butter, opened ham and ice cream lines were all passes or went to a card
# about something else (peanut butter reached the nuts-keep row, tea went to how to brew it).
# One row, one table, because these are one kind of question: a store-cupboard food, a figure,
# and the one thing about it that surprises people.
STORECUPBOARD_KEEP = (
    (("soy sauce", "light soy", "dark soy", "shoyu"),
     "Soy sauce keeps for years in the cupboard, and about a year once it is opened, because the "
     "salt stops anything growing in it. It darkens and a salt crust can form at the neck, and "
     "neither is spoilage; bin it only if it smells sour or has a film on top."),
    (("vinegar", "malt vinegar", "white vinegar", "balsamic", "cider vinegar", "wine vinegar"),
     "Vinegar does not go off: it keeps for years, opened or not, because it is already acid. A "
     "cloudy stringy blob in the bottle is the mother, which is harmless - strain it out and carry "
     "on - and a weaker taste after a couple of years is the only thing that changes."),
    (("tea", "tea bags", "teabags", "tea bag", "loose leaf", "green tea", "earl grey",
      "pg tips", "chamomile tea", "peppermint tea"),
     "Tea does not go off, it goes stale: about six months past the date in a sealed tin, and a "
     "year for loose leaf, after which the flavour fades rather than spoils. Keep it in a tin away "
     "from the light and the kettle's steam, and it is safe to drink long after it has lost its "
     "best."),
    (("peanut butter", "peanut butter jar", "nut butter", "almond butter"),
     "An opened jar of peanut butter keeps about three months in the cupboard, or six in the fridge "
     "if you want it to last. The oil that separates on top is normal - stir it back in rather than "
     "pouring it off - and the sign to bin it is a smell of paint or old oil, which is the nuts "
     "going rancid.",
     "Peanut butter freezes well: a jar keeps about six months in the freezer and thaws overnight "
     "in the fridge, though it may need stirring again afterwards."),
    (("ham", "sliced ham", "cooked ham", "wafer thin ham", "honey roast ham"),
     "An opened pack of cooked ham keeps two to three days in the fridge, sealed in a box, and the "
     "use-by date on the pack only holds while it is unopened. It should feel dry and smell of "
     "nothing much; sliminess or a sour smell means bin it, and do not re-wrap it and hope.",
     "Cooked ham freezes for about one to two months: wrap it in portions, because it goes watery "
     "and salty once thawed and will not slice thin again. Thaw it in the fridge overnight and use "
     "it in a cooked dish rather than a sandwich."),
    (("ketchup", "tomato ketchup", "brown sauce", "hp sauce"),
     "Opened ketchup keeps about a month in the cupboard and six months in the fridge, and the date "
     "on the bottle only counts while it is sealed. A dark colour or a little watery liquid is "
     "normal; a fizzy smell or mould at the neck means bin it."),
    (("marmite", "vegemite", "bovril"),
     "Marmite keeps for years - a couple of years past the date, easy - because it is salty and "
     "dark and nothing grows in it. It can dry out and go stiff in the jar; a spoonful of hot water "
     "stirred in brings it back, and it is safe to finish either way."),
    (("golden syrup", "treacle", "black treacle", "maple syrup"),
     "Golden syrup and treacle keep for years in the cupboard, and black treacle improves for the "
     "first year. Maple syrup is the one that needs the fridge once opened, about six months, and "
     "it is the only one here that can grow mould on top."),
    (("worcestershire sauce", "worcester sauce", "tabasco", "hot sauce", "chilli sauce",
      "sriracha", "franks"),
     "Worcestershire sauce and vinegar-based hot sauces keep for years in the cupboard, and about a "
     "year once opened; a hot sauce can darken and thicken, which is fine. The ones to refrigerate "
     "are the fresh chilli sauces and anything with fruit in it, which keep about three months."),
    (("salt", "table salt", "sea salt", "rock salt"),
     "Salt does not go off at all: it is a mineral and nothing grows in it, so the date means "
     "nothing. It clumps in damp air - a few grains of rice in the cellar, or a quick dry in a warm "
     "oven - and that is the only thing that changes."),
    (("baking powder", "bicarbonate of soda", "bicarb", "baking soda"),
     "Baking powder keeps about six months once the tin is opened, and bicarbonate of soda about a "
     "year, because they lose their fizz rather than spoil. Test it: a teaspoon in a cup of hot "
     "water should foam at once, and if it does not, the cake will not rise."),
    (("cornflour", "corn flour", "custard powder"),
     "Cornflour keeps about a year in a sealed tub in the cupboard, and custard powder about six "
     "months once opened, because both take up damp and go lumpy. It does not go mouldy or unsafe - "
     "it stops thickening properly, which is the sign to replace it."),
    (("ice cream", "ice cream tub", "vanilla ice cream", "gelato", "sorbet"),
     "Ice cream keeps about two to three months in the freezer before it dries out and goes icy, "
     "though it is safe far longer. Press a sheet of cling film onto the surface or keep the "
     "cardboard lid tight, and do not refreeze a tub that has melted, because that is when it turns "
     "grainy and grows ice crystals."),
)

# The question, not the food: a keeping row that fires on the food alone takes "how do i make soy
# sauce" and "what can i do with leftover ham", which are cooking lines.
SC_KEEP_ASKS = ("keep", "keeps", "keeping", "kept", "last", "lasts", "lasting", "go off",
                "goes off", "gone off", "going off", "how long", "store", "stores", "stored",
                "storing", "storage", "out of date", "past its date", "past its best",
                "use by", "still good", "still ok", "still safe", "shelf life", "expire",
                "expires", "expired",
                # "does ketchup need to be in the fridge" is the same shelf-life question in the
                # words people use, and the phrases are long enough not to take "my ham is in the
                # fridge and I need a recipe"
                "in the fridge", "in the cupboard", "in a cupboard", "need to be in the fridge",
                "need to be refrigerated", "refrigerate", "refrigerated",
                "gone hard", "going hard", "gone stiff",
                # the tea card's own words: "tea does not go off, it goes stale" - and the line was
                # a search hedge on main because "stale" was not an ask in this table
                "stale", "stales", "gone stale", "goes stale", "going stale", "went stale")

# "last" is one of the asks and it is also how a day is named: "i did a hot wash with vinegar last
# week and the smell came back" is a cleaning line, and it reached the pantry card because "last"
# met "week" - the answer was "Vinegar does not go off: it keeps for years". A time a thing was
# used is not a shelf life, so a named day stands the row down; "how long does it last" still asks.
_LAST_TIME = ("last week", "last night", "last time", "last month", "last year", "last summer",
              "last winter", "last spring", "last autumn", "last fall", "last christmas",
              "last easter", "last weekend", "last sunday", "last monday",
              "last tuesday", "last wednesday", "last thursday", "last friday", "last saturday")

# A store-cupboard food used to clean with is a cleaning question, not a keeping one: the washing
# machine, the dishwasher, the drain and the kettle have their own cards, and the food named in
# the line is the thing it is cleaned with.
_CLEANING_WITH_IT = ("wash", "washing", "washed", "washing machine", "dishwasher",
                     "smell", "smells", "smelly", "smelled", "stink", "stinks", "stinking",
                     "odour", "odor", "musty", "limescale", "hard water")

# A card that answers a dish, a brand or a job stands this row down: those have better answers.
SC_KEEP_AVOID = _LAST_TIME + _CLEANING_WITH_IT + (
                 "recipe", "recipes", "make", "making", "homemade", "from scratch",
                 "how do i make",
                 "how do i cook", "how much", "per person", "calories", "good for you", "healthy",
                 "diet", "marinade", "marinate", "substitute", "instead of", "brand", "cheapest",
                 "buy", "price", "offer", "clean", "cleaning", "descale", "kettle", "sink",
                 "drain", "wasp", "ant", "weed", "pickle", "pickling", "chutney",
                 "left out", "leave it out", "left on the side", "sitting out", "out of the fridge",
                 "defrost", "thaw", "thawed", "refreeze", "re-freeze",
                 # "how long to brew tea" and "how long does ham take to cook" are jobs, not
                 # shelf lives, and the brew card and the gammon card answer them better
                 "brew", "brewing", "brew it", "steep", "steeping", "steeped", "mash",
                 "tea bag in", "teabag in", "the bag in", "leave the bag", "leaving the bag",
                 "cuppa", "milk in first", "teapot",
                 # steeping is the making too, and with "brew" in the list its other name was
                 # the one hole left: "how long should i steep tea" and "green tea how long to
                 # steep" both got the six-months-in-a-tin answer instead of the three or four
                 # minutes
                 "infuse", "infusing",
                 # a cup cooling down is not a shelf life either: the question is the drink, and
                 # the six-months answer is about the tin
                 "cool", "cooling", "cool down", "cools down", "too hot to drink",
                 # "how long for black tea", straight after "how do i make tea", is the brew time
                 # and the six-months answer was winning it on "how long" alone: a how-long *for*
                 # a thing asks how long to do it, where "how long does it keep" asks the tin
                 "how long for", "how many minutes",
                 "cook", "cooking", "roast", "roasting", "boil", "boiling", "joint", "gammon",
                 "take to cook", "how long to cook", "in the oven", "air fryer", "slow cooker",
                 # a pet's tea is its dinner, and it is not going off like the tin: "my dog has
                 # gone off his tea" was the shelf life of tea instead of a dog to ring the vet
                 # about, and the same goes for any animal named in a keeping question.
                 "dog", "dogs", "puppy", "pups", "cat", "cats", "kitten", "kittens",
                 "rabbit", "rabbits", "hamster", "hamsters", "budgie", "budgies",
                 "guinea pig", "guinea pigs", "pet", "pets", "vet")


def _storecupboard_keep(memory, understood):
    """The keeping answer for the cupboard food the line names."""
    said = " " + str((understood or {}).get("clean")
                     or (understood or {}).get("text") or "").lower() + " "
    frozen = any(word in said for word in ("freezer", "freeze", "frozen", "defrost", "thaw"))
    best = None
    for row in STORECUPBOARD_KEEP:
        names, reply = row[0], row[1]
        if frozen and len(row) > 2:
            reply = row[2]
        for name in names:
            if " %s " % name in said or said.startswith(name + " "):
                if best is None or len(name) > best[0]:
                    best = (len(name), reply)
                break
    if best:
        return best[1]
    return ("Most of these keep far longer than the date on the packet: soy sauce and vinegar for "
            "years, tea for about six months past its date, and an opened jar of peanut butter for "
            "about three months. The date is a quality date on most of them, not a safety one.")


SC_KEEP_NAMES = tuple(name for row in STORECUPBOARD_KEEP for name in row[0])

# A row is (names, reply) and may carry a third item: the day words in which that food is asked
# about. They are added to the row's ask, not to DATE_ASK, so a day said as "the next day" reaches
# the tub it belongs to and leaves cooked rice to the 24-hour rule.
# A date row answers for the packet in the cupboard, and "ok to eat" is a date word as often as it
# is a leftovers one. "Is it ok to eat rice the next day" was answered "Dry rice keeps for years
# in a sealed jar in a cupboard" - true, and not the question - while the cooked-rice card (24
# hours in the fridge, one reheat to piping hot) sat behind it in the table. A line that names the
# day after or says the food is already cooked is the leftovers question, so the packet-date row
# stands down for it.
# The words here are day words and leftover words only. "cooked" and "tomorrow" were in this list
# first and cost two lines the better answer: "avoid" matches word forms, so "cooked" caught
# "im cooking rice tonight can i eat it tomorrow", the packet card stood down, and the water ratio
# that cooks the rice answered a question about eating it the next day.
DATED_STAND_DOWN = {
    "rice": ("leftover", "leftovers", "left over", "reheat", "reheated", "reheating",
             "next day", "the next day", "the day after", "day after", "day later",
             "days later", "yesterday", "in the fridge", "out of the fridge", "takeaway"),
}


def _kept_a_while(reading):
    """True when the line says the thing has already been kept somewhere for a length of time.

    "is it ok to eat rice thats been in the fridge 3 days" reached this row on "rice" and "ok to
    eat", which is the date on the pack. The date is for the unopened pack; a thing that has been
    in the fridge three days is the cooked-rice rule, said by the keeping row for that food.
    """
    return bool(reading.get("kept"))


def _dated_row(row):
    names, reply = row[0], row[1]
    asks = DATE_ASK + tuple(row[2] if len(row) > 2 else ())
    return entry("keep-%s-dated" % names[0], (names, asks), reply, bias=1,
                 avoid=DATED_STAND_DOWN.get(names[0], ()),
                 guard=lambda reading: not _kept_a_while(reading))


ENTRIES = [_DAY_AFTER_ENTRY, DATES_OWN, YOGHURT] + [
    _dated_row(row) for row in DATE_ROWS
] + [
    entry("keep-cooked-veg", (COOKED_VEG_NAMES, KEEPING_KEY), COOKED_VEG_REPLY, bias=1,
          avoid=COOKED_VEG_STAND_DOWN + COOKED_VEG_COOK_WORDS + USE_UP_WORDS + FLOP_WORDS
          + KEEP_TECHNIQUE),
] + [
    entry("keep-%s" % names[0], (names, KEEPING_KEY), reply, bias=1,
          # a cooked dish made of the food is a leftovers question, and "what can i do with it"
          # is a dish question: both have their own answers.
          avoid=(tuple(word for word in _STAND_DOWN
                       if not (names[0] in COOKED_IN_THE_ROW
                               and (word in COOKED_WORDS
                                    or word in COOK_LINE_WORDS)))
                 + ROW_COOK_FORMS.get(names[0], ())
                 + FLOP_WORDS + KEEP_TECHNIQUE + ROW_STAND_DOWN.get(names[0], ())))
    for names, reply in ROWS
] + [
    entry("keep-%s-limp" % names[0], (names, FLOP_WORDS), FIX_FIRST[names[0]],
          bias=2, ask=FLOP_WORDS, avoid=_STAND_DOWN)
    for names, _reply in ROWS if names[0] in FIX_FIRST
] + [
    # Mushrooms already have a keeping row (cooking.KEEPS: a week in a paper bag), but not the
    # question people actually ask about them, which is the slime. It is the bag: they are about
    # 90% water and a sealed one traps the sweat, so the fix comes first and the verdict last.
    # "can i still eat slimy mushrooms" was answered with the limp-lettuce card before this.
    entry("keep-mushroom-slimy",
          (("slimy", "slimey", "slimier", "slimiest", "soggy", "sweaty", "wet"),
           ("mushroom", "mushrooms", "button mushrooms", "chestnut mushrooms", "closed cup",
            "portobello", "shiitake")),
          _slimy_mushrooms,
          bias=2,
          # washing them is what a slimy one needs least, and a cooked dish or a sauce is another
          # question: those keep their own answers.
          avoid=("wash", "washing", "washed", "recipe", "recipes", "sauce", "soup", "risotto",
                 "pizza", "lasagne", "stew", "pie", "curry", "pickle", "dry", "dried",
                 "grow", "growing", "forage", "foraging", "magic")),
    # A bowl of guacamole asked about before it browns is a different question from the one the
    # cold-dip card answers: it knows the fault once it has happened ("has gone brown"), so
    # `how do i stop guacamole going brown` and `why does guacamole go brown` reached nothing at
    # all. It is the same avocado and the same air, so one card covers stopping it, keeping it
    # green and why it happens. The card lives here rather than in cooking.py, which is over the
    # size the world will accept: a change to that file cannot be submitted.
    entry("guacamole-browns",
          (("guacamole", "guac", "avocado dip", "avocado mash"),
           ("brown", "browns", "browning", "going brown", "goes brown", "go brown",
            "green", "stay green", "keep green", "fresh", "stop", "prevent", "why")),
          "It is the air, not the lime: a cut avocado browns where oxygen reaches it, and the "
          "greenest guacamole is the one with the least air in it. Press cling film right onto "
          "the surface in a shallow tub, keep the stones in if you like, and a squeeze of lime "
          "plus a pinch of salt slows it. If it has already browned it is still fine to eat - "
          "stir the top layer in and it looks green again.",
          bias=2,
          # a dip that has already gone brown keeps the cold-dip card, and a recipe or a dish is
          # another question.
          avoid=("has gone", "have gone", "went", "turned", "recipe", "recipes", "make",
                 "making", "freeze", "frozen", "calories", "how much")),
]

# --- the cold chain breaks: a power cut, a freezer that thawed ------------------------------
#
# A cut is not a shelf-life question and it is not a recipe question: it is a verdict on food
# that has been warm, and it was reaching the energy answers ("we had a power cut last night"
# got Economy 7) because "power" on its own names the bill as well as the supply. So the rows
# below are keyed on the state of the cold chain - still shut, thawed, off, refrozen - and never
# on the word "power" alone.
CUT_WORDS = ("power cut", "power cuts", "power went off", "power goes off", "power has gone off",
             "power is off", "power was off", "power failure", "power outage", "power out",
             "lost power", "lose power", "losing power", "no power", "without power",
             "electricity went off", "electricity was off", "electricity is off", "no electricity",
             "without electricity", "lost the electricity", "freezer went off", "freezer was off",
             "freezer is off", "freezer has been off", "cut out", "cut off",
             # "how long does food last if the power goes" is the same outage, asked as a rule
             "power goes", "power go", "power went", "power came back", "power is back",
             "when the power goes", "if the power goes", "if the power cuts")

# "cut out" names the supply and it also names the point: "im starting to think im not cut out for
# teaching" was answered with the two freezer numbers, because the words "cut out" are in the ask
# list. The point is the opinion held about a person and the supply is a thing that stopped, so the
# words after "cut out" decide it - "for" and "to (be)" are the aptitude, and every other line keeps
# the outage.
CUT_OUT_FOR = re.compile(r"\bcut out (?:for|to)\b", re.I)


def _cut_out_for_is_an_aptitude(understood):
    """True when "cut out" is about being suited to a job, so the cold-chain row stands down."""
    said = str((understood or {}).get("clean") or (understood or {}).get("norm_text") or "")
    return bool(CUT_OUT_FOR.search(said))


# The supply going off is one question and what the freezer did about it is another: a door that
# stayed shut means the food is fine, and the answer is the two numbers rather than the bin.
WHEN_WORDS = ("last night", "yesterday", "overnight", "this morning", "today", "hours", "hour",
              "day", "days", "two days", "3 days", "four hours", "6 hours", "since", "meanwhile",
              "still", "think", "worried", "safe", "ok", "fine", "food", "freezer", "fridge",
              "shut", "closed", "opened", "cold")

THAW_WORDS = ("thawed out", "thawed", "thaw", "thawing", "defrosted out", "defrosted",
              "defrost", "defrosting", "melted out", "melted",
              "unfrozen", "no longer frozen",
              # "warm" and "soft" are not here: "my fridge feels warm is it cold enough" is a
              # fridge-temperature question, and a warm fridge is not a thawed one.
              # "soggy" on its own is not a thaw: it is the water fault, and a fried coating that
              # has gone soft is a cooking question. Only the freezer in the line makes it a thaw.
              "gone soft in the freezer", "soggy in the freezer", "soggy from the freezer",
              "soggy out of the freezer", "soggy after the freezer")

REFREEZE_WORDS = ("refreeze", "refrozen", "refroze", "re-freeze", "re freeze", "refreezing",
                  "put it back in the freezer", "back in the freezer", "freeze it again")

# A thaw that is still a job to do, not a thaw that has happened: "how long does it take to defrost
# a chicken", "how long to thaw a kilo of mince", "defrost chicken how long". The cards below
# answer the state of food that has already come out of the freezer, and they were answering these
# with the ice-crystal rule, while the row that times the job (`chicken-defrost`) never got the
# line. The figure the person asked for is the whole question, so a how-long about thawing is not
# this question whatever its other words are (intent, `time`).
TIMES_A_THAW = re.compile(r"\b(?:defrost|thaw)\w*\b", re.I)
ASKS_HOW_LONG = re.compile(r"\bhow (?:long|many (?:hours|minutes|days)|soon)\b", re.I)


def _a_thaw_that_is_a_job(understood):
    """True when the line asks how long thawing something takes, so the food-state card stands down."""
    said = str((understood or {}).get("clean") or (understood or {}).get("norm_text") or "")
    if not TIMES_A_THAW.search(said):
        return False
    return bool(ASKS_HOW_LONG.search(said))


# `cooking.py`'s `refreeze-food` and `refreeze-meat` own the thawed-and-back-in question, so this
# section adds no row for it: two rows would answer one question twice.

# A cut is not the bill, and it is not the decision to own a freezer: those lines name the supply
# and the money together, and they were what took "we had a power cut last night" to the tariff.
COLD_NOT = ("tariff", "economy 7", "economy seven", "night rate", "day rate", "bill", "bills",
            "supplier", "suppliers", "standing charge", "direct debit", "kwh", "unit rate",
            "cheaper", "cheapest", "worth it", "should i buy", "buy a freezer", "chest or upright",
            "chest freezer or", "upright", "running cost", "energy use", "how much electricity",
            "switch", "solar", "battery", "generator", "camping",
            # a food question in pregnancy is the pregnancy table's, not "is it still ok": "is
            # ice cream safe in pregnancy" was answered with the melting-and-refreezing card
            "pregnant", "pregnancy", "trimester", "weeks pregnant")

COLD_REPLIES = {
    "cut": "Keep the doors shut and most of it is fine: a full freezer holds its cold for about "
           "48 hours, a half-full one about 24, and a fridge about 4. Do not open them to look - "
           "that is what lets the cold out. When the power is back, cook and eat the thawing "
           "things first and leave the rest frozen.",
    "thawed": "Judge it on ice crystals rather than on how long it sat: food that is still firm "
              "and icy can be cooked and eaten or refrozen, and meat that thawed in the fridge can "
              "always go back in. Anything soft and warm goes in the bin - meat, fish, shellfish, "
              "cooked rice and milk most of all - and do not taste it to check. Melted ice cream "
              "is binned whatever it feels like.",
    "fridge": "Food in a fridge whose door stayed shut is safe for about 4 hours, and after that "
              "the perishables go: milk, soft cheese, cooked meat, cooked rice and leftovers, "
              "and anything past its date. Butter, hard cheese, jam, pickles and most fruit and "
              "veg come through a warm day, so a full clear-out is not needed.",
    "icecream": "It is safe but it will be grainy: melting and refreezing separates the ice cream, "
                "so it goes icy and slushy rather than creamy. Eat it now rather than keep it. If "
                "the tub was actually warm for hours, bin it - dairy that has been warm is not "
                "worth the risk.",
}

# The cheeses people name at home, and the two questions the keeping table's single cheese row
# does not reach by name: storing it, and mould on it.
CHEESE_NAMES = ("cheddar", "parmesan", "brie", "camembert", "feta", "stilton", "mozzarella",
                "gruyere", "gorgonzola", "blue cheese", "goats cheese", "goat cheese",
                "cream cheese", "cottage cheese", "halloumi", "red leicester", "wensleydale")
STORE_ASKS = ("store", "stores", "storing", "stored", "how do i store", "how should i store",
              "how to store", "how do you store", "best way to store", "where do i keep",
              "where should i keep", "wrap", "wrapped", "wrapping", "once opened")
MOULD_WORDS = ("mould", "mouldy", "mold", "moldy", "moulds", "fuzzy", "furry", "gone mouldy",
               "green bits", "white bits", "spots", "speckled", "fur",
               # what mould looks like before anyone says the word. "blue bits" is the mould
               # question on a brie and the good news on a stilton, and the cheese decides which
               # of the two answers it gets - "my brie has blue bits on it" was a hedge.
               "blue bits", "blue spots", "blue spot", "bits of blue")

# Mould on cheese is one rule with two verdicts, and which one you get depends on the cheese in
# the line, not on which card caught it: brie and cream cheese go in the bin whole, cheddar and
# parmesan are cut an inch past it, and the blue in a stilton is the point rather than a fault.
SOFT_CHEESES = ("cream cheese", "cottage cheese", "brie", "camembert", "mozzarella", "feta",
                "goat cheese", "goats cheese", "mascarpone", "ricotta")
BLUE_CHEESES = ("blue cheese", "stilton", "gorgonzola", "roquefort", "dolcelatte")


def _cheese_mould(memory, reading):
    """The mould verdict for the cheese the line names, and the general one when it names none."""
    said = (reading or {}).get("clean") or ""
    words = " %s " % said.lower()
    for name in BLUE_CHEESES:
        if name in words:
            return ("The blue in %s is meant to be there. Green or white fuzz on it is not, so a "
                    "blue cheese that has grown it goes in the bin." % name)
    for name in SOFT_CHEESES:
        if name in words:
            return ("Mould on %s means the whole piece goes in the bin: the threads run all the "
                    "way through a soft cheese, so there is nothing to cut back to." % name)
    return ("Cut the mould off hard cheese an inch past it and the rest is fine. Soft cheese, "
            "cream cheese and anything already grated or sliced goes in the bin, because the "
            "threads reach further than you can see.")

ENTRIES += [
    # The bare line ("we had a power cut last night") asks for the two numbers, not for the bin.
    entry("cold-cut", (CUT_WORDS, WHEN_WORDS), COLD_REPLIES["cut"], bias=2, ask=CUT_WORDS,
          # "not cut out for the job" is a person's doubt, not an outage
          guard=lambda understood: not _cut_out_for_is_an_aptitude(understood),
          avoid=COLD_NOT),
    # What the freezer did is more specific than the cut, so these sit above the general row.
    entry("cold-thawed", (THAW_WORDS, WHEN_WORDS + ("meat", "chicken", "food", "freezer")),
          COLD_REPLIES["thawed"], bias=5, ask=THAW_WORDS,
          # a how-long about thawing is the timing of the job, and the row that times it owns it
          guard=lambda understood: not _a_thaw_that_is_a_job(understood),
          # how to defrost the freezer is a maintenance job with a method of its own, and going
          # back in the freezer is `cooking.py`'s refreeze question, with the fridge rule in it
          avoid=COLD_NOT + ("how do i defrost", "how to defrost", "how do you defrost",
                            "how can i defrost", "defrost my freezer", "defrost the freezer",
                            "defrost a freezer", "defrosting a freezer", "best way to defrost",
                            "way to defrost",
                            # and any of the ways the machine's own defrosting is asked about:
                            # "my freezer needs defrosting shall i do it now" was answered with
                            # the rule for thawed food, which is another question
                            "needs defrosting", "needs a defrost", "frosting up", "should i defrost",
                            "shall i defrost", "do i defrost it", "defrost it now")
          # "can i freeze mince again after defrosting" is a second-freeze question whatever
          # word it uses for it, and that answer already has the fridge rule in it
          + REFREEZE_WORDS + ("again", "second time")),
    # A frozen thing that has gone soggy is a thaw, whatever verb it uses: "my frozen chicken is
    # soggy" was the raw-chicken keeping answer once "soggy" left THAW_WORDS, because the line
    # says "frozen" rather than "freezer". So the freezer word is the ask and "soggy" is the key.
    entry("soggy-from-the-freezer", (("soggy", "soggyish", "mushy"),
                                     ("frozen", "freezer", "froze", "ice", "icy", "ice crystals")),
          COLD_REPLIES["thawed"], bias=4, ask=("soggy", "mushy"),
          # a soggy vegetable in a pan or a salad is the water fault, and a fried coating that
          # has lost its crisp is a cooking question: neither has a freezer in it, but a line
          # about the packet in the freezer can carry a cooking word too
          avoid=("pan", "salad", "batter", "breaded", "sauce", "risotto", "soup", "chips",
                 "fries", "roast", "cooked")),
    # "the freezer stayed shut so i think its ok" names no cut at all: it is a check on the food,
    # and the two numbers are the answer rather than the shop's opinion of freezers.
    entry("cold-kept-shut", (("freezer", "fridge", "food"),
                             ("stayed shut", "kept it shut", "kept the door shut", "didnt open",
                              "did not open", "stayed closed", "not opened", "still cold",
                              "still frozen")),
          COLD_REPLIES["cut"], bias=4,
          ask=("stayed shut", "kept it shut", "kept the door shut", "didnt open", "did not open",
               "stayed closed", "not opened"),
          # "wont stay shut" is the opposite of "stayed shut" and read as the same words a beat
          # later ("stay" and "stayed" are one word to the matcher), so a freezer door that will
          # not stay closed was told the food was fine: "shut" is also a WHEN_WORD, and the door
          # that will not shut is the seal, in home.py. The denials are here by name for that
          # reason.
          avoid=COLD_NOT + ("wont stay shut", "wont shut", "wont close", "will not stay shut",
                            "will not shut", "will not close", "keeps opening", "pops open",
                            "keeps popping open", "door gap", "not shutting properly")),
    # The door left open is the same question as a cut with a different cause, and on main
    # `e43fd80` it had no answer at all: "my freezer door got left open overnite" was
    # "Got it. Is there anything you'd like a hand with?" and "is the food still ok" after it
    # was the honest shrug. A door left ajar is not a power cut - the cold it loses is the warm
    # air that came in - so the answer is the ice-crystal test and both verdicts.
    entry("cold-door-open",
          (("freezer", "fridge", "freezer door", "fridge door"),
           ("door", "left open", "left it open", "left the door open", "was left open",
            "got left open", "door was open", "door open", "open all night", "open overnight",
            "open all day", "ajar", "didnt shut", "did not shut",
            "didnt close", "not closed properly", "stayed open", "open for hours",
            "left ajar")),
          ("Check for ice crystals rather than counting the hours: anything still firm and icy "
           "can be cooked and eaten or put back, and nothing needs binning for the door alone. "
           "What went soft and warm goes in the bin - meat, fish, shellfish, cooked rice and milk "
           "most of all - and do not taste it to check. A fridge is the stricter one: milk, cooked "
           "meat, cooked rice and leftovers go if the door was open for more than about four "
           "hours, while butter, hard cheese, jam and pickles come through it. Melting ice cream "
           "is binned whatever it feels like, and a freezer that was open all night is worth "
           "running for an hour before you trust the ice."),
          bias=3,
          # the door is the ask: a thermostat, a seal that will not shut, the power going off and
          # going back in the freezer are four other answers
          ask=("left open", "left it open", "left the door open", "was left open",
               "got left open", "door was open", "door open", "open all night", "open overnight",
               "ajar", "didnt shut", "did not shut", "stayed open"),
          # (a door that will not shut is the latch question, so "wont shut" is not here at all)
          avoid=COLD_NOT + ("seal", "seals", "gasket", "thermostat", "temperature setting",
                            "too cold", "not cold enough", "frost", "freezing up", "ice box",
                            "how do i defrost", "how to defrost", "defrost my freezer",
                            "defrost the freezer")
          + REFREEZE_WORDS),
    # A clear-out is the same verdict asked the other way round: nothing needs binning on the
    # strength of the cut alone, and ice crystals are what decide.
    entry("cold-clear-out", (("freezer", "fridge freezer"),
                             ("everything", "all of it", "throw out", "throw away", "bin it all",
                              "clear out", "chuck out", "whole lot")),
          COLD_REPLIES["thawed"], bias=3,
          ask=("throw out", "throw away", "bin it all", "bin everything", "clear out",
               "chuck out", "should i bin"), avoid=COLD_NOT),
    # The state of the fridge, said as a phrase, so the four hours beat a recipe that happens to
    # name milk. The nouns stay in the entries that own them: a key word only one answer used is
    # worth a point to it, so listing milk here would take that point off the milk answer.
    entry("cold-fridge", (("fridge was off", "fridge is off", "fridge has been off",
                           "fridge went off", "fridge was warm", "fridge has been warm",
                           "fridge is warm", "fridge off", "fridge"),
                          WHEN_WORDS + ("off", "warm", "warmth", "all day", "hours")),
          COLD_REPLIES["fridge"], bias=5, ask=CUT_WORDS + ("fridge was off", "fridge is off",
                                                           "fridge went off", "fridge off",
                                                           "warm fridge", "fridge warm"),
          avoid=COLD_NOT + ("fridge freezer",)),
    entry("cold-ice-cream", (("ice cream", "icecream", "ice lolly", "ice lollies", "gelato",
                              "frozen yogurt"),
                             THAW_WORDS + REFREEZE_WORDS + ("ok", "safe", "still", "bin")),
          COLD_REPLIES["icecream"], bias=4,
          ask=("ice cream", "icecream", "ice lolly", "ice lollies", "gelato"), avoid=COLD_NOT),
]


# --- ripe, ripe enough, and how to get it there ------------------------------------------------
# "How do I ripen a mango" and "how do I tell if a mango is ripe" are one fruit and one answer
# with two openings, and "how long does a mango keep" is the same row again. So a row here is
# not a paragraph but three sentences - the test, the trick, and the keeping - and the line
# chooses which one leads. The fogged-spectacles answer in cleaning.py is the same shape: the
# cause first when the line asks why, the fix first when it asks what to do.
# A fruit that is not ripe yet is said by the colour about as often as by the touch, and "green"
# was in none of these lists: "my plums are still green" and "the pears are too green" were the
# only ripeness complaints that had no row at all, while "still hard" had two. The words are
# named once and read by all three lists below - the key side, the ask side and the stated side -
# because they are one family and only the sentence around them changes.
UNDER_RIPE = ("green", "still green", "too green", "very green", "so green", "green as",
              "not ripened", "hasnt ripened", "hasn't ripened", "didnt ripen", "didn't ripen",
              "wont ripen", "refusing to ripen")
RIPEN_WORDS = UNDER_RIPE + (
               "ripe", "riper", "ripen", "ripens", "ripening", "unripe", "underripe",
               "overripe", "hard", "firm", "still hard", "ready", "ready to eat",
               "soft enough", "tell if", "know if", "how do i tell", "how can i tell",
               "when is it ready", "sweet enough",
               # the fruit said to be unripe rather than asked about: "my plums are sour" is the
               # same question as "how do i ripen plums", and so is "can you make a mango softer"
               "softer", "soften", "sour", "not ripe", "too hard", "rock hard", "tasteless",
               # "is a pineapple supposed to be soft at the bottom" is a ripeness question whose
               # only ripeness word is "soft"
               "soft", "squishy", "soft at the bottom", "soft on the bottom", "gone soft",
               "getting soft",
               # "how do i pick a good mango" is the same question as "how do i tell if a mango
               # is ripe" and shares no word with it. The phrases are about choosing one, not
               # about harvest time: a bare "pick" would take "when do i pick apples", which is
               # the garden's question and has its own answer.
               "pick a good", "pick good", "picking a good", "pick the best", "pick a ripe",
               "pick ripe", "choose a good", "choosing a good", "choose the best",
               "choose a ripe", "choosing a ripe", "good one", "good ones", "best one",
               # and the plain verb, because people say "how do i choose a watermelon" and
               # "how do i pick a peach" and no other word in those lines is a ripeness word.
               # "when do i pick apples" stays the garden's: it asks when, not how.
               "how do i pick", "how do i choose", "how to pick", "how to choose",
               "which one to pick", "which one to choose", "which to pick", "which to choose",
               "pick one", "choose one")

# (names, how to tell, how to get it there, how long it keeps)
RIPEN_TABLE = (
    (("mango", "mangoes", "mangos"),
     "A ripe mango gives slightly under a gentle press, like a ripe peach, and smells sweet at "
     "the stem end; the red blush says nothing, so a green one can still be ready.",
     "A hard one ripens on the counter in 2 to 4 days, faster in a paper bag with a banana, "
     "since the banana gives off the gas that does the work.",
     "Once it gives, it keeps about 5 days in the fridge, and a cut mango keeps 3 days in a "
     "sealed tub."),
    (("melon", "melons", "cantaloupe", "honeydew", "galia"),
     "A ripe melon feels heavy for its size, and the end opposite the stem gives a little under "
     "your thumb; a cantaloupe smells sweet there too.",
     "A whole one softens on the counter in 2 or 3 days, quicker in a paper bag, but once it is "
     "cut it will not ripen any further.",
     "Wrap cut melon and keep it 3 days in the fridge; a whole ripe one keeps about a week there."),
    (("watermelon", "watermelons"),
     "A ripe watermelon is heavy for its size, has a creamy yellow patch where it lay on the "
     "ground, and gives a hollow thud when you tap it.",
     "It will not ripen once it is off the vine, so a pale one stays pale and the only thing to "
     "do is keep it cool and eat it.",
     "Whole, it keeps a week or two in a cool room, and cut watermelon keeps 3 days in the "
     "fridge in a sealed tub."),
    (("peach", "peaches", "nectarine", "nectarines"),
     "A ripe peach gives to a gentle press and smells sweet at the stem, and the skin between "
     "the red patches is cream rather than green.",
     "Peaches ripen in a paper bag on the counter in 1 to 3 days, and the fridge is what stops "
     "them and turns them mealy.",
     "Once they give, keep them in the fridge for 3 to 5 days and take them out an hour before "
     "you eat them."),
    (("plum", "plums", "apricot", "apricots", "greengage", "greengages"),
     "A ripe plum gives slightly under the thumb and smells sweet at the stem, and its skin "
     "should be tight rather than wrinkled.",
     "Plums and apricots ripen in a paper bag on the counter in 2 to 4 days.",
     "Once ripe they keep about a week in the fridge, and 3 days in a fruit bowl."),
    (("cherry", "cherries"),
     "A ripe cherry is firm and shiny, dark all over for its variety, with a green stem that "
     "bends rather than snaps.",
     "Cherries do not ripen after picking, so a pale, soft one stays pale and soft.",
     "Keep them unwashed in the fridge for about a week and wash them just before you eat, "
     "because a wet cherry splits and moulds."),
    (("pear", "pears"),
     "A ripe pear gives a little at the neck, just under the stem, and a pear that is soft in "
     "the belly is already past its best.",
     "Pears ripen from the inside out, so buy them firm and leave them on the counter for 2 to 4 "
     "days, or in a paper bag with a banana.",
     "Once the neck gives, they keep about 5 days in the fridge and go floury left out in the "
     "bowl."),
    (("kiwi", "kiwis", "kiwifruit"),
     "A ripe kiwi gives under a gentle press, the way a ripe avocado does.",
     "Hard kiwis ripen on the counter in 3 to 5 days, faster in a paper bag with an apple or a "
     "banana.",
     "Once soft, they keep about 2 weeks in the fridge, and apart from other fruit if you want "
     "them to stay firm."),
    (("pineapple", "pineapples"),
     "A ripe pineapple smells sweet at the base, feels heavy for its size, and a leaf from the "
     "middle of the crown pulls out easily. Softening at the bottom is part of it ripening, so a "
     "firm one with a soft base is ready rather than wrong.",
     "A pineapple gets no sweeter once it is picked, only softer, and it starts at the base, so "
     "the one you buy is as good as it will get.",
     "Whole, it keeps about a week on the counter, and cut pineapple keeps 3 to 4 days in the "
     "fridge in its own juice. One that is soft all over and smells of wine is overripe: eat it "
     "today or freeze it."),
    (("fig", "figs"),
     "A ripe fig is soft all over, droops at the neck and often has a bead of syrup at the eye.",
     "Figs do not ripen once they are picked, so a hard one stays hard.",
     "Keep them 2 or 3 days in the fridge, laid on a plate rather than piled up, and they taste "
     "best at room temperature."),
    (("grape", "grapes", "bunch of grapes"),
     "Ripe grapes are firm and come away from the bunch easily, with a dusty bloom on the skin "
     "rather than a sticky one.",
     "Grapes do not ripen after picking, so a sour bunch stays sour.",
     "Keep them unwashed in a bag in the fridge for a week or more, and wash them just before "
     "eating."),
    # The fruits people keep in the bowl rather than the drawer. Each of these was a shrug while
    # the eleven above it answered, and the shapes are the same three sentences so the line's
    # asking picks the opening the same way.
    (("tomato", "tomatoes"),
     "A tomato is ready when it feels heavy and gives slightly in the hand, smells of tomato "
     "where the stalk was, and the colour is deep and even; a hard, pale one that smells of green "
     "is not there yet.",
     "They ripen off the vine in a bowl on the counter, quicker with a banana or an apple beside "
     "them, and the fridge is what stops that and kills the flavour.",
     "Keep them out of the fridge for up to a week on the counter, and a cut tomato in a tub for "
     "2 days."),
    (("lemon", "lemons", "lime", "limes"),
     "Citrus is picked ripe, so the test is weight rather than colour: a lemon or lime that feels "
     "heavy for its size and gives slightly under a thumb is full of juice, and a light, rock-hard "
     "one is dry inside.",
     "Nothing ripens them at home - a hard one softens a little on the counter in a few days, and "
     "a soft one goes straight in the fridge.",
     "Keep them a week or two in the bowl and a month in the fridge, and a lemon going soft is "
     "still good for juice and zest."),
    (("orange", "oranges", "satsuma", "satsumas", "clementine", "clementines", "tangerine",
      "tangerines"),
     "An orange or a satsuma is ready when it feels heavy for its size, which is juice rather than "
     "thick skin, and smells sweet at the stem; the small thin-skinned ones are usually the "
     "sweeter.",
     "Citrus does not ripen any further once it is picked, so a pale, dry one stays that way.",
     "Keep them a week or two in the bowl and a month in the fridge, and a clementine that is "
     "light and hollow-feeling has dried out at the ends."),
    (("apple", "apples", "braeburn", "cox", "gala", "granny smith"),
     "Apples are picked ripe and keep, so judge by feel: firm, heavy, a clean apple smell and a "
     "fresh green stem.",
     "There is nothing to ripen - a soft or mealy one has been off the tree too long and will not "
     "come back.",
     "Keep them for weeks in the fridge, far longer than on the counter, and away from other fruit "
     "because an apple gives off the gas that ripens everything beside it."),
    (("coconut", "coconuts"),
     "Shake it: a fresh coconut sloshes with liquid, and a silent one has dried out inside. Pick "
     "one heavy for its size with no cracks or damp patches at the eyes.",
     "A coconut is picked ripe, so there is nothing to do at home but open it.",
     "Drink the water the day it is opened, keep the flesh 3 to 4 days in a tub in the fridge, and "
     "freeze what you will not eat."),
    (("papaya", "papayas", "pawpaw", "pawpaws"),
     "A papaya is ready when the skin is mostly yellow-orange rather than green, it gives slightly "
     "under a thumb and smells faintly sweet rather than green.",
     "A green one ripens on the counter in 2 or 3 days, faster in a paper bag, and the fridge "
     "holds it once it is soft.",
     "Eat a ripe one within 2 days, and a cut one within 2 days from the fridge."),
    (("strawberry", "strawberries"),
     "Strawberries do not ripen after picking, so look for deep red right up to the tip under the "
     "leaves, a sweet smell and a dry, bright green cap.",
     "There is nothing to ripen at home and a pale one will not colour up; take them out of the "
     "fridge half an hour before you eat them, which is the only thing that improves them.",
     "Keep them 3 to 5 days in the fridge, unwashed and spread on kitchen paper, since washing "
     "them early is what turns them soft."),
    (("blueberry", "blueberries", "raspberry", "raspberries", "blackberry", "blackberries"),
     "Ripe berries are deep in colour all over with a dusty bloom, plump and only just soft, and a "
     "shrunken or leaking one is past it; taste one, because a punnet is better judged by flavour "
     "than by colour.",
     "Berries do not ripen once they are picked, so a pale one stays pale and sharp.",
     "Keep them 3 to 5 days in the fridge, spread on a plate lined with kitchen paper rather than "
     "heaped in a bag."),
    (("pomegranate", "pomegranates"),
     "A ripe pomegranate is heavy for its size, has square-ish sides rather than a round ball, and "
     "leathery, slightly scuffed skin rather than a shiny one.",
     "Pomegranates are picked ripe and do not ripen further, so a pale, light one stays sharp.",
     "Keep them for weeks in a cool cupboard, the seeds sweetest the day it is opened."),
)

# What the line is asking. "How long does it keep" wants the keeping sentence first, "how do I
# ripen it" the trick, and a plain "is it ripe" the test.
KEEP_ASKS = ("keep", "keeps", "store", "storing", "storage", "last", "lasts", "how long",
             "fridge", "freezer", "freeze", "frozen", "how much longer")
# A line that says the fruit will not ripen yet has already done the test: "the melon i bought is
# rock hard" wants the trick, not a paragraph on how to squeeze a melon, so the state of it leads
# to the trick the same way the verb does.
RIPEN_ASKS = UNDER_RIPE + (
              "ripen", "ripens", "ripening", "hurry", "faster", "speed it up",
              "speed them up", "softer", "soften", "still hard", "rock hard", "hard as",
              "too hard", "not ripe", "unripe", "still firm", "sour", "tasteless", "no flavour",
              "no flavor", "get it ripe", "get them ripe", "make it ripe", "make them ripe",
              # "why are my pears hard" has already said the fruit is hard: that is the trick
              "hard", "sour", "tasteless", "bland")
# "How do i tell" is the one ask that wants the test even when the line calls the fruit hard.
TELL_ASKS = ("tell if", "know if", "how do i tell", "how can i tell", "how to tell",
             "is it ready", "is it ripe", "when is it", "when are they", "ready to eat",
             # "is a pineapple supposed to be soft" asks what a ripe one feels like, which is
             # the test sentence, not the trick
             "supposed to be", "supposed to", "should it be", "should they be", "meant to be",
             "is it normal", "is that normal",
             # the ways people ask how to test a fruit are the verbs of testing it
             "press", "squeeze", "smell", "feel like")

# A fruit is also a topping, an ingredient, a plant in the garden and a thing you peel: those
# lines have answers of their own, and a ripening paragraph in front of them is the wrong reply.
RIPEN_ASIDE = ("pizza", "hawaiian", "topping", "toppings", "juice", "smoothie", "jam",
               "chutney", "pie", "tart", "crumble", "cake", "salad", "salsa", "sauce",
               "recipe", "recipes", "curry", "muffin", "loaf", "grow", "growing", "grew",
               "plant", "plants", "planted", "vine", "vines", "tree", "trees", "blight",
               "greenhouse", "allotment", "seed", "seeds", "sow", "sowing", "compost",
               "peel", "peeled", "peeling", "deseed", "stone", "stoned", "core", "cored",
               "cut up", "chop", "chopped",
               # an opened tin of peaches is a question about the tin, not about the peach, and
               # "two days in the fridge" is the answer (cooking.tin-keep), not three to five
               # "canned" cannot go in: it is a loose form of "can", so every "can i ripen
               # cherries" would stand down on the modal. The phrases that name the tin are enough.
               "tin", "tins", "tinned", "tin of", "tins of", "can of", "cans of", "jar", "jars",
               "opened", "in syrup", "dried", "dried fruit", "sundried",
               # a canned or dried fruit is only in the line as the loose form of "can", which
               # would stand down every "can i ripen cherries" on the modal, so the tin words
               # above are the phrases that name it
               "in a can", "out of a can", "from a can", "in a jar", "out of a jar")


def _ripen_lead(text):
    """Which sentence of the row the line is asking for."""
    if any(word in text for word in TELL_ASKS):
        return "test"
    if any(word in text for word in RIPEN_ASKS):
        return "trick"
    if any(word in text for word in KEEP_ASKS):
        return "keep"
    return "test"


def _ripens(test, trick, keep):
    def reply(memory, understood):
        read = understood if isinstance(understood, dict) else {}
        text = str(read.get("clean") or read.get("text") or "").lower()
        lead = _ripen_lead(text)
        # "The pears are still hard" then "what do i do" carries no word of its own: the row only
        # reached the line through the line it leans on, so that line decides the opening too.
        leans = read.get("leans_on")
        if lead == "test" and not any(word in text for word in TELL_ASKS):
            if isinstance(leans, (list, tuple)):
                leans = " ".join(str(word) for word in leans)
            if leans:
                lead = _ripen_lead(text + " " + str(leans).lower())
        if lead == "keep":
            return keep
        if lead == "trick":
            return trick + " " + test
        return test + " " + trick
    return reply


ENTRIES += [
    entry("ripen-%s" % names[0], (names, tuple(KEEPING_KEY) + RIPEN_WORDS),
          _ripens(test, trick, keep), bias=2,
          avoid=_STAND_DOWN + RIPEN_ASIDE)
    for names, test, trick, keep in RIPEN_TABLE
]

# --- "my peaches are hard as stones" is a ripeness question, not a knife question ------------
# The ripen rows above stand down on the cutting words, because "how do i stone a cherry" is a
# knife question and the ripeness answer is not what to say to it. But the same word comes up in
# the one sentence that is entirely about ripeness: "my peaches are hard as stones" names the
# stone as a way of saying how hard they are, and the knife row answered it. So the hardness
# stated is its own key, and a row built on it keeps its place in front of the knife even when the
# line says "stones", "core" or "chop" - the fruit is not ripe, and that is the whole question.
UNRIPE_STATED = UNDER_RIPE + (
                 "hard", "hard as", "as hard as", "rock hard", "still hard", "so hard",
                 "unripe", "not ripe", "nowhere near ripe", "too hard", "firm as", "as firm as",
                 "like a stone", "like stones", "as stones", "as a stone", "sour", "tasteless",
                 "no flavour", "no flavor", "won't ripen", "wont ripen", "will not ripen",
                 "not softening", "refuses to ripen")

# The tin and the jar are a different food with a different answer, so they still stand the row
# down; the knife words do not, because hardness is the question and the knife is the aside.
_RIPEN_ASIDE_KEEPING = ("pizza", "hawaiian", "topping", "toppings", "juice", "smoothie", "jam",
                        "chutney", "pie", "tart", "crumble", "cake", "salad", "salsa", "sauce",
                        "recipe", "recipes", "curry", "muffin", "loaf", "grow", "growing",
                        "grew", "plant", "plants", "planted", "vine", "vines", "tree", "trees",
                        "blight", "greenhouse", "allotment", "seed", "seeds", "sow", "sowing",
                        "compost", "tin", "tins", "tinned", "tin of", "tins of", "can of",
                        "cans of", "jar", "jars", "opened", "in syrup", "dried", "dried fruit",
                        "sundried", "in a can", "out of a can", "from a can", "in a jar",
                        "out of a jar")


# A hard fruit is not a dish: "what can i do with hard peaches" is about getting them ripe, so the
# rows for the fruit stated hard leave the dish asks out of the stand-down and keep the rest.
_STAND_DOWN_HARD = tuple(
    word for word in _STAND_DOWN
    if not any(dish in word or word in dish for dish in DISH_ASK))


def _ripen_haystack(understood, memory):
    """The current line with the line it leans on and the last few turns behind it."""
    read = understood if isinstance(understood, dict) else {}
    parts = [str(read.get("clean") or read.get("text") or "")]
    leans = read.get("leans_on")
    if isinstance(leans, dict):
        parts.append(str(leans.get("text") or ""))
    elif isinstance(leans, (list, tuple)):
        parts.append(" ".join(str(word) for word in leans))
    turns = (memory or {}).get("turns")
    if isinstance(turns, list) and turns and isinstance(turns[-1], dict):
        # the turn being answered is not in the list yet when a row is asked
        for turn in turns[-3:]:
            said = turn.get("user")
            if isinstance(said, str):
                parts.append(said)
    return " ".join(parts).lower()


def _ripen_row_for(text):
    """The table row whose fruit the text names, or None."""
    for row in RIPEN_TABLE:
        names = row[0]
        for name in names:
            if re.search(r"\b%s\b" % re.escape(name), text):
                return row
    return None


def _ripen_from_the_chat(memory, understood):
    """"will they ripen" and "how long until they are ready": the fruit was named a line ago."""
    row = _ripen_row_for(_ripen_haystack(understood, memory))
    if row is not None:
        return row[2] + " " + row[1]
    return ("Most fruit ripens on the counter in 2 to 4 days, and a paper bag with a banana in it "
            "halves that; the fridge is what stops it, so leave them out until they give. Once "
            "they give, they keep a few days in the fridge.")


ENTRIES += [
    entry("ripen-stated-%s" % names[0], (names, UNRIPE_STATED),
          _ripens(test, trick, keep), bias=2,
          avoid=_STAND_DOWN_HARD + _RIPEN_ASIDE_KEEPING)
    for names, test, trick, keep in RIPEN_TABLE
]

# A vegetable softens in a pan, not on a windowsill, and this row reads "soften" and "how long"
# with no fruit named: "how long do carrots take to soften" was answered "Most fruit ripens on the
# counter in 2 to 4 days" and the carrot's own five-to-seven-minutes card never ran. A vegetable
# named in the line is the pan's question, so the fruit row stands down on the vegetables people
# actually ask the time for; a fruit in the same list ("soft fruit") is not in it.
_NOT_A_FRUIT = ("carrot", "carrots", "potato", "potatoes", "new potato", "new potatoes",
                "parsnip", "parsnips", "swede", "swedes", "turnip", "turnips", "beetroot",
                "cabbage", "cabbages", "broccoli", "cauliflower", "sprout", "sprouts",
                "onion", "onions", "leek", "leeks", "celery", "courgette", "courgettes",
                "aubergine", "aubergines", "pumpkin", "squash", "butternut", "sweet potato",
                "sweet potatoes", "green bean", "green beans", "runner bean", "runner beans",
                "pea", "peas", "sweetcorn", "spinach", "kale", "chard", "fennel", "asparagus",
                "artichoke", "artichokes", "mushroom", "mushrooms", "pepper", "peppers",
                "shallot", "shallots", "spring onion", "spring onions", "chestnut", "chestnuts",
                "lentil", "lentils", "chickpea", "chickpeas", "bean", "beans", "chickpeas",
                "pasta", "rice", "noodle", "noodles", "couscous", "quinoa", "barley",
                "stock", "stew", "soup", "curry", "casserole", "mince", "chicken", "beef",
                "lamb", "pork", "sausage", "sausages", "egg", "eggs")

ENTRIES.append(
    # "my peaches are hard as stones" then "will they ripen": the second line names no fruit at
    # all, and the table rows need one, so the fruit is read from the line it leans on and from
    # the turns just before it.
    entry("ripen-from-the-chat",
          (("ripen", "ripen them", "ripening", "ready", "soften", "ripe"),
           ("will they", "will it", "will these", "do they", "do these", "they ripen",
            "it ripen", "them ripen", "these ripen", "let them", "let these", "leave them",
            "how long", "until", "till they", "get them", "make them")),
          _ripen_from_the_chat, bias=3,
          avoid=("bread", "cake", "cheese", "banana bread", "yoghurt", "yogurt", "milk",
                 "chicken", "meat", "fish", "wine", "beer", "sourdough", "dough", "starter",
                 "breast", "bump", "pregnancy", "pregnant", "nappy", "nappies", "potty")
          + _NOT_A_FRUIT))

ENTRIES += [
    # The keeping table's cheese row names the cheeses but not the store question, so
    # "how do i store parmesan" was an honest pass everywhere, and "how long does cheddar keep
    # once opened" went to the vegetable-drawer row. This entry is the store question for the
    # cheeses people name, and the once-opened figure with it. The ask shapes keep it off the
    # lines that table already answers ("how long does parmesan keep"), so nothing that works
    # today moves.
    entry("cheese-store-by-name", (CHEESE_NAMES, STORE_ASKS),
          "Hard cheese keeps about 2 weeks in the fridge once it is opened and soft cheese about "
          "a week. Wrap it in paper rather than cling film, which sweats it, and keep it in the "
          "drawer at the bottom rather than the door.",
          bias=2, ask=STORE_ASKS,
          avoid=("how much", "per person", "cheeseboard", "board", "recipe", "what can i make",
                 "melt", "melted", "stringy", "grate", "grated", "good for you", "calories",
                 "healthy", "freeze", "freezer", "slimy", "gone hard", "gone dry",
                 "dried out") + MOULD_WORDS),
    # A named cheese that has gone mouldy reached nothing at all: "my parmesan has gone mouldy"
    # was answered "I'm listening", "can i eat around the mould on cheddar" went to a city, and
    # "is it ok to eat mouldy stilton" was a pass. The mould card in cooking.py is keyed on the
    # word "cheese" and a name is all these lines have. One card, because it is one rule.
    entry("cheese-mould-by-name", (CHEESE_NAMES + SOFT_CHEESES + BLUE_CHEESES,
                                   MOULD_WORDS + ("eat", "safe", "ok", "cut", "around it",
                                                  "bin", "throw")),
          _cheese_mould, bias=3, ask=MOULD_WORDS),
    # One row for the sauce, above the keeping table, because a table row names a food and a
    # sauce is asked about in three shapes. `ask=SAUCE_KEEPING_WORDS` keeps it off the recipe
    # lines ("how do i make pasta sauce"), and the avoid list keeps it off the dishes whose own
    # keeping answer is better ("how long does bolognese keep" is the cooked-dish card with the
    # reheat rule in it, and sauce left out is the two-hour rule's question).
    entry("pasta-sauce-keep", (PASTA_SAUCE_WORDS, SAUCE_KEEPING_WORDS),
          _pasta_sauce_keep, bias=2, ask=SAUCE_KEEPING_WORDS,
          avoid=("make", "making", "recipe", "recipes", "cook", "cooking", "how do i cook",
                 # The pan, not the jar: "how long should i simmer a tomato sauce" and "how long
                 # do i cook tinned tomatoes" are the recipe's minutes, and "how long" alone was
                 # enough to bring them here for the open-jar length.
                 "simmer", "simmering", "simmered", "boil", "boiling", "fried", "fry", "fries",
                 "frying", "hob", "pan", "stir", "minutes", "how many minutes", "tinned tomatoes",
                 "chopped tomatoes", "tin of tomatoes",
                 "how do i make", "lasagne", "lasagna", "pizza", "pasta bake", "what can i make",
                 "what can i do", "serve", "serving", "saucepan", "ketchup", "soy sauce",
                 "hot sauce", "worcestershire", "apple sauce", "cranberry sauce", "mint sauce",
                 "bbq sauce", "barbecue sauce", "how much", "per person", "portion", "portions",
                 # a bolognese has a card of its own with the better-next-day line, and sauce
                 # left out is the two-hour rule's question rather than a shelf life
                 "bolognese", "left out", "leave it out", "leaving it out", "left on the side",
                 "stay out", "stays out", "sitting out", "out of the fridge",
                 "on the counter", "overnight")),
    # The cupboard foods, gated on the keeping question so a recipe or a brand line stands down.
    entry("storecupboard-keep", (SC_KEEP_NAMES, SC_KEEP_ASKS),
          _storecupboard_keep, bias=1, ask=SC_KEEP_ASKS, avoid=SC_KEEP_AVOID),
    # Mould on a jar of jam is the one mould question with a different answer from the loaf's:
    # a high-sugar jam can have the patch lifted off, and anything low-sugar or homemade cannot.
    # "the jam has white fluff on it" was the egg-whipping card on main `e06365c`, because "white"
    # is a loose form of "whites" and "fluff" of "fluffy", and "the jam has mould on it" reached
    # nothing at all.
    entry("jam-mould", (("jam", "marmalade", "preserve", "preserves", "chutney", "chutneys",
                         "jam jar", "jam jars", "jar of jam", "marmalade jar", "kilner jar"),
                        ("mould", "mouldy", "mold", "moldy", "fluff", "fluffy", "furry", "fur",
                         "fuzz", "fuzzy", "spots", "speckled", "bloom", "white", "green",
                         "blue", "black", "bits")),
          ("Mould on the top of a jam lifts off: take a spoon and the patch plus a good centimetre "
           "around it, and the rest is fine if it smells and tastes normal. Bin the jar instead if "
           "it is a low-sugar or homemade jam, if the mould runs down the side of the jar, or if "
           "it smells fermented - and never spoon it back in."),
          bias=2,
          avoid=("lid is", "lid has", "peanut butter", "bread", "loaf", "cheese", "meat",
                 "ham", "yoghurt", "jam roly", "doughnut", "sponge", "cake", "tart", "recipe")),
]
# --- the state the food is in now is not whether it has spoiled -------------------------
# "My crisps have gone soft", "my salt is clumpy", "my flour is lumpy" and "is the water on top
# of yoghurt ok" all got a shrug or a neighbour's card on main: the shelf-life rows are keyed on
# keeping words ("how long", "in the fridge") and these lines ask about the state the food is in,
# which is the other question. It is damp or separation in every one of them, not spoilage, and
# the fix is a few minutes of heat, a stir or a sifter. A verdict-first reply for the lines that
# ask whether it is still safe, the fix first for the lines that ask what to do about it.

_CRUNCH_FOODS = ("crisps", "crisp", "potato crisps", "biscuits", "biscuit", "crackers",
                 "cracker", "cereal", "cereals", "cornflakes", "muesli", "granola", "nuts",
                 "crispbread", "pretzels", "tortilla chips", "breadsticks",
                 "bread sticks", "oatcakes", "corn chips", "rice cakes", "pork scratchings",
                 "peanuts", "cashews", "almonds", "walnuts")

_CRUNCH_STATE = ("gone soft", "soft", "gone stale", "stale", "chewy", "soggy", "damp",
                 "rubbery", "lost its crunch", "not crunchy", "no crunch")

# The foods that go soft and have no keeping row of their own: a biscuit, a cereal and a bag of
# nuts keep their own cards, which answer "how do i keep biscuits fresh" better than a jar and a
# tight lid do, so the fresh half of this family is scoped to the ones nothing else names.
_CRUNCH_OWN = ("crisps", "crisp", "potato crisps", "crackers", "cracker", "crispbread",
               "pretzels", "tortilla chips", "breadsticks", "bread sticks", "oatcakes",
               "corn chips", "rice cakes", "pork scratchings")

_CRUNCH_VERDICT = ("Still fine to eat: soft is damp, not spoilage, and heat takes the damp back "
                   "out. Bin them instead if there is mould on any of them, or if they smell of "
                   "old paint or crayons, which is the oil in them going rancid.")

_CRUNCH_FIX = ("Soft, not spoilt: they have taken damp out of the air. Spread them on a tray and "
               "give them 4 to 5 minutes at 150C, then leave them to cool - they crisp as they "
               "cool, not in the oven. Popped corn and nuts take the same and 3 minutes is "
               "enough; a biscuit that has gone chewy comes back the same way.")

_CRUNCH_KEEP = ("To keep the crunch, tip them into a jar or a tin with a tight lid rather than "
                "leaving them in the bag, which breathes, and keep them in a cupboard rather than "
                "the fridge, which is damp. A piece of kitchen paper in the box takes up the damp "
                "the same way.")

_YOGHURT_WHEY = ("That clear liquid is whey, and it belongs to the yogurt: stir it back in. "
                 "Yogurt that has separated into curds and watery liquid and smells sharp, fizzy "
                 "or of alcohol is the one to bin.")

_YOGHURT_FIX = ("Yogurt separates as the whey rises, and spooning from the same spot makes it "
                "happen sooner: take from the side and stir the tub before you serve it. Plain "
                "yogurt keeps about a week past the date once it is open, and stirring is all a "
                "watery tub needs; a sharp or fizzy smell is when to bin it.")

_SALT_CLUMPS = ("Clumped salt has taken damp, not gone off: break it up with the back of a spoon "
                "and it still tastes of salt and works the same in cooking. A few grains of rice "
                "or a piece of dry cracker in the jar keeps it running, and a lidded jar in a dry "
                "cupboard keeps it clump-free where the paper packet does not.")

_FLOUR_LUMPS = ("Lumps in flour are damp, not spoilage: sift it and it is fine to bake with. If "
                "it also smells musty or sour, or the lumps are moving, bin the bag - that is "
                "mites - wipe the shelf out and keep the next bag in a sealed jar.")

_FLOUR_MITES = ("Those are flour mites or weevils and that bag has to go: seal it and bin it, then "
                "go through the dry cupboard - rice, oats, cereal, pasta, dried fruit - and bin "
                "anything open that has them in. Wipe the shelf out, and keep flour in a sealed "
                "jar from then on. They are not a health risk once cooked, but nothing worth "
                "keeping is left in that bag.")


def _said_anything(understood, words):
    said = " ".join(str((understood or {}).get(k) or "")
                    for k in ("clean", "norm_text", "text")).lower()
    return any(word in said for word in words)


_CRUNCH_SAFE = ("safe", "still eat", "still ok", "still good", "can i eat", "ok to eat",
                "edible", "bin", "throw", "off", "bad", "risky", "ill")


def _crunch_reply(memory, understood):
    if _said_anything(understood, _CRUNCH_SAFE):
        return _CRUNCH_VERDICT + " " + _CRUNCH_FIX
    return _CRUNCH_FIX + " " + _CRUNCH_VERDICT


def _yoghurt_reply(memory, understood):
    if _said_anything(understood, ("keep", "keeping", "stop", "runny", "watery", "separate")):
        return _YOGHURT_FIX + " " + _YOGHURT_WHEY
    return _YOGHURT_WHEY


def _flour_reply(memory, understood):
    if _said_anything(understood, ("weevil", "weevils", "mite", "mites", "bug", "bugs",
                                   "worm", "worms", "moving", "insects", "maggots")):
        return _FLOUR_MITES
    return _FLOUR_LUMPS


# A recipe or a shop is not this question, and neither is a nutrition line: those keep their own
# answers, and a crisp-lover's "are crisps bad for you" must not be answered with a tray and an
# oven.
_STATE_NOT_FOOD = KEEP_NOT_KEEPING + ("recipe", "recipes", "how do i make", "how do you make",
                                      "make my own", "homemade", "buy", "buying", "shop",
                                      "supermarket", "brand", "brands", "best", "cheapest",
                                      "where can i", "calories")

ENTRIES += [
    # The crisp, the biscuit and the cracker: the four words people use ("soft", "stale",
    # "chewy", "fresh") and the fix, which is heat and then cooling.
    entry("keep-crunch-gone", (_CRUNCH_FOODS, _CRUNCH_STATE),
          _crunch_reply, bias=2,
          ask=("soft", "stale", "chewy", "soggy", "damp", "rubbery", "crunch",
               "crunchy", "gone", "lost"),
          avoid=_STATE_NOT_FOOD + ("dip", "dips", "recipe", "chocolate", "cake", "bread",
                                   "loaf", "sandwich", "butter", "roast", "salted nuts",
                                   "nut allergy", "allergic", "peanut butter")),
    # The other half of it: "how do i keep crisps fresh" is the same damp question asked before
    # it happens, and crisps have no keeping row of their own.
    entry("keep-crunch-fresh", (_CRUNCH_OWN, ("fresh", "freshness", "stay fresh",
                                              "keep them fresh", "keeps them fresh")),
          _CRUNCH_KEEP + " " + _CRUNCH_FIX, bias=2,
          ask=("fresh", "freshness"),
          avoid=_STATE_NOT_FOOD + ("dip", "dips", "chocolate", "cake", "sandwich", "butter",
                                   "roast", "salted nuts", "nut allergy", "allergic")),
    # The yogurt's clear liquid is whey, and the tub is fine: it was answered with a shrug, and
    # "how do i stop yogurt going watery" with nothing at all.
    entry("keep-yoghurt-whey",
          (("yogurt", "yoghurt", "yogurts", "yoghurts", "greek yogurt", "greek yoghurt",
            "natural yogurt", "natural yoghurt", "plain yogurt", "plain yoghurt"),
           ("water on top", "water at the top", "water in it", "watery", "runny", "separated",
            "separating", "split", "whey", "liquid on top", "liquid in it", "curdled",
            "water out", "get the water out", "drain", "drain it", "sieve", "strain")),
          _yoghurt_reply, bias=2,
          ask=("water", "watery", "runny", "separated", "split", "whey", "liquid", "curdled",
               "keep", "stop", "drain", "strain", "sieve"),
          avoid=_STATE_NOT_FOOD + ("starter", "culture", "make my own", "how do i make")),
    # Salt takes damp and clumps; it does not spoil, and "my salt is clumpy" was an echo.
    entry("keep-salt-clumps",
          (("salt", "sea salt", "table salt", "rock salt", "kosher salt", "salt cellar",
            "salt shaker", "salt jar"),
           ("clumpy", "clumped", "lumpy", "stuck together", "caked", "caking", "gone hard",
            "hard", "damp", "block", "solid")),
          _SALT_CLUMPS, bias=2,
          ask=("clumpy", "clumped", "lumpy", "stuck", "caked", "caking", "hard", "damp",
               "block", "solid"),
          avoid=KEEP_NOT_KEEPING + ("bath", "bath salts", "epsom", "road", "grit", "lamp",
                                    "salt water", "sea water", "gargle", "blood pressure",
                                    "recipe", "bread", "dough", "brine", "rub", "seasoning",
                                    "how much salt")),
    # Flour lumps are damp, and the lump card that answered "my flour is lumpy" was the one about
    # glands. Mites are the same question with a different ending.
    entry("keep-flour-lumps",
          (("flour", "plain flour", "self raising flour", "self-raising flour", "bread flour",
            "wholemeal flour", "white flour"),
           ("lumpy", "lumps", "clumpy", "clumps", "weevils", "weevil", "mites", "mite", "bugs",
            "worms", "moving", "damp", "sour")),
          _flour_reply, bias=2,
          ask=("lumpy", "lumps", "clumpy", "clumps", "weevils", "weevil", "mites", "mite",
               "bugs", "worms", "moving", "damp", "sour"),
          avoid=KEEP_NOT_KEEPING + ("bread", "loaf", "cake", "recipe", "recipes", "how do i make",
                                    "bake", "baking", "sauce", "thicken", "roux", "how much")),
]

# ---------------------------------------------------------------------------
# Mould or slime on produce that is already home from the shop.
#
# The only rows keyed on a mould word and a fruit were the growing ones, so "my strawberries have
# gone mouldy" was answered by garden.py's grey-mould row ("pick and bin every affected fruit
# rather than leaving it on the plant", water at the base) and "my oranges have gone mouldy" by the
# lemon shelf-life. A punnet in the fridge is not a crop, and the kitchen had no answer at all.
#
# What decides the answer is the firmness of the thing, not which fruit it is: mould threads run
# under the skin of anything soft and wet, so a berry, a tomato or a leaf with fuzz on it goes in
# the bin and its neighbours are washed and eaten today; a firm fruit or root is cut an inch past
# the patch and the rest is eaten. `cheese-mould-by-name` and `keep-mushroom-slimy` above own their
# own foods, and the growing question keeps its garden rows through the avoid list below.

OFF_BERRIES = ("strawberry", "strawberries", "raspberry", "raspberries", "blueberry",
               "blueberries", "blackberry", "blackberries", "gooseberry", "gooseberries",
               "cherry", "cherries", "grapes", "grape", "berry", "berries", "punnet",
               "punnet of", "soft fruit", "stone fruit")
# no herbs here: "my herbs have gone slimy" already has the better answer in herbs-keep (bin the
# slimy stems, use the green ones today, and why the bunch keeps badly), and this row only took it
# away. A cabbage however is this row's, because the leaf answer is the leaf answer.
OFF_LEAVES = ("lettuce", "spinach", "salad leaves", "leaves", "rocket", "watercress", "kale",
              "cabbage", "bag of salad", "salad bag", "salad", "coleslaw mix")
OFF_SOFT = ("cucumber", "cucumbers", "courgette", "courgettes", "zucchini", "tomato", "tomatoes",
            "pepper", "peppers", "aubergine", "aubergines", "avocado", "avocados", "mango",
            "mangoes", "peach", "peaches", "nectarine", "nectarines", "plum", "plums", "fig",
            "figs", "melon", "melons", "squash", "pumpkin", "mushy fruit")
# no banana: a banana that has gone black, or "gone off", has ripened and main's own answer
# ("Mash them into banana bread: 3 black bananas...") is the right one. It was in this group for
# one day and the row took "my bananas are going off" off the banana-bread card.
OFF_CITRUS = ("orange", "oranges", "lemon", "lemons", "lime", "limes", "clementine",
              "clementines", "satsuma", "satsumas", "tangerine", "tangerines", "grapefruit",
              "mandarin", "mandarins")
# no potato, no onion and no garlic: main's row for the three is the better and the safer answer
# ("bin anything soft, slimy or smelly, and keep the rest in the dark"), and a mouldy potato or
# clove is not something to trim a patch off. A hard root or a hard fruit is.
OFF_FIRM = ("apple", "apples", "pear", "pears", "carrot", "carrots", "swede", "turnip",
            "beetroot", "parsnip", "parsnips", "ginger", "cabbage head", "cauliflower",
            "broccoli")
OFF_ANY = ("fruit", "fruits", "veg", "vegetables", "produce", "punnet", "the drawer",
           "salad drawer", "veg drawer", "crisper", "greengrocer", "the shopping")
# the spoiling, not the keeping: a shelf-life question is the keeping row's, and "spots" alone is
# a bruise or a ripening mark, so every form here says the food has turned. "is it safe to eat" is
# deliberately not a form: every line that asks it also names the state, and on its own it pulled
# in "is it safe to eat limp lettuce", which wants the revive answer. "white bits" was a form for
# one day: it is a spot, not a state, and it took "my beetroot has white bits on it" from the
# pickle answer.
OFF_WORDS = ("mould", "mouldy", "molds", "mold", "moldy", "fuzzy", "furry", "fuzz", "fur",
             "going mouldy", "gone mouldy", "mould on it", "mould on them", "fluff on",
             "fluffy", "slimy", "slime",
             "slimey", "slimier", "gone off", "gone bad", "rotting", "rotten", "rot",
             "gone rotten", "going off", "gone past it", "on the turn")
# the garden holds the growing question, and the kitchen row must not answer it: a crop on the
# plant, an allotment bed and a watering can are `plant-rot`'s and `soft-fruit-rot`'s lines.
OFF_AVOID = ("plant", "plants", "on the plant", "growing", "grow", "grew", "garden", "gardener",
             "allotment", "crop", "crops", "vine", "vines", "greenhouse", "polytunnel", "tree",
             "soil", "compost", "mulch", "water", "watering", "watered", "harvest", "pick",
             "picking", "picked them", "seedling", "seedlings", "bush", "fertiliser",
             "fertilizer", "feed", "blossom", "blossom end", "slug", "slugs", "snail", "snails",
             "sow", "sowing", "sowed", "transplant", "prune", "pruning", "planted",
             # a dish, a drink or a bake is the recipe's question
             "recipe", "recipes", "cook", "cooking", "bake", "baking", "juice", "juicing",
             "smoothie", "jam", "chutney", "pie", "crumble", "muffin", "muffins", "cake",
             "compost bin", "food waste", "bin day", "wheelie",
             # white or grey mould on a growing courgette is powdery mildew and botrytis, and the
             # garden rows own both: "my courgettes have white mould" lost its mildew answer to
             # this row when it was first added. A fridge never gets mildew in the sentence.
             "mildew", "powdery", "powder", "white powder", "white mould", "grey mould",
             "gray mould", "on the leaves", "on the fruit", "on the stem",
             # a cooked potato, a dish and a bake are `gone-off-pot`'s and the recipe rows': "my
             # baked potato is slimy" is a cooked thing that turned, not produce in a drawer
             "cooked", "cooking water", "baked", "bake", "baked potato", "jacket", "jacket potato",
             "boiled", "boiling", "roast", "roasted", "mashed", "mash", "chips", "fries", "fried",
             "soup", "stew", "curry", "pie", "tart", "casserole", "leftover", "leftovers",
             "reheat", "reheated", "microwave", "salad dressing", "dressed",
             # and a shop that sold it is consumer.py's refund question, not a kitchen one
             "shop", "shops", "supermarket", "sold", "sell", "selling", "refund", "receipt",
             "money back", "take it back", "took it back", "return it", "complaint", "complain",
             "council", "use by", "best before", "label", "packet", "packaging", "delivery",
             # stopping it happening is the keeping row's question, and "bin them" is the wrong
             # answer to "how do i stop my strawberries going mouldy"
             "stop", "stops", "stopping", "prevent", "preventing", "how do i keep", "keep them",
             "keep it from", "keep them from", "last longer", "make them last", "make it last",
             "so they dont go", "so it doesnt go", "so they don't go", "so it doesn't go")


OFF_NAMES = OFF_BERRIES + OFF_LEAVES + OFF_CITRUS + OFF_SOFT + OFF_FIRM + OFF_ANY


def _produce_is_named(understood):
    """True when the line names the fruit, the vegetable or the punnet that has turned.

    A mould word alone is another row's line: "the shop sold me mouldy bread" is the refund and
    "there is mould in the bathroom" is the cleaning row, and neither names produce. Cooked words
    stand this row down in the `avoid` list rather than here, so the number of things this has to
    know stays small.
    """
    low = " %s " % " ".join(str((understood or {}).get("clean")
                                or (understood or {}).get("text") or "").lower().split())
    return any((" %s " % name) in low for name in OFF_NAMES)


# A group answer has to name the thing the line named: "Fuzz, slime or an off smell on a tomato,
# a cucumber or a pepper" was the sentence for fifteen different fruits and vegetables, so a
# question about a melon was answered about a tomato. The branch now reads the name out of the
# line and says it. These are the words that are a category rather than a thing, and they keep the
# generic sentence.
_OFF_GROUP_WORDS = frozenset((
    "berry", "berries", "punnet", "punnet of", "soft fruit", "stone fruit", "fruit", "fruits",
    "veg", "vegetables", "produce", "the drawer", "salad drawer", "veg drawer", "crisper",
    "greengrocer", "the shopping", "mushy fruit", "leaves", "salad", "bag of salad",
    "salad bag", "salad leaves", "coleslaw mix",
))


def _off_one(name):
    """The singular of a produce name, for the sentence that names it."""
    if name.endswith("ies"):
        return name[:-3] + "y"
    for ending in ("oes", "ches", "shes", "sses"):
        if name.endswith(ending):
            return name[:-2]
    if name in ("leaves", "leafes"):
        return "leaf"
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name


def _produce_gone_off(memory, reading):
    """The mould verdict for the produce the line names, in the kitchen rather than the garden."""
    said = " %s " % (((reading or {}).get("clean") or "").lower())

    def thing(group, categories=False):
        """The one produce name in the line from this group, or None.

        The longest form wins so "salad leaves" is not read as "salad", and a category word
        ("berries", "punnet", "produce") gives None, which keeps the generic sentence.

        A branch that never names the thing it is talking about can take a category word, so the
        leaves branch does: "salad leaves gone slimy" was read as "salad", a category, and
        answered with the fuzz sentence, while "lettuce gone slimy" got the slime sentence. Say
        so with categories=True and the rule is the branch's own.
        """
        hit = None
        for name in sorted(group, key=len, reverse=True):
            if (" %s " % name) in said or said.strip().startswith(name + " "):
                if name in _OFF_GROUP_WORDS:
                    return name if categories else None
                hit = name
                break
        return hit

    def phrase(name):
        """("the tomatoes", True) for a plural, ("the melon", False) for one."""
        if name is None:
            return None, False
        one = _off_one(name)
        return "the " + name, one != name

    berries = phrase(thing(OFF_BERRIES))
    leaves = phrase(thing(OFF_LEAVES, categories=True))
    citrus = phrase(thing(OFF_CITRUS))
    soft = phrase(thing(OFF_SOFT))
    firm = phrase(thing(OFF_FIRM))

    if berries[0]:
        return ("Bin every %s with fuzz on it and the ones touching it, then wash the rest and eat "
                "them today. On a berry the mould threads run under the skin where you cannot see "
                "them, so there is nothing to cut back to, and a closed punnet passes it on fast. "
                "Spread what is sound on kitchen paper in the fridge and it will hold a day or "
                "two." % _off_one(berries[0][4:]))
    if leaves[0]:
        return ("Pick out the slimy or furry leaves and bin them: that slime is bacteria, not "
                "water, and cooking will not make it safe to eat. Wash the rest well and eat or "
                "cook them today, because in a closed bag it spreads to whatever touches it. Dry "
                "the next lot in a tea towel and keep them in a bag with a sheet of kitchen "
                "paper, because wet leaves in a sealed bag are what went wrong in the first place.")
    if citrus[0]:
        return ("Bin %s and check the rest of the bag. Mould on citrus starts on the skin and the "
                "flesh under it is soft and wet, so there is nothing worth cutting back to - and "
                "dry the drawer and the bag, because a damp one passes it on. The sound ones keep "
                "a couple of weeks loose in the fridge." % citrus[0])
    if soft[0]:
        return ("Bin %s. %s mostly water, so the mould threads run right through %s and there is "
                "nothing to cut back to, and cooking does not make it safe again. A soft patch "
                "with no mould on it is just older - trim that away and cook the rest today."
                % (soft[0], "They are" if soft[1] else "It is",
                   "them" if soft[1] else "it"))
    if firm[0]:
        return ("Cut the mould off with an inch to spare and use the rest, unless the flesh under "
                "it is soft or smells wrong. A firm fruit or root does not carry the threads deep, "
                "so a small patch on an apple or a carrot is not the whole of it - and bin %s, "
                "because it spreads to what it touches in a drawer." % firm[0])
    return ("Anything soft and wet - a berry, a tomato, a leaf - goes in the bin once it has fuzz "
            "on it, and the sound ones it touched are washed and eaten today. A firm fruit or root "
            "can have the patch cut away with an inch to spare, unless the flesh underneath is "
            "soft or smells off.")


ENTRIES.append(
    entry("produce-gone-off",
          (OFF_BERRIES + OFF_LEAVES + OFF_CITRUS + OFF_SOFT + OFF_FIRM + OFF_ANY, OFF_WORDS),
          _produce_gone_off, bias=4, ask=OFF_WORDS, avoid=OFF_AVOID,
          guard=_produce_is_named))


ENTRIES.append(
    # The sweet that goes in the freezer, and the milk: one row, one table (see FREEZE_SWEETS).
    # The ask is the sweet itself, so a line that says "freeze" about a stew or a curry is still
    # the cooked-dish row's question, and the avoid list keeps the recipe, the nutrition line and
    # the shelf life, which the keeping rows answer better.
    entry("freeze-sweet", (FREEZE_SWEET_NAMES, FREEZE_WORDS), _freeze_a_sweet, bias=3,
          ask=FREEZE_SWEET_NAMES, avoid=FREEZE_SWEET_AVOID))
