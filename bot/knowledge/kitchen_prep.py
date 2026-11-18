"""Kitchen prep: the small things you do before the cooking, not the cooking.

The answers lane owns this domain. It holds two kinds of row, both about a step that happens
before anything goes in the pan or the oven.

The room-temperature table: "room temperature" is two questions, how warm a bedroom should be and
what to do with a steak before cooking it. Neither cooking's tables nor sleep's could hold the
kitchen half without moving the rarity of a word a dozen other lines are weighed against -
"should I rest a steak" went to a different answer the moment it did - so the row lives in a table
of its own, keyed by the cut and the instruction.

The step table: "do i need to sift flour", "do i have to peel the potatoes", "should i prick the
jacket potatoes", "do i need to score the pork skin". The person already knows what they are
cooking and is asking whether one step matters, and the answer is yes or no in the first words
with the one consequence that decides it. These lines were answered by a row that shared a word
with them and not the question: the vegetarian card for sifting flour, the coat card for a jacket
potato, the side dishes table for peeling, the red-meat limit for patting a steak dry. The step is
the question; the food only picks which sentence inside the answer.

Only the steps with no card of their own are here. The cooking entries already answer resting
meat, soaking pulses, rinsing rice, washing mushrooms, pricking sausages, deseeding chillies,
greasing a tin, salting pasta water and marinating, and each row here stands down for exactly
those foods.
"""

import re

from ..memory import last_user
from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

_MEAT_ROWS = [
    # "Room temperature" is an instruction in a kitchen, not a bedroom reading. The egg line is
    # already the eggs row's; a steak on the counter is this one, and it was answered with the
    # temperature a bedroom should be.
    # The subject is the meat, not the steak: "should i let chicken come to room temperature" is
    # the same instruction and was reaching the bedroom card, because the sleep stand-down took it
    # off the keeping row and only the cut named here could answer it. Chicken, pork and a joint
    # are cooked the same way - dry it, season it, put it in a hot pan - so the row speaks for all
    # of them and says so in its first sentence.
    entry("meat-room-temperature", (("steak", "steaks", "chicken", "chicken breast", "turkey",
                                    "pork", "lamb", "beef", "fish", "meat", "the meat",
                                    "chops", "sausages"),
                                    ("room temperature", "out of the fridge", "rest out",
                                     "twenty minutes", "an hour before", "come to room",
                                     "warm up before", "before cooking", "before it goes in")),
          "It barely matters: twenty minutes on the counter warms the meat by a couple of degrees "
          "inside, so the middle still cooks the same. Leaving raw meat out for hours is a food "
          "safety risk. What does make a difference is patting it dry and seasoning it just before "
          "it goes in the pan - a dry surface browns, a wet one steams.",
          avoid=("keep", "keeps", "keeping", "how long", "left out", "overnight", "gone off",
                 "still good", "defrost", "thaw", "freeze", "frozen", "wash", "washing",
                 "rinse", "safe", "food poisoning", "pink", "raw in the middle",
                 "is it cooked", "cooked through", "cooked to", "done", "how do i know",
                 "what temperature", "how hot", "oven", "rest a joint", "resting",
                 # a sausage pricked or splitting is the prick-sausages row's question, and
                 # "before cooking" alone was enough to hand it this one instead
                 "prick", "pricking", "pricked", "pierce", "pierced", "split", "splits",
                 "burst", "bursts", "skin", "skins"),
          bias=1),
]

# A preparation verb as it is said, with the forms a person uses for the same action.
_SIFT = ("sift", "sifts", "sifting", "sifted", "sieved", "sieve the")
_PEEL = ("peel", "peels", "peeling", "peeled")
_PRICK = ("prick", "pricks", "pricking", "pricked", "pierce", "piercing")
_SCORE = ("score", "scores", "scoring", "scored", "slash", "slashing", "slit", "slits",
          "slitting")
_BLANCH = ("blanch", "blanches", "blanching", "blanched", "refresh", "refreshing")
_PARBOIL = ("parboil", "parboils", "parboiling", "parboiled", "part boil", "partly boil")
_RINSE = ("rinse", "rinses", "rinsing", "rinsed")
_PAT = ("pat", "pats", "patting", "patted", "dab", "dabs", "dabbing")
_TRIM = ("trim", "trims", "trimming", "trimmed", "top and tail", "top and tailing")

# The second half of the key, and the thing that makes the line a question at all: without it
# the verb alone is a method question ("how do i peel potatoes"), which is the recipe rows'
# turn. The matcher wants two key parts, and these are the words a person uses when asking
# whether a step is worth doing.
_ASK = ("need", "needs", "needed", "have to", "has to", "should", "must", "necessary",
        "worth", "point", "bother", "bothering", "essential", "important")

# Scoring meat has no card anywhere else, so its row also answers the same question asked as a
# method ("how do i score pork skin"), which the yes-or-no words alone would not match.
_SCORE_ASK = _ASK + ("how do i", "how to", "how should i", "how do you")

# A food, or a food's part, has to be in the line: the verb alone is not enough, or every
# "do i need to score" and "should i trim" in the language lands here.
_FOOD = re.compile(
    r"\b(?:potato|potatoes|spud|spuds|jacket|jackets|carrot|carrots|parsnip|parsnips|swede|"
    r"turnip|tomato|tomatoes|apple|apples|pear|pears|peach|peaches|plum|plums|cucumber|"
    r"cucumbers|courgette|courgettes|aubergine|aubergines|pepper|peppers|onion|onions|garlic|"
    r"mushroom|mushrooms|bean|beans|chickpea|chickpeas|lentil|lentils|pea|peas|broccoli|"
    r"cauliflower|cabbage|sprout|sprouts|spinach|kale|sweetcorn|corn|rice|risotto|pasta|"
    r"spaghetti|noodles|flour|cocoa|sugar|oats|porridge|couscous|quinoa|bread|dough|loaf|"
    r"sourdough|pastry|cake|sponge|batter|scone|scones|chicken|turkey|beef|lamb|pork|steak|"
    r"mince|sausage|sausages|bacon|ham|gammon|duck|fish|salmon|cod|haddock|tuna|prawn|prawns|"
    r"mussels|squid|chilli|chillies|chilies|ginger|cheese|butter|milk|cream|yoghurt|yogurt|"
    r"egg|eggs|tofu|almonds|walnuts|peanuts|chips|chip|fries|vegetables|veg|salad|fruit|meat|"
    r"joint|roast|skins?|fat|skin|asparagus|leek|leeks|celery|fennel|radish|radishes|"
    r"spring onion|spring onions|scallion|scallions|beetroot|sweet potato|sweet potatoes|"
    r"butternut|squash|pumpkin)\b")

# A step in something that is not food at all.
_NOT_FOOD = re.compile(
    r"\b(?:hair|nails|beard|feet|foot|hands|paint|wall|wallpaper|wood|deck|fence|car|bike|"
    r"engine|boiler|floor|tile|tiles|grout|bath|shower|toilet|drain|washing machine|"
    r"dishwasher|kettle|loan|mortgage|insurance|email|letter|application|job|interview|"
    r"contract|passport|visa|exam|hedge|lawn|tree|trees|bush)\b")


def _said(understood):
    """The line's own words, as the reading hands them over."""
    reading = understood or {}
    text = reading.get("clean") or reading.get("text")
    if not text:
        text = " ".join(str(word) for word in (reading.get("words") or ()))
    return " " + str(text).lower() + " "


def _asks_whether_the_step_is_needed(understood):
    """The row's guard: a food, an ask about the step, and nothing that is not food."""
    said = _said(understood)
    if _NOT_FOOD.search(said):
        return False
    if not _FOOD.search(said):
        return False
    return any(word in said for word in ("need", "have to", "has to", "should", "must",
                                         "necessary", "worth", "point", "bother", "essential",
                                         "important"))


def _how_or_whether(understood):
    """Scoring has no other card for meat, and a bare "how do i score pork skin" is the same
    question asked as a method: this row's own reply answers it too."""
    if _asks_whether_the_step_is_needed(understood):
        return True
    said = _said(understood)
    if _NOT_FOOD.search(said) or not _FOOD.search(said):
        return False
    return any(phrase in said for phrase in ("how do i", "how to ", "how should i",
                                             "how do you"))


def _patting_it_dry(understood):
    """Pat dry is two words with the thing in the middle: "should i pat the steak dry"."""
    return _asks_whether_the_step_is_needed(understood) and " dry" in _said(understood)


# The things a blanch is a step in: a line that says "blanch" or "freeze" about one of these is
# this row's question, where "should i freeze the soup" is the freezer card's.
_BLANCHABLE = re.compile(
    r"\b(?:vegetables|veg|greens|beans|green beans|runner beans|broad beans|carrots|peas|"
    r"broccoli|cauliflower|sprouts|spinach|kale|sweetcorn|corn|cabbage|leeks|celery|asparagus|"
    r"courgettes|mange tout|potatoes|potato|tomatoes|tomato|almonds|nuts)\b")

# The freezer, in the words people use for it. A line that says one of these is asking about
# keeping the food, which is a different question from whether to do the step at all.
_FREEZING = ("freeze", "freezes", "freezing", "frozen", "freezer")


def _a_step_the_turn_before(memory):
    """True when the turn before was a step about food, so a bare "and if im freezing them" has
    both the food and the step to lean on. The subject of a follow-up is the turn before it."""
    earlier = last_user(memory) if memory is not None else ""
    earlier = " " + " ".join(str(earlier or "").split()).lower() + " "
    if not earlier.strip() or _NOT_FOOD.search(earlier):
        return False
    if not _FOOD.search(earlier):
        return False
    return any(_says(earlier, *forms) for forms in _STEP_VERBS)


def _a_freezing_question(understood):
    """A question about the freezer: the word for it, and it is not about something else."""
    said = _said(understood)
    if _NOT_FOOD.search(said) or not _says(said, *_FREEZING):
        return False
    if _says(said, "potato", "potatoes", "chips", "chip", "fries"):
        return False
    if _BLANCHABLE.search(said):
        return True
    return not _FOOD.search(said) and any(phrase in said for phrase in (" if ", " and ",
                                                                       "what about", "then ",
                                                                       "when "))


def _blanching_or_freezing(understood):
    """The blanch row's guard: whether to blanch, or what to do about the freezer, which is the
    same step asked about keeping instead of eating."""
    return _asks_whether_the_step_is_needed(understood) or _a_freezing_question(understood)


def _says(said, *words):
    return any(re.search(r"\b" + word + r"\b", said) for word in words)


def _sift_reply(memory, understood):
    said = _said(understood)
    if _says(said, "icing sugar", "powdered sugar", "icing"):
        return ("Yes: icing sugar clumps as soon as the bag is open, and a lump shows in icing "
                "or sits in a dusting like grit. A sieve is quicker than a whisk for a smooth "
                "glacé icing, and a fine one gives the even dusting you want on a cake.")
    if _says(said, "cocoa"):
        return ("Yes, always: cocoa is the one that clumps hardest, and lumps will not beat out "
                "of a batter or a sauce. Sift it with the flour or whisk it into hot water first.")
    return ("Not from a fresh bag: modern plain and self-raising flour are already fine and "
            "loose. Sift it if the bag has been open for months, if there are lumps, or if you "
            "are making a light sponge or folding flour into beaten egg whites - the air sifting "
            "adds is what makes those rise. Cocoa powder always wants a sieve.")


def _peel_reply(memory, understood):
    said = _said(understood)
    if _says(said, "mash", "mashed"):
        return ("Not for mash: scrub them and leave the skin on if you like the flecks - most of "
                "the fibre sits there - and peel after boiling if you want the mash white and "
                "smooth. Peeling raw potatoes takes a third of the flesh off with the skin, so "
                "if you peel first, boil them in their own water.")
    if _says(said, "roast", "roasting", "roastie", "roasties", "oven"):
        return ("Yes for roast potatoes: peel them, cut them the same size, parboil 8 minutes, "
                "drain, shake in the pan to rough up the edges, then roast at 200C (180C fan) in "
                "hot fat for 40 to 45 minutes. Skins left on make a good, quicker wedge - just "
                "not a crisp roastie.")
    if _says(said, "boil", "boiling", "boiled", "salad", "salad"):
        return ("Not unless you want them white: scrub new potatoes and boil them with the skins "
                "on - that is where the fibre and a good part of the flavour sit - and peel only "
                "for mash, for a smooth soup, or if the skin has gone green or damaged.")
    if _says(said, "butternut", "squash", "pumpkin"):
        return ("Only if you want it in cubes: roast the halves cut side down in their skins - "
                "the flesh scoops out clean - but peel it for a soup or a tray of cubes, and "
                "mind your hands, because the skin is hard and slippy.")
    if _says(said, "beetroot"):
        return ("Roast them whole in their skins and the skin slips off afterwards: foil at 200C "
                "(180C fan) for an hour, then rub it away with kitchen paper. Peel raw beetroot "
                "only if you are grating it raw - but wear gloves, because it stains.")
    if _says(said, "sweet potato", "sweet potatoes"):
        return ("No need: the skin of a sweet potato is thin, it crisps in the oven, and it is "
                "where much of the fibre sits - scrub it and roast or bake it whole. Peel it "
                "only for a mash or a smooth soup.")
    if _says(said, "cucumber", "cucumbers"):
        return ("Only if the skin is thick, waxy or bitter at the stem end: a supermarket "
                "cucumber is fine unpeeled, and scoring it with a fork lengthways gives the "
                "ridged look without losing anything.")
    if _says(said, "carrot", "carrots", "parsnip", "parsnips", "swede", "turnip"):
        return ("Only if they are old: a young carrot or parsnip wants a scrub with a brush, "
                "while an old one tastes soapy and woody with the skin on. Peel a thin layer "
                "rather than down to the core, because the sweetest part is just under it.")
    if _says(said, "tomato", "tomatoes"):
        return ("Only for a smooth sauce or a clear soup: cut a small cross in the base, drop "
                "them in boiling water for 30 seconds and then into cold, and the skins slip "
                "off. For a chunky sauce or a tray of roasted tomatoes leave them on - they "
                "soften and disappear anyway.")
    return ("Only if the skin is thick, muddy or bitter. Scrubbing does the same job on "
            "anything thin-skinned and a good part of the flavour sits right under it, so peel "
            "as thinly as you can when you do.")


def _prick_reply(memory, understood):
    said = _said(understood)
    if _says(said, "potato", "potatoes", "jacket", "jackets", "spud", "spuds"):
        return ("Yes, 4 or 5 deep pricks with a fork: without them the steam has nowhere to go "
                "and a jacket potato bursts in the oven. Rub the skin with oil and salt first "
                "and it crisps while it bakes.")
    return ("Yes for anything with a skin going into a hot oven or a microwave - a tomato, a "
            "potato, an aubergine - so the steam has somewhere to go instead of splitting it "
            "open.")


def _score_reply(memory, understood):
    said = _said(understood)
    if _says(said, "pork", "crackling", "belly", "shoulder"):
        return ("Yes for crackling: score the skin about a centimetre deep in a diamond "
                "pattern, dry it well, rub in plenty of salt and start the joint hot. The "
                "scores are what let the fat render out and the skin bubble.")
    if _says(said, "bread", "dough", "loaf", "sourdough"):
        return ("Yes: one slash about a centimetre deep just before it goes in the oven lets "
                "the loaf open where you chose rather than where it wants to. A wet blade and a "
                "quick, confident cut are what make it clean.")
    if _says(said, "sausage", "sausages", "chipolata", "chipolatas", "black pudding"):
        return ("Not scored, and usually not even pricked: a good butcher's sausage pricked loses "
                "its juice, so cook it gently instead - a moderate pan or a 180C oven - and it "
                "will not split. A cheap, tight-skinned one splits whatever you do to it.")
    if _says(said, "fish", "salmon", "cod", "bass", "trout", "skin"):
        return ("Yes for a crisp pan skin: three shallow slashes through the skin stop the "
                "fillet curling and let the heat through. Score it before it goes in the pan, "
                "and dry the skin well.")
    return ("Yes when the skin has to let something out: a joint of pork for crackling, a loaf "
            "that has to open where you want it, a fish fillet that would curl. Score about a "
            "centimetre deep and dry the surface first.")


def _blanch_reply(memory, understood):
    said = _said(understood)
    # The freezer is its own question, and it is first: "do i need to blanch beans before
    # freezing them" is about keeping them, not about a salad, so the arm that answers it must
    # not be behind the nut, potato and tomato arms - and it reads the turn before, because
    # "and if im freezing them" is the same question without the vegetable in it.
    if _says(said, *_FREEZING):
        if _says(said, "potato", "potatoes", "chips", "chip", "fries"):
            # Raw potato goes black and mushy in the freezer, so "blanch potatoes before freezing"
            # is the freezer card's answer (cook them first), not this row's.
            return None
        if not (_BLANCHABLE.search(said) or _a_step_the_turn_before(memory)):
            return None
        return ("Yes before freezing: two minutes in boiling water, then straight into iced "
                "water, dry them and bag them. That is what stops the enzymes that turn them "
                "grey and soft, so they keep about a year instead of going limp and grassy in a "
                "couple of months, and they go into the pan straight from frozen. Cooked "
                "leftover vegetables are fine to freeze without blanching.")
    if _says(said, "almond", "almonds", "nut", "nuts", "hazelnut", "hazelnuts", "walnut",
                "walnuts", "pistachio", "pistachios"):
        return ("Only if you want the skins off: a minute in boiling water and then straight "
                "into cold, and each one slips out of its skin between your fingers. For "
                "flaked or ground almonds there is nothing to do.")
    if _says(said, "potato", "potatoes", "chips", "chip", "fries"):
        return ("For chips, yes: three minutes in boiling water, then drain and dry them "
                "completely before frying. That softens the outside, and the roughened surface "
                "is what turns crisp.")
    if _says(said, "tomato", "tomatoes"):
        return ("That is the peeling step: 30 seconds in boiling water and straight into cold, "
                "and the skins slip off. Nothing else needs it.")
    return ("Only if you are eating them later: two minutes in boiling salted water and then "
            "straight into iced water keeps green vegetables bright and just-cooked for a salad "
            "or a reheat. Into the freezer, it is the step that matters most - a minute or two "
            "blanched, then dried and bagged, and it keeps a year instead of going limp and "
            "grassy. Eaten straight away, steam them instead - one pan, and they keep more of "
            "the vitamins.")


def _parboil_reply(memory, understood):
    return ("Yes for roast potatoes and chips: about 8 minutes in boiling salted water until a "
            "knife goes in and the outside gives, then drain and shake them in the pan to "
            "roughen the edges, and roast at 200C (180C fan) in hot fat for 40 to 45 minutes. "
            "The roughened edges are what go crisp. Potatoes for mashing need the full boil, "
            "not this.")


def _rinse_reply(memory, understood):
    said = _said(understood)
    if _says(said, "quinoa"):
        return ("Yes, quinoa wants it: 30 seconds under cold water in a sieve takes off the "
                "saponin on the surface, which tastes soapy and bitter. It is the one grain that "
                "really needs it - and toast it dry in the pan afterwards and it smells nutty.")
    if _says(said, "barley", "pearl barley", "bulgur", "couscous", "lentil", "lentils"):
        return ("A quick rinse is enough, and it is mostly to check for grit and bits of husk: "
                "run cold water through it in a sieve until it runs clear. No soaking, no "
                "scrubbing - that is for dried beans, and it is a different question.")
    return ("A quick rinse under cold water is enough for most grains and pulses - it clears out "
            "dust and loose husk, and takes no more than a few seconds in a sieve. Rice is the "
            "one where rinsing is a real choice: rinse for separate grains, leave it for a "
            "risotto or a rice pudding.")


def _pat_dry_reply(memory, understood):
    return ("Yes, and it is the step people skip: a wet surface steams instead of browning, so "
            "pat meat, fish and potatoes dry with kitchen paper and salt them just before they "
            "go in the pan. It matters most for a steak, a chicken breast with the skin on and "
            "anything going into a hot oven.")


def _trim_reply(memory, understood):
    said = _said(understood)
    if _says(said, "steak", "beef", "pork", "lamb", "chicken", "meat", "joint", "gammon"):
        return ("Only if you want it leaner: a rim of fat bastes the meat and is what you are "
                "paying for, so leave it on and cut it away on the plate. Silverskin - the "
                "shiny, tough membrane - is the one that must come off, or the meat curls.")
    if _says(said, "asparagus"):
        return ("Yes, and the woody end knows where it is: bend each spear until it snaps, and "
                "throw the stub away - it is fibrous and never softens. Do not cut them all at "
                "the same length by eye, or you will keep the tough part on the thin spears.")
    if _says(said, "leek", "leeks"):
        return ("Yes: cut off the dark green top for stock, and slit the leek lengthways down "
                "the white so the grit between the layers can rinse out. A leek that looks clean "
                "is usually the one with sand in it.")
    if _says(said, "celery"):
        return ("A rinse and a trim of the base is enough. If the strings bother you, peel them "
                "off the outside of the stalk with a vegetable peeler - the flavour is in the "
                "stalk, not the strings.")
    return ("Only the tough bits: the stalk end of a bean, the woody end of an asparagus spear, "
            "the base of a sprout, the stringy root of a spring onion. Trimming more than that "
            "wastes the vegetable, and most of what people cut away cooks down to nothing anyway.")


# id, the verb's forms, the reply, what stands the row down, a guard that is not the plain one,
# a nudge towards the row, and a wider key where the same question is also asked as a method.
_STEPS = (
    ("sift", _SIFT, _sift_reply, (), None, 1),
    ("peel", _PEEL, _peel_reply,
     # a fruit's skin is `fruit-skin-edible`'s question, and ginger and garlic are peeled in
     # `cook-a-staple`: those cards answer the yes-or-no better than a general peel rule
     ("apple", "apples", "pear", "pears", "peach", "peaches", "plum", "plums", "banana",
      "bananas", "orange", "oranges", "kiwi", "avocado", "mango", "ginger", "garlic",
      "onion", "onions", "shallot", "shallots", "prawn", "prawns",
      # the mushroom card already answers peeling, and in better words
      "mushroom", "mushrooms"), None, 3),
    ("prick", _PRICK, _prick_reply,
     # `prick-sausages` is the sausage card, and it is the better answer for a sausage
     ("sausage", "sausages", "chipolata", "chipolatas", "black pudding"), None, 1),
    ("score", _SCORE, _score_reply,
     # the bread slash has a card of its own, and it words the angle and the rise better; a
     # sausage is not fenced here, because the reply's own first words say it is not scored
     ("bread", "dough", "loaf", "loaves", "sourdough", "banneton", "boules"), _how_or_whether, 3,
     _SCORE_ASK),
    ("rinse", _RINSE, _rinse_reply,
     # rice and mushrooms have cards of their own, and a tinned bean is drained, not rinsed.
     # Raw chicken especially: the food-safety card says not to wash it, and its answer is the
     # one that matters ("should i rinse the chicken" got grains advice without this).
     ("rice", "risotto", "sushi", "pudding", "mushroom", "mushrooms", "tinned", "canned",
      "already cooked", "drain", "chicken", "turkey", "beef", "pork", "lamb", "steak", "mince",
      "meat", "fish", "salmon", "prawn", "prawns", "bacon", "gammon", "sausage", "sausages"), None, 1),
    ("blanch", _BLANCH + _FREEZING, _blanch_reply, (), _blanching_or_freezing, 2),
    ("parboil", _PARBOIL, _parboil_reply, (), None, 1),
    ("pat-dry", _PAT, _pat_dry_reply, (), _patting_it_dry, 2),
    ("trim", _TRIM, _trim_reply, (), None, 1),
)

# Every step verb this module answers, for reading the subject of a follow-up off the turn before.
_STEP_VERBS = tuple(row[1] for row in _STEPS)

# One row per verb: the verb is the question, so one answer covers every food it is said of,
# and the food in the line only picks which sentence inside the reply. A row with `None` for its
# guard gets the module's own; anything else is that row's guard, even if it were ever to be a
# callable that is falsy.
_STEP_ROWS = [
    entry("prep-" + _id, (_forms, _ask or _ASK), _reply, avoid=_avoid, bias=_bias,
          guard=_asks_whether_the_step_is_needed if _guard is None else _guard)
    for _id, _forms, _reply, _avoid, _guard, _bias, _ask in
    [row + (None,) if len(row) == 6 else row for row in _STEPS]
]

# The domain's rows: the meat before the pan, and the steps that are not the cooking.
ENTRIES = _MEAT_ROWS + _STEP_ROWS
