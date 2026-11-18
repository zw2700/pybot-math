"""Three everyday kitchen questions the cooking table had no answer for.

Cooking itself is too big to add to: bot/knowledge/cooking.py is at the hub's one-megabyte
limit, so a change to it cannot be uploaded at all. The rows here are new answers rather than
edits to an existing one, which makes this the cheap place to put them - they are ordinary
cooking entries with the same key, reply and avoid shape as the rest.

Each of these was measured on the whole bot before it was written:

  why is my bread crumbly            "I don't know enough to answer that honestly. A search..."
  what is a roux                     "I'm not sure about that one, sorry - I'd rather not guess"
  my freezer is full what can i do   "A dead appliance is usually the plug, the fuse or a door switch"

A crumbly loaf is a baking fault (water, flour, kneading, a warm cut) and not a stale or a flat
one, so those rows keep their lines. "What is a roux" is a definition and the sauce row's reply
opens with the pan, so the definition has its own row and the sauce row stands down for it. And
a freezer with no room in it is not a broken appliance: `appliance-broken` in home.py keeps
"what can i do" in its key for its own lines, and now stands down for a full or packed freezer.

Four sentences at most for a kitchen answer, cause first: that is what a person wants back.

The last three are the other half of the baking and sauce faults. A loaf that collapses, a
sourdough starter that stops working and a soup that curdles each name a fault the table had no
row for, so all eight ways of saying them were a shrug or an echo ("why does my bread collapse"
was a search hedge, "my bread keeps collapsing" was "Thanks for telling me"). They are apart from
the neighbours on purpose: the dense-bread answer owns "sank in the middle" and "dense", the flat
cake answer owns "my cake sank", and the split-sauce answer owns "my sauce split" - a soup is a
pot of liquid with dairy or egg in it and wants the prevention, not the rescue.

The two rows at the end of the file came later. "My curry went wrong", with no word for what it
did, reached no row at all: every fault has one of its own - split, watery, salty, lumpy, mushy,
sank, did not rise - so the line that names none of them got "I'm listening - say more if it
helps", and "i ruined the curry" got the roast meat answer about resting a joint. A dish that
went wrong is a short list of faults, and that list is the answer: four for a pot, three for a
bake. Once the line names the fault the row for that fault is more specific and keeps it.
"""

import re

from .dishes import a_plan_that_might_be_ruined, not_ruled_out
from .lookup import entry
from .cooking import JACKET_FILL, _crowd, _crowd_meal, _occasion

ANSWERS = ("cooking",)

ENTRIES = [
# "What can i bake" was answered with garden plants: `plants-for-sun` in garden.py keys "baking"
# (as in a baking hot border) beside "what can i", so every "what can i bake" line - with
# bananas, with the kids, an easy one, a birthday - got lavender and salvia. The garden key says
# "baking hot" now, and the baking question has a row of its own, with the four things a person
# can start this afternoon and the one habit that stops a cake sinking.
entry("bake-ideas",
      (("what can i bake", "what should i bake", "what shall i bake", "what can we bake",
        "what should we bake", "what to bake", "what can i bake today", "bake something",
        "something to bake", "baking ideas", "ideas for baking", "want to bake",
        "want to do some baking", "feel like baking", "fancy baking", "start baking",
        "get into baking", "getting into baking", "learn to bake", "what could i bake"),
       ("bake", "baking", "baked", "oven", "flour", "cake", "cakes", "biscuits", "cookies",
        "bread", "scones", "brownies", "easy", "quick", "simple", "today", "tonight",
        "weekend", "kids", "children", "beginner", "first time", "sweet", "something",
        "nothing", "banana", "bananas", "chocolate", "lemon")),
      "Scones take 15 minutes, flapjacks 25, a Victoria sponge 40 and banana bread an hour, so "
      "start with whichever time you have, and ripe bananas are the reason to make the last "
      "one. Weigh everything out before you start, cream the butter and sugar until the mixture "
      "is pale, and keep the oven door shut for the first two thirds of the time, because the "
      "cold air that gets in is what makes a cake sink.",
      # a sale, a birthday and a party have their own answers, and so do bread, pastry and the
      # two things with "baked" in the name that are not baking
      avoid=("cake sale", "bake sale", "sale", "stall", "school fair", "fete", "fayre",
             "birthday", "wedding", "christening", "party", "celebration", "how many people",
             "tin size", "which tin", "how long", "temperature", "gas mark", "fan oven",
             "bake blind", "blind", "pastry", "shortcrust", "baked potato", "baked potatoes",
             "jacket potato", "baked beans", "bake beans", "no oven", "microwave", "air fryer",
             "sourdough", "yeast", "why did my", "why is my", "sank", "soggy", "burnt",
             "crumbly", "stodgy", "goes flat", "went flat", "pizza", "casserole",
             "one pot", "traybake chicken", "fish", "salmon", "chicken")),

# "What is a roux" is a definition and "how do i make one" is a method, and the how-to reply
# opens with the pan, not with what a roux is. One row for the definition, and the sauce row
# stands down for it below.
entry("what-a-roux",
      (("roux", "beurre manie", "beurre manié"),
       ("what is", "whats a", "what's a", "what is a", "explain", "mean", "means",
        "definition", "difference", "used for", "for")),
      "A roux is equal weights of butter or oil and plain flour cooked together in a pan, and "
      "it is what thickens a white sauce, a gravy or a soup: melt 25g of butter, stir in 25g "
      "of plain flour and cook it a minute to take the raw flour taste off, then add the milk "
      "or stock a splash at a time, whisking. A pale roux thickens most, and the darker you "
      "cook it the less it thickens, which is why a brown roux for gravy needs more flour.",
      avoid=("without flour", "cornflour", "corn flour", "gluten free", "gluten-free",
             "cheese sauce", "white sauce", "bechamel", "béchamel")),

# A crumbly loaf is not a stale one and not a flat one: it is water, flour and kneading, and
# it had no answer at all ("why is my bread crumbly" was a search hedge).
entry("bread-crumbly",
      (("bread", "loaf", "loaves", "sourdough", "buns", "roll", "rolls", "focaccia"),
       ("crumbly", "crumbles", "crumbling", "falls apart", "falling apart", "fall apart",
        "breaks up", "breaking up", "falls to pieces", "sandy", "stodgy and dry",
        "dry and crumbly", "wont hold together", "won't hold together")),
      "Crumbly bread is usually too little water or too much flour: the dough should be tacky "
      "and slightly sticky rather than dry enough to handle, so hold back a little of the "
      "flour and weigh it rather than scooping with a cup. Knead until a piece stretches thin "
      "enough to see light through it, which is what holds the crumb together, and let the "
      "loaf cool on a rack for an hour before cutting, because warm bread tears. If it is also "
      "pale and heavy, the oven was too cool or the loaf was under-proved.",
      # a stale, mouldy or flat loaf is another row's answer
      avoid=("stale", "mouldy", "mould", "mold", "green", "rise", "rising", "flat", "yeast",
             "prove", "proof",
             # a cake is not a loaf, and "crumbly" was taking cakes through the "cake" in the
             # key above: a crumbly cake is fat, egg and over-mixing, not water and kneading
             "cake", "cakes", "sponge", "sponges", "muffin", "muffins", "cupcake", "cupcakes",
             "traybake", "tray bake", "brownie", "brownies", "scone", "scones")),

# A freezer packed to the door is the other freezer question, and the broken-appliance row in
# home.py was answering it ("my freezer is full what can i do" got the plug and fuse answer)
# because "what can i do" was in its key.
entry("freezer-full",
      (("freezer", "freezers", "freezer drawer", "chest freezer"),
       ("full", "full up", "too full", "packed", "overfull", "no room", "stuffed",
        "no space", "run out of room", "run out of space", "bursting")),
      "A freezer works best about three-quarters full: the frozen food holds the cold, but "
      "packed to the door it cannot move air and the food at the front starts to thaw. Freeze "
      "flat in bags with the air pressed out and stand them on edge like files, keep the "
      "oldest at the front so it goes first, and use the crush to cook from it - a full "
      "freezer is a week of dinners if you eat what is in it. A drawer that will not close "
      "means it is time for a clear-out, not more squeezing.",
      avoid=("defrost", "not working", "broken", "dead", "died", "faulty", "ice", "frost",
             "smell", "leak", "cold", "warm", "temperature")),
# A crumbly cake was reaching the bread row above ("why is my cake crumbly" got water, flour
# and kneading), because "cake" sat in that row's key. A cake crumbles for the opposite reasons
# a loaf does: too much flour or too little fat and egg, and a batter beaten on after the flour
# went in. Kept apart from the flat-bake row in cooking.py by the fault words: that one is the
# cake that did not rise, this one is the cake that did.
entry("cake-crumbly",
      (("cake", "cakes", "sponge", "sponges", "muffin", "muffins", "cupcake", "cupcakes",
        "loaf cake", "traybake", "tray bake", "brownies", "brownie", "victoria sponge"),
       ("crumbly", "crumbles", "crumbling", "falls apart", "falling apart", "fall apart",
        "falls to pieces", "sandy", "wont hold together",
        "won't hold together", "breaks up", "breaking up")),
      "A crumbly cake usually has too much flour or too little fat and egg, or it was beaten "
      "on after the flour went in: weigh the flour rather than scooping it with a cup, and stop "
      "mixing the moment the last streaks of flour disappear. Take it out a shade early rather "
      "than late, because five extra minutes dries a sponge and dry is what crumbles, and cool "
      "it in the tin for ten minutes before turning it out. Cut it cold: a cake cut warm breaks "
      "the crumb as the knife goes through.",
      # the cake that did not rise, the cake that sank and the cake's icing are other rows
      avoid=("rise", "rises", "risen", "rising", "didnt rise", "not risen", "sinking", "sank",
             "sunken", "icing", "frosting", "buttercream", "tin size", "how long in the oven",
             # "my sponge is dry and crumbly" is the dry-bake answer's line: a dry sponge is
             # too long in the oven, and this row only says dry crumbles as a consequence
             "dry", "dried out", "overbaked", "over baked",
             "how do i make", "recipe", "bake a cake", "make a cake", "freeze", "freezing",
             # a keeping question after a crumbly cake is about the cake's shelf life, not the
             "keep", "keeps", "keeping", "kept", "last", "lasts", "how long", "fridge",
             "refrigerate", "store", "storing", "stored", "stays fresh", "still good")),

# A cloudy stock is not a cloudy drink and not a cloudy beer: it is a stock that boiled, or one
# that was never skimmed, and it can be cleared with an egg white raft. Nothing answered it.
entry("stock-cloudy",
      (("stock", "broth", "bouillon", "consomme", "consommé", "chicken stock", "beef stock",
        "vegetable stock", "bone broth"),
       ("cloudy", "clouded", "murky", "not clear", "unclear", "bits in it", "sediment",
        "how do i clear", "clear it", "make it clear", "looks cloudy")),
      "A cloudy stock boiled: once it comes to the boil the fat and protein break up into "
      "droplets that nothing will settle again, so keep it at the barest simmer with the lid "
      "off and skim the grey foam off the top in the first twenty minutes. To clear one that "
      "has already gone cloudy, whisk a lightly beaten egg white into the cold stock, bring it "
      "slowly to a simmer and let the white rise and set as a raft, then lift it out with the "
      "bits trapped in it. Strain through a sieve lined with kitchen paper, and do not stir it "
      "while it simmers or the raft breaks up.",
      avoid=("beer", "lager", "ale", "wine", "juice", "cider", "gravy", "sauce", "soup",
             "cloudy day", "weather", "sky", "rain", "urine", "water", "aquarium")),

# Oil in baking is not the swap question and not the buying question: "how much oil do i put in
# a cake" was a shrug, "how much cooking oil in a cake" was the buying advice about brands, and
# "can i use olive oil in a cake" got the advice on choosing and storing a bottle. The amount,
# the choice of oil and whether olive oil belongs are one answer, and the amount is the same
# fraction whatever the recipe: 80g of oil for every 100g of butter.
#
# "instead of" is where the swap table is, and a spent pan is its own question, so this row
# stands aside for both rather than saying the same thing twice with a different number.
entry("oil-in-a-cake",
      (("oil", "olive oil", "vegetable oil", "sunflower oil", "rapeseed oil", "cooking oil"),
       ("cake", "cakes", "sponge", "muffin", "muffins", "brownies", "brownie",
        "traybake", "tray bake", "carrot cake", "chocolate cake", "banana bread")),
      "Use 80g of oil for every 100g of butter the recipe asks for - about 4 to 5 tablespoons in "
      "a 20cm cake - and expect a slightly denser, moister crumb. Sunflower, vegetable or "
      "rapeseed gives a light plain cake; keep olive oil for a cake with a flavour of its own, "
      "like carrot or chocolate, where a good extra virgin is an asset rather than a taste you "
      "notice. Skip it where the method creams butter and sugar for air, and in pastry.",
      # "can i use olive oil in brownies" ties with the spent-pan row (both match the oil and
      # the asking shape, and that row weighs 5 for its own reuse lines), so a spot that suits
      # a salad but not a cake is what decides it here. Main's spent-pan row gained weight
      # again since, so the nudge is 5 to keep a brownie with the cake.
      bias=5,
      ask=("how much", "how many", "how", "which", "what", "can i", "could i", "do i",
           "should i"),
      avoid=("instead of", "swap", "swapping", "replace", "replacing", "substitute",
             # a cake that wants making is a recipe line, and the recipe rows answer those
             "recipe", "make a cake", "make the cake", "make my cake", "bake a cake",
             "icing", "frosting", "buttercream", "tin size", "how long in the oven",
             # keeping, buying and reuse are their own rows, and each one has a home already
             "store", "storing", "keep", "keeping", "go off", "goes off", "gone off", "last",
             "healthiest", "healthy", "calorie", "calories", "reuse", "reusing", "deep fat",
             "fry", "frying", "oil paint", "hair", "skin", "drizzle", "dressing",
             # A line that names both fats is a choice between them, and the comparison row owns
             # that question: "should i use butter or oil in a sponge" wants which one, not how
             # much. Only the butter shapes are here, so "can i use olive oil or sunflower oil in
             # a cake" keeps the swap row.
             "butter or", "or butter",
             # "how much oil for a cake tin" is greasing and lining, not the swap: the tin sizes
             # card answers it. A loaf of bread is not a cake swap either - the bread rows hold
             # the ratio - but "loaf cake" and "banana bread" are still cakes, so nothing here
             # may be the bare word "cake", "bread" or "loaf".
             "cake tin", "cake tins", "loaf tin", "tin", "tins", "grease", "greasing",
             "greased", "line the tin", "lining the tin", "loaf of bread", "bread dough",
             "dough")),

# A question about the freezer is not a keeping question, and two rows were answering it with
# the fridge rule: "can i freeze rice" and "can i freeze cooked rice" got "it keeps 24 hours in
# the fridge, no longer" from `rice-storage`, and "can i freeze bread" got "keep bread at room
# temperature, not the fridge" from `bread-keep`. Both keys hold a freeze word, and both rows
# are right for their own line. These two rows are the freeze half, and they carry a bias
# because the keeping rows reach the same line on the same score.
entry("freeze-cooked-rice",
      (("rice", "basmati", "long grain rice", "white rice", "cooked rice", "leftover rice"),
       ("freeze", "freezes", "freezing", "frozen", "freezer", "can i freeze", "freeze it")),
      "Yes: cool it within the hour, box it while it is still warm rather than hot, and freeze "
      "it the same day - cooked rice keeps about a month in the freezer. Reheat it once until "
      "it is piping hot all the way through, and do not freeze it again after that.",
      ask=("freeze", "freezer", "frozen", "freezing"),
      bias=1,
      # frying it, making it or boiling it is another row's question
      avoid=("fry", "fried", "stir fry", "bake", "boil", "cook it", "how do i cook",
             "how long does it take", "reheat", "microwave", "pudding", "risotto")),

entry("freeze-bread",
      (("bread", "loaf", "loaves", "sliced loaf", "sourdough"),
       ("freeze", "freezes", "freezing", "frozen", "freezer", "can i freeze", "freeze it")),
      "Slice it first, then bag it: bread keeps about three months in the freezer and the "
      "slices go straight into the toaster from frozen. Freeze it on the day you buy it, "
      "because a loaf frozen when it is already going stale thaws out stale.",
      ask=("freeze", "freezer", "frozen", "freezing"),
      bias=1,
      # a fresh, stale or mouldy loaf is another row's answer, and so is making it.
      # dough is the other freezing question, and "can i freeze bread dough" wants the rise
      # and the bag rather than a sliced loaf
      avoid=("fresh", "stale", "mouldy", "mould", "mold", "keep", "store", "last", "rise",
             "rising", "prove", "proof", "bake", "recipe", "crumbs", "sauce", "butter",
             "dough", "batter")),
# "ideas for a roast" was answered with roast veg pasta and "what goes with a roast" with the
# potatoes alone: the potato and side rows key on a named meat or a named vegetable, and a line
# that names nothing past the roast had no menu. This is the whole plate.
entry("roast-dinner-menu",
      (("roast", "roast dinner", "sunday roast", "roasting joint", "roast lunch"),
       ("ideas", "menu", "what else", "what should i have", "what should i make",
        "what to serve", "what can i serve", "what goes with", "what to have with", "sides",
        "side dishes", "serve with", "have with", "cook with it")),
      "A roast is one joint, potatoes, two veg and gravy, and the veg is where you ring the "
      "changes: carrots and parsnips roasted round the meat for the last 45 minutes, greens or "
      "cabbage steamed, and peas with mint if it is lamb. Add Yorkshire puddings for beef, "
      "stuffing and apple sauce for pork, bread sauce for chicken or turkey. Work back from the "
      "meat, because the joint rests 20 minutes and that is when the potatoes go up to full "
      "heat.",
      # a named meat or a named vegetable is a different question with its own row, and so is
      # the timing of the joint: "what goes with roast lamb" and "how long do i roast a chicken"
      # must keep the answers they already give
      avoid=("lamb", "beef", "chicken", "pork", "turkey", "gammon", "duck", "ham", "goose",
             "potato", "potatoes", "parsnip", "parsnips", "carrot", "carrots", "yorkshire",
             "how long", "temperature", "temp", "gas mark", "defrost", "frozen", "freeze",
             "leftover", "leftovers", "veg", "vegetables", "vegan", "vegetarian",
             "nut roast", "casserole", "slow cooker", "air fryer",
             # roasting a tray of vegetables is the vegetables row's question
             "roast veg", "roast vegetables", "roasted veg", "roasted vegetables"),
      bias=1,
      # a roast the line has just ruled out is not the roast it wants the plate for
      guard=not_ruled_out("sunday-roast")),


# No flour in the house is not a cupboard-cleaning question: `cupboards-clean` in cleaning.py
# keeps "how" in its key and "flour" among its cupboard words, so "how do i make bread without
# flour" was told to empty one cupboard at a time. The flourless recipe below was answered with
# a 500g strong-white-flour loaf, which is the one thing the person said they had none of.
#
# The row asks for the no-flour words, so a plain bread question never reaches it: "bread" is
# one of the commonest words in the kitchen and this answer would be wrong for all of them.
entry("bread-without-flour",
      (("bread", "loaf", "loaves", "flatbread", "flatbreads", "soda bread", "naan", "pitta",
        "pita", "rolls", "buns", "bake", "baking", "make", "recipe", "recipes"),
       ("without flour", "with no flour", "no flour", "flourless", "out of flour",
        "ran out of flour", "run out of flour", "no bread flour",
        # "none left" on its own is any empty shelf: "what can i make for dinner there is none
        # left in the fridge" was reaching the oat loaf from it, and the person said nothing
        # about flour. Only with the flour word beside it.
        "none left of the flour", "no flour none left", "flour none left")),
      "With no flour at all, the quickest loaf is an oat one: blitz 300g porridge oats in a "
      "blender until they look like flour, then mix in 2 teaspoons of baking powder, 1 "
      "teaspoon of salt and 300g of thick yogurt or buttermilk, pour it into a lined loaf tin "
      "and bake at 180C for 40 to 45 minutes. For something in ten minutes, mash cold potato "
      "into a dough with 2 tablespoons of cornflour, salt and a knob of butter, pat it into "
      "flat rounds and fry them dry for three minutes a side. Ground almonds or a gluten-free "
      "bread flour blend also work cup for cup in a soda bread: 400g of either, 1 teaspoon of "
      "bicarbonate of soda, 350ml of buttermilk, 20 minutes at 200C.",
      ask=("without flour", "with no flour", "no flour", "flourless", "out of flour",
           "ran out of flour", "run out of flour", "no bread flour",
           "none left of the flour", "no flour none left", "flour none left"),
      # a crumbly, stale or flat loaf is another row's answer, and so is a cake or a sauce that
      # wants thickening
      avoid=("crumbly", "stale", "mouldy", "mould", "mold", "flat", "yeast", "sourdough",
             "cake", "cakes", "sauce", "gravy", "thicken", "roux", "batter", "pancake",
             "pancakes", "gluten free", "gluten-free", "bread machine",
             # pastry and a pie are the pastry rows' question: "how do i make pastry without
             # flour" wants a substitute, not a loaf
             "pastry", "shortcrust", "short crust", "pie", "pies", "tart", "tarts", "quiche"),
      # "flourless bread recipe" is the flourless question even though the bread recipe row
      # scores on "recipe" too: the one thing the person has said they lack is what this answers.
      # The garden's "baking hot border" row keys "baking" and "what can i", so "i have no flour
      # what can i bake" reached the drought plants; a line that says it has no flour is this row
      # whatever else it asks.
      bias=4),
# "How do I keep chicken juicy" is one of the most common cooking questions there is, and the
# bot had no answer: on main it got the shelf life ("Wrap the leftovers within an hour and they
# keep 3 days in the fridge"), "keep my turkey moist" and "keep the meat moist" got the search
# hedge, "keep roast beef tender" and "keep salmon moist" got the storage card, "tips for juicy
# chicken" got "What's the thing you most want to get right?". The "keep" in those lines is
# about how the meat cooks, not how long it lasts, so this row keys on the quality wanted
# (juicy, moist, tender) with the meat that is being cooked, and stands aside for every keeping,
# freezing, safety and recipe line.
#
# The breast card in cooking.py already answers "how do i keep chicken breast juicy" with the
# flatten-and-roast method, so a named breast or thigh stays with it.
entry("keep-meat-juicy",
      # A cut is named with its animal: "joint", "shoulder", "rib" and "ribs" are body parts
      # as often as they are cuts, and the bare words answered "my knee joint is tender" and
      # "my shoulder is tender" with this card. Every real cut line carries its animal, so the
      # bare words are out and the cut is keyed together with the meat it belongs to.
      (("chicken", "turkey", "beef", "pork", "lamb", "steak", "roast", "brisket", "meat",
        "duck", "gammon", "ham", "chops", "chop", "whole bird", "crown",
        # not "sausages": "how do i keep sausages juicy" wants the roast instructions, and a
        # rest is not what a sausage is for
        "belly pork", "loin",
        "joint of beef", "joint of lamb", "joint of pork", "joint of meat", "roasting joint",
        "beef joint", "lamb joint", "pork joint",
        "shoulder of lamb", "shoulder of pork", "lamb shoulder", "pork shoulder",
        "rib of beef", "beef ribs", "pork ribs", "spare ribs", "rack of ribs", "lamb ribs",
        "chump", "rack of lamb"),
       ("juicy", "juicier", "juiciest", "moist", "moister", "tender", "tenderer", "succulent",
        "moisture", "not dry", "isnt dry", "isn't dry", "not go dry", "not dry out",
        "doesnt dry", "doesn't dry", "wont dry", "won't dry", "drying out", "dry out",
        "dries out", "not dried out", "from drying", "juices in", "stays moist",
        # how the fault is usually written when it happens every time: main answered all of
        # these with the shelf life, because the only word that reached a row was "keeps"
        "comes out dry", "come out dry", "coming out dry", "turns out dry",
        "comes out tough", "comes out rubbery")),
      "Dry meat is overcooked meat, so keep it juicy with a thermometer and a rest rather than "
      "basting: chicken and pork come out of the oven at 74C, beef at 55C for medium rare or 65C "
      "for well done, and then sit on a warm board under foil for 10 to 20 minutes, which lets the "
      "juice settle back in instead of running onto the plate. A 2kg chicken wants 20 minutes per "
      "500g plus 20 at 190C, started breast down so the white meat sits in the fat. Basting mostly "
      "costs oven heat and changes little.",
      # The keeping rows reach these same lines on the same words ("keeps", "roast", "dry") and
      # they are right for their own ask, so the nudge is what settles it for the cooking one.
      # It has to be 3 to beat `cooked-keep-beef` on "how do i keep roast beef tender", and at 3
      # it still leaves "how long does roast beef keep" and "does roast beef keep in the fridge"
      # with the keeping row.
      bias=3,
      # keeping, freezing, safety, nutrition and the cooking method are each another row's line
      avoid=(# a board or a wooden spoon drying out is the kitchen kit's question, not the
             # meat's: "my chopping board is drying out" was told how to rest a roast
             "chopping board", "cutting board", "wooden board", "wooden spoon", "spatula",
             "fridge", "freezer", "freeze", "freezes", "freezing", "frozen", "leftovers",
             "leftover", "how long", "days", "reheat", "reheating", "safe", "safely",
             "bacteria", "poisoning", "left out", "overnight", "thaw", "defrost", "marinade",
             "marinading", "marinating", "brine", "brining", "rub", "calories", "protein",
             "healthy", "healthier", "cheap", "price", "cost", "recipe", "air fryer",
             "slow cooker", "sous vide", "deep fry", "temperature to cook", "how long to cook",
             "what temperature", "breast", "breasts", "thigh", "thighs", "burgers", "mince",
             "meatballs", "stew", "casserole", "curry", "soup", "sandwich", "ribeye",
             # how to cook it, how to rest it and how long for are each an answer already
             "how do i cook", "how to cook", "how do i roast", "how to roast", "rest",
             # a slow cook and a rubbery result are each a row already: "how do i slow cook beef
             # so its tender" had the 150C pot-roast method and "why does my chicken come out
             # rubbery" had the cooked-too-fast card, and both lost it to this one
             "slow cook", "slow cooking", "slow-cooked", "slow roast", "rubbery", "rubber",
             "tough", "tougher", "toughest",
             "resting", "rest it", "how long in the oven", "roasting time", "cooking time",
             # a body is not a cut: "my knee joint is tender" and "tender joint pain" were
             # getting this card off the bare "joint" and "shoulder", and so were "my ribs are
             # tender" and a shoulder ache. None of these words can be in a cooking line, so the
             # card stands down for anything that says where it hurts.
             "knee", "knees", "hip", "hips", "ache", "aches", "aching", "achy", "pain", "pains",
             "painful", "sore", "soreness", "stiff", "stiffness", "injury", "injured", "sprain",
             "sprained", "arthritis", "physio", "physiotherapy", "muscle", "muscles", "sciatica",
             "slipped disc", "trapped nerve", "hamstring", "elbow", "wrist", "ankle", "neck",
             "my back", "bad back", "back pain", "shoulder pain", "neck pain", "joint pain",
             "my knee", "my shoulder", "my ribs", "my hip", "my elbow", "my wrist", "my ankle",
             "my knees", "my joints", "shoulder ache", "sore shoulder",
             # A fish is not a joint of meat: this card gives chicken and pork 74C, and a fish is
             # done at 50 to 55C, so the fish words stay out of this key and the fish's own cards
             # (keep-fish-moist, the keeping card, the pan card) hold those lines.
             "cod", "haddock", "trout", "mackerel", "tuna", "prawns",
             "seafood", "fishcakes", "fish cake", "fish cakes")),
# A fish asked for the same quality is a different card, not a hedge: main answered "how do i
# keep the fish moist" with "I'm not sure about that one, sorry", and the meat card would have
# given it 74C, which is a chicken number. Fish is done at 50 to 55C or the moment it flakes.
# "how long does salmon keep" is the keeping card and "how do i cook salmon" is the pan card, so
# this stands down for both.
entry("keep-fish-moist",
      # tuna and prawns are left out on purpose: "how do i keep tuna moist" is an opened tin and
      # "how do i keep prawns juicy" is the cooked-prawns keeping card, and both are right where
      # they are. The words here are the ones only a fish-quality line uses, so the shared ones
      # ("tender", "succulent") do not change how rare they are for the meat card either.
      (("fish", "salmon", "cod", "haddock", "trout", "mackerel", "seafood", "fishcakes",
        "fish cake", "fish cakes", "sea bass", "bass", "hake", "pollock", "sardines",
        "kippers", "monkfish", "fish fillet", "fish fillets",
        # a tuna steak is a fresh piece of fish, not the opened tin the keeping card answers:
        # "how do i keep tuna steak juicy" was the tin card ("left in the tin it tastes of metal")
        "tuna steak", "tuna steaks"),
       # "drying out" and "dry out" are left to the meat card: a word shared inside a domain is
       # weighed by how rare it is there, and borrowing them lowered the meat card's score
       # enough that "how do i keep my roast chicken from drying out" fell back to the keeping
       # card. A fish that is "always dry" already has its own answer in cooking.py.
       ("juicy", "juicier", "moist", "moister", "flakes", "rubbery", "stays moist",
        "keep it moist")),
      "Fish is done at 50 to 55C, or the moment a fork twists a flake and it just separates, and "
      "it keeps cooking off the heat, so take it out a touch early and rest it two minutes. Cook "
      "it through to 63C for anyone pregnant, elderly or with a weak immune system. A "
      "salmon fillet wants 4 to 6 minutes a side in a hot pan or 8 to 12 minutes at 200C, cod and "
      "haddock a minute or two more, a tuna steak only 1 to 2 minutes a side so the middle stays "
      "pink, and a whole fish 10 minutes per 2.5cm of thickness. Salt it "
      "15 minutes ahead or not at all and keep lemon off it until it is off the heat: both draw "
      "water out. Flakes that stay in soft pieces mean it was in long enough, so lift it then "
      "rather than waiting for it to look white all through.",
      bias=3,
      # the keeping card, the pan card, the shop and the nutrition are each another answer
      avoid=("fridge", "freezer", "freeze", "frozen", "leftovers", "how long", "days", "reheat",
             "safe", "safely", "bacteria", "poisoning", "left out", "overnight", "thaw",
             "defrost", "recipe", "healthy", "healthier", "protein", "calories", "cheap",
             "price", "cost", "buy", "shop", "mercury", "pregnant", "allergy", "allergic",
             "how do i cook", "how to cook", "how do i pan fry", "how to pan fry", "bake",
             "baking", "batter", "fish and chips", "breadcrumbs", "smoked", "smoking",
             "sushi", "raw", "shellfish", "prawn cocktail")),
# "Im bored of the same dinners" was answered by the eat-less-meat row - "make the vegetarian
# dish the main for the whole table" - which is a different question. A rut is not a diet, so this
# row answers the rut with the one thing that breaks it: three dinners straight away, then the
# three things that make the same shopping come out new.
entry("dinner-rut",
      (("bored", "bored of", "bored with", "same dinners", "same meals", "same old dinners",
        "dinner rut", "stuck in a rut", "run out of ideas", "running out of ideas",
        "tired of cooking", "tired of the same", "sick of the same", "sick of cooking",
        "fed up of cooking", "fed up with cooking", "cooking the same"),
       ("dinner", "dinners", "tea", "supper", "meals", "meal", "cooking", "cook", "food",
        "recipes", "ideas", "what can i try", "what can i make", "suggest", "weeknight")),
      # The first sentence has to hand over a dinner: a person out of ideas who is given a
      # principle still has nothing to cook, so the dinners come first and the principle after.
      "Try a traybake, a stir-fry and a pasta this week: change one of three things and the same "
      "dinner comes out new - the shape (traybake, stir-fry, pasta, curry, soup), the carb under "
      "it (rice, potatoes, couscous, bread, noodles) or the sauce that finishes it (tomato, "
      "yoghurt and lemon, a spice paste, gravy, pesto). Mince is a ragu, a chilli with rice, or a "
      "cottage pie. Keep five dinners you can cook without thinking and swap one of those each "
      "week.",
      # a named dish, a diet, a budget and a time limit are four other rows: "what can i cook
      # with mince" wants the mince answer, not a lecture about variety, and "bored of chicken
      # every night" wants five ways with a chicken, which is a food-family row of its own
      avoid=("mince", "chicken", "beef", "pork", "lamb", "fish", "salmon", "pasta", "rice",
             "potato", "potatoes", "eggs", "vegetarian", "vegan", "gluten", "dairy",
             "calorie", "calories", "healthy", "budget", "cheap", "student", "kids",
             "family", "party", "how long", "minutes", "freeze", "leftover", "leftovers",
             "goes with", "meal prep", "batch"),
      bias=2),

# Making yoghurt is one method and two temperatures, and nothing answered it: "how do i make
# yoghurt at home" was a search hedge on main. The keeping question and the diet question have
# their own rows and keep them.
entry("make-yoghurt",
      (("yoghurt", "yogurt", "yoghurt maker", "yogurt maker", "natural yoghurt", "live yoghurt"),
       ("make", "making", "home", "at home", "homemade", "myself", "starter", "culture",
        "ferment", "fermented", "set it", "from milk", "own yoghurt", "machine",
        "without a machine", "no machine")),
      "Warm a litre of milk to just below boiling - 85C, or small bubbles round the edge of the "
      "pan - then let it cool to about 43C, which is a finger in it feeling warm rather than hot. "
      "Stir in 3 tablespoons of live natural yoghurt, keep it at that warmth for 8 to 12 hours in "
      "a flask, a yoghurt maker or an airing cupboard, and chill it once it has set; keep 3 spoons "
      "back as the starter for the next lot. Long or warm and it turns sour and grainy, cool or "
      "short and it stays runny.",
      avoid=("how long", "keep", "keeps", "keeping", "gone off", "off", "bin", "use by",
             "healthy", "good for you", "bad for you", "calories", "sugar", "protein", "calcium",
             "dairy free", "lactose", "freeze", "frozen", "thick", "greek", "skin on")),
# roast a whole chicken" never reaches it however the bird is spelled.
entry("whole-chicken-value",
      (("whole chicken", "whole chickens", "a whole bird", "whole birds", "whole chook",
        "buy a whole chicken", "buying a whole chicken", "chicken whole",
        "whole chicken or breast", "whole chicken or breasts", "whole chicken vs breasts"),
       ("cheaper", "cheapest", "cheap", "cost", "costs", "price", "prices", "worth it",
        "worth buying", "worth the money", "better value", "value", "more expensive",
        "expensive", "save", "saves", "saving", "save money", "money", "vs", "versus",
        "instead of breasts", "instead of fillets", "or breasts", "or fillets")),
      "A whole chicken is nearly always the cheaper way to buy chicken: a 1.5kg bird gives about "
      "700g of meat plus a carcass for stock, which is four portions for £4 to £5, where the same "
      "weight in breast fillets is £7 to £9. The catch is a third of the weight is bone and it "
      "takes 15 minutes to joint. Roast it whole for a Sunday, joint it for a curry or a traybake, "
      "and simmer the carcass for stock; buy fillets only when dinner has to be quick.",
      ask=("cheaper", "cheapest", "cheap", "cost", "costs", "price", "prices", "worth it",
           "worth buying", "worth the money", "better value", "value", "more expensive",
           "expensive", "save", "saves", "saving", "save money", "money", "vs", "versus",
           "instead of breasts", "instead of fillets", "or breasts", "or fillets"),
      # cooking it is not this row's problem: the money words in `ask` already keep the cooking
      # lines out ("how long do i roast a whole chicken" has no money word in it), and an `avoid`
      # list of cooking words took the value lines that name a roast - "is a whole chicken
      # cheaper if i roast it myself" and "is a whole chicken better value for a roast" were
      # both the cook-time card. What stays is another bird, and the freezer.
      avoid=("turkey", "turkeys", "stuffing", "defrost", "freeze", "freezing", "frozen")),

]

# A dish that has gone wrong, with no word for what it did. Every fault the bot knows has a row
# of its own - split, watery, salty, lumpy, mushy, sank, did not rise - and the person who says
# "my curry went wrong" was getting "I'm listening - say more if it helps", while "i ruined the
# curry" got the roast meat answer about resting a joint. But "went wrong" on a dish is only
# ever a short list of things, and the list is the answer: the four faults of a savoury pot and
# the three of a bake. Once somebody says what happened the specific row takes over, so this one
# holds only the lines that name no fault at all.
_FAULT = ("went wrong", "gone wrong", "went out wrong", "went badly", "gone badly",
          "turned out wrong", "messed up", "screwed up", "ruined", "is a disaster",
          "was a disaster", "didnt work out", "didn't work out", "not gone right",
          # "it did not turn out" is the same sentence as "it turned out wrong", and it was
          # the half of the pair that was still reaching "I'm listening - say more if it helps".
          # "didnt turn out" on its own, not "turn out", because "how do i turn out a cake"
          # and "when do i turn out the pie" are method questions.
          "didnt turn out", "didn't turn out", "did not turn out", "doesnt turn out",
          "turned out badly", "turned out wrong", "was a flop", "flopped", "failed")

# A fault already happened; "does that ruin it" is a plan being weighed. These two rows are keyed
# on the words a dish goes wrong with and on the dish, and the dish can come from the line before
# ("is the food expensive" / "does that ruin it"), so a question asked in the present about what a
# choice would do to a dish got the list of ways a pot fails. A dish fault is only ever said about
# something already cooked, so a ruin-or-spoil verb standing as the subject's own verb after
# does/will/would is another question, and both rows stand down for it. This is a guard and not an
# avoid word because an avoid phrase is read loosely, in any order: "does the lemon ruin it" and
# "will that spoil the sauce" would still be answered, and "i ruined the curry" would not.
entry_dish_went_wrong = entry(
    "dish-went-wrong",
    # the fault phrase first, because it is what has to be said; the dish second, because a
    # pot and a bake fail differently and the dish is what tells them apart
    (_FAULT,
     # The dishes people cook on a weeknight, not just the ones with a recipe behind them. A
     # chicken, a rice, a tray of meatballs, a pizza or a takeaway went wrong in one of the same
     # four ways, and until it was here "my chicken went out wrong" got "Got it. Is there
     # anything you'd like a hand with?" and "my fish went out wrong" got "Noted: your fish went
     # out wrong." - a fault said back instead of a fault answered.
     ("curry", "stew", "casserole", "gravy", "soup", "broth", "sauce", "chilli", "chili",
      "risotto", "pasta", "lasagne", "lasagna", "bolognese", "ragu", "tagine", "dal", "daal",
      "stir fry", "stir-fry", "roast", "pie", "pudding", "porridge", "rice dish",
      "chicken", "rice", "fish", "salmon", "potatoes", "mash", "pizza", "noodles",
      "meatballs", "meatloaf", "takeaway", "food", "dinner", "dish", "meal",
      # main grew most of the whole-meal nouns while this branch waited; "supper" is the one
      # still missing, and the fault phrase is still needed, so "what should i have for
      # dinner" is untouched
      "supper")),
    "Nearly always one of four things: too thin (simmer it uncovered for ten minutes), too salty "
    "(bulk it out with more of what is already in it, not water), caught on the bottom (into a "
    "clean pan, without scraping the base), or bland (salt a little, then a squeeze of lemon or a "
    "splash of vinegar). Tell me which it is and I will give you the fix for that dish.",
    # a bake is the other row's list, and a broken appliance is nobody's cooking fault
    avoid=("cake", "cakes", "sponge", "bread", "loaf", "scone", "scones", "pastry", "biscuit",
           "biscuits", "cookie", "cookies", "brownie", "brownies", "muffin", "muffins",
           "oven", "fridge", "freezer", "dishwasher", "washing machine", "washer", "boiler",
           "microwave", "kettle", "blender", "toaster", "hob", "cooker",
           # "ruined" is also said of a pan's coating and of a whole evening
           "pan", "evening", "date", "day", "weekend", "holiday", "meal out", "dinner out",
           # and a dinner party that went wrong is a night to plan, not a dish: it has a row
           # of its own about one oven dish instead of several pans
           "party", "parties", "guests", "hosting",
           # scrambled eggs have their own row about too much heat, which is the real fault
           "eggs", "egg", "scrambled", "poached", "boiled",
           # and a pizza is baked, so it is the bake row's to answer
           "pizza", "pizzas"),
    guard=a_plan_that_might_be_ruined)

entry_bake_went_wrong = entry(
    "bake-went-wrong",
    (_FAULT,
     ("cake", "cakes", "sponge", "bread", "loaf", "loaves", "scone", "scones", "pastry",
      "biscuit", "biscuits", "cookie", "cookies", "brownie", "brownies", "muffin", "muffins",
      "bun", "buns", "yorkshire", "bake", "bakes", "baking", "sourdough", "dough",
      # a pizza is a dough that goes in an oven, so its faults are the bake's three: a pale,
      # floppy base under a cold oven, a tough one from too much mixing, no rise from old yeast.
      # The pot list (too thin, too salty, caught, bland) is a sauce list and fits it badly.
      "pizza", "pizzas",
      "starter")),
    "Nearly always one of three: an oven running 20C cooler than it says (an oven thermometer "
    "pays for itself), too much mixing once the flour went in (stop as soon as no dry flour "
    "shows), or old raising agent - bicarbonate and baking powder lose their fizz about six "
    "months after opening. Tell me what it did - sank, dry, heavy, burnt - and I will give you "
    "the fix for it.",
    avoid=("oven", "fridge", "freezer", "dishwasher", "washing machine", "washer", "boiler",
           "microwave", "kettle", "blender", "toaster", "hob", "cooker", "pan", "pans",
           "evening", "date", "day", "weekend", "holiday", "recipe", "how do i make",
           "make a cake", "bake a cake", "without flour", "no flour", "freeze", "frozen",
           "keep", "keeping", "stale", "mouldy", "mould", "mold"),
    guard=a_plan_that_might_be_ruined)

# A pancake, a waffle or a crepe fails in a pan rather than in the oven, so neither list above
# answers it: "my pancakes went wrong" was an echo while "my pancakes are flat" already had its
# own row. The three faults of a batter are the answer, and the flat one still wins the line when
# the person says which fault it is.
entry_batter_went_wrong = entry(
    "batter-went-wrong",
    (_FAULT,
     ("pancake", "pancakes", "crepe", "crepes", "waffle", "waffles", "batter",
      "drop scones", "blini", "blinis", "yorkshire pudding batter")),
    "A batter that goes wrong is nearly always one of three: too thick (a splash more milk, until "
    "it runs off the whisk in a ribbon), the pan not hot enough (a drop should sizzle the moment "
    "it lands, so heat it a minute longer than feels right), or turned too early (wait for bubbles "
    "across the top and a dry-looking edge). Resting the batter fifteen minutes fixes half of "
    "them, and a pinch of baking powder lifts the thick American ones.",
    # a recipe, a bought one and a pancake day are other lines, and "batter" is also a fish
    avoid=("recipe", "how do i make", "how to make", "how do you make", "shrove", "day",
           "fish", "chicken", "shop", "supermarket", "freeze", "frozen", "bought",
           "oven", "fridge", "freezer", "dishwasher", "washing machine", "microwave"))

ENTRIES.append(entry_dish_went_wrong)
ENTRIES.append(entry_bake_went_wrong)
# Cold sauces that are one technique: an egg yolk that takes the oil slowly. "how do i make
# mayonnaise", "how do i make tartare sauce", "how do i make aioli" and "how do i make croutons"
# were all "I'm not sure about that one, sorry", and "what goes in mayonnaise" reached the
# recycling card, which is a list of what goes in a bin.
entry_make_mayonnaise = entry(
      "make-mayonnaise",
      # the sauce first, because it is what has to be named; the ask words second, including
      # "what goes in", which is the same question as "how do i make" about a sauce
      (("mayonnaise", "mayo", "aioli", "tartare sauce", "tartar sauce", "salad cream",
        "garlic mayo", "remoulade", "garlic aioli"),
       ("make", "making", "made", "own", "homemade", "recipe", "how do i", "how to",
        "what goes in", "from scratch", "without egg", "no egg", "egg free", "vegan")),
      "Whisk an egg yolk with a teaspoon of mustard and a pinch of salt, then add 250ml of oil in a "
      "thin thread to start with - drop by drop - and only pour faster once it has thickened; "
      "finish with a squeeze of lemon. If it splits, put a fresh yolk in a clean bowl and whisk the "
      "split batch in a spoonful at a time. Tartare sauce is mayonnaise with chopped capers, "
      "gherkins and parsley, aioli is the same with crushed garlic, and salad cream is mayonnaise "
      "loosened with vinegar and a pinch of sugar.",
      # the jar to buy, the keeping and the calories are three other answers, and a sauce that
      # has split has its own row, which knows more about a split than this one does
      avoid=("buy", "brand", "shop", "price", "cost", "gift", "healthy", "calories", "calorie",
             "diet", "jar", "jars", "bottle", "bottles", "recycling", "bin", "keep", "keeping",
             "store", "fridge", "freeze", "gone off", "off", "split", "splits", "split sauce",
             "curdled", "sandwich", "burger", "chips"),
      bias=2)

# Croutons and breadcrumbs are what stale bread is for, and the revive answer ("sprinkle it with
# water and warm it") is the right answer to a different question: a loaf that is dry, not a
# handful of cubes to go in a soup.
entry_croutons = entry(
      "croutons-and-breadcrumbs",
      (("croutons", "crouton", "breadcrumbs", "bread crumbs", "panko", "toasted bread cubes"),
       ("make", "making", "own", "homemade", "from", "stale", "leftover", "left over",
        "how do i", "how to", "what can i do", "use up")),
      "Cut stale bread into cubes, toss them in olive oil with a little salt, and bake at 180C for "
      "8 to 10 minutes until they rattle in the tin - a halved garlic clove in the oil is the whole "
      "trick. For breadcrumbs, tear the bread up, blitz it or grate it on the coarse side, dry them "
      "in the same oven for 5 minutes, and they keep a month in a jar.",
      # reviving a dry loaf, a stuffing, a bread sauce and a pudding are three other answers
      avoid=("revive", "soft again", "fresh again", "gone hard", "stuffing", "bread sauce",
             "pudding", "mouldy", "mould", "mold", "keep", "keeping", "freeze", "frozen",
             "toast", "toasted cheese"),
      bias=2)

# "sunday roast timings for six people" and "what time should i put the roast in" were punts, and
# "roast timings" with them: the roast rows key on a named joint (roast-chicken, roast-joint) or
# on the menu ("what goes with a roast"), and the timetable answer keys on "make"/"cook"/"how
# long" through the shared recipe verbs, so a line that asks when to start and for how many
# people reached none of them. This row is the whole oven worked backwards from the time you eat,
# and it holds the named joints out so each one keeps the minutes-per-500g answer it already has.
# The row keys the for-N phrases, so it has to say the number back: quiet-kangaroo measured
# "sunday lunch for eight people what time do i start" and "sunday roast for twelve" both being
# told about six people, which is an answer to a question nobody asked. The count is read off the
# line and the weight and the oven time follow from it; with no number in the line the reply
# keeps the six-person example.
_COUNT_WORDS = (("a dozen", 12), ("four", 4), ("five", 5), ("six", 6), ("seven", 7), ("eight", 8),
                ("nine", 9), ("ten", 10), ("eleven", 11), ("twelve", 12), ("sixteen", 16),
                ("twenty", 20))


def _spoken(line, word):
    return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", line) is not None


# A follow-up that asks how many the meal was for ("how many people is it for") has no figure
# of its own, and the six-person example is an answer about somebody else's dinner. The table is
# the one an earlier line set, read only from a line that names the meal and a count of people,
# so a time ("10 more minutes") or an age is never taken as the number at the table.
_THE_MEAL_NAMED = re.compile(
    r"\b(?:roast|sunday (?:lunch|dinner)|christmas dinner|xmas dinner|turkey dinner|"
    r"cooking (?:for|a meal)|doing the dinner)\b", re.I)
_THE_TABLE_NAMED = re.compile(
    r"\b(?:for\s+)?(?P<n>\d{1,2}|a dozen|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|sixteen|twenty)\s*"
    r"(?:people|persons?|adults?|kids|children|guests?|of us|coming|eating)\b"
    r"|\broast(?:\s+is)?\s+for\s+(?P<only>\d{1,2}|a dozen|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|sixteen|twenty)\b", re.I)
_TABLE_WORDS = {"a dozen": 12, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
                "sixteen": 16, "twenty": 20}
# The table put right on its own: "actually its 10 people" after "a roast for 8" is the new
# number for the same meal, and the line that set the eight does not have to be named again.
_A_TABLE_PUT_RIGHT = re.compile(r"\b(?:actually|no|nope|sorry|make it|change it|instead)\b", re.I)


def _the_table_the_chat_set(memory):
    """The number the chat said this meal is for, or 0 when no earlier line set one.

    "im doing a roast on sunday for 8 people" then "how many people is it for" is the same
    question about the same table: the first line set it, and answering the second with the
    six-person example contradicts what the person said a turn earlier. Only the last few of
    their own lines are read, and only one that names the meal and a count of people, so an
    age, a weight or a cooking time is never taken as the number at the table.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return 0
    for turn in reversed(turns[-8:]):
        said = " ".join(str((turn or {}).get("user") or "").lower().split())
        if not said:
            continue
        found = _THE_TABLE_NAMED.search(said)
        if not found or not (_THE_MEAL_NAMED.search(said) or _A_TABLE_PUT_RIGHT.search(said)):
            continue
        raw = (found.group("n") or found.group("only") or "").lower()
        count = int(raw) if raw.isdigit() else _TABLE_WORDS.get(raw, 0)
        if 2 <= count <= 30:
            return count
    return 0


def _roast_head_count(line):
    """The number of people the line is cooking for, or 0 when it names none."""
    for found in re.findall(r"(?<![a-z0-9])(\d{1,2})(?![a-z0-9])", line):
        count = int(found)
        if 4 <= count <= 30:
            return count
    for word, count in _COUNT_WORDS:
        if _spoken(line, word):
            return count
    return 0


def _kilos(count):
    """The raw weight to buy, said the way a butcher would say it."""
    grams = count * 250
    if grams % 1000 == 0:
        return "%dkg" % (grams // 1000)
    if grams % 500 == 0:
        return "%d.5kg" % (grams // 1000)
    return "%.2fkg" % (grams / 1000.0)


def _the_time_a_joint_needs(grams):
    """The time this card's own rule gives a joint of this weight: 20 minutes per 500g plus 20.

    Worked out from the grams rather than from the whole kilos in the buy weight. A weight that
    is not a whole number of kilos was read as the kilos below it, so six people - who want
    1.5kg, three lots of 500g - were told "an hour and 0 minutes" by the same card that says 20
    minutes per 500g plus 20, and five, seven, nine and eleven were as short.
    """
    minutes = int(grams / 25) + 20
    hours, minutes = divmod(minutes, 60)
    if hours > 1:
        return "%d hours %d minutes" % (hours, minutes) if minutes else "%d hours" % hours
    if hours == 1:
        return "an hour and %d minutes" % minutes if minutes else "an hour"
    return "%d minutes" % minutes


# The dishes, joints and diets a roast question is really about, and the ways a roast goes
# wrong. They are kept out of the crowd card by the words of the line that asks, not by the topic
# carried over from the turn before: after "how long do i cook the chicken" the topic still says
# "chicken", so the old avoid list refused the crowd card for "and how many people" - the ask had
# no meal word of its own, the meal was the plan on the table, and the person got no answer at
# all. A line that says one of these is a question about that dish, and the crowd card is not the
# answer to it, so the check moved into the row's own function: the arbiter tests an avoid list
# against the topic, and the topic is the turn before as often as it is this line.
_NOT_THE_CROWD_CARD = (
    "chicken", "beef", "lamb", "pork", "turkey", "duck", "goose", "gammon", "ham",
    "joint", "potato", "potatoes", "carrot", "carrots", "parsnip", "parsnips",
    "yorkshire", "stuffing", "gravy", "temperature", "temp", "gas mark", "defrost",
    "frozen", "freeze", "leftover", "leftovers", "vegan", "vegetarian", "veggie",
    "plant based", "nut roast", "slow cooker", "air fryer", "roast veg", "roast vegetables",
    "roasted veg", "roasted vegetables", "soggy", "dry", "burnt", "bland", "recipe", "ideas",
    "what goes with", "menu", "sides")


def _the_dish_the_line_names(line):
    """True when the line itself names a dish, a joint or a diet the crowd card is not for."""
    for word in _NOT_THE_CROWD_CARD:
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", line):
            return True
    # A roast the line rules out is not a roast the person is asking the count for: "i dont want
    # to do a roast what else could i do for 4" was answered with the joint for four.
    from .dishes import dishes_ruled_out
    return "sunday-roast" in dishes_ruled_out(line)


def _roast_for_a_crowd(memory, understood):
    line = " " + re.sub(r"[^a-z0-9' ]+", " ", str((understood or {}).get("clean")
                                                 or (understood or {}).get("text")
                                                 or "").lower()) + " "
    if _the_dish_the_line_names(line):
        return None
    count = _roast_head_count(line) or _the_table_the_chat_set(memory)
    if not count:
        return (
            "Allow about 250g of raw meat each with the bone in, or 150g boneless: six people "
            "want a 2kg chicken or a 1.5kg joint. Work backwards from the time you want to eat: "
            "meat in at 190C (170C fan) " + _the_time_a_joint_needs(2000) + " before, because a 2kg bird "
            "is 20 minutes per 500g plus 20. Potatoes in an hour before, parboiled and "
            "rough in hot fat at 200C for 45 minutes. Stuffing and pigs in blankets 25 minutes "
            "before the end, greens 10. The meat comes out to rest 15 minutes under foil, and "
            "the gravy is made in the tin while it does.")
    kilos = _kilos(count)
    length = _the_time_a_joint_needs(count * 250)
    return (
        "For %d people allow about 250g of raw meat each with the bone in, or 150g boneless, so "
        "buy about %s in total: one joint that size, or two good-sized chickens. "
        "Work backwards from the time you want to eat: meat in at 190C (170C fan) %s "
        "before, because a joint is 20 minutes per 500g plus 20. Potatoes in an hour "
        "before, parboiled and rough in hot fat at 200C "
        "for 45 minutes. Stuffing and pigs in blankets 25 minutes before the end, greens 10. "
        "The meat comes out to rest 15 minutes under foil, and the gravy is made in the tin "
        "while it does." % (count, kilos, length))


entry_roast_for_a_crowd = entry(
      "roast-for-a-crowd",
      # the multi-word "for" phrases are deliberately not in this part: a phrase eats the words
      # it matches, so "roast for four" matched "roast for" here and then had no "for" left for
      # the "for four" in the number list, and the row scored nothing. The bare "roast" is
      # enough for the meal, and every for-N phrase then matches on its own words.
      (("sunday roast", "roast dinner", "roast lunch",
        "sunday lunch", "sunday dinner", "roast", "roasting"),
       ("timings", "timing", "timetable", "what time", "when do i start", "when should i start",
        "work back", "work backwards", "for four", "for 4", "for five", "for 5", "for six", "for 6",
        "for seven", "for 7", "for eight", "for 8", "for nine", "for 9", "for ten",
        "for 10", "for eleven", "for 11", "for twelve", "for 12",
        "for six people", "for eight people", "for ten people",
        "how much meat", "how much should i buy", "quantity", "per head", "per person",
        "how many", "plan", "schedule", "order of things")),
      _roast_for_a_crowd,
      # a named joint or bird is its own minutes-per-500g answer, and the potatoes, the veg and
      # the menu are three other rows: this one only answers the line that names the meal and
      # asks when to start
      # no avoid list: it is tested against the topic as well as the line, and the topic is the
      # turn before, so "how long do i cook the chicken" then "and how many people" lost the
      # card to a word from the turn before. `_the_dish_the_line_names` keeps the same dishes
      # out of the card using the words of this line only.
      # "roast dinner for 8 people" is the crowd-cooking answer's question, not a timetable:
      # the ask words make this row only answer a line that says when or how much
      # "sunday roast for six" and "roast for eight" say the number and nothing else, and with
      # no time word in the gate they fell through to the plan-the-week cards: the number is the
      # whole of the timetable question when the meal is named, so the for-N phrases are ask words
      # too. "roast dinner for 8 people" is still the crowd-cooking answer's line, because that
      # row keys the number as well and its card is the one that adds up the shopping.
      ask=("timing", "timings", "time", "timetable", "plan", "schedule", "when", "start",
           "how long", "much", "many", "order", "quantity", "per head", "per person",
           "for four", "for 4", "for five", "for 5", "for six", "for 6", "for seven", "for 7",
           "for eight", "for 8", "for nine", "for 9", "for ten", "for 10", "for eleven", "for 11",
           "for twelve", "for 12"),
      bias=1)


ENTRIES.append(entry_make_mayonnaise)
# How far a bird goes is the question next to its value: "how many meals can i get from a
# whole chicken" and "how many people does a whole chicken feed" were a search hedge and a
# shrug, while the table knew the per-person weight ("about 200 g each") and nothing about
# what a whole bird actually yields. The answer is the count first, then the meat weight it
# rests on, then the stock that comes out of the frame.
ENTRIES.append(entry(
    "whole-chicken-meals",
    (("whole chicken", "whole bird", "whole roast chicken", "a chicken"),
     ("how many meals", "how many people", "how many portions", "feed", "feeds", "serves",
      "go round", "goes round", "go far", "goes far", "how far", "far", "enough for", "last",
      "stretch")),
    "Two meals from a 1.5kg bird, three from a 2kg one: four roast portions, then enough "
    "stripped off the frame for two more in a curry, a stir-fry or sandwiches - about 600g of "
    "cooked meat from 1.5kg, because a third of the raw weight is bone, skin and water. The "
    "frame then gives roughly 2 litres of stock, which is a soup or a risotto, and the fat "
    "roasts the potatoes.",
    # buying one, cooking one and the price of one are the three rows next to this: the
    # count words in the second group keep a value line and a cook-time line out
    ask=("chicken", "bird"),
    avoid=("how long", "oven", "roast it", "temperature", "defrost", "frozen", "freeze",
           "cheaper", "cost", "price", "value", "worth", "per person", "grams", "kg",
           "how much chicken", "stock cube", "curry recipe", "leftover chicken",
           # a breast or a fillet is one portion, not a bird: "how many meals from a chicken
           # breast" was answered with the whole-bird count, which is four times the truth
           "breast", "breasts", "fillet", "fillets", "thigh", "thighs", "wing", "wings",
           "leg", "legs", "drumstick", "drumsticks", "mince", "diced", "strips",
           # "how far in advance can i prepare chicken" and "how far can i keep it" carry the
           # same "far" and must stay with the keeping and preparing rows
           "in advance", "prepare", "prep", "keep", "fridge", "freezer", "cold", "raw",
           "how long", "safe", "reheat", "defrost")))

ENTRIES.append(entry_croutons)
ENTRIES.append(entry_batter_went_wrong)
ENTRIES.append(entry_roast_for_a_crowd)


# The collapse said once: the loaf row and the "it rises then it drops" row are the same fault.
_loaf_collapse_text = (
    "A loaf that collapses rose and then fell back, which is a prove that ran too long: the yeast "
    "has eaten its sugar and the gluten that held the bubbles gives way when the heat hits it. "
    "Shape it and prove it only until a floured finger pressed in leaves a dent that springs back "
    "slowly - if the dent stays, it is ready, and if it fills at once it is not. Bake it at 220C "
    "(200C fan) and leave the door shut for the first 20 minutes, and cut the water and yeast "
    "slightly next time; a loaf that also smells of alcohol went well past ready.")

# A loaf that collapses is not a dense one and not a flat one: the dense-bread row answers "my
# bread sank in the middle" and "why is my bread dense", and a collapse is the loaf that rose and
# then fell back, which is a prove that ran too long. Nothing answered it: "why does my bread
# collapse" was "That's beyond what I know well", "my loaf collapses" was "Right. What have you
# tried so far?" and "my bread collapsed in the oven" was "Got it."
entry_loaf_collapse = entry(
    "loaf-collapse",
    (("bread", "loaf", "loaves", "sourdough", "sourdough loaf", "buns", "roll", "rolls",
      "focaccia", "tin loaf", "white loaf", "wholemeal loaf"),
     ("collapse", "collapses", "collapsed", "collapsing", "caved in", "caves in",
      "fell in", "falls in", "fell", "deflated", "deflates", "shrunk", "shrinks")),
    _loaf_collapse_text,
    # the dense, flat and crumbly loaves are three other rows, and a keeping or a recipe line is
    # not a fault at all
    avoid=("dense", "sank", "sunken", "sinking", "flat", "didnt rise", "did not rise",
           "not rising", "wont rise", "won't rise", "crumbly", "stale", "mouldy", "mould",
           # not a bare "keep": `avoid` is matched word by word, and the forms of "keeps" are
           # "keeps" and "keep", so "keep" in this list stood the row down for every "my bread
           # keeps collapsing" - the fault lines were the ones it was written for. The keeping
           # question is fenced by "how long" and "shelf life" instead.
           "mold", "freeze", "frozen", "recipe", "how do i make", "how long", "shelf life",
           "how to make", "oven temperature", "starter", "cake", "cakes",
           "banana", "malt", "soda"))
ENTRIES.append(entry_loaf_collapse)

# "it rises then it drops in the oven" is the same collapse said without the word loaf, and the
# whole of it is in the line: no bread word is needed to know what went up and came down. It was
# answered with "Got it. Is there anything you'd like a hand with?" and, before that, with the
# oven door's hinge, because "drops" and "oven" are a door's words too. Two halves are enough: a
# thing going up, and the same thing coming back down.
entry_rises_then_drops = entry(
    "rises-then-drops",
    (("rise", "rises", "risen", "rising", "goes up", "went up", "puffs up", "puffed up",
      "comes up", "came up", "springs up", "sprung up", "proves up", "proved up"),
     # the fall half has to carry every verb people use for a loaf going down, not just the two
     # the first cut had: "my bread rises then sinks", "my bread has risen and fallen" and "my
     # dough rose then sank" are the same fault said with a different word, and none of them
     # reached this row while the word was missing.
     ("drops", "dropped", "drops back", "dropped back", "falls", "fall", "fell", "fallen",
      "falls back", "fell back", "sinks", "sink", "sinking", "sank", "sunk", "collapses",
      "collapse", "collapsed", "collapsing", "deflates", "deflate", "deflated", "caves in",
      "cave in", "caved in", "flops", "flop", "flopped", "deflated")),
    _loaf_collapse_text,
    # a cake, a souffle and a Yorkshire pudding have their own sinking answers, and a keeping or
    # a recipe line is not a fault at all
    avoid=("cake", "cakes", "sponge", "souffle", "soufflé", "yorkshire", "pudding", "muffin",
           "muffins", "scone", "scones", "meringue", "how long", "keep", "keeps", "shelf life",
           "recipe", "freeze", "frozen", "starter", "flat"),
)
ENTRIES.append(entry_rises_then_drops)

# A starter that stops working is the third sourdough question, and the feeding row answers "how
# do i feed my sourdough starter", "my starter stopped bubbling" and "my starter has hooch" with
# the ratios, which is right for a feed and no answer for a person whose starter is dying. The
# fault words are what tells them apart.
entry_starter_dying = entry(
    "starter-dying",
    (("sourdough starter", "sour dough starter", "starter", "starters", "levain", "sourdough"),
     ("dying", "died", "dies", "dead", "killed", "killing", "not rising", "isnt rising",
      "isn't rising", "stopped rising", "stopped growing", "wont rise", "won't rise",
      "not bubbling", "stopped bubbling", "no bubbles", "flat and lifeless")),
    "A starter that has stopped rising is usually hungry, cold or both: give it equal weights of "
    "flour and water, about its own weight, at room temperature (20 to 25C) and it should double "
    "in four to eight hours. If it has gone quiet, feed it twice a day for three or four days "
    "without putting it back in the fridge, and use wholemeal or rye flour for one of those feeds, "
    "which wakes it faster than white. A dark liquid on top is alcohol, not death: pour it off and "
    "feed. Mould - pink, black or furry - is the only one to throw away.",
    # how to make one, how to feed one and what to call it are three other rows, and a bought
    # loaf or a keeping question is not this question
    avoid=("how do i make", "how to make", "start from scratch", "from scratch", "name",
           # "keep" is out for the reason the loaf row gives: "my starter keeps dying" is this
           # row's own line and a bare "keep" in `avoid` takes it away.
           "call it", "recipe", "buy", "shop", "freeze", "frozen", "fridge",
           "mould", "mold", "pink", "black",
           # A loaf that did not rise is the bread's question, not the jar's: "my sourdough
           # bread wont rise" was the prove-it-longer card on main ("give it another hour until
           # it has doubled") and this row took it, feeding a starter the person never mentioned
           # as the problem. Naming the bread, the loaf or the dough is naming the loaf.
           "bread", "breads", "loaf", "loaves", "dough", "roll", "rolls", "boule", "batard"))
ENTRIES.append(entry_starter_dying)

# --- a starter with mould on it, and a starter put away in the fridge ---------------------------
# `starter-dying` answers a starter that has gone quiet, and its `avoid` already sends "mould",
# "mold", "pink" and "black" away on purpose. Nothing picked them up: "my starter has gone
# mouldy" was "I'm listening - say more if it helps", "can i save a sourdough starter with mould
# on it" was a search hedge and "should i throw away a starter with mould" was "That's your call,
# not mine". The keep-it-in-the-fridge question went the other way - "how long can i keep a
# starter in the fridge" was answered by the fridge shelf-life card ("cooked food keeps 3 to 4
# days"), which is wrong for the one food in the kitchen that is kept alive on purpose.
_STARTER_NAMES = ("sourdough starter", "sour dough starter", "starter", "starters", "levain",
                  "sourdough", "sour dough")

entry_starter_mould = entry(
    "starter-mould",
    (_STARTER_NAMES,
     ("mould", "mold", "mouldy", "moldy", "fur", "furry", "fuzz", "fuzzy", "green", "black",
      "pink", "orange", "white film", "white layer", "skin on top", "gone off", "ruined")),
    "Look at the colour before you do anything. A white or creamy film on top, with no fur on it, "
    "is kahm yeast and the starter is fine: skim it off, move the jar to a clean one and feed it. "
    "Anything furry, or pink, orange, green or black, means mould has gone through the jar - "
    "throw it out and start again, because the spores are in the flour and not just on the "
    "surface. Wash the jar with hot soapy water before the next one, and keep the sides scraped "
    "down so nothing grows on the rim.",
    # how to make one, how to feed it and what to call it are three other rows, and a loaf or a
    # cake that went mouldy is the food's question, not the jar's
    avoid=("bread", "breads", "loaf", "loaves", "cake", "cakes", "muffin", "muffins", "bun",
           "buns", "jam", "cheese", "yoghurt", "yogurt", "fruit", "freeze", "frozen", "name",
           "call it", "recipe", "how do i make", "how to make", "ratio"))

entry_starter_keeping = entry(
    "starter-keeping",
    (_STARTER_NAMES,
     ("keep", "keeping", "store", "storing", "fridge", "refrigerator", "how long", "last",
      "leave it", "leave my", "holiday", "holidays", "away", "two weeks", "a week", "month",
      "months", "travel", "forget", "forgot", "neglect")),
    "A starter in the fridge will sit for weeks without much harm and months if you feed it now "
    "and then: once a week is plenty in the cold, and a grey liquid on top is alcohol, which you "
    "pour off. Before you bake, take it out, feed it and let it double at room temperature, and "
    "feed it twice a day for two days if it has been in there a while. Going away for a month is "
    "fine - feed it thick, spread a spoonful on baking parchment, dry it and it can be woken up "
    "afterwards.",
    # how to feed it, how to make one, what to call it and one that has stopped working are four
    # other rows; a food that went mouldy in the fridge is the food's question
    avoid=("how do i feed", "how to feed", "feed it", "feeding", "ratio", "flour and water",
           "mould", "mold", "mouldy", "moldy", "name", "call it", "recipe", "how do i make",
           "how to make", "not rising", "wont rise", "died", "dead", "milk", "cheese", "meat"))

# A starter's smell was the third of the jar questions with no row of its own: "my starter smells
# like nail polish" and "my sourdough starter smells of acetone" got the feeding ratios, which
# tells a worried person how to feed the thing they think has spoiled. `starter-dying` puts
# "smell" in its `avoid` on purpose, so nothing owned it.
entry_starter_smell = entry(
    "starter-smell",
    (_STARTER_NAMES,
     # "sour" and "off" are out of this list: they are inside "sourdough" and "off"
     # matches inside other words, so "can i use sourdough starter for yoghurt" was
     # read as a smell question. A smell is named by a smell word here.
     ("smell", "smells", "smelling", "smelly", "stinks", "stink", "whiff",
      "acetone", "nail polish", "nail varnish", "vinegar", "vinegary", "sharp",
      # "yoghurt" is out too: the smell is what makes this the smell question, and a
      # yoghurt-and-starter line is the yoghurt rows' business.
      "sickly", "alcohol", "beery")),
    "Sniff it and match the smell: yoghurt or beer is a healthy starter at work and nothing needs "
    "doing; acetone or nail polish means it has run out of food and is making alcohol, so pour "
    "off any liquid on top and feed it twice a day until it smells of yoghurt again; vinegar or "
    "a sharp sourness is the same thing further along, so feed it more often than once a day "
    "and use a splash of it in a bake rather than a whole loaf.",
    # a jar that has grown something on it, one that has stopped working, and how to feed or make
    # one are four other rows
    avoid=("mould", "mold", "mouldy", "moldy", "fur", "fuzzy", "pink", "orange", "green film",
           "not rising", "wont rise", "stopped rising", "died", "dead", "how do i feed",
           "how to feed", "feeding ratio", "how do i make", "how to make", "name", "call it",
           "recipe", "milk", "cheese", "yoghurt pot", "yogurt pot", "bread", "loaf",
           "loaves"),
    # "my starter smells like yoghurt" reached the yoghurt-tub card ("a little watery
    # separation on yogurt is fine"), so naming the jar and the smell beats a tub.
    bias=2)

ENTRIES.append(entry_starter_mould)
ENTRIES.append(entry_starter_keeping)
ENTRIES.append(entry_starter_smell)

# A soup curdles for the same reason a sauce splits, but the split-sauce row answers "how do i
# stop it": its reply is the rescue (cold cream, a whisk, a sieve), and a pot of soup wants the
# heat kept under a simmer and the cream added at the end. "my soup curdled", "my soup keeps
# curdling", "how do i stop my soup curdling" and "why does my soup curdle" were all a shrug.
entry_soup_curdle = entry(
    "soup-curdle",
    (("soup", "soups", "broth", "bisque", "chowder", "minestrone", "soup pot", "pot of soup"),
     ("curdle", "curdles", "curdled", "curdling", "split", "splits", "splitting",
      "separated", "separates", "separating", "grainy", "grainy bits")),
    "A creamy or egg-thickened soup curdles when it gets too hot or too sharp: keep it under a "
    "simmer - small bubbles at the edge, never a rolling boil - and stir the cream, yogurt or egg "
    "in off the heat at the very end. Acid does the same, so add wine, lemon or tomatoes early and "
    "let them cook down before the dairy goes in, and a pinch of bicarbonate of soda in a "
    "tomato soup stops the split. If it has already gone, take it off the heat and blend it smooth "
    "with a little cold cream, or whisk in a cornflour slurry and warm it gently.",
    # the split sauce, the curdled custard, the hollandaise and the cheese sauce are four other
    # rows, and a recipe or a keeping question is not a fault
    avoid=("sauce", "sauces", "custard", "hollandaise", "mayonnaise", "cheesecake", "cake",
           "cream sauce", "gravy", "curry", "recipe", "how do i make", "how to make",
           "freeze", "frozen", "fridge", "how long", "shelf life"))
ENTRIES.append(entry_soup_curdle)

# --- baking with no eggs, a bird that is boring, and bread that did not rise -------------------
# Three faults people report in their own words, each of which was reaching an answer for a
# different question: "i have no eggs what can i bake" was the *sunny-border* answer (the garden's
# `plants-for-sun` keys "what can i" and "baking", as in a baking hot border), "im bored of
# chicken every night" was the what-can-i-do activity card ("try something with your hands: a new
# recipe, a jigsaw"), and "why did my bread not rise" was the how-to-prove instructions, which is
# the answer to "how do i make bread rise" and no help at all to somebody holding a flat loaf.
entry_no_eggs = entry(
      "baking-without-eggs",
      (("no eggs", "without eggs", "out of eggs", "no egg", "egg free", "eggless",
        "eggless"),
       # only baking words ask this: "what can i cook with no eggs" and "what can i make with no
       # eggs" already get the egg-swap answer with the weights in it, which is the better answer
       ("bake", "baking", "cake", "cakes", "biscuits", "cookies", "muffins", "scones", "sweet",
        "dessert", "pudding", "traybake", "recipe", "what can i bake")),
      "Plenty bakes without eggs: shortbread, flapjack, a fruit crumble, icebox biscuits and most "
      "traybakes need none at all. If a recipe wants an egg for binding, a tablespoon of ground "
      "flaxseed in three of water stands in for one, and a tablespoon of yogurt or half a mashed "
      "banana does the same job in a cake. Add a splash more milk, because egg is liquid too.",
      # "what can i use instead of an egg" is the *swap* row and it is more specific than this one
      # ("one egg becomes 60g of yoghurt, half a mashed banana, or a flax egg"), so the asking-for-a-
      # substitute shapes stand this row down and keep their own answer
      avoid=("instead", "replace", "substitute", "swap", "swap out", "egg free cake",
             "dinner", "tea", "supper", "buy", "shop", "sainsbury", "tesco", "price", "cost",
             "calories", "vegan", "gluten", "sank", "sinking", "sunny border", "plant",
             "freeze", "keep", "cook", "dinner", "tea"),
      bias=3)

entry_bored_of_chicken = entry(
      "bored-of-chicken",
      (("chicken", "chicken breast", "chicken breasts", "chicken thigh", "chicken thighs",
        "chicken wing", "chicken wings", "chicken drumsticks", "roast chicken", "whole chicken",
        "chicken pieces"),
       ("bored", "boring", "bored of", "fed up", "sick of", "tired of", "every night",
        "every day", "same thing", "different", "something else", "ideas", "other ideas",
        "another way", "change",
        # Betting on the words that are not a recipe: the meal ask is what a rut sounds like
        # when it is said as a question. "Something with chicken that's not a roast" and "what
        # can i do with chicken breasts" both fell through this row - the first to the whole-bird
        # timing card, the second to a roast-thigh time - because neither names boredom.
        "not a roast", "no roast", "isnt a roast", "instead of a roast", "apart from a roast",
        "other than a roast", "besides a roast", "what can i make", "what can i cook",
        "what can i do", "what else can i make", "what else can i do", "something with chicken")),
      "The fastest change is the cut and the heat rather than a new recipe: thighs roasted hot "
      "with paprika and lemon (200C for 35 to 40 minutes), breasts bashed flat and griddled in "
      "four minutes, wings salted and roasted at 200C for 45, or the whole bird pulled into tacos "
      "with lime and yogurt. After that it is the sauce that stops it being the same dinner - a "
      "traybake with chorizo and chickpeas, a satay with peanut butter and soy, or a tray of "
      "thighs marinated in yogurt and curry powder.",
      # the praise card ("the chicken was lovely"), the cooking times and the shopping are others
      avoid=("was lovely", "was delicious", "came out", "how long", "temperature", "calories",
             "healthy", "buy", "price", "raw", "frozen", "defrost", "freeze", "bone",
             # a chicken that is already cooked is the cooked-chicken card's: "any idea what to do
             # with leftover roast chicken" and "roast chicken leftovers ideas" were reaching this
             # row on "roast chicken" plus "ideas", and shredding it into a salad is the answer
             # they want, not a new way to cook one.
             "leftover", "leftovers", "left over", "cooked", "cold chicken", "sandwich",
             "sandwiches", "salad", "salads", "shred", "shredded", "use up", "using up",
             # "every day" is in this row's key, and it is also how the diet question is asked:
             # "can i eat chicken every day" and "is chicken every day bad for me" were answered
             # with a new way to cook it. Whether a food is all right daily is the verdict's.
             "can i eat", "ok to eat", "okay to eat", "safe to eat", "good for", "is chicken",
             "how often", "how much", "too much", "should i eat", "is it bad"),
      bias=3)

entry_bread_did_not_rise = entry(
      "bread-did-not-rise",
      (("bread", "loaf", "dough", "bread dough", "sourdough"),
       # the *question* shapes ask why, and they get the four causes. The report shapes stay with
       # the prove answer that already owns them ("Give it another hour..."), because a person who
       # says "my loaf didnt rise" is asking what to do next and that answer says it.
       ("not rise", "not risen", "did not rise", "hasnt risen", "hasn't risen",
        "hasnt proved", "hasn't proved", "why did", "why has", "why is", "what went wrong",
        "what happened")),
      "Four things stop a loaf rising, in the order worth checking. The yeast is dead - test it in "
      "warm water with a pinch of sugar and it should foam in ten minutes; water over about 45C, or "
      "a tin past its date, kills it. The water was too hot or too cold, so the dough never got "
      "going. The salt went in on top of the yeast and stalled it - keep them apart until the flour "
      "is in. Or it simply had not had long enough somewhere warm: doubling takes 1 to 2 hours at "
      "25C and much longer in a cold kitchen. A dough that rose and then fell was left too long.",
      # the rising instructions, the recipe, the shopping and a loaf gone stale are other answers,
      # and so is every other bread fault: bare "why is" plus a bread word reaches this row whatever
      # the fault is, so the cards that already own a sticky dough, a crumbly crumb, a dense loaf
      # and a pastry's dough stand it down - each of those is a different diagnosis, and the rise
      # card's four causes are the wrong four for them.
      avoid=("how do i make bread rise", "how long to prove", "how long do i prove", "recipe",
             "how do i make bread", "stale", "mouldy", "keep", "freeze", "buy", "price",
             "gluten free", "no yeast", "without yeast", "sourdough",
             "sticky", "crumbly", "dense", "sank", "sunken", "pastry",
             # a loaf still wet in the middle is the undercooked table's question, whatever the
             # "why is" in front of it: "why is my bread soggy in the middle" was getting the four
             # causes of a loaf that never rose
             "soggy in the middle", "wet in the middle", "doughy", "raw in the middle",
             "gummy", "wet inside", "stodgy",
             "not cooked in the middle", "not bake in the middle", "not cook in the middle",
             # a loaf that rose and fell has its own row now (`loaf-collapse`), and "why is my
             # bread collapsing" is that question, not this one
             "collapse", "collapses", "collapsed", "collapsing", "caved", "deflated", "fell"),
      bias=2)

ENTRIES.append(entry_no_eggs)
ENTRIES.append(entry_bored_of_chicken)
ENTRIES.append(entry_bread_did_not_rise)

# Scoring a loaf is what decides where a rising loaf opens: a slash you cut is a split you
# chose, and without it the crust tears wherever it is weakest, usually at the side. There was no
# row for it at all ("should i score the loaf" was "Not mine to decide, sorry").
entry_score_the_loaf = entry(
      "score-the-loaf",
      (("bread", "loaf", "loaves", "sourdough", "dough", "boule", "batard", "baguette", "rolls",
        "buns", "focaccia"),
       ("score", "scored", "scoring", "scores", "slash", "slashed", "slashing", "slashes",
        "cut the top", "cut into the top", "snip the top", "top of the loaf", "top of the bread",
        "split at the side", "splits at the side", "burst at the side", "bursts at the side",
        "split down the side", "burst open", "bursts open", "split open", "splits open",
        "cracked open", "cracks open", "crack on top", "cracked on top", "split on top")),
      "Yes - one slash about 1cm deep at a shallow angle is what decides where the loaf opens, "
      "so it rises where you cut instead of tearing wherever the crust is thinnest. Do it with a "
      "wet blade just before the loaf goes in, not before the final prove, or the cut closes up "
      "again. A tin loaf needs no slash, because the tin holds the sides and the top is free to "
      "rise; a round loaf or a long one on a tray wants one slash along it or a cross on top.",
      # a loaf that did not rise, a dense crumb, a bakery's bread, a cake and the shopping are
      # other rows: the words above are about the cut on the top and nothing else.
      avoid=("did not rise", "not risen", "not rise", "dense", "crumbly", "sank", "collapsed",
             "stale", "mouldy", "freeze", "recipe", "buy", "price", "calories", "sourdough starter",
             "cake", "cakes", "pastry", "score a goal", "score points", "score in", "test score",
             "credit score", "music", "sheet music", "film", "game", "match"))

ENTRIES.append(entry_score_the_loaf)
# --- making the basics yourself -------------------------------------------
# Butter, ice cream, fresh pasta, a soft cheese, kefir and ketchup were six shrugs on main: "how do
# i make butter" and "how do i make tomato ketchup" were a search hedge, "how do i make ice cream
# at home", "how do i make pasta", "how do i make cottage cheese" and "how do i make kefir" said
# they did not know. Each is one method with one temperature in it, and a friend answers it. They
# are keyed on the thing made and a making word, and every keeping, diet and buying question about
# the same food keeps the row it already had.
# What makes a line a making question. The ask in front of it ("can i", "how do i") is NOT here:
# every making question has a making word as well, and on its own the ask is also how a person
# asks whether they may use a thing - "can i use butter in cooking" and "can i use kefir in a
# smoothie" were the churn and the kefir cards, because "can i" scored beside the food word and
# the making question was never asked.
MAKE_AT_HOME = ("make", "making", "made", "home", "at home", "homemade", "home made", "myself",
                "own", "from scratch", "recipe", "churn", "churning", "ferment", "fermenting",
                "starter", "culture")

ENTRIES.append(entry(
    "make-butter",
    (("butter", "buttermilk"),
     MAKE_AT_HOME + ("cream", "double cream", "churn")),
    ("Churn double cream past whipped cream and it splits into butter and buttermilk: 300ml of "
     "double cream at room temperature, beaten in a food processor or shaken in a jar for 10 "
     "minutes, first goes thick, then grainy, then sloshes. Pour the buttermilk off, rinse the "
     "butter in ice-cold water and squeeze it dry with the back of a spoon, work in salt to "
     "taste, and it keeps 2 weeks in the fridge. The buttermilk is for scones or pancakes."),
    # a butter question that is not a making question: what it costs, what it does to you, how
    # long it keeps, what to use instead, and how much a recipe wants
    avoid=("keep", "keeps", "keeping", "gone off", "rancid", "freeze", "frozen",
           # a nut butter is not churned cream: it has a row of its own below
           "peanut", "peanuts", "peanut butter", "almond butter", "cashew", "nut butter",
           "substitute", "instead", "replace", "swap", "healthy", "healthier", "bad for you",
           "calories", "cholesterol", "dairy free", "vegan", "how much", "how many", "grams",
           "price", "cost", "cheap", "buy", "salted or unsalted", "lurpak", "brand",
           "shortbread", "cake", "pastry", "toast", "sandwich"),
    bias=2))

ENTRIES.append(entry(
    "make-ice-cream",
    (("ice cream", "icecream", "gelato", "sorbet"),
     MAKE_AT_HOME + ("machine", "churn", "freezer", "without a machine", "no churn")),
    ("No machine needed: whip 300ml of double cream to soft peaks, fold in a 397g tin of "
     "condensed milk and whatever flavouring you like, and freeze it in a loaf tin for 4 hours, "
     "stirring it twice in the first hour. The creamier way is a custard - 4 yolks, 100g sugar "
     "and 500ml of milk and cream cooked to 80C - frozen in a tub and beaten every 30 minutes "
     "three times. Home-made ice cream wants eating within a fortnight."),
    # "how do i stop ice cream going icy" is the crystals answer, not the making one: the word
    # "ice" in the line reaches this row through "ice cream", so the fault words hold it out
    # A "how long does ice cream last" line asks the freezer clock, not the method, and "last"
    # is how most people say it: "keeps" alone left the making row answering it with a recipe.
    avoid=("keep", "keeps", "keeping", "last", "lasts", "lasting", "still good",
           "use by", "go off", "gone off", "out of date",
           "melted", "melting", "soft", "scoop", "shop",
           "icy", "ice crystals", "crystals", "crystallised", "crystalised", "freezer burn",
           "grainy", "hard as a rock", "stops it going icy", "going icy", "went icy",
           "buy", "brand", "ben and jerrys", "healthy", "calories", "sugar", "dairy free",
           "vegan", "lactose", "milk free", "price", "cost", "vanilla ice cream",
           "strawberry ice cream", "which ice cream", "best ice cream"),
    bias=2))

ENTRIES.append(entry(
    "make-pasta",
    (("pasta", "tagliatelle", "fettuccine", "ravioli", "pappardelle"),
     MAKE_AT_HOME + ("dough", "flour", "egg", "eggs", "semolina", "fresh")),
    ("Fresh pasta is 100g of tipo 00 flour and one large egg per person, mixed to a stiff dough, "
     "kneaded 5 minutes and rested 30 minutes under a bowl, then rolled as thin as you can and "
     "cut. It cooks in 2 to 3 minutes in salted water, not the 10 a dried pasta takes. Semolina "
     "and water with no egg is the southern way, and it wants a rolling pin or a machine."),
    # a pasta question is mostly not this one: the cooking time, the shape, the sauce, the bake
    # and the swap all have rows of their own, and this row is only the making
    avoid=("how long", "cook", "cooking", "boil", "al dente", "sauce", "bake", "baked",
           "lasagne", "shape", "shapes", "gluten free", "instead", "substitute", "keep",
           "leftover", "calories", "healthy", "dried", "packet", "brand", "barilla",
           "price", "cost", "how much pasta", "portion", "grams per person",
           # "i made too much pasta" is the surplus row's line, not a recipe
           "too much", "made too much", "make too much", "left over", "left over pasta"),
    bias=2))

ENTRIES.append(entry(
    "make-soft-cheese",
    (("cottage cheese", "cream cheese", "soft cheese", "ricotta", "mascarpone", "quark",
      "paneer", "halloumi", "cheese"),
     MAKE_AT_HOME + ("milk", "vinegar", "lemon", "rennet", "curdle", "curds")),
    ("Warm 2 litres of whole milk to 80C - steaming, not boiling - stir in 3 tablespoons of "
     "lemon juice or white vinegar, and it separates into curds and whey. Strain it through a "
     "muslin for 20 minutes for a soft curd to eat that day, four hours for a cottage cheese, or "
     "overnight with a weight on it for a paneer you can fry. Add a pinch of salt and a splash "
     "of the whey back at the end, and keep it 5 days."),
    avoid=("keep", "keeps", "keeping", "gone off", "healthy", "calories", "protein",
           "instead", "substitute", "buy", "shop", "brand", "philadelphia", "price", "cost",
           "cake", "cheesecake", "on toast", "sauce", "melt", "melted", "grated", "toastie",
           "sandwich", "board", "baked", "macaroni", "pizza", "topping"),
    bias=2))

ENTRIES.append(entry(
    "make-kefir",
    (("kefir", "water kefir", "milk kefir"),
     MAKE_AT_HOME + ("grains", "milk", "culture", "starter", "ferment")),
    ("Milk kefir is 1 to 2 tablespoons of live kefir grains in a litre of whole milk in a jar "
     "with a loose lid, left out of the fridge for 24 hours and then strained: the grains go back "
     "in fresh milk and the kefir goes in the fridge. The grains grow, so give the extra away. "
     "With no grains, 2 tablespoons of live yoghurt or buttermilk starts it off, though it stops "
     "after a few lots. It keeps a week."),
    avoid=("keep", "keeps", "keeping", "healthy", "good for you", "gut", "probiotic",
           "buy", "shop", "brand", "price", "cost", "dairy free", "lactose", "calories",
           "where can i buy"),
    bias=2))

ENTRIES.append(entry(
    "make-ketchup",
    (("ketchup", "tomato ketchup", "catsup"),
     MAKE_AT_HOME + ("tomatoes", "tomato", "sauce", "sugar", "vinegar")),
    ("Simmer 1kg of tomatoes with an onion, 100g of sugar, 150ml of vinegar, a teaspoon of salt "
     "and a spice bag of cloves, peppercorns and a bay leaf for 45 minutes, then blend it and "
     "simmer it down until a spoon dragged across the pan leaves a line. Push it through a sieve "
     "and bottle it hot: it keeps a month in the fridge once opened. Tinned tomatoes and half the "
     "sugar make a thinner, sharper ketchup."),
    avoid=("keep", "keeps", "keeping", "healthy", "sugar", "calories", "instead",
           "substitute", "buy", "shop", "brand", "heinz", "price", "cost", "on chips",
           "with chips", "how much"),
    bias=2))

# Four more things people make at home rather than buy, all of them a shrug or a wrong card on
# main: "can i make my own peanut butter" was a search hedge (and, once the butter row above was
# written, the churned-cream butter - a nut butter is not dairy), "can i make my own baked beans",
# "can i make my own sausages" and "can i make my own ice lollies" were a hedge and a cool-bag card.
ENTRIES.append(entry(
    "make-peanut-butter",
    (("peanut butter", "nut butter", "almond butter", "cashew butter", "peanuts"),
     MAKE_AT_HOME + ("peanut", "peanuts", "nuts", "blitz", "roast")),
    # A row that keys on the food alone answers every line that names it, and "peanut butter" is
    # in half the peanut questions there are: "can i give my baby peanut butter" wants the
    # six-months smear, "is peanut butter good for you" the two tablespoons, "can i eat peanut
    # butter" the nut-free list. What makes this row the answer is the asking, so the making words
    # are required rather than merely worth a point.
    ("Roast 300g of shelled peanuts at 180C (160C fan) for 10 minutes until they smell nutty, "
     "then blitz them in a food processor for 3 to 5 minutes, scraping down the sides: first it is "
     "crumbs, then a ball, then suddenly a smooth butter. Add a pinch of salt and a teaspoon of "
     "honey, and a spoon of oil if you want it looser. It keeps a month in a jar."),
    # "peanut butter" is the whole first arm of the key, so every line that says it matched
    # both arms and got the recipe back: "can i eat peanut butter while pregnant", "... while
    # breastfeeding", "... every day", "is peanut butter safe during pregnancy". Whether it is
    # safe to eat is not how to make it, and the words that ask it stand this row down. The
    # class is a food named in both arms - a recipe row whose subject is its own keyword - and
    # the other make- rows here ("make-butter", "make-ice-lollies") name their subject once, so
    # they never took an "is it ok to eat" line.
    avoid=("keep", "keeps", "keeping", "healthy", "calories", "protein", "instead",
           "substitute", "buy", "shop", "brand", "price", "cost", "sandwich", "toast",
           "allergy", "allergic", "reaction", "dogs",
           "pregnant", "pregnancy", "expecting", "every day", "a day", "portion", "serving",
           "good for you", "good for me",
           # A baby's portion is a weaning question, not a recipe: "can my baby have peanut
           # butter" and "how do i give my baby peanut butter" were both the roast-and-blitz
           # card while the allergen row that answers them was stood down by this one. The
           # make-ice-lollies row beside it carries the same fence for the same reason.
           "baby", "babies", "toddler", "toddlers", "my son", "my daughter", "weaning",
           "first foods", "first tastes", "highchair", "high chair",
           # not "breastfeeding": with this row standing down, "can i eat peanut butter while
           # breastfeeding" fell to the caffeine row and was told 200mg a day, which is no better
           # than the recipe. The eating-while-feeding fence is a separate change, and this row
           # should not hand a line to a worse answer on its way out.
           ),
    # The avoid list above names the ways a line asks about eating peanut butter, and that is a
    # list nobody finishes: "can i eat peanut butter", with no feeding and no diet word in it,
    # still matched both arms and got the recipe. A how-to row needs the how-to ask. MAKE_AT_HOME
    # is what every other recipe row here keys with, so this row is "make it" only when the line
    # says make, and no list of ways somebody might ask whether they can eat it has to be kept.
    bias=2, ask=MAKE_AT_HOME))

# The other question about a jar of nut butter: it separates. With the recipe row standing down
# for a line that does not say make, "how do i stop peanut butter separating" lost its answer
# altogether, and the recipe it used to get was not it either.
ENTRIES.append(entry(
    "nut-butter-separates",
    (("peanut butter", "nut butter", "almond butter", "cashew butter"),
     ("separat", "separates", "separating", "separated", "oily", "oil on top", "stir",
      "stirring", "runny", "liquid", "grainy", "hard", "stiff", "fridge", "upside down",
      "store", "storing", "storage", "keep", "keeping", "keeps")),
    "Natural nut butter separates because there is nothing in it but nuts: the oil rises and the "
    "solids sink. Stir it back in with a knife, from the bottom of the jar upwards, and it comes "
    "together in a minute or two. A jar that has set hard mixes more easily if it stands upside "
    "down for a day first, and standing it in a bowl of warm water for five minutes softens it "
    "without cooking it. An opened jar keeps a few months in the cupboard and longer in the "
    "fridge, though cold makes it stiffer to spread.",
    avoid=("make", "making", "recipe", "blitz", "roast", "roasted", "homemade", "calories",
           "healthy", "allergy", "allergic", "baby", "sandwich", "toast", "brand", "best",
           "buy", "shop", "cost", "price", "cookie", "cake", "biscuit"),
    bias=2))
ENTRIES.append(entry(
    "make-ice-lollies",
    (("ice lollies", "ice lolly", "popsicles", "popsicle", "ice pops", "lolly", "lollies"),
     MAKE_AT_HOME + ("juice", "mould", "moulds", "molds", "sticks", "freezer", "fruit")),
    ("Blend or mash soft fruit with a little sugar and lemon - strawberries, mango, berries, or "
     "just orange juice - and pour it into moulds or paper cups with a stick in, leaving a "
     "centimetre at the top because water expands. Four to six hours in the freezer. A splash of "
     "yoghurt or milk makes them creamier, and a spoon of vodka stops them going rock hard."),
    avoid=("keep", "keeps", "keeping", "melted", "melting", "shop", "buy", "brand",
           "healthy", "sugar", "calories", "price", "cost", "toddler", "baby", "choking"),
    bias=2))

ENTRIES.append(entry(
    "make-baked-beans",
    (("baked beans", "beans on toast", "haricot beans", "cannellini beans"),
     MAKE_AT_HOME + ("tomato", "tomatoes", "sugar", "haricot", "dried")),
    ("Soak 250g of dried haricot beans overnight, boil them hard for 10 minutes then simmer for "
     "an hour until soft (or start from two tins). Simmer a tin of tomatoes with an onion, a "
     "tablespoon of black treacle or brown sugar, a teaspoon of mustard, a splash of vinegar and "
     "a pinch of salt for 20 minutes, stir the beans in and bake at 160C (140C fan) for 40 "
     "minutes. It keeps 4 days and freezes."),
    avoid=("keep", "keeps", "keeping", "healthy", "calories", "sugar", "instead",
           "substitute", "buy", "shop", "brand", "heinz", "price", "cost", "on toast",
           "how long do i cook", "tin of"),
    bias=2))

ENTRIES.append(entry(
    "make-sausages",
    (("sausages", "sausage meat", "sausagemeat"),
     MAKE_AT_HOME + ("mince", "meat", "pork", "casings", "skins", "seasoning")),
    ("Sausages are 70/30 lean pork to fat, minced coarse and kept cold: for 1kg of shoulder add "
     "18g of salt, a teaspoon of pepper, a teaspoon of sage and 100ml of iced water, mix it until "
     "it is sticky, and stuff it into soaked hog casings - or shape it into patties, which needs "
     "no casing at all. Fry a small piece to taste for salt before you stuff the rest. Eat them "
     "within 3 days or freeze them."),
    avoid=("keep", "keeps", "keeping", "healthy", "calories", "protein", "instead",
           "substitute", "buy", "shop", "brand", "price", "cost", "how long do i cook",
           "how do i cook", "in the oven", "air fryer", "barbecue", "bangers"),
    bias=2))

# Two more of the same family, from the same probe: "how long do i ferment yoghurt for" and "how
# long do i incubate yoghurt for" reached the keeping row ("An unopened tub keeps about a week past
# the date on the lid") because "how long" is a keeping word, and "what temperature for yoghurt"
# was a shrug; "can i make my own granola" and "can i make my own muesli" were both a shrug as well.
ENTRIES.append(entry(
    "yoghurt-fermenting",
    (("yoghurt", "yogurt", "yoghurt maker", "yoghurt pot"),
     ("ferment", "fermenting", "fermented", "incubate", "incubating", "incubator", "culture",
      "starter", "warm spot", "airing cupboard", "what temperature", "how warm", "set it",
      "how long do i leave", "how long to ferment", "didnt set", "did not set", "wont set")),
    ("Keep it at 43C for 8 to 12 hours: a yoghurt maker does it, an airing cupboard or an oven "
     "switched off with the light on is close enough, and a flask of it in a warm water bath "
     "works too. Below 40C it takes longer and tastes sourer, above 46C the culture dies and it "
     "stays milk. It is set when it pulls away from the side of the jar - then chill it for 4 "
     "hours before eating, which is when it firms up properly."),
    avoid=("keep", "keeps", "keeping", "use by", "past the date", "out of date", "gone off",
           "mould", "cheap", "buy", "brand", "calories", "protein", "dairy free", "lactose",
           # "starter" is a yoghurt culture here, and a sourdough jar is a different
           # starter: "my starter smells like yoghurt" was told to hold 43C for 8 to 12
           # hours, which is the incubating answer for a jar nobody is incubating.
           "my starter", "the starter", "starter smells", "starter has",
           "starter is", "starter went", "starter gone"),
    bias=3))

# A crisp that is made at home is the same question as the butter and the yoghurt: what a person
# types is "can i make my own crisps" and the packet card ("a handful of crisps is a treat") is
# the wrong answer, because they have already decided to make them.
ENTRIES.append(entry(
    "make-crisps",
    (("crisps", "potato crisps", "crisp"),
     MAKE_AT_HOME + ("potato", "potatoes", "sliced", "slices", "oven", "fry", "frying",
                     "salted", "salt", "crunchy", "crispy")),
    ("Slice floury potatoes about 2mm thin - a mandoline, or a peeler does one at a time - rinse "
     "the starch off in cold water, then dry the slices properly on a tea towel: a wet slice "
     "steams instead of crisping. Fry at 160C for 3 minutes, until the bubbling dies down, or "
     "toss them in a tablespoon of oil and bake at 200C for 15 to 20 minutes, turning once. Salt "
     "the moment they come out and cool them on kitchen paper. Dry slices and a steady "
     "temperature are the whole trick."),
    # A roast potato is a crisp word too, and "how do i get a crisp roast potato" was this row
    # telling somebody to slice potatoes 2mm thin. Anything that says roast is the oven tray.
    avoid=("roast", "roasts", "roasted", "roasting", "parboil", "parboiled", "parboiling",
           "sunday lunch", "yorkshire",
           "buy", "buying", "shop", "brand", "packet", "walkers", "which", "best", "healthy",
           "healthier", "bad for you", "calories", "sugar", "salt in", "how much salt",
           "baby", "toddler", "kids", "child", "keto", "air fryer", "keep", "keeps", "keeping",
           "pastry", "crumble", "apple", "shop bought", "multipack", "price", "cost", "cheap",
           # A chip is not a crisp, but "crispy" folds to "crisps" and reached this row: "how do
           # i make crispy chips" was a packet of crisps recipe, and the cut-potato answer -
           # `veg-chips-crisp`, which is about the chips - never got its turn.
           "chip", "chips", "fries", "french fries", "oven chips", "chip shop",
           # and a roast potato is not a crisp either: "how do i get a crisp roast potato" was
           # thin slices fried at 160C, which is a crisp, and `roast-potatoes` (parboil, shake,
           # hot fat) is the answer the person asked for. A crisp word in a roast line is about
           # the outside of the potato, not a different dish.
           "roast", "roasted", "roasting", "roasties", "parboil", "parboiled", "sunday dinner"),
    bias=2))

ENTRIES.append(entry(
    "make-granola",
    (("granola", "muesli", "toasted oats", "breakfast cereal"),
     MAKE_AT_HOME + ("oats", "honey", "syrup", "nuts", "oven", "bake", "toast")),
    ("Toss 300g of oats with 100g of nuts and seeds, then stir in 3 tablespoons of oil, 3 of honey "
     "or maple syrup and a pinch of salt, and spread it thin on a lined tray. Bake at 160C (140C "
     "fan) for 20 to 25 minutes, stirring twice, until it is golden - it crisps as it cools. Add "
     "dried fruit after baking, or it burns. It keeps a month in a jar; muesli is the same mix "
     "untoasted."),
    avoid=("keep", "keeps", "keeping", "healthy", "calories", "sugar", "protein", "buy",
           "shop", "brand", "price", "cost", "which", "best", "toddler", "kids"),
    bias=2))

# Shortbread is asked as an amount ("how much butter in shortbread") as often as a recipe, and the
# kitchen had no card at all - the baby weaning row used to answer it, which is a card about a
# child's first fats. The ratio is the answer, so it leads, and the method follows from it.
ENTRIES.append(entry(
    "shortbread-amounts",
    (("shortbread", "shortbreads", "shortbread fingers", "millionaires shortbread"),
     ("butter", "how much", "how many", "much", "ratio", "ratios", "flour", "sugar",
      "margarine")),
    ("Shortbread is one part sugar, two parts butter and three parts flour: for a 20cm round that "
     "is 60g caster sugar, 120g butter and 180g plain flour. Cream the butter and sugar, work in "
     "the flour without kneading it, press it into the tin, prick it, and bake at 150C (130C fan) "
     "for 35 to 40 minutes until it is pale gold rather than brown. It firms as it cools, so cut "
     "it into fingers while it is still warm."),
    avoid=("calories", "how many calories", "healthy", "diet", "buy", "shop", "supermarket",
           "brand", "price", "cost", "gluten", "vegan", "baby", "toddler", "child",
           "thermomix", "air fryer", "biscuit base", "cheesecake", "crumbly", "crumbs",
           "store", "storing", "keep", "keeps", "sealed", "freeze", "frozen",
           "food processor", "processor", "recipe", "recipes", "how do i make",
           "how long", "oven"),
    bias=2))

# A fruit jelly is a jam, and making one is not: "how do i make apple jelly" and "how do i make
# mint jelly" were both the honest shrug on main, and the jam row answers the setting point, not
# the straining. The fault words stay with the fault rows, so "my jelly didnt set" and "how do i
# know when jam is set" still get their own answers.
ENTRIES.append(entry(
    "make-fruit-jelly",
    (("apple jelly", "mint jelly", "redcurrant jelly", "crab apple jelly", "bramble jelly",
      "blackberry jelly", "quince jelly", "rowan jelly", "rosemary jelly", "damson jelly",
      "fruit jelly", "jelly", "jellies"),
     ("make", "making", "homemade", "from scratch", "how do i", "how to", "recipe",
      "apples", "apple", "mint", "redcurrants", "crab apples", "brambles", "blackberries",
      "quinces", "damsons", "strain", "muslin", "juice")),
    ("Cook the fruit with just enough water to stop it catching - apples and blackberries 20 "
     "minutes, redcurrants 10, mint as a strong vinegar infusion - then strain it through a "
     "muslin or a clean tea towel hung over a bowl and leave it overnight: squeeze it and the "
     "jelly goes cloudy. For every 600ml of juice weigh out 450g of sugar, warm them together "
     "until the sugar has gone, then boil hard to 104C (or until a drop on a cold plate "
     "wrinkles) and pot it hot. It sets in a day."),
    avoid=("didnt set", "did not set", "wont set", "won't set", "not set", "runny", "liquid",
           "how do i set", "how to set", "set a jelly", "set the jelly", "set it", "setting point",
           "when is it set", "is it set", "has it set", "how do i know when", "know when a jelly",
           "wobbly", "how long does", "keeps", "keeping", "out of date", "gone off", "mould",
           "calories", "sugar", "healthy", "buy", "shop", "brand", "price", "cost", "rowntrees",
           "hartley", "jam", "marmalade", "chutney", "crumble", "pie", "cake"),
    bias=2))

# A child who has already drunk the milk that turned is not asking what to do with the bottle: the
# keeping row ("bin it, use it within about 5 days") answers a shopping question, and this is the
# half hour after the drink. Sour milk is not a poisoning, and saying so is the whole of the help.
# The reply is written for a child, and "Ring 111 if the child is under one" is wrong for a
# grown-up who did it themselves: "i drank milk that smelt sour" was getting this card. The row
# keeps the half hour after a child's drink, so the child has to be in the line.
_CHILD_DRANK_IT = re.compile(
    r"\b(?:baby|babies|infant|toddler|toddlers|child|children|childs|kid|kids|boy|girl|son|"
    r"daughter|newborn|little one|grandchild|grandson|granddaughter)\b")
ENTRIES.append(entry(
    "milk-that-turned-was-drunk",
    (("milk",),
     ("drank", "drunk", "drank some", "swallowed", "sipped", "had some", "has had some",
      "gave him", "gave her", "gave my", "gave the", "off milk", "sour milk", "turned milk",
      "milk that was off", "milk that had gone off", "milk was off", "milk had gone off",
      "bad milk", "milk that turned", "curdled milk")),
    ("Sour milk is curdled and unpleasant, not poisonous: it will not give a child the food "
     "poisoning that undercooked meat does, and a mouthful or a cup is very unlikely to do "
     "anything. Offer water, and watch for vomiting or diarrhoea over the next few hours. Ring "
     "111 if the child is under one, cannot keep water down, or seems unwell rather than just "
     "cross about it. Then bin the bottle - the date is about quality, not safety."),
    avoid=("how do i know", "how can i tell", "how long", "keep", "keeps", "keeping",
           "use by", "date on the", "freeze", "frozen", "buy", "brand", "price", "cost",
           "calories", "protein", "lactose", "allergy", "allergic", "recipe", "sauce",
           "cheese", "yoghurt", "yogurt", "kefir", "breastfeeding", "formula", "cows milk",
           "which milk", "what milk", "oat milk", "soya milk", "almond milk"),
    guard=lambda understood: bool(_CHILD_DRANK_IT.search(
        " " + str((understood or {}).get("clean") or "").lower() + " ")),
    bias=3))

# A burnt pot has a rescue answer already, and "why does my rice keep burning" was given it: the
# person asked what went wrong and got told to lift the burnt bits out. The two questions need two
# answers, so a why or a stop or a keeps-burning wording has its own row, with the cause.
entry_rice_burnt = entry(
      "rice-keeps-burning",
      (("rice", "basmati", "long grain", "pilau", "risotto rice", "brown rice"),
       ("why", "keep burning", "keeps burning", "always burn", "always burning", "burning",
        "burns", "burn", "stop it burning", "stop burning", "prevent",
        "what am i doing wrong")),
      "Rice burns when there is no water left under it: the heat is too high, so the pan dries out "
      "before the grain is cooked and the bottom scorches. One mug of rice to one and a half of "
      "water, bring it to the boil with the lid on, then turn it down to the lowest ring for 10 to "
      "12 minutes without stirring - stirring rubs the starch off and makes it catch. A heavy pan "
      "and a lid that fits are most of the fix, and 5 minutes off the heat at the end finishes it.",
      # the question has to be a why or a how-to-stop: "i burnt the rice again" wants the rescue
      # card, which is the one that says what to do with the pan in front of them
      ask=("why", "keep", "keeps", "always", "stop", "prevent", "wrong"),
      bias=2,
      # what to do with the pan that has already burnt is the rescue card, and a rice pudding or a
      # fried rice is another dish
      avoid=("already burnt", "what can i do", "what do i do", "do with", "can i still eat",
             "still eat", "throw", "bin", "rescue", "save it", "burnt bits",
             # rice that sticks is the rinse-and-ratio card, which is the better answer.
             # "sticky" is here as well as "stick": the fault is nearly always said that way
             # ("why does rice go sticky", "why is my rice sticky"), and the word was missing,
             # so the question "why does rice go sticky" was given the reason rice burns.
             "stick", "sticks", "sticking", "sticky", "stick to the pan", "catch", "catches",
             # a rice that came out wrong in another way has its own fault card
             "crunchy", "crunch", "hard", "undercooked", "underdone", "raw", "mushy",
             "stodgy", "soggy", "wet", "dry", "slimy", "gluey",
             "rice pudding", "fried rice", "risotto", "paella", "sushi", "rice cooker",
             "how long", "calories", "healthy", "freeze", "reheat", "leftover rice", "buy",
             "price", "grow"))

ENTRIES.append(entry_rice_burnt)

# "can i freeze an open bag of frozen peas" and "can i refreeze frozen peas" were both told how long
# to boil peas: the freezer table answers "can i freeze X" for food that is not frozen yet, and an
# open bag or a second freeze is a different question. The rule people want is short, so it leads.
ENTRIES.append(entry(
    "freeze-an-open-bag",
    (("freeze", "freezing", "frozen", "freezer", "thaw", "thawed", "thawing", "defrost",
      "defrosted", "defrosting"),
     ("refreeze", "re freeze", "re-freeze", "again", "twice", "already", "open", "opened",
      "bag", "packet", "pack", "opened bag", "half used", "half bag", "left out")),
    ("An open bag of frozen veg goes straight back in the freezer: press the air out, clip it, and "
     "use it within a month or two before it dries out or picks up ice. Re-freezing is the one with "
     "a rule: food that has fully thawed can be cooked and then frozen again, but not frozen raw a "
     "second time, because the thaw is when bacteria multiply and freezing does not kill them. "
     "Frozen peas that have half thawed in a warm kitchen are still peas - cook them now rather "
     "than put them back."),
    # a line that names a second freeze or an opened bag; "can i freeze mashed potato" and "can i
    # freeze milk" are the freezer table's own questions and stay there
    ask=("refreeze", "re freeze", "re-freeze", "again", "twice", "already", "open", "opened",
         "bag", "packet"),
    avoid=("mashed", "milk", "breast milk", "cakes", "cake", "bread", "meat", "chicken", "beef",
           "pork", "fish", "rice", "soup", "stock", "banana", "bananas", "avocado", "eggs",
           "potatoes", "cooked", "leftover", "leftovers", "put the heating", "pipes", "burst"),
    bias=2))

# "what can i put on a baked potato" was the dinner-ideas fallback, which answered with how to
# roast wedges: the potato is already baked and the question is what goes on it. The jacket rows
# in cooking.py answer the bake and the filling from the same entry, and their filling text is
# reused here rather than written a second time, so one potato question keeps one answer.
entry_potato_toppings = entry(
      "baked-potato-toppings",
      (("baked potato", "baked potatoes", "jacket potato", "jacket potatoes", "potato",
        "potatoes"),
       ("put on", "topping", "toppings", "top it", "fill", "filling", "fillings",
        "what can i put", "what do you put", "what should i put", "what goes on")),
      JACKET_FILL,
      ask=("put on", "topping", "toppings", "fill", "filling", "fillings", "goes on",
           "what can i put", "what do you put", "what should i put"),
      # how long to bake it, how long it keeps and what to do with mash are other cards
      avoid=("how long", "oven", "temperature", "calories", "healthy", "buy", "price", "keep",
             "leftover", "leftovers", "freeze", "frozen", "reheat", "mash", "mashed", "chips",
             "wedges", "soup", "peel", "grow", "growing", "plant", "plants", "dog", "dogs",
             "sprout", "sprouts", "raw", "boil", "boiling", "microwave", "salad",
             # cheese and beans is what goes *in* a potato; what goes *on* it is the seasoning
             # table: "what herbs should i put on potatoes" got the fillings for "put on"
             "herb", "herbs", "spice", "spices", "seasoning", "rosemary", "thyme", "paprika",
             "cumin", "salt and pepper"))

ENTRIES.append(entry_potato_toppings)


# --- a recipe made for a different amount or a different tin -------------------------------
# "does doubling a recipe double the time" reached a search hedge, "can i halve a recipe" too, and
# "i have a bigger tin than the recipe says" was answered with the price-per-kilo card. All three
# are one question: the numbers on the page are for a different size of the same dish, and what
# changes is the vessel and the timing, not the heat. The batch words are keyed apart from "batch
# cook" and "two trays at once", which have their own rows.
_TIN_AREA = {
    "15cm": "about half",
    "18cm": "about a third less than a 20cm",
    "20cm": "the recipe's own",
    "23cm": "about a third more",
    "25cm": "about half again",
}


def _recipe_amount(memory, understood):
    """The answer for a doubled, halved or differently tinned recipe, chosen by the words said."""
    said = " " + str((understood or {}).get("clean") or understood.get("text") or "").lower() + " "
    tin = any(word in said for word in (" tin ", " tins ", " sandwich tin", " cake tin"))
    other_size = any(phrase in said for phrase in
                     ("bigger", "larger", "smaller", "different size", "different tin",
                      "other tin", "wrong size", "too big", "too small", "deeper"))
    if tin and other_size:
        return ("Go by the area of the tin rather than the numbers on the page: a 23cm round holds "
                "about a third more than a 20cm, so the same batter fills it shallower and bakes "
                "5 to 10 minutes faster, and scaling the batter up by that third fills it to the "
                "same depth in the same time. Keep the oven temperature, fill to two-thirds, and "
                "check with a skewer 5 minutes before the recipe's time either way.")
    halving = any(phrase in said for phrase in
                  ("halve", "halving", "half the recipe", "half a recipe", "half this recipe",
                   "half batch", "smaller batch", "only two of us", "just for one",
                   "just me", "for two"))
    if halving:
        return ("Halve everything except the egg and the raising agent: beat the egg and weigh "
                "half of it, and keep the baking powder or yeast nearer two-thirds, because it "
                "does not scale down in a straight line. Use a smaller tin or pan so the depth "
                "stays the same, keep the temperature, and start checking 5 minutes earlier - a "
                "smaller batch comes up to heat and browns sooner.")
    return ("No - the time barely changes, the quantity does. Keep the oven or hob where it was "
            "and add 10 to 20 minutes for the extra volume to heat through and reduce, checking "
            "early rather than trusting the clock. Use a wider pot or two tins rather than a "
            "deeper one, swap two trays on their shelves halfway, and cut the liquid by about a "
            "tenth because less of it evaporates. Salt, chilli, stock and herbs do not double "
            "exactly: add three-quarters, taste, then top up.")


ENTRIES.append(entry(
    "recipe-amount",
    # the amount words, then a cooking word, so "double glazing", "a double bed" and "twice a
    # week" never reach the kitchen
    (("double the recipe", "double a recipe", "double this recipe", "doubling the recipe",
      "doubling a recipe", "doubling", "doubled the recipe", "double batch", "double the batch",
      "two batches", "twice as much", "make twice", "twice the recipe", "halve", "halving",
      "half the recipe", "half a recipe", "half this recipe", "half batch", "smaller batch",
      "bigger tin", "larger tin", "smaller tin", "different tin", "tin size", "bigger cake",
      "bigger dish", "smaller dish", "scale up", "scale down", "scale the recipe",
      # the second turn on a time: "a roast chicken takes 1 hour 20" then "and if i cook two at
      # once" reached the echo, and the pair words keep it off the oven-shelf row
      "two at once", "cook two at once", "two at the same time", "cook two at the same time",
      "make two at once", "bake two at once", "two in the oven at once"),
     ("recipe", "recipes", "batch", "mixture", "batter", "dough", "ingredients", "quantities",
      "amount", "amounts", "tin", "tins", "cook", "cooking", "bake", "baking", "oven", "time",
      "longer", "freeze", "portion", "portions")),
    _recipe_amount,
    # "i have a bigger tin than the recipe says" and "i want to double a recipe" state the job
    # rather than ask about it, so the person's own words about their tin or their intention are
    # an ask too
    ask=("does", "do i", "can i", "should i", "how long", "how much", "will", "if i", "is it",
         "what", "longer", "time", "quantities", "i have", "ive got", "i've got", "i want",
         "i need", "i only", "im making", "i'm making"),
    # double glazing, a double bed, a double garage and a double dose of medicine are not a
    # bigger dinner; the dairy, freezer and bread rows answer their own lines
    avoid=("glazing", "glazed", "bed", "garage", "vision", "check", "checked", "dose", "doses",
           "tablets", "medicine", "paracetamol", "ibuprofen", "antibiotic", "insulin", "breast",
           "formula", "baby", "toddler", "dog", "cat", "air fryer", "slow cooker", "microwave",
           "yorkshire", "bread", "sourdough", "starter", "pizza", "roast potatoes", "turkey",
           "chicken", "chickens", "bird", "birds", "cake", "cakes", "sponge", "tray", "trays",
           "tin of", "dishes", "things", "christmas", "calories", "how many calories", "protein", "price", "cheaper", "buy",
           "supermarket", "pack", "keep", "keeps", "reheat", "leftover", "leftovers",
           # "double cream" is the dairy and not "double the recipe": the bare word "double" is
           # read as "doubling", so "can i freeze double cream" was the add-20-minutes card. The
           # phrases are adjacent words, so "can i double the cream in a recipe" still reaches
           # this row, which is what it is for.
           "double cream", "single cream", "soured cream", "creme fraiche", "whipping cream",
           "extra thick cream", "double cream in", "a pot of cream", "cream cheese"),
    bias=1))
# "What weight is a joint" was the weight-training card: "choose a weight you can lift 10 times
# but not 15". A joint of meat asked about by weight is a shopping question, and the portion the
# table already knew ("about 250g of raw meat each with the bone in") is the answer, with the
# buy-weight worked out from the count when the line gives one. The card is `_roast_for_a_crowd`,
# asked for its own reply, so the shopping and the timetable cannot drift apart.
#
# The avoid list is the other rows' lines rather than this one's: a named meat is its own
# minutes-per-500g answer, a time word is `joint-time`, a slow roast is the slow-roast row, and
# a knee, a hip or a shoulder is a body. The weight-training card keeps every line with a lift,
# a dumbbell or a gym in it, because none of those words is here.
entry_joint_weight = entry(
      "joint-weight",
      (("joint", "joints", "roast"),
       ("what weight", "weight", "how heavy", "how big", "how much", "size", "per person",
        "each", "each person", "per head")),
      _roast_for_a_crowd,
      ask=("weight", "what weight", "how heavy", "how big", "how much", "size",
           "per person", "per head", "each"),
      avoid=("how long", "time", "timing", "timetable", "minutes", "oven", "temperature",
             # "roasting" is not here either: its forms are the "roast" this row asks with.
             "gas mark", "cook", "cooking", "done", "kilo", "kilos", "kg",
             "pound", "pounds", "lbs",
             "chicken", "turkey", "duck", "goose", "beef", "lamb", "pork", "gammon", "ham",
             "brisket", "shoulder", "leg of", "joint of", "mince", "slow cooker", "air fryer",
             "my joint", "joints hurt", "joint pain", "knee", "knees", "hip", "hips",
             # "weights" is not here on purpose: its plural form is the plain "weight" the
             # question is asked with, so it stood this row down on its own lines.
             "lift", "lifting", "dumbbell", "dumbbells", "barbell", "gym",
             "workout", "exercise", "squat", "squats", "press"))

ENTRIES.append(entry_joint_weight)

# "how do i know the griddle is hot" was "That's beyond what I know well, sorry", and "when is the
# griddle hot enough" was the washing-machine temperature card. The pan-heat answer already exists
# for a line that names the oil ("the oil shimmers and moves in the pan"), but a person asking how
# to tell is often asking before anything is in the pan, and the row needed a fat to be reached.
# So this one keys the pan and the asking, and stands down when a fat or a smoke point is named, so
# "when does oil start to smoke" keeps its own card.
_PAN_THING = ("pan", "pans", "griddle", "griddle pan", "skillet", "frying pan", "wok",
              "saucepan", "non stick pan", "pan base", "flat pan", "cast iron pan")
_PAN_IS_HOT_ASK = ("hot", "hot enough", "properly hot", "up to heat", "ready", "heated",
                   "how do i know", "how can i tell", "how do you know", "when is it",
                   "when is the", "how long to heat", "how long does it take to heat",
                   "warm enough", "smoking hot")

ENTRIES.append(entry(
    "pan-heat-without-a-fat",
    (_PAN_THING, _PAN_IS_HOT_ASK),
    ("Three things, and any one of them is enough. Hold your hand an inch above the surface: it "
     "should feel properly hot after about two seconds, not straight away. Flick a few drops of "
     "water in and they should bead and skate across the pan rather than sit there and hiss. And "
     "the whole base should look faintly shimmering rather than wet. Give a heavy pan three or "
     "four minutes on a medium heat and a thin one two, and let it heat before you turn it up."),
    # a fat or a smoke point is the oil row's question, and so is anything being cooked: "how do i
    # know the chicken is done" is a temperature question, not a pan one
    avoid=("oil", "oils", "butter", "fat", "lard", "ghee", "dripping", "smoke", "smoking",
           "smoke point", "season", "seasoning", "clean", "cleaning", "wash", "washed", "burnt",
           "stuck", "stick", "rust", "oven", "temperature of the oven", "gas mark", "air fryer",
           "chicken", "steak", "fish", "egg", "eggs", "pancake", "bacon", "onion", "bread",
           "buy", "price", "which pan", "what pan", "best pan", "induction", "hob", "hot plate",
           "hotplate", "barbecue", "bbq", "grill",
           # "how do i know when the pan is hot" is the frying temperature's question in the
           # words people use for it, and that card answers it with the number and the bread
           # cube. This row takes the vessels and the shapes that card has no line for - the
           # griddle, and "when is the pan ready", and how long the heat takes.
           "pan is hot", "wok is hot", "test the pan heat",
           # this row answers how to tell a dry pan has come up to heat, and with `bias=5` it was
           # taking every hot-pan line that named a surface or a mark as well: "can i put a hot pan
           # on the worktop", "the hot pan left a mark on the worktop" and "my hot pan scorched the
           # counter" were all told to hold a hand an inch above the pan. The surface the pan can
           # go down on, the mark it leaves, and the water it meets are three other rows. The
           # cracked and cold-water halves of this fence are already here, from the same round.
           "worktop", "worktops", "counter", "countertop", "work surface", "worksurface",
           "benchtop", "the table", "wooden table", "wood table", "the side", "on the side",
           "chopping board", "wooden board", "bread board", "trivet", "granite", "quartz",
           "marble", "laminate", "glass table", "stone worktop",
           "mark", "marks", "marked", "scorch", "scorched", "scorching", "stain", "stains",
           "stained", "white mark", "burn mark", "burnt the", "melted the",
           # "can i put a hot pan in cold water" has the pan and the heat in both its halves, and
           # it is not asking how to tell the pan is hot: it is asking what the cold water does to
           # it. The card that answers that already exists ("give a very hot pan five minutes
           # before it meets cold water") and this row's bias of 5 was beating it to the line.
           # "under the tap" and "rinse it" are left out on purpose: without them the tap line
           # still reaches this row, and with them it reached the cistern's isolation valve.
           "cold water", "in water", "in the sink", "dunk", "dunking", "quench",
           "warp", "warped", "warping", "crack", "cracks", "cracked",
           "cool down", "cool the pan", "soak", "soaking"),
    # the frying-temperature row keys "pan" and "hot" as well, and it answers a pan with oil in
    # it: "how do i know the pan is hot" and "how do i know when the pan is ready" are about a
    # dry pan, so this row takes them
    bias=5))

# "pan first or oil first" and "oil first or pan first" are the same question, and main gave them
# opposite answers: "Pan first - that's the one I'd take, and either is fine" and "Oil first - ..."
# The choice card says the bot has no taste, which is right about a curry and wrong about this: a
# dry pan cannot be judged for heat and cold oil on a cold pan heats unevenly, so there is an
# answer. Both spellings reach it, and the card that used to coin-flip them stands down because
# the row scores higher than it.
_ORDER_ASK = re.compile(
    r"\b(?:pan|pans|wok|griddle|skillet|frying pan)\b[^.?!]{0,24}\bfirst\b"
    r"|\bfirst\b[^.?!]{0,24}\b(?:pan|oil|butter|fat)\b"
    r"|\bwhich\s+(?:one\s+)?first\b|\bpan\s+first\b|\boil\s+first\b", re.I)

ENTRIES.append(entry(
    "pan-then-oil",
    (("pan", "pans", "wok", "griddle", "skillet", "frying pan", "hot pan", "cold pan"),
     ("first", "which first", "pan first", "oil first", "butter first", "one first",
      "heat the pan", "heat the oil", "hot pan")),
    ("Pan first, then the oil. A dry pan heats evenly and you can judge its heat with your hand "
     "or a drop of water, and oil added to a pan that is already hot shimmers and moves at once "
     "instead of sitting in a cold pool. The exception is a marinade, a rub or a cold steak "
     "straight from the fridge, which goes into the hot oil rather than the bare pan."),
    # the smoke point, the shelf life of used oil and the sauce question are other rows'
    avoid=("smoke", "smoking", "smoke point", "keep", "keeps", "store", "storing", "reuse",
           "reusing", "throw away", "get rid", "dispose", "drain", "oven", "air fryer",
           "first time", "my first", "first go", "first aid", "first birthday", "panini"),
    guard=lambda understood: bool(_ORDER_ASK.search(
        " " + str((understood or {}).get("clean") or "").lower() + " ")),
    bias=6))
# A razor clam is a shellfish, and the only places the word "razor" reached were the shaving
# rows: "how do i cook razor clams" was answered "Warm the hair first - a shower or a flannel",
# then, once the shaving rows stood down, the mussel safety card ("Tap each mussel"). They are
# like a clam with a straight shell, so they want the sand out and four minutes of steam, and
# there is no beard to pull.
# A herb somebody is growing is a herb they have too much of, and the pantry answered neither
# half: "i have a rosemary bush what can i cook" was the ten-minute dinner list, "i have a mint
# plant what can i cook" was how to buy a mint plant, and "i have too much rosemary what can i
# cook" was the card about cooling leftovers fast. The picking is the part a plant adds, and the
# rest of the answer is the herb's own - at the start for a woody one, at the end for a soft one.
_HERBS_GROWING = ("rosemary", "thyme", "sage", "bay", "bay leaf", "bay leaves", "oregano",
                  "mint", "basil", "coriander", "cilantro", "parsley", "dill", "chives",
                  "tarragon", "herb", "herbs")
# Only the words for something that is still in the ground: a surplus of cut herbs is the
# pantry rows' line ("i have too much mint", "what can i cook with thyme"), and this row is the
# plant's own question, so a line without a plant in it never reaches it.
_HERB_PLANT_WORDS = ("plant", "plants", "bush", "bushes", "tree", "pot", "pots", "flowerpot",
                     "herb pot", "patio", "window box", "garden", "allotment", "sprouting",
                     "come back", "coming back", "gone mad", "running riot", "taken over")
# A herb in the ground is only this row's question when the line also asks what to do with it:
# a plant word on its own is the garden's ("when do i plant basil", "my mint has taken over the
# garden", "do herbs come back every year" were all answered "Pinch the top few leaves" before
# this check, over four green garden tests).
_HERB_USE_ASK = ("cook", "cooked", "cooking", "use", "uses", "using", "do with", "make", "made",
                 "making", "recipe", "recipes", "eat", "eating", "salad", "sauce", "pesto",
                 "stuffing", "roast", "roasting", "grill", "grilling", "bake", "baking")
# A glut is the same question as a plant: "i have too much rosemary what can i cook" was the
# ten-minute dinner list, while "i have a rosemary bush what can i cook" reached this row. The
# cooking ask has to be in the line as well, so a plain "i have too much mint" stays the pantry's.
_HERB_SURPLUS_WORDS = ("too much", "too many", "lots of", "loads of", "a lot of", "so much",
                       "plenty of", "glut", "glut of", "overgrown", "surplus")
_WOODY_HERB = frozenset(("rosemary", "thyme", "sage", "bay", "oregano"))


_HERB_OWNED = re.compile(r"\b(?:have|has|having|got|there's|there is|bought|given|gave)\b",
                         re.I)


def _herb_use_asked(understood):
    """True when the line asks for a use, or says the plant is theirs: "i have a sage bush" is
    a person holding a herb they do not know what to do with, and "Noted: you have a sage bush"
    is not an answer. A line about growing one or a fault in it is the garden's, and those
    words are in this row's avoid list, so they never arrive here."""
    clean = " " + str((understood or {}).get("clean") or "").lower() + " "
    words = set(str(word).lower() for word in (understood or {}).get("words") or ())
    if words & set(_HERB_USE_ASK):
        return True
    if any(" " + word + " " in clean for word in _HERB_USE_ASK):
        return True
    # a glut of cut herbs is the pantry's ("i have too much mint" is the soft-herb card), so
    # the possession shape only counts when something growing is named
    if not any(" " + word + " " in clean for word in _HERB_PLANT_WORDS):
        return False
    return bool(_HERB_OWNED.search(clean))


def _herb_plant_reply(memory, understood):
    """The picking and the herb's own use - woody at the start of the cooking, soft at the end.
    When the line asked what to cook, the cooking comes first."""
    words = set(str(word).lower() for word in (understood or {}).get("words") or ())
    clean = " " + str((understood or {}).get("clean") or "").lower() + " "
    woody = bool(words & _WOODY_HERB) or any(" " + herb + " " in clean for herb in _WOODY_HERB)
    if woody:
        use = ("Use them at the start of the cooking, because heat is what opens them up: "
               "rosemary or thyme with potatoes, lamb, chicken or a tray of vegetables, sage "
               "with pork or in a brown butter, and a bay leaf in rice or a stew.")
        pick = ("Take a few sprigs from the tips rather than cutting back to the old wood, and a "
                "third off the top is the most a bush wants at once - it grows back from there. ")
    else:
        use = ("Use them at the end, off the heat, so the flavour stays - chopped into a green "
               "sauce with oil, lemon and garlic, torn over tomatoes or fish, or stirred into a "
               "soup just before it is served.")
        pick = ("Pinch the top few leaves and leave the stem, and the plant keeps going: a third "
                "off the top is plenty at once, and it grows back from the cuts. ")
    # a line that asks what to cook wants the cooking first; a line about the plant itself
    # ("look at the state of this bush") wants the picking first
    if _herb_use_asked(understood):
        return use + " " + pick.strip()
    return pick + use


ENTRIES.append(entry(
    "herb-plant-to-cook",
    (_HERBS_GROWING, _HERB_PLANT_WORDS + _HERB_SURPLUS_WORDS),
    _herb_plant_reply,
    bias=3,
    guard=_herb_use_asked,
    # a herb with something wrong with it is the garden's question, and so is growing one:
    # "how do i grow rosemary", "why is my basil wilting" and "how do i take basil cuttings"
    # keep the rows they had before this one.
    avoid=("grow", "grows", "growing", "grew", "propagate", "propagating", "seed", "seeds",
           "sow", "sowing", "cutting", "cuttings", "repot", "repotting", "potting", "wilt",
           "wilting", "wilts", "yellow", "yellowing", "brown", "dying", "died", "dead", "die",
           "prune", "pruning", "fertiliser", "fertilizer", "feed", "pests", "pest", "aphids",
           "frost", "winter", "indoor", "indoors", "sunlight", "shade", "soil", "compost",
           "buy", "where can i buy", "how do i keep", "keep it alive", "overwinter",
           "plugs", "seeds",
           # a plant that has run wild is the garden's question, not a supply of herbs:
           # "my mint has taken over the garden" was "Pinch the top few leaves"
           "taken over", "take over", "taking over", "come back", "comes back", "coming back",
           "gone mad", "going mad", "running riot", "overgrown", "spreading", "spreads",
           "spread", "invasive", "taking hold",
           # whether a herb is safe to eat is not whether it wants picking: "can i eat mint
           # from the garden" was a how-to-prune card, and a food-safety question deserves the
           # answer it had rather than the picking one
           "safe", "unsafe", "can i eat", "is it safe", "dogs", "dog", "cats", "cat",
           "poison", "poisonous", "toxic", "pesticide", "pesticides", "kids", "toddler")))


ENTRIES.append(entry(
    "razor-clams",
    # Only the razor spellings: plain "clams that are open" is the shellfish safety row's
    # question, and this card took it while the plain clam words were in this key.
    (("razor clam", "razor clams", "razor shell", "razor shells", "razor fish", "razorfish"),
     ("cook", "cooking", "prepare", "clean", "cleaning", "steam", "steaming", "grill",
      "grilling", "how do i", "how to", "what do i do", "eat", "serve", "recipe", "best way",
      "open", "shut", "sand", "grit")),
    ("Rinse them under cold water and leave them an hour in salty water so they spit out the "
     "sand, then steam or grill them for about four minutes, until the shells open. They have no "
     "beard to pull like a mussel, and any that will not open go in the bin. Garlic, chilli, "
     "lemon and parsley is all they need."),
    avoid=("shave", "shaving", "shaved", "blade", "blades", "burn", "bumps", "razor burn",
           "beard", "beard trimmer", "hair removal", "wax", "waxing", "razor blade")))


# --- measuring, and reading the recipe in front of you ----------------------
def _lined(memory, understood):
    """The words the person typed, cleaned, with a space at each end."""
    return " " + " ".join(
        str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower().split()
    ) + " "


# What a cup of each ingredient weighs, and the one thing to know about measuring it. The person
# asked about the ingredient they named, so the reply opens on that ingredient: a card that opens
# "spoon the flour into the cup" is the wrong first sentence for "how do i measure butter", and
# the earlier version of this row answered butter, sugar and rice with it because it keyed the
# asking rather than the thing asked about.
_CUP_OF = (
    ("flour", "plain flour", "self raising flour", "self-raising flour", "bread flour",
     "spelt", "wholemeal",
     "Spoon the flour into the cup and level it off with a knife - a scoop straight from the bag "
     "packs in up to a fifth more, which is the difference between a light cake and a heavy one. "
     "A cup of plain flour is about 120g, and a level tablespoon about 8g."),
    ("sugar", "caster sugar", "granulated", "brown sugar", "icing sugar", "muscovado",
     "Spoon white sugar into the cup and level it, and pack brown sugar down hard. A cup of caster "
     "or granulated sugar is about 200g, a cup of icing sugar about 120g, and a level tablespoon "
     "of caster sugar about 12g."),
    ("butter", "margarine", "lard", "shortening",
     "Butter is easiest by weight: a cup is about 225g, a stick about 113g, a level tablespoon "
     "about 14g. If you have a block in its wrapper, the paper is marked in 25g lines - cut on "
     "them and there is nothing to wash up. Soften it first, or it will not cream evenly."),
    ("oats", "porridge oats", "rolled oats",
     "A cup of rolled oats is about 90g, and 50g a person is a portion of porridge. Spoon them in "
     "and level rather than pressing them down, because oats settle and a packed cup can weigh half "
     "again as much."),
    ("cocoa", "cocoa powder",
     "A cup of cocoa powder is about 85g, and it is the one ingredient that really does want "
     "spooning and levelling: cocoa compacts badly and a scooped cup can be a third heavier."),
    ("honey", "syrup", "golden syrup", "treacle", "molasses",
     "Honey and syrup are measured in a jug at eye level, not a cup, because they do not settle "
     "flat - a cup of honey is about 340g. Warm the spoon or the jug in hot water first and it "
     "will run out clean."),
    ("milk", "water", "oil", "buttermilk",
     "Liquids go in a jug on the worktop, read at eye level with the jug standing still - a cup "
     "of milk or water is 240ml and a cup of oil about 225ml."),
)

# "how do i measure rice" keeps the rice card on main, which answers it with the rinse and the
# one-mug-to-one-and-a-half, so this row stands down on rice rather than replacing a good answer
# with a flour paragraph.
_MEASURE_AWAY = ("rice", "basmati", "risotto", "pasta", "spaghetti", "noodles", "couscous",
                 "quinoa", "porridge", "soup", "gravy", "stock")


# The half of the answer that holds whatever the ingredient was: no scales, one mug, and why the
# cup is the weak measure it is. It is also the whole answer for a line that names no ingredient
# ("how do i measure ingredients"), which the earlier version of this row left on the hedge.
_MEASURING_TAIL = (
    "Spoon it into the cup and level it rather than scooping from the bag, because a cup is a "
    "volume and how much it holds depends on how the ingredient went in. With no scales at all, "
    "use one mug for everything in the recipe - the proportions matter more than the exact weight.")


def _measuring(memory, understood):
    line = _lined(memory, understood)
    if any(re.search(r"\b" + re.escape(w) + r"\b", line) for w in _MEASURE_AWAY):
        return None
    for words in _CUP_OF:
        for word in words[:-1]:
            if re.search(r"\b" + re.escape(word) + r"\b", line):
                return words[-1] + " " + _MEASURING_TAIL
    return _MEASURING_TAIL


# The terms a recipe uses, each of which is its own one-sentence answer. Leading with the term the
# line names is the whole point: "what does divided mean in a recipe" was answered with a
# paragraph in which the word 'divided' was the third item, and the person asked for the term.
_RECIPE_TERM = (
    (("divided", "divide", "half in the sauce", "reserve"),
     r"\bdivid(?:ed|e)\b",
     "'Divided' means the amount is split between stages: half the cheese in the sauce and half on "
     "top, or the butter half in the cake and half in the icing. Weigh or measure the whole lot "
     "out and set the second part aside in a bowl before you start, or it is easy to tip it all "
     "in at once."),
    (("until", "cue", "how do i know when it is done"),
     r"\buntil\b",
     "'Until' is a cue, not a time: until golden, until it comes away from the pan, until a "
     "skewer comes out clean. The recipe gives you the sign to look for because the clock cannot - "
     "ovens and tins differ - so trust your eyes and nose first and the timer second."),
    (("mise en place", "prep", "prepped", "prep ahead"),
     r"\bmise en place\b|\bprep\b",
     "Mise en place is everything weighed, chopped and set out in bowls before you turn the heat "
     "on - the French for 'in place'. It is the whole trick of the last five minutes of a recipe: "
     "most dishes go wrong there because the onion was not chopped yet. Read the ingredients as a "
     "shopping-and-chopping list and do all of it first."),
    (("cup", "cups", "what is a cup"),
     r"\bcups?\b",
     "A cup in a recipe is a volume: 240ml, or 8 US fluid ounces, which is a bit over half a pint. "
     "Most British recipes weigh in grams instead and a British teacup is not a US cup, so a "
     "recipe that says cups is written in American measures - and a cup of flour is about 120g, a "
     "cup of sugar about 200g."),
    (("serves", "makes", "how many does it serve"),
     r"\bserves\b|\bmakes\b|\bhow many\b",
     "'Serves four' usually means four as a main with something alongside, and the number is a "
     "guide rather than a promise - a hungry four will finish a dish written for six. Halve or "
     "double the weights if your table is smaller or bigger, and keep the tin size and the time "
     "in mind when you do."),
)


def _the_recipe_term(memory, understood):
    line = _lined(memory, understood)
    for words in _RECIPE_TERM:
        if re.search(words[1], line):
            return words[2]
    return None



# "how do i measure flour" was the honest fallback and "what does divided mean in a recipe" was
# answered with long division: the cooking half of a measuring or a recipe-reading question had
# nothing to reach. Three cards, because they are three jobs: measuring, reading, scaling.
ENTRIES.append(entry(
    "measure-ingredients",
    (("measure flour", "measuring flour", "weigh flour", "measure out flour",
      "measure sugar", "measuring sugar", "measure butter", "weigh butter",
      "measure with cups", "measuring cups", "cup measure", "cups to grams",
      "grams to cups", "measure ingredients", "measuring ingredients",
      "weigh ingredients", "weighing ingredients", "kitchen scales", "digital scales",
      "measure oil", "measure milk", "measure oats", "measure cocoa",
      "measure syrup", "measure honey", "ounces to grams", "oz to grams"),
     ("how do i", "how to", "how much", "what is", "weigh", "weighing", "measure",
      "measuring", "convert", "grams", "cups", "ounces", "oz", "accurate", "properly",
      "right", "best way", "scoop")),
    _measuring,
    # a blood sugar question and a portion-size question are two other answers
    # "how do i measure ingredients without scales" already has a card full of mug and spoon
    # weights, and it is the better answer to that line, so this row leaves it alone.
    avoid=("without scales", "no scales", "no weighing", "mug", "mugs",
           # rice, pasta and porridge have their own cards, and main's rice answer is the better
           # one for "how do i measure rice": a cup of rice is a cooking question, not a baking one
           "rice", "basmati", "risotto", "pasta", "spaghetti", "noodles", "couscous", "quinoa",
           "porridge",
           "blood sugar", "diabetes", "diabetic", "insulin", "sugar intake", "how much sugar",
           "added sugar", "cut down on sugar", "sugar free", "portion", "portion size",
           "how many calories", "calories in", "protein", "carbs", "weight loss",
           "lose weight", "diet", "weigh myself", "bathroom scales", "scale says")))

ENTRIES.append(entry(
    "read-a-recipe",
    (("read a recipe", "read the recipe", "follow a recipe", "following a recipe",
      "reading a recipe", "recipe card", "recipe says", "recipe mean", "recipe means",
      "recipe tells", "in a recipe", "on a recipe", "understand a recipe",
      "how do recipes work", "recipe instructions", "mise en place", "prep ahead"),
     ("how do i", "how to", "understand", "read", "reading", "follow", "following",
      "mean", "means", "divided", "until", "prep", "prep time", "serves", "makes",
      "what does", "what is", "whats", "what's", "explain", "trick", "tips", "first")),
    lambda memory, understood: _the_recipe_term(memory, understood) or (
     "Read it twice, all the way through, before you touch anything: what it serves, the prep "
     "time and the cooking time separately, the oven setting, and whether anything has to chill, "
     "soak or rest. Then get every ingredient out and cut up, which is what the French call mise "
     "en place - most recipes go wrong in the last five minutes because the onion was not chopped "
     "yet. Two phrases to know: 'divided' means the amount is split between stages (half the "
     "cheese in the sauce, half on top), and 'until' is a cue rather than a time - until golden, "
     "until it comes away from the pan. Times in a recipe are for that oven and that tin; trust "
     "your eyes and nose first. Check the tin size too, because a wrong-sized tin changes the "
     "depth and with it the time."),
    # long division, a recipe to eat out of, and a dish are other answers
    avoid=("divide", "division", "divided by", "vitamin", "nutrition", "calories",
           "slimming", "restaurant", "takeaway", "meal plan", "meal idea", "what should i cook",
           "dinner idea")))

# Its own id: `bot/knowledge/cooking.py` already holds a `halve-a-recipe` row, the short one that
# says halve every ingredient and leave the oven alone. This row covers the lines that row does
# not reach - "how do i make half", "times the recipe", "how do i scale the recipe for 4 to 6" -
# and two rows under one id leave `tests.test_ids_are_unique` red on main (#7573, after #9126).
ENTRIES.append(entry(
    "halve-a-batch-keep-the-tin",
    (("halve a recipe", "halving a recipe", "half the recipe", "half a recipe",
      "double a recipe", "doubling a recipe", "scale a recipe", "scaling a recipe",
      "smaller batch", "bigger batch", "recipe for two", "recipe for one",
      "make half", "make double", "times the recipe"),
     ("how do i", "how to", "can i", "is it", "do i", "times", "oven", "tin", "pan",
      "same", "longer", "shorter", "easier")),
    ("Halve the weights but not quite everything: salt, spices and strong flavours go a little "
     "under half, because they do not scale with the rest, and a raising agent like baking powder "
     "goes to about three quarters of half, or the bake tastes of it. An egg is the awkward one, "
     "so weigh it beaten and use half by weight - about 25g of a large egg. The tin matters more "
     "than the time: half the batter in the same tin is a shallow cake that bakes fast and dries, "
     "so use a smaller tin and check it early rather than turning the oven down. Doubling is the "
     "same in reverse: double the tin's volume, not its width, or bake in two tins."),
    avoid=("half a portion", "half the price", "half price", "half of it", "freeze",
           "leftovers", "keep", "store", "reheat", "calories", "guests", "party")))

# "what can i bake with kids" and "how do i bake with my kids" were both "That's beyond what I
# know well, sorry", and "easy things to bake with children" was "Got it. Is there anything you'd
# like a hand with?".
entry_bake_with_children = entry(
    "bake-with-children",
    # The garden's "baking hot border" row keys "baking" and "what can i", so a line that asks
    # what to bake in the request frame went to the sunny border: "what can i bake with kids" was
    # a list of lavender and salvia. The request words are part of the subject here.
    # Only baking words ask this question. `cook`, `cooking` and `make` are the evening meal:
    # "what can i cook for my family" already gets "Kids, about 15 minutes: pasta with butter and
    # cheese, fish fingers", and that is the answer that person wants.
    (("bake", "baking", "what can i bake", "what should i bake", "what to bake", "what can we bake",
      "things to bake", "bake with kids", "bake with my kids", "bake with children",
      "bake with the kids", "baking with kids", "baking with children", "easy bake"),
     ("kids", "kid", "children", "child", "toddler", "grandchildren", "family", "my son",
      "my daughter", "with my kids", "with children", "with kids")),
    "Three that work with children, easiest first: flapjack (no oven hands, just stirring and a "
    "flat tin), fairy cakes (they can fill the cases and ice them once cool) and shortbread "
    "(three ingredients, and cutting shapes is the fun part). Give the little ones the measuring "
    "and the stirring and keep the oven and the hob to yourself, and expect it to take twice as "
    "long as it would alone.",
    # baking a cake for someone is a different question, and so is a bake that failed
    avoid=("birthday", "went wrong", "sank", "flat", "burnt", "burned", "raw", "soggy", "vegan",
           "gluten", "dairy", "calories"),
    bias=3)
ENTRIES.append(entry_bake_with_children)

# "what can i bake with the kids" then "they are 5 and 7" then "anything without too much mess" -
# the third line names no baking of its own and leaned on the first, and main answered it with the
# quick-tea card ("Kids, about 15 minutes: pasta..."). The children's card answers the first two
# and this one is a question about the mess, so it is keyed on the mess words, and the baking or
# the children can come from the line or from the line it leans on (lookup.find searches that when
# the typed line reaches nothing).
entry_bake_nothing_messy = entry(
    "bake-nothing-messy",
    (("mess", "messy", "messing", "mess-free", "no mess", "less mess", "much mess", "too much mess",
      "messiest", "minimal mess", "cleaning up", "clean up", "clear up", "clearing up",
      "washing up", "wash up", "one bowl", "fuss", "faff"),
     ("bake", "baking", "baked", "kids", "kid", "children", "child", "toddler", "grandchildren",
      "with the kids", "with kids", "with children", "cook", "cooking", "recipe",
      "recipes", "ingredients",
      # "kitchen" used to be here and it was a place standing in for a job: "my kitchen is a
      # mess" and "the kitchen is a mess" are statements about a room, and they were answered
      # with the least-messy-bakes list because the room and the mess were the row's only two
      # signals. A place is not a job, so the row now wants the baking or the cooking itself -
      # "what can i bake with the kids", "any recipes that wont make a mess", "things to cook
      # with no washing up" all still reach it, and the room's state reaches the tidying row.
      )),
    "The least messy bakes are the ones with one bowl and no icing: a no-bake fridge cake "
    "(melted chocolate and butter, crushed biscuits, into a lined tin, an hour in the fridge), "
    "flapjack (one pan on the hob, one lined tin) and rocky road, which is the same thing with "
    "marshmallows. Shortbread and gingerbread shapes are tidy because the dough is stiff, and "
    "drop scones or pancakes make the mess in one jug. Three things that keep it small: weigh the "
    "ingredients out before anyone is called in, stand the bowl on a tray with the bin beside it, "
    "and line the tin with a sheet that overhangs so the whole bake lifts out.",
    # the floor, the paint and the glitter are other cards' mess
    # a kitchen that is a mess *after* baking is the tidying card's, and this row is only ever
    # asked what to make: "my kitchen is a mess after baking" was the tidying answer on main and
    # must keep it
    avoid=("floor", "kitchen floor", "paint", "painting", "glitter", "playdough", "play dough",
           "sand", "mud", "garden", "house", "room", "bedroom", "car", "iron", "hoover",
           "washing machine", "laundry", "dishes", "grease", "burnt on", "after baking",
           "mess after", "clean the kitchen", "cleaning the kitchen", "tidy the kitchen",
           "tidy up", "wipe", "clear the kitchen", "clear away", "sink full"),
    bias=2)
ENTRIES.append(entry_bake_nothing_messy)

# The other direction of the powder swap. "can i substitute baking powder for baking soda" is the
# easy one and main answered it with the comparison ("Baking soda is pure bicarbonate..."); the
# swap verdict underneath opens with the other direction ("bicarbonate in place of baking powder"),
# so the one line that asks this way got told how to use the wrong powder. The direction is a
# reading of the line, not a word, so it is a guard: powder before the swap word and soda after it.
_POWDER_FOR_SODA = re.compile(
    r"\bbaking powder\b[^.?!]{0,24}?\b(?:instead of|in place of|for|substitute for|replace|"
    r"swap for|swap with)\b[^.?!]{0,16}?\b(?:baking soda|bicarbonate|bicarb|soda)\b", re.I)


def _powder_goes_in_for_soda(understood):
    read = understood if isinstance(understood, dict) else {}
    text = " " + str(read.get("clean") or read.get("text") or "").lower() + " "
    return bool(_POWDER_FOR_SODA.search(text))


entry_powder_for_soda = entry(
    "powder-in-place-of-soda",
    (("baking powder", "powder"),
     ("bicarbonate of soda", "bicarb", "baking soda", "soda"),
     ("instead of", "in place of", "for", "substitute", "replacement", "replace", "swap",
      "swapping", "use", "using", "can i", "could i")),
    "Use about three teaspoons of baking powder for each teaspoon of baking soda, and put the "
    "acid the recipe counted on - buttermilk, yoghurt, lemon juice - in some other way, or the "
    "rise goes flat. That is the easy direction, because baking powder already carries its own "
    "acid. The other way round is not a straight swap: bicarbonate is about four times stronger "
    "and needs an acid to work, so a quarter of a teaspoon with a teaspoon of lemon juice or "
    "vinegar stands in for each teaspoon of powder.",
    # the comparison, the identity and the "what is it" questions are other rows'
    avoid=("difference", "different", "same", "vs", "versus", "what is baking powder",
           "what is bicarbonate", "soapy", "tastes of soap", "what does it do", "why do i need"),
    guard=_powder_goes_in_for_soda,
    bias=3)
ENTRIES.append(entry_powder_for_soda)

# --- a fault in the food that no row was watching --------------------------------------
# Four asks off a typed sweep, each landing on a card about something else or on a nod.
ENTRIES.append(entry(
    "pizza-base-soggy",
    (("pizza", "pizza base", "pizza bases", "pizza dough", "margherita"),
     ("soggy", "soggy bottom", "wet", "limp", "not crisp", "not crispy", "doughy in the middle",
      "raw in the middle", "went soggy", "goes soggy", "stodgy")),
    "A soggy pizza is three things at once: a cool oven, a thin tray and a wet topping. Heat the "
     "oven and the tray to its top setting for 20 minutes, roll the base thin and put it onto the "
     "hot tray, drain the mozzarella and pat any vegetables dry, and keep the sauce to a thin "
     "layer. Bake it high for 10 to 12 minutes, then finish it under the grill for a minute.",
     # the dough recipe, the takeaway, the frozen one and the calories are other rows
     avoid=("recipe", "how do i make dough", "how do i make pizza dough", "dough recipe",
            "flour", "yeast", "takeaway", "delivery", "order", "frozen", "calories",
            "healthy", "how long does it", "freeze"),
     # the dough recipe has "pizza" and "base" in its key and answered the soggy one
     bias=2))

ENTRIES.append(entry(
    "raw-flour-taste",
    (("floury", "tastes of flour", "tastes floury", "raw flour", "raw flour taste",
      "chalky", "tastes like flour", "flour taste", "powdery taste"),
     # "tastes", "taste", "why" and "how do i" used to be here and they were not a subject at all:
     # every line with a floury word in it matched, so "my potatoes taste floury" got the raw-flour
     # sauce card and so did "the flour tastes old". What the answer is about is the sauce, so the
     # sauce words are the second group, and the flour itself is fenced off below.
     ("sauce", "gravy", "soup", "stew", "curry", "roux", "white sauce", "cheese sauce",
      "casserole", "pie filling", "get rid of", "floury taste", "why does",
      "why is my sauce", "why has my sauce")),
    "A floury taste means the flour is still raw, and the fix is time on the heat, not more "
     "seasoning: simmer it 5 to 10 minutes longer, stirring, so the starch cooks through and "
     "loses the raw edge. A roux wants 2 or 3 minutes of bubbling before any liquid goes in, and "
     "if the sauce is already made, a splash of stock and a slow simmer takes it out. Milk, "
     "butter or cream rounds off what is left.",
     avoid=("bread", "bake", "cake", "batter", "pancake", "flourless", "which flour",
            "what flour", "how much flour", "grams", "cup", "self raising", "plain flour",
            # a floury potato is a kind of potato and a flour that tastes old has gone off: both
            # used to land here because "tastes" matched, and neither is a raw sauce
            "potato", "potatoes", "spud", "spuds", "old", "gone off", "off", "smell", "smells",
            "smelling", "musty", "rancid", "stale", "keep", "keeps", "last", "lasts")))

ENTRIES.append(entry(
    "metallic-taste-in-food",
    (("metallic", "metal", "tastes of metal", "taste of metal", "tastes metallic"),
     ("rice", "soup", "sauce", "stew", "pasta", "teapot", "tea", "water", "food", "dish",
      "curry", "pan", "kettle", "cook", "cooked", "boiled")),
    "A metal taste in food is usually the pan or the water rather than the food: an unlined "
     "aluminium or cast-iron pan with anything acidic, a metal spoon left in a tomato sauce, or "
     "a furred-up kettle. Cook acidic dishes in stainless steel, enamel or non-stick, move "
     "leftovers out of the pan into glass or plastic, and descale the kettle with a 50/50 mix of "
     "water and white vinegar.",
     avoid=("mouth", "in my mouth", "gum", "gums", "dentist", "medicine", "pregnant",
            "pregnancy", "sinus", "blood", "iron tablet", "coins", "coin", "pipe",
            # a kettle that tastes of metal has its own descaling answer, and it is the better one
            "my kettle", "the kettle", "kettle tastes", "kettle smells", "from the kettle"),
     # the mouth-and-gums card shares "metallic" and "taste", and won the food lines
     bias=2))

# A burger that will not hold together is the binding and the handling, and it is a kitchen fault
# with a kitchen answer - on main it was answered by the composer's "Nice one. How did the rest
# of it go?", which congratulates somebody whose dinner has just fallen into the pan.
BURGER_APART = ("fell apart", "falling apart", "falls apart", "fall apart", "broke up",
                "breaking up", "breaks up", "crumbled", "crumbling", "crumbles", "wont hold",
                "won't hold", "not holding", "holds together", "hold together",
                "went to pieces", "slid apart", "disintegrated")
BURGER_APART_REPLY = (
    "It falls apart for three reasons: the mince is too lean, it was handled too much, or "
    "it was turned before it had a crust. Use mince with some fat in it (20 per cent is right), "
    "break it up with a fork rather than squeezing it, and add an egg and a couple of spoons of "
    "breadcrumbs per 500g if the meat is lean - then shape it loosely, press a shallow dip in the "
    "middle and chill it 20 minutes so it sets. Salt it just before it goes in the pan, cook it "
    "in a hot pan and leave it alone for 3 minutes before the first turn, and it will hold."
    .replace("a egg", "an egg"))


ENTRIES.append(entry(
    "burger-fell-apart",
    # the plural is left to the burger row in cooking.py, which already answers "my burgers fall
    # apart in the pan" well: what this row is for is the singular and the other minced-meat
    # shapes, where the composer was congratulating somebody whose dinner had just collapsed
    (("burger", "patty", "patties", "beefburger",
      "meatball", "meatballs", "meatloaf", "kofta", "koftas", "frikadellen"),
     BURGER_APART),
    BURGER_APART_REPLY,
    # the plural is the burger row's, and only the plural: "burgers" here does not fence the
    # singular out of the row, which is the line this row was built for
    avoid=("how do i make", "recipe", "best burger", "veggie", "vegan", "bean burger",
           "tofu", "bun", "buns", "sauce", "cheese slice", "restaurant", "takeaway"),
    bias=1))

# --- a meal for the situation the line describes -------------------------------------------
# A line that says the situation and then asks what to cook was answered about the situation:
# "my son has a football match saturday and its freezing, what should i feed him before" got the
# baby-room-temperature card, "im back at work monday after a year off with the baby, what should
# i take for lunch" got the exercise ramp-up, and "my back is bad and i cant stand long, what can
# i cook quickly" got the back-pain card. The ask at the end is the meal, so one table holds the
# meals: the situation picks which one, and each is a dish with the reason it suits.
#
# The situation words are what let this stand beside the ordinary dinner rows: a line with no
# situation in it ("what should i cook tonight") matches nothing here and keeps its own answer.
MEAL_SITUATIONS = (
    (("football match", "before a match", "before the match", "playing sport", "five a side",
      "swimming gala", "cross country", "sports day", "before training", "game tomorrow",
      "before football", "before rugby", "before a run", "before swimming",
      "rugby match", "netball match", "hockey match", "match tomorrow", "before the game",
      "before his match", "before her match", "match on saturday", "match on sunday",
      "football tomorrow", "swimming gala", "sports day"),
     "Feed them plain carbohydrate about three hours before, not straight before: a bowl of pasta "
     "with a little butter or cheese, a jacket potato, or toast and banana, plus water. Keep the "
     "fat and the fibre light so it is out of the stomach by kick-off, and have a banana or a "
     "flask of squash for after. A cold day wants a warm drink in a flask more than a bigger "
     "meal."),
    (("coeliac", "celiac", "gluten free", "gluten-free", "no gluten", "wheat allergy"),
     "Cook one dish that is gluten-free by nature rather than making a second version: chicken "
     "thighs roasted with potatoes and lemon, a chilli with rice, or a fish pie with a mashed "
     "top. Check the stock cube, the soy sauce and the sausages, because that is where the wheat "
     "hides, use a clean board, and put the bread in its own basket so nothing is cross-"
     "contaminated."),
    (("no oven", "oven is broken", "oven broke", "without an oven", "hob only", "just a hob",
      "oven is out", "no cooker", "microwave only", "moving house"),
     "Everything on the hob: pasta with a sauce made in the same pan, rice with a stir fry, "
     "tinned tomatoes with beans and eggs poached in them, or soup with bread. One pan and one "
     "hob ring is plenty if you add the pasta to the sauce with a ladle of its water, and a "
     "kettle fills in for hot water."),
    (("tight budget", "on a budget", "skint", "no money", "cheap meals", "cheap dinners",
      "money is tight", "cutting back", "cost of living"),
     "Build the week on eggs, lentils, beans, oats, frozen vegetables and chicken thighs: a "
     "lentil bolognese, a bean chilli, egg fried rice, a frittata and a soup covers five dinners "
     "for about the price of one takeaway. Frozen veg and tinned tomatoes cost less and waste "
     "less than fresh, and a whole chicken gives a roast plus a second meal from the carcass."),
    (("pregnant", "cant stand the smell", "can't stand the smell", "smell of cooking",
      "smells make me", "cooking makes me"),
     "Eat cold or barely cooked while the smell turns your stomach: sandwiches, cereal, yoghurt, "
     "fruit, cheese and crackers, or a plate of the dinner you cooked yesterday eaten cold. Cook "
     "once in the morning when the kitchen is fresher, open a window and use the extractor, and "
     "let somebody else do the frying - it is the smell of hot fat that carries."),
    (("chest infection", "no appetite", "lost my appetite", "recovering from flu", "got the flu",
      "been ill", "feeling ill", "off my food", "cant eat", "can't eat"),
     "Small and plain, eaten often: soup, toast, rice pudding, yoghurt, a banana, scrambled egg "
     "on a good day, and a drink beside you all day. Do not worry about a proper dinner while "
     "you are ill - calories and fluid are the job, and the appetite comes back with them."),
    (("my back", "back is bad", "bad back", "cant stand long", "can't stand for long",
      "standing hurts", "on my feet all day", "knee is bad", "cant stand up"),
     "One tray in the oven and one pot on the hob, done in about ten minutes of standing: "
     "chicken thighs or sausages with chopped veg and oil at 200C for 30 minutes, or a chilli "
     "you leave to simmer. Sit at the table to prep with everything within reach, use a stool at "
     "the hob, and cook double so tomorrow needs no standing at all."),
    (("camping", "in a tent", "in the tent", "no fridge", "campervan", "camper van",
      "festival", "no electricity"),
     "One pot, no fridge: pasta with tinned tomatoes, tinned beans and a chopped chorizo or a "
     "tin of tuna, or a curry from a jar with rice. Take food that keeps without cooling - tins, "
     "dried pasta, noodles, porridge oats, bread, hard cheese, apples - and a small gas ring "
     "plus matches in a plastic bag, because a wet night in a tent is when the cooking has to be "
     "simple."),
    (("packed lunch", "packed lunches", "take to work", "take for lunch", "lunch for work",
      "lunchbox", "lunch box", "back at work", "back to work", "school lunch", "dinner lady"),
     "Cook one extra portion of dinner and box it: rice, pasta or a grain with a protein and "
     "something sharp keeps a day in a cool bag and needs no microwave. If there is nothing "
     "left over, a flask of soup with bread, or a tub of couscous made with boiling water from a "
     "kettle and stirred with feta, tomato and herbs, takes five minutes the night before."),
    (("night shift", "night shifts", "eats at 3am", "at 3am", "works nights", "working nights",
      "night worker"),
     "Treat the shift as two meals: a proper one before you go in - rice, pasta or potato with "
     "protein and vegetables - then something light about two thirds of the way through, like a "
     "sandwich, yoghurt, fruit or cereal, rather than a full dinner at 3am. Heavy fat at that "
     "hour sits on the stomach and makes the last hours worse, and a flask of something warm "
     "helps more than coffee at the end of the shift."),
    (("pudding", "dessert", "to bring a cake", "bring a cake", "bring a dessert", "bbq",
      "barbecue", "pot luck", "bring something"),
     "Bring something that travels and needs no fridge: a lemon drizzle traybake, brownies, a "
     "fruit crumble in its dish, or an Eton mess carried as meringue, cream and fruit in three "
     "tubs to layer at the table. Cut it in the tin so it arrives whole, and take the serving "
     "spoon with you."),
    (("tiny kitchen", "no worktop", "small kitchen", "no space", "little space",
      "one hob ring", "no surface"),
     "One tray or one pan a night, prepped on a board balanced on the hob or the table: a "
     "traybake of chicken, potatoes and veg, a one-pot pasta where everything goes in together, "
     "or a stir fry chopped straight into the pan. Clear as you go so the board has a home, and "
     "cook double on the nights you have room, because the second meal needs no worktop at all."),
)
# What the line has to ask for: a meal, not a fact about the situation.
MEAL_ASK = ("what can i cook", "what can i make", "what should i cook", "what should i make",
            "what can we eat", "what shall i cook", "what shall i make", "what should i feed",
            "what can i feed", "what can i bring", "what should i bring", "what do i feed",
            "what do i cook", "what do i make", "what is quick", "whats quick", "what's quick",
            "what can i give", "what should i give", "what to cook", "what to make",
            "meal ideas", "dinner ideas", "what can i do for dinner", "what can i do for tea",
            "what should i take for lunch", "what do i take for lunch", "what to take for lunch",
            "what should i buy", "what do i buy", "what cake can i make", "what can i bake",
            "how do i prep", "prep a meal", "what should i eat", "what can i eat",
            "what should he eat", "what should she eat", "what should they eat")
# Diabetes is two questions and they were one row: "what can i bake for a diabetic" wants the
# low-sugar cake, and "my husband is diabetic what can i make for dinner" wanted a dinner and got
# the cake, because both are "what can i make" in this table. So the bake is its own row, keyed on
# the sweet the line names, and every other ask for a diabetic meal falls through to the plate
# rule in cooking.py - half the plate vegetables, a quarter protein, a quarter starch - which is
# the answer to the dinner. Nothing is banned for a diabetic, so this row is about the bake only.
DIABETES_WORDS = ("diabetic", "diabetics", "diabetes", "type 1", "type 2", "blood sugar",
                  "watching my sugar", "sugar free", "low sugar", "no sugar", "sugar diabetes")
SWEET_ASK = ("cake", "cakes", "bake", "baking", "biscuit", "biscuits", "pudding", "puddings",
             "dessert", "desserts", "something sweet", "sweet treat", "sweet things", "sweets",
             "sweetener", "sweeteners", "sugar substitute")
DIABETIC_BAKE = (
    "Bake something that is low in sugar by nature rather than swapping in sweeteners: an "
    "almond and olive oil cake, a carrot cake made with less sugar and more spice, or berries "
    "with cream and a little dark chocolate. Keep the portion small and have it after a meal "
    "rather than on its own, and put the fruit and the cream on the plate so the cake slice can "
    "be thinner.")
# A dinner that happens to mention sugar is a dinner, and a recipe ask is the cake row's.
# The meal is the other question and it is asked by naming a meal. "Recipe" was in this list and
# is not a meal: "diabetic birthday cake recipe" was handed to the tin-size row, which answers how
# big a tin a sponge needs, and a diabetic cake recipe is this row's own question. "How do i make"
# left with it, for the same reason - "how do i make a cake for a diabetic" is a bake.
_A_MEAL_IS_NAMED = ("dinner", "dinners", "supper", "lunch", "main meal", "main course")
# "Can she eat cake" and "is cake ok for a diabetic" name a cake but ask whether it is allowed,
# and the answer to that is that nothing is banned and the portion is what counts - the plate
# rule, not something to bake. The eating verb is what tells the two apart: "what cake can i make"
# is a bake, "can i eat cake" is not.
_ALLOWED_ASKS = ("is it ok", "is it okay", "is it alright", "allowed", "ok for", "okay for",
                 "bad for", "good for", "fine for", "suitable for")
_EATING_VERBS = (" eat ", " have ", " drink ")


def _asks_what_is_allowed(said):
    """True when the line asks whether a food is allowed rather than asking for a recipe."""
    if any(phrase in said for phrase in _ALLOWED_ASKS):
        return True
    if not any(verb in said for verb in _EATING_VERBS):
        return False
    return any(word in said for word in (" can ", " could ", " should ", " is ", " are "))


def _a_bake_is_the_ask(understood):
    """The row answers a sweet that is asked for, and stands aside for a meal or a permission.

    A guard rather than a reply that returns None: a row that matches and then declines takes the
    turn down with it, where a guard lets the row behind it answer - "can a diabetic eat cake" is
    the plate rule's, and it was the plate rule that answered it before.
    """
    said = " " + str((understood or {}).get("clean") or "").lower() + " "
    if any(" %s " % word in said for word in _A_MEAL_IS_NAMED):
        return False
    return not _asks_what_is_allowed(said)


ENTRIES.append(entry(
    "a-bake-for-a-diabetic", (DIABETES_WORDS, SWEET_ASK), DIABETIC_BAKE, bias=2,
    guard=_a_bake_is_the_ask))

MEAL_SITUATION_WORDS = tuple(word for words, _reply in MEAL_SITUATIONS for word in words)
MEAL_ASK_WORDS = tuple(" ".join(phrase.split()) for phrase in MEAL_ASK)


def _meal_for_the_situation(memory, understood):
    """The dinner the situation wants, or nothing when the line names no situation."""
    said = str((understood or {}).get("clean") or "").lower()
    if not any(phrase in said for phrase in MEAL_ASK_WORDS):
        return ""
    for words, reply in MEAL_SITUATIONS:
        if any(word in said for word in words):
            return reply
    return ""


ENTRIES.append(entry(
    "meal-for-the-situation",
    (MEAL_SITUATION_WORDS, MEAL_ASK),
    _meal_for_the_situation,
    # the fridge, the freezer, the oven and the illness with its own card are other answers, and
    # a line asking whether it is safe to eat something is not asking for a menu
    avoid=("gone off", "is it safe", "still ok", "eat the", "freezer broke", "nothing to eat",
           "should i eat", "how long does", "thaw", "defrost", "allergic", "allergy",
           "intolerant", "poisoning", "recipe for", "how do i make a"),
    bias=3))

# "Can i leave the sugar out of a cake" was a shrug ("That's beyond what I know well"), and the
# half of the same question - "can i halve the sugar" - went to the halve-a-recipe row, which
# scales a recipe rather than saying what the sugar was doing in it. Sugar is the one ingredient
# of a bake that people cut on purpose, and the amount it can lose differs by what is being
# baked, so it is its own row rather than an edit to the scaling one.
#
# The ask is what tells this apart from the other sugar lines: "how much sugar is in a can of
# coke", "is sugar bad for you" and "how much sugar in a cake recipe" all name sugar and none of
# them is asking to take it out. The cut words are the ask, and the foods are the key.
_BAKE_NAMED = ("cake", "cakes", "biscuit", "biscuits", "cookie", "cookies", "bun", "buns",
               "muffin", "muffins", "loaf", "loaves", "bread", "sponge", "brownie", "brownies",
               "flapjack", "flapjacks", "traybake", "tray bake", "pie", "crumble", "pudding",
               "frosting", "icing", "buttercream", "recipe", "recipes", "bake", "baking",
               "baked", "batter", "dough", "meringue", "scone", "scones", "shortbread",
               "cheesecake", "swiss roll", "madeira", "victoria sandwich", "tin", "tins",
               "oven", "frosting", "ganache", "dessert")


def _a_bake_is_named(understood):
    """True when the line names something being baked, so the sugar is in a recipe.

    "Can i leave the sugar out of a cake" is this row's line; "im trying to cut down on sugar",
    "should i give up sugar" and "how much sugar is in a can of coke" are the diet's and the
    drink's, and none of them names a bake at all.
    """
    said = understood.get("clean") if isinstance(understood, dict) else understood
    words = " " + str(said or "").lower() + " "
    return any((" " + name + " ") in words for name in _BAKE_NAMED)


ENTRIES.append(entry(
    "less-sugar-in-a-bake",
    (("sugar", "caster sugar", "granulated", "icing sugar", "brown sugar", "sweetener",
      "sweet"),
     ("less", "leave", "leaving", "leave out", "leaving out", "left out", "left",
      "take", "taking", "take out", "taking out", "cut", "cutting", "cut down",
      "cut the", "cut it", "reduce", "reducing", "halve", "halving", "half the", "omit",
      "skip", "skipping", "no sugar", "without sugar", "sugar free", "sugar-free",
      "too sweet", "less sweet", "not so sweet", "healthier", "healthy", "diet", "diabetic",
      "diabetes", "calories", "how little", "how much less")),
    "You can cut the sugar in most cakes and traybakes by a third to a half and still get a good "
     "bake, but not all of it: sugar keeps the crumb soft, browns the crust and holds the "
     "structure, so a cake with none bakes pale, dry and crumbly. Leave at least a quarter of "
     "what the recipe asks, add a splash of milk if the batter looks stiff, and eat it within a "
     "couple of days. Bread needs its teaspoon to get the yeast going, and jam and meringue are "
     "set by their sugar, so those cannot be cut.",
    # A line about cutting sugar *out of the diet* is not about a bake, and this row is: "im
    # trying to cut down on sugar" was answered with the cake card. The bake has to be named, and
    # a word for the eating is enough to rule it out.
    guard=lambda said: _a_bake_is_named(said),
    avoid=("how much sugar", "how many calories", "calories in", "coke", "cola", "fizzy",
           "cereal", "yoghurt", "yogurt", "juice", "squash", "energy drink", "bad for",
           "addictive", "teeth", "blood sugar", "insulin", "type 2", "type 1",
           # a recipe that is scaled is the halve-a-recipe row's line, and it answers the
           # amounts rather than what the sugar does
           "double", "doubling", "half the recipe", "for two tins", "two tins",
           # keeping and going off are other rows
           "keep", "keeps", "last", "lasts", "gone off", "fridge", "freeze"),
    # the scaling row keys "halve" and "cake" as well, and answers the amounts; a line that
    # names the sugar is asking what the sugar does, so the sugar row outranks it
    bias=5))

# A head count at your table is a cooking question, whether or not the line names a meal. The
# crowd row in cooking.py reads a table off a food noun or a cooking verb, so the commonest way
# of saying it - "we're having 12 people on saturday" - reached no row at all and was answered
# "Noted: you're having 12 people on saturday", the filing cabinet STYLE.md rules out. The number
# of people coming is the subject of the line, so the one-dish answer is the reply; nothing else
# in the bot reads a count of people as a thing to cook for. Rows that name a meal, a quantity
# ("how much food for 30") or a food fault keep their lines.
# What has to come after the number for it to be a table rather than a head count: people
# coming, a day, a meal, a party. "we've got 20 people in the office" and "12 people applied for
# the job" are the same number and not a dinner.
_TABLE_AHEAD = (
    r"(?=[^.?!]{0,30}?\b(?:coming|come|round|over|due|arriving|invited|tonight|tomorrow|"
    r"this\s+weekend|next\s+week|"
    r"for\s+(?:dinner|lunch|tea|supper|brunch|christmas|a\s+meal|the\s+meal|a\s+party|"
    r"a\s+buffet|a\s+barbecue|a\s+bbq|a\s+birthday|sat|sun|fri|mon|tue|wed|thu)|"
    r"at\s+(?:my|our|a|the)\s+(?:party|do|barbecue|bbq|dinner|table|wedding|reception)|"
    r"on\s+(?:sat|sun|fri|mon|tue|wed|thu)\w*))")

_A_TABLE_OF_PEOPLE = re.compile(
    # having / feeding / invited / catering for a number: the number is the table.
    r"\b(?:having|have\s+got|feeding|catering\s+for|invited|inviting|cooking\s+for|"
    r"making\s+food\s+for|supper\s+for|dinner\s+for|lunch\s+for|tea\s+for|"
    r"table\s+for|seats?\s+for)\s+(?:\d{1,3}|a\s+dozen|twenty|thirty|forty|fifty)\b"
    + _TABLE_AHEAD +
    # "12 people round on saturday": the count said as people, here for something.
    r"|\b(?:\d{1,3}|a\s+dozen|twenty|thirty|forty|fifty)\s+(?:people|guests|adults|folk|"
    r"of\s+us|grown\s*ups)\b" + _TABLE_AHEAD +
    # "having people over on saturday": the table said as people first, with no number, and the
    # day or the meal after it. Without that second half "what do i say to the people coming"
    # is a meeting, and the table row has no business in it.
    r"|\b(?:people|guests|adults)\s+(?:coming|round|over|due|arriving)\b" + _TABLE_AHEAD,
    re.I)

# A table announced is not a quantity question, a food fault or a diet one: those rows are
# narrower and keep their lines.
_NOT_A_TABLE = (
    "how much", "how many", "per head", "per person", "per guest", "amount", "quantity",
    "kilos", " kg", "grams", "portions", "portion", "how big a", "how large a",
    "poison", "poisoning", "hygiene", "allergy", "allergic", "reaction", "ill", "sick",
    "waste", "bin", "bins", "food bank", "dog food", "cat food", "pet food", "baby food",
    "fast food", "menu", "seating", "seat", "plates", "cutlery", "chairs", "parking",
    # standing-up food is not an oven dish: "were having a bbq for 12 people on saturday" has
    # the party-food answer already, and a tray of chicken thighs is the wrong shape for it
    "bbq", "barbecue", "barbeque", "buffet", "finger food", "party food", "canape",
    "nibbles", "crisps", "sausage rolls", "sandwiches", "picnic",
    "how many people does", "feeds", "feeding a",
    # a plan for the week, and not knowing how to cook at all, are their own questions and they
    # answer a table of six better than one tray of chicken thighs does: "having 6 people over on
    # saturday and i need to plan a dinner", "im having six people over on saturday and i cant
    # cook".
    "plan", "planning", "meal plan", "the week", "cant cook", "can't cook", "cannot cook",
    "never cooked", "dont know how to cook", "don't know how to cook", "beginner",
)


def _a_table_announced(understood):
    """Whether the line states a table of people, with no meal and no cooking verb in it."""
    read = understood if isinstance(understood, dict) else {}
    text = " " + str(read.get("clean") or read.get("text") or "").lower() + " "
    if not _A_TABLE_OF_PEOPLE.search(text):
        return False
    return not any(phrase in text for phrase in _NOT_A_TABLE)


_A_DIET = (("vegetarian", "meat"), ("vegan", "meat"), ("no meat", "meat"),
           ("nut allergy", "nuts"), ("gluten free", "gluten"), ("dairy free", "dairy"),
           ("lactose", "dairy"))


def the_table_of_people(memory, understood):
    """The one-dish answer for a stated table, sized by the number in the line.

    The reading is the one cooking.py's own crowd row does, over the line plus the last few
    turns: an occasion named one turn back ("a bit of a do for my mums birthday", then "im
    cooking for 12 on saturday") belongs to the table being cooked for, and a table of twelve
    told the plain version while cooking's row tells the fuller one is the same line answered two
    ways. Where both rows fit, both now say the same thing, so the person sees no difference.
    """
    read = understood if isinstance(understood, dict) else {}
    line = str(read.get("clean") or read.get("text") or "")
    text = line
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if isinstance(turns, list):
        text += " " + " ".join(str(turn.get("user") or "") for turn in turns[-4:]
                               if isinstance(turn, dict))
    text = text.lower()
    banned = set()
    for word, food in _A_DIET:
        if word in text:
            banned.add(food)
    return _crowd_meal(banned, _occasion(text), _crowd(text))


entry_a_table_of_people = entry(
    "a-table-of-people",
    (("people", "guests", "adults", "folk", "of us", "feeding", "cooking for", "catering"),
     ("coming", "round", "over", "for", "having", "feeding", "catering", "invited", "due",
      "arriving", "on saturday", "on sunday", "on friday", "on monday", "tonight", "tomorrow")),
    the_table_of_people,
    # the quantity, the meal, the fault and the diet rows are narrower and keep their lines
    avoid=("how much", "how many", "per head", "per person", "per guest", "portion",
           "poison", "hygiene", "allergy", "allergic", "food bank", "menu", "seating",
           "chairs", "plates", "cutlery", "feed the dog", "feeding a baby"),
    guard=_a_table_announced,
    # A table of people is the cooking question even where a lunch or a stay row also fits: the
    # person has said how many they are feeding, and the answer to that is what to cook.
    bias=1)
ENTRIES.append(entry_a_table_of_people)
