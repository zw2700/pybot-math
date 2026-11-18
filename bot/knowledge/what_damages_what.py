"""A thing put on another thing: bleach on a mattress, vinegar on granite.

The everyday question of this shape is "can i use <product> on <surface>", and the bot had no
row of that shape at all: every cleaning row asks what the *job* is ("how do i clean a mattress",
"how do i get a stain out of the sofa"), so a line that names a product and a surface skipped all
of them and landed on whatever row held one of the two words:

    can i use bleach on a mattress          -> how to bleach white cotton
    can i use vinegar on a phone screen     -> how much screen time for children
    can i use a metal scourer on a non stick pan -> why food tastes of metal
    can i use white vinegar on a granite worktop -> a search hedge

The rows here are keyed by the *pair*: the product in the first group, the surface in the second,
because "will this damage that" is the question and either word alone is something else. Each
answer says what happens and what to use instead, which is what the person wanted to know.
"""
import re

from .lookup import entry

# Every surface here is in the home, and that is the topic these rows answer as.
# A mattress and a duvet are the same word family and not the same answer: a mattress does not go
# in a machine at all, and a duvet cover does, so the reply reads which one the line names.
_MATTRESS = ("mattress", "mattresses", "memory foam", "foam", "mattress topper",
             "mattress protector", "mattress cover", "headboard", "bed base", "divan")


def _bleach_on_bedding(memory, understood):
    text = (understood.get("text") or "").lower()
    if _names(text, _MATTRESS):
        return ("No: the cover yellows and the foam keeps the smell of it, and bleach does not "
                "reach the sweat and the mites you are after. Vacuum both sides, dust it with "
                "bicarbonate of soda for an hour and vacuum again, and dab a stain with cool water "
                "and a little washing-up liquid. Air it with the bed stripped, and a washable "
                "protector saves the next one.")
    return ("Not neat bleach: the cotton weakens and goes yellow, and a synthetic duvet or pillow "
            "clogs and holds the smell of it. A white cotton cover takes a laundry bleach in a hot "
            "wash at the label's temperature; anything else wants detergent at 60 and a long dry. "
            "Pillows and duvets go in a big drum with a couple of towels to balance it.")



ANSWERS = ("home-and-diy",)

# The products people name by brand as often as by kind: vinegar comes as white vinegar, malt
# vinegar, a descaler or a bottle of lemon juice, and the question is the acid either way.
_ACID = ("vinegar", "white vinegar", "malt vinegar", "distilled vinegar", "lemon juice",
         "lemon", "citric acid", "descaler", "descaling", "limescale remover", "barkeeper",
         "bar keepers friend", "acid")
_STONE = ("granite", "granite worktop", "granite worktops", "granite counter", "granite top",
          "marble", "marble worktop", "marble worktops", "marble floor", "marble tiles",
          "limestone", "travertine", "onyx", "alabaster", "quartz", "quartz worktop",
          "quartz worktops", "stone worktop", "stone worktops", "stone floor", "stone floors",
          "slate worktop", "slate floor", "slate hearth", "stone counter", "stone counters")

# Bleach is the one cleaner people reach for on a stained mattress, and it is the wrong one: the
# cover yellows and the foam underneath holds the smell of it for weeks.
_BLEACH = ("bleach", "bleaching", "milton", "bleach spray", "domestos", "thin bleach",
           "household bleach", "mould spray", "mould remover")
_BEDDING = ("mattress", "mattresses", "memory foam", "foam mattress", "mattress topper",
            "mattress protector", "mattress cover", "pillow", "pillows", "duvet", "duvets",
            "bedding", "headboard")

# A screen is cleaned with a cloth and not with a bottle: the liquid runs into the edge and the
# alcohol or the vinegar takes the coating off, which is the mark people then blame on the cloth.
_WET = ("water", "spray", "sprays", "spraying", "wipes", "wipe", "wipes", "damp cloth",
        "glass cleaner", "windex", "window cleaner", "alcohol", "isopropyl", "vodka",
        "hand sanitiser", "hand sanitizer", "soap", "soapy water", "vinegar", "bleach")
_SCREEN = ("phone screen", "phone", "laptop screen", "laptop", "tv screen", "tv", "television",
           "monitor", "computer screen", "tablet", "tablet screen", "ipad", "iphone", "screen",
           "screens", "kindle", "e reader", "watch screen", "smartwatch", "touchscreen",
           "touch screen")

# A coated pan is not a steel one: the scourer takes the coating off in flakes and the pan is
# done, and the flakes are the reason people then say the food tastes of metal.
_ABRASIVE = ("scourer", "scourers", "metal scourer", "wire wool", "steel wool", "brillo",
             "abrasive", "abrasives", "sandpaper", "scrub", "scrubbing", "scrubber",
             "wire brush", "metal brush", "bleach", "oven cleaner", "sharp knife", "knife")
_COATED = ("non stick", "non-stick", "nonstick", "teflon", "tefal", "coated pan", "coated pans",
           "frying pan", "frying pans", "wok", "air fryer", "air fryer basket", "rice cooker",
           "rice cooker bowl", "baking tray", "baking trays", "griddle", "crepe pan",
           "pancake pan", "bread tin", "cake tin", "muffin tin")

# Liquid washing-up liquid in a machine lathers a kitchen floor's worth of foam out of the door
# and can reach the pump. The machine rows below it are about what goes *in* a dishwasher.
_HAND_LIQUID = ("washing up liquid", "washing-up liquid", "fairy liquid", "dish soap",
                "dishwashing liquid", "hand soap", "shower gel", "bubble bath", "shampoo",
                "body wash", "swarfega", "laundry liquid", "detergent", "soap")
# A dishwasher only: a washing machine question about what goes in it is a wash-care card, and
# this row's answer is about the hot dry cycle and the salt that a dishwasher has.
_MACHINE = ("dishwasher", "dish washers", "dishwasher tablets", "dishwasher tablet")
# The hand-liquid row is about both machines: a washing machine full of washing-up liquid foams
# out of the drawer exactly as a dishwasher foams out of the door.
_ANY_MACHINE = _MACHINE + ("washing machine", "washing machines", "washer", "tumble dryer",
                           "dryer")

# What a dishwasher ruins, said by name: the wood swells and splits, the carbon steel and the
# aluminium go grey and pitted, the crystal clouds and the gold rim comes off.
_NOT_WASHABLE = ("wooden spoon", "wooden spoons", "wooden spatula", "wooden spatulas",
                 "wooden board", "wooden chopping board", "chopping board", "wooden handle",
                 "wooden handles", "knife", "knives", "chefs knife", "chef's knife",
                 "kitchen knife", "carving knife", "bread knife", "aluminium", "aluminum",
                 "cast iron", "carbon steel", "copper", "crystal", "crystal glass",
                 "gold rim", "gold rimmed", "gold-rimmed", "fine china", "bone china",
                 "thermos", "vacuum flask", "garlic press", "cheese grater", "non stick",
                 "non-stick", "nonstick", "silver cutlery", "silver", "pewter")

# The "can i" frame: the line is asking whether the pair is safe rather than telling the bot it
# has already done it. A row here reads any line that names both words, because "i put bleach on
# the mattress" wants the same advice about the stain it has left.
_HOW_ASK = re.compile(
    r"\b(?:can|could|should|may|is it|is|are|will|would|safe|ok|okay|alright)\b", re.I)

# One answer per material, because the reason is different for each of them and a list of five
# reasons is not an answer to "can i put my knives in the dishwasher": the first thing named in
# the line is what the person has in their hand.
_WOOD = ("wood", "wooden", "bamboo", "teak", "board", "boards", "chopping board", "spoon",
         "spoons", "spatula", "spatulas", "utensil", "utensils", "handle", "handles", "mug tree",
         "bowl", "bowls", "rolling pin")
_KNIFE = ("knife", "knives", "blade", "blades", "chef's knife", "chefs knife", "carving knife",
          "bread knife", "kitchen knife", "steak knife", "steak knives")
_IRON = ("cast iron", "carbon steel", "skillet", "griddle pan", "seasoned pan")
_SOFT_METAL = ("aluminium", "aluminum", "copper", "silver", "silver cutlery", "pewter", "brass",
               "tin", "tinned", "cake tin", "muffin tin", "baking tray", "roasting tin")
_DELICATE = ("crystal", "crystal glass", "wine glass", "wine glasses", "decanter", "gold rim",
             "gold rimmed", "gold-rimmed", "china", "bone china", "fine china", "antique",
             "hand painted", "hand-painted", "printed glass")
# A thing with a space the water cannot drain out of is its own reason: it rusts, it smells, and
# the machine cannot dry it.
_TRAPPED = ("thermos", "vacuum flask", "flask", "garlic press", "cheese grater", "grater",
            "lemon squeezer", "squeezer", "pepper mill", "coffee grinder", "whisk",
            "colander", "potato ricer")
# Stone and marble stand the detergent and the heat badly: a mortar comes out dull and chalky.
_STONEWARE = ("marble", "mortar", "pestle", "mortar and pestle", "stoneware", "slate",
              "granite", "soapstone", "terracotta", "pizza stone", "baking stone",
              "pizza steel")

# The key of the row is the whole list: the reply reads the line to pick the reason, so a word
# that only reached the branches inside it left "can i put a lemon squeezer in the dishwasher" and
# "a marble mortar" as punts while the reply for both was already written.
_NOT_WASHABLE = _NOT_WASHABLE + _TRAPPED + _STONEWARE
_COATING = ("non stick", "non-stick", "nonstick", "teflon", "coated pan", "coated", "air fryer",
            "air fryer basket", "rice cooker", "bread maker", "bread machine")


def _names(text, words):
    return any(re.search(r"\b%s\b" % re.escape(word), text) for word in words)


# Stone is not one thing: a quartz worktop is resin and stands a splash, a marble one etches and
# never comes back, so leading with "acid dulls marble" on a quartz line is answering a question
# the person did not ask.
_HARD_STONE = ("quartz", "quartz worktop", "quartz worktops", "granite", "granite worktop",
               "granite worktops", "granite counter", "granite top", "slate", "slate worktop",
               "slate floor", "slate hearth")


def _acid_on_stone(memory, understood):
    text = " " + str((understood or {}).get("text") or "").lower() + " "
    if _names(text, ("descaler", "descaling", "limescale remover")):
        acid = "descaler"
    elif _names(text, ("lemon juice", "lemon")):
        acid = "lemon juice"
    else:
        acid = "vinegar"
    if _names(text, _HARD_STONE):
        return ("That one stands it: quartz and a sealed granite or slate surface take an acid "
                "splash — " + acid + " — so wipe it off rather than leave it standing. Marble, "
                "limestone, travertine and onyx are the ones that etch, and the dull patch they "
                "leave never comes back. Warm water and a drop of washing-up liquid is all any of "
                "them needs.")
    return ("That one etches: acid dulls a marble, limestone, travertine or onyx surface and the "
            "patch never comes back, so a wipe with " + acid + " is the wrong cleaner. Granite and "
            "quartz stand one now and then but do not need it. Warm water with a drop of "
            "washing-up liquid, dried off, and a pH-neutral stone cleaner for the rest.")


def _what_the_machine_ruins(memory, understood):
    """The reason the thing in the person's hand cannot go in the machine.

    The row answers every "can i put X in the dishwasher" line, and a reply that lists wood, steel
    aluminium and crystal answers none of them well. The line is read for the material it names
    and the reply is about that one, with the by-hand rule after it.
    """
    text = " " + str((understood or {}).get("clean")
                     or (understood or {}).get("text") or "").lower() + " "
    after = ("By hand in hot water, and dried straight away. Stainless steel, glass, plastic "
             "boards and everyday china are fine in the machine.")
    if _names(text, _IRON):
        return ("Not a seasoned pan: the wash strips the seasoning and the heat dries it to rust, "
                "so it comes out grey and sticks. Scrub it with hot water and a stiff brush while "
                "it is warm, dry it on the hob, and wipe a little oil over it. Stainless steel "
                "and glass are fine in the machine.")
    if _names(text, _WOOD):
        return ("Not a wooden one: it swells, splits along the grain and the glue in a board lets go, and "
                "a wooden handle soon feels rough. Wash it by hand in hot soapy water, stand it up "
                "to dry rather than flat, and rub food-safe oil into a board or a spoon now and "
                "then. Plastic boards are fine in the machine.")
    if _names(text, _KNIFE):
        return ("Not a knife: the edge knocks against the basket and the other cutlery, the "
                "handle can swell or lift, and the point comes out blunt. Wash it by hand in hot "
                "soapy water, dry it at once, and put it back in a block or on a magnetic strip. "
                "Stainless steel and everyday china are fine in the machine.")
    if _names(text, _SOFT_METAL):
        return ("Not bare aluminium or copper: the salt and the drying cycle leave it grey, "
                "pitted and chalky, and a tinned baking tray comes up patchy. By hand in hot "
                "soapy water is all it needs, and dry it at once. Stainless steel, glass and "
                "china are fine in the machine.")
    if _names(text, _TRAPPED):
        return ("Not that one: the water gets into a space it cannot drain out of, and it comes "
                "out rusty, chalky or sour, or with the soap still in it. Rinse it by hand in hot "
                "water and leave it to drain upside down. Plain crockery, stainless steel, glass "
                "and plastic boards are fine in the machine.")
    if _names(text, _STONEWARE):
        return ("Not stone: the detergent and the drying cycle take the surface off a marble "
                "mortar or a slate board and leave it dull and chalky, and a pizza stone soaks up "
                "water and can split in the oven next time. Rinse it in warm water and a stiff "
                "brush, no soap if you can, and dry it slowly. Plain crockery, stainless steel and "
                "glass are fine in the machine.")
    if _names(text, _DELICATE):
        return ("Not that: crystal clouds and can chip, a gold rim or a printed pattern comes off "
                "in the hot water, and anything with a trapped space holds water that rusts or "
                "smells. Wash it by hand in warm water with a drop of washing-up liquid and dry "
                "it with a cloth. Plain glass, stainless steel and everyday china are fine in the "
                "machine.")
    if _names(text, _COATING):
        return ("Not a coated one: the hot water and the detergent dull the coating and it starts "
                "to flake, and the same goes for an air fryer basket or a rice cooker bowl. Wash "
                "it with the soft side of a sponge and dry it before it goes back. Stainless "
                "steel, glass and china are fine in the machine.")
    return ("Look for the dishwasher-safe mark on the base or the handle first, and wash by hand "
            "anything without one: wood swells, thin metal and a sharp edge suffer, and china "
            "with a gold rim loses it. Stainless steel, glass and everyday china are fine in the "
            "machine.")


ENTRIES = [

    # -- acid on stone ------------------------------------------------------
    # Granite, marble, limestone, travertine and quartz are all sold as "stone worktops" and the
    # answer differs, so the reply names the ones it is about rather than saying "stone".
    entry("acid-on-stone",
          (_ACID, _STONE),
          _acid_on_stone,
          bias=3,
          # the standby list, the kettle, the shower and the stain rows are other questions, and
          # "how do i make a vinegar cleaner" is a recipe rather than a warning about stone
          avoid=("make", "makes", "recipe", "mix", "homemade", "kettle", "shower", "glass",
                 "mirror", "drain", "plughole", "grout", "toilet", "weeds", "weed", "kill",
                 "ant", "ants", "wasp", "stain", "stains", "stained", "remove", "removing")),

    # -- bleach on a mattress ---------------------------------------------
    # The white-cotton row answers "can i use bleach on X" for anything, because the bleach is the
    # subject and the cotton is the second word, and a mattress was told to soak it for ten
    # minutes in five litres. The bias is what settles the tie with that row.
    entry("bleach-on-a-mattress",
          (_BLEACH, _BEDDING),
          _bleach_on_bedding,
          bias=4,
          avoid=("cotton", "towels", "whites", "white shirt", "shirt", "school uniform",
                 "nappy", "nappies", "nursery", "bottle", "bathroom", "toilet", "grout",
                 "mould on the wall", "washing machine")),

    # -- bleach on wood ----------------------------------------------------
    # "can i use bleach on a wooden chopping board" got the white-cotton soak, and on a wooden
    # table the beeswax card, which never mentions the bleach. Wood is not a fabric and not a
    # surface you polish round the question.
    entry("bleach-on-wood",
          (_BLEACH, ("wood", "wooden", "chopping board", "chopping boards", "cutting board",
                     "cutting boards", "table", "tables", "oak", "pine", "floorboard",
                     "floorboards", "floor boards", "decking", "deck", "work bench", "workbench",
                     "shed", "fence", "door")),
          "No: household bleach takes the finish off and lifts the grain into a pale, furry patch, "
          "and a board keeps the smell of it. For a real mark, sand the patch and use an "
          "oxalic-acid wood bleach from a DIY shop, following the tin. For everyday care, hot "
          "water, a scrub of coarse salt, and standing it up to dry does more than bleach ever "
          "will.",
          bias=2,
          avoid=("stain", "stains", "mould", "mold", "white marks", "water marks", "ring",
                 "polish", "varnish", "oil it", "wax")),

    # -- bleach on a body --------------------------------------------------
    # The same shape with a person on the other side. "can i use bleach on a cut" came back with
    # the ten-minute soak for white towels, which is the one answer nobody should ever get here.
    entry("bleach-on-skin",
          # An injury word, not a skin word: "can i use bleach on my skin" is the first-aid card
          # for a splash on the skin, which is the right answer and was being taken off it.
          (_BLEACH, ("cut", "cuts", "wound", "wounds", "graze", "grazed", "broken skin",
                     "sore", "open cut", "open wound", "cut on my finger", "cut on my hand",
                     "burn", "blister")),
          "No, never on a cut or on broken skin: bleach burns the tissue, kills the new cells and "
          "leaves the cut slower to close. Rinse it under cool running water for five minutes, "
          "press a clean cloth on it for ten, then cover it. Wash splashes off skin with soap and "
          "water. A deep, dirty or gaping cut, or one that will not stop bleeding, wants 111 or a "
          "walk-in centre today.",
          bias=1,
          avoid=("white", "towels", "shirt", "cotton", "laundry", "wash", "toilet", "grout",
                 "wood", "floor", "mattress", "nappy", "nappies", "bottle", "bathroom")),

    # -- bleach on grout ---------------------------------------------------
    # The commonest bleach question there is, and both this branch and its base left it as a
    # search hedge while the answer is one line long.
    entry("bleach-on-grout",
          (_BLEACH, ("grout", "grouting", "tile grout", "tiles", "tile", "shower grout",
                     "bathroom grout", "kitchen grout")),
          "Yes on white cement grout: a cup of thin bleach in four litres of water, brushed on, "
          "left fifteen minutes and rinsed, kills the mould at the root. Never on coloured or "
          "epoxy grout, which it bleaches patchy, and never mixed with a limescale remover. A "
          "stiff brush and an old toothbrush do most of the work; a bicarbonate paste lifts the "
          "rest.",
          bias=2,
          avoid=("stain", "stains", "white marks", "haze", "smell", "smells", "mould on the wall",
                 "shift", "replace", "cost", "how much does", "cleaner", "clean the tiles",
                 "how do i clean")),

    # -- liquid on a screen ------------------------------------------------
    # "can i use vinegar on my phone screen" was answered with the screen-time card for children,
    # which is the same word and a different house. A liquid is what the question is about.
    entry("liquid-on-a-screen",
          (_WET, _SCREEN),
          "A cloth, not a bottle: a microfibre cloth just damp with water, wrung out, wiped over "
          "with the screen off, then a dry corner for the streaks. No sprays straight onto a "
          "screen, because the liquid runs into the edge; no vinegar, alcohol, glass cleaner or "
          "hand sanitiser, because they take the coating off and leave the smeary patch you are "
          "trying to clean.",
          bias=3,
          avoid=("how much", "how long", "time", "children", "child", "kids", "kid", "toddler",
                 "baby", "bedtime", "sleep", "addict", "addicted", "addiction", "cracked",
                 "smashed", "broken", "replace", "replacement", "repair", "crack", "not working",
                 "wont turn on", "won't turn on", "black", "dead", "battery", "charge",
                 "buy", "buying", "which one", "best one", "protector")),

    # -- a scourer on a coated pan -----------------------------------------
    entry("abrasive-on-a-coated-pan",
          (_ABRASIVE, _COATED),
          "Not with a scourer or wire wool: it takes the coating off in flakes, the pan stops "
          "being non-stick, and those flakes are what people find in the food. Use the soft side "
          "of a sponge with hot water and washing-up liquid while the pan is still warm, and a "
          "wooden or silicone spatula in it. Soak a burnt patch with water and a little "
          "bicarbonate rather than scrubbing it.",
          bias=3,
          avoid=("metal taste", "taste", "tastes", "tasting", "metallic", "rust", "rusty",
                 "warp", "warped", "handle", "loose handle", "season", "seasoning",
                 "re-season", "reseason", "cast iron", "stainless", "buy", "buying",
                 "which pan", "best pan", "replace", "replacing", "worth")),

    # -- hand liquid in a machine -----------------------------------------
    entry("hand-liquid-in-a-machine",
          (_HAND_LIQUID, _ANY_MACHINE),
          "No: washing-up liquid and hand soap lather, and a dishwasher or a washing machine "
          "turns a teaspoon of it into foam that comes out of the door and can reach the pump. "
          "Dishwasher tablets or powder in the dishwasher, washing powder or liquid in the "
          "washing machine, and a splash of hand liquid only for hand washing. If it has already "
          "foamed, run the machine empty with a rinse.",
          bias=3,
          avoid=("hand wash", "by hand", "sink", "bowl", "washing up by hand", "cheaper",
                 "cheapest", "save", "saving", "cost", "much", "how much", "which one",
                 "best", "eco", "short", "tablet", "tablets", "salt", "rinse aid")),

    # -- what a dishwasher is happy with ----------------------------------
    # The other half of the same question, and it was three punts: "can i put a plate in the
    # dishwasher", "can i put a plastic lunchbox in the dishwasher". Everyday things are the
    # answer a person wants when they are standing at the sink deciding, and a list of what
    # breaks is no help with a plate.
    entry("fine-in-the-dishwasher",
          (("plate", "plates", "bowl", "bowls", "mug", "mugs", "cup", "cups", "beaker",
            "beakers", "tumbler", "tumblers", "cutlery", "fork", "forks", "spoon", "spoons",
            "teaspoon", "teaspoons", "dish", "dishes", "saucepan", "saucepans", "pan", "pans",
            "tray", "trays", "lunchbox", "lunch box", "tupperware", "plastic box",
            "plastic container", "pyrex", "jug", "casserole", "mixing bowl", "plate rack"),
           _MACHINE),
          "Yes, if there is no hand-wash label on it: everyday china, plain glass, stainless "
          "cutlery and pans, and plastic that says dishwasher safe. Top rack for lids and thin "
          "plastic, and anything that holds water goes face down. Scrape rather than rinse, and "
          "leave the wooden spoons, the sharp knives and the cast iron for the sink.",
          bias=1,
          avoid=("broken", "cracked", "chipped", "chips", "stained", "stains", "not cleaning",
                 "smells", "leaking", "buy", "buying", "which", "best", "cheaper", "cheapest",
                 "cost", "much", "worth", "how do i load", "load", "stack", "fix", "repair")),

    # -- what a dishwasher ruins ------------------------------------------
    entry("what-a-dishwasher-ruins",
          (_NOT_WASHABLE, _MACHINE),
          _what_the_machine_ruins,
          bias=3,
          avoid=("not draining", "wont drain", "won't drain", "leaking", "leak", "smell",
                 "smells", "not cleaning", "filter", "salt", "rinse aid", "tablet", "tablets",
                 "powder", "how do i load", "load", "stack", "buy", "buying", "which",
                 "cheaper", "cheapest", "cost", "much", "worth", "fix", "repair", "error",
                 "broken", "not working", "noise", "noisy")),

]
