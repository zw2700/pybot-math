"""Whether a whole dish is good for you: "is lasagne healthy", "is pizza bad for you".

The nutrition domain answers a food ("is pasta fattening", "how much sugar is in coke") one
ingredient at a time, and it does that well. A dish is a different question: lasagne, pizza, a
kebab and a roast dinner are several foods on one plate, so the row that answers them has to say
what the plate is made of and which part of it is the part to watch. Nothing owned that, so:

    is chilli con carne good for you   -> "beyond what I know well, sorry"
    is lasagne healthy                 -> "I'm not sure about that one, sorry"
    is pizza bad for you               -> the same
    is cottage pie healthy             -> the same
    is a burger good for you           -> the same
    is curry good for you              -> the same
    is soup healthy                    -> the same

and the ones that did answer answered a food rather than the dish: "is fish and chips healthy"
was the oily-fish card, "is pasta bake healthy" the method ("cook the pasta 2 minutes short of
the packet"), "is a kebab bad for you" the frying card, "is cheese on toast healthy" the bread
card, and "is chilli healthy" told the person that spices are not bad for you.

So this is one row keyed on the dish's own name plus a health word, with the verdict as data:
what the dish is made of, the one part that adds up, and the swap that keeps it. It stands down
where the question is really about a food on the plate ("is chicken good for you" is
nutrition's), a portion ("how many calories in a lasagne" is measures'), a method ("how do i
make lasagne") or a child, a pet or a pregnancy, which nutrition's own entry wrapper already
keeps out.

Every dish here is one people ask about in these words; a dish not in the table passes, so the
honest hedge is still there for anything this file does not know.
"""
import re

from .lookup import entry
# The same fence nutrition puts round its rows: a baby, a child, a pet, a pregnancy and the date
# on the pack are all different answers, and a verdict meant for an adult is wrong for every one
# of them. It is written out here rather than borrowed with nutrition's `entry` wrapper because
# one dish name is made of a guard word: "is a hot dog bad for you" is a food question, and the
# wrapper's `dog` would refuse it (the answer came back about keeping a dog cool). So the words
# are nutrition's own, and the reading takes out the dish name before it looks at them.
from .nutrition import _A_STATEMENT_ABOUT_ME, _NOT_A_PERSON_OR_PET, _PACK_DATE

ANSWERS = ("health", "food-and-drink")

# The words that make a line a question about the dish being good for you. "calories" is not one
# of them: how much is in a portion is measures.py's table, and the two answers are different.
_HEALTH_ASK = ("good for you", "good for me", "good for us", "good for my",
               "bad for you", "bad for me", "bad for us", "bad for my",
               "healthy", "unhealthy", "healthier", "healthiest", "fattening", "nutritious",
               "is it healthy", "is that healthy", "how healthy", "is it bad", "is that bad",
               "should i eat", "better for you", "worse for you",
               "diet", "is it junk", "junk food", "clean eating")

# One verdict per dish: what it is made of, the part that adds up, and the swap that keeps it.
# Written to be said in one breath, because the question is a yes-or-no about tonight's dinner.
VERDICTS = {
    "chilli con carne": (
        # "is chilli healthy" was the spices row ("spices are not bad for you"), and the dish is
        # what people mean: a bowl of chilli with rice, not a chilli pepper.
        ("chilli con carne", "chilli con carni", "chili con carne", "chilli con carne",
         "chili con carne", "chilli", "chili"),
        "Chilli con carne is a good everyday meal: lean mince for protein, kidney beans for fibre "
        "and tinned tomatoes, and it is the rice, the cheese and the sour cream that add up. Go "
        "easy on those three and use five per cent mince, and a big bowl is about 400 calories. "
        "The ready-made jars are where the salt is."),
    "lasagne": (
        ("lasagne", "lasagna", "lasagnes"),
        "Lasagne is fine as a meal, and the cheese sauce is the part to watch: a portion is about "
        "450 to 550 calories, and half of that can be the white sauce and the cheese on top. Use "
        "less of both, put a big salad or green beans with it, and the same recipe is a normal "
        "dinner rather than a heavy one."),
    "pizza": (
        ("pizza", "pizzas", "margherita", "pepperoni pizza"),
        "Pizza is bread, cheese and topping, so the thin crust and the vegetable toppings are the "
        "good end of it and a stuffed crust with extra cheese is the other end. A whole 12-inch "
        "one is 1,000 to 1,200 calories, so half with a salad is a meal, and a takeaway one "
        "carries a lot of salt."),
    "fish and chips": (
        ("fish and chips", "fish n chips", "chippy", "chip shop"),
        "Fish and chips is fine once a week: the fish is lean protein and the chips are the fat, "
        "so a portion is around 900 to 1,000 calories. Have mushy peas or a pickled onion "
        "instead of a second handful of chips, and skip the batter on the fish if you want the "
        "biggest single saving."),
    "cottage pie": (
        ("cottage pie", "shepherds pie", "shepherd's pie", "shepards pie"),
        "Cottage pie, or shepherd's pie - the same dish with lamb - is a good meal: lean mince, "
        "vegetables and mashed potato, and the butter and cream in the mash is the part that adds "
        "up. Mash it with a splash of milk instead, add extra carrot and peas to the mince, and a "
        "portion is about 400 calories; with lamb, spoon off the fat before the mash goes on."),
    "burger": (
        ("burger", "burgers", "cheeseburger", "beefburger", "hamburger"),
        "A burger is as good as what it is made of: a plain beef patty or a grilled chicken fillet "
        "is lean protein, and the white bun, the cheese and the chips are the rest. A takeaway "
        "burger meal is 1,000 calories and up, so one at home in a wholemeal bun with salad and a "
        "smaller pile of oven chips is the same dinner at half of it."),
    "curry": (
        ("curry", "curries", "tikka masala", "chicken tikka", "korma", "balti", "dopiaza",
         "rogan josh", "jalfrezi"),
        "Curry is a good way to eat vegetables and pulses, and the cream, the ghee and the oil are "
        "what make a takeaway one heavy: a tikka masala or a korma is 500 to 700 calories a "
        "portion. A tomato-based curry, a dal or a dry-fried one from the same menu is a third to "
        "half of that, and the rice is a fistful rather than a plateful."),
    "pasta bake": (
        ("pasta bake", "tuna bake", "macaroni cheese", "mac and cheese", "cauliflower cheese"),
        "A pasta bake is pasta, sauce and cheese on top, so the cheese and the white sauce are "
        "where the calories are: a portion is 500 to 600 calories, more with a thick cheese "
        "crust. Wholewheat pasta, a tomato-based sauce, half the cheese and a layer of vegetables "
        "in it makes the same dish a lighter one."),
    "soup": (
        ("soup", "soups", "broth", "minestrone", "leek and potato"),
        "Soup is as good as what went in it: a vegetable or lentil soup with beans or chicken in "
        "it is a proper meal, usually 150 to 250 calories a bowl, and a creamy one or a "
        "bread-bowl one is several times that. Watch the salt in the tinned and carton ones, "
        "which is often the whole day's worth in one bowl."),
    "roast dinner": (
        ("roast dinner", "sunday roast", "roast beef", "roast lamb", "roast potatoes",
         "yorkshire pudding"),
        "A roast is a good plate when the vegetables are the biggest thing on it: meat, potatoes "
        "and two or three veg is a balanced meal, and the roast potatoes, the Yorkshire pudding "
        "and the gravy are what push it past 800 calories. Roast the potatoes in a little oil "
        "rather than a lake of fat, and put more greens on rather than a second potato."),
    "cheese on toast": (
        ("cheese on toast", "toastie", "toasted sandwich", "cheese toastie", "grilled cheese"),
        "Cheese on toast is fine as a quick lunch: wholegrain bread and a matchbox-sized piece of "
        "cheese is about 350 calories with good protein and calcium. The cheese is the salty, "
        "fatty part, so grate it rather than slice a thick slab, and a tomato or some Worcestershire "
        "sauce on top means less cheese tastes like more."),
    "kebab": (
        ("kebab", "kebabs", "doner", "shish kebab", "chicken shish"),
        "A kebab is better than its reputation: grilled chicken or shish is lean protein, and the "
        "doner meat, the garlic mayo and the bread are what add up. Ask for chilli sauce and salad "
        "instead of garlic mayo, eat the meat and salad first, and a large doner in a naan is "
        "1,000 calories and up."),
    "full english": (
        ("full english", "fry up", "fry-up", "full breakfast", "cooked breakfast",
         "bacon and eggs"),
        "A full English is not a daily breakfast but it is not junk either: eggs, beans, "
        "mushrooms and grilled tomato are good, and the sausages, bacon, black pudding and fried "
        "bread are the salt and the fat. Grill rather than fry, keep it to two rashers and one "
        "sausage, and it is a 600 to 700 calorie breakfast that keeps you going till lunch."),
    "beans on toast": (
        ("beans on toast", "beans on toast"),
        "Beans on toast is a good cheap meal: the beans give fibre and protein and the toast is "
        "the carbohydrate, about 300 calories for a tin on two slices. The sauce is where the "
        "sugar and salt are, so a reduced-salt tin and wholegrain bread is the same meal done "
        "better, and a bit of cheese grated on top adds protein rather than much fat."),
    "stir fry": (
        ("stir fry", "stir-fry", "stirfry", "stir fried", "wok"),
        "A stir fry is one of the best everyday dinners: lots of vegetables, lean meat, prawns or "
        "tofu, and it is the oil and the noodles that decide the rest. Two teaspoons of oil in a "
        "hot wok and a fistful of noodles rather than a packet is 400 calories, and the "
        "ready-made sauces carry the sugar and salt."),
    "sandwich": (
        ("sandwich", "sandwiches", "butty", "butties", "wrap", "wraps", "baguette"),
        "A sandwich is as good as its filling: lean meat, tuna, egg, cheese or hummus with salad "
        "and wholemeal bread is a balanced lunch at 350 to 450 calories. The mayonnaise, the "
        "thick butter and the big bag of crisps beside it can double that, so mustard or a thin "
        "scrape of mayo and a piece of fruit instead is the same lunch."),
    "risotto": (
        ("risotto", "risottos"),
        "Risotto is rice cooked in stock with a little cheese and butter, so it is a good meal if "
        "the vegetables or seafood are the point of it: a mushroom or pea risotto is about 450 "
        "calories a bowl. Go easy on the cheese and butter stirred in at the end, which is the "
        "part that turns it heavy, and it does not need cream at all."),
    "paella": (
        ("paella", "paellas"),
        "Paella is rice, saffron, vegetables and seafood or chicken, which is a good combination: "
        "a portion is about 450 to 500 calories. The chorizo and the salt are what to watch, and "
        "the rice is the biggest thing on the plate, so more prawns and peppers and a smaller "
        "spoon of rice makes it lighter without changing the dish."),
    "sausage and mash": (
        ("sausage and mash", "bangers and mash", "sausages and mash", "sausage mash"),
        "Sausages and mash is comfort food with a real cost: two good sausages are 300 to 400 "
        "calories and mostly fat and salt, and the butter and milk in the mash add more. Two "
        "sausages, mash with milk only and a big pile of peas or greens is a 550-calorie dinner, "
        "and a chicken or veggie sausage is leaner."),
    "pie": (
        ("steak pie", "chicken pie", "meat pie", "pie and mash"),
        "The pastry is the part that adds up in a pie: a slice of steak pie is 500 to 600 "
        "calories, and a top-only pie with a puff lid is a good deal lighter than one with a base "
        "as well. Fill it with lean meat and vegetables, serve it with greens or beans rather "
        "than chips, and a pie is a normal dinner."),
    "fish pie": (
        ("fish pie", "fishermans pie", "fish pie"),
        "Fish pie is a good meal: white fish and often prawns for lean protein, milk for the sauce "
        "and mashed potato on top, about 400 to 450 calories a portion. The butter and cheese in "
        "the mash are the part that adds up, so mash with milk and save the cheese for the top, "
        "and serve it with peas or greens rather than more bread."),
    "falafel": (
        ("falafel", "falafels"),
        "Falafel is chickpeas, herbs and spices, so it brings fibre and protein that a meat "
        "burger does not have, and it is fried or baked in oil: four falafel are about 220 "
        "calories. Baked falafel or the ones you cook at home in a little oil are lighter than a "
        "takeaway wrap, and a salad with them is a proper meal."),
    "gravy": (
        ("gravy", "gravies", "onion gravy", "bisto"),
        "Gravy is not the calorie problem on a plate - a ladleful is about 30 to 60 calories - it "
        "is the salt, and a stock cube or granules carries most of a day's worth in one jug. "
        "Make it from the roasting juices with a spoonful of flour and a little of the vegetable "
        "water, and it is the cheapest flavour on the table."),
    "toad in the hole": (
        ("toad in the hole", "sausage and yorkshire", "sausages in batter"),
        "Toad in the hole is sausages baked in Yorkshire pudding batter, so it is sausage, flour, "
        "egg and milk with a lot of oil in the tin: a good plateful is 600 to 800 calories. Two "
        "sausages each rather than four, a lot of greens or carrots on the side, and onion gravy "
        "rather than a jug of it, and it is a decent dinner."),
    "quiche": (
        ("quiche", "flans", "savoury tart", "savoury flan"),
        "A quiche is eggs and cream in pastry, so the pastry and the cream are where the calories "
        "are: a shop slice is 350 to 450 calories and a lot of salt in the ham and cheese ones. "
        "A crustless one baked in a lined tin, or a frittata, gives you the same lunch with about "
        "half the calories, and salad on the side is what makes it a meal."),
    "dhal": (
        ("dhal", "dal", "daal", "lentil curry", "tarka dal", "chana masala"),
        "Dhal is lentils simmered with spices, which makes it one of the best cheap dinners there "
        "is: about 200 calories a bowl with 12g of protein and plenty of fibre. The ghee or the "
        "cream stirred in at the end is the part to watch, and a bowl with rice or a chapati and "
        "some spinach is a complete meal."),
    "hot dog": (
        ("hot dog", "hot dogs", "hotdog", "hotdogs", "corn dog"),
        "A hot dog is a frankfurter in a soft bun: the sausage is processed meat and salty, about "
        "150 calories on its own, and the bun and the sauces take it to 300 to 350. One at a "
        "match or a barbecue is fine; the everyday version is a grilled chicken or veggie sausage "
        "in a wholemeal bun with onions and mustard rather than ketchup and mayo."),
    "butty": (
        ("chip butty", "chip barm", "chip muffin", "sausage butty", "sausage sandwich",
         "bacon butty", "bacon sandwich"),
        "A butty is bread with something fried in it, so the bread is the carbohydrate and the "
        "filling is the fat and the salt: a chip butty is about 450 calories, a bacon or sausage "
        "one 350 to 450, and none of them bring any vegetables. It is a good cheap lunch now and "
        "then; have it with a piece of fruit or some salad and it stops being the whole meal."),
    "chow mein": (
        ("chow mein", "chowmein", "chop suey", "singapore noodles"),
        "Chow mein is noodles, vegetables and a little meat or prawn, stir-fried in oil with a "
        "salty sauce: a takeaway portion is 500 to 700 calories and the oil and salt are what "
        "make it heavy. Ask for it with extra vegetables and less sauce, or cook it at home with "
        "two teaspoons of oil, and it is a balanced fast dinner."),
    "biryani": (
        ("biryani", "biriani", "pilau", "pilaf", "fried rice"),
        "Biryani is rice, meat or vegetables and spice, cooked with ghee or oil, so a portion is "
        "500 to 700 calories and the rice is most of it. The meat and vegetables are the good "
        "part, so ask for extra of those, and a raita rather than a creamy sauce keeps it "
        "lighter."),
    "flapjack": (
        ("flapjack", "flapjacks", "cereal bar", "granola bar", "breakfast bar"),
        "A flapjack is oats held together with butter, syrup and sugar, so it is a biscuit with "
        "fibre in it: a shop one is 200 to 250 calories and 15g of sugar, and a cereal bar is "
        "often much the same. It is a better snack than a chocolate bar and it is not a healthy "
        "one; a handful of nuts or a yoghurt with fruit keeps you going longer for the same "
        "calories."),
    "milkshake": (
        ("milkshake", "milk shake", "shake from", "frappe", "smoothie milkshake"),
        "A milkshake is milk, ice cream and syrup, so a large one is a dessert in a cup: 500 to "
        "700 calories and 60g of sugar in the fast-food ones. Milk with a banana and a spoon of "
        "cocoa blended at home is about 200 calories and gives the same thick drink with real "
        "protein in it."),
    "houmous": (
        ("houmous", "hummus", "humous", "houmus"),
        "Houmous is a good thing to have in the fridge: chickpeas, tahini, lemon and oil, so it "
        "brings fibre and a little protein, and two tablespoons is about 100 calories. The oil "
        "and tahini are where the calories are and the dippers are what decide the snack, so "
        "carrot, cucumber and pepper with it rather than half a bag of pitta."),
    "coleslaw": (
        ("coleslaw", "slaw"),
        "Coleslaw is cabbage and carrot in a dressing, so the vegetables are the good part and "
        "the mayonnaise is the rest: a heaped tablespoon is about 100 calories, most of it oil. "
        "A yogurt or half-mayo dressing, or vinegar and a little oil, turns it into a genuinely "
        "light side, and it counts as a portion of veg either way."),
    "pasty": (
        ("cornish pasty", "pasty", "pasty company", "steak bake"),
        "A pasty is pastry, potato and a little meat, and the pastry is the half of it: a large "
        "one is 500 to 700 calories and a lot of salt. A small one with a salad or some fruit is "
        "a lunch; a large one plus chips is lunch and dinner in one, and the filling is mostly "
        "potato rather than meat."),
    "sausage roll": (
        ("sausage roll", "sausage rolls", "sausage sandwich", "sausage butty"),
        "A sausage roll is sausage meat in puff pastry, so it is fat and salt in a small package: "
        "a standard one is about 300 to 350 calories and a big bakery one around 500. Two of them "
        "and a coffee is a full lunch for most people, so one with something with fibre - a piece "
        "of fruit, some soup - is the better way to have it."),
    "nuggets": (
        ("chicken nuggets", "nuggets", "chicken goujons", "goujons", "chicken dippers",
         "turkey dinosaurs"),
        "Chicken nuggets are chicken, breadcrumbs and oil, and the breadcrumb and the frying are "
        "most of the calories: five shop ones are about 250 calories with around 12g of fat. "
        "Oven-baked rather than fried, or a grilled fillet cut into strips and dipped in breadcrumbs "
        "baked at home, and they stop being the junk version of a good food."),
    "burrito": (
        ("burrito", "burritos", "wrap meal", "quesadilla", "enchilada"),
        "A burrito is a big flour tortilla with rice, beans or meat and cheese, so it is a full "
        "meal in one hand: 600 to 800 calories, and the rice and cheese are what fill it. Beans "
        "instead of double meat, no sour cream, and asking for extra salsa and salad leaves makes "
        "the same wrap a lighter lunch."),
    "croissant": (
        ("croissant", "croissants", "pain au chocolat", "pastry for breakfast", "danish pastry"),
        "A croissant is flour and butter folded into layers, so a plain one is about 250 to 300 "
        "calories and mostly fat, and a pain au chocolat about 350 with the sugar. One with "
        "coffee is a fine breakfast now and then; two are a meal, and they leave most people "
        "hungry again by ten because there is so little protein or fibre in them."),
    "granola": (
        ("granola", "granolas", "muesli", "fruit and nut granola"),
        "Granola looks healthier than it is: the oats are good, but the honey or syrup and the oil "
        "it is baked with make a 50g serving about 250 calories and often 12g of sugar. Plain "
        "muesli or porridge with fruit gives the same oats with a fraction of the sugar, and if "
        "you keep the granola, 30g on top of yogurt is the portion."),
    "ploughmans": (
        ("ploughmans", "ploughman's", "ploughmans lunch", "cheese and pickle sandwich"),
        "A ploughman's is bread, cheese and pickle with salad, which is a balanced lunch - and the "
        "cheese and the bread are the two big pieces, so a matchbox of cheese and two slices is "
        "about 500 calories. Ask for more salad and apple and less bread and it is a good pub "
        "choice; the pickle and the cheese are where the salt is."),
    "couscous": (
        ("couscous", "cous cous", "bulgur wheat", "bulghur"),
        "Couscous is steamed semolina, so it is much like rice or pasta: about 110 calories per "
        "100g cooked, and it is what goes with it and how much of it that decides the meal. It "
        "takes flavour from lemon, herbs and roasted vegetables better than rice does, so it is a "
        "good base for a salad, and a fistful dry is a portion."),
    "fish finger sandwich": (
        ("fish finger sandwich", "fish finger butty", "fish fingers", "fish sticks"),
        "Fish fingers are fish in breadcrumbs: four of them are about 200 calories and the "
        "breadcrumbs are fried, so a sandwich of them with butter and ketchup comes to about 500. "
        "Grilled rather than fried, wholemeal bread and a little ketchup with no butter is the "
        "same lunch at 400, and it is a decent source of protein and omega-3 for the price."),
    "noodles": (
        ("instant noodles", "pot noodle", "noodle", "noodles", "ramen", "super noodles"),
        "Instant noodles are mostly white carbohydrate and salt: a packet is 350 to 400 calories "
        "and often half a day's salt in the flavour sachet. Use half the sachet, add an egg, "
        "spinach or frozen peas, and it becomes a quick meal rather than a snack, which is the "
        "difference between the packet and the pot."),
    "salad": (
        ("salad", "salads", "side salad", "green salad", "caesar salad"),
        "A salad is as good as the dressing: leaves and vegetables are almost free calorie-wise, "
        "and two tablespoons of oily dressing is 150 calories of pure fat. Keep the dressing on "
        "the side and use a little, add protein - egg, tuna, chicken, chickpeas, cheese - and a "
        "salad is a real meal rather than a side. A bought Caesar or pasta salad is a different "
        "thing entirely, often 400 calories or more."),
    "chips": (
        ("chips", "french fries", "fries", "oven chips", "chips from the chippy"),
        "Chips are potatoes and oil, and oven chips have about a third of the fat of fried ones: a "
        "portion of oven chips is 200 to 250 calories against 400 or more for a chippy portion. "
        "Leave the skins on, spread them out so they crisp rather than steam, and have them with "
        "protein and vegetables rather than as the whole meal."),
    "takeaway": (
        ("takeaway", "take away", "takeout", "take out", "chinese takeaway", "indian takeaway"),
        "A takeaway is not automatically bad, but the portions and the oil are bigger than what "
        "you would cook: a Chinese or Indian takeaway for one is usually 900 to 1,200 calories. "
        "Order one dish rather than three, with plain rice rather than fried, and eat half and "
        "keep the rest for tomorrow."),
    "halloumi": (
        ("halloumi", "halloumi fries", "veggie burger", "vegetarian burger", "vegan burger"),
        "Halloumi is cheese, so it is high in salt and fat: a 100g portion is around 320 calories "
        "and a lot of the day's salt. Grill it rather than fry it, have it with salad and "
        "vegetables rather than chips, and it is a good way to make a meat-free meal rather than a "
        "healthy one on its own."),
}

# The dish names, longest first, so "fish and chips" is read before "chips" and "chilli con
# carne" before a shorter form. A name two dishes could claim ("shepards pie") belongs to the
# first dish that lists it, which is why `_by_name` is built in table order.
_by_name = {}
for _dish, (_names_for_dish, _text) in VERDICTS.items():
    for _name in _names_for_dish:
        _by_name.setdefault(_name, _dish)
_NAMES = sorted(_by_name, key=lambda name: (-len(name.split()), -len(name)))


# The words nutrition's fence is made of, as one list, for the reading below.
_FENCE = tuple(_NOT_A_PERSON_OR_PET) + tuple(_A_STATEMENT_ABOUT_ME) + tuple(_PACK_DATE)


def _fenced(said):
    """True when the line is about a child, a pet, a pregnancy, a diet or a pack date.

    The dish name is taken out first, because one of them holds a fence word: "hot dog" said
    `dog`, so "is a hot dog bad for you" was fenced out of this row and a pet-care row answered
    it with how a dog cools down. `is that ok for my dog` still fences, because `hot dog` is not
    in it and `my dog` is.
    """
    rest = " " + said + " "
    for name in _NAMES:
        rest = rest.replace(f" {name} ", " ").replace(f" {name}s ", " ")
    return any(f" {word} " in rest or f" {word}s " in rest for word in _FENCE)


def _the_dish(memory, understood):
    """The verdict for the dish the line names, or None when it names none of them.

    The names are read here rather than kept in the key, because a key would have to hold every
    alias of every dish to reach the row: this way one row answers "is lasagne healthy" and "is
    a lasagne bad for me", and the reading decides which dish the answer is about.
    """
    said = " " + re.sub(r"[^a-z0-9' ]+", " ", str(understood.get("clean") or "").lower()) + " "
    said = re.sub(r"\s+", " ", said)
    if _fenced(said):
        return None
    for name in _NAMES:
        if f" {name} " in said or f" {name}s " in said:
            return VERDICTS[_by_name[name]][1]
    return None


ENTRIES = [
    # One row for every dish in the table: the health words are the ask, and the guard reads
    # which dish the line named. A portion question ("how many calories in a lasagne") names one
    # of the health words only by accident, so "calories" is deliberately not in the ask, and a
    # method question ("how do i make lasagne") names none of them at all.
    entry("dish-is-it-good-for-you",
          # the names are in the key so the row is reachable at all: a line with no dish word in
          # it should find nothing here. The long ones are phrases, so a dish scores higher than
          # the single food inside it ("fish and chips" beats the oily-fish row's "fish").
          (tuple(_NAMES), _HEALTH_ASK),
          _the_dish,
          # A food on the plate is nutrition's own row and a portion is measures': "is chicken
          # good for you" is a chicken breast, not a chicken dinner, and both rows say more than
          # this one can. What a dish is called but not eaten as - a pet's food, a brand, a
          # restaurant - is not this question either.
          avoid=("how many calories", "how much sugar", "how much salt", "how much fat",
                 "how much protein", "recipe", "how do i make", "how do i cook",
                 "what goes with", "what to serve", "side dish", "calories in",
                 "carbs in", "protein in",
                 # A pet, a child, a pregnancy and a pack date are fenced in `_fenced` rather
                 # than listed here: the fence takes the dish name out of the line first, so
                 # "is a hot dog bad for you" is a question about the food and "is a hot dog
                 # bad for dogs" is not. Listing "dog" here is what sent that first line to the
                 # pet-care row, which explained how a dog cools down.
                 "restaurant", "menu", "delivery", "order",
                 # keeping and safety are their own answer and a calorie verdict is the wrong
                 # one: "is leftover pizza still ok to eat" wants the fridge rule, not the
                 # number, and "is it ok to eat pink burgers" wants the 71C.
                 "leftover", "left over", "left out", "still ok", "still good", "still safe",
                 "safe to eat", "ok to eat", "next day", "reheat", "reheated", "cold",
                 "fridge", "freezer", "freeze", "how long does", "how long will", "how long can",
                 "gone off", "pink", "raw", "undercooked", "use by", "out of date",
                 # a comparison of two foods is not a verdict about one, and "is granola
                 # healthier than porridge" has its own row that weighs both.
                 "than", " vs", "versus", "or porridge", "or cereal", "instead of"),
          bias=1),
]
