"""How long a vegetable takes, and what "done" looks like when it gets there.

One domain of its own so its many vegetable names cannot change how rare a word is inside
another domain's keys (lookup.entries points that out: a new domain may not take a point away
from an entry somewhere else).

The boiling and steaming times of the vegetables `cooking.py` does not already answer:
cauliflower, carrots, cabbage, swede, leek, courgette, asparagus, sweetcorn, spinach, kale,
butternut squash, celeriac, mange tout, beetroot, turnip, fennel, pak choi and spring greens.
"how long does cauliflower take to boil" was a fallback before this table.
"""

import re

from .lookup import entry, tokens

ANSWERS = ("cooking", "food-and-drink")


# How long a vegetable takes is the same fact however the line is worded, so it is one table:
# the vegetable, the boiling time, and what "done" looks like. cooking.py already answers the
# vegetables a person is most likely to ask about (broccoli, peas, potatoes, sprouts, parsnips,
# sweet potato); these are the rest, and the ones that used to fall back - `how long does
# cauliflower take to boil` was a shrug.
def _phrase_in(text, phrase):
    """True when the phrase is in the line, on word boundaries ("soft" is not "soften")."""
    return bool(re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text))


VEG_TIME = (
    (("cauliflower",),
     "6 to 8 minutes for florets in already boiling salted water, 12 to 15 for a whole small "
     "one, and it is done when a knife goes into the stalk with no resistance. Steamed, give it "
     "2 or 3 minutes more."),
    (("carrot",),
     "10 to 15 minutes for thick coins, 8 for thin ones, 20 for whole carrots, in already "
     "boiling salted water. They are done when a knife slides in easily - a little bite is "
     "better than soft, and they go on cooking once drained."),
    (("cabbage",),
     "5 to 8 minutes for shredded cabbage in already boiling salted water, and less for the "
     "loose outer leaves. It is done when it has wilted and lost its raw edge but still has "
     "some bite; overcook it and it turns sweet and grey."),
    (("swede",),
     "25 to 30 minutes in 3cm chunks in boiling salted water, or 40 to 50 minutes whole. The "
     "knife test is the one that counts: it should go in with no resistance at all, because "
     "slightly underdone swede is hard and watery."),
    (("leek",),
     "6 to 8 minutes in thick rings, 3 to 4 if you slice them thin, in boiling salted water. "
     "Rinse the grit out from between the layers first - leeks hold soil better than any other "
     "vegetable - and stop while they still hold their shape."),
    (("courgette",),
     "3 to 4 minutes in boiling salted water, and no more: it is mostly water, so it goes from "
     "just right to mush fast. Better still, fry thick slices in a little oil for the same time "
     "- boiled courgette tastes of very little."),
    (("asparagus",),
     "3 to 5 minutes depending on thickness, standing up in a pan with the tips out of the "
     "water if you can, or in a wide pan. It is done when a knife goes into the stalk - bend one "
     "and it should still have some spring."),
    # The two artichokes are different vegetables and needed rows of their own: nothing in the
    # table answered "how do i cook artichoke" or "how do i cook jerusalem artichokes" (the
    # artichoke card in cooking.py is the what-can-i-make-with one), and "how long do i boil
    # artichokes" was a search hedge.
    (("globe artichoke", "globe artichokes", "artichoke", "artichokes"),
     "25 to 35 minutes whole in already boiling salted water, standing up in a deep pan with the "
     "tips out of the water if they fit. It is done when a leaf near the middle pulls away "
     "easily; drain it upside down so the water runs out of the leaves."),
    (("jerusalem artichoke", "jerusalem artichokes", "sunchoke", "sunchokes"),
     "10 to 12 minutes in already boiling salted water, scrubbed and cut into even pieces, and it "
     "is done when a knife goes in with no resistance at all. Roasting suits it better than "
     "boiling - 25 to 30 minutes at 200C (180C fan) - because it goes sweet and nutty at the "
     "edges."),
    (("sweetcorn", "corn on the cob", "corn cob"),
     "5 to 8 minutes for a cob in boiling unsalted water (salt makes the kernels tough), 4 to 5 "
     "from frozen. It is done when the kernels are bright yellow and a sharp knife cuts one "
     "easily."),
    (("spinach",),
     "1 to 2 minutes, and that is generous: put it in boiling water, push it under, and take it "
     "out as soon as it has wilted. Spinach is nearly all water, so longer only means losing "
     "it - squeeze it out and season it after."),
    (("kale",),
     "3 to 5 minutes in boiling salted water, stalky pieces first, and 6 to 8 if you want it "
     "soft enough for a soup. Strip the tough stems out before it goes in, and drain it well - "
     "kale holds a lot of water."),
    (("butternut squash", "squash"),
     "15 to 20 minutes in 3cm chunks in boiling salted water, or 25 to 30 in bigger pieces. It "
     "is done when a knife slides in with no resistance; roast it instead if you want it sweet "
     "and caramelised rather than watery."),
    (("celeriac",),
     "15 to 20 minutes in 2cm chunks in boiling salted water with a squeeze of lemon, which "
     "keeps it pale. It is done when a knife slides in easily, and it makes a good mash with "
     "butter and plenty of pepper."),
    (("mange tout", "mangetout", "sugar snap"),
     "2 to 3 minutes in boiling salted water, then straight into cold water so they stay "
     "bright. They are done when they are hot through and still squeak when you bite one - the "
     "pod is the point."),
    (("french beans", "green beans", "runner beans", "string beans"),
     "4 to 6 minutes for french beans, 5 to 7 for runner beans, in boiling salted water. They "
     "are done when a bean bends without snapping; top and tail them and string the runners "
     "first."),
    (("broad beans", "broad bean", "fava beans"),
     "2 to 3 minutes for small ones and 4 to 5 for big ones, in boiling salted water, then slip "
     "the grey skins off if they are big. They are done when a bean is tender and tastes sweet, "
     "not floury."),
    (("kohlrabi",),
     "12 to 15 minutes in wedges or 20 to 25 whole, peeled, in boiling salted water - it is "
     "done when a knife slides into the middle with no resistance. Steaming takes the same time "
     "and keeps more of the sweetness."),
    (("beetroot",),
     "45 to 60 minutes whole and unpeeled in boiling water, 25 to 30 if you cut it into wedges. "
     "A knife should slide in with no resistance, and the skin rubs off under cold water once "
     "it is cool enough to handle."),
    (("turnip",),
     "15 to 20 minutes in 3cm chunks in boiling salted water, and 25 to 30 whole. It is done "
     "when a knife goes in easily; drain it well, because turnip holds water and a wet mash is "
     "a sad mash."),
    (("fennel",),
     "8 to 10 minutes in wedges in boiling salted water, cut through the root so they hold "
     "together. It is done when a knife goes into the thickest part; boiled fennel goes sweet "
     "and soft, and a squeeze of lemon at the end keeps it fresh."),
    (("pak choi", "pak choy", "bok choy"),
     "2 to 3 minutes, halved lengthways, in boiling salted water - the leaves wilt almost at "
     "once. Better in a hot pan with a little oil, garlic and soy for the same 3 minutes."),
    (("spring greens", "collard", "greens"),
     "4 to 6 minutes shredded in boiling salted water, stalky bits first. They are done when "
     "they are tender but still green; drain them well and dress with butter or a little oil."),
)

# How to cook one, for the lines that ask how rather than how long. It is the same table's
# second fact, so it is looked up by the same vegetable name: "how do i cook cabbage" was a
# hedge while its keeping, its freezing and its boiling time were each answered. The sentences
# below carry their own times, because a method with no time is not an answer to it.
VEG_HOW = {
    "carrot": "peel or just scrub them, cut into batons, and boil or steam for 6 to 8 minutes "
              "until a knife goes in easily. Roast batons at 200C (180C fan) for 25 to 30 "
              "minutes with oil and a little honey. Whole small ones take 10 to 12 minutes "
              "boiled, and older carrots are sweeter and take longer.",
    "cabbage": "shred it and cook it briefly, or it goes grey and soft: boil or steam 4 to 5 "
               "minutes, or fry it in butter for 5 to 6 with a splash of water and the lid on "
               "for the first half. Salt at the end. Red cabbage is the exception and wants a "
               "slow braise of 45 minutes or more, with vinegar and something sweet.",
    "spinach": "it needs seconds, not minutes: wash it, put it in a hot pan with a knob of "
               "butter and stir for 1 to 2 minutes until it has just collapsed, then drain off "
               "the water it gives. Boiling it makes it slimy; squeeze it dry and dress it with "
               "butter, nutmeg or a little garlic.",
    "asparagus": "snap off the woody end of each spear (it breaks where it should), then boil "
                 "or steam 3 to 4 minutes for thin spears or 5 to 6 for fat ones, or roast at "
                 "200C (180C fan) for 10 to 12 minutes with oil, salt and lemon. It is done when "
                 "a knife goes in with no crunch left.",
    "leek": "slice it first, then wash it: grit hides between the layers, so swill the slices in "
            "a bowl of water and lift them out. Sweat them in butter with the lid on for 8 to 10 "
            "minutes, stirring now and then, until soft but not browned, and a splash of water "
            "stops them catching. They go sweet, and they are the base of potato and leek soup.",
    "courgette": "slice them about 1cm thick, salt them for 10 minutes and pat them dry if you "
                 "want them firm, then fry in a hot pan for 3 to 4 minutes a side until golden. "
                 "To roast, toss in oil and bake at 200C (180C fan) for 20 minutes. Don't crowd "
                 "the pan: they steam rather than brown.",
    "kale": "strip the leaves off the stalks, then either steam 4 to 5 minutes until tender, or "
            "toss with oil and salt and roast at 180C (160C fan) for 12 to 15 minutes until the "
            "edges crisp. Raw kale is fine in a salad if you massage it with oil and lemon for a "
            "minute first, which softens it.",
    "swede": "peel and cube it, then boil for 20 to 25 minutes until it mashes easily, and mash "
             "it with butter, salt and pepper - a little cream or a knob of butter takes away the "
             "sharpness. It roasts well too, in 2cm cubes at 200C (180C fan) for 30 to 35 "
             "minutes.",
    # "how do i cook artichoke" and "how do i cook jerusalem artichokes" were a search hedge
    # each: the artichoke card in cooking.py is the what-can-i-make-with one, so nothing
    # answered the how-to. They are two different vegetables with two different methods, so
    # the globe one stands down on the Jerusalem one's name.
    "globe artichoke": "cut the top inch off, snip the points off the outer leaves, and boil or "
                       "steam 25 to 35 minutes until a leaf near the middle pulls away easily. "
                       "Eat the leaves dipped in butter or vinaigrette, then scrape out the "
                       "fuzzy choke and eat the heart. To roast, halve them, oil the cut sides "
                       "and pack them cut down in a dish at 200C (180C fan) for 25 to 30 "
                       "minutes with a splash of water and a lid for the first half.",
    "jerusalem artichoke": "scrub them instead of peeling, since the skin is thin, and roast "
                           "them 25 to 30 minutes at 200C (180C fan) in oil, or boil 10 to 12 "
                           "minutes and mash them with butter like potato: they go sweet and "
                           "nutty fast, so test early. A squeeze of lemon or a splash of vinegar "
                           "keeps them from discolouring, and start with a small portion, "
                           "because they earn their other name.",
}

# Vegetables with a method and no boiling time of their own: a mushroom is not boiled, and a
# green bean is a fresh bean rather than the dried pulse the soaking entry answers with.
VEG_HOW_EXTRA = (
    (("green beans", "runner beans", "french beans", "string beans", "fine beans"),
     "top and tail them, and slice runner beans thinly, then boil or steam 4 to 5 minutes for "
     "green beans or 5 to 7 for runner beans: they should still squeak. Drain them and toss with "
     "butter or a little garlic. Old runner beans have strings and hard seeds, so slice them "
     "fine and cook them a few minutes longer."),
    (("mushroom", "mushrooms", "button mushrooms", "chestnut mushrooms"),
     "get the pan hot and add them dry first for a minute so they give up their water, then add "
     "butter or oil and cook 4 to 5 more minutes until golden. Wipe or rinse them quickly and "
     "dry them - either is fine - and don't crowd the pan or they boil in their own juice. "
     "Season at the end, not the start."),
)

# The words that make a line a how-to-cook question. A time word beats them: "how long do i
# cook cabbage" is the table's timing answer, not this one. A named method beats them too, so
# "how do i roast carrots" stays with the roast entries.
VEG_HOW_ASKS = ("cook", "cooking", "cooked", "prepare", "prep", "prepare", "boil", "boiled",
                "boiling", "steam", "steamed", "steaming", "best way", "method", "properly")

# The named methods, which have their own entries and are not "how do i cook it at all".
VEG_NAMED_METHOD = ("roast", "roasted", "roasting", "oven", "bake", "baked", "baking", "fry",
                    "fried", "frying", "grill", "grilled", "air fryer", "airfryer",
                    "microwave", "barbecue", "bbq", "slow cooker", "pressure cooker")

# A vegetable timing is not an answer about roasting, freezing, growing or calories. Those
# lines belong to the entries that own them, so this entry stands down and lets them through.
VEG_OTHER = (
    "roast", "roasted", "roasting", "oven", "bake", "baked", "baking", "fry", "fried",
    "frying", "grill", "grilled", "air fryer", "microwave", "barbecue", "bbq", "soup",
    "puree", "mash", "fridge", "freezer", "keep", "keeps", "last", "leftovers",
    "leftover", "calories", "calorie", "healthy", "health", "protein", "carb", "carbs",
    "vitamin", "vitamins", "iron", "dog", "dogs", "cat", "cats", "rabbit", "plant",
    "plants", "planting", "grow", "growing", "garden", "allotment", "seed", "seeds",
    "buy", "buying", "cost", "price", "cheap", "shop", "supermarket", "market",
    "recipe", "allergy", "allergic", "baby", "weaning", "blw", "diet", "diabetes",
    "sugar", "barely", "raw", "purple", "yellow", "brown", "mouldy", "gone off",
    "gone soft", "went soft", "gone limp", "limp", "bendy", "rubbery", "sprouting",
    "sprouted", "wilted", "wilt", "slimy",
    # a spaghetti squash is a different vegetable with its own answer (roast it, then fork it
    # into strands), not the butternut row
    "spaghetti squash", "acorn squash", "pattypan",
)

# The words that make a line a question about *how long* rather than about *how*. "how do i cook
# cauliflower" is answered on main with the whole-head roast, which is a good answer to it;
# "how long do i cook cauliflower" is this table's. Every real timing question has one of these
# in it, so requiring one costs nothing and keeps the method questions with their own entries.
VEG_TIME_WORDS = ("how long", "long", "minutes", "mins", "minute", "time", "times", "hour",
                  "hours", "tender", "done", "ready", "take", "takes", "need", "needs")

# The words that are another question wherever they sit, and the ones that only are when they
# sit beside the vegetable (a method, a way of keeping it).
VEG_NOT_FOR_US = (
    "fridge", "keep", "keeps", "keeping", "last", "lasts",
    "leftovers", "leftover", "calories", "calorie", "healthy", "health", "protein", "carb",
    "carbs", "vitamin", "vitamins", "iron", "dog", "dogs", "cat", "cats", "rabbit", "plant",
    "plants", "planting", "grow", "growing", "garden", "allotment", "seed", "seeds", "buy",
    "buying", "bought", "cost", "price", "cheap", "shop", "supermarket", "market", "allergy",
    "allergic", "baby", "weaning", "diet", "diabetes", "sugar", "mouldy", "gone off",
    "gone soft", "went soft", "gone limp", "limp", "bendy", "rubbery", "wilted", "wilting",
    "slimy",
    # "sprouting" is an onion past its best, but the loose forms reach "sprouts": that word
    # made every brussels-sprouts line another entry's question, and "roast brussels sprouts
    # in the oven" was a search hedge. The phrase is what the question actually says.
    "are sprouting", "is sprouting", "have sprouted", "has sprouted", "gone to seed",
    # "when do i pick my sweetcorn" and "when do i harvest the corn" are the garden's question:
    # the row knows how long to boil it, not when it is ripe in the field.
    "harvest", "harvesting", "pick", "picking", "picked", "ripe", "ripen", "ripened",
    # "when are my courgettes ready" reads as a method line without this: the row knows how
    # long to boil a courgette, and ready-to-pick is the garden's question the same way
    # "when do i pick" is.
    "when are", "are my", "are they ready", "ready to pick",
    # A soaking question is about the dried pulse or bean, and this table only knows how long a
    # fresh vegetable takes in the pan: "how long do i soak broad beans" was answered with 2 to
    # 3 minutes in boiling water. The dried-bean row in cooking.py is the one that knows.
    "soak", "soaks", "soaking", "soaked", "overnight", "dried", "dry",
    # A vegetable somebody has said they do not like is not one to cook: "i dont like mushrooms
    # what can i cook" got the method for frying mushrooms. The dislike is the meal question's
    # (what to cook instead), so every vegetable row stands down on it.
    "dont like", "don't like", "do not like", "doesnt like", "doesn't like",
    "do not like them", "do not like it", "does not like them", "hate", "hates", "hated",
    "cant stand", "can't stand", "not a fan", "fussy",
    "wont eat", "won't eat", "will not eat", "wont touch", "won't touch",
)

# The words that make the gap between a method word and the vegetable a question about the time
# rather than about the method: "im doing a roast, how long do leeks take to cook".
VEG_ASK_BETWEEN = ("how", "long", "time", "times", "minutes", "mins", "take", "takes")

# The words that carry no method of their own, so "carrots take to roast" reads as "carrots
# roast" and the roasting is the question, not the boiling time.
VEG_FILLER = ("take", "takes", "took", "to", "for", "in", "on", "the", "a", "an", "oven",
              "when", "at", "should", "i", "you", "do", "need", "long", "how")
# A way of cooking sitting in the middle means the method was named after all, and those words
# are what this row answers: "how long do leeks take to cook in a roast" is a cooking time.
VEG_COOK = ("boil", "boiled", "boiling", "steam", "steamed", "steaming", "cook", "cooked",
            "cooking", "fry", "fried", "frying", "grill", "grilled", "simmer", "simmered")


def _takes_to(words, position, spot):
    """True for "carrots take to roast" and "carrots take in the oven", and nothing else."""
    between = words[position + 1:spot]
    if not between or not all(word in VEG_FILLER for word in between):
        return False
    if any(word in VEG_COOK for word in between):
        return False
    return any(word in ("take", "takes", "took") for word in between)


VEG_ASKS = ("boil", "boiled", "boiling", "steam", "steamed", "steaming", "cook",
            "cooked", "cooking", "how long", "long", "time", "times", "minutes",
            "mins", "tender", "done", "ready", "take",
            # "how do i prepare leeks" and "whats the best way to cook cabbage" are the same
            # how-to question as "how do i cook cabbage", so they have to reach the row too.
            "prepare", "prep", "best way", "method", "properly")

def _near(text, phrase):
    """Where the phrase sits among the words of the line, or None.

    The plural counts as the same word: "how long do i roast carrots" has the method word next
    to the vegetable, and reading "carrot" alone would have missed it.
    """
    wanted = str(phrase).lower()
    for index, word in enumerate(str(text).lower().replace("'", " ").split()):
        if word == wanted or word == wanted + "s" or word + "s" == wanted:
            return index
    return None


def _a_word(text, word):
    """True when the whole word (or its plain plural) is in the line.

    `_same_word` is deliberately loose, which suits a dish name typed with a slip but not a
    vegetable: it would read "cake" as "kale". A vegetable timing is a claim about one food,
    so it is matched exactly.
    """
    have = tokens(text)
    if not have:
        return False
    for one in have:
        if one == word or one == word + "s" or one + "s" == word:
            return True
        if one.endswith("es") and one[:-2] == word:
            return True
    return False


def _name_in(text, name):
    """True when `name` is in the line as whole words, singular or plural.

    "mange tout" and "pak choi" are two words, and the plural of "runner bean" is "runner
    beans": the last word of the name takes the plural, the rest has to match exactly.
    """
    wanted = tokens(name)
    have = tokens(text)
    if not wanted or not have:
        return False
    last = len(wanted) - 1
    for i in range(len(have) - len(wanted) + 1):
        run = have[i:i + len(wanted)]
        if run[:last] == wanted[:last] and _a_word(" ".join(run[last:]), wanted[last]):
            return True
    return False


# The words that say a food is not wanted, and the reach they have in front of it: "i dont like
# mushrooms", "no carrots left", "without the spinach", "not a fan of beetroot". A vegetable the
# line rules out is not the vegetable to cook, and a timing for it answers a question nobody
# asked ("i dont like mushrooms what can i cook" got how long to cook mushrooms).
RULE_OUT = ("no", "not", "without", "dont", "don't", "doesnt", "doesn't", "didnt", "didn't",
            "hate", "hates", "hated", "dislike", "dislikes", "allergic", "intolerant",
            "avoid", "avoids", "avoiding", "free", "off", "skip", "skipping", "except")
_RULE_OUT_REACH = 4


def _ruled_out(text, names):
    """True when the line names one of these foods only to rule it out.

    The rule-out word has to be close in front of the food it rules out, so "i dont like
    mushrooms, how long do i cook carrots" keeps the carrot row, and "carrots with no butter"
    keeps it too: the words after the vegetable are another ingredient's.
    """
    words = str(text or "").lower().replace("'", " ").split()
    if not words:
        return False
    for name in names:
        wanted = str(name).lower().replace("'", " ").split()
        if not wanted:
            continue
        for start in range(len(words) - len(wanted) + 1):
            run = words[start:start + len(wanted)]
            if run[:-1] != wanted[:-1] and run != wanted:
                continue
            if not _a_word(" ".join(run[-1:]), wanted[-1]):
                continue
            before = words[max(0, start - _RULE_OUT_REACH):start]
            if any(word in RULE_OUT for word in before):
                return True
    return False


def _typed_line(memory, understood):
    """The line as the person typed it, or "".

    The `understood` an entry is handed has the context words of the conversation appended to
    it ("and how long does that take egg spinach"), and a follow-up is about the dish, not about
    its spinach: that line, after a frittata with spinach, was answered "Spinach: 1 to 2
    minutes" - a true fact and the wrong answer. `memory["understood"]` holds the line typed.
    """
    if isinstance(memory, dict):
        now = memory.get("understood")
        if isinstance(now, dict) and now.get("text"):
            return now["text"]
    if isinstance(understood, dict):
        return understood.get("text") or ""
    return ""


def _reply_for(names, said, how=None):
    """The entry for one vegetable: its own time, or how to cook it, or None.

    One entry per vegetable rather than one entry for the table, because a follow-up is
    answered from the answer just given: `bot/modules/answers.py` narrows the last reply to the
    figure asked for, and it stands down only when the thing the line names reached an entry of
    its own. With a single `veg-time` entry every vegetable was the same entry, so "how long to
    boil a swede" straight after a kohlrabi answer came back "12 to 15 minutes." - the kohlrabi
    time with its name trimmed off. An entry of its own makes each vegetable a thing of its own.
    """
    def answer(memory, understood):
        text = _typed_line(memory, understood)
        if not text:
            return None
        if not any(_a_word(text, word) for word in VEG_ASKS):
            return None  # "i bought a cauliflower" is not a timing question
        if _ruled_out(text, names):
            # "i dont like mushrooms what can i cook" is a dinner with none of them, not a
            # request for the method: a timing for the food they just turned down is no answer.
            return None
        # A how-to question ("how do i cook cabbage") is the same row's other fact. A timing
        # question outranks it, and so does a named method: "how long do i cook cabbage" and
        # "how do i roast carrots" are answered elsewhere.
        how_asked = (how is not None
                     and any(_a_word(text, word) for word in VEG_HOW_ASKS)
                     and not any(_phrase_in(text, word) for word in VEG_TIME_WORDS)
                     and not any(_a_word(text, word) for word in VEG_NAMED_METHOD))
        if not how_asked and not any(_phrase_in(text, word) for word in VEG_TIME_WORDS):
            return None  # "how do i cook cauliflower" is the method's question, not this one
        if any(_a_word(text, word) for word in ("freezer", "freeze", "freezing")) and not \
                any(_a_word(text, word) for word in ("boil", "boiling", "steam", "steaming",
                                                     "cook", "cooking", "blanch")):
            # Storing is another entry's question: "how long does spinach keep in the freezer"
            # and "can i freeze cooked carrots" are not asking how long it takes to cook.
            return None
        # The name this row answers to, longest first, so "butternut squash" is its own row and
        # not the plain "squash" one.
        where = None
        for name in sorted(names, key=len, reverse=True):
            if _name_in(text, name):
                where = name
                break
        if where is None:
            return None
        # An oven is never this table's question, wherever the word sits: "how long does
        # cauliflower take in the oven" was two words too far from the vegetable for the rule
        # below and got the boiling time, 6 to 8 minutes for florets. A roast dinner in the oven
        # is still the vegetable's own timing, because "roast" only stands this down beside the
        # name.
        if any(_phrase_in(text, phrase) for phrase in ("in the oven", "in an oven",
                                                       "in my oven", "in the air fryer", "in a hot oven")):
            return None
        # A roasting, keeping, growing or calorie question is another entry's, but only when the
        # word is the one asked about, which is when it sits beside the vegetable: "how long do i
        # roast carrots" and "how long do carrots keep" are those, while "im doing a roast, how
        # long do leeks take to cook" is a timing question about leeks.
        position = _near(text, where.split()[-1])
        words = str(text).lower().replace("'", " ").split()
        for word in VEG_OTHER:
            if not _phrase_in(text, word):
                continue
            if where in word.split():
                # The vegetable is part of a longer name that is a different thing: a spaghetti
                # squash is roasted and forked into strands, not this row's "squash".
                return None
            spot = _near(text, word)
            if position is None or spot is None:
                continue
            if spot < position:
                between = words[spot + 1:position]
                if not any(ask in between for ask in VEG_ASK_BETWEEN):
                    return None      # "how long do i roast carrots": the method is the question
            elif spot > position and _takes_to(words, position, spot):
                # "how long do carrots take to roast" is the roasting's answer, not this row's
                # boiling time: the "takes to" shapes hide the method from the distance rule
                return None
            elif spot - position <= 2:
                return None          # "carrots gone soft", "cabbage in the fridge"
        head = where[0].upper() + where[1:]
        if how_asked:
            if _a_word(text, "frozen"):
                return (head + ", from frozen: straight into already boiling water and take 2 "
                        "minutes off - " + how)
            return head + ": " + how
        if not said:
            # This row is a method and not a boiling time (a mushroom is not boiled), and its
            # method has the minutes in it. "how long do i cook mushrooms" asked the pan and got
            # nothing at all: the line carried a time word, so the row was not the how-to answer,
            # and there was no time to add. The method's own minutes are the answer to both.
            return head + ": " + how
        if _a_word(text, "frozen"):
            # Frozen is the one form where a fresh time is not enough: it goes in from frozen
            # and wants less. The rule is the same whatever the vegetable, said the same way.
            return (head + ", from frozen: go straight into already boiling water and take 2 "
                    "minutes off - " + said)
        return head + ": " + said
    return answer


# The oven is not the boiling table's question, so a line about roast vegetables used to stand
# down and reach nothing at all: "carrots in the oven", "roast carrots", "green beans in the
# oven" and "how long do carrots take in the oven" all got a search hedge or a "Got it". A
# boiled time is wrong in an oven, but a hedge is worse; the minutes below are the oven's own.
# Potatoes are not here on purpose: roast potatoes and wedges already have answers of their own
# (parboil, then hot fat), and this row would take those lines off them.
ROAST_MINUTES = {
    "carrot": ("25 to 30", "halved lengthways or cut into batons"),
    "parsnip": ("30 to 35", "cut into wedges, and they want a little honey or sugar to brown"),
    "leek": ("25 to 30", "halved lengthways and laid cut side down"),
    "cabbage": ("25 to 30", "cut into wedges through the core so they hold together"),
    "sprouts": ("25 to 30", "halved and laid cut side down"),
    "brussels sprouts": ("25 to 30", "halved and laid cut side down"),
    "green beans": ("12 to 15", "kept whole"),
    "french beans": ("12 to 15", "kept whole"),
    "runner beans": ("12 to 15", "kept whole"),
    "broccoli": ("15 to 18", "cut into florets with the stalk split"),
    "courgette": ("18 to 20", "halved lengthways"),
    "onion": ("30 to 35", "cut into wedges through the root"),
    "beetroot": ("50 to 60", "left whole and unpeeled in foil"),
    "swede": ("35 to 40", "cut into 3cm chunks"),
    "squash": ("30 to 35", "cut into 3cm chunks"),
    "butternut squash": ("30 to 35", "cut into 3cm chunks"),
    "pepper": ("20 to 25", "cut into thick strips"),
    "peppers": ("20 to 25", "cut into thick strips"),
    "fennel": ("25 to 30", "cut into wedges through the root"),
    "kohlrabi": ("30 to 35", "cut into wedges"),
    "turnip": ("30 to 35", "cut into 3cm chunks"),
    "celeriac": ("30 to 35", "cut into 3cm chunks"),
    # the two artichokes, which had a boiling time and no oven one: "how long do i roast
    # artichokes" was a search hedge
    "artichoke": ("25 to 30", "halved, oiled on the cut side and packed cut down in a dish"),
    "globe artichoke": ("25 to 30", "halved, oiled on the cut side and packed cut down in a dish"),
    "jerusalem artichoke": ("25 to 30", "scrubbed, halved if large, in a single layer"),
    "jerusalem artichokes": ("25 to 30", "scrubbed, halved if large, in a single layer"),
    "kale": ("10 to 12", "torn off the stalk and tossed in oil, for the crispness rather than a side"),
    "aubergine": ("25 to 30", "cut into 3cm chunks"),
    "tomato": ("15 to 20", "halved, cut side up"),
    "red onion": ("30 to 35", "cut into wedges through the root"),
    # The vegetables whose own row is a boiling time or a pan method: a mushroom is not boiled
    # and asparagus is not a pan vegetable, so without these the oven question fell to a hedge
    # while the boil row won the words and had nothing to say about it.
    # The reply adds "in a single layer with a little oil" itself, so a shape that says the
    # layer and the oil again reads as one sentence said twice: "in one layer with room between
    # them - crowded mushrooms steam, in a single layer with a little oil so it browns".
    "mushroom": ("15 to 20", "left whole if small and halved if large, with room between them "
                             "because crowded mushrooms steam instead of browning"),
    "mushrooms": ("15 to 20", "left whole if small and halved if large, with room between them "
                              "because crowded mushrooms steam instead of browning"),
    "asparagus": ("10 to 12", "kept whole; they brown rather than bend"),
    "sweetcorn": ("25 to 30", "cobs turned once half way; loose kernels take 12 to 15"),
    "corn on the cob": ("25 to 30", "cobs turned once half way; loose kernels take 12 to 15"),
    "shallots": ("25 to 30", "left whole and unpeeled, or halved through the root"),
    "garlic": ("25 to 30", "a whole head with the top sliced off and wrapped in foil, then "
                           "squeezed out of its skins"),
    "radish": ("15 to 20", "halved - the heat goes and they come out sweet and mild"),
    "romanesco": ("20 to 25", "cut into florets like a cauliflower, and quicker because the "
                              "florets are smaller"),
    "spring onion": ("8 to 10", "kept whole; they scorch at the tips before the middle softens"),
    "spring onions": ("8 to 10", "kept whole; they scorch at the tips before the middle softens"),
    "pak choi": ("8 to 10", "halved lengthways and laid cut side down"),
    "tenderstem broccoli": ("12 to 15", "kept whole, stalks and all"),
    "chicory": ("20 to 25", "halved through the root so the leaves hold together"),
    "okra": ("12 to 15", "left whole with the tops trimmed, and dry so it does not go slimy"),
    "mangetout": ("8 to 10", "kept whole and turned once; they are done when the pods blister"),
}

ROAST_WORDS = ("roast", "roasted", "roasting", "roasts", "oven", "baked", "baking", "bake",
               "air fryer", "in the oven", "in an oven", "in my oven", "tray bake")

# A line that names boiling, steaming or parboiling is asking this table's question, even when
# the oven is in it: "how long do i parboil potatoes before the oven" is not a roast time.
ROAST_NOT_FOR_US = ("boil", "boiled", "boiling", "steam", "steamed", "steaming", "parboil",
                    "parboiled", "blanch", "blanched", "microwave", "fry", "fried", "frying",
                    "grill", "grilled", "soup", "mash", "puree", "fridge", "freezer", "freeze",
                    "keep", "keeps", "last", "calories", "plant", "plants", "grow", "growing",
                    "dog", "dogs", "cat", "cats", "buy", "cost", "price", "cheap", "shop",
                    "gone soft", "gone limp", "mouldy", "slimy", "wilted", "sprouting")


def _roast_reply(memory, understood):
    """How long one vegetable takes in the oven, or None when the line asks something else."""
    text = _typed_line(memory, understood)
    if not text:
        return None
    if not any(_phrase_in(text, word) for word in ROAST_WORDS):
        return None
    lowered = str(text).lower()
    if any(_a_word(text, word) for word in ROAST_NOT_FOR_US):
        return None
    if _ruled_out(text, tuple(ROAST_MINUTES)):
        return None  # the vegetables the line turned down are not what to roast
    where = None
    for name in sorted(ROAST_MINUTES, key=len, reverse=True):
        if _name_in(text, name):
            where = name
            break
    if where is None:
        return None
    minutes, how = ROAST_MINUTES.get(where, ("25 to 30", "cut into even pieces"))
    head = where[0].upper() + where[1:]
    return (head + ": " + minutes + " minutes in the oven at 200C (180C fan), " + how +
            ", in a single layer with a little oil so it browns rather than steams. It is done "
            "when the edges are browned and a knife goes into the thickest piece easily.")



# Words that stand one vegetable row down and not the rest: the globe artichoke keys the bare
# "artichoke", so a Jerusalem line would otherwise be a row about boiling leaves.
VEG_EXTRA_AVOID = {
    "globe artichoke": ("jerusalem", "jerusalem artichoke", "jerusalem artichokes",
                        "sunchoke", "sunchokes"),
}


def _slug(name):
    """An entry id for a vegetable: "butternut squash" is `veg-butternut-squash`."""
    return "veg-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


ENTRIES = tuple(
    entry(_slug(names[0]), (names, VEG_ASKS), _reply_for(names, said, VEG_HOW.get(names[0])),
          # The avoid list is the words that are another entry's question wherever they sit in
          # the line. A method word is not one of them ("im doing a roast, how long do leeks
          # take to cook" is this entry's), so those are weighed beside the vegetable instead.
          avoid=VEG_NOT_FOR_US + VEG_EXTRA_AVOID.get(names[0], ()), bias=2)
    for names, said in VEG_TIME) + tuple(
    entry(_slug(names[0]), (names, VEG_ASKS), _reply_for(names, None, how),
          avoid=VEG_NOT_FOR_US, bias=2)
    for names, how in VEG_HOW_EXTRA)

ENTRIES = ENTRIES + (
    entry("veg-roast", (tuple(ROAST_MINUTES),
                        ("in the oven", "oven", "roast", "roasted", "roasting", "bake", "baked",
                         "baking", "air fryer", "how long", "long", "minutes", "time",
                         # The commonest way people write the question names the time and the
                         # method but never says "how long": "roasting time for beetroot" and
                         # "beetroot time in the oven" were the beetroot's boiling row, which
                         # has the vegetable and a time word of its own.
                         "roasting time", "roast time", "time in the oven", "oven time",
                         "how long in the oven")),
          _roast_reply,
          # Same rule as the boiling table: another entry's question wherever it sits.
          avoid=VEG_NOT_FOR_US, bias=1),
)

# A chip that came out limp is a fault, and the row that owns the chip line in cooking.py
# (`chips-cook`) answers it with the cooking times, because its key carries "crispy" and "soggy"
# beside "how long". A limp chip has a cause - water on the surface, a crowded tray, fat that is
# not hot enough - so it is a fault answer, and the softer words are in this key so that this row
# takes the fault and the timing row keeps the timing question. It sits here, in the vegetable
# domain that already owns the oven and roast rows for roots, because `cooking.py` is at the
# hub's one-megabyte wall and cannot be added to.
ENTRIES = ENTRIES + (
    entry("veg-chips-crisp",
          (("chips", "chip", "fries", "french fries", "oven chips", "homemade chips",
            "chips and fries", "wedges", "potato wedges", "wedge"),
           ("soggy", "soft", "limp", "floppy", "crispy", "crisp", "crispier", "crisp up",
            "go crispy", "not crispy", "not crisp", "wont crisp", "won't crisp")),
          "Soggy chips are a steam problem, so the fix is dry and hot: pat fresh-cut chips dry "
          "(rinse the starch off first if you cut them yourself) and put frozen ones in straight "
          "from the freezer, then get the oven and the tray properly hot - 200C (180C fan) - and "
          "spread them in one layer with space around each chip, because a crowded tray steams "
          "instead of crisping. Salt them as they come out and not before, since salt pulls water "
          "to the surface. If they still come out limp, cook them twice: 10 minutes at 160C to "
          "soften the middle, then 8 minutes at 190C to crisp the outside, with a few minutes "
          "resting in between.",
          # the cooking time, the portion, the calories, the freezer, the plate and the recipe are
          # six other rows, and a roast potato is not a chip
          avoid=("how long", "minutes", "temperature", "how much", "portion", "portions",
                 "price", "calorie", "calories", "healthy", "unhealthy", "freeze", "refreeze",
                 "defrost", "reheat", "leftover", "left over", "goes with", "with what",
                 "chip shop", "takeaway", "roast potato", "roast potatoes", "roasties",
                 # a breaded or battered thing that will not stay crisp is `fried-crisp`, below:
                 # "how do i keep fried chicken crispy" was answered with "Soggy chips are a
                 # steam problem", which is the right fault on the wrong food.
                 "chicken", "fish", "prawn", "prawns", "halloumi", "tofu", "nugget", "nuggets",
                 "goujon", "goujons", "schnitzel", "katsu", "scotch egg", "onion ring",
                 "onion rings", "spring roll", "spring rolls", "batter", "battered", "breaded",
                 "breadcrumb", "breadcrumbs", "panko", "tempura"),
          bias=2),
    # A fried or breaded thing that has gone soft is the same water-and-steam fault as a chip,
    # but the fix is a different one - the coating, the oil and the draining, not the oven - so
    # it is its own row rather than a branch inside the chips answer.
    entry("fried-crisp",
          (("chicken", "fish", "prawn", "prawns", "halloumi", "nugget", "nuggets",
            "goujons", "schnitzel", "katsu", "scotch egg", "onion rings", "spring rolls",
            # not "breaded" or "breadcrumbs": a letter out, they are the word "bread", and
            # "my bread is soggy" and "how do i stop bread going soggy" were given the
            # fried-coating answer because of it.
            "batter", "battered", "coated", "panko", "tempura", "fried"),
           ("crispy", "crisp", "crunchy", "crunch", "soggy", "soft", "limp", "goes soft",
            "gone soft", "not crispy", "wont crisp", "won't crisp", "stay crisp", "keep crisp")),
          "Three things keep a fried coating crisp: a dry surface, oil that is hot enough, and "
          "air under it once it is out. Pat the food dry and flour it before the egg and crumbs, "
          "because a wet surface steams from the inside; fry at about 175C to 180C, which is a "
          "cube of bread browning in 60 seconds, since cooler oil soaks in and hotter oil browns "
          "the outside before the middle is done. Drain it on a rack over a tray rather than on "
          "kitchen paper, which traps the steam against the underside, and never put a lid or "
          "foil over the plate: serve it straight away, or hold it uncovered in a 100C oven on a "
          "rack, which keeps the coating dry for about 20 minutes. If you are cooking in "
          "batches, do not pile the finished pieces on top of each other.",
          # the oven time, the internal temperature, the calories, the freezing and the recipe
          # are other rows, and a chip has its own answer above
          avoid=("how long", "minutes", "temperature", "how much", "portion", "portions",
                 "calorie", "calories", "healthy", "unhealthy", "freeze", "refreeze", "defrost",
                 "reheat", "leftover", "left over", "goes with", "chip", "chips", "fries",
                 "roast potato", "roast potatoes", "pizza", "recipe", "marinade", "marinate",
                 "bake", "roast", "air fryer", "sous vide", "raw", "pink", "safe", "done",
                 # a chicken that went soggy in the freezer is the thawed-food answer, not this
                 # one: the ice-crystal rule is in the keeping tables.
                 # tofu already has its own crispness answer (press it, then cornflour), and
                 # this row was taking it: "how do i get tofu crispy" was a good reply before
                 "tofu", "pressed tofu",
                 "freezer", "frozen", "freeze", "thaw", "thawed", "thawing", "defrost",
                 "defrosted", "defrosting", "refreeze", "refrozen", "last night", "still ok",
                 "still okay", "safe to eat", "gone off", "went off"),
          # the keeping rows also key on the food and a word, and "how do i keep fried chicken
          # crispy" was answered with how long cooked chicken lasts in the fridge; the general
          # soggy card takes "how do i stop my fried chicken going soggy" unless this row is
          # allowed to out-rank it, because it names the food and the coating.
          bias=5),
)

# --- a vegetable that went soggy: the water fault ------------------------------------------
# "how do i stop courgettes going soggy" was a search hedge while "how do i cook courgette so
# it is not soggy" answered, because the boiling rows are keyed on a cooking verb and "stop ...
# going soggy" has none. Soggy is not a timing question either: it is the water fault, and the
# fix depends on whether the vegetable is going in a pan or into a sandwich, so the vegetables
# that fail the same way are grouped and a new one costs a word. Lettuce and the leaves are
# deliberately not here: a wet leaf is `salad-revive` and `soggy-lunch`, which have their own
# answers about drying and dressing.
WATER_WORDS = ("soggy", "going soggy", "goes soggy", "gone soggy", "went soggy", "go soggy",
               "soggy when", "watery", "watery when", "leaking water", "leaks water",
               "gives up water", "let out water", "mushy", "wet")

WATER_FAMILIES = (
    (("courgette", "courgettes", "zucchini"),
     "Courgette goes soggy because it is mostly water, so the water has to come out before it "
     "hits the pan: slice it about 1cm thick, salt it for 10 to 15 minutes, pat it dry, then "
     "cook it in a wide hot pan in one layer with no lid, or roast it at 220C spread out. "
     "Crowding the pan steams it, and a lid guarantees it - and if it is going in a salad, salt "
     "it and drain it first rather than dressing it early."),
    (("cucumber", "cucumbers"),
     "Cucumber goes soggy because salt and dressing pull the water out of it: slice it, salt it "
     "for 10 minutes and drain it on kitchen paper, or scoop the watery middle out with a "
     "teaspoon, and dress it at the table rather than an hour before. For a sandwich it wants to "
     "be patted dry and kept away from the bread until you eat."),
    (("aubergine", "aubergines", "eggplant", "eggplants"),
     "Aubergine goes soggy when it soaks up oil: salt the slices for 20 minutes, pat them dry, "
     "then fry in hot oil in one layer, or brush them with oil and roast at 200C until the edges "
     "colour. It is done when it collapses and looks glossy, not when it is merely soft."),
    (("mushroom", "mushrooms"),
     "Mushrooms go soggy when they are crowded or covered: they are mostly water, so give them a "
     "wide hot pan with a little oil, one layer, no lid, and let the water cook off before you "
     "turn them. Salt only at the end, or they give up their water early and stew."),
    (("tomato", "tomatoes", "cherry tomatoes"),
     "Tomato goes watery when it is cooked with the lid on or with too much salt early: halve "
     "them, salt them in a colander for 10 minutes and let the juice run off, then roast them cut "
     "side up at 200C, or cook them uncovered so the water reduces instead of pooling."),
    (("pepper", "peppers", "bell pepper", "bell peppers"),
     "Peppers go soft and watery when they are cooked fast in a crowded pan: cut them into strips "
     "of the same size and give them a hot wide pan in one layer, or roast them at 200C until the "
     "skins blister - then they are sweet rather than wet."),
    (("butternut squash", "squash", "pumpkin"),
     "Squash goes soggy when it is steamed rather than roasted: cut it into 3cm chunks, toss in "
     "oil, spread it in one layer and roast at 200C for 30 to 35 minutes, turning once. Boiled or "
     "covered, it holds on to the water and turns to mush."),
)

ENTRIES = ENTRIES + (
    entry("veg-watery", (tuple(name for names, _fix in WATER_FAMILIES for name in names),
                         WATER_WORDS),
          lambda memory, understood: _watery_veg(understood),
          # "keep" and "how long" are not on this list: "how do i keep courgette from going
          # soggy" is exactly this question, and "my peppers go soggy in the fridge" is the same
          # fault with the shelf named, so "fridge" is out too - only the freezer keeps a
          # vegetable in a way this row has nothing to say about. What does stand the row down is
          # another entry's subject - the garden, the calories - and the leaf faults, which have
          # their own answers.
          avoid=("freezer", "freeze", "frozen", "thawed", "thaw", "thawing", "defrosted",
                 "defrost", "how long", "last", "lasts", "leftovers",
                 "leftover", "reheat", "calories", "calorie", "healthy", "protein", "vitamin",
                 "plant", "plants", "planting", "grow", "growing", "garden", "allotment",
                 "seed", "seeds", "harvest", "pick", "picking", "ripe", "buy", "buying",
                 "cost", "price", "cheap", "supermarket", "allergy", "allergic", "baby",
                 "weaning", "diabetes", "mouldy", "gone off", "wilted", "wilting", "slimy",
                 "limp"),
          # A named vegetable that has gone wet is this row's question and nobody else's, so it
          # is allowed to out-rank the keeping rows that a word of it also reaches: "how do i
          # stop peppers going soggy in the fridge" was read as thawed food (keeping.py's
          # `cold-thawed` keys on "soggy" and "fridge") and answered with the ice-crystal rule.
          # Only a line that is about the freezer or a thaw is stood down, higher up.
          bias=5),
)


def _watery_veg(understood):
    """The fix for a vegetable that has gone wet, per family; None when the line names none."""
    words = understood.get("words") if isinstance(understood, dict) else None
    text = " ".join(str(word) for word in (words or ())) or str(
        (understood or {}).get("clean") or "")
    text = text.lower()
    best = None
    for names, fix in WATER_FAMILIES:
        for name in names:
            if _phrase_in(text, name) and (best is None or len(name) > best[0]):
                best = (len(name), fix)
    return best[1] if best else None


# A vegetable goes soft as well as hard, and "soggy", "limp" and "mushy" are what an extra three
# minutes in the water looks like. The words were already in `VEG_OTHER` above, standing the
# timing rows down, and nothing took the line: "my vegetables are soggy" was "Thanks for telling
# me", "my cauliflower is mushy" was "I'm listening", and "my broccoli is overcooked" was advice
# about dry meat. The fault is the method the vegetable was given, so a roast is answered as a
# roast and a pan of water as a pan of water, and one row covers the whole set.
VEG_SOFT_FAULTS = ("soggy", "limp", "floppy", "mushy", "slimy", "watery", "overcooked",
                   "over cooked", "too soft", "went soft", "gone soft", "gone soggy",
                   "going soggy", "gone limp", "went limp", "not crisp", "not crispy",
                   "wont crisp", "won't crisp", "soft and wet")

# The vegetables that fail this way. Potatoes and mushrooms are left out on purpose: a potato
# goes waxy, floury or watery by variety and its own rows know which, and a mushroom goes
# rubbery from too much water rather than soft from too long in it.
VEG_SOFT_NAMES = (tuple(name for names, _said in VEG_TIME for name in names)
                  + tuple(name for names, _how in VEG_HOW_EXTRA for name in names)
                  + tuple(VEG_HOW)
                  + ("vegetables", "veg", "veggies", "mixed veg", "stir fry veg", "roast veg",
                     "leafy greens", "broccoli", "peas", "sprouts", "sprout", "parsnip",
                     "parsnips", "romanesco", "broccolini", "spring onions", "shallot",
                     "shallots", "butternut", "pumpkin", "aubergine", "aubergines"))

# The method words, which decide which of the answers below the line gets.
VEG_ROASTED = ("roast", "roasted", "roasting", "oven", "baked", "baking", "air fryer",
               "airfryer", "tray", "traybake", "grill", "grilled")

# The vegetables that collapse rather than soften, and the ones that go from squeaky to mushy in
# a minute: each has its own answer because the number of minutes is the whole answer.
VEG_WET = ("courgette", "courgettes", "zucchini", "aubergine", "aubergines", "marrow",
           "tomato", "tomatoes", "squash", "butternut squash", "butternut", "pumpkin")
VEG_LEAVES = ("spinach", "kale", "chard", "cavolo nero", "spring greens", "greens",
              "leafy greens", "collard")
VEG_PODS = ("peas", "mange tout", "mangetout", "sugar snap", "green beans", "runner beans",
            "french beans", "string beans", "broad beans", "broad bean", "fava beans")
# A vegetable that has *gone* limp - rather than come out of the pan soft - has been sitting in the
# fridge, and the fix for that is iced water, not a hotter pan. The words are the state changing over
# time, which is what tells a raw carrot from an overcooked one.
VEG_RAW_FAULTS = ("gone soft", "went soft", "gone limp", "went limp", "gone floppy",
                  "gone bendy", "gone rubbery", "gone wrinkly", "gone leathery", "lost its crunch",
                  "lost their crunch", "gone dry", "dried out")

# A prevention question - "how do i stop broccoli going soggy" - is the timing row's line, not a
# fault: it knows the minutes and the cold-water dunk for its own vegetable. Only the words that
# name no vegetable at all ("my veg") leave that question to the fault card.
VEG_PREVENTION = ("how do i stop", "how can i stop", "how to stop", "how do i keep", "how can i keep",
                  "how do i prevent", "how do i make sure", "how long", "how do i cook",
                  "how do i boil", "how do i steam", "how do i roast", "how do i fry",
                  "stop it going", "stop them going", "stop it from going", "stop them from going",
                  "keep it from", "keep them from", "so it doesnt go", "so they dont go",
                  "so it doesn't go", "so they don't go")

VEG_GENERIC = ("veg", "vegetables", "veggie", "veggies", "mixed veg", "stir fry veg", "root veg",
               "veg mix", "veg of", "some veg")

# The cooking words, which say the vegetable was in a pan even when it has "gone" soft in it.
VEG_COOKED = ("roast", "roasted", "roasting", "boil", "boiled", "boiling", "steam", "steamed",
              "fry", "fried", "frying", "cook", "cooked", "cooking", "oven", "pan", "microwave",
              "air fryer", "stir fry", "stir fried", "grill", "grilled", "bake", "baked")

VEG_BRASSICAS = ("broccoli", "cauliflower", "cabbage", "sprouts", "sprout", "romanesco",
                 "broccolini", "pak choi", "pak choy", "bok choy", "kalettes", "savoy",
                 "kohlrabi", "turnip")


def _soft_veg(text, understood=None):
    """The fix for a vegetable that came out soft, wet or limp, or None."""
    if not isinstance(text, str) or not text:
        return None
    # A follow-up says "them": "and how do i stop them going soggy" after courgettes. The typed
    # line names no vegetable, so the vegetable comes from the conversation the reading carries,
    # and the answer is about the courgette rather than about vegetables in general.
    if not any(_name_in(text, name) for name in VEG_SOFT_NAMES) and isinstance(understood, dict):
        said = str(understood.get("text") or "").lower()
        if said and said != text:
            text = said
    if any(_phrase_in(text, word) for word in ("slimy", "smelly", "sour", "gone off")):
        return ("A raw vegetable that is slimy and smells is going off, so bin the affected leaves "
                "or the whole bag: that slime is bacteria, not water, and cooking will not make it "
                "safe to eat. Slime on a cooked vegetable is the harmless kind - it means too long "
                "in the water - so drain it, press the water out and dress it with oil and lemon.")
    if (any(_phrase_in(text, word) for word in VEG_RAW_FAULTS)
            and not any(_phrase_in(text, word) for word in VEG_COOKED)):
        return ("A raw vegetable that has gone limp has lost water, not flavour: it is still safe to "
                "eat, and half an hour in a bowl of iced water firms it up again for a salad. After "
                "that, cook it - roast it at 200C, or put it in a soup or a stir-fry - because a "
                "limp one will not crisp back on its own. For the next lot, a bag or a lidded tub in "
                "the salad drawer keeps it firm for weeks, and cutting the green tops off carrots "
                "stops them pulling the water out of the root.")
    # "how do i stop broccoli going soggy" wants the broccoli row's minutes, and it has them.
    if (any(_phrase_in(text, word) for word in VEG_PREVENTION)
            and not any(_name_in(text, word) for word in VEG_GENERIC)):
        return None
    if any(_name_in(text, name) for name in VEG_PODS):
        return ("Peas and beans go from squeaky to mushy in about a minute: 2 minutes for frozen "
                "peas straight into boiling water, 4 to 5 for green beans, and drain them the "
                "moment they are bright. If they are already soft, toss them in butter with a "
                "squeeze of lemon and serve them as they are - a soft pea will not firm up - or "
                "let them cool into a salad or a soup.")
    if any(_name_in(text, name) for name in VEG_LEAVES):
        return ("Spinach, kale and other leaves go slimy in a pan of water, so cook them in "
                "almost none: a hot pan with a knob of butter and a spoon of water, 1 to 2 "
                "minutes until they have just collapsed, then press the water out. Raw leaves "
                "that have only gone limp come back in 15 minutes in iced water; cooked ones that "
                "are slimy were in too much water, so squeeze them dry and dress them with butter "
                "or a little vinegar, or fold them into a sauce.")
    if any(_name_in(text, name) for name in VEG_BRASSICAS):
        return ("Broccoli, cauliflower and cabbage go soft and grey from too long at a rolling "
                "boil: 4 to 5 minutes for broccoli florets, 6 to 8 for sprouts or shredded "
                "cabbage, 12 to 15 for a whole cauliflower, then straight into a colander with "
                "the lid off, because it goes on cooking in its own steam. If it has already gone grey and sulphury, give it a "
                "minute in a hot pan with butter and garlic, or put it in a gratin or a soup.")
    if any(_name_in(text, name) for name in VEG_WET):
        return ("Courgette, aubergine and tomato are mostly water, so that water has to come out "
                "before the heat goes on: slice them, salt them for 10 minutes and pat them dry, "
                "then fry or roast in one layer in a hot pan and do not crowd it, because a crowded "
                "pan steams them instead of browning. Already limp: turn the heat up to drive the "
                "water off, or put them in a sauce or a soup.")
    if any(_phrase_in(text, word) for word in VEG_ROASTED):
        return ("A vegetable that comes out of the oven soft was steamed rather than roasted: it "
                "went in wet, or the tray was crowded. Dry it, toss it in oil, spread it in one "
                "layer with air between the pieces, and give it 200C (180C fan) with the door "
                "shut. Already limp: turn the heat up for the last 10 minutes to colour what you "
                "can, and serve it with something sharp - it will not crisp back.")
    return ("A vegetable goes limp and wet from too long in the water, from a lid left on so the "
            "steam cannot escape, or from a pan too small for the amount: cook it in a shallow "
            "layer with a splash of water rather than a deep panful, taste it a minute before "
            "the time in the recipe, and drain it the second a knife slides in, lid off. If it "
            "is already soft, drive the water off in a hot dry pan with a little butter, or put "
            "it in a soup or a sauce, because it will not crisp again. A raw vegetable gone limp "
            "in the fridge is the same rescue: it has lost water rather than been overcooked, so "
            "roast it at 200C or put it in a soup within the day.")


ENTRIES = ENTRIES + (
    entry("veg-gone-soft",
          (VEG_SOFT_NAMES, VEG_SOFT_FAULTS),
          lambda memory, understood: _soft_veg(_typed_line(memory, understood), understood),
          # chips, salad, a stewed apple and a bag of frozen peas for the freezer are four other
          # rows: this one is a vegetable on the plate that came out wrong.
          avoid=("chips", "chip", "fries", "wedges", "roasties", "salad", "lettuce",
                 "apple", "fruit", "pasta", "rice", "noodles", "bread", "cake",
                 "pastry", "meat", "chicken", "beef", "pork", "lamb", "fish", "egg", "soup",
                 "sauce", "gravy", "curry", "stew", "pie", "pizza", "freezer", "freeze",
                 "frozen", "fridge", "keep", "keeps", "calories", "healthy", "recipe",
                 # a bag of spinach to use up is the use-it-up row's line, not a fault
                 "use up", "use it up", "what can i do", "can i do with", "left over",
                 "leftover", "leftovers", "meal idea", "meal ideas"),
          bias=2),
)
