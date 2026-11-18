"""Which one to buy: the variety of an everyday ingredient for the job in hand.

"which potatoes are best for mash", "what rice should i use for a risotto", "which cheese for
pizza" are not cooking-method questions and not recipe questions, and the bot had no answer for
any of them: on main all twelve lines measured either got the method card for the ingredient
("Boil them in salted water: 15 to 20 minutes ..."), a recipe for a dish nobody asked about
("How about mushrooms on toast ..."), or the punt ("I'm not sure about that one, sorry"). A
person choosing in a shop wants one thing - the name of the variety - so that is the first
sentence of every row here.

One domain of its own so that its ingredient names do not change how rare a word is inside
another domain's keys (lookup.entries points that out: a new domain may not take a point away
from an entry somewhere else).

The shape of the family, rather than a list of lines: the key is the ingredient, and the line
must be *choosing* one - `which`, `what sort of`, `best for`, `should i get`. A method line
("how do i boil potatoes") and a portion line ("how many potatoes per person") fail the guard
and keep the rows that answer them. The use decides the variety, so each row is one table of
(kind of job -> variety and why) and a plain "which potatoes are best" gets the split.
"""

import re

from .lookup import entry

ANSWERS = ("cooking", "food-and-drink")

# The words that make a line a choice rather than a question about the ingredient itself. The
# key below already holds them (a key word must be in the line for the row to score at all);
# this is the reading, for the lines that hold the ingredient and something that only looks
# like a choice.
_CHOOSING = re.compile(
    r"\b(which|what (sort|kind|type|variety)|best|better for|good for|should i (get|buy|use|pick)"
    r"|shall i (get|buy|use)|right (one|type|kind)|the one for)\b")
# A method, a portion or a recipe is a different row's question even when a choosing word is in
# the line: "whats the best way to boil potatoes" is the boiling row.
_NOT_A_CHOICE = re.compile(
    r"\b(how (long|many|much|do i|to)|minutes|temperature|calories|per person|recipe|reheat"
    r"|freeze|freezer|leftover|left over|calorie"
    # "is cheese good for you" is a health question that happens to hold the words "good for"
    r"|good for (you|me|us|kids|children|my|the)|bad for (you|me|us|kids|children|my|the)"
    r"|healthy|unhealthy|fattening)\b")


def _line(understood):
    """The repaired line, lower case, with a space at each end, for a whole-word search."""
    text = understood.get("plain") or understood.get("clean") or ""
    return " " + str(text).lower() + " "


def _names_pattern(names):
    """The ingredient words as one alternation, longest first so "plum tomatoes" wins."""
    return "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))


# A potato that tastes floury is not a fault and it is not a cooking question: it is the variety,
# which is the same thing this card answers when the line says "which". "my potatoes taste floury",
# "floury potatoes" and "is floury better for roast potatoes" had no card at all - the first and
# the third got the raw-flour sauce card and the calories card - so the words are read here.
_A_FLOURY_OR_WAXY = re.compile(r"\b(?:floury|waxy|fluffy)\b", re.IGNORECASE)


def _potato_kind_is_named(understood):
    """True when the line asks which sort of potato, by the chooser or by the sort's own word."""
    if _chooser(("potato", "potatoes", "spud", "spuds", "new potatoes"))(understood):
        return True
    if not isinstance(understood, dict):
        return False
    said = str(understood.get("text") or understood.get("clean") or "")
    if not said:
        said = " ".join(str(word) for word in understood.get("words") or ())
    return bool(_A_FLOURY_OR_WAXY.search(said)) and bool(re.search(r"\bpotato", said, re.I))


def _chooser(names):
    """A guard: the choosing word has to be about *this* ingredient.

    "which knife should i use for chopping an onion" and "which oil for roast potatoes" hold a
    choosing word, an ingredient and a use, and both are about the knife and the oil. So the
    choice has to be attached to the ingredient - "which potatoes", "what sort of potatoes",
    "potatoes ... should i use", "potatoes are best for" - and a word in between is a different
    subject. A method, a portion or a health question is turned away whatever the word order.
    """
    ingredient = _names_pattern(names)
    # "what kinds of rice are there" and "types of rice" ask for the range the card already holds
    # ("Basmati for curry, jasmine for Thai, arborio for risotto"), and the plural or the other word
    # order used to leave the line unanswered: the choosing word was only read as "what kind of".
    lead = re.compile(r"\b(which|what (sort|kind|type|variety)s? of|(sort|kind|type|variety)s? of|"
                      r"best|better|right)"
                      r"\s+(the\s+)?(" + ingredient + r")\b")
    # "which cut of lamb for a roast": the kind of thing being chosen is named between the
    # choosing word and the ingredient, and it is still the ingredient being chosen.
    cut = re.compile(r"\b(which|what)\s+((cut|piece|joint|part|side)s?\s+of\s+)(the\s+)?("
                     + ingredient + r")\b")
    # "what flour for bread": no verb at all, and the job is the only other half of the question.
    bare = re.compile(r"\bwhat\s+(the\s+)?(" + ingredient + r")\b[^.!?]{0,15}?\bfor\b")
    trail = re.compile(r"\b(" + ingredient + r")\b[^.!?]{0,30}?"
                       r"\b((should|do|shall|would) i (get|buy|use|pick)|is best|are best"
                       r"|best for|better for|good for)\b")
    # The map of the ingredient rather than one of it chosen for a job: "what kinds of rice are
    # there", "what are the different types of potato", "what potatoes are there". The plural is
    # the whole difference from "what kind of rice should i get", which the lead above reads, and
    # it is the same ask: the answer is the kinds and what each is for.
    kinds = re.compile(r"\b(?:what|which)\s+(?:are\s+the\s+|are\s+)?"
                       r"(?:different\s+|main\s+|other\s+|the\s+)?"
                       r"(?:kinds|types|sorts|varieties)\s+of\s+(?:the\s+)?(" + ingredient + r")\b"
                       r"|\b(?:what|which)\s+(" + ingredient + r")s?\b[^.!?]{0,24}?"
                       r"\b(?:are there|do you get|do you sell|come in)\b")

    def guard(understood):
        text = _line(understood)
        if _NOT_A_CHOICE.search(text):
            return False
        return bool(lead.search(text) or cut.search(text) or bare.search(text)
                    or trail.search(text) or kinds.search(text))
    return guard


def choosing(understood):
    """True when the line choosing a variety of one of these ingredients.

    `cooking.meal` asks this before it offers a dish: "what flour should i use for bread" holds
    two pantry ingredients, so the what-can-I-make-with table answered it with a pancake recipe.
    A line that is choosing a kind is not asking what to cook with it.
    """
    return any(e.guard(understood) for e in ENTRIES)


def _pick(rows, default):
    """A reply built from a (pattern -> sentence) table: the first use named wins."""
    def reply(memory, understood):
        text = _line(understood)
        for pattern, said in rows:
            if re.search(pattern, text):
                return said
        return default
    return reply


# Each ingredient is one entry whose reply reads the *use* out of the line. The variety is a
# fact about the ingredient, so one row answers every way of asking it and every use of it.
_POTATO = (
    (r"\broast(s|ed|ing)?\b|\broasties\b|\boven potato", 
     "Maris Piper or King Edward for roast potatoes: a floury one crisps at the edges where a "
     "waxy one goes hard and pale. Parboil 8 minutes, shake them in the pan to rough the edges, "
     "then roast at 200C (180C fan)."),
    (r"\bmash(ed|ing)?\b",
     "Maris Piper, King Edward or Rooster for mash: floury potatoes mash light, and waxy ones go "
     "gluey. Steam them dry for a minute after draining and mash with warm milk and butter."),
    (r"\bwedges?\b",
     "Maris Piper or King Edward for wedges: cut them into sixths, parboil 5 minutes, toss in oil "
     "and roast at 200C (180C fan) for 25 minutes. A floury potato crisps outside and stays fluffy "
     "in the middle."),
    (r"\bchips?\b|\bfries\b|\bchippy\b",
     "Maris Piper or Rooster for chips: floury potatoes take the double fry without going greasy, "
     "and the second fry at 190C is what makes them crisp."),
    (r"\bsalad\b|\bboil(ed|ing)? whole\b|\bnew potato",
     "Charlotte, Jersey Royal or Nicola for a salad or boiled whole: waxy potatoes hold their "
     "shape, where a floury one breaks up in the bowl."),
)

_APPLE = (
    (r"\bcrumble\b|\bpie\b|\btart\b|\bcook(ing|ed)?\b|\bbak(e|ing)\b|\bstew(ed|ing)?\b"
     r"|\bsauce\b|\bchutney\b|\bbramble\b",
     "Bramley for a crumble or a pie: it is sharp and collapses where an eater stays in lumps. "
     "One eater (Cox or Braeburn) to two Bramleys if you like a bit of bite left."),
    (r"\bsalad\b|\beat(ing)? raw\b|\braw\b|\bsnack\b|\blunchbox\b|\bcheese\b",
     "Cox, Braeburn or Gala for eating raw: firm, sharp and they do not go floury in a bag. "
     "Pink Lady and Jazz are sweeter, so keep them for a snack on their own."),
)

_ONION = (
    (r"\braw\b|\bsalad\b|\bsalsa\b|\bsandwich\b|\bguacamole\b|\bburger\b|\bchutney\b",
     "Red onion for anything raw - a salad, a salsa, a sandwich: it is milder and keeps its "
     "crunch. A shallot is gentler still and a good swap in a dressing."),
    (r"\bcurry\b|\bstew\b|\bsoup\b|\bbolognese\b|\bsauce\b|\bslow\b|\bcasserol|\bchilli\b"
     r"|\bbase\b|\bfry(ing)?\b|\bbrown(ing)?\b|\bpasta\b",
     "Brown onions for cooking: the most sugar, so they go sweet and soft in a curry or a stew. "
     "Shallots are milder and finer, which is why the French use them for a sauce."),
)

_TOMATO = (
    (r"\bsalad\b|\braw\b|\bsandwich\b|\bon toast\b|\bbruschetta\b",
     "Cherry or piccolo tomatoes for a salad: smaller and sweeter, because they are bred to be "
     "eaten raw. On the vine are fresher than loose ones, and never keep them in the fridge."),
    (r"\bsauce\b|\bpassata\b|\bpasta\b|\bstew\b|\bcook(ing|ed)?\b|\bbolognese\b|\bsoup\b"
     r"|\bsauce\b|\bpizza\b|\bcurry\b",
     "Plum tomatoes for a sauce - Roma or San Marzano: drier, fewer seeds, and they cook down "
     "sweet. Out of season a tin of plum tomatoes beats the fresh ones on the shelf."),
)

_RICE = (
    (r"\bcurry\b|\bbasmati\b|\bpilau\b|\bbiryani\b|\bindian\b|\bdaal\b|\bdhal\b",
     "Basmati for a curry: long, separate grains that stay light under a wet sauce. Wash it "
     "until the water runs clear and cook it 1 to 1.5 with water."),
    (r"\bthai\b|\bstir.?fr(y|ied)\b|\bjasmine\b|\bchinese\b|\bfried rice\b",
     "Jasmine for Thai and stir-fried dishes: softer and a little sticky, so it eats well with "
     "a wet sauce. Sushi wants short-grain, which is a different rice again."),
    (r"\bsushi\b|\bshort.?grain\b|\bkoshihikari\b",
     "Short-grain for sushi - sold as sushi rice, and koshihikari if you want the best: it is "
     "sticky enough to hold the roll together where long-grain falls apart. Rinse it until the "
     "water runs clear and use a little less water than the packet says."),
    (r"\brisotto\b|\barborio\b|\bcarnaroli\b|\bpaella\b|\bbomba\b|\bpudding\b|\bsoup\b",
     "Arborio or carnaroli for a risotto (carnaroli holds its bite better), bomba for a paella, "
     "and short pudding rice for rice pudding. None of them take kindly to being rinsed."),
)

_MUSHROOM = (
    (r"\bstir.?fr(y|ied)\b|\bnoodle|\basian\b|\bthai\b|\bchinese\b",
     "Oyster or shiitake for a stir-fry: they hold their shape and taste of something. Add them "
     "to a hot pan dry first, then the oil, or they steam."),
    (r"\bburger\b|\bgrill(ed|ing)?\b|\bstack\b|\bbreakfast\b|\btoast\b",
     "Portobello for a burger or under the grill: big, flat and meaty enough to be the main "
     "thing. Brush them with oil and grill 4 minutes a side."),
    (r"\bsalad\b|\braw\b",
     "Button mushrooms for a raw salad: mild and firm. They are grown in compost, so wipe them "
     "rather than soak them, and dress them just before serving."),
)

_CHEESE = (
    (r"\bpizza\b|\bmelting\b|\bmelt\b|\btoastie\b|\bcalzone\b",
     "Low-moisture mozzarella for a pizza: it melts and stretches without a puddle, which fresh "
     "mozzarella will give you. Tear a fresh one and drain it on kitchen paper first if that is "
     "what you have."),
    (r"\bsandwich\b|\btoast\b|\bsauce\b|\bmacaroni\b|\bcauliflower\b|\bcrumble\b|\bpasta bake\b",
     "A mature cheddar for a sandwich or a cheese sauce: it carries the flavour when it is "
     "diluted. Gruyere melts more smoothly, so a rarebit or a fondue wants that."),
    (r"\bgrat(ed|ing)?\b|\bpasta\b|\brisotto\b|\bsoup\b",
     "Parmesan (or pecorino) for grating over pasta, risotto or soup: salty and dry, so a little "
     "goes a long way. Buy it in a wedge and grate it; the ready-grated tub tastes of nothing."),
    (r"\bsalad\b|\bfeta\b|\bhalloumi\b|\bgreek\b",
     "Feta for a salad: salty and crumbly, and it does not melt into the leaves. Halloumi is the "
     "one for grilling or frying, because it holds its shape."),
)

_FISH = (
    (r"\bcurry\b|\bstew\b|\bpie\b|\bsoup\b|\bcasserole\b|\btraybake\b|\bbake\b",
     "A firm white fish for a curry, a pie or a traybake - cod, haddock or hake: it holds "
     "together where a delicate one flakes away. Add it late and cook it gently."),
    (r"\bfr(y|ied|ying)\b|\bpan\b|\bgrill(ed|ing)?\b|\broast(ed|ing)?\b",
     "A firm white fish (cod, haddock, hake) or an oily one (salmon, mackerel) for the pan or the "
     "grill: both stand up to the heat. Mackerel is the cheapest fish worth eating twice a week."),
    (r"\bsalad\b|\bsandwich\b|\braw\b|\bsushi\b",
     "Salmon, tuna or a hot-smoked fish for a salad or a sandwich: meaty enough to be the main "
     "thing. Raw fish for sushi wants fish frozen first and sold as sushi grade."),
)

_BEEF = (
    (r"\bstew(s|ed|ing)?\b|\bslow\b|\bcasserole\b|\bbraise[ds]?\b|\bpot roast\b|\bpie\b|\bcurry\b"
     r"|\bmince\b|\bbolognese\b",
     "Chuck or blade for a stew or anything slow: both are full of connective tissue, which "
     "turns to gelatin and gives you a thick gravy. 2 to 3 hours at a bare simmer, and never a "
     "rolling boil."),
    (r"\broast\b|\bsunday\b|\bcarvery\b",
     "For roasting, topside or silverside for lean and easy to carve, or rib for flavour and "
     "fat. Beef for roasting wants 20 minutes at 220C then 15 minutes per 500g at 180C for rare."),
    (r"\bsteak\b|\bfry(ing)?\b|\bgrill(ed|ing)?\b|\bbarbecue\b|\bbbq\b|\bsandwich\b",
     "Ribeye for flavour, sirloin for a firmer bite, fillet for tenderness and the most money "
     "for the least taste. For a steak sandwich, a cheaper cut - flank or bavette - sliced thin "
     "across the grain is what restaurants use."),
)

_FLOUR = (
    (r"\bbread\b|\bpizza\b|\bbaguette\b|\bbap\b|\bfocaccia\b|\bpitta\b|\bnaan\b",
     "Strong white bread flour for bread and pizza: the extra gluten is what makes the dough "
     "rise and stretch. Plain flour makes a flat, crumbly loaf, and wholemeal needs a little "
     "extra water and a longer rise."),
    (r"\bcake\b|\bsponge\b|\bscone\b|\bself.?raising\b|\bvictoria\b|\bmuffin\b|\bflapjack\b",
     "Self-raising flour for a sponge or a scone, or plain flour with 2 teaspoons of baking "
     "powder per 100g. Strong bread flour is the one to keep out of a cake, because the gluten "
     "makes it chewy."),
    (r"\bpastry\b|\bpie\b|\btart\b|\bshortcrust\b|\byorkshire\b|\bbatter\b|\bsauce\b"
     r"|\bthicken\b|\bcrumble\b",
     "Plain flour for pastry, Yorkshire pudding, batter and sauces: no raising agent and less "
     "gluten than bread flour, so it stays short and crisp. Cornflour thickens a sauce without "
     "flouring the taste."),
)

_CHOCOLATE = (
    (r"\bbrownie|\bcake|\bcookie|\bbiscuit|\bmelt|\bbaking|\bbake|\bmousse|\btruffle"
     r"|\bganache|\bsauce|\bicing|\bicing sugar|\bcooking\b",
     "A 70% dark chocolate for brownies and cakes: bitter enough to cut the sugar in the batter, "
     "and it melts cleanly. Milk chocolate makes a brownie too sweet and 85% makes it dry, so "
     "70% is the one to buy."),
    (r"\beat(ing)?\b|\bsnack\b|\bgift\b|\bbar\b|\braw\b|\bhot chocolate\b|\bdrink\b",
     "For eating on its own, 70% is where chocolate starts to taste of something: a supermarket "
     "own-brand 70% is as good as the expensive bars for most people. Milk chocolate is a "
     "different thing, and better eaten than baked with."),
)

_LAMB = (
    (r"\bslow\b|\bstew(s|ed|ing)?\b|\bcasserole\b|\bbraise[ds]?\b|\bpulled\b|\bcurry\b",
     "Shoulder for anything slow, or neck fillet cut into chunks for a stew: both give up their "
     "fat and gelatine over a couple of hours. Leg is the one to keep for roasting, because it "
     "is leaner and goes dry in a casserole."),
    (r"\broast\b|\bsunday\b|\bcarvery\b|\bjoint\b",
     "A leg for a roast - bone in for flavour, boned and rolled for easy carving. Shoulder is "
     "cheaper, sweeter and needs 4 hours at 160C instead of 20 minutes a pound at 200C."),
    (r"\bchop|\bgrill(ed|ing)?\b|\bbbq\b|\bbarbecue\b|\bfr(y|ied|ying)\b|\bpan\b",
     "Chops for the grill or the pan - loin for lean, best end for the sweetest - and they want "
     "4 minutes a side from room temperature. Cutlets and neck fillet are the cheaper ones that "
     "still take a quick cook."),
)

# The key only has to earn the threshold: the guard is what decides whether the line is a
# choice about this ingredient, so plain "what" is enough beside the ingredient word.
_CHOOSE_WORDS = ("which", "what", "what sort", "what kind", "what type", "best for", "better for",
                 "good for", "should i get", "should i buy", "should i use", "shall i get",
                 "do i use", "do i get", "do i buy", "should i pick", "right one", "the one for",
                 # the map of the ingredient, asked in the plural: "what kinds of rice are there"
                 "what kinds", "what types", "what sorts", "what varieties", "which kinds",
                 "which types", "kinds of", "types of", "sorts of")

ENTRIES = (
    entry("pick-potato",
          (("potato", "potatoes", "spud", "spuds", "new potatoes"),
           _CHOOSE_WORDS + ("floury", "waxy", "fluffy")),
          _pick(_POTATO,
                "Floury potatoes (Maris Piper, King Edward, Rooster) for roast, mash and chips, "
                "waxy ones (Charlotte, Jersey Royal, Nicola) for salads and boiling whole. The "
                "bag says which on the front, so buy by that rather than by the price."),
          avoid=("how long", "minutes", "temperature", "calories", "per person", "recipe",
                 "reheat", "freeze", "leftover", "left over", "grow", "growing", "chit",
                 "sprout", "green", "peel"),
          guard=_potato_kind_is_named,
          bias=2),
    entry("pick-apple",
          (("apple", "apples"), _CHOOSE_WORDS),
          _pick(_APPLE,
                "Bramley for cooking, Cox or Braeburn for eating: a Bramley is sharp and falls "
                "apart, and an eater stays in pieces. A bag of 'cooking apples' at the market is "
                "a Bramley."),
          avoid=("how long", "keep", "keeping", "store", "storage", "brown", "went brown",
                 "calories", "healthy", "tree", "grow", "growing", "recipe"),
          guard=_chooser(("apple", "apples")),
          bias=2),
    entry("pick-onion",
          (("onion", "onions", "shallot", "shallots"), _CHOOSE_WORDS),
          _pick(_ONION,
                "Brown onions are the all-rounder: sweet and soft once cooked. Red for anything "
                "raw, shallots for a sauce you want gentler, and white for a Mexican dish."),
          avoid=("how long", "keep", "keeping", "store", "sprout", "sprouting", "make me cry",
                 "cry", "eyes water", "chop", "chopping", "peel", "recipe", "calories"),
          guard=_chooser(("onion", "onions", "shallot", "shallots")),
          bias=2),
    entry("pick-tomato",
          (("tomato", "tomatoes", "cherry tomatoes", "plum tomatoes"), _CHOOSE_WORDS),
          _pick(_TOMATO,
                "Plum tomatoes for cooking and cherry ones for eating raw: plum are drier and "
                "fewer-seeded, so they make a sauce; cherry are sweeter, so they make a salad."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "refrigerate", "ripen",
                 "ripening", "green", "blight", "grow", "growing", "plant", "recipe", "calories"),
          guard=_chooser(("tomato", "tomatoes", "cherry tomatoes", "plum tomatoes")),
          bias=2),
    entry("pick-rice",
          (("rice", "basmati", "jasmine rice", "risotto rice", "pudding rice"), _CHOOSE_WORDS),
          _pick(_RICE,
                "Basmati for curry, jasmine for Thai and stir-fried, arborio or carnaroli for "
                "risotto, pudding rice for rice pudding. Plain long-grain is the all-rounder and "
                "the one to buy in a big bag."),
          avoid=("how long", "minutes", "cook", "cooking", "wash", "rinse", "leftover",
                 "left over", "reheat", "freeze", "calories", "per person", "microwave",
                 "recipe", "water",
                 # a phone in a bag of rice is the phone's question: "is rice good for a wet
                 # phone" was told basmati for curry and jasmine for Thai (@ivory-magnet, #9232
                 # family). Rice varieties are never about a device that got wet.
                 "phone", "phones", "iphone", "mobile", "laptop", "tablet", "camera",
                 "device", "wet phone", "water damage", "dropped", "dropped it",
                 # which rice is this row's question; rice against another carb is the
                 # comparison row's: "is rice or pasta better for you" was told which rice goes
                 # with curry, and it had asked which of the two to eat
                 "or pasta", "or potatoes", "or potato", "or bread", "or noodles", "or couscous",
                 "better for you", "healthier", "healthiest"),
          guard=_chooser(("rice", "basmati", "jasmine rice", "risotto rice", "pudding rice")),
          bias=2),
    entry("pick-mushroom",
          (("mushroom", "mushrooms"), _CHOOSE_WORDS),
          _pick(_MUSHROOM,
                "Chestnut mushrooms are the all-rounder for cooking, button for raw, portobello "
                "for a burger, and oyster or shiitake for a stir-fry. Wipe them rather than "
                "washing them."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "wash", "washing", "dirt",
                 "grow", "growing", "pick", "picking", "forage", "foraging", "recipe",
                 "calories", "poisonous", "safe"),
          guard=_chooser(("mushroom", "mushrooms")),
          bias=2),
    entry("pick-cheese",
          (("cheese", "cheddar", "mozzarella", "parmesan", "feta"), _CHOOSE_WORDS),
          _pick(_CHEESE,
                "Cheddar is the all-rounder for cooking and sandwiches, mozzarella for a pizza, "
                "parmesan for grating and feta for a salad. Gruyere is the one that melts "
                "smoothly for a rarebit."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "freeze", "mould", "mold",
                 "calories", "healthy", "lactose", "milk", "vegan", "recipe"),
          guard=_chooser(("cheese", "cheddar", "mozzarella", "parmesan", "feta")),
          bias=2),
    entry("pick-fish",
          (("fish", "cod", "haddock", "salmon", "mackerel", "hake"), _CHOOSE_WORDS),
          _pick(_FISH,
                "Cod, haddock or hake for anything that cooks in a sauce, salmon or mackerel for "
                "the pan and the grill, and a firm white fish for a pie. Mackerel is the "
                "cheapest fish worth eating every week."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "freeze", "fresh", "smell",
                 "calories", "healthy", "mercury", "pregnant", "bone", "bones", "recipe",
                 "sustainable", "farmed", "wild"),
          guard=_chooser(("fish", "cod", "haddock", "salmon", "mackerel", "hake")),
          bias=2),
    entry("pick-flour",
          (("flour", "bread flour", "self raising flour", "plain flour"), _CHOOSE_WORDS),
          _pick(_FLOUR,
                "Strong white bread flour for bread and pizza, plain for pastry and sauces, "
                "self-raising for a sponge. The bag names the job on the front."),
          avoid=("how long", "keep", "keeping", "store", "weevils", "moths", "calories",
                 "healthy", "gluten", "freeze", "recipe", "substitute", "instead of"),
          guard=_chooser(("flour", "bread flour", "self raising flour", "plain flour")),
          bias=2),
    entry("pick-chocolate",
          (("chocolate", "dark chocolate", "milk chocolate"), _CHOOSE_WORDS),
          _pick(_CHOCOLATE,
                "70% dark for baking and for eating on its own: it is the one that tastes of "
                "chocolate without being bitter. Milk chocolate is for eating."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "bloom", "white bloom",
                 "calories", "healthy", "caffeine", "dogs", "dog", "melt", "temper", "recipe"),
          guard=_chooser(("chocolate", "dark chocolate", "milk chocolate")),
          bias=2),
    entry("pick-lamb",
          (("lamb", "mutton"), _CHOOSE_WORDS),
          _pick(_LAMB,
                "Shoulder for anything slow, leg for a roast, chops for the grill. Shoulder is "
                "the cheaper half and the one with more flavour."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "freeze", "mince",
                 "defrost", "calories", "healthy", "pink", "safe", "food poisoning",
                 "recipe", "price"),
          guard=_chooser(("lamb", "mutton")),
          bias=2),
    entry("pick-beef",
          (("beef", "steak", "chuck", "brisket", "mince"), _CHOOSE_WORDS),
          _pick(_BEEF,
                "Chuck or blade for anything slow, topside or rib for a roast, ribeye or sirloin "
                "for a steak. The cheap cuts are the ones with the flavour; they just need time."),
          avoid=("how long", "keep", "keeping", "store", "fridge", "freeze", "mince",
                 "defrost", "calories", "healthy", "iron", "pink", "safe", "food poisoning",
                 "recipe", "price", "cheap", "price per"),
          guard=_chooser(("beef", "steak", "chuck", "brisket", "mince")),
          bias=2),
)
