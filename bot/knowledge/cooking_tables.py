"""The big tables of cooking: what a recipe is, what is in a pantry, what a food holds.

Kept here so bot/knowledge/cooking.py stays under the size the uploader takes. Data only:
nothing in this module reads a line.
"""

NOT_WANTED = {
    "rice cooker": ("without", "no", "dont", "don't", "havent", "haven't"),
    # There is a short method row for buttermilk under BASICS, but "how do i make buttermilk" is
    # the cheat for it (lemon juice in milk, five minutes) and not the method, so it stands down.
    "buttermilk": ("make", "making", "makes", "substitute", "instead", "without", "no", "dont",
                   "don't", "havent", "haven't", "don't have", "replace", "swap", "keeps", "keep",
                   "store", "storing", "freeze", "freezer", "frozen"),
    # a question about eating more of them is not a question about the pan: "how do i eat more
    # vegetables" wants the habits answer, and a five minute method for it is the wrong one
    'vegetables': ("grow", "plant", "garden", "allotment", "juice", "smoothie", "frozen", "tin",
                   "more", "eat", "eating", "eaten", "fussy", "kids", "children", "family",
                   "diet", "calories", "portion", "portions", "serving", "servings"),
    'onions': ("pickled", "raw", "rings", "spring", "red onion", "shallot", "soup", "stuffed",
               "bhaji", "chutney", "cry", "crying", "eyes", "smell", "smells", "smelly", "stink",
               "stinks", "fridge", "freezer", "frozen", "keeping", "keep", "store", "storing"),
    'chop an onion': ("cry", "crying", "tears", "eyes", "pickled", "raw", "rings", "ring",
                      "spring", "red onion", "shallot", "soup", "stuffed", "bhaji", "chutney",
                      "smell", "smells", "smelly", "stink", "stinks", "fridge", "freezer",
                      "frozen", "keep", "keeping", "store", "storing", "grow", "plant",
                      "caramelise", "caramelize", "soften", "sweet", "french onion"),
    # A prep job turns itself down when the line is about something else the same words can mean:
    # baked potatoes, garlic bread, avocados that will not ripen, pineapples on pizza.
    'peel a potato': ("grow", "plant", "boil", "roast", "bake", "mash", "chip", "chips", "watery",
                      "sprout", "sprouts", "green", "eyes", "salad", "soup", "gnocchi",
                      "freezer", "frozen", "store", "keeping", "keep", "brown", "browning"),
    'chop garlic': ("bread", "butter", "grow", "plant", "smell", "smells", "smelly", "breath",
                    "hands", "press", "roast", "sauce", "aioli", "mayo", "mayonnaise", "powder",
                    "granules", "store", "keep", "freezer", "frozen", "sprout", "sprouts"),
    'peel ginger': ("tea", "grow", "plant", "powder", "ground", "biscuit", "bread", "cake", "beer",
                    "ale", "pickled", "sushi", "store", "keep", "freezer", "frozen", "root"),
    'chop a carrot': ("boil", "roast", "grow", "plant", "soup", "cake", "muffin", "raw", "salad",
                      "stick", "sticks", "batons", "freezer", "frozen", "store", "keep"),
    'chop mushrooms': ("pizza", "stuffed", "garlic", "toast", "pasta", "soup", "risotto", "pie",
                       "grow", "pick", "wild", "forage", "freezer", "frozen", "dried", "dry",
                       "raw", "eat", "store", "keep", "slimy", "gone off"),
    'cut an avocado': ("toast", "salad", "guacamole", "ripen", "ripe", "brown", "browning",
                       "store", "keep", "freezer", "frozen", "smoothie", "plant", "tree", "grow",
                       "sushi", "calories", "healthy", "good for"),
    'peel a mango': ("juice", "smoothie", "chutney", "dried", "ripen", "ripe", "grow", "tree",
                     "salad", "salsa", "sticky", "ice cream", "store", "keep", "freezer"),
    'cut up a pineapple': ("pizza", "juice", "upside", "cake", "grow", "plant", "skin", "coconut",
                           "tin", "can", "ring", "rings", "dried", "ripen", "ripe", "store",
                           "keep", "freezer", "frozen"),
    'juice a lemon': ("cake", "drizzle", "curd", "preserve", "pickle", "tree", "grow", "plant",
                      "water", "detox", "morning", "hot", "tea", "store", "keep", "freezer",
                      "peel", "zest"),
    'corn on the cob': ("popcorn", "flour", "starch", "syrup", "tin", "can", "kernels", "fritter", "chowder", "bread"),
    'butternut squash': ("soup", "risotto", "seeds", "grow", "plant", "carve", "pumpkin"),
    # "do i need to soak broad beans" is the dried ones, and the dried-bean row is the one that
    # knows about soaking: a person who asks about soaking a bean has never meant the fresh pod.
    # The fresh row stands down on every soaking word, and on "dried"/"dry" beside the name.
    'broad beans': ("soak", "soaks", "soaking", "soaked", "overnight", "dried", "dry", "dries",
                    "tinned", "canned", "tin", "can", "bag", "packet"),
    'pork chops': ("slow cooker", "casserole", "apple", "cider", "butterfly", "cheap"),
    'fish': ("tank", "tanks", "aquarium", "fish tank", "fishbowl", "fish bowl", "gravel",
             "filter", "dechlorinator", "fish and chips", "fish fingers", "pond", "pet", "smell", "smells",
             "smelly", "shellfish", "allergy", "market", "monger", "batter", "smoke", "smoked",
             "smoking", "cure", "cured", "gravad", "gravlax", "kipper", "kippers", "cat", "cats",
             "dog", "dogs", "raw", "sashimi", "sushi", "stock", "sauce", "pie", "cakes",
             "fishcake", "fishcakes", "frozen", "freezer", "thaw", "defrost", "leftover",
             "leftovers", "more", "eat", "eating", "eaten", "portion", "portions", "serving",
             "servings", "twice", "week", "healthy", "oily"),
}

MEAL_IDEAS = (
    (("mince", "minced beef", "ground beef", "beef mince"),
     "Brown a packet of mince with a chopped onion, then add a tin of tomatoes and a stock cube: "
     "20 minutes gives bolognese, or add kidney beans, cumin and chilli powder for chilli. Top it "
     "with mashed potato and grill it if you want a cottage pie."),
    # "what can i make with leftover chicken" names a chicken to use up, not one to cook: the
    # raw-chicken idea below told somebody with cooked chicken to fry strips of it. The names
    # start earlier in the line than "chicken" does, so this row wins for those lines only.
    (("leftover chicken", "left over chicken", "cooked chicken", "already cooked chicken",
      "leftover turkey", "cooked turkey"),
     "Cooked chicken needs no cooking: fold it into a curry, risotto or soup for the last two "
     "minutes, layer it in a pie under pastry, or use it cold in a salad with mayonnaise, lemon "
     "and something crunchy. Reheat it once, until piping hot all the way through."),
    (("chicken", "chicken breast", "chicken thighs"),
     "Cut chicken into strips and fry it with an onion, then add a tin of tomatoes or a jar of "
     "curry sauce: rice or pasta turns either into dinner in about 20 minutes. Thighs are more "
     "forgiving than breast if you are new to it."),
    (("egg", "eggs"),
     "Eggs are a whole meal: an omelette with whatever cheese and vegetables you have, scrambled "
     "eggs on toast, or a quick frittata finished under the grill. All three take under 15 "
     "minutes."),
    (("potato", "potatoes"),
     "Boil diced potatoes for 12 minutes, then fry them with onion and any meat or veg for a "
     "quick hash, or top baked ones with beans and cheese. Chop them small so they cook in the "
     "time the rest does."),
    (("pasta", "spaghetti", "penne", "noodles"),
     "Boil the pasta, and while it cooks soften garlic in olive oil, add a tin of tomatoes and a "
     "pinch of chilli: sauce and pasta are ready together in 12 minutes. A splash of the pasta "
     "water makes the sauce cling."),
    (("rice",),
     "Cook the rice, then fry it with an egg, frozen veg and soy sauce: about 10 minutes from "
     "cold rice to egg fried rice. Or stir a tin of beans and tomatoes through it for a one-pan "
     "dinner."),
    (("tomato", "tomatoes", "tinned tomatoes", "chopped tomatoes"),
     "A tin of tomatoes is a sauce: soften onion and garlic, add the tomatoes and simmer 10 "
     "minutes, then use it on pasta, with beans, or over chicken. A pinch of sugar fixes a tin "
     "that tastes sharp."),
    (("chickpea", "chickpeas", "beans", "lentils"),
     "Fry onion and garlic, add a tin of chickpeas, beans or lentils with tomatoes and cumin, and "
     "simmer 15 minutes: a filling dinner with rice or bread. Lentils cook in the same time as "
     "rice, so they are the cheapest way to make a meal bigger."),
    (("cheese",),
     "Cheese turns most things into dinner: grate it over pasta with a splash of the cooking "
     "water, toast it on bread with tomatoes, or melt it into an omelette. A grilled cheese on "
     "toast with a fried egg on top is a proper quick tea."),
    (("tuna",),
     "Tuna, pasta and a tin of tomatoes make a 15-minute dinner, or mix tuna with mayonnaise, "
     "sweetcorn and pasta for a cold lunch. Add the tuna at the end so it stays in flakes."),
    (("sausage", "sausages"),
     "Fry or roast the sausages while potatoes boil, then mash them with butter for bangers and "
     "mash; any leftovers go into a pasta bake. Leave them whole and cook them gently, because a "
     "pricked sausage leaks its fat and splits anyway."),
    (("fish", "salmon", "cod"),
     "Wrap the fish in foil with lemon and butter and bake at 200C (180C fan) for 12 to 15 "
     "minutes, with rice or potatoes on the side. It is done as soon as the flesh flakes."),
    (("bread", "toast"),
     "Bread is dinner if you toast it: beans on toast, a fried-egg sandwich, or a cheese toastie "
     "with a tin of soup. A grated-cheese-and-onion toastie takes 5 minutes in a dry pan."),
    (("mushroom", "mushrooms"),
     "Fry mushrooms hard until golden, then add cream or creme fraiche and serve them on toast or "
     "with pasta. Do not crowd the pan or they steam instead of browning."),
    (("vegetables", "veg", "broccoli", "carrots"),
     "Roast chopped veg at 200C (180C fan) for 25 minutes with oil and salt, then stir it through "
     "pasta or rice; a fried egg on top makes it a meal. Frozen veg works too, straight into the "
     "pan for the last 5 minutes."),
    (("bacon",),
     "Bacon makes a quick pasta: fry it with an onion, add a tin of tomatoes or a splash of cream, "
     "and toss it with pasta. The fat in the pan is the flavour, so do not pour it away."),
)

SIDES = (
    (("roast chicken", "roast dinner", "roasting chicken", "turkey", "whole chicken"),
     "Roast potatoes in the same oven for the last 45 minutes (boil them 10 minutes first, drain "
     "and shake them in hot oil and salt), and peas or greens with butter. Gravy from the tin is "
     "fine. If there is room, a tray of carrots, parsnips and onion can go in beside the bird, so "
     "the whole dinner comes out of one oven."),
    (("sausages", "sausage", "bangers"),
     "Mash and onion gravy: boil the potatoes 15 minutes, mash them with butter and milk, and "
     "soften sliced onion in the sausage pan with a spoon of flour and a splash of stock for the "
     "gravy. Peas take 3 minutes, and the pan the sausages cooked in is the flavour."),
    (("lamb", "lamb chops", "roast lamb"),
     "New potatoes with butter and mint, peas, and yoghurt stirred with chopped mint and lemon "
     "instead of mint sauce. Roast carrots and parsnips if the oven is on anyway; both take about "
     "40 minutes beside the meat."),
    (("steak", "beef", "roast beef"),
     "Chips and a sharp green salad, or a jacket potato if the oven is already on. Cook the steak "
     "last and rest it 5 minutes, then dress the salad in the pan with oil, vinegar and a spoon of "
     "mustard so nothing in it is wasted."),
    (("salmon", "fish", "cod", "haddock", "fishcakes", "fish pie"),
     "New potatoes and peas, or rice with greens wilted in a pan with butter. A squeeze of lemon "
     "and yoghurt with chopped dill is all the sauce it needs, and both take less time than the "
     "fish."),
    (("curry", "chilli", "daal", "dal", "dhal"),
     "Rice, and naan or a chapati if you have them. Grate cucumber, salt it for 10 minutes and "
     "squeeze it dry, then mix with yoghurt and cumin for a raita that cools the heat; mango "
     "chutney and coriander if they are in the cupboard."),
    (("pasta", "spaghetti", "lasagne", "lasagna"),
     "Garlic bread and a green salad with a sharp dressing, because the salad is what cuts through "
     "the sauce. Tear the bread, rub it with garlic, oil and salt and give it 8 minutes in a hot "
     "oven while the pasta cooks."),
    # "grill" was in this list and it is a machine, not a dish: "what goes with it" after a grilled
    # corn answered coleslaw, and a grill line that names a food should get that food's side.
    (("burger", "burgers", "hot dogs", "barbecue", "bbq"),
     "Coleslaw, chips and pickles: shred cabbage and carrot, salt it, squeeze it dry and mix it "
     "with mayonnaise and a splash of vinegar. Corn on the cob and a bowl of potato salad fill the "
     "same table without any more cooking."),
    (("shepherds pie", "shepherd's pie", "cottage pie", "pie", "stew", "casserole"),
     "Peas or greens with butter, and bread and butter to mop the plate. A spoon of mustard or "
     "horseradish on the side cuts through a rich pie, and both take 5 minutes from frozen."),
    (("soup", "broth"),
     "Bread and butter, or a cheese toastie cut in fingers for dipping. Something crunchy on top "
     "- toasted seeds, croutons, a handful of crisps - turns a bowl of soup into a meal."),
    (("risotto", "paella", "pilaf"),
     "A green salad with lemon in the dressing, and bread. Keep the salad cold and sharp, since "
     "the rice is rich and soft, and put it on the table at the same time as the pan."),
    # "what goes with chips" was answering with how to salt them; the chips are the side here.
    (("chips", "fries", "french fries"),
     "Fish fingers, a fried egg or a burger, and something sharp with them: peas, pickles or "
     "coleslaw, or a chip butty with white bread, butter and vinegar."),
    (("ham", "gammon", "pork"),
     "New potatoes, peas, and mustard or pickles: a spoon of mustard in the juices in the pan "
     "makes the sauce, and cabbage braised in butter fills the plate for very little."),
    (("rice", "pilau", "basmati"),
     "Rice is the blank part of the plate, so it wants something wet and sharp with it: a curry, "
     "a daal, a chilli or a stir-fry, or grilled chicken with soy, ginger and lime. A spoon of "
     "yoghurt with mint or a squeeze of lemon on the rice itself makes the plainest meal taste "
     "finished."),
    (("mash", "mashed potato", "baked potato", "jacket potato", "potato", "potatoes",
      "new potatoes", "boiled potatoes", "chips"),
     "Potatoes want something with juice on it: sausages and onion gravy, a pie, a stew, or a "
     "roast with the meat juices poured over. Peas, greens or a sharp pickle alongside stop it "
     "tasting flat, and for mash warm the plates and beat in butter and warm milk at the end."),
    (("chicken", "chicken thighs", "chicken breast"),
     "Roast potatoes or mash, and something green with butter, plus a sauce made in the pan: "
     "splash in stock or wine, scrape the brown bits up and let it reduce for 2 minutes. That is "
     "a whole dinner from what is already on the hob."),
    (("halloumi", "halloumi cheese"),
     "Halloumi is salty and squeaky, so it wants something juicy and sharp: tomatoes with lemon "
     "and herbs, couscous with chopped apricots, or a flatbread with yoghurt and a little chilli. "
     "Fry it dry in a hot pan for a minute a side and eat it straight away, while the middle is "
     "still soft."),
    # Its own line, because a feta question answered with "halloumi is salty and squeaky" is the
    # wrong cheese described: feta is crumbly and wants sweet or juicy things, not a dry pan.
    (("feta", "feta cheese"),
     "Feta is salty and crumbly, so it wants something sweet or juicy against it: watermelon, "
     "roasted peppers, tomatoes and cucumber with lemon and oregano, or a tray of roasted veg and "
     "chickpeas with feta crumbled over at the end. It does not melt, so add it last."),
    # The cob is usually the side itself, so it wants the wet, sharp things beside it rather
    # than another potato: "what goes with corn on the cob" was a search punt.
    (("corn on the cob", "sweetcorn", "corn"),
     "Butter, salt and pepper, and then the wet, sharp things next to it: coleslaw, a tomato and "
     "red onion salad with lime, or a spoon of chilli butter melted over the cobs. It sits beside "
     "a barbecue, a roast chicken or a bowl of chilli without any more cooking, and 2 minutes "
     "under a hot grill after boiling blisters the kernels."),
    (("prawns", "prawn", "king prawns", "shrimp", "prawn linguine"),
     "Prawns take two minutes, so the rest is what you make first: garlic, chilli and butter in "
     "a pan with parsley, tossed through pasta or piled on toast, and a green salad or lemony "
     "courgette ribbons beside it. Bread to mop the pan is the best part."),
)

SEASONINGS = (
    (("roast lamb", "leg of lamb", "lamb chops", "lamb", "mutton"),
     "Rosemary, garlic and black pepper are the classic on lamb: push slivers of garlic and "
     "rosemary into a leg, or rub chops with oil, salt, crushed garlic and a pinch of cumin. "
     "Anchovy mashed into the rub, or a spoon of mint sauce stirred through yoghurt, is the other "
     "one that works. Salt the meat the night before if you have the time."),
    (("roast beef", "steak", "beef", "brisket"),
     "Beef wants salt and coarse black pepper, and not much else: salt a steak 40 minutes before "
     "it goes in the pan, or rub a roast with mustard, thyme and horseradish before it goes in the "
     "oven. A spoon of horseradish in creme fraiche is the sauce, not the seasoning."),
    (("roast chicken", "whole chicken", "chicken thighs", "chicken breasts", "chicken", "turkey"),
     "Lemon, garlic, thyme and paprika: rub the skin with oil, salt, lemon zest, crushed garlic "
     "and a spoon of paprika, and put half a lemon inside. For pieces, the same mix with cumin "
     "instead of paprika is what most traybakes want."),
    (("pork", "pork chops", "belly pork", "gammon", "ham"),
     "Fennel seed, sage and black pepper are made for pork: crush the fennel, mix it with salt and "
     "rub it into the fat, and put sage leaves under the skin. A little mustard or cider in the "
     "pan at the end finishes it."),
    (("salmon", "fish", "cod", "haddock", "trout"),
     "Fish takes lemon, dill and butter, and salt before it cooks rather than after: zest the "
     "lemon over it, lay dill on top and put a knob of butter on each piece. Paprika or fennel "
     "seed for a fillet that will be fried hard."),
    # tofu sat in the cheese line, and "what seasoning for tofu" came back describing halloumi
    # and feta; tofu has no salt of its own at all, which is the opposite advice
    (("tofu", "firm tofu", "silken tofu", "tempeh"),
     "Tofu has no salt or fat of its own, so it needs both: soy sauce, sesame oil, garlic and "
     "ginger, or a marinade it sits in for half an hour after being pressed. Fry it hard in a "
     "little oil first, until the edges are brown, and sauce it after - added wet, it steams and "
     "stays pale."),
    (("halloumi", "feta"),
     "Chilli, lemon and oregano, with salt only if the cheese needs it: halloumi and feta are "
     "already salty, so they want heat and acid instead. Tofu wants soy, garlic and ginger before "
     "it goes in the pan, and a little cornflour to help it brown."),
    # "any good rub for ribs" and "how do i do ribs on the barbecue" named no food this table
    # held, so the rub question was a shrug. Ribs take the sweet, smoky, sticky rub rather than
    # the beef one, because they are cooked longer and need sugar to crust before it burns.
    (("ribs", "rack of ribs", "pork ribs", "spare ribs", "baby back ribs", "beef ribs"),
     "Ribs want sugar in the rub and acid in the sauce: brown sugar, paprika, salt, black pepper, "
     "garlic powder and a little cumin, rubbed on the night before or an hour ahead. Cook them "
     "low, covered, for two to three hours at 150C, then paint with barbecue sauce and finish "
     "them hot for ten minutes. The sugar is what makes the crust, and it burns above 200C, so "
     "sauce goes on late."),
    (("potato", "potatoes", "new potatoes", "roast potatoes", "chips"),
     "Salt, oil and a herb that can take the heat: rosemary or thyme in the tray with the potatoes, "
     "and salt in the water they boil in, not only at the end. Paprika or garlic granules dusted "
     "on halfway through browning."),
    (("rice", "pilau", "basmati", "couscous"),
     "Rice wants salt in the water, a bay leaf or a cardamom pod while it cooks, and butter or oil "
     "stirred through at the end. Cumin seeds fried in the oil first is what turns plain rice into "
     "pilau."),
    (("tomatoes", "tomato", "cherry tomatoes", "passata"),
     "Tomatoes want salt, a little sugar if they are pale, and a herb that is not shy: basil "
     "torn in at the end for a salad, oregano or thyme in the pan for a sauce, and garlic "
     "cooked gently rather than browned. Salt them ten minutes before they go in and the juices "
     "come out and turn into the sauce."),
    (("vegetables", "veg", "squash", "pumpkin", "butternut", "courgette", "courgettes",
      "carrots", "broccoli", "cauliflower", "aubergine"),
     "Roast veg wants salt, oil and heat, then something sharp at the end: lemon zest, a splash of "
     "vinegar or a crumble of feta. Cumin and paprika for squash and carrots, oregano and chilli "
     "for courgette and aubergine, and salt halfway through rather than only at the start."),
    (("burger", "burgers", "sausage meat", "meatballs", "mince"),
     "Season the meat before it is shaped, not after: salt, black pepper and a little onion or "
     "mustard in the mix, then fry a spoonful to taste before you commit the lot. A burger needs "
     "nothing on the outside but salt, pepper and a hot pan."),
    # Last, so any named food wins over it: "seasoning for a roast" names no meat, and the honest
    # answer is the one that says what each roast wants.
    (("roast", "roast dinner", "roasting joint", "joint of meat"),
     "Salt the joint the night before if you can, then rub it with oil and pepper before it goes "
     "in: lemon, garlic and thyme for chicken, mustard and horseradish for beef, rosemary and "
     "garlic for lamb, fennel and sage for pork. Salt early is the one that makes the difference, "
     "because it gets into the meat instead of sitting on the skin."),
)

DIET_VARIANTS = {
    # "nuts, fruit, yoghurt, oatcakes, cheese": an office snack list is a protein list, and the
    # protein does not have to be a nut. Sent to a family who said nuts are off the table.
    "Bring something with protein and fibre in it - nuts, fruit, yoghurt, oatcakes, cheese - and "
    "keep it in your drawer or the office fridge, so the 3pm vending machine is not the decision. "
    "It is cheaper too: a \u00a31.20 snack a day is about \u00a3250 a year. Water in a bottle on the desk "
    "covers most of what people mistake for hunger.":
        "Bring something with protein and fibre in it - fruit, yoghurt, oatcakes, cheese, hummus - "
        "and keep it in your drawer or the office fridge, so the 3pm vending machine is not the "
        "decision. It is cheaper too: a \u00a31.20 snack a day is about \u00a3250 a year. Water in a "
        "bottle on the desk covers most of what people mistake for hunger.",
    # "cooked ones crumble into a sprout and bacon dish, or simmer 15 minutes in milk"
    "Chestnuts: cooked ones crumble into a sprout and bacon dish, or simmer 15 minutes in milk "
    "and blitz into soup, which is sweet enough without cream.":
        "Chestnuts: simmer them 15 minutes and peel them while they are still hot, then crumble "
        "them into a stuffing or stir them through a soup - they mash like potato, and a chestnut "
        "soup is sweet enough on its own without any sugar. Roast them at 200C (180C fan) for 20 "
        "minutes if you want them to peel easily.",
    # "mashed with butter, salt and plenty of black pepper, alongside sausages"
    "Mash it: cubed swede boiled 20 minutes, drained well and mashed with butter, salt and "
    "plenty of black pepper, alongside sausages.":
        "Mash it: cubed swede boiled 20 minutes, drained well and mashed with butter, salt and "
        "plenty of black pepper. It roasts well too - cubes tossed in oil, 40 minutes at 200C "
        "(180C fan) until the edges caramelise - and it is a good soup with carrot and a little "
        "nutmeg.",
    # "with chopped bacon or smoked sausage, then stirred through pasta or mash"
    "Shredded cabbage fried hot for 7 minutes with chopped bacon or smoked sausage, then stirred "
    "through pasta or mash, is a dinner rather than a side.":
        "Shredded cabbage fried hot for 7 minutes with garlic and a pinch of chilli, then stirred "
        "through mash or rice with a squeeze of lemon, is a dinner rather than a side. Add a "
        "spoon of mustard to the pan and it tastes of more than it is.",
    # "A roast is one joint, potatoes, two veg and gravy": the card is the vegetables and the
    # joint is context, so the meat-free version keeps the sides and names what goes in its place.
    "A roast is one joint, potatoes, two veg and gravy, and the veg is where you ring the "
    "changes: carrots and parsnips roasted round the meat for the last 45 minutes, greens or "
    "cabbage steamed, and peas with mint if it is lamb. Add Yorkshire puddings for beef, "
    "stuffing and apple sauce for pork, bread sauce for chicken or turkey. Work back from the "
    "meat, because the joint rests 20 minutes and that is when the potatoes go up to full heat.":
        "A roast is potatoes, two veg and gravy, and the veg is where you ring the changes: "
        "carrots and parsnips roasted in oil for the last 45 minutes, greens or cabbage steamed, "
        "and peas with mint. The middle of the plate is a nut roast, a whole roasted cauliflower "
        "or a mushroom and lentil loaf, and the gravy is made with vegetable stock and a spoon of "
        "soy. Put the potatoes in at full heat 40 minutes before you want to eat and the timing "
        "looks after itself.",
    # "Meat, fish, eggs, milk, beans, lentils, nuts and tofu are good sources": the list is the
    # answer, so it is replaced rather than dropped.
    "Protein is a building material made of chains of amino acids: the body uses it to build and "
    "repair muscle, skin, hair and organs, and enzymes are proteins too. Meat, fish, eggs, milk, "
    "beans, lentils, nuts and tofu are good sources.":
        "Protein is a building material made of chains of amino acids: the body uses it to build "
        "and repair muscle, skin, hair and organs, and enzymes are proteins too. Beans, lentils, "
        "chickpeas, tofu, nuts, seeds and whole grains are good sources, and you do not have to "
        "combine them at one meal: a day of them does the job. Eggs and dairy count too if you "
        "eat them.",
    # "tossed with pasta and parmesan"
    "Courgette pasta: sliced and fried with garlic in plenty of olive oil for 8 minutes, tossed "
    "with pasta and parmesan.":
        "Courgette: sliced and fried with garlic in plenty of olive oil for 8 minutes, until the "
        "edges brown, then dressed with lemon and plenty of black pepper - good on its own, "
        "through rice, or under a roast.",
}

FREEZE_FACTS = (
    (("milk",), "Yes: freeze it fresh, leave an inch of room for it to expand, and shake it after "
                "thawing - it is fine for cooking and cereal even if it looks a little separated."),
    # There is no cream answer to give here: ice cream is made to be frozen, and "cream" in the
    # line was reaching the row that says cream must never be frozen at all.
    (("ice cream", "icecream", "ice-cream", "gelato"),
     "Ice cream is already frozen, so it keeps months in its tub: press cling film onto the surface "
     "once it is open so it does not go icy. Home-made ice cream without a churn freezes hard, so "
     "stir it every half hour for the first two hours and it stays scoopable."),
    (("cream",), "Cream is the one thing not to freeze: it splits and thaws out grainy. Freeze the "
                 "cake or sponge plain and put fresh cream on when you serve it."),
    (("cheese",), "Grate hard cheese and freeze it in bags, then use it straight from frozen in "
                  "cooking. Soft cheese and cream cheese go grainy, so keep those in the fridge."),
    (("butter",), "Yes: wrap it well, cut into portions first if you can, and it keeps about 3 "
                  "months."),
    (("banana", "bananas"), "Peel and slice them first, then bag them. They thaw soft, so they are "
                            "for smoothies and banana bread rather than eating."),
    (("egg", "eggs"), "Not in the shell: beat the yolks and whites separately (or beat them whole), "
                      "write how many on the bag, and use within 3 months."),
    (("avocado", "avocados"), "Only as mash, or halves with lemon on them. It thaws soft, so it is "
                              "for guacamole rather than salad."),
    (("herb", "herbs", "basil", "parsley", "coriander", "cilantro", "mint"), "Chop them and freeze "
     "in an ice-cube tray topped up with oil or water, or freeze whole sprigs in a bag for "
     "cooking."),
    (("berry", "berries", "strawberry", "strawberries", "raspberry", "raspberries", "blueberry",
      "blueberries"), "Spread them out on a tray first so they freeze loose, then bag them. They "
                      "thaw soft, which is fine for crumble or yoghurt."),
    (("bread", "loaf"), "Slice it first, then it goes straight in the toaster, and it keeps about 3 "
                        "months."),
    (("stock", "gravy"), "Cool it fast, freeze it flat in bags or in ice-cube trays, and it keeps "
                         "about 3 months."),
    (("cake batter", "batter", "sponge mix"),
     "Yes: freeze the batter in the tin, wrapped, and bake it from frozen with 15 to 20 minutes "
     "extra at the usual temperature, or freeze it in portions and thaw overnight in the fridge."),
    (("cake",), "Wrap it well, in slices if that is how you will eat it, and it keeps about 3 "
                "months."),
    (("wine",), "Freeze what is left in ice-cube trays and drop a cube into a stew or a sauce."),
    # The everyday foods that had no row at all: the line fell through to a shrug, or - for
    # pasta - to the boiling time, which is the answer to a different question.
    (("mushroom", "mushrooms", "chestnut mushrooms"),
     "Cook them first: raw mushrooms go slimy when frozen. Fry them until the water has gone, cool "
     "them fast, then freeze in bags for about 3 months and use them from frozen in sauces."),
    (("pizza", "pizzas", "pizza dough", "dough"),
     "Yes: a cooked pizza freezes for about 2 months, wrapped, and goes into a hot oven straight "
     "from frozen. Raw dough freezes after the first rise, in an oiled bag, and thaws overnight in "
     "the fridge."),
    # The named fish and shellfish belong with "fish", which was the only one of them here: "can
    # i freeze cod" and "can i freeze prawns" were a shrug while "can i freeze salmon" had an
    # answer, and the rule is the same for all of them.
    (("mince", "beef", "lamb", "pork", "fish", "salmon", "bacon", "meat",
      "cod", "haddock", "trout", "mackerel", "tuna", "prawn", "prawns", "shellfish",
      "sardines", "sea bass", "monkfish", "hake", "kippers"),
     "Yes, cooked or raw: freeze it the day you buy it, or within a day of cooking it, in portions, "
     "and use it within 3 months. Thaw it in the fridge overnight rather than on the counter, cook "
     "it right through, and do not refreeze meat that has already been thawed."),
    # A bag of leaves is not a blanching vegetable: it is nearly all water, so freezing bursts it
    # and it thaws limp and brown. The honest answer is "not for salad" (spinach stays in the
    # vegetable row below, because spinach is the one leaf that freezes well).
    # Fruit that has a "good for you" row of its own lost the freeze question to it: "can i freeze
    # grapes" was told that grape skins are where the colour and the fibre are, and "can i freeze
    # apple" that apple skin is the best part. The freeze row's food words are read off this table,
    # so a fact here is also the word that brings the line to this answer.
    # The rest of the everyday freezer questions, in one place: each was a shrug ("can i freeze
    # tofu", "can i freeze jam", "can i freeze rhubarb") or the wrong card ("can i freeze sweet
    # potato" got the raw-potato warning, "can i freeze pineapple" got the pizza joke, "can i
    # freeze cream cheese" was told to grate hard cheese).
    (("rhubarb",), "Yes: cut it into lengths, bag it and freeze it raw for about 3 months - it goes "
                   "soft as it thaws, which is exactly what a crumble wants. Stewed rhubarb freezes "
                   "well too, and slightly under-sweetened, since it takes sugar when you use it."),
    (("beetroot", "beet"),
     "Cook it first: roast or boil whole beetroot, rub the skins off, then slice and bag it, and it "
     "keeps about 3 months. Raw beetroot freezes hard and woody, so cook first; pickled beetroot "
     "freezes badly, because the vinegar soaks in and the slices go limp."),
    (("sweet potato", "sweet potatoes", "yam", "yams"),
     "Cook it first: roast, mash or par-boil chunks, cool and bag, and it keeps about 3 months. Raw "
     "sweet potato goes watery and black, so it is the one root that wants cooking before the "
     "freezer - and mash freezes better than chunks."),
    (("tofu", "bean curd"),
     "Yes: press the water out, cut it into cubes and freeze it in a bag. The texture turns spongy "
     "and it takes up sauce better afterwards, so it is a good thing to do with a block you will "
     "not use; it keeps about 3 months and can be cooked from frozen."),
    (("jam", "marmalade", "preserve", "preserves"),
     "Yes, jam freezes: it keeps its colour and set better than in a cupboard, and a jar keeps about "
     "a year in the freezer. Leave an inch of room in the jar for it to expand, and thaw it in the "
     "fridge overnight; it will not go off in the freezer, so the date on it is about quality."),
    (("mayonnaise", "mayo", "salad cream"),
     "Not well: mayonnaise splits when it freezes and thaws oily and grainy, so a jar in the fridge "
     "door is the right place for it. A sandwich made with it does not freeze well either - keep "
     "mayo for the day of eating - though a cooked dish with mayo in it freezes fine."),
    (("nuts", "almonds", "walnuts", "cashews", "peanuts", "pistachios", "pecans", "hazelnuts"),
     "Yes, and it is the best place for them: nuts go rancid in a warm cupboard in a few months, and "
     "frozen they keep about a year. Bag them, press the air out, and use them from frozen - they "
     "thaw in minutes and toast straight from the freezer."),
    (("sandwich", "sandwiches", "wrap", "wraps"),
     "Only a plain one: meat, cheese or peanut butter sandwiches freeze fine for about a month if you "
     "leave out the salad, cucumber and tomato, which thaw to water. Spread the filling to the edges "
     "so the bread does not dry, wrap each one, and let it thaw in the fridge overnight or pack it "
     "frozen for lunch."),
    (("prawn", "prawns", "shrimp", "shrimps"),
     "Yes, raw or cooked: freeze them the day you buy them, in a bag with the air pressed out, and "
     "use within 3 months. Thaw them in the fridge overnight rather than in warm water, and do not "
     "refreeze them once thawed - cooked prawns go rubbery if you freeze them twice."),
    (("dumpling", "dumplings", "gyoza", "potsticker", "potstickers"),
     "Yes: freeze them raw on a tray so they stay separate, then bag them, and cook from frozen - "
     "they need about 3 minutes longer in the pan or steamer, and no thawing. They keep about 3 "
     "months, and a frozen dumpling goes straight into soup."),
    (("melon", "watermelon", "cantaloupe", "honeydew"),
     "Yes: cut it into chunks, spread them on a tray to freeze loose, then bag them - and eat them "
     "frozen or in a smoothie, because melon thaws limp and watery. It keeps about 3 months, and a "
     "melon that is already cut goes in the fridge first and the freezer within 3 days."),
    (("mango", "mangoes", "papaya", "pineapple"),
     "Yes: cut it into chunks, freeze them on a tray so they stay loose, then bag them. They thaw "
     "soft, so they are for smoothies, yoghurt or a lassi rather than a fruit salad, and they keep "
     "about 3 months. Pineapple is the one that holds its shape best, and frozen mango is what most "
     "smoothie bars use."),
    (("date", "dates", "raisins", "sultanas", "dried fruit"),
     "Yes: dried fruit freezes well and comes back as it was - bag it and it keeps about a year, "
     "which is longer than the cupboard. It does not go hard, so you can chop dates straight from "
     "the freezer for a cake, and a bag that has gone dry revives in the freezer."),
    (("peach", "peaches", "plum", "plums", "apricot", "apricots", "nectarine", "nectarines"),
     "Best halved and stoned first, then frozen on a tray and bagged: they keep about 3 months and "
     "are for crumble, jam or a smoothie. The skins slip off as they thaw, so there is no need to "
     "peel them first, and a peach freezes better than it keeps in the fruit bowl."),
    (("cream cheese", "soft cheese", "mascarpone", "ricotta", "brie", "camembert", "feta"),
     "Soft cheese freezes but thaws grainy and a bit watery, so it is for cooking - a baked"
     " cheesecake, a sauce, a pasta bake - rather than for a cracker. Wrap it well, freeze up to 2 "
     "months, and thaw it in the fridge; a whole brie or camembert is better baked from frozen."),
    (("oat milk", "soya milk", "soy milk", "almond milk", "coconut milk", "plant milk"),
     "Yes: plant milk freezes, though it can separate, so shake it hard once it has thawed. Leave an "
     "inch of room in the bottle or carton for it to expand, and a tin of coconut milk freezes well "
     "in an ice-cube tray - a cube is about a tablespoon for a curry."),
    (("breast milk", "expressed milk", "pumped milk"),
     "Expressed breast milk keeps 5 days in the fridge at the back and 6 months in the freezer, in "
     "the amounts you will use, dated. Thaw it in the fridge overnight and use it within 24 hours, "
     "warm it in a jug of warm water rather than the microwave, and never refreeze it or add fresh "
     "milk to a thawed bottle."),
    (("formula milk", "formula", "baby formula"),
     "Not the made-up bottle: mix each feed fresh with boiled water left to cool to about 70C, and "
     "throw away whatever is left in the bottle. Ready-made formula keeps 24 hours in the fridge "
     "once it is opened, and the freezer is not the place for it - frozen and thawed formula "
     "separates and is not worth the risk for a baby."),
    (("sour cream", "creme fraiche", "creme fresh"),
     "It splits when it freezes and thaws grainy and watery, so it is no good as a spoonful on a "
     "baked potato afterwards. It is fine in a dish that is going to be cooked - a stroganoff or a "
     "cake - so freeze it stirred into that rather than on its own."),
    (("baby food", "puree", "purees", "pureed food", "weaning food"),
     "Yes: spoon it into an ice-cube tray, freeze it, then pop the cubes into a bag - each cube is "
     "about an ounce, so a couple makes a portion. It keeps about a month, thaws in the fridge or "
     "in a bowl of warm water, must be heated right through and cooled before it is offered, and "
     "never goes back in the freezer once warmed."),
    (("grape", "grapes"),
     "Yes: wash and dry them, spread them on a tray to freeze loose, then bag them. They go hard "
     "and sorbet-like, so they are for eating frozen or for smoothies rather than a fruit salad, "
     "and they keep about 3 months."),
    (("apple", "apples", "pear", "pears"),
     "Best cooked first: stewed or sliced apple freezes about 3 months in bags, and it goes into a "
     "crumble from frozen. Raw slices go brown and soft, so toss them in lemon juice and use them "
     "for baking rather than a salad."),
    # citrus is juiced and zested before the freezer, not put in whole: "can i freeze lemons",
    # "can i freeze limes" and "can i freeze orange juice" were all a shrug.
    (("lemon", "lemons", "lime", "limes", "orange", "oranges", "grapefruit"),
     "Juice them first and freeze the juice in an ice-cube tray - a cube is about a tablespoon - "
     "and zest them into a small bag; both go straight into cooking from frozen and keep about 3 "
     "months. A whole citrus fruit freezes but thaws soft and dull, so use those for juice rather "
     "than slices."),
    (("orange juice", "juice", "apple juice"),
     "Yes: pour it into a bottle with an inch of room for it to expand, or freeze it in ice-cube "
     "trays for drinks, and it keeps about 4 to 6 months. It separates as it thaws, so shake it, "
     "and the vitamin C tails off the longer it sits, which is why a month-old cube is for "
     "flavour rather than for goodness."),
    # the salad vegetables that are nearly all water: they thaw limp, so the answer is "not for
    # salad" rather than the general yes
    (("cucumber", "cucumbers"),
     "Not for salad: a cucumber is nearly all water, so the ice bursts it and it thaws limp and "
     "watery. It is fine cooked into a soup or a curry, or frozen as tzatziki, where the water "
     "does not matter."),
    (("coleslaw", "slaw", "sauerkraut"),
     "Freeze the shredded cabbage on its own and it keeps for cooking; dressed coleslaw does not "
     "freeze, because the mayonnaise splits and the cabbage goes limp and watery. So bag the dry "
     "cabbage and dress a fresh bowl when you want one."),
    (("guacamole", "guac", "hummus dip"),
     "It freezes, but it thaws a little watery and dull: press cling film onto the surface so it "
     "does not go brown, freeze it for up to a month, then stir it well and use it in a wrap or on "
     "toast rather than as a dip for guests. Lemon juice on top helps it stay green."),
    (("lettuce", "salad", "salad leaves", "rocket", "arugula", "watercress"),
     "Not if you want it raw: a leaf is nearly all water, so the ice bursts its cells and it thaws "
     "limp and brown. It is fine cooked, so braise it or stir it into soup instead, and a bag that "
     "has already gone limp is better cooked than frozen."),
    # Spring onions freeze better than they keep, and "can i freeze spring onions" was getting the
    # general freezer answer while "can i freeze spinach" got its own row.
    (("spring onion", "spring onions", "scallion", "scallions"),
     "Yes: chop them, bag them and freeze them, and they go straight into cooking from frozen for "
     "about 3 months. They lose their crunch, so they are no good raw afterwards, and the white "
     "parts freeze better than the green."),
    (("vegetable", "vegetables", "veg", "peas", "spinach", "broccoli", "carrots", "carrot",
      "green beans", "sweetcorn", "sweet corn", "corn", "cauliflower", "cabbage", "sprouts",
      "sprout", "kale", "parsnip", "parsnips", "pepper", "peppers", "leek", "leeks",
      "courgette", "courgettes", "zucchini", "turnip", "turnips", "swede", "runner beans",
      "mangetout", "sugar snap", "beans", "butternut", "pumpkin"),
     "Yes: blanch them in boiling water for 2 minutes, cool them in cold water, dry them and bag "
     "them. They keep about 3 months and go into the pan from frozen; cooked leftover veg is fine "
     "too, though it comes out softer."),
    # raw potato is the one vegetable that must not go in as it is
    (("raw potato", "raw potatoes", "potato", "potatoes", "new potatoes", "spuds"),
     "Not raw: raw potato goes black and mushy in the freezer. Cook it first - roast potatoes, "
     "chips, mash or par-boiled - and it keeps about 3 months, with mash the one that thaws best. "
     "Par-boiled and roughed up in the pan first gives you roast potatoes straight from frozen."),
    # alliums and soft veg are chopped raw, no blanching at all
    (("onion", "onions", "shallot", "shallots", "spring onions", "celery",
      "ginger", "garlic", "chilli", "chillies", "chili", "chilies"),
     "Chop them raw and bag them: onions, shallots, celery, ginger, garlic and chillies all freeze "
     "without blanching and keep about 3 months. Freeze them spread out on a tray first if you want "
     "them loose, and cook them from frozen - they soften rather than brown."),
    (("tomato", "tomatoes", "cherry tomatoes", "passata"),
     "Yes, and no blanching needed: freeze them whole on a tray, or halve them and bag them. The "
     "skins split and slip off as they thaw, so they are for sauces, soups and stews rather than "
     "salads, and they keep about 3 months."),
    (("pasta", "spaghetti", "penne", "fusilli", "macaroni", "noodles", "tagliatelle"),
     "Yes: cook it a minute short of the packet, toss it with a little oil or sauce so it does not "
     "clump, and freeze it in portion bags. It comes back in minutes in boiling water or straight "
     "in a sauce."),
    # The bakes a person freezes mid-week, and the things whose answer is not the general "yes,
    # about 3 months": pastry wants to go in raw, a crumble wants to go in unbaked, and yoghurt
    # and chocolate come out changed. Every one of these was a shrug, because the freeze row's
    # key listed its food words by hand and these were not among them.
    (("scone", "scones", "fruit scone", "cheese scone"),
     "Bake them first: cool them completely on a rack, bag them and they keep about 2 months. Warm "
     "them from frozen for 8 to 10 minutes at 160C (140C fan) and they come back close to fresh - "
     "raw dough freezes too, cut into rounds, and bakes from frozen with 3 minutes extra."),
    (("pancake", "pancakes", "crepe", "crepes"),
     "Yes: cool them, stack them with baking paper between so they do not stick, bag the stack and "
     "freeze it for about 2 months. They go straight into a hot pan, or the toaster, from frozen."),
    (("waffle", "waffles"),
     "Yes: cool them on a rack so they do not steam soft, bag them, and they keep about 2 months. "
     "Give them 3 or 4 minutes in a hot oven or the toaster from frozen and they crisp up again."),
    (("crumpet", "crumpets"),
     "Yes, in the pack they came in or bagged, for about 2 months, and they toast from frozen with "
     "an extra minute or two."),
    (("pastry", "shortcrust", "shortcrust pastry", "pie crust", "pastry dough"),
     "Raw is the way: flatten the pastry into a disc, wrap it and it keeps about 3 months, then "
     "thaw it overnight in the fridge and roll it cold. A baked pastry case freezes too but it "
     "softens, so give it 5 minutes in a hot oven to crisp before you fill it."),
    (("crumble", "fruit crumble", "crumble topping"),
     "Freeze it before it is baked, not after: a baked crumble goes soggy as it thaws. Assemble it "
     "in the dish, wrap the whole thing, and bake it from frozen at the usual heat plus 15 minutes."),
    (("yoghurt", "yogurt", "greek yoghurt", "greek yogurt"),
     "It freezes but it separates, so it thaws grainy and watery and is no good on its own. It is "
     "fine in a smoothie or stirred into a curry or naan dough, and frozen in ice-cube trays it "
     "makes a quick lassi."),
    (("chocolate", "milk chocolate", "dark chocolate"),
     "It freezes, but the surface goes white and powdery as it thaws. Wrap it tightly, thaw it in "
     "the fridge, and use it for melting or baking rather than for eating."),
)

FOOD_CALORIES = {
    # Mac and cheese is a food, not a Mac: the storage row was answering the calorie question
    # because "mac" was the machine in the line. "Mac" is not a meal on its own, so the dish
    # words are what the line carries.
    "mac and cheese": ("mac and cheese", "a normal portion", 600),
    "macaroni and cheese": ("macaroni and cheese", "a normal portion", 600),
    "macaroni cheese": ("macaroni cheese", "a normal portion", 600),
    "mac n cheese": ("mac and cheese", "a normal portion", 600),
    "macaroni": ("macaroni", "a cooked bowl", 220),
    "banana": ("a banana", "a medium one", 105),
    "apple": ("an apple", "a medium one", 95),
    "orange": ("an orange", "a medium one", 62),
    "pear": ("a pear", "a medium one", 100),
    "strawberries": ("strawberries", "a handful", 30),
    "grapes": ("grapes", "a handful", 60),
    "avocado": ("an avocado", "a whole one", 240),
    "carrot": ("a carrot", "one", 25),
    "tomato": ("a tomato", "one", 22),
    "broccoli": ("a portion of broccoli", "a normal portion", 40),
    "egg": ("an egg", "one", 78),
    "slice of bread": ("a slice of bread", "a normal slice", 80),
    # "how many calories in a slice of white bread" was answered with the bread recipe, because
    # the table held the bare "slice of bread" and the line puts a word in the middle of it. The
    # kinds of bread are the same slice, so each one is a row on its own.
    "white bread": ("a slice of white bread", "a medium slice", 80),
    "brown bread": ("a slice of brown bread", "a medium slice", 75),
    "wholemeal bread": ("a slice of wholemeal bread", "a medium slice", 75),
    "sourdough": ("a slice of sourdough", "a medium slice", 90),
    "sourdough bread": ("a slice of sourdough bread", "a medium slice", 90),
    "toast": ("a slice of toast", "a medium slice", 80),
    "bread roll": ("a bread roll", "one", 150),
    "slice of cheese": ("a slice of cheese", "a normal slice", 110),
    "glass of milk": ("a glass of milk", "a 200ml glass", 130),
    "milk": ("a glass of milk", "a 200ml glass", 130),
    "yoghurt": ("a pot of yoghurt", "a small pot", 120),
    "porridge oats": ("a 40g portion of oats", "a 40g dry portion",
                      {"protein": 4, "carbs": 24, "sugar": 0, "fat": 3, "fibre": 4}),
    "porridge": ("a bowl of porridge", "made with water", 150),
    "cereal": ("a bowl of cereal", "with milk", 170),
    "baked potato": ("a baked potato", "a medium one", 200),
    "chips": ("a portion of chips", "a normal portion", 350),
    "pasta": ("a bowl of pasta", "a cooked bowl", 300),
    "rice": ("a bowl of rice", "a cooked bowl", 220),
    "slice of pizza": ("a slice of pizza", "a normal slice", 250),
    "croissant": ("a croissant", "one", 280),
    "doughnut": ("a doughnut", "one", 250),
    "chocolate bar": ("a chocolate bar", "a standard one", 240),
    "biscuit": ("a biscuit", "one", 50),
    "crisps": ("a packet of crisps", "a normal packet", 150),
    "pint of beer": ("a pint of beer", "a pint", 200),
    # The can and the bottle are how most beer is drunk at home, and the unit answer was taking
    # "how many calories in a can of beer" before this row existed.
    "can of beer": ("a can of beer", "a 330ml can", 140),
    "bottle of beer": ("a bottle of beer", "a 330ml bottle", 140),
    # The same drink has several names and sizes, and people ask for the calories in the one
    # they are holding. Without these rows the weekly alcohol limit answered instead.
    "can of lager": ("a can of lager", "a 330ml can", 140),
    "pint of lager": ("a pint of lager", "a pint", 210),
    "can of cider": ("a can of cider", "a 330ml can", 210),
    "bottle of wine": ("a bottle of wine", "a 750ml bottle", 620),
    "glass of wine": ("a glass of wine", "a 175ml glass", 130),
    "gin and tonic": ("a gin and tonic", "a single", 130),
    "coke": ("a can of coke", "a 330ml can", 140),
    "cola": ("a can of cola", "a 330ml can", 140),
    "orange juice": ("a glass of orange juice", "a 200ml glass", 110),
    "latte": ("a latte", "a medium one with whole milk", 190),
    "teaspoon of sugar": ("a teaspoon of sugar", "a level teaspoon", 16),
    "tablespoon of oil": ("a tablespoon of oil", "a tablespoon", 120),
    "peanut butter": ("a tablespoon of peanut butter", "a tablespoon", 95),
    "ice cream": ("a scoop of ice cream", "a scoop", 140),
    "peanuts": ("a handful of peanuts", "a handful", 180),
    # The everyday biscuits and snacks people weigh up out loud. A bare "a biscuit" row cannot
    # answer "how many calories in a digestive": the number is the whole question, and the
    # answers are 40 to 95 calories in a portion that looks the same on the plate.
    "digestive": ("a digestive biscuit", "one", 80),
    "digestive biscuit": ("a digestive biscuit", "one", 80),
    "digestives": ("a digestive biscuit", "one", 80),
    "rich tea": ("a rich tea biscuit", "one", 40),
    "rich tea biscuit": ("a rich tea biscuit", "one", 40),
    "hobnob": ("a hobnob", "one", 95),
    "hobnobs": ("a hobnob", "one", 95),
    "custard cream": ("a custard cream", "one", 60),
    "custard creams": ("a custard cream", "one", 60),
    "ketchup": ("a tablespoon of ketchup", "a tablespoon", 15),
    "cornflakes": ("a 40g bowl of cornflakes", "a 40g bowl", 150),
    "corn flakes": ("a 40g bowl of cornflakes", "a 40g bowl", 150),
    "granola": ("a 50g portion of granola", "a 50g portion", 240),
    "cereal bar": ("a cereal bar", "one", 130),
    "granola bar": ("a cereal bar", "one", 130),
    "milkshake": ("a medium milkshake", "a 400ml one", 400),
    "milkshakes": ("a medium milkshake", "a 400ml one", 400),
    # the same portions as FOOD_NUTRIENTS below, because "how many calories in a sausage" is
    # how people ask far more often than "how much protein": one table for the food, one row
    # per column set so the two never disagree.
    "sausage": ("a sausage", "one thick one", 95),
    "ham": ("a slice of ham", "one slice", 28),
    "turkey": ("a 120g portion of turkey", "one breast", 150),
    "steak": ("a 150g steak", "lean and grilled", 260),
    "pork chop": ("a pork chop", "one 150g chop", 290),
    "beef mince": ("a 100g portion of beef mince", "100g cooked", 240),
    "mince": ("a 100g portion of beef mince", "100g cooked", 240),
    "halloumi": ("a 100g portion of halloumi", "about four slices", 330),
    "kidney beans": ("a 100g portion of kidney beans", "100g cooked", 120),
    "black beans": ("a 100g portion of black beans", "100g cooked", 130),
    "cashews": ("a handful of cashews", "a 30g handful", 165),
    "spinach": ("a 100g portion of spinach", "100g cooked", 25),
    # The food people ask the calorie question about is very often a composite - a sausage roll,
    # a meat pie, a sandwich - rather than a single ingredient, and a composite is not in any
    # table until it is written down. Each row here is the same portion as its row in
    # FOOD_NUTRIENTS below, so "how many calories in a pasty" and "how much protein in a pasty"
    # are the same portion, and the two figures agree to the rounding.
    "sausage roll": ("a sausage roll", "one", 330),
    "sausage rolls": ("a sausage roll", "one", 330),
    "pasty": ("a pasty", "one", 400),
    "pastie": ("a pasty", "one", 400),
    "meat pie": ("a meat pie", "one", 470),
    "pork pie": ("a pork pie", "one", 420),
    "shepherds pie": ("a portion of shepherd's pie", "a 400g portion", 410),
    "shepherd's pie": ("a portion of shepherd's pie", "a 400g portion", 410),
    "spring roll": ("a spring roll", "one", 120),
    "spring rolls": ("a spring roll", "one", 120),
    "yorkshire pudding": ("a yorkshire pudding", "one", 100),
    "yorkshire puddings": ("a yorkshire pudding", "one", 100),
    "scotch egg": ("a scotch egg", "one", 240),
    "scotch eggs": ("a scotch egg", "one", 240),
    "sandwich": ("a sandwich", "one", 330),
    "sandwiches": ("a sandwich", "one", 330),
    "chip butty": ("a chip butty", "one", 460),
    "lasagne": ("a portion of lasagne", "a 400g portion", 550),
    "lasagna": ("a portion of lasagne", "a 400g portion", 550),
    # A dish has a portion like any other food, so the same table answers the calorie and
    # nutrient question about it. A curry, a chilli, a bolognese and a stir fry are what people
    # ask about by name and none of them is a single ingredient: "how much protein in a chicken
    # curry" and "how many calories in a chilli" both reached no entry at all while the figures
    # below were what they wanted.
    # A dish the meal table above already counts (a chicken curry, a bolognese, a cottage pie)
    # is not repeated here: one fact, one table.
    "chicken tikka masala": ("a portion of chicken tikka masala", "a 400g portion", 560),
    "chilli con carne": ("a portion of chilli con carne", "a 350g portion", 430),
    "fish pie": ("a portion of fish pie", "a 400g portion", 400),
    "chicken salad": ("a bowl of chicken salad", "a 300g bowl", 250),
    "chicken soup": ("a bowl of chicken soup", "a 350g bowl", 150),
    "lentil soup": ("a bowl of lentil soup", "a 350g bowl", 190),
    "dal": ("a portion of dal", "a 300g portion", 250),
    "chicken stir fry": ("a portion of chicken stir fry", "a 400g portion", 400),
    "stir fry": ("a portion of stir fry", "a 400g portion", 350),
    "chicken sandwich": ("a chicken sandwich", "one", 280),
    "tuna sandwich": ("a tuna sandwich", "one", 300),
    "slice of cake": ("a slice of cake", "one slice", 200),
    "victoria sponge": ("a slice of victoria sponge", "one slice", 220),
    "bakewell tart": ("a bakewell tart", "one", 250),
    "scone": ("a scone", "one", 220),
    "scones": ("a scone", "one", 220),
    "crumpet": ("a crumpet", "one", 110),
    "crumpets": ("a crumpet", "one", 110),
    "bagel": ("a bagel", "one", 260),
    "bagels": ("a bagel", "one", 260),
}

FOOD_NUTRIENTS = {
    "egg": ("an egg", "one", {"protein": 6, "carbs": 1, "sugar": 1, "fat": 5, "fibre": 0,
                              "calcium": 28, "salt": 0.2}),
    "egg white": ("an egg white", "one", {"protein": 4, "carbs": 0, "sugar": 0, "fat": 0,
                                          "fibre": 0}),
    "milk": ("a glass of milk", "a 200ml glass",
             {"protein": 7, "carbs": 10, "sugar": 10, "fat": 7, "fibre": 0,
              "calcium": 240, "salt": 0.2}),
    "glass of milk": ("a glass of milk", "a 200ml glass",
                      {"protein": 7, "carbs": 10, "sugar": 10, "fat": 7, "fibre": 0,
                       "calcium": 240, "salt": 0.2}),
    "cup of milk": ("a cup of milk", "a 250ml cup",
                    {"protein": 9, "carbs": 12, "sugar": 12, "fat": 8, "fibre": 0,
                     "calcium": 300, "salt": 0.25}),
    "greek yoghurt": ("a pot of Greek yoghurt", "a 150g pot",
                      {"protein": 15, "carbs": 6, "sugar": 6, "fat": 5, "fibre": 0,
                       "calcium": 170}),
    "greek yogurt": ("a pot of Greek yoghurt", "a 150g pot",
                     {"protein": 15, "carbs": 6, "sugar": 6, "fat": 5, "fibre": 0,
                      "calcium": 170}),
    "pot of yoghurt": ("a pot of yoghurt", "a 150g pot",
                       {"protein": 6, "carbs": 9, "sugar": 9, "fat": 4, "fibre": 0,
                        "calcium": 200}),
    "yoghurt": ("a pot of yoghurt", "a 150g pot",
                {"protein": 6, "carbs": 9, "sugar": 9, "fat": 4, "fibre": 0,
                 "calcium": 200}),
    "yogurt": ("a pot of yoghurt", "a 150g pot",
               {"protein": 6, "carbs": 9, "sugar": 9, "fat": 4, "fibre": 0,
                "calcium": 200}),
    "cottage cheese": ("a 100g portion of cottage cheese", "a 100g portion",
                       {"protein": 11, "carbs": 3, "sugar": 3, "fat": 4, "fibre": 0,
                        "calcium": 80, "salt": 0.8}),
    "slice of cheese": ("a slice of cheese", "a normal slice",
                        {"protein": 8, "carbs": 0, "sugar": 0, "fat": 10, "fibre": 0}),
    "cheddar": ("a 30g piece of cheddar", "a 30g piece",
                {"protein": 8, "carbs": 0, "sugar": 0, "fat": 10, "fibre": 0,
                 "calcium": 220, "salt": 0.5}),
    "chicken thigh": ("a chicken thigh", "one, cooked",
                      {"protein": 25, "carbs": 0, "sugar": 0, "fat": 10, "fibre": 0}),
    "salmon": ("a salmon fillet", "a 140g fillet",
               {"protein": 28, "carbs": 0, "sugar": 0, "fat": 17, "fibre": 0}),
    "tin of tuna": ("a drained tin of tuna", "a 110g tin",
                    {"protein": 26, "carbs": 0, "sugar": 0, "fat": 1, "fibre": 0}),
    "tuna": ("a drained tin of tuna", "a 110g tin",
             {"protein": 26, "carbs": 0, "sugar": 0, "fat": 1, "fibre": 0, "salt": 1}),
    "prawns": ("a portion of prawns", "a 100g portion",
               {"protein": 20, "carbs": 0, "sugar": 0, "fat": 1, "fibre": 0, "salt": 1}),
    "bacon": ("two rashers of bacon", "two rashers",
              {"protein": 7, "carbs": 0, "sugar": 0, "fat": 8, "fibre": 0, "salt": 1.8}),
    "sausages": ("two sausages", "two",
                 {"protein": 12, "carbs": 8, "sugar": 1, "fat": 16, "fibre": 1,
                  "salt": 1.6}),
    "sausage": ("a sausage", "one thick one",
                {"protein": 6, "carbs": 4, "sugar": 1, "fat": 8, "fibre": 0}),
    "turkey": ("a 120g portion of turkey", "a 120g portion",
               {"protein": 30, "carbs": 0, "sugar": 0, "fat": 2, "fibre": 0}),
    "steak": ("a 150g steak", "a 150g steak",
              {"protein": 35, "carbs": 0, "sugar": 0, "fat": 12, "fibre": 0}),
    "pork chop": ("a pork chop", "one 150g chop",
                  {"protein": 35, "carbs": 0, "sugar": 0, "fat": 15, "fibre": 0}),
    "beef mince": ("a 100g portion of beef mince", "100g cooked",
                   {"protein": 25, "carbs": 0, "sugar": 0, "fat": 15, "fibre": 0}),
    "mince": ("a 100g portion of beef mince", "100g cooked",
              {"protein": 25, "carbs": 0, "sugar": 0, "fat": 15, "fibre": 0}),
    "halloumi": ("a 100g portion of halloumi", "a 100g portion",
                 {"protein": 22, "carbs": 2, "sugar": 1, "fat": 25, "fibre": 0}),
    "lentils": ("a 100g portion of cooked lentils", "a 100g cooked portion",
                {"protein": 9, "carbs": 20, "sugar": 1, "fat": 0, "fibre": 8,
                 "iron": 3.3}),
    "chickpeas": ("a 100g portion of cooked chickpeas", "a 100g cooked portion",
                  {"protein": 9, "carbs": 27, "sugar": 5, "fat": 3, "fibre": 8,
                   "iron": 2.9}),
    "kidney beans": ("a 100g portion of kidney beans", "100g cooked",
                     {"protein": 8, "carbs": 20, "sugar": 1, "fat": 0, "fibre": 6}),
    "black beans": ("a 100g portion of black beans", "100g cooked",
                    {"protein": 9, "carbs": 23, "sugar": 0, "fat": 0, "fibre": 8}),
    "baked beans": ("a 200g portion of baked beans", "half a tin",
                    {"protein": 10, "carbs": 25, "sugar": 10, "fat": 1, "fibre": 8,
                     "iron": 2.5, "salt": 1.2}),
    "tofu": ("a 100g portion of tofu", "a 100g portion",
             {"protein": 12, "carbs": 1, "sugar": 1, "fat": 6, "fibre": 1,
              "calcium": 200}),
    "quinoa": ("a 100g portion of cooked quinoa", "a 100g cooked portion",
               {"protein": 4, "carbs": 21, "sugar": 1, "fat": 2, "fibre": 3}),
    "oats": ("a 40g portion of oats", "a 40g dry portion",
             {"protein": 4, "carbs": 24, "sugar": 0, "fat": 3, "fibre": 4, "iron": 1.6}),
    "porridge oats": ("a 40g portion of oats", "a 40g dry portion",
                      {"protein": 4, "carbs": 24, "sugar": 0, "fat": 3, "fibre": 4}),
    "porridge": ("a bowl of porridge", "made with water",
                 {"protein": 5, "carbs": 27, "sugar": 0, "fat": 4, "fibre": 4}),
    "slice of bread": ("a slice of bread", "a normal slice",
                       {"protein": 4, "carbs": 15, "sugar": 2, "fat": 1, "fibre": 2,
                        "iron": 1.2, "salt": 0.4}),
    "wholemeal bread": ("a slice of wholemeal bread", "a normal slice",
                        {"protein": 5, "carbs": 14, "sugar": 1, "fat": 1, "fibre": 3,
                         "iron": 1.3, "salt": 0.4}),
    "bread": ("a slice of bread", "a normal slice",
              {"protein": 4, "carbs": 15, "sugar": 2, "fat": 1, "fibre": 2,
               "iron": 1.2, "salt": 0.4}),
    "pasta": ("a bowl of cooked pasta", "a 200g cooked bowl",
              {"protein": 10, "carbs": 60, "sugar": 2, "fat": 2, "fibre": 4, "iron": 1.4}),
    "rice": ("a bowl of cooked rice", "a 180g cooked bowl",
             {"protein": 5, "carbs": 50, "sugar": 0, "fat": 1, "fibre": 1}),
    "brown rice": ("a bowl of cooked brown rice", "a 180g cooked bowl",
                   {"protein": 5, "carbs": 45, "sugar": 1, "fat": 2, "fibre": 4}),
    "baked potato": ("a medium baked potato", "a medium one",
                     {"protein": 5, "carbs": 45, "sugar": 2, "fat": 0, "fibre": 5,
                      "potassium": 900}),
    "potato": ("a medium potato", "a medium one",
               {"protein": 4, "carbs": 30, "sugar": 2, "fat": 0, "fibre": 3,
                "potassium": 700}),
    "sweet potato": ("a medium sweet potato", "a medium one",
                     {"protein": 2, "carbs": 26, "sugar": 7, "fat": 0, "fibre": 4}),
    "banana": ("a banana", "a medium one",
               {"protein": 1, "carbs": 27, "sugar": 14, "fat": 0, "fibre": 3,
                "potassium": 430}),
    "apple": ("an apple", "a medium one",
              {"protein": 1, "carbs": 25, "sugar": 19, "fat": 0, "fibre": 4}),
    "orange": ("an orange", "a medium one",
               {"protein": 1, "carbs": 15, "sugar": 12, "fat": 0, "fibre": 3,
                "calcium": 50, "potassium": 240}),
    "pear": ("a pear", "a medium one",
             {"protein": 1, "carbs": 27, "sugar": 17, "fat": 0, "fibre": 6}),
    "strawberries": ("strawberries", "a handful",
                     {"protein": 1, "carbs": 6, "sugar": 4, "fat": 0, "fibre": 2}),
    "grapes": ("grapes", "a handful",
               {"protein": 1, "carbs": 17, "sugar": 16, "fat": 0, "fibre": 1}),
    "avocado": ("an avocado", "a whole one",
                {"protein": 3, "carbs": 12, "sugar": 1, "fat": 21, "fibre": 10}),
    "broccoli": ("a portion of broccoli", "a normal portion",
                 {"protein": 3, "carbs": 3, "sugar": 2, "fat": 0, "fibre": 3,
                  "iron": 0.7, "calcium": 40}),
    "peas": ("a portion of peas", "a normal portion",
             {"protein": 5, "carbs": 9, "sugar": 3, "fat": 0, "fibre": 4, "iron": 1.2}),
    "peanut butter": ("a tablespoon of peanut butter", "a tablespoon",
                      {"protein": 4, "carbs": 3, "sugar": 1, "fat": 8, "fibre": 1}),
    "almonds": ("a handful of almonds", "a 30g handful",
                {"protein": 6, "carbs": 5, "sugar": 1, "fat": 15, "fibre": 4}),
    "walnuts": ("a handful of walnuts", "a 30g handful",
                {"protein": 5, "carbs": 2, "sugar": 1, "fat": 19, "fibre": 2}),
    "cashews": ("a handful of cashews", "a 30g handful",
                {"protein": 5, "carbs": 9, "sugar": 2, "fat": 13, "fibre": 1}),
    "hummus": ("a 100g portion of hummus", "a 100g portion",
               {"protein": 8, "carbs": 14, "sugar": 1, "fat": 10, "fibre": 6}),
    "chocolate bar": ("a chocolate bar", "a standard one",
                      {"protein": 3, "carbs": 26, "sugar": 24, "fat": 13, "fibre": 2}),
    "crisps": ("a packet of crisps", "a 25g packet",
               {"protein": 2, "carbs": 13, "sugar": 0, "fat": 8, "fibre": 1}),
    # The drinks people ask about by name, because the sugar in them is the question and the
    # caffeine card was answering it: "how much sugar is in a cup of tea" and "how many calories
    # in a cup of tea" were told the 400mg caffeine limit, and sugar in a squash was a shrug. A
    # tea or a coffee has no sugar of its own, which the table can say, and the figure that
    # matters is what goes in - so the answer says the spoonful's number beside the zero.
    # the subject says "cup" and the portion says "mug" on purpose: both words are how people
    # write the drink, and the amount check reads the one the line used against either
    "tea": ("a cup of tea", "a mug without sugar",
            {"protein": 0, "carbs": 0, "sugar": 0, "fat": 0, "fibre": 0}),
    "coffee": ("a cup of coffee", "a mug without sugar",
               {"protein": 0, "carbs": 0, "sugar": 0, "fat": 0, "fibre": 0}),
    "squash": ("a glass of squash", "a 250ml glass as you make it",
               {"protein": 0, "carbs": 5, "sugar": 5, "fat": 0, "fibre": 0}),
    "energy drink": ("a 250ml can of energy drink", "a 250ml can",
                     {"protein": 0, "carbs": 27, "sugar": 27, "fat": 0, "fibre": 0}),
    "apple juice": ("a glass of apple juice", "a 200ml glass",
                    {"protein": 0, "carbs": 21, "sugar": 21, "fat": 0, "fibre": 0}),
    "coke": ("a can of coke", "a 330ml can",
             {"protein": 0, "carbs": 35, "sugar": 35, "fat": 0, "fibre": 0}),
    "cola": ("a can of cola", "a 330ml can",
             {"protein": 0, "carbs": 35, "sugar": 35, "fat": 0, "fibre": 0}),
    "orange juice": ("a glass of orange juice", "a 200ml glass",
                     {"protein": 1, "carbs": 20, "sugar": 20, "fat": 0, "fibre": 0,
                      "potassium": 400}),
    "ice cream": ("a scoop of ice cream", "a scoop",
                  {"protein": 2, "carbs": 15, "sugar": 13, "fat": 7, "fibre": 0}),
    # The iron-heavy foods, which people ask about by name: spinach is the one line where the
    # ironing board used to answer, and a bowl of cereal is the everyday source of it.
    "spinach": ("a 100g portion of spinach", "a 100g portion",
                {"protein": 3, "carbs": 1, "sugar": 0, "fat": 0, "fibre": 2,
                 "iron": 2.7, "calcium": 100, "potassium": 500}),
    "kale": ("a 100g portion of kale", "a 100g portion",
             {"protein": 3, "carbs": 1, "sugar": 1, "fat": 1, "fibre": 2,
              "iron": 1.5, "calcium": 150, "potassium": 400}),
    "cereal": ("a 40g bowl of cereal", "a 40g bowl",
               {"protein": 4, "carbs": 25, "sugar": 8, "fat": 1, "fibre": 4,
                "iron": 3, "salt": 0.4}),
    "cornflakes": ("a 40g bowl of cornflakes", "a 40g bowl",
                   {"protein": 3, "carbs": 33, "sugar": 3, "fat": 0, "fibre": 1,
                    "iron": 3.2, "salt": 0.5}),
    "chicken": ("a 150g piece of cooked chicken", "a 150g piece",
                {"protein": 45, "carbs": 0, "sugar": 0, "fat": 4, "fibre": 0,
                 "iron": 1.5, "salt": 0.2}),
    "ham": ("a slice of ham", "a 25g slice",
            {"protein": 5, "carbs": 0, "sugar": 0, "fat": 1, "fibre": 0, "salt": 0.6}),
    "wholemeal pasta": ("a bowl of cooked wholemeal pasta", "a 200g cooked bowl",
                        {"protein": 11, "carbs": 55, "sugar": 2, "fat": 2, "fibre": 8,
                         "iron": 2.6}),
    # The everyday biscuits, cereals and sauces, beside the fruit and the egg: "how much sugar is
    # in a digestive" was a shrug, and the four biscuits people ask about are 1g to 4g each, which
    # is exactly the difference a person cannot guess. Ordinary supermarket versions.
    "digestive": ("a digestive biscuit", "one",
                  {"protein": 1, "carbs": 10, "sugar": 3, "fat": 2, "fibre": 1}),
    "digestive biscuit": ("a digestive biscuit", "one",
                          {"protein": 1, "carbs": 10, "sugar": 3, "fat": 2, "fibre": 1}),
    "digestives": ("a digestive biscuit", "one",
                   {"protein": 1, "carbs": 10, "sugar": 3, "fat": 2, "fibre": 1}),
    "rich tea": ("a rich tea biscuit", "one",
                 {"protein": 1, "carbs": 6, "sugar": 1, "fat": 1, "fibre": 0}),
    "rich tea biscuit": ("a rich tea biscuit", "one",
                         {"protein": 1, "carbs": 6, "sugar": 1, "fat": 1, "fibre": 0}),
    "hobnob": ("a hobnob", "one", {"protein": 1, "carbs": 12, "sugar": 4, "fat": 4, "fibre": 1}),
    "hobnobs": ("a hobnob", "one", {"protein": 1, "carbs": 12, "sugar": 4, "fat": 4, "fibre": 1}),
    "custard cream": ("a custard cream", "one",
                      {"protein": 1, "carbs": 9, "sugar": 3, "fat": 3, "fibre": 0}),
    "custard creams": ("a custard cream", "one",
                       {"protein": 1, "carbs": 9, "sugar": 3, "fat": 3, "fibre": 0}),
    "ketchup": ("a tablespoon of ketchup", "a tablespoon",
                {"protein": 0, "carbs": 4, "sugar": 4, "fat": 0, "fibre": 0}),
    "granola": ("a 50g portion of granola", "a 50g portion",
                {"protein": 5, "carbs": 32, "sugar": 11, "fat": 8, "fibre": 3}),
    "cereal bar": ("a cereal bar", "one",
                   {"protein": 2, "carbs": 17, "sugar": 7, "fat": 3, "fibre": 2}),
    "granola bar": ("a cereal bar", "one",
                    {"protein": 2, "carbs": 17, "sugar": 7, "fat": 3, "fibre": 2}),
    "milkshake": ("a medium milkshake", "a 400ml one",
                  {"protein": 11, "carbs": 60, "sugar": 55, "fat": 7, "fibre": 0}),
    "milkshakes": ("a medium milkshake", "a 400ml one",
                   {"protein": 11, "carbs": 60, "sugar": 55, "fat": 7, "fibre": 0}),
    # The composites, on the same portions as their rows in FOOD_CALORIES: a sausage roll, a
    # pasty, a sandwich and a pie are what people ask a nutrient figure about, and on main
    # "how much protein in a scone" was answered with the protein a person needs in a day,
    # which is true and is not what was asked. Four grams of carbohydrate or protein is 16
    # calories and a gram of fat is 9, so each row's fuel adds up to its calories.
    "sausage roll": ("a sausage roll", "one",
                     {"protein": 9, "carbs": 27, "sugar": 1, "fat": 20, "fibre": 1.5}),
    "sausage rolls": ("a sausage roll", "one",
                      {"protein": 9, "carbs": 27, "sugar": 1, "fat": 20, "fibre": 1.5}),
    "pasty": ("a pasty", "one",
              {"protein": 11, "carbs": 38, "sugar": 2, "fat": 22, "fibre": 2}),
    "pastie": ("a pasty", "one",
               {"protein": 11, "carbs": 38, "sugar": 2, "fat": 22, "fibre": 2}),
    "meat pie": ("a meat pie", "one",
                 {"protein": 15, "carbs": 45, "sugar": 2, "fat": 26, "fibre": 2}),
    "pork pie": ("a pork pie", "one",
                 {"protein": 15, "carbs": 33, "sugar": 2, "fat": 26, "fibre": 1.5}),
    "shepherds pie": ("a portion of shepherd's pie", "a 400g portion",
                      {"protein": 18, "carbs": 40, "sugar": 6, "fat": 20, "fibre": 4}),
    "shepherd's pie": ("a portion of shepherd's pie", "a 400g portion",
                       {"protein": 18, "carbs": 40, "sugar": 6, "fat": 20, "fibre": 4}),
    "spring roll": ("a spring roll", "one",
                    {"protein": 3, "carbs": 14, "sugar": 1, "fat": 6, "fibre": 1}),
    "spring rolls": ("a spring roll", "one",
                     {"protein": 3, "carbs": 14, "sugar": 1, "fat": 6, "fibre": 1}),
    "yorkshire pudding": ("a yorkshire pudding", "one",
                          {"protein": 3, "carbs": 12, "sugar": 1, "fat": 4, "fibre": 0.5}),
    "yorkshire puddings": ("a yorkshire pudding", "one",
                           {"protein": 3, "carbs": 12, "sugar": 1, "fat": 4, "fibre": 0.5}),
    "scotch egg": ("a scotch egg", "one",
                   {"protein": 12, "carbs": 15, "sugar": 1, "fat": 15, "fibre": 1}),
    "scotch eggs": ("a scotch egg", "one",
                    {"protein": 12, "carbs": 15, "sugar": 1, "fat": 15, "fibre": 1}),
    "sandwich": ("a sandwich", "one",
                 {"protein": 15, "carbs": 40, "sugar": 5, "fat": 12, "fibre": 3}),
    "sandwiches": ("a sandwich", "one",
                   {"protein": 15, "carbs": 40, "sugar": 5, "fat": 12, "fibre": 3}),
    "chip butty": ("a chip butty", "one",
                   {"protein": 10, "carbs": 60, "sugar": 3, "fat": 20, "fibre": 5}),
    "lasagne": ("a portion of lasagne", "a 400g portion",
                {"protein": 30, "carbs": 45, "sugar": 8, "fat": 28, "fibre": 4}),
    "lasagna": ("a portion of lasagne", "a 400g portion",
                {"protein": 30, "carbs": 45, "sugar": 8, "fat": 28, "fibre": 4}),
    # The dishes, in the same portions as the calorie table above: a dish is not an ingredient,
    # and the two figures for it have to agree.
    "chicken curry": ("a portion of chicken curry", "a 350g portion",
                      {"protein": 30, "carbs": 12, "sugar": 5, "fat": 18, "fibre": 3}),
    "chicken tikka masala": ("a portion of chicken tikka masala", "a 400g portion",
                             {"protein": 32, "carbs": 18, "sugar": 9, "fat": 24, "fibre": 3}),
    "chilli con carne": ("a portion of chilli con carne", "a 350g portion",
                         {"protein": 25, "carbs": 20, "sugar": 8, "fat": 15, "fibre": 8}),
    "spaghetti bolognese": ("a portion of spaghetti bolognese", "a 400g portion",
                            {"protein": 25, "carbs": 55, "sugar": 9, "fat": 14, "fibre": 5}),
    "cottage pie": ("a portion of cottage pie", "a 400g portion",
                    {"protein": 22, "carbs": 40, "sugar": 6, "fat": 16, "fibre": 5}),
    "fish pie": ("a portion of fish pie", "a 400g portion",
                 {"protein": 20, "carbs": 35, "sugar": 5, "fat": 18, "fibre": 3}),
    "chicken salad": ("a bowl of chicken salad", "a 300g bowl",
                      {"protein": 30, "carbs": 8, "sugar": 5, "fat": 12, "fibre": 4}),
    "chicken soup": ("a bowl of chicken soup", "a 350g bowl",
                     {"protein": 12, "carbs": 12, "sugar": 4, "fat": 6, "fibre": 2}),
    "lentil soup": ("a bowl of lentil soup", "a 350g bowl",
                    {"protein": 12, "carbs": 25, "sugar": 4, "fat": 5, "fibre": 8}),
    "dal": ("a portion of dal", "a 300g portion",
            {"protein": 14, "carbs": 30, "sugar": 3, "fat": 8, "fibre": 9}),
    "chicken stir fry": ("a portion of chicken stir fry", "a 400g portion",
                         {"protein": 28, "carbs": 45, "sugar": 10, "fat": 12, "fibre": 5}),
    "stir fry": ("a portion of stir fry", "a 400g portion",
                 {"protein": 18, "carbs": 45, "sugar": 9, "fat": 12, "fibre": 6}),
    "chicken sandwich": ("a chicken sandwich", "one",
                         {"protein": 18, "carbs": 35, "sugar": 4, "fat": 6, "fibre": 3}),
    "tuna sandwich": ("a tuna sandwich", "one",
                      {"protein": 20, "carbs": 34, "sugar": 4, "fat": 9, "fibre": 3}),
    "slice of cake": ("a slice of cake", "one slice",
                      {"protein": 3, "carbs": 27, "sugar": 18, "fat": 9, "fibre": 1}),
    "victoria sponge": ("a slice of victoria sponge", "one slice",
                        {"protein": 3, "carbs": 30, "sugar": 20, "fat": 10, "fibre": 1}),
    "bakewell tart": ("a bakewell tart", "one",
                      {"protein": 3, "carbs": 33, "sugar": 20, "fat": 12, "fibre": 1.5}),
    "scone": ("a scone", "one",
              {"protein": 4, "carbs": 35, "sugar": 8, "fat": 7, "fibre": 1.5}),
    "scones": ("a scone", "one",
               {"protein": 4, "carbs": 35, "sugar": 8, "fat": 7, "fibre": 1.5}),
    "crumpet": ("a crumpet", "one",
                {"protein": 3, "carbs": 23, "sugar": 1, "fat": 1, "fibre": 1}),
    "crumpets": ("a crumpet", "one",
                 {"protein": 3, "carbs": 23, "sugar": 1, "fat": 1, "fibre": 1}),
    "bagel": ("a bagel", "one",
              {"protein": 10, "carbs": 50, "sugar": 3, "fat": 2, "fibre": 3}),
    "bagels": ("a bagel", "one",
               {"protein": 10, "carbs": 50, "sugar": 3, "fat": 2, "fibre": 3}),
    # the two the calories table already holds as a meal, so the same portion is written here
    "fish and chips": ("a normal portion of fish and chips", "a normal portion",
                       {"protein": 45, "carbs": 75, "sugar": 2, "fat": 40, "fibre": 6}),
    "pizza": ("a 12-inch takeaway pizza", "a whole pepperoni one",
              {"protein": 90, "carbs": 220, "sugar": 20, "fat": 84, "fibre": 10}),
    "kebab": ("a doner kebab in pitta with sauce", "a standard one",
              {"protein": 45, "carbs": 70, "sugar": 8, "fat": 60, "fibre": 5}),
    # ...and the sweet one the calories table holds, on the same portion
    "doughnut": ("a doughnut", "one",
                 {"protein": 3, "carbs": 30, "sugar": 12, "fat": 13, "fibre": 1}),
    "doughnuts": ("a doughnut", "one",
                  {"protein": 3, "carbs": 30, "sugar": 12, "fat": 13, "fibre": 1}),
    "donut": ("a doughnut", "one",
              {"protein": 3, "carbs": 30, "sugar": 12, "fat": 13, "fibre": 1}),
    "croissant": ("a croissant", "one",
                  {"protein": 5, "carbs": 33, "sugar": 7, "fat": 14, "fibre": 2}),
    "croissants": ("a croissant", "one",
                   {"protein": 5, "carbs": 33, "sugar": 7, "fat": 14, "fibre": 2}),
    "biscuit": ("a biscuit", "one",
                {"protein": 1, "carbs": 7, "sugar": 3, "fat": 2, "fibre": 0.5}),
    "biscuits": ("a biscuit", "one",
                 {"protein": 1, "carbs": 7, "sugar": 3, "fat": 2, "fibre": 0.5}),
}

FOOD_CALORIE_MEALS = {
    "chicken and chips": ("a plate of chicken and chips", "a normal takeaway plate", 850),
    "fish and chips": ("fish and chips", "a normal portion", 840),
    "burger and chips": ("a burger and chips", "a normal portion", 900),
    "sausage and chips": ("sausage and chips", "a normal portion", 700),
    "egg and chips": ("egg and chips", "a normal portion", 600),
    "beans on toast": ("beans on toast", "one slice with half a tin", 300),
    "cheese on toast": ("cheese on toast", "one slice", 320),
    "bangers and mash": ("bangers and mash", "two sausages with mash", 700),
    "roast dinner": ("a roast dinner", "a normal plate", 750),
    # The takeaway dishes people ask about by name. A whole pizza is a dish, and the parts of it
    # are dishes too, so the longest name in the line wins: "slice of pizza" is longer than
    # "pizza", and a slice is 250 rather than the two thousand in a whole one.
    "doner kebab": ("a doner kebab in pitta with sauce", "a standard one", 1000),
    "kebab": ("a doner kebab in pitta with sauce", "a standard one", 1000),
    "chicken tikka masala": ("chicken tikka masala with pilau rice and a naan", "a takeaway "
                             "portion", 1300),
    "curry and rice": ("a curry with pilau rice", "a takeaway portion", 900),
    "pie and chips": ("pie and chips", "a normal portion", 1000),
    "chinese takeaway": ("a Chinese takeaway", "sweet and sour chicken with egg fried rice", 1200),
    "chinese": ("a Chinese takeaway", "sweet and sour chicken with egg fried rice", 1200),
    "indian takeaway": ("an Indian takeaway", "chicken tikka masala with pilau rice and a naan",
                        1300),
    "indian": ("an Indian takeaway", "chicken tikka masala with pilau rice and a naan", 1300),
    "pizza slice": ("a slice of pizza", "a normal slice", 250),
    "slice of pizza": ("a slice of pizza", "a normal slice", 250),
    "half a pizza": ("half a 12-inch pepperoni pizza", "half of one", 1000),
    "pizza": ("a 12-inch takeaway pizza", "a whole pepperoni one", 2000),
    # The everyday dishes that were a shrug. Each is the dish as it arrives on a plate or in a
    # bag, because that is the question: "how many calories in a lasagne" is not asking about
    # the ingredients, and a bare "curry" is a takeaway one until the line says otherwise.
    "big mac": ("a Big Mac", "one", 500),
    "cheeseburger": ("a cheeseburger", "a standard one", 320),
    "burger": ("a burger", "a standard takeaway one", 500),
    "curry": ("a takeaway curry", "a takeaway portion", 700),
    # A dish a person names with two words is the dish they meant, and the one-word row above
    # would otherwise take it: "chicken curry" answered with "a portion of roast chicken is about
    # 300 calories" is a confident number for a food nobody asked about, which is worse than the
    # shrug it replaced. The table already prefers the longest name in the line, so a compound
    # only has to be in it to win.
    "chicken curry": ("a portion of chicken curry", "a normal plateful", 600),
    "chicken korma": ("a chicken korma", "a takeaway portion", 800),
    "chicken tikka": ("a portion of chicken tikka", "a normal plateful", 350),
    "curry sauce": ("a portion of curry sauce", "a small pot", 150),
    "curry powder": ("a teaspoon of curry powder", "a teaspoon", 6),
    "whole chicken": ("a whole roast chicken", "a whole one", 1600),
    "cappuccino cake": ("a slice of cappuccino cake", "a normal slice", 350),
    "spaghetti bolognese": ("a portion of spaghetti bolognese", "a normal plateful", 600),
    # Lasagne, shepherd's pie, pasty, Bakewell tart and a sandwich are not here on purpose: the
    # ingredient table already answers them with a number of its own (550 at 400g, 410 at 400g,
    # 400, 250, 330), and a second row would only change a number main already gets right. A row
    # belongs here where main says nothing, not where it says something different.
    "cottage pie": ("a portion of cottage pie", "a normal plateful", 400),
    "muffin": ("a muffin", "a shop one", 350),
    "pastry": ("a pastry", "a standard one", 300),
    "cappuccino": ("a cappuccino", "a medium one with semi-skimmed milk", 120),
    "mars bar": ("a Mars bar", "one", 230),
    "bowl of soup": ("a bowl of soup", "a thick vegetable one", 250),
    "slice of cake": ("a slice of cake", "a normal slice", 350),
    "cupcake": ("a cupcake with buttercream", "one", 350),
    # A whole cake is the one dish where the portion is the answer: "how many calories in a cake"
    # is asked about the eight to ten slices it makes, so the number is the whole thing and the
    # note says how it is cut. "A slice of cake" is the longer name and wins its own lines.
    "cake": ("a whole 20cm sponge cake", "a whole one, cut into 8 to 10 slices", 3200),
    "piece of cake": ("a slice of cake", "a normal slice", 350),
    "coffee cake": ("a slice of coffee cake", "a normal slice", 350),
    "coffee": ("a white coffee", "a mug with milk", 35),
    # "how many calories in a cup of tea" was the caffeine limit, and "does tea have calories"
    # was a dinner plate. A mug of tea is nearly nothing black, and the milk is the figure.
    "tea": ("a cup of tea", "a mug with a splash of semi-skimmed milk", 15),
    "chicken": ("a portion of roast chicken", "a normal helping", 300),
    "soup": ("a bowl of soup", "a thick vegetable one", 250),
}

BAKES = {
    "chocolate cake": (("chocolate cake", "chocolate sponge", "chocolate gateau"),
                       "Equal weights of everything: for a 20cm tin, 200g each of soft butter, "
                       "caster sugar, eggs and self-raising flour, with 50g of the flour swapped "
                       "for cocoa. Cream the butter and sugar, beat the eggs in one at a time, "
                       "fold in the flour and cocoa, then bake at 180C (160C fan) for 25 to 30 "
                       "minutes, until a skewer comes out clean."),
    "victoria sponge": (("victoria sponge", "sponge cake", "victoria sandwich", "plain sponge"),
                        "Weigh the eggs and use the same weight of soft butter, caster sugar and "
                        "self-raising flour: three eggs fills two 20cm tins. Cream butter and "
                        "sugar, beat the eggs in a spoonful at a time, fold in the flour, split "
                        "between the tins and bake at 180C (160C fan) for 20 to 25 minutes, then "
                        "sandwich with jam and whipped cream."),
    "brownies": (("brownies", "brownie", "chocolate brownies"),
                 "Melt 200g dark chocolate with 180g butter, beat in 250g sugar and 3 eggs, then "
                 "fold in 100g plain flour and a pinch of salt. Bake in a lined 20cm square tin "
                 "at 180C (160C fan) for 20 to 25 minutes: the middle should still be a little "
                 "soft when you take it out, and it sets as it cools."),
    "scones": (("scones", "scone", "cheese scones"),
               "350g self-raising flour, 2 teaspoons baking powder, 85g cold butter rubbed in, "
               "then 3 tablespoons of sugar and about 150ml milk to bring it together - handle it "
               "as little as you can. Cut into rounds, brush with milk and bake at 220C (200C fan) "
               "for 12 to 15 minutes, until risen and golden."),
    "bread": (("white bread", "bread", "loaf of bread", "bread dough", "loaf"),
              "500g strong white flour, 7g dried yeast, 10g salt and 350ml warm water, kneaded "
              "for 10 minutes until smooth and stretched. Leave it somewhere warm for an hour "
              "until doubled, knock it back, shape it into a tin, leave it 45 minutes more, then "
              "bake at 220C (200C fan) for 30 minutes - it is done when it sounds hollow "
              "underneath."),
    "banana bread": (("banana bread", "banana loaf"),
                     "Three very ripe bananas mashed with 150g soft brown sugar, 2 eggs and 100g "
                     "melted butter, then 250g self-raising flour and a teaspoon of cinnamon "
                     "folded in. Bake in a lined loaf tin at 170C (150C fan) for 55 to 60 "
                     "minutes; a skewer in the middle should come out with crumbs, not batter."),
    "flapjack": (("flapjack", "flapjacks"),
                 "Melt 150g butter with 120g golden syrup and 120g soft brown sugar, stir in 300g "
                 "porridge oats, press into a lined 20cm square tin and bake at 180C (160C fan) "
                 "for 20 to 25 minutes. Leave it in the tin until it is completely cold, or it "
                 "will not cut."),
    "cookies": (("cookies", "cookie", "chocolate chip cookies", "biscuits"),
                "Cream 125g soft butter with 100g sugar, beat in 1 egg, then stir in 175g plain "
                "flour, half a teaspoon of bicarbonate of soda and 100g chocolate chips. Roll "
                "into balls, space them well apart on a lined tray and bake at 180C (160C fan) "
                "for 10 to 12 minutes - they firm up as they cool."),
    "crumble": (("crumble", "fruit crumble", "apple crumble"),
                "Rub 100g cold butter into 200g plain flour with 75g sugar until it looks like "
                "breadcrumbs, then scatter it over fruit with a spoon of sugar on top. Bake at "
                "190C (170C fan) for 35 to 40 minutes, until the fruit bubbles at the edges and "
                "the top is golden."),
    # No bare "pastry" here: puff pastry is a different answer from shortcrust, so each names
    # itself and the naked word stays with the fault entries that need it.
    "puff pastry": (("puff pastry", "puff pastry sheet", "ready rolled puff pastry"),
                    "Puff pastry: a sheet with the filling already cooked and cooled goes in at "
                    "200C (180C fan) for 25 to 30 minutes, and one brushed with beaten egg "
                    "browns better. Score the top so the steam gets out."),
    "shortcrust pastry": (("shortcrust pastry", "pie crust", "pastry"),
                          "Half the fat to flour by weight: 250g plain flour and 125g cold butter "
                          "rubbed in with a pinch of salt, then a few spoons of cold water to "
                          "bring it together. Rest it in the fridge 30 minutes before rolling, "
                          "and bake blind at 190C (170C fan) for 15 minutes for a flan case."),
    # Every named loaf is its own recipe, because the white loaf above is a confident wrong answer
    # to all of them: a sourdough loaf has no dried yeast in it, soda bread has no yeast at all and
    # is not left to rise, wholemeal drinks more water and takes twice as long, a machine wants
    # the ingredients in a different order, and a gluten-free loaf is not made by swapping one
    # flour for another. Eggy bread already has its own answer (recipe-french-toast) and is left
    # alone.
    "sourdough bread": (("sourdough bread", "sourdough loaf", "sour dough bread", "sourdough"),
                        "Sourdough is a starter, not dried yeast: 100g of fed starter to 500g "
                        "strong flour and about 350ml water, mixed and left 4 to 6 hours with a "
                        "fold every hour until it is puffy, then shaped and proved in the fridge "
                        "overnight. Bake it at 250C in a lidded pot for 20 minutes with the lid "
                        "on and 20 to 25 with it off. A starter takes about a week of feeding "
                        "before it will raise a loaf, so this is a plan for next weekend rather "
                        "than tonight."),
    # no soda row here: main grew its own soda-bread answer (no yeast, no waiting, bicarbonate
    # and buttermilk) and a second row only took the timing line away from the loaf table, where
    # "how long do i bake soda bread for" gets 35 to 45 minutes and the first 15 with steam.
    "wholemeal bread": (("wholemeal bread", "wholewheat bread", "whole wheat bread",
                         "wholemeal loaf", "brown bread", "granary loaf"),
                        "Use 300g wholemeal flour with 200g strong white, 7g dried yeast, 10g "
                        "salt and about 380ml warm water: wholemeal drinks more, so it wants a "
                        "wetter dough than white. Leave it 2 to 3 hours until it has doubled "
                        "rather than 1 to 2, prove the shaped loaf 45 minutes, then bake at 220C "
                        "(200C fan) for 35 to 40 minutes."),
    "bread maker loaf": (("bread maker", "breadmaker", "bread machine"),
                         "Put the water in the pan first, then the flour, then the salt in one "
                         "corner and the yeast in the other so the salt never sits on the yeast, "
                         "and set the basic white programme. 500g of flour and 7g of yeast fits a "
                         "standard 1.5kg machine, and taking the loaf out about 5 minutes before "
                         "the end keeps the crust from going soft in the pan."),
    "gluten free bread": (("gluten free bread", "gluten-free bread", "gluten free loaf",
                           "gf bread"),
                          "Buy a gluten-free bread blend with a binder in it rather than swapping "
                          "the flour in a normal recipe, which gives a brick: the dough is more "
                          "like a thick batter, so it goes straight into the tin and gets one "
                          "rise, then 40 to 45 minutes at 200C (180C fan). Let it cool fully "
                          "before you slice it, or it crumbles."),
}

KEEPS = (
    (("potato", "potatoes", "new potatoes", "spuds", "tatties"),
     "Keep potatoes in a paper or cloth bag in a dark cupboard, around 7 to 10C if you have "
     "somewhere that cool: light turns them green and the fridge turns the starch to sugar, so "
     "never the fridge and never a sealed plastic bag. Pick out any that have gone soft and they "
     "keep a month or more; cut small green patches away, but bin one that is green all through "
     "or sprouting badly."),
    (("onion", "onions", "shallots"),
     "Onions want dry, dark and airy: a mesh bag or a string in a cupboard, never the fridge, "
     "where the damp makes them soft and mouldy, and not in the same bag as the potatoes, "
     "because each makes the other go off faster. They keep a month or more, and a cut half "
     "keeps 3 to 4 days wrapped in the fridge."),
    # Spring onions are the exception in this table: they are not a dry-stored onion at all, and
    # "how do i keep spring onions fresh" was getting the cupboard advice, which rots them. The
    # phrase is the key, so the onion row below does not take them back.
    (("spring onion", "spring onions", "scallion", "scallions", "salad onion", "salad onions"),
     "Spring onions are a fridge thing, unlike the dried onions below: wrap them in a sheet of "
     "kitchen paper or a clean tea towel and put them in the salad drawer, where they keep one to "
     "two weeks. A bunch that has gone floppy perks up in a glass of cold water for half an hour, "
     "roots down, and chopped ones freeze well in a bag for cooking."),
    (("garlic", "garlic bulb", "garlic bulbs"),
     "Whole garlic bulbs keep for months somewhere dry, dark and airy - a basket or a paper bag, "
     "not the fridge, where they go rubbery and mould. A clove that has started to sprout is "
     "still fine to cook with, and peeled cloves keep about a week in a jar in the fridge."),
    # Leeks are a fridge thing and they were the one vegetable in this table with no row of its
    # own: "how long do leeks keep in the fridge" reached the cooked-food shelf life instead.
    (("leek", "leeks"),
     "Leeks keep about a week in the salad drawer, loose in a bag or standing in an inch of water "
     "in a jar, and the green tops go in the freezer for stock. Cut leeks dry out from the cut "
     "end first, so keep them whole until you cook them; a leek that has gone slimy at the root "
     "is past it, and the layers inside hold grit, so wash them after slicing."),
    (("carrot", "carrots"),
     "Carrots keep for weeks in the salad drawer of the fridge, in a bag or a lidded tub so they "
     "do not dry out, with the green tops cut off because they pull the water out of the root. "
     "Bendy ones are still safe to eat and firm up again in a bowl of iced water for half an "
     "hour."),
    (("mushroom", "mushrooms", "chestnut mushrooms", "button mushrooms"),
     "Mushrooms keep about a week in the fridge in a paper bag, never a plastic one, which makes "
     "them sweat and go slimy. Don't wash them until you cook them; dry and shrivelled is fine, "
     "slimy or smelly is not."),
    (("berries", "strawberries", "raspberries", "blueberries", "blackberries"),
     "Berries keep 3 to 5 days in the fridge, spread on a plate lined with kitchen paper rather "
     "than heaped in the punnet, and only washed when you eat them. Pick out a mouldy one "
     "straight away, because it spreads through the lot, and freeze or cook the soft ones "
     "instead of binning them."),
    (("lemons", "lemon", "limes", "lime", "oranges"),
     "Lemons and limes keep a couple of weeks in the fridge in a bag in the salad drawer, or "
     "about a week on the counter. A cut half keeps 3 days wrapped cut side down, and a hard one "
     "gives more juice after 20 seconds in the microwave."),
    (("apples", "apple"),
     "Apples keep for weeks in the fridge, far longer than on the counter, and away from other "
     "fruit, because the gas they give off ripens everything beside them. A bruised one is fine: "
     "cut the bruise out and use it first."),
    # eggs are not in this table: raw and boiled eggs keep for different lengths, so one reply
    # cannot lead with the right one. They are two entries below.
    # "how long do i keep coffee beans" was getting the dried-beans soaking fact, because "beans"
    # is a pulse word and nothing in the table answered coffee. Coffee is not a pulse.
    (("coffee beans", "coffee bean", "ground coffee", "coffee"),
     "Whole beans keep about a month once the bag is open, in a sealed tin somewhere cool and dark; "
     "the freezer holds them six months and keeps the flavour better than the fridge, which is the "
     "worst place for them. Ground coffee is stale in a week or two, so buy it whole if you can, "
     "and keep the bag squeezed shut rather than in the fridge door."),

    (("butter", "salted butter", "unsalted butter", "block of butter"),
     "Butter keeps about 2 weeks in the fridge once opened, wrapped so it does not pick up the "
     "smell of everything else, and 3 months in the freezer; salted keeps longer than unsalted. It "
     "is fine in a dish on the counter for a day or two, and it turns rancid at the surface first, "
     "which shows as a darker edge and a cheese smell."),
    (("cheese", "cheddar", "brie", "camembert", "parmesan", "mozzarella", "feta", "stilton"),
     "Hard cheese keeps 2 weeks in the fridge once opened and soft cheese about a week: wrap it in "
     "paper rather than cling film, which sweats it, and keep it in the vegetable drawer, which is "
     "the coldest part. Cut the mould off hard cheese an inch past it and the rest is fine; mould "
     "on soft cheese means the whole piece goes."),
    # The pot in the fridge is the keeping question people ask most after a big cook, and the
    # general cooked-food row ("3 to 4 days") is right but says nothing about a pot, a freezer,
    # or reheating it once. Soup is also not a food in COOKED_KEEPS, so "how long will soup keep"
    # had no row at all and fell through to a cooking time - "6 to 8 minutes" to a keeping
    # question. One row, because a stew, a curry and a casserole are the same pot.
    # A curry, a casserole and a gravy already have keeping answers of their own that name the
    # dish ("It keeps 3 days in the fridge") and the pot row took them with a soup-first answer,
    # so its names are the thin things that had no row at all.
    (("soup", "soups", "broth", "stew", "stews",
      # the soup's own name is a phrase and beats the food in it: "how long does chicken soup
      # keep" was the raw-chicken row (1 to 2 days, which is the dangerous direction for a pot
      # of soup) and "how long does vegetable soup keep" was the veg drawer (a week). A soup
      # made of something is still the pot.
      "chicken soup", "vegetable soup", "tomato soup", "lentil soup", "mushroom soup",
      "potato soup", "leek soup", "noodle soup", "onion soup", "minestrone", "chowder",
      "bone broth", "beef stew", "chicken stew", "lamb stew", "soup mix"),
     "Soup keeps 3 to 4 days in the fridge in a sealed pot, and stew or curry the same, and any "
     "of them freezes for up to 3 months. Cool a big pot quickly by standing it in a sink of cold "
     "water, then reheat only what you are eating, once, until it is piping hot right through."),
    # Seven foods people ask about every week that had no row at all, so both halves of the
    # question went elsewhere: "how long does mince keep" and "how long does ham keep" were a
    # search hedge, "is my tofu out of date" and "is my avocado out of date" were a hedge too,
    # "how long does cream keep" was the yogurt spoilage card, and "how long does orange juice
    # keep" was the lemons row, because "oranges" is in it. Each row is the food, where it
    # lives and the number of days, which is the whole question.
    (("tofu", "bean curd", "firm tofu", "silken tofu", "smoked tofu"),
     "Tofu keeps for months in its unopened pack, so the date on it is the one to go by. Once it "
     "is open, keep it in a tub covered with cold water and change the water every day: it is "
     "good for 3 to 5 days like that, and freezing it changes it to a spongier texture that "
     "takes a sauce better in a curry or a stir-fry. Tofu that smells sour or feels slimy goes "
     "in the bin - it is one of the foods where the smell is the answer."),
    (("cream", "double cream", "single cream", "whipping cream", "creme fraiche", "creme fresh",
      "soured cream", "sour cream"),
     "Cream goes by the date on the pot more than by any rule of thumb, and once it is open it "
     "keeps about 5 days in the fridge, with double cream lasting a few days longer than single. "
     "Keep it near the back rather than in the door, where the temperature swings. A little "
     "separation is fine and stirs back in; a sour smell, a yellow tinge or any mould means bin "
     "it, because cream does not come back."),
    (("mince", "minced beef", "beef mince", "lamb mince", "pork mince", "turkey mince",
      "chicken mince", "mincemeat"),
     "Raw mince keeps 1 to 2 days in the fridge, on the bottom shelf in a bowl so nothing drips, "
     "and freezes for about 3 months; once it is cooked, a bolognese, chilli or shepherd's pie "
     "keeps 3 to 4 days in the fridge. Cook it on the day you buy it, or freeze it that day and "
     "thaw it in the fridge overnight - it is the food to be strictest about, because mincing "
     "spreads bacteria right through the meat. Grey-brown on the outside is only oxygen and is "
     "fine; grey all through, slimy, or sour-smelling is not."),
    (("ham", "cooked ham", "sliced ham", "gammon", "prosciutto", "serrano", "parma ham"),
     "Sliced ham from a packet keeps 3 to 4 days in the fridge once it is open, in a tub or "
     "wrapped in its paper, and a whole cooked ham keeps about a week. Dry-cured ham like Parma "
     "or Serrano keeps far longer, a couple of weeks wrapped in the fridge, because the salt is "
     "doing the work. Ham that feels tacky or slimy, or smells sour, goes in the bin whatever the "
     "date says."),
    (("avocado", "avocados", "avocado pear"),
     "A hard avocado is not ripe yet: leave it on the counter for 3 to 5 days, and a paper bag "
     "with a banana in it ripens it in half the time. Once it gives to a gentle squeeze, it keeps "
     "2 to 3 days in the fridge. A cut half keeps a day or two with the stone left in, lemon "
     "juice on the flesh and cling film pressed right down on it; brown patches are only air and "
     "are fine to cut away, but a soft, stringy or sour-smelling one is not."),
    (("orange juice", "apple juice", "fruit juice", "lemon juice", "lime juice", "juice carton",
      "juice box", "smoothie", "smoothies",
      # "how long does fresh juice keep" named no named fruit and fell through: the juice is
      # the subject whether or not the person says which fruit, and the asked-for keep holds
      # the bare word off a line that is only a drink order.
      "fresh juice", "freshly squeezed", "juice", "juices"),
     "Fresh juice keeps 3 to 4 days in the fridge once it is opened, and a carton's date is for "
     "the unopened pack: after opening the vitamin C fades and it starts to ferment, so it is not "
     "a thing to keep for a week. Keep it cold, shake it before pouring, and go by the smell - "
     "juice that is fizzy or sharp has started to turn. A smoothie keeps about 2 days, and a "
     "shop-bought one no longer than its date."),
    (("halloumi", "grilling cheese"),
     "Halloumi keeps a couple of weeks unopened in the fridge, and about a week once the pack is "
     "open if you keep it in its brine or in a tub of salty water: out of the water it dries and "
     "goes rubbery rather than off. It also freezes, though it crumbles a little afterwards, and "
     "a block that has gone pink or smells sour is past it."),
    # The vegetables in the drawer that had no row at all, so both halves of the question went
    # elsewhere: "how do i store courgette", "how long do aubergines keep", "how do i keep
    # celery crisp", "how do i store broccoli" and "how long do radishes keep" were a search
    # punt, and "how long does butternut squash keep" was handed the roasting time. Each row
    # says where it lives, how long it keeps and what the signs are, in that order, because a
    # keeping line sends it on the first ask and the signs are what the next turn asks for.
    (("courgette", "courgettes", "zucchini", "zucchinis"),
     "Courgettes keep about a week in the salad drawer, loose in a paper bag rather than a plastic "
     "one that sweats them, and unwashed until you cook them. They go soft at the ends first, and "
     "a soft one is still fine grated into a soup, a fritter or a cake; one with slimy skin or "
     "mould on the stalk end goes in the bin."),
    (("aubergine", "aubergines", "eggplant", "eggplants"),
     "An aubergine keeps about a week in the fridge drawer, in a paper bag or loose, and only 2 to "
     "3 days once it is cut, wrapped on the cut face. It is a warm-weather fruit and the fridge "
     "will mark the skin, so a week is the limit rather than a target. One that has gone soft, "
     "dull and spongy has dried out: use it in a curry or a dip rather than a bake, and bin one "
     "with a brown, wet patch."),
    (("broccoli", "broccoli head", "tenderstem", "tenderstem broccoli", "purple sprouting"),
     "Broccoli keeps 3 to 5 days in the fridge, loose in a bag or a tub with a sheet of kitchen "
     "paper to take the damp. It drinks, so stand the stalk in an inch of water and it holds a "
     "couple of days longer. Yellowing florets are old age rather than rot and are fine cooked; a "
     "head that smells strong, is slimy or has black patches should go."),
    (("radish", "radishes", "raddish", "raddishes"),
     "Radishes keep 1 to 2 weeks in the fridge once the leaves are off, because the leaves pull the "
     "water out of the root; put them in a damp tea towel or a bag in the salad drawer. A soft, "
     "bendy radish crisps up again in iced water for 20 minutes. Split or slimy ones are past it."),
    (("butternut squash", "butternut", "squash", "pumpkin", "crown prince"),
     "A whole squash keeps a month or more somewhere cool, dry and dark, and it does not need the "
     "fridge. Cut, it keeps 4 to 5 days wrapped in the fridge, seeds scooped out. A squash goes "
     "sweeter after it is picked, so a patch of green skin is fine; soft brown patches or a sour "
     "smell mean bin it."),
    # "greens" is not a name here: it is the stem of "green", and it took "are green potatoes
    # safe to eat" to the cabbage row. The phrase "spring greens" is safe because it is a phrase.
    (("cabbage", "cabbages", "white cabbage", "red cabbage", "savoy", "spring greens"),
     "A whole cabbage keeps 2 weeks or more in the fridge drawer, and a cut one about a week with "
     "the cut face wrapped tight, because it dries from the cut. Keep it whole until you need it "
     "and cut out the core. Yellowing outer leaves are fine, slimy or black patches are not."),
)

PANTRY = {
    "egg": (("egg", "eggs"),
            "Scrambled eggs: 3 eggs on a low heat with butter, taken off while still glossy, on "
            "toast in 5 minutes."),
    "pasta": (("pasta", "spaghetti", "penne", "macaroni", "linguine", "fusilli"),
              "Aglio e olio: sliced garlic and a little chilli warmed in olive oil, tossed with "
              "the pasta and a splash of pasta water, 10 minutes."),
    "rice": (("rice", "basmati", "long grain rice"),
             "Egg fried rice: cold rice fried hard, an egg scrambled into it with soy sauce and "
             "peas, 10 minutes."),
    "potato": (("potato", "potatoes", "new potatoes", "spuds"),
               "Roast potatoes: parboiled 8 minutes, shaken in the pan with hot oil, then 40 "
               "minutes at 200C (180C fan)."),
    "chicken": (("chicken", "chicken thigh", "chicken thighs", "chicken breast",
                 "chicken breasts", "thighs"),
                "Roast chicken thighs at 200C (180C fan) for 35 to 40 minutes, skin side up and "
                "salted first; the skin crisps and the juices run clear."),
    "turkey": (("turkey", "turkey mince", "turkey breast", "turkey thigh"),
               "Turkey mince is lean and quick: brown it with onion and paprika in 10 minutes, "
               "then add a tin of tomatoes or a jar of curry sauce. Breast wants a hot oven and "
               "20 minutes, or a quick slice in a stir-fry, or it dries out."),
    "mince": (("mince", "minced beef", "ground beef", "minced meat", "beef mince",
               "pork mince", "lamb mince"),
              "A quick ragù: brown the mince hard, add onion, garlic and a tin of tomatoes, and "
              "simmer for 20 minutes."),
    "halloumi": (("halloumi", "halloumi cheese"),
                 "Halloumi: slice it 1cm thick, pat it dry and fry it in a dry pan for 2 minutes a "
                 "side until it is crisp outside and squeaky inside, then pile it on flatbread "
                 "with tomatoes, lemon and oil."),
    "sweet potato": (("sweet potato", "sweet potatoes"),
                     "Sweet potato wedges: cut into wedges, toss with oil, salt and paprika and "
                     "roast at 200C (180C fan) for 30 minutes, turning once. Whole ones take 45 "
                     "minutes and split open with butter and beans."),
    "squash": (("squash", "butternut squash", "pumpkin"),
               "Roast squash: cubes at 200C (180C fan) for 30 minutes with oil, salt and thyme, "
               "then toss it through pasta with parmesan, or blitz it with stock into soup."),
    "kale": (("kale", "cavolo nero"),
             "Kale: strip the stalks, tear the leaves, rub them with oil and salt for a minute "
             "and roast 12 minutes at 200C (180C fan) until the edges crisp, or stir it through "
             "pasta at the end."),
    "leek": (("leek", "leeks"),
             "Leeks: slice and wash them well, because grit hides between the layers, then sweat "
             "them in butter for 10 minutes and stir them through pasta, potatoes or soup."),
    "beetroot": (("beetroot", "beet", "beets"),
                 "Beetroot: wrap whole ones in foil and roast at 200C (180C fan) for an hour, then "
                 "rub the skins off and eat with feta and oil; grated raw with lemon is a salad "
                 "in 5 minutes."),
    "pork": (("pork", "pork chop", "pork chops", "pork loin"),
             "Pork chops: pat them dry, salt them, then 3 to 4 minutes a side in a hot pan and "
             "rest them 5 minutes, which is what keeps them juicy. Apple or mustard in the pan "
             "while they rest makes the sauce."),
    "lamb": (("lamb", "lamb chops", "lamb steak"),
             "Lamb chops: oil, salt and rosemary, 3 minutes a side in a very hot pan, then rest 5 "
             "minutes. Cubes of it browned with cumin and cinnamon, then tomatoes for 20 minutes, "
             "is a quick keema for rice."),
    "beef": (("beef", "steak", "beef steak"),
             "Steak: salt a thick one, 2 minutes a side in a smoking-hot pan, then rest it as long "
             "as it cooked. Thin strips are better stir-fried hard for 2 minutes with garlic and "
             "soy."),
    "chorizo": (("chorizo",),
                "Chorizo: slice and fry it 2 minutes and use the red oil it leaves to cook onions, "
                "chickpeas or potatoes in. A little flavours a whole pan."),
    "couscous": (("couscous",),
                 "Couscous: pour the same volume of boiling water or stock over it, lid on for 5 "
                 "minutes, then fork it through with oil, lemon and herbs."),
    "hummus": (("hummus", "houmous", "humus"),
               "Hummus on toast with sliced tomato and a drizzle of oil is a real lunch, and "
               "loosened with lemon and water it dresses roast vegetables."),
    "sausage": (("sausage", "sausages"),
                "Sausage and bean stew: brown the sausages, add a tin of beans and a tin of "
                "tomatoes with a spoon of paprika, and simmer for 20 minutes."),
    "bacon": (("bacon", "rashers"),
              "Bacon pasta: fry it with garlic, then toss it with pasta, parmesan and a splash "
              "of pasta water."),
    "ham": (("ham",),
            "A ham omelette: eggs cooked slowly in butter, ham laid in and folded over, 5 "
            "minutes."),
    "tuna": (("tuna", "tinned tuna"),
             "Tuna pasta: the tuna stirred through a garlicky tomato sauce, or cold with "
             "mayonnaise and sweetcorn."),
    "salmon": (("salmon",),
               "Roast salmon at 200C (180C fan) for 12 to 15 minutes with lemon, salt and a "
               "knob of butter, or wrap the fish in foil and bake it the same way: it is done as "
               "soon as the flesh flakes."),
    "prawn": (("prawn", "prawns", "shrimp"),
              "Garlic prawns: 2 minutes a side in garlic and chilli oil, then tossed with pasta "
              "or piled on toast."),
    "chickpea": (("chickpea", "chickpeas", "garbanzo beans"),
                 "Roast chickpeas: drained, dried, tossed with oil, salt and paprika, 25 minutes "
                 "at 200C until crisp; warm them with a tin of tomatoes for a quick curry."),
    # "bean sprouts" is its own thing: a bean row that answers it with beans on toast is the
    # naked word catching a longer name, so the longer name comes first and answers for itself.
    "bean sprouts": (("bean sprouts", "bean sprout", "beansprouts", "beansprout"),
                     "Bean sprouts: the last thing into a stir-fry, 2 minutes on a high heat with "
                     "garlic and soy so they stay crunchy, and a handful on top of a noodle soup "
                     "raw is the crunch in it."),
    "bean": (("beans", "bean", "kidney beans", "baked beans", "black beans"),
             "Beans on toast, done properly: warmed with a little garlic and paprika, and a "
             "spoon of butter at the end."),
    "lentil": (("lentil", "lentils", "red lentils"),
               "Red lentil dhal: lentils, a tin of tomatoes and cumin simmered for 20 minutes, "
               "finished with a spoon of sizzled butter."),
    # Feta is not a melting cheese, so the toastie idea was the wrong answer for it: it has its
    # own row, and the cheese row answers for the ones that do melt.
    "feta": (("feta", "feta cheese"),
             "Baked feta: put a block in a small dish with cherry tomatoes, oil, oregano and a "
             "pinch of chilli, and bake at 200C (180C fan) for 20 minutes, then mash it together "
             "and scoop it up with bread. Or crumble it cold over tomatoes, cucumber, oil and "
             "lemon."),
    "halloumi": (("halloumi", "halloumi cheese"),
                 "Sliced halloumi, fried in a dry hot pan 2 minutes a side until it is golden and "
                 "squeaky, then piled into a wrap or on top of a salad with lemon and mint."),
    "cheese": (("cheese", "cheddar", "mozzarella", "parmesan", "gruyere"),
               "A cheese toastie in a dry pan, pressed flat, 5 minutes: cheese inside, low heat "
               "so it melts before the bread burns."),
    "tomato": (("tomato", "tomatoes", "tinned tomatoes", "chopped tomatoes", "passata"),
               "A 15-minute tomato sauce: garlic softened in olive oil, a tin of tomatoes and "
               "salt, simmered while the pasta cooks."),
    "onion": (("onion", "onions"),
              "Onion soup: onions cooked slowly in butter for 20 minutes, then stock, with bread "
              "and cheese on top."),
    "garlic": (("garlic",),
               "Garlic bread, or aglio e olio: garlic warmed gently in butter or oil, never "
               "browned, which is what turns it bitter."),
    "mushroom": (("mushroom", "mushrooms"),
                 "Garlic mushrooms: fried hard in butter until brown, then a spoon of cream and "
                 "plenty of pepper."),
    "spinach": (("spinach",),
                "Wilted spinach: a hot pan, a knob of butter, 2 minutes, then a grate of nutmeg "
                "or a squeeze of lemon."),
    "courgette": (("courgette", "courgettes", "zucchini"),
                  "Courgette pasta: sliced and fried with garlic in plenty of olive oil for 8 "
                  "minutes, tossed with pasta and parmesan."),
    "pepper": (("pepper", "peppers", "bell pepper", "bell peppers"),
               "Fajitas: peppers and onion in a very hot pan with paprika and cumin, then "
               "wrapped in a tortilla."),
    "carrot": (("carrot", "carrots"),
               "Carrot soup: carrots and onion softened in butter, covered with stock, simmered "
               "20 minutes and blended."),
    "broccoli": (("broccoli",),
                 "Roasted broccoli: oil, salt and 15 minutes at 200C, which beats boiled by a "
                 "mile."),
    "cucumber": (("cucumber", "cucumbers"),
                 "Cucumber salad: slice it thin, salt it for 10 minutes and squeeze the water "
                 "out, then dress it with vinegar, oil and dill or mint."),
    "noodle": (("noodle", "noodles", "egg noodles", "ramen"),
               "Noodles: soak them in hot stock for 3 minutes, then add soy sauce, a drop of "
               "sesame oil and any greens in the fridge."),
    "aubergine": (("aubergine", "aubergines", "eggplant"),
                  "Roast aubergine: halve them, score the flesh, oil and salt it, and roast cut "
                  "side up at 200C (180C fan) for 30 minutes until it collapses."),
    "cauliflower": (("cauliflower", "cauliflowers"),
                    "Roast cauliflower: florets tossed in oil, cumin and salt at 200C (180C fan) "
                    "for 25 minutes, until the edges are brown and crisp."),
    "tofu": (("tofu", "firm tofu", "silken tofu"),
             "Crisp tofu: press a block, cube it, fry in hot oil until golden on most sides, "
             "then toss with soy sauce, honey and chilli."),
    "quorn": (("quorn", "quorn mince", "quorn pieces", "quorn fillets", "mycoprotein"),
              "Quorn: fry an onion with it until it colours, then add a tin of tomatoes and a "
              "stock cube and simmer 15 minutes - it takes flavour well and goes rubbery if it "
              "boils hard, so add it late to a curry."),
    "lettuce": (("lettuce", "lettuces", "salad leaves"),
                "Lettuce: torn into a bowl with oil, vinegar and salt, or braised in a covered "
                "pan with a knob of butter for 5 minutes."),
    "spring greens": (("spring greens", "spring green", "collard greens", "collard"),
                      "Spring greens: shredded and fried hot for 4 minutes with garlic and a "
                      "splash of soy, or braised 10 minutes under a lid with butter - the stalk "
                      "should give and the leaf stay green."),
    "rice noodle": (("rice noodles", "rice noodle"),
                    "Rice noodles: soaked in boiling water for 5 minutes, then tossed hot with "
                    "prawns, tofu or egg, soy sauce and whatever vegetables you have - they "
                    "need no boiling, and they go gluey if they stand in water."),
    "butter bean": (("butter beans", "butter bean"),
                    "Butter beans are already cooked, so warm them through: mashed with garlic, "
                    "lemon and olive oil onto toast, or in a tomato sauce with paprika for 10 "
                    "minutes."),
    "cabbage": (("cabbage",),
                "Shredded cabbage fried hot for 7 minutes with chopped bacon or smoked sausage, "
                "then stirred through pasta or mash, is a dinner rather than a side."),
    "pea": (("peas", "pea", "frozen peas"),
            "Pea soup: frozen peas and a chopped onion simmered in stock for 10 minutes, then "
            "blended, with a drop of mint."),
    "leek": (("leek", "leeks"),
             "Leek and potato soup: sliced leeks softened in butter for 10 minutes, diced potato "
             "and stock added and simmered 15 minutes, then blended or mashed rough."),
    "swede": (("swede", "swedes", "turnip", "turnips", "neeps"),
              "Mash it: cubed swede boiled 20 minutes, drained well and mashed with butter, salt "
              "and plenty of black pepper, alongside sausages."),
    "parsnip": (("parsnip", "parsnips"),
                "Roast parsnips: quartered, tossed in oil and honey, 35 minutes at 200C (180C "
                "fan) until the edges caramelise."),
    "beetroot": (("beetroot", "beets"),
                 "Roast beetroot whole and unpeeled at 200C (180C fan) for an hour, then rub the skin "
                 "off and dress the wedges with oil, vinegar and salt."),
    "kale": (("kale", "cavolo nero"),
             "Massage shredded kale with oil, lemon and salt for a minute, then roast it at "
             "200C (180C fan) for 8 minutes until the edges crisp."),
    "sprouts": (("sprouts", "brussels sprouts", "brussel sprouts"),
                "Halve the sprouts and fry them cut side down in butter for 8 minutes without moving "
                "them, then add a splash of water and a lid for 3 minutes so they steam through."),
    "celeriac": (("celeriac",),
                 "Celeriac mash or remoulade: boil and mash it with potato and butter, or shred "
                 "it raw with mayonnaise, mustard and lemon."),
    "squash": (("squash", "pumpkin"),
               "Roast squash cubes with oil, chilli and garlic for 30 minutes at 200C (180C fan), "
               "then toss them through pasta with parmesan, or blend with stock for soup."),
    "celery": (("celery",),
               "Braise celery: sticks softened in butter for 5 minutes, then stock and a lid for 20 "
               "minutes, and it goes sweet; it is also the base of every soup and stew."),
    "fennel": (("fennel",),
               "Fennel: slice it thin and roast at 200C (180C fan) for 25 minutes with oil and salt "
               "until the edges caramelise, or shave it raw with lemon and parmesan."),
    "aubergine": (("aubergine", "aubergines", "eggplant"),
                  "Salt sliced aubergine for 20 minutes, then fry in plenty of oil until soft "
                  "and add it to a tomato sauce, or roast halves at 200C for 30 minutes."),
    "cucumber": (("cucumber", "cucumbers"),
                 "Smash the cucumber, salt it for 10 minutes, then dress it with vinegar, garlic and "
                 "a spoon of chilli oil."),
    "coconut milk": (("coconut", "coconut milk", "coconut cream"),
                     "Coconut curry: fry a spoon of curry paste, add the coconut milk you have "
                     "(half a tin is plenty for two) and whatever veg you have, and simmer it 10 "
                     "minutes; serve it with rice."),
    "sweetcorn": (("sweetcorn", "corn"),
                  "Sweetcorn fritters: a tin of drained corn, 2 eggs and 3 spoons of flour, "
                  "fried 2 minutes a side."),
    "bread": (("bread", "toast", "rolls", "baguette"),
              "Eggy bread: bread soaked in beaten egg and fried in butter for 2 minutes a side."),
    "tortilla": (("tortilla", "tortillas", "wrap", "wraps"),
                 "Quesadilla: grated cheese and anything else you have between two tortillas, "
                 "fried dry for 2 minutes a side."),
    "flour": (("flour", "plain flour", "self raising flour"),
              "Pancakes: 100g flour, 2 eggs and 300ml milk whisked and rested 20 minutes, then a "
              "minute a side in a hot buttered pan."),
    "milk": (("milk",),
             "A white sauce: butter and flour cooked a minute, then milk whisked in and simmered "
             "5 minutes, for pasta or cauliflower cheese."),
    "cream": (("cream", "double cream", "single cream", "creme fraiche", "soured cream"),
              "Splash cream into a hot pan with garlic and grated parmesan, let it bubble a "
              "minute and toss it with pasta: a sauce in 10 minutes."),
    "butter": (("butter",),
               "Shortbread: 100g butter rubbed into 150g flour and 50g sugar, pressed into a tin "
               "and baked at 160C (140C fan) for 25 minutes."),
    "yoghurt": (("yoghurt", "yogurt", "greek yoghurt"),
                "A quick raita or breakfast bowl: yoghurt with fruit, honey and oats, or grated "
                "cucumber and mint alongside a curry."),
    "lemon": (("lemon", "lemons"),
              "Lemon and garlic chicken, or just a squeeze over the finished dish: lemon at the "
              "end lifts almost anything."),
    "banana": (("banana", "bananas", "overripe bananas"),
               "Banana pancakes: 2 ripe bananas mashed with 2 eggs and a spoon of flour, fried in "
               "butter 2 minutes a side."),
    "apple": (("apple", "apples"),
              "Stewed apple: sliced with a spoon of sugar and a splash of water, 10 minutes, "
              "then over porridge or yoghurt."),
    "oats": (("oats", "porridge oats", "oatmeal"),
             "Porridge: 50g oats to 250ml milk with a pinch of salt, stirred for 5 minutes, with "
             "banana or grated apple in it."),
    # --- the rest of the shop -------------------------------------------------------------
    # Forty ingredients people are given, inherit, or buy once and then stare at. Each one got
    # the search hedge ("what can I make with duck" was a shrug), and the pantry is the one table
    # every "what can I cook with X" line ends in, so these rows are the breadth of that table
    # rather than forty new answers to forty questions.
    "duck": (("duck", "duck breast", "duck breasts", "duck legs", "duck leg"),
             "Duck breast: score the skin, lay it skin down in a cold dry pan on a low heat for "
             "12 to 15 minutes to let the fat run out, then 3 minutes skin up and rest 5. Legs "
             "want 2 hours at 160C (140C fan) until the meat pulls off the bone."),
    "fig": (("fig", "figs"),
            "Figs: halve them, dot with honey and bake 15 minutes at 200C (180C fan) until they "
            "slump, then eat them with yoghurt or blue cheese, or lay them beside roast duck."),
    "venison": (("venison", "venison steak", "venison haunch", "venison shoulder"),
                "Venison is lean, so cook it fast and leave it pink: 3 minutes a side in a hot pan "
                "for a haunch steak, then rest it 5 minutes. The shoulder wants 2 hours at 150C "
                "(130C fan) with red wine and juniper."),
    "rabbit": (("rabbit", "rabbit leg", "rabbit legs"),
               "Rabbit: brown the joints, then braise them an hour with mustard, stock and thyme, "
               "or treat the legs like chicken thighs in a white wine stew."),
    "squid": (("squid", "calamari"),
              "Squid is 2 minutes or 40: score and slice the tubes, then either fry hard for 2 "
              "minutes with garlic, chilli and lemon, or stew the rings 40 minutes with tomatoes "
              "until they are tender. Anything in between is rubber."),
    "mussel": (("mussel", "mussels"),
               "Mussels: rinse them and pull the beards off, then steam 4 minutes in a covered pan "
               "with white wine, garlic and parsley, and throw away any that stay shut."),
    "clam": (("clam", "clams"),
             "Clams: soak them an hour in salty water so they spit out sand, then steam 4 minutes "
             "with wine, garlic and chilli. Ones that are open before cooking or shut after it go "
             "in the bin."),
    "scallop": (("scallop", "scallops"),
                "Scallops: pat them very dry, sear 90 seconds a side in a hot pan and turn them "
                "once. Wet scallops steam instead of browning, and the drying is the whole trick."),
    "crab": (("crab", "crab meat"),
             "Crab: the white meat on toast with lemon and a little mayonnaise, the brown meat "
             "warmed with chilli and garlic and stirred through pasta. Either needs nothing else."),
    "artichoke": (("artichoke", "artichokes", "globe artichoke", "jerusalem artichoke",
                   "jerusalem artichokes"),
                  "Globe artichokes: boil 25 to 35 minutes until a leaf pulls away, then dip the "
                  "leaves in butter and scrape the choke off for the heart. Jarred hearts are "
                  "faster: halve them, fry them in oil and garlic and toss them with pasta."),
    "radish": (("radish", "radishes"),
               "Radishes: sliced raw with butter and salt, or roasted 20 minutes at 200C (180C "
               "fan), which takes the heat out of them and leaves them sweet."),
    "okra": (("okra", "lady fingers"),
             "Okra goes slimy when it stews slowly, so dry it well and fry it whole and fast in "
             "hot oil, or roast it 15 minutes at 200C (180C fan) with oil, salt and paprika."),
    "plantain": (("plantain", "plantains"),
                 "Plantain: green ones are savoury, so slice and fry them 3 minutes a side like "
                 "chips with salt; black ones are sweet, so fry thicker coins and eat them with "
                 "ice cream."),
    "rhubarb": (("rhubarb",),
                "Rhubarb: chop it with sugar and orange zest and bake 20 minutes at 180C (160C "
                "fan) - it makes its own liquid, so add no water - then spoon it over yoghurt or "
                "porridge, or under a crumble."),
    # Soft fruit is asked for by the punnet - "what can i make with strawberries" - and the dish
    # table had nothing under any of the four, so the line got the search hedge. A punnet of
    # soft fruit is eaten as much as it is cooked, so those go in the answers too.
    # A bag of herbs is bought as often as a punnet of fruit and had no answer at all, so
    # "what can i make with a bag of parsley" was a hedge while every vegetable had a card.
    "soft herbs": (("parsley", "basil", "coriander", "cilantro", "dill", "mint", "chives",
                    "tarragon", "herbs", "soft herbs", "fresh herbs"),
                   "Soft herbs - parsley, basil, coriander, dill, mint, chives - want the end of "
                   "the cooking, not the start: chop them and stir them in off the heat. A "
                   "handful blitzed with oil, lemon and garlic is a green sauce for fish, chicken "
                   "or new potatoes, and the stems go in at the start of a soup."),
    # The woody herbs had no row at all while every soft one did, so "i have too much thyme",
    # "what can i do with rosemary" and "i have a rosemary bush what can i cook" got a read-back
    # ("Noted: you have too much thyme.") or the ten-minute list. They are used differently from
    # the soft ones - they go in at the start and stand up to heat - so they get their own answer.
    "woody herbs": (("rosemary", "thyme", "sage", "bay", "bay leaf", "bay leaves", "oregano",
                     "woody herbs", "hard herbs"),
                    "Woody herbs - rosemary, thyme, sage, bay - go in at the start, because heat "
                    "is what opens them up: strip the leaves into the oil with potatoes, lamb, "
                    "chicken or a tray of vegetables, or push a sprig into a joint before it "
                    "roasts. They are strong, so a sprig or a teaspoon of chopped leaves is "
                    "plenty, and a bay leaf in rice or a stew is the cheapest way to use one."),
    "strawberry": (("strawberry", "strawberries"),
                   "Strawberries: halved with a spoon of sugar and left 10 minutes to draw their "
                   "juice, over yoghurt, meringue or ice cream; or sliced with basil and a splash "
                   "of balsamic as a salad."),
    "raspberry": (("raspberry", "raspberries"),
                  "Raspberries: crushed with a fork and a spoon of sugar over porridge or yogurt, "
                  "folded through whipped cream as a fool, or baked under a crumble."),
    "blueberry": ((("blueberry", "blueberries")),
                  "Blueberries: stirred into pancake or muffin batter, or simmered 5 minutes with "
                  "a spoon of sugar and a squeeze of lemon for a compote that keeps a week."),
    "blackberry": (("blackberry", "blackberries"),
                   "Blackberries: simmered 8 minutes with sugar and a chopped apple, which is what "
                   "sets them, then over yoghurt or under a crumble."),
    "gooseberry": (("gooseberry", "gooseberries"),
                   "Gooseberries: stew 8 minutes with sugar and a splash of elderflower, which is "
                   "what takes the sourness, or bake them under a crumble; they also cut through "
                   "mackerel or pork."),
    "blackcurrant": (("blackcurrant", "blackcurrants"),
                     "Blackcurrants: simmer 8 minutes with sugar and a splash of water into a "
                     "compote for yoghurt, or cook them down into a sharp sauce for duck or game."),
    "cranberry": (("cranberry", "cranberries"),
                  "Cranberries: simmer 10 minutes with sugar, orange zest and a splash of water "
                  "until they burst, and that sauce keeps a week in the fridge."),
    "apricot": (("apricot", "apricots", "dried apricots"),
                "Apricots: halve them, dot with butter and sugar and bake 20 minutes at 180C "
                "(160C fan); dried ones poach in 10 minutes in water, sugar and a strip of orange "
                "peel."),
    "nectarine": (("nectarine", "nectarines"),
                  "Nectarines: halve them, grill cut side up 5 minutes with a little butter and "
                  "sugar, or slice them raw into a salad with mozzarella and basil."),
    "brie": (("brie", "camembert"),
             "Brie or camembert: bake a whole one at 180C (160C fan) for 15 minutes, scored with "
             "garlic and thyme, and dip bread or roasted vegetables into it."),
    "stilton": (("stilton", "blue cheese", "gorgonzola", "roquefort"),
                "Blue cheese: crumble it over a pear and walnut salad, or stir it into a soup off "
                "the heat, where it melts into something richer than cream."),
    "ricotta": (("ricotta",),
                "Ricotta: whisk it with lemon zest and honey onto toast, fold it through spinach "
                "and pasta, or use it as a cheesecake or stuffed-pasta filling."),
    "mascarpone": (("mascarpone",),
                   "Mascarpone: fold it with a little icing sugar and lemon over fruit, or beat it "
                   "into a risotto at the end instead of butter and parmesan."),
    "tempeh": (("tempeh",),
               "Tempeh: slice it, simmer 5 minutes to take the bitterness off, then fry it 3 "
               "minutes a side and glaze it with soy, honey and lime."),
    "seitan": (("seitan",),
               "Seitan: slice and fry it hard for 3 minutes a side for a crisp edge, then finish "
               "it in any sauce - soy, ginger and garlic, or tomato and paprika."),
    "harissa": (("harissa", "harissa paste"),
                "Harissa is chilli, garlic, cumin and pepper already balanced: stir a spoon into "
                "yoghurt for a dip, or toss it with oil and root vegetables before roasting."),
    "tahini": (("tahini",),
               "Tahini: whisk it with lemon juice and cold water and it loosens and thickens into "
               "a dressing, or spoon it over roast cauliflower with pomegranate."),
    "miso": (("miso", "miso paste"),
             "Miso: stir a spoon into hot but not boiling water with tofu and spring onion for "
             "soup, or mix it with butter and honey as a glaze for salmon or aubergine."),
    "kimchi": (("kimchi",),
               "Kimchi: fry it 3 minutes in a hot pan, juice and all, then stir it through rice "
               "with a fried egg, or pile it cold onto a grilled cheese."),
    "sauerkraut": (("sauerkraut",),
                   "Sauerkraut: drain it and warm it 5 minutes in butter with caraway, which is the "
                   "version that goes with sausage or a baked potato. Raw, it is a sharp salad."),
    "polenta": (("polenta",),
                "Polenta: 1 part to 4 of boiling stock, whisked in and stirred 5 minutes, then "
                "eaten soft with a ragù, or spread flat to cool, cut into chips and fried."),
    "bulgur": (("bulgur", "bulgar wheat", "burghul"),
               "Bulgur: pour double its volume of boiling stock over it, lid on for 15 minutes, "
               "then fork it through with lemon, parsley and tomato."),
    "barley": (("barley", "pearl barley"),
               "Pearl barley: simmer 30 to 40 minutes in stock, then stir it through a stew or a "
               "mushroom soup, where it thickens as well as fills."),
    "quinoa": (("quinoa",),
               "Quinoa: rinse it, simmer 15 minutes in twice its water until the grains uncurl, "
               "then drain it and fork it through with oil, lemon and herbs."),
    "gnocchi": (("gnocchi",),
                "Gnocchi: boil them 2 minutes until they float, then fry them 3 more in butter so "
                "they crisp, and toss them with sage, tomato or blue cheese."),
    "filo": (("filo", "phyllo", "filo pastry", "phyllo pastry", "fillo"),
             "Filo: brush each sheet with butter and stack 4 or 5, then bake 20 minutes at 200C "
             "(180C fan) with spinach and feta inside, or scrunch it dry over a fruit tart."),
    "anchovy": (("anchovy", "anchovies", "anchovy fillets"),
                "Anchovies: melt two or three fillets in oil with garlic and chilli for 2 minutes "
                "and toss them through pasta with breadcrumbs, or lay them over lamb before "
                "roasting."),
    "sardine": (("sardine", "sardines", "tinned sardines"),
                "Sardines: mash tinned ones into toast with lemon and chilli, or grill fresh ones 3 "
                "minutes a side and eat them with bread and a sharp salad."),
    "mackerel": (("mackerel",),
                 "Mackerel: score and salt it, then grill or fry it 4 minutes skin side down. It "
                 "is rich, so lemon, horseradish or gooseberry is what cuts through it."),
    "hake": (("hake",),
             "Hake: roast a thick fillet 12 minutes at 200C (180C fan) with oil and lemon, or fry "
             "it 3 minutes a side. It flakes into big white pieces that hold together in a stew."),
    "monkfish": (("monkfish",),
                 "Monkfish: cut it into chunks, fry 4 minutes with garlic and paprika, then add "
                 "tomatoes and chickpeas and cook 10 minutes more - it stays firm like a lobster "
                 "tail."),
    "pheasant": (("pheasant", "partridge", "grouse", "game bird", "game birds"),
                 "Pheasant and partridge are lean and dry out fast: brown the birds in a pan, then "
                 "roast 25 to 35 minutes at 190C (170C fan) with bacon over the breast, and rest "
                 "them 10 minutes. A casserole with stock, wine and bacon suits them better than "
                 "a hot oven."),
    "trout": (("trout", "rainbow trout"),
              "Trout: whole, stuffed with lemon and thyme, in a hot oven for 20 minutes; fillets "
              "pan-fried 3 minutes skin side down for crackling skin, then 1 minute the other "
              "side."),
    "bass": (("sea bass", "seabass", "bass fillet"),
             "Sea bass: score the skin, salt it, and fry it skin side down 4 minutes then 1 minute "
             "the other way. It needs nothing but lemon and something green."),
    "bream": (("bream", "sea bream"),
              "Sea bream: whole, stuffed with fennel and lemon, roasted 25 minutes at 200C (180C "
              "fan), or fillets fried 3 minutes a side. The skin crisps and lifts off in one "
              "piece when it is ready."),
    "tilapia": (("tilapia",),
                "Tilapia: it is mild and soft, so fry the fillets 2 minutes a side in butter and "
                "finish with lemon, or steam them with ginger and soy for 8 minutes."),
    "salami": (("salami", "pepperoni", "salami slices"),
               "Salami: fried 2 minutes, it flavours a whole pan of pasta with its fat and pepper, "
               "or lay slices on a pizza for the last 5 minutes so they crisp at the edges."),
    "prosciutto": (("prosciutto", "parma ham", "serrano ham", "pancetta slices"),
                   "Prosciutto needs nothing but good bread and butter, but a slice wrapped round "
                   "a chicken breast or a fish fillet and roasted 20 minutes bastes the meat as it "
                   "cooks."),
    "black pudding": (("black pudding", "white pudding", "haggis"),
                      "Black pudding: fry or grill it in 1cm slices 2 minutes a side, or crumble it "
                      "into a pan with potatoes and apple for a hash. Haggis is boiled or "
                      "microwaved 45 minutes, or fried in slices the same way."),
    "watercress": (("watercress",),
                   "Watercress: soup in 10 minutes - potato and onion simmered soft, watercress in "
                   "for the last 2 minutes, then blitzed - or a salad with orange and walnuts, "
                   "since its pepper needs something sweet."),
    "asparagus": (("asparagus", "asparagus spears"),
                  "Asparagus: roast at 200C (180C fan) for 12 minutes with oil and salt, or boil "
                  "the spears 4 minutes. Either way they want only parmesan or a poached egg on "
                  "top."),
    "samphire": (("samphire", "marsh samphire"),
                 "Samphire: boil it 2 minutes, then toss it with butter and lemon and no salt - it "
                 "is already salty - and eat it with fish."),
    "mango": (("mango", "mangoes"),
              "Mango: a ripe one cubed into yoghurt or a salad with chilli and lime, an underripe "
              "one grated into a slaw. Standing a hard one in a paper bag for two days ripens it "
              "faster than the fridge, which stops it."),
    "avocado": (("avocado", "avocados", "avocado pear"),
                "Avocado: on toast with lemon and salt, or in a salad with tomato and red onion. "
                "It needs an acid and salt more than anything else, and it ripens in a paper bag "
                "beside a banana."),
    "papaya": (("papaya", "pawpaw", "guava", "persimmon"),
               "Papaya, guava and persimmon are all eat-it-raw fruit: halve them, scoop or slice, "
               "and add lime - papaya with lime and chilli, guava in a smoothie, persimmon sliced "
               "into yoghurt or a salad."),
    "passionfruit": (("passionfruit", "passion fruit"),
                     "Passionfruit: halve it and spoon the pulp over yoghurt, meringue or "
                     "cheesecake, or stir it into a dressing for a leafy salad."),
    "pomegranate": (("pomegranate", "pomegranate seeds"),
                    "Pomegranate: cut it in half and tap the back with a spoon over a bowl to free "
                    "the seeds, then scatter them over a salad or a lamb dish for sharpness and "
                    "crunch."),
    "plum": (("plum", "plums", "greengage", "greengages", "damson", "damsons"),
             "Plums, greengages and damsons: halve them, dot with sugar and bake 20 minutes at "
             "180C (160C fan) with a splash of water, then serve with yoghurt or under a crumble. "
             "Damsons need more sugar than the others."),
    "walnut": (("walnut", "walnuts"),
               "Walnuts: toasted 5 minutes in a dry pan, they lift a pear, beetroot or blue cheese "
               "salad; ground with garlic, bread and oil they become a sauce for pasta."),
    "almond": (("almond", "almonds", "ground almonds", "flaked almonds"),
               "Almonds: toasted 5 minutes, flaked ones scattered over a rice or a green salad; "
               "ground almonds thicken a sauce or stand in for some of the flour in a cake."),
    "cashew": (("cashew", "cashews"),
               "Cashews: roasted 10 minutes at 180C (160C fan) with salt and paprika for a snack, "
               "or blitzed with water into a cream for curries and soups."),
    "pistachio": (("pistachio", "pistachios"),
                  "Pistachios: chopped into couscous or a rice salad, or crushed over yoghurt and "
                  "honey - the green is half the point."),
    "hazelnut": (("hazelnut", "hazelnuts"),
                 "Hazelnuts: toasted 8 minutes at 180C (160C fan) and rubbed in a cloth to lose "
                 "their skins, then chopped into a salad or a chocolate pudding."),
    "chestnut": (("chestnut", "chestnuts"),
                 "Chestnuts: cooked ones crumble into a sprout and bacon dish, or simmer 15 "
                 "minutes in milk and blitz into soup, which is sweet enough without cream."),
    "pine nut": (("pine nut", "pine nuts", "pine kernels"),
                 "Pine nuts: toasted 3 minutes in a dry pan and stirred through a salad, or "
                 "browned in butter with sage and spooned over pasta. They burn in seconds, so "
                 "watch them."),
    "nut": (("nut", "nuts", "mixed nuts"),
            "Nuts: toasted 5 to 8 minutes in a dry pan with salt, they finish a salad, a rice or a "
            "bowl of yoghurt and honey. Chopped and fried with breadcrumbs they make a crust for "
            "pasta."),
    "pecan": (("pecan", "pecans"),
              "Pecans: toasted 8 minutes, chopped into a sweet potato dish with maple syrup, or "
              "baked into a tart with brown sugar and butter."),
    "cornmeal": (("cornmeal", "corn meal", "semolina", "semolina flour"),
                 "Cornmeal and semolina: dusted over a tray they stop bread and pizza sticking, "
                 "and semolina cooked with hot milk and sugar for 5 minutes is a pudding."),
    "condensed milk": (("condensed milk",),
                       "Condensed milk is sweet and thick: a tin boiled under water for 3 hours "
                       "becomes caramel for a banoffee, and a spoon sweetens coffee."),
    # The other tin, and not the same tin: "what can i make with evaporated milk" asked for a
    # dish, and the sweet one's caramel is not it.
    "evaporated milk": (("evaporated milk",),
                        "Evaporated milk: stirred into a white sauce it makes macaroni cheese or "
                        "a gratin without any cream, and it goes in a curry or a rice pudding "
                        "the same way."),
    "pork belly": (("pork belly", "belly pork", "pork ribs", "ribs", "spare ribs",
                    "short ribs"),
                   "Pork belly: score the skin, salt it, roast 30 minutes at 220C (200C fan) then "
                   "1 hour at 170C (150C fan) for crackling over soft meat. Ribs want 2 hours "
                   "wrapped in foil at 150C (130C fan), then 15 minutes uncovered and glazed at "
                   "220C (200C fan)."),
    "brisket": (("brisket", "beef shin", "shin beef", "stewing steak", "beef stewing steak"),
                "Brisket and shin need time, not attention: brown the meat, then 3 hours at 150C "
                "(130C fan) covered with onions, stock and a splash of vinegar, until it pulls "
                "apart."),
    "spring onion": (("spring onion", "spring onions", "scallion", "scallions"),
                     "Spring onions: sliced raw over rice, soup or a baked potato, or softened 1 "
                     "minute in a hot pan with ginger before the rest goes in."),
    "smoked haddock": (("smoked haddock", "smoked fish"),
                       "Smoked haddock: poached in milk for 5 minutes, then flaked back into that "
                       "milk under mashed potato for a fish pie - undyed is the milder one."),
    "bagel": (("bagel", "bagels"),
              "Bagels: halved and toasted, then tomato and cheese under the grill for 5 minutes "
              "for a bagel pizza, or just cream cheese and black pepper."),
    "maple syrup": (("maple syrup",),
                    "Maple syrup: spooned over pancakes, porridge or yogurt, or brushed onto "
                    "carrots, bacon or salmon before they go under the grill."),
    "chocolate": (("chocolate", "dark chocolate", "milk chocolate", "chocolate chips"),
                  "Chocolate: melted with butter and stirred into beaten eggs for a mousse, or "
                  "baked into brownies - 150g chocolate, 100g butter, 2 eggs and 100g sugar, 25 "
                  "minutes at 170C (150C fan)."),
    "spelt": (("spelt", "freekeh", "farro", "rye grain"),
              "Spelt, freekeh and farro cook like rice but chewier: simmer 25 to 30 minutes in "
              "salted water, drain, then toss with oil, lemon and roasted vegetables."),
    "yam": (("yam", "yams", "cassava"),
            "Yam and cassava: peel them, boil 20 minutes until a knife goes in easily, then mash "
            "with butter, or fry boiled chunks in oil for a crisp outside."),
    "rhubarb fool": (("elderflower", "elderflower cordial"),
                     "Elderflower cordial is the shortcut for fruit: a splash in stewed gooseberry, "
                     "rhubarb or apple takes the sourness and costs nothing."),
    # The odds and ends a kitchen actually has left over: a jar with a spoonful in it, the other
    # half of the pastry, the chips nobody ate. They are ingredients like any other, so they are
    # rows in this table rather than a second table of their own, and the idea is what to make
    # with the part that is left.
    "pesto": (("pesto", "green pesto", "red pesto", "jar of pesto"),
              "Stir a spoon of pesto through hot pasta with a splash of the cooking water, spread "
              "it over chicken or fish before baking, or loosen it with oil and lemon as a "
              "dressing for tomatoes or mozzarella."),
    "jam": (("jam", "marmalade", "preserve", "preserves", "fruit jam"),
            "Jam or marmalade going spare: spoon it over porridge or yoghurt, warm it with a "
            "splash of water into a sauce for pancakes or a sponge, or glaze a roast chicken or "
            "gammon with it for the last 15 minutes."),
    "gravy": (("gravy", "leftover gravy", "gravy left"),
              "Leftover gravy: freeze it in an ice cube tray for the next roast, or loosen it "
              "with stock and use it as the base of a stew, a pie filling or a sauce for "
              "sausages and mash."),
    "pastry": (("pastry", "puff pastry", "shortcrust", "shortcrust pastry", "leftover pastry"),
               "Pastry going spare: cut it into strips, twist them with grated cheese and bake 12 "
               "minutes at 200C (180C fan), or line a tin and fill it with whatever is in the "
               "fridge for a tart. It also freezes fine."),
    "chips": (("chips", "leftover chips", "fries", "french fries"),
              "Leftover chips: fry them again in a hot pan with a little oil for 3 minutes to "
              "crisp them up, or chop them into a tortilla or frittata with eggs and finish it "
              "under the grill."),
    "cake": (("cake", "leftover cake", "sponge cake"),
             "Cake going stale: crumble it into a bowl with custard, or with fruit and cream for "
             "a trifle, and slices toasted in a hot pan with butter come back crisp. It also "
             "freezes well, wrapped whole."),
    "egg white": (("egg white", "egg whites", "leftover egg whites"),
                  "Leftover egg whites: whisk them stiff with 50g of sugar per white and bake "
                  "meringues at 110C (100C fan) for an hour, or use them to bind a frittata or "
                  "to coat fish before breadcrumbs. They freeze for months in a tub."),
    "runner bean": (("runner bean", "runner beans"),
                    "Runner beans: top and tail them, slice them thinly and boil 4 minutes, then "
                    "toss with butter and a little garlic - the older ones are better shredded "
                    "into a curry or a chutney than eaten on the side."),
    # Made things that are left over in the fridge rather than raw ingredients, the same way a
    # stale cake or a half jar of pesto is: the row is what to do with the rest of it. The aliases
    # are the phrases a leftover line actually says, so a bare "curry" or "stuffing" is not a
    # pantry thing and "how long do you simmer a ragu" is left to the dish table.
    "marrow": (("marrow", "vegetable marrow", "marrows"),
               "Marrow is mild and watery, so it wants flavour and heat: halve it, scoop out the "
               "seeds, stuff it with mince and rice and bake 45 minutes at 190C (170C fan), or "
               "cube it into a curry. Grated, salted for 20 minutes and squeezed dry, it goes into "
               "a chutney with vinegar, sugar and ginger."),
    "buttermilk": (("buttermilk", "leftover buttermilk"),
                   "Buttermilk is made for soda bread and pancakes: 284ml with 250g flour and a "
                   "teaspoon each of bread soda and salt makes a loaf that needs no rising, and a "
                   "pancake batter likes it thinned with it. It keeps about a week in the fridge, "
                   "and it tenderises chicken in a marinade."),
    "hot cross bun": (("hot cross bun", "hot cross buns", "leftover buns"),
                      "Hot cross buns going stale: halve and toast them buttered, or bake them in a "
                      "bread and butter pudding - buttered halves, a custard of 2 eggs and 300ml "
                      "milk, 25 minutes at 170C (150C fan)."),
    "stuffing": (("stuffing", "sage and onion", "sage and onion stuffing", "leftover stuffing"),
                 "Leftover stuffing: press it into a tray, cut it into squares and roast 15 "
                 "minutes at 200C (180C fan) for crisp edges, roll it into balls and fry them, or "
                 "crumble it over a tray of roast vegetables for the last 10 minutes."),
    "porridge": (("porridge", "leftover porridge", "cold porridge"),
                 "Cold porridge sets solid, so loosen it with a good splash of milk and reheat it "
                 "gently in a pan, or beat an egg into it and fry spoonfuls in butter for oat "
                 "fritters that take jam."),
    "bolognese": (("bolognese", "bolognaise", "ragu", "ragù", "leftover bolognese"),
                  "Leftover bolognese: layer it with pasta and white sauce and bake 25 minutes at "
                  "200C (180C fan), spoon it hot over a jacket potato, or thin it with stock and a "
                  "tin of beans into a soup."),
    "curry": (("leftover curry", "curry sauce", "leftover curry sauce"),
              "Leftover curry: the spice deepens overnight, so reheat it once until piping hot "
              "and eat it with rice, or put it in a baking dish under mash for a curry pie. Do not "
              "reheat it a second time."),}

DISHES = (
    {"id": "egg-potato-hash",
     "uses": ("potato", "egg"),
     "cooked": ("potato",),
     "text": "A potato hash: fry diced potatoes with an onion in hot oil for 15 minutes until "
             "crisp, then crack the eggs in and put a lid on for 3 minutes. Cheese over the top "
             "if there is any, and the yolk does the sauce."},
    {"id": "mince-cabbage",
     "uses": ("mince", "cabbage"),
     "text": "Fry the mince hard with a chopped onion until it browns, then add shredded cabbage, "
             "a splash of soy sauce and a little stock and put a lid on for 8 minutes. Cheap, "
             "filling, and it takes about 20 minutes."},
    {"id": "mince-rice",
     "uses": ("mince", "rice"),
     "text": "Mince and rice in 20 minutes: brown the mince hard, add a chopped onion and a tin "
             "of tomatoes or baked beans, season with Worcestershire sauce and soy, and simmer "
             "while the rice cooks."},
    {"id": "aubergine-pasta",
     "uses": ("aubergine", "pasta"),
     "text": "Aubergine pasta: fry cubed aubergine in plenty of olive oil for 10 minutes until "
             "soft, add garlic and a tin of tomatoes, simmer 10 minutes and toss with the pasta."},
    {"id": "chicken-noodles",
     "uses": ("chicken", "noodle"),
     "text": "Chicken noodles: fry sliced chicken in a hot pan for 6 minutes, add garlic, ginger "
             "and any vegetables, then the cooked noodles, soy sauce and a squeeze of lime. "
             "Twenty minutes, one pan."},
    {"id": "tofu-noodles",
     "uses": ("tofu", "noodle"),
     "text": "Crisp tofu noodles: fry cubed tofu until golden, then add cooked noodles, soy "
             "sauce, a spoon of peanut butter or sesame oil and any greens for the last 2 "
             "minutes."},
    {"id": "potato-egg-hash",
     "uses": ("potato", "egg", "cheese"),
     "cooked": ("potato",),
     "text": "A potato hash: fry diced cooked potatoes with onion in hot oil until crisp, crack in "
             "the eggs, then sprinkle the cheese over and put a lid on for 3 minutes. Everything in "
             "one pan, and the runny yolk does the sauce."},
    {"id": "courgette-mushroom-pasta",
     "uses": ("courgette", "mushroom"),
     "text": "Courgette and mushroom pasta: fry sliced mushrooms hard in olive oil until golden, "
             "add the courgette in half-moons for 5 minutes, then toss with pasta, parmesan and a "
             "splash of the pasta water. Plenty of oil, because both soak it up."},
    {"id": "chicken-spinach-cream",
     "uses": ("chicken", "spinach"),
     "text": "Chicken and spinach in one pan: brown strips of chicken for 6 minutes, stir in a "
             "crushed garlic clove and a handful of spinach until it wilts, then add a spoon of "
             "cream cheese or creme fraiche and a splash of the pasta water. Pasta or rice, 20 "
             "minutes, one pan."},
    {"id": "frittata",
     "uses": ("egg", "spinach"),
     "cooked": ("spinach",),
     "text": "A frittata: whisk 6 eggs with a splash of milk, pour them over a pan of wilted "
             "spinach and finish it under the grill for 5 minutes. Cheese on top is worth it and "
             "it's good cold the next day too."},
    {"id": "egg-fried-rice",
     "uses": ("rice", "egg"),
     "cooked": ("rice",),
     "text": "Egg fried rice: fry yesterday's cold rice in a little oil for 3 minutes, push it "
             "aside and scramble an egg in the gap, then stir it together with soy sauce and "
             "peas. Cold rice is the important bit; fresh rice goes gluey."},
    {"id": "cheese-omelette",
     "uses": ("egg", "cheese"),
     "cooked": ("cheese",),
     "text": "A cheese omelette: beat 3 eggs, cook them in butter on a low heat for 2 minutes, "
             "fold the cheese in and slide it onto toast. Low heat is what keeps it soft rather "
             "than rubbery."},
    {"id": "mushroom-omelette",
     "uses": ("egg", "mushroom"),
     "cooked": ("mushroom",),
     "text": "Fry the mushrooms in butter until brown and set them aside, then cook 3 beaten "
             "eggs slowly in the same pan and fold the mushrooms through. Five minutes, and the "
             "mushrooms get colour instead of steaming."},
    {"id": "courgette-frittata",
     "uses": ("egg", "courgette"),
     "text": "Grate the courgette, squeeze the water out, fry it briefly with garlic, then pour "
             "5 beaten eggs over it and finish under the grill for 5 minutes. Salting and "
             "squeezing the courgette stops the dish turning watery."},
    {"id": "ham-omelette",
     "uses": ("egg", "ham"),
     "cooked": ("ham",),
     "text": "A ham omelette: 3 beaten eggs cooked slowly for 2 minutes, the ham laid over one "
             "half and folded across. Cheese in with the ham is good, and it beats a sandwich for "
             "the same effort."},
    {"id": "tomato-pasta",
     "uses": ("pasta", "tomato"),
     "text": "A 15-minute tomato pasta: soften sliced garlic in olive oil, add the tinned "
             "tomatoes and a pinch of salt, and simmer while the pasta cooks. Tear in a few basil "
             "leaves at the end and loosen it with a splash of pasta water so it clings."},
    {"id": "tuna-pasta",
     "uses": ("pasta", "tuna"),
     "text": "Tuna pasta: cook the pasta, then stir the drained tuna through a tin of tomatoes "
             "warmed with garlic, or mix it cold with mayonnaise and sweetcorn for a lunch. Both "
             "take under 15 minutes."},
    {"id": "courgette-pasta",
     "uses": ("pasta", "courgette"),
     "text": "Fry sliced courgette and garlic in plenty of olive oil for 8 minutes, then toss "
             "with the cooked pasta and a handful of parmesan. It thickens into a sauce of its "
             "own, and it needs more oil than you think."},
    {"id": "mushroom-pasta",
     "uses": ("pasta", "mushroom"),
     "text": "Fry the mushrooms hard in butter until they brown, add a splash of cream or a "
             "spoon of cream cheese, and toss with the pasta and plenty of pepper. Mushrooms "
             "need the pan hot or they turn to water."},
    {"id": "bacon-pasta",
     "uses": ("pasta", "bacon"),
     "text": "Bacon pasta: fry chopped bacon with garlic and chilli, then toss it with the cooked "
             "pasta, a beaten egg, a handful of parmesan and a splash of pasta water off the "
             "heat. The heat of the pasta cooks the egg into a sauce."},
    {"id": "mac-cheese",
     "uses": ("pasta", "cheese"),
     "text": "Mac and cheese from scratch: boil the pasta, make a quick sauce with a knob of "
             "butter, a spoon of flour and a splash of milk, melt in the grated cheese and mix. "
             "Twenty minutes, no packet needed."},
    {"id": "pea-pasta",
     "uses": ("pasta", "pea"),
     "text": "Pasta with peas: cook the peas with the pasta for the last 3 minutes, then toss "
             "with butter, parmesan and pepper. A chopped mint leaf is worth adding if you have "
             "one."},
    {"id": "garlic-spaghetti",
     "uses": ("pasta", "garlic"),
     "text": "Aglio e olio: warm 4 sliced garlic cloves and a little chilli in 4 tablespoons of "
             "olive oil until they just colour, then toss with the cooked spaghetti and a splash "
             "of pasta water. Ten minutes, and salt it properly."},
    {"id": "chicken-rice",
     "uses": ("chicken", "rice"),
     "text": "One-pan chicken and rice: brown the chicken thighs in a wide pan, add chopped "
             "onion and the rice, pour over twice the rice's volume of stock and simmer covered "
             "for 20 minutes. Let it stand 5 minutes off the heat before serving."},
    {"id": "leftover-chicken-rice",
     "uses": ("chicken", "rice"),
     "cooked": ("chicken", "rice"),
     "text": "Chicken fried rice from the leftovers: fry chopped onion and cold rice hard in "
             "oil for 3 minutes, add the shredded cooked chicken for the last minute with soy "
             "sauce and peas. Cold rice straight from the fridge is what keeps it separate, and "
             "nothing gets boiled twice."},
    {"id": "chicken-potato-tray",
     "uses": ("chicken", "potato"),
     "text": "A traybake: halve the potatoes, toss everything with oil, salt and lemon slices, "
             "and roast at 200C (180C fan) for 35 to 40 minutes, skin side up, until the skin is "
             "crisp and the juices run clear. Squeeze the roasted lemon over before serving."},
    {"id": "chickpea-curry",
     "uses": ("chickpea", "tomato"),
     "text": "A quick chickpea curry: fry onion, garlic and curry powder for 5 minutes, add the "
             "tinned tomatoes and chickpeas, and simmer for 15. Spinach or yoghurt stirred in at "
             "the end rounds it off."},
    {"id": "chickpea-spinach",
     "uses": ("chickpea", "spinach"),
     "text": "Chickpeas and spinach: fry onion, garlic, ginger and cumin, add the chickpeas and "
             "a splash of stock, then wilt the spinach through at the end. Ten minutes, and it's "
             "as good cold as hot."},
    {"id": "lentil-soup",
     "uses": ("lentil", "carrot"),
     "text": "Lentil soup: soften chopped onion and carrot in oil, add red lentils, a tin of "
             "tomatoes and stock, and simmer for 25 minutes. Blend it if you like it smooth."},
    {"id": "dhal",
     "uses": ("lentil", "tomato"),
     "text": "Red lentil dhal: simmer the lentils with a tin of tomatoes, garlic, ginger and "
             "cumin in stock for 20 minutes. Finish with a spoon of butter sizzled with more "
             "cumin."},
    {"id": "sausage-potato",
     "uses": ("sausage", "potato"),
     "text": "Sausage and potato traybake: cut the potatoes into wedges, roast them with the "
             "sausages at 200C (180C fan) for 35 minutes. A spoon of mustard and honey over "
             "everything for the last 10 minutes tastes like more than it is."},
    {"id": "sausage-bean",
     "uses": ("sausage", "bean"),
     "text": "Sausage and bean casserole: brown the sausages, soften an onion, add a tin of "
             "beans, a tin of tomatoes and a spoon of paprika, and simmer for 20 minutes. Crusty "
             "bread is the point of it."},
    {"id": "bolognese",
     "uses": ("mince", "tomato"),
     "text": "Mince and tomatoes make a ragù: brown the mince hard, add chopped onion and "
             "garlic, a tin of tomatoes and a splash of stock, and simmer for at least 30 "
             "minutes. It's better the next day and it freezes well."},
    {"id": "cottage-pie",
     "uses": ("mince", "potato"),
     "text": "Cottage pie: brown the mince with onion and carrot, add a tin of tomatoes and a "
             "splash of stock, and simmer 20 minutes. Top with mashed potato and bake at 200C for "
             "25 minutes, with fork marks on top."},
    {"id": "mince-pasta",
     "uses": ("mince", "pasta"),
     "text": "Brown the mince with onion and garlic, add a tin of tomatoes and simmer for 20 "
             "minutes while the pasta cooks. That's a bolognese, and the longer it simmers the "
             "better it gets."},
    {"id": "salmon-potato",
     "uses": ("salmon", "potato"),
     "text": "Roast the potatoes at 200C for 30 minutes, then put the salmon on the tray for the "
             "last 12 minutes. Lemon, salt and a little butter over everything is enough."},
    {"id": "prawn-pasta",
     "uses": ("prawn", "pasta"),
     "text": "Fry garlic and chilli in olive oil, add the prawns for 2 minutes until they turn "
             "pink, then toss with the pasta and a squeeze of lemon. Prawns need barely any "
             "cooking, so they go in at the very end."},
    {"id": "tuna-potato",
     "uses": ("tuna", "potato"),
     "text": "Boil the potatoes, then toss them warm with tuna, olive oil, lemon and chopped "
             "onion or capers. It's a ten-minute dinner and better than it sounds."},
    {"id": "bean-quesadilla",
     "uses": ("bean", "tortilla"),
     "text": "Mash the beans with a little cumin, spread them over half a tortilla, fold it and "
             "fry it dry for 2 minutes each side. Cheese in the middle helps, and salsa or "
             "yoghurt on top finishes it."},
    {"id": "cheese-quesadilla",
     "uses": ("cheese", "tortilla"),
     "text": "Quesadilla: grated cheese and anything else you have between two tortillas, fried "
             "dry for 2 minutes a side. Cut it into wedges and dip it in salsa or yoghurt."},
    {"id": "toastie",
     "uses": ("bread", "cheese"),
     "text": "A cheese toastie in a dry pan with something heavy on top is 5 minutes: butter the "
             "outside, cheese inside, low heat so the middle melts before the bread burns."},
    {"id": "eggy-bread",
     "uses": ("bread", "egg"),
     "text": "Eggy bread: beat an egg with a splash of milk and salt, soak the bread for a few "
             "seconds, and fry it in butter for 2 minutes a side. Ketchup or a squeeze of lemon "
             "cuts the richness."},
    {"id": "pancakes",
     "uses": ("flour", "egg", "milk"),
     "text": "Pancakes: 100g flour, 2 eggs and 300ml milk whisked smooth, rested 20 minutes, then "
             "cooked in a hot buttered pan for a minute a side. The rest is what stops them "
             "tearing."},
    {"id": "shortbread",
     "uses": ("flour", "butter"),
     "text": "Shortbread: rub 100g butter into 150g flour with 50g sugar, press it into a tin and "
             "bake at 160C (140C fan) for 25 to 30 minutes. Three ingredients, and it keeps a "
             "week."},
    {"id": "banana-pancakes",
     "uses": ("banana", "flour"),
     "text": "Mash 2 ripe bananas into 2 eggs and a spoon of flour, and fry small pancakes in "
             "butter for 2 minutes a side. Ripe bananas are the whole point, and they need no "
             "added sugar."},
    {"id": "banana-smoothie",
     "uses": ("banana", "milk"),
     "text": "Blend a ripe banana with a glass of milk and a spoon of oats for a breakfast that "
             "takes a minute. A spoon of peanut butter or yoghurt makes it thicker."},
    {"id": "porridge",
     "uses": ("oats", "milk"),
     "text": "Porridge: 50g oats to 250ml milk, simmered and stirred for 5 minutes with a pinch "
             "of salt. Grated apple or sliced banana in at the start sweetens it without sugar."},
    {"id": "overnight-oats",
     "uses": ("oats", "yoghurt"),
     "text": "Overnight oats: equal parts oats and yoghurt with a splash of milk in a jar, left "
             "in the fridge overnight and topped with fruit in the morning. No cooking, and it "
             "keeps two days."},
    {"id": "apple-crumble",
     "uses": ("apple", "flour", "butter"),
     "text": "Apple crumble: stew sliced apples with a spoon of sugar, rub 100g butter into 150g "
             "flour and 75g sugar for the top, and bake at 190C for 30 minutes. Make double and "
             "freeze one."},
    {"id": "veg-soup",
     "uses": ("carrot", "potato", "onion"),
     "text": "Vegetable soup: soften the onion, add chopped carrot and potato, cover with stock "
             "and simmer for 20 minutes, then blend or leave it chunky. A spoon of cream or "
             "yoghurt at the end makes it feel finished."},
    {"id": "leek-potato-soup",
     "uses": ("leek", "potato"),
     "text": "Leek and potato soup: soften sliced leeks in butter for 10 minutes without colour, "
             "add diced potato and stock to cover, simmer 15 minutes, then mash it rough so it "
             "still has texture. About 30 minutes, and it freezes."},
    {"id": "cabbage-bacon",
     "uses": ("cabbage", "bacon"),
     "text": "Fried cabbage with bacon: cut the bacon into strips and fry it until crisp, then "
             "add shredded cabbage to the fat with a splash of water and a lid for 5 minutes, and "
             "finish with plenty of black pepper. 15 minutes, one pan."},
    {"id": "kale-colcannon",
     "uses": ("kale", "potato"),
     "text": "Colcannon: boil potatoes and mash them with butter and hot milk, then stir through "
             "shredded kale wilted in the same pan for the last 3 minutes. Season hard and make a "
             "well in the middle for more butter."},
    {"id": "root-traybake",
     "uses": ("swede", "carrot"),
     "text": "A root traybake: chunks of swede and carrot with a potato or a parsnip if you have "
             "one, tossed in oil, salt and thyme, spread out in one layer and roasted at 200C "
             "(180C fan) for 40 minutes, turned twice. Sausages laid on top for the last 25 minutes "
             "make it dinner."},
    {"id": "sprouts-pasta",
     "uses": ("sprouts", "pasta"),
     "text": "Sprouts pasta: halve the sprouts and fry them cut side down in butter until browned, "
             "then toss with pasta, lemon zest, parmesan and a splash of the pasta water. Bitter "
             "and savoury, and 20 minutes."},
    {"id": "veg-stirfry",
     "uses": ("pepper", "broccoli"),
     "text": "Stir-fry the pepper and broccoli in a very hot pan for 4 minutes with garlic and "
             "soy sauce. Add noodles or rice, and keep everything moving so it chars rather than "
             "steams."},
    {"id": "cheesy-mash",
     "uses": ("potato", "milk", "butter"),
     "text": "Mash the boiled potatoes with butter and a splash of warm milk and season it well. "
             "Cheese or a spoon of mustard in with it turns mash into the best part of dinner."},
    {"id": "mince-onion",
     "uses": ("mince", "onion"),
     "text": "Cook the onions slowly in oil for 10 minutes until sweet, then turn the heat up, add "
             "the mince and brown it hard before anything wet goes in. A tin of tomatoes makes it a "
             "ragù; kidney beans and chilli powder turn it into chilli, or top it with mash and "
             "grill it for cottage pie."},
    {"id": "onion-omelette",
     "uses": ("egg", "onion"),
     "text": "Soften a sliced onion in butter for 8 minutes, pour over 3 beaten eggs and cook "
             "them slowly, then fold it in half. Slow onions are the difference between a "
             "Spanish-ish tortilla and a plain omelette."},
    {"id": "fried-potato-onion",
     "uses": ("potato", "onion"),
     "text": "Fry cubed parboiled potatoes in hot oil until golden, then add a sliced onion for "
             "the last 5 minutes with salt and plenty of pepper. A fried egg on top makes it "
             "dinner."},
    {"id": "chicken-onion-curry",
     "uses": ("chicken", "onion"),
     "text": "Fry sliced onions for 10 minutes, add garlic, ginger and curry powder, then the "
             "chicken and a splash of stock, and simmer for 20 minutes. Yoghurt or tinned "
             "tomatoes stirred in at the end make the sauce."},
    {"id": "loaded-jacket",
     "uses": ("potato", "cheese"),
     "text": "Jacket potatoes: prick them, 12 to 15 minutes in the microwave then 10 in a hot "
             "oven for the skin, and split them with grated cheese and a spoon of beans or "
             "butter. That's dinner for about 80p a head."},
    {"id": "shakshuka",
     "uses": ("egg", "tomato"),
     "text": "Shakshuka: soften onion and garlic, add a tin of tomatoes and cumin and simmer 10 "
             "minutes, then crack the eggs into hollows, cover and cook for 6 minutes. Bread to "
             "dip is not optional."},
    {"id": "spinach-pasta",
     "uses": ("pasta", "spinach"),
     "text": "Wilt the spinach in a pan with garlic and a knob of butter, then toss it through "
             "the cooked pasta with parmesan and pepper. Ten minutes, and it needs more spinach "
             "than you think once it wilts."},
    {"id": "bean-tomato",
     "uses": ("bean", "tomato"),
     "text": "A quick bean stew: soften onion and garlic, add a tin of beans and a tin of "
             "tomatoes with paprika and cumin, and simmer for 15 minutes. Good on toast, rice or "
             "a jacket potato."},
    {"id": "tuna-rice",
     "uses": ("tuna", "rice"),
     "text": "Tuna rice bowl: warm the rice, then top it with tuna, sweetcorn, a spoon of "
             "mayonnaise or yoghurt and plenty of pepper. Five minutes and no cooking beyond the "
             "rice."},
    {"id": "prawn-rice",
     "uses": ("prawn", "rice"),
     "text": "Fry garlic, chilli and the prawns for 2 minutes, then stir through cooked rice with "
             "soy sauce and a beaten egg. Prawn fried rice in 10 minutes."},
    {"id": "lemon-chicken",
     "uses": ("lemon", "chicken"),
     "text": "Roast the chicken with sliced lemon, garlic and oil at 200C (180C fan) for 35 to "
             "40 minutes, then squeeze the cooked lemon over it. The skin crisps and the juice "
             "does the sauce."},
    {"id": "mash-cheese",
     "uses": ("potato", "cheese"),
     "cooked": ("potato",),
     "text": "Potato cakes from the mash: mix it with the grated cheese and a spoon of flour, "
             "shape flat cakes and fry them in butter for 3 minutes a side until crisp. Or spread "
             "it in a dish, top with cheese and grill it for 5 minutes."},
    {"id": "scrambled-eggs",
     "uses": ("egg", "milk"),
     "text": "Soft scrambled eggs: beat 3 eggs with a splash of milk and a pinch of salt, cook "
             "them in butter on a low heat, stirring, and take them off while still glossy. On "
             "toast in 5 minutes; add 100g of flour and it's a pancake batter instead."},
    {"id": "mushroom-cream",
     "uses": ("mushroom", "cream"),
     "text": "Creamy mushrooms on toast: fry the mushrooms hard in butter until they brown, "
             "pour in a splash of cream and let it bubble for a minute, then spoon it over toast "
             "with plenty of pepper. The hot pan first is what stops them going watery."},
)

RECIPES = (
    (("chilli con carne", "chilli con carni", "chilli", "chili con carne"),
     ("chilli con carne",),
     "About 40 minutes start to finish. Fry 500g mince hard until it browns, then add a chopped onion, two cloves of garlic, a "
     "heaped teaspoon each of cumin and smoked paprika and a tablespoon of tomato puree, and "
     "cook 2 minutes more. Add a tin of tomatoes, a tin of kidney beans and 200ml stock, and "
     "simmer 30 minutes; the long simmer is what makes it taste finished rather than of powder.",
     # "chillies" is not in this list: loose word forms make it veto "chilli con carne" itself
     # a chilli you sow, plant or grow is a gardening question: "when should i plant chillies"
     # was answered with the mince
     ("chilli oil", "chilli sauce", "chilli plant", "chilli pepper", "grow",
      "plant", "planting", "planted", "sow", "sowing", "seed", "seeds", "seedling",
      "seedlings", "garden", "greenhouse")),
    # "spag bol" is what most people call this and it was the one name the row did not hold:
    # "how do i make spag bol" was a shrug and "spaghetti bolognese recipe" was answered with
    # aglio e olio, because the only word the tables knew was spaghetti and spaghetti is pasta.
    (("bolognese", "spaghetti bolognese", "spag bol", "spag bols", "spaggy bol",
      "spagetti bolognese", "ragu", "bolognaise", "bolonaise", "bolagnese"),
     ("bolognese", "ragu", "spag bol"),
     "About 75 minutes start to finish. Soften a chopped onion, carrot and celery in oil for 10 minutes, add 500g mince and brown it "
     "hard, then a glass of milk or wine, a tin of tomatoes and a spoon of tomato puree. Simmer it "
     "45 minutes to an hour, as low as it will go; the long cook is the difference between mince "
     "in tomato and a ragu.",
     ("lasagne", "lasagna", "vegetarian", "vegan", "quorn", "jar")),
    (("macaroni cheese", "mac and cheese", "macaroni and cheese"),
     ("macaroni cheese", "mac and cheese"),
     "About 40 minutes start to finish. Make a roux from 40g butter and 40g flour, whisk in 500ml milk and let it thicken, then stir "
     "in 150g mature cheddar off the heat. Stir it through cooked macaroni, top with more cheese "
     "and breadcrumbs and bake 20 minutes at 200C (180C fan); mustard powder in the sauce is what "
     "stops it tasting flat.",
     ("bake", "leftover", "freeze")),
    (("cauliflower cheese",),
     ("cauliflower cheese",),
     "About 40 minutes start to finish. Boil the florets 5 minutes until just tender, then make the same sauce as macaroni cheese - "
     "40g butter, 40g flour, 500ml milk, 150g cheddar - and pour it over them in a dish. Grate "
     "more cheese on top and bake 20 minutes at 200C (180C fan) until the top blisters; a spoon of "
     "mustard in the sauce stops it tasting of nothing.",
     ("soup", "roast", "freeze")),
    (("stir fry", "stir-fry", "stirfry"),
     ("stir fry",),
     "About 15 minutes start to finish. Cut everything before you start and cook in a single layer over the highest heat: hard "
     "vegetables 2 minutes, then soft ones and the meat, then sauce off the heat. Two batches beat "
     "one full wok, because a crowded pan steams instead of frying, and soy sauce goes in at the "
     "end so it does not burn.",
     ("soggy", "watery", "limp", "sauce", "frozen", "recipe for")),
    (("egg fried rice", "fried rice"),
     ("fried rice",),
     "About 10 minutes start to finish. Use rice cooked and chilled first - day-old is ideal - and fry it hard in a hot pan for 3 "
     "minutes with a little oil before anything else goes in. Push it aside, scramble an egg in "
     "the gap, then mix it through with soy sauce, sesame oil and frozen peas; fresh hot rice "
     "steams and goes gluey.",
     ("microwave", "leftover", "reheat")),
    (("stuffing", "sage and onion"),
     ("stuffing",),
     "About 45 minutes start to finish. Fry a chopped onion soft, then mix it with 100g breadcrumbs, a tablespoon of chopped sage, "
     "50g melted butter and an egg, and season well. Bake it in a buttered dish at 190C (170C fan) "
     "for 30 minutes; cooking it outside the bird keeps it crisp and is the safer way to do it.",
     # "stuff" is the word the matcher reads as stuffing, and it is also how people say things:
     # "how do i sell stuff on ebay" was this dish, so the selling words stand it down.
     ("chicken", "turkey", "cushion", "pillow", "sell", "selling", "sold", "ebay", "vinted",
      "depop", "gumtree", "marketplace", "declutter")),
    (("sprouts", "brussels sprouts", "brussel sprouts"),
     ("sprouts", "brussels"),
     "About 15 minutes start to finish. Trim them and cut a cross in the base, then boil 6 to 8 minutes in salted water until a "
     "knife goes in easily - no longer, or they go grey and sulphury. Halve and fry them in butter "
     "with bacon or chestnuts for the last 3 minutes, which is what turns them from a duty into "
     "something people go back for.",
     ("roast", "mouldy", "grow", "plant", "leftover")),
    # A sandwich and a salad are the two lunches the table had no row for: "how do i make a
    # sandwich" and "how do i make a salad" were both a shrug, and both are made at home more
    # often than anything else in this table. Each row answers the plain question and stands
    # aside for the keeping, the wet and the portion, which have their own answers.
    (("sandwich", "sandwiches", "cheese sandwich", "packed lunch sandwich", "blt",
      "club sandwich", "sandwich filling", "sandwich fillings", "toastie", "toasties",
      "toasted sandwich", "toasted sandwiches"),
     ("sandwich", "ideas", "idea", "decent", "boring", "put in", "goes in", "what goes in",
      "different"),
     "Butter both slices right to the edges before anything else - that is the barrier that "
     "keeps the bread from going soggy - then put the wet things against the butter and the "
     "cheese, ham or egg in the middle, and cut it in half so it holds together. A good "
     "sandwich is about 1cm of filling on bread cut no thicker than that; keep it to two "
     "fillings plus something sharp, and the wet filling goes in a separate box if the "
     "sandwich is built early. Fillings that work: cheddar with apple and mustard, tuna with "
     "celery and mayo drained well, ham with cucumber and piccalilli, or a leftover roast with "
     "something pickled. For a toastie, butter the outside of both slices and press "
     "them in a hot dry pan until they are golden on both sides.",
     ("soggy", "goes soggy", "went soggy", "go soggy", "not soggy", "keep", "keeps", "keeping",
      "store", "stored", "freeze", "frozen", "calories", "healthy", "how many", "how much",
      "wrap", "wraps", "burger", "hot dog", "kids", "party")),
    (("salad", "salads", "green salad", "side salad", "leaf salad", "salad leaves",
      "mixed salad", "lettuce salad"),
     ("salad",),
     "Dry the leaves properly - a tea towel or a spinner - because water is what makes a "
     "dressing slide off them, then dress with 3 parts olive oil to 1 part vinegar and a "
     "teaspoon of mustard, and salt it at the table. A bowl of leaves becomes a dish with one "
     "crunchy thing (toasted seeds, croutons, a handful of nuts) and one sharp thing (pickled "
     "onion, a squeeze of lemon, a little grated cheese), and it wants dressing a minute before "
     "it is eaten, never hours.",
     ("dressing", "dressings", "vinaigrette", "keep", "keeps", "keeping", "store", "stored",
      "last", "lasts", "long", "wilt", "wilted", "wilting", "limp", "soggy", "watery", "wet",
      "wash", "washing", "bag", "buy", "supermarket", "calories", "healthy", "fruit",
      "pasta", "potato", "coleslaw", "slaw", "caesar", "nicoise", "recipe")),
    (("bread sauce",),
     ("bread sauce",),
     "About 20 minutes start to finish. Simmer half an onion studded with cloves and a bay leaf in 300ml milk for 10 minutes, then "
     "strain it and stir in 60g fresh breadcrumbs, a knob of butter and a grating of nutmeg. It "
     "thickens in 5 minutes and should be the consistency of thick custard; make it the day "
     "before and reheat it gently.",
     ("loaf", "freeze")),
    (("quiche", "quiche lorraine"),
     ("quiche",),
     "About an hour start to finish. Line a tin with shortcrust and bake it blind at 190C (170C fan) for 15 minutes, then fill "
     "with 3 eggs beaten with 200ml cream, salt and nutmeg, plus bacon or cheese. It needs 30 to "
     "35 minutes until barely set in the middle; blind baking first is what stops a soggy base.",
     ("without a tin", "no tin", "vegan", "crustless", "leftover")),
    (("scones", "scone"),
     ("scones",),
     "About 30 minutes start to finish. Rub 60g cold butter into 350g self-raising flour with a pinch of salt, stir in 150ml milk "
     "and 2 tablespoons of sugar, and pat it out 2cm thick - handle it as little as possible. Cut "
     "the rounds straight down, glaze with milk and bake 12 to 15 minutes at 220C (200C fan); "
     "twisting the cutter is what seals the sides and stops them rising.",
     # "scones without buttermilk" asks for the substitute, which has its own entry
     ("cream tea", "jam", "warm", "freeze", "without buttermilk", "no buttermilk", "buttermilk",
      "substitute", "instead", "swap")),
    (("shortbread",),
     ("shortbread",),
     "About 45 minutes start to finish. Work 150g plain flour, 100g butter and 50g caster sugar together into a crumbly dough, press "
     "it into a tin and prick it all over, then bake 30 to 35 minutes at 160C (140C fan) until "
     "pale gold. Cut it into fingers while it is warm and leave it in the tin to cool, because "
     "shortbread is fragile until it sets.",
     ("biscuit", "dough", "freeze")),
    (("brownies", "brownie"),
     ("brownies",),
     "About 45 minutes start to finish. Melt 200g dark chocolate with 175g butter, beat in 250g sugar, 3 eggs and 100g flour, and "
     "bake 25 minutes at 180C (160C fan) in a lined tin. Take it out while the middle still "
     "wobbles - it sets as it cools - and that is the difference between fudgy and cake.",
     ("without", "egg free", "eggless", "vegan", "gluten", "leftover", "freeze")),
    # "how do i make rice pudding" was answered with an apple crumble and "how do i make rice
    # crispy cakes" with a Victoria sponge: both are dishes whose first word is another food, so
    # the row that owns rice or cake took the line. Each is its own dish with its own method.
    (("rice pudding", "rice puddings"),
     ("rice pudding",),
     "About 1 hour 20 minutes start to finish. Butter a dish and put in 60g pudding rice, 600ml whole milk, 150ml cream, 40g "
     "sugar and a strip of lemon peel or a bay leaf. Bake at 150C (130C fan) for 1 hour 15, "
     "stirring once after 30 minutes, until the rice is soft and the top is browned. It thickens "
     "as it cools, so loosen it with milk; grate nutmeg over the top.",
     # a rice pudding that is asked for with something left out, or a tin, is another answer
     ("without", "no egg", "egg free", "eggless", "vegan", "dairy free", "tin", "tinned", "shop",
      "buy", "microwave", "slow cooker", "crockpot", "crock pot", "pressure cooker")),
    (("rice crispy cakes", "rice krispie cakes", "rice crispies", "rice krispies",
      "crispy cakes", "krispie cakes", "cornflake cakes"),
     # the ask is the same dish in any spelling: a bare "rice krispie cakes" reached the row's
     # key and then failed its ask, because only the "crispy" spelling was listed in the ask
     ("rice crispy cakes", "rice krispie cakes", "crispy cakes", "krispie cakes",
      "rice crispies", "rice krispies", "cornflake cakes"),
     "About 15 minutes plus 30 to set. Melt 100g butter with 200g marshmallows, or 200g chocolate, over a low heat, take it off "
     "the heat and stir in 150g rice cereal, press it into a lined tin and chill until it sets. A "
     "spoon of golden syrup keeps them soft, and too long on the heat makes them hard.",
     ("without", "vegan", "healthy", "calories", "shop", "buy", "gift")),
    (("custard",),
     ("custard",),
     "About 20 minutes start to finish. Warm 300ml milk and 150ml cream with a vanilla pod, whisk it into 4 egg yolks and 50g sugar, "
     "then cook it gently, stirring, until it coats the back of the spoon - about 80C, never a "
     "boil. Off the heat at that point it thickens; let it boil and it scrambles.",
     ("powder", "tin", "cold", "leftover")),
    (("coleslaw",),
     ("coleslaw",),
     "About 15 minutes start to finish. Shred white cabbage and carrot finely, salt them 10 minutes and squeeze the water out, then "
     "mix with mayonnaise, a splash of vinegar and a spoon of mustard. Squeezing is what stops it "
     "going watery in an hour; it keeps 3 days in the fridge.",
     ("dressing", "recipe for", "buy", "shop")),
    (("hummus", "houmous", "humous"),
     ("hummus",),
     "About 5 minutes start to finish. Blitz a drained tin of chickpeas with 2 tablespoons of tahini, the juice of a lemon, a clove "
     "of garlic, half a teaspoon of salt and 3 or 4 tablespoons of iced water until it is smooth "
     "and pale. The iced water is the trick: it whips the tahini and turns a grainy paste into the "
     "smooth stuff. No tahini? Two tablespoons of yoghurt or toasted sunflower seeds do the "
     "same job, and it still beats the tub.",
     ("shop", "buy", "calories", "healthy")),
    (("gammon", "gammon joint", "ham joint"),
     ("gammon",),
     "About 2 hours start to finish for a 1.5kg joint. Simmer a smoked gammon joint 20 minutes per 500g, then change the water once if it is very "
     "salty, and finish it in a hot oven 20 minutes with a glaze of mustard, honey and cloves. "
     "Rest it 15 minutes before carving; boiling first is what keeps it from drying out.",
     ("ham", "sandwich", "leftover", "freeze", "slow cooker", "pressure cooker",
      "air fryer", "microwave")),
    (("prawns", "prawn"),
     ("prawns",),
     "About 5 minutes start to finish. Prawns are done in 2 to 3 minutes: fry them in hot butter with garlic until they turn pink "
     "and curl into a C, then take them out of the pan. The moment they curl into a tight O they "
     "are overcooked and rubbery, so they go in last and come out first.",
     ("frozen", "defrost", "smell", "pink", "peel", "devein")),
    (("vegetable soup", "soup from scratch", "make soup"),
     ("soup",),
     "About 35 minutes start to finish. Soften an onion, carrot and celery in butter for 10 minutes, add 1kg of whatever vegetables "
     "you have plus 1 litre of stock, and simmer 20 minutes before blending. Season it at the end "
     "and taste it twice; a squeeze of lemon or a spoon of cream at the end is what makes a plain "
     "soup taste finished.",
     ("tinned", "tin of", "leftover", "freeze", "bread", "with")),
    # --- the sauces and the pastry everything else is built from -------------
    (("white sauce", "bechamel", "bechamel sauce", "cheese sauce", "sauce for pasta"),
     ("white sauce", "bechamel"),
     "About 10 minutes start to finish. Melt 40g butter, stir in 40g plain flour and cook it 1 minute, then add 500ml milk a splash "
     "at a time, whisking each addition in before the next. Simmer 5 minutes until it coats a "
     "spoon; adding all the milk at once is what makes it lumpy, and a whisk beats a spoon.",
     ("pasta bake", "lasagne", "macaroni", "for pasta", "recipe for")),
    (("shortcrust pastry", "shortcrust", "pastry", "pie crust"),
     ("shortcrust pastry", "pastry"),
     "About 45 minutes start to finish. Rub 125g cold butter into 250g plain flour until it looks like breadcrumbs, add a pinch of "
     "salt and 2 to 3 tablespoons of cold water, and bring it together with a knife - stop the "
     "moment it holds. Rest it in the fridge 30 minutes before rolling; warm pastry shrinks in the "
     "tin and tears.",
     # "pasty" alone is one edit from "pastry", so the typo reader vetoed every pastry line:
     # the Cornish pie has to be named in full to stay out of this answer.
     ("soggy", "cracked", "puff", "filo", "choux", "buy", "shop", "shortbread", "cornish pasty")),
    (("curry from scratch", "chicken curry", "curry", "curry sauce"),
     ("curry",),
     "About 40 minutes start to finish. Fry a chopped onion 8 minutes until golden, then garlic, ginger and a tablespoon each of "
     "ground cumin, coriander and turmeric for 1 minute, and only then the meat. Add a tin of "
     "tomatoes, 150ml yoghurt or coconut milk and simmer 25 minutes; frying the spices in oil is "
     "what separates a curry from meat in a sauce.",
     ("jar", "paste", "leftover", "how long does", "keep", "freeze", "curry powder", "plant",
      "leaf", "leaves")),
    (("shepherds pie", "shepherd's pie", "cottage pie", "shepards pie"),
     ("shepherds pie", "shepherd's pie", "cottage pie"),
     "About 75 minutes start to finish. Brown 500g mince, soften an onion and carrot with it, add a tablespoon of flour, a "
     "tablespoon of tomato puree, 300ml stock and a splash of Worcestershire, and simmer 25 "
     "minutes until it is thick rather than wet. Top with mash, fork the surface so it crisps, and "
     "bake 25 minutes at 200C (180C fan). Shepherd's pie is lamb, cottage pie is beef.",
     ("vegetarian", "vegan", "quorn", "lentil", "sweet potato", "leftover", "freeze")),
    (("fish pie",),
     ("fish pie",),
     "About 50 minutes start to finish. Poach 500g mixed fish in 300ml milk for 5 minutes, use that milk to make a white sauce with "
     "40g butter and 40g flour, and fold in the fish, a handful of prawns and a spoon of mustard. "
     "Top with mash and bake 25 minutes at 200C (180C fan); a hard-boiled egg in the middle is "
     "traditional and the sauce needs to be looser than you think before it bakes.",
     ("fishcake", "fish cake", "bake", "freeze", "restaurant")),
    (("beef stew", "beef casserole", "stew", "casserole"),
     ("beef stew", "stew", "casserole"),
     "About 2 to 3 hours start to finish. Brown 1kg of chuck steak in batches in a heavy pot, soften two onions and a carrot in the "
     "same pot, add a tablespoon of flour, 500ml stock, a bay leaf and a splash of Worcestershire, "
     "and cook 2 hours at 150C (130C fan) with the lid on. Chuck or shin, never lean stewing "
     "steak: the fat and sinew are what go soft and make the gravy.",
     ("slow cooker", "leftover", "freeze", "vegetarian", "vegan", "microwave", "lamb", "chicken")),
    (("risotto", "mushroom risotto", "risotto rice"),
     ("risotto",),
     "About 30 minutes start to finish. Soften an onion in butter, stir in 300g arborio rice for 2 minutes, then add 1 litre of hot "
     "stock a ladle at a time, waiting for each to be absorbed, for about 18 minutes. Beat in "
     "butter and parmesan off the heat at the end; cold stock is what stalls the rice, and it "
     "should still flow on the plate.",
     ("rice pudding", "leftover", "microwave", "bake", "freeze", "reheat", "reheating")),
    (("crumble", "fruit crumble"),
     ("crumble",),
     "About an hour start to finish. Rub 100g cold butter into 200g plain flour with 100g sugar and a pinch of salt until "
     "crumbly, put 800g of fruit in a dish with 2 tablespoons of sugar and a spoon of cornflour, "
     "and bake 35 to 40 minutes at 190C (170C fan). Cornflour is what stops the juice running; "
     "keep the crumble loose rather than pressing it down.",
     ("bread and butter", "yorkshire", "batter", "savoury", "freeze")),
    (("bread and butter pudding", "bread pudding"),
     ("bread and butter pudding",),
     "About 75 minutes start to finish. Butter slices of stale white bread, layer them in a dish with raisins, and pour over a "
     "custard of 3 eggs, 300ml milk, 150ml cream and 50g sugar; leave it 20 minutes to soak, then "
     "bake 35 minutes at 170C (150C fan) in a water bath. Stale bread and the soak are the two "
     "things that stop it turning into scrambled egg.",
     ("crumble", "summer pudding", "leftover", "freeze")),
    (("roast parsnips", "parsnips"),
     ("roast parsnips", "parsnips"),
     "About 50 minutes start to finish. Peel and quarter them, cutting out the woody core, parboil 3 minutes, toss in oil, honey and "
     "salt, and roast 35 to 40 minutes at 200C (180C fan). They want longer and more space than "
     "potatoes; crowding the tin steams them instead of caramelising.",
     # "when should i plant parsnips" is the sowing question, and the word plant in a cooking
     # line is what hands it over: the roast row already stands down for grow
     ("soup", "mash", "puree", "how long do they keep", "grow", "plant", "planting",
      "planted", "sow", "sowing", "sowed", "seed", "seeds", "harvest", "when should i plant",
      "time of year", "bed")),
    (("dumplings", "suet dumplings"),
     ("dumplings",),
     "About 25 minutes start to finish. Mix 100g self-raising flour with 50g suet, a pinch of salt and enough cold water to make a "
     "soft dough, roll into 8 balls and drop them onto a simmering stew for the last 20 minutes "
     "with the lid on. Do not lift the lid while they cook; the steam is what makes them light.",
     ("chinese", "gyoza", "steamed", "pork", "frozen")),
    (("victoria sponge", "victoria sandwich"),
     ("victoria sponge", "victoria sandwich"),
     "About 45 minutes start to finish. Weigh 4 eggs and use the same weight of butter, sugar and self-raising flour: cream the "
     "butter and sugar, beat the eggs in one at a time, fold the flour in, and split it between two "
     "20cm tins. Bake 22 to 25 minutes at 180C (160C fan) until it springs back, and do not open "
     "the oven in the first 20 minutes.",
     ("vegan", "gluten", "without", "eggless", "loaf", "tray bake",
      "keep", "keeps", "keeping", "last", "lasts", "stale", "fresh", "store", "freeze",
      "fridge", "freezer", "reheat", "leftover", "leftovers")),
    (("flapjacks", "flapjack"),
     ("flapjacks",),
     "About 35 minutes start to finish. Melt 150g butter with 120g golden syrup and 120g light brown sugar, stir in 300g oats and a "
     "pinch of salt, and press it into a lined tin. Bake 20 to 25 minutes at 180C (160C fan) until "
     "the edges are gold - it firms as it cools, so pulling it out early is what keeps it chewy.",
     ("american", "pancake", "porridge", "oatcake")),
    (("cheesecake",),
     ("cheesecake",),
     "About 75 minutes start to finish. For a baked one, beat 600g cream cheese with 150g sugar, 3 eggs and a tablespoon of flour, "
     "pour it on a biscuit base of 250g digestives and 100g butter, and bake 45 minutes at 160C "
     "(140C fan). Cool it in the oven with the door open, because a sudden draught is what cracks "
     "the top.",
     ("no bake", "no-bake", "vegan", "shop", "buy", "restaurant", "freeze")),
    (("waffles", "waffle batter"),
     ("waffles", "waffle"),
     "About 30 minutes start to finish. Whisk 250g plain flour, 2 teaspoons of baking powder, 2 eggs, 300ml milk and 100g melted "
     "butter and cook them in a hot, well-brushed waffle iron for 3 to 4 minutes. Baking powder "
     "is what makes them crisp outside; too much batter is what makes them spill and go soggy.",
     ("toppings", "shop", "buy", "frozen", "chicken and waffles")),
    (("naan", "naan bread"),
     ("naan",),
     "About 90 minutes, rise included start to finish. Mix 300g plain flour, 150g yoghurt, 7g yeast, a teaspoon of sugar and 100ml warm water into "
     "a soft dough, leave it an hour, then roll ovals and cook them in a very hot dry pan 2 "
     "minutes a side until they blister. Brush with garlic butter afterwards; without the yoghurt "
     "they come out like pitta.",
     ("shop", "buy", "frozen", "peshwari", "keema")),
    (("garlic bread",),
     ("garlic bread",),
     "About 20 minutes start to finish. Mash 2 cloves of crushed garlic into 75g soft butter with chopped parsley, spread it into "
     "slices most of the way through a part-baked baguette, wrap it in foil and bake 15 minutes at "
     "200C (180C fan), then open the foil for the last 5 to crisp it. Soft butter spreads evenly; "
     "melted butter runs to the bottom and burns.",
     ("cheesy", "cheese stuffed", "shop", "buy", "frozen", "dough")),
    (("smoothie", "smoothies", "green smoothie"),
     ("smoothie",),
     "About 5 minutes start to finish. Blend a banana, a handful of frozen berries, 200ml milk or yoghurt and a spoon of oats for "
     "about 30 seconds, adding liquid until it pours. Frozen fruit instead of ice is what keeps it "
     "thick and cold, and a spoon of oats makes it hold you until lunch.",
     ("weight", "diet", "protein powder", "detox", "juicer")),
    (("rice and peas",),
     ("rice and peas",),
     "About an hour start to finish. Soak 300g of kidney beans overnight, simmer them with a tin of coconut milk, a sprig of "
     "thyme, a chopped onion and a scotch bonnet for 40 minutes, then add 300g of washed rice and "
     "cook 20 minutes with the lid on. Do not stir it while it cooks; that is what makes it gluey.",
     ("black eyed", "green beans", "pea risotto", "nigerian")),
    (("french toast", "eggy bread"),
     ("french toast", "eggy bread"),
     "About 15 minutes start to finish. Beat 2 eggs with 100ml milk, a pinch of salt and a little cinnamon, soak slices of slightly "
     "stale bread for 20 seconds a side and fry them in butter for 2 to 3 minutes a side over a "
     "medium heat. Stale bread and a medium heat are the whole trick: fresh bread turns to "
     "scrambled egg and a hot pan burns the outside.",
     ("savoury", "cheese", "vegan", "banana bread")),
    (("french onion soup",),
     ("french onion soup",),
     "About 75 minutes start to finish. Slice 1kg of onions and cook them in butter on a low heat for 40 to 45 minutes, stirring now "
     "and then, until they are dark gold; then add a tablespoon of flour, 150ml white wine and 1.5 "
     "litres of beef stock and simmer 20 minutes. Ladle it into bowls with a slice of toasted "
     "baguette and gruyere and grill until the cheese bubbles; the time in the pan is the soup.",
     ("quick", "pressure cooker", "slow cooker", "soup maker")),
    (("curry paste", "thai curry paste", "tikka paste"),
     ("curry paste",),
     "About 10 minutes start to finish. Blitz 2 onions, 4 garlic cloves, a thumb of ginger, 2 chillies, a teaspoon each of cumin, "
     "coriander and turmeric and a splash of oil into a paste, then fry it in oil for 5 minutes "
     "before the meat goes in. Frying the paste until it darkens and smells sweet is what takes "
     "the raw edge off; a jar is fine when you are short of time.",
     ("buy", "shop", "thai green", "red curry", "massaman", "how long does")),
    (("sushi rice",),
     ("sushi rice",),
     "About 40 minutes start to finish. Rinse 300g of short-grain rice until the water runs clear, cook it with 330ml water, then "
     "fold through a dressing of 3 tablespoons of rice vinegar, 2 of sugar and a teaspoon of salt "
     "while it is still warm and let it cool to room temperature. Fanning it as it cools is what "
     "gives the grains their shine; do not put it in the fridge.",
     ("brown", "how long does", "sushi at home", "shop")),
    (("meatballs", "meatballs in sauce"),
     ("meatballs",),
     "About 40 minutes start to finish. Mix 500g of mince with 50g breadcrumbs, 1 egg, a grated onion and a teaspoon of salt, roll "
     "them the size of a walnut and brown them in oil before they go into the sauce for 20 "
     "minutes. Breadcrumbs and egg hold them together; browning first is what stops them falling "
     "apart in the tomato.",
     ("vegan", "vegetarian", "ikea", "swedish", "shop", "buy", "soup")),
    (("lasagne", "lasagna"),
     ("lasagne", "lasagna"),
     "About 90 minutes start to finish. Layer ragu, white sauce and lasagne sheets three times, finishing with white sauce and "
     "parmesan, and bake 40 minutes at 180C (160C fan), resting it 10 minutes before you cut it. "
     "Make the ragu thicker than you would eat on pasta and use fresh sheets or a splash of water "
     "in the dish, or the top dries before the middle is soft.",
     ("vegetarian", "vegan", "courgette", "aubergine", "spinach", "shop", "ready meal")),
    (("ratatouille",),
     ("ratatouille",),
     "About 50 minutes start to finish. Cook a sliced aubergine, two courgettes and two peppers separately in oil until golden, "
     "then simmer them with a tin of tomatoes, onion, garlic and thyme for 25 minutes. Cooking the "
     "vegetables separately first is the difference between ratatouille and vegetable mush.",
     ("film", "cartoon", "pixar", "roasted vegetables")),
    (("colcannon",),
     ("colcannon",),
     "About 30 minutes start to finish. Boil 1kg of potatoes, mash them with 100g butter and 150ml milk, then fold in 300g of "
     "shredded cabbage (or kale) that you cooked in butter for 5 minutes with a few spring onions. "
     "Warm the milk before it goes in and do not beat the mash too hard, or it goes gluey.",
     ("champ", "bubble and squeak", "cabbage soup")),
    (("beans on toast", "baked beans on toast"),
     ("beans on toast",),
     "About 10 minutes start to finish. Warm a tin of beans in a pan with a knob of butter and a dash of Worcestershire for 4 "
     "minutes while the toast browns, and put the beans on the toast rather than the toast in the "
     "beans. Butter on the toast first stops it going soggy, and a pinch of pepper or a little "
     "cheese is the upgrade.",
     ("from scratch", "dried beans", "homemade baked beans", "recipe for beans")),
    (("pizza sauce", "pizza topping"),
     ("pizza sauce",),
     "About 25 minutes start to finish. Crush a tin of plum tomatoes by hand with a teaspoon of salt, a crushed garlic clove, a "
     "tablespoon of olive oil and a pinch of oregano; do not cook it, it cooks on the pizza. "
     "Cooking the sauce first is what makes it taste stewed, and too much sauce is what makes the "
     "base soggy.",
     ("pasta", "bolognese", "dough", "base", "shop", "jar")),
    (("coleslaw dressing", "dressing for coleslaw"),
     ("coleslaw dressing",),
     "About 5 minutes start to finish. Mix 4 tablespoons of mayonnaise with a tablespoon of white wine vinegar, a teaspoon of sugar "
     "and a pinch of salt and pepper, then toss it through shredded cabbage and carrot. Vinegar "
     "and sugar are what stop it tasting flat; a vinaigrette is for salad leaves, not coleslaw.",
     ("vinaigrette", "salad dressing", "hot", "warm", "shop", "buy")),
    (("bread", "loaf", "loaves", "white loaf", "wholemeal loaf", "sourdough loaf"),
     ("make", "bake", "baking", "recipe", "how", "ingredients", "from scratch", "method",
      "how long", "time", "knead", "prove", "oven"),
     "About 3 hours start to finish, most of it waiting. Mix 500g strong white flour, 7g yeast, "
     "10g salt and 325ml warm water into a soft dough, knead 10 minutes until it is smooth and "
     "springs back, leave it covered until it has doubled (about an hour), shape it into a tin and "
     "prove it another hour, then bake 30 to 35 minutes at 220C (200C fan). Knock it out of the "
     "tin and let it cool before you cut it, or the crumb goes gummy.",
     # a fault, a keeping question or a swap is a different answer: "my bread is dense" and
     # "why is my sourdough flat" have their own entries on main.
     ("dense", "sank", "sunken", "flat", "risen", "rise", "rising", "prove", "proving", "proof",
      "stale", "keep", "keeping", "store", "storing", "lasts", "freeze",
      # a timer question wants the number, not the method, and _RECIPE_ASK carries "how long".
      # `avoid` is matched word by word, so a phrase never fires - the single word "long" does,
      # and the phrases this replaces were doing nothing at all.
      "long",
      "mould", "mouldy", "sliced", "toast", "crumbs",
      # how to slice a loaf is a knife question, not the mixing bowl's: "how should i slice a
      # loaf of sourdough" and "how thick should i slice bread" were both this method card.
      "slice", "slices", "slicing", "thick", "thickness", "thin", "evenly",
      "breadcrumbs", "machine", "maker", "without", "gluten",
      # a sweet loaf is a cake, not this yeast method: the row's bare "loaf" was catching
      # "loaf cake", "banana bread", "malt loaf" and "lemon drizzle loaf".
      "cake", "cakes", "banana", "bananas", "fruit", "malt", "drizzle", "soda", "teacake",
      "teacakes", "carrot", "courgette", "zucchini", "pumpkin")),
    # A sweet loaf is a cake in a tin, not the yeast method the bread row above holds: "fruit
    # loaf recipe" and "i want to make a malt loaf" had nothing to answer them, because that
    # bread row stands aside for "fruit" and "malt" on purpose. One row for the family, keyed on
    # the loaf's own name, so the plain bread lines keep the bread method.
    (("fruit loaf", "malt loaf", "fruited loaf", "tea loaf", "bara brith", "fruit bread",
      "fruited bread"),
     ("fruit loaf", "malt loaf", "tea loaf", "bara brith", "fruit bread"),
     "About 1 hour 40 minutes start to finish. Soak 300g mixed dried fruit in hot tea for 20 "
     "minutes, then beat in 225g self-raising flour, 100g soft brown sugar, 2 eggs and 100g "
     "melted butter, and bake it in a lined 900g loaf tin at 160C (140C fan) for 60 to 70 "
     "minutes, until a skewer comes out clean. The soak is what stops it baking dry; for malt "
     "loaf add 2 tablespoons of malt extract to the tea and give it 10 minutes longer.",
     # a timer question wants the clock, not the method - `avoid` is matched word by word, so
     # the single word is what stands the row aside (the bread row above does the same)
     ("shop", "buy", "supermarket", "toast", "why", "sank", "dense", "long")),
    # The bread row stands down for "without", so a no-yeast loaf had only the prove
    # instructions, which cannot work without yeast. Soda bread is the answer that does.
    (("soda bread", "soda loaf", "no yeast bread", "bread without yeast", "no yeast",
      "yeast free bread", "bread with no yeast"),
     ("soda bread", "no yeast", "without yeast", "yeast free", "bread", "loaf"),
     "About 50 minutes start to finish. Mix 500g plain or wholemeal flour, a teaspoon of "
     "bicarbonate of soda, a teaspoon of salt and 400ml buttermilk until it just comes "
     "together, shape it into a round, cut a deep cross in the top and bake at 200C (180C fan) "
     "for 30 to 35 minutes. Work it as little as you can and bake it the moment it is mixed: "
     "there is no yeast to lift it, and every extra minute of kneading makes it heavier.",
     # "how long do i bake soda bread for" is the timer's, and a pizza, naan or flatbread made
     # without yeast is a different bread with its own recipe - this row is the soda loaf only.
     ("shop", "buy", "keep", "store", "freeze", "fried", "flourless", "long",
      "pizza", "naan", "flatbread", "pitta", "pita", "focaccia", "ciabatta", "bagel",
      "bagels", "crumpet", "crumpets", "pancake", "pancakes", "doughnut", "doughnuts",
      "scone", "scones", "cake", "cakes", "tortilla", "tortillas", "chapati", "chapattis")),
    # The dishes the table was missing that people ask for by name, in the plainest words: a
    # "how do i make a frittata" or "how do i cook carrots" line had nothing to answer it. They
    # take their place in the same table rather than a second one, so one dish is one answer
    # however the line asks for it, and they inherit `_RECIPE_NOT_THIS` and the fault words.
    (("guacamole", "guac"),
     ("guacamole",),
     "About 10 minutes start to finish. Mash 2 ripe avocados with the juice of a lime and a good "
     "pinch of salt, then stir in half a small onion, a chilli and a handful of coriander, all "
     "chopped small. Lime, not the stone, is what keeps it green, so press cling film onto the "
     "surface if it is waiting.",
     ("shop", "buy", "calories", "healthy", "brown")),
    (("roast dinner", "sunday roast", "roast lunch"),
     ("roast dinner",),
     "About 2 hours start to finish for a 2kg chicken. Work backwards from the meat: 20 minutes "
     "per 500g plus 20 at 190C (170C fan), so a 2kg bird is 1 hour 40 and then rests 15 minutes. "
     "Potatoes go in at 200C for 45 minutes, so start them 20 minutes after the bird; stuffing "
     "and pigs in blankets 25 minutes; the veg 10 minutes before the end; and make the gravy in "
     "the roasting tin while the meat rests.",
     ("restaurant", "pub", "carvery", "vegan", "vegetarian", "calories", "roast beef",
      "roast lamb", "roast pork", "joint")),
    # Two rows for one vegetable, because "how do i roast carrots" was being told to boil them:
    # the roast row is first and leads with the oven's 25 minutes, and each row's avoid keeps the
    # other's method off it, so a line that says boil or roast gets the one that says it.
    (("carrot", "carrots"),
     ("roasted carrots",),
     "Roast carrots at 200C (180C fan) for 25 minutes with oil, salt and a spoon of honey, "
     "turning them once; boiled, a peeled carrot takes 5 to 7 minutes in salted water. Whole ones "
     "take longer than batons and they go mushy fast, so taste one rather than watching the clock.",
     # a carrot that came out soggy is a fault, not a request for a method: "how do i make my
     # carrots less soggy" asked for the fix and was given the roasting recipe. The fault words
     # are here because this row is keyed on "make" + "carrots", which is also how a fault in
     # the pan is said.
     ("cake", "raw", "grow", "plant", "allotment", "juice", "soup", "purée", "puree",
      "boil", "boiled", "boiling", "salted water",
      "soggy", "mushy", "overcooked", "over cooked", "too soft", "watery", "less soggy",
      "less mushy", "went soggy", "go soggy")),
    (("carrot", "carrots"),
     ("carrots",),
     "Five to seven minutes in boiling salted water, until a knife goes in with a little "
     "resistance left; or roast them at 200C (180C fan) for 25 minutes with oil, salt and honey. "
     "Whole ones take longer than sliced, and they go mushy fast, so taste one rather than "
     "watching the clock.",
     ("cake", "raw", "grow", "plant", "allotment", "juice", "soup", "purée", "puree",
      "roast", "roasting", "roasted", "oven", "honey",
      "soggy", "mushy", "overcooked", "over cooked", "too soft", "watery", "less soggy",
      "less mushy", "went soggy", "go soggy")),
    (("frittata", "spanish omelette", "tortilla"),
     ("frittata",),
     "About 30 minutes start to finish. Soften an onion and any veg in an ovenproof pan for 8 "
     "minutes, pour over 6 beaten, seasoned eggs, and cook on the lowest heat for 5 minutes until "
     "the edges set. Then put the pan under a hot grill for 4 to 5 minutes to finish the top; it "
     "is done when the middle has just stopped wobbling.",
     ("vegan", "wrap", "wraps", "burrito", "frozen", "chips")),
    (("milkshake",),
     ("milkshake",),
     "About 5 minutes start to finish. Three scoops of vanilla ice cream and 200ml of cold milk, "
     "blended 20 seconds, with a spoon of malt powder or a little vanilla. Less milk for a thick "
     "one, and drink it straight away: it separates as it stands.",
     ("healthy", "calories", "vegan", "shop", "buy")),
    (("fairy cake", "fairy cakes", "cupcakes", "buns"),
     ("fairy cakes",),
     "About 35 minutes start to finish. The equal-weights sponge (100g each of butter, sugar and "
     "self-raising flour and 2 eggs) spooned into 12 paper cases, baked at 180C (160C fan) for 15 "
     "minutes until they spring back. Butter and icing sugar beaten together, twice as much sugar "
     "as butter, pipes on top.",
     ("hot cross", "burger", "bread", "iced", "shop", "buy", "calories", "vegan")),
    (("lemon drizzle", "lemon cake"),
     ("lemon drizzle",),
     "About 55 minutes start to finish. The equal-weights sponge (175g each of butter, sugar and "
     "self-raising flour and 3 eggs) with the zest of a lemon, in a lined loaf tin at 180C (160C "
     "fan) for 40 minutes. While it is warm, prick it and pour over 100g of icing sugar mixed with "
     "the juice of that lemon.",
     ("shop", "buy", "calories", "vegan", "gluten")),
    (("wrap", "wraps"),
     ("wrap",),
     "About 5 minutes start to finish. Warm the tortilla for 30 seconds a side in a dry pan so it "
     "folds without cracking, put the filling in a line down the middle, fold the two ends in and "
     "roll it up tightly. Anything wet goes in first with something crisp on top, or the wrap "
     "goes soggy.",
     ("gift", "present", "shop", "buy", "calories", "healthy")),
    (("rub", "spice rub", "dry rub"),
     ("dry rub",),
     "About 5 minutes start to finish, then 30 minutes resting. A tablespoon of paprika, a "
     "teaspoon each of salt, black pepper, garlic powder and cumin, and a pinch of cayenne. Rub "
     "it over the chicken with a little oil and leave it 30 minutes, or overnight in the fridge: "
     "the salt is what carries the flavour in.",
     # "rub" on its own is also a wall before painting and a stain on a shirt, and main answers
     # both; a spice rub is the only rub this row is for
     ("eyes", "sore", "ache", "burn", "itch", "skin", "back", "shoulder",
      "wall", "walls", "paint", "painting", "sanding", "sand", "sandpaper", "stain", "stains",
      "wood", "varnish", "furniture", "rub down", "rubbed down", "floor", "floorboards",
      "brass", "silver", "shoe", "shoes", "leather")),
    (("batter", "yorkshire batter", "pancake batter"),
     ("batter",),
     "About 35 minutes start to finish, most of it resting. 150g of plain flour, 1 egg, 200ml of "
     "milk and a pinch of salt, whisked to a smooth batter and rested 30 minutes. For a crispy "
     "coating, 100g of plain flour and 100g of cornflour with 200ml of very cold beer or "
     "sparkling water, mixed at the last minute.",
     ("phone", "battery", "car", "flat", "dead", "leftover")),
    (("pie", "meat pie"),
     ("pie",),
     "About 1 hour start to finish. Line a pie dish with shortcrust pastry, put in filling that "
     "has cooled (a hot filling steams the base), brush the rim with egg and lay a lid on, "
     "pressing it down. Cut a hole in the middle for the steam, brush the top with egg, and bake "
     "at 200C (180C fan) for 30 to 35 minutes until the pastry is golden.",
     ("fish pie", "shepherds pie", "shepherd's pie", "cottage pie", "sweet", "apple", "moussaka",
      "pie maker",
      # a pie chart is a spreadsheet question
      "chart", "charts", "excel", "spreadsheet", "graph", "graphs", "diagram", "powerpoint")),
    (("burrito", "burritos"),
     ("burrito",),
     "About 10 minutes start to finish. Warm a large tortilla, then put rice, beans, cheese and "
     "salsa in a line down the middle, leaving a border. Fold the two ends in, roll it tight, and "
     "seal it seam down in a hot dry pan for a minute: that holds it shut and crisps the outside.",
     ("shop", "buy", "frozen", "calories")),
    # Chips and a meringue are the two everyday things the table was missing: "how do i make
    # chips" and "how do i make meringue" were both a shrug on main, and each has a method
    # people follow every week. Chips are keyed on the potato cut and stand aside for the
    # portion ("how many chips"), the takeaway ("chip shop") and the side dish ("what goes with
    # chips"), because those three already have answers.
    (("chips", "fries", "french fries", "oven chips", "homemade chips"),
     ("chips",),
     "Cut floury potatoes (Maris Piper, King Edward) into 1cm chips, rinse the starch off under "
     "the tap and dry them thoroughly, then toss in oil and salt and roast at 220C (200C fan) "
     "for 30 to 35 minutes, turning twice. Dry chips and a single layer are the whole trick: "
     "wet chips steam instead of crisping, and a crowded tray does the same. For the soft "
     "middle, blanch them in boiling water for 5 minutes and dry them before they go in.",
     ("how many", "how much", "calories", "healthy", "shop", "buy", "supermarket", "takeaway",
      "chip shop", "chippy", "crisps", "best", "goes with", "with what", "side", "wedges",
      "sweet potato", "salad", "burger", "long", "freeze", "frozen",
      # "a chipped mug" and "a chipped plate" are the chip in the china, not the potato:
      # the cut-potato row answered a repair question with a recipe. A chip taken out of a
      # worktop, a sink, a bath, a tile or a glass is the same kind of repair question.
      "mug", "mugs", "cup", "cups", "plate", "plates", "bowl", "bowls", "tooth", "teeth",
      "tooth is", "windshield", "windscreen", "paint", "nail", "nails", "polish", "varnish",
      "worktop", "worktops", "counter", "countertop", "counter top", "sink", "sinks", "basin",
      "bath", "baths", "enamel", "tile", "tiles", "grout", "glass", "glasses", "laminate",
      "veneer", "stone", "granite", "quartz", "marble", "skirting",
      # "fried" reads as "fries" a letter out, so a fried chicken or a fried fish was given
      # the cut-potato recipe. Anything breaded or battered is `fried-crisp` in vegetables.py.
      # "breaded" and "breadcrumbs" are left out: a letter out they are the word "bread",
      # which is in this list for the loaf.
      "chicken", "fish", "prawn", "prawns", "halloumi", "tofu", "nugget", "nuggets", "goujon",
      "goujons", "katsu", "schnitzel", "scotch egg", "onion ring", "onion rings", "spring roll",
      "spring rolls", "batter", "battered", "panko",
      "tempura", "sausage", "sausages", "rice", "egg", "eggs", "toast", "bread", "cheese")),
    (("meringue", "meringues", "meringue nest", "meringue nests", "pavlova"),
     ("meringues", "meringue", "pavlova"),
     "Whisk 2 egg whites in a spotless dry bowl to stiff peaks, then add 110g of caster sugar a "
     "spoonful at a time, whisking until the meringue is glossy and you cannot feel the sugar "
     "between your fingers. Pipe or spoon nests and bake at 120C (100C fan) for 1 hour, then "
     "turn the oven off and leave them inside until it is cold: the slow dry is what keeps them "
     "crisp, and an egg white weighs about 30g, so 60g of white per 110g of sugar. A pavlova is "
     "the same mixture with a teaspoon each of cornflour and white vinegar whisked into the "
     "sugar, spread into a 20cm circle with a dip in the middle and baked 1 hour 15, and it "
     "wants cream and fruit on top once it is cold.",
     ("weep", "weeping", "weeps", "wept", "crack", "cracked", "cracks", "hollow", "sticky",
      "soggy", "chewy", "buy", "shop", "supermarket", "keep", "keeps", "store", "freeze",
      "frozen", "calories", "healthy", "eton", "lemon meringue", "pie",
      "why", "wont stiffen", "not stiff", "stiffen", "collapse", "peaks")),
    # The everyday dishes the table had no method for at all: typed on their own, each of these
    # was a shrug or an echo, and each is something people cook every week. They are keyed on the
    # dish, so the fault ("my yorkshire puddings did not rise"), the keeping question and the
    # nutrition question keep the rows they already had - the `avoid` words are what stand this
    # row down for them, since a bare name is not the only line that reaches it.
    (("omelette", "omelettes", "omelet", "plain omelette", "cheese omelette"),
     ("omelette", "omelet"),
     "About 5 minutes start to finish. Beat 2 or 3 eggs with a pinch of salt, melt a knob of "
     "butter in a non-stick pan over a medium heat until it foams, pour the eggs in and stir once, "
     "then leave them alone until the top is barely set. Fold it in half and slide it onto the "
     "plate while the middle still looks a little wet, because it finishes cooking on the way; "
     "cheese, ham or herbs go in before the fold, and low heat is what keeps it tender rather "
     "than rubbery.",
     ("sticking", "sticks", "stuck", "rubbery", "burnt", "calories", "healthy", "protein",
      "how many", "how long", "how many minutes", "take", "freeze", "leftover", "microwave",
      "air fryer")),
    (("jacket potato", "jacket potatoes", "baked potato", "baked potatoes"),
     ("jacket potato", "jacket potatoes", "baked potato", "baked potatoes"),
     "About 1 hour 15 minutes start to finish. Prick a 250g potato all over, rub it with oil and "
     "salt and bake it at 200C (180C fan) for an hour to an hour and a quarter, straight on the "
     "oven shelf rather than in a dish, so the skin crisps all over. In a hurry, microwave it 8 "
     "minutes first and then give it 20 minutes in the hot oven for the skin. Cut a cross in the "
     "top and open it while it is hot, with the butter going in before the filling.",
     ("calories", "healthy", "how long", "how many minutes", "air fryer", "freeze", "leftover",
      "foil", "tin foil", "oven chip", "chips", "goes with", "with what", "filling ideas",
      "toppings")),
    (("toad in the hole",), ("toad in the hole",),
     "About 55 minutes start to finish. Brown 8 sausages in a little oil in a roasting tin for 10 "
     "minutes at 220C (200C fan), then pour over batter made from 100g plain flour, 2 eggs and "
     "150ml milk that has rested 30 minutes, and bake 25 to 30 minutes without opening the door. "
     "The tin and the oil have to be properly hot when the batter goes in, or it will not climb.",
     ("leftover", "freeze", "vegetarian", "vegan", "calories", "healthy", "called", "name",
      "how long", "how many minutes")),
    (("sausage casserole", "sausage casseroles"),
     ("sausage casserole", "sausage casseroles"),
     "About 1 hour start to finish. Brown 8 sausages whole in a casserole dish, lift them out, "
     "soften an onion and a carrot in the fat, stir in a tablespoon of flour, then 500ml stock, a "
     "tin of tomatoes and a tin of beans, and put the sausages back in for 30 to 40 minutes at "
     "180C (160C fan). Browning them first is what keeps them whole, and the flour is what "
     "thickens the gravy.",
     ("leftover", "freeze", "vegetarian", "vegan", "calories", "healthy", "slow cooker",
      "best sausage", "how many", "how long", "how many minutes")),
    (("pizza", "pizzas", "homemade pizza"), ("pizza", "pizzas"),
     "About 1 hour 30 minutes start to finish, most of it rising. 500g strong white flour, 7g yeast, "
     "325ml water and 10g salt mixed and left an hour, then stretched thin on a floured tray and "
     "baked as hot as the oven goes, 240C or more, on a tray or stone heated for 20 minutes first, "
     "for 8 to 10 minutes. Tomato and cheese go on lightly, because a heavy topping steams the base "
     "instead of baking it.",
     ("order", "takeaway", "delivery", "frozen", "calories", "healthy", "buy", "shop",
      "how many", "goes with", "with what", "dough", "base", "pizza oven", "stone", "how long",
      "how many minutes")),
    (("crumpets", "crumpet"), ("crumpets", "crumpet"),
     "About 1 hour 45 minutes start to finish, most of it rising. 300g strong white flour, 7g yeast, "
     "a teaspoon of sugar and 350ml warm milk and water mixed to a thick batter and left an hour, "
     "then half a teaspoon of bicarbonate of soda stirred in with a splash of water, and ladled "
     "into buttered metal rings in a heavy pan on a low heat for 6 to 8 minutes, until the top is "
     "set and full of holes. Toast them before eating, because that is what crisps the outside.",
     ("buy", "shop", "supermarket", "toast", "toaster", "leftover", "fridge", "mould", "mold",
      "calories", "healthy", "how many", "goes with", "with what", "how long",
      "how many minutes")),

    # The dish the table did not hold. A name is how a lot of people ask for a method - the row
    # above reads a bare name as the ask, and these are the names that reached nothing at all:
    # carbonara, paella, tacos, nachos, falafel, shakshuka, dhal, katsu curry, pad thai, biryani,
    # burger, pork chops and a full english all came back "I'm listening" or "Got it".
    (("carbonara",),
     ("carbonara",),
     "About 20 minutes start to finish. Boil 200g of spaghetti and, while it cooks, fry 150g of "
     "chopped pancetta or streaky bacon until the fat runs, then take the pan off the heat. Beat "
     "3 eggs with 60g of grated pecorino or parmesan and plenty of black pepper, toss the drained "
     "pasta through the bacon, then stir the egg in off the heat so it turns into a glossy sauce "
     "rather than scrambled egg - the heat of the pasta is enough to cook it.",
     ("vegetarian", "vegan", "jar", "shop", "ready meal", "calories", "healthy", "ham")),
    (("paella", "chicken paella", "seafood paella"),
     ("paella",),
     "About 40 minutes start to finish. Soften a chopped onion and a red pepper in olive oil in a "
     "wide pan, stir in 2 chopped garlic cloves, a teaspoon of smoked paprika and 300g of paella "
     "or bomba rice for a minute, then add 900ml of hot stock and your chicken or prawns and "
     "simmer 18 minutes without stirring. Rest it 5 minutes off the heat under a tea towel: the "
     "crust on the bottom is the point, and stirring it is what stops it forming.",
     ("vegetarian", "vegan", "rice for", "which rice", "what rice", "basmati", "saffron", "shop",
      "frozen", "calories", "healthy", "keep")),
    (("tacos", "taco"),
     ("tacos", "taco"),
     "About 20 minutes start to finish. Warm corn or wheat tortillas in a dry pan for 20 seconds "
     "a side and keep them in a tea towel, then fill them with something already cooked and cut "
     "small - spiced mince, shredded chicken, black beans, fried fish or roast vegetables - with "
     "raw onion, coriander and a squeeze of lime. Two fillings and something sharp is a better "
     "taco than four that all taste the same.",
     ("shells", "kit", "shop", "frozen", "calories", "healthy", "seasoning")),
    (("nachos",),
     ("nachos",),
     "About 15 minutes start to finish. Spread a bag of tortilla chips in a single layer in a "
     "roasting tin, scatter over grated cheddar and sliced jalapenos and bake at 200C (180C fan) "
     "for 8 to 10 minutes, then put the cold things on after it comes out - salsa, soured cream, "
     "guacamole, coriander. Everything added before baking goes soggy, and a single layer is what "
     "stops half the chips being bare.",
     ("shop", "frozen", "calories", "healthy", "microwave", "cinema")),
    (("falafel",),
     ("falafel",),
     "About 30 minutes plus an overnight soak. Soak 250g of dried chickpeas in plenty of water "
     "overnight - tinned ones are already cooked and the mix falls apart - then blitz them with a "
     "small onion, 2 garlic cloves, a big handful of parsley and coriander, a teaspoon of cumin "
     "and a good pinch of salt. Shape walnut-sized balls and fry in 2cm of oil at 180C for 3 to 4 "
     "minutes until dark gold, or flatten them into patties and shallow fry.",
     ("mix", "wet", "watery", "shop", "buy", "calories", "healthy", "good for you", "bake")),
    (("shakshuka",),
     ("shakshuka",),
     "About 25 minutes start to finish. Soften a sliced onion and a red pepper in oil for 8 "
     "minutes, add 2 garlic cloves, a teaspoon of cumin and a pinch of chilli, then a tin of "
     "tomatoes and simmer 10 minutes until thick. Make wells in the sauce, crack in 4 eggs, cover "
     "and cook 5 to 7 minutes, until the whites are set and the yolks still run; feta scattered "
     "over at the end is the usual finish.",
     ("shop", "calories", "healthy", "recipe for four")),
    (("dhal", "dal", "daal", "lentil dhal", "tarka dhal"),
     ("dhal", "dal", "daal"),
     "About 35 minutes start to finish. Simmer 200g of red lentils with 700ml water, a chopped "
     "onion, 2 garlic cloves, a teaspoon of turmeric and salt for 25 minutes, stirring now and "
     "then, until it is soft and thick. Fry a teaspoon each of cumin and mustard seeds in ghee or "
     "oil with a pinch of chilli and stir that through at the end - that last frying is what makes "
     "it taste like dhal rather than lentils.",
     ("healthy", "good for you", "calories", "no lentils", "shop", "buy", "wet", "watery")),
    (("katsu curry", "chicken katsu", "katsu"),
     ("katsu curry", "chicken katsu", "katsu"),
     "About 40 minutes start to finish. Fry a chopped onion and a carrot for 8 minutes, stir in 2 "
     "tablespoons of mild curry powder and one of plain flour, then add 500ml of stock and simmer "
     "15 minutes; blend it smooth with a splash of soy sauce and a teaspoon of honey. Serve it "
     "with rice and breaded chicken or tofu, and make the sauce a bit looser than you think, "
     "because it thickens as it stands.",
     ("shop", "frozen", "takeaway", "wagamama", "calories", "healthy", "how many")),
    (("pad thai",),
     ("pad thai",),
     "About 20 minutes start to finish. Soak 200g of flat rice noodles in hot water for 10 "
     "minutes, then stir-fry prawns or tofu in a very hot wok, push them aside and scramble 2 eggs "
     "in the space, and add the drained noodles with 2 tablespoons of tamarind or lime juice, 2 of "
     "fish sauce and 1 of sugar. Toss for a minute with beansprouts and peanuts; the pan must be "
     "hot or the noodles steam instead of frying.",
     ("shop", "takeaway", "calories", "healthy", "how many")),
    (("biryani", "chicken biryani", "lamb biryani"),
     ("biryani",),
     "About 1 hour 20 minutes start to finish. Brown 500g of lamb or chicken with a chopped onion, "
     "2 garlic cloves, a tablespoon of garam masala and a cup of yoghurt, then simmer 25 minutes. "
     "Part-cook 300g of basmati for 5 minutes, layer it over the meat with saffron milk and fried "
     "onions, and steam it covered on the lowest heat for 20 minutes - the layering and the steam "
     "are what make it a biryani rather than rice with meat on top.",
     ("dry", "watery", "rice for", "which rice", "what rice", "healthy", "calories", "shop")),
    (("burger", "burgers", "homemade burger", "beefburger"),
     ("burger", "burgers"),
     "About 20 minutes start to finish. Shape 500g of minced beef into four patties with nothing "
     "but salt and pepper - work it as little as you can - and cook them in a very hot dry pan 2 "
     "to 3 minutes a side, pressing once. Rest them a minute, then build with cheese, lettuce, "
     "tomato and something sharp like pickles or mustard; salt inside the mix draws the water out "
     "and makes them dry.",
     ("healthy", "calories", "fattening", "make you fat", "shop", "buy", "frozen", "mcdonalds",
      "restaurant", "bun", "vegan", "vegetarian")),
    (("pork chops", "pork chop"),
     ("pork chops", "pork chop"),
     "About 20 minutes start to finish. Take the chops out of the fridge 20 minutes ahead, pat "
     "them dry and season well, then cook in a hot pan 3 to 4 minutes a side and rest 5 minutes. "
     "Cooked through means 65 to 70C at the centre, and a thick chop is better finished 5 minutes "
     "in a 200C oven than blackened in the pan.",
     ("how long", "how many minutes", "calories", "healthy", "shop", "buy", "slow cooker",
      "casserole", "apple sauce")),
    (("full english", "full english breakfast", "fry up", "cooked breakfast"),
     ("full english", "full english breakfast", "fry up", "cooked breakfast"),
     "About 30 minutes start to finish. Grill the sausages and bacon for 10 minutes and keep them "
     "warm while you fry the black pudding, mushrooms and tomatoes, and do the eggs last in the "
     "same pan. Beans warmed in a small pan and toast done at the end, so nothing is standing cold "
     "- and if you are feeding more than two, the oven on low is the only way to land it all at "
     "once.",
     ("hotel", "cafe", "calories", "healthy", "menu", "vegetarian", "vegan")),

)

