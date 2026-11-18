def _the_water_ask(understood):
    """"when can i give water": water, being given, and no drink of the person's own.

    The table answers a food by name once a child is named, and this line names none - the water
    is the whole question - so this row brings its own evidence rather than standing down. The
    adult's own drink is somebody else's row: "how much water should i drink a day" names no
    one to give it to, so it is left alone here.
    """
    text = " " + _text(understood) + " "
    if " water " not in text and not text.endswith(" water "):
        return False
    if any(word in text for word in ("i drink", "should i drink", " a day ", "litre", "liter",
                                     "pint", "eight glasses", "2 litres", "2 liters")):
        return False
    return any(word in text for word in ("give", "giving", "offer", "when can", "how much",
                                         "how often", "sips"))


"""Baby feeding: weaning, first foods, and what a baby can have.

The answers lane owns this domain. This is the food end of parenting: the questions people ask
in the first two years, over and over and usually in a hurry - what do I start with, what can
they eat at this age, can my baby have this thing, how do I bring in an allergen. The facts are
mainstream weaning guidance, kept as data so one fact answers every way of asking for it: "can
my baby have yogurt", "is yoghurt ok for a 7 month old" and "can i give my baby yoghurt" all
reach the same row.

Three tables carry the domain:

- `STAGES` is the age table: what a baby eats and how much of it, from before weaning to a year
  old. One row answers "what can they eat", "how many meals a day" and "how much" alike,
  because all three are the same stage, and the age is read off the line when the answer is
  built rather than keyed three times.
- `FOODS` is the verdict table: one row per food people ask about, each with the answer as it
  would be said - the verdict first, then the age, then the one thing that matters. A food with
  no row is not answered here at all.
- `NOT_A_MENU` and `NOT_A_BABY` are the stand-downs. A baby with a cold, a cot, a car seat or a
  baby shower is not a baby with a menu, and a puppy is not a baby at all. Every row here stands
  down for those, because a food table that answers "my baby has petechiae on her legs" is worse
  than no table.

The other half of the same care is in the keys: a row needs a word of *eating*, not just a baby
and an ask. "what can i give a neighbour who just had a baby" and "how deep should the water be
for a baby bath" have a baby and a question in them and nothing to do with food, and they are
left to the rows that answer them.
"""
import re

from .lookup import entry, not_the_heat_of_an_argument

ANSWERS = ("family-and-parenting", "food-and-drink")

# The words people use for the person being fed. A row needs one of these before it can fire,
# so "my baby" is the subject of everything on this table.
_BABY = ("baby", "baby's", "babys", "babies", "infant", "infants", "little one",
         "little ones", "newborn", "newborns", "breastfed baby", "bottle fed baby",
         "weaning", "weaned")
# People type the possessive without its apostrophe, and "my babys food" then read as nobody's
# food at all: "can i put salt in my babys food" lost the salt answer for it. The same missing
# s is in "my babies", which is a plural and already here.

# The age the line says it with, which is what the stage table is indexed by. This is the first
# part of the stage row, so a line with no age in it - "how much should i feed my baby" - never
# reaches it and keeps the newborn-feeding answer it already had.
AGE = ("month old", "months old", "week old", "weeks old", "newborn", "newborns",
       "1 year old", "one year old", "a year old", "eighteen month", "18 month",
       # An age written in words is the same age as one written in digits, and the stage table
       # reads the figure either way: "my two year old, what should i feed her" was a shrug
       # because the key only knew "one year old". Bare "year old" stays out, as the note below
       # says - a five-year-old's homework is not a feeding question.
       "two year old", "three year old", "four year old", "five year old", "six year old",
       "seven year old", "eight year old", "nine year old", "ten year old",
       "toddler", "toddlers",
       # A figure with its unit next to it is the age however it is written, and "baby is 1" is a
       # first birthday: the reply reads the number off the line, so the key only has to see that
       # an age was given at all. "year old" alone is deliberately not here - a five-year-old's
       # homework, bedtime and screen time are not feeding questions, and that word is in all
       # of them.
       "month", "months", "baby is")

# The subject of a row is a baby or the age they are, because a line gives one or the other.
BABY = _BABY + AGE

# A bare "month" or "months" is not an age. "can i eat rice that has been in the cupboard for
# months" was answered with the baby-rice verdict and "is it safe to eat mussels in months
# without an r" with the fish-bones one, both on that single word: the unit is a length of time
# in half the sentences people write, and the age is the figure in front of it. The entry keys
# keep the bare words so "7 months" still reaches the stage rows; only the gate below reads the
# figure, which is what _AGE_FIGURE is for.
_UNIT_WITHOUT_FIGURE = ("month", "months")

# The words that make the line about eating. "have" and "give" are not here on purpose: they
# are in every second sentence a person writes about a baby ("what can i give a neighbour who
# just had a baby"), and the verdict rows below carry them instead, next to a named food.
EATING = ("eat", "eats", "eating", "feed", "feeds", "feeding", "food", "foods", "solids",
          "meals", "meal", "wean", "weaning", "weaned", "diet", "portion", "portions",
          "puree", "purees", "finger food", "finger foods", "breakfast", "lunch", "tea",
          "supper", "snack", "snacks", "drink", "drinks", "milk", "menu")

# A baby who is unwell is not a baby with a menu: these lines are an illness, a reaction or a
# choking, and they belong to the safety module and the child-fever rows. Every row here stands
# down for them, so a food verdict can never take a red flag.
# The words a parent uses to say a baby will not eat, which NOT_A_MENU fences off from the
# menu rows and which the refusal row needs in its own key.
_THE_REFUSAL_WORDS = ("spits", "spit", "spat")

NOT_A_MENU = (
    "not breathing", "isnt breathing", "isn't breathing", "stopped breathing", "choking",
    "choked", "limp", "floppy", "unresponsive", "wont wake", "won't wake", "blue", "pale",
    # A baby working to breathe is a same-day check with a card of its own, and the whole of
    # that card's key is a breath word: with the age and the ask in the line this table ranked
    # in front of it on "my baby is breathing fast what should i do".
    "breathing", "breathe", "breathes", "breathless", "wheezing", "wheeze", "grunting",
    "grunt", "sucking in", "under the ribs",
    "fever", "temperature", "rash", "petechiae", "hives", "swollen", "swelling", "vomiting",
    # The complaint is asked with its inflected form as often as the noun: "my toddler is
    # constipated what can i do" reached the age table on the age word alone, because the
    # fence held "constipation" and the line said "constipated".
    "throwing up", "sick", "diarrhoea", "diarrhea", "constipation", "constipated",
    "blood", "reaction",
    # A child who is ill is asked about by the illness cards, not fed from a menu: "what should
    # i feed a toddler who is ill" and "my baby is unwell what should i feed her" were the
    # family-food and first-foods answers with no mention of the illness at all.
    "ill", "unwell", "poorly", "off her food", "off his food", "off their food", "off food",
    "allergic reaction", "anaphylaxis", "a&e", "ambulance", "999", "111", "hospital", "doctor",
    "gp", "health visitor", "refusing feeds", "not feeding", "isnt feeding", "isn't feeding",
    "losing weight", "not putting on weight", "how often", "how many times",
    # How much they eat, or refusing to, is its own question: the rows for a child who will not
    # eat and a child who only eats one thing answer it, and a first-foods list does not.
    "wont eat", "won't eat", "not eating", "isnt eating", "isn't eating", "refuses", "refusing",
    "fussy", "picky", "hates", "spits", "throwing food", "throws food", "only eats",
    # The rest of a baby's day and the rest of a baby's health, which other rows answer: a cold,
    # colic, a cot, a car seat, a nappy, a jab, a bath, a swimming lesson, a night's sleep.
    "cold", "cough", "blocked nose", "ear infection", "colic", "colicky", "windy", "wind",
    "gripe", "reflux", "possetting", "thrush", "eczema", "teething", "teeth", "jab", "jabs",
    "immunisation", "immunisations", "vaccination", "vaccinations", "calpol", "paracetamol",
    "ibuprofen", "dose", "doses", "medicine", "medicines", "tongue tie", "cradle cap",
    "bath", "bathing", "bathwater", "swim", "swimming", "pool", "cot", "crib", "moses",
    "pram", "buggy", "pushchair", "car seat", "carseat", "highchair", "high chair", "bib",
    "sterilise", "steriliser", "formula", "dummy", "nappy", "nappies", "wipes", "nap", "naps",
    "sleep", "sleeping", "crying", "unsettled", "routine", "nursery", "childminder", "creche",
    # A baby on the way, a baby just born, and a baby somebody else is buying for: news, gifts
    # and names, none of which is a menu.
    "pregnant", "pregnancy", "expecting", "labour", "birth", "born", "shower", "christening",
    "gift", "present", "neighbour", "neighbor", "my sister", "my brother", "my cousin",
    "my friend", "my niece", "my nephew", "grandchild", "grandson", "granddaughter",
    # A drink they will not take is a different question from what they may have.
    "wont drink", "won't drink", "refuses to drink", "temp", "in a bottle", "in the bottle",
    "how much water", "how much juice",
)

# How much milk, how many feeds, how many ounces: a milk question with a row of its own that
# gives the eight to twelve feeds in 24 hours, so a menu and a stage card stand down for it. It
# is its own list rather than part of the stand-down above because the milk row is the row that
# answers it - a stand-down that names the question stands down the answer too, and that is what
# kept "how much milk should my baby drink" on the litre-a-day water card.
_HOW_MUCH_MILK = (
    "how many feeds", "how many feed", "how many bottles", "how many ounces", "how many oz",
    "how many ml", "how many mls", "feeds a day", "bottles a day", "ounces of milk",
    "ml of milk", "how much formula", "how much expressed", "how much should i feed",
    "how much to feed", "how much should i be feeding", "how much should i give my baby",
    "how much milk", "how much breastmilk", "how much breast milk",
)

# The same stand-down for pets: a puppy and a kitten are fed, but not by this table.
NOT_A_BABY = ("puppy", "pup", "puppies", "dog", "dogs", "kitten", "kittens", "cat", "cats",
              "vet", "hamster", "guinea", "rabbit", "rabbits", "litter", "crate", "animal",
              "pets", "lamb", "calves", "foal", "chick", "parrot", "fish tank")

# Starting to wean is not a question this table should take: the family table's weaning row
# answers it, and its answer ends with the two lines this one would lose - no honey before one,
# no whole nuts or grapes, and always sit with them while they eat. Every row here stands down
# for the word, so "when should i start weaning" keeps that answer. The method by name - baby
# led weaning, blw - is this table's own row and stands down for nothing here.
# "finger foods" is the same shape for the same reason: it is in that row's key, and the answer
# that comes back ends with the choking fences a list of first foods does not have.
WEANING_ELSEWHERE = ("wean", "weans", "weaned", "weaning", "finger food", "finger foods")

# A lump on a body is a health question and nothing to do with texture. "my baby has a lump",
# "my baby has a lump on his head" and "my baby has a lump under the skin" were all answered with
# "Do not blend it back: the window for lumps is about seven to nine months". One list, every row
# in this table that answers a lumpy meal, so a new one is fenced the day it is written. The
# phrases only a meal uses ("lumps in her food") are deliberately not here.
# The parts of the body are what make it a lump and not a texture, not the prepositions: a baby's
# meal says "lumps in her food" with the same two words, so "lump in" cannot be on this list.
A_BODY_LUMP = ("a lump", "has a lump", "had a lump", "found a lump", "under the skin",
               "armpit", "armpits", "neck", "groin", "head", "breast", "testicle", "testicles",
               # not "mouth": a meal says "spits them out of her mouth" with the same word, and
               # two good lines dropped to "Got it." for it. A lump in a mouth still reaches the
               # lumpy-meal row, which is where main sent it anyway.
               "scrotum", "gum", "gums", "cheek", "swollen", "swelling", "bump", "bumps",
               # the rest of the body, because a lump on a back was still answered with the
               # weaning card: "my baby has a small lump on his back" was told not to blend
               # the lumps back into the meal.
               "back", "bottom", "tummy", "leg", "thigh", "shoulder", "chest", "forehead",
               "under the arm", "in the nappy area", "skin")

# A number of months is not always an age. A phone, a gym, a tenancy and a warranty are all sold
# in months, and the age table reads the unit alone, so "i signed up for a 12 month contract and
# want out" was answered with the three signs of readiness for solids. This is the one word of
# the agreement that the number belongs to, and every row here stands down for it: what a baby
# eats is never the answer to a question about a contract.
NOT_AN_AGE = ("contract", "contracts", "membership", "memberships", "subscription",
              "subscriptions", "tenancy", "lease", "warranty", "insurance", "loan", "loans",
              "instalment", "instalments", "repayments", "gym", "phone contract",
              "mobile contract", "broadband", "cancellation", "notice period",
              # ...and a month is not always an age either: "is it ok to eat mussels in a month
              # without an r" was answered with "start with soft food they can hold themselves".
              # The words that name the month as a month, rather than an age, stand every row
              # here down, so a baby with shellfish keeps its own answer.
              "without an r", "with an r", "time of year")

# A spice named in the line is the spices row's question, not the dish's: "can i put cinnamon in
# my babys porridge" was answered with the row about porridge oats, while "can my baby have
# cinnamon" and "can my baby have porridge" keep their own answers. The spice row is the one that
# says mild spices are fine early, so every verdict here stands down for a spice by name.
SPICE_NAMES = ("cinnamon", "cumin", "turmeric", "paprika", "nutmeg", "coriander", "cardamom",
               "saffron", "curry powder", "chilli powder", "chili powder", "black pepper",
               "white pepper", "mixed spice", "allspice", "garam masala", "spices", "spice",
               "herbs", "herb", "mild curry")

# A question about water in the body is nobody's food verdict: "does drinking coffee dehydrate
# you" and "does coffee count as water" name a drink this table knows (tea and coffee both, with
# a baby) and were scored as its rows before the answer had a chance to say no. The verdict is
# about what a child may eat or drink, so a line that asks about dehydration stands the whole
# table down and the drink question keeps its own row.
NOT_ABOUT_WATER = ("dehydrate", "dehydrates", "dehydrated", "dehydration", "dehydrating",
                   "hydration", "diuretic", "electrolytes")

# A job is never a baby's age. "is it ok to leave a job after three months" read "three months"
# as a stage and was answered by the feeding table's punt, because the age is the only thing in
# the line this domain knows. Every row here carries STAND_DOWN, so the job words go in the
# shared fence. The bare "work" is not in it: "my baby is 6 months and i go back to work" is
# still a feeding line, and only the job nouns hold a line out.
JOB_WORDS = ("job", "jobs", "my job", "new job", "job offer", "leave a job", "leaving a job",
             "left a job", "quit my job", "quitting my job", "boss", "employer", "employee",
             "career", "resign", "resigning", "resignation", "hand in my notice",
             "handing in my notice", "notice period", "interview", "salary", "my salary")

STAND_DOWN = (NOT_A_MENU + _HOW_MUCH_MILK + NOT_A_BABY + WEANING_ELSEWHERE + NOT_AN_AGE
              + SPICE_NAMES + NOT_ABOUT_WATER + JOB_WORDS)

# A book for the baby is not the readiness question, and "read" reaches this domain's "ready"
# because the words are matched in their loose form: "what book should i read to my baby" was
# the three-signs card. "read" itself cannot go in an avoid list here - it would stand the row
# down for every "ready" line too - so the book nouns hold the line out instead.
BOOK_WORDS = ("book", "books", "novel", "picture book", "story", "stories", "read to",
              "reading to", "read aloud")

# --- the age table ---------------------------------------------------------------------
# One row per stage a person asks about, in months, so a line that names an age is answered from
# the table rather than from whichever food word happened to be in it. `until` is the age the
# row stops applying at, and a stage with `until` None runs on to two years.
STAGES = (
    {"from": 0, "until": 5,
     "reply": "Milk is all a baby needs before about six months, and food before four months "
              "is not recommended at all. If they seem hungrier, more milk is the answer - ask "
              "your health visitor before starting anything early."},
    {"from": 6, "until": 8,
     "reply": "At this age milk is still the main food, so treat eating as practice: two or "
              "three small goes a day of soft food they can hold - cooked carrot or broccoli, "
              "toast fingers, banana, plain yoghurt, mashed lentils. One new food at a time, a "
              "few days apart, so a reaction is easy to spot."},
    {"from": 9, "until": 11,
     "reply": "By now it is three meals a day plus milk, and what they eat starts to matter: "
              "chopped versions of your own meal, soft meat or fish with the bones out, pasta, "
              "beans and lentils, fruit, full-fat dairy. No added salt or sugar, and no honey "
              "before the first birthday."},
    {"from": 12, "until": None,
     "reply": "From one they can eat what the rest of the family eats: three meals and two "
              "snacks, whole cows milk as a drink at about 350 to 400ml a day, and no added "
              "salt. Honey is fine from now on."},
)

# A number written as a word, for "my baby is one what can they eat now": the engine reads a
# typed figure, and this reads the word, so both spellings of the same age answer alike.
_NUMBER_WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                 "ten", "eleven", "twelve")

# --- the verdict table ------------------------------------------------------------------
# One row per food or drink people ask about: the words they call it and the answer. The answer
# opens with the verdict, because the question is nearly always a yes/no one, then gives the age
# and the one thing that matters.
FOODS = (
    {"names": ("yogurt", "yoghurt", "yoghurts", "yogurts", "fromage frais", "greek yogurt",
               "greek yoghurt", "kefir", "skyr"),
     "reply": "Yes, plain full-fat yoghurt is fine from six months. Buy natural or Greek rather "
              "than the children's fruit pots, which are mostly sugar - stir in mashed fruit "
              "instead - and give it with a meal rather than as a drink."},
    {"names": ("cheese", "cheddar", "cheeses", "parmesan", "mozzarella", "cream cheese",
               "brie", "camembert", "blue cheese", "stilton", "gorgonzola", "roquefort",
               "mould ripened", "mold ripened", "soft cheese", "goats cheese", "feta"),
     "reply": "Yes, from six months, in small amounts, because cheese is salty: about 25g a day "
              "is plenty for a little one. Stick to pasteurised cheese - brie, camembert and "
              "blue cheese are the ones to leave raw, and they are fine once cooked until "
              "steaming hot."},
    {"names": ("egg", "eggs", "scrambled egg", "boiled egg", "omelette"),
     "reply": "Yes, well cooked, from six months: scrambled egg, a hard-boiled egg mashed with "
              "a fork, or omelette cut into fingers. An egg with the red lion stamp can be given "
              "runny because those hens are vaccinated; without the stamp, cook it until white "
              "and yolk are both solid."},
    {"names": ("strawberry", "strawberries", "raspberry", "raspberries", "blueberry",
               "blueberries", "berries", "blackberries"),
     "reply": "Yes, from six months - cut them in half or quarters, because a round berry is a "
              "choking shape. Berries are acidic, so they can bring on a red nappy rash, and "
              "that is not an allergy; a rash round the mouth that fades on its own is usually "
              "the same thing."},
    {"names": ("peanut butter", "peanut", "peanuts", "nut butter", "almond butter",
               "nut", "nuts", "almonds", "cashews", "almond"),
     "reply": "Yes, and early is better than late: from six months, a thin smear of smooth "
              "peanut butter on toast or stirred into porridge. Never a spoonful on its own and "
              "never a whole nut - those are choking shapes, so use ground or butter only. "
              "Offer it on a day they are well, in the morning, then keep it in their week."},
    # Raisins are the one dried fruit people ask about by name and the one that got the
    # health-visitor hedge, because no card names them: a handful is a choking shape and a
    # sticky thing on the teeth, which is a verdict worth saying in that order.
    {"names": ("raisins", "raisin", "sultanas", "sultana", "dried fruit", "dried apricots",
               "prunes", "dates", "currants", "cranberries", "dried cranberries"),
     "reply": "Yes, from six months, but chop them: a whole raisin is the shape that blocks a "
              "small throat and it is sticky enough to sit on the teeth, so cut each one in "
              "half, give them with a meal rather than as a snack on their own, and keep them "
              "to a small handful a day. Dried fruit counts as one of the five a day, so it is "
              "not a substitute for fresh fruit - and never dried fruit with added sugar or "
              "yoghurt coating."},
    # Tea is the everyday drink a baby is most often offered a sip of at a table, and the card
    # that came back was the milk-and-water one, which never mentions it. The answer is no, and
    # the reason is the iron: the tannins in tea stop it being absorbed, and the caffeine is
    # not something a small body needs.
    {"names": ("tea", "teas", "green tea", "herbal tea", "camomile tea", "chamomile tea",
               "peppermint tea", "fruit tea", "coffee", "cola", "coke", "energy drink",
               "energy drinks", "caffeine", "fizzy drink", "fizzy drinks", "diet coke"),
     # A child of twelve is not this table's line, and the caffeine card that main has for
     # "can my child have caffeine" says the better thing for that age - the amounts and the
     # sleep - so the words that make a line a child's stand this row down.
     "extra": ("child", "children", "kid", "kids", "toddler", "toddlers", "teen", "teens",
               "teenager", "teenagers", "school", "year old", "12", "under 12", "10", "14",
               # "does drinking coffee dehydrate you" is an adult's drink question, and the
               # health row beside this one answers it: nothing about dehydration is a weaning
               # question, so the named drink does not carry this table's row into it.
               "dehydrat", "dehydrate", "dehydrates", "dehydrated", "dehydrating",
               "dehydration", "hydrate", "hydrated", "hydration"),
     # The drinks card answers "how much should a baby drink" and it was winning this one on
     # the word "drink", so the named drink has to outrank it: a question that names the drink
     # is not the question about how much.
     "bias": 3,
     "reply": "No, not as a drink: tea and coffee both carry caffeine a small body does not "
              "need, and the tannins in tea stop iron being absorbed, which matters most in the "
              "first two years. Cola, energy drinks and fizzy drinks are the same answer with "
              "sugar on top, and herbal teas are no better for a baby. Milk and water are the "
              "drinks: breast milk or formula before one, whole cows milk from one, and water "
              "in an open cup with meals from six months."},
    {"names": ("liver", "lamb's liver", "chicken liver", "kidney", "pate", "liver pate", "paté"),
     "reply": "Liver is fine from six months, but once a week at most: it is packed with vitamin A "
              "and iron, and too much vitamin A builds up. Cook it through, mash or blend it into "
              "something they already eat, and count liver, liver pate and cod liver oil as the "
              "same thing in that week. Pate itself is salty, so leave that until after the first "
              "birthday and then keep it to a thin scrape."},
    {"names": ("crisps", "crisp", "chips", "wotsits", "quavers", "cheese puffs"),
     "reply": "No, not before one, and rarely after: crisps are salty and they are a choking "
              "shape, and the same goes for chips with salt on. A handful of soft veg sticks, "
              "toast fingers or a bit of cheese is the same idea without the salt."},
    {"names": ("wheat", "soya", "soy", "sesame", "gluten"),
     "reply": "Yes, from six months, and early is the point: wheat, soya and sesame are three of "
              "the allergens to give in the first year, one at a time, on a day they are well and "
              "in the morning. Bread, pasta, cereal, tofu and tahini all count, and once a food "
              "is in, keep giving it a couple of times a week rather than stopping."},
    {"names": ("cows milk", "cow's milk", "whole milk", "full fat milk", "semi skimmed milk"),
     "reply": "Not as a drink before twelve months: it has too little iron and too much salt "
              "and protein for a baby. You can cook with it, or put a splash on cereal, from six "
              "months. From one, give whole milk, about 350 to 400ml a day."},
    {"names": ("water", "juice", "fruit juice", "squash", "cordial", "orange juice",
               "apple juice", "smoothie", "smoothies", "milkshake", "milkshakes"),
     "own_ask": _the_water_ask,
     # A toddler's drinks are counted in litres, which another row already does: this one is
     # about what goes in the cup the first time.
     # "how much water should my baby drink" reached the litre-a-day card for a toddler, so
     # only the words that name somebody bigger stand this row down now.
     "extra": ("toddler", "toddlers", "litre", "litres", "2 year", "3 year", "4 year",
               "5 year", "child", "children", "kids", "i drink", "should i drink",
               "how much should i"),

     # The first clause has to be safe for the youngest parent asking: "water is the drink to
    # offer" was the first sentence a mother of a four month old read.
    "reply": "Not before six months - milk is all they need, and extra water can upset their "
              "salts. From six months, water is the drink to offer in an open cup with meals, and "
              "juice or squash is not needed at any age: if you give it, wait until twelve months, "
              "dilute it, and keep it to a meal in a cup rather than a bottle."},
    # Honey is the one food with an answer of its own already, in the cooking table, and it is a
    # good one: it names the porridge, the dummy and the cough remedy. Two rows for one fact
    # means the day they disagree the bot gives one of them to somebody, so this table leaves it.
    {"names": ("salt", "salty", "stock cube", "stock cubes", "gravy", "bacon", "ham",
               "sausages", "sausage", "salted", "marmite", "yeast extract", "bovril",
               "soy sauce", "baked beans", "beans on toast", "tomato ketchup", "ketchup",
               "brown sauce", "mayonnaise", "mayo", "soup", "soups", "gravy granules",
               "stock", "salted butter"),
     "reply": "No salt at all in their food before one, and very little after: a baby's kidneys "
              "cannot cope with it. That rules out stock cubes, gravy granules, bacon, ham, "
              "sausages and most sauces - cook their portion separately and season yours."},
    {"names": ("sugar", "sweets", "chocolate", "biscuits", "biscuit", "cake", "cakes",
               "jelly", "jam", "marmalade", "rice pudding", "custard"),
     "reply": "There is no need for sugar at all before two, and it is worth keeping it that "
              "way while you can, because it is what makes them prefer sweet food later. Fruit "
              "is the sweet thing to give, and cheese or toast makes a better snack than a "
              "biscuit."},
    {"names": ("grapes", "grape", "cherry tomatoes", "cherries", "olives", "hot dog", "hot dogs"),
     "reply": "Yes, but cut them: grapes, cherry tomatoes and olives go lengthways into "
              "quarters and sausages lengthways into strips, because the round shape is what "
              "blocks a small throat. Whole grapes are the food toddlers choke on most, and "
              "popcorn is not one to give before about four."},
    # Everything below was a shrug: a common food asked about by name, and no row of the table
    # named it, so "can my baby have popcorn" was the grapes card ("Yes, but cut them") and
    # "can my baby have tofu" was the health visitor's line.
    {"names": ("popcorn", "pop corn", "puffed corn", "corn snacks"),
     "reply": "No, not before about four: popcorn is light, hard and the exact shape that lodges "
              "in a small airway, and it is the food toddlers choke on most after grapes. Puffed "
              "corn snacks are the same shape and salty as well, so leave those too, and keep "
              "crisps for an occasional treat after one, sitting down."},
    {"names": ("rice cake", "rice cakes", "corn cake", "corn cakes", "oat cake", "oat cakes",
               "crackers", "cracker", "breadsticks", "bread sticks", "rusks", "rusk"),
     "reply": "Yes, from six months, and they are good for the pincer grip - but read the packet "
              "first, because they are often the saltiest thing in the baby aisle. Unsalted rice "
              "cakes, plain oatcakes and no-salt breadsticks are the ones to pick; a rusk is "
              "mostly sugar, so treat it as a biscuit rather than a food."},
    {"names": ("cucumber", "cucumbers", "tomato", "tomatoes",
               # Bare "pepper" is the spice, not this row's vegetable: "can i put pepper in my
               # babys food" was answered "cucumber and tomato cut into finger-length batons",
               # while the spice row - which says black pepper in cooking is fine - is the row
               # that answers it. A pepper that is the vegetable says so in the line (bell, red,
               # green, sweet), and the spice row takes the rest.
               "bell pepper", "bell peppers", "red pepper", "green pepper", "sweet pepper",
               "lettuce", "celery", "radish", "radishes",
               "spring onion", "spring onions", "beetroot", "raw carrot", "carrot sticks"),
     "reply": "Yes, from six months, raw or cooked: cucumber and tomato cut into finger-length "
              "batons or quarters are two of the easiest first finger foods, because a baby can "
              "hold them and gum them. Cherry tomatoes and olives go lengthways into quarters, "
              "and celery strings are worth peeling off before you hand it over."},
    {"names": ("tofu", "bean curd", "edamame", "soya bean", "soy bean", "tempeh"),
     "reply": "Yes, from six months, cooked through: tofu cut into strips is soft enough to gum, "
              "and it takes on whatever it is cooked in. It is soya, so introduce it the way you "
              "would peanut - a little on its own the first time, then watch for two hours - and "
              "keep it plain rather than in a salty marinade."},
    # Quorn is not soya, and it was in the tofu row's own names: "can my baby have quorn" was
    # told "It is soya, introduce it the way you would peanut", which is wrong about the food.
    {"names": ("quorn", "mycoprotein", "quorn mince", "quorn pieces", "meat free mince",
               "veggie mince", "vegetarian mince"),
     "reply": "Yes, from six months, cooked through and chopped small: Quorn is mycoprotein, a "
              "fungal protein rather than soya, and the plain mince and pieces are low in salt "
              "and fine for a baby. It is a protein swap rather than a whole food, so give it "
              "with something iron-rich - lentils, beans or a little meat - and read the packet "
              "on the breaded and ready-made versions, which are salty."},
    # Raw fish and cured fish are their own verdict: the cooked-fish row says "well cooked and
    # every bone out", which is the wrong advice for sushi and for a slice of smoked salmon.
    {"names": ("sushi", "sashimi", "raw fish", "raw prawns", "smoked salmon", "smoked mackerel",
               "gravadlax", "gravalax", "cured fish", "oysters"),
     "reply": "Sushi is fine once the fish in it is cooked: a cooked prawn or salmon roll, or a "
              "vegetable one, is a good finger food from six months. Raw fish and raw shellfish "
              "wait until they are five, because of the parasites and the bones. Smoked salmon "
              "is cured rather than cooked and it is salty, so a flake now and then is the most "
              "of it.",
     "bias": 2},
    {"names": ("fish", "salmon", "tuna", "cod", "prawns", "shellfish", "prawn", "mussels"),
     "reply": "Yes, well cooked and with every bone out - flake it and check between your "
              "fingers first. Oily fish like salmon once or twice a week is worth having. Leave "
              "out shark, swordfish and marlin, and keep tuna to about one small tin a week."},
    {"names": ("toast", "bread", "crumpet", "pitta", "cracker", "crackers", "chapati",
               "chapatis", "naan", "roti", "wrap", "wraps", "bagel", "bagels", "scone",
               "scones", "teacake"),
     "reply": "Yes, from six months - toast fingers are one of the easiest first foods because "
              "a baby can hold them. White, wholemeal or a mix is fine; bread has salt in it "
              "already, which is a reason not to add more, not a reason to wait.",
     # "can i give him toast" is the food; "give him a toast" is the speech, and "raise a
     # glass" is the same speech. The article is the whole difference.
     "pronoun": True,
     "extra": ("a toast", "raise a glass", "raise the glass", "speech", "speeches",
               "wedding", "best man", "eulogy", "few words", "say a few words")},
    # A bottle is not a menu: "can i put cereal in my babys bottle" is about a bottle feed, and
    # the water row keeps "can my baby have water in a bottle" because this is that row's only.
    {"names": ("banana", "bananas"),
     "reply": "Yes, from six months, and it is one of the easiest first foods: mash it or cut it "
              "into finger-length pieces a baby can hold. It is sweet and soft, so it goes down "
              "on a day when nothing else does."},
    {"names": ("avocado", "avocados", "guacamole", "avocado pear"),
     "reply": "Yes, from six months: ripe avocado mashed on toast fingers, or in a wedge they can "
              "hold with the skin as a handle. The fat in it is the kind a growing baby needs, "
              "and its blandness sits well next to a stronger taste."},
    {"names": ("broccoli", "cauliflower", "courgette", "carrot", "carrots", "sweet potato",
               "butternut squash", "parsnip", "peas", "green beans", "spinach", "kale",
               "leeks", "swede", "turnip", "asparagus", "plantain", "mushroom", "mushrooms",
               "mange tout", "sugar snap peas", "runner beans", "cabbage", "brussels sprouts",
               "cauliflower cheese"),
     "reply": "Yes, from six months, cooked soft enough to squash between your fingers - a whole "
              "floret or a stick of carrot is a handle a baby can hold and gum. Keep offering "
              "the ones they refuse: it can take ten tries before a vegetable is eaten."},
    {"names": ("potato", "potatoes", "mash"),
     "reply": "Yes, from six months: mashed potato with a little of their usual milk or unsalted "
              "butter, or soft roast potato in strips. No salt in the water or on top, and skip "
              "chips and crisps, which are salty and hard to manage."},
    {"names": ("pasta", "fusilli", "penne", "macaroni", "spaghetti", "noodles"),
     "reply": "Yes, from about six months once they can pick things up: shapes like fusilli or "
              "penne are easier to hold than spaghetti, and cook them a minute past the packet "
              "so they are soft. Cut long pasta, and keep the sauce low in salt."},
    {"names": ("rice", "couscous", "quinoa", "bulgur"),
     "reply": "Yes, from six months, cooked soft - as a mash, or pressed into a sticky ball they "
              "can pick up. No salt in the water. Cooked rice is the one to be careful with: cool "
              "it fast, fridge it within the hour, and reheat it once, hot all through."},
    {"names": ("hummus", "houmous", "chickpeas"),
     "reply": "Yes, from six months: spread it thin on toast fingers or let them dip a finger of "
              "pitta in it, and it counts as a portion of protein. Shop hummus can be salty, so "
              "a plain one or your own is better."},
    {"names": ("lentils", "dhal", "daal", "beans", "kidney beans", "chick pea", "pulses"),
     "reply": "Yes, from six months: red lentils cook down into a thick dhal they can eat from a "
              "spoon or with bread, and mashed beans go into a sauce the same way. Pulses are a "
              "good source of iron, and a squeeze of lemon or some tomato helps the iron go in."},
    {"names": ("mango", "melon", "watermelon", "peach", "pear", "plum", "nectarine",
               "blueberries", "raspberries", "kiwi", "kiwis", "pineapple", "coconut",
               "grated coconut", "strawberry", "strawberries", "blackberries", "cherries",
               "apricot", "apricots", "papaya", "fig", "figs", "orange", "satsuma",
               "mandarin", "clementine"),
     "reply": "Yes, from six months: soft ripe fruit in strips or wedges they can hold, and a "
              "wedge with the skin on makes a handle to gnaw. Round fruit is the one to cut - "
              "berries in half, grapes lengthways - and stay with them while they eat it."},
    {"names": ("chicken", "beef", "lamb", "pork", "mince", "meat"),
     "reply": "Yes, from six months: soft cooked meat in strips they can hold, or minced into a "
              "sauce, and it is the best source of the iron a baby uses up at about six months. "
              "A strip of well-cooked chicken or a lamb chop bone is a good thing to gnaw, with "
              "the gristle and small bones taken out."},
    {"names": ("porridge", "oats", "cereal", "baby rice"),
     "extra": ("bottle", "bottles", "in a bottle", "in the bottle", "bottle feed"),
     "reply": "Yes, from six months, and ordinary porridge oats made with their usual milk are "
              "as good as any baby cereal, with no added sugar or salt. Baby rice is almost all "
              "starch, so it fills them up without feeding them much."},
)

# A line that asks what to feed and names no age is still asking about the beginning, so it gets
# the first-foods answer: "what should i feed my baby first", "what can i feed my baby".
_FIRST_FOODS = (
    "Start with soft food they can hold themselves rather than something on a spoon: cooked "
    "carrot or broccoli, toast fingers, ripe pear, banana, avocado, or a spoon of plain "
    "yoghurt. One food at a time, a few days apart, so a reaction is easy to spot, and milk "
    "first so they are not too hungry to try. How much is a few spoonfuls or a few sticks at "
    "the start, half a fist by nine months and about a fist at a year. Around six months is the "
    "age, unless a health visitor has said otherwise.")

# The shapes of "what should I feed it", which is the same question whatever the age. The feed
# row carries them as well as the stage row, because a line framed as "what can i give a 6 month
# old" is read with "can" and "give" as framing and the stage row has to name the framing to see
# the age in it at all.
_WHAT_TO_FEED = ("what can", "what should", "what do", "what to", "what shall", "what could",
                 "what will", "what food", "what foods", "what food do i", "how much", "how many",
                 "how often", "when can", "when should", "when do", "is it ok to", "can i give",
                 "can i feed", "can i start", "can they have", "can she have", "can he have",
                 "where do i start")


def _text(understood):
    """The line as lower-case words, digits and all."""
    words = understood.get("words") if isinstance(understood, dict) else None
    if isinstance(words, (list, tuple)) and words:
        return " ".join(str(word) for word in words).lower()
    return str((understood or {}).get("clean") or "").lower()


# A figure and its unit typed into the chat: "7 months", "13 mths", "2 yrs".
_AGE_FIGURE = re.compile(r"\b(\d{1,2})\s*-?\s*(month|months|mth|mths|year|years|yr|yrs)\b")


def _age_in_the_chat(memory, understood):
    """The age the conversation gave a turn or two ago, for a line that only says "he".

    "my little one is 7 months old" then "how much milk should he have now" is one question in
    two halves, and the second half names the baby with a pronoun and no age. The bands are only
    useful if the age travels, so a pronoun line reads back through what the person typed before
    it. Nothing else does: a line that names an age of its own is never second-guessed, and a
    line with no pronoun is not read as one about the baby of three turns ago.
    """
    words = {str(word).lower() for word in (understood.get("words") or ())}
    if not words & set(_THE_CHILD):
        return None
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return None
    said_now = str(understood.get("clean") or "").strip().lower()
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("user") or "").strip().lower()
        if not text or text == said_now:
            continue
        numbers = [{"value": int(match.group(1)), "unit": match.group(2)}
                   for match in _AGE_FIGURE.finditer(text)]
        age = _age_in_months({"clean": text, "words": text.split(), "numbers": numbers})
        if age is not None:
            return age
    return None


def _age_in_months(understood):
    """The age the line gives, in months, or None when it names none.

    A figure with a unit ("9 month old", "13 months", "1 year") is read from the engine's own
    numbers, so a line written in digits and a line written in words read the same. A bare
    figure after "baby is" is only read when it is a 1, which is how a person says a first
    birthday; any other bare figure is too ambiguous to guess at, and no age is better than a
    wrong stage.
    """
    for number in understood.get("numbers") or ():
        if not isinstance(number, dict):
            continue
        value = number.get("value")
        if not isinstance(value, int) or value < 0:
            continue
        unit = str(number.get("unit") or "").lower()
        if unit.startswith("month"):
            return value
        if unit.startswith("year"):
            return 12 * value
        if unit.startswith("week"):
            return 0
    said = _text(understood)
    if re.search(r"\bbaby is (one|1)\b", said) or re.search(r"\b(one|1) year old\b", said):
        return 12
    for words in _NUMBER_WORDS:
        if re.search(r"\b%s\s+months?\b" % words, said):
            return _NUMBER_WORDS_AT[words]
        # "my two year old, what should i feed her": the age is spelled and the unit is the
        # word "old", so the figure-with-a-unit reader above never sees it.
        if re.search(r"\b%s\s+years?[\s-]*old\b" % words, said):
            return 12 * _NUMBER_WORDS_AT[words]
    # "my kid 4, what should i feed him", "my daughter 6": the verb is left out and so is the
    # unit, which is how people type, and the older-child word is the only thing that says the
    # figure is years. Beside "baby" the same figure is months and stays unread, as before.
    if any(re.search(r"\b%s\b" % word, said) for word in _OLDER_CHILD_WORD):
        bare = re.search(r"\b(?:%s)\s+(?:is\s+|are\s+|aged\s+|at\s+|of\s+)?(\d{1,2})\b"
                         r"(?!\s*(?:month|months|mth|mths|week|weeks|wk|wks|day|days|stone|"
                         r"kilos|kilo|kg|lbs|pounds)\b)"
                         % "|".join(_OLDER_CHILD_WORD), said)
        if bare and 2 <= int(bare.group(1)) <= 19:
            return 12 * int(bare.group(1))
    if re.search(r"\b(toddler|toddlers)\b", said):
        return 12
    if re.search(r"\b(newborn|newborns)\b", said):
        return 0
    return None


_NUMBER_WORDS_AT = {word: index + 1 for index, word in enumerate(_NUMBER_WORDS)}


def _stage(understood):
    """The reply for the stage the line's age lands on, or None when it names no age."""
    age = _age_in_months(understood)
    if age is None:
        return None
    for stage in STAGES:
        until = stage["until"]
        if age >= stage["from"] and (until is None or age <= until):
            return stage["reply"]
    return None


# How much milk a baby drinks is not the water question, and the card that answers a water
# question gives the toddler and school-age figures - a litre, six to eight cups - which is the
# wrong number for a baby of any age under one. The figure is a band, and the band is the age the
# line names: milk alone before six months, mostly milk to a year, three or four cups after.
_MILK_WORDS = ("milk", "breastmilk", "breast milk", "expressed milk", "expressed")
_MILK_HOW_MUCH = ("how much", "how many", "how often", "much milk", "much breastmilk",
                  "many ounces", "how many oz",
                  # "what milk should i give my 1 year old" was the toddler's litre of water
                  "what milk", "which milk", "what kind of milk", "what type of milk",
                  "best milk", "right milk")
# A drink for somebody else, or not a drink at all: the toddler and the school child keep the
# litre card, an adult's own glass is not this table, and milk in a recipe is the kitchen's.
_NOT_A_BABY_MILK = ("toddler", "toddlers", "2 year", "two year", "3 year", "three year",
                    "4 year", "four year", "5 year", "five year", "child", "children", "kids",
                    "should i drink", "i drink", "i have", "can i have", "adult", "pump",
                    "pumping", "recipe", "latte", "cappuccino", "protein", "calcium")

# The verbs a quantity of milk comes with: "how much milk should my baby drink", "how much milk
# does a 9 month old need". Without one of them the row ties with the row that gives the toddler
# and school-age water figures, and a tie went to that row.
_A_DRINK = ("drink", "drinks", "drinking", "have", "has", "need", "needs", "take", "takes")

# A count is an amount of milk, not a menu and not a cup: "how many ounces should a 3 month old
# drink" is the eight to twelve feeds question.
_A_COUNT = ("how many ounces", "how many oz", "how many ml", "how many mls", "ounces", "oz",
            "ml", "mls")

# A follow-up names the baby with a pronoun and no age: "how much milk should he have now". The
# row answers with every band rather than nothing, because the band the person needs is in it and
# the alternative on main was the litre-a-day figure for a school child.
_THE_CHILD = ("he", "she", "him", "her", "they", "them")

_MILK_UNDER_SIX = (
    "Milk is the whole diet before six months, so there is no set amount: eight to twelve "
    "feeds in 24 hours, on demand, day and night. Six or more wet nappies a day and a baby who "
    "settles after a feed mean they are getting enough, and the scales settle it better than the "
    "ounces. Nothing else goes in the bottle - no cereal, no water unless it is hot.")
_MILK_SIX_TO_TWELVE = (
    "About 500 to 600ml (17 to 20oz) of breast milk or formula a day from six to twelve months, "
    "in four or five feeds, and food goes alongside it rather than instead of it: milk is still "
    "the main drink until the first birthday, and the wet nappies still say whether it is enough.")
_MILK_OVER_ONE = (
    "About 350 to 400ml (12oz) a day of whole cows milk from one, in a cup rather than a bottle: "
    "that much covers the calcium without filling them up before meals, and more than about "
    "500ml crowds out the iron in food.")


_WATER_UNDER_SIX = (
    "Under six months, none: milk is all they need and extra water can upset the salts in a "
    "small body. From six months, offer a little water in an open cup with meals - a few sips is "
    "enough, and they will take what they need rather than a set amount. From one, water with "
    "every meal and between meals as they ask for it, and that is when a cup measuring roughly a "
    "litre a day starts to make sense.")
_WATER_OVER_ONE = (
    "Water with every meal and between meals whenever they ask for it: a cup measuring roughly a "
    "litre a day is the toddler figure, and the milk they drink counts towards it. Leave the cup "
    "where they can reach it and refill it without a fuss. Under six months it was none, because "
    "extra water upsets the salts in a small body, so do not go back to that unless a doctor says "
    "so.")
_WATER_NO_AGE = (
    "Under six months, none: milk is all they need and extra water can upset the salts in a "
    "small body. From six months, offer a little water in an open cup with meals - a few sips is "
    "enough, and they will take what they need rather than a set amount. From one, water with "
    "every meal and between meals as they ask for it, and that is when a cup measuring roughly a "
    "litre a day starts to make sense.")
_WATER_JUICE = (
    " Juice and squash are not needed at any age: if you give juice at all, wait until twelve "
    "months, dilute it, and keep it to a meal in a cup.")


def _how_much_water(memory, understood):
    """How much water, for the age the line gives or the chat already knows."""
    age = _age_in_months(understood)
    if age is None:
        age = _age_in_the_chat(memory, understood)
    if age is not None and age < 6:
        return _WATER_UNDER_SIX + _WATER_JUICE
    if age is not None and age >= 12:
        return _WATER_OVER_ONE + _WATER_JUICE
    return _WATER_NO_AGE + _WATER_JUICE


def _milk_volume(memory, understood):
    """How much milk, for the age the line gives - and for all three bands when it gives none."""
    age = _age_in_months(understood)
    if age is None:
        age = _age_in_the_chat(memory, understood)
    if age is not None and age < 6:
        return _MILK_UNDER_SIX
    if age is not None and age < 12:
        return _MILK_SIX_TO_TWELVE
    if age is not None:
        return _MILK_OVER_ONE
    return _MILK_UNDER_SIX + " " + _MILK_SIX_TO_TWELVE + " " + _MILK_OVER_ONE


# What goes in the cup, for the age the line gives. One static paragraph was wrong for the older
# lines: it led with the under-six rule for "how much should a 1 year old drink", which is a
# confident wrong answer to a question whose right answer is a litre a day.
_DRINK_UNDER_SIX = (
    "Milk is the only drink before six months - breast milk or formula, on demand, and nothing "
    "else in the bottle, not even water.")
_DRINK_SIX_TO_TWELVE = (
    "Milk is still the main drink at this age: breast milk or formula on demand, and water in an "
    "open cup with meals from six months. A free-flow cup or a straw cup is better than a bottle "
    "from six months, since the sucking is what makes the fuss. Juice and squash are not needed "
    "at any age; if you give juice at all, wait until twelve months, dilute it, and keep it to a "
    "meal.")
_DRINK_OVER_ONE = (
    "About a litre a day for a one-year-old, and the milk they drink counts towards it: whole "
    "cows milk at roughly 350 to 400ml of that, in a cup rather than a bottle, and water with "
    "every meal and whenever they ask. Leave the cup where they can reach it and refill it "
    "without a fuss. Juice and squash are not needed; if you give juice, dilute it and keep it "
    "to a meal in a cup.")


def _what_a_baby_drinks(memory, understood):
    """What goes in the cup, for the age the line gives or the chat already knows."""
    age = _age_in_months(understood)
    if age is None:
        age = _age_in_the_chat(memory, understood)
    if age is not None and age < 6:
        return _DRINK_UNDER_SIX
    if age is not None and age < 12:
        return _DRINK_SIX_TO_TWELVE
    if age is not None:
        return _DRINK_OVER_ONE
    return _DRINK_UNDER_SIX + " " + _DRINK_SIX_TO_TWELVE + " " + _DRINK_OVER_ONE


# A snack, as opposed to a meal or a weaning question: the word the person uses, and a child to
# give it to. "Snack" is also the word in front of a film or a party, and those lines are not
# about a baby at all, so the row stands down for them.
_SNACK = ("snack", "snacks", "snacking", "a snack", "between meals", "in between meals",
          "little and often")
_SNACK_CHILD = _BABY + AGE + ("child", "children", "kid", "kids", "1 year old", "2 year old",
                              "3 year old", "4 year old", "school age")
_NOT_A_SNACK = ("party", "parties", "buffet", "guests", "film", "films", "movie", "match",
                "half time", "picnic", "me", "myself", "adult", "adults", "for the adults",
                "recipe", "make ahead", "christmas", "birthday", "wedding", "work")

_SNACK_UNDER_SIX = (
    "No snacks before six months: milk is the whole of it, and a baby that young does not need "
    "anything between feeds, only more milk.")
_SNACK_SIX_TO_TWELVE = (
    "From six months, two or three small goes a day at set times rather than all day long, and "
    "the best snacks are the ones they can hold: toast fingers, soft fruit, cooked veg sticks, "
    "plain yoghurt, a little cheese, oatcakes. Keep away from the choking shapes - whole grapes, "
    "whole nuts, popcorn - and sit them down while they eat.")
_SNACK_OVER_ONE = (
    "Two snacks a day between meals is right from one: fruit, plain yoghurt, toast, oatcakes, "
    "cheese, veg sticks. Keep them at set times rather than in the hand all afternoon, because a "
    "child who grazes does not sit down for the meal, and keep the choking shapes - whole grapes, "
    "whole nuts, popcorn - for later.")


def _snacks(memory, understood):
    """What to give between meals, banded by the age the line names."""
    age = _age_in_months(understood)
    if age is None:
        age = _age_in_the_chat(memory, understood)
    if age is not None and age < 6:
        return _SNACK_UNDER_SIX
    if age is not None and age < 12:
        return _SNACK_SIX_TO_TWELVE
    if age is not None:
        return _SNACK_OVER_ONE
    return _SNACK_SIX_TO_TWELVE + " " + _SNACK_OVER_ONE


def _says_what_they_eat(understood):
    """Whether the line is about eating at all, or only has a baby and a question in it.

    The key can only insist on one part after the first two, and an age and an ask are both
    reachable without a word of eating: "my baby is breathing fast what should i do" and "what do
    i need for a newborn" each name the age and the ask and nothing to do with food. So the eating
    word is checked here, in the reply itself, where both can be required at once.
    """
    said = _text(understood)
    padded = " %s " % said
    return any(" %s " % word in padded for word in EATING)


_PLANT_MILK_BABY = (
    "Not as their main drink, no. A baby under a year needs breast milk or first infant formula, "
    "and a plant milk does not have the protein, fat, calcium or vitamins to stand in for it. In "
    "cereal, porridge or cooking from six months it is fine - choose one with no sugar and with "
    "calcium and vitamin D added."
)
_PLANT_MILK_RICE = (
    "Rice milk is the one to leave out completely before five years: it has arsenic in it, which "
    "a small body clears slowly, and a child drinking it daily can take in too much. Oat, soya or "
    "coconut milk, unsweetened and fortified, are the better swaps over one."
)
_PLANT_MILK_CHILD = (
    "Yes, as a drink now - unsweetened and with calcium and vitamin D added, and it does not "
    "replace their food. Soya is the only one with protein close to cows milk, so it is the usual "
    "swap; rice milk still waits until five."
)


def _plant_milk(memory, understood):
    """A plant milk by the age of the child, because the answer changes twice.

    Under a year it is not a drink at all; rice milk is out until five whatever the age; over a
    year an unsweetened fortified one is a fair swap. The words are read the same way the milk
    bands are - the age in the line first, then the age the chat gave - so a follow-up gets the
    same answer as the question it follows.
    """
    age = _age_in_months(understood)
    if age is None:
        age = _age_in_the_chat(memory, understood)
    said = _text(understood)
    rice = "rice" in said
    if age is None:
        return _PLANT_MILK_BABY + " " + _PLANT_MILK_RICE
    if age < 12:
        return _PLANT_MILK_BABY + (" " + _PLANT_MILK_RICE if rice else "")
    if rice:
        return _PLANT_MILK_RICE
    return _PLANT_MILK_CHILD


def _by_age(memory, understood):
    """The stage the line names, and the first foods for a line that names no age.

    A line with no word of eating in it is not answered from this table at all: returning None
    lets it go on to the row that does answer it.
    """
    if not _says_what_they_eat(understood):
        return None
    return _stage(understood) or _FIRST_FOODS


# The words that turn a food named in a line into a question about it: "can my baby *have*
# cheese", "is it ok to *give* a 6 month old toast", "when can babies *drink* water". Only the
# bare "my baby loves yoghurt" is left out, because it is not asking anything.
# The phrases are in the list as well as the single words, because a line is read with its
# framing taken out - "can i give my baby porridge" loses "can i give" before the parts are
# counted - and a row that names the framing keeps it. Without them "can i give my baby porridge
# for breakfast" was answered by the first-foods row on "breakfast" alone.
_VERDICT_ASK = ("have", "has", "give", "gives", "giving", "eat", "eats", "eating", "feed",
                "drink", "drinks", "try", "ok", "safe", "allowed", "much", "many", "any",
                "can i give", "can i feed", "can i put", "can i try", "am i allowed",
                "is it ok to", "should i give", "ok to give", "safe to give",
                "when can", "when should")


# How a parent names the child when they do not say "baby": "can my son eat grapes", "can my
# child have cheese", "is honey ok for my daughter". None of these is in BABY, so before this
# list the row was never reached and the line fell through to "I don't know enough to answer
# that honestly" - a punt where the answer was one word away. A per-food verdict is right for a
# child of any age (cheese is salty at eight as it is at eight months), so these are not capped
# by the age the pronoun path uses: "my son is 8 months old what can he eat" reads its own age.
_A_CHILD = ("son", "sons", "daughter", "daughters", "child", "children", "kid", "kids",
            "boy", "boys", "girl", "girls", "little boy", "little girl", "grandchild",
            "grandchildren", "grandson", "granddaughter", "stepson", "stepdaughter")


# Everything that names a baby, minus the bare month unit: see _UNIT_WITHOUT_FIGURE.
_NAMES_A_BABY = tuple(word for word in BABY if word not in _UNIT_WITHOUT_FIGURE) + _A_CHILD

# A grown-up asking what a baby's food is like is not weaning one: "is baby food healthy for
# adults" and "can adults have baby rice" were answered "start at around six months with soft
# food in sticks". The word adult is the whole of that, and it is the only thing the food's own
# name cannot tell us - "can i reheat baby food" is a parent, and "can i eat baby rice" is caught
# by the speaker-eats check the gate already does.
_FOR_A_GROWN_UP = ("adult", "adults", "grown up", "grown ups", "grownup", "grownups",
                   "for a grown up", "for adults", "is it ok for me", "safe for me")

# A food can carry "baby" in its name, and then the word is the product and not the person:
# "can i eat baby rice" is somebody asking about the packet in the cupboard. The name is taken
# out only to test whether the line names a baby anywhere else - a line that does not, and whose
# speaker is eating, is the speaker's own lunch. "baby yogurt" is deliberately not here: "can i
# give my baby yogurt" is a parent.
_NOT_A_BABY_NAME = ("baby rice", "baby porridge", "baby cereal", "baby food", "baby foods",
                    "baby jar", "baby jars", "baby pouch", "baby pouches", "baby porridge pot")


def _names_no_baby(text):
    """The line with the foods that call themselves baby taken out."""
    low = " %s " % text
    for name in _NOT_A_BABY_NAME:
        low = low.replace(" %s " % name, " thing ")
    return low


# A rate is not an age. "month" and "months" are in AGE so that "how many months" is read as a
# baby question, and a sum of money going aside every month then named a baby too: "i got a bit of
# a bonus so i can do 250 a month now" was answered "Do not blend it back: the window for lumps is
# about seven to nine months".
_A_RATE_IN_MONTHS = re.compile(r"\b(?:a|per|each|every|the)\s+month\b", re.I)


def _a_baby_is_named(understood):
    """True when the line itself says whose food this is: a baby, an age, a little one, a child."""
    low = " " + _text(understood) + " "
    if _AGE_FIGURE.search(low):
        return True
    hit = [word for word in _NAMES_A_BABY if (" " + word + " ") in low]
    if hit and all(word in ("month", "months") for word in hit) and _A_RATE_IN_MONTHS.search(low):
        return False  # "250 a month" is a rate, and the pot is not a child
    return bool(hit)


# A pronoun line read back through the chat is this table's while the child the chat named is
# young enough to be at the table's stage: three years, which is past the age rows on purpose.
_A_BABY_TILL = 36


# The pronouns that can only mean a person. "they" and "them" are left out on purpose: "my
# bananas go brown before i can eat them" is a pronoun, and it is not a baby.
_A_CHILD_PRONOUN = ("he", "she", "him", "her", "his", "hers")

# A body that has something wrong with it is not a food. The row's names are the foods themselves
# ("liver", "kidney"), so "my baby has kidney problems" scored as a food question and was answered
# with how often a baby may eat liver - about a different organ, and no answer to what was asked.
# The condition word is anchored to the organ the row is named for: "my baby has kidney problems"
# is a body to be looked after, while "my toddler has had a scan, is cheese ok" is a food question
# about a child who happened to be examined. A scan, a stone or an operation on the whole line would
# stand the table down for lines that are asking what to cook.
_A_ORGAN = r"(?:liver|kidneys?|hearts?)"
_A_CONDITION = re.compile(
    r"\b(" + _A_ORGAN + r")\b(?:\W+\w+){0,2}?\W+"
    r"(?:problems?|conditions?|disease|failure|infections?|damage|stones?|transplants?|"
    r"surgery|operation|disorder|dialysis|reflux)\b", re.I)


def _a_condition_of_this_food(names, understood):
    """Is the line's condition about this row's food, and is that the whole question?

    A condition is not a food, but only the row whose food is the organ has to stand down.
    `my baby has kidney problems` scores on this table's kidney row, and that row is the offal
    card, so it has to go; `my toddler has a heart condition, is cheese ok` scores on the cheese
    row and the person is asking about cheese, so the cheese card is the answer.

    The line also has to name no other food of the row: the offal card is keyed on pate as well as
    liver, and `my daughter had a liver transplant, can she have pate` is a question about pate -
    the transplant is the reason the question is being asked, not a different question.
    """
    text = _text(understood)
    match = _A_CONDITION.search(text)
    if match is None:
        return False
    organ = match.group(1).lower()
    if organ.endswith("s"):
        organ = organ[:-1]
    low = " " + text.lower() + " "
    if not any(organ in str(name).lower() for name in names):
        return False
    # What is left of the line once the condition is taken out: a food named there is the
    # question. `my baby has liver disease, is liver ok` names the liver twice - once as the
    # body with something wrong with it, once as the thing on the plate - and the second one is
    # the ask. A second condition is not a food either, so it stands the row down as well.
    rest = _text({"clean": text[:match.start()] + " " + text[match.end():]})
    if _A_CONDITION.search(rest):
        return False
    for name in names:
        word = str(name).lower()
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", rest.lower()):
            return False
    return True


# The adults a line says "she" or "her" about, and the words for the ones whose unsteadiness,
# refusing food or a lump is theirs and not a baby's. A pronoun is the only way half these lines
# name the baby, so it cannot be dropped, but "my mum is 78 and a bit unsteady on her feet" was
# answered "Do not blend it back: the window for lumps is about seven to nine months" - the "bits"
# and the "her" together read as a weaning line. An adult named in the line is the pronoun's
# subject, and this table's answers are not about them.
_AN_ADULT = ("mum", "mummy", "mom", "mommy", "mother", "dad", "daddy", "father", "nan", "nana",
             "gran", "granny", "grandma", "grandmother", "grandad", "granddad", "grandpa",
             "grandfather", "husband", "wife", "partner", "boyfriend", "girlfriend", "aunt",
             "auntie", "uncle", "carer", "neighbour", "neighbor", "friend", "mam", "sister",
             "brother", "boss", "colleague")

# ... but only when the line is about the person. A grown-up can have an opinion about a baby's
# food and the person is still asking about the food: "my mum thinks she should have lumps by
# now", "my husband says she should try lumps", "my nan says give her a bit of porridge". An
# adult's name alone stood those cards down, and "my mum thinks she should have lumps by now" was
# answered with a card about a lump in the neck. The words that make a line this table's are its
# own: the texture words, and the foods `FOODS` below already answers. "eat" and "food" are
# deliberately not here - a grown-up who cannot eat is a line about the grown-up.
_A_TABLE_WORD = ("lump", "lumps", "lumpy", "wean", "weans", "weaning", "weaned", "puree",
                 "purees", "mash", "mashes", "mashed", "spoon", "spoons", "spoonful", "bottle",
                 "bottles", "sippy", "finger food", "solids", "texture", "textures")

# The foods are read from the table rather than written out again beside it, so the two cannot
# drift apart.
_A_TABLE_FOOD = frozenset(name for food in FOODS for name in food["names"])


def _a_table_word_is_named(understood):
    low = " " + _text(understood) + " "
    if any((" " + word + " ") in low for word in _A_TABLE_WORD):
        return True
    return any((" " + name + " ") in low for name in _A_TABLE_FOOD)


def _a_pronoun_is_in_the_line(understood):
    low = " " + _text(understood) + " "
    if not any((" " + word + " ") in low for word in _A_CHILD_PRONOUN):
        return False
    if _a_table_word_is_named(understood):
        return True
    return not any((" " + word + " ") in low for word in _AN_ADULT)


def _a_baby_or_a_pronoun(understood):
    """The feeding rows' guard: the line has to be about a young child, not an adult.

    A pronoun is the child only when the line names nobody grown-up. "what can i give him for
    lunch" is a baby the chat has already named; "my nan is diabetic, what can i take to her for
    tea" is a nan, and the first-foods paragraph answered it because the key takes a pronoun and
    an eating verb and asks nothing else.

    Stricter than `_a_pronoun_is_in_the_line` on purpose, and only the feeding rows use it: the
    rows that answer a texture ("my mum thinks she should have lumps by now") or a food by name
    ("my nan says give her a bit of porridge") read the adult's name as an opinion about the
    baby's meal, which is right for them and wrong for this table's oldest question.
    """
    if _a_baby_is_named(understood):
        return True
    low = " " + _text(understood) + " "
    if not any((" " + word + " ") in low for word in _A_CHILD_PRONOUN):
        return False
    return not any((" " + word + " ") in low for word in _AN_ADULT)


# The row below answers a *baby's* first food, and it has never asked how old the child is:
# "my kid is 4 years old, what should i feed him" was told to start with soft food in sticks.
# An age of a year or more is not weaning, so the feeding rows stand down on one.
_OLDER_CHILD_WORD = ("kid", "kids", "child", "children", "son", "daughter", "boy", "girl",
                     "teenager", "teenagers", "teen", "lad", "lass")
_A_BARE_YEAR_FIGURE = re.compile(
    r"\b(?:is|are|aged|at)\s+(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\d{1,2})\b"
    r"(?!\s*(?:month|months|week|weeks|wk|wks|mth|mths|day|days))")


def _an_age_of_a_year_or_more(understood):
    """True when the line gives the child an age of a year or more.

    One reader for every shape people write an age in, so the guard and the stage table cannot
    disagree about the same line: a figure with a unit ("18 months", "4 years"), a spelled age
    with "old" ("my two year old"), and a bare figure beside a word for an older child ("my kid
    4", "my daughter 6"), because nobody says "my kid 4" of a baby of four months. Beside "baby"
    a bare figure is months, and `_age_in_months` leaves it unread, exactly as before.
    """
    age = _age_in_months(understood)
    return age is not None and age >= 12


def _of_weaning_age(understood):
    """The feeding rows' other guard: a first food is for a child young enough to need one."""
    return not _an_age_of_a_year_or_more(understood)


# "Can I eat this" is about the speaker's own lunch; "how much milk should i give" is about the
# baby's, and the verb is what tells them apart. A pronoun and an eating verb within a word or
# two of each other is the person eating; give, feed and offer are somebody else eating.
_SELF_PRONOUN = ("i", "i'm", "im", "me", "we", "we're", "you", "you're", "my", "our")
_OWN_EATING = ("eat", "eats", "eating", "ate", "have", "has", "having", "had", "drink", "drinks",
               "drinking", "drank", "cook", "cooks", "cooking", "make", "makes", "making",
               "try", "tries", "trying", "buy", "buying")
_FOR_ME = ("bad for you", "good for you", "healthy for you", "unhealthy for you",
           "for me", "my lunch", "my dinner", "my breakfast", "my tea", "on my plate")

# The things people only do for a baby. "how do i drop a milk feed", "how do i stop
# breastfeeding" and "when do i introduce water" name no baby at all, and they are the baby
# questions the table was built for, so the act itself is a way of naming the person fed.
_BABY_ACT = ("breastfeed", "breastfeeds", "breastfeeding", "breast feed", "breast feeding",
             "formula", "wean", "weans", "weaning", "weaned", "milk feed", "milk feeds",
             "drop a feed", "drop a milk feed", "a cup", "open cup", "sippy", "solids",
             "dummy", "teat", "sterilise", "sterilising", "puree", "baby rice", "first foods",
             "finger food", "finger foods", "introduce water", "introduce a cup",
             "introducing water", "introduce solids", "introduce allergens", "first tastes",
             "the first taste",
             # A dish made soft for somebody who cannot chew is the baby's: "can i put butter in
             # mash" has no baby word in it at all and no "for me" either, and the butter row is
             # the one that answers what may go into it. Everything still has to score, so a
             # recipe line of the speaker's own ("can i put butter in mashed potato for my
             # dinner", "how do i mash potatoes") keeps the cooking table.
             "mash", "mashed", "mashing", "mashed up", "squash it", "fork mash")

# The shop-bought answer is about jars, pouches and purees, and nobody writes "my baby" in
# "are jars as good as homemade": the row's own words have to count as naming the feeder. So a
# phrase that only a question about feeding a baby is made of joins the gate. They are pairs on
# purpose - "jar" alone is jam and chutney ("how long does homemade jam keep in jars"), and the
# bath, the bottle steriliser and the freezer bags keep the answers they have.
# A first taste of a food is a feeding line even with nobody named: "how do i introduce eggs",
# "how do i introduce cow's milk", "when do i first give fish". The verb "introduce" is a verb
# about people as often as about food, so a food from this table's own list has to be in the line,
# and a line about the speaker's own diet keeps out of it.
_INTRODUCES_A_FOOD = re.compile(
    r"\b(?:introduc(?:e|ing|ed)|first\s+(?:taste|try|time\s+giving)|start(?:ing)?\s+giving)\b")
_NOT_MY_DIET = ("diet", "into my", "to my diet", "for me", "myself", "my own")


_A_FEEDING_PHRASE = ("jars or pouches", "jars and pouches", "jars as good", "pouches as good",
                     "jars or homemade", "pouches or homemade", "own purees", "purees or",
                     "puree or jars", "buy jars", "shop bought", "shop-bought",
                     "ready made pots", "ready-made pots", "rusk", "rusks",
                     "how much milk should i give",
                     # A pouch of food and a jar of food are what a baby eats from, and these
                     # lines never say "baby": "are pouches any good", "how do i warm a pouch",
                     # "can i buy pouches". The row that answers them scores on the same words,
                     # and the jam, the chutney, the freezer and the steriliser keep their own
                     # answers because their rows score higher.
                     "jar", "jars", "pouch", "pouches", "puree", "purees", "pureed")
# Water is the one a person asks about without the baby in the line at all, and the water row is
# the answer: "when can i give water", "when can i give them water", "when can i start giving
# water" were the search hedge once the gate went in. The verb is what carries them, so it is a
# phrase of its own rather than another food word - "give water" is what a gardener and an animal
# do as well, and both of those had their own answer before ("should i give water to my dog",
# "how often should i give water to a cactus"). A plant or an animal in the line is that answer's,
# so this phrase does not open the table for it.
_GIVING_WATER = ("give water", "giving water", "give them water", "give him water",
                 "give her water", "start giving water")
# ...and it is a question when it opens this table: "give water" on its own is the start of a
# sentence about a plant, a dog or a person, and it stays the hedge it was.
_GIVING_WATER_ASKS = frozenset("when can should how howmuch age what".split())
# The phrase above is the only one that names no food at all: "give water" is what a gardener and
# an animal do too, and both of those had their own answer before ("should i give water to my
# dog", "how often should i give water to a cactus"). A plant or an animal in the line is that
# answer's, so the phrase does not open this table for it.
_GIVING_WATER_OUT = frozenset("""plant plants cactus cacti garden gardens flower flowers tree trees
    grass lawn shrub shrubs seedling seedlings houseplant houseplants dog dogs puppy puppies cat
    cats kitten kittens pet pets vet hamster rabbit bird birds fish pond""".split())


# A feeding word about the mother herself, and a question about what she eats: "is it ok to eat
# soft cheese while breastfeeding" is her plate, and the cheese row's keeping answer ("hard cheese
# keeps two weeks once opened") is about the fridge, not about her diet.
_WHILE_SHE_FEEDS = re.compile(
    r"\bwhile (?:breastfeeding|breast feeding|nursing|lactating|chestfeeding)\b"
    r"|\bwhen (?:breastfeeding|breast feeding|nursing|lactating)\b"
    r"|\bbreastfeeding (?:can|should|could|may|is|and)\b", re.I)
_HER_OWN_EATING = re.compile(
    r"\b(?:can|should|could|may|do) i (?:eat|drink|have|avoid|skip|cut out)\b"
    r"|\bis it (?:ok|okay|safe|fine) to (?:eat|drink|have)\b"
    r"|\banything i (?:cant|can't|shouldnt|shouldn't) (?:eat|drink|have)\b"
    r"|\bwhat can i (?:eat|drink|have)\b", re.I)


def _says_the_speaker_is_eating(words, said):
    """Whether the line is somebody asking about their own food rather than a baby's."""
    if any(phrase in said for phrase in _FOR_ME):
        return True
    for index, word in enumerate(words):
        if word in _SELF_PRONOUN:
            # "can my son eat grapes" is the child eating: the pronoun belongs to the child, and
            # the eating verb after it is theirs.
            if index + 1 < len(words) and words[index + 1] in _A_CHILD + BABY:
                continue
            if any(later in _OWN_EATING for later in words[index + 1:index + 4]):
                return True
    return False


def _the_line_feeds_somebody(understood, memory):
    """Whether this line is about feeding a baby, the ages they are, or the child just named.

    A food and a word of asking are not a baby. "how many calories in a slice of white bread",
    "how much sugar is in a can of coke", "is full fat milk bad for you", "can i eat peanut
    butter every day" and "i have a nut allergy can i eat at a curry house" all named a food and
    asked about it, and this table answered every one of them with the baby version - the last
    to somebody who had just said they were allergic to nuts. So the person being fed is
    required, and there are only three ways to give them:

    - the line names a baby or an age: "can my baby have cheese", "what can a 7 month old eat";
    - the line says "she" or "him", and the chat has a baby in it a turn or two back:
      "can she have peanut butter every day" after "my baby is 7 months old";
    - the line names nobody at all - "what about cheese", "how much milk should i give" - and the
      chat has a baby in it. A line that says "i" or "my" with no baby word in it is the
      person's own lunch, whatever the chat was about.
    """
    word_list = [str(word).lower() for word in (understood.get("words") or ())]
    words = set(word_list)
    said = _text(understood)
    padded = " %s " % said
    # The chat can be about the dog when the food question arrives: "my dog has been sick" then
    # "what should i feed him tomorrow". The topic is the animal's, no baby is named and no age
    # is given, so the food table stands down and the pet card answers if it has one.
    if (understood.get("topic") == "pets" or understood.get("topic_own") == "pets"):
        if not _a_baby_is_named(understood) and _age_in_months(understood) is None:
            return False
    # "can adults have baby rice" is a grown-up asking about a baby's food, and the word adult is
    # the whole answer: the table is about feeding a baby, not about what a baby's food is like.
    if any(cue in padded for cue in _FOR_A_GROWN_UP):
        return False
    stripped = _names_no_baby(said)
    names_a_baby = (any((" %s " % word) in stripped for word in _NAMES_A_BABY)
                    or bool(_AGE_FIGURE.search(stripped)))
    # "should i make my own purees or buy jars" reads as the speaker cooking, and the phrase is
    # what says it is not: a feeding phrase outranks the cooking reading.
    feeds = any(phrase in padded for phrase in _A_FEEDING_PHRASE)
    if not feeds and len(word_list) >= 3 and words & _GIVING_WATER_ASKS:
        if any(phrase in padded for phrase in _GIVING_WATER):
            feeds = not any((" %s " % word) in padded for word in _GIVING_WATER_OUT)
    # "how do i introduce eggs" is the allergen ladder's question, and it names no baby: the verb
    # for a first taste plus a food is what says a child is being fed. It is not a line about the
    # speaker's own diet.
    # A bottle and formula are feeds but not allergens, and "how do i introduce a bottle" is the
    # bottle-feeding question, not this ladder's.
    if not feeds and _INTRODUCES_A_FOOD.search(padded) and not any(
            cue in padded for cue in _NOT_MY_DIET) and any(
            (" " + word + " ") in padded for word in _ALLERGEN_FOOD - {"bottle", "formula"}):
        feeds = True
    if not names_a_baby and not feeds and _says_the_speaker_is_eating(word_list, said):
        return False
    if (not names_a_baby and _WHILE_SHE_FEEDS.search(said)
            and _HER_OWN_EATING.search(said)):
        # The mother is the one being fed and the one eating: nobody else is named, so the table
        # of what a baby eats is not this line's answer.
        return False
    if _a_baby_is_named(understood):
        return True
    if _age_in_months(understood) is not None:
        return True
    if feeds:
        return True
    # "he" and "she" are the child, and "they" is a baby whose sex the person has not said. "them"
    # is not, because it is the beans on the counter and the jars in the cupboard ("i have butter
    # beans what can i do with them" reached the fat row on "them" alone). A pronoun that points
    # at the dog or the cat is not a child, whichever food word is beside it.
    if words & {"he", "she", "him", "her", "his", "hers", "they"}:
        return not _the_pronoun_is_an_animal(understood)
    if _says_the_speaker_is_eating(word_list, said):
        return False
    if any(" %s " % act in padded for act in _BABY_ACT):
        return True
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list):
        return False
    said_now = said.strip().lower()
    for turn in reversed(turns):
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("user") or "").strip().lower()
        if not text or text == said_now:
            continue
        earlier = " %s " % text
        if _AGE_FIGURE.search(earlier):
            return True
        if any(" %s " % word in earlier for word in _NAMES_A_BABY):
            return True
    return False


_ALLERGEN_ROW = (
    "Give the common allergens early and often rather than late: from six months, one at a "
    "time, on a day they are well and in the morning - peanut, egg, milk, wheat, fish, "
    "shellfish, sesame and soya. Once a food is in, keep giving it a couple of times a "
    "week, because stopping is what raises the risk. With severe eczema or a reaction "
    "already, ask a GP before starting.")

# The food side of the row. "introduce" is a verb about people as often as about food, and the
# two key halves are satisfied by a baby and nothing to eat: "how do i introduce a new baby to a
# toddler" was told to give the common allergens early and often, where the answer people want is
# the introducing-two-people card (tests/test_introducing_a_partner_is_not_a_baby.py on main).
# So a line that names an allergen or any food keeps the row, and one that only puts two people in
# a room together stands it down.
_ALLERGEN_FOOD = frozenset((
    "allergen", "allergens", "allergy", "allergies", "peanut", "peanuts", "peanut butter",
    "egg", "eggs", "milk", "cows milk", "wheat", "fish", "shellfish", "sesame", "soya", "soy",
    "nuts", "nut butter", "dairy", "cheese", "yoghurt", "yogurt", "strawberry",
    "strawberries", "kiwi", "tomato", "food", "foods", "finger food", "finger foods", "solids",
    "weaning", "wean", "puree", "purees", "reaction", "rash", "hives", "eczema", "reflux",
    # not "bottle": "how do i introduce a bottle to a breastfed baby" is a feeding question with
    # no food in it, and it was told to give the common allergens early and often
    "formula", "meal", "meals", "breakfast", "lunch", "dinner", "spoon", "lumps"))
# Introducing one person to another: the verb, then "to" and an article or a possessive. A line
# like "when do i introduce it" has neither, so it keeps the food row.
_INTRODUCING_PEOPLE = re.compile(
    r"\bintroduc(?:e|ing|ed)\b.*?\bto (?:a|an|the|my|our|her|his|their|each)\b")


def _the_allergen_row(memory, understood):
    """The allergen answer, unless the line is introducing two people to each other."""
    text = " " + _text(understood) + " "
    if _INTRODUCING_PEOPLE.search(text) and not any(
            (" " + word + " ") in text for word in _ALLERGEN_FOOD):
        return ""
    return _ALLERGEN_ROW
# A pronoun is not a baby. "my mum is coming on sunday" then "shes 72" then "she cant eat much
# salt" was answered with the no-salt-before-one rule: "she" was in the line and the chat gave the
# age as a bare number, which is not a figure this table can read, so the pronoun alone was taken
# as the evidence. These are the grown-ups a chat names, and one of them behind the pronoun means
# the line is not about a baby.
_GROWN_UP = ("mum", "mums", "mom", "moms", "mother", "mam", "dad", "dads", "father", "stepdad",
             "stepmum", "stepmom", "gran", "grans", "granny", "grandma", "grandad", "grandpa",
             "nana", "nan", "pop", "husband", "wife", "partner", "boyfriend", "girlfriend",
             "brother", "brothers", "sister", "sisters", "friend", "friends", "neighbour",
             "neighbor", "colleague", "boss", "aunt", "auntie", "uncle", "cousin", "housemate",
             "flatmate", "roommate", "carer", "client", "customer", "patient", "man", "woman",
             "lady", "gentleman", "fella", "guy", "bloke", "she", "he", "her", "him")


# The animals a chat can be about. "he" after "my dog has been sick" is the dog, and the food
# table's rules for a child under three are not the answer to what to feed him: "what should i
# feed him tomorrow" reached the first-foods paragraph and the six-month weaning age.
_ANIMAL = ("dog", "dogs", "puppy", "puppies", "pup", "pups", "cat", "cats", "kitten",
           "kittens", "rabbit", "rabbits", "hamster", "hamsters", "guinea", "pig", "pigs",
           "parrot", "bird", "birds", "horse", "horses", "pet", "pets", "vet")


def _the_pronoun_is_an_animal(understood):
    """True when the "he" or "she" of the line points at an animal the chat named."""
    places = []
    ref = understood.get("ref")
    if isinstance(ref, dict):
        places.extend(value for key, value in ref.items()
                      if key in ("he", "she", "they", "him", "her") and isinstance(value, str))
    leans = understood.get("leans_on")
    if isinstance(leans, dict):
        places.extend(str(leans.get(key) or "") for key in ("subject", "text"))
    for place in places:
        words = [word for word in re.split(r"[^a-z']+", place.lower()) if word]
        if any(word in _ANIMAL for word in words):
            return True
    return False


def _the_pronoun_is_a_grown_up(understood):
    """True when the "she" or "he" of the line points at a grown-up the chat named.

    "my mum" behind the pronoun is a person, and a person with no age this table can read is not
    a baby: the food rules here are for a child under three. A referent that carries a baby word
    ("my baby", "my little one", "my son" while the chat gives him months) is not this.
    """
    ref = understood.get("ref")
    if not isinstance(ref, dict):
        return False
    for key in ("he", "she", "they", "him", "her"):
        place = ref.get(key)
        if not isinstance(place, str) or not place.strip():
            continue
        words = [word for word in re.split(r"[^a-z']+", place.lower()) if word]
        if any(word in _BABY or word in _A_CHILD_PRONOUN or word in ("one", "baby", "child")
               for word in words):
            continue
        if any(word in _GROWN_UP for word in words):
            return True
    return False


def _verdict(names, reply, extra=(), bias=0, own_ask=None, pronoun=False):
    """One verdict row: the food by name, the baby, and the word that asks for a verdict.

    The asking words are in the key and the baby is in `ask`. Score counts two of a key's parts
    and the subject has to be said, so food plus asking word is already two: with the asking
    words in `ask` instead, "can i eat bananas" and "should i give up sugar" reached rows about
    babies. The baby is the part that makes the row this table's, so it is the part that is
    required, and the asking words stay in the key where they rank the row against the others.

    The baby is often not in the line at all: "my little one is 9 months old" then "can he have
    strawberries", or "my baby has reflux" then "is it ok to give water". So the asking words are
    the reach (`ask=_VERDICT_ASK`) and this reply is what decides, by reading the line and the
    chat behind it: a baby, an age or a child in the line; an age the chat is about, read with the
    reader the age rows use (`_age_in_the_chat`); a person pronoun in the line the follow-up
    reader rewrote ("and egg" -> "can i give her egg"); or a baby word in the line it leans on.
    An empty reply is how an entry says "not mine", so the answer the line had before the table
    gets the turn.
    """
    def answer(memory, understood):
        if _a_condition_of_this_food(names, understood):
            # "my baby has kidney problems" is a body to be looked after, not a food to be judged:
            # the food name in the line is the organ, and the row would answer about the menu. It
            # is the organ's own row that stands down, and only when nothing else is being asked
            # about: "kidney stones, can he have cheese" is still the cheese question.
            return ""
        if own_ask is not None and own_ask(understood):
            # A row can bring its own evidence for whose question this is, for the lines where
            # no child is named because the food itself is the whole question.
            return reply
        if _a_baby_is_named(understood):
            return reply
        if _a_pronoun_is_in_the_line(understood):
            # The follow-up reader rewrites the line with the subject it leans on in front of it
            # ("and egg" -> "can i give her egg"), so a pronoun here is the baby of this chat.
            age = _age_in_the_chat(memory, understood)
            if age is not None:
                return reply if age <= _A_BABY_TILL else ""
            # No age the chat can give, so the pronoun is the only evidence there is - and it is
            # evidence against this table when it points at a grown-up with nothing of this
            # table's own in the line.
            if _the_pronoun_is_a_grown_up(understood) and not _a_table_word_is_named(understood):
                return ""
            return reply
        age = _age_in_the_chat(memory, understood)
        # A child of school age is not this table's: "my son is 12 years old" then "can he have
        # tuna" is a grown-up's portion question, and "from six months" would be a strange answer
        # to it. The age rows stop at two, so the pronoun read stops a little later than that.
        if age is not None and age <= _A_BABY_TILL:
            return reply
        # The chat can name a baby and give no age at all: "my baby has reflux" then "is it ok to
        # give water", "we are starting weaning" then "can i give her banana". A baby word is not
        # a child word - "my son" may be twelve, which the age above catches - so only this
        # table's own words count here.
        leans = understood.get("leans_on")
        if isinstance(leans, dict) and isinstance(leans.get("words"), list):
            before = " " + " ".join(w for w in leans["words"] if isinstance(w, str)) + " "
            if any((" " + word + " ") in before for word in _BABY + _A_CHILD_PRONOUN):
                return reply
        return ""

    # A row can key the pronoun too, for a food that is a whole line on its own ("can i give
    # him toast"): the baby is in the chat, not in the line.
    child = BABY + _A_CHILD_PRONOUN if pronoun else BABY
    return entry("babyfood-" + re.sub(r"[^a-z0-9]+", "-", names[0]),
                 (names, child, _VERDICT_ASK), answer, ask=_VERDICT_ASK, bias=bias,
                 avoid=STAND_DOWN + extra)


# "Season" is two words in one spelling: the spice you cook with, and the run of episodes or a
# league. The spice row below keys on "seasoning", and the loose form of that word is the same as
# "season"; with "start" among its asking words, "season 2 starts tonight" scored as a baby's
# first spices and was answered "yes, and earlier is better than later". A season of a show, a
# team or a gym is not a menu, so that row stands down for it unless the line is about a child.
_SEASON_OF_A_SHOW = re.compile(
    r"\b(?:season\s*(?:\d+|one|two|three|four|five|six)|this season|next season|last season"
    r"|new season|the season|final season|first season|episodes?|series|box set|binge"
    r"|football|cricket|rugby|premier league|the league|league|fixtures?|match|matches"
    r"|team|teams|gym|the show|on tv|netflix)\b")


def _not_a_season_of_a_show(understood):
    """True unless "season" here is episodes or a league: then the spice row is not the answer."""
    low = " " + _text(understood) + " "
    if any((" " + word + " ") in low for word in _BABY + _A_CHILD):
        return True
    return not _SEASON_OF_A_SHOW.search(low)


# The spice row's key arm is BABY plus the asking words, and "seasoning", "pepper" and "ginger"
# are the words half the kitchen lines are made of: "what spices go in a curry" and "should i
# season the pan before cooking" scored as a baby's first spices and were answered "yes, and
# earlier is better than later". Nothing in those lines is a child, so the row stands down
# unless the line says whose food it is - a baby, a child, an age, or the pronoun a follow-up
# reader has put in front of it ("and cinnamon" -> "can i give her cinnamon").
def _a_child_is_in_the_line(understood):
    """True when the line names the child whose food this is, so the spice row may answer.

    A pronoun counts, because the follow-up reader puts one in front of a lean ("and cinnamon" ->
    "can i give her cinnamon"), but only while nothing in the line is a season of a show or a
    league: "he only started this season" has a pronoun and is about a footballer.
    """
    low = " " + _text(understood) + " "
    if any((" " + word + " ") in low for word in BABY + _A_CHILD) or _AGE_FIGURE.search(low):
        return True
    if _SEASON_OF_A_SHOW.search(low):
        return False
    return any((" " + word + " ") in low for word in _A_CHILD_PRONOUN)


# The words the wake-to-feed row is built from, named once so the shared stand-down can be read
# against them: "sleep", "sleeping" and "how often" are in NOT_A_MENU and in this row's own key,
# and a key word in a row's avoid zeroes the row. That is how "how often should i wake my baby to
# feed" and "how do i wake a sleepy baby for a feed" were answered by the funeral-tea buffet.
# The wake has to be the parent's own act: a bare "wake" is a loose form of "wakes" too, so the
# key holds only phrases where somebody is doing the waking ("should i wake", "wake my baby"), and
# "my baby wakes every hour" stays with the night-waking card that already answers it.
_WAKE_TO_FEED_KEY = (
    ("should i wake", "shall i wake", "do i need to wake", "do i have to wake", "can i wake",
     "could i wake", "how do i wake", "how often should i wake", "how long should i let",
     "wake my baby", "wake my newborn", "wake the baby", "wake a baby",
     # not "wake for a feed" on its own: that is also how a parent says "my 9 month old still
     # wakes for a feed", which the night-waking card already answers. The row is the parent
     # deciding to do the waking, so every phrase above names the waker or the asking.
     "wake up for a feed", "wake a sleepy baby", "wake a sleepy newborn", "wake a sleepy",
     "sleepy for a feed", "too sleepy to feed"),
    BABY + ("feed", "feeds", "feeding", "night", "nights", "sleep", "sleeping",
            "slept", "through the night", "should i", "do i need to", "how often",
            "how long"))
_WAKE_TO_FEED_WORDS = frozenset(
    word for part in _WAKE_TO_FEED_KEY for word in part)
ENTRIES = [
    # What a baby eats at the age the line names, and how much of it. The age is read when the
    # reply is built, so one row answers "what can my 7 month old eat", "how many meals a day
    # should a 9 month old have" and "my baby is 1 what can they eat now" without three keys.
    # The bias is what settles "my baby is 1 what can they eat now": the age is in the line, so
    # the stage that age lands on answers it, and the ageless first-foods row below does not.
    # `ask=AGE` is what makes the age a requirement rather than a bonus: with three parts a
    # line can reach the score on the asking and the eating alone, and that is how "what should
    # i put in a packed lunch for a 7 year old" and "my 3 year old throws his food on the floor
    # every meal what do i do" were answered from a table about babies.
    # What is in the cup is a drink question, not a food one: "how much should my toddler
    # drink" was the litre-a-day card until this row took it, and the food stage is the wrong
    # answer to it.
    entry("babyfood-by-age", (_WHAT_TO_FEED, AGE, EATING), _by_age, ask=AGE, bias=1,
          # The key names no person at all - a "what can i give" and an eating verb are enough -
          # so the line has to say whose food it is: an age, a baby, or a pronoun with no adult
          # named. Without this, "my nan is diabetic, what can i take to her for tea" was the
          # first-foods paragraph, and the nan was a baby of about six months.
          # The age guard is NOT on this row. The stage table answers every age from twelve
          # months up with the family-food reply, so standing the row down on a year or more
          # took the one-year-old's answer away: "what can i give my 1 year old for lunch" went
          # from "From one they can eat what the rest of the family eats" to a gift-for-a-child
          # card. `_of_weaning_age` stays on the first-foods row below, which is the one that
          # hands a four-year-old soft sticks of carrot.
          guard=_a_baby_or_a_pronoun,
          avoid=STAND_DOWN + ("drink", "drinks", "drinking", "drank", "thirsty", "fluids",
                              "hydrate", "hydrated")),
    # Eating what the family eats is the question for a child of one and up, and it was answered
    # by the card about moving to a new city: "can my baby eat what we eat" reached "city-next"
    # on the word "we".
    entry("babyfood-family-food",
          (_BABY + ("child", "children", "kid", "kids", "toddler", "toddlers", "1 year old",
                    "one year old"),
           ("what we eat", "what you eat", "our food", "our dinner", "our meals", "family food",
            "family meal", "family meals", "the same as us", "same as us", "adult food",
            "grown up food", "eat what we eat", "eat what i eat", "eat the same")),
          "From about a year they can have what the rest of the family eats, with two changes: "
          "take their portion out before the salt goes in, and cut it small - no whole grapes, "
          "whole nuts or popcorn before about four. Before one the food is practice, and milk is "
          "still the meal, so the family dinner is offered alongside it rather than instead of it.",
          bias=1, avoid=NOT_A_MENU + NOT_A_BABY),
    # What finger food to give, which the weaning stand-down otherwise leaves unanswered: the
    # family row answers "when can a baby have finger foods", and this one answers "which".
    entry("babyfood-finger-foods",
          (("finger food", "finger foods", "fingerfoods", "finger foods for"),
           ("what", "which", "ideas", "list", "good", "best", "options", "suggest", "suggestions")),
          "Sticks and strips they can pick up and hold: cooked carrot, broccoli or green beans, "
          "toast fingers with a thin smear of peanut butter, ripe pear or banana, soft cheese, "
          "scrambled egg, well-cooked chicken or pasta shapes. Cut grapes and cherry tomatoes "
          "lengthways into quarters, cook hard vegetables until they squash between your fingers, "
          "and always have them sitting down while they eat.",
          bias=1, avoid=NOT_A_MENU + NOT_A_BABY + ("when", "how old", "age", "choking", "gagging")),
    # "when do i give my baby a spoon" was the birth-registration card, because "give my baby"
    # is how a form is asked for. The spoon is a weaning question.
    entry("babyfood-a-spoon",
          (("spoon", "spoons", "loaded spoon", "cutlery", "fork", "forks",
            "her own spoon", "his own spoon",
            "feed herself", "feed himself", "feed themselves", "feeding herself",
            "feeding himself"),
           BABY + ("give", "gives", "giving", "hold", "holds", "use", "using", "when", "start",
                   "started", "first", "should", "eat", "eating")),
          "From the very first meals, at six months: put a loaded spoon in their hand and let "
          "them get it to their mouth, however badly, while you load another. They will grip it "
          "in a fist at first and get more on the floor than in, and that is the learning, not a "
          "failure. Until they have the pincer grip, around eight or nine months, the spoon works "
          "best with thick things - porridge, mash, yoghurt - and finger food does the rest. Let "
          "them decide when the meal is over, and never shovel a spoon in while they are crying, "
          "because that is how a baby learns to dread the highchair. A children's fork with "
          "rounded prongs is fine too from around nine months, and it does the one job a spoon "
          "cannot - stabbing the piece they have decided they want.",
          bias=3, avoid=NOT_A_MENU + NOT_A_BABY
          + ("cutlery set", "wedding", "christening", "gift", "present", "silver", "antique",
             "my dinner", "i eat", "restaurant")),

    # "my baby wont drink from a cup" was the litre-a-day card for a toddler: the stand-down
    # that keeps a menu out of a refusal is also the list that named this question, so the
    # refusal words are left out of the stand-down here.
    entry("babyfood-refusing-a-cup",
          (("wont drink from a cup", "won't drink from a cup", "wont take a cup",
            "won't take a cup", "refuses a cup", "refuses the cup", "refuses a beaker",
            "will not drink from a cup", "wont drink from a beaker", "wont use a cup",
            "hates the cup", "spits out the cup", "not drinking from a cup",
            "refuses to drink", "wont drink", "won't drink", "refuses milk",
            "wont drink milk", "will not drink"),
           BABY + ("cup", "beaker", "drink", "drinks", "drinking", "water", "milk", "wont",
                   "won't", "refuses", "should", "do", "i")),
          "Keep offering it and don't make it a fight: a little water in an open cup at every "
          "meal, your own cup in your hand at the same time, and no bottle as a fallback in "
          "between. Free-flow beakers and straw cups are worth trying, because a valve bottle "
          "teaches a different suck. Milk is still the main drink until a year, so a baby who "
          "takes only a few sips from a cup is not going short - the cup is practice, and most "
          "get there between nine months and a year.",
          bias=5,
          avoid=NOT_A_BABY
          + tuple(word for word in NOT_A_MENU
                  if word not in ("wont drink", "won't drink", "refuses to drink", "refuses",
                                  "refusing", "refused", "refuse"))
          # A bottle is somebody else's row, and a refusal in a bottle is not a cup.
          # A bottle is somebody else's row, and a refused meal is the keep-it-plain card's.
          + ("bottle", "bottles", "teat", "teats", "formula", "breast", "breastfeeding",
             "food", "foods", "eat", "eats", "eating", "solids", "meals")),

    # Formula to a year, and what follows it. "when should my baby stop having formula" was the
    # health visitor hedge, and the follow-on milks are sold for exactly this question.
    entry("babyfood-stopping-formula",
          (("stop formula", "stop having formula", "stop giving formula", "stop the formula",
            "come off formula", "off formula", "switch to cows milk", "move to cows milk",
            "change to cows milk", "when do i stop formula", "follow on milk", "follow-on milk",
            "stage 2 milk", "hungrier baby milk", "growing up milk"),
           BABY + ("formula", "milk", "when", "stop", "stopped", "switch", "change", "give",
                   "giving", "should", "do i")),
          "First infant milk until the first birthday, then whole cows milk in a cup. There is no "
          "need to move to a follow-on or hungry-baby milk: they are the same kind of thing with "
          "a different label, and the labels are marketing rather than a stage. Do not switch to "
          "cows milk as the main drink before twelve months, because it has too little iron. If "
          "you are stopping breastfeeding rather than formula, drop one feed at a time, about a "
          "week apart, and leave the bedtime one until last.",
          bias=3,
          # The shared stand-down names "formula" itself, and this row is the formula question.
          avoid=NOT_A_BABY + tuple(word for word in NOT_A_MENU if word != "formula")),

    # Which formula to buy, and whether to change it, is its own question and it had no card at
    # all: "which formula should i buy" was the search hedge, "should i switch my babys formula"
    # was the refused-bottle card ("have somebody else offer it"), "can i change formula brand"
    # was a shrug, and "how do i switch formula" and "what formula should i use for my baby"
    # were the spreadsheet card, because "formula" is Excel's word too. The brand is a question
    # about the tin, and the making up, the amount and the sterilising all keep their own rows.
    entry("babyfood-which-formula",
          (("formula", "formula milk", "baby formula", "infant formula",
            "first infant milk", "infant milk", "hungry baby milk", "hungry baby",
            "follow on milk", "follow-on milk", "stage 2 milk", "stage 3 milk",
            "growing up milk", "brand of formula", "formula brand", "formula brands"),
           ("which", "what", "best", "better", "switch", "switching", "switched",
            "change", "changing", "changed", "try", "trying", "brand", "brands", "use",
            "using", "buy", "buying", "choose", "choosing", "recommend", "worth", "need",
            "mix", "mixing", "suit", "suits", "baby", "babies", "baby's", "babys",
            "newborn", "infant", "bottle", "bottles", "feed", "feeds", "feeding",
            "milk", "colic", "colicky", "reflux")),
          ("Every first infant milk sold has to meet the same standard, so the brand matters much "
           "less than the price and the tin you can get hold of: pick one first infant milk and "
           "stay with it. Hungry-baby and follow-on milks are the same kind of thing under a "
           "different label, and moving to them is marketing rather than a stage, so there is no "
           "need to change when a baby seems hungrier - offer a little more of the same milk "
           "first, because it is usually volume and not the powder. If you do want a different "
           "brand, change straight over rather than mixing two powders in one bottle, and give it "
           "a few days: a bit of wind, looser nappies or more posseting on a new milk usually "
           "settles, while blood in the nappy, forceful vomiting, a rash or eczema that will not "
           "settle is worth a word with the health visitor about a milk-free trial."),
          # The rest of formula is four other rows: making it up (the kettle and 70C), how much,
          # sterilising, and the move to cows milk. A maths formula is the spreadsheet and
          # school rows' word, and none of those questions is this one.
          avoid=("how much", "how many", "how often", "ml", "oz", "ounces", "scoop",
                 "scoops", "make up", "making up", "made up", "prepare", "preparing",
                 "sterilise", "sterilising", "steriliser", "kettle", "70c", "70 c",
                 "cool it", "left out", "left over", "two hours", "reheat", "warm up",
                 "bottle warmer", "how long", "how do i make", "cows milk", "whole milk",
                 # The temperature of the water, and the making up of the powder, is the
                 # method row's question, not the brand's.
                 "temperature", "how hot", "hot water", "boiling", "boil the kettle", "warm it",
                 "the formula for", "formula for the", "area", "circle", "triangle",
                 "equation", "quadratic", "maths", "math", "algebra", "percentage",
                 "spreadsheet", "sheet", "excel", "cell", "cells", "calculate", "gcse",
                 "homework",
                 # A formula in a column of numbers is the spreadsheet card's line, including
                 # when it arrives as a follow-up to a spreadsheet turn ("What would the formula
                 # look like for a column of numbers?"), which the context search would otherwise
                 # hand to this row.
                 "column", "columns", "row", "rows", "numbers", "number", "sum", "autosum",
                 # Breast or bottle is a different question with its own answer, and it is
                 # about the feeding and not the tin.
                 "breast", "breastfeeding", "breastfeed", "breastfed", "breast milk",
                 "breastmilk", "expressed", "expressing"),
          # "which formula should i buy" is three stopwords and one content word - "which",
          # "should" and "buy" are all dropped before scoring - so the asking has to be in the
          # key as well, or the shortest form of the question gets the search hedge.
          ask=("which", "what", "buy", "buying", "brand", "best", "better", "switch", "change",
               "use", "try", "mix", "mixing", "worth", "recommend", "need", "needs", "does",
               "do", "is", "are", "should", "suit", "suits", "right", "good"),
          # The tin wins over the rows that share one word with it: the refused-bottle card
          # ("have somebody else offer it") and the toddler-drinks card both key "baby" and
          # "milk", and neither is a question about which milk to buy.
          bias=3),

    # "how do i introduce a cup" and "when do i introduce water" reached the advice row about
    # introducing two people, which shares the verb and nothing else, and a shrug.
    entry("babyfood-introducing-a-cup",
          (("introduce water", "introduce a cup", "introduce the cup", "introduce a beaker",
            "introduce a sippy cup", "introduce an open cup", "first cup", "first water",
            "start water", "start a cup", "offer water", "offer a cup", "offer a beaker"),
           ("do i", "i", "we", "should", "when", "how", "baby", "cup", "beaker", "water",
            "drink", "sips")),
          "Water in an open cup, from six months and with meals: a few sips is the whole point, "
          "and an open cup or a free-flow beaker teaches the sip that a valve bottle never does. "
          "Hold the cup with them at first, or use a small one they can get both hands round, and "
          "expect it down the front for a week or two. Milk stays the main drink until a year, so "
          "water is offered rather than pushed, and juice or squash is not needed at all.",
          bias=3, avoid=NOT_A_MENU + NOT_A_BABY
          + ("partner", "boyfriend", "girlfriend", "my son", "my daughter", "new man",
             "new woman", "family", "child to", "to my child", "to my kids")),

    # Fat, spice and seasoning: three everyday questions that got the health visitor hedge,
    # because a condiment is not a food and no verdict row named one.
    entry("babyfood-butter-and-oil",
          # The fat word is the subject and the baby word is not: with BABY in the first arm,
          # every "can my baby have X" line scored on "baby" alone.
          (("butter", "oil", "spread", "margarine", "ghee", "lard", "fats", "fat"),
           BABY + ("have", "has", "eat", "give", "cook", "cooking", "add", "put", "use", "ok",
                   "safe", "can", "should", "in", "on", "for")),
          "Yes, in the amounts you would use yourself: a little unsalted butter or a teaspoon of "
          "rapeseed or olive oil in their mash, on toast, or to cook their vegetables in. Fat is "
          "not the enemy at this age - it carries the vitamins and it is most of what makes a "
          "small stomach feel fed - so do not go for low-fat spreads or skimmed anything before "
          "two. Salt is the thing to watch, and butter is salty, so keep it to a scrape.",
          # The baby is the requirement, not a bonus: the second arm's "on" and "in" are what
          # made "my coat has oil on it" two parts and got weaning advice for a stain.
          bias=3, ask=BABY + ("puree", "purees", "mash", "mashed", "solids", "spoon", "bowl",
                              "baby food", "food", "foods"),
          avoid=NOT_A_MENU + NOT_A_BABY
          # "peanut butter" is the nut row's: the word butter in it used to win the line, and the
          # answer was about frying fat rather than about the allergen.
          + ("frying", "deep fry", "fryer", "chip pan", "oven", "car", "engine", "bike",
             "chain", "central heating", "radiator", "boiler", "hair", "skin", "essential oil",
             "drain", "drains", "sink", "plughole", "toilet", "loo", "pipes", "grease",
             "freeze", "freezer",
             "frozen", "thaw", "shelf life", "use by", "go off", "gone off",
             "peanut butter", "peanut", "peanuts", "nut butter", "almond butter", "nuts")),
    entry("babyfood-spices-and-herbs",
          # The names are the same list that stands the other rows down, so the two cannot drift:
          # `SPICE_NAMES` held turmeric, paprika, nutmeg, saffron, cardamom, coriander, allspice
          # and garam masala, and this arm did not, so "can my baby have turmeric" stood every
          # other row aside for a spice by name and then had none to answer it - the person got
          # the health visitor. "is paprika ok for a baby" and "can i give my baby nutmeg" the
          # same. The words that are not a name (spicy, seasoning, garlic, ginger, curry) stay
          # here, since a dish or a habit is not a spice by name.
          (SPICE_NAMES + ("spice rack", "spicy", "seasoning", "pepper", "chilli", "chili",
                          "garlic", "ginger", "curry", "curries", "mild curry"),
           # The function words are out of this arm on purpose. With them, "can i use turkey
           # mince in chilli" scored as a baby question on "chilli" + "can" + "use" + "in" and
           # got the answer about introducing spices at six months. Every real line of this row
           # names a baby, a toddler or an age, which is what `BABY` is.
           BABY),
          "Yes, and earlier is better than later: mild spices and herbs - cumin, cinnamon, "
          "turmeric, garlic, ginger, parsley, coriander - from six months, in the food you cook "
          "for the family. A baby who meets flavour early is usually the one who eats more widely "
          "at two. What to leave out is the heat and the salt: no chilli heat, no salt, no stock "
          "cubes. Black pepper in cooking is fine; a hot dish is not, because it is painful "
          "rather than dangerous.",
          bias=3, avoid=NOT_A_MENU + NOT_A_BABY
          + ("grow", "growing", "plant", "sow", "garden", "windowsill", "recipe", "bake",
             "spice rack", "where to buy", "grind",
             # A spice in the eye is the eye's question, whatever baby words are in the line:
             # "my baby got chilli in her eye" was told when to introduce spices at six months,
             # and the next turn, "she is screaming", was "I'm listening". The eye injury does
             # not care whose eye it is or how old its owner is.
             "in the eye", "in her eye", "in his eye", "in their eye", "in my eye",
             "eye is", "eyes are", "eye hurts", "eyes hurt", "eyeball", "screaming",
             # The mother eating is not the baby eating: "is spicy food ok when breastfeeding"
             # got "mild spices and herbs from six months", which is a weaning answer to a
             # question about her dinner. nutrition.py's food-while-breastfeeding has it.
             "breastfeeding", "breast feeding", "breast-feeding", "nursing", "lactating",
             "while im feeding", "while breastfeeding"),
          guard=_a_child_is_in_the_line),

    # An eczema baby is the one the allergen advice is written for: the two travel together, so
    # "my baby has eczema can i give her egg" is an allergen question with a skin word in it.
    entry("babyfood-eczema-and-egg",
          (("eczema", "dry skin", "flaky skin", "hives", "my baby has eczema", "baby eczema",
            "eczema and egg", "egg and eczema"),
           ("egg", "eggs", "peanut", "peanuts", "peanut butter", "milk", "dairy", "wheat",
            "soya", "soy", "sesame", "fish", "nut", "nuts", "allergen", "allergens", "allergy",
            "shellfish", "give", "start", "try", "introduce")),
          "Yes, and don't put it off because of the eczema: a baby with eczema is the one most "
          "likely to react, and early, regular tastes of egg and peanut lower the chance of a "
          "real allergy rather than raising it. Give a small amount in the morning, at home, on "
          "a day you are not going out, and keep it in their diet a couple of times a week once "
          "it is fine. If the eczema is bad or already infected, ask the GP or health visitor "
          "before you start, and if there is a reaction - hives, swelling, vomiting, wheeze - "
          "stop and call 999 if the breathing changes.",
          bias=8, ask=("give", "start", "try", "introduce", "have", "eat", "can i"),
          # The shared stand-down names "eczema" itself (an illness is not a menu), and this row
          # is keyed on the skin word, so that one word is left out of it here.
          avoid=NOT_A_BABY + tuple(word for word in NOT_A_MENU if word != "eczema")
          + ("my eczema", "i have eczema", "my skin", "itchy", "flare", "cream", "emollient",
             "steroid", "bad", "worse", "infected", "weeping", "oozing")),

    # "what milk should i give my 1 year old" is a milk question with no drink word in it, so
    # the volume row could not reach it and the toddler's litre card answered instead. Same
    # bands as the volume row, entered by the choice rather than the amount.
    entry("babyfood-which-milk",
          (("what milk", "which milk", "what kind of milk", "what type of milk", "best milk"),
           BABY + AGE + ("give", "giving", "should", "for", "to", "use", "buy")),
          _milk_volume, ask=BABY + AGE + ("give", "giving", "should", "use"),
          bias=3, avoid=NOT_A_MENU + NOT_A_BABY + WEANING_ELSEWHERE + _NOT_A_BABY_MILK),
    # A plant milk is not a milk for a baby, and rice milk is not one for a child either: the
    # amount card was answering "can my baby have rice milk" with newborn feeding, and
    # "can my baby have almond milk" with the peanut-butter row.
    entry("babyfood-plant-milks",
          (("rice milk", "rice drink", "oat milk", "oat drink", "almond milk", "soya milk",
            "soy milk", "soya drink", "coconut milk", "coconut drink", "plant milk",
            "plant based milk", "hemp milk", "cashew milk", "pea milk", "milk alternative"),
           BABY + AGE + ("have", "has", "give", "giving", "drink", "drinks", "drinking", "ok",
                         "safe", "use", "cook", "cooking", "instead", "can", "should")),
          _plant_milk, ask=("have", "has", "give", "giving", "drink", "drinks", "drinking",
                            "ok", "safe", "use", "cook", "cooking", "instead", "can", "should"),
          bias=4, avoid=NOT_A_MENU + NOT_A_BABY + WEANING_ELSEWHERE),
    # How much milk. "how much milk should my baby drink" was the litre-a-day water card, and
    # "a 6 month old" and "a 12 month old" made no difference to it.
    entry("babyfood-how-much-milk", (_MILK_WORDS, _MILK_HOW_MUCH, _A_DRINK),
          _milk_volume, ask=BABY + AGE + _THE_CHILD, bias=2,
          avoid=NOT_A_MENU + NOT_A_BABY + WEANING_ELSEWHERE + _NOT_A_BABY_MILK),
    # What goes in the cup, for the lines that ask the question whole. The water row answers a
    # named drink; this one answers "what can my baby drink" without naming one, which was the
    # litre-a-day card for a toddler.
    entry("babyfood-what-a-baby-drinks",
          # The whole question is a phrase as well as a word: the family row keyed on a child
          # word plus "drink" was answering "what can my baby drink" with the litre a day card
          # for a toddler, and a phrase outscores the two plain words it is made of.
          (BABY, ("what can my baby drink", "what can a baby drink", "what can babies drink",
                  "what should my baby drink", "what can my baby have to drink",
                  "how much should my baby drink", "how much should a baby drink",
                  "how much can my baby drink", "how much should babies drink",
                  "how much can a baby drink",
                  "straw", "straws", "sippy cup", "open cup",
                  "drink", "drinks", "drinking")),
          _what_a_baby_drinks,
          # A straw and a sippy cup are drink words, and the toddler's litre card outranked this
          # row on "can my baby drink from a straw".
          bias=4, ask=BABY + AGE,
          # A count of ounces or millilitres is the feeds question, which the family table
          # answers with eight to twelve in 24 hours; this row is what goes in the cup.
          avoid=NOT_A_MENU + NOT_A_BABY + _NOT_A_BABY_MILK + _A_COUNT),
    # "Is my baby getting enough" is the worry behind a lot of quiet turns. The signs are a
    # better answer than any amount, and the litre card was answering it because of the word
    # milk.
    entry("babyfood-getting-enough",
          (BABY, ("enough", "getting enough", "fed", "feeding well", "putting on weight")),
          "The signs are the answer, not an amount: six or more wet nappies a day, dirty nappies "
          "that turn from black to yellow in the first week, steady weight along their own line, "
          "and a baby who settles after a feed and is alert when awake. A baby who is drowsy, "
          "has fewer wet nappies or is not back to birth weight by two weeks needs to be seen.",
          bias=2,
          # What a baby can get enough *of* is a different question each time: iron, vitamin D
          # and sleep are not the nappies-and-weight answer, and a toddler's plate is not a
          # baby's feeds.
          avoid=NOT_A_MENU + NOT_A_BABY
          + ("toddler", "toddlers", "how much", "iron", "vitamin", "vitamins", "vitamin d",
             "calcium", "protein", "calories", "fibre", "fiber", "sleep", "sleeping",
             # the parent's own weight is a body question, and "i put on weight after my baby"
             # was answered with the nappies-and-weight card because the baby and the weight
             # are both in the line. Only the shapes where the person is the one weighing
             # something: "my baby has put on weight" is still this row's line.
             "i put on", "i have put on", "ive put on", "i've put on", "i gained",
             "lose weight", "losing weight", "lose the baby weight", "weight loss",
             "baby weight", "my own weight", "back to my old weight", "slimming")),
    # Whether it is time to start at all. The three signs are what a person is really asking
    # for, and "reaching for your food" or "waking at night" on their own are the two that get
    # people starting early.
    entry("babyfood-ready-for-solids",
          # "start" alone is the food question ("what food do i start my baby on"), so the key
          # wants the readiness words or the word solids next to it.
          # A pronoun is the child here too: "is she ready for food" and "when can i start
          # giving her food" were both a punt, and no baby word is ever said in them because
          # the chat has already named her. The food phrases are the same question asked with
          # the word "food" instead of "solids".
          (BABY + _A_CHILD_PRONOUN,
           ("ready", "readiness", "start solids", "starting solids",
                  "start on solids", "starting on solids", "first tastes",
                  # "signs" is the word the readiness question is asked with, and it is a
                  # phrase rather than the bare word because the same stem is the verb: "i
                  # signed up for a 12 month..." matched "signs" and, with the "month" of the
                  # contract, reached this row.
                  "the signs", "signs of", "any signs", "any sign", "a sign", "show signs",
                  "shows signs", "showing signs", "signs that", "signs should", "signs to",
                  "introduce solids", "introducing solids", "introduce food",
                  "introducing food", "give solids", "when to wean",
                  # the framing ("when do i introduce") is taken out of the line before the
                  # parts are counted, so the words left are the subject's own.
                  "solids", "solid food", "solid foods",
                  # the same question asked from the other end: "is my baby too young for
                  # solids at 4 months" reached nothing at all
                  "too young", "too early", "old enough", "young for solids",
                  "young for food", "early for solids",
                  # "when can i start giving her food", "when do i start giving food": the
                  # verb and the noun are the whole question, and "solids" is never said.
                  "start giving", "start food", "starting food", "start on food",
                  "give food", "giving food", "ready for food", "food ready",
                  "give her food", "give him food", "first food")),
          "Three signs, all at once, and around six months: sitting up with little or no "
          "support, steady head control, and swallowing food rather than pushing it back out "
          "with the tongue. Reaching for your plate or waking at night is not a sign on its "
          "own. Before four months is too early, and by six months it is time - waiting longer "
          "makes the iron and the chewing harder.",
          # The same guard as the row below: "is she ready for food" is the baby, and "is my
          # nan ready for food" is not.
          guard=_a_baby_or_a_pronoun,
          bias=1, avoid=STAND_DOWN + BOOK_WORDS),
    # What to feed, for the lines that name no age: "what should i feed my baby first" is the
    # same question as the one above with the age left out.
    # A named meal is not the first-foods question: "what can i give my baby for breakfast"
    # was this row's soft-food paragraph, where the cooking table names a breakfast that suits
    # a baby. The age-less first-foods ask keeps the row; a named meal keeps its own answer.
    # A pronoun is the child for the food list too: "what food should i start her on" and
    # "what can i give him for lunch" name no baby at all.
    # "give" is how the first food is asked for -- "what should i give her first" names no
    # food word at all, so the eating ask alone stood the row down.
    entry("babyfood-what-to-feed", (_WHAT_TO_FEED, BABY + _A_CHILD_PRONOUN), _FIRST_FOODS,
          # "what can i give him for lunch" is the baby; "my nan is diabetic, what can i take to
          # her for tea" is a nan, and this row answered it with the first-foods paragraph.
          guard=lambda u: _a_baby_or_a_pronoun(u) and _of_weaning_age(u),
          ask=EATING + ("give", "gives", "giving", "first", "start", "starting"),
          avoid=STAND_DOWN + ("breakfast", "lunch", "dinner", "supper", "snack", "snacks",
                             # a bottle, a cup and a night feed are not food to start on:
                             # "when should i stop giving my baby a bottle" was told to start
                             # with soft food in sticks. The family bottle row owns it.
                             "bottle", "bottles", "teat", "teats", "cup", "cups", "sippy",
                             "night feed", "night feeds", "night feeding", "off the bottle",
                             "sterilise", "sterilising", "formula")),
    # Baby-led weaning is a method rather than a food, so it is asked about by name. The answer
    # says what it is and settles the worry underneath, which is choking.
    entry("babyfood-baby-led-weaning",
          (("baby led weaning", "baby-led weaning", "blw", "babyled weaning"),
           ("what", "how", "is", "explain", "mean", "means", "safe", "better", "start",
            "started", "starting")),
          "Baby-led weaning means skipping spoon-fed purees and letting them pick up soft "
          "finger food themselves from about six months. It is safe at that age and no more of "
          "a choking risk than spoon feeding, and you do not have to choose: most people end up "
          "doing a mix of both.", bias=1, avoid=NOT_A_MENU + NOT_A_BABY),
    # Whether food has to be pureed. The answer is no, and the reason is the lumps-and-chewing
    # window, which is what the person is really asking about.
    entry("babyfood-puree",
          (BABY, ("puree", "purees", "pureed", "blend", "blended", "lumps", "lumpy", "smooth")),
          "You do not have to: soft finger food is safe from six months and teaches chewing "
          "sooner. If you do puree, keep it thick rather than watery and move on to lumps and "
          "finger food by about eight or nine months - a baby still on smooth food at one is "
          "the one who struggles with texture later.",
          bias=2, avoid=STAND_DOWN + A_BODY_LUMP),
    # A food can bring on an allergy, and this is the one weaning question with a timing rule
    # worth stating plainly. A line that says a reaction already happened is not this row.
    entry("babyfood-allergens",
          (BABY,
           ("allergen", "allergens", "allergy", "allergies", "sensitive", "sensitivities",
            "introduce", "introducing")),
          _the_allergen_row, bias=3, avoid=STAND_DOWN),
    # Asking how to introduce a food is asking about a first taste, and the allergen row cannot
    # take it: its first arm is a baby word and these lines name the food instead ("how do i
    # introduce eggs", "how do i introduce cow's milk", "how do i introduce solids"). Until this
    # row they were told to show the older child the scan picture, because "introduce" is a verb
    # about people too. The gate every row here passes (`_only_for_a_baby`) reads the verb plus a
    # food as a feeding line, so this row is the one that answers it.
    entry("babyfood-first-taste",
          (("introduce", "introducing", "introduced", "first taste", "first tastes",
            "first time giving", "start giving", "start on"),
           ("egg", "eggs", "milk", "cow's milk", "cows milk", "peanut", "peanuts",
            "peanut butter", "nut butter", "wheat", "fish", "sesame", "soya", "nuts", "dairy",
            "cheese", "yoghurt", "yogurt", "strawberry", "kiwi", "food", "foods", "finger food",
            "solids", "allergen", "allergens", "puree", "lumps")),
          ("One new food at a time, in the morning on a day they are well: a teaspoon is a first "
           "taste, then watch for twenty minutes, and a rash, swelling or sickness means stop and "
           "ring 111. Once a food is in, keep giving it a couple of times a week, because stopping "
           "is what raises the risk. Peanut and egg are the ones worth doing early rather than "
           "late, and with severe eczema or a reaction already, ask a GP before starting."),
          bias=2, avoid=STAND_DOWN + ("bottle", "bottles", "bottle feed", "formula", "dummy")),
    # A snack is its own question - how many, and what, between meals - and it is the one an
    # eating word only half covers: "what snacks can i give my baby" was the health visitor line
    # and "healthy snacks for a toddler" was "I'm listening". The age picks the band, the same way
    # it does for milk.
    entry("babyfood-snacks", (_SNACK, _SNACK_CHILD), _snacks, bias=1,
          avoid=NOT_A_MENU + NOT_A_BABY + _NOT_A_SNACK),
    # Three lines that reached a card about something else: a jar and a pouch of shop food got
    # the weaning start, ice cream got the birth registration, and a baby who only wants milk got
    # a supper idea. Each is a question a parent asks in the first year, so each gets a row.
    entry("babyfood-shop-bought",
          (("jar", "jars", "pouch", "pouches", "shop bought", "shop-bought", "ready made",
            "ready-made", "baby food", "commercial", "supermarket"),
           ("ok", "fine", "good", "safe", "healthy", "buy", "worth", "reheat", "warm", "use",
            "best", "better", "any good", "have", "give", "can")),
          "Jars, pouches and ready-made pots are fine, and the rules on them are the same as on "
          "anything else: no salt, no sugar, no honey before one. Read the stage on the front "
          "against what they are managing now, decant it into a bowl rather than feeding from the "
          "pouch, and throw away what the spoon has been in. Warm it by standing the bowl in hot "
          "water, never in the pouch or the jar, and check it is not hot in the middle.",
          # "can i buy baby pouches" reached the health-visitor line: the row's own words are the
          # question, so it is asked for and answered here rather than handed on. A grown-up
          # eating a jar of it is still the other row's question ("can i eat a whole jar of baby
          # food" is "Yes, it is just food"), hence NOT_A_BABY here.
          bias=2, avoid=NOT_A_MENU + NOT_A_BABY
          + ("fridge", "freezer", "keep", "last", "left out", "defrost", "batch")),
    entry("babyfood-ice-cream",
          (("ice cream", "icecream", "ice lolly", "ice lollies", "lolly", "lollies", "gelato"),
           BABY + ("toddler", "child", "children", "kid", "kids", "1 year old", "one year old")),
          "A taste of plain ice cream from six months is fine, and it is the sugar rather than the "
          "cold that is the reason not to make it a habit: the shop stuff is mostly sugar, and the "
          "cones are a choking shape for a baby. Frozen yoghurt, a frozen banana or a lolly made "
          "from fruit puree gives the same thing with less sugar in it.",
          bias=1, avoid=NOT_A_MENU + NOT_A_BABY),
    entry("babyfood-only-milk",
          (("only wants milk", "only wants Breast milk", "only drinks milk", "no interest in food",
            "not interested in food", "won't eat", "wont eat", "will not eat", "refuses food",
            "refusing food", "won't take food", "wont take food", "spits it out",
            # A baby who pushes the spoon away is saying the same thing as one who will not
            # eat, and the line is written as a report rather than a question about the food:
            # "she pushed the spoon away", "he spat it out" and "she turns her head away from
            # the spoon" were answered with a nod.
            "pushed the spoon away", "pushes the spoon away", "pushed the spoon", "spoon away",
            "pushed it away", "pushes it away", "pushes the food away", "pushed the food away",
            "spat it out", "spat the food out", "spat out", "turns her head away",
            "turns his head away", "turns away from the spoon", "turns away from food",
            "closes her mouth", "closes his mouth", "shakes her head", "shakes his head",
            "wont take the spoon", "won't take the spoon", "wont open her mouth",
            "won't open his mouth",
            # "she keeps spitting the food out" was the two-hours-out-of-the-fridge card: a meal
            # that comes back out of a baby is a refusal, not a food that has been sitting about.
            "spits the food out", "spitting the food out", "spits food out", "spitting food out",
            "keeps spitting the food out", "keeps spitting food out", "spitting it out",
            "keeps spitting it out", "spits it all out", "spitting it all out",
            "spits his food out", "spits her food out", "spat the food out"),
           BABY + _A_CHILD_PRONOUN
           + ("child", "children", "kid", "kids", "toddler", "toddlers")),
          "That is normal for the first weeks: milk is still their food, and eating is practice. "
          "Keep offering one or two teaspoons once a day without coaxing, put them in the chair "
          "with you eating at the same time, and let them see the food rather than putting it in "
          "their mouth. Go to the health visitor if they are past nine months and still taking "
          "almost nothing, if they are dropping weight, or if they gag and cough on every texture.",
          bias=1,
          # A pronoun only reads as the baby when a feeding word is beside it: "she pushed the
          # spoon away" is this row, and "she pushed me away" is not.
          guard=lambda u: _a_baby_is_named(u) or _a_pronoun_is_in_the_line(u),
          # The shared stand-down holds the refusal words themselves ("spits", "refuses",
          # "wont eat"), which is the one thing this row is here to answer: a word that is also
          # in the key zeroes the row, so "she keeps spitting the food out" matched nothing at
          # all once the fridge card was fenced off. They come out for this row only.
          # "shakes his head" is in the key, and a pronoun is in the guard, so a pet reached this
          # row and was told milk is still his food: "my dog keeps shaking his head" and "my
          # puppy is shaking his head" got the weaning answer instead of the ear one. A pet is
          # not a baby here, the same stand-down the rows above already take.
          avoid=tuple(word for word in NOT_A_MENU + NOT_A_BABY
                      + ("ill", "unwell", "poorly", "temperature", "fever", "sick")
                      if word not in _THE_REFUSAL_WORDS)
                  # "normal for the first weeks" is a baby on their first spoons, and a word in
                  # both the key and the stand-down zeroes the row: a toddler spitting food out
                  # is the fussy-eating question, not this one.
                  + ("toddler", "toddlers", "child", "children", "kid", "kids")),
    entry("babyfood-lumpy-food",
          (("refuses lumpy food", "refusing lumpy food", "won't eat lumpy food",
            "lumpy food", "lumpy foods", "lumpy", "refuses lumps", "hates lumps", "lumps",
            "lumpier", "texture", "textures", "chewy",
            # "bits" was here on its own and swallowed the quantity in "a bit of": every baby
            # food line with a small amount in it - "can i give my baby a bit of honey" (the
            # honey row's question, and the one that matters), "a bit of yoghurt", "a bit of
            # water", "a bit of spice" - was answered with "Do not blend it back". Only the
            # words that are about the pieces themselves count now.
            "bits of food", "bits of it", "the bits", "spits the bits", "chunks"),
           # "when can she have lumps" names the baby only as "she", so the pronoun is a part
           # of this row as well as the word "baby" is of the others.
           _BABY + _THE_CHILD
           + ("refuse", "refuses", "refusing", "refused", "hates", "hate", "won't", "wont",
              "will not", "spits", "gags", "struggles", "too early", "have", "has", "try",
              "start", "move on", "when", "can")),
          "Do not blend it back: the window for lumps is about seven to nine months, and a baby "
          "who stays on smooth food gets crosser about texture later. Mash rather than puree, "
          "leave soft lumps you can squash with a fork, and give finger food next to the spoon so "
          "they are practising chewing whatever the spoon does. Gagging while they learn is normal "
          "and it is not choking - stay calm, sit them up, and let them bring it forward.",
          # Not STAND_DOWN: the milk-refusal words in it ("refuses", "won't take") are half of
          # what this row is asked with, and they kept "my baby refuses lumpy food" on the
          # cooking row about whisking lumps out of sauce.
          bias=4,
          # "lumps" is the word a lump in your own armpit and a lump in the garden both use, so
          # the baby has to be in the line: "i have a lump in my armpit" was answered with "Do
          # not blend it back: the window for lumps is about seven to nine months". A pronoun
          # keeps "when can she have lumps", which says the baby only as "she".
          # A row between two adults is not a weaning question either: "he got a bit heated with
          # me" was this card, on the pronoun and the word "bit"
          # (bot/knowledge/lookup.py, not_the_heat_of_an_argument).
          guard=lambda u: (_a_baby_is_named(u) or _a_pronoun_is_in_the_line(u)) \
          and not_the_heat_of_an_argument(u),
          # Not the shared stand-down: "refuses" and "wont eat" are in it for the illness and
          # milk rows, and they are two of the words this row is asked with.
          # "my daughter chews her nails" is a nail line that reached this row on "chews" and
          # "her": a child's nails are not lumps in a weaning meal.
          avoid=NOT_A_BABY + WEANING_ELSEWHERE + _HOW_MUCH_MILK
          + ("nails", "nail", "fingernails", "fingernail", "nail biting", "cuticles",
             "choking", "choke", "first aid", "fever", "temperature", "rash", "ill", "unwell",
             "poorly", "not feeding", "isnt feeding", "breathing", "hospital", "999", "111",
             # A lump on a body is a health question and nothing to do with texture: "my baby
             # has a lump on his head" was answered with "do not blend it back". The body
             # parts are named, so "does he have to have lumps" is still this row.
             ) + A_BODY_LUMP),
    # A lump in a baby's mouth is a health question like a lump anywhere else, and it had no
    # row of its own: "my baby has a lump in his mouth" dropped to "Thanks for telling me" and
    # "my baby has a lump on his cheek" to "Got it.", because the adult mouth-lump card is keyed
    # on "my mouth" and nobody's baby says that. Saying where it is beats a bare lump.
    entry("babyfood-lump-in-mouth",
          (("lump in his mouth", "lump in her mouth", "lump in their mouth", "lump in the mouth",
            "lump in his gums", "lump on his gums", "lump on her gums", "lump on the gum",
            "lump on his gum", "lump on her gum", "lump in his cheek", "lump on his cheek",
            "lump on her cheek", "lump on the cheek", "lump inside his cheek",
            "lump under his tongue", "lump on his tongue", "lump on his lip", "lump on her lip",
            "lump on the roof of his mouth", "bump in his mouth", "bump on his gum",
            "bump on his cheek", "white lump in his mouth", "lump inside his mouth"),
           ("baby", "babies", "newborn", "month old", "months old", "year old", "toddler",
            "child", "son", "daughter", "kid", "what", "why", "should", "worried", "is it",
            "normal", "check", "how", "have", "has", "got", "noticed", "found", "there is")),
          "Most lumps in a baby's mouth are harmless: the little white pearls on the gums of a "
          "newborn, a mucocele from a bite on the lip, or a firm bony bump on the roof of the "
          "mouth. Leave it alone, do not squeeze it, and keep the mouth clean. Show it to the "
          "health visitor, a dentist or a GP within two weeks if it is still there after three "
          "weeks, or if it is hard, bleeding, growing, or comes with a fever or with a baby who "
          "will not feed - that is a check, not an emergency. A lump on the outside of the cheek "
          "is a skin lump and is usually harmless too; the ones that need a look are the same "
          "ones, plus anything that is hot and spreading.",
          bias=4,
          avoid=NOT_A_BABY + WEANING_ELSEWHERE + _HOW_MUCH_MILK
          + ("tooth", "teeth", "teething", "toothache", "dentist appointment", "brace", "braces",
             "ulcer", "ulcers", "cold sore", "blister", "blisters", "hand foot and mouth",
             "chickenpox", "measles", "mumps", "tonsil", "tonsils", "tongue tie")),

    # A reaction to a food went to a greeting ("my baby has a reaction to egg" got "I'm
    # listening"), which is the one kind of line in this table that must never be answered with
    # a nod. The safety card keeps the emergencies: anything airways or floppy stands this down.
    entry("babyfood-food-reaction",
          (BABY + ("child", "children", "kid", "kids", "toddler", "toddlers", "1 year old",
                   "one year old"),
           ("reaction", "reacted", "reacts", "reacting", "allergic", "allergy", "hives",
            "swollen", "swelling", "rash round the mouth", "sick after eating")),
          "Stop giving that food and watch them for the next two hours. A rash, hives, swelling "
          "round the mouth, vomiting or a runny tummy is worth a same-day call to the GP or 111, "
          "and write down what they ate, how much and how long it took. Swelling of the lips or "
          "tongue, a hoarse cry, noisy breathing, or going pale and floppy is 999 - that is "
          "anaphylaxis and it needs an ambulance, not a wait. Do not try that food again until "
          "you have been told it is safe to.",
          bias=4,
          avoid=NOT_A_BABY
          + ("breathing", "wheeze", "floppy", "limp", "unresponsive", "999", "ambulance",
             "epipen", "epi pen", "tongue", "hay fever", "hayfever", "vaccine", "vaccination",
             "jab", "jabs", "mmr", "immunisation", "nappy rash", "teething", "covid")),
    # Dropping the milk was a shrug, and it is one of the most common questions of the second
    # half of the first year: what to stop, in what order, and how much milk is left at the end.
    entry("babyfood-dropping-feeds",
          # The phrase carries the question; the second arm is the milk word, because
          # "how do i drop a feed" names no baby and still means this.
          (("drop a milk feed", "drop a feed", "drop feeds", "dropping feeds",
            "stop breastfeeding", "stop breast feeding", "stop nursing", "stop feeding",
            "wean off the breast", "give up breastfeeding", "finish breastfeeding",
            "dropping milk feeds", "drop a bottle", "drop the bottle", "dropping bottles",
            "cut down feeds", "cut down bottles", "cut down on bottles", "fewer feeds",
            "fewer bottles", "give up a feed", "stop a feed", "stopping feeds", "reduce feeds",
            "reduce milk", "less interested in milk", "feeding less"),
           BABY + ("milk", "bottles", "bottle", "feeds", "feed", "bf", "breastfeeding",
                   "child", "children", "kid", "kids", "toddler", "toddlers")),
          "One feed at a time, about a week apart, and start with the one they are least "
          "bothered about - usually the mid-morning or mid-afternoon bottle rather than the first "
          "or the bedtime one. Offer a cup and a snack at the time you dropped, expect a few "
          "grumpy days, and keep the bedtime feed longest because it is doing the most work. Milk "
          "falling as food rises is the plan, not a problem: by a year three meals, two snacks "
          "and about 350 to 400ml of milk a day is enough.",
          bias=3,
          # A baby of a few weeks who has stopped feeding is the family table's urgent card, and
          # the words that make a line that one stand this row down.
          avoid=NOT_A_MENU + NOT_A_BABY + _HOW_MUCH_MILK
          + ("newborn", "newborns", "neonate", "weeks old", "week old", "1 month old",
             "2 month old", "3 month old", "one month old", "two month old", "three month old",
             "not feeding", "isnt feeding", "isn't feeding", "refusing feeds", "not taking feeds",
             "too sleepy")),
    # "what foods to avoid for a baby" is the other half of first foods and it was answered with
    # the list of things to give. The question is the one where a wrong answer costs most, so it
    # gets a row of its own, ordered by what actually goes wrong: salt, honey, choking shapes.
    entry("babyfood-what-to-avoid",
          (("what foods to avoid", "foods to avoid", "what food to avoid", "what not to give",
            "foods not to give", "what not to feed", "foods not to feed",
            "what should i not give", "what should i not feed", "what shouldnt i give",
            "what shouldn't i give", "what should i avoid", "foods should i avoid",
            "avoid giving", "foods to avoid giving", "what to avoid giving",
            "not feed my baby", "not feed a baby", "not give my baby", "should i not feed",
            "foods are unsafe",
            "unsafe foods", "what is unsafe to give", "what is unsafe to feed",
            "what cant my baby eat", "what can't my baby eat", "what can a baby not eat",
            "what cant a baby eat", "what can't a baby eat"),
           BABY + AGE + _THE_CHILD,
           ("avoid", "unsafe", "not", "give", "giving", "feed", "feeding", "eat", "eating",
            "food", "foods", "should", "what", "can")),
          "No salt and no sugar, and no honey at all before the first birthday. No whole nuts, "
          "whole grapes, popcorn or anything hard and round, because those are the shapes that "
          "block a small throat - cut grapes and cherry tomatoes into quarters lengthways. Skip "
          "low-fat and diet foods, unpasteurised cheese, raw or runny egg without the red lion "
          "stamp, and shark, swordfish and marlin. Cow's milk as a drink waits until twelve "
          "months, though in cooking it is fine from six; tea, coffee, cola and juice are not "
          "needed at any age.",
          # The newborn "not feeding" row is keyed on the same words and it wins the tie without
          # a bias of its own here: "what should i not feed my baby" is a food question, and a
          # baby who really has stopped feeding names an age these lines do not.
          bias=5,
          # A baby who is choking or reacting is a first-aid card, not a list, and the illness
          # rows and the reaction row keep theirs.
          avoid=NOT_A_MENU + NOT_A_BABY + WEANING_ELSEWHERE
          + ("water", "juice", "squash", "milk", "drink", "drinks", "drinking", "thirsty",
             "bottle", "bottles", "cup",
             # The mother eating is not the baby eating: "what foods should i avoid while
             # breastfeeding" was this list of things not to give a baby. A feeding mother has
             # no list to avoid, and nutrition.py's food-while-breastfeeding says so.
             "breastfeeding", "breast feeding", "breast-feeding", "nursing", "lactating",
             "chestfeeding", "while im feeding"),
          # The baby is already a part of the key, so `ask` only has to insist on the ask that
          # makes it a question about what not to give: an age is often absent from these lines.
          ask=("avoid", "not", "unsafe", "give", "giving", "feed", "feeding", "eat", "eating")),
    # "how much water should my baby drink" was the litre-a-day card for a toddler, which is
    # the wrong amount and the wrong person. The phrases are whole, because a bare "how much"
    # is the milk question's and the toddler's card answers it.
    entry("babyfood-how-much-water",
          (("how much water", "how much water should", "how much water can",
            "how much juice", "how much squash"),
           BABY + ("child", "children", "kid", "kids", "drink", "drinks", "day")),
          _how_much_water,
          bias=4,
          # "how much water do i need a day" is an adult's question, and the words that make
          # this row reach it ("water", "day") are the same words an adult uses: the second
          # part cannot tell a baby from a grown-up, so the line itself has to name one.
          # The `avoid` below cannot do it - it stands down for "child" and "toddler", which
          # are the words the baby questions are asked with.
          guard=lambda u: _a_baby_is_named(u) or _a_pronoun_is_in_the_line(u),
          # The shared stand-down names "how much water" itself (the cup row must not answer an
          # amount), and a row keyed on the question cannot carry that word in its own avoid.
          avoid=NOT_A_BABY
          + tuple(word for word in NOT_A_MENU
                  if word not in ("how much water", "how much juice"))
          + ("toddler", "toddlers", "child", "children", "kids", "2 year", "3 year", "4 year",
             "5 year", "i drink", "should i drink")),
    # "should i wake my baby to feed" was answered with the funeral-tea buffet ("food that needs
    # no carving and no serving"), because "wake" is in that row's key and "feed" in its ask. The
    # question is the commonest one a new parent asks at three in the morning, and the answer is
    # a rule about weight and weeks, not a plate of sandwiches.
    entry("babyfood-wake-to-feed",
          _WAKE_TO_FEED_KEY,
          "No, not once they are back to their birth weight and gaining: a baby who sleeps is "
          "allowed to sleep, and night waking is normal for the first months. Wake them for a "
          "feed only if they are under two weeks old, were early or small, are jaundiced, are not "
          "yet back to their birth weight or are too sleepy to take a full feed - then offer every "
          "two to three hours, and make it worth their while: change the nappy first, undress them "
          "to the vest, and stroke a cool flannel over the hands and face.",
          bias=3,
          # A key word in a row's own avoid zeroes the row, so the shared stand-down is read
          # against this row's key: "sleep", "sleeping" and "how often" are the words it was
          # losing on.
          avoid=tuple(word for word in NOT_A_MENU
                      if word not in _WAKE_TO_FEED_WORDS)
          + ("alarm", "alarm clock", "wake up early", "wake up tired", "wake up at night",
             "cant sleep", "can't sleep", "insomnia", "tired all the time", "wake up",
             "woken up by", "wake me up", "for the wake", "funeral")),
] + [_verdict(row["names"], row["reply"], row.get("extra", ()), row.get("bias", 0),
                 row.get("own_ask"), row.get("pronoun", False))
     for row in FOODS]


def _a_line_that_feeds_a_baby(understood):
    """Whether this line, or the line it leans on, names somebody being fed.

    The same test the reply makes, made before the best entry is chosen rather than after. An
    empty reply is how a row says "not mine", but a row that says it has already taken the
    turn: the topic the next line leans on is read from the entry that won, and the rows either
    side lose a line they would have answered.
    """
    if _the_line_feeds_somebody(understood, {}):
        return True
    leans = understood.get("leans_on") if isinstance(understood, dict) else None
    words = leans.get("words") if isinstance(leans, dict) else None
    if not isinstance(words, list):
        return False
    carried = " %s " % " ".join(str(word).lower() for word in words if isinstance(word, str))
    if _AGE_FIGURE.search(carried):
        return True
    return any((" %s " % word) in carried for word in _NAMES_A_BABY)


def _only_for_a_baby(row):
    """One gate for the whole table: nobody who is not feeding a baby is answered from it.

    The check is done here, once, rather than in every row: a row that names a food is one
    sentence away from the same question an adult asks about their own lunch, and the two are
    told apart by who is named, not by the food. A row's own reply callable still runs inside.
    """
    reply = row.reply

    def gated(memory, understood):
        if not _the_line_feeds_somebody(understood, memory):
            return None
        return reply(memory, understood) if callable(reply) else reply

    row.reply = gated
    # and stand it down as a candidate, not only at the reply: a row with a guard of its own
    # keeps it (the two that name the baby or the pronoun in the line)
    if getattr(row, "guard", None) is None:
        row.guard = _a_line_that_feeds_a_baby
    return row


ENTRIES = [_only_for_a_baby(row) for row in ENTRIES]
