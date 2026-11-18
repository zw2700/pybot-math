"""Kitchen faults that come back as a mirror of what the person said, or as another food's answer.

"Got it - your marmalade is cloudy" is not an answer, and three of these lines get one that is
about a different thing: "my pickle is fizzy, is that ok" was told how long an opened jar keeps,
and "my haricot beans are still hard" was told to pull the string down the seam of runners, which
is advice about a green bean. Each fault has a cause worth knowing, so each one gets the cause and
the fix rather than a set of steps.

Nothing here is a keeping, cooking or storing question: `avoid` sends those back to the entries
that already answer them, and a line this module does not recognise passes, so another entry keeps
its turn. A smoking pan, a shrunk pastry and a lumpy custard already have their answers, and their
words are not keys here.
"""
from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# Three faults that come back as a mirror of what the person said - "Got it, your marmalade is
# cloudy" - or as an answer about a different food. A smoking pan, a shrunk pastry and a lumpy
# custard already have their answers, so those lines are left alone.
_KITCHEN_THING = ("jam", "marmalade", "pickle", "pickles", "pickled", "pickled onions",
                  "pickled onion", "onions", "onion", "beetroot", "gherkin", "gherkins",
                  "cornichon", "cornichons", "sauerkraut", "kimchi", "jalapeno", "jalapenos",
                  "chutney",
                  "lentils", "lentil", "chickpeas", "chickpea", "beans", "haricot",
                  "butter beans", "split peas", "cannellini")
_KITCHEN_FAULT = ("cloudy", "mouldy", "mould", "moldy", "mold",
                  "furry", "fuzz", "white stuff", "white bits", "white film", "white bloom",
                  "white specks", "fizzy", "bubbling", "bubbles", "slimy",
                  "still hard", "went hard", "stay hard", "stayed hard", "wont soften",
                  "won't soften", "didnt soften", "didn't soften", "not softening", "rock hard",
                  "too hard")


def _kitchen_fault(memory, understood):
    """Three kitchen faults, each with its own cause.

    The jam is scum, the pickle is three answers in one jar - mould, a flat white film and a
    fizz - and the pulses are about how old they are.
    """
    words = [str(word).lower() for word in (understood.get("words") or [])]
    said = " ".join(words)

    def has(*wanted):
        # eggs/egg, pickles/pickle: the same loose match the rest of the knowledge base uses
        return any(word == want or word.startswith(want) for word in words for want in wanted)

    def says(*phrases):
        return any(phrase in said for phrase in phrases)

    if has("jam", "marmalade", "chutney"):
        if has("cloudy") or says("is cloudy", "looks cloudy", "went cloudy"):
            return ("A cloudy jam or marmalade is scum and trapped air, not a fault: it sets and "
                    "eats exactly the same. Skim the froth off with a slotted spoon as it boils, "
                    "add a small knob of butter at the end to settle the bubbles, and let it stand "
                    "five minutes off the heat before potting so the peel does not float. A "
                    "marmalade made with the whole fruit is cloudy by nature, and only a clear "
                    "jelly asks for strained juice.")
    if has("pickle", "pickles", "chutney") or says("white stuff", "white bits", "white film"):
        if has("fizzy", "bubbling", "bubbles") or says("is fizzy", "went fizzy", "bubbling"):
            return ("Bubbles and a little fizz in a brine pickle are the fermentation working, and "
                    "the pickle is fine: lactic acid bacteria give off carbon dioxide as they turn "
                    "the sugar to acid, and the jar settles down after a week or two. Keep the "
                    "vegetables under the brine and taste a piece - a sharp, clean sourness is "
                    "right. If the brine has gone thick and slimy, or it smells of rot rather than "
                    "vinegar, throw that jar away.")
        if has("white stuff", "white bits", "white specks", "bloom") \
                or says("white stuff", "white bits", "white specks", "white film", "white bloom",
                        "cloudy brine"):
            # A flat white film is the harmless one, and this is the line that says so first.
            return ("A flat white film or speckle on top of a pickle is usually kahm yeast, which "
                    "is harmless: skim it off, keep the vegetables under the brine and the pickle "
                    "is fine. Fuzzy or hairy mould - blue, green, black - is a different thing: "
                    "throw that jar away, because the mould's threads reach down through the brine "
                    "and spooning it off the top does not make it safe. A weight that keeps "
                    "everything under the liquid stops both.")
        if has("mouldy", "mould", "moldy", "mold", "furry", "fuzz", "green", "blue", "black",
               "hairy") or says("mould on", "mouldy", "gone mouldy", "went mouldy"):
            # Any other mould is the one to throw away, so that is the first thing said.
            return ("Throw that jar away: mould on a pickle is not something you can rescue, "
                    "because the threads reach down through the brine and lifting the patch off "
                    "the top leaves them behind. The one exception is a flat white film with no "
                    "fuzz - that is usually kahm yeast, and skimming it off is enough, provided "
                    "the pickle still smells sour and tastes clean. Keeping the vegetables under "
                    "the brine with a weight is what stops mould taking hold.")
    if has("lentils", "lentil", "chickpeas", "chickpea", "beans", "haricot", "butter beans",
           "split peas") or says("split peas", "haricot beans", "butter beans", "cannellini"):
        if has("still hard", "went hard", "stay hard", "stayed hard", "wont soften",
               "won't soften", "didnt soften", "didn't soften", "not softening", "rock hard",
               "too hard") or says("still hard", "wont soften", "won't soften", "stay hard"):
            # One sentence on purpose: the composer strips a sentence the bot has just said, and
            # a reply in pieces came back as a dangling clause when the next pulse was asked about.
            return ("Old pulses are the usual reason: lentils and beans lose the ability to soften "
                    "as they age, so cook them in plenty of unsalted water, add the salt at the "
                    "end, and give chickpeas and dried beans an overnight soak and 60 to 90 "
                    "minutes at a bare simmer.")
    return None

ENTRIES = (
    # Glasses and mugs are the hand-washed things cleaning.py keeps apart from the machine; this
    # is the one prep question the other cooking tables had no row for.
    entry("wash-produce",
          (("vegetables", "veg", "lettuce", "salad", "leaves", "spinach", "kale", "cabbage",
            "fruit", "apples", "grapes", "tomatoes", "cucumber", "herbs", "potatoes",
            "carrots", "mushrooms", "berries", "strawberries"),
           ("wash", "washing", "rinse", "rinsing", "cleaned", "dirty", "muddy", "soil",
            # not "peel", which is how you take the skin off a potato, not how you rinse one
            "before cooking", "before eating")),
          "Rinse under cold running water and rub the surface between your hands - a colander "
          "under the tap and a shake does most of it, a salad wants its leaves separated and dried "
          "in a tea towel, and grapes want the bunch broken up so the water reaches all of them. "
          "Soap and washing-up liquid are not for food, and a sealed bag marked ready to eat is "
          "already washed.",
          # keeping, storing, freezing and cooking a vegetable are other answers, and so is
          # washing your hands or the dishes. Pasta and rice are staples, not produce:
          # "do i need to rinse pasta for a salad" was this row, and the salad in it is the dish.
          avoid=("pasta", "spaghetti", "macaroni", "penne", "fusilli", "tagliatelle", "noodles",
                 "rice", "how long", "keep", "keeping", "store", "storage", "freeze", "frozen",
                 "fridge", "how do i cook", "boil", "roast", "recipe", "my hands", "dishes",
                 "clothes", "car", "dog", "salad dressing", "which salad",
                 # "apples" matches the "apple" in "apple watch", so a watch that got washed was
                 # told to rinse the produce and dry it in a tea towel. A device is not produce.
                 "apple watch", "watch", "watches", "phone", "iphone", "laptop", "tablet",
                 "ipad", "kindle", "earbuds", "airpods", "headphones", "device", "remote",
                 # a mushroom has its own card with the don't-soak lore on it, and the general
                 # rinse read worse than it did (hardy-guava)
                 "mushroom", "mushrooms",
                 # garden mud is brushed off dry, because wet mud smears: the muddy-veg card is
                 # the better answer for "how do i clean muddy carrots" (deft-lime)
                 "mud", "muddy",
                 # "leaves" is a salad leaf and it is also the verb in "my flatmate leaves the
                 # washing up all the time", which is who does the job rather than how to rinse
                 # a lettuce. Washing up and the people in the house are the load question's.
                 "washing up", "flatmate", "housemate", "roommate", "partner", "husband",
                 "wife", "boyfriend", "girlfriend", "never helps", "chores", "chore",
                 "leaves it", "leaves the", "leaves them", "left the", "all the time"),
          bias=2),
    entry("kitchen-fault", (_KITCHEN_THING, _KITCHEN_FAULT),
          _kitchen_fault,
          # how long it keeps, how to cook it, what to make with it and how to store it are all
          # questions with answers of their own; this one is only for the thing that went wrong
          avoid=("how long", "how do i cook", "how do i make", "recipe", "keep", "freeze",
                 "fridge", "soak", "soaking", "how many", "how much", "should i", "can i",
                 "why is my potato", "sprouted", "sprouts"),
          bias=1),
)
