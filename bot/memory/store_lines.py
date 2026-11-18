"""The store's template pools: the words it reads and the words it says.

Every upper-case pool in `bot/modules/memory_store.py` whose value is a literal - a string, a
tuple or a list of them, or a group of pools named from them - lives here, so the module that
reads and answers with them stays a readable size. They are moved, not rewritten: the values are
identical, and the module imports every name back, so `memory_store.TOPIC_ASK` is the same object
it always was. A pool built by calling something at import time (`tuple(_p(...) for ...)`) stays
in the module, because moving it would move the words and the code that makes them apart.
"""

import re

PRIORITY = 7000

# The one topic this module is a specialist in: the animals a person has just told us about. A
# naming ask ("what should I call it?") is read as a pets line, and the pet entry - litter tray,
# bowls, a vet visit - would take the turn on that word while the store's own line, the names
# themselves, sat in front of it. Declaring the topic is what the arbiter's specialist rule needs
# to keep the answer that was asked for.
#
# Both declarations belong in one tuple: the ages an ask reads back ("what ages are my kids" is
# read as "family-and-parenting") were added as a second `ANSWERS = ...` line, which silently
# replaced the pets one and handed the naming ask back to the pet entry (litter tray, bowls).
# It is deliberately a short list: declaring every topic would make the store take lines where an
# entry has the better answer ("she doesnt eat meat" is advice about the meal, not the fact).
ANSWERS = ("pets", "family-and-parenting")

RECALL_HINTS = ("say", "said", "saying", "remember", "recall", "again", "told", "tell", "know",
                "what's", "whats", "what")

SELF = ("you", "your", "we", "i")

# A plan ask with a "for" on it names its own subject: "whats my plan for dinner" is a meal and
# "whats my plan for the weekend" is the weekend, not the plan they told us about.
NOT_THE_PLAN = r"(?!\s+for\b)"

# "Anything on?" asks what is in the diary, and "anything on bbc" asks what to watch: a medium
# after "on" is what makes the line about television rather than about the plans, and the store
# answered the first with its empty calendar and read out "You haven't told me about anything
# coming up yet" to a person choosing something to watch.
# A night out names its venue the same way and was read the same way: "is there anything on at
# the cinema" and "anything on at the pictures" got the empty calendar, so the places people go
# to be shown something stand beside the media, with or without the "at the" in front of them.
# "the cinema", "a gig" and "the pictures" are where; a channel and a venue are both a place
# that answers the question before any plan does.
ON_A_MEDIUM_OR_AT_A_VENUE = (
    r"telly|tv|television|radio|bbc|itv|channel|netflix|amazon|prime|disney|iplayer|now\s?tv|"
    r"sky|spotify|youtube|cinema|cinemas|pictures|theatre|theater|matinee|gig|gigs|concert|"
    r"concerts|arena|playhouse|"
    # A device is not a plan either, and it is the one people say "on" about most: "i cant hear
    # anything on my phone", "there's nothing on my screen" and "anything on my laptop" all
    # reached the empty calendar, which answered a fault with "Nothing so far - you haven't
    # mentioned anything coming up. What have you got?". The thing spoken from, and the thing
    # things are seen on, are as much a subject after "on" as a channel is.
    r"phone|phones|mobile|screen|screens|monitor|laptop|laptops|computer|computers|pc|"
    r"tablet|tablets|ipad|kindle|speaker|speakers|headphones|earphones|earbuds|device")
NOT_ON_A_MEDIUM = (r"(?!\s*(?:(?:at|in)\s+)?(?:the\s+|a\s+|my\s+|our\s+)?(?:"
                   + ON_A_MEDIUM_OR_AT_A_VENUE + r")\b)")

# The words a request to hear the reply again can carry and still be only that request: "repeat
# that slowly", "say that again step by step". They are taken off the line before its words are
# counted, so they cannot make a line about the steps an ask for the last reply.
REPEAT_ADVERB = (r"(?:again|slower|slowly|step by step|once more|clearer|simply|for me|"
                 r"please|thanks|in order)")

# The facts that are a limit: what a person cannot eat, what they do not eat, and what they have.
# These are the three a second person shares, and the only three: "my son is 6" then "im too" is
# not an age of the person talking.
LIMITS = ("allergies", "diet", "condition")

DENIAL_SAY = {"allergies": "{Thing} back on the table, then.",
              "condition": "Right, no {thing} \u2014 that makes things easier, then.",
              "diet": "Right \u2014 meat is back on the table, then.",
              "pets": "Right \u2014 no {thing}, then."}

# A correction that names the right thing as well as the wrong one - "im allergic to soya not
# peanuts" - is not only a fact being taken back: the new one is the fact to say back, and the
# old one is what it replaced. Said as one breath, because "peanuts back on the table" alone
# leaves the person wondering whether the soya was heard.
CORRECTED_SAY = {"allergies": "{Thing}, not {old} \u2014 got it.",
                 "condition": "Right, {thing} now, not {old} \u2014 got it."}

# What the store has to call a fact when it says one back after a retraction.
RETRACT_SAY = {"allergies": "the allergy note", "condition": "the health note",
               "diet": "the diet note", "budget": "the budget", "job": "the job",
               "city": "the place you live", "from": "where you\u2019re from",
               "born": "where you were born", "age": "your age", "height": "your height",
               "name": "your name", "places": "that place"}

# A retraction takes back what the line before it said. `people` is not that: it is the set of
# people the chat has mentioned, written by every line that names one, and dropping it on "take
# that back" answered a condolence with "Right - that person is off the record, then." A taste and
# someone else's fact are left for the same reason: they are not what a retraction names.
NOT_RETRACTED = ("taste", "other", "people", "pet", None)

_FACT_SLOT = ("(?:job|work|name|budget|allerg\\w*|pets?|cats?|dogs?|kittens?|pupp(?:y|ies)|"
             "animals?|salary|birthday|age|partner|husband|wife|kids?|children|son|daughter|"
             "mum|mom|dad|sister|brother|car|address|postcode)")

# How long a corrected age can be said in: a short line about the figure, not a new sentence
# that happens to hold a number.
PET_AGE_FIX_WORDS = 8

# A fact kept against someone the user looks after is corrected by saying it again in their
# shape ("my mum is allergic to peanuts"), because that is the reading that already knows how to
# keep it. What the saying can carry, and how the note words it, per kind of fact.
OTHER_SAID = (("name", "is called"), ("allergies", "is allergic to"), ("condition", "has"),
              ("diet", "is"), ("diet", "eats"))

OTHER_KIND_SAY = {"name": "{v}, got it.",
                  "allergies": "{v} it is, then \u2014 I'll keep your {who} off those.",
                  "condition": "{v} it is, then \u2014 I'll keep that in mind for your {who}.",
                  "diet": "{v} it is, then \u2014 that's what I'll go with for your {who}."}

AGE_FIX_WORDS = 8

NAME_FIX_WORDS = 9

NAME_GIVEN_WORDS = 5

# The unit a value is said in, and the family it measures. A figure is only a correction of
# something measured the same way: "5 kilos" is the plan when the plan is losing kilos, while
# "no 2 weeks" after a budget of 400 is a duration, and taking its figure as the budget said
# "your budget is 2". The words are the ones the correction shapes allow after a number.
UNIT_FAMILY = {"pound": "money", "pounds": "money", "quid": "money", "euro": "money",
               "euros": "money", "dollar": "money", "dollars": "money", "k": "money",
               "kilo": "weight", "kilos": "weight", "kg": "weight", "kgs": "weight",
               "kilogram": "weight", "kilograms": "weight", "stone": "weight",
               "stones": "weight", "st": "weight", "lb": "weight", "lbs": "weight",
               "gram": "weight", "grams": "weight", "g": "weight",
               # A height is measured the way a weight is (FACT_FAMILY maps both to "weight"),
               # so a figure put right in either unit lands on it: "i am 175cm" then "make it
               # 180cm", and "im 5 foot 10" then "no, 5 foot 8".
               "cm": "weight", "centimetre": "weight", "centimetres": "weight",
               "centimeter": "weight", "centimeters": "weight", "foot": "weight",
               "feet": "weight", "ft": "weight", "inch": "weight", "inches": "weight",
               "litre": "volume", "litres": "volume", "liter": "volume", "liters": "volume",
               "mile": "distance", "miles": "distance", "km": "distance",
               "minute": "time", "minutes": "time", "min": "time", "mins": "time",
               "hour": "time", "hours": "time", "day": "time", "days": "time",
               "week": "time", "weeks": "time", "month": "time", "months": "time",
               "year": "time", "years": "time"}

# What a fact kept by the store is measured in, for the facts that are measured in something.
# A budget given as "400" names no unit, but a correction of it said as "600 pounds" is still
# money: the fact's own key says which family a value for it can be in.
FACT_FAMILY = {"budget": "money", "pay": "money", "salary": "money", "wage": "money",
               "rent": "money", "price": "money", "spend": "money",
               "weight": "weight", "height": "weight", "distance": "distance"}

# Words that carry the rest of the plan rather than a unit after a number, as an alternation.
NOT_A_UNIT = (r"in|on|at|for|by|before|after|and|then|this|next|of|to|from|until|till|or|but|so|"
              r"with|without|the|a|an")

# The words an amount is said in when it is not a figure: "half a stone", "a couple of weeks",
# "a few minutes". The plan's own amount is swapped in one piece, so the words after it stay put.
AMOUNT_WORD = (r"(?:an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve"
               r"|half\s+an?|half|a\s+couple\s+of|a\s+few|a\s+bit\s+of"
               r"|\d+(?:[.,]\d+)?)")

SPELLING_APART = 3

# A value taken back says so on its own: nothing is put in its place, so "got it, {v}" would
# read as if it had been noted.
CORRECTION_SAY_DROP = {"allergies": "Got it — no {v}."}

# The facts that are a list of things the person named, so one of them can come off again.
DROP_LISTS = ("allergies",)

CORRECTION_SAY = {"budget": "{v} — got it, I'll work to that.",
                  "pet": "{v} — got it, I'll call the {a} {v}.",
                  # A count corrected says the count back at the size the person put it.
                  "pets_count": "{v} — got it.",
                  # A count of children is corrected by the bare new count, and the note
                  # says the count back the way the person would.
                  "kids": "{v} — got it.",
                  "name": "{v} — got it, I'll call you {v}.",
                  # A name given for somebody else: the person is in the store, not the ask.
                  "person_name": "{v} — got it, I'll say {v}.",
                  "age": "{v} — got it, {v} it is.",
                  # A weight is said back in its own sentence, unit and all, so the reply cannot
                  # read as if the unit had been dropped or the figure were a count of something.
                  "weight": "{v} — got it, you weigh {v}.",
                  "city": "{v} — got it, I'll say {v}.",
                  "places": "{v} — got it, I'll say {v}.",
                  "job": "{v} — got it, I'll say {v}.",
                  # A plan is said back as the sentence it was kept in, so the note carries the
                  # rest of it ("a trip to Lisbon in May") instead of a bare value.
                  "plan": "Got it — {v}.",
                  "allergies": "{v} — got it, I'll keep that out of anything I suggest.",
                  # A birthday is a date, and a date said back as a bare value ("The 4th of May —
                  # got it") is the one fact where the words around it are what say what it is.
                  "birthday": "Got it — your birthday is {v}.",
                  # A whole plan said back with its new number: "got it — leave for the airport
                  # at 5", not a bare "5" the person cannot place.
                  "line": "{v} — got it."}

# A correction that names the wrong value as well says both back, so the person hears which
# number it is that went.
CORRECTION_SAY_PAIR = {"plan": "{v}, not {w} — got it."}

# A pet's name put right is not a number going up: it is a name, it is the one the person will
# use every day, and the reply that carries it is the chat going on rather than a receipt. The
# terse note ("Max, not Milo — got it.") said the right thing and stopped, so a correction of a
# name read colder than the line that gave the name in the first place ("A cat called Milo.
# What's it like to live with?"). Two reviewers marked it on the shapes people use most. So the
# note keeps both names - the person is checking they were heard, and the old one is what got
# replaced - and then says one warm thing about the pet that is now called that. Varied, because
# the same words twice in a chat is the bot reading itself back.
PET_RENAMED_SAY = (
    "{v}, not {w} — got it. How's {v} settling in?",
    "Right — {v}, not {w}. That's the name I'll use.",
    "{v}, not {w} — noted. {v} it is from now on.",
    "{v}, not {w}; glad you said. How's {v} getting on?",
)

BARE_ECHO_ONLY = "{v} — got it."

# How many lines back a correction may reach for the fact it is fixing. A person says a fact,
# asks about it, hears it said back and only then hears it wrong ("im a nurse", "whats my job?",
# "no i mean a teacher"), so the fact is not always on the line just before the correction.
CORRECTION_BACK = 4

# The clock a plan says after "at": "at 6", "at 10.30am", "at noon". The figures are read
# without a word boundary after them, because that boundary does not fall between the minutes
# and the am in "10.30am": `\b` after "10" fails on "10.30am", so the match stopped at the hour
# and the store answered "what time is my interview" with "At 10." over a plan saying 10.30am.
AT_TIME_VALUE = (r"(?:\d{1,2}(?:[:.]\d{2})?(?!\d)"
                r"|(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
                r"|noon|midday|midnight)(?:\s*(?:am|pm|o'?clock))?")

# How old someone they told us about is. "how old is my son", "what age is your mum", "how old
# are the kids": the number was given with the person ("my son is 7"), so memory has it and the
# world does not.
# What someone they told us about is called: "what's my sister called", "whats my sisters name",
# "what is my brothers name". The name was given with the person ("my sister is called meg"), so
# this is a fact about the chat; without it the line fell through to the search hedge.
# The relation an ask names may be said with "in law" after it: "what is my brother-in-law
# called", "what is my mother in laws name". One person, whichever way it is typed.
KIN_ASK = r"[a-z]+(?:[ \t]*-?[ \t]*in[ \t]*-?[ \t]*laws?)?"

# "in law" said after a relation word, however it is typed: "brother-in-law", "sister in law".
# The person the ask is about is the in-law, not the brother, and the store files them under the
# plain phrase, so the ask has to be read the same way.
IN_LAW_AFTER_TEXT = r"[ \t]*-?[ \t]*in[ \t]*-?[ \t]*laws?\b"

# Which people a pronoun can point at: "his" is a he, "her" is a she, "their" either.
PRONOUN_FITS = {"his": ("he",), "him": ("he",), "he": ("he",),
                "her": ("she",), "she": ("she",),
                "their": ("he", "she"), "them": ("he", "she"), "they": ("he", "she")}

# A child they have named is a child they have, so a count the store was never given says so
# rather than a flat no.
CHILD_RELATIONS = ("son", "daughter", "child", "kid", "boy", "girl", "stepson", "stepdaughter",
                   "twins")

# "what do you know about my mum", "tell me about my sister", "what did i say about my son":
# a recall ask that names someone else in the family asks for the whole person, not one line of
# them, so it is answered with everything the store holds about that person. The words that make
# it a recall are the asking ones: "what do you think about my sister" is an opinion, not this.
# "about her" is the same ask about the person just named, which is how a follow-up comes.
# "the kids" is the same ask as "my kids": a household's children have no other word for them,
# and "tell me about the kids" was falling past this to the search hedge with both names on file.
_ABOUT_WHO = (r"(?:my|our)\s+[a-z]+\b|the\s+(?:kids?|children|child)\b|her\b|him\b|"
              r"them\b|she\b|he\b|they\b")

# The ask that names no person but means the people already given an age: "how old are my kids",
# "what ages are the children", "how old are they".
# The people a "my kids" / "the children" ask is about.
# "my boys" and "my girls" are children too, and a line that gives them by name and age files
# them under that word, so an ask in the same word has to find them. "my youngest" and "my eldest"
# are how people name one of several children, so "how old are my kids" answers with them instead
# of denying ages the chat was just given.
CHILD = ("son", "daughter", "twins", "baby", "child", "kid", "boy", "girl", "youngest", "eldest",
         "oldest")

# The plural of a child word names the same child: "my children are 4, 7 and 9" is filed under
# "children", and a later "the kids" asks about that entry, so the plural is read as its singular
# and not as some other word the store keeps.
CHILD_OF = {"children": "child", "kids": "kid", "childs": "child", "babies": "baby",
            "boys": "boy", "girls": "girl", "sons": "son", "daughters": "daughter"}

# A word that names a family as a group, and the people the store may already have in it: "how
# old are my parents" is the mum and the dad the chat has been told about. The ask keeps the word
# they used - the store used to singularise it and answer "You haven't told me how old your parent
# is", which is a fact it holds said back to them as a denial.
FAMILY_GROUP = {
    "parents": ("parent", "mother", "mum", "mom", "mam", "mummy", "mommy", "father", "dad",
                "daddy", "papa", "stepmother", "stepfather"),
    "grandparents": ("grandparent", "grandmother", "grandma", "gran", "nan", "nana", "granny",
                     "grandfather", "grandad", "granddad", "grandpa"),
    "siblings": ("sibling", "brother", "sister", "half brother", "half sister"),
    "brothers": ("brother", "half brother"),
    "sisters": ("sister", "half sister"),
    "kids": CHILD,
    "children": CHILD,
    "twins": ("twin", "son", "daughter", "child", "kid"),
    "boys": ("son", "boy", "child", "kid"),
    "girls": ("daughter", "girl", "child", "kid"),
    "grandchildren": ("grandson", "granddaughter", "grandchild"),
    "uncles": ("uncle",),
    "aunts": ("aunt",),
    "cousins": ("cousin",),
}

# The foods that are two words: a word set splits on the gap, so "peanut butter" would be read as
# "peanut" and the answer would name the wrong thing. Longest phrase first, then the single words.
FOOD_PHRASES = {
    "nuts": ("peanut butter", "satay sauce", "nut butter", "nut roast", "almond milk"),
    "peanuts": ("peanut butter", "satay sauce", "nut butter"),
    "dairy": ("ice cream", "ice-cream", "milk chocolate", "double cream", "sour cream",
              "cream cheese"),
    "gluten": ("soy sauce", "stock cube", "stock cubes"),
    "wheat": ("soy sauce", "stock cube", "stock cubes"),
}

# The answers that offer a side and name the case it is for: "A cat is the kinder choice if
# you're out all day". Only an answer like that can be chosen by the next line.
ADVICE_MODULES = ("answers", "chat")

# Which fact of theirs is held, by the key the store writes it under.
SLOT_KEY = {
    "name": ("name",),
    "job": ("job",),
    "city": ("city", "town", "from"),
    "budget": ("budget",),
    "allergy": ("allergies", "allergy"),
    "pets": ("pets",),
    "age": ("age",),
}

# The fact an ask that only names it is about. The words are the fact's own ("town" for the
# place they live, "age" for how old they are), and "work" is the job they do.
#
# Where they are from is left out on purpose, and "country" and "hometown" with it: the store
# keeps a place they are from and a place they live apart, and this slot is the second one. A
# line naming the first is answered by the reader the store already has for it
# ("i live in leeds" / "and my hometown" -> "You haven't said where you're from - I know you live
# in Leeds"), which is the accurate answer, not by "You live in Leeds."
BARE_SLOTS = (
    ("allergy", r"\ballerg"),
    ("budget", r"\bbudget"),
    ("pets", r"\b(?:dog|cat|pet|animal)s?\b"),
    ("job", r"\b(?:job|work)\b"),
    ("city", r"\b(?:city|place|town)\b"),
    ("name", r"\bname\b"),
    ("age", r"\bage\b"),
)

# A place question is about the person's own places only when it names them: "which city did i
# say first", "where do i live", "where is my sister living". "which country in europe has the
# second most people" has the same opening words and asks about the world, and the store has no
# business answering it with "You haven't mentioned a place yet." while geography knows the
# answer.
# "whereabouts" is the same ask word as "where": "whereabouts do i live" was answered by the
# search hedge while the store had the place on file.
WHERE_ASK = r"where(?:abouts| abouts)?"

# A person they love in trouble is not a day coming up, but a bare "im scared" is about them all
# the same: "my dad is in hospital" / "im scared" was answered "Worry like that is usually mostly
# 'what if'. Write down what's actually at stake and it gets smaller" - a line that would fit any
# frightening thing, and never says who it is about. The kin word and the bad news have to be in
# the one line, so "my mum is coming to stay" and "i read about a hospital" are left alone.
KIN = (r"mum|mom|mother|dad|father|son|daughter|child|kid|wife|husband|partner|brother|sister"
       r"|gran|granny|nan|nana|grandma|grandad|grandpa|grandmother|grandfather|friend|mate|baby"
       r"|children|kids|nephew|niece|aunt|uncle|cousin|stepson|stepdaughter")

# The news itself, in any tense somebody would say it in: "my son has been really unwell", "my
# mum was diagnosed with cancer", "my wife had a fall".
BAD_NEWS = (
    r"(?:is|are|was|were|has been|have been|had been|got|has got|have got|got taken"
    r"|has ended up|ended up)?\s*(?:really\s+|very\s+|quite\s+|so\s+)?"
    # "sick of school" is a complaint about school, not an illness: the word "sick" takes a
    # person in hospital only when nothing follows it. The same goes for "ill of", which nobody
    # writes, so one lookahead covers the pair.
    r"(?:in hospital|in the hospital|in a coma|on a ventilator|unwell|(?:ill|sick)(?!\s+of\b)"
    r"|poorly|dying"
    r"|struggling|getting worse|worse)"
    r"|(?:was|got|has been|had been)?\s*(?:diagnosed|taken into hospital)"
    r"|has cancer|had cancer|has had a fall|had a fall|took a fall|is terminal")

# How a count is said back when the answer is about a gap: "another 20 minutes", "one more
# session a week".
_UNIT_SAID = {"minutes": ("minute", "minutes"), "hours": ("hour", "hours"),
              "steps": ("step", "steps"), "litres": ("litre", "litres"),
              "glasses": ("glass", "glasses"), "km": ("km", "km"),
              "miles": ("mile", "miles"), "days": ("day", "days"), "weeks": ("week", "weeks"),
              "nights": ("night", "nights"), "a week": ("session a week", "sessions a week"),
              "a day": ("session a day", "sessions a day")}

# The unit families a figure is counted in, so "2 litres" and "1.5 to 2 litres" and "six to eight
# glasses" are comparable and a length against a weight is not.
_AMOUNTS = (
    # A count of times something is done is the one a "three sessions a week" answer is about, so
    # it is written so that "twice a week", "two times a week" and "three sessions a week" are the
    # same family.
    ("a week", r"(?:(?:times?|sessions?|runs?|workouts?|walks?)\s+)?(?:a|per|each)\s+week"),
    ("a day", r"(?:(?:times?|sessions?|glasses?)\s+)?(?:a|per|each)\s+day"),
    ("minutes", r"minutes?|mins?"),
    ("hours", r"hours?|hrs?"),
    ("litres", r"litres?|liters?|l\b"),
    ("glasses", r"glasses?"),
    ("steps", r"steps?"),
    ("km", r"km\b|kilometres?|kilometers?|k\b"),
    ("miles", r"miles?|mi\b"),
    ("days", r"days?"),
    ("weeks", r"weeks?"),
    ("nights", r"nights?"),
    # The figures a guideline is written in as often as litres and steps: "the limit for an
    # adult is 6g", "roughly 2,000 to 2,500 calories", "10 micrograms of vitamin d".
    ("grams", r"grams?|grammes?|g\b"),
    ("calories", r"calories|cals?\b|kilocalories|kcals?"),
    ("micrograms", r"micrograms?|microgrammes?|mcgs?|\u00b5g|ug\b"),
    ("milligrams", r"milligrams?|milligrammes?|mgs?"),
)

_AMOUNT_WORDS = {"once": 1, "twice": 2, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                 "twelve": 12}

# The \b at both ends matters: without it "his body weight a day" matched the "eight" inside
# "weight" and answered "Twice a day is under the eight a day that answer named" to someone
# feeding a dog.
# The boundary goes before the figure and after a number written as a word. A digit needs no
# trailing one, because a unit runs straight on from it: "6g of salt", "300ml", "2000".
_COUNT_WORD = r"\b(?:\d+(?:,\d{3})*(?:\.\d+)?|(?:once|twice|one|two|three|four|five|six" \
              r"|seven|eight|nine|ten|eleven|twelve)\b)"

# Two units that count the same thing: 20 minutes against "two hours", 5k against "three miles".
# Only conversions that are exact enough to say out loud are here.
_CONVERT = {("minutes", "hours"): 60.0, ("hours", "minutes"): 1 / 60.0,
            ("km", "miles"): 0.621371, ("miles", "km"): 1.609344}

_WEEKLY = "a week"

# The unit families a figure comes in, and the words the answer may say it with.
FIGURE_UNITS = {
    "week": ("week", "weeks", "fortnight", "fortnights"),
    "day": ("day", "days"),
    "month": ("month", "months"),
    "year": ("year", "years"),
    "hour": ("hour", "hours"),
    "minute": ("minute", "minutes"),
    "second": ("second", "seconds"),
    "mile": ("mile", "miles"),
    "km": ("km", "kilometre", "kilometres", "kilometer", "kilometers"),
    "kilo": ("kilo", "kilos", "kg", "kilogram", "kilograms"),
    "stone": ("stone", "stones"),
    "pound": ("pound", "pounds", "lb", "lbs"),
}

FIGURE_TIME = ("week", "day", "month", "year", "hour", "minute", "second")

# A number written with its thousands grouped ("20,000", "40,000") is one number, and it starts
# at its first digit: reading it from the comma found "000 miles" in "20,000 to 40,000 miles" and
# handed back " 000 miles." for "how many miles is that".
FIGURE_NUMBER = (r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|a|an|one|two|three|four|five"
                 r"|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty"
                 r"|sixty|ninety|hundred)")

FIGURE_QUALIFIER = (r"(?:about|around|roughly|nearly|almost|up to|at least|over|under|just|only"
                    r"|maybe|probably|another)")

LOOK_BACK_FIGURE = 3

FIGURE_ANSWER_LEN = 120

# They may have said the detail already: "i paid 200 pounds for a new bike" answers "how much did
# it cost", so the store answering "you didn't say" would be wrong about what they told us.
# People type the number as a word as often as a figure - "a film for two hours", "three books" -
# and asking "how long was it?" of a line that just said two hours is the bot not listening.
COUNT_WORD = (r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
              r"|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty"
              r"|hundred|dozen|couple|few|several|lot|lots|plenty|number)")

# A place in lower case: "i got a new job in leeds". The word after "in/to/at" has to be a name
# and not a month, a part of the day or one of the everyday phrases ("in order", "at the time"),
# or the ask-back would be dropped for the wrong reason.
PLACE_NOT = ("the|a|an|my|his|her|their|our|your|its|it|this|that|these|those|order|time|general"
             "|total|all|front|charge|public|private|fact|mind|particular|future|past|advance"
             "|june|july|may|march|april|august|september|october|november|december|january"
             "|february|monday|tuesday|wednesday|thursday|friday|saturday|sunday|home|work|bed"
             "|town|touch|least|once|twice|night|morning|evening|afternoon|weekend|month|year"
             "|between|case|some|any|no|one|two|first|last|next|same|other|else|person|people")

# Said back with the person turned round: their "where are we staying" comes back as "where are
# you staying", so the ask is about their own news and not a question of ours.
TURNED = {"we": "you", "our": "your", "my": "your", "us": "you", "me": "you",
          "im": "you are", "i": "you", "ive": "you've"}

# The nouns a possessive can name, and the fact the store keeps them as. Anything else ("my
# neighbour", "my old school") is not a thing the chat has been told the facts of.
PART_HELD = {
    "job": "job", "jobs": "job", "work": "job", "role": "job", "shift": "job", "shifts": "job",
    "hours": "job", "pay": "job", "salary": "job", "boss": "job", "colleagues": "job",
    "son": "people", "daughter": "people", "kid": "kids", "kids": "kids", "child": "kids",
    "children": "kids", "mum": "people", "dad": "people", "mother": "people",
    "father": "people", "sister": "people", "brother": "people", "partner": "people",
    "wife": "people", "husband": "people", "family": "people", "parents": "people",
    "dog": "pets", "cat": "pets", "puppy": "pets", "kitten": "pets", "pets": "pets",
    "car": "owns", "bike": "owns", "phone": "owns", "laptop": "owns", "house": "city",
    "flat": "city", "home": "city", "garden": "city", "town": "city", "area": "city",
    "name": "name", "age": "age", "budget": "budget", "diet": "diet",
}

PART_KEYS = ("job", "people", "kids", "pets", "owns", "city", "places", "name", "age",
             "budget", "diet", "allergies")

# The facts a part can be asked about: a job, a person, a pet, a thing they own, their children,
# their own name, age, budget or diet. A trip is not one of them - "im off to edinburgh" then
# "what is there to see" is a question about Edinburgh, and the answers module has the answer.
KEPT_THINGS = ("job", "people", "owns", "kids", "pets", "name", "age", "budget", "diet")

# A "no" is only said when the line names the thing it is about: "i am right" reads as a name,
# so "am i right?" must not be answered "No — you're ...". A number needs no naming word.
NAMED_BY = {
    "name": r"\bname\b|\bcalled\b",
    "age": r"\bold\b|\bage\b|\d",
    "job": r"\bjob\b|\bwork\b|\bliving\b|\bam i an?\b|\bwas i an?\b",
    "city": r"\bliv(?:e|es|ing)\b|\bhome\b|\bcity\b|\btown\b",
    "from": r"\bfrom\b|\bhometown\b|\bgrew up\b|\bborn\b",
    "allergies": r"\ballerg",
    "budget": r"\bbudget\b|\bspend\b|\bafford\b|\d",
    "diet": r"\bvegetarian\b|\bvegan\b|\bdiet\b|\beat\b|\bfood\b",
    "pets": r"\bdog\b|\bcat\b|\bpet\b|\bhamster\b|\brabbit\b|\bfish\b|\bbird\b|\bhorse\b",
}

# The facts a remembering frame can be about: the ones the store keeps as a value it can say
# back. A plan or a line said in their own words is not one of them.
RESTATED_KEYS = ("name", "age", "job", "city", "from", "diet", "budget", "allergies", "pets")

# A correction that swaps one named thing for another ("sorry, i meant porto, not lisbon")
# leaves the person with a new thing and nothing about it: the note says which one the bot goes
# with, and the answer about the new one is the reason they said it. The old value is the one the
# line before the correction carried, so the corrected sentence is that line with the old value
# swapped out - the same swap the store just made to the fact.
# The facts a swap can be about: the thing the line named (the city it is going to, the job, the
# diet) and the plan the line was kept as.
SWAPPABLE = ("city", "places", "job", "diet", "plan", "plans")

_TENS_WORDS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty",
               "ninety")

# The kinds of fact about someone else a correction can put right, and the shape of the line that
# says it back. An age is a figure and goes back in words, the way the person says it; the things
# said in words go back whole ("Peanuts it is, then - I'll keep your son off those.").
CORRECTED_AGAIN = ("{Value}, not {was} \u2014 got it.",
                   "{Value}, then \u2014 your {who} is {value} now.",
                   "Not {was} \u2014 {value}. Got it.")

CORRECTED_AGAIN_WHO = ("{Value} \u2014 got it, your {who} is {value} from now on.",
                       "{Value}, then \u2014 I have your {who} down as {value}.")

# A correction that moves a fact from one person to another: "my son is 9" and then "sorry i meant
# my daughter is 9". The store took the second line as a fact about the daughter, but the age was
# already the son's, so nothing in the reply said the fact had changed hands - and the word
# "sorry" in front of a relation reached the row on how to word an apology, which told the person
# to name what they had done wrong and say it plainly. A friend says which child is the nine year
# old; each line below names both, because that is the news in the line.
CORRECTED_WHICH_PERSON = (
    "{Value} \u2014 your {who}, not your {was_who}. Got it.",
    "Ah, it's your {who} who is {value} \u2014 I had that with your {was_who}.",
    "{Value} goes with your {who}, then, not your {was_who}. Noted.",
    "Your {who}, not your {was_who} \u2014 I've moved that over.",
)

# Names by animal. Short, easy to say and hard to mix up; nothing here is a person's name, so the
# bot is not naming the pet after anybody the person knows.
CAT_NAMES = ("Miso", "Pepper", "Juniper", "Biscuit", "Saffron", "Marmalade", "Clover", "Smudge",
             "Willow", "Pip")

DOG_NAMES = ("Finn", "Nell", "Bramble", "Otto", "Rufus", "Tilly", "Ziggy", "Juno", "Alfie",
             "Moss")

SMALL_NAMES = ("Pip", "Peanut", "Willow", "Nibbles", "Bramble", "Squeak", "Poppy", "Titch")

# What a friend adds after the names: the part of the choice that lasts.
NAME_ADVICE = (
    "Pick the one you would not mind calling across a park at night - that rules more names out "
    "than anything else.",
    "Say each one out loud first: a name you shorten anyway is the one you will end up using.",
    "Two syllables carries best, and use only the chosen one for the first fortnight, so it "
    "learns its own name quickly.",
    "The right answer is usually the one everybody in the house can spell and shout.",
)

RESUME = (
    "Back to {thing}, then. What did you want to know about it?",
    "OK, back to {thing}. Where were we?",
    "Right, {thing} again. Go on.",
    "Back to {thing} it is. I'm still here.",
    "Righto, {thing}. What's the question?",
    "Back to {thing}. I've still got what you told me about it.",
)

# What the store says when it is asked what is coming up and nothing is.
NO_PLANS_REPLY = ("You haven't told me about anything coming up yet. What's on?",
                  "Nothing so far — you haven't mentioned anything coming up. What have you got?")

# The week in the order it runs, so the day before an event can be named.
WEEK = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

TAIL_WINDOW = 40      # how much of the tail before "for it" a setting-out verb is read in

# A person named in the plural is still a person, and English changes its verb for one: "my
# children dont eat meat" is "Your children don't eat meat", never "Your children doesn't". The
# words come from the store, so this is the one place the verb is chosen.
PLURAL_PEOPLE = ("children", "people", "parents", "kids", "twins", "boys", "girls", "friends",
                 "mates", "flatmates", "housemates", "colleagues")

# What a named diet keeps off the plate, so "what cant she have" is answered with the food it
# rules out rather than with the diet's own name said again. A diet said as a missing food
# ("no meat") is left alone: the sentence the store already has says exactly that.
DIET_RULES_OUT = {
    "vegan": ("meat, fish, dairy or eggs", ""),
    "plant-based": ("meat, fish, dairy or eggs", ""),
    "plant based": ("meat, fish, dairy or eggs", ""),
    "vegetarian": ("meat or fish", ""),
    "veggie": ("meat or fish", ""),
    "veg": ("meat or fish", ""),
    "pescatarian": ("meat", " (fish is fine)"),
    # A free-from diet names the food it rules out, so the ask is answered with that food instead
    # of with the diet's own name said back: "my wife is gluten free" then "what can she eat" was
    # "Your wife is gluten-free." - true, and no help at all.
    "gluten-free": ("gluten", ""),
    "dairy-free": ("dairy", ""),
    "lactose-free": ("dairy", ""),
    "wheat-free": ("wheat", ""),
    "sugar-free": ("sugar", ""),
    "low-carb": ("carbohydrates", ""),
}

# A denial - "You haven't told me about your diet", "You haven't mentioned a budget yet" - is
# only true when the person never said it. The store reads its facts by pattern, so a line it did
# not file still says the thing ("my budget is tight this month", "i mostly eat low fat stuff"),
# and denying it tells someone they never said what they said a turn ago. Before any denial the
# lines they sent are read for the words the fact goes by, and the last one is quoted instead.
#
# Two rules keep the quote honest, because a wrong quote is worse than the denial. The words are
# whole words: "fat" is in "father" and "pay" is in "paying", and only the second is about money.
# And every word here is the fact itself, not something near it - a spend is not a budget, a flat
# tyre is not a flat, a care home is not their home - so the line quoted is one a person would
# agree says the thing.
DENIAL_WORDS = {
    "diet": ("diet", "diets", "dieting", "eat", "eats", "eating", "food", "meal", "meals",
             "vegan", "vegetarian", "veggie", "pescatarian", "keto", "paleo"),
    "budget": ("budget", "budgets", "afford", "affording", "save", "saving", "savings", "wage",
               "wages", "salary", "income", "earn", "earns", "earning", "cash"),
    # "where do i live" is the one ask with no word list at all: "i have a flat tyre", "i work in
    # a care home" and "i live in a house with a big garden" all carry the words and none of them
    # says where they live, which is the thing the denial is about. A line the fact reader files
    # is in the store already, so nothing is lost by staying quiet here.
    "allergy": ("intolerant", "intolerance", "react", "reaction", "epipen", "coeliac", "celiac",
                "anaphylaxis", "anaphylactic"),
    "job": ("job", "jobs", "work", "works", "working", "worked", "role", "career", "employer",
            "employed", "office", "shift", "shifts", "boss", "manager", "colleagues"),
}

# The front of the fact's own word rather than the whole of it: "allergic" and "allergy" are one
# word to the person saying it, and no other word starts with them.
DENIAL_STEMS = {"allergy": ("allerg",)}

# A word for more than one person, and the relations in the store that belong to each. The store
# keeps people one by one ("my son is called jack and my daughter is called emma"), so a plural
# ask reached nothing: "what are my children called" was answered with a search for what to name
# a child, two turns after the chat had been told both names.
CHILD_RELATIONS = ("son", "daughter", "child", "kid", "baby", "twin", "boy", "girl",
                   "stepson", "stepdaughter", "teenager", "lad", "lass")

GROUP_OF = {
    "children": CHILD_RELATIONS, "childs": CHILD_RELATIONS, "kids": CHILD_RELATIONS,
    "parents": ("mum", "dad", "parent", "stepmum", "stepdad"),
    "siblings": ("brother", "sister", "half-brother", "half-sister"),
    "brothers": ("brother",), "sisters": ("sister",),
    "grandparents": ("grandma", "grandad", "grandparent"),
    "grandchildren": ("grandson", "granddaughter", "grandchild"),
    "aunts": ("aunt",), "uncles": ("uncle",), "cousins": ("cousin",),
}

# The same person under the word people use for them: "my mother" and "my mum" are one relation,
# and the store files the word the line used, so an ask that says one has to find the other.
RELATION_ALIKE = {"mother": "mum", "mom": "mum", "mam": "mum", "mummy": "mum",
                  "father": "dad", "daddy": "dad",
                  "nana": "grandma", "nan": "grandma", "granny": "grandma",
                  "gran": "grandma",
                  "grandmother": "grandma", "grandpa": "grandad", "grandfather": "grandad",
                  "auntie": "aunt", "kid": "child", "childs": "child", "kids": "child"}

# A month only says a date with a word in front of it or a day of the month beside it: "i may go
# to bristol" is a plan with no date in it, and "spain in july" is a plan with one.
# The months in the order they run, so a month a plan names can be counted from.
MONTH_ORDER = ("january", "february", "march", "april", "may", "june", "july", "august",
               "september", "october", "november", "december")

# Whether they have any of a kind of person at all: "do i have any brothers or sisters". The
# store knew there was a sister and answered with a search for what brothers are, which is the
# one thing a chat that is about their own family cannot be answered with. The words are the
# plural relations above, and the same ones singular, because "do i have a brother" is the
# same ask.
HAVE_ANY_WORDS = ("brothers", "sisters", "siblings", "children", "kids", "childs", "parents",
                  "grandchildren", "grandparents", "aunts", "uncles", "cousins", "family",
                  "brother", "sister", "child", "kid", "sons", "daughters", "mums", "dads",
                  "parents", "son", "daughter", "mum", "dad", "parent", "grandson",
                  "granddaughter", "aunt", "uncle", "cousin")

# The word an answer about one relation uses for that person.
HER_WORD = {"sister": "her", "daughter": "her", "mum": "her", "granddaughter": "her",
            "aunt": "her", "brother": "him", "son": "him", "dad": "him",
            "grandson": "him", "uncle": "him"}

# What a diet rules out, in the food words a person uses. The cooking tables cannot carry it:
# cooking.NO_MEAT_DIET leaves fish open on purpose, because plenty of people who say "i don't eat
# meat" do eat fish (see the note there). A diet word is the one place the line is settled - a
# vegetarian does not eat fish either, and a pescatarian is the one who does. "im vegetarian" and
# "what cant i eat" was answered "You're vegetarian.", which is the label said back rather than
# the food it rules out.
DIET_FOOD = {"vegetarian": ("meat", "fish"), "veggie": ("meat", "fish"),
             "vego": ("meat", "fish"), "pescatarian": ("meat",),
             "pescetarian": ("meat",),
             "vegan": ("meat", "fish", "dairy", "eggs"),
             "plant based": ("meat", "fish", "dairy", "eggs"),
             "plantbased": ("meat", "fish", "dairy", "eggs")}

# A group word names several people the chat has been told about, in one word: "what are my
# children called" is "what are my son and daughter called", and the store holds both names. The
# ask was read as a relation the store does not know and fell to the search hedge one line after
# it had said "Noted: your daughter emma is 4 and your son jack is 6". Each group is the
# relations it covers; a word that is not here ("what are my cousins called") is still the
# unknown relation it was.
PERSON_GROUP = {
    "children": CHILD_RELATIONS, "childs": CHILD_RELATIONS, "kids": CHILD_RELATIONS,
    "brood": CHILD_RELATIONS,
    "boys": ("son", "boy", "stepson"),
    "girls": ("daughter", "girl", "stepdaughter"),
    "parents": ("mum", "mother", "dad", "father", "stepmum", "stepdad", "parent"),
    "siblings": ("brother", "sister", "stepbrother", "stepsister"),
    "grandchildren": ("grandson", "granddaughter", "grandchild"),
    "grandkids": ("grandson", "granddaughter", "grandchild"),
    "grandparents": ("nan", "nana", "gran", "granny", "grandma", "grandad", "grandpa"),
    "twins": ("twins", "son", "daughter"),
}

# The words that are already several people: an entry filed as "kids" is more than one child.
PLURAL_PEOPLE = ("children", "childs", "kids", "twins", "babies")

# The verb says which thing it is: "what do i drive" names no thing of its own.
OWNED_BY_THE_VERB = (("drive", "car"), ("ride", "bike"))

# How a fact about another person is said back. Two wordings each, so the same fact told twice
# in one chat does not read as a machine reading a list.
PREGNANT_SAY = (
    "Noted — your {who} is pregnant, so nothing alcoholic for her. Say if you want a hand with "
    "what to cook or what to plan.",
    "Your {who} being pregnant is worth knowing — I'll keep drink out of anything I suggest.",
)

# The same fact with the length they gave: "my wife is 8 weeks pregnant" is said back with the
# weeks in it, because that is the part of the line the next turn is about.
PREGNANT_WEEKS_SAY = (
    "Noted — your {who} is {weeks} weeks pregnant, so nothing alcoholic for her. Say if you want "
    "a hand with what to cook or what to plan.",
    "Your {who} at {weeks} weeks — I'll keep drink out of anything I suggest, and say if a meal "
    "plan would help.",
)

# The person's own pregnancy, said back to them. The length is the half that dates it, so it is
# named; the drink is the one thing every meal and plan for the next months has to leave out.
PREGNANT_OWN_SAY = (
    "Lovely news — {weeks} weeks. Nothing alcoholic in anything I suggest, and say if you want a "
    "hand with meals or with what to plan.",
    "That's lovely news — {weeks} weeks in, and I'll keep the drink out of anything I suggest. "
    "Say the word if a meal plan would help.",
)

LIMIT_SAY = (
    "Noted, your {who} doesn't drink — I'll not put wine in the plan.",
    "Good to know your {who} isn't drinking; I'll leave it out of what I suggest.",
)

# Breastfeeding is not a pregnancy and is not said back as one: the woman is feeding a baby that
# has arrived, and "your wife being pregnant" is a fact the store was never told.
FEEDING_SAY = (
    "Noted — your {who} is breastfeeding, so I'll keep the drink out of what I suggest and keep the "
    "ideas to food.",
    "Good to know your {who} is breastfeeding; I'll leave anything with drink in it off the list.",
)

STATE_WAS_SAY = (
    "Noted - I'll take that as something that was, not something now. Tell me what you'd like a "
    "hand with and I'll pick it up from there.",
    "Thanks for telling me. I'll keep that in the past rather than reading it as news now.",
)

# A pet's age is a fact of theirs, the same way a relation's is: "how old is my dog", "how old
# are the cats". "how old is a dog" is a question about the world and is left alone, so the ask
# has to say whose animal it is.
PET_WORDS = r"dog|puppy|cat|kitten|rabbit|hamster|parrot|goldfish|fish|horse|pet"

PRONOUN_PEOPLE = ("she", "he", "they", "him", "her", "them")

# A line that gives the person's own fact away instead is left to the readers that know how to
# keep it: "my wife is pregnant too" is news about the wife, not the allergy said again.
SAME_FACT_THEIR_OWN = ("allergies", "diet", "condition", "age", "job", "name", "budget", "pets",
                       "places", "plan")

# What a condition kept for somebody else rules out of their food, so "what can he eat" and "can
# he have cheese" are answered with the food rather than with the condition's name said again.
# Coeliac disease and a gluten intolerance are the same plate and a lactose intolerance is dairy;
# nothing else on this list names a single food, so nothing else is claimed about a plate.
CONDITION_RULES_OUT = {
    "coeliac": "gluten",
    "celiac": "gluten",
    "gluten intolerant": "gluten",
    "lactose intolerant": "dairy",
}

# A condition that rules out no food at all still changes what is on the plate, and the honest
# answer says only that much: a diabetic is watching sugar and white carbs, not giving them up.
CONDITION_KEEPS_DOWN = {
    "diabetic": "sugar and white carbs",
    "high cholesterol": "saturated fat and fried food",
    "high blood pressure": "salt",
}

# A make or a trim said in its proper form is not a title case: "a BMW", "a Golf GTI".
CAR_CAPS = {"bmw": "BMW", "vw": "VW", "mg": "MG", "gti": "GTI", "tdi": "TDI", "mpv": "MPV"}

# A count as a word. It is not called NUMBER_WORD: the pattern of the same name above reads a
# number the person typed, and a module-level name that shadows it makes every line through the
# correction path above raise AttributeError.
NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
                9: "nine", 10: "ten"}

_SUBJECT_KEYS = {"pet": "pets", "allergy": "allergies", "budget": "budget", "job": "job",
                 "name": "name", "city": "city", "limit": "limits"}

PLURAL_PETS = {"cat": "cats", "dog": "dogs", "puppy": "puppies", "kitten": "kittens",
               "rabbit": "rabbits", "bunny": "bunnies", "hamster": "hamsters", "fish": "fish",
               "bird": "birds", "horse": "horses", "pony": "ponies", "parrot": "parrots",
               "mouse": "mice", "guinea pig": "guinea pigs", "tortoise": "tortoises"}

COUNT_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
               9: "nine", 10: "ten"}

# An answer long enough that it cannot be read a second time: past this many words the store says
# what it said in its first sentence rather than expecting anyone to re-read the whole thing.
A_SHORT_ANSWER = 14

# The fact a recall key stands for, so a callback can tell "the store keeps this" from "the
# chat never mentioned it".
KEY_SLOT = {"name": "name", "job": "job", "city": "city", "from": "from", "diet": "diet",
            "budget": "budget", "allergy": "allergies", "allergies": "allergies", "age": "age",
            "pet": "pet", "pets": "pets", "limit": "allergies", "height": "height"}

CONCEPTS = {}

# The possessive written without its apostrophe, which is how most people type it: "my mums
# birthday", "my dads car", "my sisters wedding". Without the bare "s" the word never had a
# boundary to finish on, so a line about the person was not read as one and the store answered
# "you haven't told me anything about your mum" about a line it was holding.
# A determiner after it is where an idiom lives, not a person: "my mums the word" owns nothing.
POSSESSIVE = r"(?:(?:'s|s'|s)(?!\s+(?:the|a|an)\b))?"

QUOTE_LEADS = ("You said: ", "Your own words were: ", "This is what you told me: ",
               "You put it like this: ")

ASKED_LEADS = ("You asked: ", "Your question was: ", "What you said was a question: ")

# "There is nothing here yet" is said in more than one way: the same sentence twice running is
# the one thing STYLE.md rules out, and this line is the answer to a question people ask twice.
NOTHING_STARTED = (
    "We haven't really started yet — you go first.",
    "Nothing yet: there's nothing of yours to look back on. Where would you like to begin?",
    "So far it's just been hellos, so there's nothing to go back over. What's on your mind?",
    "We're still at the beginning — you haven't given me anything to hold onto yet.",
)

# A line that points back at what was said before, when there is nothing before it: "same as
# before", "the usual", "and the other one", "the thing you said". The small-talk pools answered
# these with a receipt of a line nobody gave ("Thanks for telling me — I'm here if you want to dig
# into any of that"), which thanks a person for a pointer and answers nothing. What is true is
# that there is no before to go on, so that is the line, with the thing itself asked for.
POINTS_BACK_NOTHING = (
    "There's nothing before this chat for that to be, so I've no 'before' to go on. What is it "
    "you want?",
    "We've only just started, so there's nothing before this to point at — say the thing itself "
    "and I'll answer it.",
    "Nothing said yet for that to be. Tell me the thing in a word or two and I'll take it from "
    "there.",
    # A reader said the line this replaces ("That points back at something I haven't got") read
    # like a machine reporting an error. The same thing in a person's words, and a warmer one for
    # "the usual", which is the most conversational of the lines that get this pool.
    "You haven't said the thing itself yet — what is it?",
    "‘The usual’ is what you'd say to someone who already knows. I don't yet — what is it?",
)

# An ask whose only subject is a pointing word, as the first thing said in a chat: "how do i do
# it", "how long will it take", "do that again". There is nothing for the word to be, and the
# answer says so and asks for the thing in the fewest words that will name it.
POINTING_WORD_NOTHING = (
    "There's nothing before this chat for that to be. What are we working on?",
    "I haven't got anything for that to point at yet — give me the thing in a few words and "
    "I'll answer for it.",
    "That's the first thing you've said, so I've nothing in hand for it to mean. What is it?",
    "Nothing said yet for that to be: tell me the thing itself in a word or two and I'll take it "
    "from there.",
)

# An ask about what they said or were worried about, as the first thing in a chat: "what was it i
# was worried about". There is nothing to recall, and the honest answer says so instead of taking
# the line as a worry of theirs and giving advice about worrying.
WHAT_I_SAID_NOTHING = (
    "Nothing yet — you haven't told me anything, so there's nothing for that to be. What was on "
    "your mind?",
    "You haven't said yet, so I'd be making it up. Tell me what it was and I'll keep it.",
)

# A clause that says how to go on with a change rather than in full: the advice's own limit, and
# the words it opens with. Read from the answer, never written here, so the limit stays the one
# the bot already gave.
RESTRICT_OPENS = (
    "cut", "reduce", "shorten", "lower", "drop", "halve", "taper", "ease", "ease off",
    "keep it", "keep to", "keep the", "keep your", "go easy", "take it", "skip", "swap",
    "switch", "replace", "rest", "ice", "warm up", "stretch", "cut back", "fewer", "less",
    "lighter", "gentler", "shorter", "slower",
)

# How the store hands the call back. All three name the limit before they say it, so the line
# reads as an answer to the question and not as the same paragraph a second time.
CALL_LEADS = (
    "Yes, but {limit}. And {condition}.",
    "Keep going, but {limit}. And {condition}.",
    "Yes — {limit}. And {condition}.",
    "Go on, but {limit}. And {condition}.",
)

# The lengths a budget can be said in. "half an hour" and "an hour" are not a count and a unit, so
# they are read on their own; everything else is a count in front of a unit.
LENGTH = (r"(?:half\s+an\s+hour|an\s+hour|"
          r"(?:\d+|an?|a\s+couple\s+of|a\s+few|"
          r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
          r"thirty|forty|forty-five|fifty|sixty|ninety)\s*"
          r"(?:minutes?|mins?|hours?|hrs?))")

WORD_NUMBERS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
                "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
                "forty-five": 45, "fifty": 50, "sixty": 60, "ninety": 90}

UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600}

# How the store hands the answer back, cut to the room there is. The move comes first, because it
# is the answer to the question behind the budget, and the budget is tied in after it - said first
# it made the whole reply a remark about the clock. There are two shapes and not one: a budget that
# leaves some of the answer out is a limit ("20 minutes covers that"), and one bigger than every
# move in the answer is not ("two hours is more than enough for all of that").
BUDGET_FITS = (
    "{part}. {budget} covers that.",
    "{part}. That fits inside {budget}.",
    "{part}. {budget} is enough for that.",
)

# A budget that leaves nothing out is not a limit on the answer, so these say only what is true of
# every answer they are said about: each step of it fits. "5 minutes is more than enough for that"
# was said of a steak that takes longer than five minutes in all, one step at a time.
BUDGET_MORE = (
    "{part}. {budget} is more than enough for the steps of it.",
    "{part}. That is more than enough time for the steps of it, one at a time.",
    "{part}. Nothing in it needs longer than {budget}, so there is more than enough there.",
)
# Any figure at all, with a unit or without: "tuna pasta in 15, macaroni cheese in 25" has three,
# and only the last carries "minutes", so a count of lengths said nothing about the list it is.
ANY_FIGURE = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty"
    r"|thirty|forty|fifty|sixty|ninety|hundred)\b", re.I)

# A budget too small for any of the answer keeps the answer: it only takes longer than they have.
BUDGET_TIGHT = (
    "{part}. That wants longer than {budget}, but it is still the answer.",
    "{part}. It takes longer than {budget}, but this is still it.",
)

# The store closes the subject, never a thread the safety module is holding: "i don't want to talk
# about it" inside a crisis is the person still in danger, and the pools that carry that thread
# say so. Words that only appear in those answers, so a card about a burn or a fall is left alone.
HELD_THREAD = ("crisis", "suicide", "overdose", "call an ambulance", "999 now", "111 now",
               "hospital now", "call someone with you")

GRIEF_WORDS = ("died", "passed away", "funeral", "sorry for your loss", "cancer", "hospice",
               "in hospital", "grief", "miss him", "miss her", "miss them")

CLOSE_PLAIN = (
    "Fair enough — we'll leave it there. I'm here if you want to come back to it.",
    "Alright, dropped. Say the word if you pick it up again later.",
    "That's fine by me. I'm not going anywhere if you change your mind.",
)

CLOSE_HEAVY = (
    "Of course. You don't have to talk about it with me — I'm here either way.",
    "That's alright. It can wait, and so can I.",
    "Understood. Nothing more from me on it unless you bring it up.",
)

CHANGE_PLAIN = (
    "Yes. Food, films, or something to do at the weekend — pick one and I'll run with it.",
    "Sure. Give me a subject — cooking, telly, plans — and I'll take it from there.",
    "Of course. Tell me what you'd rather chew on: dinner, a film, the weekend?",
)

CHANGE_HEAVY = (
    "Yes, gladly. Anything you'd rather think about — a film, dinner, the weekend?",
    "Of course. We can leave that where it is — something light instead, like dinner or a film?",
    "Happily. Something light, then — a film, dinner, or the weekend?",
)

# The reply when there is nothing to name: the person asked before saying anything, or said it so
# long ago that reading it back would be a guess about which line they mean.
CHECK_NOTHING_SAID = (
    "Nothing came through before that one — say it again and I'll take it from there.",
    "I don't have a line from you before this one. Go on, and I'll pick it up.",
)

# Said back when the thing in hand is not a fact but how they feel, where reading their own words
# back ("you are so sad") is the machine talking.
CHECK_A_FEELING = (
    "Yes — I've got it.",
    "I heard you, and I'm still here.",
    "Yes, that came through.",
)

CHECK_A_QUESTION = (
    "Yes — I've got the question.",
    "Yes, I have it — anything else on it?",
    "Got it, I have your question.",
)

CHECK_PLAIN = (
    "Yes — {said}.",
    "Got it — {said}.",
    "Yes, that's what I have: {said}.",
)

# The times the person's own day runs on. "i get up at seven" was read as nothing to keep: the
# next line, "what time do i get up", got a lesson on sleep, and "what time do i start work" got
# "No live opening times here" - the shop card, for a question about their own morning. A
# routine time is a fact like any other, so it is filed when it is said and said back when it is
# asked, with no advice in between.
#
# The clock as a person writes it: "seven", "half six", "quarter past six", "six thirty",
# "6:30", "7pm", and the way the minutes get typed in chat-speak: "5 30", "6 45", "7 15". Kept as
# they said it, because "half six" said back as "6:30" is the bot doing arithmetic at somebody.
# The space form is not decoration: the words "six thirty" were read and the figures "6 30" were
# not, so `i get up at 5 30 for work` filed half five and said back "You're up at 5." - the
# person's own morning quoted back with the minutes gone - and `my shift starts at 7 15` became
# "You start work at 7." A figure pair with a space was read as the hour and the minutes thrown
# away, because the match stopped at the word boundary after the first figure.
CLOCK_SAID = (r"(?:half (?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
              r"|quarter (?:past|to) (?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
              r"|(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
              r"(?: (?:thirty|fifteen|forty-five))?"
              r"|(?:1[0-2]|0?[1-9])(?:[:. ][0-5]\d)?\s*(?:am|pm)?"
              r"|noon|midday|midnight)")

# "i get up at seven", "i usually get up around seven", "im up at half six", "we eat about six".
# The subject is the person, so a clock on somebody else's morning ("my son wakes at five") is
# left to the person reader.
ROUTINE_SUBJECT = r"(?:i|we|im|i'm|i am|we're|we are)"

# What a time is the time of, in the words the store says back.
ROUTINE_SAY_BACK = {"get up": "You're up at {at}.",
                    "go to bed": "You go to bed at {at}.",
                    "start work": "You start work at {at}.",
                    "finish work": "You finish work at {at}.",
                    "leave": "You leave at {at}.",
                    "get home": "You get home at {at}."}
