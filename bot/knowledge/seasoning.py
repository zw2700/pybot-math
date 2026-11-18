"""Seasoning: how much of a spice goes in the dish, as a figure rather than a rule.

"How much cinnamon in a cake", "how many cloves of garlic in a curry", "how many cloves for
mulled wine" and "how much chilli powder for four" are one question about one ingredient, and
none of them had an owner here: the cake's tin table read out the tin sizes, the spice row
answered "spices are not bad for you", the units row took the mulled wine and the planting row
took the garlic. The amount is a fact about the spice and is the same whatever dish is named
beside it, so it is a table read by the spice - one line per ingredient - rather than a rule
per dish. Garlic sits first so that "cloves of garlic" is the garlic figure and not the clove
one.

A line that is not a dose stays out: growing a spice, whether it is good for you, a pet that
ate it, a jar that went off, the price of the jar and a count of buns for a crowd all have
their own answers, and each of them is a word in _SPICE_NOT_A_DOSE.
"""
import re

from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# One ingredient, one figure: "how much cinnamon in a cake", "how many cloves for mulled wine",
# "how many cloves of garlic in a curry". None of these had an owner. The cake's tin table read
# out the sizes for "how many cloves in a cake", the spice row answered "spices are not bad for
# you", the units row took the mulled wine, and the planting row took the garlic. What is asked
# is an amount, and the amount is the same whatever dish is named beside it, so it is a table
# read by the spice rather than a rule per dish. Garlic sits first so that "cloves of garlic" is
# the garlic figure and not the clove one.
_SPICE_AMOUNTS = (
    # "cloves of garlic" is the garlic, not the clove: the name that starts in the same place as
    # the bare word is the longer one, so the two words around it are part of the name here.
    (("garlic", "cloves of garlic", "clove of garlic", "garlic cloves", "garlic clove"),
     "Two or three cloves for a curry, stew or sauce that serves four: a fat clove is about a "
     "teaspoon once crushed, so a teaspoon of the jarred paste stands in for one."),
    (("garlic powder", "garlic granules"),
     "Half a level teaspoon of garlic powder for a curry for four, which stands in for a clove "
     "or two; granules are weaker, so use a whole teaspoon, and add either one with the liquid "
     "rather than at the end, because they need a minute to soften."),
    (("black pepper", "ground pepper", "peppercorns", "pepper"),
     "Half a teaspoon of ground black pepper for a dish that serves four, stirred in at the end "
     "with the salt: pepper is aroma rather than heat, and it goes flat when it cooks for a long "
     "time, so a long stew wants it twice - once at the start and a little at the end."),
    (("vanilla", "vanilla extract", "vanilla essence"),
     "A teaspoon of vanilla extract in a 20cm cake; essence is weaker, so use two, and vanilla "
     "paste about the same as the extract."),
    (("cinnamon",),
     "A teaspoon or two in a 20cm sponge, and half a teaspoon on a bowl of porridge: start with "
     "one and taste, because an old jar is weaker than a new one."),
    (("baking powder",),
     "Two level teaspoons per 200g of plain flour, which is what lifts a sponge. Self-raising "
     "flour already has it in, so add none there."),
    (("bicarbonate of soda", "bicarbonate", "bicarb", "baking soda"),
     "Half a teaspoon per 200g of plain flour, with something acid - buttermilk, yogurt, lemon "
     "juice - to set it off; on its own it leaves a soapy taste."),
    # Allspice is not a blend, whatever the name suggests: it is one dried berry that tastes of
    # clove, cinnamon and nutmeg together, which is why it used to be answered with the mixed
    # spice line and why "it is a blend, so it is gentler" was wrong about it.
    (("allspice", "ground allspice", "pimento", "pimento berries"),
     "A quarter teaspoon of ground allspice for a 20cm cake, or six berries in a jar of pickle: "
     "it tastes of clove, cinnamon and nutmeg at once, so a little stands in for all three."),
    (("mixed spice", "pumpkin spice"),
     "Two teaspoons in a 20cm cake, or a teaspoon across a dozen buns: it is a blend, so it is "
     "gentler than any single spice in it."),
    (("nutmeg",),
     "A quarter of a whole nut, grated, for a 20cm cake or a pan of rice pudding. Whole nutmeg "
     "keeps its flavour for years and ground loses it in months."),
    (("ground ginger", "ginger"),
     "A teaspoon of ground ginger in a 20cm cake or a stir-fry for four; fresh ginger is about "
     "three times the weight for the same heat."),
    (("garam masala",),
     "A teaspoon or two for a curry for four, stirred in at the very end with the heat off: it "
     "is a finishing blend, and cooked from the start it loses the scent that is the point of "
     "it."),
    (("curry powder", "masala"),
     "A tablespoon of curry powder for a curry for four. Fry it in the oil for half a minute "
     "before the liquid goes in and it tastes twice as strong."),
    (("chilli powder", "chili powder", "cayenne", "chilli flakes", "chili flakes"),
     "Half to one teaspoon for four, and taste before the second half: heat builds as it cooks, "
     "so it is easy to overshoot and hard to take back."),
    # A chilli is a spice as well as a vegetable, and "how much chilli per person" is the heat
    # question it never had an owner for. The fresh word reads after the powder, because "how
    # much chilli powder" names the powder and not a chilli, and one word of the two answers both.
    (("chilli", "chili", "chillies", "chilis", "chile"),
     "One chilli for four is enough heat for most people: add a second at the end if you want "
     "more, and taking out the seeds and white pith halves the heat without losing the taste."),
    (("cumin", "ground cumin", "cumin seeds"),
     "A teaspoon of ground cumin in a chilli or a curry for four, or a tablespoon of the seeds, "
     "which want thirty seconds in a dry hot pan first to wake them up."),
    # The leaf and the seed are two different spices in one word: "how much coriander to garnish"
    # is a handful of the fresh green, and the ground seed line was what it got.
    (("fresh coriander", "coriander leaves", "coriander to garnish", "coriander garnish"),
     "A small handful of fresh coriander for four, torn in at the end: the stems hold most of "
     "the flavour, so chop them into the sauce and keep the leaves for the top."),
    (("coriander", "ground coriander", "coriander seeds"),
     "A teaspoon of ground coriander for a curry for four; the seeds toast in a dry pan in half "
     "a minute and grind to something fresher and more citrus than the jar."),
    (("turmeric",),
     "Half a teaspoon is colour and a teaspoon is flavour for a dish that serves four; more than "
     "that turns bitter, which is why it is never heaped in."),
    (("paprika", "smoked paprika"),
     "A teaspoon for four is enough for the colour and the smoke; it burns in a hot pan, so add "
     "it with the liquid rather than at the start."),
    # The herbs go in by the handful and the spoonful rather than by the jar: a dried herb is
    # weaker than the fresh one, so the fresh figure is three times the dried one and both are
    # said, because "how much thyme in a stew" can be either.
    (("oregano", "dried oregano"),
     "A teaspoon of dried oregano for four, or a tablespoon of fresh leaves. Dried oregano wants "
     "ten minutes in the sauce to soften; fresh is stirred in at the end."),
    (("thyme", "fresh thyme", "dried thyme", "thyme leaves"),
     "Three or four sprigs of fresh thyme for four, or a teaspoon of the dried leaves: the woody "
     "stems come out before serving, so tie them in a bundle if you want the job easy."),
    (("rosemary", "fresh rosemary", "dried rosemary"),
     "One sprig for a roast for four, or a teaspoon of the needles chopped fine. It is strong "
     "and resinous, so it goes in at the start with the meat rather than at the end."),
    (("sage", "fresh sage", "dried sage"),
     "Four or five leaves for four, or a teaspoon dried and crumbled: it is the strongest of the "
     "soft herbs and turns medicinal if it is doubled, so it is the one to under-do."),
    (("bay leaf", "bay leaves", "bay"),
     "One leaf for a stew or a pan of rice for four, and take it out at the end: two is plenty "
     "in a big pot, and a broken leaf left in is what makes a stew taste of the cupboard."),
    (("basil", "fresh basil", "dried basil"),
     "A handful of fresh leaves for four, torn in off the heat at the end, or a teaspoon of dried "
     "in the sauce while it cooks. Dried basil loses the scent that is the reason to use it."),
    (("parsley", "fresh parsley", "dried parsley"),
     "Two tablespoons of chopped fresh parsley for four, stirred in at the end. Dried parsley is "
     "mostly for colour, so use twice as much and expect little taste from it."),
    (("dill", "fresh dill"),
     "A tablespoon of chopped dill for four, in at the end: it is a soft herb and the scent goes "
     "with heat, so it is stirred through just before the pot comes off."),
    (("mint", "fresh mint", "dried mint"),
     "A handful of leaves for four, torn rather than chopped, or a teaspoon of dried mint. In a "
     "yogurt sauce or a salad it wants to be the last thing that goes in."),
    (("mixed herbs", "italian herbs", "herbes de provence", "dried herbs"),
     "A teaspoon of mixed dried herbs for four; a tablespoon if the pot is a big one and cooking "
     "for an hour or more, because the dried leaves give up their taste slowly."),
    # "How much spice for a curry for four" names no single spice, and a blend is still a
    # spoonful: it goes last so that every named spice above is read first.
    (("spice", "spices", "spice mix", "seasoning", "mixed herbs and spices"),
     "A tablespoon of a ground spice blend for a dish that serves four, and a tablespoon over a "
     "kilo of chicken: taste after the first spoonful, because blends vary more in heat than "
     "their labels let on."),
    # Saffron is sold by the pinch and asked for by the dish, because a paella is where most
    # people meet it: three or four threads is the whole of it.
    (("saffron",),
     "Three or four threads for a paella or a risotto for four, steeped in a spoonful of the hot "
     "stock first: any more than that and it starts to taste of the chemist's shelf."),
    (("star anise", "star aniseed", "stars anise"),
     "One whole star anise for a bottle of mulled wine or a slow-cooked pork for four: it is "
     "liquorice-strong, and two would take over the whole pot."),
    (("clove", "cloves", "ground clove", "ground cloves"),
     "A quarter teaspoon of ground cloves for a 20cm cake, or four to six whole ones in a bottle "
     "of mulled wine: it is strong, and more than that tastes medicinal."),
)
# A spice question that is not about a dish: what it is for, whether it is good for you, a plant
# to grow, a pet that ate it or a jar that went off all have their own answers.
_SPICE_NOT_A_DOSE = ("plant", "planting", "planted", "grow", "growing", "sow", "sowing",
                     "good for", "bad for", "healthy", "safe", "allergy", "allergic",
                     "ate", "eaten", "dog", "cat", "puppy", "kitten", "baby", "toddler",
                     "pregnan", "out of date", "gone off", "mouldy", "price", "prices",
                     # a herb is a plant before it is an ingredient: "how much water does basil
                     # need" is a watering question, and the water row answers it.
                     "water", "sun", "sunlight", "soil", "compost", "fertiliser",
                     "fertilizer", "plant food", "in a pot", "in the garden",
                     "cost", "buy", "cheapest", "substitute", "instead of", "swap",
                     # a count of dishes for a crowd is a portion question: "how many cinnamon
                     # buns for 20 people" is not a teaspoon of anything, and the row that
                     # portions buns out answers it. "per person" and "a head" are not in this
                     # list: a rate of the spice is still the spice, so "how much curry powder per
                     # person" wants the tablespoon and not the card about spices being good for
                     # you, while "how much chicken per person" is the portion table's question.
                     # "people" is not here either: "how much chilli for four people" is still a
                     # spoonful of chilli, and what a headcount actually counts is the dish, which
                     # the bun and batch words below stand down on. The portion table answers the
                     # dishes themselves.
                     "each", "servings",
                     "portions", "buns", "rolls", "batches", "a crowd",
                     # a jar of cinnamon has a price, and "how much is a jar of cinnamon" is the
                     # shopping question rather than a spoonful.
                     "how much is", "how much are", "how much for", "jar", "jars",
                     # how many cloves come in a bulb is a count out of a pack, which is the row
                     # beside this one, so the amount of spice stands down on the phrase.
                     "in a bulb", "in one bulb", "a bulb of", "bulb of",
                     # "can i put cinnamon in my coffee" is whether a spice is a good idea, and
                     # the spice row in nutrition.py answers it.
                     "in my coffee", "in coffee", "in my tea", "in tea",
                     # "how much turmeric is too much" is a dose-and-safety question, and the
                     # spice row answers it; an amount for a dish is a different ask.
                     "too much", "how much is too much", "limit", "a day", "per day",
                     # "how much chilli con carne for four" is how much of the dish to make, and
                     # the one word "chilli" in it is the dish's name rather than a chilli.
                     "con carne",
                     # A pepper on a supermarket shelf is a vegetable, and the table's pepper is
                     # the mill: a stuffed or roasted pepper is a portion question.
                     "bell pepper", "bell peppers", "red pepper", "green pepper",
                     "yellow pepper", "orange pepper", "sweet pepper", "sweet peppers",
                     "jalapeno", "jalapenos", "scotch bonnet", "romano", "padron")


# The one dish people name the whole spice rack for: a bottle of mulled wine is cloves, cinnamon
# and star anise together, so the dish is read before the single spice it also names.
_MULLED_WINE = ("Four to six whole cloves, a cinnamon stick snapped in two and a star anise in a "
                "bottle of red: warm it gently for twenty minutes without letting it boil, and "
                "taste before you add any sugar.")


# A spice in a drink is a spoonful per mug rather than a spoonful for a cake: "how much pumpkin
# spice in a latte" names a spice the cake line also names, and the cake's figure is the wrong
# one for a mug.
_PUMPKIN_LATTE = ("A quarter to half a teaspoon for a mug, whisked into the coffee with the milk "
                  "and a little sugar: it is mostly cinnamon, so it needs the sugar to taste of "
                  "anything.")


def _spice_amount(memory, understood):
    """The figure for one spice, when the line asks how much of it goes in a dish."""
    said = " " + re.sub(r"[^a-z0-9 ]+", " ",
                        str((understood or {}).get("clean") or "").lower()) + " "
    if any((" " + word + " ") in said for word in _SPICE_NOT_A_DOSE):
        return ""
    if "mulled wine" in said:
        return _MULLED_WINE
    if "pumpkin spice" in said and any(drink in said for drink in
                                       ("latte", "coffee", "cappuccino", "mug", "cup")):
        return _PUMPKIN_LATTE
    # The spice the line asks about is the one it names first, not the first row of the table:
    # "how much cumin in a chilli" is a question about cumin, and the bare "chilli" of the dish
    # was taking it. Where two names begin in the same place the longer one is the name, so
    # "chilli powder" stays the powder and "fresh coriander" the leaf.
    first_at, first_len, first_reply = None, 0, ""
    for variants, reply in _SPICE_AMOUNTS:
        for variant in variants:
            found = re.search(r"\b" + variant + r"\b", said)
            if found is None:
                continue
            at = found.start()
            if first_at is None or at < first_at or (at == first_at and len(variant) > first_len):
                first_at, first_len, first_reply = at, len(variant), reply
    return first_reply

ENTRIES = [
    entry("spice-amount",
          # The key names the thing in the jar, and only the words the table above answers:
          # a word in the key that no row of the table speaks for is a word that pulls the row
          # into a line it then has to stand down on, and it is worth less to the whole ranking
          # for being in more keys.
          (("clove", "cloves", "garlic", "pepper", "black pepper", "ground pepper",
            "peppercorns", "cinnamon", "vanilla", "baking powder", "bicarbonate",
            "bicarb", "baking soda", "mixed spice", "allspice", "pumpkin spice", "nutmeg",
            "ginger", "curry powder", "garam masala", "masala", "chilli powder", "chili powder",
            "cayenne", "chilli flakes", "chilli", "chili", "chillies", "turmeric", "paprika", "cumin", "coriander", "saffron",
            "oregano", "thyme", "rosemary", "sage", "bay leaf", "bay leaves", "bay",
            "basil", "parsley", "dill", "mint", "mixed herbs", "italian herbs", "dried herbs",
            "star anise", "cardamom", "fennel seeds", "mustard seeds",
            "spice", "spices", "spice mix", "seasoning"),
           # The dish the spice goes into is how the amount is asked: "how much garlic in a
           # curry" and "how much pepper in a sauce" name the spice and the dish and no amount
           # word at all. The dish belongs in the key rather than in the reply, and the ask
           # below still wants an amount word, so "can i put cinnamon in a sauce" is not this
           # row's line - the health row answers that one.
           ("how much", "how many", "much", "many", "amount", "spoon", "spoons",
            "teaspoon", "teaspoons", "tablespoon", "tablespoons",
            "in a curry", "in the curry", "in a stew", "in the stew", "in a sauce",
            "in the sauce", "in a soup", "in the soup", "in a chilli", "in the chilli")),
          _spice_amount,
          # The spice and herb rows below name cloves, garlic and cinnamon too, and a word that
          # sits in more keys is worth less to the ranking, so the amount needs the extra weight
          # to beat the health row, the planting row and the tin table on those words.
          bias=3,
          # The ask is the amount and nothing else. "add", "put in" and "in a" were in this
          # list at first, and they pulled in every yes/no line with a spice in it ("should i
          # add cumin to my chilli"), which the health row answers; an amount is asked with an
          # amount word, so the words that carry one are the whole of the ask.
          ask=("how much", "how many", "much", "many", "amount", "spoon", "spoons",
               "teaspoon", "teaspoons", "tablespoon", "tablespoons", "grams", "handful"),
          avoid=_SPICE_NOT_A_DOSE +
          ("calories", "carbs", "protein", "how many calories", "cholesterol")),
]
