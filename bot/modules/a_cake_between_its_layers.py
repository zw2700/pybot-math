"""A cake asked what goes between its layers is the filling question, not five other cards.

Six wordings of the same everyday question reached five other rows on main: "what can i put
between the layers of a cake" was a punt, "what cream goes in a victoria sponge" and "what goes in
the middle of a lemon cake" were the sponge weights, "what filling for a coffee cake" and "how do
i fill a cake" were how long buttercream keeps, and the two splitting lines were worse than punts -
"how do i layer a cake" was the haircut card, whose key holds a bare "layers", and "how do i cut a
cake in half" was "Divide it by 2: half of 46 is 23".

The cake is in every one of those lines, so the reading is the two halves of the question: a cake
named, and a word that says *between* - filling, middle, layers, split, half, which cream, which
jam. Asking is part of it: a cake that sank, domed or is raw in the middle is a fault, and "i cut
myself a slice of cake" is a cut with a knife in it.

Then the matcher is asked what the line reaches, and a row that answers a cake keeps the turn: the
recipe for a named cake ("how do i make a cream cake"), how long it keeps, how many calories, the
buttercream in grams, the tin for a birthday cake. Only the rows that answered the wrong thing
stand down, listed once in `NOT_THE_CAKE_ROW`, and a punt has nothing to lose.

A module rather than a row because the rows that took these lines - the haircut, the halving sum,
the sponge weights - are in files at the repository's size cap and each would need its own avoid.
The card is written once here and answers every way of asking it.
"""
import re

from ..knowledge.lookup import find
from ..understanding import understand

PRIORITY = 1200
# The line is about baking or about a dish, and a topic entry that matched "cake" on its own does
# not answer what goes between the layers (README, "Routing": `ANSWERS_INSTEAD`).
ANSWERS_INSTEAD = ("cooking", "food-and-drink", "home-and-diy")

# The cake, in the words people use for one.
A_CAKE = re.compile(
    r"(?<![a-z])(?:cake|cakes|sponge|gateau|cupcake|cupcakes|victoria sponge|"
    r"victoria sandwich|madeira|loaf cake|sandwich cake)(?![a-z])", re.I)
# What says *between*: the filling, the middle, or the cut that makes two halves.
BETWEEN = re.compile(
    r"(?<![a-z])(?:filling|fill|filled|between the layers|between the two|in the middle|"
    r"the middle of|middle of it|layer|layers|layer it|two layers|three layers|split|"
    r"split it|sandwich it|halve|in half|what cream|which cream|what jam|cream goes|"
    r"jam goes|goes between|goes in the middle)(?![a-z])", re.I)
# Asking, not handing in a cake that went wrong.
NOT_ASKING = re.compile(
    r"\b(?:why|sank|sink|sunk|sinking|stodgy|dense|heavy|dry|burn|burnt|undercooked|raw|gummy|"
    r"domed|dropped|didnt rise|didn't rise|flat|stale|birthday|vegan|gluten|egg free|"
    r"no eggs|cupcake cases|icing|frosting|whip|whipping|myself|himself|herself|a slice|"
    r"a piece of|how long|keep|keeps|last|freeze|fridge|calorie|calories|how many|many people|"
    r"serves|feed|tin size|what size tin|instead of the egg)\b", re.I)

# The rows that answered these lines with something else. A row that answers a cake keeps its
# turn, so the list is only what was measured wrong: the recipe for a named cake, the sponge
# weights, the dish plan that read "what goes in the middle" as the ingredients, the haircut
# and the halving sum.
NOT_THE_CAKE_ROW = frozenset((
    "recipe-lemon-drizzle", "amount-in-a-dish", "plan-followup", "hair-cut-yourself",
    "half-of-a-number", "bakes",
))

THE_FILLING = (
    "Jam and buttercream, jam first: a thin layer of jam stops the two halves sliding, then "
    "buttercream on top of it - about 3 tablespoons of jam and 150g of buttercream for a 20cm "
    "cake. Split the sponge by pushing cocktail sticks in at the height you want all the way "
    "round, then cut to them with a long serrated knife, turning the cake as you go so the line "
    "meets itself. A chocolate cake takes ganache instead - 100g dark chocolate melted into 100ml "
    "double cream, cooled until it holds - and fresh cream with fruit is the best filling there "
    "is, though it wants making on the morning you eat it.")


def asks_about_its_layers(said):
    """True when the line asks where the filling or the split goes in a cake."""
    if not isinstance(said, dict):
        return False
    if said.get("kind") not in (None, "question", "request", ""):
        return False
    text = " ".join(
        str(part) for part in (said.get("clean"), said.get("text")) if isinstance(part, str))
    if isinstance(said.get("words"), (list, tuple)):
        text = text + " " + " ".join(str(word) for word in said["words"])
    if not text.strip():
        return False
    return bool(A_CAKE.search(text) and BETWEEN.search(text) and not NOT_ASKING.search(text))


def respond(text, memory):
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    said = understand(text, memory)
    if not asks_about_its_layers(said):
        return None
    row = _the_row(text, memory)
    if row is not None and getattr(row, "id", "") not in NOT_THE_CAKE_ROW:
        return None
    return THE_FILLING


def _the_row(text, memory):
    try:
        return find(understand(text, memory if isinstance(memory, dict) else {}))
    except Exception:                       # pragma: no cover - the matcher must never crash a turn
        return None


