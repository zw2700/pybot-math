"""A figure about something the person made is not a look-up (PRIORITY -997).

"how many calories in my stew", "how many grams of sugar in a flapjack", "how many grams in an
apple pie", "how many carbs in my dinner", "how many calories in a quiche" all reached the seed
fallback - "I'm not sure about that one, sorry - I'd rather not guess. A quick search online will
get you a solid answer". Nothing can know those numbers: the recipe, the portion and what went
into it are what decide them, and the figures are on the recipe card or the label on the pack.
A search engine is the wrong instrument for somebody's own stew.

This is a module rather than a kind in bot/compose/gap.py because that file is shared with every
lane, and a new file cannot conflict. PRIORITY -997 puts it just above the seed fallback (-1000)
and below every module that can answer, so it only ever speaks where nothing else did: the food
rows that know their figures keep their turn.

The measure shape alone is never enough, which is the whole fence here. A conversion ("how many
ml in a bath"), a brand ("how many calories in a big mac"), a meal deal and a staple ("how many
grams of rice for two people") all have the same shape and are all answered elsewhere or not
this kind at all, so a line needs a dish word or the person's own cooking and portion. "How much
sugar is in a flapjack" is the same ask with "much" in it, so both words are read.
"""
import re

PRIORITY = -997

# The measure, then the thing it is measured in: grams, calories, carbs, sugar, spoonfuls.
A_FIGURE = re.compile(
    r"\bhow (?:many|much)\s+(?:grams?|g|kg|calories?|cals?|carbs?|carbohydrate|sugar|salt|"
    r"protein|fat|fibre|fiber|ml|millilitres?|litres?|ounces?|oz|slices?|portions?|servings?|"
    r"spoons?|tablespoons?|teaspoons?)\b[^?!]{0,40}?\b(?:in|of|per|for)\b", re.I)
# Something made rather than grown, poured or sold in a packet.
DISH = re.compile(
    r"\b(?:stew|casserole|pie|quiche|tart|cake|flapjack|brownie|biscuit|scone|pudding|"
    r"crumble|lasagne|lasagna|curry|chilli|soup|broth|risotto|paella|pizza|sandwich|"
    r"wrap|salad|roast|stir ?fry|noodle|dumpling|loaf|bake|smoothie|porridge|granola|"
    r"muffin|pastry|gravy|sauce|dressing|hummus|dip|pancake|omelette|frittata)\b", re.I)
# Their own pan, their own plate: the answer is in what they used.
THEIRS = re.compile(
    r"\b(?:my|the one i|i made|i baked|i cooked|homemade|home made|left ?overs?)\b|"
    r"\b(?:portion|serving|slice|bowl|plate|helping)\b", re.I)

POOL = (
    "The recipe and the portion are what set that, not a general figure: the weights on your own "
    "recipe card or the label on the pack, divided by how many it served. Tell me what went in "
    "and how many it made, and I will work the sum out with you.",
    "Nothing here can know that one - it depends what went into it and how much of it you had. "
    "Your recipe or the pack has the figures for the whole thing, so halve it or quarter it; "
    "give me the amounts and I will do the division.",
)


def respond(text, memory):
    clean = " ".join(str(text or "").lower().split())
    if not clean:
        return None
    if not A_FIGURE.search(clean):
        return None
    if not (DISH.search(clean) or THEIRS.search(clean)):
        return None
    return POOL[0]
