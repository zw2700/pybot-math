"""Standing in for an ingredient: what to use instead of the thing that has run out.

The answers lane owns this domain. A cook who has started a recipe and found the butter gone
asks one thing, in a dozen shapes - "what can i use instead of butter", "i've no butter, what
can i use", "can i use oil instead of butter", "butter substitute" - so the shape of the ask is
one shared tuple (SWAP_ASK below) on every row, and the ingredient is the row's own key.

Why this is a domain of its own rather than a corner of cooking.py: the rows that answer a
substitution question elsewhere are keyed on their own subject, and a loose ask word of theirs
takes the swap line first. `oil-smoking` keys on the fat words including "butter" and asks for
"can i use" (that is how "can i still use it" after frying is asked), so "what can i use instead
of butter" was answered with where to pour the pan of spent oil. The nutrition rows do the same
for sugar, honey and chocolate ("swap rather than erase" is an answer about cutting down, not
about baking), and the keeping rows take anything that names a food with "out of" in it. Each
row here is therefore gated twice: the ingredient has to be named, and the line has to be asking
for a stand-in. A line that is only about the ingredient still reaches the row it should, which
is why every entry below names in its `avoid` list the other questions about its own ingredient
(keeping it, cooking with it, how much of it, what it does to you).

The `bias` on these rows is the one place in the knowledge base where more than 2 is right, and
it is measured rather than taste. A swap row scores 5 on a line like "what can i use instead of
butter" - the ingredient's word and the phrase "instead of" - and `oil-smoking` scores the same 5
and carries bias 5, because its key holds the fat words and its ask holds "can i use" (how "can
i still use it" after frying is asked); it had to outrank the pudding rows and did it that way.
So any row here whose ingredient is a fat needs 6 to be in front of it, and that is the whole
of FAT_SWAP. Every other row needs 2, which is the nudge cooking.py's own swap rows use to beat
the ingredient rows beside them.
"""
import re

from .lookup import entry

# The topics this domain answers. Both already exist (cooking.py declares the same pair), so the
# union bot/modules/answers.py publishes does not change: this file only takes back the lines
# those rows answer wrongly.
ANSWERS = ("cooking", "food-and-drink")

# The words that say "the recipe wants this and I haven't got it". They name the ask, never the
# ingredient, so the same tuple is a key part and the hard gate on every row: without one of
# them the line is about the ingredient itself and belongs to the row that answers that.
SWAP_ASK = ("instead", "instead of", "substitute", "substitutes", "substituting", "swap",
            "swaps", "swapping", "replace", "replacing", "replacement", "alternative",
            "stand in for", "stand-in for",
            # a shortage is the same question as a swap
            "ran out", "run out", "im out of", "i'm out of", "we're out of", "were out of",
            "im all out", "i'm all out", "none left", "all out of", "no longer have",
            "dont have", "don't have", "havent got", "haven't got", "i have no", "ive no",
            "i've no", "ive got no", "i've got no", "we have no", "theres no", "there's no",
            "weve got no", "we've got no", "theyre all gone", "they're all gone",
            # the short way of asking, which is how a swap is usually put to a person
            "what can i use", "what do i use", "what should i use", "anything else",
            "something else", "what else")

# Enough to be in front of `oil-smoking` on a swap line, which keys on the fat and carries bias 5
# (see the module docstring). Used only by the rows whose ingredient that entry also names.
FAT_SWAP = 6


def _other_way_round(*others):
    """The phrases a line uses when the *other* ingredient is the one being replaced.

    "Can I use oil instead of butter" is a question about the pair, and cooking.py already
    answers those pairs one by one with its own verdict rows ("yes, use three-quarters of the
    weight and expect a denser crumb"). A row here is the answer to a missing ingredient, so it
    stands down whenever the line names another ingredient as the one being swapped out - which
    is the only reading of "instead of X" when X is not this row's own word.
    """
    return tuple(phrase for word in others
                 for phrase in ("instead of " + word, "in place of " + word))

# The other questions about the same ingredient, which are not a swap. Kept in one place because
# every row here needs the same idea: a swap row must never answer "how long does it keep", "how
# much of it should I eat" or "how do I cook it".
NOT_A_SWAP = ("keep", "keeps", "keeping", "kept", "store", "stored", "storing", "how long",
              "last", "lasts", "freeze", "frozen", "gone off", "off", "fridge", "cupboard",
              "calories", "healthy", "unhealthy", "good for you", "bad for you", "diet",
              "cut down", "cut out", "give up", "lose weight", "how much", "how many")

# The ingredient is not the subject of these: a line that asks about an allergy, a pregnancy,
# a patch of the garden, a stain or the dog has the word but not the question, and the row for
# the ingredient must leave it alone. Kept apart from NOT_A_SWAP because the reason differs -
# that one is the other questions about the food, this one is the food as something else.
# A dish named around the swap ("no ricotta for the lasagne") is *not* listed anywhere: the
# dish is why the cook is asking, and an avoid word for it silently stood the row down.
NOT_A_SWAP_EITHER = ("pregnant", "pregnancy", "breastfeeding", "allergy", "allergic",
                     "intolerance", "safe to eat", "healthy", "healthiest", "benefits",
                     "grow", "growing", "plant", "planting", "blooms", "bloom",
                     "clean", "cleaning", "stain", "stains", "smell", "smells", "dogs",
                     "cats", "parrots", "lice", "burns", "plaster", "monkeys", "symptoms",
                     "side effects", "too much")

def _the_chilli_swap(memory, reading):
    """Which form of chilli the line is short of, and what stands in for that one."""
    text = " " + str((reading or {}).get("clean") or "").lower() + " "
    after = " ".join(_swapped_out(text))
    short_of_powder = ("powder" in after or "flakes" in after
                       or re.search(r"\b(?:no|without|out of|none left of)\s+(?:\w+\s+)?"
                                    r"chilli (?:powder|flakes)\b", text))
    if short_of_powder:
        return ("Paprika with a pinch of cayenne is the closest thing to chilli powder: about "
                "four parts paprika to one of cayenne, and a little more cayenne if you want it "
                "hot. For flakes, crushed dried chillies or a pinch of cayenne do the job.")
    return ("A quarter teaspoon of chilli powder or a pinch of flakes stands in for one fresh "
            "chilli, and hot sauce works in a sauce rather than where the chilli is sliced over "
            "the top.")


# What to put in the place of a food the person has said they will not eat. A swap is the same
# question whether the kitchen is out of a thing or the person cannot stand it: "i hate broccoli
# what can i have instead" was a search hedge on main, and the onion, butter and cream swaps
# beside it answered the shortage shape all along.
TASTE_SAID = ("hate", "hates", "hated", "hateful", "dont like", "don't like", "do not like",
              "doesnt like", "doesn't like", "does not like", "cant stand", "can t stand",
              "can't stand", "cannot stand", "not a fan of", "not a fan", "not keen on",
              "not fussed on", "dislike", "dislikes", "loath", "loathe", "cant eat", "can't eat")

# The words that ask what to have instead. A taste with none of these in the line is the store's
# to say back, so this tuple is the second gate on the row.
ASKS_FOR_A_SWAP = ("instead", "what else", "anything else", "something else", "what can i have",
                   "what could i have", "what should i have", "what can i eat", "what should i eat",
                   "what do i eat", "else can i eat", "leave it out", "leave them out",
                   "leave out", "skip it", "without", "what can i use", "what do i use",
                   "what should i use", "substitute", "swap", "replace", "alternative",
                   "what can i put", "what can i have on", "stand in")

# The ask with no stand-in word in it: the line names the food and says it will not have it.
LEAVE_OUT_ASK = ("leave it out", "leave them out", "leave out", "leaving it out", "skip it",
                 "skip them", "go without", "do without")

REFUSED_ASK = TASTE_SAID + ASKS_FOR_A_SWAP

# The food, and what to put in its place. Written per food rather than as a template, because
# what to say about a hated mushroom is about the savoury depth it was providing.
REFUSED_FOR = {
    "broccoli": ("Cauliflower does the same job in a bake or a curry, and beans, romanesco or "
                 "frozen peas are the easy green on the side. If it is the sulphury smell you "
                 "cannot stand, roast it hard with oil and a squeeze of lemon rather than "
                 "boiling it - that takes the edge off."),
    "calabrese": ("Cauliflower, romanesco or green beans stand in for it in a bake or a curry, "
                  "and roasting it hard with oil and lemon softens the sulphury edge."),
    "cauliflower": ("Broccoli, celeriac or roast carrots do the bulk in a bake, and a spoon of "
                    "grain mustard in the cheese sauce covers the gap."),
    "mushroom": ("Aubergine or courgette takes the same space in a bake or a sauce, and a splash "
                 "of soy or a spoon of miso gives back the savoury depth they were there for. In "
                 "a mince, a tin of lentils does it too."),
    "mushrooms": ("Aubergine or courgette takes the same space in a bake or a sauce, and a splash "
                  "of soy or a spoon of miso gives back the savoury depth they were there for. In "
                  "a mince, a tin of lentils does it too."),
    "tomato": ("Roast red peppers or a spoon of tomato puree in the base give the sweetness "
               "without the pieces, and lemon or a dash of vinegar at the end gives back the "
               "acidity. Raw in a salad or a sandwich, cucumber, radish or peppers give the "
               "crunch and the juice. If it is the texture, passata is a different thing in the "
               "mouth from a chopped tomato."),
    "tomatoes": ("Roast red peppers or a spoon of tomato puree in the base give the sweetness "
                 "without the pieces, and lemon or a dash of vinegar at the end gives back the "
                 "acidity. Raw in a salad or a sandwich, cucumber, radish or peppers give the "
                 "crunch and the juice. If it is the texture, passata is a different thing in "
                 "the mouth from a chopped tomato."),
    "onion": ("Leek is the closest, milder by weight and slower to soften; shallots are sweeter, "
              "spring onions sharper and better raw, and a teaspoon of onion powder stands in for "
              "one onion in a stew. Nobody will notice it gone from a sauce."),
    "onions": ("Leek is the closest, milder by weight and slower to soften; shallots are sweeter, "
               "spring onions sharper and better raw, and a teaspoon of onion powder stands in "
               "for one onion in a stew. Nobody will notice it gone from a sauce."),
    "garlic": ("Leave it out - nothing collapses. The greens of a leek or a spring onion give "
               "the savoury note without the heat, and a pinch of asafoetida does it if you have "
               "some. If it is the little bits you dislike rather than the taste, garlic oil or "
               "a whole crushed clove fished out at the end gives the flavour and none of them."),
    "peas": ("Sweetcorn, broad beans, edamame or fine green beans all go in at the same minute "
             "at the end, and frozen sweetcorn is the one nobody argues with."),
    "courgette": ("Green beans or spinach go in for the same bulk, and aubergine or peppers "
                  "roast in the same tray. Courgette adds water, so whatever you use, use less "
                  "stock."),
    "aubergine": ("Courgette, peppers or big flat mushrooms roast in the same tray and take the "
                  "same oil, and they do not need salting first."),
    "spinach": ("Kale or chard wilt in the same minute, and frozen peas or a handful of beans go "
                "in where the spinach was going. If it is the slime, wilt it for 30 seconds and "
                "squeeze it dry in a sieve."),
    "cabbage": ("Spring greens, kale or a bag of coleslaw mix do the same job, and they cook "
                "faster than a hard white cabbage."),
    "carrot": ("Butternut squash, parsnip or swede roast and mash in its place. If it is the raw "
               "carrot in a salad, cucumber sticks or peppers give the crunch."),
    "carrots": ("Butternut squash, parsnip or swede roast and mash in its place. If it is the raw "
                "carrot in a salad, cucumber sticks or peppers give the crunch."),
    "celery": ("Leek or fennel go in at the same point of a base, and a pinch of celery salt "
               "gives the flavour where the stick was. If it is the strings, peel them off with a "
               "potato peeler."),
    "pepper": ("Courgette or mushroom takes the space in a tray bake, and a teaspoon of paprika "
               "gives the sweetness people usually wanted from it."),
    "peppers": ("Courgette or mushroom takes the space in a tray bake, and a teaspoon of paprika "
                "gives the sweetness people usually wanted from it."),
    "beetroot": ("Roast carrots or sweet potato sit in the same tray and mash the same way, "
                 "without the earthiness you are trying to get away from."),
    "fish": ("Chicken, eggs, beans or halloumi give you the protein the fish was for, and a white "
             "fish is far milder than an oily one if it was the fishiness you could not take. "
             "Fish cakes and fish pie with a white sauce and plenty of parsley are how most "
             "people who say they hate fish eat fish."),
    "coriander": ("Flat-leaf parsley does the same job in a salad or on top of a curry, and "
                  "basil or mint if the dish leans that way. If it tastes of soap to you, that is "
                  "the gene, not fussiness."),
}


def _asks_for_a_swap(understood):
    """Whether the line asks what to have in the place of the food it names.

    The gate on the row itself: a taste with no ask in it is somebody saying what they will not
    eat, and the store answers that with a note, or the food's own "no onion then" plan row does.
    Letting this row win those lines took the answer away rather than giving a better one.
    """
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    if not any(phrase in text for phrase in ASKS_FOR_A_SWAP):
        return False
    # "what can i use instead of tomato puree" is the shortage question: the row for tomato
    # puree answers it, and this row stands down before it can win the line and hand back
    # nothing. The stand-down is here as well as in `_refused_food` because a callable reply
    # that returns nothing still costs the line the row that was asked for.
    for phrase in ("instead of", "in place of", "substitute for"):
        at = text.find(phrase)
        if at >= 0 and any(name in text[at:] for name in REFUSED_FOR):
            return False
    return True


def _refused_food(memory, understood):
    """What to put in the place of the food the line says it will not eat.

    A line that names the food after "instead of" is the shortage question, not the taste: the
    row for that food answers "what can i use instead of mushrooms" with tinned or frozen ones,
    which is the right answer to a pantry and the wrong one to a person who cannot stand them.
    This row stands down there and the food's own swap row takes the turn.
    """
    said = " " + " ".join(str(word).lower() for word in (understood.get("words") or [])) + " "
    text = " " + str((understood or {}).get("clean") or "").lower() + " "
    if not any(phrase in text for phrase in ASKS_FOR_A_SWAP):
        # A taste on its own is the store's, which says it back and remembers it ("Noted: you
        # don't like mushrooms on your pizza"). Only a line that asks what to have in its place
        # is this row's, and then the swap is the answer rather than the note.
        return None
    for phrase in ("instead of", "in place of", "substitute for"):
        at = text.find(phrase)
        if at >= 0 and any(name in text[at:] for name in REFUSED_FOR):
            return None
    for name in sorted(REFUSED_FOR, key=len, reverse=True):
        if (" " + name + " ") in said or said.strip() == name:
            return REFUSED_FOR[name]
    return None



ENTRIES = [
    # A food the person will not eat, and what to put there instead. The row is keyed on the
    # food and gated on the refusal, so "i hate broccoli" alone is not this row's line, and a
    # shortage of the same food keeps its own swap row above.
    entry("swap-what-i-will-not-eat",
          # The taste is the key, not the food: keying the twenty foods in REFUSED_FOR made the
          # swap domain's own word list so much less rare that "what can i use instead of tomato
          # puree" lost its row and got a hedge. "leave it out" is here because it is how the
          # question is put with no stand-in word at all ("can i leave out the garlic").
          (TASTE_SAID + LEAVE_OUT_ASK, REFUSED_ASK),
          _refused_food, bias=2, guard=_asks_for_a_swap,
          # the refusal is the ask here rather than a shortage, and "what else" is how the
          # substitute is asked for after it
          ask=SWAP_ASK + REFUSED_ASK,
          avoid=NOT_A_SWAP + ("grow", "growing", "plant", "planting", "allotment", "recipe",
                              "cook", "cooking", "kitchen", "job", "work", "monday", "school",
                              "commute", "weather", "rain", "garden", "slug", "slugs", "pigeon",
                              "pigeons", "cats", "cat", "dog", "child", "children", "toddler",
                              "baby", "kids", "son", "daughter", "husband", "wife", "partner",
                              "mum", "dad", "guests", "guest", "allergy", "allergic")),
    # The one that started this: on main the plain butter question reached the pan of spent
    # frying oil, because that row's ask holds "can i use" and its key holds "butter". The bake
    # and the pastry questions are cooking.py's own swap rows and are left alone here.
    entry("swap-butter-plain", (("butter", "butters", "salted butter", "unsalted butter"),
                                SWAP_ASK),
          "Margarine at the same weight, or a neutral oil at about three-quarters of the weight "
          "in cakes, muffins and pancakes. For greasing a tin or frying an egg, any cooking oil "
          "does the same job; keep the butter where its taste is the point, as in shortbread and "
          "buttercream.",
          avoid=NOT_A_SWAP + _other_way_round("margarine", "oil", "lard", "ghee", "shortening") + (
                              "cake", "cakes", "baking", "bake", "pastry", "shortbread",
                              "buttercream", "biscuit", "biscuits", "cookie", "cookies", "scone",
                              "scones", "brownie", "brownies", "flapjack", "soften", "softened",
                              "room temperature", "smoke", "smoked", "smoking", "melt", "melted"),
          ask=SWAP_ASK, bias=FAT_SWAP),
    entry("swap-margarine", (("margarine", "marg", "spread", "sunflower spread"), SWAP_ASK),
          "Butter swaps in at the same weight, and so does a block margarine meant for baking. "
          "The soft spread in a tub is about a fifth water, so it gives a wetter, paler bake - "
          "use it for spreading, not for pastry.",
          # butter stands this row down: "can i use margarine instead of butter" wants the butter
          # row's answer ("margarine at the same weight"), and on main it got the frying-pan one
          avoid=NOT_A_SWAP + _other_way_round("butter", "oil", "lard", "ghee", "shortening") + (
                              "cake", "cakes", "pastry", "bake", "baking", "biscuit", "biscuits",
                              "cookie", "cookies", "scone", "scones", "sponge", "brownie",
                              "brownies", "muffin", "muffins", "healthy", "unsaturated",
                              "cholesterol"),
          ask=SWAP_ASK, bias=FAT_SWAP),
    # Oil is asked for in a cake far more often than it is asked about in a pan, and the pan is
    # the oil-smoking row's. The key's second part is the bake, so a frying line stays there.
    entry("swap-lard", (("lard", "ghee", "dripping", "shortening", "vegetable shortening"),
                        SWAP_ASK),
          "Butter at the same weight for pastry and puddings, or a block margarine for a meat-free "
          "one. For frying, ghee and clarified butter take the heat like lard does; dripping is "
          "closest in taste, so use it where the fat is the flavour.",
          ask=SWAP_ASK, bias=FAT_SWAP),
    entry("swap-oil-baking", (("oil", "vegetable oil", "sunflower oil", "rapeseed oil"),
                              ("cake", "cakes", "baking", "bake", "brownies", "brownie", "muffin",
                               "muffins", "sponge", "loaf", "carrot cake", "banana bread",
                               "pancakes", "flapjacks", "traybake", "tray bake")),
          "Melted butter at a quarter more than the oil - 100ml of oil becomes 125g of melted "
          "butter - or the same amount of a block margarine. For a lighter bake, replace up to "
          "half the oil with yoghurt or apple sauce; a low-fat spread holds too much water to "
          "take the oil's place.",
          # "can i use oil instead of butter" is the other direction, which cooking.py answers with
          # its own verdict row: this row is only for the oil that is missing, not the butter.
          avoid=NOT_A_SWAP + _other_way_round("butter", "margarine", "lard", "ghee") + (
                              "fry", "frying", "fried", "chips", "chip pan", "deep fryer",
                              "fryer", "smoke", "smoked", "smoking", "reuse", "used oil",
                              "old oil", "engine", "car", "olive oil", "healthy", "olive",
                              "cholesterol"),
          ask=SWAP_ASK, bias=4),
    entry("swap-oil-plain", (("oil", "cooking oil", "vegetable oil", "sunflower oil"),
                             SWAP_ASK),
          "For frying and roasting, melted butter or margarine works at the same amount; turn "
          "the heat down a little, because butter burns sooner than oil. In a cake, oil-for-"
          "butter is the other direction: use three-quarters of the weight of the butter the "
          "recipe asks for.",
          avoid=NOT_A_SWAP + _other_way_round("butter", "margarine", "lard", "ghee") + (
                              "cake", "cakes", "baking", "bake", "brownies", "brownie", "muffin",
                              "muffins", "sponge", "smoke", "smoked", "smoking", "reuse",
                              "used oil", "old oil", "engine", "car", "cars", "sumps", "sump",
                              "olive oil", "healthy", "cholesterol", "dispose", "recycle",
                              "throw away", "get rid"),
          ask=SWAP_ASK, bias=FAT_SWAP),
    # The nutrition row answers "how do i swap sugar for healthier snacks", which is a different
    # question from what stands in for 100g of caster sugar in a sponge.
    entry("swap-sugar", (("sugar", "caster sugar", "granulated sugar", "white sugar",
                          "brown sugar", "icing sugar"), SWAP_ASK),
          "In baking, caster and granulated are the same thing and brown sugar swaps for white "
          "at the same weight, with a little more moisture. To use less, replace up to a quarter "
          "of the sugar with mashed banana or apple sauce and keep the rest - taking all of it "
          "out changes how the bake sets.",
          # a line that names honey at all is asking about honey in the sugar's place, which the
          # honey verdict answers ("it is sweeter and wetter, use three-quarters"), so it is not
          # this row's even in its own words
          avoid=NOT_A_SWAP + _other_way_round("honey", "syrup", "treacle") + (
                              "honey", "maple", "maple syrup", "golden syrup", "treacle",
                              "teeth", "children", "kids", "baby", "addiction", "free sugar",
                              "fizzy", "squash", "snacks", "sweets", "diabetes", "blood sugar",
                              "craving", "cravings"),
          ask=SWAP_ASK, bias=4),
    entry("swap-honey", (("honey", "runny honey", "clear honey"), SWAP_ASK),
          "Golden syrup or maple syrup at the same weight, or 100g of sugar with an extra "
          "tablespoon of water for every 100g of honey. Honey is sweeter and wetter than sugar, "
          "so a bake takes about three-quarters of it plus a splash more liquid.",
          avoid=NOT_A_SWAP + _other_way_round("sugar", "syrup", "treacle") + (
                              "baby", "babies", "under one", "cough", "coughs", "sore throat",
                              "teeth", "diabetes", "blood sugar", "porridge", "toast", "tea"),
          ask=SWAP_ASK, bias=4),
    entry("swap-golden-syrup", (("golden syrup", "treacle", "black treacle", "dark treacle",
                                 "corn syrup"), SWAP_ASK),
          "Honey or maple syrup at the same weight in flapjacks, puddings and cakes. Dark treacle "
          "is stronger, so use half and make the rest up with honey; in a toffee or a fudge the "
          "syrup is doing the setting, so swap golden syrup for light corn syrup and nothing else.",
          avoid=NOT_A_SWAP + ("tin", "tins", "price", "buy"), ask=SWAP_ASK, bias=4),
    entry("swap-chocolate", (("dark chocolate", "milk chocolate", "cooking chocolate",
                             "plain chocolate", "chocolate"), SWAP_ASK),
          "For 25g of dark chocolate, use 3 level tablespoons of cocoa with a teaspoon of sugar "
          "and a teaspoon of butter or oil. Milk chocolate goes in at the same weight but is "
          "sweeter, so leave a spoonful of the recipe's sugar out.",
          avoid=NOT_A_SWAP + ("percentage", "squares", "eat", "eating", "bar", "bars", "mood",
                              "cocoa percentage", "caffeine"),
          ask=SWAP_ASK, bias=4),
    entry("swap-cream-cheese", (("cream cheese", "philadelphia", "soft cheese"), SWAP_ASK),
          "Mascarpone is the closest in a cheesecake or a frosting, loosened with a splash of "
          "milk. Full-fat Greek yoghurt works in a no-bake filling but tastes sharper, and "
          "blended cottage cheese is the low-fat version - drain it first or the bake turns wet.",
          avoid=NOT_A_SWAP + ("toast", "bagel", "bagels", "sandwich", "salmon"), ask=SWAP_ASK,
          bias=3),
    entry("swap-sour-cream", (("sour cream", "creme fraiche", "fromage frais"), SWAP_ASK),
          "Sour cream and creme fraiche stand in for each other one for one, and full-fat "
          "yoghurt at the same amount does the same job if it is stirred in off the heat so it "
          "does not split. In a cake or a marinade, buttermilk works; in a dip, thick yoghurt or "
          "soft cream cheese.",
          avoid=NOT_A_SWAP + ("dip", "baked potato", "jacket"), ask=SWAP_ASK, bias=3),
    entry("swap-mayonnaise", (("mayonnaise", "mayo", "salad cream"), SWAP_ASK),
          "Plain yoghurt is tarter and thinner, so mix it half and half with mayonnaise if there "
          "is a little left, or use salad cream for a sweeter sandwich. From nothing: whisk oil "
          "into a teaspoon of mustard and a splash of vinegar.",
          ask=SWAP_ASK, bias=4),
    entry("swap-vinegar", (("vinegar", "white wine vinegar", "cider vinegar", "malt vinegar",
                            "red wine vinegar", "rice vinegar", "sherry vinegar",
                            "balsamic vinegar", "balsamic"), SWAP_ASK),
          "Lemon or lime juice at the same amount in a dressing or a sauce, and white wine, "
          "cider and malt vinegar swap for each other freely. Where the vinegar is raising a "
          "cake, lemon juice does the same job; balsamic is too sweet for that.",
          avoid=NOT_A_SWAP + ("clean", "cleaning", "cleaned", "limescale", "kettle", "wash",
                              "washing", "weed", "weeds", "glass", "windows", "smell", "pickle",
                              "pickling", "descale"),
          ask=SWAP_ASK, bias=4),
    entry("swap-stock", (("stock", "stock cube", "stock cubes", "chicken stock",
                          "vegetable stock", "beef stock", "bouillon"), SWAP_ASK),
          "A stock cube or a teaspoon of bouillon powder in hot water is the quickest, and one "
          "cube makes about 500ml. With none in the cupboard, use the water the vegetables were "
          "boiled in with a splash of soy and a pinch of salt, or a glass of wine in a stew.",
          # "can i use a stock cube instead of stock" is the pair verdict's, and a line that
          # already names a cube is not asking what stands in for stock
          avoid=NOT_A_SWAP + ("cube", "cubes",
                              "make", "making", "carcass", "carcasses", "bone", "bones",
                              "shares", "market", "markets", "invest", "investing", "isa",
                              "buy", "buying", "sell", "selling", "price", "prices", "crash",
                              "dividend", "dividends"),
          ask=SWAP_ASK, bias=4),
    entry("swap-breadcrumbs", (("breadcrumbs", "bread crumbs", "panko", "breadcrumb"), SWAP_ASK),
          "Crushed crackers, cornflakes or crisps at the same weight, or a slice of stale bread "
          "whizzed in a blender. Oats work in meatballs and a crumble topping; in a fishcake or a "
          "burger, a spoonful of flour does the binding instead.",
          ask=SWAP_ASK, bias=4),
    entry("swap-parmesan", (("parmesan", "parmigiano", "pecorino", "grana padano"), SWAP_ASK),
          "Grana Padano is the nearest and cheaper, and Pecorino is sharper and saltier so use "
          "less of it. A mature cheddar melts more readily in a sauce but tastes quite different; "
          "for a vegetarian, check the cheese is made with a vegetarian rennet.",
          avoid=NOT_A_SWAP + ("vegetarian rennet", "rind"), ask=SWAP_ASK, bias=4),
    entry("swap-tomato-puree", (("tomato puree", "tomato paste", "tomato concentrate",
                                 "passata"), SWAP_ASK),
          "Tomato ketchup works in a pinch, a tablespoon for a tablespoon, with the recipe's "
          "sugar left out. Otherwise simmer tinned tomatoes down by half, or use passata and cook "
          "it a little longer - it is thinner, so it needs reducing.",
          ask=SWAP_ASK, bias=4),
    entry("swap-coconut-milk", (("coconut milk", "coconut cream"), SWAP_ASK),
          "In a curry, another tin of coconut milk is the answer, or a spoon of ground almonds "
          "with single cream. A plant milk with a teaspoon of oil stands in for the tin in a "
          "soup; yoghurt or cream work too, stirred in off the heat so they do not split.",
          ask=SWAP_ASK, bias=3),
    entry("swap-oats", (("oats", "porridge oats", "rolled oats", "jumbo oats"), SWAP_ASK),
          "Rolled and porridge oats are the same thing, and jumbo oats are only bigger, so swap "
          "them by weight. In a flapjack or a crumble, crushed cornflakes or a spoonful of flour "
          "stand in for them.",
          avoid=NOT_A_SWAP + ("breakfast", "fibre", "bowl", "cook", "cooking",
                              "overnight", "soak", "soggy"),
          ask=SWAP_ASK, bias=4),
    entry("swap-suet", (("suet", "vegetarian suet", "shredded suet"), SWAP_ASK),
          "Grated frozen butter at the same weight, or a vegetable shortening if it has to be "
          "meat-free. In a dumpling, butter rubbed into the flour makes a lighter one than suet "
          "does, so use the same amount and add a little less liquid.",
          ask=SWAP_ASK, bias=4),
    entry("swap-garlic", (("garlic", "garlic clove", "garlic cloves", "garlic puree"), SWAP_ASK),
          "About a quarter teaspoon of garlic powder, or half a teaspoon of garlic granules, is "
          "one clove; in a slow cook the powder is the better swap because it will not burn. A "
          "spring onion, or a pinch of asafoetida, gives the savoury note without the heat.",
          avoid=NOT_A_SWAP + ("grow", "growing", "plant", "planting", "smell", "breath", "bread",
                              "bulb", "bulbs", "sprout", "sprouting"),
          ask=SWAP_ASK, bias=4),
    entry("swap-onion", (("onion", "onions", "shallot", "shallots", "spring onion",
                          "spring onions"), SWAP_ASK),
          "Any of the onion family does another's job by weight: shallots are milder and "
          "sweeter, leeks gentler and slower to soften, spring onions sharper and best raw. A "
          "teaspoon of onion powder stands in for one onion in a stew or a sauce.",
          avoid=NOT_A_SWAP + ("cry", "crying", "cried", "tears", "eyes", "grow", "growing",
                              "plant", "sprout", "sprouting", "layers", "soup", "soups", "ring",
                              "rings", "fried", "caramelise", "caramelised", "caramelize"),
          ask=SWAP_ASK, bias=4),
    entry("swap-fresh-herbs", (("fresh herbs", "fresh basil", "fresh parsley", "fresh coriander",
                                "fresh thyme", "fresh rosemary", "fresh mint"), SWAP_ASK),
          "Dried herbs at a third of the amount, added earlier so they have time to soften, and "
          "frozen chopped herbs go in straight from the freezer. Basil is the one that does not "
          "dry well: use it fresh, or a spoonful of pesto.",
          avoid=NOT_A_SWAP + ("wilt", "wilting", "wilted", "limp", "keep fresh", "last longer",
                              "windowsill", "grow", "growing", "plant", "freeze them"),
          ask=SWAP_ASK, bias=4),
    entry("swap-flour", (("flour",), SWAP_ASK),
          "Self-raising flour stands in for plain at the same weight, with the baking powder the "
          "recipe asks for left out; for the other way round, add 2 level teaspoons of baking "
          "powder to every 150g of plain flour. Bread flour works in a cake but drinks more "
          "liquid, and for thickening a sauce cornflour at half the amount is better.",
          avoid=NOT_A_SWAP + ("plain flour", "self raising", "self-raising", "bread flour",
                              "strong flour", "00 flour", "knead", "kneading", "yeast", "bread",
                              "prove", "rising", "thicken", "thickens", "thickening", "weigh",
                              "grams", "lumps", "sieve"),
          ask=SWAP_ASK, bias=4),
    # Bread flour is the one flour with no swap of its own: swap-flour stands down on "bread
    # flour", "strong flour" and "bread" on purpose, and nothing else took the line, so "what can
    # i use instead of bread flour" was answered with the calorie comparison of rice and pasta.
    # The flour people run out of is strong white for a loaf or 00 for a pizza, and plain is
    # nearly the same thing, so the answer is the same for all of them.
    entry("swap-bread-flour", (("bread flour", "strong flour", "strong white flour",
                                "strong white", "00 flour", "type 00 flour",
                                "bread flour blend"),
                               SWAP_ASK),
          "Plain flour stands in at the same weight, and the loaf is a little softer for it, so "
          "knead two or three minutes longer to build the gluten back. A teaspoon of gluten powder "
          "per 500g gets closer, and for a pizza or a naan plain flour is all you need. Do not use "
          "self-raising: it is the wrong lift for bread.",
          # a cake, a pastry or a thickening is swap-flour's question, and flour as a food is the
          # calorie comparison's: this row is the loaf
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER +
                ("no flour", "without flour", "flourless", "ran out", "run out", "out of flour",
                 "none left", "cake", "cakes", "sponge", "muffin", "muffins", "biscuit",
                 "biscuits", "scone", "scones", "shortbread", "pastry", "pie", "tart", "quiche",
                 "sauce", "gravy", "thicken", "thickening", "batter", "pancake", "pancakes",
                 "breadcrumbs", "cornflour", "semolina", "gram flour", "chickpea flour",
                 "self raising", "self-raising", "almond flour", "coconut flour", "rye flour",
                 "spelt",
                 # the other direction: "can i use bread flour instead of plain flour" is a
                 # question about a cake or a pastry, and swap-flour answers it
                 "instead of plain", "instead of self raising", "instead of self-raising",
                 "for a cake", "in a cake", "for pastry", "for a pie"),
          ask=SWAP_ASK, bias=5),

    entry("swap-cheese", (("cheese",), SWAP_ASK),
          "Any hard cheese melts in for another: cheddar for gruyere or comte, mozzarella for a "
          "mild melter, and a spoon of parmesan or pecorino for the salty finish. Soft cheeses "
          "only swap within their own kind - ricotta and cottage cheese for each other, feta "
          "for goat's cheese - and a splash of milk with butter covers cheese in a sauce.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER +
                ("cheddar", "mozzarella", "feta", "parmesan", "pecorino", "ricotta",
                 "mascarpone", "cream cheese", "cottage cheese", "blue cheese", "brie",
                 "camembert", "halloumi", "goat", "gruyere", "comte", "grill", "grilled",
                 "melt", "melting", "toastie", "toasty", "sandwich", "sauce split", "mould",
                 "mold", "rind", "vegetarian", "rennet"),
          ask=SWAP_ASK, bias=4),
    entry("swap-dried-tomatoes", (("sun dried tomatoes", "sun-dried tomatoes", "sundried",
                                   "dried tomatoes", "sundried tomatoes"), SWAP_ASK),
          "For the flavour in a sauce or a bake, fresh tomatoes cooked down to a third of the "
          "volume with a pinch of sugar and salt get close; a spoon of tomato puree plus a "
          "little olive oil is quicker. In a salad or on bread, halve the weight of fresh "
          "cherry tomatoes and salt them ten minutes first.",
          # "sun" is in the ingredient's own name, so the garden row that answers shade under a
          # tree cannot be stood down by it: the ask gate is what keeps a garden line out.
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    # ---------------------------------------------------------------------------------------
    # The rest of the shop cupboard. Every line below was a shrug on main - "that's beyond what
    # I know well" - while the answer is one short sentence a cook would give without thinking.
    # They share the gate above, so a question about the ingredient itself still goes where it
    # did: the `avoid` list on each row is the questions that name the same word.
    # ---------------------------------------------------------------------------------------
    entry("swap-double-cream", (("double cream", "heavy cream", "whipping cream", "thick cream"),
                               SWAP_ASK),
          "For cooking, milk with a knob of butter and a teaspoon of cornflour thickens much like "
          "cream does. For whipping, chill a tin of evaporated milk and whip it until thick, or "
          "fold full-fat Greek yoghurt into a topping - creme fraiche stirs in without splitting "
          "but will not hold a peak.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-ricotta", (("ricotta",), SWAP_ASK),
          "Cottage cheese drained and mashed is the closest everyday swap, and cream cheese or "
          "mascarpone works where the ricotta is not baked. In a lasagne or cannelloni, a thick "
          "white sauce does the same job.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-mascarpone", (("mascarpone",), SWAP_ASK),
          "Full-fat cream cheese with a spoon of double cream beaten in comes closest, and thick "
          "cold custard does the job in a tiramisu. Cream cheese on its own is sharper, so add a "
          "little icing sugar when it is for a dessert.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-condensed-milk", (("condensed milk", "sweetened condensed milk"), SWAP_ASK),
          "Simmer 500ml of milk with 150g of sugar for about 20 minutes, until it is a third "
          "smaller and syrupy - that is condensed milk. Evaporated milk with sugar stirred in is "
          "the quick version, and a tin of coconut milk with a spoon of sugar is the dairy-free "
          "one.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-evaporated-milk", (("evaporated milk",), SWAP_ASK),
          "Simmer milk down by half, or use single cream where the recipe is not for whipping. In "
          "a bake or a sauce, ordinary milk with a spoon of milk powder stirred in comes close.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-soy-sauce", (("soy sauce", "soya sauce", "light soy sauce", "dark soy sauce"),
                             SWAP_ASK),
          "For seasoning, tamari if the trouble is gluten, or a pinch of salt and a splash of "
          "Worcestershire in a stew. In a stir-fry, miso loosened in a little water or a spoon of "
          "oyster sauce gives the same savoury depth.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-worcestershire", (("worcestershire sauce", "worcester sauce", "worcestershire"),
                                 SWAP_ASK),
          "Soy sauce with a squeeze of lemon and a pinch of sugar is the nearest, and a spoon of "
          "brown sauce works in a stew. In a Bloody Mary, a little balsamic and a dash of Tabasco "
          "replaces it.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-fish-sauce", (("fish sauce", "nam pla", "nuoc mam"), SWAP_ASK),
          "Soy sauce with a squeeze of lime is the usual stand-in, and a teaspoon of anchovy paste "
          "stirred into water does the same for depth. Salt with a little sugar gets you close if "
          "there is nothing else in the cupboard.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-oyster-sauce", (("oyster sauce",), SWAP_ASK),
          "Hoisin with a splash of soy sauce is closest - sweeter and less salty, so use a little "
          "less. A spoon of mushroom sauce, or soy sauce with half a teaspoon of sugar, works in a "
          "stir-fry.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-mustard", (("mustard", "dijon mustard", "english mustard", "wholegrain mustard",
                            "mustard powder"), SWAP_ASK),
          "Horseradish for heat in a sandwich, or mustard powder mixed with water for a dressing. "
          "In a cheese sauce, Worcestershire with a little vinegar covers the tang.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-ketchup", (("ketchup", "tomato ketchup"), SWAP_ASK),
          "A spoon of tomato puree with a little sugar and vinegar is closest, since that is "
          "mostly what ketchup is. In a marinade, passata with honey works; on a plate, brown "
          "sauce.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-tahini", (("tahini", "sesame paste"), SWAP_ASK),
          "Peanut butter loosened with a little water comes closest in hummus, and sunflower seed "
          "butter is the nut-free one. Both are sweeter than tahini, so add a squeeze of lemon.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-anchovies", (("anchovies", "anchovy", "anchovy fillets", "anchovy paste"),
                             SWAP_ASK),
          "A spoon of fish sauce or a teaspoon of soy sauce gives the same savoury depth, and "
          "Worcestershire is the classic swap in a Caesar dressing. On a pizza, olives or capers "
          "bring the salt instead.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-capers", (("capers", "caper"), SWAP_ASK),
          "Chopped green olives are the nearest, or a few cornichons for the vinegar. Both are "
          "milder, so add a squeeze of lemon; in a sauce, a little chopped anchovy does the same "
          "salty job.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-cheddar", (("cheddar", "cheddar cheese", "mature cheddar"), SWAP_ASK),
          "Any firm cheese melts much the same - Edam, gouda or a mild Lancashire. Parmesan will "
          "do in a bake but it is saltier and does not melt smoothly, so use half.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-mozzarella", (("mozzarella", "buffalo mozzarella"), SWAP_ASK),
          "A low-moisture block of mozzarella-style cheese, or torn string cheese, melts the same "
          "way on a pizza, and fontina is the closest by taste. Cheddar will do in a bake, but it "
          "is sharper and oilier.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-feta", (("feta", "feta cheese"), SWAP_ASK),
          "Halloumi or a firm goat's cheese crumbles in the same way, and ricotta salata is the "
          "closest in taste. Cottage cheese drained and salted works on a salad, but not in the "
          "oven.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-bacon", (("bacon", "streaky bacon", "bacon rashers", "smoked bacon"), SWAP_ASK),
          "Pancetta or lardons are the closest, and smoked streaky gives the same salty fat. For "
          "the flavour with no meat, a spoon of smoked paprika and a little olive oil.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-pancetta", (("pancetta", "lardons", "guanciale"), SWAP_ASK),
          "Streaky bacon is the everyday swap - blanch it first if you want it less smoky - and "
          "chopped ham works in a sauce. In a carbonara, bacon is the usual stand-in for "
          "guanciale.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-chorizo", (("chorizo",), SWAP_ASK),
          "Smoked paprika with a little garlic gives the flavour, since chorizo is mostly that. "
          "For the texture, a firm cooking sausage or chopped salami works.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-ginger", (("ginger", "fresh ginger", "ginger root"), SWAP_ASK),
          "A quarter teaspoon of ground ginger for each teaspoon of fresh, added with the other "
          "dry spices. In a stir-fry, a little lemon zest and a pinch of black pepper comes "
          "closer, because ground ginger is sweeter and loses the heat.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-chilli", (("chilli", "chillies", "chili", "fresh chilli",
                           "green chilli", "red chilli"), SWAP_ASK),
          # The two forms of the same ingredient are each other's swap, so the row answers both
          # directions and the phrase says which one it is: a missing fresh chilli takes powder,
          # and a missing spoon of powder takes paprika and cayenne. A single sentence cannot
          # open with both ("what can i use instead of chilli powder" was answered "chilli powder
          # or flakes at a quarter of the amount", which is no use to someone with no powder).
          _the_chilli_swap,
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-cumin", (("cumin", "ground cumin", "cumin seeds"), SWAP_ASK),
          "Ground coriander with a pinch of caraway comes closest, or a little paprika for warmth "
          "without the earthy note. There is no near match, so taste as you go and use less than "
          "the recipe says.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-paprika", (("paprika", "smoked paprika", "sweet paprika"), SWAP_ASK),
          "A pinch of cayenne with a little sugar, or chilli powder at half the amount. Smoked "
          "paprika has no true swap: a drop of liquid smoke, or a little bacon fat, brings the "
          "smoke.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-cinnamon", (("cinnamon", "ground cinnamon", "cinnamon stick"), SWAP_ASK),
          "Mixed spice or nutmeg at half the amount, and allspice is the closest single spice at "
          "the same quantity. In a Moroccan dish, a pinch of ginger and cumin fits better.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-vanilla", (("vanilla", "vanilla extract", "vanilla essence", "vanilla pod"),
                           SWAP_ASK),
          "Maple syrup or honey at the same amount in a cake, or a spoon of the syrup from a jar "
          "of stem ginger. A teaspoon of strong coffee does the same job in a chocolate bake.",
          # "extract" and "essence" are not listed: the line "instead of vanilla extract" holds
          # them itself, and the question about buying the real thing is the pod one
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-cocoa", (("cocoa", "cocoa powder"), SWAP_ASK),
          "Drinking chocolate is not a swap - it has sugar and milk powder in it - so melt dark "
          "chocolate instead, at twice the weight of the cocoa. For colour alone, strong coffee "
          "plus a spoon of extra flour does it.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-gelatine", (("gelatine", "gelatin", "gelatine leaves", "gelatine powder"),
                            SWAP_ASK),
          "Agar is the vegetarian swap and it sets firmer: use a quarter of the weight, boil it "
          "for a minute and let it set cold. For a mousse, extra whipped cream or a spoon of "
          "cornflour in the custard holds it softly instead.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-lentils", (("lentils", "red lentils", "green lentils", "puy lentils"), SWAP_ASK),
          "A tin of chickpeas or beans for the same sauce, or split peas if there is time to cook "
          "them. Red lentils are the ones that thicken a soup, so nothing else quite does that "
          "job.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-chickpeas", (("chickpeas", "chick pea", "garbanzo beans"), SWAP_ASK),
          "Cannellini or butter beans are closest in a stew or a salad, and white beans mashed "
          "with lemon and oil make a hummus. Frozen or tinned broad beans work in a curry.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-beans", (("beans", "tinned beans", "cannellini beans", "haricot beans",
                          "kidney beans", "butter beans", "black beans"), SWAP_ASK),
          "Another tinned pulse does the same job in a stew - chickpeas, cannellini or black beans "
          "- at the same drained weight. In a salad, a tin of lentils needs no cooking at all.",
          # "butter beans" carries a fat word in its name, and the pan-of-spent-oil row keys
          # every fat word: the same 6 that puts a fat swap in front of it does it here
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=FAT_SWAP),
    entry("swap-saffron", (("saffron", "saffron threads"), SWAP_ASK),
          "Turmeric gives a similar colour at a pinch, but none of the honeyed taste, so use less "
          "than you think. In rice or a stew, a spoon of the water from soaked dried apricots, or "
          "a little orange zest, comes closer.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-raisins", (("raisins", "sultanas", "currants"), SWAP_ASK),
          "Chopped dates or dried apricots work in a cake, though they are sweeter and stickier, "
          "so dust them in flour first. Soaked prunes give the same moisture to a teabread.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-dates", (("dates", "medjool dates"), SWAP_ASK),
          "Raisins or dried figs stand in, soaked in hot water first if the recipe blends them. "
          "For sweetness in a flapjack or a smoothie, a mashed banana works.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-banana", (("banana", "bananas"), SWAP_ASK),
          "Apple sauce or yoghurt keeps a cake as moist - about 60g for one banana - and a spoon "
          "of honey covers the sweetness. For binding, one egg does the job.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-apple-sauce", (("apple sauce", "applesauce"), SWAP_ASK),
          "Mashed banana or yoghurt at the same weight keeps a cake as moist, and pureed pear "
          "tastes closer. For a sauce to go with pork, stewed apple with a knob of butter.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-olive-oil", (("olive oil", "extra virgin olive oil"), SWAP_ASK),
          "Any cooking oil fries and roasts the same, and a mild one is better than a peppery "
          "olive oil in a cake. For a dressing, rapeseed oil with a squeeze of lemon is closest - "
          "keep the olive oil for finishing.",
          # the pan of spent oil is `oil-smoking`'s question and it also keys on the oil words
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=FAT_SWAP),
    entry("swap-olives", (("olives", "green olives", "black olives"), SWAP_ASK),
          "Capers or chopped cornichons bring the salt and the tang, and chopped anchovy does the "
          "same in a sauce. Roasted red pepper is closer in texture for a salad.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-creamed-coconut", (("creamed coconut", "coconut cream", "coconut block"),
                                   SWAP_ASK),
          "A tin of coconut milk is the same thing with more water in it - about a third of a "
          "block's weight. Coconut cream from a tin stirs straight in, and dairy cream works "
          "where the coconut taste does not matter.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-semolina", (("semolina",), SWAP_ASK),
          "Polenta or fine cornmeal works in most recipes, though it needs longer to soften. For "
          "dusting a loaf or a pizza, plain flour does the same job, a little more coarsely.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-polenta", (("polenta", "cornmeal"), SWAP_ASK),
          "Fine semolina cooked the same way, or a coarse cornmeal flour - both want stirring for "
          "longer. Instant polenta is the quickest stand-in for the long-cooked sort.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-beer", (("beer", "ale", "stout", "lager"), SWAP_ASK),
          "In a stew or a batter, the same amount of stock with a squeeze of lemon - cider for a "
          "pork dish. Ginger ale with a splash of vinegar keeps the sweetness and the lift in a "
          "batter.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    entry("swap-bicarbonate", (("bicarbonate of soda", "bicarb", "baking soda", "bicarbonate"),
                               SWAP_ASK),
          "Baking powder at three times the amount, since it already carries its own acid, though "
          "it tastes of salt. Without either, stiffly beaten egg white lifts a small bake.",
          # a line that names baking powder is the pair verdict's ("not on its own"), so this
          # row answers only the missing bicarbonate
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("baking powder",),
          ask=SWAP_ASK, bias=4),
    entry("swap-leeks", (("leeks", "leek"), SWAP_ASK),
          "Onions or spring onions are the nearest - one leek is about two onions, and they "
          "soften faster. In a soup, a couple of celery sticks with the onion fills the gap.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER,
          ask=SWAP_ASK, bias=4),
    # The grains and the salad shelf. "what can i use instead of couscous" was a search hedge,
    # and rice and pasta reached the nutrition row that weighs them by the hundred grams.
    entry("swap-couscous", (("couscous",), SWAP_ASK),
          "Bulgur wheat takes the same steeping and has more bite, quinoa cooks in 15 minutes, "
          "and orzo or pearl barley work in a salad though they need boiling. Same weight, same "
          "dressing; couscous is the blandest of them, so taste for salt and lemon.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-bulgur", (("bulgur wheat", "bulgur", "burghul"), SWAP_ASK),
          "Couscous is the closest and needs no cooking at all - cover it with the same weight of "
          "boiling water for five minutes. Pearl barley or quinoa work in a salad or a soup, but "
          "both want simmering first, and a little more dressing.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-quinoa", (("quinoa",), SWAP_ASK),
          "Couscous or bulgur stand in cold in a salad, and rice or pearl barley where it goes "
          "into a soup, all at the same dry weight. Quinoa is the gluten-free one, so if that is "
          "why it is on the list, keep to rice or millet instead.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-pearl-barley", (("pearl barley", "barley"), SWAP_ASK),
          "Bulgur wheat or rice in a soup or a stew, and both cook in a fraction of the time - "
          "about 15 minutes against 40. Orzo does the same job in a broth when the cook wants the "
          "bite without the chew.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    # The nuts. "instead of ground almonds" reached the coffee row, which keys on "ground".
    entry("swap-ground-almonds", (("ground almonds", "almond flour", "almond meal"), SWAP_ASK),
          "Blanched almonds ground fine in a processor are the same thing, and walnuts or "
          "cashews ground the same way work in a cake. Desiccated coconut thickens a bake but "
          "tastes of coconut, so use half the weight and add a spoon of milk.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("coffee", "grinder", "mill", "beans"),
          ask=SWAP_ASK, bias=5),
    entry("swap-pine-nuts", (("pine nuts", "pinenuts", "pine kernels"), SWAP_ASK),
          "Sunflower seeds or flaked almonds at the same weight, toasted in a dry pan the same "
          "way, and cashews or walnuts go into a pesto. Keep them moving, because all of them "
          "catch sooner than pine nuts do.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-walnuts", (("walnuts", "walnut halves"), SWAP_ASK),
          "Pecans are the closest in taste and texture and swap one for one, and hazelnuts or "
          "almonds work in a bake. Chop them about the same size, since a smaller nut browns "
          "faster in the oven.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-peanut-butter", (("peanut butter", "smooth peanut butter", "crunchy peanut "
                                  "butter"), SWAP_ASK),
          "Another nut butter swaps one for one, and tahini or sunflower seed butter do the same "
          "in a sauce or a smoothie. In a bake, mashed banana or apple sauce at the same weight "
          "keeps it moist when the peanut butter was there for that.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("dog", "dogs", "bird", "birds", "feeder"),
          ask=SWAP_ASK, bias=4),
    entry("swap-sesame-oil", (("sesame oil", "toasted sesame oil"), SWAP_ASK),
          "For the toasted taste, walnut oil, or a plain oil with a teaspoon of toasted sesame "
          "seeds left to sit in it for an hour. For frying, any neutral oil; tahini loosened with "
          "a little oil is closest in a dressing, though it is thicker.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("hair", "skin", "massage", "cradle cap"),
          ask=SWAP_ASK, bias=5),
    # The vegetables. These were all hedges, and one word for the vegetable is not another.
    entry("swap-spinach", (("spinach", "baby spinach"), SWAP_ASK),
          "Chard is the closest, and kale or spring greens work cooked though they want a few "
          "minutes longer. In a salad or on a pizza, rocket or the young leaves of beetroot "
          "stand in raw.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    # "i have no frozen peas" came back as how long to boil frozen peas, and "what can i use
    # instead of frozen peas" as what a bag of them is good for: a bag nobody has is a swap
    # question, and the form rows answer only the form ("no frozen, so fresh"), not the food.
    entry("swap-peas", (("peas", "pea", "frozen peas", "garden peas", "petit pois", "petits pois",
                         "mushy peas"), SWAP_ASK),
          "Tinned or fresh garden peas at the same weight, and frozen mixed veg or a handful of "
          "chopped green beans does the same job in a stew, a pie or a curry - add them near the "
          "end either way. In a salad, chopped spring onion and a stick of celery give the green "
          "crunch instead.",
          # `frozen` is not in NOT_A_SWAP for this row: half the people who have none of them
          # say the word, and the keeping rows stand this one down on their own words.
          avoid=NOT_A_SWAP_EITHER + ("keep", "keeps", "keeping", "kept", "store", "stored",
                                     "storing", "last", "lasts", "gone off", "refreeze",
                                     "re-freeze", "re freeze", "how long", "still good",
                                     "out of date", "calories", "healthy", "diet", "how much",
                                     "how many", "cut down"),
          ask=SWAP_ASK, bias=4),
    entry("swap-mushrooms", (("mushrooms", "mushroom", "chestnut mushrooms",
                              "button mushrooms", "closed cup mushrooms"), SWAP_ASK),
          "Tinned or frozen mushrooms at the same weight, drained and dried in the pan so they "
          "brown, or a few dried porcini soaked for the savoury depth. For the texture in a pie, "
          "cooked lentils or chopped aubergine.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("magic", "hallucinogenic", "grow", "growing",
                                                  "picking", "foraging", "identify"),
          ask=SWAP_ASK, bias=4),
    entry("swap-courgette", (("courgette", "courgettes", "zucchini"), SWAP_ASK),
          "Aubergine or a green pepper in a ratatouille or a traybake, and cucumber where it is "
          "raw - grated and squeezed, it does the same job in a salad. In a cake, grated carrot "
          "or mashed banana at the same weight keeps it as moist.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-aubergine", (("aubergine", "aubergines", "eggplant"), SWAP_ASK),
          "Courgette or two big flat mushrooms in a bake, and peppers in a traybake; all of them "
          "take less oil. Salt and roast the swap the same way, because the browning is what the "
          "aubergine was there for.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-peppers", (("peppers", "bell pepper", "bell peppers", "red pepper",
                            "green pepper", "yellow pepper"), SWAP_ASK),
          "Any colour of pepper swaps for another, and a green one is sharper than a red. With "
          "none in, celery or courgette in a stew, or a spoon of tomato puree for the sweetness "
          "a roasted red pepper gives.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("peppercorns", "black pepper", "white pepper",
                                                  "cracked", "grinder", "sneeze"),
          ask=SWAP_ASK, bias=4),
    entry("swap-celery", (("celery", "celery sticks"), SWAP_ASK),
          "Fennel is the closest, with a little more aniseed, and celeriac chopped small does the "
          "cooked job. In a salad, cucumber batons with a pinch of salt give the crunch, and a "
          "pinch of celery seed flavours a soup.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-harissa", (("harissa", "harissa paste"), SWAP_ASK),
          "A spoon of tomato puree with a pinch of chilli flakes, a crushed garlic clove and a "
          "teaspoon of cumin is close. Any chilli paste does in a marinade, though it will be "
          "hotter, so add it a spoon at a time.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-miso", (("miso", "miso paste", "white miso", "brown miso"), SWAP_ASK),
          "Soy sauce is the everyday stand-in - a teaspoon for a tablespoon of white miso, "
          "stirred in off the heat. A spoon of tahini loosened with soy gives the nutty depth in "
          "a dressing, and both are salty, so taste before adding more.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-curry-paste", (("curry paste", "thai curry paste", "red curry paste",
                                "green curry paste"), SWAP_ASK),
          "Fry a tablespoon of curry powder with a crushed garlic clove and the same of ginger in "
          "oil and you have a rough paste for one curry. For a Thai curry, fish sauce and lime "
          "juice matter more than the paste, so taste and add those.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("curry powder", "how much", "hot"),
          ask=SWAP_ASK, bias=4),
    # The sweet and the boozy, and the dairy-free cheeses.
    entry("swap-maple-syrup", (("maple syrup",), SWAP_ASK),
          "Honey or golden syrup at the same weight, though honey is sweeter, so use a little "
          "less. In a marinade or a glaze, soft brown sugar with a splash of water does the same; "
          "on pancakes there is no real stand-in for the maple taste.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("tap", "tree", "trees", "sugar shack"),
          ask=SWAP_ASK, bias=4),
    entry("swap-brandy", (("brandy", "cognac"), SWAP_ASK),
          "Rum, whisky or sherry at the same amount does the job in a cake or on a Christmas "
          "pudding, and apple juice with a scrap of vanilla is the alcohol-free one. A smoky "
          "whisky is stronger than brandy, so use a little less of it.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("butter", "sauce", "cream", "flambe",
                                                  "flambé", "set fire"),
          ask=SWAP_ASK, bias=4),
    entry("swap-tofu", (("tofu", "firm tofu", "silken tofu", "smoked tofu", "bean curd"),
                        SWAP_ASK),
          "Paneer or halloumi hold their shape in a curry, though both are saltier and neither "
          "takes up the sauce as well; tempeh is nearest in texture. For silken tofu in a soup "
          "or a smoothie, plain yoghurt does the same.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("soy", "soya", "vegan", "protein"),
          ask=SWAP_ASK, bias=4),
    entry("swap-paneer", (("paneer",), SWAP_ASK),
          "Halloumi is the closest and goes squeaky rather than grainy, and firm tofu presses "
          "and cubes the same way and takes the sauce. Feta works in a salad but will not hold "
          "together in a curry, and it is saltier.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-halloumi", (("halloumi",), SWAP_ASK),
          "Paneer fries the same way and is much less salty, so taste before adding salt to the "
          "pan; firm tofu does the job in a vegetable stack. Where it is eaten cold in a salad, "
          "feta is the closest taste.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=4),
    entry("swap-jam", (("jam", "marmalade", "fruit jam"), SWAP_ASK),
          "Marmalade or a fruit compote at the same weight, and mashed banana or apple sauce in a "
          "cake. For a glaze on a bake, warmed honey with a spoon of water does the same job; a "
          "spoon of jam in a marinade can be replaced by honey and a splash of vinegar.",
          # a jammed printer and a traffic jam have the word and not the question
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("traffic", "printer", "printing", "paper",
                                                  "door", "drawer", "stuck", "lid", "jar",
                                                  "mould", "mold", "out of date", "open"),
          ask=SWAP_ASK, bias=4),
    # The two staples people swap for a change rather than a shortage ("instead of rice
    # tonight"), and the tinned tomato, whose own row answers a different question about a tin.
    entry("swap-rice", (("rice", "white rice", "basmati rice", "long grain rice"), SWAP_ASK),
          "Quinoa, couscous or orzo at the same dry weight, and pearl barley where it goes into a "
          "soup; all of them cook in about the time rice does. For a curry, naan or a baked "
          "potato does the same job of soaking up the sauce.",
          # cooking it, keeping it and how much of it are the rice rows' own questions
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("cook", "cooking", "boil", "boiling", "water",
                                                  "ratio", "pudding", "risotto", "wash", "rinsing",
                                                  "rinse", "microwave", "leftover", "left over",
                                                  "per person", "reheat", "how do i", "sticky",
                                                  "sushi", "paella", "vinegar", "wine",
                                                  "krispies", "crispies", "cereal",
                                                  "rice cake", "rice cakes", "rice milk"),
          ask=SWAP_ASK, bias=5),
    entry("swap-pasta", (("pasta", "spaghetti", "penne", "fusilli", "macaroni", "tagliatelle"),
                         SWAP_ASK),
          "Rice, potatoes or orzo at the same weight, and courgette ribbons if it is the "
          "lightness that is wanted. For a bake, a layer of sliced potato or a tin of beans "
          "under the sauce fills the dish the same way.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("cook", "cooking", "boil", "boiling", "water",
                                                  "al dente", "sauce", "salad", "bake", "shapes",
                                                  "fresh pasta", "dried", "leftover", "reheat",
                                                  "how long", "how do i"),
          ask=SWAP_ASK, bias=5),
    entry("swap-tinned-tomatoes", (("tinned tomatoes", "canned tomatoes", "tinned chopped "
                                    "tomatoes", "chopped tomatoes"), SWAP_ASK),
          "Fresh tomatoes simmered for ten minutes stand in for a tin, and frozen chopped ones "
          "go straight in with three or four minutes extra. Passata at the same volume thickens "
          "without the bits, and a spoon of tomato puree with water is the last resort; taste for "
          "salt, since a tin already has some.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("bpa", "lining", "brand", "cheap", "best",
                                                  "which"),
          ask=SWAP_ASK, bias=5),
    # The store cupboard's odds and ends, and four rows that were answering a neighbour: "instead
    # of oat milk" reached the oats row, "instead of cocoa butter" the chocolate one, "instead of
    # digestive biscuits" the cut-down-the-sugar talk, and "instead of bread" and "instead of
    # noodles" the row that weighs carbs by the hundred grams.
    entry("swap-oat-milk", (("oat milk", "oatly", "oat drink"), SWAP_ASK),
          "Another unsweetened plant milk swaps one for one - soya is the closest in protein and "
          "in coffee, and almond is thinner. In a bake, dairy milk does the same job, or the same "
          "volume of water with a spoon of oil.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=5),
    entry("swap-cocoa-butter", (("cocoa butter",), SWAP_ASK),
          "Where it sets something - chocolate, a cream - there is no true swap, because that is "
          "the job it does; shea butter or coconut oil at the same weight come closest and set "
          "softer. Where it is only the fat in a bake, butter or a neutral oil.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("cocoa powder",), ask=SWAP_ASK, bias=5),
    entry("swap-digestive-biscuits", (("digestive biscuits", "digestives", "digestive biscuit"),
                                      SWAP_ASK),
          "Rich tea or shortbread crushed the same way make the same cheesecake base, and ginger "
          "nuts give it a kick. With no biscuits in, 250g of oats blitzed with 125g of melted "
          "butter sets just as firm.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("calories", "biscuit tin", "dunk"),
          ask=SWAP_ASK, bias=5),
    entry("swap-noodles", (("noodles", "egg noodles", "rice noodles", "ramen noodles",
                            "udon", "soba"), SWAP_ASK),
          "Spaghetti broken in half does the stir-fry job, and rice or vermicelli in a soup; udon "
          "and soba swap for each other by weight. Cook them a minute less than you would, since "
          "the swap goes back in the pan.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=5),
    entry("swap-bread", (("bread", "white bread", "sliced bread", "stale bread"), SWAP_ASK),
          "A wrap, a pitta or a bagel does the sandwich job, and brioche or panettone the same "
          "weight in a bread-and-butter pudding. Where the bread is there for crumbs, blitzed "
          "crackers or a handful of oats.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("carbs", "calories", "toast", "toaster",
                                                  "breadmaker", "bread machine", "make bread",
                                                  "bake bread", "yeast", "sourdough", "stale",
                                                  "flour", "bread flour"),
          ask=SWAP_ASK, bias=5),
    entry("swap-brown-sauce", (("brown sauce", "hp sauce", "brown sauce bottle"), SWAP_ASK),
          "Ketchup with a dash of Worcestershire sauce and a pinch of pepper is close, and a "
          "spoon of chutney loosened with a little vinegar does in a sandwich. Brown sauce is "
          "dates, tamarind and vinegar, so a spoon of tamarind or a little date syrup stirred "
          "into the ketchup gets nearer.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("stain", "stains", "shirt", "carpet"),
          ask=SWAP_ASK, bias=5),
    entry("swap-gravy", (("gravy", "gravy granules", "gravy powder", "bisto"), SWAP_ASK),
          "The roasting juices with a teaspoon of flour and a splash of stock are a gravy "
          "already; with no juices, a stock cube in water thickened with a spoon of cornflour. A "
          "dash of soy or Worcestershire and a little of the vegetable water give it the depth.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("lump", "lumps", "lumpy", "too thick",
                                                  "too thin"),
          ask=SWAP_ASK, bias=5),
    entry("swap-tortillas", (("tortillas", "tortilla", "wraps", "wrap bread"), SWAP_ASK),
          "A pitta or a thin flatbread wraps the same filling, and a lettuce leaf for a lighter "
          "one. Corn and flour tortillas swap for each other in a bake, though corn ones want a "
          "moment in a dry hot pan first or they crack.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("spanish tortilla", "potato tortilla",
                                                  "omelette"),
          ask=SWAP_ASK, bias=5),
    entry("swap-sriracha", (("sriracha", "sriracha sauce"), SWAP_ASK),
          "A teaspoon of chilli flakes with a crushed garlic clove and a pinch of sugar in a "
          "little vinegar is close, and any other chilli sauce does the job. Tabasco is thinner "
          "and sharper, so use a few drops and add a pinch of sugar.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=5),
    entry("swap-pineapple", (("pineapple", "tinned pineapple", "pineapple rings"), SWAP_ASK),
          "Tinned pineapple in juice is the same fruit, drained and patted dry before it goes on "
          "a pizza; fresh pineapple needs a few minutes in the pan first. In a smoothie or a "
          "salsa, mango or peach bring the same sweetness and tang.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER + ("pizza topping",), ask=SWAP_ASK, bias=5),
    entry("swap-cream-of-tartar", (("cream of tartar",), SWAP_ASK),
          "For a quarter teaspoon of cream of tartar, use half a teaspoon of lemon juice or white "
          "vinegar: it is there to steady egg whites or to stop sugar crystallising. Baking "
          "powder is not a swap, since it brings its own acid and its own rise.",
          avoid=NOT_A_SWAP + NOT_A_SWAP_EITHER, ask=SWAP_ASK, bias=5),
]


# The words that end the name of the thing being replaced. "can i use cornflour instead of plain
# flour in a cheese sauce" is a question about the flour, and every word after "instead of" up to
# "in" is that thing; without a stop list "in" and "a" would be read as ingredients too.
_SWAP_STOP = ("and", "or", "but", "in", "for", "on", "with", "to", "when", "because", "since",
              "so", "my", "the", "a", "an", "this", "that", "it", "recipe", "please", "if",
              "what", "from", "at", "as", "of", "into", "how", "tonight", "today", "now")

# The shapes that ask for a dish rather than a stand-in. "what can i make for dinner if i dont
# have any cheese" has a shortage in it, so SWAP_ASK alone reached the cheese table: the honest
# answer to a missing ingredient in a meal is "leave it out and finish the dish", not a list of
# other cheeses. A line that also says "instead" is a swap whatever else it says.
_MAKE_ASK = ("what can i make", "what can i cook", "what can i have", "what should i cook",
             "what shall i make", "what should i make", "what do i make", "what can we have",
             "what can we eat", "what can i do for dinner", "whats for dinner",
             "what's for dinner", "what can i make for dinner")

# The words that make the line a swap even when it also asks what to make.
_SWAP_SAID = ("instead", "in place of", "substitute", "swap", "replace", "alternative",
              "stand in for", "stand-in for", "what else can i use", "what can i use")


def _swapped_out(text):
    """The ingredient the line names after "instead of", as the words it used."""
    said = []
    words = str(text or "").lower().replace(",", " ").replace(".", " ").split()
    for position, word in enumerate(words):
        if word != "instead":
            continue
        if position + 1 >= len(words) or words[position + 1] != "of":
            continue
        for following in words[position + 2:]:
            if following in _SWAP_STOP:
                break
            said.append(following)
    return said


def _fenced(row, said):
    """The row's reply, with two general stand-downs in front of it.

    The first is the phrase itself rather than a list of pairs: a row answers nothing when the
    line names something else as the thing being replaced and the row does not own one of those
    words ("instead of plain flour" on the cheese row). `_the_other_side_of_a_swap` can only
    name the pairs the file already knows about.

    The second is the dish ask: a shortage inside "what can i make" wants something to eat, not
    another kind of the same ingredient.
    """
    own = {word for name in _names(row.key[0]) for word in str(name).lower().split()}
    # The taste row below is the one that answers a food somebody will not eat, so the shortage
    # rows for that food stand down on it: "i dont like mushrooms what can i use instead" was
    # answered with tinned or frozen mushrooms, which is the pantry question and not the one
    # asked.
    taste_row = str(getattr(row, "id", "") or "") == "swap-what-i-will-not-eat"

    def answer(memory, understood):
        text = " " + str((understood or {}).get("clean") or "").lower() + " "
        swapped = _swapped_out(text)
        if swapped and not any(_same_word(word, mine) for word in swapped for mine in own):
            return ""
        # only when the taste row can answer it: a taste with no "instead" in the line is the
        # store's note or the food's own "no onion then" answer, and standing that down left the
        # line with a hedge ("i dont like onions what can i do" was "start the dish with a leek").
        if not taste_row and any(phrase in text for phrase in TASTE_SAID) \
                and any(phrase in text for phrase in ASKS_FOR_A_SWAP) \
                and any((" " + str(name).lower() + " ") in text
                        for name in _names(row.key[0]) if " " not in str(name)):
            return ""
        asking_for_a_dish = any(phrase in text for phrase in _MAKE_ASK)
        if asking_for_a_dish and not any(phrase in text for phrase in _SWAP_SAID):
            return ""
        return said(memory, understood) if callable(said) else said

    return answer


def _fence_every_row(rows):
    """Every row is fenced, so a row added later is fenced without being told to be."""
    for row in rows:
        row.reply = _fenced(row, row.reply)


def _names(part):
    """The alternative names of one key part, as written ("olive oil" gives one name)."""
    return tuple(part if isinstance(part, tuple) else (part,))


def _same_word(one, other):
    """True for "olive" and "olives", so a plural never reads as a different ingredient."""
    return str(one).lower().rstrip("s") == str(other).lower().rstrip("s")


def _inside(name, mine):
    """True when every word of `name` is a word of the row's own name.

    The word forms are loose, so "instead of olives" also matches "instead of olive oil": a row
    that stood down on it would stand down on its own question.
    """
    return all(any(_same_word(word, own) for own in mine) for word in str(name).split())


def _the_other_side_of_a_swap(rows):
    """Give every row the name of every *other* ingredient, on the far side of "instead of".

    "Can I use butter instead of oil in a cake" is a question about the oil that has run out, and
    both rows are reachable from it: the butter row has the butter, the words "can i use" and
    "instead of", and the oil row has the oil. Half of the lines people write in this shape were
    answered by the wrong side of it, because which ingredient is missing is told by the words
    after "instead of" and the matcher weighs every word the same.

    So a row stands down whenever another ingredient in this file is named as the one being
    replaced. It costs nothing on the question the row is for: a swap line names the ingredient
    that has gone and no second one ("what can i use instead of butter", "no butter left"), and
    when it does name a second one that second ingredient is the missing one, and its own row -
    or cooking.py's verdict for the pair - answers it.

    Two names are left out. One is the row's own name, since "instead of cream cheese" is the
    cream cheese row's line. The other is a name whose words all sit inside the row's own name
    (see _inside). Only the first key part is read - the second is SWAP_ASK, and its words are
    the ask, never a thing a cook can be short of.
    """
    for row in rows:
        mine = {str(name).lower() for name in _names(row.key[0])}
        own_words = {word for name in mine for word in name.split()}
        phrases = []
        for other in rows:
            if other is row:
                continue
            for name in _names(other.key[0]):
                if str(name).lower() in mine or _inside(name, own_words):
                    continue
                phrases.append("instead of " + str(name))
                phrases.append("in place of " + str(name))
        if phrases:
            row.avoid = row.avoid + tuple(phrases)


_the_other_side_of_a_swap(ENTRIES)

_fence_every_row(ENTRIES)
