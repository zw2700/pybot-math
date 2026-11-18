"""Six kitchen questions about the tools rather than the food, and none of them had an answer.

The board, the spoon, the knife and the pan are the things a person picks up every day, and on
main every line below was a shrug - the "I'm not sure about that one, sorry" family, or "Got it.
Is there anything you'd like a hand with?" - because the cooking table only knows food and the
cleaning table only knows the state of a thing (smelly, mouldy, rusty):

  how do i stop my chopping board sliding   I'm not sure about that one, sorry
  my chopping board keeps slipping          Got it. Is there anything you'd like a hand with?
  my wooden spoon split                     Thanks for telling me
  how do i hold a knife properly            I don't know enough to answer that honestly
  my pan handle is loose                    Got it. Is there anything you'd like a hand with?
  my saucepan handle gets hot              Got it. Is there anything you'd like a hand with?
  how do i season a wooden chopping board   That's beyond what I know well, sorry

Cooking itself is too big to add to: bot/knowledge/cooking.py is over the hub's one-megabyte
upload limit, so this is the file the kitchen's new rows go in, next to cooking_gaps.py.

The neighbours keep their own lines, and the avoid lists below are what does it: a board that
smells is `cooking.board-smell`, a wooden spoon gone mouldy is `cleaning.mouldy-wood`, rusty
kitchen kit is `cooking.rusty-kitchen-gear`, and a knife that needs sharpening is
`cooking.kitchen-knives`. Those are four different questions with four different answers.

Cause first, then the fix, in three sentences: that is what a person wants back.
"""

from .body import a_persons_temperature
from .lookup import entry

ANSWERS = ("cooking",)

# What may go in the basket, which is the question people ask about a new air fryer. Every one of
# these was answered with the appliances' times card ("Air fryer: chicken thighs 25 minutes at
# 190C..."), which is a different question, and the answer depends on the thing being put in.
AIR_FRYER = ("air fryer", "air fryers", "airfryer", "air-fryer", "air frier", "air-frier")

# The thing, then what to say about it. The line is read for the thing named rather than for the
# ask, because "can i put foil in an air fryer" and "can i put a glass dish in an air fryer" are
# the same question with two different answers.
AIR_FRYER_BASKET = {
    "foil": ("Foil is fine over the food but not on the floor of the drawer: it blocks the holes "
             "the hot air comes through, so the fan strains and the food steams instead of "
             "crisping. Loosely tented over the top to stop something browning too fast, with the "
             "sides clear, is the way it is meant to be used."),
    "parchment": ("Yes, so long as the food holds it down: a loose sheet lifts into the element of "
                  "a nearly empty basket and scorches. The perforated liners sold for air fryers "
                  "are the safe version, and a sheet of baking paper cut to fit with a few holes "
                  "punched in it does the same job."),
    "glass": ("Any dish that says oven-safe works if it fits with a finger's width all round - a "
              "small Pyrex or a ceramic ramekin is about right. Let it come up to room "
              "temperature first, because cold glass into a hot basket can crack."),
    "metal": ("Metal is what the basket is made of, so a small tin, a cake mould or skewers are "
              "fine as long as they do not touch the roof. Skip anything with a loose foil lid, "
              "and use a tin whose non-stick has not started to flake."),
    "silicone": ("Silicone is the one soft thing that belongs in there: moulds, liners and "
                 "handles are fine to 200C or more, and they lift out without scratching the "
                 "basket. Check the packet for the top temperature before you trust a cheap one "
                 "at 200C."),
    "plastic": ("Nothing plastic goes in the basket - it warps and can give off fumes at 180C. "
                "Cling film, freezer bags and plastic tubs come off first, and a plastic tub is "
                "only useful afterwards, to stand the hot basket on."),
    "chicken": ("A whole chicken needs a big one, 5 litres and up, and it must not touch the roof: "
                "spatchcock it or truss it tight. At 180C give it 25 minutes per 500g plus 10, and "
                "check the thickest part of the thigh reaches 74C; if the skin colours early, a "
                "loose foil hat over the top settles it."),
}


def _air_fryer_basket(memory, understood):
    """What to say about the thing the line wants to put in the basket."""
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    for thing in ("parchment", "baking paper", "greaseproof"):
        if thing in text:
            return AIR_FRYER_BASKET["parchment"]
    for thing in ("cling film", "plastic", "freezer bag", "tub", "tupperware", "container"):
        if thing in text:
            return AIR_FRYER_BASKET["plastic"]
    if "foil" in text:
        return AIR_FRYER_BASKET["foil"]
    if "whole chicken" in text or ("chicken" in text and "whole" in text):
        return AIR_FRYER_BASKET["chicken"]
    if any(word in text for word in ("glass", "pyrex", "ceramic", "ramekin", "dish", "bowl",
                                     "plate", "mug")):
        return AIR_FRYER_BASKET["glass"]
    if "silicone" in text or "sillicone" in text:
        return AIR_FRYER_BASKET["silicone"]
    if any(word in text for word in ("metal", "tin", "mould", "mold", "skewer", "skewers",
                                     "loaf")):
        return AIR_FRYER_BASKET["metal"]
    return None


def a_dish_has_its_own_heat(understood):
    """True when the line names a dish the dish table has an oven heat for.

    The probe answers the doneness of a joint; a dish with a number in the dish table answers
    the heat it is cooked at, and it is the row that should take the line.
    """
    if not isinstance(understood, dict):
        return False
    text = str(understood.get("clean") or understood.get("text") or "")
    if not text:
        return False
    from . import dishes
    plan = dishes.PLANS.get(dishes.dish_in(text) or "")
    return bool(isinstance(plan, dict) and plan.get("temp"))


ENTRIES = [
# A board that walks across the worktop is friction, not technique: a wet cloth is the whole
# answer, and it is what a chef does rather than anything sold for it.
entry("board-slide",
      (("chopping board", "chopping boards", "cutting board", "cutting boards",
        "wooden board", "wooden boards", "plastic board", "butcher block",
        # "how do i stop the board slipping on granite" names no material: the bare board is this
        # question, and the avoid list below is what keeps it to a kitchen one
        "board", "boards", "the board", "my board"),
       ("slid", "slides", "sliding", "slip", "slips", "slipping", "slippy", "moves", "moving",
        "wobble", "wobbles", "wobbling", "wobbly", "stay still", "stays still", "stay put",
        "stays put", "steady", "grip", "non slip", "non-slip", "nonslip", "stop it moving")),
      "A board slides because nothing is gripping the worktop, and the fix is a tea towel: wet "
      "it, wring it out and spread it flat underneath, and the board will not move - that is "
      "what kitchens do rather than anything you buy. A non-slip mat cut to size or a rubber "
      "band round each end does the same. If the board is too small to hold both the food and "
      "what you have cut off it, a bigger one is the real answer, because a crowded board makes "
      "you work with the knife in a rush.",
      # every other board in a house: the ironing board, the floor, the noticeboard, the keys
      avoid=("ironing", "surfboard", "surf", "skateboard", "skate", "snowboard", "board game",
             "board games", "board of", "keyboard", "keyboards", "dashboard", "scoreboard",
             "blackboard", "whiteboard", "noticeboard", "notice board", "headboard",
             "floorboard", "floorboards", "skirting", "cupboard", "cupboards", "wardrobe",
             "cheeseboard", "chessboard", "chess", "abroad")),

# Wood that has split is a hygiene question as well as a broken one: the crack is where food goes
# and a wash cannot follow.
entry("wooden-spoon-split",
      (("wooden spoon", "wooden spoons", "wooden spatula", "wooden spatulas", "wooden utensil",
        "wooden utensils", "spoon", "spoons", "spatula", "spatulas", "rolling pin",
        "wooden handled", "wooden handles"),
       ("split", "splits", "splitting", "cracked", "crack", "cracks", "cracking", "splinter",
        "splinters", "splintered", "broken", "broke", "rough", "gone rough", "fuzzy",
        "hairy", "flaking")),
      "Split wood - a spoon, a spatula, a rolling pin - is a hygiene problem before it is a broken "
      "one: the crack holds food "
      "where a wash cannot reach, so bin it if the split goes through or the wood inside has "
      "gone dark, and sand it smooth with fine paper along the grain and oil it if the split is "
      "only a surface one. Wood is cheap - a new spoon is a couple of pounds - and water and "
      "heat are what split it, so never soak one and never put it in the dishwasher. Oil spoons "
      "and boards once a month with food-safe mineral oil, not olive oil, which goes rancid.",
      # a mouldy spoon is the cleaning table's row, and a smelly one is the board's
      avoid=("mould", "mouldy", "mold", "moldy", "mildew", "musty", "smell", "smells", "smelly",
             "stain", "stains", "rust", "rusty", "soup", "stirring", "stir"),
      # A spoon that has gone rough is this row's question and the furniture care row's too, and
      # the two were tied: `cleaning.wood-care` comes first in the registry, so it took "my
      # wooden spoon is rough" and told the person to sand a table. The bias is for the spoon.
      bias=1),

# How to hold a knife is a technique question with a right answer, and the knife row only knows
# sharpening: "how do i hold a knife properly" was a search hedge.
entry("knife-grip",
      (("knife", "knives", "kitchen knife", "chef's knife", "chefs knife", "blade",
        # "how do i stop cutting my fingers when chopping" names the job and no knife at all
        "chopping"),
       ("hold", "holding", "grip", "properly", "correctly", "right way", "how should i",
        "dice", "dicing", "chop", "chopping", "cutting", "technique", "fingers",
        "claw", "keep my fingers", "without cutting myself",
        "cutting my fingers", "cut my fingers", "cutting myself", "knife slips",
        "slips when i chop")),
      "Hold the knife in a pinch grip - thumb and forefinger pinching the blade where it meets "
      "the handle, the other three fingers round the handle - which lines the blade up with "
      "your forearm and gives you control. On the other hand, curl the fingertips under so the "
      "knuckles lead and the flat of the blade rides against them, because that is what keeps "
      "fingers clear rather than watching them. Keep the tip down on the board and push forward "
      "instead of chopping up and down, and keep the knife sharp: a blunt one skids off onion "
      "skin and that is when people cut themselves.",
      # a knife that needs sharpening, a rusty one and a cut finger are other rows
      # An injury is the first-aid row's line, so the bare "cut my finger" is not enough here:
      # the loose match takes "cutting my fingers" with it, and "how do i stop cutting my fingers
      # when chopping" is a technique question. The phrases below only catch a cut that happened.
      avoid=("sharp", "sharpen", "sharpening", "sharper", "blunt", "dull", "hone", "steel",
             "rust", "rusty", "i cut my finger", "i cut my hand", "i cut myself",
             # keeping a knife, washing it and oiling it is the care row: "how should i keep
             # my knives" is not a question about the grip
             "keep", "keeping", "kept", "store", "storing", "storage", "oil", "oils", "oiled",
             "oiling", "wash", "washing", "dry", "drying",
             "cut my finger with", "cut my hand with", "cut myself with", "cut my finger on",
             "sliced my finger", "sliced my hand", "severed", "bleeding", "bled", "stitches",
             # choosing one is a shopping question, and the grip is no answer to it
             "best knife", "which knife", "what knife", "buy", "buying", "recommend",
             "a good knife", "knife set",
             "cut me", "slipped and cut", "came down on my finger", "cut through my",
             "stabbed", "knife block", "knife crime")),

# A loose handle is a scald waiting to happen, so the answer says how to tighten it and when to
# stop using it.
entry("pan-handle-loose",
      (("pan", "pans", "saucepan", "saucepans", "frying pan", "wok", "stock pot", "pot", "pots",
        "pan lid", "pressure cooker"),
       ("handle", "handles", "loose", "wobbly", "wobbles", "wobbling", "screw", "screws",
        "rivet", "rivets", "tighten", "tight", "came off", "coming off", "fell off",
        "falls off", "falling off")),
      "Most loose pan handles are one screw through a bracket: hold the nut on the inside with "
      "pliers and turn the screwdriver, then check it again after the next wash, because the "
      "heat works it loose again. A riveted handle that has worked loose cannot be tightened "
      "back safely, so the pan goes, and until it is fixed lift it with both hands rather than "
      "by the handle - a pan of boiling water letting go is a scald to the legs and feet. If the "
      "screw has stripped the wood, a slightly longer screw with a washer will bite again.",
      # a handle that gets hot is the next row: the screw is fine there, the heat is the problem
      avoid=("door", "doors", "window", "cupboard", "drawer", "fridge", "oven", "knife",
             "suitcase", "bag", "tool", "hammer",
             "hot", "heats", "heating", "heating up", "gets hot", "got hot", "too hot",
             "burn", "burns", "burnt", "burning", "scald", "scolds", "melt", "melting")),

# "my saucepan handle gets hot" reached the loose-handle row, which is a confident wrong answer:
# the screw is fine, the heat is the problem. This is the row for it.
entry("pan-handle-hot",
      # The heat alone is not the question: "how do i know when the pan is hot" and "i left the
      # pan on the heat" are about the food, and only a handle that gets hot is this row. A third
      # key part would not hold that line back - scoring needs two words in all, not one from each
      # part - so the handle is required through `ask`, which the matcher honours.
      (("pan", "pans", "saucepan", "saucepans", "frying pan", "wok", "stock pot", "pot", "pots"),
       ("hot", "heats", "heating", "heating up", "gets hot", "got hot", "too hot", "burn",
        "burns", "burnt", "burning", "scald", "scolds", "melt", "melting")),
      "A pan handle gets hot because the metal carries heat up from the base, and the flame "
      "licking past the side of the pan makes it worse: keep the gas inside the base so it does "
      "not climb the wall, and use a lower heat with a bigger pan rather than a fierce flame "
      "under a small one. Hold the handle in a dry folded tea towel or a silicone sleeve, never a "
      "wet cloth, because water carries heat straight through to your hand. Turn the handle in "
      "over the hob when you are not holding it, so nobody catches it going past.",
      ask=("handle", "handles", "handgrip", "grip", "holding it"),
      # a loose or falling-off handle is the row above, and a burnt dinner is the cooking table's
      avoid=("loose", "wobbly", "wobbles", "screw", "screws", "rivet", "rivets", "tighten",
             "came off", "coming off", "fell off", "falls off", "falling off", "food", "dinner",
             "sauce", "burnt the", "oven", "door", "window")),

# Wood dries out, shrinks and splits, and the answer for a board is oil rather than a new board.
entry("board-season",
      (("chopping board", "wooden board", "wooden chopping board", "cutting board",
        "wooden boards", "butcher block", "wooden worktop",
        # "my board has split down the middle" is the same question as a named one
        "board", "boards", "the board", "my board"),
       ("oil", "oils", "oiling", "oiled", "season", "seasoning", "seasoned", "treat",
        "treating", "condition", "conditioning", "dry", "drying", "dried out", "dry out",
        "warped", "warping", "crack", "cracks", "cracked", "cracking", "split", "splits",
        "splitting",
        # A board that has bowed is the same board with the same fix, and the oil sentence
        # alone does not say what to do about it: "my cutting board is bowed" and "my board
        # doesnt sit flat" were both a listening line while "my board is warped" reached this
        # row, so the shape of the warp is a key word here too.
        "bowed", "bow", "bowing", "bent", "bending", "curved", "curving", "not flat",
        "doesnt sit flat", "doesn't sit flat", "wont sit flat", "won't sit flat",
        "rocks", "rocking",
        # a worktop is sealed and protected with the same oil a board is, and "how do i seal a
        # butcher block worktop" found one key word and nothing else
        "seal", "seals", "sealing", "sealed", "waterproof", "protect", "protecting",
        "protection",
        # "how do i care for a wooden chopping board" was answered with watering the plants, and
        # "look after" was a shrug: neither names oil, and both are this row's question
        "look after", "looking after", "care for", "caring for", "maintain", "maintenance",
        "keep it nice", "last longer", "keep it going",
        "hairy", "fuzzy", "furry", "gone rough", "raised grain", "rough patches")),
      # The oil goes first because that is what is being asked: "how do i season a chopping
      # board" is not a question about a bow, and the answer used to open with one.
      "Rub a thin coat of food-safe mineral oil into both faces and the edges once a month, and "
      "more often in a dry kitchen: that is all seasoning a board is, and olive or vegetable oil "
      "go rancid in the wood, so use mineral oil or a board wax. A board that has warped wants "
      "the same oil after a drink, because one face has taken on water that the other did not: "
      "damp both faces, lay it flat on the worktop with a heavy pan across it for a few days, "
      "then wash it, stand it up to dry and oil it. A board that has split down the grain cannot "
      "be cleaned safely enough for food afterwards, so sand the crack out flat or replace it, "
      "and never soak a board or put it in the dishwasher.",
      # the smell of a board and a mouldy one are the other two rows
      avoid=("smell", "smells", "smelly", "stain", "stains", "mould", "mouldy", "mold",
             "mildew", "musty", "onion", "garlic", "raw chicken",
             "ironing", "surfboard", "skateboard", "snowboard", "board game", "board games",
             "board of", "keyboard", "dashboard", "scoreboard", "blackboard", "whiteboard",
             "noticeboard", "notice board", "headboard", "floorboard", "floorboards",
             "skirting", "cupboard", "cupboards", "wardrobe", "abroad"),
      # The rarity bonus is part of how an entry ranks (a key word no other row in the table uses
      # says more about the line), so the rows added below - the knife is oiled and dried too -
      # took "oil" out of this row's own words and it lost a tie it used to win: "how do i oil my
      # chopping board" became the furniture wood-care row. The bias is that bonus put back.
      bias=1),
# --- looking after the kit ------------------------------------------------
# The knife, the scales, the scissors and the thermometer are the four things in a kitchen that
# people ask how to keep, and every line below was a shrug on main - or worse, the kitchen room
# routine, because "kitchen" plus "how" was enough for it to claim the line:
#
#   how do i store my knives                        I don't know enough to answer that honestly
#   do i need to oil my knife                       I'm not sure about that one, sorry
#   how do i calibrate my kitchen scales            the clean-the-kitchen paragraph
#   how do i use kitchen scales                     the clean-the-kitchen paragraph
#   my kitchen scales are not accurate              "Thanks for telling me"
#   how do i use a meat thermometer                 the search hedge
#   how do i clean my kitchen scissors              the clean-the-kitchen paragraph
#   my kitchen scissors are stiff                   "Thanks for telling me"
#   my digital scales keep switching off            advice about sleep
#   what knife should i buy                         the search hedge
#   which knives do i actually need                 the search hedge
#
# Keeping a thing, using a thing, mending a thing and choosing a thing are four questions, so
# they are four rows; sharpening a knife stays `cooking.kitchen-knives`, holding one stays
# `knife-grip`, a blunt pair of scissors stays `cooking.sharpening-scissors`, rust stays
# `cooking.rusty-kitchen-gear` and a board that needs oil stays `board-season`.
entry("knife-care",
      (("knife", "knives", "kitchen knife", "kitchen knives", "blade", "chef's knife",
        "chefs knife", "carbon steel knife", "stainless steel knife", "paring knife",
        "knife handle"),
       ("store", "storing", "stored", "storage", "keep", "keeping", "kept", "oil", "oils",
        "oiled", "oiling", "care", "caring", "look after", "looking after", "looked after",
        "maintain", "wash", "washing", "clean", "cleaning", "dry", "drying", "drawer",
        "block", "magnetic", "sleeve", "sheath", "dishwasher", "hand wash", "patina",
        "carbon steel", "last longer")),
      "Keep a knife dry, edge away from anything hard, and it will last: wash it by hand in hot "
      "soapy water, dry it at once and put it back in a block, a magnetic strip or a sleeve, "
      "never loose in a drawer where the edge knocks against everything else. Never leave one in "
      "the sink and never put it in the dishwasher, because the heat and the long soak blunt the "
      "edge and split a wooden handle. A carbon steel blade rusts in minutes, so wipe it dry and "
      "rub on a film of food-safe oil after every wash, and oil a wooden handle once a month.",
      # sharpening, holding it and rust are the rows named above, and choosing one is the row
      # below: none of them is a question about keeping it
      avoid=("sharp", "sharpen", "sharpening", "sharper", "blunt", "dull", "hone", "hold",
             "holding", "grip", "cut my", "cutting my", "cut myself", "i cut", "rust", "rusty",
             "best", "buy", "buying", "which", "recommend", "spend", "worth", "slipped",
             "engrave", "cheese knife", "steak knife", "bread knife", "pocket knife",
             "penknife", "stanley knife", "butter knife"),
      bias=1),

# Pressing tare is what a scale is for and nobody teaches it, so the bowl on first and the
# display counting only what you add is the whole answer to "how do i use it".
entry("scales-use",
      (("kitchen scales", "kitchen scale", "digital scales", "digital scale", "weighing scales",
        "weighing scale", "scales", "scale"),
       ("use", "using", "tare", "zero", "reset", "weighing out", "weigh out", "add up",
        "how do i weigh", "how to weigh", "measure out", "measuring out", "get one", "which one",
        "worth it", "bother", "need", "needed", "worth buying", "good one")),
      "Put the bowl or the jug on the scales first, press tare - or the zero button - and then "
      "add the flour, so the display counts only what you put in; press it again for the next "
      "thing and the bowl never has to come off. Weigh the wet things first and the dry ones "
      "after, because a scale cannot tell you what you have already added. A scale with a "
      "1g step is the one to own: a 5g step cannot measure 7g of yeast.",
      # the mug answer for someone with no scales, a bathroom scale, and a scale that reads
      # wrong are three other rows
      avoid=("bathroom", "my weight", "lose weight", "weigh myself", "diet", "weight loss",
             "stone", "baby", "newborn", "baggage", "suitcase", "airport", "parcel", "postage",
             "kettle", "limescale", "descale", "fish", "broke", "broken", "without", "grams",
             "cups", "recipe", "convert", "no scales", "guitar", "music", "map", "model",
             "richter", "economies of", "accurate", "accuracy", "inaccurate", "widely",
             "drift", "drifts", "readings", "switching off", "switches off", "turns itself off",
             "battery", "batteries"),
      bias=1),

# A scale that reads a few grams light makes a cake heavy and bread that does not rise, and the
# battery is what most of them need: the check and the fix are one answer.
entry("scales-wrong",
      (("kitchen scales", "kitchen scale", "digital scales", "digital scale", "weighing scales",
        "weighing scale", "scales", "scale"),
       ("accurate", "accuracy", "inaccurate", "not accurate", "wrong", "out", "out by", "drift",
        "drifts", "drifting", "readings", "different readings", "jumpy", "jumps", "jumping",
        "switching off", "switches off", "switching itself off", "turns itself off", "dead",
        "battery", "batteries", "stopped working", "all over the place", "calibrate",
        "calibration", "check it", "test it", "trust it", "reliable")),
      "A scale that switches itself off mid-weigh or jumps about almost always wants a new "
      "battery, and one that reads a little wrong wants checking against something whose weight "
      "you know: a 1kg bag of sugar should read 1kg and 500ml of water weighs 500g. Weigh on a "
      "hard, flat surface with the feet clear of the worktop and nothing else touching the bowl. "
      "If it is still out by more than a few grams on a known weight, throw it away rather than "
      "cooking around it, because every bake after that is a guess.",
      # how to use one, the mug answer for someone with no scales, and a bathroom scale are
      # three other rows
      avoid=("bathroom", "my weight", "lose weight", "weigh myself", "diet", "weight loss",
             "stone", "baby", "newborn", "baggage", "suitcase", "airport", "parcel", "postage",
             "kettle", "limescale", "descale", "fish", "broke", "broken", "without", "grams",
             "cups", "recipe", "convert", "no scales", "guitar", "music", "map", "model",
             "richter", "economies of", "tare", "zero button", "how do i use", "how to use",
             "weigh out", "measuring out", "need one", "do i need", "worth it", "bother"),
      bias=2),

# Nobody knows what to do with the thermometer in the drawer, and "is it done" is the question
# that follows. Cooking temperatures are per meat and the check is a glass of ice water.
entry("meat-thermometer",
      (("thermometer", "meat thermometer", "temperature probe", "probe", "digital thermometer",
        "instant read thermometer", "thermapen", "temperature"),
       ("use", "using", "where", "insert", "read", "reading", "check", "accurate", "calibrate",
        "clean", "wash", "safe", "internal", "should i", "worth it", "buy", "need", "done",
        "cooked")),
      "Push the probe into the thickest part, away from bone, fat and the tin, and wait for the "
      "number to stop climbing: 75C for chicken and pork, 63C for beef or lamb you want pink, and "
      "60C for a joint that will rest, because it keeps rising as it sits. Chicken thighs want "
      "80C if you have the patience, since that is where the connective tissue gives in. Check the "
      "thermometer itself by standing it in a glass of crushed ice and water, where it should "
      "read 0C, and wash the probe in hot soapy water between uses.",
      # the oven's own thermometer, a fever, and the chicken-done row are other questions
      avoid=("oven", "dial", "fan", "gas mark", "room", "outside", "weather", "greenhouse",
             # a pizza carries no joint to probe: "what temperature do i cook pizza at" was
             # told to push the probe into the thickest part, away from bone, fat and the tin
             "pizza", "pizzas", "bake", "baking", "cake", "cakes", "bread", "pastry",
             "fever", "body temperature", "child", "baby", "fridge", "freezer", "boiler",
             "radiator", "wall", "thermostat", "heating", "central heating", "water",
             # the row keys a bare "temperature", so "what temperature should i wash towels
             # at" was the probe and the joints: a laundry noun is the wash dial's line, and
             # wash-temperature answers it with the heat each load wants
             "laundry", "the wash", "wash at", "washing machine", "washer dryer",
             "towels", "towel", "sheets", "sheet", "bedding", "duvet", "duvets", "linen",
             "clothes", "clothing", "whites", "darks", "colours", "colors", "shirts",
             "shirt", "socks", "jeans", "jumper", "jumpers", "load of washing",
             "fabric softener", "non-bio", "tumble dryer", "tumble", "bio detergent",
             # the heat of an iron is `clothing.iron-heat`, and a burnt soleplate is the
             # cleaning row: a bare "temperature" let the probe take both
             "iron", "ironing", "ironing board", "soleplate", "steam iron", "press",
             # the oven's heat for a bake is the baking rows' ("what temperature should i bake
             # a cake at" was the probe and the joints)
             "bake", "baking", "baked", "roast", "roasting", "roasted", "cake", "cakes",
             "bread", "pastry", "biscuits", "cookies", "scones", "yorkshire", "casserole",
             "oven temperature", "gas mark", "how long in the",
             # a thermometer has nothing to say about washing a nappy either
             "nappy", "nappies", "dishes", "hands", "hair",
             # a named meat is that meat's own row ("what temperature should chicken be"),
             # which gives the doneness as well as the number
             "chicken", "turkey", "pork", "lamb", "beef", "steak", "sausage", "sausages",
             "burger", "burgers", "fish",
             # The dial on the washing machine is the other "what temperature should i ..."
             # question, and it is asked far more often than this one: "what temperature should
             # i wash bedding at", "... wash towels at" and "... wash whites at" were all
             # answered "push the probe into the thickest part", because "temperature" and
             # "wash" are a score of four here and the laundry row beside it scored the same.
             # A probe question never names bedding, towels or clothes, so those words stand
             # this card down and `clothing.wash-temperature` takes the line.
             "bedding", "bed sheets", "sheets", "duvet", "duvets", "pillow", "pillows",
             "pillowcases", "towels", "towel", "flannels", "underwear", "socks", "knickers",
             "boxers", "nappies", "nappy", "laundry", "clothes", "clothing", "shirts", "jeans",
             "jumper", "jumpers", "wool", "woollen", "delicates", "whites", "darks", "colours",
             "washing machine", "wash cycle", "wash at", "wash on",
             # A cake and a loaf are asked for a dial number in the same words as a probe, and
             # the baking row holds the number: "what temperature does a cake need" and "what
             # temperature do i bake bread at" were both answered "push the probe into the
             # thickest part", which is also the deck's `tempis-02` and `thankstep-06`.
             "cake", "cakes", "sponge", "bake", "baking", "baked", "bread", "loaf",
             "scones", "pastry", "muffins", "biscuits", "buns", "cookies", "pie",
             "pies", "tarts",
             # A dial turned up or down is the oven's question, not the probe's: "thanks, i need
             # a higher temperature" after a bread question is the bread row's follow-up (220C,
             # or 230C for a hotter oven), never a probe pushed into a joint.
             "higher", "lower", "hotter", "cooler",
             # The heat a home is kept at is the thermostat's card, and "room" alone did not
             # reach it: "what temperature should i keep the house at", "... the flat at" and
             # "... the bedroom at" were all told to push the probe into the thickest part of
             # the joint, where "what temperature should the house be" beside them was 18C. A
             # probe question never names a room of a home, so the rooms stand this card down -
             # as phrases for the house itself, because "how do i use a meat thermometer at
             # home" is still the probe.
             "the house", "my house", "our house", "a house",
             "the home", "my home", "our home", "at home in",
             "the flat", "my flat", "our flat", "the apartment", "my apartment",
             "keep the house", "keep the flat", "keep the home", "keep the heating",
             "bedroom", "bedrooms", "living room", "nursery", "bathroom", "hallway",
             "attic", "cellar"),
      # A number with the word "temperature" is a fever as often as it is a roast, and the
      # reading knows which: "my temperature is 39, what should i do" was this card. The
      # person's own temperature stands it down, and `body.fever-rest` answers instead.
      # ...and a dish that has its own oven heat is the dish table's question: "what
      # temperature do i cook chips at" was "push the probe into the thickest part", which is
      # about a joint and not about chips.
      guard=lambda understood: (not a_persons_temperature(understood)
                                and not a_dish_has_its_own_heat(understood)),
      bias=1),

# A pair of scissors that will not open is nearly always the pivot, and the answer is a drop of
# oil: sharpening a blunt pair is `cooking.sharpening-scissors`, which is a different question.
entry("scissors-clean",
      (("kitchen scissors", "scissors", "kitchen shears", "kitchen snips"),
       ("stiff", "stiffen", "stiffened", "seized", "hard to open", "wont open", "won't open",
        "stuck", "sticking", "sticky", "gunk", "gummed up", "clean", "cleaning", "wash",
        "washing", "dirty", "oil", "oiling", "loosen", "sieze")),
      "Wash them by hand in hot soapy water, working the blades open and closed under the water "
      "so the gunk at the pivot comes out, then dry them at once: a dishwasher rusts the pivot "
      "and takes the edge off. A pair that is stiff or hard to open is nearly always the pivot "
      "rather than the blades, so put a drop of cooking oil or a squirt of WD-40 on it and work "
      "the blades open and closed, then wipe the surplus off. If the two blades have started to "
      "spread, nip the screw at the pivot up a quarter turn.",
      # a blunt pair, rusty kit, garden shears, hairdressing scissors and nail scissors are
      # five other rows
      avoid=("blunt", "dull", "sharpen", "sharpening", "sharp", "chews", "wont cut",
             "cut properly", "not cutting", "garden", "gardening", "secateurs", "hedge", "hedges",
             "branch", "branches", "nail", "nails", "toenail", "hair", "haircut", "barber",
             "fabric", "cloth", "wallpaper", "wrapping", "paper", "thread", "first aid",
             "bandage", "dog", "cat", "grooming", "rust", "rusty", "stain", "stains",
             "cut myself", "cut my finger", "cut my hand", "slipped", "kids", "child", "toddler"),
      bias=2),

# Choosing one is a shopping question with a short honest answer, and the grip and sharpening
# rows step aside for it.
entry("knife-buying",
      (("knife", "knives", "kitchen knife", "chef's knife", "chefs knife", "chefs knives",
        "santoku", "knife set", "knife block", "cooks knife"),
       ("buy", "buying", "should i buy", "which", "what knife", "how much", "spend", "worth",
        "recommend", "need", "actually need", "start with", "beginner", "good", "best", "set",
        "gift", "first knife", "look for", "what should i")),
      "One 20cm cook's knife does almost everything, so spend the money there - around 25 to 40 "
      "pounds on a forged one with a full tang gets an edge that holds - and add a serrated bread "
      "knife and a small paring knife when you need them, rather than buying a set of six cheap "
      "ones that none of them do a job well. Hold it before you buy it, because the handle has to "
      "fill your hand, and only buy something you can sharpen yourself with a steel or a stone.",
      # the grip, the sharpening and the keeping rows are the three neighbours
      avoid=("sharp", "sharpen", "sharpening", "blunt", "dull", "hone", "hold it properly",
             "grip", "store", "storing", "oil", "care", "rust", "rusty", "cut my", "cut myself",
             "slipped", "crime", "attack", "stab", "threat", "weapon"),
      # "what should i look for in a chefs knife" reads as a careers question on its bare words
      bias=2),
# The thing in the basket decides the answer, so this row is only about that: the times, the
# health claim, the size and the cleaning of an air fryer are four other questions, and the food
# named beside it has its own row for how long it takes.
entry("air-fryer-basket",
      (AIR_FRYER, ("foil", "tin foil", "aluminium foil", "parchment", "baking paper",
                   "greaseproof", "glass", "pyrex", "ceramic", "dish", "bowl", "plate", "metal",
                   "tin", "tins", "mould", "mold", "skewer", "skewers", "plastic", "cling film",
                   "silicone", "sillicone", "liner", "liners",
                   "freezer bag", "tub", "tupperware", "container", "whole chicken", "mug",
                   "safe", "put in", "put it in", "go in", "goes in", "fit", "fits")),
      _air_fryer_basket,
      avoid=("how long", "how many minutes", "minutes", "temperature", "what temperature",
             "chips", "thighs", "legs", "salmon", "bacon", "sausages", "healthier", "healthy",
             "less oil", "worth it", "better than", "compare", "oven", "size", "how big", "litre",
             "litres", "capacity", "preheat", "clean", "cleaning", "wash", "smoke", "smoking",
             "smell", "smells", "broken", "not working", "fuse", "energy", "electricity", "cost",
             "cheaper", "buy", "which one", "recommend", "recipe", "recipes", "dinner", "tea",
             "lunch", "weight", "diet", "calories"),
      bias=2),
]
