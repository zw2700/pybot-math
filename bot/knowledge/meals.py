"""Meal ideas: what to cook tonight, and what to make from what is already in the kitchen.

The answers lane owns this domain. bot/knowledge/cooking.py holds techniques and timings
(how long to roast a chicken, why rice goes sticky); this file holds dishes, keyed by the
ingredients they use and how long they take. One row therefore answers every way of asking
for it: "what should I cook tonight", "anything quick with eggs", "I have spinach and
potatoes, what can I make", "something without meat".

The reply is composed rather than canned: the picker reads the ingredients the line names
(memory["understood"]), drops dishes that clash with a limit the person set (no meat, no
cheese, vegan, a time limit), prefers the dish that uses most of what they have, and does
not offer the dish it just offered. So a new ingredient or a new dish is one row of data,
not a new rule.
"""
import functools
import random
import re

from .cleaning import not_a_mark_on_a_thing
from .lookup import not_the_heat_of_an_argument as _not_an_argument
from .dishes import KIDS_IDEA, a_dish_is_already_the_plan
from .occasions import BRING_NOT_FOOD
from ..compose import fit
from ..understanding import line_as_read
from .lookup import entry, says_it_has_gone_off

# The topics this domain answers, for the arbiter's specialist rule (see bot/knowledge).
ANSWERS = ("cooking", "food-and-drink")

# --- the dishes ---------------------------------------------------------------
# ingredient, time, diet: each dish lists the ingredients it uses (canonical names) and
# the one-clause method that makes it possible. "minutes" is a realistic weeknight total.


# A dish named for a category does not read back after the frame: "Something else that works is
# dhal." is a fragment, where "... is carbonara." is a sentence. `name` stays the key the matching
# uses; `said` is how it is quoted back to the person.
SAID_AS = {"dhal": "a lentil dhal", "chilli": "a chilli"}


class Dish:
    __slots__ = ("name", "uses", "minutes", "diet", "how", "favourite", "said")

    def __init__(self, name, uses, minutes, diet, how):
        self.name = name
        self.said = SAID_AS.get(name, name)
        self.uses = tuple(uses)
        self.minutes = minutes
        self.diet = diet
        self.how = how
        # A good answer to the open "what shall I cook tonight?", when nothing is named.
        self.favourite = name in FAVOURITES

    def __repr__(self):
        return f"<Dish {self.name}>"


# The dishes that make a good answer to the open "what shall I cook tonight?", in the order a
# friend would offer them: everyday, cheap, and not a lot of shopping needed.
FAVOURITES = ("a frittata", "tomato pasta", "chickpea curry", "dhal", "a bean stew",
              "a chicken traybake", "macaroni cheese", "a sausage traybake", "tuna pasta",
              "vegetable soup", "a potato curry", "a salmon traybake")
# The dishes people cook when they want the table to say something: what "looks nice" and
# "impress the in laws" should land on, rather than the cheapest half-hour supper.
SHOW_OFF = ("a salmon traybake", "a chicken traybake", "mushroom risotto",
            "aubergine parmigiana", "a sausage and mash", "a cod traybake", "chilli",
            "spaghetti bolognese", "a halloumi traybake", "a turkey traybake",
            "a squash and chickpea traybake", "chicken curry")

DISHES = (
    Dish("a frittata", ("egg", "spinach"), 20, "vegetarian",
         "beat six eggs, stir in whatever vegetables you have (spinach wilted first if it is "
         "raw), cook it in an oiled ovenproof pan for 5 minutes and finish it under the grill "
         "for 8"),
    Dish("shakshuka", ("egg", "tomato", "onion"), 25, "vegetarian",
         "soften an onion with a tin of tomatoes and a pinch of cumin for 10 minutes, crack the "
         "eggs into the sauce, cover and cook 5 minutes more"),
    Dish("egg fried rice", ("egg", "rice", "pea"), 15, "vegetarian",
         "fry cold cooked rice in hot oil for 5 minutes, push it to one side, scramble two eggs "
         "in the gap, then stir it all together with soy sauce and peas"),
    Dish("an omelette", ("egg", "cheese"), 10, "vegetarian",
         "whisk two or three eggs, cook them gently in butter for 2 minutes, add grated cheese "
         "and fold it over"),
    Dish("a Spanish tortilla", ("egg", "potato", "onion"), 30, "vegetarian",
         "fry sliced potato and onion softly for 15 minutes, mix them into five beaten eggs and "
         "set it in the pan for another 10"),
    Dish("carbonara", ("pasta", "egg", "bacon", "cheese"), 20, "meat",
         "fry the bacon, cook the pasta, then toss it off the heat with beaten eggs, grated "
         "cheese and plenty of black pepper"),
    Dish("tomato pasta", ("pasta", "tomato", "garlic"), 20, "vegan",
         "fry sliced garlic in olive oil for a minute, add a tin of tomatoes and simmer 10 "
         "minutes while the pasta cooks"),
    Dish("tuna pasta", ("pasta", "tuna"), 15, "fish",
         "stir a tin of tuna through hot pasta with olive oil, lemon and capers if you have them"),
    Dish("pesto pasta", ("pasta", "pesto"), 12, "vegetarian",
         "stir pesto through hot pasta with a spoonful of the cooking water to loosen it"),
    Dish("macaroni cheese", ("pasta", "cheese", "milk"), 25, "vegetarian",
         "make a quick white sauce from butter, flour and milk, melt the cheese into it and stir "
         "it through cooked pasta"),
    Dish("courgette pasta", ("pasta", "courgette", "garlic"), 20, "vegan",
         "fry thin courgette slices with garlic for 8 minutes and toss them with pasta, lemon "
         "and black pepper"),
    Dish("broccoli pasta", ("pasta", "broccoli", "garlic"), 20, "vegetarian",
         "boil the broccoli with the pasta for the last 5 minutes, then toss it all with garlic "
         "fried in oil and a lot of pepper"),
    Dish("mushroom risotto", ("rice", "mushroom", "onion"), 30, "vegetarian",
         "soften the onion, add the rice and mushrooms, then stir in hot stock a ladle at a time "
         "for 20 minutes"),
    Dish("mushrooms on toast", ("mushroom", "bread", "garlic"), 15, "vegetarian",
         "fry the mushrooms hard in butter so they colour, add garlic at the end and pile them "
         "onto toast"),
    Dish("chickpea curry", ("chickpea", "tomato", "onion"), 25, "vegan",
         "fry an onion with curry powder, add a tin of chickpeas and a tin of tomatoes and simmer "
         "for 15 minutes"),
    Dish("dhal", ("lentil", "onion", "garlic"), 30, "vegan",
         "simmer red lentils with onion, garlic and cumin in plenty of water for 25 minutes, "
         "until soft, then salt it"),
    Dish("a bean stew", ("bean", "tomato", "onion"), 25, "vegan",
         "fry the onion, add a tin of beans, a tin of tomatoes and paprika and simmer 15 minutes"),
    Dish("chilli", ("mince", "bean", "tomato", "onion"), 40, "meat",
         "brown the mince, add onion, a tin of beans and a tin of tomatoes with chilli and cumin, "
         "and simmer it 25 minutes"),
    Dish("a veggie chilli", ("bean", "pepper", "tomato", "onion"), 25, "vegan",
         "fry a chopped pepper and onion, add beans, tomatoes and chilli powder and simmer 20 "
         "minutes; rice or a baked potato alongside"),
    Dish("a sausage traybake", ("sausage", "potato", "onion"), 45, "meat",
         "toss sausages, halved potatoes and onion wedges with oil on a tray at 200C (180C fan) "
         "for 40 minutes, turning once"),
    Dish("a chicken traybake", ("chicken", "potato", "lemon"), 40, "meat",
         "toss chicken thighs, potato chunks and lemon slices with oil at 200C (180C fan) for 40 "
         "minutes, skin side up"),
    Dish("a chicken stir-fry", ("chicken", "pepper", "noodle"), 20, "meat",
         "slice the chicken thin, fry it hot for 5 minutes with sliced peppers, then add cooked "
         "noodles and soy sauce"),
    Dish("chicken curry", ("chicken", "onion", "tomato"), 35, "meat",
         "brown the chicken, add onion and curry paste, then a tin of tomatoes, and simmer 20 "
         "minutes"),
    Dish("a salmon traybake", ("salmon", "potato", "broccoli"), 30, "fish",
         "roast the potatoes at 200C for 20 minutes, then add the salmon and broccoli with oil "
         "and lemon and give it 12 minutes more"),
    Dish("a salmon rice bowl", ("salmon", "rice", "cucumber"), 25, "fish",
         "pan-fry the salmon 4 minutes a side and flake it over rice with sliced cucumber and soy"),
    # The ingredient row below says smoked haddock "wants a fish pie" and there was no fish pie in
    # the table, so a smoked haddock ask fell through to the smoking row and got the method for
    # hot-smoking a salmon. It is the fish pie the row promised.
    Dish("a smoked haddock fish pie", ("smoked haddock", "potato", "milk"), 40, "fish",
         "poach the haddock in milk for 5 minutes, flake it into a dish with that milk and a spoon "
         "of flour, top it with mashed potato and bake at 200C for 25 minutes"),
    # Salads are asked for by name ("i want a salad for dinner") and the table had none.
    Dish("a tuna salad", ("tuna", "tomato", "cucumber"), 10, "fish",
         "drain a tin of tuna into a bowl with chopped tomato and cucumber, dress it with oil, "
         "lemon and salt, and add a handful of leaves or cold pasta if you want it filling"),
    Dish("a chickpea salad", ("chickpea", "tomato", "cucumber", "lemon"), 10, "vegan",
         "toss a drained tin of chickpeas with chopped tomato and cucumber, dress it with lemon "
         "juice, olive oil and salt, and crumble cheese over it if you eat it"),
    Dish("a chicken salad", ("chicken", "lettuce", "tomato"), 15, "meat",
         "fry or griddle a chicken breast 5 minutes a side, rest it 5 minutes, then slice it over "
         "leaves and tomato with oil and lemon"),
    Dish("a prawn stir-fry", ("prawn", "noodle", "pepper"), 15, "fish",
         "fry the prawns 2 minutes, add peppers, cooked noodles and soy sauce and toss until hot"),
    Dish("a tofu stir-fry", ("tofu", "pepper", "rice"), 20, "vegan",
         "pat the tofu dry, fry it until golden, add peppers, soy and ginger, and serve it on rice"),
    Dish("a baked potato with beans", ("potato", "bean", "cheese"), 25, "vegetarian",
         "microwave the potato 8 minutes, rub it with oil and salt and crisp it in a hot oven for "
         "15, then top it with hot beans and cheese"),
    Dish("a potato curry", ("potato", "onion", "tomato"), 30, "vegan",
         "fry onion with spices, add cubed potato and tomatoes with a splash of water and simmer "
         "20 minutes"),
    Dish("a bacon and egg hash", ("potato", "bacon", "egg"), 25, "meat",
         "fry cubed cooked potato until crisp, add chopped bacon, then crack an egg in and cover "
         "the pan for 3 minutes"),
    Dish("a cheese toastie", ("bread", "cheese", "butter"), 10, "vegetarian",
         "butter the outside, fill it with cheese and cook it in a dry pan for 3 minutes a side "
         "with something heavy on top"),
    Dish("beans on toast", ("bread", "bean"), 8, "vegan",
         "warm the beans in a pan with a little oil and plenty of pepper and pour them over thick "
         "toast"),
    Dish("a quesadilla", ("tortilla", "cheese", "bean"), 10, "vegetarian",
         "fill a tortilla with cheese and beans, fold it and dry-fry it 2 minutes a side"),
    Dish("vegetable soup", ("carrot", "onion", "potato"), 30, "vegan",
         "fry the onion and carrot 5 minutes, add potato and enough stock to cover, simmer 20 "
         "minutes and blend it"),
    Dish("a leek and potato soup", ("leek", "potato", "onion"), 30, "vegetarian",
         "sweat sliced leeks and onion in butter for 8 minutes without colouring them, add cubed "
         "potato and stock to cover, simmer 20 minutes and mash it roughly"),
    Dish("lentil soup", ("lentil", "carrot", "onion"), 35, "vegan",
         "fry onion and carrot, add lentils and stock and simmer for 25 minutes"),
    Dish("pea and mint soup", ("pea", "onion"), 15, "vegan",
         "simmer frozen peas and a chopped onion in stock for 10 minutes with a handful of mint, "
         "then blend it"),
    Dish("spinach and chickpea curry", ("spinach", "chickpea", "onion", "tomato"), 25, "vegan",
         "fry an onion with curry powder, add a tin of chickpeas and a tin of tomatoes and simmer "
         "15 minutes, then stir the spinach in at the end until it wilts"),
    Dish("a halloumi traybake", ("halloumi", "potato", "pepper", "onion"), 35, "vegetarian",
         "toss cubed potato and sliced pepper in oil and roast 20 minutes at 200C (180C fan), then "
         "add thick slices of halloumi for the last 12 minutes and squeeze lemon over it"),
    Dish("cabbage with bacon", ("cabbage", "bacon"), 20, "meat",
         "fry chopped bacon until crisp, add shredded cabbage and a splash of water and cook it 8 "
         "minutes"),
    # Ideas that came over from cooking.py's ingredient table, kept here with the rest.
    Dish("spaghetti bolognese", ("mince", "tomato", "onion", "pasta"), 30, "meat",
         "brown the mince with a chopped onion, add a tin of tomatoes and a stock cube and "
         "simmer it 20 minutes while the spaghetti cooks"),
    Dish("a sausage and mash", ("sausage", "potato", "onion"), 30, "meat",
         "boil the potatoes 15 minutes, fry or roast the sausages, then mash the potatoes with "
         "butter and make a quick onion gravy in the pan"),
    Dish("a chicken and rice", ("chicken", "rice", "onion"), 30, "meat",
         "fry strips of chicken with an onion, add a tin of tomatoes or a spoon of curry paste, "
         "then stir in cooked rice for the last 2 minutes"),
    Dish("roast veg pasta", ("pasta", "veg", "carrot", "pepper", "onion"), 30, "vegan",
         "roast chopped veg at 200C (180C fan) for 25 minutes with oil and salt and stir it "
         "through cooked pasta"),
    Dish("a bacon pasta", ("pasta", "bacon", "tomato", "onion"), 20, "meat",
         "fry the bacon with an onion in a dry pan, add a tin of tomatoes, and toss it through "
         "pasta with a splash of the cooking water"),
    Dish("mince and cabbage", ("mince", "cabbage", "onion"), 20, "meat",
         "brown the mince with a chopped onion, add shredded cabbage and a splash of water and "
         "cook it 8 minutes with a lid on"),
    Dish("a cheesy potato hash", ("potato", "egg", "cheese", "onion"), 25, "vegetarian",
         "boil the diced potato 12 minutes, fry it with an onion until it colours, then crack "
         "eggs over it and scatter cheese on top"),
    Dish("a cod traybake", ("white fish", "potato", "tomato"), 35, "fish",
         "roast potato chunks and cherry tomatoes at 200C (180C fan) for 20 minutes, then lay "
         "the cod on top with oil and lemon and give it 12 minutes more"),
    Dish("a turkey traybake", ("turkey", "potato", "onion"), 40, "meat",
         "toss turkey pieces, potato chunks and onion wedges with oil and paprika at 200C "
         "(180C fan) for 35 minutes"),
    Dish("a sweet potato curry", ("sweet potato", "chickpea", "tomato", "onion"), 30, "vegan",
         "fry onion with curry powder, add cubed sweet potato and a tin of tomatoes, simmer 20 "
         "minutes and stir in a tin of chickpeas"),
    Dish("aubergine parmigiana", ("aubergine", "tomato", "cheese"), 45, "vegetarian",
         "fry sliced aubergine in plenty of oil until soft, layer it in a dish with tomato sauce "
         "and grated cheese, and bake at 190C (170C fan) for 25 minutes"),
    Dish("a squash and chickpea traybake", ("squash", "chickpea", "onion"), 35, "vegan",
         "toss squash chunks, onion wedges and cumin with oil at 200C (180C fan) for 25 minutes, "
         "then stir in a tin of chickpeas and a squeeze of lemon"),
    Dish("a ham and potato chowder", ("bacon", "potato", "onion", "milk"), 30, "meat",
         "fry chopped ham and onion 5 minutes, add diced potato and stock to cover, simmer 15 "
         "minutes and stir in a splash of milk"),
    Dish("a baked feta pasta", ("feta", "pasta", "tomato"), 25, "vegetarian",
         "put a block of feta in a dish with halved cherry tomatoes, oil, oregano and a pinch "
         "of chilli, bake at 200C (180C fan) for 20 minutes, then mash it into the tomatoes and "
         "stir through cooked pasta"),
    Dish("a fish foil bake", ("salmon", "lemon", "potato"), 25, "fish",
         "wrap the fish in foil with lemon and butter and bake at 200C (180C fan) for 12 to 15 "
         "minutes, with boiled potatoes on the side"),
)

# --- the words for each ingredient --------------------------------------------
# One canonical name per ingredient, so "eggs", "egg" and "boiled eggs" are one thing and a
# dish only has to say "egg".
INGREDIENTS = {
    "egg": ("egg", "eggs"),
    "cheese": ("cheese", "cheddar", "mozzarella", "parmesan"),
    # Feta is its own thing: "what can i make with feta" is baked feta, and the cheese row only
    # had "grate it over pasta", which is a different answer to a name that specific.
    "feta": ("feta", "feta cheese"),
    "milk": ("milk", "cream"),
    # A plant milk is not dairy: "what can i make with oat milk" must not come back as macaroni
    # cheese. Each one is a name of its own, and the phrase pass takes it before bare "milk".
    "coconut milk": ("coconut milk", "tinned coconut milk", "coconut cream"),
    "oat milk": ("oat milk",),
    "soy milk": ("soy milk", "soya milk"),
    "almond milk": ("almond milk",),
    "rice milk": ("rice milk",),
    "plant milk": ("plant milk", "plant milks"),
    # A compound name is one food, not the words inside it: "condensed milk" is not milk and
    # "butter beans" are not butter. The phrase pass takes each of these before the bare word
    # in it, so "what can i make with condensed milk" is not answered with macaroni cheese and
    # "with butter beans" is not answered with shortbread. None of them is in a dish of this
    # table, so the kitchen table's own idea for the food answers.
    "condensed milk": ("condensed milk",),
    "evaporated milk": ("evaporated milk",),
    "butter bean": ("butter beans", "butter bean"),
    "butter": ("butter",),
    "pasta": ("pasta", "spaghetti", "penne", "macaroni"),
    "noodle": ("noodle", "noodles", "ramen"),
    # Rice noodles are soaked, not boiled, and "rice noodles and prawns" is one food and a
    # prawn rather than fried rice: a name this specific is a name of its own.
    "rice noodle": ("rice noodles", "rice noodle"),
    "rice": ("rice", "risotto"),
    "bread": ("bread", "toast", "baguette", "rolls"),
    "tortilla": ("tortilla", "tortillas", "wrap", "wraps"),
    "potato": ("potato", "potatoes", "spud", "spuds"),
    "sweet potato": ("sweet potato", "sweet potatoes"),
    "squash": ("butternut", "butternut squash", "squash", "pumpkin"),
    # "tom" is a person far more often than a tomato ("my cats, milly and tom").
    "tomato": ("tomato", "tomatoes", "toms", "passata", "tinned tomatoes",
               "chopped tomatoes"),
    "onion": ("onion", "onions", "shallot", "shallots"),
    # A leek is not an onion: "what can i make with a leek" wants a leek dish.
    "leek": ("leek", "leeks"),
    "garlic": ("garlic",),
    "pepper": ("pepper", "peppers", "capsicum"),
    "carrot": ("carrot", "carrots"),
    "courgette": ("courgette", "courgettes", "zucchini"),
    "aubergine": ("aubergine", "eggplant"),
    "broccoli": ("broccoli",),
    "cabbage": ("cabbage",),
    "pea": ("pea", "peas"),
    "bean": ("bean", "beans", "baked beans", "kidney beans", "black beans"),
    "chickpea": ("chickpea", "chickpeas", "hummus"),
    "lentil": ("lentil", "lentils", "dhal", "dal"),
    "spinach": ("spinach", "kale", "chard"),
    "mushroom": ("mushroom", "mushrooms"),
    "chicken": ("chicken",),
    "sausage": ("sausage", "sausages"),
    "mince": ("mince", "minced beef", "ground beef", "beef"),
    "bacon": ("bacon", "ham", "pancetta", "chorizo"),
    "tuna": ("tuna",),
    "salmon": ("salmon",),
    # White fish goes in by name: cod and haddock are what a Friday ask is usually about.
    "white fish": ("cod", "haddock", "pollock", "white fish", "fish fillets", "fish"),
    # Smoked haddock is not a plain white fish: it is smoked, so it poaches in milk and it wants
    # a fish pie. Asked as a white fish it was answered with a cod traybake.
    "smoked haddock": ("smoked haddock", "smoked fish"),
    "turkey": ("turkey",),
    "prawn": ("prawn", "prawns", "shrimp"),
    "tofu": ("tofu",),
    "quorn": ("quorn", "quorn mince", "quorn pieces", "quorn fillets", "mycoprotein"),
    "lemon": ("lemon", "lemons", "lime", "limes"),
    "pesto": ("pesto",),
    "maple syrup": ("maple syrup",),
    "chocolate": ("chocolate", "dark chocolate", "milk chocolate", "cooking chocolate",
                  "chocolate chips"),
    "bagel": ("bagel", "bagels"),
    "cucumber": ("cucumber",),
    "lettuce": ("lettuce", "salad leaves", "leaves", "rocket"),
    # "greens" was a form of lettuce, so "what can i make with spring greens" came back as a
    # chicken salad. A bag of greens is a cabbagey green, and it is its own food.
    "spring greens": ("spring greens", "spring green", "collard greens", "collard",
                      "greens"),
    "halloumi": ("halloumi", "paneer"),
    # "what can i make with a bag of frozen veg" is the commonest way people name a bag of
    # mixed vegetables: it is one ingredient, not whatever happens to be in the bag.
    "veg": ("veg", "vegetables", "vegetable", "frozen veg", "frozen vegetables", "mixed veg",
            "mixed vegetables", "frozen mixed veg"),
}

# The ingredients some dish in the table will actually cook with. A name that is on the
# ingredient list but in no dish is a food this table cannot make anything out of.
IN_A_DISH = frozenset(name for _dish in DISHES for name in _dish.uses)

# The fish are separate ingredients here, because "what can i make with salmon" is a different
# dish from "what can i make with cod". A person who says they do not eat fish has ruled out all
# of them, so a limit on the family has to put every one out: without that the alternative
# offered to a person who does not eat fish was a salmon traybake.
FISH_INGREDIENTS = frozenset(("white fish", "salmon", "tuna", "prawn"))

WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

# Styles of dish people ask for by name. "i fancy a curry" wants a curry, not a soup that
# happens to fit the clock.
DISH_STYLE = ("curry", "soup", "stew", "stir fry", "stir-fry", "traybake", "pie", "salad",
              "roast", "risotto", "noodles", "casserole", "bake")
# A craving for a kind of dish is a request for one, even with no question mark and no food
# word: "i fancy a stew tonight" is not news about someone's evening.
STYLE_WANT = ("fancy", "mood for", "feel like", "up for", "craving", "i want a", "i want some")
# How people describe a style the table does not name: nobody says "i fancy a curry" when they
# mean "i fancy something spicy", and the dish that answers it is a curry, a chilli or a stir-fry.
STYLE_CUES = {"spicy": ("curry", "chilli", "stir fry"), "hot": ("curry", "chilli", "stir fry"),
              "creamy": ("risotto", "pasta", "curry"), "cosy": ("soup", "stew", "casserole"),
              "cosy night": ("soup", "stew"), "comfort": ("soup", "stew", "pie", "macaroni"),
              "warming": ("soup", "stew", "casserole"),
              "fresh": ("salad", "stir fry"), "light": ("salad", "soup")}
# Words that ask for the cheap end of the table. A dish is cheap when everything in it is a
# staple: the point is not the price of a chicken but which dishes people cook on a budget.
# A day out is its own kind of meal: things that travel and eat cold, not a traybake.
CARRY_ASK = ("picnic", "picnics", "beach", "day out", "day trip", "road trip", "train journey",
             "long journey", "flight", "cool box", "coolbox", "cooler box", "flask")
CARRY_REPLIES = (
    ("Things that travel well: a frittata or a quiche cut in wedges, cold sausages or sausage "
     "rolls, cheese and oatcakes, cherry tomatoes, and fruit that survives a bag. Pack anything "
     "wet in its own box and take a bag for the rubbish."),
    ("Cold and easy to carry: a frittata cut in wedges, sausage rolls, cheese with oatcakes or "
     "bread, tomatoes and a bag of grapes. Freeze a bottle of water the night before - it keeps "
     "the food cold and then it is your drink."),
)
CHEAP_ASK = ("cheaper", "cheap", "cheapest", "budget", "afford", "save money", "less money",
             "tight month", "low on money", "money is tight", "skint", "payday", "hard up",
             "no money", "short of money", "on a tight budget",
             # A student kitchen is a cheap kitchen: "easy meals for students" is not an ask
             # for salmon.
             "student", "students", "uni", "university", "fresher", "freshers", "halls",
             "shared kitchen", "one pan")
# "healthy dinner ideas" is a filter on the table, not decoration on the sentence: it should
# come back with vegetables, fish or beans, not a traybake under a cheese crust.
LIGHT_ASK = ("healthy", "healthier", "healthily", "light", "lighter", "slimming", "low calorie",
             "low fat", "nutritious", "fresh", "clean eating", "balanced", "not too heavy",
             "something light")
LIGHT_SET = ("a salmon traybake", "a salmon rice bowl", "a tofu stir-fry", "a chickpea salad",
             "a chicken salad", "vegetable soup", "a leek and potato soup", "lentil soup",
             "pea and mint soup", "spinach and chickpea curry", "a chicken stir-fry",
             "a prawn stir-fry", "a fish foil bake", "a cod traybake", "roast veg pasta",
             "a squash and chickpea traybake", "a bean stew", "a chicken and rice")
# A small person or a holiday named with an ingredient and no dinner word is an activity, not
# a dinner: "easter egg ideas for toddlers" wants a hunt and some paint, not an omelette.
SMALL_PEOPLE = ("toddler", "toddlers", "baby", "babies", "kid", "kids", "children", "child",
                "nursery", "grandchild", "grandchildren", "easter", "halloween", "christmas",
                "birthday", "bonfire night")
# Children are the eaters, not a limit on the shopping: a line that names them and no food is the
# "what do i feed them" question, which has its own answer in dishes.KIDS_IDEA.
CHILD_AT_TABLE = ("toddler", "toddlers", "baby", "babies", "kid", "kids", "children", "child",
                  "little ones", "little one", "grandchild", "grandchildren", "family",
                  "families", "my son", "my daughter")
# Food before a race, a match or training is fuelling, not dinner: what to eat an hour before
# a 10k is a different question from what to cook, and a bean stew is the wrong answer to it.
EVENT_WORDS = ("race", "match", "game", "training", "workout", "gym", "run", "10k", "5k",
               "marathon", "football", "rugby", "cricket", "netball", "swim", "competition",
               "tournament", "triathlon", "fight", "climb")
BEFORE_EVENT = ("before a", "before the", "before my", "before i", "morning of", "day of",
                "pre workout", "pre-workout", "fuel for", "fuelling", "fueling")
MEAL_WORD = ("dinner", "tea", "supper", "lunch", "meal", "meals", "cook", "cooking", "eat",
             "eating", "food", "hungry", "starving", "bake", "baking")

CHEAP_SET = ("egg", "potato", "bean", "chickpea", "lentil", "pasta", "rice", "onion",
             "tomato", "cheese", "cabbage", "carrot", "bread", "pea", "spinach", "cucumber",
             "lemon", "tofu", "noodle", "mushroom", "courgette", "aubergine", "squash",
             "pepper", "broccoli")
CHEAP = set(CHEAP_SET)


def cheap(item):
    """A dish a tight month can carry: nothing bought fresh and skippable in it."""
    return all(use in CHEAP for use in item.uses)

FOOD_WORDS = tuple(word for forms in INGREDIENTS.values() for word in forms)
FOOD_WORDS += ("meal", "meals", "dinner", "supper", "teatime", "lunch", "food", "cook",
               "cooking", "recipe", "eat", "eat something", "hungry", "kitchen", "fridge",
               "cupboard", "starving", "starved", "famished",
               # "im home late, something quick" is a request for a dinner: the "something" is
               # the food, so a hurry is not a shrug.
               "something quick", "something fast", "something easy", "something simple",
               "something filling", "something hot")
# A dish named by its style is food too: "can i do a quick soup" is a dinner ask with no
# ingredient in it, and the style words carry it the way "dinner" does.
FOOD_WORDS += tuple(DISH_STYLE) + tuple(STYLE_CUES)

# Limits people put on an idea, and the diets that satisfy them.
NO_MEAT = ("vegetarian", "veggie", "vegan", "meatless", "no meat", "without meat", "less meat",
           "cut out meat", "cut down on meat", "no meat or fish", "meat free", "meat-free")
NO_CHEESE = ("dairy", "lactose", "no cheese", "without cheese", "cheeseless")
# A diet word is a meal word: "im vegetarian, what can i have tonight" names no food but is
# plainly a request for a dinner, and the diet is what the table has to work with.
FOOD_WORDS += tuple(NO_MEAT) + tuple(NO_CHEESE)
# Ways of ruling an ingredient out. "dinner ideas that arent pasta" and "no mince tonight" are
# limits on the idea, so the words before the food name decide how it is read: without them the
# table hears pasta and suggests pasta.
NO_CUE = ("no", "without", "arent", "isnt", "dont want", "dont eat", "dont like", "doesnt eat",
          "doesnt like", "sick of", "bored of", "tired of", "had enough", "not in the mood for",
          "cant eat", "cant have", "allergic to", "instead of",
          # A food somebody says they hate is ruled out as surely as one behind a "no": "i hate
          # mushrooms what should i cook" was offered mushrooms on toast, and "i cant stand fish"
          # with a cod traybake. Both sets of words are kept: the plain ones and the same limit
          # said as a reluctance ("not fussed", "disliked").
          "hate", "hates", "hated", "dislike", "dislikes", "disliked", "loathe", "cant stand",
          "can't stand", "not a fan", "not a fan of", "not fussed", "not keen", "not keen on",
          "fed up of", "fed up with", "had it with",
          # A child who will not eat something is the same limit as a dislike: "my kids wont
          # eat mushrooms what can i cook" got the method for frying mushrooms.
          "wont eat", "won't eat", "will not eat", "wont touch", "won't touch",
          # "im out of cheese" said after an idea is a limit like any other.
          "out of", "ran out of", "run out of", "none left", "no more",
          # "i dont have any cheese", "we havent got any onions": a food they are short of is a
          # limit like one they do not eat, and read as an ingredient it came back to them in a
          # dish that used it - an omelette with grated cheese offered to someone who had just
          # said there was none in the house.
          "dont have", "do not have", "havent got", "have not got", "got no", "short of")
# The words a person puts between the cue and the food: "dont have ANY cheese", "im out of THE
# milk", "no MORE rice". A cue that only matches when the food follows it directly is no use for
# the way people actually say it.
# "much" is not one of them: "i dont have much cheese" is a little cheese left, and a dish that
# uses a little is still a dish they can cook.
NO_GAP = ("", " any", " the", " a", " an", " some", " more", " any more", " of the",
          " of any", " any of the",
          # A dislike is said with "of" between the cue and the food: "im not a fan of mushrooms"
          # and "im not keen on mushrooms" were read as no limit at all, and the mushroom row
          # answered a person who had just said they did not want mushrooms.
          " of", " on")

# A line asking how to do something, how long for, or whether it is still safe is a technique
# question: bot/knowledge/cooking.py answers it, and the meal table keeps out.
# The words that make a line a game rather than a meal: the meal row keys on "tonight" and
# "for two", which a game asks for as well.
GAME_WORDS = ("game", "games", "board game", "board games", "boardgame", "boardgames",
              "puzzle", "puzzles", "jigsaw", "jigsaws", "chess", "cards", "quiz")

TECHNIQUE = ("how", "long", "safe", "time", "temperature", "temp", "defrost", "thaw", "store",
             "keep", "best way", "way to cook", "way to make", "how to",
             "reheat", "burning", "burnt", "smell", "rubbery", "sticky", "soggy", "lumpy", "raw",
             "pink", "undercooked", "ruined", "freeze", "why")

# "How do I use up carrots" is the same question as "use up carrots": the "how" is how people
# start it, not a request for a technique. TECHNIQUE carries it so that the rows which suggest a
# dinner stand aside for a real method question, but here the use-up words are the whole ask -
# "how do i use up milk", "how do i use up leftover potatoes", "how do i use up the rest of the
# joint" - and with "how" in the avoid the row never answered them, so the bot shrugged. Every
# other technique word still stands the row down: "how long does leftover rice keep", "how do i
# reheat leftover chicken", "how do i freeze bananas" and "why did my leftover potatoes go pink"
# are all other rows' questions. "stale" goes the other way, in: "how do i use up stale bread" is
# the stale-bread row's question, and reviving the loaf is the answer that helps, so a stale word
# is what went wrong with the food rather than what to do with it.
USE_UP_TECHNIQUE = tuple(word for word in TECHNIQUE if word != "how") + ("stale",)

# What to do with something cooked that has to be eaten up, by what it is.
USE_UP = (
    (("chicken", "turkey", "meat", "beef", "pork", "lamb", "ham", "joint"),
     "Shred it into fried rice, or fold it through a white sauce with pasta and bake it 20 minutes "
     "at 200C; cooked meat only needs heating through"),
    (("potato", "potatoes"),
     "Fry cold chopped potatoes with an onion until crisp, or fold them into a frittata and finish "
     "it under the grill; both take about 20 minutes"),
    (("bread", "loaf"),
     "Tear it into a salad with tomatoes, oil and salt, or blitz it into breadcrumbs and freeze "
     "them for topping a bake"),
    (("cheese",),
     "Grate it into a macaroni cheese, or make a toastie with it and a little mustard"),
)

# A use-up line names something already cooked, or spare in the fridge, so the answer has to be a
# use for it. The rows above are written for the foods people ask about most; the table below is
# what any cooked thing of that kind will take, said with the food's own name in it. It was written
# because "what can i do with leftover cabbage" was answered "Roast them with oil and salt for 25
# minutes" - a vegetable it never names, cooked from raw - and "leftover beetroot" got "Roast
# beetroot whole and unpeeled at 200C for an hour", which is an hour's work rather than a use for
# the beetroot in the fridge. One table, called from here and from cooking.py, so a food with no
# written idea is still answered as the thing it is.
UP_GREENS = ("spinach", "cabbage", "kale", "chard", "greens", "collard", "collards", "savoy",
             "sprout", "sprouts", "broccoli", "broccolini", "cauliflower", "romanesco",
             "kalettes", "spring green", "spring greens", "lettuce", "rocket", "cress",
             "watercress", "pea", "peas", "green bean", "green beans", "mangetout", "asparagus")
UP_ALLIUMS = ("onion", "onions", "leek", "leeks", "shallot", "shallots", "garlic",
              "spring onion", "spring onions", "red onion", "red onions")
UP_ROOTS = ("beetroot", "parsnip", "parsnips", "carrot", "carrots", "turnip", "turnips",
            "swede", "celeriac", "squash", "pumpkin", "sweet potato", "sweet potatoes",
            "potato", "potatoes", "artichoke", "artichokes", "fennel", "jerusalem artichoke",
            "jerusalem artichokes")
UP_SOFT = ("courgette", "courgettes", "zucchini", "aubergine", "aubergines", "pepper",
           "peppers", "mushroom", "mushrooms", "tomato", "tomatoes", "corn", "sweetcorn",
           "butternut", "okra", "bean", "beans")
UP_GRAINS = ("rice", "quinoa", "couscous", "bulgur", "barley", "pasta", "noodle", "noodles",
             "spaghetti", "macaroni", "lentil", "lentils", "chickpea", "chickpeas", "porridge",
             "oat", "oats")
UP_FRUIT = ("cranberry", "cranberries", "apple", "apples", "pear", "pears", "banana",
            "bananas", "berry", "berries", "raspberry", "raspberries", "strawberry",
            "strawberries", "rhubarb", "plum", "plums", "peach", "peaches", "nectarine",
            "nectarines", "mango", "pineapple", "orange", "oranges", "grapes", "cherry",
            "cherries", "apricot", "apricots", "fig", "figs", "melon")
UP_MEAT = ("chicken", "beef", "lamb", "pork", "ham", "bacon", "sausage", "sausages", "turkey",
           "duck", "mince", "steak", "liver", "chorizo", "gammon", "meat", "meatballs")
UP_FISH = ("salmon", "cod", "haddock", "tuna", "prawn", "prawns", "mackerel", "trout", "fish",
           "fishcake", "fishcakes", "sardine", "sardines", "crab", "anchovy", "anchovies")
UP_CLASSES = (
    # Written in the voice of a recipe rather than with "it": the line may say one beetroot or
    # three parsnips, and a pronoun that agrees with the wrong one reads worse than no pronoun.
    (UP_GREENS, "butter or oil in a hot pan for 3 or 4 minutes is enough, or stir through a "
                "soup, an omelette or a pasta sauce just before you serve. Shred raw into a "
                "salad with oil and lemon if you would rather have it cold."),
    (UP_ALLIUMS, "cook slowly in butter until sweet, which takes 15 minutes and is worth it, "
                 "then stir through a soup, a gravy or a tray of roasted veg. On a pizza, a tart "
                 "or a piece of toast it is a topping on its own."),
    (UP_ROOTS, "cut into cubes and fry in a little oil until the edges crisp, or mash with "
               "potato for a bubble and squeak, or simmer into a soup. Cold in a salad with a "
               "sharp dressing is just as good."),
    (UP_SOFT, "fry in a hot pan with garlic and oil until the water is gone, stir into a pasta "
              "or a sauce, or bake under cheese."),
    (UP_GRAINS, "fry hard with an onion and whatever veg you have, loosen into a soup or a stew, "
                "or fold into a salad with oil and lemon. Heat through until piping hot, and bin "
                "it if it has sat out."),
    (UP_FRUIT, "simmer 10 minutes with a spoon of sugar and a splash of water for a compote, "
               "fold into a crumble, or spoon over yoghurt or porridge."),
    (UP_MEAT, "shred or slice into a sandwich, a salad, a fried rice or a curry, and add at the "
              "end so it only heats through. Covered in the fridge it keeps 3 days."),
    (UP_FISH, "flake cold through pasta or a salad with lemon and yoghurt, or mix into a fishcake, "
              "and don't reheat it hard or it dries out."),
)
# Every food this table answers, so the entry that calls it reaches them all.
UP_FOODS = UP_GREENS + UP_ALLIUMS + UP_ROOTS + UP_SOFT + UP_GRAINS + UP_FRUIT + UP_MEAT + UP_FISH
_UP_FOOD_SET = frozenset(UP_FOODS)


# A dish is a use, and a method is not. The pantry row for a food says one or the other: "Leek and
# potato soup: sliced leeks softened in butter" is a way to use up the leeks in the fridge, and
# "Roast beetroot whole and unpeeled at 200C for an hour" is how to cook a beetroot from raw, which
# is not an answer to what to do with the one already in there. So when the pantry's idea names a
# dish, it stays the answer, exactly as it was before this table existed; when it only says how to
# cook the thing, the moves for its kind of food are the better answer. Being generous with this
# list can only keep the answer the bot gave before, so the words are here rather than a curated
# table of a hundred and seventy-five rows.
USE_DISH_WORDS = ("soup", "broth", "stew", "curry", "casserole", "salad", "pasta", "risotto",
                  "traybake", "pie", "gratin", "mash", "remoulade", "pancake", "fritter",
                  "dhal", "dal", "sauce", "compote", "crumble", "hummus", "dip", "fajita", "cake",
                  "bread", "toast", "sandwich", "omelette", "frittata", "pizza", "burger",
                  "pilaf", "snack", "crisp", "chip", "relish", "chutney", "slaw")
# "roast", "bake" and "grill" are deliberately not in it: they are the two verbs almost every from-raw row
# begins with ("Roast beetroot whole and unpeeled for an hour", "Wrap the fish in foil and bake
# it"), so they would stand this table
# down for exactly the lines it exists for. A row that offers a bake or a roast as the use says so
# with a dish word as well ("...then toss them through pasta").


def _up_food(words):
    """The first food in the line this table answers, as the line spells it."""
    for index, word in enumerate(words):
        if word in _UP_FOOD_SET:
            return word
        if index + 1 < len(words) and " ".join(words[index:index + 2]) in _UP_FOOD_SET:
            return " ".join(words[index:index + 2])
    return None


def idea_is_a_dish(idea):
    """True when a pantry idea is a way to use the food up rather than how to cook it raw."""
    return any(word in str(idea or "").lower() for word in USE_DISH_WORDS)


def named_food(words, understood=None):
    """The food a line names, preferring the kind this table knows, or None."""
    named = _up_food(words) or _named(understood or {})
    if isinstance(named, (list, tuple)):
        named = named[0] if named else None
    return named or None


def use_it_up(name):
    """How to use up a spare or cooked food, told by the kind of food it is, naming it."""
    said = str(name or "").strip()
    folded = said.lower()
    for words, move in UP_CLASSES:
        if folded in words:
            return "Leftover %s: %s" % (said, move)
    # A name this table knows as the tail of a longer one ("leftover roast chicken" is a chicken).
    for words, move in UP_CLASSES:
        if any(folded.endswith(" " + word) or folded.startswith(word + " ") for word in words):
            return "Leftover %s: %s" % (said, move)
    return ("Leftover %s: already cooked, so treat it as an ingredient - stir through a soup or "
            "a curry, fry with an onion and an egg, or eat cold in a salad with oil and vinegar."
            % said)


# The words that ask for something in a hurry.
QUICK = ("quick", "quicker", "quickly", "fast", "faster")
# A line that says the day is over wants the shortest dish in the table, not the best one.
BEDTIME = ("off to bed", "to bed soon", "in bed soon", "early night", "bed early", "knackered",
           "shattered", "exhausted", "up early", "early start")

# Being hungry is the ask, however the line is read: "im starving, anything quick" is a request
# for a meal even when the parser files it as news about how they feel.
HUNGRY = ("starving", "starved", "famished", "hungry", "hank marvin", "need to eat",
          "need something to eat", "something to eat", "skip lunch", "skipped lunch",
          "havent eaten", "have not eaten")

# "Something nice for my girlfriend on friday" is not a weeknight hurry: the ask is a meal worth
# making an effort over, so the pick is a proper dish rather than the quickest one on the table.
IMPRESS = ("nice", "fancy", "special", "impress", "impressive", "anniversary", "birthday",
           "date night", "romantic", "treat", "trying to cook something")

# A line that asks for a meal to make an effort over, with no other ask in it: "cooking to
# impress". It is not the whole of IMPRESS, because "nice" and "treat" are said about a chat
# and a biscuit as often as about a dinner.
IMPRESS_ASK = ("impress", "impressing", "to impress", "make an effort", "pull out all the stops",
               "special occasion", "something special", "trying to cook something")
# Cooking for someone in particular is the same ask when the line also says it should be good:
# "something nice for my girlfriend on friday". The pair is needed both ways, because "buy a
# present for my mum" is a shopping line and "dinner with my mum" is a Tuesday.
IMPRESS_FOR = ("for my girlfriend", "for my boyfriend", "for my partner", "for my wife",
               "for my husband", "for my mum", "for my mom", "for my dad", "for my in laws",
               "for my in-laws", "for her", "for him")
IMPRESS_WORTH = ("nice", "fancy", "special", "impressive", "impress", "treat", "birthday",
                 "anniversary", "proper", "best", "good")

# Words that say the line is about training, sleep, travelling or a technique, not a meal.
NOT_A_MEAL = ("exercise", "workout", "workouts", "run", "runs", "walk", "meditate", "shower",
              "study", "clean", "sleep", "nap", "train", "commute", "boil", "bake")

# The dinner ask is a dinner ask: "what do i eat" without a meal named is somebody standing in
# the kitchen at six, but "what do i eat for breakfast" is a breakfast question with its own
# answer, and the same words sit in front of it. So the entry that answers the bare ask stands
# down as soon as the line names a different meal of the day, and that meal's own entry (or the
# whole table's shrug) answers instead of a tray of pasta at eight in the morning.
ANOTHER_MEAL = ("breakfast", "brunch", "snack", "snacks", "lunch", "luncheon", "pudding",
                "dessert", "afters", "afternoon tea", "high tea", "elevenses")

# Not a dish on a plate: a packed lunch, a picnic or a buffet asks for something that travels,
# which is a different table of knowledge. Passing leaves the honest shrug rather than a
# suggestion nobody can carry to work.
# A meal idea is for someone who is eating, not for a diet the food has to respect or a
# question about a technique: the allergy and the temperature facts answer those.
NOT_FOR_ME = ("allergy", "allergic", "allergies", "nut", "nuts", "peanut", "peanuts",
              "intolerance", "intolerant", "coeliac", "celiac", "temp", "temperature")

# Being ill is a health question, not an ingredient: "i have chicken pox and a fever" is not a
# chicken dinner. ("a cold" is not here: "the kids got a cold and theres no school" is a dinner.)
HEALTH = ("pox", "fever", "flu", "vomiting", "diarrhoea", "diarrhea", "migraine", "nausea",
          "nauseous", "throwing up", "sore throat", "cant keep anything down", "sick bug")
# Ways of saying no dairy, none of them a question only a doctor can answer.
NO_DAIRY = ("no dairy", "without dairy", "dairy free", "dairy-free", "lactose", "no milk",
            "without milk", "milk free", "milk-free", "cant have dairy", "cannot have dairy")

# Being unwell is a question about the illness, not a dish pick: "what can i eat after having a
# tooth out" wants soft food and a dentist, and a sausage traybake is the one answer that must
# never come back. The words are read on the whole line, because a symptom is never an
# ingredient.
UNWELL = ("stomach", "tummy", "dodgy stomach", "bad stomach", "upset stomach", "sick", "sickness",
          "being sick", "feel sick", "feeling sick", "throwing up", "nausea", "nauseous",
          "diarrhoea", "diarrhea", "constipated", "constipation", "food poisoning", "have a cold", "got a cold",
          "a bad cold", "chest infection", "tooth", "teeth", "dentist", "wisdom tooth",
          "tooth out", "toothache", "root canal", "filling", "gums", "sore mouth",
          "mouth ulcer", "tonsils", "out of date", "use by", "past their date", "past its date",
          "past the date", "gone off", "off eggs", "still ok to eat", "still safe to eat")

# "im sick of pasta" is being tired of it, not being ill, so the bored sense is read first.
SICK_OF = ("sick of", "tired of", "bored of", "bored with", "fed up with", "had enough of",
           "sick and tired")

# What someone with a condition may eat is a question about the condition, not a dish pick: the
# answer has to know about blood sugar, gluten or kidneys, and guessing at it is worse than
# passing. bot/knowledge/health.py and the safety lane answer these.
CONDITION = ("diabetes", "diabetic", "type 1", "type 2", "blood sugar", "ibs", "irritable bowel",
             "crohns", "crohn's", "colitis", "gout", "kidney", "kidneys", "cholesterol",
             "coeliac", "celiac", "anaphyla", "allergy", "allergic", "pregnant",
             "pregnancy", "breastfeeding")

# An empty kitchen is a shopping list, not a dish: the table cannot pick from a fridge that has
# nothing in it.
EMPTY = ("no food", "nothing in", "empty fridge", "empty cupboards", "bare cupboard",
         "nothing at home", "no shopping", "run out of food")

# A leftover is a use-up question, not an idea question: "what can I make with leftover rice"
# belongs to the leftover facts, which say what is safe and what it turns into.
NOT_AN_IDEA = ("leftover", "left over", "leftovers", "spare", "use up", "using up")

# A food word in a line is not an ask for dinner. "Do I need to wash rice before I cook it",
# "is that normal", "what's wrong with my tomatoes" and "does that matter" all name food and
# want a fact, a diagnosis or reassurance, so the broad asks below stay off them.
HOW_TO = ("need to", "do i need", "is it safe", "still use", "can i use", "wash", "washing",
          "wrong", "normal", "matter", "cheaper", "worth", "difference", "better to",
          "how do i", "why does", "why do", "is that ok", "is that ok", "is it ok",
          # "can i cook chicken from frozen" is a thawing question with its own answer.
          "from frozen", "still frozen", "defrost", "defrosting", "thaw", "thawing")

# They are already cooking: "im cooking a curry tonight" is not an ask for an idea, and a
# suggestion under it reads as though the bot was not listening.
# A soup has its own method cards (`soup-make` and its three siblings), so a line that names one
# is about the soup, not a request to be handed a dish built from an ingredient: "i have chicken
# and want soup" was answered "I'd do a chicken stir-fry".
SOUP_NAMED = ("soup", "soups", "broth", "broths")

OWN_MEAL = ("im cooking", "i'm cooking", "i am cooking", "cooking a", "cooking some",
            "already cooking", "on the hob", "in the oven", "making a", "im making",
            "i'm making", "just made")

# Someone else's eating is a different question: "my son will only eat bread and butter" is
# about a fussy eater, not a request for a recipe with bread in it.
# The words are the person's eating, never the request: "my son is a picky eater" wants the
# fussy-eater advice, but "what should i cook for a picky child" is a dinner ask with a fussy
# child in it, and cooking.py's own fussy-eater entry still gets the first of the two.
OTHER_PEOPLE = ("only eat", "only eats", "only ate", "wont eat", "won't eat", "doesnt eat",
                "doesn't eat", "refuses to eat", "refuses")

# A fridge that is on the blink is a repair, not a recipe ("the fridge is making a funny noise").
BROKEN = ("noise", "noisy", "rattling", "broken", "broke down", "not working", "stopped working",
          "leaking", "leak", "repair", "repairs", "warranty", "engineer", "fuse", "socket",
          "smells", "smelly", "won't close", "wont close")

# "I've got pork chops, what goes with them" wants the side dish, not a new main.
WHAT_GOES = ("goes with", "go with", "serve with", "goes nicely")

# A pet is not an ingredient and a name is not a fridge list ("i've got two cats, milly and tom").
NOT_MY_KITCHEN = ("cat", "cats", "dog", "dogs", "kitten", "puppy", "pets", "hamster", "rabbit",
                  "called", "named", "nickname")

# A question about weighing and converting is arithmetic about a recipe, not a request for a
# dish: "my kitchen scales broke and every recipe i have is in grams".
MEASURING = ("scales", "weigh", "weighing", "weighed", "convert", "converting", "conversion",
             "grammes", "ounces", "tablespoon", "tablespoons", "teaspoon", "teaspoons",
             "ml", "litres", "millilitres")

# A line about a drink names food words too ("i have tea with milk every morning"), so a line
# A line about sleep is about sleep: "is tea before bed a bad idea" wants the caffeine answer,
# not a dish, and it says tea and idea and nothing else that would keep it away.
SLEEP = ("bed", "before bed", "bedtime", "sleep", "asleep", "awake", "waking", "insomnia")

# with a drink in it is not a request for dinner. meal-tea leaves "tea" out of its own avoid,
# because there tea is the meal.
DRINK = ("tea", "brewing", "brewed", "tea bag", "tea bags", "kettle", "mug",
         "drinking", "drinks") + SLEEP

# "packed" alone would kill "i have a pack of cod" (a loose form of the word), so the packed
# lunch is spelled out.
# A plant that is sick is the garden's question, not a dinner: "my tomatoes have blight" got "try a
# tuna salad" and "my potatoes have blight" got a vegetable soup, because the meal table keys a food
# word and a "have". These words are the trouble on the plant, never the produce in the pan.
AILING_PLANT = ("blight", "mildew", "mould", "mold", "mouldy", "moldy", "rot", "rots", "rotting",
                "rotted", "rust", "wilt", "wilting", "yellowing", "yellow leaves",
                "yellowed", "drooping", "dying", "disease", "diseased", "infected", "infection",
                "aphids", "blackfly", "whitefly", "slugs", "snails", "caterpillars",
                "not growing", "stopped growing", "flowering", "fruiting", "prune", "pruning",
                "compost", "allotment", "greenhouse", "polytunnel", "raised bed", "sowed",
                "sowing", "planted", "planting", "growing", "grow", "harvest", "crop", "crops")

NOT_A_DISH = NOT_A_MEAL + ("packed lunch", "packed lunches", "pack lunch", "packing lunch",
                           "lunchbox", "lunchboxes", "lunch box", "lunch boxes", "school lunch",
                           "bento", "picnic", "buffet", "canape",
                           "finger food", "party food")

# One list of the lines this table is not the answer to, for cooking.py's own meal-ideas entry
# (which now delegates its reply here) to carry as its avoid list.
# A dish that has gone wrong is a repair, and the cooking table owns repairs: "2 much salt in the
# soup, what do i do" wants the fix, not a different dinner. The words are the fault, never the
# food, so they are read on the whole line.
REPAIR = ("too much salt", "much salt", "much spice", "much chilli", "much pepper", "much sugar",
          "too salty", "over salted", "oversalted", "too spicy", "too hot to eat",
          "too thin", "too thick", "too sweet", "too sour", "burnt", "burning", "caught on the",
          "sticking to the pan", "stuck to the pan", "soggy", "curdled", "split", "went wrong",
          "messed up", "ruined", "dried out", "overcooked", "undercooked", "not cooked",
          "still raw", "raw in the middle", "tastes off", "smells off", "went off")

# A journey that went wrong or a booking somebody wants their money back for is not a lunch to
# pack. The words are the claim, not the journey, so they are read on the whole line.
MONEY_MATTERS = ("refund", "refunds", "refunded", "money back", "get my money",
                 "reimbursed", "reimbursement", "compensation", "compensated", "claim",
                 "claimed", "claiming", "charge", "charges", "charged", "fee", "fees",
                 "voucher", "insurance", "rebook", "rebooking", "no show", "no-show",
                 "missed", "delay", "delayed", "cancelled", "canceled", "cancellation",
                 "didnt take", "didn't take", "did not take", "didnt go", "couldnt go",
                 "could not go")

# A line asking what to say is asking for words, not for a dish. "in laws" is a key of the
# impressive-dinner entry and "what" one of its asking words, so "what do i say to my mother in
# law who criticises everything" was answered "Quick: tuna pasta in 15, a frittata in 20", and
# "what do i say to my mother in law" the same with no food in the line at all. A dinner that is
# the subject of the conversation ("my mother in law is coming for dinner, what do i cook") has
# no asking-for-words shape in it, so it keeps the table.
SAYING = ("what do i say", "what should i say", "what can i say", "what shall i say",
          "what do i tell", "what should i tell", "what can i tell", "what shall i tell",
          "what to say", "what to tell", "how do i say", "how should i say",
          "what do i reply", "what should i reply", "what to reply")

NOT_MINE = tuple(dict.fromkeys(
    NOT_A_DISH + NOT_AN_IDEA + OWN_MEAL + OTHER_PEOPLE + HOW_TO + WHAT_GOES + BROKEN + HEALTH
    + EMPTY + MEASURING + REPAIR + UNWELL + SAYING))

# "im cooking" is on the not-mine list because "im cooking salmon, how long" is a technique
# question, but "im cooking for one tonight" is a dinner ask. One-person asks keep the guard
# everywhere else and drop only these openers.
# "run out of" is a limit in a kitchen ("im out of cheese") but a run is exercise, so the
# out-of entry keeps every guard except the run words.
# The delegating meal-ideas entry in cooking.py uses this shorter list: a buffet, a picnic or a
# "how do i plan meals for the week" is still that entry's line, because cooking.py's own crowd,
# pantry and plan answers sit behind it. The dish table passes on them in suggest(); the entry
# itself must not, or the line reaches nothing at all.
NOT_MINE_ENTRY = tuple(w for w in NOT_MINE
                       if w not in ("buffet", "canape", "canapes", "finger food", "party food",
                                    "how do i", "how to"))
NOT_MINE_OUT = tuple(w for w in NOT_MINE if w not in ("run", "runs", "out of", "ran out of"))
NOT_MINE_ASK = tuple(w for w in NOT_MINE
                     if w not in ("im cooking", "i'm cooking", "i am cooking", "cooking a",
                                  "cooking some", "already cooking",
                                  # "something cheaper" after an idea is a limit, not a
                                  # question about whether cooking is cheaper than a takeaway.
                                  "cheaper", "worth", "afford"))
# "cheaper" is a how-to question ("is it cheaper to cook") and a budget limit; only the
# second one is a dinner ask.
NOT_MINE_CHEAP = tuple(w for w in NOT_MINE_ASK if w not in ("cheaper",))

# Every opener has to read as a sentence with the dish name after it: "Easy one: mushroom
# risotto." is a label, not an answer, and it is the sentence a later turn would quote back.
OPENERS = ("Try", "I'd do", "Go for", "How about", "Go with")
TIMES = ("About {n} minutes.", "Roughly {n} minutes in all.", "{n} minutes, give or take.")
# Most methods name their own cook time ("simmer for 25 minutes"), and then "35 minutes, give or
# take" after it reads as a contradiction rather than a total. When the method has a time in it,
# the tail says plainly that it is the whole thing.
TOTAL_TIMES = ("Roughly {n} minutes in all.", "About {n} minutes in all.",
               "{n} minutes from start to finish.", "Roughly {n} minutes, start to finish.")
COOK_TIME = re.compile(r"\d+\s*(?:to\s*\d+\s*)?(?:min|minute|hour|hr)")
# The second sentence stands on its own, because a later turn may quote only that one: an
# alternative that begins "Or" reads as a fragment when the sentence before it is dropped.
FOLLOW_ON = ("If you'd rather have something else, {alt} takes {n} minutes.",
             "Something else that works is {alt}, at {n} minutes.")
# Only said when they have actually ruled cheese out: an alternative is not a licence to
# invent a dislike ("No cheese on that?" after "something quick please" is nonsense).
FOLLOW_ON_NO_CHEESE = "Without the cheese, there is {alt}, at {n} minutes."


def _variant(options, understood, memory):
    """One of options, varied by the line itself rather than by the turn count alone."""
    turns = memory.get("turns") or []
    clean = (understood.get("clean") or "") if isinstance(understood, dict) else ""
    seed = len(turns) * 7919 + sum(ord(c) for c in clean)
    return random.Random(seed).choice(list(options))


# A dinner party is a meal; what to wear to it, or what to take, is not.
NOT_A_MEAL_SUBJECT = ("what to wear", "wear to", "to wear", "dress code", "outfit", "dinner roll",
                      "dinner lady", "dinner jacket", "what to bring", "what should i bring",
                      "bring to a", "take to a dinner party")

# A dessert is the end of the dinner, not another dinner: "what can i make for dessert" got a
# tuna pasta here, which is the one thing nobody wants after a plate of it. The pudding entries
# in cooking.py answer these lines, so this table stands down.
DESSERT_ASK = ("dessert", "desserts", "pudding", "puddings", "afters", "something sweet",
               "sweet thing", "sweet treat", "ice cream")

# A way of asking how, not what: cooking.py owns the timings, temperatures and water.
# A line that wants to make the thing itself is the making row's question, not a dinner pick. This
# table answered them with a dish: "can i make my own cheese" was "I'd do an omelette", "can i make
# my own baked beans" a baked potato with beans. The making rows in cooking.py know the method (and
# a food with no making row gets the honest hedge, which is better than a dinner nobody asked for).
MAKING_AT_HOME = ("make my own", "make our own", "making my own", "making our own", "made my own",
                  "made our own", "make it myself", "make them myself", "make it ourselves",
                  "make them ourselves", "make your own", "making your own", "from scratch")

TECHNIQUE_ASK = ("how long", "how do i", "how do you", "how to", "how many minutes",
                 "what temperature", "what temp", "how much water", "how much rice",
                 "how much pasta", "should i boil", "do i need to soak")
# A use-up ask wears the how-do-i shape and is not a technique question: "how do i use up
# leftover chicken" wants a dish, and the technique gate above stood the table down for it, so
# the line got a shrug while "what can i make with leftover chicken" got the stir-fry. The
# clock questions stay where they were - "how long do i cook chicken for" has no use-up in it.
USE_UP_ASK = ("use up", "using up", "used up", "eat up", "eating up")

# Ways of saying a thing is not in the kitchen: "i dont have any cheese", "we havent got
# rice", "theres no milk left". Said after an idea, that is a limit on the idea like any
# other, and these are the plainest ways people say it.
NO_HAVE = ("dont have", "don't have", "didnt have", "didn't have", "havent got",
           "haven't got", "havent any", "haven't any", "have no", "got no", "there is no",
           "theres no", "there's no")

# The words people put between the "no" and the food it is about: "i dont have ANY cheese",
# "there is no MORE milk". Two at most, so "no idea how much cheese" is still not a limit.
NO_HAVE_GAP = r"(?: (?:any|a|an|the|some|more|of|that|this)){0,2}"


@functools.lru_cache(maxsize=None)
def _no_have(cue, shape):
    """The "no X" pattern for one cue and one ingredient, compiled once.

    `_ruled_out` asks for one pattern per cue and per ingredient form - about 13k of them for a
    single meal line - and `re` caches only 512 compiled patterns, so every one of those was
    compiled again on every turn: 5-7 s of a reply that reads a line and picks a dish. The
    pattern depends on nothing but these two words, so it is built once and kept.
    """
    return re.compile(r"(?<![a-z])" + re.escape(cue) + NO_HAVE_GAP
                      + r" " + re.escape(shape) + r"(?![a-z])")


# A negative in front of a dislike is a liking: "i dont dislike mushrooms whats for dinner" is a
# person who wants mushrooms, and the dislike word alone ruled them out. The phrases are blanked
# before the cues are looked for, so nothing about that food is read as a limit.
DOUBLE_NO = ("dont dislike", "do not dislike", "doesnt dislike", "does not dislike",
             "dont hate", "do not hate", "doesnt hate", "does not hate", "dont mind",
             "do not mind", "doesnt mind", "does not mind")


def _ruled_out(text):
    """The ingredients the line rules out: "anything but pasta", "ive had enough rice"."""
    plain = " " + " ".join(WORD.findall(text.replace("'", ""))) + " "
    for phrase in DOUBLE_NO:
        if f" {phrase} " in plain:
            plain = plain.replace(f" {phrase} ", " ")
    out = set()
    for ingredient, forms in INGREDIENTS.items():
        for form in forms:
            if not form.isalpha() and " " not in form:
                continue
            if not form.isalpha():
                shape = form.replace("'", "")
            else:
                shape = form
            # A cue can only rule out a food the line names: "no cheese" says nothing about the
            # rice. Both tests below already need the shape to sit in the line as a whole word,
            # so asking that first decides nothing new - and it skips the pattern the second
            # test builds, which is where a meal line used to ask `re` for seventeen thousand
            # patterns about foods that were not in it.
            if f" {shape} " not in plain:
                continue
            for cue in NO_CUE:
                if any(f" {cue}{gap} {shape} " in plain for gap in NO_GAP):
                    out.add(ingredient)
                    break
            else:
                # The same thing said as a missing ingredient rather than as a taste: the food
                # can have a word or two between it and the "no" ("any", "more").
                for cue in NO_HAVE:
                    if _no_have(cue, shape).search(plain):
                        out.add(ingredient)
                        break
    return out


def _the_fish_are_out(clean, diet=""):
    """True when it is fish itself that is out, not one fish named by itself.

    "i dont eat fish", "no seafood" and "allergic to fish" are about the family, so every fish in
    FISH_INGREDIENTS goes; "i dont eat salmon" is about the salmon, and the other fish stay.
    """
    plain = " " + " ".join(WORD.findall(clean.replace("'", ""))) + " "
    for cue in NO_CUE:
        for family in ("fish", "seafood"):
            if f" {cue} {family} " in plain:
                return True
    diet = (diet or "").lower()
    return "fish" in diet or "seafood" in diet


def _is_the_ruled_out_food(word, text):
    """Whether a food word in the line is one of the foods the line rules out.

    `_ruled_out` answers with the pantry's name for the food, and a line says one of its forms:
    "i cant stand fish what can i cook" rules out `white fish`, and "fish" is a form of it. The
    caller has the word from the line and needs to know whether it is the same food, which is not
    the same question as whether the two spellings match.
    """
    word = word.strip().lower()
    if not word:
        return False
    for ingredient in _ruled_out(text):
        for form in INGREDIENTS.get(ingredient, ()) + (ingredient,):
            form = form.strip().lower()
            if form == word or form.startswith(word) or word.startswith(form):
                return True
    return False


def _named(understood):
    """The canonical ingredients the line names, in the order they are mentioned.

    It reads the words as typed and the tidied line the understanding engine keeps in
    "norm", so a slip it has already fixed ("tomartoes", "potatos") still finds the thing.
    """
    words = list(understood.get("words") or [])
    tidied = understood.get("norm_text")
    if not isinstance(tidied, str):
        tidied = " ".join(understood.get("norm") or [])
    for word in WORD.findall(tidied):
        if word not in words:
            words.append(word)
    text = " ".join(words)
    found = []
    # Phrases first, so "sweet potato" is a sweet potato and not a potato with an adjective in
    # front of it, and "baked beans" are beans rather than something in the oven.
    for ingredient, forms in INGREDIENTS.items():
        phrases = [form for form in forms if not form.isalpha()]
        hit = [phrase for phrase in phrases if phrase in text]
        if hit:
            found.append(ingredient)
            for phrase in hit:
                text = text.replace(phrase, " ")
                words = [w for w in words if w not in phrase]
    for ingredient, forms in INGREDIENTS.items():
        if ingredient in found:
            continue
        if any(form in words for form in forms if form.isalpha()):
            found.append(ingredient)
    return found


def _clock(numbers):
    """The minutes a line allows, from "20 minutes" or "half an hour", else None."""
    for number in numbers or ():
        if not isinstance(number, dict):
            continue
        if number.get("unit") not in ("minutes", "minute", "min", "mins"):
            continue
        try:
            value = int(number.get("value"))
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return None


_NO_MEAT_BLOCKER = ("time", "times", "rush", "money", "energy", "idea", "clue", "chance",
                    "reason", "need", "way", "point", "room", "doubt", "harm", "but")


def _no_meat(text):
    """A line that rules meat out, in whatever order the words come.

    "im vegetarian" and "no meat" are the plain forms. "she doesnt eat meat" puts the meat
    after the negative, so the words just after a "no", "without" or "doesnt eat" are read
    too. Only whole words count and only a few words of slack, so "i know meat is pricey" and
    "i have no time to cook chicken" are not a diet.
    """
    if any(cue in text for cue in NO_MEAT):
        return True
    words = [word.strip(",.!?;:") for word in text.split()]
    for cue in NO_CUE:
        cue_words = cue.split()
        width = len(cue_words)
        for start in range(len(words) - width + 1):
            same = words[start:start + width] == cue_words
            # "nothing with meat in it" carries the same "no" as "no meat".
            if not same and width == 1 and words[start] in ("nothing", "none", "nobody"):
                same = True
            if not same:
                continue
            after = words[start + width:start + width + 5]
            if any(word in _NO_MEAT_BLOCKER for word in after):
                continue
            if "meat" in after or "chicken" in after:
                return True
    return False


def _later(memory, understood):
    """A limit said after an idea ("and quick", "and something vegetarian") means something
    only when an idea is on the table or the line is about food at all.

    Without this, "whats a quick and easy way to learn excel" reads as a request for a
    quicker dinner, because "quick" and "and" are enough to match.
    """
    plan = memory.get("meal_plan") if isinstance(memory.get("meal_plan"), dict) else {}
    if plan.get("offered"):
        return suggest(memory, understood)
    text = " ".join(understood.get("words") or [])
    if any(word in text for word in FOOD_WORDS) or any(
            cue in text for cue in ("dinner", "tea", "supper", "lunch", "meal", "recipe",
                                    "cook", "eating", "eat", "food")):
        return suggest(memory, understood)
    return None


# The words that make a line the lunch question rather than the dinner one.
LUNCH_ASK = ("lunch", "lunchbox", "lunchboxes", "lunch box", "lunch boxes", "packed lunch",
             "school lunch", "lunchtime", "lunch time", "brunch")


# Words that make a turn a request for ideas rather than a statement about how they eat.
IDEA_ASK = ("idea", "ideas", "suggest", "suggestion", "recommend", "options", "option",
            "recipes", "inspiration")


def _limits(understood, memory):
    """What this line rules out: (allowed diets or None, ingredients to avoid, max minutes).

    An earlier turn of the same request keeps its limits ("dinner?" -> "without meat" ->
    "and quick"), for a few turns, and only while the line adds no ingredients of its own:
    naming new food starts a fresh request.
    """
    clean = understood.get("clean") or ""
    text = " ".join(understood.get("words") or [])
    allowed, without = None, set()
    # What this line itself names: an ingredient named again is not one they are out of.
    said_now = set(_named(understood))

    if _no_meat(clean):
        allowed = {"vegan", "vegetarian"}
    if "vegan" in text or any(cue in clean for cue in NO_DAIRY):
        # "lactose intolerant" and "dairy free" are the same limit as "vegan" for this table:
        # no milk, butter or cheese in the pick.
        allowed = {"vegan"}
    if "no fish" in clean or "without fish" in clean or "no seafood" in clean:
        allowed = set(allowed or {"vegan", "vegetarian", "fish"}) - {"fish"}
    if any(cue in clean for cue in NO_CHEESE):
        without.add("cheese")
    # Any ingredient the line puts behind "no", "without", "arent" or "sick of".
    without.update(_ruled_out(clean))
    minutes = _clock(understood.get("numbers"))
    # "quicker please" means quicker than the idea they were just given, not quicker than
    # nothing, so it is read before a plain "quick" gets there first and allows the same time.
    if minutes is None and ("quicker" in text or "faster" in text):
        plan_now = memory.get("meal_plan")
        was = (plan_now or {}).get("pick") if isinstance(plan_now, dict) else ""
        order = ([was] if was else []) + list(
            reversed((plan_now or {}).get("offered") or () if isinstance(plan_now, dict) else ()))
        for name in order:
            item = next((dish for dish in DISHES if dish.name == name), None)
            if item is not None:
                minutes = item.minutes - 1
                break
    # "quick" says how long, not what for: it is a clock only when the line is about food, or
    # when an idea from this request is already on the table. "quick one, how often should i
    # do it" about a kettle is neither.
    if minutes is None and any(word in text for word in QUICK) and (
            memory.get("meal_plan") or any(word in text for word in FOOD_WORDS)
            or any(cue in text for cue in ("dinner", "tea", "supper", "lunch", "meal",
                                           "recipe", "eating", "cook"))):
        minutes = 20
    if minutes is None and ("half an hour" in clean or "30 minutes" in clean):
        minutes = 30
    # A night that is nearly over is a clock: "i am off to bed soon, what should i cook" wants
    # the ten-minute answer, not a 25-minute one, so a bedtime or a bone-tired line caps it.
    if any(cue in clean for cue in BEDTIME):
        minutes = min(minutes or 15, 15)

    # What they told the bot about themselves once holds every time, not just for the turn they
    # said it: "im vegetarian" a moment ago is still true of tonight's dinner.
    about = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    diet = str(about.get("diet") or "").lower()
    if allowed is None and diet:
        if "vegan" in diet:
            allowed = {"vegan"}
        elif "vegetarian" in diet:
            allowed = {"vegan", "vegetarian"}
    if "dairy" in diet or "lactose" in diet or "cheese" in diet:
        without.add("cheese")
    if _the_fish_are_out(clean, diet):
        without.update(FISH_INGREDIENTS)
    for allergy in about.get("allergies") or ():
        name = str(allergy).lower().rstrip("s")
        if name in INGREDIENTS:
            without.add(name)

    # Someone else in the party they have already told the bot about is a limit on the dish too.
    # "my mum wont eat meat any more" is stored against her, and the next line's "what can i
    # cook" is still cooking for the same table, so the pick has to be one she can eat: the
    # answer used to be tuna pasta. Only the diets a dish can be picked by are read here, and
    # only the meat-free ones, because "no fish" and "no dairy" change a dish rather than pick it.
    for person in memory.get("others") or ():
        theirs = str((person or {}).get("diet") or "").lower() if isinstance(person, dict) else ""
        if not theirs:
            continue
        if "vegan" in theirs or "plant" in theirs:
            allowed = {"vegan"}
        elif "vegetarian" in theirs or _no_meat(theirs):
            if allowed is None:
                allowed = {"vegan", "vegetarian"}
        if "dairy" in theirs or "cheese" in theirs:
            without.add("cheese")
        if "fish" in theirs or "seafood" in theirs:
            without.update(("fish", "tuna", "salmon", "prawn", "cod"))

    # The same goes for what they said in an earlier turn of this conversation: a limit that
    # was said once ("im vegetarian") keeps holding while the turns carry on.
    if allowed is None or not without:
        for turn in reversed((memory.get("turns") or [])[-6:]):
            said = str((turn or {}).get("user") or "").lower() if isinstance(turn, dict) else ""
            if not said:
                continue
            # "vegetarian dinner ideas" is a request, not a fact about the person, and it must
            # not become a diet that holds for the rest of the conversation: "what can i make
            # with bacon" after it was answered "since you are vegetarian, I'd leave that out".
            if _no_meat(said) or "vegan" in said:
                if not any(cue in said for cue in IDEA_ASK):
                    if allowed is None and _no_meat(said):
                        allowed = {"vegan", "vegetarian"}
                    if "vegan" in said:
                        allowed = {"vegan"}
            if any(cue in said for cue in NO_CHEESE) or "no dairy" in said:
                without.add("cheese")
            # "i have no eggs" a turn earlier still holds: an ingredient they said they were
            # out of is out, unless they name it again.
            for gone in _ruled_out(said):
                if gone not in said_now:
                    without.add(gone)

    plan = memory.get("meal_plan")
    wanted = [name for name in _named(understood) if name not in without]
    if isinstance(plan, dict) and not wanted \
            and len(memory.get("turns") or []) - plan.get("turn", 0) <= 3:
        if allowed is None and plan.get("allowed"):
            allowed = set(plan["allowed"])
        without.update(plan.get("without") or ())
        minutes = minutes if minutes is not None else plan.get("minutes")
    return allowed, without, minutes


def _fits(item, allowed, without, minutes, grace=0):
    if allowed is not None and item.diet not in allowed:
        return False
    if without and set(item.uses) & without:
        return False
    if minutes is not None and item.minutes > minutes + grace:
        return False
    return True


def _rotate(items, understood, memory):
    """The list turned to start at a place that follows the line, so the same ask varies."""
    if not items:
        return items
    seed = len(memory.get("turns") or []) * 7919 + sum(ord(c) for c in understood.get("clean", ""))
    start = seed % len(items)
    return list(items[start:]) + list(items[:start])


# How much over the clock a dish may run before it stops counting as quick, and the words that
# mean the clock is a hard limit rather than a wish ("under 20 minutes" is not "20-ish").
GRACE = 10
HARD_CLOCK = ("under", "only", "max", "maximum", "less", "tops", "just")

# What a kitchen has in anyway: a dish that needs one of these on top of what they named is
# still dinner, while one that needs a whole ingredient they never mentioned is a shopping trip.
STAPLE = frozenset("""
onion garlic butter milk egg cheese pasta rice bread tomato potato bean pea carrot lemon flour
oil stock herb spice pepper salt noodle tortilla butter
""".split())


def _spread(ranked):
    """Three dishes, quickest first: the ten-minute one, the twenty-minute one, the slower one.

    Three is what a person says when a friend asks what to cook: enough to choose between,
    short enough to read. Two of them are in the quick half of the table, so the list is not
    three variations on the same slow supper.
    """
    picks = []
    shapes = set()
    for low, high in ((0, 15), (16, 25), (26, 95)):
        fits = [item for item in ranked if low <= item.minutes <= high]
        # Two soups in one list is one idea said twice: a band gives a shape that no other pick
        # has taken, and only repeats a shape when that is all the table has for the band.
        distinct = [item for item in fits if _shape(item) not in shapes]
        for pool in (distinct, fits):
            if pool:
                chosen = [item for item in pool if item.favourite] or pool
                picks.append(chosen[0])
                shapes.add(_shape(chosen[0]))
                break
    return picks


# The shape of a dish, so three picks are three different plans: "pea and mint soup" and
# "vegetable soup" are the same evening to anyone reading the answer.
DISH_SHAPES = ("soup", "stew", "curry", "pasta", "traybake", "salad", "stir-fry", "risotto",
               "hash", "bake", "pie", "toast", "sandwich", "omelette", "tortilla", "frittata",
               "potato", "rice", "noodles", "bolognese", "chowder", "parmigiana", "mash")


def _shape(item):
    words = item.name.replace("-", " ") + " " + item.name.replace("-", " ").replace(" ", "")
    for shape in DISH_SHAPES:
        if shape.replace(" ", "") in item.name.replace("-", " ").replace(" ", ""):
            return shape
    return ""


def _best(names, allowed, without, minutes, memory, understood):
    """The dish that uses most of what they named, fewest extra ingredients, then quickest.

    With nothing named, a favourite first, in the order a friend would offer them; a dish
    already offered in this request goes to the back.
    """
    plan = memory.get("meal_plan")
    offered = set(plan.get("offered") or ()) if isinstance(plan, dict) else set()
    # The bot may ask this module twice for the same line (a proposal, then the reply it
    # actually gives). What the first pass planned is not something the user has seen, so it
    # must not push that dish to the back and change the answer mid-turn.
    if isinstance(plan, dict) and plan.get("turn", -1) >= len(memory.get("turns") or []):
        offered = set()
    # A dish named by its style ("i fancy a curry", "a soup please") is the answer, so that
    # style is looked at first: without it a curry ask gets whatever fits the clock.
    said = " ".join((understood or {}).get("words") or ())
    style = [cue for cue in DISH_STYLE if cue in said]
    for word, shapes in STYLE_CUES.items():
        if word in said:
            style += [shape for shape in shapes if shape not in style]
            style = [shape for shape in style if shape in DISH_STYLE or any(
                shape in item.name for item in DISHES)]
    named = set(names)
    # A dish a few minutes over the clock still counts as the quick one they asked for when it
    # means not sending them shopping ("mince in 20 minutes" is bolognese, not a new vegetable).
    words = set((understood or {}).get("words") or ())
    hard = bool(words & set(HARD_CLOCK))
    grace = GRACE if named and not hard else 0
    pool = [item for item in DISHES if _fits(item, allowed, without, minutes, grace)]
    if not pool:
        pool = [item for item in DISHES if _fits(item, allowed, without, None)] or list(DISHES)
    # A style named by them ("i fancy a soup") beats the clock: they asked for a soup, so a
    # soup ten minutes over a twenty-minute ask is still the answer they wanted.
    # A cue said a turn or two ago still holds: "im skint until payday" then "what can i cook"
    # is still a cheap dinner, and "im trying to eat better" then "what should i cook" is still
    # a light one. The words of the current line are already in here.
    across = _said_about(memory, said)
    if any(cue in across for cue in CHEAP_ASK):
        thrifty = [item for item in pool if cheap(item)] or [item for item in DISHES if cheap(item)]
        if thrifty:
            pool = thrifty
    if any(cue in across for cue in LIGHT_ASK):
        light = [item for item in pool if item.name in LIGHT_SET]
        if light:
            pool = light
    if style:
        # A dish shape they said out loud beats the clock: "i fancy a soup, i have 20 minutes" is
        # a soup twenty minutes over, not a salad. A vague adjective does not - "something hot"
        # only leans towards a curry, and "its only ten minutes but i want something hot" was
        # answered with a 30-minute curry. So a style has to fit the clock unless the shape was
        # named, and a style that fits nothing falls back to the clock instead of overriding it.
        named_shape = any(cue in said for cue in DISH_STYLE)
        styled = [item for item in DISHES
                  if any(cue in item.name.replace("-", " ") for cue in style)
                  and _fits(item, allowed, without, None if named_shape else minutes, grace)]
        if styled:
            pool = styled
    if named:
        # What they have matters more than the clock: a dish that uses it and takes ten minutes
        # longer beats a quick dish that ignores it ("mince and nothing fancy" -> not beans).
        using = [item for item in pool if named & set(item.uses)]
        if not using:
            using = [item for item in DISHES if named & set(item.uses)
                     and _fits(item, allowed, without, None)]
        if using:
            pool = using
    # The only dishes that fit are the ones just offered: they asked for an idea, not for the
    # same idea twice ("i've got chickpeas" then "something quick please"), so widen out.
    if offered and all(item.name in offered for item in pool):
        fresh = [item for item in DISHES if item.name not in offered]
        still = [item for item in fresh if named & set(item.uses)]
        if named and fresh and not still:
            # They named the food again and every dish this table has for it is already on the
            # table: the answer is one of those dishes said again, never a supper that leaves
            # the mince in their fridge ("ive got mince in the fridge" after bolognese and
            # chilli is mince and cabbage, not beans on toast).
            pool = [item for item in pool if named & set(item.uses)] or pool
        else:
            # Keep what they have as long as there is another dish that uses it; only drop the
            # ingredient when the clock leaves nothing ("chickpeas" has one quick dish).
            wider = ([item for item in fresh if named & set(item.uses) and _fits(item, allowed, without, minutes)]
                     or [item for item in fresh if named & set(item.uses)]
                     or [item for item in fresh if _fits(item, allowed, without, minutes)]
                     or fresh)
            if wider:
                pool = wider
    if not named:
        favourites = _rotate([item for item in pool if item.favourite], understood, memory)
        others = _rotate([item for item in pool if not item.favourite], understood, memory)
        order = favourites + others
        order.sort(key=lambda item: item.name in offered)
        return order

    def rank(item):
        used = len(named & set(item.uses))
        extra = set(item.uses) - named
        # A dish already offered in this request goes to the back, however well it fits, and an
        # extra ingredient nobody mentioned counts against it more than a cupboard staple.
        # Between two dishes that each use one of the named ingredients, the one that uses the
        # first ingredient they named wins: the ask is about that one first.
        lead = bool(names) and names[0] in item.uses
        # A dish named after what they have is the plainest answer to "what can i cook with
        # spinach": the spinach and chickpea curry before a frittata that also happens to take
        # spinach, even though the frittata is quicker and wants one thing fewer. It comes after
        # the shopping, though: a dish that carries the food in its name but wants a whole extra
        # ingredient they never mentioned is not the plainest answer to "what can i make with
        # mince" - bolognese is, and "mince and cabbage" is the one that sends them out for
        # cabbage.
        titled = any(word in item.name for word in names)
        return (item.name in offered, -used, not lead, len(extra - STAPLE), len(extra),
                not titled, item.minutes)

    return sorted(pool, key=rank)


# How an ingredient reads in a sentence: "with mince", "with chickpeas", "with potatoes".
UNCOUNTABLE = frozenset("""
mince beef pork lamb chicken turkey bacon ham fish salmon tuna rice pasta bread cheese milk
butter spinach broccoli cabbage kale leek garlic onion sugar flour yoghurt courgette aubergine
""".split())


def _prose(names):
    """The ingredients as a person would say them: "chickpeas and tomatoes", not "chickpea"."""
    said = []
    for name in sorted(names):
        if name in UNCOUNTABLE:
            said.append(name)
        elif name in ("potato", "tomato"):
            said.append(name + "es")
        else:
            said.append(name + "s")
    if len(said) > 1:
        return ", ".join(said[:-1]) + " and " + said[-1]
    return said[0] if said else ""


def _stick(memory, names, allowed, without):
    """The dish just offered, if it is what uses the ingredient they still have."""
    plan = memory.get("meal_plan") if isinstance(memory.get("meal_plan"), dict) else {}
    for name in reversed(plan.get("offered") or ()):
        item = next((dish for dish in DISHES if dish.name == name), None)
        if item is not None and set(names) & set(item.uses) and _fits(item, allowed, without, None):
            return item
    return None


# A method may offer dairy as an extra ("crumble cheese over it if you eat it"). Said to
# someone who has just ruled dairy out, that is the dish offering what it was told to avoid,
# so the clause goes and the dish stays.
DAIRY_EXTRAS = (", and crumble cheese over it if you eat it",)


def _without_dairy(text, without):
    if "cheese" not in without and "milk" not in without:
        return text
    for extra in DAIRY_EXTRAS:
        text = text.replace(extra, "")
    return text


def _times(how):
    """The tail that fits the method: a total when the method already named its own cook time."""
    return TOTAL_TIMES if COOK_TIME.search(how or "") else TIMES


def _describe(item, understood, memory, without=()):
    turns = memory.get("turns") or []
    last = (turns[-1].get("bot") if turns else "") or ""
    openers = [option for option in OPENERS if not last.startswith(option)] or list(OPENERS)
    opener = _variant(openers, understood, memory)
    when = _variant(_times(item.how), understood, memory).format(n=item.minutes)
    how = _without_dairy(item.how, without)
    how = how[0].upper() + how[1:]
    return f"{opener} {item.said}: {how}. {when}"


def use_up(memory, understood):
    """What to do with an ingredient they already have cooked: "leftover roast chicken".

    The written rows above say the most about the foods people ask about most; every other food
    the kitchen knows is answered from its kind, with its own name in the first words, because a
    use-up question that comes back as how to cook the thing from raw is the wrong question
    answered well ("leftover beetroot" was an hour in the oven).
    """
    words = list(understood.get("words") or [])
    text = " ".join(words)
    said = None
    # The food as they said it, so "leftover sweet potatoes" is not the potato row and its answer
    # is not about potatoes.
    up = _up_food(words)
    for forms, how in USE_UP:
        if up is not None and up not in forms:
            continue
        hit = [form for form in forms if form in words] or [form for form in forms if form in text]
        if hit:
            said = hit[0]
            memory["meal_plan"] = {"turn": len(memory.get("turns") or []), "ingredients": [],
                                   "allowed": None, "without": [], "minutes": None,
                                   "offered": [said]}
            return f"Leftover {said}: {how[0].lower()}{how[1:]}."
    # The food as they said it: the kitchen's ingredient table is the first reader, and a word
    # from the class table is the second, so a food the meal table has never heard of (beetroot,
    # quinoa, cranberries) still gets its own name back in the answer.
    named = up or _named(understood)
    if named:
        said = named[0] if isinstance(named, list) else named
        # The pantry has an idea for most foods. Where that idea is a dish it is the answer, and
        # this stands aside for it; where it is only how to cook the food from raw, the moves for
        # its kind of food answer instead.
        from . import cooking  # late: cooking.py imports this module as it loads
        idea = cooking.pantry_idea(said) or ""
        if any(word in idea.lower() for word in USE_DISH_WORDS):
            return None
        memory["meal_plan"] = {"turn": len(memory.get("turns") or []), "ingredients": [],
                               "allowed": None, "without": [], "minutes": None,
                               "offered": [said]}
        return use_it_up(said)
    return None


def _plan(memory, names, allowed, without, minutes, offered):
    """Remember what was offered and the limits set, so the next turn can build on it."""
    earlier = memory.get("meal_plan") if isinstance(memory.get("meal_plan"), dict) else {}
    memory["meal_plan"] = {
        "turn": len(memory.get("turns") or []),
        "ingredients": list(names) or list(earlier.get("ingredients") or ()),
        "allowed": sorted(allowed) if allowed is not None else earlier.get("allowed"),
        "without": sorted(without),
        "minutes": minutes,
        "offered": (list(earlier.get("offered") or ()) + list(offered))[-4:],
        # The dish this turn led with. "quicker please" is quicker than that one, not than the
        # alternative offered after it.
        "pick": (list(offered) or [earlier.get("pick") or ""])[0],
    }


# Words that ask for food. A line with none of them and nothing from the kitchen in it is not
# asking for a meal at all ("i only have an oven and one tray"), and the dish table has to
# decline it: other code paths read this function as "what would you suggest for this line".
# "cook", "make" and "eat" are not in this list: they are how people talk about a kitchen, not
# a request for dinner, and "she likes cooking but has a tiny kitchen" is a gift question. A
# line with no meal in it needs something from the fridge named, or a word like "dinner".
ASK_WORDS = ("what", "whats", "any", "dinner", "dinners", "tea",
             "supper", "supper", "lunch", "lunches", "breakfast", "meal", "meals", "food",
             "hungry", "starving", "idea", "ideas", "suggest", "suggestion",
             "recommend", "recommendation", "something", "anything", "tonight",
             "recipe", "recipes", "leftover",
             "leftovers", "use up", "eat up", "cook up", "fridge", "freezer", "cupboard",
             "pantry", "hungry", "inspiration", "options")


# How a diet they told the bot about once reads back to them, so a suggestion that would put
# that food back on the plate can say why it is not doing it.
DIET_SAID = (("dairy free", "dairy free"), ("lactose", "lactose intolerant"),
             ("vegan", "vegan"), ("vegetarian", "vegetarian"), ("gluten free", "gluten free"),
             ("no meat", "not eating meat"), ("no fish", "not eating fish"),
             ("no dairy", "dairy free"), ("cutting out", "cutting things out"))


# "quick", "fast" and "hurry" are not in ASK_WORDS: they say how long, not what for, so "quick
# one, how often should i do it" about a kettle is not a request for a dinner. A clock in the
# line still counts, and a plan from the last turn still counts.
#
# A thank-you is not an ask: "nice one, thx" after a dish gets "Glad that helped", not a
# second recipe.
ACK_WORDS = ("thanks", "thank you", "thx", "cheers", "nice one", "will do", "ill try that",
             "i'll try that", "sounds good", "good idea", "great idea", "lovely", "perfect")


# Words that say who cannot eat what. A plain crowd answer (one tray of chicken thighs) is
# wrong once a line says vegetarian, vegan or an allergy, so the dishes answer instead.
DIET_WORDS = ("vegetarian", "vegan", "veggie", "dairy free", "lactose", "gluten free",
              "no meat", "meat free", "meatless", "pescatarian", "pescetarian", "allergic",
              "allergy", "nut free", "nut allergy", "halal", "kosher")


# Words that ask for a meal rather than describing one somebody is about to cook. The crowd
# answer is a plan for a table, so it needs a line that asks: "maybe i will cook her favourite
# thing", said about someone who has died, is not a request for a traybake that feeds eight.
ASK_CUES = ("what", "which", "anything", "any", "need", "want", "feed", "party", "guests",
            "everyone", "ideas", "idea", "suggest", "recommend", "decide", "menu", "plan",
            "help me")


# "im trying to work out what to cook for six people" is read as news about the plan, and it is
# a request all the same: the words that ask are in the line, whatever the reading calls it.
ASK_IN_NEWS = ("what to cook", "what to make", "what to have", "what to eat", "what should i",
               "what can i", "ideas for", "idea for", "help me", "need something", "need a",
               "trying to work out", "trying to decide", "trying to plan", "cant decide",
               "can't decide", "any suggestions", "suggest something")


def reads_as_news(understood, clean=""):
    """True when the line is news about a meal rather than a request for one.

    "maybe i will cook her favourite thing", said about someone who has died, is news. A line
    that asks what to cook is a request even when the reading files it as news, because the
    asking words are in it ("im trying to work out what to cook for six people").
    """
    understood = understood if isinstance(understood, dict) else {}
    if str(understood.get("intent") or "") != "news":
        return False
    low = str(clean or understood.get("clean") or "").lower()
    return not any(cue in low for cue in ASK_IN_NEWS)


def asks_for_a_meal(understood, clean=""):
    """True when this line is a request for a meal, not news about one."""
    understood = understood if isinstance(understood, dict) else {}
    intent = str(understood.get("intent") or "")
    kind = str(understood.get("kind") or "")
    if reads_as_news(understood, clean):
        return False
    if kind == "question" or intent in ("question", "request"):
        return True
    low = str(clean or understood.get("clean") or "").lower()
    return any(cue in low.split() for cue in ASK_CUES)


def says_a_diet(text):
    """True when the line itself names a diet or an allergy."""
    low = str(text or "").lower()
    return any(cue in low for cue in DIET_WORDS)


def _carry(memory, understood):
    """A picnic or a day out: what to pack, not what to cook."""
    line = str(understood.get("clean") or "").lower()
    # "we went to the beach yesterday" is a day out, not a request for a packed lunch: the ask
    # is the word that wants something, and a diet changes what goes in the bag.
    # A day out is the subject; the question is what to put in the bag. So the line has to ask
    # for something to eat or take, or it is a story about the beach.
    # "picnic for a veggie friend" asks with a diet rather than a verb, and that is still a
    # request for something to put in the bag.
    if not any(word in line for word in ("make", "take", "bring", "pack", "packing", "food",
                                         "eat", "eating", "lunch", "idea", "ideas", "need",
                                         "snack", "snacks", "something", "anything",
                                         "for a picnic", "on a picnic", "day out",
                                         "veggie", "vegetarian", "vegan", "no meat", "gluten",
                                         "kid", "kids", "children", "child", "toddler",
                                         "people", "family", "friends")):
        return None
    if any(word in line for word in ("went to", "was at", "we had", "yesterday", "last week")):
        return None
    # A flight or an airport is also where people ask about money, delays and what they are
    # allowed to carry: "my flight was cancelled am i owed anything" and "can i take a lighter
    # on a flight" are not packed lunches, and "anything" or "take" is not a food word. The
    # venue only counts as a meal when the line also names something to eat or drink.
    if any(word in line for word in ("flight", "flights", "plane", "airport", "airline",
                                     "cancelled", "canceled", "delayed", "delay", "refund",
                                     "owed", "compensation", "lighter", "luggage", "baggage",
                                     "security", "passport", "check in", "check-in")):
        if not any(word in line for word in ("food", "eat", "eating", "lunch", "snack", "snacks",
                                             "picnic", "sandwich", "meal", "meals", "drink",
                                             "drinks", "breakfast", "dinner", "packed")):
            return None
    # A lunchbox is its own answer, and it lives in another entry: a packed lunch is eaten at a
    # desk, not on a rug, and the sandwich there is a better answer than a cold frittata.
    if any(word in line for word in ("packed lunch", "lunchbox", "lunch box", "school lunch",
                                     "bento")):
        return None
    # Whether food may be carried on at all is the security question, and travel.py's
    # flight-food answers it; the picnic list is the answer to what to pack for a journey.
    # "can i bring my own lunch on a flight" was a frittata in wedges when the line was asking
    # whether it would be taken off them at the tray. A journey with no permission in it ("what
    # food should i take on a long flight") keeps the list, and a flask to work is not a flight.
    if any(word in line for word in ("flight", "flights", "plane", "airport", "airline",
                                     "security")) and any(
            word in line for word in ("can i take", "can i bring", "can we take",
                                      "can we bring", "could i take", "could i bring",
                                      "am i allowed", "are we allowed", "allowed to take",
                                      "allowed to bring", "allowed on", "100ml", "liquids")):
        return None
    # An answer that is the same every time it is asked the same way: the choice is
    # varied by the line and the turn, not by the process, so a deck comparison measures
    # the change and not the dice.
    reply = _variant(CARRY_REPLIES, understood, memory)
    if any(word in line for word in ("veggie", "vegetarian", "vegan", "no meat")):
        reply = reply.replace("cold sausages or sausage rolls, ", "").replace(
            "sausage rolls, ", "")
    if any(word in line for word in ("kids", "children", "child", "toddler", "little ones")):
        reply += " For small people, add something they will actually eat: breadsticks, cheese."
    return reply


def _kitchen_answer(understood):
    """cooking.py's answer for a kitchen with no oven, hob or microwave, or None."""
    from . import cooking  # imported here: cooking.py imports NOT_MINE from this file
    answer = cooking.without(understood)
    return answer if isinstance(answer, str) and answer.strip() else None


# Coeliac, gluten free and no wheat are cooking.py's list, not this table's dishes: a pasta
# dish is the wrong answer, and the other module says which dishes are safe.
GLUTEN = ("coeliac", "celiac", "gluten", "wheat free", "no wheat", "no gluten")


def _said_about(memory, clean=""):
    """The line and the last few turns, lowercased, for cues that hold across turns."""
    said = [str(clean or "")]
    for turn in (memory.get("turns") or ())[-4:]:
        if isinstance(turn, dict) and turn.get("user"):
            said.append(str(turn["user"]).lower())
    return " ".join(said)


def _diet_said(memory, understood=None):
    """The diet word the person used about themselves, if they used one."""
    said = " ".join(str((turn or {}).get("user") or "").lower()
                    for turn in (memory.get("turns") or ())[-6:] if isinstance(turn, dict))
    if isinstance(understood, dict) and understood.get("clean"):
        said += " " + str(understood["clean"]).lower()
    about = memory.get("user") if isinstance(memory.get("user"), dict) else {}
    said = (str(about.get("diet") or "").lower() + " " + said).strip()
    for cue, reads in DIET_SAID:
        if cue in said:
            return reads
    return ""


def _fresh(reply, item, memory):
    """A sentence they were told a turn ago is not an answer.

    A follow-up can land back on the idea just given ("and how long does that take?"), and
    saying the same sentence again is no help; the clock is what is still unknown then.
    """
    turns = memory.get("turns") or []
    last = ""
    for turn in reversed(turns):
        if isinstance(turn, dict) and turn.get("bot"):
            last = str(turn["bot"])
            break
    if not last:
        return reply
    head = re.split(r"(?<=\.)\s+", reply)[0]
    if head and head in last:
        return f"{item.said.capitalize()} takes about {item.minutes} minutes."
    return reply


# A meal for a table is not a weeknight pick: twelve people are not "a frittata in 20 minutes".
# The crowd and occasion answers live in bot/knowledge/cooking.py, so this table stands aside.
CROWD_SAID = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
              "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
              "thirty": 30}
CROWD_ASK = ("party", "buffet", "birthday", "wedding", "christening", "guests", "everyone")


def _crowd_answer(memory, understood):
    """What cooking.py says for a meal for a table, or None when it has nothing."""
    from . import cooking  # imported here: cooking.py imports NOT_MINE from this file
    said = [str(understood.get("clean") or "")]
    for turn in (memory.get("turns") or ())[-4:]:
        if isinstance(turn, dict) and turn.get("user"):
            said.append(str(turn["user"]))
    text = " ".join(said).lower()
    # "for 20 minutes" is a clock, not twenty people.
    text = re.sub(r"\bfor\s+\d{1,3}\s*(?:min|mins|minute|minutes|hour|hours|sec|seconds)\b",
                  " ", text)
    answer = cooking._crowd_or_any(text, cooking._excluded(text))
    return answer if isinstance(answer, str) else None


COUNT_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
               9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def _count_word(number):
    """The word for how many are eating, so the reply says "four" the way the line did."""
    return COUNT_WORDS.get(int(number), str(int(number)))


# "what can i cook for 4 and 7 year olds" is two children, not a table of four. The ages sit in
# the same "for N" shape the headcount is read from, so they are taken out before the count is
# read: a number followed by "year old" or "years old" is how old somebody is, never how many of
# them there are. The two-child shape ("4 and 7 year olds") is the common one, and "a 4 year old"
# is the single-child one.
_AGE_SHAPE = re.compile(
    r"\b(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"(?:\s*(?:,|and|&)\s*(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve))?"
    r"\s*(?:years?|yrs?)\s*(?:-\s*)?olds?\b", re.I)


def _for_a_table(memory, understood):
    """How many people are eating, when the line or the last few turns said so."""
    said = [str(understood.get("clean") or "").lower()]
    for turn in (memory.get("turns") or ())[-4:]:
        if isinstance(turn, dict) and turn.get("user"):
            said.append(str(turn["user"]).lower())
    joined = " ".join(said)
    kids_named = bool(_AGE_SHAPE.search(joined))
    text = _AGE_SHAPE.sub(" ", joined)
    counts = [int(n) for n in re.findall(
        r"\bfor\s+(\d{1,3})\b(?!\s*(?:min|mins|minute|minutes|hour|hours|sec|seconds)\b)",
        text)]
    for word, value in CROWD_SAID.items():
        if re.search(r"\bfor\s+" + word + r"\b(?!\s*(?:min|minute|hour))", text) \
                or re.search(r"\b" + word + r"\s+(?:people|of us|adults|guests|coming)\b",
                             text):
            counts.append(value)
    if any(phrase in text for phrase in CROWD_ASK):
        counts.append(6)
    if counts:
        best = max(counts)
        # "cheap tea for two adults and a 4 year old" is three at the table. The adults are
        # counted out loud and the child is not, so the child is added on - but only when the
        # line said adults, because a plain "for 4" is already the whole table.
        if kids_named and re.search(r"\badults?\b", text):
            return best + len(_AGE_SHAPE.findall(joined))
        return best
    # A line that names only ages names no table: "for 4 and 7 year olds" is two children, and
    # how many are eating is a thing the reply would be guessing at. Better to say nothing about
    # the count than to open with a number of eaters that the line never said.
    return 0 if kids_named else 0


# "what can i make with parsnips" names a food the table does not know. A generic pick around
# whatever is in the fridge is worse than passing, because the cooking table can look the thing
# up: the ask is the ingredient, so an ingredient the table cannot see is not its question.
KITCHEN_WORDS = set(
    ["a", "an", "the", "my", "our", "some", "any", "half", "leftover", "left", "over", "frozen",
     "fresh", "tin", "tins", "can", "cans", "jar", "jars", "packet", "packets", "pack", "packs",
     "bag", "bags", "bunch", "few", "bit", "bits", "little", "of", "and", "or", "in", "on",
     "fridge", "freezer", "cupboard", "what", "can", "could", "i", "we", "you", "make", "made",
     "cook", "cooking", "do", "done", "with", "from", "use", "up", "using", "recipe", "recipes",
     "ideas", "idea", "please", "tonight", "dinner", "tea", "supper", "lunch", "meal", "meals",
     "food", "eat", "have", "got", "there", "is", "are", "only", "just", "lot", "lots", "loads",
     "plenty", "still", "also", "for", "to", "it", "this", "that", "these", "those", "one", "two",
     "three", "four", "five", "kg", "g", "grams", "oz", "lb", "big", "small", "old", "new",
     "cooked", "raw", "tinned", "dried", "spare", "extra", "again", "rest", "leftovers"])
WITH_ASK = re.compile(r"\b(?:with|using|from)\s+(.{2,60})")
# "need a recipe for shortbread" names a dish, not a food: the recipe table answers it, and a
# weeknight dish answers something else. The words that make a line a meal ask rather than a
# dish name are dropped before the tail is read.
RECIPE_FOR = re.compile(r"\b(?:recipe|recipes)\b(?:\s+(?:for|of|to make))?\s+(.{2,60})")
NOT_A_DISH_NAME = ("idea", "ideas", "meal", "meals", "dinner", "dinners", "tea", "supper",
                   "lunch", "tonight", "please", "pls", "plz", "quick", "easy", "cheap")


# "what should i cook for a family with kids" is a dinner for company, not a list of foods:
# the words after "with" name the people eating, so the tail is not an ingredient the table has
# failed to find. Without this the whole "cook something for a meal with friends" family of
# lines was read as an unknown food and hedged.
COMPANY = frozenset((
    "kid", "kids", "child", "children", "toddler", "toddlers", "baby", "babies", "teen",
    "teens", "teenager", "teenagers", "family", "families", "friend", "friends", "mate",
    "mates", "flatmate", "flatmates", "housemate", "housemates", "partner", "partners",
    "husband", "wife", "boyfriend", "girlfriend", "mum", "mums", "dad", "dads", "mother",
    "mothers", "father", "fathers", "parent", "parents", "sister", "sisters", "brother",
    "brothers", "gran", "grans", "grandma", "grandmas", "grandad", "grandads", "nan", "nans",
    "grandparent", "grandparents", "grandchild", "grandchildren", "nephew", "nephews",
    "niece", "nieces", "cousin", "cousins", "son", "sons", "daughter", "daughters", "in law",
    "in laws", "in-laws", "inlaw", "inlaws", "law", "laws", "guest", "guests", "people",
    "one", "ones", "everyone",
    "somebody", "someone", "workmate", "workmates", "colleague", "colleagues", "crowd",
    "household", "neighbours", "neighbors", "visitors", "company", "others", "them", "us",
    "we", "me", "you", "ourselves", "myself", "yourself", "anyone", "nobody"))


# The words after "with" run on past the ingredient into the rest of the sentence - "with her 4
# year old what should i cook", "with the kids coming over" - so a pronoun, a verb or an age left
# in the tail was read as a food the table has never heard of, and the line went unanswered.
NOT_AN_INGREDIENT = frozenset((
    "my", "your", "his", "her", "its", "our", "their", "mine", "yours", "hers", "ours",
    "theirs", "is", "are", "was", "were", "be", "been", "being", "am", "do", "does", "did",
    "done", "should", "shall", "would", "could", "can", "will", "year", "years", "old",
    "month", "months", "week", "weeks", "day", "days", "tonight", "today", "tomorrow",
    "it", "them", "him", "we", "us", "they", "these", "those", "again", "still", "coming",
    "coming", "staying", "stay", "stays", "visiting", "visit", "over", "coming", "around",
    "here", "there", "soon", "later", "too", "also", "just", "now", "quite", "really",
    # A budget of time is not a thing in the kitchen. "dinner with no time to cook" and "what
    # can i make with half an hour" read the clock as the ingredient, and the table then said it
    # had never heard of the food, so a dinner question got no answer at all.
    "time", "times", "hour", "hours", "minute", "minutes", "mins", "moment", "rush",
    "hurry", "while", "effort",
    # The words a line about a time budget is built from are never in the fridge either: "dinner
    # with no time to cook" left "no" behind as the one thing in the kitchen, and a dinner
    # question was turned down because the table had never heard of that food. "nothing" is
    # deliberately not here: "what can i make with nothing in the fridge" is the empty-kitchen
    # card's line, and a word that says the kitchen is empty is the one thing that must reach it.
    "no", "not", "any", "some", "much", "many", "more", "less", "enough", "half",
    "little", "bit", "proper", "decent", "nice", "simple", "whole", "quick", "quickly",
    "fast", "easy", "something", "anything", "thing", "things"))


def _company(tail):
    """True when the words after "with" name the people eating, not ingredients."""
    return any(word in COMPANY or word.rstrip("s") in COMPANY for word in tail)


def _unknown_ingredient(clean, known):
    """True when the line asks what to make with a food the table has never heard of."""
    for match in WITH_ASK.finditer(clean):
        rest = [word for word in WORD.findall(match.group(1))
                if word not in KITCHEN_WORDS and word not in NOT_AN_INGREDIENT
                and not word.isdigit()]
        if not rest:
            return False
        if _company(rest):
            # "with kids", "with my in laws", "with friends coming over": the tail is who is
            # eating, not what is in the fridge.
            continue
        if not any(word in known or word.rstrip("s") in known or word.rstrip("es") in known
                   for word in rest):
            return True
    return False


def _unknown_dish_recipe(clean, known):
    """True for "a recipe for <dish>" where the dish is not food the tables know."""
    match = RECIPE_FOR.search(clean)
    if not match:
        return False
    tail = [word for word in WORD.findall(match.group(1)) if word not in KITCHEN_WORDS
            and word not in NOT_A_DISH_NAME and not word.isdigit()]
    if not tail:
        return False
    return not any(word in known or word.rstrip("s") in known or word.rstrip("es") in known
                   for word in tail)


def unknown_food(understood):
    """True when the line names food the dish table has no row for.

    The line is read as the understanding engine read it, repairs and all. Both readers below
    match the line rather than its words ("a recipe for <dish>"), and read as typed the shape
    slipped past every line with the slip inside the word "recipe" itself: "i need a recipie for
    shortbread" was answered with ten-minute dinners while the shortbread card was waiting.
    """
    clean = line_as_read(understood).lower()
    known_food = set(FOOD_WORDS) | set(INGREDIENTS)
    for words in INGREDIENTS.values():
        known_food.update(words)
    if _unknown_ingredient(clean, known_food):
        return True
    return _unknown_dish_recipe(clean, known_food)


# Words a line can put behind "without" that are a limit this table can cook around even though
# they are not food: a diet is read into `allowed`, and a food into `without`.
NOT_FOOD_LIMITS = ("meat", "dairy", "gluten", "wheat", "lactose", "sugar", "salt", "fat", "nuts",
                   "nut", "fish", "seafood", "shellfish", "eggs", "carbs", "carb", "calories",
                   "oil", "butter", "flour", "pasta", "rice", "potato", "potatoes")

WITHOUT_WORD = re.compile(r"\bwithout\s+(?:the\s+|any\s+|a\s+|much\s+|so\s+much\s+)?"
                          r"(?P<food>[a-z][a-z'-]{1,24})", re.I)


def _something_it_has_not_got(understood, allowed, without):
    """True when the line's "without X" is a thing this table cannot read as a food or a diet.

    The dishes know foods and diets. Anything else is the rest of the bot's business, and this
    table answering it is how "i dont have any money" came back with a curry.
    """
    if allowed is not None or without:
        return False
    clean = str((understood or {}).get("clean") or "").lower()
    match = WITHOUT_WORD.search(clean)
    if not match:
        return False
    word = match.group("food").lower()
    return word not in NOT_FOOD_LIMITS and word not in FOOD_WORDS \
        and word.rstrip("s") not in FOOD_WORDS


def suggest(memory, understood):
    """A dinner idea for this line: from what they named, within the limits they set."""
    if says_it_has_gone_off(understood.get("clean")):
        # "my mince smells a bit is it still ok" named a food, which is all this table needs, and
        # it answered with a ragù. A dish built on an ingredient the person has just said smells
        # wrong is the one reply nobody wants: the sniff test in still_ok.py is the answer.
        return None
    if a_dish_is_already_the_plan(str((understood or {}).get("norm_text")
                                      or (understood or {}).get("clean") or "")):
        # "fancy a spag bol tonight" names the dish it means to cook, and this row answered it
        # with a chicken traybake. The dish's own card, or the plan for it, is the answer.
        return None
    plan = memory.get("meal_plan") if isinstance(memory.get("meal_plan"), dict) else {}
    allowed, without, minutes = _limits(understood, memory)
    # "something without cheese" names cheese to rule it out, not to use it.
    names = [name for name in _named(understood) if name not in without]
    if _something_it_has_not_got(understood, allowed, without):
        # "what can i make without money" is a line about money. "Without" is followed by
        # whatever a line is short of, and a dish picked at random is an answer to nobody; the
        # modules that know about money or time answer it.
        return None
    if names and not any(name in IN_A_DISH for name in names):
        # They named a food, and this table has no dish that uses it: "what can i make with
        # coconut milk" is a question for the kitchen table, not a dish picked at random.
        return None
    clean = str(understood.get("clean") or "").lower()
    if (not names and not _for_a_table(memory, understood)
            and any(cue in clean for cue in MEAL_WORD)
            and any(cue in clean for cue in CHILD_AT_TABLE)):
        # "what can i cook with my kids", "what should i cook for my toddler", "with the family":
        # the people eating are the constraint and no food is named, so the child's dinner is the
        # answer - the few things a friend would put in front of them - and a quick supper picked
        # from this table is a reply to a different question. A line that names a food keeps the
        # table, because then the food is what to cook with.
        return KIDS_IDEA
    kitchen = _kitchen_answer(understood)
    if kitchen:
        return kitchen  # what to cook in the kitchen they have is cooking.py's list, not a dish
    if any(cue in clean for cue in BEFORE_EVENT) and any(
            word in clean for word in EVENT_WORDS):
        return None  # fuel before a race or a match: not a dinner pick
    if any(cue in clean for cue in SMALL_PEOPLE) and not any(
            cue in clean for cue in MEAL_WORD):
        return None  # an egg hunt for toddlers, a birthday, a Christmas: not a dinner pick
    if any(cue in clean for cue in NOT_A_MEAL_SUBJECT):
        # "what to wear to a dinner party" and "what to bring to a dinner party" are about the
        # clothes and the bottle, not the cooking: the party-outfit answer owns those lines, and
        # the crowd answer for a dinner party took them because "dinner party" reads as a table.
        return None
    if any(cue in clean for cue in DESSERT_ASK):
        # "what can i make for dessert" wants a pudding: the dessert entries in cooking.py
        # answer it, and a dinner picked here is a reply to a different question.
        return None
    if any(cue in clean for cue in TECHNIQUE_ASK) and not any(
            cue in clean for cue in USE_UP_ASK):
        # "how long do i cook chicken for" / "what temperature should i cook chicken at" is a
        # technique question: cooking.py answers those, and naming a dish instead is a reply to
        # a question nobody asked.
        return None
    if any(cue in clean for cue in REPAIR):
        return None  # a dish that went wrong is a repair, and the cooking table owns those
    if any(cue in clean for cue in MAKING_AT_HOME):
        return None  # what to make it out of is the making row's question, not a dish to cook
    if any(cue in clean for cue in OTHER_PEOPLE):
        # "my son wont eat vegetables" is the fussy-eater advice in cooking.py, not a dish pick.
        return None
    if any(cue in clean for cue in UNWELL) and not any(
            cue in clean for cue in SICK_OF):
        # "what can i eat with a dodgy stomach" is about being ill, and health.py and the safety
        # lane answer it; a weeknight dish is the wrong answer to give someone who is unwell.
        return None
    if unknown_food(understood):
        return None  # a food the table does not know: the kitchen table can look it up
    if any(cue in _said_about(memory, clean) for cue in GLUTEN + CONDITION):
        # Coeliac, diabetes and a nut allergy have their own answers in cooking.py and health.py;
        # a weeknight dish with a guess at the numbers is not one of them.
        return None  # coeliac and gluten free have a list of their own in cooking.py
    asked = any(word in clean for word in ASK_WORDS)
    impress = any(cue in clean for cue in IMPRESS)
    impress_ask = (any(cue in clean for cue in IMPRESS_ASK)
                   or (any(cue in clean for cue in IMPRESS_FOR)
                       and any(cue in clean for cue in IMPRESS_WORTH)))
    news = reads_as_news(understood, clean)
    hungry = any(cue in clean for cue in HUNGRY)
    fancying_a_shape = (any(cue in clean for cue in DISH_STYLE)
                        or any(cue in clean for cue in STYLE_CUES))
    wanting = any(cue in clean for cue in STYLE_WANT) and fancying_a_shape
    # "im out of cheese", said about a dinner already on the table, is a limit on it: the
    # ingredient is named only to be ruled out, so it is not a name to cook around.
    out_of = bool(_ruled_out(clean)) and bool(plan.get("offered"))
    if news and minutes is None and not names and not plan.get("ingredients") and not hungry \
            and not wanting and not out_of and not impress_ask:
        # "maybe i will cook her favourite thing", said about someone who has died, is news
        # about a meal rather than a request for one. The reading a follow-up gets can add the
        # topic word ("... lunch") and then look like an ask, so news is checked first.
        return None
    # "and something vegetarian" is a limit on the idea already on the table, so a diet word
    # with an idea in hand is an ask; the same word on its own ("im vegetarian") is a fact.
    limit_follow = allowed is not None and bool(plan.get("offered"))
    if not (names or plan.get("ingredients") or minutes is not None or asked or limit_follow
            or wanting or out_of or impress_ask):
        # A diet on its own is not an ask: "im vegetarian and i dont eat dairy" is a fact about
        # them, which the greeting answers better than a dish would.
        return None  # no food, no ask, no limit, no plan: this line is not about a meal
    if not names and str(understood.get("kind") or "") == "thanks":
        return None  # a thank-you for the last idea is not a request for another one
    if (_for_a_table(memory, understood) >= 6 and asks_for_a_meal(understood, clean)
            and not says_a_diet(clean)):
        # A meal for a table is not one weeknight dish: hand the line to the crowd answer in
        # bot/knowledge/cooking.py, which knows how to feed eight from one oven dish. A line
        # that says who cannot eat what stays here, where the dishes know their own diets.
        crowd = _crowd_answer(memory, understood)
        if crowd:
            return crowd
    # A lunch is the lunch table's answer: cooking.py has the packed lunch, the lunchbox and
    # the five-minute sandwich, and a dish table full of dinners answers the wrong meal. The
    # dinner asks ("whats for dinner") and the kitchen ones ("what can i make with tuna") stay.
    if any(cue in clean for cue in LUNCH_ASK):
        return None
    # What was remembered about their last ingredient is the subject only when this line names
    # nothing of its own. A food it names that this table has no dish for ("what can i make with
    # oats" after peas) is that food's question, and answering it with peas is answering the
    # turn before: the pantry has porridge.
    if not names and WITH_ASK.search(clean):
        asked_for = [word for word in WORD.findall(WITH_ASK.search(clean).group(1))
                     if word not in KITCHEN_WORDS and word not in NOT_AN_INGREDIENT
                     and not word.isdigit()]
        known_here = {form for forms in INGREDIENTS.values() for form in forms}
        # The same read as _unknown_ingredient: a "with" tail that names the company ("cook
        # something for a meal with friends") is not an ingredient this table has missed.
        if asked_for and not _company(asked_for) and not any(
                word in known_here or word.rstrip("s") in known_here for word in asked_for):
            return None
    carried = not names
    names = names or [name for name in plan.get("ingredients") or () if name not in without]
    if carried and names and (any(cue in clean for cue in DISH_STYLE)
                              or any(cue in clean for cue in STYLE_CUES)):
        # "whats a good stir fry" is a fresh request: the remembered peas cannot turn it into a
        # soup, so the shape they asked for picks the dish and the peas wait.
        names = []
    # Something they have just picked up that their own diet rules out ("im dairy free" then
    # "what can i cook with the cheese in the fridge") is the answer to say first, not to
    # ignore: the pick would otherwise quietly leave it on the shelf.
    ruled_now = _ruled_out(str(understood.get("clean") or ""))
    off_limits = [name for name in _named(understood) if name not in ruled_now
                  and (name in without
                       or (allowed is not None
                           and not any(name in dish.uses and dish.diet in allowed
                                       for dish in DISHES)))]
    names = [name for name in names if name not in off_limits]
    if off_limits and not names:
        pick = _best([], allowed, without, minutes, memory, understood)[0]
        _plan(memory, [], allowed, without, minutes, [pick.name])
        # The ingredient is left unnamed on purpose: naming what they cannot eat reads as a
        # suggestion of the very thing that is out, so the reason is what gets said instead.
        reason = _diet_said(memory)
        lead = (f"Since you are {reason}, I'd leave that out" if reason
                else "I'd leave that out")
        return (f"{lead} and do {pick.said} ({pick.minutes} minutes): {pick.how}.")
    ranked = _best(names, allowed, without, minutes, memory, understood)
    # A dish this request has already had is not an idea: take the next one that uses what they
    # named. Only when every dish using it has been offered does the same one come back, and
    # then the ask is answered as a limit rather than described again.
    offered = list(plan.get("offered") or ())
    fresh = [dish for dish in ranked if dish.name not in offered]
    if not fresh and names and minutes is not None:
        # Everything this table has for what they named is on the table already, and the clock
        # rules out nothing: say which one it is and what it costs rather than describe it again.
        best = ranked[0]
        _plan(memory, names, allowed, without, minutes, [best.name])
        return (f"{best.said.capitalize()} is the quickest I know with {_prose(names)}, at "
                f"{best.minutes} minutes; that is every dish I have for them.")
    ranked = fresh or ranked
    if impress and not names:
        # "something nice for my girlfriend on friday" is a meal to make an effort over, not
        # the quickest thing in the table: a dish that takes half an hour beats a frittata, and
        # one of the dishes people cook to show off beats an ordinary half-hour supper. The
        # slower dishes stay as the fallback, so a fridge of lentils still gets a real answer.
        slower = [dish for dish in ranked if dish.minutes >= 30]
        ranked = slower or ranked
        shown = [dish for dish in ranked if dish.name in SHOW_OFF]
        ranked = shown or ranked
    first = ranked[0]
    if names and minutes is not None and (
            not (set(first.uses) & set(names)) or first.minutes > minutes + GRACE):
        # Nothing new uses what they have inside the clock, so say so plainly rather than
        # suggesting a dish that ignores the mince sitting in the fridge.
        stick = _stick(memory, names, allowed, without)
        if stick is not None:
            how = stick.how[0].upper() + stick.how[1:]
            when = _variant(_times(stick.how), understood, memory).format(n=stick.minutes)
            _plan(memory, names, allowed, without, minutes, [stick.name])
            return (f"{stick.said.capitalize()} is still the quickest I know with "
                    f"{_prose(names)}: {stick.how}. {when}")
    second = ranked[1] if len(ranked) > 1 else None
    if not names and not without and allowed is None and minutes is None and not impress:
        # A bare "what should I cook tonight" with nothing to go on: three quick things they
        # can pick from and a question back, rather than one dish invented around a fridge
        # nobody has described.
        picks = _spread(ranked)
        if len(picks) >= 2:
            names_offered = [item.name for item in picks]
            _plan(memory, names, allowed, without, minutes, names_offered)
            said = ", ".join(f"{item.said} in {item.minutes}" for item in picks[:-1])
            last = picks[-1]
            # The word that opens the list is the word they asked with. "im skint, what can i
            # cook" and "cheap dinner ideas" were answered "Quick: ..." - the dishes were the
            # thrifty ones, but the reply never said cheap, and money was the question.
            said_words = " ".join(understood.get("words") or [])
            thrifty = any(cue in _said_about(memory, said_words) for cue in CHEAP_ASK)
            eaters = _for_a_table(memory, understood)
            if thrifty and 2 <= eaters <= 12:
                # "cheap meals for four people" is about feeding four: the count they gave is
                # part of the answer, or they cannot tell whether it is enough.
                opener = f"Cheap, and enough for {_count_word(eaters)}:"
            elif thrifty:
                opener = "Cheap:"
            else:
                opener = "Quick:"
            if fit.wanted(memory) == "pick" and not thrifty:
                # The line asked for one dish - "what should i cook tonight", "what can i make" -
                # and three dishes with no pick among them answered a different question: the
                # person has to make the choice the bot was asked to make, and the first thing on
                # the line is a label rather than a dish. The first dish is said as the pick now,
                # and the rest of the shortlist follows it as the other ideas, so the person gets
                # the dish they asked for and can still see what else there was.
                #
                # The pick carries its time ("in 15 minutes") and the other two are named plainly
                # after it. That is what "how long does that take" next turn reads: the follow-up
                # is answered from the previous reply's first sentence and needs the pick's time
                # there, and before this change the only time in it was the last dish's, so the
                # person who asked about their pick was told 30 minutes.
                one, rest = picks[0], picks[1:]
                # The alternatives stay in the pick's own sentence, joined with ", or". A full stop
                # before "Or" reads to `bot/memory/reject.py` as no list at all
                # (`choice.options_in` splits the reply at the sentence), so "no i dont fancy
                # that" came back with the other two dishes lost and "you pick" with no dish.
                others = "".join(f", or {item.said} in {item.minutes}" for item in rest)
                return (f"Here's my pick: {one.said} in {one.minutes} minutes{others}. "
                        "Tell me what is in the fridge and I will narrow it down.")
            return (f"{opener} {said}, or {last.said} if you have {last.minutes} minutes. Tell "
                    f"me what is in the fridge and I will pick properly.")
    if not names and second is not None:
        # Nothing to match, so give a pick and one alternative in a single breath.
        _plan(memory, names, allowed, without, minutes, [first.name, second.name])
        if second.minutes < first.minutes - GRACE:
            tail = f"If you want something quicker, {second.said} takes {second.minutes} minutes."
        elif abs(second.minutes - first.minutes) <= GRACE:
            # The same length of time: the clock is not what tells them apart, so it is said
            # once, in the first sentence, and a "how long?" follow-up finds it there.
            tail = f"Something else that works is {second.said}."
        else:
            tail = f"Something else that works is {second.said}, at {second.minutes} minutes."
        return (f"I'd do {first.said} ({first.minutes} minutes): {first.how}. " + tail)
    reply = _describe(first, understood, memory, without)
    # A second dish is worth a sentence when it is built on what they named: with two or more
    # ingredients it has to use more than one of them, and with a single ingredient it has to use
    # that one. "what should i cook tonight with mince" wants more than one answer.
    shared = len(set(second.uses) & set(names)) if second is not None else 0
    # The alternative may take a little longer than the first dish, but not much: a 40-minute
    # chilli alongside a 20-minute dinner is a different evening.
    if (second is not None and names and shared >= min(2, len(names))
            and second.minutes <= max(25, first.minutes + 10)):
        options = FOLLOW_ON
        if "cheese" in without and "cheese" not in second.uses:
            options = FOLLOW_ON + (FOLLOW_ON_NO_CHEESE,)
        if abs(second.minutes - first.minutes) <= GRACE:
            # Close enough in time that the clock is not the difference: one time in the reply
            # keeps the answer about the dish, and a "how long?" follow-up finds it in the first
            # sentence instead of quoting the alternative back.
            alt = _variant(("Something else that works is {alt}.",
                            "There is {alt} as well."), understood, memory)
            alt = alt.format(alt=second.said)
        else:
            alt = _variant(options, understood, memory).format(alt=second.said, n=second.minutes)
        reply = _fresh(f"{reply} {alt}", first, memory)
    _plan(memory, names, allowed, without, minutes,
          [first.name] + ([second.name] if second else []))
    return _fresh(reply, first, memory)


# What to order at a named takeaway, one answer per counter. The choosing row below asks about a
# takeaway in general, in the words of a decision ("chinese or indian", "should we get"); these
# are the lines that name the counter and ask what is good there, which was a shrug: "whats nice
# from a chippy", "best thing from a chip shop", "what do i order at a kebab shop" and "whats
# nice from a bakery" were all punts while "what should i get from the chippy" was answered. The
# counter is the subject, so the answer is what to order at that one counter and not a choice
# between counters.
TAKEOUT_PICKS = (
    (("pizza place", "pizza shop", "pizza parlour", "pizza parlor", "pizza", "pizzas",
      "dominos", "domino's"),
     "One pizza each and a garlic bread to share: a 12-inch is one hungry person and a 9-inch a "
     "light one, so a 12-inch between two plus a side is the cheaper way to feed a pair. A plain "
     "margherita and one with a topping beats two fully loaded ones, which are the ones left "
     "half eaten."),
    (("bakery", "bakers", "baker", "patisserie", "bakery shop"),
     "Buy the loaf that is still warm and one pastry to eat before you get home: a sourdough or a "
     "tin loaf keeps two days on the board and a week sliced in the freezer, and a cheese twist or "
     "a croissant is what a bakery is for. Ask which loaf is today's rather than yesterday's - it "
     "is the one question they are always happy to answer."),
    (("sandwich shop", "deli", "deli counter", "subway", "baguette shop", "sandwich bar"),
     "The filling that is made fresh, in a baguette or a sub rather than sliced bread, and ask for "
     "the salad on the side if it has to travel back to a desk: wet salad in the sandwich is what "
     "makes it collapse. A hot filling - meatballs, a toastie, a chicken escalope - is the one "
     "worth ordering out, because it is the one that will not be as good made at home."),
)
# The counters above, as words, so the entry can name the place it answers for.
TAKEOUT_PLACES = tuple(name for names, _ in TAKEOUT_PICKS for name in names)

# What a line asks about a counter. The choosing words are deliberately absent - "or",
# "decide", "which one" and "cant decide" belong to the row that chooses between counters, and
# a line with two of them in it ("chinese or indian") is that row's question.
TAKEOUT_ASK = ("what", "whats", "what is", "what are", "nice", "good", "best", "better",
               "recommend", "order", "get", "have", "should i", "should we", "do i",
               "do we", "worth", "idea", "ideas",
               # how many to buy is a counter question, and the pizza row below answers it
               # (one each, a 12-inch each, garlic bread to share): "how many pizzas do i need
               # for 8 people" was a shrug while "should i get one pizza or two" was answered.
               "how many")


def _takeout_pick(memory, understood):
    """What to order at the counter the line names: the most specific name wins."""
    clean = str((understood or {}).get("clean") or "").lower()
    best, longest = None, -1
    for names, reply in TAKEOUT_PICKS:
        for name in names:
            if len(name) > longest and re.search(r"\b" + re.escape(name) + r"\b", clean):
                best, longest = reply, len(name)
    return best


def _counters_named(clean):
    """Which rows of the table above the line names, by row: "bakery" and "baker" are one row."""
    rows = set()
    for index, (names, _) in enumerate(TAKEOUT_PICKS):
        for name in names:
            if re.search(r"\b" + re.escape(name) + r"\b", clean):
                rows.add(index)
                break
    return rows


# A definition and a yes-or-no about the shop are not what to order there: "what is a patisserie"
# wants what the place is, and "is the bakery nice" a verdict on the shop. A word that asks for
# the best at the counter keeps the row ("whats a good thing from the bakery").
DEFINITION_SHAPE = re.compile(r"\bwhat(?:'s| is| are|s)?\s+(?:a|an|the)\s+([a-z']+)")
ASKING_WORDS = {"good", "great", "nice", "best", "better", "cheap", "cheapest", "decent",
                "safe", "healthy", "worth", "solid", "vegetarian", "vegan"}


def _one_counter(understood):
    """True when the line asks what to order at one counter named in it."""
    clean = str((understood or {}).get("clean") or "").lower()
    if re.match(r"^(?:is|are|was|were)\b", clean):
        return False  # "is a bakery nice": a verdict on the shop, not the order
    shape = DEFINITION_SHAPE.search(clean)
    if shape and shape.group(1) not in ASKING_WORDS:
        return False  # "what is a patisserie": what the place is, not what to order
    return len(_counters_named(clean)) <= 1


# A food that has gone wrong is not an ingredient. The words are the ones people use for what
# they can see and smell, kept out of `meal-haves` so the keeping and spoilage rows answer.
SPOILT_FOOD = ("mouldy", "mould", "moldy", "mold", "blue spots", "green spots", "white spots",
               "black spots", "spots", "speckled", "fluff", "fluffy", "fuzzy", "furry", "fur",
               "green bits", "white bits", "blue bits", "smells", "smelly", "smelt", "stinks",
               "gone off", "went off", "going off", "slimy", "sour", "rancid", "stale",
               "fizzy", "curdled", "separated", "went bad", "gone bad", "rotten", "off it")

def _not_a_mark_and_not_a_row(understood):
    """A mark on something and a row that got heated are both not food in the kitchen.

    "i got egg on my shirt" is not an ingredient (the guard below), and "things got heated at
    dinner" is an argument, not a dinner: it was answered "Quick: tuna pasta in 15".
    """
    return not_a_mark_on_a_thing(understood) and _not_an_argument(understood)


ENTRIES = [
    # A clock and a hungry person, with no ingredient named: "im knackered, need something on the
    # table in 15 minutes" is a dinner question, and the feeling is the reason for it.
    entry("meal-hurry",
          (("need something", "something on the table", "on the table", "get dinner on",
            "dinner on the table", "feed the kids", "something fast"),
           ("minutes", "minute", "mins", "min", "quick", "quickly", "fast", "hurry", "now",
            "late", "knackered", "shattered", "starving", "hungry")),
          suggest, bias=-1,
          avoid=("sleep", "bed", "tired out", "go to bed", "nap", "breath", "chest", "pain",
                 "hurt", "doctor", "gp", "hospital", "panic", "anxious", "worried")
                + NOT_A_DISH + HOW_TO + MEASURING + DRINK + NOT_MY_KITCHEN),
    # What shall I cook: the open ask, with whatever they have and whatever they must avoid.
    # These four are broad on purpose, so they carry a small negative bias: a specific fact
    # about the thing named (bot/knowledge/cooking.py's leftover rice, say) wins the turn.
    entry("meal-tonight", (("tonight", "supper", "teatime", "what should i cook",
                            "what can i cook", "what should i make", "what can i make",
                            "what can i eat", "what should i eat", "what to eat", "whats for",
                            "what can i have", "what should i have", "what to have",
                            "what can we have", "what shall i have", "what can i make for",
                            "whats to eat", "what is for", "what would you cook",
                            # The same ask with "do" in it, which is how most people put it:
                            # "what do i eat" matched no entry at all, so a bare dinner
                            # question got the search line.
                            "what do i eat", "what do i cook", "what shall i eat",
                            # A meal to make an effort over names no dish either, and the
                            # line that asks for it often says "impress" and nothing else
                            # ("i need to impress my in laws with dinner", "cooking to
                            # impress"). suggest() is the part that knows to pick a dish
                            # worth the effort, so the key only has to reach it.
                            "impress", "impressing", "to impress", "in laws", "in-laws",
                            "guests", "guest", "dinner party", "special dinner"),
                           # "something easy that looks impressive" names no dish and no
                           # occasion word, and it was read as small talk. The effort is in the
                           # second group so plain "something easy" cannot reach this row.
                           ("impress", "impressing", "impressive", "in laws", "in-laws",
                            "guests", "guest", "special dinner", "made an effort",
                            "looks impressive", "look impressive", "looks like effort"),
                           FOOD_WORDS + ("impress", "impressing", "in laws", "in-laws",
                                         "guests", "guest", "fancy", "special")), suggest,
          bias=-1,
          # A line that names a diet is a constraint on the dish, not a request to be told what
          # to cook: "one of the guests cant eat wheat" was answered with a tray of chicken
          # thighs and sausages, which is the one thing that guest cannot have.
          avoid=("long", "time", "temperature", "oven", "safe", "defrost", "thaw", "reheat",
                 "store", "keep", "burnt", "burning", "smell", "gone", "off",
                 "dairy", "gluten", "wheat", "lactose", "vegan", "vegetarian", "vegetarians",
                 "allergic", "allergy", "coeliac", "celiac", "intolerant",
                 "doesnt eat", "does not eat", "can not eat", "cant eat", "can not have",
                 "cant have",
                 # A person who has stopped eating is an appetite question, not a request for a
                 # dinner: "my mother in law hardly eats" was answered with a dinner suggestion,
                 # and family.elderly-appetite is the row that owns it.
                 "hardly eats", "hardly eat", "barely eats", "barely eat", "wont eat",
                 "won't eat", "stopped eating", "not eating", "isnt eating", "isn't eating",
                 "no appetite", "lost his appetite", "lost her appetite", "off her food",
                 "off his food", "gone off her food", "gone off his food", "not hungry",
                 # A symptom is a question about the symptom, not a request for a dinner:
                 # "what can i eat for constipation" was answered with a dish to sit down to.
                 # UNWELL is this table's own not-a-dish list and the other rows already carry
                 # it through NOT_MINE, so the dinner row joins them instead of keeping a copy.
                 ) + UNWELL
                + OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN + MEASURING
                + DRINK + ANOTHER_MEAL
                # "in laws" and "guests" are asking words here, so a line about what to say to
                # them reached the dinner table ("what do i say to my mother in law who
                # criticises everything" was answered "Quick: tuna pasta in 15"). The words to
                # say are not a dish.
                + SAYING),
    # Two rows were called `meal-ideas`: this one, which answers "suggest me something with
    # chicken", and cooking_entries.py's, which answers "what shall i cook tonight". They are
    # different questions, so this one carries its own name and the id is written once.
    entry("meal-ideas-anything", (("idea", "ideas", "suggest", "suggestion", "suggestions",
                                   "inspiration",
                          "recommend", "recommendation", "options", "something", "quick"),
                         FOOD_WORDS), suggest,
          bias=-1,
          avoid=("book", "books", "film", "films", "movie", "podcast", "album", "gift", "present",
                 "name", "poison", "read", "watch", "tv", "show", "series", "surname", "word",
                 "card", "cards",
                 # "hot" is a food word in this table, so "is a hot tub a good idea" and "is a
                 # hot bath a good idea" were meal ideas: what makes "hot" mean food is the
                 # thing after it, so the things that are not food come out here.
                 "tub", "bottle", "bath", "yoga", "tap", "weather", "radiator", "shower")
                 + OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN + MEASURING
                 + DRINK + HOW_TO + BROKEN + HEALTH + EMPTY,
          # A loose "something" plus a food word is not an ask: a follow-up can pick up the
          # food word from the last answer ("... something or just send a card" after eggs).
          ask=("idea", "ideas", "suggest", "recommend", "option", "options", "inspiration",
               "for dinner", "for tea", "for lunch", "for supper", "to cook", "to make",
               "to eat", "something with", "something quick", "fancy", "hungry", "starving",
               "dinner", "tea", "supper", "lunch", "meal", "cook", "make")),
    # "I have eggs and spinach, what can I make": the ingredients are the question.
    entry("meal-with", (FOOD_WORDS, ("make", "cook", "should i cook", "should i make",
                                     "can i cook", "can i make", "shall i cook", "shall i make")),
          suggest, bias=-1,
          avoid=TECHNIQUE + OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_FOR_ME + HEALTH
                + EMPTY + NOT_MY_KITCHEN + MEASURING + DRINK + HOW_TO + WHAT_GOES + BROKEN
                + SOUP_NAMED),
    # "I've got chicken and potatoes": listing what is in the kitchen is the ask in itself.
    # The second part is how people say "this is what is in my kitchen": a pack, a tin, a
    # leftover. Without those words "i have a pack of cod" scores too low to be an ask.
    entry("meal-haves", (FOOD_WORDS + ("what else can i do with", "what else can i make with",
                                       "what else can i cook with", "what else with",
                                       "something else to do with", "other ideas for",
                                       "any other ideas"), ("have", "has", "got", "only", "pack",
                                      "packs", "packet", "tin", "tins", "bag", "bags", "bunch",
                                      "leftover", "leftovers", "left over", "half a", "few",
                                      "else", "other")), suggest, bias=-1,
          avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_FOR_ME + HEALTH + EMPTY
                + NOT_MY_KITCHEN + MEASURING + DRINK + HOW_TO + WHAT_GOES + BROKEN + AILING_PLANT
                # What is in the kitchen is an ingredient; what has gone wrong with it is the
                # spoilage question. "the jam has white fluff on it" was a baby-food sugar card
                # and "my bread has blue spots" was beans on toast, because the food word plus
                # "have" or "has" is the whole of this row's key. Whatever is named here is the
                # subject of a keeping card instead.
                + SPOILT_FOOD
                + SOUP_NAMED
                + ("how",),
          # A food named *on* something is a mark on it, not an ingredient in the kitchen:
          # "i got egg on my shirt" and "ive got sun cream on my shirt" were both read from the
          # food word alone (an omelette, macaroni cheese) while the mark went unanswered.
          guard=_not_a_mark_and_not_a_row),
    # A limit on the last idea: "something without meat", "no cheese please".
    entry("meal-limit", (("without", "no", "minus", "skip", "vegetarian", "veggie", "vegan"),
                         ("meat", "cheese", "dairy", "fish", "pork", "chicken", "milk", "gluten")),
          suggest, bias=-1, avoid=HEALTH + EMPTY + NOT_MY_KITCHEN + MEASURING),
    # A time limit on the last idea: "and quick, I've only got 20 minutes".
    entry("meal-quick", (("quick", "fast"), ("minute", "minutes", "min", "mins", "time")),
          suggest, bias=-1, avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN + MEASURING
          + DRINK + HOW_TO + BROKEN + HEALTH + EMPTY),
    # The same limit said as a clock: "something on the table in 15 minutes".
    entry("meal-clock", (("minute", "minutes", "min", "mins", "hour", "hours", "half an hour"),
                         ("dinner", "supper", "tea", "eat", "eating", "cook", "cooking", "table",
                          "food", "meal", "lunch", "breakfast", "hungry")),
          suggest, bias=-1, avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN + MEASURING
          + DRINK + HOW_TO + BROKEN + HEALTH + EMPTY + ("been", "how", "long", "oven", "boil", "bake")),
    # "something quick please", "i need something fast", after an idea or before one.
    # As above: the second `meal-hurry`, for "something quick please", and the id is now its own.
    entry("meal-hurry-quick", (("quick", "quicker", "fast", "hurry", "hurry up", "starving"),
                               ("please", "something", "idea", "one", "dinner", "food", "meal")),
          suggest, bias=-1, avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN + MEASURING
          + DRINK + HOW_TO + BROKEN + HEALTH + EMPTY + ("walk", "chat")),
    # Another idea, asked for on its own once one has been offered: "and something quicker".
    entry("meal-more", (("quicker", "faster", "different", "another", "other", "instead",
                         "else"),
                        ("something", "idea", "ideas", "option", "options", "meal", "dinner",
                         "dish")),
          suggest, bias=-1, avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + MEASURING + HOW_TO + BROKEN + HEALTH + EMPTY,
          # "should i tell my boss i'm looking for something else" is "something else" too,
          # so a second idea needs the meal in the line or in the ask.
          ask=FOOD_WORDS + ("dinner", "tea", "meal", "supper", "food", "eat", "tonight", "cook",
                            "cooking", "quick", "quicker", "faster", "hungry")),
    # Something already cooked that has to be used up: "leftover roast lamb", "spare potatoes".
    # "the rest of the joint" is the same question: the rest of a thing already cooked is what
    # has to be eaten up, and the word "rest" there is the remainder rather than a standing time.
    # Cooked chicken and cold pasta have their own leftover facts in bot/knowledge/cooking.py,
    # which say how long they keep as well as what they turn into, so they are not here.
    entry("meal-use-up", (("leftover", "left over", "leftovers", "spare", "use up", "using up",
                          "rest of"),
                          ("turkey", "meat", "beef", "pork", "lamb", "ham", "potato",
                           "potatoes", "vegetables", "veg", "greens", "cabbage", "broccoli",
                           "carrots", "bread", "loaf", "cheese", "joint")),
          # "can I reheat leftover chicken curry" and "how long does it keep" are how-tos,
          # and bot/knowledge/cooking.py has the reheat and fridge facts for them.
          use_up, bias=1, avoid=USE_UP_TECHNIQUE),
    # Tea is the evening meal in Britain and a drink everywhere else, so this entry needs a
    # word that says what to eat ("for tea", "tea time", "cook", "tonight") and the drink
    # words in the avoid keep the kettle questions for cooking.py's brewing facts.
    entry("meal-tea", (("tea", "teatime", "tea time"),
                       ("for tea", "make", "cook", "shall", "should", "whats", "what can i",
                        "ideas", "idea", "quick", "something", "tonight", "supper", "cheap",
                        "easy", "hurry", "starving")),
          suggest, bias=-1,
          avoid=TECHNIQUE + OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + NOT_AN_IDEA + NOT_MY_KITCHEN
          + MEASURING + HOW_TO + BROKEN + HEALTH + EMPTY
                + ("brew", "brewing", "steep", "tea bag", "tea bags", "green tea", "black tea",
                   "cup of tea", "cup of", "mug", "kettle", "herbal", "chamomile", "peppermint",
                   "drink", "drinking", "cold", "desk", "caffeine", "sugar") + SLEEP),
    # A limit said on its own, often a turn after an idea: "i'm eating less meat",
    # "only got half an hour". What it rules out is the whole ask.
    # "and something vegetarian", "make it vegetarian": the limit comes a turn later, with no
    # food word of its own, so the phrases carry the whole ask.
    entry("meal-diet-again", (("something", "anything", "and", "make it", "make", "instead"),
                              ("vegetarian", "vegan", "meat free", "meat-free", "meatless")),
          _later, bias=-1,
          avoid=NOT_FOR_ME + HEALTH + EMPTY + NOT_MY_KITCHEN + MEASURING + DRINK + HOW_TO
                + WHAT_GOES + NOT_AN_IDEA),
    # "something cheaper" after an idea is a limit on it, and so is "im out of cheese": both
    # are said back to a bot that just named a dinner.
    entry("meal-cheaper", (("cheaper", "cheap", "cheapest", "budget", "afford", "save money",
                            "less money", "money is tight"),
                           ("something", "and", "dinner", "tonight", "meal", "idea", "ideas",
                            "make", "cook", "what", "any", "else")),
          _later, bias=-1,
          # "whats the cheapest way to insure my car" reached this entry on "cheapest" and
          # "car": a policy is not a dinner, and no dinner line says insurance
          avoid=NOT_MINE_CHEAP + TECHNIQUE + HEALTH + WHAT_GOES + MEASURING
                + ("insure", "insurance", "insured", "car insurance", "policy", "premium",
                   "third party", "no claims", "mot")),
    entry("meal-out-of", (("out of", "ran out of", "run out of", "none left", "no more"),
                          FOOD_WORDS),
          suggest, bias=-1,
          # "out of" is the key, and "left out of the fridge all night" carries it too. A pantry
          # that ran out is what this row answers; food that was out on the side is the
          # food-safety row's, so those words turn this one away.
          avoid=NOT_MINE_OUT + TECHNIQUE + HOW_TO + HEALTH + WHAT_GOES + MEASURING
                + ("left out", "out of the fridge", "out of the freezer", "all night",
                   "overnight", "two hours", "safe to eat", "gone off")),
    # A dish asked for by its style and nothing else: "whats a good stir fry", "can i do a
    # quick soup". The style word is the whole subject, so the table answers it.
    entry("meal-style", (("what", "whats", "any", "good", "nice", "fancy", "fancy a", "i fancy",
                          "feel like", "up for", "want", "mood", "the mood", "craving", "do",
                          "ideas", "idea", "suggest",
                          "quick", "easy", "best", "make", "cook", "having"),
                         DISH_STYLE),
          suggest, bias=-1,
          avoid=NOT_MINE + TECHNIQUE + HOW_TO + HEALTH + DRINK + SLEEP + WHAT_GOES + MEASURING),
    # Which takeaway to get. "What takeaway should we get" was a shrug, "chinese or indian for
    # tea" got the tuna-pasta plan, and "we always get the same takeaway" got a chat ack. The
    # choosing words are the ask, so "we fancy a takeaway tonight" keeps the question back.
    entry("takeaway-choice",
          (("takeaway", "takeaways", "take away", "chippy", "chip shop", "chinese", "indian",
            "kebab", "kebabs", "thai", "pizza night", "delivery", "deliveroo", "just eat",
            "curry house", "chicken shop"),
           ("should we get", "shall we get", "what should we get", "what shall we get",
            "what should i get", "what shall i get", "which", "which one", "cant decide",
            "can't decide", "decide", "choose", "any ideas", "ideas", "idea", "recommend",
            "what do you think", "or", "we always get", "same takeaway", "same old", "bored of",
            "sick of", "the kids", "kids want", "something different", "not the usual")),
          "Fish and chips feeds a group for the least money and nobody argues about it. If tastes "
          "differ, Indian beats Chinese: more vegetarian mains, and the sides stretch, so two "
          "mains with one rice and one bread feeds three. With a fussy child or someone veggie, a "
          "Chinese with plain rice and a separate veg dish keeps everyone fed. And if it is the "
          "same order every week, add one dish you have never had rather than swapping the whole "
          "thing - that is how you find the next usual.",
          # An order to complain about, a calorie count, a diy version and a takeaway that has to
          # be kept are all other questions, each with its own answer.
          avoid=("calorie", "calories", "healthy", "healthier", "diet", "slimming", "lose weight",
                 "how do i make", "make at home", "recipe", "cook it", "how do i cook", "freeze",
                 "freezing", "reheat", "left over", "leftover", "food poisoning", "hygiene",
                 "arrived cold", "wrong order", "forgot", "missing", "refund", "complain",
                 "complaint", "allergy", "allergic", "gluten", "price", "cheaper", "cost",
                 # a spice in a dish is a recipe or a heat question: "which chinese dish is not
                 # spicy" and "thai green curry paste or powder" are not choosing a takeaway
                 "spicy", "mild", "heat", "paste", "powder", "sauce", "spice", "spices",
                 "ingredient", "ingredients", "marinade")),
    # "im cooking for one tonight, any ideas" is a dinner ask with no food word in it: the
    # one-person note is the whole subject, so it needs its own line in the table.
    entry("meal-for-one", (("cooking", "cook", "dinner", "tonight", "meal", "supper"),
                           ("for one", "for myself", "just me", "on my own", "by myself")),
          suggest, bias=-1,
          # A game is not a dinner: "a game for two people tonight" and "board game for two
          # tonight" were answered with the quick-dinner list, because "tonight" and "for two"
          # are this row's keys and nothing in the line said food. The word that says what the
          # two of them are for decides it.
          avoid=NOT_MINE_ASK + TECHNIQUE + DRINK + SLEEP + HEALTH + HOW_TO
                + GAME_WORDS),
    # The same for two: "dinner for two that looks nice" is a shape of evening, not a food, and
    # "date night" is the same request in the words people use for it.
    entry("meal-for-two", (("cooking", "cook", "dinner", "tonight", "meal", "supper", "date night",
                            "date-night", "anniversary", "nice", "fancy", "special", "treat",
                            "impress",
                            # an occasion is a dinner for two, in the words people use for it:
                            # "what should i cook for valentines day" reached the letter, and once
                            # the letter stood down it was the quick row's tuna pasta. Valentines
                            # is the occasion this row is for.
                            "valentines", "valentine", "valentine's", "valentines day"),
                           ("for two", "for 2", "for three", "for 3", "for four", "for 4",
                            "for five", "for 5", "for the two of us", "date night", "date-night",
                            "anniversary", "romantic", "looks nice", "look nice", "to impress",
                            # "something nice for my girlfriend on friday" is a dinner for
                            # someone in particular, said without naming any food.
                            "for my girlfriend", "for my boyfriend", "for my partner",
                            "for my wife", "for my husband", "for her", "for him",
                            "for my mum", "for my mom", "for my dad", "to say sorry",
                            # the occasion said again in the group that means "make an effort":
                            # a valentines dinner is not the fifteen-minute row's line.
                            "valentines", "valentine", "valentine's", "valentines day",
                            # "whats a nice thing to cook for a date" names a thing, not a dish,
                            # and the shapes that ask for a thing are this row's ask
                            "thing to cook", "something to cook", "nice thing to cook",
                            "something nice to cook", "nice meal", "nice dinner")),
          suggest, bias=-1,
          # A present is not a dinner: "whats a nice present for my dad whos 60" has the "nice"
          # and the "for my dad" this row is keyed on, and a traybake is not an answer to it
          # (bright-comb). The gift rows own a present, a birthday and a voucher.
          # A game is not a dinner either: "a game for two people tonight" and "board game for
          # two tonight" were answered with the quick-dinner list, because "tonight" and "for
          # two" are this row's keys and nothing in the line said food. GAME_WORDS is the same
          # list the games entries read, so the two rows cannot drift apart.
          avoid=NOT_MINE_ASK + TECHNIQUE + DRINK + SLEEP + HEALTH + HOW_TO + GAME_WORDS + (
              "present", "presents", "gift", "gifts", "voucher",
              "buy him", "buy her", "get him", "get her", "what should i get",
              "what can i get", "what to get")),
    # Food to carry is not food to cook: a picnic, a beach day or a long train wants things
    # that travel and eat cold, which is a different list from the dinner table. "We went to
    # the beach" is not this - it needs a word that asks for something to eat or take.
    entry("meal-carry", (CARRY_ASK,
                         ("something", "anything", "make", "take", "bring", "pack",
                          "packing", "food", "eat", "eating", "lunch", "ideas", "idea",
                          "snack", "snacks", "family", "friends", "kids", "children",
                          "toddler", "veggie", "vegetarian", "vegan")),
          _carry, bias=-1,
          # A day out is the reason for the food, not a request for it: "cheap family day out"
          # names no food and no carrying, so the picnic list was the answer to a line about a
          # day that costs nothing. One word that asks for something to eat or take has to be
          # there, which is what the comment above already said the entry needs.
          ask=("something", "anything", "make", "take", "bring", "pack", "packing", "food",
               "eat", "eating", "eaten", "lunch", "lunches", "lunchbox", "lunchboxes",
               "picnic", "picnics", "flask", "cool box", "coolbox", "cooler box", "drink",
               "drinks", "snack", "snacks", "ideas", "idea", "breakfast", "supper",
               "dinner", "tea", "hungry"),
          # The meal table's own guard list names a picnic, because the lunch answer lives in
          # another entry; this entry is the picnic answer, so its own word comes out of it.
          # Money is not a picnic either: "can i get a refund on a flight i didnt take" carries
          # both "flight" and "take", so without these it was answered with a frittata cut in
          # wedges, and the flight answers behind it never got the line.
          avoid=tuple(word for word in NOT_MINE if word not in ("picnic", "picnics"))
                + TECHNIQUE + HOW_TO + HEALTH + SLEEP + DRINK + WHAT_GOES + MEASURING
                + MONEY_MATTERS
                # Where to eat is not what to carry: "and is there anywhere good to eat" after
                # a beach question keeps "beach" in the chat, and a picnic list is a wrong
                # answer to a person choosing a restaurant. The eating-out row has the ask.
                + ("eat out", "eating out", "anywhere to eat", "anywhere good to eat",
                   "anywhere nice to eat", "somewhere to eat", "place to eat", "places to eat",
                   "good place to eat", "restaurant", "restaurants", "cafe", "pub lunch")
                # Whether food may be carried through an airport is the security question, and
                # travel.py's flight-food has the answer; the picnic list is the answer to what to
                # pack for a journey. "can i bring my own lunch on a flight" was a frittata in
                # wedges when the line was asking whether it would be taken off them at the tray.
                + ("airport", "airports", "security", "hand luggage", "carry on", "carry-on",
                   "cabin bag", "100ml", "liquids")
                # A pet that comes along is the thing being carried, not the food: "can i take my
                # dog to the beach" was a frittata in wedges because "beach" and "take" were both
                # here. The pet half of the occasions table is reused rather than written again,
                # and the people half is left out on purpose - a picnic with the kids is food.
                + tuple(word for word in BRING_NOT_FOOD
                        if "dog" in word or "cat" in word)),
    # "and quick" on its own: quicker than the idea they were just given, so no clock and no
    # food word of its own either.
    entry("meal-faster", (("quick", "quicker", "faster", "fast", "soon"),
                          ("and", "please", "make it", "make", "something")),
          _later, bias=-1,
          avoid=NOT_FOR_ME + HEALTH + EMPTY + NOT_MY_KITCHEN + MEASURING + DRINK + HOW_TO
                + WHAT_GOES + NOT_AN_IDEA + SLEEP),
    entry("meal-limit-only", (("less", "no", "without", "only", "instead", "cut down",
                               "cut out", "cutting down", "cutting out", "reduce", "minus",
                               "skip", "quick", "faster", "half an hour"),
                              ("meat", "dairy", "cheese", "fish", "pasta", "rice",
                               "minutes", "minute", "hour", "gluten", "sugar")),
          # "i want to eat less sugar" is a goal, not a request for dinner: like main's meal
          # entry, a limit on its own only answers when there is a word that asks.
          # "only", "got", "need" and "time" are not ask words: they are the key's own words
          # ("only" plus "minutes" is the limit itself), so any line with minutes in it was a
          # request for dinner - "its only ten minutes but i hate it" got a quesadilla, "the
          # meeting is only ten minutes" a chickpea salad, and "i can only manage about five
          # minutes" a twenty-minute frittata. What asks is a food, a meal, or a word like these.
          suggest, bias=-1, ask=("what", "shall", "should", "can i", "could i", "idea", "ideas",
                        "suggest", "recommend", "dinner", "tea", "supper", "lunch", "meal",
                        "cook", "make", "tonight", "quick", "fast", "hurry", "something",
                        "instead", "please", "starving", "hungry"),
          avoid=OWN_MEAL + OTHER_PEOPLE + NOT_A_DISH + MEASURING + HOW_TO + BROKEN + HEALTH + EMPTY),
    # What to order at the counter the line names, which the choosing row does not answer because
    # the line states no choice: "whats nice from a chippy" is a question about the chippy.
    entry("pick-at-the-counter", (TAKEOUT_PLACES, TAKEOUT_ASK),
          _takeout_pick, bias=1, guard=_one_counter,
          avoid=("calorie", "calories", "healthy", "healthier", "diet", "slimming",
                 "lose weight", "nutrition", "how many calories", "how many kcal",
                 "how many carbs", "how much", "price", "cheaper",
                 "cost", "expensive", "cheapest", "deal", "voucher", "discount",
                 "open", "opening", "closing", "closed", "late", "near me", "nearby",
                 "where is", "nearest", "deliver to", "allergy", "allergic", "gluten",
                 "vegetarian", "vegan", "halal", "hygiene", "food poisoning", "refund",
                 "wrong order", "missing", "arrived cold", "complain", "complaint",
                 "how do i make", "make at home", "at home", "recipe", "cook it",
                 "how do i cook", "spicy", "mild", "heat", "paste", "powder", "sauce",
                 "spice", "spices", "marinade", "ingredient", "ingredients", "freeze",
                 "freezing", "reheat", "left over", "leftover", "work", "job", "career",
                 # the counters in another country, and the name of a shop that sells to shops,
                 # are not a line about ordering tonight
                 "wholesale", "bulk", "in spain", "in france", "in italy", "in germany",
                 # the bare word "pizza" is what a line about a pizza says, so the shapes that
                 # ask what goes on one, how to cook one or how to make the dough are named out:
                 # the recipe, the oven and the calorie rows all answer those better.
                 "topping", "toppings", "pizza oven", "pizza stone", "best pizza",
                 "dough", "base from scratch", "how do i make", "make a pizza", "cook a pizza",
                 "should i make", "can i make", "to make",
                 # a time or a heat is the kitchen's question, not the counter's: the bake
                 # time, the oven and the temperature each have their own row, and "how long
                 # do i bake a pizza" / "how long should i cook pizza" / "what temp for frozen
                 # pizza" were all told "one pizza each and a garlic bread to share" here
                 # while "how long does a pizza take in the oven" was answered properly.
                 "how long", "how hot", "bake", "baking", "baked", "oven", "temperature",
                 "temp", "degrees", "gas mark", "minutes", "takes to cook",
                 "take to cook", "until crisp", "until golden",
                 "bad for you", "is pizza",
                 # what to do with the box is the rubbish domain's: "what bin does a pizza box go
                 # in" was answered "one pizza each and a garlic bread to share".
                 "bin", "bins", "recycling", "recycle", "cardboard", "compost", "bin it",
                 "throw away", "get rid", "box", "boxes",
                 # and the base is the kitchen's, not the counter's: "how do i get a crispy
                 # pizza base", "how do i get a crispy crust on pizza" and "how do i stop my
                 # pizza sticking to the tray" were all told "one pizza each and a garlic bread
                 # to share". The words a base is asked about are named and the asking shapes are
                 # not: this is a row that honestly answers "how do i order a pizza online", so
                 # holding out `HOW_TO` here also took the four order and delivery lines to a
                 # payment card, an oven card and a hedge.
                 "crispy", "crisp", "crust", "soggy", "dough", "flour", "yeast", "rise",
                 "prove", "proving", "proofing", "stretch", "stretching", "homemade",
                 "from scratch", "my pizza", "the base", "sticking", "sticks", "stuck",
                 "tray", "trays", "thin crust", "thick crust")),
]

# A dinner party is a meal, but what to wear to one, or what to take to it, is about the clothes
# and the bottle: the party-outfit answer owns those lines. The guard belongs to the whole table
# rather than to one row, because "dinner party" is a meal word in several of them.
for _row in ENTRIES:
    _row.avoid = tuple(_row.avoid) + NOT_A_MEAL_SUBJECT
