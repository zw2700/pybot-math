"""The cooking entries themselves, one list of them, kept out of cooking.py for size alone.

The world refuses a file over 1 MB, and the list of how-to-cook questions was 411 KB of
cooking.py. Nothing about the questions changed when they moved: cooking.py copies this list
where it used to stand, so the entries are the same entries in the same order, in the one
cooking domain, with the same keys and the same replies. Every helper they use is imported from
cooking.py, which has already defined them by the time this module is imported.
"""
import re

from ..compose.repair import amends_to, line_of
from .dishes import KEEP_QUALITY_WORDS, PAIRING_FOODS
from .freshness import (a_cooling_question_not_a_keeping_one, soak_but_not_left_out,
                        _not_how_to_keep_it_fresh, _not_just_a_hard_loaf)
from .lookup import (DAY_WORDS, JOB_GUARD, PACK_DATE, TOOTH_OUT, entry,
                     not_the_flat_you_live_in)
from .shopping import not_a_present
from .body import a_persons_temperature

from . import cooking as _cooking_tables
from .cooking import (
    DECIDING, _line, missing, without,
    BAKED_GOODS_WORDS, CALORIE_ASKS, COMING_APART, COOK_VERBS, COOK_WORDS,
    DEFINITION_WORDS, DIABETIC_PLATE, FOOD_CALORIES, FOOD_CALORIE_MEALS, FOOD_NUTRIENTS,
    FREEZER_KEEP, FREEZE_FACTS, GLUTEN_FACT_ASKS, GLUTEN_FACT_FOODS, GLUTEN_FREE_ASKS,
    GLUTEN_FREE_DISHES, KEEPING,
    KEEP_ASK, LEAFY, LEAFY_AVOID, MEATLESS_ROAST,
    NOT_A_COOKING_LINE, OPEN_ASK, PET_LINE_WORDS, PLAN_NAMES,
    STAPLE_ASK, STORAGE, WANT_SOMETHING_ELSE, _BAKE_FAULT,
    _BAKE_THING, _CHEAP_AVOID, _EGG_DISH, _EGG_FAULT,
    _EGG_SAUCE, _FOOD, _A_TASTE, _FREEZE_AVOID, _GLUTEN_FREE_SKIP,
    _GRAIN_FOOD, _GRAIN_WORD, _MASH_NOT_THIS, _MEAL_ASK_AVOID,
    _NOT_MINE, _NO_MEAT, _NUTRIENT_ASK_WORDS, _NUTRIENT_WORDS, _OUT_ASK,
    _STAPLE_NAMES, _SWAP_ASK, _WET_FOOD, asks_a_gluten_fact, _bake, _learn_to_cook,
    _not_a_portion_ask,
    _BAKE_FAULT_FAMILIES, _BAKE_FOLLOW_SHAPES, _BAKE_KEEP_SHAPES, _BAKE_KEEPING,
    _BAKED_GOODS, _CAKE_NAMES, _NO_CAKE_RISE, _NO_LOAF_RISE, _NO_SPREAD_RISE,
    _bake_follow, _bake_keep, _gummy,
    _a_soft_fruit_is_still_a_cooking_question,
    _bake_always, _bake_burning, _bake_fault, _bake_fruit, _baked_keep,
    _body, _bread, _bread_rise_answer, _breakfast_ideas,
    _burnt_dish, _burnt_pan, _cake_fault, _calories,
    _cauliflower_rice, _chicken_time, _chocolate, _coffee_fault,
    _container_keep, _cook_word, _cookies, _dip_fault,
    _dough, _dry, _egg_fault, _eggs, _falls_apart,
    _flat, _free_of_gluten_fact, _freeze_food, _gluten_free, _grainy,
    _MINCE_GRAIN_DISH, _MINCE_GRAIN_WORD, _mince_grainy, _crowd,
    _greasy, _herbs_keep, _honey_age, _kids_veg,
    _bans_of, _legs, _lentils, _lumpy, _lunch_ideas, avoids_for_the_one_talked_about,
    _meal_ideas, _meal_plan, _meat_defrost, _mince,
    _non_stick_pan, _nut_free, _nutrients, _oil_smoking,
    _pancake_batch, _pancakes, _pasta_cook, _pastry_fault,
    _popcorn_keep, _popcorn_make, _protein, _pudding_ideas,
    _pulses, _rest_the_meat, _rice_time, _roast_joint,
    _roast_shopping, _salty, _scramble, _sides,
    _jacket, _jam_make, _mushroom_wash, _poach_fish, _soggy_lunch, _soup, _split,
    _staple, _tea_reply,
    _stuck_jar, _sugar_work, _sweet_potato, _tenders_are_a_piece, _tenders_method,
    _thighs,
    _time_budget, _tin_answer, _tough, _turkey,
    _turkey_cut, _undercooked, _vegan_bake, _watery,
    entry,
)

# The cuts and the whole things that had no method card at all: "how long to cook lamb chops",
# "how do i cook a lamb shank", "how do i cook kidneys" and "how do i cook a whole fish" were
# all "I don't know enough to answer that honestly", and the joint timetable, the beef steak
# card and the four-things-that-make-a-cook card were the wrong answers to them. A cut decides
# the method and the time, so each one gets a row of its own.
#
# These rows live in this file rather than in cooking.py because that file is over the world's
# 1 MB upload limit (1,051,269 bytes on main) and a branch that touches it cannot be opened at
# all. They are appended to cooking's one table here, at import, so the staple row below and
# every other reader see a single table of methods - the same arrangement the keeping rows have.
_EXTRA_BASICS = (
    # The chops and the shank had no method card at all: "how long to cook lamb chops" and
    # "how do i cook a lamb shank" were both "I don't know enough to answer that honestly", and
    # the joint timetable ("beef or lamb: 20 minutes at 220C, then 15 minutes per 500g") is the
    # wrong card for either - a chop is a pan job of a few minutes and a shank wants a long
    # braise. The cuts lead the answer because that is what decides the time.
    (("lamb chops", "lamb chop", "lamb cutlets", "lamb cutlet"),
     "Lamb chops are a hot-pan job, 3 to 4 minutes a side for pink in the middle, or 5 if you "
     "want them through, then 3 minutes resting: a chop is thin, so the pan has to be properly "
     "hot before they go in and the fat edge wants standing on to render. In the oven they take "
     "12 to 15 minutes at 200C (180C fan). Salt them just before they go in, not before."),
    (("lamb shank", "lamb shanks"),
     "Braise lamb shanks: brown them in a heavy pan, then cook covered at 160C (140C fan) for 2 "
     "to 2.5 hours with stock, onion, carrot and a spoon of tomato, until the meat gives way to "
     "a fork. They are the cut a slow cooker suits, on low for 6 to 8 hours. Cook them the day "
     "before if you can, because the sauce sets and the fat comes off in one piece."),
    (("gammon steak", "gammon steaks", "gammon"),
     "Gammon steak is cooked through, not pink: 4 to 5 minutes a side in a hot pan, or 15 to 20 "
     "minutes under a grill, turning once. If it is thick or you want it milder, simmer it 15 "
     "minutes in water first, then dry it and fry it. It needs no salt - it is already cured - "
     "and a spoon of honey or marmalade in the pan at the end glazes it."),
    # Brisket had the beef steak card ("2 to 3 minutes a side for medium rare"), which is a whole
    # different animal: a brisket is the toughest cut on the beast and it is only good after hours
    # of low heat. It is the same shape of mistake the gammon steak had - the word "beef" decided
    # the card, not the cut - so the steak entry now stands down for it too.
    (("beef brisket", "brisket", "brisket joint", "rolled brisket"),
     "Brisket is a long cook, not a quick one: in the oven at 150C (130C fan), covered, for 3 "
     "to 4 hours, or about 1 hour per 500g, with a splash of stock in the tin, until a fork "
     "slides in with no pull. "
     "Season it heavily the night before if you can. It slices better after 20 minutes resting, "
     "and it is the one cut that is better the next day."),
    # "how do i cook lamb kofta" was given the leg-of-lamb timetable, because lamb was in the line
    # and a leg is the only lamb the timetable knows. Kofta is minced and it is minutes on a grill.
    (("lamb kofta", "kofta", "koftas", "lamb kofte", "kofte"),
     "Kofta is minced lamb shaped by hand: mix 500g of mince with a grated onion squeezed dry, a "
     "handful of parsley, cumin, cinnamon and salt, then shape fingers around a skewer and grill "
     "them 10 to 12 minutes, turning, on a barbecue or under the grill, or bake them on a tray "
     "in the oven at 200C (180C fan) for "
     "15 to 18 minutes, or fry them 3 to 4 minutes a side. The onion is what keeps "
     "them soft; squeeze it or they fall apart."),
    # A duck leg is a braise and a whole duck is a roast, and neither is the duck breast card: both
    # were a shrug. The legs are the half of the bird that wants the long cook.
    (("duck legs", "duck leg", "duck thighs", "duck thigh"),
     "Roast duck legs at 160C (140C fan) for 1.5 to 2 hours, skin side up on a rack over a tin, "
     "until the skin is crisp and the meat pulls off the bone: the long slow heat is what renders "
     "the fat under the skin, and a hot oven just burns it. Prick the skin, salt it well, and do "
     "not cover them."),
    # "how do i cook liver" was answered with the four-things-that-make-a-cook card. Liver is a
    # two-minute job and the mistake everyone makes is cooking it until it is grey.
    (("liver", "lambs liver", "chicken liver", "chicken livers", "calves liver", "pig liver"),
     "Liver is a hot, fast job: pat it dry, flour it lightly if you like, and fry it 2 to 3 "
     "minutes a side in a hot pan with butter, no more, until it is brown outside and still pink "
     "in the middle. Past that it goes grainy and bitter. Soaking it 30 minutes in milk takes the "
     "edge off a strong one, and it wants onions cooked slowly first, not alongside."),
    # "how do i cook kidneys" was answered with the four-things-that-make-a-cook card as well, and
    # a kidney is the same two-minute job as a liver. It stands down for the medical kidney: pain,
    # stones and kidney disease are the health module's and they were the words that could have
    # followed the food in.
    (("kidneys", "kidney", "lamb kidneys", "pig kidneys", "calves kidneys"),
     "Kidneys are a hot, fast job like liver: halve them, cut out the white core, and fry them 2 "
     "minutes a side in a very hot pan with butter, or 3 to 4 minutes in total if they are sliced. "
     "Past that they go rubbery. In a stew they are the opposite - an hour and a half, low - which "
     "is why the same meat has two timings."),
    # A whole duck is not the duck breast card and it was a shrug: the breast is 18 minutes, the
    # whole bird is a roast with a lot of fat to render, and the two heats are the trick.
    (("whole duck", "a whole duck", "roast duck", "roasting duck"),
     "Roast a whole duck at 200C (180C fan) for 20 minutes, then at 160C (140C fan) for 20 "
     "minutes per 500g, pricking the skin all over and salting it first: the hot start crisps the "
     "skin and the lower heat renders the fat under it. Rest it 15 minutes. If you have time, pour "
     "a kettle of boiling water over it and let it dry before it goes in - that is what makes the "
     "skin crackle."),
    # Whole fish was the salmon fillet card, or a rod licence for the verb "fish". A whole fish is
    # scored and roasted, and the timing is by thickness rather than by weight.
    (("whole fish", "a whole fish", "whole salmon", "whole trout", "whole sea bass",
      "whole mackerel"),
     "A whole fish is scored on both sides and roasted at 200C (180C fan) for 20 to 25 minutes "
     "for a 1kg fish, or about 10 minutes for every 2.5cm through the thickest part, with lemon "
     "and herbs in the belly and a little oil rubbed into the skin. It is done when the eye has "
     "gone white and the fin pulls out easily. Sit it on sliced onion or fennel so it does not "
     "stick."),
    # Scallops were a shrug, and they are the cheapest win in a kitchen: a minute and a half a
    # side. The coral, the dry pan and the crowding are the three things people get wrong.
    (("scallops", "scallop", "king scallops"),
     "Scallops take 1.5 to 2 minutes a side in a very hot pan and no more: pat them dry, salt "
     "them, and put them in when the oil just starts to smoke, then leave them alone until the "
     "edge is golden brown. Wet scallops steam instead of browning, and a crowded pan does the "
     "same. The orange coral is good to eat and wants half the time."),
    # Monkfish, squid, crab, rabbit and a lamb neck were all "beyond what I know well". They are
    # the same shape of question - a thing in a supermarket that people buy once and are not sure
    # of - so each is a method and a time, with the pet, the calorie and the price lines avoided.
    (("monkfish",),
     "Monkfish takes 12 to 15 minutes at 200C (180C fan), or 3 to 4 minutes a side in a hot pan: "
     "it is dense and holds together, so a rasher of bacon or a slice of prosciutto wrapped round "
     "it and a squeeze of lemon at the end is all it needs. It is done when it turns opaque white "
     "right through, and unlike cod it will not fall apart if you give it another minute."),
    (("squid", "squid rings", "calamari"),
     "Squid is either 2 minutes or 45: rings, or tubes scored in a diamond pattern, into a very hot "
     "pan for 1 to 2 minutes until they curl and turn opaque, or into a stew or a slow braise for "
     "45 minutes to an hour - anything in between is rubber. Pat them dry first, or they steam "
     "instead of browning."),
    (("crab", "dressed crab", "brown crab"),
     "A cooked crab is picked, not cooked again: twist off the claws, crack them with the back of "
     "a knife, and pull the white meat out of the shell, keeping the brown meat from the body "
     "separate because it is the stronger tasting of the two. A live crab goes into boiling salted "
     "water for about 15 minutes and cools in the water."),
    (("rabbit", "rabbit stew", "wild rabbit"),
     "Rabbit wants either a long braise or a fast roast: jointed and browned, then covered with "
     "stock and cooked at 150C (130C fan) for 1.5 to 2 hours, it comes away from the bone; the "
     "saddle roasted at 200C for 20 to 25 minutes stays moist. It is very lean, so it needs bacon, "
     "wine or a lid to keep it from drying out."),
    (("lamb neck", "neck of lamb", "lamb neck fillet", "neck fillet"),
     "A lamb neck is a braise: brown it, then cook it covered at 150C (130C fan) with stock and "
     "onions for 2 to 2.5 hours until the meat comes off the bone, or 8 hours on low in a slow "
     "cooker. Neck fillet is the quick cut of the same name - 4 to 5 minutes a side in a hot pan, "
     "rested for 5."),
    # Oxtail was "beyond what I know well" and it is a Sunday staple: three hours, and the bone is
    # why it tastes of anything.
    (("oxtail", "oxtail stew", "ox tail"),
     "Oxtail needs about 3 hours: brown the pieces, then cook them covered at 150C (130C fan) "
     "with stock, onion, carrot and a spoon of tomato until the meat comes away from the bone - "
     "the bone and the gelatine in it are what give the sauce its body. Skim the fat off the top "
     "before serving, and it is better made the day before."),
)

# Each of those rows answers a method question and nothing else: the calories, the cost, the
# slow cooker, the leftovers and the medical sense of the same word belong to rows that already
# answer them, so the new row stands down for those words.
_EXTRA_GUARDS = {
    # A chop is one fast answer and a joint, a curry or a casserole is another: what to make
    # with them, how long to roast the whole thing and what they cost a kilo are not this row.
    'lamb chops': ("slow cooker", "casserole", "curry", "roast a leg", "leg of lamb", "shoulder",
                   "joint", "how many", "calories", "cheap", "marinade", "rub"),
    'lamb shank': ("slow cooker", "how many", "calories", "cheap"),
    # "how long to boil a gammon joint" is the joint timetable, and a joint is not a steak.
    # "should i boil it first", the line after a gammon steak, is still this row's: the card
    # says to simmer it first. A joint is the joint timetable's question, not this one's.
    'gammon steak': ("joint", "joints", "roast", "roasting", "how many", "calories", "cheap",
                     "ham", "bacon", "sausage"),
    # A whole brisket is not a steak and it is not the roast-joint timetable either: it is its own
    # long cook. What to make with the leftovers and what it costs are other rows' questions.
    'beef brisket': ("steak", "steaks", "joint", "roast joint", "how many", "calories", "cheap",
                     "leftover", "leftovers", "sandwich", "slow cooker", "pressure"),
    'lamb kofta': ("leg of lamb", "shoulder", "roast", "joint", "how many", "calories", "cheap",
                   "slow cooker", "casserole", "curry"),
    'duck legs': ("breast", "breasts", "how many", "calories", "cheap", "whole duck"),
    'liver': ("pate", "pate recipe", "how many", "calories", "cheap", "iron", "pregnant",
              "healthy", "good for"),
    # The medical kidney owns the word beside pain, stones and disease: a card about frying would
    # be grotesque there, and those are the words a person types with it.
    'kidneys': ("pain", "ache", "aches", "stone", "stones", "disease", "infection", "function",
                "failure", "dialysis", "transplant", "doctor", "gp", "hospital", "urine",
                "blood", "protein", "damage", "filter", "how many", "calories", "cheap", "iron",
                "healthy", "good for", "pregnant"),
    'whole duck': ("breast", "breasts", "legs", "leg", "how many", "calories", "cheap",
                   "leftover", "leftovers"),
    # The verb "fish" has a licence and a tank: a whole fish is the cooking question, and the
    # fillet, the stock and the fishcake rows are not this one.
    'whole fish': ("fishing", "fish tank", "tank", "aquarium", "pond", "fillet", "fillets",
                   "fishcake", "fishcakes", "stock", "monger", "market", "raw", "sashimi",
                   "sushi", "allergy", "shellfish", "how many", "calories", "cheap"),
    'scallops': ("shellfish", "allergy", "allergic", "how many", "calories", "cheap", "frozen",
                 "freezer", "raw", "sashimi", "reef", "seagull", "seagulls"),
    'oxtail': ("how many", "calories", "cheap", "soup", "dog", "dogs"),
    'monkfish': ("how many", "calories", "cheap", "frozen", "mercury", "pregnant", "sustainable"),
    # a squid is bait and calamari is a menu, and a pet squid is in a tank
    'squid': ("bait", "fishing", "tank", "how many", "calories", "cheap", "frozen", "mercury",
              "pregnant", "restaurant", "menu"),
    # a crab in a tank is a pet, and a crab louse is a different question entirely
    'crab': ("hermit", "tank", "pet", "pets", "moulting", "molting", "louse", "lice", "pubic",
             "itch", "itching", "how many", "calories", "cheap", "shellfish", "allergy",
             "allergic", "pregnant", "mercury"),
    # a rabbit is a pet far more often than it is a dinner, so the pet words stand this row down
    # and "how long do rabbits live" is not a braise: this row keys the animal with "how long", so
    # a lifespan question was answered with a cooking time - on today's main it still is - and the
    # animal table has the years. Words about living stand the row down.
    'rabbit': ("pet", "pets", "my", "hutch", "hutches", "cage", "litter", "droppings", "sick",
               "ill", "vet", "sneezing", "sneeze", "eating", "feed", "feeding", "fur",
               "neutered", "adopt", "bonded", "how many", "calories", "cheap", "wild",
               "live", "lives", "lived", "lifespan", "life span", "life expectancy",
               "how old"),
    'lamb neck': ("how many", "calories", "cheap", "pain", "stiff", "ache", "aches"),
    # A whole fish is scored and roasted with the head and tail on, which is a different method and
}

# The fillet row is first in the table, so "how do i cook a whole fish" reached it before the
# whole-fish row could: a whole fish is scored and roasted by thickness, which is a different
# method and a different time. The fillet row stands down for the word that says the fish is
# whole, and a fillet still gets the fillet card.
if "whole" not in _cooking_tables.NOT_WANTED.get("fish", ()):
    _cooking_tables.NOT_WANTED["fish"] = ("whole",) + tuple(
        _cooking_tables.NOT_WANTED.get("fish", ()))
# A rabbit is somebody's animal before it is a joint, and the care question is asked with the
# plainest words there are ("look after", "keep", "should i get one", "for a child"). None of them
# is a word about cooking, so the method row stands down for them: "how do i look after a rabbit"
# was answered "Rabbit wants either a long braise or a fast roast", and "should i get a rabbit"
# the same, because the guard held only the words for an animal kept already ("my", "hutch",
# "vet") and not the words for taking one on. Added here rather than in the row above so the
# row stays the row it is.
_EXTRA_GUARDS['rabbit'] = tuple(_EXTRA_GUARDS['rabbit']) + (
    "look after", "looking after", "care for", "caring for", "should i get", "should we get",
    "shall i get", "thinking of getting", "of getting a", "get a rabbit", "get one",
    "getting one", "own a rabbit", "owning", "new rabbit", "as a pet", "for my son",
    "for my daughter", "for my child", "for a child", "for kids", "for our", "keep a rabbit",
    "keeping a rabbit", "rabbit for", "asking for", "asked for", "wants a", "want a",
    "birthday", "get one as", "have a rabbit", "having a rabbit", "bring home", "need for",
    "needs for", "need to get", "to get a rabbit")

_cooking_tables.NOT_WANTED.update(_EXTRA_GUARDS)
_cooking_tables.BASICS = tuple(_cooking_tables.BASICS) + _EXTRA_BASICS
# The staple row below is keyed on the names in the table, so the new cuts have to be in that
# key or "how do i cook kidneys" never reaches the method at all.
_STAPLE_NAMES = _STAPLE_NAMES + tuple(
    name for _names, _reply in _EXTRA_BASICS for name in _names)
# A person after a take-verb is a trip, not a buffet: "im taking my mum to bath for her birthday"
# holds "birthday" and "taking", so the party row answered a day out with pasta salad and paper
# plates, and the lines after it were read as party food too ("what should we do there" got the
# cook-for-a-crowd advice). Naming the person is what a trip looks like, so the row stands down
# and the day out is left to the rows that plan one.
# "is my rice still ok" on its own is the bag in the cupboard, and that card answers it. The
# keeping question is about the cooked bowl only when the line says the rice was cooked, so the
# still-ok row names the subject ("rice", "still ok") as the cupboard row does and this guard is
# what tells the two apart. A guard rather than an avoid word, because the cue and the rice have
# to be two separate mentions: an avoid word would stand the row down for its own subject.
_RICE_WAS_COOKED = re.compile(
    r"\b(?:cooked|leftover|left over|takeaway|take away|last night|yesterday|in the fridge|"
    r"in the freezer|refrigerated)\b")


# The one card both cooked-rice keeping rows give. It has to stand alone on the takeaway and the
# day-after lines, so it carries the bin rule that the cooler "rice-storage" card leaves out; two
# copies of a 340-character reply in one file is a second place to forget when the rule changes.
_COOKED_RICE_KEEPS = (
    "Cooked rice keeps a day in the fridge and no longer: cool it within an hour of cooking, box "
    "it, and put it in cold. Reheat it once, all the way through until it is steaming hot, and "
    "never a second time - the spores that grow in rice left warm are not killed by reheating. "
    "Rice that sat out overnight goes in the bin, and so does anything that smells or feels "
    "slimy.")


def _the_rice_was_cooked(understood):
    said = str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower()
    return bool(_RICE_WAS_COOKED.search(said))


_TAKEN_PERSON = (r"(?:mum|mom|mam|mummy|dad|daddy|father|mother|son|daughter|child|children|"
                 r"kid|kids|baby|wife|husband|partner|boyfriend|girlfriend|friend|mate|"
                 r"brother|sister|cousin|nan|gran|granny|grandma|grandad|grandpa|niece|nephew|"
                 r"aunt|uncle|neighbour|neighbor|family|parents|him|her|them)")
_TAKING_SOMEBODY = re.compile(
    r"\b(?:take|takes|taking|took|taken|bring|brings|bringing|brought)\s+"
    r"(?:(?:my|his|her|our|their|the|a|your)\s+)?" + _TAKEN_PERSON + r"(?!'s)\b")


def _not_a_trip(understood):
    """True unless the line is taking somebody somewhere, which is a day out and not a buffet."""
    said = (understood.get("norm_text") or understood.get("text") or "").lower()
    return _TAKING_SOMEBODY.search(said) is None


# "I cooked pasta yesterday, can I eat it" is a keeping question, and the pan row was taking it
# because "cooked" is a form of its own "cook": the day-before words are what tell a bowl in the
# fridge from a pan on the hob, so the cooking rows stand down on them the way they already stand
# down on "next day" and "leftover".
_DAY_BEFORE = ("yesterday", "yesterdays", "last night", "this morning", "the day before",
               "day before", "the day after", "day after", "day later", "a day later",
               "days ago", "a couple of days ago", "2 days ago", "two days ago")

# Food carried onto a plane is the security question, and travel.py's flight-food answers it. The
# lunch and picnic rows own the food at school, work or a party, and on a flight line they stood in
# its way: "can i take a packed lunch on a plane" got the five-minute packed lunch, and "can i take
# a picnic on a plane" the party buffet, both answers to a question about a kitchen rather than a
# security tray. They stand down on the flight words; the same food at work or on a train keeps its
# own answer, because "journey", "train" and "car" are not here.
_ON_A_FLIGHT = ("plane", "planes", "flight", "flights", "flying", "airport", "airports",
                "security", "hand luggage", "carry on", "carry-on", "cabin bag", "cabin")

# A lunchbox is one person's lunch, and a lunch for other people is a table to cook for. The
# sandwich row answered "im having my parents over for lunch on sunday" and "whats a good
# lunch for 6 people" with a wrap and a drink, and the guests went unfed. Anyone else on the
# line - a guest, the family, a number at the table - stands the row down so the cooking-for-a-
# crowd row answers instead.
#
# It is a guard rather than an `avoid` word because `avoid` is read one word at a time, and a
# lunchbox for a family is still a lunchbox: with the person words in `avoid`, "packed lunch
# ideas for the family", "lunchbox ideas for the whole family" and "what can i put in everyones
# lunchbox" all lost the row and got a search hedge where main had answered them.
_OTHER_PEOPLE_AT_LUNCH = re.compile(
    r"\b(?:everyone|everybody|friends?|parents?|relatives?|"
    r"in\s?laws?|guests?|visitors?|"
    # "what do people usually have for lunch" asks about people in general, so bare
    # "people" is not here: only the shapes that put people at this table.
    r"(?:people|folk) (?:coming|over|round|for|at)|having people|"
    r"for (?:\d+|three|four|five|six|seven|eight|nine|ten|twelve|twenty) "
    r"(?:people|adults|guests|kids|children))\b")
# "of us" is read as a count rather than as a phrase: "whats a good lunch for 2 of us" is two
# people and a sandwich apiece, which is the row's own answer, while three or more is somebody
# cooking for a table. A bare phrase cannot tell those apart, and it stood the row down for a
# couple as readily as for a family.
# "the family" is not in that list on purpose. It is the household as often as it is guests, and
# with the lunch row stood down for it, "lunch ideas for the family" and "sunday lunch ideas for
# the family" reached the ten-minute kids' tea - a card that invents small children. The family
# lunches that are a table are named as one ("lunch for the family", "having the family over"),
# and those phrases are read by the crowd row itself.
_PACKED_LUNCH_NOUNS = ("packed lunch", "packed lunches", "lunchbox", "lunchboxes",
                       "lunch box", "lunch boxes", "school lunch", "school lunches",
                       "work lunch", "lunch for work", "lunch to take", "take to work",
                       "take for lunch", "pack up", "packed up", "packup")


def _one_persons_lunch(understood):
    """Whether the line is one person's lunch rather than a meal for other people.

    A line that names a packed lunch or a lunchbox keeps the row whoever it is for: the
    person words are about who eats it, not about whether it leaves the house, and
    "packed lunch ideas for the family" is a lunchbox question before it is a table.
    """
    # The reading is not always the line as it was typed. "whats a good lunch for 4 of us"
    # reaches the entry read back as "what is a good lunch for four of me", because the
    # understanding pass puts the first person in: with only `clean` to go on, the guard saw
    # one person on a table of four and the sandwich answered the crowd. `text` keeps what the
    # person typed, so both are read and the first that names other people stands the row down.
    if not understood:
        return False
    lines = [str(understood.get(field) or "").lower() for field in ("text", "clean")]
    if not any(lines):
        lines = [" ".join(str(word) for word in understood.get("words") or ()).lower()]
    for said in lines:
        if any(noun in said for noun in _PACKED_LUNCH_NOUNS):
            return True
        if _OTHER_PEOPLE_AT_LUNCH.search(said):
            return False
        # A counted table is a table however it is phrased: "ideas for a sunday lunch for 10"
        # names nobody and reads as one person's lunch without the number, and the number is
        # what the crowd row counts. Six is where that row starts calling it a crowd.
        table = _crowd(said)
        if table >= 6 or (table >= 3 and "of us" in said):
            return False
    return True


# The food words of the freeze row are read off FREEZE_FACTS instead of being written out a second
# time: 44 names had a fact in that table but no word in this key, so "can i freeze garlic", "can
# i freeze yoghurt" and "can i freeze an egg" reached no entry at all and got a shrug while the
# answer sat in the table beside them. A fact added there now reaches the row by itself. The short
# list under it is the few words the key had that no fact names.
_FREEZE_WORDS_NOT_IN_FACTS = ("blackberries", "cherries", "cooked pasta", "soup")
# Fresh ginger's keeping row already answers the freezing half of the question - freeze it whole
# and grate it from frozen - and that is the better answer for ginger than "chop it and bag it",
# so the freeze row stands back for it and the fact table keeps its row.
_FREEZE_KEEPS_ITS_KEEPING = ("ginger",)
_FREEZE_FOOD_WORDS = tuple(sorted(
    ({str(_name).lower() for _names, _fact in FREEZE_FACTS for _name in _names}
     | set(_FREEZE_WORDS_NOT_IN_FACTS))
    - set(_FREEZE_KEEPS_ITS_KEEPING)))
# The same question with the dish left out: "can i freeze the rest", "can i freeze it", "will this
# freeze". The rest of the store answered these with a search hedge while the general rule - cool
# it within two hours, box it while it is still warm, about three months, never refreeze once
# thawed - sat in this row's own fallback, because the key wanted a food name and these lines name
# nothing. Anything a person points at in a kitchen is a food they mean, so the pointing words are
# words of this row too, and the row answers them with the general rule unless the chat already
# says what the dish is.
_FREEZE_POINTING_WORDS = ("it", "this", "that", "these", "those", "them", "the rest", "the other half",
                          "the remainder", "whats left", "what is left", "the spare", "some",
                          "any left", "any spare", "a portion", "the leftovers")

# The asking words a freeze question is put together with. A sentence about the speaker never
# says them: "i can read it fine but freeze when someone talks to me" is a person freezing up,
# and the bare freeze word plus a pointing word answered it with food.
_FREEZE_ASKS = ("can i freeze", "can you freeze", "can we freeze", "could i freeze",
                "should i freeze", "do i freeze", "how do i freeze", "how to freeze",
                "how long can i freeze", "how long do i freeze", "is it ok to freeze",
                "is it okay to freeze", "is it alright to freeze", "is it safe to freeze",
                "is it fine to freeze", "will it freeze", "will this freeze", "will they freeze",
                "will that freeze", "would it freeze", "do i need to freeze",
                "does it freeze", "does this freeze", "can this be frozen", "can it be frozen",
                "can that be frozen", "can these be frozen", "can they be frozen",
                "is it freezable", "is this freezable", "ok to freeze", "freezes well",
                "freeze well", "goes in the freezer", "put it in the freezer",
                "put this in the freezer", "keep it in the freezer", "can i keep it frozen")

# The age a parent names a child by: "my 2 year old refuses vegetables" is "my son refuses
# vegetables" with the age where the word would be. The wording is what people type, in the
# order the engine's `norm` leaves it.
_AGE_WORDS = ("year old", "years old", "year-old", "years-old", "yearold", "yearsold",
              "month old", "months old", "month-old", "months-old", "monthold", "monthsold",
              "week old", "weeks old", "week-old", "weeks-old", "weekold", "weeksold")


def _open_wine(memory, understood):
    """The three bottles people open: a cork, a screw cap, and a sparkling one.

    A screw cap has no cork to turn, and a sparkling bottle is opened the other way round, so the
    opening sentence is picked from the line: one card that leads with a corkscrew is wrong for two
    of the three.
    """
    line = " " + (understood.get("clean") or "") + " "
    if any(word in line for word in (" screw cap", " screwcap", " cap ", " caps ", " cap,",
                                     " cap.", " cap?")):
        return ("A screw cap just twists off with a crack, and the ring stays on the neck - no "
                "corkscrew, and the cap goes back on between glasses. If it will not turn, hold the "
                "top still and turn the bottle.")
    if any(word in line for word in (" prosecco", " champagne", " sparkling", " cava", " fizz",
                                     " bubbly", " sekt", " cremant")):
        return ("Chill it, then hold the cork and turn the bottle rather than the cork, pointing it "
                "away from people and anything breakable, and let it sigh out rather than bang. "
                "Sparkling wine is opened cold and slowly because the gas is the wine.")
    return ("Cut the foil below the rim, then stand the bottle on the table and turn the corkscrew "
            "into the middle of the cork; lever it out in two stages on the hinge and ease the last "
            "bit by hand so it does not pop. If the cork is dry and stubborn, wrap the neck in a warm "
            "cloth for a minute first. A screw cap simply twists off.")

# A staple that has run out is the same question as a swap for an ingredient, and it was the one
# shape the swap table did not hold: those stalls are keyed on the ingredient (butter, milk, eggs)
# and a staple was never one. "im out of rice", "we are out of rice" and "no potatoes left" were a
# shrug from the composer, because the freshness row (which used to take them with the bin-it
# card) stands down and nothing else says what stands in. Only the shortage shorthands are here:
# a bare "out of" is the oven and the fridge ("how long can butter stay out of the fridge").
_SHORTAGE_ASK = ("ran out", "run out", "im out of", "i'm out of", "were out of", "are out of",
                 "we're out of", "all out of", "none left", "havent got", "haven't got",
                 "got none", "have none", "no rice left", "no pasta left",
                 "no potatoes left", "no spuds", "out of rice", "out of pasta",
                 "out of potatoes", "out of spuds")

# The plain method of a staple answers a line that asks how to cook it, and it is the better
# answer there: these three rows are only about what stands in, so a line that says cook,
# how long or recipe belongs to the staple and to the dish made of it, not here. Without
# this list "how do i cook potato wedges" lost the wedges method to the boiled-potato doneness
# answer, because the swap row took the first place and the doneness entry came next.
_STAPLE_METHOD_AVOID = ("cook", "cooking", "cooked", "how long", "how much",
                        "how many", "recipe", "recipes", "method", "instructions", "best way",
                        "boil", "boiling", "boiled", "roast", "roasting", "bake", "baking",
                        "fry", "frying", "steam", "microwave")
# "how do i make porridge in the microwave" was answered with the hob, because one reply has to
# serve every porridge line and the hob method came first. A line that names the microwave wants
# the bowl it is standing in front of: the amounts, the minutes and the stir halfway, in that
# order.
def _porridge(memory, understood):
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if "microwave" in said or "microwaving" in said or "micro" in said.split():
        return ("Put 40g of porridge oats in a big bowl with 250ml of milk or water - a big bowl, "
                "because it climbs the sides - and microwave it on high for 2 minutes. Stir it, "
                "then give it another 30 seconds to a minute until it is as thick as you like; it "
                "thickens more as it stands, so stop while it still looks a little loose. A pinch "
                "of salt and a spoon of honey or jam at the end.")
    return ("Simmer 1 part oats to 3 parts liquid for 5 minutes, stirring now and then, and add a "
            "pinch of salt; that gives creamy porridge rather than lumps. Milk added at the end "
            "keeps it creamier than cooking it all in milk. In a microwave, a single bowl takes 2 "
            "minutes on high, stirred halfway; stop early, as it thickens as it stands.")
# --- the stock pot ----------------------------------------------------------
# "Stock" is two words at once: the pot of bones and peelings, and a share in a company. The
# money side keeps its own lines - the `shares` row in money_words.py stands down on "simmer",
# "carcass" and "skim" now - and this is the kitchen side of the word.
#
# One row answers the whole family, because every stock question is the same pot with a
# different bone in it and a different ask on top: the kind of bone decides the time and the
# method, and the ask decides which sentence leads. Keeping the kinds as a table means a new
# one (ham hock, a fish frame, mushroom peelings) is one line here and no new row, and the
# questions that come as a follow-up - freezing it, cubes, the scum, more flavour - are
# answered for every kind at once.
#
# What it replaced: "how long do i simmer stock" was answered with the share price card, and
# every named stock - vegetable, fish, beef, "without bones" - got the chicken carcass method.
STOCK_BROWN = ("beef", "lamb", "pork", "veal", "oxtail", "venison", "mutton", "game", "ham")
STOCK_FISH = ("fish", "prawn", "prawns", "seafood", "shellfish", "salmon", "cod", "haddock",
              "trout", "mackerel")
STOCK_VEG = ("vegetable", "veg", "veggie", "mushroom", "mushrooms", "peelings", "scraps",
             "vegan", "vegetarian", "without bones", "no bones", "no meat")

STOCK_METHODS = {
    "chicken": (
        "Chicken or turkey stock simmers 1.5 to 2 hours at the barest bubble, and 3 if you "
        "want it stronger. Skim the grey foam off in the first twenty minutes and keep the "
        "lid off so it never boils hard, then strain it through a sieve. Cool it fast in a "
        "sink of cold water, which takes about an hour, and it keeps 4 days in the fridge or "
        "3 months frozen.",
        "Cover the picked carcass with cold water, add an onion, a carrot, a bay leaf and a few "
        "peppercorns, bring it to the barest simmer and skim the grey foam off in the first "
        "twenty minutes; 2 hours is plenty, 3 if you want it stronger. Strain it, cool it in a "
        "sink of cold water for about an hour, and it keeps 4 days in the fridge or 3 months "
        "frozen."),
    "brown": (
        "Beef, lamb or pork stock wants 3 to 4 hours at the barest simmer, after half an hour "
        "of browning the bones in a hot oven. It should set like jelly when it is cold, which "
        "is what tells you the bones were worth the time.",
        "Brown the bones with the onion and carrot halved at 220C (200C fan) for 30 minutes "
        "first, because the colour and most of the flavour come from that browning. Then cover "
        "them with cold water, add a bay leaf and a few peppercorns and simmer at the barest "
        "bubble for 3 to 4 hours, skimming the foam in the first twenty minutes. Strain it, and "
        "it keeps 4 days in the fridge or 3 months frozen."),
    "fish": (
        "Fish stock takes 20 to 30 minutes at a bare simmer and no longer - after that the bones "
        "turn it bitter and gluey. Skim the foam, don't stir it, and strain it through kitchen "
        "paper.",
        "Fish stock is the quick one: fish bones and trimmings with an onion, a carrot, a bay "
        "leaf and a few peppercorns, covered with cold water and simmered 20 to 30 minutes and "
        "no longer. Strain it through a sieve lined with kitchen paper, and it keeps 2 days in "
        "the fridge or 3 months frozen."),
    "veg": (
        "Vegetable stock simmers 30 to 40 minutes, and longer than that the sweetness goes "
        "muddy. Leave out the strong greens - cabbage, broccoli, cauliflower, beetroot - and "
        "season it at the end.",
        "Vegetable stock needs no bones at all: an onion, a carrot, a stick of celery, a bay "
        "leaf and a few peppercorns in cold water, simmered 30 to 40 minutes. Leave out "
        "cabbage, broccoli, cauliflower and beetroot, which turn it bitter and sour, put soft "
        "herbs in at the end, and it keeps 4 days in the fridge or 3 months frozen."),
}

STOCK_KEEP = (
    "Homemade stock keeps 4 days in the fridge and 3 months in the freezer. Cool it fast, get "
    "it into the fridge within 2 hours, freeze it in bags laid flat or in an ice cube tray for "
    "spoonfuls, and bring it back to a rolling boil before you eat it. A cube or a carton "
    "follows the date on the pack.")
STOCK_CUBES = (
    "A stock cube makes about 450ml of stock, one cube to a pint of water, and they are salty, "
    "so taste before you add any salt. Crumble it into hot water rather than dropping it in "
    "whole, and use half for a small pan of rice or gravy. Fresh stock in a tub beats a cube "
    "whenever the stock is the point of the dish.")
STOCK_CUBE_KEEP = (
    "A stock cube keeps its flavour for about a year in a dry cupboard, and the date on the box "
    "is the honest guide. Once the foil is open, wrap the rest or keep it in a sealed tub, "
    "because a cube that takes in damp goes hard and clumps; a soft one is still fine to use.")
STOCK_SKIM = (
    "Skim the grey foam off in the first twenty minutes with a spoon or a ladle, and keep the "
    "pot at the barest simmer with the lid off. The foam is blood and protein: it tastes flat "
    "and it is what clouds a stock, and after twenty minutes there is nothing left to skim. "
    "Don't stir the pot, or the fat mixes back in.")
STOCK_SLOW = (
    "In a slow cooker, cover the bones and vegetables with cold water and cook on low for 6 to "
    "8 hours, or high for 3 to 4, then strain it. Brown the bones in the oven first or the "
    "flavour is thin, and keep the liquid an inch below the lid. A slow cooker stock is weaker "
    "than a simmered one, so reduce it by a third before you freeze it.")
STOCK_FLAVOUR = (
    "Flavour comes from browning: roast the bones and the vegetables at 220C (200C fan) for 30 "
    "minutes before they go in the pot, and add a spoon of tomato puree or a few dried "
    "mushrooms. Don't let it boil, which drives the aroma off, and salt it only at the end. "
    "Reduce the strained stock by half and you have a stronger one for the freezer.")
STOCK_HEALTH = (
    "Stock is flavour, not medicine: it has some minerals and collagen from the bones, but the "
    "evidence for the joint and skin claims is thin, and a stock cube is mostly salt. "
    "Homemade with little or no salt is the useful version of it, and it is the cheapest way "
    "to make a soup or a stew taste of something.")
STOCK_AMOUNT = (
    "A litre of stock to 300g of risotto rice, added a hot ladle at a time; about 500ml for a "
    "soup for two; and enough to cover the bones in the pot by an inch. Whatever is left "
    "freezes in a bag, so make more than you need.")

# The word "stock" has a life outside the kitchen on both sides of the Atlantic, and this row
# must keep out of each: a share in a company, what a shop has on a shelf, a bone that hurts.
STOCK_AVOID = (
    "share", "shares", "market", "markets", "invest", "investing", "investor",
    "investors", "trade", "trading", "trader", "portfolio", "index fund", "isa",
    "dividend", "dividends", "price", "prices", "worth", "buy", "buying", "bought",
    "sell", "selling", "sold", "company", "companies", "ftse", "nasdaq", "wall street",
    # no "bond" or "bonds" here: "bones" is one slip from "bonds", and the typo reader would
    # turn every line about bones away from this row
    "crash", "crashed", "crypto", "bitcoin", "pension", "profit",
    "earnings", "valuation", "penny", "equities", "equity", "broker", "stockbroker",
    "in stock", "out of stock", "stock up", "stocking up", "christmas stocking",
    # a cloudy stock has its own row in cooking_gaps.py and answers it better than the method
    "cloudy", "clouded", "murky", "sediment",
    # the health side of "bone": a break, an ache, a scan, a supplement for the garden
    "broke", "broken", "fracture", "fractured", "sprain", "sprained", "hurt", "hurts",
    "ache", "aches", "pain", "pains", "swollen", "x-ray", "xray", "bone density",
    "osteoporosis", "arthritis", "bone meal", "garden", "plant", "plants", "soil",
    "compost", "fertiliser", "fertilizer")


def _stock_answer(memory, understood):
    """The stock pot this line is about: the kind of bone from the line, the ask from the line."""
    said = [str(word).lower() for word in (understood.get("words") or [])]
    if not said:
        return None
    line = " %s " % " ".join(said)

    def says(*words):
        return any(" %s " % word in line for word in words)

    if says(*STOCK_VEG):
        kind = "veg"
    elif says(*STOCK_FISH):
        kind = "fish"
    elif says(*STOCK_BROWN):
        kind = "brown"
    else:
        kind = "chicken"
    time_reply, method = STOCK_METHODS[kind]
    cubes = says("cube", "cubes", "granule", "granules", "bouillon")
    keeps = says("keep", "keeps", "keeping", "keep it", "store", "storing", "last", "lasts",
                 "freeze", "freezes", "freezing", "frozen", "freezer", "fridge", "use by",
                 "go off", "gone off", "out of date", "expire", "expired", "best before")
    if cubes and keeps:
        return STOCK_CUBE_KEEP
    if cubes:
        return STOCK_CUBES
    if keeps:
        return STOCK_KEEP
    if says("slow cooker", "crockpot", "crock pot", "pressure cooker", "slow"):
        return STOCK_SLOW
    if says("skim", "skimming", "scum", "foam", "froth"):
        return STOCK_SKIM
    if says("healthy", "healthier", "good for", "benefit", "benefits", "collagen",
            "nutritious", "nutrition"):
        return STOCK_HEALTH
    if says("flavour", "flavor", "taste", "tastes", "bland", "better", "stronger",
            "strong", "rich", "richer"):
        return STOCK_FLAVOUR
    if says("how much", "how many"):
        return STOCK_AMOUNT
    if says("how long", "long", "hours", "hour", "minutes", "minute", "time", "simmer",
            "simmering", "boil", "boiling", "cook", "cooking"):
        return time_reply
    return method


# A smoker is a different oven, so the heat and the time are the answer, and they change with the
# thing being smoked. The names are matched on the line's own words, longest first, so a brisket
# does not take the ribs' four to six hours.
_SMOKE_THINGS = ("brisket", "ribs", "rib", "pulled pork", "pork", "shoulder", "chicken", "turkey",
                 "wings", "sausage", "sausages", "salmon", "trout", "mackerel", "haddock", "fish",
                 "cheese", "tofu", "beef", "steak", "lamb", "duck")

_SMOKE_REPLIES = {
    "brisket": (
        "Brisket is low and slow: 110 to 120C at the lid, a couple of chunks of oak or hickory, "
        "and about 1.5 hours per kg - a 4kg joint is 9 to 11 hours - until it probes 93 to 95C "
        "inside. Wrap it in foil or butcher paper once the bark is dark and set, and rest it an "
        "hour before slicing."),
    "ribs": (
        "Pork ribs take 110 to 120C for four to six hours, until the meat has pulled back from the "
        "bone and the rack bends without breaking. Rub them with salt, sugar and paprika the night "
        "before, and only sauce them in the last 20 minutes or the sugar burns."),
    "chicken": (
        "Smoke chicken at 130 to 140C rather than lower, so the skin renders instead of going "
        "rubbery: about two hours for a whole bird, and off the heat at 74C in the thickest part "
        "of the thigh. Smaller pieces take 45 minutes to an hour."),
    "salmon": (
        "Hot-smoke salmon at 120C for 45 minutes to an hour, after an hour in a salt-and-sugar "
        "brine so it stays moist and the white protein does not leak out. Cold-smoking is a "
        "different job and needs a cure and a much cooler box."),
    "cheese": (
        "Smoke cheese at 90 to 110C for 30 to 45 minutes - long enough to take the colour, not "
        "long enough to melt it - and let it firm up in the fridge for a day before eating."),
    "default": (
        "Low and slow is the rule: 110 to 120C at the lid, with the meat off the direct heat, and "
        "time by thickness rather than by the clock - beef to 93 to 95C so it pulls, chicken to "
        "74C, pork ribs four to six hours. Keep the lid down, and a couple of chunks of wood is "
        "plenty; more than that turns it bitter."),
}


# "Smoked haddock" is a fish on the slab, not a question about a smoker, and the participle alone
# was enough to reach the row: "how do i cook smoked haddock" and "what can i make with smoked
# haddock" were both answered with the method for hot-smoking a salmon. A smoked food wants a
# recipe, so the row stands down unless the line has a smoking word that is not that participle -
# the verb, the noun, or the gear.
_SMOKING_WORDS = {"smoke", "smokes", "smoked", "smoking", "smoker", "smokers", "bbq",
                  "barbecue", "barbeque", "woodchips", "pellet", "pellets"}
_SMOKING_PHRASES = ("hot smoke", "cold smoke", "wood chips", "low and slow", "pellet grill",
                    "smoke it", "smoke them", "smoke a ", "smoke an ")


def _asks_about_a_smoker(reading):
    """A guard: a food that is already smoked is a recipe, not a question about a smoker."""
    said = str((reading or {}).get("text") or "").lower()
    words = set(re.findall(r"[a-z']+", said))
    if "smoked" not in words:
        return True
    if words & {word for word in _SMOKING_WORDS if word != "smoked"}:
        return True
    return any(phrase in said for phrase in _SMOKING_PHRASES)


def _smoke_food(memory, reading):
    words = {str(word).lower() for word in (reading.get("words") or ())}
    for name in _SMOKE_THINGS:
        if name in words:
            if name in ("rib",):
                name = "ribs"
            elif name in ("pulled pork", "pork", "shoulder"):
                name = "ribs" if "rib" in words else "default"
            elif name in ("turkey", "wings"):
                name = "chicken"
            elif name in ("trout", "mackerel", "haddock", "fish"):
                name = "salmon"
            elif name in ("sausage", "sausages", "tofu", "beef", "steak", "lamb", "duck"):
                name = "default"
            return _SMOKE_REPLIES[name]
    return _SMOKE_REPLIES["default"]


# The "make it thick" ask, written out per subject: "how do i make soup thick", "how do i make
# my sauce thick", "how do i make thick gravy". The recipe table carries "make soup" as a phrase,
# and a phrase outranks this row's single "thick", so the plainest way of asking the fault went to
# the forty-minute method instead. Written as a helper because the same expansion is what any fault
# row with a subject list and a property list needs, not just this one.
# "i have no frozen peas", "we are out of garden peas", "no petit pois left": the row that says
# how to cook them is the answer to a pan of peas and no answer at all to a person who has none.
# The shortage has to be said of this food, with nothing but a word or two about its form between
# the shortage and the name ("no frozen peas", "out of garden peas"), because "peas out of the bag"
# is about cooking them and stays the cooking row's.
SHORT_OF_THE_HOUSE = re.compile(
    r"\b(?:no|without|out of|ran out of|run out of|none left|nothing left|havent got|"
    r"haven't got|havent any|haven't any|dont have|don't have|didnt have|didn't have|"
    r"not got any|got none)\s+(?:\w+\s+){0,2}(?:%s)\b")


def _not_short_of(*foods):
    """A guard: stand the row down when the line says the house has none of these.

    A guard rather than an `avoid` word, because the shortage and the food have to sit together
    in the line: `out of` in an avoid list stands the row down for "peas out of the bag", and
    `no` for "no need to thaw them first", which are both about cooking them.
    """
    pattern = re.compile(SHORT_OF_THE_HOUSE.pattern % "|".join(foods))

    def guard(understood):
        said = str((understood or {}).get("text") or "").lower()
        return not pattern.search(said)
    return guard


def _make_it(nouns, props):
    out = []
    for noun in nouns:
        for prop in props:
            # Only the ask that names the fault after the subject. "Make a thick sauce for pasta"
            # is a recipe for a thick sauce, not a complaint about a thin one, and the recipe
            # table answers it well, so the property-first form is deliberately not written out.
            # "Make the sauce thicker for pasta" is the recipe's line, not the fault's, so only the
            # plain subject is written out. "Make the gravy thick" reaches the gravy row, which
            # already answers the thickening.
            out.extend(("make " + noun + " " + prop, "make my " + noun + " " + prop))
    return tuple(out)


# How to keep a wedge of cheese is one question and what to do with the mould on it is another,
# and the mould answer was being given to the storage question: "how should i store cheese" opened
# with "Cut the mould off hard cheese with a good inch to spare". One row, because it is the same
# wedge in the same fridge, and the reading says which of the two the line asked.
_CHEESE_TROUBLE_WORDS = ("mould", "mouldy", "mold", "moldy", "gone off", "out of date", "off",
                         "smell", "smells", "smelt", "slimy", "ammonia", "blue", "green",
                         "fuzzy", "furry", "spots", "bits", "still ok", "ok to eat",
                         "safe to eat", "can i eat", "is it ok")


# The keeping of each kind, said for the kind a follow-up names: "its a brie" after the store
# question is a brie and not a wedge, and the row's one card said the same thing again, which the
# composer hands back as nothing new and the person hears a suggestion for dinner instead.
_CHEESE_KIND_KEEP = {
    "soft": "Soft cheese like brie or camembert keeps about a week once opened - wax paper, then "
            "loosely in a bag in the warmest part of the fridge - and a soft one that grows mould "
            "goes in the bin whole, because the threads run right through it.",
    "blue": "Blue cheese keeps about two weeks once opened, in wax paper in the warmest part of "
            "the fridge. The blue veins are meant to be there; green or white fuzz is not, and it "
            "does not come off a blue.",
    "hard": "Hard cheese like a cheddar keeps about two weeks once opened, wrapped in wax paper in "
            "the warmest part of the fridge, and it dries out before it spoils.",
}


def _the_kind_of_cheese_named(said):
    """Which kind of cheese the line names, or "" when it names none."""
    from .keeping import BLUE_CHEESES, CHEESE_NAMES, SOFT_CHEESES

    for kind, names in (("blue", BLUE_CHEESES), ("soft", SOFT_CHEESES)):
        if any(" %s" % name in said for name in names):
            return kind
    if any(" %s" % name in said for name in CHEESE_NAMES):
        return "hard"
    return ""


def _not_a_serving_frame(reading):
    """True unless the line asks what to put beside something.

    "what pairs best with blue cheese" is a dinner: the cheese row keeps the word "blue" for the
    veins going wrong, and it took the ask. A serving frame is a question about a plate, not about
    the wedge in the fridge, so the row stands down and the pairing rule answers.
    """
    from . import dishes
    text = str((reading or {}).get("clean") or (reading or {}).get("text") or "").lower()
    return not dishes.asks_for_a_side_of_a_food(text)


def _cheese_keep(memory, reading):
    """The mould verdict when the line is about the wedge going wrong, storage when it is not."""
    said = " %s " % str(reading.get("clean") or "").lower()
    if any(" %s " % word in said or said.strip().startswith(word)
           for word in _CHEESE_TROUBLE_WORDS):
        # The storage sentence stays on the end of the mould answer: it was the whole card, and
        # a line about the mould is the line that asked for both ("can i cut the mould off
        # cheese" wants the cut, and the wrap is what to do with the rest).
        return ("Cut the mould off hard cheese with a good inch to spare and it is fine to eat; "
                "bin soft cheese, cream cheese and anything grated that has mould on it. To keep "
                "the rest, wrap it in wax paper or baking paper and then loosely in a bag, and "
                "keep it in the warmest part of the fridge: cling film makes it sweat and go "
                "slimy.")
    # The length of each kind is in the sentence, because the line after this one is often the
    # other kind: "and the soft one" is answered by the sentence that names soft cheese, and
    # without one there was nothing new for the composer to hand the turn to, so it went to the
    # echo ("Got it - the soft one."). Soft keeps about a week and a hard wedge two, which is the
    # difference people are actually asking about.
    kind = _the_kind_of_cheese_named(said)
    if kind:
        # The line names the cheese, so the kind is known: it came up in the chat as "its a
        # brie", which is not a question the paper-and-bag card answers a second time.
        return _CHEESE_KIND_KEEP[kind]
    return ("To keep cheese, wrap it in wax paper or baking paper and then loosely in a bag, in "
            "the warmest part of the fridge. A hard wedge keeps about two weeks once opened. "
            "Soft cheese keeps about a week once opened, and cling film sweats it and makes it "
            "slimy, so leave it in the tub it came in.")


MAKE_IT_THICK = _make_it(("soup", "stew", "sauce", "gravy", "curry", "chilli", "casserole"),
                         ("thick", "thicker"))
_OATS_HEALTH = ("healthy", "healthier", "healthiest", "good for me", "good for you",
               "nutritious", "nutrition", "diet", "dieting", "slimming", "lose weight",
               "put on weight", "filling", "fattening", "calories", "sugar")


def _overnight_oats(memory, reading):
    """The recipe, or the health answer when the health is what was asked.

    "are overnight oats healthy" is not a question about how to make them, and a reply that
    starts with the ratio answers the wrong one. Same row, because it is the same breakfast.
    """
    said = str(reading.get("clean") or "").lower()
    if any(word in said for word in _OATS_HEALTH):
        return ("As healthy as what you put in the jar: oats are a slow-carb breakfast and the "
                "milk or yoghurt adds protein, so a portion with fruit keeps you full till lunch. "
                "The sugar comes from the honey, syrup and dried fruit, so go easy on those - and "
                "a shop-bought pot can carry a lot of it. Make it yourself and it is one of the "
                "better breakfasts going.")
    return _OVERNIGHT_OATS_RECIPE


_OVERNIGHT_OATS_RECIPE = (
    "Overnight oats are soaked in the fridge, not cooked: about 1 part oats to 1 to 1.5 parts "
    "milk or yoghurt in a jar, left 6 hours or overnight, then eaten cold with fruit. Rolled "
    "oats are the ones that work - steel-cut stay chewy and instant oats go to mush - and a "
    "spoon of chia or a grated apple thickens them. You do not need to soak oats before "
    "cooking porridge; 5 minutes in a pan does that.")



# A bake with no sugar in it is a different question from the recipe for it: every recipe
# below that holds sugar answers "how do i make sugar free cookies" with "100g of sugar" unless
# it stands down. The line is asking what sweetens the bake instead, which the swap-sugar and
# cut-down rows answer, so the sugar-carrying recipes stand down for these shapes. Written as
# a constant because the next recipe row that holds sugar wants the same words.
NO_SUGAR = ("sugar free", "sugar-free", "without sugar", "no sugar", "no added sugar",
            "sugar substitute", "sugar substitutes", "sweetener", "sweeteners")


# The milk in a cup of tea is three questions that arrive in the same words, and the answer has
# to lead with the half that was asked: "how much milk in a cup of tea" wants the amount and
# "what milk is best for tea" wants the kind, while "milk first or last" wants the order. The
# order and the kind are the answer the row always gave, kept word for word for the bare order
# question.
TEA_MILK_ORDER = (
    "Tea first, milk last, in a mug: you can see how strong the tea has got before you pour, and "
    "the leaves brew in water at full heat instead of water cooled by milk. Milk first is the old "
    "way with a pot and a thin china cup - a splash of milk stopped boiling water cracking the "
    "china, and it stretched a small amount of tea - so it is not wrong, just fussier, and the "
    "bottom of the cup ends up milky unless you stir.")
TEA_MILK_KIND = (
    "Semi-skimmed is the usual: whole milk tastes rounder, skimmed thinner, and both are fine. "
    "Of the plant milks, oat and soy are the closest to it.")
TEA_MILK_AMOUNT = (
    "A splash: about 15 to 30ml, a tablespoon or two, in a 250ml mug. Taste it at 10ml, because "
    "you cannot take it out, and a strong builder's tea takes more than a mild one.")
TEA_MILK_PLANT = (
    "Oat milk is the nearest to dairy in tea and the one that behaves best - the barista ones are "
    "made not to split. Soy is fine but can taste beany in a strong cup, almond is thin, and "
    "coconut changes the taste. Pour it in after the water and stir.")

# "how much" and "what milk" are the two halves that need their own lead. The words are whole
# words after the line is read, so "much" cannot come from "how much does a kettle cost" here:
# the row's key needs `tea` as well, and a price line has no tea in it.
TEA_MILK_AMOUNT_ASKS = ("how much milk", "much milk", "how many ml", "how many mls",
                        "how much of it", "quantity of milk", "how milky", "how strong")
TEA_MILK_KIND_ASKS = ("what milk", "which milk", "best milk", "what kind of milk",
                      "what type of milk", "milk is best", "milk should i use", "milk to use",
                      "milk do you use", "milk is good", "milk good in tea", "oat milk",
                      "soy milk", "soya milk", "almond milk", "plant milk", "skimmed milk",
                      "semi skimmed", "whole milk", "milky")

# The plant milks have a paragraph of their own: "is oat milk good in tea" is a question about
# that milk, not about which milk to keep in the fridge.
TEA_MILK_PLANT_SAID = ("oat milk", "soy milk", "soya milk", "almond milk", "plant milk",
                       "plant-based milk", "coconut milk", "nut milk")

# Naming the milk in a brew is only a question when the line asks one. A thread about a brew
# carried its words into the next line, so an answer to the offer of a cup - "milk and one
# sugar", "white with two", "milk no sugar" - met the bare `milk` of the key and was handed the
# whole order of a cup of tea. The words below are the asks this row answers; a preference has
# none of them and stays with the small talk that was already handling it.
TEA_MILK_ASK = ("how", "how much", "how many", "what", "which", "what's", "should",
                "should i", "can i", "could i", "do i", "does", "is", "are", "would",
                "will", "best", "first", "last", "before", "after", "order", "stir",
                "go in", "goes in", "put in", "instead",
                # the brew phrases are asks in their own right: "milk in tea", "milk in a cup
                # of tea" and "oat milk in tea" say what they are about with no question word
                # at all, so they have to be here or the answer they had is lost.
                "in tea", "in my tea", "in the tea", "in a cup of tea", "in a mug of tea",
                "in a brew", "in my brew", "for tea", "for my tea", "for a cup of tea",
                "with tea", "with my tea", "with a cup of tea")


# A brew is not a pan. These dish words stand the row aside when the line itself names the
# dish ("does the milk go in first for scrambled eggs"), and `_a_thread_of_a_pan` does the same
# for a thread where the dish was named a turn earlier: "im making scrambled eggs" and then
# "does the milk go in first" carries only the milk by the second line, and the order of a cup
# of tea is the wrong answer to a pan of eggs. "Sugar" is not one of them: "milk and sugar" is
# how somebody takes a cup.
_TEA_MILK_DISH = ("egg", "eggs", "scrambled", "omelette", "omelettes", "flour", "batter",
                  "pancake", "pancakes", "dough", "biscuit", "biscuits", "chocolate",
                  "cocoa", "butter", "yoghurt", "yogurt", "gravy", "soup", "dumpling",
                  "dumplings", "bake", "baking", "baked", "filling", "icing", "frosting",
                  "meringue")

# The pans a milk question turns up in mid-recipe. Only the thread guard reads these: a line
# that names one of them is already turned away by the row's own `avoid` ("porridge", "sauce",
# "mash", "cake" ...), and "oats" there would take "is oat milk good in tea" with it.
_TEA_MILK_PAN = _TEA_MILK_DISH + ("porridge", "oats", "oatmeal", "custard", "mash", "mashing",
                                  "sauce", "roux", "curry", "stew", "souffle", "quiche")

# What makes a line about the drink when the line does not say the word "tea": the order of a
# cup arrives as "milk first or last", which names nothing else at all.
_TEA_MILK_BREW = ("tea", "teas", "teabag", "teabags", "tea bag", "tea bags", "brew",
                  "brews", "brewing", "cuppa", "cuppas", "kettle", "teapot", "pot of tea",
                  "cup of tea", "mug of tea", "mug", "cup", "hot water")


def _a_thread_of_a_pan(memory):
    """True when the turns just before this one were about a dish, not about a brew."""
    if not isinstance(memory, dict):
        return False
    words = []
    for turn in (memory.get("topics") or [])[-2:]:        # this turn is not in topics yet
        if not isinstance(turn, dict):
            continue
        words.extend(turn.get("words") or ())
        words.extend(str(turn.get("text") or "").split())
    plan = (memory.get("user") or {}).get("plan")
    if isinstance(plan, str):
        words.extend(plan.split())
    low = " " + " ".join(str(word).lower() for word in words) + " "
    return any(f" {dish} " in low for dish in _TEA_MILK_PAN)


# The milk in a cup of coffee: the kind asked about, the amount, and why a milk splits in it. Three
# questions that arrive on the same two words, so the half that was asked leads.
MILK_FOR_COFFEE_KIND = (
    "In coffee, oat is the plant milk that behaves best - the barista cartons are made not to "
    "split, and they foam. Soy is next and tastes slightly beany in a long black; almond is thin "
    "and can separate in hot coffee; coconut changes the taste of the cup. Whole milk foams the "
    "thickest and semi-skimmed is the usual for a flat white, and a splash of milk in black coffee "
    "takes the edge off without much milk at all.")
MILK_FOR_COFFEE_AMOUNT = (
    "A splash: about 20 to 40ml in a mug of filter coffee, a tablespoon or two, and 100 to 150ml "
    "in a latte or a cappuccino, where the milk is most of the cup. Pour it in after the coffee so "
    "you can see how dark it has gone, and heat the milk for a milky drink - cold milk takes the "
    "heat out of a small cup.")
MILK_FOR_COFFEE_SPLIT = (
    "Milk splits in coffee because the coffee is hot and acidic: the acid takes the milk towards "
    "the point where its proteins clump, and the heat sets the clumps, which is why the specks "
    "appear in a long black and not in a latte. Let the coffee cool for a minute before the milk "
    "goes in, use the fresher bottle, and use a barista plant milk if it keeps happening - those "
    "have oil and a stabiliser added so they hold together.")


def _the_milk_for_a_coffee(memory, understood):
    """The kind of milk for a coffee, how much of it, or why it splits - whichever was asked."""
    text = " " + ((understood or {}).get("clean") or "").lower() + " "
    # " split " as well as " splits " and " splitting ": "does milk split in coffee" is asked
    # with the bare verb, and it was falling through to the ranking of plant milks - an answer
    # about which carton to take, given about the cow's milk already in the cup.
    if any(said in text for said in ("curdl", " split ", " split,", " splits ", " splitting ",
                                     " separated ", " separates ", " gone lumpy ",
                                     " lumps in ")):
        return MILK_FOR_COFFEE_SPLIT
    if any(said in text for said in ("how much", "how many ml", "how many mls", "how milky",
                                     "much milk", "much of it")):
        return MILK_FOR_COFFEE_AMOUNT
    return MILK_FOR_COFFEE_KIND


def _tea_milk_reply(memory, understood):
    """The amount, the kind, the order or the plant milk, whichever the line asked about.

    One answer, not the whole page: the first half the line asked about leads, and only a
    second question in the same line ("what milk and how much") gets a second paragraph.
    """
    text = " " + ((understood or {}).get("clean") or "").lower() + " "
    if not any(f" {word} " in text for word in _TEA_MILK_BREW) and _a_thread_of_a_pan(memory):
        return None                     # the pan the thread is about is not a cup of tea
    amount = any(ask in text for ask in TEA_MILK_AMOUNT_ASKS)
    kind = any(ask in text for ask in TEA_MILK_KIND_ASKS)
    plant = any(f" {said} " in text for said in TEA_MILK_PLANT_SAID)
    if amount:
        return TEA_MILK_AMOUNT + " " + (TEA_MILK_PLANT if plant else TEA_MILK_KIND)
    if kind:
        return TEA_MILK_KIND + (" " + TEA_MILK_PLANT if plant else "")
    if plant:
        return TEA_MILK_PLANT
    return TEA_MILK_ORDER

# A meal said as a meal, not a meal mentioned after the ingredient: "what can i use instead of
# cream for dinner" is still a swap (the cream is in the sauce), while "im egg free what can i have
# for breakfast" is a breakfast question. So the ask for the meal has to be in the line, not the
# word "dinner" on its own.
# The meals whose answers read the diet: breakfast and lunch have a table each that a diet is
# read against (`cooking._breakfast_ideas`, `cooking._lunch_ideas`), and the dinner list and the
# dish table are filtered by it too, so a person who cannot eat the thing being swapped gets a
# meal instead of the card. Each phrase is a whole ask ("what can i have for breakfast"), never a
# bare "for breakfast": "what can i use instead of milk for breakfast" is a swap question with a
# meal on the end, and the card is the right answer to it.
SWAP_NOT_A_MEAL = ("what can i have for breakfast", "what should i have for breakfast",
                   "what shall i have for breakfast", "what can i make for breakfast",
                   "what can i eat for breakfast", "what to have for breakfast",
                   "ideas for breakfast", "breakfast ideas", "breakfast idea",
                   "what can i have for lunch", "what should i have for lunch",
                   "what shall i have for lunch", "what can i make for lunch",
                   "what can i eat for lunch", "what to have for lunch",
                   "ideas for lunch", "lunch ideas", "packed lunch", "lunchbox",
                   "lunch box",
                   "what can i have for dinner", "what should i have for dinner",
                   "what shall i have for dinner", "what can i make for dinner",
                   "what can i eat for dinner", "what to have for dinner",
                   "what can i have for tea", "what should i have for tea",
                   "what can i make for tea", "what can i eat for tea", "what to have for tea",
                   "what can i have for supper", "what can i make for supper",
                   "ideas for dinner", "dinner ideas", "ideas for tea", "tea ideas",
                   "ideas for supper")


# "Without" asks for two different things. It asks for a stand-in when what follows is the
# missing ingredient - "how do i bake a cake without eggs", "gravy without flour" - and it
# describes a step when what follows is an outcome - "how do i fry an egg without breaking the
# yolk", "how do i cook rice without it going mushy", "roast potatoes without them sticking".
# A key word cannot tell those apart: "egg" and "without" are both in the yolk line, so the
# stand-in card answered a frying question with "one egg becomes 60g of yoghurt". English does
# tell them apart, because an outcome is said with a gerund ("breaking", "going", "sticking")
# and a missing ingredient is said with a noun ("eggs", "flour"). The verbs that mean "which
# contains" are the exception, since they are gerunds too and are still asking for a stand-in:
# "bake a cake without using eggs".
_A_SUPPLY_VERB = ("using", "adding", "putting", "having", "eating", "including",
                  "containing", "needing", "buying", "serving", "cooking", "mixing")
# The words that can sit between "without" and the outcome: "without it breaking", "without the
# yolk breaking", "without them going soggy". A pronoun or a determiner means the gerund two or
# three words later is about that thing, which is a step; "eggs" straight after "without" is a
# missing ingredient and never takes one of these.
# Sticking is the one outcome that already has cards reading the clause itself ("Get the pan
# properly hot with the oil already in it", the pasta and the rice beside it), and those answer a
# "without them sticking" line better than the dish does, so this guard leaves it alone.
_A_ITS_OWN_FAULT = ("sticking", "stick")
_A_WITHOUT_SUBJECT = ("it", "them", "that", "this", "they", "you", "me", "him", "her",
                      "the", "a", "an", "my", "his", "its", "their", "your", "our")


def _an_outcome(word):
    """True for a word that names what must not happen: "breaking", "going", "splitting"."""
    if word in _A_ITS_OWN_FAULT:
        return False                    # a card of its own reads that clause and answers it
    return word.endswith("ing") and word not in _A_SUPPLY_VERB


def _a_swap_and_not_a_step(understood):
    """False when the line's only "without" describes an outcome, so the swap is not asked."""
    clean = str((understood or {}).get("clean") or "")
    words = re.sub(r"[^a-z0-9' ]+", " ", clean.lower()).split()
    seen = False
    for index, word in enumerate(words):
        if word != "without":
            continue
        seen = True
        after = words[index + 1:index + 4]
        if not after:
            continue                    # "without" on its own says nothing a swap row can use
        if after[0] in _A_WITHOUT_SUBJECT:
            if any(_an_outcome(word) for word in after[1:]):
                continue                # "without it breaking": a step, so keep looking
            return True                 # "without the eggs": a thing is missing
        if _an_outcome(after[0]):
            continue                    # "without breaking the yolk": a step
        return True                     # "without eggs": a thing is missing
    return not seen                      # another ask word in the key did the work


def _swap(entry_id, key, reply, **rest):
    """A swap entry that keeps out of the meals and out of the steps.

    The stand-in card is about an ingredient inside a bake or a sauce, so a line that asks what
    to have for a meal is answered by the meal ideas instead, whatever the ingredient word in it,
    and a line that says what must not happen ("without breaking the yolk") is a cooking step and
    not a shortage. A couple of these carry their own `avoid` as well, and all of it has to hold;
    a guard of their own is combined with this one rather than replaced.
    """
    avoid = tuple(rest.pop("avoid", ()) or ())
    guard = rest.pop("guard", None)
    if guard is not None:
        rest["guard"] = lambda understood: _a_swap_and_not_a_step(understood) and guard(understood)
    else:
        rest["guard"] = _a_swap_and_not_a_step
    return entry(entry_id, key, reply, avoid=SWAP_NOT_A_MEAL + avoid, **rest)


# A dish is not the answer when the line says one of its ingredients is missing. The cake row
# keys on the dish and the verb, so "how do i make a cake without using eggs" was handed the
# method - "weigh 4 eggs in their shells" - which is the one thing the person said they could not
# use. Every stand-in row already answers "without", so a line that says "without" and names an
# ingredient the dish needs is a substitution question and the dish card stands down; the marker
# is the one word both sides read, and "no" is left out on purpose because no stand-in row keys
# on it ("a cake with no butter" is still a card of its own, and a punt would be no better).


def _said_to_be_missing(clean):
    """The words the line says are not there: the three after "without"."""
    words = re.sub(r"[^a-z0-9' ]+", " ", str(clean or "").lower()).split()
    missing = set()
    for index, word in enumerate(words):
        if word == "without":
            missing.update(words[index + 1:index + 4])
    return missing


def _leaves_out(*ingredients):
    """A dish card stands down when the line says an ingredient it needs is not there.

    Only the ingredients the card's own method would reach for are named, so a line about a
    missing tin, oven or hour still gets the method: "how do i make a cake without a tin" is a
    cake question, and "how do i make a cake without using eggs" is a substitution one.
    """
    stems = set()
    for one in ingredients:
        stems.add(one)
        stems.add(one[:-1] if one.endswith("s") else one + "s")

    def guard(understood):
        said = _said_to_be_missing((understood or {}).get("clean"))
        return not any(word in stems for word in said)

    return guard

# "Is it ok to eat bread past the date" asks for a verdict, and the keeping card answers with
# where to store it, so a person is told the paper bag and never whether the loaf is safe. The
# pack date is the reason the question is asked, so on those words the reply leads with the
# verdict and keeps the storage tip second; every other keeping question gets the tip first.
BREAD_KEEP = ("Keep bread at room temperature in a paper bag or a bread bin, not the fridge: the "
              "cold makes it go stale faster. Freeze what you won't eat in two days, sliced, and "
              "bring a stale loaf back with a splash of water and 5 minutes in a hot oven.")
# "How long does bread keep" and "how long does a loaf last" ask for the days, and the keeping
# card answered with where to store it and never a number: a person was told the paper bag and
# left to guess whether their loaf had another day in it. Cooked chicken, rice, milk, hummus and
# an open jar all lead with the figure; the loaf was the one keeping row that did not. So a
# duration ask gets the lifespan first and the storage after it, and every other keeping line
# (mouldy, fresh for longer, the bin or the fridge) still opens on the tip.
BREAD_LIFE = ("A loaf keeps 3 to 4 days in a paper bag or a bread bin at room temperature, and 3 "
              "months sliced in the freezer. The fridge stales it faster than the cupboard, so "
              "leave it out and cut slices as you need them, freeze what you won't eat in two "
              "days, and a stale loaf comes back with a splash of water and 5 minutes in a hot "
              "oven.")
BREAD_DATED = ("Bread a day or two past the date is fine if it looks and smells all right: a loaf goes "
               "dry or hard before it goes unsafe, and 5 minutes in a hot oven brings it back. "
               "Don't cut the mould off and eat the rest - the threads reach further than the "
               "green you can see, so bin that loaf. Keep it in a paper bag or a bin at room "
               "temperature rather than the fridge, and freeze half sliced.")


# "Season" is also a run of episodes, a league or a gym's year, and the two pan rows below key on
# it. `season-new-pan` has "new" among its pan words, so "when does the new season start" scored on
# "season" and "new" and was told to wash the factory oil off. A season of a show is not a pan.
_A_SEASON_OF_A_SHOW = re.compile(
    r"\b(?:season\s*(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)|this season"
    r"|next season|last season|new season|final season|first season|second season"
    r"|episodes?|series|box set|binge|the show|on tv|on netflix|netflix|streaming"
    r"|football|cricket|rugby|premier league|the league|leagues|fixtures?|match|matches"
    r"|team|teams|gym|what should i watch)\b")


def _not_a_season_of_a_show(understood):
    """True unless "season" here is episodes, a league or a gym: then a pan is not the answer."""
    said = " " + " ".join(str((understood or {}).get(key) or "")
                          for key in ("clean", "norm_text", "norm")).lower() + " "
    return not _A_SEASON_OF_A_SHOW.search(said)


def _bread_kept(memory, understood):
    """The verdict for "is it ok to eat bread past the date", the paper bag for the rest."""
    said = " ".join(str((understood or {}).get(key) or "")
                    for key in ("clean", "norm_text", "norm")).lower()
    if any(word in said for word in PACK_DATE) or "the date" in said:
        return BREAD_DATED
    # "how long does a loaf keep" is the number of days, so the number comes first; the rest of
    # the keeping words are the storage tip, which is the answer to "how do i keep bread fresh".
    if re.search(r"\bhow long\b|\bhow many days\b|\bhow many weeks\b"
                 r"|\bshelf[- ]?life\b|\blasts? for\b", said):
        return BREAD_LIFE
    return BREAD_KEEP
# "What can i put in a lunchbox that isnt sandwiches" is asked by every parent of a fussy eater,
# and the lunch rows had no answer for it: `lunch-ideas` stands down for the food the line names
# ("a line that names the food is answered better by that food's own entry"), and here the named
# food is the one being turned down, so nothing answered and the person got a search hedge. The
# words below say "not bread" rather than "a diet", so they are their own row and their own
# answer - a lunch that carries without bread instead of a sandwich with the bread taken out.
NO_SANDWICH = ("that isnt a sandwich", "that isnt sandwiches", "that isnt a sandwich or",
               "that isint a sandwich", "that is not a sandwich", "that is not sandwiches",
               "that isnt just sandwiches", "isnt a sandwich", "isnt sandwiches",
               "isn't a sandwich", "isn't sandwiches", "not a sandwich", "not sandwiches",
               "no sandwich", "no sandwiches", "without a sandwich", "without sandwiches",
               "with no sandwiches", "with no bread", "not bread", "no bread", "without bread",
               "other than sandwiches", "other than a sandwich", "besides sandwiches",
               "besides a sandwich", "apart from sandwiches", "apart from a sandwich",
               "instead of sandwiches", "instead of a sandwich", "not always sandwiches",
               "sick of sandwiches", "bored of sandwiches", "hates sandwiches",
               "wont eat sandwiches", "won't eat sandwiches", "doesnt want sandwiches",
               "wont eat bread", "won't eat bread", "doesnt eat bread", "does not eat bread",
               "refuses bread", "wont eat a sandwich", "wont eat a sandwich or",
               "hates bread", "no more sandwiches", "sick of bread", "bored of bread",
               "off sandwiches", "gone off sandwiches")


# The no-sandwich lunchbox, as a table like the snack table above: the chat may already know the
# child cannot have dairy, and the whole card was thrown away because it offered cheese cubes,
# leaving a parent who had just said "he wont eat sandwiches" with a repeat of the sandwich line.
# Each option carries the foods in its own words, so `_bans_of` and the allergy about somebody
# else leave out that option and keep the rest of the list.
_NO_SANDWICH_KID_ITEMS = (
    ("cooked pasta or rice from last night's dinner in a tub", "gluten pasta"),
    ("cheese cubes", "dairy cheese"),
    ("a boiled egg", "egg"),
    ("crackers or oatcakes", "gluten cracker crackers"),
    ("veg sticks with hummus", "sesame hummus"),
    ("a yoghurt", "dairy yoghurt"),
    ("some fruit", ""),
)
_NO_SANDWICH_ADULT_ITEMS = (
    ("last night's dinner in a tub", ""),
    ("pasta or rice salad", "gluten pasta"),
    ("cold chicken", "meat chicken"),
    ("cheese with oatcakes", "dairy cheese gluten oatcake oatcakes"),
    ("a boiled egg", "egg"),
    ("veg sticks and hummus", "sesame hummus"),
    ("soup in a flask", ""),
    ("yoghurt and fruit", "dairy yoghurt"),
    ("fruit", ""),
)


def _a_lunchbox_without(items, banned):
    """The options that name nothing the chat has ruled out, in the order they were written.

    Whatever survives is kept, however few of them there are. Reading the raw list again when
    fewer than two were left dropped every ban exactly when the bans bit hardest: a child
    allergic to dairy, egg, gluten and sesame was offered "cheese cubes and a boiled egg". A
    list with nothing left comes back empty, and the caller says the list is short rather than
    reading the banned food out.
    """
    return [food for food, words in items if not (set(words.split()) & banned)]


# Who a lunch is for is settled by the chat, not only by the line in hand. "my son is allergic
# to dairy" then "what can i put in his lunchbox" was read as an adult's lunch, because the second
# line names no child, and a seven year old was offered cold chicken and soup in a flask. The
# store already keeps the person the chat is about, so the child list reads that as well.
CHILD_NAMES = frozenset((
    "son", "daughter", "child", "children", "kid", "kids", "baby", "toddler", "boy", "girl",
    "stepson", "stepdaughter", "grandson", "granddaughter", "nephew", "niece", "schoolchild",
    "schoolboy", "schoolgirl", "little one", "youngest", "eldest"))
# A lunchbox is a child's lunch in the way a packed lunch is not: no adult says "my lunchbox"
# about the tub in their bag. "school lunch" is in the kid words of the card already.
CHILDS_LUNCH_WORDS = ("lunchbox", "lunchboxes", "lunch box", "lunch boxes", "pack up",
                      "packed up", "his lunch", "her lunch", "his bag", "her bag")


def _lunch_is_for_a_child(memory, said):
    """Whether the lunch in hand is a child's, from the line and from the person the chat is on."""
    whole = set(str(said or "").split())
    # whole words, not substrings: "son" inside "person" and "season" said nothing about a child
    if whole & CHILD_NAMES:
        return True
    if any(phrase in said for phrase in CHILDS_LUNCH_WORDS):
        return True
    if not isinstance(memory, dict):
        return False
    person = memory.get("person")
    who = str((person or {}).get("who") or "").strip().lower() if isinstance(person, dict) else ""
    if who in CHILD_NAMES:
        return True
    people = (memory.get("user") or {}).get("people") if isinstance(memory.get("user"), dict) else ()
    for one in people or ():
        if str(one).strip().lower() in CHILD_NAMES:
            return True
    return False


def _said_no_sandwich(memory):
    """The chat has already turned a sandwich down, so the lunch after it is the same lunch.

    "he wont eat sandwiches" then "what can i put in his lunchbox" got the sandwich sentence back,
    which is the one thing the chat had ruled out. Only the last few turns are read: a person who
    said it ten turns ago and has asked about something else since is not still on it.
    """
    if not isinstance(memory, dict):
        return False
    turns = memory.get("turns")
    for turn in list(turns or [])[-4:]:
        line = str((turn or {}).get("user") if isinstance(turn, dict) else "").lower()
        if any(phrase in line for phrase in NO_SANDWICH):
            return True
    return False


def _lunch_ideas_after_a_no(memory, understood):
    """The packed lunch, unless the chat has already turned a sandwich down.

    The no-sandwich card is keyed on the line ("what can i put in a lunchbox that isnt
    sandwiches"), so the lunch asked for two turns later - "what can i put in his lunchbox" - was
    answered with the sandwich sentence the chat had just ruled out. A fact said earlier outlives
    the line it was said on, so the card reads the chat too.
    """
    reply = _lunch_ideas(memory, understood)
    # The card is only replaced when it puts a sandwich back in front of them: a person who cannot
    # have gluten already gets a lunch that says "not a sandwich", and that answer knows their diet
    # better than the plain table does, so it stays.
    offers_one = "sandwich" in reply.lower() and "not a sandwich" not in reply.lower()
    if offers_one and _said_no_sandwich(memory):
        return _no_sandwich_lunch(memory, understood)
    return reply


def _no_sandwich_lunch(memory, understood):
    """A packed lunch that is not a sandwich, said as what to put in it."""
    said = " ".join(str(word) for word in ((understood or {}).get("words") or ())).lower()
    # A lunch for a child is the same list with the plain things said first: a seven year old
    # who has just been offered a sandwich-free lunch is not going to eat a rice salad.
    kid = _lunch_is_for_a_child(memory, said) or any(
        word in said for word in ("year old", "nursery", "school", "fussy", "picky"))
    user = (memory or {}).get("user") if isinstance(memory, dict) else None
    banned = set(_bans_of(user)) | set(avoids_for_the_one_talked_about(memory))
    if banned:
        for said_allergy in (user or {}).get("allergies") or ():
            for word in str(said_allergy).lower().replace(",", " ").split():
                tag = _SNACK_FAMILY_OF.get(word)
                if tag:
                    banned.add(tag)
        kept = _a_lunchbox_without(_NO_SANDWICH_KID_ITEMS if kid else _NO_SANDWICH_ADULT_ITEMS,
                                  banned)
        if not kept:
            # Nothing on the list is safe for this person. Naming a food here would put back the
            # thing the filter just took out, so the shape of the lunch is said and no food is.
            who = "he" if kid else "you"
            return ("With that much ruled out there is nothing on the usual list to name: build "
                    "the lunch from what " + who + " already eats at home, a tub of dinner kept "
                    "cold and a drink, and check the label on every packet you use. "
                    + ("A flask of soup or leftovers does the same job and is often the easiest "
                       "with a fussy eater." if kid else ""))
        listed = ", ".join(kept[:-1]) + " and " + kept[-1] if len(kept) > 1 else kept[0]
        how_many = ("any three of those and a drink is a lunch" if len(kept) >= 3
                    else "both of those and a drink is a lunch" if len(kept) == 2
                    else "that and a drink is a lunch")
        if kid:
            return ("For a lunchbox with no sandwich: " + listed + " - " + how_many + ". A flask "
                    "of soup or leftovers does the same job and is often the easiest with a "
                    "fussy eater, because it is food they already eat at home.")
        return ("For a packed lunch with no sandwich: " + listed + " travel" +
                ("s" if len(kept) == 1 else "") + " well. " + how_many.capitalize() + ", and the "
                "tub of dinner is the one that keeps you full until tea.")
    if kid:
        return ("For a lunchbox with no sandwich: cooked pasta or rice from last night's dinner "
                "in a tub, cheese cubes or a boiled egg with crackers or oatcakes, veg sticks "
                "with hummus, a yoghurt and some fruit - any three of those and a drink is a "
                "lunch. A flask of soup or leftovers does the same job and is often the easiest "
                "with a fussy eater, because it is food they already eat at home.")
    return ("For a packed lunch with no sandwich: last night's dinner in a tub is the easiest, "
            "and pasta or rice salad, cold chicken or cheese with oatcakes, a boiled egg, veg "
            "sticks and hummus, soup in a flask, yoghurt and fruit all travel well. Any three of "
            "those plus a drink is a lunch, and the tub of dinner is the one that keeps you full "
            "until tea.")


def _coffee_late(memory, reading):
    """The late cup gets its answer first; the jitters get the explanation.

    "Should i have a coffee this late" and "is it too late for coffee" ask for a decision, and
    main's answer - which opens with how caffeine peaks and clears - left the person to work it
    out. "Coffee makes me anxious" is the other question the same row answers, and being told the
    hour to stop by is no answer to it, so the two shapes are phrased separately.
    """
    clean = (reading.get("clean") or "").lower()
    # "how long before bed should i stop drinking coffee" is asking for the cut-off hour, and
    # the yes-no sentence below told them it was too late instead of when it is not.
    if re.search(r"\bhow long\b|\bhow many hours\b|\bwhat time\b|\bwhen should i stop\b|"
                 r"\bstop drinking\b|\bcut off\b|\blast (?:cup|coffee)\b|\bhow late\b|"
                 # "is coffee before bed a bad idea" is the same cut-off question, and the
                 # yes-no sentence read as an argument with a time it had already assumed
                 r"\bbefore bed\b|\bbedtime\b|\bbefore sleep\b", clean):
        return ("Stop by early afternoon, and count back: caffeine's half-life is about five "
                "hours, so half a 4pm cup is still in you at 9pm and a quarter of it at 2am. If "
                "you are in bed at eleven, a last full cup around 2pm leaves almost nothing by "
                "then; after that make it decaf, which has about 2mg a cup against 80.")
    late = ("late", "tonight", "this evening", "in the evening", "this afternoon",
            "in the afternoon", "before bed", "bedtime", "pm", "at night", "night")
    if any(word in clean for word in late):
        # "should i have one" wants a no and "is it too late" wants a yes: the same sentence
        # answered both, so the permission question read as permission.
        if re.search(r"\b(?:should|shall|can|could|may)\s+(?:i|we)\b"
                     r"|\b(?:is|would)\s+it\s+(?:ok|okay|alright|fine|bad|a\s+bad\s+idea)\b"
                     r"|\bdo\s+i\s+dare\b", clean):
            return ("No, not if you want to sleep: half the caffeine is still there five or six "
                    "hours later, so a 4pm cup can still be working at midnight. Keep to one or "
                    "two cups a day, stop by early afternoon, make the afternoon one decaf, and "
                    "eat something with it. Palpitations, shakiness or panic that come with "
                    "caffeine are worth mentioning to a GP, especially with chest pain or "
                    "breathlessness.")
        return ("Yes, too late if you want to sleep at a normal hour: half the caffeine is still "
                "there five or six hours later, so a 4pm coffee can still be working at "
                "midnight. Keep to one or two cups a day, stop by early afternoon, make the "
                "afternoon one decaf, and eat something with it. Palpitations, shakiness or panic "
                "that come with caffeine are worth mentioning to a GP, especially with chest pain "
                "or breathlessness.")
    return ("It is the caffeine: it peaks about half an hour after the cup and takes five or six "
            "hours to leave your system, so a 4pm coffee can still be in you at midnight. Keep to "
            "one or two cups, stop by early afternoon, make the afternoon one decaf, and eat "
            "something with it. Palpitations, shakiness or panic that come with caffeine are worth "
            "mentioning to a GP, especially with chest pain or breathlessness.")

# The words that ask how long something keeps, for the rows that carry a class of dish rather than
# one dish. They are the same words the keeping table has always been keyed on.
# The words that put a line back in the oven or the freezer rather than in the fridge: a cooking
# time, a recipe, a how-to, a freeze. A dish's own cooking time is its method's answer, not this.
NOT_A_KEEPING_ASK = ("how do i", "how to", "recipe", "recipes", "what can i make",
                     "what can i do", "how long to cook", "how long to bake", "how long in the",
                     "take to cook", "take to bake", "cooking time", "bake", "baking", "oven",
                     "boil", "fry", "roast", "cook", "cooking", "freeze", "freezer", "frozen",
                     "defrost", "thaw", "thawing", "reheat",
                     # A keeping question asks for a window, and these ask about the food:
                     # "is paella good for you", "is quinoa good for you" and "is risotto safe
                     # to eat when pregnant" are nutrition and safety lines, and a storage window
                     # is the wrong card for them.
                     "good for you", "healthy", "unhealthy", "fattening", "calories",
                     "how many calories", "pregnant", "pregnancy", "safe in pregnancy")

# The dishes below are a class rather than a table, and "how long does quinoa take" is the other
# clock: the person has the quinoa in the pan and wants the twelve to fifteen minutes, and the row
# gave them the days a cooked dish keeps. The shape cannot go in the avoid list above, because
# "take" is the same word in the spoilage sense - "how long does quinoa take to go off" wants the
# keeping window, and putting "take" in the avoid took that answer away with it. So the shape is a
# guard, which reads the line in order: how long the thing takes, and nothing said about how it is
# kept.
_COOKING_CLOCK = re.compile(r"\bhow long\b[^.?!]*?\btak(?:e|es|en|ing)\b")
_A_KEPT_THING = re.compile(
    r"\b(?:keep|keeps|keeping|kept|last|lasts|lasting|fridge|freezer|freeze|frozen|store|stored|"
    r"storage|shelf life|left out|left over|leftover|still (?:ok|okay|good|safe|fine)|"
    r"safe to eat|use by|go off|goes off|going off|gone off|go bad|goes bad|went bad|"
    r"out of date)\b")


# The avoid list above carries "what can i make" and "what can i do", and they do not catch a
# line that asks them: the frame words ("what", "can") are emptied out before a row is weighed, so
# "i have leftover quinoa what can i make" still reached the keeping row and was told the days it
# keeps when the use-up answer is the one they asked for. The ask is a shape, so it is read from
# the line: a question about what to make, cook or do with the food is not a keeping question.
_MAKE_IT_ASK = re.compile(
    r"\b(?:what (?:can|should|shall) i (?:make|cook|do|have)|what to (?:make|cook|do)|"
    r"what else can i (?:make|cook)|ideas (?:for|with)|something (?:for|with)|"
    r"use (?:it )?up|using (?:it )?up|use up the|recipe|recipes)\b")


def _not_a_make_it_ask(understood):
    """True unless the line asks what to make or do with the food rather than how it keeps."""
    text = str((understood or {}).get("clean") or "").lower()
    return not _MAKE_IT_ASK.search(text)


def _not_a_cooking_time(understood):
    """True unless the line asks how long a dish takes, saying nothing about how it is kept.

    "how long does quinoa take" was answered with "That keeps 3 to 4 days in the fridge once it is
    cooked", which is the wrong clock: the pan is on the hob (#7032's class rows, whose avoid list
    catches "how long does couscous take to cook" by the word "cook" and not the shorter ask).
    A line that says how the food is kept - "keep", "last", "in the fridge", "still good", "go
    off" - keeps the keeping answer whatever else it says.
    """
    if not _not_a_make_it_ask(understood):
        return False
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if not words:
        return True
    joined = " ".join(words)
    if not _COOKING_CLOCK.search(joined):
        return True
    return bool(_A_KEPT_THING.search(joined))


KEEPING_WORDS = ("how long", "keep", "keeps", "keeping", "kept", "last", "lasts", "lasting",
                 "fridge", "freezer", "freeze", "frozen", "store", "stored",
                 "storage", "shelf life", "shelf-life", "still good",
                 # "safe" and "good for" on their own are nutrition asks, and "day"/"days"
                 # on their own is "i eat three eggs a day": the keeping sense is the compound,
                 # "safe to eat" and "day old".
                 "safe to eat", "day old", "days old",
                 "how many days", "left over", "leftover")

# "How do i store milk" and "how long does milk keep" are one question and one row, and the
# store shapes were missing from the key words of the rows written before this: "how do i store
# milk" was a shrug while "how long does milk keep" answered, and the same for broccoli. The
# words here are the ones people type, which the keeping table did not all have: "store",
# "storing" and "how do i store" reached nothing at all.
STORE_ASKS = ("store", "stores", "storing", "stored", "storage",
              "how do i store", "how should i store", "how do you store", "how to store",
              "best way to store", "where do i keep", "where should i keep",
              "keep it fresh", "keep them fresh", "keep fresh", "stays fresh",
              "stay fresh", "keeps fresh")

# A store question about milk asks how to keep it and a gone-off milk question asks whether to
# bin it, and one card answers both: it leads with whichever the line asked. The baby milk words
# are here so a bottle of breast milk or made-up formula never gets the carton's five days.
_BREAST_MILK = ("breast milk", "breast", "expressed", "baby milk", "bottle of milk",
                "baby bottle", "babies bottle")


def _milk_keep(memory, understood):
    """A store question leads with the keeping; a gone-off milk question leads with the bin."""
    said = " %s " % " ".join(str((understood or {}).get(key) or "")
                             for key in ("clean", "norm_text", "norm")).lower()
    if "formula" in said or "made up" in said or "made-up" in said:
        # powder in water is not a carton: the clock starts when the powder goes in, and what is
        # left in the bottle after a feed is not kept at all
        return ("Made-up formula is good for 2 hours at room temperature and 24 hours in the "
                "fridge, and the clock starts when the powder goes in - throw away whatever is "
                "left in the bottle after a feed.")
    if any(word in said for word in _BREAST_MILK):
        # a bottle of expressed milk has its own hours, and "once opened" means nothing for it:
        # the carton's five days is the wrong number for it in both directions
        return ("Expressed breast milk keeps about 4 hours at room temperature, up to 4 days at "
                "the back of the fridge, and 6 months in the freezer; once thawed it is good for "
                "24 hours in the fridge and must not be refrozen.")
    keeping = ("Once opened, keep milk in the fridge and use it within about 5 days; the date on "
               "the carton is about quality, not safety, so milk that has been kept cold is fine a "
               "day or two past it.")
    spoilt = "If milk smells or tastes sour, bin it, whatever the date says."
    if "fresh" in said or any(shape in said for shape in STORE_ASKS):
        return keeping + " " + spoilt
    return spoilt + " " + keeping


# "keeps" and "how long" are two different readings of one cake. A cake that keeps sinking is a
# fault; a cake that keeps 2 days is a keeping question. _BAKE_KEEPING holds the bare verbs, which
# as an avoid is wide enough to veto every "my cake keeps sinking", "my sponge keeps collapsing"
# line the fault answer is for - so the fault row takes the shapes and the place words only.
_BAKE_KEEPING_SHAPED = tuple(word for word in _BAKE_KEEPING
                             if word not in ("keep", "keeps", "keeping", "kept", "last",
                                             "lasts")) + _BAKE_KEEP_SHAPES
# A drink is a drink. "how much tea is too much" is the caffeine limit, not a pot that
# overflowed, and `made-too-much` took it because "tea" is in its key as the evening meal and
# "too much" is its key word. A cup and a pot are told apart by what else the line says: a
# measure or a how-much word means a dose, and a cooking verb means there is food left over.
_DRINK_NAMES = ("tea", "teas", "coffee", "coffees", "espresso", "caffeine", "energy drink",
                "energy drinks", "cola", "coke", "matcha", "chai", "green tea", "herbal tea",
                "decaf", "hot chocolate", "milkshake", "smoothie", "juice", "wine", "beer")
_ASK_WORDS = ("how", "what", "is", "are", "was", "should", "can", "could", "do", "does",
              "did", "am", "limit", "safe", "ok", "bad", "healthy", "unhealthy", "worried")
_DOSE_WORDS = ("much", "many", "too", "limit", "safe", "ok", "bad", "healthy", "unhealthy",
               "day", "daily", "week", "weekly", "cup", "cups", "mug", "mugs", "glass",
               "glasses", "pint", "pints", "litre", "litres", "liter", "liters", "mg", "ml")
_COOKING_WORDS = ("made", "make", "makes", "cooked", "cook", "cooks", "cooking",
                  "left over", "left", "leftover", "leftovers", "freeze", "frozen", "freezer",
                  "pot", "pan", "jug", "batch", "reheat", "reheated", "keep", "keeps", "store",
                  "stored", "waste", "wasting", "wasted", "bin", "binned", "pour", "poured",
                  "split", "cool", "chill", "fridge", "throw", "throwing", "thrown", "portion",
                  "portions", "soup", "stew", "curry", "dinner", "supper", "meal")


def not_a_cup_of_tea(understood):
    """True unless the line asks how much of a drink is too much.

    A cooking verb or a pot in the line means there is something left over, and that stays with
    the freezing card. A drink with a measure in it and no cooking word is a dose question, and
    the caffeine limit owns it. Anything else is not this caller's business, so it is let past.
    """
    words = [str(word).lower() for word in (understood.get("words") or ())]
    if not words:
        return True
    joined = " %s " % " ".join(words)
    if not any(" %s " % name in joined for name in _DRINK_NAMES):
        return True
    if any(" %s " % word in joined for word in _COOKING_WORDS):
        return True
    # A question, not a remark: "too much tea in my mug" says nothing about a limit, and the
    # card that answers it is the one about the surplus.
    if not any(" %s " % word in joined for word in _ASK_WORDS):
        return True
    if any(" %s " % word in joined for word in _DOSE_WORDS):
        return False
    return True


# The four-in-the-afternoon snack, as a table rather than one sentence, because the chat knows
# what the person cannot eat and a card that names peanut butter to someone who has just said
# "im allergic to peanuts" is the one mistake this lane never makes. Each option carries the food
# families in its words; `cooking._bans_of` turns the person's own allergies, condition and diet
# into the words to leave out, so the same row answers every eater without a second list.
_SNACK_OPTIONS = (
    ("Greek yoghurt with berries", "dairy milk yoghurt"),
    ("an apple with a spoon of peanut butter", "nut peanut butter"),
    ("a handful of nuts with a boiled egg", "nut egg"),
    ("hummus with carrot and oatcakes", "sesame hummus chickpea"),
    ("cheese on two crackers", "dairy cheese gluten cracker"),
    ("a banana and a glass of milk", "dairy milk banana"),
    ("rice cakes with mashed avocado", "rice avocado"),
    ("home-made popcorn", "corn popcorn"),
    ("carrot sticks and a few olives", "carrot olive"),
)


# An allergy is said by the food, not by the family: memory keeps "peanuts", "cashews" or
# "almonds", and the table's tags say "nut". One table maps what a person might name to the tag,
# so a cashew allergy leaves out the peanut butter as well.
_SNACK_FAMILY_OF = {}
for _tag, _named in (
        ("nut", "nut nuts peanut peanuts almond almonds cashew cashews walnut walnuts "
                "hazelnut hazelnuts pistachio pistachios pecan pecans brazil brazils"),
        ("dairy", "dairy milk milks cheese cheeses yoghurt yogurts yogurt butter cream lactose"),
        ("gluten", "gluten wheat coeliac celiac flour bread pasta cracker crackers"),
        ("sesame", "sesame tahini hummus"),
        ("egg", "egg eggs mayonnaise")):
    for _word in _named.split():
        _SNACK_FAMILY_OF[_word] = _tag


def _a_snack(memory, understood):
    """Protein and fibre, from the options left once the chat's own bans are taken out."""
    user = (memory or {}).get("user") if isinstance(memory, dict) else None
    banned = set(_bans_of(user))
    # The allergy that matters here can belong to somebody else in the chat: "my daughter is
    # allergic to nuts" and then "and a snack" was answered with an apple and a spoon of peanut
    # butter, because only the user's own allergies were read.
    banned |= set(avoids_for_the_one_talked_about(memory))
    for said in (user or {}).get("allergies") or ():
        for word in str(said).lower().replace(",", " ").split():
            tag = _SNACK_FAMILY_OF.get(word)
            if tag:
                banned.add(tag)
    chosen = [food for food, words in _SNACK_OPTIONS
              if not (set(words.split()) & banned)]
    if not chosen:
        chosen = ["whatever protein and fibre you can eat safely"]
    listed = ", ".join(chosen[:2])
    if len(chosen) >= 3:
        listed += " or " + chosen[2]
    return ("Go for protein plus fibre at about four in the afternoon, 150 to 250 calories: "
            + listed + ". It holds you a couple of hours where a biscuit holds you twenty "
            "minutes, so you are not starving at dinner.")


# The bake row's own guard: a bake is flat, a home is flat, and only the words next to each
# other say which. `not_the_flat_you_live_in` is the one definition, so this is a plain alias and
# not a second regex that could drift from it.
_not_the_flat_you_live_in_bake = not_the_flat_you_live_in
_COFFEE_LEADS = (
    ("cappuccino", "A cappuccino is a third espresso, a third steamed milk and a third foam: pull "
                   "a double espresso (about 60ml), heat about 120ml of milk to 60-65C while "
                   "letting plenty of air in so it doubles to a stiff foam, then pour the milk in "
                   "and spoon the foam on top."),
    ("latte", "A latte is a double espresso (about 60ml) with about 200ml of milk heated to 60-65C "
              "and frothed barely at all, so it is a thin layer of microfoam over hot milk rather "
              "than a cap. Pour with the jug low and the drink stays glossy."),
    ("macchiato", "A macchiato is a double espresso (about 60ml) with just a spoonful of milk foam "
                  "stained into it: heat a little milk to 60-65C, froth it, and drop a dessert "
                  "spoon of the foam on top of the shot."),
    ("americano", "An americano is a double espresso (about 60ml) with about 120ml of hot water "
                  "added, never the other way round: the water goes in after the shot because "
                  "brewing onto hot water scorches the coffee and it turns bitter."),
    ("espresso", "An espresso is about 18g of finely ground coffee to a double shot of 60ml in "
                 "25-30 seconds. Grind fine, tamp level and firm, and if it runs much faster the "
                 "grind is too coarse, if it dribbles the grind is too fine."),
)

_THE_MILK_ONLY = ("froth the milk", "froth milk", "froth", "frothing", "frothed milk",
                  "steam the milk", "steam milk", "steaming", "milk frother", "steam wand",
                  "milk steamer", "no machine", "without a machine")


def _a_coffee(memory, understood):
    """The drink the line names, said first, then the milk.

    Every one of these is a flat white's answer otherwise, and "how do i make a latte at home"
    wants the latte in its first sentence, not the flat white's recipe with a note at the end.
    """
    said = str((understood or {}).get("norm_text")
               or (understood or {}).get("text") or "").lower()
    for name, lead in _COFFEE_LEADS:
        if name in said:
            return lead + " " + _COFFEE_MILK_TAIL
    if any(phrase in said for phrase in _THE_MILK_ONLY):
        return _THE_FROTH_CARD
    return ("A flat white is a double espresso (about 60ml) with about 100ml of milk heated to "
            "60-65C and frothed only to a thin, glossy microfoam, poured with the jug low so the "
            "foam sits in a thin layer rather than a cap on top, while a latte takes twice the "
            "milk and less foam, and a cappuccino more air again. " + _COFFEE_MILK_TAIL)


_COFFEE_MILK_TAIL = ("Whole milk froths most easily and skimmed the least. With no steamer, heat "
                     "the milk in a pan to just before it simmers and whisk hard for 20 seconds, "
                     "or shake it in a lidded jar and give it 30 seconds in the microwave.")

_THE_FROTH_CARD = ("Heat the milk to 60-65C - hot but not simmering, because above that the milk "
                   "turns and tastes cooked - then get air in for the first few seconds and stop: "
                   "with a steam wand, tip it just under the surface so it hisses, then sink it to "
                   "spin the milk into a glossy microfoam. With no machine, heat it in a pan and "
                   "whisk hard for 20 seconds, or shake it in a lidded jar and microwave it for 30 "
                   "seconds. Whole milk froths most easily and skimmed the least.")


def _tins_keep(memory, understood):
    """A tin keeps for years; the acidic ones are best inside 18 months.

    "how long do tins last", "how long does a tin of beans keep" and "is a tin of tomatoes ok
    after the date" all want the tin in the first sentence. The opened tin is a different
    question and stands this row down.
    """
    return ("Tins keep for years in a cool cupboard, though anything acidic - tomatoes, fruit, "
            "pickles - is best inside 18 months, and a dented or rusty tin is worth using soon. "
            "The date on a tin is a best-before for quality rather than a use-by. Bin any tin that "
            "is bulging, smells sharp when you open it, or fizzes. Once it is open, what is left "
            "goes into a bowl with a lid, not back in the tin: 2 days in the fridge for tuna or "
            "beans, and eat anything acidic within a couple of days.")


def _tomato_sauce(memory, understood):
    """The sauce, opening with the time when the line asks how long it takes.

    "how long should i simmer a tomato sauce", "how long do i cook tinned tomatoes" and "how long
    should i simmer tomatoes" all asked for the minutes and got the drawer card or a hedge. The
    recipe is the same one; only the first sentence changes.
    """
    said = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "")
    said = said.lower() + " "
    if any(phrase in said for phrase in ("how long", "simmer", "minutes", "how many minutes",
                                         "time", "takes", "take")):
        return ("Twenty to thirty minutes on a low simmer, and it is better at forty: soften the "
                "garlic in olive oil, add a tin of tomatoes and a pinch of salt, and let it go "
                "uncovered so it thickens. Tear in basil at the end and loosen it with a splash of "
                "pasta water. A long simmer is what turns tinned tomatoes from sharp into sweet, so "
                "if it tastes sour give it another ten minutes rather than more sugar.")
    return ("A good 15-minute tomato sauce: soften sliced garlic in olive oil, add a tin of tomatoes "
            "and a pinch of salt, and simmer it while the pasta cooks. Tear in a few basil leaves at "
            "the end and loosen it with pasta water.")
# How long a cooked dish keeps once frozen, said for the dish in hand. The row answers for every
# cooked dish it names, and its one sentence listed the times for mash, stew, curry, soup and
# bolognese - so "can i freeze lasagne", on turn seven of a chat, was told "it keeps a month for
# mash", and the next line "how long does it keep" cut that sentence down to "It keeps a month
# for mash." on a dish it was not about. Each dish now says its own time, and a dish with no row
# of its own gets the rule that covers almost all of them.
def freeze_cooked_answer(memory, understood):
    """The public name for the cooked dish's freezing answer, for the rows beside this one."""
    return _freeze_cooked(memory, understood)


FREEZE_DISH_TIMES = (
    (("mash", "mashed potato", "mashed potatoes", "potato", "potatoes"), "about one month"),
    (("lasagne", "lasagna", "pasta bake", "casserole", "shepherds pie", "cottage pie",
      "pie", "risotto", "paella", "gratin", "stew", "curry", "soup", "chilli",
      "bolognese", "leftovers", "food",
      # the same dishes the row now picks up, said back by name: "yes - it keeps about three
      # months in the freezer" reads better than the fallback that lists mash in it.
      "quiche", "frittata", "omelette", "moussaka", "tagine", "meatballs", "burrito",
      "quesadilla", "stuffing", "sausage rolls", "samosa", "spring rolls", "dumplings",
      "fishcakes", "fish cakes", "nut roast"), "about three months"),
)

# The part of the answer that is the same whatever the dish: what to do with it when it comes out.
FREEZE_COOKED_STEP = (
    "Reheat it from frozen until it is piping hot right through, or thaw it overnight in the "
    "fridge and use it once.")


def _freeze_cooked(memory, understood):
    """How long the cooked dish in the line keeps in the freezer, said for that dish.

    The dish is the one the line or the chat is on, and none named gets the general rule with the
    figures in it: a person who asks "can i freeze it" has not said what it is.
    """
    said = " %s " % " ".join(str(word).lower() for word in (understood.get("words") or ()))
    for names, keeps in FREEZE_DISH_TIMES:
        # the plural is the same dish: "can i freeze burritos" was the fallback that lists mash
        # because the table says burrito, and a list of plurals beside every name goes stale.
        if any(" %s " % name in said or " %ss " % name in said for name in names):
            # The keeping time comes first, and the cooling step after it: a "how long for" said
            # next is about how long it keeps, and the hour it takes to cool is the only other
            # length in the answer, so written the other way round that hour is what came back.
            return ("Yes - it keeps %s in the freezer, so cool it within an hour, then pack it "
                    "flat in bags or tubs so it freezes fast. %s" % (keeps, FREEZE_COOKED_STEP))
    return ("Yes - cooked dishes keep about three months frozen, and a month for mash, so cool it "
            "within an hour, then pack it flat in bags or tubs so it freezes fast. %s"
            % FREEZE_COOKED_STEP)


# A pan going down somewhere is this row's question only when the pan is hot or has done damage.
# The placement words say nothing about heat, so "i put the dish on the table", "i put the cold pan
# on the worktop" and "i put the kettle on the side" were all answered with the worktop card, which
# reads as if the bot had not listened. Heat, a just-off-the-heat phrase, or damage does the asking.
_HOT_SAID = re.compile(
    r"\b(?:hots?|hotter|scorching|scorched|scorch|sizzling|smoking|steaming|melted|melts?|"
    r"burnt|burned|burns?|blistering|straight off|off the (?:hob|ring|heat|burner)|just off|"
    r"just came off|came off the|left a (?:mark|ring|stain))\b", re.IGNORECASE)


def _a_hot_thing_is_being_set_down(understood):
    """True when the line says the thing was hot, or that it marked what it stood on."""
    if not isinstance(understood, dict):
        return True
    said = understood.get("text") or understood.get("clean") or ""
    if not said:
        said = " ".join(understood.get("words") or ())
    return bool(_HOT_SAID.search(str(said)))


# The words a batter goes by, whether it is poured into a pan or into a tin.
_BATTER = ("pancake", "pancakes", "crepe", "crepes", "batter", "waffle", "waffles",
           "yorkshire pudding", "yorkshire puddings", "yorkshires", "pikelet", "pikelets",
           "drop scones", "blini", "blinis")
_BATTER_IN_A_TIN = ("tin", "tins", "tray", "trays", "muffin", "muffins", "oven",
                    "yorkshire", "yorkshires", "pudding", "puddings")
# A waffle iron is a pan that closes: hot, oiled and not pulled open too soon.
_BATTER_IN_AN_IRON = ("iron", "waffle iron", "waffle maker", "waffles", "waffle")

_LOAF = ("bread", "loaf", "loaves", "sourdough", "bloomer", "brioche", "teacake", "teacakes")


def _out_of_the_tin(memory, reading):
    """A bake that stuck to its tin, said for a cake or for a loaf.

    Both want the tin lined before they go in, and both come out the same way round, but a loaf
    has no crumb to press back together and its own trick is the strip of paper that overhangs.
    """
    words = set(reading.get("words") or ())
    if words.intersection(_LOAF):
        return ("A loaf sticks to the tin when the tin was bare or the dough was wet: oil the tin "
                "all over, and line the base and the two long sides with a strip of baking paper "
                "that overhangs the top, so you lift the loaf out by the paper. Run a knife round "
                "the edges while it is still warm, wait ten minutes, then turn it out and tap the "
                "base - and let it cool on its side so the crust does not go soft.")
    return ("A cake sticks to the tin when it was greased unevenly, turned out before it had "
            "firmed, or baked in a tin that was not lined. Line it with a strip of baking paper "
            "across the base and up two sides and it lifts out whole. Run a thin knife round the "
            "edge while it is still warm, wait ten minutes, then turn it out onto a rack - and if "
            "it does crack, stick it back together with a little jam or buttercream and nobody "
            "will know.")


def _a_batter_that_sticks(memory, reading):
    """How to stop a batter sticking, read off what it is cooked in.

    A pancake in a pan, a waffle in an iron and a Yorkshire pudding in a tin are one fault with
    three cures, and the line's own words pick the one that answers it. A batter in a pan wants a
    hotter pan and a wiped film of oil; an iron wants the same and the lid left alone; a tin wants
    the fat hotter than the batter and the oven door shut.
    """
    words = set(reading.get("words") or ())
    if words.intersection(_BATTER_IN_AN_IRON):
        return ("A waffle iron that grips wants to be properly hot before the batter goes in, and "
                "brushed with a little oil right into the grooves: heat it five minutes, oil it, "
                "and fill to the edge of the pattern only. Leave the lid shut for a minute and "
                "let the waffle come away by itself - one pulled open early tears.")
    if words.intersection(_BATTER_IN_A_TIN):
        return ("A batter that sticks to the tin wants the fat hotter than the batter: put a little "
                "oil or dripping in each hole and heat the tin in the oven at 220C (200C fan) for "
                "10 minutes, until it shimmers, then pour the batter in and shut the door. Do not "
                "open it for 20 minutes - the cold air drops them - and if one still sticks, give "
                "it 5 minutes more, because a batter that comes away rough was not done.")
    return ("A batter that sticks wants a hotter pan and less fat than you would think: heat a "
            "non-stick or well-seasoned pan on a medium heat for a couple of minutes, wipe it "
            "with a little oil on kitchen paper, and pour when a drop of batter sizzles at once. "
            "Wait until the top bubbles and the edges look dry before you turn it, because "
            "lifting one early is what tears it, and thin a thick batter with a splash of milk, "
            "or it sits in the middle of the pan and grips.")


# What to do about a food that stuck to the pan, said once so the food this table knows and the
# food it has never heard of cannot drift into two answers.
_STUCK_TO_A_PAN = (
    "Get the pan properly hot with the oil already in it, then leave the food alone for the first "
    "minute: it releases itself once it has browned. For pasta, stir it for the first minute in a "
    "big pan of water; for rice, rinse it and don't stir it at all.")

# A frozen pizza is a cooking question: "frozen" alone made it a freezing question, so
# "how do i cook a frozen pizza" got "most cooked food freezes well".
_FROZEN_SAID = frozenset((
    "frozen", "freezer", "freeze", "freezes", "froze", "defrost", "defrosted", "defrosting",
    "thaw", "thawed", "thawing", "cold", "ice", "straight",
))


def _a_frozen_pizza(understood):
    """True when the line says the pizza came out of a freezer (or a chiller)."""
    return bool(_FROZEN_SAID.intersection(understood.get("words") or ()))


SLICE_METHOD = ("A serrated bread knife, long gentle sawing strokes and almost no downward "
                "pressure: a sharp straight knife crushes the crumb instead of cutting it. Lay "
                "the loaf on its side so the cut is level, cut from the far edge towards you, "
                "and slice the whole loaf at once if you are going to freeze it.")
SLICE_THICK = ("About 1cm to 1.5cm for a sandwich, 2cm for toast, and a fresh sourdough wants the "
               "thicker end of that because its crumb is denser. A very thin slice tears unless "
               "the bread is a day old, since new bread is too soft to hold a thin cut.")
SLICE_WARM = ("Let it cool first, an hour on a rack for a loaf: a warm loaf is still setting "
              "inside, so a slice squashes the crumb and lets the steam out, and the cut face "
              "goes gummy. Warm bread also stales faster once it has been cut.")
STALE_FAST = ("A lean loaf with no fat or sugar in it stales faster than a shop one that has "
              "both, and the cut face is where it dries: stand the loaf cut side down on a "
              "board, keep it in a paper bag or a bin rather than the fridge, and freeze what "
              "you will not eat in two days - sliced, so you can take out what you need. A "
              "sourdough goes hard rather than mouldy first, and 5 minutes in a hot oven with a "
              "splash of water brings a slice back.")


# A slice is two things: the act of cutting a loaf, which is this row's question, and a portion
# of bread, which is a nutrition question. "A slice of bread", "two slices" and "slices of bread"
# ask what is *in* one, and the counting word is what tells them apart: after "how much protein in
# porridge oats", "and in a slice of bread" was told about a serrated knife, and so was "what
# about two slices". A line that counts the slices is a portion, and this row stands aside.
_A_PORTION_OF_SLICES = re.compile(
    r"\b(?:a|an|one|two|three|four|five|six|\d+)\s+slices?\b|\bslices?\s+of\b")
# unless the line is plainly asking how, which is the knife whatever it counts.
_STICKING_A_CUT = re.compile(r"\b(?:how|why|should|which way|what is the best way)\b")


def _bread_sliced(memory, understood):
    """How to cut a loaf, how thick, whether warm, or why it stales - the line says which."""
    said = " " + str((understood or {}).get("clean") or (understood or {}).get("text") or "").lower() + " "
    if _A_PORTION_OF_SLICES.search(said) and not _STICKING_A_CUT.search(said):
        return None
    if any(word in said for word in (" stale", " stales", " staling", " hard", " dry", " drying",
                                     " why does", " why do", " goes off", " gone hard")):
        return STALE_FAST
    if any(word in said for word in (" thick", " thickness", " thin", " wide",
                                     " how wide", " size of")):
        return SLICE_THICK
    if any(word in said for word in (" warm", " hot", " just baked", " fresh out", " still warm",
                                     " straight out")):
        return SLICE_WARM
    return SLICE_METHOD

# "the kids wont eat kidney beans" is the beans question, not the tea question. The tea row
# keys on the eating words (a person asking "what should i feed my kids" asks the same thing as
# "kids tea ideas"), so a line naming a food tied with that food's own row and the tea row's
# bias won the tie: the bean card ("Mash them in rather than serve them whole") came back as a
# plate of fish fingers. A named food is the more specific question, so this row stands down.
# Only the ingredient names count, never the whole food vocabulary: "food", "dinner", "eat"
# and "veg" are what the tea question itself is made of.
def _no_named_food(understood):
    from .meals import INGREDIENTS  # imported here: this file loads with meals
    words = set(understood.get("words") or ())
    named = set()
    for key, forms in INGREDIENTS.items():
        # "veg" is a category, not an ingredient: "my kids wont eat their veg" is the refusing-veg
        # card's line, and standing the tea row down for it cost that line its warmer answer
        # (a reviewer caught it on a 20-line probe - 4 gains, that one loss).
        if key == "veg":
            continue
        named.update(forms)
    return not (words & named)

# Three faults a bowl of porridge has, and no pan's answer fits any of them: tinned tomatoes,
# potatoes and vinegar all have a place, and it is not in a bowl of oats.
_PORRIDGE_SALT = ("too salty", "salty", "too much salt", "over salted", "oversalted",
                  "salt went", "extra salt", "double salt")
_PORRIDGE_BLAND = ("bland", "tastes of nothing", "taste of nothing", "no taste", "tasteless",
                   "nothing in it", "a bit boring", "boring")


def _porridge_fault(memory, understood):
    said = str(understood.get("clean") or understood.get("text") or "").lower()
    if any(word in said for word in _PORRIDGE_SALT):
        return ("A bowl of porridge with too much salt in it takes more milk and more oats, not "
                "water: stir in a good splash of milk and a spoon more oats and give it two "
                "minutes on the heat, then a spoon of plain yoghurt or a little honey at the end. "
                "Water alone just leaves you with a thin bowl that is still salty.")
    if any(word in said for word in _PORRIDGE_BLAND):
        return ("Porridge is bland for want of salt and something on top, not for want of skill: "
                "put a pinch of salt in the pan, cook it in milk rather than water, and finish it "
                "with honey, jam, brown sugar, banana, berries or a spoon of peanut butter. Salt "
                "is the one that matters - without it everything else tastes flat.")
    if "overnight" in said or "soak" in said or "soaked" in said or "in a jar" in said:
        # nothing has been cooked yet, so there is no pan to salt
        return ("Stir a pinch of salt and a splash more milk or yoghurt into the jar, because salt "
                "and milk are what turn the sweetness down, and leave it ten minutes to mellow. If "
                "it is still too sweet, add a spoon more oats and a little milk rather than more "
                "sugar in future: the sweetness sits on top of soaked oats rather than in them.")
    return ("Stir in a splash more milk or plain yoghurt and a pinch of salt, because salt is "
            "what turns the sweetness down, and leave it a minute to loosen. If it is still too "
            "sweet, a handful of berries or a spoon of yoghurt does more than adding more oats. "
            "Next time, leave the sugar out of the pan or the jar and put it on the table: "
            "porridge takes very little, and the milk brings out the sweetness of the oats.")


# The surfaces a hot pan may go on, named the way a person names them, and the ones it may not.
# `hot-pan-surface` answers the where-question ("where can i put a hot pan") and the yes/no about
# one named surface alike, and the verdict used to be the reply's second sentence: "can i put a
# hot pan on a granite worktop" was told where a pan can go, and only afterwards that granite is
# the one it must not touch. A person who names a surface is asking about that surface, so the
# answer opens on it; a line that names none keeps the balanced answer, which is the whole of
# what "where can i put a hot pan" asks.
_HOT_PAN_TAKES = (
    # The hob needs its own word. A bare "glass top" is how people say the table they eat off, and
    # that is the one surface in this list that shatters, so a line that only says "glass top"
    # gets the balanced answer below - whose no still names glass tables - rather than a
    # confident yes about the wrong surface.
    ("a glass ceramic or induction hob",
     r"glass (?:ceramic )?hob|ceramic hob|induction (?:hob|top)|glass[- ]top hob"),
    ("a stainless steel worktop",
     r"stainless(?: steel)? (?:worktop|work top|top|surface|bench)"),
    ("the hob", r"\bhob\b"),
)
_HOT_PAN_REFUSES = (
    ("granite", r"granite", "the heat shock cracks stone"),
    ("quartz", r"quartz", "the heat shock cracks stone"),
    ("marble", r"marble", "the heat shock cracks stone"),
    ("a laminate worktop", r"laminate", "the heat shock scorches and lifts it"),
    ("a wooden worktop or board",
     r"wood(?:en)? (?:worktop|work top|(?:\w+ )?board)", "the heat scorches the wood"),
    ("a wooden table", r"wood(?:en)? table", "the heat scorches the wood"),
    ("a glass table", r"glass[- ]?top table|glass table", "the heat shock can crack it"),
)
_HOT_PAN_CAN = ("Straight off the ring a hot pan can go back down on a glass ceramic or induction "
                "hob, and on a stainless steel worktop, because those are built for it.")
_HOT_PAN_NOT = ("Keep it off granite, quartz, marble and laminate worktops, wooden boards and "
                "glass tables: the heat shock cracks stone and scorches laminate.")
_HOT_PAN_TIP = "A trivet or a folded dry cloth under it, and nothing wet on a hot hob."


def _a_hot_pan_surface(text):
    """The verdict for the surface this line names, and the surface as it is called.

    Returns ("yes", name, "") for a surface built to take a hot pan, ("no", name, the reason) for
    one the heat damages, and (None, None, "") when the line names no surface at all. The reason
    is the surface's own - wood scorches and stone cracks - because one sentence for all of them
    told a person with a wooden worktop that the heat shock would crack their stone.
    """
    said = " %s " % (text or "").lower()
    # The no is read first, because two of the surfaces are said with the word the hob is:
    # "a glass table" must not be read as the glass of a glass hob.
    for name, pattern, reason in _HOT_PAN_REFUSES:
        if re.search(r"(?:%s)" % pattern, said):
            return "no", name, reason
    for name, pattern in _HOT_PAN_TAKES:
        if re.search(r"(?:%s)" % pattern, said):
            return "yes", name, ""
    return None, None, ""


def _the_hot_pan_place(memory, understood):
    """The surface answer, opening on the verdict when the line names the surface."""
    verdict, surface, reason = _a_hot_pan_surface(_line(understood))
    if verdict == "no":
        return ("No - not on " + surface + ": " + reason + ". " + _HOT_PAN_CAN + " "
                + _HOT_PAN_TIP)
    if verdict == "yes":
        return ("Yes - " + surface + " takes it straight off the ring. " + _HOT_PAN_NOT + " "
                + _HOT_PAN_TIP)
    return _HOT_PAN_CAN + " " + _HOT_PAN_NOT + " " + _HOT_PAN_TIP


def something_to_bake_in_the_oven(understood):
    """True when the line names a dish, whose own heat the dish table answers.

    The oven row answers the oven's own heat - a dial that runs hot, a thermometer that reads
    wrong - and a line that names a dish wants that dish's number instead.
    """
    if not isinstance(understood, dict):
        return False
    text = str(understood.get("clean") or understood.get("text") or "")
    if not text:
        return False
    from . import dishes
    return bool(dishes.dish_in(text))


# A tray of roast potatoes, and the one fault that wants a different answer from the method.
# Every shape of the question used to get the method read out again, except the burnt tray, which
# reached the roast-vegetable salvage card ("cut the black edges off and give it ten more
# minutes"): what a burnt tray needs is the reason it happened.
_ROAST_BURNT = ("burn", "burnt", "burning", "black", "blackened", "caught", "too hot",
                "too dark", "stuck")


_ROAST_STUCK = ("stuck", "stick", "sticks", "sticking", "welded", "glued")


# A tray that came out hard is the third fault the same row answers, and it was the one main
# answered with two cards that each missed: "how do i make roast potatoes without them going hard"
# got the dish plan's reheating note ("they reheat well at 200C for 8 minutes"), and "my roast
# potatoes are hard in the middle" got the boiled-vegetable card. A potato that is hard has not
# had long enough, and the tray is why.
_ROAST_HARD = ("hard", "harder", "still hard", "too hard", "undercooked", "under cooked",
               "under-done", "not cooked", "not soft", "raw in the middle", "hard in the middle",
               "hard centre", "hard centers", "not done")


# A joint named beside the tray is not a different subject. Bare nouns in `avoid` win over every
# key word, so "roast potatoes in beef dripping", "roast potatoes with the lamb" and "with the
# gammon" stopped reaching this row at all and fell to the joint's row or to a chat ack - and
# beef, goose, lamb and the rest are the words of the fat and the plate, not of another subject.
# What is the joint's own question is its timing, so the row stands down only when a joint is
# named *and* a time is being asked for it, and never when the line names the fat, which is a
# tray word: "in goose fat" and "in beef dripping" are this method.
_JOINT_WORDS = ("chicken", "turkey", "beef", "lamb", "pork", "ham", "gammon", "goose", "duck",
                "joint", "bird", "brisket")

_A_JOINT_TIMING = re.compile(
    r"\bhow long\b|\bhow many minutes\b|\bhow many hours\b|\btakes?\b|\btiming\b"
    r"|\btime\b|\bminutes per\b|\bper (?:kg|500g|pound|lb)\b|\bis it done\b"
    r"|\bwhen is it done\b")

_A_FAT_WORD = re.compile(r"\bfat\b|\bdripping\b|\bdrippings\b|\blard\b|\btallow\b")


def _not_the_joint_timing(understood):
    """True unless the line asks a joint's cooking time: then the joint's own row answers."""
    said = " " + " ".join(str((understood or {}).get(key) or "")
                          for key in ("clean", "norm_text", "norm")).lower() + " "
    if not any(re.search(r"\b" + word + r"\b", said) for word in _JOINT_WORDS):
        return True
    if _A_FAT_WORD.search(said):
        return True
    return not _A_JOINT_TIMING.search(said)



def _roast_potatoes(memory, reading):
    """A roast potato question: the reason the edges caught or stuck, or the method."""
    clean = str(reading.get("clean") or "").lower()
    if any(word in clean for word in _ROAST_STUCK):
        return ("Sticking is the tray and the wet, not the heat: put the oiled tray in to get hot "
                "before the potatoes go on, dry them on a tea towel once they are drained, and "
                "keep them in one layer with space between them so the steam can get out. "
                "Turn them at 25 minutes with a fish slice rather than a spoon, and whatever is "
                "already browned comes away on its own.")
    if any(word in clean for word in _ROAST_HARD):
        return ("Hard in the middle is a size and time problem, not a heat problem: cut them no "
                "bigger than a golf ball, parboil them a full 8 minutes so the middle starts to "
                "cook before the outside crisps, and give the tray 10 to 15 minutes more at 200C "
                "(180C fan) in one layer. Test the biggest one with the point of a knife: it "
                "should slide in with no resistance at all.")
    if any(word in clean for word in _ROAST_BURNT):
        return ("Too hot, or the potatoes went in wet: turn the oven down to 190C (170C fan), "
                "spread them in one layer with space between them and turn them at 25 minutes. "
                "Dry them on a tea towel after the parboil and shake them rough, because a wet "
                "potato steams and then blackens at the edges before the middle is done.")
    return ("Parboil peeled potatoes for 8 minutes, drain them, shake the pan to rough up the "
            "edges, then roast at 200C (180C fan) in a thin layer of hot oil for 40 to 45 "
            "minutes. The rough edges are what go crunchy. If they came out of a freezer bag, "
            "none of that applies: 200C (180C fan) for 20 to 25 minutes straight from frozen, "
            "in one layer.")
ENTRIES = [
    # A batter is not a cake and its tin is not a cake tin. "my pancakes stick to the pan" and "my
    # yorkshire puddings stuck to the tin" were told to stir them and keep the water at a rolling
    # boil, which is a pot of pasta's answer, and the same words dropped a pancake recipe on the
    # yorkshire line. What a batter sticks to is a pan that is not hot enough, or fat that is not
    # hotter still, and that answer serves a pancake, a crepe, a waffle and a Yorkshire pudding
    # alike, so one row takes them all and reads the pan or the tin off the line.
    entry("a-batter-that-sticks",
          (_BATTER,
           ("stuck", "sticks", "stick", "sticking", "grips", "tears", "tearing", "breaking",
            "broke", "come out", "comes out", "came out", "getting out", "get it out",
            "get them out", "come away")),
          _a_batter_that_sticks,
          bias=2,
          # the batter itself (flat, thick, fluffy) and how many to make are other answers, and a
          # pan to buy or a bought mix is the shop's business
          avoid=("flat", "thin", "thick", "fluffy", "rise", "risen", "recipe", "how many",
                 "mix", "bought", "buy", "frozen", "freeze", "warm", "reheat",
                 "oil", "which pan", "what pan", "best pan", "pan for", "shrove", "day",
                 "sugar", "lemon")),
    # Soaking a food overnight is a step in a recipe, and nothing answered it for the foods that
    # do not want one: "can i soak pasta overnight", "can i soak noodles overnight" and "can i
    # soak rice overnight" were the night-sweat card and then, once that was fenced, a punt. The
    # pulses have their own row, so beans, chickpeas and lentils are deliberately not here.
    # --- washing up ------------------------------------------------------------
    # A pan with a burnt bottom is a cleaning question. The safety module now leaves these alone
    # (THING_BURNT), so without an entry here the answer would be an honest shrug.
    # --- the small kitchen know-how questions -----------------------------------
    # These are the lines people type mid-cook, in their own words: a burnt slice, an egg with a
    # cracked shell, spaghetti that clumped, what simmering even means. Each was a shrug on main,
    # and each has a short concrete answer. `fix-burnt` deliberately passes `toast`, so the slice
    # is nobody else's; the cauliflower and hummus answers are the whole-head and freezing ones,
    # not the "what can i make with it" idea, which stays with the pantry.
    # "can I leave the slow cooker on while I'm at work" is a question about the appliance, not a
    # request for a recipe: a list of stews answered it on main once safety stopped reading the
    # electric cooker as a gas ring. It takes "half full of liquid" and a lid, which is what makes
    # the day safe, and it stays out of the leftover and defrosting questions.
    entry("slow-cooker-left-on", (("slow cooker", "slow-cooker", "crockpot", "crock pot"),
                                  ("leave", "left", "leaving", "on all day", "all day",
                                   "overnight", "all night", "on all night",
                                   "while im out", "while im at work",
                                   "while i am out", "while i am at work", "unattended",
                                   # "keep" is the other way people say "leave on", and it was
                                   # in `avoid`, where a bare word takes lines away from the entry
                                   # and never adds one: "can i keep the slow cooker on overnight"
                                   # got the stew list. These phrases carry that meaning instead,
                                   # so "keep cooked rice in the slow cooker" stays a keeping
                                   # question and "keep it on" is an appliance one.
                                   "keep the slow cooker on", "keep a slow cooker on",
                                   "keep the crockpot on", "keep the crock pot on",
                                   "keep it on", "keeping it on", "keep it going",
                                   "keep it warm", "keeping it warm",
                                   "safe", "ok", "okay", "fine", "alright")),
          "Yes - that is what it is built for, and leaving a slow cooker on low while you are out "
          "is an ordinary thing to do. Keep it at least half full of liquid so it does not dry out "
          "and catch, put the lid on and do not lift it, sit it on a dry worktop with the cord well "
          "away from the hot sides, and keep it to about 8 hours on low (4 on high). Cooked food "
          "left in it on warm all evening is the one to avoid: cool the food, put it in the fridge, "
          "and reheat it once, piping hot.",
          # the recipe list, the defrosting and the leftovers are other answers
          # a bare "keep" was here and took the appliance question with it (see the key above)
          avoid=("recipe", "recipes", "what can i cook", "what to cook", "dinner ideas",
                 "frozen", "freeze", "defrost", "thaw", "reheat", "left over", "leftover",
                 "leftovers", "store", "storage", "keep in the fridge", "fridge", "freezer",
                 "clean", "cleaning", "smell", "smells", "keep it clean",
                 # washing the pot is the other question, and "is a slow cooker pot dishwasher
                 # safe" was answered "Yes - that is what it is built for, and leaving a slow
                 # cooker on low while you are out is an ordinary thing to do", which reads as a
                 # yes about the dishwasher and is about something else entirely
                 "dishwasher", "dish washer", "wash", "washing", "scrub", "stained",
                 "burnt on", "stuck on",
                 "gas", "hob")),
    entry("burnt-toast", (("toast", "toasted", "slice of toast", "toastie"),
                          # A burnt word is required, not just "is it safe": the answer is about
                          # the black on a slice, and "safe" alone also matched "is it safe to eat
                          # toast when pregnant", which is a food-safety question for a midwife.
                          ("burnt", "burned", "black", "charred", "scorched", "brown", "too long",
                           "in too long", "left it in")),
          "Yes, scrape the black off with a knife and eat the rest: it tastes fine, and burnt toast "
          "is not dangerous in the way people fear. Very charred bread does carry more acrylamide, "
          "so it is not something to make a habit of, but one slice is nothing to worry about. The "
          "smoke is the bigger nuisance, so open a window and run the extractor.",
          # a smoking kitchen is the smell entry, and an animal or a pregnancy is not this answer
          # "i burnt my toast and now the kitchen stinks" is about the smell in the room, not
          # about whether the slice is safe to eat. "stink" and its family were missing, so a
          # line that had already said the kitchen smells got "scrape the black off and eat it".
          avoid=("smell", "smells", "smelling", "stink", "stinks", "stinking", "stank", "reek",
                 "reeks", "odour", "pong", "smoke", "smoky", "alarm", "toaster broke",
                 "bread bin", "gone mouldy", "mould", "mold",
                 "dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "pet", "pets", "bird",
                 # whole words only: _forms has no prefix matching, so "pregnan" would match
                 # nothing a person writes - "is burnt toast safe during pregnancy" fell through
                 "parrot", "rabbit", "hamster", "pregnant", "pregnancy", "pregnancies",
                 "baby", "toddler", "child", "kids",
                 "tummy", "stomach ache", "food poisoning")),
    entry("cracked-egg", (("egg", "eggs"), ("crack", "cracked", "cracks", "crack in the shell",
                                           "shell is cracked", "broken shell",
                                           # an egg that leaked or broke in the box is the same
                                           # question, and the answer below already says what to
                                           # do with a crack that has leaked white in it. Without
                                           # these words the line left the nutrition entry and
                                           # reached nobody: "the egg leaked in the box are the
                                           # others ok" got "That would bother me too."
                                           "leak", "leaks", "leaked", "leaking", "egg leaked",
                                           "broke in the box", "broken in the box",
                                           "broke in the carton", "broken in the carton",
                                           "cracked in the box", "cracked in the carton")),
          "A hairline crack is fine: cook it and eat it. A crack with a bit of leaked white is "
          "usually fine too if it is fresh and you cook it through, but bin it if the shell is "
          "dirty from a cracked egg or it has been sitting warm, since the shell is what keeps "
          "bacteria out. Keep cracked eggs out of anything raw, like mayonnaise.",
          avoid=("shell went in", "shell in", "bit of shell", "chapped", "cracked lips",
                 "cracked skin", "cracked heel", "cracked heels", "pavement", "phone", "screen",
                 "plaster", "wall", "tile", "tiles",
                 # "how do i crack an egg" asks for the method, and eggs cracking in the pan is
                 # the boiling question, which has its own times
                 "how do i crack", "how to crack", "crack an egg", "cracking an egg",
                 "separate an egg", "separating an egg",
                 "boil", "boiling", "boiled", "pan", "stop", "stopping", "prevent", "shells in"),
          # The egg entries added `egg`/`eggs` to two more keys, so this one lost its rarity
          # point against `keep-eggs` ("an egg cracked in the fridge is it ok" was becoming the
          # boiled-eggs-keep-a-week answer). A cracked shell is this question, not storage.
          bias=1),
    entry("crack-egg", (("egg", "eggs"), ("crack", "cracks", "cracking", "cracked")),
          "Tap it on a flat worktop, not the rim of the bowl: one firm tap, turn it a quarter "
          "and tap again, then pull the halves apart over the bowl with your thumbs and let it "
          "drop. The flat tap cracks the shell in a line; a rim tap dents it and pushes shell "
          "into the egg. If a piece does go in, lift it out with a wet finger or the edge of a "
          "shell half, which the white will not cling to.",
          # The state of a shell that is already cracked is the cracked-egg answer, eggs that
          # crack while boiling are the boiling answer, and a broken yolk is nobody's cooking
          # method. "Crack" also means a phone, a joke and a nut.
          avoid=("is cracked", "cracked shell", "shell is cracked", "hairline", "leaked",
                 "leaks", "still ok", "still okay", "safe to eat", "safe", "bin it", "bad egg",
                 "boil", "boiling", "boiled", "pan", "poach", "poached", "scrambl", "yolk",
                 "separate", "separating", "separated", "white", "whites",
                 "phone", "screen", "window", "wall", "pavement", "tile", "tiles", "glass",
                 "joke", "password", "code", "nuts", "walnut", "coconut", "cracker", "crackers",
                 "whip", "cracking on", "get cracking", "crack someone", "knuckle", "lip",
                 "lips", "skin", "heel", "heels", "ribs", "back")),
    entry("broken-yolk", (("yolk", "yolks"),
                          ("broke", "break", "breaks", "broken", "split", "punctured",
                           "pierced", "burst")),
          "A broken yolk is still good: fry it as it is or scramble it, and it tastes the same "
          "though it will not look as neat. When you want them whole, crack each egg into a cup "
          "first and slide the good ones into the pan, so one broken one does not spoil the rest.",
          # A broken yolk is this answer, not the boiling times; a crack in the shell itself is
          # the cracked-egg answer.
          avoid=("boil", "boiling", "boiled", "runny", "dipping", "how long", "minutes"),
          bias=1),
    entry("separate-egg", (("egg", "eggs"), ("separate", "separating", "separated",
                                             "egg white", "egg whites", "whites")),
          "Crack the egg into your hand over a bowl and let the white slide through your "
          "fingers, or tip the yolk from one half-shell to the other and let the white fall. "
          "Cold eggs separate more cleanly than warm ones, so take them straight from the "
          "fridge, and lift a stray bit of shell out with the wet shell itself, which the white "
          "will not cling to.",
          # Keeping whites or yolks is a storage question, and "whites" on its own is the
          # laundry answer, so this one is nudged above it. Whipping whites is a different
          # question again, with its own entry (`whisk-egg-whites`): "how do i get egg whites
          # stiff" is about the peaks, not about getting the yolk out.
          avoid=("broke", "broken", "split", "how long", "boil", "poaching water", "freeze",
                 "freezer", "frozen", "keep", "keeps", "store", "storage", "left over",
                 "stiff", "stiffly", "stiffen", "stiffens", "stiffened", "stiffening",
                 "whisk", "whisks", "whisking", "whisked", "whip",
                 "whipping", "whipped", "peak", "peaks", "meringue", "souffle", "overbeat",
                 # folding is the step after whipping, and leftover whites are a storage
                 # question: both are single words, because "left over" never matches "leftover"
                 "fold", "folds", "folding", "folded", "leftover", "leftovers"),
          bias=1),
    # "my meringue wont stiffen" fell through to "Annoying - is it every time?", because
    # whisk-egg-whites keeps "meringue" out of its key (a recipe ask is not a peaks ask) and
    # nothing else answered it. Same question, the meringue's own words in the key.
    entry("meringue-stiffen",
          (("meringue", "meringues", "meringue mix", "meringue mixture"),
           ("stiffen", "stiffens", "stiff", "stiffly", "peak", "peaks", "wont stiffen",
            "not stiff", "floppy", "collapse", "collapsed", "whip", "whisk", "beating",
            # "my meringue went flat" was an echo: a meringue is the subject already, so the plain
            # words for the fault belong here too
            "flat", "went flat", "gone flat", "falls flat", "fell flat", "sank", "has sunk",
            "sunk", "deflated")),
          "Whip the whites in a spotless dry bowl - any trace of yolk, grease or water stops them "
          "stiffening - add a pinch of cream of tartar or a drop of lemon, then add the sugar a "
          "spoonful at a time once they hold soft peaks and stop the moment the whisk pulls up a "
          "stiff point that stands on its own: over-whisked whites go dry and collapse when you "
          "fold the sugar in.",
          # a meringue to buy, eat or keep is another answer, and the recipe ask keeps the plan
          avoid=("buy", "shop", "supermarket", "keep", "keeps", "store", "freeze", "frozen",
                 "calories", "recipe for", "nest", "eton", "pavlova", "lemon meringue",
                 "how do i make meringues", "how to make meringues", "make meringues")),
    entry("hummus-grainy",
          (("hummus", "houmous", "humous"),
           ("grainy", "gritty", "lumpy", "bitty", "not smooth", "smooth", "chalky")),
          "Blend it far longer than feels sensible - 3 to 4 minutes in a food processor, scraping "
          "down twice - and add 2 to 3 tablespoons of iced water while it runs: graininess is "
          "under-blending and a paste that is too dry, and rubbing the skins off the chickpeas "
          "before you blitz them takes it the rest of the way.",
          # making it fresh, keeping it and freezing it are other answers
          avoid=("recipe", "calories", "healthy", "keep", "keeps", "freeze", "frozen", "store",
                 "tin of", "tahini", "what is in")),
    entry("freeze-hummus", (("hummus", "houmous", "humous"),
                            ("freeze", "freezer", "frozen", "defrost", "keep", "how long",
                             "storage", "store", "shelf life", "shelf-life")),
          "Hummus keeps about a week in the fridge in a sealed tub, and it freezes well for "
          "about four months. To freeze it, smooth it flat in a tub, thaw it overnight in the "
          "fridge and stir it well, adding a squeeze of lemon and a splash of water when it comes "
          "back, since it returns a little grainy. Leave off the pool of oil and the swirl until "
          "you serve it, because they separate.",
          avoid=("recipe", "make", "calories", "healthy")),
    entry("roast-cauliflower", (("cauliflower", "cauliflowers"),
                                ("whole", "how long", "roast", "oven", "bake", "time",
                                 "temperature", "cook")),
          "A whole head takes about 45 minutes at 200C (180C fan): rub it all over with oil, salt "
          "and pepper, sit it stalk down in a tray and cover it with foil for the first 25 minutes, "
          "then uncover it so the outside browns. It is done when a knife goes in with no "
          "resistance. Florets tossed in oil take 25 minutes at the same heat.",
          avoid=("what can i make", "what can i do with", "ideas", "leftover", "cheese sauce",
                 "soup", "rice", "mash",
                 # "how long does cauliflower keep in the fridge" is the keeping entry, and a
                 # boiled or steamed head wants its own time, not 45 minutes in the oven
                 "keep", "keeps", "keeping", "fridge", "freezer", "freeze", "store", "storage",
                 "go off", "gone off", "boil", "boiled", "boiling", "steam", "steamed",
                 "steaming", "microwave", "puree", "pureed", "rice",
                 # an air fryer is not a 200C oven for 45 minutes: that burns a whole head
                 "air fryer", "airfryer", "air-fryer")),
    # "how long do i bake apples for" is a time question about a whole fruit, and the answer
    # depends on the apple: the kinds are named in the reply rather than one number standing for
    # both. The pan and the microwave are different times, so the line is read for them.
    entry("bake-fruit", (("apple", "apples", "bramley", "bramleys", "cooking apple",
                          "cooking apples", "baked apple", "baked apples",
                          # the same question about the other fruit in the oven: a plum is done
                          # in 20 minutes and a quince takes the best part of two hours
                          "pear", "pears", "plum", "plums", "peach", "peaches", "nectarine",
                          "nectarines", "quince", "quinces", "baked pear", "baked pears",
                          "baked plum", "baked plums", "baked peach", "baked peaches"),
                          ("bake", "baked", "baking", "oven", "roast", "roasted", "how long",
                           "temperature", "temp", "time", "gas mark", "stew", "stewed", "poach",
                           "poached", "microwave", "core", "cored", "how hot", "soft")),
          _bake_fruit,
          # a keeping question, a pudding that already has a recipe and a drink are not this.
          # The second half is the other fruit's own words: a plum tomato, plum pudding, quince
          # paste and peach melba are each a different answer, and a pear tree is the garden.
          avoid=("keep", "keeps", "keeping", "fridge", "freezer", "freeze", "store", "storage",
                 "go off", "gone off", "pie", "tart", "crumble",
                 "toffee", "cider", "juice", "chutney", "air fryer", "airfryer", "air-fryer",
                 "tomato", "tomatoes", "paste", "melba", "tree", "trees", "jam",
                 "smoothie", "yoghurt", "yogurt", "brandy", "stone fruit", "prune", "prunes",
                 "damson", "damsons", "greengage", "greengages",
                 # a pudding is a dish of its own, and "im doing baked apples for pudding" is
                 # this row's question: only a pudding named with the fruit stands it down
                 "plum pudding", "steamed pudding", "christmas pudding", "summer pudding"),
          ask=("how long", "how hot", "time", "temperature", "temp", "bake", "baked", "baking",
               "oven", "roast", "stew", "stewed", "poach", "microwave", "gas mark", "soft"),
          # a soft fruit is this row's question once the line names a way of cooking it
          guard=_a_soft_fruit_is_still_a_cooking_question),
    # A shoulder is the joint you cannot roast like a leg: it needs the long low cook, and
    # "how do i cook a shoulder of lamb" was getting the leg's 25 minutes per 500g at 200C.
    entry("slow-roast", (("slow roast", "slow-roasted", "slow roasted", "slow cooking",
                          "pot roast", "casserole", "shoulder of lamb", "lamb shoulder",
                          "shoulder of pork", "pork shoulder", "shoulder of beef"),
                         ("oven", "temperature", "how hot", "what temp", "gas mark", "heat",
                          "setting", "how do i cook", "how do i roast", "how to cook",
                          "how to roast", "how long", "best way to cook", "best way to roast",
                          "how do i slow roast", "how do i slow cook", "slow roast", "slow cook")),
          "Set the oven to 150C (130C fan, gas 2) for a slow roast: lower than that and the meat "
          "sits in the danger zone for hours, higher and the outside dries before the middle "
          "softens. A covered pot keeps it moist, and a shoulder of lamb or pork or a beef "
          "brisket wants 4 to 5 hours. It is ready when a fork twists easily in the middle.",
          avoid=("slow cooker", "crockpot", "crock pot", "air fryer")),

    # A non-stick pan is the other way round: no scouring, no soak-and-scrub, and a flaking
    # coating is the end of it, which is not what the bicarbonate answer says to do.
    # Two questions reach this pan and they want different sentences first: "how do i clean it"
    # wants the sponge, and "is it still safe" wants the verdict before the sponge. The second
    # was answered with the first - "Warm water, washing-up liquid and a soft sponge" read as an
    # answer to "is my scratched pan safe", which is the wrong opening for a safety question.
    entry("non-stick-pan", (("non stick", "nonstick", "teflon", "non-stick", "pan coating",
                             "coating on my pan", "coating is coming off",
                             # the pan that has been scratched is usually asked without the
                             # words "non-stick" anywhere in it - "my pan is scratched",
                             # "should i throw away a scratched pan", "can i still use a scratched
                             # pan", "my pan has lost its coating" - and all of them were a shrug
                             # or a search hedge on main. The phrases carry the coating, so a
                             # question about which pan to buy and a burnt pan to clean keep
                             # their own rows.
                             "scratched pan", "scratched pans", "pan is scratched",
                             "pan has a scratch", "pans are scratched", "scratch in my pan",
                             "scratches in my pan", "scratches on my pan", "pan is scratched up",
                             "coating has come off", "coating came off", "coating has gone",
                             "coating is gone", "pan has lost its coating",
                             "lost its coating", "lost the coating", "bits of coating"),
                            ("clean", "cleaning", "wash", "washing", "scratch", "scratched",
                             "scratches", "scrub", "scouring", "burnt", "stained", "coating",
                             "flaking", "peeling", "stick", "sticking", "safe", "safety",
                             "still use", "use it", "throw away", "throwing away", "bin it",
                             "replace", "replacing", "worn", "bits", "coming off", "flakes")),
          _non_stick_pan, bias=1),
    # The cast iron pan is the one pan whose washing question has a different answer: soap and a
    # soak are what take the seasoning off, so it needs its own entry before burnt-pan.
    entry("cast-iron-pan", (("cast iron", "cast-iron", "skillet", "griddle pan"),
                            ("clean", "washing", "wash", "soap", "soapy", "rust", "rusty", "rusts",
                             "season", "seasoning", "seasons", "reseason", "re-season", "restore",
                             "stick", "sticking", "sticks",
                             "strip", "stripped", "oily", "dry", "scrub", "black", "dishwasher",
                             "dishwashers",
                             # "how do i look after my cast iron pan" names no fault at all, so
                             # every word in the fault list missed it and the line was a shrug.
                             # Looking after one is the same answer as cleaning and seasoning it.
                             "look after", "looks after", "looking after", "care", "caring",
                             "care for", "maintain", "maintenance", "keep it", "look",
                            # leaving one wet or to soak is the washing question, and "wet" was
                            # not a key at all: "is it ok to leave my cast iron pan wet" was the
                            # plaster cast's answer, and "can i leave it to soak" was a shrug.
                            "wet", "leave", "leaves", "leaving", "left", "overnight", "soak",
                            "soaks", "soaking", "soaked")),
          ("Scrub it with hot water and a stiff brush or a handful of coarse salt while it is still "
           "warm, then dry it on the hob over a low heat: a little washing-up liquid is fine, but "
           "soaking it is what strips the seasoning. To season it, rub a thin film of oil over the "
           "inside and bake it upside down at 200C for an hour, then do it once more. If it rusts, "
           "scrub the rust off first and season it the same way afterwards. Keep it out of the "
           "dishwasher: the detergent strips the seasoning off and the pan comes out with rust "
           "spots. A wok wants exactly this care too."), bias=1,
          # a cast-iron plant is a houseplant, not a pan: "how do i care for a cast iron plant"
          # was this row, and the plant's own card answers it
          avoid=("plant", "plants", "aspidistra", "houseplant", "leaves", "leaf", "compost",
                 # a wok is carbon steel and seasons by being used over a flame, which is a
                 # different answer from scrubbing a skillet: "how do i season a wok" was this
                 # card, which tells you to scrub the very layer a wok needs.
                 "wok", "woks", "carbon steel", "carbon steel wok",
                 "watered", "garden")),
    # A new pan is not always a cast-iron pan: a non-stick pan is not seasoned at all, and
    # "how do i season a new pan" was a shrug because nothing named a pan without naming the metal.
    entry("season-new-pan", (("season", "seasoning", "cure", "curing", "first use", "new pan"),
                             ("pan", "pans", "frying pan", "saucepan", "non stick", "nonstick",
                              "new", "wok", "skillet", "griddle")),
          "Wash off the factory oil in hot soapy water first. If it is cast iron or carbon steel, "
          "rub a thin film of flavourless oil over it and heat it until it just smokes, then let it "
          "cool and repeat two or three times - that is the seasoning. A non-stick pan is not "
          "seasoned at all: washing it is enough, and high heat is what ruins the coating.",
          avoid=("cast iron", "cast-iron"), guard=_not_a_season_of_a_show, bias=1),
    entry("burnt-smell", (("smell", "kitchen", "house", "flat", "room"),
                          ("burnt", "burning", "smoky", "smoke")),
          ("Open the windows and run the extractor fan, then simmer a pan of water with a splash of "
           "vinegar or a sliced lemon for ten minutes, which clears the air faster than air freshener. "
           "Wash whatever was in the oven, and leave a bowl of bicarbonate of soda in the kitchen "
           "overnight to take the last of it out of the air.")),
    entry("simmer-or-boil",
          (("simmer", "simmering", "simmered"),
           ("boil", "boiling", "boils", "difference", "rolling", "gentle", "between",
            "same thing", "mean", "means")),
          "A boil is a churn of big bubbles you cannot stir down; a simmer is a lazy tremble of "
          "small bubbles, about 90C against 100C. Stews, sauces and rice want the simmer, because "
          "a hard boil toughens meat and breaks the grains, while pasta and potatoes want the "
          "boil. When in doubt turn it down until the bubbles just keep coming.",
          avoid=("soup maker", "slow cooker", "air fryer")),
    entry("learn-to-cook",
          (("learn to cook", "learning to cook", "never cooked", "cant cook", "can't cook",
            "cook from scratch", "proper meals", "cooking basics", "basic cooking",
            "better at cooking", "where do i start cooking",
            # NOT bare "how do i cook": that phrase is how people name a dish they want cooked
            # ("how do i cook salmon", "how do i cook a roast chicken"), and it made this entry
            # beat every dish in the book. The lines that mean "teach me to cook" say it another
            # way - "i can't cook", "where do i start cooking" - and are all in this group.
            # "i can't cook" is the sentence people actually send, and the second group used to
            # want a "how/where/start" word, so it got a nod instead. The words below are the
            # gate for that sentence: a line can only match them and this entry's key together
            # when it says the person cannot cook, never when it names a dish.
            "rubbish at cooking", "useless in the kitchen", "hopeless at cooking",
            "no good at cooking", "cannot cook", "can not cook", "cant really cook",
            "will never be able to cook",
            "how do i cook properly", "cook properly", "how do i cook for myself",
            "how do i learn to cook", "teach me to cook", "how do i get into cooking",
            "i want to learn to cook", "how do i start cooking", "how do i cook",
            "how do i cook something"),
           # a dish, a technique or a fault named in the line is that entry's question
           ("how", "what", "start", "should", "first", "beginner", "learn", "want", "where",
            "improve", "get better", "no idea", "simple", "easy",
            "cant", "can't", "cannot", "at all", "rubbish", "useless", "hopeless", "no good")),
          # The card stands down when the line names a food the pantry or the staples table
          # already answers, because "how do i cook chard" is chard's own question: the reply
          # is in cooking.py, where the food names are read out of those tables.
          _learn_to_cook,
          # a named dish, a named technique and a fault are their own answers
          # a pulse is a named food with its own times, and "how do i cook" is in this entry's
          # key, so "how do i cook dried beans" was answering "learn to cook" with a list of
          # four meals. A food named in the line is never the beginner's guide.
          avoid=("beans", "dried beans", "black beans", "kidney beans", "butter beans",
                 "haricot", "cannellini", "pinto", "split peas", "chickpeas", "chick peas",
                 "lentils", "lentil",
                 "reheat", "freeze", "frozen", "calories", "calorie", "oven", "air fryer",
                 "slow cooker", "microwave", "how long", "how much", "cost", "recipe for",
                 "restaurant", "takeaway", "meal plan", "for one"),
          # "how do i cook" is also how a dish is named - "how do i cook salmon", "how do i cook
          # a roast chicken" - and this entry beat every dish in the book. The dish's own answer
          # reaches the line too, so this one stands behind all of them and takes a line that
          # names nothing at all.
          bias=-2),
    entry("first-curry",
          (("curry", "curries"),
           ("easy", "never made", "never cooked", "first time", "simple", "beginner", "basic",
            "someone who", "no idea")),
          "Start with a chickpea or chicken curry built on four things: onion, garlic, ginger and "
          "a spoon of curry powder. Soften a chopped onion in oil for 8 minutes, add the garlic, "
          "ginger, a teaspoon of curry powder and one of cumin for a minute, then the chicken or "
          "a drained tin of chickpeas, a tin of tomatoes and 100ml of stock, and simmer 20 "
          "minutes. Stir yoghurt in off the heat at the end, and taste for salt.",
          avoid=("stain", "stains", "smell", "freeze", "left out", "reheat", "microwave",
                 "calorie", "calories", "healthy", "restaurant", "takeaway")),
    entry("pudding-store-cupboard",
          # "afters" was a key word on its own, and a plural-shaped key word also matches its
          # singular, so "i have wind and bloating after meals" matched "after" and "i have" -
          # two key words - and got Eve's pudding instead of the bloating answer. The phrase is
          # what the dessert line says, so the phrase is what the key holds.
          (("pudding", "dessert", "something sweet", "for afters", "afters to eat"),
           ("what i have", "i have", "i've got", "ive got", "nothing in", "store cupboard",
            "cupboard", "whatever", "left over", "leftover", "in the house", "no eggs")),
          "Eve's pudding is the one to know when the cupboard is thin: sliced apple or any fruit "
          "in a dish, then a sponge of 100g each of butter, sugar and self-raising flour with 2 "
          "eggs spread over the top, baked 40 minutes at 180C (160C fan). With no flour at all, "
          "halved bananas baked with butter, brown sugar and a pinch of cinnamon take 15 minutes.",
          # a named pudding, a Christmas one and a shop-bought one are their own questions, and
          # so is a symptom: "afters" is a loose form of "after", so "i have wind and bloating
          # after meals" reached this pudding because of the word "after".
          avoid=("christmas", "shop", "buy", "restaurant", "calorie", "calories", "sugar free",
                 "custard powder", "black pudding", "yorkshire",
                 "bloating", "bloated", "wind", "farting", "trapped wind", "nausea", "sick",
                 "ill", "stomach", "cramps", "diarrhoea", "constipated", "reflux", "heartburn",
                 "intolerance", "allergy", "allergic", "food poisoning")),
    # --- rice, grains, pasta -------------------------------------------------
    entry("rice-sticky", ("rice", ("sticky", "sticking", "sticks", "stick to the pan", "gluey",
                                  "mushy",
                                  # a clump is the same fault said with the rice stuck to itself:
                                  # "my rice always goes clumpy" was a shrug, because the word was
                                  # in the pan row's avoid and in no key at all
                                  "clumpy", "clumped", "clumps", "a clump", "goes clumpy",
                                  "keeps going clumpy", "gone clumpy", "all clumped together",
                                  # the same fault said as a habit: "my rice keeps going sticky"
                                  # and "my rice came out sticky" were the streak card and the
                                  # frying-pan card
                                  "keeps going sticky", "keeps coming out sticky",
                                  "keeps turning out sticky", "always comes out sticky",
                                  "comes out sticky", "came out sticky", "turns out sticky",
                                  "turned out sticky", "sticky again", "keeps sticking")),
          "Rinse the rice until the water runs clear, cook it 1 part rice to 1.5 parts water with "
          "the lid on, and leave it alone: 12 minutes on a low simmer, then 10 minutes off the "
          # a rice that sticks is a rice question, and the stir-fry pan answer was taking it
          "heat. Stirring while it cooks is what makes rice gluey.", bias=1),
    # "how do i cook sticky rice" is not the rice-that-came-out-gluey question: the sticky rice of
    # Thai and Japanese food is a different grain, soaked and steamed and never rinsed or stirred.
    # The two rows share the word "rice", so this one asks for the *name* of the grain and leaves
    # the accident to the row above.
    entry("sticky-rice",
          (("sticky rice", "glutinous rice", "glutinous", "sweet rice", "sticky rice flour"),
           ("cook", "cooking", "make", "how", "steam", "steaming", "soak", "soaking", "need",
            "water", "long", "rice cooker", "basket", "what", "which", "best", "kind", "type")),
          "Soak it first, then steam it: four hours or overnight in cold water, drained, spread in "
          "a lined bamboo basket or on a cloth over a pan of boiling water, and steamed for 20 to "
          "25 minutes until it is translucent and chewy. It is a different grain from ordinary "
          "rice - short, opaque and chalky - and it is never boiled or stirred, which is what makes "
          "it a sticky ball rather than a pot of mush. In a hurry, an hour in warm water does the "
          "job, and a rice cooker with a sticky-rice setting takes 1 part rice to 1 part water and "
          "does the steaming for you.",
          # a rice that went gluey by accident is the row above, and the safety questions - how
          # long it keeps, whether it can be reheated - are rice-leftover's
          avoid=("went sticky", "goes sticky", "go sticky", "came out sticky", "turned sticky",
                 "too sticky", "why is my rice", "keep", "freeze", "fridge", "leftover",
                 "left over", "reheat", "safe", "how long does",
                 # sushi is short-grain rice seasoned with vinegar, not the glutinous grain:
                 # "how do i make sticky rice for sushi" is the sushi-rice question, and the
                 # soak-and-steam answer is a different dish (grand-iris)
                 "sushi", "nigiri", "maki", "onigiri"),
          bias=1),
    entry("rice-leftover", ("rice", ("leftover", "left over", "yesterday", "spare")),
          ("Yesterday's rice makes great fried rice: heat a little oil, add the cold rice and fry it "
           "hard for 3 minutes without stirring much, then push it aside and scramble an egg in the "
           "gap with soy sauce, peas or whatever vegetables you have."),
          # Freezing and storing rice is a food-safety question, not a recipe, and so is a
          # "can I still eat it" line with a day in it ("can i eat leftover rice tomorrow").
          avoid=("freeze", "freezer", "frozen", "defrost", "fridge", "keep", "store",
                 "storage", "reheat", "safe", "how long", "tomorrow", "next day")),
    entry("rice-left-out", ("rice", ("left out", "overnight", "all night", "room temperature",
                                     "sat out")),
          "Rice left out at room temperature is the one leftover worth being strict about: bin it "
          "after 2 hours. Cooked rice can grow a toxin that reheating doesn't destroy, so cool any "
          "leftovers fast, fridge them within the hour, and eat them within a day.",
          # a soak is a step with raw rice in it, not a leftover: "should i soak rice overnight"
          # and "do i need to soak brown rice overnight" are the soaking question, which has its
          # own entry below. The keeping card is about rice that has already been cooked. The
          # soak words are not a word list here, because a line can be both - the guard keeps
          # the row for "i soaked rice overnight and left it out".
          avoid=("rinse", "rinsing", "washing",
                 "dry", "uncooked", "raw", "before cooking"),
          guard=soak_but_not_left_out),
    # Soaking rice is the twin of the pulses question and it is not the same answer: people ask
    # it about basmati, brown rice and pilau, and on main "should i soak rice overnight" was the
    # bin-it-after-2-hours card about cooked rice.
    entry("rice-soak", (("soak", "soaking", "soaked"),
                        ("rice", "basmati", "jasmine", "long grain", "brown rice", "pilau",
                         "biryani", "pilaf", "white rice", "rice cooker", "sushi rice")),
          "Long grain, basmati and jasmine rice do not need soaking - rinse it in a sieve until "
          "the water runs clear and cook it straight away, and that rinse is what stops it going "
          "sticky. Soak when the dish asks for it: about 30 minutes for pilau or biryani, and an "
          "hour or two for brown rice, then use a little less water because the grains already "
          "hold some. Do not leave raw rice sitting in water overnight on the counter - do it in "
          "the fridge if you want to get ahead.",
          # cooked rice is the keeping and bin-it question, and a rice pudding is a different dish
          avoid=("leftover", "left over", "left out", "left it out", "left it", "cooked",
                 "fridge", "freezer", "freeze",
                 "reheat", "keep", "keeps", "pudding", "risotto", "sushi", "sticky", "soggy",
                 "microwave", "how long does it keep"),
          # A soak verb is the subject, so this holds the tie against the water-ratio answer:
          # "do i need to soak rice before cooking" and "how long should i soak rice" were both
          # told the water ratio, which is the question after the soak, not the soak itself.
          bias=1),
    # And the twin of rice-soak for the other staple people ask it about: soaking pasta is not a
    # thing, and on main the question was answered with the night-sweat card, and then with the
    # bin-it card once the leftover row stopped standing down for a soak. Nobody wants to be told
    # to bin dried pasta.
    entry("pasta-soak", (("soak", "soaking", "soaked"),
                         ("pasta", "spaghetti", "penne", "macaroni", "noodles", "linguine",
                          "fusilli", "tagliatelle", "orzo")),
          "Dried pasta does not need soaking: it cooks in 8 to 12 minutes in salted boiling "
          "water, and soaking it first just makes it pale and floppy. If it is cooked pasta you "
          "mean, it keeps 3 days in the fridge, and anything that sat out for more than 2 hours "
          "gets binned.",
          # cooked pasta is the bin-it and keep questions, and a sauce is a different dish
          avoid=("left out", "left it out", "leftover", "left over", "reheat", "fridge",
                 "freezer", "freeze", "sauce", "salad", "bake", "oven", "cheese")),
    # The rinse is the twin of the soak and has the opposite answer, which is why the two rows
    # name different verbs. On main `871915c7` "should i rinse pasta" was handed to the
    # talk-it-through card ("Not mine to decide, sorry") and "do i need to rinse pasta" was a
    # shrug: the only rinse row in the base is about rice, where the answer is yes.
    entry("pasta-rinse", (("rinse", "rinsing", "rinsed", "wash", "washing", "washed"),
                          ("pasta", "spaghetti", "penne", "macaroni", "linguine", "fusilli",
                           "tagliatelle", "orzo", "noodles")),
          "No, pasta does not need rinsing: it comes out of the pot already wet, and rinsing "
          "cools it and washes off the surface starch that makes a sauce cling. Drain it and "
          "toss it straight into the sauce, keeping a mugful of the cooking water to loosen "
          "things if it looks dry. The one exception is pasta for a cold salad, where a quick "
          "rinse under cold water stops it clumping - then drain it well and dress it while it "
          "is still slightly warm so it takes up the dressing.",
          # cooked pasta has its own keeping and bin-it rows, and a salad is the exception this
          # row already speaks to
          # "canned" is not in this list: an avoid word is matched loosely, so "canned" also
          # matches the line's own "can", and every "can i rinse pasta" was stood down by the
          # word "can" - the row answered "should i", "could i" and "is it ok to" and nothing
          # beginning "can i". "tinned" and "tin" cover the tinned-pasta question without it.
          avoid=("left out", "leftover", "left over", "reheat", "fridge", "freezer", "freeze",
                 "how long", "tomorrow", "sauce", "bake", "oven", "cheese", "jar", "jars",
                 "tinned", "tin"),
          ask=("rinse", "rinsing", "rinsed", "wash", "washing", "washed",
               # "should i rinse the pasta with cold water" is the same question said with the
               # water in it, and on main the cool-bag card took it on "cold water" alone;
               # "can i rinse pasta for a salad" is the exception this reply already speaks to.
               "cold water", "with cold water", "under cold water", "under the tap", "tap",
               "salad", "for a salad",
               # the ask gate is what keeps a sauce and a bake off this row, and it was also
               # keeping out the plainest way people ask: "can i rinse pasta for a salad" was a
               # punt on this branch while "do i need to" and "should i" were answered
               "can i", "can we", "could i", "is it ok", "is it okay", "ok to", "okay to"),
          # "should i rinse the pasta with cold water" ties with the cool-bag card on score and
          # that card carries a bias of 2, so the pasta has to outrank it: this row is only in
          # the running at all when the line names pasta.
          bias=3),
    # "how do i drain pasta" had no row at all: the rinse row wants a rinse verb, the cook row
    # wants water or the clock, and the no-kit table only fires when the line names a colander,
    # so the plainest step of the job was a search hedge while "how do i drain pasta without a
    # colander" was answered. The drain verbs are the key and the rinse words stand it down, so
    # the two rows keep their own lines.
    entry("pasta-drain", (("drain", "draining", "drained", "strain", "straining", "strained",
                           "colander", "sieve"),
                          ("pasta", "spaghetti", "penne", "macaroni", "noodles", "linguine",
                           "fusilli", "tagliatelle", "orzo", "shells")),
          "Scoop out a mugful of the cooking water first, then tip the pasta into a colander in "
          "the sink: that cloudy water is what loosens a sauce that has gone too thick. Shake it "
          "once, do not rinse it, and get it back into the warm pan with the sauce straight "
          "away, because drained pasta starts sticking to itself within a minute. Never leave it "
          "sitting in the colander - it carries on cooking in its own heat and goes soft.",
          avoid=("rinse", "rinsing", "rinsed", "wash", "washing", "washed",
                 "left out", "leftover", "left over", "reheat", "fridge", "freezer", "freeze",
                 "how long", "minutes", "salt", "boil", "boiling", "portion", "how much",
                 "sauce recipe", "bake", "oven", "cheese"),
          ask=("drain", "draining", "drained", "strain", "straining", "strained", "colander",
               "sieve")),
    # The fourth of the same family, because "is it ok to soak cashews overnight" was a
    # night-sweat answer: nuts and dried fruit get a soak for texture, not for safety.
    entry("soak-nuts", (("soak", "soaking", "soaked"),
                        ("cashews", "cashew", "almonds", "almond", "walnuts", "walnut", "nuts",
                         "peanuts", "peanut", "raisins", "raisin", "sultanas", "sultana",
                         "dates", "prunes", "apricots", "dried fruit")),
          "Nuts and dried fruit are safe to soak and nothing spoils while they do it: cover them "
          "in water, keep them in the fridge, and they are soft by morning. Almonds slip their "
          "skins after a night in water, cashews blend smoother for a sauce, and raisins or "
          "dates plump up in warm water in about 20 minutes.",
          # an allergy, a calorie count and a nut that has gone off are all other questions
          avoid=("allergy", "allergic", "anaphylactic", "calories", "protein", "rancid",
                 "gone off", "gone bad", "mouldy", "stale", "bitter", "left out", "left it")),
    entry("pasta-left-out", (("pasta", "spaghetti", "penne", "macaroni", "noodles"),
                             ("left out", "overnight", "all night", "room temperature", "sat out")),
          "Bin it, I'm afraid: cooked pasta left out for more than 2 hours isn't worth eating, "
          "even if it looks and smells fine. Get leftovers into the fridge within the hour next "
          "time and they keep 3 days.",
          # in the fridge is pasta-keep's question; this one is about food left sitting out

          avoid=("fridge", "in the fridge", "refrigerator"),
          # and a soak is not a night on the side, unless the line says it ended there:
          # "can i soak pasta overnight" was told to bin it
          guard=soak_but_not_left_out),
    # "can i put hot food in the fridge" was a hedge and "should i cool food before putting it in
    # the fridge" was answered with how the compressor works, so the one thing a cook wants to
    # know - can a warm pot go in now - was nowhere. The safety rule is cool it fast, not cool it
    # first, and both of those lines are the same question.
    entry("fridge-hot-food",
          (("hot food", "warm food", "hot leftovers", "leftovers", "hot pot", "hot pan",
            # "can i put a warm pot in the fridge" is this row's own headline line, and it
            # answered with an ice-block card because the subject list knew only "hot pot".
            "warm pot", "warm pan", "warm dish", "warm container", "warm pot of", "warm pan of",
            "warm soup", "warm stew", "warm casserole", "warm curry", "warm rice", "warm pasta",
            # the pot with no adjective: "let the pot cool right down before it goes in the
            # fridge" covered no subject word at all, so the mechanism card explained the
            # compressor to someone asking whether to wait.
            "the pot", "a pot", "the pan", "a pan", "the stew", "a stew", "the curry",
            "the soup", "a soup", "the casserole",
            "hot soup", "hot stew", "hot casserole", "soup", "stew", "casserole", "chilli",
            "curry", "rice", "pasta", "food"),
           ("fridge", "refrigerator", "put in the fridge", "put it in the fridge", "go in the fridge",
            "in the fridge", "cool", "cooling", "cool down", "cool it down", "let it cool",
            "leave it to cool", "straight in", "put away",
            # "should i let the pot cool right down before it goes in the fridge" reached the
            # fridge-thermometer card on main: the pot going in is this question, not the gauge.
            "cool right down", "cool before", "cool first", "let the pot cool",
            "let the pan cool", "goes in the fridge", "go in the fridge")),
          "Straight in is fine - a modern fridge copes with a warm pot, and food left on the "
          "counter to cool is the bigger risk. Split a big batch into shallow boxes so it drops "
          "below 5C within 90 minutes, cover it loosely while it is still warm, and keep it away "
          "from the milk and the cooked meat on the shelf below. The rule is cool it fast, not "
          "cool it first.",
          # how the fridge works, how long a leftover keeps and what to do with it are other rows
          # A leftover that is already in the fridge is a keeping question, not a cooling one:
          # "leftover curry in the fridge is it ok" and "my leftovers have been in the fridge
          # since friday" were both told to put the pot straight in, which it had been for days.
          # The warm-pot question names a pot or a pan and no day, and it keeps its answer.
          avoid=("how does", "how do fridges", "compressor", "freezer", "freeze", "defrost",
                 # a dish that is too hot, too spicy or too salty is a fault to fix, and the fix
                 # cards in this file answer it: "the curry is too spicy how do i cool it down"
                 # was told to put the pot straight in the fridge. The cooling words are shared
                 # by the two questions, so the fault stands the fridge question down.
                 "too spicy", "too hot to eat", "too salty", "too much salt", "too bland",
                 "too sweet", "too sour", "too much chilli", "too much chili", "less spicy",
                 "make it milder", "way too spicy", "way too salty",
                 "reheat", "microwave", "how long", "how many days", "recipe", "what can i make",
                 "eat", "safe to eat", "ok to eat", "why is my fridge", "not cold", "frost",
                 "smell", "ice", "left out", "out overnight", "left overnight",
                 "overnight on the counter", "rice left out", "toppings",
                 "reheat in", "pasta bake", "sauce for",
                 # A pan that wants cooling so it can be washed is not a pot going in the fridge,
                 # and "should i let the pan cool before washing" was answered "straight in is
                 # fine - a modern fridge copes with a warm pot". The sink is the tell.
                 "before washing", "before i wash", "before washing up", "washing up",
                 "wash it", "wash the pan", "washing the pan", "in the sink", "the sink",
                 # not a bare "is it ok": "is it ok to put warm food in the fridge" is this
                 # row's own line and it was handed to the fridge-thermometer card by it. The
                 # keeping question always names the leftover, the day or the "still".
                 "is it still ok", "is it still good", "still ok", "still good",
                 "ok after", "good after", "since friday", "since yesterday",
                 "since monday", "since tuesday", "since wednesday", "since thursday",
                 "since saturday", "since sunday", "for 2 days", "for two days", "for 3 days",
                 "for three days", "for 4 days", "for four days", "leftover", "left over",
                 "leftovers in the fridge", "cooked rice in the fridge",
                 # the things that cool at their own speed and are eaten on their own clock are
                 # answered by freshness.cool-before-fridge, which reads what is in the person's
                 # hand: cooked rice has an hour and a reason, a warm bottle of milk is stood in
                 # cold water, and a cake comes out of its tin. This row's shallow box is right
                 # for a pot and wrong for all three.
                 "rice", "milk", "bottle", "bottles", "formula", "baby", "cake", "cakes",
                 "sponge", "muffin", "cupcake", "brownie", "bread", "loaf"),
          # the mechanism card in science.py and the appliance-failure card both scored level
          # with this row on "should i cool food before putting it in the fridge" and
          # "is it ok to put warm food in the fridge": the warm pot is what the question is
          # about, and neither of those answers says whether to put it in.
          bias=2,
          # a pot that has already been in there for days is not a pot going in: "is rice thats
          # been in the fridge 3 days ok" and "cooked pasta in the fridge 5 days ok" were both
          # told to put the pot straight in (see UNDERSTOOD "kept"). The period is the same
          # question said in weeks or months, and it is not in the reading yet, so the words are
          # read too: "the stew has been in the fridge a week" is the keeping rows' line.
          guard=lambda reading: (not reading.get("kept")
                                 and a_cooling_question_not_a_keeping_one(reading))),
    # The study table's "sticks" is memory sticking, and it was answering "how do i keep a
    # barbecue from sticking" with a revision technique. The kitchen word in the line is what
    # says which one it is, and study.py's own fence backs this row up.
    entry("bbq-sticking",
          (("barbecue", "barbecues", "barbeque", "bbq", "bbqs", "grill", "grill bars",
            "barbecue grill", "charcoal grill", "gas grill"),
           ("stick", "sticks", "sticking", "stuck", "stick to")),
          "Oil the food, not the bars: get the grill hot, brush the bars clean, then brush the "
          "meat, fish or veg itself with a little oil and put it on. Leave it alone for three or "
          "four minutes - it frees itself once it has sealed - then turn it with tongs rather than "
          "a fork, and keep a spray bottle of water for flare-ups.",
          # cleaning it is the cleaning row's question, and the grill in a cooker is not this one
          avoid=("clean", "cleaning", "scrub", "rust", "rusty", "winter", "store", "read",
                 "book", "chapter", "revision", "revise", "remember", "study", "exam",
                 "oven", "grill pan", "hob", "toast", "cheese on toast", "bacon", "pasta",
                 "rice", "cake", "dough", "how long", "temperature", "recipe", "marinade"),
          # the pan-sticking card answers "how do i stop meat sticking to the grill" with pasta
          # advice, and the smoke-salmon recipe took "how do i stop fish sticking on the bbq":
          # a grill and a stick word is this row's line whatever the food is, so the bias is
          # three, the same as the oil row's
          bias=3),
    # A keeping question about cooked rice is said as a day: "is cooked rice ok tomorrow",
    # "we had a takeaway last night, is the rice still ok", "leftover rice ok the day after".
    # On main the first was answered with the water ratio for cooking it, the second with the
    # bag in the cupboard, and the third with a card that lists four foods and puts rice third.
    # The day word is the shape, and each phrase here is a keeping shape rather than a day word
    # alone, so "im cooking rice tomorrow, how" keeps its method and "what can i make with
    # leftover rice" keeps its fried-rice answer.
    entry("rice-cooked-tomorrow",
          # "the next day" and "reheat" are left out on purpose: those lines already reach the
          # cooked-rice card on main, and a second card saying the same thing in other words is
          # not an improvement. These are the shapes that did not reach it.
          ("rice", ("ok tomorrow", "tomorrow ok", "safe tomorrow", "the day after", "day after",
                    "still ok the day after", "still good the day after")),
          _COOKED_RICE_KEEPS,
          # nothing here guards on "cook": avoid matches word forms, so it would catch the
          # "cooked rice" in the very line this row is for
          avoid=("water", "minutes", "how long to cook", "pot",
                 "pan", "ratio", "rinse", "raw", "dry", "uncooked", "bag", "packet", "pack",
                 "jar", "airtight", "cupboard", "larder", "past its date", "past the date",
                 "after the date", "out of date", "expired", "opened", "open for", "weevils",
                 "year", "years", "months", "idea", "ideas", "make with", "do with", "use up",
                 "what can i", "anything i can", "recipe", "recipes", "fry", "fried", "freeze",
                 "freezing", "freezer", "burnt", "burned", "burnt bits", "slimy", "smell",
                 "smells", "pudding", "milk", "sugar", "phone", "cat", "dogs", "dog", "cats",
                 "bird", "birds", "pets", "the washing", "laundry", "curry", "sushi",
                 "risotto", "paella", "bake", "baked", "salad"),
          # it has to beat the method rows a rice line fits equally well: the water ratio and
          # the ten to twelve minutes are both "rice" and both confident wrong answers here.
          # Two, because the bag-in-the-cupboard row added since keys "rice" with "still ok" too,
          # and at one the takeaway line came out as the dry-rice card again.
          bias=2),
    # "is my rice still ok" on its own is the cupboard question, and the dry-rice card answers it
    # ("Dry rice keeps for years in an airtight jar") -
    # tests.test_a_slimy_rice_is_not_a_diet_question holds that line. The bag-in-the-cupboard row
    # keys "rice" with "still ok" as well, and on a newer main it won
    # "we had a takeaway last night, is the rice still ok" even at bias 2: the row that names the
    # subject of the line ("rice") is ranked ahead of a row that reaches it on a cue word alone.
    # So this row names the subject as the cupboard row does, and a guard keeps it off the bare
    # line: "is my rice still ok" has no cooked cue in it, and that one is the cupboard question
    # (tests.test_a_slimy_rice_is_not_a_diet_question holds it).
    entry("rice-cooked-still-ok",
          ("rice", ("still ok", "still good", "still be ok", "still safe", "safe to eat",
                    "ok to eat")),
          _COOKED_RICE_KEEPS,
          avoid=("water", "minutes", "how long to cook", "pot", "pan", "ratio", "rinse", "raw",
                 "dry", "uncooked", "bag", "packet", "pack", "jar", "airtight", "cupboard",
                 "larder", "weevils", "year", "years", "months", "idea", "ideas", "make with",
                 "do with", "use up", "recipe", "recipes", "fry", "fried", "freeze", "freezer",
                 "burnt", "burned", "slimy", "smell", "smells", "pudding", "milk", "sugar",
                 "curry", "sushi", "risotto", "paella", "bake", "salad"),
          # two, to sit ahead of the cupboard row that keys the same words at bias 1
          bias=2,
          guard=_the_rice_was_cooked),
    entry("rice-storage", ("rice", ("leftover", "left over", "reheat", "next day", "yesterday",
                                    "gone off", "safe to eat", "ok to eat", "again", "keep",
                                    # "can i leave rice in the fridge for 2 days" was answered
                                    # with ten-minute dinners: the keeping question is asked
                                    # with "leave" as well as "keep"
                                    "leave", "leaves", "leaving", "for 2 days", "for two days",
                                    "for 3 days", "for three days", "few days", "a day",
                                    "fridge", "last", "lasts", "store", "storing", "freeze",
                                    "freezing", "safe", "safe to eat", "how long does cooked rice",
                                    "shelf life", "shelf-life", "good for")),
          ("Cool cooked rice fast and box it: it keeps 24 hours in the fridge, no longer, and "
           "you reheat it once until it's piping hot all the way through. Rice left out at room "
           "temperature is the one leftover worth being strict about."),
          # the bag of rice a wet phone is standing in is not the cooked-rice keeping question,
          # and "how long should i leave it" after "i put it in rice" was answered with the 24
          # hours rule, where the person was asking about the phone
          avoid=("cupboard", "larder", "bag", "tin", "dry", "uncooked", "raw", "buy", "curry",
                 "with curry", "wash", "washing", "rinse", "rinsing", "rice cooker",
                 "leave it", "left it", "phone", "mobile", "iphone", "bath", "battery",
                 "wont turn on")),
    # The other half of the same question: dry rice is not the one that spoils in a day, so
    # "how do i store rice" wanted the cupboard, not the cooked-rice rule.
    entry("pasta-portion", (("pasta", "spaghetti", "penne", "noodles"),
                            ("per person", "portion", "how much", "much", "person", "serving",
                             "handful")),
          ("Allow 75 to 100g of dry pasta per person as a main, or 50g as a starter: a bunch of "
           "spaghetti as thick as a 10p coin is about 80g. Pasta roughly doubles in weight when "
           "cooked, so a 500g packet feeds four or five."),
          # The pan and the water are the other half of "how much": "how much water for pasta"
          # was answered with the weight per person, which is not what was asked.
          avoid=("sauce", "dressing", "salad", "water", "pan", "salted", "salt", "boiling")),
    entry("pasta-water", (("pasta", "spaghetti", "penne", "noodles", "macaroni", "fusilli"),
                          ("water", "pan", "how much water", "litre", "litres", "salt", "salted",
                           "boiling", "rolling boil", "stick", "sticks", "sticking")),
          "About a litre of water for every 100g of pasta: a big pan filled about two thirds, at "
          "a rolling boil before the pasta goes in, and a teaspoon of salt per four litres. Keep "
          "it boiling and stir for the first minute so the pieces do not stick together - there is "
          "no need for oil in the water, which only makes the sauce slide off.",
          # the amount per person is pasta-portion's, and a sauce question is not about the pan
          avoid=("per person", "portion", "sauce", "dressing", "salad", "bake", "lasagne",
                 "lasagna", "soup", "pudding", "how long", "gluten")),
    entry("slow-cooker-burning", (("slow cooker", "slow cookers", "slow-cooker", "crockpot",
                                   "crock pot", "slowcooker"),
                                  ("burn", "burns", "burning", "burnt", "burned", "sticking",
                                   "sticks", "stuck", "catch", "catches", "catching", "caught",
                                   "dried out", "drying out", "dry out", "scorch", "scorched",
                                   "overcook", "overcooked", "too hot", "on the bottom",
                                   "the bottom")),
          "Nearly always too little liquid: the food should be at least a third covered, and the "
          "pot no more than two thirds full. Cook on low rather than high, keep the lid on (every "
          "lift loses about 20 minutes of heat), and add milk, cream or flour in the last half "
          "hour, because dairy and thickeners are what catch. A liner or a smear of oil stops the "
          "edges sticking, and if it only ever burns round the sides the pot is thin-based and "
          "running hot - a tea towel under it or a new pot fixes that.",
          # leaving it on while you are out, the recipes and the cleaning are other answers
          avoid=("left on", "leave on", "left it on", "overnight", "all night", "all day",
                 "while im out", "while i am out", "safe", "recipe", "recipes",
                 "what can i cook", "what to cook", "dinner ideas", "clean", "cleaning",
                 "smell", "smells", "what can i make"),
          # "how do i stop my slow cooker from burning things" and "why does my slow cooker dry
          # out" are the fault, not a plan: the recipe list outbid this row on the plain words,
          # and the walking row took the drying out one on "out".
          bias=1),
    entry("rice-portion", ("rice", ("per person", "portion", "much", "person", "serving")),
          "Allow about 75g of dry rice per person, or a mugful for two: it swells to two or three "
          "times its size, and leftover rice is better under- than over-estimated."),
    entry("rice-water", ("rice", ("water", "ratio", "much water", "how long", "long", "time",
                                  "takes", "take", "cook")),
          _rice_time,
          # how long it keeps, and a rice pudding or a paella, are other questions
          avoid=("fridge", "keep", "keeps", "keep for", "leftover", "left out", "freeze", "freezer",
                 # a bag of rice a phone is sitting in is not being cooked: "how long should i
                 # leave it" after "i put it in rice" was answered with the pan method and the
                 # water ratio, where the person was asking about the phone
                 "leave it", "leave it in", "left it in", "phone", "mobile", "iphone", "device",
                 "battery", "bath", "water damage", "wont turn on", "drained",
                 "pudding", "paella", "risotto", "pilau", "sushi", "milk", "sugar",
                 # a rice cooker, a microwave or a pressure cooker is its own set of timings
                 "cooker", "microwave", "pressure", "steamer", "instant",
                 # how long dry rice keeps is the cupboard question, not the pan one
                 "uncooked", "store", "storing", "stored", "last", "lasts", "jar", "airtight",
                 # wild rice takes 40 to 45 minutes and cauliflower "rice" is grated and fried
                 # with no water at all, so neither wants the long-grain method; and rice
                 # noodles are cooked like pasta, drained rather than absorbed
                 "wild", "cauliflower", "noodles")),
    entry("quinoa", ("quinoa", ("cook", "water", "time", "bitter")),
          "Rinse quinoa well, simmer it in twice its volume of salted water for 15 minutes, then "
          "drain and let it steam with the lid on for 5. Rinsing takes off the bitter coating; the "
          "grains are done when the little tails pop out."),
    entry("porridge", (("porridge", "oats", "oatmeal"), ("water", "milk", "creamy", "lumpy",
                                              "cook", "gluey", "stodgy", "thick", "stirring",
                                              "microwave", "make", "how long", "time")),
          _porridge,
          # "what can i make with oats" asks for ideas, not the porridge method; overnight oats
          # are soaked cold, so they want the fridge; and a baby's porridge is not the adult
          # method, because salt is the one thing that must not go into a baby's food.
          avoid=("what can i make", "what else", "ideas", "recipes", "biscuits", "cookies",
                 "flapjack", "granola", "muesli", "bread", "cakes", "muffins",
                 # "is oat milk as good as cows milk" compares drinks; it is not the bowl method
                 "as good", "better than", "instead of", "good for", "healthy", "fattening",
                 "which milk",
                 "overnight", "soak", "soaked", "soaking", "no cook", "uncooked",
                 "cold water", "jar", "baby", "babies", "weaning", "wean", "toddler",
                 "toddlers", "under one", "6 months", "six months", "first foods",
                 "blw", "puree")),
entry("porridge-fault",
          (("porridge", "porridge oats", "oats", "oatmeal", "ready brek", "readybrek",
            "oat so simple", "overnight oats"),
           ("too much sugar", "too sweet", "sweet", "sugary", "over sweet", "oversweet",
            "too much honey", "honey", "golden syrup", "jam", "syrup",
            "too salty", "salty", "too much salt", "over salted", "oversalted", "salt",
            "bland", "tastes of nothing", "no taste", "tasteless", "nothing in it")),
          _porridge_fault,
          # the method, the ingredient questions and the baking are other rows, and a bowl that is
          # loose, thick or lumpy already has its own answer
          avoid=("how do i make", "how to cook", "how do i cook", "how long", "microwave",
                 "what can i make", "what else", "ideas", "recipe", "recipes", "biscuits",
                 "cookies", "flapjack", "granola", "muesli", "bread", "cakes", "muffins",
                 "healthy", "healthier", "fattening", "calories", "good for you", "which milk",
                 "as good", "better than", "instead of", "baby", "babies", "weaning", "toddler",
                 "lumpy", "gluey", "stodgy", "watery", "too thin", "too thick", "thick",
                 "sauce", "soup", "stew", "curry", "bread sauce"),
          bias=2),
    # Soaked oats had nowhere to go: the porridge row stands down for "overnight" and "soak",
    # because they are made cold in the fridge, and the health rows stand down for a cooking step,
    # so "do i need to soak porridge oats overnight" was answered with the night-sweats card.
    entry("overnight-oats",
          (("oats", "oat", "oatmeal", "porridge", "bircher"),
           ("soak", "soaked", "soaking", "overnight", "jar")),
          _overnight_oats,
          # the hot bowl, the baby's bowl and a coeliac question are other rows' lines
          avoid=("boil", "boiled", "cook oats", "cooking oats", "cooked oats", "how do i cook",
                 "how to cook", "how long do oats", "how long does porridge", "microwave",
                 "simmer", "lumpy",
                 "creamy", "stodgy", "gluey", "baby", "babies", "toddler", "weaning", "wean",
                 "coeliac", "celiac", "gluten", "allergy", "allergic", "reaction", "rash",
                 "fattening", "calories", "how many calories", "weight",
                 # a flapjack or a biscuit uses oats dry: soaking is not the step there
                 "flapjack", "flapjacks", "biscuits", "cookies", "muffins", "bread",
                 "granola", "muesli")),
    entry("couscous", ("couscous", ("cook", "water", "fluffy", "lumpy")),
          "Pour boiling water or stock over the couscous to just cover it, cover the bowl and leave "
          "it 5 minutes, then fork it through with a little olive oil. Never stir it with a spoon: "
          "that's what makes it clumpy."),
    # "water" alone used to be in this key and pulled every salt-and-water line here (rice,
    # potatoes, blanching), so the water is named only as pasta water: the phrase.
    entry("pasta-salt", (("pasta", "spaghetti", "penne", "noodles", "salt the water",
                          "salting the water", "salted the water", "salt in the water",
                          "water for pasta", "pasta water"),
                          ("salt", "salted", "salty")),
          ("Salt the water properly: about 10g, a heaped teaspoon, per litre of boiling water, so a "
           "big pan takes a good tablespoon. That is what seasons the pasta itself, since it takes "
           "up the salt while it cooks. Add it once the water is boiling so it dissolves fast, and "
           "taste the water - it should taste like the sea, not like a mistake."),
          # "salt the water" is the pasta phrase; the same words about rice, potatoes or
          # vegetables are those entries' questions
          avoid=("rice", "potato", "potatoes", "veg", "vegetables", "beans", "peas", "broccoli",
                 "egg", "eggs", "blanch", "blanching", "bread", "dough", "cake", "stock"),
          bias=2),
    # A line that names the pasta and the sticking is the pasta question; fix-sticking (the
    # general "it stuck to the pan" entry, bias=1) used to outscore it and answer with the pan.
    entry("pasta-cook", (("pasta", "spaghetti", "noodles", "linguine", "penne", "macaroni"),
                         ("water", "salt", "boil", "time", "cook", "lump", "lumps",
                          "sticking", "stick",
                                    "together", "clump", "clumps",
                          # "how long does pasta take" asks the same thing without the word time
                          "long", "take", "takes", "minutes")),
          _pasta_cook,
          # a portion question names the pasta too ("how much pasta is one portion, i always cook
          # too much"), so without this the higher bias above would take pasta-portion's lines.
          # "sticking to the pan" is the general fault entry's line whatever is in the pan
          # "keeps" alone is not a keeping question ("my pasta keeps sticking together" is the
          # cooking one), but the fridge and the leftover words are: those are pasta-keep's
          avoid=("portion", "portions", "per person", "how much", "serving",
                 # "it's glued to the pan" is fix-sticking's question; a pasta that clumps in the
                 # water is this one, so only the sticking-to-the-pan phrases are kept out
                 # "how do i stop pasta boiling over" is the pot, not the clock or the salt:
                 # pan-boil-over in cooking.py owns it, and this row answered it with the method.
                 "boil over", "boils over", "boiling over", "boiled over", "overflow", "overflows",
                 "spill", "spills", "spilling", "spilled", "spilt",
                 "sticks to the pan", "stuck to the pan", "sticking to the pan", "glued to the pan",
                 "bottom of the pan", "bottom of my pan", "saucepan",
                 "fridge", "in the fridge", "leftover", "left over", "next day", "gone off",
                 # a bowl cooked yesterday is the keeping question: pasta-keep has that answer
                 *(_DAY_BEFORE),
                 # and so is the bowl kept for tomorrow. "cooked" is a form of this entry's own
                 # "cook", so the keeping shapes have to hold the pan entry out: "how do i store
                 # cooked pasta overnight" and "is cooked pasta ok tomorrow" were the method for
                 # boiling it. A bare "keep" or "store" is not enough - "my pasta keeps sticking
                 # together" is this entry's own line - so the day and the pronoun are the shapes.
                 "for tomorrow", "until tomorrow", "til tomorrow", "till tomorrow",
                 # a bare "tomorrow" stood the pan row down for a plan as well: "i am cooking
                 # pasta for 8 tomorrow" is a dish to cook and lost its method to a stall. The
                 # clock is a keeping question only when the line asks whether the pasta is
                 # still good, so the ok-shapes are what hold the pan row out.
                 "ok tomorrow", "okay tomorrow", "still ok tomorrow", "tomorrow ok",
                 "ok overnight", "okay overnight", "still ok overnight", "ok the next day",
                 "okay the next day", "keep overnight", "store overnight",
                 "in the fridge overnight", "overnight in the fridge",
                 "left out overnight", "sat out overnight",
                 "keep it", "keep the rest", "keep leftovers", "keep leftover",
                 "store it", "storing", "store the rest", "stored",
                 # a keeping verb on a word that says the pasta is already cooked is the box in
                 # the fridge, whatever day it names: "how do i keep cooked pasta overnight" has
                 # no "ok" shape in it. "cooked" after the verb is what tells it apart from the
                 # pan's own "my pasta keeps sticking together".
                 "keep cooked", "keeps cooked", "keeping cooked", "kept cooked",
                 "keep the cooked", "store cooked", "stores cooked", "storing cooked",
                 "stored cooked", "store the cooked",
                 # freezing pasta is the freeze table's question: "can i freeze cooked pasta"
                 # was the boiling times, because "cooked" is a form of this entry's "cook"
                 "freeze", "freezing", "frozen", "freezer", "defrost", "defrosting",
                 # a pasta bake is its own dish with its own oven plan, not a pan of pasta
                 "bake", "baked", "oven", "baking",
                 # "how long does cooked pasta last" is a keeping question, not a timing one:
                 # pasta-keep asks on the keeping words, and this entry keys "long" and "take"
                 # for the pan, so a keeping word is what tells the two apart.
                 "last", "lasts", "lasting", "days", "day") + _MEAL_ASK_AVOID + WANT_SOMETHING_ELSE,
          bias=1),
    entry("pasta-keep", (("pasta", "spaghetti", "penne", "noodles", "macaroni"),
                         ("fridge", "keep", "store", "leftover", "left over", "next day", "last",
                          "safe", "reheat",
                          # the day words are the cooked bowl's question, and keeping.py's dried
                          # row stands down for them, so this is where "can i eat pasta the day
                          # after" now lands instead of on the two-year cupboard.
                          "the day after", "day after", "a day after", "day later",
                          "a day later", "the following day", "following day", "yesterday",
                          "last night",
                          # "is cooked pasta ok tomorrow" names no keeping verb at all, and it
                          # reached the pan entry; the day itself is a keeping word, and it is
                          # the one people use.
                          "tomorrow", "overnight", "next morning")),
          ("Cooked pasta keeps 3 days in the fridge in a sealed box, tossed with a little oil so it "
           "doesn't clump. Reheat it in the sauce with a splash of water until piping hot, once "
           "only, and bin it if it smells sour or feels slimy."),
          # bias 1: "how long does cooked pasta last" is held apart from the boiling entry by
          # pasta-cook's own `last`/`days` avoid, because a bias here lifts this entry over the
          # keeping table's pasta row and "how do i store pasta" came back with the cooked rule.
          ask=KEEP_ASK, bias=1,
          # "what do i do with leftover pasta" wants a way to eat it, not a storage rule. Dry,
          # fresh and opened pasta are cupboard stock, and keeping.py's pasta row has that answer;
          # this entry used to take those lines whenever the timing entry stood aside.
          avoid=("fry", "fried", "make", "made", "recipe", "recipes", "ideas", "do with", "bake",
                 "baked", "use up", "turn into", "dry", "dried", "uncooked", "fresh", "opened",
                 "open packet", "packet", "cupboard", "larder", "tin", "jar",
                 # "how do i keep pasta warm" is the pan, not the box in the fridge
                 # "i need a pasta dish for tomorrow night" is a menu request: with only the
                 # day in the pan row's avoid it reached the box in the fridge, so a dish,
                 # a meal or an idea stands the keeping row down and a recipe answers.
                 "dish", "dishes", "a dish", "meal", "meals", "menu", "dinner", "supper",
                 "something to eat", "idea", "ideas",
                 # a soak is a step before cooking, not a way to keep a cooked bowl: the words
                 # are the answer that says dried pasta and rice are boiled, not soaked
                 "soak", "soaks", "soaking", "soaked",
                 ) + KEEP_QUALITY_WORDS),
    # The sauce by its own name: "how do i make tomato sauce", "a quick tomato sauce" and "how do
    # i make a quick tomato sauce" were a shrug, a hedge and "Eggs are the fastest dinner there
    # is", because the row wanted the word "pasta" in the line and the sauce is most often named
    # without it. The tin, the garlic and the fifteen minutes are the same answer either way.
    entry("pasta-sauce", (("pasta", "tomato sauce", "tomato sauces", "passata", "marinara",
                           "napoli sauce", "napolitana sauce",
                           # The sauce made from the fruit goes by the tin as often as by the
                           # name: "how long do i cook tinned tomatoes" and "how long should i
                           # simmer chopped tomatoes" were a hedge and the drawer card.
                           "tinned tomatoes", "chopped tomatoes", "tin of tomatoes",
                           "simmered tomatoes", "tomatoes"),
                          # No question words and no bare "make" in the second part: "how do i"
                          # and "make" between them made every pasta question reach this row, so
                          # "how do i make pasta" was answered with the sauce. 
                          ("sauce", "tomato", "quick", "dinner", "easy", "recipe",
                           "homemade", "from scratch", "tinned", "passata",
                           # the pan's own words, so "how long do i simmer passata" and
                           # "how many minutes should the sauce simmer" are the minutes
                           "simmer", "simmering", "boil", "boiling", "how long", "minutes",
                           "how many minutes", "cook", "cooking", "pan", "hob", "stir")),
          _tomato_sauce,
          # "can i freeze pasta sauce" and "how long does pasta sauce keep" are the keeping
          # questions, which the entry below answers: a recipe cannot answer either of them.
          avoid=("keep", "keeps", "keeping", "store", "storing", "stored", "fridge", "freezer",
                 "freeze", "frozen", "last", "lasts", "lasting", "tomorrow",
                 "overnight", "next day", "the day after", "gone off", "go off", "still ok",
                 "still good", "open jar", "opened jar", "jar of",
                 # whether a tin is still good is a keeping question too, and "is a tin of
                 # tomatoes ok after the date" was answered with the 15-minute sauce
                 "out of date", "past the date", "after the date", "use by", "best before",
                 "expired", "date on",
                 # "im making a pasta bake" and "what can i make with leftover pasta" are a
                 # dish and a use-up, not the sauce, and the row now answers the sauce by its
                 # own name. Written as whole phrases: "making a" as an avoid word also stood
                 # the row down for "how do i make a tomato pasta sauce", because an avoid word
                 # matches the other forms of itself and "making" is "make".
                 "im making", "i am making", "pasta bake", "lasagne", "lasagna", "casserole",
                 "leftover", "leftovers", "use up", "do with", "make with", "what can i make",
                 "what should i make", "tray",
                 # "tomato sauce on a white shirt" is a stain, not a recipe
                 "stain", "stains", "stained", "shirt", "shirts", "carpet", "sofa",
                 "settee", "tablecloth", "splashed", "spilled", "spilt", "dripped", "got on",
                 "on my", "remove", "get out", "get off", "clean off", "wipe",
                 # a sauce the person already has, and something wrong with it, is a fault
                 # question: the card simmers, blends a ladleful and stirs it back, and it was
                 # losing those lines to the recipe once the recipe answered to the sauce's own
                 # name. "thicker" is the commonest of them.
                 "thicker", "thick", "too thin", "watery", "reduce", "reduction",
                 "bland", "acidic", "bitter", "too sweet", "too sour", "sour", "salty",
                 "too salty", "split", "separated", "burnt", "burned", "caught", "gone wrong",
                 # whether a sauce is good for you is the nutrition card's question
                 "healthy", "health", "good for you", "bad for you", "calories", "sugar",
                 "nutrition", "diet",
                 # a sauce for a pizza is the dough's page, and it has its own answer
                 "pizza", "pizza base", "pizza bases", "for pizza")),
    # --- eggs ----------------------------------------------------------------
    # bias 1 puts these times level with the keeping entries, which also carry "soft": the
    # follow-up "and a soft one" reaches whichever the line leans on, and a timer is what was
    # asked for after a timer.
    # The bare line, when the learner card stood down for the foods. "how do i cook an egg" was
    # the four-things card and then a hedge, which is worse than either: the three everyday ways
    # with an egg are short enough to say in one answer, and each of them has its own row for the
    # line that names it (so this row steps aside for every one of those words).
    entry("egg-cook", (("egg", "eggs"), ("cook", "cooking", "cooked")),
          "Boil them 6 minutes for a runny yolk or 9 to 10 for hard boiled, lowering them into "
          "water that is already boiling and cooling them under the tap before you peel. Frying "
          "is butter in a hot pan, 2 to 3 minutes for a runny yolk, and scrambling is low heat "
          "and slow stirring, off the heat while it is still glossy.",
          avoid=("boil", "boiled", "boiling", "fry", "fried", "frying", "poach", "poached",
                 "poaching", "scramble", "scrambled", "scrambling", "omelette", "microwave",
                 "hard", "soft", "runny", "yolk", "shell", "crack", "cracked", "separate",
                 "fresh", "float", "safe", "pregnant", "baby", "babies", "keep", "keeps",
                 "store", "storing", "leftover", "leftovers", "replace", "substitute", "vegan",
                 "allergy", "allergic", "rice", "fried rice")),
    # "how do i make a dippy egg" named the dip and no boil at all and was a punt: the dippy egg
    # is the boiled one with soldiers, so the word is in the key beside "dipping".
    entry("egg-boil", (("egg", "eggs"), ("runny", "soft", "boiled", "yolk", "dipping",
                                          "dippy")),
          "Lower eggs into already boiling water: 6 minutes for a runny yolk, 7 for jammy, 9 to 10 "
          "for hard boiled. Cool them in cold water for a minute before peeling so the shell comes "
          "away cleanly.",
          # "how long are boiled eggs good for" is how long they keep, not how long to boil them,
          # and "boiled" is the cooking word as well as the keeping word. The keeping rows hold
          # these shapes, so this one stands down for them.
          avoid=("good for", "keep", "keeps", "keeping", "last", "lasts", "fridge",
                 "use by", "out of date", "go off", "gone off",
                 # "how do i get a runny fried egg" was these boiling times: a runny yolk in a
                 # pan is the fried or the poached egg, and each of those has its own row
                 "fry", "fried", "frying", "poach", "poached", "poaching", "scramble",
                 "scrambled", "omelette", "green", "grey", "gray") + _NUTRIENT_ASK_WORDS),
    # "and a soft one" after the times above is the same question narrowed, and the times answer
    # already gave the soft end of it, so this one adds the extra minute detail instead of
    # repeating the whole range.
    # "how do i make a runny yolk" and "how do i get a soft yolk" name no egg at all: the yolk is
    # the subject and the runny or jammy word is the ask, so both are spelled out in the key. The
    # answer opens on the soft egg itself ("for a soft one, 5 to 6 minutes") so it reads as an
    # answer to that line as well as to the follow-up it was written for.
    entry("egg-boil-soft", (("egg", "eggs", "yolk", "yolks", "egg yolk", "egg yolks"),
                            ("soft", "soft boiled", "runny", "jammy")),
          "For a soft one, 5 to 6 minutes: 5 leaves the yolk running, 6 gives a set white with a "
          "soft middle. Cool it under cold water the moment it comes out, or it carries on cooking "
          "in its own heat.", bias=1,
          # A runny yolk asked about a person is a food-safety question, and `raw-egg` is the entry
          # that knows the Lion mark (snug-parrot: "is a soft boiled egg safe when pregnant" and
          # "is soft boiled egg ok for a baby" were getting the five-minute time instead).
          avoid=("safe", "safely", "ok", "okay", "fine", "risk", "pregnant", "pregnancy",
                 "baby", "babies", "toddler", "child", "children", "kids", "dipping soldiers",
                 # a runny yolk in a pan is the fried or the poached egg, not the boiled one
                 "fry", "fried", "frying", "poach", "poached", "poaching", "scramble",
                 "scrambled", "omelette", "green", "grey", "gray", "ring", "peel", "peeling",
                 # how long a soft boiled egg keeps is the keeping row's question, the same way
                 # it is for a hard boiled one
                 "good for", "keep", "keeps", "keeping", "last", "lasts", "fridge",
                 "use by", "out of date", "go off", "gone off") + _NUTRIENT_ASK_WORDS),
    # "how do i stop eggs cracking when boiling" was the six-minute timing: the two cracking
    # entries keep out of the pan on purpose (a shell that is already cracked, and how to open
    # one, are their questions), so nothing said why an egg splits in the water.
    entry("egg-crack-boiling", (("egg", "eggs"), ("crack", "cracks", "cracking", "cracked",
                                                  "split", "splits", "burst", "bursts", "bust",
                                                  "explode", "explodes", "exploded")),
          "Nearly always the air pocket at the fat end: prick that end with a pin first, lower "
          "them in on a spoon instead of dropping them, and take them out of the fridge ten "
          "minutes before so the shell is not cold when it meets the heat. Keep the water at a "
          "gentle simmer rather than a rolling boil, and a splash of vinegar in the pan sets any "
          "white that leaks before it trails.",
          # the pan is the gate: "how do i crack an egg" is the method, and a shell cracked in
          # the box is the food-safety question
          ask=("boil", "boiling", "boiled", "pan", "pot", "water", "simmer"),
          avoid=("phone", "screen", "window", "wall", "pavement", "lips", "skin", "joke", "nuts",
                 "coconut", "cracker", "crackers", "carton", "box", "shell went in",
                 "bit of shell"),
          bias=1),
    entry("egg-scramble", (("egg", "eggs", "scrambled"), ("rubbery", "rubber", "tough", "dry",
                                                          "watery", "wet", "runny", "sloppy",
                                                          "fluffy", "scramble", "scrambling")),
          _scramble,
          # "runny" is here for "how do i keep scrambled eggs runny", and it also caught
          # "how do i get a runny fried egg", which is a pan of hot fat rather than a fork and a
          # jug: the fried, boiled and poached eggs each have their own row, so they stand this
          # one down
          avoid=("fry", "fried", "frying", "boil", "boiled", "boiling", "poach", "poached",
                 "poaching", "omelette", "omelet")),
    entry("egg-poach", (("egg", "eggs"), ("poach", "poached", "poaching")),
          "Bring a pan of water to a bare simmer with a splash of vinegar, stir it into a gentle "
          "whirlpool and slide the egg in from a cup. 3 minutes gives a soft yolk; lift it out with "
          "a slotted spoon onto kitchen paper."),
    entry("egg-fresh", (("egg", "eggs"), ("fresh", "float", "old", "test", "off", "bad", "rotten",
                                          "date", "dates", "expired", "keep", "keeps", "last",
                                          "lasts", "longer", "store", "storing", "safe")),
          # the keys are storing words as well as freshness ones, so the reply leads with
          # whichever of the two the line asked about
          _eggs),
    # The time leads, because "how long does an omelette take" is the same ask as "how do i make
    # one" and only the time was missing from the answer: every other staple that answers the
    # method answers the clock in its first sentence (pasta, rice, a jacket potato), and "how long
    # does an omelette take to cook" already landed here while the plain "take" was a search
    # hedge. The key words carry the time question as well as the method ones, so both land.
    entry("omelette", (("omelette", "omelet"),
                       ("filling", "fillings", "easy", "make", "fold", "cook",
                        "long", "take", "takes", "time", "minutes", "put", "inside",
                        "flip", "flipping",
                        # "how many eggs go in an omelette" is this row's question, and the
                        # count is in its first sentence. The cholesterol card used to take it
                        # because "how many" is in its key for the daily allowance; now that the
                        # allowance stands down on the verb, this row has to take the line, or the
                        # bot answers a count it knows with a shrug.
                        "how many")),
          "Two to three minutes in the pan: beat two eggs with a pinch of salt, pour them into a "
          "hot buttered pan and pull the set edges inwards with a spatula. Add cheese, mushrooms "
          "or ham on one half, fold it over and slide it out while the middle is still soft."),
    # The fault word is the same in every egg dish and the fix is not: the pan, the oven and the
    # jug each need their own numbers, and each of these lines was answered by another food
    # before (pancake batter, tough pastry) or by nothing at all.
    # "how do i make creme anglaise" and "how do i make pastry cream" were a punt, and the one
    # worth answering before the faults, because a sauce that has not curdled yet is a method.
    entry("creme-anglaise", (_EGG_SAUCE, ("make", "makes", "making", "how", "recipe", "method",
                                          "custard", "thicken", "thickens", "thickening")),
          "Warm 300ml double cream with a vanilla pod or a teaspoon of paste and 100ml of milk "
          "until it steams, and beat 4 egg yolks with 60g of sugar. Pour the hot cream into the "
          "yolks slowly, whisking, then put it back on a low heat and stir without stopping for 4 "
          "to 6 minutes, to about 82C, until it coats the back of the spoon. Strain it into a jug "
          "and it thickens as it cools.",
          avoid=("flour", "cake", "grainy", "gritty", "split", "curdled", "filling", "pie"),
          bias=1),
    entry("egg-dish-fault", (_EGG_DISH, _EGG_FAULT), _egg_fault,
          avoid=("chicken", "meat", "steak", "pork", "lamb", "beef", "turkey", "fish", "tofu",
                 "cake", "biscuit", "biscuits", "bread", "pasta", "rice", "potato", "potatoes",
                 "muffin", "muffins", "scrambled", "scrambling", "poached", "boiled", "microwave",
                 "skin", "hair"),
          bias=1),

    # --- chicken, meat, fish ------------------------------------------------
    entry("chicken-done", ("chicken", ("temperature", "temp", "internal", "thermometer", "75",
                                       "74", "done", "cooked through",
                                       # the plain way people ask it: "how do i know if chicken is
                                       # cooked", "is my chicken cooked", "how do i check it"
                                       "know", "knowing", "tell", "check", "checking", "cooked")),
          ("Chicken is cooked when the thickest part reaches 75C on a digital thermometer, pushed "
           "into the thigh without touching bone; 74C held for a minute is the same thing. The "
           "juices run clear and no pink is left. A whole bird at 190C (170C fan) takes 20 minutes "
           "per 500g plus 20."), bias=1,
          # The key now holds "cooked", and a loose form of that is "cook", so "chicken cooking
          # time" and "how do i cook chicken" reach this entry as well. The line has to be asking
          # how to tell before this answers, and then the timing entry keeps its own lines.
          ask=("know", "knowing", "tell", "check", "checking", "done", "cooked through",
               "temperature", "temp", "thermometer", "internal", "is my", "is the", "is it",
               "when is it done", "when its done"),
          # Oven temperature, storage and "is it safe to eat" are other entries' questions.
          avoid=("oven", "fan oven", "gas mark", "safe to eat", "is it safe", "left out",
                 "overnight", "pink", "raw", "fridge", "freezer", "frozen", "defrost", "keep",
                 "store", "breast", "thigh", "roast", "roasting", "roasted", "how long",
                 "kg", "whole bird", "per 500g", "minutes",
                 # a cooked bird that has gone off is a keeping question, and one already
                 # cooked is a leftovers question
                 "already", "off", "gone off", "fresh", "smell", "smells",
                 # a bird left out all night is a food-safety question, and the words are not
                 # next to each other in that line, so both halves are named
                 "left", "out all night", "all night", "overnight", "room temperature",
                 # and washing a raw bird before it goes in is a hygiene question
                 "wash", "washing", "washed", "rinse", "rinsing")),
    entry("roast-chicken", ("chicken", ("how long", "time", "roast", "roasting", "cook", "oven",
                                        "per pound", "per lb", "pound", "minutes per")),
          _chicken_time, avoid=("pox", "wing", "soup", "stock", "salad", "nugget", "thigh",
                                # a line that says rest is asking about the rest, not the minutes
                                # in the oven: rest-meat answers it
                                "rest", "resting", "rested",
                                # the skin has its own answer, and a line that says what the skin
                                # should be like is asking for it, not for the minutes
                                "skin", "skinless", "crispy", "crisp", "crackling", "golden",
                                "pale", "flabby", "soggy skin",
                                "breast", "leg", "legs", "drumstick", "drumsticks",
                                # a tender or a strip is a thin piece with its own minutes, and
                                # "tender" alone is the texture of the meat, not a time
                                "tender", "tenders", "strip", "strips", "goujon", "goujons",
                                "fridge", "freezer", "frozen", "freeze", "leftover",
                                # "I've got half a roast chicken left over" is not a cooking-time
                                # question: the bird is already cooked, they are asking what to do
                                # with the rest of it, and "how long does chicken take to defrost"
                                # is thawing time, which chicken-defrost answers.
                                "left over", "left", "spare", "already cooked", "keep",
                                "shelf life", "shelf-life", "good for",
                                # "how long till chicken goes off" is a keeping question, and the
                                # oven time is the one answer a person asking when to bin it must
                                # not get. The "done" entry above already stands down on "off";
                                # this one did not.
                                "off", "go off", "goes off", "going off", "gone off",
                                "defrost", "defrosting", "defrosted", "thaw", "thawing", "thawed",
                                "unthaw",
                                # a curry, a pie or a casserole is a different cooking question
                                "curry", "casserole", "pie", "stew", "simmer", "soup",
                                # and a marinade question is about flavour and time in the fridge,
                                # not about how long the bird roasts
                                "marinade", "marinate", "marinating", "marinated",
                                # "how many pounds of chicken for 12 people" is a quantity of
                                # meat, not a cooking time, and it arrives here on the word
                                # "pound" in the key. The quantity is named by what it weighs or
                                # how many birds, never by who is eating: a portion is not a
                                # subject, so "how do i roast a chicken for 6 people" keeps the
                                # time every other dish row gives it.
                                "how many pounds", "how many lb", "how many kilos", "how many kg",
                                "how many grams", "how many birds", "how many chickens",
                                "how many do i need", "how much chicken", "how much do i need",
                                "how much will i need", "per person", "each",
                                # an air fryer is a different oven: the minutes below are for a
                                # 190C oven, and there is no air-fryer row yet, so the honest
                                # answer there is that this one does not know.
                                "air fryer", "airfryer", "air fry", "air frying") + WANT_SOMETHING_ELSE
                                + PET_LINE_WORDS),
    # "how long do chicken tenders take" was reaching the lifespan of a hen and "how do i cook
    # chicken tenders" the time for a 2kg bird, so the piece has a row of its own. The key holds
    # the plural only: "chicken tender" on its own is the texture of the meat ("how do i make my
    # chicken tender"), which is not a cooking time and gets nothing from this.
    entry("chicken-tenders", (("chicken tenders", "chicken strips", "chicken goujons", "tenders",
                               "goujons"),
                              ("how long", "long", "time", "times", "minutes", "minute", "oven",
                               "cook", "cooking", "cooked", "bake", "baked", "baking", "fry",
                               "fried", "frying", "grill", "grilled", "grilling", "air fryer",
                               "airfryer", "air", "recipe", "recipes", "temperature", "temp",
                               "done", "way", "ways", "roast", "roasted", "make", "makes",
                               "making", "boil", "boiled", "boiling")),
          _tenders_method, guard=_tenders_are_a_piece,
          # This card keys on "tender" as the texture of the meat and is nudged 3 to beat the
          # keeping rows. A line that names the piece is asking for its minutes, so this row
          # carries the same 3 and wins on the extra key word instead of on a nudge.
          bias=3,
          # a tray of tenders already cooked is a leftovers question, and "how many calories in
          # chicken tenders" asks about the meat, not the oven
          avoid=("leftover", "left over", "leftovers", "already cooked", "use up", "using up",
                 "salad", "soup", "stock", "sandwich", "wrap", "dog", "cat", "puppy", "kitten",
                 "pet", "vet", "nugget", "nuggets", "wing", "pox", "defrost", "thaw", "frozen",
                 "freezer", "how many", "how much", "calories", "protein", "tough", "rubbery",
                 "chewy", "texture", "side dish", "sauce")),
    entry("chicken-stuffed", ("chicken", ("stuff", "stuffing", "stuffed")),
          "Stuff the neck end only and weigh the bird with the stuffing in: use the same 20 minutes "
          "per 500g plus 20, so usually 15 to 20 minutes longer. Check the stuffing is piping hot "
          "in the middle, not just the meat."),
    # "brest" is written down here: it is one slip from "breast", but also one from "rest", and
    # the typo reader will not choose between two meanings. Without the word the line fell through
    # to the plan entry, which timed a whole bird and told a breast question 500g and 20 minutes.
    entry("chicken-breast", (("chicken breast", "chicken breasts", "chicken brest",
                              "chicken brests"), ("juicy", "dry", "how long", "moist",
                                                  "moisture", "cook", "time")),
          "Flatten chicken breasts to an even thickness, season them and roast at 200C (180C fan) "
          "for 18 to 20 minutes, or until the middle is 74C. Resting them for 5 minutes keeps the "
          "juice in; slicing them straight from the oven is what dries them out."),
    entry("chicken-thighs", ("chicken", ("thigh", "thighs")), _thighs, bias=1,
          # a thigh already cooked is a leftover question, not a cooking time, the same way a leg
          # is: "how do i use up leftover chicken thighs" wants the cooked-chicken answer and got
          # 35 to 40 minutes at 200C.
          avoid=("leftover", "left over", "leftovers", "already cooked", "next day",
                 "cold chicken", "what can i do with", "what can i make", "use up", "using up",
                 "soup", "stock", "sandwich", "salad")),
    # A leg is a piece like a thigh and the times are its own: this is the entry the whole-bird
    # answer used to take ("a chicken leg how long" timed a 2kg bird).
    entry("chicken-legs", ("chicken", ("leg", "legs", "drumstick", "drumsticks")), _legs, bias=1,
          # A leg already cooked is a leftover question, not a cooking time, and 'cooked chicken'
          # keeps "how do i know when chicken legs are cooked" - which is a timing question.
          avoid=("leftover", "left over", "leftovers", "already cooked", "next day",
                 "cold chicken", "what can i do with", "what can i make", "use up",
                 "soup", "stock", "sandwich", "salad",
                 # defrosting is a fridge question with its own entry, not a cooking time
                 "defrost", "thaw",
                 # a leg for a dog is a pet question; a thigh, breast or wing is a different
                 # piece with a different time; and "are they healthy" asks about the meat,
                 # not the oven
                 "dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "raw",
                 "thigh", "thighs", "breast", "breasts", "wing", "wings", "healthy",
                 "healthier", "curry", "casserole", "pie")),
    # "i forgot to take the chicken out the freezer" is the same question as "how do i defrost
    # it", said as the thing that just went wrong; forgetting is the tell, not "freezer", because
    # "how long can chicken stay in the freezer" is the storage answer.
    entry("chicken-defrost", ("chicken", ("defrost", "thaw", "frozen", "forgot", "forgotten",
                                          # "i keep forgetting to take the chicken out" is the
                                          # bird still in the freezer and wanting to be out of it:
                                          # the tense of the forgetting was not in the list, so
                                          # the line fell to a row about remembering to revise
                                          "forget", "forgetting", "forgot to take",
                                          "forget to take", "forgetting to take",
                                          "took it out", "take it out", "out of the freezer",
                                          "still in the freezer", "still frozen")),
          "Defrost chicken in the fridge overnight, on a plate on the bottom shelf, never on the "
          "worktop. Small pieces take a few hours, a whole bird a day or two; cook it as soon as it "
          "is thawed.",
          # "is frozen chicken ok after 2 years" is shelf life, not how to thaw it. A length of
          # time, or a phrase that asks whether it is still safe to eat, stands this down and
          # lets the storage answer take the line. The words for where the bird is do not:
          # "i forgot to take the chicken out of the freezer" is still a defrost question, and
          # "is it safe to defrost chicken on the counter" is still about thawing.
          avoid=("year", "years", "month", "months",
                 "still good", "still ok", "ok after", "use by", "out of date",
                 "safe to eat", "still safe", "safe after", "is it safe after",
                 "how long can chicken", "how long can i keep", "how long can you keep",
                 "how long can i leave", "how long does chicken last",
                 "how long does chicken keep", "stay in the freezer",
                 "last in the freezer", "keep in the freezer", "leave in the freezer",
                 "in the freezer for")),
    # "how long can chicken stay in the freezer" and "...last in the freezer" were timed like a
    # roast: they matched the plan follow-up, which times the bird the conversation named. Staying,
    # lasting and freezing are how people ask shelf life, so this entry claims them.
    # "shelf life" and "cooked" are here as well as main's words: "shelf life of cooked chicken"
    # was reaching the roast timings, and so was "how long does cooked chicken last".
    entry("chicken-storage", ("chicken", ("fridge", "freezer", "freeze", "freezing", "frozen",
                                          "store", "keep", "stays", "stay", "lasts", "last",
                                          # "raw chicken storage" says the same thing with the
                                          # noun, and "storage" is not a form of "store"
                                          "storage", "storing", "stored",
                                          # "raw" is not a shelf-life word: it is how the safety
                                          # question is asked ("is it ok to eat raw chicken"), and
                                          # with it here this row beat chicken-pink on every one
                                          # of those lines. The fridge, the freezer and the
                                          # days are what this answer is about.
                                          "uncooked", "shelf life", "shelf-life",
                                          # "how long is cooked chicken good for" is shelf life,
                                          # said the way most people say it
                                          "good for",
                                          # "how long till chicken goes off" is the same shelf
                                          # life asked the other way round, and without these
                                          # the oven time answered it ("20 minutes per 500g plus
                                          # 20") - the one thing a person asking when to bin it
                                          # must not be told.
                                          "go off", "goes off", "going off", "gone off")),
          "Raw chicken keeps 1 to 2 days in the fridge, on the bottom shelf, and cooked chicken "
          "3 days; both freeze well for up to 3 months. Go by the use-by date on the pack, which "
          "beats any general rule.",
          # how to keep a breast moist is a cooking question, not a shelf-life one: "keep" is the
          # ask here, and the raw-chicken storage line was answering it
          avoid=PET_LINE_WORDS + ("moist", "moisture", "juicy", "tender",
                                  # "chicken" is the bird and it is also the nerve: "i want to
                                  # ask out my crush but i keep chickening out" matched this row
                                  # on "chicken" plus "keep" and was told how long raw chicken
                                  # lasts in the fridge. The phrase is a fear, not a shelf life,
                                  # so the row stands down for it and the asking-out row answers.
                                  "chicken out", "chickening out", "chickened out", "cold feet",
                                  "ask her out", "ask him out", "ask them out", "ask out",
                                  "ask someone out", "asking her out", "asking him out",
                                  # "is chicken good for you" is the diet verdict, and this row
                                  # keys "good for" (for "how long is cooked chicken good for"),
                                  # so it answered a question about the diet with a shelf life.
                                  # The verdict is `chicken-healthy` in nutrition.py, and the
                                  # words below are how that question is asked.
                                  "good for you", "good for me", "good for us", "bad for you",
                                  "bad for me", "healthy", "unhealthy", "healthier",
                                  "fattening", "nutritious", "health benefits", "protein",
                                  # "can i cook chicken from frozen" is a method question and
                                  # `chicken-defrost` answers it, but this row keys `frozen` too
                                  # and scored one higher, so the line got "raw chicken keeps 1 to
                                  # 2 days in the fridge". A line that cooks the bird from frozen
                                  # is not asking how long it keeps, and one that asks whether a
                                  # frozen bird is still good says none of these phrases.
                                  # "i have chicken in the fridge what can i cook" is a meal
                                  # ask, not a keeping one: the fridge is where the chicken is,
                                  # and the answer it wants is what to do with it
                                  "what can i cook", "what can i make", "what do i make",
                                  "dinner idea", "dinner ideas", "meal idea", "meal ideas",
                                  "recipes for",
                                  "from frozen", "straight from frozen", "still frozen",
                                  "cook frozen", "cooking frozen", "cook it frozen",
                                  "cook from frozen", "cooking from frozen",
                                  "cooked from frozen",
                                  "roast from frozen", "roast it from frozen",
                                  "fry from frozen", "fry frozen",
                                  "without defrosting", "without thawing",
                                  "no need to defrost", "no need to thaw",
                                  "defrost it first", "not defrosted",
                                  # "can i cook a whole frozen chicken" says the method in
                                  # other words, with "a whole" between the verb and the bird
                                  "whole frozen", "frozen whole", "frozen bird",
                                  "frozen chicken in the", "frozen chicken on the",
                                  # the pot is not a shelf life: "can i freeze chicken stock"
                                  # and "how long can i keep chicken bones" are the stock row
                                  "stock", "stocks", "broth", "carcass", "carcasses",
                                  "bone", "bones", "stockpot",
                                  # "how long till it goes off" is a length of time, and "has it
                                  # gone off" is the yes-or-no test with signs to look for. This
                                  # row answers the first; `still-chicken` in still_ok.py answers
                                  # the second ("a sour or ammonia smell, a tacky or slimy feel")
                                  # and carried it until the present tense of "go off" joined this
                                  # row's key and outscored it on "has my chicken gone off".
                                  "has it gone off", "has my chicken gone off",
                                  "has the chicken gone off", "has this gone off", "has it gone",
                                  "is it off", "is my chicken off", "is the chicken off",
                                  "is this off", "how do i know", "how can i tell",
                                  "how do you tell", "know if", "tell if", "still ok", "still good",
                                  "ok to eat", "okay to eat", "safe to eat", "still safe",
                                  "smell", "smells", "smelly", "slimy", "sour", "funny smell"),
          # "should i keep chicken" was a first-date invitation: `friends.ask-someone-out` reads
          # "chicken out" a word at a time and its want words now hold "keep", so a bird and a
          # keeping word reached it. A bird and a keeping word is this card's question.
          bias=1),
    # Turkey and duck are the same rule as chicken, and "my turkey came out pink" was going to
    # the laundry card with the chicken lines until the birds were named here too.
    # "is that bad", the line people write a turn after this card, is read against the entry the
    # chat is on (`_leans_on`): the answer has to be about one of the words the line uses, and
    # "bad" is the whole of it. The freshness rows kept their follow-ups because "fish is bad" is
    # in their keys; this card said nothing about bad anywhere, so the follow-up reached it and
    # was then turned down, and the composer's "get it looked at" line took a cooking turn. The
    # word sits in the first sentence so the sentence the follow-up gets is the one that answers
    # it - the verdict and the action together.
    # "in the middle" is where the pink is and how the line says it: the follow-up reads the
    # entry it is on by the last word of the topic ("chicken pink middle"), so the row has to
    # know the word the topic ends on or it is not about the chat it is answering.
    entry("chicken-pink", (("chicken", "turkey", "duck", "goose"),
                            ("pink", "raw", "undercooked", "bloody", "middle", "in the middle",
                             # a grey, translucent middle is the same fault said without the
                             # word pink: "my chicken is grey inside" and "why is my chicken
                             # grey" were a shrug and the search hedge
                             "grey", "gray", "greyish", "grey inside", "gray inside")),
          "Pink chicken in the middle means it is undercooked, so don't eat it. That is a bad "
          "sign rather than a taste thing: put it back in the pan or oven until the juices run "
          "clear and the thickest part reaches 74C, and a little pink near the bone in a roast is "
          "still fine. A grey, translucent middle is the same thing said another way: it has not "
          "come up to temperature yet, so give it another few minutes rather than looking at the "
          "colour of the outside.",
          # "raw chicken storage" is the storage card's line: the word "raw" left the key of the
          # keeping rows when this row took it, so the keeping words are fenced back out here
          avoid=PET_LINE_WORDS + ("storage", "store", "stores", "storing", "stored", "fridge",
                                  "freezer", "freeze", "frozen", "how long", "use by",
                                  "left out", "leftover", "leftovers", "keep", "keeps", "kept"),
          bias=1),
    # "is it ok to eat raw pork" was a shrug on main: the chicken has its pink row and the red
    # meat had none, though the rule is different in one place - a whole cut can be pink, mince
    # cannot. One whole cut of red meat is one fact: a chop, a loin, a shoulder or a steak can be
    # a little pink in the middle and still be safe, and it is the minced and the stuffed that
    # has to be grey all the way through.
    entry("pork-pink", (("pork", "pork chop", "pork chops", "pork loin", "pork belly",
                         "pork shoulder", "pork steak", "gammon", "beef", "steak", "steaks",
                         "lamb", "lamb chop", "lamb chops", "veal", "red meat",
                         # "is it ok to eat pink meat" names no animal, and the policy card
                         # stands down for "pink" as well, so the bare word had no answer at all
                         "meat", "pink meat", "raw meat",
                         # The other half of the same rule is the minced meat that cannot be
                         # pink, and "is it ok to eat pink burgers" was a shrug on main: the
                         # reply already says burgers, mince and sausages have to be grey all
                         # through to 71C, so the words people use for them belong in the key.
                         "burger", "burgers", "mince", "minced", "minced meat", "sausage",
                         "sausages", "meatball", "meatballs", "kofta", "kofte", "nugget",
                         "nuggets", "kebab", "kebabs", "patty", "patties"),
                        ("pink", "raw", "undercooked", "bloody", "safe", "safely", "ok to eat",
                         # grey through a burger or a sausage is the fault this card warns
                         # about; a grey surface on a steak is the pan, which is another card
                         "grey inside", "gray inside", "grey in the middle",
                         "gray in the middle", "grey through", "gray through",
                         "grey all through",
                         "okay to eat", "fine to eat", "eat it", "still ok", "rare",
                         # the same reading as the chicken's: the pink is "in the middle"
                         "middle", "in the middle")),
          "A whole cut of red meat - a chop, a loin, a shoulder or a steak, whether pork, lamb or "
          "beef - can be a little pink in the middle and still be safe if it reaches 63C and "
          "rests for a few minutes, but mince, sausages and burgers have to be grey all the way "
          "through to 71C. A mouthful of raw pork or lamb by accident is very unlikely to do you "
          # "is that bad" is read against this card, and the sentence with "bad" in it is the one
          # the follow-up gets, so the verdict and what to do about it sit in the same sentence.
          "harm, but a serving of it is a bad idea: salmonella, E. coli and, rarely, roundworm. "
          "Cook it through, and see a doctor if you get cramps, fever or diarrhoea in the next "
          "few days.",
          avoid=PET_LINE_WORDS + (
                                  # the policy question is the red-meat row's, not this one
                                  "how much", "how many", "a day", "a week", "diet", "cancer",
                                  "bowel", "cholesterol", "processed", "portion", "portions",
                                  "healthy", "good for you", "bad for you", "should i eat",
                                  # a tuna steak is a fish steak: "is tuna steak ok rare" is the
                                  # searing card and the red-meat rule is not about fish
                                  "fish", "tuna", "salmon", "cod", "haddock", "prawns",
                                  "sashimi", "ceviche", "crackling", "roast", "how long", "oven",
                                  "temperature",
                                  "thermometer", "recipe", "marinade", "freeze", "frozen",
                                  "how do i", "cook", "cooking", "grill", "fry", "frying",
                                  "sear", "bake", "barbecue", "bbq", "sunday roast",
                                  "well done", "medium rare", "how to"),
          bias=1),
    # The other half of the red-meat rule, split out because it is the other subject and the
    # first sentence is what a person reads: a whole cut can be pink, mince cannot, and
    # "can i eat raw mince" was getting the whole-cut sentence, which reads as permission.
    # "can i eat burger medium rare" was a shrug: "medium rare" sat in the whole-cut row's avoid.
    entry("mince-pink", (("mince", "minced", "minced meat", "mincemeat", "burger", "burgers",
                          "sausage", "sausages", "sausagemeat", "meatball", "meatballs",
                          "kofta", "kofte", "kebab", "kebabs", "patty", "patties", "nugget",
                          "nuggets", "raw mince", "raw burger", "rare burger", "hamburger"),
                         ("pink", "raw", "undercooked", "bloody", "safe", "safely", "ok to eat",
                          "okay to eat", "fine to eat", "eat it", "still ok", "rare", "medium",
                          "medium rare", "well done", "in the middle", "middle", "should i eat")),
          "Mince, sausages and burgers have to be cooked grey all the way through to 71C, and a "
          "whole steak does not: mincing mixes the bacteria from the outside through the meat, so "
          "a rare burger is a real risk in a way a rare steak is not. Out, order it well done; at "
          "home, no pink in the middle and the juices run clear. A mouthful of raw mince is very "
          "unlikely to do any harm, but a serving of it is a bad idea - cook it through, and see a "
          "doctor if you get cramps, fever or diarrhoea in the next few days.",
          # how to cook one is the cooking card's, and the keeping question is the storage one's
          avoid=PET_LINE_WORDS + ("how do i cook", "how to cook", "how long", "recipe",
                                  "recipes", "how do i make", "sauce", "gravy", "bolognese",
                                  "lasagne", "lasagna", "chilli", "stew", "casserole", "pie",
                                  "oven", "grill", "barbecue", "bbq", "fry", "frying", "bake",
                                  "temperature", "thermometer", "meat free", "vegetarian",
                                  "vegan", "quorn", "soya", "plant based", "i made", "leftover",
                                  "leftovers", "fridge", "freezer", "freeze", "frozen", "keep",
                                  "keeps", "kept", "store", "stores", "storing", "stored",
                                  "storage", "use by", "how much", "a week", "a day",
                                  "diet", "processed", "cancer", "protein", "calories",
                                  # a pregnant person asking has a card written for her, and
                                  # "a mouthful of raw mince is very unlikely to do any harm"
                                  # is the wrong reassurance on the toxoplasmosis answer: the
                                  # same fence the pet words use, for the same reason
                                  "pregnant", "pregnancy", "expecting", "breastfeeding",
                                  "breast feeding", "conceive", "conceiving", "trimester"),
          bias=2),
    # "is it ok to eat raw fish" was the omega-3 portions card and "can i eat raw salmon" and
    # "is raw tuna safe" were a shrug: the freshness row stands down for "raw" because a spoilage
    # test reads as permission, and nothing answered the cooking question underneath. Fish is the
    # one food where the answer is a rule rather than a temperature: it is the parasites, and
    # freezing kills them.
    entry("fish-raw", (("fish", "salmon", "tuna", "cod", "haddock", "mackerel", "sea bass",
                        "trout", "sardines", "sashimi", "anchovies", "yellowtail", "halibut",
                        "raw fish", "raw salmon", "raw tuna"),
                       ("raw", "undercooked", "pink", "rare", "sashimi", "ceviche", "safe",
                        "safely", "ok to eat", "okay to eat", "fine to eat", "eat it",
                        "is it ok", "can i eat", "middle", "in the middle")),
          "Raw fish is safe to eat if it has been frozen first - 24 hours at -20C kills the "
          "parasites, and that is what sushi-grade fish has had - so a fresh fillet from a "
          "fishmonger eaten the day you buy it is fine for most people, and a supermarket fillet "
          "is not meant for it. Skip raw fish altogether if you are pregnant or your immune "
          "system is weak, and never eat freshwater fish raw.",
          avoid=PET_LINE_WORDS + ("tank", "fish tank", "aquarium", "goldfish", "pond", "ponds",
                                  "fish bowl", "pet fish", "kitten", "cat", "dog", "hamster",
                                  # "fishing" is not here: avoid matches by stem, and it
                                  # matches the word "fish" in every line this row answers
                                  "fish for", "rod licence", "angling",
                                  "smoked", "cured", "kipper", "fish fingers", "fish and chips",
                                  "pregnant", "pregnancy", "omega", "portions", "how long",
                                  "oven", "grill", "fry", "frying", "bake", "baking", "recipe",
                                  "temperature", "thermometer", "how do i cook", "cook it",
                                  "cooking", "poach", "steam", "season", "buy", "price",
                                  "is it off", "gone off", "still ok", "smell", "fridge",
                                  # "how often can i eat tuna" is a portions question, and the
                                  # oily-fish row answers it ("two portions a week"); this row is
                                  # about eating it raw.
                                  "how often", "how many times", "every day", "everyday",
                                  "twice a week", "a week", "per week", "a day"),
          bias=1),
    # A fish in the pan is not a live fish. "my fish is falling apart", "my fish breaks up in the
    # pan" and "my fish is falling to bits" were all the tank card ("A new fish needs the tank
    # ready before it goes in"), because a fish and a word like "my" is most of that row's key;
    # "how do i stop fish falling apart" was the rod licence, off the verb "fish"; and "why does my
    # fish fall apart when i fry it" was a lesson on gravity, off "fall". Nothing on the list was
    # about a pet: a live fish does not fall apart, the flesh of a cooked one does.
    # One complaint, a different fix per food: see `_falls_apart`. The fish part of it is the
    # row that fish needed, but the words are the rule, so meatballs, tofu and a stew get their
    # own answer from the same entry.
    entry("fix-falls-apart", (COMING_APART,
                              _FOOD + ("meatballs", "meatball", "kofta", "koftas", "tofu",
                                       "paneer", "halloumi", "tempeh", "rissoles", "fish pie",
                                       "fishcakes", "fishcake", "salmon", "cod", "haddock",
                                       "toad in the hole", "sausage meat", "potatoes", "mash",
                                       "dumplings", "falafel", "stew", "casserole")),
          _falls_apart, bias=1,
          avoid=PET_LINE_WORDS + ("tank", "fish tank", "aquarium", "goldfish", "pond", "ponds",
                                  "koi", "guppy", "guppies", "betta", "bowl", "pet fish",
                                  "filter", "whitespot", "white spots", "sick", "ill",
                                  # "fishing" is not here: avoid matches by stem, and it would
                                  # match the word "fish" in every line this row answers
                                  "fish for", "rod licence", "angling",
                                  "smoked", "cured", "kipper", "fish fingers", "fish and chips",
                                  "raw", "sashimi", "pregnant", "pregnancy",
                                  # a marriage, a plan and a wall fall apart too, and the food
                                  # gate is what keeps them out; these are the lines where the
                                  # food word is a metaphor
                                  "my plan", "my plans", "family", "relationship", "marriage",
                                  "friendship", "my car", "my van", "my bike", "sofa", "boots",
                                  "shoes", "wall", "walls", "shed", "fence", "roof", "teeth",
                                  "hair"),
          ),
    entry("roast-shopping",
          # A named roast or bird, plus a real buying shape. "need" alone used to be enough, which
          # made every timing line about a roast ("my roast potatoes need longer", "the roast needs
          # another 20 minutes") a request for a shopping list.
          (("roast", "roast dinner", "sunday roast", "christmas dinner", "xmas dinner",
            "turkey dinner", "chicken dinner", "roast lamb", "roast beef", "roast pork",
            "roast chicken", "roast turkey", "nut roast", "turkey"),
           ("buy", "buying", "shop", "shopping", "shopping list", "pick up", "pick some up",
            "need to buy", "need to get", "to get in", "get in", "buy for", "shop for")),
          _roast_shopping, bias=1,
          avoid=("wine", "how long", "leftover", "left over", "freeze", "frozen", "fridge",
                 "tin", "tray", "pan", "dish", "sauce", "gravy granules", "vegan", "veggie",
                 "vegetarian", "no meat", MEATLESS_ROAST, "allergy", "allergic",
                 # timing and state, never shopping
                 "minutes", "longer", "another", "resting", "rest", "done", "gas mark",
                 "temperature", "oven",
                 # when to buy is a lead-time question, not a quantity: "how many days before
                 # christmas should i buy the turkey" got the amount and not the day
                 "days", "weeks", "when", "before", "early", "advance", "order",
                 # the trimmings and sides are bought by name, and the line says so: "i need to
                 # buy potatoes for the roast" names potatoes, so the meat amount is the wrong
                 # answer to it even though a roast is in the line
                 "potato", "potatoes", "carrot", "carrots", "parsnip", "parsnips", "sprout",
                 "sprouts", "cabbage", "broccoli", "peas", "cauliflower", "swede", "turnip",
                 "stuffing", "sausagemeat", "pigs in blankets", "yorkshire", "batter",
                 "bread sauce", "cranberry", "pudding", "gravy", "horseradish", "mint sauce",
                 "apple sauce", "onion", "onions")),
    entry("steak", (("steak", "beef"), ("cook", "medium", "rare", "juicy", "pan", "how long",
                                        "minute")),
          "Get a heavy pan properly hot, pat the steak dry, salt it and sear it 2 to 3 minutes a "
          "side for medium rare, turning once. Rest it 5 minutes under foil before cutting, which "
          "matters as much as the cooking.",
          # A gammon steak is cured pork and it is cooked through, so the beef timetable is both
          # the wrong time and the wrong advice for it: "how long to cook a gammon steak" and the
          # follow-up "should i boil it first" both came here for a medium-rare beef steak.
          avoid=("freezer", "frozen", "freeze", "fridge", "keep", "keeps", "last", "stay", "thaw",
                 "defrost", "gammon", "gammon steak", "gammon steaks")),
    # "what temperature for a roast joint of beef" was a shrug: the steak entry wants "steak"
    # and the chicken entry is the bird. A joint is its own timetable, and the internal
    # temperatures are the honest half of the answer.
    entry("roast-joint", (("roast joint", "joint of beef", "beef joint", "roast beef",
                           "joint of lamb", "leg of lamb", "roast lamb", "shoulder of lamb",
                           "joint of pork", "leg of pork", "roast pork", "pork joint"),
                          ("temperature", "how long", "time", "oven", "cook", "roast",
                           "hot", "fan", "minutes", "done",
                           # the same ask with the everyday verb: "im doing a beef joint"
                           # and "im making a leg of lamb" were both a shrug, while
                           # "im cooking a beef joint" answered. Doing and making are
                           # what people say for the cooking they have planned.
                           "doing", "making")),
          _roast_joint,
          # the fast timetable is not a slow roast, and a joint is not what to serve with it
          avoid=("slow", "slowly", "low and slow", "overnight", "pulled", "serve", "serving",
                 "serves", "side", "sides", "goes with", "what with", "accompany",
                 # a joint is not a curry: with "making" read as cooking, "im making a leg of
                 # lamb curry" would be handed the roasting timetable
                 "curry", "curries",
                 # and a joint for a buffet is the party-food question, which answers it
                 "buffet", "buffets", "party",
                 # how long to rest the joint is rest-meat's question
                 "rest", "resting", "rested")),
    # "how long should i rest it" was answered with the gym rest between sets and "why do you rest
    # meat" with an honest shrug, and the roast rows gave the roasting time to a line about the
    # rest. Resting is its own question, and one answer covers every joint.
    entry("rest-meat", (("rest", "resting", "rested"),
                        ("meat", "steak", "roast", "joint", "chicken", "turkey", "lamb", "beef",
                         "pork", "gammon", "brisket", "ribs", "rack", "shoulder", "bird",
                         "chops", "roasted", "carve", "carving")),
          _rest_the_meat,
          avoid=("shortcrust", "pastry", "bread", "dough", "rise", "rises", "rising",
                 "proving", "proof", "sourdough", "cake",
                 # the gym and the bedside are not the carving board
                 "gym", "sets", "set", "rep", "reps", "run", "running", "jog", "walk", "walking",
                 "exercise", "training", "workout", "muscle", "muscles", "injury", "sore",
                 "sleep", "bed", "nap", "tired", "ill", "sick", "cold", "flu", "days", "week"),
          bias=1),
    # A mince dish that went grainy is its own fault: the pan was not hot enough and the mince
    # boiled in its own juice. Keyed on the dish and the fault, so a grainy fudge stays the sugar
    # row's and a grainy sauce reaches the mince.
    entry("mince-grainy", (_MINCE_GRAIN_DISH, _MINCE_GRAIN_WORD),
          _mince_grainy,
          avoid=("chocolate", "fudge", "toffee", "caramel", "icing", "custard", "cake", "sugar",
                 "freeze", "freezer", "fridge", "leftover", "leftovers", "reheat")),
    entry("mince", (("mince", "minced beef", "ground beef"),
                     ("brown", "cook", "bolognese", "sauce", "grey", "tough", "rubbery", "dry")),
          _mince),
    entry("sausages", (("sausages", "sausage", "chipolata", "chipolatas", "bangers"),
                       ("cook", "oven", "pan", "juicy", "how long", "grill", "fry", "frying")),
          "Roast sausages at 200C (180C fan) for 25 to 30 minutes, turning once, or fry them on a "
          "medium heat for about 15. Pricking them lets the juice out, so don't."),
    entry("bacon", ("bacon", ("crispy", "cook", "oven", "how long")),
          "Lay bacon rashers on a rack over a tray and bake at 200C (180C fan) for 15 to 18 "
          "minutes: crisp, flat and no splashing. In a pan, start it in a cold pan on a medium heat "
          "so it renders before it burns."),
    entry("salmon", ("salmon", ("cook", "oven", "bake", "time", "how long")),
          "Bake salmon fillets at 200C (180C fan) for 12 to 15 minutes, until the flesh just "
          "flakes. In a hot pan, 4 minutes skin side down and 1 minute the other way is enough; "
          "salmon dries out fast when it's overcooked.",

          # "how long does cooked salmon last" is a keeping question, and the fillets' bake time
          # is the wrong clock for it.
          avoid=("last", "lasts", "keep", "keeps", "keeping", "store", "stored", "shelf life",
                 "fridge", "freezer", "gone off", "out of date", "tomorrow", "next day",
                 # poaching is the one method where the number is different and the water matters,
                 # and "how long to poach salmon" was getting 200C for 12 to 15 minutes: the oven
                 # answer tells you to do the opposite of what a poach wants.
                 "poach", "poached", "poaching", "poached salmon", "steam", "steamed")),
    entry("mushroom-wash",
          (("mushroom", "mushrooms", "button mushrooms", "chestnut mushrooms", "portobello",
            "field mushrooms", "shiitake"),
           ("wash", "washing", "washed", "rinse", "rinsing", "clean", "cleaning", "clean them",
            "dirt", "grit", "peel", "peeled", "before cooking", "before you cook")),
          # whether to peel is a different question from whether to wash, and "do i need to
          # peel mushrooms" was getting the rinse card, which never says what to do about the
          # skin: one entry, two answers, branched on the line.
          lambda memory, understood: _mushroom_wash(understood),
          # a keeping, freezing or growing question names mushrooms too, and none of them is
          # about cleaning them
          avoid=("freeze", "freezing", "frozen", "keep", "keeping", "store", "storing",
                 "fridge", "last", "lasts", "slimy", "gone off", "raw", "pick", "picked",
                 "forage", "dried", "dry", "soup", "sauce", "risotto", "stuffed", "grow",
                 "growing", "garden", "poisonous"),
          # vegetables.py answers mushrooms with its own roasting-and-frying row and carries a
          # bias of 2, so "how should i clean mushrooms before cooking" landed there on the
          # word "cooking" alone. Cleaning them is this entry's question wherever the cooking
          # word sits in the line. The bias lifts this entry over that one, and the `ask` list
          # keeps it off every line that only names a mushroom: "i bought mushrooms" names no
          # cleaning word, so it is not this entry's question.
          ask=("wash", "washing", "washed", "rinse", "rinsing", "clean", "cleaning", "dirt",
               "grit", "peel", "peeled", "before cooking"),
          bias=3),
    entry("salmon-poach",
          (("salmon", "fish", "haddock", "cod", "trout"),
           ("poach", "poached", "poaching", "poached salmon", "poach in milk", "water bath")),
          lambda memory, understood: _poach_fish(understood),
          # the poaching water is what this answers, so a line about a sauce or a salad that
          # happens to name salmon is not it
          avoid=("bake", "baked", "baking", "roast", "roasted", "fry", "fried", "grill",
                 "grilled", "smoked", "raw", "sushi", "freeze", "frozen", "thaw", "keep",
                 "fridge", "salad", "sandwich", "teriyaki")),

    # --- how do you know it is done? ---------------------------------------
    # One entry per meat, because the numbers are the answer: "what temperature should i cook
    # pork at", "what temperature is pork done" and "how long do i roast a leg of lamb" are the
    # same question, and the meat in the line is what picks the row, not the shape of the ask.
    # Chicken has its own entry above (75C) and a steak is a pan method, so steak keeps that line.
    # --- a cold dip that is not the texture you wanted ----------------------
    # "my houmous is too thick" and "my tzatziki is watery" were shrugs, and they are not the hot
    # sauces the watery entry fixes: a cold dip is put right cold, out of the fridge. The fix is
    # chosen from the dip the line names, because houmous and guacamole do not want the same words.
    entry("dip-fault",
          (("houmous", "hummus", "humous", "tzatziki", "raita", "aioli", "mayonnaise", "mayo",
            "guacamole", "salsa", "baba ganoush", "tapenade", "dip", "dips", "garlic sauce",
            "yogurt dip", "yoghurt dip"),
           ("too thick", "too thin", "watery", "runny", "too dry", "split", "curdled",
            "gone brown", "went brown", "turned brown", "lumpy", "seized", "ruined",
            "went wrong", "fix")),
          lambda memory, understood: _dip_fault(understood),
          avoid=("simmer", "reheat", "chicken", "bolognese", "curry", "stew", "soup"),
          bias=1),
    # "can i eat prawns from frozen" was the defrost card, "can i eat raw prawns" was a shrug
    # and "are prawns already cooked" was the pan-time card: a prawn is the one seafood where the
    # pack decides the answer, because most of them are sold already cooked and the rest have to
    # turn pink all the way through. None of the fish rows can say that, and the defrost card
    # answers the wrong question - a frozen cooked prawn is eaten once thawed, not cooked.
    entry("prawns-doneness", (("prawn", "prawns", "king prawns", "king prawn", "shrimp",
                               "shrimps", "tiger prawns", "prawn cocktail", "langoustine",
                               "langoustines"),
                              ("raw", "uncooked", "cooked", "ready", "already cooked",
                               "from frozen", "frozen", "cold", "safe", "safely", "ok to eat",
                               "okay to eat", "fine to eat", "eat it", "eat them", "thawed",
                               "defrosted", "need to cook", "have to cook", "should i cook",
                               "do i need to cook", "pink", "grey", "grey inside", "sushi",
                               # "pregnancy" is here because "prawns and pregnancy" names the
                               # subject and nothing else: without the word the row did not
                               # reach the line at all and it fell to a back-channel. The
                               # questions are stood down by the avoid below, not by this.
                               "pregnancy", "pregnant", "eat cold", "eat them cold",
                               "without cooking", "no cooking", "without defrosting")),
          "Check the pack first, because most prawns are sold already cooked: those only need "
          "thawing, and a cooked prawn is safe to eat cold once it has defrosted overnight in the "
          "fridge. Raw prawns are grey rather than pink, and those have to be cooked all the way "
          "through until they curl, turn pink and are opaque in the middle - 2 to 3 minutes in a "
          "hot pan or 1 to 2 minutes in boiling water, and you can put them in frozen with a "
          "minute or two extra. Thawed prawns keep a day, do not go back in the freezer, and in "
          "pregnancy eat only the thoroughly cooked ones. Bin any that smell of ammonia or feel "
          "slimy.",
          # the pan time, the defrosting, the keeping and the recipe are all other cards' lines,
          # and a prawn in a curry or a linguine is an ingredient rather than a question
          # The bare words "defrost" and "thaw" cannot be in an avoid list at all: lookup._forms
          # folds "defrosted" to "defrost" and "thawed" to "thaw", so naming them stood this row
          # down on the very lines it is for ("can i eat defrosted prawns" kept the fish card).
          # The instruction shapes stay, and so does the whole cook-how question rather than one
          # form of it: "how do i cook king prawns" was a regression against the pan-time card.
          avoid=("how long do prawns take", "how long to cook prawns", "how long does it take",
                 "how long do i cook", "how long should i cook", "how long do you cook",
                 "how long do king", "how long in the", "how many minutes",
                 "how do i defrost", "how to defrost", "recipe", "recipes",
                 "how do i cook", "how to cook", "best way", "method", "curry",
                 "stir fry", "stir-fry", "linguine", "pasta", "risotto", "paella", "noodle",
                 "noodles", "reheat", "keep", "keeps", "leftover", "leftovers", "freeze",
                 "refreeze", "sauce", "garlic", "butter", "tempura", "batter", "barbecue",
                 "bbq", "air fryer", "oven", "grill", "price", "buy", "sustainable", "farm",
                 "prawn cracker", "prawn crackers", "prawn toast",
                 # A pregnancy question is the pregnancy card's: it says which shellfish is fine
                 # ("cooked prawns, mussels that have opened in the pan ... are all fine") and
                 # which to skip, and this row's one clause about it is thinner than that. The
                 # shapes below are how a pregnancy question is asked, not the bare topic word:
                 # "prawns and pregnancy" names the subject and keeps this row.
                 "when pregnant", "while pregnant", "if pregnant", "in pregnancy",
                 "during pregnancy", "weeks pregnant", "im pregnant", "i'm pregnant",
                 "pregnant and", "pregnancy and") + PET_LINE_WORDS,
          bias=6),
    entry("fish-defrost", (("fish", "salmon", "cod", "prawns"), ("defrost", "frozen", "thaw")),
          "Defrost fish in the fridge overnight, still wrapped, on a plate. If you're short of "
          "time, seal it in a bag and sit it in cold water for an hour, changing the water; never "
          "defrost it on the worktop. A prawn is quicker, and needs no night in the fridge: cold "
          "water for 10 to 15 minutes, or straight into a curry or stir-fry from frozen with two or "
          "three minutes extra."),

    # --- vegetables and sides ----------------------------------------------
    # Defrosting meat is the same answer whatever the cut, and main shrugs on all of it: "how do
    # i defrost a turkey", "how do i defrost mince", "how do i defrost sausages" all fell through
    # to "I don't know enough to answer that honestly". Chicken and fish have their own entries
    # above, so this one stays off those words.
    entry("meat-defrost", (("turkey", "mince", "sausages", "sausage", "beef", "pork", "lamb",
                            "chops", "steak", "gammon", "bacon", "joint", "liver", "kidneys",
                            # "meat" on its own is how most people say it: "is it safe to defrost
                            # meat on the worktop" named no cut and got a shrug. Chicken stays out,
                            # because chicken-defrost above answers for the bird.
                            "meat", "red meat",
                            # "can i just cook it from frozen" names no cut at all, and the cut is
                            # often in the turn before ("i forgot to defrost the mince"). The
                            # freezer words are the whole question, so they are a key part here and
                            # the reply says which cuts are safe and which are not.
                            "from frozen", "cook it frozen", "cooked from frozen",
                            "without defrosting", "without thawing", "no need to defrost",
                            "have to defrost", "need to defrost"),
                           ("defrost", "defrosting", "defrosted", "thaw", "thawing", "thawed",
                            "frozen")),
          _meat_defrost, bias=2,
          ask=("defrost", "defrosting", "defrosted", "thaw", "thawing", "thawed", "frozen"),
          # keeping, freezing and reheating are other answers: "how long can mince stay in the
          # freezer" is storage, not thawing
          avoid=("freezer", "freeze", "refreeze", "re-freeze", "keep in the fridge",
                 "leftover", "leftovers", "reheat", "use by", "gone off", "off smell",
                 # chicken and fish answer for themselves above, and "can i cook chicken from
                 # frozen" is the chicken entry's line, not this one's
                 "chicken", "prawn", "prawns", "fish", "salmon", "cod",
                 # "from frozen" is in the key above, so "can i cook frozen pizza from frozen"
                 # matched this entry twice and got the mince answer. The frozen things that are
                 # not meat have answers of their own, so they are named here.
                 "pizza", "chips", "chip", "fries", "wedges", "waffles", "nuggets",
                 "fish fingers", "peas", "sweetcorn", "veg", "vegetables", "broccoli",
                 "spinach", "berries", "fruit", "pastry", "rice", "bread", "pie",
                 "potato", "potatoes", "dumplings", "samosa", "spring rolls", "yorkshire",
                 "cake", "pancake", "pancakes", "croissant", "dough")),
    entry("roast-potatoes", (("potato", "potatoes"),
                             # "crisp" and "crispy" were the make-crisps row's, so "how do i get a
                             # crisp roast potato" was told to slice them 2mm thin and fry them,
                             # and "roast potatoes fluffy inside" was a how-to-keep-cool card
                             ("roast", "crispy", "crisp", "crunchy", "crunchiest", "soggy",
                              "oven", "fluffy", "burn", "burnt", "burning", "black",
                              "blackened", "caught", "too hot", "stuck", "edges")),
          _roast_potatoes,
          # A roast or an oven has to be in the line: "the potatoes boiled dry and burnt" is a pot
          # on the hob, and this row's burn answer is about a tray.
          ask=("roast", "roasts", "roasting", "roasted", "roastie", "roasties", "oven",
               "in the tin", "in the tray"),
          bias=3, guard=_not_the_joint_timing,
          # "oven" in the key is what catches "how long do potatoes take in the oven", and it is
          # also in "how do i cook sweet potato in the oven": a sweet potato is a different
          # vegetable with a different answer, so it passes instead of getting this one.
          # a keeping or reheating question ("how long do roast potatoes keep") is the dish
          # plan's answer, not this method's.
          avoid=("sweet", "sweet potato", "sweet potatoes", "yam", "yams",
                 # one potato in its skin is not a tray: "how do i make a jacket potato crispy"
                 # and "how do i get crispy skin on a baked potato" want an hour at 200C, not 40
                 # minutes of parboiled chunks.
                 # a joint named in the line used to be listed here, as bare nouns, and it
                 # took "roast potatoes in beef dripping" and "roast potatoes with the lamb" out
                 # of this row: `_not_the_joint_timing` above is the guard now, and it stands
                 # down only when the joint's own cooking time is what is being asked.
                 # an air fryer is its own method and its own answer: "how do i make roast
                 # potatoes in the air fryer" is the basket, not a 200C oven tray.
                 "air fryer", "air fryers", "airfryer", "air-fryer", "air fried", "airfry",
                 "jacket", "jacket potato", "jacket potatoes", "baked potato", "baked potatoes",
                 "baking potato", "potato skin", "potato skins", "skin on",
                 "keep", "keeps", "keeping", "last", "lasts", "stale", "freeze", "fridge",
                 "freezer", "reheat", "leftover", "leftovers",
                 # "roast" in the key is what makes "how long do roast potatoes take" this
                 # method, and it also made every nutrition line about roast potatoes this
                 # method: "are roast potatoes fattening", "...bad for you", "...healthy" and
                 # "how many calories in roast potatoes" were the potato nutrition card and
                 # became "parboil them for 8 minutes". Whether a tray is fattening is not a
                 # roasting question, so those words stand this row down.
                 "fattening", "fatten", "calories", "calorie", "how many calories", "healthy",
                 "healthier", "unhealthy", "bad for you", "good for you", "slimming", "diet",
                 "weight loss", "waistline", "carbs", "keto", "nutrition", "nutritious",
                 # "what goes with roast potatoes" is the accompaniments question - main's
                 # what-goes-with card answers it with gravy - and this row answered it with
                 # the method, because "roast" and "potatoes" are the words of both.
                 "goes with", "go with", "went with", "serve with", "served with",
                 "to serve with", "accompaniment", "accompaniments", "side with",
                 "sides to go with")),
    entry("mash", (("mash", "mashed potato", "mashed potatoes"), ("lumpy", "smooth", "fluffy",
                                                                 "cream", "creamy", "make",
                                                                 "how do i mash", "how do you mash",
                                                                 "how to mash", "mash the potatoes",
                                                                 "mashing them with",
                                                                 "best", "butter", "milk",
                                                                 # "how long should i boil
                                                                 # potatoes for mash" is this
                                                                 # method's first step: with
                                                                 # "how long" only in
                                                                 # potato-boil, and potato-boil
                                                                 # naming mash in its avoid,
                                                                 # nothing answered it at all
                                                                 "how long", "boil", "boiling",
                                                                 "minutes", "time")),
          "Boil them in salted water: 15 to 20 minutes for chunks and 20 to 25 for whole medium "
          "potatoes, until a knife slides in with no resistance. Floury potatoes mash best, so "
          "steam them dry for a minute, then mash with warm milk and butter and stop as soon as "
          "it's smooth: over-beating turns it gluey.",
          # "how long" used to be in the key, and it took every keeping question about mash
          # ("how long does mashed potato keep in the fridge") away from the keeping entries.
          # Nothing wanted is lost: every "how long does it take to make mash" line says "make".
          avoid=_MASH_NOT_THIS),
    # Milk and butter are in the method above, so a line that has to leave one of them out is not
    # that method: it is the question of what replaces them. Before this, `swap-butter` answered
    # "how do i make mash without butter" with a substitution for cakes and biscuits.
    entry("mash-dairy-free", (("mash", "mashed potato", "mashed potatoes"),
                              ("without butter", "no butter", "butter free", "without milk",
                               "no milk", "milk free", "dairy free", "dairy-free", "no dairy",
                               "without dairy", "instead of butter", "instead of milk", "vegan",
                               "olive oil", "plant based", "plant-based")),
          "Mash it with the water it cooked in and a fat that is not butter: two or three spoons "
          "of the cooking water and two tablespoons of olive oil, or the same of a dairy-free "
          "spread, plus a splash of warm oat or soy milk if you want it looser. Work it with a "
          "fork or a whisk for a minute rather than a masher - starch and liquid are what make it "
          "smooth - and taste for salt, because without butter it wants a little more. A spoon of "
          "mustard, horseradish or a soft garlic clove cooked with the potatoes puts back some of "
          "the flavour the butter was giving."),
    # The salted water and the milk in the method above are the two things a baby's mash cannot
    # have, so this is its own answer rather than the same one with a note on the end.
    entry("mash-for-baby", (("mash", "mashed potato", "mashed potatoes", "potato", "potatoes"),
                            ("baby", "babies", "for my baby", "for a baby", "weaning", "weaned",
                             "toddler", "6 months", "six months", "9 months", "first foods")),
          "Cook the potato on its own in unsalted water and mash it with a little of that water, "
          "some of their usual milk or a knob of unsalted butter, and no salt at all: babies under "
          "one should have none, and their kidneys cannot deal with it. Keep it smooth and a "
          "little looser than yours while they are learning to swallow, and add nothing else "
          "until you know they have had it before. Your health visitor is the one to ask about "
          "amounts and what to add next, because it depends on the baby's age."),
    entry("onion-cry", ("onion", ("cry", "crying", "tears", "eyes")),
          "Cutting an onion breaks its cells and releases a gas that irritates your eyes, so they "
          "make tears to wash it away. A sharp knife and a chilled onion release less of it, and "
          "the root end holds most of it, so cut that last.",
          # a person's eyes watering over an onion is the onion's answer, not the garden's and not
          # the dry-eye one: "my eyes water when i chop onions" was the tomato-watering card
          # because the rows keyed on water and eyes tie, and the onion row carried no weight
          bias=3,
          # an animal that ate an onion is the poisoning question, even when its eyes are watering
          avoid=("dog", "dogs", "puppy", "puppies", "cat", "cats", "kitten", "kittens", "pet",
                 "pets", "ate", "eaten", "eat", "eats", "eating", "poison", "poisoned",
                 "poisonous", "toxic")),
    # "is it safe to eat limp lettuce" was answered with the iced-water method: the fix for limp
    # leaves is not the answer to "can I still eat this", and slimy leaves cannot be rescued at
    # all. The verdict comes first here, and the question has its own key so the keeping and the
    # reviving answers keep their lines.
    entry("leaf-can-i-eat-it",
          (("limp", "wilted", "floppy", "soggy", "slimy", "gone over", "gone brown", "brown edges"),
           ("safe", "safely", "eat", "eating", "edible", "still ok", "still good", "ok to eat",
            "still fine", "throw away", "bin it", "use it")),
          "Limp leaves are fine to eat: wilting is only water loss, so they are safe once they have "
          "had 10 minutes in iced water. Slimy, sour-smelling or brown-and-soft leaves are not "
          "safe, and no rinse fixes them, so bin those.",
          # a pet, a person, a plant or a hair that is limp is not a bag of leaves
          avoid=LEAFY_AVOID + ("dog", "cat", "puppy", "kitten", "pet", "baby", "toddler", "child",
                               "hair", "feel", "tired", "plant", "garden", "ground",
                               # "how do I stop it going limp" is the keeping question, and the
                               # follow-up after a "can I eat it" turn carries the eat words too
                               "keep", "keeps", "keeping", "stop", "stops", "crisp", "crisper",
                               "fresh", "fresher", "last", "longer", "revive", "reviving")),
    # Drying a bunch is a job of its own, and it had no row at all: "how do i dry lavender"
    # and "how do i dry herbs" were a search hedge, and "how do i dry lavender for sleep"
    # the same. Only the drying words are in it, so keeping a bunch fresh (herbs-keep),
    # dried against fresh in a recipe (dried-herbs) and a herb that has gone yellow are
    # other answers.
    entry("dry-herbs", (("dry", "drying", "dehydrate", "dehydrating", "hang",
                         "hanging", "preserve", "preserving"),
                        # "bay" is not in this list on its own: it is the word in "bay window"
                        # as often as it is a leaf, so the herb is named as the leaf it is - the
                        # same rule as any other word that lives inside a compound ("how do i
                        # hang a curtain rail on a bay window" was a bunch of herbs)
                        ("herb", "herbs", "lavender", "rosemary", "thyme", "sage", "oregano",
                         "mint", "bay leaves", "bay leaf", "laurel", "parsley", "dill", "tarragon",
                         "chives", "marjoram", "lemon balm", "chamomile", "camomile", "basil")),
          ("Hang it in small bunches, upside down and spread out, somewhere warm, dark and dry "
           "with a bit of air moving - a shed, an airing cupboard or a room with the window open "
           "- and it is dry in one to two weeks. A low oven at 50C with the door ajar does the "
           "same in an hour or two. Strip the leaves or buds off the stems once they crumble, keep "
           "them in a sealed jar out of the light, and they hold their flavour for about a year. "
           "Lavender keeps its scent better in a paper bag than in a jar, and the buds go into a "
           "small cloth bag for a drawer or under a pillow."),
          # a herb that is going yellow, limp or mouldy is a keeping fault, a line about fresh
          # against dried is dried-herbs', and a bunch you bought to cook with is herbs-keep's
          avoid=("yellow", "yellowing", "wilt", "wilted", "wilting", "limp", "soggy", "dying",
                 # a plant whose leaves have dried is a plant that wants water or light, not a
                 # bunch to hang up: the leaves said first
                 "dry leaves", "dried leaves", "has dry", "have dry", "leaves are", "leaves look",
                 "leaves going", "leaves turning", "going crispy", "crispy",
                 "drooping", "droopy", "curling", "brown", "spots", "mouldy", "moldy", "mould",
                 "instead of", "substitute", "in place of", "fresh or dried", "dried or fresh",
                 "recipe", "cook with", "cooking with", "how much",
                 # a herb that is already dried is a keeping or a cooking question, and both
                 # have a row: "how do i store dried herbs" and "how long do dried herbs keep"
                 # belong to dried-herbs
                 "store", "storing", "storage", "keep", "keeps", "keeping", "how long", "last",
                 "lasts", "shelf life")),
    entry("dried-herbs", (("rosemary", "thyme", "oregano", "herbs"), ("dried", "fresh",
                                                                    "instead", "substitute")),
          "Dried herbs are fine in anything cooked: use about half the amount of fresh and add them "
          "earlier so they soften. Keep fresh for the end, and for salads and dressings where "
          "their green taste is the point.",
          # a keeping question is herbs-keep's: "how long do fresh herbs last" asked which herb
          # to use, and got a lecture on dried ones. "dried" stays out of that avoid, so a line
          # about keeping dried herbs still reaches this entry.
          avoid=("limp", "soggy", "wilt", "wilted", "stay fresh", "keep fresh", "rubbery")),
    entry("garlic-hands", ("garlic", ("smell", "hands", "stink", "smelly")),
          "Rub your hands on something stainless steel under cold running water, like the tap or a "
          "spoon, and the smell goes; salt, lemon juice or coffee grounds work too. The sulphur "
          "compounds bind to the metal instead of your skin.",
          # "my breath smells of garlic" is the breath row's question: the hands trick does
          # nothing for breath, which comes out of the lungs
          avoid=("breath", "bad breath", "garlic breath", "mouth", "breathe", "breathing")),
    entry("garlic-burn", (("garlic", "garlic clove", "garlic cloves"),
                          ("burn", "burns", "burnt", "burned", "burning", "bitter", "black",
                           "black bits", "went black", "gone black", "scorch", "scorched",
                           "too hot", "high heat", "caught")),
          "Garlic burns in seconds because it's full of sugar: crush or slice it and add it later "
          "than the onion, on a lower heat. If it's already bitter, start again; burnt garlic "
          "taints the whole dish.",
          # ...and a line about the smell of it is the breath row's, which the burn words above
          # would otherwise take: "does burnt garlic give you bad breath" is a breath question.
          avoid=("breath", "bad breath", "garlic breath", "mouth", "breathe", "breathing",
                 "still smell", "smells of")),
    # Garlic going green or blue is the one colour change in a kitchen that is not spoilage, and
    # it was reaching the storage answer, the planting answer and the laundry one instead - the
    # blue card even rang a 999 for "my garlic went blue when i pickled it" (fixed in safety.py).
    entry("garlic-green", (("garlic", "garlic clove", "garlic cloves", "pickle", "pickles",
                            "pickled", "chutney", "kimchi", "sauerkraut"),
                           ("green", "blue", "teal", "turquoise", "colour", "colours", "coloured",
                            "safe", "harmless", "gone off", "off")),
          ("That green or blue is harmless: the sulphur compounds in garlic and onions turn "
           "colour with acid, and with copper or unlined iron, and nothing else about the food "
           "changes, so eat it. It shows up in garlic dressed with lemon or vinegar, in pickle "
           "brines and in pickled onions. Blanching the cloves for 30 seconds before pickling, "
           "adding the acid at the end and using a stainless pan all stop it happening."),
          # keeping it, planting it and how long it lasts are other answers
          avoid=("store", "storing", "storage", "keep", "keeping", "plant", "planting", "grow",
                 "growing", "how long", "sprout", "sprouting", "sprouted", "skin", "peel",
                 "smell", "burn", "burnt"),
          bias=3),
    entry("roast-vegetables", (("vegetables", "veg"), ("roast", "oven", "time", "how long")),
          "Cut vegetables into similar-sized pieces, toss them with oil and salt and roast at 200C "
          "(180C fan) for 30 to 40 minutes, turning once. Give them space on the tray; a crowded "
          "tray steams instead of roasting.",
          # "how long do vegetables take to grow" is the garden's question: growing, sowing and
          # planting words mean the vegetables are in the ground, not on the tray.
          avoid=("take to grow", "to grow", "grow", "growing", "grows", "sow", "sowing",
                 "seed", "seeds", "harvest", "crop", "crops", "allotment", "raised bed",
                 "veg patch", "vegetable patch")),
    entry("broccoli", ("broccoli", ("cook", "boil", "steam", "steaming", "steamed", "how long",
                                    "time", "done", "tender", "know when", "soggy", "mushy",
                                    "green", "yellow", "yellowing", "gone yellow")),
          "Boil or steam broccoli for 4 to 5 minutes, until a knife goes in with a little bite "
          "left. Drain it and run it under cold water if you're not serving it straight away: that "
          "keeps it green instead of army-issue grey. Broccoli that has already gone yellow is "
          "either overdone or a few days old - it is still fine to eat, so give it 3 minutes next "
          "time and use this lot in a soup or a stir-fry rather than on the plate."),
    # The greens that are not broccoli: cabbage, red cabbage, kale and a boiled cauliflower were
    # all shrugs on their own cooking line, and a brassica going bitter or yellow was an ack.
    entry("kale", ("kale", ("cook", "boil", "steam", "steaming", "how long", "time", "done",
                            "tender", "prepare", "strip", "stalks", "bitter")),
          "Strip the leaves off the stalks - the stalks are the woody, bitter part - then boil or "
          "steam the leaves for 3 to 5 minutes, until they are soft but still bright. Curly kale "
          "takes the 5 and cavolo nero nearer 3. Massage it with oil and salt if it is going in a "
          "salad raw, which softens it in a couple of minutes without cooking it. A splash of "
          "lemon or vinegar at the end keeps the colour.",
          avoid=("keep", "keeping", "store", "last", "freeze", "grow", "growing", "plant", "slug",
                 "slugs", "crisps", "crisps", "chip", "chips", "crispy")),
    entry("cauliflower-boil", ("cauliflower",
                               ("boil", "boiled", "steam", "how long", "time", "tender", "white",
                                "grey", "soggy", "cook")),
          "Florets take 5 to 7 minutes in boiling salted water and a whole head 10 to 15, until a "
          "knife slides into the stalk with no crunch left. A tablespoon of milk or lemon in the "
          "water keeps it white rather than grey, and salt it properly or it tastes of nothing. "
          "Drain it well, because a cauliflower left sitting in its water goes soft and sulky.",
          avoid=("roast", "roasting", "roasted", "oven", "cheese", "bake", "baked", "rice",
                 "freeze", "keeping", "keep", "curry", "soup", "grow", "growing")),
    # Cabbage is the family nobody answered at all: the boil, the red sort, the bitterness and
    # "make it taste better" were four different shrugs.
    entry("cabbage-boil",
          (("cabbage", "white cabbage", "green cabbage", "savoy", "savoy cabbage", "hispi",
            "pointed cabbage", "spring greens", "greens"),
           ("boil", "boiled", "cook", "cooking", "steam", "steaming", "how long", "time", "done",
            "tender", "soft", "soggy", "prepare", "wedges", "shred")),
          "Cut it into wedges so the stalk cooks with the leaf, drop it into plenty of boiling "
          "salted water and leave the lid off: 5 to 8 minutes for a firm white or green cabbage, "
          "3 to 4 for savoy and spring greens, until a knife goes into the stalk with a little "
          "resistance left. Drain it at once and toss it with a knob of butter or a little oil - "
          "cabbage left standing in the pan carries on cooking and turns to water.",
          avoid=("red cabbage", "red cabbages", "bitter", "bitterness", "smell", "smelly",
                 "stink", "keep", "keeping", "store", "shop", "buy", "grow", "growing", "plant",
                 "slug", "slugs", "recipe", "leftover", "freeze", "pickle", "sauerkraut",
                 "coleslaw", "kimchi", "soup", "stuffed", "roll", "rolls", "meat")),
    entry("red-cabbage", (("red cabbage", "red cabbages"),
                          ("cook", "cooking", "braise", "braised", "how long", "time", "boil",
                           "vinegar", "apple", "sweet", "christmas", "prepare")),
          "Braise it rather than boil it: shred it, soften sliced onion in butter, add the cabbage "
          "with a chopped apple, two tablespoons of vinegar and a spoon of sugar, a splash of "
          "water, then put the lid on for 45 to 60 minutes on a low heat, stirring now and then. "
          "The vinegar is not for flavour alone - it is what keeps the colour a deep red instead "
          "of a grey-blue, so taste and add more at the end.",
          avoid=("bitter", "keep", "keeping", "store", "buy", "grow", "growing", "plant", "slug",
                 "slugs", "freeze", "pickle", "raw", "salad", "slaw", "coleslaw", "sauerkraut")),
    entry("cabbage-bitter",
          # "greens" stays out of the key: its loose form is "green", and a bare "green" made
          # "why are my potatoes green" a brassica answer instead of the solanine one
          (("cabbage", "red cabbage", "sprouts", "sprout", "spring greens", "kale", "cauliflower",
            "broccoli", "brassica", "brassicas"),
           ("bitter", "bitterness", "sulphur", "sulfurous", "why", "tastes", "taste", "smells",
            "smelly")),
          "The bitterness is the sulphur compounds in the leaves, and cooking makes it worse the "
          "longer it goes on: past about 8 minutes a brassica turns sweet-smelling and bitter at "
          "the same time. So cook it briefly in plenty of fast-boiling water, leave the lid off, "
          "and cut it into even pieces so the stalk is not still raw when the leaf is done. If it "
          "has already gone bitter, fat and acid rescue it: butter or olive oil, a squeeze of "
          "lemon, a pinch of sugar, or bacon and onion fried first and the cabbage tossed through.",
          avoid=("smell", "smelly", "stink", "house", "room", "kitchen", "keep", "keeping",
                 "store", "buy", "grow", "growing", "plant", "slug", "slugs", "freeze", "recipe",
                 "soup", "raw", "salad",
                 # a green potato is solanine, which is the poisonous answer, not this one
                 "potato", "potatoes", "solanine", "green potato", "green potatoes")),
    entry("cabbage-better",
          (("cabbage", "spring greens", "sprouts", "sprout", "kale"),
           ("taste better", "tastier", "nicer", "more interesting", "liven", "boring", "bland",
            "enjoy", "like it", "make it", "how do i make")),
          "Three things, in this order: cooking it less, fat and salt. Boil or shred-and-fry it for "
          "4 to 6 minutes only, then toss it with butter or a little oil, salt, and something "
          "sharp - lemon, vinegar, or a spoon of mustard. Fried bacon or chorizo, onion softened "
          "first, a pinch of chilli or caraway, or a dusting of nutmeg all give it a reason to be "
          "on the plate. A splash of cream or a spoon of yoghurt turns it into something people go "
          "back for.",
          avoid=("bitter", "bitterness", "smell", "smelly", "stink", "keep", "keeping", "store",
                 "buy", "grow", "growing", "plant", "slug", "slugs", "freeze", "recipe", "soup",
                 "leftover")),
    entry("salad-wilt", (LEAFY, ("fresh", "keep", "keeping", "store", "storing", "crisp",
                                 "crisper", "crispy", "soggy", "slimy", "rubbery", "gone over",
                                 "last", "longer", "how long", "a week", "days")),
          "About 5 days in the salad drawer; a whole unopened bag keeps a week longer. Wash and dry "
          "the leaves properly, keep them in a bag with a piece of kitchen paper and dress them "
          "only at the table, because wet leaves and early dressing are what make salad limp. "
          "Brown-edged or slimy leaves are past it, so pick those out before they spread.",
          # a line swapping one form for another is the form answer's, not a keeping one:
          # "can i use fresh spinach instead of frozen" was getting the salad-drawer answer
          # a salad that has gone soggy is a wet-salad question, not a shelf-life one: that is
          # `soggy-lunch` below, and the shelf life is the wrong answer to it
          avoid=LEAFY_AVOID + ("instead", "instead of", "in place of", "substitute", "swap",
                               "swapped", "frozen", "freezer", "tinned", "canned", "jarred",
                               "dried", "soggy", "went soggy", "gone soggy", "going soggy",
                               "wet", "dressing", "dressed", "sauce")),
    entry("salad-revive", (LEAFY, ("limp", "wilt", "wilted", "wilty", "revive", "reviving",
                                   "floppy", "perk", "crisp up")),
          "Plunge it in iced water for 10 to 15 minutes: cut an inch off the stems first if it is "
          "a whole lettuce or a bunch, and most of the crispness comes back. Dry it in a tea "
          "towel afterwards and keep it in a bag with a piece of kitchen paper, because wet "
          "leaves are what made it limp in the first place.",
          avoid=LEAFY_AVOID),
    # What goes in a sandwich had no row of its own: `recipe-sandwich` in cooking.py is a recipe
    # and stands down unless the line asks how to make one, so "what can i put in a sandwich" and
    # "what goes in a sandwich" were a shrug while the fillings were on the card that refused
    # them. "ideas for sandwich fillings" reached the satiety row instead, which answers how
    # filling a food is. A sandwich asking what to put in it wants the list.
    entry("sandwich-fillings",
          (("sandwich", "sandwiches", "sarnie", "sarnies", "butty", "butties", "toastie",
            "toasties", "toasted sandwich", "lunchbox sandwich", "packed lunch sandwich",
            "sandwich filling", "sandwich fillings", "wrap", "wraps", "flatbread"),
           ("put in", "put inside", "goes in", "go in", "fill", "filling", "fillings",
            "ideas", "idea", "different", "instead of", "bored of", "boring", "sick of",
            "always have", "something")),
          "One moist thing and one with a bit of crunch or sharpness, and it stops being a sad "
          "sandwich: cheddar with apple and pickle, tuna with celery and a little mayo (drained, "
          "or the bread goes), hummus with grated carrot and cucumber, or leftover roast chicken "
          "with lettuce and mustard. Butter both slices to the edges first so the bread does not "
          "go soggy, and keep tomato or cucumber in the middle. Egg with cress, brie with grape, "
          "or corned beef with a lot of mustard are the other three worth having in your pocket.",
          # the making, the keeping and the soggy bread are their own answers, and a party or a
          # child's lunchbox is a different question from what to put in your own
          avoid=("recipe", "how do i make", "make a sandwich", "soggy", "wet bread", "how long",
                 "last", "lasts", "keep", "keeps", "keeping", "store", "stored", "freeze",
                 "frozen", "calories", "how many", "healthy", "kids", "children", "party",
                 "buffet", "platter", "shop", "buy", "cost",
                 # a lunch with no sandwich in it is asking for something else entirely: "what
                 # can i put in a packed lunch that isnt sandwiches" was given the fillings
                 # list, which is the one thing it ruled out.
                 "isnt", "is not", "not a sandwich", "not sandwiches", "no sandwich",
                 "no sandwiches", "without a sandwich", "without sandwiches",
                 "instead of a sandwich", "instead of sandwiches", "other than a sandwich",
                 "apart from sandwiches", "besides sandwiches",
                 # and "is a sandwich enough for lunch" is a how-filling question, not a
                 # what-shall-i-put-in-it one
                 "how filling", "fill me up", "keeps me full", "how much food"),
          # "what can i put in a sandwich" carries no ask of its own, and the satiety row keys
          # the same "filling" with a bias, so this row needs the point on its side to take it.
          bias=2),
    entry("soggy-lunch", (("salad", "salads", "lettuce", "leaves", "sandwich", "sandwiches",
                           "wrap", "wraps", "roll", "rolls", "baguette", "sub", "subs",
                           "coleslaw", "pasta salad", "lunch", "lunchbox", "packed lunch"),
                          # "watery" is deliberately not here: a watery salad is salt pulling
                          # the water out of the cabbage or the cucumber, which is `fix-watery`'s
                          # line and the better answer for coleslaw. The soggy words do the work.
                          ("soggy", "went soggy", "gone soggy", "going soggy", "goes soggy",
                           "wet", "leaky", "dressing", "dressed", "sauce")),
          _soggy_lunch,
          # a limp or wilted leaf is `salad-revive`, and a keeping question is the shelf life
          # the keeping words are phrases on purpose: "keeps" would match the bare "keep" in
          # "how do i keep a sandwich from going soggy", which is a wet-bread question
          avoid=("limp", "wilt", "wilted", "revive", "crisp up", "how long", "last", "lasts",
                 "keep fresh", "stay fresh", "stays fresh", "freeze", "frozen", "buy", "grow")),
    entry("herbs-keep", (("herbs", "basil", "parsley", "coriander", "cilantro", "mint", "dill",
                          "chives"),
                         ("keep", "keeping", "store", "storing", "fresh", "last", "longer",
                          "how long", "a week", "days", "wilt", "wilted", "limp",
                          "soggy", "droop", "droopy", "rubbery", "slimy", "gone over")),
          _herbs_keep,
          # a dried herb does not go in a jar of water: those lines are dried-herbs', and a
          # supermarket pot somebody wants to keep alive is a plant question, not a cut-herb one
          avoid=("plant", "growing", "grow", "soil", "pot", "leaves", "dried", "dry", "drying",
                 "alive", "keep alive", "keeping alive", "from dying", "stop dying",
                 # "keep dying" is the same plant question said the other way round: a herb
                 # that keeps dying is being grown, not kept in a jar
                 "keep dying", "keeps dying",
                 # A herb that has gone yellow is a growing plant, not a bunch in a bag: the word
                 # was a key of this row, so "my basil is going yellow" got the jar of water
                 # instead of the pot answer. It is a fence now, not a key.
                 "yellow", "yellowing", "yellowed", "gone yellow", "going yellow",
                 # The same fence was one word short again: "how do i keep parsley going over
                 # winter" and "how do i keep chives coming back" name no pot and no soil, so
                 # the cut-herb row took them and answered with a jar of water. A herb that is
                 # going, coming back or overwintering has roots, and garden.py answers it.
                 # not the bare "going"/"gone": "my herbs have gone slimy" is this row's own
                 # slimy branch, and fencing it turned a good answer into a shrug
                 "going over", "going to seed", "keep going", "come back", "comes back",
                 "coming back",
                 "over winter", "over the winter", "overwinter", "overwintering",
                 "through the winter", "survive", "survives", "perennial", "dies back",
                 "garden", "outside", "border"),
          bias=1),
    # choosing one is the same question as testing one: "how do i choose a good avocado" and
    # "how do i pick a ripe one" were a search hedge, because this row only knew the word ripe.
    entry("avocado-ripen", ("avocado", ("ripe", "ripen", "hard", "quick", "soft",
                                        "how do i pick", "how do i choose", "pick a good",
                                        "choose a good", "pick the best", "good one")),
          "Put a hard avocado in a paper bag with a banana and leave it on the counter for a day or "
          "two; the banana's gas speeds it up. Once it gives slightly at the stem end it's ready, "
          "and lemon juice stops a cut one going brown."),
    # "Green" is the word for a banana that is not ripe, and it was not a key: "my bananas are
    # still green", "the bananas are too green" and "my bananas are still hard" were a nod, while
    # "how do i ripen bananas" was this row. A banana is not in keeping.py's ripen table (its
    # keeping is a row of its own, banana-keep), so the words live here.
    entry("banana-ripe", (("banana", "bananas"),
                          ("ripe", "ripen", "ripening", "brown", "black", "quick",
                           "green", "still green", "too green", "very green", "so green",
                           "hard", "still hard", "too hard", "soften", "softer", "not ripe",
                           "unripe", "not ripening", "wont ripen", "wont go yellow")),
          "Bananas ripen fastest in a paper bag on the counter, especially with an apple; the "
          "fridge slows them right down but turns the skin black. Black-spotted skin is a sweet "
          "banana, and overripe ones are perfect for banana bread."),
    # Bananas: keeping them is not ripening them. "how do i store bananas" and "how long do
    # bananas last" had no entry, and the only banana entries are the ripe/black ones.
    entry("banana-keep", (("banana", "bananas"), ("store", "storing", "keep", "keeping", "last",
                                                  "longer", "fresh", "fridge", "how long",
                                                  "a week",
                                                  # the middle of the complaint is the point of it:
                                                  # "how do i keep bananas from going black" and
                                                  # "why do my bananas go black" were both the
                                                  # banana bread recipe, because "black" stood this
                                                  # row down and the overripe row took the line.
                                                  "going black", "go black", "goes black",
                                                  "from going", "stop them going", "stop it going",
                                                  "stay fresh", "last longer")),
          "They ripen because of the ethylene gas they give off themselves, so a bunch goes "
          "together and the top of the bunch goes first. Keep them on the counter, loose rather "
          "than in a bag or the fruit bowl with other fruit - an apple or a tomato speeds them up "
          "- and pull one off the bunch as you use them. Once they are as ripe as you like them, "
          "the fridge slows them right down: the skin goes black, the fruit inside stays good for "
          "days.",
          avoid=("ripen", "riper", "overripe", "mushy", "bread", "cake",
                 "plant", "tree", "growing", "grow", "allergy", "allergic", "skin",
                 # how many to eat is a nutrition question, not a keeping one: a storage tip
                 # for it is a confident wrong answer
                 "eat", "eating", "ate", "daily", "calorie", "calories", "fattening",
                 "healthy", "carbs", "sugar", "potassium", "diet")),
    entry("season-wok", (("wok", "woks", "carbon steel wok", "carbon steel pan"),
                         ("season", "seasoning", "seasons", "reseason", "re-season", "new",
                          "first", "stick", "sticking", "strips", "stripped", "smoke", "smoky",
                          "oily", "black", "look after", "care", "factory")),
          ("A new carbon steel wok comes with a factory oil on it: scrub that off with hot water "
           "and a drop of washing-up liquid, dry it on the hob, then heat it until it just begins "
           "to smoke and wipe a teaspoon of groundnut or rapeseed oil round the inside with kitchen "
           "paper - three or four times and it goes dark and glossy. After that wash it with hot "
           "water and a soft brush, no soap and never a soak, and dry it on the heat. A wok is not "
           "non-stick; it gets closer every time you cook in it."),
          avoid=("plant", "recipe", "sauce", "which wok", "buy", "best wok", "cast iron",
                 "cast-iron", "skillet", "burnt", "burned", "bicarbonate", "clean", "cleaning",
                 "wash", "washing", "scrub", "rust", "rusty", "sticky"),
          bias=3),
    # A wok that is already the owner's is cleaned, and the seasoning card answers a new one. Both
    # come up as "how do i ... a wok", and the everyday clean is the commoner question.
    entry("wok-everyday-cleaning",
          (("wok", "woks"),
           ("clean", "cleaning", "cleaned", "wash", "washing", "washed", "scrub", "scrubbing",
            "after every use", "after use", "dry", "drying", "rust", "rusty", "sticky")),
          ("Hot water and a soft brush while it is still warm, no washing-up liquid and never a "
           "soak, then dry it on the hob over a low heat and wipe a smear of oil round the inside "
           "with kitchen paper. That thin film is the whole of the care. If a patch of rust "
           "appears, scour just that spot, dry it, and season it again on the heat - a wok is not "
           "non-stick, it gets closer every time you cook in it."),
          avoid=("season", "seasoning", "new", "first", "plant", "recipe", "sauce", "buy",
                 "best wok", "cast iron", "cast-iron", "skillet", "burnt", "burned",
                 "bicarbonate", "dishwasher", "what is a wok", "whats a wok"),
          bias=4),
    entry("peel-tomatoes",
          (("peel", "peeling", "peeled", "skin", "skins", "skinned", "de-skin", "deseed",
            # "the best way to skin tomatoes" is the how, not "my tomatoes are splitting":
            # the phrase, so the whole-bare-word "skin" cannot take the garden question
            "skin tomatoes", "skin a tomato", "way to skin", "skinning tomatoes",
            "skinned tomatoes", "take the skins off"),
           ("tomato", "tomatoes", "plum tomatoes", "cherry tomatoes", "tomato skin",
            "tomato skins", "them", "these", "those")),
          ("Nick a small cross in the base of each one, drop them into boiling water for 20 to 30 "
           "seconds, then straight into cold water: the skin curls back at the cross and slips off "
           "with your fingers. For a sauce you can skip peeling and just grate the tomato "
           "cut-side down on a box grater - the skin stays in your hand."),
          # the seed question is a different answer, and a fruit with a peel of its own is not
          # this one: "how do i peel a mango" was reaching it through the bare peel word
          avoid=("seed", "seeds", "deseed only", "potato", "potatoes", "apple", "apples",
                 "mango", "orange", "oranges", "banana", "ginger", "garlic", "onion", "onions",
                 "carrot", "carrots", "butternut", "squash", "egg", "eggs", "prawn", "prawns",
                 "almond", "almonds", "peach", "peaches", "avocado",
                 # a tomato splitting on the vine is the garden question, and it names the skin
                 "splitting", "split", "cracked", "cracks", "burst", "bursting", "rot",
                 "rotting", "blossom end", "vine", "greenhouse", "crop")),
    entry("tomato-store", ("tomatoes", ("fridge", "store", "keep", "taste", "flavour")),
          "Keep tomatoes on the counter, not in the fridge: cold kills their flavour and turns the "
          "texture mealy. Only put them in the fridge once they're fully ripe and you need to keep "
          "them a few more days.",
          # a tin of tomatoes is not a ripe tomato on a counter
          avoid=("tin", "tins", "tinned", "can", "cans", "canned", "opened", "open", "jar",
                 "passata", "puree", "paste")),

    # --- baking -------------------------------------------------------------
    # Baking soda and bicarbonate of soda ARE the same thing, and the comparison row above used
    # to say they were not: "is baking soda the same as bicarbonate of soda", "are baking soda and
    # bicarbonate of soda the same" and "baking soda or bicarbonate of soda" all got "They are not
    # the same: baking soda is pure bicarbonate..." - which is the difference between the soda and
    # the powder, given to a question about one powder under two names. The identity is its own
    # row, fenced off the powder with "powder", so the comparison questions keep the comparison.
    entry("bicarbonate-is-baking-soda",
          (("baking soda", "bicarbonate of soda", "bicarb", "bicarbonate"),
           ("same as bicarbonate", "same as baking soda", "same as bicarb",
            "the same as bicarbonate", "the same as baking soda", "the same thing", "the same",
            "one and the same", "identical", "or bicarbonate of soda", "or baking soda",
            "or bicarbonate", "or bicarb", "bicarbonate and baking soda",
            "baking soda and bicarbonate", "bicarbonate and soda", "is bicarb baking soda",
            "is baking soda bicarb")),
          "Yes - baking soda and bicarbonate of soda are the same thing under two names: the "
          "American name and the British one. Baking powder is the different one, because it has "
          "an acid and a starch mixed in with the bicarbonate, so it fizzes on its own and the "
          "soda needs an acid such as buttermilk, yoghurt or lemon to do anything.",
          # a comparison of the soda with the powder is the other row's question, and so is a
          # recipe that names one of them
          avoid=("powder", "self raising", "self-raising", "how much", "in date", "out of date",
                 "tastes", "taste", "soapy", "cleaning", "clean", "drain", "soda bread",
                 "laundry", "washing", "drink", "drinking", "fizzy", "club soda", "soda water"),
          # higher than the comparison row's 4, because "baking soda or bicarbonate of soda" names
          # a pair too and the comparison row reads it as one: the identity row cannot take a line
          # with "powder" in it at all, so this bias only decides the one thing it is for
          bias=6),
    # The two powders are one question, and people ask it in a hurry with "vs", "or" or "which":
    # "baking soda vs powder" went to the general difference row, "bicarbonate of soda or baking
    # powder" was read as a choice between two named things and answered "Bicarbonate of soda...",
    # and "do i need baking powder or soda" was a punt. The powders are the subject and the
    # comparison words are the ask, as they are for the recipe line that already worked.
    entry("baking-soda-vs-powder", (("baking soda", "bicarbonate of soda", "bicarb", "soda",
                                     "baking powder"),
                                    # "substitute" and "do i need" were in this list and they
                                    # are a gate of their own elsewhere: main has a
                                    # uses-bicarbonate-of-soda-for-baking-powder row that reads
                                    # the substitution both ways, and "do i need" caught every
                                    # "do i need baking powder for pancakes" line and answered
                                    # it with the comparison. The comparison is what this row
                                    # is for, so it is keyed on the comparing words and the
                                    # substitution stays with the row that owns it.
                                    # "same" was here and it made this row lie: "is baking soda
                                    # the same as bicarbonate of soda" was answered "They are not
                                    # the same", and they are. The identity has its own row above,
                                    # keyed on the same phrases, so the comparison keeps the
                                    # comparing words only.
                                    ("difference", "substitute", "instead", "vs", "v", "versus",
                                     "or", "which one", "which",
                                     # "or" on its own is a stopword, so the phrasings people
                                     # actually use are keyed whole
                                     "or baking powder", "or soda", "or bicarb",
                                     "difference between", "which one do i need")),
          "They are not the same: baking soda is pure bicarbonate and needs an acid (buttermilk, "
          "yoghurt, lemon, treacle) to make things rise, while baking powder already has the acid "
          "in it. One way is easy and the other is not: in place of a teaspoon of soda use about "
          "three teaspoons of baking powder, and put the acid the recipe counted on in some other "
          "way or the tang is lost; in place of a teaspoon of baking powder use a quarter teaspoon "
          "of bicarbonate with a teaspoon of lemon juice or vinegar, and only in something that "
          "has the acid to meet.",
          # a recipe that already names one of them keeps its own answer, and so does a stale tin
          # and a too-much-bicarbonate cake; the self-raising question has the conversion and the
          # cleaning question is about cleaning, not about cake
          avoid=("how much", "in date", "out of date", "old", "stale", "leftover", "flat",
                 "self raising", "self-raising", "plain flour", "cleaning", "clean", "caustic",
                 "soda bread", "drain", "laundry", "washing", "tastes", "taste", "soapy",
                 # a swap question ("can i use bicarbonate of soda instead of baking powder")
                 # is the uses-bicarbonate-of-soda-for-baking-powder row's, and that row reads
                 # the direction the line asked; this row's comparison answered it the wrong
                 # way round once it outranked it
                 "instead", "instead of", "in place of", "substitute", "replacement",
                 # "soda" is a drink as well as a raising agent, and the key's bare "or"
                 # matched the drinking question: "should i drink soda or water" was handed the
                 # leavening lecture. The drinking words stand this row down, and the water card
                 # answers it as it does on main.
                 "drink", "drinking", "drink it", "thirsty", "fizzy", "cola", "coke", "pop",
                 "club soda", "soda water", "tonic", "sparkling", "lemonade"),
          bias=4),
    # The everyday "how do i make it" asks that had no entry: a bread line reached bread-rise
    # only if it also said rise or yeast, a cake line reached cake-time only if it said bake or
    # how long, and "how do i make soup" reached soup-thick only with thick or thin in it. One
    # entry each for the making itself, with the faults left to the entries that already hold them.
    # Each of the three needs a question in the line: an announcement ("im making a cake for my son
    # on saturday", "im baking some bread tomorrow") is the dish-plan path in bot/modules/answers.py.
    entry("bread-make", (("bread", "dough", "loaf", "loaves", "baguette", "rolls", "buns"),
                         ("make", "making", "bake", "baking", "recipe", "from scratch", "white",
                          "wholemeal")),
          _bread,
          # the avoid list below carries the word "yeast", which only keeps a yeast question off
          # the method: "how do i make bread without using yeast" still got the knead-and-prove
          # method with the yeast in it, so a line that says the yeast is not there stands down
          guard=_leaves_out("yeast"),
          avoid=("rise", "rising", "risen", "yeast", "flat", "puff", "sourdough", "starter",
                 "keep", "store",
                 "stale", "mouldy", "mould", "mold", "fresh", "tastes", "taste", "flavour",
                 # a loaf already in the kitchen is a use-it-up question, and "leftover bread
                 # recipes" got the full knead-and-prove method ("recipes" is an ask word here).
                 # The marker has to sit on the bread itself: "bread recipes using leftover milk"
                 # is a loaf question, and the milk is the leftover.
                 "leftover bread", "left over bread", "leftovers bread", "bread leftovers",
                 "old bread", "stale bread", "yesterdays bread", "use up the bread",
                 "use up bread", "using up bread",
                 "naan", "pitta", "pita", "focaccia", "ciabatta", "soda", "banana", "garlic",
                 # a sweet loaf is not this bread: "how do i make a loaf cake", "fruit loaf",
                 # "malt loaf recipe" and "lemon drizzle loaf" were all getting the yeast method.
                 # Single words only, because avoid is matched word by word and a phrase such as
                 # "loaf cake" can never fire.
                 "cake", "cakes", "fruit", "malt", "drizzle", "teacake", "carrot", "courgette",
                 "zucchini", "pumpkin", "sultana", "sultanas", "raisin", "raisins", "cherry",
                 # a timer question wants the tin time, not the whole method
                 "long",
                 # this recipe is a white loaf with wheat in it, so it is the wrong answer to
                 # every other flour: a gluten-free or wholemeal line gets nothing rather than
                 # a strong-white-flour method, and the heat question keeps its own entry.
                 "gluten", "gluten free", "gluten-free", "rye", "spelt", "spelt flour",
                 "without egg", "without eggs", "no egg", "no eggs", "egg free",
                 "eggless", "temperature", "temp", "degrees", "gas", "mark", "hot", "how hot",
                 "oven"),
          ask=(("how", "what", "which", "recipe", "recipes", "should", "could", "can", "help",
                "advice", "tips"),)),
    # Three bread checks that are not the method: is the yeast still alive, is the dough too
    # stiff, and is the oven running hot. bread-make keys dough, so each of these is keyed on the
    # fault and stands down for the how-to, so "how do i make bread" keeps its method.
    entry("yeast-alive", (("yeast", "yeasts"),
                          ("alive", "dead", "died", "active", "test", "testing", "check", "fresh",
                           "old", "out of date", "expired", "expiry", "date", "working", "work",
                           "foam", "foamy", "bubble", "bubbles", "fizzy", "prove", "proof",
                           "rise", "risen", "fail", "failed")),
          "Stir a teaspoon of sugar into 100ml of water that is warm but not hot - about 35C, "
          "blood heat, because over 45C kills it - sprinkle the yeast on top and leave it 10 "
          "minutes. A thick foam across the surface means it is alive and ready to use; if it "
          "sinks and sits there, it is dead, and fresh yeast is the only fix. Do this before you "
          "weigh anything else: it costs ten minutes and it is the first thing to rule out when a "
          "loaf does not rise.",
          # the method, the flours and the other faults all have their own answers
          avoid=("how do i make", "recipe", "flour", "knead", "oven", "temperature",
                 "how much", "how many", "sourdough", "starter", "baking powder", "fresh bread"),
          ask=(("how", "what", "is", "should", "can", "does", "do", "why", "know", "tell",
                "test", "check", "still"),)),
    entry("dough-tight", (("dough", "doughs", "mix"),
                          ("tight", "stiff", "dry", "firm", "tough", "hard", "stretchy",
                           "elastic", "springy", "tearing", "tears", "resists", "resist",
                           "add water", "more water", "water", "wet", "sticky", "slack",
                           "runny", "sloppy", "tacky", "gooey")),
          _dough,
          avoid=("how do i make", "recipe", "pizza", "pastry", "cookie", "cookies", "cake",
                 "scone", "shortcrust", "biscuit", "breadcrumbs", "breaded", "filo", "puff",
                 "freeze", "freezer", "fridge", "keeping", "keeps", "overnight", "leftover",
                 "chicken", "meat", "fish", "batter"),
          ask=(("my", "should", "can", "do", "how", "what", "is", "why", "add", "need"),)),
    # A bare ask for the oven's heat has no dish to go on, and the dial row answered it with
    # "drop the dial about 20C for a fan oven" - advice about an oven that runs hot, where the
    # person wanted the number to set. A line that names a dish keeps that dish's own heat.
    # The ask is the wording, not one keyword: the dial row (`oven-hot` below) matches "oven"
    # plus "temperature" too, and a row that only holds the same two words never outscores it -
    # the phrase is what says the question is about the heat to set. Every phrase is one way of
    # asking the same thing, so a new way of asking belongs in this list beside the others.
    entry("oven-heat", (("what temperature should the oven be", "what temperature should my oven be",
                         "what temperate should the oven be", "what temp should the oven be",
                         "what temperature do i set the oven", "what temperature should i set the oven",
                         "what temp do i set the oven", "what temperature should the oven",
                         "how hot should the oven be", "what heat should the oven be",
                         "what temperature for the oven", "what temperature is the oven",
                         "what temperature should an oven be", "what temperature to cook at",
                         "what temperature should i cook at", "what gas mark should the oven be",
                         "what gas mark should my oven be", "what gas mark for the oven",
                         "what temperature should i put the oven on", "what temp should i put the oven on",
                         "what temperature do you set an oven to", "what temp do you set an oven to",
                         "what temperature is my oven meant to be", "what temperature is an oven meant to be",
                         "what setting should the oven be on", "what setting should the oven be",
                         "what setting should my oven be on", "what setting do i put the oven on"),
                        ("oven", "temperature", "temp", "hot", "heat", "cook", "bake", "set", "gas")),
          "For most things, 180C (160C fan, gas mark 4) for cakes, biscuits, a tray of "
          "vegetables and a slow roast, and 200C (180C fan, gas mark 6) for chips, roast "
          "potatoes and anything you want brown and crisp. Go to 220C (200C fan, gas mark 7) "
          "for a fast pizza or a crisp edge, and down to 150C (130C fan, gas mark 2) for "
          "meringues and slow bakes.",
          # a dish named in the line keeps its own heat, and an oven running hot is the dial
          avoid=("chips", "chip", "cake", "cakes", "sponge", "chicken", "turkey", "beef", "pork",
                 "lamb", "joint", "bread", "pizza", "pastry", "yorkshire", "muffin", "scone",
                 "biscuit", "cookie", "meringue", "casserole", "fish", "salmon", "lasagne",
                 "lasagna", "pie", "potatoes", "air fryer", "airfryer", "microwave",
                 "slow cooker", "runs hot", "running hot", "too hot", "overheat", "overheats",
                 "calibrate", "thermometer", "dial", "not working", "wont heat", "won't heat",
                 "not heating", "not heat up", "broken", "smoking", "smoke", "fever", "body",
                 "fridge", "freezer", "water", "baby", "milk"),
          bias=1),
    entry("oven-hot", (("oven", "fan", "fan oven", "temperature", "temp", "gas", "gas mark",
                        "dial", "thermometer", "degrees"),
                       ("hot", "hotter", "overheats", "runs hot", "too hot", "running hot",
                        "drop", "lower", "reduce", "adjust", "temperature", "temp",
                        "check", "accurate", "wrong", "thermometer", "fan",
                        # "how do i calibrate my oven" asks for the same figure this row gives,
                        # and it reached nothing: no other row is about the oven's own heat.
                        # It is asked about the oven here, not named as one: a line that names
                        # the oven still needs one of these words to be this row's question.
                        "calibrate", "calibrated", "calibration", "calibrating")),
          "Drop the dial about 20C for a fan oven, and check the real heat with a cheap oven "
          "thermometer hung in the middle: an oven that runs 25C hot browns the outside before the "
          "middle is set, which is the commonest reason a bake burns on the bottom and stays raw "
          "in the middle. Trust the thermometer over the dial, turn the tray round halfway "
          "through, and if yours runs hot by a fixed amount, note the number you actually use on "
          "a sticker inside the door.",
          # the dish timings and the bread heat keep their own answers
          avoid=("bread", "cake", "roast", "chicken", "pizza", "pastry", "yorkshire", "muffin",
                 "scone", "biscuit", "cookie", "casserole", "air fryer", "airfryer",
                 "microwave", "slow cooker", "not heating", "wont heat", "won't heat",
                 "not working", "broken", "smell", "smoke", "door", "light",
                 # the fan is the mechanical part, and a noisy or sticking fan is a repair
                 # question: "the fan in my oven is noisy" was getting the dial advice
                 "noisy", "noise", "loud", "rattl", "rattling", "rattles", "grinding", "squeak",
                 "squeaky", "bulb", "seal", "hinge", "element", "stays on", "stay on",
                 "wont turn off", "won't turn off", "keeps running", "spins", "shelf", "shelves",
                 "rack", "clean", "cleaning",
                 # a bill is not a dial: "how do i lower my gas bill" was getting "drop the
                 # dial about 20C for a fan oven", because "gas" and "lower" met in this key.
                 # The bill and the boiler are money going out, and energy-bill answers them.
                 "bill", "bills", "bill has", "bill went", "bill is", "energy", "tariff",
                 "standing charge", "unit rate", "direct debit", "kwh", "boiler",
                 "heating", "radiator", "radiators", "thermostat", "insulation",
                 "smart meter"),
          ask=(("my", "should", "can", "do", "how", "what", "is", "why", "does", "check"),),
          # "should i check my temperature" met "temperature" and "check" in this key and was
          # told to drop the oven dial 20C for a fan oven. A person's own temperature is the
          # body rows' line, and the word "check" is how a fever question is put.
          # ...and a dish's own oven heat is the dish table's answer: "what temperature should
          # the oven be for chips" was told to drop the dial 20C, when the number wanted is 200C.
          guard=lambda understood: (not a_persons_temperature(understood)
                                    and not something_to_bake_in_the_oven(understood))),
    entry("cake-make", (("cake", "cakes", "sponge", "victoria", "sponges"),
                        ("make", "making", "recipe", "from scratch", "plain", "vanilla",
                         "chocolate")),
          "Weigh 4 eggs in their shells and use the same weight of butter, caster sugar and "
          "self-raising flour: beat the butter and sugar until pale, add the eggs a spoon at a "
          "time, fold in the flour, then split it between two greased 20cm tins. Bake at 180C "
          "(160C fan) for 25 to 30 minutes, until it springs back and a skewer comes out clean, and "
          "sandwich it with jam and buttercream once it is cold.",
          avoid=("time", "temperature", "oven", "sink", "sank", "sunken", "stuck", "burn", "burnt",
                 "nut", "nuts", "allergy", "allergic", "birthday", "party", "freeze", "keeping",
                 "icing", "frosting", "decorate", "vegan", "gluten",
                 # an egg-free cake is a substitution question and main already answers it;
                 # "weigh 4 eggs" is the wrong answer to it.
                 "without egg", "without eggs", "no egg", "no eggs", "egg free", "egg-free",
                 "eggless", "flax", "aquafaba", "chocolate") + NO_SUGAR,
          ask=(("how", "what", "which", "recipe", "recipes", "should", "could", "can", "help",
                "advice", "tips"),),
          # the avoid list above holds the phrasings that were written out; this holds the rest,
          # because "without using eggs", "without any eggs" and "made with no butter" are the
          # same question and no list of them stays complete
          guard=_leaves_out("egg", "butter")),
    # A tin is a size question and a lining question, and main shrugged at both: "what size loaf
    # tin should i use" and "should i line my loaf tin" got "a search should sort you out".
    entry("loaf-tin",
          (("loaf tin", "loaf tins", "bread tin", "cake tin", "cake tins", "tin size", "tins",
            "tin"),
           # "bread" and "cake" are here for "which tin for a fruit cake"; the four lines they
           # used to steal - a storage, a timing, a cleaning and a "without butter" question -
           # are held off in the avoid list below, one phrase each.
           ("what size", "size", "which size", "how big", "how much", "loaf", "bread", "cake",
            "line", "lined", "lining", "grease", "greased", "parchment", "paper", "need",
            "buy", "big", "small", "fit", "fills")),
          _tin_answer,
          # a tin of food is the storage questions' and the tinned-goods answers', not a tin size
          # "tinned" and "rusty" are left out: a loose form match makes "tinned" hit the word
          # "tin" itself and veto every line this entry is for.
          avoid=("of beans", "of tomatoes", "of tuna", "of soup", "of peaches", "of sweetcorn",
                 "of chickpeas", "opened", "open tin", "canned", "rust", "recycle", "recycling",
                 "biscuit", "biscuits", "baked beans",
                 # a cake that will not come out of its tin is the turning-out answer's line
                 "out of the tin", "out of a tin", "out of the pan", "out of a pan",
                 "out of its tin", "out of its pan", "stuck", "sticks",
                 "loosen", "loosening", "wont come out", "won't come out", "turn it out",
                 "turned out", "shrinking", "came out",
                 # a roasting tin for a joint is a different tin and a different answer
                 # ("christmas" is not here: a christmas cake's tin size is this answer's line)
                 "roasting tin", "roast tin", "roasting", "roast", "traybake", "tray bake",
                 "chicken", "turkey", "joint of meat",
                 # and a line that says it is making bread wants the bread method, tin or no tin
                 "make bread", "bake bread", "baking bread", "bread in", "bread dough", "knead",
                 # keeping, timing, cleaning and what to use instead of butter are four other
                 # questions that name a tin
                 "store", "storing", "stored", "keep", "keeps", "keeping", "kept", "how long",
                 "burnt", "burn", "clean", "cleaning", "scrub", "wash", "without butter",
                 "no butter", "instead of butter", "margarine",
                 # "grease" and "line" are in this row's key for "which tin for a fruit cake",
                 # but a line asking how to grease or line one wants the method, not the
                 # measurements: "how do i grease a cake tin" tied with this row for the top
                 "grease a cake tin", "grease the cake tin", "grease a loaf tin",
                 "grease the loaf tin", "grease a tin", "grease the tin", "grease and line",
                 "greasing a tin", "how do i grease", "what do i grease",
                 "prepare a cake tin", "prepare the cake tin", "prepare my cake tin",
                 "prepare a loaf tin", "prepare the loaf tin", "prepare a tin",
                 "prepare the tin", "prepare a baking tin", "how do i prepare",
                 # a tin of pulses is a cooking question, not a tin size, and "do i need to soak
                 # tinned chickpeas" got the loaf-tin measurements. The pulse's name is in the
                 # line but "of chickpeas" only catches one word order, so the food's own names
                 # stand this entry down wherever they appear. "tinned" is not here: it is a
                 # loose form of "tin" itself and would veto every line this entry is for.
                 "chickpea", "chickpeas", "lentil", "lentils", "beans", "pulses", "soak",
                 "soaking", "soaked", "drained and rinsed",
                 # a tin of paint is the decorating question's, and "how much does a tin of
                 # paint cost" was answered with loaf sizes: the paint words stand this down
                 "paint", "painting", "paint tin", "emulsion", "wallpaper", "gloss", "undercoat"),
          ask=(("how", "what", "which", "should", "could", "can", "do i", "size", "help")),
          bias=1),
    entry("soup-make", (("soup", "soups"),
                        ("make", "making", "recipe", "vegetable", "chicken", "lentil", "leek",
                         "squash", "carrot", "from scratch")),
          "Soften a chopped onion in oil with a pinch of salt for 8 to 10 minutes, add the main "
          "vegetable - about 700g of squash, carrots, leeks or tomatoes - then cover it with a "
          "litre of stock and simmer 20 minutes until everything is soft. Blend it, taste for salt "
          "at the end, and add a potato or a handful of lentils if you want it thicker without cream.",
          avoid=("thick", "thinner", "runny", "bland", "salty", "keep", "freeze", "reheat",
                 "leftover", "tinned", "tin", "packet", "sachet", "canned", "shop",
                 # A pulse named in the line has its own card - soak or not, how long to simmer -
                 # so "making a soup with lentils" and "im making soup with chickpeas" keep that
                 # answer instead of the vegetable method that mentions lentils in passing.
                 "lentil", "lentils", "chickpea", "chickpeas", "split peas", "beans", "pulses"),
          # An announcement of soup is its method question: "im making chicken soup" and "i have
          # chicken and want soup" were both answered with a chicken stir-fry, because the dish
          # they named is not one of the kitchen's plans and the ingredient picker took the line.
          ask=(("how", "what", "which", "recipe", "recipes", "should", "could", "can", "help",
                "advice", "tips", "making", "make", "made", "cooking", "cook", "want", "wanted",
                "fancy", "planning"),)),
    # A slow cooker is not an oven: "can i cook a whole chicken in a slow cooker" was getting the
    # 190C timings, which is a wrong answer rather than a different one.
    entry("slow-cooker-chicken", (("chicken", "bird", "chicken thighs"),
                                  ("slow cooker", "slow-cooking", "slow cooked", "crockpot",
                                   "crock pot", "slowcooker", "slow")),
          "In a slow cooker a 2kg chicken takes 4 to 5 hours on low, or 3 hours on high: sit it on "
          "a few balls of foil so it is not stewing in its own juice, and do not add water, as it "
          "makes plenty. Check the thigh juices run clear and the thickest part reaches 75C before "
          "you take it out.",
          # "how long in the slow cooker for a whole chicken" ties with roast-chicken on 5 and
          # loses on key length, so a bias breaks the tie in favour of the method named.
          # A leg or a drumstick has its own entry and its own time (2 to 3 hours on low), so a
          # line that names one is not the whole bird; without this "can i cook chicken legs in
          # the slow cooker" was told a 2kg bird takes 4 to 5 hours.
          avoid=("frozen", "defrost", "thighs only", "breast", "leg", "legs", "drumstick",
                 "drumsticks"), bias=1),
    # "flat" is the word for a loaf that did not rise, so a line with bread or dough in it and
    # "flat" in it is this entry, not fix-bland (which reads "flat" as the taste of dull food and
    # carries bias=1, so it used to win every one of these).
    # A shaper's loaf has its own name, and "the naan didnt puff up" is the same fault as
    # "the bread didnt rise", so every name a person gives their dough stands in for "bread".
    entry("bread-rise", (("bread", "breads", "dough", "sourdough", "loaf", "loaves",
                          "focaccia", "pitta", "pita", "naan", "buns", "bun", "rolls",
                          "baguette", "ciabatta"),
                         ("rise", "rising", "risen", "flat", "yeast", "puff up", "puffed up",
                          "prove", "proves", "proving", "proved", "proof", "proofed",
                          "proofing")),
          _bread_rise_answer(),
          # The keeping questions are held out as phrases, not as the bare word "keep": "my bread
          # keeps coming out flat" is this fault said with the fault verb, and the bare word was
          # standing this entry down for it, so the storage row answered a baking question ("It
          # keeps 3 days in a paper bag"). A line that asks how long it keeps still has "how
          # long", "store", "fridge" or "shelf life" in it, and those stay here.
          avoid=("mouldy", "mould", "mold", "stale",
                 "shelf life", "shelf-life", "store", "storing", "storage",
                 "keep fresh", "keeps fresh", "stays fresh", "stay fresh", "keeps for",
                 "keep for", "in the fridge", "in the freezer", "how do i keep", "how to keep",
                 # "my bread tastes flat" is a seasoning question, so leave it to fix-bland
                 "taste", "tastes", "tasting", "flavour", "flavourless", "bland", "seasoned",
                 "seasoning", "salt", "salty",
                 # no yeast at all is a soda loaf, and there is nothing to prove without it
                 "without", "yeastless",
                 # A loaf that went up and came back down is a collapse, not a prove that is
                 # still running: "my bread rises then sinks" was told to leave it another hour
                 # at 25C, which is the advice for a dough that has not risen yet. The rise
                 # words are the first half of the collapse row's key, so a line with a fall
                 # word in it belongs there. "my bread didnt rise" and "my bread won't rise" have
                 # no fall word and keep this answer.
                 "sink", "sinks", "sinking", "sank", "sunk", "collapse", "collapses",
                 "collapsed", "collapsing", "deflate", "deflates", "deflated", "fallen",
                 "fell", "caved in", "caves in", "flopped"),
          bias=1),
    # bread going mouldy or stale has its own answers now, so those words stay out of this key
    # Keeping questions for the things people ask about and the base had no answer for: a cake, a
    # block of butter, an avocado once it is cut. Each one needs a keeping word as the second part
    # so the baking and the ripeness questions keep their own answers.
    entry("cake-keep", ("cake", ("keep", "keeps", "keeping", "last", "lasts", "store", "storing",
                                 "fridge", "freeze", "frozen", "shelf life", "shelf-life",
                                 "how long", "still good", "gone off",
                                 # "how do i stop a cake going stale" is the same keeping question
                                 # asked as a prevention, and it was reaching a cut-the-sugar row
                                 "stale", "going stale", "go stale", "goes stale", "stay fresh",
                                 "stays fresh", "keep fresh", "keeps fresh", "fresh for")),
          "A plain sponge or fruit cake keeps 3 to 4 days in a tin, and a week in the fridge if it "
          "has fresh cream or custard in it. Undecorated, it freezes well for 2 months: wrap it "
          "whole, and ice it after it thaws. It goes stale because the starch firms up rather than "
          "because it dries out: a tin with a lid, half an apple in it, and 15 seconds in the "
          "microwave brings a slice back.",
          ask=KEEP_ASK,
          # the bake is a different question, "how long" belongs to it, and `freeze-food` already
          # wraps and freezes a cake better than this can
          avoid=("bake", "baking", "oven", "tin size", "sink", "sank", "rise", "risen", "recipe",
                 "freeze", "freezing", "frozen", "how long in the oven", "how long do i bake",
                 "how long should i bake", "take", "takes", "take to cook", "start to finish",
                 # a cake on its way out is a use-it-up question, and the answer to it is what to
                 # make with it (the pantry's cake row), not how long it keeps
                 "use up", "using up", "use it up", "use them up")),
    entry("baked-keep", (BAKED_GOODS_WORDS,
                         ("keep", "keeps", "keeping", "last", "lasts", "store", "storing",
                          "how long", "still good", "gone off", "shelf life", "shelf-life",
                          "fridge", "freeze", "frozen", "stale", "going stale", "stay fresh")),
          _baked_keep(),
          ask=KEEP_ASK,
          # the bake, the fault and the recipe are other answers, and "how long" alone is how the
          # bake gets asked, so those words stay out
          avoid=("bake", "baking", "oven", "recipe", "how long in the oven", "how long do i bake",
                 "how long should i bake", "take", "takes", "take to cook", "start to finish",
                 "temperature", "degrees", "gas mark", "why is", "why are", "why do", "sink",
                 "sank", "rise", "risen", "gooey", "crispy", "chewy", "burnt", "burn",
                 # how long it keeps is a different question from what to make with the rest of it
                 "use up", "using up", "use it up", "use them up")),
    entry("butter-keep", ("butter", ("keep", "keeps", "keeping", "last", "lasts", "store",
                                     "storing", "fridge", "freeze", "frozen", "shelf life",
                                     "shelf-life", "how long", "still good", "gone off",
                                     # "gone off" was in this key and "gone rancid" was not, so
                                     # "my butter has gone rancid" matched one word of the key and
                                     # was handed to a recipe suggester, which offered a cheese
                                     # toastie. The answer to a fat that has turned is the last
                                     # sentence of the reply below, so the words people use for
                                     # it are key words here.
                                     "rancid", "gone rancid", "smells off", "tastes off",
                                     "smells funny", "smells bad", "gone bad", "is it off",
                                     "out of the fridge", "soften")),
          "Butter keeps 2 to 3 weeks in the fridge and about 4 days in a covered dish on the "
          "counter; salted lasts longer than unsalted. It freezes for 3 months, cut into what you "
          "use in a fortnight. Rancid butter smells like old paint and tastes sharp, so bin it.",
          # and the ask has to allow the words people use for a fat that has turned: "my butter
          # has gone rancid" is not one of KEEP_ASK's questions, so the key words alone still
          # left it to the recipe suggester.
          ask=KEEP_ASK + ("rancid", "gone rancid", "smells off", "tastes off", "smells funny",
                          "smells bad", "gone bad", "off"),
          # "can you freeze butter" is main's freeze answer, which says yes and how to wrap it:
          # this entry only writes the keeping, so it leaves the freezing question alone.
          # Getting cold butter soft in a hurry is the softening row below, which is a how-to and
          # not a keeping fact: this entry's own key holds "soften", so "how do i soften butter
          # quickly" was told how long butter lasts in the fridge, and the softening row - which
          # exists and says to grate it - never got the line. A word in the key and the same word
          # in the avoid list is how a row hands its own neighbour's question back.
          avoid=("freeze", "freezing", "frozen", "make butter", "churn", "substitute",
                 "instead of butter", "margarine", "vegan butter", "buttercream", "shortbread",
                 "pastry", "biscuit",
                 # "room temperature" is not held out: it is how the keeping question is asked
                 # too ("how long does butter keep at room temperature"), and that stays here.
                 # The softening row holds its own keeping lines off instead.
                 "soften", "softening", "soft", "quickly", "quick",
                 "hard to spread", "too hard", "spread")),
    entry("avocado-keep", (("avocado", "avocados", "avocado half"),
                           ("keep", "keeps", "keeping", "last", "lasts", "store", "storing",
                            "fridge", "brown", "cut", "once cut", "half", "ripen", "ripe",
                            "shelf life", "shelf-life", "how long")),
          "A cut avocado keeps 1 to 2 days in the fridge: leave the stone in, press cling film "
          "right onto the cut face, and squeeze lemon or lime over it. The surface browns where "
          "air gets to it, which is harmless - scrape that bit off. A whole hard one ripens on the "
          "counter in 3 to 5 days and then keeps a day or two in the fridge.",
          ask=("how", "what", "can", "should", "does", "do", "will", "long", "keep", "keeps",
               "last", "lasts", "is", "are", "still", "ok", "okay", "safe", "store", "storing"),
          avoid=("grow", "tree", "plant", "guacamole", "toast", "recipe", "salad")),
    entry("leftover-pizza", (("pizza", "pizzas", "leftover pizza", "cold pizza"),
                             ("leftover", "left over", "cold", "next day", "keep", "keeps",
                              "fridge", "reheat", "reheating", "safe", "ok to eat", "still good",
                              "how long", "last", "lasts", "freeze")),
          "Cold pizza is fine if it went into the fridge within a couple of hours of arriving: eat "
          "it within 3 days, and reheat it to piping hot if you want it hot again - a splash of "
          "water in the pan or 10 minutes in a hot oven brings the base back. Pizza left out "
          "overnight is the one to throw away.",
          ask=("how", "what", "can", "should", "does", "do", "will", "long", "keep", "keeps",
               "last", "lasts", "is", "are", "still", "ok", "okay", "safe", "cold", "left",
               "leftover", "reheat", "eat"),
          # "say it while you are still there" was the restaurant-complaint answer and it took
          # every cold-pizza line, so the complaints keep their own words
          avoid=("restaurant", "takeaway", "delivery", "delivered", "deliver", "order",
                 "wrong order", "charged", "complaint", "complain", "refund", "manager",
                 "arrived", "arrive", "cold when", "when it arrived", "waited", "late",
                 "missing",
                 # a pizza BOX is `rubbish.dispose-pizza-box`: "can i put a pizza box in the
                 # recycling" was answered "cold pizza is fine if it went into the fridge", and so
                 # was "what bin does a pizza box go in", because the key held the bare word "box".
                 "box", "boxes", "bin", "bins", "recycling", "recycle", "cardboard", "compost",
                 "throw away", "get rid",
                 # "can i freeze pizza" is `freeze-food`'s question, which says how long and
                 # how to wrap it, and "how do i reheat pizza" is the reheat entry's, which
                 # names dry heat and the oven; this entry only writes the keeping.
                 "freeze", "freezing", "frozen", "reheat", "reheating", "warm it up",
                 # and "how long is pizza in the oven" is the oven's question: the bare "how
                 # long" in this key took the cooking time and answered with keeping
                 # the cooking words are phrases rather than bare "cook", because "cooked" is the
                 # same word family and "how long does cooked pizza keep" is this entry's own
                 # question: a keeping word on the line keeps the keeping answer.
                 # and a ball of dough is not a cooked pizza: "how long does fresh pizza dough
                 # last" is about the dough, which this entry has nothing to say about
                 "dough",
                 "oven", "bake", "baking", "baked", "to cook", "how long to cook",
                 "how long should i cook", "should i cook", "how long can i cook",
                 "how long do you cook", "cooking time", "how long do i cook",
                 "temperature", "degrees", "gas mark", "minutes", "how hot",
                 "take to cook", "takes to cook", "time in the oven")),
    # The knife, rather than the mixing bowl: "how should i slice a loaf of sourdough" and "how
    # thick should i slice bread" were the three-hour bread method, "how do i slice bread evenly"
    # was a shrug, and "why does my sourdough go stale so fast" was another.
    entry("bread-slice", (("bread", "loaf", "loaves", "sourdough"),
                          # a bare "why" and "dry" made this row the answer to "why is my bread
                          # dense"; the staling shape is asked with the word for it.
                          ("slice", "slices", "sliced", "slicing", "cut", "cutting", "thick",
                           "thickness", "thin", "evenly", "warm", "hot", "stale", "stales",
                           "staling")),
          _bread_sliced, bias=3,
          avoid=("cake", "cakes", "sponge", "loaf cake", "banana bread", "malt loaf", "teacake",
                 "mould", "mouldy", "mold", "moldy", "gone off", "bin it", "toaster", "toasted",
                 "make", "bake", "baking", "recipe", "ingredients", "knead", "prove", "oven",
                 "crumbs", "breadcrumbs", "pudding", "sauce", "filling", "slice of cake",
                 "pizza", "cheese", "ham", "shop", "buy", "supermarket", "price", "baker",
                 # keeping a loaf is bread-keep's question, and "how do i keep a cut loaf fresh"
                 # was answered with the knife: only the cutting is this row's.
                 "keep", "keeps", "keeping", "store", "storing", "fresh", "longer", "last",
                 "lasts", "lasting", "freeze", "freezer", "frozen", "shelf life", "paper bag",
                 "bread bin", "fridge",
                 # "is sliced bread ok" is about the bread, not the knife: a verdict stays with
                 # the rows that give verdicts.
                 "is it ok", "is it okay", "alright", "all right", "safe", "healthy", "good for",
                 "bad for", "fine to eat", "better for you", "ok", "okay",
                 # bringing a stale loaf back, or using it up, is the stale-bread rows' answer:
                 # "how do i refresh stale bread" and "what can i do with stale bread" were told
                 # why it went stale instead.
                 "refresh", "revive", "bring it back", "bring it round", "use up", "leftover",
                 "leftovers", "do with", "fault", "dense", "sank", "sunken", "flat", "risen",
                 "rise", "rising", "prove", "proving", "knead", "kneaded",
                 # what is in a slice is the nutrition rows' answer: "how much protein in a
                 # slice of bread", "calories in a slice of bread" and "how much salt in a
                 # slice of bread" were all handed the knife instead.
                 "how much", "how many", "protein", "calories", "calorie", "carbs", "carb",
                 "salt", "sugar", "fibre", "fiber", "iron", "vitamin", "healthy",
                 # how long it takes to go stale is the keeping row's question, and the
                 # complaint that it is stale already is the refresh row's.
                 "how long", "stale by", "already stale", "went stale", "gone stale",
                 "knife", "falls apart", "falling apart")),
    entry("bread-keep", (("bread", "loaf", "loaves"),
                          ("keep", "store", "fresh", "last", "longer", "soft", "freeze",
                                   "fridge", "bin", "paper bag", "hard", "dry",
                                   # "shelf life" is how people ask this too, and on its own it
                                   # was answered with a "Got it."
                                   "shelf life", "shelf-life")
                          # "is it ok to eat bread past the date" is this row's question, and the
                          # day on the pack is the whole of what makes it one. The fibre row took
                          # it instead, because "ok" and "eat" are not keeping words.
                          + PACK_DATE),
          _bread_kept,
          ask=KEEP_ASK,
          # "how do i stop my bread going mouldy" is a keeping question, so it has to stay in this
          # key even though the mould word is in it; only the bin-it phrasing goes to bread-mouldy.
          avoid=("stale", "going stale", "rise", "rising", "risen", "eggy", "bread and butter",
                 "garlic")),
    entry("jar-keep", (("jar", "pesto", "pickle", "pickles", "chutney", "jam", "marmalade",
                        "ketchup", "mustard", "mayonnaise", "mayo", "salsa", "dip", "tahini",
                        # a tube or a jar of puree is the same question, and "how long does
                        # tomato puree keep once opened" was a shrug. Not a bare "paste": a curry
                        # paste is a cooking question, and it took "how long does it take to
                        # cook" out of a paste conversation
                        "puree", "purees", "tomato puree", "tomato paste"),
                       ("opened", "open", "keep", "last", "fridge", "safe", "how long", "gone off",
                        "off", "ok", "store")),
          ("Once a jar is opened it lives in the fridge: pesto, sauces and ketchup are usually good "
           "for 1 to 2 weeks, pickles, chutney, jam and mustard for months, and the label's "
           "once-opened line beats any general rule. Keep the surface under a little oil and bin it "
           "if it smells sharp or the lid bulges."),
          # a jar is also where a dry staple lives: "how long does dry rice keep in a jar" is the
          # cupboard question, and its own row answers it
          avoid=("rice", "pasta", "spaghetti", "noodles", "flour", "lentils", "porridge",
                 "oats", "sugar", "cereal", "couscous", "quinoa"),
          ask=KEEP_ASK),
    entry("container-keep-follow", (("it", "that", "them", "the jar", "the bottle"),
                                    ("last", "lasts", "keep", "keeps", "fridge", "how long",
                                     "storing", "store")),
          _container_keep,
          ask=("last", "lasts", "keep", "keeps", "fridge", "how long", "storing", "store"),
          bias=3,
          # the food named in the line has its own keeping answer, and so does every dish
          # A person being put down is not food being stored: "it" plus "keeps" caught
          # "my friend keeps putting me down and it is getting to me".
          # "how long does it take to heal after a tooth out" is a wound healing, not food
          # keeping: "it" and "how long" were the whole of the match.
          avoid=OPEN_ASK + TOOTH_OUT + ("lid", "lids", "stuck", "budge", "tight", "loosen",
                            "undo", "jar",
                            # leave from an earlier year is not a jar: "i saved some holiday
                            # from last year can i use it" matched "it" + "last" and got the
                            # days a jar keeps
                            "holiday", "holidays", "annual leave", "days leave", "saved up",
                            "carry over", "carried over", "entitlement",
                            "put me down", "puts me down", "putting me down",
                            # "how do i keep it up" keeps something going, not food: the two
                            # words it shares with this row are the whole of the line
                            "keep it up", "keep going", "habit", "routine", "motivation",
                            # "how do i ask my coworker to keep it down" is noise, not a jar:
                            # "it" and "keep" were the whole match and the bias did the rest
                            "keep it down", "keep the noise down", "turn it down",
                            "noise", "noisy", "loud", "louder", "quiet", "quieter",
                            "music", "radio", "neighbour", "neighbours", "next door",
                            "colleague", "colleagues", "coworker", "coworkers", "co-worker",
                            "co-workers", "workmate", "workmates", "teammate", "teammates",
                            "at work", "office", "my desk", "the desk")
          + tuple(_FOOD) + ("milk", "cheese", "yogurt", "yoghurt", "cream", "butter", "eggs",
                            "rice", "pasta", "bread", "salad", "wine", "beer", "stock",
                            "day", "days", "week", "weeks", "month", "months",
                            # "it" and "that" are the follow-up, not a subject, so any line with
                            # a real subject of its own that also says "how long" matched here:
                            # "how long does it take to get over a breakup" was answered with
                            # the days a jar of pesto keeps. A grief is not a jar.
                            "breakup", "break up", "broke up", "my ex", "relationship",
                            "grief", "grieving", "mourning", "bereavement", "heal",
                            "healing", "get over", "getting over", "divorce",
                            # "how long does it take to <do something>" asks how long a job
                            # runs, not how long food keeps: the row keys the follow-up "it"
                            # with "how long", so "how long does it take to paint a room" was
                            # answered with the days a jar of pesto keeps. A keeping question
                            # says "does it last", not "does it take to".
                            "does it take to", "will it take to", "would it take to",
                            "will it take", "would it take", "does it take",
                            # "my fridge is always full and i never use it all" is the food
                            # waste question: it carries the follow-up "it" and the word
                            # "fridge", so this row's own two keys were the whole match. What
                            # the line is about is what gets thrown out, and `plans.food-shop-
                            # waste` is the card for that, so any waste phrasing stands this
                            # down - a keeping question asks how long the thing lasts.
                            "always full", "never use it all", "never use it", "never use them",
                            "use it all up", "waste", "wasting", "wasted", "went to waste",
                            "throw it away", "thrown away", "in the bin", "goes off",
                            # "how do i keep them busy on a long journey" is the children in the
                            # car: "them" and "keep" were the whole of the match, and the days a
                            # jar keeps is not what a person asks in a traffic jam.
                            "busy", "occupied", "entertained", "journey", "long journey",
                            "long drive", "car journey", "road trip", "motorway",
                            "flight", "plane", "ferry")),
    # The lid that will not turn. Tapping the rim and getting a grip is what usually does it, and
    # the hot water is for swelling a metal lid rather than for the food inside.
    entry("stuck-jar", (("jar", "lid", "lids", "jam jar", "pickle jar", "screw top", "screw-top",
                         "vacuum seal", "cap"),
                        ("open", "opening", "stuck", "tight", "budge", "loosen", "undo", "turn",
                         "wont open", "won't open", "cant open", "can't open", "cannot open",
                         "hard to open", "get the lid off", "lid off", "stubborn", "grip",
                         "wont come off", "will not come off", "wont go back on",
                         "will not go back on", "stuck shut")),
          _stuck_jar,
          # a storing question is the keeping row's, however it is worded: "how do i store an
          # open jar of jam" is not a stuck lid, and neither is "where do i keep it"
          avoid=("sterilise", "sterilize", "sterilising", "preserve", "preserving", "baby",
                 "babies", "formula", "teat", "mould", "mouldy", "mold", "moldy",
                 "keep", "keeps", "last", "lasts", "fridge", "how long", "how many", "how much",
                 "how big", "how full", "gone off", "store", "stored", "storing", "where",
                 "storage", "shelf life"),
          bias=2),
    # The bottle is often named by colour instead of by the word "wine": "an open bottle of
    # red", "an opened bottle of white". Those phrases keep it off a white sauce or a red
    # cabbage, which share the colour and none of the keeping.
    entry("open-wine", (("wine", "bottle of red", "bottle of white", "bottle of wine",
                         "red wine", "white wine", "rose wine"),
                        ("open", "opened", "bottle", "keep", "last", "how long",
                         "left over", "leftover", "vinegary", "gone off", "fridge")),
          ("An open bottle keeps 3 to 5 days: stopper it and keep it in the fridge, reds too, and "
           "take a red out an hour before you drink it. A vacuum stopper or a squirt of inert gas "
           "buys another day or two, and after that the wine is still fine for cooking - wine that "
           "has turned vinegary is a good vinegar."),
          # how to get the bottle open is not how long it keeps: "how do i open a wine bottle" was
          # this card, which answers a question about a bottle that is already open
          avoid=("how do i open", "how to open", "how can i open", "how do you open",
                 "how would i open", "ways to open", "get the cork out", "get it open",
                 "crack it open", "pop the cork", "uncork", "corkscrew", "screw cap",
                 "twist the cap"),
          ask=KEEP_ASK),
    # A wine that has gone flat is asked about as a fault in the glass, not as a keeping question:
    # "why does my wine taste flat" and "why does wine go flat" were the low-mood card ("do one
    # small thing you used to enjoy today") because "flat" is a mood word, and once the mood rows
    # stopped reading a thing's flatness they had no answer at all. It is one question about the
    # bottle that has been open a while, so it is the open-wine answer said as a why.
    entry("wine-gone-flat", (("wine", "bottle of red", "bottle of white", "bottle of wine",
                              "red wine", "white wine", "rose wine", "prosecco", "champagne",
                              "sparkling wine", "cava"),
                             ("flat", "taste flat", "tastes flat", "tasting flat", "gone flat",
                              "goes flat", "went flat", "tastes dull", "lost its fizz",
                              "no fizz", "not fizzy")),
          ("Flat means the fizz has gone, or - in a still wine - the fresh edge that made it "
           "worth drinking, because the gas and the aromas escape as soon as air gets in. A "
           "stopper and the fridge slow that to 3 to 5 days; a vacuum stopper or a squirt of "
           "inert gas buys a day or two more. Past that it is cooking wine, and wine that has "
           "turned vinegary is a good vinegar."),
          # how long a bottle keeps is open-wine's question, and it answers it with the numbers
          avoid=("still flat", "bottle flat", "flat tyre", "flat battery", "leftover",
                 "left over", "how long", "keep", "keeps", "last", "lasts", "still good",
                 "fridge", "store", "storing", "shop", "buy"),
          bias=1),
    # "which wine with dinner" is a choice, not a keeping question, so the second group is the
    # food or the deciding verb and the keeping words are held out - those belong to open-wine.
    entry("wine-with-food", (("wine", "red wine", "white wine", "rose wine"),
                             ("goes with", "go with", "pair", "pairs", "pairing", "match",
                              "choose", "pick", "which", "good", "buy", "recommend",
                              "dinner", "roast", "steak", "fish", "chicken", "curry", "pasta",
                              "cheese", "pudding", "dessert", "party", "meal", "serve")),
          ("Match the weight, not the colour: a light white with fish or chicken, a fuller red "
           "with red meat and stews, and rose or a light red in between. If you are guessing, a dry "
           "white or a medium red goes with nearly everything on a table, acidity cuts through fat, "
           "and a slightly sweet white is the safer bet with a hot curry. Serve reds a little cool "
           "and buy two bottles of one cheaper wine rather than one expensive one."),
          # keeping an open bottle, opening one without a corkscrew and a wine stain on the sofa
          # are three other rows, and a wine that is a gift is not a wine for dinner
          avoid=("open", "opened", "keep", "keeps", "last", "how long", "left over", "leftover",
                 "vinegary", "gone off", "fridge", "corkscrew", "opener", "stain", "stains",
                 "spill", "spilled", "spilt", "carpet", "sofa", "shirt", "gift", "present",
                 "freeze", "frozen", "vinegar", "alcohol free", "units", "pregnant",
                 # a drink that is good or bad for you is a health question, not a pairing one:
                 # "good" is in this key because "what white wine is good" is an ask about the
                 # bottle, so the health shapes have to be held out or every "is wine good for
                 # you" is answered with what to drink with dinner.
                 "good for you", "bad for you", "healthy", "health", "benefit", "benefits",
                 "calories", "safe",
                 # cooking with it, not drinking it: the wine is an ingredient in these
                 "cook", "cooking", "cooked", "recipe", "recipes", "oven", "bake", "sauce",
                 "stew", "marinate", "marinade", "risotto", "substitute", "instead of",
                 "reduce", "deglaze", "how much"),
          # "what wine with a curry" is asked more often than "how do i make a curry", and the
          # curry recipe won it on words alone. The pairing is the subject, so it goes first.
          bias=2),
    # "refreeze" is not in this key on purpose: it is refreeze-food's word, and sharing it
    # makes the word common enough that the refreezing answer loses its own line
    entry("freeze-food", (("freeze", "freezer", "freezing", "frozen"),
                          _FREEZE_FOOD_WORDS),
          _freeze_food,
          ask=KEEP_ASK,
          # soup and mash have their own, more specific freezing answer, and so does thawing
          avoid=("soup", "soups", "broth", "mashed potato", "mash", "refreeze", "refroze",
                 "re-freeze", "thawed", "already thawed", "freeze again", "defrost",
                 "defrosting", "defrosted",
                 "stew", "stews", "casserole", "casseroles", "curry", "curries", "chilli",
                 "chili", "bolognese", "lasagne", "lasagna", "leftover", "leftovers",
                 "left over",
                 # cooking something that is already frozen is a cooking question, not a freezing
                 # one: "how do i cook a frozen pizza" and "how do i cook frozen peas"
                 # and "can i use frozen spinach instead of fresh" is a substitution question: the
                 # person already has the frozen pack and wants to know if it will do
                 "instead", "instead of", "in place of", "substitute", "swap",
                 "how do i cook", "how long do i cook", "how to cook", "how do i reheat",
                 "how do i heat", "air fryer", "what temperature", "in the oven",
                 "from frozen", "slow cooker", "straight from frozen",
                 # a brain freeze is the headache from a cold mouthful, not a question about
                 # freezing food: "why do i get brain freeze when i eat ice cream" reached this
                 # entry on the words freeze and ice cream
                 "brain freeze", "brainfreeze", "ice cream headache") + _FREEZE_AVOID),
    entry("cake-time", ("cake", ("how long", "bake", "baking", "time", "oven")),
          # A bare "how long does it take?" is answered from this entry, so it carries the total
          # as well as the tin times: "about an hour and a half" is what people plan an afternoon
          # around, and the figure was only in the dish plan, which this answer displaces.
          "A 20cm sponge bakes at 180C (160C fan) for 25 to 30 minutes; a loaf tin needs 45 to 55. "
          "It's done when a skewer in the middle comes out clean, and it's worth checking 5 minutes "
          "early the first time. About an hour and a half start to finish, counting mixing and "
          "cooling.",
          # the keeping question is the cake plan's: "how long does cake last" was getting the
          # oven times, which reads like the answer and is not one
          avoid=("keep", "keeps", "keeping", "last", "lasts", "lasting", "stale", "fresh",
                 "store", "stored", "storing", "storage", "freeze", "fridge", "freezer",
                 "reheat", "leftover", "leftovers", "go off", "gone off")),
    entry("cake-plan", ("cake", ("birthday", "party", "celebrate", "celebrating")),
          "A two-layer chocolate or madeira sponge is the easy crowd-pleaser: bake it the day before, "
          "wrap it well and fill it with buttercream on the day. One 20cm tin serves 8 to 10 people "
          "generously.",
          # A birthday cake is an occasion bake, so it beats the plain oven-timings entry even
          # when the line asks how long: the plan says when to bake it and how many it serves.
          avoid=("how long", "time", "oven", "temperature"), bias=1),
    # "what can i bake for a birthday party" had no row of its own: the outfit entry answered it,
    # and the birthday cake plan needs the word "cake" in the line. A party bake is the tray of
    # things, so this row is keyed by the baking verb and the occasion.
    entry("party-bake", (("bake", "baking", "baked", "bakes", "make", "making"),
                         ("birthday", "birthday party", "party", "celebration", "christening",
                          "birthday tea", "party tea", "gathering", "friends coming",
                          "family coming")),
          ("For a birthday tea, a big chocolate or lemon traybake cut into squares is the easy "
           "one: one tin feeds 15 and you bake it the day before. Then a batch of fairy cakes, "
           "some jam tarts and a plate of sausage rolls, and the table is done.",
           "Bake a traybake the day before the party - chocolate or lemon, one tin feeds 15 in "
           "squares - then add fairy cakes, jam tarts and sausage rolls. That covers a birthday "
           "tea without any decorating."),
          # "how do i make it up to my mum" is a party bake only to the words: once the store has
          # put the subject back ("how do i make my mums birthday up to my mum") the row read it
          # as a bake still to plan, and the tray bake took a turn about putting something right
          # (bot/compose/repair.py, amends_to).
          guard=lambda reading: not amends_to(line_of(reading)),
          # A dinner party is a meal, not a bake, and "what should i cook for a dinner party" was
          # answered with the traybake when this row was first written.
          avoid=("how long", "temperature", "oven", "gas mark", "weigh", "store", "keep",
                 "freeze", "fridge", "speech", "present", "gift", "games", "decorate",
                 "decorations", "wear", "outfit", "invitations", "invites", "venue",
                 "dinner party", "dinner", "supper", "tea party", "meal", "main course",
                 "starter", "roast", "curry", "barbecue", "bbq",
                 # how much of a drink to make is a measure question, not a bake: "how much
                 # coffee should i make for a party" was answered with the traybake
                 "coffee", "wine", "beer", "lemonade", "squash", "punch", "cocktails",
                 # "how do i make conversation at a party" is the party's small-talk answer:
                 # "make" and "party" together are a bake for any line with a "make" in it.
                 # "what to say" and "strangers" reach the same small-talk answer from the
                 # other side, and a nervous guest is not a traybake either.
                 "conversation", "small talk", "mingle", "mingling", "nobody to talk",
                 "know anyone", "networking", "talk to people", "what to say", "talk about",
                 "nervous", "strangers"),
          bias=1),
    # "ideas for a birthday tea" was landing on the ten-minute-dinners row: a tea is not a
    # weeknight dinner, and the two words "birthday tea" on their own are too thin a key (3, under
    # the minimum), so the asking words carry the rest. A bare "party" is left out on purpose:
    # "ideas for a birthday party" is a party to plan and the planning row answers it.
    entry("tea-party-food", (("ideas", "idea", "suggest", "suggestions", "food", "serve",
                              "make", "making", "bake", "baking", "what shall i"),
                             ("birthday tea", "party tea", "christening tea", "afternoon tea",
                              "tea party", "tea for")),
          ("A birthday tea is sandwiches and cake, not a dinner: white bread with the crusts off, "
           "filled with ham, cheese or egg mayo, then sausage rolls, a plate of crisps, and a "
           "traybake or a Victoria sponge with fairy cakes for the children, or scones with jam "
           "and cream for an afternoon tea. Nothing needs serving hot, so it can be made that "
           "morning.",
           "Keep it to sandwiches, something savoury and cake: fill white bread with ham, cheese "
           "or egg mayo, add sausage rolls, then a big sponge or traybake and fairy cakes. A jug "
           "of squash and a pot of tea, and nothing has to be hot."),
          # A tea here is a party, so a plain "what should i cook for dinner" or a brew question
          # is not this row.
          avoid=("dinner", "supper", "roast", "curry", "meal", "cup of tea", "brew",
                 "caffeine", "green tea")),
    entry("cake-nut-free", ("cake", ("nut", "nuts", "allergy", "allergic", "allergies")),
          ("Go for a chocolate cake with no nuts at all: a plain chocolate sponge with cocoa and "
           "boiling water, iced with melted chocolate and cream. Check the chocolate and any "
           "ready-made icing for 'may contain nuts', and keep the worktop and tin clean if the "
           "allergy is serious.")),
    entry("sourdough-start", (("sourdough", "sourdough starter", "starter", "wild yeast"),
                              ("make", "making", "start", "starting", "begin", "create",
                               "from scratch", "grow", "first time", "recipe",
                               "keep it going")),
          "Stir 50g strong white flour and 50g water in a jar and leave it covered at room "
          "temperature. Every day throw half away and feed it the same 50g plus 50g. It bubbles "
          "within three to five days and is ready when it doubles in 4 to 6 hours, smells of "
          "yoghurt and tastes sour: 5 to 7 days in all. Rye or wholemeal flour starts faster; "
          "chlorinated tap water can slow it down.",
          # a car starter motor is the mechanic's question, not the baker's, and a starter that
          # is already going is the feeding question below rather than how to begin one
          avoid=("car", "engine", "motor", "ignition", "battery", "won't turn over",
                 "feed", "feeds", "feeding", "fed", "bubbling", "bubbles", "bubbly",
                 "smell", "smells", "acetone", "hooch", "alive", "dead", "rise", "rising")),
    # A starter is asked about by its own name, without the word sourdough: "my starter isnt
    # bubbling" and "should my starter smell of acetone" are the same question, and the plain
    # key answered neither ("my starter isnt bubbling" got a shrug and a search suggestion).
    entry("sourdough-feed", (("sourdough", "starter", "sourdough starter"),
                             ("feed", "fed", "bubbly", "bubbling", "bubbles", "alive", "rise",
                              "rising", "smell", "smells", "smelling", "acetone", "hooch",
                              # starting one is the same conversation as feeding one, and "how do
                              # i start a sourdough starter" was going to the job interview's
                              # "tell me about yourself" answer, which is what bare "starter" plus
                              # "how" scored.
                              "start", "starting", "begin", "beginning", "make", "making",
                              "create", "grow", "get going", "going", "from scratch",
                              # ready, waiting and waking are the same jarful: "how do i know my
                              # starter is ready" reached the job interview's ninety seconds, and
                              # "how do i wake up my starter" reached a punt. The two words that
                              # answer them are the state, not a verb.
                              "ready", "know", "wake", "wakes", "waking", "woke", "woken",
                              "wake up", "double", "doubles", "doubled", "doubling",
                              "look after", "care for")),
          "Feed a sourdough starter equal weights of flour and water, about its own weight, once a "
          "day at room temperature. To start one from nothing, mix 50g of wholemeal flour with 50g "
          "of water and feed it the same way every day - it takes about a week of that before it "
          "doubles reliably. It is ready to bake with when it doubles within 4 to 6 hours and "
          "smells of yoghurt rather than acetone.",
          # A car's starter motor is "going" and a starter is "fed", so bare "starter" plus
          # "going" or "start" reached this answer: "my starter motor is going" was told to feed
          # it equal weights of flour and water. The vehicle words are the whole of the fix - the
          # key itself has to stay wide enough for "how do i start a sourdough starter".
          avoid=("name", "called", "call", "ideas", "mould", "mouldy", "mold", "moldy",
                 "motor", "motors", "engine", "engines", "car", "cars", "van", "van's",
                 "battery", "lawnmower", "lawn mower", "motorbike", "motorcycle", "scooter",
                 "tool", "tools", "solenoid", "ignition", "alternator")),
    # The baking faults that came back as a shrug or a "Noted!". Each is keyed on the thing that
    # went wrong and the bake it went wrong in, so a line about a cake does not reach the biscuit
    # answer and a line about the oven does not reach any of them.
    # A sugar fault belongs to the sweet it is in: an icing is sifted and beaten, a fudge is
    # warmed with milk and beaten, a caramel is melted back with a spoonful of water. Chocolate is
    # not here, because a grainy chocolate is a seized one and that answer already exists.
    entry("sugar-grainy", (_GRAIN_FOOD, _GRAIN_WORD),
          _grainy,
          avoid=("chocolate", "choc", "honey", "maple", "bread", "cake", "biscuit", "cookie",
                 "meat", "chicken", "beef", "pork", "rice", "pasta", "potato", "potatoes")),
    entry("sugar-work", (("sugar", "sugars", "caramel", "toffee", "fudge", "praline",
                          "brittle", "syrup", "candy"),
                         ("dissolve", "dissolves", "dissolved", "dissolving", "dissolv",
                          "melt", "melts", "melting", "melted", "crystallise", "crystallised",
                          "crystallising", "crystallize", "crystallized", "crystalise",
                          "crystalised", "crystals", "grainy", "grain", "clear", "syrup",
                          "caramel", "caramelise", "caramelize", "toffee", "brittle", "boiling",
                          "bitter", "burnt", "stir", "stirring", "make", "making", "made",
                          "hard", "hardened", "hardens", "block", "solid", "lumps", "lumpy",
                          "soften", "softens", "softening")),
          _sugar_work,
          # "how do i dissolve sugar in water" and "why does my caramel crystallise" were both
          # answered by the row about eating less sugar, which reads "how do i" plus "sugar" as
          # a question about the diet. A line that names a way of working it wants the pan.
          bias=1,
          # The amount of sugar in a food and the health of eating it are other entries.
          avoid=("how much sugar", "calories", "calorie", "diabetes", "diabetic",
                 # A grainy fudge or a crystallised caramel is `sugar-grainy`'s question: it
                 # knows the rescue for that sweet, and this is about working the sugar itself.
                 "grainy", "grain", "gritty", "granular", "sandy", "crunchy",
                 # Baking with sugar is a recipe, not a pan of syrup.
                 "cake", "cakes", "biscuit", "biscuits", "cookie", "cookies", "bread",
                 "sugar free", "free",
                 "diet", "blood sugar", "hyper", "children", "child", "kids", "kid", "toddler",
                 "baby", "tooth", "teeth", "addicted", "addiction", "quit", "give up", "eat less",
                 "cut down", "cravings", "chocolate", "choc", "honey", "maple",
                 # what sugar does to the body is the health rows' question
                 "fat", "fatter", "fattening", "weight", "lose weight", "gain weight",
                 "healthy", "unhealthy", "bad for", "good for", "addictive", "energy",
                 "sleepy", "hyperactive", "mood", "skin", "acne",
                 "icing", "frosting", "buttercream", "fondant", "dog", "dogs", "cat", "cats",
                 "puppy", "kitten")),
    entry("chocolate-seize", (("chocolate", "choc"),
                              ("seize", "seized", "seizing", "melt", "melting", "melted", "grainy",
                               "dip", "dipped", "dipping", "strawberry", "strawberries", "fruit",
                               "stiff", "thick", "lumpy", "bloom", "white", "grey", "gray",
                               "streak", "streaks", "temper", "tempering", "microwave", "water bath",
                               "bain marie")),
          _chocolate),
    # The baking faults that came back as a shrug: a crack, a weep, a shrink, a mixture that
    # split. One entry, because the fault and the bake together are what pick the fix.
    entry("bake-fault", (_BAKE_THING, _BAKE_FAULT),
          _bake_fault,
          # a cheesecake that is not cooked through is a keep question, and a pastry case has its
          # own answers for a soggy or a shrinking lining
          avoid=("keep", "freeze", "fridge", "how long", "recipe", "how do i make"),
          bias=1),
    entry("cookie-spread", (("cookie", "cookies", "biscuit", "biscuits", "shortbread"),
                            ("spread", "spreading", "flat", "thin", "melt", "melted", "run",
                             "running", "wide", "squash", "pool", "grease", "greasy")),
          _cookies),
    entry("biscuit-hard", (("biscuit", "biscuits", "cookie", "cookies", "shortbread", "scone",
                            "scones"),
                           ("hard", "harder", "tough", "rock", "rocky", "dry", "stale", "brittle",
                            "snap", "breaks")),
          "Hard biscuits are usually baked a couple of minutes too long or worked too much: pull "
          "them out while the middles still look slightly soft, because they firm as they cool, "
          "and mix just until the flour is in. More butter or an extra yolk keeps them short, and "
          "a slice of bread in the tin softens them overnight.",
          # a scone that is dry or tough is answered by the scone recipe itself, which names the
          # cold butter, the one fold and the 220C, and that is the whole of a scone's fault. Once
          # scones had a plan row of their own this entry started winning those lines and said
          # "hard biscuits" about a scone.
          avoid=("scone is dry", "scone is tough", "scone is chewy", "scones are dry",
                 "scones are tough", "scones are chewy", "scone too dry", "scones too dry",
                 "scones dry", "scone dry", "scones tough", "scone tough", "scones chewy",
                 "scone chewy", "scones came out dry", "scones went dry", "scones were too dry",
                 "scone was too dry", "scones are too dry", "scone is too dry")),
    entry("biscuit-crumble", (("biscuit", "biscuits", "cookie", "cookies", "shortbread", "scone",
                               "scones"),
                              ("crumbly", "crumbles", "crumble", "crumbs", "falling apart",
                               "falls apart", "fell apart", "sandy")),
          "Crumbly biscuits have too little fat or too much flour, and the dough was worked too "
          "long: weigh the butter properly, rub it in until it looks like breadcrumbs, and stop "
          "mixing the moment it comes together. Let them cool on the tray, because they are "
          "fragile while hot, and handle the dough as little as you can."),
    entry("jam-make",
          (("jam", "marmalade", "chutney", "preserve", "preserves", "fruit cheese"),
           ("make", "making", "homemade", "from scratch", "my own", "recipe", "sugar",
            "how do i start", "what fruit")),
          lambda memory, understood: _jam_make(understood),
          # a jam that will not set, a jar to sterilise and a jar to keep are three other
          # answers, and every one of them names jam too
          avoid=("set", "setting", "sets", "runny", "too thin", "firm", "pectin", "sterilise",
                 "sterilize", "sterilising", "jar", "jars", "store", "storing", "keep",
                 "keeping", "mouldy", "mould", "freeze", "frozen", "how long") + NO_SUGAR),
    entry("bake-always", (("baking", "bake", "bakes", "baked", "everything i bake", "all my bakes",
                           "my cakes", "my loaves", "my bakes", "when i bake", "whatever i bake"),
                          # The second signal is that the fault *always* happens. "comes out" and
                          # "turns out" are how any single bake is described, so carrying them here
                          # let this row take a named bake's fault from the row that knows it: "my
                          # loaves are coming out flat" and "my cakes come out flat" were told to
                          # check the baking powder is in date, while the very same lines said with
                          # "the bread"/"the rolls" reached the bread row. A pattern across bakes
                          # is what this row answers, and a pattern is said with one of these.
                          ("always", "never", "every time", "every single time", "each time",
                           "no matter what", "whatever i do", "always comes", "always come",
                           "always does", "never comes", "never come",
                           # the always-ness is also said about the whole batch rather than with a
                           # frequency word: "everything i bake comes out dry", "whatever i bake
                           # comes out flat", "all my bakes come out dry"
                           "everything i bake", "whatever i bake", "all my bakes", "when i bake")),
          _bake_always,
          avoid=("how long", "keep", "keeps", "freeze", "fridge", "recipe", "how do i make",
                 "buy", "shop", "calories", "healthy", "what temperature", "how hot"),
          bias=1),
    entry("bake-keep-follow", (_BAKE_KEEP_SHAPES,
                               ("it", "they", "them", "keep", "last", "long", "days", "freeze")),
          _bake_keep, bias=1),
    entry("bake-follow", (_BAKE_FOLLOW_SHAPES,
                          ("i", "it", "that", "them", "they", "wrong", "happen", "again", "stop",
                           "use", "eat", "ok", "differently", "else", "right", "fix", "next")),
          _bake_follow,
          avoid=("keep", "keeps", "last", "lasts", "fridge", "freeze", "reheat", "reheat",
                 "how long",
                 "toast", "toastie", "toasties"),
          bias=1),
    entry("jam-set", (("jam", "jelly", "marmalade", "chutney"),
                      ("set", "setting", "runny", "thin", "firm", "setter", "pectin", "test",
                       "plate", "wrinkle", "sugar", "how long", "boil")),
          "Jam sets at 104 to 105C, so boil it hard for 10 to 15 minutes and test a drop on a cold "
          "plate: push it with a finger, and if it wrinkles it is ready. Jam that stays runny has "
          "had too little sugar or too little pectin - add a handful of gooseberries or a squeeze "
          "of lemon and boil it again."),
    entry("jar-sterilise", (("jar", "jars", "bottle", "bottles"),
                            ("sterilise", "sterilize", "sterilising", "sterilizing", "clean",
                             "cleaning", "wash", "washing", "scald", "preserve", "preserving",
                             "jam", "chutney")),
          "Wash the jars in hot soapy water, rinse them, and stand them upside down in an oven at "
          "120C for 15 minutes; fill them while they are still hot. Lids go in a bowl of boiling "
          "water for a minute, and a dishwasher on its hottest cycle does the same job.",
          # A baby's bottle is not a jam jar, and a jar that has gone mouldy is a mould question,
          # so both are left to whoever answers them properly. Neither is a water bottle, a flask
          # or a thermos: "how do i wash my water bottle" has nothing to do with preserving, and the
          # sterilising answer would be wrong for it.
          avoid=("baby", "babies", "formula", "teat", "teats", "feeding", "mould", "mouldy",
                 "mold", "moldy", "water bottle", "water bottles", "gym bottle", "sports bottle",
                 "drink bottle", "drinking bottle", "flask", "thermos", "hot water bottle",
                 "bottle of water", "reusable")),
    # Ties are broken by which row was registered first, and the keeping row above comes first,
    # so this one carries a bias: it is the answer to every "soften / soften quickly / too hard to
    # spread" line, and the bias also puts it in front of the bedroom temperature row, which read
    # "how do i get butter to room temperature" as a question about sleeping.
    entry("butter-soften", ("butter", ("soften", "soft", "room temperature", "quick", "hard",
                                       "hard to spread", "spread", "spreading")),
          "Cut cold butter into small cubes and leave it 15 minutes, or grate it; both soften it "
          "fast without melting it. Don't microwave it, because butter that's too warm splits a "
          "cake mix.",
          bias=2,
          # A keeping question that mentions room temperature is the row above's, so this one
          # turns those lines down rather than take them on the room-temperature word alone.
          avoid=("how long", "keep", "keeps", "keeping", "last", "lasts", "still good",
                 "gone off", "go off", "shelf life", "fridge", "freeze", "frozen", "out of the fridge",
                 "safe to leave out", "leave out")),
    # The commonest swaps, keyed by the thing that is missing. Each one is asked both ways
    # round ("what can i use instead of buttermilk", "i ran out of milk, what can i use") and
    # both carry a way of asking for a stand-in, so the ingredient alone still reaches the entry
    # that is about it.
    _swap("swap-buttermilk", (("buttermilk",), _SWAP_ASK),
          "For 250ml of buttermilk: 250ml of milk with a tablespoon of lemon juice or white "
          "vinegar, left 10 minutes to thicken. Plain yoghurt thinned with milk works too, and so "
          "does sour cream loosened with a splash of milk."),
    _swap("swap-cream", (("cream", "sour cream", "double cream", "single cream", "creme fraiche"),
                         _SWAP_ASK),
          "For cooking: milk with a knob of butter and a teaspoon of cornflour thickens much like "
          "cream. Cold, or on the side: plain yoghurt, sour cream or creme fraiche. Stir those in "
          "off the heat, because cream and yoghurt split if they boil."),
    _swap("swap-eggs", (("egg", "eggs"), _SWAP_ASK),
          "In cakes and biscuits, one egg becomes 60g of yoghurt, half a mashed banana, or a "
          "tablespoon of ground flax or chia stirred into 3 tablespoons of water and left 10 "
          "minutes. Those bind but do not lift, so add half a teaspoon of baking powder. For "
          "glazing or binding mince, a little milk or oil does the job.",
          # A quiche, a tart and a custard are set by the eggs themselves, not held together by
          # them, so 60g of yoghurt is the wrong fact for those: "can i make a quiche without
          # eggs" was answered with the cake rule. The set dishes have their own row below.
          avoid=("quiche", "quiches", "tart", "tarts", "flan", "flans", "frittata",
                 "frittatas", "custard", "creme anglaise", "pastry cream", "custard tart")),
    # The set dishes, where the egg is the structure rather than the glue. Kept apart from the
    # swap rows above because the honest answer is a different dish, not a substitute.
    entry("no-eggs-in-a-set-custard",
          (("quiche", "quiches", "tart", "tarts", "flan", "flans", "frittata", "frittatas",
            "custard tart", "egg custard"),
           ("without eggs", "without egg", "no eggs", "no egg", "egg free", "egg-free",
            "eggless", "out of eggs", "ran out of eggs", "run out of eggs", "no eggs left",
            "cant eat eggs", "can't eat eggs", "allergic to eggs", "egg allergy",
            "instead of eggs", "replace the eggs", "replace eggs", "swap the eggs")),
          "A quiche is set by its eggs, so leaving them out gives you warm vegetables in a "
          "pastry case rather than a quiche. The nearest thing is 300g of silken tofu blended "
          "smooth with a tablespoon of cornflour, or 100g of chickpea flour whisked with 250ml "
          "of water and a spoon of oil for a firmer, nuttier set: bake either at 180C for 30 to "
          "35 minutes, until the middle still wobbles. If the reason is an allergy, read the "
          "pastry label too, because some shortcrust has egg in it.",
          bias=2),
    # Nobody is taught this and everybody guesses: "how do i drain a can of tuna" was answered
    # with the drain-cleaning card (a kettle of boiling water down the plughole). A tin is a
    # lid, a press and a bowl if the liquid is worth keeping.
    entry("drain-a-tin",
          (("tin", "tins", "can", "cans", "tinned", "canned", "can of", "tin of"),
           ("drain", "draining", "drained", "strain", "straining", "get the water out",
            "get the oil out", "water out", "oil out", "brine", "juice", "liquid")),
          "Open the tin most of the way, hold the lid down with your thumb and tip it over the "
          "sink with a gap of about a centimetre, so the liquid runs out and the food stays in. "
          "Pressing the lid flat and squeezing is tidier still, and the lid laid over a bowl "
          "makes a strainer if you want to keep the oil or brine for a dressing. Tuna in water "
          "wants a good press before the mayo; chickpeas and sweetcorn want a rinse as well.",
          avoid=("drain outside", "drain cover", "manhole", "gully", "gutter", "downpipe",
                 "plughole", "sink", "shower", "bath", "blocked", "smell", "smells", "boiling "
                 "water", "bicarbonate", "vinegar", "battery", "phone", "laptop", "pond",
                 # a tin of pulses already has the answer that matters - "drain them, rinse the
                 # salty water off" - and it says more about them than a strainer can, so this
                 # row leaves chickpeas, beans and lentils to `pulses-tinned`
                 "chickpeas", "chick peas", "beans", "bean", "lentils", "lentil", "pulses"),
          bias=1),
    _swap("swap-butter", (("butter",), _SWAP_ASK),
          "In cakes and biscuits, margarine at the same weight, or a neutral oil at about "
          "three-quarters of the weight. For frying and greasing, any oil will do. Do not swap the "
          "butter in pastry, shortbread or buttercream, where its taste is the whole point."),
    # Butter that separates in the pan is a heat problem, not a swap: "my melted butter split"
    # and "how do i melt butter without it splitting" were answered with the stand-in card, and
    # nothing else answered them at all. Keyed on butter plus the fault, so a cake that needs
    # less butter and a butter that goes rancid keep the rows that own them.
    entry("butter-splits-when-melted", (("butter", "butters"),
                                        ("melt", "melts", "melted", "melting", "split",
                                         "splits", "splitting", "separated", "separates",
                                         "seized", "grainy", "oily")),
          "Melt it on the lowest heat, in small pieces, and take the pan off as soon as most of it "
          "has gone - the rest melts in the warm pan. Butter splits when it gets too hot, because "
          "the milk solids cook and squeeze the fat out and it goes grainy and oily: a split "
          "batch comes back if you let it cool a little and whisk in a teaspoon of cold water, "
          "and simply warming it again will not fix it.",
          avoid=("instead", "substitute", "swap", "replace", "alternative", "ran out",
                 "run out", "dont have", "don't have", "havent got", "haven't got",
                 "how long", "keep", "keeps", "fridge", "freeze", "frozen", "gone off",
                 "rancid", "no butter", "without butter", "dairy free", "vegan",
                 # a sauce that splits is a sauce question, and the sauce card says what to whisk
                 # in: "the butter sauce split" is the sauce's own fault, not a pan of butter
                 "sauce", "sauces", "hollandaise", "beurre blanc", "cake", "cakes", "pastry",
                 "shortbread", "biscuits", "frosting", "buttercream", "cookie", "cookies",
                 "toast", "sandwich", "scones", "crumbs", "mould", "mold")),
    # Three more things people run out of mid-recipe, in the same shape as the rows above:
    # "no soya sauce what can i use" and "no breadcrumbs" were shrugs, and "no mayonnaise what
    # can i use in a sandwich" reached the take-it-or-leave-it row.
    entry("swap-soy-sauce-shortage", (("soy sauce", "soya sauce", "soy", "soya", "no soy sauce",
                              "no soya sauce"), _SWAP_ASK),
          "Salt is the honest swap: about a quarter teaspoon of salt for each tablespoon of soy "
          "sauce, with a splash of water so the dish does not dry out. Tamari is the same thing "
          "without the wheat, and in a marinade a teaspoon of balsamic or Worcestershire sauce "
          "brings back the dark savoury note."),
    entry("swap-breadcrumbs-shortage", (("breadcrumbs", "bread crumbs", "breadcrumb", "no breadcrumbs"),
                               _SWAP_ASK),
          "Blitz stale bread, or crush crackers, cornflakes or oatcakes in a bag with a rolling "
          "pin. A crumble or a gratin topping takes porridge oats or crushed crisps, and for "
          "binding mince or meatballs a slice of bread soaked in a little milk is the classic."),
    entry("swap-mayonnaise-shortage", (("mayonnaise", "mayo", "no mayonnaise"), _SWAP_ASK),
          "Plain yoghurt or sour cream for a dip or a dressing, loosened with a spoon of water "
          "or lemon, and hummus, butter or mashed avocado in a sandwich. To make it from scratch: "
          "one egg yolk with a teaspoon of mustard, then 150ml of oil added drop by drop while "
          "you whisk, and a squeeze of lemon at the end."),
    _swap("swap-milk", (("milk",), _SWAP_ASK),
          "In cakes, scones and pancakes: water plus a knob of butter, or two tablespoons of milk "
          "powder stirred into the water. Any unsweetened plant milk works too. In a savoury sauce "
          "or mash, stock or the pasta water tastes better than plain water."),
    _swap("swap-yoghurt", (("yoghurt", "yogurt"), _SWAP_ASK),
          "In marinades and dressings: sour cream, creme fraiche or buttermilk. In baking: milk "
          "with a teaspoon of lemon juice, left 10 minutes. In a curry, stir any of them in off "
          "the heat, or they split into grains."),
    # The raising agent has one row, further down: the older `swap-baking-powder` here answered
    # the swap alone with the same bicarbonate line and left "i havent got any baking powder" to a
    # "noted". Both rows carried the id, so the later copy was a duplicate that no test could see
    # going stale - `tests.test_knowledge_load` names it. Removed, and the row below covers both
    # asks.
    # There is no stand-in for yeast, so the answer is the bread that needs none: that is what a
    # person asking mid-recipe wants, not a lecture on what yeast does.
    entry("swap-cornflour", (("cornflour", "corn starch", "cornstarch"), _SWAP_ASK),
          "Plain flour at twice the amount, whisked into cold liquid before it goes in, or "
          "arrowroot at the same amount. Simmer a minute afterwards, but do not boil a cornflour "
          "sauce hard, because it thins out again."),
    # Two things a cook runs out of that the table above does not cover, and both were a shrug:
    # "no lemons, what can i use" and "what can i use instead of wine in a risotto". The lemon is
    # asked for its juice and for its zest, which are two different swaps, so the answer says both.
    entry("swap-lemon", (("lemon", "lemons", "lime", "limes"), _SWAP_ASK),
          "For the juice: lime is the nearest, or white wine vinegar or cider vinegar at half the "
          "amount, or a splash of orange juice if the dish is sweet anyway. For the zest: lime or "
          "orange zest, or a few drops of lemon essence. Where the lemon is the whole point - "
          "lemon drizzle, hollandaise, a lemon tart - a bottle of juice does the job, and nothing "
          "else does."),
    entry("swap-wine", (("wine", "white wine", "red wine", "vermouth", "sherry", "marsala"),
                        _SWAP_ASK),
          "Leave the wine out and use the same amount of hot stock, plus a squeeze of lemon or a "
          "teaspoon of white wine vinegar so it still tastes bright. A splash of dry vermouth or "
          "dry sherry is the closest thing to the wine itself, so half wine and half stock is a "
          "good way back. In a risotto, add the stock a ladle at a time either way, and taste for "
          "salt at the end."),
    # A staple that has run out is the same question as a swap for an ingredient, and it was the
    # one shape the table above did not hold: the stalls are keyed on the ingredient (butter, milk,
    # eggs) and a staple was never one. "im out of rice", "we are out of rice" and "no potatoes
    # left" were a shrug from the composer, because the freshness row (which used to take them
    # with the bin-it card) stands down and nothing else says what stands in. The staples answer
    # each other, because any of them carries the same sauce; what each entry refuses is the dish
    # that is the staple itself.
    entry("swap-rice-shortage", (("rice", "basmati rice", "long grain rice"), _SHORTAGE_ASK),
          "No rice under a curry or a stew: pasta, couscous, bulgur or a baked potato do the same "
          "job, drained and buttered the same way, and a tin of chickpeas or a handful of extra "
          "vegetables fills the plate if there is less of any of them than you thought. Keep the "
          "portion the same - 75 to 100g dry a person. Risotto, paella and egg fried rice want "
          "rice itself, so cook something else instead of swapping them.",
          # a portion, a cooking time and a keeping question are other entries' lines, and a rice
          # dish that names its own rice is the dish's
          # a portion, a cooking time and a keeping question are other entries' lines, and a dish
          # that is named after the rice is the dish's: "how do i make rice pudding" and "how do i
          # cook paella rice" were both the plain method before those entries existed.
          avoid=_STAPLE_METHOD_AVOID + (
                 "per person", "keep", "keeps", "freeze",
                 "reheat", "leftover", "leftovers", "risotto", "paella", "rice pudding",
                 "rice cooker", "brown rice", "white rice", "sushi rice", "cauliflower rice",
                 "rice bowl", "rice krispie", "rice balls", "carbs", "calories")),
    entry("swap-pasta-shortage", (("pasta", "spaghetti", "noodles", "macaroni"), _SHORTAGE_ASK),
          "No pasta: rice, potatoes or couscous under the same sauce, and a layer of sliced potato "
          "does the job of lasagne sheets in a bake. Keep the sauce as it was - it is the part "
          "that carries the meal - and the same weight of whatever you use, 75 to 100g dry a "
          "person.",
          avoid=_STAPLE_METHOD_AVOID + (
                 "per person", "keep", "keeps", "freeze",
                 "reheat", "leftover", "leftovers", "lasagne", "salad", "carbs",
                 "calories")),
    entry("swap-potatoes", (("potatoes", "potato", "spuds", "spud"), _SHORTAGE_ASK),
          "No potatoes: pasta, rice or couscous beside the same dinner, and if it is mash that is "
          "wanted, parsnip, celeriac or butter beans mash much the same once they are soft, with "
          "butter and a little of the cooking water. Roast potatoes really do want potatoes - "
          "nothing else crisps that way - so roast carrots, squash or onions instead.",
          # the dishes made of potatoes are theirs - wedges, chips, a gratin, a salad, a jacket -
          # and a shortage line never names one of them
          avoid=_STAPLE_METHOD_AVOID + (
                 "per person", "keep", "keeps", "freeze",
                 "reheat", "leftover", "leftovers", "sweet potato", "mashed potato", "mash",
                 "potato salad", "potato gratin", "gratin", "wedges", "chips",
                 "jacket", "crisps", "dauphinoise", "carbs", "calories")),
    # The same question for the three things a bake cannot go ahead without, keyed by what has
    # run out: "i havent got any baking powder" was a "noted", "no yeast what do i do" a hedge, and
    # "what can i use instead of plain flour" a "rather not guess". The swap entries above cover
    # butter, eggs, milk and cream; these are the raising agent and the flour.
    entry("swap-baking-powder", (("baking powder", "raising agent", "no baking powder",
                                  "without baking powder"), _SWAP_ASK + _OUT_ASK),
          "A teaspoon of baking powder is a quarter teaspoon of bicarbonate of soda plus half a "
          "teaspoon of cream of tartar. Without the cream of tartar, use the quarter teaspoon of "
          "bicarbonate and swap a spoonful of the liquid for lemon juice, vinegar or buttermilk, "
          "because bicarbonate needs an acid to work. Self-raising flour already carries it - "
          "about 2 teaspoons in every 150g - so a self-raising recipe needs none at all.",
          # "what is the difference between baking soda and baking powder" is the comparison
          # entry's question, and a sourdough starter is a different problem again.
          avoid=("difference", "different", "vs", "how much", "how many", "sourdough", "starter",
                 "soda bread", "bicarbonate of soda in")),
    entry("swap-plain-flour", (("plain flour", "all-purpose flour", "all purpose flour",
                                "no plain flour", "no flour left"),
                               _SWAP_ASK + _OUT_ASK),
          "Instead of plain flour, self-raising is the usual stand-in: use it at the same weight "
          "and leave out the baking powder the recipe asks for, or add a teaspoon less. Bread "
          "flour works in cakes and scones too but drinks more liquid, so add it a spoonful at a "
          "time. For thickening a sauce, cornflour at half the amount does the job better."),
    entry("swap-yeast", (("yeast", "no yeast"), _SWAP_ASK + _OUT_ASK),
          "Without yeast, bread needs a different kind of rise: a soda bread with bicarbonate of "
          "soda and buttermilk, or flatbreads and rotis, which need no rising at all. For a pizza "
          "or a focaccia today, half a teaspoon of bicarbonate and a teaspoon of lemon juice to "
          "300g of flour will puff it in a hot oven instead."),
    entry("vegan-baking", (("vegan", "vegans", "plant based", "plant-based", "eggless", "egg free",
                            "egg-free", "dairy free", "dairy-free"),
                           ("cake", "sponge", "biscuit", "biscuits", "cookie", "cookies", "scone",
                            "scones", "muffin", "muffins", "brownie", "brownies", "pancake",
                            "pancakes", "bake", "baking", "loaf", "bread", "flapjack",
                            "flapjacks", "blondie", "blondies", "oat bar", "oat bars", "pastry",
                            "shortcrust", "pie", "pie crust", "tart", "tarts", "tart case",
                            "quiche", "flan", "crumble", "crumbles", "brioche", "challah")),
          _vegan_bake,
          # whether it is good for you is a different question from how to make it
          avoid=("healthy", "healthier", "healthily", "unhealthy", "calories", "fattening",
                 "good for you", "bad for you"),
          bias=1),
    entry("self-raising", (("plain flour", "all-purpose flour", "flour"), ("self-raising",
                                                                        "self raising",
                                                                        "substitute", "baking powder")),
          "To make self-raising flour, add 2 level teaspoons of baking powder to every 150g of "
          "plain flour, plus a pinch of salt. Mix it well before using it, or some bakes rise more "
          "than others."),

    # --- sauces, seasoning, fixing a dish -----------------------------------
    # Two more faults in the "a dish that came out wrong" family above, in the same shape: the
    # words that name the fault plus one of the _FOOD words, bias=1 so naming the fault wins.
    entry("fix-sweet", (("sweet", "sugary", "too much sugar", "over sweet"),
                        _FOOD),
          "Balance it with salt and acid rather than more of anything sweet: a pinch of salt, a "
          "squeeze of lemon or a spoon of vinegar, and a little more of whatever the dish is built "
          "on - flour, cream, yoghurt, tinned tomatoes. For a cake that is already baked, serve it "
          "with unsweetened cream or fruit, and cut the sugar by a quarter next time: most recipes "
          "take it.",
          avoid=("potato", "potatoes", "wine", "cider", "beer", "perfume", "smell", "smells",
                 "voice", "music", "dream", "dreams", "tooth", "teeth", "sherry",
                 # "sweet and sour" is a dish, not a fault
                 "sweet and sour", "sour and sweet"),
          bias=1),
    entry("fix-sour", (("sour", "acidic", "too much lemon", "too much vinegar", "vinegary",
                        "too sharp"),
                       _FOOD),
          "Take the edge off with fat and sweetness rather than more of anything sour: a knob of "
          "butter or a spoon of cream, a pinch of sugar, or a little bicarbonate of soda on the "
          "tip of a knife for a tomato sauce. If it is a stew or a curry, ten more minutes of "
          "simmering with the lid off softens the acid; if it is a salad dressing, add oil rather "
          "than more honey.",
          avoid=("milk", "cream", "yoghurt", "yogurt", "off", "gone off", "date", "wine", "cider",
                 "beer", "stomach", "breath", "mood",
                 # a drink that tastes sour is a brewing question (measures.py's coffee-taste),
                 # not a dish to rescue with butter. The fault is said about the drink, so the
                 # phrases go in, not the bare words: "my coffee cake tastes sour" is a cake.
                 "coffee tastes", "coffee taste", "coffee that tastes", "coffee is sour",
                 "espresso tastes", "espresso is sour", "tea tastes", "tea taste",
                 "tea that tastes", "tea is sour",
                 # a sour taste in the mouth is a body question, not a cooking one
                 "mouth", "tongue", "sick", "vomit",
                 # "sweet and sour" is a dish, not a fault
                 "sweet and sour", "sour and sweet",
                 # a sour cup is a brewing fault with its own answer - the grind, the water and
                 # the time - not a pan of food to be balanced with cream. The phrases go in, not
                 # the bare words: "my coffee cake tastes sour" is a cake, and it belongs here.
                 "coffee tastes", "coffee taste", "coffee that tastes", "coffee is sour",
                 "coffee is bitter", "espresso tastes", "espresso is sour", "latte tastes",
                 "cup of coffee taste", "tea tastes", "tea is bitter", "tea taste"),
          bias=1),
    entry("chilli-heat", (("chilli", "chili", "curry", "spicy", "spice"),
                          ("too hot", "too spicy", "too much", "cool", "milk", "hot", "mild",
                           "less", "milder", "yoghurt")),
          "To cool a dish that's too hot, stir in yoghurt, cream or coconut milk at the end, or "
          "serve it with rice and something dairy on the side. Water doesn't help; a little sugar "
          "and lemon balances the heat without hiding it.",
          # "i made too much chilli" is a pot that overflowed, not a dish that is too hot: the
          # quantities are one key part here ("too much"), so a surplus of a made dish matched and
          # got advice about cooling the heat. The surplus is `made-too-much`'s line.
          avoid=("made too much", "cooked too much", "make too much", "cook too much",
                 "made far too much", "left over", "leftover", "leftovers", "freeze",
                 "freezer")),
    # "how do i deseed a chilli" reached the chilli con carne recipe: a dish and a vegetable are
    # one word, and the dish carries a whole method that never mentions the seeds. The seeds and
    # the white pith are most of the heat, so seeding a chilli is its own answer.
    entry("chilli-prep", (("chilli", "chillies", "chillis", "chili"),
                          ("deseed", "de-seed", "de seed", "seed", "seeds", "pith")),
          "Cut the chilli in half lengthways and scrape out the seeds and the white pith with a "
          "teaspoon or the tip of a knife: nearly all the heat sits there, so a chilli with them "
          "out is mild and the flesh left behind still tastes of chilli. Wash your hands straight "
          "after and keep them off your eyes; leave the seeds in when you want the heat.",
          # a dish made with chilli, a chilli that is too hot to eat and a chilli to grow are
          # three other answers: the first is a recipe, the second is what to do with the heat,
          # and the third is the garden's.
          avoid=("con carne", "recipe", "sauce", "soup", "stew", "curry", "dish", "dinner",
                 "too hot", "too spicy", "cool it down", "mild", "milder", "less hot",
                 "grow", "plant", "seedling", "seeds to sow", "sow", "dry", "drying",
                 "freeze", "store", "keep", "buy")),
    entry("curry-split", (("curry", "sauce", "gravy", "hollandaise", "mayonnaise", "mayo",
                           "bearnaise", "béarnaise", "custard", "custards", "creme anglaise",
                           "crème anglaise", "creme patissiere", "crème pâtissière",
                           "pastry cream", "custard tart", "custard tarts", "custard filling",
                           "creme caramel", "crème caramel"),
                          # "fix", "save" and "rescue" are in nearly every fault question ("can i
                          # save it"), so they pulled burnt sauces here; the fault word does the work.
                          ("split", "splits", "splitting", "curdled", "curdle", "curdling", "grainy",
                           "seized")),
          _split,
          # "i burnt the sauce, can i save it" is the burnt-pan answer, not a split one
          avoid=("burnt", "burn", "burnt on", "scorched", "caught")),
    entry("soup-thick", (("soup", "stew", "casserole", "stews", "casseroles", "curry",
                          "curries", "sauce"),
                         ("thicken", "thick", "thicker", "thickens", "thicken it",
                          "thickens it", "watery", "runny", "thin", "too thin", "too watery",
                          "make soup thicker", "make my soup thicker", "make a thicker soup",
                          "make it thicker", "thicker soup",
                          # The same ask without the "-er", which is how most people say it: "how
                          # do i make soup thick" was handed the whole soup method, because the
                          # recipe table's "make soup" is a phrase and this row's "thick" was one
                          # word. `_make_it` writes the phrase out for this row's own subjects.
                          *MAKE_IT_THICK,
                          # the other direction, written the ways people write it: "thinner",
                          # "thin it down". The reply itself comes from `_body`, which reads
                          # which way the pot is wrong.
                          "thinner", "thin down", "thin it", "make it thinner",
                          "make my soup thinner", "soup thinner", "less thick",
                          # a pot that is stodgy, claggy or gluey is the same complaint as one
                          # that is too thick, and _body already reads those words as "too thick"
                          "stodgy", "stodge", "claggy", "gluey")),
          _body,
          # "thicken" is shared with gravy-lumpy now and a shared word scores lower for both, so
          # the "thicken it" wording carries the weight here. A bias would have taken the stew and
          # curry lines off fix-watery as well, and those want the tomato puree answer.
          # "make soup thicker" is written out as a phrase: the recipe table has "make soup" and a
          # phrase outranks a single word, so the written-out lines were handed the whole soup
          # recipe. The phrase wins them back without touching the stew and curry complaints.
          ),
    entry("gravy-lumpy", ("gravy", ("lumpy", "lump", "lumps", "thick", "thicker", "thin",
                                    "runny", "too thin", "thicken", "thickens", "make", "smooth",
                                    "sieve", "sieved")),
          "Whisk the flour into the meat juices off the heat before adding stock, then simmer it "
          "for 5 minutes. If it's already lumpy, pour it through a sieve and push the lumps "
          "through with a spoon. Too thin or runny, simmer it uncovered to reduce it, or knead "
          "equal butter and flour and whisk that in a little at a time."),

    # --- storage and food safety -------------------------------------------
    # A pot that came out bigger than the meal is a shape of its own: "i made too much" names no
    # subject at all, and "i made too much soup" names a dish as the thing that overflowed. On main
    # `3f95bf8` both got nothing useful - "nice - how did it go?", "noted: youve got loads of
    # leftovers", a shrug - and four were answered about something else: too much rice was the
    # rinsing steps, too much chilli was the cool-a-hot-dish advice, too much for two people was a
    # meeting, too much at christmas was a gift budget. The keeping answers exist; nothing reached
    # them from the quantity. So this row is keyed on the quantity and the surplus, and it says
    # where the keeping answers are.
    entry("made-too-much",
          (("too much", "far too much", "way too much", "too many", "loads", "lots", "so much",
            "plenty left", "double the amount", "overcatered"),
           ("made", "make", "makes", "cooked", "cook", "left over", "left", "leftover",
            "leftovers", "food", "dinner", "tea", "lunch", "meal", "batch", "portion",
            "portions", "soup", "stew", "curry", "chilli", "bolognese", "mash", "rice", "pasta",
            "lasagne", "lasagna", "casserole", "pie", "cake", "bread", "chicken", "meat")),
          ("Get it cold fast and split it now: cool it within an hour, keep what you will eat in "
           "the next 3 days in the fridge and freeze the rest flat in bags or tubs. Mash keeps a "
           "month frozen and stew, curry, soup or bolognese three, and a cake or a loaf freezes "
           "well sliced, three months; rice is the one to be strict with - fridge it within the "
           "hour and eat it within a day. Reheat once, until piping hot right through, and next "
           "time cook 75 to 100g of dry pasta or 60g of rice a head."),
          # a cup of tea is not a pot of stew: "how much tea is too much" is the caffeine limit,
          # and "i made too much tea" keeps this card because it says it was made
          guard=not_a_cup_of_tea,
          # "too much" is a quantity in other rooms too: a drink, a spend, a symptom, or a
          # seasoning. Those lines are not a pot that overflowed.
          # a count of cups is not a pot that overflowed: "is 4 cups of tea too much" was answered
          # with the cool-it-and-freeze-it card, because "tea" is in the key above as the evening
          # meal. The caffeine limit owns that line.
          # "how much tea is too much" and "is too much tea bad for you" ask the caffeine
          # question, and the drinking shapes are held out by the drink rather than by the word
          # "tea": a pot that overflowed says "i made too much", not "how much tea".
          avoid=("cups of tea", "cups of coffee", "cup of tea", "cup of coffee", "mugs of tea",
                 "mug of tea", "caffeine", "coffees",
                 "how much tea", "how much green tea", "green tea", "herbal tea", "black tea",
                 "tea a day", "teas a day", "tea is too much", "too much tea is",
                 "is too much tea", "how much tea is", "much tea a day",
                 "tea every day", "cup of tea a day",
                 "drink", "drinking", "drank", "alcohol", "beer", "wine", "coffee", "tea bags",
                 "spend", "spending", "spent", "money", "pay", "paid", "afford", "budget",
                 "salt", "salty", "sugar", "spice", "spices", "spicy", "seasoning", "pepper",
                 "chilli powder", "hot sauce", "exercise", "training", "work", "overtime",
                 "sleep", "slept", "screen", "sun", "throw", "throwing", "thrown", "waste",
                 "wasting", "wasted", "bin", "binned", "left out", "leftover medicine",
                 "tablet", "tablets", "medicine", "medicines",
                 # a shop that came home too big is the shopping-and-waste answer, and a "what
                 # can i make with" is a recipe
                 "bought", "buy", "buying", "shop", "shopping", "supermarket",
                 "what can i make", "what can i do with", "make with", "use up", "use them up",
                 # "what can i cook" is the same recipe question as "what can i make": "i have
                 # too much rosemary what can i cook" was told to cool it within the hour and
                 # freeze the rest flat, and there was no pot.
                 "what can i cook", "what can i cook with", "can i cook with",
                 # the freeze, the fridge and the reheat each have a row of their own that names
                 # the dish; "i made too much soup can i freeze it" wants those, not this
                 "freeze", "freezer", "frozen", "thaw", "thawing", "defrost", "reheat",
                 "reheating",
                 # a person saying they make themselves sick after eating has told you something
                 # serious, and this card told them to cool it within the hour and freeze the rest
                 # flat. "too much" is also how a binge is described, so the disclosure stands the
                 # food-storage card down and the person gets a reply that is about them
                 # (safe-needle, #answers 109626).
                 "make myself sick", "made myself sick", "making myself sick",
                 "make myself throw up", "made myself throw up", "making myself throw up",
                 "make myself vomit", "made myself vomit", "throw up after eating",
                 "threw up after eating", "sick after eating", "vomit after eating",
                 "vomiting after eating", "purge", "purged", "purging", "binge", "binged",
                 "bingeing", "binge eating", "bulimia", "bulimic", "anorexia", "anorexic",
                 "eating disorder", "starve myself", "starving myself", "not eating",
                 "guilt about eating", "feel guilty after eating")),
    entry("chicken-left-out", ("chicken", ("overnight", "left out", "sit out", "sitting out",
                                            "out of the fridge", "all night", "room temperature")),
          "Bin it, I'm afraid: cooked chicken left out for more than 2 hours isn't safe to eat, "
          "even if it looks and smells fine. Next time, get leftovers into the fridge within an "
          "hour and they'll keep 3 days."),
    entry("leftovers-keep", (("leftovers", "leftover", "cooked food", "cooked last night",
                              "cooked yesterday", "food cooked", "from last night",
                              "dinner last night", "tea last night", "supper last night"),
                             ("how long", "safe", "fridge", "keep", "days", "store", "storing",
                              "where", "shelf life", "shelf-life", "ok", "okay", "eat",
                              "eat it", "still good", "reheat")),
          "Cooked leftovers keep 3 to 4 days in the fridge if they went in within 2 hours of "
          "cooking. Reheat them until piping hot all the way through, once only, and bin anything "
          "you're unsure about.",
          # "leftover" is a word about medicine too: "where should i take my leftover antibiotics"
          # was the keeping time of last night's dinner. A leftover with a medicine in it is the
          # pharmacy's question (rubbish.py, dispose-medicines), so the food row stands aside.
          avoid=("medicine", "medicines", "tablet", "tablets", "pill", "pills", "capsule",
                 "capsules", "antibiotic", "antibiotics", "prescription", "inhaler", "syringe",
                 "epipen", "painkiller", "painkillers", "antidepressant", "antidepressants",
                 "medication",
                 # A food with a keeping row of its own is that row's question: widening this one
                 # to "last night's dinner" made "is it safe to reheat leftover rice the next
                 # day" the 3-to-4-day leftovers answer, when rice has its own 24-hour rule.
                 "rice", "pasta", "spaghetti", "noodles", "chicken", "turkey", "ham", "gammon",
                 "bacon", "sausage", "sausages", "salmon", "fish", "prawns", "pizza", "soup",
                 "stew", "curry", "potato", "potatoes", "tofu", "cream", "milk",
                 # a leftover that is a material is not a plate of food: "how do i store leftover
                 # paint" and "how do i keep leftover paint from going off" were told to eat it
                 # within 3 to 4 days, because "leftover" and "store" are this row's two words
                 "paint", "paintbrush", "paintbrush", "emulsion", "gloss", "undercoat", "primer",
                 "varnish", "wood stain", "woodstain", "wallpaper", "tile adhesive", "grout",
                 "cement", "mortar", "filler", "sealant", "caulk", "silicone", "sandpaper",
                 "timber", "compost", "gravel", "screws", "tiles"),
          # "is it safe to eat food cooked last night" was reaching the card about eating late and
          # putting on weight: a leftovers question wearing the words of a meal-time one. The
          # meal-time card scores higher on its own words, so this row has to be preferred where
          # the line names food that was already cooked.
          bias=4),
    # A dish the table had no row for was a shrug: "how long does couscous keep", "how long does
    # paella keep" and "how long does guacamole keep" all came back as "I don't know enough to
    # answer that honestly". Every kitchen keeps these the same way, so the window is the row and
    # the dish names are its data: a cooked dish is the 3-to-4-day rule, a dip or a fresh-herb
    # salad is a day or two, and a set dessert is 2 to 3 days. A dish that gets a row of its own
    # later still wins, because this row only claims the names listed here.
    entry("a-cooked-dish-with-no-row",
          (("couscous", "bulgur", "bulghur", "quinoa", "risotto", "paella", "biryani",
            "jambalaya", "gumbo", "cassoulet", "tagine", "goulash", "moussaka", "ratatouille",
            "falafel", "paneer", "polenta", "gnocchi", "dumplings", "stuffed peppers",
            "stuffed aubergine", "vegetable bake", "macaroni cheese", "mac and cheese",
            "cauliflower cheese"),
           KEEPING_WORDS),
          "That keeps 3 to 4 days in the fridge once it is cooked: cool it within two hours, get "
          "it covered into the fridge, and reheat it once, piping hot all the way through. "
          "Anything with rice or chicken in it is the one to be strict with, and what you will not "
          "eat in that time freezes well for 2 to 3 months.",
          # A recipe, a cooking time or a freeze is not a keeping question: "how long does
          # couscous take to cook" and "can i freeze paella" were both answered with the days it
          # keeps, which is the row over-claiming rather than the line asking twice.
          avoid=NOT_A_KEEPING_ASK, guard=_not_a_cooking_time),
    entry("a-dip-or-a-herb-salad-keeps",
          (("guacamole", "tzatziki", "aioli", "taramasalata", "tabbouleh", "tabouleh",
            "raita", "salsa verde", "sour cream dip", "onion dip", "egg mayonnaise"),
           KEEPING_WORDS),
          "A day or two at most, and it is the avocado, the cucumber and the fresh herbs that turn "
          "first: keep it covered, pressed down so no air is on top, and in the coldest part of "
          "the fridge. Guacamole is at its best the day it is made, so make what you will eat.",
          avoid=NOT_A_KEEPING_ASK, guard=_not_a_cooking_time),
    entry("a-baked-fruit-pudding-keeps",
          (("crumble", "apple crumble", "rhubarb crumble", "fruit crumble", "cobbler",
            "fruit tart", "apple tart", "treacle tart", "lemon tart", "jam tart",
            "baked apple", "baked apples"),
           KEEPING_WORDS),
          "A crumble or a tart keeps 2 to 3 days in the fridge, covered: the topping goes soft "
          "before it goes off. Reheat it at 180C (160C fan) for 15 minutes to crisp the top again, "
          "and freeze it unbaked for 3 months, then bake it from frozen for 20 minutes longer.",
          avoid=NOT_A_KEEPING_ASK, guard=_not_a_cooking_time),
    entry("a-set-dessert-keeps",
          (("cheesecake", "tiramisu", "panna cotta", "chocolate mousse", "lemon mousse",
            "creme caramel", "flan", "posset", "mousse"),
           KEEPING_WORDS),
          "A set dessert like that keeps 2 to 3 days in the fridge, covered, and it is better on "
          "the second day than the first. A cheesecake is 3 to 4 days and freezes well in slices; "
          "a mousse or a posset is the shortest at 2 days, because it is mostly cream and egg.",
          avoid=NOT_A_KEEPING_ASK, guard=_not_a_cooking_time),
    entry("fridge-temp", ("fridge", ("temperature", "how cold", "setting", "dial", "cold",
                                     # "warm" on its own is not a temperature word: "something
                                     # warm for dinner, but the fridge is nearly empty" reached
                                     # this card because the line named a fridge and a warm
                                     # dinner. A fridge that is warm is said as a phrase.
                                     "too warm", "feels warm", "felt warm", "running warm",
                                     "not cold enough", "warm again")),
          "Your fridge should be between 0 and 5C, with the coldest shelf at the bottom; use a "
          "thermometer rather than the dial. Keeping it properly cold is the single easiest way to "
          "make food last longer.",
          # a cold beer or an opened bottle is a keeping question, not a temperature one.
          avoid=("beer", "wine", "bottle", "opened")),
    entry("beer-keeping", ("beer", ("fridge", "keep", "last", "off", "flat", "opened",
                                   "how long")),
          "Unopened beer is best within three to six months in the fridge, and drinkable for a lot "
          "longer than that; an opened bottle goes flat within a day, so finish it fresh. Keep it "
          "upright and out of sunlight, which skunks the flavour faster than age does."),
    entry("wine-no-corkscrew", (("corkscrew", "no opener", "bottle opener"),
                                ("open", "no", "without", "dont", "don't", "havent", "haven't",
                                 "forgot", "lost", "missing", "wine")),
          "Drive a long screw into the middle of the cork, leave a few centimetres sticking out and "
          "lever it up a little at a time with a fork, pliers or the back of a key. In a pinch you "
          "can push the cork in with the handle of a wooden spoon, which is fine if you are "
          "drinking the bottle now. Warm the neck in your hands first if the cork is stubborn.",
          # OPEN_ASK cannot sit here: "how do i open a bottle with no corkscrew" is this entry's
          # own line, and the opener is what is missing, not the grip.
          avoid=("stain", "carpet", "spill"),
          bias=1),
    entry("wine-bottle-open",
          (("wine", "bottle of red", "bottle of white", "red wine", "white wine", "rose wine",
            "prosecco", "champagne", "sparkling wine", "cava", "cork", "screw cap"),
           ("open", "opening", "uncork", "get it open", "crack it open", "pop the cork",
            "screw cap", "twist the cap", "twist off", "undo the cap", "how do i open")),
          _open_wine,
          # a bottle with no opener, a cork that broke, and how long an open bottle keeps are the
          # neighbours, and each of them is the better answer to its own line
          avoid=("no corkscrew", "without a corkscrew", "without the corkscrew", "no opener",
                 "havent got a corkscrew", "haven't got a corkscrew", "dont have a corkscrew",
                 "don't have a corkscrew", "lost the corkscrew", "forgot the corkscrew",
                 "cork broke", "cork snapped", "cork in the bottle", "how long", "gone off",
                 "go off", "goes off", "still good", "still ok", "still fine",
                 "vinegar", "keep", "last", "fridge", "leftover", "left over", "already open",
                 "opened bottle", "open bottle", "stain", "carpet", "sauce", "recipe", "risotto",
                 "gravy", "mulled",
                 # "can i open a bottle of red wine and leave it out" is a keeping question with an
                 # opening word in it, and the keeping row has the 3 to 5 days
                 "leave it out", "leaving it out", "left out", "leave it", "out overnight",
                 "overnight", "in the fridge", "in the rack", "how many days"),
          bias=1),
    # A cork that snapped, or one pushed in, is the evening ruined differently from a bottle with
    # no opener, and no key held it: "the cork broke in the bottle" and "the cork snapped off in
    # the neck" were shrugs.
    entry("broken-cork", (("cork", "corks", "stopper", "broken cork", "cork breaks",
                           "cork broke", "cork has broken", "cork snapped", "piece of cork",
                           "bits of cork"),
                          ("broke", "breaks", "broken", "snapped", "snapped off",
                           "fell in", "dropped in", "crumbled", "brittle",
                           "pushed in", "in the bottle", "in the neck", "stuck", "wedged",
                           "half", "crumbs", "out", "remove")),
          ("Push it in: a cork that has snapped or dropped into the bottle does no harm to a wine "
           "you are drinking tonight, and a clean cork floats. To get it out, pour the wine into a "
           "jug through a sieve, fish the cork out and pour it back. A cork stuck in the neck comes "
           "out on a long screw turned into it and pulled with pliers."),
          # "corky" cannot sit here: it is one slip from "cork" itself, and the slip test would
          # then throw away every cork line. The words are what the cork is not - a board, a floor,
          # a hat.
          avoid=("board", "floors", "flooring", "tiles", "oak", "pinboard", "bulletin", "hat",
                 "recipe", "risotto")),
    # A bowl of leaves is a side, and "how do i make a salad more filling" was answered with the
    # five-a-day rule (400g, a handful is a portion) while "how do i make a salad filling" got the
    # dressing method: both were told how many vegetables to eat rather than what turns a salad
    # into a meal. The ask is the meal, and "a meal" is the whole question here.
    entry("salad-a-meal",
          (("salad", "salads", "leaves", "salad leaves", "green salad", "side salad"),
           ("filling", "filling up", "more filling", "fill me up", "into a meal", "a meal",
            "plate of food", "substantial", "satisfying", "keep me full", "stays with me",
            "hungry", "proper meal")),
          "Leaves are the vegetable, not the meal: add a protein, something starchy and something "
          "rich, and dress it while the starch is still warm. Chickpeas or a boiled egg, new "
          "potatoes and feta is dinner; tinned tuna, leftover rice and a spoon of mayo is lunch. "
          "A plate rather than a side bowl is the portion that fills you, and salt it properly.",
          # the dressing, keeping, washing and shopping questions are their own answers, and a
          # named salad (pasta, potato, coleslaw, caesar) has its own
          avoid=("dressing", "vinaigrette", "keep", "keeps", "keeping", "store", "stored", "last",
                 "lasts", "long", "wilt", "wilted", "limp", "soggy", "watery", "wet", "wash",
                 "washing", "bag", "buy", "supermarket", "calories", "healthy", "fruit",
                 "pasta", "potato", "coleslaw", "slaw", "caesar", "nicoise", "sandwich", "wrap",
                 "instead of", "substitute", "swap", "recipe")),
    entry("leftover-veg", (("vegetables", "veg", "mixed veg", "root vegetables", "greens"),
                           ("leftover", "left over", "leftovers", "leftovers", "spare", "use up",
                            "what do i do", "what can i do", "what should i do")),
          "Fry them into a hash: chop them small, start with an onion and a pinch of salt, and let "
          "them crisp at the edges before you add anything wet. Roasted vegetables are better "
          "through pasta with garlic and a spoonful of the cooking water, and anything soft goes "
          "into soup with stock and a blender.",
          # the vegetable question has its own answers; this is only about the ones already cooked
          # "what can i do with leftover veg before it goes off" is the general use-it-up meal
          # question and has its own answer; this entry is for a named vegetable.
          avoid=("raw", "freeze", "frozen", "plant", "grow", "garden", "seeds", "soup", "roast",
                 "salad", "healthy", "portion", "five a day",
                 "use up", "to use", "before it goes off", "goes off", "before they go off",
                 "going off", "use it up")),
    # An egg past its date is main's `egg-fresh` and the keeping entry in `cooking.py`; this
    # domain does not need a third answer to it.
    entry("veg-keep", (("cabbage", "mushrooms", "carrots", "lettuce", "spinach", "broccoli",
                        "courgette", "courgettes", "peppers", "vegetables", "veg", "salad",
                        # the veg the list forgot: a plain keeping question about any of these
                        # was a shrug ("how long do parsnips keep", "how long do sprouts keep",
                        # "how long do cauliflower keep"), and they keep by the same rules as
                        # the names above. Root veg and the brassicas are named as themselves
                        # rather than as "veg", because the line usually names only the one.
                        "parsnip", "parsnips", "swede", "swedes", "turnip", "turnips",
                        "sprout", "sprouts", "brussels sprouts", "brussel sprouts",
                        "cauliflower", "cauliflowers", "radish", "radishes", "kale", "chard",
                        "pak choi", "bok choy", "fennel", "celeriac", "kohlrabi",
                        "sweetcorn", "corn on the cob", "runner beans", "mangetout",
                        "sugar snap peas", "asparagus",
                        # leeks, green beans, spring onions, celery and shallots are left out
                        # on purpose: each already has a warmer answer of its own (a week in
                        # the drawer for leeks, five days for green beans, dry and dark for
                        # shallots), and this general card would talk over it.
                        # a pulse is only a veg question when the tin is named: cooked chickpeas
                        # get the general three-to-four-days answer, which is the safer one
                        "tin of beans", "tin of chickpeas", "tinned beans", "tinned chickpeas",
                        # "opened" alone is any carton, jar or bottle: milk and wine keep their
                        # own answers, and a jar of pesto has jar-keep
                        "open tin", "opened tin", "tin once opened", "once opened"),
                       # no bare "fridge": "half a cabbage in the fridge, what can I do with it"
                       # is a recipe line, and the recipe entry answers it
                       ("keep", "keeps", "last", "lasts", "still ok", "still good", "gone off",
                        "safe", "how long",
                        # "how do i store broccoli" and "how do i store veg" were shrugs next to
                        # "how long does broccoli keep", which had the drawer card all along. The
                        # bare words only, never the phrases with them: a phrase scores as well as
                        # a word, and the extra point made this general card outrank a named
                        # vegetable's own row ("how do i store spinach" lost the spinach card).
                        "store", "stores", "storing", "stored", "storage"),
                       ),
          "Most veg keeps about a week in the fridge drawer, and a bit longer than you'd think if "
          "it stays dry: keep it in a bag or box, and don't wash it until you use it. Cabbage, "
          "carrots and peppers go soft before they go off; mushrooms and salad are the ones that "
          "turn slimy, so use those first. Root veg - parsnips, swede, turnips, celeriac - is the "
          "longest of all, weeks in the fridge and months somewhere cool and dark, and sprouts and "
          "cauliflower are the quick ones: a bag with the air pressed out, and eat them inside a "
          "week before they yellow. An opened tin of beans or chickpeas keeps 3 days in a covered "
          "bowl in the fridge.",
          # "how long" is the phrase both kinds of question use, so the cooking ones have to be
          # named: "how long should I boil carrots" is a pan question, not a fridge-drawer one.
          # "and how long does that take" is a follow-up about the cooking, so "take" joins the
          # verbs: the food word it matched on was carried over from the turn before.
          # "opened" and "open tin" are here for the tin, but a jar is not a tin and a jar of
          # pesto has its own answer (jar-keep); so do the meats, which keep days not a week
          avoid=("make", "cook", "recipe", "dinner", "meal", "tonight", "freezer", "freeze",
                 # `keep` is also how a gardener asks about a pest: "how do i keep slugs off my
                 # lettuce" is the night patrol, not the fridge drawer. The pest is the fence.
                 "slug", "slugs", "snail", "snails", "pest", "pests", "bug", "bugs", "insect",
                 "insects", "caterpillar", "caterpillars", "aphid", "aphids", "blackfly",
                 "greenfly", "holes", "eaten", "eating",
                 "take", "takes", "took", "jar", "jars", "pesto", "ketchup", "mayonnaise",
                 "jam", "pickle", "chutney", "tuna", "fish", "meat", "chicken", "ham",
                 "bacon", "sausage", "mince",
                 # a drink is not veg: "how long does milk last after you open it" and "is wine
                 # still ok a week after opening" are their own answers
                 "milk", "wine", "beer", "juice", "squash", "cream", "yoghurt", "yogurt",
                 "cheese", "butter",
                 # every vegetable with a keeping line of its own wins over this paragraph: a
                 # carrot keeps for weeks and a mushroom wants a paper bag, and "about a week"
                 # is wrong for both. This entry is for the veg with no line of its own.
                 "mushroom", "mushrooms", "carrot", "carrots", "potato", "potatoes", "onion",
                 "onions", "spring onion", "spring onions", "garlic", "apple", "apples",
                 "banana", "bananas", "lemon", "lemons", "berries", "tomato", "tomatoes",
                 "eggs", "egg", "bread", "rice", "pasta", "ginger", "herbs",
                 "opened tin of beans", "opened tin of chickpeas")
                + COOK_VERBS),
    entry("food-dates", (("use by", "best before", "sell by"), ("date", "mean", "safe", "difference")),
          "'Use by' is about safety: don't eat it after that date, and don't freeze it after it "
          "either. 'Best before' is about quality, so food is usually fine for a while after, using "
          "your eyes and nose."),
    entry("leftover-pasta", ("pasta", ("leftover", "left over", "yesterday", "spare")),
          "Cold pasta is best fried: toss it in a hot pan with oil, garlic and whatever vegetables "
          "you have, and add a splash of water or passata so it doesn't stick. Or bake it in a "
          "white sauce with cheese on top for 20 minutes at 200C."),
    entry("leftover-chicken",
          (("chicken", "chicken thigh", "chicken thighs", "chicken breast", "chicken breasts",
            "chicken drumstick", "chicken drumsticks",
            # the way people name cooked chicken in the fridge: the pizza row above takes "cold
            # pizza" the same way, and without it "what can i do with cold chicken" reached the
            # roasting table and got a method for a raw bird
            "cold chicken", "cold roast chicken", "cooked chicken"),
           ("left over", "left", "leftover", "spare", "half a", "already cooked",
            # "cold" is how the pizza row above reads the same question
            "cold")),
          "Half a roast chicken is two more meals: strip the meat off the carcass now, keep it in a "
          "covered tub in the fridge for up to 3 days, and use it cold in a salad, or hot in a pie, "
          "curry, risotto, soup or sandwiches. Reheat it once, until piping hot all the way through, "
          "and simmer the carcass "
          "with an onion for stock.",
          # the safety, freezing and recipe questions have their own entries
          avoid=("safe", "safely", "how long", "bin", "smell", "smells", "sick", "pregnant", "dog",
                 "cat", "freezer", "freeze", "frozen", "left out", "overnight", "all night",
                 # a line that counts the hours it has been out is the food-safety question, not
                 # the leftovers one: "left the chicken out for a few hours" is asking whether it
                 # is still all right, and the answer is the two-hour rule. "left the chicken on
                 # the counter" is the same sentence with the time shown instead of counted.
                 "hour", "hours", "on the counter", "on the side", "counter", "worktop",
                 "make", "recipe", "recipes", "ideas", "cook with",
                 "room temperature", "reheat", "reheated", "microwave", "warm up", "twice")),
    entry("chicken-salad", ("chicken", ("salad", "sandwich", "wrap", "mayonnaise")),
          "Shred or slice cooked chicken and mix it with mayonnaise, a squeeze of lemon, salt and "
          "pepper, then add crunch: celery, red onion, or apple and walnuts. It's better after 20 "
          "minutes in the fridge, and keeps 2 days.",
          # what to put cooked chicken in is a more particular ask than what to do with the
          # whole bird, so these lines go to the sandwich rather than to chicken-meal
          # "keeps 2 days" is in the answer, but "how long does chicken salad keep" is a food
          # safety question and belongs with the cooked-chicken keeping answer
          bias=2, avoid=("keep", "keeps", "how long", "fridge", "last", "lasts", "still ok",
                         "still good", "gone off",
                         # what a chicken salad holds is the portion table's question, not how
                         # to make one: "how much protein in a chicken salad" was answered with
                         # the mayonnaise
                         "protein", "carbs", "carbohydrates", "calories", "calorie", "cals",
                         "kcal", "fat", "sugar", "fibre", "fiber", "nutrition", "nutrients",
                         "how much protein", "how many calories", "how many carbs",
                         # "and what can i do with it that isnt another sandwich" asks for a
                         # different meal, not a sandwich with mayonnaise in it
                         "another sandwich", "isnt another", "isn't another", "not another",
                         "left over", "leftover", "leftovers", "use up", "what can i do with")),
          entry("cake-sink", (_NO_LOAF_RISE + ("souffle", "soufflé"),
                        ("sink", "sank", "sunk", "collapsed", "collapse", "sunken", "flat",
                         "dropped",
                         # "my cake rose and fell" is the same fault in the words people use for
                         # a bake: the rise half is in `_NO_LOAF_RISE`'s neighbour rows, so the
                         # fall half has to carry it
                         "fell", "fallen", "falls", "rose and fell", "risen and fallen",
                         "rose then fell", "went down", "came down",
                         # the same fault said as a habit, which the matcher reads as a
                         # different word: "my cake keeps sinking" matched nothing at all and
                         # got a reflective "thanks for telling me"
                         "sinking", "keeps sinking", "keeps collapsing", "always sinks",
                         "sinks every time", "sank again")),
          "A cake sinks when it's underbaked, when the oven door was opened early, or when there's "
          "too much raising agent; all three make it rise fast and then drop. Bake it at 180C "
          "(160C fan) without opening the door for the first 20 minutes, and check with a skewer.",
          # "my cake came out flat" is this entry, not fix-bland: flat on a bake means it did not
          # rise, while flat on a stew means it has no taste. "Tastes flat" is still the seasoning
          # answer, so the taste words pass.
          # a scone that spread out is not a cake that sank: the fault is too much liquid or warm
          # butter, so the scone row answers it and this one stands down, which is what "why did
          # my scones spread out flat" needed (it was this card)
          avoid=("taste", "tastes", "tasted", "tasting", "bland", "dull", "season", "seasoning",
                 "bread", "dough", "prove", "proved", "proving", "proof", "yeast", "sourdough",
                 "knead", "kneading", "scone", "scones", "yorkshire", "yorkshires",
                 "brownie", "brownies") + _BAKE_KEEPING_SHAPED,
          bias=2),
    # A scone that spread out is a different fault from one that sank, and from a cake at all:
    # the dough was too wet, the butter went in warm, or the cutter was twisted and sealed the
    # edges. "why did my scones spread out flat" was the cake-sink answer on main.
    entry("scone-spread",
          (("scone", "scones", "soda bread", "soda farl", "soda farls"),
           ("spread", "spreads", "spreading", "spread out", "spread flat", "flat", "wide",
            "melted", "run together", "ran together", "lost their shape", "lost its shape")),
          "Scones spread when the dough is too wet or the butter warmed up: it wants to be a soft, "
          "shaggy dough you pat out rather than roll, and the butter cold and cut in small. Handle "
          "it as little as possible, pat it to about 3cm thick, and cut straight down with a floured "
          "cutter without twisting it, because a twist seals the edges and stops the rise. A dough "
          "that is too wet also spreads before the middle sets, so add flour a spoonful at a time "
          "until it just stops sticking to the bowl.",
          bias=1),
    # The other half of the same question: not "why did it sink" but "how do i get it to rise".
    # "how do i get my cake to rise" was a hedge and "how do i raise a cake" was the pay-rise
    # meeting, because the only word the matcher had for a rise was a raising agent in a recipe.
    entry("cake-rise", (("cake", "cakes", "sponge", "sponges"),
                        ("rise", "rises", "rising", "risen", "raise", "raised", "raising",
                         "taller", "fluffy", "light")),
          # The causes come before the method, because half these lines are "my cake didnt rise,
          # what went wrong" and a person whose bake has failed wants the culprit named, not a
          # recipe they may already have followed.
          "A cake rises on three things - the air you beat in, the bubbles the raising agent "
          "makes, and steam - and when it does not, the culprit is nearly always baking powder past "
          "its date (a teaspoon per 150g of plain flour, or use self-raising), the flour beaten in "
          "too hard once it went in, or the oven door opened in the first 20 minutes. Cream the "
          "butter and sugar until pale and fluffy, fold the flour in with a spoon, fill the tin "
          "two-thirds full, and bake at 180C (160C fan) without opening the door.",
          # the recipe, the sinking and the bread questions each have their own entry, and "make a
          # cake" is the recipe however the question ends
          avoid=("what makes", "makes a cake", "make a cake", "make my cake", "recipe", "recipes",
                 "sunken", "sank", "sunk", "sinking", "collapsed", "bread", "sourdough", "yeast",
                 "breadmaker", "taste", "tastes", "flat", "biscuit", "biscuits"),
          bias=1),
    # "the milk in my fridge smells off but the date is fine" is a milk question with the fridge
    # in it as the place the milk is, and the appliance row took it: the reply was to photograph
    # the inside of the fridge and claim for a repair. A place named in the line is not the
    # subject of it, so this row carries the bias to keep a bottle away from the appliance, and
    # the phrases below are how people say the smell. "My fridge is not cold" and "my fridge is
    # broken" still reach the appliance, because neither of them names any food.
    # The key's two halves have to be near each other in the line, so the place the bottle is kept
    # is a key word too: "the milk in my fridge smells off" put a fridge between milk and smells
    # and scored nothing at all, while "the milk smells off in the fridge" scored five.

    entry("milk", ("milk", ("sour", "off", "smell", "smells off", "smelt off", "smells sour",
                            "smells funny", "smells wrong", "in my fridge", "in the fridge",
                            "in our fridge", "keep", "how long", "date", "opened",
                            "ok", "still ok", "safe", "still good", "past it", "gone off",
                            "shelf life", "shelf-life")
                          # the day word is the same question as the date: "can i drink milk
                          # tomorrow" was the dairy-free swap card, because the only rows that
                          # scored were the diet plan and a keeping stand-down, and this card had
                          # no day word to score on.
                          + DAY_WORDS
                          # the store question is the same one: "how do i store milk" was a
                          # shrug while "how long does milk keep" had the card all along
                          + STORE_ASKS
                          # a bottle of expressed milk is a milk row too, and without its own
                          # name here "how do i store breast milk" and "how do i freeze breast
                          # milk" were answered with the puberty card, whose only word in common
                          # was "changes"/"milk" - the breast milk branch below has the hours
                          + ("breast milk", "breastmilk", "expressed milk", "formula milk")),
          _milk_keep,
          # a milk tooth is a child's tooth: "my son's milk tooth fell out" was answered with the
          # carton, because milk is the only word the two have in common
          avoid=("tooth", "teeth", "milk tooth", "milk teeth", "baby tooth", "baby teeth",
                 "tooth fairy", "fell out", "wobbly", "loose tooth",
                 # a fridge that is warm, noisy or broken is the appliance, and a fridge that
                 # smells is the cleaning row: neither is this bottle
                 "not cold", "isnt cold", "isn't cold", "broken", "warm", "noisy", "buzzing",
                 "freezer", "fridge door",
                 # "the fridge smells of milk" is the fridge that smells, and that card washes
                 # out the door seal and the drain hole
                 "smells of milk", "smells like milk", "smell of milk", "smells of cream",
                 "smells of yoghurt",
                 # "is milk ok in pregnancy" is not a question about a sour carton: the
                 # pregnancy row answers it, and this one only shares the word "ok" with it.
                 "pregnant", "pregnancy", "expecting", "miscarriage", "trimester",
                 # a supply question is not a storage question: "how do i stop my breast milk
                 # drying up" wants feeding advice, and the hours are a wrong answer to it
                 "drying up", "supply", "enough milk", "low supply", "milk supply")),
    # A pan that smokes is a hot fat and a worried cook, and the bot said "your wok is smoking -
    # I'll remember that". Fat smokes at a temperature, so the answer is the heat, the fat's own
    # limit and what to do with the pan you already have: wipe it out, do not just carry on.
    entry("oil-smoking",
          (("pan", "pans", "oil", "oils", "butter", "fat", "grease", "greases", "greasy",
            "wok", "lard", "ghee", "dripping",
            "margarine", "olive oil", "rapeseed", "sunflower", "vegetable oil", "frying pan",
            "skillet", "deep fat fryer", "fry", "fries", "frying", "fryer", "deep fry",
            "deep frying", "fry up", "chip pan", "chips"),
           ("smoking", "smokes", "smoke", "smoked", "smoky", "burnt", "burning", "too hot",
            "overheating", "smoke point", "smokes when", "reuse", "re-use", "reusing",
            "used oil", "old oil", "used cooking oil", "old frying oil", "used frying oil",
            # "is the oil still good after frying" and "can i still use it" are the reuse ask
            # a bare "can i use" also caught every swap - "can i use butter instead of oil" and
            # "can i use sunflower oil instead of vegetable oil" are the substitution table's
            # line - so each form below names the old fat being used again
            "still good", "still use", "can i use it", "can i use it again", "can i use this oil",
            "can i use that oil", "can i use the oil", "can i use the oil again",
            "can i use this fat", "can i use that fat", "can i use it once more",
            # the heat of the oil and a pan that foams are the same subject as a pan that smokes,
            # and both were shrugs or the oven-chip time
            "how hot", "hot enough", "temperature", "foam", "foams", "foamy", "foaming",
            "bubbling",
            # "how do i know when the pan is hot" is the same question as "how hot should the
            # pan be", and it was a punt on main while "is the pan hot enough" answered well:
            # the word people leave out is "enough". The phrases below name the pan or the fat
            # with the heat, so a bare "hot" is still not a key on its own.
            "is hot", "is ready", "pan heat", "the heat", "test the heat", "check the heat",
            "hot oil", "oil is hot", "oil is ready", "fat is hot", "fat is ready",
            "heat the pan", "heating the pan", "heat the oil", "heating the oil",
            # pan first or oil first, and where the oil actually goes
            "put the oil in", "put in the oil", "add the oil", "adding the oil", "oil go in",
            "oil goes in", "pan first", "oil in the pan", "oil in a pan", "hot pan first",
            "pan be hot", "hot before", "before the oil", "before adding the oil",
            "pan hot before", "when do i add the oil",
            # a person with a bottle of spent fat asks where it goes, which is the same subject
            "throw out", "throw away", "get rid", "getting rid", "dispose", "disposal", "bin it",
            "recycle", "recycling", "down the sink", "what to do with", "where do i put",
            "where do i pour",
            # "can i put fat down the toilet" and "can i pour grease down the drain" are the
            # same question as "where do i put cooking oil" - may I - and both were shrugs
            # while the answer was sitting in this row's disposal arm. The one it must still
            # not take is a drain that has already blocked on fat, which is the unblocking
            # steps, so that phrase is on the row's avoid list below.
            "down the toilet", "down the loo", "down the drain", "down the plug hole",
            "down the plughole")),
          _oil_smoking,
          # healthy eating is frying-oil's, a pan with burnt-on grease is the cleaning answer, and
          # nothing here is about stopping smoking: "the oil in my pan is smoking" once reached the
          # quit-smoking card.
          avoid=("healthiest", "healthy", "unhealthy", "unsaturated", "saturated", "cholesterol",
                 "calories", "burnt on", "scrub", "clean", "cleaning", "give up",
                 # the fat in a body is not the fat in a pan: "how do i get rid of belly fat" was
                 # poured into a jam jar, and "does running burn belly fat" was told the pan was
                 # past its smoke point. The body words are what tell the two apart, with the
                 # losing words, because "get rid of" alone is the bottle and "fat" alone is a pan.
                 "belly fat", "body fat", "stomach fat", "tummy fat", "thigh fat", "leg fat",
                 "arm fat", "bingo wings", "love handles", "muffin top", "fat around",
                 "fat on my", "lose fat", "losing fat", "lost fat", "burn fat", "burning fat",
                 "burns fat", "burn belly", "fat loss", "fat burning", "spot reduce", "get abs",
                 "flat stomach", "tone my", "toning my", "loose weight",
                 # a pan that already has burnt food in it is the bicarbonate answer, not a pan
                 # that is smoking now; phrases, because a bare "burnt" would stand down
                 # "how do i stop my pan burning", which is this entry's own question
                 "burnt food", "burnt bits", "stuck to", "bottom of my pan", "bottom of the pan",
                 "bicarbonate", "soak", "pan is burnt", "frying pan is burnt",
                 # "my pan has burnt stuff stuck on it" is a pan to soak, and it was told the fat
                 # was past its smoke point: "stuck to" does not cover "stuck on", and nothing
                 # here named the stuff. A pan somebody wants rescued is the same job.
                 "stuck on", "stuck on it", "stuck on the pan", "stuck on the bottom",
                 "burnt stuff", "stuff stuck", "burnt pan", "burned pan", "scorched pan",
                 "rescue the pan", "rescue a burnt", "save the pan", "pan is ruined",
                 "burnt layer",
                 # keen-book: "how do i get rid of the smell of frying" is a smell in the room,
                 # not where the fat goes, and the disposal arm would answer it
                 "smell", "smells", "smelling", "smelly", "odour", "odor", "stink", "stinks",
                 # a pan that has bowed is a pan that no longer sits flat, not a pan of fat at
                 # its smoke point: "can i still use a warped pan" was answered with the spent-oil
                 # card because "still use" is this row's own reuse ask
                 # a bottle of oil going into the freezer is a storage question, not a pan:
                 # "can i put oil in the freezer" was told the fat was past its smoke point
                 "freezer", "freeze", "freezing", "frozen", "fridge", "refrigerator",
                 "warped", "warp", "warping", "warped pan", "wont sit flat", "doesnt sit flat",
                 "doesn't sit flat", "bowed", "spins", "rocks",
                 # where a hot pan goes down is the surface's question, not the fat's; the
                 # phrases all name a pan being put somewhere, so "put the oil in a hot pan"
                 # is untouched
                 "put a hot pan", "put the hot pan", "stand a hot pan", "stand the hot pan",
                 "set a hot pan", "set the hot pan", "hot pan on", "hot pan down",
                 # one fat in place of another is the substitution table's line, not the pan's
                 "instead of", "in place of", "substitute", "substituting", "swap", "swapping",
                 "replace", "replacing", "alternative to",
                 # "should butter be room temperature" and "how hot should the oven be for a
                 # roast" are not the oil's question
                 "room temperature", "soften", "softened", "baking", "cake", "bake", "roast",
                 # "what can i use instead of butter" is a swap question, and `swap-butter`
                 # answers it: this row holds the word butter and the phrase "can i use", so it
                 # scored higher and answered with how to deal with a pan of spent fat. The ask
                 # for a stand-in is never about a pan that is smoking, so it stands this row
                 # down wherever it appears.
                 "instead of", "in place of", "substitute", "swap", "stand in for",
                 "alternative to",
                 # a bare lack is not a swap ask. "ive no oil left and the pan started smoking"
                 # and "my oil smoked and i have no oil left" are the pan's question, and the
                 # bare lacks in this list handed them to the quit-smoking row - "smoking" is the
                 # one word the two subjects share. The swap-shaped phrases are what the list is
                 # here for, and every line that wants a stand-in says one of them.
                 "what can i use", "can i use instead", "what do i use", "use instead",
                 # snug-parrot: "how do i store used oil", "how do i keep used oil" and "can i keep
                 # used oil" are where a bottle lives, which keep-oil answers; the key's own
                 # "used oil" and "old oil" are disposal words and were outranking it. A pan that
                 # is smoking is not a cupboard.
                 # "keep the oil" stays here because that is the pan's oil and a reuse question;
                 # "keep used oil" is a bottle in a cupboard and is keep-oil's.
                 # "can i use margarine instead of butter" and "what can i use instead of
                 # butter" are the swap question, not a pan of spent fat: the key pairs a fat
                 # with "can i use", and nothing in the line is about heat or reuse.
                 "instead of butter", "instead of margarine", "in place of butter",
                 "in place of margarine", "substitute for butter", "substitute for margarine",
                 # A person asking what stands in for an ingredient is not asking what to do
                 # with the oil they fried in, and this entry names the fats people run out of:
                 # "no butter what can i use" reached it and was told to strain the oil and use
                 # it once more, while the swap row had the right answer. The swap question is
                 # a phrase ("what can i use", "ran out"), never the bare "no" or "out".
                 # the swap words and a shortage of a fat, never the bare "what can i use":
                 # "what can i use to fry chips" is this row's own question and was a hedge
                 # once that phrase was in the list.
                 "instead", "instead of", "in place of", "substitute", "alternative",
                 "no butter", "no margarine", "no lard", "no dripping", "no ghee",
                 "run out of butter", "ran out of butter", "out of butter", "out of margarine",
                 "none left", "havent got any butter", "haven't got any butter",
                 "im out of butter", "i'm out of butter",
                 "store", "stored", "storing", "storage", "cupboard", "shelf", "pantry", "larder",
                 "keep used", "keeps used", "keeping used", "kept used",
                 "where do i keep", "where can i keep", "where to keep",
                 "keep old", "keeps old", "keeping old", "kept old", "how long", "last", "lasts",
                 # civil-coconut: "how do i dispose of engine oil" is hazardous waste, not the
                 # kitchen bottle, and the car row that answers it is right - "put it in the
                 # rubbish" is the wrong advice for a sump.
                 "engine", "engines", "car", "cars", "motor", "motorbike", "motorcycle",
                 "lawnmower", "mower", "gearbox", "gear oil", "hydraulic", "diesel", "petrol",
                 "two stroke", "2 stroke", "sump", "oil change", "garage",
                 "quit", "cigarette", "cigarettes", "vape", "fag", "fags", "i smoke",
                 "stop smoking", "stopped smoking", "electric", "cooker", "oven", "barbecue",
                 "bbq", "fire alarm", "chimney",
                 # The "still use" and "can i use" asks in the key are the oil's, and a pan with
                 # a worn coating has the same words in it: "my non stick pan is scratched can i
                 # still use it" was told to strain the fat through a coffee filter. A coating
                 # question is the pan's row, and it opens with the verdict.
                 "non stick", "non-stick", "nonstick", "teflon", "coating", "coated",
                 "scratched", "scratches", "scratch", "flaking", "peeling",
                 # "my mug is chipped, can i still use it" and "a plate got chipped, should i
                 # throw it away" are crockery questions: the key word "chips" is the potato, and
                 # the reuse and throw-away words are the oil's, so the pan answered a mug
                 "mug", "mugs", "plate", "plates", "cup", "cups", "saucer", "saucers", "bowl",
                 "bowls", "glass", "glasses", "tumbler", "tumblers", "teapot", "jug", "dish",
                 "dishes", "crockery", "cutlery", "worktop", "tile", "tiles",
                 # A greasy thing is not a pan. "grease" and "greasy" are in the key, and the
                 # key's other half is every "get rid of" and "down the drain" phrase, so
                 # "how do i get rid of greasy shine on my face" was answered "the fat is past
                 # its smoke point, turn the heat down" - a pan of fat for a face. A part of a
                 # person, or a shine on one, is the body's or the cleaning row's, and the same
                 # fence is on mark-on-skin and garment-shine.
                 "face", "faces", "forehead", "nose", "chin", "cheeks", "cheek", "skin",
                 "t-zone", "t zone", "scalp", "hair", "hands", "hand", "thighs", "elbow",
                 "elbows", "shoulders", "neck", "shine", "shines", "shiny", "sheen", "gleam",
                 "glow", "oily", "spot", "spots", "pores",
                 # "sink" used to stand the row down and it was the one word that stopped it
                 # answering its own disposal line: "can i pour oil down the sink" is the
                 # question the fat-down-the-drain answer is written for, and it was a search
                 # hedge while the same row keyed the phrase. The crockery questions it was
                 # meant to keep out all name the thing in the sink (mug, plate, dishes,
                 # cutlery) or the dirt on it (clean, grease, smell), and a line with none of
                 # those and no fat word cannot reach the row at all.
                 "blocked", "blocked up", "blockage", "blocking", "slow draining", "drains slowly",
                 "worn out"),
          ask=("my", "the", "is", "why", "what", "how", "should", "does", "do", "i", "a", "it",
               "keep", "keeps", "when", "cant", "started", "starts"),
          # "can i reuse oil after it smoked" ties with plan-pudding, whose loose "afters" reads
          # the "after" as a dessert word: both scored 4 and the tie-break went to the longer
          # key. Three points of bias, not a wider key, because the keys are right.
          bias=5),
    entry("frying-oil", ("oil", ("healthiest", "healthy", "best", "cook", "frying")),
          "Olive oil or rapeseed oil is a good everyday choice: both are high in unsaturated fat "
          "and fine for normal frying. Save the extra virgin olive oil for salads and low heat, "
          "and use a plain vegetable oil when you need a very hot pan."),
    # How much fat and how hot is a chip pan question, and it is the one thing the people who
    # ask it are actually asking: "how much oil for chips" was told most cars take 4 to 5 litres,
    # and with the car row stood down it fell through to a search hedge while the frying-fat row
    # answered a pan that was already smoking. The volume and the temperature are one answer,
    # and the danger of hot fat belongs with them.
    entry("chip-pan-fat",
          (("oil", "fat", "lard", "dripping", "sunflower oil", "vegetable oil", "rapeseed oil",
            "groundnut oil", "frying oil", "chip pan", "fryer", "deep fat fryer",
            "deep-fat fryer"),
           # the food being fried, or the pan it is fried in, in the line: a bare "how much oil
           # should i put in the pan" is a question about a frying pan of any food, and this
           # answer is only right for a deep pan of fat.
           ("chips", "chip pan", "chip pans", "fryer", "fryers", "deep fat fryer",
            "deep-fat fryer", "fries", "french fries", "wedges", "doughnuts", "donuts",
            "batter", "scampi", "onion rings", "fried chicken", "tempura",
            "deep frying", "deep fry", "deep fried", "deep-fried")),
          ("For a chip pan or a fryer, fill it no more than a third full and never past half - "
           "hot fat rises when the food goes in, and a pan that is too full is the way people "
           "get burned. 180C is the temperature for chips: a cube of bread browns in about 30 "
           "seconds. Fry in small batches so the fat does not drop, stand back as the chips go "
           "in, and never leave the pan."),
          # a pan that is already smoking is oil-smoking's line, and the amount to buy or the
          # price is the frying-oil row's
          avoid=("smoking", "smokes", "smoke", "smoked", "burnt", "burning", "on fire",
                 "caught fire", "healthiest", "healthy", "unsaturated", "saturated",
                 "cholesterol", "calories", "price", "cost", "buy", "best pan", "which pan",
                 "motor", "car", "engine", "van",
                 # an air fryer takes no oil at all: the chips time is chips-cook's answer
                 "air fryer", "air-fryer", "airfryer", "cheapest", "which oil",
                 # which oil to fry in is the frying-oil row's question, and it answered "what
                 # oil for frying chips" well before this row existed
                 "what oil", "best oil", "kind of oil", "type of oil", "which fat"),
          bias=2),
    entry("cheese-store", ("cheese", ("store", "keep", "fridge", "mould", "mouldy", "mold", "moldy",
                                      "wrap", "gone off", "date", "dates", "out of date",
                                      # the test in your hand, which reached no row at all:
                                      # "my cheese smells off" was a refund card, then a "Got it."
                                      "off", "smell", "smells", "smelt", "smells like",
                                      "slimy", "ammonia", "ammonia smell", "still ok",
                                      # what mould is called before anyone says the word:
                                      # "my cheese is going blue" was answered with "Got it."
                                      "blue", "blue spot", "blue spots", "gone blue",
                                      "going blue", "turning blue", "blue mould", "green",
                                      "is it ok", "ok to eat", "safe to eat", "gone slimy",
                                      # the same two questions asked with the storing verb and
                                      # nothing else: "where do i put cheese in the fridge" was
                                      # answered by the fridge-disposal row and "should i wrap
                                      # cheese in cling film" by the tortilla wrap.
                                      "put", "where do i put", "cling film", "clingfilm",
                                      "storing", "stored", "keep it")),
          _cheese_keep, guard=_not_a_serving_frame),
    # --- what to make with what is in the kitchen --------------------------
    # "what's"/"whats" because the matcher reads the raw words of a line, apostrophe and all
    # "what do kids eat" and "what should i feed my kids" are the same question as "kids tea
    # ideas", and the eating words were not in the second part, so they went looking for another
    # table: "what do kids like to eat" reached the city row, and with the goat's "kids" removed
    # ("what should i feed my kids for lunch") they would have fallen to a hedge.
    # A son or a daughter is a kid, and the words people actually use were not in the key:
    # "my son is 4 years old, what should i feed him" reached no table at all and the line came
    # back as a shrug. Brothers, sisters and the child's own name are still the person row's.
    entry("kids-tea", (("kids", "children", "child", "son", "sons", "daughter", "daughters",
                        "boy", "boys", "girl", "girls"),
                       ("tea", "dinner", "supper", "meal", "food", "eat", "eats", "eating",
                        "feed", "feeds", "feeding", "fed")),
          "Keep it plain and fast: fish fingers or chicken strips with peas and oven chips, pasta "
          "with grated cheese and sweetcorn, or a cheese omelette with toast. Put something green "
          "on the plate and don't make a second dinner if they refuse it.",
          # a tea at home, not catering for a party or a picnic: those are party-food's lines
          bias=1,
          # a food named in the line is that food's question, not this one
          guard=_no_named_food,
          # a breakfast is the breakfast table's question, and "what do kids eat for breakfast"
          # was answered with fish fingers once the eating words were in the key.
          avoid=("picnic", "party", "birthday", "guests", "take", "bring", "school", "packed",
                 # "can kids eat nuts" is a question about the food, not about a dinner: a food
                 # that has a card of its own keeps it (the allergen introduction for nuts and
                 # peanut, the cutting-up card for grapes and berries), and honey stays the honest
                 # "I don't know" rather than a plate of fish fingers. Only foods whose card is
                 # known are here.
                 "nuts", "nut", "peanut", "peanuts", "peanut butter", "honey", "grape", "grapes",
                 "berry", "berries", "strawberry", "strawberries", "egg", "eggs", "shellfish",
                 "choking", "sesame", "soya", "soy",
                 "breakfast", "cereal", "toast",
                 # a drink is not a dinner: "is it ok to feed kids goats milk" is the milk row's
                 "milk", "goats milk", "goat milk", "formula", "bottle",
                 # what to give them is this row; a child who will not eat it is the
                 # when-to-worry line, and a plate of fish fingers is the wrong answer to
                 # "my little girl wont eat her tea" (the child words in the key reach here
                 # once "my little girl" is read as the child)
                 # ...and the refusal has to be about the meal in front of them: "the kids wont
                 # eat spicy" is what to cook for them, and its answer is still this row.
                 "wont eat her", "wont eat his", "wont eat their", "wont eat the", "wont eat it",
                 "won't eat her", "won't eat his", "won't eat their", "wont eat anything",
                 "wont eat at all", "will not eat it", "will not eat her", "will not eat his",
                 "not eating", "isnt eating", "isn't eating", "stopped eating",
                 "refuses to eat", "refusing to eat", "refusing food", "wont touch her food",
                 "wont touch his food", "off her food", "off his food", "off their food",
                 "gone off her food", "gone off his food", "gone off their food",
                 "fussy", "picky", "gagging", "choking", "swallowing")),
    # How to cook rice is deliberately not here: the method depends on the rice the line names
    # (long grain, brown, wild, basmati, in a microwave), and that is a table of its own. This file
    # keeps rice only as a keeping question, which is a different thing to ask.
    # --- pancakes, the oven timings and the small things people ask mid-cook ---
    entry("pancake-batch", (("pancake", "pancakes"),
                            ("how many", "how much", "for four", "for 4", "for six", "for 6",
                             "for eight", "for 8", "per person", "people")),
          _pancake_batch,
          # this entry is the amounts: a line that says "how do i make" asks for the method, and
          # the pancakes entry below gives it with the time, so this one stays off those lines.
          avoid=STORAGE + ("how do i make", "how to make", "recipe", "method", "how do i cook")),
    entry("lasagne-time", (("lasagne", "lasagna", "macaroni cheese", "shepherds pie",
                            "cottage pie"),
                           ("how long", "oven", "time", "temperature", "day before", "ahead",
                            "assemble", "prepare", "morning", "cook")),
          "Bake a lasagne at 190C (170C fan) for 35 to 40 minutes, until it bubbles at the edges. "
          # the keeping clause is its own sentence, with no figure in it: the answer to the
          # follow-up "how long does it keep in the fridge" is the keeping entry, and a duration
          # sitting in the same sentence as "keep ... in the fridge" was being read back as the
          # keeping time ("15 minutes.")
          "Made ahead, cover it and keep it in the fridge. Cook it from cold with foil over the "
          "top for the first 25 minutes, and give it 15 minutes extra so the middle is hot.",
          bias=1, avoid=STORAGE),
    entry("turkey-buy", (("turkey", "goose"),
                         ("buy", "when", "christmas", "order", "days", "defrost", "thaw")),
          "Order a fresh turkey to collect on the 23rd or the morning of the 24th, and a frozen one "
          "to come out of the freezer 3 to 4 days before for a big bird. Allow 20 minutes per 500g "
          "plus 20 at 180C (160C fan), and rest it 30 minutes under foil and tea towels.",
          # "days" is a key word here, so the storage words below are the ones to keep out.
          # The bird already in the kitchen is the other direction: "i have some turkey left from
          # christmas" and "there is turkey left over" are leftovers, not an order for another
          # one, and the leftover-turkey row below answers them.
          avoid=("keep", "keeps", "keeping", "fridge", "last", "lasts", "left out", "left after",
                 "left from", "left over", "use by", "gone off", "still ok", "safe")),
    entry("leftover-turkey",
          ("turkey", ("left over", "left", "leftover", "leftovers", "spare", "half a",
                      "already cooked", "cold", "from christmas", "after christmas")),
          "Shred or slice the cold turkey: it is the best part of the bird, and it goes into "
          "sandwiches, a salad with mayonnaise and lemon, a curry, risotto or soup for the last two "
          "minutes, or a pie under pastry. Keep it in a covered tub in the fridge for up to 3 days, "
          "reheat it once until piping hot all the way through, and simmer the stripped carcass "
          "with an onion and a carrot for 30 minutes to make stock.",
          # the safety question, the keeping question, the weight question and the order for a
          # fresh bird all have rows of their own, and this one is only what to do with the meat
          avoid=("safe", "safely", "how long", "bin", "smell", "smells", "sick", "pregnant", "dog",
                 "cat", "freezer", "freeze", "frozen", "left out", "overnight", "all night",
                 "hour", "hours", "on the counter", "on the side", "counter", "worktop",
                 "room temperature", "reheat", "reheated", "microwave", "warm up", "twice",
                 "buy", "order", "defrost", "thaw", "weight", "size", "per person", "roast",
                 "oven", "temperature", "when should i",
                 # a line that asks for a dish is the meal table's: "i have turkey left, what can
                 # i make" wants the traybake rather than what to do with the meat in general
                 "make", "recipe", "recipes", "ideas", "cook with")),
    entry("turkey-size", (("turkey", "goose"),
                          ("how big", "size", "much", "many", "per person", "people", "for 4",
                           "for four", "for 6", "for six", "for 8", "for eight", "for 10",
                           "for ten")),
          "Allow about 500g of turkey per person, a bit more if you want leftovers: 4kg feeds 8 "
          "comfortably, 5kg feeds 10. Check the label for the weight once it is stuffed, and buy "
          "the bird rather than a crown if you want the legs for a curry afterwards.",
          # The country and the bird share a name. "how much cash should i take to turkey" and
          # "how much money should i take to turkey" were answered with the weight of the bird:
          # the money words are the holiday question (money-abroad), and the size of a bird is
          # asked with people, kilos or "per person", never with cash.
          avoid=STORAGE + ("cash", "money", "currency", "spending", "spending money", "abroad",
                           "holiday", "lira", "hotel", "flight")),
    entry("banana-bread", ("banana", ("bake", "bread", "cake", "brown", "overripe", "use up",
                                      "recipe", "make")),
          "Brown bananas are perfect for banana bread: mash 3 of them with 100g melted butter, 150g "
          "sugar, 2 eggs and 200g self-raising flour, and bake at 180C (160C fan) for about an hour. "
          "It keeps 4 days in a tin and freezes well.",
          bias=1,
          # "my bananas go brown before i can eat them" asks how to slow ripening, and main's
          # banana-ripe answers it; a making word is what makes this a bake line. Black and
          # overripe bananas are main's banana-overripe, which gives the same recipe with a
          # freezing tip, so this entry only takes the brown ones.
          # A pancake is not a loaf: "how do i make banana pancakes" is the banana-pancake line
          # (2 bananas, 2 eggs, a spoon of flour), and "banana" plus "make" alone took it here.
          avoid=KEEPING + ("why", "slow", "slower", "faster", "stop", "last longer", "keep them",
                           "keeps them", "before i can", "ripen", "ripens", "ripening", "black",
                           "overripe", "over ripe", "too ripe", "mushy", "gone off", "left over",
                           "pancake", "pancakes", "pancake batter", "crepe", "crepes",
                           "flapjack", "waffle", "waffles",
                           # A banana plant is not a banana: "banana plant leaves turning
                           # brown" is a houseplant fault, and this row took it on "banana" and
                           # "brown" and answered with the loaf.
                           "plant", "plants", "tree", "palm", "leaves", "leaf", "soil", "grow",
                           "growing", "houseplant", "potted") + NO_SUGAR),
    entry("party-food", (("party", "buffet", "picnic", "birthday"),
                         ("food", "snack", "nibbles", "ideas", "make", "cook", "menu", "take",
                          "bring", "feed", "kids")),
          "Cheap food that people finish and that travels: a big bowl of pasta salad, sausage "
          "rolls or sausages on sticks, cheese and crackers, and a tray of fairy cakes. Keep it to "
          "things you can make the day before, and buy the paper plates.",
          # "party games for kids" reached this row on the words party and kids and got a buffet,
          # which is the other half of the same afternoon: a line that says games is a games
          # question, and entertainment.py answers it.
          avoid=("game", "games", "play", "playing", "activities", "activity", "entertain",
                 "entertainment", "pass the parcel", "musical chairs", "treasure hunt", "prize",
                 "prizes", "bored", "keep them busy") + _ON_A_FLIGHT,
          guard=_not_a_trip),
    # --- drinks -------------------------------------------------------------
    entry("coffee-less", ("coffee", ("less", "afternoon", "instead", "alternative", "replace",
                                     "cut", "too much", "drink less")),
          "Try a strong decaf, or a rooibos or barley-cup drink if you want the ritual without the "
          "caffeine. Green tea or a sparkling water with lemon work too; the slump at 3pm is often "
          "dehydration and a walk as much as coffee.",
          # "how many milligrams of caffeine in a mug of filter coffee" is a dose question
          # (measures.py's caffeine-per-drink), not a cut-down question: the word "caffeine" was
          # one of this entry's moments and made the amount ask look like the habit ask.
          # "how do I make my coffee less bitter" has "less" in it but asks about taste, which
          # is measures.py's coffee-taste question.
          avoid=("bitter", "sour", "taste", "tastes", "tasting", "burnt", "grind", "grinder",
                 "water", "brew", "brewing", "beans", "strength", "strong",
                 # "how much coffee is too much" is the daily-limit question, not the habit
                 # one: the safe intake answer lives in measures.py.
                 "how much", "limit", "milligrams")),

    # The other half of the same word. Bitterness and sourness are the two ends of the same dial,
    # so one answer covers both: it is over-extracted or under-extracted, and the fix is the
    # grind, the water and the time - never "drink decaf instead", which is what the row above
    # gave a person asking how to make their coffee taste better.
    # Used grounds are not the brew: "what can i make with coffee grounds" is about the spent
    # stuff, so the phrase is the key and not the bare word, which is also a football ground.
    entry("coffee-grounds",
          (("coffee grounds", "used coffee grounds", "spent coffee", "leftover coffee grounds",
            "coffee grouts"),
           ("what can i", "make", "use", "do with", "compost", "garden", "plants", "fridge",
            "smell", "smells", "smelly", "scrub", "clean", "sink", "drain", "bin", "good for",
            "keep")),
          "Put them to work rather than down the sink: a handful of used grounds goes in the "
          "compost or round plants that like a little acid - blueberries, camellias, hydrangeas - "
          "and a small dish of dry ones in the fridge takes up smells for a couple of days. They "
          "also make a gritty paste for a stained sink or a scorched pan, and a weak brew poured "
          "over the garden is fine once it is cold. Keep them out of the drain, where they set "
          "like cement, and off seedlings in a thick layer, which stops water getting through.",
          bias=1),
    entry("coffee-bitter", (("coffee", "espresso", "americano", "cafetiere", "french press",
                             "instant coffee"),
                            # a strength question ("what coffee is less strong") is a measure,
                            # not a fault, so the strength words stay out of this key
                            ("bitter", "sour", "burnt", "burning", "awful", "horrible", "nasty",
                             "tastes bad", "taste bad", "grind", "brewing")),
          _coffee_fault,
          bias=1,
          # The words stay out of the key below rather than in an avoid list: "cake" is one slip
          # from "cafe", and the misspelt-avoid guard would then turn down "coffee at home like a
          # cafe" in a cup that tastes bitter.
          avoid=("caffeine", "decaf", "cut down", "less coffee", "quit", "give up", "sleep",
                 "pregnant", "blood pressure", "heart", "anxious", "jitters")),
    entry("tea-brew", (("tea", "green tea", "teabag", "teabags", "tea bag", "tea bags",
                        # the drink under its everyday names, without the word "tea" in the line:
                        # "how do i make a proper brew" and "how do i brew a decent cuppa" reached
                        # nothing at all. "brew" was in the second group and always was: it never
                        # helped, because the first group had no word for the drink.
                        "brew", "brews", "brewing", "cuppa", "cuppas", "pot of tea", "flask",
                        "thermos"),
                       ("bitter", "sour", "stewed", "brew", "how long",
                        "make", "taste", "tastes", "steep", "weak",
                        "strong", "stronger", "watery", "temperature",
                        # a pot, an iced glass and a cloudy cup are the same subject brewed
                        # another way, and each has its own answer inside the row
                        "pot", "teapot", "iced", "ice", "cloudy", "scum", "film",
                        "proper", "decent", "method", "perfect", "lovely",
                        # A request for a cup is a request for a cup: "can i have a cup of tea"
                        # names the drink and asks for it, and the brewing answer is the one a
                        # person wants. Without these the line fell through to the caffeine row
                        # and was told the daily safe limit for the thing it had just asked for
                        # (royal-zipper, #8152): five shapes, all of them a request, all of them
                        # answered with 400mg a day.
                        "can i have", "can i get", "could i have", "could i get", "may i have",
                        "i want a", "i'd like", "id like", "ill have", "i'll have",
                        # "how do you like your cup of tea" is the drink, not the expression:
                        # the idiom row stands the line down and on main it fell to the idiom's
                        # own definition through the bare key. Milk first or last is the answer
                        # that line wants.
                        "how do you like")),
          _tea_reply,
          # "tea" is also the evening meal in Britain, so "what shall I make for tea" is a dinner
          # question, not a kettle one: the brew answer needs a word that names the drink.
          ask=("brew", "brewing", "steep", "steeped", "bitter", "sour", "stewed", "taste",
               "tastes", "weak", "strong", "stronger", "watery", "green tea", "black tea",
               "make tea", "tea bag", "tea bags", "teabag", "teabags", "cup", "mug", "kettle",
               "milk", "sugar", "temperature",
               # "how do i make a pot of tea" and "how do i stop tea going cloudy" name the drink
               # and the making, but their words are not in the list above on their own
               "pot of tea", "teapot", "teapots", "iced tea", "ice", "cloudy", "cup of tea",
               "mug of tea", "hot water", "proper cup", "decent cup",
               # a flask or a thermos of tea is brewed the same way and then kept, so the times
               # are the answer it wants: "how do i make a flask of tea" reached nothing at all
               "cuppa", "cuppas", "flask", "thermos",
               # the same request shapes, asked in the sentence rather than in the key
               "can i have", "can i get", "could i have", "could i get", "may i have",
               "i want a", "i'd like", "id like", "ill have", "i'll have", "how do you like",
               # steeping under its other name is the making too: "how long to infuse loose leaf
               # tea" reached nothing, and the salad row took it on the word "leaf"
               "infuse", "infusing", "infused", "loose leaf", "loose leaves", "leaf tea"),
          # "what can i make with teabags" is a drink question though it is worded as a meal
          # one: the brew answer outranks the ten-minute dinners by one step.
          bias=1,
          # "brew" now opens this row on its own, and a brew is also a beer or a coffee: those
          # have their own answers and are not tea times.
          avoid=("coffee", "coffees", "espresso", "cafe", "beer", "ale", "lager", "stout",
                 "wine", "cider", "mead", "kombucha", "homebrew", "home brew")),

    # The milk in a cup of tea is the one part of a brew that is asked about on its own, usually
    # as a two-word follow-up ("milk first or last") that never says the word tea. `tea-brew`
    # lists "milk" under ask= but no milk wording in its key, so these lines reached whatever
    # other row owned the word: the nutrition card ("milk first or last"), the caffeine limit
    # ("how much milk in a cup of tea") and even the white sauce ("what milk for tea").
    entry("tea-milk",
          (("milk first", "milk in first", "milk last", "milk in last", "milk go in",
            "milk goes in", "milk in before", "milk then", "milk or tea", "tea or milk",
            "milk in a cup of tea", "milk in a mug of tea", "milk in tea", "milk in my tea",
            "milk for tea", "milk with tea", "milk for a cup of tea", "milk in a brew",
            # the subject on its own, because the natural wordings put a word between them:
            # "what milk is best for tea", "what milk should i use for tea", "is oat milk good
            # in tea", "how much milk should i put in tea", and none of those reached this row.
            # The second group does the work of keeping it to tea: a line about milk on its own,
            # or milk in coffee, in porridge or in a sauce, has no tea in it to meet this.
            # The plant milks are named because the pantry answers "what can i make with oats"
            # on the same two words: "is oat milk good in tea" was porridge.
            "milk", "oat milk", "soy milk", "soya milk", "almond milk", "plant milk",
            "skimmed milk", "semi skimmed milk", "whole milk", "milk in my brew"),
           # `tea` is the word that keeps this to a brew: with a loose `what`, `best`, `use` or
           # `much` in the second group instead, "what can i cook with milk" met the bare `milk`
           # of the first group and was answered with the order of a cup of tea.
           # "go in" and "goes in" are not here: the first group already holds "milk go in"
           # and "milk goes in", the order word comes with them ("... first", "... before"),
           # and on their own they took every line shaped "milk goes in <place>": "does milk
           # go in the freezer" lost its freezing answer to the order of a cup of tea.
           ("first", "last", "before", "after", "order", "tea", "cup of tea", "mug of tea",
            "brew", "cuppa", "stir")),
          # The order for the bare question, and the half that was asked first for the other
          # two: `_tea_milk_reply` puts the amount or the kind in front.
          _tea_milk_reply,
          # A brew in the conversation is enough for the key to meet, so a terse answer to the
          # offer of one - "milk and one sugar", "white with two" - was read as a question
          # about the brew and got the whole order of a cup. Naming the milk is only a question
          # when the line also asks: how much, which kind, or which goes in first. A word of
          # the ask has to be in the line, so a preference stays with the small talk.
          ask=TEA_MILK_ASK,
          # a cup of coffee, a bowl of porridge, mash, a white sauce and a baby's bottle all have
          # a milk question of their own, and a recipe is not a brew
          avoid=("coffee", "porridge", "cereal", "mash", "potato", "potatoes", "sauce",
                 "recipe", "cake", "scone", "scones", "bread", "rice pudding", "custard",
                 "baby", "babies", "newborn", "formula", "breast", "breastfeeding", "bottle",
                 "latte", "cappuccino", "flat white", "milkshake", "smoothie", "allergy",
                 "allergic", "intolerance", "lactose", "calcium", "calories", "calorie",
                 "caffeine", "protein", "pregnant", "curdl", "split", "freeze", "frozen",
                 "gone off", "off", "use by", "cloudy", "cloudiness", "scum", "film",
                 "murky",
                 # `tea` is an alternative in the second group, not a requirement, so a bare
                 # `milk` plus an order word (`first`, `last`, `before`) reached this row from
                 # any pan: "does the milk go in first for scrambled eggs" and "which goes in
                 # first the milk or the flour" were told "Tea first, milk last, in a mug". A
                 # dish word stands the row aside and leaves the line to the row that owns it.
                 ) + _TEA_MILK_DISH,
          bias=1),

    # The milk in a coffee is the same question as the milk in a tea, and it had no row: the brew
    # row above stands down for coffee, the barista row below stands down for "best" and "which",
    # and the pantry read "oat milk" as oats and milk, so "is oat milk good in coffee" and "what
    # milk is best for coffee" were both handed a method for porridge and a bag of beans to buy.
    # Asked about the milk in a cup of coffee, not about coffee: the second key group is the drink,
    # and the ask holds the words that make it a question about what goes in the cup.
    entry("milk-for-coffee",
          (("milk",), ("coffee", "coffees", "latte", "lattes", "cappuccino", "flat white",
                       "espresso", "americano", "mocha", "macchiato")),
          _the_milk_for_a_coffee,
          # a preference ("milk, one sugar") is not a question, and the amount in the cup, the
          # caffeine, a machine, a bag of beans and whether coffee is good for you all have rows
          ask=("which", "what", "best", "good", "better", "ok", "should i", "can i", "could i",
               "do i", "does", "is", "are", "worth", "instead of", "rather than", "goes in",
               "go in", "use", "put in", "oat milk", "soy milk", "soya milk", "almond milk",
               "plant milk", "skimmed", "semi skimmed", "whole milk", "barista", "taste",
               "tastes", "split", "curdle", "froth", "foam"),
          # "how much coffee should i drink" is a caffeine limit and "does coffee break a fast" is
          # the fast: neither is a question about the milk, and the milk word is only carried in.
          avoid=("too much", "fast", "fasting", "calorie", "calories",
                 "caffeine", "pregnant", "pregnancy", "breastfeeding", "sleep", "anxiety",
                 "blood pressure", "stain", "stains", "machine", "beans", "bag", "buy", "buying",
                 "price", "cost", "costs", "shop", "cafe", "healthy", "good for you",
                 "bad for you", "before bed", "decorate", "art", "paint", "tables", "table",
                 "book", "books", "shop", "grinder", "descale", "clean"),
          # The caffeine rows still take "how much milk in a cup of coffee" and "my milk split in
          # my coffee", which are their lines to lose: the row above answers the kind of milk, the
          # amount and the split, and a fence on the caffeine rows is the next change, not this one.
          bias=1),

    # "how much water should i put in the kettle for two cups of tea" reached nothing: the brew
    # entry is about temperature and time, not about how full the kettle goes.
    # The cook_kit row "tea-water" does the sum for the mugs you name; this one is the flat
    # "a mug is about 250 ml". One id for two rows means one of them answers unseen.
    entry("tea-water-mug",
          # "kettle" only: "how do i make a cup of tea" is the brew times, and a key that
          # carried "cup of tea" took it.
          # The second group wants the shape of the question, not the loose words: with bare
          # "how much", "water" and "much" in it, "how much does a kettle cost", "how much
          # electricity does a kettle use" and "my kettle water tastes of plastic" all got the
          # fill advice.
          (("kettle",),
           ("how much water", "much water", "how full", "how far to fill", "fill the kettle",
            "filling the kettle", "cups of water", "how much to fill", "full to fill")),
          "About 250ml a mug and a splash more for what boils off, so roughly 600ml for two mugs - "
          "fill one mug and tip it in twice, then a little extra. Only boiling what you need is "
          "the quickest saving in the kitchen and it scales the kettle up more slowly, but don't "
          "go under the element's minimum or the kettle will click off before it boils.",
          # "how many calories in a cup of tea" and "how many cups of tea is too many" are a
          # nutrition question and a caffeine one, not how full the kettle goes.
          avoid=("descale", "limescale", "scale", "clean", "vinegar", "citric", "broken",
                 "repair", "boil dry", "element", "filter", "hard water", "calorie", "calories",
                 "caffeine", "sugar", "milk", "too many", "how many", "strong", "how long",
                 # a kettle that is faulty, costly or tastes of something is not a fill question
                 "cost", "costs", "price", "electricity", "energy", "buy", "buying", "best",
                 "which kettle", "plastic", "taste", "tastes", "tasting", "slow", "leak", "leaks",
                 "switch", "switching", "switches"),
          bias=1),

    # "how do i make a flat white" was answered "Wash white cotton at the hottest temperature
    # the label allows" - the whites wash keys "make" and "white", and a coffee has both. The
    # drink names are the first key part, because each of them is a coffee and nothing else, and
    # the second part is the making: how, froth, steam, at home, the machine.
    entry("coffee-at-home",
          (("flat white", "latte", "lattes", "cappuccino", "cappuccinos", "macchiato", "mocha",
            "americano", "espresso", "steam milk", "steaming milk", "milk for coffee",
            "coffee milk", "milk frother", "steam wand", "milk steamer"),
           ("how do i make", "how to make", "how do you make", "make a", "make one", "make it",
            "how do i froth", "froth", "frothing", "how do i steam", "steam", "steaming",
            "at home", "the milk", "my milk", "properly", "like a cafe", "like a coffee shop",
            "no machine", "without a machine", "machine")),
          _a_coffee,
          # a caffeine limit, a coffee before bed, a machine to buy, a price and a calorie count
          # are all other questions with the drink's name in them
          # "how do i froth milk for coffee" already has its own card - cold milk in a lidded jar,
          # shaken and microwaved - which is the better answer for a person with no machine, so
          # the froth words stand this row down and keep it
          avoid=("froth milk", "froth the milk", "frothy milk", "milk froth", "frothed milk",
                 "frothing milk", "best for frothing",
                 "caffeine", "how much", "too much", "how many", "before bed", "sleep",
                 "pregnant", "pregnancy", "breastfeeding", "heart", "blood pressure", "anxiety",
                 "calories", "calorie", "healthy", "healthier", "bad for", "good for",
                 "cost", "costs", "price", "buy", "buying", "best", "which", "recommend",
                 "decaf", "instant", "beans", "ground", "grinder", "pod", "pods",
                 "nespresso", "clean", "cleaning", "descale", "shop", "cafe",
                 "barista", "job", "stain", "stains", "white t shirt", "shirt"),
          bias=1),
    # --- kitchen kit, knives and smells --------------------------------------
    # Keeping the edge is a knife question and the kitchen room routine is not: "how do i keep my
    # kitchen knives sharp" has "kitchen" and "how" in it, and the room answered it with the
    # order to clean a kitchen in. The room stands down for kitchen kit now, and the bias settles
    # the tie on the lines it still reaches.
    # A honing steel is asked about by name, and "properly" is how people ask: the row keyed
    # only the word "steel", so "how do i use a honing steel" and "what is a honing steel" were
    # a search hedge. No room word in the key: an earlier version keyed "kitchen", and with
    # "dull" in the second part it then answered a dull kitchen floor, dull paint and dull
    # lighting instead of the knife.
    entry("kitchen-knives", (("knife", "knives", "blade", "honing steel", "sharpening steel"),
                             ("sharp", "sharpen", "sharpening", "blunt", "dull", "steel", "hone",
                              "honing", "properly", "the right way")),
          ("Ten strokes a side on a steel brings a blunt edge back for a week; a whetstone, coarse "
           "side then fine, once a month is what actually sharpens it. Hold the blade at 20 "
           "degrees, keep the fingers of your other hand behind the edge, and wash and dry it by "
           "hand: a dishwasher blunts a knife and splits a wooden handle."),
          bias=1),
    # Rust is the same repair on a tray, a tin and a knife, and none of them had an answer: "my
    # baking tray is rusty" and "my knife has rust spots" were both a shrug, and "how do i stop my
    # knife going rusty" got the chemistry of iron oxide from the science domain and no fix. The
    # second key group is what keeps this entry to the kitchen, so a rusty nail, a rusty bike and
    # rusty German stay where they belong.
    entry("rusty-kitchen-gear",
          # The bare word "kitchen" used to stand in the second group, and it made any rust line
          # that mentions the kitchen a baking tray: "my kitchen tap is rusty" and "the kitchen
          # radiator is rusty" were told to bake it at 200C to seal it again. A tap and a radiator
          # are not kitchen kit, so the kitchen tools are named as the phrases people write.
          (("rust", "rusty", "rusting", "rusted", "rusts"),
           ("baking tray", "baking trays", "tray", "trays", "tin", "tins", "cake tin",
            "muffin tin", "loaf tin", "tart tin", "bun tin", "roasting tin", "sheet pan",
            "bakeware", "springform", "knife", "knives", "blade", "cutlery", "fork", "forks",
            "spoon", "spoons", "whisk", "sieve", "grater", "pan", "pans", "wok",
            "tin opener", "can opener", "kitchen knife", "kitchen knives",
            "kitchen scissors", "kitchen tongs", "utensil", "utensils")),
          ("Scrub the rust off with a paste of bicarbonate of soda and water or a green scouring "
           "pad, rinse it and dry it at once. A little rust is not poisonous, but a tray that has "
           "rusted through will keep flaking into food: scrub it, rub a film of oil over it and "
           "bake it at 200C for 15 minutes to seal it again, and replace it once the metal is "
           "pitted. Knives, forks and tins rust because they sit wet, so wash and dry them by "
           "hand and never leave them in the sink or put them through the dishwasher."),
          bias=1),
    entry("board-smell", (("chopping board", "board", "worktop", "wooden spoon", "wooden spoons",
                           "spoon", "spoons", "utensils"), ("smell", "smells", "smelly",
                                                                   "onion", "garlic", "fish",
                                                                   "clean", "stain")),
          ("Scrub it with half a lemon and a big pinch of salt, rinse in the hottest water you "
           "have and dry it standing up: that lifts onion, garlic and fish out of wood or "
           "plastic. Plastic boards can go through the dishwasher, wooden ones should never."),
          # bare "board" plus "clean" was worth four points, so "how do i clean skirting boards"
          # was answered with a lemon and a pinch of salt. The boards that are not kitchen kit
          # stand it down; a chopping board, a worktop and a wooden spoon are untouched.
          avoid=("skirting", "skirting board", "skirting boards", "floorboard", "floorboards",
                 "ironing board", "whiteboard", "notice board")),
    entry("fish-smell", (("fish", "fishy", "cooking smell"), ("smell", "smells", "smelly", "stink",
                                                              "get rid", "kitchen", "house")),
          ("Boil a pan of water with a few slices of lemon or a splash of vinegar for 10 minutes "
           "with the window open: that is what clears cooking smells out of the air. Wash the pan, "
           "the board and the bin straight away, and leave a bowl of bicarbonate of soda in the "
           "fridge overnight if the smell got in there."),
          # a fish tank that smells is where a live fish lives, and the tank has its own answer:
          # "my fish tank smells" was told to boil up a pan of lemon
          avoid=("tank", "fish tank", "aquarium", "goldfish", "pond", "ponds", "fish bowl",
                 "tropical fish", "pet fish")),
    # "this fish tastes fishy" is a cooking question with no smell and no kitchen in it, so the
    # smell row could not take it and nothing did: it came back "A fish. What's it like to live
    # with?" - a fish is a pet. The taste is the whole ask here, so the taste words carry it.
    entry("fish-tastes-fishy",
          (("fish", "fishes", "cod", "salmon", "mackerel", "haddock", "tuna", "prawns", "prawn",
            "trout", "herring", "sardines", "sprats"),
           ("tastes", "taste", "tasting", "tasted", "fishy", "tastes fishy", "too fishy",
            "smells fishy", "strong", "strongly", "muddy", "bitter")),
          ("Judge it by the smell first, not the taste: fish that is off has an ammonia or "
           "bleach-sharp smell, dull sunken eyes and flesh that stays dented when you press it, "
           "and that goes in the bin rather than on a plate. A fish that is fresh but tastes or "
           "smells strongly of the sea is usually an oily one - mackerel, herring, sardines, "
           "salmon - and soaking it in milk for 20 minutes, or rubbing it with lemon, takes the "
           "edge off. Cook it with acid and something sharp: lemon, vinegar, capers, dill, "
           "tomatoes. Frozen fish tastes stronger than fresh, so use it in a sauce or a pie "
           "rather than on its own."),
          # the tank, the fridge and the kitchen air are other questions
          avoid=("tank", "aquarium", "goldfish", "pet", "bowl", "pond", "kitchen smells",
                 "house smells", "get rid of", "cooking smell", "smell in", "gone off",
                 "still ok", "use by", "shelf life", "mouldy")),
    entry("bread-stale", (("bread", "loaf", "baguette", "rolls"),
                          ("stale", "dry", "hard", "yesterday", "keep fresh", "stop it going",
                           "going stale", "revive", "soft again"),
                          # the ask, so that a loaf that is dry inside a question a person asked
                          # about it - "is it ok to eat bread thats gone a bit hard", "can i eat
                          # this stale loaf" - is this row's line and not the mould notice's.
                          # The row needs a word that says the loaf has dried out, so the ask is
                          # on `ask=` below and the plain "is my bread still ok" stays a fresh
                          # question for the row that answers it.
                          ("is it ok", "is it still", "ok to eat", "okay to eat", "can i eat",
                           "can i still", "still ok", "still okay", "still good", "safe to eat",
                           "eat it", "use it", "bin it", "throw it", "ruined", "gone a bit",
                           "what can i do with", "what do i do with", "hard", "dry")),
          ("Stale bread is dry, not spoilt: sprinkle it with water and warm it in a 180C oven for "
           "6 to 8 minutes and it comes back close to fresh, and a dry loaf is the right bread for "
           "toast, croutons, breadcrumbs or a panzanella. To stop it happening, keep the loaf "
           "whole and cut slices as you need them, in a paper bag or a bread bin rather than the "
           "fridge, and freeze half of it sliced on day one."),
          ask=("stale", "dry", "hard", "hardened", "tough", "yesterday", "soft again", "revive",
               "gone a bit hard", "gone hard", "gone dry", "dried", "going stale"),
          guard=_not_how_to_keep_it_fresh,
          bias=2),
    # The prevention answer is main's, and it has to stay: "how do i stop my bread going mouldy"
    # is a keeping question and this entry answers it. The bin-it question is a different line -
    # "can i cut the mould off" - and it gets its own entry below, so neither has to hedge.
    entry("bread-mouldy", (("bread", "loaf"),
                           ("mouldy", "mould", "mold", "green", "freeze", "bin",
                            # People describe what they can see rather than the word "mould":
                            # "my bread has blue spots" was answered with beans on toast on main
                            # `e06365c`, because bread is a food word and "has" is a having.
                            "blue spots", "white spots", "black spots", "green spots",
                            "spots", "speckled", "specks", "blue fluff", "white fluff",
                            "green fuzz", "fuzzy", "furry", "fur", "spores", "blue", "greenish")),
          ("Warmth, damp and the plastic bag it came in are what mould needs, so a loaf in a warm "
           "kitchen goes green within days. Keep it in a paper bag or a bread bin, freeze half of "
           "it sliced on day one, and never keep it in the fridge unless you only ever toast it.")),
    entry("bread-mould-cut", (("bread", "loaf", "loaves"),
                              ("gone off", "off", "smells", "smell", "smelt", "slimy",
                               "still ok", "is it ok", "is it still", "ok to eat", "eaten",
                               # the date on the bag is the same question as "is it still ok", and
                               # "is my bread out of date" was reaching no row at all
                               "out of date", "past its date", "past the date", "use by",
                               "use by date", "best before", "gone past",
                               "cut the mould off", "cut it off", "scrape it", "scrape the mould",
                               "eat around", "eat it", "cut", "cutting", "scrape", "salvage",
                               "trim", "still eat", "safe", "ok", "okay", "bin", "throw",
                               "away")),
          ("Don't cut the mould off a loaf and eat the rest: the threads reach further than the "
           "green you can see, so bin it. Warmth, damp and the plastic bag it came in are what "
           "mould needs, so a loaf keeps longer in a paper bag or a bin, with half of it frozen "
           "sliced on day one. Hard cheese is the exception - cut an inch around the mould and the "
           "rest is fine."),
          # the prevention line names no cutting, and the keeping entry owns it
          avoid=("stop", "prevent", "going mouldy", "keep it", "store", "how do i keep",
                 # the bin is not the loaf, and the words after the compound noun say which one
                 # the line is about: "my bread bin is mouldy" and "the bread bin is green
                 # inside" say what the bin is like, so they are the cleaning entry's
                 # washing-out answer. "mouldy bread in my bread bin" and "the bread in my bin is
                 # mouldy" say what the bread is like, and stay here.
                 "bread bin is", "bread bin has", "bread bin smells", "bread bin stinks",
                 # the bin being cleaned or emptied is the washing-out answer's, and "how do i
                 # clean a bread bin" and "the bin smells of old bread" were both told not to eat
                 # the mouldy loaf. The bin is the subject in those lines, not the bread.
                 "clean the bin", "clean a bread bin", "cleaning the bin", "clean my bread bin",
                 "wash the bin", "wash a bread bin", "washing the bin", "bin smells", "bin stinks",
                 "empty the bin", "emptying the bin",
                 "bread bin was", "bread bin went", "bread bin looks", "bread bin gets",
                 # the same rule with the mould said first: "there is mould in my bread bin"
                 # and "mould at the bottom of the bread bin" name the container, not the loaf,
                 # and were told to bin the loaf and eat none of it. The bin is what gets washed.
                 "mould in my bread bin", "mould in the bread bin",
                 "mould inside my bread bin", "mould inside the bread bin",
                 "mould at the bottom of the bread bin", "mould at the bottom of my bread bin",
                 "lunchbox", "lunch box", "container")
          # a pack date is the keeping question, not the mould one: "is it ok to eat
          # bread past the date" was answered "don't cut the mould off a loaf" on main
          + PACK_DATE,
          # and a loaf that is only dry has not been spoilt: the stale row says the oven trick
          guard=_not_just_a_hard_loaf,
          bias=1),
    # Freezer shelf life, as its own answer. "How long can beef stay in the freezer" was answered
    # with the fridge numbers, and "how long can fish stay in the freezer" with the searing time,
    # because nothing here read "stay ... in the freezer" as a keeping question.
    entry("freezer-time",
          (("freezer", "freeze", "frozen", "freezing"),
           ("how long", "long", "keep", "keeps", "last", "lasts", "stay", "stays", "months", "year",
            "years", "safe", "still good")),
          FREEZER_KEEP,
          ask=KEEP_ASK,
          # cooking, thawing and the fridge are other questions; the foods below have a better
          # answer of their own, and chicken's shelf life is chicken-storage's line.
          avoid=("cook", "cooking", "oven", "roast", "bake", "baking", "reheat", "fry", "air fryer",
                 "boil", "microwave", "take", "defrost", "thaw", "fridge", "refrigerator",
                 "worktop", "counter", "rice", "milk", "formula", "chicken",
                 # the appliance and the power cut are not shelf-life questions
                 "power cut", "powercut", "power outage", "power failure", "without power",
                 "broken", "repair",
                 "not freezing", "stopped working", "freezer last", "freezer lasts",
                 # "how long can food be out of the freezer" is the two-hour rule, not a shelf
                 # life: the keeping answer says "in the freezer, about 3 months", which is a
                 # true fact and no answer at all to food that is already out of it. The same
                 # words with "in" keep this row - "how long can beef stay in the freezer" is
                 # still its own question.
                 "out of the freezer", "left out", "leave it out", "leaving it out",
                 "left on the side", "sitting out", "stay out", "stays out", "stood out",
                 "out overnight", "all night", "overnight")),
    entry("freeze-cooked", (("freeze", "freezer", "frozen"),
                            ("mash", "mashed potato", "potato", "stew", "curry", "soup",
                             "leftovers", "chilli", "bolognese", "food", "lasagne", "lasagna",
                             "pasta bake", "casserole", "shepherds pie", "cottage pie", "pie",
                             "risotto", "paella", "gratin",
                             # The dishes people ask about that had no row of their own at all
                             # and were refused with a hedge: "can i freeze a quiche", "can i
                             # freeze meatballs", "can i freeze a frittata", "can i freeze
                             # moussaka", "can i freeze burritos", "can i freeze stuffing". They
                             # are cooked dishes like every other row here, so they take the same
                             # rule and the same keeping time.
                             "quiche", "quiches", "frittata", "frittatas", "omelette",
                             "omelettes", "moussaka", "tagine", "meatballs", "meatball",
                             "burritos", "burrito", "quesadilla", "quesadillas", "stuffing",
                             "sausage rolls", "samosas", "samosa", "spring rolls", "dumplings",
                             "fishcakes", "fish cakes", "nut roast")),
          _freeze_cooked,
          # food that is out of the freezer, or out of the fridge, is the two-hour rule's
          # question (`freshness.py`), not "can i freeze it": this row was answering "how long
          # can food be out of the freezer" with a freezing method.
          avoid=("out of the freezer", "left out", "leave it out", "leaving it out",
                 "left on the side", "sitting out", "stay out", "stays out", "stood out",
                 "out overnight", "all night")),
    entry("jacket-potato", (("jacket potato", "jacket potatoes", "baked potato",
                             "baked potatoes", "bake a potato", "bake potatoes",
                             "baking potato", "potato in the oven"),
                            ("oven", "cook", "how long", "time", "crispy", "microwave", "air",
                             "done", "know", "ready", "bake", "make", "best", "quick",
                             # the filling is the jacket's own question: "how do i fill a
                             # jacket potato" and "what goes with a baked potato" were shrugs,
                             # and a topping is not a second potato recipe.
                             "fill", "filling", "topping", "toppings", "goes with", "beans",
                             "cheese", "tuna")),
          lambda memory, understood: _jacket(understood),
          # one whole potato in its skin is not a tray of roast potatoes: "how long to roast
          # potatoes in the oven" matched this entry on potato, oven and how long, and got an
          # hour for one potato instead of the 40 to 45 minutes a tray wants.
          # "crispy" and "crunchy" used to be here, because a tray of roast potatoes is the
          # other thing people want crisp: but crisp skin on a baked potato is this entry's own
          # question, and "how do i make a jacket potato crispy" was getting the parboil-and-
          # shake method for roasties. The phrases that name this potato are ruled out of the
          # roast entry instead, so the subject decides and not the adjective.
          avoid=("roast", "roasting", "roasted", "roasties", "soggy",
                 "wedges", "chips", "parboil", "parboiled",
                 # what to put *on* a potato is the seasoning table, not the bake time or the
                 # cheese-and-beans list: "what herbs should i put on potatoes" got the fillings
                 "herb", "herbs", "spice", "spices", "seasoning", "rosemary", "thyme", "paprika",
                 "cumin",
                 # A line that cooks it *in the microwave* wants the 8 to 10 minutes on high,
                 # which `potato-microwave` already answers: "how do i make a jacket potato in
                 # the microwave" only got an hour at 200C here. The shapes are statements of
                 # method, not the bare word: "can i microwave a jacket potato" is still this
                 # entry's, because its answer is where the shortcut tip lives.
                 "in the microwave", "how long do i microwave", "how long should i microwave",
                 "how long to microwave", "how long in the microwave")),
    entry("potato-done",
          (("potato", "potatoes"),
           ("know when", "how do i know", "how can i tell", "when are they done",
            "when are potatoes", "done", "tender", "soft", "ready", "cooked", "cooked through")),
          "Test them with a knife rather than a fork: it should slide in with no resistance at all "
          "and the potato should still hold its shape. Boiled, that is 10 to 12 minutes for small "
          "new potatoes, 15 to 20 for chunks and 20 to 25 for whole medium ones; a fork tells you "
          "too late, and a potato left a minute too long goes watery.",
          # a tray of roast potatoes has its own doneness ("deep gold and crusty"), and a
          # cupboard that has gone soft is a keeping question: only the boiled ones are here.
          avoid=("keep", "keeps", "keeping", "store", "storing", "last", "lasts", "gone off",
                 "sprout", "sprouting", "sprouts", "mouldy", "fridge", "freezer", "green",
                 "greening", "gone green", "gone soft", "sweet potato", "sweet potatoes",
                 "roast", "roasting", "roasted", "roasties", "crispy", "crunchy", "oven",
                 # the microwave and the air fryer are their own timings: "how do i cook
                 # potatoes in the microwave" is not a question about testing them
                 "microwave", "microwaving", "microwaved", "air fryer", "air fry", "airfryer",
                 "air fried")),
    entry("potato-microwave",
          (("potato", "potatoes"),
           ("microwave", "microwaving", "microwaved")),
          "Prick a whole potato all over and give it 8 to 10 minutes on high, turning it halfway. "
          "Chunks or small new potatoes take 5 to 6 minutes with a splash of water in the dish. "
          "Let it stand a minute before you cut into it, and use a knife to check it really is soft "
          "all through.",
          avoid=("sweet potato", "sweet potatoes", "yam", "oven", "roast", "roasting", "bake",
                 "baked", "chip", "chips", "salad", "grow", "plant", "seed potato")),
    # Corn is the third vegetable with its own microwave time, and it was a punts: "how do i
    # microwave corn" and "can you microwave sweetcorn" reached nothing, because the staple method
    # is fenced off the microwave (its own rows hold those timings) and no row held corn's.
    entry("corn-microwave",
          (("corn", "sweetcorn", "corn on the cob", "corn cobs", "corn cob"),
           ("microwave", "microwaving", "microwaved", "micro")),
          "In the microwave a cob takes 3 to 4 minutes on full power for one and 5 to 6 for two: "
          "leave it in its husk, or wrap it in a sheet of damp kitchen paper, and turn it once "
          "halfway. Give it a minute to stand before you butter it, because it carries on cooking. "
          "Loose kernels in a covered bowl with a splash of water take 2 to 3 minutes, stirred "
          "halfway, and frozen sweetcorn the same plus a minute.",
          # a tin, a salad and a field are not a cob; and popcorn has its own answer
          avoid=("popcorn", "popping corn", "cornflour", "corn flour", "corned beef", "hash",
                 "tinned", "tin of", "salad", "salsa", "grow", "growing", "plant", "sow",
                 "sweet corn plant", "field", "tortilla", "bread", "fritter", "fritters")),
    entry("potato-airfryer",
          (("potato", "potatoes"),
           ("air fryer", "air fry", "airfryer", "air fried", "airfried")),
          "Air-fry potato chunks at 200C for 20 to 25 minutes, shaking the basket halfway: cut them "
          "to the same size, keep them in one layer and toss them in a little oil first. Parboiled "
          "ones take 12 to 15 minutes, and a whole jacket potato about 40 minutes at 190C.",
          # `dishes.plan-ideas` scores 5 on the same line ("air fryer" and "how long") and its
          # bias is -2, so with equal scores the air-fryer dinner list beat this entry and "how
          # long do potatoes take in the air fryer" got "chicken thighs 25 minutes".
          avoid=("sweet potato", "sweet potatoes", "yam", "grow", "plant", "seed potato"),
          bias=1),
    # --- basics a person asks in their first year of cooking --------------------
    # "how do i make mash", "how do i make pancakes", "how do i cook burgers" and the fish finger
    # packet all got a shrug on main: each one is a plain method question with a short, concrete
    # answer, and none of them belongs to another entry. They pass the faults (lumpy mash, a
    # tough burger) and the buying questions, which have their own answers.
    entry("pancakes", (("pancake", "pancakes", "pancake batter", "crepe", "crepes"),
                       ("make", "recipe", "batter", "mix", "american", "fluffy", "thin",
                        "perfect", "easy", "homemade", "flat", "rise", "risen", "sink",
                        "sank", "thin", "runny",
                        # a bare "how long do i cook pancakes" was a shrug: the method sentence
                        # holds the minute a side, so the time words belong to this key too.
                        "how long", "time", "cook", "cooking", "minute", "minutes")),
          # airy-deer: "best pancake mix" and "where to buy pancake mix" are the shop product.
          # "how do i make pancake mix" still answers, because it says make and no shop word.
          _pancakes,
          # airy-deer: a diet-restricted pancake question is a swap question, and a plain batter
          # with eggs and milk in it is the one answer that cannot help.
          avoid=("buy", "shop", "shops", "supermarket", "box", "packet", "packet mix",
                 "bought", "where can i get", "without eggs", "no eggs", "eggless", "egg free",
                 "without milk", "dairy free", "vegan", "gluten free",
                 # "my pancake batter is watery" is a fault in the batter, and fix-watery knows
                 # what a batter wants; the recipe is the answer to how to make one.
                 "watery", "too thin", "too runny")),
    entry("yorkshire-pudding", (("yorkshire pudding", "yorkshire puddings", "yorkshires",
                                 "yorkshire puds"),
                                ("make", "cook", "rise", "risen", "flat", "crispy", "how",
                                 "recipe", "time", "oven", "oil", "batter")),
          "Get the tin and its oil smoking hot, 220C (200C fan), before the batter goes anywhere "
          "near it. The batter is 100g plain flour, 2 eggs, 150ml milk and a pinch of salt, rested "
          "30 minutes and poured in cold, about 1cm deep, and then the oven door stays shut for 20 "
          "minutes. Flat ones are a cool tin or a batter that was too thin.",
          # airy-deer: "how many yorkshire puddings per person" and "how do i reheat them" are
          # not the batter method, and bare "how" was pulling both in.
          avoid=("tea", "teabag", "tea bag", "dales", "terrier", "per person", "how many",
                 "reheat", "reheating", "leftover", "leftovers", "freeze", "freezer", "keep",
                 "buy", "shop", "shop bought", "supermarket", "packet",
                 # what a pudding is worth on the plate is the nutrient table's question
                 "protein", "calories", "calorie", "kcal", "carbs", "carb", "carbohydrates",
                 "sugar", "fat", "fibre", "fiber", "nutrition", "nutrients")),
    entry("burgers", (("burger", "burgers", "beef burger", "patty", "patties"),
                      ("cook", "make", "recipe", "juicy", "grill", "barbecue", "bbq", "how long",
                       "homemade", "best")),
          # true-iguana's catch: `sauce` in the key pulled "what is in burger sauce" into the patty
          # method, and a bun is bread. Neither is this answer, so they are passed on.
          "Use 20% fat beef mince, shape loose patties about 2cm thick and press a dent in the "
          "middle with your thumb so they stay flat as they cook. Over a high heat, give them 3 "
          "minutes a side for medium and rest them 2 minutes before they go in the bun. Salt the "
          "outside just before they hit the heat: salt in the mix makes them bouncy.",
          # airy-deer's catch: "best burger in london" is choosing where to eat, not cooking, so
          # the eating-out words are passed on with the sauce and the bread.
          avoid=("sauce", "bun", "buns", "roll", "rolls", "relish", "ketchup", "restaurant",
                 "restaurants", "near me", "nearby", "takeaway", "take away", "delivery", "place",
                 "london", "near") + _NO_MEAT),
    # Beef mince is the first thing in the method above, so a burger that cannot have it is a
    # different method, not the same one: before this, "how do i make burgers without mince" got
    # "use 20% fat beef mince".
    entry("burger-no-meat", (("burger", "burgers", "patty", "patties", "bean burger",
                              "veggie burger"),
                             ("without mince", "no mince", "without beef", "no beef", "without meat",
                              "no meat", "meat free", "meat-free", "vegetarian", "veggie", "vegan",
                              "lentil", "lentils", "bean", "beans", "chickpea", "chickpeas",
                              "pulse", "pulses", "mushroom", "tofu")),
          "Mash a drained tin of black beans or chickpeas with a grated small onion, a handful of "
          "breadcrumbs, a spoon of tomato puree and an egg to bind it - or a flax egg, a tablespoon "
          "of ground flaxseed in three of water, left ten minutes - then chill the mix twenty "
          "minutes so the patties hold. Shape them 2cm thick and fry 4 to 5 minutes a side, or bake "
          "them 20 minutes at 200C (180C fan). Keep them thick and turn them gently: they are "
          "softer than beef, and a thin one breaks. A spoon of smoked paprika is what makes them "
          "taste of something."),
    entry("fish-fingers", (("fish finger", "fish fingers", "fishfingers"),
                           ("cook", "oven", "air fryer", "how long", "grill", "fry", "bake",
                            "best")),
          "Straight from the freezer, 12 to 15 minutes at 200C (180C fan) on a tray, turned once, "
          "until the crumbs are crisp and the middle is hot; an air fryer does them in 10 minutes "
          "at 190C. Don't thaw them first, or the breadcrumbs slide off. Chips, peas and something "
          "sharp to dip them in."),
    entry("halloumi", (("halloumi",),
                       ("cook", "fry", "fried", "grill", "air fryer", "squeaky", "crispy",
                        "how long", "best", "pan")),
          "Slice it 1cm thick, pat it dry and fry it in a dry non-stick pan 2 minutes a side until "
          "it is golden, or grill it 3 minutes a side. Patting it dry is what gives a crust instead "
          "of steam, and turning it once keeps it from going rubbery. It is already salty, so it "
          "needs no oil or salt."),
    entry("sweet-potato", (("sweet potato", "sweet potatoes"),
                           ("cook", "oven", "roast", "bake", "boil", "air fryer", "how long",
                            "wedges", "mash", "fries", "chips")),
          _sweet_potato,
          avoid=("cook with", "cooking with", "make with", "do with", "use up",
                 "recipes", "recipe", "ideas", "idea", "dinner", "tonight",
                 "meal", "meals"),
          bias=1),
    entry("pizza-base", (("pizza", "pizza base", "pizza dough", "dough"),
                         ("base", "dough", "make", "homemade", "recipe", "rise", "no yeast")),
          "Stir 500g strong white flour, 325ml warm water, 7g yeast and 10g salt into a soft "
          "dough, knead it 8 minutes and leave it 1 to 2 hours until doubled. Stretch it thin, "
          "and bake as hot as your oven goes, 250C, for 10 to 12 minutes. With no yeast, use a "
          "flatbread base or add a teaspoon of baking powder and rest it 20 minutes."),
    entry("pulses-soak", (("chickpeas", "chick pea", "chick peas", "dried chickpeas", "beans",
                            "dried beans", "black beans", "butter beans", "kidney beans",
                            "white beans", "haricot beans", "cannellini beans", "pinto beans",
                            "split peas", "black eyed peas"),
                          ("soak", "soaking", "soaked", "overnight", "dried", "long",
                           "need to soak", "slow", "slow cooker", "how do i cook",
                           "how do you cook", "how long do i cook", "how long to cook",
                           "still hard", "still firm", "wont soften", "will not soften",
                           "not softening", "hard after", "too hard", "without soaking",
                           "no soak", "skip the soak", "quick soak", "cook", "boil")),
          _pulses,
          # "my beans are still hard after an hour" is a pulse line and dishes.py's veg-fault
          # entry reads "beans" as the vegetable, with the bias it carries for the cabbage and
          # the carrot. This one is about a bag of dried beans, so it holds the tie and the
          # fresh beans are turned away in the reply above.
          bias=2,
          # "what can I cook with chickpeas" is a meal question, and it was getting the soaking
          # fact because "cook" is in this entry's key. "recipe" is deliberately not avoided:
          # "recipe for cooking dried chickpeas" is a prep question, and avoiding it there left
          # the line with no answer at all ("Noted!").
          # lentils are in the key for "do lentils need soaking", but the first sentence here is
          # about chickpeas, and "how long do lentils take" was getting chickpea times. The lentil
          # lines have their own entry now, written about lentils.
          avoid=("coffee", "coffee bean", "coffee beans",
                 "cook with", "cooking with", "make with", "do with", "dinner", "tea", "supper",
                 "meal", "meals", "what can i make", "what should i cook",
                 # "need a cheap recipe with chickpeas" is a what-to-cook line and it was getting
                 # the soaking times, because "need" and "chickpeas" are both in this key
                 "cheap recipe", "cheap recipes", "cheap meal",
                 "what could i cook", "what could i make",
                 "lentil", "lentils", "red lentils", "green lentils", "puy lentils",
                 "brown lentils", "lentil soup", "dal", "daal", "dhal",
                 # a tin is not a bag, so a tinned line is never a soaking question. "canned" is
                 # deliberately not an avoid word: an avoid word is matched loosely, and "can"
                 # in "can i cook beans without soaking" is the same form, so it switched this
                 # entry off for every "can I" line ever asked about a pulse. The reply turns a
                 # tin away instead ("tinned", "tin of", "cans of").
                 "tinned", "tin of", "tin", "tins", "jarred",
                 # A food named with "cheap recipe" is a meal to cook, not a bag to soak: the
                 # meal entry answers it. The bare "recipe" stays out, because "recipe for
                 # cooking dried chickpeas" is this entry's own question.
                 "cheap recipe", "easy recipe", "quick recipe", "recipe with", "recipes with",
                 "recipe using", "recipe that", "recipe ideas",
                 # Keeping a pan of beans is not a bag question: "how long do cooked beans keep
                 # in the fridge", "how do i store cooked beans" and "can i freeze cooked beans"
                 # all had the keeping answer and were getting the soaking times, because
                 # "cooked" folds onto this entry's "cook".
                 # "fridge" alone is not here, or "can i soak beans in the fridge overnight"
                 # stands this row down and lands on a keeping card: a soak in the fridge is a
                 # soaking question. The keeping words either side of it are what tell the two
                 # apart, and every keeping line carries one of them.
                 "keep", "keeps", "keeping", "store", "stores", "storing", "stored",
                 "freezer", "freeze", "freezes", "freezing", "frozen", "defrost", "defrosting",
                 "reheat", "reheating", "leftover", "leftovers", "left over",
                 "last", "lasts", "gone off", "still good", "how long do they keep",
                 # the fridge phrases a keeping line actually uses: "do cooked beans need to
                 # go in the fridge" carries none of the words above, and with the bare word
                 # taken out of this list it reached the soaking times
                 "go in the fridge", "in the fridge for", "in the fridge after",
                 "fridge for", "the fridge until", "cooked beans keep", "keep in the fridge"
                 # An appliance is not an avoid word, because raw kidney beans in a slow cooker
                 # ARE this entry's safety line: the reply stands down for the other appliance
                 # lines instead, where the pot's own card answers.
                 ) + _CHEAP_AVOID),
    # Lentils are the one pulse people cook without planning: no soaking, twenty minutes, and a
    # texture that changes with the time, so they get their own times rather than chickpeas'.
    entry("lentils-cook",
          (("lentil", "lentils", "red lentils", "green lentils", "puy lentils", "brown lentils",
            "split lentils"),
           ("cook", "cooking", "boil", "boiling", "simmer", "how long", "minutes", "take",
            "takes", "soak", "soaking", "soaked", "overnight", "dried", "soft", "mushy",
            "firm", "soup", "dal", "daal", "dhal", "curry")),
          _lentils,
          # a lentil dish is a recipe, not a timer: "lentil soup recipe", "what can i make with
          # lentils" and "are lentils good for you" are three other questions.
          # keeping lentils is a different question from cooking them: "can i freeze cooked
          # lentils" wants the freezing answer, not the timetable.
          avoid=("recipe", "recipes", "what can i make", "what can i cook", "meal idea",
                 "meal ideas", "healthy", "protein", "good for you", "calories", "calorie",
                 "nutrition", "diet", "iron", "fibre", "fiber", "lose weight",
                 "freeze", "freezes", "freezing", "frozen", "defrost", "defrosting",
                 "reheat", "reheating", "in the fridge", "keep in the fridge",
                 "how long does it keep", "left over", "leftover", "leftovers")),
    entry("frozen-pizza",
          (("frozen pizza", "frozen pizzas", "pizza"),
           # "temperature" and "cold" are `fridge-temp`'s words: a word two entries share stops
           # counting as specific, and this entry sharing them pushed the fridge-temperature
           # answer behind the fridge-fault one for "my fridge is not cold".
           ("cook", "cooking", "oven", "how long", "gas mark", "fan", "crispy",
            "soggy", "best", "properly", "bake", "baking", "preheat", "middle", "shelf",
            "air fryer",
            # "do i need to defrost it first" is a cook-from-frozen question, not a keeping
            # one, and "what temperature" is how the same question is asked again.
            "defrost", "defrosting", "thaw", "thawed", "straight from", "straight in",
            "what temperature", "temp", "temps")),
          ("Frozen pizza wants a fully heated oven, not a cold one: 200C (180C fan, gas mark 6) "
           "for 12 to 15 minutes, straight on the shelf or a hot tray, until the cheese bubbles "
           "and the base lifts. A cold oven gives you a soggy middle and a pale top, and an air "
           "fryer does a small one in 8 to 10 minutes at 180C."),
          # a pizza you make is a dough question, and a pizza you keep is a freezing one
          avoid=("dough", "base", "homemade", "make", "making", "recipe", "scratch", "yeast",
                 "leftover", "leftovers", "left over", "freeze", "freezing",
                 "refreeze", "keep", "keeps", "storing", "how long does", "calories",
                 "healthy", "takeaway", "delivery", "shop", "buy", "price", "toppings",
                 # a pizza stone is its own kit, and this answer is about a tray and a shelf
                 "stone", "pizza stone",
                 # a chilled pizza cooks in less time, and this answer opens as if it were frozen
                 "fresh", "chilled", "ready made", "ready-made", "ready meal",
                 # a pizza that was never frozen is the other row's: this answer opens "Frozen
                 # pizza wants a fully heated oven", which is the wrong first word for "how long
                 # do i bake a pizza". The bare `pizza` in the key is what reached those lines,
                 # so the row only answers when something says the pizza is a frozen one.
                 ),
          guard=_a_frozen_pizza),    # The tinned question is not the dried one: "can i use tinned chickpeas without soaking
    # them" wants "no soaking needed", and the dried entry answers it as if the tin were a bag.
    entry("pulses-tinned", (("tinned chickpeas", "canned chickpeas", "tinned beans",
                             "canned beans", "tinned kidney beans", "tinned butter beans",
                             "tin of chickpeas", "tin of beans", "can of chickpeas",
                             "can of beans", "tinned lentils", "tin of lentils",
                             "can of lentils", "jar of chickpeas", "jarred chickpeas",
                             "jar of beans", "jarred beans", "straight from the tin"),
                            ("soak", "soaking", "need", "use", "cook", "eat", "ready",
                             "drain", "instead", "tin", "can")),
          "Tinned chickpeas and beans are already cooked, so there is no soaking and no long "
          "simmer: drain them, rinse the salty water off and they are ready in a soup, a curry "
          "or a salad. Use about two tins where a recipe asks for 250g of dried weight. Dried "
          "ones are the ones that want 8 hours of cold water and 45 to 60 minutes of simmering.",
          # "what can i cook with a tin of chickpeas" is a meal question, and the meal entry
          # answers it; this one is for "is the tin already cooked, and do I need to soak it".
          avoid=("recipe", "dinner", "meal", "ideas", "what can i cook", "what can i make",
                 "what could i cook", "what could i make", "what should i cook", "cook with",
                 "make with",
                 # "what can i do with a tin of chickpeas" is a meal question too, and the
                 # chickpeas entry gives the three quick ideas; this one is about the tin
                 "what can i do", "do with", "what do i do", "what should i make",
                 "what should i have", "suggest", "something quick", "quick meal",
                 # a dropped tin is an injury, not a cooking question
                 "dropped", "slipped", "foot", "finger", "thumb", "toe", "burn", "burned",
                 "spill", "spilled", "broke", "broken", "shelf")),
    # A bag costs less than a tin for the same amount on the plate, and people ask it as a
    # money question ("are tinned beans cheaper than dried") and as a cooking one ("is it
    # cheaper to cook dry beans"). It got the dry-meat rescue, the soaking timetable or a meal
    # list, none of which say which is cheaper, so the comparison has its own answer.
    entry("pulses-cheaper",
          (("dried beans", "dry beans", "dried chickpeas", "dry chickpeas", "dried lentils",
            "dry lentils", "dried peas", "dried pulses", "tinned beans", "canned beans",
            "tinned chickpeas", "canned chickpeas", "tinned lentils", "canned lentils",
            "beans", "chickpeas", "lentils", "pulses",
            # the price question is often a bare comparison: "are tinned ones cheaper",
            # "dried or tinned". The pulse word is in the phrase. "tinned" and "dried" alone
            # are modifiers, not a subject - a bare "tinned" made a tin of tuna a pulse, so
            # "is tinned tuna worth buying" was answered as if it were about lentils.
            "tinned or dried", "dried or tinned", "dried ones", "tinned ones",
            "dried version", "tinned version", "from a tin", "out of a tin", "in a tin",
            "bag of", "a bag", "from dried"),
           ("cheaper", "cheapest", "cheap", "cost", "costs", "price", "prices", "worth it",
            "worth the money", "worth buying", "save", "saves", "saving", "money", "value", "better value",
            "more expensive", "expensive", "vs", "versus")),
          "Dried beans, chickpeas and lentils cost about a third of the tinned price for the same "
          "amount on the plate: half a kilo of dried, around £1.20, cooks up to about the same as "
          "three or four tins at 70p to 90p each, and a bag of dried lentils is under £2 a kilo "
          "where mince is £5 to £7 for 500g, so pulses are much the cheaper protein. Tinned wins "
          "when dinner has to be on the table in ten minutes; dried wins if you cook a big pot at "
          "the weekend and freeze it in portions.",
          # a tin of coffee or baked beans is a different shopper's question, and dried pasta or
          # rice is a different comparison
          avoid=("coffee", "baked beans", "baked bean", "green beans", "green bean",
                 # "a bag of" is what brought a building material in here: "how much does a bulk
                 # bag of gravel cost" was answered with the price of dried lentils
                 "gravel", "sand", "cement", "concrete", "topsoil", "compost", "shingle",
                 "chippings", "bulk bag", "bark", "slate", "aggregate", "paving", "mortar",
                 "ballast", "mulch", "woodchip", "pebbles", "building",
                 "pasta", "rice", "noodles", "snake", "pet", "dog", "cat",
                 # "beans or peas with dinner" is a meal, not a price comparison
                 "dinner", "tea", "supper", "lunch", "breakfast", "meal", "meals", "tonight",
                 "salad", "curry", "soup", "recipe", "recipes", "protein",
                 # "is tinned tuna worth buying" and "are lentils worth eating" are one
                 # "worth" away from a price question and are about something else: whether
                 # the food is good for you, and whether it is worth the money at all. The
                 # words for that reading keep them off the comparison.
                 "healthy", "healthier", "healthiest", "good for you", "worth eating",
                 "nutritious", "filling", "tuna", "fish", "salmon", "prawn", "prawns",
                 "tomato", "tomatoes"),
          bias=1),
    # An opened tin is a different question from what is in it: how long it keeps now, and why it
    # cannot stay in the tin. "How long does an opened tin of tomatoes last" was a shrug, and "an
    # open tin of beans in the fridge" got the dried-bean prep answer.
    # "can" on its own is a modal verb ("can i keep...") and "canned" is a loose form of it, so
    # the ask below is what keeps this entry off "what can i do with leftover veg". Only "can of"
    # is a tin on its own.
    entry("tin-keep", (("tin", "tins", "tinned", "can of", "cans of", "tin of", "tins of"),
                       ("opened", "open", "once opened", "after opening", "in the fridge",
                        "half a tin", "half a can", "kept in the tin", "still in the tin",
                        "in the tin", "in a tin", "gone off", "off")),
          "An opened tin keeps 2 days in the fridge, and only once you have emptied it into a "
          "bowl or a lidded tub: leave food in the tin and the metal taints it and can make you "
          "ill. Cover it, keep it cold, and reheat it until it is piping hot. An unopened tin "
          "keeps for years in a cupboard, so trust the date stamped on it.",
          ask=("opened", "open", "once opened", "after opening", "in the fridge",
               "half a tin", "half a can", "kept in the tin", "still in the tin",
               "in the tin", "in a tin", "tin", "tins", "tinned", "tin of", "tins of",
               "can of", "cans of"),
          # "how do i open a tin without a can opener" is a tool question, and a recipe that
          # happens to use a tin is a meal question.
          # a tin of paint is not a tin of beans: "how do i stop my paint drying out in the tin"
          # was answered with "an opened tin keeps 2 days in the fridge", which is the worst kind
          # of wrong answer because the fridge is not even a joke here
          avoid=("paint", "paint tin", "emulsion", "gloss", "undercoat", "varnish", "wood stain",
                 "opener", "can opener", "without an opener", "without a can opener",
                 "how do i open", "how to open", "how do you open", "tin without",
                 "recipe", "dinner", "meal", "ideas", "what can i make", "what can i cook",
                 "what should i cook", "cook with", "make with", "soak", "soaking",
                 "already cooked", "do i need to cook",
                 # what is in a tin is the food tables' question: "how much protein in a tin
                 # of tuna" asks about the tuna, not about how long an opened tin keeps.
                 "protein", "carbs", "carb", "carbohydrate", "carbohydrates", "calories",
                 "calorie", "fibre", "fiber", "how much fat", "how much sugar",
                 # a cake or a biscuit lives in a tin too, and that is a baking question;
                 # freezing an opened tin is the freeze entry's question.
                 "cake", "cakes", "biscuit", "biscuits", "bread", "loaf", "baking", "traybake",
                 "cake tin", "loaf tin", "baking tin", "roasting tin", "tin foil", "foil",
                 "freeze", "freezing", "frozen",
                 # a jar, a bottle and a carton each keep their own way, and milk has the
                 # sourness test that matters more than the tin.
                 "jar", "jars", "jam", "pesto", "ketchup", "mayonnaise", "chutney", "pickle",
                 "milk", "cream", "yoghurt", "bottle", "carton", "wine"),
          # "how long does an opened tin of beans last" is the opened tin, and the tinned-beans
          # entry matches "tin of beans" as a phrase, so this one needs the nudge.
          bias=2),
    entry("salad-dressing", (("vinaigrette", "dressing", "salad dressing"),
                             ("make", "recipe", "oil", "vinegar", "ratio", "good", "keep")),
          "Whisk 3 parts olive oil to 1 part vinegar with a teaspoon of mustard, a pinch of salt "
          "and pepper: the mustard holds it together. Make it in a jam jar and shake it, and it "
          "keeps a week in the fridge.",
          # "how do i make a fancy dress costume" was answered with salad dressing, because
          # "dressing" is this row's word and "make" was in the line. A costume is never a sauce.
          avoid=("costume", "costumes", "fancy dress", "dress up", "dressing up", "world book day",
                 "halloween", "outfit", "party outfit")),
    entry("avocado-brown", (("avocado", "avocados"),
                            ("brown", "going brown", "browning", "black", "keep", "stop")),
          "Lemon or lime juice on the cut face slows it down, and cling film pressed right onto "
          "the flesh works better than a loose lid. Brown patches are only air damage; cut them "
          "off and the rest is fine."),

    entry("stock-carcass",
          (("stock", "stocks", "broth", "broths", "carcass", "carcasses", "bones", "bone",
            "bone broth", "stockpot", "stock pot", "bouillon", "consomme", "consommé"),
           ("chicken", "turkey", "beef", "fish", "lamb", "pork", "ham", "duck", "goose",
            "venison", "vegetable", "veg", "mushroom", "mushrooms", "peelings", "scraps",
            "make", "made", "making", "recipe", "use", "keep", "keeps", "keeping",
            "store", "freeze", "freezer", "fridge", "last", "how long", "how much",
            "how many", "simmer", "simmering", "boil", "boiling", "cook", "cooking",
            "time", "hours", "minutes", "cube", "cubes", "granules", "skim", "scum",
            "foam", "risotto", "slow cooker", "pressure cooker", "healthy", "good for",
            "taste", "flavour", "flavor", "bland", "better", "stronger", "vegan",
            "vegetarian", "without bones", "no bones", "jelly")),
          _stock_answer,

          # A dog that has eaten a bone is a vet question, not a stock recipe: nothing about the
          # pot belongs in that answer, and "chicken"/"bones" are the two words it shares with it.
          # A person's own bone is the same shape: "how long does a broken bone take to heal" is
          # "bones" + "long" + "take", and it was reaching this pot and then punting, because the
          # row that owns the question scored lower than a recipe for stock. The pot's own words
          # are added to these, so a stock line still comes here.
          avoid=PET_LINE_WORDS + ("broken", "broke", "heal", "heals", "healing", "healed",
                                  "fracture", "fractured", "mend", "mending", "broken bone",
                                  "my bone", "my arm", "my leg", "my wrist", "my ankle",
                                  "my finger", "my toe", "my rib", "my collarbone",
                                  # "bones" is in this row's key because a pot of stock is made
                                  # from them, and the count of a person's own is the same word:
                                  # "how many bones in the human body" and "how many bones do i
                                  # have" were answered "a litre of stock to 300g of risotto rice".
                                  # `science.bones` is the row that answers them, and it names a
                                  # body, a human or a skeleton, so those shapes are the fence.
                                  # Bare "bones" stays out of it: "how long to simmer bones for
                                  # stock" is still this pot.
                                  "human", "human body", "the body", "my body", "your body",
                                  "in the body", "in my body", "skeleton", "skeletal",
                                  "how many bones", "bones do i have", "bones in the body",
                                  "bones in my body", "bones does a", "bones has a") + STOCK_AVOID),
    entry("chicken-skin", (("chicken", "turkey"),

                           ("skin", "crispy", "crisp", "golden", "brown")),
          "Dry the skin and salt it, keep it uncovered in the fridge for an hour if you can, and "
          "roast it on a rack at 200C (180C fan) without basting or covering. Steam is the enemy: "
          "a wet bird in a crowded tin comes out pale and flabby."),
    # "freezer" is not in this key: the freezer has its own keeping entry with its own numbers,
    # and sharing the word meant every "how long can X stay in the freezer" got the fridge days.
    entry("fridge-life", (("fridge",),
                          ("how long", "keep", "keeps", "last", "safe", "still ok", "gone off",
                           # A verdict asked of a thing that has been kept asks the same
                           # question, and its words are not the keeping words: "is it ok to eat
                           # fish thats been in the fridge since sunday" reached nothing, because
                           # the line asks "ok to eat" and this row's ask was "still ok". The
                           # subject half still has to say the place, so a line that asks a
                           # verdict with no place in it ("is it ok to eat reheated rice") is
                           # not this row's.
                           "days", "use by", "out of date",
                           # "is it ok in the fridge til tomorrow" carries no measure at all, so
                           # it reached no entry and the follow-up path cut the last answer down
                           # to the sentence of it that says "fridge". The keeping words are the
                           # key here; the fridge is the subject.
                           "overnight", "til tomorrow", "till tomorrow", "until tomorrow",
                           "next day", "in the morning",
                           "ok to eat", "safe to eat", "alright to eat", "ok to drink",
                           "safe to drink", "can i eat", "can we eat", "edible")),
          ("Cooked food keeps 3 to 4 days in the fridge, raw meat and fish 1 to 2 days, and milk, "
           "cheese and yogurt until the date on the pack, or a couple of days past it if they look "
           "and smell right. Cooked rice is the exception at 1 day, and anything left out for more "
           "than 2 hours goes in the bin: the bugs that make you ill have no smell."),
          # The subject of this row is cooked food and what is left over, not the fridge. A line
          # that names a food with its own keeping row has that row's answer ("carrots keep for
          # weeks in the salad drawer"), and "how long do carrots keep in the fridge" was getting
          # this cooked-food table instead. Which foods those are is not written here: the KEEPS
          # table below is the list, and the loop after it adds every name in it to this row's
          # avoid. A keeping row added tomorrow stands this table down without an edit here.
          avoid=("rice", "chicken", "milk", "egg", "eggs", "cheese", "yogurt", "leftovers",
                 "leftover", "beer", "wine", "drink", "drinks", "bottle", "lager",
                 # "i keep water in the fridge" is where the water lives, not how long food
                 # keeps: the keeping words are the key, so a "keep" about a drink reached here.
                 "keep water", "keeps water", "keep a jug", "keep the jug", "jug", "jugs",
                 # a food with its own keeping answer must not be given the general table: "how
                 # long does ginger last in the fridge" was getting the cooked-food list instead
                 # of the paper bag and the freezer
                 "ginger", "spring onion", "spring onions", "scallion", "scallions",
                 "lettuce", "spinach", "rocket", "arugula", "salad", "leaves", "leafy",
                 "watercress", "herb", "herbs", "basil", "coriander",
                 # an apple keeps for weeks and a fridge makes it mealy, so the general cooked-food
                 # table is the wrong answer for it: "how long do apples keep in the fridge" was
                 # getting the 3-to-4-days list while the apple entry sat one line away.
                 "apple", "apples", "fruit", "banana", "bananas", "orange", "oranges",
                 "berries", "strawberries",
                 # "how do i keep milk from boiling over" matched "keep" and "milk" and was told
                 # how many days cooked food lasts: a pan that boils over is the pot's answer.
                 "boil over", "boils over", "boiling over", "boiled over", "overflow",
                 "overflows", "spill", "spills", "spilling", "spilled", "spilt",
                 # the fridge's own clock is home.py's fridge-first-cold: "how long does a
                 # fridge take to get cold" is not four days of cooked food
                 "get cold", "gets cold", "get colder", "cool down", "cools down",
                 "cooling down", "get to temperature", "get down to temperature",
                 "come down to temperature", "putting food in", "put food in",
                 "how long should i wait", "wait before",
                 # the fridge itself is the question when it smells or wants cleaning, and
                 # "how do i keep a fridge smelling fresh" was given the cooked-food days
                 "smell", "smells", "smelly", "stink", "stinks", "stinking", "odour",
                 "odor", "musty", "off smell", "bad smell", "smelling fresh", "smells fresh",
                 "clean the fridge", "clean out the fridge", "clean my fridge", "cleaning the fridge",
                 # a sourdough starter is kept alive rather than eaten inside four days,
                 # so "how long can i keep a starter in the fridge" is the jar's question
                 # and the cooked-food list is the wrong clock for it
                 "starter", "starters", "sourdough", "sour dough", "levain",
                 "wipe out", "defrost the fridge", "fridge smelling", "fridge smells")
                 # a burnt dinner is not a keeping question: "i burnt the roast, is it still ok"
                 # was given the cooked-food days, and the burnt-food answer says what to do
                 # with the black and whether it can be eaten.
                 + ("burnt", "burned", "charred", "scorched", "burnt on", "caught on the bottom")
                 # a fridge repair is the job, not four days of cooked food
                 + JOB_GUARD),

    # --- a dish that came out wrong -----------------------------------------
    # People rarely ask "how do I season a sauce"; they say what went wrong: "it came out bland",
    # "my curry is too watery", "the sauce tastes flat". Each entry below is one fault, keyed by
    # the words people use for it plus one of the _FOOD words above, and answers with the fix and
    # why it happened. Each entry carries bias=1, so naming what went wrong beats a technique
    # entry that happens to score the same. A new fault is one more entry.
    # Popcorn had no cards of its own, so "how do i make stovetop popcorn" was answered by the
    # hob-cleaning one, which is the only place the words "hob" and "stovetop" were written
    # down, and "how long does popcorn last" was a shrug. One card for making it, one for keeping
    # it and one for whether it is a healthy snack: three asks, three answers.
    entry("popcorn",
          (("popcorn", "pop corn", "popping corn", "popcorns"),
           _FOOD + ("pop", "popped", "popping", "kernels", "kernel", "hob", "pan", "pot",
                    "microwave", "stovetop", "stove top", "how", "best", "homemade",
                    "at home", "cinema", "salted", "salty",
                    "without oil", "no oil", "air pop", "air-popped", "air popped")),
          _popcorn_make,
          avoid=("ceiling", "popcorn ceiling", "corn on the cob", "sweetcorn", "grow",
                 "growing", "plant", "plants", "keep", "keeps", "keeping", "store",
                 "storing", "last", "lasts", "stale", "chewy", "soft", "leftover",
                 "healthy", "healthier", "calories", "diet", "weight", "fattening", "fat",
                 "makes you fat", "unhealthy",
                 # "how do i clean my popcorn maker" is a cleaning line: without these the
                 # maker's "popcorn" was enough for the method card
                 "clean", "cleaning", "wash", "washing", "maker", "popper", "machine",
                 # a smell in the room is not a method: "how do i get the smell of popcorn out
                 # of the sofa" was answered with the pan-and-lid recipe. Only the smell words:
                 # "sofa" is one slip from the key word "soft", and a misspelt avoid word is
                 # read as the word itself, which stood this card down for "my popcorn went soft"
                 "smell", "smells", "smelling", "smelled", "smelly", "odour", "odor",
                 "smell of popcorn", "popcorn smell", "get rid of the smell", "curtains",
                 "cushions", "cushion", "carpet", "carpets",
                 # a caramel or toffee coating is a different job from plain popcorn, and the
                 # pan method answers neither
                 "caramel", "toffee", "toffeed", "caramelised", "caramelized",
                 # "why does popcorn pop" is the science card's question, not the method's
                 "why"),
          bias=1),
    entry("popcorn-keep",
          (("popcorn", "pop corn", "popping corn", "kernels"),
           ("keep", "keeps", "keeping", "store", "storing", "storage", "last", "lasts",
            "long", "stale", "soft", "chewy", "leftover", "left over", "airtight", "tin",
            "jar", "crisp", "crispy", "fresh", "how long", "came out", "comes out", "turned",
            "went", "gone", "go", "goes")),
          _popcorn_keep,
          avoid=("ceiling", "corn on the cob", "sweetcorn",
                 "smell", "smells", "smelling", "smelled", "smelly", "odour", "odor",
                 "smell of popcorn", "popcorn smell", "curtains", "cushions", "cushion")),
    entry("popcorn-health",
          (("popcorn", "pop corn"),
           ("healthy", "healthier", "healthiest", "diet", "calories", "fattening", "weight",
            "good for you", "bad for you", "snack", "better than", "nutrition", "fibre",
            # "does popcorn make you fat" is the same question as "is it fattening"
            "fat", "fats", "makes you fat", "make me fat", "put on weight", "carbs",
            "unhealthy")),
          "Air-popped popcorn is a good snack: a big bowl is roughly 30 to 50 calories, it is "
          "whole grain, and the fibre and the chewing make it more filling than crisps. It is the "
          "butter, the salt and the toffee that turn it into a treat, so go easy on those rather "
          "than on the popcorn itself.",
          avoid=("ceiling", "corn on the cob", "sweetcorn",
                 "smell", "smells", "smelling", "smelly", "odour", "odor",
                 "smell of popcorn", "popcorn smell", "curtains", "cushions", "cushion"),
          bias=1),
    entry("fix-bland",
          (("bland", "tasteless", "flavourless", "no flavour", "more flavour", "lacks flavour",
            "tastes of nothing", "no taste", "flat", "dull"),
           # `_A_TASTE` and not `_FOOD`: how the fault was said ("came out", "turned out") is
           # not a dish, and a bare "it came out flat" is about the bake in the line before it -
           # the follow-up reading reaches that row, where this one answered the saying alone.
           _A_TASTE),
          "Season it in that order: a pinch more salt, then a squeeze of lemon or a splash of "
          "vinegar, then something savoury like a stock cube, a splash of soy or a knob of butter. "
          "Bland food is nearly always short of salt and acid rather than spice; if you're cutting "
          "salt, the lemon and the savoury splash do most of it on their own.",
          avoid=("coffee", "flat white", "latte", "cappuccino", "espresso", "americano", "tea",
                 "wine", "beer", "cider", "lager", "champagne", "lemonade", "cola",
                 "fizzy", "battery", "tyre", "tire", "joke", "voice", "music", "greyhound", "dog",
                 "dogs", "cat", "cats", "puppy", "kitten", "rent", "landlord", "garden",
                 "flatmate", "flat mate", "neighbour", "neighbours", "mortgage", "tenancy",
                 "lease", "estate agent",
                 # a pancake or a Yorkshire pudding that is flat did not rise: it is not short of
                 # salt, and `pancakes` answers that. A loaf that came out flat is the same fault,
                 # so the bread words stand this card down too (`bread-rise` answers them)
                 "pancake", "pancakes", "yorkshire pudding", "yorkshires",
                 # "flat" is also a dwelling, and "no oven in my new flat what can i cook" was
                 # getting the seasoning answer because "flat" + "cook" scores four. The place
                 # words below are only ever a home, so a taste question never carries them.
                 "new flat", "my flat", "the flat", "our flat", "in the flat", "in my flat",
                 "moved in", "moved into", "moving in", "moving into", "renting", "tenancy",
                 "let agreed", "deposit",
                 # the same place, counted: "its a two bed flat and we have a lot of stuff" was
                 # the seasoning card twice over - "flat" is the taste and "stuff" is a form of
                 # stuffing in the food list. A home is never a taste, however it is counted.
                 "bed flat", "bedroom flat", "studio flat", "one bed", "1 bed", "two bed",
                 "2 bed", "three bed", "3 bed", "bedsit", "bungalow",
                 # (not "my stuff" or "the stuff": the avoid list is stemmed, so "stuffing"
                 # meets them and "my stuffing was bland" lost its answer)
                 "a lot of stuff", "lots of stuff", "too much stuff", "boxes of stuff",
                 "stuff to move", "moving house", "house move", "moving flat", "move flat",
                 "bread", "breads", "sourdough", "loaf", "loaves", "dough",
                 "risen", "rose", "prove", "proved", "proving", "proofed", "proving basket",
                 # "flat" is also a place, and spoilage questions have their own answers
                 "mould", "mouldy", "mold", "moldy", "gone off", "went off", "stale", "sour",
                 "safe to eat", "still eat", "how long does it keep", "how long does my"),
          # The place words above only catch the shapes they spell out, and a flat with a size or
          # a condition in front of it slips through: "how do i make my small flat look bigger"
          # keys `flat` with `look` and got "Season it in that order: a pinch more salt". The
          # guard reads the determiner and the small adjectives, so a home is a home however it
          # is described, and a bake that came out flat keeps its own answer.
          guard=_not_the_flat_you_live_in_bake,
          bias=1),
    entry("fix-salty",
          (("salty", "too much salt", "over salted", "oversalted", "salt in it", "too salty"),
           _FOOD),
          _salty,
          avoid=("sea", "ocean", "water", "pool", "sweat", "tears", "crisps", "chips"),
          bias=1),
    entry("fix-watery",
          (("watery", "runny", "too thin", "sloppy", "too much liquid",
            # The other way people say it: the sauce "never thickens", it "wont thicken". The
            # dish is in the same line and _FOOD knows it, so one phrase answers them all.
            "never thickens", "wont thicken", "won't thicken", "not thickening",
            "isnt thickening", "isn't thickening", "doesnt thicken", "doesn't thicken",
            "wont reduce", "won't reduce", "never reduces",
            # How a pastry, a batter or a fried mix is described: "my pastry is too wet to roll
            # out". Bare "wet" stays out, because "it is wet outside" is the weather.
            "too wet", "a bit wet", "is wet", "went wet", "bit wet"), _FOOD + _WET_FOOD),
          _watery,
          # a watery drink is a brew question: "my coffee tastes watery" was coming here because
          # _FOOD carries taste/tastes, and it was told to simmer the lid off.
          avoid=("soup", "gravy", "ketchup", "paint", "nail", "glue", "poo", "nappy",
                 # a wok has its own fault row, and the two share the word "watery": "my stir
                 # fry is watery" was told to simmer it with the lid off for ten minutes.
                 "stir fry", "stir-fry", "stirfry", "wok", "stir fried",
                 "diarrhoea", "egg", "eggs", "yolk", "yolks", "poach", "poached", "boil", "boiled",
                 "omelette", "honey", "nose", "coffee", "tea", "drink", "drinks", "mug", "cuppa",
                 "kettle",
                 # a dressing is meant to be loose, and it is not the vegetables that made it so
                 "dressing", "dressings", "vinaigrette",
                 # A wet salad stays here, not with the soggy-lunch entry: salt drawing the water
                 # out is the cause for coleslaw and pasta salad, so `soggy-lunch` leaves the
                 # watery lines to this one.
                 ),
          bias=1),
    # A pot of yogurt that has gone grainy was a shrug while "my homemade yoghurt is grainy" got
    # the make-it card, which is about heat, not about the fault.  The two causes are the milk
    # going above the culture's range and a pot that was shaken or frozen on the way home.
    entry("yoghurt-grainy",
          (("yoghurt", "yogurt", "yoghurts", "yogurts", "homemade yoghurt", "home made yoghurt",
            "home-made yoghurt", "yoghurt pot", "labneh", "skyr", "kefir"),
           ("grainy", "grainy bits", "gritty", "bitty", "lumpy", "lumps", "curdled", "separated",
            "split", "squeaky", "chalky", "went wrong", "goes wrong", "failed", "fail",
            "didnt set", "didn't set", "wont set", "won't set", "not set")),
          "Shop-bought yoghurt that looks grainy has usually been shaken about or chilled too "
          "hard in transit: stir the whey back in and eat it, it is harmless. Homemade yoghurt "
          "goes grainy when the milk got above about 46C, because the culture and the milk "
          "proteins clump: heat the milk to 85C first, cool it to 43-45C before stirring the "
          "starter in, and keep it at 43C while it sets - an oven with just the light on, or a "
          "flask, holds it steadier than a warm spot that swings.",
          # how long a pot keeps, what to use instead of yoghurt and a watery dip are other rows
          avoid=("use instead", "substitute", "instead of", "how long does", "out of date",
                 "use by", "sell by", "gone off", "mould", "mold", "freeze", "freezer",
                 "frozen yoghurt", "ice cream", "watery", "runny", "calories", "protein",
                 "diet", "baby", "weaning", "greek", "which yoghurt", "best yoghurt"),
          bias=1),
    entry("fix-dry",
          # "overdone" is how a joint is described, and it was not a key word: "the joint is
          # overdone" got an echo, and "joint" was not a food the key knew either
          (("dry", "dried out", "overcooked", "over cooked", "over-cooked", "overdone",
            "over done", "over-done"),
           _FOOD + _BAKED_GOODS + ("joint", "joints")),
          _dry,
          avoid=("scrambled", "scramble", "wine", "cider", "skin", "hands", "mouth", "weather",
                 "washing", "clothes", "dryer", "tumble", "hair", "eye", "eyes", "cough",
                 "chicken breast", "breast", "market", "markets", "shares", "stocks",
                 "portfolio", "protein", "shampoo", "conditioner",
                 # a pet's food is not a cooking fault: "is dry food ok for my cat" is the
                 # feeding question, and the pets domain has it
                 "cat", "cats", "dog", "dogs", "kitten", "puppy", "pet", "pets",
                 # drying the dishes is a kitchen job, not a dish that came out dry
                 "dishes", "plate", "plates", "towel", "towels", "sink", "draining board",
                 # "dry beans" is an ingredient, not a fault: "is it cheaper to cook dry
                 # beans" was answered "serve it with something wet" because "dry" is this
                 # entry's word and beans are food. The cost of dried pulses is its own
                 # question, and this is not a plate of food that came out dry.
                 "dry beans", "dried beans", "dry chickpeas", "dried chickpeas",
                 "dry lentils", "dried lentils", "dry pulses", "dried pulses",
                 "dry peas", "dried peas", "split peas",
                 "brownie", "brownies",
                 "flapjack", "flapjacks", "scone", "scones", "sponge", "sponges",
                 # the same rule with herbs: a bunch hung up to dry is not a plate of food
                 # that came out dry, and "how do i dry herbs" was "serve it with something
                 # wet - gravy, a spoon of yoghurt" because "herbs" is food and "dry" is this
                 # entry's word
                 "dry herb", "dry herbs", "dried herb", "dried herbs", "drying herbs",
                 "dry them", "dry lavender", "drying lavender",
                 # and a dry rub is the opposite of a fault: "how do i make a dry rub" was told
                 # to serve it with something wet, because "dry" and "rub" both belong here.
                 "dry rub", "dry rubs", "spice rub", "rub for", "make a rub", "rub recipe",
                 "rub the", "what goes in a rub")
          + _BAKE_KEEPING,
          bias=1),
    # A cake burning is not a sauce burning: the rescue for a pan ("lift the burnt bits out")
    # is the wrong instruction for something still in the oven, and "how do i stop the cake
    # burning" was the sugar-drinking answer because "stop" and "cake" are craving words. The
    # bake words below are the gate, so a burnt sauce keeps fix-burnt.
    entry("bake-burning",
          (("burnt", "burned", "burning", "burns", "burn", "charred", "scorched", "caught",
            "catching", "too brown", "brown on top", "browned too fast", "dark on top",
            "black on top", "burnt on top", "burnt on the edges", "burning around the edges",
            # the bottom is the other end of the oven, and these are the words people use for
            # it: "why do my cakes burn on the bottom" and "my muffins burn on the bottom" were
            # the burnt-sauce card and a one-line fragment of the top answer
            "burnt on the bottom", "burned on the bottom", "burn on the bottom",
            "burns on the bottom", "burning on the bottom", "burnt bottom", "bottom burnt",
            "black on the bottom", "black at the bottom", "bottom is black", "bottom is burnt",
            "bottom goes black", "burnt underneath", "burns underneath", "burning underneath",
            "bottom of my cake", "bottom of the cake", "bottom of my bread", "bottom of the loaf",
            "bottom of my pie", "cake bottom"),
           ("cake", "cakes", "sponge", "loaf", "loaves", "bread", "buns", "biscuits", "cookies",
            "muffins", "brownies", "cheesecake", "pastry", "pie", "pies", "tart", "tarts",
            "bake", "baking", "baked", "oven", "tin", "traybake", "scones", "pizza", "quiche",
            "victoria sponge", "fruit cake", "madeira")),
          _bake_burning,
          ask=("oven", "bake", "baking", "baked", "tin", "tray", "shelf", "top", "edges", "cake",
               "cakes", "sponge", "loaf", "loaves", "bread", "buns", "biscuits", "cookies",
               "muffins", "brownies", "cheesecake", "pastry", "pie", "pies", "tart", "tarts",
               "scones", "pizza", "quiche", "traybake", "bake it", "stop it",
               # the bottom is as much a part of the bake as the top, and the ask gate was the
               # reason "my pizza burnt on the bottom" reached nothing at all
               "bottom", "underneath", "underside"),
          # the pan and the grill are fix-burnt's and the toast one's, and a burnt piece of meat
          # under a grill is not a cake in a tin
          avoid=("pan", "pot", "saucepan", "sauce", "gravy", "soup", "stew", "rice", "toast",
                 "toaster", "meat", "chicken", "roast", "steak", "sausage", "sausages", "bbq",
                 "barbecue", "smell", "smoke", "alarm", "iron", "shirt", "hand", "finger",
                 "skin", "sun", "candle", "coffee", "espresso", "tea ", "kettle", "panini",
                 # getting the burnt off a tin is the cleaning answer, not the foil one: a tin
                 # to wash is not a cake burning in the oven
                 # getting the burnt off a tin is the cleaning answer, not the foil one: a tin
                 # to wash is not a cake burning in the oven
                 "clean", "cleaning", "cleaned", "cleaner", "scrub", "scrubbing", "scour",
                 "soak", "wash", "washing", "wipe", "wiping", "stain", "stains", "stained",
                 # "crusted" is not here: its loose form is "crust", and that took "my bread has
                 # burnt marks on the crust" and "the pastry burnt on the crust" off the bake
                 # answer (#2905). A crusted tin still says "clean" or "burnt on", which the
                 # cleaning entry keys on, so nothing is lost by leaving the word out.
                 "residue", "grease", "greasy", "shelf",
                 "off the tin", "off my tin", "off the tray", "get the burnt off",
                 # a burnt-on oven door or shelf is a cleaning question, not a bake: the bare
                 # word "oven" in the key is enough for this entry to take "my oven door glass
                 # is burnt on" off `oven-clean`, so the cleaning sense stands this one down
                 # bare "marks" took "my bread has burnt marks on the crust" with it, and that is
                 # a bake; the marks only stand this entry down when they are on the oven itself
                 "marks on the oven", "marks in the oven", "marks off the oven",
                 "glass", "door", "burnt on bits", "burnt on the glass", "burnt on the door",
                 # the same cleaning sense said by the part of the oven instead of the door
                 "bottom of the oven", "sides of the oven", "inside of the oven",
                 "inside of my oven", "interior of the oven",
                 # the phrase, not the bare word: "the cake is stuck to the tin and burnt" is a
                 # bake that needs rescuing, and bare "stuck" handed it the lining-the-tin answer
                 "stuck to the oven", "stuck on the oven"),
          bias=1),
    entry("fix-burnt",
          # "charred" is the word a person uses when the black is on purpose or on a grill, and
          # "is charred meat bad for you" reached nothing at all: a punt, while "is burnt meat bad
          # for you" was answered. "blackened" is left out on purpose - blackened chicken is a dish.
          (("burnt", "burned", "scorched", "charred", "caught on the bottom",
            "caught at the bottom", "burnt on the bottom", "burned on the bottom",
            "stuck to the bottom"),
           # the parts of a roast are food nobody's food list had, so "the stuffing burnt" and
           # "the crackling burnt" reached nothing and got an echo back
           _FOOD + ("stuffing", "crackling", "parsnips")),
          _burnt_dish,
          # a burnt *drink* is the brew question: "my coffee tastes burnt" was told to lift the
          # burnt bits out of the pan. Phrases, not bare words, so a coffee cake stays a cake.
          # Not the bare word "oven". It was here to keep the cleaning sense off this row, and the
          # phrases above already do that ("marks on the oven", "glass", "door", "bottom of the
          # oven", "inside of my oven"), so all it did was disown the food that burnt *in* the
          # oven: "my roast burnt in the oven" - the deck's own line - fell through to "Thanks for
          # telling me" while "my roast is burnt" got the meat's rescue. The oven lines it was
          # meant for still get the bicarbonate card, and a bake still stands this row down on its
          # own words (cake, bread, pastry, tray, shelf).
          avoid=("toast", "toaster", "smell", "smoke", "alarm", "iron",
                 # a bake is never the sauce card's line: "lift the burnt bits out rather than
                 # stirring them in" is the rescue for a pot, and it was the answer to "why do my
                 # cakes burn on the bottom", "my cake burnt on the bottom" and "why does my
                 # bread burn on the bottom". bake-burning's gate is the bake noun, so the bake
                 # words stand this one down and the foil, the shelf and the tin answer it.
                 "cake", "cakes", "sponge", "muffins", "brownies", "scones", "loaf", "loaves",
                 "bread", "pie", "pies", "tart", "tarts", "pastry", "biscuits", "cookies",
                 "traybake", "cheesecake", "quiche", "flapjack", "fruit cake",
                 "victoria sponge", "cake tin", "baking tray", "baking sheet", "pizza",
                 # "yorkshire" and "batter" are out of this list on purpose: a burnt Yorkshire
                 # has its own rescue inside `_burnt_dish` now, and with the word here the line
                 # reached no row at all and got a random pancake idea instead.
                 "shirt", "hand", "finger", "mouth", "tongue", "skin", "sun", "candle",
                 # a burning chest or throat is a body question and not a pan one: "burning in my
                 # chest after a curry" and "my throat is burning after a curry" were given "take
                 # it off the heat and lift out the burnt bits", because a curry is in _FOOD and
                 # the key's "burnt" matches "burning".
                 "chest", "throat", "tummy", "stomach", "gullet", "heartburn", "reflux",
                 "acid", "indigestion", "burning when i", "burns when i", "burning in my",
                 "burns in my", "burning after", "burns after", "eyes", "eye", "lips",
                 # a pan in the line is not a reason to pass any more: "i burnt the bottom of a
                 # pan of rice" was declined by this entry and by burnt-pan together, and got
                 # nothing. Getting it *off* the pan is the cleaning question, so those words,
                 # and not the pan, decide.
                 "clean", "cleaning", "cleaned", "scrub", "scour", "soak", "soaking", "wash",
                 "washing", "comes off", "come off", "off the bottom", "off my pan",
                 "off the pan", "off the inside", "off the base", "get it off", "still stuck",
                 "stuck on", "wont come", "won't come",
                 # "my pan has burnt food stuck to it" is the same cleaning question, and "stuck
                 # on" does not read "stuck to": it was answered with the acrylamide card about
                 # how burnt food is not poisonous, which is the other question. Phrases, because
                 # "stuck to the bottom" is this row's own key - a pot of rice caught on the
                 # bottom is the rescue.
                 "stuck to it", "stuck to the pan", "stuck to my pan", "stuck to the pot",
                 "stuck to my pot", "stuck in the pan", "stuck in my pan",
                 # the same words with the other article: "how do i get burnt food off a pan"
                 # was still the acrylamide card while "off the pan" and "off my pan" were
                 # handled, so the list has to hold all three ways of saying the pan
                 "off a pan", "off a pot", "off pots", "off pans",
                 "coffee tastes", "coffee taste", "coffee that tastes", "coffee is burnt",
                 "espresso tastes", "espresso is burnt", "tea tastes", "tea taste",
                 "tea that tastes", "tea is burnt"),
          bias=1),
    entry("fix-undercooked",
          # "why does my bread not bake in the middle" and "bread doesnt cook in the middle" are the
          # same complaint said with a verb: the loaf is doughy, and the recipe and the baking time
          # were what answered them
          (("undercooked", "under cooked", "under-cooked", "underbaked", "under baked",
            "underbake", "doesnt cook in the middle", "doesn't cook in the middle",
            "not cook in the middle", "wont cook in the middle", "won't cook in the middle",
            "doesnt bake in the middle", "doesn't bake in the middle",
            "not bake in the middle", "wont bake in the middle", "won't bake in the middle",
            "not cooking in the middle", "not baking in the middle",
            "isnt cooked in the middle", "isn't cooked in the middle",
            "isnt baked in the middle", "isn't baked in the middle",
            "arent cooked in the middle", "aren't cooked in the middle",
            "is not cooked in the middle", "is not baked in the middle",
            "still hard", "hard in the middle",
            "doughy", "doughy in the middle", "claggy in the middle",
            "crunchy", "raw in the middle", "not cooked through", "not cooked in the middle",
            "wet in the middle", "soggy in the middle", "not done in the middle",
            "still crunchy"),
           # a loaf is a bread word the fault table did not know, and "in the middle" is how
           # people say where it is still wet
           _FOOD + ("loaf", "loaves", "sourdough", "bread roll", "bread rolls", "traybake",
                    "yorkshires", "batter", "pancake", "pancakes", "dumplings")),
          _undercooked,
          # Readiness, not a fault: a crunchy salad, a crunchy topping and "how do i make it
          # crunchy" all want a different answer, and a crunchy *chicken* is a food-safety
          # question that chicken-pink already owns.
          avoid=("crispy", "salad", "slaw", "topping", "crumble", "goes with", "side", "snack",
                 # wanting something crunchy is not a complaint that it is: the readiness asks
                 # are their own how-to lines, and this entry is only the fault.
                 "how do i make", "how to make", "how do i get", "how to get", "how do i keep",
                 "how to keep", "make crunchy", "get crunchy", "stay crunchy", "want it crunchy",
                 "want them crunchy",
                 "chicken", "turkey", "pork", "sausage", "sausages", "burger", "burgers",
                 "prawns", "prawn", "mussels", "mince",
                 "how do i make it crunchy", "how do i get it crunchy", "how do i make them crunchy",
                 "how do i keep", "keep them crunchy", "i want it crunchy", "want it crunchy",
                 "love crunchy", "like it crunchy", "extra crunchy"),
          bias=1),
    entry("fix-greasy",
          (("greasy", "oily", "fatty", "too much oil", "too oily", "swimming in oil",
            "swimming in fat", "too greasy"),
           # chips and a fry-up are food too, and they were the lines that found this gap
           # chips and a fry-up are food too, and they were the lines that found this gap.
           # Roast potatoes stay out: main already answers those with the method that stops it.
           _FOOD + ("chips", "chip", "fries", "fry", "pakora", "pakoras", "doughnuts",
                    "doughnut", "onion rings", "tempura")),
          _greasy,
          # a greasy *hair* or forehead is not a kitchen: the kitchen words are what make this food,
          # and a paper towel on the scalp answer would be absurd in a chat about chips.
          avoid=("hair", "skin", "face", "forehead", "scalp", "hands", "pizza", "takeaway",
                 "take away", "take-away", "restaurant", "chippy", "delivery", "burger van"),
          bias=1),
    entry("fix-sticking",
          (("sticking", "sticks to the pan", "stuck to the pan", "glued to the pan", "sticks"), _FOOD),
          _STUCK_TO_A_PAN,
          # Food stuck to *itself* is pasta-cook or rice-sticky; only the pan is this entry's.
          # A cake does not come off the way a steak does, and "how do i stop cake sticking to the
          # tin" was answered with the hot-pan advice: cake-out-of-tin has the paper and the ten
          # minutes, and the baked things below are all that entry's or the baking faults'.
          avoid=("label", "sticker", "drawer", "window", "door", "envelope", "stamp", "plaster",
                 "tape", "fridge", "lid",
                 # "how do i make it stick" is about carrying something on, not about a pan:
                 # the food word is what makes a kitchen line a kitchen line, and these phrases
                 # never turn up in one
                 # ... and the bare word "stick" is a verb about carrying on in more lines than
                 # it is about a pan, so the things people are trying to keep going are named:
                 # "how do i make my revision stick" is revision-start's question.
                 "make it stick", "make it stick this time", "stick with it", "stick at it",
                 "keep it up", "keep going", "habit", "routine", "motivation", "revision",
                 "revise", "revising", "study", "studying", "exam", "exams", "practice",
                 "practising", "practicing", "training", "workout", "skills", "skill",
                 "together", "clumped", "clumps", "clumpy", "gluey", "sticky rice",
                 "cake", "cakes", "sponge", "loaf", "bread", "bun", "buns", "muffin", "muffins",
                 "pastry", "baking paper", "baking parchment", "baking tin", "cake tin",
                 "springform", "tin", "tins",
                 # a batter poured into a pan or a tin sticks for its own reasons (heat, fat,
                 # turning it too soon), and `a-batter-that-sticks` answers each of them
                 "pancake", "pancakes", "crepe", "crepes", "batter", "waffle", "waffles",
                 "yorkshire", "yorkshires", "yorkshire pudding", "pikelet", "pikelets"),
          bias=1),
    # The same answer for a food this table has never heard of. "my gyoza stuck to the pan", "my
    # hash browns stuck to the pan", "my plantain stuck to the pan" and "my pierogi stuck to the
    # pan" name no word of _FOOD, so fix-sticking could not see them, and they reached the
    # burnt-pan card instead - simmer it with bicarbonate and lift the burnt layer with a wooden
    # spoon, which is a pan to clean. Whatever the food, "X stuck to the pan" is one question and
    # its answer is the hot pan and the food left alone, so the phrase pair alone is the key here
    # and a food the table knows keeps fix-sticking's own line.
    entry("food-stuck-to-a-pan",
          (("stuck to the pan", "stuck to my pan", "stuck on the pan", "sticks to the pan",
            "sticks to my pan", "sticking to the pan", "sticking to my pan", "glued to the pan",
            "stuck to the wok", "stuck to the skillet", "stuck to the griddle",
            "stuck to the frying pan", "stuck to the pot", "stuck to my pot",
            "stuck to the saucepan", "stuck to my saucepan", "stuck to the bottom of the pan",
            "stuck to the bottom of my pan", "stuck to the bottom of the pot",
            "stuck to the bottom of my pot", "sticking to the bottom of the pan",
            "sticking to the bottom of the pot"),
           # the pan is the other half, so a cake stuck to a tin, a sticker on a window and a
           # food stuck to a plate are not this row's lines
           ("pan", "pans", "frying pan", "wok", "woks", "skillet", "griddle", "saucepan",
            "saucepans", "pot", "pots", "casserole")),
          _STUCK_TO_A_PAN,
          # A cake, a loaf or a pastry does not come off the way a steak does, and the tin has its
          # own row; food stuck to *itself* is the pasta and rice lines; and a pan that has lost
          # its seasoning is "my pan sticks", not a food that stuck.
          avoid=("cake", "cakes", "sponge", "loaf", "loaves", "bread", "bun", "buns",
                 "muffin", "muffins", "pastry", "tin", "tins", "tray", "baking paper",
                 "baking parchment", "together", "clumped", "clumps", "clumpy", "gluey",
                 "sticky rice", "label", "sticker", "drawer", "window", "door", "envelope",
                 "stamp", "plaster", "tape", "fridge", "lid", "burnt", "burned", "burnt",
                 "black", "scorched", "clean", "cleaning", "scrub", "soak", "off the",
                 "non stick", "nonstick", "season", "seasoning",
                 # what is stuck there without a name is the pan to clean, and rice has its own
                 # two answers (the pot, and the burnt bottom)
                 "something", "anything", "everything", "stuff", "bits", "things", "rice")),
    entry("fix-lumpy",
          (("lumpy", "lumps"), _FOOD),
          _lumpy,
          avoid=("gravy", "mattress", "pillow", "breast", "skin", "throat", "gland", "bump",
                 # a coat that went on unevenly is the nails row's: "my nails came out lumpy" and
                 # "my nail polish came out lumpy" were taught to push a sauce through a sieve.
                 "nails", "nail", "nail polish", "nail varnish", "manicure", "varnish",
                 "fingernail", "fingernails", "cuticle", "cuticles",
                 # A lump in a baby's meal is the weaning question, not a sauce to whisk: "she
                 # doesnt like lumps in her food" reached this row. A person's own food is the
                 # tell, so a baby, a child or "her food" stands this row down.
                 "my baby", "baby", "babies", "weaning", "weaned", "first foods", "six months",
                 "6 months", "month old", "toddler", "my son", "my daughter", "my child",
                 "her food", "his food", "their food", "the babys", "finger food"),
          bias=1),
    # "My carrots are tough" is the same fault word about a vegetable, and the vegetable names
    # are only added here rather than to _FOOD so "my carrots are watery" does not become a
    # sauce question: this entry's own second group carries them.
    entry("fix-rubbery",
          (("rubbery", "like rubber", "chewy", "tough"),
           _FOOD + _BAKED_GOODS),
          _tough,
          avoid=("boots", "boot", "shoes", "shoe", "scrambled", "scramble", "scrambling",
                 "omelette", "fried egg", "poached", "mashed", "mash", "porridge", "interview",
                 "meeting", "boss", "decision", "choice",
                 # how mince comes out is the mince entry's question
                 "mince", "minced",
                 # chewy popcorn was stale kernels, not a dish cooked too long: `popcorn-keep`
                 # answers it
                 "popcorn", "pop corn",
                 "biscuit", "biscuits", "cookie", "cookies", "shortbread", "scone", "scones",
                 "cracker", "crackers", "flapjack", "flapjacks"),
          bias=1),
    entry("bake-gummy",
          (("gummy", "clammy", "wet in the middle", "soggy in the middle", "stodgy", "doughy",
            "raw in the middle", "undercooked in the middle", "not cooked in the middle",
            # how the same fault is said of a loaf: "why is my bread gummy inside" went to the
            # four rising causes, and "my sourdough is gummy" was a nod
            "gummy inside", "gummy in the middle", "wet inside", "stodgy in the middle",
            "doughy in the middle"),
           _BAKED_GOODS + ("bread", "loaf", "loaves", "sourdough", "focaccia", "brioche",
                           "ciabatta", "baguette", "pitta", "pita", "rolls", "bread rolls")),
          _gummy,
          avoid=("rice", "risotto", "pasta", "noodles", "semolina", "polenta", "porridge",
                 "gravy", "sauce", "stew", "bread sauce"),
          bias=1),
    entry("bake-pale",
          (("pale", "pale on top", "no colour", "not browned", "didnt brown", "did not brown",
            "wont brown", "won't brown", "stayed pale", "white on top", "looks raw",
            "looks undercooked", "underbaked", "under baked"),
           _BAKED_GOODS + ("bread", "loaf", "loaves")),
          "A bake that stays pale is short of heat or short of sugar. Check the oven with a "
          "thermometer, because most run 10 to 20C cool, and put it up 10C for the last ten "
          "minutes. Milk or egg brushed on top browns it. If the middle is still wet it is "
          "underbaked, not pale: give it 10 more minutes under foil.",
          avoid=("pale ale", "ale", "beer", "wine", "skin", "pale skin", "pale face", "i look pale",
                 "looking pale", "feel pale", "stool", "poo", "urine"),
          bias=1),
    entry("bake-soda-taste",
          (("bicarbonate", "bicarbonate of soda", "baking soda", "bicarb", "soda taste",
            "tastes of soda", "soapy", "tastes soapy", "tastes of soap", "chemical taste",
            "tastes chemical", "metallic taste", "tastes of raising agent"),
           _BAKED_GOODS + ("bread", "loaf", "loaves", "soda bread", "bake", "baked", "baking",
                           "batter", "dough")),
          "A soapy or chemical taste is too much bicarbonate, because the soda had nothing acid "
          "to react with. Use about a quarter of a teaspoon per 100g of flour and give it "
          "something sour - buttermilk, yoghurt, lemon or treacle. Sift it with the flour rather "
          "than stirring it in at the end, and a squeeze of lemon over a baked one hides most of "
          "it.",
          avoid=("clean", "cleaning", "sink", "drain", "fridge", "washing", "laundry", "stain",
                 "toilet", "bath", "oven cleaner",
                 # a line that is comparing the two powders is not a cake that tastes of one:
                 # "bicarbonate of soda or baking powder" was the soapy-taste card, because
                 # "baking" in the baked-goods group met "bicarbonate" in the first. The fence
                 # is the phrasing people compare with, not the bare words: "which", "instead",
                 # "difference" and "do i need" turn up in ordinary fault lines ("my cake tastes
                 # of soap which is annoying", "the cake tastes soapy do i need to throw it
                 # away"), and a word of them stood this card down on its own.
                 "vs", "versus", "difference between", "or baking powder", "or soda",
                 "or bicarb", "which one",
                 # "instead of baking powder" and its siblings were here and they cost a fault
                 # line: "my bread tastes of soap instead of baking powder" is a soapy loaf, and
                 # the phrase stood this card down for it, so the calories card answered. The
                 # swap question belongs to the uses-bicarbonate-of-soda-for-baking-powder row,
                 # which outranks this one and reads the direction the line asked.
                 ),
          bias=1),
    entry("fix-egg-white",
          (("egg white", "egg whites", "whites"), ("stiff", "peaks", "whip", "whipping", "whisk",
                                                   "fluffy", "rise", "volume")),
          "Any yolk, grease or water stops them whipping: use a clean dry bowl, separate the eggs "
          "while they're cold, then let the whites come to room temperature. A pinch of salt or a "
          "drop of lemon helps, and so does beating on a medium speed rather than flat out."),
    # --- pastry: a base from scratch ------------------------------------------
    # Puff is the one the shops sell and the one people try at home, and the honest home version is
    # rough puff: the same folds without the block of butter and the marble slab. Written out in
    # four steps, because "cold" is the whole method and it is the part that goes wrong.
    entry("pastry-shrink",
          (("pastry", "tart", "tart case", "quiche", "flan", "pie", "case"),
           ("shrink", "shrinks", "shrinking", "shrank", "sides", "slip", "slipping", "slides",
            "pulls", "pulled", "smaller")),
          "Pastry shrinks for three reasons: the dough is warm, it is stretched instead of eased "
          "into the tin, or it bakes without a rest. Roll it cold, press it into the corners "
          "rather than pulling it, leave a little overhang instead of trimming it flush, and chill "
          "the lined tin for 20 minutes before it goes in. That rest is what stops the sides "
          "sliding down.",
          avoid=("jumper", "jumps", "wool", "washing", "clothes", "shirt", "fabric", "cotton")),
    # "what can i make with filo pastry" was answered with a shortcrust recipe ("half the fat to
    # flour by weight"), and the puff pastry line with how to bake a sheet. Both are asking which
    # dish to put the pastry in, so the two answers sit together and the recipes stand aside.
    entry("pastry-ideas",
          (("puff pastry", "filo pastry", "phyllo pastry", "filo", "phyllo", "puff", "pastry",
            "readymade pastry", "ready made pastry", "ready-rolled pastry", "jus rol"),
           ("make with", "cook with", "do with", "what can i", "what can we", "ideas", "idea",
            "use it for", "fill it with", "fill with", "stuff it", "quick", "easy")),
          "Quick things for both, with the oven at 200C fan: puff pastry makes sausage rolls, "
          "cheese straws, palmiers, a tomato and goat's cheese tart, or a sheet folded over "
          "sliced apple as a rough tarte tatin. Filo makes spanakopita, samosas, little cigar "
          "rolls of feta and spinach, and baklava - keep it under a damp cloth while you work, "
          "because it dries out in a minute. For either one, heat the empty tray in the oven "
          "first, get the filling already cooked and cooled, brush the top with beaten egg, and "
          "don't open the door for the first 15 minutes or it sinks. Spare sheets freeze well: "
          "wrap them tight and they thaw in about 20 minutes.",
          bias=2,
          # the recipes for the pastry itself, and what it costs on the plate, are other rows
          avoid=("from scratch", "how do i make", "how to make", "rough puff", "shortcrust",
                 "choux", "suet", "protein", "calories", "calorie", "kcal", "carbs", "sugar",
                 "fat", "fibre", "fiber", "healthy", "nutrition", "shrink", "shrinks", "soggy",
                 "why", "dont", "didnt", "wont", "stuck", "burnt",
                 # "i have leftover puff pastry, what can i do with it" has its own answer,
                 # "pastry going spare: cut it into strips, twist them with grated cheese", and
                 # this row was taking it: what to do with a bit spare is a smaller question
                 "leftover", "left over", "spare", "use up", "going spare")),
    entry("make-puff-pastry",
          (("puff pastry", "rough puff", "puff", "flaky pastry", "palmiers", "sausage rolls",
            "vol au vent"),
           ("make", "making", "recipe", "how", "from scratch", "easy", "quick", "home",
            "homemade", "butter", "flour", "fold", "folds", "turn", "turns", "rise", "rising")),
          "Rough puff, which is the home version: 250g plain flour, 250g of butter still cold from "
          "the fridge cut into 1cm cubes, a pinch of salt, and about 120ml of iced water. Bring it "
          "to a dough with the butter still in visible lumps, rest it 20 minutes, then roll it out "
          "to a long rectangle, fold the top third down and the bottom third over it, and turn it a "
          "quarter turn. Do that four times, resting it in the fridge for 20 minutes if it starts "
          "to feel soft, and chill it 30 minutes before it goes in the oven. Cold butter and cold "
          "hands are what make it rise: if the butter melts into the flour it bakes flat and tough. "
          "Bake at 220C. Real puff, with a flattened block of butter folded inside, is worth buying "
          "for a special occasion; filo is always worth buying.",
          # what puff does in the oven is a fault, not the recipe. "rise" is not in this list on
          # purpose: the fault lines all say why, didnt or wont, and "how do i get my puff pastry
          # to rise" is the recipe, which is where the cold-butter reason is written out.
          # What the pastry is worth on the plate is the nutrient table's question, not the
          # recipe's: "how much protein in a sausage roll" and "how many calories in one" were
          # both answered with the four folds, because a sausage roll is made of this pastry.
          avoid=("dont", "didnt", "wont", "not", "soggy", "flat", "sunk", "burn", "burnt",
                 "shrink", "shrinks", "why", "stuck",
                 "protein", "calories", "calorie", "kcal", "carbs", "carb", "carbohydrates",
                 "sugar", "fat", "fibre", "fiber", "nutrition", "nutrients", "healthy",
                 # "what can i make with puff pastry" is a dish to put it in, not a recipe for
                 # the pastry itself, and it got the four folds.
                 "make with", "cook with", "do with", "what can i", "what can we", "use up",
                 "leftover", "left over", "with puff pastry", "goes with", "serve with")),
    entry("fix-pastry",
          ("pastry", ("breaking", "cracks", "cracking", "crumbly", "falls apart", "tears", "tearing")),
          "Pastry cracks when it's too dry or too warm: sprinkle on a little cold water, chill it "
          "for 20 minutes, and roll it between two sheets of baking paper. Patch any tear with a "
          "damp finger before it goes in the oven and nobody will see it."),
    # The two things people report about their own pastry case, and neither had an entry: "why
    # did my pastry shrink" was answered by the laundry's shrinkage rule ("wash cool, 30C, spin it
    # slow") because no kitchen entry was keyed on the fault, and "my pastry is soggy underneath"
    # got the too-much-water rule written for pasta. The fix differs by fault - the chill for a
    # shrinking case, the heat underneath for a soggy one - so one entry picks between them.
    entry("pastry-fault",
          (("pastry", "pastry case", "pastry base", "pie crust", "pie base", "pie case",
            "tart base", "tart case", "flan case", "flan base", "quiche base", "shortcrust",
            "pie", "quiche", "tart", "flan",
            # "my pastry shrunk in the tin" said the tin, not the case, and the tin-keeping
            # entry keys that word too
            "the tin", "in the tin"),
           ("shrink", "shrank", "shrunk", "shrinking", "shrinks", "pulled away", "pulls away",
            "slid down", "slides down", "slumped", "slumps", "slumping", "limp",
            "soggy", "soggy bottom", "soggy base", "soggy underneath", "wet underneath",
            "raw underneath", "pale underneath")),
          _pastry_fault,
          # a garment that shrank is the laundry's question, and a recipe for pastry itself is
          # the shortcrust one, so both stand aside here
          avoid=("clothes", "clothing", "jumper", "jumpers", "shirt", "shirts", "dress",
                 "dresses", "wool", "woollen", "cotton", "laundry", "washing", "wash",
                 "machine", "tumble", "dryer", "iron", "fabric", "curtains", "curtain",
                 "shrink wrap", "label",
                 "how do i make pastry", "pastry recipe", "shortcrust recipe",
                 "how do i make shortcrust", "puff pastry", "filo", "choux",
                 "blind bake", "blind baking", "make a quiche", "quiche recipe",
                 "make a pie", "pie recipe"),
          # "how do i stop pastry shrinking" also fits the shortcrust recipe (pastry plus an ask),
          # and the recipe is the wrong answer to a fault, so this carries one point more
          bias=2),
    # "how do i make cookies chewy" was answered with the pancake-batter rule ("a lumpy mix and a
    # minute less in the pan"): "chewy" is the rubbery-fault word, and nothing keyed it on a
    # biscuit. The soft and the hard textures already have their own answers, so this is only the
    # chewy one.
    entry("biscuit-chewy",
          (("cookie", "cookies", "biscuit", "biscuits", "shortbread", "flapjack", "flapjacks"),
           ("chewy", "chewier", "chewiness", "gooey", "squidgy", "soft centre",
            "soft in the middle")),
          "Chewy comes from soft brown sugar and pulling the tray out early: swap a third of the "
          "caster sugar for light muscovado, add an extra yolk, and take them out while the middles "
          "still look underdone, because they carry on setting on the hot tray.",
          # "chewy" is a texture the plain recipe does not mention, and "rubbery" is the fault
          # word this entry shares with fix-rubbery, so it carries two points to win both ties
          avoid=("stale", "hard", "soften", "dog", "boot", "steak", "meat"),
          bias=2),
    entry("cake-fault",
          (("cake", "cakes", "sponge", "sponges", "loaf cake", "victoria sponge", "fairy cakes",
            "cupcakes", "batter", "birthday cake"),
           ("domed", "dome", "domes", "doming", "sunken middle", "cracked", "cracks",
            "cracking", "crack", "eggy", "tastes of egg", "taste of egg", "smells of egg",
            "rise evenly", "rises evenly", "risen evenly", "uneven", "unevenly", "lopsided",
            "soggy bottom", "tunnels", "tunnelling")),
          _cake_fault,
          # a sponge that is heavy, dry or flat has its own answers, and so has the pudding
          avoid=("heavy", "dense", "sank", "sunk", "did not rise", "didnt rise", "dry", "stale",
                 "keep", "keeps", "last", "lasts", "fridge", "freezer", "freeze", "iced",
                 "icing", "decorate", "decorating"),
          bias=2),
    entry("fix-onion",
          (("onion", "onions"), ("burn", "burning", "burnt", "catch", "catching", "sticks")),
          "Turn the heat down to medium, add a little more oil, and splash in water whenever they "
          "start to catch; stir them every minute or two. Sweet onions want 8 to 10 minutes of "
          "gentle cooking — hot and fast is what burns them."),
    entry("fix-stirfry",
          (("stir fry", "stir-fry", "stirfry", "wok"),
           ("soggy", "watery", "limp", "steaming", "not crispy", "goes soft")),
          "A soggy stir-fry is a crowded pan: cook it in two batches over the highest heat you have, "
          "dry the vegetables well first, and add any sauce only at the very end off the heat."),
    # --- food safety: the asks that are about a date, a freezer or a bug --------------------
    # "is it ok to eat eggs past the date" only said "egg" and "date", and "date" was not in
    # the egg key, so the most common food question in the deck got a search suggestion.
    entry("reheat-chicken", (("chicken", "turkey"),
                             ("reheat", "reheating", "reheated", "microwave", "warm up", "hot")),
          ("Yes, once, and until it is piping hot all the way through - steam rising and no cold "
           "spot in the middle. Keep cooked chicken in the fridge no more than 3 days, don't "
           "reheat it twice, and bin it if it has been out of the fridge for more than 2 hours.")),
    # "thawed" and "defrosted" are in the key as the thing being refrozen, but they are also
    # what a defrosting question says ("how do i defrost a chicken without food poisoning"), so
    # the ask below is what makes this the refreezing answer.
    entry("refreeze-meat", (("meat", "mince", "chicken", "beef", "pork", "sausages", "fish"),
                            ("freeze", "freezer", "refreeze", "re-freeze", "refrozen", "freezing")),
          ("Only if it thawed in the fridge: that meat can go back in the freezer, though it will "
           "be a bit drier. Anything that thawed on the worktop or in a warm kitchen should be "
           "cooked and eaten now - cooking it first is what buys you extra days, not refreezing "
           "it raw."),
          # "thawed" is also what a defrosting question says ("how do i defrost a chicken without
          # giving myself food poisoning"), so the ask is what makes this the refreezing answer.
          ask=("refreeze", "re-freeze", "refrozen", "again", "back", "second time", "thawed",
               "defrosted"), bias=2),
    # One jar, one row: a second `honey-store` card sat beside this one and the two shared the
    # lines by which word happened to be in which key, so whoever edited one changed half of
    # them. The words for a jar that has set are in this key instead, and "sugar" is here only
    # as the words a person writes about a set jar ("sugary", "sugar crystals"), never as the
    # bare noun, or "how much sugar is in honey" would be answered with a keeping card.
    entry("honey-keeps", (("honey",),
                          ("go off", "gone off", "out of date", "keep", "keeps", "kept",
                           "last", "lasts", "crystallised", "crystalised", "crystallized",
                           "crystals", "hard", "hardened", "gone hard", "cloudy", "solid",
                           "gone solid", "thick", "gone thick", "granular", "grainy", "sugary",
                           "sugar crystals", "set in the jar", "store", "storing",
                           "still ok", "is it ok", "safe to eat", "use by",
                           # "can i keep honey in the fridge" is the same jar question
                           "fridge", "cupboard",
                           # "is honey still ok after years" was a shrug: the same freshness ask
                           # in the words people use for a jar, and the answer says how long it
                           # keeps instead of only that it does not spoil
                           "still good", "past the date", "after the", "years", "expired",
                           "best before")),
          ("Honey does not really go off - a jar keeps for years: honey that clouds or sets hard "
           "has crystallised rather than spoiled, and both are normal. Stand the jar in a bowl of "
           "hot water to loosen it, and keep it in a cupboard with the lid on. The one rule is no "
           "honey for a baby under a year, because of the botulism risk.")),
    # The one honey rule people ask about, and the line about it got a health-visitor number
    # instead: a baby word plus honey is a botulism question whatever else the line says.
    entry("honey-baby", (("honey", "honey on", "honeys"),
                         ("baby", "babies", "baby's", "babys", "under one", "under 1", "infant",
                          "toddler", "toddlers", "month old", "months old", "weaning", "weaned",
                          "dummy", "one year old", "two year old", "three year old", "2 year old",
                          "3 year old", "newborn", "6 month", "7 month", "8 month", "9 month",
                          "10 month", "11 month")),
          _honey_age, bias=2),
    # "does tea with honey help a cold" was the eat-something-plain card for a poorly stomach,
    # because honey and cold are both in that row's words and neither of this one's was. A cold
    # is what honey is most often asked about, and it belongs beside the cough.
    entry("honey-cough", (("honey",), ("cough", "coughs", "sore throat", "scratchy throat",
                                       "tickly", "cold", "colds", "flu", "sniffles")),
          ("A spoonful of honey is as good as any over-the-counter cough syrup for a cough or a "
           "scratchy throat, and it is the one thing the NHS suggests first: a teaspoon straight, "
           "or in a warm drink with lemon. Never under a year old, because of the botulism risk. "
           "See a doctor if it lasts more than three weeks or comes with a fever."), bias=1,
          # "cold" is a sore on the lip as well as the illness, and the mouth answers own it
          avoid=("cold sore", "cold sores", "herpes", "lip", "lips", "blister", "blisters",
                 "honey cake", "honeycomb", "honey glaze", "honey roast", "honey mustard",
                 "recipe", "bake", "baking", "cake", "muffin", "porridge")),
    entry("raw-dough", (("cookie dough", "cake batter", "raw dough", "dough", "batter",
                         "cake mix", "cookie mixture"),
                        ("eat", "safe", "taste", "lick", "spoon", "raw")),
          ("Best not: raw flour and raw egg are both a real risk, and flour is the one people "
           "forget - it can carry E. coli straight from the field. Normal dough is for the oven; "
           "if you want to eat it raw, use a recipe with heat-treated flour and no egg.")),
    # A plain raw egg is not a flour question: "can i eat raw eggs" was getting the cookie-dough
    # answer, which is about the flour, and it has its own honest answer in the UK.
    entry("raw-egg", (("raw egg", "raw eggs", "runny egg", "runny eggs", "soft boiled",
                       "dippy egg", "dippy eggs"),
                      ("eat", "safe", "ok", "okay", "fine", "pregnant", "risk")),
          ("In the UK, eggs with the British Lion mark are fine raw or runny, even for pregnant "
           "women, babies and older people, because the hens are vaccinated. Eggs without the stamp "
           "should be cooked until the white and yolk are solid. Anything with raw egg in it - mayo, "
           "mousse, homemade ice cream - should be kept in the fridge and eaten within a day or two."),
          # "can dogs eat raw egg" was this card, which is about a person's breakfast: an egg
          # question with an animal in it is the pet's answer, and `pet-can-eat` has one
          avoid=("dog", "dogs", "puppy", "pup", "cat", "cats", "kitten", "kittens", "pet", "pets",
                 "rabbit", "hamster", "guinea pig", "budgie", "parrot", "horse"),
          bias=1),
    entry("wash-chicken", (("chicken", "turkey"), ("wash", "washing", "rinse", "rinsing",
                                                    "clean")),
          ("Don't: washing raw chicken splashes bacteria over the sink, the taps and anything "
           "within a metre, and cooking kills them anyway. Pat it dry with kitchen paper, bin the "
           "paper, wash your hands, and cook it right through."), bias=1),

    # --- the words on a recipe -------------------------------------------------
    # The glossary answers "what does sear mean", not "how long do i boil potatoes": the word
    # and a definition shape are both required, so a cooking verb in an ordinary question stays
    # with the dish entries.
    entry("cook-words",
          (tuple(COOK_WORDS),
           DEFINITION_WORDS + ("how do i", "how do you", "how to", "how should i")),
          _cook_word, bias=1, avoid=NOT_A_COOKING_LINE,
          ask=DEFINITION_WORDS + ("how do i", "how do you", "how to", "how should i")),
    # How many eggs a person wants is the portion table's question now (#1150 keys it on the
    # food and the eaters), so the glossary stays the glossary: one word, one definition.
    # --- requests for ideas -------------------------------------------------
    # "Something to go with roast chicken" wants the rest of the plate, not the bird's cooking
    # time, and it went to the roast timings before this entry existed.
    entry("meal-sides",
          (("go with", "goes with", "going with", "goes nicely", "goes well with",
            "have with", "eat with", "have it with", "side for", "sides for", "side dish",
            "side dishes", "serve with", "serving with", "to serve with", "alongside",
            "what side", "which side", "pairs with",
            # the adverb slot, filled: "what pairs best with blue cheese", "what goes best
            # with lamb", "what to eat with couscous". The pairing frame reads any adverb
            # between the verb and "with", so the key only needs the commonest.
            "pairs best with", "pairs well with", "pairs nicely with", "goes best with",
            "to go with", "to have with", "to eat with", "serve alongside", "go alongside",
            # what to put on the meat, rather than beside it: "seasoning for lamb" was "Thanks
            # for telling me" and "what spice for beef" a shrug, because every key word here
            # named the rest of the plate. The same entry answers both, from SEASONINGS.
            "seasoning for", "seasoning", "spice for", "spices for", "spice with",
            "spices with", "herb for", "herbs for", "herb with", "herbs with", "rub for",
            "what spice", "what spices", "what herb", "what herbs", "which spice",
            "which spices", "which herbs", "what seasoning", "flavour for",
            "how do i season", "how to season", "how should i season", "season a",
            # bare "season" and "seasoned" stay out: a season is episodes, a league and the
            # close season for fishing, and this row won "what is the close season for fishing"
            # only to decline it, which dropped the licence answer back to a fish's biology.
            "season the", "season it", "what to put on", "put on the",
            # a rub is a seasoning question that names no food: "how do i make a dry rub" was
            # the blister card, because "rub" belongs to a new pair of shoes as well
            "dry rub", "spice rub", "rub recipe", "what goes in a rub"),
           ("chicken", "roast", "sausages", "sausage", "lamb", "beef", "steak", "halloumi",
            "feta", "prawns", "prawn", "shrimp",
            "salmon", "fish", "cod", "curry", "chilli", "daal", "dal", "pasta",
            "spaghetti", "lasagne", "lasagna", "burger", "burgers", "barbecue", "bbq",
            "turkey", "ham", "gammon", "pork", "pie", "stew", "casserole", "soup",
            "risotto", "paella", "hot dogs", "rice", "mash", "mashed potato", "potato",
            "potatoes", "chips",
            # the side that is itself the vegetable: "what goes with corn on the cob", "something
            # to go with sweetcorn". Without it the line named a food this row did not hold.
            "corn", "sweetcorn", "corn on the cob",
            # the foods whose seasoning question had no row to reach: "what seasoning for tofu",
            # "how do i season mince", "any good rub for ribs", "what herbs go with tomatoes",
            # "what spice goes with pumpkin" were all a punt, and SEASONINGS has an answer for
            # every one of them.
            "tofu", "mince", "ribs", "tomato", "tomatoes", "cherry tomatoes", "pumpkin",
            "butternut") + PAIRING_FOODS + PLAN_NAMES),
          _sides,
          # the key alone is not enough: "the handle came off the side of the pan" is a fault,
          # and "what goes with a blue sofa" names no food at all, since _sides only answers a
          # dish it knows.
          ask=("what", "which", "side", "sides", "serve", "serving", "go", "goes",
               "going", "with", "alongside", "suggest", "recommend", "any", "some",
               "for", "spice", "spices", "herb", "herbs", "seasoning", "rub", "flavour"),
          # the angling sense of "season" is the rod licence's line, and a fish beside it is no
          # food: "what is the close season for fishing" and "when is the close season for
          # salmon" were answered with lemon and dill, then with new potatoes and peas
          avoid=("sofa", "curtain", "paint", "carpet", "shirt", "jumper", "wine",
                 "close season", "closed season", "fishing season")),
    # A bake is asked for by name and wants weights: "how do i make chocolate cake", "scone
    # recipe", "brownies from scratch". Anything about a time or a heat belongs to the timing
    # entries, so this one steps aside for those.
    entry("bakes",
          (("chocolate cake", "chocolate sponge", "chocolate gateau", "victoria sponge",
            "sponge cake", "victoria sandwich", "plain sponge", "brownies", "brownie",
            "chocolate brownies", "scones", "scone", "cheese scones", "white bread", "bread",
            "loaf of bread", "bread dough", "banana bread", "banana loaf", "flapjack",
            "flapjacks", "cookies", "cookie", "chocolate chip cookies", "crumble", "fruit crumble",
            "apple crumble", "pastry",
            "shortcrust pastry", "pie crust",
            # the loaves that are not the white one, each with its own recipe in BAKES: a line
            # can name one of these without ever saying "bread" ("how do i make sourdough"),
            # and it is still asking for a recipe.
            "sourdough", "sourdough bread", "soda bread", "soda loaf", "wholemeal bread",
            "brown bread", "bread maker", "bread machine", "breadmaker",
            "gluten free bread", "gluten-free bread"),
           # a second part, because a one-word key cannot score ("bread" on its own is one
           # word of the key, not two) and because a bake is only a recipe question when the
           # line is asking for one.
           ("make", "makes", "making", "bake", "baking", "recipe", "recipes", "cook",
            "cooking", "from scratch", "whats")),
          _bake,
          # a bake that went wrong is a fixing question with its own entry
          # A sourdough loaf has its own recipe now, so the word stays in the key; only the
          # starter itself (feeding it, waking it up) is the starter entry's question.
          avoid=("rise", "rising", "prove", "proving", "wont", "won't", "went wrong", "blunt",
                 "knife", "knives", "mouldy", "mould", "soggy", "stodgy", "burnt", "stuck",
                 "sharp", "stale", "starter",
                 "tough", "chewy", "rubbery", "gummy", "pale", "sank",
                 "didnt rise", "didn't rise", "not risen", "raw in the middle",
                 "underbaked", "under baked", "is crumbly", "too crumbly", "so crumbly",
                 "came out crumbly", "come out crumbly", "went crumbly", "falls apart",
                 "falling apart",
                 # keeping or freezing a bake is its own question, and the second part of this key
                 # carries a bare "whats": "whats the best way to store bread" scored as a recipe
                 # request and came back with the flour-and-yeast card. The keeping row and the
                 # freeze row answer those, so this row stands down for them.
                 "store", "storing", "storage", "keep", "keeps", "keeping", "keep fresh",
                 "stays fresh", "last", "lasts", "fridge", "freezer", "freeze", "frozen",
                 "bread bin",
                 # a nail is not a bake: "what helps a crumbling nail" reached this row through
                 # the word crumble and got the crumble topping, when the person was describing a
                 # nail. The nails rows are in health.py and routines.py.
                 "nail", "nails", "toenail", "toenails", "fingernail", "fingernails",
                 # a soda loaf is the no-yeast recipe row's, not this one
                 "soda", "without",
                 # a machine they are thinking of buying is the buying entry's question
                 "bread maker worth", "worth a bread maker",
                 "buy a bread maker", "buying a bread maker", "buy a bread machine")
                 + NO_SUGAR,
          bias=1),
    entry("meal-plan",
          (("week", "weekly", "weeknight", "weeknights", "meal plan", "meal planning",
            "plan the week", "plan for the week", "food shop", "food shopping",
            "shop for the week", "menu", "batch", "batch cook", "batch cooking",
            "batches", "plan", "planning",
            # "how can i eat well on a small budget" and "how do i eat cheap and healthy" name no
            # week at all, and they are the same ask: the plan for a cheap week. They are phrases
            # rather than the bare "eat", which would make "what should i eat for dinner" a week
            # plan for one dinner.
            "eat well", "eat cheap", "eat healthy", "eat healthily", "eat properly",
            "eating well", "eating cheap", "eating healthy", "eating healthily",
            "eat for less", "small budget", "tight budget", "on a budget", "cheap food",
            "cheap meals", "student", "students", "skint", "broke"),
           ("meal", "meals", "dinner", "dinners", "cook", "cooking", "cheap", "budget",
            "shop", "shopping", "batch", "ideas", "feed", "family")),
          _meal_plan,
          # a week is planned in words like these; "how long do i cook a chicken" is a timing
          ask=("week", "weekly", "plan", "planning", "menu", "batch", "shop", "shopping",
               "cheap", "budget", "ideas", "what", "any", "suggest", "help"),
          avoid=("how long", "temperature", "oven", "recipe", "supermarket open",
                 "opening times", "delivery", "online shop",
                 # a wedding, a party or a big do is planned by the guests and the venue, not by
                 # the eight cheap foods: "how do i plan a wedding on a budget" got this row
                 "wedding", "weddings", "getting married", "hen do", "stag do", "venue",
                 "registrar", "bride", "groom", "guest list", "guests",
                 # a weekend away, a holiday or a night out is not a week of dinners: "how do i
                 # plan a cheap weekend away" was answered with the eight cheap foods to buy
                 "away", "weekend away", "holiday", "holidays", "trip", "weekend break",
                 "city break", "getaway", "night away", "days away", "hotel", "hostel",
                 "flight", "flights", "abroad", "day out", "days out",
                 # "a week in october" is a holiday and "where should i go" asks where, but
                 # neither word settles it on its own: "cheap meals for a week in january" is
                 # the meal plan with a month in it and "where can i go for cheap food" is a
                 # shopping question. Both are decided in _meal_plan, which stands this row down
                 # for a month or a going phrase only when the line names nothing to eat.
                 # A week off is a week to fill, not a week of dinners: "i have a week off and
                 # no idea what to do" was answered with four dinners to plan and cook.
                 "week off", "weeks off", "week off work", "few days off", "time off")),
    entry("time-budget",
          # The minutes have to sit next to something about eating: "i've got about twenty
          # minutes a day for it", said of a guitar, is a habit and not a dinner, so "got",
          # "only" and "have" say nothing on their own, while "quick" still carries the murmur
          # of a hurry in a cooking turn ("and quick, i've only got 20 minutes").
          (("minutes", "minute", "mins", "half an hour", "quarter of an hour", "hour"),
           # "quick" is not a key word: it is the word the tomato-pasta answer and the pasta
           # rows already share, and a second entry using it took the rarity off "quick" and
           # made "quick dinner ideas using tinned tomatoes and pasta" a dinner-ideas line
           # instead of the tomato-pasta answer. The minutes in the line carry the hurry here.
           ("dinner", "cook", "cooking", "meal", "meals", "tea", "supper", "lunch", "eat",
            "eating", "make", "making", "food", "tonight", "hurry", "hungry",
            "recipe")),
          _time_budget, bias=1,
          ask=("cook", "cooking", "dinner", "tea", "meal", "eat", "make", "food", "tonight",
               "quick", "hurry", "hungry", "recipe"),
          avoid=("how long", "should i cook", "temperature", "oven", "keep", "leftover",
                 "reheat", "freeze", "boil", "bake",
                 # "quick" is the hurry in "and quick, i've only got 20 minutes", not the
                 # "quick question" somebody asks about anything else
                 "quick question", "quick q",
                 # a line that asks what to cook is the meal ideas' question, and it answers it
                 # in its own words; the hurry alone is this one's.
                 "what can i cook", "what can i make", "what should i cook",
                 "what should i make", "what could i cook", "what could i make")),
    entry("meal-ideas",
          (("meal", "dinner", "supper", "tea", "tea time", "for tea", "recipe", "what can i cook",
            "what can i make", "what should i cook", "what should i make", "what shall i cook",
            "what shall i make", "what to cook", "what to make", "meal ideas",
            # "what should i eat for dinner" said nothing the table knew: the ask is a meal,
            # and "eat" is how most people say it.
            "what to eat", "what should i eat", "what shall i eat", "what can i eat",
            "what could i eat",
            # the softer ask: "what could i cook with a tin of chickpeas" matched nothing at
            # all, so it got the search line while "what can i cook" got a recipe.
            "what could i cook", "what could i make",
            "dinner ideas",
            # the same ask with the bot in front of it: "what can you help me cook tonight"
            # is a dinner question, not a question about what the bot can do.
            "what can you cook", "what can you make", "what can you help me cook",
            "what can you help me make", "can you help me cook", "can you help me make",
            "help me cook", "help me make",
            # asking for a plan for the week's meals names no dish either:
            # "meal plan on a budget" matched nothing and got an echo of itself.
            "meal plan", "meal plans", "meal planning", "plan meals", "plan my meals",
            "planning meals", "meals for the week", "plan for the week", "weekly meals",
            "food plan", "food for the week",
            # the place a meal is made from is a key word too, because "this is all there is"
            # is three points on its own and the score floor is four: "i have chicken in the
            # fridge and not much else" needs the fridge as its second point
            "fridge", "freezer", "cupboard"),
           ("make", "cook", "quick", "easy", "ideas", "fancy", "tonight", "use up",
            # "no time" is the verb of this ask as often as "cook" is: "no time for dinner" and
            # "no time for tea" name a meal and a shortage of time and nothing else, so with the
            # shortage only in `ask` they sat one point under the floor and got a nod. A dinner
            # ask that names the time it has not got is the plainest quick-dinner question there
            # is, and "for dinner" in DISH_ASK keeps the rows that are not about a meal out of it.
            "no time", "no spare time", "in a rush", "in a hurry", "not enough time",
            # The line that follows a plan is often the idiom and nothing else: "nothing too
            # fancy" after "im doing a meal plan for the week". The bare word "fancy" was rare
            # enough to carry that follow-up only while one entry keyed it, and the recipe rows
            # key it now that a dish can be asked for by wanting it ("i fancy a curry"). A
            # phrase is matched as a phrase whatever the word's rarity is, so the entry that
            # answers the idiom names the idiom.
            "too fancy", "nothing fancy", "fancy something", "something fancy",
            "can i have", "should i have", "shall i have", "cheap", "need", "want",
            # a plan for the week is the same ask in different words: without these
            # "meal plan on a budget" scored one point short and got an echo.
            "plan", "planning", "budget", "week", "weekly",
            # a dinner ask often names no verb and no time: "whats for dinner" (which the
            # normaliser reads as "what is for dinner"), "what to have for dinner" and
            # "what should we have for dinner" all matched nothing and got the shrug,
            # while "whats for tea tonight" only worked because of "tonight". The whole phrase
            # is keyed and never the bare "what is"/"what to": those two words open every line
            # ("what is a dinner roll", "what to wear to a dinner party") and a dinner or a tea
            # is ordinary English.
            "what is for", "whats for", "what's for", "what to have", "what should we have",
            "what shall we have", "what could we have", "what can we have", "what are we having",
            "what should i have for", "what shall i have for", "what is for dinner",
            # "i have mince in the fridge and not much else" names one thing and says it is all
            # there is, which is a dinner question in the plainest words - but it holds no meal
            # word, so the food's storage card took it ("Raw chicken keeps 1 to 2 days in the
            # fridge"). The shapes of "this is all there is" are the ask.
            "and not much else", "and nothing else", "nothing much else in", "and thats it",
            "not much else", "nothing else", "all i have", "all ive got",
            "all i've got", "only got", "only have", "only have got", "thats all i have",
            "that is all i have", "thats all ive got", "this is all i have",
            # the same ask with a number of people instead of a verb: "cheap meals for four
            # people" and "cheap healthy dinner for two" were acknowledged as statements and
            # never answered.
            "for two", "for 2", "for three", "for 3", "for four", "for 4", "for five",
            "for 5", "for six", "for 6", "for eight", "for 8", "for a family",
            # "im having guests for dinner" names the table, not a topic of small talk
            "guests", "guest",
            # the ask above says "what should i eat"; the meal itself is the second word
            "dinner", "tea", "supper", "lunch")),
          _meal_ideas,
          # a meal question asks; "I always cook tea for the kids" mentions the meal but wants no
          # idea, so one asking word has to be there as well as the key
          ask=("what", "shall", "should", "any", "can i", "ideas", "idea", "anything",
               "suggest", "help", "quick", "easy", "fast", "cheap", "tonight", "fridge",
               "need", "want", "decide", "plan", "planning", "budget",
               # "im having guests for dinner and one is veggie" asks by saying what is
               # happening; a guest is a meal to plan for, not small talk.
               "having",
               # Saying there is no time to cook is asking for the quickest dinner, in the words
               # people use for it. "no time to cook dinner" and "dinner with no time to cook"
               # matched the meal words and then stopped at the ask, because none of the asking
               # words is in them, and the shortest way to say "what can I cook quickly" got a
               # nod back instead of the ten-minute list. None of these names a time of day, so
               # they cannot pull "what time is dinner" (which is in the guards below).
               "no time", "not enough time", "no spare time", "short of time", "short on time",
               "pressed for time", "pushed for time", "dont have time", "don't have time",
               "didnt have time", "didn't have time", "hardly any time", "not much time",
               "in a rush", "rushed", "in a hurry", "last minute"),
          avoid=("how long", "temperature", "oven", "portion", "allergic",
                 # a fridge as a thing to buy, mend or complain about is not a fridge with
                 # dinner in it, and the place words are key words now
                 "buy", "buying", "bought", "new fridge", "new freezer", "repair", "mend",
                 "broken", "not cold", "not freezing", "warm", "thermometer", "shelf", "shelves",
                 "seal", "seals", "clean", "cleaning", "smell", "smells", "defrost the fridge",
                 "power cut", "empty the fridge", "freezer burn", "frozen solid",
                 # a dinner is an event as well as a meal: the dress code, the present and the
                 # roll on the side are not dinner ideas, and "dinner lady" is a job.
                 "wear", "wearing", "wore", "dress", "dress code", "outfit", "bring",
                 "roll", "rolls", "lady", "jacket",
                 # "what time is dinner" asks when the meal is, not what to cook, and the
                 # asking words above now read it as a dinner-idea question.
                 "what time", "when is", "what did i", "how many",
                 # "cheap meals without meat" is a plan to eat less meat, and the plan entry
                 # answers it; the "cheap" asking word above made this entry earn the string
                 # for the first time and take it away from the plan.
                 # "no meat" is not in this list on purpose: "no meat please, what can i cook
                 # with chicken" still asks what to cook, and it was answered better by the
                 # dinner list than by the roast-chicken timing.
                 "without meat", "meat free", "meat-free", "meatless",
                 "less meat", "less red meat",
                 # "i cant eat dinner tonight" is about appetite, not about what to cook. What
                 # says so is the meal or the quantity after the words, not the bare "cant eat":
                 # "i cant eat gluten, what can i make for tea" is a diet the dinner list cooks
                 # around, and the bare phrase kept the list off every one of those lines.
                 "cant eat dinner", "cant eat anything", "cant eat much", "cant eat today",
                 "cant eat tonight", "cant eat at the moment", "cannot eat dinner",
                 "can not eat dinner", "cant face", "cannot face", "no appetite",
                 "not hungry", "off my food", "cant stomach", "cannot stomach",
                 "allergy", "breakfast", "brekkie", "brekky", "chicken thigh", "chicken thighs",
                 # "roast chicken" is not here: "what can i make with leftover roast chicken" is a
                 # leftover question, and the leftover idea answers it. A timing question about it
                 # says "how long" or "oven", which are still out.
                 "chicken breast", "whole chicken", "leftover rice",
                 "left over rice", "leftover pasta", "left over pasta",
                 # "tea" is also a drink, and a line about tea keeping you awake or
                 # about brewing it is not a meal question: without this guard the
                 # "tonight" asking word made "I had tea tonight and couldn't sleep"
                 # and "is tea before bed a bad idea" get the ten-minute dinner list.
                 "sleep", "sleeping", "sleepy", "awake", "before bed", "caffeine",
                 "brew", "brewed", "brewing", "steep", "steeped", "bitter",
                 "chamomile", "green tea", "black tea", "tea bag", "tea bags",
                 "cup of tea", "mug of tea",
                 # "what can i do in it for dinner" points back at the machine or the pan the
                 # last turn named, and that appliance's own answer should keep the turn
                 "in it", "with it", "air fryer", "slow cooker", "pressure cooker",
                 "in this", "in that", "in mine",
                 # "help me make a budget" says "make" and nothing about food: the plan-making
                 # phrasings send it to the money answer without touching a real cooking line
                 # like "what can i cook tonight on a budget".
                 "make a budget", "make my budget", "set a budget", "budget plan",
                 "make a plan for my money", "plan my money",
                 # a dinner is also a thing that happens somewhere: "whats for dinner at the
                 # wedding" is a guest asking about the menu, and "whats for dinner in france"
                 # is about the country. Neither wants a weeknight dish. "at home" and
                 # "tonight" are a cooking ask and stay answered.
                 "wedding", "weddings", "reception", "restaurant", "hotel", "canteen",
                 "on the plane", "at school", "at christmas", "christmas day", "christmas eve",
                 "in france", "in spain", "in italy", "in greece", "in portugal", "in mexico",
                 "in japan", "in china", "in india", "in thailand", "in america", "abroad",
                 # a diet word on the dinner ask is a diet question, and the diet entries
                 # answer it: "what should we have for dinner vegetarian" got the plain
                 # dinner list. The bare words would also take "im vegetarian, what can i
                 # cook with mince", which is a cooking question this entry answers well,
                 # so only the phrases with a meal in them are guarded.
                 "dinner vegetarian", "dinner vegan", "dinner no meat",
                 "vegetarian dinner", "vegan dinner", "plant based dinner",
                 "no meat for dinner", "dinner with no meat") + _NOT_MINE),

    # "is it ok to skip breakfast" was getting the list of breakfast ideas, because `skip` was in
    # that entry's asking words. It is a yes-or-no question, so it gets its own answer.
    # The yes-or-no shapes people use: "is it ok to skip breakfast", "do i have to eat
    # breakfast", "should i eat breakfast if i'm not hungry", "is breakfast the most important
    # meal". All of them put a deciding word next to "breakfast", which is why the ideas entry
    # (keyed on "what" and "should") used to take them and answer with porridge.
    entry("breakfast-skip", (("skip", "skipping", "skipped", "miss", "missed", "not eating",
                              "no breakfast", "not hungry", "never eat", "eat no",
                              "dont have breakfast", "don't have breakfast", "without breakfast",
                              # the "is it necessary" shapes. "have to" and "need to" alone were
                              # too loose - "i have to eat breakfast at 6 for work" and "does
                              # breakfast have to be hot" are not this question - so the asking
                              # shape comes with the word: "do i have to", not "have to".
                              "necessary", "important", "do i have to", "do i need to",
                              "must i", "is it ok", "is it bad", "is skipping"),
                             ("breakfast", "brekkie", "brekky", "meal in the morning",
                              "morning meal")),
          # Two sentences, so the short version a repeated question gets is still a whole answer:
          # "no breakfast" shares the word "eat" with the middle of a longer answer, and the
          # composer gave back the fragment "Eat something if you get shaky."
          "Skipping breakfast is not harmful for most adults: what matters is the food you eat "
          "over the whole day, not the hour you start. Don't skip it if you are pregnant, on "
          "insulin or a diabetes tablet that can cause hypos, or a child - and eat something if "
          "you get shaky or headachy mid-morning.",
          bias=1),
    entry("breakfast-ideas",
          (("breakfast", "brekkie", "brekky"),
           # the diet words are asking words here too: "breakfast for a vegan" names nothing to
           # cook, so without them the line had no answer at all and the bot said "Noted!".
           ("idea", "ideas", "what", "good", "quick", "easy", "make", "have", "eat",
            "healthy", "filling", "should", "vegan", "vegetarian", "veggie",
            "plant based", "dairy free", "gluten free", "no eggs", "no dairy", "no meat",
            "allergic", "allergy", "intolerant", "doesnt eat", "doesn't eat", "cant eat",
            "can't eat")),
          _breakfast_ideas,
          # "is it ok to skip breakfast" and "is breakfast the most important meal" are the
          # nutrition entry's questions (nutrition.py, breakfast-important), not a call for ideas
          avoid=("won't", "wont", "refuse", "refuses", "buffet", "hotel", "time", "late",
                 "skip", "skipping", "is it ok", "necessary", "most important", "is it bad",
                 "is it true")),
    entry("lunch-ideas",
          (("lunch", "packed lunch", "lunchbox", "lunch box", "school lunch", "work lunch"),
           ("idea", "ideas", "quick", "easy", "make", "have", "eat", "what", "should",
            "good", "healthy", "pack", "packed",
            # "is it worth bringing my own lunch to work" is a lunch idea, not a contract
            "bring", "bringing", "worth", "own lunch")),
          # The lunch is the same one `lunch-exclusion` gives, read against what the person has
          # already said they cannot eat: a vegetarian who asks what to have for lunch was told
          # to put ham or tuna in a sandwich, in the turn after the bot said it would plan around
          # the vegetarian. It reads the turns, not only this line, so it needs no diet word here.
          _lunch_ideas_after_a_no,
          # a line that names the food is answered better by that food's own entry
          avoid=("rice", "pasta", "leftover rice", "left over rice", "potato", "potatoes",
                 "egg", "eggs", "chicken", "tuna", "cheese", "mince", "sausages", "bacon",
                 "beans", "chickpeas", "lentils", "tofu", "noodles", "couscous", "quinoa",
                 "salad", "soup", "sandwich", "bread", "ham", "fish",
                 "skipping", "skip", "no time", "missed", "forgot",
                 # "what should i say at a work lunch" is a conversation, not a sandwich
                 "say", "talk", "talk about", "conversation", "small talk",
                 # "im just having my lunch" is small talk, not a plan for lunch
                 "just having", "having my lunch", "just had lunch", "had my lunch",
                 "on my lunch", "eating my lunch",
                 # a lunch for guests is the crowd row's question: see _one_persons_lunch
                 "coming over", "come over", "coming round", "come round",
                 "over for", "round for") + _ON_A_FLIGHT,
          # one person's lunch only: a packed lunch for the family is still a packed lunch
          guard=_one_persons_lunch),
    entry("lunch-no-sandwich",
          (("lunch", "lunches", "lunchbox", "lunchboxes", "lunch box", "lunch boxes",
            "packed lunch", "packed lunches", "school lunch", "school lunches", "work lunch",
            "pack up", "packed up"),
           NO_SANDWICH),
          _no_sandwich_lunch, bias=3,
          # the sandwich itself is the `sandwich` row's question, and the shelf life and the
          # keeping are the cold-lunch row's: this one is only the lunch that leaves bread out
          avoid=("how long", "keep", "keeps", "keeping", "freeze", "frozen", "recipe",
                 "recipes", "calories", "healthy", "allergy", "allergic", "gluten",
                 "coeliac", "celiac") + _ON_A_FLIGHT),

    # "what can i have as a snack" was a search hedge, and so were "what is a healthy snack",
    # "what can i snack on" and "what shall i have for a snack". The lunch and dinner lists
    # answered their own questions, so the snack got one: the rule first, then things in the
    # house. Stopping the habit is the nutrition row's question, not this one.


    entry("snack-ideas",
          (("snack", "snacks", "snacking", "nibbles", "between meals", "in between meals"),
           ("what", "whats", "idea", "ideas", "can i have", "could i have", "should i have",
            "shall i have", "have for", "healthy", "good", "nice", "best", "quick", "easy",
            "instead", "alternative", "alternatives", "suggest", "suggestions", "fancy",
            "filling", "fill", "keep me going", "small", "light",
            # "any snack ideas that arent crisps" and "a snack i can take to work"
            "any", "not", "arent", "aren't", "take to work", "at work", "for work")),
          _a_snack,
          avoid=("stop", "stopping", "cant stop", "can't stop", "why do i", "why am i",
                 "help me", "how do i stop", "break the habit", "habit", "at night", "night",
                 "midnight", "late", "evening", "after dinner", "in bed",
                 # a baby or a child's snack is the baby food table's
                 "baby", "babies", "toddler", "child", "children", "kid", "kids", "son",
                 "daughter", "weaning", "wean", "nursery", "school",
                 # buying them is a shopping question
                 "buy", "buying", "shop", "shopping", "supermarket", "price", "cost",
                 "cheapest", "brand", "best before",
                 # a party or a meeting wants a platter, not a 4pm bite; and a snack for the
                 # road is the travel question - "snack ideas for a long drive" was handed Greek
                 # yoghurt and berries to eat in a car
                 "party", "guests", "buffet", "meeting", "christmas", "birthday", "film",
                 "cinema", "road trip", "flight",
                 "drive", "driving", "car", "journey", "train", "plane", "picnic", "camping",
                 "packed lunch", "lunchbox", "lunch box",
                 # the drinks are not snacks, and the tea rows own them
                 "tea", "coffee", "drink", "juice", "cola"),
          bias=1),

    entry("lunch-exclusion",
          (("lunch", "packed lunch", "lunchbox", "lunch box", "school lunch", "work lunch"),
           ("dont eat", "don't eat", "do not eat", "cant eat", "can't eat", "cannot eat",
            # the third person says the same thing: "for someone who doesnt eat meat" is a
            # vegetarian lunch, and without it the plain lunch entry took the line and listed ham
            "doesnt eat", "doesn't eat", "does not eat", "wont eat", "won't eat",
            "no meat", "meat free", "meat-free", "no cheese", "no dairy", "no eggs", "no egg",
            "no fish", "no tuna", "no ham", "no nuts", "vegetarian", "veggie", "vegan",
            "plant based", "allergic", "allergy", "intolerant",
            "dairy free", "gluten free", "nut free", "egg free",
            # "off dairy at the moment, lunch ideas" is the same refusal as "no dairy".
            "off dairy", "off meat", "off gluten", "off fish", "off eggs")),
          _lunch_ideas_after_a_no, bias=2,
          avoid=("how long", "left out", "freeze", "recipe") + _ON_A_FLIGHT),
    # A baby's food is still food, and a grown-up asking about it wants an answer, not a health
    # visitor. The baby table stands its own rows down on an adult word, which is right - but
    # then nothing answered "can adults have baby rice" or "is baby food healthy for adults", and
    # the composer's baby hand-off sent them to a phone line. This is that answer, and it is here
    # rather than in babyfood.py because the gate in that file is what stands down for it.
    entry("baby-food-for-a-grown-up",
          (("baby rice", "baby porridge", "baby cereal", "baby food", "baby foods",
            "baby puree", "baby purees", "baby yoghurt", "baby biscuit", "baby biscuits",
            "baby pouch", "baby pouches", "baby jar", "baby jars", "jars of baby food",
            "jar of baby food", "baby pasta"),
           ("eat", "eating", "eaten", "adult", "adults", "grown up", "grown ups",
            "grownup", "for adults", "for me", "myself", "healthy", "any good",
            "ok for me", "is it ok", "bad for me", "good for you", "good for me",
            "bad for you", "waste", "finish")),
          "Yes, it is just food: baby rice is finely ground rice, and the jars are ordinary fruit "
          "or vegetables cooked soft with no salt or sugar added, so there is nothing in them a "
          "grown-up needs to avoid. They are bland on purpose and cost several times what the same "
          "weight of rice or fruit does, so finishing a jar is fine and buying them for yourself is "
          "not worth it.",
          # A row may not list its own subject: "baby" inside "baby rice" zeroes the score.
          avoid=("my baby", "a baby", "baby have", "baby has", "give my baby", "infant",
                 "wean", "weaning", "toddler",
                 "6 months", "six months", "month old", "months old", "newborn",
                 "how much", "how many", "portion", "recipe", "how long", "freeze"),
          # "can i eat a whole jar of baby food" is a grown-up's question about the jar, and the
          # shop-bought row keys the same two words: the grown-up's reading wins.
          bias=3),
    entry("nut-allergy",
          (("nut", "nuts", "peanut", "peanuts"),
           ("allergic", "allergy", "allergies", "eat", "avoid", "safe")),
          _nut_free,
          # "present for someone with a nut allergy" is a present, and the safe-food list is not
          # what it asks for.
          guard=not_a_present,
          # "can i eat peanut butter every day" is a question about a food, not about an
          # allergy, and the nut-free meal list ("plenty: meat, fish, eggs...") was handed to
          # somebody asking whether peanut butter is fine daily. The allergy words are what
          # this row is for, so a line asking how often or how much stands it down.
          avoid=("dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "vet",
                 "every day", "everyday", "a day", "per day", "how often", "how much",
                 "too much", "good for you", "bad for you", "healthy", "fattening",
                 "calories", "lose weight", "gain weight",
                 # A feeding mother's own plate is family.py's question: this row answered "can i
                 # eat peanuts while breastfeeding" with the nut-free shopping list, which is for
                 # a household that has to keep nuts out, not for her diet.
                 "breastfeeding", "breast feeding", "breastfeed", "nursing", "lactating",
                 "chestfeeding", "while feeding")),
    entry("vegan-main", ("vegan", ("main", "dinner", "meal", "cook", "ideas", "make")),
          "A chickpea and spinach curry is easy and filling: fry onion, garlic, ginger and spices, "
          "add a tin of tomatoes and a tin of chickpeas, simmer 15 minutes and stir spinach through "
          "at the end. Serve it with rice, and check the stock cube is vegan."),
    entry("vegetarian-main", ("vegetarian", ("main", "dinner", "meal", "cook", "ideas", "make",
                                             "party", "guests", "cooking")),
          "A roast vegetable and feta traybake is hard to beat: chop peppers, red onion, "
          "courgette and sweet potato, toss in oil, salt and thyme, roast at 200C for 35 minutes, "
          "then crumble feta over and give it 10 more. Serve with couscous and a sharp green salad."),
    # --- eating less meat ------------------------------------------------------
    # Swapping half the meat for pulses is the commonest everyday cooking ask that got a shrug.
    # Each entry is keyed on the thing the person named - the plan, the meat being replaced, the
    # children, the tofu - so "we eat less meat" is not answered with "how to cook tofu". Lentils
    # and chickpeas keep `pulses-soak`, which already answered those lines on main.
    # The topic half and the intent half are separate words rather than one long phrase, because
    # the phrase alone scores 3 and MIN_SCORE is 4: "how do i cut down on meat" is the whole line
    # and still has to reach this entry. "cut" is only here as "cut down"/"cut back" - a bare "cut"
    # next to "meat" is the knife question ("how do i cut meat for a stir fry").
    entry("less-meat",
          (("meat", "meatless", "meat free", "meat-free", "plant based", "plant-based",
            "vegetarian", "veggie", "pulses"),
           ("less", "fewer", "cut down", "cut back", "cutting down", "cutting back", "reduce",
            "reducing", "without", "free", "swap", "swapping", "drop", "dropping", "give up",
            "trying", "start", "started", "tips", "ideas", "help", "advice", "plan", "plans")),
          "Swap rather than subtract: use lentils or a tin of beans for half the mince in a ragu, "
          "mushrooms for the other half, and chickpeas where a curry had chicken, and nobody at the "
          "table notices. Two meat-free dinners a week is easier to keep than a rule; keep the "
          "protein up with eggs, beans, lentils, tofu and cheese, which is the part people get wrong.",
          # a plan question, so a bare "we eat less meat than we used to" is not one
          ask=("how", "what", "any", "should", "tips", "help", "trying", "want", "idea", "ideas",
               "can", "will", "kids", "children", "family", "week", "meals"),
          # "my dog eats less meat than he used to" is a vet question, not a menu one, and the
          # plan beats the swap entry when a line names both ("cheap meals without meat"). One
          # step is not enough for that line: the general meal ideas rank level with the plan and
          # won the tie on file order, so a plan question got the list of dinners instead.
          bias=2,
          # "no meat please, what can i cook with chicken" is a question about cooking chicken, so
          # it belongs to the ingredient. A plan that mentions a meat it likes ("i want to eat less
          # meat but i love chicken") still gets the plan, which is why these are phrases.
          # A line about somebody who already eats no meat is not a plan to cut down: "she doesnt
          # eat meat" after "im cooking something nice for my girlfriend" is about that dish. It
          # reaches this entry through the context rewrite, which lends the line the word "trying"
          # from the turn before, so the guest shapes have to be refused here.
          avoid=("doesnt eat meat", "does not eat meat", "dont eat meat", "do not eat meat",
                 "doesnt eat any meat", "dont eat any meat", "no meat please", "no meat though",
                 "she is vegetarian", "hes vegetarian", "is a vegetarian", "vegetarian guest",
                 "dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "vet", "quorn",
                 "cook with chicken", "cook with beef", "cook with mince", "cook with meat",
                 "cook with lamb", "cook with pork", "cook with bacon", "cook with sausages",

                 "cook with fish", "cook with turkey",
                 # somebody who is already vegetarian is not cutting down: they eat no meat,
                 # and "use lentils for half the mince" is advice for a different person
                 "im vegetarian", "im veggie", "im vegan", "i am vegetarian", "i am veggie",
                 "i am vegan", "im a vegetarian", "im a veggie", "im a vegan",
                 "ive been vegetarian", "vegetarian for years",
                 # nor is a line that asks for a vegetarian meal rather than a plan: "any ideas
                 # for a vegetarian meal" carries "vegetarian" and "ideas" and nothing about
                 # eating less, and the swap advice is a reply to a question nobody asked. The
                 # meal rows name a dish, which is what that line wants. The plural stays out
                 # ("meat free meals this week" is still the plan), so each shape is one meal.
                 "a vegetarian meal", "a vegetarian dinner", "a vegetarian main",
                 "a vegetarian recipe", "some vegetarian", "vegetarian meal ideas",
                 "vegetarian dinner ideas", "vegetarian main", "vegetarian recipe",
                 "a veggie meal", "a veggie dinner", "some veggie", "veggie meal ideas",
                 "a meat free meal", "a meat-free meal", "a meat free dinner",
                 "a meat-free dinner", "something vegetarian", "anything vegetarian")),
    entry("instead-of-mince",
          (("mince", "minced beef", "ground beef", "chicken", "beef", "meat"),
           ("instead", "instead of", "replace", "replacement", "substitute", "substitutes",
            "swap", "alternative", "without")),
          "Swap in pulses: red lentils for mince (a mug of them and a splash more stock, "
          "20 minutes), or a tin of green lentils and chopped mushrooms for the texture, and "
          "chickpeas, tofu or big flat mushrooms where there was chicken. Season it the way you "
          "would the meat, with stock, soy or paprika, and the swap goes unnoticed.",
          # cooking, freezing and reheating meat are their own questions
          avoid=("dog", "dogs", "cat", "cats", "puppy", "pet", "pets", "raw", "freeze", "frozen",
                 "thaw", "thawed", "defrost", "reheat", "leftover", "leftovers", "how long",
                 "safe", "gone off", "off", "meal", "meals", "dinner", "dinners", "cheap",
                 "recipes", "recipe", "ideas", "menu", "veg", "vegetarian", "vegan")),
    # "can i use turkey mince in chilli" and "can i use turkey mince in spag bol" were honest
    # passes: `instead-of-mince` is about swapping meat out altogether, and this is a swap of one
    # mince for another.
    entry("use-a-leaner-mince",
          (("turkey mince", "chicken mince", "quorn mince", "soya mince", "soy mince",
            "lean mince", "5% mince", "turkey breast mince", "vegan mince", "veggie mince"),
           ("can i use", "can i swap", "use", "instead", "swap", "works", "work",
            "in chilli", "in a chilli", "in spag bol", "in spaghetti bolognese", "in bolognese",
            "in lasagne", "in a lasagne", "in cottage pie", "in a cottage pie", "in ragu")),
          "Yes, weight for weight, and it needs a hand: turkey and chicken mince are leaner than "
          "beef, so brown them in a tablespoon of oil and add a splash more stock than the recipe "
          "says, or they go dry and chalky. Quorn and soya mince are a straight swap too - use "
          "the same volume, add stock, and give them fifteen minutes rather than forty. In a "
          "chilli or a bolognese nobody notices.",
          avoid=("dog", "dogs", "cat", "cats", "puppy", "pet", "raw", "freeze", "frozen",
                 "defrost", "reheat", "how long", "safe", "gone off", "christmas", "roast",
                 "stuffing", "carve", "whole bird", "thaw")),

    entry("beans-kids",
          (("beans", "lentils", "chickpeas", "peas"),
           ("kids", "children", "child", "toddler", "fussy", "hate", "hates", "wont eat",
            "won't eat", "refuse", "refuses", "faddy")),
          "Mash them in rather than serve them whole: beans or lentils blended into a tomato sauce "
          "or a shepherd's pie disappear, and peas or sweetcorn folded through rice do too. Put the "
          "new thing next to something they already eat, no bargaining and no second dinner, and "
          "keep offering it - it can take eight or ten tries before a child accepts a food.",
          avoid=("allergic", "allergy", "rash", "wind", "gas", "bloating", "dog", "dogs", "cat",
                 "cats", "puppy", "kitten")),
    entry("cook-tofu",
          ("tofu", ("cook", "cooking", "crispy", "crisp", "taste", "tasteless", "fry", "fried",
                    "bake", "marinade", "marinate", "press", "squeaky", "nice")),
          "Press it first: wrap the block in kitchen paper, weight it down for 15 minutes, then "
          "cube it and toss it in cornflour. Fry in a hot pan with a little oil until golden on "
          "two sides, and stir the sauce in off the heat - tofu added to a wet pan steams and stays "
          "soft. It is meant to taste of nothing, so it takes on whatever it is cooked with."),
    entry("protein-no-meat",
          # "will they get enough protein" is the follow-up after the plan, and it carries
          # neither "without meat" nor "vegetarian": `enough` is what makes it the same question.
          ("protein", ("without meat", "no meat", "no meat or fish", "meat free", "meat-free",
                       "plant based", "plant-based", "vegan", "vegetarian", "enough",
                       "get enough", "will they",
                       # "cheap sources of protein" and "what is the cheapest protein" are the
                       # same question as "enough protein without meat": which foods, and how
                       # much. "complete" is the other end of it ("is rice and beans a complete
                       # protein"), which the reply answers from the line.
                       "cheap", "cheapest", "budget", "afford", "affordable", "source",
                       "sources", "complete",
                       # Asking what to eat for protein is asking for this list, not for what
                       # protein is. The definition row in science.py keys the bare "what", so
                       # "what should i eat for protein" and "what foods are high in protein"
                       # were answered with "chains of amino acids" while "where do i get
                       # protein" got the food. The words below are the ask, so the list takes
                       # every one of them, and the definition row holds them out.
                       "what should i eat", "what should i have", "what do i eat",
                       "what can i eat", "what to eat", "what should i be eating",
                       "what foods", "what food", "which foods", "which food",
                       "eat for protein", "eat to get protein", "foods for protein",
                       "high in protein", "protein rich", "protein-rich", "lots of protein",
                       "good protein", "best protein", "what has protein")),
          _protein,
          # building muscle is a different question with a different answer
          avoid=("muscle", "muscles", "gym", "bulk", "bulking", "whey", "shake", "shakes",
                 "bodybuilding", "gaining"),
          # A line that names a nutrient is about the nutrient: "how do i get more protein
          # without meat" belongs here, not to the plan to cut down, which also answers it. The
          # two rank level with the plan's rarity counted, and the tie went to whichever entry
          # came first in the file, so the plan took the protein question back as soon as a
          # chicken-protein entry made "protein" a common word. One above the plan's own nudge,
          # so this entry still wins the line that names both.
          bias=2),
    # The second row called `party-food`: this is the plan-the-food answer, and the older row
    # above answers the "something to take to a party" ask. One id each, so neither copy hides
    # behind the other.
    entry("party-food-plan",
          (("party", "buffet", "picnic", "guests", "people coming", "friends coming",
            # A baby shower is a party, and the word "baby" in it was stealing the line: "im
            # having a baby shower what food should i make" got the health visitor and "baby
            # shower food ideas" got the list of muslins. The shower is the occasion, and the
            # food for it is the same plan as any other standing-up do.
            "baby shower", "baby showers", "bridal shower", "baby sprinkle"),
           ("food", "snacks", "nibbles", "finger food", "ideas", "cheap", "feed", "make",
            # "cook" and "serve" are the same ask as "make", and without them in the key
            # "what should i cook for a baby shower" scored nothing at all
            "cook", "cooks", "cooking", "serve", "serving")),
          "Cheap party food people actually eat: a big pot of chilli or a pasta bake, garlic bread, "
          "and a bowl of crisps and dips. For standing-up food, sausage rolls, cheese straws and "
          "fruit on sticks go further than anything fiddly.",
          # "make", "cook" and "serve" are how the host asks, and "what should i make for a
          # baby shower" has no food word in it at all.
          ask=("party", "buffet", "picnic", "guests", "food", "snacks", "nibbles",
               "make", "makes", "making", "cook", "cooking", "serve", "serving", "feed"),
          # "snacks" is on the snack row's key as well, and a word two rows use is worth a point
          # less to both: with the snack row added, "good snacks for a party" lost this card to
          # the plainer party row and read "Cheap food that people finish and that travels"
          # instead of the buffet plan. The party is this row's subject, so it keeps the point.
          bias=1,
          # "how do i make conversation at a party" is the small-talk answer, not the buffet:
          # "party" and "make" are enough for this key on any line with a make in it.
          avoid=("cake", "decorations", "music", "playlist", "venue", "invite", "invitation",
                 "conversation", "small talk", "mingle", "mingling", "nobody to talk",
                 "know anyone", "networking", "talk to people",
                 # the same small-talk answer is reached from "what should i say" and from a
                 # nervous guest, and neither is a bowl of crisps.
                 "what to say", "talk about", "nervous", "strangers") + ("picnic", "picnics")),
    entry("kids-vegetables",
          (("toddler", "kid", "kids", "child", "children", "son", "daughter")
           # the age is how a parent names the child: "my 2 year old refuses vegetables" is
           # "my son refuses vegetables" with the age where the word would be
           + _AGE_WORDS,
           ("vegetables", "veg", "broccoli", "greens", "carrot", "carrots", "fussy")),
          _kids_veg,
          ask=("vegetables", "veg", "broccoli", "greens", "carrot", "carrots", "fussy",
               # the second half of the question is often a method with no child in it:
               # "my son wont eat vegetables" then "should i just blend veg into a sauce"
               "blend", "blended", "blender", "puree", "pureed", "purée", "hide", "hidden",
               "sneak", "mask", "grate", "grated"),
          # "whats a quick dinner for two kids who wont eat anything green" is a meal question,
          # and the pantry answers it with a dish everybody can eat
          # A child who will not eat beans or lentils is the beans answer, not the greens one:
          # that entry is about pulses and knows what to do about them.
          # "what can i cook for a kid who hates vegetables" is the feeding question, not the
          # dinner one: a "cook" in the line no longer sends it to the meal ideas, only a
          # dinner/tea/quick/recipe word does.
          avoid=("dinner", "dinners", "tonight", "for tea", "quick", "recipe", "recipes",
                 "bean", "beans", "lentil", "lentils", "chickpea", "chickpeas", "pulses",
                 # an age names a child only when the person is one: "my 40 year old husband
                 # wont eat veg" is a grown-up who can serve himself, and so is a parent whose
                 # own diet the line is about
                 "husband", "wife", "partner", "boyfriend", "girlfriend", "my mum", "my dad",
                 "my mother", "my father", "my stepdad", "my stepmum", "my nan", "my gran"),
          # the meal ideas answer the same line too (they score higher), and a child who will not
          # eat veg wants the feeding answer, so the specific row is ranked above the general one
          bias=1),
    entry("cheese-board", ("cheese", ("board", "platter", "party", "guests")),
          "For six people, pick three or four cheeses: something soft like brie, a hard one like a "
          "mature cheddar, a blue, and something goat's or sheep's for variety. Add crackers, "
          "grapes, chutney and nuts, and take them out of the fridge an hour before."),
    entry("cook-a-staple", (_STAPLE_NAMES, STAPLE_ASK), _staple, bias=1,
          # how much of it to buy is the portion table's question and how long to cook it is
          # this row's, so the bare "how much" and "how many" live in a guard instead of in the
          # avoid list: see `_not_a_portion_ask`.
          guard=_not_a_portion_ask,
          # "how long does uncooked rice last" is the keeping answer, not the method: "last" and
          # "uncooked" were the gap that let this entry answer a keeping question with a recipe.
          # a licence or a permit is the angling answer, not a recipe: "do i need a licence to
          # fish" was getting the baked-fish method. Only the paperwork words are held out, so
          # "how do i cook fish" keeps this entry.
          avoid=("play squash", "playing squash", "squash court", "game of squash",
                 "racquetball", "licence", "license", "licencing", "licensing", "permit",
                 "angling", "angler",
                 "rod", "tackle", "bait", "close season", "day ticket",
                 # a tank is not an ingredient: "how do i clean a fish tank" and "how do i clean
                 # my fish tank" got a method for baking fish, because "fish" is a staple name
                 # and "how do i clean" is one of the asks.
                 "tank", "tanks", "aquarium", "fish tank", "fish tanks", "fishbowl",
                 "fish bowl", "gravel", "dechlorinator",
                 # a fish in a tank that wants feeding is not a fish for the pan: the staple name
                 # plus "how" was enough for "how often do you feed a fish" and "how often do i
                 # feed fish", which were both told to bake fillets for 12 to 15 minutes. Only
                 # the pet phrases, so "how do i cook fish for a family" keeps this row.
                 "goldfish", "tropical fish", "koi", "betta", "guppy", "pet fish",
                 "feed the fish", "feed a fish", "feed my fish", "feed fish",
                 "feed the goldfish", "feeding the fish", "feeding fish", "fish flakes",
                 # the same animal kept as a pet is the pet's own question: "what do i need for
                 # a rabbit" reached this row on the staple name plus the "do i" of the ask and
                 # came back with a braise. A hutch, a cage, bedding or a buying shape says the
                 # animal is not for the pan, and "how do i cook rabbit" keeps the braise.
                 "hutch", "hutches", "cage", "cages", "guinea pig", "guinea pigs", "cavies",
                 "hamster", "hamsters", "budgie", "budgies", "pet", "pets", "bedding",
                 "look after", "care for", "what do i need", "need for", "need to buy",
                 "need to get", "need before",
                 # how they get on with each other is the pet question as well: "how do i bond
                 # two rabbits" came back with the braise, and a rabbit of yours is not a joint.
                 # ("my rabbit" and "our rabbit" are not here: "our rabbit died, do i need a
                 # funeral director" is a pet-loss line, and standing this row down for it let a
                 # weaker condolence take the turn from the grief answer that fits the question.)
                 "bond", "bonding", "bonded", "introduce them", "two rabbits",
                 "pet rabbit", "house rabbit", "as a pet",
                 # how long the animal can be left is the pet's own question, and "how long" is
                 # one of this row's asks: "how long can a rabbit be left alone" was the braise.
                 "alone", "left alone", "on its own", "on her own", "on his own", "lonely",
                 "last", "lasts", "lasting", "uncooked", "airtight", "stale", "staleness",
                 "leftover", "leftovers", "left over", "go with", "goes with", "gone off",
                 "per person", "portion", "portions", "serving", "servings",
                 "freeze", "freezer", "refreeze", "reheat", "keep", "keeping", "store", "ratio",
                 # where it is kept is a keeping question: "how long can i leave cooked rice in the
                 # fridge" wants the cooked-rice rule, not the method that cooked it.
                 "fridge", "refrigerator", "out of the fridge", "left out", "leave it out",
                 "leaving it out",
                 # "<bone> stock" is the stock pot, not the staple: the staple name sits in this
                 # key, so "how do i make vegetable stock" answered with the rule for boiling
                 # vegetables rather than the stock row it belongs to.
                 "beef stock", "chicken stock", "turkey stock", "ham stock", "lamb stock",
                 "pork stock", "fish stock", "vegetable stock", "veg stock", "bone broth",
                 "stock cube", "stock cubes", "stock pot", "stockpot",
                 "dry", "sticky", "stuck", "salty", "lumpy", "lumps", "gluey", "claggy", "soggy",
                 "watery", "microwave", "sunk", "pink", "burnt",
                 "scrambled", "scramble", "poach", "poached", "fried", "fry", "omelette",
                 # "when do i harvest my onions" is a harvest question with a "do i" in it, and it
                 # used to come out as the method for frying them: the picking words stand the
                 # method down so the crop's own harvest row answers.
                 "harvest", "harvesting", "pick", "picking", "picked", "lift", "lifting",
                 "dig up", "dig them up", "ripe", "ripen", "when are they ready",
                 "plant", "grow", "paddy", "field", "sick", "allergy", "allergic", "wine",
                 # a vegetable patch is where they are grown, not how they are cooked
                 "patch", "veg patch", "vegetable patch", "plot", "allotment", "raised bed",
                 "raised beds", "kitchen garden", "sow", "sowing", "harvest", "crop", "crops",
                 # a crop in the ground is the gardener's line, not the pan's, but the grown
                 # crop cannot be kept out from here: "how do i know when my carrots are done" is
                 # a cook asking for the time, and a when-form in this list swallowed it. The
                 # harvest rows carry the done-words instead, so a gardener's line goes to the
                 # garden and a pan's line comes back here.
                 "slimming", "calories", "syn", "syns", "points", "crispy", "roast",
                 # a fault has its own answer already: rice that sticks, porridge that boils
                 # over, pasta that clumps - the plain method does not answer any of them
                 "stop", "sticking", "sticks", "stuck together", "clumping", "clumps",
                 "boil over", "boils over", "boiling over", "boiled over",
                 # and a different staple is a different answer: rice noodles are not rice
                 "noodles", "noodle", "vermicelli",
                 # the same rule for a staple with a method of its own: the fish rows of BASICS
                 # named fish fingers, so "how do i cook fish fingers" went to the plain fish
                 # method instead of the 12 to 15 minutes at 200C answer written for them
                 "fish finger", "fish fingers", "fishfinger", "fishfingers",
                 # a qualifier makes it a different recipe, not the plain method: mash without
                 # butter, mash for a baby, rice you wash first all have their own answer
                 # ("without" alone cannot go here: "rice without a rice cooker" is the pan method)
                 "without butter", "without milk", "without dairy", "no butter", "no milk",
                 "dairy", "dairy free", "vegan", "mash", "mashed", "mashing",
                 "baby", "babies", "toddler", "weaning",
                 "wash", "washing", "rinse", "rinsing",
                 # a bean or a pea that is soaked is the dried pulse's question, and this entry
                 # answers the fresh one: "how long do you soak broad beans" was the four-minute
                 # boil of a fresh pod, because the staple's name is in this key. The soaking
                 # entry knows the times, so the plain method stands down on the soaking words.
                 "soak", "soaks", "soaking", "soaked", "overnight", "quick soak", "no soak",
                 # "how long does cooked rice last in the fridge" is a keeping question, and it
                 # was reaching the rinse-and-simmer method with no rice turn before it
                 "fridge", "fridged", "last", "lasts", "frozen", "days", "weeks", "month",
                 # a fish that breathes is not a fish to cook: "how do fish breathe underwater"
                 # reached the plain fish method on "fish" and "how"
                 "breathe", "breathes", "breathing", "underwater", "gills")),
    entry("potato-boil",
          # "how long do spuds take to boil" is the same question as "how long do potatoes
          # take", and spuds and tatties are how half the country asks it.
          (("potato", "potatoes", "new potatoes", "spud", "spuds", "tattie", "tatties"),
           ("boil", "boiling", "how long", "minutes", "tender", "soft", "done",
            "cook", "cooking", "make",
            # "how do i stop potatoes going mushy" and "my potatoes always fall apart" are the
            # same timer question asked as a fault, and neither had a row: mushy, fall apart and
            # break up are the words people use for it
            "mushy", "mush", "soggy", "watery", "fall apart", "falls apart", "falling apart",
            "fell apart", "break up", "breaks up", "breaking up", "broke up", "crumbly",
            "disintegrate", "disintegrates")),
          "Boil them in salted water: 10 to 12 minutes for small new potatoes, 15 to 20 for chunks, "
          "20 to 25 for whole medium ones. A knife should slide in with no resistance at all, and "
          "drain them the moment it does, or they go watery. If they keep going mushy, it is "
          "usually the potato rather than the pan: floury ones (Maris Piper, King Edward, Desiree) "
          "break up in water and are for mashing and roasting, so boil the waxy ones (Charlotte, "
          "Nicola, any new potato) and keep the water at a gentle simmer rather than a rolling "
          "boil, and do not stir them.",
          # "how long" is in this key, and it is in everybody else's potato question too: the
          # keeping one ("how long do potatoes keep"), the roasting one ("how long do roast
          # potatoes take", which used to be told to boil them) and the jacket one.
          # "how long do potatoes keep" is a keeping question, not a timer, and a potato inside a
          # dish - a gratin, a salad, sweet potato - is that dish's question
          avoid=("keep", "keeps", "keeping", "store", "storing", "last", "lasts", "gone off",
                 "sprout", "sprouting", "sprouts", "mouldy", "fridge", "freezer",
                 "green", "greening", "gone green", "gone soft",
                 "roast", "roasting", "roasted", "oven", "jacket", "baked", "bake",
                 "gratin", "dauphinoise", "salad", "sweet", "scalloped", "wedges", "crispy",
                 "chips",
                 # a pan of water is not a microwave or an air fryer either
                 "microwave", "microwaved", "microwaving", "air fryer", "air fry", "airfryer",
                 "air fried")),
    # Chips that came out soft are answered on main now, by `veg-chips-crisp` in
    # bot/knowledge/vegetables.py: that row owns the chip fault and its key gained "wedges" with
    # this change, so there is one chips answer and not two.
    # Where a hot pan can go, asked four ways and answered with nothing: "can i put a hot pan on a
    # glass hob" was the burn card until the safety arm stopped reading "put ... hot pan" as a
    # scald, and a punting gap after it. The surface is the question, so the surface words are the
    # key and the reply is about heat shock, not about the pan.
    # The pan that is still screaming hot and the sink: a cold plunge warps a thin pan and cracks
    # enamel and cast iron, and "is it safe to put a hot pan in cold water" was a water-safety card.
    entry("hot-pan-cool",
          (("pan", "pans", "saucepan", "frying pan", "wok", "skillet", "pot", "enamel pan",
            "cast iron", "baking tray", "roasting tin",
            # A tin that comes out of the oven is the same hot thing as a pan: "can i put my
            # cake tin in cold water to cool it" was answered with how to keep a cool bag cold.
            "cake tin", "tins", "loaf tin", "muffin tin", "springform", "baking dish",
            "oven dish", "casserole dish", "dutch oven", "stock pot", "griddle", "chip pan",
            "pie tin", "tray"),
           ("cold water", "cold tap", "in the sink", "into the sink", "under the tap", "rinse",
            "cool it down", "cool down", "cooling down", "cooling it", "cool my pan",
            "cool the pan", "cool a pan", "ice water", "quench", "thermal shock", "soak it",
            "run it under", "let it cool", "crack", "cracked", "plunge",
            "straight away", "right away", "hot pan",
            # Washing is the same wait with a different reason: the pan is being cooled to be
            # cleaned, not to be stored, and the fridge row was taking every "let the pan cool".
            "cool before washing", "cool it before washing", "let it cool before washing",
            "let the pan cool before", "cool the pan before", "before washing",
            "before i wash", "before washing up", "cool it first", "cool first",
            "warm water",
            # The question before the damage: "will cold water warp my pan" is this row's, and
            # the pan that has already gone is the row below.
            "will it warp", "will cold water", "warp my pan", "warp it", "warping my pan")),
          "Give a very hot pan five minutes before it meets cold water: a thin stainless or "
          "aluminium pan can warp, and enamel or cast iron can crack. Warm water first, or fill the "
          "sink and set the pan in it rather than running the tap straight onto it. Deglazing on the "
          "hob with a splash of stock or wine is fine - it is the cold plunge from a screaming pan "
          "that is not.",
          avoid=("glass hob", "worktop", "counter", "countertop", "granite", "quartz", "marble",
                 "laminate", "wooden board", "chopping board", "trivet", "glass table",
                 # The glass surface said the other way round: "can i put a hot pan on a glass
                 # top table" and "on the glass top" were this row's cold-plunge answer, because
                 # a table called a glass top matches none of the surface words above. The
                 # surface row reads that phrase itself, and a bare glass top there falls to the
                 # balanced answer rather than to a yes, because a glass top is as often a table
                 # as a hob.
                 "glass top", "glass-top",
                 # "taps" stood this row down for its own key phrase: a stand-down word is read
                 # as a stem, so "under the tap" was a line the row could never answer, and
                 # "can i put my hot wok under the tap" went to the pan-heat card instead. The
                 # plumbing line it was there for names the fitting, so the fitting is the word.
                 "isolation valve", "stopcock", "stop cock", "mixer tap", "kitchen tap",
                 "dripping tap", "leaking tap", "tap washer", "cistern", "boiler",
                 # The surface the pan was set down on is the surface row's question, and it was
                 # losing every one of these to this row's bias: "can i put a hot pan straight on
                 # the hob" and "can i put a hot pan on a wooden table" were both told that cold
                 # water warps a pan.
                 "hob", "hobs", "gas hob", "electric hob", "on the hob", "ring", "on the ring",
                 "wooden table", "wood table", "the table", "work surface", "worksurface",
                 "benchtop", "on the side", "rested the hot", "rested a hot", "put the hot",
                 "placed the hot", "set the hot", "stood the hot",
                 "heating", "radiator", "shower", "bath", "washing machine",
                 # a pan that has already gone is the row below, and a warped board is the
                 # board's own oil answer
                 # phrases, not the bare "warped": a stand-down word is read as a stem, so
                 # "warped" here stood this row down for "will cold water warp my pan" too, and
                 # the pan that has not gone yet was told what to do once it has
                 # "where can i put a hot pan" asks where, and the surface row answers it; this
                 # one told them to let it cool, which is not what was asked
                 "where can i put", "where do i put", "where should i put", "where to put",
                 "where can i set", "what can i put it on",
                 "has warped", "already warped", "is warped", "gone warped", "it warped",
                 "wont sit flat", "doesnt sit flat", "doesn't sit flat", "spins on the hob",
                 "rocks on the hob",
                 # A pan that has already warped is the row above, which says what a warped base
                 # means: "my pan warped after i ran it under the tap" was this row's "give a very
                 # hot pan five minutes", advice a day late. Phrases, not the bare "warped", for
                 # the reason given above.
                 "my pan warped", "warped after", "warped from", "pan has warped",
                 "pan is warped", "pan warped",
                 # A pan for the dishwasher is the dishwasher row's question, hot or not, and so
                 # is a pan for the fridge: "can i put a hot pan in the fridge" was this row's
                 # cold-water card, and the keeping row has the answer (straight in is fine)
                 "dishwasher", "fridge", "freezer", "refrigerator"),
          ask=("can i put", "can i rinse", "is it ok to put", "is it safe to put", "should i rinse",
               "in cold water", "cold water", "under the tap", "before washing", "before i wash",
               "cool before", "cool it", "let it cool", "let the pan cool", "will it warp",
               "warp my pan", "warp it", "warp", "warping",
               # The asks people actually bring: "should i cool my pan under the tap" and
               # "how do i cool down a hot baking tray quickly" were a shrug and a stretching
               # routine, because "should i" and "how do i cool" were not in this list.
               "should i", "shall i", "is it safe", "safe to", "ok to", "okay to",
               "how do i cool", "how to cool", "how can i cool", "how do you cool",
               "cool my", "cool the", "cool a", "cool down"),
          # "can i put a hot pan in cold water" was the water-on-a-run card on sport (7 points)
          # with this row at 6: the pan and the sink are what the line is about, and a runner's
          # hydration is not. Measured against 24 pan, sink and washing lines, none of which
          # changed hands.
          # Raised from 3 to 6 for the lines the same row still lost: "can i put my hot wok
          # under the tap" was the pan-heat row's "Hold your hand an inch above the surface"
          # (bias 5, and it keys the wok and the word hot), which is how to tell a pan is hot,
          # not what cold water does to one. A line the surface row owns keeps its avoid words
          # (worktop, granite, trivet, glass hob) and stands this row down.
          bias=6),
    entry("hot-pan-surface",
          (("pan", "pans", "saucepan", "saucepans", "frying pan", "wok", "skillet", "pot", "pots",
            "griddle", "casserole", "baking tray", "roasting tin",
            # the thing set down is often named by its shape rather than as a pan: "i placed the
            # hot tray on the table" and "i put the hot kettle down on the worktop" reached
            # nothing at all, because "baking tray" was the only tray in the group
            "tray", "trays", "tin", "tins", "dish", "dishes", "kettle", "casserole dish",
            # ...and a tin out of the oven is set down the same way as a pan
            "cake tin", "loaf tin", "muffin tin", "baking dish", "dutch oven", "pie tin"),
           ("hot pan", "hot pans", "glass hob", "glass top", "ceramic hob", "induction hob",
            # "where can i put a hot pan" names no surface and was answered with how to tell a
            # pan is hot; the question is where, and this row is where
            "where can i put", "where do i put", "where should i put", "where to put",
            "where can i set", "where can i stand",
            "worktop", "worktops", "counter", "countertop", "granite", "quartz", "marble",
            "laminate", "wooden worktop", "wood worktop", "glass table", "trivet", "table",
            "wooden table", "wood table", "the table", "work surface", "worksurface", "benchtop",
            "on the side", "chopping board", "wooden board", "straight off the hob", "off the ring",
            # the thing that was set down, said as a tray or a dish rather than a pan
            "hot tray", "hot roasting tin", "hot baking tray", "hot dish", "hot pot",
            "hot casserole", "hot kettle")),
          # The verdict for the surface the line names, then the same two sentences: "can i put a
          # hot pan on a granite worktop" opens on the no, and "can i put a hot pan on a glass
          # hob" on the yes. See `_a_hot_pan_surface`.
          _the_hot_pan_place,
          # a pan to be washed, a pan of burnt food and a hob to be cleaned are their own rows,
          # and cold water on a hot pan is a warping question rather than a surface one
          avoid=("clean", "cleaning", "wash", "washing", "scrub", "soak", "burnt", "stain",
                 "stains", "cold water", "sink", "warp", "warped", "season", "seasoning",
                 "dishwasher",
                 # a pan for the fridge or the freezer is the keeping row's question, and this
                 # row's "where can i put" ask was taking it: "can i put a hot pan in the fridge"
                 # is where the pan can keep, not where it can be set down
                 "fridge", "freezer", "refrigerator",
                 # A pan with food in it is cooking, not a place to put a pan down: "i put the
                 # chicken in a hot pan" was this row's answer, which is about a worktop, and the
                 # chicken card is the one that was being asked for. Anything that goes into the
                 # pan says so, and so does the phrase itself.
                 "in a hot pan", "in the hot pan", "in a pan", "in the pan", "into the pan",
                 "into a hot pan", "chicken", "meat", "steak", "beef", "pork", "lamb",
                 "mince", "bacon", "sausage", "sausages", "fish", "salmon", "prawn",
                 "prawns", "egg", "eggs", "oil", "butter", "onion", "onions", "garlic",
                 "potato", "potatoes", "veg", "vegetables", "rice", "pasta", "noodles",
                 "sauce", "tofu", "mushroom", "mushrooms", "flour", "dough", "pancake"),
          # The line that says where the pan has already gone is the same question as the one that
          # asks where it can go: "i put the hot pan on the worktop", "i placed the hot tray on
          # the table" and "i rested the hot tray on the side" were all "How was it, overall?" or
          # a burn card, because the ask group only held the asking forms.
          ask=("can i put", "can i stand", "can i set", "where can i put", "where do i put",
               "is it ok to put", "is it safe to put", "put a hot", "where should i put",
               "what should i put", "i put", "i placed", "i set", "i stood", "i rested",
               "put the hot", "placed the hot", "set the hot", "stood the hot", "rested the hot",
               "put it on", "placed it on", "set it on", "what happens",
               # how the placement question is asked without a verb of putting: "hot pan on
               # laminate worktop is that ok", "does a hot pan crack granite", "is a hot pan ok
               # on a glass table" all reached a cleaning or repair card instead
               "is that ok", "is that alright", "is that safe", "is it ok on", "is it safe on",
               "hot pan on", "hot tray on", "hot dish on", "hot pot on", "hot tin on",
               "does a hot", "will a hot", "can a hot", "can a hot pan",
               "ok on", "safe on", "alright on", "straight off", "off the oven"),
          # the mark-on-a-worktop row answers the mark already there and shares "worktop" and
          # "mark" with this one, so this row has to win the tie: the question is where the pan
          # goes. What keeps the two apart is the guard, not the bias - the placement words say
          # nothing about heat.
          guard=_a_hot_thing_is_being_set_down,
          # the mark row also carries "hot pan" and "hot tray", so a placement line matches both;
          # the higher bias is what gives the question about the pan the pan's answer.
          # Raised from 3: "where can i put a hot pan" scored 5 on the pan-heat row, which answers
          # how to tell a pan is hot, and 3 here, which is where a hot pan can go. 6 is above
          # that row's 5, and a line this row's avoid words name still stands it down.
          bias=6),
    entry("pan-dry",
          (("pan", "pans", "saucepan", "saucepans", "pot", "pots", "wok", "skillet", "pan"),
           ("boiled dry", "boils dry", "boil dry", "boiling dry", "boiled away", "boils away",
            "all boiled away", "went dry", "dried out", "ran dry", "left it on", "left the pan",
            "forgot it", "forgot about it")),
          "Take it off the heat and let it cool where nobody will grab it - and do not put cold "
          "water in it while it is hot, because a hot dry pan can warp or crack and the steam "
          "spits. Once it has cooled, look at the base: a rainbow tint or a blue-black patch is "
          "the metal heat-tinted, which is fine and does not affect the cooking, while food stuck "
          "on lifts in a soak of hot water and a spoon of bicarbonate of soda. A pan that boiled "
          "dry with nothing in it usually only needs a wash, and one with milk or sugar in it "
          "wants the soak.",
          avoid=("how long", "how many", "what temperature", "buy", "best pan", "non stick",
                 "nonstick", "which pan", "recipe")),
    entry("chips-cook",
          (("chips", "oven chips", "frozen chips", "fries", "french fries"),
           ("cook", "cooking", "oven", "air fryer", "fryer", "best", "properly", "how long",
            "bake", "homemade", "perfect")),
          ("Frozen chips want 20 to 25 minutes at 200C (180C fan), turning once; an air fryer does "
           "them in 12 to 15 minutes at 200C, shaken once. Fresh-cut chips take 30 to 35. One "
           "layer with space between them, and salt when they come out: a crowded tray steams."),
          # no ask gate: "frozen chips, how long" is the same question without a question word,
          # and the food words below keep the rest out. A bare "what temperature" is the temp
          # table's line, not this one: it answers the number on its own, and this reply must not
          # argue with it over 20 degrees.
          # The staple table does not take chips at all, so this is the entry for the everyday
          # chip line; without it "how do i cook frozen chips" went to the freezing answer.
          avoid=("temperature", "portion", "portions", "per person", "how much", "price", "buy",
                 "shop",
                 "freezer", "freeze", "refreeze", "defrost", "heating up", "reheat", "leftover",
                 "left over", "chip shop", "takeaway",
                 "healthy", "healthier", "unhealthy", "calorie", "calories", "fat", "fattening",
                 "nutrition", "good for", "cholesterol", "salt", "diet",
                 # frying your own from scratch is another answer, not frozen-oven timing
                 "from scratch", "scratch")),
    entry("leftovers-freeze",
          (("freeze", "freezing", "frozen", "defrost"),
           ("leftovers", "leftover", "curry", "stew", "soup", "mash", "mashed potato", "cooked",
            "rice", "bolognese")),
          "Most cooked food freezes well: cool it within two hours, pack it in portions and label "
          "the date. Eat it within three months for the best quality, defrost it in the fridge "
          "overnight and reheat it once until piping hot. Mashed potato freezes well but goes grainy "
          "if you reheat it in a microwave, so warm it through in a pan with a splash of milk. Rice "
          "is the one to be careful with: freeze it within an hour of cooking, not the next day."),
    entry("reheat-leftovers",
          (("reheat", "reheating", "reheated", "heat up", "heat it up", "warm up", "warm it up",
            "microwave"),
           ("leftovers", "leftover", "curry", "stew", "soup", "mash", "mashed potato", "bolognese",
            "takeaway", "pizza", "rice", "chicken", "fish", "pie", "pasta", "dinner", "plate",
            "food")),
          "Reheat it until it is piping hot all the way through, not just warm at the edges: a splash "
          "of water, a lid on, and a stir halfway so it heats evenly. In a microwave, cover it, heat "
          "in one-minute bursts, then let it stand two minutes; in a pan or an oven it wants about 20 "
          "minutes at 180C. You can reheat leftovers once only - chicken and rice are the two to be "
          "strictest with - so heat what you are going to eat and bin the rest.",
          # pizza is the one leftover that wants dry heat: "how do i reheat pizza" was told to put
          # a splash of water in a lidded pan, which is right for curry and wrong for a slice
          #
          # "microwave" is in the key because people say "can I microwave this", so the entry has
          # to say what it is about: how a microwave works is a science question, not a leftover.
          ask=("reheat", "reheating", "reheated", "heat up", "heat it up", "warm up", "warm it up",
               "leftovers", "leftover", "curry", "stew", "soup", "mash", "mashed potato",
               "bolognese", "takeaway", "pizza", "rice", "chicken", "fish", "pie", "pasta",
               "dinner", "plate"),
          avoid=("bottle", "baby", "formula", "milk feed", "bread", "cake", "pizza")),
    entry("reheat-jacket",
          (("reheat", "reheating", "reheated", "heat up", "heat it up", "warm up", "crisp up",
            "reheat them"),
           ("jacket potato", "jacket potatoes", "baked potato", "baked potatoes")),
          "A jacket potato comes back best at 200C (180C fan): split it open, brush the cut faces "
          "with oil so they crisp, and give it about 20 minutes, or 8 to 10 if you only want it hot "
          "right through. Three minutes in the microwave and then 10 in the oven is quicker and "
          "nearly as good; on its own a microwave leaves the skin soft and leathery.",
          avoid=("salad", "tuna", "cheese", "filling", "keep", "keeps", "how long",
                 "still good", "gone off", "grow", "plant")),
    entry("reheat-pizza", (("pizza", "slice", "slices"),
                           ("reheat", "reheating", "heat up", "warm up", "cold", "leftover",
                            "left over", "next day", "soggy", "crispy")),
          "Dry heat, not the microwave: 200C for 8 to 10 minutes straight on the oven shelf, or in a "
          "covered frying pan on a low heat for 5 minutes - both give you a crisp base again. A "
          "microwave heats the water in the sauce and turns the base to leather, so only use it for "
          "10 seconds if you want it warm rather than good."),
    # The same question with the dish left out: "can i freeze the rest", "can i freeze it",
    # "will this freeze". The rest of the store answered these with a search hedge while the
    # general rule - cool it within two hours, box it while it is still warm, about three months,
    # never refreeze once thawed - sat in `freeze-food`'s own fallback, because that row's key
    # wanted a food name and these lines name nothing.
    #
    # It is a row of its own rather than the pointing words added to `freeze-food`: the wider key
    # stopped that row reaching a freeze question through the chat ("and if i freeze it" after a
    # chicken was answered with the general rule and now reaches nothing at all), because a row
    # whose key can match the line itself is no longer read as borrowing its subject.
    #
    # The subject is the asking words, not the bare "freeze": "i can read it fine but freeze when
    # someone talks to me" is a person freezing up, and a key of ("freeze" x pointing words)
    # answered it with food. The asking words are never put together in a sentence about the
    # speaker.
    entry("freeze-anything", (_FREEZE_ASKS, _FREEZE_POINTING_WORDS),
          _freeze_food,
          ask=KEEP_ASK,
          # the phrases stay whole: `avoid` matches loosely, and split into single words
          # "from frozen" hands this row "frozen", which is its own subject word
          avoid=("soup", "soups", "broth", "mashed potato", "mash", "refreeze", "refroze",
                 "re-freeze", "thawed", "defrost", "defrosting", "defrosted", "stew", "stews",
                 "casserole", "casseroles", "curry", "curries", "chilli", "chili", "bolognese",
                 "lasagne", "lasagna", "brain freeze", "brainfreeze", "instead", "instead of",
                 "substitute", "swap", "from frozen", "ice cream",
                 "leftover", "leftovers", "left over") + _FREEZE_AVOID,
          bias=0),
    entry("refreeze-food",
          (("refreeze", "refroze", "re-freeze", "freeze again", "frozen again"),
           ("mince", "meat", "chicken", "fish", "rice", "safe", "ok", "okay", "fine", "harm",
            "again",
            # "can i refreeze food that has thawed" names no meat and no dish, so it reached
            # nothing at all: the general word and the thaw are enough to reach this answer.
            "food", "thawed", "defrosted", "has thawed", "thawed out")),
          "Cooked food can go back in the freezer once - cool it within two hours, rice within one, "
          "and rice should only be reheated once after that. Raw meat or fish turns on where it "
          "thawed: on the worktop or in a warm kitchen, cook it and eat it now, because it should "
          "not be frozen again - the thaw lets bacteria multiply and freezing does not undo that. "
          "Only meat or fish that thawed in the fridge can go back in, a bit drier than before.",
          avoid=("bread", "cake", "banana", "milk", "berries")),
    entry("vegetarian-guest", (("vegetarian", "veggie", "pescatarian", "no meat",
                                "doesnt eat meat", "doesn't eat meat", "does not eat meat",
                                "eat much meat", "much meat", "not much meat", "scarcely any meat",
                                "meat free", "meat-free"),
                               ("cook", "make", "dinner", "lunch", "menu", "idea", "ideas",
                                "coming", "guest", "guests", "round", "for")),
          ("Pick a dish that is good on its own rather than meat with the meat left out: a chickpea "
           "and spinach curry with rice, a mushroom and lentil lasagne, or a tray of roasted veg "
           "with feta and couscous. One proper veggie main plus the usual sides is plenty, and it "
           "is worth asking what they actually eat, because vegetarian covers a wide range."),
          # a line that names meat is somebody asking what to do with the meat, whatever else it
          # says: "no meat please, what can i cook with chicken" is a chicken question.
          avoid=("chicken", "beef", "pork", "lamb", "turkey", "mince", "bacon", "sausage",
                 "sausages", "ham", "fish", "prawns", "salmon", "steak", "chorizo",
                 # a cheap week is a money question, and the cheap plan answers it with a week
                 # of veggie dinners instead of one veggie main
                 "cheap", "cheaper", "skint", "broke", "budget", "money", "afford", "fiver"),
          # a dietary constraint is more specific than a general "what should i cook", so this
          # outranks meal-ideas on those lines; not so far that it takes a crowd question, where
          # main's answer about cooking for a table is the one that helps
          bias=1),
    # A guest with diabetes was the one dietary constraint with no answer: meals.py stands
    # aside for a condition ("coeliac, diabetes and a nut allergy have their own answers") and
    # nothing held this one, so "what can i cook for a diabetic" got a ten-minute pasta dish and
    # "what can i cook for someone with diabetes" got the search hedge.
    entry("diabetic-guest", (("diabetic", "diabetics", "diabetes", "type 1", "type 2",
                              "blood sugar", "sugar diabetes"),
                             # A cooking word has to carry the line: "i have type 2 diabetes,
                             # what can i eat" and "can a diabetic eat bananas" are the plate
                             # rule in health.py ("nothing is banned: it is the size of the
                             # starchy and sugary part that counts"), and this card answering
                             # them with a dinner to cook is a reply to a different question.
                             ("cook", "cooking", "make", "making", "dinner", "lunch", "meal",
                              "menu", "idea", "ideas", "coming", "guest", "guests", "visiting",
                              "round", "over", "feed", "serve")),
          # One text for the line that names the condition and for the follow-up that does not:
          # _meal_ideas reads the same words out of the recent turns.
          DIABETIC_PLATE,
          # The condition itself is the health table's question, and so is anything measured:
          # "what is type 2 diabetes", "is diabetes reversible", "how many carbs a day", "can a
          # diabetic drink beer" and "my blood sugar is high" are not dinners to pick.
          avoid=("what is", "reversible", "reverse", "cure", "cured",
                 "symptom", "symptoms", "diagnosed", "diagnosis", "test", "tests", "hba1c",
                 "insulin", "tablets", "metformin", "level", "levels", "high", "low",
                 "hypo", "hyper", "shaky", "dizzy", "thirsty", "weeing", "losing weight",
                 "how many carbs", "carbs a day", "calories", "how much sugar", "sugar free",
                 "sugar-free", "diet drink", "beer", "alcohol", "wine", "drink", "drinks",
                 "cake", "cakes", "biscuit", "biscuits", "bake", "baking", "pudding", "dessert",
                 "sweet", "sweets", "chocolate"),
          bias=1),
    entry("one-main-everyone", (("two dinners", "two meals", "one main", "same dinner",
                                "mixed group", "half vegetarian", "mixed table",
                                "vegetarians and meat eaters", "meat eaters",
                                "everyone can eat", "everyone will eat", "everyone eats",
                                "everyone at the table"),
                               ("make", "cook", "main", "dinner", "one", "everyone", "dish",
                                "feed")),
          ("Make the vegetarian dish the main for the whole table and put the meat on the side as "
           "an extra: a mushroom and lentil lasagne, a chickpea and spinach curry with rice, or a "
           "tray of roasted veg with feta and couscous. Nobody gets a plate of sides, and you cook "
           "one dinner."),
          avoid=("chicken", "beef", "pork", "lamb", "turkey", "mince", "bacon", "sausage",
                 "sausages", "ham", "fish", "prawns", "salmon", "steak", "chorizo"),
          bias=2),
    # no "afters": its loose form is "after", and "out of breath after two minutes" is not a
    # pudding question. Only words that cannot be anything else belong in a key.
    # A fussy eater is not a vegetarian: plain food with the sauce on the side, not a veggie main.
    # "wont eat vegetables" and "refuses to eat" are the same child as "fussy eater": the words
    # that carry the question are about refusing food, not about the label a parent puts on it
    entry("pudding-ideas", (("pudding", "puddings", "dessert", "desserts"),
                            ("make", "idea", "ideas", "quick", "easy", "nice", "sunday",
                             "dinner", "guest", "guests", "like", "want", "any",
                             # the pudding asked for in the middle of a meal being planned:
                             # "what about pudding" after the main course is chosen. The line
                             # names the sweet and nothing else, so the earlier turn is not
                             # there to supply "idea" once the chat has moved on a turn.
                             "what about", "how about", "and for", "for after",
                             # "gotta bring a dessert, family do, 12 of us" is the same question
                             # as "give me a pudding idea": the person says where it is going
                             # rather than what they want, so the words about the occasion carry
                             # it. The first group still gates it, so a "family dinner" line
                             # without a pudding word in it never lands here.
                             "bring", "bringing", "people", "crowd", "party", "family",
                             "ahead", "of us", "weekend", "feed",
                             # "a dessert for six" names the table and nothing else
                             "four", "five", "six", "seven", "eight", "nine", "ten",
                             "eleven", "twelve")),
          _pudding_ideas,
          # a parent describing a child who will not eat dinner is not asking for a recipe, and
          # a pudding offered as a reward is the thing the child advice says not to do
          avoid=("refuses", "refuse", "refusing", "wont eat", "won't eat", "will not eat",
                 "fussy", "picky", "faddy", "reward", "bribe", "veg", "vegetables", "dinner time",
                 # the lean-back phrase is a pudding question only when the line names nothing
                 # else to eat or drink: "what about a cheese board instead of pudding" wants the
                 # cheese board, "and for pudding a glass of port" is about the drink, and a
                 # crumble with sugar and custard is the wrong answer for a diabetic.
                 "cheese", "cheeseboard", "wine", "port", "beer", "cider", "lager", "gin",
                 "brandy", "whisky", "sherry", "diabetic", "diabetes", "sugar free",
                 "no sugar", "gluten free", "pub", "restaurant", "cafe", "menu",
                 # "pudding" is two dishes: the sweet after dinner and the suet pudding that is
                 # dinner. A line that says which one it means is not a dessert question, and a
                 # crumble with custard is the wrong answer to the other.
                 "savoury pudding", "savory pudding", "steak and kidney", "suet",
                 "black pudding", "white pudding", "pease pudding", "yorkshire pudding")),
    # The other pudding: a suet crust steamed for hours with steak and kidney in it is dinner,
    # and the question people ask is what to put with it. Before this the line reached the
    # dessert entry ("savoury pudding" carries "pudding" + "sunday") and answered with a crumble.
    entry("savoury-pudding", (("savoury pudding", "savory pudding", "steak and kidney pudding",
                               "suet pudding", "suet crust"),
                              ("what goes with", "serve with", "serve", "side", "recipe", "make",
                               "making", "cook", "cooking", "how", "sunday", "dinner",
                               "gravy", "mash")),
          ("A steak and kidney pudding is dinner, not afters: line a buttered basin with suet "
           "crust (200g self-raising flour, 100g suet, a pinch of salt, water to a soft dough), "
           "fill it with beef skirt and kidney tossed in flour, season it hard and add a little "
           "stock, then lid it and steam it for three to four hours. Serve it with mashed potato, "
           "buttered greens or peas and extra gravy, and turn it out onto a plate with a cloth "
           "round the basin. It is better made a day ahead and steamed again, which is how it "
           "suits a Sunday."),
          # the sweet puddings stay with their own entry, and a pie is not a pudding: a steak
          # and kidney *pie* is shortcrust and an oven, and it had its own answer (chips and a
          # sharp green salad) until the bare "steak and kidney" in this key took it.
          avoid=("crumble", "rice pudding", "bread and butter", "eton mess", "dessert",
                 "sweet", "sugar", "custard",
                 "pie", "pies", "pastry", "shortcrust", "puff pastry", "filo", "oven"),
          bias=1),
    # A broken set of scales is a cooking question the bot had no answer to: "my kitchen scales
    # broke and every recipe i have is in grams" got "Sorry to hear that". A mug is how people
    # who own no scales cook, so the reply gives the mug's weights and the spoon's.
    # "how do i" and "how can i" used to be in the second group, and the ask shape is not evidence
    # of the topic: "how do i get the white scale out of my kettle" matched "scale" and "how do i"
    # and got the mug-and-flour answer instead of descale-kettle (#answers nine-row list).
    entry("no-scales", (("scales", "scale", "weigh", "weighing", "weigh out", "weighs"),
                        ("broke", "broken", "without", "no scales", "no scale", "grams", "cups",
                         "convert", "instead", "measure")),
          ("Without scales, measure with one mug and keep using it for everything in the recipe: a "
           "250ml mug holds about 150g of plain flour, 200g of caster sugar, 225g of butter or "
           "250g of milk, and a level tablespoon is 15g of flour, 12g of sugar or 15g of oil. A "
           "mug of rice to one and a half mugs of water is the same ratio by volume, so the "
           "recipe still works; if you bake often, a digital scale costs less than a bag of "
           "flour and settles it."),
          # "weight" alone cannot go in: the typo reader takes the key word "weigh" for a
          # misspelt "weight" and turns the entry down for its own question.
          avoid=("bathroom", "my weight", "lose weight", "losing weight", "diet", "kg", "stone",
                 "pounds", "weigh myself", "scale says", "baby", "newborn", "baggage",
                 "airport", "how many grams in", "how many cups in", "how much does",
                 "how many cups")),
    # A tart filling is asked about as the filling ("what filling for a lemon tart") or as the
    # whole bake, and neither had an answer: both got the shrug. The lemon one is the one people
    # ask for, so the reply leads with it and the pastry case is the second thing they need.
    entry("tart-filling", (("tart", "tarts", "tartlet", "tartlets", "flan", "flan case"),
                           ("filling", "fill", "make", "recipe", "bake", "baking", "what goes in",
                            "what should i put", "put in", "lemon", "pastry case",
                            "how do i")),
          ("A lemon tart filling is four eggs, 200g of caster sugar, the juice and zest of four "
           "lemons and 200ml of double cream, whisked together and poured into a part-baked "
           "pastry case, then baked at 150C for 30 to 35 minutes until it is set with a wobble "
           "in the middle, because it firms up as it cools and needs no cornflour. Bake it in a "
           "loose-bottomed tin you have lined with shop-bought shortcrust if you are short of "
           "time, and let it cool completely before you take it out of the tin or the sides "
           "will crack."),
          avoid=("soggy", "soggy bottom", "blind bake", "blind baking", "baking beans", "case",
                 "pastry", "shrink", "shrinkage", "crack", "cracked", "ramekin", "small pan",
                 "saucepan", "tin", "tins", "quiche", "shop", "buy", "calories", "sugar free",
                 "gluten free", "vegan",
                 # a lemon tart is the one filling this entry has a recipe for: a chocolate or
                 # fruit tart is a different pudding and stays the shrug it was
                 "chocolate", "fruit tart", "fruit flan", "fruit tarts")),
    entry("rice-rinse", ("rice", ("wash", "washing", "rinse", "rinsing")),
          # "washing" is the laundry as often as it is the grain: after "how do i cook rice",
          # "how do i know if the washing is done" was answered with this card. The washing means
          # the rice only when the line says rice, or says nothing but the verb.
          "For a risotto or a rice pudding, don't rinse it: that surface starch is what makes it "
          "creamy. For separate, fluffy grains, rinse in a sieve until the water runs clear, which "
          "washes the starch off. It was never about hygiene.",
          avoid=("cooker", "pot", "pan", "machine", "appliance",
                 # "washing" is the laundry as often as it is the grain: after "how do i cook
                 # rice", "how do i know if the washing is done" was answered with this card
                 "the washing", "washing machine", "washing up", "laundry", "clothes", "dishes",
                 "is done", "done yet", "line", "basket", "darks", "lights"),
          bias=1),
    # The question people actually ask about the bag in the cupboard is whether it is still
    # good, and that is the same question as how long it keeps: "rice has been open for a year
    # is it safe", "does rice go off", "is rice ok after the date". The row used to stand down
    # on exactly those words - "cupboard", "gone off", "safe to eat", "ok to eat" - so a dry
    # bag was answered with the cooked-rice 24 hours rule, with the opened-jar rule ("how long
    # does dry rice keep in a jar"), or with a shrug ("does rice go off"). The words that make
    # it the cooked bowl are still in the avoid list below.
    entry("rice-dry-store", ("rice", ("store", "storing", "stored", "keep", "keeping", "kept",
                                      "uncooked", "jar", "airtight", "last", "lasts",
                                      # the freshness ask, in the words people use for the bag:
                                      # "does rice go off", "rice has been open for a year is it
                                      # safe", "is dry rice ok after the date"
                                      "go off", "goes off", "gone off", "open", "opened",
                                      "unopened", "packet", "bag", "out of date", "past the date",
                                      "after the date", "expired", "still ok", "still good",
                                      "safe to eat", "year", "years", "months")),
          ("Dry rice keeps for years in an airtight jar in a cool, dark cupboard - the date on the "
           "bag is a best-before, not a use-by: brown rice is the one that turns, in about six "
           "months, and it tells you by smelling of old oil. Weevils or damp and it goes out. "
           "Only cooked rice needs the fridge, and that one is worth being strict about: 24 hours "
           "and no longer."),
          # a bowl of rice kept warm, or reheated, is a different question from the dry grain
          avoid=("cooked", "leftover", "left over", "reheat", "next day", "yesterday", "fridge",
                 "curry", "wash", "washing", "rinse", "rinsing", "freeze", "freezing",
                 "how long to cook", "water", "pudding", "puddings", "milk", "sugar",
                 # a bowl of cooked rice is the one to be strict about, and "is it safe to eat
                 # cold rice" wants that card rather than the bag's
                 "cold", "warm", "hot",
                 # "is rice ok for cats" is a food-for-a-pet question, not a keeping one
                 "cat", "cats", "dog", "dogs", "pet", "pets", "bird", "birds",
                 ) + KEEP_QUALITY_WORDS,
          bias=1),
    # The same question about the other shelf-stable things in the cupboard. On main "does sugar
    # go off" and "how long do tins last" were shrugs, and the tin was worse than that: "how long
    # does a tin of beans keep" was answered with the veg drawer. Two rows rather than one,
    # because the food with a keeping answer of its own keeps it - salt has one and honey has one,
    # and a combined row took both of those lines off them.
    #
    # Neither "can" nor "canned" is a key word: the word forms match each other, so "can my
    # landlord keep my deposit" and "can i keep it" were both answered with a tin of tomatoes.
    # Nor a bare "off": "im off sugar" means giving it up.
    entry("tins-keep", (("tins", "tin of", "tins of", "tinned", "cans of", "tin", "canned food",
                         "canned goods"),
                        ("keep", "keeps", "last", "lasts", "how long", "go off", "goes off",
                         "gone off", "stored", "storage", "still ok", "still good",
                         "out of date", "past the date", "after the date", "expired", "use by",
                         "best before", "date")),
          _tins_keep,
          # whether a tin is good is a keeping question; how long its contents cook for is not,
          # and "how long should i simmer tinned tomatoes" is the sauce row's line
          avoid=("simmer", "simmering", "cook", "cooking", "boil", "boiling", "fry", "frying",
                 "roast", "heat", "minutes", "recipe", "sauce", "soup", "stew", "casserole",
                 "make", "made", "dinner", "supper",
                 # a tin of paint and a tin of polish are not food
                 "paint", "polish", "wax", "oil", "petrol", "biscuit", "biscuits", "cake", "cakes",
                 # an opened tin is the 2-days-in-a-bowl card, and it answers that better
                 "open", "opened", "once open", "half", "leftover", "left over"),
          # "how long does a tin of beans keep" was the veg drawer: a tin is this row's subject
          bias=2),
    entry("sugar-keeps", (("sugar",), ("go off", "goes off", "gone off", "keep", "keeps",
                                       "how long", "still ok", "still good", "years old",
                                       "shelf life", "crystallised", "crystallized", "hard")),
          ("Sugar does not go off: white sugar keeps for years, and the date on the bag is a "
           "best-before for quality rather than a use-by. Brown sugar sets hard rather than "
           "spoiling - a slice of bread or apple in the jar softens it again - and sugar with "
           "insects or damp in it goes out."),
          # a blood sugar reading, and the things sugar is cut down for, are other questions
          avoid=("low", "high", "levels", "blood", "hypo", "diabetes", "diabetic", "im off",
                 "cutting out", "cut out", "gave up", "give up", "diet", "weight", "calories",
                 "cough", "recipe", "cake", "bake", "baking", "jam", "marmalade", "syrup",
                 "substitute", "instead of", "replace")),

    entry("chickpeas", (("chickpeas", "chickpea", "chick peas", "garbanzo beans"),
                        ("make", "do", "cook", "use", "tin", "tinned", "can", "ideas", "with")),
          "Fry a drained tin in olive oil with cumin and paprika for 8 minutes and they go crunchy "
          "enough to eat as a snack or over a salad; mash them with tahini, lemon and garlic for "
          "hummus, or simmer them in tomatoes and coconut milk for a curry in 20 minutes."),
    entry("buttermilk-make", ("buttermilk", ("make", "making", "homemade", "from milk", "yourself")),
          "Stir a tablespoon of lemon juice or white vinegar into 250ml of milk and leave it 10 "
          "minutes to thicken: that is buttermilk for a recipe. Thinned plain yoghurt or soured "
          "cream work too, and milk alone is fine in most pancake and muffin recipes.",
          avoid=("pancake", "pancakes", "muffin", "muffins", "scone", "scones", "cake",
                 "dressing", "substitute", "instead", "replace", "alternative")),
    # One row per food, so every way of asking "how many calories in X" is one lookup. The food
    # has to be in the table: a line about a takeaway, a recipe or a diet passes.
    # One answer per kind of bake, keyed on the gluten-free ask plus the dish, so every way of
    # asking for a cake without wheat is one lookup and the sauces and the porridge keep theirs.
    entry("gluten-free-baking",
          (GLUTEN_FREE_ASKS, GLUTEN_FREE_DISHES),
          _gluten_free,
          # a nudge over the vegan bake entry: a vegan answer cannot see the gluten, and a
          # gluten-free one can see the dairy, so the line that names both gets this one
          bias=1,
          ask=GLUTEN_FREE_ASKS,
          avoid=_GLUTEN_FREE_SKIP),
    # "is rice gluten free" is a fact about the food, not a request to cook it: the recipe rows
    # for rice, oats and porridge were answering it with a method, and every plain food with no
    # row of its own got a search hedge. The table this file already keeps says which foods are
    # made with wheat, so every one of them answers the yes or no here.
    entry("gluten-free-fact",
          (GLUTEN_FACT_FOODS, GLUTEN_FACT_ASKS),
          _free_of_gluten_fact,
          # over the blend row: "is baking powder gluten free" is a food with "baking" in its
          # name, and it was the bake answer
          bias=3,
          ask=GLUTEN_FACT_ASKS,
          guard=asks_a_gluten_fact),
    entry("calories-in-food",
          # The food and the ask are the two key parts. The function words that used to sit in the
          # second tuple ("in", "of", "has", "does", "there", "much", "many") are in every other
          # line in the language, so a sentence with no food and no calorie word in it still
          # scored: "still hasnt called me back" was answered with nothing at all (this reply
          # declines), and the line never reached a row that could answer it.
          (CALORIE_ASKS, tuple(FOOD_CALORIE_MEALS) + tuple(FOOD_CALORIES)),
          _calories,
          # The food itself is the gate, and it is read from the table: a food the table does
          # not have, or a line about burning them, passes to whatever answers next.
          avoid=("a day", "per day", "burn", "burned", "burnt", "exercise", "diet",
                 "lose weight")),
    # The same table answers what is in the portion: protein, carbohydrate, sugar, fat and
    # fibre. The nutrient is the gate, and the food has to be in the table, so a diet question
    # ("how much protein do i need a day") and a dish ("protein in a chicken curry") pass.
    entry("nutrients-in-food",
          # The ask and the nutrient together ("how much protein", "how many carbs") is the
          # phrase people write, and a portion can carry another domain's key words - a glass of
          # milk is also "glasses", which is the water-intake question. The phrase outranks the
          # bare word so the nutrient answer is the one that gets read.
          (tuple(word for word, _column in _NUTRIENT_WORDS)
           + tuple("how much %s" % word for word, _column in _NUTRIENT_WORDS)
           + tuple("how many %s" % word for word, _column in _NUTRIENT_WORDS),
           tuple(FOOD_NUTRIENTS)),
          _nutrients,
          avoid=("a day", "per day", "daily", "a week", "lose weight", "build muscle", "diet",
                 "shakes", "shake", "powder", "supplement", "deficiency", "instead",
                 "substitute", "substitute for", "how do i", "recipe", "cook", "make",
                 # "how much protein in a chicken breast" is this file's own answer, with the
                 # calories and the size of a breast in it: the table has a plain chicken and
                 # must not replace it with the shorter figure.
                 "breast", "breasts",
                 # "how much iron in a shirt" is the ironing: the mineral word is in the key,
                 # so the other sense of it is kept out here.
                 "shirt", "shirts", "crease", "creases", "board",
                 # The bare "steam" was one edit from "steak", and a line word one edit from an
                 # avoid word zeroes the whole row, so "how much protein in a steak" found no
                 # entry at all. The steaming itself is what the guard is for.
                 "steaming", "steamed", "steam it", "steam them")),
    entry("calories-a-day", (("calorie", "calories", "kcal"),
                             ("a day", "per day", "daily", "should i eat", "need")),
          "An adult needs roughly 2,000 to 2,500 calories a day, and the exact number depends on "
          "your size and how much you move: about 2,000 suits most women and 2,500 most men, with "
          "1,500 to 1,800 for steady weight loss. Food labels count in kilocalories, so the "
          "\"calories\" on a packet are these numbers.",
          ask=("a day", "per day", "daily", "should i eat", "need", "how many"),
          avoid=("banana", "chicken", "bread", "carbs", "protein", "sugar")),
    entry("chicken-protein", (("chicken breast", "chicken breasts"),
                             ("protein", "calories", "macros", "nutrition")),
          "A cooked chicken breast is about 30g of protein per 100g, so a 175g breast carries "
          "roughly 50g, near a quarter of a day's protein for an adult, at about 280 calories."),

    # --- the second shelf: the small jobs people hit in their first year of cooking -------
    # Each one is a job, not a dish: frying an egg, peeling garlic, keeping ginger, a cheese
    # sauce, a burger that holds together. They are keyed on the job words and pass on anything
    # else, so "how do i fry chicken" and "how do i keep garlic" do not reach them.
    entry("egg-fry", (("fry", "frying", "fried"),
                      ("egg", "eggs")),
          "Heat a little oil or butter in a frying pan over a medium heat until it shimmers, break "
          "the egg into a cup and slide it in, and give it 2 to 3 minutes for a runny yolk. Spoon "
          "the hot fat over the white to set the top, and salt it at the end so the yolk doesn't go "
          "spotted.",
          avoid=("rice", "bread", "toast", "chicken", "fish", "onion", "onions", "potato",
                 "potatoes", "chips", "pancake", "pancakes", "bacon", "sausage", "sausages",
                 "tomato", "mushroom", "mushrooms", "noodles", "leftover", "microwave")),
    # "skins" rather than "skin": chicken-skin keys "skin", and making that word common would
    # cost it the rarity it needs to beat the roast-chicken timing answer on a crispy-skin line.
    entry("garlic-peel", (("garlic",), ("peel", "peeling", "peeled", "skins", "quick", "quickly",
                                        "easy", "faster", "fast", "hassle")),
          "Press the clove on the board with the flat of a knife until it cracks and the skin comes "
          "away in one piece; a handful of cloves shaken hard in a lidded jar works too. For a whole "
          "bulb, drop the cloves in boiling water for 30 seconds and the skins slip off.",
          # "how to get rid of garlic breath fast" is not the peeling job: it reached this row on
          # garlic and "fast" and was told to press the clove with a knife.
          avoid=("hands", "smell", "smelly", "stink", "burn", "burnt", "bitter", "bread", "butter",
                 "breath", "bad breath", "garlic breath", "mouth", "breathing",
                 "sauce", "roast", "plant", "grow", "growing", "keep", "store", "freeze", "go off",
                 "sprout", "green", "how much", "how many", "substitute", "instead", "powder",
                 "paste", "how long")),
    # Crushing garlic is the job before the pan, and it is not peeling: "how do i crush garlic
    # without a press" wanted neither the peel trick nor the burning answer, and had nothing.
    entry("garlic-crush",
          (("garlic", "garlic clove", "garlic cloves", "a clove of garlic"),
           ("crush", "crushed", "crushing", "mince", "minced", "chop", "chopped", "press",
            "without a press", "no press", "puree", "paste", "smash", "grate", "grated")),
          "Put the clove on the board, lay the flat of a wide knife on it and press down hard "
          "with the heel of your hand until it splits; pull the skin off, chop it, then drag the "
          "knife across the pile a few times with a pinch of salt and it turns to paste. The "
          "bottom of a glass or the back of a spoon crushes it just as well, and the fine side "
          "of a grater gives you a purée for a sauce.",
          avoid=("peel", "peeling", "peeled", "skins", "burn", "burnt", "bitter", "bread",
                 "butter", "roast", "plant", "grow", "growing", "keep", "store", "freeze", "go off",
                 "sprout", "sprouts", "green", "how much", "how many", "substitute", "instead",
                 "powder", "smell", "smelly", "hands", "how long", "cloves in a bulb",
                 "breath", "bad breath", "garlic breath", "mouth", "breathing")),
    entry("ginger-keep", (("ginger",),
                          ("keep", "store", "storing", "last", "freeze", "freezer", "fresh",
                           "fridge", "grate", "long")),
          "Keep fresh ginger, unpeeled, in the fridge drawer for about 3 weeks, or freeze it whole "
          "and grate it straight from frozen: it grates finer that way and keeps 3 months. A "
          "teaspoon of the frozen gratings is about the same as a thumb of fresh.",
          ask=KEEP_ASK),
    entry("marinade", (("marinade", "marinade", "marinate", "marinating", "marinated"),
                       ("make", "how long", "recipe", "good", "best", "overnight", "quick",
                        "goes", "go", "put", "use", "ingredients", "chicken", "steak", "meat",
                        "fish", "tofu", "lamb", "pork")),
          "Whisk 3 parts oil to 1 part acid - lemon, wine or vinegar - with salt, then add garlic, "
          "honey, soy, herbs or yoghurt. Give chicken or fish 30 minutes to 2 hours and tougher meat "
          "4 hours or overnight, always in the fridge; a lot of acid or sugar left on for a day "
          "turns meat mushy.",
          avoid=("bottle", "jar", "shop", "buy", "price")),
    # No cheese-sauce, stuffing or hummus entry here: main has all three now, with quantities
    # and a total time (the recipes table), and a plainer method beside them reads as a step back.
    # "make", "recipe" and "taste" are on almost every recipe line, so they are not here: they
    # were enough to take "how do i make a stir fry" off the heat-and-crowding answer.
    entry("stirfry-sauce", (("stir fry", "stirfry", "stir-fry", "wok"),
                            ("sauce", "flavour", "flavor", "tasty", "taste")),
          "Stir 2 tablespoons of soy, 1 of oyster sauce, a teaspoon of sugar and a teaspoon of "
          "cornflour into 100ml of water or stock and pour it in when the vegetables are nearly "
          "done: it thickens in about a minute. Garlic and ginger go in first, in the oil, before "
          "anything wet.",
          avoid=("rice", "noodles", "calories", "how long", "pan", "buy")),
    # "how do i make soup taste better", not "my soup tastes bland": the fault entries own the
    # complaints, so this one needs a make/better word as well as the soup.
    entry("soup-flavour", (("soup",),
                           ("make", "better", "improve", "more flavour", "flavour", "boring",
                            "lifeless", "interesting")),
          _soup,
          # "how do i make soup thicker" is a thinning question with `make` in it, and this entry
          # outranks soup-thick on that word alone: the thickening words hand it back.
          avoid=("bland", "tasteless", "no taste", "tin", "can", "carton", "shop", "buy",
                 "calories", "recipe", "thicker", "thicken", "thickening", "thick", "thin",
                 "watery", "runny"),
          # "how do i make soup" is the recipe table's line now, and its answer carries a total
          # time and quantities this one has not: the entry only speaks when the line asks about
          # how the soup tastes, so a plain make-a-soup question keeps the fuller answer.
          ask=("taste", "tastes", "tastier", "better", "flavour", "flavourless", "boring",
               "lifeless", "improve", "interesting", "dull", "flat"),
          bias=2),
    entry("beetroot-cook", (("beetroot", "beetroots", "beet"),
                            ("cook", "roast", "boil", "bake", "peel", "prepare", "long")),
          "Wrap whole beetroot in foil with a splash of oil and roast at 200C (180C fan) for 1 to "
          "1.5 hours, until a knife slides in, or boil it 40 to 60 minutes. Rub the skins off with a "
          "tea towel while they are still warm, and wear gloves unless you want pink hands.",
          avoid=("blood", "urine", "wee", "stain", "juice", "sugar", "watch")),
    entry("turkey-crown", (("turkey",), ("crown", "long", "cook", "roast", "time", "temperature",
                                        "juicy", "dry", "weight", "whole", "bird")),
          _turkey,
          avoid=("leftover", "leftovers", "sandwich", "stock", "carcass", "defrost", "freeze",
                 "calories", "price", "buy",
                 # A bird's weight does not keep its cuts: a breast, a leg or a spatchcock cooks in
                 # far less time than a whole turkey, and the whole-bird timetable is a confident
                 # wrong number for all of them.
                 "breast", "breasts", "leg", "legs", "thigh", "thighs", "fillet", "fillets",
                 "drumstick", "drumsticks", "wing", "wings", "spatchcock", "mince", "steak",
                 "escalope", "escalopes", "butterflied")),
    entry("turkey-cut", (("turkey", "turkeys"),
                         ("breast", "breasts", "leg", "legs", "thigh", "thighs", "fillet",
                          "fillets", "drumstick", "drumsticks", "wing", "wings", "spatchcock",
                          "escalope", "escalopes", "steak", "steaks")),
          _turkey_cut, bias=2,
          # the whole bird, the crown, thawing, buying and the leftovers are other answers
          avoid=("whole", "whole bird", "crown", "stuffed", "stuffing", "defrost", "thaw",
                 "frozen", "freeze", "leftover", "leftovers", "sandwich", "stock", "carcass",
                 "mince", "burger", "burgers", "price", "calories", "safe", "poison")),
    # "how do i make stuffing" and "stuffing recipe" are the recipes table's now (a total time and
    # the quantities). What main still shrugs at is stuffing the bird itself, which is a safety
    # answer rather than a recipe one, so this entry is held to the inside-the-bird lines.
    entry("stuffing-inside", (("stuffing", "stuff", "stuffed"),
                              ("inside", "in the bird", "in the turkey", "between the legs",
                               "a turkey", "the turkey", "a bird", "the bird", "for turkey",
                               "safe", "salmonella", "raw", "juices")),
          "Better not: cook it in a separate buttered tray, 25 minutes at 180C, because "
          "stuffing in a turkey soaks up the raw juices and holds the middle of the meat "
          "below a safe heat, so the bird needs about 20 minutes more and the stuffing comes out "
          "soggy. If you do stuff it, give the stuffing itself a thermometer read of 74C before the "
          "bird comes out to rest.",
          avoid=("nose", "sick", "ill", "blocked", "stuffed up", "full", "eat too much",
                 "mushroom", "pepper", "peppers", "cushion", "toy", "teddy", "envelope")),
    entry("turkey-order", (("turkey", "turkeys"),
                           ("order", "ordering", "ordered", "buy", "buying", "bought", "collect",
                            "collecting", "shop", "shopping", "when", "days", "early", "ahead",
                            "size", "big")),
          "Order it from a butcher or a supermarket a week or two ahead, and collect a fresh bird "
          "two or three days before: it keeps fine in the coldest part of the fridge for that "
          "long. If it is going in the freezer, buy it now, because a frozen turkey needs 24 hours "
          "in the fridge for every 2kg, so a 6kg bird is three days of thawing on its own.",
          # how long to cook it, what to do with the leftovers, and the thaw are other answers
          avoid=("cook", "cooking", "roast", "roasting", "time", "temperature", "long", "done",
                 "defrost", "defrosting", "thaw", "thawing", "leftover", "leftovers", "sandwich",
                 "stock", "carcass", "breast", "leg", "thigh", "mince", "calories", "poison",
                 "visa", "holiday", "currency")),
    entry("cauliflower-rice", (("cauliflower", "cauliflowers"),
                               ("rice", "couscous", "carb", "carbs", "keto", "blitz", "grate",
                                "grated", "pulse", "instead", "substitute", "low carb")),
          _cauliflower_rice,
          avoid=("roast", "roasting", "whole", "cheese", "soup", "plant", "grow", "harvest",
                 "pick", "keep", "fridge", "freezer", "frozen", "freeze", "smell", "yellow",
                 "black", "spots", "worms", "caterpillar")),
    entry("burger-bind", (("burger", "burgers", "patty", "patties"),
                          ("fall apart", "falling apart", "break up", "breaking up",
                           "breaks up", "crumbly", "hold", "holds", "binding", "bind",
                           "make", "juicy", "dry", "recipe", "best", "together")),
          "Use mince that is at least 20% fat, shape it loosely without packing it down, and salt "
          "only the outside just before it goes in the pan: that is all the binding beef needs. If "
          "it keeps breaking up or the meat is lean, mix in an egg and a handful of breadcrumbs and "
          "chill the patties 20 minutes.",
          avoid=("veggie", "vegetarian", "vegan", "bean", "chicken burger", "halloumi",
                 "bun", "buns", "bap", "baps", "bread", "buy", "price", "restaurant", "london",
                 "near me", "nearby", "takeaway", "take away", "delivery", "place", "places",
                 "shop", "calories", "fast food")),
    entry("pesto", (("pesto",),
                    ("make", "recipe", "best", "how", "basil", "pine nuts", "pinenuts")),
          "Blitz 50g of basil, 30g of pine nuts, 50g of parmesan, a small garlic clove and a pinch "
          "of salt, then pour in about 100ml of olive oil with the motor still running. Rocket or "
          "spinach and walnuts stand in for basil and pine nuts, and it keeps a week in a jar under "
          "a layer of oil.",
          # a jar with a spoonful left is a use-it-up question, and the pantry's pesto row answers
          # it with what to do with the rest rather than how to make a fresh batch
          avoid=("jar", "shop", "price", "buy", "allergy", "nut allergy",
                 "use up", "using up", "use it up", "leftover", "left over")),
    entry("flat-bake", (("flat", "didnt rise", "didn't rise", "did not rise", "not risen",
                         "no rise", "came out flat"),
                        _NO_CAKE_RISE + ("pancake", "pancakes", "yorkshire", "batter",
                                         "bake", "baked", "baking",
                                         "cupcake", "cupcakes", "muffin", "muffins",
                                         "bun", "buns")),
          _flat,
          # pancakes-flat and yorkshire-pudding answer their own flat lines now, so this one keeps
          # the bakes main still shrugs at: scones, muffins and a batter that will not rise
          avoid=("spread", "spreads", "spreading", "spread out", "wide", "thinner", "melted",
                 "pooled", "pool",
                 "bread", "dough", "loaf", "taste", "tastes", "tasted", "bland", "dull",
                 "season", "fizzy", "beer", "tyre", "tire", "battery", "landlord", "rent",
                 "flatmate", "apartment", "screen", "phone", "bike", "car", "pancake", "pancakes",
                 "crepe", "crepes", "yorkshire", "yorkshires", "toad in the hole",
                 # a flat that is hot, cold or freezing is the flat you live in, not a bake
                 "hot", "cold", "freezing", "freezing cold", "heating", "heater",
                 "radiator", "radiators", "boiler", "warm", "leak", "leaking", "damp", "mould")
                 + _BAKE_KEEPING,
          # `fix-bland` reads a bare "flat" as a taste, and it ties this entry on "my scones came
          # out flat" because both match two key words: a bake that is flat is short of rise, so
          # this one wins the tie. A line with a taste word in it is still fix-bland's, above.
          # "my flat" used to be in the avoid list, and an avoid phrase is read loosely: the two
          # words only had to be in the line, so "my scones came out flat" was thrown away with
          # it. The determiner next to the word is what makes it a home, which is a guard.
          guard=_not_the_flat_you_live_in_bake,
          bias=3),
    entry("aubergine", (("aubergine", "aubergines", "eggplant", "eggplants"),
                        ("rubbery", "bitter", "soggy", "cook", "salty", "oil", "fry")),
          ("Slice it, salt it for 20 minutes and pat it dry, then cook it in plenty of hot oil until "
           "it's deep golden: aubergine soaks up oil like a sponge, so a dry pan and too little fat "
           "is what leaves it rubbery. Roasting at 200C for 25 minutes works the same way."),
          bias=2,
          avoid=("plant", "growing", "grow", "soil", "allotment")),
    entry("peas-frozen", (("peas", "frozen peas", "pea", "petit pois", "petits pois",
                           "garden peas"),
                          ("frozen", "cook", "boil", "steam", "microwave", "how long",
                           "grey", "mushy")),
          ("Drop frozen peas into already boiling water and give them 2 to 3 minutes: they're "
           "blanched before freezing, so they need no more than that. They're done when they float "
           "and taste sweet; longer turns them grey."),
          # keeping a bag of peas and cooking a pan of them are different questions, and "how
          # long" is in both: the keeping verbs stand this row down and the keeping row answers.
          avoid=("keep", "keeps", "keeping", "kept", "refreeze", "re-freeze", "re freeze",
                 "still good", "out of date", "go off", "gone off", "last", "lasts", "stay",
                 "good for"),
          # a house with no peas in it is not a pan of peas: the swap and pantry rows answer
          # "i have no frozen peas", which came back as how long to boil them.
          guard=_not_short_of("peas?", "pea", "petit pois", "petits pois", "garden peas",
                              "frozen peas")),
    entry("peas-keeping", (("peas", "frozen peas", "pea", "petit pois", "petits pois",
                            "garden peas", "sweetcorn", "broad beans"),
                           ("keep", "keeps", "keeping", "kept", "last", "lasts", "stay",
                            "freezer", "refreeze", "re-freeze", "re freeze", "go off",
                            "gone off", "good for", "out of date", "how long")),
          ("Frozen peas keep about a year at -18C in a bag that stays shut: they don't go off, "
           "they dry out and turn starchy, so a bag from two winters ago is safe but not worth "
           "eating raw. Once they have thawed on the counter, cook them and eat them that day "
           "rather than freezing them again; a bag that thawed but stayed cold in the fridge can "
           "go back in the freezer, though the texture will be softer."),
          # a pan of peas is the cooking row's, and `ask` keeps this one from answering "how long
          # do i boil frozen peas"
          avoid=("boil", "boiled", "cook", "cooked", "cooking", "steam", "microwave", "recipe")),
    entry("banana-overripe", (("banana", "bananas"), ("overripe", "over ripe", "too ripe",
                                                       "mushy", "black", "use up", "going off",
                                                       "left over",
                                                       # how a person says "I have more of this than
                                                       # I can eat": "too many bananas", "loads of
                                                       # bananas". Without these it got the
                                                       # ten-minute dinner list.
                                                       "too many", "so many", "lots of",
                                                       "loads of", "spare", "left")),
          ("Mash them into banana bread: 3 black bananas, 175g self-raising flour, 100g soft butter, "
           "100g sugar and 2 eggs, 50 to 55 minutes at 180C. Or peel and freeze them for smoothies; "
           "they go black in the freezer but taste the same."),
          bias=1,
          # how many you can eat is the diet question, and "too many" is in the key above for
          # "too many bananas to use up": "how many bananas a day is too many" was answered with
          # a banana bread recipe, which is an answer to a different worry.
          #
          # A bunch that is going black and a bunch you want to keep from going black are two
          # questions: the keeping row answers how to slow it down, and this one is what to do
          # with the ones that have got there.
          avoid=("keep", "keeps", "keeping", "stop them", "stop it", "going black", "go black",
                 "last longer", "stay fresh", "store", "storing", "storage", "how do i keep",
                 "plant", "growing", "grow", "tree", "soil",
                 "a day", "per day", "healthy", "good for you", "diet", "calories",
                 "how many can i", "is it ok to eat", "is it bad", "fattening")),
    entry("pancakes-flat", (("pancake", "pancakes", "crepes", "crepe"), ("flat", "thin", "thick",
                                                                          "fluffy", "rise", "light")),
          ("Flat pancakes are usually over-mixed or too thin: stir until the flour just disappears, "
           "leaving lumps, and use roughly 1 part flour to 1.2 of milk by volume. Resting the batter "
           "15 minutes helps, and a pinch of baking powder makes the thick American ones rise."),
          bias=2,
          # A fix answers a fault, not a request for the method: "how do i make thick fluffy
          # pancakes" is asking for the American batter, and the fault entry took it because
          # "thick" and "fluffy" are the words it watches for.
          avoid=("day", "shrove", "recipe book", "how do i make", "how to make", "how can i make",
                 "how do you make", "recipe", "batter")),
    # A loaf is not a cake: it comes out of the tin by the paper, not by the knife and the ten
    # minutes, and "how do i get my bread out of the tin" was a shrug until the bread words
    # reached this row.
    entry("cake-stuck-tin", (_BAKED_GOODS + ("bread", "loaf cake"),
                             ("stuck", "sticks", "sticking", "come out", "comes out", "getting out",
                              "get it out", "broke", "breaking", "broken", "tin", "tins", "pan")),
          _out_of_the_tin,
          avoid=("baking", "bake", "temperature", "oven", "how long", "rise", "sunk", "raw",
                 "mouldy", "fridge",
                 # lining a fruit cake's tin is the deep-tin answer's, not the stuck-cake fix's
                 "fruit cake", "christmas cake", "rich fruit", "wedding cake", "simnel",
                 "dark fruit",
                 # and greasing a tin is getting ready to bake, not a cake that has already
                 # stuck: "do i need to grease the tin for brownies" was told how to line one
                 "grease", "greasing", "greased", "how do i grease", "should i grease",
                 "do i need to grease", "prepare the tin", "prepare a tin")),
    # A microwave is a way to cook rice, not only a way to reheat it. The reheating entry keys
    # on "microwave" too (people say "can i microwave this"), so "how do i cook rice in a
    # microwave" was answered "reheat it until it is piping hot all the way through" - advice
    # for last night's dinner, given to somebody with a bag of raw rice. This entry answers the
    # cooking, and the reheat and leftover words in its avoid send those lines back.
    entry("rice-microwave",
          (("rice", "basmati", "long grain rice", "white rice", "jasmine rice"),
           ("microwave", "microwaving", "microwaved", "micro wave")),
          "Use a big bowl, because it boils up: one mug of rice to two mugs of boiling water, a "
          "pinch of salt, a plate over the top, and 10 minutes on full power. Leave it to stand 5 "
          "minutes still covered - that is what finishes it - then fork it through from the "
          "bottom. Rinse the rice first so the grains stay separate.",
          # The plain "can i microwave rice" is asked with a tub of cooked rice in hand, about
          # whether it is safe and how, so the entry only fires when the line names cooking:
          # "how do i cook rice in a microwave", "can i microwave rice instead of boiling it".
          ask=("cook", "cooking", "boil", "boiling", "instead", "how do i", "make", "making",
               "how long", "long does", "takes", "minutes", "water", "time"),
          avoid=("reheat", "reheating", "leftover", "left over", "next day", "yesterday",
                 "already cooked", "pouch", "packet", "ready cooked", "sticky", "pudding",
                 "risotto", "freeze", "freezer", "last night", "last nights", "night before",
                 "yesterdays", "spare", "is it safe", "safe to"),
          bias=2),
    entry("rice-fluffy", (("rice", "basmati", "long grain", "jasmine"),
                          ("fluffy", "separate", "not sticky", "grains", "perfect", "nice",
                           "light", "like the takeaway", "like a restaurant", "how do i get")),
          "Rinse it until the water runs clear, use 1 part rice to 1.5 parts water, bring it to a "
          "boil, then turn it right down, put the lid on and leave it 10 minutes without stirring. "
          "Take it off the heat and let it sit 5 minutes with the lid on, then fork it through from "
          "the bottom - that steam is what makes the grains separate.",
          avoid=("sticky", "sushi", "pudding", "risotto", "paella", "mushy", "stuck", "burnt",
                 "microwave", "leftover", "reheat", "how long", "per person", "freeze",
                 # rice cooked yesterday is the leftovers question, not the rinse-and-simmer one,
                 # and "how long is cooked rice good for" is the keeping rule, not the method
                 *(tuple(_DAY_BEFORE) + ("good for",)))),
    # "how do i make bread sauce" is its own recipe, so a bare "sauce" in the key is too wide:
    # the sauce has to be named or asked for as a method ("how do i thicken a sauce").
    entry("white-sauce", (("white sauce", "bechamel", "béchamel", "roux", "cheese sauce",
                           "parsley sauce", "lumpy sauce", "thicken a sauce",
                           "thickening a sauce", "sauce for"),
                          ("make", "making", "how do i", "how to", "recipe", "lumpy", "thicken",
                           "basic", "easy", "best")),
          "Melt 25g of butter, stir in 25g of plain flour and cook it a minute, then add 300ml of "
          "milk a splash at a time, whisking each splash in before the next - that is what keeps it "
          "smooth. Simmer it 3 or 4 minutes, season with salt and pepper, and stir in a handful of "
          "grated cheese off the heat for a cheese sauce.",
          avoid=("tomato", "pasta sauce", "apple sauce", "soy sauce", "hot sauce", "bbq",
                 "cranberry", "brown sauce", "worcestershire", "gravy", "custard",
                 "bread sauce", "hollandaise", "pesto", "curry sauce", "mint sauce",
                 # "how do i make a sauce for pasta" asks for the quick tomato one, and the
                 # "sauce for" phrase above was answering it with a white sauce. A white
                 # sauce named for a dish ("cheese sauce for pasta") still gets it.
                 "sauce for pasta", "sauce for the pasta", "sauce for spaghetti",
                 # "how do i thicken a sauce without flour" was answered with a roux - a sauce out
                 # of the flour the person had just said they had not got. Those lines are the
                 # thicken-without-flour row's.
                 "without flour", "no flour", "anything but flour", "cornflour", "corn starch",
                 "cornstarch", "arrowroot", "gluten free", "gluten-free", "without wheat",
                 "no wheat", "coeliac", "celiac")),
    # A missing ingredient is not a reason to guess at the recipe that uses it. This is the roux
    # row's sibling for the lines that turn the flour down.
    entry("thicken-without-flour",
          # The verb is the key, not the noun: "is soy sauce gluten free" carries "sauce" and
          # "gluten free" and was handed the cornflour slurry, which is not its question at all.
          (("thicken", "thickening", "thicker", "thickens", "roux", "slurry", "gravy"),
           ("without flour", "no flour", "not use flour", "cornflour", "corn starch",
            "cornstarch", "arrowroot", "gluten free", "gluten-free", "without wheat", "no wheat",
            "instead of flour", "other than flour", "coeliac", "celiac", "coeliacs")),
          "Cornflour is the quickest stand-in: mix one tablespoon with two tablespoons of cold "
          "water, stir it into the simmering sauce and let it bubble for two minutes - it only "
          "thickens at a boil. Arrowroot does the same and gives a clearer gloss. With no starch "
          "at all, simmer with the lid off until it coats a spoon, or off the heat whisk in a knob "
          "of cold butter or a spoonful of cream. A gluten free plain flour blend makes a roux "
          "the same way as ordinary flour.",
          # A stew or a soup that wants to be thicker already has the right answer - simmer it
          # uncovered, or blend a ladleful - so those lines keep their own rows.
          avoid=("stew", "stews", "soup", "soups", "casserole", "casseroles", "hotpot",
                 "porridge", "yoghurt", "yogurt", "smoothie",
                 "stain", "starch the shirt", "wallpaper", "paint", "hair", "custard",
                 "bread sauce", "hollandaise", "jam", "setting point"),
          bias=2),
    entry("omelette-stick", (("omelette", "omelet", "frittata", "scrambled eggs", "eggs"),
                             ("stick", "sticks", "sticking", "stuck", "stuck to the pan",
                              "burn", "burning", "pan")),
          "A hot non-stick pan with butter foaming but not browning, and eggs beaten just enough "
          "to mix: pour them in, then push the set edges into the middle and tip the pan so the "
          "raw egg fills the gap. Take it off the heat while the top is still a little wet - it "
          "finishes cooking in the pan, and that is what stops it sticking and going rubbery.",
          avoid=("boil", "boiled", "poach", "scrambled eggs how", "frying", "rice", "pasta",
                 "cake", "batter", "meat", "fish", "chicken")),
    entry("pork-crackling", (("crackling", "crackle", "pork belly", "pork shoulder",
                              "pork loin", "pork roast", "pork joint"),
                             ("crispy", "crisp", "how do i", "how", "get", "make", "best",
                              "soft", "soggy", "not", "wont", "won't", "failed")),
          "Score the skin, pour a kettle of boiling water over it, dry it and rub in plenty of "
          "salt and a little oil, then roast it at 220C for 30 minutes and 180C after that, "
          "without basting or covering it, and if the skin is still soft once the meat has "
          "rested cut the crackling off and grill it for 5 minutes on a rack.",
          # a joint that is dry or tough is a cooking problem, not a skin problem
          avoid=("dry", "dry out", "tough", "bland", "gravy", "apple sauce", "leftover",
                 "sandwich", "pulled")),
    entry("sprouts", (("sprouts", "sprout", "brussels", "brussel", "brussels sprouts"),
                      ("bitter", "taste", "tasting", "cook", "cooking", "boil", "roast",
                       "not", "less", "how do i", "how long", "best way", "nice")),
          # The fault is the bitterness: "how do i cook sprouts" wants the plain method and the
          # timing, which the recipe table answers, and it was getting this fault answer.

          "Bitter means overcooked or undercooked: halve them and boil 4 to 5 minutes, no more, "
          "or roast them cut side down at 200C for 20 minutes. Cut a cross in the stalk end so "
          "the middle cooks at the same time as the outside, and finish with butter, lemon or a "
          "little bacon - a pinch of sugar in the water does very little.",
          # "how do i keep garlic from sprouting" is a keeping question: the word "sprouting"
          # folds to "sprout" and took the veg-drawer answer with it
          avoid=("christmas shopping", "freeze", "leftover", "soup", "keep warm", "warming",
                 "stay warm", "ahead of time", "warm", "garlic", "onion", "onions", "potato",
                 "potatoes", "seeds", "bean sprouts", "alfalfa", "keep from", "store",
                 "storing"),
          ask=("bitter", "bitterness", "sour", "taste", "tasting", "tastes")),
    entry("coffee-cafe", (("coffee", "espresso" ), ("cafe", "café", "home", "better", "taste",
                                                     "barista", "grind", "make")),
          ("Fresh beans ground just before you brew, and a scale: 60g of coffee per litre for filter, "
           "or 18g in a double espresso. Stale grounds or a brew too weak to taste is what makes "
           "home coffee thin next to a cafe's."),
          # a question about strength is a measure (see coffee-strength), not about beans. A
          # coffee cake is a bake, and fix-sour already answers it on the key words, so the
          # avoid list here stays as it was: "cake" would be one slip from "cafe" and the
          # misspelt-avoid guard would then turn down "how do i make coffee at home like a cafe".
          avoid=("machine", "buy", "best", "gift", "shop", "weak", "weaker", "strong",
                 "stronger", "strength",
                 # "make" is in the key, and it is the verb of every line about what coffee
                 # does to a person: "does coffee make my headaches worse" got the grind-and-
                 # scale answer instead of the headache one. The health words hand those lines
                 # to coffee-jitters and the headache row, and a line about brewing keeps "make".
                 "headache", "headaches", "migraine", "migraines", "worse", "anxious",
                 "anxiety", "jittery", "shaky", "palpitations", "sleep", "awake", "head")),
    # Caffeine is what makes coffee do this, and the answer is how much, when, and when to see a
    # doctor - not a better grind. "coffee makes me anxious" reached the cafe row above because
    # "makes" and "make" are one loose form.
    entry("coffee-jitters", (("coffee", "espresso", "caffeine", "energy drinks", "energy drink"),
                             ("anxious", "anxiety", "jittery", "jitters", "shaky", "shakey",
                              "palpitations", "heart racing", "racing heart", "cant sleep",
                              "can't sleep", "keep me awake", "keeps me awake", "awake",
                              "before bed", "sleep", "panic", "wired", "keeps me up",
                              "keep me up", "up at night", "wide awake", "cant get to sleep",
                              "can't get to sleep",
                              # the shape the question usually takes: "should i have a coffee
                              # this late", "is it too late for coffee", "coffee at 4pm"
                              "late", "too late", "this late", "tonight", "this evening",
                              "in the afternoon", "pm", "ok to")),
          _coffee_late,
          avoid=("stain", "stains", "machine", "pod", "pods", "shop", "buy", "gift", "table",
                 "grounds", "garden", "compost", "plant", "plants", "cupboard", "pregnant",
                 "pregnancy", "baby", "child", "toddler")),
    # A coffee that does not agree with you is its own question: "i feel sick after coffee" was
    # the caffeine half-life answered (how long it stays in you), "coffee gives me stomach ache"
    # reached nothing, and "i cant drink coffee any more it makes me ill" was answered with how to
    # grind beans like a cafe. The fix is about the drink and the stomach, not the hour.
    entry("coffee-upsets-me", (("coffee", "coffees", "espresso", "espressos", "latte", "lattes",
                                "cappuccino", "cappuccinos", "americano", "americano", "caffeine",
                                "energy drink", "energy drinks", "flat white"),
                               ("sick", "queasy", "queasiness", "nausea", "nauseous", "nauseated",
                                "stomach", "stomach ache", "stomachache", "tummy", "gut",
                                "acid", "acid reflux", "reflux", "heartburn", "indigestion",
                                "ill", "disagree", "disagrees", "cant drink",
                                "can't drink", "cannot drink", "any more", "anymore", "upsets",
                                "upset", "bloated", "bloating", "loose", "diarrhoea", "diarrhea",
                                "runs", "toilet", "makes me feel", "feel sick", "gives me")),
          "The caffeine and the acids in coffee are what do it: on an empty stomach coffee "
          "raises stomach acid and speeds the gut on, which is the sick, sloshy feeling. Drink it "
          "after food rather than instead of it, make it weaker (same water, less coffee), try a "
          "darker roast or cold brew, and take it with milk if black is the problem. If it gives "
          "you heartburn, stomach pain or loose stools most days, cut to one small cup and see a "
          "GP.",
          ask=("sick", "queasy", "nausea", "nauseous", "nauseated", "stomach", "stomach ache",
               "tummy", "gut", "acid", "reflux", "heartburn", "indigestion", "ill",
               "disagree", "disagrees", "cant drink", "can't drink", "any more", "anymore",
               "upsets", "upset", "bloated", "bloating", "loose", "diarrhoea", "diarrhea",
               "toilet", "feel sick", "makes me feel", "gives me"),
          # the hour, the jitters and the brewing are three other rows, and the stain is the
          # cleaning table's. "is coffee bad for you" and "is coffee ok on an empty stomach" are
          # the general-health rows and they answer them well - four cups a day, and the caffeine
          # arriving at the same speed either way - so those two lines keep their rows.
          avoid=("bad for you", "empty stomach", "healthy", "unhealthy", "how many cups",
                 "stain", "stains", "machine", "machines", "pod", "pods", "shop", "buy", "gift",
                 "grind", "grinder", "grounds", "compost", "plant", "plants", "cake", "biscuit",
                 "tiramisu", "cafe", "café", "barista", "how long", "half life", "half-life",
                 "sleep", "bed", "bedtime", "late", "awake", "tonight", "evening", "anxious",
                 "anxiety", "jittery", "jitters", "shaky", "palpitations", "headache",
                 "headaches", "migraine", "withdraw", "withdrawal", "decaf", "pregnant",
                 "pregnancy", "taste", "tastes", "strength", "strong", "weak", "how much",
                 "too much"),
          bias=3),

    # The why of the kitchen: a person asking "why does meat go brown" wants the reason, not the
    # method, and on main these lines were reaching the nearest how-to entry or the weather.
    entry("beans-gas",
          (("beans", "bean", "lentils", "lentil", "chickpeas", "chickpea", "pulses",
            "cabbage", "broccoli", "cauliflower", "sprouts", "kale"),
           ("gas", "gassy", "fart", "farts", "farting", "flatulence", "windy", "wind")),
          ("Beans, lentils and the cabbage family carry sugars your small intestine cannot break "
           "down, so the bacteria in your gut ferment them and give off gas. It is normal, and it "
           "settles: rinse tinned beans well, soak dried ones and pour that water away, cook them "
           "properly, and add them a little at a time so your gut adjusts over a few weeks."),
          # a boiler or a gas bill is not this, and "wind" is the weather word as often as the
          # polite one for gas
          avoid=("boiler", "hob", "cooker", "bill", "bills", "meter", "leak", "smell of gas",
                 "central heating", "weather", "forecast", "gale", "door", "gate", "window")),
    entry("potato-green",
          (("potato", "potatoes", "spuds", "spud"),
           ("green", "greening", "greened", "sprouted", "sprouting", "sprouts", "solanine",
            "bitter")),
          ("Green on a potato is chlorophyll, which is harmless, but it comes up in the light "
           "alongside solanine, which is not: cut out any green patches, and bin a potato that is "
           "green all over or has long white sprouts. Keep them in a dark cupboard rather than on "
           "the windowsill, and never eat the sprouts."),
          # keeping them from going green is a storage question and already has its answer;
          # a cupboard in the line means they are asking about storage, not about solanine
          avoid=("how do i stop", "stop them", "keep them from", "prevent", "last longer",
                 "cupboard", "what am i doing wrong", "doing wrong"),
          # keep-potato answers "how do i store them" and ties with this on the word "potatoes":
          # a line that says green wants the solanine, not the cupboard
          bias=1),
    entry("egg-green-ring",
          (("egg", "eggs", "yolk", "yolks"),
           ("green", "grey", "gray", "ring", "sulphur", "sulfur", "greyish")),
          ("The green ring is iron from the yolk meeting sulphur from the white, which happens when "
           "an egg is cooked too long or cooled slowly. It is harmless. Lower eggs into water that "
           "is already boiling, give them 9 to 10 minutes for hard boiled, and run them under cold "
           "water straight away to stop the ring forming."),
          # how long they keep, and how to peel them, are other answers
          avoid=("keep", "keeping", "how long", "storage", "store", "peel", "peeled", "fresh",
                 "gone off", "floating", "float"),
          # egg-boil ties with this on "green": the ring is the question here, not the timings
          bias=1),
    # "my eggs wont peel" was a shrug ("what have you tried so far?"): egg-boil answers the
    # timings, egg-green-ring keeps "peel" out of its key on purpose, and nothing took the
    # peeling itself. The fix is mostly the cooling, so it is the whole answer.
    entry("eggs-peel",
          (("egg", "eggs", "hard boiled", "hard-boiled", "hardboiled"),
           ("peel", "peels", "peeled", "peeling", "shell", "shells", "sticks", "sticking")),
          # no figure in this answer: "how long do i boil an egg" straight after it read "3
          # minutes" as the boiling time, and the answer from the last answer is what a follow-up
          # gets. The cooling is the fix, so it is said without a number.
          "Cool them fast in iced water - an egg peeled warm tears, and the cold sets the white "
          "away from the shell - then tap the shell all over and start at the fat end, where the "
          "air pocket is, with a teaspoon of the water under the shell to loosen it. A teaspoon of "
          "bicarbonate in the pan helps too, and the freshest eggs are the ones that stick, so an "
          "egg a week or two old peels more cleanly than one from today.",
          # the peeling answer, not the timings or the green ring: both carry their own lines
          avoid=("how long", "minutes", "soft boiled", "runny", "green", "grey", "gray", "ring",
                 "poach", "poached", "scramble", "scrambled", "fry", "fried", "keep", "keeping",
                 "store", "fresh", "float"),
          bias=1),
    # "the potatoes came out watery" got the watery-sauce fix, and "my lasagne was runny" got
    # the same one: a dish that goes wet is not a sauce that needs reducing, and each of these
    # has a cause of its own.
    entry("potato-watery",
          # not the bare word "mash": "my mash is watery" has its own answer (cold milk, wet
          # potatoes), and this one never mentions milk
          (("potato", "potatoes", "boiled potatoes", "mashed potatoes"),
           ("watery", "waterlogged", "soggy", "wet", "sloppy")),
          "Drain them the second a knife slides in and let them sit in the colander off the heat "
          "for 2 minutes so the steam escapes: potatoes go watery when they sit in their water, "
          "and a lid left on traps it back on. Save a splash of the cooking water to loosen mash "
          "instead of milk if it still looks wet.",
          avoid=("sauce", "soup", "stew", "casserole", "curry", "gravy", "sweet", "salad",
                 "keep", "keeps", "fridge", "freezer", "roast", "oven", "gratin"),
          # fix-watery answers a wet dish in general, it already carries bias 1, and it comes
          # earlier in this list, so it takes the tie on two key parts. A pan of potatoes is not
          # a sauce to reduce, so this one sits above it.
          bias=3),
    entry("lasagne-runny",
          (("lasagne", "lasagna", "moussaka", "cannelloni"),
           ("runny", "watery", "sloppy", "wet", "slumped", "fell apart", "falls apart")),
          "Let it stand 10 to 15 minutes out of the oven before you cut it, which is what sets the "
          "layers: a lasagne that runs was cut straight from the oven. Next time reduce the ragu "
          "until a spoon leaves a trail and use a thicker bechamel - 50g each of butter and flour "
          "to 500ml of milk - with the egg in it.",
          avoid=("recipe", "recipe for", "vegetarian", "vegan", "freeze", "frozen", "keep",
                 "reheat", "calories", "how do i make", "how to make", "sauce"),
          # it ties fix-watery, which already carries bias 1, and a lasagne that will not set
          # is not a sauce to reduce
          bias=2),
    # "the sauce tastes bitter" was an echo ("Got it - is there anything you'd like a hand
    # with?"): garlic-burn wants garlic in the line, tea-brew wants tea, and nothing took a
    # bitter sauce. Bitterness in a sauce is nearly always burnt garlic, a roux taken too far,
    # or an oil that has gone over.
    entry("sauce-bitter",
          (("sauce", "sauces", "gravy", "soup", "stew", "ragu", "curry", "casserole", "chilli"),
           # not bare "sour": "can i use sour cream in a curry" is a swap question, and
           # "sweet and sour" names a dish. The fault is said as a taste.
           ("bitter", "bitter taste", "tastes bitter", "too bitter", "tastes sour",
            "sour taste", "went sour", "turned sour", "is sour")),
          "Bitter in a sauce is burnt garlic, a roux or flour taken past golden, or a burnt pan "
          "scraped back in; a pinch of sugar, a spoon of cream and a squeeze of lemon take the "
          "edge off, but if it tastes of scorched garlic or flour there is no rescuing it. Low "
          "heat, garlic in last and stirred for 30 seconds is the fix next time.",
          avoid=("beer", "coffee", "tea", "chocolate", "green", "sprout", "sprouts", "lemon",
                 "orange", "greens", "keep", "keeps", "store", "fridge", "freezer", "almond",
                 "almonds", "melon", "cucumber", "kale",
                 "sour cream", "sweet and sour", "sourdough", "sauerkraut")),
    entry("smoothie-thick",
          (("smoothie", "smoothies", "shake", "protein shake"),
           ("thick", "too thick", "gluey", "stodgy", "lumpy", "wont blend", "not blending",
            # "how do i make my smoothie thinner" is the same job as "too thick": it wants
            # liquid in, so this row already holds the right answer for it.
            "thinner", "less thick", "thin it", "thin it out", "make it thinner")),
          "Loosen it with liquid before anything else - a splash of milk, water or juice, then "
          "blend again - and add ice last: a smoothie thickens as it stands, so make it a little "
          "thinner than you want it, and a spoon of yoghurt or half a banana gives body without "
          "the clag.",
          avoid=("recipe", "recipes", "calories", "healthy", "protein", "green", "diet")),
    # The other direction of the row above, and the one that had no answer at all: "how do i
    # make my smoothie thicker" is asking for less liquid and more solid, so it cannot be the
    # loosen-it reply. The row above needs a complaint about thickness, so the words that ask
    # for the opposite are its own key here.
    entry("smoothie-thin",
          (("smoothie", "smoothies", "shake", "protein shake", "milkshake", "milkshakes"),
           ("thicker", "thicken", "more filling", "filling", "add body", "more body", "bulk it",
            "too thin", "so thin", "very thin", "watery", "runny", "not filling")),
          "Leave some of the liquid out and put something solid in instead: half a banana, a "
          "spoon of Greek yoghurt, oats or peanut butter, or a handful of frozen fruit, then "
          "blend it again. Pour the milk or juice in last, a splash at a time, until it moves "
          "the way you want - ice waters it down, so keep it to a few cubes.",
          avoid=("recipe", "recipes", "calories", "healthy", "protein powder", "diet",
                 "too thick", "loosen", "add milk", "more milk")),
    entry("cheesecake-cracked",
          (("cheesecake", "baked cheesecake"),
           ("crack", "cracked", "cracks", "cracking", "sank", "fallen", "fell")),
          "A cracked cheesecake was overbaked or cooled too fast: bake it until the edge is set "
          "and the middle still wobbles, then turn the oven off and leave it inside with the door "
          "ajar for an hour so it comes down to room temperature slowly. Sour cream on top hides "
          "any crack, and a water bath stops most of them.",
          avoid=("recipe", "recipe for", "how do i make", "no bake", "no-bake", "chill", "set in the fridge", "buy")),
    entry("ice-cream-icy",
          (("ice cream", "icecream", "sorbet", "frozen yoghurt"),
           ("icy", "ice crystals", "crystals", "grainy", "rock hard", "freezer burn")),
          "Icy ice cream is water freezing into crystals: more fat and sugar (cream instead of "
          "milk, a spoon of glucose or a splash of alcohol), churn it cold, and stir a home-made "
          "tub every 30 minutes for the first 3 hours so the crystals stay small. A freezer that "
          "runs very cold makes it harder still, so move it to the door shelf.",
          avoid=("recipe", "recipe for", "how do i make", "calories", "buy", "shop", "keep",
                 "keeps", "freezer burn on meat")),
    entry("chocolate-bloom",
          (("chocolate", "chocolates"), ("white", "bloom", "grey", "gray", "streaky", "dusty",
                                         "patchy")),
          ("White streaks on chocolate are bloom, and it is harmless: either the cocoa butter has "
           "melted and set again, or damp has pulled sugar to the surface. It still melts and "
           "tastes the same. Keep it in a cool cupboard around 15 to 18C rather than the fridge, "
           "which is what causes it."),
          avoid=("white chocolate", "hot chocolate", "drinking chocolate", "milk chocolate",
                 "dark chocolate", "chocolate bar", "recipe", "cake", "mug", "sauce")),
    # What to mix with a bottle, which is a real ask the day before a party and met the search
    # hedge. It is a drinks question rather than a recipe, so it names what flatters each spirit
    # instead of one cocktail to follow.
    entry("drink-mixer",
          (("gin", "vodka", "rum", "whisky", "whiskey", "brandy", "tequila", "spirit", "spirits"),
           ("mixer", "mixers", "mix", "mix with", "goes with", "good with", "tonic", "what goes",
            "what should i", "serve with", "drink", "drinks", "dark rum", "white rum",
            "spiced rum", "what can i mix", "what to mix")),
          "Gin wants tonic about one to three with a big wedge of lemon or lime, and cucumber or a "
          "sprig of rosemary if you have it; vodka takes the same plus elderflower or ginger beer, "
          "dark rum wants ginger beer and a squeeze of lime, whisky wants soda or ginger ale, and "
          "tequila wants grapefruit soda and salt. Cheap tonic is fine but use plenty of ice and "
          "stir it, because a warm, flat G and T tastes of nothing.",
          # A spirit in a recipe is a cooking question, and the units or the price are other ones.
          avoid=("recipe", "cake", "sauce", "marinade", "flambe", "how much", "units", "calories",
                 "is gin bad", "how is gin made", "distillery", "cheapest", "price")),
    entry("browns-in-the-pan",
          (("meat", "steak", "steaks", "chicken", "roast", "onions", "bacon", "sausages",
            "bread", "toast", "chips", "potatoes", "browning", "pork", "lamb"),
           ("brown", "browns", "browning", "crust", "sear", "seared", "searing", "maillard",
            # the same complaint said as the colour it went instead: "my steak is grey", "the
            # meat is grey", "my bacon went grey" and "the sausages are grey" were two echoes
            # and a shrug, and this card is the one that already says it goes grey in a
            # crowded pan
            "grey", "gray", "greyish", "went grey", "goes grey", "no colour", "no color",
            "isnt brown", "isn't brown", "not brown", "didnt colour", "didn't colour")),
          ("It is the Maillard reaction: past about 140C the sugars and amino acids on the surface "
           "rearrange into hundreds of new flavour compounds, and that is the brown crust and the "
           "savoury smell. Pat the surface dry first, get the pan properly hot, and leave space, "
           "because steam from a crowded pan keeps everything at boiling and it goes grey instead."),
          # don't cook it through, is it safe, how long: those are other answers, and "brown
          # bread" and "brown rice" are the colour of the food, not what the pan did to it
          # `grey` and `gray` used to be fenced here, which left the complaint said as a colour
          # ("my steak is grey") with no answer at all: an echo or a shrug. The senses that are
          # not the pan - meat that has gone off, mould, a pale roast chicken skin - are fenced
          # by their own words instead.
          avoid=("safe", "done", "raw", "pink", "blood", "thermometer", "temperature", "how long",
                 "pale", "stew", "casserole", "slow cooker",
                 "smell", "smells", "smelly", "gone off", "went off", "off", "mould", "mold",
                 "mouldy", "moldy", "slimy", "slime", "is it ok", "ok to eat", "safe to eat",
                 "food poisoning", "bad", "date", "use by", "keep", "keeping", "freezer",
                 "freeze", "fridge", "left out",
                 "brown bread", "brown rice", "brown sugar", "brown flour", "wholemeal",
                 "white bread", "white rice", "better for you", "healthy", "healthier",
                 "good for you", "calories", "fibre")),
    entry("milk-curdle",
          (("milk", "cream", "yoghurt", "yogurt"), ("curdle", "curdled", "curdles", "curdling",
                                                    "split", "splits", "lumpy")),
          ("Milk curdles when heat or acid makes its proteins clump together: lemon, wine, vinegar "
           "or tomatoes, or a hard boil. Add acid off the heat and slowly, keep dairy out of a "
           "rolling boil, and stir a spoonful of flour or cornflour into the milk first when you "
           "are cooking it into a sauce."),
          avoid=("sour cream", "creme fraiche", "crème fraîche", "buttermilk", "keep", "keeping",
                 "gone off", "off", "date", "freeze", "freezer", "breast", "formula", "baby")),
    # The everyday "how do I cook this" asks that had no entry: a roast joint, a batter, a scone,
    # a curry base, a cake that will not leave the tin, a pizza from the freezer and a pie with a
    # soggy bottom. Each is keyed on the dish plus an ask, so a passing mention ("I had pancakes
    # for breakfast") is left to another module.
    entry("roast-lamb", (("lamb", "leg of lamb", "shoulder of lamb"),
                          ("roast", "roasting", "oven", "cook", "joint", "leg", "shoulder")),
          "A leg of lamb is 25 minutes per 500g at 200C (180C fan), then 15 minutes resting under "
          "foil: about 1 hour 5 in total for a 2kg leg pink, 1 hour 25 for well done. Score the "
          "fat into diamonds, push garlic and rosemary into the cuts, and put it in a hot oven.",
          avoid=("chop", "chops", "leftover", "mince", "keema", "casserole", "hotpot", "stew",
                 "kebab", "shank", "curry", "shepherd", "goes with", "with it", "side",
                 # a shoulder is a long slow cook, and the slow-roast entry answers it
                 "shoulder",
                 # a slow roast is the other method entirely: a shoulder at 150C for four to five
                 # hours, not 25 minutes per 500g at 200C, and the slow-roast entry has it
                 "slow", "slowly", "slow roast", "slow roasted", "slow-roasted", "low and slow",
                 # how long the joint rests is rest-meat's question, not the roasting time
                 "rest", "resting", "rested",
                 # a curry is not a roast, and the roast-joint row next door avoids it too
                 "curry", "curries"),
          ask=("how long", "how many minutes", "time", "minutes", "temperature", "degrees",
               "gas mark", "how hot", "per kilo", "per kg", "per pound", "what temperature",
               # the plain ask the kitchen sends without a number in it: "how do i roast a leg
               # of lamb" was a shrug on every head before this
               "how do i roast", "how do i cook", "how should i cook", "how to roast",
               "how to cook", "best way to roast", "best way to cook"),
          bias=2),
    # Nothing answered "how long should i knead dough": the plan's proving time came back, which
    # is the wrong fifteen minutes to give someone with their hands in the bowl. One entry, and
    # the proving words are its avoid so a rest-or-rise question keeps its own answer.
    entry("knead-dough", (("knead", "kneading", "kneaded"),
                          ("dough", "bread", "how long", "long", "much", "should", "by hand",
                           "mixer", "machine", "enough", "until")),
          "Knead it 10 minutes by hand, or 5 to 8 minutes in a mixer with a dough hook: it is "
          "ready when it is smooth, feels a little tacky, and springs back when you press a "
          "finger in. The real test is to stretch a piece thin enough to see light through it "
          "without it tearing.",
          ask=("knead", "kneading", "how long", "how much", "should", "do i", "by hand", "mixer"),
          # a named dough keeps its own recipe: "how long should i knead pizza dough" is the
          # pizza dough entry, which has the weights and the 8 minutes in the same answer
          avoid=("prove", "proving", "proof", "proving time", "rise", "rises", "rising", "rest",
                 "resting", "sourdough", "pastry", "shortcrust", "pasta", "cake", "cookie",
                 "cookies", "biscuit", "biscuits", "no knead", "no-knead", "pizza dough",
                 "naan", "flatbread", "focaccia", "brioche", "croissant", "hot cross buns"),
          bias=1),

    entry("cake-tin-grease", (("cake", "sponge", "loaf", "bread", "baking tin", "cake tin",
                               "pastry", "bundt", "bundt tin",
                               "pie", "tart", "quiche",
                               # the small tins a person greases one by one: the general
                               # prepare-the-tin row was answering muffins and buns, and every
                               # one of them wants the same butter-and-flour
                               "muffin", "muffins", "bun", "buns", "cupcake", "cupcakes",
                               "sandwich tin", "springform", "loaf tin", "muffin tin"),
                               ("tin", "tins", "pan", "grease", "greasing", "greased", "line",
                                "lining", "lined", "parchment", "baking paper", "springform",
                                "stick", "sticks", "sticking")),
          "Rub the inside of the tin all over with butter or a little oil, then dust it with flour "
          "and tip the extra out, or cut a circle of baking parchment for the base: either is enough "
          "for a sponge, and both together never hurt. For a fruit cake or a big loaf, line the "
          "sides with a strip of paper too, and let the cake cool 10 minutes in the tin before you "
          "turn it out. A pastry case wants only a thin smear of butter and no flour, or the base "
          "goes soggy.",
          ask=("grease", "greasing", "line", "lining", "paper", "parchment", "stick", "sticking",
               "how do i", "how should i", "what do i", "why does"),
          # A tin to clean is not a tin to line: "how do i clean a burnt cake tin" was answered
          # with the butter-and-flour method, which is how to prepare a tin for the next cake.
          avoid=("sink", "sank", "sunken", "risen", "rise", "leftover", "freeze", "freezer",
                 "out of the tin", "out of a tin", "out of the pan", "out of a pan",
                 "turn it out", "turn out", "stuck", "how long", "recipe",
                 "loosen", "loosening", "loosened", "free the cake",
                 "clean", "cleaning", "cleaned", "wash", "washing", "scrub", "scour", "soak",
                 "burnt on", "baked on", "crusted", "off the tin",
                 # greasing a tin is never the answer to a burnt one, however the line puts it:
                 # "how do i get the burnt off my cake tin" still got butter and flour
                 "burnt", "burned", "burning", "scorched", "charred",
                 # a fruit cake's tin is the deep-tin answer's, not this one's: lining one for a
                 # Christmas cake takes a double thickness and a paper collar, not a paper circle
                 "fruit cake", "christmas cake", "rich fruit", "wedding cake", "simnel",
                 "dark fruit",
                 # a bundt has no flat base for a paper circle and wants the paste instead, which
                 # is its own row below
                 "bundt", "bundt tin", "bundt pan",
                 # pastry in a tin is the pastry row's, which chills it before it goes in:
                 # "how do i stop pastry sticking" was answered with butter and flour for a cake
                 "pastry", "shortcrust", "shortcrust pastry", "pastry case", "chill the pastry",
                 "chilling", "banneton", "proving basket",
                 # dough on a bench or on your hands is the dough row's: the word "bread" in this
                 # key was catching "how do i stop bread dough sticking to my hands" as a tin
                 "dough", "hands", "bench", "knead", "kneading", "wet dough", "sticky"),
          # the general "butter it and dust it with flour" row answers a tin as well as a pan,
          # and a cake tin wants the paper for the base and the ten minutes cooling: this row is
          # the cake's, so it sits in front of the pan's
          bias=3),

    # A bundt has no flat base for a paper circle, so the tin the cake is baked in changes the
    # method rather than just the size: the grooves want a paste brushed into every one of them,
    # and a paper circle in a ring tin is useless. "how do i grease a bundt tin" was the general
    # "butter it and dust it with flour" card, which sends a person to a paper circle that has
    # nowhere to sit.
    entry("bundt-tin",
          (("bundt", "bundt tin", "bundt pan", "ring tin", "kugelhopf", "gugelhupf",
            "bundt cake"),
           ("grease", "greasing", "greased", "line", "lining", "flour", "dust", "dusting",
            "stick", "sticking", "stuck", "comes out", "come out", "turn out", "prepare",
            "paste", "how do i", "should i")),
          "A bundt has no flat base for a paper circle, so use a paste instead: mix equal weights "
          "of soft butter and plain flour (a tablespoon of each is plenty for a big tin) and brush "
          "it into every groove with a pastry brush, getting right into the corners and the central "
          "tube. Tap out any loose flour and bake the cake as the recipe says, then let it stand 10 "
          "minutes in the tin before turning it out - any longer and the steam softens the crust "
          "and it tears. A silicone bundt needs no paste at all, just a light oil.",
          # a cake that already stuck, a keeping question and the tin-size measurements are other
          # rows, and a bundt cake recipe is the baking card's
          avoid=("recipe", "how long", "oven", "temperature", "calories", "keep", "freeze",
                 "frozen", "stale", "size", "which tin", "how big", "stuck to", "came out of",
                 "didnt come out", "didn't come out", "sank", "raw", "burnt", "burned"),
          bias=3),

    # Stuck in the tin, not sticking to it: the prevention is below, and the two were one entry
    # until "how do i stop cake sticking to the tin" had to choose between a rescue and a fix.
    # A guard phrase matches the words that are there, so "out of the tin" did not catch "out of
    # a tin", "out of its pan" or "loosen a cake from the tin": those went to the tin-size row,
    # to the greasing row, or to the stuck-in-the-tin line that is about a life. Same answer,
    # every spelling of the sentence.
    entry("cake-out-of-tin", (("cake", "sponge"),
                               ("out of the tin", "out of a tin", "out of the pan",
                                "out of a pan", "out of its tin", "out of its pan", "stuck",
                                "release", "turn it out", "turn out", "take it out",
                                "loosen", "loosening", "loosens", "run a knife", "free the cake",
                                "breaking", "without breaking")),
          "Let it cool in the tin for 10 minutes, until it starts to shrink from the sides, and "
          "turn it out then: too hot and it breaks, stone cold and it sticks. Run a thin knife "
          "round the edge first, and line the tin with baking paper next time so it cannot grab.",
          avoid=("sink", "sank", "risen", "rise", "leftover", "freeze", "freezer", "fruit")),
    # Baking basics: the plain "how do I make a loaf / a cake / cookies" ask, which used to fall
    # back or reach a plan gadget. One entry per thing baked, keyed on the thing plus the ask.
    # --- the three that got another food's answer ------------------------------
    # A pastry base is the one "soggy" the dishes table cannot route, because a pastry base is not
    # a plan, so "why is my pastry soggy" was answered with the pasta-and-roast general text.
    entry("pastry-soggy", (("pastry", "pie", "pies", "quiche", "quiches", "tart", "tarts",
                            "flan", "pastry base", "pie base", "shortcrust"),
                           ("soggy", "sad", "wet", "bottom", "base", "blind", "blind bake",
                            "crisp", "crispy")),
          "Bake it blind: chill the lined tin for 20 minutes, prick the base, cover it with paper "
          "and baking beans, then 15 minutes at 200C (180C fan) and 5 minutes uncovered to dry the "
          "base out. Brush the hot base with beaten egg so the filling cannot soak in, and cook a "
          "wet filling down first - a quiche or a fruit pie goes soggy from the inside too.",
          ask=("soggy", "sad", "wet", "bottom", "base", "blind", "blind bake", "crisp", "crispy"),
          bias=2,
          avoid=("how do i make pastry", "pastry recipe", "make shortcrust", "shortcrust recipe",
                 "puff pastry", "filo", "choux", "pastry flour", "pasta", "pizza")),
    # An omelette that sticks is a heat-and-fat question, and the answer it used to get was about a
    # different pan and a different fault: "it has lost its baked-on oil" (seasoning) or a bicarb
    # soak (a burnt pan).
    entry("omelette-sticking", (("omelette", "omelet", "omelettes", "omelets", "frittata",
                                 "scrambled eggs", "scrambled egg"),
                                ("sticking", "sticks", "stuck", "pan", "sticking to the pan",
                                 "burnt", "burning", "heat")),
          "Turn the heat down and add fat: a knob of butter with a teaspoon of oil in a pan that is "
          "already hot, then the egg in when the butter foams but has not browned, and a silicone "
          "spatula pushing the set edges into the middle. A stainless pan is ready when a drop of "
          "water beads and skitters across it; on a non-stick one, no metal tools and no empty pan "
          "over a high heat.",
          ask=("omelette", "omelet", "omelettes", "omelets", "frittata", "scrambled egg",
               "scrambled eggs"),
          bias=2),
    # "how much salt in bread dough" was the six-grams-a-day limit for a person, and "how much
    # yeast for 500g flour" and "how much water in bread dough" were a shrug. A loaf is a set of
    # percentages, so the entry gives the percentages and the grams together.
    entry("bread-quantities", (("bread", "breads", "dough", "loaf", "loaves", "flour",
                                "baguette", "rolls", "buns",
                                # an ingredient of the loaf names the loaf as well: "how much
                                # yeast do i need" was a search shrug, because the row wanted
                                # the word bread or dough before it would read the word yeast.
                                "yeast"),
                               ("salt", "yeast", "water", "hydration", "how much", "how many",
                                "grams", "percentage", "percent", "ratio", "quantity",
                                "quantities")),
          "For a 500g loaf: 10g of salt, 7g of dried yeast and 320ml of tepid water. That is the "
          "ratio to remember rather than the grams - 2% salt, a little over 1% yeast and about 64% "
          "water by flour weight - so double the flour and double all three. The dough should feel "
          "tacky but come away from the bowl; add water a spoon at a time if it is stiff and a "
          "spoon of flour if it is sloppy.",
          # The line has to be making bread: "how much flour" is the pancakes' question and
          # belongs to whatever recipe is being made, so a bare amount asks nothing here.
          ask=("bread", "dough", "loaf", "loaves", "yeast", "sourdough", "prove", "knead",
               "breadmaker", "hydration"),
          bias=2,
          avoid=("cake", "cakes", "sponge", "pastry", "scone", "scones", "pancake", "pancakes",
                 "batter", "yorkshire", "gravy", "sauce", "thicken", "porridge", "pasta",
                 "rice", "couscous", "pizza", "naan", "pitta", "pita", "soda", "banana",
                 # a person's water is not a dough's water, and neither is a person's salt
                 "drink", "drinking", "drunk", "thirsty", "thirst", "glasses", "litres",
                 "liters", "bottle", "bottled", "tap water", "dehydrated", "hydrated",
                 "a day", "adult", "child", "children", "baby", "blood pressure", "diet",
                 # "bread" is two questions: what goes into a loaf and what a slice does to you.
                 # This entry answers the first, so the nutrient words and the eating shapes
                 # stand it down - "how much protein in a slice of bread" is the nutrient table's
                 # line, and the salt, yeast and water ratio is an answer to another question.
                 # a drink is brewed with yeast too, and its own row is the one that knows
                 "beer", "brewing", "wine", "cider", "kombucha",
                 "protein", "calories", "calorie", "kcal", "carbs", "carb", "carbohydrate",
                 "carbohydrates", "fibre", "fiber", "fat", "fats", "sugar", "sugars", "iron",
                 "vitamin", "vitamins", "nutrition", "nutrients", "healthy", "good for you",
                 "slice", "slices", "sandwich", "sandwiches", "toast", "toasted",
                 "sourdough", "starter", "gluten free", "gluten-free", "breadmaker",
                 "bread maker", "machine",
                 # ...and what is in the bread is not what goes into it: "how much salt is in a
                 # slice of bread" and "how much sugar in bread" are questions about the loaf you
                 # buy, and the amounts to bake one with leave those unanswered.
                 "slice", "slices", "sliced", "per slice", "in a slice", "sugar", "calories",
                 "carbs", "carbohydrate", "fibre", "fiber", "healthy", "unhealthy",
                 "good for you", "bad for you", "nutrition", "how much is in")),

    entry("cookies-basic", (("cookie", "cookies", "biscuit", "biscuits"),
                             ("how do i make", "how to make", "recipe", "from scratch", "make",
                              "bake", "chewy", "crispy")),
          "125g soft butter creamed with 100g sugar, an egg beaten in, then 200g plain flour and "
          "half a teaspoon of baking powder. Roll walnut-sized balls, space them well apart, and "
          "bake at 180C (160C fan) for 10 to 12 minutes - they firm up as they cool.",
          # a named biscuit has its own recipe in the person's head: oat cookies made with plain
          # flour and no oats is a wrong answer, so this generic one steps aside.
          avoid=("leftover", "stale", "freeze", "freezer", "raw", "dog", "digestive", "rich tea",
                 # "chewy" and "crispy" are in the key because a texture question is still a
                 # cookie question, but this reply says nothing about texture, and the chewy and
                 # the hard-biscuit answers do: they take those lines
                 "chewy", "chewier", "chewiness", "gooey", "squidgy", "soft centre",
                 "oat", "oats", "ginger", "shortbread", "flapjack", "peanut", "chocolate chip",
                 "without egg", "without eggs", "no egg", "no eggs", "egg free", "egg-free", "eggless",
                 "vegan", "dairy free", "dairy-free", "flax", "aquafaba") + NO_SUGAR),
    # "ice a cake" and "icing a cake" are the same job said as a verb, and neither had an
    # answer: "how do i ice a cake" was a shrug. The act is a phrase so that a bag of ice, an
    # iced bun and an ice-cream are not kitchen jobs, and "cake" in the second half is what
    # lets the verb form score: the first half still needs an icing word.
    entry("buttercream", (("icing", "buttercream", "frosting", "ice a cake", "ice the cake",
                            "icing a cake", "ice cupcakes", "icing cupcakes",
                            "cover a cake", "coat a cake", "put icing on"),
                           ("how do i make", "how to make", "recipe", "make", "for a cake",
                            "chocolate", "vanilla", "cake", "cakes", "cupcake", "cupcakes")),
          "Beat 100g soft butter with 200g icing sugar, a spoonful at a time, then a splash of "
          "milk or vanilla until it is light and spreadable. That covers the top and middle of a "
          "20cm cake; for chocolate, beat in 50g cooled melted dark chocolate.",
          # Making it in advance is a keeping question and main answers it ("3 to 4 days in the
          # fridge"); the recipe used to take that turn.
          avoid=("leftover", "freeze", "freezer", "keeps", "keep", "gone hard", "runny",
                 "sugar paste", "fondant", "day before", "night before", "ahead", "fridge",
                 "in advance", "days") + NO_SUGAR),
    # "pipe" and "write" are verbs with two lives: a plumber's pipe, an icing bag, and the pen
    # of a letter. The written-letter side of "write" is in the avoid list below.
    # "pipe" is a verb with two lives: a plumber's pipe and an icing bag. The bot had neither
    # answer, so "how do i pipe a swirl" and "how do i pipe buttercream roses" got the search
    # line about calling a plumber, and "how do i pipe icing on a cake" got the buttercream
    # keeping answer. The act is the first key part and the thing being piped the second, so
    # "how do i make icing" stays with the recipe above and a leaky pipe reaches nothing here.
    entry("cake-piping", (("pipe", "piping", "piped", "icing bag", "piping bag", "nozzle",
                           "nozzles", "star tip", "star nozzle", "icing nozzle", "swirl",
                           "swirls", "rosette", "rosettes", "cake decorating", "decorate a cake",
                           "write on a cake", "writing on a cake", "lettering",
                           # the same two verbs again, as what a letter is written on: the
                           # cake is named, and the words are the ones a bag is used for
                           "write happy birthday", "writing happy birthday",
                           "happy birthday on", "message on a cake", "message on the cake",
                           "name on a cake", "name on the cake"),
                          ("icing", "buttercream", "frosting", "cake", "cakes", "cupcake",
                           "cupcakes", "swirl", "swirls", "rose", "roses", "rosette",
                           "rosettes", "letters", "lettering", "writing", "tip", "nozzle",
                           "bag")),
          "Stiff buttercream, or cream whipped until it holds a peak, a star nozzle and a steady "
          "squeeze: hold the nozzle 1cm above the cake, squeeze, then stop squeezing before you "
          "lift away or you get a tail. For a swirl start in the middle and spiral out; a 1M star "
          "tip does swirls and roses, a plain round tip is for writing. Chill the icing 15 minutes "
          "if it slumps, and practise on a plate first.",
          ask=("how", "what", "which", "best", "tip", "tips", "should", "can", "do i",
               "technique", "help"),
          # a plumbing question names a pipe and nothing this entry answers; a keeping question
          # about icing is the fridge answer's line, and the recipe above is "make icing"
          avoid=("plumber", "plumbing", "boiler", "radiator", "leak", "leaking", "leaks", "burst",
                 "copper", "solder", "soldering", "drain", "water pipe", "pipe under", "under the",
                 "washing machine", "tap", "gutter", "lagging", "frozen pipe", "keep", "keeps",
                 "keeping", "fridge", "freezer", "leftover", "store", "storing", "days",
                 "make icing", "make buttercream", "make the icing",
                 # "write" and "letter" are the same pair of words as a cake you write on and
                 # a letter you write to somebody, and the icing answer took nine of them:
                 # a cover letter, a resignation, a thank you, a complaint, a letter to a
                 # landlord, an MP, the council, a school appeal and an apology all got
                 # "stiff buttercream, a star nozzle and a steady squeeze". The acts are told
                 # apart by what is being written, so the written-letter words are named here
                 # and the letter entries keep the lines they answer.
                 # Only the shapes that are a letter and never a cake: a bare "neighbour",
                 # "school" or "love" here made the icing answer give up "how do i pipe a
                 # name on a cake for my neighbour", which is a cake.
                 "cover letter", "resignation", "reference", "cv", "letter of",
                 "letter to", "letter for", "letter about", "thank you letter",
                 "letter to my", "in writing", "put it in writing",
                 "love letter", "love note", "love poem", "valentine",
                 "complaint", "complain", "eulogy", "sick note",
                 # ...and the plainest one of all: "how do i write a letter" was the icing
                 # answer, because "write" reached "writing" and "letter" reached "letters".
                 # Two signals, no cake in the line. The phrases below are all a letter and
                 # never a cake.
                 # Only the shapes that cannot be a cake: "write a letter" is also "how do i
                 # write a letter on a cake", and standing down for it left that line with no
                 # answer at all, because the formal-letter row will not take the word cake.
                 "write letters to", "writing letters to",
                 "send a letter", "sending a letter", "a letter to", "letter to a",
                 "letters to",
                 # The same word reached the start and the end of a letter: "what do i write
                 # at the start of a letter" was the icing card, because "write" and "letter"
                 # are the two signals it needs. A phrase with "the" in it is a letter being
                 # written and never a cake, and "pipe the letters on a cake" still is not
                 # caught, as it has no "the ... letter" phrase.
                 "of a letter", "start of a letter", "end of a letter",
                 "beginning of a letter", "top of a letter", "in a letter")),
    entry("chocolate-cake", (("chocolate cake", "chocolate sponge"),
                              ("how do i make", "how to make", "recipe", "from scratch", "make",
                               "bake", "basic", "simple")),
          "200g plain flour, 200g sugar, 50g cocoa, 2 eggs, 150ml milk and 100g melted butter, "
          "whisked together and baked in two lined tins at 180C (160C fan) for 22 to 25 minutes. "
          "Sandwich it with buttercream or jam and it stays soft for days.",
          avoid=("leftover", "freeze", "freezer", "sink", "sank", "mug", "vegan", "gluten")),
    # A whole bird is carved after it rests, and a pan of vegetables is soup before it is
    # anything else: the three plainest jobs in a kitchen that had no answer at all.
    # "joint" is not a bird word: "how do i carve a joint of beef" was getting the bird method,
    # and a confident wrong answer is worse than the shrug it replaced.
    # The reply carries no bare figure on purpose: "how long do i roast a chicken" asked straight
    # after it is read as a part of this answer and cut down to the first number in it, and a cook
    # following "10 minutes" would take the bird out raw. The rest time belongs to the roast.
    entry("carve-chicken", (("carve", "carving", "carved"),
                            ("chicken", "roast chicken", "turkey", "bird")),
          "Take the legs off first: cut the skin between leg and body, bend the leg outwards and "
          "cut through the joint rather than the bone. Then slice each breast across the grain "
          "from the thin end, keeping the knife flat against the carcass, and let the bird rest "
          "before you start if you can.",
          avoid=("ham", "beef", "lamb", "pork", "gammon", "joint of", "wood", "stone", "pumpkin",
                 "chicken breast", "chicken breasts", "carving knife", "carving board",
                 # a dish that is not a bird: a soup line read with an earlier subject put
                 # back in once reached this answer, and carving a bird is the wrong method
                 "soup", "soups", "stew", "casserole", "sauce", "gravy", "pizza", "dough",
                 "bread", "cake", "curry")),
    # The recipes table answers "how do i make soup" and "i want to make soup" with the onion,
    # carrot and celery method, and it is the better answer, so this one stays away from those
    # lines and takes the asks it misses: "what soup can i make", "do you have a soup recipe".
    entry("soup-plain", (("soup", "soups"),
                         ("make", "homemade", "from scratch", "basic",
                          "how do i", "recipe")),
          "Soften an onion in oil for 8 to 10 minutes, add whatever vegetables you have, cover "
          "them with stock by an inch and simmer 20 minutes. Blend it if you want it smooth, and "
          "season at the end - a spoon of cream or a squeeze of lemon lifts a plain soup.",
          # A bare "quick" or "plain" in the key took "how do i make a quick soup" and "how do
          # i make plain soup" from soup-make, which names the vegetables and the 700g. Those
          # are "how do i make soup" with an adjective, so this entry only takes the asks that
          # soup-make cannot read: "what soup can i make", "got a soup recipe".
          ask=("what", "recipe", "do you have", "got a", "any ideas", "easy",
               "soup ideas"),
          avoid=("thicken", "thick", "thicker", "watery", "runny", "freeze", "frozen", "keep",
                 "leftover", "reheat", "healthy", "calories", "tinned", "store",
                 "storing", "stored", "stock", "bought", "shop")),
    # The counter row and the frozen row both stand down for a heat word now, so this row has to
    # key the heat itself: "what gas mark for pizza" and "what temp for pizza" name no cooking
    # verb and no frozen pizza, and without these they got an apology where main at least had a
    # card. The answer already carries the heat, so the line gets a number.
    entry("pizza-home", (("pizza",),
                         ("cook", "cooking", "bake", "oven", "at home", "stone", "tray",
                          "how do i", "best way",
                          "temp", "temperature", "gas mark", "how hot", "degrees", "heat",
                          "oven setting", "what setting", "fan")),
          # The bake time comes first and the preheat carries no figure: "how long do i cook a
          # pizza" asked after this is cut down to the first number in the answer, and "20
          # minutes" is the heating, not the cooking.
          "Heat the oven as high as it goes with a heavy tray or a pizza stone inside, then slide "
          "the pizza onto the hot tray and give it 8 to 12 minutes, until the edge blisters and "
          "the underside is crisp: a thin base and a preheated surface do what an oven alone will "
          "not. Keep the toppings light, because too much sauce or cheese steams the middle.",
          # "how do i make pizza at home" is the dough, which the dough entry answers with the
          # weights; this one is the oven and the tray.
          avoid=("base", "dough", "yeast", "flour", "make", "making", "from scratch", "recipe",
                 "freeze", "frozen", "leftover", "reheat", "takeaway", "order", "delivery",
                 "healthy", "calories")),
    entry("pesto-bitter", (("pesto",),
                           # a bare "why" made "why is my pesto thick" the bitter answer: the
                           # fault word itself is what asks the question, so it is not in the key
                           ("bitter", "bitterness", "taste", "tastes", "fix")),
          "Bitterness is usually the raw garlic and the pine nuts: toast the nuts, use half a "
          "small clove, and stir in a handful of parsley or a squeeze of lemon at the end. Blitz "
          "in short pulses, because blending for a long time warms the basil and turns it bitter, "
          "and keep it in the fridge under a film of oil for a week.",
          # "pesto" holds a "pest", which is a pest controller's word in the shrug table, so the
          # cooking answer has to exist for the line to stay out of it. Main's own `pesto` row
          # keys the making words, and "how do i stop pesto tasting bitter" matches both: the
          # fault is the narrower subject, so this one takes the tie.
          avoid=("grow", "growing", "plant", "plants", "garden"), bias=1),
    entry("pesto-thick", (("pesto",), ("thick", "thickens", "stodgy", "dry", "claggy")),
          "Too thick: loosen it with a spoon of the water the pasta cooked in, or a squeeze of "
          "lemon, and taste again - the starch in pasta water binds it back to the basil instead of "
          "just thinning it out. Add more oil only at the end, a little at a time.",
          avoid=("grow", "growing", "plant", "plants", "garden"),
          # main's `fix-dry` is (dry x a food) with bias 1, and "my pesto is dry" matches both:
          # a thick pesto is loosened with pasta water, not with stock, so this takes the tie.
          bias=2),
    entry("pesto-thin", (("pesto",), ("thin", "runny", "watery", "soggy", "loose")),
          "Too runny: dry the basil properly after washing and blitz in more ground nuts and "
          "parmesan, a spoon at a time, rather than more oil, which is usually what made it sloppy "
          "in the first place. A soggy pesto is wet leaves, so spin them dry and start again.",
          # main's `fix-watery` is (watery x a food) with its own bias, and a runny pesto is fixed
          # with more nuts and cheese rather than with a roux: the narrower row takes the tie.
          avoid=("grow", "growing", "plant", "plants", "garden"), bias=2),
    entry("pesto-brown", (("pesto",), ("brown", "browns", "browned", "black", "dark")),
          "Brown pesto is the basil oxidising where the air reaches it, not spoilage: press it flat "
          "in the jar and cover the surface with a film of olive oil, and stir a squeeze of lemon "
          "through before you serve it. It is still good to eat for a few days if it was in the "
          "fridge and smells fine.",
          avoid=("grow", "growing", "plant", "plants", "garden"), bias=2),
    entry("pesto-freeze", (("pesto",), ("freeze", "freezing", "frozen", "freezer", "ice cube",
                                       "ice cubes", "make ahead", "day before")),
          "Pesto freezes better than it keeps: spoon it into an ice-cube tray, freeze it, tip the "
          "cubes into a bag, and drop one straight into hot pasta. In the fridge it is good for "
          "about a week, best with a film of olive oil over the surface.",
          # "can i freeze leftover pesto" reads as freeze-cooked's `leftovers`; the pesto is the
          # subject, so this one gets the nudge rather than freeze-cooked losing the word.
          bias=1),
    entry("pesto-nuts", (("pesto",), ("nut", "nuts", "allergy", "allergic", "pine", "pine nuts",
                                      "substitute", "instead", "swap")),
          "Pine nuts are the classic and sunflower seeds or cashews are the usual swap, about the "
          "same weight; toast whichever you use first, because raw seeds taste flat and pine nuts "
          "turn bitter once they are brown.",
          # "can i make pesto without pine nuts" is main's `pesto` recipe by its `make`, and the
          # question is about the nuts: the swap takes the tie.
          bias=1),
    entry("pesto-vegetarian", (("pesto",), ("vegetarian", "vegan", "parmesan", "cheese", "rennet",
                                            "dairy")),
          "Most shop pesto is not vegetarian: parmesan is made with animal rennet and jars "
          "usually use it. Buy one marked vegetarian, or make it with a vegetarian hard cheese, "
          "and leave the cheese out altogether for vegan.",
          # "is pesto ok for vegetarians" also carries "ok", which is one of jar-keep's keeping
          # words, so this needs the nudge to win that tie.
          bias=2),
    # Salt in a pesto is a cheese question, and it is asked both ways: how much to put in, and
    # what to do now that it has gone too salty. Main answered the first with the 6g-a-day salt
    # limit and the second with the stew advice to bulk it out with potatoes and stock.
    entry("pesto-salt", (("pesto",), ("salt", "salty", "too salty", "oversalted", "saltier",
                                         "seasoning", "seasoned")),
          "Pesto is saltier than it tastes because the parmesan and pecorino carry it, so add a "
          "pinch only after the cheese is in. If it has gone too salty, stir through more basil, "
          "ground nuts or a spoon of breadcrumbs and finish with a squeeze of lemon; more cheese "
          "only makes it worse.",
          # the fault words are the salt limit's and the stew answer's, and neither is a pesto:
          # "how much salt should i put in pesto" was the 6g-a-day line
          avoid=("grow", "growing", "plant", "plants", "garden", "blood pressure", "daily",
                 "too much salt in my diet"),
          bias=2),
    # A rusty tin is a safety question about the metal, and main answered it with how to line a
    # tin so the cake comes out whole. `loaf-tin` holds "rust" off already, so the line reaches
    # this row rather than the size answer.
    entry("rusty-cake-tin", (("cake tin", "cake tins", "baking tin", "loaf tin", "springform",
                              "sandwich tin", "traybake tin", "brownie tin"),
                             ("rusty", "rust", "rusted", "rusting")),
          "Surface rust is harmless: scrub it off with a green scourer, dry the tin, and line it "
          "with baking paper so the cake never touches the metal. Replace a tin that has rusted "
          "right through, or whose coating is flaking into the food.",
          # "a tin of tomatoes that went rusty" is not a thing, but a loose form of "rust" would
          # also catch "rustle" and the grow-your-own rows; the key is the tin's own names.
          avoid=("grow", "growing", "plant", "plants", "garden", "gate", "car", "bike"),
          bias=2),
    # The other half of every "how do i smoke ..." line is cooking, and the verb sent it to the
    # stop-smoking plan in science.py ("The most reliable way is nicotine replacement"). science's
    # smoking rows now stand down for a food, and this row answers the low-and-slow question, by
    # the thing being smoked, because the time and the heat are the whole answer.
    entry("smoke-meat",
          (("smoke", "smoking", "smoked", "smoker", "bbq", "barbecue", "barbeque", "low and slow",
            "wood chips", "pellet grill"),
           ("brisket", "ribs", "rib", "pork", "pulled pork", "shoulder", "chicken", "turkey",
            "wings", "sausage", "sausages", "salmon", "trout", "mackerel", "haddock", "fish",
            "cheese", "tofu", "beef", "steak", "lamb", "duck", "meat")),
          _smoke_food,
          # the habit, the alarm and the broken appliance are other rows' answers
          avoid=("quit", "stop smoking", "gave up", "give up", "nicotine", "cigarette",
                 "cigarettes", "vape", "vaping", "patch", "patches", "pack a day", "craving",
                 "smoke alarm", "smoke detector", "alarm", "detector", "carbon monoxide",
                 "chimney", "bonfire", "exhaust", "engine", "car", "diesel", "fireplace",
                 "wood burner", "log burner", "oven", "grill pan", "oil", "frying", "burnt",
                 "smells", "smelling", "smell", "smoky kitchen", "toaster"),
          # the line has to be asking how, not pricing: "is it cheaper to buy coffee in bulk"
          # after a brisket turn reached this row on the talk alone
          ask=("how", "what", "which", "temperature", "temp", "long", "time", "when", "recipe",
               "should i", "do i"),
          # "how long do i smoke a brisket for" also carries a time word, and the roast table
          # answers the time; this row has the heat as well as the time
          guard=_asks_about_a_smoker,
          bias=3),
]

# The same word, the other question. "How do I keep pasta from sticking" and "how do I keep the
# chicken moist" are about the pan, not the cupboard, and the keeping rows above own both "keep"
# and the food, so they answered with a date on a packet. The quality words are what tells the two
# apart, so every keeping row now holds them out and this entry takes the line: a food, a keeping
# word, and a quality the food is meant to have when it reaches the plate.
KEEP_HOW = ("keep", "keeps", "keeping", "stay", "stays", "stop", "stopping")

# The four qualities people want a dish to reach the plate with. They are the whole difference
# between the two questions that share the word "keep": "how long does pasta keep" is about the
# cupboard, "how do I keep pasta warm" is about the pan.
KEEP_QUALITIES = ("sticking", "stick", "sticks", "stuck", "together", "al dente",
                  "warm", "hot", "heated",
                  "moist", "juicy", "tender", "succulent",
                  "crisp", "crispy", "crunchy")

# The food the line names has to be the sort of food the answer is about: "keep" plus "warm" made
# a line out of "how do i keep my house warm" and out of "how do i keep warm in winter", so the
# food is read off the line and the entry passes when there is none.
_KEEP_FOOD = ("pasta", "spaghetti", "noodles", "noodle", "rice", "potato", "potatoes", "chips",
              "mash", "vegetables", "veg", "greens", "broccoli", "carrots", "beans", "peas",
              "meat", "steak", "beef", "chicken", "turkey", "pork", "lamb", "gammon", "ham",
              "sausage", "sausages", "bacon", "fish", "salmon", "cod", "prawns", "eggs",
              "pancakes", "soup", "stew", "curry", "casserole", "cakes", "cake", "bread",
              "pastry", "pasties", "buns", "joint", "roast", "breast", "thigh", "thighs",
              "chop", "chops", "cutlets", "wings", "halloumi", "tofu", "couscous", "squash",
              "paneer", "pilaf", "risotto", "pie", "pizza", "wedges",
              # The Sunday lunch is the meal people hold and the base had no word for half of
              # it: "how do i keep yorkshire puddings warm" was a search hedge, "how do i keep my
              # house warm" was the heating card, and "how do i keep gravy warm" was answered
              # with its fridge life - which is the other question that shares the word "keep".
              "yorkshire", "yorkshires", "yorkshire pudding", "yorkshire puddings",
              "stuffing", "gravy", "bread sauce", "cranberry sauce", "apple sauce",
              "burger", "burgers", "hot dog", "hot dogs", "sausage roll", "sausage rolls",
              "naan", "naans", "tortilla", "tortillas", "pitta", "pittas", "pita", "pitas",
              "chapatis", "mushey peas", "mushy peas", "dumplings", "pigs in blankets",
              "baguette", "baguettes", "ciabatta", "bagels", "cob", "cobs", "roll", "rolls")

# A cut with its own cooking row keeps it: "how do i keep chicken breast juicy" is answered by the
# breast (200C, 18 to 20 minutes, rest 5), and a whole turkey by the turkey. This entry takes the
# line only when the meat is named in general terms, which is when nothing else fits it.
_KEEP_MEAT = ("meat", "meats", "steak", "steaks", "mince", "joint", "chop", "chops", "thigh",
              "thighs", "wings", "cutlets", "ribs", "fillet", "loin", "stewing steak",
              # a sausage is not a joint: it has a roasting row of its own (200C, 25 to 30
              # minutes, turning once) and "slice across the grain" is nonsense for one
              "meatballs", "chicken")

# How the dish named in the line is held warm is the dish's own business: a plate of pasta is
# kept loose with its cooking water, a stack of pancakes is kept under a cloth in a low oven, and
# a tray of chips is kept uncovered in one layer. "how do i keep pancakes warm" used to get the
# pasta reply, pasta-water sentence and all.
_KEEP_GRAIN_WORDS = {"pasta", "spaghetti", "noodles", "noodle", "couscous"}
_KEEP_STACK_WORDS = {"pancakes", "cake", "cakes", "bread", "buns", "pastry", "pasties",
                     "waffles", "yorkshire", "yorkshires"}

# A flatbread is not a pancake: it goes in a cloth or foil, close together, where its own steam
# keeps it soft, and it dries out in the open.
_KEEP_FLATBREAD_WORDS = {"naan", "naans", "tortilla", "tortillas", "pitta", "pittas", "pita",
                         "pitas", "chapatis", "baguette", "baguettes", "ciabatta", "bagels",
                         "cob", "cobs", "roll", "rolls",
                         # a garlic baguette wants the foil and not the cloth: a tea towel leaves
                         # the crust soft
                         "garlic bread"}

# A jug is not a tray: gravy, custard and a sauce are held in the jug over water, because they
# set and skin when they are left on a ring, and a poured sauce cannot be spread out in one layer.
_KEEP_POUR_WORDS = {"gravy", "bread sauce", "cranberry sauce", "apple sauce", "custard",
                    "onion gravy", "jus"}

# Anything that is served in a heap and dries out rather than steams: stuffing, burgers, sausages
# in a roll. It wants the low oven, covered, with a splash of water in the bottom.
_KEEP_COVERED_WORDS = {"stuffing", "burgers", "burger", "hot dogs", "hot dog", "sausage rolls",
                       "sausage roll", "pigs in blankets", "dumplings", "meatballs"}
_KEEP_CRISP_HELD_WORDS = {"potatoes", "potato", "chips", "wedges", "mash"}

_KEEP_STICK_WORDS = {"sticking", "stick", "sticks", "stuck", "together", "al dente"}
_KEEP_HOT_WORDS = {"warm", "hot", "heated"}
_KEEP_SOFT_WORDS = {"moist", "juicy", "tender", "succulent"}

# What sticking together is, and what it is not. A pan of boiling water is where things clump -
# pasta, potatoes, noodles - so stirring them in and keeping the water moving is the answer. A
# batter or a bake in a tin never sits in water: "how do i stop pancakes sticking" and "how do i
# stop pastry sticking to the tin" were told to stir them once and keep the water at a rolling
# boil, which is a pot of pasta's answer. The food has to be one that boils for this row to speak,
# and a bake or a batter with its own row answers its own sticking.
_KEEP_BOILED = ("pasta", "spaghetti", "noodles", "noodle", "potato", "potatoes", "chips",
                "vegetables", "veg", "greens", "broccoli", "carrots", "beans", "peas",
                "dumplings", "gnocchi", "couscous")


def _keep_how(memory, reading):
    """How to keep a dish the way it should be, read off the quality the line asks for.

    Passes when the line names no quality, no food, or no meat for a juiciness answer, so the
    entry below it gets its turn: a cake kept moist is a tin and a fridge, not a pan and a rest.
    """
    words = set(reading.get("words") or ())
    if not words.intersection(KEEP_QUALITIES) or not words.intersection(_KEEP_FOOD):
        return None
    if words & _KEEP_STICK_WORDS:
        # The grain has a row of its own for this one - rinse it, soak it, the water ratio - and
        # a rice line about sticking is that row's, not this entry's.
        if "rice" in words:
            return None
        if not words.intersection(_KEEP_BOILED):
            # a bake in a tin, a batter in a pan or a tray of food does not sit in water: pass, so
            # the row that knows the thing can answer how to stop it sticking
            return None
        return ("Stir it once as it goes in and once more a minute later, keep the water at a "
                "rolling boil with room for the pieces to move, and lift it out with tongs or a "
                "spider rather than tipping it into a colander. Oil in the water does nothing - "
                "it floats - but a splash of oil through it after draining stops it setting into "
                "one lump.")
    if words & _KEEP_HOT_WORDS:
        # the words are single tokens, so a dish with two words in its name is joined here
        if {"garlic", "bread"} <= words:
            words = words | {"garlic bread"}
        # Rice is the awkward one of the hot dishes and has an answer of its own: a pan of rice
        # held over more heat dries out and catches, so it is the lid and the cloth that keep it
        # warm, and rice standing warm is the food-safety case nobody thinks about.
        if "rice" in words:
            return ("Lid on and off the heat, with a folded tea towel over the pan under the lid: "
                    "rice holds warm that way for 20 to 30 minutes, and an hour or two in a "
                    "covered dish in an oven on 80C with a splash of water is the limit. That "
                    "limit is not fussiness - cooked rice left standing warm grows bacillus "
                    "cereus, so past two hours cool it fast and reheat it once, thoroughly.")
        held = ("Hold it hot rather than hotting it up later: an oven on its lowest, a slow "
                "cooker on low, or a bowl over a pan of simmering water, all covered, which keeps "
                "food above 63C where bacteria stop multiplying. ")
        if words & _KEEP_GRAIN_WORDS:
            return held + ("Keep back a cup of the cooking water and stir it through so nothing "
                           "sets into a block, and do not leave it warm for more than an hour or "
                           "two.")
        if words & _KEEP_POUR_WORDS:
            # the poured ones are answered on their own: the general hold-it-hot sentence names a
            # pan of simmering water, and saying that twice in one reply is not an answer
            return ("Stand the jug in a pan of simmering water on the lowest ring, or pour it "
                    "into a flask, and give it a stir every so often: a sauce left on the hob "
                    "catches, and one left standing still grows a skin. Loose it with a splash of "
                    "stock or milk before it goes out, and an hour or two is as long as it holds.")
        if words & _KEEP_COVERED_WORDS:
            return ("A covered dish in the oven on its lowest, with a splash of stock "
                    "or water in the bottom so the edges do not dry: in one layer rather than "
                    "piled up, and uncovered if it is meant to stay crusty. An hour or two is "
                    "the limit - after that it is a leftover, and a leftover is cooled fast and "
                    "reheated once.")
        if words & _KEEP_FLATBREAD_WORDS:
            return ("Keep them wrapped and close together - a clean tea towel or foil - in the "
                    "low oven, or give each one a minute a side in a warm dry pan. A lid or a "
                    "covered dish steams a flatbread soft, and it dries out in the open, so ten "
                    "to fifteen minutes in the cloth is all it needs.")
        if words & _KEEP_STACK_WORDS:
            return held + ("Stack them on a plate under a clean tea towel, rather than under a "
                           "lid or foil, which traps the steam and leaves them limp, and do not "
                           "hold them warm for more than an hour or two.")
        if words & _KEEP_CRISP_HELD_WORDS:
            return held + ("One layer on a tray, uncovered, not piled in a bowl where they "
                           "steam and go soft, and do not leave them warm for more than an hour "
                           "or two.")
        return held + ("Cover it and do not leave it warm for more than an hour or two.")
    if words & _KEEP_SOFT_WORDS:
        if not words.intersection(_KEEP_MEAT):
            return None                 # a moist cake is a tin and a fridge, not a pan and a rest
        return ("Juiciness is decided before the pan and lost at the end: salt the meat 40 "
                "minutes ahead or soak it in brine, cook it to 74C in the middle for chicken and "
                "pork (54C for beef you want pink), and rest it under loose foil for 10 minutes "
                "so the juices settle back into the fibres. Then slice across the grain, not "
                "along it.")
    return ("Crisp survives only in the open: cool anything fried or roasted in one layer on a "
            "rack or a paper-lined tray, never in a pile or a closed tub, where the steam turns it "
            "soft within minutes. Then reheat it 4 to 5 minutes at 200C on a bare tray, not in a "
            "microwave. A dry surface before it goes in the fat is the other half of it.")


# ask= the qualities, because two of the three parts of the key are not enough on their own: the
# sentence above reads the rest off the line and passes. bias=-1 keeps the food's own cooking row
# ahead of it wherever both fit ("keep the beef tender" still gets the beef times).
ENTRIES.append(entry("keep-how", (KEEP_HOW, KEEP_QUALITIES, _FOOD), _keep_how, bias=-1,
                     ask=KEEP_QUALITIES,
                     avoid=("party", "parties", "buffet", "guests", "for a crowd",
                            "how long", "how many", "recipe", "recipes", "fridge",
                            "freezer", "freeze", "next day", "tomorrow", "reheat",
                            # a salad leaf stays crisp in the fridge, so crispness is the
                            # keeping question for it and the pan answer is not
                            "lettuce", "salad", "leaves", "spinach", "rocket", "watercress",
                            "celery", "cucumber", "cabbage", "herb", "herbs",
                            # a pan that will not let go, a grain with its own water rule, and a
                            # cut or a bird with its own cooking row, are all answered already
                            "pan", "pans", "wok", "tray", "risotto", "porridge",
                            "quinoa", "breast", "breasts", "turkey", "beef", "pork", "lamb",
                            "salmon", "cod", "fish", "prawns", "bacon", "cake",
                            # "bread" was held out here so that a keeping question about it
                            # stayed with its own row, and that took "how do i keep garlic bread
                            # warm" with it: the stack under a tea towel is right for a loaf, a
                            # naan and a garlic baguette alike, so the word is allowed through
                            # and a bread that wants to stay moist still passes below
                            )))


# Ribs are the same cut as belly pork and a different question: "how do i cook ribs" was the
# beginner's card ("learn four things and the rest follows") because the pantry lists the meat
# under "pork belly" and nothing answered the cooking of it, and "how long do ribs take in the
# oven" was reaching the revision card on "long" and "take". The times are the whole answer, so
# the row keys the cut and asks for the cooking words.
ENTRIES.append(entry(
    "ribs-low-and-slow",
    (("ribs", "rib", "spare ribs", "short ribs", "pork ribs", "baby back ribs", "beef ribs",
      "pork rib"),
     ("cook", "cooking", "oven", "bake", "baked", "roast", "roasted", "slow cooker",
      "slow-cooker", "crockpot", "crock pot", "tender", "long", "time", "temperature", "temp",
      "how", "glaze", "glazed", "fall off the bone")),
    ("Ribs want low and slow: 2 to 2.5 hours covered at 150C (130C fan) with a splash of water "
     "in the tray, then 15 minutes uncovered at 220C (200C fan) with a glaze to sticky them up. "
     "In a slow cooker it is 6 to 8 hours on low, then 10 minutes under the grill. They are done "
     "when the meat has pulled back from the bone and a fork twists in it easily."),
    # the smoker has its own heat and its own times, and a line that says smoke or smoker is
    # that row's; a barbecue is the same ribs on the same grill, so "bbq ribs in the oven" and
    # "how do i cook ribs on the bbq" keep this row's times
    avoid=("smoke", "smoked", "smoking", "smoker", "low and slow", "wood chips", "pellet grill",
           # "i cooked" and "i made" cannot go here: the avoid test is typo-tolerant, and "cooked"
           # is two letters from the "cook" this row keys
           "last night", "yesterday", "we had", "we ate", "turned out", "came out",
           # a rib in the body is the sore-ribs answer, and a prime rib or a ribeye is a steak
           "hurt", "hurts", "hurting", "pain", "ache", "aches", "breathing", "breathe", "cough",
           "bruise", "bruised", "broken", "cracked", "cage", "x ray", "x-ray",
           "prime rib", "ribeye", "rib eye", "rib cap", "ribs recipe for a crowd",
           # the price, the reheat and last night's dinner are other rows' answers
           "how much", "cost", "costs", "price", "prices", "cheap", "expensive", "afford",
           "reheat", "reheating", "reheated", "leftover", "leftovers", "warm up", "warmed up",
           "microwave", "air fryer", "freeze", "freezer", "frozen"),
    # no ask= here: "slow cooker ribs" is how people ask this, and it reaches the kitchen as a
    # statement. The two key parts are enough, and the bias keeps the row behind a dish's own
    bias=2))


# "Do I need to prick sausages" was a shrug, and the one place the bot mentioned pricking said to
# do it ("Prick them and cook them gently so the skins do not split"), which is the older advice
# and the wrong one: a pricked sausage leaks its fat and juice into the pan. The question is not
# the cooking time - that row has 20 minutes at 190C for a thick one - so this row keys the
# pricking itself and answers it.
ENTRIES.append(entry(
    "prick-sausages",
    (("sausage", "sausages", "banger", "bangers", "chipolata", "chipolatas", "bratwurst",
      "frankfurter", "frankfurters", "hot dog", "hot dogs"),
     ("prick", "pricked", "pricking", "prick them", "pierce", "pierced", "stab", "stabbed",
      "split", "splits", "splitting", "burst", "bursts", "bursting", "skin", "skins")),
    ("No - leave them whole. Pricking lets the fat and juice run out into the pan, so they come "
     "out drier, and it is fast high heat that splits a skin, not a skin that went unpricked: "
     "cook them at 180C (160C fan) for 25 to 30 minutes, or in a pan on a medium heat, turning "
     "them now and then, and let them colour slowly. A thick one that splits anyway is still "
     "fine to eat - it has just tightened faster than the inside cooked."),
    # the cooking time, the keeping and the price are other rows' answers, and the prick of a
    # finger or an injection is a different word's question
    avoid=("how long", "minutes", "how many", "calories", "healthy", "freeze", "freezer",
           "fridge", "keep", "reheat", "how much", "cost", "price", "recipe", "make my own",
           "finger", "thumb", "injection", "vaccine", "blood", "diabetes", "glucose"),
    bias=2))

# --- what went wrong in the pan ---------------------------------------------
# A line that says a dish did not work ("the jelly didnt set", "my omelette stuck") names a fault,
# not a how-to, and the word it shares with a neighbour is what pulled it away: "jelly" went to the
# jam-setting answer, "stuck" to the burnt-pan cleaning one, "peas" to the runner-bean strings.
# These four rows key the dish AND the fault, so they answer the accident and leave the how-to,
# the cleaning and the growing to the rows that own them.
ENTRIES.append(entry(
    "jelly-wont-set",
    (("jelly", "jello", "gelatine", "gelatin", "blancmange"),
     ("set", "sets", "setting", "didnt set", "wont set", "wont", "runny", "liquid", "firm",
      "wobbly", "solid", "why", "how much", "how many", "leaves", "powder")),
    ("Jelly is measured by liquid: 4 leaves of gelatine, or 2 teaspoons of powder, to every pint "
     "(570ml), then 4 hours in the fridge - overnight to be sure. Fresh pineapple, kiwi, papaya, "
     "mango and figs have an enzyme that stops gelatine setting, so simmer those for 2 minutes "
     "first or the jelly stays liquid. Still runny after that? Melt it gently and stir in one more "
     "leaf per pint."),
    # "bramble jelly" and "crab apple jelly" are jam, and jam sets at 104C by sugar and pectin:
    # that is the jam row's answer, and a leaf of gelatine is no help with it
    avoid=("jam", "marmalade", "setting point", "104", "105", "pectin", "boil", "boiling",
           "bramble", "blackberry", "blackberries", "crab apple", "rowan", "quince", "damson",
           "sloe", "sloes", "redcurrant", "red currant", "gooseberry", "elderflower", "cranberry",
           "mint jelly", "apple jelly", "sugar", "thermometer", "preserve", "preserves", "chutney",
           "how long does jelly keep", "keep", "keeps", "fridge life", "sweets", "candy",
           "royal jelly", "jellyfish", "jelly bean", "jelly shoes"),
    bias=2))

ENTRIES.append(entry(
    "peas-that-stay-hard",
    (("peas", "pea", "marrowfat", "garden peas", "frozen peas", "split peas"),
     ("hard", "tough", "woody", "wont soften", "wont go soft", "still hard", "not soft",
      "crunchy", "chalky", "like bullets", "bitter", "old")),
    ("Peas that stay hard are usually old: the sugar has turned to starch and no amount of cooking "
     "brings them back. Frozen garden peas need 2 to 3 minutes in boiling water, fresh ones 3 to 5. "
     "Marrowfat and other big dried peas want a soak overnight and 40 minutes of simmering, and a "
     "quarter teaspoon of bicarbonate of soda in the water helps them soften. Acid is the other "
     "culprit - lemon juice or tomatoes in the pan keep peas firm - so add those at the end."),
    # a runner bean that is stringy is a bean, not a pea, and the strings answer is that row's;
    # a pea in the garden is a seed to sow and a sweet pea is a flower
    avoid=("runner", "runners", "bean", "beans", "string", "stringy", "strings", "de-string",
           "sow", "sowing", "plant", "planting", "grow", "growing", "allotment", "climbing",
           "sweet pea", "sweet peas", "flower", "seed", "seeds", "germinate", "sprout",
           "protein", "calories", "healthy", "nutrition"),
    bias=2))

ENTRIES.append(entry(
    "bread-machine-loaf-failed",
    (("bread machine", "breadmaker", "bread maker", "bread-mixer", "dough hook"),
     ("failed", "fail", "didnt work", "not working", "brick", "flat", "sank", "dense", "heavy",
      "no rise", "didnt rise", "collapsed", "stodgy", "raw", "sunken")),
    ("A brick out of a bread machine is nearly always the yeast: check the date, keep it and the "
     "salt apart in the tin (salt kills yeast on contact), and use water at 20 to 25C, because hot "
     "water kills it just as well. Half a teaspoon of dried yeast to 500g of strong white flour is "
     "the other thing to check. If the dough never rose the yeast is dead; if it rose and then "
     "fell, there was too much of it or the salt went in with it."),
    # the oven running cold is the oven's own answer, and a loaf in a tin or by hand is the
    # bread-baking row's
    avoid=("oven temperature", "oven thermometer", "fan oven", "temperature of the oven",
           "by hand", "by-hand", "sourdough", "knead", "kneading", "flour", "which flour",
           "recipe", "buy", "which machine", "best machine", "worth it", "cost", "price",
           "clean", "cleaning", "paddle", "pan stuck"),
    bias=2))
# A cup or a bowl that goes cold is one question, and three cards were taking it: the streak card
# ("why does my tea keep going cold" was told "the rule that keeps a habit alive is never miss
# twice"), the cold-and-flu card ("my soup keeps going cold" got "a cold usually peaks in two or
# three days"), and the tea shelf-life card ("how do i keep my tea hot" was told tea does not go
# off, it goes stale). What they all want is the one thing that actually keeps a drink hot, so
# that is what this answers, and the words for it are the temperature words and not "keep".
COLD_CUP_NAMES = ("tea", "coffee", "soup", "broth", "stew", "gravy", "porridge", "hot chocolate",
                  "cuppa", "brew", "drink", "dinner", "food", "plate", "mug", "cup", "pot")

COLD_CUP_ASKS = ("going cold", "goes cold", "gone cold", "keeps going cold", "keeps cold",
                 "keep going cold", "cold before", "lukewarm", "gone lukewarm", "stone cold",
                 "keep it hot", "keep hot", "keeps it hot", "keep my tea hot", "keep tea hot",
                 "keep my coffee hot", "keep the soup hot", "keep soup hot", "stays hot",
                 "stay hot", "staying hot", "goes warm", "gone warm",
                 # "can i reheat soup" and "can i reheat coffee" are the food-safety and the
                 # coffee cards' questions, and a bare "reheat" here took both: five reheat
                 # lines got "warm the cup" instead of "reheat it until it is piping hot".
                 # Reheating already-made food is not keeping a fresh cup warm, so the word
                 # stands this row down rather than keying it.
                 # a cup kept warm is the same question said the other way round: "how do i keep
                 # my coffee warm at work" was a search hedge on main
                 "keep it warm", "keep warm", "keeps warm", "keep my tea warm", "keep tea warm",
                 "keep my coffee warm", "keep coffee warm", "keep the soup warm", "stays warm",
                 "stay warm", "staying warm",
                 "warm it up", "warm it back up", "cold by the time")

ENTRIES.append(
    entry("a-cup-going-cold", (COLD_CUP_NAMES, COLD_CUP_ASKS),
          "Warm the cup or the bowl first: fill it with boiling water, leave it a minute, tip it "
          "out and then fill up, because a cold mug takes most of the heat out in the first "
          "minute. A lid or a tea cosy keeps a drink hot far longer than a bigger pot does, and a "
          "flask is the only thing that holds it for hours, so make a smaller pot and top it up. "
          "For soup, a deeper bowl keeps the heat in better than a wide shallow one, and warming "
          "the bowls with hot water before you serve buys another few minutes.",
          ask=COLD_CUP_ASKS,
          # what a cold is, how long a virus lasts and whether soup helps are other cards, and a
          # cup already in the fridge is a keeping question
          avoid=("i have a cold", "have a cold", "my cold", "a bad cold", "head cold", "chesty",
                 "sore throat", "runny nose", "cough", "coughing", "sneez", "flu", "temperature",
                 "fever", "virus", "symptom", "day of work", "fridge", "freezer", "frozen",
                 "ice", "iced", "cold brew", "ice cream", "cold sore", "cold water", "recipe",
                 "how do i make", "how do you make", "kettle", "coffee machine", "brew time",
                 "reheat", "reheating", "reheat it", "warm up the leftover", "leftovers"),
          bias=3))

# --- the same dish in the pot you actually have ------------------------------
# A rice pudding is a baked dish, a slow cooker job or a microwave one, and the time and the milk
# change with the pot. The person who names the pot wants that pot's numbers, and on main all of
# these were other answers: "rice pudding in the slow cooker" was banana pancakes (the fence that
# keeps a recipe row off an appliance line stood the pudding's own method down), and "how do i
# make rice pudding in the microwave" was the reheat card. The dish row keys the dish and the
# pot, and a dish that is made more than one way says which way in its reply.
_RICE_PUDDING_SLOW = (
    "3 to 4 hours on low. Butter the slow cooker pot and put in 60g pudding rice, 700ml whole "
    "milk, 100ml cream, 40g sugar and a strip of lemon peel or a bay leaf: the extra milk is "
    "there because nothing evaporates in a slow cooker. Stir once after an hour and then leave "
    "the lid on, because lifting it drops the heat. Take the lid off for the last 30 minutes if "
    "you want the top to catch, and loosen it with milk before it goes into bowls.")
_RICE_PUDDING_MICROWAVE = (
    "About 25 minutes. Use a big bowl, because it swells and boils up, and put in 60g pudding "
    "rice, 600ml whole milk, 40g sugar and a strip of lemon peel. Microwave on high for 10 "
    "minutes, stir, then 8 minutes, stir, then 5 minutes at a time until the rice is soft. It "
    "carries on cooking as it stands, so stop while it is still a little loose, and finish it "
    "under the grill if you want a browned top.")
_RICE_PUDDING_PRESSURE = (
    "20 minutes on high pressure with a 10 minute natural release: 60g pudding rice, 600ml whole "
    "milk, 40g sugar and a strip of lemon peel in a dish on a trivet over water. Do not fill the "
    "pot more than half way, because milk froths up through the valve. Loosen it with milk once "
    "the pressure is down, and grill the top if you want it browned.")


def _rice_pudding_pot(memory, reading):
    """The pot the line named, worded for that pot."""
    said = str(reading.get("clean") or " ".join(reading.get("words") or [])).lower()
    if any(one in said for one in ("pressure cooker", "instant pot", "multicooker")):
        return _RICE_PUDDING_PRESSURE
    if any(one in said for one in ("microwave", "microwaved", "microwaving")):
        return _RICE_PUDDING_MICROWAVE
    return _RICE_PUDDING_SLOW


ENTRIES.append(entry(
    "rice-pudding-pot",
    (("rice pudding", "rice puddings"),
     ("slow cooker", "slowcooker", "slow-cooker", "crockpot", "crock pot", "microwave",
      "microwaved", "microwaving", "pressure cooker", "instant pot", "multicooker")),
    _rice_pudding_pot,
    # a pudding already made is the keeping, reheating or portion answer, and a pudding wanted
    # without something is the swap's
    avoid=("keep", "keeps", "keeping", "last", "lasts", "reheat", "reheating", "leftover",
           "leftovers", "shelf life", "gone off", "stale", "calories", "how much", "how many",
           "without", "vegan", "dairy free", "tin", "tinned", "shop", "buy", "rice cake",
           "rice cakes", "rice crispy", "rice crispies", "already made", "shop bought"),
    # the plain "how do i make rice pudding" belongs to the dish's own method, and this row is
    # only for the pot named in the line
    ask=("slow cooker", "slowcooker", "slow-cooker", "crockpot", "crock pot", "microwave",
         "microwaved", "microwaving", "pressure cooker", "instant pot", "multicooker"),
    bias=2))
# --- is this food vegetarian? ------------------------------------------------
# The everyday ask in this family is a yes-or-no about one named food, and main answered it with a
# shrug ("is a croissant vegetarian", "is gelatin vegetarian") or, worse, with a recipe: "is
# parmesan vegetarian" got the cheese toastie and "are chips vegetarian" got the leftover-chips
# fix. The answer belongs to the food, not to the asking, so each row below is the food plus the
# diet word and the verdict is the one thing the packet does not tell you: the rennet, the
# gelatin, the anchovy, the dripping. A food not in the table is the general row's, which says
# what to read on a label.
_VEGETARIAN_FOODS = (
    (("parmesan", "parmesan cheese", "grana padano", "pecorino", "pecorino romano"),
     "Probably not: Parmesan, Grana Padano and Pecorino are set with animal rennet, which comes "
     "from the stomach of a calf or a lamb, so the traditional ones are not vegetarian. Some "
     "supermarket versions use microbial rennet instead - the ingredient list or the Vegetarian "
     "Society logo is the only way to tell."),
    (("gelatin", "gelatine", "jelly", "jelly cubes", "marshmallow", "marshmallows", "haribo",
      "gummy sweets", "gummy bears", "gummies", "wine gums", "jelly babies", "chewy sweets"),
     "Not if the packet says gelatin or gelatine: that is made from pork or beef skin and bone, so "
     "jelly, marshmallows, jelly babies and most gummy sweets are out. The vegetarian versions set "
     "with pectin, agar or carrageenan instead, and they say so on the front."),
    (("worcestershire sauce", "worcester sauce", "worcestershire"),
     "Not the ordinary Lea & Perrins: Worcestershire sauce is made with anchovies, so it is "
     "neither vegetarian nor vegan. Anchovy-free versions exist, and a splash of soy sauce or "
     "balsamic does the same job in a stew or a cheese on toast."),
    (("caesar dressing", "caesar salad", "caesar"),
     "No, not a classic one: Caesar dressing has anchovies and Parmesan, so the dressing and the "
     "salad with it are not vegetarian. Vegetarian versions swap the anchovy for capers and use a "
     "hard cheese made with microbial rennet."),
    (("pesto", "green pesto", "pesto sauce"),
     "Usually not: jarred pesto is made with Parmesan or Pecorino, and both are set with animal "
     "rennet. Look for one labelled vegetarian, or make it with a vegetarian hard cheese - the "
     "basil, pine nuts, garlic and oil are all fine."),
    (("chips", "fries", "chip shop chips", "french fries"),
     "Usually yes - potatoes and oil - but chip-shop chips can be fried in beef dripping, which is "
     "traditional in the north, and a shop that fries them in the same oil as the fish is a no for "
     "some people. Ask, or use oven chips and read the packet."),
    (("croissant", "croissants", "pastry", "pastries", "danish", "pain au chocolat",
      "puff pastry", "shortcrust"),
     "Yes: a croissant is flour, butter, yeast, sugar and egg, all of which are vegetarian, though "
     "not vegan. Ordinary pastry is vegetarian too, with one exception - some savoury pie pastry "
     "still lists lard, so read the packet before you assume."),
    (("stock cube", "stock cubes", "stock", "gravy", "gravy granules", "bouillon"),
     "Read the packet: plenty of chicken and beef stock cubes are actually vegetarian, and plenty "
     "of 'vegetable' gravies have meat fat in them. The vegetarian ones are labelled, and a "
     "vegetable stock cube with a dash of soy sauce covers the same ground."),
    # Feta and halloumi are asked about on their own and the answer for each is different from
    # "most cheese is fine", so they keep a row each side of the general one.
    (("feta", "feta cheese"),
     "Usually yes: most supermarket feta is made with microbial rennet and says so on the back, "
     "while the traditional barrel-aged Greek and Bulgarian sorts use animal rennet, so read the "
     "label before you count on it."),
    (("halloumi", "halloumi cheese"),
     "Often not: most halloumi is made with animal rennet, so look for vegetarian on the packet or "
     "the Vegetarian Society logo. The vegetarian versions grill and squeak the same way."),
    (("cheese", "cheddar", "mozzarella", "brie", "cottage cheese", "cream cheese"),
     "Most cheese is fine, but the hard ones - Parmesan, Grana Padano, Pecorino, and some "
     "traditional cheddars - are set with animal rennet. Cheddar, mozzarella and cottage cheese "
     "are usually made with microbial rennet, and the Vegetarian Society logo settles it."),
    (("wine", "beer", "cider", "ale", "lager", "stout"),
     "It may not be, technically: wine and beer are often fined with isinglass from fish swim "
     "bladders, gelatin or egg white, and the fining agent never appears on the label. Most "
     "supermarket bottles now print 'suitable for vegetarians', so buy one that does."),
    (("rice", "pasta", "bread", "noodles", "flour", "potatoes"),
     "Yes: rice, pasta, noodles, flour and potatoes are vegetarian, and bread almost always is - "
     "the exception is lard in some traditional loaves. Egg pasta is still vegetarian, it is only "
     "vegan that rules it out."),
    (("chocolate", "milk chocolate", "dark chocolate"),
     "Usually yes: cocoa, milk and cocoa butter are all vegetarian. Check the bar for gelatin in "
     "chewy or marshmallow fillings, and remember whey is fine for a vegetarian but not for a "
     "vegan."),
)
# The diet word and the food are two signals, and the vegetarian-plan row in dishes.py reads
# "are chips vegetarian" as a request for a dinner, scores higher on the carrier "are", and then
# declines for lack of a cooking context, so the line fell through to the shrug. The asking shape
# is the third signal, and it is what makes the line a question about the food rather than a plan.
_VEG_SHAPE = ("is", "are", "was", "were", "ok", "okay", "suitable", "can i eat", "can i have",
              "can i", "does", "do", "safe", "fine", "allowed", "eat", "edible")
for _names, _verdict in _VEGETARIAN_FOODS:
    ENTRIES.append(entry("is-veg-" + _names[0].replace(" ", "-"), (_names, _VEG_SHAPE), _verdict,
                         # The vegetarian-plan row in dishes.py scores one higher on the carrier
                         # alone ("are chips vegetarian" is a plan to it), so it has to be beaten
                         # on points; its own `_veggie` then declines for lack of a cooking
                         # context and the line used to reach the shrug.
                         ask=("vegetarian", "veggie"), bias=2))


# The open version of the same question: "how do i know if something is vegetarian", "what should
# i look for on the label". The list is the hidden ingredients, because the visible ones are
# obvious and these are the ones people miss.
ENTRIES.append(entry(
    "vegetarian-label",
    (("vegetarian", "veggie"),
     ("how do i know", "how can i tell", "how to tell", "check", "checking", "label", "labels",
      "look for", "look out", "watch out", "ingredients", "hidden", "sure", "certain", "find out",
      "what to look", "packet", "packets")),
    ("Read the ingredient list for the four that catch people out: rennet (animal, in hard cheese), "
     "gelatin (pork or beef, in sweets and jelly), anchovy (Worcestershire sauce, Caesar dressing) "
     "and lard or suet (pastry, some bread). The Vegetarian Society logo, a green V or the words "
     "'suitable for vegetarians' settle it faster than any list, and 'may contain fish' means the "
     "same fryer or the same factory rather than an ingredient."),
    # a plan question is not this one: "im vegetarian, what can i cook" is the dinner row's
    avoid=("dinner", "tea", "lunch", "breakfast", "meal", "meals", "cook", "cooking", "recipe",
           "recipes", "ideas", "restaurant", "menu", "protein", "iron", "b12", "child",
           "children", "kids", "guest", "guests", "party", "cut down", "going vegetarian",
           "become", "start being", "im vegetarian", "i am vegetarian"),
    bias=1))

# "How do i tenderise cheap steak" had no row, and "how do i make steak tender" reached the
# keep-it-juicy card, which is about not overcooking it. A cheap cut is a different method:
# salt, acid, time and the way you cut it.
ENTRIES.append(entry(
    "tenderise-cheap-meat",
    (("tenderise", "tenderize", "tenderising", "tenderizing", "tenderise it", "tender",
      "tough steak", "tough meat", "cheap cut", "cheap steak", "cheap meat",
      # The cut is "skirt steak", never the bare word: the word forms strip "-ing", so a bare
      # "skirt" in the key made "how do i dust skirting boards" a plain steak question and it was
      # answered with salt, acid and slicing. The boards are fenced below as well, for the line
      # that also says "chewy" or "tough" about something else in the room.
      "skirt steak", "skirt steaks", "flank", "chewy"),
     ("how do i", "how to", "make", "makes", "make it", "best way", "stop it being", "too tough",
      "chewy", "softer", "soften", "marinade", "marinate", "salt")),
    ("Salt it an hour ahead - a good pinch per side, left uncovered in the fridge - or marinate it "
     "30 minutes to an hour in something acidic: lemon juice, wine, buttermilk or yoghurt. Then "
     "cut across the grain in thin slices, which does more for a chewy steak than any marinade, "
     "and cook it fast over high heat to no more than medium, or braise it slowly for hours if it "
     "is a stewing cut like shin, chuck or brisket. A bash with a rolling pin between two sheets "
     "of baking paper works for thin cuts like flank and skirt."),
    # the cook-it timetable, the roasting time and the resting are other cards
    # The plain cook-it question keeps the steak card's sear timetable.
    # A cut named for a long cook is the braise card's, not this one: "i have stewing steak and a
    # slow cooker" wants the three hours at 150C, and the salt-and-slice answer here is the wrong
    # method for it - the next turn of that chat went back to the brisket card, so turn one was
    # contradicting turn two. The cuts went out of the key and into this fence for the same reason.
    avoid=("how long", "medium rare", "rare", "temperature", "sear", "searing", "pan", "grill",
           "barbecue", "bbq", "oven", "roast", "rest", "resting", "freezer", "frozen",
           "thaw", "defrost", "keep", "leftover", "leftovers",
           "slow cooker", "slow cook", "slow cooked", "slow cooking", "casserole", "stew",
           "stews", "stewing", "braise", "braised", "braising", "brisket", "shin", "chuck",
           "oxtail", "pot roast", "pressure cooker", "air fryer",
           "how do i cook", "how do i cook it", "cook a steak", "cooking a steak",
           "cook the steak", "cook my steak", "fry a steak", "frying a steak",
           # "skirting" folds to "skirt", so "how do i paint the skirting" reached this card
           # and was told to salt it and cut across the grain. The paint rows answer it.
           "skirting", "skirting board", "skirting boards", "skirt board", "skirt boards",
           "paint", "paints", "painting", "repaint", "painted", "gloss", "satin", "emulsion",
           "undercoat", "woodwork", "primer"),
    bias=1))

# The kitchen says what it has not got, and the rest of the base answers as if it had it. Every
# appliance-lack answer exists already (`without()` in cooking.py picks between the hob-only
# meals, the no-bake cake and the kettle-only supper), but it was only ever reached when nothing
# else matched, so a dish row answered first and talked the person through a bake in an oven they
# had just said they had not got: "can i bake a cake with no oven" was "A 20cm sponge bakes at
# 180C...", "can i bake bread without an oven" the three-hour loaf. The row below is that answer
# with the words people say the lack with, and it stands down (returns None) whenever
# `without()` has nothing to say, so a line that names a missing microwave in the middle of
# something else keeps the row it had.
NO_APPLIANCE = ("no oven", "without an oven", "without the oven", "dont have an oven",
                "don't have an oven", "havent got an oven", "haven't got an oven",
                "got no oven", "no hob", "without a hob", "dont have a hob",
                "don't have a hob", "havent got a hob", "haven't got a hob",
                "no microwave", "without a microwave", "dont have a microwave",
                "don't have a microwave", "havent got a microwave", "haven't got a microwave",
                "no cooker", "without a cooker", "dont have a cooker", "don't have a cooker",
                "only got a hob", "only have a hob", "only a hob", "just a hob",
                "only got a microwave", "only have a microwave", "only a microwave",
                "just a microwave", "only got a kettle", "only have a kettle", "only a kettle",
                "just a kettle", "no oven tho", "no oven though", "oven broke", "oven is broken",
                "oven doesnt work", "oven doesn't work", "oven not working", "oven is gone",
                "no oven in", "hob broke", "hob is broken", "hob doesnt work",
                "hob doesn't work", "hob not working")


def _no_appliance(memory, understood):
    """The answer for a kitchen missing an appliance, or None when the line is about something else."""
    if not isinstance(understood, dict):
        return None
    gone = missing(understood)
    if not gone:
        return None
    # a decision about the appliance is the money rule's, and a fault report is the repair row's
    said = _line(understood)
    if any(re.search(r"\b" + re.escape(word) + r"\b", said) for word in DECIDING):
        return None
    # The list has just been given, so the second ask is the same list again, and that is the
    # repeat path's line: answering it here cut the answer down to its closing tail ("Eggs,
    # tinned fish and beans all cook in a pan in minutes") instead of "Same as before: ...".

    from ..memory import last_bot

    before = str(last_bot(memory) or "").lower()
    if any(came in before for came in ("you cannot bake without an oven", "you can still eat well",
                                       "you can still eat properly", "a kettle still makes",
                                       "with an oven and no hob")):
        return None
    return without(understood)


ENTRIES.append(entry(
    "kitchen-without-an-appliance",
    (NO_APPLIANCE, ("bake", "baking", "cook", "cooking", "make", "eat", "dinner", "tea",
                    "meal", "meals", "cake", "cakes", "bread", "loaf", "biscuit", "biscuits",
                    "cookie", "cookies", "roast", "pie", "pastry", "what can i", "what should i",
                    "any ideas", "ideas", "recipe", "recipes", "tonight", "supper", "lunch",
                    # a kitchen that has just lost its oven says so without asking a question at
                    # all: "no oven in my new flat" is the what-can-i-cook line, and every answer
                    # for it is in `without()`
                    "kitchen", "flat", "house", "place", "moving", "moved", "move in")),
    _no_appliance,
    # the appliance as a thing to buy, mend or give back is another lane's: what to do about the
    # machine itself, not what to cook in the kitchen that has lost it
    avoid=("repair", "repairing", "replace", "replacing", "mend", "mending", "fix", "fixing",
           "engineer", "warranty", "guarantee", "quote", "quotes", "worth", "landlord",
           "landlady", "letting agent", "buy", "buying", "cost", "cheap", "best", "which one",
           "recommend", "brand", "install", "installing", "fit", "fitting", "fuse", "element",
           "thermostat", "fan", "door", "seal", "gas", "electric", "energy", "bill", "bills",
           # a pudding with no oven is the cold-pudding table's own answer, and it names the
           # three things people actually want to make
           "pudding", "puddings", "dessert", "desserts"),
    bias=2))
# "how long do you boil an egg" then "does that work for duck eggs too": the times above are a
# hen's egg, and a duck egg is bigger, so the follow-up was answered with the hen's numbers again.
# A bird named in the line is the point of the question, so it gets its own card rather than the
# egg row repeating itself.
ENTRIES.append(entry(
    "duck-eggs",
    (("duck egg", "duck eggs", "ducks egg", "ducks eggs"),
     ("boil", "boiled", "boiling", "cook", "cooking", "same", "work", "works", "how long",
      "how", "use", "bake", "baking", "substitute", "instead", "too", "runny", "hard", "eat",
      "longer", "take longer", "more time", "difference", "differently", "differ")),
    "A duck egg takes about a minute longer than a hen's: 7 to 8 minutes for a runny yolk and 11 "
    "for hard boiled, from already boiling water. It is bigger, the white sets firmer and the yolk "
    "is richer, which is why it is good in baking and fried; cook it exactly like a hen's egg, "
    "cool it under the tap before peeling, and keep it in the fridge like any egg.",
    # a duck on a pond, duck for dinner and duckweed in the garden are other answers
    bias=3,
    # a duck egg that might not be safe is the raw-egg row's question, which knows the rules
    avoid=("safe", "safely", "raw", "salmonella", "pregnant", "baby",
           "pond", "garden", "weed", "duckweed", "roast", "crispy", "confit", "feed",
           "feeding", "pet", "the ducks"),
))


# The other half of the smoked family, once the smoking row stops answering it: a fish that comes
# smoked is already cooked, so "how do i cook smoked haddock" and "how do i cook kippers" were
# left with a shrug. The answer is the heat and the four minutes, and the fish said in the line is
# the fish named back, because a kipper and a smoked mackerel are not the same shape on the plate.
_SMOKED_FISH = ("smoked haddock", "smoked mackerel", "smoked trout", "smoked fish", "kippers",
                "kipper", "smoked herring")
_SMOKED_FISH_REPLY = (
    "Smoked {fish} is already cooked, so it only wants heating through: 3 to 4 minutes under a hot "
    "grill, or 4 to 5 minutes in milk that is barely simmering, which keeps it moist. Flake it "
    "while it is warm into a fish pie, scrambled eggs or a salad with a squeeze of lemon.")


# Smoked salmon is the same family and the opposite answer: it is cured, not cooked, so it is eaten
# cold or warmed at the last minute, and "how do i cook smoked salmon" was answered with the heat
# and time for baking a raw fillet.
SMOKED_SALMON_ALREADY = (
    "Smoked salmon is cured rather than cooked, so it needs no cooking at all: eat it cold on "
    "bread with a squeeze of lemon and black pepper, or warm it through at the very end - folded "
    "into hot pasta, a risotto or scrambled eggs off the heat - because heat turns it firm and "
    "salty. Do not fry or bake it.")


def _smoked_fish_reply(memory, reading):
    """The smoked fish the line names, in the answer that fish wants."""
    said = str((reading or {}).get("text") or "").lower()
    if "smoked salmon" in said or "lox" in said:
        return SMOKED_SALMON_ALREADY
    return _SMOKED_FISH_REPLY.format(fish=_smoked_fish(reading))


def _smoked_fish(reading):
    said = str((reading or {}).get("text") or "").lower()
    for name in _SMOKED_FISH:
        if name in said:
            if name in ("kipper", "kippers", "smoked herring"):
                return "kipper"
            return name[len("smoked "):] if name.startswith("smoked ") else name
    return "haddock"

ENTRIES.append(entry(
    "smoked-fish",
    (("smoked haddock", "smoked mackerel", "smoked trout", "smoked fish", "kipper", "kippers",
      "smoked herring", "smoked salmon", "lox"),
     ("cook", "cooking", "heat", "hot", "grill", "grilled", "poach", "poached", "serve", "eat",
      "how", "best way", "what do i do", "what can i do", "warm", "warm up")),
    _smoked_fish_reply,
    # smoked salmon is eaten cold out of the packet, so it is not this row's fish; the smoking row
    # and the health rows have their own asks
    avoid=("gravad", "gravlax", "healthy", "healthier", "omega",
           "pregnant", "pregnancy", "freeze", "frozen", "keep", "how long", "hot smoke",
           "cold smoke", "smoker", "wood chips", "low and slow", "barbecue", "bbq"),
    bias=2))
