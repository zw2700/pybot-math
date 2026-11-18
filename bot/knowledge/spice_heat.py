"""How hot a named spice is: one table, one row for each line of it.

"Is paprika spicy", "how hot is cumin" and "is cinnamon hot" all reached a search hedge, and
"how hot is a paprika" reached the weather card because the only "hot" the bot knew about was
the outdoors. Heat is a fact about a named spice, not a judgement, so it lives here as a table:
the names people write on a jar, the band the spice sits in, and the one thing worth knowing
about using it. Adding a spice is adding a line.

Every row is keyed on the names plus the words that ask the question, so "is cayenne spicy",
"how hot is cayenne", "how strong is cayenne" and "does cayenne make it hot" reach the same
verdict without the wording mattering. The ranges are the ordinary published Scoville bands and
they are said as ranges, because the same spice varies from jar to jar.
"""
from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# What makes a line a question about how hot something is. These are the asks; the spice name in
# each row's key is what makes the line a question about a spice at all.
HOT = ("how hot", "how spicy", "is it hot", "is it spicy", "spicy", "hot", "heat", "hotter",
       "mild", "milder", "mildest", "hottest", "scoville", "strong", "strength", "fiery",
       "burn", "burns", "burning", "kick", "too much heat")

# The question is about a spice on a shelf, not about a car, a radiator or a jar to buy: the
# same word is a Porsche, an engine that is overheating and a supermarket shelf.
NOT_A_SPICE_LINE = ("engine", "coolant", "radiator", "brake", "porsche", "car", "van", "boiler",
                    "heating", "oven temperature", "how hot should the oven", "weather",
                    "forecast", "outside", "today", "tomorrow", "sun", "barbecue", "bbq",
                    "instead of", "substitute", "swap", "replace", "where can i buy", "cheap",
                    "grow", "growing", "plant", "sow", "seedling", "recipe", "how do i make",
                    "make my own", "how much", "how many")

# name -> (the ways it is written, the answer). The answer opens with the verdict, because it is
# the whole of what was asked.
HEAT = (
    (("paprika", "sweet paprika", "hungarian paprika"),
     "Paprika is mild, around 1,000 Scoville - closer to a red pepper than to a chilli. A "
     "teaspoon colours a pot and sweetens it more than it heats it, which is why a goulash can "
     "take two spoons and still be gentle."),
    (("smoked paprika", "smoky paprika", "pimenton"),
     "Smoked paprika is mild too, around 1,000 Scoville - the smoke comes from drying the "
     "peppers over oak, not from heat. Half a teaspoon is enough to taste it; more turns a dish "
     "bitter rather than hotter."),
    (("cayenne", "cayenne pepper"),
     "Cayenne is hot: about 30,000 to 50,000 Scoville, so a quarter teaspoon heats a whole pot. "
     "It has little taste of its own, which is why it is the thing to reach for when a dish needs "
     "heat and not another flavour."),
    (("chilli powder", "chili powder"),
     "Chilli powder is a blend, usually mild to medium with cumin and oregano in it, so the heat "
     "depends on the jar - some are mostly cayenne. Taste a pinch on your tongue before you "
     "decide how much goes in."),
    (("chilli flakes", "chili flakes", "red pepper flakes", "crushed chillies"),
     "Chilli flakes are medium-hot, around 30,000 to 50,000 Scoville, and they give their heat "
     "slowly: a pinch in oil at the start is warmer than the same pinch scattered at the end."),
    (("curry powder",),
     "Curry powder is mild - it is turmeric, cumin, coriander and fenugreek, and it is not where "
     "the heat in a curry comes from. Two spoons in a curry for four is about right, and the heat "
     "is added separately with chilli."),
    (("garam masala",),
     "Garam masala is warm, not hot: cinnamon, cardamom, cloves and pepper, ground together. A "
     "teaspoon goes in at the end of cooking, where the smell survives; boiled for an hour it "
     "tastes of dust."),
    (("cumin", "jeera"),
     "Cumin is not hot at all - it is warm, earthy and slightly bitter, and it is the smell of a "
     "curry rather than the fire in it. A teaspoon for four, fried in the oil for a few seconds "
     "first."),
    (("turmeric", "haldi"),
     "Turmeric is not hot: earthy and a little bitter, and too much of it tastes of soap. Half a "
     "teaspoon for four is plenty, and it stains a wooden spoon and a white shirt for good."),
    (("cinnamon", "cassia"),
     "Cinnamon is warm and sweet, not hot. The sticks sold cheaply are cassia, which is stronger "
     "and slightly bitter - fine in a curry, and worth knowing if a recipe came out tasting of "
     "cloves."),
    (("black pepper", "peppercorns", "ground pepper"),
     "Black pepper is mildly hot, at the back of the throat, and nothing like chilli: a whole "
     "teaspoon of it is gentler than a pinch of cayenne. Freshly ground is far sharper than the "
     "dust in a jar."),
    (("white pepper",),
     "White pepper is hotter than black, with a farmyard smell that suits soups, congee and "
     "Chinese cooking. Use half as much as you would black."),
    (("mustard powder", "english mustard", "mustard"),
     "Mustard is hot in a different place from chilli - it burns in the nose and fades in a few "
     "seconds. Mixed with water it is hottest; vinegar or hot liquid takes the edge off it."),
    (("ginger", "root ginger", "ginger powder"),
     "Ginger is warm and sharp rather than hot like chilli, and the burn fades in seconds. A "
     "thumb-sized piece grated into a curry for four is a good amount."),
    (("garlic powder", "garlic granules"),
     "Garlic powder is not hot at all - it is savoury and a little sweet, and it burns if it "
     "sits in hot oil, so add it with the liquid."),
    (("coriander", "coriander seed", "ground coriander"),
     "Coriander seed is not hot: it tastes of orange peel and hay, and it is the rounded body in "
     "a curry powder. Toast it before grinding and the smell doubles."),
    (("nutmeg",),
     "Nutmeg is warm and sweet, not hot - a quarter teaspoon in a cheese sauce or a pudding is "
     "the usual dose, and more tastes of medicine."),
    (("cloves", "ground cloves"),
     "Cloves are warm and very strong, not hot, and two or three in a pot is enough. Too many "
     "and the dish tastes of the dentist."),
    (("cardamom",),
     "Cardamom is aromatic, not hot: menthol and flowers. Crush the pods just before they go in, "
     "because the seeds lose their smell within a day of grinding."),
    (("five spice", "chinese five spice"),
     "Five spice is not hot - star anise, fennel, cinnamon, cloves and pepper - and it is strong, "
     "so half a teaspoon for four is the usual amount."),
    (("sumac",),
     "Sumac is not hot: it is sour and fruity, the taste of lemon without the wet. A teaspoon "
     "over a salad or grilled meat at the end."),
    (("horseradish", "wasabi"),
     "Horseradish is hot in the nose, like mustard, and the burn lasts seconds rather than "
     "minutes. A teaspoon of the creamed sort is plenty for a plate of beef."),
    (("sriracha",),
     "Sriracha is mild to medium, around 2,000 Scoville - ketchup-hot rather than chilli-hot, and "
     "sweet. A spoon per bowl adds heat slowly enough to taste as you go."),
    (("tabasco", "tabasco sauce"),
     "Tabasco is about 2,500 Scoville, sharper and much saltier than sriracha, so a few shakes "
     "per plate. It is vinegar-forward: added early it dulls, added at the table it does not."),
    (("gochujang",),
     "Gochujang is medium, around 1,000 to 2,000 Scoville, and sweet and fermented with it, so "
     "the heat arrives after the sweetness. A tablespoon for four."),
    (("harissa",),
     "Harissa is medium-hot, roughly 4,000 to 5,000 Scoville, with cumin and garlic in the paste. "
     "A spoon per portion stirred into the sauce at the end."),
    (("jalapeno", "jalapenos", "jalapeño"),
     "A jalapeño is mild to medium, 2,500 to 8,000 Scoville: hot enough to eat raw in slices, and "
     "much milder pickled or cooked. The seeds and white pith hold most of the heat."),
    (("serrano", "serranos"),
     "A serrano is 10,000 to 23,000 Scoville - two or three times a jalapeño, with a cleaner, "
     "greener taste. Half a one is enough for a curry for four."),
    (("poblano", "poblanos"),
     "A poblano is mild, 1,000 to 1,500 Scoville - roasted and stuffed it tastes of smoke and "
     "green pepper, not of heat."),
    (("ancho", "anchos"),
     "An ancho is a dried poblano: mild, 1,000 to 2,000 Scoville, raisin-sweet and a little "
     "smoky. Two soaked in a sauce for four give colour and depth without heat."),
    (("chipotle", "chipotles", "chipotle in adobo"),
     "A chipotle is a smoked, dried jalapeño, 2,500 to 8,000 Scoville. The adobo it comes in is "
     "milder than the pepper itself - one pepper and a spoon of the sauce for a pot for four."),
    (("habanero", "habaneros", "habañero"),
     "A habanero is very hot, 100,000 to 350,000 Scoville, and fruity with it. A quarter of one "
     "heats a pot for four, and it is worth wearing gloves for a batch: the oil stays on hands for "
     "hours and soap barely shifts it."),
    (("scotch bonnet", "scotch bonnets"),
     "A scotch bonnet is very hot, 100,000 to 350,000 Scoville, with a fruity, almost apricot "
     "taste that survives the heat. One, deseeded, is enough for a family curry."),
    (("allspice",),
     "Allspice is warm and peppery, not hot - it tastes of cinnamon, clove and nutmeg at once, "
     "which is where the name comes from. A few berries in a stew or a cake, and no heat at all."),
    (("star anise",),
     "Star anise is not hot: it is liquorice-sweet and very strong, so one star in a pot for four. "
     "Two and the dish tastes of cough sweets."),
    (("fennel seed", "fennel seeds", "fennel"),
     "Fennel seed is not hot - it is sweet and aniseedy, and it is half the taste of a sausage. A "
     "teaspoon crushed in a curry for four."),
    (("fenugreek", "methi"),
     "Fenugreek is not hot: it is bitter and maple-sweet, and a little goes a long way. The leaves "
     "are gentler than the seeds, which turn a dish bitter if they are fried too hard."),
    (("asafoetida", "hing"),
     "Asafoetida is not hot, but it is ferociously strong - a pinch in hot oil, no more, and it "
     "smells of onions and garlic once it has cooked. A quarter teaspoon for a pot for four."),
    (("curry leaves", "curry leaf"),
     "Curry leaves are not hot at all: they are citrusy and nutty, and they only give that up when "
     "fried in hot oil for a few seconds at the start. Dried ones taste of very little."),
    (("zaatar", "za'atar"),
     "Za'atar is not hot: it is thyme, sesame and sumac, so it is herby and sour. A spoon over "
     "bread or yoghurt, not a source of heat."),
    (("berbere",),
     "Berbere is medium to hot, roughly 3,000 to 5,000 Scoville - a blend of chilli, paprika, "
     "fenugreek and warm spices. A tablespoon for four gives an Ethiopian stew its heat."),
    (("jerk seasoning", "jerk spice", "jamaican jerk"),
     "Jerk seasoning is hot: it is scotch bonnet with allspice, thyme and sugar, so it can be "
     "100,000 Scoville or more. A tablespoon per kilo of chicken, and less if the jar is old - "
     "chilli loses its heat over a year or two."),
    (("peri peri", "piri piri"),
     "Peri peri is hot, 50,000 to 175,000 Scoville, and sharp with lemon and vinegar. A spoon in a "
     "marinade for four is a strong heat once it is cooked down."),
    (("sambal", "sambal oelek"),
     "Sambal is medium to hot, 2,000 to 10,000 Scoville depending on the jar, and salty and sour "
     "with it. A teaspoon per portion stirred in at the end."),
    (("ras el hanout",),
     "Ras el hanout is a Moroccan blend and not usually hot - cumin, coriander, cinnamon, ginger "
     "and pepper - though some jars have chilli in. A tablespoon for a tagine or a tray of "
     "vegetables."),
    (("togarashi", "shichimi togarashi", "nanami togarashi"),
     "Togarashi is mild to medium, mostly sesame, orange peel and seaweed with a little chilli, so "
     "it is a finishing sprinkle rather than a heat source."),
    (("chilli oil", "chili oil", "chili crisp", "chilli crisp"),
     "Chilli oil is as hot as the chillies that went into it - usually medium, around 10,000 "
     "Scoville - and the crisp bits are hotter than the oil. A teaspoon over noodles."),
    (("hot sauce",),
     "Hot sauce covers everything from 500 to 300,000 Scoville, so the bottle is the only way to "
     "know: Tabasco is about 2,500, sriracha about 2,000, and a scotch bonnet sauce can be a "
     "hundred times hotter. Taste a drop before you commit."),
    (("birds eye", "bird's eye", "bird eye chilli", "thai chilli"),
     "A bird's eye chilli is hot, 50,000 to 100,000 Scoville - one or two will heat a curry for "
     "four, and they are hotter dried than fresh."),
)

# Asked as a superlative, the answer is a name and a number.
EXTRA = (
    (entry("spice-hottest-chilli",
           (("hottest chilli", "hottest chili", "hottest pepper", "hottest chillies",
             "worlds hottest", "strongest chilli"),
            ("which", "what", "is the", "hottest", "name")),
           "The hottest chilli on the ordinary record is Pepper X at around 2.7 million "
           "Scoville, after the Carolina Reaper at about 1.6 million - both too hot to eat raw, "
           "and used in sauces at a fraction of a percent. A habanero at 300,000 is already a "
           "hundred times a jalapeño.",
           avoid=NOT_A_SPICE_LINE,
           bias=1)),
    (entry("spice-mildest-chilli",
           (("mildest chilli", "mildest chili", "mildest pepper", "mild chilli", "mild chillies"),
            ("which", "what", "is the", "mildest", "name", "recommend")),
           "The mildest chillies are the ones grown to be eaten like vegetables: shishito, "
           "around 100 Scoville and mild nine times in ten, and poblano at 1,000 to 1,500. "
           "Deseeding a hotter one takes most of the heat out without losing the taste.",
           avoid=NOT_A_SPICE_LINE,
           bias=1)),
)


def _rows():
    """One row per spice: the names it is written as, and the verdict, in the same shape."""
    built = []
    for number, (names, reply) in enumerate(HEAT):
        built.append(entry("spice-heat-" + names[0].replace(" ", "-").replace("'", ""),
                           (names, HOT),
                           reply,
                           # "instead of paprika" is the substitution question, which has its
                           # own answer, and a dish that is already too hot is a fault in the
                           # cooking rather than a fact about the spice.
                           avoid=NOT_A_SPICE_LINE + ("instead", "substitute", "ran out",
                                                     "my curry", "too spicy", "too hot",
                                                     # "what does a dash of hot sauce mean" asks
                                                     # how much a dash is, so the measure word is
                                                     # the subject of the line and not the sauce.
                                                     # The asking shape, not the word: a dash of
                                                     # hot sauce in a soup is still the sauce.
                                                     "what does a dash", "what is a dash",
                                                     "how much is a dash", "dash mean",
                                                     "what does a pinch", "what is a pinch",
                                                     "how much is a pinch", "pinch mean"),
                           bias=1))
    return tuple(built)


ENTRIES = _rows() + EXTRA
