"""The reply to a line that is nothing but a number.

People plan out loud in numbers. "20 mins", "45 a month", "its about 5 miles", "40 minutes each
way", "20 pounds a week". The number is the constraint the whole plan turns on, and it is usually
the answer to the question the bot asked one turn earlier: "what can you spend?", "how long have
you got?", "how far is it?".

What the bot says to such a line today is nothing. It is not a question, so no module answers it;
it carries no feeling, so no pool fits; the memory store can file it ("Got it - you have 40
pounds left for food this week") or it lands in one of the stock lines, and both are the failure
STYLE.md names. Measured on main, one process a line:

    its 45 a month              -> I'm listening - say more if it helps.
    20 mins                     -> Got it. Is there anything you'd like a hand with?
    its about 5 miles           -> I'm listening - say more if it helps.
    forty minutes each way      -> Thanks for telling me - I'm here if you want to dig in.
    we have 40 pounds left ...  -> Got it - you have 40 pounds left for food this week.

A number on its own is half of a sum, and the sum is the reply. Three sums, all of them
arithmetic the bot can do without knowing anything:

- a rate across time: "45 a month" is 540 a year, "20 a week" is 87 a month. The yearly figure is
  what a person actually weighs a thing against, and nobody does that sum in their head.
- a habit across time: "40 minutes each way" is 1 hour 20 a day and 6 hours 40 a week. The cost of
  a commute is invisible until it is added up.
- a distance as a time: 5 miles is about 100 minutes walking and 12 in the car, and which of those
  matters depends on whether they have the car.

Where the number has no second number to work with ("20 mins" of what?), the reply is the same
arithmetic one step cheaper: the shortest version rather than the best one, one thing done
properly and not two done badly. That is what a friend says when they hear "I have twenty
minutes".

The read is deliberately narrow. The number has to be the whole line, wrapped in the lead-ins
people wrap numbers in ("its", "about", "only", "just", "i have", "and") and followed only by the
words that say what the number is about ("a month", "each way", "on the bus", "left", "now"). A
line with a subject of its own - "i have 2000 saved and no idea what to do with it" - is not a
bare number and keeps the reply it has today. A number that is not time, distance or money is
left alone: "95 kilos" is a body, and the health answers are not this file's to guess at.
"""
import re

from ..memory import last_bot
from . import pick

# A currency mark sits on the number itself ("£250"), so it is read with the number rather than
# stripped as a lead-in.
CURRENCY = ("£", "$", "\u20ac")

# The lead-ins a bare number arrives wrapped in. Every one of them says only "the number is
# coming", so dropping them leaves the number at the front of the line. "i have" and "i've got"
# are how people report a budget; "and" is how the second half of a plan often starts.
LEAD = frozenset((
    "its", "it's", "thats", "that's", "the", "about", "around", "roughly", "probably", "maybe",
    "only", "just", "like", "so", "and", "but", "plus", "well", "currently", "still", "now",
    "i", "have", "we", "got", "ive", "i've", "we've", "weve", "there", "is", "there's", "theres",
    "it", "of", "us", "them", "both", "looks", "works", "out", "at", "keeps", "costs", "cost",
    "pays", "paid", "uses", "takes", "spend", "spent", "save", "saved", "earn", "earns", "makes",
    "make", "means", "that", "this", "they", "he", "she", "my", "our", "his", "her", "was",
    "were", "will", "would", "be", "a", "an", "half", "for", "on", "over", "under", "being",
    # "i weigh 90 kilos", "the dog weighs 30 kilos": the verb is how a weight is said out loud,
    # and without it the figure was left to the caller and the line was echoed back.
    "weigh", "weighs", "weighed", "weighing",
    # A wage is said with its verb in the lead: "i bring home 2100 a month", "i take home 1800".
    # The verb is what says the number is what they are paid, so it is read here as well as in
    # `INCOME` below - without it the line was a receipt and the sum was never done.
    "bring", "brings", "bringing", "brought", "take", "takes", "taking", "took", "home",
    "clears", "net", "nett",
    # Money set aside is a rate too: "i put 300 a month away, is that a lot" was read as a
    # question about the strain of saving and answered "when it's like that, everything else can
    # wait". "save" was here and "put" was not.
    "put", "puts", "putting",
))

# The units, and what each family is. Time is kept in minutes, distance in miles, money in whole
# units of whatever they are counting; the reply works in those and quotes the number back in the
# unit the person used.
UNITS = {
    "minute": ("time", 1.0), "minutes": ("time", 1.0), "min": ("time", 1.0),
    "mins": ("time", 1.0), "hour": ("time", 60.0), "hours": ("time", 60.0),
    "hr": ("time", 60.0), "hrs": ("time", 60.0),
    "day": ("span", 1.0), "days": ("span", 1.0),
    "week": ("span", 7.0), "weeks": ("span", 7.0),
    "month": ("span", 30.0), "months": ("span", 30.0),
    "year": ("span", 365.0), "years": ("span", 365.0),
    "mile": ("distance", 1.0), "miles": ("distance", 1.0),
    "km": ("distance", 0.6214), "kilometre": ("distance", 0.6214),
    "kilometres": ("distance", 0.6214), "kilometers": ("distance", 0.6214),
    "pound": ("money", 1.0), "pounds": ("money", 1.0), "quid": ("money", 1.0),
    "euro": ("money", 1.0), "euros": ("money", 1.0), "dollar": ("money", 1.0),
    "dollars": ("money", 1.0), "grand": ("money", 1000.0), "k": ("money", 1000.0),
    "metre": ("size", 1.0), "metres": ("size", 1.0), "meter": ("size", 1.0),
    "meters": ("size", 1.0), "foot": ("size", 0.3048), "feet": ("size", 0.3048),
    "inch": ("size", 0.0254), "inches": ("size", 0.0254), "cm": ("size", 0.01),
    # Weight, in kilos. "pound" and "pounds" stay money: a bare "8 pounds" is a price far more
    # often than a baby, and the family is chosen by the words people use for weight alone.
    "stone": ("weight", 6.35029), "stones": ("weight", 6.35029),
    "kilo": ("weight", 1.0), "kilos": ("weight", 1.0), "kilogram": ("weight", 1.0),
    "kilograms": ("weight", 1.0), "kg": ("weight", 1.0), "kgs": ("weight", 1.0),
    "lb": ("weight", 0.4536), "lbs": ("weight", 0.4536),
}
# The words people count in when they are not typing digits. "a" and "an" are one, "half" is a
# half, and "a couple" and "a few" are the two and three people mean by them.
NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000, "dozen": 12, "couple": 2,
    "few": 3, "half": 0.5, "a": 1, "an": 1, "several": 4,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
# How a period is said after the number. "45 a month" and "45 per month" are the same line, and
# which period it is changes the sum completely: a year is twelve months and fifty-two weeks.
PERIODS = (
    ("a month", "month"), ("per month", "month"), ("each month", "month"), ("monthly", "month"),
    ("a week", "week"), ("per week", "week"), ("each week", "week"), ("weekly", "week"),
    ("a year", "year"), ("per year", "year"), ("each year", "year"), ("yearly", "year"),
    ("a day", "day"), ("per day", "day"), ("each day", "day"), ("daily", "day"),
    ("a fortnight", "fortnight"), ("per fortnight", "fortnight"),
)
# "i've got about twenty minutes a day for it": what comes after the number can be a pronoun
# pointing back at what the bot was already asked, which names no new subject and leaves the number
# the whole of the line. Only a preposition and a pronoun together count - a preposition with a
# noun after it ("20 minutes for the roast") is a new subject and is still refused.
POINTING_BACK = frozenset(("for", "on", "about", "of", "at", "with", "in", "into", "to",
                           "towards", "toward", "from"))
A_PRONOUN = frozenset(("it", "that", "this", "them", "those", "these", "him", "her",
                       "everything", "anything", "something"))
# The speaker's own doubt at the end of the line, which is about the figure and not about what it
# is for. "at least" and "at most" are deliberately absent: they change the figure.
HEDGES = frozenset(("think", "thought", "reckon", "guess", "suppose", "believe", "hope", "say",
                    "imagine", "assume"))
# What the number is about, when it is not the period: a trip is measured each way, and "on the
# bus" says the number is travel rather than a task.
TRIP = re.compile(r"\b(each\s+way|each-way|one\s+way|round\s+trip|there\s+and\s+back|"
                  r"on\s+the\s+(?:bus|train|tube|tram|bike|bicycle)|in\s+the\s+car|"
                  r"by\s+(?:car|bus|train|bike)|commut\w*)\b")
PER_DAY = re.compile(r"\b(a\s+day|per\s+day|each\s+day|every\s+day|a\s+weekday)\b")
# The only words allowed after the number and its unit. A tail word outside this list means the
# line said something else as well, and a line that said something else is not a bare number.
TAIL = frozenset((
    "each", "way", "one", "round", "trip", "there", "and", "back", "a", "an", "per", "every",
    "day", "days", "week", "weeks", "month", "months", "year", "years", "fortnight", "hour",
    "hours", "minute", "minutes", "weekday", "left", "now", "though", "today", "already", "more",
    "total", "altogether", "on", "in", "the", "bus", "train", "tube", "tram", "bike", "bicycle",
    "car", "to", "work", "at", "moment", "right", "so", "far", "max", "maximum", "ish", "or",
    "about", "around", "extra", "over", "under", "spare", "saved", "saving", "savings",
    "coming", "out", "roughly", "odd", "monthly", "weekly", "yearly", "daily", "currently",
    # "we get 2000 a month between us": the household said after the period rather than before it.
    "between",
    "probably", "maybe", "only", "just", "like", "well", "still", ":",
    # A number with nowhere else to go: "15 hours a week is all i have", "200 a month to spend".
    "is", "all", "what", "have", "has", "to", "play", "with", "spend", "by", "of", "it", "that",
    "i", "we", "they", "you", "off", "away", "wide", "long", "high", "tall", "deep", "square",
    "weeknight", "weeknights", "weekday", "weekdays", "morning", "mornings", "evening",
    "evenings", "night", "nights", "shift", "shifts", "tops", "plus", "minus", "if", "when",
))

# The judgement asked on the same line as the figure it is about ("its 45 a month, is that a lot",
# "the cleaner is 40 a week, is that fair"). It is the same question as the bare rate's caller asks
# one line later, so it is taken off the tail and the rate is read as the rate.
DOUBT_ON_THE_FIGURE = re.compile(
    # up to three words between the rate and the judgement ("300 a month away, is that a lot",
    # "12 a month for spotify, is that normal"), then the judgement itself, which has to be about
    # the figure ("is that a lot") or name the money words on its own ("too much", "too dear").
    r"^(?:[a-z',\u2019]+\s+){0,3}(?:is|isnt|isn'?t|was|wasnt|wasn'?t|too|thats|that'?s)\b\s*"
    r"(?:that|this|it|they)?\s*(?:a\s+lot|too\s+much|too\s+dear|expensive|cheap|dear|pricey|"
    r"steep|normal|about\s+right|fair|reasonable|good\s+value|worth\s+it|okay?)\b", re.I)

# Money set aside is a rate like any other, and the sum it comes to is the same arithmetic. The
# questions around it are not: "would you pay 3,600 up front for the same thing" is about buying
# something, and to somebody putting 300 a month away it is nonsense. The saver gets the year and
# a question about the saving.
SAVINGS_AFTER_A_RATE = re.compile(
    r"\b(?:savings?|save|saves|saving|saved)\b"
    r"|\b(?:put|puts|putting|set|setting|pay|paying)\b[^.!?]{0,14}\b(?:away|aside|by|in|into)\b")
SAVINGS = (
    "{q} {period} is {year} a year. That is the figure to plan with, not the weekly one.",
    "{q} {period} is {year} a year. Is it steady, or does it move with the month?",
    "{q} {period} is {year} a year - the yearly figure is the one that adds up to something.",
)

# A rate across time. The sum is the point: a month of something is small and a year of it is not,
# and the yearly figure is the one that decides.
MONEY_MONTH = (
    "{q} a month is {year} a year. Put as a year it is easier to weigh against a one-off cost.",
    "{q} a month is {year} a year - the number that matters if it runs for a while.",
    "{q} a month is {year} a year. Would you pay {year} up front for the same thing?",
    "{q} a month is {year} a year, which is the figure to hold against the yearly price.",
)
MONEY_WEEK = (
    "{q} a week is {month} a month, about {year} a year. Weekly adds up faster than it feels.",
    "{q} a week is {month} a month and {year} a year. Is that steady or a bad patch?",
    "{q} a week - that is {year} a year, or {month} a month. Which one is it really?",
)
MONEY_YEAR = (
    "{q} a year is {month} a month, about {week} a week. That is how it lands.",
    "Put as a month, {q} a year is {month} - and a month is the number people plan on.",
    "{q} a year is {month} a month. Is the money coming in monthly or in lumps?",
)
MONEY_DAY = (
    "{q} a day is {month} a month. It is the small daily ones that get away from people.",
    "{q} a day is {year} a year. Would you notice it going out once a year?",
)
# A sum that arrives rather than one that goes out. "i earn about 1800 a month" is not a price to
# be weighed up: "is that 21,600 a year - would you pay 21,600 up front for the same thing?" is a
# question nobody can answer about their own wage. The year figure is still the one that matters,
# because a wage is compared job to job, so it is said and then left with a question that fits.
INCOME_MONTH = (
    "{q} a month is {year} a year. Is that what you were expecting, or are you working out where "
    "it goes?",
    "{q} a month is {year} a year before anything comes off it. What are you weighing it against?",
    "{q} a month comes to {year} a year, which is the figure to compare one job with another.",
)
INCOME_WEEK = (
    "{q} a week is {month} a month, about {year} a year. Is the work steady or up and down?",
    "{q} a week is {year} a year - that is what it comes to over the good and the quiet weeks.",
)
INCOME_YEAR = (
    "{q} a year is {month} a month, about {week} a week. Is that what it was before, or a change?",
    "{q} a year is {month} a month. Put as a month it is easier to see where it goes.",
)
INCOME_PLAIN = (
    "{q} - is that what you take home, or before anything comes off it?",
    "{q}. Does that have to cover everything, or is some of it spoken for already?",
)
# The words that say the money is coming in rather than going out. "paid" on its own does not: "i
# paid 60 for it" is a price, and only "i get paid" is a wage.
INCOME = re.compile(
    r"\b(?:earn(?:s|ed|ing)?|salary|salaries|wages?|income|pension|take[- ]home|"
    r"get(?:s|ting)? paid|paid (?:me|us)|pays? me|my pay|a pay ?rise|pay ?rise|"
    # "i bring home 2100 a month" is the same statement as "i earn 2100 a month" and it is how a
    # wage is said in a household: without the verb here the line was a receipt and nothing else.
    r"bring(?:s|ing)? (?:it )?home|brought (?:it )?home)\b")
# A sum with no period needs no arithmetic, only the question that turns it into a plan.
MONEY_PLAIN = (
    "{q} - is that the whole budget or what is left of a bigger one?",
    "{q} goes further as a plan than as a number. What does it need to cover?",
    "{q}. What does it have to stretch to?",
)
# A duration with nothing else attached: what fits inside it.
TIME_BUDGET = (
    "{q} is enough for one thing done properly and not two done badly.",
    "In {q} take the shortest version of it rather than the best one. What is it for?",
    "{q} goes faster than it looks, so decide before you start rather than halfway through.",
    "{q} is tight - one thing only. What are you fitting into it?",
    "{q}: get everything out before the clock starts and the time is all work, not looking.",
)
# A journey: the cost of it over a week, which is the part people never add up.
TIME_TRIP = (
    "{q} each way is {day} a day, {week} a week if it is five days. Worth a number first.",
    "{q} twice a day is {day}, and five days of it is {week}. Do you get to sit down for it?",
    "That is {day} of your day, {week} a week. It is the part of the job nobody pays you for.",
)
# Time said per day: the number is a habit, and a habit is easier to weigh as a week.
TIME_A_DAY = (
    "{q} a day is {week} a week - small enough to keep up, which is the point of it.",
    "{q} a day adds up to {week} a week. Enough to see a change if it is the right thing.",
    "{q} a day, so {week} a week. The trick is that it has to fit a day you actually have.",
)
# A bigger block of time needs a different question from a twenty-minute gap, and a weekly
# figure is easier to feel per day.
TIME_LONG = (
    "{q} is a real chunk of a week. What has to fit inside it?",
    "{q} - is that what you have, or what you think it needs?",
    "{q} is enough to get somewhere with it. What is the first thing in there?",
)
TIME_WEEK = (
    "{q} a week is about {day} a day. That is what it has to fit into.",
    "{q} a week comes to {day} a day - doable, if nothing else takes that slot.",
)
# A size is a sum too: a wall is "2 metres by 3", and the number that matters is the area, which
# is what everything from paint to flooring is sold by.
AREA = (
    "{q} by {b} is {area} square metres - have the number before you buy anything.",
    "That is {area} square metres. What is going on it?",
    "{q} by {b} is {area} square metres. A tin or a roll never covers what the label claims.",
)
# A distance is really a time, and which time depends on how they would go. Under a few miles
# the walk is the interesting number and the car is nothing; past thirty the drive is a day out.
# Three bands and not two, because a time nobody would take is not an option: ten hours on foot
# is not "close", and two hours on a bike is not a way to read twenty five miles.
DISTANCE_NEAR = (
    "{q} is about {walk} minutes walking, or {bike} on a bike.",
    "{q} - {walk} minutes on foot, and no time at all on a bike ({bike} minutes).",
    "{q} is close enough to walk in {walk} minutes, or ride in {bike}.",
)
# Three to ten miles: a ride or a drive. The walk is left out on purpose - it is an afternoon.
DISTANCE_MID = (
    "{q} is about {bike} minutes on a bike, or {drive} in the car.",
    "{q} - a ride of about {bike} minutes, or {drive} driving.",
    "{q} is close enough to cycle ({bike} minutes) and quick in the car ({drive}).",
)
# Past ten miles it is a drive, and the walk and the bike stop being answers. "A day out" is only
# said of a day out: twelve miles is a short drive, not an expedition.
DISTANCE_FAR = (
    "{q} is about {drive} of driving.",
    "{q} is {drive} behind the wheel.",
    "{q} - {drive} in the car, and a lot longer any other way.",
)
DISTANCE_DAY_OUT = (
    "{q} is about {drive} of driving - a day out rather than a hop.",
    "{q} is {drive} behind the wheel; a day out, with a stop on the way.",
)
# "each way" only when the person said so: "its about 300 miles" is 300 miles, not 300 each way.
DISTANCE_FAR_TRIP = (
    "{q} each way is {drive} in the car. Doable in a day if you leave early.",
    "{q} each way - {drive} behind the wheel, and that is before you turn round.",
)
# A stretch of days or weeks with nothing else said: what it is doing is the reply.
SPAN_DAYS = (
    "{q} is long enough to know whether it is working and short enough to change course.",
    "{q} - what has it done in that time? Better, worse or the same?",
    "{q} is a while. Is it going the way you want?",
)
SPAN_WEEKS = (
    "{q} is usually where a thing either settles or needs a proper look. Which is it?",
    "{q} - what would have to change for you to be happy with it?",
    "{q} is enough time for something to show. What has shown?",
)
SPAN_MONTHS = (
    "{q} is long enough that the small bits add up. What is the biggest part of it?",
    "{q} - is that how long it has been, or how long it needs to last?",
)
# A weight is the one bare figure with no card behind it: "about a stone" and "5 kilos" were
# answered "Got it. Is there anything you'd like a hand with?", and "10 lbs" the same, which is
# the bot having nothing to say about a number a person almost only says about their own body.
# The figure comes back in the unit they did not use, because the kilos and the stones are the
# same weight said two ways and the other one is the one that is news.
WEIGHT_LOSS = (
    "{q} is {other} - at a pound or two a week that is {slow} to {fast} weeks, and the slow way "
    "is the one that stays off.",
    "{q} - {other}. Think in months rather than weeks: a pound or two a week is {slow} to {fast} "
    "weeks, and that is the pace that holds.",
    "{q} is {other}, so it is a few months of small changes rather than a push. What would you "
    "change first?",
)
WEIGHT_PLAIN = (
    "{q} is {other}. Is that you, or something you are carrying?",
    "{q} - {other}. What is it that weighs that?",
)
# A thing was named a turn back ("i bought a whole salmon by mistake" / "its about 3 kilos"), so
# the figure belongs to it and "is that you, or something you are carrying" is the bot asking
# about the salmon. The conversion is still the news; the question is not.
WEIGHT_OF_A_THING = (
    "{q} is {other}.",
    "{q} - {other}. Is that what you expected?",
)
# The person's own weight, said with the verb ("i weigh 90 kilos"): the figure is not a target,
# so offering a pace would be answering a question they did not ask, and asking "is that you, or
# something you are carrying" is asking what the line said.
WEIGHT_THEIR_OWN = (
    "{q} is {other}. Is there a number you are aiming for?",
    "{q} - {other}. What would you like to do about it?",
)
# A turn or two back saying the figure is about a body: the pace is then the useful part of the
# answer, and "is that you, or something you are carrying" is the bot not having listened.
WEIGHT_ON_THE_TABLE = re.compile(
    r"\b(?:weight|weigh|weighing|weighed|lose|losing|lost|slim|slimming|diet|diets|dieting|"
    r"stone|stones|kilos?|kilograms?|kg|lbs?|bmi|calories|waist|dress size)\b")
# The body said without the word: "ive put a bit on over christmas", which is the turn people
# say before the figure, so the figure is the answer to what they put on.
WEIGHT_GOING_ON = re.compile(
    r"\bput (?:on|it on|a bit on|a few on|a little on|a couple on|some on|another on|"
    r"weight on|the weight on|a stone on|half a stone on)\b|\b(?:piling|piled|piling it) on\b")


def _number_at(words, at):
    """(value, how many words it took) for the number starting at `words[at]`, or (None, 0).

    People write a number in more than one word ("twenty five minutes", "three hundred a
    year"), so a tens word followed by a units word is added up and a number followed by
    "hundred" is multiplied, the way it is said.
    """
    first = _amount(words[at])
    if first is None:
        return None, 0
    if at + 1 < len(words):
        nxt = words[at + 1].lower().replace("-", "")
        if nxt == "hundred" and first < 100:
            return first * 100, 2
        # Only a units word after a tens word: "twenty five", not "forty a month".
        if words[at].lower() in TENS and nxt in ("one", "two", "three", "four", "five", "six",
                                                "seven", "eight", "nine"):
            return first + NUMBERS[nxt], 2
    return first, 1


def _amount(word):
    """The number a word gives, or None: "45", "£250", "twenty", "forty", "twentyfive"."""
    plain = word.replace(",", "")
    for mark in CURRENCY:
        plain = plain.replace(mark, "")
    plain = plain.replace("-", "")
    if re.fullmatch(r"\d+(?:\.\d+)?", plain):
        return float(plain)
    if plain in NUMBERS:
        return float(NUMBERS[plain])
    for ten, base in TENS.items():
        if plain.startswith(ten) and plain[len(ten):] in NUMBERS:
            return float(base + NUMBERS[plain[len(ten):]])
    return None


def _fmt(value):
    """A number as a person writes it: whole numbers whole, halves with one decimal place."""
    if float(value).is_integer():
        return "{:,}".format(int(round(value)))
    return "{:.1f}".format(value).rstrip("0").rstrip(".")


def _minutes(total):
    """A length in minutes said the way people say it: "1 hour 20", "6 hours 40"."""
    total = int(round(total / 5.0)) * 5  # people say "2 hours 10", not "2 hours 9"
    if total < 60:
        return "%d minutes" % total
    hours, minutes = divmod(total, 60)
    if not minutes:
        return "%d hour%s" % (hours, "" if hours == 1 else "s")
    return "%d hour%s %d" % (hours, "" if hours == 1 else "s", minutes)


# "<thing> is <number>" is still a bare number: "the wall is 2 metres by 3", "my rent is 900 a
# month", "the commute is forty minutes each way". The thing named in front is what the number is
# about, which is the tail's job when it comes after the number, so it is dropped the same way.
SUBJECT = re.compile(r"\A(?:the|my|our|their|his|her|its|this|that|it|there)\s+\w+\s+"
                     r"(?:is|are|was|were|would be|will be)\s+", re.I)

# A word that is the sum itself. "A tenner" and "a fiver" are how people with a small amount
# talk about it, and they carry both the number and the money, so the line reads as money with no
# digit in it. "Twenty quid" needs none of this: quid is a unit like pounds.
MONEY_NOUN = {"tenner": 10, "fiver": 5}
SUM_IN_A_WORD = re.compile(r"\b(?:a|an)\s+(tenner|fiver)\b", re.I)


def _the_sum_inside_the_word(text):
    """("a tenner", "... 10 ...") when the line names its sum with a word, else ("", text)."""
    # `said` is the period loop's own name further down, so nothing here may be called that.
    found = SUM_IN_A_WORD.search(text)
    if not found:
        return "", text
    said = "a %s" % found.group(1).lower()
    return said, (text[:found.start()] + "%d" % MONEY_NOUN[found.group(1).lower()]
                  + text[found.end():])


# A bare "k" is a thousand of something, and which something is on the table a moment ago. "i
# went for a run this morning" / "how far" / "about five k" is five kilometres, and it was read as
# five thousand pounds - "5 k - is that the whole budget or what is left of a bigger one?" Nobody
# answers that about a run.
ON_THE_TABLE_DISTANCE = re.compile(
    r"\b(?:far|further|distance|miles?|km|kilometres?|kilometers?|kms|run|runs|running|ran|"
    r"walk|walked|walking|walks|cycle|cycled|cycling|drive|drove|driving|"
    r"commute|commuting|hike|hiked|hiking|swim|swam|swimming|journey|trip)\b")


# And the other way round: a sum on the table beats a distance, so "i want to save up for a bike"
# / "about five k" is still money. A bike is a purchase, not a distance, and that is why it is not
# in the words above.
ON_THE_TABLE_MONEY = re.compile(
    r"\b(?:budget|spend|spending|spent|cost|costs|afford|save|saving|savings|price|prices|buy|"
    r"buying|bought|paid|pay|rent|bill|bills|deposit|money|cash|quid|salary|wage|wages|"
    r"income|pension|£|\$|€)\b")


def _the_money_words(text):
    return bool(ON_THE_TABLE_MONEY.search(str(text or "").lower()))


def _about_a_distance(clean, memory):
    """True when the thing just said, or the last turn or two, is a distance and not a sum."""
    said = " ".join(str(clean or "").lower().split())
    elsewhere = [said]
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in [t for t in turns if isinstance(t, dict)][-2:] if isinstance(turns, list) else []:
        elsewhere += [str(turn.get(key) or "") for key in ("user", "bot")]
    if any(_the_money_words(text) for text in elsewhere):
        return False
    return any(ON_THE_TABLE_DISTANCE.search(text.lower()) for text in elsewhere)


A_BUDGET_THEY_SET = re.compile(r"\b(?:my|our)\s+(?:budget|limit|cap|ceiling|spending money)\b")


def _read(clean, memory=None):
    """(value, family, unit, period, phrase, tail) for a bare number line, or six Nones.

    `phrase` is the number as the person said it ("45", "£250", "half an hour") so the reply can
    quote it back, and `tail` is what the words after it said the number is about.
    """
    text = clean.strip().strip(".!,")
    # "3km", "5miles": on a phone the unit is stuck to the figure, and a number with letters
    # after it is not a number to `_amount`, so the whole line was left to the caller and "3km"
    # got nothing at all. The unit is split off here and the rest of the reading is unchanged.
    text = re.sub(r"(?<=\d)(kilometres|kilometers|kilograms|kilogram|miles|mile|stones|kilos|"
                  r"kilo|stone|kms|km|mi|kgs|kg|lbs|lb)\b", r" \1", text, flags=re.I)
    named = bool(SUBJECT.search(text))
    # "my budget is about 800 pounds" sets a limit for the rest of the conversation, and the store
    # answers that with "I'll keep what I suggest inside it". Asking what it has to stretch to, one
    # line after being told it is a budget, is the bot not listening.
    a_budget = bool(A_BUDGET_THEY_SET.search(text))
    text = SUBJECT.sub("", text, count=1)
    # "a tenner", "a fiver": the number is inside the noun, so the line is about money with no
    # digit and no unit word in it. It is read as the sum it is, and the reply quotes "a tenner"
    # back rather than "10 pounds", because that is what the person said.
    sum_word, text = _the_sum_inside_the_word(text)
    words = text.split()
    at = 0
    while at < len(words) and _amount(words[at]) is None:
        if words[at].lower() not in LEAD:
            return (None,) * 6
        at += 1
    if at >= len(words):
        return (None,) * 6
    head = words[at]
    amount, took = _number_at(words, at)
    body = words[at + took:]
    # "half an hour", "half a mile": the half is the number and the hour is the unit.
    if head.lower() == "half" and body[:1] and body[0].lower() in ("a", "an"):
        body = body[1:]
    unit = body[0].lower() if body and body[0].lower() in UNITS else ""
    if unit:
        body = body[1:]
    # "an hour and a half each way": the half is part of the number, and leaving it out said
    # forty-five minutes was an hour.
    half_more = [word.lower() for word in body[:3]] == ["and", "a", "half"]
    if half_more:
        amount *= 1.5
        body = body[3:]
    body = _without_a_remark(body)
    body = _without_the_household(body)
    tail = " ".join(body).lower()
    period = None
    for said, name in PERIODS:
        if tail == said or tail.startswith(said):
            period = name
            body = body[len(said.split()):]
            break
    # "its 45 a month, is that a lot": the judgement on the figure is the question about that
    # figure, so the rate is still the whole of what the line is about. Read as more than a rate
    # the line reached no number pool at all, and the turn went to whatever else matched a word in
    # it. Only the judgement shapes are taken off, and only once a period has been read, so
    # "45 a month for the gym" and a bare "is that a lot" are untouched.
    if period and DOUBT_ON_THE_FIGURE.match(" ".join(body).strip(" .,!?")):
        body = []
    for word in body:
        plain = word.lower().strip(".,!?:")
        # A number, a unit or a word that says what the number is about; anything else means the
        # line said something more and is not a bare number.
        if plain in TAIL or plain in UNITS or _amount(word) is not None:
            continue
        if _a_length_they_have_bounded(clean, unit, body, period):
            # "i have 20 minutes before i have to leave": the rest of the line says what the
            # stretch has to fit inside, not what the number is about.
            break
        return (None,) * 6
    phrase = head if head[:1].isdigit() or head[:1] in CURRENCY else _fmt(amount)
    if unit in ("k", "grand"):
        phrase = "%s %s" % (phrase, unit)
    if head.lower() == "half" and unit:
        phrase = "%s %s" % ("half an" if unit[:1] in "aeiouh" else "half a", unit)
    if head.lower() in ("a", "an") and unit:
        phrase = "%s %s" % ("an" if unit[:1] in "aeiouh" else "a", unit)
    if half_more:
        phrase = "%s and a half" % phrase
    if unit:
        family, factor = UNITS[unit]
        body_tail = " ".join(body).lower()
        if unit == "k" and not period and _about_a_distance(clean, memory):
            # "a k" with a distance on the table is a kilometre, not a thousand pounds. The "k" is
            # dropped from the phrase so the reply does not read "5 k km".
            return (amount * UNITS["km"][1], "distance", "km", None,
                    phrase[:-2].strip() if phrase.endswith(" k") else phrase, body_tail)
        if family == "money" and unit in ("pound", "pounds", "quid", "euro", "euros", "dollar",
                                          "dollars") and TRIP.search(body_tail + " " + tail):
            return (None,) * 6
        if family == "money" and a_budget:
            return (None,) * 6
        if family == "span" and named:
            # "my kitten is 4 months", "the boiler is 15 years old": a period said about a named
            # thing is that thing's age, not a stretch of time the person is living through, and
            # asking what it has done in that time is nonsense ("4 months is long enough that the
            # small bits add up" to a kitten).
            return (None,) * 6
        if family == "weight" and named:
            # "the parcel is 2 kilos", "my bag was 22 kilos": the line says what weighs that,
            # so "is that you, or something you are carrying" is asking what it just told us. A
            # named thing keeps whatever answer it had.
            return (None,) * 6
        return amount * factor, family, unit, period, phrase, body_tail
    if _a_take_without_home(words[:at]) and not sum_word:
        # "i take 5 a day" is a count of tablets, and "take" leads a wage only as "take home":
        # the arithmetic on the tablets ("5 a day is 1,825 a year") is about money nobody said.
        # A unit the reading already knows - "it takes 20 minutes" - is not this question.
        return (None,) * 6
    if a_budget and not sum_word:
        return (None,) * 6
    if period:
        if not sum_word and _a_count_the_question_asked_for(clean, memory):
            return (None,) * 6
        phrase = sum_word or phrase
        return amount, "money", "money", period, phrase, " ".join(body).lower()
    # A number with no unit and no period is only money when it carries a currency mark: a bare
    # "250" could be anything, so it keeps whatever the caller would have said.
    if sum_word:
        return amount, "money", "money", None, sum_word, " ".join(body).lower()
    if head[:1] in CURRENCY:
        return amount, "money", "money", None, phrase, ""
    return (None,) * 6


def _q(phrase, unit):
    """The number with its unit, unless the unit is the period the sentence already carries."""
    if unit in ("money", "k", "grand") or unit in phrase:
        return phrase
    return "%s %s" % (phrase, unit)


# A span of time in these pools is a stretch the person is living through - "what has it done in
# that time?", "is that how long it has been, or how long it needs to last?" - so once something is
# on the table the line has to say they are already in it. "i ordered a sofa / about 3 weeks" is a
# wait and "the vet gave me antibiotics / ten days" is a course; neither is theirs to report on.
SPAN_FRAME = re.compile(
    r"\b(?:been|since|ago|started|start|had|having|took|taking|on it|so far|now)\b", re.I)
# "how long does a cold last", "how long is the drive", "how long in the oven": the number that
# follows is a fact about the thing asked about, so a line about spending the time well ("get
# everything out before the clock starts") is advice about the wrong thing. "how long should i
# boil an egg" is the other kind - the person is choosing a stretch of their own - and keeps it.
A_QUESTION_ABOUT_A_LENGTH = re.compile(
    r"\bhow (?:long|far|much|many|big|deep|hot)\b|\bhow soon\b|\bwhen will\b", re.I)
A_BUDGET_QUESTION = re.compile(
    r"\bhow (?:long|much time|often)\s+(?:should|shall|do|can|could|might|would) (?:i|we)\b",
    re.I)


# A figure the person bounds - "its only 2 hours", "only 20 minutes" - is not a budget they have
# to fill: they are telling themselves the thing is short, and a line about what fits inside the
# time answers a question nobody asked. "i only have 20 minutes" is the other kind: they have the
# time and want it spent well, so the possession keeps the reading.
A_BOUND = re.compile(r"\b(?:only|just|barely|no more than|at most|less than)\b", re.I)
# A length the person has is bounded by what it has to fit around, and the clause that says so is
# not a new subject: "i have 20 minutes" was read as time to spend well, and "i have 20 minutes
# before i have to leave" was not read at all - the same statement got a budget line or a
# "Thanks for telling me - I'm here if you want to dig into any of that" depending on whether they
# said why (honey-bat, #routing thread 179, and "i have half an hour free" too). The words that
# follow the unit here are what the stretch has to fit inside or what it is for, and the number is
# still the whole of what the person is telling the bot.
BOUNDED_BY = frozenset((
    "before", "until", "till", "til", "to", "for", "free", "spare", "off", "left", "after",
    "between", "while", "then", "so", "if", "and", "but", "plus", "today", "tonight", "now",
))
# The frame that makes the length theirs: "i have", "ive got", "got", "we've only got". A number
# that is not in it ("a 20 minute walk", "the 20 minute drive") is the length OF something, which
# is a fact about it and not time on their hands, so the words after the unit are read as before.
THEY_HAVE_THE_TIME = re.compile(
    r"^\s*(?:(?:i|we|ive|i've|we've|weve)\s+(?:only\s+|just\s+)?(?:have|had|got)\b|"
    r"(?:only\s+|just\s+)?got\b)", re.I)
# "we have 3 weeks left", "20 minutes to go": the figure is what is left of a stretch that is
# already running, so nothing has to be fitted into it - the same wrong question as a bound, and
# "3 weeks is enough time for something to show. What has shown?" is said to somebody counting
# down (hearty-emu, #6254).
A_REMAINDER = re.compile(r"\b(?:left|to go|remaining|to run)\b", re.I)
THEY_HAVE_IT = re.compile(r"\b(?:have|has|had|got|left|spare|need|needs|gives? me)\b", re.I)


# A length the person bounds is not a budget to fill, so every pool above answers a question
# nobody asked: "2 hours is enough for one thing done properly and not two done badly" is a
# lecture at somebody nervous about a flight. Standing the whole reading down is not the answer
# either - the turn then fell to the plain acknowledgement ("Got it - it's only two hours."),
# which says nothing back (fast-ant, #6254). The bound is the thing to answer: they have put a
# number on the length themselves, and what a friend asks is whether it feels short to them.
# Every line below says something about the length first and asks after: a reply that is nothing
# but a question turns the lecture into a shrug in question form, and STYLE.md asks for the answer
# in the first sentence (steward-agile-lychee, #6254). What is true of a length they have bounded is
# that it is small, so the sentence says so and the question is about their side of it.
A_LIMIT_ON_A_LENGTH = (
    "{q} is short. What is on the other side of it?",
    "{q} is not much time to sit through. What would make it easier?",
    "{q} is nothing in the scheme of a day. What are you least looking forward to?",
    "{q} is short enough that it will be over before it has properly started. What do you want "
    "out of it?",
)
# "we have 3 weeks left", "i have 20 minutes left": what is left of a stretch that is already
# running, so what the person is deciding is what goes in it, not whether it is short.
A_WHAT_IS_LEFT = (
    "{q} left - short enough now that what goes in it matters. What has to happen in it?",
    "{q} left - that is the room there is. What is the one thing that has to get done?",
    "{q} left, so it is time to decide what matters. What would you put first?",
)


def _a_length_they_have_bounded(clean, unit, body, period):
    """Whether a length the person has is being bounded or explained, not made into a subject.

    Read only for a unit of time, only when the line says the time is theirs ("i have", "ive
    got", "got"), and only when the words after the unit open on what the stretch is bounded by
    ("before i have to leave", "to get to the station", "free", "between meetings"). A number
    that is not in that frame is the length of something ("a 20 minute walk", "the 20 minute
    drive"), and the words after it say what it is the length of, so nothing is loosened there.
    """
    family = UNITS.get(unit, (None, None))[0]
    if family != "time" or period:
        return False
    said = " ".join(str(clean or "").lower().split())
    if not THEY_HAVE_THE_TIME.search(said):
        return False
    if not body:
        return False
    return body[0].lower().strip(".,!?:") in BOUNDED_BY


def _a_bound_not_a_budget(clean):
    """Whether the length is a limit the person put on it rather than time they have to spend."""
    said = " ".join(str(clean or "").lower().split())
    return bool(A_BOUND.search(said) and not THEY_HAVE_IT.search(said))


def _the_turn_above(memory):
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    return turns[-1] if turns else {}


# A figure the line itself calls a change ("i need to lose two stone", "ive put a stone on") is
# an amount, whatever its size. A body word from a turn above only makes the figure a change when
# the figure is the size of one: a stone is, and ninety kilos is somebody's weight, so the pace
# "99 to 198 weeks" is arithmetic about the wrong number.
A_CHANGE_SAID = re.compile(
    r"\b(?:lose|losing|lost|shed|shedding|drop|dropping|shift|shifting|put on|putting on|"
    r"gained|gaining|gain|gained|lose off|off)\b")
A_CHANGE_IS_THIS_SMALL = 20.0        # kilos: a couple of stone is a target, not a body weight

# "i weigh 90 kilos" says whose weight it is without naming a thing, and "is that you, or
# something you are carrying" is the bot asking a question the line answered.
I_WEIGH = re.compile(r"\bi (?:weigh|weighed|weighs)\b|\bive (?:weighed|put)\b")


def _the_change_is_the_line(clean):
    """Whether this line itself says the figure is weight coming off or going on."""
    return bool(A_CHANGE_SAID.search(" ".join(str(clean or "").lower().split())))


def _a_weight_they_mean_themselves(memory, clean=""):
    """Whether this line, or a turn or two back, says the figure is about a body."""
    if I_WEIGH.search(" ".join(str(clean or "").lower().split())):
        return True
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)][-2:]
    for turn in turns:
        for key in ("user", "bot"):
            said = " ".join(str(turn.get(key) or "").lower().split())
            if WEIGHT_ON_THE_TABLE.search(said) or WEIGHT_GOING_ON.search(said):
                return True
    return False


# "the dog weighs 30 kilos", "he weighs 30 kilos": the line says what is being weighed, so the
# figure is that thing's and the question about who it belongs to has been answered.
SOMETHING_WEIGHED = re.compile(
    r"\b(?:he|she|it|they|we|you|the|my|our|his|her|their|this|that)\b[^.?!]{0,24}"
    r"\bweighs?\b|\bweighs?\b[^.?!]{0,24}\b(?:the|my|our|his|her|their|this|that)\b")


def _a_thing_was_named(memory, clean=""):
    """Whether this line or the turn above named a thing this figure could be the weight of.

    "its about 3 kilos" after "i bought a whole salmon by mistake" is the salmon's weight, and
    asking "is that you, or something you are carrying" is the bot not reading its own
    conversation. The names come from the understanding engine's own list, so this is the same
    set of things the rest of the bot recognises.
    """
    if SOMETHING_WEIGHED.search(" ".join(str(clean or "").lower().split())):
        return True
    above = _the_turn_above(memory).get("user")
    if not above:
        return False
    try:
        from ..understanding.topics import THINGS
    except Exception:  # noqa: BLE001 - without the list the figure is answered plainly
        return False
    words = re.findall(r"[a-z]+", str(above).lower())
    return any(word in THINGS for word in words)


def _a_span_they_are_in(clean, memory):
    """Whether the line, or the turn above it, says this stretch has already been lived."""
    said = [clean]
    above = _the_turn_above(memory).get("user")
    if above:
        said.append(above)
    return any(SPAN_FRAME.search(" ".join(str(one or "").lower().split())) for one in said)


# "how many calories" / "2000 a day": the figure that comes back is that many of the thing asked
# about, and "2000 a day is 730,000 a year" is arithmetic about a quantity nobody is spending. A
# rate is money only when nothing on the table says the count is of something else.
A_COUNT_ASKED_FOR = re.compile(r"\bhow many\s+([a-z]+)")
A_WAY_OF_PAYING = re.compile(
    r"\b(?:money|pounds?|quid|euros?|dollars?|bucks?|pence|cost|costs|spend|spent|spending|pay|"
    r"paid|paying|price|priced|budget|rent|bill|bills|salary|wage|wages|income|save|saving|"
    r"savings|afford|cheap|expensive|earn|earned|overdraft|loan|subscription)\b|[\u00a3$\u20ac]")


def _a_count_the_question_asked_for(clean, memory):
    """Whether the turn above asked "how many <thing>" and nothing on the table is money.

    A rate with no currency word in it ("2000 a day") is read as money, and that is right for
    "45 a month" out of nowhere. It is wrong when the bot has just asked how many of something:
    the person is answering that question, so the number counts the thing asked about.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    above = turns[-1] if turns else {}
    said = [" ".join(str(above.get("user") or "").lower().split()),
            " ".join(str(above.get("bot") or "").lower().split()),
            " ".join(str(clean or "").lower().split())]
    if not any(A_COUNT_ASKED_FOR.search(one) for one in said[:2]):
        return False
    return not any(A_WAY_OF_PAYING.search(one) for one in said)


def _a_fact_about_a_length(memory):
    """Whether the turn above asked how long something lasts, is, or takes."""
    above = " ".join(str(_the_turn_above(memory).get("user") or "").lower().split())
    return bool(above and A_QUESTION_ABOUT_A_LENGTH.search(above)
                and not A_BUDGET_QUESTION.search(above))


def reply_for(clean, memory):
    """A reply to a line that is nothing but a number, or None to leave it to the caller."""
    value, family, unit, period, phrase, tail = _read(clean, memory)
    if family is None:
        return None
    if family == "span" and _the_turn_above(memory) and not _a_span_they_are_in(clean, memory):
        return None
    if family == "time" and not period and value <= 180 and _a_fact_about_a_length(memory):
        return None
    if family in ("time", "span") and not period and A_REMAINDER.search(
            " ".join(str(clean or "").lower().split())):
        left = pick(A_WHAT_IS_LEFT, memory, clean).format(q=_q(phrase, unit))
        return left[:1].upper() + left[1:]
    if family == "time" and not period and _a_bound_not_a_budget(clean):
        # The length is a limit they set, not time they have: answer the limit itself rather
        # than standing down to the acknowledgement. The reading is kept because the pools above
        # are the wrong ones for it, and a turn with nothing in it is worse than either.
        limit = pick(A_LIMIT_ON_A_LENGTH, memory, clean).format(q=_q(phrase, unit))
        return limit[:1].upper() + limit[1:]
    reply = _say(family, _q(phrase, unit), value, period, tail, memory, clean, unit)
    # A number is often the first word of the reply ("an hour: get everything out first", "£250 -
    # is that the whole budget?"), and a sentence does not start in lower case.
    return reply[:1].upper() + reply[1:] if reply else None


# A thing named as the person's own: "my mortgage", "our rent", "the energy". This is how a line
# says what the rate is *for*, and it is the difference between a rate that can be judged and a
# number that can only be summed - see `the_thing_they_pay_for`.
THEIR_THING = re.compile(r"\b(?:my|our|the|his|her|their)\s+([a-z][a-z'-]{2,})")
# Words that follow one of those words without naming a thing: a period, a quantity, or the
# person themselves. "the last one" and "my whole bill" are not what is being paid for.
NOT_A_THING = frozenset("""
month months week weeks year years day days fortnight quarter hour hours minute minutes time
times lot lots one ones thing things rest whole same other other's own money cash budget
first last next same top bottom bill bills price prices cost costs total monthly weekly yearly
""".split())


def the_thing_they_pay_for(clean):
    """What the rate in the line is for, or None when the line only gives the number.

    "my mortgage is 900 a month, is that normal" names the thing, so the question can be answered
    the way a person answers it - by comparing that thing with the same thing elsewhere, which is
    what the price pool does. "its 45 a month, is that a lot" names nothing: there is no "it" in
    the line to compare with anything, and the only answer about what they said is the sum it
    comes to over a year. Same reading, one word apart, so the caller asks this before choosing.
    """
    said = " ".join(str(clean or "").lower().split())
    for word in THEIR_THING.findall(said):
        if word not in NOT_A_THING:
            return word
    return None


def the_rate_they_asked_about(clean, memory=None):
    """The arithmetic on a rate the line itself carries and judges, or None.

    "its 45 a month, is that a lot" is a question about that rate. The comparison advice the price
    pool gives - two or three places, the same thing - is for a price with no figure in the line,
    because there is nothing to work out; here there is, and the sum it comes to over a year is
    the one answer that is about what the person said. A line that does name the thing ("my
    mortgage is 900 a month") is the other way round - see `the_thing_they_pay_for`.
    """
    value, family, unit, period, phrase, tail = _read(clean, memory)
    if family != "money" or not period:
        return None
    from .prices import PRICE_JUDGEMENT
    said = " ".join(str(clean or "").lower().split())
    if not PRICE_JUDGEMENT.search(said):
        return None
    if SAVINGS_AFTER_A_RATE.search(said) and period in ("month", "week", "year"):
        year = value * {"month": 12, "week": 52, "year": 1}[period]
        said_period = {"month": "a month", "week": "a week", "year": "a year"}[period]
        reply = pick(SAVINGS, memory, clean).format(
            q=_q(phrase, unit), period=said_period, year=_fmt(year))
        return reply[:1].upper() + reply[1:]
    reply = _say(family, _q(phrase, unit), value, period, tail, memory, clean, unit)
    return reply[:1].upper() + reply[1:] if reply else None


def _without_a_pointing_tail(words):
    """The words with a trailing preposition and pronoun taken off ("a day for it").

    The pronoun says the subject is the one already on the table, so it adds nothing the number
    does not already have. It is not a new subject like the noun in "20 minutes for the roast".
    """
    if len(words) >= 2:
        tail = [word.lower().strip(".,!?:;") for word in words[-2:]]
        if tail[0] in POINTING_BACK and tail[1] in A_PRONOUN:
            return words[:-2]
    return words


def _without_a_hedge(words):
    """The words with the speaker's own doubt taken off the end ("... a day, i think").

    "i think", "i reckon", "i guess" after a number say how sure the person is of it, not what it
    is about, and the number is still the whole of the line. Only the speaker's doubt: "at least"
    and "at most" change what the figure means and are left where they are.
    """
    if len(words) >= 2:
        tail = [word.lower().strip(".,!?:;") for word in words[-2:]]
        if tail[0] in ("i", "id", "i'd") and tail[1] in HEDGES:
            return words[:-2]
    return words


# The household said between the figure and its period: "we bring home 3000 between us a month"
# is "3000 a month" with the people named in the middle. Those words are never what the number is
# about, so they come off before the period is read - otherwise the period was never found, the
# line was not a wage, and the store answered it with a receipt.
THE_HOUSEHOLD = (("between", "us"), ("between", "the", "two", "of", "us"),
                 ("for", "the", "two", "of", "us"), ("for", "both", "of", "us"),
                 ("between", "the", "two", "of", "them"), ("together",), ("combined",),
                 ("in", "total"), ("altogether",), ("in", "all"))


def _without_the_household(words):
    """The words with the household taken off, if that is what they are.

    The phrase sits in front of the period ("3000 between us a month") or behind it ("3000 a
    month between us"), and either way it is the people, not the thing the number is about.
    """
    plain = [word.lower().strip(".,!?:;") for word in words]
    for phrase in THE_HOUSEHOLD:
        if tuple(plain[:len(phrase)]) == phrase:
            return words[len(phrase):]
        if len(plain) > len(phrase) and tuple(plain[-len(phrase):]) == phrase:
            return words[:-len(phrase)]
    return words


TAKE = ("take", "takes", "taking", "took")


def _a_take_without_home(lead):
    """Whether the line led with "take" and never said "home": a count, not a wage."""
    said = [word.lower().strip(".,!?:;") for word in lead]
    return any(word in TAKE for word in said) and "home" not in said


def _without_a_remark(words):
    """A number with the person's own tail on it: "a day for it, i think"."""
    for _ in range(3):
        trimmed = _without_a_pointing_tail(_without_a_hedge(words))
        if trimmed == words:
            break
        words = trimmed
    return words


def _in_a_conversation(memory):
    """Whether the bot has already been told what the number is about."""
    return any(turn.get("user") for turn in (memory.get("turns") or []) if isinstance(turn, dict))


# Ninety minutes and up is not a stretch anybody calls tight, and "one thing only" is advice for
# a quarter of an hour: "ive got 2 hours between meetings" was answered "2 hours is tight - one
# thing only. What are you fitting into it?", and "i have 3 hours" the same way ("3 hours goes
# faster than it looks, so decide before you start"). Two hours holds a thing and the tidying up
# after it, so the two lines that tell the person the time is short are for a shorter stretch.
A_STRETCH_THAT_IS_NOT_SHORT = 120


def _not_short(pool, value):
    """The pool with the lines that tell the person the time is short taken out, if it is not."""
    if value < A_STRETCH_THAT_IS_NOT_SHORT:
        return pool
    kept = tuple(line for line in pool
                 if "is tight" not in line and "faster than it looks" not in line)
    return kept or pool


def _without_a_question(pool):
    """"5 minutes" after "how long shall i boil an egg" is not an opening: asking what it is for
    again, one turn after being told, is the bot not listening. Lines that ask are for a number
    that arrives out of nowhere."""
    return tuple(line for line in pool if "?" not in line) or pool


def _say(family, q, value, period, tail, memory, clean, unit=None):
    """The reply for one family of number, or None."""
    if family is None:
        return None
    if family == "money":
        if INCOME.search(str(clean or "").lower()):
            if period == "month":
                return pick(INCOME_MONTH, memory, clean).format(q=q, year=_fmt(value * 12))
            if period in ("week", "fortnight"):
                weeks = value if period == "week" else value / 2.0
                return pick(INCOME_WEEK, memory, clean).format(
                    q=q, month=_fmt(round(weeks * 52 / 12.0)), year=_fmt(weeks * 52))
            if period == "year":
                return pick(INCOME_YEAR, memory, clean).format(
                    q=q, month=_fmt(round(value / 12.0)), week=_fmt(round(value / 52.0)))
            return pick(INCOME_PLAIN, memory, clean).format(q=q)
        if period == "month":
            return pick(MONEY_MONTH, memory, clean).format(q=q, year=_fmt(value * 12))
        if period == "week":
            return pick(MONEY_WEEK, memory, clean).format(
                q=q, month=_fmt(round(value * 52 / 12.0)), year=_fmt(value * 52))
        if period == "year":
            return pick(MONEY_YEAR, memory, clean).format(
                q=q, month=_fmt(round(value / 12.0)), week=_fmt(round(value / 52.0)))
        if period in ("day", "fortnight"):
            per_day = value / 14.0 if period == "fortnight" else value
            return pick(MONEY_DAY, memory, clean).format(
                q=q, month=_fmt(round(per_day * 30)), year=_fmt(round(per_day * 365)))
        return pick(MONEY_PLAIN, memory, clean).format(q=q)
    if family == "time":
        if period == "day" and not TRIP.search(str(tail or "")):
            # "20 minutes a day" was answered as a plain twenty minutes, so the "a day" was
            # dropped and the whole of it (a couple of hours a week) went unsaid.
            # Every day is seven days: the week is the figure the reply quotes, and a five-day
            # week in it said twenty minutes a day was 1 hour 40 a week when it is 2 hours 20 -
            # the month below was already counting thirty days, so the two halves disagreed.
            return pick(TIME_A_DAY, memory, clean).format(
                q=q, week=_minutes(value * 7), month=_minutes(value * 30))
        if TRIP.search(tail):
            return pick(TIME_TRIP, memory, clean).format(
                q=q, day=_minutes(value * 2), week=_minutes(value * 10))
        if period == "week":
            return pick(TIME_WEEK, memory, clean).format(q=q, day=_minutes(value / 7.0))
        if value > 180:
            return pick(TIME_LONG, memory, clean).format(q=q)
        pool = TIME_BUDGET if not _in_a_conversation(memory) else _without_a_question(TIME_BUDGET)
        return pick(_not_short(pool, value), memory, clean).format(q=q)
    if family == "distance":
        if value <= 0:
            return None
        walk = int(round(value * 20))            # three miles an hour
        bike = int(round(value * 5))             # twelve miles an hour
        drive = int(round(value * 1.33 if value > 10 else value * 2.4))
        if value <= 3:
            return pick(DISTANCE_NEAR, memory, clean).format(q=q, walk=walk, bike=bike)
        if value <= 10:
            return pick(DISTANCE_MID, memory, clean).format(
                q=q, bike=bike, drive=_minutes(drive))
        if TRIP.search(str(tail or "")):
            pool = DISTANCE_FAR_TRIP
        elif value > 60:
            pool = DISTANCE_DAY_OUT
        else:
            pool = DISTANCE_FAR
        return pick(pool, memory, clean).format(q=q, drive=_minutes(drive))
    if family == "size":
        # "2 metres by 3" is one measurement too few to be useful; the pair is an area, and an
        # area is what paint, flooring and wallpaper are sold against.
        other = re.search(r"\bby\s+(\d+(?:\.\d+)?|" + "|".join(sorted(NUMBERS)) + r")\b", tail)
        if other is None:
            return None
        second = _amount(other.group(1))
        if not second or second <= 0:
            return None
        return pick(AREA, memory, clean).format(q=q, b=_fmt(second), area=_fmt(value * second))
    if family == "span":
        if value <= 3:
            return pick(SPAN_DAYS, memory, clean).format(q=q)
        if value <= 21:
            return pick(SPAN_WEEKS, memory, clean).format(q=q)
        if value <= 400:
            return pick(SPAN_MONTHS, memory, clean).format(q=q)
    if family == "weight":
        if value <= 0.2:
            return None
        kilos = "%s kilo%s" % (_fmt(round(value, 1)), "" if round(value, 1) == 1 else "s")
        pounds = value / 0.4536
        said_kilos = (unit or "") in ("kilo", "kilos", "kilogram", "kilograms", "kg", "kgs")
        other = "%s pound%s" % (_fmt(round(pounds, 1)), "" if round(pounds, 1) == 1 else "s") \
            if said_kilos else kilos
        slow = max(1, int(round(pounds / 2.0)))
        fast = max(1, int(round(pounds)))
        # A pound or two a week is the pace worth naming only when it is more than a week or two
        # of it: "half a kilo is 1.1 pounds" answered "that is 1 to 1 weeks" is arithmetic nobody
        # asked for.
        body = _a_weight_they_mean_themselves(memory, clean)
        if body and fast > 2 and (value <= A_CHANGE_IS_THIS_SMALL
                                  or _the_change_is_the_line(clean)):
            pool = WEIGHT_LOSS
        elif I_WEIGH.search(" ".join(str(clean or "").lower().split())):
            pool = WEIGHT_THEIR_OWN
        elif _a_thing_was_named(memory, clean):
            pool = WEIGHT_OF_A_THING
        else:
            pool = WEIGHT_PLAIN
        return pick(pool, memory, clean).format(q=q, other=other, slow=slow, fast=fast)
    return None


# --------------------------------------------------------------- the figure against the answer
# The water, sleep and exercise answers all give their rule as a range with a unit: "Six to eight
# glasses a day", "seven to nine hours", "about 150 minutes a week". The next line then gives the
# person's own figure and often no unit at all - "i drink about 3", "i get about 5" - because the
# unit is the one the answer just used. The old turn was an echo ("Got it - you drink about 3"),
# which is the one reply that tells them nothing about the number they just offered. The figure is
# read in the answer's own unit, and where it sits is the reply.
A_RANGE_WITH_A_UNIT = re.compile(
    r"\b(?P<lo>\d{1,4}(?:\.\d+)?|" + "|".join(sorted(NUMBERS, key=len, reverse=True)) + r")"
    r"\s*(?:to|and|-|\u2013|or)\s*"
    r"(?P<hi>\d{1,4}(?:\.\d+)?|" + "|".join(sorted(NUMBERS, key=len, reverse=True)) + r")"
    r"\s*(?P<unit>glasses?|litres?|liters?|hours?|minutes?|steps|portions?|servings?|"
    r"sessions?|workouts?|units?)\b"
    r"(?:\s*(?:a|per|each)\s*(?P<period>day|week|month))?", re.I)
# The unit as it is said again in the reply: "3 glasses", "20 minutes".
UNIT_SAID = {"glasses": "glasses", "glass": "glasses", "litres": "litres", "litre": "litres",
             "liters": "litres", "liter": "litres", "hours": "hours", "hour": "hours",
             "minutes": "minutes", "minute": "minutes", "steps": "steps", "step": "steps",
             "portions": "portions", "portion": "portions", "servings": "portions",
             "serving": "portions", "sessions": "sessions", "session": "sessions",
             "workouts": "sessions", "workout": "sessions", "units": "units", "unit": "units"}
# Which part of a day the unit belongs to, so the reply can give the one step that closes the gap.
UNIT_IS = (
    (re.compile(r"glass|litre|liter", re.I), "water"),
    (re.compile(r"hour", re.I), "sleep"),
    (re.compile(r"minute|step|session|workout", re.I), "move"),
    (re.compile(r"portion|serving", re.I), "portion"),
)
# A rule the answer states as one figure rather than a range: "aim for about 150 minutes a week".
# Only a figure with an aiming word in front of it is a rule; "a 30-minute earlier bedtime" is a
# step inside an answer, not the thing the person's own figure is measured against.
A_SINGLE_RULE = re.compile(
    r"\b(?:about|around|roughly|at least|aim for|aim to|up to|no more than|no less than)\s+"
    r"(?P<num>\d{1,4}(?:\.\d+)?)\s*"
    r"(?P<unit>glasses?|litres?|liters?|hours?|minutes?|steps|portions?|servings?|sessions?|"
    r"workouts?|units?)\b(?:\s*(?:a|per|each)\s*(?P<period>day|week|month))?", re.I)
# A line that only gives a figure: "i drink about 3", "maybe 5", "i get five". A unit may come
# after it, but only the answer's own unit ("10 glasses" against six to eight glasses a day); a
# line with a unit of its own ("i drink 2 litres a day") is another entry's question and is left.
A_FIGURE_ALONE = re.compile(
    r"^(?:[a-z']+\s+){0,5}?(?P<num>\d{1,3}(?:\.\d+)?|" +
    "|".join(sorted(NUMBERS, key=len, reverse=True)) + r")\s*(?P<what>[a-z']*)\s*\.?$", re.I)
# The words people put in front of a figure when they are not sure of it. They carry no subject
# and no unit, so the figure is the whole of the line.
ABOUT_A_FIGURE = re.compile(
    r"\b(?:i (?:drink|get|sleep|do|walk|run|eat|have|take|manage|average|only get|usually get)"
    r"|about|around|roughly|maybe|only|just|probably|usually|average|like)\b", re.I)
# A year of age is not a figure against the answer's unit: "how many hours of sleep do i need" /
# "im 34" is a person, not thirty-four hours.
AN_AGE = re.compile(r"\b(?:i'?m|im|i am)\b|\byears? old\b|\bage\b", re.I)
NOT_A_UNIT_ITSELF = re.compile(r"[£$€]|\b(?:k|kg|g|mg|ml|cm|mm|miles?|km|inches|feet|foot)\b",
                               re.I)
FIGURE_BELOW = (
    "{figure} {unit} is short of the {range} the answer named. {step}",
    "{figure} {unit} - that is under the {range} that answer gave, so the gap is the bit worth "
    "closing. {step}",
    "You are at {figure} {unit} against {range}. {step}",
)
FIGURE_INSIDE = (
    "{figure} {unit} is inside the {range} the answer named - that is the part that matters, so "
    "keep it there rather than adding to it.",
    "{figure} {unit} sits in the {range} the answer named. Steady is the whole of it at that "
    "level.",
)
FIGURE_ABOVE = (
    "{figure} {unit} is past the {range} the answer named. {step}",
    "You are already over the {range} the answer named at {figure} {unit}. {step}",
)
STEPS = {
    "water": {
        "below": "Put a glass by the kettle and have one with each meal, which is three before "
                 "you count anything else.",
        "above": "Past that, more is not better: pale straw is the check, and you are already "
                 "there.",
    },
    "sleep": {
        "below": "Half an hour earlier to bed, with the same wake-up time even after a bad "
                 "night, is what closes it.",
        "above": "Sleeping past it is not a gain - the steady wake-up time is what keeps the "
                 "good nights coming.",
    },
    "move": {
        "below": "Two ten-minute walks beat one long one, because they are easier to keep up.",
        "above": "Past it, the gain is in keeping it going rather than adding more.",
    },
    "portion": {
        "below": "One at breakfast and one at each main meal gets you to it without a plan.",
        "above": "Past it, the thing worth holding is the mix rather than the count.",
    },
}
A_STEP_EITHER_WAY = {
    "below": "Start at what you can keep up and add a little when it feels easy.",
    "above": "Being past it is not what needs fixing; keeping it steady is.",
}


PERIOD_NAMED = {"day": "a day", "week": "a week", "month": "a month"}

# A bare figure is read in the answer's unit only when the two are the same size. "three" against
# "six to eight glasses" is three of the thing asked about; "3" against "150 minutes a week" is
# three sessions, or three walks, or three of something else, and the answer's unit read into it
# invents "You are at 3 minutes against 150 minutes a week". An order of magnitude is the line the
# figures path already draws, so the same one is drawn here, in both directions.
TEN_TIMES = 10


def _the_unit_of_one(unit):
    """The unit as it is written after a figure of one: "1 glass", not "1 glasses"."""
    word = str(unit or "")
    if word.endswith("sses"):
        return word[:-2]  # glasses -> glass, classes -> class
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 2:
        return word[:-1]
    return word


def _the_answer_range(above):
    """(low, high, unit, said) for the rule with a unit in the answer, or None.

    A range is the usual shape ("six to eight glasses a day"); a single aiming figure is the other
    ("aim for about 150 minutes a week"), and both are a rule the person's own figure sits against.
    """
    # The rule that comes first in the answer is the one the figure is about: "about 150 minutes a
    # week" is stated before the "three or four sessions a week" that is a way of doing it, and a
    # bare "20" means twenty of the first unit, not twenty of the last.
    rules = []
    for found in A_RANGE_WITH_A_UNIT.finditer(above):
        low = _amount(found.group("lo").lower())
        high = _amount(found.group("hi").lower())
        if not low or not high or low <= 0 or high <= 0:
            continue
        if high < low:
            low, high = high, low
        rules.append((found.start(), low, high, found.group("unit").lower(),
                      found.group("period")))
    for found in A_SINGLE_RULE.finditer(above):
        value = _amount(found.group("num").lower())
        if not value or value <= 0:
            continue
        rules.append((found.start(), value, value, found.group("unit").lower(),
                      found.group("period")))
    if not rules:
        return None
    _, low, high, unit, period = min(rules, key=lambda rule: rule[0])
    return (low, high, unit,
            _the_rule_said(low, None if low == high else high, unit, period))


def _the_rule_said(low, high, unit, period):
    """The rule as the reply says it back: "6 to 8 glasses a day", "150 minutes a week"."""
    figure = "%s to %s" % (_fmt(low), _fmt(high)) if high is not None else _fmt(low)
    said = "%s %s" % (figure, UNIT_SAID.get(str(unit).lower(), str(unit).lower()))
    when = PERIOD_NAMED.get(str(period or "").lower())
    return said + (" " + when if when else "")


def _the_family(unit):
    for pattern, family in UNIT_IS:
        if pattern.search(unit):
            return family
    return ""


def the_figure_against_the_answer(clean, memory):
    """The figure the person gives, read in the unit of the rule the answer just named, or None.

    Only a line that is a figure and little else is read, and only when the bot's last answer
    named a rule with a unit. A money amount, a measurement or an age is left to the entries that
    read those, and so is a line whose own unit is not the answer's.
    """
    line = " ".join(str(clean or "").lower().split())
    if not line or NOT_A_UNIT_ITSELF.search(line) or AN_AGE.search(line):
        return None
    if not ABOUT_A_FIGURE.search(line):
        return None
    alone = A_FIGURE_ALONE.match(line)
    if alone is None:
        return None
    figure = _amount(alone.group("num"))
    if not figure or figure <= 0 or figure > 500:
        return None
    reading = memory.get("understood") if isinstance(memory, dict) else None
    if isinstance(reading, dict) and "maths" in (reading.get("asks") or ()):
        return None
    above = " ".join(str(last_bot(memory) or "").split())
    if not above:
        return None
    named = _the_answer_range(above)
    if not named:
        return None
    low, high, unit, said = named
    family = _the_family(unit)
    said_unit = UNIT_SAID.get(unit, unit)
    their_unit = (alone.group("what") or "").lower()
    if their_unit and (_the_family(their_unit) != family or not family):
        return None  # they named something else, and another entry reads that
    if figure * TEN_TIMES < low or figure > high * TEN_TIMES:
        # Not the answer's unit at all: a bare three where the rule counts minutes is three of
        # something else, and the echo is a better reply than a figure in a unit they never said.
        return None
    figure_said = _fmt(figure)
    said_unit = _the_unit_of_one(said_unit) if figure == 1 else said_unit
    if figure < low:
        step = STEPS.get(family, A_STEP_EITHER_WAY)["below"]
        reply = pick(FIGURE_BELOW, memory, clean).format(
            figure=figure_said, unit=said_unit, range=said, step=step)
    elif figure > high:
        step = STEPS.get(family, A_STEP_EITHER_WAY)["above"]
        reply = pick(FIGURE_ABOVE, memory, clean).format(
            figure=figure_said, unit=said_unit, range=said, step=step)
    else:
        reply = pick(FIGURE_INSIDE, memory, clean).format(
            figure=figure_said, unit=said_unit, range=said)
    return reply[:1].upper() + reply[1:]
