import re

from . import pets
"""What is in food, and how much of it to eat: the everyday healthy-eating questions.

The answers lane owns this domain. People ask these as facts ("how many calories in a
banana"), as worries ("is pasta fattening", "are eggs bad for cholesterol") and as habits
they want to change ("how do I stop eating sugar at night"). Entries are keyed by the food
or the nutrient, not by the wording, so one row answers "how much sugar is in coke" and
"is there a lot of sugar in a can of coke".

Cooking a dish lives in cooking.py and dishes.py; a portion of pasta or rice in measures.py;
protein for training and food around a run in sport.py. This module is the nutrition side:
calories, sugar, salt, fibre, fat, alcohol, caffeine, and the habits that people ask about by
name. Numbers are UK guidance for an ordinary adult (a 2,000 kcal a day reference intake),
said plainly, with the "see your GP" line only where a diet question is really a health one.
"""
from .cooking import COOKING_VERBS
from .lookup import (DAY_WORDS, PACK_DATE, a_food_is_being_kept, entry as _raw_entry,
                     food_has_gone_off, not_a_count_for_the_box_or_the_dish)
from .shopping import not_a_present

# The topics this domain answers (bot/understanding/topics.py); answers.py declares the union.
ANSWERS = ("health", "food-and-drink", "fitness")


def _frozen_and_tinned_reply(memory, understood):
    """Fresh against frozen, asked as health, as money, as a smoothie, or of fruit."""
    said = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    smoothie = any(word in said for word in ("smoothie", "smoothies", "blender", "shake"))
    price = any(word in said for word in (" cheap", " cheaper", " cheapest", " cost", " costs",
                                          " price", " prices", " budget", " dearer", " value"))
    # a tin of fruit is the one that carries syrup; frozen berries are not tinned fruit, and
    # "are frozen berries good for you" was answered with the syrup warning.
    fruit = (any(word in said for word in (" fruit", " fruits", " peach", " peaches", " mango",
                                           " pineapple", " pears", " cherries"))
             and any(word in said for word in ("tinned", "tin of", "canned", "can of", " from a tin")))
    if smoothie:
        return ("Frozen berries and frozen fruit are the better buy for a smoothie: they are picked "
                "ripe and frozen within hours, so they keep more vitamin C than soft fruit that has "
                "sat in a punnet, and frozen chunks chill the drink and thicken it without ice. Tip "
                "them in from frozen with the yoghurt or milk and blend - no need to thaw, and no "
                "added sugar, unlike the fruit in syrup.")
    if price:
        return ("Almost always yes: frozen vegetables cost less than fresh for the same weight, "
                "because nothing has to be sorted, shipped soft or thrown away, and tinned beans, "
                "chickpeas and tomatoes are cheaper still. Frozen also wastes nothing, since you "
                "pour out what you need and the bag goes back. The one thing worth paying for "
                "fresh is a vegetable you are going to eat raw, where the texture is the point.")
    if fruit:
        return ("Tinned fruit counts, with one catch: it is picked ripe and tinned within hours, so "
                "the vitamins survive, but fruit in syrup is a pudding rather than a portion - a "
                "couple of tinned peach halves in syrup carry about 15g of sugar. Buy the ones in "
                "juice, or rinse the syrup off, and tinned fruit does the same job as fresh. Frozen "
                "berries are the better buy of the two, since nothing is added to them at all.")
    return ("Frozen and tinned are as good as fresh, and often better: vegetables are frozen within "
            "hours of picking, so their vitamins outlast a cabbage that has sat in the fridge all "
            "week, and tinned tomatoes are better than the pale ones flown in out of season. Frozen "
            "peas, sweetcorn, spinach and berries are the best buys, and tinned beans, chickpeas and "
            "sardines are cheap protein with nothing added. The tin or the bag is not the problem - "
            "read the label: brine, syrup, oil and sauces are where the salt and sugar come from. "
            "Frozen fish is fine too, thawed overnight in the fridge and cooked from there.")


def entry(id, key, reply, avoid=(), bias=0, ask=(), slips=(), keep=(), guard=None):
    """A nutrition entry. Every one of them passes on a children's or a pet line.

    A child's portions and a dog's food are different answers, and both are asked in the same
    words ("how much should I feed my son", "can my dog eat grapes"), so the guard sits here
    rather than in forty separate `avoid` lists. `keep` names the guard words an entry answers
    anyway: "how do I get my kids to eat veg" is a question for exactly that entry.

    The pack date is the second guard, for the same reason: "is it ok to eat bread past the date"
    is a question about whether the loaf is still edible, and the fibre row answered it with "two
    slices is about 6g of fibre". What is in a food is not what has happened to it, so every row
    here stands down on the words that mean the day printed on the pack (`PACK_DATE`) and on the
    line that says the food has gone off at all (`food_has_gone_off`): "is my chicken still ok to
    eat" was answered with what is in a chicken.
    """
    # The pack words below are half of that one rule written out as `avoid` words; a smell said of
    # the food needs the reading, not a word, so it is asked here once for every row.
    if guard is None:
        guard = lambda read: not food_has_gone_off(read)
    else:
        inner = guard
        guard = lambda read: inner(read) and not food_has_gone_off(read)
    # `guard_words` are the avoid words this wrapper adds; `guard` is the reading test the entry
    # passed in. They are two different things and the names must not collide: a tuple handed to
    # the matcher as a guard is called on the reading and raises, which loses the entry.
    guard_words = tuple(word for word in _NOT_A_PERSON_OR_PET + _A_STATEMENT_ABOUT_ME + _PACK_DATE
                        if word not in keep)
    avoid = tuple(avoid) + guard_words
    return _raw_entry(id, key, reply, avoid=avoid, bias=bias, ask=ask, slips=slips,
                      guard=guard)


# The day on the pack, which no nutrition row answers: read from lookup so the freshness, keeping
# and nutrition rows all mean the same thing by "past the date".
_PACK_DATE = PACK_DATE

# A baby, a child, a pregnant person and a pet each get different advice, and a diet answer
# meant for an adult is wrong for all four. People do ask "can my dog eat grapes" in exactly
# the words of a nutrition question, so this is the whole of the guard.
_NOT_A_PERSON_OR_PET = (
    "my dog", "my cat", "puppy", "kitten", "dog", "cat", "hamster", "rabbit", "parrot",
    "baby", "babies", "newborn", "toddler", "my son", "my daughter", "my child", "my kid",
    "my kids", "children", "child", "pregnant", "pregnancy", "breastfeeding", "nursing",
    "year old", "years old", "year-old", "year old son", "my four year old",
    "under one", "weaning", "allergic", "allergy", "intolerance", "coeliac", "diabetic",
    "diabetes", "kidney", "kidneys", "warfarin", "medication", "on tablets",
)

# The thing being timed is the subject, not the timing words. This row answers "should i eat
# before or after X" for a *session* - energy before, repair after - so a line that times a dose is
# a different question with its own row: "should i take my vitamins before or after food" was told
# "something small and mostly carbohydrate one to two hours before gives you the energy for the
# session". Read the other way the same test keeps this row where it belongs: "before or after
# food" and "before or after a meal" time the eating itself, and those are a person asking how to
# eat, which is this row's subject. So the row stands down for a dose, not for every line that has
# no session in it.
_A_DOSE = re.compile(
    r"\b(?:vitamins?|multivitamins?|supplements?|probiotics?|iron|folic\s+acid|calcium"
    r"|tablets?|pills?|capsules?|creatine|magnesium|omega\s?3|collagen|melatonin|electrolytes?"
    r"|ibuprofen|paracetamol|aspirin|naproxen|painkillers?|medicines?|medication"
    r"|antibiotics?|steroids?)\b")


def not_a_dose(understood):
    """True unless the line times a dose rather than a session or a meal.

    Public because the same shape reaches other timing rows: the subject of "before or after what"
    is the session, the dose or the journey, and a row answers only its own subject.
    """
    said = str(understood.get("clean") or understood.get("plain") or "").lower()
    return not _A_DOSE.search(said)


# A statement about the user's own diet ("im vegetarian and i dont eat dairy", "i dont eat dairy
# though") is something to remember and plan around, not a question about a food: the memory lane
# answers it, and a nutrition entry that grabbed it answered a question nobody asked.
_A_STATEMENT_ABOUT_ME = (
    # the matcher's forms drop a lone "i", so these are written without it
    "dont eat", "don't eat", "do not eat", "im vegetarian", "i'm vegetarian",
    "im vegan", "i'm vegan", "no dairy", "dairy free", "lactose", "cut out",
    "gave up", "quit meat", "dont drink", "don't drink", "im allergic", "i'm allergic",
)

# "i dont eat veg" is a dislike to remember, not a request for the five-a-day answer. The
# shortfall wording ("i dont eat enough veg") is the entry's own line, so only the plain dislike
# is listed here: it is what the statement guard used to catch on every nutrition entry.
_DISLIKE = ("dont eat veg", "don't eat veg", "dont eat vegetables", "don't eat vegetables",
            "dont eat any veg", "don't eat any veg", "dont eat fruit", "don't eat fruit",
            "dont eat salad", "don't eat salad", "dont eat greens", "don't eat greens",
            "never eat veg", "never eat vegetables", "dont like veg", "don't like veg",
            "dont like vegetables", "don't like vegetables")


# Who refuses the veg decides the answer, and "wont eat" does not say who: an adult partner who
# will not eat vegetables was handed "A child refusing veg is normal and nearly all of them grow
# out of it", and "my husband refuses to eat greens" was handed nothing at all. So the person is
# read from the words for the person, in three places: the speaker, a grown-up they name, and a
# child they name.
_ME_ASKING = (" i wont eat", " i won't eat", " i refuse", " i dont eat", " i don't eat",
              " i never eat", " i hate veg", " i hate vegetables", " i hate vegtables",
              " i cant eat", " i can't eat", " i cant stand", " i can't stand",
              # the speaker's own wish rather than a refusal: "i want to like them" and "i wish
              # i liked them" are the person asking for themselves, and they were answered as a
              # child because the line names nobody at all
              " i want to like", " i want to eat", " i want to start eating", " i wish i liked",
              " i wish i could eat", " i'd like to like", " id like to like",
              " im a fussy", " i am a fussy", " im picky", " i am picky",
              " help me like", " for myself", " myself")
# A child the line names: a son, a daughter, a year old. These are words for a child and nothing
# else, so they beat a grown-up word in the same line ("my son's friend wont eat veg" is still
# about the son's age, not the friend's).
_A_CHILD = (" kid", " kids", " child", " children", " son", " sons", " daughter", " daughters",
            " lad", " lads", " lass", " wee one", " toddler", " baby",
            " year old", " years old", " year-old", " nursery", " my boy ", " my girl ",
            " teenager", " weaning", " grandson", " granddaughter", " grandchild", " stepson",
            " stepdaughter", " niece", " nephew",
            # the everyday names a child is given instead of "child": "my little boy is 4 and he
            # wont eat veg" was asked who it was about, because none of these was a child word
            " boy", " girl", " little one", " lil un", " lil one", " our kid",
            " youngster", " nipper", " infant", " preschool", " pre school", " school age")
# "fussy" and "picky" are said of a grown-up as often as of a child - "my husband is a fussy
# eater" was answered as a child because the word alone was read as one - so they are only the
# child once the line has not named an adult.
_FUSSY = (" fussy", " fussy eater", " picky", " picky eater", " faddy")
_A_GROWN_UP = (" husband", " wife", " partner", " boyfriend", " girlfriend", " fiance",
               " fiancee", " fiancé", " fiancée", " other half", " my man", " my fella",
               " mate", " mates", " friend", " flatmate", " housemate", " brother", " sister",
               " mum", " mom", " mother", " dad", " father", " adult", " grown up", " grownup",
               " colleague", " lodger", " in laws", " mother in law", " father in law")

_VEG_FIVE_A_DAY = ("Five a day is 400g, and a portion is a handful - about 80g - so one carrot, "
                   "one apple, three heaped tablespoons of peas or a cereal bowl of salad each "
                   "count. The easy version is to add rather than swap: a handful of frozen peas "
                   "or spinach into whatever you are cooking anyway, and fruit where you can see "
                   "it.")
_VEG_A_CHILD = ("A child refusing veg is normal and nearly all of them grow out of it. Keep "
                "putting a small amount on the plate with no pressure and no pudding bribe, keep "
                "serving the two or three they do eat (peas, sweetcorn, raw carrot), and grate or "
                "blend the rest into what they already like - carrot and courgette into a "
                "bolognese, spinach into soup, cauliflower into mash. Eat the same food yourself "
                "at the same table, and expect eight or ten tries before a new one is accepted: a "
                "refused spoon today is not a lost cause.")
# A grown-up is not a child with a bigger plate: nobody grows out of it, there is no pudding to
# bribe, and the thing that helps is taking the argument off the plate.
_VEG_A_GROWN_UP = ("Cook one meal and serve it in parts, keeping the vegetables separate so a "
                   "portion can be taken or left without it becoming a scene, and put a new one "
                   "beside something they already like rather than on its own. Policing the plate "
                   "makes it worse at any age - a handful of dinners eaten happily beats a row "
                   "twice a week - and hiding it is fair too: grate carrot or courgette into a "
                   "bolognese, spinach into soup, cauliflower into mash. A refused vegetable "
                   "usually needs eight or ten calm tries before it is accepted, so one refusal "
                   "is not a verdict.")


def _a_word_in(line, words):
    """Whole words only: " my boy " would otherwise be found inside " my boyfriend ", and a
    partner would be answered as a child."""
    for word in words:
        if word.startswith(" ") and word.endswith(" "):
            if word in line:
                return True
        else:
            if re.search(r"\b" + re.escape(word.strip()) + r"\b", line):
                return True
    return False


_VEG_WHO_IS_IT = ("Who is it who won't eat them - you, a partner, or a child? What helps is "
                   "different for each: five a day is a plate to add to, a grown-up gets a "
                   "portion they can take or leave, and a child gets no pressure and eight or "
                   "ten tries.")

# A third-person pronoun is somebody else, never the speaker: "he wont touch veg" after "i hate
# vegetables" is about him, and reading the person back would answer the wrong one.
# "them" is not on this list: it is the veg far more often than a person ("i want to like them").
_SOMEONE_ELSE = (" he ", " she ", " him ", " her ", " his ", " hers ", " the kids ",
                 " the children ")


# "my 40 year old husband wont eat veg" is a year old in the line and a grown-up in the kitchen:
# an age of 18 or more is not a child's age, so it must not beat the word "husband".
_CHILD_AGE = re.compile(r"\b(\d{1,3})\s*(?:year|yr)s?[\s-]*old\b")
_AGE_WORDS = (" year old", " years old", " year-old")


def _a_child_in(line):
    """A child the line names: a son or a 4 year old, but not a 40 year old husband."""
    for word in _A_CHILD:
        if word in _AGE_WORDS:
            continue
        if _a_word_in(line, (word,)):
            return True
    for match in _CHILD_AGE.finditer(line):
        if int(match.group(1)) < 18:
            return True
    return False


def _who_in_line(line):
    """Who a line says the refusal is about: "me", "grown-up", "child", or None.

    The order is the whole job. The speaker first, because "i wont eat them" is a person asking
    about their own plate. Then an adult the line names, but only when the line has not named a
    child in the same breath. Only then a child, and "fussy"/"picky" count as a child only
    because an adult was not named: "my husband is a fussy eater" is a grown-up.
    """
    if _a_word_in(line, _ME_ASKING):
        return "me"
    a_child = _a_child_in(line)
    if _a_word_in(line, _A_GROWN_UP) and not a_child:
        return "grown-up"
    if a_child or _a_word_in(line, _FUSSY):
        return "child"
    return None


def _who_this_is_about(memory, understood):
    """Who the refusal is about, reading back through the conversation when the line says nobody.

    "i want to like them" and "what can i do" name no person at all, so they were answered as a
    child on the strength of the word "veg"; the person was in the turn before, and that is where
    they are read from: "i wont eat vegetables" / "i want to like them" is the speaker, and
    "my husband is a fussy eater" / "he wont touch veg" is the husband. A pronoun for somebody
    else stops the read-back, because then the line is about them and the earlier speaker is the
    wrong answer. With nothing to go on the answer is None and the caller asks rather than
    assuming a child.
    """
    line = " " + str(understood.get("clean") or "").lower() + " "
    who = _who_in_line(line)
    if who:
        return who
    somebody_else = _a_word_in(line, _SOMEONE_ELSE)
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    said_now = line.strip()
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        text = " " + str(turn.get("user") or "").strip().lower() + " "
        if not text.strip() or text.strip() == said_now:
            continue
        who = _who_in_line(text)
        if who == "me" and somebody_else:
            return None
        if who:
            return who
    return None


def _veg_reply(memory, understood):
    """Five a day for the person asking, and a different answer for the person they name: the
    adult advice (add a handful to what you cook) is not what helps a child who refuses the
    stuff, and a grown-up who refuses it is not a child either.

    The person is read from the line first and from the conversation after it, and a line that
    says a pronoun and nothing anywhere else gets asked who it is: a child is named ("my son",
    "my 4 year old") and an adult is named, so "he" on its own is nobody to guess at.
    """
    who = _who_this_is_about(memory, understood)
    if who == "me":
        return _VEG_FIVE_A_DAY
    if who == "grown-up":
        return _VEG_A_GROWN_UP
    if who == "child":
        return _VEG_A_CHILD
    return _VEG_WHO_IS_IT


# The ways people ask to change their whole diet at once, rather than about one food.
_EAT_BETTER = ("eat better", "eat healthier", "eating better", "eating healthier", "eat more healthily",
               "improve my diet", "eat properly", "eat well", "better diet", "healthy diet",
               "healthy eating", "eat clean", "eat like")

# How much of each nutrient a day, which is a different question from how much is in a food, and a
# different answer again for a teenager: the vitamins and minerals where the number changes at
# that age are the ones with a second reply here. One table, so "how much calcium a day", "how much
# calcium does a teenager need" and "how much iron should a woman have" cannot drift apart.
_A_DAY = {
    "calcium": {
        "adult": "About 700mg of calcium a day for an adult, which is a pint of milk or a pot of "
                 "yoghurt and a matchbox of cheese. Cheese, tinned sardines, almonds and fortified "
                 "cereal all count, and the figure is the same for men and women.",
        "teen": "Teenagers need about 1,000mg of calcium a day for a boy and 800mg for a girl, "
                "which is a pint of milk plus a pot of yoghurt, with cheese or tinned sardines "
                "through the week. Those are the years the bones lay down their density, so it "
                "matters more now than it will at 30.",
    },
    "iron": {
        "adult": "Men need about 9mg of iron a day and women about 15mg until the menopause, which "
                 "is why women run low far more often. Red meat, lentils, beans, fortified cereal "
                 "and dark green veg are the sources; vitamin C in the same meal helps you take it "
                 "up, and tea or coffee with the meal blocks it.",
        "woman": "About 15mg of iron a day, which is nearly twice what a man needs, because of the "
                 "monthly loss: lentils, beans, fortified cereal, red meat and dark green veg are "
                 "the sources, and vitamin C in the same meal helps you take it up. Tea and coffee "
                 "with food block it, so leave a gap either side.",
        "teen": "A teenage boy needs about 11mg of iron a day and a teenage girl about 15mg, "
                "because she loses some every month and both of them are growing fast. Lentils, "
                "beans, fortified cereal, red meat and dark green veg are the sources, and vitamin "
                "C at the same meal helps; tea and coffee with food work against it.",
    },
    "protein": {
        "adult": "About 0.75g of protein per kilo of body weight a day, which is roughly 50g for a "
                 "65kg adult: a palm-sized portion at each meal covers it, from eggs, milk, beans, "
                 "lentils, chicken or fish. You do not need to count grams to get there.",
        "teen": "A teenager needs about the same protein per kilo as an adult, so 45g to 55g a day "
                "for most of them: a palm-sized portion at each meal, and more if they are training "
                "hard or growing fast. Eggs, milk, beans, lentils, chicken and fish all count.",
    },
    "magnesium": {
        "adult": "Men need about 300mg of magnesium a day and women about 270mg, and wholemeal "
                 "bread, nuts, beans, green veg and dark chocolate cover it without any supplement. "
                 "A supplement is for a low a doctor has actually found.",
    },
    "potassium": {
        "adult": "The target is about 3,500mg a day, and most people fall short of it. A banana is "
                 "about 430mg, so potatoes, beans, milk, fruit and vegetables are what closes the "
                 "gap; there is no need for a supplement.",
    },
    "vitamin d": {
        # the same frame as the vitamin-d row below (autumn and winter, all year if you cover up):
        # a person who asks both lines in one conversation must not be told two different things
        "adult": "Take 10 micrograms (400 IU) of vitamin D a day through autumn and winter, roughly "
                 "October to March, and all year if you cover up or stay indoors. Take it as a "
                 "supplement rather than hoping for it from food: oily fish, eggs and fortified "
                 "spread will not get you there.",
        "teen": "Teenagers want the same 10 micrograms (400 IU) of vitamin D a day, from a "
                "supplement from October to March and all year if they cover up or are hardly "
                "outside. It is the one vitamin worth buying, because the food eaten will not "
                "supply it and the UK sun does not in winter.",
    },
    "vitamin c": {
        "adult": "Aim for 40mg of vitamin C a day: one orange, a couple of peppers or a handful of "
                 "broccoli covers it, so a supplement is money for nothing unless a doctor has told "
                 "you otherwise. It also helps you take up the iron in beans and cereal at the same "
                 "meal.",
    },
    "vitamin b12": {
        "adult": "You need 1.5 micrograms of vitamin B12 a day, which any diet with meat, fish, "
                 "covers easily. Vegans need it from fortified milk or cereal or a tablet, because "
                 "plants do not make it and the stores you are born with run out after a few years.",
    },
    "folic acid": {
        "adult": "Take 200 micrograms of folic acid a day as an adult, from a supplement or fortified "
                 "cereal. If you are trying for a baby, or in the first 12 weeks of pregnancy, it is "
                 "400 micrograms and it wants starting before you conceive.",
    },
    "zinc": {
        "adult": "Men need 9.5mg of zinc a day and women 7mg, which meat, beans, nuts, cheese and "
                 "wholegrain cereal cover. More than 25mg a day for a long stretch works against "
                 "copper, so a big zinc supplement is not a thing to take on a guess.",
    },
}

# The words people use for each, longest first so "vitamin b12" is not read as "vitamin b".
_A_DAY_WORDS = (
    ("vitamin b12", "vitamin b12"), ("vitamin b-12", "vitamin b12"), ("b12", "vitamin b12"),
    ("folic acid", "folic acid"), ("folate", "folic acid"), ("folic", "folic acid"),
    ("vitamin c", "vitamin c"), ("vit c", "vitamin c"),
    ("vitamin d", "vitamin d"), ("vit d", "vitamin d"),
    ("calcium", "calcium"), ("magnesium", "magnesium"), ("potassium", "potassium"),
    ("zinc", "zinc"), ("iron", "iron"), ("protein", "protein"),
)

# The teenager is the one age whose figures differ, and "how much calcium does a teenager need"
# was reaching the sleep chart because a bare teenager word was enough for it. The woman is the
# one other word that changes a figure: 15mg of iron is the woman's number, not the man's.
_A_DAY_TEEN = ("teenager", "teenagers", "teen", "teens", "teenage", "16 year", "15 year",
               "14 year", "13 year", "17 year", "18 year", "year 10", "year 11",
               "secondary school")
_A_DAY_WOMAN = ("woman", "women", "female", "girl", "girls", "period", "periods", "menstrual",
                "menstruating", "menopause", "pregnant", "trying to conceive", "breastfeeding")


_CEREAL_BOWLS = (
    # the bowl, the words people call it, and the verdict, led by the bowl they asked about
    (("granola", "crunchy clusters", "crunchy nut clusters"),
     "Granola is oats with oil and sugar baked on, so a 50g serving usually carries about 11 to "
     "15g of sugar, and a bowl of it with milk is closer to a pudding than to porridge. It is not "
     "a bad breakfast, it is a portion problem: measure 40g into a bowl rather than pouring from "
     "the bag, pick a bag with under 10g of sugar per 100g, and eat it with plain yoghurt and "
     "fruit, which is the fibre and the protein that make it last until lunch."),
    (("muesli", "bircher"),
     "Muesli is oats, nuts and dried fruit with no baking, so it carries less added sugar than "
     "granola - usually 7g to 12g per 50g, most of it from the raisins and dates. The fibre is "
     "good and the oats are wholegrain; measure it, because a mugful of muesli plus milk is a "
     "large bowl of energy, and the dried fruit is what adds up."),
    (("cornflakes", "corn flakes", "rice krispies", "coco pops", "frosties"),
     "A plain cornflake is mostly refined flour with a little sugar, and a 30g bowl is about 8g of "
     "sugar before the milk. It is not poison, and a fortified one does give you your B vitamins "
     "and iron; it is just the breakfast that keeps you least full for its calories, so add fruit "
     "or yoghurt to it rather than a second bowl."),
    (("bran flakes", "all bran", "weetabix", "shreddies", "shredded wheat", "wheat biscuits"),
     "These are the wholegrain end of the cereal shelf: bran flakes and Weetabix carry several "
     "times the fibre of cornflakes for about the same calories, and Shredded Wheat has nothing "
     "added at all. Two Weetabix with milk and a banana is a genuinely filling breakfast with "
     "about 4g of fibre, and the sugar comes from the banana rather than the box."),
)

# One line each, for a line that names two bowls: the full verdicts are a paragraph apiece, and
# two paragraphs is not an answer to "granola or muesli".
_CEREAL_SHORT = {
    "granola": "Granola is oats with oil and sugar baked on: fine, but it is a 40g portion - a "
               "50g serving carries about 11g to 15g of sugar, so pick a bag under 10g per 100g.",
    "muesli": "Muesli is unbaked oats, nuts and dried fruit: more fibre than granola and less "
              "added sugar, though the raisins still count, so measure the bowl.",
    "cornflakes": "Cornflakes are refined flour with about 8g of sugar in a 30g bowl: the least "
                  "filling of them for the calories.",
    "bran flakes": "Bran flakes and Weetabix are the wholegrain end, with several times the fibre "
                   "of cornflakes for about the same calories.",
    "porridge": "Porridge is the plainest and the best everyday bowl: no added sugar, about 4g of "
                "fibre in 40g, and it keeps you full until lunch.",
}

PORRIDGE_VERDICT = (
    "Porridge is the better everyday bowl: oats are wholegrain, and a 40g serving has about "
    "4g of fibre and no added sugar, so it keeps you full until lunch. Plain cereal does the "
    "same job with less fibre; granola and crunchy clusters are the ones to watch, because a "
    "50g serving can carry 12 to 15g of sugar. If you want cold cereal, pick a wholegrain one "
    "with under 10g of sugar per 100g.")


def _the_bowl_named(understood):
    """Every bowl the line names, in the order the words appear in it."""
    line = " " + " ".join(str(understood.get("clean") or understood.get("text") or "")
                          .lower().split()) + " "
    found = []
    for names, verdict in _CEREAL_BOWLS:
        spots = [line.find(" " + name) for name in names if (" " + name) in line]
        if spots:
            found.append([min(spots), names[0], verdict])
    spots = [line.find(" " + word) for word in ("porridge", "oat", "oats", "oatmeal")
             if (" " + word) in line]
    if spots:
        found.append([min(spots), "porridge", PORRIDGE_VERDICT])
    found.sort()
    seen, bowls = set(), []
    for at, name, verdict in found:
        if name in seen:
            continue
        seen.add(name)
        bowls.append((at, name, verdict))
    return bowls


def _cereal_verdict(memory, understood):
    """The verdict on the bowl the person named, and the comparison only when they named two."""
    named = _the_bowl_named(understood)
    if not named:
        return PORRIDGE_VERDICT
    if len(named) == 1:
        return named[0][2]
    first, second = named[0], named[1]
    if {first[1], second[1]} == {"porridge", "granola"}:
        return ("Porridge is the better everyday bowl of the two: oats and water with no added "
                "sugar, about 4g of fibre in 40g, and it keeps you full. Granola is the same oats "
                "with oil and sugar baked on - 11g to 15g of sugar in a 50g serving - so it is a "
                "pudding's worth of sugar with a good fibre story. If you like the crunch, granola "
                "on top of plain yoghurt, 20g rather than 50g, is the compromise.")
    if {first[1], second[1]} == {"porridge", "muesli"}:
        return ("Porridge is the plainer of the two and has no added sugar; muesli brings nuts and "
                "dried fruit, so it has more fibre and more sugar - 7g to 12g in 50g. Either is a "
                "good breakfast; muesli needs measuring, porridge needs nothing but oats.")
    # two bowls that are not the porridge pairs get one line each, so the answer stays an
    # answer rather than two paragraphs
    return (_CEREAL_SHORT.get(first[1], first[2].split(".")[0] + ".") + " " +
            _CEREAL_SHORT.get(second[1], second[2].split(".")[0] + "."))


def _a_day(memory, understood):
    """The daily figure for the nutrient the line names: the woman's number or the teenager's
    where it differs, the adult's otherwise.

    A teenager is a person whose numbers are different rather than a child, which is why this one
    entry carries two replies instead of handing the line to the children's guard, and the iron
    figure is the one that also turns on the sex of the person asking.
    """
    clean = " " + ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    name = None
    for word, nutrient in _A_DAY_WORDS:
        if word in clean:
            name = nutrient
            break
    if not name:
        return None
    # how much of a nutrient is in a named food is the portion table's question, and it answers
    # it with the food's own figure ("an egg has about 6g of protein"): a line that names one
    # food is that question whatever it adds around it
    from .cooking import FOOD_NUTRIENTS, _nutrient_food
    if _nutrient_food(clean, FOOD_NUTRIENTS) is not None:
        return None
    figures = _A_DAY[name]
    if any(word in clean for word in _A_DAY_TEEN) and "teen" in figures:
        return figures["teen"]
    if any(word in clean for word in _A_DAY_WOMAN) and "woman" in figures:
        return figures["woman"]
    return figures["adult"]


_PREGNANT = ("pregnant", "pregnancy", "trying for a baby", "trying to conceive",
             "expecting a baby", "we are trying", "first 12 weeks", "antenatal",
             "breastfeeding", "breast feeding", "months pregnant", "weeks pregnant")


def _pregnancy_vitamins(memory, understood):
    """The supplement answer for a pregnancy, which is not the adult figure.

    A pregnant person is the one group whose numbers are not the adult table: folic acid is
    double for the first 12 weeks, vitamin D is wanted all year rather than in winter, and an
    iron supplement is not something to start on a guess. The nutrition guard would otherwise
    send every one of these lines to the conversation lane as a statement about the speaker.
    """
    line = " " + ((understood or {}).get("clean") or "").lower() + " "
    if any(word in line for word in ("vitamin a", "liver", "cod liver", "retinol")):
        return ("Skip vitamin A supplements and liver while you are pregnant: too much of it is "
                "harmful to the baby, and it is the one vitamin people take by accident, in a "
                "multivitamin or a cod liver oil. An ordinary multivitamin is not the one to "
                "take - a pregnancy one leaves the vitamin A out.")
    if any(word in line for word in ("folic", "folate")):
        return ("Take 400 micrograms of folic acid every day from before you conceive until the "
                "end of week 12, which is double the ordinary 200: it cuts the risk of spina "
                "bifida, and food alone will not get you there. After 12 weeks, and while "
                "breastfeeding, the ordinary 200 is enough.")
    if any(word in line for word in ("vitamin d", "vit d")):
        return ("Take 10 micrograms (400 IU) of vitamin D every day, all year, while you are "
                "pregnant and while you breastfeed. The figure is the same as everyone else's, "
                "but you cannot count on the sun or on food, so it comes from a supplement.")
    if "iron" in line:
        return ("You do not need an iron supplement unless a blood test shows you are low: your "
                "blood count is checked at your booking appointment and again at about 28 weeks, "
                "and low iron is treated then. Vitamin C with a meal helps you take up the iron "
                "in food, and tea or coffee with it works against you.")
    if "calcium" in line:
        return ("You need the same 700mg of calcium a day as anyone else - a pint of milk, or a "
                "pot of yoghurt and a matchbox of cheese. The baby takes what it needs from your "
                "bones whatever you eat, so the dairy is for your bones, not theirs, and a "
                "supplement is only for a low a blood test has found.")
    if "b12" in line or "vegan" in line:
        return ("Vitamin B12 matters in pregnancy and breastfeeding, and it comes from meat, fish, "
                "milk and eggs: if you are vegan, take a B12 supplement or a fortified milk, "
                "because the baby's supply comes from yours and the stores run down quietly.")
    return ("Folic acid, 400 micrograms a day until the end of week 12, and vitamin D, 10 "
            "micrograms a day all year, are the two worth taking in pregnancy. Leave out vitamin "
            "A and liver, and take iron only for a low a blood test has found.")

# Where to get more of a nutrient, one row per nutrient: "how do i get more iron" was the
# weight-loss answer on main, "what foods are high in iron" and "how do i get more calcium"
# were shrugs, and "how do i get more vitamin d" was the answer about taking a multivitamin
# with food. A nutrient asked about its sources is a table lookup, so it is one table keyed by
# the nutrient and one row answers every way of asking it.
MORE_OF = (
    (("iron", "ferritin", "anaemia", "anemia", "anaemic", "anemic"),
     "Red meat, liver, lentils, beans, chickpeas, tofu, fortified cereal and dark green veg are "
     "the everyday sources, and a bowl of fortified cereal or a lentil curry is as good as a "
     "steak. Have vitamin C in the same meal - a glass of orange juice, peppers, tomatoes - "
     "because it can double how much you take up, and keep tea and coffee an hour away from the "
     "meal, since the tannins block it. A low a blood test has found is treated with tablets."),
    (("calcium",),
     "A pint of milk, or a pot of yoghurt and a matchbox-sized piece of cheese, covers the "
     "700mg an adult needs. Tinned sardines or salmon with the bones, tofu set with calcium, "
     "fortified plant milk, and kale, broccoli or watercress are the ones that beat the dairy "
     "doubters. Vitamin D is what gets it into the bones, which is why the two are talked about "
     "together."),
    (("vitamin d", "vit d"),
     "Sun is the main source and food will not cover it: from about October to March in the UK "
     "the sun is too weak, so 10 micrograms (400 IU) a day from a supplement is the standard "
     "advice for everyone. Oil-rich fish, egg yolk, and fortified cereal or spread have some, but "
     "you would need a lot of them. Do not take more than 100 micrograms a day."),
    (("b12", "vitamin b12", "b-12"),
     "B12 is only in animal foods: meat, fish, milk, cheese and eggs, so a small pot of yoghurt "
     "or a portion of fish most days covers it. If you eat vegan, or very little of those, take a "
     "supplement (about 10 micrograms a day or 2000 a week) or choose plant milks with B12 added, "
     "because the body's stores last years and the shortage creeps up unnoticed."),
    (("potassium",),
     "Bananas get the credit, but potatoes, beans, lentils, tomatoes, spinach and orange juice "
     "have as much or more. Adults want about 3,500mg a day, and five portions of veg plus a "
     "potato or a banana gets most people there. If a kidney problem has been diagnosed, ask "
     "before adding potassium-rich food."),
    (("magnesium",),
     "Nuts, seeds, wholemeal bread, porridge oats, beans, lentils and dark green veg are the "
     "sources, and about 300mg a day covers an adult. A handful of nuts and a bowl of porridge "
     "is most of it. Supplements are only worth it if a blood test has shown a low."),
    (("zinc",),
     "Meat, shellfish, eggs, milk, beans, lentils and wholemeal bread are the sources, and "
     "adults need about 9.5mg a day for men and 7mg for women. Oysters, beef and pumpkin seeds "
     "are the richest. Taking zinc long-term at high doses upsets the copper balance, so a "
     "supplement is for a low a blood test has found."),
    # Vitamin C and folate were the two the table left out: "what foods are high in vitamin c" got
    # "a pharmacist or your GP can answer that today", "which foods have vitamin c" got the fifteen
    # minute dinners, and every folate line got a shrug or a recipe.
    (("vitamin c", "vit c"),
     "Peppers, oranges, kiwi, broccoli, tomatoes and potatoes with the skin on are the everyday "
     "sources, and a glass of orange juice is plenty for the day. Vitamin C is easily destroyed by "
     "heat, so steam or eat them raw where you can, and five portions of fruit and veg covers an "
     "adult without anything extra."),
    (("folate", "folic acid"),
     "Green veg, lentils, beans, oranges and fortified cereal are the everyday sources, and about "
     "200 micrograms a day covers an adult without trying. Anyone pregnant, or trying for a baby, "
     "is advised 400 micrograms of folic acid a day as a supplement from before conception until "
     "12 weeks, and that is not something food alone can cover."),
    (("omega 3", "omega-3", "oily fish", "fish oil"),
     "One portion of oily fish a week is the advice: salmon, mackerel, sardines, herring, "
     "trout, pilchards or fresh tuna, about 140g cooked. Tinned sardines or mackerel count and "
     "are the cheapest way. If you do not eat fish, walnuts, chia, flaxseed and rapeseed oil "
     "give the plant kind, which the body converts only a little of, so a supplement is "
     "reasonable for a vegan."),
)

# The words that say the line is asking where a nutrient comes from, not how much of it to have
# (that is nutrient-a-day) and not what is in one named food (that is the food table).
# The sources of a nutrient are asked for with the meal, not the nutrient: "what should i eat
# for iron" and "what can i eat for calcium" are where the iron and the calcium come from, and
# they were the dinner table's question - "Here's my pick: tuna pasta in 15 minutes" - while
# "what should i have for iron" and "what foods are high in iron" both got the sources. The
# word "eat" is what the two families were split on, so the eating shapes are ask words here.
_MORE_OF_ASK = ("more", "get more", "getting more", "increase", "boost", "add", "sources",
                "source", "foods", "which foods", "what foods", "high in", "rich in", "best way",
                "best ways", "how do i get", "how can i get", "want more", "need more",
                "plenty of", "top up", "up my", "deficient", "deficiency", "enough",
                "eat for", "have for", "should i eat", "can i eat for", "could i eat for",
                "do i eat", "what to eat", "should i have")


def _more_of(memory, understood):
    """Where to get more of the nutrient this line names, or None when it names none."""
    line = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    # how much of a nutrient is in one named food is the food table's question, and it answers it
    # with that food's figure ("an egg has about 6g of protein"): a line that names a food is
    # that question, whatever else it says around it
    from .cooking import FOOD_NUTRIENTS, _nutrient_food
    if _nutrient_food(line, FOOD_NUTRIENTS) is not None:
        return None
    for words, text in MORE_OF:
        if any(" " + word + " " in line or line.strip().startswith(word + " ") for word in words):
            return text
    return None


def _low_iron(memory, understood):
    """A person who thinks their iron is low wants a blood test before a shopping list."""
    return ("That is worth a blood test rather than a guess: tiredness, breathlessness on the "
            "stairs, pallor, brittle nails and hair loss are the usual signs, and your GP can "
            "check a full blood count in a few days. Do not start iron tablets on suspicion - "
            "too much iron is harmful - but do eat iron-rich food meanwhile: red meat, lentils, "
            "beans, fortified cereal and dark green veg, with vitamin C in the same meal and tea "
            "or coffee kept an hour away.")


# What a nutrient is for. "is iron good for you", "is calcium good for you", "is magnesium good
# for you", "is zinc good for you", "is b12 good for you" and "what does iron do" were every one of
# them the search hedge, and "is vitamin d good for you" and "is vitamin c good for you" were the
# pharmacist card. It is one question about one nutrient, so it is one table keyed by the nutrient
# (the same shape as MORE_OF and _A_DAY, so the three cannot drift apart), and the reply says what
# the nutrient does, where it comes from, and whether a supplement is worth buying.
NUTRIENT_ROLE = (
    (("iron", "ferritin"),
     "Iron carries oxygen round your body in red blood cells, which is why a shortage shows up as "
     "tiredness, breathlessness on the stairs, pallor and brittle nails or hair loss. Red meat, "
     "liver, lentils, beans, fortified cereal and dark green veg are the everyday sources, and "
     "vitamin C in the same meal helps you take it up. Too much iron is harmful, so tablets are "
     "for a low a blood test has found rather than for a guess."),
    (("calcium",),
     "Calcium is what bones and teeth are built from, and it also matters for muscles and for "
     "blood clotting: an adult needs about 700mg a day, which is a pint of milk or a pot of "
     "yoghurt and a matchbox of cheese. Vitamin D is what gets it into the bones, so the two go "
     "together. A supplement is worth it only if you cannot manage the dairy, and 500mg is plenty."),
    (("vitamin d", "vit d"),
     "Vitamin D is what lets your body take up calcium, so it is the bones and muscles that suffer "
     "without it, and a low is linked with tiredness and aching. Sun makes most of it, so in the "
     "UK take 10 micrograms (400 IU) a day from October to March, and all year if you cover up or "
     "are indoors a lot. More than 100 micrograms a day is too much."),
    (("vitamin c", "vit c"),
     "Vitamin C is for skin, gums, blood vessels and healing, and it can double how much iron you "
     "take up from a meal. 40mg a day is plenty, and one orange, a couple of peppers or a handful "
     "of broccoli covers it, so a supplement is money for nothing. It is destroyed by heat, so "
     "steam rather than boil where you can."),
    (("vitamin b12", "b12", "b-12"),
     "B12 is for nerves and red blood cells, and a shortage creeps up over years because the liver "
     "stores it: tingling hands, tiredness, a sore tongue and low mood are the usual signs. It is "
     "only in animal foods - meat, fish, milk, eggs - so if you eat vegan take it from fortified "
     "milk or cereal, or a tablet of about 10 micrograms a day."),
    (("magnesium",),
     "Magnesium is used in hundreds of reactions, from muscles and nerves to blood sugar, and an "
     "adult needs about 300mg a day. Nuts, seeds, wholemeal bread, porridge, beans, lentils and "
     "dark chocolate cover it, so a supplement buys little unless a blood test has found a low."),
    (("zinc",),
     "Zinc is for healing, immunity and the sense of taste and smell, and adults need about 9.5mg "
     "a day, 7mg for women: meat, shellfish, eggs, milk, beans and wholemeal bread cover it. More "
     "than 25mg a day for months works against copper, so a big zinc supplement is not worth it."),
    (("potassium",),
     "Potassium is what keeps the heart beating evenly and the muscles working, and adults want "
     "about 3,500mg a day. Potatoes, beans, lentils, milk, bananas and tomatoes are the everyday "
     "sources, and most people fall short of it without trying. If a kidney problem has been "
     "diagnosed, ask before adding potassium-rich food."),
    (("folate", "folic acid"),
     "Folate is for making new cells, which is why it matters most in early pregnancy: 400 "
     "micrograms a day from before conception until week 12 cuts the risk of spina bifida. "
     "Outside pregnancy, green veg, beans, lentils and fortified cereal cover the 200 micrograms "
     "an adult needs."),
)

# The ask is the verdict, not the figure: "how much iron a day" is nutrient-a-day's question and
# "what foods are high in iron" is more-of-a-nutrient's. Byworded reads are fine here because the
# key carries a nutrient name, so nothing fires without one.
_ROLE_ASK = ("good for", "bad for", "what does", "does it do", "why do i need", "why do you need",
             "benefits", "benefit", "important", "needed", "necessary", "what is it for",
             "point of", "any good", "useful", "role", "what is the point")


def _nutrient_role(memory, understood):
    """What the nutrient this line names does, or None when it names none."""
    line = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    from .cooking import FOOD_NUTRIENTS, _nutrient_food
    if _nutrient_food(line, FOOD_NUTRIENTS) is not None:
        return None
    for words, text in NUTRIENT_ROLE:
        if any(" " + word + " " in line or line.strip().startswith(word + " ") for word in words):
            return text
    return None


# A carton that is not milk is answered as itself. The row's key has named "oat milk" and
# "almond milk" since it was written, and the reply was the cow's paragraph: "is oat milk
# healthy" was told that a 200ml glass has 7g of protein, which is true of the cow and not of the
# oat, and "oat milk or almond milk" was the porridge recipe. The numbers below are a 200ml glass
# of the unsweetened, fortified carton, because that is the one that replaces milk; a sweetened
# one carries two or three teaspoons of sugar on top of what is listed.
_PLANT_MILKS = (
    (("soy milk", "soya milk", "soy bean milk", "soybean milk", "soy", "soya"),
     "Soya is the closest to milk: about 7g of protein in 200ml, the same as semi-skimmed, and it "
     "is the one to take if protein is what you are replacing. Check the carton says calcium and "
     "B12 added - those come from the fortification, not from the bean - and buy it unsweetened, "
     "because the sweetened soya is nearer a pudding."),
    (("oat milk", "oat drink", "oatly", "oat"),
     "Oat is the creamiest and the best in coffee and porridge: about 2g of protein in 200ml, and "
     "7 to 8g of sugar that comes from the oats themselves rather than from a spoon. Buy the "
     "barista or no-added-sugar carton, and check it is fortified with calcium and B12, because "
     "unsweetened oat is thin on both."),
    (("almond milk", "almond drink", "almond"),
     "Almond is the lightest: about 1g of protein and 50 calories in 200ml, and thin in coffee. "
     "It is worth having only if the carton is fortified, since almonds are a small part of it, "
     "and it is no good at all for a nut allergy."),
    (("coconut milk drink", "coconut drink", "coconut milk"),
     "The coconut drink in a carton has almost no protein - about 0.5g in 200ml - and around 40 "
     "calories, and it tastes of coconut, so it is for a smoothie or a curry rather than a cup of "
     "tea. The tin of coconut milk is a cooking ingredient with 20g of fat a serving, not a milk "
     "to drink."),
    (("rice milk", "rice drink", "rice"),
     "Rice milk is sweet without added sugar and has about 1g of protein in 200ml, the least of "
     "them. It is not the drink for a child under five, because of the arsenic rice takes up; a "
     "fortified soya or oat carton is what a toddler should have instead."),
    (("hemp milk", "hemp drink", "hemp"),
     "Hemp has about 3g of protein in 200ml, a nutty taste and it does not split in hot coffee. "
     "It is the one to take if soya and nut milks are both out."),
    (("pea milk", "pea protein milk", "pea"),
     "Pea milk has about 6g of protein in 200ml, close to soya, and it froths well. It tastes of "
     "pea on its own, so it is better in coffee than in a glass."),
)

# Which milk for what, for the line that asks for a ranking rather than about one carton.
_THE_MILK_RANKING = (
    "For protein, soya or pea: about 6 to 7g in 200ml, against 1 to 2g for oat, almond and rice. "
    "For coffee and porridge, oat, because it is creamy and does not split. For the fewest "
    "calories, almond or the coconut drink, at about 40 to 50 a glass. Whichever you pick, take "
    "the unsweetened one and check the carton says calcium and B12 added: calcium, iodine and B12 "
    "are the three milk supplies and a plant carton does not unless it says so.")

# The environment is its own question about the carton, and it is the one a plant milk is usually
# asked about: "is oat milk better for the environment" was answered with the oat's protein and
# sugar, which is a confident answer to a different question. These are the per-litre figures from
# the standard life-cycle comparison (Poore and Nemecek, 2018): dairy about 3 kg of CO2e a litre,
# oat and soya about 1, rice about 1.2 and almond about 0.7, with a small fraction of dairy's land.
# Almond is the thirstiest - several hundred litres of water a litre of milk - and rice the highest
# of the plant milks after that, so the swap helps on carbon whichever carton it is.
_MILK_AND_THE_PLANET = (
    # The whole comparison is in the first sentence on purpose: a follow-up turn repeats only the
    # opening sentence of an answer it has given before, and "is almond milk bad for the
    # environment" cut to "plant milks beat dairy" would not have said anything about the almond.
    "Yes, on carbon every plant milk is far below dairy: a litre of oat or soya is about a third "
    "of dairy milk's emissions and a fraction of its land, rice is a little higher because paddy "
    "fields make methane, and almond is the lowest of them but the thirstiest, at several hundred "
    "litres of water a litre. So take oat or soya if it is water you are counting as well as "
    "carbon, and remember the carton matters much less than the swap: the milk nobody drinks is "
    "the worst of the lot.")

# The words that ask about the planet rather than about the body. "water" on its own is not one of
# them, because half the milk questions in the deck are about a watery pint.
_THE_PLANET = ("environment", "environmental", "environmentally", "emissions", "carbon", "co2", "co 2", "planet",
               "climate", "sustainable", "sustainability", "land use", "water use", "footprint",
               "greenhouse", "methane", "eco friendly", "eco-friendly", "greener", "greenest",
               "global warming", "greenhouse gas", "how much water", "litres of water",
               "liters of water", "water footprint", "gallons of water")

# A child's milk is the child's question: "can my toddler have oat milk" is about what a small
# child may drink all day, and the family domain answers it with the amounts and the age.
_MILK_FOR_A_CHILD = ("baby", "babies", "toddler", "toddlers", "weaning", "weaned", "wean",
                     "breastfed", "formula", "one year old", "1 year old", "two year old",
                     "2 year old", "under 5", "under five", "under two", "under 2",
                     "my kid", "my child", "my son", "my daughter")


# Plain milk, and dairy itself, keeps the answer it had: the plant paragraph is for a carton that
# is not milk, and for the line that asks which to take.
_COW_MILK_REPLY = (
    "Milk is good for you: a 200ml glass has about 7g of protein and a third of an adult's daily "
    "calcium, and it is one of the cheapest ways to get both. Semi-skimmed is the sensible default "
    "for most adults - the same protein and calcium as whole milk with about half the fat. Whole "
    "milk is the right one for a child under two, and a fortified plant milk is the swap if you do "
    "not do dairy.")

# "is milk ok" is two questions in three words: whether milk is all right to drink, and whether
# the bottle in the fridge is still all right. The ask is the same one this row now answers, and a
# bare "ok" or "safe" with no word of goodness in the line is as likely the carton, so the answer
# covers it in one sentence rather than picking one reading.
_THE_FRIDGE_CHECK = (
    "If the question was about the bottle in your fridge rather than about milk itself, smell it: "
    "sour or lumpy and it goes, whatever the date says.")
_A_BARE_OK_ASK = ("ok", "okay", "alright", "fine", "safe", "any good", "worth it")


def _a_bare_word(said, words):
    """True when one of `words` is said on its own, at either end of the line as well as inside.

    `" ok "` alone missed the commonest way this is asked: "is milk ok" ends with the word, and
    an "ok" at the very front is the same filler ("ok is milk fine"). Matching the ends is what
    keeps that line's fridge check; without it the row answered the bare "is milk ok" with the
    paragraph about milk being good for you, which does not answer it.
    """
    said = " " + said.strip() + " "
    for word in words:
        if f" {word} " in said or said.startswith(f" {word} ") or said.rstrip() == f" {word}":
            return True
        if said.rstrip().endswith(f" {word}"):
            return True
    return False
_NOURISHING = ("good", "healthy", "fattening", "bad", "calcium", "protein", "vitamin", "vitamins",
               "nutrient", "nutrients", "diet", "fatten", "health", "benefit", "benefits", "need",
               "better", "worse", "calorie", "calories", "strong", "stronger")

# The words that ask for a ranking rather than for one carton.
_WHICH_MILK = ("which milk", "which is best", "what milk", "best milk", "best alternative",
               "plant milk", "plant milks", "plant based", "plant-based", "dairy alternative",
               "dairy alternatives", "milk alternative", "milk alternatives", "non dairy",
               "non-dairy", "instead of milk", "replace milk", "switch from milk", "switch to",
               "milk is best", "healthiest milk")


def _a_plant_milk(memory, understood):
    """The carton the line named, or the ranking when it asks which milk to take."""
    said = " " + (understood.get("clean") or understood.get("norm_text") or "").lower() + " "
    if any(" " + word in said for word in _MILK_FOR_A_CHILD):
        return None
    # The planet comes before the carton: the line names a milk to ask about emissions, and the
    # protein and sugar of that one carton is not the answer to it.
    if any(" " + word + " " in said or said.rstrip().endswith(" " + word)
           or (" " + word + "s ") in said for word in _THE_PLANET):
        return _MILK_AND_THE_PLANET
    named = []
    for words, said_about_it in _PLANT_MILKS:
        if any(" " + word + " " in said or said.rstrip().endswith(" " + word)
               or (" " + word + "s ") in said for word in words):
            named.append((words[0], said_about_it))
    # A longer name wins over its own short form: "coconut milk drink" is not "coconut" twice.
    kept = []
    for name, text in named:
        if not any(name != other and name in other for other, _ in named):
            kept.append((name, text))
    if len(kept) == 1:
        return kept[0][1]
    if len(kept) > 1:
        # Two cartons in one line is the comparison, and each gets its own sentence.
        return " ".join(text for _, text in kept[:2]) + " " + (
            "If it is protein you are after, take the one with more of it; if it is the cup of "
            "tea or the coffee, take the one that does not split.")
    if any(word in said for word in _WHICH_MILK):
        return _THE_MILK_RANKING
    if (_a_bare_word(said, _A_BARE_OK_ASK)
            and not any(word in said for word in _NOURISHING)):
        return _COW_MILK_REPLY + " " + _THE_FRIDGE_CHECK
    return _COW_MILK_REPLY


def _coffee_or_tea(memory, understood):
    """A verdict on the drink the line named. "is tea good for you" was the coffee answer, word
    for word, because one row covers both drinks and the reply opened "Coffee is not the
    villain it was" - a sentence about the wrong cup."""
    line = " " + (understood.get("clean") or "").lower() + " "
    tea = " tea" in line or "teas " in line
    coffee = "coffee" in line or "espresso" in line or "latte" in line
    if tea and not coffee:
        return ("Tea is fine: four or five cups of ordinary black tea is about half the caffeine "
                "of the same number of coffees, it counts towards your fluid, and the tea itself "
                "has no calories - the sugar and the biscuits are what add up. Herbal and green "
                "teas are caffeine-free or nearly, so they are not the ones to worry about in "
                "the evening. If you are anaemic or take iron tablets, keep the cup an hour away "
                "from a meal, because the tannins cut how much iron you take up.")
    return ("Coffee is not the villain it was: up to about four cups a day is linked to no harm "
            "for most adults, and it may be mildly protective for the heart and liver. The "
            "trouble is what goes in it (a latte is 120 calories) and drinking it late enough to "
            "spoil your sleep. Filter coffee raises cholesterol a little more than espresso, "
            "which is why paper filters are still worth using.")



def _not_a_keeping_question(understood):
    """Whether the line is a which-is-better question rather than a keeping one."""
    return not a_food_is_being_kept(understood)

def _wholegrain(memory, understood):
    """The wholemeal swap for the grain the line names: rice, or pasta."""
    said = " " + " ".join(str(word).lower() for word in (understood.get("words") or [])) + " "
    pasta = any(word in said for word in (" pasta", " spaghetti", " macaroni", " noodles",
                                          " penne", " fusilli", " tagliatelle"))
    rice = " rice" in said
    head = ("Wholewheat pasta keeps the bran and the germ, so it has about three times the fibre "
            "of white" if pasta and not rice else
            "Brown rice keeps the bran and the germ, so it has about three times the fibre of white")
    rest = ("White rice and pasta are not bad - they just give you less fibre and less staying "
            "power. Both keep their calories, around 130 to 150 per 100g cooked, so the swap is "
            "about fibre and fullness, not about weight.")
    if pasta and not rice:
        rest = ("White pasta is not bad - it just gives you less fibre and less staying power. "
                "It keeps its calories, around 130 to 150 per 100g cooked, so the swap is about "
                "fibre and fullness, not about weight. Wholewheat takes a minute or two longer "
                "and holds sauce well; the half-and-half bag is an easy start if the family "
                "notices the change.")
        return head + ", and it has a slower rise in blood sugar too. " + rest
    return (head + " and a slower rise in blood sugar; wholewheat pasta is the same idea against "
            "white pasta. " + rest)


# The rule that keeps a policy row out of the kitchen lives in cooking.py, beside the verbs it
# reads, because every row about an amount of food needs it: `not_a_cooking_question` is shared, so
# "what temperature should i cook pork at" stands the allowance down by the same test that any other
# amount row would use, instead of by a list of wordings on this one row.

# A line about how a piece of meat is cooked is not a line about how much of it is allowed. The
# red meat row is the only row that has to stand down for this, and it reads the cooking verbs the
# rest of the knowledge base already uses, so the test lives here rather than as an avoid list of
# wordings somebody thought of: written as an avoid list it only ever covered what was on it, and
# "what temperature should i cook pork at" was answered with "no more than 70g of red meat a day".
_A_THERMOMETER = re.compile(
    r"\b(?:temperature|temperatures|temp|temps|thermometer|internal|oven|gas mark|how long|"
    r"minutes|mins|done|doneness|medium|rare|medium-rare|well done)\b")


def not_a_cooking_question(understood):
    """True when the line is about a food rather than about how it is cooked.

    False as soon as the line says how hot, how long, or how it is done - "what temperature should
    i cook pork at", "what gas mark for a leg of lamb", "when is the turkey done", "what temp for a
    medium rare steak" - whatever the food is called and however the question is worded. True for
    the questions the allowance answers: "is red meat bad for you", "how much red meat should i
    eat", "how often can i eat steak".
    """
    if not isinstance(understood, dict):
        return True
    clean = understood.get("clean") or ""
    if not isinstance(clean, str):
        clean = " ".join(str(part) for part in clean)
    said = " ".join(("%s %s" % (understood.get("text") or "", clean)).lower().split())
    if COOKING_VERBS.search(said):
        return False
    return not _A_THERMOMETER.search(said)


# The sugary-drink verdict names its own drink: "is squash bad for you" was answered with the
# figures of a can of cola, which is the right answer to a question nobody asked. The words are
# the drinks people say by name; anything else falls through to the cola figures, which is the
# figure the range is set by.
_SWEET_DRINKS = ("lemonade", "squash", "cordial", "irn bru", "lucozade", "sprite", "fanta",
                 "7up", "cherryade", "tonic water", "ginger beer", "cream soda", "soda", "pop",
                 "fizzy drink", "soft drink")


def _sugary_drink_reply(memory, understood):
    text = " " + ((understood.get("text") or understood.get("clean") or "").lower()) + " "
    named = ""
    for word in _SWEET_DRINKS:
        if " %s " % word in text:
            named = word
            break
    tail = ("The sugar is the whole problem: it comes as liquid, so it does not fill you up, and "
            "it is what dentists see. Diet and zero versions cut the sugar and are the sensible "
            "swap rather than a healthy drink; water, or fizzy water with a slice of lemon, is the "
            "free one.")
    if named:
        return ("A glass of %s is about as sugary as cola - roughly 35g in a 330ml glass, seven "
                "teaspoons - and an adult should stay under 30g a day in total. %s"
                % (named, tail))
    return ("A 330ml can of cola has about 35g of sugar, seven teaspoons, and lemonade, squash "
            "and the rest are in the same range - an adult should stay under 30g a day in total. "
            + tail)


ENTRIES = [
    # --- calories in everyday food -----------------------------------------
    entry("sugar-in-coke", (("coke", "coca cola", "cola", "fizzy drink", "soft drink", "pepsi",
                             "lemonade"), ("sugar", "calorie", "calories", "how much sugar",
                                           "teaspoons", "spoonfuls")),
          "A 330ml can of regular Coke has 35g of sugar, about seven teaspoons, and 139 calories. "
          "Diet and zero versions have none, and the newer zero-sugar versions taste much closer "
          "to the original than they used to."),
    entry("sugar-in-juice", (("orange juice", "fruit juice", "juice", "smoothie"),
                             ("sugar", "healthy", "good for", "how much", "calorie", "calories",
                              # "can i drink orange juice" is the same fact as "is fruit juice
                              # healthy", and it was reaching the citrus-squeezing method in
                              # fruit.py because it carries the noun "juice"
                              "can i drink", "should i drink", "bad for", "ok to drink",
                              "okay to drink", "as bad as", "better than", "worse than")),
          "Fruit juice has as much sugar as the equivalent amount of Coke - about 20g in a 200ml "
          "glass of orange juice - with none of the fibre of the fruit and none of the chewing that "
          "makes you feel full. One small glass a day with a meal is the usual advice; a smoothie is "
          "not much better once the fruit is blended.",
          # grapefruit and its juice change how some medicines are broken down, so "can i drink
          # grapefruit juice with statins" is a pharmacist's question: a sugar fact is a wrong
          # answer to it, and an honest pass leaves room for the medicine answer
          avoid=("statin", "statins", "medication", "medicines", "medicine", "pills", "tablets",
                 "warfarin", "blood pressure tablets", "antibiotics")),
    # "Is coke bad for you" and "is lemonade healthy" were the composer's "not sure about that
    # one", beside a fruit-juice row that answers the same question about a glass of juice. One
    # verdict for the drinks, keyed by the names people use, and the diet versions stand down to
    # the sweetener row below.
    entry("a-sugary-drink",
          (("coke", "cola", "coca cola", "pepsi", "lemonade", "squash", "fizzy drink",
            "fizzy drinks", "soft drink", "soft drinks", "soda", "pop", "cordial",
            "irn bru", "lucozade", "sprite", "fanta", "7up", "tonic water", "ginger beer",
            "cream soda", "cherryade"),
           ("bad for", "good for", "healthy", "unhealthy", "is it ok", "is it okay",
            "ok to drink", "okay to drink", "how bad", "should i drink", "can i drink",
            "is it bad", "worth drinking", "better than")),
          _sugary_drink_reply,
          # the diet versions are the sweetener question, the sugar count is the sugar row, and a
          # glass of juice has its own answer; a spill is neither
          avoid=("diet", "zero", "sugar free", "sugar-free", "sweetener", "sweeteners",
                 "aspartame", "how much sugar in", "how many calories in", "calories in",
                 "juice", "smoothie", "energy drink", "sports drink", "recipe", "cocktail",
                 "mixer", "spill", "spilled", "stain", "carpet", "sofa", "fridge", "freeze",
                 "ice cube", "bottle", "can i keep", "goes flat", "out of date",
                 # plain fizzy water has none of the sugar this card is about
                 "fizzy water", "sparkling water", "carbonated", "soda water",
                 "club soda")),

    # Plain fizzy water is the one drink in the fizzy aisle with no sugar in it, and it was a
    # hedge: "is fizzy water bad for you", "is sparkling water good for you". Keyed by what it is
    # called, and the flavoured bottles stand down because they are the sugary-drink question.
    entry("sparkling-water",
          # The phrases, not the bare adjectives: "sparkling" and "fizzy" are the wine's and the
          # cider's words too, so `is sparkling wine bad for you` was told there is no sugar and no
          # calories in water, and `is fizzy wine bad for you` the same. Every water line says the
          # water, so the two-word phrases cover them all and the adjectives are the alcohol rows'
          # to answer.
          (("sparkling water", "fizzy water", "carbonated water", "soda water", "club soda",
            "sparkling water drink"),
           ("bad for", "good for", "healthy", "unhealthy", "safe", "is it ok", "is it okay",
            "ok to drink", "teeth", "instead of", "count", "hydrate", "drink", "day")),
          "Sparkling water is water with carbon dioxide dissolved in it, so there is no sugar and "
          "no calories in it and it counts towards your fluids like still water. The fizz is a "
          "weak acid, which is why dentists say drink it with a meal rather than sip it all day, "
          "and it can leave you feeling bloated. The flavoured bottles are the ones to read: many "
          "of them carry sugar or sweetener.",
          # the flavoured and sweetened ones are the sugary-drink card, and a machine that will
          # not fizz or a bottle that has gone flat is a different question
          avoid=("flavoured", "flavored", "sweetener", "sugar free", "sugar-free", "diet",
                 "lemonade", "coke", "cola", "squash", "goes flat", "gone flat", "went flat",
                 "machine", "soda stream", "sodastream", "canister", "bottle of gas",
                 "make my own", "carbonate at home")),
    # The sweet, asked about as a food. "is chewing gum bad for you" and "how much sugar in
    # chewing gum" are everyday questions about a thing people chew, and the smoking entry keys
    # bare "gum" for nicotine gum, so both reached the stop-smoking plan.
    entry("chewing-gum-sweet",
          (("chewing gum", "chewing-gum", "gum"),
           ("bad", "good", "healthy", "unhealthy", "calorie", "calories", "teeth", "tooth",
            "hurt", "stomach", "swallow", "eat", "day", "much", "any")),
          "Sugar-free gum is good for your teeth: the chewing makes saliva, which washes the acid "
          "off, and a regular piece holds only about 2g of sugar anyway, so sugar-free is the one "
          "to pick. Give it to nobody's dog, though - the xylitol in sugar-free gum is poisonous "
          "to them.",
          # "the gum under my tooth is swollen" is the tissue, not the sweet: the singular gum
          # beside a possessive or a tooth is the body, and a person with an abscess was being
          # told to chew sugar-free gum for their teeth. The plural and the chewing forms still
          # answer, so "my gums are fine, is chewing gum bad for them" keeps the sweet.
          avoid=("nicotine", "quit", "quitting", "stop smoking", "smoking", "smoke", "vape",
                 "vaping", "patch", "patches", "teething", "baby", "toddler", "sore", "bleed",
                 "bleeding", "gums are", "my gums", "gum is", "gum has", "gum feels",
                 "gum hurts", "gum looks", "my gum", "the gum", "gum under", "gum line",
                 "gumline", "gum disease", "gum infection", "swollen", "receding", "dentist",
                 "hair", "carpet", "jeans", "clothes", "shoe", "floor", "table", "stuck",
                 "off my", "out of")),
    # --- what to eat and what to cut ---------------------------------------
    entry("belly-fat", (("belly fat", "stomach fat", "tummy fat", "spot reduce", "love handles"),
                        ("lose", "get rid", "reduce", "burn", "how do i", "can i")),
          "You cannot choose where fat comes off: sit-ups build the muscle under it, not the layer "
          "on top. A calorie deficit shrinks fat everywhere, and where it goes first is down to "
          "genetics, so for most people the waist is the last place to change."),
    entry("sugar-craving", (("sugar", "sweets", "sweet", "chocolate", "biscuits", "cake",
                             "craving", "cravings"),
                            # "reduce" and "lower" are the same ask as "cut": "how do i reduce
                            # sugar in my diet" was reaching the cooking-words row
                            ("stop", "cut", "cutting", "reduce", "reducing", "lower", "give up",
                             "quit", "less", "crave",
                             "cravings", "addicted", "addiction", "at night", "evening",
                             "after dinner",
                             # "she cant have much sugar" is the same question as "how do i cut
                             # down on sugar", said as a rule somebody has been given. It was the
                             # baby-food table's, because that table took a bare pronoun as proof
                             # a baby was meant - so an adult in the line was told "there is no
                             # need for sugar at all before two". The salt row already carries
                             # these phrases on main, so the sugar row matches it.
                             "cant have much", "cant eat much", "cannot have much",
                             "cannot eat much", "shouldnt have", "shouldnt eat")),
          "Cut the sugar you drink first, because liquid sugar does not fill you up at all, then "
          "make sure you are eating protein and fibre at meals: most evening sugar cravings are "
          "hunger from a lunch that was too small or too white. Keep the sweet thing out of the "
          "house rather than relying on willpower at nine at night, and expect three or four days "
          "of feeling deprived before it settles.",
          # A cake in a tin is a cake to bake, not a craving to break: "how do i stop cake
          # sticking to the tin" is the tin question, and the kitchen words below are what tells
          # the two apart. "how do i stop the cake burning" is the same shape - two craving words
          # and nothing else - and a bake going wrong in the oven belongs to the cooking domain.
          avoid=("stick", "sticks", "sticking", "stuck", "tin", "tins", "tray", "trays",
                 "grease", "greased", "parchment", "springform", "bake", "baked", "baking",
                 "oven", "flour", "dough", "batter", "pan", "pans", "paper",
                 "burn", "burns", "burnt", "burned", "burning",
                 # "no sugar in my tea please" is how somebody takes their drink, and the tea
                 # row answers it: the limit wording above must not take a drink order. The
                 # phrases are the order itself, not any line with "my tea" in it, because
                 # "how do i cut sugar out of my tea" is a cutting-down question.
                 "no sugar in my tea", "no sugar in my coffee", "no sugar in my cup",
                 "no sugar for me", "no sugar thanks", "without sugar in my tea",
                 "without sugar in my coffee", "just milk thanks",
                 # "how do i stop a cake going stale" is a keeping question: "stop" plus "cake"
                 # was enough for this row, and a cake going stale is the cooking domain's
                 "stale", "going stale", "go stale", "goes stale", "gone off", "keep fresh",
                 "keeps fresh", "keep it fresh",
                 # a cake that crumbles is a bake gone wrong, not a craving: "how do i stop my
                 # cake from crumbling" is two craving words ("stop", "cake") and nothing else,
                 # and with the cooking rows holding cakes at arm's length this row took it
                 "crumbly", "crumbles", "crumb", "crumbs", "crumbling", "falls apart",
                 "falling apart", "soggy", "sank", "sunken", "didnt rise", "risen",
                 # a cake drying out in the oven is the bake's fault too: "how do i stop my cake
                 "dry", "drying", "dried", "sink", "sinks", "sinking", "sunk", "flat",
                 "recipe", "recipes", "icing", "frosting", "sponge", "sponges", "loaf",
                 # "why do i crave sugar" is the mechanism question: this key has "crave", so it
                 # took the line from science's craving-why
                 "why", "cause", "causes", "what causes"),
          bias=1),
    entry("sugar-swaps", (("sugar", "sugary", "sweets", "biscuits", "chocolate"),
                          ("cut out", "give up", "swap", "swaps", "instead", "replace",
                           "alternative", "less sugar", "reduce", "cut down", "eat instead")),
          "Swap rather than erase: a yoghurt with fruit instead of a yoghurt with sugar in it, two "
          "squares of dark chocolate instead of a bar of milk, nuts or cheese instead of biscuits, "
          "and sparkling water or squash instead of fizzy drinks. Keep one sweet thing you really "
          "like, at a set time, rather than cutting sugar out completely - the all-or-nothing "
          "version is the one that collapses in a fortnight.",
          # "i cut out dairy" is a statement about their diet, not a request for swaps
          keep=("cut out",)),
    # The plain question about the sweet itself: "is sugar bad for me" was a hedge from the
    # composer, and the rows either side of it answer "how do i stop eating it" and "how much is
    # in a can". What people want is the number and whether it is poison.
    entry("sugar-plain",
          # sweeteners are their own row's question: "are sweeteners bad for you" was answered
          # with aspartame before this row existed, and it still is
          # "honey" is not in this key: a comparison with honey is the honey row's question
          # ("is honey healthier than sugar" answered "80 per cent sugar" before this row and
          # was taken by it once the row existed), and "is honey good for you" is the honey row
          # too. The reply still names honey in the 30g line, which is where it belongs.
          (("sugar", "sugars", "sugary", "added sugar", "free sugar", "free sugars", "white sugar"),
           ("bad for me", "bad for you", "bad for us", "bad", "healthy", "healthier",
            "healthiest", "unhealthy", "poison",
            "poisonous", "safe", "ok", "okay", "fine", "addictive", "addicted", "addiction",
            "cause diabetes", "causes diabetes", "diabetes", "worse", "really", "truth",
            "is it", "is sugar", "are sugars")),
          # a reviewer's blocker: this row takes "is sugar addictive" and "is brown sugar
          # healthier" on its key words, and the body answered neither. Three clauses, no more:
          # habit not addiction, brown sugar is white sugar, and the 30g line. The diabetes
          # sentence is gone because `sugar-diabetes` answers those lines itself and this row
          # was only repeating it.
          ("In the amount most people eat, sugar is not poison, but it is the easiest calorie to "
           "take in unnoticed and the main cause of tooth decay. It is habit-forming rather than "
           "addictive like nicotine. Brown sugar is white sugar with molasses: same calories, "
           "same limit. Keep free sugars - the added sort, plus honey, syrup and juice - under "
           "30g a day, about seven teaspoons, which one can of Coke uses up. Whole fruit is the "
           "exception: the fibre slows it down."),
          # how to cut it, why you crave it and how much is in a thing all have their own rows,
          # and so does every other sweet that happens to carry the word
          avoid=("cut down", "cut out", "cutting", "give up", "quit", "stop eating", "crave",
                 "craves", "craving", "cravings", "swap", "swaps", "instead", "replace",
                 "how much sugar in", "in a can", "in coke", "in a coke", "in a glass", "teaspoons",
                 # "sugaring" is the hair-removal technique, and the loose match reads it as a
                 # form of this row's own word, so it cannot go in the avoid as a bare word -
                 # that stands the row down for "is sugar bad for me" too. The phrases are what
                 # a question about the technique looks like.
                 "what is sugaring", "sugaring better", "sugaring or", "leg sugaring",
                 "body sugaring", "sugaring hair",
                 "wax", "waxing", "shave", "shaving", "ingrown", "scrub", "hair", "skin",
                 "baby", "babies", "toddler", "kid", "kids", "child", "children", "dog", "cat",
                 "bake", "baking", "cake", "icing", "meringue", "caramel", "toffee",
                 "substitute for sugar", "replacement for sugar")),
    entry("snacking-night", (("snacking", "snack", "snacks", "eat at night", "eating at night",
                              "after dinner", "snacking late at night",
                              "eat late at night", "eating late at night",
                              "hungry late at night", "hungry at midnight",
                              "snack at midnight", "crisps at midnight",
                              "eat at midnight", "eating at midnight",
                              "snacking at midnight", "hungry at midnight",
                              # "late at night" was a key on its own, and it is a time, not a
                              # food: "my ex keeps texting me late at night" and "he rings me
                              # late at night" both got the evening-snacking answer. The
                              # eating has to be in the line, as it does for "in the evening".
                              # So has "midnight": "i cant get to sleep before midnight" and
                              # "i keep scrolling til midnight" were both getting this answer.
                              # bare "in the evening" was a snacking key, so every evening question
                              # about something else - "how do i switch off from work in the
                              # evening", "how do i fall asleep in the evening" - came here. The
                              # phrase now needs eating in it.
                              "in the evening snack", "snacking in the evening",
                              "snack in the evening", "eat in the evening",
                              "eating in the evening", "evening snacking",
                              "eat too much in the evening", "eat so much in the evening",
                              "sweets in the evening", "crisps in the evening",
                              "biscuits in the evening", "hungry in the evening"),
                             ("stop", "how do i", "why", "keep", "cant", "can't", "help", "avoid")),
          "Evening snacking is usually habit plus a lunch that was too small, not greed. Eat a "
          "proper lunch with protein and fibre in it, have your evening meal a bit later, then "
          "brush your teeth straight after it and leave the kitchen - it is far easier to change "
          "the routine than to resist the cupboard.",
          # A person being sick after dinner is not snacking: "my mum keeps being sick after
          # dinner" was answered with the evening-snacking advice, because "after dinner" is a key.
          avoid=("being sick", "feel sick", "feels sick", "feeling sick", "sick after",
                 "throws up", "throwing up", "threw up", "throw up", "vomit", "vomits",
                 "vomiting", "nausea", "nauseous", "diarrhoea", "diarrhea", "unwell",
                 "stomach bug", "food poisoning", "indigestion"),
          bias=1),
    entry("eat-more-veg", (("vegetables", "veg", "greens", "salad", "fruit and veg"),
                           ("more", "eat", "how do i", "get", "fussy", "hate", "kids", "five a day",
                            "portions", "refuses", "refuse", "wont eat", "picky",
                            # "she wont touch vegetables" is the same refusal as "she wont eat
                            # them", and it was answered with a shrug: the word for the refusal
                            # has to be on the key as well as on the ask below.
                            "wont touch", "won't touch", "wont try", "won't try", "wont eat any",
                            "turns his nose", "turns her nose", "turns their nose",
                            "hates veg", "hates greens", "hates vegetables",
                            "doesnt like veg", "doesn't like veg", "off his food",
                            "off her food", "faddy", "picky eater")),
          _veg_reply,
          # a dressing, a salad to go with dinner, washing a bag of it, keeping it fresh, and the
          # veg that goes unused in the fridge are all other questions
          avoid=("dressing", "vinaigrette", "mayonnaise", "wash", "recipe", "with dinner",
                 "side salad", "what goes with", "slimy", "limp", "wilted", "wilting", "last",
                 "keep a bag", "goes off", "gone off", "fridge", "freezer", "store", "throwing",
                 "throw away", "waste", "binned", "bin", "unused", "left over", "leftover",
                 "doesnt get used", "goes to waste",
                 # "green" is the loose form of the "greens" in this key, so every lawn and
                 # grass question arrived here: "how do i get my lawn green again" got the
                 # five-a-day answer instead of garden's lawn row.
                 "lawn", "lawns", "grass", "mow", "mowing", "mowed", "turf",
                 "greener", "green again", "brown patches",
                 # A line that asks for a meal and mentions the refusal on the way past is a meal
                 # question: "whats a quick dinner for two kids who wont eat anything green" was
                 # answered by the kids' dinner row until the refusal words above tipped the
                 # contest to this one. The meal rows keep those.
                 "for dinner", "for tea", "for supper", "for lunch", "for tea tonight",
                 "quick dinner", "quick tea", "dinner idea", "dinner ideas",
                 # a child named only as "one of them" is a household at a table, and the
                 # picky-eater row is the one built for that line ("one of them wont touch
                 # greens"); this entry speaks about one person the line has named.
                 "one of them", "one of the kids", "one of my kids", "one of the children",
                 "one of ours", "one of mine", "tea idea",
                 "tea ideas", "meal idea", "meal ideas", "what can i cook", "what should i cook",
                 "what should i make", "meal plan") + _DISLIKE,
          # and the line has to be about eating more of it, not about the veg in the drawer
          ask=("more", "fussy", "hate", "kids", "kid", "children", "five a day", "portions",
               "wont eat", "sparingly", "eet", "vegtables", "how do i get",
               # a refusal said in the third person is the same question as "wont eat": "he
               # refuses to eat greens" and "she wont touch vegetables" were answered with a
               # shrug because neither word was on this gate, though both are on the key above
               "refuse", "refuses", "refused", "refusing", "wont touch", "won't touch",
               "wont try", "won't try", "turns his nose", "turns her nose", "turns their nose",
               # "hate" already takes the forms of the word, so "hates veg" / "hates greens"
               # need not be spelled out here - and they must not be: a phrase built from words
               # the line already has stood this whole entry aside, and "she hates anything
               # green" went back to a nod.
               "turns up his nose", "turns up her nose", "doesnt like veg",
               "doesn't like veg", "off his food",
               "off her food", "picky eater", "faddy",
               # how little of it they eat, said as a shortfall rather than as "more"
               "enough", "barely", "hardly", "not eating", "dont eat", "don't eat",
               "should eat", "ought to eat", "need to eat"),
          # "how do i get my kids to eat veg" is this entry's own question, not a child portion one
          keep=("my kids", "my kid", "children", "child", "kids", "toddler", "my son",
                "my daughter", "my child",
                # how little of it they eat is a shortfall with an answer, not a diet to
                # remember: "i dont eat enough veg" was filed as a diet and said back as
                # "You don't eat enough veg, good to know". The plain dislike ("i dont eat
                # vegetables") stays a statement, which is what the avoid below is for.
                "dont eat", "don't eat", "do not eat")),
    # "how do i eat better" is the same question as "what does a balanced meal look like", and it
    # had no answer at all: the line was filed as a plan ("Then start with the smallest version of
    # it"), which is no help to somebody asking what to change on their plate.
    entry("balanced-meal", (("balanced meal", "balanced diet", "healthy diet", "eat healthily",
                             "healthy eating", "eat better", "eat healthier", "eating better",
                             "eating healthier", "eat more healthily", "improve my diet",
                             "eat properly", "eat well", "clean up my diet", "better diet"),
                            ("what", "how", "should i", "look like", "is", "start", "way",
                             "tips", "advice", "help",
                             # the same wish said as a statement rather than a question:
                             # "im trying to eat better" was answered "I'm listening", because
                             # the phrase was in the line but nothing else in the key was.
                             "trying", "trying to", "trying out", "want", "want to", "wanted to",
                             "need to", "trying hard", "attempting")),
          "Half the plate vegetables or salad, a quarter protein (fish, chicken, beans, eggs), a "
          "quarter starchy carbohydrate, plus a thumb of fat and fruit for pudding. If most meals "
          "look roughly like that and you drink water rather than fizzy drinks, you do not need to "
          "count anything.",
          # somebody who hates cooking is not helped by a plate to assemble from scratch, and the
          # line says so itself
          avoid=("hate cooking", "hate to cook", "dont cook", "don't cook", "cant cook",
                 "can't cook", "no cooking", "without cooking", "dont like cooking",
                 "don't like cooking", "no time to cook", "hate the kitchen", "cant be bothered"),
          bias=1),
    # "i want to eat better but i hate cooking" is a real ask with a real answer: the plate, built
    # from things that need no cooking at all.
    entry("eat-better-no-cooking",
          (_EAT_BETTER, ("hate cooking", "hate to cook", "dont cook", "don't cook", "cant cook",
                         "can't cook", "no cooking", "without cooking", "dont like cooking",
                         "don't like cooking", "no time to cook", "no time", "cant be bothered",
                         "hate the kitchen", "cant use an oven", "only a kettle")),
          "You can eat well without cooking if you build the plate from the shop: a bag of salad "
          "or a punnet of tomatoes, ready-cooked chicken or a tin of tuna or chickpeas, and bread, "
          "couscous or a microwave pouch of rice. Frozen veg straight from the microwave is the "
          "cheapest half-plate of vegetables there is, and a pot of yogurt with fruit is pudding. "
          "The only rule that matters is the half plate of vegetables, and that needs no hob.",
          # the cooking itself is another entry's question, and so is a diet to remember
          avoid=("recipe", "recipes", "how long", "oven", "roast", "bake", "baking", "fry",
                 "boil", "what can i cook", "what can i make"),
          bias=2),
    # --- the specific worries ----------------------------------------------
    entry("carbs-are-bad", (("carbs", "carbohydrate", "carbohydrates", "bread", "pasta", "rice",
                             "potatoes"), ("bad", "fattening", "good for you", "unhealthy",
                                          "should i avoid", "should i cut", "give up", "cut out")),
          "Carbohydrate is not fattening in itself - it has 4 calories a gram, the same as protein "
          "and less than half of fat's 9 - and wholegrain versions carry the fibre that keeps you "
          "full. What adds up is the fat and sugar that arrives with it (chips, garlic bread, "
          "cream sauces), and the portions. Wholegrain carbs are worth keeping."),
    entry("pasta-fattening", (("pasta", "spaghetti", "noodles"), ("fattening", "bad for you",
                                                                "make you fat", "healthy",
                                                                "lose weight", "diet")),
          "Pasta on its own is about 130 calories per 100g cooked and no more fattening than rice or "
          "bread: it is the portion (75 to 100g dry) and what goes on it - cream, cheese, oil - that "
          "adds up. Wholewheat pasta has more fibre, and cooling and reheating it makes some of the "
          "starch harder to digest, which blunts the blood sugar rise a little.",
          bias=1),
    entry("rice-or-pasta", (("rice", "pasta", "noodles", "bread", "potatoes", "potato"),
                             ("worse", "better", "slimming", "fattening", "healthier", "or rice",
                              "or pasta", "instead of", "rather than", "which is")),
          "Rice, pasta and boiled potatoes are much the same for you: about 130 to 150 calories "
          "per 100g cooked, so the portion is what matters - 75 to 100g dry of rice or pasta, or "
          "a potato the size of your fist. Pick whichever you will actually eat and fill half the "
          "plate with vegetables; the wholemeal versions are a small upgrade, not a different food.",
          # a portion, a cooking time or a recipe is another module's question, and the brown
          # against white comparison is brown-rice, which gives the fibre figures
          avoid=("how much", "how many", "how long", "cook", "boil", "recipe", "for six",
                 "for four", "for two", "per person", "leftover", "freeze", "reheat",
                 "brown rice", "white rice", "wholegrain", "wholewheat", "wholemeal",
                 "brown pasta",
                 # this row is which carb is better, so a fat swapped for another fat is not its
                 # line: "can i use butter instead of oil in bread" was answered with the calorie
                 # comparison of rice, pasta and potatoes because "bread" and "instead of" are
                 # both here.
                 "instead of butter", "instead of oil", "instead of margarine",
                 "instead of lard", "instead of suet",
                 # a flour has a swap of its own and this row has no business in it:
                 # "what can i use instead of bread flour" was answered with the calories in
                 # rice, pasta and potatoes, because "bread" is a carb word here and "instead of"
                 # is this row's ask.
                 "flour", "flours"),
          # "are potatoes fattening" is a food question, not a nutrient one: carbs-are-bad also
          # scores on it, and the potato answer names the food the line names.
          bias=1,
          # this row is which carbohydrate is the better buy for you, and "is it better to keep
          # bread in the fridge" is a keeping question that shares the words "bread" and "better".
          # The keeping rows answer it; a which-is-better line names no keeping word.
          guard=_not_a_keeping_question),
    entry("brown-rice", (("brown rice", "white rice", "wholegrain rice", "brown pasta",
                          "wholewheat pasta", "wholemeal pasta", "brown or white rice",
                          "white or brown rice", "brown or white pasta",
                          # "should i eat brown or white rice" named the grain only through
                          # the choice between them, and the rice-cooking row took it.
                          "brown or white", "white or brown", "wholemeal or white",
                          "white or wholemeal",
                          # the grain named without its partner: "should i eat brown or white
                          # rice" arrives as single words, so the choice is one of them
                          "brown", "white"),
                         ("better", "healthier", "which", "than", "difference", "instead",
                          "worth", "or white", "or brown", "around",
                          # how the swap is asked with no comparison word in it at all:
                          # "should i eat brown or white rice" is the same question.
                          "should", "eat", "swap", "switch")),
          _wholegrain, bias=1,
          # brown bread, brown sugar, brown sauce and a brown onion are other rows: this one is
          # the grain, and it names the one the line names.
          avoid=("bread", "flour", "sugar", "sauce", "onion", "stock", "meat", "mince",
                 "pudding", "rice pudding", "tea", "coffee", "wine", "basmati", "risotto",
                 "how long", "how much water", "cook", "boil",
                 # "should i wash whites at 60" is a load of washing, not a grain: the bare
                 # colour key took the line and answered with the fibre in brown rice, where
                 # the clothing row's answer about washing white cotton is the one asked for.
                 # A wash is asked with a machine, a detergent or a temperature, and a line with
                 # one of those and no food in it is never a question about the grain.
                 "wash", "laundry", "detergent", "bleach", "washing machine",
                 "tumble dryer", "degrees")),
    # "is frozen veg healthy" was the five-a-day card, "are frozen vegetables less nutritious"
    # was the blanching instructions and "is tinned food as good as fresh" was a ten-minute
    # dinner: the comparison is what was asked, and nothing answered it.
    entry("frozen-and-tinned",
          (("frozen", "freezer", "tinned", "tin", "canned", "can of", "from a tin",
            "frozen peas", "frozen veg", "frozen vegetables", "frozen fruit", "frozen fish",
            "tinned tomatoes", "tinned beans", "tinned fruit", "canned tomatoes"),
           ("as good as", "as healthy", "as nutritious", "less nutritious", "more nutritious",
            "better than", "worse than", "healthy", "healthy as", "nutritious", "as fresh",
            "than fresh", "just as good", "vitamins", "fresh or frozen", "frozen or fresh",
            "tinned or fresh", "fresh or tinned", "worth it", "good for you",
            # the money and the smoothie are the same question in another shape: "is frozen veg
            # cheaper" went to the blanching card and "is frozen fruit good in a smoothie" to a
            # punt, so both are asked of this row and answered by what the line wants (below).
            "cheaper", "cheapest", "cost", "costs", "price", "budget", "smoothie", "smoothies")),
          _frozen_and_tinned_reply,
          bias=2,
          avoid=("how many", "how much", "portion", "portions", "recipe", "cook", "boil",
                 "blanch", "defrost", "thaw", "reheat", "freezer broke", "freezer is", "freezer not",
                 "power cut", "fridge broke", "still frozen", "left out", "went off", "off food",
                 "refreeze", "how long", "keeps", "lasting", "covering", "wedding", "cake",
                 # a named fish has its own nutrition answer, and the oily-fish row is the one
                 # that gives the two portions a week: "is tinned tuna healthy" was this row.
                 # "is tinned fish healthy" names no fish, so the bare forms stand down for the
                 # same two-portions answer instead of this row's vegetable card.
                 "tuna", "salmon", "sardines", "sardine", "mackerel", "oily fish", "omega",
                 "fish healthy", "fish good for", "fish in a tin", "tinned fish", "canned fish",
                 "protein", "calories",
                 # a ready-made food in the freezer is not a vegetable: "is frozen pizza healthy"
                 # was told frozen peas were the best buy, which is a confident wrong answer.
                 "pizza", "pizzas", "chips", "oven chips", "ready meal", "ready meals", "nugget",
                 "nuggets", "fish fingers", "fish finger", "ice cream", "pastry", "pie", "pies",
                 "burger", "burgers", "takeaway", "takeaways", "sausage roll", "sausage rolls",
                 "soup")),
    entry("eggs-cholesterol", (("egg", "eggs"), ("cholesterol", "bad for", "heart", "how many",
                                                 "safe", "good for", "can i eat", "should i eat",
                                                 "can i have", "every day", "everyday", "daily")),
          "Eggs are back on the everyday list: the cholesterol in food turned out to matter far less "
          "than the saturated fat in your diet, so most people can eat them daily. If you have "
          "familial high cholesterol or heart disease, ask your GP - otherwise one or two a day is "
          "fine, and they are one of the cheapest good sources of protein.",
          # a bare "how many eggs is that" is about the recipe just given, not about a daily limit
          ask=("cholesterol", "heart", "bad for", "safe", "good for", "healthy", "can i eat",
               "should i", "a day", "a week", "daily",
               # "how often may I eat this" is the same verdict as "how many a day": "can i eat
               # eggs every day" was the egg-free swap and "is it ok to eat eggs every day" the
               # three weeks in the box, because neither word was in this row's ask.
               "ok to eat", "okay to eat", "fine to eat", "every day", "everyday", "each day",
               "how often", "too many"),
          # A cracked shell is a food-safety question, not a cholesterol one. "safe" is in this
          # key, so "is it safe to use a cracked egg" was answered with the daily-limit reply and
          # the cracked-egg entry (which says what to do with the egg) never got it.
          # "how many" and "should i" are how the daily limit is asked, and they are also how a
          # cooking time is asked: "how many minutes should i boil eggs" was answered with the
          # two-a-day advice. A time is asked of the pot, so a line with a time in it is not this.
          # "how many eggs" is the allowance here, not a count in a dish or in the box
          guard=not_a_count_for_the_box_or_the_dish,
          avoid=("crack", "cracked", "cracks", "shell", "shells", "fridge",
                 # a raw egg is the food-safety answer's question, not the daily limit's
                 "raw egg", "raw eggs", "raw",
                 "how many minutes", "how many mins", "how long", "minutes", "minute",
                 "timer",
                 # "is raw egg safe" and "are runny eggs ok in pregnancy" are the raw-egg rows,
                 # which say what to do with the egg rather than how many are allowed.
                 "raw", "runny", "undercooked", "pregnant", "pregnancy", "lion",
                 # "is it ok to eat eggs past the date" is the shelf life, and "ok to eat" is in
                 # this key now, so a date in the line is the box's question, not the daily limit.
                 "past the date", "past its date", "past their date", "past the date on",
                 "out of date", "gone off", "use by", "best before", "float", "floats"),
          bias=1),
    entry("red-meat", (("red meat", "beef", "lamb", "pork", "bacon", "sausages", "processed meat",
                        "ham", "steak",
                        # mince is the red meat most people cook and the one they ask about:
                        # "is mince healthy" and "is mince good for you" were the search shrug.
                        "mince", "minced beef"),
                       ("bad", "healthy", "unhealthy", "cancer", "how much", "how often",
                        "should i", "safe", "good")),
          "The UK advice is no more than 70g of red meat a day, and to go easy on processed meat "
          "(bacon, ham, sausages) because the cancer link is strongest there. Lean red meat is a "
          "good source of iron and zinc, so it is a question of amount and frequency rather than "
          "giving it up: two or three meat meals a week and fish or beans the rest.",
          # "how much protein in a sausage" is a portion question, not a cancer-risk one, and the
          # nutrient table has the figure: the red meat is the subject of the line, not its ask.
          # "how much" is in this key, and with the avoid below a policy line still keeps it.
          avoid=("protein in", "grams of protein", "grammes of protein", "how much protein",
                 "carbs in", "how many carbs", "how much fat", "fat in", "how much sugar",
                 "sugar in", "fibre in", "how much fibre",
                 # "should i" is in the key, and it is also how the most ordinary plating
                 # question is asked: "what should i serve with roast lamb" was answered with the
                 # 70g a day, because the joint and "should i" were both in the line. What goes
                 # beside a joint is the sides' answer, so a line that says serve or side is not
                 # this one. The red-meat questions themselves say none of these words.
                 "serve", "serving", "served", "go with", "goes with", "going with", "side",
                 "sides", "side dish", "what to have with", "have with it",
                 # "safe" is in the key above, and so "is pink pork safe" was answered with the
                 # 70g a day when the person was asking whether the meat was cooked. Pink, raw
                 # and undercooked are the cooking question, which cooking_entries answers.
                 "pink", "raw", "undercooked", "bloody", "still ok", "ok to eat",
                 "safe to eat",
                 # how to flavour the joint is not how much of it to eat: "what should i season
                 # steak with" was the 70g-a-day answer, and the seasoning table has the salt,
                 # pepper and horseradish it asked for.
                 "season", "seasoning", "seasoned", "spice", "spices", "spiced", "herb",
                 "herbs", "rub", "rubbed", "marinade", "marinate", "flavour", "flavor",
                 # how hot, how long and how it is done is not an avoid phrase but the guard
                 # above: `_not_a_cooking_question` reads the whole line with the cooking verbs
                 # the rest of the knowledge base uses, so "what temperature should i cook pork
                 # at", "what gas mark for roast beef" and "how long do i cook a joint for" all
                 # stand this row down without a list of wordings to keep up.
                 # what to make with the meat on the shelf is the recipe row's question, and
                 # "what should i make for tea, i've got mince in" was answered with the 70g a
                 # day once mince joined the subject above. "what's a good swap for mince in a
                 # bolognese" is the same: the person is cooking, not auditing their diet.
                 "what should i make", "what can i make", "what should i cook", "what can i cook",
                 "make for tea", "make for dinner", "make for lunch", "make with", "meal with",
                 "dinner with", "tea with", "recipe", "swap for", "swaps for", "swapped",
                 "substitute", "instead of mince", "i've got", "i have got", "ive got",
                 # a mince pie is fruit and suet in pastry, not the red meat on the plate, and
                 # "is a mince pie healthy" was answered with the 70g a day.
                 "mince pie", "mince pies", "mincemeat",
                 # what it costs is the shopping question, not this one: "how much is mince a
                 # kilo" was answered with the 70g a day because the meat and "how much" were
                 # both in the line. "how much is too much red meat" says none of these words.
                 "a kilo", "per kilo", "per kg", "price", "prices", "priced", "cost", "costs",
                 "cheaper", "cheapest",
                 # how much of it to buy or cook for the people at the table is the portion row's
                 # question: "how much mince do i need", mid-chilli for eight, was answered with
                 # the 70g a day once mince joined the subject above. A policy line never asks
                 # what you need or what you weigh it out in.
                 "do i need", "will i need", "should i buy", "shall i buy", "need to buy",
                 "per person", "per head", "grams", "grammes", "kg", "kilos",
                 "how much mince", "how much beef", "how much lamb", "how much pork"),
          guard=not_a_cooking_question),
    entry("fruit-sugar", (("fruit", "fructose", "grapes", "mango"), ("too much", "sugar",
                                                                   "fattening", "bad",
                                                                   "how much fruit")),
          "Whole fruit is not the same as added sugar: the fibre and water slow it down and one "
          "piece is about 60 calories. The only people who need to limit it are those told to by a "
          "doctor, and even then it is juice and dried fruit that matter most. Two or three pieces "
          "a day is a normal amount."),
    entry("fried-food", (("fried", "frying", "chips", "takeaway", "takeaways", "kebab",
                          "fried chicken"), ("healthy", "bad", "how often", "unhealthy",
                                             "ok to eat", "safe")),
          "Frying adds about 50 to 100 calories per portion of oil soaked in, and oven chips have "
          "roughly a third of the fat of fried ones. Frying at the right temperature helps: if the "
          "oil is hot enough the food steams from inside and takes on less. Once or twice a week is "
          "not the problem; it is the rest of the plate that matters."),
    # Reading the back of a packet is one of the most common everyday questions there is, and
    # nothing answered it: "how do i read a nutrition label" was sent to the laundry symbols.
    entry("food-label",
          (("nutrition label", "nutrition labels", "food label", "food labels", "nutrition",
            "nutritional information", "traffic light", "traffic lights", "ingredients",
            "ingredients list", "packet", "packaging", "back of the packet", "label"),
           ("read", "reading", "understand", "mean", "means", "high", "low", "check",
            "how do i read", "what does", "explain", "compare", "per 100g", "per 100 g",
            "serving", "servings", "portion")),
          "Work in per 100g, not per serving, because serving sizes are chosen to look small. On "
          "that column, high is more than 17.5g of fat, 5g of saturates, 22.5g of sugar or 1.5g of "
          "salt; low is 3g of fat, 1.5g of saturates, 5g of sugar or 0.3g of salt. Traffic-light "
          "labels colour the same numbers for you. Check the ingredients list too: whatever is "
          "listed first is what there is most of, and sugar has many names - syrup, concentrate, "
          "juice, maltodextrin - so a label can be sugar-heavy without the word appearing near the "
          "top.",
          # a care label, a price tag and a parcel are other answers
          avoid=("clothes", "shirt", "jumper", "trousers", "garment", "washing", "wash", "iron",
                 "ironing", "care label", "parcel", "address", "price", "jar", "tin", "can",
                 "freezer", "wine", "beer")),
    entry("salt-too-much", (("salt", "salty", "sodium"), ("too much", "how much", "limit",
                                                        "healthy", "reduce", "cut", "how many",
                                                        "a day", "teaspoons",
                                                        # "is salt bad for you" was a shrug while
                                                        # this row held the 6g figure: the
                                                        # verdict shape was not in its key.
                                                        "bad for you", "bad for me", "good for you",
                                                        "unhealthy", "is it bad", "is salt bad",
                                                        # a goal clause names the direction, and
                                                        # "i'm trying to eat less salt" is the same
                                                        # question as "how do i cut down on salt"
                                                        "less", "lower", "cut down", "cut back",
                                                        # "she cant eat much salt" is the same
                                                        # question said as a rule somebody has
                                                        # been given, and it had no answer at all
                                                        # once the baby table stopped taking it
                                                        "cant eat much", "cant have much",
                                                        "cannot eat much", "not much",
                                                        "shouldnt eat", "should not eat",
                                                        "shouldnt have", "has to eat less",
                                                        "watch the salt", "no salt", "avoid")),
          "The limit for an adult is 6g of salt a day, about a level teaspoon, and most people eat "
          "8g without ever adding any: bread, cheese, bacon, sauces and ready meals are where it "
          "hides. Check the label - 1.5g of salt per 100g is high, 0.3g is low - and taste before "
          "you add more at the table."),
    entry("fibre", (("fibre", "fiber", "roughage"), ("how much", "a day", "need", "get more",
                                                    "constipated", "healthy",
                                                    # the shortfall wording, now that it is no
                                                    # longer filed as a diet with "even enough"
                                                    # in it: "i dont eat enough fibre" was left
                                                    # with no answer at all.
                                                    "enough", "barely", "hardly", "get",
                                                    "should eat", "dont eat", "don't eat",
                                                    # "what should i eat for more fibre" and "im
                                                    # trying to eat more fibre" are the same
                                                    # question as "how much fibre do i need", and
                                                    # both were going to the search hedge
                                                    "eat", "eating", "food", "foods", "more",
                                                    "increase", "best", "good sources",
                                                    "sources", "what", "diet", "in my diet",
                                                    "good", "good for you", "benefits", "help")),
          "Aim for 30g of fibre a day, and most people get half that. The easy sources are beans "
          "and lentils (7 to 8g a tin), wholegrain bread and pasta, porridge oats, and fruit with "
          "the skin on. Increase it slowly and drink more water, or you will feel bloated for a "
          "week.",
          # "i dont eat enough fibre" is a shortfall, not a diet to remember, and the statement
          # guard would otherwise pass it to nobody
          keep=("dont eat", "don't eat", "do not eat")),
    # The mirror of the fibre row: "how do i eat more protein" had no answer at all, and the
    # gym rows are about building muscle, not about where the protein comes from.
    entry("more-protein", (("protein", "proteins"), ("more", "enough", "get",
                                                     "increase", "sources", "best", "good",
                                                     "what", "eat", "eating", "food", "foods",
                                                     "need", "should eat", "dont eat",
                                                     "don't eat", "in my diet", "add")),
          "Aim for a palm-sized portion of protein at each meal - eggs, milk or yoghurt at "
          "breakfast, beans, lentils or chicken at lunch, fish or mince at dinner - which lands "
          "most adults near the 0.75g per kilo of body weight they need. Greek yoghurt, cottage "
          "cheese, tinned fish, eggs, tofu and lentils are the cheapest ways to add it.",
          # "how much" is fenced out rather than merely left out of the key: a line that asks for
          # a figure is the sport row's (grams a day, 1.6g a kilo if you lift), and this row is
          # about where the protein comes from. Both rows answering side by side left "how much
          # protein do i need" on the vaguer one.
          avoid=("shake", "powder", "whey", "creatine", "supplement", "supplements", "steroid",
                 "bulk", "bulking", "bodybuilder", "how much protein in", "in an egg", "in chicken",
                 "how much")),
    # "how do i get more iron in my diet" was the weight-loss answer, "what foods are high in
    # iron" and "how do i get more calcium" were shrugs, and "how do i get more vitamin d" was
    # the answer about taking a multivitamin with food. The sources of a nutrient are a table
    # lookup, so one row reads MORE_OF and every way of asking the same nutrient lands on it.
    entry("more-of-a-nutrient",
          (tuple(word for words, _text in MORE_OF for word in words), _MORE_OF_ASK),
          _more_of,
          # how much to have is nutrient-a-day's question, and a supplement brand or a high dose
          # is not a food question at all. "what is in one named food" is not handled here:
          # "is in" as an avoid word also took "what foods are HIGH IN iron" (the matcher reads
          # the phrase loosely, and "in" alone was enough), so the food table's lines are turned
          # down inside _more_of, where the food can actually be named.
          avoid=("how much", "how many", "a day", "per day", "daily", "mg", "micrograms",
                 "supplement", "supplements", "tablet",
                 "tablets", "dose", "dosage", "overdose", "too much", "blood test",
                 # the ironing homograph: the metal, the appliance and the creases
                 # "ironing" and "ironed" are NOT in this list: the matcher reads "iron" as a
                 # loose form of them, so listing them turned every iron question down before
                 # the row could score. The creases and the appliance are named instead.
                 "shirt", "shirts", "crease", "creases", "steam",
                 "clothes", "trousers", "board", "rust", "pan", "pans", "soleplate"),
          bias=1),
    # "i think i am low in iron" was answered with "a walk and someone to talk to": a worry about
    # a nutrient is a health question, and the answer is a blood test before a supplement.
    entry("low-iron",
          (("low in iron", "iron low", "iron levels", "iron level", "iron deficiency",
            "deficient in iron", "anaemic", "anaemia", "anemia", "anemic", "need iron",
            "lack of iron", "iron tablets", "iron supplement"),
           ("worth", "should i", "think", "wonder", "worried", "always tired", "tired all",
            "pale", "breathless", "my", "i", "am", "need", "take", "start", "check",
            "test", "blood", "doctor", "gp", "levels")),
          _low_iron,
          # a line about ironing, about the metal or about iron in a named food is not this row
          avoid=("shirt", "shirts", "crease", "creases", "steam", "clothes",
                 "trousers", "board", "rust", "pan", "pans", "soleplate", "iron in", "in spinach",
                 "in cereal", "in food", "in beef", "in liver", "in lentils", "supplement dose",
                 # what an iron tablet is best taken with, and taken away from, is the mixing
                 # question, not "my iron might be low": "can i take iron tablets with tea" and
                 # "can i take antacids with my iron tablets" were both answered with a blood test
                 "with tea", "with coffee", "with milk", "with food", "with water",
                 "with orange juice", "with breakfast", "take with", "take it with",
                 "antacid", "antacids", "gaviscon", "rennie", "omeprazole", "lansoprazole"),
          bias=1),
    entry("vitamins", (("vitamins", "supplements", "multivitamin", "vitamin"), ("should i take",
                                                                               "need", "worth",
                                                                               "any point",
                                                                               "take")),
          "For most people with a varied diet the only supplement worth taking is vitamin D in autumn "
          "and winter (10 micrograms a day), plus folic acid if you are pregnant or trying. A "
          "multivitamin mostly makes expensive urine; if you eat little fish, vegans should add B12."),
    # "how much calcium do i need a day" was a shrug, "how much iron do i need a day" was the
    # ironing answer and "how much calcium does a teenager need" was the sleep chart: one table of
    # daily figures, one row, and the age in the line picks the adult or the teenager reply.
    entry("nutrient-a-day",
          (("calcium", "iron", "protein", "magnesium", "potassium", "zinc", "folic acid",
            "folate", "vitamin d", "vitamin c", "vitamin b12", "b12"),
           ("how much", "how many", "a day", "per day", "daily", "need", "needed", "should i take",
            "should i have", "should i be", "recommended", "mg", "micrograms", "enough",
            "do i need", "much of")),
          _a_day,
          # how much of a nutrient is in a named food is the food table's question, and it is
          # answered better there ("a glass of milk has about 240mg")
          avoid=("is in", "are in", "there in", "a test", "blood test", "test cost", "cost",
                 "costs", "price", "cheapest", "how much calcium in", "how much iron in",
                 "how much protein in", "how much vitamin d in", "how much vitamin c in",
                 "how much vitamin b12 in", "how much b12 in", "how much magnesium in",
                 "how much potassium in", "how much zinc in", "how much folate in",
                 "supplement", "supplements", "multivitamin",
                 # the ironing homograph: the metal, the appliance and the creases. "ironing" and
                 # "ironed" are not in this list on purpose: the matcher reads "iron" as a loose
                 # form of them, so listing them turned every real iron question down here before
                 # the row could score.
                 "shirt", "shirts", "crease", "creases", "creased", "steam", "steamer",
                 "clothes", "trousers", "linen", "fabric", "board", "rust", "pan", "pans",
                 "soleplate", "water tank", "limescale",
                 "supplement dose", "deficiency", "deficient", "anaemic", "anaemia", "low iron",
                 # the water, the salt and the sugar limits have their own rows
                 "salt", "sodium", "sugar", "water", "calories", "calorie"),
          bias=2),
    # The verdict on a nutrient, which had no owner at all: see NUTRIENT_ROLE. It sits beside
    # nutrient-a-day and more-of-a-nutrient, and the three are one table each so the same nutrient
    # cannot be described two different ways.
    entry("nutrient-role",
          (tuple(word for words, _text in NUTRIENT_ROLE for word in words), _ROLE_ASK),
          _nutrient_role,
          # the figure, the sources and the food it is in are the other three rows' questions, and
          # a person who is pregnant, feeding a baby or asking for a child is the guard's
          avoid=("how much", "how many", "a day", "per day", "daily", "mg", "micrograms",
                 "supplement", "supplements", "multivitamin", "tablet", "tablets", "dose",
                 "dosage", "blood test", "deficiency", "deficient",
                 "foods", "high in", "rich in", "sources", "which foods", "what foods",
                 # the ironing homograph, exactly as nutrient-a-day fences it
                 "shirt", "shirts", "crease", "creases", "creased", "steam", "steamer",
                 "clothes", "trousers", "linen", "fabric", "board", "rust", "pan", "pans",
                 # "ironing" is NOT here: the matcher reads "iron" as one form of it, so listing
                 # it turned every iron question down before the row could score (the same trap
                 # nutrient-a-day records above)
                 "soleplate", "water tank", "limescale", "golf", "gym", "weights",
                 "heat", "hot", "cold", "plug", "fuse", "sparks", "spitting", "spray",
                 # the pregnancy and the child questions have their own answers
                 "pregnant", "pregnancy", "breastfeeding", "breast feeding", "trying for a baby",
                 "baby", "babies", "child", "children", "toddler", "kids"),
          bias=1),
    # a pregnancy is the one time the adult table is the wrong table, and the nutrition guard
    # (which keeps adult portions away from a baby, a child and a pregnant person) turned every
    # one of these lines into "thanks for telling me": "how much folic acid should i take in
    # pregnancy" was a shrug, "how much iron do i need when pregnant" was a baby-shopping list.
    entry("pregnancy-nutrients",
          # the key is the nutrient, never the word "vitamin" or "supplement" on its own: those
          # are the words the `vitamins` row is built from, and a word only one row uses counts
          # for more in the ranking. Listing them here took "do i need to take supplements" away
          # from that row and gave it the how-to-take-them answer instead.
          (_PREGNANT,
           ("folic", "folate", "iron", "calcium", "b12", "vitamin a", "vitamin d", "vit d",
            "liver")),
          _pregnancy_vitamins, bias=2,
          avoid=("cost", "costs", "price", "cheapest", "how much does", "is in", "are in",
                 "how much iron in", "how much folic acid in", "calories", "sugar", "salt"),
          # "should i take folic acid when trying for a baby" carries "baby", which the guard
          # otherwise reads as a child's portion question
          keep=_PREGNANT + ("baby", "babies")),
    entry("healthy-weight", (("how much should i weigh", "healthy weight", "ideal weight",
                               "my weight", "bmi", "overweight", "underweight", "obese",
                               # the ways people ask their own weight, which reached the "add
                               # weight to the bar" row instead: "what weight should i be",
                               # "what weight should i aim for", "whats my goal weight".
                               "what weight should i be", "what weight should i aim",
                               "what weight should i target", "what should i weigh",
                               "what should my weight be", "what weight is healthy",
                               "goal weight", "target weight", "how heavy should i be",
                               "what weight do i need to be"),
                              ("what", "should", "healthy", "is", "am i", "how", "check")),
          "Healthy weight is a range, not a number: a BMI of 18.5 to 24.9 for most adults, which for "
          "someone 1.70m tall is roughly 54kg to 72kg. BMI gets it wrong for very muscular people "
          "and for older people who have lost muscle, so add a waist measurement - under 94cm for a "
          "man and 80cm for a woman is the usual guide. If your weight has changed without trying, "
          "that is worth a word with a GP.",
          # a breed name is an animal, and "my labrador is overweight what do i do" is the dog's
          # question: the BMI card is for a person's own weight. "What should i weigh up" is the
          # decision and not the bathroom scale (deck row judged-04), and a line that names a
          # lift is asking about a bar, which how-heavy answers.
          # bias=1 because how-heavy scores a bare "what weight" line the same as this one.
          bias=1,
          avoid=pets.ANIMAL_NOUNS + ("weigh up", "weighing up", "weigh it up", "weigh them up",
                                     "weighing it up", "weigh the pros", "weigh the options",
                                     "lift", "lifting", "lifted", "bench", "squat", "squats",
                                     "deadlift", "dumbbell", "dumbbells", "barbell", "kettlebell",
                                     "reps", "sets",
                                     # "how do i work out my bmi" asks for the sum, and another
                                     # row does the sum: this one is the range it falls in
                                     "work out", "calculate", "calculation", "formula")),
    entry("count-calories", (("count calories", "counting calories", "count your calories",
                              "track calories", "tracking calories", "calorie counting",
                              "log my food", "food diary", "myfitnesspal"),
                             ("need", "should", "worth", "do i", "have to", "how", "any point",
                              "need to", "does", "did", "work", "works", "any good", "help",
                              "helpful", "necessary", "bother")),
          "You do not need to count calories to lose weight, and most people who do stop within a "
          "month. What works is changing a few things you can see: no liquid calories, half the "
          "plate vegetables, weighing out pasta and rice rather than eyeballing them. If you like "
          "numbers, a two-week food diary tells you where the calories actually are, which is more "
          "useful than tracking forever.",
          bias=2),
    entry("before-or-after-food", (("before or after", "before and after", "which is better",
                                    "eat first or"),
                                   # the food word has to be in the key: the session words alone
                                   # ("should i stretch before or after running") are a question
                                   # about stretching, and this answer landed on it.
                                   ("eat", "eating", "food", "meal", "carbs", "protein",
                                    "fuel")),
          "Both, for different reasons: something small and mostly carbohydrate one to two hours "
          "before gives you the energy for the session, and some protein within a couple of hours "
          "after helps the muscle repair. If you only do one, the after matters more for strength "
          "training and the before matters more for a long run.",
          ask=("eat", "eating", "food", "meal", "breakfast", "lunch", "dinner", "carbs",
               "carbohydrate", "protein", "fuel", "before or after", "before and after",
               "eat first or", "which is better"),
          avoid=("stretch", "stretching", "stretches", "warm up", "warmup", "cool down",
                 "mobility", "foam roll", "before bed", "in the morning",
                 # "should i take ibuprofen before or after food" is a tablet question; the
                 # medicine and the stomach are health.py's medicine-with-food
                 "ibuprofen", "paracetamol", "aspirin", "naproxen", "painkiller", "painkillers",
                 "tablet", "tablets", "medicine", "medicines", "medication", "antibiotic",
                 "antibiotics", "steroid", "steroids",
                 # a railway is not a session: "should i eat before or after my train" was told
                 # about "the energy for the session". A bare "train" is not here, because the
                 # exercise is "training" and the avoid list matches forms, not whole words.
                 "my train", "the train", "a train", "train home", "train journey", "flight",
                 "plane", "ferry"),
          # a dose is not a session, and this answer is only true of a session: see `not_a_dose`
          guard=not_a_dose,
          bias=2),
    entry("emotional-eating", (("eat when", "eating when", "comfort eating", "emotional eating",
                                "eat my feelings", "food when", "i eat too much", "cant stop "
                                "eating", "can't stop eating", "overeating"),
                               ("stressed", "sad", "bored", "upset", "lonely", "tired", "anxious",
                                "angry", "why", "stop", "help", "how", "when")),
          "Eating to manage a feeling is very ordinary, and the feeling does not go away because you "
          "tell yourself off for it. The practical version: eat proper meals so hunger is not part "
          "of it, keep the triggering food out of the house, and put a ten-minute walk or a phone "
          "call between the urge and the cupboard - the urge usually passes. If it happens most "
          "days and you feel out of control, that is worth talking to a GP about; Beat's helpline "
          "(0808 801 0677) is free and does not judge."),
    entry("food-guilt", (("guilty", "guilt", "ashamed", "hate myself", "bingeing", "binge",
                          "purge", "made myself sick", "overate",
                          # the whole feeling said as one phrase, so the row names what the line
                          # is about and not only the feeling: "how do i stop feeling guilty
                          # about food" was reaching the hard-conversation card and was told to
                          # ask for ten minutes at a calm time, which is a talk with a person
                          "guilty about food", "guilty about eating", "guilt about food",
                          "guilty after eating", "guilty for eating", "guilty about what i eat",
                          "food guilt", "guilty about my weight"),
                         ("eating", "ate", "food", "after", "help", "stop", "why", "how")),
          "One big meal does not undo anything - a day of overeating is a few hundred calories over, "
          "not a week's worth - so the useful move is to go back to a normal meal at the normal time "
          "rather than to skip or punish yourself. If you are bingeing regularly, or making yourself "
          "sick or using laxatives, please tell a GP: that is treatable, and Beat (0808 801 0677) "
          "will talk it through with you first.",
          # "how do i say no without feeling guilty" is a refusal question: the say-no answer
          # owns it, and "guilt" in the line is what makes saying no hard, not what is eaten.
          # A bare "how" stays in the key, because "how do i deal with guilt" is this entry.
          # The other refusal verbs stand the entry down too: with the feeling clause cut, the
          # remaining "how do i refuse" still scored here on "how", and answered a say-no ask
          # with the overeating card.
          avoid=("say no", "saying no", "refuse", "refusing", "turn down", "turning down",
                 "decline", "declining",
                 # "purge" is a plumber's word too: "how do i purge air from the boiler" and
                 # "how do i purge the heating system" were answered "One big meal does not undo
                 # anything", which is a weight card for a person with a cold radiator.
                 "radiator", "radiators", "boiler", "boilers", "pipe", "pipes", "piping",
                 "plumbing", "plumber", "heating", "central heating", "heat pump", "valve",
                 "valves", "thermostat", "sump", "engine", "coolant", "brake", "brakes",
                 "hydraulic", "airlock", "drain", "drains", "water system", "cooling system",
                 "immersion heater", "hot water", "underfloor", "flush", "flushing",
                 # the things people purge that are not a body
                 "email", "emails", "inbox", "mailbox", "file", "files", "data", "cache",
                 "computer", "laptop", "phone", "photo", "photos", "folder", "folders",
                 "hard drive", "facebook", "instagram", "twitter", "social media",
                 "loft", "garage", "cupboard", "wardrobe", "shed", "garden", "house",
                 "server", "spreadsheet", "contacts", "downloads", "windows")),
    entry("carbs-at-night", (("carbs", "carbohydrate", "pasta", "rice", "bread", "potatoes"),
                              ("at night", "in the evening", "before bed", "late", "night")),
          "Carbs in the evening do not turn into fat any faster than carbs at lunch: your body "
          "stores what it does not use whenever you eat it. A plate of pasta at nine is only a "
          "problem if it is on top of a full day of eating or sits so heavy it spoils your sleep. "
          "Try to leave two hours between dinner and bed."),
    entry("fasting", (("fasting", "fast", "16 8", "5 2", "intermittent"),
                      ("good for you", "healthy", "work", "worth", "should i", "safe",
                       "lose weight", "any good")),
          "Fasting works for weight loss because it makes eating less happen almost by accident, "
          "not because it does anything special: 16:8 and 5:2 come out level with ordinary calorie "
          "cutting in the trials. Pick it only if skipping breakfast suits you - if it leaves you "
          "raiding the cupboard at nine at night, it will not work. Not for anyone pregnant, "
          "underweight or with a history of eating disorders.",
          # "my battery is draining fast" is a phone question, and "fast" alone was reaching this
          avoid=("battery", "batteries", "phone", "laptop", "charger", "charging", "charge",
                 # "fast" is the word this entry keys, and it is also inside "how fast": "how
                 # fast should i run a 5k" is a pace question, not a fasting one, so the speed
                 # words are what the entry has to stand aside for. `quickly` and `rate` were
                 # tried here and taken out: "does fasting help you lose weight quickly" and
                 # "at what rate should i fast" are fasting lines, and neither reaches the key
                 # by way of a speed word.
                 "how fast", "how fast can", "how fast should", "how fast do", "how fast will",
                 "fastest", "mph", "speed", "pace")),
    entry("cheese-bad", (("cheese", "cheddar", "dairy"), ("bad for you", "healthy", "fattening",
                                                          "unhealthy", "good for you", "eat",
                                                          "how much")),
          "Cheese is calorie-dense - about 400 calories per 100g of cheddar - but a portion is only "
          "30g, roughly a matchbox, and it brings calcium and protein with the fat. It is not a food "
          "to avoid, it is a food to weigh: grated rather than sliced goes further.",
          # "can i eat cheese past its date" is a keeping question, and a calorie answer is the
          # wrong thing to hand someone asking whether their cheese is still good.
          avoid=("date", "dates", "out of date", "past its date", "keep", "keeps", "last",
                 "lasts", "gone off", "mouldy", "mould", "fridge", "freeze", "tomorrow")),
    entry("spices-are-fine", (("spice", "spices", "spicy", "herb", "herbs", "seasoning",
                              "pepper", "black pepper", "chilli", "chili", "cumin", "cinnamon",
                              "turmeric", "garlic", "ginger", "paprika", "curry powder",
                              "mixed herbs"),
                             ("bad for you", "bad for me", "good for you", "good for me",
                              "healthy", "unhealthy", "fattening", "ok", "okay", "safe",
                              "fine", "harm", "worth", "a day", "every day", "too much",
                              # "can i put cinnamon in my coffee" asks the same thing and has
                              # no health word in it at all
                              "put in", "put cinnamon", "in my coffee", "in coffee", "in my tea",
                              "in tea", "in cooking", "add to", "sprinkle",
                              # "can i put spices in a chilli for 4" is a cooking ask, not a
                              # health one: the verb and the dish both sit away from the spice
                              # word, so the phrase "put in" never matches.
                              "put", "add", "use", "go in", "goes in", "how much",
                              "in a chilli", "in a curry", "in a stew", "in a sauce",
                              "in a soup", "in soup", "in the chilli", "in the curry")),
          "Spices are not bad for you: they are the cheapest way to make plain food taste of "
          "something, which is why a boring diet gets eaten less. Turmeric, cinnamon, garlic, "
          "ginger and black pepper do no harm in the amounts that go in cooking, and the salt "
          "and the heat are what to watch - a hot dish is painful rather than harmful. Watch the "
          "blends and the ready-made sauces, because they carry the salt.",
          # the baby table owns "can my baby have spices", and its answer is about a baby's
          # first tastes rather than about a grown-up's cooking.
          avoid=("baby", "babies", "baby led", "weaning", "wean", "puree", "months old",
                 "month old", "toddler", "my son", "my daughter", "my child", "pregnant",
                 # "how many calories in a chilli con carne" was answered with "spices are not
                 # bad for you": the dish is in this row's key as an example, and a figure about
                 # the dish is the portion tables' question. The dishes that have a portion are
                 # named here rather than the figure words, so "does chilli have sugar in it" and
                 # "does cinnamon have calories" keep this answer.
                 "con carne", "tikka masala", "bolognese", "stir fry", "cottage pie",
                 "fish pie", "lentil soup", "chicken salad", "chicken sandwich")),
    entry("tomato-nutrition", (("tomato", "tomatoes", "cherry tomatoes", "plum tomatoes",
                                "tinned tomatoes", "tomato juice"),
                               ("healthy", "good for", "bad for", "fattening", "unhealthy",
                                "nutrition", "nutritious", "vitamins", "calories",
                                "how many calories", "worth eating", "count as")),
          "Tomatoes are one of the good everyday foods: about 18 calories per 100g, so a whole "
          "one is roughly 20, and they bring vitamin C, potassium and lycopene. Cooked with a "
          "little oil the lycopene is easier for the body to use, so tinned tomatoes and a "
          "home-made sauce count as well as fresh ones - the salt and sugar in a bought jar are "
          "what to watch, not the tomatoes.",
          # a tomato that is unripe, going off, being kept or being grown is a different question
          # with its own answer, and a calorie line is the wrong reply to every one of them
          avoid=("keep", "keeps", "last", "lasts", "fridge", "freezer", "freeze", "gone off",
                 "going off", "off", "mouldy", "mould", "ripe", "ripen", "unripe", "green",
                 "plant", "growing", "grow", "blight", "greenhouse", "chutney", "relish",
                 "sauce recipe", "growbag")),
    entry("sushi", (("sushi", "sashimi"), ("healthy", "good for you", "fattening", "calories",
                                           "is it")),
          "Sushi is a good everyday choice: fish, rice and vegetables, with very little fat, and a "
          "supermarket box is usually 300 to 500 calories. The traps are the fried fillings, the "
          "mayonnaise-heavy boxes and the soy sauce, which is salty enough to matter if you pour in "
          "the whole sachet."),
    entry("wholemeal-bread", (("brown bread", "wholemeal", "white bread", "granary bread",
                               "wholegrain bread", "seeded bread"),
                              ("better", "healthier", "which", "should i", "than", "difference",
                               "bad for", "good for", "worth")),
          "Wholemeal is the better everyday loaf: the same calories as white, but two to three "
          "times the fibre, and the fibre is what keeps you full and helps your gut. Brown bread "
          "is not the same thing - it is often white flour with colouring and a little bran added, "
          "so look for the word wholemeal or wholegrain on the label. It is worth the swap; it is not "
          "worth worrying about when there is only white in the house.",
          # rice and pasta have their own entries: the loaf answer never answers a rice line
          avoid=("rice", "pasta", "noodles", "potato", "potatoes"), bias=1),
    entry("butter-margarine", (("butter", "margarine", "spread", "lurpak"), ("better", "healthier",
                                                                           "or", "which",
                                                                           "should i use")),
          "Both are about 100 calories a tablespoon, so the difference is small. Butter is "
          "saturated fat; the olive- and rapeseed-oil spreads are the healthier swap if you use a "
          "lot of it, and the ones with added plant sterols do lower cholesterol a little. If you "
          "use a scraping on toast, use whichever you like more."),
    entry("porridge-vs-cereal",
          (("porridge", "oats", "oatmeal", "cereal", "cereals", "cornflakes", "muesli", "granola",
            "shreddies", "weetabix", "bran flakes", "crunchy nut"),
           ("better", "healthier", "worse", "or", "which", "than", "instead", "good for",
            "bad for", "sugar", "filling", "worth", "swap", "healthy",
            # the comparison said as one phrase is worth more than the two words it is made of:
            # "is porridge better than cereal" tied with the shelf-label card, which also keys
            # "better", and lost to it on rarity, so the question about two breakfasts was
            # answered with a lesson on price per kilo.
            "better than", "healthier than", "worse than", "instead of", "rather than",
            "or porridge", "porridge or", "cereal or", "or cereal",
            # "is porridge ok" is the same verdict as "is porridge good for you", said the way
            # most people say it, and it named no comparison at all: the cooking table's idea
            # for leftover porridge answered it ("Cold porridge sets solid, so loosen it ...").
            # These are the yes-or-no words of a verdict; the cooking and keeping questions that
            # also say "ok" are kept out below.
            "is it ok", "ok", "okay", "alright", "all right", "fine", "safe", "bad",
            "is porridge ok", "good or bad", "any good", "worth eating", "should i eat",
            # the comparison the other way round: "are cornflakes as good as porridge" was a
            # search suggestion, because "as good as" is not any of the words above.
            "as good as", "as healthy as", "as filling as", "just as good")),
          # the verdict names the bowl the person asked about: "is granola ok for you" was
          # answered with a paragraph that began "Porridge is the better everyday bowl", which is
          # advice about a breakfast they did not ask about
          _cereal_verdict,
          # cooking a bowl of porridge, and a flapjack or a loaf made with oats, are other answers
          avoid=("overnight", "recipe", "cook", "cooking", "how do i make", "bake", "baking",
                 # the verdict words above are common ones, so the questions that are not a
                 # verdict keep their own answers: cold porridge, reheating it, a baby, a price
                 "cold", "reheat", "reheating", "leftover", "left over", "fridge", "freezer",
                 "freeze", "keeps", "how long", "baby", "babies", "toddler", "weaning",
                 "my son", "my daughter", "cheaper", "price", "cost", "calories in",
                 "bread", "flapjack", "cookie", "cookies", "biscuit", "smoothie", "milk",
                 "gluten", "weaning",
                 # "whats cheaper oats or cereal" is a price question wearing the same comparison,
                 # and the new "better than" phrases would otherwise take it: the shelf-label
                 # card keeps every line that asks what something costs.
                 "cheaper", "price", "prices", "cost", "costs", "how much",
                 "per kilo", "per 100g", "on offer", "bargain", "value", "box"),
          # A new row that uses these words makes them common in the rarity table, which lowers
          # this row's score on lines it owns but does not share a brand with ("is a bowl of
          # cereal a healthy breakfast" fell through to the breakfast-ideas list). One point of
          # bias keeps the health comparison here and leaves every portion line with the bowl.
          bias=1),
    # "how much cereal should i eat" reached the cupboard-clearing card, because a cupboard key
    # carries the dry goods and a bare "how": a portion question is about the bowl, and the bowl
    # has a figure on the packet nobody weighs.
    entry("cereal-portion",
          (("cereal", "cereals", "cornflakes", "muesli", "granola", "shreddies", "weetabix",
            "bran flakes", "porridge", "porridge oats", "oats", "oatmeal", "crunchy nut",
            "rice krispies", "coco pops", "frosties", "special k", "cheerios"),
           ("how much", "much", "portion", "portions", "serving", "servings", "per person",
            "how many", "should i eat", "should i have", "am i meant to", "bowl", "bowlful",
            "how much of", "too much", "enough")),
          "A 40g serving of cereal is one small bowl - check the box, because granola and muesli "
          "are heavier per spoon than cornflakes, and most people pour about twice the serving "
          "into a normal bowl. For porridge, 40g of dry oats is one portion, which is about four "
          "heaped tablespoons or half a mug; it swells to a proper bowl with 250ml of milk or "
          "water. If a 40g bowl leaves you hungry by ten, add a banana or a spoon of yogurt "
          "rather than more cereal, and if you are measuring granola, weigh it once - a 50g "
          "serving can carry 12 to 15g of sugar.",
          # cooking the bowl, a recipe that uses oats, and a cereal bar with the sugar question
          # are other rows: the milk and water here are the porridge method's words
          avoid=("cook", "cooking", "make", "made", "recipe", "microwave", "hob", "pan",
                 "overnight", "soak", "bake", "baking", "bread", "flapjack", "cookie",
                 "cookies", "biscuit", "bar", "bars", "smoothie", "weaning", "baby", "toddler",
                 "kids", "sugar", "calories", "calorie", "healthy", "healthier", "better",
                 # how much milk or water goes in the pan is the porridge method, and a figure
                 # for one nutrient is the nutrient row, not a portion
                 "milk", "water", "fibre", "fiber", "protein", "carbs", "carb", "iron",
                 "vitamin", "vitamins", "salt", "nutrients", "nutrient",
                 "worse", "gluten", "allergy", "allergic", "cupboard", "cupboards", "pantry",
                 "larder", "moths", "weevils", "mice", "store", "storage", "keep", "keeps"),
          # the cupboard row keys the dry goods too and a portion question names one of them, so
          # this row has to outrank it: a bowl is not a cupboard
          bias=2),
    entry("sweeteners",
          (("sweetener", "sweeteners", "aspartame", "sucralose", "stevia", "splenda", "canderel",
            "diet coke", "diet drinks", "diet drink", "coke zero", "sugar free", "sugar-free"),
           ("bad", "safe", "worse", "healthier", "cancer", "ok", "okay", "alright", "use",
            "better", "fine", "harm", "harmful", "instead", "good")),
          "Sweeteners are safe at the amounts in drinks and yoghurts: aspartame, sucralose and "
          "stevia have been tested for decades, and the cancer alarm about aspartame is a hazard "
          "rating that would need something like twenty cans a day. The honest catch is that diet "
          "drinks do not seem to help people lose weight - they do not fill you up, and they keep a "
          "sweet tooth sweet. Water, tea or coffee is the cheaper swap.",
          bias=1),
    entry("honey-vs-sugar",
          (("honey",), ("sugar", "better", "healthier", "than", "instead", "less", "swap", "worse",
                        "or", "which",
                        # "is honey good for you" is the same comparison as "is honey better
                        # than sugar", and it was a hedge; the cough and sore-throat lines are
                        # fenced below, so the plain health question can come here
                        "good for", "good for you", "healthy", "healthier", "bad for",
                        "bad for you")),
          "Honey is sugar with a nicer story: it is about 80 per cent sugar, and a teaspoon has "
          "roughly the same calories as a teaspoon of sugar, so it counts towards the 30g a day "
          "free-sugar limit in exactly the same way. It tastes sweeter, so you may use less of it. "
          "The one real difference is that honey is not for babies under one.",
          avoid=("sore throat", "cough", "cold", "lemon", "jar", "local honey", "hayfever",
                 "hay fever", "allergy", "allergies")),
    entry("cooking-oil",
          (("olive oil", "sunflower oil", "vegetable oil", "rapeseed oil", "coconut oil",
            "groundnut oil", "cooking oil", "frying oil", "rapeseed", "sunflower"),
           ("better", "healthier", "which", "than", "or", "use", "fry", "frying", "cook",
            "cooking", "worth", "bad", "good", "healthy")),
          "For everyday cooking, olive oil and rapeseed oil are the best all-rounders: mostly "
          "unsaturated fat, and rapeseed has the most omega-3 of the ordinary oils. Extra virgin "
          "olive oil is fine for frying at normal pan heat. Coconut oil is the one to hold back on, "
          "because it is about 85 per cent saturated fat. Whichever you use it is still about 120 "
          "calories a tablespoon, so how much matters more than which.",
          avoid=("hair", "skin", "drizzle", "dressing", "recipe", "substitute for", "run out",
                 "gone off", "rancid", "smoke point", "splash")),
    entry("baked-potato",
          (("baked potato", "baked potatoes", "jacket potato", "jacket potatoes", "potato",
            "potatoes"),
           ("healthy", "good for", "fattening", "bad for", "diet", "calories", "carbs", "better",
            "lose weight", "slimming", "weight")),
          "A jacket potato is a good everyday carbohydrate: about 200 calories for a medium one, "
          "more fibre than rice or pasta if you eat the skin, and it fills you up. What decides the "
          "meal is the topping - beans, tuna, cottage cheese or chilli are fine; a lake of butter, "
          "cheese and mayo turns it into the calorie bomb people blame the potato for.",
          avoid=("grow", "growing", "plant", "planting", "harvest", "sprouting", "chit", "chitting",
                 "store", "storing", "boil", "boiling", "roast", "roasting", "mash", "chips",
                 "wedges", "recipe", "cook", "salad", "soup", "gnocchi")),
    # A roast potato is not a jacket potato: once "roast" was out of the baked-potato row's
    # avoid, "how many calories in roast potatoes" and "are roast potatoes fattening" were
    # answered with the jacket potato's "about 200 calories for a medium one", which is the
    # wrong potato and the wrong number - the fat the tray goes in is the whole question.
    entry("roast-potato-nutrition",
          # the bare potato is the baked-potato row's line: "how many calories in potatoes" is
          # a plain potato, not a tray of them, so only the roast names are keyed here.
          (("roast potato", "roast potatoes", "roasties", "roastie", "roasted potatoes",
            "roasted potato"),
           ("calories", "calorie", "fattening", "fatten", "healthy", "healthier", "unhealthy",
            "bad for you", "good for you", "slimming", "diet", "weight loss", "waistline",
            "carbs", "carb", "keto", "nutrition", "nutritious", "how many calories")),
          "About 200 calories per 100g as a side, nearer 300 if the tray is deep in oil - the "
          "potato itself is only about 90 before the fat goes on, so it is a carbohydrate like any "
          "other and the oil is what adds up. A thin film that just coats them, on a tray that is "
          "hot rather than swimming, is what keeps a roast potato an everyday thing.",
          # the method, the keeping, the crisps and the jacket potato are four other answers
          avoid=("how do i make", "how do you make", "recipe", "parboil", "crispy", "crisp",
                 "keep", "keeps", "freeze", "reheat", "leftover", "leftovers", "jacket",
                 "baked", "mash", "chips", "crisps", "wedges", "salad", "soup", "grow",
                 "plant", "sprout", "store")),

    entry("skip-a-meal",
          # a skipped breakfast has its own entry ("is breakfast important"), which says why a
          # bowl with protein in it helps; this row is the meal people drop in the middle of a day
          (("skip lunch", "skip dinner", "skip a meal", "skip meals", "skipping meals",
            "skipping lunch", "skipping dinner", "miss lunch", "missed lunch", "miss a meal",
            "no lunch", "not eating lunch", "skip tea"),
           ("bad", "ok", "okay", "fine", "healthy", "worse", "matter", "harm", "should i",
            "is it", "problem", "wrong")),
          "Skipping a meal now and then is fine - a busy day, a lie-in, a big late breakfast - and "
          "nothing bad happens. What matters is the total you eat and drink across the day, and "
          "whether you get so hungry that you raid the cupboard at four. Skipping meals on purpose "
          "to control your weight tends to backfire; skipping one because you are not hungry is not "
          "a problem.",
          bias=1,
          # "is breakfast important" is its own entry, and fasting is a different question
          avoid=("fasting", "fast", "16:8", "intermittent")),
    entry("milk-choice",
          (("milk", "whole milk", "semi skimmed", "skimmed milk", "full fat milk", "oat milk",
            "soya milk", "almond milk", "dairy"),
           ("good for", "as good", "good", "healthy", "better", "fattening", "bad for", "which",
            "or", "than", "calcium", "protein", "worth", "need",
            # "how much milk should i drink" was answered with the alcohol unit limit (the units
            # row reads "drink"), and the amount of milk a person drinks is this row's question
            "how much", "how many", "a day", "per day", "pint", "pints", "glass", "glasses",
            "should i drink", "drink a day",
            # "can i have milk" is asking whether milk is good for you, and with the free-from
            # table standing down it landed on the macaroni cheese recipe.
            "can i have", "can i drink", "ok to have", "ok to drink",
            # "should i have dairy" was the one shape of the same question that still had no
            # answer on this head: it was fenced off the free-from card and the milk row's list
            # had "can i have" but not "should i have", so it went to the refusal.
            "should i have", "should i drink", "should i eat",
            # "is oat milk ok" was the porridge recipe: the row that reads "oat" and "milk" took
            # it, and this row never saw the line because "ok" was not one of its ask words.
            "ok", "okay", "fine", "safe", "alright", "any good", "worth it", "better than")),
          _a_plant_milk,
          bias=1,
          avoid=("breast", "formula", "weaning", "allergy", "allergies", "intolerant", "intolerance",
                 "lactose", "gone off", "off milk", "sour", "expired", "curdle", "curdled",
                 "how long", "freeze", "goat", "make", "recipe", "sauce", "froth", "frothing",
                 "steam", "coffee", "tea",
                 # "how much milk in porridge" is the porridge recipe, and the amount words
                 # above took it once this row had them: the milk that goes into a dish belongs
                 # to the dish's own table.
                 "in porridge", "for porridge", "porridge", "in a sauce", "in the sauce",
                 "in a cake", "in the cake", "bake", "baking", "cook", "cooking",
                 "in a recipe", "for the recipe", "in batter", "in a smoothie",
                 # "how much is a pint of milk these days" is a price, not a nutrition question,
                 # and the amount words above are what let it in
                 "price", "prices", "cost", "costs", "how much is", "these days", "pence",
                 "pounds", "cheap", "cheapest", "supermarket", "shop",
                 # a pudding or a dinner that has to be dairy free is a cooking question: "i
                 # cant eat dairy, what can i have for pudding" was answered with milk.
                 "pudding", "puddings", "dessert", "desserts", "cant eat", "can't eat",
                 "cannot eat", "dairy free", "no dairy", "what can i")
                 # a day word asks whether this carton is still good, and the answer to that is
                 # the carton card: "can i drink milk tomorrow" was told milk is good for you.
                 + DAY_WORDS),
    entry("eat-after-run", (("eat", "eating", "food", "protein", "recover", "recovery"),
                            ("after a run", "after the run", "after running", "after i run",
                             "after my run", "after a saturday run", "after the gym",
                             "after a workout", "after my workout", "after exercise",
                             "afterwards", "post workout", "post-workout", "recover")),
          "Within an hour or so, something with carbohydrate and 20 to 30g of protein: milk and a "
          "banana, yoghurt with fruit, eggs on toast, a chicken sandwich. The window is wider than "
          "the gym lore says - the total protein and calories across the day matter more than the "
          "half hour - but eating soon after does help you feel human again.",
          bias=1),
    entry("breakfast-important", (("breakfast", "morning"), ("important", "skip", "skipping",
                                                             "most important", "necessary",
                                                             "eat", "should i")),
          "Breakfast is not magic, and skipping it does not make you fat or thin on its own: what "
          "matters is the total day. If you are hungry in the morning, eat something with protein "
          "and fibre - eggs, porridge, yoghurt and fruit - because it makes the mid-morning biscuit "
          "much less likely. If you are genuinely not hungry, waiting until lunch is fine.",
          bias=2,
          # "what should I have for breakfast" is a request for ideas, and cooking.py answers it
          ask=("important", "skip", "skipping", "necessary", "is it", "does it matter", "true",
               "worth", "need to", "is breakfast")),
    entry("coffee-good", (("coffee", "tea", "espresso", "latte"), ("bad for you", "healthy",
                                                                 "good for you",
                                                                 "heart", "safe", "caffeine",
                                                                 "good")),

          _coffee_or_tea,
          # brewing questions (how much water, how long to steep) belong to cooking.py
          avoid=("kettle", "boil", "brewing", "brew", "teapot", "cups of tea", "put in",
                 "how much water", "milk", "steep",
                 # "how much coffee is safe in a day" is the limit question, and the entry that
                 # answers it carries the numbers: 400mg, and 200mg in pregnancy.
                 "how much", "how many", "limit", "a day", "per day")),
    entry("alcohol-units", (("alcohol", "drinking", "beer", "wine", "booze", "units"),
                            ("how much", "how many", "cut down", "cutting down", "stop",
                             "reduce", "limit", "week", "safe", "healthy", "too much",
                             "a day", "per day", "should i",
                             # "is wine good for you" is the same question as "how much wine is
                             # safe", and it was the honest shrug: the row keys "wine" and had
                             # "healthy" as its only health word, so the shape people actually
                             # use - "is X good for you", "is X bad for you" - missed it.
                             # Not the "bad for you" shapes: `alcohol-risk` in science.py answers
                             # "is beer bad for you" with the cancer-risk reading, which is the
                             # better card for that question. What had no owner was the
                             # "good for you" shape, and that is what the limit answers.
                             "good for you", "good for me", "is it good")),
          "The UK limit is 14 units a week for men and women, spread over three or more days, and a "
          "unit is a small glass of wine or half a pint of ordinary beer - so a bottle of wine is "
          "about nine. Cutting down works better with rules than willpower: no drink on two nights "
          "a week, no drink in the house, and a smaller glass.",
          # "drinking" is the word for water too, and this entry was taking "how much water should
          # i drink" away from science.py's water-intake
          bias=1,
          # "what should i get my sister who doesnt drink alcohol" is a present, and the limit
          # is not what it is asking for.
          guard=not_a_present,
          ask=("alcohol", "units", "beer", "wine", "booze", "drinking", "cut down", "limit",
               "a week", "per week", "too much", "safe", "reduce", "stop"),
          # "should i drink full fat milk" reached this row on "drink" and was answered with the
          # unit limit: a drink that is not alcohol is not a units question, so the drinks that
          # are not alcohol are named here beside water and squash.
          avoid=("water", "fluids", "hydrate", "thirsty", "water bottle", "bottles of water",
                 # "united" is one letter from "units", so "how many countries in the united
                 # kingdom" matched this row's ask and was answered with the 14-unit limit.
                 # A place is not a drink.
                 "united kingdom", "united states", "great britain", "kingdom", "countries",
                 "country", "states", "nation", "nations",
                 "glasses of water", "kettle", "squash", "juice", "milk", "full fat milk",
                 "full-fat milk", "orange juice", "fizzy", "smoothie", "milkshake", "cordial",
                 "kombucha",
                 # "a bottle of wine" is a units line and the bare word "bottle" used to stand
                 # this entry down, so it was answered as a storage question.
                 # a driving limit is cars.py's answer, and this entry was taking it: "how many
                 # drinks can i have before driving" got the 14-units-a-week figure instead of
                 # "no safe number of drinks"
                 "driving", "drive", "drink driving", "behind the wheel", "breathalyser",
                 "the morning after", "before driving", "drive home",
                 # a limit is not a method: habits.cut-down-drinking owns the how, and the bias
                 # below was tipping "i want to cut down on drinking" to the 14-unit figure
                 # the person's own wish is the method entry's line ("i want to cut down on
                 # drinking" was getting the 14-unit figure), while "how do i cut down on
                 # alcohol" keeps the limit-and-rules answer it has always had
                 "want to cut down", "want to cut", "want to reduce", "want to stop",
                 "drink less", "drinking less", "stop drinking", "stopping drinking",
                 "quit drinking", "give up drinking", "give up the drink",
                 "cut down on drinking", "cut down on the drinking", "reduce my drinking",
                 "i drink too much",
                 # "i drink 16 coffees a week is that too much" is a caffeine question: "drink"
                 # is a form of "drinking", so a count of coffees reached the units answer. Only
                 # the drinks with caffeine in them are named here.
                 "coffee", "coffees", "tea", "teas", "caffeine", "cola", "energy drink",
                 "energy drinks",
                 # A baby's milk is measured in ounces and millilitres and asked for in months,
                 # and both words are also a units question's ("how many ounces should a 3 month
                 # old drink" took the 14-unit figure). A child of any age is not drinking
                 # alcohol, so the age and the child are what stand this row down.
                 "baby", "babies", "newborn", "newborns", "infant", "infants", "toddler",
                 "toddlers", "my baby", "month old", "months old", "week old", "weeks old",
                 "year old", "years old", "formula", "breast milk", "breastfeeding",
                 "ounces", "feed", "feeds", "feeding")),
    # Alcohol and a baby is its own question and it had no answer at all: "is it safe to drink
    # alcohol when pregnant" was reaching cars.py's drink-driving limit, and once that entry was
    # guarded it fell to "Lovely to hear. Enjoy it!" for a woman worried about a glass of wine
    # before she knew.
    entry("alcohol-while-breastfeeding",
          (("alcohol", "wine", "beer", "lager", "cider", "prosecco", "champagne", "gin", "vodka",
            "a drink", "drink", "drinks", "drinking", "units", "booze"),
           ("breastfeeding", "breast feeding", "breast-feeding", "breastfeeding my",
            "nursing", "feeding my baby", "feeding the baby", "expressing", "pumping",
            "breast milk", "breastmilk", "while im feeding", "while breastfeeding",
            # "is beer good for milk supply" is the old wives' tale this row is asked about
            "milk supply", "my supply", "supply")),
          "Feed first, then have the drink: alcohol is in your milk at its highest about half an "
          "hour to an hour after a glass and is gone in two to three hours for one drink, and "
          "there is no need to pump and dump - that only empties the milk, it does not speed the "
          "alcohol up. So an odd glass with a meal is fine, especially if you feed just before it "
          "or wait a couple of hours after. Getting properly drunk is the thing to avoid, and so "
          "is sharing a bed or a sofa with the baby after drinking.",
          # "can i drink while pregnant" is the pregnancy entry's, and it is a different answer.
          # No ask: the two parts are already an alcohol word and a feeding word, and the ask
          # words a line like this uses ("can i", "while") are the framing taken out of it.
          bias=3,
          # The module guard stands every row down on "breastfeeding", because adult diet
          # advice is wrong for a feeding person - but this row *is* the feeding question,
          # so it keeps the two words it is asked with.
          keep=("breastfeeding", "nursing", "my baby", "baby", "babies"),
          # A drink that is not alcohol is not this question. Part one holds the bare verb
          # ("drink", "drinks", "drinking") because people say "is a drink ok while
          # breastfeeding", and that verb answers for *any* drink: "can i drink coffee while
          # breastfeeding" got the alcohol paragraph, and so did tea, cola, water, juice and
          # milk - the caffeine answer it had before lost to this row's bias. The named
          # non-alcoholic drinks are listed instead of the verb being cut, because dropping the
          # verb would lose "is a drink ok while breastfeeding".
          avoid=("pregnant", "pregnancy", "expecting", "trimester", "trying for a baby",
                 # not "decaf": the caffeine row already stands down on it, so adding it here
                 # would turn that line into a handoff rather than a right answer
                 "coffee", "coffees", "caffeine", "espresso", "latte", "cappuccino",
                 "tea", "teas", "green tea", "herbal tea", "peppermint tea", "camomile tea",
                 "cup of tea", "cola", "coke", "pepsi", "fizzy drink", "fizzy water",
                 "water", "juice", "orange juice", "apple juice", "squash", "lemonade",
                 "energy drink", "sports drink", "milkshake", "smoothie", "hot chocolate",
                 # "milk" alone cannot go in this list: "is beer good for milk supply" is one of
                 # the lines this row exists for, so only the drinking-milk shapes stand down
                 "drink milk", "drinks milk", "glass of milk", "cows milk", "cow's milk",
                 "soya milk", "oat milk", "almond milk", "a milky drink",
                 # keeping "baby" is what lets "a glass of wine while feeding my baby" through,
                 # and the child is never the one drinking
                 "my baby have", "my baby drink", "my baby has", "give my baby", "baby beer",
                 "baby wine", "toddler",
                 # This row is the alcohol question and it is keyed on the word "drink", which
                 # every other drink in the world uses too: "can i drink coffee while
                 # breastfeeding" was answered with Feed first, then have the drink - the
                 # alcohol card - and so were tea, cola and water. A row about one drink does
                 # not answer a line that names another, which is the same rule the caffeine row
                 # keeps in the other direction (its own avoid list is alcohol, wine, beer).
                 "coffee", "caffeine", "decaf", "tea", "cola", "coke", "diet coke",
                 "energy drink", "energy drinks", "water", "juice", "squash", "lemonade",
                 "hot chocolate",
                 # the cups that were missing from the list above: "can i drink matcha while
                 # breastfeeding", "...chai...", "...rooibos..." and a herbal tea were answered
                 # with Feed first, then have the drink, which is the alcohol card
                 "matcha", "chai", "rooibos", "fennel tea", "nettle tea", "herbal",
                 "peppermint", "camomile", "chamomile")),
    # "can i eat curry while breastfeeding" had no row of its own, and the caffeine row answered
    # it ("keep it to about 200mg a day") because the line had "can i" and "while breastfeeding".
    # There is no list of foods a feeding mother must avoid, and that is the answer people need.
    entry("food-while-breastfeeding",
          (("breastfeeding", "breast feeding", "breast-feeding", "nursing", "lactating",
            "chestfeeding", "while im feeding", "while breastfeeding", "still feeding"),
           ("eat", "eating", "food", "foods", "diet", "curry", "curries", "spicy", "spice",
            "chilli", "chili", "garlic", "onion", "onions", "peanut", "peanuts", "nuts", "nut",
            "sushi", "beans", "cabbage", "broccoli", "citrus", "tomato", "tomatoes", "dairy",
            "cheese", "milk", "juice", "orange juice", "apple juice", "squash", "fizzy",
            # the bare drinking words are not in this key: "water" and "drink" are the fluid
            # row's words (breastfeeding-drinks answers how much to drink), and adding them here
            # made those words common enough that "is tap water ok while breastfeeding" lost
            # the tap-water answer and got the fluid one. A word another row needs stays rare.
            "caffeine free", "decaf",
            "anything i eat", "what can i eat", "avoid any foods", "foods to avoid",
            "make my baby", "windy", "fussy", "gassy")),
          "There is no list of foods to avoid while you are breastfeeding: eat normally and "
          "often, because feeding makes you hungry. Curry, garlic, onions and spicy "
          "food are all fine - your baby may notice the flavour in your milk and be a bit fussy "
          "for a day, and that passes without either of you giving anything up. Peanuts and "
          "other nuts are fine too unless your baby has already reacted to them. The fish rules "
          "from pregnancy stay: no shark, swordfish or marlin, and tuna to about two fresh "
          "steaks or four medium tins a week. If you think one food is upsetting them, note the "
          "day and try it again in a fortnight rather than cutting out a whole food group.",
          bias=2,
          # The module guard stands every row down on a feeding person, because adult portions
          # are wrong for one; this row is the feeding question, so it keeps its own words.
          keep=("breastfeeding", "breast feeding", "breast-feeding", "nursing", "lactating",
                "chestfeeding", "while im feeding"),
          # The drink rows have their own answers (caffeine at 200mg, alcohol and the timing),
          # and medicine while feeding is the pharmacist's question, not a food one.
          avoid=("coffee", "coffees", "caffeine", "espresso", "latte", "cappuccino",
                 # "is tap water ok while breastfeeding" is the tap-water card's question, and
                 # the bare "water" in the key above would otherwise take it
                 "tap", "tap water", "bottled water", "boiled", "boil", "chlorine", "fluoride",
                 "water filter", "safe to drink", "hard water", "soft water",
                 "tea", "teas", "green tea", "cola", "energy drink", "energy drinks",
                 "alcohol", "wine", "beer", "units",
                 "paracetamol", "ibuprofen", "medicine", "medication", "antibiotic",
                 "pregnant", "pregnancy", "my baby have", "give my baby", "my baby eat",
                 "weaning", "month old", "months old", "year old", "how much milk",
                 "how many ounces", "recipe", "cook", "bake")),

    entry("alcohol-in-pregnancy",
          (("pregnant", "pregnancy", "expecting", "expecting a baby", "trying to conceive",
            "trying for a baby"),
           ("alcohol", "drink", "drinking", "wine", "beer", "cider", "prosecco", "gin", "vodka",
            "a glass", "glass of", "a drink", "safe", "ok", "okay", "fine", "worried")),
          "No amount of alcohol is known to be safe in pregnancy, so the advice is none at all. "
          "But a drink or two before you knew is very unlikely to have done any harm, and the "
          "worry is worse than the drink: most women who had one went on to have a healthy baby. "
          "Tell your midwife so it is in your notes, and if stopping is hard, ask for help rather "
          "than doing it alone.",
          keep=("pregnant", "pregnancy", "expecting", "trying to conceive", "trying for a baby"),
          # the pregnant word alone is not enough: "is caffeine ok in pregnancy" and "can i eat
          # soft cheese while pregnant" are nutrition questions this entry must not take.
          ask=("alcohol", "drink", "drinking", "drank", "wine", "beer", "cider", "prosecco",
               "gin", "vodka", "booze", "a glass", "glass of"),
          avoid=("breastfeeding", "nursing", "feeding a baby", "my dog", "my cat",
                 # The bare verb "drink" is in the key above, so every drink was read as
                 # alcohol: "can i drink milk while pregnant" was given the no-alcohol paragraph
                 # and "can i drink juice while pregnant" the same. A drink that is not alcohol
                 # stands this row down; a line that names alcohol as well still reaches it,
                 # because only the other drink is in this list.
                 "milk", "milkshake", "milkshakes", "juice", "orange juice", "squash",
                 "smoothie", "smoothies", "water", "bottled water", "fizzy water", "coffee",
                 "tea", "decaf", "decaff", "decaffeinated", "cola", "diet coke", "coke",
                 "energy drink", "energy drinks", "hot chocolate", "lemonade")),

    entry("caffeine-before-bed", (("coffee", "tea", "caffeine", "espresso", "energy drink",
                                  "green tea"),
                                 ("before bed", "at night", "in the evening", "bedtime", "evening",
                                  "keep you awake", "cant sleep", "can't sleep", "sleep", "awake",
                                  "bed")),
          "Caffeine is still in your body hours later: about half of it is gone after five or six "
          "hours, so a 4pm coffee is still a quarter there at midnight. Have your last ordinary cup "
          "by early afternoon and switch to decaf, herbal tea or water after that. If you are "
          "sensitive, even one after 6pm can cost you the deep sleep that does the repairing.",
          # the amount people can have in a day is caffeine-limit's question, not this one
          ask=("before bed", "at night", "in the evening", "bedtime", "evening", "keep you awake",
               "sleep", "awake", "bed", "cant sleep", "can't sleep", "late")),
    entry("water-habit", (("water", "hydrate", "hydration", "drinking", "fluid", "fluids"),
                            ("drink more", "make myself", "forget", "remember", "hate water",
                             "dont like water", "don't like water", "taste of water",
                             "never drink", "keep forgetting", "struggle to drink",
                             "getting enough", "how do i drink",
                             # how little they drink, in the words people use for it: these
                             # lines were told to unscrew the aerator on a tap, because the
                             # plumbing entry had "water" and "barely" in its key
                             "barely drink", "hardly drink", "barely any water",
                             "hardly any water", "dont drink enough", "don't drink enough",
                             "not drinking enough", "drink enough water", "dehydrated",
                             # the same shortfall said with a quantity instead of "enough":
                             # "i dont drink much water", "i dont drink any water", "i dont
                             # drink water at all" were said back as "Noted: ..." because the
                             # statement guard below caught "dont drink" first
                             "drink much", "drink any", "drink very little", "drink little",
                             "drink nothing", "water at all", "any water", "much water",
                             "little water", "rarely drink", "seldom drink")),
          "Fill a bottle in the morning and keep it where you sit, and put a glass by the kettle so "
          "every cup of tea comes with one. Drinking with meals and after every trip to the loo is "
          "the cheapest trigger. Squash, tea and milk count towards your fluids, so if you dislike "
          "plain water, flavour it with lemon or have a diluted squash instead.",
          # the daily amount is science.py's water-intake, and water that is not coming out of
          # the tap is the plumbing question: "barely any water coming out of the tap" is a
          # blocked aerator, not a person who forgets to drink
          avoid=("how much", "how many", "litres", "liters", "pints", "glasses a day",
                 # "should i drink more water" and "do i need to drink more water" ask for the
                 # figure, not a habit, and "drink more" alone was enough to take them.
                 "should i drink", "should i be drinking", "do i need to drink",
                 "am i drinking enough",
                 # the other direction is science.py's water-too-much: a person asking how to
                 # stop, or one who is always thirsty, is not short of the tips below. "how do
                 # i stop drinking so much water" got "fill a bottle in the morning" because
                 # "much water" is in the key above.
                 "too much", "so much", "stop drinking", "thirsty", "thirst", "quench",
                 # a shortfall that names water is the amount question, the same as "i dont
                 # drink enough water"; without water in the line, "i dont drink enough" keeps
                 # the tips
                 "drink enough water", "drinking enough water",
                 "kettle", "boil", "teapot", "bottle feed", "formula", "plant", "garden",
                 "tap", "taps", "faucet", "shower", "pipe", "pipes", "boiler", "cistern",
                 "radiator", "pressure", "coming out", "comes out", "hot water", "cold water",
                 "drain", "leak", "leaking", "mould", "bath", "sink"),
          # "i dont drink much water" is a statement about the speaker, which the shared guard
          # normally keeps for the memory lane. Here the thing in the line is water and the rest
          # of it is a shortfall, which is this entry's own question, so the guard stands down.
          keep=("dont drink", "don't drink", "do not drink")),
    entry("eat-slowly", (("slowly", "slow", "chew", "full up", "still hungry"), ("eat", "eating",
                                                                               "meal", "chewing",
                                                                               "why")),
          "It takes about twenty minutes for the fullness signal to arrive, so a meal eaten in five "
          "leaves you looking for more afterwards. Put the fork down between mouthfuls, drink water "
          "with the meal and eat at a table without a screen - those three do more than any rule "
          "about chewing a set number of times.",
          # "any way to slow that down" about bananas is not this: the ask has to be about a meal
          ask=("chew", "chewing", "full up", "fuller", "still hungry", "too fast", "slow down",
               "slowly", "meal", "mealtime", "meal times"),
          # "why" and "slowly" together reach this entry from any machine that is being slow, and
          # "why is my phone charging so slowly" was answered with the fullness signal and a fork. A
          # device that charges or downloads is not a meal, so the entry stands down on those words.
          avoid=("phone", "iphone", "ipad", "tablet", "kindle", "charger", "charging", "charge",
                 "battery", "laptop", "computer", "pc", "wifi", "wi fi", "internet", "download",
                 "downloads", "downloading", "app", "apps", "printer", "boiler", "heating",
                 "car", "engine", "toothbrush", "hoover", "vacuum",
                 # the same shape in plumbing: "why is my bath draining so slowly" was the
                 # fullness signal and a fork, and a bath, a sink or a pipe is not a meal either
                 "bath", "baths", "sink", "sinks", "shower", "drain", "drains", "draining",
                 "drainage", "plughole", "plug hole", "toilet", "pipe", "pipes", "plug")),
    # "will that fill me up", asked straight after the bot named a dish made of pasta and a tin of
    # tomatoes, was the honest shrug on main `8e3fd80`. It is the commonest follow-up there is -
    # whatever the dish was, whether it holds you is a question about protein, bulk and portion -
    # so the entry answers the shape rather than the dish, and needs no memory to do it.
    entry("meal-filling",
          (("fill me up", "fills me up", "fill you up", "filling", "keep me full", "keep you full",
            "stay full", "stays with me", "still hungry", "hungry again", "hold me over",
            "keep me going"),
           ("meal", "dinner", "tea", "lunch", "supper", "dish", "that", "this", "it", "soup",
            "salad", "pasta", "rice", "noodles", "toast", "sandwich", "stew", "curry", "sauce",
            "tomato", "tomatoes", "eat", "eating", "cook", "cooking", "supper")),
          ("Whether a dish holds you comes down to two things, and pasta or rice with a tomato "
           "sauce has neither: there is almost no protein in it and very little fat. Add a tin of "
           "chickpeas or beans, a boiled egg, a handful of grated cheese or a thick slice of bread "
           "and the same dish keeps you full for hours instead of one. The other half is the "
           "amount: a portion of dry pasta about the size of your closed fist is right for one "
           "person, and a tin of tomatoes counts as the vegetable, not the filling. The things "
           "that fill you up for least money are beans, lentils, potatoes, eggs, oats, yoghurt and "
           "wholemeal bread, and a soup or a green salad on its own rarely lasts past two hours."),
          # "still hungry" is the slow-eating answer's phrase too, and how much to eat for a
          # specific goal, how many calories a dish has and why a person wakes up hungry are
          # three other answers
          ask=("fill me up", "fills me up", "fill you up", "filling", "keep me full",
               "keep you full", "stay full", "stays with me", "still hungry", "hungry again",
               "hold me over", "keep me going"),
          # What gets filled up again is a tank, not a person: "she keeps borrowing my car and
          # never fills it up" was told about protein and portion size.
          avoid=("car", "cars", "van", "petrol", "diesel", "fuel", "the tank", "tyres",
                 "borrow", "borrowing", "lends it", "keeps borrowing",
                 # a dental filling is not a filling meal: "can i eat after a filling" was
                 # answered with how much protein a plate of pasta has
                 "after a filling", "after my filling", "after the filling",
                 "after the dentist", "after the dentist appointment",
                 "calories", "how many calories", "lose weight", "losing weight", "slimming",
                 "diet", "gain weight", "how much should i eat", "waking up hungry",
                 "wake up hungry", "in the night", "at night", "why am i always hungry",
                 "always hungry", "all the time", "no appetite", "not eating",
                 "how long to cook", "recipe", "how do i make",
                 # "what should i eat to stay full" wants meals named, and the meal-idea row
                 # names three; this one stands down and lets it answer
                 "what should i eat", "what can i eat", "what shall i eat", "what do i eat",
                 "meal ideas", "ideas for dinner",
                 # "the washing machine is noisy when it fills" and "my filling hurts when i eat
                 # something cold" scored on "fills"/"filling" plus a bare "it"/"eat" and were
                 # answered with whether a dish holds you. A machine that fills and a tooth that
                 # fills are not a meal, and neither is a dentist. "fillings" is NOT one of these
                 # words: it is one edit from the row's own "filling", and `_misspelt_avoid` reads
                 # a word the engine does not know as a slip of the avoid word, so the row stood
                 # down for "is soup filling" and ate every plain fullness question.
                 "washing machine", "machine", "washer", "dishwasher", "tumble dryer",
                 "dryer", "boiler", "kettle", "bath", "radiator", "shower", "toilet",
                 # the same list, in the words people use: a loo fills, a cistern fills and a
                 # header tank fills, and "the loo bangs after it fills" was told what protein a
                 # plate of pasta has. The bowl and the tank are the fixture, not the plate.
                 "loo", "loos", "lav", "lavatory", "wc", "bog", "cistern", "cisterns", "tank",
                 "the tank", "header tank", "flush", "flushes", "flushing", "overflow",
                 "dental", "dentist", "tooth", "teeth", "gum", "gums", "cavity", "toothache",
                 "hurts", "hurting", "hurt", "sensitive", "ache", "aching",
                 # "can you fill in this form" and "i filled in the form but it didnt save" were
                 # answered with whether a dish holds you: the verb is the same and the thing
                 # being filled is paper. Nothing about protein belongs in an answer to a form,
                 # so the row stands down and the fallback's own reader for a thing of theirs
                 # that is on their side of the screen answers instead.
                 "form", "forms", "paperwork", "questionnaire", "questionnaires",
                 "application", "applications", "self assessment", "tax return",
                 "the box", "this box", "that box",
                 # "can you help me fill this in" names no form at all, and the row read the
                 # "fill" and answered with a dish. Filling a form in is never a meal.
                 "fill in", "fills in", "filling in", "filled in",
                 "fill out", "fills out", "filling out", "filled out",
                 "fill this in", "fill it in", "fill that in",
                 "fill this out", "fill that out", "fill it out"),
          bias=2),
    # "Whats a healthy dinner" and "meals under 500 calories" got the shrug, and "dinner under 600
    # calories" got a chat nod: the calorie rows know how many calories are in a food and how many
    # a day needs, and no row knew the everyday shape of the question, which is what to put on the
    # plate. The answer is the same for every cap, because the cap comes out of the plate, so it is
    # written once here and the number in the line is the person's own.
    entry("light-dinner",
          (("healthy", "healthier", "light", "lightest", "low calorie", "low-calorie", "calorie",
            "calories", "kcal", "slimming", "diet"),
           ("dinner", "dinners", "tea", "supper", "lunch", "lunches", "meal", "meals", "eat",
            "eating", "cook", "cooking", "plate")),
          "A healthy dinner is a palm of protein, a fist of potato, rice or pasta, and half the "
          "plate vegetables: 150g of chicken with 200g of new potatoes and a big pile of broccoli "
          "comes to about 400 calories, so a 500-calorie cap is easy to stay under, and a salmon "
          "fillet or a fist of chickpeas makes the same plate again. Grill or roast rather than "
          "fry, and measure the oil, because a tablespoon of it is 100 calories on its own.",
          # how many calories are in a food, how many a day needs, calorie counting and what to eat
          # to lose weight are four other answers, and a calorie cap on a food is the food's own row
          avoid=("how many calories in", "calories in a", "calories in an", "calories in my",
                 "how many calories are in", "how many calories does", "how many calories should",
                 "count calories", "counting calories", "track calories", "calorie counting",
                 "a day", "per day", "day should", "should i eat", "how many", "how much",
                 "lose weight", "losing weight", "weight loss", "slimming world", "keto",
                 "fasting", "intermittent", "in a banana", "in an egg", "recipe", "how do i make",
                 "how long", "calorie deficit", "burn", "exercise", "gym")),
    entry("weigh-weekly", (("weigh", "weighing", "scale", "scales", "weight"), ("how often",
                                                                              "every day",
                                                                              "every morning",
                                                                              "daily",
                                                                              "weekly")),

          "Weigh yourself once a week, same time, same clothes, rather than daily: body water swings "
          "2 to 3 pounds a day and daily weighing mostly tells you about salt and hormones. Judge "
          "the trend over a month, and use a tape measure round your waist alongside it.",
          # how OFTEN to weigh is a different question from how much you should weigh
          ask=("how often", "often", "every day", "every morning", "daily", "weekly", "day")),
]

# Is this food good for me? One verdict per everyday food, keyed by the food and asked every way
# people ask it ("is rice healthy", "is that healthy" a turn after they said rice, "are potatoes
# fattening"). The question is about the diet, not the recipe, so it lives here and not in the
# cooking table: the numbers that decide it are calories, fibre and what goes with the food.
HEALTH_WORDS = ("healthy", "healthier", "unhealthy", "good for you", "good for me", "good for us",
                "bad for you", "bad for me", "fattening", "make me fat", "ok to eat", "okay to eat",
                "fine to eat", "any good", "worth eating", "good for my heart", "bad for my heart",
                "should i eat", "should i avoid", "low fat", "good source", "nutritious",
                # "can i eat bananas" and "can i eat cheese" were punts while the verdict for the
                # food sat here with no key to reach it: "can i" is how people ask the same
                # question as "should i eat". "can i have" is not here - it opens a request for a
                # recipe, a portion or an idea as often as it asks about a food.
                "can i eat", "can i still eat", "am i allowed to eat", "is it bad to eat",
                "is it ok to have", "is it okay to have",
                # "what is spinach good for" and "what are the health benefits of kale" are the
                # same question as "is spinach good for you", and they were every one of them a
                # shrug while the verdict sat in the table with no key to reach it. The food
                # name is the other half of the key, so a bare "good for" cannot take a line
                # about anything but one of these foods.
                "good for", "good about", "health benefits", "benefits of",
                "what does it do for", "superfood",
                # how much of it a day is the same question about the diet, and it was a shrug
                # for the foods whose row says a portion ("how many bananas a day"). "a day" as a
                # pair of words, not "how many", so "how many calories in a banana" keeps the
                # figures it asks for.
                "a day", "per day",
                # "can i eat peanut butter every day" is the same question as "is it healthy",
                # and without these it was a shrug.
                "every day", "everyday", "daily",
                # The permission is the same question as "is it good for you": "can i eat
                # spinach" and "can i have bananas" were a search hedge, because the verdict
                # table only knew the health words. A recipe that happens to be asked this way
                # is kept out by HEALTH_AVOID ("how do i", "cook", "recipe") and by each row's
                # own avoid list.
                "can i eat", "can i have", "can i drink", "am i allowed",
                "should i have", "should i eat", "should i drink",
                # "how much peanut butter should i eat" is a portion question about one food,
                # which is what these rows answer ("two tablespoons is about 190 calories"). The
                # bare "how much" stays in HEALTH_AVOID for the cooking quantities, so the ask
                # has to be the whole phrase.
                "how much should i eat", "how much can i eat", "how much of it",
                "how much of this", "what portion", "how big a portion", "portion size",
                # "how much peanut butter is too much" is the portion question in the words people
                # use, and "how much is" in HEALTH_AVOID stood it down for the quantities guard.
                "too much", "how much is too much")
# A recipe, a cooking time or a portion is another table's question, and the brown against white
# comparison is brown-rice, which carries the fibre figures.
HEALTH_AVOID = ("how do i", "how long",
                # a serving frame is a dinner, not a verdict: "what can i have with fish` was
                # handed the oily-fish paragraph, and "what goes with lentils" the lentil one,
                # because the food name is half of every verdict key. One shared list, so every
                # food in the table is held out of a pairing ask at once.
                "have with", "have it with", "eat with", "goes with", "go with", "serve with",
                "serving with", "pairs with", "alongside", "on the side", "as a side",
                "side dish", "side dishes", "what side", "which side",
                # the bare "how much" was a cooking quantity guard, and it also stood the
                # verdicts down for a portion of one food ("how much peanut butter should i
                # eat"). The quantities it was there for are named instead.
                "how much for", "how much does", "how much to",
                "how much do i need", "how much water", "how much milk", "how much flour",
                "per person", "for four", "for six",
                "for two", "cook", "cooking",
                # "boil", "baking" and "roast" stood here to keep a method out of the verdict
                # table, and "how do i", "how long" and "cook" already do that: what the three
                # went on to keep out was the verdict itself, so "is a boiled egg healthy" was
                # the boiling method and "is an omelette healthy" was a search hedge, while
                # "is it better to boil or roast potatoes" is still turned away by "better".

                "recipe", "freeze", "frozen", "reheat", "leftover", "leftovers", "keep",
                "brown rice", "white rice", "wholegrain", "wholewheat", "wholemeal", "better",
                "which is", "difference", "or rice", "or pasta", "instead of",
                # A food that treats a symptom is the home-remedy question, not the diet one
                # ("is honey good for a cough", "what is good for a cold"), and a growing one is
                # the garden's ("is spinach good for a small pot").
                "cold", "cough", "sore throat", "symptom", "grow", "growing", "plant",
                "garden", "allotment", "seed", "pot", "pots", "soil", "compost",
                "window box", "container",
                # "is it ok to eat pink chicken" is a cooking question, not a diet one: "ok to
                # eat" is an ask here, so the healthy cards took it and said chicken is lean
                # protein, and "is raw pork safe" got the red-meat policy.
                "pink", "raw", "undercooked", "bloody",
                # A day word is the leftovers question. "Is it ok to eat chicken the next day"
                # was "Chicken is lean protein - about 30g in a breast for 160 calories", which
                # is true of any chicken ever cooked and says nothing about last night's, and
                # "is it ok to eat rice the next day" took the calorie card the same way. The
                # keeping tables answer both, in the words of the day they were asked about.
                "next day", "the next day", "the day after", "day after", "day later",
                "days later", "yesterday", "tomorrow", "in the fridge", "out of the fridge",
                "out of date", "past its date", "past the date", "use by", "still ok",
                "still good",
                # A nutrient figure is a different table's question and it knows the number:
                # "is spinach a good source of iron" was the 2.7mg row on main and the general
                # greens verdict here, which is worse. Sugar is the free-sugar row's.
                "iron", "vitamin", "vitamins", "calcium", "protein", "fibre", "fiber",
                "potassium", "omega 3", "omega-3", "sugar", "salt",
                # "can i eat food left out overnight" is the fridge-safety line, and "can i eat
                # before a run" is the when-to-eat one; both have their own answers.
                # "can i eat spinach thats gone a bit yellow" is a staleness question with a
                # keeping row of its own, not a diet one.
                "yellow", "yellowing", "gone yellow", "gone off", "slimy", "mouldy", "moldy",
                "smell", "smells", "smelly", "went off", "past the date", "out of date",
                "left out", "overnight", "out of the fridge", "before a run", "after a run",
                "before bed", "brush", "brushing", "diabetes", "diabetic", "allergy",
                "allergic", "egg free", "egg-free", "nut free", "nut-free", "dairy free",
                "gluten free", "vegan", "vegetarian", "pregnant", "baby", "toddler",
                "leftover", "leftovers", "out to eat", "takeaway", "restaurant")
# A verdict is about one food, so the rows below say what a portion of it is worth and what to
# watch. The tables they extend already answer rice, bread, lentils, oily fish, chicken and
# yoghurt; the foods below are the rest of what people ask about by name from the supermarket,
# chosen because "is X good for you" was a search hedge for every one of them.
FOOD_HEALTH = (
    ("rice-healthy", ("rice",),
     "Rice on its own is about 130 calories per 100g cooked and not fattening: what goes with it "
     "and how much of it decides that. A mug of cooked rice, about 150g, is a normal portion, and "
     "brown rice has around three times the fibre of white.",
     ()),
    ("bread-healthy", ("bread", "toast", "sourdough", "wrap", "wraps", "pitta", "bagel"),
     "Bread is fine: two slices of wholegrain or seeded is about 6g of fibre and a fair base for a "
     "meal. The white sliced loaf has less fibre and less staying power, so keep it for toast and "
     "make the everyday one wholegrain.",
     # "is burnt toast bad for you" is the acrylamide question, and it got the fibre verdict
     # because "toast" is a word this row answers for. A loaf that caught is the burnt-food row's.
     ("burnt", "burned", "charred", "scorched", "burnt toast", "burned toast", "black")),
    ("lentils-healthy", ("lentils", "lentil", "beans", "chickpeas", "pulses", "hummus"),
     "Lentils and beans are one of the best buys in the shop: a drained tin has around 8g of "
     "protein and 6g of fibre for about 120 calories. They count towards your five a day and they "
     "keep you full far longer than the same weight of rice.",
     ()),
    ("oily-fish-healthy", ("salmon", "mackerel", "sardines", "tuna", "fish", "kippers", "trout"),
     "Oily fish is worth two portions a week: the omega-3 in salmon, mackerel and sardines is what "
     "the heart and the joints use, and a 140g cooked portion is a serving. Tinned sardines and "
     "mackerel count and are the cheapest way to do it; tinned tuna is the lean one, so it gives "
     "protein rather than omega-3.",
     # a fish that is kept is fed, not eaten: "do i need to feed fish every day" and "what should i
     # feed my goldfish" were handed the oily-fish verdict, because this row keys on "fish" and
     # "every day" is one of the asks. The feeding shapes, not the bare animal, so "is fish
     # healthy" and "is salmon healthy" keep this row.
     ("feed fish", "feeds fish", "feeding fish", "fed fish", "feed a fish", "feed the fish",
      "feed my fish", "fish food", "goldfish", "aquarium", "fish tank", "tropical fish",
      "koi carp", "can i give my cat", "can i give my dog", "give my cat", "give my dog",
      "can my cat eat", "can my dog eat", "for my cat", "for my dog")),
    # Prawns, scallops, mussels and squid had no verdict row at all: "are prawns healthy" and "are
    # scallops healthy" were both search hedges while the oily-fish row answered tuna. Shellfish is
    # lean protein, which is the thing people want to know, and what makes a prawn dish heavy is
    # the mayonnaise or the breadcrumbs rather than the prawn.
    ("shellfish-healthy", ("prawn", "prawns", "king prawns", "scallop", "scallops", "mussel",
                           "mussels", "crab", "squid", "calamari", "oyster", "oysters",
                           "shellfish", "prawn cocktail"),
     "Shellfish is the leanest protein in the shop: 100g of prawns is about 100 calories and 20g "
     "of protein with barely any fat, and scallops and mussels are much the same, with iron and "
     "zinc in the molluscs. Prawns carry cholesterol, but that matters far less than the "
     "saturated fat in a diet, so it is the mayonnaise, the butter or the breadcrumbs that make "
     "a prawn dish heavy rather than the prawns.",
     # a crab apple is not a crab, and a shellfish that has gone off is the keeping question.
     # So is a shellfish that will not open: "is it ok to eat mussels that didnt open" asks what
     # to do with the closed ones, and this row took the line off the mussels rule (which has the
     # answer) because it also named mussels. What a shellfish is worth eating is a different
     # question from whether this one is safe, so the words of the second stand this row down.
     ("crab apple", "crab apples", "went off", "gone off", "smells off", "smells", "smell",
      "shell", "shells", "picked", "picking", "allergy", "allergic", "pregnant", "pregnancy",
      "open", "opened", "opening", "unopened", "shut", "closed", "dead", "didnt", "didn't",
      "stay shut", "stays shut", "stayed shut")),

    ("chicken-healthy", ("chicken", "turkey", "chicken breast", "chicken thighs"),
     "Chicken is lean protein - about 30g in a breast for 160 calories - so it is what you cook it "
     "in that matters. Skin off and not fried, it is one of the better everyday meats; the breaded "
     "and the deep-fried versions carry the fat.",
     ()),
    ("yoghurt-healthy", ("yoghurt", "yogurt", "greek yoghurt", "fromage frais", "skyr"),
     "Plain yoghurt is a good buy: about 10g of protein and a third of a day's calcium in a 150g "
     "pot. The fruit ones and the children's tubes are the ones with 12g of sugar or more, so buy "
     "plain and add your own fruit or a spoon of jam.",
     ()),
    # An egg asked about as food for you is a verdict, not the pot: on main `is an omelette
    # healthy` was a search hedge and `is a boiled egg healthy` was the boiling method. The one
    # egg verdict already there (`eggs-cholesterol`) needs a word from its own second group, and
    # `healthy` is only an ask for it, so the line covered one signal and was turned away. The
    # dish names are in this row because a person asks about the omelette they are about to eat,
    # and what makes it heavy is what it is cooked in, not the egg.
    # Not the bare "egg" or "eggs": `eggs-daily` already answers "is an egg healthy" and
    # `eggs-cholesterol` answers "is an egg bad for you", and both are better lines than this
    # one for a bare egg. The gap was only the egg as a dish.
    ("eggs-healthy", ("omelette", "omelettes", "frittata", "scrambled egg",
                      "scrambled eggs", "boiled egg", "boiled eggs", "poached egg",
                      "poached eggs", "fried egg", "fried eggs"),
     "An egg is one of the cheapest good foods there is: about 78 calories and 6g of protein, "
     "with the B12 and vitamin D that people buy supplements for. The cholesterol in food turned "
     "out to matter far less than the saturated fat in the diet, so one or two a day is fine for "
     "most people. What makes an omelette heavy is the butter and the cheese, not the eggs.",
     ("crack", "cracked", "shell", "shells", "rubbery", "fluffy", "filling", "fold",
      "cholesterol", "how many", "a day",
      # "is a boiled egg bad for you" is the cholesterol question, and `eggs-cholesterol` has
      # answered it since before this row existed: the dish verdict is for the asks that want a
      # verdict ("is an omelette healthy"), not for the one that is already a card of its own.
      "bad for you", "bad for me")),
    # not the bare word "greens": the matcher reads a plural as its singular, and "green"
    # reaches "green tea" and "green beans", which are not leaves.
    ("greens-healthy", ("spinach", "kale", "chard", "leafy greens", "watercress",
                        "spring greens", "cavolo nero", "swiss chard"),
     "Spinach, kale and the other leafy greens are among the best value in the shop at about 25 "
     "to 35 calories per 100g: a bag wilted in a pan is one of your five a day and brings folate, "
     "vitamin C and vitamin K, plus nitrates that help blood pressure. The iron in spinach is "
     "real (2.7mg per 100g) but poorly absorbed, so eat it with something containing vitamin C - "
     "lemon, peppers, a glass of juice. One caution: if you get kidney stones, spinach is the "
     "leaf to go easy on, because of its oxalate.",
     ("smoothie", "salad", "soup", "slug", "slugs", "limp", "wilted", "bag of", "dressing")),
    ("broccoli-healthy", ("broccoli", "cauliflower", "sprouts", "brussels sprouts", "cabbage",
                          "romanesco", "cavolo nero"),
     "The brassicas are worth eating often and cost about 30 to 40 calories per 100g: broccoli "
     "has more vitamin C than an orange per 100g, and the whole family brings folate, vitamin K "
     "and fibre. Steam it for 4 or 5 minutes rather than boiling it to bits, since long cooking "
     "is what loses the vitamin C. There is nothing in them that detoxes anything - the reason to "
     "eat them is that they fill half a plate for very few calories.",
     # not the bare word "sprouting": the matcher reads it as a form of "sprouts", so it
     # masked the row's own key and every brussels-sprouts verdict was a hedge. The phrase is
     # what the question actually says.
     ("smoothie", "salad", "soup", "slug", "slugs", "patch", "are sprouting",
      "is sprouting", "have sprouted", "has sprouted")),
    ("carrots-healthy", ("carrot", "carrots"),
     "Carrots are about 40 calories per 100g and one decent carrot gives you more than a day's "
     "vitamin A, as beta-carotene. Cooked with a little fat - butter, oil, in a stew - you absorb "
     "more of it than from raw sticks, so both are worth eating. They do not turn you orange "
     "unless you eat them by the bagful for weeks, and they are one of the cheapest vegetables "
     "there is.",
     ("smoothie", "soup", "cake", "muffin", "muffins", "juice", "slug", "slugs", "fly",
      "flies")),
    ("banana-healthy", ("banana", "bananas", "apple", "apples", "orange", "oranges", "pear",
                        "pears"),
     "A banana is about 100 calories with 3g of fibre and around 400mg of potassium, and the "
     "sugar in it (about 14g) comes with that fibre and water, so it is a snack rather than a "
     "problem - fresh fruit is not what the 30g free-sugar limit is aimed at. A greener one has "
     "more resistant starch, which is good for the gut; a spotted one is sweeter and easier to "
     "digest before a run. One or two a day is fine, and the same holds for apples, oranges and "
     "pears at 60 to 80 calories each.",
     # "is apple juice healthy" was the banana card: "apple" is in this key and "healthy" is the
     # ask, so the row answered for a glass of juice. Juice has its own row, and the fruit's
     # verdict is not the drink's.
     ("smoothie", "loaf", "cake", "bread", "banana bread", "muffin", "muffins", "ice cream",
      "frozen", "ripen", "ripe", "green", "peel", "slug", "fly", "flies", "juice", "juices",
      "cider", "smoothies", "dried", "crisps", "chips", "tree", "trees", "grow")),
    ("avocado-healthy", ("avocado", "avocados", "guacamole"),
     "Avocado is a good food that is easy to overdo: half a medium one is about 150 calories and "
     "15g of fat, nearly all of it monounsaturated, which is the kind that helps cholesterol "
     "rather than harming it. It also brings about 5g of fibre and more potassium than a banana "
     "per 100g. Half a day is a sensible portion; a whole one on toast is a meal, not a spread.",
     ("ripen", "ripe", "brown", "black", "stone", "keep", "freeze", "toast", "smash",
      "guacamole")),
    ("gluten-healthy", ("gluten", "seitan", "vital wheat gluten"),
     "Gluten is just the protein in wheat, barley and rye, and it is only a problem for the "
     "roughly one in a hundred people with coeliac disease, or for a wheat allergy - for everyone "
     "else there is nothing to avoid. If bread and pasta leave you bloated, windy or tired, ask "
     "the GP for a coeliac blood test before you cut gluten out, because the test only works while "
     "you are still eating it. Wholegrain wheat is one of the best sources of fibre in an "
     "ordinary diet, so it is worth keeping unless a test says otherwise.",
     # a person who cannot eat gluten, or asks what to have for a meal without it, wants the
     # free-from list and the meal ideas: the verdict is for the person asking whether gluten
     # itself is bad for them
     ("free", "flour", "bread", "recipe", "bake", "baking", "cake", "coeliac", "celiac",
      "allergy", "allergic", "intolerant", "intolerance", "sensitivity",
      "cant eat", "can't eat", "cannot eat", "without", "avoid", "cut out", "cutting out",
      "for lunch", "for breakfast", "for dinner", "for tea", "for supper", "for pudding",
      "what can i have", "what can i eat", "lunch", "breakfast", "dinner")),
    ("nuts-healthy", ("nuts", "almonds", "walnuts", "cashews", "hazelnuts", "pistachios",
                      "pecans", "brazil nuts", "mixed nuts"),
     "A 30g handful of nuts is about 175 calories and one of the better snacks you can buy: 6g "
     "of protein, 3g of fibre and fat that is mostly unsaturated, and people who eat them "
     "regularly tend to weigh less, not more, because they are satisfying. Walnuts are the one "
     "with omega-3 (plant ALA). Buy them unsalted and unsweetened, and count the handful out "
     "rather than eating from the bag.",
     ("squirrel", "birds", "bird", "feed the", "nut free", "nut-free", "recipe", "cake",
      "roast", "roasted", "toast", "cost")),
    ("peanut-butter-healthy", ("peanut butter", "peanut", "peanuts", "almond butter"),
     "Peanut butter is a decent everyday food: two tablespoons is about 190 calories with 7g of "
     "protein and 2g of fibre, and it keeps you full. The catch is the jar - buy one whose only "
     "ingredients are peanuts and salt, since the sweetened ones add sugar and palm oil - and "
     "use a level tablespoon rather than a spoon over the sink.",
     # "can i eat a peanut butter sandwich" is a question about peanut butter, and fencing the
     # word "sandwich" sent it to the nut-free list.
     ("jar", "recipe", "cookie", "cookies", "biscuit", "cake", "smell",
      "rancid", "stir")),
    ("berries-healthy", ("berries", "blueberries", "strawberries", "raspberries", "blackberries",
                         "cherries", "grapes"),
     "Berries are the best fruit for the calories - about 30 to 60 per 100g - and a 80g portion "
     "counts towards your five a day, with vitamin C, fibre and the red and purple pigments that "
     "give them their colour. Frozen ones are just as good and a lot cheaper out of season. A "
     "punnet is two or three portions, so tip half into a bowl rather than eating from the box.",
     ("smoothie", "jam", "crumble", "pie", "cake", "muffin", "muffins", "freeze", "frozen",
      "ripen", "ripe", "keep", "wine", "slug", "slugs", "birds", "net")),
    ("dark-chocolate-healthy", ("dark chocolate", "chocolate", "cocoa", "milk chocolate"),
     "Dark chocolate is the one to keep in the house if you want chocolate: 70 per cent cocoa is "
     "about 600 calories per 100g, so two squares is 120 or so, and it carries iron and magnesium "
     "with less sugar than milk chocolate. The heart-health claims come from cocoa flavanols and "
     "need far more than a square a day, so treat it as a nicer 120 calories, not a supplement.",
     ("recipe", "cake", "brownie", "brownies", "melt", "melted", "temper", "mould", "mold",
      "bloom", "gift", "easter", "hot chocolate", "store", "keep", "biscuit", "biscuits")),
    ("butter-healthy", ("butter", "ghee", "lard", "double cream"),
     "Butter is fine in small amounts and is not a health food: about 700 calories per 100g and "
     "half of it saturated fat, so a teaspoon on vegetables is 35 calories and a thick spread on "
     "two slices is nearer 200. The guideline is 20g of saturated fat a day for a woman and 30g "
     "for a man, which is why oil is the better everyday cooking fat and butter is the one for "
     "the taste.",
     # "can i eat a peanut butter sandwich" is the peanut butter row's line, and "butter" is the
     # last word of it: a two-word food name beats the noun it ends with.
     ("margarine", "spread", "than", "instead", "cook", "cooking", "fry", "frying", "bake",
      "baking", "soften", "melt", "melted", "goes off", "rancid", "churn", "beans",
      "peanut butter", "peanut", "peanuts", "nut butter", "almond butter", "cocoa butter",
      "shea butter", "bread and butter", "butterfly", "buttermilk")),
    ("mushrooms-healthy", ("mushrooms", "mushroom", "chestnut mushrooms", "portobello",
                           "shiitake"),
     "Mushrooms are about 20 calories per 100g, so a whole punnet is a portion for under 50: they "
     "bring 3g of protein, B vitamins including riboflavin and niacin, and selenium, plus the "
     "savoury taste that makes them useful in a meal that is meant to fill you up. The vitamin D "
     "some packs advertise comes from being treated with UV light - it is real, but a few "
     "minutes in the sun does the same job.",
     ("forage", "foraging", "pick", "picking", "poisonous", "grow", "growing", "kit", "slug",
      "slugs", "fly", "flies", "slimy", "recipe", "soup", "stuffed", "stew", "gravy")),
)
# A verdict is about whether a food is good to eat, and a food that is going off is another
# question: it is the rot, the mould and the date that decide it, and the row that answers those
# says so plainly ("a bruised one is fine: cut the bruise out and use it first"). "my apples are
# rotting on the tree" then "can i still eat the sound ones" reached the fruit verdict instead,
# because that row's key holds apples too, and the person got a card that opens on a banana's
# calories. A going-off word in the line, or in the line it leans on, stands every verdict down
# and leaves the question to the row that knows about rot.
# `stale` and `turned` are left out on purpose: "is stale bread bad for you" is a plain verdict
# and `stale` read it as spoilage, and `turned` is in "turned thirty" and "turned the oven down".
_GOING_OFF = re.compile(
    r"\b(?:rotting|rotten|rotted|going soft|gone soft|mouldy|moldy|mould|mold|gone off|"
    r"going off|out of date|past it|bruised|overripe|over-ripe|slimy|wilted|wilting|"
    r"sprouting|sprouted|furry|fuzzed|smells off|smelling off)\b")

# Some of those words name a state rather than spoilage: an overripe banana, a bruised apple and
# a sprouted potato are still ordinary food, and "are overripe bananas bad for you" asks about
# bananas, not about this lot. Only these words can be beaten by a verdict question; mould, rot,
# slime and a date are the food being spoiled whatever else the line says.
_A_STATE_NOT_SPOILAGE = re.compile(
    r"\b(?:overripe|over-ripe|bruised|going soft|gone soft|wilted|wilting|"
    r"sprouting|sprouted)\b")

# A verdict shape in the line being answered: "are overripe bananas good for you", "are sprouted
# beans healthy". It is the food the question is about.
_A_VERDICT_ASK = re.compile(
    r"\b(?:good for (?:you|me|us)|bad for (?:you|me)|healthy|unhealthy|fattening|"
    r"nutritious|healthier|healthiest|vitamins?|minerals?|calories|how many calories)\b")

# The borrow only counts when the line being answered is itself a question about eating or
# keeping. "my grapes are mouldy" then "can i still eat the sound ones" is one; "my grapes are
# mouldy" then "are grapes good for you" is not, and that plain verdict has to survive.
# `bad` on its own is not in here: "are grapes bad for you" is a plain verdict, and reading it as
# "is this lot bad" stood the berries card down for the sugar one.
_EDIBILITY_ASK = re.compile(
    r"\b(?:can i (?:still )?(?:eat|use|keep)|is it (?:ok|okay|safe|still)|is (?:it|that|this) bad|"
    r"safe to eat|still eat|still good|still fine|still use|good to eat|throw (?:it|them|this|that)|"
    r"throw (?:it |them )?(?:away|out)|bin it|keep it|keep them|how long|"
    r"what can i do with|use (?:it|them)|off|spoilt|spoiled)\b")


def _not_a_verdict_on_what_is_going_off(understood):
    """False when the food the line is about is going off: that is a keeping question.

    A guard says whether the row may answer, so this says no to exactly that case and yes to
    every other.
    """
    understood = understood or {}
    clean = str(understood.get("clean") or "").lower()
    if _GOING_OFF.search(clean):
        # "are overripe bananas good for you" is a verdict on bananas; "can i eat overripe
        # bananas" is about this lot. A state word yields to a verdict question, and to nothing
        # else.
        if _A_STATE_NOT_SPOILAGE.search(clean) and _A_VERDICT_ASK.search(clean) \
                and not _EDIBILITY_ASK.search(clean):
            return True
        return False
    leans = understood.get("leans_on")
    if isinstance(leans, dict):
        past = str(leans.get("text") or "").lower()
        if _GOING_OFF.search(past) and _EDIBILITY_ASK.search(clean):
            return False
    return True


for _food_id, _food_names, _food_line, _food_avoid in FOOD_HEALTH:
    ENTRIES.append(entry(
        _food_id, (_food_names, HEALTH_WORDS), _food_line,
        avoid=HEALTH_AVOID + _food_avoid, bias=1,
        guard=_not_a_verdict_on_what_is_going_off))


# How often, not whether: "how often can i eat tuna" was handed the fish-freshness card ("fish
# goes off faster than anything else") and "how much tuna is safe" the raw-fish card, so the one
# number the person asked for was in neither. It is a fact about tuna alone and it is the same
# number for everyone, so it is a row of its own, and its subject is the bare word: a two-word
# subject phrase clears the lookup on its own and took "is tinned tuna good for you" off the
# verdict it already had.
ENTRIES.append(entry(
    "tuna-a-week", (("tuna",), ("how often", "how many", "how much", "a week", "per week",
                                "every day", "every other day", "twice a week", "times a week",
                                "in a week", "safe", "limit", "too much", "maximum")),
    "Four medium tins a week, or two fresh tuna steaks: that is the limit for an adult, and it is "
    "about the mercury rather than the fat. Tuna is the one oily fish that does not count towards "
    "the two portions a week - canning strips most of the omega-3 - so it is protein, not a "
    "fish-oil dose. If you are pregnant or trying, keep to the same four tins; a child gets about "
    "half a tin as a portion.",
    # the freshness, the recipe and the animal are not the frequency question
    avoid=("smell", "went off", "off fish", "freshness", "defrost", "thaw", "recipe", "recipes",
           "sandwich", "salad", "pasta", "bake", "feed", "my cat", "my dog", "cat food",
           "dog food", "healthy", "good for you", "fattening", "nutritious", "calories",
           # and what is in it is the nutrition card's: "how much protein in a tin of tuna" is
           # about the 26g, not about how many tins a week
           "protein", "carb", "carbs", "carbohydrate", "fat", "fats", "iron", "vitamin",
           "vitamins", "minerals", "omega", "nutrition", "nutrients", "ingredients"),
    bias=2))

# "is olive oil good for you" was the shopping row ("Look for extra virgin and a harvest date"),
# which is a good answer to a question nobody asked, and "is olive oil fattening" the search
# hedge: the bottle has an owner and the diet has none. Oil is 9 calories a gram, so the honest
# verdict says both things at once - the best everyday fat, and a tablespoon of it is 120.
ENTRIES.append(entry("olive-oil-healthy",
    (("olive oil", "olive oils", "extra virgin", "extra virgin olive oil", "evoo"),
     # not "healthy": the oils-comparison card answers "is olive oil healthy" with the best
     # all-rounders (olive, rapeseed, and coconut held back) and the calorie rule, which is a
     # better answer than one oil's verdict. The shape with no owner was "good for you".
     ("good for you", "good for me", "good for us", "bad for you", "bad for me",
      "fattening", "make me fat", "calorie", "calories", "heart",
      "cholesterol", "any good", "worth eating", "nutritious", "superfood", "every day",
      "daily", "a day", "should i use", "better than")),
    "Olive oil is the best everyday fat you can keep in the kitchen: mostly monounsaturated, and "
    "the extra virgin sort brings the polyphenols that are the reason it is worth using raw. It "
    "is still 9 calories a gram, so a tablespoon is about 120 calories - the drizzle counts, and "
    "a recipe's 'glug' can be three of them. Pour it over a finished dish or bread for the taste, "
    "cook with a cheaper oil when the pan is hot, and read 'light' as light in taste, not in "
    "calories.",
    # the bottle to buy, a cake to bake, a pan to fry in and an oil that is not for eating are
    # other rows' lines
    avoid=HEALTH_AVOID + ("pick", "choose", "choosing", "buy", "buying", "best", "brand",
                          "bottle", "tin", "harvest", "supermarket", "shop", "price", "cheap",
                          "expensive", "label", "keep", "keeping", "store", "stored",
                          "fry", "fries", "frying", "fryer", "deep fat", "chip pan",
                          "roast potatoes", "cake", "cakes", "baking", "sponge", "muffin",
                          "car", "engine", "bike", "hair", "skin", "essential oil", "paint",
                          "lamp", "olive tree", "grow", "growing"),
    bias=1))

# --- the crispbread snack ---------------------------------------------------------------
# "is a rice cake good for you" was answered with the plain-rice calories card (the table read
# "rice" and stopped), "are rice cakes healthy" the same, and "can i eat rice cakes every day"
# was the search hedge. A rice cake is its own food: mostly air, about 30 calories each, and the
# question people actually have is whether that makes it a good snack.
ENTRIES.append(entry("rice-cakes",
    (("rice cake", "rice cakes", "rice cracker", "rice crackers", "corn cake", "corn cakes"),
     ("good", "healthy", "healthier", "unhealthy", "for you", "calorie", "calories", "eat",
      "eating", "every day", "daily", "snack", "snacks", "topping", "toppings", "put",
      "filling", "fill", "diet", "weight", "lose", "kids", "breakfast", "gluten")),
    "They are about 30 to 35 calories each, so a plain one is low fat and low salt - but it is "
    "nearly all air, and air does not fill anyone up for long. Treat it as a plate rather than "
    "a snack: cottage cheese, peanut butter, hummus, mashed avocado or a boiled egg on top turns "
    "two cakes into something that lasts to lunch. The flavoured and chocolate-coated ones are "
    "the ones to watch, because the salt or sugar on them is why people eat six. Most plain ones "
    "are gluten free, though the flavoured sort is worth reading the packet for.",
    # the plain rice rows, the puffed-rice treats and the rice cooker questions are others
    avoid=("risotto", "basmati", "brown rice", "white rice", "fried rice", "rice pudding",
           "krispie", "crispy", "krispies", "puffed rice", "rice cooker", "sushi", "paella",
           "how long", "how do i cook", "how do i make", "freeze", "frozen", "reheat",
           "leftover", "cupboard", "mould", "weevil", "pantry"),
    bias=2))

# --- the words on a label ----------------------------------------------------------------
# Four things a person reads in the small print before they know what they mean: a unit on a
# wine bottle, the glycaemic index on a diet page, "ultra-processed" in a headline and "food
# miles" on a menu. All four were a shrug on main. Each answer says what the thing is first,
# then the number or the rule that makes it useful.
ENTRIES.append(entry("unit-of-alcohol",
    (("unit of alcohol", "units of alcohol", "unit", "units", "alcohol unit", "alcohol units"),
     ("what is", "whats", "what's", "how many", "how much", "in a bottle", "in a glass",
      "wine", "beer", "lager", "gin", "vodka", "whisky", "prosecco", "pint", "bottle",
      "safe", "limit", "week", "day", "drink", "drinking", "count", "calculate", "work out")),
    "A unit is 10ml of pure alcohol, which is a small glass of wine at 12 per cent, half a pint "
    "of ordinary lager or a single 25ml spirit - so you work it out as strength times volume. The "
    "UK guideline is no more than 14 units a week for men and women, spread over three days or "
    "more, and a 13 per cent bottle of wine is about nine or ten units, so a bottle most nights "
    "is over it.",
    ask=("unit of alcohol", "units of alcohol", "alcohol unit", "units")))

ENTRIES.append(entry("glycaemic-index",
    (("glycaemic index", "glycemic index", "gi", "low gi", "high gi", "glycaemic load"),
     ("what is", "whats", "what's", "mean", "means", "low", "high", "diet", "diabetes",
      "blood sugar", "lose weight", "weight", "food", "foods", "chart", "list", "use",
      "worth", "matter", "better")),
    "The glycaemic index rates a food by how fast its carbohydrate raises blood sugar compared "
    "with pure glucose, from 0 to 100: a banana is about 50, white bread about 75, porridge oats "
    "about 55, lentils about 30. Low is 55 or under, and the trick is the company the "
    "carbohydrate keeps - fat, "
    "protein and fibre all slow it down, which is why a boiled potato beats a baked one and "
    "lentils barely move the number.",
    ask=("glycaemic index", "glycemic index", "low gi", "high gi", "glycaemic load")))

ENTRIES.append(entry("ultra-processed-food",
    (("ultra processed", "ultra-processed", "ultraprocessed", "upf", "processed food",
      "processed foods", "ultra processed food", "ultra processed foods"),
     ("what is", "whats", "what's", "mean", "means", "bad", "bad for you", "avoid", "cut out",
      "healthy", "unhealthy", "list", "food", "foods", "eat", "diet", "how much", "ok",
      "better", "cook", "homemade", "why")),
    "Ultra-processed food is the industrial end of the scale: things made mostly from extracts "
    "and additives - emulsifiers, colourings, flavourings, sweeteners - that you would not cook "
    "with at home, like fizzy drinks, crisps, sausages, ready meals and most breakfast cereal. "
    "The evidence is that people eat more of it and put on weight, but the class is broad enough "
    "that hummus and wholemeal bread land in it, so judge by the ingredient list rather than the "
    "label. Cooking from plain ingredients is the practical answer.",
    ask=("ultra processed", "ultra-processed", "upf", "processed food", "processed foods")))

ENTRIES.append(entry("food-miles",
    (("food miles", "food mile", "air miles", "food miles of"),
     ("what is", "whats", "what's", "mean", "means", "carbon", "climate", "better", "worse",
      "local", "buy local", "matter", "important", "reduce", "cut", "vegetarian", "meat",
      "imported", "seasonal", "kite")),
    "Food miles are the distance food travels from where it is grown to your plate, and they "
    "matter less than most people think: transport is around a tenth of the emissions in a "
    "typical shopping basket, while what the food is and how it was made is most of the rest. "
    "Air-freighted green beans and out-of-season asparagus are the exceptions worth avoiding; "
    "eating less meat and wasting less food cuts far more than buying only local.",
    ask=("food miles", "food mile", "air miles")))


# The takeaway words this row keys are also the takeaway card's own subject, so the card stands
# down for them unless the line says "junk" too - see the guard on the entry below.
_NAMED_TAKEAWAY = re.compile(r"\b(?:takeaway|takeaways|take out|takeout|fast food)\b")


def _not_a_named_takeaway(understood):
    """False for a line whose only fast food is a takeaway, which the takeaway card answers."""
    clean = str((understood or {}).get("clean") or "").lower()
    if not _NAMED_TAKEAWAY.search(clean):
        return True
    return bool(re.search(r"\bjunk\b", clean))


# "How do i stop eating junk food" was the "I'd rather not guess" hedge: the sugar row keys
# sugar, sweets and biscuits, and crisps, chips and takeaways are none of those words. Same
# question, different food, so it gets its own row rather than a pile of words in the sugar one.
ENTRIES.append(entry(
    "junk-food",
    (("junk food", "junk", "fast food", "takeaway", "takeaways", "take out", "crisps", "chips",
      "sweets", "chocolate", "cakes", "biscuits", "fizzy drinks", "processed food", "ready meals"),
     # The asking words are the whole second signal. A bare "eat" or "eating" made the card fire
     # on a report ("i eat takeaway three times a week"), which is a person telling the chat about
     # their week, not asking how to change it - the acknowledgement is the right reply to that.
     ("stop", "stop eating", "cut", "cutting", "cut down", "reduce", "reducing", "give up",
      "quit", "less", "too much", "every day", "all the time", "habit")),
    ("Swap rather than ban, because the ban is what makes the 9pm trip to the shop happen: keep "
     "something you actually like at home that takes two minutes - frozen chips in the oven, "
     "popcorn, yoghurt with fruit, toast and peanut butter. Eat protein and fibre at lunch, "
     "because a day of white carbs is what makes the evening raid feel compulsory, and do not "
     "shop hungry: the aisle is the thing that decides it, not willpower. One takeaway a week, "
     "on a day you choose, holds better than none at all."),
    # a cake in a tin and chips in a fryer are cooking questions, and this answer is about habit
    # "how do i stop junk email" was answered with this card, because "junk" and "stop" were the
    # whole of what it keys and the posting list has its own answer: the junk in a line about
    # mail, an inbox or spam is not food.
    avoid=("email", "emails", "inbox", "spam", "mail", "mails", "letterbox", "letter",
           "letters", "post", "postman", "texts", "text message", "messages",
           "recipe", "recipes", "bake", "baking", "oven", "fryer", "frying", "air fryer",
           "how do i cook", "how long", "temperature", "homemade", "make", "making",
           "dog", "cat", "puppy", "child", "kids", "toddler", "baby",
           # one named food is the sugar row's or the snacking row's question, and both answers
           # are better than this one: this row is for the general "junk food" ask, so the
           # named drink and snack are fenced back to their own cards.
           "drink", "drinking", "fizzy", "coke", "cola", "juice", "squash", "soda",
           "energy drink", "alcohol", "beer", "wine", "crisps", "chocolate", "sweets",
           "biscuits", "cake", "cakes",
           # "junk" is a money word too: "how do i stop spending money on junk" is the 24-hour
           # rule and the saved card, and this card about the 9pm shop is an answer to a
           # different question. The spending words fence it back to money's own row.
           "spend", "spends", "spending", "spent", "money", "buy", "buying", "bought", "pay",
           "paying", "paid", "budget", "waste", "wasting", "save", "saving", "£", "£s",
           "cost", "costs", "cheaper", "afford"),
    # One named fast food is the takeaway card's question, and its answer - one planned night a
    # week with the money set aside - is better than this one: "how do i stop eating takeaways"
    # was answered with the general swap card. A line that says "junk food" as well is this
    # card's own question, so the guard reads the whole line rather than the word.
    guard=_not_a_named_takeaway,
    bias=1))
# --- the first meal after a fast --------------------------------------------------------
# "how do i break my fast" was the search hedge and "how do i end a fast" was worse: the
# study module's essay-conclusion row keys "ending", which folds to "end", so the first meal
# after a fast was answered with "say what it adds up to, not what you have already said", a
# paragraph of advice about a last paragraph. The fence went on in `study.py`; this is the
# answer the line was owed. It keys the two ways people say it - breaking a fast and ending
# one - and stands aside for every other thing that breaks.
ENTRIES.append(entry("breaking-a-fast",
    (("break a fast", "break my fast", "break the fast", "breaking a fast", "breaking my fast",
      "broke my fast", "end a fast", "end my fast", "end the fast", "ending a fast",
      "finish a fast", "finished my fast", "come off a fast", "coming off a fast",
      "first meal after", "after a fast", "after fasting", "after my fast", "out of a fast"),
     ("how", "what", "should", "eat", "best", "safely", "properly", "start", "i", "my",
      "do", "can", "when")),
    "Start small and gentle: a piece of fruit, a yoghurt or a slice of toast, then wait twenty "
    "minutes before a proper meal. Fat, sugar and coffee on an empty stomach are what make people "
    "feel sick, shaky and headachy, so go easy on those and have a glass of water first. If you "
    "have gone more than a day without eating, break it over an hour or two rather than in one "
    "sitting, and ask a GP first if you take diabetes medication.",
    # a broken bone, a broken phone, a broken habit and a break in a shift are all "break"
    avoid=("break my arm", "break a leg", "broken bone", "break a bone", "break up", "breaking up",
           "broke up", "break the law", "break in", "breaking news", "break the ice",
           "break a window", "break a habit", "bad habit", "break the news", "lunch break",
           "tea break", "coffee break", "break even", "break down", "broken down", "fast car",
           "fastest", "how fast", "speed"),
    bias=1))
