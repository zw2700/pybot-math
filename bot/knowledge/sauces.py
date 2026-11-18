"""The sauces that go with a roast, one row each, keyed by the sauce rather than the wording.

Main answered "how do i make bread sauce" with a white loaf - 500g of strong flour, 7g of yeast,
350ml of water - because the word "bread" is the recipe's and the sauce was never a subject. The
same shape took the other three: "how do i make cranberry sauce" and "how do i make mint sauce"
were shrugs, and "how do i make apple sauce" was answered with the goodness of apple skin. A roast
dinner is the meal people cook for a table of guests and the sauces are the part they ask about,
so the four are here, with the horseradish and the brandy butter that go with the beef and the
pudding.

Why its own domain: each sauce is a short recipe and a keeping rule, and cooking_entries.py is
where one-off rows go - this is a table of them. It answers the cooking topic and is gated on the
word "sauce", so the herb itself, the fruit itself and the cranberry juice are somebody else's
question.
"""
import re

from .lookup import entry as _entry

ANSWERS = ("cooking", "food-and-drink")

# A gate, not a key: the word "sauce" has to be in the line. "Does cranberry juice help a UTI",
# "how do i grow mint" and "are apples good for you" all name a food from this table without
# asking how to make a sauce of it, and none of them says "sauce".
_IS_A_SAUCE = ("sauce", "sauces", "sauce.", "sauces?")

# The words that make a sauce line a request for the recipe, its keeping or its fault. All the
# rows share them, so a line that only names the sauce and asks nothing else ("bread sauce") still
# reaches the row: the subject alone is the question for a recipe.
_ASKING = ("sauce", "sauces", "make", "makes", "making", "made", "recipe", "recipes",
           "cook", "cooking", "how",
           "what", "whats", "need", "want", "christmas", "turkey", "roast", "lamb", "beef",
           "pork", "goose", "ham", "dinner", "homemade", "from scratch", "jar", "bought",
           "ahead", "make it ahead", "ahead of time", "in advance", "the day before",
           # the keeping question is this table's too, and each row answers it in its own words:
           # a sauce named after a fruit keeps like a sauce, not like the fruit. A reviewer found
           # the words gone and the sauce answering with the food it is made of.
           "keep", "keeps", "keeping", "kept", "last", "lasts", "freeze", "freezes", "freezer",
           "freezing", "frozen", "defrost", "fridge", "refrigerate", "how long",
           "how much", "sugar", "vinegar", "hot", "mild", "quick", "easy", "best", "good",
           "nice", "serve", "served", "with", "goes")
# The fault and the keeping are somebody else's rows: a lumpy apple sauce has a remedy, a thin
# cranberry sauce has a fix, and "can i freeze apple sauce" is the apple sauce's keeping answer
# ("stewed apple freezes 3 months"). Those rows answer the sauce by name, so this table takes
# only the request for the recipe itself - and a reviewer found the fault and keeping words here,
# where the recipe answered nine questions it does not answer at all.
_NOT_A_RECIPE = ("lumpy", "lumps", "lump", "thick", "thicker", "thicken", "thickened",
                 "thickening", "runny", "thin", "watery", "sweet", "sweeter", "too sweet",
                 "sharp", "sour", "bitter", "salty", "bland", "separated", "split", "curdled",
                 "grainy", "gelatinous", "out of date", "use by", "gone off", "mouldy")

# How long a sauce keeps is the row's other question, and it is answered from the row: ask the
# fruit's or the bread's keeping card instead and a jar of cranberry sauce is "dried fruit, 6
# months in a sealed jar". The fault words above stay stood down - the generic fault cards are
# written for a sauce too.
_KEEPING = re.compile(
    r"\b(?:keep|keeps|keeping|kept|last|lasts|lasting|freeze|freezes|freezer|freezing|frozen|"
    r"defrost|fridge|refrigerated|refrigerate|how long|how many days|till|until)\b", re.I)

# A keeping word in the line settles it: "how long does cranberry sauce keep" and "can i keep
# bread sauce in the fridge until friday" are both keeping questions, and the second one has an
# "until" in it that must not turn it into a step.
_A_KEEPING_WORD = re.compile(
    r"\b(?:keep|keeps|keeping|kept|last|lasts|lasting|freeze|freezes|freezer|freezing|frozen|"
    r"defrost|fridge|refrigerated|refrigerate)\b", re.I)

# "How long" and "until" on their own do not make a keeping question. "How long do i simmer the
# cranberry sauce", "how long does bread sauce take to make", "stir the cranberry sauce until
# the sugar dissolves" and "add the milk to the bread sauce until smooth" are all asking for the
# method - and it holds the time, "Simmer ... for 10 minutes" - so this table must answer them
# with the recipe rather than stand down for it. A reviewer caught the keeping paragraph taking
# four of these; a first fix stood the row down instead and lost the recipe to a general card,
# which is the same fault one step along. Two shapes are a step or a time:
#   - an "until"/"till" clause, which introduces a step and never a keeping question;
#   - a how-long with a cooking verb in it.
# A keeping word anywhere in the line is read as keeping first, so "can i keep bread sauce in
# the fridge until friday" still gets the sauce's two days.
_A_COOKING_TIME = re.compile(
    r"\b(?:how long|how many minutes)\b[^.?!]{0,45}?"
    r"\b(?:cook|cooks|cooking|simmer|simmering|boil|boiling|bake|baking|roast|roasting|"
    r"microwave|microwaving|reheat|reheating|stir|stirring|reduce|reducing|whisk|whisking|"
    r"take|takes|leave|on the stove|on the hob|in the oven|stove|hob|oven)\b"
    r"|\b(?:simmer|simmering|cook|cooking|boil|boiling|bake|baking|roast|roasting|stir|"
    r"stirring|reduce|reducing|whisk|whisking)\b[^.?!]{0,30}?\buntil\b", re.I)

# An "until" clause is a step - "add the milk to the bread sauce until smooth", "cook the apple
# sauce until it is soft" - and the verb in front of it is not always one of the cooking verbs
# above. The method in this row is what holds the step, so an until-clause line gets the recipe.
# A keeping word anywhere in the line still settles it first, which keeps "can i keep bread
# sauce in the fridge until friday" a keeping question.
_AN_UNTIL = re.compile(r"\b(?:till|until)\b", re.I)

# "How long does mint sauce need to sit" is the standing time, and the method in this row has it
# ("leave it 20 minutes"): a how-long with a standing or resting verb in it is a step's length,
# not a shelf life, and the keeping paragraph answered it with a month in the fridge.
_A_STEP_LENGTH = re.compile(
    r"\b(?:how long|how many minutes|how many hours)\b[^.?!]{0,40}?"
    r"\b(?:sit|sits|sitting|rest|rests|resting|stand|stands|standing|set|sets|setting|"
    r"soak|soaks|soaking|marinate|marinating|chill|chilling|before (?:you )?serv|"
    r"before use|to cool)\b", re.I)

# One keeping answer per sauce, in the sauce's own words rather than the fruit's or the bread's.
_KEEPS = {
    "bread sauce": (
        "Bread sauce is best the day it is made. It keeps 2 days covered in the fridge, and it "
        "reheats gently with a splash of milk in a pan rather than in the microwave, which makes "
        "the crumbs grainy. It does not freeze well: the sauce splits and the breadcrumbs go "
        "gritty, so make it fresh and reheat what is left."),
    "cranberry sauce": (
        "In a clean jar with a lid the sauce keeps 2 weeks in the fridge, and it freezes for 3 "
        "months in small tubs. Thaw it overnight, because the set loosens a little and a stir "
        "brings it back; it keeps a week once a jar has been opened."),
    "mint sauce": (
        "Mint sauce keeps about a month in a sealed jar in the fridge, and it does not freeze: "
        "the mint goes black and limp and the vinegar takes over. Make it in small amounts and "
        "stir in fresh mint if it has been sitting a while."),
    "apple sauce": (
        "Apple sauce keeps 4 to 5 days in a covered dish in the fridge and freezes for 3 months "
        "in bags or tubs. Thaw it overnight and stir it, because it can look watery once it "
        "defrosts - a spoon of butter or a quick beat brings it back."),
    "horseradish sauce": (
        "Fresh horseradish sauce keeps 3 or 4 days in the fridge, and it does not freeze well: "
        "the cream splits and the heat fades. A jarred one lasts months in the fridge once "
        "opened."),
    "brandy butter": (
        "Brandy butter keeps 2 weeks covered in the fridge and freezes for 3 months - roll it in "
        "a log and slice it cold. Let it soften a few minutes at the table but do not leave it "
        "out of the fridge for long."),
}

# Some sauces are asked for by their own name with no "sauce" on the line - "how do i make toum",
# "how do i make hollandaise" - and the shared gate would stand down on both. Their gate is the
# shared one plus the names that are a sauce on their own.
_SAUCE_OR_TOUM = _IS_A_SAUCE + ("toum",)
_SAUCE_OR_HOLLANDAISE = _IS_A_SAUCE + ("hollandaise", "bearnaise", "béarnaise")

# The brandy butter is not a sauce, so its own gate names what it is. A gate, not a key: the
# butter itself, a butter dish and a butter substitute are somebody else's rows.
_IS_A_BRANDY_BUTTER = ("brandy butter", "hard sauce", "brandy cream", "brandy butter sauce")

# Garlic sauce is two sauces, and the word the line uses is the whole difference: "garlic yoghurt
# sauce" was answered with a litre of milk and a yoghurt-making recipe, and it wants the spoonful
# version, not the oil emulsion.
_GARLIC_EMULSION = (
    "Crush 4 peeled garlic cloves with a good pinch of salt to a smooth paste, then add 200ml of "
    "neutral oil a few drops at a time, beating all the time, and a little lemon juice whenever "
    "it thickens - the garlic takes up the oil and it turns white and thick like mayonnaise. If "
    "it splits, put a fresh clove in a clean bowl and beat the split batch into it a spoonful at "
    "a time. For the quick yoghurt version, stir crushed garlic, lemon and salt into 200g of "
    "thick yoghurt.")
_GARLIC_YOGHURT = (
    "Crush one garlic clove to a paste with a good pinch of salt - crushing rather than chopping "
    "is what stops it biting - then stir it into 200g of thick Greek yoghurt with a squeeze of "
    "lemon and leave it 10 minutes. A tablespoon of mayonnaise keeps it from splitting when it "
    "meets hot food, and grated cucumber, mint or a little cumin turns it into a dip.")


def _garlic_sauce(memory, understood):
    """The oil emulsion, or the spoonful-in-yoghurt version when the line says yoghurt."""
    line = ((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    if "yoghurt" in line or "yogurt" in line:
        return _GARLIC_YOGHURT
    return _GARLIC_EMULSION


_SAUCES = (
    (("bread sauce", "breadsauce"),
     "Simmer 300ml of whole milk with half an onion studded with 4 cloves and a bay leaf for 10 "
     "minutes, then fish the onion out, stir in 100g of fresh white breadcrumbs and simmer 3 to 4 "
     "minutes until it is thick and creamy. Season it with salt, pepper and grated nutmeg, and "
     "stir in a knob of butter at the end. Make it an hour ahead and reheat it gently with a "
     "splash of milk.",
     ("stuffing", "stuffing a chicken", "sandwich", "toast", "breadcrumbs for", "stale bread")),
    (("cranberry sauce", "cranberry jam", "cranberries", "cranberry"),
     "Tip 250g of cranberries into a pan with 100g of sugar, the zest and juice of an orange and "
     "2 tablespoons of water, and simmer it 8 to 10 minutes, until the berries pop and it is "
     "thick but still a little chunky. It firms up as it cools, so take it off while it is looser "
     "than you want it on the plate. A jar keeps a week in the fridge and it freezes well.",
     ("juice", "uti", "water infection", "cystitis", "vitamin", "good for you", "healthy",
      "dried", "supplement", "tablets", "grow", "growing", "bush", "bog")),
    (("mint sauce", "mint jelly"),
     "Pour 4 tablespoons of boiling water over 4 tablespoons of sugar and stir until it has "
     "dissolved, add 4 tablespoons of white wine vinegar, then stir in a big handful of mint "
     "chopped as finely as you can and leave it 20 minutes. That is the sweet-sharp mint sauce "
     "for lamb; mint jelly is the bought set version, and a spoon of redcurrant jelly with fresh "
     "mint does the same job in a hurry.",
     ("grow", "growing", "plant", "pot", "dying", "wilted", "yellow", "spread", "take over",
      "peppermint", "tea", "oil", "leaves in")),
    (("apple sauce", "applesauce", "apple compote"),
     "Peel, core and chop 3 cooking apples, put them in a pan with 2 tablespoons of water and 1 "
     "of sugar, and simmer 8 to 10 minutes with the lid on until they collapse. Beat them smooth "
     "or leave it chunky, and stir in a knob of butter for a richer one. Bramleys are the apples "
     "that go fluffy; eaters stay in lumps and taste sweeter.",
     ("skin", "peel", "good for you", "healthy", "vitamin", "baby", "weaning", "tree",
      "grow", "orchard", "variety", "bake in the oven")),
    (("horseradish sauce", "horseradish cream", "horseradish"),
     "Grate fresh horseradish root finely - or use a jarred one - and fold about 2 tablespoons of "
     "it into 4 tablespoons of creme fraiche or whipped double cream with a squeeze of lemon, a "
     "pinch of salt and a little sugar. Grate it near an open window or in a food processor: the "
     "heat is in the fumes, not the flesh, and it hits the back of your nose.",
     ("grow", "growing", "plant", "root in the garden", "is it a weed", "leaves")),
    (("brandy butter", "hard sauce", "brandy cream"),
     "Beat 100g of soft butter with 100g of icing sugar until it is pale, then add 3 to 4 "
     "tablespoons of brandy a spoonful at a time: it should be stiff enough to hold a spoon "
     "upright. Chill it in a dish and serve it cold with Christmas pudding or mince pies, where "
     "it melts into the pudding rather than sitting on top of it.",
     ("how much brandy", "drunk", "alcohol free", "without alcohol", "for a child"),
     _IS_A_BRANDY_BUTTER),
    # The pan sauces: the sauce is made in the tin the meat came out of, and the brown bits are the
    # whole point of it. "how do i make peppercorn sauce" and "how do i make mushroom sauce" were
    # both the search hedge, and the two are one technique with a different flavouring.
    (("peppercorn sauce", "green peppercorn sauce", "pepper sauce", "peppercorn"),
     "Pour off most of the fat from the pan you cooked the steak in and set it back on a medium "
     "heat: add a splash of brandy or red wine and scrape the brown bits up, then 150ml of stock "
     "and a tablespoon of crushed green peppercorns, and let it reduce by half. Take it off the "
     "heat, stir in 100ml of double cream and a teaspoon of Dijon, and put it back for a minute "
     "until it coats a spoon. Season at the end and taste first: reduced stock is already salty, "
     "and a sauce made with cream takes a lot of pepper.",
     ("grow", "growing", "plant", "peppercorns in", "grinder", "white pepper", "black pepper",
      "sneezing", "buy", "brand", "jar", "shop"),
     _IS_A_SAUCE),
    (("mushroom sauce", "mushroom cream sauce", "creamy mushroom sauce"),
     "Fry 200g of sliced mushrooms in butter over a high heat until the water they give off has "
     "gone and they squeak in the pan, then add a chopped shallot and a splash of wine or stock "
     "and scrape the brown bits up. Add 150ml of stock, reduce it by half, pour in 100ml of cream "
     "and simmer 3 minutes; finish off the heat with thyme or tarragon and a knob of butter. Do "
     "not crowd the pan or they steam grey instead of browning.",
     ("grow", "growing", "foraging", "picking", "poisonous", "magic", "dried", "buy", "shop",
      "keep in the fridge", "gone slimy"),
     _IS_A_SAUCE),
    # The emulsion: garlic, oil and lemon, which is the same trick as mayonnaise the other way up
    # (oil into garlic rather than into egg). "how do i make garlic sauce" and "how do i make toum"
    # were a hedge and a punt, and hollandaise with them.
    (("garlic sauce", "toum", "garlic cream", "lebanese garlic sauce", "garlic yoghurt sauce",
      "garlic yogurt sauce"),
     _garlic_sauce,
     ("buy", "jar", "shop", "brand", "grow", "planting", "bread", "chicken kiev",
      "calories", "healthy", "keep", "freeze"),
     _SAUCE_OR_TOUM),
    (("hollandaise", "hollandaise sauce", "bearnaise", "béarnaise"),
     "Whisk 2 egg yolks with a tablespoon of water and a teaspoon of lemon juice in a bowl over a "
     "pan of barely simmering water until it thickens enough to hold a ribbon, then take it off "
     "the heat and beat in 125g of melted butter a few drops at a time, with the bowl still warm "
     "but not hot. Season with salt and a little cayenne. If it gets too thick, a spoon of warm "
     "water loosens it; if it splits, a teaspoon of cold water beaten in hard usually brings it "
     "back. Keep it warm, never hot, or the yolks scramble.",
     ("buy", "jar", "shop", "sachet", "packet", "leftover", "reheat", "freeze",
      "eggs benedict", "poached egg"),
     _SAUCE_OR_HOLLANDAISE),
)


# The sauces whose question names the tin as well as the sauce.
_MADE_IN_THE_PAN = ("peppercorn sauce", "mushroom sauce")



def _keeps(reply, keeping):
    """The sauce's own keeping answer when the line asks how long it lasts, else the recipe."""
    def answer(memory, reading):
        line = ""
        if isinstance(reading, dict):
            line = str(reading.get("norm_text") or reading.get("clean") or
                       reading.get("text") or "")
        if _A_KEEPING_WORD.search(line):
            # the keeping question, answered here when the sauce has its own answer and stood
            # down otherwise: an answer to a different question reads as confidence and the
            # person never learns their sauce went off.
            return keeping or None
        if _AN_UNTIL.search(line) or _A_STEP_LENGTH.search(line):
            # a step or a step's length, and this row is where the method for it lives
            return reply(memory, reading) if callable(reply) else reply
        if _A_COOKING_TIME.search(line):
            # a how-long-to-cook line is the timing rows' question: this table's keeping answer
            # would be a confident reply about the wrong thing, and its recipe is not a time.
            return None
        if keeping and _KEEPING.search(line):
            return keeping
        if not keeping and _KEEPING.search(line):
            # a keeping question this row has no keeping answer for - "how long does hollandaise
            # keep" - is the shrug's or another row's, not the recipe's: an answer to a different
            # question reads as confidence and the person never learns their sauce went off.
            return None
        return reply(memory, reading) if callable(reply) else reply
    return answer


def _rows():
    entries = []
    for number, row in enumerate(_SAUCES):
        names, reply, avoid = row[0], row[1], row[2]
        gate = row[3] if len(row) > 3 else _IS_A_SAUCE
        entries.append(_entry(
            "sauce-" + names[0].replace(" ", "-"),
            (names, _ASKING),
            _keeps(reply, _KEEPS.get(names[0], "")),
            ask=gate,
            # the sauce is the subject, so a line about the meat, the fruit or the herb itself is
            # not read here even when the words of the table are in it. A pan sauce is the
            # exception: it is made in the tin the steak came out of, so those words are its
            # question rather than a different one.
            avoid=avoid + _NOT_A_RECIPE + (
                () if names[0] in _MADE_IN_THE_PAN
                else ("meat", "steak", "joint", "roasting tin", "gravy", "stock")),
            # a named sauce is the answer, ahead of any row that shares the word in its name
            bias=2 + (1 if number == 0 else 0)))
    return entries


ENTRIES = _rows()
