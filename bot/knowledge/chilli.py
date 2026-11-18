"""Chillies as a vegetable: what to do with a glut, how hot the thing is, and what stands in.

The answers lane owns this domain. A chilli is a dish as well as a vegetable, and the dish
answers every way of asking for the recipe, so these are the questions the recipe is the wrong
answer to: keeping a box of them, freezing them, drying them, chopping them, how hot one is and
what to use when there are none. Each row is keyed by the chilli names plus the words that name
the job or the property, so "how hot is a jalapeno" and "how spicy is a chilli" reach the same
answer without either of them naming a chilli variety.
"""
import re

from . import lookup
from . import lookup
from .lookup import entry, said_in_this_line

ANSWERS = ("cooking", "food-and-drink")

# A dish made with chillies is the recipe's question, not the vegetable's, and it is named in
# one of these words rather than by the chilli. Every row below carries them: "can i freeze
# chilli con carne" was answered by the box-in-the-fridge-drawer row.
DISH = ("con carne", "con carni", "bolognese", "chilli beef", "stew", "recipe", "dish",
        "saucepan", "in a curry")
# A pot of it is the other thing again: "how long is a pot of chilli good for" was answered by the
# box-in-the-drawer card, and "can i freeze leftover chilli" with "freeze them whole in a bag and
# slice them still frozen", which is nonsense for a stew. These words name the cooked dish, so
# the cooked-dish row below answers instead. "leftover" is not here: it is a key word above.
COOKED = (" pot ", "pot of", "a pot", "batch", "cooked", "already made", "made it")
# A follow-up says "it", and the chilli it leans on can be either the vegetable or the dish: after
# "im making a chilli tonight" and "how long does it need", "can i freeze it" was answered "Freeze
# them whole in a bag and slice them still frozen", which is nonsense for a stew. The reading that
# reaches these rows carries the dish word from an earlier line, so the ingredient rows have to see
# the word in the line itself: anything that only refers back is the dish's keeping question, which
# the cooked-dish row answers.
_CHILLI_IN_THE_LINE = ("chilli", "chillies", "chile", "chiles", "jalapeno", "jalapenos",
                       "habanero", "scotch bonnet", "birds eye")


def _the_vegetables_or_the_pot(memory, understood, vegetable_answer, pot_answer):
    """The vegetable's answer, or the cooked dish's when this line is only pointing at one.

    "im making a chilli tonight", "how long does it need", and then "can i freeze it" was answered
    "Freeze them whole in a bag and slice them still frozen", which is a bag of peppers, not a pot
    of stew. The last line names nothing, so the thing being asked about is the dish the talk is
    on, and the answer for a cooked dish is one this base already keeps: the dish's own plan
    sentence, or the freezing table in `bot/knowledge/cooking_entries.py`. Both are imported
    rather than said again here, and a chat with no dish in it still gets the vegetable's answer.
    """
    if _a_chilli_in_this_line(memory, understood):
        return vegetable_answer
    if isinstance(memory, dict) and _a_dish_in_the_chat(memory, understood):
        pot = pot_answer(memory, understood)
        if isinstance(pot, str) and pot.strip():
            return pot
    return vegetable_answer


def _a_dish_in_the_chat(memory, understood):
    """True when the conversation is on a dish, so "it" is a pot and not a bag of peppers."""
    from . import dishes  # imported here: the dish tables build on this module's neighbours
    try:
        return bool(dishes.dish_for(memory, understood))
    except Exception:  # noqa: BLE001 - the vegetable's own answer is the safe one
        return False


def _the_plans_keeping_answer(memory, understood):
    """The dish's own keeping sentence, for a pot the conversation is already on."""
    from . import dishes  # imported here: the dish tables build on this module's neighbours
    return dishes.follow_up(memory, understood)


def _the_cooked_dish_freezing_answer(memory, understood):
    """The freezing answer for a cooked dish, from the table that keeps them all."""
    from .cooking_entries import freeze_cooked_answer  # imported here: a neighbour's table
    return freeze_cooked_answer(memory, understood)


def _a_chilli_in_this_line(memory, understood):
    """True when this line names the vegetable rather than leaning on a dish said earlier."""
    text = said_in_this_line(understood, memory).lower()
    return any(word in text for word in _CHILLI_IN_THE_LINE)


# The verbs that name a pan. A chilli in a pan is the dish, and the keeping row is about a box in
# the drawer: "how long should i simmer a chilli for" got the box.
HEAT_WORDS = ("simmer", "simmering", "simmered", "cook", "cooking", "boil", "boiling", "fry",
              "frying", "fried", "roast", "roasting", "roasted", "bake", "baking", "baked",
              "oven", "hob", "pan", "minutes", "stir fry", "grill", "steam")


# A dish on a takeaway menu is asked about by its heat far more often than about how to make it:
# "how spicy is a korma", "how hot is a jalfrezi", "which curry is mildest". The kitchens have an
# order they all roughly keep, so it is one table read weakest first, and the answer is the dish's
# place on it. "hot" is a weather word to the forecast card, which is what "how hot is a jalfrezi"
# got, so the row carries a point of bias and both answers name a dish.
CURRY_HEAT = (
    (("korma", "pasanda", "butter chicken", "makhani"),
     "mildest on the menu, creamy and with no chilli heat at all"),
    (("tikka masala", "tikka", "masala"),
     "mild, a tomato and cream sauce with a little warmth"),
    (("rogan josh", "dhansak", "balti"),
     "medium, warming rather than burning"),
    (("madras",),
     "the first properly hot one on most menus, hot without being punishing"),
    (("jalfrezi",),
     "hot, with green chillies and peppers left in"),
    (("vindaloo",),
     "very hot, and hotter in some kitchens than others"),
    (("phal", "naga", "tindaloo"),
     "the hottest thing on the menu, and past the point where most people taste anything else"),
)

# What the line calls the dish, so the reply can name it back: a person who typed "jalfrezi" is
# asking about a jalfrezi, and "the dish" reads as a shrug.
CURRY_NAMES = {name: name for names, _ in CURRY_HEAT for name in names}

# The order as one sentence, for the line that asks which is mildest rather than about one dish.
CURRY_ORDER_LINE = "korma, pasanda, butter chicken, tikka masala, rogan josh, balti, dhansak, madras, jalfrezi, vindaloo, phaal"

_HEAT_WORDS = ("spicy", "spice", "spicier", "hot", "hotter", "hottest", "mild", "milder",
               "mildest", "heat", "strength", "how strong", "scoville", "burn", "burning",
               "too spicy", "too hot", "which is mildest", "least spicy")


# A dish in front of the person that is too hot to eat is the rescue question, not the menu's
# scale: "my curry is way too spicy, what can i do" was answered with the korma-to-phal order,
# when cooking.py's chilli-heat card has the answer and its own words ("too hot", "too spicy")
# score the same here. A fault in the food is not a place on the menu, so the fault stands this
# row down and the rescue card answers. The menu's own questions - "how hot is a jalfrezi",
# "which curry is mildest", "how spicy is a korma" - name no fault and keep their answer.
_A_FAULT_IN_THE_DISH = (
    "too spicy", "too hot to eat", "too hot for me", "too hot for the kids", "way too hot",
    "way too spicy", "far too spicy", "far too hot", "cool it down", "cool the heat",
    "cool this down", "make it milder", "make it less spicy", "less spicy", "not so spicy",
    "too much chilli", "too much chili", "blow your head off", "burning my mouth",
)


def _curry_heat(memory, understood):
    """The dish's place on the menu's scale, or the whole order when the line names no dish."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)
    flat = " " + str(understood.get("clean") or understood.get("text") or "").lower() + " "
    flat = re.sub(r"[^a-z0-9' ]+", " ", flat)
    if any(phrase in flat for phrase in _A_FAULT_IN_THE_DISH):
        return None
    for index, (names, place) in enumerate(CURRY_HEAT):
        for name in names:
            if name in said:
                return ("A %s is %s. Mildest to hottest the usual menu runs %s, so ask for it mild "
                        "and the kitchen leaves the chilli out - and if you want heat with flavour, "
                        "step one up the list rather than two."
                        % (name, place, CURRY_ORDER_LINE))
    return ("Mildest to hottest the usual takeaway menu runs %s. A korma or pasanda has no chilli "
            "heat at all, a tikka masala is mild, and a jalfrezi and up are the hot end; ask for "
            "any of them mild and the kitchen makes it without the chilli."
            % CURRY_ORDER_LINE)


# The bean word in the line can be the thing somebody already has rather than the thing they
# are asking about: "got mince and kidney beans but no chopped tomatoes" is a question about the
# tomatoes, and it was answered with the beans card. A shortage names the subject of the line, so
# this stands the beans row down unless what is missing is itself a bean.
_SHORTAGE = re.compile(
    r"\b(?:but no|and no|no|without|short of|missing|havent got|haven't got|not got"
    r"|ran out of|run out of)\s+((?:[a-z']+\s*){0,3})")
_BEAN_STEMS = ("bean", "kidney", "pinto", "cannelli", "haricot", "baked", "black")


def _short_of_something_else(understood):
    """False when the line says what it has run out of and that thing is not a bean."""
    # the reading's words are a list, so they go through the one helper that joins them: taken as
    # the fallback for a string they put a list into `finditer` (see lookup.said_text)
    for match in _SHORTAGE.finditer(lookup.said_text(understood)):
        near = match.group(1).split()[:3]
        if not any(word.startswith(_BEAN_STEMS) for word in near):
            return False
    return True


# What a pot of it keeps, and the one stand-down the keeping row cannot say in a word list.
# "how long" is a keeping word in this file, and a pan of it can be either question: on the hob it
# is the cooking time, in the fridge it is the keeping time. A bare word cannot tell those apart -
# `pan` in the avoid list stood the row down for the keeping question and the boiler answered it -
# and a bare `cook` in the avoid list is loose-matched, so it eats its own past participle and
# takes "how long does cooked chilli keep" with it. The line's verb and the cues beside it are
# what tell them apart, so the reply reads its own line: a cook verb with nothing that keeps is
# the cooking question and this row returns nothing, which hands the line to the cook-time card.
A_COOK_CLOCK_VERB = re.compile(r"\b(?:take|takes|taking|simmer|simmering|boil|boiling|fry|frying|"
                               r"bake|baking|roast|roasting|cook|cooks|cooking|poach|steam|grill)\b")
A_KEEPING_CUE = re.compile(r"\b(?:keep|keeps|keeping|kept|last|lasts|lasting|store|stored|fridge|"
                           r"freezer|freeze|frozen|good for|leftover|left over|reheat|reheats|"
                           r"out of date|use by|still good|safe to eat|night|tomorrow)\b")
A_POT_OF_CHILLI_KEEPS = (
    "A pot of chilli keeps 3 days in the fridge, in a sealed box, once it has cooled within "
    "two hours of cooking; it freezes for 3 months and it is better the next day anyway. "
    "Reheat it once, until it is piping hot right through, and don't leave it out on the "
    "hob overnight.")


def _the_pot_keeps(memory, understood):
    """The pot's keeping clock, or nothing when the line asks how long a pan takes to cook."""
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if A_COOK_CLOCK_VERB.search(said) and not A_KEEPING_CUE.search(said):
        return ""
    return A_POT_OF_CHILLI_KEEPS


ENTRIES = (
    # "how do i use up chillies", "how do i store chillies" and "how long do chillies last" were
    # answered by the chilli con carne method, and "how do i keep chillies fresh" by a keeping row
    # about something else: a dish and a vegetable are one word.
    entry("chilli-keep",
          (("chilli", "chillies", "chilli pepper", "jalapeno", "jalapenos", "habanero",
            "scotch bonnet"),
           ("use up", "keep", "keeping", "store", "storage", "how long", "last", "left over",
            "leftover", "glut", "plenty of")),
          lambda memory, understood: _the_vegetables_or_the_pot(
              memory, understood,
              "Loose in the fridge drawer they keep a week or two, and longer in a paper bag than "
              "in plastic: the bag holds the moisture that turns them soft. A glut is better "
              "frozen or dried than left to go wrinkly - both keep the heat - and a handful also "
              "becomes chilli oil, which is the fastest way to use up twenty at once.",
              _the_plans_keeping_answer),
          # "my chilli is too dry" is a fault in the dish, not a question about keeping them:
          # the state word is what tells the two apart. Freezing and drying have their own rows,
          # because each is asked on its own and the first sentence has to be about that.
          # A pan of them is the cooking question, not the drawer: "how long should i simmer a
          # chilli for" was answered with "loose in the fridge drawer they keep a week or two",
          # because "how long" is a keeping word and the row had no heat verb to stand it down.
          avoid=DISH + HEAT_WORDS + ("too spicy", "too hot", "less spicy", "too dry", "is dry",
                                     "tastes dry",
                        "came out dry", "too wet", "plant", "grow", "growing", "sow", "seedling",
                        "powder", "flakes", "paste", "freeze", "frozen", "drying", "dry them",
                        "instead of", "substitute", "swap", "replace", "oil",
                        # "take" rather than "how long does it take": the follow-up is written out
                        # with its subject first ("how long does the chilli take"), so the phrase
                        # the person typed no longer appears by the time the row is asked. A
                        # keeping question says "last"; a duration of doing says "take".
                        # "and how long does it take" after "im making chilli tonight" was told
                        # "loose in the fridge drawer they keep a week or two".
                        "take", "takes", "taking") + COOKED,
          bias=1),
    # A pot of it is a cooked dish with its own keeping answer: "how long is a pot of chilli good
    # for" reached the box-in-the-drawer card, and with that card stood down it reached the
    # recipe's "about 40 minutes start to finish". The dish words are asked for, so a line naming
    # chillies on their own still gets the vegetable.
    entry("chilli-pot-keep",
          (("chilli", "chillies", "chilli con carne", "chilli beef"),
           ("keep", "keeps", "keeping", "good for", "last", "lasts", "how long", "store",
            "fridge", "freezer", "freeze", "leftover", "left over")),
          _the_pot_keeps,
          ask=(" pot ", "pot of", "a pot", "batch", "cooked", "made", "leftover", "left over",
               "con carne", " pan ", "pan of", "a pan"),
          # "chilli con carne" has its own keeping row, which says the same thing in one line.
          # A cooking time is not a keeping time, and the dish is where that matters most:
          # "how long does it take to cook a chilli" was told "A pot of chilli keeps 3 days in
          # the fridge". The row keeps "how long" as a key, which a duration also says, so the
          # cooking words have to stand it down - the same list the vegetable's keeping row uses.
          # The pan is not one of them. `pan` itself stood this row down for "how long does a pan
          # of chilli keep", which is the keeping question asked of a pan, and the boiler's
          # appliance row answered it ("Turn the water off at the isolation valve"). A pan words
          # the dish, not the hob: the hob, the oven and the heat verbs are in the list and the
          # pan is in the ask, so the reply decides on the verb the line actually used.
          avoid=("plant", "grow", "growing", "seedling", "sow", "powder", "flakes", "paste",
                 "how hot", "too spicy", "too dry", "instead of", "con carne", "con carni",
                 "take", "takes", "taking", "simmer", "simmering", "boil", "boiling", "fry",
                 "frying", "oven", "hob", "how long to cook", "cooking time"),
          # cooking.py's cooked-mince row carries "chilli" too and asks for "leftover", so a
          # leftover chilli keeps the mince answer, which is the same clock and the same box.
          bias=1),
    # the dish's heat is its own question, and it is the one a menu line asks
    entry("curry-heat",
          (("korma", "pasanda", "butter chicken", "tikka masala", "tikka", "rogan josh", "dhansak",
            "balti", "madras", "jalfrezi", "vindaloo", "phal", "naga", "tindaloo", "curry",
            "curries"),
           _HEAT_WORDS),
          _curry_heat,
          # the recipe, the calories, the drink and the heartburn have their own cards
          avoid=("recipe", "how do i make", "how to make", "calories", "sugar", "healthy",
                 "wine", "beer", "drink", "side", "sides", "goes with", "naan", "rice",
                 "hangover", "heartburn", "reflux", "indigestion", "stomach", "baby", "toddler",
                 "child", "kids", "plant", "grow", "seedling", "powder", "flakes", "paste"),
          # "how hot is a jalfrezi" was answered with the week's weather
          bias=1),
    # A curry is finished with something cooling, and the question "do i need to add yoghurt" was
    # answered by nothing at all while the same line written with "too spicy" in it reached the
    # heat card. The dish and the thing stirred into it are the two halves, so the row reads both
    # and answers the finishing (when to add it, how not to split it) rather than the heat scale.
    entry("curry-yoghurt",
          (("curry", "curries", "dal", "daal", "dhal", "tikka", "masala", "korma",
            "rogan josh", "balti"),
           ("yoghurt", "yogurt", "dahi", "cream", "coconut milk", "raita", "creme fraiche",
            "crème fraîche", "soured cream", "sour cream")),
          "Yes - a spoonful of yoghurt stirred in at the end is the usual finish: it cools the "
          "heat and rounds off a sharp or bitter edge. Take the pan off the heat first and stir "
          "the yoghurt into a spoonful of the sauce in a cup before it goes back in, so it does "
          "not split; full-fat or Greek yoghurt splits less than low-fat, and a splash of cream "
          "or coconut milk does the same job.",
          # a pot that has split, a pot that is too runny and a diet question are all other rows
          avoid=("split", "splits", "splitting", "curdled", "curdle", "curdling", "grainy",
                 "seized", "too thick", "too thin", "watery", "runny", "calories", "healthy",
                 "how many", "protein", "freeze", "frozen", "mouldy", "out of date", "gone off"),
          bias=1),
    # "can i freeze fresh chillies" was answered by the storage row, whose second sentence is
    # about freezing: the answer has to start with the thing that was asked.
    entry("chilli-freeze",
          (("chilli", "chillies", "chilli pepper", "jalapeno", "jalapenos", "habanero",
            "scotch bonnet"),
           ("freeze", "frozen", "freezing", "bag up", "ice cube")),
          lambda memory, understood: _the_vegetables_or_the_pot(
              memory, understood,
              "Freeze them whole in a bag and slice them still frozen: they go soft, so they are "
              "for cooking rather than for a salad, but the heat survives a few months. Chopped "
              "into an ice-cube tray with a little oil is the other way, one cube per curry, and "
              "there is no need to blanch them first.",
              _the_cooked_dish_freezing_answer),
          # cooking.py's freeze-cooked row carries the bare word "chilli" too, and so does the
          # garden's frost row through "freezing", so the nudge is what settles this against
          # them. A pot that is already made is a different question with its own row - "can i
          # freeze leftover chilli" lost its cooked-mince answer to a bigger nudge - so leftover
          # is fenced here rather than weighed.
          avoid=DISH + ("too spicy", "too hot", "too dry", "is dry", "plant", "grow", "growing",
                        "sow", "not working", "broken", "instead of", "oil",
                        "leftover", "left over", "cooked", "already made", "batch")
          + COOKED,
          bias=1),
    # the same for drying: "how do i dry chillies" was answered by the fridge drawer.
    entry("chilli-dry",
          (("chilli", "chillies", "chilli pepper", "jalapeno", "jalapenos", "habanero",
            "scotch bonnet"),
           ("dry", "dried", "drying", "dehydrate", "dehydrator", "dry them out")),
          "Thread them on cotton and hang the string by a sunny window until they are leathery "
          "and rattle when you shake one, which takes two to three weeks in a warm room, or split "
          "them and dry them in a low oven at 60C with the door ajar for six to eight hours. Dry "
          "them whole and they keep a year in a jar; grind them for flakes once they are crisp.",
          avoid=DISH + ("too spicy", "too hot", "too dry", "is dry", "tastes dry", "came out dry",
                        "too wet", "plant", "grow", "growing", "sow", "tumble dryer",
                        "washing", "instead of", "oil",
                        # "the chilli boiled dry" is a pan on the hob, not a chilli to hang:
                        # the pot-dry words are the dish's rescue, and a chilli that is being
                        # dried on a string is never boiled
                        "boiled dry", "boils dry", "boil dry", "boiling dry", "boiled away",
                        "boils away", "caught on the bottom", "stuck to the bottom",
                        "saucepan", "in the pan", "in the pot"),
          # the "too dry" fault row and the dry-dish advice score on "dry" as readily as this
          # one does, and the chilli names say which is meant
          bias=1),
    # "how hot is a jalapeno" was answered by the weather fallback and "how do i chop a chilli"
    # by the chilli con carne method. The seed question has its own row in cooking.py; this one is
    # the vegetable's heat and knife work, and the variety names are what tell it from a dish.
    entry("chilli-vegetable",
          (("chilli", "chillies", "chilli pepper", "jalapeno", "jalapenos", "habanero",
            "scotch bonnet", "birds eye", "bird's eye"),
           ("chop", "chopped", "slice", "prepare", "prep", "how hot", "hot", "heat", "spicy",
            "strength", "how strong")),
          "Heat is in the variety before it is in the size: a jalapeno is mild enough to eat raw, "
          "a bird's eye or a scotch bonnet will heat a whole curry, and the same kind varies from "
          "one to the next, so taste a sliver before you commit to two. Chop them small and add "
          "them early for a rounded heat, or late and sliced for a sharp one; the white pith and "
          "the seeds carry most of it, so scraping them out takes the edge off without making it "
          "mild. Wash your hands straight after and keep them off your eyes, or wear gloves for "
          "the very hot ones: the oil stays on skin for hours and soap barely shifts it.",
          # the seed question, the fault, the products and the substitutions have their own rows
          avoid=DISH + ("deseed", "de-seed", "seed", "seeds", "pith", "too spicy", "too hot",
                        "less spicy", "mild", "milder", "cool down", "cool it", "flakes",
                        "powder", "paste", "plant", "grow", "growing", "sow", "seedling")),
    # The oil that burns a mouth burns an eye, and "rubbed my eye after chopping chillies" was
    # answered by the variety card (it owns "chop") while "chilli in my eye" got an echo. The
    # subject is the chilli and the job is the eye, so this row keys on both and the eye words are
    # deliberately narrow: the variety row's advice to keep them off your eyes is not the answer
    # to having got some in one.
    entry("chilli-eye",
          (("chilli", "chillies", "chili", "chillis", "jalapeno", "jalapenos", "habanero",
            "scotch bonnet", "chilli oil", "chilli juice"),
           ("in my eye", "in the eye", "in my eyes", "my eye", "my eyes", "eyeball",
            "eye is", "eyes are", "eye hurts", "eyes hurt", "stinging", "stings", "rubbed my eye",
            "rubbing my eye",
            # somebody else's eye: "my baby got chilli in her eye" is the same injury as the
            # person's own, and "her eye" is how it is said.
            "in her eye", "in his eye", "in their eye", "his eye", "her eye", "their eye")),
          "Don't rub it: rinse the eye with milk if you have some, then clean, cool water or "
          "saline for ten to fifteen minutes with the lid held open, and blink it through. The "
          "burn fades over an hour or so and the redness can last a day. Ring 111 or go to an eye "
          "casualty the same day if the pain is getting worse rather than better, if your sight is "
          "blurred, or if you wear a contact lens - take it out first. Wash your hands and the "
          "knife before you touch your face again, because the oil sits on skin for hours and soap "
          "barely shifts it.",
          avoid=DISH),

    # "what can i use instead of chilli flakes" was answered by the dandruff card, because
    # "flakes" belongs to a scalp, and "i have no chillies" got nowhere at all.
    entry("chilli-substitute",
          (("chilli", "chillies", "chilli flakes", "chilli powder", "chilli sauce", "chili",
            "chilli paste", "cayenne", "paprika", "gochujang", "sriracha"),
           ("instead of", "substitute", "substitution", "swap", "replace", "alternative",
            "no chillies", "run out", "ran out", "out of", "stand in", "same as")),
          "Paprika plus a pinch of cayenne is the closest thing to chilli powder: about four parts "
          "paprika to one of cayenne, and smoked paprika if you want the depth back. For flakes, a "
          "teaspoon is roughly one fresh chilli, so half a teaspoon of cayenne or a chopped red "
          "pepper does the job, and a spoon of sriracha, gochujang or hot sauce adds heat and a "
          "little sweetness. Without any of those, black pepper and a little ginger give the bite "
          "even though the flavour is different.",
          avoid=DISH + ("deseed", "de-seed", "pith", "how hot", "how spicy", "too spicy",
                        "too hot", "plant", "grow", "growing", "sow", "seedling", "store",
                        "freeze", "keep", "dry them", "drying", "make chilli oil")),
    # "how do i make chilli oil" got "That is everything I have on that one", and
    # "how do i store chilli oil" got the box-in-the-fridge-drawer row.
    entry("chilli-oil",
          # the oil has to be named: "chilli" plus "how do i" is every chilli question there is
          (("chilli oil", "chili oil"),
           ("make", "recipe", "how do i", "store", "keep", "last", "shelf life", "infuse",
            "chillies in", "with dried")),
          "Warm 200ml of a plain oil with four sliced chillies and a crushed garlic clove over the "
          "lowest heat for five minutes - it should barely bubble, because burnt chilli turns "
          "bitter - then let it cool completely before you bottle it. Keep it in the fridge and use "
          "it within a fortnight, since fresh garlic and fresh chilli in oil will grow things at "
          "room temperature; dried flakes in oil keep far longer, up to three months cold.",
          # "make" and "how do i" are on every line, so the chilli oil phrase is what decides it
          # and the vegetable questions are kept out
          avoid=DISH + ("chop", "deseed", "seed", "pith", "how hot", "how spicy", "too spicy",
                        "less spicy", "store chillies", "freeze", "instead of", "substitute",
                        "plant", "grow", "sow")),
    # Whether a chilli has beans in it is the one question about the dish that the recipe is the
    # wrong answer to: "should i add beans to my chilli" was handed the whole method from "fry
    # 500g of mince", "do i need beans in chilli" reached the green-vegetables row (a bean on a
    # plate, not a bean in a pot) and "what beans for chilli" got nothing at all. A person asking
    # this has the pot on already, so the answer is which beans, how many and what to do without.
    entry("chilli-beans",
          (("chilli", "chili", "chilli con carne", "chili con carne", "chillies"),
           ("beans", "bean", "kidney beans", "kidney bean", "black beans", "pinto beans",
            "cannellini", "baked beans", "haricot", "tin of beans", "tinned beans")),
          "Beans are optional, and it is a regional thing rather than a rule: Tex-Mex chilli "
          "usually has none, and most home versions have kidney beans. If you want them, a 400g "
          "tin of kidney or black beans, drained and rinsed, goes in with the tomatoes so it "
          "simmers the last 30 minutes - about one tin to 500g of mince, and no longer, because "
          "they go floury. Without them, keep the mince at 500g and add an extra onion or a "
          "handful of red lentils with the stock so it does not go dry and sharp. Baked beans are "
          "the sweet one: they work, but they want less sugar and a splash of vinegar in the pot.",
          # a bean on a plate, a bean to grow and a bean to soak are three other answers, and the
          # recipe is a fourth: the dish words stand this row down when the line wants the method
          ask=("chilli", "chili"),
          avoid=("how do i make", "how do you make", "recipe", "green beans", "runner beans",
                 "broad beans", "soak", "soaking", "dried beans", "grow", "plant", "sow",
                 "beans on toast", "side", "salad"),
          # a line that is short of something else is a question about that thing
          guard=_short_of_something_else,
          # "how does chilli get its heat" and "how many chillies for four" are the spice row,
          # and it is reached from the dish word plus an amount word. A line that says beans as
          # well is the pot, so this row has to outrank it: "how many beans in chilli" was
          # answered with how much chilli to use for four people.
          bias=6),
)

