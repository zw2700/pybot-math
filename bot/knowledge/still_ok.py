"""Gone off: "is this still ok to eat", about the thing in your hand.

The one food question where guessing is worst, and one people ask every week: a pack of chicken
two days past its date, mince that smells a bit, a bit of blue on the cheddar. `cooking.py`
answers what to do with a food and its `KEEPS` table answers how long it keeps; neither answers
"is this one still all right", which wants the test and the verdict.

The entries here are data, not a new mechanism: keys, `avoid`, `ask` and the shared food words
come from `bot.knowledge.lookup` and `bot.knowledge.cooking`, so there is one matcher and one set
of food words in the bot.

Three gates keep a row off the lines that belong to somebody else, and every one of them is a
wrong answer rather than a dull one if it is missing:

- `DIET_WORDS` - "is cheese bad for you", "is it ok to eat 2 eggs a day": a spoilage test there
  reads as a diet answer, and the diet answer already exists.
- `RAW_WORDS` - "is it safe to eat raw pork" asks how to cook it. A spoilage test reads as
  permission to eat it raw, which is the worst possible reply.
- keeping and cooking words - "how long does mince keep", "is it ok to reheat chicken": those
  have their own answers, and a yes-or-no test given instead loses the number they asked for.

A line that is not one of these questions passes, so the row fires only when the line names the
food *and* asks the spoilage question with one of `OFF_ASKS`.

Eggs and cheese are not here: main already tests a suspect egg in a glass of water and already
says to cut the mould off hard cheese, so those lines have their answer. Only the five foods
that get a hedge or a nutrition speech are in this table.
"""
import re

from .cooking import PET_LINE_WORDS
from .lookup import PACK_DATE, entry

# The topic ids this domain answers (bot/understanding/topics.py).
ANSWERS = ("cooking", "food-and-drink")

# What makes a line an "is it still all right to eat" line rather than a keeping or a cooking
# one. Without one of these the row does not fire at all.
# "Off" is how most people say it - "has the chicken gone off", "is my chicken off", "did the beef
# go off" - and the rows below used to miss every one of them, because the ask only knew the
# "still ok" and "safe to eat" shapes. `OFF_THE_THING` keeps the preposition out.
# The three groups a raw vegetable can fall in. What makes them different is why the answer
# differs, so each group carries its own reason: a bean has a protein heat destroys, a potato has
# solanine and a starch that resists digestion, and a brassica or a salad vegetable is simply
# eaten as it grows.
_RAW_VEG_GROUPS = (
    ("potato", ("potato", "potatoes", "sweet potato", "sweet potatoes"),
     "Cook %(one)s rather than eating %(them)s raw: a raw potato and any green patch on it "
     "carry solanine, which gives stomach ache and vomiting, and the raw starch is hard to "
     "digest. Boil, roast or mash %(them)s, and bin any potato with green patches or sprouts."),
    # Yam, plantain and cassava are starchy like a potato but they carry no solanine, so the
    # reason is the starch and the taste. Cassava is the one that matters: raw it carries cyanide.
    ("starchy", ("yam", "yams", "cassava", "plantain", "plantains"),
     "Cook %(one)s rather than eating %(them)s raw: the starch is hard to digest uncooked and "
     "%(one)s tastes bitter and astringent raw. Boil, roast or fry %(them)s until tender, and "
     "peel cassava and cook it right through - raw cassava carries cyanide, and boiling or "
     "frying is what takes it out."),
    ("dried-bean", ("kidney beans", "red kidney beans", "cannellini beans", "haricot beans",
                    "black beans", "pinto beans", "butter beans", "soya beans", "soy beans",
                    "flageolet beans", "chickpeas", "chick peas", "black-eyed beans"),
     "Dried %(one)s have to be boiled hard for at least ten minutes: raw and undercooked ones "
     "carry a protein that causes violent vomiting and cramps, and a slow cooker never gets hot "
     "enough. Tinned ones are already cooked, so rinse and eat them."),
    ("green-bean", ("green beans", "runner beans", "broad beans", "french beans",
                    "string beans"),
     "Cook %(one)s rather than eating them raw: they hold a protein that upsets the stomach, so "
     "boil or steam them four to five minutes until they are tender but still squeaky. A handful "
     "raw in a salad is not dangerous for most people, but they taste better cooked."),
    ("salad", ("broccoli", "cauliflower", "kale", "spinach", "peas", "mangetout",
               "sugar snap peas", "carrot", "carrots", "cucumber", "courgette", "courgettes",
               "beetroot", "onion", "onions", "spring onion", "spring onions", "mushroom",
               "mushrooms", "cabbage", "red cabbage", "sweetcorn", "sweet corn", "pepper",
               "peppers", "bell pepper", "celery", "radish", "radishes", "lettuce", "fennel",
               "avocado", "tomato", "tomatoes", "cress", "watercress", "rocket", "leek",
               "garlic", "ginger", "parsnip", "swede", "turnip"),
     "%(Cap)s %(are)s fine raw: wash %(them)s and eat %(them)s as %(they)s %(are)s - the "
     "crunch and the vitamins are what cooking takes out. A minute in boiling water softens "
     "%(them)s if you would rather have %(them)s cooked."),
)

# Plural names are the ones a person says with "they": "raw peas" and "raw carrots" but "raw
# broccoli", "raw sweetcorn". A name that ends in -s but names one thing is spelled out here
# rather than guessed at.
_RAW_VEG_PLURAL_S = frozenset(("sweetcorn", "sweet corn", "cress", "watercress", "mangetout"))

# Longest first: "sweet potato" and "green beans" have to win over the "potato" and "bean" inside
# them, or the answer is about the wrong vegetable.
_RAW_VEGETABLE_NAMES = tuple(sorted(
    (name for _, names, _ in _RAW_VEG_GROUPS for name in names), key=len, reverse=True))

_RAW_VEG_ONE = dict((name, (group, text)) for group, names, text in _RAW_VEG_GROUPS
                    for name in names)

# Cooking, keeping and shopping lines name a vegetable without asking about eating it raw, and the
# sprout already has its own row above.
_RAW_VEGETABLE_NOT = (
    "how long", "how do i cook", "how to cook", "how long to cook", "how long do i cook",
    "recipe", "recipes", "roast", "roasting", "roasted", "boil", "boiling", "boiled", "steam",
    "steaming", "fry", "frying", "fried", "air fry", "air fryer", "slow cooker", "soup",
    "curry", "stew", "bake", "baking", "baked", "microwave", "grow", "growing", "grown",
    "plant", "planting", "garden", "allotment", "seed", "seeds", "harvest", "blight",
    "fridge", "freezer", "freeze", "keeping", "keeps", "keep", "store", "shop", "buy",
    "cheapest", "price", "calories", "protein", "fibre", "vitamin", "nutrition", "diet",
    "sprout", "sprouts", "alfalfa", "beansprouts", "bean sprouts", "green potato",
    "green potatoes", "solanine", "dog", "dogs", "puppy", "cat", "cats", "kitten",
    # not a bare "pet" or "pets": `_misspelt_avoid` reads "peas" as a misspelling of "pets", and
    # that stood the row down for every "can i eat raw peas" line there is.
    "vet", "rabbit", "hamster", "guinea pig", "bird", "chicken", "chickens",
)


def _raw_vegetable(memory, reading=None):
    """The verdict for the vegetable the line names, in the group it belongs to.

    A raw vegetable question is answered by which vegetable it is, not by which way it was asked:
    "can i eat raw potato" and "raw broccoli" are the same shape and want opposite answers, so the
    reply is chosen from the table above and only the name comes from the line.
    """
    understood = reading if isinstance(reading, dict) else {}
    text = " " + str(understood.get("clean") or "").replace("'s", " ") + " "
    for name in _RAW_VEGETABLE_NAMES:
        if " %s " % name not in text:
            continue
        _, template = _RAW_VEG_ONE[name]
        plural = name.endswith("s") and name not in _RAW_VEG_PLURAL_S
        return template % {"one": name, "Cap": name[:1].upper() + name[1:],
                           "them": "them" if plural else "it",
                           "they": "they" if plural else "it",
                           "are": "are" if plural else "is"}
    return None


OFF_ASKS = ("ok", "okay", "safe", "still", "eat", "eat it", "bin", "throw", "use", "use it",
            "fine", "smell", "smells", "smelly", "sour", "bad", "should i keep", "should i",
            # The evidence is the ask when a person states it and asks nothing else: "my
            # chicken has gone slimy" says a slimy feel and nothing more, and it got the chat
            # nod while "my chicken has gone slimy is it ok" got the answer. The same for the
            # other words these answers name as the test - a tacky or sticky feel, a musty
            # smell, grey-green patches - because each one is the spoilage question in its
            # plainest form and none of them names a second thing the row could be about.
            "slimy", "slime", "slimy feel", "tacky", "musty", "discoloured", "discolored",
            "grey green", "grey-green", "green patches", "gone slimy", "is slimy",
            "off", "gone off", "going off", "go off", "went off", "gone bad",
            "how do i know", "how can i tell", "how do you tell", "know if", "tell if",
            # The freshness side of the same test, and it was getting the baking time for
            # fillets ("how do i know if fish is fresh") and a rod licence ("how can i tell if
            # fish is fresh"). A bare "fresh" is here too because "is my salmon fresh" has no
            # other ask word in it at all.
            "fresh", "is fresh", "still fresh", "smells fresh", "looks fresh", "fresh to eat",
            "fresh enough", "is it fresh", "fresh or not",
            # The date on the packet in the words people use for it. "is my ham out of date" is
            # the same question as "is my ham still ok", and the rows missed every one of them
            # because the ask only knew the still/smell shapes. A row still needs its food word,
            # so a passport or a car insurance renewal cannot reach these.
            "out of date", "past its date", "past the date", "past their date",
            "use by", "use by date", "best before", "gone past",
            # A day word is the same test asked about last night's dinner: "is it ok to eat
            # chicken the next day" names the food and asks whether it is still good, and it
            # reached no row here - it took the lean-protein card and then a shrug, while "is
            # chicken still ok" had the answer all along.
            "next day", "the next day", "the day after", "day after", "day later",
            "days later", "yesterday", "in the fridge", "out of the fridge",
            # A food that has *gone* is the report of a sign, not a question, and it is the whole
            # question a person has: "my chicken has gone slimy" was "Thanks for telling me" -
            # the shrug STYLE.md names - because none of the words above is a way of asking. The
            # sign itself is the ask: nobody says "my chicken has gone slimy" for any reason but
            # to be told whether to bin it.
            "slimy", "gone slimy", "went slimy", "is slimy", "looks slimy",
            "smells off", "smelt off", "smells wrong", "smells funny", "has gone",
            "gone bad", "has gone bad", "looks off", "is off")

# A bare "off" is also a preposition, and those lines are about something else: the skin off a
# fish, the smell of frying off the kitchen, the pan off the heat. Each keeps its own answer.
OFF_THE_THING = ("off the", "off my", "off your", "off his", "off her", "off its", "off them",
                 "off it", "cut off", "cutting off", "chop off", "chopping off", "slice off",
                 "skin off", "take the skin", "fat off", "off the bone", "turn off", "turned off",
                 "switch off", "switched off", "day off", "days off", "time off", "off work",
                 "off sick", "show off", "better off", "worse off", "off the menu", "off the heat",
                 "off the hob", "off the plate")

# The smell, look and date words that make a food line a spoilage question.
OFF_WORDS = PACK_DATE + (
             "still ok", "still ok to eat", "still good", "ok to eat", "okay to eat", "gone off",
             "going off", "off", "smells", "smell", "smelly", "slimy", "funny", "bad",
             # The feel and the look, next to the smell and the slime: "my chicken is tacky"
             # and "the ham is musty" name the same test as "my chicken smells" and reached
             # no row at all. These three are the words the answers themselves name as the
             # sign, and none of them is a cooking word, so a method question cannot reach a
             # row through one ("sticky" is left out for that reason - sticky rice, sticky
             # toffee and sticky ribs are all method questions).
             "tacky", "musty", "discoloured", "discolored", "grey green", "grey-green",
             "gone bad", "past it", "past its date", "is it safe", "safe to eat",
             # The words on the packet. "is my ham out of date" is the spoilage test in the
             # most common phrasing there is, and it reached no row at all: "past its date"
             # was the only date phrase in this list.
             "out of date", "past the date", "past their date", "use by", "use by date",
             "best before", "gone past", "gone past its date",
             # the freshness side of the same test
             "fresh", "is fresh", "still fresh", "smells fresh", "looks fresh", "fresh to eat",
             "fresh enough", "is it fresh", "fresh or not",
             # The day words are the same test about last night's dinner, and they belong in the
             # key rather than only in the ask: "is salmon ok the next day" names the fish and
             # asks with a bare "ok" and nothing else, which scores below the threshold, so it
             # reached no row at all while "is salmon still ok" was answered.
             # "tomorrow" is the same test in the words people type most, and it is here because
             # a food with no keeping row had no other answer: "can i eat the chicken tomorrow"
             # was "I don't know enough to answer that honestly" while "is the chicken ok the next
             # day" was answered, and the two are the same question. The ask gate keeps it off
             # "can i keep cooked prawns for tomorrow", which is a how-long line.
             "next day", "the next day", "the day after", "day after", "yesterday", "tomorrow",
             "tomorow", "tmrw", "tomoz",
             "in the fridge", "out of the fridge",
             # "is chicken ok after 3 days" says the day as a count, and it shares no phrase
             # with any of the above. The numbers people say are the same few, so they are
             # spelled out here as the one rule they are.
             "after a day", "after one day", "after 2 days", "after two days", "after 3 days",
             "after three days", "after 4 days", "after four days", "after 5 days",
             "after five days", "a couple of days later", "a few days later",
             # "should i bin my chicken", "do i need to throw the mince away". The decision is
             # the state as far as the person asking is concerned: they have already decided the
             # food is suspect and want the signs. The row scored nothing at all on these, so
             # they fell to the composer's "not mine to decide" shrug.
             "bin", "bin it", "throw", "throw it", "throw away", "throw out", "chuck",
             "toss", "chuck it", "toss it",
             # "can i still eat this chicken" is the same question as "is this chicken still ok",
             # and it scored nothing: "still" and "eat" are ways of asking, not signs, so no
             # state word was in the line and the row never fired. The eating shapes are signs
             # too - a line that offers to eat the thing is asking about the thing in its hand.
             "still eat", "eat this", "eat that", "can i eat", "still alright",
             "still all right", "alright")

# A spoilage question is a yes/no about safety, and the row that can answer it has to beat the
# row that only describes the food. On main it lost every tie: "my chicken smells a bit, can i
# cook it" got the room-smell card (open a window and simmer a lemon), "my pork smells can i cook
# it" the same, "is my chicken still ok to eat" the lean-protein card, and "my chicken went out of
# date yesterday can i eat it" the keeping card. Every one of those is a row that scored the same
# as this one - the food word and one ask word each - and a tie was enough to take the turn. A
# person asking whether the food in their hand is safe is asking the one question where a dull,
# wrong answer does real harm, so these rows are nudged above anything they tie with. The gates
# above are what keep them off the lines that are not about spoilage.
SPOILAGE_BIAS = 3

# The foods the knowledge base already has a card for. A line that names one of these has its
# own answer and must keep it: the row below is for the lines that name no food at all.
EXTRA_FOODS = ("yogurt", "yoghurt", "cream", "soured cream", "single cream", "double cream",
               "ham", "gammon", "leftover", "leftovers", "pate", "smoked salmon", "prawn",
               "prawns", "sausage", "sausages", "burger", "burgers", "milk", "kefir")


def _names_no_food(understood):
    """True when the line names no food, so the unnamed spoilage row is the one to answer.

    "smells off can i still cook it" has nothing to look up, so the questions below are the whole
    question. "my milk smells a bit off, should i still use it" names the milk, and the milk card
    says more about it than any general rule can; without this test the general row took that
    line and gave back a rule about rice and hard cheese.

    The pantry table is read here rather than imported at the top of the file, because it is
    built from this module's own tables and the import would go round in a circle.
    """
    from . import meals
    understood = understood if isinstance(understood, dict) else {}
    words = {str(word).lower() for word in (understood.get("words") or ())}
    text = " " + str(understood.get("clean") or "").lower() + " "
    known = meals.IN_A_DISH | set(meals.INGREDIENTS) | set(EXTRA_FOODS)
    if any(word in known for word in words):
        return False
    # A pantry name of two words ("soured cream", "coconut milk") is never one word of the line.
    return not any(name in known and (" %s " % name) in text for name in known)


# A food that is bad for you is a nutrition line, never a spoilage one. Shared by every row so
# the gate is one list; "is ham processed meat bad" was being answered with a slimy-ham test.
DIET_WORDS = ("every day", "a day", "a week", "per day", "per week", "healthy", "unhealthy",
              "good for you", "bad for you", "diet", "dieting", "processed", "nutrition",
              "nutritious", "protein", "calories", "vitamins", "how many", "too much",
              "too many", "pregnant", "pregnancy", "listeria", "cholesterol", "diabetic",
              "diabetes", "allergic", "allergy", "intolerant", "lactose", "toddler", "baby",
              "for a toddler", "for a baby")

# Raw and undercooked lines ask how to cook the food. "Is it safe to eat raw pork" answered
# with a spoilage test reads as permission, so every row stands down for these.
# "Rare" belongs here with the other doneness words: the spoilage rows are about a smell, a
# slime and a colour, and "is it safe to eat rare steak" is a question about the middle of the
# meat, which the whole-cut row answers. Without it the spoilage card won that line on score.
RAW_WORDS = ("raw", "undercooked", "undercook", "underdone", "bloody", "raw inside",
             "pink in the middle", "still pink", "not cooked through", "rare", "medium rare",
             "blue steak")

# A bare "pink" is the same question said without the "still", and on meat it is a cooking
# question: "is it ok to eat pink chicken" and "is it safe to eat pink beef" were the freshness
# test, which reads as a yes. The cooking rows answer those, so the two rows about meat stand
# down for it. Cured meat and yogurt keep `RAW_WORDS`: pink ham is what ham looks like, and the
# freshness test is the answer a person asks for by saying it.
UNDERCOOKED_PINK = RAW_WORDS + ("pink",)

# Reheating, defrosting, the number of days in the fridge and "why does it go mouldy" all have
# their own answers in `cooking.py`. A spoilage test given instead loses the number asked for.
# A texture complaint is the same mistake the other way round: "my chicken is dry, is it safe"
# is the 75C answer about dry meat, and no amount of smelling finds a texture fault.
_NOT_THIS = ("frozen", "defrost", "defrosting", "thaw", "thawing", "left out", "overnight",
             # Buying is not keeping: "should i buy chicken tomorrow" is a shopping question
             # and it was answered with the slimy-chicken test once "tomorrow" joined the key.
             "buy", "buying", "to buy", "shop for", "shopping list",
             "room temperature", "reheat", "reheating", "reheated", "heat up", "heated up",
             "warm up", "microwave", "warm through", "piping hot", "fridge",
             # The number of days is the keeping question and it has its own card with the
             # number in it, so "how many days does chicken last" stands this test down. A
             # bare "day" is not the same thing: "is it ok to eat chicken the next day" is
             # the verdict, asked about last night's dinner, and it was turned away here and
             # then lost to the lean-protein card and a shrug.
             "how many days", "how many day", "does it last", "do they last", "will it last",
             "days in the fridge", "day in the fridge", "days in a fridge",
             "how long", "why", "what causes", "cause",
             # "how do i keep chicken fresh" is a keeping question, and it was reaching the
             # spoilage test once "fresh" joined the asks. "should i keep" stays an ask.
             "how do i keep", "how do i store", "how to keep", "how to store",
             "how can i keep", "how should i keep", "how can i store",
             "dry", "dried out", "overcooked", "rubbery", "tough", "chewy",
             # a meat or a fish that is going back in the freezer is the refreezing question, not
             # the sniff test: "is it safe to refreeze meat" was the colour-of-a-chop card,
             # because this row names the meat and carries the bias that settles the tie
             "refreeze", "refroze", "re-freeze", "refreezing", "freeze again", "frozen again",
             # A food somebody was sold already past its date is a complaint to the shop, not a
             # sniff test: "the shop sold me out of date chicken" wants the refund, and it was
             # reaching the chicken card once the spoilage rows stopped losing their ties. Any
             # way of saying "I bought it like this" stands these rows down; "i bought chicken
             # yesterday, is it still ok" keeps every word and is still the spoilage question.
             "sold me", "sold us", "sold it to me", "refund", "money back", "take it back",
             "take them back", "bring it back", "return it", "bought it like that",
             "illegal to sell", "sell food", "selling food", "sell by", "complaint",
             "complain", "bought out of date", "bought it out of date", "bought this out of date",
             "buying out of date", "out of date when i bought", "was out of date when i bought",
             # Freezer burn is the one patch of food that looks wrong and is safe, and the
             # freezer's own card says so: "is it safe to eat freezer burnt meat" was the
             # red-meat sniff test once these rows stopped losing their ties, which is the
             # opposite of the answer. The freezer-burn row is the answer to this one.
             "freezer burn", "freezer burnt", "freezerburn", "freezer-burn", "freezer burned",
             "frost bitten", "frostbite")

# Unripe fruit and vegetables are safe: hard, sour and starchy rather than sweet, and not
# poisonous. It is asked in exactly the words of the spoilage questions - "is it ok to eat unripe
# tomatoes", "are green tomatoes safe", "can i eat unripe mango" - and every one of them was a
# shrug on main. The one green thing that genuinely is dangerous, a green potato, has its own row
# in `cooking.py`, and the words that ask for it are kept off this one.
UNRIPE_WORDS = ("unripe", "unripened", "underripe", "under ripe", "not ripe", "isnt ripe",
                "green tomatoes", "green tomato", "green bananas", "green banana",
                "green plums", "green mango", "hard avocado", "hard mango", "hard peach",
                "hard peaches", "hard pears")
UNRIPE_NOT = ("potato", "potatoes", "solanine", "chutney", "relish", "recipe", "recipes",
              "make", "making", "cook", "cooking", "cook them", "fried green", "fry",
              "how do i ripen", "ripen them", "get them to ripen", "plant", "growing", "grow",
              "shop", "buy", "pick", "when to pick", "harvest", "blight", "garden")

# Who gets food poisoning from a chicken is a question about the germ, not about a claim, and the
# claim card was answering it with the council's environmental health team. The germ that matters
# in the UK is campylobacter, and the answer is heat, not smell.
POISONING_WORDS = ("food poisoning", "poisoning", "campylobacter", "salmonella", "listeria",
                   "give you", "give me", "make you ill", "make you sick", "make me ill",
                   "make me sick", "get ill", "get sick", "harmful", "carry", "causes",
                   "cause food", "why is it bad", "why is chicken bad", "why dangerous")
POISONING_NOT = ("how long", "how many days", "how do i cook", "how do i cook it", "cook it",
                 "cooking time", "roast", "roasting", "temperature", "defrost", "defrosting",
                 "thaw", "thawing", "freeze", "freezing", "fridge", "freezer", "rice",
                 "left out", "reheat", "reheating", "i have", "i got", "i ate", "i think i",
                 "my stomach", "diarrhoea", "vomiting", "symptoms", "treatment", "how to treat",
                 "restaurant", "takeaway", "cafe", "pub", "wedding", "buffet", "kebab",
                 "gave me", "made me", "report", "complaint", "claim", "compensation",
                 "sue", "advice", "what should i do")

# Mince has a keeping row of its own, and this one is about red meat that forgives: the two give
# opposite advice, so a keeping question about mince leaves the chop behind. "is the mince off"
# keeps it, because the freshness test is this row's own line.
MINCE_WORDS = ("mince", "minced", "mincemeat", "mince meat", "ground beef", "ground meat",
               "ground lamb", "ground pork", "beef mince", "lamb mince", "pork mince",
               "turkey mince", "chicken mince")

# The keeping question about mince is the one that counts days - "is the mince ok the next day",
# "how long does mince keep in the fridge" - and the keeping row has that number. The verdict
# question - "is this mince still ok to eat", "my mince smells a bit is it still ok" - is the
# sniff test, and it was being sent away with the days: "still ok" and "still good" are how the
# verdict is asked, so they are deliberately not here, and `MINCE_VERDICT_WORDS` below says so
# outright. With them the line reached the doneness card about pink centres, which answers what
# temperature mince needs and not whether the pack in the fridge has had it.
MINCE_KEEPING_WORDS = ("day", "days", "next day", "the day after", "day after", "days later",
                       "keep", "keeps", "keeping", "kept", "how long",
                       "ok to eat", "safe to eat", "use by",
                       "yesterday", "tomorrow", "tonight", "left out", "left over", "leftovers",
                       "in the fridge", "out of the fridge", "fridge", "freezer", "frozen")


# A dish in front of the person that is too hot to eat, too spicy or too salty is a fault to
# rescue, and cooking_entries' fix cards own it. The leftovers row is keyed on the dish words and
# "eat", so "my chilli is too hot to eat" was told it keeps 3 to 4 days in the fridge. The fault
# stands the keeping question down.
_A_FAULT_IN_THE_DISH = re.compile(
    r"\b(?:too (?:hot to eat|hot for|spicy|salt\w*|sweet|sour|bland|thick|thin|dry)"
    r"|way too (?:spicy|hot|salty)|less spicy|make it milder|too much (?:chilli|chili|salt|spice)"
    r"|to cool it down)\b")


def _not_a_fault_in_the_dish(understood):
    """False when the line is a fault in the food, which the fix cards answer."""
    said = str((understood or {}).get("clean") or "").lower()
    return not _A_FAULT_IN_THE_DISH.search(said)

# The words that make a mince line the verdict about the pack in the fridge rather than the
# doneness policy: a person asking "is this mince still ok to eat" is holding it, and the answer
# is the sniff test. On its own "ok to eat" is not enough - "is it safe to eat mince" is a
# question about pink middles, and the red-meat doneness row answers it.
MINCE_VERDICT_WORDS = ("still ok", "still good", "still fine", "still safe", "still alright",
                       "still all right", "smells", "smell", "smelly", "slimy", "sour", "off",
                       "gone bad", "gone off", "went off", "looks off", "is off", "green")


def _mince_keeping_is_its_own_row(understood):
    """False when the line is a keeping question about mince, which has a row of its own."""
    said = str((understood or {}).get("text") or (understood or {}).get("clean") or
               " ".join((understood or {}).get("words") or ())).lower()
    said = " %s " % re.sub(r"[^a-z0-9']+", " ", said).strip()
    if not any(" %s " % word in said for word in MINCE_WORDS):
        return True
    if any(" %s " % word in said for word in MINCE_VERDICT_WORDS):
        return True
    return not any(" %s " % word in said for word in MINCE_KEEPING_WORDS)
# A cooked dish is the subject of two different questions: what to do with it (the recipe) and
# whether the one in the fridge is still all right (this row). The words that make it the second
# are the keeping ones; a line with neither is a line about cooking the dish.
_KEEPING_IN_THE_LINE = ("fridge", "freezer", "keep", "keeps", "keeping", "last", "lasts",
                        "ok", "okay", "safe", "still", "next day", "tomorrow", "gone off",
                        "go off", "went off", "smell", "smells", "slimy", "sour", "days",
                        "how long", "bin", "throw", "eat")


# A dish made on a day gone by is the pot in the fridge rather than the recipe, so the day is a
# keeping word when the line asks nothing about cooking: "stew made yesterday can i have it" is
# the leftovers question, and it was answered with the two hours the stew takes to cook.
_PAST_KEEPING = ("yesterday", "last night", "this morning", "days ago", "day ago",
                 "the day before", "a couple of days", "a few days")
_COOKING_ASK = ("what can i make", "what can i do with", "what should i make", "what can i cook",
                "what shall i cook", "what should i cook", "cook tonight", "cook for dinner",
                "make tonight", "recipe", "recipes", "meal idea", "ideas for", "idea for",
                "how do i make", "how to make", "how do i cook", "how to cook", "cook it",
                "reheat", "re-heat", "use up", "using up", "what goes with", "serve with",
                "side for", "freeze")


def _not_a_recipe_now(understood):
    """False for "what can i make with the leftover curry", true for "is the curry still ok"."""
    text = " ".join(str((understood or {}).get("clean") or "").lower().split())
    # The cooking ask is read first: "we had curry last night what can i cook tonight" carries
    # "ok" inside "cook" and "last" inside "last night", so the keeping words matched it and the
    # pot in the fridge answered a line that asks for tonight's dinner.
    if any(word in text for word in _COOKING_ASK):
        return False
    if any(word in text for word in _KEEPING_IN_THE_LINE):
        return True
    return any(word in text for word in _PAST_KEEPING)


# How many days ago the dish was cooked or put in the fridge, for the row that answers the
# leftover. "can i eat stew that was made 4 days ago" is answered "a cooked dish keeps 3 to 4
# days" and left there: the rule is given and the person's own dish is not. The count is what
# turns the rule into the verdict, so it is read here in the words people use for it - the number
# in front of "days ago", and the plain phrases for the same thing.
_COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fourteen": 14,
                "a couple of": 2, "a few": 3, "a": 1}
_DAYS_AGO = re.compile(
    r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fourteen)"
    r"\s+days?\s+(?:ago|old|since)\b|"
    # "been in the fridge for 4 days", "sat in there 3 days", "in the fridge 2 days"
    r"\b(?:in the fridge|in there|sat there|sitting there|been there|in the pot|in the tub)"
    r"(?:\s+(?:for|about|nearly|over))?\s+(\d{1,2}|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|eleven|twelve|fourteen)\s+days?\b|"
    r"\b(?:made|cooked|did it|made it|cooked it)\s+(\d{1,2}|one|two|three|four|five|six|seven|"
    r"eight|nine|ten|eleven|twelve|fourteen)\s+days?\b", re.I)
_DAYS_SAID = (
    ("the day before yesterday", 2), ("yesterday", 1), ("this morning", 0), ("last night", 1),
    # "is leftover curry ok to eat the next day": the dish is from today, and the question is
    # about tomorrow, so the day asked about is the first one the rule allows.
    ("tomorrow", 1), ("the next day", 1), ("next day", 1),
    ("a couple of days", 2), ("two days", 2), ("a few days", 3), ("three days", 3),
    ("a week", 7), ("a fortnight", 14), ("a month", 30),
)


def _how_many_days_ago(text):
    """The day count the line gives for the dish, or None when the line gives none."""
    match = _DAYS_AGO.search(text)
    if match:
        said = next(part for part in match.groups() if part)
        number = _COUNT_WORDS.get(said.lower())
        return int(said) if number is None else number
    for phrase, days in _DAYS_SAID:
        if phrase in text:
            return days
    return None


# What makes a line the question the verdict answers. A statement about the pot - "i made a curry
# last night", "i went for a curry last night" - already gets the rule and is left alone; only a
# line that asks gets a yes or a no in front of it.
# "leftover stew made yesterday ok" ends on the ask itself, with no verb in front of it, and got
# the rule with no verdict because none of the asks below is in it. A line that ends on one of
# these words is asking, whatever it starts with; a statement about the pot does not end on one
# ("i made a curry last night").
_ENDS_ON_AN_ASK = re.compile(r"\b(?:ok|okay|alright|all right|safe|edible)\s*[.!]*$", re.I)
_VERDICT_ASKS = ("can i", "could i", "should i", "shall i", "do i", "is it", "is that", "is this",
                 "will it", "would it", "are they", "does it", "ok to", "okay to", "safe to",
                 "still ok", "still good", "still fine", "am i ok", "too late", "gone off")

# The keeping rule for a cooked dish, and the same rule said as a verdict about the day count.
# "At the edge" is deliberate on the fourth day: 3 to 4 days is a range, so the fourth day is the
# last one the bot will call fine, and it says which way it would go rather than hedging.
def _the_verdict_on_the_days(days):
    if days is None:
        return ""
    if days <= 0:
        return "Yes - it is from today or last night, so it is fine."
    if days == 1:
        return "Yes - a day in the fridge is nothing, so it is fine."
    if days <= 3:
        return ("Yes - %d days is inside the 3 to 4 days a cooked dish keeps in the fridge, so it "
                "is fine." % days)
    if days == 4:
        return ("At the edge, I'm afraid: 3 to 4 days is the limit, so today is the last day I "
                "would eat it and I would not leave it for tomorrow.")
    return ("No, I would not: a cooked dish keeps 3 to 4 days in the fridge, and rice only 1, so "
            "%d days is past it." % days)


_LEFTOVERS_RULE = ("Cooled within two hours and kept covered in the fridge, a cooked dish keeps 3 "
                   "to 4 days, and anything with rice in it only 1. Reheat only the portion you "
                   "are eating, once, until it is piping hot right through - a second reheating is "
                   "where people get caught. It is past it if it smells sour or looks slimy, and "
                   "if it sat out warm for more than 2 hours, bin it whatever it looks like.")


def _the_leftovers_answer(memory, reading):
    """The keeping rule, opened by the verdict on the days this line gives.

    A verdict is an answer to a question, so it is only given to one: "i made a curry last night"
    is news about the pot rather than a question about it, and a "Yes - a day in the fridge is
    nothing" in front of the rule would be answering something nobody asked.
    """
    from .lookup import the_line

    reading = reading if isinstance(reading, dict) else {}
    said = " ".join(str(reading.get("clean") or "").lower().split())
    asked = (any(word in said for word in _VERDICT_ASKS)
             or "?" in str(reading.get("text") or "")
             or bool(_ENDS_ON_AN_ASK.search(said)))
    if not asked:
        return _LEFTOVERS_RULE
    verdict = _the_verdict_on_the_days(_how_many_days_ago(the_line(reading)))
    if not verdict:
        return _LEFTOVERS_RULE
    if verdict.startswith("No"):
        return verdict + (" Reheating does not make it safe: the toxins old food builds up do not "
                          "all break down with heat and they do not all smell.")
    return verdict + " " + _LEFTOVERS_RULE



# "Left over" is a dish in one line and a sum of money in the next, and "each month" fits both:
# `i have 200 left over each month` is a budgeting question, and the dish-and-period rows read
# the money as a dish and the month as a fridge life, so they answered "past it, I'm afraid -
# bin it". A guard is the right shape here rather than another word on each `avoid`, because the
# money can be said a hundred ways ("£200 spare", "30 quid over", "what is left after the rent")
# and every one of them is the same fact about the line.
_MONEY_IN_THE_LINE = re.compile(
    r"[£$€]\s?\d|\b\d+\s?(?:pounds?|quid|dollars?|euros?|bucks?)\b|"
    r"\b(?:money|budget|pay|paid|payday|salary|wages?|savings?|income|pension|"
    r"rent|mortgage|bills?|overdraft|debt|direct debit|standing order)\b|"
    # a sum this size is not a portion: "200 left over" is money a hundred times for every time
    # it is sausages, and the dish rows only need to stand down when they cannot be sure
    # "leftover" written as one word is the same sum, and it was the spelling that got through:
    # `i have 200 leftover each week` was told "past it, I'm afraid - bin it" while the spaced
    # twin got the budgeting card
    r"\b\d{2,}\s*(?:left ?overs?|spare|over a month|over each|over every)\b|"
    # and "each"/"every"/"per" with a period is a habit of money rather than a date on food:
    # a dish is left in the fridge for "a week", never "each week"
    r"\b(?:left ?overs?|spare)\b[^?.!]{0,20}\b(?:each|every|per)\s+(?:week|month|year|payday)\b")


def _not_about_money(understood):
    """Whether the sum in the line is something to keep rather than something to eat."""
    if not isinstance(understood, dict):
        return True
    said = " ".join(str(value) for value in (understood.get(key) for key in
                                             ("clean", "norm_text", "text", "plain"))
                    if isinstance(value, str)).lower()
    return _MONEY_IN_THE_LINE.search(said) is None

ENTRIES = (
    # "can you get food poisoning from chicken" was reaching the claim card in consumer.py, which
    # answered a person asking about a germ with "report it to the council". The words a person
    # uses for the germ are not the words for the claim: the claim says where they ate and what
    # they lost, and this one names the chicken and asks whether it is dangerous at all.
    entry("chicken-food-poisoning", (("chicken", "chickens", "turkey"),
                                     POISONING_WORDS),
          "Yes - chicken is the commonest source of food poisoning in Britain, because "
          "campylobacter lives on the raw meat and a drop of the juice is enough to make you ill. "
          "Heat is what kills it: cook chicken right through to 74C in the thickest part, don't "
          "wash it raw (that splashes the bacteria round the sink), keep it away from anything you "
          "eat uncooked, and wash your hands, the board and the knife afterwards. Symptoms come 1 "
          "to 3 days later, usually cramps and diarrhoea for about a week, and the thing that "
          "matters is fluid; blood in it, a high fever or a week with no improvement is a GP.",
          # the pet words are spelled out rather than PET_LINE_WORDS: that list carries
          # "poisoned", whose loose forms include "poisoning", and it stood this row down for the
          # exact question it answers. A dog that ate the chicken is still the vet's line.
          avoid=POISONING_NOT + DIET_WORDS + _NOT_THIS + OFF_THE_THING + RAW_WORDS
          + ("dog", "dogs", "puppy", "cat", "cats", "kitten", "pet", "pets", "vet",
             "swallowed", "swallow", "chewed", "choking", "choke", "vomiting"),
          # the claim card in consumer.py holds "food poisoning" and "chicken" too. The avoid
          # list above is what keeps the claim lines themselves on the claim card, so this row
          # only needs to be preferred where the germ is the question.
          bias=6),
    # Tomatoes, potatoes and rhubarb carry solanine in their leaves and stems, and every one of
    # these lines was a plant-care answer: "are tomato leaves poisonous" got the yellow-leaves
    # feed card, which reads as though the leaves were food.
    entry("plant-leaves-poisonous",
          (("tomato leaves", "tomato leaf", "tomato plant leaves", "tomato stems",
            "potato leaves", "potato leaf", "potato shoots", "potato sprouts",
            "rhubarb leaves", "rhubarb leaf", "aubergine leaves", "courgette leaves"),
           ("poison", "poisonous", "toxic", "toxic to", "safe to eat", "safe to feed",
            "edible", "can i eat", "can you eat", "eat them", "eat the leaves", "harmful",
            "dangerous", "eat it")),
          "The leaves and stems of tomatoes, potatoes and rhubarb contain solanine and oxalic "
          "acid, which are mild poisons: a stray leaf in a salad will do you no harm, but a "
          "plateful brings a stomach ache, sickness and diarrhoea, and cooking does not destroy "
          "it. So don't eat them and don't brew them as tea, wash your hands after handling the "
          "plants, and keep pets and small children away from the leaves. The fruit, the tubers "
          "and the rhubarb stalks are the parts that are food.",
          avoid=("yellow", "yellowing", "pale", "blight", "spots", "curl", "curling", "wilt",
                 "wilting", "holes", "black", "brown", "feed", "fertiliser", "compost", "prune",
                 "pruning", "grow", "growing", "harvest", "plant them", "when to plant"),
          bias=2),
    entry("still-chicken", ("chicken", OFF_WORDS),
          "Chicken is the one to be strict about: a sour or ammonia smell, a tacky or slimy feel, "
          "or any change of colour means bin it, and cooking it will not make it safe. Raw chicken "
          "keeps 1 to 2 days in the fridge and cooked chicken 3; if it has sat out warm for more "
          "than 2 hours, that is enough on its own.",
          avoid=DIET_WORDS + UNDERCOOKED_PINK + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING,
          ask=OFF_ASKS, bias=SPOILAGE_BIAS),
    entry("still-meat", (("meat", "beef", "lamb", "pork", "steak", "mince", "joint"), OFF_WORDS),
          "Red meat is more forgiving than chicken: a grey-brown colour on the outside of a chop "
          "is just air and it is fine, but a sour or putrid smell, a sticky tacky surface or "
          "green patches means bin it. Raw beef, lamb and pork keep 3 to 5 days in the fridge, "
          "mince only 1 to 2.",
          # Mince is the red meat that is not forgiving, and its own row says so: "is the mince ok
          # the next day" was answered "a grey-brown colour on the outside of a chop is just air
          # and it is fine", which is the one thing a chop's advice must not say about mince. The
          # keeping question about mince leaves this row; the freshness question keeps it.
          guard=_mince_keeping_is_its_own_row,
          avoid=DIET_WORDS + UNDERCOOKED_PINK + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING,
          ask=OFF_ASKS, bias=SPOILAGE_BIAS),
    entry("still-fish", (("fish", "salmon", "cod", "prawns", "prawn", "haddock", "tuna",
                          # "how do i know if fish is off" is the same question as "is the fish
                          # off", and it was reaching the cooking method and the rod licence
                          # instead: a phrase that names the food and the state wins a tie.
                          "fish is off", "fish off", "fish gone off", "fish has gone off",
                          "salmon is off", "prawns are off", "fish gone bad", "fish is bad",
                          # the freshness side, which reached a rod licence: "how can i tell if
                          # fish is fresh" is the same question as "is the fish off".
                          "fish is fresh", "fish fresh", "salmon is fresh", "salmon fresh",
                          "prawns are fresh", "cod is fresh"),
                         OFF_WORDS),
          "Fish goes off faster than anything else and does not forgive it: it should smell of the "
          "sea, so an ammonia or fishy-sharp smell, flesh that stays dented when you press it, or "
          "grey gills means bin it. Use it the day you buy it or freeze it that day.",
          # the smell of fried fish in the kitchen is a cooking-smell question, not this one
          avoid=DIET_WORDS + RAW_WORDS + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING
          + ("kitchen", "fried", "frying", "fry", "get rid of the smell", "smell out",
             # a fish tank that smells is the tank's question, and the fish in it is alive:
             # "my fish tank smells" was told how to tell a fish that has gone off
             "tank", "fish tank", "aquarium", "goldfish", "pond", "ponds", "fish bowl",
             "tropical fish", "pet fish", "fish tank water",
             # ... and "my dishwasher smells of fish" is the appliance's question: a machine
             # that smells is a clean-the-filter job, whether the word in the line is fish,
             # prawns or last night's curry.
             "dishwasher", "washing machine", "fridge", "freezer", "oven", "microwave", "sink",
             "bin", "bins", "bin smells", "cupboard smells", "room smells", "house smells",
             "smells of fish", "smells like fish", "smelling of fish",
             # how often is not how fresh: "how often can i eat tuna" and "how often can i eat
             # salmon" were told how to tell a fish that has gone off. How many days it keeps is
             # still this row's question, so the frequency is what stands it down.
             "how often", "a week", "per week", "every day", "every other day", "twice a week",
             "three times a week", "times a week"),
          ask=OFF_ASKS, bias=SPOILAGE_BIAS + 1),
    entry("still-ham", (("ham", "bacon", "sausage", "sausages", "salami", "chorizo"), OFF_WORDS),
          "Cured meat is not immune: a slimy feel, a sour or musty smell, or grey-green patches "
          "means bin it. Ham keeps about 3 days once the pack is open, dry-cured bacon up to a "
          "week, and sausages 2 to 3 days.",
          avoid=DIET_WORDS + RAW_WORDS + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING,
          ask=OFF_ASKS, bias=SPOILAGE_BIAS),
    entry("still-yogurt", (("yogurt", "yoghurt", "cream", "creme fraiche", "soured cream"),
                           OFF_WORDS),
          "Bin it if it smells sour or fizzy rather than tangy, or if there is any mould on the "
          "surface; a little watery separation on top is fine, so stir it back in. Cream keeps "
          "about 5 days once opened, and yogurt a week past its date if it has been in the fridge.",
          # a cream for the skin is not a cream for the fridge: "does sun cream go off" was told
          # to stir it back in, and "has my moisturiser gone off" the same
          avoid=DIET_WORDS + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING
          + ("sun cream", "suncream", "sunscreen", "sunblock", "moisturiser", "moisturizer",
             "face cream", "hand cream", "body cream", "eczema cream", "nappy cream",
             "shaving cream", "cold cream", "ice cream", "eye cream", "facial cream", "spot cream",
             # A yogurt question that names the date is the date rule, which says how long an
             # opened and an unopened tub keep and ends with the same sniff test; the verdict
             # card has the bin rule and no number, so the date question keeps its own card.
             "out of date", "past the date", "past its date", "past their date", "use by",
             "use by date", "best before", "date on the lid", "went out of date",
             # A sourdough starter is a jar of flour and water on the counter, not a pot in the
             # fridge, and comparing its smell to a yoghurt is how people describe a healthy one:
             # "my starter smells like yoghurt" was told "bin it if it smells sour or fizzy rather
             # than tangy". The starter rows know a yoghurt smell is good, so a starter names
             # another question and stands this row down.
             "starter", "starters", "sourdough", "ginger bug", "kombucha scoby"),
          ask=OFF_ASKS, bias=SPOILAGE_BIAS),
    # The foods nothing else knows: "is my tofu out of date" and "is my avocado out of date" were
    # the dried fruit row, and a general card that says which of the two dates matters is a far
    # better answer than a punt. It sits at bias -3 so a row that knows the food always wins.
    entry("still-date-rule", (("out of date", "past its date", "past the date", "past their date",
                               "use by", "use by date", "use-by", "best before", "best-before",
                               "gone past", "after the date", "date on it", "date on the",
                               "still edible"),
                              # the date phrase is the whole gate, so the second part is only the
                              # shape of the question: without it the phrase counted once and the
                              # row never reached the threshold
                              ("is my", "is it", "is this", "is that", "are my", "are these",
                               "my", "still", "ok", "safe", "good", "edible", "eat", "keep",
                               "bin", "throw", "use")),
          "Two dates mean two things: use-by is about safety, so the food goes in the bin after "
          "it, even if it looks and smells fine; best-before is about quality, so dry rice, "
          "pasta, flour and sugar are fine for months past it, and a tin for years. For anything "
          "fresh, smell it and touch it: a sour smell, a slimy surface or mould means bin it, and "
          "cooked food is 2 days in the fridge whatever the label said.",
          # a pet's dinner, a diet question, a shortage ("im out of bread") and a cooked or
          # defrosted line are all somebody else's answer
          avoid=DIET_WORDS + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING + (
                 "out of milk", "out of bread", "out of rice", "out of chicken", "out of cheese",
                 "out of eggs", "out of sugar", "out of flour", "run out", "ran out", "none left",
                 "havent got", "recipe", "how do i cook", "how long to cook", "how long do i cook",
                 "freeze", "defrost", "reheat", "sell by", "expiry",
                 # a date on something that is not food is a different question, and this card
                 # would answer "is my passport out of date" with the use-by rule for a yoghurt
                 "passport", "licence", "license", "driving licence", "mot", "insurance",
                 "warranty", "guarantee", "ticket", "tickets", "coupon", "voucher", "gift card",
                 "card", "cards", "debit card", "credit card",
                 # a car, a van or a bike does not have a use-by date either: "my car is out of
                 # date" was handed the rule for a yoghurt. The phrases name the vehicle and the
                 # date together rather than the vehicle alone, because a person who left the
                 # shopping in a hot car is still asking about the food.
                 "car is out of date", "car out of date", "car is past its", "van is out of date",
                 "van out of date", "vehicle is out of date", "bike is out of date",
                 "tyre", "tyres", "tire", "tires",
                 "membership", "subscription", "battery", "batteries", "smoke alarm", "alarm",
                 "fire extinguisher", "medicine", "medication", "tablets", "inhaler", "epipen",
                 "food bank", "sell by date", "sell-by", "expiry date", "expires"),
          ask=OFF_ASKS, bias=-3),
    # A food that has gone off, with nothing naming which food: "smells off can i still cook it",
    # "this smells a bit off is it ok". The rows above all need a food word and there is none
    # here, so the line reached the room-smell card - a lemon down the sink for a question about
    # whether the dinner is safe. What a friend says does not depend on which food it is: a sour
    # smell is the one sign that means bin it whatever it is. It sits below the rows that name the
    # food, so knowing the food always wins, and it stays off a room, a bin or an appliance, which
    # have their own cards. It sits above the room-smell card, which it tied with on "smells off
    # can i still cook it" and lost.
    entry("still-unnamed",
          (("smells off", "smelt off", "smells funny", "gone off", "has gone off",
            "went off", "smells wrong", "smells a bit off", "gone bad", "has gone bad",
            "looks off", "smells iffy", "smells dodgy"),
           ("can i cook", "can i eat", "cook it", "eat it", "still cook", "still eat",
            "ok to eat", "safe to eat", "is it ok", "is it safe", "use it", "bin it",
            "throw it", "keep it", "should i")),
          "If it smells sour, or wrong rather than just strong, bin it - cooking does not make an "
          "off food safe. Cooked rice, cooked meat and anything with a sauce are the strict ones; "
          "hard cheese and dry bread are the ones you can judge by looking.",
          avoid=("kitchen", "room", "rooms", "house", "flat", "home", "bin", "bins",
                 "drain", "drains", "fridge", "freezer", "oven", "microwave",
                 "dishwasher", "washing machine", "tumble dryer", "sink", "cupboard",
                 "car", "cars", "van", "garage", "loft", "shed", "sofa", "carpet",
                 "dog", "dogs", "cat", "cats", "puppy", "pet", "pets", "vet",
                 "smoke", "damp", "mould", "mold", "musty", "gas", "paint") + PET_LINE_WORDS,
          ask=OFF_ASKS, bias=2, guard=_names_no_food),
    # "safe" on its own is how half these lines are asked - "are green tomatoes safe" matched
    # none of OFF_WORDS, which only carries the phrase "is it safe" and "safe to eat" - so the
    # plain verdict words are in the key too.
    entry("still-unripe", (UNRIPE_WORDS, OFF_WORDS + ("eat", "safe", "ok", "okay", "fine",
                                                     "poison", "poisonous", "toxic", "harm",
                                                     "ill", "sick", "bad for")),
          "Unripe fruit and veg are safe to eat - hard, sour and starchy rather than sweet, not "
          "poisonous - and a day or two on the counter, or in a paper bag with a banana, ripens "
          "most of them; cooking does the rest, as fried green tomatoes and green banana show. A "
          "green potato is the one exception: that green is solanine, it does not cook out, so "
          "bin it.",
          avoid=DIET_WORDS + _NOT_THIS + PET_LINE_WORDS + OFF_THE_THING + UNRIPE_NOT,
          ask=OFF_ASKS + ("eat", "safe", "poison", "poisonous", "toxic", "harm", "ill", "sick"),
          # The bias is what settles the tie with the ripeness rows in keeping.py: "can i eat
          # unripe mango" names a fruit and an unripe word, so both rows match two words and the
          # ripeness row answers "2 to 4 days on the counter" to a question that is really about
          # whether it is safe. The verdict is the answer here; how to ripen it is the second
          # sentence of the same reply.
          bias=3),
    # Raw vegetables are a food-safety question and the table has none: "can i eat raw potato",
    # "raw mushrooms" and "is raw potato safe" reached the boiled-potato card or a search hedge,
    # and ten more raw lines - broccoli, cauliflower, kale, spinach, sweet potato, beetroot,
    # green beans, peas, onion, beetroot - got a shrug. The vegetables split into three groups
    # that want three different answers, so the reply is chosen by the vegetable the line names
    # rather than by the shape of the ask: the ones that are a salad, the ones with something in
    # them that heat destroys, and the hard starches that have to be cooked.
    entry("raw-vegetable",
          ((tuple(_RAW_VEGETABLE_NAMES),
            # The ask is the word "raw" and its synonyms, not the verdict words: the verdict
            # words are in every "is it ok to eat broccoli" line, and this row is only about a
            # vegetable eaten uncooked. "is raw potato safe" carries "raw" already.
            ("raw", "uncooked", "not cooked", "eat raw", "eat it raw", "eat them raw",
             "eat it uncooked", "without cooking", "safely eat raw", "can you eat raw"))),
          _raw_vegetable,
          avoid=_RAW_VEGETABLE_NOT,
          # Ties with the cooking rows that name the same vegetable ("raw green beans" is also
          # the green beans card, which says how to boil them but never whether raw is safe):
          # the safety answer is the one that was asked for.
          bias=4),
    # "can you get food poisoning from eggs" was reaching the stomach-bug recovery card, the same
    # complaint-shaped answer the chicken and rice rows were written for. Salmonella is the germ,
    # and the answer in Britain turns on the Lion mark, which is why the reply names it.
    entry("eggs-food-poisoning", (("egg", "eggs", "egg white", "egg yolk", "runny egg",
                                  "runny eggs"), POISONING_WORDS),
          "Eggs are the second commonest source after chicken, and the germ is salmonella, which "
          "sits on the shell and sometimes in the egg. In Britain a British Lion-marked egg is "
          "fine raw or runny, even in pregnancy, because those flocks are vaccinated; an unmarked "
          "egg, a duck egg or anything from abroad is the one to cook through. Keep eggs cold, "
          "don't wash them, and bin one that is cracked and dirty. Cramps and diarrhoea come 12 "
          "to 72 hours later and usually pass in a few days; fluid is the thing that matters.",
          avoid=POISONING_NOT + DIET_WORDS + _NOT_THIS + OFF_THE_THING + RAW_WORDS
          + ("dog", "dogs", "puppy", "cat", "cats", "kitten", "pet", "pets", "vet",
             "how do i cook", "boil", "boiling", "boiled", "poach", "poached", "scrambl",
             "fry", "frying", "fried", "omelette", "bake", "baking", "meringue", "mayonnaise",
             "white", "whites", "yolk", "yolks", "shell", "cracked", "crack", "float",
             "freshness", "how long", "keep", "keeps", "box", "date"),
          bias=4),
    # Four more lines where the food-safety question was answered by the cooking method, the
    # airport card or a chat nod. They are here rather than in a new module because this is the
    # table that holds "is this food safe to eat", and the machinery (the room-odour guard, the
    # diet hold, the off-the-thing shapes) already belongs to it.
    #
    # "can you get food poisoning from rice" was reaching the stomach-bug recovery card, the
    # same complaint-shaped answer the chicken row was written for. Rice is the one leftover
    # worth being strict about, so the germ is bacillus cereus and the answer is speed, not smell.
    entry("rice-food-poisoning", (("rice", "rices"), POISONING_WORDS),
          "Yes - rice is the leftover worth being strict about. The germ is bacillus cereus, "
          "whose spores survive cooking, so rice left sitting warm grows them and reheating does "
          "not always clear what they made. Cool it fast (spread it on a tray or rinse it under "
          "cold water), box it within the hour, keep it in the fridge no more than a day, and "
          "reheat it once, piping hot all the way through. Cramps and vomiting inside a few "
          "hours of eating are the usual sign; fluid is what matters, and a day of it or blood "
          "in it is a GP.",
          # POISONING_NOT carries "rice" - the chicken row needed it held away - so this row
          # takes everything else on that list and nothing that names its own food.
          avoid=tuple(w for w in POISONING_NOT if w != "rice") + DIET_WORDS + _NOT_THIS
          + OFF_THE_THING + RAW_WORDS
          + ("dog", "dogs", "puppy", "cat", "cats", "kitten", "pet", "pets", "vet",
             "pudding", "risotto", "paella", "sushi", "cook", "cooking", "boil", "boiling",
             "how much water", "basmati", "brown rice", "wild rice", "microwave"),
          bias=4),
    # A sprout is eaten raw in a salad, so the question is food safety, and main answered it with
    # the green-beans cooking card ("top and tail them, boil 4 to 5 minutes"). Sprouts are grown
    # warm and damp, which is also how bacteria grow, so the answer is rinse, cook, and the people
    # who should not eat them raw at all.
    entry("raw-sprouts", (("sprouts", "sprout", "alfalfa", "bean sprouts", "beansprouts",
                           "mung beans", "radish sprouts"),
                          ("raw", "eat", "eating", "safe", "ok", "okay", "washed", "wash",
                           "cook", "cooked", "cooking", "salad", "pregnant", "pregnancy",
                           "should i", "can i", "are they", "in a sandwich")),
          "Bean and alfalfa sprouts are the one salad thing to be careful with: they are grown "
          "warm and damp, which is exactly what bacteria like, and rinsing does not remove what "
          "has got inside the seed. Eat them cooked - stir-fried or dropped into soup for a "
          "minute - and if you want them raw, buy a bag that says ready to eat and keep it cold. "
          "Pregnant, elderly, or on treatment that lowers your immunity, cook them: the same "
          "advice covers a raw mung-bean salad.",
          avoid=("brussels", "brussel", "christmas", "roast", "roasting", "boil", "boiling",
                 "steam", "steaming", "how long", "minutes", "how do i cook", "how to cook",
                 # not "sprouting" or "sprout them": _forms("sprouting") carries "sprout",
                 # which is this row's own noun, and it stood the row down for its own question.
                 "grow", "growing", "grown", "seed", "seeds", "garden", "window sill",
                 "windowsill", "jar", "potato", "potatoes", "get rid of", "pest", "aphid"),
          bias=3),
    # "a fly landed on my sandwich" reached the airport liquids card, because "sandwich" and
    # "fly" are both travel words. A fly on food is a hygiene question with a short answer.
    entry("fly-on-food", (("fly", "flies", "bluebottle", "bluebottles", "wasp", "wasps"),
                          ("landed", "landing", "land", "on my food", "on my sandwich",
                           "on my dinner", "on my drink", "in my drink", "in my food",
                           "in my tea", "crawling", "walked on", "sat on")),
          "Brush it off and eat the food: a fly that lands for a moment leaves little behind, "
          "and the dose is what matters. If it has been walking about on it, cut away that patch "
          "or rinse what you can, and tip out a drink it fell into. What is worth avoiding is "
          "food a fly has been sitting on for a while, or anything from a bin or off the floor, "
          "because flies feed on waste and carry it on their legs.",
          avoid=("airport", "security", "hand luggage", "check in", "flight", "flights",
                 "plane", "heathrow", "gatwick", "holiday", "abroad", "how do i get rid of",
                 "get rid of flies", "infestation", "traps", "trap", "kite", "flag", "butterfly",
                 "butterflies", "drone", "dragonfl", "firefl", "fly a", "flying to",
                 "flying out", "business", "screen", "net curtains",
                 # a wasp landing on a person is not a wasp landing on the food: this row keys
                 # "wasp" and "landing", and with bias=4 it answered "a wasp keeps landing on
                 # me" with how to eat a sandwich. Both words are needed for the food question.
                 "on me", "landed on me", "landing on me", "on my arm", "on my leg",
                 "on my face", "on my neck", "on my hand", "on my head", "keeps landing",
                 "stinging", "stung", "sting", "chasing me", "buzzing", "swat"),
          bias=4),
    # The pot in the fridge is the question people ask most after a big cook, and no row owned
    # it: "leftover curry in the fridge is it ok" and "is leftover curry ok to eat the next day"
    # both reached the chat nod on main, while the same thing said as "how long does leftover
    # curry keep" had a number. `fridge-life` holds "leftover" out of its key on purpose (a
    # leftovers answer is a different, longer one) and `leftover-meal` holds the safety words
    # out, so a leftover with no food of its own fell between the two. One row for every cooked
    # dish, because the clock, the cooling and the single reheat are the same for all of them.
    # The foods with a spoilage row of their own keep it: "is my leftover chicken still ok" is
    # about the chicken, and the chicken row says the stricter thing.
    # A cooked dish that has been in the fridge for a week, a fortnight or a month has one answer,
    # and it is not a cooling method and not a recipe: it is past it, and bin it. The cooling rows
    # were answering "the stew has been in the fridge a week" with "straight in is fine - a modern
    # fridge copes with a warm pot", which is the answer to a question the person had stopped
    # asking days earlier, and "is a week in the fridge too long for curry" was answered with a
    # twenty-five-minute chickpea recipe. The period is what makes this the question, and the
    # dish is what says the period is a fridge life rather than a cooking time: a week, a
    # fortnight and a month are longer than anything cooked keeps, so the reply is the bin.
    entry("past-it-in-the-fridge",
          (("leftovers", "leftover", "left over", "curry", "stew", "casserole", "chilli",
            "tagine", "goulash", "bolognese", "lasagne", "risotto", "soup", "stew", "rice",
            "shepherds pie", "cottage pie", "the sauce", "the broth", "the dish"),
           # the period, said as weeks or months: a day or two is still-leftovers' question, and
           # they answer it with the number rather than the bin
           ("a week", "one week", "two weeks", "three weeks", "a fortnight", "fortnight",
            "weeks", "a month", "one month", "two months", "months", "week old", "weeks old",
            "last week", "the week before", "a while", "ages")),
          "Past it, I'm afraid - bin it. A cooked dish keeps 3 to 4 days in the fridge, and rice "
          "only 1, so a dish from last week is well beyond that, and reheating it does not make "
          "it safe: the toxins that build up in old food do not all break down with heat and "
          "they do not all smell. Scrape it out, wash the box with hot soapy water, and next "
          "time freeze the half you will not eat within the three days.",
          # a fridge that is broken, a shop's use-by date and a freezer are other rows; so is
          # the dish that is only a day or two old, which keeps its number
          avoid=("use by", "use-by", "best before", "sell by", "date on", "supermarket", "shop",
                 "frozen", "freezer", "defrost", "thaw", "refreeze", "refroze", "reheat",
                 "reheating", "microwave", "recipe", "what can i make", "what can i cook",
                 "meal ideas", "how do i make", "how to make", "cook it", "how long do i cook",
                 "fridge is", "fridge not", "not cold", "stopped working", "warm in the fridge",
                 "temperature", "thermometer", "power cut", "smells", "sour", "slimy", "mould",
                 "mouldy", "mold", "moldy", "gone off", "go off", "off",
                 "rice", "chicken", "meat", "beef", "lamb", "pork", "fish", "prawns", "milk",
                 "cream", "yoghurt", "yogurt", "cheese", "eggs", "egg", "pasta", "bread",
                 "baby", "babies", "toddler", "child", "children", "dog", "cat", "pregnant",
                 # "left over" is money as often as it is a dish, and "each month" is the
                 # period that made this row answer it: "i have 200 left over each month" is a
                 # budgeting question and it was told "past it, I'm afraid - bin it". The other
                 # periods and the one-word spelling are the same question, and a dish is left
                 # in the fridge for "a week", never "each week".
                 "each month", "every month", "each week", "every week", "each year",
                 "every year", "per week", "per month", "per year", "each payday",
                 "left over each", "left over every", "left over per",
                 "leftover each", "leftover every", "leftover per", "leftover a month",
                 "leftover this month", "leftovers each", "leftovers every"),
          # the dish and the period together are this row's line, so it outranks the cooling rows
          # and the recipes that share one of the two
          bias=3,
          # and a sum of money is not a dish, whatever period it is said with
          guard=_not_about_money),
    entry("still-leftovers",
          (("leftovers", "leftover", "left over", "left in the fridge", "whats left",
            "what's left", "the rest of the", "curry", "stew", "casserole", "chilli", "tagine",
            "goulash", "bolognese", "shepherds pie", "cottage pie", "lasagne", "risotto"),
           # The second half is the keeping ask said plainly, which is what OFF_WORDS is
           # missing: "leftover curry in the fridge is it ok" carries a bare "ok" and nothing
           # else, and the table's asks are all two words long ("still ok", "ok to eat").
           ("ok", "okay", "is it ok", "is that ok", "safe", "is it safe", "safe to eat",
            "eat", "eat it", "still", "still good", "still ok", "next day", "the next day",
            "tomorrow", "fridge", "gone off", "go off", "went off", "smell", "smells",
            "smelly", "sour", "slimy", "days", "day", "how long", "keep", "keeps", "last",
            "lasts", "bin", "throw", "been in", "sat in", "made on", "cooked it on",
            # "stew made yesterday can i have it" gave the row only "stew": the ask it carries is
            # the phrase "can i have", which is grammar and names nothing, so the second position
            # had no word of its own. The day the dish was made is that word, and it is the one
            # the person used instead of a count.
            "yesterday", "last night", "this morning",
            # A long period said in weeks or months is the same keeping question as a few days:
            # "the stew has been in the fridge a week" was answered "straight in is fine - a
            # modern fridge copes with a warm pot", and "is a week in the fridge too long for
            # curry" with a twenty-five-minute recipe. The number in the reply is what answers
            # them, and it is past it at a week whatever the dish.
            "a week", "one week", "two weeks", "three weeks", "a fortnight", "fortnight",
            "weeks", "a month", "one month", "two months", "months", "week old", "weeks old",
            "last week", "the week before", "a while", "ages")),
          _the_leftovers_answer,
          # `_NOT_THIS` is not used here: the words it holds out are the keeping words this row
          # answers with ("in the fridge", "3 days", "how long"), and holding them out is what
          # kept the row off "leftover curry in the fridge is it ok". The cooking and defrosting
          # shapes are named instead.
          avoid=DIET_WORDS + UNDERCOOKED_PINK
                + ("frozen", "defrost", "defrosting", "thaw", "thawing", "left out", "overnight",
                   "all night", "all day", "room temperature", "sat out", "sitting out",
                   "how do i keep", "how do i store", "how to keep", "how to store",
                   "how can i keep", "how should i keep", "refreeze", "refroze", "re-freeze",
                   "freeze again", "reheat it twice", "how many times can i reheat",
                   "how do i reheat", "how to reheat", "best way to reheat", "why",
                   "what causes", "cause", "mouldy", "mould", "moldy", "mold")
                + ("chicken", "turkey", "meat", "beef", "lamb", "pork", "steak", "mince",
                   "fish", "salmon", "cod", "prawns", "prawn", "ham", "bacon", "sausage",
                   "egg", "eggs", "rice", "milk", "cheese", "yogurt", "yoghurt", "cream",
                   "pasta", "pizza", "bread", "potato", "potatoes", "tomato", "tomatoes",
                   # what to make with them is the cooking question, and it has its own answer
                   # a line that asks how long keeps its own answer: the general cooked-food
                   # table and the soup row both give a number, and this row must not take the
                   # question they answer to say the same thing at more length
                   "how long does", "how long do", "how long can i", "how long will",
                   "how long should", "how long to",
                   # the method of cooking it is not the keeping of it: "im cooking a curry
                   # tonight" then "how long should i simmer it for" reached this row on the
                   # carried-over subject, and a simmer is the pot's own question
                   "simmer", "simmering", "boil", "boiling", "fry", "frying", "bake", "baking",
                   "roast", "roasting", "grill", "grilling", "oven", "slow cooker", "air fryer",
                   "minutes", "start to finish", "how do i cook", "how to cook", "how long do i cook",
                   "how many days", "what can i make", "what can i eat", "what can i have",
                   "what to eat",
                   "what goes with", "goes with", "serve with", "side dish", "side for",
                   "what can i do with", "recipe", "recipes", "use up",
                   "using up", "idea", "ideas", "meal ideas", "dinner ideas", "how do i make",
                   "how to make", "how do i cook", "how to cook", "how long do i cook",
                   "how long to cook"),
          ask=("ok", "okay", "safe", "eat", "eat it", "still", "next day", "tomorrow", "fridge",
               # "stew made yesterday can i have it" asks the same thing as "is it still ok"
               # without a keeping word in it, and reached the two-hour recipe for stew.
               "can i have", "have it", "have some", "can i still have", "can i eat it",
               "gone off", "go off", "went off", "smell", "smells", "smelly", "sour", "slimy",
               "days", "day", "how long", "keep", "keeps", "last", "lasts", "bin", "throw",
               "should i", "made it", "made on", "cooked it on", "been in", "sat in",
               "a week", "two weeks", "a month", "last week"),
          # the period makes this the keeping question, and the cooling rows name a pot and no
          # period: this row answers the dish that has been in the fridge for days or weeks. The
          # recipe for the dish is keyed on the same word.
          bias=2,
          # A line whose subject is a dish somebody wants to cook tonight is the recipe, not the
          # pot in the fridge: "what can i make with leftover curry" and "how do i make a curry"
          # are cooking. A cooking verb in the line with no keeping word stands the row down.
          # A fault in the dish - too hot to eat, too spicy, too salty - is the rescue card's
          # question, not the pot in the fridge.
          guard=lambda understood: (_not_a_recipe_now(understood)
                                    and _not_a_fault_in_the_dish(understood))),
    # The five-second rule is a question people ask outright, and "i dropped my toast on the
    # floor is it ok" got a chat nod on main.
    # The rule is asked about by name as often as the dropped toast is described, so the name of
    # the rule is in the first group: "is the five second rule true" names no floor at all.
    entry("five-second-rule", (("floor", "ground", "carpet", "worktop", "pavement",
                                "five second rule", "five seconds rule", "5 second rule",
                                "five-second rule", "five second", "five seconds", "5 second"),
                               ("dropped", "drop", "fell", "fallen", "picked it up", "pick it up",
                                "blew on it", "kiss it better", "true", "real", "myth",
                                "a thing", "still ok", "safe", "eat it")),
          "The five-second rule is not real: bacteria stick the moment food touches the floor, "
          "and it is the wetness that decides how much, not the seconds. A dry biscuit or a piece "
          "of toast is a small risk - brush it off and use your judgement - but anything damp, "
          "sticky or eaten with your hands should go in the bin, and anything dropped outside or "
          "in a bathroom always should. If it did go down, it is a wait-and-see, not a hospital "
          "trip: a healthy stomach usually deals with it.",
          avoid=("phone", "screen", "keys", "won't turn on", "wont turn on", "signal",
                 "cracked", "dropped it", "dropped my phone", "dropped the", "dropped a",
                 "dropped out", "prices dropped", "temperature dropped", "how do i stop",
                 "my back", "my hip", "fell over", "fell down", "fell off the ladder",
                 "fell off my bike", "fell out of bed"),
          bias=3),
)

# A smell stuck in a room is a cleaning question, not a spoilage one. "how do i get the smell of
# fish out of the house", "my house smells of fish" and "the fish smell wont go" all name a food
# and a smell word, so every row here matched them and gave a test for whether the fish in your
# hand is safe - when the fish is long eaten and the question is how to clear the air. The room
# words and the shapes that say the smell has taken hold stand the whole domain down;
# `cleaning.kitchen-smell` answers those lines with airing and a simmering pan.
# One list for every row, because a food-freshness table gets this wrong for every food at once,
# and the next row somebody adds inherits the guard instead of repeating it.
_ROOM_ODOUR = ("out of the house", "out of my house", "out of the flat", "out of my flat",
               "out of the kitchen", "out of the room", "house smells", "flat smells",
               "kitchen smells", "room smells", "smell wont go", "smells wont go",
               "wont go away", "lingering smell", "stinks in here")
for _item in ENTRIES:
    _item.avoid = _item.avoid + _ROOM_ODOUR


# "is it ok to eat mussels in a month without an r" was the baby-food table's first-foods answer,
# because the age table reads "month" on its own and "is it ok to" is a weaning shape. The r rule
# is an old shellfish question with a straight answer, and nothing in the knowledge base had it.
_SHELLFISH = ("mussels", "mussel", "oysters", "oyster", "clams", "clam", "cockles", "scallops",
              "shellfish", "lobster", "crab", "whelks", "razor clams")
# The second half is *which months*, and nothing else. It used to hold the liveness words as
# well - "ok to eat", "still alive", "gone off", "bad ones", "how long do they keep" - because
# "is it ok to eat oysters in august" needed one of them, and every month word already covers
# that line. What those words really did was take a question about a dead mussel away from the
# card that answers it: "is it ok to eat mussels that didnt open" is the tap-and-bin test, and
# an r-rule card about the days before fridges is the wrong answer to it. So the months stay and
# the liveness words go back to the mussel row.
# The second part is the r rule itself plus the shapes people put it in - "is it ok to eat
# mussels in a month without an r". The phrase "without an r" cannot be keyed on its own, because
# understanding rewrites the letter ("without an r" reads as "without an are"), so "ok to eat" is
# what lets that line match at all.
# A bare month name is a trap: "my daughter may have eaten a mussel" and "i may have eaten a bad
# oyster" are the word "may" as a modal, not the month, and both were taken by this card. The
# months are keyed as "in <month>", which is how a month appears in a shellfish line ("mussels in
# may", "oysters in august", "can i buy mussels in july"), and those still match.
_R_MONTHS = ("without an r", "without an 'r'", "without the letter r", "month with an r",
             "months with an r", "only in months", "in an r month", "no r in the month",
             "r in the month", "summer months", "in may", "in june", "in july", "in august",
             "in september", "spawning",
             # "without an r" cannot be keyed on its own - understanding rewrites the letter, so
             # it reads as "without an are" - and "ok to eat" is what lets the shapes people
             # actually write match: "is it ok to eat mussels in a month without an r".
             "ok to eat", "okay to eat", "alright to eat")
ENTRIES = ENTRIES + (
    entry("shellfish-r-rule",
          (_SHELLFISH, _R_MONTHS),
          "The rule about only eating shellfish in months with an r is about the days before "
          "fridges: May to August are the warm months, when shellfish spoil fastest and when "
          "mussels spawn and go watery. It is not a law now - farmed mussels and rope-grown "
          "ones are sold all year and are safe - so buy from a fishmonger or a shop with a busy "
          "counter, keep them cold, and use the tests that actually tell you: a live mussel is "
          "shut, or shuts when you tap it, and one that stays open goes in the bin; cook them in "
          "a covered pan for 5 to 8 minutes and throw away any that are still shut afterwards. "
          "Eat them the day you buy them, and never eat them raw.",
          # pregnancy, a baby, a recipe and a bought ready meal are other cards
          # a question about one shellfish's condition is the mussel row's: an open shell, a
          # dead one, a smell, a fridge, a "gone off" - the r rule is about the calendar
          avoid=("pregnant", "pregnancy", "expecting", "baby", "toddler", "child", "weaning",
                 "recipe", "white wine", "garlic", "restaurant", "frozen", "freeze",
                 "how long do they keep", "dog", "cat",
                 "open", "opened", "unopened", "didnt open", "didn't open", "stays open",
                 "still alive", "alive", "dead", "gone off", "smell", "smells", "smelly",
                 "bad ones", "keep in the fridge", "fridge"),
          bias=4),
)

# A yellow leaf is the sign people notice most and the one no row knew: "can i eat spinach thats
# gone a bit yellow", "my lettuce has gone yellow" and "can i eat lettuce thats gone a bit slimy"
# were a search hedge and two chat nods, while the same question about lettuce wilt already had
# the iced-water answer. The greens are one row because the answer is the same for all of them:
# yellow is age, slime is spoil.
_LEAFY_GREENS = ("spinach", "baby spinach", "lettuce", "lettuce leaves", "little gem",
                 "kale", "curly kale", "salad leaves", "salad leaf", "bag of salad",
                 "salad bag", "rocket", "watercress", "cress", "chard", "spring greens",
                 "leafy greens", "bok choy", "pak choi", "collard greens", "cavolo nero",
                 "greens")

# The words for a leaf that has changed, and the asking words, because "my spinach is going
# yellow" carries no ask at all while "is yellow spinach ok" carries no ask of the usual shape.
# Only the signs that mean something: a colour, slime, a soft spot. Wilting and going limp are
# not here on purpose - those lines already have a good answer (the iced-water revive, and the
# wilting chat that says limp leaves are water loss and safe), and this row would take them.
_LEAFY_SIGNS = ("yellow", "yellowed", "yellowing", "gone yellow", "going yellow",
                "turning yellow", "turned yellow", "gone a bit yellow", "slightly yellow",
                "gone slimy", "slimy", "slime", "brown", "browning", "gone brown",
                "turned brown", "black spots", "mushy", "gone soft",
                # The plural leaf is how people say it when the colour is on the leaf rather than
                # on the bag: "my kale has yellow leaves can i eat it", "can i eat spinach with
                # yellow leaves". Without these the autumn card and the houseplant card took those
                # lines on "yellow leaves" alone, though neither is about a bag in a fridge.
                "yellow leaves", "yellow leaf", "yellowed leaves", "yellowing leaves",
                "brown leaves", "slimy leaves", "soggy", "soggy leaves",
                # the ask said in the same line as the sign: "the kale is yellow and soggy can i
                # use it" is a spoilage question, and the pan-of-water card was taking it
                "use it", "eat it", "still use", "still eat")

# A leaf that has only gone limp has its own good answer - wilting is water loss and iced water
# brings it back - so this row asks the line for a colour or a slime before it answers. Without
# the fence "my kale is wilted can i still use it" was taken by this row on the words "still
# use", and the short wilting answer it had was better than the long spoilage one.
_LEAFY_SHOWS = re.compile(
    r"\b(?:yellow\w*|brown\w*|black\w*|slimy|slime|mushy|sour\w*|smell\w*|smelly)\b", re.I)


def _the_leaf_shows_a_colour(understood):
    """The line names a colour, a slime or a smell on the leaf, not just that it went limp."""
    if not isinstance(understood, dict):
        return False
    return bool(_LEAFY_SHOWS.search(understood.get("clean") or understood.get("text") or ""))


# A cabbage is the same question with a different answer: yellow there is the two or three outer
# leaves, and the head behind them keeps for weeks. Keyed on its own so it does not pull the bag
# of leaves answer apart, and so "can i eat cabbage thats gone yellow" stops landing on the
# caterpillar card.
_CABBAGES = ("cabbage", "white cabbage", "green cabbage", "red cabbage", "savoy",
             "savoy cabbage", "hispi", "pointed cabbage")

_CABBAGE_SIGNS = ("yellow", "yellowed", "yellowing", "gone yellow", "going yellow",
                  "turning yellow", "yellow leaves", "yellow leaf", "brown", "browning",
                  "gone brown", "limp", "wilting", "wilted", "soft", "outer leaves",
                  "slimy", "smelly")

ENTRIES = ENTRIES + (
    entry("leafy-greens-yellow",
          (_LEAFY_GREENS, _LEAFY_SIGNS),
          "Check for slime before you look at the colour: a yellow or floppy leaf is age rather "
          "than poison - light and time break the green down - so pick those out and use the "
          "rest. Slimy, sour-smelling or brown-and-soft leaves are not safe, and once one leaf "
          "is slimy the bag is best binned, because the slime is bacteria and rinsing does not "
          "take it off. Wilting on its own is only water loss, so 10 minutes in iced water brings "
          "the crunch back, and limp-but-dry leaves are perfect in a soup, a curry or a stir-fry. "
          "Keep the bag in the salad drawer with a piece of kitchen paper in it and eat it within "
          "3 to 5 days of opening.",
          # a leaf on a growing plant is the garden's question, not the fridge's, and a recipe
          # is about cooking the greens rather than about whether they are still good
          avoid=("garden", "gardening", "allotment", "plot", "compost", "feed", "fertiliser",
                 "fertilizer", "blight", "grow", "growing", "grown", "plant", "plants",
                 "planting", "seed", "seeds", "seedlings", "sow", "sowing", "soil", "hydroponics",
                 "tomato", "courgette", "why are my leaves", "recipe", "recipes",
                 "how do i cook", "how to cook", "how long does", "how long do", "how long can i",
                 "keep", "keeps", "last", "lasts", "freeze", "frozen",
                 # reviving limp leaves and using a bag up are their own cards, and a leaf that
                 # went soggy in the pan is the cooking answer rather than a spoilage one
                 "revive", "reviving", "bring it back", "crisp", "crispness", "fresh again",
                 "use up", "using up", "what can i do with", "what can i make", "ideas",
                 "cook", "cooking", "cooked", "pan", "boil", "boiling", "steam",
                 "steaming", "wilt it", "wilted in a pan"),
          guard=_the_leaf_shows_a_colour,
          # bias 2, not 1: "my kale has yellow leaves can i eat it" and "can i eat spinach with
          # yellow leaves" scored level with the autumn card, and the tie went to the card about
          # trees. Two words of the line name the greens; nothing in it is about a tree.
          bias=2),
    entry("cabbage-yellow-outer-leaves",
          (_CABBAGES, _CABBAGE_SIGNS),
          "Yellow or brown outer leaves on a cabbage are just age: peel off the ones that have "
          "gone, trim the dried stem end, and the firm head inside is still good - a whole "
          "cabbage keeps a month or more in the fridge, and a cut half keeps a couple of weeks "
          "wrapped. The one to bin is a head that is slimy or sour-smelling right through, or "
          "soft all the way to the middle. If only the outside looks tired, it is a stir-fry or "
          "a soup rather than the bin.",
          # a cabbage in the ground is the garden's question, and a slaw or a recipe is about
          # cooking it rather than about whether it is still good
          avoid=("garden", "gardening", "allotment", "plot", "compost", "feed", "fertiliser",
                 "fertilizer", "blight", "grow", "growing", "grown", "plant", "plants",
                 "planting", "seed", "seeds", "seedlings", "sow", "sowing", "soil",
                 "flower", "flowers", "flowering", "bolted", "bolting", "recipe", "recipes",
                 "slaw", "coleslaw", "pickle", "pickling", "ferment", "sauerkraut",
                 "how long does", "how long do", "how long can i", "keep", "keeps", "last",
                 "lasts", "freeze", "frozen", "how do i cook", "how to cook", "roast"),
          bias=3),
)
