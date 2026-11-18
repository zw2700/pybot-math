"""Odours in clothes: the smoke a coat holds, a smell a garment has picked up, and gym kit.

Three everyday questions, and none of them had its own answer:

  how do i get smoke smell out of a coat     the room: "Air the room hard, wash the soft things
                                             (curtains, cushions, throws)"
  how do i get the smell out of my coat      "I'm not sure about that one, sorry"
  my jacket smells of bonfire                "Thanks for telling me - I'm here if you want to dig
                                             into any of that."
  how do i get smoke out of a wool coat      nothing
  my gym kit smells even after washing       "Buy one adjustable dumbbell or one kettlebell ..."
  how do i get sweat smell out of gym clothes the biology of nervous sweat, and no fix

The smoke card is about a room - open the windows, wash the curtains - so a coat that came back
from a bonfire gets told to air the house. The gym kit line reached a strength-training answer
because "kit" is what a home gym is called in Britain.

Each row names the garment and the smell that is in it, so the room, the washing machine, the shoes,
the towels and the fridge keep the cards they already answer well.
"""

import re

from .lookup import a_food_is_being_kept, entry, only_a_container

ANSWERS = ("home-and-diy", "shopping", "fitness")

# A garment a smell can be in. "coat" and "jacket" are the two people write about, and a suit or a
# dress goes to the dry cleaner rather than the washing machine.
GARMENT = ("coat", "coats", "jacket", "jackets", "jumper", "jumpers", "cardigan", "fleece",
           "hoodie", "blazer", "suit", "suits", "dress", "dresses", "shirt", "shirts", "trousers",
           "skirt", "scarf", "clothes", "clothing", "wardrobe", "outfit", "uniform", "costume",
           "gloves", "hat", "beanie", "bag", "backpack", "rucksack", "handbag", "luggage",
           "suitcase", "sleeping bag", "tent",
           # The trousers of most of the world, and the two things people sleep and work in:
           # "my jeans smell", "how do i get the smell out of my jeans", "my tshirt smells" and
           # "my pyjamas smell" were each a shrug or a receipt, and "my jeans smell of smoke" was
           # told to air the room and wash the curtains - the same wrong answer this file was
           # written to stop for a coat. Denim is not in every other garment list for free,
           # because a jean question is usually about the fit or the wash, not a smell.
           "jeans", "jean", "denim", "tshirt", "t shirt", "teeshirt", "tee shirt", "t-shirts",
           "t shirts", "joggers", "sweatpants", "trackies", "track suit", "tracksuit",
           "pyjamas", "pajamas", "pj s", "pjs", "nightie", "nightdress", "dressing gown",
           "bathrobe", "robe", "slippers", "socks", "sock", "tights", "stockings", "bra",
           "bras", "underwear", "boxers", "knickers", "pants", "apron", "overalls", "scrubs",
           "tabard")

# The smells a garment holds. "smoke" is the one people ask about most, by a long way.
SMELL = ("smell", "smells", "smelly", "smelling", "stink", "stinks", "stinking", "stunk", "odour",
         "odor", "reek", "reeking", "whiff", "musty", "must", "damp", "fusty", "sweat", "BO",
         "smoke", "smoky", "bonfire", "campfire", "fire", "cigarette", "cigarettes", "smoking",
         "tobacco", "nicotine", "vape", "curry", "cooking", "garlic", "perfume", "aftershave",
         "vinegar", "bleach", "petrol", "diesel", "paint", "chemical", "mildew", "mouldy")

# A room, a soft furnishing, an appliance or a car is another card's question: the room smoke card,
# the washing machine service wash, the fridge, the bin.
NOT_A_GARMENT = ("room", "rooms", "house", "home", "flat", "kitchen", "bedroom", "living room",
                 "hall", "hallway", "car", "van", "sofa", "settee", "couch", "curtain", "curtains",
                 "carpet", "rug", "rugs", "mattress", "bed", "bedding", "duvet", "pillow",
                 "pillows", "sheet", "sheets", "towel", "towels", "washing machine", "washer",
                 "dishwasher", "fridge", "freezer", "bin", "bins", "wheelie", "oven", "microwave",
                 "kettle", "drain", "sink", "toilet", "shower", "walls", "wall", "ceiling",
                 "paint", "furniture", "chair", "chairs", "table", "wardrobe", "wardrobe door",
                 # A wardrobe is furniture you cannot air outside or wash: "my wardrobe smells
                 # musty" wants the damp card in cleaning.py, not a garment card (broad-door,
                 # #4965). "wardrobe door" stays beside it for the line that names the door.
                 "drawer", "cupboard", "books", "book", "microwave oven", "car seats", "hands",
                 "breath", "mouth", "feet", "shoes", "shoe", "trainers", "boots", "socks",
                 "wellies", "helmet", "washing-up", "dishcloth", "cloth", "sponge", "bin bag")

# Getting a smell out of a garment is what these rows do; putting a smell on one is a different
# question (fabric conditioner, a scent, a spray).
ASK = ("get rid of", "get out", "get the smell", "remove", "removing", "take away", "stop the "
       "smell", "smells of", "smells like", "smelling of", "stinks of", "stinks like",
       "how do i clean", "how do i wash", "how do i freshen", "freshen up", "air out", "air it",
       "how do i make it smell better", "how do i get it to stop smelling")

# A potato is not a garment. "jacket" is one of the garment words above and "cooking" is one of
# the smells below, so "how long should i cook a jacket potato" matched this table twice over and
# was told to air itself outside for a day and wash it at 30C. The two words being neighbours is
# what tells the one from the other: a jacket potato is a different thing from a jacket, and no
# word of a line can say that on its own. A list of dish words in `avoid` cannot either, because
# one word of a phrase in `avoid` is enough by itself, and "my coat smells of roast dinner",
# "my jumper smells of boiled eggs" and "my shirt smells of boiled milk" are all still a coat, a
# jumper and a shirt. So the test is adjacency, and it is a `guard` rather than a key word.
_GARMENT_THEN_FOOD = re.compile(
    r"\b(?:" + "|".join(GARMENT) + r")\s+(?:potato|potatoes|baked potato|jacket potato)\b")


# The words that say a thing smells, as against the things a smell can be of. Both sit in one key
# above, and only the first kind is a smell question: "how do i get curry out of a white shirt" and
# "bleach on my white shirt" are a stain and a bleach job, and both were told to air the garment
# outside for a day because "curry" and "bleach" are in the list as things a coat can smell of. A
# line that says neither "smells" nor "stinks" nor "whiff" anywhere, and asks to get something out
# rather than a smell, is about the thing, not about the smell.
SMELL_SAID = ("smell", "smells", "smelly", "smelling", "smelled", "stink", "stinks", "stinking",
              "stunk", "odour", "odor", "reek", "reeks", "reeking", "reeked", "whiff", "whiffs",
              "musty", "must", "damp", "fusty", "sweat", "sweaty", "bo", "smoky", "mildew",
              "mouldy", "moldy", "stale", "fumes", "fumey", "scented")
_ODOUR_SOURCE = ("curry", "cooking", "garlic", "perfume", "aftershave", "vinegar", "bleach",
                 "petrol", "diesel", "paint", "chemical", "fire", "smoke")


def _a_source_is_not_a_smell(understood):
    """Whether a line with a garment and a smell source in it is really about the smell.

    A food, a bleach or a fire in the line is a smell question only when the line says the thing
    smells: "my coat smells of curry" is, "how do i get curry out of my white shirt" is a stain. A
    line with no source word at all is left alone, because "how do i stop my coat smelling" names
    nothing but the smell.
    """
    words = [str(one).lower() for one in ((understood or {}).get("words") or ())]
    text = " ".join(words)
    if not any(source in text for source in _ODOUR_SOURCE):
        return True
    return any(named in text for named in SMELL_SAID)


def _a_garment_is_not_a_food(understood):
    """Whether a line with a garment word and a smell word in it is about a garment at all.

    A garment word straight in front of a food word names the food: "jacket potato", "jacket
    potatoes". Anything else - "my jacket smells of cooking", "my coat smells of roast dinner" -
    is still the garment, however many kitchen words it carries.

    A bag is where the shopping is, so a line about a food going mouldy or stale in one is the
    food's question: "why does bread go mouldy faster in a bag" was told to air itself outside
    for a day and wash at 30C. That is the only garment word in such a line, which is what
    `only_a_container` checks; "my gym bag smells musty" has no food in it and keeps its answer.
    """
    words = (understood or {}).get("words") or ()
    text = " ".join(str(one) for one in words).lower()
    if _GARMENT_THEN_FOOD.search(text):
        return False
    if a_food_is_being_kept(understood) and only_a_container(understood, GARMENT):
        return False
    return True


ENTRIES = [
# Smoke in a garment: air first, then wash, and nothing is rubbed or sprayed.
entry("smoke-in-clothes",
      (GARMENT + ("hood", "collar", "sleeves", "lining", "wool", "woollen", "dry clean only"),
       ("smoke", "smoky", "bonfire", "campfire", "woodsmoke", "wood smoke", "cigarette",
        "cigarettes", "cigarette smoke", "fag smoke", "smoking", "tobacco", "nicotine", "vape",
        "vaping", "fire", "fire pit", "chiminea", "bbq", "barbecue", "pub", "stale")),
      "Air it before you wash it: hang it outside, or in a room with a window open, for a day, "
      "because most of the smell sits on the surface and blows off. Then wash it at whatever the "
      "label allows - 30C for a washable coat, 40C for a jumper - with half the usual detergent "
      "and no softener. If it cannot be washed, hang it in a steamy bathroom for twenty minutes and "
      "air it again, or put it in a bag with a saucer of bicarbonate of soda overnight. Don't spray "
      "perfume on it; that makes smoke plus scent, and it clings harder.",
      bias=4,
      ask=SMELL,
      avoid=NOT_A_GARMENT + ("stain", "stains", "stained", "staining", "marked", "yellowed",
                             "fire alarm", "smoke alarm", "fireplace", "chimney", "wood burner",
                             "smoking meat", "smoker", "how do i stop smoking", "quit smoking",
                             "give up smoking", "smoke point", "burnt", "burning")),

# Sweat in gym kit: the fix is cool water, no softener, air drying, and washing it out of the bag.
entry("gym-kit-smell",
      (("gym kit", "gym clothes", "gym gear", "workout clothes", "workout gear", "sports kit",
        "running kit", "running clothes", "running gear", "training kit", "cycling kit",
        "gym top", "sports bra", "leggings", "base layer", "lycra", "sports clothes",
        "exercise clothes", "kit",
        # People name the piece, not the outfit: "my gym shorts smell" and "my running tops
        # smell sour" are the same question as "my gym kit smells", and a plastic-heavy
        # garment is exactly what this answer is about. The phrases hold a garment word of
        # their own where they can: a bare "tops" is read by the matcher as the start of "top",
        # so "top of the stairs smells damp" and "my white top smells of sweat" became this
        # card, and both belong to their own answers (@green-thimble, #6045). A swimming
        # costume stays with the swimwear row, which has the chlorine rinse.
        "shorts", "gym shorts", "running shorts", "cycling shorts", "gym tops", "running tops",
        "gym top", "running top", "vest", "jersey", "sports socks", "running socks"),
       ("smell", "smells", "smelly", "smelling", "stink", "stinks", "stinking", "sweat", "sweaty",
        "odour", "odor", "musty", "damp", "fusty", "washing", "washed", "wash", "clean",
        "bacteria", "after washing", "even after washing")),
      "Wash kit cool - 30C is enough - with a scoop of bicarbonate of soda or a sports wash, no "
      "fabric softener at all, and air dry it. The smell is bacteria in the synthetic fibres, not "
      "in the sweat: sweat itself has no smell, and a warm wash with softener leaves a film the "
      "bacteria live in, which is why kit can smell the moment it gets damp again. Get it out of "
      "the gym bag the same day and hang it to dry before it goes in the basket.",
      bias=4,
      ask=SMELL,
      # a strength plan, a workout to start with, and why sweat happens are other cards
      avoid=NOT_A_GARMENT + ("dumbbell", "dumbbells", "kettlebell", "weights", "barbell",
                             "routine", "programme", "program", "plan", "workout plan", "to buy",
                             "buy", "which shoes", "trainers to buy", "body odour", "deodorant",
                             "antiperspirant", "hyperhidrosis", "chafing", "blister",
                             "runners knee", "injury",
                             # a swimming costume smells of the pool, not of sweat: the fix is a
                             # rinse in cold water straight after, and the chlorine row has it
                             "chlorine", "pool", "swimming pool", "swim",
                             # "top of the stairs smells damp" is a room, and the plural key
                             # would otherwise read it as a garment (@green-thimble, #6045).
                             # A room, a wall and a ceiling are the damp answer's, not this card's
                             "stairs", "stair", "landing", "hall", "hallway", "landings",
                             "room", "rooms", "ceiling", "ceilings", "wall", "walls",
                             "loft", "lofts", "attic", "garage", "shed", "sheds",
                             "cupboard", "cupboards", "wardrobe", "wardrobes")),
      # "sweating" must not be here: the matcher reads sweat and sweating as one word, so listing it
      # stood down every "sweat smell" line. A why-do-i-sweat question names no kit and is already
      # out of this key on its own.

# A smell on a garment that is not smoke: whatever it is, the answer is the same, and the two ways
# a thing that cannot be washed gets freshened are what people do not know.
entry("smell-in-a-garment",
      (GARMENT,
       SMELL + ("washing", "washed", "dry clean", "dry cleaning", "freshen", "air it", "aired")),
      "Air it outside for a day first, then wash it if it can be washed - at the temperature on the "
      "label - with half the usual detergent and no softener, and dry it in the open air rather "
      "than on a radiator. "
      "Anything that cannot be washed - a wool coat, a blazer, a suit - goes in a steamy bathroom "
      "for twenty minutes, or in a bag with a saucer of bicarbonate of soda overnight, and then "
      "air. If it comes back after that, the smell is in what it is stored in, so wash the drawer "
      "or the wardrobe and let both dry out before the clothes go back.",
      bias=2,
      ask=SMELL,
      guard=lambda understood: (_a_garment_is_not_a_food(understood)
                                and _a_source_is_not_a_smell(understood)),
      # a stain is the stain card's question: "how do i get sweat stains out of a shirt" wants the
      # bicarbonate paste, not a wash guide. Sweat is the same: "my t shirt smells of sweat" has a
      # card of its own that soaks the garment in vinegar, and this generic air-and-wash answer is
      # the weaker one. A swimming costume smells of the pool, so it keeps the chlorine rinse.
      avoid=NOT_A_GARMENT + ("sweat", "sweaty", "sweat smell", "smells of sweat", "smell of sweat",
                             # mould in a garment is clothing.py's: it brushes the spores off
                             # outdoors and washes at the hottest the label allows, which is a
                             # better answer than "air it outside" for spots that are growing
                             "mould", "mouldy", "mold", "moldy", "mildew", "mildewy", "mildewed",
                             "spores", "black spots", "green spots",
                             "swimsuit", "swimming costume", "bikini", "wetsuit", "wetsuits",
                             "pool", "chlorine", "swimming", "swim",
                             "stain", "stains", "stained", "staining", "marks", "yellow marks",
                             "armpit", "armpits", "fabric softener", "conditioner", "scent",
                             "perfume to wear",
                             "which perfume", "smell nice", "make it smell nice", "air freshener",
                             "candle", "diffuser", "smoke", "smoky", "bonfire", "cigarette",
                             "gym kit", "gym clothes", "running kit",
                             # "a bag of <food>" is the shopping, not a garment: "what can i cook
                             # with a bag of potatoes" was told to air itself outside for a day,
                             # because the row keys "bag" and reads "cooking" as its ask. The
                             # consumer rows already read the phrase this way (@tidy-aspen).
                             "bag of", "bags of")),

# Why a washed thing still smells, which is the same key asked the other way: "why do my jeans
# smell", "why do my clothes smell after washing", "why does my coat smell" all wanted the
# mechanism and all got the air-it-outside card, which is the answer to what to do about it.
# A separate row rather than a rewrite, because the card above is what a follow-up quotes back
# and its first sentence has to stay the fix.
entry("smell-in-a-garment-why",
      (GARMENT,
       SMELL + ("washing", "washed", "dry clean", "dry cleaning", "freshen", "air it", "aired")),
      "It is bacteria eating what the wash leaves behind - sweat, body oil and skin cells - and "
      "they are not all removed by a cool quick wash, which is why a garment can smell the moment "
      "it warms up again. Synthetics hold it worst: polyester and elastane are oil-loving, so the "
      "film of body oil stays on the fibre, while cotton and linen let it go. Softener and too "
      "much detergent make it worse by leaving their own coating for the bacteria to sit in. So "
      "wash at the hottest the label allows with the amount of powder for a dirty load, skip the "
      "softener, and dry it fast and in the open air; once the smell has set in a wash at 60 with "
      "half a cup of bicarbonate of soda usually shifts it.",
      bias=3,
      ask=("why", "how come", "what makes", "whats making", "what is making", "reason",
           "what causes", "what caused"),
      guard=lambda understood: (_a_garment_is_not_a_food(understood)
                                and _a_source_is_not_a_smell(understood)),
      avoid=NOT_A_GARMENT + ("sweat", "sweaty", "sweat smell", "smells of sweat",
                             "smell of sweat",
                             # a damp smell is water in the cloth or the room, not what the
                             # wash left in the fibre, and the damp card says where water hides
                             "damp", "damps", "musty", "mustiness", "damp smell", "smells damp",
                             "smell damp", "smells of damp", "smell of damp", "dank",
                             "mould", "mouldy", "mold", "moldy", "mildew", "mildewy", "mildewed",
                             "spores", "black spots", "green spots",
                             "swimsuit", "swimming costume", "bikini", "wetsuit", "wetsuits",
                             "pool", "chlorine", "swimming", "swim",
                             "stain", "stains", "stained", "staining", "marks", "yellow marks",
                             "armpit", "armpits", "fabric softener", "conditioner", "scent",
                             "perfume to wear",
                             "which perfume", "smell nice", "make it smell nice", "air freshener",
                             "candle", "diffuser", "smoke", "smoky", "bonfire", "cigarette",
                             "gym kit", "gym clothes", "running kit"),
      ),
]
