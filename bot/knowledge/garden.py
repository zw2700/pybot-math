"""Gardens and plants: the everyday jobs that decide whether things grow.

The answers lane owns this domain. One Entry per problem or job, keyed by the plant and the
symptom or task, so "my basil leaves are going yellow", "why are my basil leaves yellow" and
"is my basil overwatered" reach the same answer. Each reply says what is most likely wrong
and the one thing to change first, because most of these have a single cause.
"""
import re

from .lookup import DISH_ASK, RING_AS_A_CALL, entry

ANSWERS = ("garden-and-plants",)

# A plant is as often reported as a state as asked about with a verb: "my brambles are taking
# over", "the hedge is overgrown", "the laurel is out of control", "my roses have gone wild".
# Nothing in those lines says cut, prune or when, so every cutting row missed them and the state
# was echoed back ("Your brambles are taking over - noted") or, for "my hedge is out of control",
# read as a job wearing the person down. These are the words for a plant that has got the better
# of the space; each row that answers what to do about one takes them in its state half.
# "small" is in the not-fruiting key because people say "the fruit is small", but "a small
# garden" and "a small space" say where the plant is going, not what the fruit did.
_SMALL_PLACE = re.compile(r"\bsmall\b\s+(?:garden|gardens|space|plot|patio|balcony|yard|"
                          r"allotment|greenhouse|windowsill|window box|pot|pots|veg patch|"
                          r"vegetable patch|veg plot|back yard)")


def _a_small_place_ask(understood):
    """True when "small" is about the garden rather than the fruit: those are the growing rows'."""
    reading = understood if isinstance(understood, dict) else {}
    line = " ".join(str(reading.get(key) or "") for key in ("clean", "norm_text", "plain")).lower()
    return not _SMALL_PLACE.search(line)


GONE_WILD = ("overgrown", "over growing", "out of control", "gone wild", "gone mad",
             "gone rampant", "gone berserk", "out of hand", "getting out of hand",
             "taking over", "taken over", "takes over", "took over", "taking it over",
             "rampant", "running riot", "gone everywhere", "spreading everywhere",
             "a mess", "is a jungle", "needs cutting back", "needs cutting",
             "needs trimming", "needs a cut", "needs taming", "needs bringing back",
             "getting too big", "got too big", "taken the garden over", "taking the garden over")

# A symptom on its own is not a houseplant. Two words in one alternative ("little flies", "brown
# spots", "tall and thin") already cover the two positions a key needs, so without this the fly
# entry answered "little black flies in my kitchen" and the spot entry answered a line about a
# rash. The pot is what makes the line about a houseplant; the symptom words stay as they are.
INDOORS = ("plant", "plants", "houseplant", "house plant", "house plants", "pot", "pots",
           "compost", "soil", "potting", "indoor", "indoors", "windowsill", "leaves", "leaf",
           "stems", "fern", "ferns", "orchid", "orchids", "monstera", "cactus", "cacti",
           "succulent", "succulents", "peace lily", "snake plant", "spider plant", "basil",
           "herb", "herbs", "calathea", "pothos", "aloe", "dracaena", "palm", "geranium",
           "african violet", "christmas cactus", "hoya", "amaryllis", "cyclamen")



# A lawn with a colour word in the line is asking about the patches, so that answer comes first;
# a lawn that is only being mown or fed gets the order the rest of the answer reads in. Same two
# paragraphs, put in the order the line asked for.
_LAWN_MOW = ("Mow little and often in the growing season, not shorter than about 4cm, and leave the "
             "clippings off unless it is long.")
# "the grass in my garden is dead" was a shrug: a brown lawn in a dry summer is dormant far more
# often than it is dead, and the test is a tuft in the hand rather than the colour.
_LAWN_DEAD = ("A brown lawn is usually dormant rather than dead, so check before you dig it up: "
              "pull a tuft - if the roots hold and there is green at the base it will come back "
              "after a week of deep watering, and if the tuft lifts like a mat it has gone. Dead "
              "patches want the old grass raked out and reseeded in early autumn, when the ground "
              "is warm and the rain does the watering.")
_LAWN_COLOUR = ("Yellow or brown patches in dry weather are usually thirst - water deeply once a "
                "week in a dry spell rather than a sprinkle daily - and thin pale grass in spring "
                "wants a feed rather than a reseed.")
_LAWN_REST = ("Scarify and aerate in autumn, reseed bare patches, and water deeply once a week in "
              "dry spells rather than a sprinkle daily.")
# "How do I make my grass greener" is a feeding question, not a patch question: the answer is food
# and water, and it leads, because a hungry lawn is the usual reason it looks dull.
_LAWN_GREEN = ("Deeper green comes from feeding and watering rather than from seed or a spray: a "
               "spring lawn feed with nitrogen in it, and a deep soak once a week in dry weather "
               "instead of a daily sprinkle.")
_LAWN_REST_SEED = "Scarify and aerate in autumn, and reseed the bare patches."
# Aerating and scarifying are the two lawn jobs people ask for by name, and each one was answered
# with a sentence that only mentioned it in passing: "how often should i aerate the lawn" got the
# watering rule, and "how often should i scarify the lawn" got mowing. Each job gets the answer it
# asks for, with when, how often and what to do after.
_LAWN_AERATE = ("Aerate once a year, in early autumn while the grass is still growing and the "
                "ground is soft: push a garden fork in about 10cm deep at 15cm intervals and rock "
                "it back, which is enough for most lawns, or hire a hollow-tine machine for "
                "compacted clay or a lawn that people walk on all summer. Brush sharp sand or a "
                "top dressing into the holes afterwards, leave the plugs on the grass to break "
                "down, and water it if the weather stays dry for a week. A lawn that is bad enough "
                "to want aerating twice a year wants the thatch scarified out first, a fortnight "
                "before.")
_LAWN_RESEED = ("Reseed in early autumn, or in spring once the soil has warmed up: fork the bare "
                "patch over to loosen it, rake it level, scatter the seed at the rate on the box, "
                "and press it in with a board or the back of a rake so it is in contact with the "
                "soil. Keep it damp for a fortnight - a light sprinkle morning and evening beats "
                "one soak - and keep off it until the new grass is about 5cm tall.")
_LAWN_SCARIFY = ("Scarify in early autumn, or in spring on a lawn that has gone spongy: set a "
                 "spring-tine rake or a machine to just touch the surface and pull the dead "
                 "thatch out in two passes, one way across the lawn and one up and down, taking "
                 "off no more than a centimetre at a time. Clear what comes up, water it if the "
                 "weather stays dry, and feed it a fortnight later rather than the same day. Once "
                 "a year is plenty, and a lawn with less than a centimetre of thatch does not "
                 "need it at all.")


# A raised bed is one box with five questions in it - how deep, what goes in the bottom, what to
# fill it with, what it can sit on and what to build it from - and every one of them was arriving
# somewhere else. The depth, the cardboard and the mix are the same in all five answers, so the
# reply reads the line for which one was asked.
_A_RAISED_BED_BOTTOM = ("bottom", "cheap", "cheaply", "cost", "fill it", "fill the", "filling",
                        "what goes in", "put in", "line", "line it", "lining", "cardboard",
                        "logs", "twigs", "leaves", "rubble", "gravel", "layer", "layers",
                        "newspaper", "free", "for free", "bulk")
_A_RAISED_BED_GRASS = ("grass", "lawn", "turf", "weeds", "dig", "digging", "no dig")
_A_RAISED_BED_PAVING = ("paving", "concrete", "patio", "slabs", "slab", "driveway", "decking",
                        "tarmac", "on the ground")
_A_RAISED_BED_GROW = ("what can i grow", "what to grow", "grow in", "plant in", "grow this",
                      "what will grow", "what should i grow", "crops", "vegetables in", "veg in")
_A_RAISED_BED_SOIL = ("soil", "compost", "topsoil", "loam", "mix", "manure", "grit", "sand",
                      "multipurpose")
_A_RAISED_BED_AMOUNT = ("how much", "how many bags", "how many litres", "volume", "calculate",
                        "work out", "cubic", "tonne", "tonnes", "bulk bag")
_A_RAISED_BED_DRY = ("dries out", "drying out", "dried out", "dry out", "water", "watering",
                     "water it", "wilt", "wilting", "mulch")
_A_RAISED_BED_BUILD = ("build", "make", "wood", "timber", "sleepers", "sleeper", "bricks",
                       "brick", "materials", "cost", "cheap", "should i use", "treated")


def _a_raised_bed(memory, understood):
    """The raised-bed question that was actually asked, with the depth and the mix in it."""
    said = _words(understood)
    if any(_has(said, word) for word in _A_RAISED_BED_AMOUNT):
        return ("Work it out as a volume: length times width times depth, all in metres, and add "
                "a tenth for settling. Bulk loam-based compost from a builders' merchant is far "
                "cheaper than bags, and two parts topsoil to one part compost fills it better "
                "than pure compost, which sinks.")
    if any(_has(said, word) for word in _A_RAISED_BED_DRY):
        return ("A raised bed dries out much faster than the ground, because the roots are above "
                "it on all four sides: water when the top 2cm is dry, a good soak twice a week in "
                "summer rather than a daily sprinkle, and a mulch of compost or grass clippings "
                "holds it. Thirty centimetres of soil holds far longer than fifteen.")
    if any(_has(said, word) for word in _A_RAISED_BED_BOTTOM):
        return ("Line the bottom with cardboard to smother the weeds, then fill it free: logs, "
                "twigs, leaves and any garden waste you have, then two parts topsoil to one part "
                "compost on top. Skip rubble, gravel and plastic, and keep it no wider than about "
                "1.2m so you can reach the middle from both sides without standing on the soil.")
    if any(_has(said, word) for word in _A_RAISED_BED_GRASS):
        return ("Straight onto the grass with no digging: mow it short, lay cardboard or four "
                "layers of newspaper over the whole footprint, soak it, and fill on top - the "
                "grass dies underneath and the worms pull it in. Keep it no wider than about 1.2m "
                "so you can reach the middle from both sides.")
    if any(_has(said, word) for word in _A_RAISED_BED_PAVING):
        return ("On slabs or concrete it needs no cardboard and no digging: stand the frame on "
                "the paving, leave a gap at the bottom edge so water runs off, and be ready to "
                "water more, because a bed on slabs dries out faster than one on soil. Twenty "
                "centimetres of soil is enough for salad, herbs and dwarf beans.")
    if any(_has(said, word) for word in _A_RAISED_BED_GROW):
        return ("In twenty centimetres of soil: salad, herbs, radishes, dwarf beans, onions and "
                "carrots. Potatoes, tomatoes, courgettes and anything tall want forty or more, "
                "because their roots and their water need the depth. Keep it no wider than about "
                "1.2m so you can reach the middle from both sides without standing on the soil.")
    if any(_has(said, word) for word in _A_RAISED_BED_SOIL):
        return ("Fill it with a mix of topsoil and compost rather than pure compost, which dries "
                "out and sinks: two parts topsoil to one part compost, and a handful of grit if it "
                "holds water. Twenty centimetres is enough for salad, herbs and dwarf beans, "
                "thirty for carrots, onions and beetroot.")
    if any(_has(said, word) for word in _A_RAISED_BED_BUILD):
        return ("Untreated timber is fine and cheap and lasts about five years; tanalised timber "
                "8 to 10 years; old bricks or paving slabs cost nothing and last longer, and "
                "creosoted railway sleepers stay away from anything you eat. Keep it no wider than "
                "about 1.2m so you can reach the middle.")
    return ("Twenty centimetres deep does salad, herbs and dwarf beans; thirty for carrots, onions "
            "and beetroot; forty or more for potatoes and tomatoes. Untreated timber is fine and "
            "cheap, line the bottom with cardboard to smother the weeds, and fill it with a mix of "
            "topsoil and compost rather than pure compost, which dries out and sinks. Keep it no "
            "wider than about 1.2m so you can reach the middle from both sides without standing on "
            "the soil.")


def _words(understood):
    """The line as one lower-case string with single spaces, for the small word tests below."""
    return " " + re.sub(r"[^a-z0-9' ]+", " ", str((understood or {}).get("clean")
                                                  or (understood or {}).get("text")
                                                  or "").lower()) + " "


def _has(line, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", line) is not None


# A garden job is asked for in two shapes and they want the two halves in the other order: "how
# do i take cuttings" wants the way of it, "when do i take cuttings" wants the month, and a card
# that holds both puts its date in the last sentence where the person who asked for it never looks.
# The test is the same for every job, so it is written once.
_WHEN_ASKS = ("when", "what month", "which month", "what time of year", "time of year",
              "best time", "what time", "month", "season", "what week",
              # "how often should i cut basil" is the same interval question as "when do i cut
              # basil": once a fortnight from June is the date answered as a rate
              "how often", "how frequently", "how regularly", "when in the year")


def _asks_when(line):
    """True when the line wants a date rather than a method: "when do i prune thyme"."""
    return any(_has(line, word) for word in _WHEN_ASKS)


def _cutting_reply(memory, understood):
    """The cuttings answer, with the season in front when the line asks when to take one."""
    body = ("Cut a shoot about 8 to 10cm long just below a leaf joint, strip the bottom leaves "
            "off, and push it into a small pot of damp, gritty compost, then a clear bag over the "
            "top holds the moisture in. Bright light, out of direct sun, and most soft cuttings - "
            "geraniums, fuchsias, penstemons, herbs - root in two to four weeks; tug one gently and "
            "it holds when there are roots. Geraniums, busy lizzies and pothos also root in a glass "
            "of water changed every few days, and a spider plant does the job for you: the "
            "plantlets on the long runners are ready to pot up once they have roots 2cm long, "
            "still attached to the parent if you like.")
    # "when do i take cuttings" asks for the season as well as the method, so the timing goes first
    if _asks_when(_words(understood)):
        return ("Late spring to early summer, when the new growth has firmed at the base but still "
                "bends - May and June for most shrubs. " + body)
    return body
# The words a line has to say itself before the "make it look better" card may answer. The
# reading carries a topic from turns back, so a line that has moved on - "she likes gardening but
# she is in a flat with no garden", then "so what should i do" - was arriving at a card about
# borders that the person had already said they do not have.
_GARDEN_IN_THE_LINE = ("garden", "gardens", "border", "borders", "flowerbed", "flowerbeds",
                       "plot", "yard", "outdoor", "outdoors", "front", "back", "lawn",
                       "allotment", "outside", "flower bed", "flower beds")


def _names_the_garden(understood):
    """True when this line says the garden, not when a topic from earlier turns does."""
    said = " " + re.sub(r"[^a-z0-9' ]+", " ", str((understood or {}).get("text") or "").lower()) + " "
    return any(_has(said, word) for word in _GARDEN_IN_THE_LINE)


# The rot words are the same ones a loaf, a spread of cheese and a joint of meat use, and the
# garden row outranks the kitchen's on them: "my bread has gone mouldy can i cut it off" was told
# to pick the affected fruit off and bin it, and so was the same line about cheese. A kitchen noun
# with no plant word in the line is the kitchen's question, so the crop row stands down for it.
# The garden noun test is there for the houseplants and crops that borrow the word - a cheese
# plant is a monstera, and tomatoes and potatoes are still grown outside.
_KITCHEN_ROT = ("cheese", "bread", "loaf", "loaves", "toast", "jam", "meat", "ham",
                "bacon", "sausage", "mince", "chicken", "fish", "salmon", "milk",
                "butter", "cream", "yoghurt", "yogurt", "leftovers", "sandwich", "pasta",
                "rice", "soup", "sauce", "gravy", "cake", "biscuit")
_GROUND_THING = ("plant", "plants", "crop", "crops", "fruit", "fruits", "seedling",
                 "seedlings", "greenhouse", "allotment", "vine", "vines", "tree", "trees",
                 "leaf", "leaves", "root", "roots", "compost", "soil", "ground", "pot",
                 "pots", "bed", "beds", "garden", "flower", "flowers")


def _a_kitchen_thing(understood):
    """True when the line is food in the kitchen, not a crop still growing or just lifted."""
    line = _words(understood)
    if not any(_has(line, word) for word in _KITCHEN_ROT):
        return False
    return not any(_has(line, word) for word in _GROUND_THING)


# A leaf word is a question about the leaves, and "at the bottom" is where the lowest leaves are.
# Without a black or rotting word in the line, the leaf is the subject and blossom end rot is not:
# "my tomato plants have yellow leaves at the bottom" was told the fruit had rot.
_LEAF_WORDS = ("leaf", "leaves", "yellow", "yellowing", "yellowed", "pale", "veins",
               "curling", "curled", "curl", "limp", "drooping")
_A_FRUIT_THAT_ROTS = ("black", "brown", "rot", "rots", "rotting", "rotten", "sunken", "squashy",
                      "squishy", "mushy", "patch", "patches", "blossom end", "end rot", "eaten",
                      "hole", "holes")


def _a_leaf_problem_not_the_fruit(understood):
    """True when the line names the leaves and says nothing about the fruit going black."""
    line = _words(understood)
    if not any(_has(line, word) for word in _LEAF_WORDS):
        return False
    return not any(_has(line, word) for word in _A_FRUIT_THAT_ROTS)


def _lawn(memory, understood):
    """The lawn answer, in the order the line asks for it. A question about a colour or a patch is
    about the patches, so that sentence leads; a mowing or a watering question opens with mowing
    and keeps the short answer it had, without the colour sentence it did not ask about."""
    line = " " + re.sub(r"[^a-z0-9' ]+", " ", str(understood.get("clean") or understood.get("text")
                                                        or "").lower()) + " "
    colour = ("yellow", "yellowing", "brown", "browning", "patchy", "patches", "dying",
              "dead", "died", "killed")
    # a lawn that is pale, dull or washed out wants feeding, which is the greener answer, not the
    # patches one: "the grass looks dull" and "my lawn is pale and yellowish" are that question
    green = ("green", "greener", "greenest", "lush", "thicker", "thick", "dull", "pale",
             "washed out", "faded", "tired", "yellowish", "pale green", "not very green", "thin",
             "feed", "feeding", "fertiliser", "fertilizer", "starved")
    # a lawn job asked for by name is that job's question, whatever else the line says: "how
    # often should i aerate the lawn" is not a mowing question and not a watering one
    if any(_has(line, word) for word in ("aerate", "aerating", "aeration", "aerated",
                                         "spiking", "spike", "hollow tine", "hollow tines",
                                         "compacted", "compaction")):
        return _LAWN_AERATE
    if any(_has(line, word) for word in ("scarify", "scarifying", "scarified", "scarifier",
                                         "dethatch", "dethatching", "thatch", "thatching",
                                         "spongy", "raking out")):
        return _LAWN_SCARIFY
    if any(_has(line, word) for word in ("reseed", "reseeding", "re seed", "oversow", "over sow",
                                         "sow grass", "grass seed")):
        return _LAWN_RESEED
    if any(_has(line, word) for word in green) and not any(_has(line, word) for word in colour):
        return " ".join((_LAWN_GREEN, _LAWN_MOW, _LAWN_REST_SEED))
    # "my lawn is dead in patches" has already said where it is brown, so the thirst-and-feed
    # answer is the more useful next step than the tuft test: the drought row owns patches, the
    # dead row owns the whole lawn (@orange-salmon, #3826).
    if any(_has(line, word) for word in ("patch", "patches", "patchy", "in places",
                                         "here and there")):
        return " ".join((_LAWN_COLOUR, _LAWN_MOW, _LAWN_REST_SEED))
    if any(_has(line, word) for word in ("dead", "died", "killed")):
        return " ".join((_LAWN_DEAD, _LAWN_REST_SEED))
    if any(_has(line, word) for word in colour):
        return " ".join((_LAWN_COLOUR, _LAWN_MOW, _LAWN_REST_SEED))
    return " ".join((_LAWN_MOW, _LAWN_REST))


# --- the brassicas: four crops, one sowing row, four different harvest signs ----------------
# A brassica row is one sowing answer but not one harvest answer: the sign that a cabbage is ready
# says nothing about a cauliflower, so each crop has its own sentence and the crop the line names
# is the one that leads.
BRASSICA_HARVEST = {
    "broccoli": ("Cut broccoli while the head is still tight and green, before any yellow shows: "
                 "about ten to twelve weeks after planting out for a summer kind. Cut the central "
                 "head first with 10cm of stem, then the side shoots over the weeks after."),
    "cauliflower": ("Cut a cauliflower when the curd is still tight and white, ten to sixteen weeks "
                    "after planting out: bend the outer leaves over the head to keep it white, and "
                    "cut it before the curd loosens or looks grainy."),
    "sprouts": ("Pick sprouts from the bottom of the stalk upwards from October, after a frost or "
                "two, twisting each one off when it is tight and walnut-sized. The stalk goes on "
                "producing upwards for weeks, and the tops are eaten as spring greens."),
    "kale": ("Pick kale leaf by leaf from the top of the plant, never more than a third at once, "
             "and it goes on cropping all winter; the young leaves at the crown are the tender "
             "ones."),
    "cabbage": ("Cut cabbages when the heart is firm: spring and summer kinds about three months "
                "after planting out, winter ones from October. Cut rather than pull, so the stump "
                "can throw a second small head."),
}


def _brassica_harvest(memory, understood):
    """The harvest sign for the brassica the line names, not for the first one in the row."""
    line = _words(understood)
    for crop in ("broccoli", "cauliflower", "sprouts", "sprout", "kale", "cabbage"):
        if _has(line, crop):
            return BRASSICA_HARVEST["sprouts" if crop == "sprout" else crop]
    return " ".join(BRASSICA_HARVEST[crop] for crop in ("cabbage", "sprouts", "kale"))


# --- when to sow -------------------------------------------------------------------------
# "When do I plant potatoes" is the same question whatever the crop, so the crops are a table
# and one loop, not one entry written by hand. Each row: the words people use for the crop, the
# month window where it goes in the ground, and what to do that catches most people out.
SOW_ASK = ("when", "plant", "planting", "planted", "sow", "sowing", "sowed", "month", "months",
           "time of year", "best time", "what time", "early", "late", "too late", "too early",
           # "how do i grow potatoes from seed" is the seed-potato question, and the crop's own
           # row is the answer; the phrase is the whole job, so a question about what a seed does
           # ("does a seed need light to grow") still misses it
           "from seed", "seed potatoes", "seed potato")
# A crop that is sick, eaten or not coming up is a different question, and the entries below
# answer those. The harvest words are not here: they stand the sowing row down through its own
# avoid list, so that "when do i lift parsnips" keeps the harvest row.
SOW_NOT = ("yellow", "yellowing", "dying", "wilting", "drooping", "blight", "rot", "rotting",
           "mould", "mold", "pests", "slugs", "snails", "caterpillars", "holes", "eaten",
           "not growing", "failed", "tiny", "small", "came up", "come up", "no shoots",
           "not sprouted", "nothing sprouted", "rotten", "mouldy", "digging",
           "store", "storing", "chit", "chitting", "container", "pot", "pots",
           "indoor", "indoors", "windowsill", "greenhouse", "allotment", "raised bed")


# A courgette and a pumpkin share one sowing row and nothing else: one is picked small and
# often, the other is left until the skin hardens, so the crop the line names leads.
COURGETTE_HARVEST = (
    "Pick courgettes from July when they are 10 to 15cm long, and go over the plants every day "
    "in warm weather: one left to swell to marrow size stops the plant producing. Cut them with "
    "a short stalk and eat them within a few days.")
PUMPKIN_HARVEST = (
    "Pumpkins and squash are ready in September or October, when the skin has hardened so a "
    "fingernail will not mark it and the stalk has gone corky: cut with a long handle, cure them "
    "in the sun for a week, and they keep for months somewhere dry.")
BEAN_HARVEST = (
    "Broad beans are ready when the pods bulge and the beans inside are the size of a thumbnail, "
    "from June: pick from the bottom of the plant upwards and pinch out the tops once the flowers "
    "set, to stop blackfly. Runner and french beans are ready from July, at 15cm, while they are "
    "slim and snap without a string: pick every couple of days or the plants stop setting.")


def harvest_crops():
    """Every crop that has a harvest row, so a cooking method can stand down for one.

    A staple with a harvest row is two questions with one name: "how do i know when my onions are
    ready" is onions still in the ground, and "how do i cook onions" is the pan. The cooking
    method answers the second and asks to be turned down for the first.
    """
    names = set()
    for words, _reply in HARVEST_MORE:
        names.update(words)
    for words, _sow in SOWING:
        if HARVEST.get(words[0]):
            names.update(words)
    return names


def _courgette_harvest(memory, understood):
    """A pumpkin is not a courgette that was left too long."""
    line = _words(understood)
    if _has(line, "pumpkin") or _has(line, "pumpkins") or _has(line, "squash"):
        return PUMPKIN_HARVEST
    return COURGETTE_HARVEST


def _bean_harvest(memory, understood):
    """Broad beans crop a month before the runners, so the line that names them leads."""
    line = _words(understood)
    if _has(line, "broad") or _has(line, "broad bean") or _has(line, "broad beans"):
        return ("Broad beans are ready from June, when the pods bulge and the beans inside are "
                "the size of a thumbnail: pick from the bottom of the plant upwards, and pinch "
                "out the tops once the flowers have set to stop blackfly. Runner and french "
                "beans follow from July.")
    return ("Runner and french beans are ready from July: pick them at 15cm while they are slim "
            "and snap without a string. Broad beans are a month earlier, when the pods bulge. "
            "Pick every couple of days or the plants stop setting.")


# The other half of the same table: "when do i pick them" wants the harvest window and the sign
# that says it is ready, which is a different sentence from the sowing one for every crop.
HARVEST_ASK = ("harvest", "harvesting", "lift", "lifting", "dig up", "dig them up", "ready",
               "pick", "picking", "ripe", "when are", "how do i know", "pulling", "pull them",
               # "cut" is the word people use for a cabbage, a cauliflower or a head of broccoli
               # as often as "pick": without it, "when do i cut cabbages" was a sowing question.
               "cut", "cutting", "cut them", "cutting them")
# The shapes a harvest row can be asked in. "how do i harvest my onions" is the same question as
# "when do i harvest my onions", and the cooking module stands its own harvest lines down, so the
# row has to be able to take the how-to as well or the line is handed to nobody.
# "done" is a key and not an ask: "are my potatoes done" is a pan question in a kitchen, and
# cooking.py has the knife test for it. Beside a harvest ask - "how do i know my onions are done" -
# it is the garden's.
HARVEST_KEYS = ("when", "time", "ready", "done", "month", "harvest", "harvesting", "lift",
                "lifting")
HARVEST = {
    "potato": ("Lift new potatoes in June and July, once the flowers open, and maincrops in "
               "September and October when the tops have died back. Fork well beside the row so "
               "you do not spear them, then leave them on the soil for an hour to dry before "
               "storing in paper sacks in the dark."),
    "carrot": ("Pull carrots from June, thinning as you go, and lift the main crop in October "
               "before the first hard frost. They are ready when the shoulder is 2cm across. "
               "Twist the tops off before storing, because leaves keep drawing water, and keep "
               "them in damp sand in a cool shed."),
    "onion": ("Lift onions in July and August when the tops fall over and start to yellow: bend "
              "the tops down, leave them a fortnight on the soil in dry weather, then store in "
              "nets somewhere airy. An onion that is not properly dried is the one that rots "
              "and takes the rest of the sack with it."),
    "lettuce": ("Cut lettuce about eight to twelve weeks after sowing, in the morning when it is "
                "cold and crisp, at the base with a knife, and it will often come again. A "
                "lettuce that has started to shoot up a stem has bolted: pick it at once and eat "
                "it that day, because it turns bitter."),
    "pea": ("Pick peas from June, when the pods are full but still bright green and snap "
            "cleanly, and go along the row every two or three days. Leaving them on the plant "
            "stops it flowering, and a pod left too long goes starchy and tough."),
    "bean": _bean_harvest,
    "beetroot": ("Beetroot is ready eight to ten weeks after sowing, at golf-ball size for "
                 "eating fresh and up to tennis-ball size for storing. Twist the leaves off "
                 "rather than cutting, so it does not bleed, and lift them before the first "
                 "hard frost."),
    "parsnip": ("Lift parsnips from October through to February, and leave them in the ground "
                "until after a frost: the cold turns starch to sugar and they taste far better. "
                "Fork underneath the root rather than pulling, because a parsnip snaps at the "
                "shoulder and the best part stays in the soil."),
    "leek": ("Leeks can be lifted from September and stand in the ground all winter, which is "
             "the point of them: dig as you need them, and they will take hard frost. Earth up "
             "the stems a few weeks before lifting if you want more white."),
    "cabbage": _brassica_harvest,
    "courgette": _courgette_harvest,
    "radish": ("Radishes are ready about four weeks after sowing, at marble size: pull one to "
               "check rather than waiting for the row. Left longer they go woody and hot, so sow "
               "little and often instead of one big row."),
    "swede": ("Swedes are lifted from October, and are better after a frost, which sweetens them "
              "the way it does parsnips; they will stand in the ground into winter. Turnips are "
              "quick - six to eight weeks - and are best pulled small, at 5 to 7cm across."),
}


# The crops people grow for fruit are not in SOWING at all, so the harvest table has a second
# half: a crop that is picked rather than lifted still has a month and a sign that says ready.
HARVEST_MORE = (
    (("garlic",),
     "Lift garlic in July, when the bottom three leaves have yellowed and the rest are still "
     "green: stop watering a fortnight before, ease each bulb out with a fork, and dry them "
     "somewhere airy for two or three weeks before storing. Left in longer the bulbs split and "
     "they keep badly."),
    (("tomato", "tomatoes"),
     "Pick tomatoes from late July as they turn fully red, and take the whole truss in October "
     "before the first frost. Green ones left then will ripen on a windowsill next to a banana. "
     "A tomato is ready when it gives slightly in the hand and smells of tomato."),
    (("apple", "apples"),
     "Apples are ready from August for the earlies and October for the keepers: cup one and twist "
     "- ripe fruit comes away with the stalk on and the pips inside are brown. Pick in dry "
     "weather, use the windfalls first, and store only perfect fruit, in a cool dark place, not "
     "touching."),
    (("pear", "pears"),
     "Pick pears before they are ripe, from late August, while the flesh is still hard: lift one "
     "and twist, and when the stalk parts easily it is ready to finish indoors. A pear left to "
     "soften on the tree goes gritty and rotten at the core."),
    (("plum", "plums", "damson", "damsons"),
     "Plums are ready from August, when they colour up and give a little at the stalk end: pick "
     "with the stalk on and eat the soft ones first. A plum that comes away at a squeeze is over "
     "ripe, and the wasps find those the same day you do."),
    (("strawberry", "strawberries"),
     "Pick strawberries from June, when they are red all over including the tip, and pick with a "
     "short stalk in the cool of the morning. A berry that is pale at the tip will not sweeten "
     "after picking, and one left to rot takes the rest with it."),
    (("raspberry", "raspberries"),
     "Raspberries ripen from July: pick when the berry comes away from its core with no tug, and "
     "eat or freeze them the same day, because they keep a day at most. Autumn kinds crop on into "
     "October."),
    (("rhubarb",),
     "Pull rhubarb from April to the end of June, twisting each stalk out and leaving three on "
     "every crown, then stop: the plant needs the rest of the year to build up for next spring. "
     "Do not pull any in the first year after planting, and never eat the leaves."),
    (("sweetcorn", "sweet corn", "corn", "corn on the cob"),
     "Sweetcorn is ready in August and September: peel back a little husk and press a kernel with "
     "a fingernail - milky juice means ready, clear means wait, doughy means it has gone over. "
     "Cook it within the hour, because the sugar turns to starch fast."),
    (("chilli", "chillies", "chili", "chilies"),
     "Chillies are ready from late summer: pick green for a milder heat, or leave them on to turn "
     "red for the fullest flavour. Cut them with a short stalk and keep picking, because a plant "
     "left to ripen stops setting new fruit."),
    (("pumpkin", "pumpkins", "squash", "squashes"),
     "Pumpkins and squash are ready in September or October, when the skin has hardened so a "
     "fingernail will not mark it and the stalk has gone corky: cut with a long handle, cure them "
     "in the sun for a week, and they keep for months somewhere dry."),
)
# A crop on the plate is the cooking question: "how do i know when my carrots are done" wants
# the time in the pan, and the harvest row is the one that has to stand down for it.
DONE_NOT = ("cooked", "cooking", "boil", "boiled", "boiling", "roast", "roasted",
            "steam", "steamed", "soft", "tender", "mash", "mashed", "al dente")


# "are they done" is two questions for a crop you cook and one for a crop you eat raw: "how do i
# know when my carrots are done" wants the minutes in the pan, but "when are my raspberries done"
# is the pick, and standing the harvest row down for it left the line with nothing at all.
EATEN_RAW = frozenset("""raspberry strawberry blackberry blackcurrant redcurrant gooseberry apple pear
plum damson cherry tomato""".split())


def _done_means_a_pan(crop):
    return () if crop in EATEN_RAW else ("done",)


def _harvest_entries():
    """One row per crop, keyed the same way as the sowing row but only for a harvest question."""
    out = []
    for words, _sow in SOWING:
        reply = HARVEST.get(words[0])
        if not reply:
            continue
        # bias 3: "how do i know when my onions are ready" is the gardener's line, and both the
        # generic when-will-it-be-ready wording and the cooking method for the same vegetable fit
        # it as well as this row does. The row that names the crop and asks when it is ready is
        # the more specific one, so it wins the tie; a line about the pan still comes back to the
        # cooking entry, because the done-words stand this row down.
        out.append(entry("harvest-" + words[0], (words, HARVEST_KEYS),
                         reply, ask=HARVEST_ASK,
                         avoid=SOW_NOT + DONE_NOT + _done_means_a_pan(words[0]), bias=3))
    for words, reply in HARVEST_MORE:
        out.append(entry("harvest-" + words[0], (words, HARVEST_KEYS),
                         reply, ask=HARVEST_ASK,
                         avoid=SOW_NOT + DONE_NOT + _done_means_a_pan(words[0]), bias=3))
    return out

# --- a month in the line settles a sowing question -------------------------------------------
# No crop row may answer for a month outside its own window, or "what can i sow in october" goes
# out with seed potatoes. (1 = January.)
SOW_WINDOW = {
    "potato": (3, 4), "carrot": (3, 7), "onion": (3, 4), "lettuce": (3, 8),
    "pea": (3, 6), "bean": (4, 6), "beetroot": (4, 7), "parsnip": (2, 4),
    "leek": (3, 4), "cabbage": (3, 5), "courgette": (4, 6), "radish": (3, 9),
    "swede": (5, 6),
}

MONTH_NUMBER = {
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
# "may" is the month and the verb, so only the phrases make it a month: "may i plant potatoes" is
# a question about permission, "in may" is a date.
MONTH_PHRASES = ("in may", "of may", "by may", "during may", "this may", "next may")


def _month_named(understood):
    line = _words(understood)
    for word, number in MONTH_NUMBER.items():
        if _has(line, word):
            return number
    if any(phrase in line for phrase in MONTH_PHRASES):
        return 5
    return None


# What goes in the ground in each month, for the questions that name a month and no crop.
SOW_MONTH = {
    1: ("Not much goes in this month: plant garlic and shallots if the ground is not frozen, and "
        "start broad beans under cloches from late January. Chit early potatoes on a windowsill "
        "and order the seed you want for spring."),
    2: ("Broad beans and parsnips from late February, and onion sets and shallots as soon as the "
        "ground is workable. Sow tomatoes and chillies indoors under cover, and chit the early "
        "potatoes."),
    3: ("The month the plot opens: potatoes, carrots, onions, lettuce, peas, leeks, radish and "
        "cabbages all go in from now. Sow a short row every few weeks rather than one big sowing, "
        "so the crop comes over months instead of all at once."),
    4: ("Potatoes by mid-April, then beetroot and beans, courgettes indoors, and more lettuce and "
        "radish every three weeks. Keep fleece to hand: a late frost is the thing that sets April "
        "back."),
    5: ("Once the frost has gone: beans, courgettes, sweetcorn, squash and swede go out, and keep "
        "sowing lettuce and radish for a steady supply. Harden everything off for a week first."),
    6: ("Last chance for runner and french beans, courgettes and swede; keep salad and radish "
        "going. Water in the morning and mulch, because this is the month everything bolts."),
    7: ("Sow for the winter now: spring cabbage, kale, winter salad and more radish and lettuce for "
        "autumn. Lift onions and garlic as the tops fall over."),
    8: ("Spring cabbage, overwintering onion sets and winter salad go in, and the ground cleared of "
        "potatoes can take a green manure. Keep watering the beans and courgettes."),
    9: ("Sow winter salad and land cress, plant overwintering onion sets and garlic, and clear the "
        "spent crops into the compost. This is the month that decides next spring."),
    10: ("Plant garlic and overwintering broad beans for the earliest crop next year, and put in "
         "onion sets and shallots. Outdoors there is little else to sow except winter salad under "
         "cover, so clear and mulch the beds."),
    11: ("Plant garlic and broad beans if the ground is not frozen, mulch the empty beds, and order "
         "seed potatoes to chit after Christmas. Nothing else goes in outdoors."),
    12: ("Nothing goes in outdoors except garlic in a mild spell. Plan next year's rotation, order "
         "your seed, and start chitting early potatoes indoors after Christmas."),
}


def _sowing_reply(crop, reply):
    """A sowing row's answer, standing down for a month outside its own window.

    A crop is the wrong answer for a month it is not sown in. A line that says "too late" or
    "too early" gets the reassurance first, because that is what it asked.
    """
    early, late = SOW_WINDOW.get(crop, (1, 12))

    def answer(memory, understood):
        line = _words(understood)
        month = _month_named(understood)
        if month is not None and not early <= month <= late:
            return None
        if re.search(r"\btoo late\b|\btoo early\b|\blate for\b", line):
            return ("Later than the usual window it still grows, it just crops later and wants "
                    "watering while it catches up. " + reply)
        return reply

    return answer


# "What can i plant now" is the same question as "what can i plant in october" with the date left
# to us: it named no month, so it got a shrug while the month table sat right there. The words
# that mean the date the person is standing in are the month, and the bot knows the month.
NOW_WORDS = re.compile(r"\bnow\b|\bat the moment\b|\bthis month\b|\bcurrently\b|"
                       r"\bthese days\b|\bat the minute\b|\bthis time of year\b")
NEXT_MONTH_WORDS = re.compile(r"\bnext month\b|\bthe month after\b")
MONTH_NAMES = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
               7: "July", 8: "August", 9: "September", 10: "October", 11: "November",
               12: "December"}


# A season named instead of a month was in the key and had nothing behind it, so "what can i
# plant in spring" was a shrug beside a table that knows the answer. One line per season, the
# crops of its months in order, so the ask that names no date at all still gets a list.
SEASON_REPLY = {
    "spring": ("Spring is when the plot fills up: potatoes, carrots, onions, lettuce, peas, leeks "
               "and radish from March, beetroot and beans in April, and courgettes, sweetcorn "
               "and squash once the frost has gone in May. Sow a short row every few weeks "
               "rather than one big sowing."),
    "summer": ("In summer you are sowing for autumn and winter: more lettuce, radish and beetroot "
               "every three weeks, runner and french beans and courgettes until the end of June, "
               "then spring cabbage, kale and winter salad from July. Water in the morning and "
               "mulch, because this is when everything bolts."),
    "autumn": ("Autumn is the sowing for next year: plant garlic, overwintering broad beans and "
               "onion sets, and sow winter salad and land cress under cover. Clear the spent "
               "crops into the compost and mulch the empty beds, because this is the season that "
               "decides next spring."),
    "winter": ("Almost nothing goes in outdoors: garlic and broad beans in a mild spell, and "
               "everything else indoors. Sow tomatoes and chillies under cover from late winter, "
               "chit early potatoes on a windowsill after Christmas, and order the seed you want "
               "for the year."),
}
SEASON_WORDS = tuple(SEASON_REPLY)


def _this_month():
    """The month it is where the person is talking to us, or None if the clock says nothing."""
    try:
        import datetime
        return datetime.date.today().month
    except Exception:
        return None


def _sow_month(memory, understood):
    """What goes in the ground in the month the line names, or in the month it is now.

    Nothing comes back for a line that names no month and no "now": a season or a question about
    the plot in general is somebody else's answer.
    """
    line = _words(understood)
    month = _month_named(understood)
    if month is not None:
        return SOW_MONTH[month]
    for season in SEASON_WORDS:
        if _has(line, season):
            # "what can i plant for winter" is a crop to eat in winter, which is sown in autumn:
            # the winter card is for a line that asks what goes in the ground now, in winter.
            if season == "winter" and re.search(r"\bfor (the )?winter\b|\bover ?winter\b|"
                                                r"\bfor christmas\b|\bbefore winter\b", line):
                return SEASON_REPLY["autumn"]
            return SEASON_REPLY[season]
    if not (NOW_WORDS.search(line) or NEXT_MONTH_WORDS.search(line)):
        return None
    month = _this_month()
    if month is None:
        return None
    if NEXT_MONTH_WORDS.search(line):
        month = month % 12 + 1
    return "It's %s, so here's what goes in. %s" % (MONTH_NAMES[month], SOW_MONTH[month])


SOWING = (
    (("potato", "potatoes", "spuds"),
     "Plant seed potatoes from late March to mid-April, once the soil is workable and no hard "
     "frost is forecast: 30cm apart in rows 60cm apart, 10cm deep, with the sprouts pointing up. "
     "Chit them on a windowsill first, in egg boxes, for six weeks. Earlies go in first, maincrops "
     "by mid-April, and a frost on the young shoots is what sets them back."),
    (("carrot", "carrots"),
     "Sow carrots from late March to July, a few seeds every three weeks rather than one big "
     "sowing, 1cm deep and 5cm apart once thinned. They want a light, stone-free soil: stones "
     "make them fork. Cover the row with fleece or a mesh barrier, because carrot fly finds them "
     "by smell and a barrier is what actually stops it."),
    (("onion", "onions", "shallot", "shallots", "onion sets"),
     "Plant onion sets from mid-March to mid-April, pushing them into firm soil so just the tip "
     "shows, 10cm apart with 30cm between rows. Birds pull them out, so a few short sticks or "
     "netting over the row saves them. Onions want firm ground: tread the bed before planting, "
     "not after, and keep it weeded."),
    (("lettuce", "lettuces", "salad leaves", "rocket", "spinach"),
     "Sow lettuce and salad leaves from March to August, a small pinch every two or three weeks "
     "for a steady supply, 1cm deep and 20cm apart for hearting kinds. They bolt in heat: water "
     "in the morning, shade the row in a hot spell, and pick leaves young. Cut-and-come-again "
     "salad is the easiest thing to grow in a pot."),
    (("pea", "peas", "mangetout", "sugar snap"),
     "Sow peas from March to early June, 5cm deep in a wide flat trench rather than a single "
     "line, 8cm apart, with a net or twiggy sticks up for them to climb. Mice take the seed, so "
     "start them in a gutter of compost if a row disappears. Pick pods every couple of days or "
     "the plants stop producing."),
    (("bean", "beans", "runner beans", "broad beans", "french beans"),
     "Sow runner and french beans from late April to June, once the soil has warmed, 5cm deep "
     "and 20cm apart, after the last frost. Broad beans go in earlier, from February to April, "
     "in a double row. Beans need a frame or cane wigwam from the start, and water at the base "
     "when they flower or the flowers drop."),
    (("beetroot", "beets", "beet"),
     "Sow beetroot from April to July, 2cm deep and 10cm apart, thinning to one plant per station "
     "because each seed cluster holds several. Water regularly: beetroot that dries out goes "
     "woody. You can start in April under cloche and sow again in June for small roots into "
     "autumn."),
    (("parsnip", "parsnips"),
     "Sow parsnips from late February to April, and only fresh seed: parsnip seed dies in a year, "
     "which is why a saved packet comes up empty. Sow 1cm deep, 15cm apart once thinned, on ground "
     "that has not been manured or they fork. They take three weeks to show, so mark the row."),
    (("leek", "leeks", "spring onion", "spring onions"),
     "Sow leeks from March to April in a seedbed, then move them to their final spot in June at "
     "20cm apart, dropping each one into a dibbed hole and watering it in rather than filling the "
     "hole with soil. Spring onions can be sown from March to July, a pinch every three weeks, "
     "and eaten small."),
    (("cabbage", "cabbages", "broccoli", "sprouts", "sprout", "kale", "cauliflower"),
     "Sow cabbage, kale and sprouts from March to May for a winter and spring crop, 1cm deep in a "
     "seedbed, then plant out 45cm apart once they have five or six leaves. Firm the soil hard "
     "around the stem. Net them straight away: pigeons strip a young brassica in a day, and "
     "cabbage white butterflies come later."),
    (("courgette", "courgettes", "zucchini", "squash", "pumpkin", "pumpkins"),
     "Sow courgettes from late April indoors and plant out in late May or June, once nights are "
     "above 10C, 90cm apart: one plant feeds a family. They need sun, rich soil and steady water. "
     "Pick them small, at 10-15cm, because a marrow-sized courgette stops the plant producing."),
    (("radish", "radishes"),
     "Sow radishes from March to September, a pinch every two weeks, 1cm deep and 2cm apart after "
     "thinning, and they are ready in about four weeks. They are the fastest thing in the veg "
     "patch and a good one to sow with children. Dry soil makes them hot and woody, so water "
     "them."),
    (("swede", "swedes", "turnip", "turnips"),
     "Sow swede in May to June and turnips from March to August, 1cm deep and 15cm apart once "
     "thinned; swede needs the whole summer to swell and is best lifted after the first frost. "
     "Club root is the risk in acid soil, so lime the bed the winter before if you have had it."),
    # The two the table was missing, and the two people ask about most indoors: a chilli needs warm
    # soil to come up at all, which is the one thing a first-time grower gets wrong.
    (("chilli", "chillies", "chillis", "chilli pepper", "chilli peppers", "hot pepper",
      "hot peppers", "jalapeno", "jalapenos", "scotch bonnet"),
     "Sow chillies indoors in February or March, half a centimetre deep, at 21C or more: cold seed "
     "does not come up at all, so a warm windowsill or a propagator is the whole trick. Pot them on "
     "as the roots fill the pot, pinch the top out at about 15cm to make a bush, and move them to "
     "the sunniest spot in June. Water when the top of the compost is dry and feed weekly with "
     "tomato feed once the flowers open; pick green for a milder chilli, or leave them to turn red."),
    (("pepper", "peppers", "sweet pepper", "sweet peppers", "bell pepper", "bell peppers",
      "pepper plant", "pepper plants"),
     "Sweet peppers want warmth and a long season: sow indoors in late February or March, half a "
     "centimetre deep, at 20C or more, and pot them on twice before planting out in June in the "
     "sunniest, most sheltered spot you have. Water regularly, because a plant that dries out drops "
     "its flowers, and feed weekly with tomato feed when the first fruit set. Pick them green, or "
     "wait for red, which is sweeter."),
    # The herbs had no sowing row at all, so "when do i sow basil" and "how deep do i sow basil
    # seeds" were both a shrug. Basil and coriander are annuals sown each year; the woody herbs are
    # bought as plants or grown from cuttings, which is faster and what the row says.
    (("basil", "basil seed", "basil seeds", "basil plant", "basil plants"),
     "Sow basil indoors from late April to June, half a centimetre deep and barely covered, at "
     "20C or more: it sulks below 10C, so do not put it outside before June and even then keep it "
     "out of a cold wind. Pinch the tips out as it grows to keep it bushy, and sow a second pot in "
     "July so you have young plants when the first one goes woody."),
    (("parsley", "coriander", "cilantro", "dill", "chervil", "tarragon", "sage"),
     "Sow parsley, coriander and dill from March to July, 1cm deep, in a pot rather than a seedbed "
     "if you only want a windowsill's worth. Parsley is slow - two to three weeks - so keep the "
     "pot damp and be patient; coriander bolts in heat, so sow it little and often and pick the "
     "leaves young. Tarragon and sage are better bought as a plant."),
    (("mint", "mint plant", "mint plants", "mint root", "mint roots"),
     "Mint is not grown from seed: buy a plant, or pull up a piece of root with shoots on it in "
     "spring or autumn and pot it in fresh compost. Stand it in a pot with the rim above the soil, "
     "because a mint in a border takes over, and divide the pot every couple of years when the "
     "stems get thin."),
    (("rosemary", "thyme", "oregano", "oregano plant", "lavender"),
     "Rosemary, thyme and oregano are bought as small plants or grown from softwood cuttings in "
     "summer, not from seed: seed is slow and comes up uneven. They want sun, very free drainage - "
     "grit in the compost, or a gravel mulch - and far less water than basil; a woody herb in wet "
     "soil rots at the base."),
)

# A crop whose own name is also a kitchen word needs a fence of its own: "when do i add pepper"
# and "when do i put the chillies in" are cooking lines, not sowing ones.
# A herb named with a "when" scores as a sowing question even when it is a pruning one, so each
# herb row stands down on the words that mean cutting back. The same words cannot go in SOW_NOT:
# "when do i prune my apple tree" and "when do i trim lavender" have their own answers.
HERB_SOW_NOT = ("prune", "pruned", "pruning", "cut back", "cutting back", "cut", "cutting",
                "trim", "trimming", "pinch", "pinching", "pinch out", "pinching out", "deadhead",
                "deadheading", "woody", "leggy", "bolted", "bolting", "harvest", "harvesting",
                # caring for a plant you already have is not sowing one: "how do i look after a
                # basil plant" is the yellow-leaves row, and the sow row was taking it
                "look after", "looking after", "care", "care for", "caring", "keep alive",
                "keep it alive", "water", "watering", "watered",
                # The fence above is two words and the line does not have to put them side by
                # side: "how do i keep a basil plant alive" has "keep", "a basil plant" and
                # "alive", so it slipped past "keep alive" and got the sowing month. Keeping a
                # herb is never sowing one, whatever order the words come in, so the bare verb
                # fences it: "keep basil alive", "keeps a basil plant going", "keeping my mint
                # from spreading" all leave this row.
                "keep", "keeps", "keeping",
                # moving a plant up a pot size is the repotting row, and the sowing row keys
                # "basil plant", so a bare "pot" was not enough to keep it out
                "repot", "repotting", "repotted", "pot on", "potting on", "potted on",
                "root bound", "rootbound", "pot bound", "potbound", "bigger pot")

# A crop is a vegetable and also a dinner, and "when" inside a sentence is not the sowing ask:
# "my leek and potato soup went grainy when i added the cream" read as a leek, a potato and the word
# "when", so it got "Plant seed potatoes from late March to mid-April" - an allotment answer to a
# pan that split. Every crop row, not just the ones whose name is a kitchen word, stands down on
# the words of a kitchen. The harvest and the sick-plant rows keep their own lines, because those
# do not say any of this.
# The verbs of the pan. A cook's verb on a crop name is a cooking question, and the crop rows answer
# growing ones: "how long do i soak beans" got "Beans are 10 to 16 weeks from seed", and so did
# rinse, defrost, pickle, ferment, mash, blitz, stew, curry, grill, barbecue, preserve, chop, grate,
# stuff, marinate and toast. The noun lists below could never catch it, because the nouns are the
# cook's and the verb is what makes the line one.
#
# It lives in one place because two rows need it and one of them forgot: the sowing rows carry
# KITCHEN_WORDS, and `crop-weeks-named` carries a list of its own, so a verb added to one was
# missing from the other. A verb that also grows is not here: "dry" is how a crop is kept, "season"
# is when a crop is ready, "peel" is what goes on the compost, and "sprout" and "can" name the plant
# as often as the pan.
PAN_VERBS = (
    "soak", "soaks", "soaked", "soaking",
    "rinse", "rinses", "rinsed", "rinsing",
    "defrost", "defrosts", "defrosted", "defrosting",
    "pickle", "pickles", "pickled", "pickling",
    "ferment", "ferments", "fermented", "fermenting",
    "mash", "mashes", "mashed", "mashing",
    "blitz", "blitzed", "blitzing",
    "stew", "stews", "stewed", "stewing",
    "curry", "curried",
    "grill", "grills", "grilled", "grilling",
    "barbecue", "barbecued", "barbecuing", "bbq",
    "preserve", "preserves", "preserved", "preserving",
    "chop", "chops", "chopped", "chopping",
    "grate", "grated", "grating",
    "stuff", "stuffed", "stuffing",
    "marinate", "marinates", "marinated", "marinating",
    "toast", "toasts", "toasted", "toasting",
)

# The pans and machines themselves, for the same reason: "how long do beans take in a pressure
# cooker", "how long do potatoes take in an air fryer", "how long do carrots take in a steamer",
# "how long do beans take in a slow cooker" and "how long do carrots need in a soup maker" all got
# the weeks from seed. "cook" is on the fence and "cooker" is a different word, so the appliance is
# how a kitchen line says it is one without naming a single thing it does.
PAN_KIT = (
    "oven", "ovens", "fan oven", "hob", "microwave", "microwaves", "microwave oven",
    "pressure cooker", "pressure cookers", "slow cooker", "slow cookers", "air fryer",
    "air fryers", "deep fat fryer", "deep fryer", "fryer", "fryers", "steamer", "steamers",
    "saucepan", "saucepans", "pan of water", "wok", "griddle", "grill pan", "soup maker",
    "rice cooker", "bread maker", "yoghurt maker", "thermomix", "halogen oven", "actifry",
    "sous vide", "casserole dish", "roasting tin", "baking tray", "tray bake",
)
# One name for both, because a kitchen line is a kitchen line whether it says what it is doing or
# what it is doing it in, and both fences want the whole of it.
A_PAN_LINE = PAN_VERBS + PAN_KIT

KITCHEN_WORDS = (
    "soup", "soups", "salad", "salads", "mash", "mashed", "roast", "roasted", "roasting",
    "boil", "boiled", "boiling", "fry", "fried", "frying", "chips", "crisps", "bake",
    "baked", "baking", "casserole", "curry", "stew", "pie", "gratin", "cream", "creamed",
    "creamy", "gravy", "sauce", "sauces", "salty", "bland", "tasty", "delicious", "grainy",
    "curdle", "curdled", "curdles", "recipe", "recipes", "cook", "cooked", "cooking",
    "dinner", "lunch", "supper", "side dish", "wedges", "puree", "pur\u00e9e", "saute",
    "sauteed", "steam", "steamed", "microwave", "air fryer", "overcooked", "undercooked",
    "went wrong", "too much", "not smooth",
    # "how long do carrots take to soften" read as a growing time ("Carrots are 12 to 16 weeks
    # from seed") because soften is how a pan is spoken about and none of the kitchen words said
    # it. A crop is softened, browned, simmered or blanched in a pan before anything sows it.
    "soften", "softens", "softened", "softening", "tender", "tenderise", "tenderised",
    "simmer", "simmered", "simmering", "blanch", "blanched", "parboil", "parboiled",
    # "brown" and "crisp" are how a variety is named as well as what a pan does ("when do i sow
    # brown onions", "crisp lettuce"), and in this list they lost the sowing answer, so the pan
    # sense is said with the pan instead.
    "brown in a pan", "brown the onions", "browned in", "browning in", "until crisp",
    "go crisp", "al dente", "stir fry",
    "stir fried", "saucepan", "pan", "pans", "hob", "drain", "drained", "draining",
    "piping hot", "portion", "portions", "side") + A_PAN_LINE

SOW_EXTRA_AVOID = {
    "basil": HERB_SOW_NOT,
    "parsley": HERB_SOW_NOT,
    "mint": HERB_SOW_NOT,
    "rosemary": HERB_SOW_NOT,
    "pepper": ("salt", "ground", "cracked", "black", "white", "peppercorn", "peppercorns",
               "add", "season", "seasoning", "stuffed", "sauce", "recipe", "recipes",
               "soup", "salad", "pizza", "roast", "cook", "cooking"),
    "chilli": ("sauce", "oil", "paste", "powder", "flakes", "con carne", "recipe",
               "recipes", "add", "season", "stuffed", "roast", "cook", "cooking",
               "too hot", "mild", "heat"),
}

# How long each named crop takes, in the crop's own words, so the answer can lead with the one
# the line actually named. STYLE's first rule is the answer in the first sentence, and a fixed
# reply opened on potatoes for "how long do carrots take to grow". Longest first: "spring onion"
# has to be read before "onion", and "salad leaves" before "leaves".
_CROP_WEEKS = (
    (("spring onion", "spring onions"), "Spring onions are 8 to 10 weeks from seed."),
    (("sweetcorn", "sweet corn"), "Sweetcorn is 12 to 14 weeks from seed."),
    (("runner bean", "runner beans"), "Runner beans are 12 to 14 weeks from seed."),
    (("broad bean", "broad beans"), "Broad beans are 12 to 16 weeks from seed."),
    (("french bean", "french beans", "dwarf bean", "dwarf beans"),
     "French and dwarf beans are 10 to 12 weeks from seed."),
    (("salad leaves", "salad leaf", "salad"),
     "Salad leaves are 4 to 6 weeks from seed, and you pick the outer leaves as you go."),
    (("potato", "potatoes", "spud", "spuds", "tattie", "tatties"),
     "Potatoes are 10 to 12 weeks from planting for earlies and 18 to 20 for maincrop."),
    (("carrot", "carrots"), "Carrots are 12 to 16 weeks from seed."),
    (("parsnip", "parsnips"),
     "Parsnips are 22 to 24 weeks from seed, so they are most of a season."),
    (("beetroot",), "Beetroot is 10 to 12 weeks from seed."),
    (("radish", "radishes"), "Radishes are 4 to 6 weeks from seed, the quickest crop there is."),
    (("lettuce", "lettuces"),
     "Lettuce is 8 to 12 weeks from seed, and the cut-and-come-again leaves are 4 to 6."),
    (("spinach",), "Spinach is 6 to 10 weeks from seed, and it bolts in the heat of summer."),
    (("kale",), "Kale takes 10 to 12 weeks before the first pickings."),
    (("broccoli",), "Broccoli is 16 to 20 weeks from seed; sprouting broccoli takes a year."),
    (("cauliflower", "cauliflowers"), "Cauliflower is 16 to 20 weeks from seed."),
    (("cabbage", "cabbages"), "Cabbages are 16 to 20 weeks from seed, depending on the sort."),
    (("sprouts", "brussels", "brussel"), "Brussels sprouts are 20 to 24 weeks from seed."),
    (("swede",), "Swede is 20 to 24 weeks from seed."),
    (("turnip", "turnips"), "Turnips are 6 to 8 weeks from seed."),
    (("courgette", "courgettes", "marrow", "marrows"),
     "Courgettes are 10 to 12 weeks from seed, and then they do not stop."),
    (("pumpkin", "pumpkins", "squash"), "Pumpkins are 16 to 20 weeks from seed."),
    (("cucumber", "cucumbers"), "Cucumbers are 8 to 12 weeks from seed under cover."),
    (("tomato", "tomatoes"),
     "Tomatoes are 16 to 20 weeks from seed, or 12 to 16 from planting out."),
    (("chilli", "chillies", "chili", "chilis"),
     "Chillies are 16 to 20 weeks from seed, and they want warmth all of that time."),
    (("aubergine", "aubergines"), "Aubergines are 16 to 20 weeks, and want a warm summer."),
    (("pepper", "peppers"), "Peppers are 16 to 20 weeks from seed."),
    (("pea", "peas", "mangetout"), "Peas are 12 to 14 weeks from seed."),
    (("bean", "beans"), "Beans are 10 to 16 weeks from seed, the dwarf sorts quickest."),
    (("garlic",), "Garlic is about eight months from an autumn clove: plant in October and lift "
                  "in July."),
    (("strawberry", "strawberries"),
     "Strawberries fruit the summer after planting, so about a year from a new plant."),
    (("onion", "onions", "leek", "leeks", "shallot", "shallots"),
     "Onions and leeks are 20 to 24 weeks from seed, or about 20 weeks from sets."),
)

# The rest of the table, for a line that names one crop and wants the others too.
_CROP_WEEKS_REST = (
    "The others, from seed: salad leaves and radishes 4 to 6 weeks, beetroot 10 to 12, carrots "
    "and runner beans 12 to 16, peas 12 to 14, courgettes 10 to 12, sweetcorn 12 to 14, tomatoes "
    "16 to 20 from sowing (12 to 16 from planting out), cabbages and broccoli 16 to 20, parsnips "
    "22 to 24, and leeks or onions 20 to 24. Garlic takes about eight months from an autumn clove, "
    "and strawberries fruit the summer after planting. The seed packet is the tie-breaker, "
    "because a fortnight either way is normal."
)


def _crop_weeks_reply(memory, reading):
    """The weeks for the crop the line named, first, then the rest of the table."""
    said = " " + str(reading.get("plain") or reading.get("norm_text")
                     or reading.get("text") or "").lower() + " "
    words = set(reading.get("words") or ())
    for forms, lead in _CROP_WEEKS:
        if any(" " + form + " " in said for form in forms) or words & set(forms):
            return lead + " " + _CROP_WEEKS_REST
    return _CROP_WEEKS_REST


SOW_ENTRIES = [
    entry("sow-" + words[0], (words, SOW_ASK), _sowing_reply(words[0], reply),
          avoid=SOW_NOT + HARVEST_ASK + KITCHEN_WORDS + SOW_EXTRA_AVOID.get(words[0], ()), bias=1)
    for words, reply in SOWING
] + _harvest_entries() + [
    # "what can i sow in october" names no crop, so it is no single row's question: it wants the
    # month's own short list. The crop rows stand down on a month outside their window, so this is
    # what answers a month that nothing on the table is sown in.
    entry("sow-month", (("sow", "sowing", "sowed", "plant", "planting", "grow", "growing",
                         "seed", "seeds", "put in"),
                        tuple(MONTH_NUMBER) + ("in may", "of may", "by may", "during may",
                                               "this may", "next may", "now", "this month",
                                               "next month", "autumn", "spring", "winter",
                                               "summer", "next year",
                                               # the same question with the date left to us:
                                               # "what should i plant at the moment" named
                                               # no month and got a shrug
                                               "at the moment", "at the minute",
                                               "these days", "this time of year",
                                               # a season named with "in" or "for" is one
                                               # score worse than the beginner row's literal
                                               # "what can i plant", so the phrase carries it:
                                               # "in spring" is the date, and a line that
                                               # names the date is the sowing question.
                                               "in spring", "in the spring", "this spring",
                                               "next spring", "for spring", "of spring",
                                               "in summer", "in the summer", "this summer",
                                               "next summer", "for summer", "of summer",
                                               "in autumn", "in the autumn", "this autumn",
                                               "next autumn", "for autumn", "of autumn",
                                               "in winter", "in the winter", "this winter",
                                               "next winter", "for winter", "of winter",
                                               "over winter", "over the winter",
                                               "before winter", "for christmas")),
          _sow_month,
          ask=("what", "which", "can i", "could i", "anything", "what else", "when", "best",
               "now", "should i"),
          avoid=("harvest", "harvesting", "lift", "dig up", "pick", "picking", "cut", "ready",
                 "ripe", "prune", "pruning", "cutting", "cuttings", "lawn", "grass", "mow",
                 "weed", "weeds", "sick", "yellow", "yellowing", "dying", "blight", "frost",
                 "sprout", "flower", "flowers", "bulb", "bulbs", "rose", "roses", "tomato",
                 "tomatoes",
                 # A thing grown indoors is not a sowing table for the plot outdoors: "what
                 # herbs can i grow now" lost the herbs card to this row, and "what can i grow
                 # indoors now" was answered with garlic and broad beans. A herb, a houseplant,
                 # a windowsill, a greenhouse and a balcony each keep their own answer.
                 "herb", "herbs", "herb pot", "houseplant", "houseplants", "house plant",
                 "house plants", "indoor", "indoors", "inside", "windowsill", "window sill",
                 "greenhouse", "green house", "propagator", "patio", "balcony",
                 "window box", "window boxes", "hanging basket"),
          # the season and month rows have to beat the beginner card on a line that names a date
          # and says "what can i plant" - the beginner card keys that phrase literally, so the
          # date is what breaks the tie
          bias=2),
]


# --- the rows the vegetable table cannot hold -----------------------------------------------
# Bulbs, soft fruit, a lawn, a young tree and a rose have a month too, and every one of them was a
# shrug beside the crop rows: "when do i plant daffodils", "when should i plant a tree", "when do
# i prune my apple tree". They are not vegetables, so they are not in SOWING, but they are
# answered the same way - the plant's own names, a when-ask, and the month first.
SOW_WINDOW.update({"daffodil": (9, 12), "hyacinth": (9, 12), "crocus": (9, 11),
                   "snowdrop": (1, 3), "allium": (9, 11), "tomato": (3, 6),
                   "grass seed": (3, 10), "strawberry": (3, 10), "sweet pea": (2, 11),
                   "clematis": (9, 11)})

# A row about putting a plant in the ground is the wrong answer for a plant that is being cut,
# fed, or coming into flower, whatever the plant is. "when do apple trees blossom" was the apple
# pruning row and "when do trees blossom" the tree row.
PLANT_NOT = SOW_NOT + HARVEST_ASK + (
    "cut", "cutting", "prune", "pruning", "trim", "trimming", "mow", "mowing", "deadhead",
    "deadheading", "feed", "feeding", "fertilise", "fertiliser", "fertilizer", "stake", "staking",
    "blossom", "blossoms", "blossoming", "flower", "flowering", "flowers", "bloom", "blooms",
    "buds", "catkins", "pollen",
    # moving one is its own job, with its own answer: lift it in autumn with a rootball
    "move", "moving", "moved", "transplant", "transplanting", "relocate", "relocating",
    # A body word is never a planting question, whatever the plant: "i get a rash when i eat
    # strawberries" was answered by the strawberry row (main, 2026-11-06), and a person saying
    # what a fruit does to them wants a health answer or none, not a month to put it in.
    "rash", "hives", "itch", "itchy", "itching", "allergic", "allergy", "allergies",
    "swollen", "swelling", "sick", "vomit", "vomiting", "diarrhoea", "stomach", "throat",
    "breathless", "bloated", "bloating", "reaction", "anaphylaxis", "cramps")

PLANTING = (
    (("daffodil", "daffodils", "hyacinth", "hyacinths", "crocus", "snowdrop", "snowdrops",
      "allium", "alliums", "spring bulbs"),
     "Spring bulbs go in from September to November while the soil is still warm: three times the "
     "bulb's own height deep, 10cm apart for daffodils and 8cm for crocuses, pointy end up. They "
     "need a cold spell to flower, so a mild autumn is fine. Leave the leaves on for six weeks "
     "after flowering and they come back every year."),
    (("sweet pea", "sweet peas"),
     "Sow sweet peas in October for the strongest plants, or February to March under cover, 2cm "
     "deep in deep pots so the root runs straight down. Pinch out the growing tip after two pairs "
     "of leaves, harden them off, and plant out in April. Keep picking, because once they set seed "
     "they stop flowering."),
    (("strawberry", "strawberries", "strawberry plants"),
     "Plant strawberries in late summer, August to September, for a full crop the next June - a "
     "spring planting gives you a handful the same year and nothing much the next. 45cm apart with "
     "the crown level with the soil and the roots spread, straw under the fruit, and replace the "
     "plants every three years, when the crop shrinks and virus builds up."),
    (("grass seed", "lawn seed", "grass"),
     "Sow grass seed in September, or early April if you missed it: warm damp soil, weeds not yet "
     "up, and enough time to root before winter. Scatter 35g to the square metre, rake it in "
     "lightly, and keep it damp for a fortnight with a light sprinkle morning and evening rather "
     "than a soak."),
    (("tomato", "tomatoes", "tomato plants"),
     "Sow tomatoes indoors in March or April and plant them out in early June, once nights stay "
     "above 10C: 45cm apart, or one to a grow bag, burying the stem up to its first leaves. "
     "Harden them off over a week first - a cold night sets a tomato back a month."),
    (("tree", "trees", "fruit tree", "bare root", "bare-root", "shrub", "shrubs", "hedge",
      "hedges", "clematis", "climber", "climbers", "wisteria"),
     "Bare-root trees and shrubs go in from November to March while they are dormant, and potted "
     "ones any time the ground is not frozen or waterlogged. Dig a square hole twice the width of "
     "the roots, keep the soil mark on the stem at the same level, firm it in well and water it "
     "through its first summer. Autumn planting beats spring: the roots work all winter."),
    (("rose", "roses", "bare root rose", "climbing rose", "shrub rose"),
     "Plant bare-root roses from November to March, while they are dormant, or potted ones any "
     "month the ground is not frozen: a hole wide enough to spread the roots, the graft union an "
     "inch below soil level, firmed in hard. They want sun and rich soil, and a feed in March and "
     "again in July is what keeps them flowering."),
)

# The pruning row and the flowering row below keep the cutting words, so each row names its own
# fence instead of sharing one.
# A fruit tree being pruned is what the pruning row answers, so "prune", "cut" and "trim" stay out
# of its fence - but a tree coming into flower is still not a pruning question, and neither is one
# going in the ground.
PRUNE_NOT = SOW_NOT + HARVEST_ASK + (
    "blossom", "blossoms", "blossoming", "flower", "flowering", "flowers", "bloom", "blooms",
    "buds", "catkins", "pollen", "feed", "feeding", "plant", "planting", "planted", "move",
    "moving", "transplant", "transplanting")

# The trees are two different jobs with two different months, so the line's own tree decides which
# sentence leads: "when do i prune my plum tree" wants June first, not a paragraph about apples.
PRUNE_APPLE = ("Prune apples and pears in January or February while they are dormant: dead, "
               "diseased and crossing branches out first, then the oldest third of the stems, "
               "and the middle kept open.")
PRUNE_STONE = ("Prune plums, cherries and damsons in June, not in winter: silver leaf gets in "
               "through a winter cut and kills a branch a year later. Cut back to a growing shoot "
               "and leave the pruning cuts open to the air rather than painting them.")


def _prune_reply(memory, understood):
    """The winter job or the June one, whichever tree the line names, in front."""
    line = _words(understood)
    if re.search(r"\bplum|\bcherr|\bdamson", line):
        return PRUNE_STONE + " " + PRUNE_APPLE
    return PRUNE_APPLE + " " + PRUNE_STONE


# Every pruning row in this file is one plant (roses, lavender, a hedge, fruit trees), so the
# rest of the shrubs had no owner at all: "how do i prune a buddleia", "when do i prune my
# wisteria", "how do i prune a hydrangea", "how do i prune a bay tree" and "how do i prune a
# raspberry cane" were all the honest punt. Shrubs are one job with two possible dates, and which
# date it is depends on when the thing makes its flower buds, so one row covers them all.
PRUNE_BUDDLEIA = (
    "Cut a buddleia hard in March, back to about 30cm: it flowers on the shoots that grow from "
    "there, so the harder you cut the bigger the spikes. Do it every year, and take out any dead "
    "stems at the base at the same time. A neglected one can lose two thirds of its height at "
    "once and still come back.")

PRUNE_WISTERIA = (
    "Wisteria is pruned twice: in July or August shorten the long whippy shoots to five or six "
    "leaves, then in January cut those same shoots back to two or three buds. That is what turns "
    "growth into flowers. Leave any shoot you are training out longer, and do not feed it with "
    "nitrogen, which gives you leaves instead.")

PRUNE_HYDRANGEA = (
    "Leave the old flowers on over winter for frost protection, then in March cut each stem back "
    "to a fat pair of buds about 30cm up and take out the oldest stems at the base. Do not cut a "
    "mophead to the ground: it flowers on last year's wood. A paniculata kind is the exception "
    "and flowers best cut hard in spring.")

PRUNE_EVERGREEN = (
    "Trim an evergreen shrub in mid to late spring, once the frosts are over: bay, holly, laurel "
    "and box all take a tidy-up then, and bay takes a light trim in August too. Do not cut back "
    "into bare old wood, because most evergreens will not shoot again from it - a hard cut is "
    "better spread over two years.")

PRUNE_RASPBERRY = (
    "Summer-fruiting raspberries: cut the canes that fruited this year down to the ground in "
    "February and tie in the new ones. Autumn-fruiting ones are easier, because every cane is cut "
    "to the ground in February and the fruit comes on the new growth the same year. Take out the "
    "weak and crowded canes either way.")

PRUNE_LATER = (
    "Prune it in late winter or early spring, around March, while it is dormant: it flowers on the "
    "shoots that grow this year, so cutting it back then gives the strongest growth and the most "
    "flower. Take out dead and crossing stems first, then up to a third of the oldest stems at "
    "the base.")

PRUNE_EARLIER = (
    "Prune it straight after it has flowered, not in winter: it made this year's flower buds last "
    "summer, so a spring cut takes the flowers with it. Take the flowered shoots back by about a "
    "third as the blooms fade, and leave the rest of the growth alone until next year.")

# The ones people ask about oftenest, so the answer can be about that plant rather than the rule.
PRUNE_NAMED = (
    (r"buddleia|buddleja", PRUNE_BUDDLEIA),
    (r"wisteria", PRUNE_WISTERIA),
    (r"hydrangea", PRUNE_HYDRANGEA),
    (r"raspberr", PRUNE_RASPBERRY),
    (r"\bbay\b|laurel|holly|box\b|evergreen|photinia|pieris", PRUNE_EVERGREEN),
    (r"forsythia|weigela|philadelphus|mock orange|deutzia|kerria|ribes", PRUNE_EARLIER),
    (r"cotoneaster|spirea|ceanothus|hebe|buddleia", PRUNE_LATER),
)


def _prune_shrub(memory, understood):
    """The date and the cut for the shrub the line names, or the rule for any other one."""
    line = _words(understood)
    for shape, reply in PRUNE_NAMED:
        if re.search(shape, line):
            return reply
    return ("Shrubs want one of two dates. If it flowers before midsummer, cut it just after "
            "flowering, because the buds were made last year. If it flowers later, cut it in "
            "March while it is dormant, because the flowers come on the new growth. Take out "
            "dead and crossing stems first, then a third of the oldest at the base.")


PLANT_AVOID = {
    # "when do i plant tomatoes" is grow-tomatoes' answer and its test pins that, so this row only
    # takes the line that says where the plants are going - "when can i put my tomatoes outside" -
    # and stands aside for the potting and growing questions.
    "sow-tomato": PLANT_NOT + ("plant", "planting", "planted", "grow", "growing", "grown",
                               "pot", "pots", "grow bag", "greenhouse"),
    # "small" is the fence for a plant that came up small, and it also shut the door on "how do
    # i plant a tree in a small garden", which is a planting question about the size of the garden
    # and was answered with a bed of radishes.
    "sow-tree": tuple(word for word in PLANT_NOT if word != "small"),
}

# The crop rows' "too late" sentence is written for something that will still crop that year. A
# bulb planted in December is planting for the spring after next, so the bulbs row says its own.
PLANT_LATE = {
    "daffodil": ("November is the last good month, so go now: planted in December a bulb still "
                 "flowers, just later and smaller. "),
}


def _planting_reply(name, reply):
    """A planting row's answer: the crop rows' month window, and a late sentence that fits."""
    answer = _sowing_reply(name, reply)
    late = PLANT_LATE.get(name)
    if not late:
        return answer

    def with_late(memory, understood):
        if re.search(r"\btoo late\b|\btoo early\b|\blate for\b", _words(understood)):
            return late + reply
        return answer(memory, understood)

    return with_late


SOW_PLANT_CARE = (
    ("monstera", ("monstera", "monsteras", "swiss cheese plant", "cheese plant"),
     "Water a monstera when the top 2 to 3cm of compost is dry, which is about once a week in "
     "summer and every two weeks in winter. Give it bright light out of direct sun, and don't "
     "worry when water drips from the leaf tips for an hour afterwards: that is the plant pushing "
     "out moisture, not a problem."),
    ("pothos", ("pothos", "devil's ivy", "devils ivy", "devil ivy"),
     "Water a pothos about once a week, when the compost is dry and the leaves are just starting "
     "to look limp: it forgives a missed week but rots in a pot that never dries. It grows in "
     "almost any light, and a cutting in a glass of water roots in a few weeks."),
    ("snake-plant", ("snake plant", "snake plants", "sansevieria", "mother in laws tongue"),
     "Water a snake plant every two to three weeks in summer and once a month or less in winter, "
     "and only when the compost is dry all the way down. It stores water in its leaves and rots "
     "in wet soil, so the surest way to kill one is to water it on a schedule."),
    ("spider-plant", ("spider plant", "spider plants"),
     "Water a spider plant about once a week, when the top of the compost is dry, and let the pot "
     "drain. Brown tips are usually tap water or dry air rather than a watering fault: trim them "
     "off and stand the pot somewhere less dry."),
    ("peace-lily", ("peace lily", "peace lilies", "spathiphyllum"),
     "Water a peace lily when the compost is just dry, about once a week, and it will tell you "
     "when it wants more by drooping: it picks itself up within a few hours of a drink. It likes "
     "a bright spot out of direct sun and brown leaf tips mean the water or the air is hard."),
    ("fiddle-leaf-fig", ("fiddle leaf fig", "fiddle fig", "fiddle leaf"),
     "Water a fiddle leaf fig when the top 3cm of soil is dry, which is about every ten days, and "
     "let it drain right through. It sulks if it is moved or sits in a draught, and brown blotches "
     "on the leaves are usually too much water rather than too little."),
    ("zz-plant", ("zz plant", "zz plants", "zamioculcas"),
     "Water a ZZ plant every two to three weeks in summer and once a month in winter. Its thick "
     "underground stems hold water, so it survives neglect far better than kindness: yellow "
     "leaves that fall off are the sign of too much."),
    ("aloe", ("aloe", "aloe vera"),
     "Water an aloe every two to three weeks in summer and once a month in winter, soaking the pot "
     "and then letting it dry out completely. Leaves going soft and pale at the base mean the "
     "compost has stayed wet."),
    ("cactus", ("cactus", "cacti", "cactuses"),
     # the same cadence the cactus-care entry states, so the two never disagree
     "Water a cactus every two to three weeks in summer, and barely at all from November to "
     "March. Soak it, let it dry right out, and never leave the pot standing in water: more cacti "
     "die of watering than of neglect."),
    ("succulent", ("succulent", "succulents"),
     "Water a succulent by soaking the pot and then letting it dry out completely: every two to "
     "three weeks in summer, monthly in winter. The leaves going soft and see-through at the base "
     "is rot from wet compost, and shrivelled leaves are the sign it wants a drink."),
    ("orchid", ("orchid", "orchids", "moth orchid", "phalaenopsis"),
     "Water an orchid by standing the pot in tepid water for ten minutes once a week, then letting "
     "it drain: it lives in bark, not compost, so a normal watering can runs straight through. "
     "Roots that are silver want water and roots that are green have had enough."),
    ("fern", ("fern", "ferns", "boston fern", "maidenhair fern"),
     "Water a fern when the compost is barely dry, which is twice a week in summer, and stand the "
     "pot on pebbles in a saucer of water for the humidity. Crispy brown fronds are dry air, not "
     "thirst: a bathroom or a kitchen suits most ferns better than a windowsill."),
    ("rubber-plant", ("rubber plant", "rubber plants", "ficus elastica"),
     "Water a rubber plant every week to ten days, when the top 3cm of compost is dry, and wipe "
     "the leaves so the dust doesn't block the light. Dropping lower leaves one at a time is "
     "usually a cold draught or a sudden move."),
    ("jade-plant", ("jade plant", "jade plants"),
     "Water a jade plant every two to three weeks in summer and once a month in winter, and let "
     "the compost dry between waterings. It wants a sunny windowsill and shrivelled leaves mean "
     "thirst while soft, dropping leaves mean too much water."),
    ("calathea", ("calathea", "prayer plant"),
     "Water a calathea when the top of the compost is just dry, about twice a week in summer, and "
     "keep it out of direct sun. Curling leaves and brown edges are dry air: a tray of wet pebbles "
     "or a bathroom does more for it than more water does."),
)

# The care words that turn a named plant into a question: a plant name alone ("I bought a
# monstera") is a remark, and the watering words are what make it one somebody wants answered.
PLANT_CARE = (
    ("monstera", ("monstera", "monsteras", "swiss cheese plant", "cheese plant"),
     "Water a monstera when the top 2 to 3cm of compost is dry, which is about once a week in "
     "summer and every two weeks in winter. Give it bright light out of direct sun, and don't "
     "worry when water drips from the leaf tips for an hour afterwards: that is the plant pushing "
     "out moisture, not a problem."),
    ("pothos", ("pothos", "devil's ivy", "devils ivy", "devil ivy"),
     "Water a pothos about once a week, when the compost is dry and the leaves are just starting "
     "to look limp: it forgives a missed week but rots in a pot that never dries. It grows in "
     "almost any light, and a cutting in a glass of water roots in a few weeks."),
    ("snake-plant", ("snake plant", "snake plants", "sansevieria", "mother in laws tongue"),
     "Water a snake plant every two to three weeks in summer and once a month or less in winter, "
     "and only when the compost is dry all the way down. It stores water in its leaves and rots "
     "in wet soil, so the surest way to kill one is to water it on a schedule."),
    ("spider-plant", ("spider plant", "spider plants"),
     "Water a spider plant about once a week, when the top of the compost is dry, and let the pot "
     "drain. Brown tips are usually tap water or dry air rather than a watering fault: trim them "
     "off and stand the pot somewhere less dry."),
    ("peace-lily", ("peace lily", "peace lilies", "spathiphyllum"),
     "Water a peace lily when the compost is just dry, about once a week, and it will tell you "
     "when it wants more by drooping: it picks itself up within a few hours of a drink. It likes "
     "a bright spot out of direct sun and brown leaf tips mean the water or the air is hard."),
    ("fiddle-leaf-fig", ("fiddle leaf fig", "fiddle fig", "fiddle leaf"),
     "Water a fiddle leaf fig when the top 3cm of soil is dry, which is about every ten days, and "
     "let it drain right through. It sulks if it is moved or sits in a draught, and brown blotches "
     "on the leaves are usually too much water rather than too little."),
    ("zz-plant", ("zz plant", "zz plants", "zamioculcas"),
     "Water a ZZ plant every two to three weeks in summer and once a month in winter. Its thick "
     "underground stems hold water, so it survives neglect far better than kindness: yellow "
     "leaves that fall off are the sign of too much."),
    ("aloe", ("aloe", "aloe vera"),
     "Water an aloe every two to three weeks in summer and once a month in winter, soaking the pot "
     "and then letting it dry out completely. Leaves going soft and pale at the base mean the "
     "compost has stayed wet."),
    ("cactus", ("cactus", "cacti", "cactuses"),
     # the same cadence the cactus-care entry states, so the two never disagree
     "Water a cactus every two to three weeks in summer, and barely at all from November to "
     "March. Soak it, let it dry right out, and never leave the pot standing in water: more cacti "
     "die of watering than of neglect."),
    ("succulent", ("succulent", "succulents"),
     "Water a succulent by soaking the pot and then letting it dry out completely: every two to "
     "three weeks in summer, monthly in winter. The leaves going soft and see-through at the base "
     "is rot from wet compost, and shrivelled leaves are the sign it wants a drink."),
    ("orchid", ("orchid", "orchids", "moth orchid", "phalaenopsis"),
     "Water an orchid by standing the pot in tepid water for ten minutes once a week, then letting "
     "it drain: it lives in bark, not compost, so a normal watering can runs straight through. "
     "Roots that are silver want water and roots that are green have had enough."),
    ("fern", ("fern", "ferns", "boston fern", "maidenhair fern"),
     "Water a fern when the compost is barely dry, which is twice a week in summer, and stand the "
     "pot on pebbles in a saucer of water for the humidity. Crispy brown fronds are dry air, not "
     "thirst: a bathroom or a kitchen suits most ferns better than a windowsill."),
    ("rubber-plant", ("rubber plant", "rubber plants", "ficus elastica"),
     "Water a rubber plant every week to ten days, when the top 3cm of compost is dry, and wipe "
     "the leaves so the dust doesn't block the light. Dropping lower leaves one at a time is "
     "usually a cold draught or a sudden move."),
    ("jade-plant", ("jade plant", "jade plants"),
     "Water a jade plant every two to three weeks in summer and once a month in winter, and let "
     "the compost dry between waterings. It wants a sunny windowsill and shrivelled leaves mean "
     "thirst while soft, dropping leaves mean too much water."),
    ("calathea", ("calathea", "prayer plant"),
     "Water a calathea when the top of the compost is just dry, about twice a week in summer, and "
     "keep it out of direct sun. Curling leaves and brown edges are dry air: a tray of wet pebbles "
     "or a bathroom does more for it than more water does."),
)

# The care words that turn a named plant into a question: a plant name alone ("I bought a
# monstera") is a remark, and the watering words are what make it one somebody wants answered.

PLANT_CARE_WORDS = ("water", "watering", "watered", "how often", "how much", "care",
                    "care for", "look after", "keep alive", "light", "sun", "repot", "root rot",
                    "overwatered", "overwatering", "underwatered", "soak", "soaking",
                    # "how do i keep my orchid alive" puts the plant between the two words of
                    # "keep alive", so each word has to count on its own as well
                    "keep", "keeping", "alive", "thriving", "healthy",
                    # a named plant in trouble wants that plant's own cadence: "my orchid is
                    # dying" was the general houseplant answer
                    "dying", "die", "dies", "drooping", "droopy")

# The per-plant replies give a watering cadence, so a question about light must not land on them:
# "how much light does a cactus need" was answered with how often to water it. Those lines belong
# to the light answers, which say what the plant wants and where to stand it.
LIGHT_QUESTION = ("light", "sun", "sunlight", "sunny", "sunshine", "shade", "shady",
                           "bright", "direct sun", "low light", "dark", "window", "windowsill",
                           "south facing", "north facing", "east facing", "west facing",
                           "full sun", "part shade")


# "care for" is a houseplant word and a person word, and the plant rows were taking every line
# with a person in it: "how do i care for my dad" and "how do i care for my baby" were both
# answered "Water when the top couple of centimetres of compost is dry, not on a fixed day".
# What makes a line a person's is the person being the one cared for, or the person owning the
# care: "care for my mum", "my dad needs care". A plant in the line settles it the other way -
# "my dad gave me a plant, how do i care for it" is the plant's question - so the plant words
# are read first and the line stays the garden's.
A_PERSON_CARED_FOR = (r"(?:mum|mums|mother|mothers|dad|dads|father|fathers|parent|parents|"
                      r"son|sons|daughter|daughters|child|children|kid|kids|baby|babies|"
                      r"newborn|newborns|infant|infants|toddler|husband|husbands|wife|wives|"
                      r"partner|partners|boyfriend|"
                      r"girlfriend|brother|brothers|sister|sisters|gran|grans|grandma|"
                      r"grandmas|grandad|grandads|nan|nans|aunt|aunty|auntie|uncle|uncles|"
                      r"cousin|cousins|friend|friends|neighbour|neighbours|relative|"
                      r"relatives|carer|carers|elderly|pensioner|pensioners)")
# The person can stand on either side of the verb. "my mum cares for my dad" has the person
# after it; "my son cares for me" has the person doing the caring first and only a pronoun after,
# so the first pattern read that line as the garden's and answered "Water when the top couple of
# centimetres of compost is dry". A pronoun after the care word is a person too - except "it",
# which is the plant: "my dad gave me a plant, how do i care for it" stays the garden's.
A_PERSON_CARED_FOR_BY_PRONOUN = re.compile(
    r"\b(?:care|cares|cared|caring|look|looks|looking|take|takes|taking|took)\s+"
    r"(?:after|for|of)\s+(?:me|us|him|her|them)\b")
CARE_FOR_A_PERSON = re.compile(
    r"\b(?:care|cares|cared|caring|look|looks|looking|take|takes|taking|took)\s+"
    r"(?:after|for|of)\s+(?:my|our|his|her|their|the|a|an)?\s*" + A_PERSON_CARED_FOR + r"\b"
    r"|" + A_PERSON_CARED_FOR_BY_PRONOUN.pattern)
A_PERSON_NEEDING_CARE = re.compile(
    r"\b(?:my|our|his|her|their)\s+" + A_PERSON_CARED_FOR
    + r"\b[^.!?]*\b(?:care|carers?|look after|looking after|help|needs help)\b")
# An animal is not a pot plant either, and "care for" is the pet owner's word as much as the
# plant owner's: "how do i care for a kitten" and "how do i care for a puppy" were both answered
# "Water when the top couple of centimetres of compost is dry, not on a fixed day". The animal
# being the one cared for is what settles it, the same way a person is: a line that names a plant
# as well stays the garden's ("my kitten keeps eating my spider plant"), so `A_PLANT_IN_THE_LINE`
# is still asked first.
A_PET_CARED_FOR = (r"(?:dog|dogs|puppy|puppies|pup|pups|cat|cats|kitten|kittens|kitty|moggy|"
                   r"rabbit|rabbits|bunny|bunnies|hamster|hamsters|guinea pig|guinea pigs|"
                   r"gerbil|gerbils|rat|rats|mouse|mice|parrot|parrots|budgie|budgies|"
                   r"fish|goldfish|horse|horses|pony|ponies|tortoise|tortoises|reptile|reptiles|"
                   r"snake|snakes|lizard|lizards|pet|pets|animal|animals|puppies)")
CARE_FOR_A_PET = re.compile(
    r"\b(?:care|cares|cared|caring|look|looks|looking|take|takes|taking|took)\s+"
    r"(?:after|for|of)\s+(?:my|our|his|her|their|the|a|an)?\s*" + A_PET_CARED_FOR + r"\b")
# The plant words that settle a line with a person in it: the person is there to talk about the
# plant, not to be cared for.
A_PLANT_IN_THE_LINE = re.compile(
    r"\b(?:plants?|house ?plants?|pot plants?|indoor plants?|monstera|orchid|fern|cactus|"
    r"succulent|peace lily|spider plant|snake plant|pothos|calathea|zz plant|dracaena|yucca|"
    r"fiddle leaf|rubber plant|poinsettia|cyclamen|amaryllis|african violet|aloe|jade plant|"
    r"anthurium|kalanchoe|begonia|hyacinth|flowers?|shrubs?|trees?|garden|compost|leaves|"
    r"seeds?|bulbs?|lawn|hedge)\b")


def _the_care_is_for_a_person(understood):
    """False when the line is about caring for a person rather than for a plant."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    said = said.replace("\u2019", "'")
    if A_PLANT_IN_THE_LINE.search(said):
        return True
    if CARE_FOR_A_PERSON.search(said):
        return False
    if CARE_FOR_A_PET.search(said):
        return False
    return not A_PERSON_NEEDING_CARE.search(said)


_A_GARDEN_THING = ("plant", "plants", "garden", "gardens", "greenhouse", "seedling",
                  "seedlings", "pot", "pots", "flower", "flowers", "shrub", "shrubs",
                  "bush", "bushes", "bedding", "tender", "cutting", "cuttings",
                  "allotment", "polytunnel", "grow bag", "grow bags", "basket", "baskets",
                  "veg", "vegetables", "crop", "crops", "tomato", "tomatoes", "tree",
                  "trees", "fern", "ferns", "citrus", "olive", "herb", "herbs",
                  "cloche", "cloches", "plot", "border", "borders", "hanging basket")


def _a_winter_pond_line(understood):
    """False when the water is not frozen and the season is not named.

    "pump", "filter" and "feed" are in the pond row's key so that "do i need to keep the pump
    running in winter" lands there, and on their own they made every summer pond job the ice
    card: "how do i clean my pond filter" and "my pond pump has stopped working" both got
    "never smash the ice". The row answers a pond in the cold, so the cold has to be in the line.
    """
    line = _words(understood)
    return any(_has(line, word) for word in
               ("freeze", "freezes", "freezing", "frozen", "ice", "iced", "icy", "winter",
                "winters", "wintertime", "overwinter", "overwintering", "winterise",
                "winterised", "winterising", "winterize", "cold", "snow", "frost"))


def _a_christmas_tree(understood):
    """False when the tree in the line is a growing one in the garden.

    The row keyed the bare word "tree" so that "how do i look after the tree" reached it, and
    every tree in a garden came with it: "how do i choose a tree for my garden" and "how do i
    water my tree" were answered with a cut tree in a bucket. A tree is the Christmas row's when
    the line says Christmas, or names a conifer, or asks about the needles - nothing else.
    """
    line = _words(understood)
    if any(_has(line, word) for word in ("christmas", "xmas", "spruce", "fir", "nordmann",
                                         "needles", "needle", "tinsel", "decorations")):
        return True
    return not any(_has(line, word) for word in _A_GARDEN_THING)


def _garden_tree(memory, understood):
    """A growing tree: watering, pruning, and the choosing-and-planting that most lines ask."""
    line = _words(understood)
    if _has(line, "water") or _has(line, "watering") or _has(line, "how often") \
            or _has(line, "soak"):
        return ("A tree that is in its first two summers needs a proper soak of about ten litres "
                "a week, poured slowly round the roots so it sinks in, and more in a dry spell - "
                "a sprinkle from a hose wets the top inch and the roots stay shallow and thirsty. "
                "Water in the morning or the evening rather than in the middle of a hot day, and "
                "aim at the soil, not the leaves. After that a tree is on its own unless there "
                "are months without rain, when the leaves going dull and curling upwards is the "
                "sign it wants a drink. A potted tree dries out far faster and needs checking "
                "every few days in summer.")
    if _has(line, "prune") or _has(line, "pruning") or _has(line, "cut back") \
            or _has(line, "shape"):
        return ("Prune a tree in late winter while it is dormant, when the sap is down and the "
                "wound heals fast: take out the dead, the damaged and the crossing branches "
                "first, then any that rub or grow in towards the middle, and leave the rest. Do "
                "not top it or cut the leader out of the top, because that is what turns a tree "
                "into a bush of water shoots. Take out no more than a quarter of the crown in a "
                "year, cut back to a bud or a branch rather than leaving a stub, and leave "
                "anything that flowers on old wood - plum, cherry, magnolia - until just after "
                "it has flowered.")
    return ("Choose it for the space it will need in twenty years, not the one it needs now: the "
            "label gives a height and a spread, and most disappointment with trees is a tree "
            "planted at a third of its final width against a fence. Keep it well away from a "
            "house wall, the drains and the path, because roots go as wide as the branches, and "
            "check the soil and the light where it is going: a tree that wants acid soil sulks in "
            "chalk and one that wants sun goes thin in shade. Plant bare-root between November "
            "and March while it is dormant - it is cheaper, and it settles far better than a "
            "potted one in leaf. Dig a hole two or three times as wide as the roots and no "
            "deeper than the soil mark on the trunk, spread the roots, and put the stake in "
            "before the tree so the root ball is not speared. Firm it in, water it well, mulch "
            "round the base but leave a clear gap against the trunk, and give it a good soak "
            "every week or two through the first two summers, because that is what turns a "
            "stick into a tree.")


def _a_garden_tree(understood):
    """True when the line is about a tree that is growing, not the one that comes indoors."""
    line = _words(understood)
    if any(_has(line, word) for word in ("christmas", "xmas", "spruce", "fir", "nordmann")):
        return False
    return any(_has(line, word) for word in ("tree", "trees", "sapling", "saplings"))


def _a_summer_pond_line(understood):
    """False when the line is about the pond in the cold.

    "filter", "pump" and "feed" are in the key of both pond rows, and the ice is the winter
    row's question: "should i keep the pond filter running in winter" stays with it.
    """
    line = _words(understood)
    return not any(_has(line, word) for word in
                   ("freeze", "freezes", "freezing", "frozen", "ice", "iced", "icy", "winter",
                    "winters", "overwinter", "winterise", "winterize", "cold", "snow",
                    "frost"))


def _the_person_is_sad_too(understood):
    """False when the line gives the speaker the state as well as the plant.

    "my plant is sad and so am i" names the plant's state and then the speaker's own, and what
    that person needs is an answer for them, not the roots: the plant's triage waits for the
    next turn. The reading engine already knows whose the state is (`state_owner`), the way
    `_the_part_is_a_persons` reads the owner of a part, so the rows that answer a thing's state
    stand aside for the person's own.
    """
    return str((understood or {}).get("state_owner") or "") != "self"


def _plant_entries():
    """One entry per plant in PLANT_CARE, in the same shape as every other entry."""
    # A named plant's own answer beats the general houseplant one, which is what bias buys: the
    # general entry matches more of the line's words ("water", "leaves"), and its answer about
    # roots holds for a plant we cannot name. When the plant is named, its own numbers are the
    # better reply - "water when the top 2 to 3cm is dry" beats "the top couple of centimetres".
    return [entry(f"plant-{name}", (aliases, PLANT_CARE_WORDS), reply, bias=1,
                  avoid=LIGHT_QUESTION, guard=_the_care_is_for_a_person)
            for name, aliases, reply in PLANT_CARE]


# A tree or a rose is the plant people come home with and then ask about, and the words they use
# are the buying ones: "i bought a lemon tree", "i picked up an apple tree", "my new rose arrived".
# None of SOW_ASK has a buying verb, so those lines fell past the month and the planting card and
# were answered by the pantry ("Lemon and garlic chicken") or by a warm nothing. The woody plants
# are the ones sold bare-root, so the timing question is real for them and for nothing else in the
# table: a bag of seed potatoes does not need a planting month the day it is bought.
PLANT_ASK_EXTRA = {"sow-tree": ("bought", "buy", "buying", "picked up", "came home with",
                                "brought home", "arrived", "delivered", "new tree", "new shrub",
                                "in a pot", "bare root", "bare-root", "root ball"),
                   "sow-rose": ("bought", "buy", "buying", "picked up", "came home with",
                                "brought home", "arrived", "delivered", "new rose",
                                "in a pot", "bare root", "bare-root")}

SOW_ENTRIES = SOW_ENTRIES + [
    entry("sow-" + words[0],
          (words, SOW_ASK + PLANT_ASK_EXTRA.get("sow-" + words[0], ())),
          _planting_reply(words[0], reply),
          avoid=PLANT_AVOID.get("sow-" + words[0], PLANT_NOT), bias=1)
    for words, reply in PLANTING
]

SOW_ENTRIES.append(
    entry("sow-fruit-prune", (("apple tree", "apple", "apple trees", "pear", "pears", "pear tree",
                               "plum", "plums", "plum tree", "cherry", "cherries", "cherry tree",
                               "damson", "damsons", "fruit tree", "fruit trees"),
                              SOW_ASK),
          _prune_reply, avoid=PRUNE_NOT, bias=1))

# A rose in flower is the other half of the rose rows, and February is what "when do roses flower"
# used to get.
SOW_ENTRIES.append(
    entry("roses-flower", (("rose", "roses", "rose bush", "rose bushes"),
                           ("flower", "flowers", "flowering", "bloom", "blooms", "in flower")),
          "Roses flower from June into the first frosts: a first flush in June, then waves if you "
          "keep deadheading. Cut each spent flower back to a strong shoot rather than just taking "
          "the petals, and a feed after the first flush is what brings the second one on.",
          bias=1))

# A fruit bush or a cane you have just bought is a planting job, and none of the rows above is
# one: the crop rows answer "when do I plant it", `dig-a-hole` wants a digging verb, and the
# pantry answered "i bought a blueberry bush" with a blueberry compote. The buying words are what
# make this row the one ("i bought a gooseberry bush", "i picked up some raspberry canes"), so a
# question about pruning or a sick bush keeps its own answer.
BOUGHT_BUSH = ("blueberry", "blueberries", "blackberry", "blackberries", "blackcurrant",
               "blackcurrants", "redcurrant", "redcurrants", "whitecurrant", "whitecurrants",
               "gooseberry", "gooseberries", "raspberry", "raspberries", "loganberry",
               "loganberries", "tayberry", "tayberries", "honeyberry", "honeyberries",
               "bush", "bushes", "cane", "canes", "bare root", "bare-root", "root ball")
SOW_ENTRIES.append(
    entry("bought-fruit-bush", (BOUGHT_BUSH,
                                ("bought", "buy", "buying", "picked up", "came home with",
                                 "brought home", "arrived", "delivered", "got it home",
                                 "how do i plant", "how deep", "where do i plant",
                                 "planted", "planting", "going in")),
          "Plant it while the roots are still damp: stand the pot or the bare roots in a bucket of "
          "water for an hour, dig a hole twice as wide as the pot and the same depth, and set the "
          "plant so the old soil mark sits level with the ground. Blueberries and cranberries want "
          "ericaceous compost and rainwater rather than tap water; currants, gooseberries, "
          "raspberries and blackberries are happy in ordinary soil in sun or half shade. Firm it "
          "in with your heel, water it well, and pick the flowers off in the first year so the "
          "roots get going instead of the fruit.",
          avoid=("prune", "pruning", "pruned", "cut back", "dying", "dead", "died", "rot",
                 "rotting", "mould", "mold", "mildew", "jam", "cook", "recipe", "wine", "pie",
                 "crumble", "freeze", "glut"),
          bias=1))

# --- growing it, not just when to plant it ------------------------------------------------
# The crop rows above answer "when do I plant it" and nothing else, because the word "grow" was
# never in SOW_ASK - so "how do i grow potatoes", "how do i grow courgettes" and "how do i grow
# lettuce" were a shrug beside a row that already says how deep, how far apart and what the crop
# wants. A growing question is the same row as the sowing one and gets the same reply; the row's
# own fences still stand it down (a sick crop, a harvest, a pot or a windowsill), so an eaten
# potato is still the pest answer's.
GROW_ASK = ("how do i grow", "how to grow", "how do you grow", "how can i grow",
            "how should i grow", "how would i grow", "best way to grow", "way to grow",
            "want to grow", "trying to grow", "going to grow", "grow my own", "grow your own",
            "start growing", "start to grow", "can i grow", "could i grow", "do i grow",
            "to grow", "growing", "grow")
# "Grow" is a bare verb, so the lines where nothing is being planted have to stand down: a crop
# that is not growing, or bigger and faster, is a different question, and so is anything being
# cooked or bought.
GROW_NOT = PLANT_NOT + (
    "not growing", "isnt growing", "isn't growing", "arent growing", "are not growing",
    "stopped growing", "no growth", "wont grow", "won't grow", "dont grow", "don't grow",
    "didnt grow", "didn't grow", "hasnt grown", "hasn't grown", "came up", "come up",
    "nothing came up", "faster", "quickly", "bigger", "taller", "more fruit",
    # a spud sprouting in the bag is a storage question, not a sowing one ("shoots", "chitting":
    # not "sprouting", because _forms folds that onto sprout and sprouts are a brassica row)
    "shoots", "shooting", "chit", "chitting",
    "more fruit", "too big", "salt", "ground", "black pepper", "peppercorn", "peppercorns",
    "recipe", "recipes", "add", "season", "stuffed", "sauce", "soup", "salad", "roast",
    "cook", "cooking", "bake", "flakes", "oil", "paste", "powder", "buy", "price",
    "cost", "shop", "supermarket")
# A crop that already has a growing answer of its own keeps it: `grow-tomatoes` says more about
# pots, side shoots and feeding than its sowing row does.
# Every other crop people grow, so a row about one crop can stand down when the line names
# another: "how do i grow strawberries in pots", "can i grow courgettes in a pot" and "how do i
# grow herbs in a pot" were all answered with how to grow tomatoes, because "pots" is in that
# row's key. The crop rows now answer those, and the container entry below answers "in a pot".
OTHER_CROPS = ("strawberry", "strawberries", "potato", "potatoes", "spud", "spuds",
               "courgette", "courgettes", "zucchini", "chilli", "chillies", "chilli pepper",
               "pepper", "peppers", "lettuce", "carrot", "carrots", "onion", "onions",
               "pea", "peas", "bean", "beans", "beetroot", "radish", "radishes", "kale",
               "cabbage", "broccoli", "cauliflower", "sprouts", "garlic", "parsnip",
               "parsnips", "leek", "leeks", "squash", "pumpkin", "pumpkins", "cucumber",
               "cucumbers", "herb", "herbs", "spinach", "rocket", "swede", "turnip",
               "turnips", "salad", "salad leaves", "cress", "basil", "mint", "parsley",
               "chard", "celery")

# Why a bed or a pot is dry, when the person asks why rather than how often. The soak regime is
# the answer to "how often", and it is not the answer to "why is the soil in my raised bed dry" -
# that question wants the reason first and the mulch second. "why does my soil dry out so fast"
# was a hedge and "the soil in my pots dries out quickly" was the hot-pan card before this.
THE_DRY_WHY = (
    "A raised bed, a pot and a sandy border all lose water faster than a clay border does: the "
    "compost drains freely, sun and wind take it off the surface, and roots that have filled the "
    "pot drink what is left. Water until it runs out of the bottom and check a spade's depth down "
    "before deciding it is dry, then spread 5cm of compost or bark over the surface - that mulch "
    "is what stops the next lot evaporating, and a light sprinkle every day never reaches the "
    "roots at all.")
THE_DRY_HOW_OFTEN = (
    "Water deeply and less often, in the evening or early morning: a good soak twice a week "
    "in a dry spell beats a light sprinkle every day, because it reaches the roots instead of "
    "wetting the surface. Aim at the soil, not the leaves. Established shrubs, borders and "
    "perennials need nothing until the soil is dry a spade's depth down, while anything newly "
    "planted and anything in a pot is the exception and wants water every day or two in heat.")


# "how do i dry flowers" is a preserving question, and "dry" there is a verb: the row keys the
# bare word because that is how a dry bed is asked about, so the verb is what it stands down for.
_DRY_IS_A_VERB = re.compile(
    r"\b(?:how (?:do|can|should|would) i|how to|way to|best way to|want to|need to|trying to"
    r"|is it (?:ok|okay|safe) to|can i)\s+(?:dry|drying)\b(?!\s+out\b)")


def _a_bed_that_dries_out(memory, understood):
    """The reason first when the line asks why, the soak regime otherwise."""
    said = _words(understood)
    if _DRY_IS_A_VERB.search(said):
        return None
    if re.search(r"\b(?:why|how come)\b", said):
        return THE_DRY_WHY
    return THE_DRY_HOW_OFTEN

GROW_SKIP = ("tomato",)
GROW_ENTRIES = [
    entry("grow-" + words[0], (words, GROW_ASK), reply, avoid=GROW_NOT)
    for words, reply in SOWING + PLANTING if words[0] not in GROW_SKIP
]


def _blight(memory, reading):
    """Blight, in the order that matters: the potatoes first, because cutting the tops is urgent."""
    line = _words(reading)
    if _has(line, "rose") or _has(line, "roses") or _has(line, "spot") or _has(line, "spots"):
        return ("Black spot is a fungus that overwinters on the fallen leaves, so pick every "
                "spotted leaf off the plant and off the ground and bin them - never the compost - "
                "and it comes back much less next year. Water at the base rather than over the "
                "leaves, leave space round the plant for air to move, and feed it: a rose or a "
                "tomato that is growing hard shakes it off. A fungicide is the last resort, and it "
                "has to go on early, before the spots are everywhere.")
    if _has(line, "potato") or _has(line, "potatoes"):
        return ("Blight on a potato crop shows as brown-black patches that spread fast in warm wet "
                "weather, and the spores wash down to the tubers: cut the tops off at ground level "
                "and bin them, then lift the potatoes a fortnight later so the skins set and the "
                "spores do not reach them. Do not compost the tops. Next year grow a blight-"
                "resistant variety and leave more space between rows, because a crop that dries "
                "quickly after rain gets it less.")
    return ("Brown-black patches with a pale edge that spread fast in warm wet weather are blight, "
            "and once it is on a tomato plant the aim is slowing it, not curing it: cut off and bin "
            "the affected leaves (not the compost), water at the base in the morning rather than "
            "over the leaves, and take out some side shoots so the plants dry quicker. Pick the "
            "fruit that is already ripening - a green tomato will ripen on a windowsill indoors - "
            "and a copper fungicide slows it if it is caught early. Next year grow a blight-"
            "resistant variety with more room between plants.")


# The words that say which crop is rotting. A follow-up says "them" or "the sound ones", so when
# the line names no crop the last few turns are read for one: "can i still eat the sound ones"
# after "my apples are rotting on the tree" is a question about apples, and it was answered with
# the generic wet-and-still-air paragraph.
ROT_CROPS = ("seedling", "seedlings", "cutting", "cuttings", "stem", "stems", "potato",
             "potatoes", "onion", "onions", "garlic", "apple", "apples", "pear", "pears",
             "plum", "plums", "courgette", "courgettes", "cucumber", "cucumbers", "tomato",
             "tomatoes", "pepper", "peppers", "melon", "melons", "aubergine", "aubergines",
             "squash", "pumpkin", "pumpkins", "strawberry", "strawberries", "plant", "plants",
             "crop", "crops", "fruit", "fruits", "dahlia", "dahlias", "tree", "trees", "vine",
             "vines", "bed", "beds", "greenhouse", "ground", "allotment", "blossom end",
             "flower end", "bottom")


def _earlier_words(memory, keep=3):
    """The words of the last few turns, for a line that names no crop of its own."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    said = " ".join(str(turn.get("user") or "") for turn in turns[-keep:]
                    if isinstance(turn, dict))
    return _words({"clean": said})


def _rot(memory, reading):
    """A fruit rotting is not the same fault as a root rotting, and the fruit is the usual question."""
    line = _words(reading)
    if any(_has(line, w) for w in ("eat", "eating", "edible", "safe", "safe to eat",
                                   "still eat", "ok to eat", "use the rest", "use them")):
        # "can i still eat the sound ones" after the brown-rot answer is a food question, and
        # answering it with the same brown-rot paragraph is no answer at all: the repeat rule
        # threw the second one away and the person got a shrug.
        if (_has(line, "potato") or _has(line, "potatoes") or _has(line, "onion")
                or _has(line, "onions") or _has(line, "garlic")):
            return ("Bin every soft, slimy or smelly one, because rot in a potato or an onion is "
                    "not something to cut round: the spores travel through the flesh and the "
                    "whole one tastes wrong. A green patch on a potato is solanine, so cut it off "
                    "with a wide margin or bin that potato, and never eat one that has sprouted "
                    "and gone soft.")
        return ("Cut out the brown with a good margin around it and the sound part is fine to eat; "
                "anything soft, wet or with grey fuzz on it goes in the bin, not on the plate and "
                "not in the compost. Wash what you keep and use it in the next day or two, "
                "because fruit that has started to go will not keep.")
    if not any(_has(line, word) for word in ROT_CROPS):
        # "should i take them off", "can i still eat the sound ones": the crop is in an earlier
        # turn, and the branch that answers is the one for that crop.
        line = line + " " + _earlier_words(memory)
    if (_has(line, "seedling") or _has(line, "seedlings") or _has(line, "cutting")
            or _has(line, "cuttings") or _has(line, "stem") or _has(line, "stems")):
        return ("A seedling that collapses at soil level has damping off: the stem goes thin and "
                "water-soaked and the plant keels over. It is a fungus in cold, wet compost, so "
                "sow into fresh compost, water from below and let the surface dry between "
                "waterings, keep the pots warm and move the survivors into the light. Air moving "
                "round them matters more than anything you can spray: take the lid off the "
                "propagator as soon as the seedlings are up, and bin the collapsed ones with "
                "their compost.")
    if (_has(line, "blossom end") or _has(line, "black at the bottom")
            or _has(line, "black at the end") or _has(line, "bottom is black")
            or _has(line, "bottom of the fruit is black") or _has(line, "flower end")
            or _has(line, "rot at the end") or _has(line, "rotting at the end")
            or _has(line, "end is rotting") or _has(line, "end rot")
            or _has(line, "rotting at the flower") or _has(line, "rot at the flower")):
        return ("A black sunken patch on the bottom end of a tomato, a pepper or a courgette is "
                "blossom end rot, and it is not an infection: the fruit could not get enough "
                "calcium because the plant's water swung about. Water deeply and evenly - a good "
                "soak twice a week rather than a sprinkle every day - and mulch to hold it, and "
                "do not add calcium to the soil, because the calcium is there and the water is "
                "what moves it. Take the marked fruit off so the plant stops feeding it, and the "
                "later trusses come through sound.")
    if (_has(line, "potato") or _has(line, "potatoes") or _has(line, "bulb")
            or _has(line, "bulbs") or _has(line, "onion") or _has(line, "onions")
            or _has(line, "garlic")):
        return ("Sort them out now: bin anything soft, slimy or smelly, because one rotting potato "
                "or onion takes the rest with it, and cut the bad bits out of the sound ones and "
                "use those first. If they are still in the ground, lift them rather than leaving "
                "them in wet soil, and dry them somewhere airy before they go into store. Next "
                "year plant in a bed that drains - a raised bed if the plot holds water - and "
                "never store a bruised one with the sound ones.")
    if (_has(line, "apple") or _has(line, "apples") or _has(line, "pear") or _has(line, "pears")
            or _has(line, "plum") or _has(line, "plums")):
        return ("Fruit rotting on the tree is usually brown rot, and the spores come from the "
                "mummified fruit left hanging and off the ground from last year. Pick and bin "
                "every rotten one - on the tree and under it - and do not compost them, thin the "
                "clusters so the fruit has air round it, and prune out crowded branches in winter. "
                "Wasps and birds start the holes, so a trap from August saves a lot of fruit.")
    return ("Rot on the plant is wet and still air, so pick off every affected fruit and bin it - "
            "not the compost - and take off the leaves touching the ground so air moves under the "
            "plant. Water at the base in the morning rather than over the leaves, and pick what is "
            "sound a little earlier than you would otherwise, since a ripe fruit on wet soil is "
            "what goes next. Take the fruit with a soft brown bruise at the stalk end off as soon "
            "as you see it, because it will not ripen and it spreads.")


PEST_NOUNS = (
    ("caterpillar", ("caterpillar", "caterpillars", "cabbage white", "cabbage whites",
                     "cabbage worm", "cabbage worms")),
    ("whitefly", ("whitefly", "white fly", "whiteflies")),
    ("aphid", ("aphids", "aphid", "greenfly", "green fly", "blackfly", "black fly")),
    ("weevil", ("vine weevil", "vine weevils", "weevil", "weevils", "notch", "notches")),
    ("scale", ("scale insect", "scale insects", "scale", "sticky leaves")),
    ("mealybug", ("mealybug", "mealybugs", "white fluff", "fluffy white")),
)


def _pest_named(text):
    """The pest a stretch of text names, or "" when it names none."""
    for pest, words in PEST_NOUNS:
        for word in words:
            if _has(text, word):
                return pest
    return ""


def _pest_from_turns(memory, keep=3):
    """The pest the person named in the last few turns, for "will washing up liquid kill them".

    A follow-up drops the noun - it says "them", or "the ones on the cabbage" - and the row then
    fell through to the aphid answer, so a caterpillar conversation ended up being told to squash
    aphids. The pest already named in the conversation is the subject of the follow-up.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return ""
    for turn in reversed(turns[-keep:]):
        if isinstance(turn, dict):
            found = _pest_named(_words({"clean": str(turn.get("user") or "")}))
            if found:
                return found
    return ""


def _pests(memory, reading):
    """The pest named in the line leads: a caterpillar is not an aphid, and a net is not a spray."""
    line = _words(reading)
    pest = _pest_named(line) or _pest_from_turns(memory)
    if not pest:
        # No pest in this line and none in the conversation: the row has nothing of its own to
        # say, and the aphid paragraph is wrong for anything but aphids.
        return None
    if pest == "caterpillar":
        return ("Caterpillars are easiest picked off by hand in the evening, when they come out to "
                "feed, and dropped in a bucket of water - check the undersides of the leaves for the "
                "yellow eggs and squash those too. A net over the crop from May to September is the "
                "real fix, because the cabbage white butterfly cannot get in to lay: keep it clear "
                "of the leaves and peg the edges down. Inspect every few days, since a small "
                "caterpillar becomes a big one fast.")
    if pest == "whitefly":
        return ("Whitefly sits under the leaves and flies up in a cloud when you touch the plant. "
                "Yellow sticky traps catch the adults, and a spray of soapy water - a teaspoon of "
                "washing-up liquid in a litre - on the undersides of the leaves kills the young "
                "ones; repeat every few days, because it does not touch the eggs. Badly hit leaves "
                "come off. Check new plants before they go in the greenhouse, which is where "
                "whitefly gets in.")
    if pest == "aphid":
        return ("Greenfly and blackfly are both aphids and get the same treatment: squash them by "
                "hand or spray the undersides of the leaves and the soft growing tips with soapy "
                "water - a teaspoon of washing-up liquid in a litre. Broad beans are the usual "
                "blackfly crop, and the tips are the first place to look: pinch the top few inches "
                "out once the flowers set. Ladybirds and their larvae will clear a lot for you, so "
                "leave a marigold or a poached egg plant nearby.")
    if pest == "weevil":
        return ("Vine weevil is a root grub with a beetle above ground, and the beetles notch the "
                "leaf edges at night. The grubs are what kills the plant: tip a pot out and look "
                "for fat white C-shaped ones in the compost, then bin that compost and repot in "
                "fresh. A nematode watered on in late summer or early autumn is the cleanest "
                "control, and going out with a torch after dark deals with the beetles.")
    if pest == "scale":
        return ("Scale insects sit on stems and the undersides of leaves as little brown or white "
                "shells you can flick off with a fingernail, and they leave sticky honeydew that "
                "turns the leaves black. Wipe them off with a cotton bud dipped in rubbing "
                "alcohol, or spray the plant with soapy water - a teaspoon of washing-up liquid in "
                "a litre - a few times over a month, because the shells protect the ones "
                "underneath. Check the plant that arrived last, which is usually where they came "
                "in.")
    if pest == "mealybug":
        return ("Mealybug is the white cotton-wool fluff in the leaf joints and along the stems, "
                "and it hides in the same places as scale. Paint it off with a cotton bud dipped "
                "in rubbing alcohol, or spray the plant with soapy water - a teaspoon of "
                "washing-up liquid in a litre - every week for a month, and take off the worst "
                "leaves. It thrives in warm, still air, so give the plant more room and check the "
                "plants either side of it.")
    return ("Squash the aphids by hand or spray them with soapy water - a teaspoon of washing-up "
            "liquid in a litre - and get the undersides of the leaves and the soft new tips, which "
            "is where they cluster. Ladybirds and their larvae will clear a lot for you, so plant a "
            "marigold or a poached egg plant nearby. A strong jet of water knocks them off, and "
            "check the plant every few days, because aphids multiply fast and curl the new leaves.")


def _mildew(memory, reading):
    """Powdery mildew: dry roots and still air, whichever plant has the white powder."""
    return ("White powder on the leaves is powdery mildew, and it likes dry roots and still air: "
            "water thoroughly at the base rather than sprinkling the leaves, take off the worst of "
            "them, and open the plants up so the air moves. A spray of one part milk to nine parts "
            "water helps a little, and courgettes, cucumbers and roses usually carry on growing "
            "through it. Feed the plant and keep the water steady - mildew moves fastest on a "
            "plant that has been let dry out and then flooded.")
# The root crops, and the name the answer has to use. A row keyed on one class of crop cannot say
# "A carrot" to a person who said "my beetroot" - the answer was right and the noun was wrong, on
# every root except the carrot the row was written for.
ROOT_NAMES = ((r"carrots?", "A carrot"), (r"beetroots?|beets?", "Beetroot"),
              (r"parsnips?", "A parsnip"), (r"radish(?:es)?", "A radish"),
              (r"turnips?", "A turnip"), (r"swedes?", "A swede"), (r"celeriac", "Celeriac"))
ROOT_ASKS = ("carrot", "carrots", "beetroot", "beetroots", "beet", "parsnip", "parsnips",
             "radish", "radishes", "turnip", "turnips", "swede", "swedes", "celeriac")


def _root_split(memory, understood):
    """A root that split, forked or went woody: the root named decides the first sentence.

    "my beetroot have split", "why are my parsnips forked" and "my radishes have gone woody" are
    one question with three answers, because the cause differs - a drink after a dry spell, a
    stone in the soil, a root left in the ground too long - and the advice after it is the same.
    """
    text = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    name = "A root crop"
    for pattern, said in ROOT_NAMES:
        if re.search(r"\b" + pattern + r"\b", text):
            name = said
            break
    if re.search(r"\bbolt(?:ed|ing)?\b|\brun to seed\b|\bgoing to seed\b|\bgone to seed\b"
                 r"|\bflower(?:ing|ed)?\b|\bwent up\b", text):
        # a turnip, a swede or a radish is a biennial: a hot dry spell pushes it up a year early,
        # and once the stem goes the root stops swelling and turns woody
        first = (name + " runs to seed when a hot dry spell pushes it up in its first year, and "
                 "once the stem goes up the root stops swelling and turns woody in the ground.")
    elif re.search(r"\bfork(?:ed|ing)?\b|\btwo legs\b|\bdouble root", text):
        first = (name + " forks when the taproot meets a stone, a hard pan or fresh manure, or "
                 "when the seedlings were left crowded: the root splits in two to get round it.")
    elif re.search(r"\bwood(?:y|en)\b|\btough\b|\bpithy\b", text):
        first = (name + " goes woody when it is left in the ground too long, and in hot dry soil "
                 "it happens sooner: the root keeps growing and the middle turns hard and "
                 "stringy.")
    else:
        first = (name + " splits when it takes a drink after a dry spell: the root swells faster "
                 "than the skin keeps up, and too much feed does the same.")
    return (first + " Water little and often so the soil stays evenly damp rather than soaking it "
            "after a dry week, thin the seedlings so the roots have room, and lift them once they "
            "are a good size. The damaged ones are still fine to eat, so use those first.")

def _crop_setting_reply(memory, understood):
    """A crop that flowers and sets no fruit: which crop it is decides the first thing to try.

    "my courgettes are not fruiting" was answered with the "a courgette is botanically a fruit"
    line, "my runner beans are not setting" and "my strawberries are tiny" fell through to a chat
    shrug, and "why are my cucumbers bitter" was punted. They are four different problems wearing
    the same question, so each gets its own sentence rather than one paragraph of generalities.
    """
    text = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # a bitter cucumber is picked too late and stressed, which is a different first move from a
    # flower that set nothing, so it is asked before the crop's own paragraph. The cucumber fix is
    # only for the cucurbits: a bitter tomato or strawberry has ripened badly, not stewed in
    # cucurbitacin, and telling a tomato grower to cut the stalk end is a wrong answer.
    if "bitter" in text:
        if any(word in text for word in ("courgette", "courgettes", "zucchini", "squash",
                                         "pumpkin", "pumpkins", "cucumber", "cucumbers")):
            return ("A bitter cucumber, courgette or squash is stress, not a bad seed. Heat, a dry "
                    "spell at the root and a plant left to grow huge all push the bitter compounds up, "
                    "and they sit mostly at the stalk end, so cut that inch off and taste the "
                    "rest. Water regularly at the base, pick the fruit small and often rather "
                    "than leaving it to swell, and shade the plant in a heatwave.")
        if any(word in text for word in ("tomato", "tomatoes")):
            return ("A bitter tomato is usually one picked before it is fully ripe, or a plant "
                    "that ran short of water while the fruit was swelling. Leave the rest on the "
                    "vine until it is deep red all over, water evenly at the base, and taste a "
                    "ripe one before you blame the variety.")
        if any(word in text for word in ("strawberry", "strawberries")):
            return ("A bitter strawberry is underripe: the sugar comes last, so pick only fruit "
                    "that is red all over and leave the pale shoulders to colour. Water at the "
                    "base and net them, because a stressed or bird-pecked fruit turns sharp.")
        return ("Bitterness in a home-grown crop is usually stress - a dry spell at the root, or "
                "fruit picked before it ripened. Water evenly at the base, pick when it is fully "
                "coloured, and taste a ripe one before blaming the seed.")
    # small fruit is not a flower that never set: these plants have set, and the fruit is thin
    # because the roots cannot fill it. It must come before the crop paragraphs, or "my tomatoes
    # are small" is told they have no flowers at all. Strawberries keep their own tiny paragraph.
    if ("small" in text or "tiny" in text or "shrivelled" in text) and not any(
            word in text for word in ("strawberry", "strawberries", "plant", "plants",
                                      "seedling", "seedlings", "seed", "seeds", "leaf",
                                      "leaves")):
        return ("Small fruit on a plant that flowered means it has set more than its roots can "
                "fill. Water at the base so the soil stays evenly damp, feed a high-potash tomato "
                "feed once the first flowers open, and pick the fruit as soon as it is ready so "
                "the rest can swell. A dry spell while the fruit was setting is the commonest "
                "cause, and in a pot it can happen within a day or two.")
    if any(word in text for word in ("courgette", "courgettes", "zucchini", "squash", "pumpkin",
                                     "cucumber", "cucumbers")):
        return ("Courgettes, squashes and cucumbers carry male and female flowers on the same "
                "plant, and the female one has a tiny fruit behind the flower. If the little fruit "
                "goes yellow and drops off, the pollen never got to it - pick a male flower, peel "
                "the petals back and dab it into the middle of a female one early in the morning, "
                "when the flower is fresh. Cold nights under 10C and a very hot dry spell both stop "
                "the pollen working, and a plant fed hard on tomato feed grows leaves instead, so "
                "water at the base and wait for the weather to pass.")
    if any(word in text for word in ("runner", "french bean", "french beans", "broad bean",
                                     "broad beans", "beans")):
        return ("Runner beans set nothing when the soil dries out at the root, which is what makes "
                "the flowers drop before they are pollinated. Water at the base every evening in a "
                "dry spell, a good soaking rather than a sprinkle, and mulch round the plants to "
                "hold it. They also need bees, so leave a patch of flowers near the wigwam, and "
                "once the pods start pick them every couple of days because a bean left to swell "
                "stops the plant flowering.")
    if any(word in text for word in ("chilli", "chillies", "chili", "pepper", "peppers",
                                     "aubergine", "aubergines", "eggplant", "eggplants")):
        # the same three causes, but "A chilli" is the wrong noun for a pepper or an aubergine,
        # and an aubergine has its own first thing to check: it will not set in cool nights
        if "aubergine" in text or "eggplant" in text:
            crop = "An aubergine"
        elif "pepper" in text:
            crop = "A pepper"
        else:
            crop = "A chilli"
        return (crop + " drops its flowers for one of three reasons, and heat is the first. Pollen "
                "goes sterile above about 32C by day or 27C at night, so shade the plant from "
                "midday sun in a heatwave and keep the pot off hot paving. The second is feed - a "
                "plant given nitrogen grows leaves, so switch to a high-potash tomato feed once "
                "the first flowers open. The third is pollination, which barely happens in a "
                "greenhouse or on a windowsill, so tap the cane or the pot at midday and move "
                "pollen between the flowers with a soft brush. Nights below about 15C stop it "
                "setting as well, so do not put it outside before the nights are warm.")
    if any(word in text for word in ("tomato", "tomatoes")):
        return ("A tomato with no flowers at all is still growing rather than fruiting. Too much "
                "nitrogen, too little sun, and nights still below about 10C are the three usual "
                "reasons, so stop any high-nitrogen feed, keep the plant in full sun, and switch "
                "to a tomato feed once the first truss opens. If the flowers open and then drop, "
                "the pollen is what failed - tap the cane at midday to shake it loose, water "
                "evenly at the base rather than in fits, and damp the path down in a heatwave so "
                "the air is not bone dry. A truss that sets one or two fruits and drops the rest is "
                "usually a plant carrying more than its roots can fill.")
    if any(word in text for word in ("strawberry", "strawberries")):
        return ("Tiny strawberries are usually an old plant, and a strawberry bed is worth "
                "replanting every three years from fresh runners because the yield drops off after "
                "that. The other two causes are easy. Feed the plants with a high-potash feed as "
                "the flowers open rather than a nitrogen one, and cut off the runners instead of "
                "letting the plant spend its strength on new plants. Net them from the birds as the "
                "fruit colours, and water at the base so the fruit is not sitting wet.")
    return ("A vegetable that makes flowers and no fruit is usually a pollination problem before "
            "it is a feeding one. Leave the flowers for the bees, and hand-pollinate under cover "
            "with a soft brush or a dabbed male flower. Cold nights and very hot dry days both stop "
            "the pollen, and a plant fed on nitrogen grows leaves instead of fruit, so switch to a "
            "high-potash feed once the first flowers open. Water at the base and keep it even, "
            "because a plant that dries out drops its flowers before they set.")



# What crops in half a day of sun, said two ways: a bed that has to be planted wants the list, and
# a named crop that ripens wants to be told it will not ripen there. Telling a tomato plant to
# grow salad leaves is the same fault as the ferns, only a step smaller.
SHADE_LEAVES = ("salad leaves, spinach, chard, kale, rocket, parsley, mint, rhubarb, beetroot, "
                "radish and leeks")
# the crops that have to ripen, with the name a person would use in the answer
SHADE_SUN_CROPS = (("tomato", "Tomatoes"), ("tomatoes", "Tomatoes"),
                   ("courgette", "Courgettes"), ("courgettes", "Courgettes"),
                   ("zucchini", "Courgettes"), ("squash", "Squash"), ("pumpkin", "Pumpkins"),
                   ("pumpkins", "Pumpkins"), ("cucumber", "Cucumbers"),
                   ("cucumbers", "Cucumbers"), ("pepper", "Peppers"), ("peppers", "Peppers"),
                   ("chilli", "Chillies"), ("chillies", "Chillies"), ("chili", "Chillies"),
                   ("aubergine", "Aubergines"), ("aubergines", "Aubergines"),
                   ("bean", "Beans"), ("beans", "Beans"), ("pea", "Peas"), ("peas", "Peas"),
                   ("sweetcorn", "Sweetcorn"), ("corn", "Sweetcorn"),
                   ("strawberry", "Strawberries"), ("strawberries", "Strawberries"))


def _shade_crop_reply(memory, understood):
    """A crop in the shade: the ones that ripen want six hours of sun, and say so by name."""
    text = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    # a potato is the exception: it crops in half shade, just smaller, so it is told that
    # rather than that it will set nothing
    if "potato" in text or "potatoes" in text:
        return ("Potatoes will crop in half shade, just smaller and later, so they are the one "
                "root that earns a place in a bed with morning sun and four hours of it. What "
                "they will not do is fill in deep shade, where the tops grow and the tubers stay "
                "marble-sized. The crops that do best out of the sun are the leaves: "
                + SHADE_LEAVES + ".")
    named = [word for word, said in SHADE_SUN_CROPS if word in text]
    if named:
        crop = dict(SHADE_SUN_CROPS)[named[0]]
        return (crop + " want six to eight hours of direct sun a day, and in shade they grow "
                "leaves and set nothing - so give them the sunniest strip you have, against a "
                "south wall or in a pot you can move. What does crop on three to four hours is "
                "the leaf and root list: " + SHADE_LEAVES + ". Sow those thinner than you would "
                "in the open, and keep the slugs off, because slow growth and still damp air are "
                "what slugs and mildew both like.")
    return ("For a shady bed, grow the leaf and root crops: " + SHADE_LEAVES + ", and they crop "
            "on three to four hours of sun a day, which is what shade gives. Sow them thinner "
            "than you would in the open and keep the slugs off, because slow growth and still "
            "damp air are what mildew and slugs like best. Anything that has to ripen wants six "
            "hours and more, so keep tomatoes, courgettes, peppers, beans, squash and sweetcorn "
            "for the sunniest strip you have.")
# --- the herbs people actually grow, and what "woody", "leggy" and "spreading" mean for them ---
# A herb is pruned to keep it bushy, not to shape it: the growing tips come off and the plant
# throws out two shoots where it had one. That is the same rule for every soft herb, so the words
# are one table and the reply is one sentence per herb.
SOFT_HERBS = ("basil", "mint", "parsley", "coriander", "cilantro", "chives", "dill", "oregano",
              "thyme", "rosemary", "sage", "tarragon")
_HERB_PINCH = (
    "Pinch the top pair of leaves off each stem, just above the next pair down: every stem you tip "
    "sends out two sideshoots, so the plant bushes out instead of running up into one tall stem. "
    "Cut no lower than a leaf pair on basil, mint and coriander, because a stem cut back to bare "
    "wood usually does not come again. Pick from the top, a few stems at a time, and never strip a "
    "plant in one go. Rosemary, thyme and sage are the woody ones and are not pinched like basil: "
    "take the top third back in spring, once the worst of the frost has gone, and never cut into "
    "the old bare wood.")
_HERB_WOODY = (
    "A herb goes woody when it has been allowed to flower: the stems harden and it stops making "
    "leaf. Pinch the flower buds off as soon as they show, keep picking the tips, and cut a third "
    "of the oldest stems back to a low leaf pair in spring. Basil is the one that will not come "
    "back from old wood for long, so take cuttings in late summer or sow a fresh pot in June "
    "rather than fight it.")
_HERB_SPREAD = (
    "Mint spreads by runners just under the surface, so pulling it up makes it worse. Sink it in a "
    "pot with the rim 2cm above the soil, or a bottomless bucket, or grow it in a container away "
    "from the bed. In a border already taken over, fork out the runners in spring and again in "
    "autumn for two years, and cut the stems before they flower so it cannot seed.")
_HERB_LOOK = (
    "Soft herbs want sun, drainage and picking: water when the top of the soil is dry, feed weakly, "
    "and take the tips off often so the plant keeps growing leaf instead of stem. Basil and "
    "coriander are annuals, so a pot that lasts a season is normal; mint, thyme, oregano, sage and "
    "rosemary are perennials and want cutting back in spring.")
_SEEDLING_LEGGY = (
    "Seedlings go leggy for one reason: not enough light, which is worse indoors on a windowsill "
    "than in a greenhouse, and worse still too warm. Move them somewhere brighter and cooler, turn "
    "the tray each day so they do not lean, and prick them out deeper than they were - a tomato or "
    "a brassica will make roots along the buried stem. Next sowing, thin them out sooner and sow a "
    "little later in the year.")
_CACTUS_SOFT = (
    "A cactus or succulent that has gone soft is rotting from too much water: the tissue goes "
    "squishy and translucent from the base up, and it will not firm up again. Stop watering, take "
    "it out of the pot and cut away every soft part with a clean knife until the flesh is firm and "
    "clean, leave the cut to callous for a week, then set it on dry gritty compost. Water only "
    "when the compost is dry right through, and never leave the pot standing in water.")


_HERB_WINTER = (
    "Most soft herbs die down and come again rather than dying: chives and mint go to nothing and "
    "return from the roots in spring, parsley is a biennial so its second year is thin and woody, "
    "and thyme, sage, oregano and rosemary stay green through it. Before the first frost, move the "
    "pots against a wall and off the ground, cut the old stems down to about 5cm and mulch around "
    "the crowns. Then leave them alone: no feed, and water only when the compost has dried right "
    "out, because cold and wet kills more herbs than frost does.")
_HERB_WINTER_WORDS = ("winter", "winters", "overwinter", "overwintering", "frost", "frosts",
                      "frosty", "cold", "coming back", "come back", "comes back", "came back",
                      "survive", "survives", "survived", "dies back", "die back", "died back",
                      "dying back", "perennial", "perennials", "next year", "every year",
                      "keep going", "keeps going", "keep it going")


# The woody herbs are cut back once a year and the soft ones are picked all season, so the date
# answer splits the same way the pinch answer does. Both put the date in the first sentence.
_HERB_WHEN_WOODY = (
    "Take the top third back in spring, once the worst of the frost has gone and before the plant "
    "starts into growth: that is the one hard cut rosemary, thyme, sage and oregano need, and it is "
    "what stops them going leggy and bare in the middle. Never cut into the old bare wood, because "
    "a stem cut back to it usually does not come again, and a light trim over the tips after "
    "flowering holds the shape in between.")
_HERB_WHEN_SOFT = (
    "Pick basil, mint, parsley, coriander and chives from the top all through the growing season, "
    "from June into September: pinch or snip the top pair of leaves every week or two and the plant "
    "bushes out instead of running up into one tall stem. There is no yearly hard cut for these - "
    "stop at a leaf pair, because a soft stem cut back to bare wood usually does not come again - "
    "and take a few stems at a time rather than stripping the plant in one go.")
_HERB_WOODY_NAMES = ("rosemary", "thyme", "sage", "oregano", "lavender")


def _herbs(memory, understood):
    """Which herb question this is: a pinch, a woody stem, a mint that has taken over, or the care."""
    line = _words(understood)
    # "herb" and "herbs" on their own are named here too: "how do i stop my herbs bolting" is the
    # same question as the basil one, and the row matched while the dispatch found no plant
    named = any(_has(line, word) for word in SOFT_HERBS + ("herb", "herbs"))
    mint = _has(line, "mint")
    # Keeping a herb through the winter is its own answer: what dies down and what stays green,
    # and the one thing that kills them (a wet cold pot, not the frost). It came out of the
    # kitchen instead - "how do i keep parsley going over winter" got a jar of water.
    # Not when the line is asking what to put in under glass: "can i grow herbs in winter" wants
    # the list of which ones will work, which the sowing table answers, not how to keep the ones
    # already in the ground.
    if (named and any(_has(line, word) for word in _HERB_WINTER_WORDS)
            and not any(_has(line, word) for word in ("grow", "growing", "plant", "planting",
                                                      "sow", "sowing"))):
        return _HERB_WINTER
    if mint and any(_has(line, word) for word in ("spread", "spreads", "spreading", "spread out",
                                                  "taken over", "took over", "taking over",
                                                  "everywhere", "invasive", "contain", "control",
                                                  "stop it", "keep it in", "border")):
        return _HERB_SPREAD
    if named and any(_has(line, word) for word in ("woody", "wooden", "leggy", "flowered",
                                                   "flowering", "flower", "flowers", "bolted",
                                                   "bolting", "gone to seed")):
        return _HERB_WOODY
    # A woody herb that has already gone woody wants the why, which is above this; a herb being cut
    # wants the way of it, unless the line asked when, and then the date leads.
    _cutting = ("prune", "pruning", "pinch", "pinching", "tip", "tips", "top", "topping",
                "trim", "trimming", "cut", "cutting", "snip", "snipping", "back", "harvest",
                "harvesting", "pick", "picking")
    if named and _asks_when(line) and any(_has(line, word) for word in _cutting):
        if any(_has(line, word) for word in _HERB_WOODY_NAMES):
            return _HERB_WHEN_WOODY
        return _HERB_WHEN_SOFT
    if named and any(_has(line, word) for word in _cutting):
        return _HERB_PINCH
    if named:
        return _HERB_LOOK
    return None


def _seedlings(memory, understood):
    line = _words(understood)
    if any(_has(line, word) for word in ("leggy", "spindly", "straggly", "stretched", "stretching",
                                         "tall and thin", "fallen over", "falling over", "flopped",
                                         "flopping")):
        return _SEEDLING_LEGGY
    return None


def _cactus_soft(memory, understood):
    line = _words(understood)
    if any(_has(line, word) for word in ("soft", "squishy", "soggy", "mushy", "translucent",
                                         "rotting", "rotted", "collapse", "collapsed")):
        return _CACTUS_SOFT
    return None

# A hydrangea is two questions wearing one plant, and the person asking for blue does not want
# the watering first: "how do i make my hydrangea blue" led with the thirst sentence, so the one
# thing they asked for was the second thing they read. The same rows answer both, and the order
# of the sentences is decided by what the line asks.
def _hydrangea(memory, reading):
    """The colour answer for a colour question, the care answer for everything else."""
    line = str(reading.get("clean") or reading.get("text") or "").lower()
    if any(word in line.split() for word in (
            "blue", "pink", "purple", "colour", "color", "colourful", "acid", "alkaline", "lime",
            "limy", "ph", "soil", "ericaceous")):
        return ("The colour is the soil rather than the plant: acid soil gives blue, limy soil "
                "gives pink, and a pot is whatever compost you fill it with. Water in sulphur or an "
                "ericaceous feed through the season for blue, or add garden lime for pink, and give "
                "it a year, because it is next season's flowers that change. Water it well in dry "
                "spells as well - wilting in the afternoon sun is thirst, and the buds for next "
                "year dry up if it is left.")
    return ("Water a hydrangea well in dry spells, because wilting in the afternoon sun is thirst "
            "and the buds for next year dry up if it is left. The colour is the soil: acid soil "
            "gives blue, limy soil gives pink, so water in a sulphur or ericaceous feed for blue, "
            "and add garden lime for pink. Prune a mophead in early spring, taking the old flower "
            "heads and about a third of last year's stems, and leave a lacecap and a climbing "
            "hydrangea alone apart from the dead heads.")


# A wasp that has already stung somebody wants the sting treated, not advice on standing still:
# one answer is what to do with the next ten seconds, the other is what to do with the last five
# minutes, and the tense of the line says which.
# Which of the two answers the line wants is its tense, and the tense is not one word: "how do i
# avoid being stung" contains "stung" and wants the standing still, while "wasp sting first aid"
# contains no past tense at all and wants the treatment. So the ask is read first.
_AVOID_THE_STING = ("avoid", "avoiding", "prevent", "preventing", "not get stung",
                    "don't get stung", "dont get stung", "stop being stung", "keep them away",
                    "keep wasps away", "keep it away", "deter", "repel", "repellent",
                    "not sting me", "stop stinging me", "stop a wasp stinging me",
                    "stop it stinging", "wont leave me alone", "won't leave me alone")
STUNG = ("stung", "sting me", "bit me", "bitten", "got stung", "been stung", "i was stung",
         "swollen", "swelling", "hurts", "hurting", "sore", "itching",
         # the sting named as a thing rather than as an event: "what should i do about a wasp
         # sting", "bee sting what do i do", "wasp sting first aid" and "how do i stop a wasp
         # sting hurting" all got the standing-still answer, which is about a wasp that is
         # still there.
         "wasp sting", "bee sting", "sting on", "sting is", "sting hurts", "sting doesnt",
         "sting doesn't", "sting swell", "first aid",
         # and the events that carry no "sting" at all
         "stood on", "stepped on", "trod on", "trodden on", "it hurts", "really sore")

_WASP_AVOID = ("Don't swat it and don't wave: stand still or step away slowly and it loses "
               "interest in a few seconds, because a wasp stings when it feels trapped or the "
               "nest is threatened. Outside, keep sweet drinks covered and look in the can "
               "before you sip. If it does sting, scrape the sting out sideways with a "
               "fingernail, wash it and hold something cold on it.")
_WASP_STUNG = ("Scrape the sting out sideways with a fingernail or the edge of a card rather "
               "than pinching it, wash the spot and hold something cold on it for ten minutes; "
               "a wasp sting hurts for an hour or two and calms down with an antihistamine. A "
               "swollen face or throat, wheezing, or feeling faint needs 999, because that is "
               "anaphylaxis and it moves fast.")


# The tense of a line is what it wants, and "stop a wasp stinging me" carries an injury word for
# a sting that has not happened yet. So a line that asks how to keep away is read first, and the
# noun ("what should i do about a wasp sting") is the injury.
# Matched as whole words, because "stop" is inside "stopped" and "before" is in every other
# sentence: with the bare words, "the sting stopped hurting" and "it was fine before" both read
# as asking how to keep a wasp away from a sting that had already happened.
_AVOIDING_A_STING = re.compile(
    r"\b(?:avoid|prevent|stop getting stung|stop being stung|keep away|keep them away|"
    r"keep wasps? away|keep it away|not get stung|don'?t get stung|stings me|"
    r"if a (?:wasp|bee)|else stung)\b")


def _wasp_near(memory, understood):
    """What to do about a wasp near you, or about the sting it already gave."""
    said = (understood.get("clean") or understood.get("norm_text") or "").lower()
    if _AVOIDING_A_STING.search(said):
        return _WASP_AVOID
    if any(word in said for word in _AVOID_THE_STING):
        return _WASP_AVOID
    if any(word in said for word in STUNG):
        return _WASP_STUNG
    return _WASP_AVOID
# A bedroom, a hallway or a ceiling is a room, and a room is not a border: after a colour
# answer the follow-up "and what about the hallway" reached the cosmos list. But the same
# building words are how people ask about a border that happens to run along a wall - "which
# flowers for a north facing wall" is the cosmos list on main and is still the right answer -
# so a room noun only stands the row down when the line names nothing to grow in. Words alone
# cannot say that, because the word that decides it is the one the other half of the line has,
# so this is a guard rather than another `avoid` entry.
_A_ROOM_OR_WALL = (
    "bedroom", "bedrooms", "living room", "lounge", "hallway", "hallways", "bathroom",
    "bathrooms", "kitchen", "nursery", "landing", "stairs", "room", "rooms", "wall", "walls",
    "ceiling", "ceilings", "skirting", "woodwork", "feature wall", "wallpaper",
)
_SOMETHING_TO_GROW_IN = (
    "garden", "gardens", "border", "borders", "bed", "beds", "flower bed", "flower beds",
    "flower", "flowers", "plant", "plants", "planting", "planted", "grow", "grows", "growing",
    "pot", "pots", "planter", "planters", "container", "containers", "tub", "tubs", "trough",
    "basket", "baskets", "hanging basket", "window box", "windowbox", "window", "windows",
    "windowsill", "window sill", "sill", "shelf", "shelves", "shelving", "balcony", "patio",
    "yard", "lawn", "soil", "compost", "outdoor", "outdoors", "outside", "allotment",
    "climber", "climbers", "shrub", "shrubs", "tree", "trees", "rose", "rose bed",
)


def _says_one_of(said, words):
    """A single word has to be a word of the line: "bed" is not in "bedroom".

    A phrase is looked for in the line as it stands, because "living room" is two words that
    only mean a room together.
    """
    tokens = set(re.findall(r"[a-z']+", said))
    return any((one in said) if " " in one else (one in tokens) for one in words)


def _has_something_to_grow_in(reading):
    """True unless the line names a room and nothing in that room to grow a flower in."""
    reading = reading or {}
    said = " ".join(str(reading.get("clean") or reading.get("norm_text") or "").split()).lower()
    if not _says_one_of(said, _A_ROOM_OR_WALL):
        return True
    return _says_one_of(said, _SOMETHING_TO_GROW_IN)


# "What is compost" and "how do i start a compost bin" are the same table and different
# answers: one wants the word explained, the other wants the job. Both live here so the row is
# found either way, and the reply decides which sentence to lead with.
COMPOST_MEANS = ("Compost is garden and kitchen waste left to rot down into crumbly dark stuff "
                 "you dig back into the soil, which feeds the plants and holds water. ")
COMPOST_JOB = ("Mix roughly half green waste (kitchen scraps, grass) with half brown (cardboard, "
               "dry leaves, twigs), keep it as damp as a wrung-out sponge, and turn it now and "
               "then. No cooked food or meat, which attracts rats.")
COMPOST_WHAT_IS = ("what is compost", "what is a compost heap", "what is composting",
                   "what is compost made of", "compost mean", "compost stand for")
# A heap that has stopped working is the other half of the compost question, and it is asked
# as a why: "why is my compost not rotting", "why isnt my compost heating up", "my compost is
# not breaking down", "why is my compost slimy". None of them reached this row at all - the
# key held the making of a heap and the words of a fault are not in it - so each fell to a
# search suggestion or a chat nod. The fault words are in the key now, and the reply reads
# which fault it is, because the fix is different for each and the smell says which one.
COMPOST_AILING = (
    "rot", "rots", "rotting", "rotted", "breaking down", "break down", "broken down",
    "heating", "heating up", "heat up", "warm up", "not warm", "cold", "slow", "slowly",
    "stalled", "stopped", "slime", "slimy", "smell", "smells", "smelly", "smelling",
    "stinks", "stinking", "sour", "flies", "wet", "soggy", "dry", "nothing",
    "freeze", "freezes", "freezing", "frozen", "frost", "frosty",
)
COMPOST_SMELLY = ("smell", "smells", "smelly", "smelling", "stinks", "stinking", "sour",
                  "slime", "slimy", "soggy", "flies", "wet")
# A heap in a hard frost is not a broken heap, so it gets the winter answer rather than the
# three fixes: "will my compost heap freeze in the cold" was the mixing table, which is no
# answer to a question about the frost.
COMPOST_FROZEN = ("freeze", "freezes", "freezing", "frozen", "frost", "frosty", "snow",
                  "winter", "over winter")
COMPOST_IN_THE_COLD = (
    "The edges will freeze in a hard frost and the heap slows to nothing, which is normal - the "
    "middle keeps going and it picks up again in spring. To keep it working, fork it into one "
    "bigger heap, keep the lid on and lay a sheet of cardboard or an old compost bag over the "
    "top; a heap that is cold in mild weather is a different problem, and that one wants greens "
    "and more bulk.")
# A wet heap with no air in it is the commonest stalled heap and the only one you can smell.
COMPOST_TOO_WET = ("That smell is a heap with no air in it: too much wet green and nothing to open "
                   "it up. Fork in torn cardboard or dry leaves until it is as damp as a "
                   "wrung-out sponge, turn it over, and keep cooked food and meat out - those are "
                   "what the flies come for.")
# Everything else: the three things a heap needs to keep going, in the order to check them.
COMPOST_STALLED = (
    "A heap that has gone quiet is short of air, water or greens, and which one it is shows: "
    "bone dry means water it until it is like a wrung-out sponge, damp and cold means it wants "
    "greens - grass clippings, vegetable peelings - mixed through, and a heap that is damp and "
    "green but still doing nothing is too small to hold heat, so build it up to about a cubic "
    "metre. In winter it will slow right down and start again in spring, which is normal.")


# The sentence the compost row owes a whether-line that names something being put in the heap,
# and the whether-lines it does not. "will my compost heap freeze in the cold" is a whether-line
# on this row too, and it wants the frost answer; leading it with "No cooked food or meat, which
# attracts rats" answered a question nobody asked. So the row declares a reading and not a shape
# alone: the sentence leads when the line names a material - the thing the sentence is about -
# and every other line keeps the card as it is written.
NO_COOKED_FOOD = "No cooked food or meat, which attracts rats"
_NAMED_A_MATERIAL = re.compile(
    r"\b(?:cooked|meat|meats|bones?|food|foods|scraps?|bread|pasta|rice|dairy|cheese|milk|"
    r"fish|chicken|oil|oily|fat|fats|grease|gravy|cat food|dog food|pet food|leftovers?)\b",
    re.I)


def _the_no_cooked_food(understood):
    """The "no cooked food or meat" sentence for a line that names a material, else ""."""
    said = " ".join(str((understood or {}).get("clean")
                        or (understood or {}).get("text") or "").lower().split())
    return NO_COOKED_FOOD if _NAMED_A_MATERIAL.search(said) else ""


def compost_reply(memory, reading):
    line = str(reading.get("text") or reading.get("clean") or "").lower()
    for phrase in COMPOST_WHAT_IS:
        if phrase in line:
            return COMPOST_MEANS + COMPOST_JOB
    if _says_one_of(line, COMPOST_AILING):
        # "how do i stop my compost bin smelling" and "my compost bin smells and nothing is
        # breaking down" are the same heap as "why is my compost slimy", so the fault answer
        # is the answer to all three. A frost is not a fault, and the winter line is its own.
        if _says_one_of(line, COMPOST_FROZEN):
            return COMPOST_IN_THE_COLD
        if _says_one_of(line, COMPOST_SMELLY):
            return COMPOST_TOO_WET
        return COMPOST_STALLED
    return COMPOST_JOB


# A night of frost is the garden's question, and the frost row's two word lists -
# "cold/warm/freezing" and "protect/cover/survive/damage" - are matched by every line about a
# person being cold: "how do i keep warm in a cold office", "how do i survive the cold" and
# "how do i protect my skin from the cold" were answered with soil and fleece. What the row is
# for names something growing, or the fleece and the cloche it goes under.
_THE_GARDEN_IN_THE_COLD = (
    "plant", "plants", "planted", "planting", "pot", "pots", "seedling", "seedlings", "seed",
    "seeds", "sow", "sowed", "sowing", "garden", "gardener", "allotment", "border", "borders",
    "raised bed", "window box", "veg", "vegetable", "vegetables", "crop", "crops", "bedding",
    "shrub", "shrubs", "lawn", "grass", "flower", "flowers", "tree", "trees", "citrus", "olive",
    "banana plant", "tree fern", "hanging basket", "baskets", "greenhouse", "polytunnel",
    "cloche", "cold frame", "cuttings", "bulbs", "tender", "fleece", "compost", "herbs",
    "basil", "tomato", "tomatoes", "potatoes", "spuds", "geraniums", "dahlias", "agapanthus",
)


def _the_cold_is_the_garden_s(reading):
    """True when the line is about what is growing, not a person who is cold.

    The frost row is right about its own words and every way of asking the garden question names
    one of them, so this costs no gain; it only stands the row down for the line that says a
    person is cold, which has an answer elsewhere or none.
    """
    reading = reading or {}
    said = " ".join(str(reading.get("clean") or reading.get("text") or "").split()).lower()
    return _says_one_of(said, _THE_GARDEN_IN_THE_COLD)


# "My plant is bare in the middle" and "my plant lost its lower leaves" are the same question,
# and both are about the stems. "I lost the label on my plant" is not: it shares the loss word
# and nothing else, and a bare "lost" in the key took it, told the person to cut their plant
# back. A bare/leggy word is the question on its own; a loss word is only the question with a
# part of the plant in the line.
_BARE_STEMS = ("bare", "leggy", "spindly", "straggly", "skinny", "threadbare",
               # the same plant seen from the other end: too tall, stretched, long and thin,
               # and the question of how to make it bushy again are all short of light
               "too tall", "long and thin", "thin and long", "tall and thin", "tall and leggy",
               "stretched", "stretching", "etiolated", "bushy", "cut back", "cut it back",
               "trim it back", "prune")
_BARE_LOSS = ("lost", "losing", "lose", "dropped", "dropping", "drops", "gone", "going",
              "no leaves", "nothing on", "stems with no")
# A part of the plant is not enough: "my plant is dropping leaves" is leaf drop, which is
# overwatering or root trouble and has its own card. The bare middle is a position on the plant,
# so that is what the loss word has to come with.
_A_PART_OF_THE_PLANT = ("bottom", "lower", "middle", "base", "stem", "stems", "joint", "joints")


def _the_stems_are_what_is_bare(reading):
    """True when the line is about the plant's stems being bare, not about a lost thing."""
    reading = reading or {}
    said = " ".join(str(reading.get("clean") or reading.get("text") or "").split()).lower()
    if _says_one_of(said, _BARE_STEMS):
        return True
    return _says_one_of(said, _BARE_LOSS) and _says_one_of(said, _A_PART_OF_THE_PLANT)


# Digging a bed over is asked for in two shapes: "how do i dig over a bed" wants the spade and
# "when should i dig over my allotment" wants the season, and the card had the season last where
# nobody asking for it reads. Autumn leads for the when, and it is the same answer's own reason -
# the frost does the work of breaking the clods.
_DIG_OVER_METHOD = (
    "One spade deep is enough for most beds: turn the soil over, break up the clods and fork a "
    "couple of buckets of compost or well-rotted manure into each square metre as you go. Pick out "
    "every white root of bindweed and nettle as it comes up, or it will be back within weeks. "
    "Autumn is the best time, because the frost breaks the clods down for you, and leave it alone "
    "if the soil is wet enough to ball in your hand - digging clay when it is wet turns it into "
    "brick.")
_DIG_OVER_WHEN = (
    "Autumn, from October into December, once the beds are emptying: dig it over then and the "
    "frost does the work of breaking the clods down over winter, so the soil is workable in "
    "spring. On heavy clay that is the one time it is worth doing, because digging wet clay turns "
    "it into brick and digging dry clay leaves the lumps like stones. If you have to do it in "
    "spring, fork it over rather than digging.")
_DIG_OVER_TARGETS = ("bed", "beds", "border", "borders", "plot", "allotment", "ground", "soil",
                     "patch", "veg", "vegetable", "garden")


# "How do i get rid of a cold fast" was told to cover the tender plants, because "cold" is the
# weather to this domain and the illness to the person typing. The shapes below are the ones that
# make a cold a virus: getting rid of it, shifting it, catching it, treating it, the medicine for
# it, the parts of the body it fills up. A garden line never says any of them about a "cold"
# ("cover a cold frame" is a frame, and "a cold snap" is a snap), so the shape is the test and no
# list of plants has to be kept up to date.
_A_COLD_THAT_IS_AN_ILLNESS = re.compile(
    # the verbs people use about a virus, each tied to the cold it is about: "how do i get rid of
    # a cold", "how do i shift this cold", "how do i stop a cold getting worse". The tie is what
    # keeps "the nights are getting cold" and "my hands getting cold" out.
    r"\b(?:get|getting|got|shift|shifting|shake|shaking|fight|fighting|beat|beating|knock|"
    r"kill|killing|cure|curing|treat|treating|stop|stopping|prevent|preventing|dodge|dodging|"
    r"catch|catching|caught|come down with|coming down with|battling|suffering from)\s+"
    r"(?:rid of\s+|off\s+|over\s+|through\s+)?(?:a|an|this|that|my|his|her|their|the|another)\s+"
    r"(?:head |chest |bad |heavy |stinking |rotten |nasty |proper |lingering |summer )?colds?\b"
    # the thing you buy for one, said right next to it
    r"|\b(?:cold|flu)\s+(?:medicine|medicines|medication|tablets?|syrup|remedies?|cure)\b"
    r"|\b(?:medicine|medicines|medication|tablets?|syrup|remedy|remedies|lemsip)"
    r"\s+(?:for|against)\s+(?:a\s+|the\s+|my\s+|this\s+|that\s+)?colds?\b"
    r"|\b(?:sore throat|runny nose|blocked nose|stuffy nose|sneez\w*|cough|coughing|fever|"
    r"virus|flu|cold sore|cold sores|cold and flu|cold or flu)\b"
    r"|\b(?:feeling|feel|felt|been|am|is|are)\s+(?:\w+\s+){0,2}(?:ill|unwell|poorly|sick)\b"
    # a cold that is a part of the body is the circulation question: "how do i stop my hands
    # getting cold" was answered with "bring pots and hanging baskets in"
    r"|\b(?:keep|keeping|ward|stave|stay)\s+(?:away from\s+|off\s+)?(?:the\s+)?colds?\b"
    r"|\b(?:hands?|fingers?|fingertips?|feet|foot|toes?|ears?|nose)\s+"
    r"(?:are\s+|is\s+|get\s+|gets\s+|getting\s+|go\s+|goes\s+|going\s+)?cold\b"
    r"|\bsymptoms?\b")


def _the_cold_is_not_an_illness(understood):
    """False when the "cold" in the line is a virus rather than the weather."""
    line = " ".join(str((understood or {}).get("clean") or (understood or {}).get("text")
                        or "").lower().split())
    return not _A_COLD_THAT_IS_AN_ILLNESS.search(line)


def _dig_over_bed(memory, understood):
    """The date first when the line asks when to dig, the spade first when it asks how."""
    line = _words(understood)
    if _asks_when(line) and _has(line, "dig"):
        return _DIG_OVER_WHEN
    return _DIG_OVER_METHOD


# "Do i need to cover my plants tonight" was the car-insurance card ("by law you need third-party
# cover"), because "cover" is the same word. The garden's answer is a frost rule with a number in
# it, so it is a row of its own rather than a line in the insurance card's avoid.
_FROST_COVER = entry(
    "frost-cover",
    (("cover", "covering", "protect", "protection", "fleece", "cloche", "frost", "frosts",
      "cold", "freezing", "snap", "hardy", "tender"),
     ("plants", "plant", "seedlings", "seedling", "shoots", "tender plants", "veg",
      "vegetables", "tomatoes", "tomato", "potatoes", "spuds", "flowers", "flower", "shrubs",
      "shrub", "baskets", "hanging basket", "garden", "allotment", "greenhouse", "outside")),
    "Cover tender plants when frost is forecast, which means a night at 2C or below at ground "
    "level: the forecast for the town is often two or three degrees warmer than the garden, so "
    "watch for a clear, still night. Fleece, an old sheet, a cloche or a bucket of water beside "
    "them is enough, and take it off in the morning. Bring pots and hanging baskets in, water "
    "before a frost rather than after, and lift any spuds still in the ground.",
    # a cover for the car, the phone, the seat or the travel is another question with the same
    # word; the duvet and the sofa are their own answers
    guard=_the_cold_is_not_an_illness,
    avoid=("insurance", "third party", "third-party", "policy", "car", "van", "vehicle",
           "motorbike", "phone", "mobile", "travel", "seat", "pram", "buggy", "pushchair",
           "cot", "quilt", "duvet", "sofa", "cushion", "mattress", "table", "bbq cover",
           "barbecue cover",
           # "can you freeze potatoes" and "how do i freeze strawberries" are about a freezer,
           # not a frost: "potatoes" and "strawberries" are garden words as well as food, and
           # the row's own "freezing" is the word that brought them here. A line that says what
           # to do with food says it is the kitchen's question, so the garden stands down and
           # the freeze row answers.
           "can i freeze", "can you freeze", "can we freeze", "could i freeze",
           "how do i freeze", "how to freeze", "how do you freeze", "should i freeze",
           "is it ok to freeze", "is it okay to freeze", "freezer", "defrost", "thaw",
           "cooked", "mashed", "leftover", "left over", "recipe", "batch cook"),
    bias=2)

ENTRIES = SOW_ENTRIES + GROW_ENTRIES + _plant_entries() + [_FROST_COVER, 

    # The row below answers for a plant in a pot on a windowsill, and an "outside" in the line was
    # the only thing that stood it down - so "my outdoor plant is dropping flowers" was told about
    # a houseplant, and "the flowers on my bush are falling off" was a chat nod. The garden has its
    # own reasons: flower drop outside is mostly water, wind and pests, not a dark corner.
    entry("outdoor-flowers-dropping",
          (("outdoor plant", "outdoor plants", "outdoors", "garden plant", "garden plants",
            "border", "bush", "bushes", "shrub", "shrubs", "shrubbery", "hedge", "patio plant",
            "rockery", "climber", "clematis", "hydrangea", "hydrangeas", "wisteria", "lupin",
            "lupins", "dahlia", "dahlias", "hanging basket", "flower bed", "flowerbed",
            "bedding plant", "bedding plants", "perennial", "perennials", "outside",
            "roses", "rose bush", "climbing rose", "climbing roses", "lavender"),
           ("dropping", "dropped", "drops", "drop", "losing", "lost", "lose", "falling",
            "fallen", "fell", "shedding", "shed", "dying", "die", "flowers",
            "flower", "buds", "blooms")),
          ("Open flowers in a garden drop when their flush is over, so deadhead down to the next "
           "bud and most plants come again in a few weeks. Buds that fall before they open are a "
           "shock rather than age: dry roots are the commonest - water deeply once and mulch - "
           "then a cold night, strong wind, or greenfly and caterpillars, which you find by "
           "opening one fallen bud. Put that one thing right before you feed anything."),
          # The pot on the windowsill, the orchid and the crops keep their own answers, and
          # "leaves" is a different question from "flowers".
          avoid=("houseplant", "house plant", "houseplants", "indoor", "windowsill",
                 "orchid", "orchids", "tomato", "tomatoes", "courgette", "courgettes",
                 "strawberry", "strawberries", "chilli", "chillies", "chili", "pepper",
                 "peppers", "cucumber", "cucumbers", "pumpkin", "pumpkins", "marrow",
                 "aubergine", "aubergines", "peas", "beans", "runner", "broad bean",
                 "leaves", "leaf", "yellow", "yellowing", "brown", "brown tips", "tips",
                 "wilting", "wilt", "mould", "mold", "seed", "seeds", "sow", "prune",
                 "cut back", "buy", "gift", "present",
                 # `roses` is stemmed to `rose`, so the verb was in this row's key and "my bread
                 # rose then fell" was answered with deadheading advice. Nothing baked belongs
                 # here: a loaf, a cake and a souffle that rose and fell have their own rows.
                 "bread", "cake", "cakes", "dough", "loaf", "loaves", "sponge", "souffle",
                 "soufflé", "pastry", "bun", "buns", "scone", "scones", "meringue", "batter",
                 "risen", "proving", "proved", "the oven", "baked", "bake", "baking",
                 # Nothing here that never had a flower to lose: "my lavender has no flowers",
                 # "why arent my plants flowering" and "my hanging basket flowers died" are the
                 # other questions about flowers, and a card about the drop answered them with
                 # the flush and the deadheading.
                 # Whole phrases only: "flowering" folds onto "flowers" through the ending
                 # table, and it took every flower line out of this card with it.
                 "no flowers", "not flowering", "no blooms", "no buds", "no flower",
                 "flowers died", "flower died", "blooms died", "is dead", "looks dead",
                 # A "flower bed" in the line is the ground being worked, not a flower being
                 # lost: "how do i dig over a flower bed" was answered with the flush and the
                 # deadheading, and the digging card never got the line. The thing group and
                 # the ask group both match "flower" in that phrase, so only the avoid can
                 # stand the row down.
                 "dig", "digging", "dig over", "double dig", "spade", "spading", "fork",
                 "forking", "weed", "weeding", "hoe", "hoeing", "trowel", "turn the soil",
                 # A bed in a frost is the frost question, not a flower that dropped: the thing
                 # group holds "flower bed" and the ask group holds the bare noun "flowers", so
                 # "how do i protect my flower beds from frost" matched both and deadheaded the
                 # bed while the frost row stood down.
                 "frost", "frosts", "frosty", "cold spell", "cold snap", "cold night",
                 "cold weather", "protect from", "protect my", "fleece", "winter",
                 "frozen", "freezing", "froze"),
          # 3 rather than 1: `tall-things-stand-up` in science.py has "flowers" in its key and
          # "falling" among its standing words, so "the flowers on my bush are falling off" was
          # read as a plant going over and answered "A houseplant flops over" - a windowsill card
          # for a garden bush. A plant losing its petals is this row's question, whichever of the
          # two rows reads the line, so this one has to outbid it. Measured on `e1be564`: the
          # three `... flowers are falling off` lines move to this card and nothing else moves.
          bias=3),

    entry("herb-pruning",
          (("basil", "mint", "parsley", "coriander", "cilantro", "chives", "dill", "oregano",
            "thyme", "rosemary", "sage", "tarragon", "herb", "herbs"),
           ("prune", "pruning", "pinch", "pinching", "pinch out", "top", "topping", "trim",
            "trimming", "cut back", "woody", "wooden", "leggy", "flowered", "flowering",
            "bolted", "bolting", "gone to seed", "harvest", "harvesting", "keep it bushy",
            "stop it going woody", "going woody", "gone woody",
            # "when should i cut basil back" puts a word between cut and back, so the verb and
            # the "back" are separate keys rather than one phrase
            "cut", "cutting", "snip", "snipping", "back",
            # Keeping a herb through the winter is the same row's dispatch (see `_herbs`), and
            # without these words here the row never got the line: "how do i keep parsley going
            # over winter" scored on the kitchen's jar of water, and on the crowded supermarket
            # pot. "going" is not a word on its own - "going yellow" is the pot answer.
            "winter", "winters", "over winter", "over the winter", "overwinter", "overwintering",
            "frost", "frosts", "coming back", "come back", "comes back", "survive", "survives",
            "die back", "dies back", "died back", "perennial", "perennials", "going over",
            "keep going", "keeps going", "keep it going")),
          _herbs,
          # "how do i keep basil alive" and the yellow-leaf question have their own rows, and so
          # does the storage question in the kitchen: this row is about cutting the plant back
          avoid=("keep alive", "keep it alive", "yellow", "yellowing", "wilt", "wilted", "wilting",
                 "drooping", "fridge", "freeze", "frozen", "dry them", "drying", "dried",
                 "pesto", "sauce", "recipe", "plant it out", "when do i sow",
                 # taking a cutting is propagation, not pruning, and it has its own row: the
                 # hedging row keys "cutting" (the verb), so the plural is the one to fence here
                 "cuttings", "take cuttings", "taking cuttings", "propagate", "propagating",
                 "propagation", "root a cutting",
                 # a rosemary bush or shrub is a shrub to prune: "how do i prune a rosemary bush"
                 # was the pinch card, and the shrub row has the two dates
                 # the singular "bush" would fence "how do i make basil bushy", which is the
                 # pinch question, so the shrub names are spelled out
                 "rosemary bush", "thyme bush", "sage bush", "oregano bush", "lavender bush",
                 "herb bush", "bushes", "shrub", "shrubs", "hedge", "hedges",
                 # "can i grow herbs in winter" and "which herbs grow on a windowsill" ask for
                 # the list of which ones will work, which the growing table answers; the winter
                 # words in this row's key were taking them and answering about the ones already
                 # in a pot.
                 "can i grow", "what can i grow", "what herbs can i", "which herbs", "grow in",
                 "growing in", "grow on", "growing on"),
          bias=1),
    entry("mint-spreading",
          (("mint", "mint plant", "mint plants"),
           ("spread", "spreads", "spreading", "taken over", "took over", "taking over",
            "everywhere", "invasive", "contain", "containing", "control", "stop it", "keep it in",
            "border", "pot", "bucket", "root barrier")),
          _HERB_SPREAD,
          avoid=("mint sauce", "mint tea", "mint julep", "recipe", "cocktail", "chocolate",
                 "dried", "fridge", "freeze"),
          bias=1),
    entry("seedlings-leggy",
          (("seedling", "seedlings", "seed", "seeds", "sowing", "sowed", "propagator",
            "windowsill", "tomato", "tomatoes", "cabbage", "lettuce", "cress"),
           ("leggy", "spindly", "straggly", "stretched", "stretching", "tall and thin",
            "fallen over", "falling over", "flopped", "flopping", "pale and tall",
            "thin and tall")),
          _seedlings,
          avoid=("damping off", "mould", "mold", "mice", "slugs", "snails", "not coming up",
                 "died", "dying", "yellow", "wilting", "yellow", "when do i sow", "how deep"),
          bias=1),
    entry("cactus-soft",
          (("cactus", "cacti", "succulent", "succulents", "aloe", "agave", "jade plant",
            "christmas cactus", "echeveria"),
           ("soft", "squishy", "soggy", "mushy", "translucent", "rotting", "rotted", "rot",
            "collapse", "collapsed", "leaning over", "brown at the base")),
          _cactus_soft,
          # the yellow-leaf and brown-tip questions are the houseplant rows, and a shrivelled
          # cactus is thirst, not rot
          avoid=("yellow", "yellowing", "brown tips", "brown tip", "wrinkled", "shrivelled",
                 "shrivelled up", "thin", "not growing", "flower", "repot", "how often"),
          # a soft, rotting cactus is this row's question even though the general care row also
          # matches on the plant's name: "my succulent is rotting" was the general card
          bias=2),
    entry("basil-yellow-leaves",
          (("basil", "basil plant", "basil plants"),
           ("yellow", "yellowing", "dying", "drooping", "wilted", "turning", "leaves", "brown",
            "overwatered", "overwatering", "alive", "keep", "care", "water", "watering", "limp",
            # "how do i look after a basil plant" was a shrug while "how do i care for a basil
            # plant" was this answer: the two phrasings have to both reach it
            "look after", "looking after", "care for", "caring for", "keep it alive")),
          ("Yellow basil leaves are usually too much water and too little sun: it wants drainage, "
           "warmth and a sunny windowsill, and it hates sitting in a wet pot. Let the top of the soil "
           "dry out, move it somewhere brighter, and pinch the tops to keep it bushy."),
          # a leaf with holes in it was eaten, and the pest rows answer that: "something is eating
          # my basil leaves" was told its basil had too much water
          avoid=("eating my", "eating the", "ate my", "eaten", "eats", "holes", "holes in",
                 "nibbled", "pest", "pests", "infestation", "greenfly", "blackfly", "aphid",
                 "aphids", "caterpillar", "caterpillars", "slug", "slugs", "snail", "snails",
                 "flies", "gnats", "mould", "mold", "not growing", "dropping", "dropped")),
    entry("houseplant-yellow-leaves",
          # An indoor plant is named by its name, not by the bare word "plant": "why are my plant
          # leaves turning yellow" is a question about leaves in general, and the science answer
          # owns it (main has a test for that). "dying" and "droopy" are out of the second set
          # for the same reason: `cactus-care` owns "my cactus is dying", and the yellow lines all
          # carry the word yellow anyway.
          (("houseplant", "houseplants", "house plant", "house plants",
            "peace lily", "monstera", "spider plant", "orchid", "fern", "succulent", "cactus"),
           ("yellow", "yellowing", "leaves",
            # the whole phrase, because "leaves" and "yellow" on their own are what a tree in
            # autumn scores with too, and the indoor answer should outscore the autumn one.
            "yellow leaves", "leaves are yellow", "leaves going yellow", "leaves turning yellow",
            "leaves are turning yellow", "leaves have gone yellow", "leaves go yellow")),
          "Overwatering is the usual cause: yellow, soft leaves on a plant in soggy compost means "
          "stop watering and let the top inch of soil dry out, and check the pot has holes. Yellow "
          "lower leaves that are dry and crisp are the other story — that is just age, or a plant "
          "that needs feeding.",
          # An indoor plant turning yellow is overwatering, not autumn: the general phenomenon
          # entry in nature.py scores the same, so the specific one wins on bias.
          # "yellow" is what makes this the overwatering answer; brown tips are the other fault,
          # and a confident wrong cause is worse than the honest pass.
          avoid=("tomato", "tomatoes", "basil", "lawn", "grass", "tree", "rose", "roses",
                 "cucumber", "courgette", "pepper", "chilli", "outside", "garden bed",
                 "brown", "black tips", "crisp", "tips", "edges"),
          # bias 2: nature.py's autumn answer keys on the same two words ("leaves", "yellow")
          # and its rarity bonus can beat a named houseplant, which is never a tree in autumn.
          bias=2),
    # The light question is its own question: "should i move my monstera somewhere brighter" and
    # "does my monstera need more light" are neither a watering nor a brown-tips line, and the
    # choice module used to shrug at them. The plant words are the subject, so a sofa or a
    # monitor that wants moving does not reach this.
    entry("houseplant-light",
          (("light", "sunlight", "more light", "brighter", "bright", "sunny", "sun", "sunshine",
            "window", "windowsill", "window sill", "direct sun", "shade", "shady", "dark corner",
            "dark room", "corner", "where should i put"),
           ("monstera", "houseplant", "houseplants", "house plant", "house plants", "indoor plant",
            "indoor plants", "pot plant", "pot plants", "peace lily", "spider plant", "snake plant",
            "pothos", "orchid", "fern", "cactus", "succulent", "calathea", "zz plant", "dracaena",
            "yucca", "palm", "fiddle leaf", "rubber plant", "plant", "plants")),
          "Bright but out of direct midday sun is what most houseplants want: an east window, or a "
          "metre or two back from a south or west one. Move it closer to the glass if the stems "
          "are pale and stretched with gaps between the leaves, and further back if the leaves "
          "have brown scorched patches on the side facing the window. Turn the pot a quarter "
          "turn each time you water so it grows evenly, and give it a few weeks to settle - a "
          "plant moved into suddenly stronger light can scorch before it adjusts.",
          # an outdoor bed, a lawn or a tree has the sun's own answers, and a lamp, a ceiling
          # light or a fairy light is not what this is about
          avoid=("tomato", "tomatoes", "basil", "lawn", "grass", "tree", "trees", "rose", "roses",
                 "cucumber", "courgette", "pepper", "chilli", "outside", "garden bed", "lamp",
                 "ceiling", "fairy", "light fitting", "light bulb", "headlight", "sun cream",
                 "sunscreen", "sunburn",
                 # an outdoor bed is the garden's question, not the windowsill's: "what plants are
                 # good for a shady garden" was answered with the houseplant light advice because
                 # "shady" and "plants" carried it and nothing in the line said indoors
                 "garden", "gardens", "gardener", "border", "flowerbed", "flower bed",
                 "allotment", "outdoors", "outdoor", "back garden", "front garden", "veg patch",
                 "vegetable patch", "shrub", "shrubs", "hedge", "perennial", "perennials",
                 # a shady bed or a planting-out question is outdoors too. The phrase, not the
                 # bare word "bed": a houseplant standing in a shady bed is still a houseplant
                 "flower bed", "flowerbed", "planting flowers", "plant flowers",
                 "plant some flowers", "planting out", "plant out", "seedlings",
                 # a bed, a border or the soil is planting out, and "what can i plant in shade"
                 # was answered with the bright-window houseplant advice once "shade" and
                 # "plant" had matched this row. The planting question is plants-for-shade's.
                 "bed", "beds", "border", "borders", "flowerbed", "flower bed", "garden",
                 "soil", "ground", "allotment", "veg", "vegetable", "vegetables",
                 # A follow-up is composed from both turns, so "what should i plant in shade"
                 # then "will ferns work" reaches this row as "will ferns work plant shade" and
                 # got the houseplant answer. "plant shade" beside each other is a bed being
                 # planted, never a houseplant by a window.
                 "plant shade", "plants shade",
                 # a plant that fell off the windowsill names a windowsill and a plant and nothing
                 # about light: the fall is the pot row's question, and "fell" is not one of this
                 # row's key words, so it is safe here
                 "fell", "fallen", "falls", "dropped", "dropping", "knocked", "tipped",
                 "broke", "broken", "cracked", "smashed", "shattered", "spilled", "spilt",
                 "upside down", "on its side"),
          # bias 2: the photosynthesis entry in science.py keys on "light" and "plants" too, and a
          # named houseplant with a light question is this answer, not the biology of sunlight
          bias=2),
    entry("houseplant-brown-tips",
          (("houseplant", "houseplants", "house plant", "house plants", "plant", "plants", "tips",
            "leaf tips", "peace lily", "monstera", "spider plant", "orchid", "fern", "succulent",
            "cactus"),
           ("brown tips", "brown edges", "brown at the tips", "brown", "crisp", "black tips",
            "dried out edges",
            # "why are my plant leaves going brown at the tips" is the plainest way people ask
            # this and it reached the council's garden-waste row, because "leaves" is a key there
            # and no row had a phrase it matched. A named plant in a pot is this row's question
            # too, so the phrases go here rather than in the general row, which was winning the
            # fern on its rarer key words.
            "brown at the tip", "going brown at the tips", "going brown at the tip",
            "browning at the tips", "tips turning brown", "tips are turning brown",
            "tips of the leaves", "tips of my leaves", "tips of my plant", "tips of my plants",
            "tips of my plant's leaves", "tips of the plant's leaves", "brown tips on",
            "brown round the edges",
            "brown around the edges", "crispy tips", "crispy leaf tips",
            "edges of the leaves are brown", "leaf edges are brown")),
          "Brown, crisp tips are usually the water: tap water left to stand overnight, or "
          "rainwater, takes the fluoride and salts out that build up at the leaf edges. Dry air "
          "and letting the compost go bone dry do the same, so check both and cut the tips off "
          "with a clean pair of scissors — the leaf keeps going.",
          avoid=("tomato", "tomatoes", "basil", "lawn", "grass", "tree", "rose", "roses",
                 "cucumber", "courgette", "pepper", "chilli", "outside", "garden bed",
                 "yellow", "bottom", "base of the plant"),
          # "my cactus is going brown at the bottom" used to reach the general leaf row and now
          # needs no help; the pot row is two points behind on a named plant going brown, and it
          # is the row with the water and the fluoride in it, so the tie goes its way.
          bias=1),

    # "we want to grow some veg this year" says veg and nothing else the key names, so veg is in
    # the subject part: with "vegetables" alone there, the line reached no entry at all.
    entry("balcony-vegetables", (("vegetables", "veg"), "balcony", ("pots", "easy", "growing")),
          ("Salad leaves, cherry tomatoes, chillies, herbs, radishes and dwarf beans all do well in "
           "pots. Use containers at least 30cm deep with drainage holes, and water daily in summer, "
           "because pots dry out fast."),
          # a pot answer is about where they grow, not how long they take, and "how long do
          # vegetables take to grow" was getting it
          avoid=("how long", "take to grow", "long to grow", "weeks", "months", "when will",
                 "when are", "when should", "when do", "harvest", "ready", "ripe",
                 # A tomato on a balcony has its own row, which says when to sow it and how to
                 # pinch out the side shoots; this list is what answers a line that names no crop
                 # ("we want to grow some veg this year"). Ranking level with that row, the list
                 # took "i want to grow tomatoes on a balcony" and gave the pots answer instead.
                 "tomato", "tomatoes", "tomato plant", "tomato plants"),
          # With "veg" moved into the first part, "how do i grow vegetables in pots" came level
          # with the tomato and container rows and lost the general answer it used to get. The
          # bias keeps the list ahead for the question that names no crop at all.
          bias=1),
    # "How long do vegetables take to grow" is the first question a new grower asks, and the
    # answers it reached were a roasting time and the pot list. Weeks to the first picking, so
    # something can be planned.
    # "how long do potatoes take to grow" was the boiled-potato times, "how long do broccoli
    # take to grow" the broccoli cooking time, and "how long do peas take to grow" the frozen-pea
    # ones. The row above covers a crop with no name in the line ("how long do vegetables take to
    # grow") and stands aside for every named crop, because each crop has its own sowing-month
    # entry - but a sowing month is not a duration, so the "how long" question had no row at all
    # and the cook-time card answered it.
    entry("crop-weeks-named",
          (("potato", "potatoes", "spud", "spuds", "carrot", "carrots", "onion", "onions",
            "leek", "leeks", "parsnip", "parsnips", "beetroot", "radish", "radishes",
            "lettuce", "spinach", "kale", "cabbage", "broccoli", "cauliflower", "turnip",
            "turnips", "swede", "courgette", "courgettes", "marrow", "pumpkin", "pumpkins",
            "squash", "sweetcorn", "sweet corn", "pea", "peas", "bean", "beans",
            "runner bean", "runner beans", "broad bean", "broad beans", "french bean",
            "french beans", "dwarf bean", "dwarf beans", "tomato", "tomatoes", "chilli",
            "chillies", "chili", "chilis", "cucumber", "cucumbers", "garlic", "strawberry",
            "strawberries", "aubergine", "aubergines", "pepper", "peppers", "sprouts",
            "brussels", "spring onion", "spring onions", "salad leaves"),
           ("how long", "take to grow", "long to grow", "long before", "how many weeks",
            "weeks", "how soon", "time to grow", "grow", "ready", "harvest",
            "harvested", "pick", "picking", "crop", "cropping")),
          # a callable, so the first sentence is the crop in the line: the one fixed reply
          # opened on potatoes for "how long do carrots take to grow"
          _crop_weeks_reply,
          # the cooking time of the same vegetable, a chit, a disease and a sowing month are
          # other answers, and each one owns its own line
          avoid=("boil", "boiled", "boiling", "cook", "cooked", "cooking", "roast", "roasted",
                 "roasting", "mash", "mashed", "chips", "oven", "bake", "baked", "baking",
                 "steam", "steamed", "fry", "fried", "microwave", "recipe", "peel", "peeled",
                 "minutes", "jacket", "chit", "chitting", "chitted", "blight", "disease",
                 "rust", "mould", "rot", "this month", "month", "january", "february", "march",
                 # the pan words: "how long do carrots take to soften" is a cooking time, and
                 # this row keys the same crop and the same "how long". KITCHEN_WORDS is the
                 # sowing rows' fence; this row carries a list of its own, so it needs the verbs.
                 "soften", "softens", "softened", "softening", "tender", "tenderise",
                 "simmer", "simmered", "blanch", "blanched", "parboil", "parboiled",
                 "brown in a pan", "brown the onions", "until crisp", "al dente", "stir fry",
                 "saucepan", "hob", "drain", "drained", "pan of", "in a pan",
                 # A named dish is not a crop and its clock is the pan's: "how long does chilli
                 # con carne take" was answered with "Chillies are 16 to 20 weeks from seed".
                 # The dish words here are whole names, never a bare word that is also a crop -
                 # "curry" is a curry leaf plant and "soup" is a soup pea, so neither is here.
                 "con carne", "con carni", "chilli con", "bolognese", "stew", "casserole",
                 # and the pan itself, which this row's own list was missing
                 ) + A_PAN_LINE + (
                 "april", "may", "june", "july", "august", "september", "october", "november",
                 "december", "when do i sow", "when should i sow", "when do i plant",
                 "when should i plant", "what month", "sow", "sowing", "plant out",
                 "spacing", "how far apart", "feed", "fertiliser", "compost", "pot", "pots",
                 "indoors", "windowsill", "greenhouse", "freeze", "frozen", "keep", "store",
                 "why", "yellow", "wilting", "holes", "died", "dying", "not growing",
                 # "how do i grow potatoes" wants the planting method, not a number of weeks
                 "how do i grow", "how to grow", "how do you grow", "how can i grow",
                 "how should i grow", "growing tips", "tips for growing", "best way to grow",
                 "beginner", "beginners", "for beginners", "first time", "new to growing",
                 "start growing", "getting started",
                 # choosing a ripe one is not a count of weeks: "how do i pick a good tomato"
                 # was answered with the 16 to 20 weeks from seed, because "pick" is a harvest
                 # word here and the ripeness row is the one that answers how to choose one
                 "pick a good", "pick good", "picking a good", "pick the best", "pick a ripe",
                 "choose a good", "choosing a good", "choose the best", "choose a ripe",
                 "how do i pick", "how do i choose", "how to pick", "how to choose",
                 "which to pick", "which one to pick", "good one", "good ones", "best one"),
          # a nudge over the cook-time card, which ties on the same word ("how long do potatoes
          # take to grow" scored the same for this row and for the boiled-potato one). The
          # cooking vocabulary in avoid is what keeps the boil and roast lines where they were.
          bias=2),
    entry("crop-weeks",
          (("grow", "growing", "grown", "plant", "planted", "planting", "sow", "sowed", "sowing",
            "seed", "seeds", "crop", "crops", "vegetables", "veg"),
           ("how long", "take to grow", "long to grow", "weeks", "months", "how many weeks",
            "how many days", "time to", "how soon")),
          "Quick from seed: salad leaves and radishes in 4 to 6 weeks, spring onions 8, dwarf "
          "beans 10 to 12. Tomatoes, courgettes and chillies take 12 to 16 weeks from sowing, and "
          "new potatoes 10 to 12 from planting (maincrop 18 to 20). Check the seed packet for the "
          "variety, because a fortnight either way is normal, and sow a small row every three "
          "weeks so the crops arrive in a trickle rather than all at once.",
          # a plant indoors, a cooking time and a named crop's own sowing entry are other answers
          avoid=("houseplant", "houseplants", "indoor", "monstera", "orchid", "orchids", "fern",
                 "cactus", "succulent", "basil", "cook", "cooking", "boil", "boiled", "roast",
                 "roasted", "oven", "steam", "steamed", "recipe", "eat", "keeping", "store",
                 "bean sprouts", "sprouts", "sprout", "beard", "hair", "business", "crystal",
                 # a named crop has its own sowing and harvest row, with its own month
                 "onion", "onions", "potato", "potatoes", "carrot", "carrots", "garlic", "tomato",
                 "tomatoes", "broccoli", "cabbage", "kale", "pea", "peas", "bean", "beans",
                 "beetroot", "lettuce", "lettuces", "radish", "radishes", "courgette",
                 "courgettes", "leek", "leeks", "parsnip", "parsnips", "spinach", "rhubarb",
                 "strawberry", "strawberries", "apple", "pear", "chilli", "chillies",
                 "cucumber", "pumpkin", "squash", "sweetcorn", "corn", "turnip", "swede",
                 "harvest", "harvested", "harvesting", "lift", "lifting", "ripe", "ready",
                 # "what can i plant this month" is the planting-month answer, which has the
                 # month in it; this row is weeks to the first picking
                 "grass", "lawn", "turf", "moss", "wildflower", "green manure",
                 "this month", "this week", "right now", "plant now", "planting now",
                 "sow now", "january", "february", "march", "april", "may", "june", "july",
                 "august", "september", "october", "november", "december", "month by month",
                 # a bulb is planted on its own calendar and is not grown from seed: "best time
                 # to plant bulbs" got the weeks-to-salad list
                 "bulb", "bulbs", "tulip", "tulips", "daffodil", "daffodils", "allium",
                 "alliums", "crocus", "snowdrop", "snowdrops", "bulb planting")),
    entry("tulip-bulbs", ("bulbs", "tulip", "planting"),
          ("Plant tulip bulbs in November, later than daffodils, which go in from September: a cold "
           "spell helps them flower well. Plant them three times their own depth and pointy end up.")),
    entry("allotment-overgrown",
          (("allotment", "allotments", "plot"),
           ("overgrown", "weeds", "weedy", "clear", "start", "look after", "care", "first",
            "new plot", "take on", "took on")),
          ("Cover most of it with cardboard and compost to kill the weeds while you work on one bed "
           "at a time, and start with the bit you can see from the gate. Clear, dig and plant that "
           "bed this month, then move on; trying to do the whole plot at once is how people give up.")),
    # "my house plants keep dying" is written both ways, and the dying is the question, so the
    # entry takes the words people use for a plant indoors and the words for it going wrong.
    entry("houseplants-watering",
          (("houseplants", "house plants", "house plant", "houseplant", "indoor plants",
            "indoor plant", "pot plants", "pot plant", "care", "overwatering",
            # a named houseplant is the subject too: "how often should i water my monstera" is
            # the same question as "how often should i water my houseplants"
            "monstera", "peace lily", "spider plant", "snake plant", "pothos", "fern", "orchid",
            "calathea", "zz plant", "dracaena", "yucca", "fiddle leaf", "rubber plant",
            # a gift plant with a name of its own is the same care question, and it had no answer
            # at all: "how do i keep a poinsettia alive" and "how do i care for a cyclamen" were a
            # shrug while "how often should i water my monstera" was answered
            "poinsettia", "cyclamen", "amaryllis", "african violet", "aloe", "jade plant",
            "anthurium", "kalanchoe", "begonia", "hyacinth"),
           ("water", "watering", "how often", "how much", "look after", "care", "care for",
            "dying", "die", "dies", "dead", "drooping", "droopy", "yellow", "leaves", "light",
            "root rot",
            # "keep it alive" is how a gift plant is asked about, and none of the words above
            # caught it
            "keep", "keeping", "alive", "thriving", "healthy", "happy", "last",
            # a houseplant that looks unhappy is this answer, and it had no way in: "my
            # houseplant is looking sorry for itself" was told which flowers to buy, because
            # `flowers-or-plant` reads "plant" and "sorry" as a gift question
            "look sad", "looks sad", "looking sad", "unhappy", "miserable",
            "sorry for itself", "sulking", "sulky")),
          ("Water when the top couple of centimetres of compost is dry, not on a fixed day, and let "
           "it drain away rather than sitting in water. Most houseplants die of too much water rather "
           "than too little: a pot with no drainage hole, or a saucer left full, rots the roots and "
           "the leaves go yellow and drop. If the compost smells sour, repot in fresh compost and "
           "water less; if it is bone dry and light, soak the pot in a bowl for ten minutes. Beyond "
           "that it is light - most want a bright spot out of direct sun - and a feed every few "
           "weeks in spring and summer only."),
           # "care for" is now a key word, and "care" is in the first group, so "how do i care for
           # my lawn in autumn" was two matches and got the houseplant answer: anything grown
           # outdoors, or named as a garden plant, is the garden's own line.
           avoid=("lawn", "lawns", "grass", "mow", "mowing", "hanging basket",
                  "hanging baskets", "window box", "window boxes",
                  "border", "borders", "allotment", "plot", "beds", "roses", "rose",
                  "hydrangea", "lavender", "tomato", "tomatoes", "potato", "potatoes",
                  "tree", "trees", "shrub", "shrubs", "hedge", "hedges", "seeds", "seedlings",
                  "sow", "sowing", "greenhouse", "compost heap", "weeds", "slug", "slugs",
                  "snails", "cats", "cat", "dog", "dogs", "puppy", "puppies", "pup",
                  "kitten", "kittens", "rabbit", "hamster", "guinea pig", "budgie",
                  # and "how do i care for my new tattoo" is two matches the same way: a tattoo
                  # is not a pot plant, and clothing.py has two cards for it
                  "tattoo", "tattoos"),
           # a person is not a pot plant either, and every word above is about what is grown
           guard=_the_care_is_for_a_person),
    entry("watering-plants",
          (("plants", "plant", "houseplants", "houseplant", "pots", "containers"),
           ("how often", "how much", "water", "watering", "away on holiday", "holiday",
            "every day", "daily")),
          ("Check the soil before you water, not the calendar: push a finger in and water only when "
           "the top few centimetres are dry, then water until it runs out of the bottom. Plants in "
           "pots need it far more often than plants in a border, and in hot weather a big soak twice "
           "a week beats a sprinkle every day, because it gets water down to the roots."),
          # a plant that is going yellow or drooping is its own question in this file
          # "how do plants drink water" is about what happens inside the plant, so the transport
          # fact takes it; this entry answers only the pot in front of you.
          avoid=("yellow", "yellowing", "brown", "drooping", "droopy", "dying", "turning",
                 "photosynthesis", "basil", "hydrangea", "tomato", "tomatoes",
                 "drink", "drinks", "drinking", "absorb", "stems", "stem",
                 # "how often should i feed my plants" is a feeding question, and both ask
                 # "how often": the feed answer leads with March to September, not with a finger
                 "feed", "feeds", "feeding", "fertiliser", "fertilizer", "plant food",
                 "nutrients")),
    # "how often should i water my garden" is the beds and borders, and it had no owner: the
    # pot entry above wants a plant named, so the commonest watering question in the file
    # went to a hedge. A lawn (`lawn-watering`) and a tomato (`tomato-watering`) are their own
    # answers and are on the avoid list, because neither wants a border's soak.
    entry("watering-garden",
          # "my beds" and "the beds" are phrases and so weigh a little more than the bare word:
          # the dry-eye card keys "how often" and "water" too, and it took "how often should i
          # water my beds", which is a garden line if ever there was one.
          (("garden", "beds", "bed", "my beds", "the beds", "flower beds", "raised beds",
            "border", "borders", "shrubs", "shrub", "flowers",
            "new plants", "newly planted", "hanging baskets", "hanging basket",
            # the bed is often named as the soil in it, and the dry line names nothing else:
            # "why does my soil dry out so fast" and "why is my soil so dry" both reached
            # nothing, so the phrases that carry the bed are here rather than a bare "soil".
            "why does my soil", "why is my soil", "why has my soil", "why are my beds",
            "soil dry out", "soil dries", "my ground", "allotment plot", "veg plot",
            "garden plot", "allotment", "planters",
            "planter"),
           ("how often", "how much", "water", "watering", "every day", "daily", "drought",
            # "dry" on its own is how people ask why a bed is dry, and the first key part is
            # what keeps it a garden: "why is the soil in my raised bed dry" needed it.
            "dry soil", "the dry soil", "soil dry",
            "hot weather", "heatwave", "hose", "hosepipe", "sprinkler", "ban",
            # a basket that dries out between waterings is the watering question, and so is the
            # bed itself said to be dry: "my beds are bone dry" was a load of washing
            "dried out", "drying out", "dries out", "dry out", "dried up", "gone dry",
            "keeps drying", "bone dry", "parched", "cracked", "cracking",
            # "dry" on its own is the shape of the question people actually type, and the first
            # key part is what keeps it to a garden: "why is the soil in my raised bed dry".
            "dry", "too dry", "so dry", "is dry", "very dry", "dry and", "dries", "drying")),
          _a_bed_that_dries_out,
          # A bed is a flower bed here, not the one you sleep in: "how often should i change my
          # bedding" and "how often do you wash bedding" reached this entry, because bedding's
          # forms are {bedding, bedd, bedde, bed} and it met the key word "bed". The word
          # "bedding" cannot go in this list - its forms hold "bed", so it would stand the entry
          # down on "the beds need watering" too - so the guard is the laundry words that a
          # bedding question always carries and a watering question never does.
          avoid=("wash", "washing", "washed", "change", "changing", "sheets", "sheet", "duvet",
                 "pillow", "pillows", "pillowcase", "mattress", "linen", "laundry",
                 "washing machine", "tumble dryer", "quilt", "blanket",
                 "lawn", "grass", "turf", "mow", "mowing", "mow the", "weed", "weeds", "weeding",
                 "feed", "feeds", "feeding", "fertiliser", "fertilizer", "plant food",
                 "tomato", "tomatoes", "cactus", "succulent", "indoor", "houseplant",
                 "houseplants", "orchid", "monstera",
                 # a bag of something is a quantity, not a soak: "how much bark do i need for a
                 # border" is how much to buy, and the materials row works that out as a volume
                 "gravel", "shingle", "chippings", "bark", "bark chippings", "mulch",
                 "topsoil", "top soil", "compost", "bags of", "tonnes of", "tons of",
                 # a garden "bed" is not a bed you sleep in, and "bedding" folds to the same word:
                 # "how often should i wash my bedding" was answered with how to water a border
                 # not "bedding" on its own: it folds to "bed", and "how often should i water my
                 # beds" would then stand this card down too
                 "sheets", "sheet", "duvet", "pillow", "pillowcase", "pillowcases",
                 "mattress", "wash my bedding", "clean my bedding", "clean the bedding",
                 "cleaning the bedding", "bedding smells", "laundry", "washing machine",
                 "tumble dryer",
                 "pyjamas", "nightie", "linen",
                 # "how much should a border terrier weigh" is the dog's body weight, and the
                 # garden's key word "border" plus "how much" took it: nothing in a garden is
                 # asked about in kilos, so a weighing line is not this card
                 "weigh", "weighs", "weighing", "how heavy", "kg", "kilos", "kilogram",
                 "kilograms", "lbs", "weight")),
    entry("repot-a-plant",
          (("repot", "repotting", "pot bound", "root bound", "bigger pot"),
           ("plant", "plants", "pot", "houseplant", "roots", "soil", "compost")),
          ("Move it up one pot size, no bigger: roots circling the bottom of the old pot, or water "
           "running straight through, mean it is ready, and a pot that is far too big holds water "
           "round the roots and rots them. Use fresh compost, tease the roots out a little, and keep "
           "it out of direct sun for a week after.")),
    # A cutting is a question about a plant, and two science rows took it: "how do i propagate a
    # spider plant" reached the spider-silk answer (a spider is not a spider plant) and "how do i
    # root a cutting in water" the one about how plants drink. Nothing in the garden table knew
    # the word, so the whole family - rose, geranium, fuchsia, monstera, pothos, a houseplant -
    # shrugged. The cutting words are one part and the plant is the other, so a line about cutting
    # the grass or cutting costs is not this row.
    entry("take-cuttings",
          (("take a cutting", "take cuttings", "taking cuttings", "cutting", "cuttings",
            "softwood cutting", "softwood cuttings", "stem cutting", "root a cutting",
            "root cuttings", "strike a cutting", "propagate", "propagating", "propagation",
            "root in water", "roots in water"),
           ("rose", "roses", "geranium", "geraniums", "pelargonium", "pelargoniums", "fuchsia",
            "fuchsias", "plant", "plants", "shrub", "shrubs", "lavender", "hydrangea",
            "houseplant", "houseplants", "house plant", "house plants", "indoor plant", "herb",
            "herbs", "busy lizzie", "impatiens", "begonia", "begonias", "salvia", "verbena",
            "penstemon", "hebe", "buddleia", "jasmine", "honeysuckle", "ivy", "trailing plant",
            "monstera", "pothos", "spider plant", "snake plant", "tradescantia"),
           # a cutting put in a glass rather than in compost names no plant at all ("how do i
           # root a cutting in water"), so the water is a part of its own: two of the three parts
           # are enough, and the cutting words are always one of them.
           ("water", "in water", "glass of water", "jar of water", "glass", "jar",
            # "how do i take a cutting" names no plant either, and the asking around it is all
            # the rest of the line: the bare question shrugged while "how do i take cuttings from
            # a rose" was answered. These phrasings carry the job on their own.
            "how do i take a cutting", "how do i take cuttings", "how to take a cutting",
            "how to take cuttings", "how do i root a cutting", "how do i root cuttings",
            "how to root a cutting", "how do i strike a cutting", "how do i propagate",
            "how to propagate", "propagate a plant", "how do you take cuttings",
            "how do you propagate", "when do i take cuttings", "when should i take cuttings",
            "when do you take cuttings", "best time to take cuttings",
            "best time to take a cutting", "can i propagate",
            "how do i take a softwood cutting", "how to take a softwood cutting",
            "how do i take a stem cutting", "how do i take root cuttings",
            "how do i take some cuttings", "how do i root some cuttings",
            "when do i take a cutting", "when to take cuttings", "when is the best time to take",
            "what time of year do i take cuttings", "what time of year should i take cuttings",
            "what month do i take cuttings")),
          _cutting_reply,
          # "cutting" is a hundred other things: the grass, a hedge, costs, cake, a joint of meat
          avoid=("grass", "lawn", "mow", "mowing", "hedge", "hedges", "cost", "costs", "spending",
                 "budget", "cake", "cook", "cooking", "meat", "wood", "steel", "metal", "wire",
                 "hair", "out", "off", "down", "short", "fine",
                 # "cutting" is a form of "cut", so "how do i cut back a buddleia" and "when do
                 # i prune my fuchsia" were reaching the cuttings answer: cutting a plant back is
                 # the pruning rows' job, and a cutting is a piece you take off it
                 "cut back", "cutting back", "cut it back", "prune", "pruning", "pruned",
                 "deadhead", "deadheading", "hard back", "trim", "trimming"),
          ),
    # Dividing a clump is how a perennial is made into three, and the whole family shrugged:
    # "how do i split a perennial", "how do i divide hostas", "when should i divide perennials".
    # Both words are wide ("split the bill", "divide by ten"), so the second part names a plant.
    entry("divide-perennials",
          (("divide", "dividing", "division", "split", "splitting", "lift and divide",
            "how do i divide", "when do i divide", "when should i divide", "how do i split",
            "when do i split", "when should i split", "separate", "separating",
            # a clump that has outgrown its space is the same job asked the other way round:
            # "my hostas have got huge, they're taking over the border" got the party-host row
            "taking over", "taking it over", "taken over", "got huge", "grown huge",
            "too big", "outgrown", "outgrowing", "overcrowded"),
           ("perennial", "perennials", "hosta", "hostas", "daylily", "day lilies", "day lily",
            "clump", "clumps", "border plant", "border plants", "hardy geranium", "phlox",
            "crocosmia", "montbretia", "shasta daisy", "heuchera", "lily", "lilies", "sedge",
            "ornamental grass", "bamboo", "rhubarb", "strawberry", "strawberries", "plant", "plants",
            "shrub", "shrubs")),
          "Water the clump the day before, then fork it out on all sides and lever it up. Two "
          "forks back to back in the middle, pushed away from each other, part most clumps without "
          "cutting anything; a spade or an old bread knife does the rest. Shake off the loose "
          "soil, cut back the old foliage, and replant each piece at the depth it was growing, then "
          "water it in and keep it watered for a fortnight. Divide summer-flowering perennials in "
          "spring and spring-flowering ones in autumn, and hostas whenever they are in leaf but not "
          "in flower.",
          # the wide halves: a bill, a sum, a marriage
          avoid=("bill", "bills", "money", "rent", "cost", "costs", "tax", "cheque", "by 2",
                 "by 10", "by ten", "sum", "sums", "maths", "math", "number", "fraction",
                 "decimal", "percentage", "long division", "divide by", "dividing numbers",
                 "up with", "from", "husband", "wife", "partner", "expenses",
                 # a running bamboo is not divided to stop it: it is barriered, and bamboo-spread
                 # is the row for that. "taking over" in the key above was pulling the bamboo
                 # question in here.
                 "bamboo", "bamboos", "rhizome", "rhizomes"),
          ),
    # "what is the best compost for houseplants" shrugged, and the compost row is about the heap
    # in the garden, which is a different question with the same word in it.
    entry("houseplant-compost",
          (("compost", "potting compost", "potting mix", "potting soil", "peat", "peat free",
            "perlite", "grit", "bark", "soil mix"),
           ("houseplant", "houseplants", "house plant", "house plants", "indoor plant",
            "indoor plants", "for my plant", "pot", "pots", "repot", "repotting", "best",
            "which one", "what kind", "what sort")),
          "Use a peat-free multi-purpose with a good third of perlite or grit stirred through for "
          "drainage, or a ready-made houseplant mix, which is the same thing in one bag. Garden "
          "soil in a pot sets like concrete and brings in pests, so leave it outside. Orchids want "
          "bark chips and cacti want gritty cactus compost; seedling compost is too light for a "
          "plant that lives in the same pot for years.",
          avoid=("heap", "bin", "kitchen", "food waste", "make your own", "make my own",
                 "turn the compost", "smells", "smell", "rats", "flies", "allotment"),
          ),
    # "how do i stop my bamboo spreading" and "how do i stop bamboo taking over" were a shrug,
    # which is the wrong answer to give about a plant that arrives under a neighbour's fence.
    # A potato in a bag is a job with numbers in it, and "how do i earth up potatoes" was a
    # shrug: the container answer said 40cm and 30 litres and stopped, and earthing up is the
    # half of the job that keeps the tubers from going green.
    entry("tomato-feed",
          (("tomato", "tomatoes", "tomato plant", "tomato plants", "tomato seedlings"),
           ("feed", "feeds", "feeding", "fertiliser", "fertilizer", "tomato feed", "potash",
            "food")),
          "Start feeding when the first truss of flowers has set fruit, then weekly: a high-potash "
          "tomato feed, diluted as the bottle says, watered onto damp soil rather than dry. Too much "
          "nitrogen before that gives you a big leafy plant and no tomatoes, and a plant in fresh "
          "grow bag compost usually needs nothing for the first six weeks.",
          ask=("tomato", "tomatoes"),
          avoid=("baby", "babies", "breast", "newborn", "ketchup", "sauce", "recipe", "recipes",
                 "chutney", "pizza")),
    # A crop in a pot is its own question: depth and drainage decide whether it works, and the
    # spacing on the open-ground rows is no help in a bucket. One answer covers every crop that
    # grows in a container, keyed on the crop and the words for the pot.
    entry("grow-in-a-pot",
          (OTHER_CROPS + ("tomato", "tomatoes"),
           ("pot", "pots", "container", "containers", "planter", "planters", "grow bag",
            "grow bags", "growbag", "bucket", "tub", "basket", "hanging basket", "window box",
            "windowbox", "raised bed", "raised beds", "compost bag", "size pot", "big pot",
            # a bag or a sack is how people buy food, not a planter: bare "bag" made
            # "what can i make with half a bag of spinach" a grow-bag answer. The phrases that
            # do mean growing potatoes in a bag are kept whole.
            "growing bag", "growing bags", "potatoes in a bag", "potatoes in bags",
            "potato in a bag", "potato in bags", "trug")),
          ("The pot has to be deep enough and drain: 30cm deep with holes in the bottom for salad, "
           "herbs, radishes and dwarf beans, 40cm and 30 litres or more for potatoes, a courgette or "
           "a tomato, and strawberries are fine in a 20cm pot or a hanging basket. Use fresh "
           "multipurpose compost, water when the top finger-depth feels dry (twice a day in a "
           "heatwave, because a small pot dries out fast), and feed weekly once flowers open: "
           "bagged compost runs out of food in about six weeks."),
          ask=("grow", "growing", "grow my own", "plant", "planting", "sow", "sowing", "can i",
               "could i", "how", "what size", "which pot", "best", "good"),
          # it names the container as well as the crop, so it is the more specific of the two
          bias=1,
          avoid=("houseplant", "houseplants", "pot plant", "monstera", "orchid", "fern", "cactus",
                 "succulent", "peace lily", "repot", "repotting", "root bound", "rootbound",
                 "pot bound", "sick", "dying", "yellow", "wilting", "not growing", "isnt growing",
                 "isn't growing", "stopped growing", "recipe", "recipes", "cook", "cooking",
                 "roast", "soup", "salad dressing", "store", "storing",
                 # a bag in a keeping question is a bag from the shop, not a grow bag: "how do i
                 # keep a bag of salad from going slimy" is about the fridge, and a pot depth is
                 # no help with it. Keeping and wasting are the whole class, not the one line.
                 "slimy", "going slimy", "keep fresh", "keeps fresh", "keep it fresh",
                 "keep them fresh", "stays fresh", "stay fresh", "last longer", "lasts longer",
                 "last a week", "goes off", "gone off", "go off", "fridge", "freezer", "freeze",
                 "waste", "wasting", "use up", "washed", "wash the leaves",
                 # and the keeping question about the shop's bag: "how do i keep a bag of salad
                 # fresh" is about the fridge, and it slipped past "keep fresh" because the
                 # words are not side by side.
                 "keep a bag", "keep the bag", "keep a punnet", "how do i keep",
                 "keeping a bag", "make it last", "make them last")
          # and the whole dish frame, because a crop in a bag is still a crop to cook: every
          # "what can i make with a bag of <crop>" was answered with how deep the pot must be
          + DISH_ASK),
    entry("grow-tomatoes", ("tomatoes", "growing", "pots", ("plants")),
          # "when should i plant tomatoes" is this row's line - a test pins that - so the date
          # comes first and the growing advice after it, rather than the answer to a "when"
          # question opening with "give them sun".
          ("Sow indoors in March or April and plant out in early June, once the nights stay above "
           "10C. Give them sun, a big pot or grow bag, and water at the base regularly, because "
           "irregular watering is what splits them. Pinch out side shoots on cordon varieties, "
           "feed weekly once the first truss sets, and pick as soon as they are ripe."),
          # "pots" and "plants" are in the key, so an indoor plant with yellow leaves was getting
          # how to grow tomatoes; a named houseplant has its own answer (nature.py). A yellow or a
          # dying tomato is still this entry's, so those words stay out of the avoid.
          avoid=("pot plant", "pot plants", "houseplant", "houseplants", "indoor", "monstera",
                 "orchid", "fern", "cactus", "succulent", "peace lily", OTHER_CROPS,
                 # a herb in a pot is not a tomato in a pot: "how do i grow rosemary in a pot"
                 # and "how do i grow thyme in a pot" were getting "pinch out side shoots on
                 # cordon varieties", and a tomato row should never fire on a herb's name.
                 "herb", "herbs", "basil", "rosemary", "thyme", "mint", "parsley", "chives",
                 "coriander", "cilantro", "oregano", "dill", "sage", "tarragon",
                 # a plant that is not growing is asking why, not asking how to grow tomatoes
                 "not growing", "isnt growing", "isn't growing", "stopped growing", "no growth",
                 "wont grow", "won't grow", "not grown", "stunted",
                 # a tomato that has gone limp is a watering question, not a sowing date
                 "wilting", "wilted", "wilt", "drooping", "droopy", "limp", "flopping",
                 # a tomato with an illness on it is the illness row's question, not the growing
                 # one: "my tomato plants have blight" was getting "give them sun, a big pot"
                 "blight", "blighted", "mildew", "mould", "mold", "rot", "rotting", "disease",
                 "diseased", "infected", "aphids", "blackfly", "whitefly", "spots", "spotting")),
    entry("lawn-care",
          (("lawn", "grass", "turf"),
           GONE_WILD + (
            "mow", "mowing", "cut", "cutting", "how often", "patchy", "patches", "bare", "bald",
            "care", "look after", "feed", "feeding", "level", "reseed", "scarify", "scarifying",
            # the jobs people ask for by name, so the answer below can tell them apart: without
            # "thatch", "spiking" and "compacted" here "how do i get rid of thatch" reached nothing
            "thatch", "thatching", "dethatch", "dethatching", "spiking", "spike", "compacted",
            "compaction", "hollow tine", "hollow tines", "aerated", "aeration", "raking out",
            "spongy", "reseeding", "oversow", "over sow", "sow grass",
            "aerate", "aerating", "autumn", "yellow", "yellowing", "brown",
            "browning", "dying",
            # "the grass in my garden is dead" and "my lawn is dead" reached nothing at all
            "dead", "died", "killed", "dead grass",
            # "how do i make my grass greener" was answered with an explanation of chlorophyll,
            # because the lawn entry did not carry the colour people ask for
            "green", "greener", "greenest", "lush", "thick", "thicker",
            # the words people use for a lawn that has lost its colour, none of which say
            # "green": "the grass looks dull", "my lawn is pale and yellowish"
            "dull", "pale", "pale green", "yellowish", "washed out", "faded", "tired", "thin",
            "not very green",
            # "how do i get my lawn looking good" named no symptom and no job at all, and the
            # entry that owns the lawn punted one word short of its own answer
            "look good", "looking good", "looks good", "look nice", "looking nice",
            "looks nice", "look better", "looking better", "looks better", "nice lawn",
            "best lawn",
            # the bare topic behind a wrapper: "what should i do about my lawn" names no symptom
            # at all, so without these the entry that owns the lawn reached nothing and the bot
            # punted, one line away from answering "my lawn is patchy and yellow"
            "do about", "should i do", "what should i", "what can i", "can i do", "sort out",
            "sort", "improve", "fix", "advice", "help")),
          _lawn,
          # a lawn that has just been laid or sown is the watering job below, not the mowing one
          avoid=("new lawn", "new grass", "new turf", "newly laid", "newly sown", "laid turf",
                 "turf laid", "seedbed", "grass seed", "just laid", "just turfed",
                 # a wrapper word above must not take the neighbours' subjects: moss, weeds and
                 # the pests each have their own answer
                 "moss", "mould", "mold", "weed", "weeds", "dandelion", "dandelions", "clover",
                 "daisy", "daisies", "ant", "ants", "mushroom", "mushrooms", "toadstool",
                 "mole", "moles", "dog", "fox", "foxes", "leatherjacket", "chafer", "worm",
                 "worms", "frost", "snow", "flooded", "waterlogged",
                 # a machine is not a lawn: "how do i fix my grass trimmer" was a punt on main and
                 # the wrapper word "fix" brought it the mowing advice
                 "mower", "mowers", "lawnmower", "lawnmowers", "lawn mower", "trimmer",
                 "trimmers", "strimmer", "strimmers", "scarifier", "robot", "hose",
                 "sprinkler", "blade", "blades", "roller", "edging", "edger")),
    entry("new-lawn-watering",
          (("new lawn", "new grass", "newly laid", "newly sown", "turf", "seedbed", "grass seed",
            # "how do i grow a lawn from seed" names the seed and the lawn but no mowing, and
            # with only "grass seed" in this list it fell through to the biology of germination
            "lawn from seed", "grass from seed", "sow a lawn", "sowing a lawn", "seed a lawn",
            "lawn seed"),
           ("water", "watering", "damp", "hose", "sprinkler", "often", "sow", "sowing", "seed",
            "care", "after", "keep", "walk", "grow", "growing", "start")),
          "Keep a new lawn damp, not soaked: a light sprinkle morning and evening for the first "
          "fortnight, then once a day, and once it is up, water deeply twice a week instead, which "
          "teaches the roots to go down. Do not let it dry out completely in that first month and "
          "do not walk on it; the first cut waits until it is about 5cm tall."),
    entry("tomato-watering",
          (("tomato", "tomatoes", "tomato plant", "tomato plants"),
           ("water", "watering", "watered", "how often", "every day", "daily", "twice a week",
            "once a week", "deeply", "when to water", "hosepipe", "hose",
            # a tomato that has gone limp is asking about water, and "my tomato plants are
            # wilting" was getting how to grow tomatoes - sow indoors in March, and all
            "wilting", "wilted", "wilt", "drooping", "droopy", "limp", "flopping")),
          "Water tomatoes deeply two or three times a week and let the top of the soil dry in "
          "between: a little every day keeps the roots shallow. Even watering is what stops split "
          "fruit and blossom end rot, and in a pot or grow bag in hot weather twice a day can be "
          "right. Water at the base in the morning, not over the leaves.",
          # a tomato that is going yellow or brown is a fault with its own answer, and a tomato
          # feed question is not a watering one
          avoid=("yellow", "yellowing", "brown", "blight", "blossom end rot", "curling", "curl",
                 "split", "splitting", "feed", "feeds", "feeding", "fertiliser", "fertilizer",
                 "tomato feed", "potash", "ketchup", "sauce", "recipe", "recipes", "chutney",
                 "pizza", "pasta", "salad", "soup", "unripe", "ripen", "ripening", "green tomatoes",
                 "green tomato", "plant out", "pinch")),
    entry("lawn-watering",
          (("lawn", "grass", "turf"),
           ("water", "watering", "watered", "hose", "hosepipe", "sprinkler", "how often",
            "twice a week", "once a week", "every day", "daily", "drought", "dry spell",
            "heatwave", "hot weather"),
           # The commonest phrasing names the job in one phrase, and the mowing and sowing entries
           # each hold a short word of it ("how often should i water my lawn" was the mowing
           # answer). A phrase covers both words at once, so the watering entry wins it back.
           ("water my lawn", "water the lawn", "water a lawn", "water lawn", "water my grass",
            "water the grass", "water grass", "watering my lawn", "watering the lawn",
            "watering grass", "water your lawn", "when to water")),
          ("Water a lawn deeply once a week rather than lightly every day: about a centimetre, or "
           "twenty minutes with a sprinkler, in the early morning. Grass roots follow the water "
           "down, so a weekly soak makes a lawn that shrugs off a dry spell, and in a real drought "
           "it is fine to let it go brown and come back."),
          # a new lawn is its own watering job, and mowing, feeding, moss and weeds are not water
          avoid=("new lawn", "new grass", "new turf", "newly laid", "newly sown", "just laid",
                 "just turfed", "seedbed", "grass seed", "moss", "weeds", "mow", "mowing", "cut",
                 "cutting", "feed", "feeding", "patchy", "bare", "bald", "reseed", "scarify",
                 # "how often should i aerate the lawn" kept a bare "how often" and got the
                 # watering, which never mentions aerating: the job's own words take it out.
                 "aerate", "aerating", "aerated", "aeration", "spike", "spiking", "hollow tine",
                 "hollow tines", "thatch", "thatching", "top dress", "top dressing",
                 # turf that was laid a fortnight ago is the new-lawn question, not the schedule
                 "laid turf", "we laid", "just turfed it", "turfed two", "new turf laid",
                 "scarifying", "scarified", "dethatch", "dethatching", "raking out", "spongy",
                 "compacted", "compaction", "reseeding", "oversow")),
    entry("lawn-moss",
          (("moss", "mossy"), ("lawn", "grass", "turf", "mow", "scarify", "spiking", "aerate")),
          ("Moss on a lawn means shade, drainage or compacted soil, not bad luck: rake or scarify it "
           "out, spike the lawn with a fork, and feed the grass so it thickens and takes the space "
           "back. Raise the mowing height and cut back whatever is shading it, and in autumn a "
           "forkful of grit in the worst spots keeps the surface draining.")),
    # "how do i get rid of moles in my garden" was a shrug: the lawn card above stands down for
    # "mole" because a mole is not a lawn fault, and nothing else had it.
    entry("moles",
          (("mole", "moles", "molehill", "molehills", "mole hill", "mole hills"),
           ("garden", "lawn", "grass", "turf", "flowerbed", "flower bed", "beds", "veg patch",
            "get rid", "rid of", "remove", "stop", "how do i", "they keep", "every day")),
          "Moles are after worms, so a lawn full of molehills is a sign of good soil: flatten the "
          "hills, mow the grass back over them and put the soil on a bed, and leave the traps and "
          "the mole catcher to a professional, because spring traps and poison are the only things "
          "that work and both are regulated. Sonic spikes, mothballs, windmills and chewing gum do "
          "nothing. They often move on by themselves once the worms go deeper in a dry spell.",
          # a mole on your skin, a mole in the kitchen and a spy are other answers
          avoid=("skin", "spot", "spots", "arm", "leg", "shoulder", "back", "face", "doctor",
                 "gp", "dermatologist", "melanoma", "check", "bean", "beans", "sauce",
                 "chocolate", "recipe", "cook", "eat", "edible", "salsa", "mole sauce",
                 # the dish is "how do i make mole" and it is the only verb of the kitchen the
                 # fence was missing: "make" is also how the garden line is asked ("how do i make
                 # my lawn mole-free"), so the fence is the dish and not the verb
                 "make mole", "make a mole", "mole poblano", "chicken mole", "turkey mole",
                 "mole negro", "mole verde", "mole amarillo",
                 "suspected", "spy", "police"), bias=1),
    entry("weeds",
          (("weed", "weeds", "weedy", "dandelion", "dandelions", "daisies", "clover", "plantain",
            "ragwort", "bindweed", "nettles", "brambles", "ground elder"),
           ("lawn", "grass", "turf", "patio", "path", "driveway", "gravel", "border", "bed",
            "beds", "garden", "allotment", "kill", "rid", "remove", "dig", "without chemicals",
            "come back", "keep coming", "return", "spread",
            # The place a weed is in is not always given by its job: "the weeds are choking my
            # roses" names neither a bed nor a path, and a person says what the weeds are doing
            # to the plants rather than asking to kill them.
            "flower bed", "flower beds", "flowerbed", "flowerpot", "flowerpots", "flower",
            "flowers", "rose", "roses", "shrub", "shrubs", "choking", "choke", "choked",
            "smothering", "smothered", "strangling", "swamped", "taking over", "taken over",
            "overrun", "getting overrun", "everywhere", "springing up", "popping up")),
          # Keyed on the weed and the place, not on the word "lawn": the same advice covers a
          # border, a path and a gravel drive, and "how do i kill weeds without chemicals" never
          # says where they are. The moss row answers a joint too, so a line naming both is the
          # moss row's; the weed row takes the lines about weeds with nothing green in them.
          ("Get the root, not the leaves: dandelions and plantains come back from a finger of "
           "taproot, and bindweed, ground elder and nettles from any white root left in the soil, so "
           "dig them out with a grubber or fork before they seed. On a lawn, feed and mow it properly "
           "and thick grass crowds them out; on a patio, path or gravel, hoe or flame them young, or "
           "pour boiling water over them. Cardboard and mulch starve a whole bed of them in a season, "
           "and a weedkiller is the last resort, never on a windy day."),
          # A plot that is overgrown and a bed that keeps coming back are different jobs, and the
          # allotment answer is the one that starts where the person is: without this, "it's
          # completely overgrown with weeds" left the allotment conversation for generic weed advice.
          avoid=("overgrown", "allotment", "allotments", "plot", "veg patch", "veggie patch",
                 # "my cat weed on the bed" is an animal in the house, not a plant: the
                 # animal's word means the accident card, which is the one with the detergent
                 "cat", "cats", "kitten", "kittens", "dog", "dogs", "puppy", "puppies",
                 "pet", "pets", "rabbit", "hamster",
                 # "moss and weeds on my patio" is the moss card's: the joint is the job
                 "moss", "mossy", "algae", "lichen"),
          # and a weed the moss row can read too - "weeds keep coming back through the patio" -
          # is answered by the weed, which is what the line is about
          bias=1),
    # A spade in the soil is four different jobs, and nothing in this table knew the word
    # "dig": "how do i dig a hole", "how deep should i dig a hole", "how do i dig out a
    # shrub", "how do i dig over a flower bed" and "how do i dig a pond" all reached the row
    # for replying to a passive-aggressive email, which was keyed on the bare word. Each job
    # is its own row here, keyed on the verb phrase with the thing being dug as the second
    # part, so the word on its own ("they dig at me", "dig in", "dig out my old boots") is
    # nobody's.
    entry("dig-a-hole",
          (("dig a hole", "digging a hole", "dug a hole", "dig the hole", "digging the hole",
            "how deep should i dig", "how wide should i dig", "dig", "digging", "dug"),
           ("hole", "holes", "planting hole", "plant", "plants", "shrub", "tree", "rose",
            "bush", "climber", "hedge", "bare root")),
          ("Dig it square rather than round, about twice as wide as the root ball and the same "
           "depth as the pot it came in: a round hole makes the roots circle, and a hole deeper "
           "than the root leaves the plant sitting in a sump that fills with water. Keep the top "
           "soil to one side, rough up the bottom and sides of the hole with a fork so the roots "
           "can get out, plant it so the old soil mark sits level with the ground, firm it in "
           "with your heel and water it well."),
          # the other digs have a row of their own, and a hole for a fence post, a pond liner
          # or a grave is not a planting hole
          avoid=("pond", "ponds", "trench", "drain", "drainage", "grave", "post", "posts",
                 "fence", "gate", "over the", "dig over", "dig in", "dig out", "dig up",
                 "potato", "potatoes", "trampoline", "weed", "weeds"),
          bias=1),
    entry("dig-over-bed",
          # "dig my allotment over" puts the ground between the verb and its "over", so the verb is
          # a key of its own and the "over" sits with the nouns: a line with a dig and a bed in it
          # is this row's question whether or not the two words touch.
          (("dig over", "digging over", "dug over", "double dig", "double digging",
            "fork over", "dig in", "digging in", "dug in", "fork in", "turn over",
            "turning over", "dig", "digging", "dug", "fork", "forks", "forking", "turning"),
           ("bed", "beds", "border", "borders", "flower bed", "flower beds", "soil", "ground",
            "compost", "manure", "garden", "plot", "allotment", "veg", "vegetable", "patch",
            "over", "turned")),
          _dig_over_bed,
          # "turn over" and "beds" is also how a bad night is said: "i feel dizzy when i turn
          # over in bed" was the digging answer, because a symptom has no garden in it
          # and the rest of a bad night: the symptom in the bed is the body, whatever the
          # symptom is, so a back, a hip or a shoulder in bed stands this row down too
          avoid=("dizzy", "dizziness", "spins", "spinning", "spinning round", "vertigo",
                 "giddy", "light headed", "lightheaded", "nauseous", "nausea", "room spins",
                 "my back", "back hurts", "back ache", "backache", "aches", "aching",
                 "hip", "hips", "spine", "shoulder", "shoulders", "neck", "sore", "stiff",
                 "hurts", "hurting", "in bed", "at night", "wake", "wakes", "woke", "sleep",
                 # a hole is dug for a plant, a post, a pond or a grave, and each of those has its
                 # own row: the bare verb above teaches this row every dig, and these name the
                 # lines that are somebody else's
                 "hole", "holes", "pond", "ponds", "trench", "trenches", "grave", "post", "posts",
                 "fence", "path", "patio", "foundation", "footings", "sandpit", "drain",
                 "drainage", "plotting")),
    entry("dig-out-shrub",
          (("dig out", "digging out", "dug out", "dig up", "digging up", "dug up",
            "how do i get rid of", "how do i remove"),
           ("shrub", "shrubs", "bush", "bushes", "tree", "stump", "conifer", "laurel",
            "hedge", "roots", "rootball", "root ball")),
          ("Cut the shrub down to about 30cm of stem first so you can see what you are doing, "
           "then dig a trench a spade's width outside the stems and cut straight down through "
           "the roots all the way round until the rootball rocks. Lever it out with the spade "
           "rather than pulling at it, and take the big roots with it - a laurel or a willow "
           "left with roots in the ground sends up suckers for years."),
          # "remove" and "get rid of" are wide: the rubbish, the stain and the smell rows all
          # own a line that says them without a shrub in it, and the stump grinders are a
          # different job from a shrub you can lever out
          avoid=("stain", "smell", "rubbish", "tip", "council", "bins", "mould", "mildew",
                 "grind", "grinder", "stump grinder", "chemical", "weedkiller", "dead",
                 "from my", "off my"),
          bias=1),
    entry("dig-a-pond",
          (("dig", "digging", "dug", "build", "building", "make", "put in", "how deep",
            "how big", "how large", "how wide", "size", "depth"),
           ("pond", "ponds", "water feature", "wildlife pond", "water garden")),
          ("Dig it 60cm deep in the middle with a shelf 20 to 30cm deep and 30cm wide around "
           "the edge for marginal plants, and go at least a metre across - a pond shallower than "
           "that freezes solid and has nowhere for anything to live. The rim is the part people "
           "get wrong: keep it level all the way round, checked with a straight edge and a "
           "spirit level before the liner goes in, or the water shows one edge of it. Line it "
           "with butyl rather than cheap polythene, leave the liner to settle for a day, then "
           "fill it and let it stand a week before anything goes in."),
          bias=1),
    entry("prune-roses",
          (("roses", "rose", "rose bushes", "rose bush", "climbing rose"),
           GONE_WILD + ("prune", "pruning", "cut back", "cutting back", "deadhead",
                        "deadheading", "when", "winter", "spring", "shape", "leggy")),
          ("Prune roses in late winter, around February when the buds start to swell: cut out dead, "
           "thin and crossing stems first, then take the rest back by about a third, making each cut "
           "just above an outward-facing bud so the new shoot grows away from the middle. Deadhead "
           "through the summer down to the first strong leaf. Climbing roses are the exception - "
           "prune those after flowering, not in winter."),
          # a rose in a vase is the cut-flowers question, not the bush
          avoid=("vase", "vases", "bouquet", "bunch", "last longer", "cut flowers")),
    entry("foxes",
          (("fox", "foxes"), ("garden", "stop", "keep out", "keep them out", "deter", "coming",
                             "digging", "fence", "smell", "poo", "scared", "chickens",
                             # the bin is where most people meet a fox, and "bins" was not an
                             # ask word, so "how do i keep foxes out of the bins" and "foxes keep
                             # knocking over my bin" reached nothing at all
                             "bin", "bins", "wheelie", "wheelie bin", "rubbish", "waste",
                             "food waste", "bin bag", "bin bags", "bags", "knocking over")),
          ("Take away the food and the easy way in: bins with clipped lids, no pet food or bird food "
           "left out overnight, and no fallen fruit under the tree. A 2m fence is not enough on its "
           "own, because a fox can clear it or dig under it, so fit a roller bar on top or a strip of "
           "paving on the ground line. Chilli powder and commercial repellents fade in the rain and "
           "have to be renewed; a dog is the only deterrent that works every night."),
          # a fox in the garden is not a fox fact: nature.py answers what foxes are and what they eat
          bias=1,
          # a dog that rolls in what a fox leaves behind is the dog's behaviour, not the garden's:
          # "why does my dog roll in fox poo" was this card, which is about keeping foxes out
          avoid=("my dog", "the dog", "dogs", "puppy", "rolls in", "roll in", "rolling in",
                 "rolled in", "rolls on", "rolls over it", "rubs himself in", "rubs herself in",
                 "dead bird", "dead things", "licks", "licking", "ate", "eaten")),
    # A garden that is looked into is its own job, and there was no row for it: "how do i make my
    # garden more private" and "how do i stop the neighbours looking in my garden" both got a
    # shrug. The answer is mostly what to plant and how tall a fence may be, so it is a garden row
    # rather than a planning one.
    entry("garden-privacy",
          (("private", "privacy", "overlooked", "overlooking", "looked into", "looking in",
            "looks in", "nosey neighbour", "nosy neighbour", "neighbours can see", "screened",
            "screen", "screening", "block the view", "block out the view", "hide", "hiding",
            "cover up", "not see"),
           ("garden", "fence", "hedge", "tree", "trees", "plant", "grow", "window", "windows",
            "neighbours", "neighbor", "neighbors", "boundary", "patio", "decking", "balcony",
            # screening a thing in the garden is the same question: "how do i screen a wheelie
            # bin" had no answer on main
            "bin", "bins", "wheelie bin", "wheelie bins", "store", "shed", "oil tank", "heat pump")),
          ("Evergreen blocks a view all year, and yew, holly or laurel reach 2m in a few years: buy "
           "them bare-root in autumn, plant 60cm apart, and put a strip of membrane down so you are "
           "not weeding under them. Quicker than a hedge is a fence or a trellis to 2m at the back "
           "of a garden (1m is the usual limit at the front, and a listed building or a conservation "
           "area wants permission) with a climber over it - ivy, honeysuckle, a climbing rose. "
           "Pleached trees on stilts screen an upstairs window in one season, and a sail shade on "
           "posts does a patio straight away. Check whose fence it is before you build on it, and "
           "ask before taking a hedge down: a boundary hedge is often shared."),
          # a fence that has fallen down, a hedge to cut and a hotel room that is overlooked are
          # other rows, so the words that make those lines are not this one's
          avoid=("fell down", "fallen down", "blown down", "broken", "repair", "replace",
                 "prune", "pruning", "cut back", "cutting", "trim", "trimming", "hotel", "room",
                 "booking", "refund", "cost", "price", "how much", "who owns", "my neighbour says")),
    # The sun in your eyes at four in the afternoon is a garden job with a short list of answers,
    # and on main it was a tiling card: "how do i stop the sun in my eyes on the patio" is a sail
    # shade or a cantilever parasol, not grout.
    entry("patio-sun",
          (("sun", "sunlight", "sunny", "glare", "too hot", "blazing", "shade"),
           ("patio", "decking", "deck", "garden", "terrace", "balcony", "table", "chairs",
            "outside", "sitting out", "barbecue", "bbq")),
          ("Shade the table, not the whole garden: a cantilever parasol is the one that works, "
           "because its base sits off to the side and the canopy reaches over the table without a "
           "pole in the middle. Second is a sail shade on three posts, set so it faces the afternoon "
           "sun and angled 20 to 30 degrees, with the fixings tight enough that it does not flap; "
           "take it down when it blows hard, because a sail in a gale pulls the posts out. If you "
           "have the room, a tree on the west side is the best of all in five years' time - a "
           "rowan, an amelanchier or a small crab apple, 3m from the fence."),
          # a paving and grouting row also scores on "patio", and this is the sun question, so it
          # takes the tie
          bias=2),
    entry("lay-turf",
          (("turf", "turfing"), ("lay", "laying", "new lawn", "when", "how")),
          ("Lay turf in spring or early autumn, when the soil is warm and wet: clear and dig the "
           "ground, level it, tread it and rake it, then put a straight edge down and lay the rolls "
           "brick-fashion, butting them tight. Water the whole lawn as you go and keep it damp for a "
           "fortnight: the turf has no roots in the soil until it knits. Or order it early in the "
           "week and lay it the day it arrives - a roll left in the shade goes yellow in a day or two.")),
    entry("garden-start",
          # "start" on its own is how people say when a symptom began ("it started this morning
          # when I was in the garden"), so the second part is the ask, not the word: the mess
          # words cover the rest ("my garden is a mess") and the phrases cover "where do I start".
          (("garden", "back garden", "plot"),
           GONE_WILD + ("mess", "messy", "overgrown", "neglected", "jungle",
                        "where do i start", "where to start", "how do i start", "get started",
                        "starting point", "start on", "tidy up", "tidy", "sort out", "clear",
            # "start" is also how people open a garden question, so the phrasings are here and
            # the bare word is not: "starting a garden from scratch" is a plan, while "it
            # started this morning when I was in the garden" is when a symptom began.
            "start a garden", "start gardening", "starting a garden", "start my garden",
            "starting gardening", "start the garden", "begin a garden")),
          ("Take one bed, not the garden: strim or mow the lot so you can see it, then clear a "
           "single rectangle the size of a rug, dig it over and plant something in it, and cover the "
           "rest with cardboard weighted down with compost or old bricks to kill the weeds while you "
           "work through it. Half an hour a day on one bed beats a lost weekend on all of them."),
          # an allotment is the same job with its own answer
          avoid=("allotment",)),
    # "How do I get into gardening" and "what should I grow in my first year" are two of the
    # most common garden questions there are, and neither reached anything: "garden" alone is a
    # place word and the beginner's words were in no key. One answer covers both, because a
    # person starting out is asking both at once.
    entry("gardening-start",
          (("vegetable patch", "veg patch", "vegetable garden", "kitchen garden", "veg plot",
            "raised bed", "raised beds", "allotment", "garden", "gardening", "grow",
            "growing", "plant", "plants", "vegetables", "veg", "crops", "seed",
            "seeds"),
           ("get into", "getting into", "into gardening", "beginner", "beginners", "new to",
            "first year", "first time", "first garden", "never gardened", "where do i start",
            "where to start", "start with", "start off", "starting out", "begin", "start",
            "starting", "began", "set up", "setting up",
            "easy", "easiest", "small garden", "small space", "what should i grow",
            "what can i grow", "what to grow", "should i grow", "can i grow",
            "what should i plant", "what can i plant", "what to plant", "what grows")),
          # short sentences on purpose: the reply is shaped to fit, and a long comma-spliced
          # one was being cut mid-sentence ("And sow a small row of each from April").
          ("Start with what you eat and what costs most in the shop. Salad leaves, radishes, "
           "courgettes, runner beans, potatoes and tomatoes are the forgiving six, plus a herb pot "
           "by the door. Take one bed about a metre by two, not the whole garden. Dig a bag of "
           "compost into it. Sow a small row of each from April, and again in June. Salad leaves "
           "are ready to cut in four weeks, which is what keeps a first year going."),
          # a named plant, a plant indoors and an overgrown garden each have an answer of their
          # own, and "grow" alone is also a beard, a business and a crystal
          avoid=("monstera", "orchid", "orchids", "fern", "ferns", "cactus", "cacti",
                 "succulent", "succulents", "peace lily", "aloe", "basil", "fiddle leaf",
                 "calathea", "jade plant", "rubber plant", "spider plant", "snake plant",
                 "pothos", "zz plant", "houseplant", "houseplants", "house plant",
                 "house plants", "indoor", "windowsill", "overgrown", "mess", "messy",
                 "neglected", "jungle", "beard", "hair", "nails", "taller", "height",
                 "business", "following", "followers", "muscle", "muscles", "weed",
                 "cannabis", "crystal", "crystals", "bacteria", "sourdough", "mould",
                 "mold", "moisture", "lawn", "grass", "hedge", "tree", "trees",
                 # shade, sun and flowers are their own answers: this one is about crops
                 "shade", "shady", "shaded", "north facing", "north-facing", "sun", "sunny",
                 "full sun", "flower", "flowers", "colour", "color", "colours", "colors",
                 "bulbs", "hanging basket", "basket", "climber", "climbers", "shrub", "shrubs",
                 "perennial", "perennials", "annual", "annuals", "bedding",
                 # "what plant is easy to keep alive" is the houseplant list
                 "keep alive", "easy to keep", "hard to kill", "look after", "looking after",
                 # a bed is dug, so pots, a patio and a balcony are the container answer
                 "patio", "pots", "containers", "window box", "window boxes", "balcony",
                 "hanging basket", "grow bag", "grow bags", "in pots", "in a pot",
                 "in containers", "windowsill", "window sill",
                 # a watering question is not a what-to-grow question
                 "water", "watering", "watered", "how often", "how much water",
                 # a month in the line is the planting-month answer, and that row has the
                 # month's own list: "what can i plant in november" is garlic and broad beans,
                 # not a first bed
                 "january", "february", "march", "april", "may", "june", "july", "august",
                 "september", "october", "november", "december", "this month", "next month",
                 "this week", "next week",
                 # a named crop, herb or bulb has its own sowing, planting and harvest row:
                 # "what should i plant with tomatoes" is the tomato companion answer, and
                 # "easy herbs to grow" is the herb list
                 "tomato", "tomatoes", "potato", "potatoes", "carrot", "carrots", "onion",
                 "onions", "garlic", "lettuce", "lettuces", "bean", "beans", "pea", "peas",
                 "cabbage", "broccoli", "kale", "spinach", "beetroot", "radish", "radishes",
                 "courgette", "courgettes", "cucumber", "chilli", "chillies", "pumpkin",
                 "squash", "sweetcorn", "leek", "leeks", "parsnip", "parsnips", "rhubarb",
                 "strawberry", "strawberries", "runner bean", "runner beans", "broad bean",
                 "broad beans", "herb", "herbs", "mint", "chives", "rosemary", "thyme",
                 "parsley", "coriander", "dill", "sage", "oregano",
                 "bulb", "bulbs", "tulip", "tulips", "daffodil", "daffodils", "allium",
                 "alliums", "crocus", "snowdrop", "snowdrops")),
    # "How big should the patch be", five turns into a chat about growing veg, was answered
    # with a stop-smoking plan: the only key with "patch" in it was a nicotine patch. A bare
    # "patch" is not a garden word either, so the row asks how big and names the plot, and the
    # words that make a patch something else - a mattress, a bald patch, a damp patch, a tyre -
    # stand it down. The other two words a person uses for it, "plot" and "bed", are here too.
    # "what size allotment do i need" is the same ask as "how big should the patch be", and the
    # clothes-size chart keys "size" against the ask "what size" too, so the plot phrases say the
    # garden they are about and the row takes the tie (bias). A clothes line names no plot word,
    # so nothing of theirs is lost: "what size am i in europe" is still the chart.
    entry("size-of-a-plot",
          (("how big", "how large", "how wide", "how much space", "what size", "size of",
            "how many plants", "how long should the bed be", "how many beds",
            "what size allotment", "how big an allotment", "how big a plot", "what size plot",
            "how big a patch", "size of an allotment", "size of a plot", "size of a patch",
            "how much room do i need", "how much space do i need"),
           ("patch", "plot", "vegetable patch", "veg patch", "veg plot", "veg",
            "allotment", "raised bed", "raised beds", "flower bed", "flower beds",
            # a bare "bed" is a mattress as often as it is soil - "how big should my bed be"
            # was this row's first line on the bench - so the plot words name it instead
            "garden", "grow", "growing")),
          ("A patch about three metres by two is the size most first plots are, and it feeds two "
           "people through a summer. Keep the bed no wider than 1.2m, so you can reach the middle "
           "from either side without standing on it, and work back from the plants rather than "
           "from the area: a tomato wants 45cm each way, a courgette a square metre to itself, and "
           "salad leaves 20cm apart. Two of each is plenty in the first year. A raised bed wants "
           "twenty centimetres of soil for salad, herbs and dwarf beans, and thirty for carrots, "
           "onions and tomatoes."),
          # the size of a plot is asked with the plants and the words above, and the clothes-size
          # chart asks "what size" too: on a tie the plot is what the person wants
          bias=1,
          # a bed in a bedroom, a patch of skin, a damp patch, a bald patch, an eye patch and a
          # tyre patch are six other subjects: the size of a plot is only asked with a garden in
          # the line, so the words that make the patch something else stand this row down
          avoid=(
                 # a patch on a child is a plaster or a sewn-on badge, not soil: clean-bench found
                 # "what size should a patch be for a child" arriving here from a punt
                 "for a child", "for children", "for a kid", "for kids", "on a child", "child's",
                 "childs",
                 "mattress", "mattresses", "divan", "headboard", "duvet", "pillow", "pillows",
                 "sheet", "sheets", "bedroom", "king size", "super king", "double bed",
                 "single bed", "bunk", "cot", "sleep", "in bed", "to bed", "off to bed",
                 "my back", "back hurts", "back ache", "backache", "hip", "hips", "shoulder",
                 "shoulders", "sore", "stiff", "hurts", "hair", "scalp", "bald", "skin", "spot",
                 "spots", "rash", "damp", "mould", "mold", "ceiling", "wall", "walls", "eye",
                 "eyes", "tyre", "tyres", "tire", "tires", "plaster", "plasterboard", "hole",
                 "holes", "jeans", "trousers", "dress", "shirt", "nicotine", "smoke", "smoking",
                 "smoker", "quit", "vape", "gum", "pond", "ponds", "patio", "pots", "pot",
                 "container", "containers", "lawn", "dogs", "dog", "cat", "cats", "pet", "pets",
                 "hamster", "rabbit", "chicken", "chickens",
                 # a shoe, a hat and a bed sheet are also sizes somebody asks about
                 "shoe", "shoes", "bra", "dress size", "hat", "ring size", "clothes",
                 "jeans size", "trousers size", "waistcoat")),
    # "What should I plant for easy colour" is a flower question, and the only answers were the
    # vegetable ones, because "easy" and "colour" were in no key. One line per season, since a
    # garden that looks after itself is a different list in June and in February.
    entry("easy-flowers",
          (("easy flowers", "easy colour", "easy color", "flowers for", "low maintenance",
            "low-maintenance", "flower bed", "flower beds", "border", "borders",
            # bare "bedding" is a bed, and the loose forms of "bed" reach it: "i am off to bed
            # soon, what should i cook" got the easy-flowers card. Bedding plants still count.
            "bedding plants", "bedding plant",
            "flowers", "flower", "colour", "colors"),
           ("garden", "plant", "planting", "easy", "easiest", "what should i", "what can i",
            "which", "start with", "summer", "winter", "spring", "autumn", "shade", "sun",
            "pots", "cheap", "look after themselves", "come back", "perennial", "low")),
          "Cosmos, lavender, hardy geranium, sedum, verbena and pot marigold flower for months "
           "with nothing but deadheading, and daffodil and allium bulbs do the spring. Buy "
           "perennials rather than bedding: they come back every year, so the border fills itself "
           "instead of being replanted each May. Put the tallest at the back, water them in their "
           "first fortnight and leave them alone after that.",
          # a bunch for a person, a plant kept alive indoors and a single named flower are other
          # questions: "should i get her flowers or a plant" wants a florist, not a border
          avoid=("get her", "get him", "for my wife", "for my mum", "for my mom", "for my",
                 "girlfriend", "boyfriend", "husband", "wife", "anniversary", "birthday",
                 "wedding", "funeral", "sorry", "thank you", "valentine", "valentines",
                 "mothers day", "mother's day", "bouquet", "florist", "bunch", "gift",
                 "present", "rose", "roses", "tulip", "tulips", "daffodil", "sunflower",
                 "orchid", "houseplant", "houseplants", "indoor", "keep alive", "easy to keep",
                 "hard to kill", "cut flowers", "vase",
                 # the list below is a summer one: winter colour in a border has no answer yet,
                 # and a summer list is a confident wrong one
                 "winter", "christmas", "december", "january", "february",
                 # a bed for growing in is a crop question: "what can i plant in a raised bed"
                 # got cosmos and lavender, which is one guess too many
                 "raised bed", "raised beds", "veg", "vegetable", "vegetables", "crops",
                 "crop", "edible", "edibles", "salad", "allotment", "kitchen garden",
                 # "colour" here means colour in the garden, so a colour to paint a room in
                 # is another question and home's colour-choice row owns it: "which colour
                 # should i paint the bedroom" got cosmos and lavender. The paint words are
                 # what the room questions carry, so they stay here.
                 "paint", "painting", "painted", "repaint", "repainting", "emulsion",
                 "paint colour", "paint colors", "wall colour", "decorating", "decorate"),
          # a room's own walls are not a border either - after a colour answer the follow-up
          # "and what about the hallway" reached the border list - but a wall in a garden is,
          # so the room words are the guard's job, not this list's: see _has_something_to_grow_in
          guard=_has_something_to_grow_in),
    # One group of alternatives, not three parts: a bare string after the first at the top of a
    # key is a part of its own, and only the first of them can ever match, so "snails" was a dead
    # key and every snail line was a hedge ("how do i get rid of snails" answered nothing while
    # "how do i get rid of slugs" got the night patrol).
    # A bare "what should i do about slugs" named the slug and no verb, and the row wants two
    # groups, so it scored 2 and lost - to the measures row, which kept a bare "slug" as a
    # synonym for a knob of butter and told the gardener a knob is about a tablespoon. The asks
    # are here so the shortest slug question is answered by the slug answer.
    entry("slug-control", (("slugs", "snails"),
                             ("keep", "stop", "rid", "control", "eating", "lettuce", "lettuces",
                              "seedling", "what should i do", "what can i do", "what do i do",
                              "do about", "how do i", "deal with", "get rid", "problem",
                              "problems", "everywhere", "kill", "deter",
                              # the garden it is happening in is the ask, not the weed it
                              # arrived with: "slugs in my garden" was a nod on main
                              "garden", "plant", "plants", "getting", "holes", "deterrent")),
          ("Go out after dark with a torch and pick them off, which beats most products; copper tape "
           "round pots and a gritty barrier round seedlings help too. Encourage birds and frogs, and "
           "water in the morning rather than the evening.")),
    # Sap-sucking insects are one family with one answer, because the gardener cannot tell them
    # apart and does not need to: blackfly and greenfly on beans and roses, aphids on anything
    # soft, whitefly in a greenhouse. "how do i get rid of blackfly on my beans" was a shrug on
    # main and "greenfly on my roses" was "I'm listening - say more if it helps."
    entry("pests-aphids", (("blackfly", "black fly", "greenfly", "green fly", "aphid", "aphids",
                            "whitefly", "white fly", "whiteflies", "blackflies", "greenflies",
                            "lice", "plant lice", "scale insect", "scale insects"),
                           ("rid", "get rid", "stop", "kill", "control", "spray", "soap", "wash",
                            "covered", "covered in", "infestation", "eating", "sucking", "roses",
                            "beans", "broad beans", "greenhouse", "plants", "plant", "help",
                            "problem", "deal")),
          ("Rub them off with your fingers or a strong jet of water, then spray with soapy water - "
           "a teaspoon of washing-up liquid in a litre, sprayed under the leaves in the evening - "
           "and repeat every three days for a fortnight, because the eggs keep hatching. Check "
           "for ants running up the stem: they farm the aphids and keep them there, so a sticky "
           "band round the pot stops the supply line. Ladybirds and hoverflies do the rest if you "
           "leave the flowers they feed on. On broad beans, pinch out the top 10cm once the "
           "flowers set, which is where blackfly gather.")),
    # Caterpillars are a different first step from aphids: nothing sprayed on a leaf stops a
    # cabbage white laying on it, so the answer is a net and a daily check.
    entry("pests-caterpillars", (("caterpillar", "caterpillars", "cabbage white", "cabbage whites",
                                  "brassica", "cabbage", "cabbages", "holes in the leaves",
                                  "holey leaves", "nibbled", "eaten leaves"),
                                 ("rid", "get rid", "stop", "kill", "control", "eating", "eaten",
                                  "holes", "chewed", "net", "cover", "spray", "picking", "plants",
                                  "help", "deal", "problem")),
          ("Net the crop and the butterflies cannot land: a fine mesh hooped over the rows from "
           "the day you plant, weighed down at the edges, is the whole answer for cabbages and "
           "brassicas. Without a net, look under the leaves for the yellow eggs in clusters and "
           "squash them, and pick off caterpillars in the cool of the morning, when they sit on "
           "the leaf instead of dropping. A plant that has lost every leaf to the lace pattern "
           "will usually grow back if you net it now.")),
    # "why is my tap water cloudy" reached a plumber line about a boiler: the water itself is
    # the question here, and the answer is the same whether the line says cloudy, milky or white.
    entry("tap-water-cloudy", (("tap water", "cold tap", "hot water", "water", "tap",
                                "from the tap", "out of the tap"),
                               # "brown", "grey" and "gritty" are not here: brown water is a
                               # different fault with a different first step, and a reply that
                               # opens "Milky tap water is almost always air" would be wrong.
                               ("cloudy", "milky", "white", "bubbles", "bubbly", "clouded")),
          ("Milky tap water is almost always air: fill a glass, and if it clears from the bottom up "
           "in a minute or two it is just bubbles from pressure in the main and it is safe to "
           "drink. If it stays cloudy, or runs brown, blue or green, run the cold tap for two "
           "minutes and then ring your water company - and drink bottled water until it clears."),
          # a mark or a crust on the fitting is scale left by hard water, not air in it: the
          # glass test answers the wrong question, so those words pass to the limescale entry.
          # ("taps" cannot go here on its own: it loosens to "tap", and then "my tap water is
          # white" goes with it. The phrases below name the fitting without touching the water.)
          avoid=("marks", "stains", "scale", "limescale", "furred", "chalky", "crusty", "crust",
                 "on the tap", "on my taps", "on the taps", "taps are", "tap is furred",
                 "around the tap", "shower head",
                 "kettle", "boiler", "bill", "bills", "meter", "pressure", "heating", "radiator",
                 "rain", "sea", "pool", "swimming", "plant", "plants", "garden", "leaking",
                 # a pond, a fish tank and a water butt have their own water: "my pond water is
                 # green and cloudy" is algae, not air in the main
                 "pond", "ponds", "fish tank", "tank", "aquarium", "water butt", "green",
                 # "whites" cannot go here: white and whites are one word to the matcher, and
                 # every milky-water line says white.
                 "laundry", "washing machine", "shirt", "clothes", "toilet",
                 # "white stuff" is a crust sitting on the tap, which is scale, not air in the
                 # water: the milky-water reply would be wrong for it, and the scale answer owns
                 # it. A line about water still says water, cloudy, milky or tap on its own.
                 "white stuff", "crust", "crusty", "on my taps", "on the taps", "on the tap",
                 "around the tap", "around the taps", "marks", "stains", "limescale", "scale"),
          # "cloudy" is the pond row's key as well now, so the point this row used to carry for
          # being the only one in its domain to say it is gone, and it ties with the sink-cleaning
          # row, which also keys "tap" and "why": without this, "why is my tap water cloudy"
          # answers with a wipe round the bowl.
          bias=1),
    # "is tap water safe to drink", "should i filter my tap water" and "my water tastes of
    # chlorine" had no answer about the water in the reader's own house: the cloudy-water entry
    # above wants a cloudy word, so these lines were left to the plumber line about a boiler.
    entry("tap-water-safe",
          (("tap water", "the tap", "water from the tap", "drinking water", "filtered water",
            # the line often says only "my water", so the taste and the smell carry the subject
            "water tastes", "water smells", "water taste", "water smell"),
           ("safe", "safety", "drink", "drinking", "ok", "alright", "filter", "taste", "tastes",
            "chlorine", "smell", "smells", "hard")),
          ("Tap water in the UK is safe to drink - it is tested all the way to your kitchen - "
           "and the taste it sometimes has is chlorine, which is there to keep it safe: fill a "
           "jug, keep it in the fridge for an hour and the taste goes. A filter is for taste "
           "rather than safety, and it needs changing when the pack says. Old houses can still have lead "
           "pipes: run the cold tap for a minute first thing before drinking or making formula, "
           "and never use the hot tap for either. If the water is discoloured or smells of "
           "anything but chlorine, ring your water company - they test it for free - and drink "
           "bottled until they have."),
           # a country is the travel answer's line, and an alarm is the plumbing one's; a person
           # who keeps forgetting to drink is asking how to remember, not what is in the water.
           # A stain on the tap or the shower is the limescale answer's line: "hard water stains
           # on the taps" is a cleaning question, and this card's "hard" and "water" took it.
           # A pet's bowl is pets.py's, and water with a meal is the myth science.py answers:
           # "my dog wont drink water" and "is it bad to drink water with meals" both tied with
           # this entry and got the UK tap-water fact.
           avoid=("hard water stain", "hard water stains", "limescale", "scale", "scaled",
                  "white marks", "chalky", "stain", "stains",
                  # "how do i clean hard water marks off the taps" said "tap" and "hard" and
                  # landed on the drinking-water card: the marks are scale, and the mark words
                  # in either order are the cleaning question
                  "mark", "marks", "marks off", "hard water mark", "hard water marks",
                  # a tooth that hurts in water is the dental answer's line, not the supply's:
                  # "my tooth hurts when i drink water" was answered with the UK tap-water card
                  "tooth", "teeth", "gums", "gum", "enamel", "dentist", "dentists",
                  "twinge", "toothache", "hurts to drink", "hurts when i drink",
                  "forget", "forgets", "forgetting", "keep forgetting", "struggle", "struggles",
                  "struggling", "remind", "reminds", "remember", "habit", "make myself",
                  "dont drink enough", "don't drink enough", "dont like water",
                  "don't like water", "cant drink", "can't drink", "hate water",
                  "never drink", "barely drink", "hardly drink", "rarely drink",
                  "seldom drink", "drink much", "drink any", "water at all", "much water",
                  "any water", "very little water", "hardly any water",
                  "cloudy", "milky", "brown", "leaking", "boiler", "radiator", "bill", "meter",
                  # a pet's water is the pet answer's line, not the water supply's: "my dog
                  # won't drink water" was reaching this answer on "drink" and "water", and a
                  # glass with a meal is the myth science.py answers
                  "dog", "dogs", "cat", "cats", "puppy", "puppies", "kitten", "kittens", "pup",
                  "pet", "pets", "vet", "hamster", "rabbit", "horse",
                  # a person being sick is asking how to get fluid into themselves, not what is
                  # in the supply: "can i drink water when i am vomiting" was the UK tap-water
                  # card, chlorine and all. The stomach is the subject, so the supply stands down.
                  "vomit", "vomiting", "vomited", "being sick", "throwing up", "thrown up",
                  "throw up", "diarrhoea", "diarrhea", "stomach bug", "norovirus", "gastro",
                  "keep down", "keep water down", "keep anything down", "cant keep",
                  "cannot keep", "can't keep", "nausea", "nauseous",
                  "with meals", "with food", "with my meal", "with a meal", "during meals",
                  "before a meal", "before meals", "after a meal", "after meals", "while eating",
                  "abroad", "holiday", "holidays", "travelling", "travel",
                  "mexico", "turkey", "egypt", "spain", "greece", "india", "thailand",
                  "morocco", "tunisia", "cyprus", "portugal", "italy", "france", "usa",
                  "america", "bali", "vietnam", "peru", "kenya", "iceland")),
    # "what is compost" was a shrug: the entry keyed the making of it ("heap", "make",
    # "kitchen") and not the plain request to explain the word. It answers both now, and the
    # reply picks its own first sentence from the line: a what-is line gets the definition,
    # because "how do i start a compost bin" already knows what the stuff is and does not need
    # telling. `what is` alone is not a key word - "what is the best compost for houseplants" is
    # about soil and belongs to the potting row.
    entry("compost", (("compost", "composting", "compost heap", "compost bin"),
                     ("what is compost", "what is a compost heap", "what is composting",
                      "what is compost made of", "compost mean", "compost stand for",
                      "heap", "bin", "make", "start", "home", "kitchen", "garden",
                      "how", "caddy", "cooked food", "cooked", "meat", "bones",
                      "what can i put",
                      # a heap that has stopped working is the same row's question, and
                      # "compost" plus one of these is all a why-line about it says
                      "not rotting", "rotting", "rot", "rotten", "breaking down",
                      "break down", "broken down", "not breaking", "not working",
                      "heating", "heating up", "heat up", "not heating", "cold",
                      "slow", "slowly", "stalled", "stopped", "slime", "slimy",
                      "smell", "smells", "smelly", "smelling", "stinks", "sour",
                      "flies", "dry", "soggy", "wet", "nothing",
                      # the heap in the cold is the same row's question too
                      "freeze", "freezing", "frozen", "frost", "winter")),
          compost_reply,
          # "can i compost cooked food" and "can i compost bones" ask the row's second sentence,
          # which the heap's method keeps behind it: the answer is the "no" and the reason, and
          # the mixing comes after it. Declared whole, to its full stop, so no clause is cut.
          lead=("yesno", _the_no_cooked_food),
          # a word for bought soil, and the pot it goes in, is a different job
          avoid=("houseplant", "houseplants", "house plant", "house plants", "potting",
                 "seed", "seedling", "seedlings", "orchid", "orchids", "cactus", "cacti",
                 "peat", "peat free", "peat-free", "multi purpose", "multi-purpose",
                 "best compost", "which compost", "what compost", "for my pots", "in a pot",
                 "raised bed", "border", "hanging basket", "grow bag", "growbag",
                 "mushroom", "comfrey")),
    entry("ants-in-the-kitchen", (("ants", "ant"), ("kitchen", "trail", "baited", "bait", "rid",
                                                      "cupboard", "sugar",
                                                      # "how do i stop ants" and "how do i get rid
                                                      # of ants" name no room at all, and the
                                                      # answer is the same one
                                                      "stop", "get rid", "getting rid", "rid of",
                                                      "keep them", "keeping", "keep out", "house",
                                                      "home", "flat", "indoors", "everywhere",
                                                      "floor", "worktop", "counter", "sink",
                                                      "prevent", "off")),
          "Wipe the trail away with vinegar and water and put bait down close to it: they carry the "
          "bait back to the nest and that is what kills the colony, so do not spray the line they "
          "are following. Give the bait a week or two: the ants keep coming for the first few days "
          "and then the stream thins out and stops. Keep sugar and crumbs sealed for a fortnight "
          "and they stop coming. One "
          "ant is a scout; a stream means a nest under the floor or behind a skirting board.", report=True),
    entry("hydrangea-brown", ("hydrangea", ("hydrangeas", "brown", "browning", "dying", "wilting",
                                            "wilted", "wilt", "drooping", "droopy", "limp",
                                            "flowers", "water")),
          "Brown flowers on a hydrangea are almost always thirst, or simply old blooms: it has "
          "shallow roots and wants damp soil and shade from the hottest afternoon sun. Water it "
          "deeply twice a week in dry spells, mulch around the base, and cut the spent heads off so "
          "the plant puts its energy into next year's buds rather than seed.",
          # "my hydrangea wont flower" is the opposite question - nothing came, rather than
          # something came and went brown - and "flowers" in the key above was taking it from
          # the row that knows why a plant does not flower.
          avoid=("wont flower", "won't flower", "not flowering", "isnt flowering",
                 "isn't flowering", "no flowers", "no flower", "no blooms", "hasnt flowered",
                 "hasn't flowered", "never flowered", "didnt flower", "didn't flower",
                 "how do i get flowers", "not flowered", "no hydrangea flowers")),
    # Blight and powdery mildew are the two plant illnesses people ask about by name and neither
    # had a row: "my tomatoes have blight" went to a tuna salad and "how do i stop blight" to
    # nothing. Both are keyed on the illness and a plant, so the answer leads with the crop that has
    # it, and the harvest and cooking rows keep the healthy-crop lines they already answer.
    entry("tomato-blight", (("blight", "tomato blight", "potato blight", "blighted",
                             "black spot", "black spots", "leaf spot", "spots on the leaves"),
                            ("tomato", "tomatoes", "potato", "potatoes", "crop", "crops",
                             "plant", "plants", "leaves", "leaf", "greenhouse", "plot",
                             "rose", "roses", "bush", "shrub", "tree", "apple", "apples")),
          # a rose with black spot on it ties with the bathroom-mould table, which also keys
          # "black spots": the plant row is the one that has the plant as well
          _blight, bias=2,
          avoid=("ready", "when are", "harvest", "lift", "pick them", "recipe", "cook", "eat",
                 "chutney", "sauce", "salad", "soup")),
    entry("plant-mildew",
          (("mildew", "powdery mildew", "white mould", "white mold", "grey mould", "gray mould",
            "white powder", "white dust", "white coating",
            "white patches", "white film", "grey powder", "gray powder"),
           ("plant", "plants", "leaves", "leaf", "courgette", "courgettes", "cucumber",
            "cucumbers", "squash", "pumpkin", "rose", "roses", "tomato", "tomatoes", "dahlia",
            "dahlias", "pea", "peas", "melon", "melons", "vine", "vines", "greenhouse",
            # "my apple tree has white powder" is the same question as the cucumber, and the tree
            # word is what says it is a plant: without it the answer was blackthorn blossom
            "apple", "apples", "tree", "trees", "shrub", "shrubs", "bush", "fruit")),
          # "my squash leaves have white patches" is a mildew question, and a squash is a drink
          # to the stain table, so the plant words alone were not enough to win the line
          _mildew, bias=2,
          # "my dishwasher leaves a white film on glasses" is the dishwasher's film, not a leaf:
          # "leaves" is the verb there, but the word is also the plant this row keys on, so the
          # line read a plant, a "white film" and answered with powdery mildew. A mildew question
          # never names an appliance or a pane of glass, so those words stand this row down and
          # the film answers (dishwasher-glass-film, limescale) take their own lines back.
          avoid=("dishwasher", "dishwashers", "dish washer", "washing machine", "washer",
                 "dishes", "dish", "plates", "plate", "glasses", "glassware", "mugs", "cup",
                 "cups", "cutlery", "shower", "bath", "bathtub", "tiles", "sink", "smear",
                 "smears", "streaks", "kettle", "bathroom", "toilet", "tumble dryer",
                 "tumble drier")),
    entry("plant-rot",
          (("rot", "rots", "rotting", "rotted", "rotten", "going mouldy", "gone mouldy",
            "mouldy", "moldy", "blossom end", "black at the bottom", "going soft", "turning to mush",
            "grey mould", "brown rot", "damping off"),
           # no tomato here: the avoid list below turns a tomato away to `tomato-end-rot`, so a
           # tomato word in this key could only ever be dead weight
           ("plant", "plants", "crop", "crops", "fruit", "fruits",
            "courgette", "courgettes", "cucumber", "cucumbers", "pepper", "peppers",
            "melon", "melons", "aubergine", "aubergines", "dahlia", "dahlias",
            "squash", "pumpkin", "pumpkins", "strawberry",
            "strawberries", "apple", "apples", "pear", "pears", "plum", "plums", "potato",
            "potatoes", "onion", "onions", "garlic", "seedling", "seedlings", "cutting",
            "cuttings", "stem", "stems", "tree", "vine", "vines", "greenhouse", "ground",
            "allotment", "bed", "beds")),
          _rot, bias=2,
          # a loaf, a spread of cheese or a joint of meat is the kitchen's question, and it has
          # its own rows: the rot words are the same ones a crop uses, so the food nouns in the
          # line stand this row down
          guard=lambda understood: not _a_kitchen_thing(understood),
          # a fridge, a cupboard or a wheelie bin is storage, and wood is the DIY lane's: only a
          # crop that is still growing (or just lifted) is this question.
          # a mouldy pot of compost is not a rotting crop: white furry mould on the surface is
          # feeding on the compost, and the soil-mould row is the answer to that question
          avoid=("fridge", "freezer", "cupboard", "store", "stored", "storing", "keep for",
                 "use by", "best before", "bin day", "wheelie", "wood", "fence", "decking",
                 "mould on", "mouldy soil", "mouldy compost", "mouldy pot", "white mould",
                 "white stuff", "furry mould", "fuzzy mould", "plant pot mouldy",
                 "on the soil", "on the compost", "pot of compost", "potting compost",
                 "potting", "houseplant", "house plant",
                 # bare "compost" used to stand here, and it stood the row down on a seedling
                 # tray: "my seedling compost is mouldy" is damping off, which is this row, and
                 # on main it was answered. The phrase is what a mouldy pot says.
                 "deck", "shed", "window frame", "joist", "beam", "floorboard", "tooth", "teeth",
                 # a tomato's black bottom already has its own table in this file
                 # (`tomato-end-rot`), which says the same thing in its own words: two rows for one
                 # question is what this row is here to avoid.
                 "tomato", "tomatoes", "tomato plant")),
    entry("plant-pests",
          # The pest is the subject and has to be in the line: the three-part key this started
          # as let a plant word and an ask phrase match on their own, and "how do i get rid of
          # black spots on my roses" and "how do i get rid of ants on my plants" were both told
          # to squash the aphids. A pest name and one of the words below are now the whole key,
          # and a spider mite or a scale insect on a plant still reaches it through the ask.
          (("aphids", "aphid", "greenfly", "green fly", "blackfly", "black fly", "whitefly",
            "white fly", "caterpillars", "caterpillar", "cabbage white", "cabbage whites",
            "vine weevil", "vine weevils", "scale insect", "scale insects", "mealybug",
            "mealybugs"),
           ("rose", "roses", "plant", "plants", "leaves", "leaf", "cabbage", "lettuce",
            "courgette", "courgettes", "tomato", "tomatoes", "bean", "beans", "broad beans",
            "brassica", "brassicas", "flowers", "greenhouse", "crop", "crops", "shoots",
            "get rid of", "rid of", "kill", "killing", "control", "spray", "deal with",
            "covered in", "on them", "on it",
            # the pest name is the subject, so "on my orchid" or "all over the stem" is enough of
            # a second part: a named pest is the question wherever it is sitting
            "on my", "on the", "in my", "under the", "all over", "everywhere", "infested")),
          _pests, bias=2),
    entry("plant-leaves-yellow",
          # The general shape, for every plant nobody has an entry for: "my plant has yellow
          # leaves", "my orchid leaves are drooping", "my fern is turning brown at the tips". It
          # sits after the plant-specific entries (basil, hydrangea, tomatoes) and the houseplant
          # watering entry, and gives way to them, so a named plant or a named care problem wins.
          # A lawn is not here: no compost an inch down, no drainage hole, so `lawn-care` has it.
          (("leaves", "leaf", "plant", "plants", "shrub", "foliage",
            "fern", "orchid", "mint", "cactus", "succulent", "spider plant", "money plant"),
           ("yellow", "yellowing", "yellowish", "brown", "browning", "turning brown", "going brown",
            "brown tips", "crispy", "dying", "drooping", "wilting",
            # "my plant is limp" and "my plant is floppy" are the same roots question as drooping
            "limp", "floppy", "sagging",
            # "my plant looks sick" and "my plants are struggling" are the same triage; the first
            # group already needs a plant, so a person feeling sick cannot reach this.
            "sick", "poorly", "struggling", "unwell", "not looking well",
            # "my plants look sad" is the same triage as "my plant is sick", said the way
            # people say it, and it had no plant answer at all: "my plants look sad" reached
            # the chat module's "what have you noticed", and "my houseplant is looking sorry
            # for itself" was told where to buy flowers. The first group still needs a plant,
            # so somebody saying they are sad themselves never comes here.
            "look sad", "looks sad", "looking sad", "look unhappy", "looks unhappy",
            "looking unhappy", "not happy", "miserable", "sorry for itself", "sulking",
            "sulky", "struggling",
            # "sad" on its own, because "the plants look a bit sad" and "my sad little fern"
            # put a word in the middle of the phrase. The plant in the first group keeps most
            # of a person's own bad day out of this answer, but not all of it: "i feel sad about
            # my plant" names a plant and is still somebody's feeling, and the warm reply it had
            # before was the right one. So the feeling is named, the way the first group names
            # the plant - a line that says how the person feels is theirs, and the plant-looking
            # words above are how they say the plant is the sad one.
            "sad")),
          ("Nine times in ten it is the roots, not the light: check the compost an inch down and the "
           "drainage holes, because yellowing leaves are usually too much water or a pot with nowhere "
           "for it to go. Let it dry out, tip the standing water away, and give it a brighter spot "
           "away from a radiator; feed it only once it is growing again. Is it in a pot indoors, or out "
           "in the garden?"),
          ask=("leaves", "leaf", "plant", "plants", "shrub", "brown", "yellow", "turning",
               "drooping", "wilting"),
          # The word "houseplant" already has the better answer: `houseplants-watering` takes
          # `houseplant`/`house plants` with `leaves`, `yellow`, `drooping`, `dying` and the rest,
          # and its "too much water, no drainage hole, saucer left full" is this same roots answer
          # with more of the plant in it. So a line that says houseplant keeps that one, whatever
          # colour the leaves are - `the leaves on my houseplant are going brown` and `my houseplant
          # has brown tips on the leaves` are exactly those lines. "pale" is left out of the
          # colours for the same reason: pale leaves are a light question, and `plant-sunlight`
          # answers it with the photosynthesis a pale leaf actually wants.
          # A named plant or a named problem has a better answer than the general one, and those
          # entries come later in this file and are more specific, so they keep their line: the
          # brown-tip answer, the cactus one, the tomato ones, the supermarket herb pot, the
          # basil, the hydrangea and the lawn. The word "pale" is left out of the colours for the
          # same reason - pale leaves are a light question, and the sunlight entry answers it.
          avoid=("houseplant", "houseplants", "house plant", "house plants", "indoor plant",
                 "indoor plants", "pot plant", "pot plants",
                 # any tip is the brown-tip question, however it is written ("brown at the tips",
                 # "the tips are going brown"), and that answer says how to treat one
                 "tips", "tip", "brown edges", "crispy edges",
                 "mint", "parsley", "coriander", "cilantro", "chives",
                 "tomato", "tomatoes", "basil", "hydrangea", "lavender", "roses", "rose",
                 "lawn", "grass", "turf", "nettle", "garlic", "peace lily",
                 # a tree's leaf turning is the autumn fact in nature.py, not a pot with nowhere
                 # to drain
                 "tree", "trees", "apple tree", "oak", "maple", "birch", "willow", "hedge",
                 # "i feel sad about my plant" names a plant and is still somebody's own feeling
                 # - the warm reply it had before is the right one, and the plant-looking words
                 # above ("look sad", "is sad") are how a person says the plant is the sad one.
                 # So a line that says how they feel is theirs, and the plant waits for the next
                 # turn.
                 "i feel", "i am sad", "im sad", "i'm sad", "i am upset", "im upset", "i'm upset",
                 "i feel low", "i feel down", "feeling sad", "feeling low", "feeling down",
                 "made me sad", "makes me sad", "made me feel", "feel miserable",
                 "feel unhappy", "i am miserable", "i'm miserable", "feel like crying"),
          guard=_the_person_is_sad_too),
    entry("prune-lavender", ("lavender", ("prune", "pruning", "cut", "trim", "back", "woody",
                                          "leggy", "look after", "looking after", "care",
                                          "care for", "take care of", "need", "needs", "grow",
                                          "growing", "plant", "planted", "deadhead",
                                          "deadheading", "when do i", "how do i",
                                          "keep it", "keep them", "sun", "soil", "drainage")),
          "Trim it in late August, straight after flowering: take the flower stalks off plus about "
          "2.5cm of this year's leafy growth, and never cut into the bare brown wood, because it "
          "does not grow back. That keeps it dense and stops it going leggy, and leaving a little "
          "new growth on in autumn gives the plant something to shelter behind in winter. The other "
          "half of looking after it is the ground: full sun and sharp drainage, a gravelly or raised "
          "bed, because lavender rots in wet heavy soil in winter and that is the one thing that "
          "kills it. Water it for its first summer only - after that the rain is enough.",
          # "grow", "plant" and "need" are in the key so that "how do i grow lavender" and "what
          # does lavender need" reach this row, and they are the words a cuttings or a container
          # question also uses: "how do i grow lavender from cuttings" was scoring this row above
          # the cuttings one (tidy-aspen). A cutting, a seed and a pot are a different job, and
          # each has its own row.
          # Plural only, never bare "cutting": an avoid word is read in its loose forms, so
          # "cutting" also matches "cut", and three of the row's own questions - "when should i
          # cut back lavender", "when do i cut back lavender", "should i cut the flowers off my
          # lavender" - stood the row down on their own verb (keen-book).
          avoid=("cuttings", "propagate", "propagating", "from seed", "sow", "sowing",
                 "in a pot", "in pots", "in a container", "in containers", "transplant",
                 "root", "roots", "rooting",
                 # moving or splitting an established plant is its own job, and the row's
                 # "plant"/"grow" key words were taking it: "how do i move a lavender plant"
                 # had the general move-a-shrub-while-dormant answer and was getting the trim
                 "move", "moving", "moved", "relocate", "relocating", "dig up", "digging up",
                 "replant", "replanting", "split", "divide", "dividing",
                 # "how do i" and "when do i" are in the key to carry "how do i look after
                 # lavender", but they also carried every other lavender question with them:
                 # oil, drying, lavender bags and cooking all got the trim card. The row's own
                 # job words (prune, cut, trim, look after, care, grow, need) already hold the
                 # care shapes it is for.
                 "oil", "oils", "bag", "bags", "sachet", "sachets", "dry", "drying", "dried",
                 "harvest", "harvesting", "cooking", "baking", "recipe", "recipes",
                 "candle", "candles", "soap", "wreath", "bunch")),
    entry("potatoes-in-a-bag",
          (("potato", "potatoes", "spud", "spuds", "seed potatoes", "seed potato"),
           ("bag", "bags", "sack", "sacks", "grow bag", "grow bags", "growbag", "bucket",
            "tub", "container", "containers", "pot", "pots", "earthing up", "earth up",
            "earthing", "earth them up", "ridge", "ridges", "haulm", "trench", "trenches",
            # "how many" and "how deep" are here only with the container named, because bare
            # "how many" took "how many weeks do potatoes take" off the sowing row
            "how many in a bag", "how many seed potatoes", "how deep in a bag",
            "how deep in a pot", "how deep to plant them",
            # the sowing row keys "grow potatoes" and scores a phrase for it, so the container
            # lines say the container out loud: "how do i grow potatoes in a bag" is this answer
            "in a bag", "in bags", "in a sack", "in a grow bag", "in a bucket", "in a tub",
            "in a pot", "in pots", "in a container", "in containers")),
          ("Chit the seed potatoes somewhere light and cool, in an egg box, until the sprouts are "
           "2-3cm long, then plant them from late March. A 40-litre bag or a 30cm pot takes three "
           "seed potatoes: 10-15cm of compost in the bottom, sit them on it, cover them with "
           "another 10cm and water. When the shoots are 15cm above the compost, earth them up - "
           "cover all but the top few centimetres with more compost - and keep doing that until "
           "the bag is nearly full, because tubers that form near the surface turn green in the "
           "light."),
          ask=("how", "how many", "how deep", "when", "best", "can i", "do i", "should i"),
          # it names the container as well as the crop, so it beats the general container row that
          # "in a bag" and "in a bucket" also score
          bias=2,
          avoid=("sweet potato", "sweet potatoes", "couch", "crisps", "chips", "mash", "recipe",
                 "cook", "cooking", "roast", "bake", "salad", "eat", "eat them", "green bin",
                 # A crop in a bag is still a crop to cook: "what can i make with a bag of
                 # potatoes" asked what to cook and was told to chit the seed potatoes, because
                 # the row keys the crop and the word "bag" and reads "can i" as its ask. The
                 # dish frame is already what the general container row stands down for.
                 *DISH_ASK,
                 "peel", "store", "keeping", "chitting", "blight", "disease", "pest",
                 # "when do i harvest potatoes" is the harvest row's line and must stay its own
                 "harvest", "harvesting", "lift", "lifting", "dig up", "digging up", "ready",
                 "when are they ready")),

        entry("deadhead-flowers",
          # The subject comes first, because the first key part has to be said: the plant or the
          # flowers. The job is then one of two more parts, so "how do i deadhead dahlias",
          # "how do i keep cosmos flowering" and "my flowers have stopped flowering" all arrive
          # and none of them needs the other half's words.
          (("dahlia", "dahlias", "sweet pea", "sweet peas", "cosmos", "geranium", "geraniums",
            "pelargonium", "pelargoniums", "petunia", "petunias", "rose", "roses", "begonia",
            "begonias", "calendula", "marigold", "marigolds", "nasturtium", "nasturtiums",
            "lupin", "lupins", "foxglove", "foxgloves", "penstemon", "delphinium", "salvia",
            "pansy", "pansies", "viola", "zinnia", "zinnias", "sunflower", "sunflowers",
            "flower", "flowers", "flowering", "blooms", "basket", "hanging basket"),
           ("deadhead", "deadheading", "dead heads", "spent flowers", "spent blooms",
            "spent flower heads", "old flowers", "faded flowers", "faded blooms",
            "pinch out", "pinching out", "more flowers", "flowering for longer",
            "stop flowering", "stopped flowering", "keep deadheading"),
           # "keep" is a hundred things on its own, so it is a part here and needs a flower with
           # it: "how do i keep cosmos flowering" has the flower but not the word deadhead
           ("keep", "keeping", "longer", "more", "still", "wont", "won't", "stopped", "stop")),
          "Pick or snip the spent flower off with its stalk, down to the next bud or strong shoot, "
          "and do it every few days through the summer. That is the whole trick: once a plant is "
          "allowed to set seed it stops making flower, so cutting the dead heads off is what keeps "
          "it going until the frost. Dahlias, cosmos, sweet peas, geraniums and petunias all want "
          "it twice a week in a hot spell, and sweet peas must not be left to make pods, because a "
          "pod turns the plant woody and it stops. Annuals that are nearly over can be cut back "
          "hard, to 15cm, and they come again.",
          # "sweets" cannot go here: it stems to "sweet", and "how do i deadhead sweet peas" was
          # stood down by its own avoid list because of it.
          # a bunch that has been cut and brought indoors is the vase-life row's, and "keep them
          # going" / "how long do they last" were this row's before the flowers were out of water
          avoid=("sugar", "diet", "calories", "dessert", "carbs", "cut out", "cutting out",
                 "vase", "bouquet", "bunch", "cut flowers", "fresh", "last longer", "in water",
                 # a basket that has dried out is a watering question: "my hanging basket keeps
                 # drying out" was answered with how to deadhead dahlias
                 "dried out", "drying out", "dries out", "dry out", "dried up", "gone dry",
                 "has dried", "keeps drying",
                 "got flowers", "bought flowers", "gave me flowers", "flowers for my",
                 "them going", "them alive", "kept them", "keep them going",
                 # a basket that has to come through the frost is the winter row's line
                 "winter", "over winter", "in winter", "frost", "frosts", "cold",
                 "weed", "weeds", "grass", "lawn", "hedge", "tree", "trees",
                 # a rose is pruned, and the rose row is the one that says so
                 "rose", "roses", "rose bush", "rose bushes",
                 # a plant with no flowers at all is the why-has-it-not-flowered question - four
                 # causes, shade, feed, frost, pruning time - and not the deadheading job
                 "no flowers", "no flower", "no blooms", "no blossom", "not flowering",
                 "not flowered", "never flowered", "wont flower", "won't flower",
                 "hasnt flowered", "hasn't flowered", "didnt flower", "didn't flower", "blind"),
          ),
    entry("wasp-nest", ("wasp", ("wasps", "nest", "loft", "attic", "remove", "allergic", "shed")),
          "If it is somewhere nobody goes, leave it: a wasp nest dies in autumn and is never reused. "
          "If it is by a door or someone in the house is allergic, pay a local pest controller, "
          "usually 50 to 80 pounds, rather than going up a ladder with a spray - and do not block "
          "the entrance, because they will find another way into the house.",
          # A removal question should beat main's "why are wasps everywhere in autumn" fact when a
          # line fits both; the specific job wins on purpose rather than by entry order.
          bias=1, report=True),
    # A wasp near you is not a nest to remove and it is not a pest controller to call: "how do i
    # stop a wasp stinging me" was answered "call a pest controller", which is a price and a wait
    # for a question about the next ten seconds. The advice is what to do with your own body.
    # "i was stung and it hurts" names no insect at all, and it is the same question, so the
    # event is a subject word here - with a fence for the stings that are not a wasp.
    entry("wasp-near-you", (("wasp", "wasps", "bee", "bees", "wasp sting", "bee sting",
                             "sting", "stings", "stung", "was stung", "been stung", "got stung",
                             "stung me"),
                            ("stinging", "stung", "sting", "stop", "away", "near", "near me",
                             "landing", "chasing", "buzzing", "bothering", "coming at",
                             "won't leave", "wont leave", "keep coming", "swat", "swatting",
                             "around me", "stood on", "stepped on", "trod on", "hurts",
                             "hurting", "sore", "first aid",
                             # "a wasp keeps landing on me" was the card about a fly landing on
                             # food: the food card keys "landing" and "on me" together, which
                             # out-scored this row for a wasp that is circling a person
                             "keeps landing", "landing on me", "landing on my", "on me",
                             # the place the sting went in, said with a possessive: the sting
                             # words are subject words now, so a line whose only other content is
                             # "on her hand" covered one position and got no answer at all -
                             # "my daughter got stung by a wasp on her hand" was a receipt on
                             # main's treatment. The body is the second signal.
                             "hand", "hands", "foot", "feet", "leg", "legs", "arm", "arms",
                             "finger", "fingers", "thumb", "wrist", "ankle", "toe", "toes",
                             "palm", "cheek", "chin", "face", "neck", "shoulder", "ear", "ears",
                             "lip", "lips", "eye", "eyelid", "eyebrow", "head", "skin")),
          _wasp_near,
          # the way out of the room beats the fact about why they are about in autumn
          bias=2,
          # a nest in the loft, a trap in the garden and an allergy test are other answers
          avoid=("nest", "nests", "loft", "attic", "shed", "colony", "swarm", "trap", "traps",
                 "allergic to", "allergy", "anaphylaxis", "epipen", "epi pen", "pest control",
                 "pest controller", "exterminator", "remove", "removing", "get rid",
                 # a wasp loose in a room or a car is answered by what to do about the space -
                 # open a window wide, pull over - and that answer already says the rest.
                 "room", "rooms", "living room", "bedroom", "bathroom", "kitchen", "office",
                 "car", "van", "train", "bus", "indoors", "inside", "in the house",
                 "got in", "got into", "flew in",
                 # a sting already given is the sting answer, and the commonest phrasing of it
                 # has no past tense in it: "how do i treat a wasp sting" and "my wasp sting is
                 # swelling" were both told to stand still and step away from a wasp long gone.
                 "treat", "treating", "treatment", "after a sting", "swelling", "swollen",
                 # the stings that are not a wasp or a bee: a nettle, a jellyfish and a scorpion
                 # each need a different answer, and "sting" is now a subject word here
                 "nettle", "nettles", "jellyfish", "scorpion", "ant", "ants", "mosquito",
                 "mosquitos", "mosquitoes", "horsefly", "tick", "ticks", "wasp beetle")),
    # A dog that ate a clove of garlic is not a planting question, and "cloves" is a key word
    # here, so "my dog ate a garlic clove" was reaching this answer. Planting is never what an
    # eaten line means.
    entry("plant-garlic", ("garlic", ("plant", "planting", "grow", "growing", "cloves", "when")),
          "Plant garlic cloves in autumn, October to early December: pointy end up, 15cm apart and "
          "about 2.5cm deep, in a sunny spot with soil that drains. It needs cold to split into a "
          "bulb, which is why autumn beats spring. Water it while it grows and stop a fortnight "
          "before you lift it, when the leaves start to yellow, in July.",
          avoid=("ate", "eat", "eats", "eaten", "eating", "swallowed", "licked", "dog", "dogs",
                 "cat", "cats", "puppy", "kitten", "pet", "pets", "poisonous", "toxic")),
     entry("cut-flowers",
          (("cut flowers", "flowers", "flower", "bouquet", "vase", "stems", "tulips", "daffodils",
            "roses"),
           # "how do i store cut flowers" and "how often should i change the water in a vase"
           # were two shrugs: the row answers both, and the words people ask them with were the
           # only thing missing. "sugar", "aspirin", "bleach", "food" and "conditioner" are not
           # here: they ask what to put in the water, which this answer does not say, so a line
           # about them was a punt on main and is a punt again rather than confident advice
           # about a different question (curious-zebra, #5174).
           # NOT the bare "keep": a keeping row keyed on the plain verb is stood down for every
           # "my flowers keep dying" line, because "keeps" is also the fault verb ("keeps coming
           # out flat"). The phrases hold the ones that need it.
           ("last", "longer", "fresh", "keep fresh", "keep them", "keep it", "keep a",
            "keep my", "keep the", "keep alive", "alive", "looking good", "look good",
            "store", "storing", "stored", "change",
            "changing", "water", "droop",
            "drooping", "droopy", "dying", "wilt", "wilting", "vase", "days", "tips")),
          "Trim about 2cm off each stem at an angle with a sharp knife, strip any leaf that would "
          "sit in the water, and change the water every couple of days: the angle gives the stem a "
          "wide surface to drink through and the slime on old stems is what blocks it. Keep the "
          "vase out of direct sun and away from fruit, since ripening fruit gives off ethylene that "
          "ages flowers. Tulips and daffodils drink a lot, so top those up daily; daffodils go in "
          "their own vase because their sap shortens the life of other flowers.",
          # a plant in the garden has its own problem, and these lines are about a plant, not a vase
          # "flowering" is a loose form of "flowers", so it cannot go in the avoid: it took the
          # three commonest lines with it. A plant in a border is caught by the words below.
          avoid=("garden", "border", "grow", "growing", "planted", "bush", "shrub", "tree",
                 "lawn", "hydrangea", "basil", "tomato", "tomatoes", "lavender", "bulbs",
                 # a plant in the border being watered is the garden, not a vase: "how often
                 # should i water my roses" was getting "trim 2cm off each stem"
                 # "watering" is a form of "water" and the row keys it, so an avoid word written
                 # that way stands the row down for "change the water in a vase" too: only the
                 # phrases that never appear in a vase question go here
                 "water my", "water the", "feed", "feeding", "fertiliser", "fertilizer", "mulch",
                 "prune", "pruning", "deadhead", "deadheading",
                 "bloom", "blooms", "blooming",
                 # "do i put sugar in the vase" and "is it ok to put bleach in the vase" ask
                 # what to put in the water, which this answer never says, so they stand the row
                 # down (curious-zebra, #5174). It is the putting-in phrase that is held out and
                 # not the bare word: orange-salmon found that "does sugar keep flowers alive"
                 # and "does aspirin keep flowers alive" are keeping questions, and on main they
                 # got this answer - a bare "sugar" in the avoid took them away
                 "put sugar", "put bleach", "put aspirin", "add sugar", "add bleach",
                 "sugar in the vase", "bleach in the vase", "sugar in the water",
                 "bleach in the water", "in the vase water", "flower food", "flowerfood",
                 "conditioner")),
    # "how long do cut flowers last" was answered with first aid - how long a cut takes to heal -
    # because the word "cut" named an injury and nothing in the row said flowers. The keeping row
    # above answers how to make them last; this one answers how long, in numbers, which is a
    # different question with a different shape of answer.
    entry("cut-flowers-vase-life",
          # the subject has to be the vase, not the plant: with the bare flower names in this
          # group "how long do daffodils flower for" scored on "daffodils" and "how long" and
          # got "about a week", when a daffodil flowers for about six weeks in the border. The
          # names still reach this row through the words that make it a vase question - "how
          # long do roses last in a vase", "how long does a vase of tulips last" - so a border
          # question keeps its punt instead of getting a confident wrong number.
          (("cut flowers", "flowers in a vase", "vase", "bouquet", "cut stems", "flowers in water"),
           # only the how-long shape: "how do i make cut flowers last longer" is the keeping row's
           # question, and a bare "last" or "week" in this ask took it
           ("how long", "how many days", "vase life", "last a week", "last two weeks",
            "last a fortnight")),
          "About a week is a fair bet for a mixed bouquet: tulips and roses give you around seven "
          "days, daffodils and sweet peas five, carnations and lilies ten to fourteen, and a "
          "bouquet of gypsophila or dried stems longer than that. The stems seal over within a "
          "day or two, so an angled cut and clean water every couple of days is what buys the "
          "extra days.",
          # the keeping row answers the same lines and says what to do; the number is what this
          # one is for, so it wins the tie when the line asks how long
          bias=1,
          avoid=("garden", "border", "grow", "growing", "planted", "bush", "shrub", "tree",
                 "lawn", "hydrangea", "basil", "tomato", "tomatoes", "lavender", "bulbs",
                 "heal", "wound", "bleeding", "stitches", "paper cut", "my finger", "my hand",
                 # "how long do daffodils flower for" and "how long do lilies bloom" are the
                 # border, not the vase: daffodils flower for six weeks outside and five days in
                 # water, and the vase number given to a garden question is a confident wrong
                 # answer where there used to be a punt
                 "bloom", "blooms", "blooming", "in the ground", "in the border", "water my",
                 "water the", "feed", "fertiliser", "fertilizer")),
    # "how much should we spend on flowers" was a shrug: keeping a bunch alive is the cut-flowers
    # entry, and what a bunch costs - and what a wedding spends on them - was nobody's.
    entry("flowers-cost",
          (("flowers", "flower", "bouquet", "bouquets", "buttonholes", "buttonhole", "stems",
            "florist", "florists"),
           ("spend", "spending", "much", "cost", "costs", "price", "prices", "budget", "afford",
            "cheaper", "cheap", "save", "worth", "wedding", "weddings")),
          # The bouquet leads: a follow-up on this card is lifted from its first sentence, and
          # "how much does a bouquet cost" was answered "£4 to £8" because the supermarket bunch
          # came first. Whatever gets lifted from here is about a bouquet.
          "A florist bouquet is £25 to £45, a supermarket bunch £4 to £8, and dried or artificial "
          "stems sit in between and last years. For a wedding, flowers are usually 8 to 10 per cent "
          "of the budget: put the money into the bouquet and the buttonholes, which are in every "
          "photo, and use supermarket or dried stems for the tables and the aisle. For a funeral, a "
          "wreath or a casket spray is £30 to £100 and a tied sheaf £20 to £40. Buying the same "
          "flower in season, from a market rather than a florist, and arranging it yourself the day "
          "before is where the saving usually is.",
          ask=("spend", "much", "cost", "costs", "price", "budget", "afford", "cheaper", "worth",
               "wedding"),
          # keeping a bunch alive, growing them, and a flower you wear are other answers
          avoid=("last", "lasts", "longer", "fresh", "droop", "drooping", "wilt", "wilting",
                 "vase", "water", "garden", "grow", "growing", "plant", "planted", "bulbs",
                 "prune", "deadhead", "sow", "seed", "seeds", "corsage", "hair", "wrist",
                 # "how much sun do flowers need" and "how much water" are how to grow them,
                 # not what they cost: the watering row keys "how much" too, so those two are
                 # held out here.
                 "sun", "sunlight", "sunny", "shade", "light", "soil", "compost", "planting"),
          # the watering row keys "how much" and "flowers" as well, so a bare "how much are
          # flowers" was its line: one point more is what puts the price question first
          bias=2),

    entry("plant-brown-tips",
          (("brown tips", "brown tip", "tips going brown", "brown edges", "crispy edges",
            "crisp edges", "brown leaf tips", "tips are brown"),
           ("tips", "brown"),
           ("leaf", "leaves", "plant", "plant's", "houseplant", "houseplants", "foliage",
            "peace lily", "spider plant", "snake plant", "pothos", "monstera", "orchid", "fern",
            "dracaena", "yucca", "palm", "calathea", "zz plant")),
          "Brown tips are usually dry air, hard tap water or a plant that dried right out once: "
          "the leaf edges die first because they are furthest from the roots. Snip the brown off "
          "with scissors so it stops spreading, water it when the top of the compost is dry rather "
          "than in sips, move it off a radiator or a draughty windowsill, and use rainwater or "
          "left-out tap water if your water is hard.",
          # a rose or a tomato with brown leaves is its own plant's problem, not this one
          avoid=("rose", "roses", "tomato", "tomatoes", "basil", "hydrangea", "lavender",
                 "lawn", "grass", "autumn", "winter", "tree", "trees")),
    entry("cactus-care",
          (("cactus", "cacti", "succulent", "succulents", "christmas cactus", "christmas cacti"),
           ("keep", "alive", "water", "watering", "care", "care for", "dying", "shrivel",
            "shriveled", "wrinkled", "wrinkly", "yellow", "droop", "limp", "leaves", "rot",
            "look after", "thriving")),
          "Cacti and succulents want a sunny windowsill, gritty compost and far less water than "
          "they get: soak the pot, let it dry right through, and that is every two to three weeks "
          "in summer and barely at all from November to March. A Christmas cactus is the "
          "exception - it is a forest cactus - so give it bright light out of full sun, water when "
          "the top half of the pot is dry, and cool nights in autumn, which is what sets the buds.",
          # the per-plant watering rows match "keep ... alive" and "dying" as well now, and this
          # row says more about a cactus than a cadence alone does
          bias=2),
    entry("nettle-sting",
          (("nettle", "nettles", "stinging nettle", "stinging nettles"),
           ("sting", "stung", "put on", "relieve", "itch", "itchy", "rash", "hurts",
            "better")),
          "Cool it under running water or with an ice pack for ten minutes and put an "
          "antihistamine cream on it: a nettle sting is histamine plus tiny hairs, which is why a "
          "dock leaf does nothing except cool the skin as you rub it. It settles in a few hours. "
          "Get help if the swelling spreads well beyond the sting, or if they feel wheezy, sick "
          "or faint."),
    # "does a dock leaf actually work" is the same sting question, so it gets the same answer
    entry("dock-leaf",
          (("dock leaf", "dock leaves", "dockleaf", "dockleaves"),
           ("work", "works", "actually", "help", "helps", "do anything", "good", "true",
            "really", "sting", "stung", "nettle", "nettles", "why", "how")),
          "Not really: a dock leaf only helps because rubbing a cool, damp leaf on a sting cools "
          "the skin and takes your mind off it. Nettle stings are histamine plus tiny hairs, so "
          "run the sting under cool water for ten minutes and put an antihistamine cream on it; "
          "it settles in a few hours."),
    entry("tomato-end-rot",
          (("tomato", "tomatoes", "tomato plant", "tomato plants"),
           ("black", "bottom", "patch", "patches", "rot", "blossom end", "end", "squashy",
            "sunken")),
          "Those black sunken patches on the bottom are blossom end rot, and it is not a disease: "
          "the fruit cannot pull up enough calcium when watering swings from bone dry to soaked, "
          "so a dry spell then a flood sets it off. Water little and often at the base, mulch to "
          "hold the moisture, use a tomato feed, and take the marked fruit off because it will not "
          "recover.",
          # The fruit is what this is about, and "at the bottom" is where the leaves are too:
          # "my tomato plants have yellow leaves at the bottom" was told its fruit had blossom end
          # rot when the whole of the question was the leaves. A leaf word with no black or rot
          # word in the line is the leaf question, which `tomato-yellow` answers; a line that
          # names both keeps the rot, because the black word is the fruit.
          guard=lambda understood: not _a_leaf_problem_not_the_fruit(understood)),
    # A crop that will not ripen, and a fruit that rots on the plant: the two complaints that
    # arrive with the crop named rather than the symptom, so the key starts at the plant and the
    # state it is in. "why are my tomatoes not turning red" was reaching the laundry answer.
    entry("tomato-ripening",
          (("tomato", "tomatoes", "toms", "tomato plant", "tomato plants"),
           ("not ripening", "not turning red", "not turning", "wont ripen", "will not ripen",
            "still green", "stay green", "turning red", "ripening", "ripen",
            # The same question asked as the harvest rather than the colour: "will my tomatoes
            # still fruit this year" was answered "Botanically a tomato is a fruit that grows from
            # the flower", and what the person wants to know is whether the green ones will come
            # good. Both answers are in the paragraph below.
            "still fruit", "will it fruit", "will they fruit", "fruit this year", "fruiting",
            "set fruit", "setting fruit", "still crop", "will it crop", "will they crop",
            "crop this year", "still produce", "get fruit")),
          "They ripen on warmth and the ethylene they give off themselves, so the two things that "
          "speed them up are heat and a crowd: keep them on the plant while the nights stay above "
          "about 10C, and once the weather turns pick the whole truss and bring it indoors. A ripe "
          "apple or a banana skin in the paper bag does the same job as a sunny windowsill. Green "
          "tomatoes on a plant that is dying back will not come good on it - ripen them off the "
          "plant, or cook them.",
          # A green tomato in a kitchen is dinner, and a fruit that splits has its own watering
          # answer: "my tomatoes split before they ripen" is the splitting, not the ripeness.
          avoid=("chutney", "fry", "fried", "salsa", "salad", "pickle", "recipe", "cook",
                 "cooking", "roast", "split", "splits", "splitting", "crack", "cracks",
                 "cracked", "cracking")),
    # Soft fruit that rots where it grows is grey mould, and a courgette or squash that goes soft
    # at the flower end is the calcium-and-water problem the tomato answer already names: two
    # different answers, so two entries, both keyed on the crop plus the state it is in.
    entry("soft-fruit-rot",
          (("strawberry", "strawberries", "raspberry", "raspberries", "blackberry",
            "blackberries", "blueberry", "blueberries", "gooseberry", "gooseberries", "grapes",
            "currants"),
           ("rotting", "rot", "rotten", "mouldy", "moldy", "grey mould", "mushy", "going soft",
            "rots", "mould", "furry", "grey fuzz")),
          "That is grey mould, botrytis: it starts on a bruised or split berry and spreads by "
          "touch and by wet leaves, so pick and bin every affected fruit rather than leaving it "
          "on the plant. Water at the base in the morning rather than over the leaves, open the "
          "plant up so air gets through, and put straw or a mat under the fruit so it is not "
          "sitting on wet soil. It spreads in the fridge too, so do not store a mouldy punnet "
          "with sound ones.",
          # a punnet in the fridge, a pan and a recipe are dinner, not the plant
          avoid=("fridge", "freezer", "punnet", "carton", "shop", "supermarket", "keep",
                 "keeping", "recipe", "cook", "cooking", "roast", "bake", "jam", "smoothie")),
    entry("courgette-end-rot",
          (("courgette", "courgettes", "zucchini", "squash", "pumpkin", "marrow", "marrows"),
           ("rotting", "rot", "rotten", "soft end", "yellow end", "brown end", "tip", "tips",
            "end", "ends", "mushy", "going soft", "shrivelled")),
          "A courgette or squash that rots at the flower end is the same problem as blossom end "
          "rot in tomatoes: the fruit cannot pull up enough calcium when watering swings from "
          "bone dry to soaked, so the tip goes soft and brown. Water little and often at the base, "
          "mulch to hold the moisture, and take the affected fruit off because it will not "
          "recover - the plant then puts its energy into the next ones. A high-nitrogen feed "
          "makes it worse, so use a tomato feed instead.",
          avoid=("fridge", "freezer", "recipe", "cook", "cooking", "roast", "bake", "fry",
                 "pasta", "soup", "bread", "cake", "salad")),
    entry("tomato-yellow",
          (("tomato", "tomatoes", "tomato plant", "tomato plants"),
           ("yellow", "yellowing", "pale", "leaves", "leaf", "lime"),
           ("green veins", "between the veins", "between green veins", "veins")),
          "Yellow leaves on a tomato are usually a feeding or watering problem rather than a "
          "disease. If the yellow sits between green veins, that is magnesium: water evenly, "
          "mulch, and give a tomato feed with magnesium in it. If the lowest leaves go pale and "
          "drop off, the plant is short of nitrogen or the roots are waterlogged. Pick the yellow "
          "leaves off, feed weekly, and water little and often rather than in floods; brown "
          "blotches or black bottoms are a different problem.",
          # the black-bottom question has its own answer, and so does a brown tip
          avoid=("black bottom", "black bottoms", "black at the bottom", "bottom is black",
                 "bottoms are black", "blossom end", "sunken patch", "sunken patches",
                 "rot at the bottom", "rot", "brown tips", "brown tip", "fruit", "fruits",
                 # a curling leaf is a climate question, and it was getting the yellow one
                 "curl", "curls", "curled", "curling", "rolled", "rolling", "rolling up")),
    entry("pot-herb-yellow",
          # "how do i keep herbs alive" is the same crowded-pot question as "why is my basil
          # going yellow", and the word "herbs" was in no row's subject: the line fell to the
          # search hedge while the pot answer sat one word away.
          (("mint", "parsley", "coriander", "cilantro", "chives", "supermarket herbs", "herb",
            "herbs", "basil", "rosemary", "thyme", "oregano", "dill", "sage"),
           ("yellow", "yellowing", "pale", "dying", "wilted", "wilting", "drooping", "keep",
            "alive", "last", "leaves", "leaf")),
          "A supermarket herb pot is a dozen seedlings crammed into one small pot, so it runs out "
          "of root room and food and starts going yellow within a fortnight. Split it into two or "
          "three pots with fresh compost now, keep it in good light, and water when the top dries "
          "out; leaving it crowded is what kills it, not your watering.",
          # a herb with its leaves eaten was not crowded, it was eaten: the pest row answers that,
          # and "something is eating my basil leaves" was this pot answer
          avoid=("eating my", "eating the", "ate my", "eaten", "eats", "holes", "holes in",
                 "nibbled", "pest", "pests", "infestation", "greenfly", "blackfly", "aphid",
                 "aphids", "caterpillar", "caterpillars", "slug", "slugs", "snail", "snails",
                 "mould", "mold", "disease", "fungus", "mildew")),
        # The windowsill herb question is the most common garden ask there is, and the answer is
    # which herbs and why the supermarket pot dies: it is a crowded pot, not the watering.
    entry("windowsill-herbs",
          (("herbs", "herb", "basil", "mint", "parsley", "chives", "coriander", "rosemary",
            "thyme", "oregano"),
           # "keep my supermarket herbs alive" is the pot answer (pot-herb-yellow), so this entry
           # asks about the windowsill and the growing, not about keeping a bought pot going
           ("windowsill", "window sill", "kitchen window", "kitchen", "indoor", "indoors",
            "grow", "growing", "which", "easiest", "best", "dies", "dying")),
          "Basil, mint, chives and parsley are the ones that work indoors: a sunny windowsill, "
          "away from the draught of a window you open, and water when the top of the soil is dry "
          "rather than to a schedule. Mint needs its own pot or it swamps everything next to it. "
          "The supermarket pot dies because it is several seedlings crammed into one small pot, so "
          "either split it into a bigger one or expect two or three weeks and buy small plants "
          "from a garden centre instead.",
          avoid=("outdoor", "garden bed", "border", "lawn", "herbicide", "weedkiller",
                 "drying", "freeze", "frozen", "cooking with")),
    entry("prune-shrub",
    (("shrub", "shrubs", "bush", "bushes", "buddleia", "buddleja", "wisteria", "hydrangea",
      "bay tree", "bay", "laurel", "holly", "raspberry", "raspberries", "blackcurrant",
      "blackcurrants", "gooseberry", "gooseberries", "forsythia", "lilac", "philadelphus",
      "mock orange", "weigela", "spirea", "cotoneaster", "deutzia", "kerria", "viburnum",
      "hebe", "ceanthus", "ceanothus", "photinia", "pieris", "climbing plant", "climber"),
     GONE_WILD + ("prune", "pruning", "pruned", "cut back", "cutting back", "trim",
                  "trimming", "hard", "shape", "leggy", "how far back", "cut down",
                  "cut it back")),
    _prune_shrub,
    # the pruning rows above are one plant each, and a rose, a lavender, a hedge and a fruit tree
    # are each their own answer and their own month, so this row stands aside for all of them
    avoid=("rose", "roses", "lavender", "hedge", "hedges", "privet", "conifer", "apple",
           "apples", "pear", "pears", "plum", "plums", "cherry", "cherries", "damson", "fig",
           "lawn", "grass", "tomato", "tomatoes", "potato", "potatoes", "cuttings", "cutting",
           "take cuttings", "propagate", "deadhead", "deadheading", "flower", "flowers",
           "flowering", "bloom", "blooms", "blossom", "scent", "smell", "feed", "feeding",
           "fertiliser", "fertilizer", "plant", "planting", "sow", "sowing", "move",
           "transplant", "die", "dying", "died", "brown", "yellow", "drooping", "disease",
           "pick", "picking", "harvest", "harvesting", "ripe", "ripen", "ripening", "berries",
           "crop", "crops", "eat", "jam", "freeze", "freezing", "planting out",
           "black spot", "aphids", "not flowering", "no flowers"),
    bias=1),

    entry("prune-a-hedge",
    (("hedge", "hedges", "hedge trimming", "privet", "box hedge", "conifer",
      "leylandii", "beech hedge", "hornbeam"),
    GONE_WILD + ("prune", "pruning", "cut", "cutting", "trim", "trimming", "back", "when",
                 "shape", "neaten")),
    "Most hedges want one cut in late summer, from August, once the birds have finished "
    "nesting - it is against the law to disturb a nest in use, so check before you start. "
    "Box and privet take a cut in June as well. Trim so the sides slope in slightly at the "
    "top: a flat-sided hedge shades its own base and goes bare at the bottom. Leave the "
    "sides alone if you are cutting a conifer hard, because most will not regrow from old "
    "wood."),
    entry("plants-for-shade",
    (("shade", "shady", "shaded", "north facing", "north-facing", "no sun"),
    ("garden", "border", "bed", "plant", "plants", "grow", "growing", "what can i")),
    "For damp shade: ferns, hostas, astilbe, hydrangea, brunnera and foxgloves all cope and "
    "look after themselves. Dry shade under a tree is the hard one - hardy geranium, "
    "epimedium, vinca, lungwort and ivy are the ones that survive it. Whatever you plant, "
    "dig in leaf mould or compost first: shade plants fail more often from thin dry soil "
    "than from the lack of sun.",
    # a lawn in the shade is its own question, with its own answer below: this row lists plants
    # for a border, and "how do i get grass to grow in shade" was reading it as one
    avoid=("lawn", "grass", "turf", "mow", "mowing", "mown", "seed", "seeds", "reseed",
           # ferns and hostas are outdoors: a houseplant in a shady spot is the light answer's
           "houseplant", "houseplants", "house plant", "house plants", "indoor", "indoors",
           "windowsill", "pot", "pots", "conservatory",
           # and a vegetable bed under the shade wants the crops that crop, not ferns:
           # "which vegetables grow in shade" was answered with hostas and astilbe
           "vegetable", "vegetables", "veg", "crops", "crop", "salad", "edible", "edibles",
           "kitchen garden", "allotment", "tomato", "tomatoes", "potato", "potatoes", "basil",
           "lettuce", "carrot", "carrots", "beans", "peas", "onion", "onions", "garlic",
           "cabbage", "broccoli", "rhubarb", "courgette", "courgettes", "spinach", "kale"),
    # "is my plant in shade ok" is a houseplant's light question and "what should i plant in
    # shade" is a bed, and both say shade and plant. The outdoor answer only speaks when the
    # line names soil to plant in, which a houseplant by a window never does.
    ask=("grow", "growing", "bed", "beds", "border", "borders", "garden", "gardens",
         "soil", "allotment", "what should i plant", "what can i plant", "what to plant",
         "what can i grow",
         # the same phrase the light entry stands down on: a follow-up after this answer keeps
         # the bed's question instead of falling back to houseplants
         "plant shade", "plants shade"),
    # a line that names a shade and a planting is this answer, not the bright-window houseplant
    # one, and the rows that follow settle a tie the same way
    bias=4),
    # A lawn is not a border: the plants that cope with shade are not grass, and telling somebody
    # to plant ferns where they want a lawn is a confident answer to another question. Real grass
    # needs the sun, so the honest answer says how much it needs and what to do when there is
    # less.
    entry("lawn-in-shade",
          (("shade", "shady", "shaded", "shaded corner", "in the shade", "under the trees",
            "under trees", "under a tree", "north facing", "north-facing", "no sun", "dappled"),
           ("lawn", "grass", "turf", "mow", "mowing", "green", "thick", "patchy", "grow",
            "growing", "keep dying", "wont grow")),
          "Grass needs four hours of direct sun a day, so in deep shade it will always be thin: "
          "the fix is to take away the shading before you feed anything. Cut back the branches "
          "over the lawn or raise the canopy, and mow higher in shade - about 6cm rather than 4 - "
          "because longer blades catch what light there is. Feed lightly and water less often but "
          "deeply, since shade keeps the soil damp. If it stays bare, sow a shade mix of fescue "
          "and bent rather than ryegrass, or give that corner over to gravel, ferns or a bench: a "
          "lawn under a tree is a losing fight."),
    # A vegetable bed in the shade is not a border: "which vegetables grow in shade" was answered
    # with ferns, hostas and astilbe, which are lovely and none of them dinner. The crops that
    # crop in half a day of sun are a short list, and the ones that have to ripen need the sun.
    entry("veg-in-shade",
          (("shade", "shady", "shaded", "north facing", "north-facing", "no sun", "little sun",
            "half shade", "part shade", "under the trees", "under a tree", "under trees",
            "dappled"),
           ("vegetable", "vegetables", "veg", "crops", "crop", "salad", "edible", "edibles",
            "allotment", "kitchen garden", "greens", "what can i grow", "what should i grow",
            "what can i plant", "what should i plant", "tomato", "tomatoes", "potato",
            "potatoes", "lettuce", "carrot", "carrots", "cabbage", "broccoli", "rhubarb",
            "courgette", "courgettes", "beans", "peas", "garlic", "onion", "onions")),
          _shade_crop_reply,
          # a houseplant, a lawn, and the ornamental border are three other answers
          avoid=("houseplant", "houseplants", "house plant", "indoor", "indoors", "windowsill",
                 "conservatory", "lawn", "grass", "turf", "mow", "house plants", "pot", "pots"),
          bias=2),
    # A seed is not a seed round, and it is not only the biology of germination: "how do i sow
    # seeds indoors" and "how do i grow tomatoes from seed" were going to the money answer and
    # then to how a seed germinates, and neither is what the person is about to do this weekend.
    # The key is the phrases that name the job, so a question about what a seed does stays with
    # the science answer.
    entry("sowing-seeds",
          (("sow seeds", "sowing seeds", "sow a seed", "seed tray", "seed trays",
            "from seed", "start seeds", "starting seeds", "grow from seed", "sow indoors",
            "sow inside", "sow in trays", "prick out", "pricking out", "pot on"),
           ("how", "when", "best way", "what do i", "indoors", "inside", "tray", "compost",
            "heat", "light", "water", "thin", "thin out", "transplant", "start", "grow",
            "growing", "should i")),
          "Fill a tray or small pot with seed compost, firm it, water it first, and sow on the "
          "surface at the depth on the packet - about twice the seed's own size, and barely at "
          "all for tiny seed. Keep it at 18 to 21C somewhere light, cover it with a clear lid or "
          "a plastic bag until the first shoots show, then take the cover off. Water from below "
          "by standing the tray in a little water rather than pouring on top, and move each "
          "seedling into its own pot once it has two true leaves, holding it by a leaf and not "
          "the stem. Tomatoes, chillies and peppers are started indoors in March and April; hardier "
          "things wait until April, six to eight weeks before they go outside.",
          # a lawn, a crop with its own month, and the biology of germination all have their own
          # answers, and "which seeds for a salad" is a shopping question
          # a lawn, a crop with its own month, the biology of germination and a bag of seed
          # potatoes all have their own answers: "how do i grow potatoes from seed" is the chitting
          # question, and "can i eat sunflower seeds" is a food question
          avoid=("lawn", "grass", "turf", "sesame", "chia", "bird", "birds", "feed the",
                 "seedless", "sunflower seed", "pumpkin seed", "potato", "potatoes", "chit",
                 "chitting", "seed funding", "seed round", "investor", "business"),
          # "how do i grow tomatoes from seed" asks what to do, and the biology of germination
          # answers a different question in one sentence: the how-to wins the tie.
          bias=1),
    # The other half of the planting question. "what can i plant in a sunny border" was the
    # bright-window houseplant answer too, and once a border is fenced out of that row it has
    # nowhere to go - a hedge for the commonest way of asking what to put in a border.
    # "how often should i water tomatoes" was a shrug and "when should i water tomatoes" was the
    # sowing month: the outdoor plants had feeding, splitting and end-rot rows but no watering
    # cadence, only the houseplants did. One row for the watering of anything in the veg patch,
    # because the numbers are the same shape for all of them.
    entry("veg-watering",
    (("water", "watering", "watered", "how often should i water", "how often do i water",
      "how much water", "when should i water", "when do i water"),
     ("tomato", "tomatoes", "courgette", "courgettes", "bean", "beans", "runner bean",
      "runner beans", "potato", "potatoes", "pepper", "peppers", "chilli", "chillies",
      "cucumber", "cucumbers", "lettuce", "salad", "carrot", "carrots", "onion", "onions",
      "strawberry", "strawberries", "raspberry", "raspberries", "veg", "vegetable",
      "vegetables", "allotment", "greenhouse", "raised bed", "plot")),
    "Tomatoes want about two to three litres each, twice a week in dry weather, poured at the "
    "base in the morning so the leaves are dry by night. Anything in a pot needs water every day "
    "in summer, and beans, courgettes, cucumbers and potatoes want a good can each in a dry "
    "spell. Steady watering matters more than the exact amount: up and down watering is what "
    "splits tomatoes and causes blossom end rot. Rain of more than a few millimetres counts, and "
    "a mulch holds the moisture you have given them.",
    # a plant in the house, a lawn and a named hose or can are other rows; the sowing and feeding
    # questions have their own answers and are not about water
    avoid=("rinse", "rinsing", "rinsed",
      # the verb is the half people change: "wash the rice until the water runs clear" stepped
      # past a fence that only knew rinse, and this row took it on "water". Anything being
      # washed, and the phrase about the water running clear, is not a tomato.
      "wash", "washed", "washing", "water runs clear", "runs clear",
      "houseplant", "houseplants", "house plant", "monstera", "peace lily", "snake plant",
           "cactus", "succulent", "orchid", "fern", "lawn", "grass", "hose", "watering can",
           "irrigation", "sprinkler", "butt", "water butt", "rain barrel", "feed", "fertiliser",
           "fertilizer", "tomato feed", "sow", "sowing", "plant out"),
    bias=2),
    entry("plants-for-sun",
    (("sun", "sunny", "full sun", "sunshine", "south facing", "south-facing", "hot border",
      "baking hot", "baking in the sun", "drought"),
    ("plant", "plants", "grow", "growing", "border", "borders", "bed", "beds", "flowerbed",
     "what can i", "what should i")),
    "For a sunny border: lavender, salvia, verbena, sedum, rudbeckia, cosmos and a grass or two "
    "give colour from June to October and take the heat. Plant in spring or early autumn and "
    "water them well through their first summer, because that is what makes them drought-proof "
    "later; after that, a mulch in spring is most of the work. Med-style plants want sharp "
    "drainage, so add grit to heavy soil rather than compost.",
    # a houseplant, a lawn, a tomato or a vegetable bed has its own answer
    avoid=("houseplant", "houseplants", "house plant", "indoor", "window", "windowsill", "lawn",
           "grass seed", "tomato", "tomatoes", "basil", "potato", "potatoes", "veg",
           "vegetable", "vegetables", "greenhouse",
           # "baking" here means baking hot, and it was taking the kitchen sense of the word:
           # "what can i use instead of baking powder" got the sunny border. Any of the things
           # that are baked with or on is the cooking question, not this one.
           # The words are the compound ones on purpose: a bare "bake" would also stand this
           # row down for "a baking hot border", which is the garden question it exists for.
           "baking powder", "baking soda", "bicarbonate", "baking tray", "baking sheet",
           "baking tin", "baking dish", "baking paper", "parchment", "flour", "oven", "cake",
           "cakes", "biscuit", "biscuits", "bread", "scones", "muffins", "icing sugar",
           # What is going in the oven, as well as what it is baked in: "what can i bake with
           # bananas that have gone black" is a ripe-banana question and this row took it on
           # "baking" and "what can i", then had nothing to say about bananas.
           "banana", "bananas", "mash", "smoothie", "smoothies", "ripe", "overripe",
           "gone black", "gone brown",
           # The things baked with, for the same reason: "what can i bake without eggs" was
           # matched on "baking" (read from "bake") and "what can i", and was handed a sunny
           # border. An ingredient beside a cooking verb is the cooking question.
           "egg", "eggs", "butter", "sugar", "milk", "yoghurt", "yogurt", "chocolate",
           # the bare phrases "in baking" and "when baking" are left out on purpose: an avoid
           # phrase matches anywhere in the line, so "in baking" fenced out "what can i plant
           # in baking hot sun" - the very question this row exists for.
           "cocoa", "yeast", "vanilla", "frosting", "loaf", "dough", "pastry", "batter",
           # and the swap ask itself: "what can i use instead of eggs in baking" was this row,
           # because "baking" and "what can i" are its key and the eggs are the whole question.
           "instead of", "substitute", "substitutes", "swap", "replace"),
    bias=3),
    entry("cats-in-the-garden",
    (("cat", "cats", "neighbour's cat", "neighbours cat", "next door's cat"),
    ("poo", "pooing", "pooping", "toilet", "mess", "messing", "digging", "dig", "scratching",
    "wee", "weeing", "garden", "beds", "flowerbed", "border")),
    ("They go for bare, dry soil, so take that away: mulch the beds, plant closer together, "
    "and lay short prickle cuttings or a few crossed sticks over newly dug ground. Give them "
    "somewhere better - a patch of gravel or sand out in the open, cleared now and then - "
    "because a cat will keep to one spot if it has it. A motion-triggered water spray "
    "settles the persistent ones, and citrus peel and coffee grounds only work for a few "
    "days."),
    # a tray in the house is a different question, and pets.py answers it
    # An outside place has to be named. That is what keeps a cat doing it *on the bed* or
    # *in the house* out of this answer, and it cannot be done with `avoid`: "beds" is how
    # people say a flower bed, and a form of "bed" in the avoid list zeroed this entry on
    # the very lines it exists for ("next doors cat keeps pooing in my beds"). pets.py
    # answers the tray and the sofa, so the indoor words below are only a second fence.
    # The indoor lines are fenced by phrases, never by the word "bed" on its own: a key
    # word's plural is a form of the singular, so bare "bed" also matched "in my beds",
    # which is how people say a flower bed, and it zeroed this entry on the lines it
    # exists for. Every phrase below needs a word a flower-bed line does not have.
    avoid=("litter tray", "litter", "tray", "indoor", "inside the house", "pregnant",
    # a bed the cat sleeps in is not a flower bed, and "where should i put the cat bed" got the
    # mulch answer because "beds" is a form of "bed". The phrase is the fence: a bare "bed" in
    # this list would zero the row on "next doors cat keeps pooing in my beds".
    "cat bed", "dog bed", "cat basket", "dog basket", "her bed", "his bed",
    "toxoplasmosis", "carpet", "curtains", "indoors", "in the house", "in the flat",
    "sofa", "couch", "next to the tray", "outside the tray",
    # A cat that brings something dead in is hunting, and that is the pet answer, not this
    # one: "my cat keeps leaving dead mice in my bed, how do i stop it" is a hunting line
    # that reached this answer because "beds" is a form of "bed". The prey names are the
    # words a poo-or-digging line never has.
    "mouse", "mice", "rat", "rats", "vole", "voles", "dead mice", "dead bird", "prey",
    "bird", "birds", "pigeon", "pigeons", "brought in", "brings in", "dragged in",
    # "on" and not "in my bed": a key word's plural is a form of the singular, so
    # "in my bed" also matches "in my beds", and that is the pile of soil the person
    # is asking about. On the bed is the tray question; in my beds is the border one.
    "on the bed", "in the bed", "on my bed", "on our bed", "on his bed",
    "on her bed", "bedroom", "duvet",
    # A cat that wets the bed is the vet-and-tray question, and "the bed" here is short of
    # "on the bed": "my cat wet the bed" reached this row on cat + "beds" and got soil
    # advice. The accident words are the fence, and none of them is a flowerbed line.
    "wet the bed", "wets the bed", "wetting the bed", "wet on the bed", "peed", "peed on",
    "peeing", "weed on", "wees on", "wetting",
    # A cat hiding under the bed is not a cat using the border, and "bed" is the word that
    # joined the two: the key's "beds" is a form of "bed", so every bed-hiding line reached
    # this row. The place words and the hiding words name the indoor question whole.
    "under the bed", "under my bed", "under our bed", "under his bed", "under her bed",
    "hides", "hiding", "hiding under", "hides under", "wont come out", "won't come out"),
    # A list of indoor nouns can never be finished - a floor, a hall, "the corner of the
    # room" are all the tray question pets.py answers - so the fence points the other way:
    # the line has to name an outside place. Every garden line does, and no indoor one has
    # to.
    ask=("garden", "gardens", "flower bed", "flower beds", "flowerbed", "flowerbeds",
    "border", "borders", "soil", "mulch", "lawn", "allotment", "beds", "bedding",
    "plants", "plant", "vegetable patch", "veg patch", "dug", "shrub", "shrubs")),

    # A split tomato is a watering problem, and it was reaching no answer at all: "how do i stop my
    # tomatoes splitting" fell through to a planning line.
    entry("tomato-split",
          (("tomato", "tomatoes", "tomato plant", "tomato plants"),
           ("split", "splits", "splitting", "crack", "cracks", "cracking", "cracked", "burst",
            "bursting", "skin", "skins")),
          "Splitting is water, not disease: after a dry spell the roots take up water faster than "
          "the skin can stretch, so the fruit splits, and a heavy feed does the same. Water little "
          "and often at the base so the soil stays evenly damp, mulch to hold that moisture, and "
          "pick the split ones straight away because they rot where the skin is broken. In a wet "
          "spell pick the fruit a little under-ripe rather than leaving it to swell.",
          # the black bottom and the yellow leaf are their own answers
          avoid=("black", "bottom", "bottoms", "blossom end", "rot", "yellow", "yellowing",
                 "leaves", "leaf", "green veins")),
    entry("root-split",
          (("carrot", "carrots", "beetroot", "beetroots", "beet", "parsnip", "parsnips",
            "radish", "radishes", "turnip", "turnips", "swede", "swedes", "celeriac"),
           ("split", "splits", "splitting", "crack", "cracks", "cracking", "cracked", "burst",
            "bursting", "forked", "forking", "woody", "holes", "tunnels",
            # a root that ran to seed is the same problem one stage on: it will not improve
            "bolted", "bolting", "gone to seed", "going to seed", "run to seed", "flowering",
            "flowered", "gone up")),
          _root_split,
          # a carrot that has been eaten into is the pest question, and the knuckle crack is not
          # this at all
          avoid=("knuckle", "knuckles", "joint", "joints", "back", "fingers", "bones",
                 "eaten", "eaten by", "holes in the leaves", "carrot fly", "rust fly"),
          # the line itself has to name the root: reached from the topic carried over from an
          # earlier turn, this row told "how often do i feed tomato plants" when to sow carrots
          ask=("carrot", "carrots", "beetroot", "beet", "parsnip", "parsnips", "radish",
               "radishes", "turnip", "turnips", "swede", "celeriac"),
          bias=2),
    # Running to seed: a lettuce, a spinach or a herb that shoots up a stem has finished. The
    # answer was the flower-and-pollen explainer ("why is my lettuce going to seed") or a recipe
    # ("why has my lettuce bolted"), and the thing to say is what to do this week.
    entry("gone-to-seed",
          (("lettuce", "lettuces", "spinach", "rocket", "chard", "coriander", "cilantro",
            "basil", "parsley", "dill", "kale", "pak choi", "bok choy", "mustard greens",
            "leafy", "herbs", "herb"),
           ("bolted", "bolting", "bolt", "gone to seed", "going to seed", "run to seed",
            "running to seed", "ran to seed", "seeding", "flowering", "flowered", "shooting up",
            "gone up", "tall stem")),
          "Once a lettuce, a spinach or a herb sends up a stem it has run to seed, and the leaves "
          "turn bitter as it does: cut it now and eat what is still good, because it will not come "
          "back into leaf. It happens in heat and long days, so next time pick a slow-bolt variety, "
          "sow so the crop is ready before midsummer or after it, keep it watered, and shade it in "
          "a heatwave. Picking the outer leaves often keeps a plant in leaf longer.",
          # how a flower is pollinated, when to sow, and which pests eat the leaves are other
          # answers, and a bolted lettuce is still worth eating - not this row's question
          avoid=("pollinat", "pollen", "stamen", "stigma", "how do flowers", "how does a flower",
                 "when do i sow", "when should i sow", "what month", "sow", "sowing",
                 "slugs", "snails", "caterpillars", "aphids", "eaten", "recipe", "salad",
                 "how do i cook", "what can i make"),
          # the plant has to be in the line, not only in the topic carried over from before
          ask=("lettuce", "lettuces", "spinach", "rocket", "chard", "coriander", "cilantro",
               "basil", "parsley", "dill", "kale", "pak choi", "bok choy", "herb", "herbs",
               "leafy"),
          bias=1),
    # The June drop, and the tree that lets go of the whole crop. "why are my apples falling off
    # the tree" was answered with how to repaint a damp patch on a wall.
    entry("fruit-drop",
          (("apple", "apples", "apple tree", "pear", "pears", "pear tree", "plum", "plums",
            "cherry", "cherries", "damson", "damsons", "greengage", "fruit tree", "fruit trees"),
           ("dropping", "dropped", "drops", "falling off", "fall off", "fell off", "coming off",
            "falls off", "dropping its fruit", "losing fruit", "losing its fruit", "june drop",
            "dropping fruit")),
          "Fruit that drops in June and early July is the tree thinning its own crop, and it is "
          "normal: it lets go of more than it can carry, and the apples that stay grow bigger for "
          "it. If it is later than that, or the whole crop goes, look at water and pollination "
          "first - a dry spell in summer, a wet cold week when the bees were out, or a heavy pest "
          "year. Water the tree deeply once a week in dry weather, pick up the fallen fruit so "
          "wasps and rot do not move in, and let it drop what it wants.",
          avoid=("phone", "battery", "dropped my", "dropped it", "damp", "wall", "paint",
                 "repaint", "ceiling", "patch", "mould", "mold", "wifi", "signal",
                 "out of the pram", "out of the cot"),
          ask=("apple", "apples", "pear", "pears", "plum", "plums", "cherry", "cherries",
               "damson", "damsons", "greengage", "fruit tree", "fruit trees", "tree",
               "trees"),
          bias=2),
    # "what is compost" and "whats compost made of" were both a search hedge: the garden rows
    # all assume the word is understood, and the bin has its own rows.
    entry("what-is-compost",
          (("compost", "compost heap", "compost pile", "home made compost", "homemade compost"),
           ("what is", "whats", "what are", "made of", "made from", "made up of", "how do i make",
            "how do you make", "how is it made", "how to make", "mean", "explain", "difference")),
          "Compost is plant waste that has rotted down into dark crumbly stuff that smells of "
          "earth: layer green things like grass, peelings and weeds with brown things like "
          "cardboard, dead leaves and twiggy prunings, keep it as damp as a wrung-out sponge, "
          "and turn it now and then. Six months to a year and it is ready to spread on beds or "
          "dig in, and it feeds the soil rather than the plant. Bagged potting compost is a "
          "different thing - sterilised, and made light enough for roots in a pot.",
          # a smelly bin, flies, rats and what the council takes are other questions
          avoid=("bin", "bins", "caddy", "smell", "smells", "smelly", "flies", "fruit flies",
                 "rat", "rats", "maggot", "maggots", "council", "collection", "food waste",
                 "not broken down", "not heating up", "is it ready", "when is it ready",
                 # what to buy or use for a particular plant is the buying question, not this one
                 "best", "which", "buy", "bought", "houseplant", "houseplants", "potting",
                 "seed", "seeds", "seedling", "seedlings", "multipurpose", "peat", "drainage",
                 "for pots", "in a pot", "for cuttings", "for a lawn", "for the lawn"),
          bias=1),
    entry("easy-houseplants",
          (("houseplants", "house plants", "house plant", "houseplant", "indoor plants",
            "indoor plant", "plant", "plants"),
           # "keep" is not here: it was, and "my houseplants keep dying" is the commonest way
           # someone asks why their plants die - the easy-plants list is an answer to a
           # different question, and it was standing in front of the dying answer. A line that
           # wants plants to keep has "alive", "easy" or "hard to kill" in it.
           ("easy", "easiest", "hard to kill", "kill", "beginner", "beginners", "forgiving",
            "neglect", "unkillable", "simple", "recommend", "start", "alive")),
          "Spider plant, snake plant, pothos and the ZZ plant are the ones to start with: they take "
          "low light, a missed watering and a radiator, and still look fine. Water them when the "
          "compost is dry rather than on a schedule, keep them out of the hottest sun, and they will "
          "outlive the ones that want fussing.",
          # A named plant is its own entry in this file, and these four are houseplants: the
          # same four are a confident wrong answer to "what should i plant in my garden".
          avoid=("monstera", "orchid", "orchids", "fern", "ferns", "cactus", "cacti",
                 "succulent", "succulents", "peace lily", "aloe", "basil", "fiddle leaf",
                 "calathea", "jade plant", "rubber plant", "spider plant", "snake plant",
                 "pothos", "zz plant", "garden", "gardens", "border", "borders", "allotment",
                 "vegetable", "veg", "flower bed", "beds", "lawn", "outside", "outdoors",
                 "shrub", "shrubs", "tree", "trees",
                 # a plant that repels an insect, or one to grow from seed, is another question
                 "mosquito", "mosquitoes", "mosquitos", "insect", "insects", "pest", "pests",
                 "bug", "bugs", "repel", "repels", "keep away", "keep mosquitoes",
                 # "planting" is left out: it stems to "plant", which every line here has
                 "seed", "seeds", "sow", "sowing", "sowed", "from seed", "sow seeds",
                 "propagate", "propagation", "cutting", "cuttings")),
    entry("plant-dying",
          (("plant", "plants", "houseplant", "houseplants", "house plant", "house plants"),
           ("dying", "died", "drooping", "droopy", "wilted", "wilting", "limp", "sick", "wrong",
            "revive", "save", "alive", "stop", "failing", "looks bad", "not doing well")),
          "Feel the compost first: wet and smelly means too much water, so stop watering, let it "
          "drain and repot in fresh compost if the roots are brown and soft. Bone dry and light "
          "means the opposite, so soak the whole pot in a bowl for ten minutes. If it is neither, "
          "check the light and look under the leaves for tiny insects, and give it a few weeks "
          "before changing anything else: plants sulk slowly and recover slowly.",
          # a named plant has its own entry
          # a plant caught by a cold night is the frost row's: "how do i stop frost damage to
          # plants" was this answer, which is about water and light and never mentions cold
          avoid=("frost", "frosts", "frosty", "freezing", "frozen", "cold snap", "cold night",
                 "cold nights", "sub zero",
                 "monstera", "orchid", "orchids", "fern", "ferns", "cactus", "cacti",
                 "succulent", "succulents", "peace lily", "aloe", "basil", "fiddle leaf",
                 "calathea", "jade plant", "rubber plant", "spider plant", "snake plant",
                 "pothos", "zz plant", "tomato", "tomatoes", "lawn", "grass", "hedge",
                 "hydrangea")),


    # --- the plants indoors: the symptoms the pot itself shows --------------------------------
    # A houseplant is not a border plant: it cannot go and find water or light, so almost every
    # symptom at home is one of three things - too wet, too dark, or the air too dry. Keyed on the
    # symptom and not the species, because people name the symptom far more often than the plant.
    entry("leaf-drop",
          (("dropping leaves", "dropped leaves", "dropped its leaves", "losing leaves", "losing its leaves",
            "leaves dropping", "leaves falling off", "leaves falling", "leaves dropping off",
            "shedding leaves", "lost its leaves"),
           ("dropping", "falling", "dropped", "shedding"),
           ("plant", "houseplant", "house plant", "indoor", "pot", "monstera", "peace lily",
            "ficus", "rubber plant", "pothos", "succulent", "cactus", "orchid", "palm",
            "dracaena", "calathea", "fern")),
          # water first: it is the commonest cause, and a plant in soggy compost that gets moved
          # about to dry off loses leaves both ways
          ("Leaves dropping off a houseplant is usually too much water: compost that has stayed wet "
           "for a week or more, or a saucer left standing full. Feel the compost - wet means no "
           "water for a fortnight, dry means a good soak and a pot that drains. Otherwise it is "
           "reacting to a change, cold from a window or a move to a new spot: leave it where it is "
           "for a month, since moving it about is what keeps it dropping."),
          # a plant that drops its flowers or buds is asked about flowering, and orchid-reflower
          # has that answer: "my orchid dropped its flowers" was getting the leaves paragraph
          avoid=("autumn", "tree", "trees", "outside", "garden", "lawn", "tomato", "bee",
                 "bees", "caterpillar", "deer", "sheep", "hedge", "shrub", "allotment",
                 "flower", "flowers", "flowering", "bloom", "blooms", "bud", "buds",
                 # a bonsai is a named tree in a pot and has its own entry: "my bonsai is
                 # dropping leaves" is the water and light of that tree, not the houseplant
                 # paragraph this row gives to an unnamed one
                 "bonsai", "bonsais", "money tree", "juniper", "maples"),
          ask=INDOORS,
        ),

    entry("fungus-gnats",
          (("little black flies", "little flies", "tiny flies", "tiny black flies", "small black flies",
            "black flies", "fungus gnats", "gnats", "flies round my plant", "flies around my plant",
            "flies in my plant", "flies in the compost", "flies round the plant"),
           # "black" alone, with "pot", took "the bottom of my pot is black and burnt" away from
           # the burnt pan; the phrases above already carry the colour
           ("flies", "fly", "gnats", "tiny"),
           ("plant", "plants", "houseplant", "house plant", "pot", "pots", "compost", "soil",
            "potting", "indoor", "room", "windowsill", "kitchen windowsill")),
          ("Those little black flies are fungus gnats, and they are breeding in wet compost rather "
           "than eating the plant. Let the top 2-3cm dry right out between waterings, water from "
           "the bottom for a few weeks, and stand a yellow sticky trap in the pot; a layer of grit "
           "or sand on the surface stops them laying more. They are harmless to people and rarely "
           "kill a plant."),
          avoid=("fruit flies", "fruit fly", "bin", "drain", "kitchen sink", "sink", "wine",
                 "vinegar", "food waste", "caddy", "midge", "midges", "mosquito", "bite",
                 "bites", "sting", "wasps"),
          ask=INDOORS,
        ),

    entry("soil-mould",
          (("white mould", "white mold", "mould on the soil", "mould on the compost",
            "mould on top", "furry mould", "grey mould", "white stuff on the soil",
            "mould in the pot", "going mouldy", "gone mouldy", "mouldy", "moldy",
            "mouldy soil", "mouldy compost", "mouldy pot", "plant pot mouldy",
            "mould in my pot", "mould on the surface", "green mould", "algae", "slimy soil",
            # "how do i get rid of mould in a plant pot" is the same question as "mould on the
            # soil" and was a pair of football boots: no phrase of this key matched it, so the
            # row never proposed and "moulded" carried the boot row instead.
            "mould in a plant pot", "mould in a pot", "mould in my plant pot",
            "mould on a plant pot", "mould on my plant pot", "mould in the plant pot",
            "mould in the soil", "mould in the compost", "get rid of mould",
            "get rid of the mould", "mould in my soil"),
           ("mould", "mold", "white", "furry"),
           ("plant", "soil", "compost", "pot", "houseplant", "house plant", "indoor",
            "potting", "seedling", "seedlings")),
          ("White furry mould on the top of the compost is harmless: it is feeding on dead bits in "
           "compost that has stayed wet in still air. Scrape it off, water only when the top of the "
           "compost is dry, empty the saucer, and give the room some air - the plant does not need "
           "repotting."),
          avoid=("bread", "wall", "walls", "bathroom", "shower", "ceiling", "window", "grout",
                 "tile", "tiles", "cheese", "jam", "fridge", "food", "clothes", "washing",
                 "damp", "mushroom", "mushrooms",
                 # A seedling tray is the one place white mould is not harmless: damping off
                 # collapses the seedling at soil level, and that row says so. Measured on main
                 # f7fe9dda1: "my seedling compost is mouldy" was the damping-off answer and this
                 # row took it while "seedling" stood in its key.
                 "damping off", "damping", "collapsed", "collapsing", "collapses",
                 "pinched off", "pinched at", "thin stem", "stem has gone thin",
                 "fell over", "fallen over", "keeled over", "toppled",
                 # and a pot of food is not a pot of compost: "my pot of curry went mouldy" is the
                 # gone-off answer, which bins it, and this row told the person to scrape the top
                 # off and water less. Found by a reviewer, not by my own probe, because my probe
                 # had "my soup has mould on it" and no line with "pot" in it.
                 "curry", "stew", "soup", "sauce", "rice", "pasta", "noodles", "risotto",
                 "casserole", "chilli", "chili", "broth", "gravy", "bolognese", "cooked",
                 "leftovers", "leftover", "takeaway", "slow cooker", "jam", "yoghurt", "yogurt"),
          ask=INDOORS,
        ),

    entry("spider-mites",
          (("spider mites", "spider mite", "fine webs", "tiny webs", "webbing", "little webs",
            "spider webs", "webs on the plant", "webs on my plant", "cobwebs on", "white speckles",
            "speckled leaves", "stippled leaves", "dusty leaves"),
           ("webs", "webbing", "mites", "speckled", "speckles", "stippled", "dusty"),
           ("plant", "leaves", "leaf", "houseplant", "house plant", "indoor", "pot", "underside",
            "under the leaves", "monstera", "palm", "calathea", "ficus", "fern", "schefflera",
            "ivy")),
          ("Fine webbing and leaves that look speckled and dusty mean spider mites, which thrive in "
           "hot, dry air. Take the plant to the sink or shower and wash both sides of every leaf, "
           "raise the humidity around it - group it with other plants, or stand the pot on a tray "
           "of wet pebbles - and wash it again every three or four days for a fortnight, because "
           "the eggs hatch in between. A plant that is badly covered is better thrown out than "
           "fought for."),
          # "spider" itself stays out of the avoid: it is half of "spider webs on my plant", which
          # is this entry's own question. The spiders people ask about are named instead.
          avoid=("house spider", "cellar spider", "garden spider", "false widow", "spider bite",
                 "spiders in the", "big spider", "bathroom", "shed", "bite", "bites"),
          ask=INDOORS,
        ),

    entry("leggy-growth",
          (("gone leggy", "leggy", "tall and thin", "thin and straggly", "straggly", "spindly",
            "stretched out", "all stem"),
           ("leggy", "spindly", "straggly", "thin", "stretched"),
           ("plant", "houseplant", "house plant", "indoor", "leaves", "stems", "pot", "windowsill",
            "geranium", "pelargonium", "basil", "mint", "succulent")),
          ("A plant that has gone tall, thin and stretched is short of light, not ill: it is "
           "reaching for the window. Move it nearer the light and turn it a quarter turn each week "
           "so it grows evenly, then cut the straggly stems back by half - most houseplants send "
           "out two shoots from the cut, and the pieces you cut off will root in a glass of water."),
          ask=INDOORS,
        ),

    entry("orchid-water",
          (("orchid", "orchids", "moth orchid", "phalaenopsis"),
           ("water", "watering", "how often", "ice", "ice cubes", "roots", "bark", "soak",
            "droop", "drooping", "dying", "root rot", "shrivel", "wrinkled")),
          ("Water an orchid by soaking it: once a week, stand the pot in tepid water for ten "
           "minutes, let it drain right through, and put it back - never leave it standing in "
           "water, which rots the roots. They come in bark chips and a clear pot so you can see the "
           "roots: silvery-grey wants water, green is fine. Ignore the ice-cube trick; cold water "
           "on tropical roots does them no good."),
          # "how often do i water an orchid" is also a watering question, and the general
          # houseplant answer (top two centimetres dry) is wrong for bark and a clear pot
          ask=("water", "watering", "how often", "soak", "ice", "roots", "bark"),
          bias=2,
          avoid=("buy", "gift", "present", "flower shop", "wedding", "corsage")),

    # "how do i look after a bonsai" was an honest pass. A bonsai is not a species: it is an
    # ordinary tree kept small, so the answer is about water, position and the trim, and the
    # houseplant rows do not cover it.
    entry("plant-bonsai",
          (("bonsai", "bonsais", "bonsai tree"),
           ("water", "watering", "how often", "care", "care for", "look after", "keep alive",
            "feed", "trim", "prune", "outside", "indoors", "inside", "pot", "soil", "dying",
            "brown", "leaves", "winter", "beginner", "start", "buy")),
          ("Most bonsai are outdoor trees kept small, so keep it outside - a windowsill indoors is "
           "usually too dry and too warm. Water when the top of the soil is starting to dry, which "
           "is most days in summer and every few days in winter: soak it until water runs out of "
           "the holes, then let it drain. Feed every two weeks in the growing season, trim the "
           "shoots back to two leaves, and give it a cool frost-free spot in winter. Only a "
           "tropical one such as ficus stays indoors."),
          avoid=("buy one", "gift", "present", "price", "cost", "to buy")),

    entry("orchid-reflower",
          (("orchid", "orchids", "moth orchid", "phalaenopsis"),
           ("flowers", "flower", "flowering", "reflower", "rebloom", "bloom", "spike", "buds",
            "bud", "dropped", "lost", "die", "died", "not flowering", "again")),
          ("An orchid drops its flowers when that show is over, not because it is dying: cut the "
           "bare spike an inch above the second node, keep it in bright light out of direct sun, "
           "and give it cooler nights - around 16 to 18C - because the drop in temperature is what "
           "sets new buds. It usually takes a couple of months, and the old spike left on often "
           "flowers again from the same stem."),
          # an orchid that has finished flowering is asked about flowering again, and that is a
          # more specific answer than the general one; the two tie on the words otherwise
          bias=1, avoid=("buy", "gift", "present", "flower shop", "wedding")),

    # A dropped pot is its own question, and it had no answer: with the flower row fenced off, "i
    # dropped my plant pot" fell to the soil row, whose key word "potting" is a loose form of
    # "pot", and got how soil holds a plant up. Somebody holding a plant that has just fallen out
    # of its pot wants the next ten minutes, not a fact about minerals. A cracked pot, which is
    # what people say on the next turn, is the same row.
    entry("plant-pot-dropped",
          (("plant pot", "plant pots", "pot", "pots", "plant", "plants", "houseplant",
            "houseplants", "house plant", "indoor plant", "indoor plants", "windowsill",
            "compost", "soil", "potted plant", "root ball", "roots", "cutting"),
           ("dropped", "drop", "drops", "dropping", "fell", "fallen", "falls", "knocked",
            "knock", "knocked over", "tipped", "tipped over", "broke", "broken", "cracked",
            "cracks", "smashed", "shattered", "spilled", "spilt", "upside down", "on its side")),
          ("Sooner is better than tidy: lift the plant by its base rather than by the stem, keep as "
           "much of the root ball as will hold together, and shake off only the compost that has "
           "already come loose. Stand it in fresh compost in a pot with drainage holes - the same "
           "size or one up, never a big jump - firm the compost round the roots, water until it "
           "runs out of the bottom, and keep it out of direct sun for a week. White firm roots are "
           "fine and brown mushy ones can be trimmed off. A cracked pot will hold for a while, but "
           "slip it inside another pot or repot it, because a break under the rim gives way all at "
           "once."),
          # A pot that has been dropped, cracked or knocked over is this row's line, and the
          # fall words alone are not: "my plant keeps falling over", "why do my plants fall over"
          # and "my plant is too tall and keeps falling over" are a plant that is top heavy for
          # want of light and a bigger pot, and the standing-things row in science.py answers
          # them ("A houseplant flops over for one of three reasons"). Without this ask the fall
          # word took every one of those to how to lift a plant out of a pot - measured on
          # `3ae8d520`, five lines moved and nothing else moved.
          ask=("pot", "pots", "plant pot", "plant pots", "root ball", "compost", "soil",
               "out of its pot", "out of the pot", "cracked", "crack", "smashed", "shattered",
               "broken", "broke", "on its side", "upside down", "knocked", "knock",
               "dropped it", "dropped my plant", "dropped the plant", "dropped a plant",
               "dropped mine", "off the shelf", "off the windowsill", "off the table",
               "off the sill",
               # a pot that has already gone over: "my plant tipped over" is that pot, and
               # "why does my plant tip over" is the standing-things row's question, so the
               # past forms are here and the bare verb is not
               "tipped", "tipped over", "went over", "gone over", "went flying"),
          bias=2,
          # A pot of soup that fell off the hob is the kitchen's, and a plant that shed its flowers
          # or its leaves has its own answer: the fall words alone do not make this the pot row.
          avoid=("soup", "stew", "stock", "casserole", "saucepan", "pan", "rice", "pasta",
                 "boil", "boiled", "boiling", "cook", "cooking", "cooked", "kitchen", "hob",
                 "oven", "slow cooker", "pressure cooker", "chilli", "curry", "tea", "coffee",
                 "paint", "flower", "flowers", "bud", "buds", "bloom", "blooms", "petal",
                 "petals", "leaves", "leaf", "yellow", "yellowing", "drooping", "wilting",
                 "wilt", "brown")),

    entry("plant-dropping-its-flowers",
          (("houseplant", "house plant", "houseplants", "house plants", "peace lily",
            "peace lilies", "african violet", "african violets", "hoya", "cyclamen",
            "christmas cactus", "kalanchoe", "anthurium", "begonia", "fuchsia", "plant",
            "plants", "indoor plant", "indoor plants"),
           # The loss words alone, not phrases: "dropping its flowers" needs the possessive, so
           # "the flowers fell off my houseplant", "my plant lost all its flowers" and "my plant
           # is dropping flowers" all missed the row and the not-flowering row is stood down on
           # the same lines, so they fell through to a filler or the planting list.
           # The plant noun in group one is the gate that keeps "the boiler dropped" out.
           ("dropping", "dropped", "drops", "drop", "losing", "lost", "lose", "falling",
            "fallen", "fell", "shedding", "shed", "losing", "bare")),
          ("A houseplant drops its open flowers when that flush is simply over, and nothing needs "
           "doing beyond cutting the spent stems back to a leaf so the plant puts its energy into "
           "leaves and roots instead. Buds that drop before they open are a different thing: that "
           "is the plant shedding what it cannot hold, and it is usually one of four shocks - moved "
           "to a darker or draughtier spot, dried out or left standing in water, a sudden cold "
           "night by a window, or a bowl of ripening fruit nearby, whose ethylene makes buds fall. "
           "Pick one thing, put it right, and give it two or three weeks before changing anything "
           "else."),
          # The loss is not the same question as "will not flower": a peace lily that is dropping
          # the flowers it had was told to give it more light and a tomato feed, which is the
          # answer for a plant that has never flowered at all. The orchid keeps its own card.
          avoid=("orchid", "orchids", "moth orchid", "phalaenopsis", "outside", "garden",
                 "border", "lawn", "allotment", "veg patch", "vegetable", "tree", "trees",
                 # the crops have their own drop answers ("a chilli drops its flowers for one
                 # of three reasons"), and a bare "plant" in this row's key took them
                 "tomato", "tomatoes", "courgette", "courgettes", "strawberry", "strawberries",
                 "chilli", "chillies", "chili", "pepper", "peppers", "cucumber", "cucumbers",
                 "squash", "pumpkin", "pumpkins", "marrow", "aubergine", "aubergines",
                 "eggplant", "peas", "beans", "runner", "broad bean", "broad",
                 # a plant losing its leaves is not a plant losing its flowers
                 "leaves", "leaf", "yellow", "yellowing", "drooping", "wilting", "wilt",
                 "brown tips", "brown", "tips", "spotted", "mould", "mold",
                 "buy", "gift", "present", "shop", "wedding", "funeral", "cut flowers"),
          # The plant noun in group one is not enough of a gate: "i dropped my plant pot", "my
          # plant fell off the windowsill" and "i dropped the plant" are a dropped pot, a fall and
          # a knock, and all three were answered with how a plant sheds its flowers. What has to
          # be on the line is the thing lost: a flower, a bud, a petal, a bloom.
          #
          # "bare" and "shed" are not that thing on their own. "My plant is bare in the middle"
          # is a plant that is bare of leaves, and "my houseplant has bare stems" is a plant that
          # wants light and a cut back; the row below answers both, and both were being told to
          # cut back the spent flower stems.
          ask=("flower", "flowers", "flowering", "bloom", "blooms", "blooming", "blossom",
               "blossoms", "blossoming", "bud", "buds", "petal", "petals", "spike", "spikes"),
          bias=2),

    entry("houseplant-bare-at-the-bottom",
          (("houseplant", "house plant", "houseplants", "house plants", "indoor plant",
            "indoor plants", "plant", "plants", "geranium", "geraniums", "pelargonium",
            "pothos", "spider plant", "trailing plant", "palm", "fern",
            # a lily that is bare in the middle was the flowers card, and the plant is named
            "lily", "lilies", "peace lily", "peace lilies"),
           # The bare middle is one question however it is said: a joint that is "bare",
           # "leggy", "spindly", or that has "lost" its lower leaves, says the same thing.
           ("bare", "leggy", "spindly", "straggly", "skinny", "lost", "losing", "dropped",
            "dropping", "gone", "going", "no leaves", "nothing on", "stems with no",
            # the same plant from the other end: too tall, stretched, long and thin, bushy,
            # and the question of cutting it back
            "too tall", "long and thin", "thin and long", "tall and thin", "stretched",
            "stretching", "etiolated", "bushy", "cut back", "cut it back", "trim it back",
            "prune")),
          ("A plant that is bare at the bottom, or long and thin instead of bushy, is short of "
           "light: the leaves at the top are the ones getting it and the stems below have dropped "
           "theirs for want of it. Move it nearer a window out of direct midday sun, turn it a "
           "quarter turn each week so it grows evenly, and in spring cut the long leafless stems "
           "back by about a third - new shoots come from the joints just below the cut, and bare "
           "stems will not leaf up again on their own. To make it bush rather than climb, pinch out "
           "the top pair of leaves every few weeks. If it needs to be smaller, take a cutting from "
           "the top first."),
          # The flower rows own the flowering: "my peace lily is bare in the middle" is this
          # plant, but "my plant is bare of flowers" is theirs, since a flowerless plant is not a
          # leggy one.
          avoid=("flower", "flowers", "flowering", "bloom", "blooms", "blossom", "bud", "buds",
                 # an orchid and a Christmas cactus have their own cards, and so does a plant
                 # losing its leaves for another reason - yellow, brown, spots, wilting
                 "orchid", "orchids", "moth orchid", "phalaenopsis", "christmas cactus",
                 "yellow", "yellowing", "brown", "spots", "spotted", "mould", "mold",
                 "drooping", "wilting", "wilt", "limp",
                 # and the crops have their own answers, as does anything outside
                 "tomato", "tomatoes", "cucumber", "cucumbers", "courgette", "courgettes",
                 "chilli", "chillies", "chili", "pepper", "peppers", "strawberry",
                 "strawberries", "pea", "peas", "bean", "beans", "outside", "garden", "border",
                 "lawn", "allotment", "veg patch", "vegetable", "tree", "trees", "shrub",
                 "shrubs", "hedge", "compost", "cut flowers"),
          guard=_the_stems_are_what_is_bare,
          bias=1),

    entry("houseplant-feed",
          (("plant food", "fertiliser", "fertilizer", "feed", "feeding", "plant feed"),
           ("feed", "feeding", "fertiliser", "fertilizer", "food"),
           # no "how often" or "when" here: with "feed" they made "how often should i feed my dog"
           # a houseplant question. A plant word is what makes it one.
           ("houseplant", "houseplants", "house plant", "house plants", "indoor", "pot", "pots",
            "plants", "winter", "growing")),
          ("Feed houseplants from March to September, about once a month at half the strength on "
           "the bottle, and not at all in winter: most of them stop growing then, and the food just "
           "builds up in the compost. Fresh compost feeds a plant for the first couple of months, "
           "so nothing is needed after repotting."),
          # In a conversation the plant word can come from the turn before ("should i feed them"
          # after a tomato question), and the feeding of an outdoor crop is its own answer
          avoid=("tomato", "tomatoes", "cucumber", "courgette", "pepper", "chilli", "lawn",
                 "grass", "rose", "roses", "vegetable", "allotment", "outside", "garden bed",
                 "crop", "dog", "cat", "baby",
                 # a bird is fed outside, not in a pot: "what should i feed the birds in winter"
                 # was answered with houseplant feed
                 "bird", "birds", "feeder", "feeders", "bird food", "bird table", "squirrel",
                 "squirrels", "hedgehog", "hedgehogs", "fox", "foxes", "wildlife",
                 # How a plant makes its own food is photosynthesis, not feeding: "how do plants
                 # make food" was this entry, because "food" is in the second part and the plant
                 # word in the third, and a feeding does not talk about sunlight or carbon dioxide.
                 "photosynthesis", "make food", "makes food", "made food", "make their food",
                 "make their own food", "make its own food", "own food", "their food",
                 "get food", "gets food", "get energy", "feed themselves", "carbon dioxide",
                 "chlorophyll", "sunlight", "oxygen")),

    entry("misting",
          (("misting", "mist my", "mist the", "should i mist", "mist them"),
           ("mist", "misting", "misted"),
           ("plant", "plants", "houseplant", "houseplants", "leaves", "fern", "calathea", "orchid",
            "humidity")),
          ("Misting does very little: it lifts the humidity for a few minutes and does not fix "
           "brown tips or stop a plant crisping. For a fern or a calathea, group it with other "
           "plants, keep it out of draughts and stand the pot on a tray of wet pebbles that the "
           "water can evaporate from; for anything else, the odd mist is mostly for you."),
          ask=INDOORS,
        ),

    entry("leaf-spots",
          (("spots on the leaves", "brown spots", "black spots", "leaf spots", "spots on my plant",
            "spotted leaves", "patches on the leaves"),
           ("spots", "spot", "spots on", "patches"),
           ("leaves", "leaf", "plant", "houseplant", "house plant", "indoor", "pot", "monstera",
            "peace lily", "pothos", "fern", "palm", "calathea", "ficus", "dracaena")),
          ("Round brown or black spots on the leaves are usually a fungus getting in where the leaf "
           "stayed wet. Take off the worst leaves and stop misting and splashing the leaves; water "
           "the compost instead, in the morning, and give the plant more air. If the spots are soft, "
           "spreading fast, or there is a smell, take it out of the room - rot in a stem does not "
           "come back."),
          avoid=("tomato", "tomatoes", "potato", "rose", "roses", "lawn", "grass", "garden",
                 "apple", "skin", "face", "child", "dog", "cat", "mole", "moles", "spot cream",
                 "sunspot", "age spot"),
          ask=INDOORS,
          # A plant's own spot question, and it used to win this on the word "spots" being rare.
          # The blight row now asks for "spots on the leaves" too, so "my plant has white spots"
          # came back to the compost mould; the bias puts the leaf answer back in front, which is
          # where main had it.
          bias=1,
        ),

    entry("not-flowering",
          (("not flowering", "isnt flowering", "isn't flowering", "never flowers", "never flower",
            "no flowers", "wont flower", "won't flower", "no buds", "not bloomed", "isnt blooming",
            "stopped flowering", "flower again",
            # "how do i get my cactus to flower" and "...snake plant to flower" ask for the same
            # thing without the word "again" or a negative, and reached nothing: the plant's own
            # row only knows how often to water it.
            "to flower", "to bloom", "get it to flower", "flowering", "blooming"),
           # "flowers" alone is what an orchid that has finished its show is asked with, and that
           # has its own answer (orchid-reflower), so the bare word is not enough here.
           # "flowering" and "blooming" stay in the group above as well: keys match a word family,
           # so they are also how "how do i make my cactus flower" and "why wont my orchid flower"
           # reach this row, and taking them out sent both to a punt and to the orchid-dropped
           # card. A plant that has dropped the flowers it had is stood down by the avoid list
           # below instead, which is the narrower fence.
           ("flowering", "blooming", "bloom", "buds", "bud", "again", "reflower"),
           ("plant", "houseplant", "house plant", "indoor", "peace lily", "orchid", "cactus",
           "christmas cactus", "hoya", "amaryllis", "cyclamen", "african violet", "pot")),
          ("A houseplant that will not flower is usually short of light or being fed too much: "
           "most of them need a bright spot with a few hours of sun a day to set buds, and a feed "
           "high in nitrogen grows leaves at the flowers' expense, so switch to a tomato feed with "
           "more potash in late summer. Peace lilies and Christmas cacti also want cooler nights "
           "and a slightly pot-bound root to be nudged into flower; African violets want the light "
           "and nothing else changed."),
          # Losing the flowers it had is the opposite problem to not flowering, and the verb is
          # the signal, not the phrase: "my orchid is losing its flowers", "...dropped all its
          # flowers" and "...the flowers have fallen off" all want the orchid's own answer, while
          # "how do i make my cactus flower" and "why wont my orchid flower" do not have a loss
          # in them at all. An avoid word is matched by word family, so one of each is enough.
          avoid=("dropped", "dropping", "losing", "lost", "fallen", "falling", "fell",
                 "outside", "garden", "border", "lawn", "tree", "bulbs", "daffodil", "tulip",
                 # a bed or a border is outdoors, so a plant in one is not a houseplant that has
                 # stopped flowering: "how do i plant flowers in a shady bed" was this answer
                 "bed", "beds", "flower bed", "flowerbed", "planting flowers", "plant flowers",
                 "allotment", "veg patch", "vegetable patch", "outdoors",
                 "cherry", "fruit tree", "allotment", "vegetable", "wedding", "funeral",
                 # a crop that flowers and sets nothing is not a houseplant sulking, and
                 # "my tomato plants have no flowers" was answered with the light-and-feed
                 # houseplant paragraph because both rows scored the same
                 "tomato", "tomatoes", "tomato plants", "courgette", "courgettes", "squash",
                 "pumpkin", "cucumber", "cucumbers", "runner bean", "runner beans", "beans",
                 "broad beans", "french beans", "strawberry", "strawberries", "chilli",
                 "chillies", "pepper plants", "aubergine", "aubergines", "veg patch",
                 # a bunch of flowers is a present, not a plant that will not bloom: "should i
                 # get her flowers or a plant" is the gift answer's line
                 "gift", "present", "buy her", "get her", "for her", "for my mum", "for my wife",
                 "bouquet", "anniversary", "birthday", "valentine", "mothers day", "mother's day",
                 "flowers or a plant", "flowers or plant"),
          ask=INDOORS,
        ),


    entry("sour-compost",
          (("pot smells", "smells in the pot", "smelly compost", "sour smell", "smells sour",
            "smells of sewage", "smells rotten", "stinks", "smelly soil", "mouldy smell",
            "bad smell from the pot"),
           ("smells", "smell", "smelly", "stinks", "stink", "sour", "rotten", "sewage",
            "mouldy"),
           ("plant", "pot", "compost", "soil", "houseplant", "house plant", "indoor", "roots",
           "watered")),
          ("A pot that smells sour or of drains is waterlogged compost going anaerobic, and the "
           "roots are already suffering: stop watering, tip out any water in the saucer, and let "
           "it dry out for a week or two. If the smell stays, take the plant out, cut away any "
           "roots that are brown and mushy, and repot it in fresh compost in a pot with holes."),
          avoid=("bin", "kitchen", "sink", "drain", "dishwasher", "washing machine", "fridge",
                 "nappy", "baby", "dog", "cat", "toilet", "room", "house", "flat", "car",
                 "fridge", "freezer", "feet", "breath", "mouth"),
          ask=INDOORS,
        ),
    # Three garden plans nobody had an answer for: what to put in a small space, how to plant a
    # basket, and how to build a raised bed. Each was a shrug, and the raised bed was worse than a
    # shrug - "how do i make a raised bed" was answered with a fitted sheet on a mattress.
    entry("small-garden",
          (("small garden", "small gardens", "tiny garden", "little garden", "patio garden",
            "courtyard garden", "small space", "small plot", "small veg patch", "little plot",
            # A balcony and a row of pots are the small space most people who ask this actually
            # have: "what can i grow on a balcony" and "what can i grow in containers" were both
            # a punt, and the answer is the same list with the pots named. "windowsill" is
            # deliberately not here: most windowsill lines are an indoor plant's health ("my
            # plant has yellow leaves" then "it sits on a north facing windowsill"), and that is
            # the house-plant answer's turn, not this one's.
            "balcony", "balconies", "window box", "windowbox", "container", "containers",
            "grow bag", "grow bags", "roof terrace", "yard"),
           ("what can i grow", "grow", "plant", "ideas", "best crops", "what to grow",
            "in a small", "worth growing", "start with", "beginner",
            # A balcony is asked twice: what to grow on it, and then which way it faces. The
            # second turn is the same list thinned by the sun, so it keeps this card rather than
            # falling to a floor line. "north facing" is not here - that is an indoor plant's
            # window, which is the house-plant card's turn.
            "south facing", "sunny", "sun", "windy", "wind", "sheltered")),
          "Grow what gives you a lot from a little: salad leaves, radishes, spring onions, dwarf "
          "beans, cherry tomatoes, chillies, one courgette plant, herbs in a pot by the door, and "
          "strawberries in a basket. Go upwards where you can - beans and cucumbers up a frame, "
          "tomatoes in a grow bag - and sow a few seeds every three weeks rather than everything "
          "at once, so you eat from June to October instead of facing a glut in August. On a "
          "balcony, weight the pots, keep the tall things against the wall out of the wind, and "
          "follow the sun before you buy: a south or west wall grows tomatoes and herbs, a north "
          "one wants leaves, mint and ferns.",
          # a small garden is also asked as a lawn, a fence and a shed, and those are other
          # answers
          avoid=("lawn", "grass", "mow", "fence", "shed", "decking", "patio clean", "pressure",
                 "wash", "paint", "design", "landscap", "astroturf", "artificial",
                 # a line that names its crop wants that crop's own row: "how do i grow tomatoes
                 # in a small garden" is a tomato question before it is a small-garden one
                 "tomato", "tomatoes", "potato", "potatoes", "courgette", "courgettes",
                 "zucchini", "bean", "beans", "chilli", "chillies", "pepper", "peppers",
                 "strawberry", "strawberries", "herb", "herbs", "spinach", "rocket",
                 "lettuce", "salad", "carrot", "carrots", "onion", "onions", "pea", "peas",
                 "cucumber", "cucumbers", "kale", "cabbage", "broccoli", "beetroot",
                 "radish", "radishes", "pumpkin", "squash", "rhubarb", "garlic", "leek",
                 "leeks", "parsnip", "chard", "celery", "aubergine", "sweetcorn", "corn",
                 # a tree is not one of the crops a small garden gives you a lot of, and "plant"
                 # is in this key: "how do i plant a tree in a small garden" was told to grow
                 # radishes.
                 "tree", "trees", "apple tree", "shrub", "shrubs", "hedge", "hedges",
                 "climber", "climbers", "fruit tree")),
    entry("hanging-basket",
          (("hanging basket", "hanging baskets", "hanging basket plants", "basket plants"),
           ("how", "plant", "fill", "what to plant", "which plants", "look after", "water",
            "watering", "best", "keep", "dying", "dead", "liners", "line", "put",
            "what to put", "go in", "look good", "plant up", "planting up")),
          "Line it with a coco mat, or a bin bag with a few holes punched in the bottom, and use a "
          "compost that holds water. In a 30cm basket put four or five plants: something upright in "
          "the middle and trailing lobelia, petunia, bidens or trailing begonia round the edge. "
          "Water it every day in summer and twice on hot days, because a basket dries out faster "
          "than anything in the ground, and feed it with tomato feed every fortnight until "
          "September.",
          # "basket" is in this row's own key, so the shopping words are the ones that take a
          # line out of the garden
          avoid=("hamper", "gift", "wicker", "laundry", "shopping", "easter",
                 # the wintering line is the row below: a planting question should not end on
                 # what to do in November, which made the good planting answer a sentence long
                 "winter", "winters", "wintering", "overwinter", "overwintering", "frost",
                 "first frost", "keep it over", "keep them over", "next year")),
    # A basket is not winter-proof, and "how do i winter my hanging baskets" was answered with
    # how to plant one, because both are the same basket. The two are separate jobs: planting is
    # March and wintering is October, so the wintering words get their own row.
    entry("hanging-basket-winter",
          (("hanging basket", "hanging baskets", "basket", "baskets"),
           ("winter", "winters", "wintering", "overwinter", "overwintering", "frost",
            "first frost", "keep over", "keep it over", "keep them over", "die off", "dies off",
            "next year", "autumn", "october", "november")),
          "Cut it back and stop feeding, then move it against a wall out of the worst of the "
          "frost: most summer bedding will not come back, so a spring refill is the honest plan. "
          "Empty a basket you are leaving out and stand it dry, or the compost freezes solid and "
          "cracks the liner.",
          # a washing basket, a shopping basket and an Easter basket are not plants
          avoid=("hamper", "gift", "wicker", "laundry", "shopping", "easter", "washing basket",
                 "clothes", "fruit")),
    entry("raised-bed",
          (("raised bed", "raised beds", "raised bed kit", "raised planter", "raised vegetable bed",
            "raised beds for vegetables"),
           ("how", "build", "make", "fill", "depth", "how deep", "what soil", "line", "should i",
            "cheap", "best wood", "size", "how high",
            # The same box is asked about five ways and the row only answered two of them: on
            # main `367a0236` "what do i put in the bottom of a raised bed", "how do i fill a
            # raised bed cheaply" and "what can i grow in a raised bed" were a search hedge or the
            # frost card, "raised bed on grass" was the bicarbonate-of-soda degreaser, "raised bed
            # on concrete" was a chat shrug, "how do i line a raised bed" and "how do i stop a
            # raised bed drying out" were the washing-line answer, and "how much soil do i need
            # for a raised bed" was the gravel calculator. One box, one answer, split by what was
            # asked, because the layers, the surface, the mix and the volume are four questions.
            "cheaply", "cost", "what goes in", "bottom", "line it", "put in", "fill it",
            "what to fill", "grass", "lawn", "turf", "paving", "concrete", "patio", "slabs",
            "driveway", "what compost", "topsoil", "how much soil", "how many bags", "volume",
            "dries out", "drying out", "water", "watering", "wood", "timber", "sleepers",
            "bricks", "materials", "grow in", "plant in")),
          _a_raised_bed,
          # the bed in the house has its own answer, and a bed frame or a mattress is not a
          # garden box
          # "bedding" is not here: its stem is "bed", which is half this row's own key.
          # frost-cover reaches a bed through "bedding", so on this bench the box has to win the
          # tie: "how do i fill a raised bed cheaply" was the frost card on main and is the box
          # once the row is opened up, and no frost line names a raised bed.
          bias=3,
          avoid=("mattress", "duvet", "sheet", "sheets", "bedroom", "hospital", "care home",
                 "cot", "toddler", "pillow", "frame", "sleep", "hotel", "bunk", "bunk bed",
                 # a bed under frost is the frost card's question, not the box's
                 "frost", "frosts", "fleece", "cloche", "snow", "freezing", "cold snap",
                 # how big a bed should be is size-of-a-plot's question, and that row answers it
                 # with the reach and the spacing; the box's own row had the tie on "raised bed"
                 "wide", "width", "big", "large", "space", "size", "how many")),

    # --- a crop that makes flowers and no fruit, and the tomato that will not go red -----------
    # Four crops wear this one question and each needs a different first move, so the reply reads
    # the crop out of the line. "my courgettes are not fruiting" was answered with "botanically a
    # courgette is a fruit", "my runner beans are not setting" and "my strawberries are tiny" got
    # a chat shrug, and "why are my cucumbers bitter" was punted at a search engine.
    entry("crop-not-fruiting",
          (("courgette", "courgettes", "zucchini", "squash", "pumpkin", "pumpkins", "cucumber",
            "cucumbers", "runner bean", "runner beans", "french beans", "broad beans", "beans",
            "strawberry", "strawberries", "tomato", "tomatoes", "tomato plant", "tomato plants",
            "pepper", "peppers", "chilli", "chillies", "chili", "aubergine", "aubergines",
            "eggplant", "eggplants"),
           # The flowering words are the commonest way to say it, and without them a line like
           # "my chilli plant is not flowering" reached the sowing row on the words "chilli" and
           # "plant" and was told when to sow seed it already has in the ground.
           ("not fruiting", "no fruit", "not setting", "no setting", "not producing", "nothing",
            "no flowers", "not flowering", "no flowering", "wont flower", "will not flower",
            "not flowered", "flowering", "flowers", "flower", "flowers dropping", "flowers drop",
            # "why wont my peppers fruit" was answered "botanically a pepper is a fruit": the
            # phrase was not in the key, so the definition row took it. A bare "wont" is only
            # safe here because the other half of the key is a crop name.
            "wont fruit", "will not fruit", "not producing fruit", "wont", "won't", "will not",
            "never sets", "not set a thing",
            # "my aubergines arent fruiting" and "my peppers are not setting" are the same
            # question. "fruiting" is deliberately not here on its own: it stems to "fruit",
            # which made "is a pepper a fruit" the not-setting question.
            "not setting fruit", "arent fruiting", "aren't fruiting", "arent setting fruit",
            # "my chillies havent set any fruit" was answered with the definition of a fruit
            "not set", "havent set", "hasnt set", "haven't set", "hasn't set", "didnt set",
            "didn't set", "set nothing", "setting nothing", "no fruit set",
            "dropping its flowers", "falling"
            " off", "falls off", "tiny", "small", "shrivelled", "bitter", "empty", "bare")),
          _crop_setting_reply,
          # a courgette being a fruit, a tomato going black at the bottom and a split tomato are
          # all different answers, and the harvest table owns "when do i pick them"
          avoid=("botanical", "botanically", "is it a fruit", "fruit or a vegetable", "black",
                 "bottom", "blossom end", "rot", "split", "splitting", "yellow leaves", "ready to"
                 " pick", "how do i cook", "recipe", "chutney"),
          # "a small garden" is the size of the space, not a fruit that came out small, and
          # "how do i grow tomatoes in a small garden" was answered as a plant that is not
          # setting fruit.
          bias=1, guard=_a_small_place_ask),
    entry("watering-holiday", (("holiday", "holidays", "on holiday", "away", "going away",
                                "away for a week", "away for a fortnight", "while im away",
                                "while i'm away", "week away", "weekend away", "trip",
                                "vacation"),
                               ("plants", "garden", "pots", "watered", "watering")),
          "Before a week away, move the pots into shade, soak everything, and stand them on trays "
          "of water; a plastic bottle with a pinhole in the lid, upside down in the compost, keeps "
          "a big pot going for days. Anything precious is worth asking a neighbour to look in.",
          # an explainer on how a plant takes up water also keys "plants" and "water", and it
          # reads as the answer to "how do i keep my pots alive while im away": the away-word in
          # the key is what makes this the row, so it wins the tie it used to lose
          bias=2),
    entry("sow-seed", (("seed", "seeds", "seedling", "seedlings", "sow", "sowing"),
                       ("germinate", "germinating", "sprout", "coming up", "not", "fail")),
          "Seeds fail from cold soil, drying out, or being buried too deep: keep them at about "
          "18-20C, cover the tray with a clear lid until they show, and water from below so the "
          "surface stays damp. Compost over them only as deep as the seed is wide."),
    entry("rose-black-spot", (("rose", "roses", "rose bush", "rose bushes"),
                              ("black spot", "blackspot", "black spots", "spots", "spotted",
                               "yellow leaves", "losing leaves", "bare stems")),
          "Black spot is a fungus that overwinters on fallen leaves and splashes up in the rain: "
          "pick off every spotted leaf and bin it - never the compost - clear the fallen ones "
          "from the soil, and water the roots rather than the plant. Feed it and mulch with "
          "compost so it grows away from the spots, and in a bad year spray a rose fungicide "
          "when the first spots show.",
          ask=("black spot", "blackspot", "black spots", "spots", "spotted", "yellow",
               "losing leaves", "what is", "whats", "how do i", "treat", "cure", "stop"),
          # main's blight row is the general leaf-spot answer and it also names roses, so this
          # row has to rank above it to be the one the rose lines get
          bias=3,
          # a rose that will not flower is a pruning question, and the spots on tomato leaves
          # are blight, not this
          avoid=("not flowering", "no flowers", "wont flower", "won't flower", "prune",
                 "pruning", "tomato", "tomatoes", "potato", "potatoes")),
    entry("chit-potatoes", (("chit", "chitting", "chitted", "chits"),
                            ("potato", "potatoes", "seed potatoes", "spuds", "sprout",
                             "sprouting", "sprouts")),
          "Stand the seed potatoes in a single layer, eyes up, in a cool bright place - a windowsill "
          "in an unheated room, not a warm kitchen - for about six weeks from late January, and "
          "rub off all but the two or three strongest sprouts. An egg box or a tray works, and "
          "greening is fine; long white spindly shoots mean too warm and too dark."),
    entry("improve-soil", (("soil", "compost", "topsoil", "clay", "sandy soil", "soil is"),
                            ("improve", "better", "condition", "lighten", "break up", "poor",
                             "heavy", "clay", "drain", "drains", "enrich", "feed", "how do i",
                             "what should i add")),
          "Add organic matter and let the worms do the rest: two or three barrowloads of garden "
          "compost or well-rotted manure per bed, spread on top in autumn and left for the worms "
          "to pull in. On clay, grit and compost together open it up; on sand, compost holds the "
          "water. Mulch every autumn, do not dig it in, and never walk on a wet bed - the "
          "compaction is what most soil problems actually are.",
          ask=("how do i", "how", "what", "should i", "can i", "improve", "better", "add",
               # a statement about the soil is a question about it: "my soil is heavy clay"
               # names the problem and asks nothing
               "my soil", "the soil", "heavy clay", "clay soil"),
          avoid=("soil ph", "test my soil", "ph test", "potting compost", "seed compost",
                 "which compost", "ericaceous",
                 # making the compost is not what to add to a bed, and "compost" plus "how do i"
                 # carried it: "how do i make compost at home" was told to buy two barrowloads
                 # of it.
                 "make compost", "making compost", "compost at home", "compost bin",
                 "compost heap", "compost pile", "composting", "compost maker", "heap")),
    entry("courgette-no-fruit", (("courgette", "courgettes", "zucchini", "squash", "pumpkin",
                                  "pumpkins", "cucumber", "cucumbers", "marrow"),
                                 ("no fruit", "got no fruit", "not fruiting", "flowers fall",
                                  "flowers drop", "flowering but", "flowers but",
                                  "flowers but no fruit", "flowering but no fruit",
                                  "flowers but no courgettes", "flowers are",
                                  "drop off", "dropping off", "not setting", "no courgettes")),
          'Flowers dropping with no fruit is nearly always pollination: courgettes have separate male and female flowers, and the female one has a tiny fruit behind it that shrivels if no pollen arrives. Pick a male flower, strip the petals and dab it into the centre of a female one in the morning, and leave some male flowers on for the bees.',
          bias=2,
          ask=("my", "why", "what", "how", "help", "fruit", "flowers")),
    entry("prune-fruit-tree", (("apple tree", "apple trees", "pear tree", "pear trees", "plum tree",
                                 "fruit tree", "fruit trees", "cherry tree"),
                                GONE_WILD + ("prune", "pruning", "cut back", "trim",
                                             "when should i prune", "winter pruning",
                                             "shape")),
          "Prune apples and pears in winter, when they are dormant and you can see the shape: take "
          "out dead, damaged and crossing branches first, then shorten the growth you left by "
          "about a third. Plums and cherries are the exception - prune those in June or July, "
          "because winter cuts let silver leaf in. A young tree wants a clear centre like a "
          "goblet; an old one that has gone mad can be brought back over two or three winters "
          "rather than all at once.",
          ask=("how do i", "when", "how", "should i", "can i", "best time",
               "overgrown", "out of control", "taking over", "taken over", "gone wild",
               "too big"),
          avoid=("apple crumble", "apple pie", "cook", "recipe", "store the apples", "how long do apples")),
    entry("rhubarb-green", (("rhubarb", "rhubarb stems", "rhubarb stalks"),
                            ("green", "turning green", "gone green", "not red", "pale", "why")),
          "Green rhubarb is not a problem: some varieties are green-stemmed (Timperley Early goes "
          "pink, Victoria stays greener), and stems that were forced or shaded go redder than the "
          "same plant left in the open. Colour is variety and light, not ripeness - pick on stem "
          "size, and stop picking by the end of June so the crown can build up for next year. "
          "Only the leaves are poisonous, so cut those off and compost them.",
          ask=("why", "my", "are", "is", "should i", "can i", "what")),
    entry("fungus-gnats-rid", (("fungus gnat", "fungus gnats", "gnat", "gnats"),
                               ("get rid", "rid", "kill", "stop", "control", "gone", "everywhere",
                                "how do i", "how to", "deal with", "infestation")),
          "Let the top 2-3cm of compost dry right out between waterings and water from the bottom "
          "for a few weeks: the larvae live in wet compost and dry compost kills them. Stand a "
          "yellow sticky trap in the pot for the adults, put a layer of grit on the surface so "
          "they cannot lay, and repot into fresh compost if it is bad. A half potato pushed into "
          "the soil overnight collects larvae you can throw away.",
          avoid=("kitchen", "bin", "bananas", "sink", "drain", "fruit bowl", "wine", "vinegar")),
    entry("move-a-shrub", (("move", "moving", "moved", "transplant", "transplanting", "dig up",
                            "relocate"),
                           ("shrub", "shrubs", "bush", "bushes", "rose", "roses", "plant", "tree",
                            "climber", "hedge")),
          "Move a shrub while it is dormant, from late autumn to early spring, and on a mild day "
          "when the soil is not frozen. Water it the day before, dig out a rootball as wide as the "
          "branches spread, lift it onto a tarpaulin rather than by the stem, and replant at the same "
          "depth with the roots spread out. Water it weekly through the first summer and do not feed "
          "it - new roots come before new growth.",
          ask=("when", "how", "should i", "can i", "best time", "is it too late", "now"),
          # a tomato plant going outside is hardening off, and a houseplant is the houseplant
          # table's job: both name a plant to move, and neither is a shrub in the border
          avoid=("tomato", "tomatoes", "seedling", "seedlings", "houseplant", "houseplants",
                 "outside", "hardening", "pot on", "grown from seed", "into the ground",
                 "shed", "house", "office", "flat"),
          # "when can i move a plant" after a plant-care turn is a tie with plant-dying once
          # the carried topic adds a word to it, and a tie is settled by the rarity bonus, not
          # by sense. Moving is the narrower job, so it keeps the tie.
          bias=1),
    entry("lavender-cuttings", (("lavender", "lavenders"),
                                ("cutting", "cuttings", "take cuttings", "propagate", "propagating",
                                 "multiply", "grow more", "clone")),
          "Take lavender cuttings in late summer, from the soft new growth at the tip and never "
          "from the old woody stem: a piece about 10cm long, stripped of its lower leaves, pushed "
          "into a pot of gritty compost, and kept damp in a bright but shaded spot. They root in "
          "six to eight weeks, and a plastic bag over the pot for the first fortnight keeps them "
          "from wilting. Autumn cuttings are ready to plant out the following spring.",
          ask=("how do i", "how", "when", "can i", "should i", "best time")),
    entry("seedlings-disappear", (("seedlings", "seedling", "seedlings have gone", "rows",
                                   "gaps in the row", "sown"),
                                  ("disappeared", "disappearing", "have gone", "has gone",
                                   "all gone", "eaten", "vanished", "missing", "nothing came up",
                                   "nothing has come up", "werent there")),
          "Whole seedlings vanishing overnight is slugs or snails, and the answer is a night patrol "
          "with a torch plus a beer trap sunk to the rim, not pellets scattered wide. If the tops are "
          "cut off cleanly and the plant is left standing, it is a bird or a rabbit, so net the row. "
          "Mice take pea and bean seeds out of the ground, and a cloche or some fleece stops them.",
          ask=("why", "how do i", "what", "any", "stop", "help",
               # a complaint about a row is a question without the question mark
               "have", "has", "all", "overnight", "in the night", "chewed", "nibbled", "got",
               # a row that "keeps disappearing" is a complaint, not a question with a mark
               "keep", "keeps", "kept", "keeping", "are", "is", "went", "something"),
          # a seedling that is still there but tall and pale wants more light, not a slug trap
          avoid=("leggy", "tall", "straggly", "pale", "thin", "yellow", "leaves")),
    entry("garden-not-flowering", (("buddleia", "buddleja", "lavender", "clematis", "lilac", "peony",
                             "daffodil", "daffodils", "tulips", "fuchsia", "hydrangea",
                             "delphinium", "gladioli", "sweet pea", "sweet peas", "dahlia",
                             "dahlias", "camellia", "rhododendron", "azalea"),
                            ("no flowers", "no flower", "no blooms", "no blossom", "not flowering",
                             "not flowered", "hasnt flowered", "hasn't flowered", "havent flowered",
                             "haven't flowered", "never flowered", "wont flower", "won't flower",
                             "didnt flower", "didn't flower", "didnt come up", "didn't come up",
                             "nothing came up", "blind")),
          "Most of these are one of four things: it was pruned at the wrong time - a shrub that "
          "flowers on last year's wood (lavender, lilac, clematis, peony) loses its buds if you "
          "cut it in spring - it is too shaded, it got too much nitrogen and grew leaves instead, "
          "or a late frost took the buds. Bulbs that never came up were planted too shallow or too "
          "late. Give it sun, a high-potash feed and the right pruning time.",
          # the pruning rows answer when and how to cut, and a wisteria has its own twice-a-year row
          # main's not-flowering is the houseplant one, so this is the garden row and the two
          # stay out of each other's way
          avoid=("wisteria", "prune", "pruning", "cut back", "when should i", "how do i prune",
                 "deadhead", "yellow leaves", "brown leaves", "houseplant", "house plant",
                 "indoor", "peace lily", "orchid", "christmas cactus", "african violet"),
          ask=("no flowers", "no flower", "no blooms", "no blossom", "not flowering", "not flowered",
               "hasnt flowered", "hasn't flowered", "never flowered", "wont flower", "won't flower",
               "didnt flower", "didn't flower", "didnt come up", "didn't come up", "nothing came up",
               "blind")),

# --- the outdoor jobs nobody answered --------------------------------------------
# Six lines that were a punt or a wrong answer on main: a garden that will not bring birds, a
# hydrangea (colour, water, pruning), a cast-iron plant going brown, moss between paving, bamboo
# that will not stay put, a shrub to move, a bay that has gone yellow, and pots drying out in
# summer. Each is keyed on the thing the person named, so one answer serves every way of asking
# for it.
    entry("garden-birds",
          (("attract birds", "birds to my garden", "birds in the garden", "feed the birds",
            "bird feeder", "bird feeders", "bird table", "bird bath", "nest box", "nesting box",
            "more birds", "birds come"),
           ("how", "what", "feed", "feeding", "attract", "encourage", "bring", "get more",
            "bath", "table", "box", "food", "seeds", "fat balls", "winter")),
          "Food, water and cover, in that order: a feeder with mixed seed or fat balls, a shallow "
          "dish of water with a stone in it, and a shrub or a hedge to bolt into. Put the feeder "
          "where a cat cannot sit under it, leave the seed heads on perennials over winter, and "
          "skip the tidy-up in autumn - the birds eat the insects in the stems.",
          # a pet bird, a bird on a menu and an aeroplane are not a garden
          # "what should i feed the birds" has a short feeding card of its own in nature.py, and
          # this row answering it with the food-water-cover routine made a two-sentence answer
          # eight lines long. Standing down here sends the feeding words back there, while a
          # feeder, a table, a bath and a nest box stay with this row.
          avoid=("parrot", "budgie", "cockatiel", "canary", "chicken", "pet", "roast", "recipe",
                 "cook", "eat", "flight", "airport", "turkey",
                 "feed", "feeds", "feeding", "fed", "what to feed", "bird food", "food for birds",
                 "seeds", "seed", "fat balls", "mealworms", "bread", "leftovers")),
    entry("hydrangea-care",
          (("hydrangea", "hydrangeas", "mophead", "lacecap", "hortensia"),
           ("care", "water", "watering", "how often", "look after", "looking after", "prune",
            "pruning", "cut back", "deadhead", "colour", "color", "blue", "pink", "purple",
            "yellow", "brown", "wilting", "drooping", "not flowering", "flowering", "feed",
            "plant", "grow", "move", "soil", "acid", "alkaline", "ericaceous", "lime")),
          _hydrangea,
          # Two neighbouring rows already answer half of this plant: `hydrangea-brown` is the
          # wilting and the brown blooms, and `PRUNE_HYDRANGEA` is the March cut. This row keeps
          # the care and the colour, and stands aside for both of them.
          avoid=("shop", "bouquet", "wedding", "gift", "fake", "artificial", "silk", "hair",
                 "lipstick", "nail",
                 "wilting", "wilted", "wilt", "brown", "browning", "drooping", "droopy", "dying",
                 "died", "dead", "prune", "pruning", "pruned", "cut back", "cutting back",
                 "deadhead", "deadheading", "spring", "march")),
    entry("aspidistra-care",
          (("aspidistra", "aspidistras", "cast iron plant", "cast-iron plant"),
           ("care", "water", "watering", "how often", "look after", "brown", "yellow", "dying",
            "drooping", "leaves", "leaf", "repot", "split", "feed", "light", "keep alive")),
          "An aspidistra wants the opposite of fuss: a spot out of direct sun, water only when "
          "the compost is dry to the touch, and almost nothing in winter. Brown tips and splitting "
          "leaves are dry air or a wet pot rather than hunger, so let it drain and stand it "
          "somewhere less dry rather than feeding it.",
          avoid=("fake", "artificial", "buy", "shop", "flower", "gift")),
    # One table for the moss on a hard surface. cleaning.py had a second row for the same lines
    # (`outside-moss`, keyed on the surface and the moss, bias 1) and it won every tie, so this
    # one never answered: "moss on my patio" got the washing-powder card and the paving steps -
    # scrape the joints out, refill with kiln-dried sand - were unreachable. The keys and the
    # steps of both are here now.
    entry("paving-moss",
          (("moss", "mossy", "algae", "green", "greens up", "slippery", "slippy", "slick",
            "slime", "lichen", "weeds", "weed", "weeded"),
           ("paving", "patio", "path", "paths", "driveway", "drive", "block paving",
            "blockpaving", "pavers", "slabs", "slab", "blocks", "stepping stones", "bricks",
            "brick", "between the stones", "between the slabs", "between the paving",
            "between the flags", "joints", "gaps", "growing between", "growing through",
            "keep coming back", "come back every year", "decking", "deck", "concrete", "tarmac",
            "terrace", "yard", "steps", "stone flags", "flags", "gravel", "roof", "roofs")),
          "Moss on paving is damp plus shade, so the fix is to open up the joints and let them "
          "dry: scrape it out with a patio knife or a stiff brush, then refill the gaps with "
          "kiln-dried sand rather than soil. A pressure wash clears it in an afternoon but it "
          "comes back in the same damp corner, so if you want what is left dead rather than gone, "
          "biological washing powder or white vinegar on the paving, left half an hour and then "
          "scrubbed and rinsed, does that - nothing keeps it away while the joint stays wet. "
          "Weeds in the joints come out with a knife or an old screwdriver and a "
          "kettle of boiling water down the gap stops the next lot; on decking keep the jet low "
          "and go along the grain, because a hard one furries softwood.",
          # "how do i clean the green off my patio" names a wash and asks about the growth, so the
          # growth wins the tie; it also ties the pet-accident row on "driveway" and "weeds".
          bias=1,
          # a lawn, a roof and a wall each have their own answer; only the hard surfaces are here.
          # What stands on the paving, or has soaked into it, is not the paving either.
          avoid=("lawn", "grass", "turf", "mow", "scarify", "roof", "gutter", "guttering",
                 "wall", "walls", "fence", "pond", "tank", "aquarium", "fish tank", "tree",
                 "trees", "shade", "flower bed", "borders", "hanging basket", "shed",
                 "oil", "oils", "diesel", "petrol", "grease", "fuel", "paint", "cement", "render",
                 "mortar", "resin", "tar spot", "blood", "vomit", "poo", "bird mess",
                 "snow", "snowed", "ice", "icy", "grit", "gritted", "salt",
                 "table", "tables", "chair", "chairs", "bench", "benches", "seat", "seats",
                 "umbrella", "umbrellas", "parasol", "parasols", "heater", "chiminea",
                 "planter", "planters", "pot", "pots", "trough", "troughs", "swing",
                 "hot tub", "door", "doors", "gate", "gates", "bbq", "barbecue")),
    # A rocker, a crack or a slab that has sunk is the commonest thing a patio does, and nothing
    # answered it: "how do i fix a broken paving slab" and "my patio slab is loose" were shrugs.
    entry("paving-slab",
          (("paving slab", "paving slabs", "patio slab", "patio slabs", "paving stone",
            "paving stones", "flagstone", "flag stone", "flagstones", "slab", "slabs",
            "block paving", "stepping stone", "stepping stones", "patio"),
           ("broken", "broke", "cracked", "crack", "cracks", "loose", "wobbly", "rocking",
            "rocks", "rock", "sunken", "sunk", "dipped", "uneven", "lift", "lifting", "lifted",
            "replace", "replacing", "repair", "fix", "how do i", "coming up", "came up")),
          "Lift it with a spade or two thin chisels and keep the pieces to match the colour, then "
          "bed it back on a full layer of sharp sand and mortar rather than four dabs at the "
          "corners, which is what lets a slab rock. Tap it down level with its neighbours with a "
          "rubber mallet, running a straight edge across the joints, and leave it 24 hours before "
          "you brush sand in. A slab cracked in two can be glued with exterior resin, but the "
          "crack will always show.",
          # moss, weeds and a dirty patio are different jobs on the same slabs
          avoid=("moss", "mossy", "weed", "weeds", "weeding", "pressure wash", "pressure washing",
                 "clean", "cleaning", "stain", "oil", "algae", "slippy", "slippery",
                 "patio heater", "patio doors", "furniture", "table", "chairs")),

    # A roof is not paving: the moss is the same, the thing that clears it is not, and with the
    # roof words fenced out of both moss rows "moss on my roof" had no answer at all.
    entry("roof-moss",
          (("moss", "mossy"),
           ("roof", "roofs", "gutter", "gutters", "guttering", "downpipe", "downpipes", "tile",
            "tiles", "roof tiles", "slates", "shed roof", "chimney")),
          "Moss on a roof wants a scraper rather than a pressure washer: scrape it off dry, let "
          "the tiles air, and clear the gutters and downpipes so the rain runs away instead of "
          "feeding it. Don't pressure-wash an old roof - it strips the surface and finds leaks you "
          "did not have. If it comes back every year on a north-facing slope, a copper or zinc "
          "strip along the ridge kills it slowly as the rain washes over it.",
          bias=1),
    entry("bamboo-spread",
          (("bamboo", "bamboos", "running bamboo", "bamboo roots", "bamboo rhizomes"),
           ("spread", "spreading", "spreads", "contain", "containing", "containment",
            "take over", "taking over", "taken over", "control", "controlling", "stop",
            "stopping", "invasive", "everywhere", "rhizome", "rhizomes", "root barrier",
            "barrier", "neighbours", "neighbors", "get rid")),
          # "pot" is not here: growing a bamboo in a pot is a planting question, and with "pot"
          # in this part "how do i grow bamboo in a pot" scored this row and got a root barrier.
          ("A running bamboo spreads with rhizomes just under the surface, so it is contained "
           "rather than pruned: a root barrier of thick polythene or HDPE, 60cm deep and set at a "
           "slight angle outwards, all the way round, with the top 2cm left showing above the soil "
           "so you can see a rhizome trying to hop it and cut that off. Never dump a dug-out "
           "rhizome on the compost heap: it roots."),
          # a bamboo shoot is a stir-fry, a bamboo cane is a plant support and a bamboo blind is a
          # blind: none of those is a running plant in a border
          avoid=("shoot", "shoots", "eat", "eating", "cook", "cooking", "stir fry", "stir-fry",
                 "recipe", "canes", "cane", "stakes", "plant support", "flooring", "blind",
                 "blinds", "mat", "mats", "towel", "sushi", "steamer", "basket"),
          # "how do i stop bamboo taking over" is not a clump being divided: the divide row names
          # bamboo and "taking over" too, so the row that is about bamboo wins the tie
          bias=2),
    entry("bay-yellow",
          (("bay tree", "bay trees", "bay bush", "bay hedge", "bay plant", "bay leaf plant",
            "bay"),
           ("yellow", "yellowing", "going yellow", "gone yellow", "pale", "brown", "dropping",
            "dropping leaves", "losing leaves", "dying", "patchy")),
          "A bay that has gone yellow is usually water at the roots - it hates standing wet in "
          "winter and drying right out in summer - so check the drainage and water it in a dry "
          "spell. If the yellow leaves are on one side and feel sticky underneath, look for bay "
          "sucker or scale insects and wipe them off; a pale bay in a pot is often simply hungry, "
          "and a liquid feed through the summer greens it up.",
          # a bay window, a bay in a car park and a bay leaf in a recipe are other words
          avoid=("window", "windows", "bay window", "car", "parking", "park", "garage",
                 "recipe", "cook", "sauce", "soup", "stock", "dried", "supermarket", "buy")),
    entry("pots-drying",
          (("pots", "pot", "containers", "planters", "tubs", "window boxes"),
           ("drying out", "dry out", "dries out", "dried out", "water", "watering", "watered",
            "keep them watered", "hot weather", "heatwave", "holiday", "while i am away",
            "while im away")),
          "Group the pots together out of the wind, mulch the compost with gravel or bark, and "
          "stand them in a saucer so the water that runs through soaks back up. A big pot dries "
          "out far slower than a small one, so pot up rather than watering more, and in a heatwave "
          "check them morning and evening - a pot whose roots fill it can want water twice a day.",
          # the pots in the kitchen, in a shop and in a pan are not garden containers
          avoid=("dishes", "washing up", "cook", "cooking", "pan", "tea", "coffee", "yogurt",
                 "yoghurt", "jam", "supermarket", "buy", "shop", "sell", "money", "paint"),
          # "the soil in my pots dries out quickly" was the hot-pan card ("take it off the heat
          # and do not put cold water in it while it is hot"), because a kitchen row scored the
          # same on "dries out" and its own words. A line about the soil in a pot is a garden
          # line, and this row is the one that says so.
          bias=1),
]

# A hedge that has gone brown at the bottom, thin, or patchy is not a boundary dispute and not
# a "when do I cut it" question: nothing in the line is about a neighbour, a height or the light.
# It is the one thing a hedge does when it has been cut flat-sided, cut into old wood, or grown
# in the shade of its own top, and the answer is what to do about it now.
ENTRIES.append(entry(
    "hedge-gone-brown-at-the-base",
    (("hedge", "hedges", "privet", "box hedge", "conifer hedge", "leylandii", "laurel hedge",
      "beech hedge", "hornbeam", "yew", "yew hedge"),
     ("brown at the bottom", "brown at the base", "brown at the base", "gone brown",
      "bare at the bottom", "bare at the base", "bald at the bottom", "dead at the bottom",
      "bare patch", "bare patches", "patchy", "yellow", "yellowing", "yellowed", "thin",
      "sparse", "gaps", "gap", "not growing", "looks dead", "looking sorry", "sorry for itself",
      "looks bad", "looks sad", "dying", "died", "brown", "no leaves", "leaves falling",
      "dropping leaves", "bare", "bald", "bald patch", "bald patches", "patches", "patchy",
      "see through", "holes in it")),
    "Almost always the top has grown wider than the base, so the bottom sits in its own shade "
    "and the light never gets to it: cut the sides back so they slope in towards the top, take "
    "the height down a little at the same time, and feed and water the base - that is what makes "
    "it shoot again. Privet, yew, beech and hornbeam come back from old wood; leylandii and most "
    "conifers do not, so on those you cut only into green growth and accept the bare patch. If "
    "the brown is patchy and spreading with no shape to it, check for box blight or a vine weevil "
    "in the soil before you feed anything.",
    # the boundary and the light are the neighbour row's, and the cut itself is the pruning row's
    avoid=("neighbour", "neighbours", "neighbour's", "next door", "boundary", "blocking my light",
           "blocks my light", "right to light", "council", "too tall", "too high", "planning",
           "when should i cut", "when do i cut", "how often should i cut", "how do i cut",
           "what time of year"),
    # a plant named in the line wins over a bare state word: "my hedge has bald patches" matched
    # the hair-loss card on "bald patches" and was answered with a handful of hair
    bias=2))
# A sunflower question is about light and shelter before it is about a sowing date, and nothing in
# the tables held the plant: "do sunflowers need full sun", "where should i plant sunflowers" and
# "how do i grow sunflowers" were all a shrug.
ENTRIES.append(entry(
    "sunflowers",
    (("sunflower", "sunflowers", "sun flower", "sun flowers"),
     ("full sun", "sun", "sunny", "sunlight", "shade", "shaded", "north facing", "where",
      "plant", "planting", "sow", "sowing", "grow", "growing", "when", "how tall", "height",
      "stake", "stakes", "slugs", "snails", "yellow leaves", "drooping", "not flowering",
      "no flowers", "pot", "pots", "container", "variety", "varieties", "seeds", "seed",
      "from seed", "how far apart", "spacing")),
    "Six hours of direct sun, and shelter from the wind: in shade a sunflower grows tall and thin "
    "and then flops. Sow indoors in April or straight outside in May, 2cm deep and 45cm apart, "
    "and stake the tall varieties early rather than after they lean. Water and feed weekly once "
    "the bud shows, and put a slug barrier round them while they are small, because that is what "
    "takes them.",
    # nothing here is a crop to eat, so a kitchen line stays with the kitchen
    avoid=("eat", "eaten", "edible", "roast", "cook", "recipe", "oil", "seeds to eat")))

# "my tree looks dead" reached nothing: the leaf-colour answer is a fact about autumn, the hedge
# answer is about a hedge, and the pruning rows all assume the tree is alive. What a person wants
# is the test and the wait, because most garden trees that look dead in early spring are not.
ENTRIES.append(entry(
    "tree-looks-dead",
    (("tree", "trees", "apple tree", "oak", "maple", "birch", "willow", "cherry tree", "plum tree",
      "pear tree", "fruit tree", "sapling", "conifer"),
     ("dead", "died", "dying", "looks dead", "not coming back", "no buds", "no new growth",
      "still alive", "is it alive", "brown", "bare branches", "snapped", "scratch", "revive")),
    "Scratch the bark on a young twig with a fingernail: green and damp underneath means that "
    "branch is alive, dry and brown means it is not, so do three or four round the tree rather "
    "than one. Wait until mid-spring before you write it off, because a hard winter, a late frost "
    "or a dry summer makes a healthy tree leaf out late or drop its leaves early, and a bud that "
    "is plump and firm in late winter is a tree that is still coming back. If most of the "
    "scratches are brown, look for the reason before you buy a replacement: waterlogged ground, "
    "mulch heaped against the trunk, the root flare buried when it was planted, or a strimmer "
    "wound at the base are what kill a garden tree rather than old age.",
    # the pruning and planting rows answer a live tree's jobs, the hedge row answers a hedge, and
    # a felled or felled-by-the-council tree is a different question again
    avoid=("prune", "pruning", "pruned", "cut back", "when should i cut", "how do i cut",
           "plant", "planting", "planted", "sow", "sowing", "grow", "growing", "hedge", "hedges",
           "privet", "leylandii", "cut down", "fell", "felling", "stump", "neighbour",
           "neighbours", "next door", "boundary", "planning", "council", "treehouse",
           "christmas tree", "family tree",
           # the leaves going yellow on a live tree in autumn is the colour fact in nature.py
           "leaves are turning", "turning yellow", "turning brown in autumn", "losing leaves",
           "leaves falling")))

# --- a rose that is not well, or that nobody has told you how to keep ---------------------
# "my roses are dying", "my roses are wilting", "why are my roses dying" and "my climbing rose is
# dying" were all answered with the cut-flower card ("trim 2cm off each stem"), because a bunch in
# a vase and a rose in a border are the same two words. "my rose bush is dying", "my roses are
# looking sad", "my rose bush has no leaves", "how do i look after roses" and "how often should i
# water my roses" were all shrugs. One row for the plant, keyed on the plant and the symptom, and
# the vase keeps its own lines through the words below.
ROSE_NOT = ("vase", "vases", "bouquet", "bouquets", "cut flowers", "cut flower", "florist",
            "picked", "in water", "flower food", "mothers day", "mother's day", "valentine",
            "valentines", "wedding", "bunch",
            # a named pest, spot or job has its own row, and it is the better answer
            "greenfly", "blackfly", "aphid", "aphids", "black spot", "blackspot", "spot",
            "spots", "spotted", "rust", "mildew", "prune", "pruning", "pruned", "deadhead",
            "deadheading", "plant", "planting", "planted", "bare root", "sow", "sowing",
            "flower", "flowers", "flowering", "bloom", "blooms")


def _rose_care(memory, understood):
    """The rose answer the line is asking for: how much water, what to feed it, or why it is sulking."""
    line = _words(understood)
    if _has(line, "water") or _has(line, "watering") or _has(line, "how often") \
            or _has(line, "hosepipe"):
        return ("A rose in the ground wants a full watering can per plant each week in dry weather, "
                "poured at the base rather than over the leaves, and a rose in a pot wants that "
                "much every other day in summer, because a pot dries out far faster than the soil. "
                "Water in the morning, and give it a proper soak: a light sprinkle every evening "
                "only wets the top inch, and the roots stay shallow and thirsty.")
    if _has(line, "feed") or _has(line, "feeding") or _has(line, "fertiliser") \
            or _has(line, "fertilizer"):
        return ("Feed a rose with a rose feed, not a general one, from the first leaves in spring "
                "until the end of July: a handful of granules round the base in March and again in "
                "June, watered in, or a liquid feed every fortnight while it flowers. Stop by "
                "August so the new growth hardens before winter, and never feed a dry plant - "
                "water it first, or the feed burns the roots.")
    if not any(_has(line, w) for w in ("ground", "garden", "bush", "bushes", "border", "pot",
                                       "soil", "beds", "bed", "shrub", "climbing", "patio",
                                       "plotted", "planted", "allotment", "leaves", "leaf",
                                       "stems", "stem", "roots", "root", "buds", "bud",
                                       "shoots", "hedge")):
        # "my roses are dying" with no cue either way can be a bunch in a vase or a plant in the
        # ground, and the two want opposite things, so answer both rather than pick one.
        return ("Cut roses die in a day or two for a simple reason: trim 2cm off each stem at an "
                "angle, strip any leaf that would sit in the water, change the water every other "
                "day and keep them out of sun. A rose in the ground that looks dead is usually "
                "thirsty or hungry instead: a full can a week at the base, a rose feed while it "
                "flowers, and cut the brown stems back to green wood - one dry fortnight drops "
                "every leaf before the plant is dead.")
    return ("A rose in the ground is nearly always thirsty, hungry or short of air: water it at the "
            "base, a full can a week in dry spells, more in a pot, and feed it with a rose feed "
            "while it flowers. Cut out the yellowing and spotted leaves and bin them rather than "
            "compost them, because black spot and rust live on the fallen leaves and splash back up "
            "in the rain. If the stems themselves are brown and dry, prune those back to green wood "
            "and water: a rose left dry for a fortnight drops its leaves and looks dead before it "
            "is.")


ENTRIES.append(entry(
    "rose-care",
    (("rose", "roses", "rose bush", "rose bushes", "climbing rose", "climbing roses",
      "shrub rose", "shrub roses", "rambling rose", "patio rose"),
     ("dying", "died", "wilting", "wilts", "wilted", "drooping", "droopy", "yellow", "yellowing",
      "brown", "no leaves", "losing leaves", "lost its leaves", "bare", "looking sad",
      "look sad", "looks sad", "looking poorly", "poorly", "not looking well", "sulking",
      "revive", "keeping alive", "keep alive", "look after", "looking after", "care", "care for",
      "water", "watering", "feed", "feeding", "fertiliser", "fertilizer", "how often")),
    _rose_care,
    avoid=ROSE_NOT,
    bias=2))

# A cold snap is the one night of the year when the garden needs something done by hand, and
# every way of asking it was a punt on main: "how do i protect plants from frost", "how do i
# cover plants for frost", "will my plants survive the frost", "how do i keep my greenhouse
# warm". The one that was answered said the wrong thing - "how do i stop frost damage to plants"
# got the overwatering answer, because "plants" and "damage" are the dying row's words, and the
# cold is the whole question.
ENTRIES.append(entry(
    "frost-protection",
    (("frost", "frosts", "frosty", "freezing", "freeze", "frozen", "cold snap",
      "cold spell", "cold night", "cold nights", "sub zero", "minus", "cold weather", "cold",
      "winter", "winters", "overwinter",
      # "how do i keep my greenhouse warm" names no frost at all, only the job, so the warm
      # words have to count on the asking side too, and "overnight" is how a person names the
      # one night this is about: "how do i protect tender plants overnight" was a punt.
      "warm", "warmer", "heat", "heating", "insulate", "overnight"),
     ("plant", "plants", "garden", "seedlings", "seedling", "veg", "vegetables",
      "flowers", "pots", "shrub", "shrubs", "bedding", "tender", "protect", "cover",
      # A bed of flowers is the garden's question: "raised beds in a cold spell" passed the
      # "something growing" guard on "raised bed" and then matched none of this row's subject
      # words, so the row stood down and the line got a listening hedge.
      "bed", "beds", "flower bed", "flower beds", "raised bed", "raised beds",
      "border", "borders", "allotment",
      "damage", "survive", "fleece", "greenhouse", "hanging basket", "baskets",
      "cuttings", "banana plant", "tree fern", "citrus", "olive",
      # "warm", "heat" and "insulate" used to stand alone here as well, and they are the words a
      # house line brings too: "how do i keep warm in this cold snap" is person and house, not
      # soil and fleece, and it matched twice and won. A greenhouse line still reaches the row on
      # "greenhouse" alone, so the bare warm words are gone.
      "greenhouses", "bubble wrap")),
    "Water the soil the day before: wet soil holds the day's heat and gives it back at night, "
    "and dry soil gives back nothing. At dusk, not at midnight, put fleece, an old net curtain "
    "or a doubled bedsheet over the plants and take it off in the morning, and push pots "
    "together against a house wall and off the ground, because the wall and the slab give out "
    "heat all night. In a greenhouse, bubble wrap the glass and cover the plants, and a paraffin "
    "heater or a hot water bottle under a cloche does the rest. Most damage shows up two days "
    "later as blackened leaves: leave them on until spring because they are insulation, and "
    "start watching the forecast from about 5C, which is when the tender things start to go.",
    # a houseplant indoors, a lawn, a pond and a whole winter of care are other questions: the
    # cold snap is about what to put over what, tonight
    avoid=("houseplant", "houseplants", "house plant", "house plants", "monstera", "orchid",
           "lawn", "grass", "mow", "pond", "ponds", "fish", "car", "windscreen",
           # "heating" used to be here and it is one of the row's own key words - "how do i heat
           # my greenhouse" was vetoed by the row that answers it and got an argument card. The
           # boiler and the radiator keep their lines on their own nouns.
           "windscreen cover", "pipes", "pipe", "boiler", "radiator",
           "snails", "slugs", "weeds", "prune", "pruning",
           # a plant that came through the cold and now looks dead is the dying row's test,
           # which is the bark-and-compost answer, not what to put over things tonight
           "smelly", "brown and soft", "drooping", "wilted", "limp",
           # an animal that is cold is the pets table's question, not a plant's: "how do i keep
           # my dog warm in winter" was this card, which is soil and fleece
           "dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens",
           "rabbit", "rabbits", "hamster", "hamsters", "guinea pig", "budgie", "parrot",
           "pet", "pets", "animal", "animals", "horse", "chickens",
           # keeping a person or a house warm is the home rows' question, and it was reaching
           # this card because "cold snap" and "cold" are its own key words: "how do i keep warm
           # in this cold snap" and "how do i keep the house warm in winter" were both told to
           # water the soil. A greenhouse line never says any of these.
           "keep warm", "stay warm", "keep myself", "keep us warm", "keep the house",
           "house", "home", "flat", "living room", "bedroom", "room", "rooms",
           # "bed" alone was here, and it is the bed a person lies in as well as the stem of
           # "bedding": the body words carry the person's line, so a bed of flowers stays a bed.
           "in bed", "cold in bed", "feet", "foot", "hands", "hand", "fingers", "finger",
           "toes", "toe", "blanket", "duvet", "sleep", "sleeping",
           "my nan", "my mum", "my dad", "elderly", "heating bill", "energy bill",
           "bills", "bill", "thermostat", "radiator", "radiators", "boiler"),
    # A person who is cold is not a plant, and a list of their words can only name the ones
    # somebody thought of: "how do i survive the cold", "how do i protect my skin from the cold"
    # and "how do i keep my baby warm in winter" name none of the words above. The guard asks for
    # the other thing instead - something growing, or the fleece and cloche over it, which every
    # way of asking the garden question names.
    guard=_the_cold_is_the_garden_s))

# The pond in winter was three punts in a row - "how do i stop my pond freezing over", "do i need
# to keep a hole in the pond in winter", "how do i overwinter a pond" - and the answer people
# need is mostly what not to do, because smashing the ice is what kills the fish.
ENTRIES.append(entry(
    "pond-in-winter",
    (("pond", "ponds", "fish", "goldfish", "koi"),
     ("freeze", "freezes", "freezing", "frozen", "ice", "iced over", "icing over",
      "winter", "overwinter", "winterise", "winterising", "the hole", "a hole", "keep a hole",
      "pump", "filter",
      "feed", "feeding", "fed", "fish", "bottom", "cover")),
    "Never smash the ice: the shock wave stuns and kills the fish. Float a ball on the surface "
    "so it keeps a hole open as it moves, or stand a pan of hot water on the ice until it melts "
    "through, and keep a hole open all winter so the gases can get out. Keep the pump and filter "
    "running, but turn off any fountain above the water because the splash chills the pond. Stop "
    "feeding once the water is below 10C, because the fish stop digesting and the food rots, and "
    "they sit together at the bottom where the water sits at about 4C. Net the leaves out in "
    "autumn, because a rotting layer on the bottom is what turns the water green in spring.",
    # a fish that is ill, a pond that is green in summer and a new pond are other questions
    avoid=("green water", "algae", "blanket weed", "blanketweed", "filter not working",
           # a tank indoors is not a pond: "my fish tank filter is noisy" was this card, because
           # "fish" and "filter" are two of its words and none of them says outdoors.
           "tank", "tanks", "aquarium", "fish tank", "fish tanks", "fishbowl", "indoor",
           "in the house", "bedroom", "living room", "noisy", "rattling", "humming",
           "my fish is sick", "fish are dying", "build a pond", "dig a pond", "pond liner",
           "how big", "frogs", "frog", "newts", "tadpoles",
           # a fish in a bag in the freezer is the kitchen's question: "can i use frozen fish
           # instead of fresh" was the pond card, because "fish" and "frozen" are its two words
           "cook", "cooking", "recipe", "eat", "eating", "defrost", "thaw", "bake", "baked",
           "fry", "fried", "oven", "pan", "shop", "supermarket", "instead", "dinner",
           "fillets", "fillet", "fresh", "tin", "tinned", "fish fingers", "batter",
           "bought from", "is it safe",
           # "can i freeze fish" is the same storage question, and it was the pond card because
           # "fish" is this row's word and "freeze" is its act. The phrases, never the bare
           # "freeze": "how do i stop my pond freezing over" needs the word and is this row's.
           "can i freeze", "can i refreeze", "in the freezer", "the freezer", "freezer bag",
           "freeze it", "keep fish in the fridge", "how long can i keep"),
    # "pump", "filter" and "feed" are here so the winter pump question lands, and they let the
    # summer jobs in: the row answers a pond in the cold, so the cold has to be in the line
    guard=_a_winter_pond_line, bias=1))

# The other half of the year: green water, blanket weed, a filter that needs rinsing and how much
# to feed. Every way of asking it was a punt on main - "my pond has gone green", "how do i stop
# my pond going green", "how do i get rid of algae in my pond", "how do i clean my pond filter",
# "blanket weed is taking over my pond", "how often do i feed my pond fish", "how do i clear my
# pond water", "how do i clean the pond in spring" - and one said something else entirely: "my
# pond water is green and cloudy" got the answer for milky tap water.
ENTRIES.append(entry(
    "pond-in-summer",
    # not "the water" on its own: a fish tank, a water butt and a green bottle all say it, and
    # "how often should i change the water" in a chat about a tank was this card
    (("pond", "ponds", "goldfish", "koi"),
     ("green", "greener", "greenest", "pea soup", "cloudy", "murky", "mucky", "dirty",
      "algae", "alga", "blanket weed", "blanketweed", "weed", "sludge", "silt",
      "clear", "clearing", "clean", "cleaning", "spring clean", "filters", "filter",
      "pump", "leaves", "feed", "feeding", "how often", "how much", "oxygen",
      "water quality", "smell", "smells", "smelly")),
    "Green water is algae feeding on sunlight and on the nutrients in the water, so the fix is to "
    "take one of those away: put a water lily or floating plants over half the surface for shade, "
    "and plant up the margins so the water has less of the light and the feed it needs. Barley "
    "straw in a mesh bag slows blanket weed and is harmless to the fish, and a dark dye does the "
    "same job in a pond with no plants in it. Rinse the filter sponges in a bucket of pond water, "
    "never under the tap, because the chlorine kills the bacteria that keep the water clear, and "
    "clean them a little at a time so the pond never loses its whole filter in one afternoon. "
    "Feed the fish what they clear in five minutes, once a day in warm weather, and not at all "
    "below 10C, because the food they leave is what turns the water green. For blanket weed, "
    "twirl it out with a stick rather than reaching in, and net the leaves out in autumn before "
    "they sink, because the sludge on the bottom is next summer's algae.",
    # the ice, a fish that is ill, a new pond and a leaking one are other questions
    avoid=("freeze", "freezes", "freezing", "frozen", "ice", "iced", "icy", "winter",
           "winters", "overwinter", "winterise", "winterize", "cold snap", "frost",
           "my fish is sick", "fish are dying", "fish is dying", "gasping", "ammonia",
           "build a pond", "dig a pond", "pond liner", "how big", "leaking", "leak",
           "frogs", "frog", "newts", "tadpoles", "heron", "tank", "aquarium", "bowl",
           "indoor", "tap water", "drinking water", "milk",
           # a pump that has stopped is a fault to find, not a water-quality question: the
           # chat bridge that asks what it is doing is the better reply
           "stopped working", "not working", "broken", "packed up", "stopped running",
           "isnt working", "isn't working", "tripping", "noisy",
           # how much to feed them is pets.py's fish-feed row, which answers it properly, and
           # "how often" is in this row's own key for the other jobs
           "feed", "feeds", "feeding", "fed", "food", "flakes", "flake", "pellets",
           "pellet", "overfeed", "overfeeding",
           # a fish to cook is the kitchen's, and a green vegetable is not a pond
           "cook", "cooking", "recipe", "eat", "eating", "defrost", "thaw", "bake",
           "fry", "fried", "oven", "pan", "shop", "supermarket", "dinner", "fillets",
           "fillet", "fish fingers", "batter", "salad", "smoothie", "juice"),
    # the other side of the year is the ice row's, and "filter" and "pump" are in both keys
    guard=_a_summer_pond_line))

# The garden has a winter answer and no other season, so "what jobs do i do in the garden in
# spring" was the winter card (the word "jobs" was the only thing it had in common with the
# line), "jobs for the garden in october" was the winter card too, and "what do i do in the
# garden in autumn" was a punt. A season in the line is the season the person is asking about,
# and the month it is now is the season when the line says "now": one answer per season, chosen
# from what the line names, with winter keeping the text it already had.
_JOBS_IN_WINTER = (
    "The garden in winter is mostly tidying and waiting: clear the dead stems but leave seed "
    "heads and any hollow stalks standing, because insects shelter in them and the birds eat "
    "the seeds. Mulch bare soil with compost or bark, but only once the ground is not frozen, "
    "and stay off wet or frozen grass because footprints kill the blades under them. Prune apples "
    "and pears and any shrub that flowers on this year's wood, clean and sharpen the tools, and "
    "wash out the greenhouse with a mild disinfectant before spring sowing. Pots are what the "
    "cold kills, so move them against a wall, raise them onto feet so the drainage hole does not "
    "sit in water, and give tender plants a layer of bubble wrap. Check the stored produce and "
    "the dahlias every couple of weeks for rot, and order seeds in January, because the quiet "
    "months are the only time the garden has nothing urgent in it.")

JOBS_IN = {
    "spring": (
        "Spring goes in this order: rake the lawn and fork the beds once the soil has dried out "
        "enough not to clod, mulch the borders with compost before the weeds start, and prune "
        "the shrubs that flower on the wood they made last year - roses, buddleia, fuchsia - "
        "while they are still dormant. Sow the hardy veg outdoors, harden off anything you "
        "raised indoors for a week before it goes out, and feed the lawn once the grass is "
        "growing. Then watch the forecast, because a late frost is what takes the blossom and "
        "the new leaves, and a sheet of fleece over a flowering fruit tree earns its keep."),
    "summer": (
        "Summer is watering, feeding and picking: soak the beds in the evening rather than "
        "sprinkling them every day, mulch while the soil is damp to hold that water in, and "
        "water the things you planted this year first, because their roots are still shallow. "
        "Deadhead the flowers so they keep coming, feed anything in a pot every week or so, and "
        "cut the lawn a little higher rather than scalping it, which browns it in a dry spell. "
        "Pick courgettes, beans and salad small, because a plant left to swell stops making "
        "more, and get the weeds out before they set seed."),
    "autumn": (
        "Autumn is clearing and planting: pull the spent crops and annuals into the compost, "
        "plant bulbs and bare-root roses, fruit trees and hedging while the soil is still warm, "
        "and rake the leaves off the lawn and out of the pond. Cut back what has finished but "
        "leave the seed heads standing for the birds, mulch the beds, and give the lawn a late "
        "cut with an autumn feed rather than a short one. Then check what is stored - apples, "
        "onions, dahlias - for rot, and order next year's seed and bare-root plants, because "
        "the good varieties go early."),
    "winter": _JOBS_IN_WINTER,
}

# The words that make a line a question about the garden's work rather than about one plant,
# one pest or one tool, every one of which has its own answer.
_GARDEN_JOBS = (
    "jobs", "job", "what do i do", "what can i do", "what should i do", "what do i need to do",
    "what should i be doing", "what should i do next", "what needs doing", "whats to do",
    "what is there to do", "anything to do", "work to do", "tasks", "chores",
    "keep on top of", "tidy up",
)
_GARDEN_MONTHS = {
    1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring", 6: "summer",
    7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn", 12: "winter",
}
_GARDEN_SEASON_WORDS = {
    "spring": ("spring", "springtime", "march", "april", "may", "early in the year"),
    "summer": ("summer", "summertime", "june", "july", "august", "the hot weather"),
    "autumn": ("autumn", "fall", "september", "october", "november"),
    "winter": ("winter", "winters", "wintertime", "december", "january", "february"),
}
_GARDEN_NOW = re.compile(r"\bnow\b|\bat the moment\b|\bthis month\b|\bcurrently\b|"
                         r"\bright now\b|\btoday\b|\bthis week\b|\bthis weekend\b|"
                         r"\bthis time of year\b|\bat the minute\b|\bthese days\b")
# A thing you can be standing in front of, so a line that names one is a garden line whatever
# the chat was about before.
_GARDEN_THINGS = (
    "garden", "gardens", "lawn", "grass", "plot", "allotment", "allotments", "borders",
    "flowerbed", "flowerbeds", "flower bed", "flower beds", "beds", "bedding", "hedge",
    "hedges", "shrubs", "shrub", "veg", "vegetables", "veggie patch", "veg patch",
    "greenhouse", "pond", "compost", "beds and borders",
)


def _the_season_named(understood):
    """The season a garden line is about: the one it names, else the one it is now, else None."""
    line = _words(understood)
    for season in ("spring", "summer", "autumn", "winter"):
        if any(_has(line, word) for word in _GARDEN_SEASON_WORDS[season]):
            return season
    if _GARDEN_NOW.search(line):
        month = _this_month()
        if month is not None:
            return _GARDEN_MONTHS[month]
    return None


def _a_garden_line(understood):
    """True when the line, or the chat it is part of, is about the garden."""
    line = _words(understood)
    if any(_has(line, word) for word in _GARDEN_THINGS):
        return True
    topics = []
    for key in ("topic", "topics"):
        held = understood.get(key)
        if isinstance(held, str):
            topics.append(held)
        elif isinstance(held, (list, tuple, set)):
            topics.extend(str(one) for one in held)
    return "garden-and-plants" in topics


def _garden_jobs(memory, understood):
    """What needs doing in the garden in the season the line names, or None for another ask."""
    line = _words(understood)
    if not any(_has(line, word) for word in _GARDEN_JOBS):
        return None
    if not _a_garden_line(understood):
        return None
    season = _the_season_named(understood)
    if season is None:
        return None
    return JOBS_IN[season]


def _an_ask_about_now(understood):
    """True for a garden job ask that says "now" instead of naming a season.

    "what jobs can i do in the garden now" was the winter card: "jobs" is the only word the winter
    row and the line share, and its bias (there only to outrank the cold-snap row) is enough to
    beat the season row. The season row reads the month, so in November it answers autumn, which
    is the honest answer to "now". A line that names a season keeps the winter card.
    """
    line = _words(understood)
    if not _GARDEN_NOW.search(line):
        return False
    if not any(_has(line, word) for word in _GARDEN_JOBS):
        return False
    if not _a_garden_line(understood):
        return False
    for season in ("spring", "summer", "autumn", "winter"):
        if any(_has(line, word) for word in _GARDEN_SEASON_WORDS[season]):
            return False
    return _the_season_named(understood) is not None


def _not_about_now(understood):
    """The winter card answers the lines that are about winter; a "now" ask is the season row's."""
    return not _an_ask_about_now(understood)


ENTRIES.append(entry(
    "garden-jobs-in-a-season",
    (_GARDEN_JOBS,
     ("spring", "springtime", "march", "april", "may", "summer", "summertime", "june", "july",
      "august", "autumn", "fall", "september", "october", "november", "winter", "winters",
      "wintertime", "december", "january", "february", "now", "at the moment",
      "this time of year", "today", "this week", "this weekend", "at the minute")),
    _garden_jobs,
    # a frost tonight, a pond, a houseplant, a mower, a weed and a sick plant are other answers
    avoid=("frost", "frosts", "frosty", "forecast", "cold snap", "tonight", "fleece",
           "houseplant", "houseplants", "house plant", "monstera", "orchid", "pond",
           "mow", "mowing", "mower", "scarify", "scarifying", "scarifier", "prune my",
           "pruning", "sow", "sowing", "plant", "planting", "weeds", "weeding", "weed",
           "sick", "dying", "yellow", "yellowing", "disease", "pest", "pests", "slug",
           "snail", "snails", "christmas", "bedding", "hanging basket", "window box")))

# "how do i look after my garden in winter" was answered with the frost fleece because "garden"
# and "winter" are two of that row's words, and the rest of it - what to do in a wet, cold, empty
# garden - was a punt on main.
ENTRIES.append(entry(
    "garden-in-winter",
    (("garden", "gardens", "plot", "allotment", "allotments", "borders", "flowerbeds"),
     ("winter", "winters", "wintertime", "december", "january", "february", "cold months",
      "wet", "quiet", "nothing to do", "jobs", "job", "tidy", "tidy up", "put to bed",
      "over winter", "this time of year", "dark", "rain")),
    JOBS_IN["winter"],
    # a frost tonight, a pond, a lawn, a houseplant and a dead-looking shrub are other answers
    avoid=("frost", "frosts", "frosty", "freezing", "frozen", "cold snap", "forecast",
           "tonight", "cover", "fleece", "greenhouse", "pond", "lawn", "mow", "mowing",
           "houseplant", "houseplants", "house plant", "monstera", "orchid", "prune my",
           "dead", "dying", "sick", "yellow", "christmas",
           # a season named in the line is the season the person is asking about, so the quiet
           # winter row stands down for the other three: "garden jobs in spring" and "what
           # garden jobs are there in summer" were both this card, because "jobs" was the only
           # word it shared with the line
           "spring", "springtime", "march", "april", "may", "summer", "summertime", "june",
           "july", "august", "autumn", "september", "october", "november", "this spring",
           "this summer", "this autumn"),
    # "what jobs can i do in the garden now" is the season row's: this row's bias is here to
    # outrank the cold-snap row, and it was winning a "now" ask that says nothing about winter.
    guard=_not_about_now,
    # "garden" and "winter" are both frost words, so the quiet-season row has to outrank the
    # cold-snap row on the lines that name no frost at all
    bias=1))

# A cut Christmas tree was a punt both ways round - "how do i look after a christmas tree" and
# "how do i keep a christmas tree alive" - while "when should i take my christmas tree down" was
# already answered by the Twelfth Night row, which is a different question on the same noun.
ENTRIES.append(entry(
    "christmas-tree",
    # The bare word "tree" is not in the key: "how do i look after a lemon tree" and "how do i
    # care for a lemon tree in a pot" were told to stand the trunk in a bucket and saw a couple of
    # centimetres off it, which keeps a cut Christmas tree alive and says nothing about a tree in
    # a pot. A December word or a species name is what makes this the tree in the room.
    (("christmas tree", "christmas trees", "xmas tree", "the tree", "spruce", "fir",
      "nordmann", "norway spruce"),
     ("keep alive", "alive", "last", "longer", "drop", "dropping", "needles", "needle drop",
      "water", "watering", "look after", "care", "fresh", "dying", "best", "choose",
      "buy", "real tree", "stand", "base")),
    "A cut tree drinks about a litre a day, so stand it in a bucket of water, saw a couple of "
    "centimetres off the trunk first so it can take water up, and keep the base covered - a "
    "trunk that dries seals over and stops drinking. Keep it away from a radiator, a fire and "
    "the sunny window, and it will hold its needles for about four weeks instead of one. A "
    "Nordmann fir drops far less than a Norway spruce, which is the one that sheds as you bring "
    "it in. A potted tree with roots is a different animal: keep it cool and light in a porch "
    "or greenhouse, bring it in for no more than a week, and plant it out after Christmas.",
    # taking it down, the decorations, the lights and the recycling are other questions
    avoid=("take it down", "take my tree down", "twelfth night", "5 january", "6 january",
           "12th night", "dispose", "recycle", "recycling", "tip", "chuck", "lights",
           "fairy lights", "decorations", "baubles", "tinsel", "star", "buy a tree",
           "how much does a tree cost", "real or fake", "fake tree", "artificial"),
    # the bare word "tree" in the key took every tree in the garden, because a cut tree and a
    # growing one share the noun and nothing else: this stands the row down unless the line is
    # about the Christmas one
    guard=_a_christmas_tree))

# A garden tree is not the cut one either way round: "how do i choose a tree for my garden" and
# "how do i water my tree" were both the Christmas-tree card, which is about a trunk in a bucket.
ENTRIES.append(entry(
    "garden-tree",
    (("tree", "trees", "sapling", "saplings", "fruit tree", "fruit trees", "apple tree",
      "pear tree", "plum tree", "cherry tree"),
     ("plant", "planting", "planted", "choose", "choosing", "pick", "picking",
      "water", "watering", "how often", "prune", "pruning", "feed", "feeding", "stake",
      "stake it", "staked", "bare root", "bare-root", "when", "how", "which", "what",
      "small garden", "pot", "growing", "grow", "move", "moving", "far from", "distance")),
    _garden_tree,
    # the cut one, a tree that is already dying, and the tree in a shape or a diagram
    avoid=("christmas", "xmas", "spruce", "fir", "nordmann", "norway spruce", "needles",
           "needle drop", "tinsel", "baubles", "decorations", "cut tree", "cut my tree",
           "dead", "dying", "died", "dying back", "brown", "wilted", "treehouse", "tree house",
           "family tree", "decision tree", "route", "syntax tree", "genealogy",
           # "and tree nuts too" is a line about an allergy, said after one, and the memory
           # answer it belongs to was displaced by this row's "tree"
           "nut", "nuts", "tree nuts", "peanut", "peanuts", "allergic", "allergy",
           "allergies", "allergen", "intolerant"),
    # "how do i prune it" in a chat about a hedge, and a bare "the tree" with no garden word in
    # it, must not be read as this row
    guard=_a_garden_tree))

# A tree in a pot indoors is its own animal: "how do i look after a lemon tree" and "how do i care
# for a lemon tree in a pot" were the cut Christmas tree's answer, and nothing in the garden module
# covered citrus at all. What a person with a potted lemon wants is the opposite of the cut tree's
# advice: how to keep it alive for years, in the sunniest window, without overwatering it.
ENTRIES.append(entry(
    "citrus-in-a-pot",
    (("lemon tree", "lemon trees", "orange tree", "lime tree", "citrus", "citrus tree",
      "citrus trees", "calamondin", "kumquat", "lemon plant", "orange plant"),
     ("look after", "care", "cared", "keep alive", "alive", "indoors", "inside", "pot",
      "potted", "houseplant", "water", "watering", "overwater", "underwater", "feed",
      "feeding", "fertiliser", "fertilizer", "repot", "re-pot", "prune", "winter", "frost",
      "cold", "leaves", "leaf drop", "losing", "dropping", "yellow", "flower", "flowers",
      "fruit", "not fruiting", "no fruit", "best", "buy", "sun", "sunlight", "light",
      "compost", "soil", "sick", "dying")),
    'Lemons want the sunniest place you have - a south-facing windowsill, a conservatory or a '
    'patio against a warm wall - so give them six hours of direct light and turn the pot now and'
    'then so the whole plant grows evenly. Use a free-draining compost with a handful of grit or'
    'perlite, water when the top two or three centimetres of compost feels dry and far less in'
    'winter, and never stand it in a full saucer, because a potted lemon dies of soggy roots far'
    'more often than of thirst. Feed a citrus feed from March to September and nothing over the'
    'winter. Bring it indoors before the first frost, since it drops its leaves below about 5C,'
    'and prune lightly in spring once the fruit has set, because it flowers on new growth. A'
    'flower that opens indoors with no bees about wants a soft brush going over it by hand to'
    'set the fruit.',
    # A lemon in a recipe, a lemonade and the price of lemons are other questions. So is every
    # other tree in a pot: an olive, a fig and a bay want drier feet and hard pruning, so they
    # are not this row's line even though the shape of the answer is close.
    avoid=("recipe", "recipes", "juice", "juiced", "zest", "squeeze", "lemonade", "drizzle",
           "cake", "cakes", "curd", "marmalade", "how much", "price", "cost", "buy a lemon",
           "lemons cost", "bay leaf", "bay leaves", "olive oil", "tree surgeon")))

# Firewood and the log burner were not covered at all on main: "whats the best time to split
# firewood", "when should i split logs", "how long does firewood need to season", "how do i store
# firewood", "is my wood dry enough to burn" and "what wood is best for a log burner" were six
# search hedges, "how do i know if wood is seasoned" got the leather-and-board-oil card, "how long
# to dry logs before burning" got a blister card, "how do i split a log without an axe" and "how do
# i sharpen an axe" got a reading-a-graph card, and "should i cover my log pile" got the
# weighing-it-up line. It is one area with a handful of short answers, so it is one block of rows
# here, next to the rest of the garden and outdoor jobs.
ENTRIES.append(entry(
    "season-firewood",
    (("firewood", "fire wood", "logs", "log pile", "logs pile", "wood pile", "woodpile",
      "rounds", "log", "wood", "hardwood", "softwood"),
     ("season", "seasoning", "seasoned", "when", "best time", "what time of year", "how long",
      "ready to burn", "dry out", "drying", "leave it", "how many months")),
    # The one thing that decides the answer is when the wood is cut: in late winter it has the whole
    # summer to dry, and split wood dries about four times faster than a round does.
    "Split it in late winter or early spring, before the sap rises: a log cut then has the whole "
    "summer of sun and wind to dry and is ready for the fire by the autumn. Hardwood such as oak, "
    "ash and beech wants about twelve months and softwood about six to nine, and a split log dries "
    "roughly four times faster than a whole round - which is the reason to split everything now "
    "and stack it, rather than leave the rounds in a heap until you need them.",
    avoid=("cost", "price", "cheap", "how much is", "stove", "burner", "best wood", "what wood",
           # "how do i stop wood splitting when i nail it" holds "wood" and "when" and was told
           # when to split a log. A nail is joinery, and home_craft.py has that row.
           "nail", "nails", "nailed", "nailing", "pilot hole", "joist", "joists", "plank",
           "skirting", "floorboard", "floorboards",
           "which wood", "chainsaw", "axe", "hire", "kiln", "kiln dried", "delivered",
           "seasoning of a pan", "cast iron", "frying pan",
           # "how long between coats of wood stain" holds "wood" and "how long", which is this
           # row's key, and a log that needs seasoning is not a coat of stain. A finish put on wood
           # names the wood, and the coats name it too.
           "stain", "stains", "staining", "stained", "varnish", "varnishing", "varnished",
           "paint", "painting", "painted", "coats", "coat", "between coats")))

ENTRIES.append(entry(
    "wood-dry-enough",
    (("seasoned", "dry enough", "moisture", "wet wood", "damp wood", "green wood", "my wood",
      "the wood", "logs", "these logs", "firewood"),
     ("how do i know", "how can i tell", "is my", "are my", "ready", "dry", "wet", "damp",
      "meter", "moisture", "smoke", "smokes", "smoky", "smoking", "spitting", "hiss",
      "sizzle", "steam", "burn", "burning")),
    "Knock two split pieces together: well seasoned wood cracks like a bat on a ball, and green "
    "wood thuds. The ends of a dry log are pale, cracked and often dark-ringed, and a cheap "
    "moisture meter pushed into a freshly split face should read under 20 per cent. Burning wet "
    "wood is why a fire smokes, spits and blacks the glass, and it gives around half the heat, "
    "because most of the flame's energy goes on boiling the water out of the log instead of "
    "heating the room.",
    avoid=("store", "stack", "cover", "shed", "pallet", "buy", "price", "cost", "best wood",
           "which wood", "stove", "burner", "chimney", "flue")))

ENTRIES.append(entry(
    "store-firewood",
    (("firewood", "logs", "log pile", "wood pile", "woodpile", "kindling", "logs pile"),
     ("store", "storing", "stack", "stacking", "cover", "covered", "tarpaulin", "shed",
      "rain", "wet", "outside", "against the house", "keep dry", "how do i keep")),
    "Stack it off the ground on pallets or two rails, in a spot that gets sun and wind, and cover "
    "the top only - a tarpaulin over the whole pile holds the damp in and turns a drying pile into "
    "a rotting one. Keep it a wall's width away from the house so it is not a ladder for mice, and "
    "leave air gaps between the stacks rather than one solid wall of wood.",
    avoid=("cost", "price", "buy", "best wood", "which wood", "stove", "burner", "chimney",
           "season", "how long to dry", "dry enough", "moisture")))

ENTRIES.append(entry(
    "wood-for-a-burner",
    (("wood", "logs", "firewood", "timber", "log burner", "wood burner", "stove", "open fire"),
     ("best", "which", "what kind", "what sort", "what type", "should i burn", "good to burn",
      "safe to burn", "worth burning", "buy", "cheapest")),
    "Ash, oak, beech, hawthorn, hornbeam and birch are the best firewood: dense, slow burning, low "
    "in tar, and ash burns well even when it is not fully dry. Pine and other softwoods burn hot "
    "and fast and leave creosote in the flue, so they are for kindling rather than a night's burn, "
    "and never burn painted or treated timber, plywood, chipboard or driftwood - the fumes are "
    "poisonous and the salt and preservative wreck the flue.",
    avoid=("light", "lighting", "hard to light", "going out", "store", "stack", "season",
           "dry enough", "moisture", "price", "cost per", "chimney", "flue liner", "install")))

ENTRIES.append(entry(
    "sweep-the-chimney",
    (("chimney", "flue", "sweep", "sweeping", "soot", "creosote", "tar", "bird nest"),
     ("how often", "when", "how do i", "should i", "need", "worth", "cost", "price",
      "sweep", "swept", "clean", "cleaning", "blocked", "soot")),
    "Have the chimney swept once a year, before the heating season starts, and twice if it is your "
    "main heat or you burn wood - soot and creosote build up out of sight, and a blocked flue is "
    "how carbon monoxide gets into a room. A sweep costs about 40 to 80 pounds and gives you a "
    "certificate to keep for the insurance; while he is there, ask him to check the cowl and put a "
    "carbon monoxide alarm in the same room as the fire.",
    avoid=("how do i build", "chimney pot", "repoint", "render", "brick", "damp", "smoke test",
           "how do i stop it smoking", "fireplace", "install", "liner", "cost of a new")))

ENTRIES.append(entry(
    "light-the-fire",
    (("wood burner", "log burner", "woodburner", "stove", "open fire", "fireplace", "fire",
      "kindling"),
     ("light", "lighting", "lit", "light it", "keeps going out", "goes out", "wont stay in",
      "won't stay in", "hard to light", "struggle", "struggling", "smokes", "smoky")),
    "Lay it top-down: three or four split logs on the grate, a handful of kindling crossed on top, "
    "two firelighters, then light the kindling and leave the air control wide open for ten minutes "
    "before you close it down. A fire that will not catch is nearly always damp wood, kindling "
    "that is too big, or the air shut too early - small dry wood first, bigger on top, and heat "
    "the flue before you expect a flame.",
    avoid=("electrical fire", "chip pan", "house fire", "fire alarm", "smoke alarm", "firework",
           "wildfire", "campfire", "bonfire", "gas fire", "fire pit", "how do i put out",
           "extinguisher", "safety", "log burner cost", "install")))

ENTRIES.append(entry(
    "sharpen-an-axe",
    (("axe", "hatchet", "axe head", "splitting axe", "felling axe", "billhook"),
     ("sharpen", "sharpening", "sharpen it", "sharp", "blunt", "file", "filing", "hone",
      "grind", "grinding", "edge", "maintain")),
    "Clamp the head in a vice or hold the axe steady on a block and push a file away from the edge "
    "along the bevel, at the angle the bevel already has, until you feel a burr on the far side - "
    "then take two or three light strokes on that side to take it off. A file costs a few pounds "
    "and does less damage than a bench grinder, which heats the edge and takes the temper out of "
    "it; an axe only needs sharp enough to bite, not shaving sharp.",
    avoid=("chainsaw", "lawnmower", "mower blade", "secateurs", "shears", "knife", "chisel",
           "buy", "price", "cost", "which axe", "best axe", "handle", "rehandle")))

# "round" is a round of wood only when the line names the wood. The word is doing other jobs in
# "how do i round up the total", "how do i round to the nearest pound", "how do i get round the
# traffic" and "how do i fit the studying round work", and this entry's ask tuple is the words
# every question carries ("how do i", "how to", "how can i"), so each of those was answered with
# the axe and the chopping block. It is as wrong the other way: standing the card down on the bare
# word lost "how do i round a wooden post" and "how do i chop firewood", which it answers well.
# So the line has to name what is being cut - a log, firewood, a post, a stump, a branch - and a
# bare "round" counts only where the job is said too ("how do i split a round").
# The trailing \b matters: without it "ring" matched inside "ringing", so any line with
# "someone ringing" - a phone, a doorbell - named the wood and the axe answered it. The words
# are whole words or they are not the thing being cut.
_WOOD_WORDS = re.compile(
    r"\b(?:logs?|timber|firewood|wood|wooden|piece of wood|log pile|posts?|stumps?|branches?|"
    r"branch|trunks?|rings?|chopping block)\b")
_SPLITTING = re.compile(
    r"\b(?:splits?|splitting|chopp?ing|chop|wedges?|maul|axe|axes|hatchet|stuck|log splitter|"
    r"sawing|saw)")


# "Rings" in `_WOOD_WORDS` is a round of wood, and three other things own that word as well as
# the phone and the piercing the `avoid` list above names: a cooker's ring, something worn on a
# finger, and the mark a cup leaves. "how do i clean the rings on my cooker" and "... on the hob"
# were both the axe and the chopping block, while the hob-cleaning row that answers them was
# passed over. The wood is what the word means when nothing else claims it, so the other senses
# are named here and the round of wood stands down for them. This is a guard rather than three
# more `avoid` words because "burner", "stove" and "hob" are in good wood lines too ("how do i
# split logs for the wood burner"), and only a line whose one wood word is the "ring" itself can
# be about something else.
_RING_IS_NOT_WOOD = re.compile(
    r"\b(?:hob|hobs|cooker|cookers|stove|stoves|oven|ovens|burner|burners|element|elements"
    r"|ring main|wedding|engagement|wedding band|finger|fingers|jeweller|jewellery|jewelry"
    r"|gold|silver|diamond|tarnish|tarnished|worktop|worktops|counter|coffee table|cup|glass"
    r"|mug)\b")
# The wood words without "rings": a line naming any of them is still the wood's ("how do i split
# a log ring", "logs for the wood burner"). Only the "ring" on its own can be another sense.
_OTHER_WOOD = re.compile(
    r"\b(?:logs?|timber|firewood|wood|wooden|piece of wood|log pile|posts?|stumps?|branches?"
    r"|branch|trunks?|chopping block)\b")


def _splitting_a_log(understood):
    """True when the line is about a round of wood, not about going round something."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "text")).lower()
    if re.search(r"\brings?\b", said) and not _OTHER_WOOD.search(said) \
            and _RING_IS_NOT_WOOD.search(said):
        return False
    if _WOOD_WORDS.search(said):
        return True
    return bool(_SPLITTING.search(said) and re.search(r"\brounds?\b", said))


ENTRIES.append(entry(
    "split-a-log",
    (("log", "logs", "log round", "log rounds", "rounds of wood", "logs i have",
      "piece of wood", "log pile", "firewood"),
     ("split", "splitting", "chop", "chopping", "wedge", "maul", "axe", "how do i", "how to",
      "best way", "how can i", "without an axe", "stuck", "wont split", "won't split",
      "hard to split", "easier to split", "log splitter")),
    "Stand the round on a chopping block - a big flat stump - and bring the axe down through the "
    "middle, not at the edge: the ground swallows the force of a blow and the block gives it back. "
    "Knotty or wide rounds go with two steel wedges tapped in along the end grain, and a stubborn "
    "one is easier after a few weeks of drying. No axe at all means a wedge and a club hammer, or "
    "drill a line of holes down the face and hit the wood with a mallet.",
    # "ring" in the key is a ring of wood, and a nose ring is not one: "how do i clean my nose
    # ring" was answered with a chopping block and an axe. The thing in a piercing fences it off.
    avoid=("cost", "price", "buy", "which axe", "best axe", "sharpen", "handle", "season",
           "how long to dry", "store", "stack", "firewood for sale", "chainsaw", "stump",
           # A round of wood and the sound of a phone are the same word, and "ring"/"rings" is in
           # this key: "how do i stop my phone ringing at night" was the axe and the chopping
           # block. This is the same fence the hob rows carry for the same word.
           "phone", "phones", "mobile", "mobiles", "ringtone", "ringtones", "voicemail",
           "landline", "missed call", "missed calls", "doorbell", "door bell", "at night",
"piercing", "piercings", "nose ring", "nose stud", "septum", "earring", "ear ring",
           "belly bar", "hoop earring", "tragus", "helix")
    + RING_AS_A_CALL,
    guard=_splitting_a_log))

ENTRIES.append(entry(
    "chimney-smokes",
    (("chimney", "flue", "open fire", "wood burner", "log burner", "stove", "fireplace",
      "the fire"),
     ("smokes", "smoking", "smoke comes", "smoke coming", "blows back", "blowing back",
      "back into the room", "in the room", "downdraught", "down draught", "draught",
      "wont draw", "won't draw", "not drawing", "drawing")),
    "Smoke into the room is a cold flue, a blocked one or a pressure problem at the top: hold a "
    "rolled-up newspaper torch at the opening for a minute to warm the flue before you light it, "
    "and open a window a crack. If it still smokes once the fire is going, stop using it and get "
    "the sweep out, because a blocked or cracked flue lets carbon monoxide into the room. Smoke "
    "only when it is windy means the chimney needs a cowl, and smoke in a sealed room with an "
    "extractor fan running means it needs an air vent.",
    avoid=("how do i build", "chimney pot", "repoint", "render", "brick", "damp", "install",
           "liner", "sweep", "how often", "cost", "price", "santa")))

# A greenhouse is the one bit of the garden with its own climate, and the question that comes
# with it - how warm should it be, do I heat it, when do I open the vents - had no answer at all:
# "what temperature should i keep my greenhouse" and "how warm should my greenhouse be" were both
# a search hedge. The numbers are the same for every crop in it, so one row covers them.
_GREENHOUSE = ("greenhouse", "green house", "glasshouse", "polytunnel", "polytunnel")
_GREENHOUSE_ASK = ("temperature", "temperatures", "how warm", "how hot", "how cold", "warm",
                   "warmth", "heat", "heated", "heater", "heating", "degrees", "too hot",
                   "too cold", "vent", "vents", "venting", "ventilation", "frost", "frosts",
                   "freezing", "insulate", "bubble wrap", "minimum")

ENTRIES.append(entry(
    "greenhouse-temperature",
    (_GREENHOUSE, _GREENHOUSE_ASK),
    ("Aim for 15 to 25C by day: open the vents and the door at about 25C, and shut them again "
     "mid-afternoon so the heat is kept for the night, because a closed greenhouse is 5 to 10C "
     "warmer than the air outside. Tomatoes, cucumbers and peppers stop growing below about 12C "
     "and set no fruit below 15C, so a heater set to 10 to 12C keeps them alive rather than "
     "growing, and a max-min thermometer in the shade inside tells you what your own greenhouse "
     "is really doing."),
    # bias 1: the frost row keys "heat" with "greenhouse" too, because "how do i keep my
    # greenhouse warm" is one of its lines. A climate question - how warm, how hot, when to open
    # the vents - is this row's, and the numbers are the better answer to it; a frost night with
    # plants in it keeps its own row on the fleece and the cloche.
    bias=1,
    # a crop, a pest, the watering and the cleaning each have their own answer, and a window or a
    # conservatory in the house is not a greenhouse
    avoid=("water", "watering", "how often", "feed", "feeding", "fertiliser", "fertilizer",
           "whitefly", "aphid", "aphids", "red spider", "mould", "mouldy", "damping off",
           "clean", "cleaning", "wash", "glass", "pane", "panes", "broken", "repair", "paint",
           "lean-to", "conservatory", "windowsill", "houseplant", "houseplants", "recipe",
           "bake", "oven", "cook", "cooking", "grow", "growing", "sow", "sowing", "plant",
           "planting", "what can i grow")))
# Ivy and brambles are the two wild things people ask about by name, and neither is a prune: an
# ivy is cut off at the base and pulled off, and a bramble comes back from its crown and from a
# tip that touches the soil. Nothing in the table answered "the ivy is taking over the fence"
# (the state was handed back as "Ivy on your wall - I'll remember that") or "my brambles are
# taking over", and "the ivy is taking over my wall" reached the painting estimate because of the
# wall. One row each, because the two cuts are different jobs.
ENTRIES.append(entry(
    "ivy-taking-over",
    (("ivy", "english ivy", "common ivy", "climbing ivy", "ivy plant"),
     GONE_WILD + ("wall", "walls", "fence", "fences", "tree", "trees", "shed", "garage",
                  "house", "brick", "render", "gutter", "gutters", "roof", "window",
                  "windows", "get rid", "rid of", "control", "kill", "remove", "stop",
                  "growing", "spreading", "damage", "damaging", "mortar", "dangerous",
                  "pull it down", "pull down", "cut back")),
    "Ivy is cut off rather than pruned: saw through every stem where it meets the ground, leave "
    "the top to die back for a few weeks, then pull it off - pulling live ivy takes render and "
    "mortar with it. It comes back from any root left in the soil, so dig the stump out and pull "
    "up the new shoots. On a wall you want to keep it on, hold it back 30cm from the gutters, "
    "windows and the roofline, and it does the brick no harm at all.",
    # a houseplant called an ivy, a poison-ivy rash and a climbing plant that is not ivy are
    # other questions, and "ivy" alone is also a name
    avoid=("devil's ivy", "devils ivy", "devil ivy", "pothos", "houseplant", "houseplants",
           "house plant", "indoor", "pot", "pots", "windowsill", "poison ivy", "rash",
           "itchy", "ivy league", "ivy bridge", "my mate ivy", "called ivy"),
    bias=1))
ENTRIES.append(entry(
    "brambles-taking-over",
    (("bramble", "brambles", "blackberry bush", "blackberry patch", "blackberries growing",
      "thorny"),
     GONE_WILD + ("garden", "border", "bed", "beds", "fence", "hedge", "plot", "allotment",
                  "lawn", "back", "get rid", "rid of", "control", "kill", "remove", "clear",
                  "dig out", "dig up", "cut back", "cutting", "spread", "spreading")),
    "Brambles come back from the crown and from any tip that roots where it touches the soil, so "
    "cutting the tops only makes them shrubby. Cut the stems to the ground, dig the crown out "
    "with a fork and pull up the tips that have rooted further out, and do it before they flower "
    "so nothing seeds. Then keep cutting the regrowth every few weeks through the season: a "
    "bramble starved of leaves runs out of root by the second year.",
    # a blackberry is also a phone and a fruit to pick
    avoid=("blackberry phone", "blackberry key", "phone", "iphone", "android", "sim",
           "picking blackberries", "bramble jelly", "bramble jam", "crumble", "recipe",
           "cook", "eat", "fruit"),
    bias=1))

# The frost already happened, and this is the question after it: "my basil froze overnight",
# "the frost has blackened my leaves", "my potatoes got frosted", "will my plant recover after
# the frost". On main those lines got a listening line, a baked potato recipe, a chicken salad
# and the covering job, because "froze", "frosted" and "blackened" are nobody's key words and
# the row that does answer frost lines answers what to put over things *tonight*. The answer
# after the fact is mostly what not to do: wait, scratch the stem, leave it be.
_FROST_ALREADY = (
    "froze", "frozen", "frosted", "frostbitten", "frost bitten", "blackened", "black leaves",
    "burnt by the frost", "burnt by frost", "burnt by the cold", "hit by the frost",
    "hit by frost", "caught by the frost", "caught by frost", "the frost damaged",
    "frost damage to my", "any frost damage", "much frost damage",
    "damaged by the frost", "damaged by frost", "killed by the frost", "killed by frost",
    "frost has", "frost got", "frost got at", "got frosted", "got frost",
    "the frost took", "lost to the frost", "after the frost", "from the frost", "by the frost",
    "frost last night", "frost overnight", "the frost got", "died in the frost",
    # "my plants are in the frost" is a frost they are in now, not one they have come through:
    # the pointing-at-a-frost words only count once the frost is behind us.
    "died back in the frost", "were in the frost", "was in the frost", "left in the frost",
    "left them in the frost", "sat in the frost", "stood in the frost",
)
_FROST_AFTERMATH = (
    "plant", "plants", "leaves", "leaf", "stem", "stems", "shoot", "shoots", "growth",
    "bud", "buds", "seedling", "seedlings", "flowers", "flower", "tomato", "tomatoes",
    "courgette", "courgettes", "potato", "potatoes", "beans", "bean", "basil", "herbs",
    "mint", "rosemary", "geraniums", "dahlias", "bedding", "shrubs", "shrub", "tree",
    "citrus", "olive", "banana plant", "tree fern", "succulents", "cacti", "garden",
    "my garden", "the garden", "allotment", "veg", "vegetables", "crop", "crops",
    "recover", "recovery", "survive", "come back", "come round", "dead", "died", "dying",
    "cut back", "cut it back", "prune", "pruning", "trim", "limp", "wilted", "drooping",
    "what now", "now what", "will it", "will they", "should i",
)
_FROST_AFTER_THE_FACT = (
    "Nothing today: leave the blackened leaves and soft stems alone, because a plant that looks "
    "dead after a frost often has live buds further down and cutting now tells you nothing. "
    "Give it about a fortnight, then scratch the stem or the bark with a fingernail - green "
    "underneath means it is alive and can be cut back to just above a live shoot, brown and dry "
    "means that part has gone. Water it, keep it out of the next cold night, and don't feed or "
    "repot something that is still in shock; new growth is the sign it is worth keeping."
)


def _the_frost_already_bit_something(understood):
    """True when the line is about something growing that the frost has already damaged."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    said = said.replace("\u2019", "'")
    return _says_one_of(said, _FROST_ALREADY) and _says_one_of(said, _FROST_AFTERMATH)


ENTRIES.append(entry(
    "frost-damage-already",
    (_FROST_ALREADY, _FROST_AFTERMATH),
    _FROST_AFTER_THE_FACT,
    # the freezer table answers what to do with frozen food, the pond row the ice and the car row
    # a frosted windscreen. "frosting" is deliberately not here: it reduces to "frost", the same
    # form as "frosted", so it vetoed the very lines this row is for. The cake rows need no word
    # here - a cake line names no damage.
    avoid=("freezer", "frozen peas", "frozen veg", "frozen vegetables", "fridge", "thaw",
           "defrost", "refreeze", "open bag", "packet", "windscreen", "car", "cars", "pond",
           "fish", "beer", "glass",
           "freeze tomatoes", "freeze the", "can i freeze", "how do i freeze",
           # A frost coming is the covering advice, not this card: "how do i protect my plants in
           # the frost" and "my plants are in the frost" were answered "nothing today: leave the
           # blackened leaves alone", which is prevention answered with do-nothing.
           "protect", "protecting", "cover", "covering", "fleece", "cloche", "bring them in",
           "bring it in", "keep them warm", "forecast", "tonight", "tomorrow night",
           # and a frosted potato somebody wants to eat is a food question, not the garden's
           "safe to eat", "can i eat", "is it safe", "still eat", "eat them", "eat it"),
    bias=2,
    # the damage words carry it, so the guard is only about what was damaged: a food line
    # ("frozen peas in the freezer") names nothing that grows
    guard=_the_frost_already_bit_something))


# "any ideas to make my garden look better" and "how do i make my garden look better" reached
# nothing at all, so the composer's tips branch asked "What have you tried so far?" back at
# somebody who wanted ideas. The card is the ordinary "it looks tired" question - not a weed, a
# lawn, a frost, a sowing or a job too big for an afternoon - and the ask has to be there, because
# "my garden is a mess" on its own is news the store keeps.
ENTRIES.append(entry(
    "garden-looks-tired",
    # an allotment is somebody else's question (how much time it takes, whether the waiting
    # list is worth it), so it is not a key here
    (("garden", "gardens", "back garden", "front garden", "borders", "flowerbeds", "plot",
      "yard", "outdoor space"),
     ("look better", "looks better", "look nicer", "look nice", "look good", "looks good",
      "improve it", "improve my", "improve the", "make it nicer", "make it look", "ideas",
      "what should i do", "cheap", "without spending", "pride")),
    "Tidy the outline first, because a garden reads as untidy at its edges before its middle: "
    "cut the lawn edge right round with a half-moon edger, clear the path, and weed the first "
    "foot of border. Then buy three plants and no more - something tall, something scented by "
    "the door, and something that flowers for months - in pots if the soil is poor. Bark or "
    "gravel over bare soil is the cheapest thing that makes a garden look finished.",
    ask=("look", "looks", "idea", "ideas", "what", "how", "where", "tidy", "improve", "make",
         "cheap", "start", "nice", "better"),
    guard=_names_the_garden,
    # a weed, a lawn, a frost, a pond, a fence, something to sow and a gardener's bill are all
    # other questions, and each of them names its own thing in the line
    avoid=("weed", "weeds", "weeding", "dandelion", "nettle", "nettles", "bindweed", "moss",
           "lawn", "mow", "mowing", "mower", "turf", "grass seed", "re-seed", "scarify",
           "scarifying", "aerating", "frost", "frosts", "frozen", "cold snap", "winter",
           "snow", "pond", "fish", "fence", "fencing", "shed", "decking", "patio",
           "paving", "drive", "driveway", "raised bed", "greenhouse", "polytunnel",
           "slugs", "snails", "foxes", "fox", "rats", "squirrel", "deer", "cat", "cats", "dog",
           "dogs", "hire", "gardener", "how much", "cost", "price", "quote", "landscaper",
           "allotment", "allotments",
           # a line that names plants, flowers or a shrub is asking about those, and one that
           # says there is no garden at all has no borders to tidy
           "plant", "plants", "planting", "flower", "flowers", "shrub", "shrubs", "bulb",
           "bulbs", "hanging basket", "window box", "no garden", "without a garden",
           "flat", "balcony", "indoors", "inside the house",
           # a body that hurts after a day in the garden is the injury card's question, and
           # "what should i do" put those lines here
           "hurts", "hurt", "aching", "ache", "aches", "pain", "painful", "sore", "back",
           "knees", "knee", "shoulder", "shoulders", "wrist", "sprain", "strain", "injury",
           # a garden that is a mess is the start-of-the-year question, and garden-start
           # answers it with one bed at a time: "my garden looks a mess" is a job, not a look
           "mess", "messy", "overgrown", "neglected", "jungle", "where do i start",
           "where to start", "how do i start", "get started", "tidy up", "tidy", "sort out",
           "clear",
           "sow", "sowing", "seed", "seeds", "plant out", "prune", "pruning", "cut back",
           "hedge", "hedges", "trim", "climbing", "climber", "vegetable", "veg", "potato",
           "tomato", "tomatoes", "grow", "growing", "compost", "bark", "mulch", "when should"))
)


# A plant chosen for a room with no window is its own question, and on main it got nothing: "i want
# a plant for the bathroom" was the listening line and "theres no window in there" the same, so the
# one thing the person needed - which plants hold on in the dark, and that they want less water -
# never came. The row is a plant word against the room, because the room is what makes it the
# question; the plant words that already have care rows of their own (yellow leaves, brown tips,
# light) are untouched, and an outdoor bed or a garden stands the row down.
ENTRIES.append(
    entry("plant-for-a-windowless-room",
          (("plant", "plants", "houseplant", "houseplants", "house plant", "house plants",
            "pot plant", "pot plants", "pothos", "fern", "ferns", "orchid", "orchids", "palm",
            "snake plant", "zz plant", "peace lily", "spider plant", "green"),
           ("bathroom", "bathrooms", "loo", "toilet", "en suite", "ensuite", "shower room",
            "hallway", "hall", "landing", "cellar", "basement", "cupboard", "shelf", "shelves",
            "no window", "no windows", "windowless", "without a window", "no natural light",
            "no light", "dark room", "dark corner", "dark hallway", "window in there")),
          "For a room with no window, take the plants that cope with low light: pothos, snake "
          "plant, ZZ plant, peace lily and spider plant will all hold on, and a bathroom's steam "
          "suits a fern. Everything slows down in the dark, so water far less than the label says "
          "- every two to three weeks, once the top of the compost is dry - or the roots rot. If "
          "there is no daylight at all, no plant will live there: a lamp left on for twelve hours "
          "is what keeps one going, and a good fake is the honest answer for a cellar.",
          # an outdoor bed, a garden or a houseplant question about leaves is not this one
          ask=("bathroom", "loo", "toilet", "ensuite", "en suite", "shower room", "hallway",
               "hall", "landing", "cellar", "basement", "cupboard", "shelf", "shelves",
               "window", "windowless", "room", "corner", "flat", "house", "home"),
          avoid=("tomato", "tomatoes", "basil", "lawn", "grass", "tree", "trees", "rose", "roses",
                 "cucumber", "courgette", "pepper", "chilli", "outside", "garden", "gardens",
                 "border", "flowerbed", "flower bed", "allotment", "outdoor", "outdoors",
                 "shrub", "shrubs", "hedge", "hanging basket", "veg patch", "vegetable patch",
                 "yellow", "brown tips", "drooping", "wilted", "repot", "repotting",
                 "overwater", "overwatering", "root rot", "fungus gnat", "gnats",
                 "smell", "smells", "smelly", "damp", "mould", "mold", "condensation", "extractor",
                 "lamp", "ceiling light", "light bulb", "headlight", "grow light"),
          bias=2))
