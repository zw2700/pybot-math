"""The kit you haven't got: what to use instead of the thing that is not in the drawer.

The answers lane owns this domain. A cook or a householder who has started a job and found the
tool missing asks one thing in a dozen shapes - "i dont have a colander", "what if i only have
plain flour", "no sieve what can i do", "what can i use instead of a tin opener", "can i make do
without a whisk" - so the shape of the ask is one shared tuple (NO_KIT_ASK below) and the thing
that is missing is the row's own key.

Why the rows are keyed on the thing and not on the job: the answer to "no colander" is the same
answer while the pasta, the potatoes or the berries are in the water, so the words in the reply
speak about the tool's job rather than about one dish. That also keeps the table small: one line
per tool answers every dish it is used for.

What must not reach the table, and is in NOT_A_SHORTAGE:

* a tool that is broken rather than missing - "my hoover has stopped working" is a repair
  question, and telling somebody to sweep instead is not the answer they asked for;
* a tool that is being cleaned, stored, bought or chosen - "which hoover should i buy", "how do
  i clean a mop";
* a question about the thing itself - "how long do you boil an egg in a colander" is not a
  thing, but "what is a colander for" is, and the explanation is a different answer.

None of the rows is a bodge that trades a small risk for a real one: the ladder row says to
borrow a ladder rather than stand on a chair, because a fall is not an everyday inconvenience.
"""
import re

from .lookup import entry
from .swaps import SWAP_ASK

# The topics this domain answers. Both already exist (cook_kit.py declares the same trio), so
# the union bot/modules/answers.py publishes does not change.
ANSWERS = ("cooking", "food-and-drink", "home-and-diy")

# The words that say "the thing is not here". The shared swap tuple covers the ones a recipe
# question uses ("instead of", "ran out", "dont have"); the rest are how a missing tool is put
# to a person, and "make do" and "improvise" are the two that name no substitute at all.
NO_KIT_ASK = SWAP_ASK + (
    "dont have", "don't have", "havent got", "haven't got", "havent any", "haven't any",
    "dont own", "don't own", "without", "no", "none", "only have", "only got", "just have",
    "just got", "all i have", "all ive got", "all i've got", "left with", "nothing but",
    "missing", "lost", "make do", "make-do", "improvise", "bodge", "borrow", "lend",
    "what can i use", "what do i use", "what should i use", "what else can i use",
    "anything else", "something else", "what else", "alternative", "replacement",
    "substitute", "instead", "swap", "replace", "ran out", "run out", "out of",
    # A bare "out of" is a shortage - "out of baking paper", "out of foil" - and people say it
    # with no "i'm" in front, so taking it out of the ask lost every one of those. What has to be
    # fenced off is the place a thing was taken *out of*: "i left the milk out of the fridge
    # overnight" is a keeping question, not a fridge that is missing. Those go in NOT_A_SHORTAGE
    # below, as whole phrases rather than the place on its own, because a bare "fridge" fences
    # the row's own questions - "no fridge in the new flat" is a real shortage.
)

# A tool that is broken, being bought, being cleaned or being explained is not a tool that is
# missing, and each of those is somebody else's answer.
NOT_A_SHORTAGE = ("broken", "broke", "not working",
                  "stopped working", "stopping working",
                  "wont work", "won't work", "doesnt work", "doesn't work", "repair", "fix",
                  "fixing", "mend", "mending", "faulty", "spare part", "warranty", "guarantee",
                  "buy", "buying", "bought", "which one", "best", "cheapest", "recommend",
                  "clean", "cleaning", "wash", "washing", "store", "storing", "storage",
                  # scale is what a kettle or a shower head has on it, not a tool that is
                  # missing: "kettle full of scale what do i use" was told a saucepan on the hob
                  # boils water in about the same time. The bare "scale" is left out because
                  # kitchen scales are a tool in the table ("i don't have scales what do i use"),
                  # and so is "descaler", which is a thing people really do run out of.
                  "limescale", "furred", "chalky", "full of scale", "scaled up",
                  "build up of scale", "buildup of scale", "scale in the", "scale on the",
                  # the phrases, not the bare "what's": the forms of "whats" include "what",
                  # and that fenced off "what if i dont have a colander" - the most common way
                  # this question is asked
                  "what is", "what are", "whats the", "what's the", "what is a", "whats a",
                  "what's a", "how do i use", "how to use",
                  # a tin of paint is not a cake tin, and a tip that will not take one is a
                  # disposal question: "the tip near me says no paint tins if theyre not empty"
                  # got a roasting-tin traybake. "tins" stays in the table, because "i have no
                  # tins for baking" is the baking question: the paint words are what says this
                  # line is not one, and they stand the whole row down.
                  "paint", "paints", "gloss", "emulsion", "varnish", "primer", "undercoat",
                  "tip", "recycling", "dump", "skip", "waste",
                  "sharpen", "reviews", "review", "price",
                  # "i left the milk out of the fridge overnight" is taking something *out* of an
                  # appliance, not being without it: "out of" is one of the ask words (it is how
                  # a cook says the flour has run out), and every removal line reached this table
                  # - the milk, the curry, the butter, the cheese and "take the butter out of the
                  # fridge an hour before" all got the no-fridge bodge instead of the two-hour
                  # rule. Nothing is missing in those lines, so the phrase stands the row down.
                  "out of the",
                  # an appliance of its own that a line names is somebody else's answer: the
                  # oven, the slow cooker and the rice cooker each have a card that says what to
                  # do with them, and the hob row's answer is about a hob on its own
                  "oven", "ovens", "microwave", "microwaves", "slow cooker", "rice cooker",
                  "pressure cooker", "air fryer", "cooker hood",
                  # the place a thing came out of, not the place: "out of the fridge", "out of
                  # the oven". Phrase by phrase because a bare "fridge" or "freezer" fences the
                  # card's own questions ("no fridge in the new flat", "we have no freezer").
                  "out of the fridge", "out of the freezer", "out of the oven", "out of the pan",
                  "out of the window", "out of the cupboard",
                  # a person's temperature is not a kitchen tool that is missing: "how do i take
                  # my temperature without a thermometer" was answered with the meat-doneness
                  # test - press the thickest part with a finger - because a thermometer is in
                  # the table of kit. A fever is the health rows' line, and they name the number.
                  "temperature", "temperatures", "fever", "feverish", "feverishness")

# One line per tool: the thing that is missing, then what to use instead. The words after the
# colon answer the job the tool does, so the same line covers every dish the tool is used for.
# The first name in each tuple is the one the reply leans on and the one that is pluralised.
STAND_IN = (
    # --- the kitchen drawer -------------------------------------------------------------
    ("colander", ("colanders", "strainer", "strainers"),
     "A clean tea towel, or the pan's own lid held a little open over the sink: pour slowly and "
     "the water runs out between the two. A sieve over a bowl does it for rice and small pasta, "
     "and a tray of ice in a bowl of water stops it cooking on if you want the pasta cold."),
    ("sieve", ("sieves", "sifter", "sifters"),
     "A fine colander or a tea strainer does it, and if you have neither, whisk the flour round a "
     "wide bowl for half a minute: the whisk breaks the lumps and lets the air in the same way "
     "sifting does."),
    ("whisk", ("whisks", "balloon whisk", "hand whisk", "electric whisk"),
     "A fork beats eggs and cream, just slower: keep the bowl deep and the wrist loose, and for "
     "cream chill both bowl and cream first. A clean jam jar with the lid on will whip a small "
     "amount of cream in about a minute of shaking."),
    ("rolling pin", ("rolling pins",),
     "Any smooth heavy cylinder does it: a wine bottle, a tall glass or a cold milk bottle, all "
     "of them dusted with flour. Chill the bottle first and the pastry stays cold, which keeps "
     "it short."),
    ("grater", ("graters", "box grater", "cheese grater"),
     "A vegetable peeler makes shavings of hard cheese and chocolate, and a knife does for "
     "anything going into a sauce. For parmesan or zest, a fine Microplane is the tool worth "
     "buying; until then, chop it as small as you can and it melts the same."),
    ("blender", ("blenders", "liquidiser", "liquidizer"),
     "A stick blender in a deep jug does most of it, and a food processor does the rest. A "
     "masher then a sieve gets you a smooth soup without either, and a jar with a tight lid "
     "shaken hard will dress a small amount of sauce."),
    ("food processor", ("food processors", "processor", "magimix"),
     "A stick blender for anything wet, a box grater for anything hard, and a knife for "
     "anything rough. Chopping an onion small by hand takes two minutes; a blender turns it to "
     "water, so keep the blade out of it."),
    ("measuring jug", ("measuring jugs", "jug", "measuring cup"),
     "A mug is about 250 to 300 ml, and a tablespoon is 15 ml and a teaspoon 5. Anything you "
     "would weigh, weigh in grams instead: for water and milk a millilitre is a gram, so 200 ml "
     "is 200g on the scales."),
    ("tin opener", ("tin openers", "can opener", "can openers"),
     "For a ring-pull, slide a spoon handle under the ring and lever it up. For a plain tin, "
     "the back of a heavy spoon or a stiff knife pressed down on the rim and worked round the "
     "top will open it - slowly, and the edges are sharp, so hold it with a cloth."),
    ("corkscrew", ("corkscrews", "bottle opener", "bottle openers"),
     "For a cork, push it in with the handle of a wooden spoon and then pour through a small "
     "sieve, or put the bottle in a shoe and tap the base against a wall (the cork walks out). "
     "For crown caps, a coin or the back of a lighter under the edge does it."),
    ("potato masher", ("mashers", "potato mashers"),
     "A fork for anything soft, and the end of a wooden spoon for potatoes. A ricer or a sieve "
     "and the back of a spoon gives a smoother mash than a masher ever does, which is what you "
     "want for gnocchi."),
    ("cake tin", ("cake tins", "round tin", "springform tin", "tins"),
     "A roasting tin lined with paper works: bake it as a traybake at the same temperature, "
     "checking five minutes earlier, and cut it into squares. A deep frying pan with a lid will "
     "bake a shallow cake on the hob if the lid goes on and the heat stays low."),
    ("loaf tin", ("loaf tins", "bread tin"),
     "A roasting tin or a deep ovenproof saucepan lined with baking paper. Free-standing bread "
     "bakes perfectly well on a lined tray; the tin is there for the shape, and a round loaf "
     "tastes the same."),
    ("baking parchment", ("parchment", "greaseproof paper", "baking paper", "silicon paper"),
     "Grease the tin well with butter and dust it with flour, or use a silicone mat, or foil "
     "brushed with oil. Parchment and greaseproof paper are not the same thing: greaseproof "
     "sticks to a cake, so grease it again on top if that is all you have."),
    ("cling film", ("clingfilm", "plastic wrap", "saran wrap"),
     "A plate over the bowl, or a clean damp tea towel, keeps a surface from drying. For dough "
     "left to rise, an upturned bowl over the whole thing is better than film anyway."),
    ("muslin", ("muslins", "cheesecloth", "jelly bag"),
     "A clean tea towel, a new J-cloth or a pair of clean tights works for jelly and for "
     "straining yoghurt. Scalding the cloth first with boiling water keeps it from tasting of "
     "soap, and hang it over a bowl with the corners tied to a cupboard handle."),
    ("piping bag", ("piping bags", "icing bag"),
     "A freezer bag with a corner snipped off, or a sheet of baking paper rolled into a cone and "
     "taped. A good zip-lock bag will take a star nozzle if you cut the corner to its width."),
    ("skewers", ("skewer", "kebab sticks", "bamboo skewers"),
     "Rosemary stems stripped of their leaves make fine skewers for lamb and chicken, and metal "
     "kebab sticks or a cake tester do the testing job. To test a cake, a knife blade or a "
     "strand of dry spaghetti works as well as a skewer."),
    ("thermometer", ("thermometers", "meat thermometer", "sugar thermometer"),
     "For meat, press the thickest part with a finger: springy and firm is done, soft is not. A "
     "knife pushed in and pulled out shows the juice running clear for chicken, and for sugar "
     "the old test is a drop in cold water - a soft ball for fudge, a hard crack for toffee."),
    ("funnel", ("funnels",),
     "A corner of baking paper, or the top half of a plastic bottle cut off and turned upside "
     "down. For jam into a jar, a jug with a spout and a steady hand beats both."),
    ("mortar and pestle", ("pestle and mortar", "mortar", "pestle"),
     "A bowl and the end of a rolling pin crushes spices, or put them in a bag and roll over it "
     "with a tin. Whole spices toasted in a dry pan first crush far more easily, whatever you "
     "crush them with."),
    ("slotted spoon", ("slotted spoons",),
     "A fork, or a normal spoon held back against the side of the pan as you lift, drains the "
     "same. A fish slice with holes does the job for anything bigger than a pea."),
    ("tongs", ("tongs", "tongs"),
     "Two forks back to back, or a spatula and a spoon. Chopsticks are the best stand-in there "
     "is for turning small things in a hot pan."),
    ("pastry brush", ("pastry brushes", "basting brush"),
     "Your fingertips for milk or egg wash, the back of a spoon for oil, and a scrunched piece "
     "of kitchen paper for glazing a pie. None of them shed bristles, which is the one thing "
     "the brush is for."),
    # --- the appliances that are not there ----------------------------------------------
    ("fridge", ("fridges", "refrigerator", "refrigerators"),
     "Buy little and often and keep what has to stay cold in the coolest place you have: a lidded "
     "box in the garage, a bucket of cold water with a cloth over it for milk, and a windowsill "
     "on the shady side in winter. Cooked food is the one thing not to push - eat it the day you "
     "make it, and keep the shopping to what fits in one bag."),
    ("freezer", ("freezers", "freezer compartment"),
     "Cook for the day rather than the week and keep nothing back: without freezing, leftovers "
     "are good for two days in the coldest spot you have and then they go. A cool box with ice "
     "packs buys you a day for meat, and a bag of ice in a bowl does for chilling a drink."),
    ("kettle", ("kettles", "electric kettle"),
     "A saucepan of water on the hob boils in about the same time, and a microwave does a mug in "
     "ninety seconds. For tea, pour the pan water while it is still at a rolling boil; a thermos "
     "keeps a litre hot for hours if you want it ready."),
    ("hob", ("hobs", "stove", "stovetop"),
     "A hob alone cooks more than people think: pasta, rice, stews, curries and anything in a "
     "covered pan, plus a great deal of fish and veg. What it cannot do is brown a crust, so "
     "finish under the grill if there is one - a tray bake is the other way to get an oven-ish "
     "result with no oven."),
    # --- the cupboard under the stairs and the garden shed ------------------------------
    ("plunger", ("plungers", "sink plunger", "toilet plunger"),
     "Fill the bowl with enough water to cover the cup and use the flat of your hand, or a "
     "flat-bottomed cup held upside down, in short hard pushes over the plughole. Seal the "
     "overflow with a wet cloth first or the push escapes up it; if the water is not draining "
     "at all, go straight to the trap underneath with a bucket."),
    ("mop", ("mops", "floor mop"),
     "A cloth and a bucket: work backwards to the door, wringing as you go, and a dry towel "
     "under your feet dries the last of it. On a small floor a sponge and a bowl is quicker "
     "than a mop anyway."),
    ("hoover", ("hoovers", "vacuum", "vacuum cleaner", "vacuums"),
     "A broom or a stiff brush for a hard floor, and a damp rubber glove or a damp cloth for "
     "hair on carpet - it gathers in one swipe. A lint roller lifts crumbs and pet hair off a "
     "sofa or a stair carpet."),
    ("stepladder", ("stepladders", "step ladder", "ladder", "ladders"),
     "Borrow a proper ladder rather than stand on a chair, a bucket or a table: a fall from "
     "kitchen-counter height is how most DIY injuries happen, and the ceiling can wait. A "
     "neighbour, a friend or a hire shop for the afternoon is the cheap version."),
    ("drill", ("drills", "power drill", "cordless drill"),
     "Self-adhesive hooks take anything light, and a bradawl or a strong nail and a hammer "
     "starts a hole in plasterboard and soft wood. For masonry, borrow a drill: a nail in "
     "brick either bends or takes a lump of the wall with it."),
    ("hammer", ("hammers", "mallet", "mallets"),
     "A block of scrap wood or the heel of a heavy shoe taps in panel pins and small tacks "
     "without marking the surface. For anything bigger than that, wait, or borrow one: a "
     "saucepan is heavier than it looks and dents both the pan and the wall."),
    ("spirit level", ("level", "levels", "bubble level"),
     "A phone has a level in it, and a clear bottle half full of water on its side reads the "
     "same way: the bubble sits between the two marks. For a shelf, measure down from the "
     "ceiling at both ends - a shelf that matches the ceiling looks level even when it isn't."),
    ("stud finder", ("stud finders", "stud detector"),
     "Knock along the wall with a knuckle: a hollow tap is plasterboard with nothing behind it "
     "and a dull thud is a stud. A small magnet run across the wall finds the screws holding "
     "the board, and the stud is either side of them."),
    ("garden strimmer", ("strimmer", "strimmers", "weed whacker", "weed trimmer"),
     "Shears, or a pair of long-handled edging shears, cut the same grass at the edges and cost "
     "nothing to run. Cut little and often rather than letting it get long - long grass wraps "
     "round any machine, including the borrowed one."),
)


def _words(reading):
    """The line's words, in whatever shape the understanding engine handed them over."""
    words = (reading or {}).get("words")
    if isinstance(words, (list, tuple)):
        return [str(word).lower() for word in words]
    text = str((reading or {}).get("clean") or "").lower()
    return text.split()


def _the_word_for(row):
    """The name to say in the reply: the person's own word when they used a variant of it."""
    return row[0]


def _no_kit(memory, reading):
    """What stands in for the tool the line is missing, or "" when it names none.

    The longest name wins, the way a cook would read it: "potato masher" is the masher and not
    a potato, and a "loaf tin" is the tin and not the bread. The reply names the tool back to the
    person only when it is a one-word tool, because "a clean tea towel, or the pan's own lid" is
    the answer to "no colander" without repeating the word.
    """
    text = " " + str((reading or {}).get("clean") or "").lower() + " "
    words = set(_words(reading))
    best = None
    for row in STAND_IN:
        # the tool's own name first, then the words a person uses for it - the name is the one
        # in the reply's own sentence, and leaving it out matched "colanders" but not "colander"
        for name in (row[0],) + row[1]:
            if " " in name:
                if name in text and (best is None or len(name) > best[0]):
                    best = (len(name), row)
            elif name in words and (best is None or len(name) > best[0]):
                best = (len(name), row)
    if best is None:
        return ""
    return best[1][2]


# A gerund after "without" is the manner of the job, not a thing the person has not got: "how do
# i drill into tiles without cracking them" and "how do i cut an onion without crying" were both
# answered with a stand-in, because "without" is the row's own ask word and nothing checked what
# came after it. "without a rolling pin" and "without using a whisk" still are shortages, so the
# test is the shape of the clause: a bare -ing word is a way of doing it, while "using", "having"
# and the other words in the next tuple still say a thing is missing.
#
# It is a guard and not a list of phrase words because the words after "without" are endless -
# cracking, chipping, streaking, crying, kneading - while the shape of the clause is always the
# same. An avoid phrase is also read loosely, so "without a whisk" and "without a sharpener" would
# have had to be spelled out one at a time.
_WITHOUT_A_MANNER = re.compile(r"\bwithout\s+(?:\w+ly\s+)?([a-z]+ing)\b")
# ...unless the -ing word is one that means "a tool is still missing" rather than "do it this way"
_A_TOOL_IS_STILL_MISSING = frozenset((
    "using", "having", "needing", "buying", "owning", "spending", "paying", "borrowing",
))


def _is_a_shortage(reading):
    """True when the line is about a tool that is not there, so the table may answer it."""
    text = " " + str((reading or {}).get("clean") or "").lower() + " "
    manners = [match.group(1) for match in _WITHOUT_A_MANNER.finditer(text)]
    if not manners:
        return True
    # "without using a whisk" is still a whisk that is not there; "without cracking them" is not
    return not all(word not in _A_TOOL_IS_STILL_MISSING for word in manners)


ENTRIES = [
    # One row for the whole table: the gate is the ask, the tool is the key, and the reply comes
    # back from the table by the name the line used. A row per tool would be 33 copies of the
    # same 60 words of ask, and the ask is the half that gets edited.
    entry("no-kit",
          (tuple(name for row in STAND_IN for name in row[1]), NO_KIT_ASK),
          _no_kit,
          # a tool that is broken, being bought, being cleaned or being explained is not a tool
          # that is missing
          avoid=NOT_A_SHORTAGE,
          guard=_is_a_shortage,
          bias=2),
]
