"""Pasta, on its own: how long a shape takes, and the questions that were answered next door.

Pasta is the one everyday food whose answer depends on which shape is in the pan - a strand of
thin spaghetti is done in eight minutes, a tube of rigatoni needs thirteen, and fresh pasta
needs two - so a single "8 to 12" answers nobody. The times live here as data, one row per
shape, and the entry asks for a word for cooking or timing as well, so "what goes with pasta"
and "how do i keep leftover pasta" stay with the entries that answer them.

The rest is pasta that was being answered by a neighbour: a mushy pan read as rice, lasagne
sheets read as bed linen, a squash read as a strand, and pasta in the oven read as nothing.
Each one names its own subject here rather than taking the neighbour's answer.

This is a domain of its own rather than a part of bot/knowledge/cooking.py because the cooking
table is the busiest list in the repository - every cooking entry lands at the end of it - and a
domain is one file with ENTRIES, per bot/knowledge/__init__.py.
"""
from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# A "how long" question is asking for a number, so the number has to be in the first sentence.
TIME_ASK = frozenset(("how long", "minutes", "minute", "mins", "time", "long", "take", "takes",
                      "took", "quickest"))

# Per shape, because a tube takes longer than a strand. The more specific word wins, so a line
# that names two shapes gets the one that is actually in the pan.
PASTA_MINUTES = (
    (("thin spaghetti", "spaghettini", "angel hair", "linguine", "vermicelli", "capellini"),
     "8 to 9 minutes"),
    (("spaghetti", "penne", "fusilli", "macaroni", "farfalle", "bow", "bows"),
     "10 to 11 minutes"),
    (("rigatoni", "tagliatelle", "orecchiette", "cannelloni", "pappardelle", "conchiglie"),
     "11 to 13 minutes"),
    (("tortellini", "ravioli", "gnocchi", "tortelloni"), "3 to 4 minutes"),
)

# A noodle is not one thing: instant and thin wheat noodles are done in three or four minutes,
# egg noodles in four or five, and dried rice noodles need six to eight. One number would be
# wrong for two of the three, so the noodle line says all three and points at the packet.
NOODLES = ("Noodles are quick but not all the same: thin or instant ones are 3 to 4 minutes, egg "
           "noodles 4 to 5, and dried rice noodles 6 to 8, so check the packet for yours.")

# The shapes, so a line that names one is a pasta line even when it says nothing else.
SHAPES = tuple(shape for keys, _minutes in PASTA_MINUTES for shape in keys) + ("noodles", "noodle")

# What keeps the neighbours out of the time answer: a squash is a roasted vegetable, a bake is
# not a boil, a portion question is arithmetic, and the keeping questions have their own entry.
NOT_A_TIME = ("squash", "spaghetti squash", "butternut", "courgette", "zucchini", "pumpkin",
              "in the oven", "pasta bake", "baked pasta", "bake", "baked", "baking",
              "how many sheets", "how many lasagne", "how much", "portion", "portions", "per person", "fridge", "freezer",
              "keep", "keeps", "keeping", "leftover", "left over", "next day", "reheat",
              # "how long does cooked pasta last" is a keeping question, and the cooked word
              # cannot go in this list: "cooked" is a form of "cook", and it would take
              # "how long do i cook pasta" from this entry. "last" and "days" only ever ask
              # how long the food keeps.
              "last", "lasts", "lasting", "days", "day",
              "gone off", "sauce recipe", "salad", "sticking", "stuck", "clump", "clumps",
              # "how do i stop pasta boiling over" is the pot, not the clock: pan-boil-over in
              # cooking.py owns it, and the time row was answering with the salt-and-water method.
              "boil over", "boils over", "boiling over", "boiled over", "overflow", "overflows",
              "spill", "spills", "spilling", "spilled", "spilt")


# The kinds, by the job the shape does rather than by its name: a sauce clings to a twist and
# runs off a strand, a tube holds a chunk and a sheet is a bake. Each line names the shapes an
# ordinary shop actually sells, so "what are the different types of pasta" is answered with a
# handful of families rather than a list of forty shapes. Times are the ones PASTA_MINUTES holds.
PASTA_KINDS = (
    ("long strands", "spaghetti, linguine and tagliatelle",
     "a ragu, a carbonara or a butter sauce the strands can carry"),
    ("tubes", "penne and rigatoni",
     "a baked dish, and a thick sauce that fills the tube"),
    ("twists and shells", "fusilli, farfalle and conchiglie",
     "a sauce with bits in it that needs something to cling to, and pasta salad"),
    ("tiny shapes", "orzo and stelline", "soup, and a salad that should not be all bulk"),
    ("sheets", "lasagne", "a bake, layered instead of tossed"),
    ("filled", "ravioli and tortellini", "a meal on its own with butter or a light sauce"),
)

KINDS_ASK = ("kinds of pasta", "types of pasta", "sorts of pasta", "varieties of pasta",
             "kind of pasta", "type of pasta", "sort of pasta", "shapes of pasta",
             "shape of pasta", "what shapes", "which shapes", "what kinds", "what types",
             "different types", "different kinds", "how many types", "how many kinds")


def _the_kinds(memory=None, understood=None):
    """The families of shape, what each is for, and the times those shapes already have."""
    members = ["%s (%s) for %s" % (family, shapes, for_what)
               for family, shapes, for_what in PASTA_KINDS]
    return ("Pasta comes down to six families, and the family decides the job: "
            + "; ".join(members[:-1])
            + " and " + members[-1] + ". The time goes by the shape as well: 8 to 9 minutes for "
            "thin strands, 10 to 11 for spaghetti and penne, 11 to 13 for rigatoni and "
            "tagliatelle, and 3 to 4 for the filled ones. Fresh pasta is 2 to 3 minutes, not the "
            "packet time.")


def _minutes(words):
    """The minutes for the shape the line names, or the range that covers dried pasta."""
    joined = " ".join(words)
    if "noodle" in joined or "noodles" in joined:
        return NOODLES
    for keys, minutes in PASTA_MINUTES:
        if any(key in joined for key in keys):
            return "About %s for that one." % minutes
    return "Dried pasta is 8 to 12 minutes, depending on the shape: 8 to 9 for thin spaghetti."


def _pasta_time(memory, understood):
    """The time by shape, then the two things that decide whether it is right."""
    words = [str(word).lower() for word in (understood.get("words") or [])]
    if "fresh" in words:
        # shop-bought fresh pasta is a different animal from dried, and 3 minutes answered with
        # "8 to 12" would be wrong
        first = ("Fresh pasta is 2 to 3 minutes, not the packet time: it is done the moment it "
                 "floats and loses its chalky middle, so taste a strand at 2 minutes.")
    else:
        first = _minutes(words)
    return (first + " Use a big pan with about 10g of salt per litre, keep a mug of the water for "
            "the sauce, and taste a piece a minute before the packet says: shapes differ, and so "
            "do pans.")


# Which shape for which dish, because "which one holds a heavy ragu" was refused and "what pasta
# for a heavy ragu" was answered with a stodgy-rice card. One line per dish: the shapes that hold
# it, and the reason - the sauce clings to a twist, sits in a tube and slides off a strand.
PASTA_FOR_DISH = (
    (("ragu", "bolognese", "meat sauce", "slow cooked", "slow-cooked"),
     "Tagliatelle or pappardelle, or rigatoni",
     "a wide strand has the surface a thick meat sauce clings to, and a tube holds it; spaghetti "
     "is fine but most of the sauce ends up on the plate"),
    (("carbonara", "creamy sauce", "cream sauce", "cheese sauce", "macaroni cheese",
      "mac and cheese"),
     "Spaghetti or rigatoni",
     "the sauce is a coating rather than a filling, so a long strand or a tube both work, and "
     "the ridges on rigatoni hold it"),
    (("bake", "baked", "oven", "lasagne", "lasagna"),
     "Penne, rigatoni or lasagne sheets",
     "a tube keeps its shape through the oven and the sauce gets inside it, where a long strand "
     "turns to one lump"),
    (("soup", "broth", "minestrone"),
     "Orzo, stelline or any tiny shape",
     "small shapes cook in the broth and sit on the spoon, and orzo thickens it a little"),
    (("salad", "cold"),
     "Fusilli, farfalle or penne",
     "the nooks and the flat middles catch the dressing, and none of them clump when they are "
     "cold"),
    (("pesto",),
     "Trofie, fusilli or linguine",
     "trofie is the shape pesto comes from, and the others give it something to cling to"),
    (("seafood", "prawns", "prawn", "clams", "mussels"),
     "Linguine or spaghetti",
     "a long strand twines round the shellfish and the sauce stays light instead of collecting "
     "in a tube"),
)

DISH_WORDS = tuple(word for keys, _shapes, _why in PASTA_FOR_DISH for word in keys)

# NOT_A_TIME holds "salad" and "bake" because a bake or a salad is not a boiling time, but both
# are dishes someone asks which shape to use for, so the two rows about shapes drop those words
# from the list they stand down for.
NOT_A_DISH = tuple(word for word in NOT_A_TIME if word not in DISH_WORDS)

# A fault in the dish is not a question about the shape. "my pasta salad is watery" named a salad
# and the shape row answered it with the shapes that hold a dressing, when the fix was the salt
# and the drain; "the lasagne is dry" and "my pasta bake is bland" the same. The fault rows read
# the dish, so this row stands aside for the words a fault is said in.
_A_FAULT_IN_THE_DISH = ("watery", "soggy", "limp", "dry", "drier", "bland", "tasteless",
                        "mushy", "stodgy", "sticky", "gluey", "overcooked", "burnt",
                        "salty", "too salty", "undercooked", "stale")


def _for_the_dish(memory=None, understood=None):
    """The shapes for the dish the line names, then why those and not the ones next to them."""
    said = " ".join(str(word).lower() for word in (understood.get("words") or []))
    said = said or str(understood.get("clean") or "").lower()
    for keys, shapes, why in PASTA_FOR_DISH:
        if any(key in said for key in keys):
            return "%s, because %s." % (shapes, why)
    return ("Match the shape to the sauce rather than to the packet: a thick meat sauce wants a "
            "wide strand or a tube, a thin one wants a long strand, and a bake wants penne or "
            "rigatoni.")


ENTRIES = [
    # The shapes asked about as a set: "what are the different types of pasta", "what kinds of
    # pasta are there", "how many shapes of pasta", which main refused. The families are the
    # answer, and the times in the table behind them are already in PASTA_MINUTES.
    # Which shape for the dish in the line: "which pasta holds a heavy ragu", "what pasta for a
    # lasagne", the second turn of a "what are the types of pasta" conversation.
    entry("pasta-for-dish", (("pasta", "spaghetti", "penne", "fusilli", "rigatoni", "tagliatelle",
                              "linguine", "farfalle", "conchiglie", "ravioli", "tortellini",
                              "macaroni", "orzo", "trofie", "pappardelle"), tuple(DISH_WORDS)),
          _for_the_dish,
          # the timing, the pan, the portion, the keeping and the swap questions are other rows',
          # and so is a recipe: "spaghetti bolognese recipe" is the sauce's method and its time,
          # not a question about which shape to put it on.
          avoid=NOT_A_DISH + _A_FAULT_IN_THE_DISH
          + ("how long", "how much", "per person", "portion", "portions",
                              "calories", "carbs", "instead", "substitute", "swap", "stand in",
                              "replace", "difference between", "how do i", "recipe", "recipes",
                              "how to make", "how do i make", "im making", "i am making",
                              "im cooking", "i am cooking"),
          bias=2),

    entry("pasta-kinds", (("pasta", "spaghetti", "penne", "fusilli", "rigatoni", "tagliatelle",
                           "linguine", "farfalle", "conchiglie", "ravioli", "tortellini",
                           "lasagne", "orzo", "macaroni"), tuple(KINDS_ASK)),
          _the_kinds,
          # A time, a pan, a portion, a keeping question or a swap names one shape or one job and
          # is another entry's answer. A bake that asks for the shapes still gets this row: the
          # set is what was asked for.
          avoid=NOT_A_DISH + ("how long", "how much", "per person", "portion", "portions",
                              "gluten", "free", "vegan", "vegetarian", "calories", "carbs",
                              "instead", "substitute", "swap", "stand in", "replace",
                              "which one", "which is better", "difference between"),
          bias=1),

    # The shape and a word for timing. pasta-cook (in cooking.py) answers the same lines with the
    # pan method and no number, so this one has to win them: the phrase "how long" scores more
    # than the single cooking words it competes with, and the bias breaks any tie.
    entry("pasta-time", (("pasta", "spaghetti", "penne", "fusilli", "macaroni", "rigatoni",
                          "tagliatelle", "linguine", "farfalle", "orecchiette", "tortellini",
                          "ravioli", "gnocchi", "cannelloni", "noodles", "noodle"),
                         tuple(sorted(TIME_ASK))),
          _pasta_time,
          # "how do i cook pasta" wants the pan method, which is pasta-cook's answer, and the
          # keeping, portion and sticking questions are their own entries
          avoid=NOT_A_TIME,
          bias=2),

    # Which pan to use was six hedges in a row: "which pan for pasta", "what size pan for
    # pasta", "do i need a big pan for pasta". The pan care entries name a pan but not pasta,
    # and the time entry names pasta but not a pan, so the question fell between them.
    entry("pasta-pan", (("pasta", "spaghetti", "penne", "fusilli", "macaroni", "rigatoni",
                         "tagliatelle", "linguine", "farfalle", "orecchiette", "tortellini",
                         "ravioli", "gnocchi", "cannelloni", "noodles", "noodle"),
                        ("pan", "pans", "pot", "pots", "saucepan", "saucepans", "wok",
                         "size", "big", "large", "wide", "deep", "enough room")),
          "A big pot with room to spare: about 5 litres of water for 500g of pasta, so it comes "
          "back to the boil quickly and the strands do not stick together. A wide shallow pan or "
          "a large frying pan is fine for long shapes if you stir, and easier for a small "
          "portion; any deep saucepan works for short shapes.",
          # A time, a bake, a portion or a keeping question is another entry's, and a pan that is
          # burnt or non-stick is about the pan, not about the pasta.
          avoid=NOT_A_TIME + ("burnt", "burned", "non stick", "nonstick", "non-stick", "cast iron",
                              "coating", "season", "seasoning", "clean", "wash", "scour"),
          bias=1),

    # Pasta in the oven is a different question from pasta in water: it wants a dish and a bake
    # time. Keyed on the oven words only, because "how long" alone would take the fresh pasta
    # and lasagne-sheet lines.
    entry("pasta-bake", (("pasta", "lasagne", "lasagna", "macaroni", "cannelloni", "pasta bake"),
                         ("in the oven", "oven", "bake", "baked", "baking", "pasta bake")),
          "Cook the pasta 2 minutes short of the packet, mix it with a sauce that is wetter than "
          "you think, top it and bake it 20 to 25 minutes at 200C (180C fan) until the top is "
          "browned and bubbling. Cover it with foil for the first 15 minutes and the middle stays "
          "loose instead of drying out.",
          # A first-person line is somebody saying what they are cooking, and the plan for that
          # dish answers it ("im cooking a pasta bake for eight people" wants this bake's time).
          # The technique question this entry is for has no first person in it.
          avoid=("boil", "boiling", "water", "portion", "portions", "per person", "dry", "dried",
                 "leftover", "left over", "freeze", "reheat", "how many",
                 "im making", "i am making", "im cooking", "i am cooking", "im doing",
                 "i am doing", "im baking", "i am baking", "we are making", "we are cooking"),
          bias=1),

    # A squash is not a strand. "How long do i cook spaghetti squash" was getting the pasta pan
    # method, and "10 to 11 minutes" leaves the squash raw.
    entry("squash-roast", (("squash", "spaghetti squash", "butternut", "pumpkin", "acorn squash"),
                           ("roast", "roasted", "roasting", "oven", "bake", "baked", "cook",
                            "cooked", "cooking", "long", "time", "minutes")),
          "Halve it, scoop out the seeds and roast it cut side down at 200C for 35 to 40 minutes, "
          "until a knife goes into the flesh like butter; spaghetti squash wants 40 to 45, then "
          "fork it into strands. A whole one takes nearer an hour.",
          # the garden, the sport and the drink are other entries: this is the vegetable
          avoid=("blossom end", "rot", "growing", "grow", "seedling", "plant", "plot", "soil",
                 "court", "racket", "game", "player", "drink", "cordial", "juice", "sirop",
                 "seeds to sow", "variety"),
          bias=1),

    # "my spaghetti went mushy" was answered by the rice entry, because gluey grains read as
    # rice. Overcooked pasta is its own fault with its own fix.
    entry("pasta-soft", (("pasta", "spaghetti", "penne", "macaroni", "fusilli", "tagliatelle",
                          "rigatoni", "linguine", "noodles", "tortellini"),
                         ("mushy", "soggy", "overcooked", "over cooked", "too soft", "soft",
                          "slimy", "ruined", "sticky", "went wrong")),
          "Overcooked pasta has taken on water and lost its bite, so drain it now and stop the "
          "cooking under cold water. Toss it straight into a thick sauce - a ragu, a bake, or "
          "tomato with a spoon of cream cheese - rather than a thin one it cannot hold, and it "
          "will pass. Next time taste a piece a minute before the packet time.",
          avoid=("rice", "clump", "clumps", "together", "stuck", "sticking", "pan", "how long",
                 "minutes", "portion", "leftover", "sauce recipe", "in the oven", "bake"),
          bias=2),

    # "how do i drain pasta" was a punt, and so were "how do i strain spaghetti" and "how do i
    # drain noodles": the rinse row in cooking_entries.py keys the verb "rinse" and these lines
    # never say it, and the no-kit table only fires when a tool is *missing* ("drain the pasta
    # without a colander"), so the plain step of getting the water off had no row in any domain.
    # The same word sent a *food* line to the plughole: "how do i drain broccoli" and "how do i
    # drain chickpeas" got the weekly kettle down the waste pipe, because `drain-clean` in
    # cleaning.py took a bare "how" as its second key word and any line with "drain" in it plus
    # "how" scored. The rule is one rule - a draining line that names food is the step between
    # the pan and the plate - so it is one row, keyed on the draining words and the food, and
    # food covers the shapes of pasta and the things that come out of a pot of water.
    entry("drain-the-pot", (("drain", "drains", "draining", "drained", "strain", "strains",
                             "straining", "strained", "colander", "sieve"),
                            ("pasta", "spaghetti", "penne", "macaroni", "linguine", "fusilli",
                             "tagliatelle", "orzo", "noodles", "noodle",
                             "potato", "potatoes", "new potatoes", "veg", "vegetables",
                             "broccoli", "cauliflower", "carrots", "carrot", "greens", "peas",
                             "green beans", "spinach", "kale", "cabbage", "courgette",
                             "courgettes", "chickpeas", "lentils", "beans", "sweetcorn")),
          "Tip the whole pan into a colander in the sink, and keep a mugful of the water back "
          "first, because it is full of starch and it loosens a sauce that looks dry. Drain it "
          "the moment it is al dente or just tender - it keeps cooking in its own heat - then "
          "shake it dry and get it into the sauce or back into the warm pan, since anything left "
          "standing in a colander goes sticky within a couple of minutes. No colander is no "
          "problem: hold the lid on with a gap and pour slowly.",
          # a time, a bake, a portion or a keeping question is another entry's, and a rinse is
          # the row that owns that word: this row is the step between the pan and the sauce
          avoid=NOT_A_TIME + ("rinse", "rinsing", "washed", "wash", "fridge", "freezer",
                              "freeze", "leftover", "left over", "reheat", "rice", "sauce",
                              "bake", "oven", "salad", "cheese", "tin", "tinned"),
          bias=2),

    # Lasagne sheets are the one pasta nobody cooks in a pan first, and "how long do i cook
    # lasagne sheets" was being answered by the bed-sheet entry. The answer depends on which kind
    # of sheet someone has, so it names all three.
    entry("lasagne-sheets", (("lasagne", "lasagna"),
                             ("sheets", "sheet", "pre cook", "precook", "pre cooked", "boil",
                              "soak", "how long", "cook", "cooking", "fresh", "dried")),
          "Fresh lasagne sheets need no cooking at all: layer them straight in. Dried sheets made "
          "without egg go in dry too, as long as the sauce is wet enough; dried egg pasta is "
          "better for 3 or 4 minutes in boiling water first. Either way rest the finished dish 10 "
          "minutes before cutting so it holds together.",
          # the bake, the portion, the keeping and the recipe questions are other entries
          avoid=("how long do i bake", "in the oven", "oven", "reheat", "freeze", "freezer",
                 "calories", "per person", "how many", "how much", "leftover", "left over",
                 "vegetarian", "vegan", "recipe", "keep", "keeps", "keeping", "fridge", "store",
                 "storage", "safe", "next day", "gone off"),
          bias=1),
]
