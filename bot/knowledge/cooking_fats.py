"""Which fat goes in the pan: butter, oil, or one then the other.

"Butter or oil for onions" is a cooking question, and the bot answered it from the fridge: the
`butter-margarine` row in `nutrition.py` keys `butter` with `or` and is about a scraping on toast,
so every "butter or oil" line got the spread-versus-butter lesson. The other half of the fault was
worse - "should i cook onions in butter or oil" got two recipes, shortbread and onion soup, because
the line names two foods and two ingredients and the cooking domain answered with one dish each.

So the choice of fat is its own question with its own answer, and the answer is a fact about heat:
butter burns, oil does not, and which one is better depends on how hot the pan is. A line that is
not about a pan passes: `avoid` holds the fridge-and-health words, so "is butter better than
margarine" and "how much saturated fat in butter" keep their own answers.
"""
from ..compose import pick
from .lookup import entry

# The topic ids this domain answers (bot/understanding/topics.py).
ANSWERS = ("cooking", "food-and-drink")

# The fats a person can put in a pan, said as a choice. Both words have to be in the line: the row
# is about picking between two of them, and a line that names one fat is a different question
# ("is butter bad for you", "how long does butter keep").
_FAT_CHOICE = (
    # Butter against oil is the swap people actually ask about, and the two are not the same
    # thing in a pan. Lard, ghee and dripping are left out on purpose: a line that picks one of
    # those against oil is usually about a dish with its own method ("lard or oil for roast
    # potatoes" is the roast potatoes card, which says hot oil), and this row would take it.
    "butter or oil", "oil or butter", "butter or olive oil", "olive oil or butter",
    # the fridge's own choice: the spread row answers "butter or margarine" on toast, and a
    # line that says a pan brings it here
    "butter or margarine", "margarine or butter",
    # a fat asked about as a fat, whatever the pan holds
    "which fat", "what fat", "which is the best fat",
)

# The choice said with an "or" in it, as one alternation: the stand-down for the dish table.
_ALT_FAT = "|".join(_FAT_CHOICE)

# What makes it a pan and not a piece of toast.
_IN_THE_PAN = (
    "fry", "fries", "fried", "frying", "cook", "cooks", "cooked", "cooking", "roast",
    "roasting", "bake", "baking", "pan", "sear", "searing", "saute", "sauté", "stir fry",
    "griddle", "skillet", "onion", "onions", "potato", "potatoes", "carrot", "carrots",
    "mushroom", "mushrooms", "egg", "eggs", "steak", "chicken", "sausage", "sausages",
    "cake", "sauce", "curry", "pancake", "pancakes", "shallow fry", "deep fry", "oven",
)

# The fridge and the label: these lines have a nutrition answer, and a pan answer is the wrong one.
_NOT_A_PAN = (
    "healthy", "healthier", "unhealthy", "healthiest", "cholesterol", "calories", "fattening",
    "saturated", "unsaturated", "good for you", "bad for you", "heart", "diet", "dieting",
    "spread", "toast", "on toast", "sandwich", "margarine or butter on", "lurpak",
    "how much", "how many", "keep", "keeps", "last", "lasts", "fridge", "freezer", "freeze",
    "gone off", "off", "rancid", "mouldy", "mould", "substitute", "instead of butter",
    "without butter", "dairy free", "vegan", "allergy", "lactose",
)

# A vegetable in the oven has a card with its own time and temperature on it, and that card says
# which fat to toss it in. "butter or oil for roast potatoes" reached the roast potatoes card on
# main and this row took it, so the one answer with the method in it was replaced by a lesson
# about smoke points. The dish keeps its own card; the fat row answers the pans that have no dish.
_A_DISH_WITH_ITS_OWN_METHOD = (
    "roast potato", "roast potatoes", "roasties", "roast parsnip", "roast parsnips",
    "roast carrot", "roast carrots", "roast veg", "roast vegetables", "roast squash",
    "roast swede", "roast beetroot", "roast celeriac",
)

def _asks_between(line):
    """True when the line is a choice between two fats for a pan, not a request for a dish.

    "should i cook onions in butter or oil" names two foods and a cooking verb, so the meal
    table answered it with one dish for each - shortbread for the butter and onion soup for the
    onions - where the person had asked which fat to use. The dish table stands down on this
    reading and the row below answers it.
    """
    low = " " + _fold(str(line or "")) + " "
    if not any(phrase in low for phrase in (" " + _ALT_FAT + " ")):
        return False
    if not any(" " + word + " " in low for word in _IN_THE_PAN):
        return False
    return not any(" " + word + " " in low for word in _NOT_A_PAN)


def _fold(text):
    return " ".join(str(text or "").lower().split())


THE_CARD = (
    "Oil takes the heat and butter gives the taste: butter starts to burn at about 150C, "
    "so for a hot pan or a hot oven use oil and add butter at the end. Butter on its own "
    "is for a low pan where nothing goes above that heat - onions, mushrooms, eggs, 15 to "
    "20 minutes on a low heat for the onions - and in a cake oil keeps it moist for days "
    "while butter gives the flavour most people expect.")

# The card, said again in the words of the pan it was about. "should i cook onions in butter or
# oil" then "butter or oil for frying onions" is one person asking the same thing twice: the
# answers module will not put the same paragraph on the screen twice (STYLE.md), and with this
# row the only card that fits the line, the second ask reached the composer with nothing to say
# and was met with "Got it. Is there anything you'd like a hand with?" - a shrug, where main's
# oils card at least answered something. The second ask is decided by the one sentence the first
# answer already had, so that is what it gets, and a third ask gets the other one.
THE_DECIDER = (
    "For onions either is fine: butter on a low heat for 15 to 20 minutes gives the taste and "
    "will not burn below 150C, and oil takes a hotter pan - so oil for a hard fry and butter for "
    "the onions.",
    "Low heat for butter, high heat for oil: onions in butter on a low heat for 15 to 20 minutes "
    "sweeten without catching, and a pan hot enough to brown goes to the oil.",
)


def _last_reply(memory):
    """What the bot said last, so the same answer is not given word for word twice."""
    turns = (memory or {}).get("turns") or []
    if not turns:
        return ""
    return str((turns[-1] or {}).get("bot") or "")


def _fat_for_the_pan(memory, reading):
    """The card, or - when it is already on the screen - the sentence that decides the pan."""
    said = _last_reply(memory)
    if said.startswith(THE_DECIDER[0][:40]) or said.startswith(THE_DECIDER[1][:40]):
        return None      # the short answer is on the screen too; a third card would be the same
    if said.startswith(THE_CARD[:40]):
        return pick(THE_DECIDER, memory)
    return THE_CARD


ENTRIES = (
    entry("fat-for-the-pan", (_FAT_CHOICE, _IN_THE_PAN),
          _fat_for_the_pan,
          avoid=_NOT_A_PAN + _A_DISH_WITH_ITS_OWN_METHOD, bias=-1),
)
