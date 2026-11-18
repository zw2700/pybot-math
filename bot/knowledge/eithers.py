"""A choice between two everyday things: which one, and why.

The answers lane owns this domain. "brown or white bread", "tumble dryer or airer", "should I
get the LED bulbs or the halogens" and "which is better, an air fryer or a slow cooker" are
questions people send all the time, and the knowledge base had no answer for most of them: the
composer was left to pick a side on its own, and it picked badly or shrugged ("Halogen", "White
bread. I wouldn't spend another minute on it - both work", "Premium petrol").

None of these is a matter of taste. For most pairs one side is cheaper to run, quicker, kinder
on the joints or does a job the other cannot, and a friend answers with the pick and the reason.
So this domain is one table of picks, keyed on both halves of the pair (never on "or" alone, so
a line that merely mentions two things is left to the domain that knows them) plus a choice word.

It is a domain of its own rather than a part of bot/knowledge/opinions.py because the rarity
bonus the lookup gives a key word counts the entries in its own domain: with these rows inside
opinions.py, "tea" and "coffee" stopped being rare words there and "tea or coffee, which is
better for you" lost its own comparison to a card about roast dates. One table of pairs, apart
from the tables of single things.

A pair that already had a good, longer answer is not here on purpose - fresh against frozen
vegetables, gas against induction, tap water against bottled, dried against fresh herbs, iPhone
against Samsung, cats against dogs. Those answers say more than a pick and a reason, and a row
here would take the line off them.
"""
from .opinions import _either

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("cooking", "food-and-drink", "home-and-diy", "shopping", "health", "fitness",
           "cars", "technology", "entertainment", "garden-and-plants", "money", "opinions",
           "sleep", "small-talk")

# A pair row that keys on "real" and "fake" alone is every argument in the language ("real
# leather or fake leather", "real ale or lager"), so the tree row asks for the tree as well: no
# tree and no Christmas in the line, no reply, and the domain that owns the rest of it answers.
TREE_WORDS = ("tree", "trees", "christmas", "fir", "spruce", "pine")


def _a_christmas_tree(memory, understood):
    """The real-or-fake Christmas tree answer, for a line that is about the tree."""
    words = understood.get("words") if isinstance(understood, dict) else None
    text = " " + " ".join(words or ()).lower() + " "
    if not any(" " + word in text for word in TREE_WORDS):
        return None
    return ("Fake if you will use it for six Christmasses or more, real if not: making a plastic "
            "tree costs about that many years of real ones in carbon. A real tree is the better "
            "evening either way - it smells of the day.")


ENTRIES = [
    # --- the everyday pair, with a verdict and a reason ------------------------------------
    # A pair the bot has no taste about was answered by the composer with an invented side and
    # no reason at all: "led bulbs or halogen" got "Halogen", "regular or premium petrol" got
    # "Premium petrol", "brown or white bread" got "White bread. I wouldn't spend another minute
    # on it - both work", and "cream or milk in coffee" got the it-is-not-mine-to-pick answer for
    # a choice between two people. The bot does have a take on most of these, because they are
    # not matters of taste: one side is cheaper to run, gentler on the joints, quicker, or does a
    # job the other cannot. So each pair gets a verdict and the reason for it, in the words of a
    # friend, and the composer never has to guess.
    #
    # Every pair here is one the knowledge base had no answer for at all: a pair that is already
    # answered well (fresh against frozen vegetables, gas against induction, tap water against
    # bottled, dried against fresh herbs) is left alone, because those answers are longer and
    # more useful than a pick and a shrug.
    _either("white-or-wholemeal-bread",
            ("wholemeal", "wholemeal bread", "brown bread", "brown loaf", "granary",
             "brown or white", "white or brown"),
            ("white bread", "white loaf", "white"),
            "Wholemeal, for most people: more fibre, and it keeps you full until lunch. White "
            "is easier on a sore stomach and makes the better toast, so keep a white loaf in "
            "the freezer for that.",
            avoid=("rice", "pasta", "sugar", "flour", "wine", "vinegar", "sauce", "egg", "eggs",
                   "chocolate", "bread sauce", "sliced white", "toastie", "brown sauce",
                   "shoes", "boots", "hair", "eyes", "skin", "spot", "moth", "rice cooker",
                   # The nutrition card already answers "is brown bread better than white" with
                   # the calories, the fibre multiple and the warning that brown is not
                   # wholemeal, which is more than a verdict. A health comparison keeps it.
                   "better than", "better for", "healthier", "good for you",
                   "is it true", "actually")),
    _either("hardback-or-paperback",
            ("paperback", "paperbacks", "paper back"),
            ("hardback", "hardbacks", "hard back", "hardcover", "hard cover"),
            "Paperback for reading, hardback for keeping: a paperback is lighter in the hand "
            "and about half the price, and a hardback is the one to buy if you will lend it out "
            "or reread it for years.",
            avoid=("kindle", "ereader", "e-reader", "ebook", "audiobook", "library")),
    _either("gym-or-swimming",
            ("swimming", "swim", "pool", "lengths"),
            ("gym", "weights", "weight training", "the gym"),
            "Swimming if your joints, back or knees complain - the water takes the weight - and "
            "the gym if you want strength or a 40-minute session. Whichever you will go to "
            "twice a week beats the better one you skip.",
            avoid=("sea", "beach", "open water", "lido", "lessons", "learn to swim", "ear",
                   "earache", "shoulder", "cost", "membership", "price", "cheaper")),
    _either("audiobook-or-paperback",
            ("audiobook", "audiobooks", "audible"),
            ("paperback", "paper", "book", "books", "reading"),
            "Audiobook for the commute, the washing up and the walk, and paper for anything you "
            "want to remember or quote: fiction and memoir read aloud beautifully, a book with "
            "diagrams or recipes does not.",
            avoid=("kindle", "ereader", "e-reader", "ebook", "library", "hardback", "free",
                   "cheap", "subscription", "worth it", "how long", "speed")),
    _either("duvet-or-blankets",
            ("duvet", "duvets", "quilt"),
            ("blanket", "blankets", "sheets and blankets"),
            "Duvet, unless you sleep hot or share a bed with someone who does: one duvet in a "
            "lower tog is easier to kick off than a pile of blankets, and blankets are the "
            "kinder answer in a heatwave or a summer bedroom.",
            avoid=("tog", "wash", "washing", "clean", "allergy", "allergies", "dust", "mite",
                   "cover", "size", "double", "single", "king")),
    _either("fitted-or-flat-sheet",
            ("fitted sheet", "fitted sheets", "fitted"),
            ("flat sheet", "flat sheets", "top sheet"),
            "Fitted for the bottom, flat for the top: a fitted sheet stays put all night, and a "
            "flat top sheet is the one you can tuck in, layer under a duvet or throw off. A bed "
            "wants one of each.",
            avoid=("size", "sizes", "cot", "cot bed", "moses", "how to fold", "fold")),
    _either("white-or-wholemeal-pasta",
            ("wholemeal pasta", "wholewheat pasta", "brown pasta"),
            ("white pasta", "white"),
            "Wholemeal if you want the fibre and don't mind it a little denser; white holds a "
            "light sauce better and goes softer, which is what you want in a bake or with a "
            "tomato sauce and nothing else.",
            avoid=("rice", "bread", "sauce", "wine", "flour", "sugar", "chocolate", "egg")),
    _either("powder-or-liquid-detergent",
            ("powder", "washing powder", "detergent powder"),
            ("liquid", "liquid detergent", "liquid tabs", "gel"),
            "Powder for a full load, whites and hard water; liquid for a cold wash and anything "
            "greasy. Both clean, so buy whichever is cheaper and use the dose it says - more "
            "soap does not mean cleaner clothes.",
            avoid=("tablet", "tablets", "capsule", "capsules", "dishwasher", "baby", "formula",
                   "milk", "protein", "cocoa", "curry", "chilli", "spice", "bicarbonate")),
    _either("kitchen-roll-or-cloth",
            ("kitchen roll", "kitchen towel", "kitchen paper", "paper towel", "paper towels"),
            ("cloth", "cloths", "tea towel", "tea towels", "microfibre", "dishcloth"),
            "Cloth for the everyday wipe and the table after dinner; kitchen roll kept for raw "
            "chicken, a spill you want to bin and anything bodily. A cloth and a hot wash does "
            "most of what a roll does, for years instead of weeks.",
            avoid=("sanitary", "period", "nappy", "baby wipes", "reusable", "make your own",
                   "sew", "knit")),
    _either("paper-or-plastic-bag",
            ("paper bag", "paper bags", "paper"),
            ("plastic bag", "plastic bags", "carrier bag", "plastic"),
            "A bag for life beats both, because it is made once and used for years. Between "
            "the two: paper for the paper recycling, plastic if the shopping will be rained on "
            "or the bag is going to hold something wet.",
            avoid=("straw", "straws", "cup", "cups", "plate", "plates", "cutlery", "packaging",
                   "bottle", "bottles", "bin", "bin bag", "recycle", "recycling", "free",
                   "charge", "5p", "10p")),
    _either("black-or-green-tea",
            ("green tea", "green"),
            ("black tea", "black", "builders tea", "english breakfast", "earl grey"),
            "Green if you want less caffeine and drink it without milk; black if you take milk "
            "or want a proper cup in the morning. Green wants water just off the boil and two "
            "minutes, or it turns bitter.",
            avoid=("chai", "matcha", "herbal", "mint", "camomile", "chamomile", "fruit tea",
                   "rooibos", "decaf", "loose", "bags", "teapot", "sugar", "milk", "coffee")),
    _either("rice-cooker-or-pan",
            ("rice cooker", "rice cookers"),
            ("pan", "saucepan", "pot"),
            "The pan if you cook rice once a week: rinse, one and a half parts water, lid on, "
            "lowest heat, twelve minutes. A rice cooker if it is most days - it holds the "
            "temperature and switches itself off, so rice stops being something you watch.",
            avoid=("slow cooker", "pressure cooker", "air fryer", "frying pan", "wok",
                   "how long", "how do i", "recipe", "brown rice", "pudding")),
    _either("toaster-or-grill",
            ("toaster", "toasters"),
            ("grill", "grilled", "under the grill"),
            "Toaster for bread, grill for everything else: the grill does cheese on toast, "
            "garlic bread and a browned top on a bake, and the toaster does none of that. If "
            "there is room for one, the grill is more use.",
            avoid=("cheese", "sandwich", "how do i clean", "clean the", "crumpet", "bagel")),
    _either("slow-or-pressure-cooker",
            ("slow cooker", "slow cookers", "crockpot", "crock pot"),
            ("pressure cooker", "pressure cookers", "instant pot"),
            "Slow cooker for a cheap cut you leave all day; pressure cooker for the same stew "
            "in 40 minutes, or dried beans without soaking. For a weekday the pressure cooker "
            "is the one that gets used.",
            avoid=("air fryer", "recipe", "how long", "curry", "stew", "worth it", "buy",
                   "buying", "cheap", "electricity", "cost")),
    _either("air-fryer-or-slow-cooker",
            ("air fryer", "air fryers"),
            ("slow cooker", "slow cookers", "crockpot", "crock pot"),
            "They do opposite jobs, so it is not really either: the air fryer is for anything "
            "you want crisp in 15 minutes - chips, chicken, roast vegetables - and the slow "
            "cooker for a stew that needs the afternoon. If you cook chips or roast more than "
            "once a week, it is the air fryer.",
            avoid=("how long", "recipe", "curry", "stew", "cheap", "cheaper", "electricity",
                   "cost", "worth it", "buy", "buying"),
            # The appliance row in opinions ("a slow cooker is worth it if you are out all day")
            # is keyed on one appliance name plus "should i get", so it outranked this pair on
            # "in a small kitchen should i get an air fryer or a slow cooker" and gave a verdict
            # on one of the two. A pair that names both halves outranks a verdict on one.
            bias=3),
    _either("dishwasher-or-by-hand",
            ("dishwasher", "dishwashers"),
            ("by hand", "washing up", "wash up", "hand wash", "sink"),
            "The dishwasher, for a household: a full load uses less hot water than a bowl of "
            "washing-up does, and it wins on the nights you would otherwise leave the plates. "
            "By hand wins for one person with two plates and a mug.",
            avoid=("broken", "not draining", "smells", "wont", "won't", "salt", "rinse aid",
                   "tablet", "tablets", "buy", "buying", "worth it", "how do i", "clean",
                   # The running-cost card has the figures (5 to 10p against 20 to 25p a
                   # cycle), so a line that asks which is cheaper keeps it.
                   "cheaper", "cost to run", "running cost", "run a dishwasher", "how much",
                   "electricity", "gas", "kwh")),
    _either("tumble-dryer-or-airer",
            ("tumble dryer", "tumble dryers", "dryer", "tumble"),
            ("airer", "airers", "clothes rack", "washing line", "line", "radiator"),
            "Airer for anything with time to dry, which is most washing: it is free and it is "
            "kinder to the clothes. A dryer earns its place with no outdoor space, a family's "
            "washing, or something needed dry within the hour.",
            avoid=("broken", "not heating", "wont", "won't", "smells", "buy", "buying",
                   "worth it", "cost", "costs", "electricity", "condensation", "mould")),
    _either("led-or-halogen",
            ("led", "leds", "led bulb", "led bulbs"),
            ("halogen", "halogens", "halogen bulb", "halogen bulbs", "incandescent"),
            "LED, without a doubt: the same light for about a tenth of the electricity, and it "
            "lasts years rather than months. A halogen only earns its place where you want full "
            "heat instantly, like a bathroom mirror or a work lamp.",
            avoid=("headlight", "headlights", "car", "van", "dim", "dimmable", "warm white",
                   "cool white", "kelvin", "lumens", "watts", "watt", "how many")),
    _either("regular-or-premium-petrol",
            ("regular", "regular petrol", "unleaded", "95"),
            ("premium", "premium petrol", "super unleaded", "superunleaded", "98", "99"),
            "The regular grade, unless the handbook says otherwise: premium only helps an "
            "engine built and mapped for high octane. It will not clean anything and it will "
            "not give you more miles for the money.",
            avoid=("diesel", "electric", "car", "which car", "price", "prices", "cost", "per "
                   "litre", "how much")),
    _either("real-or-fake-tree",
            ("real tree", "real christmas tree", "a real one", "real"),
            ("fake tree", "fake christmas tree", "fake one", "artificial", "plastic tree",
             "fake"),
            _a_christmas_tree,
            # "faking" is a loose form of this row's own key ("fake"), so it cannot be in the
            # fence: it matched every line that says "fake" and fenced the row out of its own
            # question. A bare "real ... fake" is also most of the rest of the language, so the
            # reply asks for the tree in the line instead.
            avoid=("apple tree", "fruit tree", "garden", "plant a", "fir", "needles", "recycle",
                   "council", "cost", "costs", "price", "fake tan", "fake news",
                   "fake grass", "fake plants")),
    _either("laminate-or-wood-flooring",
            ("laminate", "laminate flooring"),
            ("real wood", "hardwood", "solid wood", "engineered wood", "wood flooring", "oak",
             "wood"),
            "Laminate for a budget and a busy house, real wood for a room you will keep: "
            "laminate shrugs off kids, dogs and a mop but cannot be sanded back when it wears, "
            "and engineered wood sits between the two at about twice the price of laminate.",
            avoid=("worktop", "counter", "table", "chair", "paint", "varnish", "how to clean",
                   "clean", "fit", "fitting", "underlay", "bathroom", "wet room")),
    _either("push-or-electric-mower",
            ("push mower", "push mowers", "manual mower", "roller mower"),
            ("electric mower", "electric mowers", "petrol mower", "petrol mowers", "ride on",
             "electric"),
            "Electric for a normal suburban lawn: lighter, quieter and it starts first time, "
            "with a cable to mind or a battery to charge. A push mower only suits a postage "
            "stamp, and petrol is for a big rough patch.",
            avoid=("robot", "lawn", "how often", "when to", "cut", "cutting", "height")),
    _either("netflix-or-prime",
            ("netflix", "netflix or prime"),
            ("prime", "amazon prime", "prime video"),
            "Prime if you shop on Amazon anyway, because the delivery is most of what you are "
            "paying for; Netflix for the bigger back catalogue of series. Better still: check "
            "which one has the two or three shows you actually want this month, and swap.",
            avoid=("delivery", "parcel", "refund", "price", "cost", "how much", "free trial",
                   "cancel", "account", "password", "worth it")),
    _either("pram-or-carrier",
            ("pram", "prams", "pushchair", "buggy", "stroller"),
            ("carrier", "carriers", "sling", "baby carrier", "baby sling"),
            "Both, if the budget runs to it: a pram for the first year and long days out, a "
            "carrier for the bus, the stairs and the fourth trimester. If it must be one, the "
            "pram that folds small wins, and a sling is £40 later.",
            avoid=("which pram", "best pram", "buy", "buying", "cost", "price", "how much",
                   "newborn", "twins", "car seat")),
    _either("cream-or-milk-in-coffee",
            ("cream", "single cream", "double cream"),
            ("milk", "semi skimmed", "whole milk", "skimmed"),
            "Milk for everyday: cream flattens the taste of the coffee and cools it. If you "
            "want it richer without the fat, hot milk is the third answer - it tastes sweeter "
            "than cold and does not thin the coffee.",
            avoid=("how much", "price", "cost", "ice cream", "scone", "strawberries", "cake",
                   "freeze", "whip", "sour", "out of date", "gone off")),
    _either("milk-or-dark-chocolate",
            ("milk chocolate", "milk choc", "milk"),
            ("dark chocolate", "dark choc", "70%", "85%"),
            "Dark, if it is one square after dinner: more cocoa, less sugar, so a little is "
            "enough. Milk chocolate is the better bar for a long afternoon, and the better one "
            "for children.",
            avoid=("how much", "calories", "bad for", "dogs", "dog", "cat", "caffeine",
                   "price", "cost", "melt", "water", "hydration", "protein", "calcium",
                   "intolerance", "allergy", "breastfeeding", "toddler", "baby")),
    _either("ketchup-or-brown-sauce",
            ("ketchup", "tomato ketchup"),
            ("brown sauce", "hp sauce", "brown"),
            "Ketchup with chips and eggs, brown sauce with bacon and a sausage sandwich: brown "
            "is vinegar and spice, ketchup is sweet tomato. Neither belongs on a steak, and a "
            "fridge has room for both.",
            avoid=("make", "recipe", "homemade", "how do i make", "stain", "out of date",
                   "calories", "sugar", "price", "cost", "brand", "heinz")),
    _either("microwave-or-oven",
            ("microwave", "microwaves"),
            ("oven", "fan oven", "the oven"),
            "Microwave for reheating, defrosting, porridge, peas and a mug of milk; the oven "
            "for anything you want crisp or browned. For one plate the microwave is quicker, "
            "and for a family dinner the oven is the one that works.",
            avoid=("broken", "not heating", "wont", "won't", "how do i clean", "clean", "smells",
                   "buy", "buying", "worth it", "replace", "repair", "sparks", "shelf")),
    _either("dishwasher-tablets-or-powder",
            ("dishwasher tablet", "dishwasher tablets", "tablets", "capsules"),
            ("dishwasher powder", "powder"),
            "Tablets, mostly: they are dosed for you and nothing gets forgotten. Powder earns "
            "its place in very hard water or when a greasy load needs a little extra, and with "
            "either, the salt is the part people forget.",
            avoid=("washing", "laundry", "clothes", "detergent", "liquid", "gel", "baby",
                   "paracetamol", "ibuprofen", "medicine", "contraceptive", "vitamin",
                   "supplement", "iron", "sleeping")),
    # --- the pairs an everyday week asks about -------------------------------------------
    # Commuting, babies, the medicine cabinet, the garden, clothes, breakfast, a cold bed, a
    # damp flat, a hot night, a hob, tonight's chicken, the skirting board, the lawn, a wall, a
    # walk, the coffee. On main each of these was answered by a coin flip ("Disposable. I
    # wouldn't spend another minute on it - both work."), a pharmacist handoff, or a card about
    # something else entirely (the gas hob priced a question about an induction one).
    _either("bus-or-train-for-a-commute",
            ("bus", "buses"),
            ("train", "trains"),
            "Train if the line is direct and runs at the hours you work: it does not sit in "
            "traffic, and a season ticket pays for itself over five days a week. Take the bus "
            "when the route is one or two changes at most - a bus that goes where you are "
            "going beats a train that leaves you a mile away.",
            avoid=("delayed", "cancelled", "canceled", "missed", "refund", "compensation",
                   "how do i", "timetable", "app", "pass", "school", "kids", "ticket")),
    _either("cloth-nappies-or-disposable",
            ("cloth nappies", "cloth nappy", "reusable nappies", "reusable nappy",
             "washable nappies", "washable nappy"),
            ("disposable nappies", "disposable nappy", "disposables", "disposable"),
            "Both, to be honest: disposables for the first month, for nights and for travelling, "
            "and cloth for the days you are home. Cloth costs a few hundred pounds over two "
            "years against well over a thousand for disposables, but it is a wash every two "
            "days plus the drying, and the drying is what people give up on.",
            avoid=("rash", "how do i wash", "stain", "stains", "leak", "leaking", "newborn",
                   "which size", "size", "nappy bin", "smell")),
    _either("own-brand-or-branded-paracetamol",
            ("own brand", "own-brand", "supermarket", "cheap paracetamol", "store brand"),
            ("branded", "brand name", "panadol", "calpol", "brand"),
            "The own-brand box: paracetamol is a licensed medicine with the same 500mg in every "
            "box, and the supermarket one costs a fraction of the branded pack. What matters is "
            "the dose - two 500mg tablets, four hours apart, eight in a day at most - and never "
            "two products with paracetamol in them at the same time.",
            avoid=("child", "baby", "infant", "pregnant", "pregnancy", "overdose", "too much",
                   "how many", "alcohol", "codeine", "co-codamol", "ibuprofen", "antibiotic",
                   "how do i", "buy", "where can i")),
    _either("hedge-trimmer-or-shears",
            ("hedge trimmer", "hedge trimmers", "electric hedge trimmer", "trimmer"),
            ("shears", "hand shears", "hedge shears", "secateurs"),
            "Shears for a hedge you can reach across: a box or a short run of privet is quicker "
            "with a sharp pair than with a cable to drag out. A trimmer once the hedge is longer "
            "than a few metres or taller than you - about 40 to 70 pounds - because it cuts a "
            "straight line that a pair of shears cannot do by eye.",
            avoid=("beard", "nose", "hair", "strimmer", "lawn", "grass", "petrol", "battery",
                   "best", "how do i", "blade", "sharp")),
    _either("a-coat-or-a-jacket-for-spring",
            ("coat", "coats"),
            ("jacket", "jackets"),
            "A jacket, unless you feel the cold: a light waterproof shell over a jumper handles "
            "a British spring and packs into a bag when the afternoon warms up. A coat earns "
            "its place on a cold, windy morning, which is what most April mornings are.",
            # "coating" is a loose form of this row's own key ("coat"), so it cannot be in the
            # fence: it matched "coating" against "coat" and fenced the row out of its own
            # question.
            avoid=("how do i clean", "wash", "washing", "size", "fit", "paint",
                   "coat of paint", "coats of", "second coat", "top coat", "undercoat",
                   "non-stick", "nonstick", "jacket potato", "jacket potatoes", "suit",
                   "dress code", "lab")),
    _either("sourdough-or-wholemeal-bread",
            ("sourdough",),
            ("wholemeal bread", "wholemeal", "wholegrain bread", "wholegrain"),
            "Wholemeal for the fibre and the everyday sandwich: two slices give about 6g, a "
            "fifth of what most people get in a day. Sourdough is the better loaf for toast and "
            "for anyone who finds shop bread sits heavy - the long rise does some of the work - "
            "but a white sourdough is still white bread.",
            avoid=("starter", "recipe", "bake", "baking", "how do i make", "rise", "keeping",
                   "freeze", "brown or white", "white or brown")),
    _either("hot-water-bottle-or-electric-blanket",
            ("hot water bottle", "hot water bottles"),
            ("electric blanket", "electric blankets", "heated blanket", "heated blankets"),
            "Hot water bottle for a bad back or for ten minutes before you get in: pennies to "
            "run, and it is what a pharmacist suggests for cramp. An electric blanket is the "
            "better buy for a cold bedroom every night - 1p to 3p an hour on low - as long as "
            "the one you have is under ten years old and you never use it with a hot water "
            "bottle in the same bed.",
            avoid=("baby", "child", "pregnant", "pregnancy", "how do i wash", "wash", "cover",
                   "leaking", "burst", "fire", "safety")),
    _either("a-dehumidifier-or-the-windows-open",
            ("dehumidifier", "dehumidifiers"),
            ("open the windows", "opening the windows", "open windows", "open a window",
             "windows open"),
            "Windows open for ten minutes in the morning whatever the weather: that swaps damp "
            "air for dry and costs nothing. A dehumidifier is for a flat that is still damp "
            "after that - about 1p an hour for a small one - and it is the answer to a wet "
            "window every morning and a musty room you dry washing in.",
            avoid=("broken", "not working", "leaking", "how do i clean", "filter", "buy",
                   "buying", "worth it", "size", "litre")),
    _either("a-fan-or-air-conditioning",
            ("fan", "fans"),
            ("air conditioner", "air conditioning", "air con", "aircon", "portable air con"),
            "A fan, for a British summer: it moves the air for a few pence an hour, and on the "
            "two or three nights that are unbearable it is enough to sleep. An air conditioner "
            "only earns several hundred pounds if you cannot sleep for weeks of heat - it uses "
            "as much electricity as a fridge and has to be vented out of a window.",
            avoid=("broken", "noisy", "not working", "how do i clean", "extractor", "bathroom",
                   "oven", "laptop", "computer", "pc", "engine", "car", "ceiling", "install",
                   "wiring")),
    _either("an-induction-hob-or-a-ceramic-one",
            ("induction hob", "induction hobs", "induction"),
            ("ceramic hob", "ceramic hobs", "ceramic top", "ceramic"),
            "Induction: it heats the pan rather than the ring, so a pan of water boils in about "
            "half the time and the surface is cool enough to wipe while you cook. Ceramic is "
            "cheaper to buy and takes any pan, but it stays hot for minutes after you turn it "
            "off and every pan has to sit flat on it.",
            avoid=("gas", "how do i clean", "scratch", "scratches", "cracked", "not working",
                   "wok", "pan set", "compatible")),
    _either("fresh-chicken-or-frozen",
            ("fresh chicken", "fresh chicken breast", "chilled chicken"),
            ("frozen chicken", "frozen chicken breast", "frozen chicken breasts",
             "frozen chicken thighs"),
            "Frozen, for the freezer and the budget: it is frozen within hours of being packed, "
            "so it is at least as good as a fresh pack that has spent days in a chiller, and it "
            "often costs half as much. Buy fresh for tonight and never refreeze it once thawed.",
            avoid=("how long", "defrost", "thaw", "safe", "food poisoning", "left out", "smell",
                   "gone off", "raw", "still pink", "rubber")),
    _either("matt-or-gloss-on-the-skirting",
            ("matt paint", "matt emulsion", "matt finish", "matt"),
            ("gloss paint", "gloss finish", "gloss"),
            "Eggshell or a water-based gloss on skirting, matt on the walls: matt marks and "
            "cannot be wiped, which is exactly what a skirting board gets from a hoover and a "
            "shoe. A water-based gloss also yellows far less than the old oil-based one.",
            avoid=("how do i paint", "sand", "sandpaper", "undercoat", "primer", "wall",
                   "walls", "ceiling", "dry", "drying", "brush", "roller", "how many coats")),
    _either("lawn-seed-or-turf",
            ("lawn seed", "grass seed", "seed"),
            ("turf", "turf rolls", "rolls of turf", "ready-made lawn"),
            "Seed for anything bigger than a small patch: it costs a fraction of turf, about a "
            "fifth of the price a square metre, and you can pick a mix for your soil and the "
            "shade. Turf earns it only when you need a lawn you can walk on within weeks, like a "
            "garden for a wedding, or on a slope seed would wash off.",
            avoid=("how long", "water", "watering", "when to", "best time", "bird", "birds",
                   "feed", "weed", "moss")),
    _either("a-roller-or-a-brush",
            ("roller", "rollers", "paint roller"),
            ("brush", "brushes", "paint brush"),
            "Both, with the roller doing the field: a 9-inch roller on a pole covers a wall in a "
            "fraction of the time, and the brush is for the edges, the corners and the strip "
            "above the skirting. A synthetic brush for water-based paint, a natural one for oil.",
            avoid=("how do i clean", "cleaning", "wash out", "hairy", "bristles", "makeup",
                   "hair", "toilet", "decorating", "paint the ceiling")),
    _either("walking-boots-or-trail-shoes",
            ("walking boots", "hiking boots", "walking boot", "hiking boot"),
            ("trail shoes", "trail running shoes", "fell shoes", "trainers"),
            "Boots for the hills and anything with mud, rock or a descent: the ankle support and "
            "the stiff sole are what stop a twist. Trail shoes for a fast, dry walk on a track, "
            "or a trip where you want one pair that also passes in a pub - they dry quicker and "
            "weigh about half as much.",
            avoid=("how do i clean", "size", "fit", "wide", "blister", "blisters", "school",
                   "work", "steel toe", "leather", "waterproofing")),
    _either("instant-coffee-or-ground",
            ("instant coffee", "instant coffees"),
            ("ground coffee", "ground beans", "coffee beans"),
            "Ground for the taste and instant for the morning you cannot be bothered: fresh "
            "ground coffee is a different drink - the oils that make the smell are gone from a "
            "jar - and a 20-pound cafetiere with a bag of ground coffee beats most instant. Keep "
            "the jar for camping and an office kitchen.",
            avoid=("caffeine", "decaf", "how much", "pregnant", "pregnancy", "stain", "stains",
                   "machine", "how do i make", "best", "which brand")),
    # --- the pairs that name a way of doing it rather than two products -------------------
    # "should i use butter or margarine in a cake" was answered with the shortbread recipe, "is
    # it cheaper to make bread than buy it" with the price of the flour and no verdict, and
    # "should i book the flight now or wait" with "Not mine to decide, sorry". A person weighing
    # two ways of doing a job wants the verdict, and the one thing that decides it.
    _either("butter-or-margarine-in-a-cake",
            ("butter", "butters", "real butter"),
            ("margarine", "margarines", "soft spread", "low fat spread", "baking spread"),
            "Butter, when the recipe says butter: it creams, it holds the air a sponge needs and "
            "it tastes of something, and a spread has more water in it, so the cake rises less "
            "and tastes flat. Margarine is fine in a plain traybake or a crumble topping, and it "
            "is the wrong thing for shortbread, pastry or anything that has to set hard as it "
            "cools.",
            avoid=("how much", "how long", "how do i", "recipe", "toast", "bread", "sandwich",
                   "salted", "unsalted", "substitute", "instead of butter", "gone off", "rancid",
                   "flour", "icing", "frosting", "vegan", "lactose", "dairy free", "calories",
                   # Which of the two a body is better off eating is the nutrition answer, not
                   # the baking one: "is butter or margarine better for you" got a sponge
                   # instruction, because the health words never say "calories".
                   "healthier", "healthy", "unhealthy", "better for you", "bad for you", "good for you",
                   "good for me", "bad for me", "cholesterol", "saturated", "unsaturated",
                   "trans fat", "diet", "nutrition", "nutritious", "heart", "cut out", "cut down",
                   "cutting out", "lose weight", "weight", "eat", "eating", "in my diet")),
    _either("make-bread-or-buy-it",
            ("make bread", "make my own bread", "bake bread", "bake my own bread",
             "homemade bread", "making bread", "baking bread", "baking my own"),
            ("buy bread", "buying bread", "bought bread", "shop bread", "buy it", "from the shop",
             "from a shop", "supermarket bread"),
            "Cheaper to make if you bake more than a loaf a week: flour, yeast and salt come to "
            "about 55p for a large loaf against £1.20 to £2.50 in a shop, but the oven costs 30 "
            "to 40p a bake and a bag of flour goes stale, so the saving is only real if the bread "
            "gets eaten. Make it for the taste and the smell; treat the money as a bonus.",
            avoid=("how do i", "recipe", "sourdough starter", "went wrong", "not rising",
                   "dough", "knead", "yeast", "flour", "gluten", "machine", "bread maker",
                   "breadmaker")),
    _either("book-now-or-wait",
            ("book now", "book it now", "book the flight", "book flights", "book the flights",
             "book the ticket", "book the train", "book the hotel", "booking now"),
            ("wait", "waiting", "hold off", "book later", "leave booking", "leave it"),
            "Book now if the trip is within about six weeks or the dates cannot move: short-haul "
            "fares are lowest six to eight weeks out, and the cheap seats are gone after that. "
            "Wait if it is more than three months away and the dates can move - long-haul is "
            "cheapest two to four months ahead - and Tuesday and Wednesday flights cost less "
            "than Friday ones.",
            avoid=("how do i", "refund", "cancel", "cancelled", "missed", "check in",
                   "baggage", "luggage", "passport", "visa", "airport", "hotel is", "booking com")),
]
