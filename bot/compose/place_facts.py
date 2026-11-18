"""A fact that belongs to one particular place, said honestly.

Whether a pub has a car park, whether a hotel takes dogs, whether a leisure centre has a pool: the
bot cannot know any of it. The line it used to give was the generic search hedge ("A quick search
online will get you a solid answer"), which is the worst reply for this shape, because the answer
exists and is one tap away on the place's own page. The bot already answers opening hours that way
("I can't check today's opening hours, sorry. The venue's own page or its map listing shows them"),
and a place's own facilities are the same kind of fact: it belongs to that place, it changes, and
nobody but them can confirm it.

`bot/compose/fallback.py` asks this first thing in `_live`, so it only ever replaces a hedge or a
shrug. The ask has to be put to a place, and it has to name a thing that belongs to one.
"""
import re

# A fact about one particular place - whether it has a car park, takes dogs, does takeaway,
# has a pool - is not the sort of thing the bot can hold: it belongs to that place and it
# changes. What the bot said instead was the generic search hedge ("A quick search online will
# get you a solid answer"), which is the worst line for it, because the answer exists and is one
# tap away on the place's own page. So it gets the same treatment as the live notes above: the
# honest limit, and where the answer actually is.
#
# The ask is a yes/no put to a place, and it has to name what is being asked about. A "do they
# have" with no thing in it is a different question ("do they have a dog" about a friend's
# house), and it keeps whatever answer it had.
PLACE_ASKS = re.compile(
    r"(?:\b(?:do|does|did)\s+(?:they|it)\s+(?:have|got|do|offer|allow|take|sell|serve|provide|"
    r"accept|permit|charge)\b"
    # "does the leisure centre have a pool", "do the rooms take dogs": the place is named in
    # the subject, so the verb is two or three words further along. The subject has to open on
    # a determiner, which is what keeps "does he have a car park pass" out of it, and the thing
    # asked about still has to be one of the place words below.
    r"|\b(?:do|does|did)\s+(?:the|this|that|these|those|a|an|my|our|your)\s+"
    r"(?:[a-z'-]+\s+){0,2}(?:have|got|do|offer|allow|take|sell|serve|provide|accept|permit|"
    r"charge)\b"
    # "is there parking at the hotel", "is there a cafe in the museum": the same ask with the
    # article left out, which is how people say it. The thing still has to be one of the place
    # words below, so "is there any chance" and "is there a god" keep their own answers.
    r"|\b(?:is|are)\s+there\s+(?:a\s+|any\s+)?"
    r"|\bcan\s+i\s+(?:bring|take|park|book|pay|use|get)\b"
    # "are the kids allowed in the beer garden": the ask is a permission put to a place, but
    # "are the kids allowed out" is a question about the children and names no place, so the
    # thing below still has to be one of the place words.
    r"|\b(?:are|is|were|was)\s+(?:the\s+|our\s+|your\s+)?"
    r"(?:dogs?|kids?|children|child|pets?)\s+(?:allowed|welcome|permitted)\b)", re.I)
# The lines that are a question about a place however they are put: nobody asks whether a dog
# is welcome at their own house.
PLACE_ASKS_OF_ITS_OWN = re.compile(
    # "are dogs allowed", "kids welcome", "dog friendly". The line has to open on it: "were the
    # kids ok" is a question about how the children are, and it keeps its own answer.
    #
    # The openers are every tense of the ask, and a determiner may sit in front of the animal or
    # the child: "were dogs allowed" and "are the dogs allowed" are the same question as "are
    # dogs allowed", and they fell through - `PLACE_ASKS` below already read the past tense, so
    # the reader matched and this gate threw the line away. "was the dog allowed in" is the same
    # ask about one animal.
    r"(?:^(?:oh |and |so |are |is |were |was |do |does |did )?"
    r"(?:the\s+|our\s+|your\s+|his\s+|her\s+)?(?:dogs?|kids?|children|child)\s+"
    r"(?:allowed|welcome|ok|okay)\b"
    # A permission asked of the place itself, with no animal in it: "is the pub in the village
    # dog friendly", "can i bring the dog in". The animal and the permission both have to be in
    # the line, and the permission verb is the one `PLACE_PERMISSION` holds.
    r"|\b(?:dog|kid|child|family)[\s-]?friendly\b"
    r"|\bdog[\s-]?friendly\b"
    r"|\b(?:is|are)\s+(?:it|they)\s+(?:good|ok|okay|suitable|fine)\s+for\b)", re.I)
# The things people ask a place about. The first list is a place's own business wherever it
# appears ("do they have a car park" needs no venue named); the second needs a place named in
# the line, because the same words belong to people and homes too ("does she have a dog",
# "is there wifi at my flat").
PLACE_OF_ITS_OWN = (
    "car park", "car parking", "parking", "toilets", "baby change", "takeaway", "take away",
    "beer garden", "play area", "soft play", "high chairs", "highchair", "dress code",
    "step free", "wheelchair access", "wheelchair", "accessible entrance", "table service",
    "cash only", "card only", "booking fee", "cover charge",
)
PLACE_WITH_A_VENUE = (
    "pool", "swimming pool", "dogs", "dog", "kids", "children", "child", "wifi", "wi-fi",
    "vegan", "gluten free", "vegetarian", "bookings", "booking", "tables", "music", "quiz",
    "screens", "garden", "food", "menu", "delivery", "parking", "rooms",
    # What a person wants to know about a place they are walking into: "does the museum have a
    # cafe", "is there a car park at the hotel", "does the gallery have lockers". These are all
    # the place's own fact, and without them the line fell to the search hedge.
    "cafe", "café", "coffee", "toilets", "toilet", "loo", "car park", "gift shop", "shop",
    "restaurant", "bar", "cloakroom", "lockers", "changing rooms", "baby change", "lifts",
    "step free access", "hearing loop", "picnic", "seating", "water",
)
# "does it allow dogs", "do they have a pool": the place was named in the last turn, so the
# thing arrives with nothing but a pronoun in front of it. Those words are a place's own
# business when the subject is "it" or "they"; "dog", "kid", "child" and "children" are left out
# on purpose, because "do they have a dog" and "do they have kids" are questions about a house
# or a family far more often than about a venue. They still count when a place is named, through
# PLACE_VENUES and PLACE_WITH_A_VENUE ("do the pub allow kids", "can i take the kids to the pub").
PLACE_ASKS_WITH_NO_SUBJECT = (
    "pool", "swimming pool", "wifi", "wi-fi", "vegan",
    "gluten free", "vegetarian", "bookings", "tables", "menu", "food", "delivery",
    "parking", "rooms",
)
# A dog is on both sides of the fence: "do they have dogs" is a household, and "do they allow
# dogs" is a venue or a landlord. The verb tells them apart, so the animal words count with a
# pronoun only when the ask is a permission put to whoever owns the place.
PLACE_ANIMALS = ("dogs", "dog")
PLACE_PERMISSION = re.compile(
    r"\b(?:allow|allows|allowed|take|takes|taking|taken|permit|permits|permitted|welcome|"
    r"welcomes|welcomed|accept|accepts|accepted|let|lets)\b", re.I)
# "do they let dogs in", "do they welcome pets": a verb the asks above do not read, with a dog
# in it, is the same ask - and only with the animal, because "do they let you bring your own
# food" is a different question and keeps its answer.
PLACE_LETS_ANIMALS = re.compile(
    r"\b(?:do|does|did)\s+(?:they|it)\s+(?:let|lets|welcome|welcomes)\b", re.I)
BARE_PLACE_SUBJECT = re.compile(r"\b(?:do|does|did)\s+(?:they|it)\b|\b(?:is|are)\s+(?:it|they)\b")
# "can i bring the dog", "can i take the kids to the pub": a permission to bring somebody to a
# place is that place's own rule. It is not one when the line names a place they go to anyway -
# "can i take the kids to school" is the school run, and it kept its own answer until this shape
# put a place line in front of it. So the destination decides: a place word from PLACE_VENUES, or
# no destination at all ("can i bring the dog in") - and "to school" has no article
# in front of it, so the destination is the word "to" itself.
A_BRING_ASK = re.compile(
    r"\b(?:can|could|may|am\s+i\s+allowed\s+to)\s+(?:i\s+|we\s+)?(?:bring|take)\b"
    r"[^.!?]{0,30}\b(?:dogs?|pets?|kids?|children|child|pram|buggy)\b", re.I)
A_DESTINATION = re.compile(r"\bto\b", re.I)
# A home of their own is not a venue: "is there wifi at my flat" and "is there parking at our
# house" are about the place they live, and the words "wifi" and "parking" are a venue's business
# only when a venue is named.
A_HOME_OF_THEIR_OWN = re.compile(
    r"\b(?:my|our|his|her|their|your)\s+(?:(?:new|own|old|little|small|big|rented)\s+)?"
    r"(?:flat|house|home|place|garden|car|van|caravan|room|office|desk)\b", re.I)
# "is there wifi", "is there food": the place is not named and there is no pronoun either, but the
# thing asked about is one a place has, so the answer is the same place's own yes or no.
PLACE_IS_THERE = re.compile(r"\b(?:is|are)\s+there\b")
PLACE_VENUES = (
    "pub", "restaurant", "cafe", "café", "coffee shop", "bar", "hotel", "b&b", "guest house",
    "campsite", "caravan site", "holiday park", "gym", "leisure centre", "swimming pool",
    "museum", "gallery", "cinema", "theatre", "venue", "shop", "store", "supermarket",
    "garden centre", "station", "salon", "barber", "hairdresser", "garage", "surgery",
    "dentist", "pharmacy", "church", "village hall", "zoo", "farm park", "library", "club",
    "spa", "soft play", "bowling", "snooker hall", "arcade",
)
# Every one of these leads with the thing the bot does know - that the answer is written down,
# and in which of the two places a place writes it - and only then where to look. "I can't check
# inside a particular place, sorry" plus a pointer is a shrug with a signpost on it (operators,
# #uncertainty): the useful part is that it is already on the page, under visiting, or in the
# terms if they are staying there.
PLACE_LINES = (
    "That is the place's own call, and it is usually written down: their own page lists it under "
    "visiting or facilities, and somewhere you are staying puts it in the booking terms. One "
    "phone call settles it either way.",
    "Whoever runs the place decides that, and it is one of the few things they all publish: their "
    "own page lists it under visiting or facilities, a phone call in opening hours gets a straight "
    "answer, and the booking terms cover a room.",
    "I can't see inside one particular place, so the answer is theirs: it will be on their page "
    "under visiting, or in the booking terms, and the phone settles anything the page leaves out.",
)


# Whether a market, a class, a match or a sale is ON is a different question from when a place
# opens, and none of the opening words read it: the "on" is the whole ask (is it happening).
# "is the market on this saturday", "is the club on tonight", "is the match on tonight", "is the
# 5 a side on tonight" and "is the boot sale on this week" all reached the search hedge, which is
# the worst reply for them: the organiser knows and posts it.
A_DAY = re.compile(
    r"\b(?:today|tonight|tomorrow|this\s+(?:week|weekend|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday)|next\s+week|the\s+weekend|weekends?|"
    r"bank\s+holiday(?:\s+monday)?|(?:mon|tues|wednes|thurs|fri|satur|sun)days?)\b")
# The ask has to put a subject in front of that day: "is <something> on <day>". "is the heating on
# tonight" and "is the telly on" are a switch, not an event, so a thing in the house stands it
# down, and "is my shift on tonight" names nothing a venue runs.
# The ask opens the line, the way the hours ask does, or it is a statement about a habit: "we do a
# quiz on a thursday" and "we were on the market on saturday" both put a subject in front of an
# "on" and were read as the question, which took a good answer's turn away. A "does" keeps the
# determiner that a bare "do a ..." does not have, so "does the club meet on wednesdays" is still
# read and "do a quiz on a thursday" is not.
ON_A_DAY = re.compile(
    r"^\s*(?:and|so|but|also|oh|hi|hello|quick one)?\s*,?\s*"
    r"(?:(?:is|are|will|was|were)\s+[^.!?]{1,40}?"
    r"|(?:does|do)\s+(?:the|that|this|our|your|their|his|her)\b[^.!?]{0,34}?)"
    r"\s+\b(?:on|running|happening|taking\s+place|going\s+ahead)\b")
# A clock ask ("is the pub open on sunday", "is the market open on fridays") already has its own
# pool - the opening hours, which says what the bot knows about hours - so it is not read here.
A_CLOCK_ASK = ("open", "opens", "opening", "opened", "close", "closes", "closing", "closed",
               "shut", "shuts", "shutting")
# "is the gym busy on mondays" wears the same "on <day>" shape as "is the market on saturday" and
# is a different question: how many people there are, which the queue note already answers. So do
# "is it crowded on sundays" and "which day is the gym quietest".
A_CROWD_ASK = ("busy", "busier", "busiest", "crowded", "packed", "rammed", "heaving", "quiet",
               "quieter", "quietest", "dead", "queues", "queue", "waiting", "how many people")
A_SWITCHED_ON_THING = (
    "heating", "boiler", "oven", "kettle", "telly", "tv", "television", "radio", "lights",
    "light", "lamp", "fan", "alarm", "immersion", "water", "hot water", "washing machine",
    "dishwasher", "tumble dryer", "dryer", "fridge", "freezer", "phone", "laptop", "fire",
    "shower", "radiator", "hob", "grill", "microwave", "sprinkler", "washer", "damp",
)
# What a day gets asked about: the things a person runs, not a shop's clock. A venue from the
# list above counts as well ("is the market on this saturday"), because a market is a place on
# the other days of the week.
PLACE_EVENTS = (
    "market", "boot sale", "car boot", "match", "game", "fixture", "class", "classes",
    "club night", "5 a side", "five a side", "concert", "gig", "show", "fair", "fete",
    "quiz", "sale", "service", "session", "sessions", "practice", "training", "meeting",
    "event", "festival", "parade", "funfair", "playgroup", "toddler group", "story time",
    "swim", "swimming", "lesson", "lessons", "course", "workshop", "jumble", "table top",
)
# The two things the bot does know about a day that moves, said before the pointer: why it moves,
# and who decides. A bare "check their page" is not a reply (operators, #uncertainty).
PLACE_ON_A_DAY_LINES = (
    "Whether it is on that day is the organiser's own call, and it is the last thing they "
    "change: a wet pitch, a stall that cannot come, a hall that falls through - and a bank "
    "holiday moves the day a market or a class runs. Their own page or a phone call on the "
    "morning gives the yes or no.",
    "That is settled on the day itself, not from here: a market, a match or a class is called "
    "off late when the weather turns, and a bank holiday can move it to another day. Their own "
    "page or listing is where the change goes up, and the phone is answered on the morning.",
    "Nobody could tell you that in advance from this end - whoever runs it decides late, for "
    "weather, a clash or a hall, and a holiday shifts the day. Their own page or a call on the "
    "morning is where the yes or no is.",
)
# Whether entry is free is the place's own price, on the day they ask about, and the one thing
# worth knowing before the pointer is what moves it: what is on, and the season.
A_FREE_ASK = re.compile(
    r"\b(?:is|are|was|were)\s+(?:it|that|this|the|a|an|my|our|your)?[\s\w'-]{0,24}?\bfree\b"
    r"|\bfree\s+(?:entry|admission|to\s+get\s+in|on\s+(?:mon|tues|wednes|thurs|fri|satur|sun))\b"
    r"|\b(?:do|does)\s+(?:you|i|they|we)\s+(?:have\s+to\s+|need\s+to\s+)?pay\b")
# A pool line has to fit every line that reaches it: the free asks are a car park, a pool, a
# campsite, a gym, a leisure centre and a museum alike, so no line here names a thing only a
# gallery has ("a touring show", "the permanent collection"). The words that stay are the ones
# true of any price - what is on, who is going, and the season.
PLACE_FREE_LINES = (
    "Whether it is free is the place's own rule and it moves with the season: some of what is "
    "there is charged even when the rest is not, and the free days change through the year. "
    "Their own site puts the price and any free day under visiting or opening times.",
    "That varies with what is on and with who is going: an event day, a member's rate and a "
    "child's rate each carry their own price, and the place sets them. Their own page lists the "
    "price for the day you are going.",
    "I can't see a place's prices from here, and they are not fixed - what is on and the time of "
    "year both change them. Their own page lists the ticket price, the free days and any "
    "concession, and the desk confirms it on the phone.",
)


def _bounded(phrase):
    return re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])")


def _has(clean, phrases):
    """True when one of these phrases is in the line as whole words."""
    for phrase in phrases:
        if _bounded(phrase).search(clean):
            return True
    return False


def _a_place_they_are_bringing_somebody_to(clean):
    """True when the line asks to bring an animal or a child to a place it names."""
    if not A_BRING_ASK.search(clean):
        return False
    if A_DESTINATION.search(clean) and not _has(clean, PLACE_VENUES):
        return False   # "can i take the kids to school" is the school run, not a venue's rule
    return True


# What a place publishes about itself rather than runs: wifi, a cafe, lockers. A calendar ask that
# carries one of these is about the facilities list, not the day, so this reader stands down.
#
# `parking` is deliberately NOT here. The note that owns it reads any rate word as a price
# question, so "is there parking at the hotel" came back with "the headline rate is only half of
# it: an evening or weekend price, a day cap" - an answer to a question nobody asked, when the
# place's own line ("it is written down under visiting or facilities, and the phone settles it")
# is the true one. The place line answers that now, because this list no longer hands it back.
PLACE_FACILITIES = frozenset("""
    wifi wi-fi toilets toilet loo loos baby changing lockers locker cafe caf restaurant
    shop food drink cash machine atm cloakroom
""".split())
# A fixture is announced by the club and moves for television, so "is the match on tonight" has a
# note of its own: a market or a quiz runs to the organiser's calendar, a fixture does not.
A_FIXTURE = re.compile(r"\bmatch(?:es)?\b|\bfixtures?\b|\bkick[\s-]?offs?\b|\bthe\s+game\b",
                        re.I)
# ... while a market, a stall or a class does keep to the organiser's calendar, so a line about one
# of those is still read here even when the word "match" turns up somewhere in it.
A_RUNS_TO_A_CALENDAR = re.compile(
    r"\b(?:market|boot sale|car boot|stall|fete|fair|jumble|table top|quiz|class|classes|"
    r"session|sessions|group|club)\b", re.I)


# A day that comes round is a timetable, not a plan for one day: "does the club meet on
# wednesdays", "is the class on wednesdays", "is the market on fridays". The day lines below are
# about one day - whether it is still on, or called off late - so a standing day is not read here
# at all. A single day ("is the club on tonight", "on this saturday") still is.
A_STANDING_DAY = re.compile(
    r"\b(?:(?:mon|tues|wednes|thurs|fri|satur|sun)days|weekends|every\s+[a-z]+)\b", re.I)


def the_line(clean):
    """The honest line for a fact that belongs to one place, or None."""
    if A_HOME_OF_THEIR_OWN.search(clean) and not _has(clean, PLACE_VENUES):
        # Their own house, flat or car is not a venue: it takes no bookings and publishes no
        # facilities page, so every line below would be about somewhere it is not.
        return None
    if PLACE_IS_THERE.search(clean) and _has(clean, PLACE_FACILITIES):
        return None
    if A_FIXTURE.search(clean) and not A_RUNS_TO_A_CALENDAR.search(clean):
        return None
    of_its_own = bool(PLACE_ASKS_OF_ITS_OWN.search(clean))
    bringing = _a_place_they_are_bringing_somebody_to(clean)
    lets_animals = bool(PLACE_LETS_ANIMALS.search(clean) and _has(clean, PLACE_ANIMALS))
    if not (of_its_own or bringing or lets_animals or PLACE_ASKS.search(clean)):
        # A day ask names no do/does/is-there shape at all ("is the market on this saturday"),
        # so it is read here rather than left to the search hedge. It is asked after the asks
        # above: "do they have a pool on sunday" is still the pool.
        return _a_day_ask(clean)
    if not (of_its_own
            or bringing
            or lets_animals
            or _has(clean, PLACE_OF_ITS_OWN)
            or (_has(clean, PLACE_VENUES) and _has(clean, PLACE_WITH_A_VENUE))
            or (BARE_PLACE_SUBJECT.search(clean)
                and _has(clean, PLACE_ASKS_WITH_NO_SUBJECT))
            or (PLACE_IS_THERE.search(clean) and _has(clean, PLACE_ASKS_WITH_NO_SUBJECT)
                and not (A_HOME_OF_THEIR_OWN.search(clean) and not _has(clean, PLACE_VENUES)))
            # "do they allow dogs", "does it take pets": a permission, not a household.
            or (BARE_PLACE_SUBJECT.search(clean)
                and _has(clean, PLACE_ANIMALS) and PLACE_PERMISSION.search(clean))):
        # "is there a market on saturday" and "is the pub free on sunday" wear one of the shapes
        # above and are still the day's question, so they are read here before the drop.
        return _a_day_ask(clean)
    return PLACE_LINES


def _a_day_ask(clean):
    """The lines for a place or an event asked about on a named day, or None.

    Read after the asks above, because "is the pub free on sunday" is both a price and a place's
    fact and the price is the part the person is asking.
    """
    if _has(clean, A_CLOCK_ASK):
        return None
    if A_FREE_ASK.search(clean) and (_has(clean, PLACE_VENUES) or _has(clean, PLACE_EVENTS)
                                     or A_DAY.search(clean)):
        # "is it free to park" and "is the wifi free" carry no day and no price worth chasing
        # here; the words for those are the place's own business and keep PLACE_LINES.
        if not _has(clean, A_SWITCHED_ON_THING):
            return PLACE_FREE_LINES
    if _has(clean, A_CROWD_ASK):
        return None
    if A_STANDING_DAY.search(clean):
        # The day lines below are about one day - still on, or called off late - so a day that
        # comes round every week is not read here. The free lines above are about a rule, which a
        # standing day does not change.
        return None
    if not (ON_A_DAY.search(clean) and A_DAY.search(clean)):
        return None
    if _has(clean, A_SWITCHED_ON_THING):
        return None
    if not (_has(clean, PLACE_VENUES) or _has(clean, PLACE_EVENTS)):
        return None
    return PLACE_ON_A_DAY_LINES
