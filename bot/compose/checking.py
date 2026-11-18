"""The things the bot cannot see, and the one place that does see them.

The floor of this bot is one reply for everything nobody knows, and on main that reply is the
honest shrug: "I'm not sure about that one, sorry - a quick search online will get you a solid
answer". It is honest, and it is useless to somebody who asked a question with a *place* behind
it. STYLE.md draws the line this module sits on:

    What time does the post office on Hill Road close today?
    I can't check live opening hours, sorry. Search for the branch online: its listing on a map
    app usually shows today's hours, holidays included.

Three things make that reply good, and none of them is in the shrug: it says what the bot cannot
do (check live hours), it names the one place that can (the branch's listing on a map app), and it
does not guess. The pool cannot do that for every line - it does not know what the line is about -
so this module reads the line for the *kind* of thing being asked about and gives the limit, the
place to look and, where it helps, one short question.

    is it on iplayer                      "I can't see what's on iPlayer from here, sorry..."
    what time is the last train to leeds  "...no live train times from me - a journey planner..."
    whats the best beach in cornwall      "...I don't know the beaches round there well enough..."
    how about moving to spain             "...it depends on your passport - gov.uk's living
                                           abroad pages and the country's own official site..."
    will it frost tonight                 "...no live weather from me - a forecast app has
                                           today's, hour by hour..."

Six kinds are here and no more, because each one has either a *named* place that knows or a list
the bot has already given, and that is what makes the reply worth more than a search: a service's
own catalogue, a journey planner, the place's own listing, the government that writes the rules,
the sky over the person's own postcode, and - the sixth - the checks the bot itself named a turn or
two ago, handed back when the person asks what to check before they commit.
Anything else stands down (returns None) and the floor answers as it did before.

Two more were added after the operator's note that a pointer on its own is not an answer: a choice
between two named things, and an ask for a shortlist. Neither names a subject - that is exactly
what the line does not have - so each one says the part that is true of every question of its
shape, what to look for and the usual first step, and then asks the one thing only the person
knows. That is STYLE.md's "what to look for" half of "Not knowing, honestly", and it comes before
any mention of where the rest lives.

This is a last resort and it is written to be one: `bot/modules/greeting.py` asks it alongside the
detail of an answer and the composer, and the composer is asked first, so a line any entry, any
module or the composer can answer never reaches this file. What it can lose is a line the shrug
would have got; what it cannot do is take a turn away from a better answer, or invent a fact to
fill the gap. Nothing here is a fact about the world: every reply says only what the bot cannot
check, what decides a thing of that kind, and where a person can find the rest.
"""
import re

from ..memory.facts import COUNTRIES

# Moving to one of these is a move at home: the paperwork for living abroad is not the answer.
HOME_NATIONS = frozenset("""england scotland wales britain uk ireland northern ireland""".split())
from . import pick

# The countries that are not the one whose council answers a bin or a pothole question. A named
# country is the cheapest way to know a thread has left the UK: "we live in spain now" carries no
# word `ABROAD` can see, and "what about the bins" after it is not a question for a council.
HOME_COUNTRIES = frozenset((
    "united kingdom", "england", "scotland", "wales", "northern ireland", "great britain",
    "britain", "uk", "ireland",
))
NOT_HOME_COUNTRIES = tuple(sorted(
    (name for name in COUNTRIES if name not in HOME_COUNTRIES), key=len, reverse=True))
# The names of the countries a move could be going to, longest first so "south sudan" is not read
# as "sudan". They are the knowledge base's own table, read the first time a line asks about the
# rules rather than at import: the table is big and most conversations never come near it. Only the
# UK's own names are left out - moving to Ireland or to Holland is a move somewhere else, moving
# to Leeds or to Edinburgh is not.
MOVE_HOME_NAMES = frozenset((
    "united kingdom", "england", "scotland", "wales", "northern ireland", "great britain",
    "britain", "uk",
))
_A_NAMED_COUNTRY = None


def _a_named_country_in(text):
    """True when the line names a country other than this one."""
    global _A_NAMED_COUNTRY
    if _A_NAMED_COUNTRY is None:
        from ..knowledge.geography import COUNTRIES as all_countries, _COUNTRY_ALIASES
        names = sorted((set(all_countries) | set(_COUNTRY_ALIASES)) - MOVE_HOME_NAMES,
                       key=len, reverse=True)
        _A_NAMED_COUNTRY = re.compile(
            r"\b(?:" + "|".join(re.escape(name) for name in names) + r")\b", re.I)
    return bool(_A_NAMED_COUNTRY.search(text or ""))

# The services whose catalogue the bot cannot see. Named the way people type them, with the form
# the reply uses - "iplayer" is "iPlayer" on screen and "bbc" alone is not a service.
SERVICES = (
    ("iplayer", "iPlayer"), ("bbc iplayer", "iPlayer"), ("itv hub", "ITV Hub"),
    ("itvx", "ITVX"), ("itv", "ITV"), ("channel 4", "Channel 4"), ("all 4", "All 4"),
    ("4od", "All 4"), ("my5", "My5"), ("netflix", "Netflix"), ("prime video", "Prime Video"),
    ("amazon prime", "Prime Video"), ("disney plus", "Disney+"),
    ("disney+", "Disney+"), ("now tv", "Now TV"), ("nowtv", "Now TV"), ("apple tv", "Apple TV"),
    ("paramount", "Paramount+"), ("britbox", "BritBox"), ("hayu", "Hayu"), ("sky go", "Sky Go"),
    ("sky q", "Sky Q"), ("sky tv", "Sky"), ("sky cinema", "Sky Cinema"),
    ("sky sports", "Sky Sports"), ("spotify", "Spotify"), ("audible", "Audible"),
    ("youtube", "YouTube"),
)
# The ask that makes a service a lookup: whether the thing is on it. A fault ("netflix keeps
# stopping"), a password, a price or a subscription is another question, and 4 of the 10 lines in
# this file's test that name a service are one of those, so the availability shape is required.
# What is not this reading however it is asked: a fault, the money, the account, the choice.
NOT_AVAILABILITY = re.compile(
    r"\b(?:stopping|stops|stopped|buffer\w*|glitch\w*|not working|keeps? (?:cutting|freezing|"
    r"loading)|wont play|won't play|password|log ?in|sign ?up|account|cancel\w*|subscri\w*|"
    r"price|prices|cost|costs|cheaper|worth it|share|sharing|binge|download\w*|aeroplane|"
    r"plane|offline|recommend|any good|what to watch|something to watch|worth watch\w*|"
    r"turn (?:off|on)|settings|autoplay|auto play|notification\w*|episodes? (?:left|to go)|"
    # "anything funny on netflix" is asking to be told about a film, which is a recommendation
    # and not a lookup.
    r"(?:anything|something|whats|what's)\s+(?:\w+\s+){0,2}(?:funny|good|scary|sad|new|"
    r"decent|chilled|violent|easy)\b|"
    r"what (?:can|could|should) (?:i|we) (?:watch|see|stream)|"
    r"(?:anything|something) (?:good )?(?:on|to watch))\b", re.I)

# A journey the bot cannot time: the mode, and the ask that wants a time or a yes/no about one.
TRAVEL = {
    "train": ("train", "trains"), "trains": ("train", "trains"), "bus": ("bus", "buses"),
    "buses": ("bus", "buses"), "coach": ("coach", "coaches"), "tube": ("tube", ""),
    "underground": ("tube", ""), "metro": ("metro", ""), "tram": ("tram", "trams"),
    "ferry": ("ferry", "ferries"), "ferries": ("ferry", "ferries"),
}

# "how do i get to bristol from cardiff" names no train and is still a journey: the route is the
# question. Both ends are required, so "how do i get to sleep" and "how do i get to work" (which
# are about a thing and a habit) are not this reading.
# Both ends are required, so "how do i get to sleep", "get to work" and "get to the gym" - a
# thing and two habits - are not this reading. The "from" is what makes it a journey.
# The superlative is the same question as "best way": a person asking the quickest way to get
# somewhere from somewhere else is asking for the route, and the reading held only the word
# "best", so "wats the quickest way to get to heathrow from ealing" reached the search hedge
# while "whats the best way to get to heathrow from ealing" got the route card. What matters is
# not which superlative it is - it is that both ends are named and the word before "way" or
# "route" is a comparison, so the two ends do the work and the adverb is a class, not a list.
_A_COMPARISON = (r"(?:best|quickest|fastest|easiest|cheapest|simplest|shortest|safest|"
                 r"most direct|nicest|prettiest)")
GET_FROM_TO = re.compile(
    r"\bhow (?:do|can|would|could) (?:i|we|you) (?:get|travel)\s+(?:to|from)\b[^?.]{0,30}\bfrom\b|"
    # "the fastest route to leeds from manchester" names both ends and no verb, and it hedged.
    # The noun has to be one that is about places - a route, a journey, a drive - because "way"
    # is not: "the best way to make bread from scratch" and "the quickest way to get over a cold
    # from day one" have the same shape and are about something else entirely.
    r"\b(?:" + _A_COMPARISON + r"\s+)?(?:route|journey|drive|commute)\s+to\b[^?.]{0,30}\bfrom\b|"
    r"\b" + _A_COMPARISON + r"\s+(?:way|route)\s+(?:to|of)\s+(?:get|getting|travel|travelling)"
    r"\s+(?:to|from)\b[^?.]{0,30}\bfrom\b|"
    r"\b" + _A_COMPARISON + r"\s+(?:way|route)\s+from\b[^?.]{0,30}\bto\b|"
    r"\b" + _A_COMPARISON + r"\s+(?:way|route)\s+(?:to|of)\s+(?:get|getting|travel|travelling)"
    r"\s+from\b[^?.]{0,30}\bto\b|"
    r"\bhow long (?:does it|will it|would it) take to (?:get|drive|travel|cycle|walk)\s+to\b"
    r"[^?.]{0,30}\bfrom\b|"
    r"\bhow (?:do|can|would|could) (?:i|we|you) (?:get|travel)\s+from\b[^?.]{0,30}\bto\b", re.I)
WANTS_A_TIME = re.compile(
    r"\b(?:what time|whatt?ime|how long|last|first|next|earliest|latest|timetable|doable|"
    r"won'?t make|is there a|are there any|how often)\b", re.I)
# "the last train to leeds" is this reading. A train that is late, a ticket price, a seat and a
# season ticket are all questions with an answer of their own, and the bot has them.
# A destination that is not a place: "the quickest way to get to sleep from a busy day" and "the
# best way to get to grips with it from here" are about a thing, not a journey, and the two ends
# being named does not make them one. Only the widened superlative can reach these - the old
# "best way to get to X from Y" did not hold "sleep" often enough to matter - so the words that
# make a destination a figure of speech are listed rather than guessed at.
NOT_A_DESTINATION = re.compile(
    r"\bget(?:ting)?\s+(?:to\s+)?(?:sleep|rid|grips|know|understand|talk|the\s+(?:point|bottom)|"
    r"terms|an?\s+agreement|a\s+decision|the\s+root)\b|"
    r"\bget(?:ting)?\s+(?:over|through|around|on\s+top\s+of|out\s+of|away\s+with|the\s+hang)\b",
    re.I)
NOT_A_JOURNEY = re.compile(
    r"\b(?:delayed|delay|cancelled|cancel|refund|ticket price|how much is .{0,20}ticket|"
    r"season ticket|railcard|strike|replacement bus|sleeper|i'?m on (?:the|a) "
    r"(?:train|bus)|on the (?:train|bus)|lost property|left (?:my|her|his) \w+ on)\b", re.I)

# A pick in a place: the thing to pick, and the noun the reply uses for it.
PICKS = (
    (("beach", "beaches"), "beaches"),
    (("pub", "pubs"), "pubs"),
    (("restaurant", "restaurants", "place to eat", "places to eat", "eatery"), "restaurants"),
    (("cafe", "cafes", "coffee shop", "coffee shops"), "cafes"),
    (("walk", "walks", "hike", "hikes"), "walks"),
    (("park", "parks"), "parks"),
    (("market", "markets"), "markets"),
    (("museum", "museums", "gallery", "galleries"), "museums and galleries"),
    (("chippy", "chippies"), "chip shops"),
    (("thing to do", "things to do", "day out", "day trip"), "things to do"),
)
# A shop's own facts - what it has, what it charges, when it delivers - are the shop's to know,
# and the bot has no window on any of them. The name is what makes the reply worth more than a
# search: "how long does aldi delivery take" gets the shop and the place on its site, not a shrug.
SHOPS = (
    ("aldi", "Aldi"), ("lidl", "Lidl"), ("tesco", "Tesco"), ("asda", "Asda"),
    ("sainsbury's", "Sainsbury's"), ("sainsburys", "Sainsbury's"), ("morrisons", "Morrisons"),
    ("waitrose", "Waitrose"), ("iceland", "Iceland"), ("co-op", "the Co-op"), ("coop", "the Co-op"),
    ("boots", "Boots"), ("superdrug", "Superdrug"), ("argos", "Argos"), ("amazon", "Amazon"),
    ("ebay", "eBay"), ("ikea", "IKEA"), ("currys", "Currys"), ("screwfix", "Screwfix"),
    ("b&q", "B&Q"), ("b and q", "B&Q"), ("homebase", "Homebase"), ("wickes", "Wickes"),
    ("halfords", "Halfords"), ("decathlon", "Decathlon"), ("sports direct", "Sports Direct"),
    ("john lewis", "John Lewis"), ("marks and spencer", "Marks and Spencer"), ("m&s", "M&S"),
    ("poundland", "Poundland"), ("home bargains", "Home Bargains"), ("the range", "The Range"),
    ("dunelm", "Dunelm"), ("asos", "ASOS"), ("wickes", "Wickes"),
)
SHOP_ASK = re.compile(
    r"\b(?:how long|how much|do they|do you|does it|can i|when|delivery|deliver|in stock|"
    r"stock|return|returns|refund|click and collect|collect|charge|postage|warranty|"
    r"guarantee|trade ?in|price|prices|cost)\b", re.I)
# The word that makes a pick word a place is the company it keeps: "a good beach read", "where
# should i park the car" and "the best way to walk the dog" are a book, a car and a dog, and a
# list of beaches, car parks and walks is the wrong answer to all three.
PICK_NOT = {
    "beach": re.compile(r"\b(?:read|reads|book|books|novel|towel|body|volleyball|ball|hut|"
                        r"huts|wedding|holiday\s+read)\b", re.I),
    "park": re.compile(r"\b(?:the car|my car|your car|the van|the bike|it there|carefully|"
                       r"properly|legally)\b", re.I),
    "walk": re.compile(r"\b(?:the dog|my dog|to work|to school|home|back|the kids to|"
                       r"take|taking|wear|wearing|bring|bringing|pack|packing|carry|boots|"
                       r"shoes|rain|wet|long|short|slow|fast|bit of a)\b", re.I),
    "market": re.compile(r"\b(?:the car|to buy|flog|sell)\b", re.I),
    "thing to do": re.compile(r"\b(?:with it|with them|with the|today|tonight|now|this evening|"
                              r"picnic|take|bring|pack)\b", re.I),
    "restaurant": re.compile(r"\b(?:wear|wearing|wore|dress|order|book a table|booking)\b", re.I),
    "chippy": re.compile(r"\b(?:order|nice from|to have|whats nice|what is nice)\b", re.I),
}
# A pick is a pick *in a place*: without one the question is "what should i do with half an hour",
# which is not a list of places to go. The place can be on the turn before this one ("we're going
# to cornwall in august" then "any good beaches for the kids").
# A time of day is not a place, and it is the word a preposition of place most often lands on
# when somebody asks what to do rather than where to go: "what do i do at dinner time" after a
# feeding question was read as a place name and answered with the day-out shape ("one thing worth
# the journey out, one long lunch"), and "what should i do in the evening" the same way. The words
# below name a part of the day, a meal or a routine, so a preposition in front of one is telling
# you when, not where; `time` is here for the same reason, it is never a place. The article is
# stepped over first, because "in the evening" and "at the weekend" are the same time as
# "in evening" and the place reading was landing on `the`. The weekend is deliberately not here: a
# weekend ask is served well by the day-out shape, which is about a day and not about a meal.
A_TIME_NOT_A_PLACE = (
    r"(?:dinner|dinnertime|dinner\s+time|lunch|lunchtime|lunch\s+time|breakfast|"
    r"breakfast\s+time|tea|teatime|tea\s+time|supper|brunch|snack|elevenses|"
    r"bed|bedtime|bed\s+time|nap|naptime|nap\s+time|playtime|play\s+time|bathtime|"
    r"bath\s+time|homework|pickup|pick\s+up|school\s+run|morning|mornings|afternoon|"
    r"afternoons|evening|evenings|night|nights|tonight|midday|noon|time)")
# The words a preposition of place can land on that are not places: the verbs the pick reading
# already refused, and the times above. "in times square" is a square and stays one - the word
# boundary keeps `time` from eating `times`.
#
# `day`, `days`, `week` and `weeks` are deliberately NOT in the list, on `weekend`'s reasoning: "in
# the day" and "in the week" ask about a stretch of time to fill, which is exactly what the day-out
# shape is written for, and `A_PART_OF_DAY` names no such thing - refusing them took the trigger off
# "what should i do in the day" and left it on the search hedge (plain-hippo's read of this).
A_NOT_A_PLACE = (
    r"(?:(?:the|a|an)\s+)?"
    r"(?:eat|go|walk|do|take|get|see|find|pick|order|book|be|have|" + A_TIME_NOT_A_PLACE + r")\b")
A_PLACE = re.compile(
    r"\b(?:in|near|around|round|at|by|beside|from|to|outside|inside)\s+"
    r"(?!" + A_NOT_A_PLACE + r")[a-z]", re.I)
WANTS_A_PICK = re.compile(
    r"\b(?:best|good|nice|decent|any good|recommend|worth|where should|what should|"
    r"suggest|anywhere|favourite|favorite|top)\b", re.I)

# A day out is not a pick the bot can be wrong about: it cannot name a beach or a museum, but the
# shape of a day and the question that decides it are honest and useful, and it is the follow-up
# its own invitation asks for ("where to stay or what to do while you are there?").
# A meal or a part of the day is a time, and "what do i do at dinner time" is an ask about a plan
# for that time. Read as a place it was answered with the day-out shape ("one thing worth the
# journey out, one long lunch"), which is a day, and refusing it left the search hedge - neither is
# an answer. What the bot does know is the shape of that part of the day, which is the same in most
# houses, and the one question that decides it.
A_MEAL_TIME = re.compile(
    r"\b(?:at|for|before|after|around|over)\s+(?:the\s+|my\s+|our\s+)?"
    r"(?:dinner|dinner\s*time|lunch|lunch\s*time|breakfast|breakfast\s*time|tea|tea\s*time|"
    r"supper|supper\s*time|brunch|tea ?time)\b", re.I)
# "this morning" and "tomorrow afternoon" name a part of the day as plainly as "in the morning"
# does, and a real line arrives with the apostrophe stripped ("what s on this morning").
A_PART_OF_DAY = re.compile(
    r"\b(?:at|in|during|over|before|after|this|tomorrow|next)\s+"
    r"(?:the\s+|my\s+|our\s+)?"
    r"(?:morning|afternoon|evening|night|midday|noon|bedtime)\b", re.I)
# The ask is what to *do*, not what to cook or eat: "what should i cook in the evening" has a card
# of its own and keeps it.
WANTS_A_PLAN = re.compile(
    r"\b(?:what|anything|any|how)\b[^?]{0,32}\b(?:should|shall|can|could|do)\s+(?:i|we)\s+do\b"
    r"|\bwhat\s+to\s+do\b|\bhow\s+(?:do|should)\s+(?:i|we)\s+(?:fill|pass|plan|spend)\b"
    r"|\banything\s+(?:to\s+do|planned|on|happening)\b"
    r"|\bwhat(?:'s|s|\s+s|\s+is|\s+else\s+is)?\s+(?:on|happening|going\s+on|good\s+to\s+do)\b",
    re.I)
# "what's on" and "what's happening" ask about the place, not about what to do with the time: a
# meal named in the same line ("whats on at lunchtime") is when they are asking about, and the
# food answer ("tell me what is in the house") is an answer to a different question. The frame is
# read first and decides the pool, whatever time was named (@plain-hippo's read on #12919).
AN_ON_ASK = re.compile(
    r"\bwhat(?:'s|s|\s+s|\s+is|\s+else\s+is)?\s+(?:on|happening|going\s+on)\b"
    r"|\banything\s+(?:on|happening)\b", re.I)
MEAL_TIME_POOL = (
    "Meals are the part worth pinning down: decide the one thing you are eating and keep the rest "
    "plain, and the time sorts itself out. What have you got in the fridge?",
    "At that time of day the trap is deciding it late. Pick the food first - something you can do "
    "with one pan is plenty - and let the rest of it be whatever it is. What do you fancy?",
    "One thing cooked and one thing cold is a meal, and it takes about twenty minutes. Tell me "
    "what is in the house and I will say which of them to use.",
)
PART_OF_DAY_POOL = (
    "The part of the day that works has one thing in it you actually want to do, and nothing else "
    "booked round it. What would that one thing be?",
    "Fill it from the other end: what would you be sorry to have missed by bedtime? That is the "
    "one thing, and the rest of the time can look after itself. What sounds good?",
    "Days like that are easier when the shape is set rather than the plan: one thing out of the "
    "house, one meal, and the rest left loose. What kind of thing do you enjoy doing?",
)


def _a_time_of_day(said):
    """The reply for a plan asked about a meal or a part of the day, or None.

    Only a line that names a time and asks what to do with it. A place named as well as the time
    ("what should we do in the evening in rome") is the day-out reading's, a person or a ward is
    not a plan at all, and a line that asks what to cook has a card of its own.
    """
    if not said:
        return None
    meal = A_MEAL_TIME.search(said)
    part = A_PART_OF_DAY.search(said)
    if not (meal or part) or not WANTS_A_PLAN.search(said):
        return None
    if NOT_A_DAY_OUT_PLACE.search(said):
        return None
    rest = said
    for match in (meal, part):
        if match:
            rest = rest.replace(match.group(0), " ")
    if A_PLACE.search(rest) or A_PLACE_THERE.search(rest):
        return None
    # A meal time is the meal pool only when the ask was about the time; a "what's on at
    # lunchtime" is about what is happening, and "one thing cooked and one thing cold" is the
    # wrong half of that.
    meal_pool = meal and not AN_ON_ASK.search(said)
    return pick(MEAL_TIME_POOL if meal_pool else PART_OF_DAY_POOL, {}, said)


THINGS_TO_DO_POOL = (
    "A day that works most places is one big thing in the morning and nothing booked after "
    "it, though I don't know this place well enough to name the things: one worth the journey "
    "out, one long lunch, the rest loose. What do you usually enjoy doing?",
    "Naming places I have not been to would be guessing, so here is the shape of a day "
    "instead: one big thing in the morning, one long lunch, and nothing booked after it. Are "
    "you after coast and walking, or food and towns?",
    "Pick the one thing you would be sorry to miss and plan the day round that, though I "
    "can't recommend places I have not been to: it decides where you stay, when you eat and "
    "what you drop. What sort of thing do you like doing?",
)
# A day out asked about the place the conversation is already in: "what should i do there",
# "anything good to do while we are there", "what should we see in rome". The line names the
# thing wanted (a day) and not the place, because the place was named a turn or two ago - the
# same follow-up the pick reading above is written for, one step wider (a day, not a beach).
# The two shapes of the ask: the thing wanted ("anything to do there", "things to do with the
# kids") and the open question ("what should we do there", "what should i see in rome").
WANTS_A_THING_DONE = re.compile(
    r"\b(?:what|anything|something|where)\b[^?.!]{0,18}\b(?:to do|to see|to visit)\b|"
    r"\b(?:things|stuff) to do\b", re.I)
ASKS_WHAT_TO_DO = re.compile(
    r"\bwhat (?:should|shall|can|could|do) (?:i|we|you) do\b|"
    r"\bwhat (?:should|shall|can|could) (?:i|we|you) (?:see|visit)\b|"
    r"\bwhats there to do\b|\bwhat is there to do\b", re.I)
WANTS_A_DAY_OUT = re.compile(
    WANTS_A_THING_DONE.pattern + "|" + ASKS_WHAT_TO_DO.pattern, re.I)
# "what should i do about my knee", "what can i do with an old laptop" and "what should i do
# tonight" are not a day out: an ask about a thing, and a line with no place in it at all, both
# stay with whatever answers them. The "with" half only stands a *do*-ask down: "anything to do
# with the kids" is the day out, and "what should i do with the kids" is the question about the
# thing in hand that another card answers.
DAY_OUT_NOT = re.compile(
    r"\b(?:about|to (?:sleep|stop|help|get|fix|make|keep)|for (?:my|the) )|"
    # a day at home is the house's business, not a place to visit
    r"\b(?:in|at|round|around) the (?:morning|afternoon|evening|night|weekend|meantime|garden|"
    r"kitchen|office|house|home|shed|garage|bedroom|bathroom|flat|car|shower|bath)\b", re.I)
A_THING_IN_HAND = re.compile(
    r"\bwith (?:it|them|him|her|this|that|an?|a)\b|"
    # a group of people is not a thing in hand: "what should i do with the kids" away for a week
    # is the day out, and "what should i do with my knee" is not
    r"\bwith (?:the|my) (?!kids|children|family|parents|boys|girls|toddler|baby|dog|"
    r"grandparents|grandchildren|niece|nephew|in-laws)\w+", re.I)
# "there" and "here" are the place: the line has no name in it, and the thread does.
A_PLACE_THERE = re.compile(r"\b(?:there|here|nearby|round here|around here)\b", re.I)
# The ask on its own, with no place word at all: "im going to spain in july" then "what should we
# see". It is the same follow-up as "what should we see there", and the trip in the thread is what
# makes it one.
A_BARE_DAY_OUT = re.compile(
    r"^\W*(?:(?:so|and|ok|okay|right|then|also|but)[\s,]+)*"
    r"(?:what|anything|something)\b[^?.!]{0,18}\b(?:to do|to see|to visit)\b|"
    r"^\W*(?:(?:so|and|ok|okay|right|then|also|but)[\s,]+)*"
    r"(?:things|stuff) to do\b|"
    r"^\W*(?:(?:so|and|ok|okay|right|then|also|but)[\s,]+)*"
    r"(?:what|where) (?:should|shall|can|could|do) (?:i|we|you) (?:do|see|visit)\b", re.I)
# The line that put a trip on the table: a place the person is going to, which is what "there"
# means for the turns after it.
A_TRIP_BEFORE = re.compile(
    r"\b(?:going to|going away|off to|flying to|driving to|heading to|travelling to|traveling to|"
    r"holiday|holidays|trip to|weekend in|week in|fortnight in|visiting|booked|days in)\b", re.I)
# A visit to see somebody, or somewhere nobody goes for a day out: "visiting my mum in hospital"
# then "what should i do there" is the ward's question, not a list of things to see.
NOT_A_DAY_OUT_PLACE = re.compile(
    r"\b(?:hospital|doctors?|dentist|gp|clinic|ward|surgery|a&e|court|work|school|nursery|"
    r"college|uni|university|interview|funeral|wedding|christening|prison|jail|care home|"
    r"vets?|physio|therapist|my mum|my dad|my sister|my brother|my son|my daughter|my kids|"
    r"my gran|my nan|my grandma|my grandad|my husband|my wife)\b", re.I)

# The rules that depend on who you are, split by who writes them: an official site about being
# somewhere else, and the council that decides a local rule.
# Moving is only a country when there is somewhere to move *to*: "move the money", "moving my
# photos to a new phone" and "change my address after moving" are not visa questions.
# A time after "to" or "in" is not a country: "my landlord says we have to move out in two
# months" put "move ... in two months" into the branch below, and three turns later "who do i
# write to" was answered with the gov.uk living-abroad pages. A move *out* is a tenancy, and a
# date, a month or "next year" names no destination at all.
A_TIME_AFTER = (
    r"(?!\s*(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"a\s+few|few|a\s+couple|next|this|last|the\s+(?:next|new|coming|end)|"
    r"january|february|march|april|may|june|july|august|september|october|november|"
    r"december|spring|summer|autumn|winter)\b)")
ABROAD = re.compile(
    r"\b(?:abroad|overseas|emigrat\w*|expat\w*|visa|residency|passport for|work permit|"
    r"right to (?:live|work)|liv(?:e|ing) abroad|work(?:ing)? abroad)\b"
    r"|\b(?:relocat|retir|buy(?:ing)? (?:a|an) (?:house|flat|place))\w*\b[^?.]{0,25}"
    r"\b(?:to|in|abroad)\b" + A_TIME_AFTER +
    r"|\bmov\w*\b(?!\s*out\b)[^?.]{0,25}\b(?:to|in|abroad)\b" + A_TIME_AFTER, re.I)
# The move on its own, with the text after it kept: the destination is the part that decides
# whether this is a plan to live somewhere else or the town the person already lives in.
# `_the_home_town` reads this and `GOING_AWAY` below, and nothing else defines them: a rewrite of
# `ABROAD` took both with it, and a name read and not defined raises inside the arbiter's try, so
# the whole move-and-paperwork reading went quiet - "what paperwork do i need" after two moves was
# answered "Hello!" on main.
MOVING = re.compile(
    r"\b(?:mov|relocat|retir|buy(?:ing)? (?:a|an) (?:house|flat|place))\w*\b[^?.]{0,25}"
    r"\b(?:to|in|abroad)\b", re.I)
# A line that says the move is still to come: where it is planned rather than where they are.
GOING_AWAY = re.compile(
    r"\b(?:abroad|overseas|emigrat\w*|expat\w*|planning to (?:move|go|leave)|"
    r"going to (?:move|emigrate)|thinking of (?:moving|emigrating|leaving)|"
    r"want(?:s|ed)? to (?:move|emigrate|live) (?:to|abroad|overseas))\b", re.I)
# The words that make "move ... to" be about a thing rather than a country.
A_THING_NOT_A_PLACE = re.compile(
    r"\b(?:phone|mobile|laptop|computer|pc|tablet|account|money|funds|savings|isa|pension|bin|"
    r"box|boxes|photos?|files?|data|number|direct debit|standing order|everything|furniture|"
    r"house|flat|home|office|job|team|city|town|area|school|bedroom|kitchen)\b", re.I)
# "how do i ask about working abroad" asks how to raise it, not what the paperwork needs.
NOT_THE_PAPERWORK = re.compile(
    r"\b(?:how do i (?:ask|raise|bring (?:it )?up|mention|broach)|who do i ask|"
    r"ask (?:my|your|the) (?:boss|manager|employer)|talk to (?:my|your) (?:boss|manager)|"
    r"send(?:ing)? (?:money|cash)|transfer(?:ring)? (?:money|cash)|ripped off|scam\w*|"
    r"how much (?:money|cash) (?:to|can)|"
    # "moving in with my boyfriend" is a person, not a country, and roaming charges are the
    # phone's business rather than a passport's.
    r"mov(?:e|ing|ed) (?:in|on)\b|"
    r"(?:phone|mobile).{0,25}(?:charges?|roaming|data|contract|plan))\b", re.I)
# What "move" is about when it is not a country: the house, the job and the town the person
# already lives in, which is not a visa question.
MOVING_HOUSE = re.compile(
    r"\b(?:house|flat|home|office|job|team|city|town|area|neighbourhood|school)\b", re.I)
# The council is named, or the ask is the one thing everybody means by "the council" without
# saying it: whether they may park where they are thinking of parking. "How do i clean my bin" and
# "how do i write a letter to my landlord" are not council questions, and the bot has answers.
COUNCIL_WORD = re.compile(
    r"\b(?:council|councils|council tax|local authority|permit|planning permission|byelaw\w*|"
    r"blue badge|housing benefit|bulky waste|licensing|premises licence|taxi licence)\b", re.I)
PARKING_RULE = re.compile(
    r"\b(?:park|parking)\b[^?.]{0,30}\b(?:allowed|legal|illegal|ok|okay|fine|ticket|permit|"
    r"charge|charges|charged|free|sunday|sundays|resident\w*|restriction\w*|badge|disabled)\b|"
    # The words in the other order: "is it legal to park on the pavement", "am i allowed to park
    # here on sundays". The rule is the same local one, and reading only the first order sent
    # both to the shrug.
    r"\b(?:allowed|legal|illegal|ok|okay|fine|against the rules)\b[^?.]{0,25}\bpark\b|"
    r"\b(?:can|could|am i allowed to|are we allowed to|where can i|where should i|is it ok to|"
    r"is it okay to)\b[^?.]{0,20}\bpark\b", re.I)
WANTS_THE_RULES = re.compile(
    r"\b(?:can i|could i|do i|does it|how do i|how can i|what do i|what are the|whats the|"
    r"what's the|am i allowed|is it (?:allowed|legal|ok|okay|possible)|are we allowed|"
    r"will i|do we|who do i|where do i|how much is the|"
    # "how about moving to spain" asks the same question as "can i move to spain": the subject
    # is the move, so the shape that opens with the subject instead of the verb counts too.
    r"how about|what about|thoughts on|what do you think (?:of|about)|is it easy to|"
    r"whats it like to|what's it like to|should we)\b", re.I)

# One short question at the end of a reply is a friend's move, not a form: it gives the person
# somewhere to put the part of the question the bot did not get. Only one reading uses it, and only
# where the answer genuinely depends on a detail (which service, which journey, what they want).
SERVICES_POOL = (
    "A catalogue turns over every month with the rights, so I can't hold the list: "
    "{service}'s own search settles it in seconds, and says whether the thing is included or "
    "to pay for.",
    "A catalogue turns over every month with the rights, so typing the title into {service}'s "
    "own search is what says whether it is there today - I can't see it from here, and it "
    "says whether that is a rental or part of the subscription.",
    "What is on {service} changes with the rights, month to month, so I can't check it: its "
    "own search is the one that knows, and it says whether that is a rental or part of the "
    "subscription.",
)
JOURNEY_POOL = (
    "No live {mode} times from me, sorry: they are re-run all day and cancellations land "
    "late, which is why a journey planner has today's and I can't - where are you starting "
    "from, and when do you need to be there?",
    "No live {mode} times from me, sorry - they are re-run all morning and cancellations land "
    "later still, so a journey planner has the real ones and I can't: tell me the "
    "two ends and the time you have to be there and I'll help you plan around it.",
)
# When both ends are already in the line, the route pool that asks for them is the wrong reply: the
# person named Ealing and Heathrow and is told to name two places. These say the ends back and put
# the one question that decides a journey - the hour - where it belongs. Nothing about a road, a
# line or a time is added: what is true of every journey (the hour decides it, the planner holds the
# times, and a buffer for parking or finding the platform) is all that is said.
ROUTE_ENDS_POOL = (
    # The ends are said back in the person's own words, so none of these opens with one: a reply
    # that began "cardiff to bristol turns on the hour" starts in a small letter, and giving it a
    # capital only trades that for "Cardiff to bristol", which is worse. The place goes where a
    # sentence can hold it instead, and at least one wording closes on a statement rather than a
    # question, because a friend does not end every turn the same way.
    "On {start} to {end} the hour you set off decides it more than the miles do, and the bit at "
    "each end counts as much as the road between - I can't see the times or the traffic from "
    "here, sorry. A journey planner does it door to door, parking or platform included, and the "
    "one thing worth settling before you look is the time you have to be there.",
    "What settles {start} to {end} is the hour more than the distance: the peak is where it goes "
    "wrong, and the queue at both ends counts as much as the road between them, so the same pair is "
    "two different journeys at eight and at eleven. I can't see the day's times or the traffic from "
    "here, so a planner is the one that gives both ends door to door - when do you need to be "
    "there?",
    "Where in each place you start and finish settles {start} to {end} more than the route between, "
    "so fix the door first and let a planner work back from the hour you have to be there. The "
    "times are the planner's, not mine, sorry.",
)
# The two ends of a route, in the words the person used, so the reply can say them back. A line
# that names one end only is left to the pool that asks for the other.
# Lazy groups with the end of the line behind them: "to heathrow from ealing" gives the two
# places with nothing after them, and the tail of a longer line ("... on friday, thanks") is trimmed
# by the words below rather than by the pattern.
_THE_ENDS = re.compile(r"\bto\s+(?P<end>.+?)\s+from\s+(?P<start>.+?)\s*[?.!,]*\s*$", re.I)
_THE_ENDS_REVERSED = re.compile(
    r"\bfrom\s+(?P<start>.+?)\s+to\s+(?P<end>.+?)\s*[?.!,]*\s*$", re.I)
# Words that end a place and start the rest of the sentence, so "heathrow from ealing on friday"
# gives "heathrow" and not "heathrow from ealing on friday". The trim runs from the right.
_NOT_THE_PLACE = frozenset((
    "the", "a", "an", "on", "at", "in", "by", "for", "about", "and", "or", "but", "tomorrow",
    "today", "tonight", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "next", "this", "please", "thanks", "quickest", "fastest", "best", "cheapest",
    "easiest", "way", "route", "time", "times",
))

def _the_route_ends(said):
    """The two places in a route ask, as the person wrote them, or None.

    The line is a route question already, so the ends are the last two place-like runs of words
    around "from" and "to". Anything longer than four words is not a place name a person typed,
    and a line whose ends are only "the"/"my" has none to say back.
    """
    for pattern in (_THE_ENDS, _THE_ENDS_REVERSED):
        found = pattern.search(said)
        if not found:
            continue
        end = _a_place_name(found.group("end"))
        start = _a_place_name(found.group("start"))
        if end and start and end.lower() != start.lower():
            return start, end
    return None

# A qualifier said after a place rather than of it: "manchester by bike", "manchester in rush
# hour", "cardiff then", "leeds tomorrow". The cut is made anywhere in the run, not only at its
# tail, because the qualifier trails whichever end it was said after - trimming the end of the
# line alone gave "manchester by bike to leeds", which states a journey nobody asked about.
_A_QUALIFIER_AFTER_THE_PLACE = re.compile(
    r"\s+(?P<word>by|via|with|in|on|upon|at|for|then|please|thanks|today|tomorrow|tonight|now|"
    r"early|late|weekdays|this|next|around)\b", re.I)
# "in" and "on" also sit inside a real name - "stoke on trent", "sutton in ashfield",
# "newcastle upon tyne" - so those two cut only when what follows them is not a name part.
# A short list, because the names that are two words joined this way are few.
_A_NAME_PART = frozenset((
    "trent", "thames", "tyne", "avon", "wye", "humber", "sea", "furness", "ashfield", "arden",
    "lyme", "wolds", "moss", "ribble", "derwent", "don", "aire", "clyde", "ness", "stour",
))

def _without_a_qualifier(run):
    """The place alone, with anything said after it about how or when cut off."""
    text = str(run or "").strip(" .?,'")
    for found in _A_QUALIFIER_AFTER_THE_PLACE.finditer(text):
        if found.group("word").lower() in ("in", "on", "upon"):
            rest = text[found.end():].split()
            if rest and rest[0].strip(".,").lower() in _A_NAME_PART:
                continue
        return text[:found.start()]
    return text

def _a_place_name(run):
    words = [word for word in _without_a_qualifier(run).split() if word]
    while words and words[-1] in _NOT_THE_PLACE:
        words.pop()
    while words and words[0] in ("the", "a", "an", "to", "from", "get", "my", "our"):
        words.pop(0)
    # "here" and "there" are ends the bot cannot see, and "here to work is a journey" is a
    # sentence about nothing the person said. Without them the line asks for the ends instead.
    if not words or len(words) > 4 or any(word in ("here", "there") for word in words):
        return ""
    return " ".join(words)

ROUTE_POOL = (
    "No timetables from me, sorry: they are re-cut every few months and the day's works "
    "change them, so I can't see today's - a journey planner has the options door to door: "
    "where from, and when do you need to be there?",
    "No timetables from me, sorry - they are re-cut every few months, so the planner is the "
    "one that knows the real times between two places, and I can't: tell me the two ends and "
    "the day and I'll help you pick.",
)
PICK_POOL = (
    "Reviews beat a guess from me on the {thing} near you, which I have never been to: a map "
    "app's, sorted by what you need, is the honest way - say what matters and I'll help you "
    "narrow it down.",
    "Reviews from people who have been beat my guess on the {thing} near you, since I have never "
    "been to any of them: sort a map app's by what you need, and the count matters more than the "
    "score.",
)
SHOP_POOL = (
    "Stock, prices and delivery change by the hour and they are {shop}'s own to know, so I "
    "can't see them: its site has them worked out for your postcode, and the checkout tells "
    "you before you pay.",
    "Stock, prices and delivery are {shop}'s own to know and they change by the hour, so "
    "there is no window on them from here: its site has the answer, and the checkout tells "
    "you before you pay.",
)
ABROAD_POOL = (
    "What paperwork you need depends on your passport and what you would be doing there, so I "
    "can't tell you which one applies: gov.uk's living abroad guidance and the country's own "
    "government site are the two that count.",
    "It depends on your nationality and your plans, so the official pages are the ones to "
    "read: gov.uk's living abroad guidance, then the destination's own government site.",
)
# The sky is the one reading here that is not a place at all: the forecast is live information
# about where the person is standing, and the bot has no window on it. A forecast app or a
# national weather site does, and it is worked out for their own postcode, which is the part a
# general answer cannot give. The pool says only that: no invented weather, no guess at the week.
WEATHER_POOL = (
    "A forecast is worked out for a postcode and re-run through the day, so I can't hold "
    "today's: a weather app has it for yours, hour by hour, and the week ahead when you are "
    "planning.",
    "A forecast is re-run for a postcode through the day, so there is no live weather from "
    "me: a forecast app or the national weather site has what is actually coming where you "
    "are.",
)
# The sky as the subject of an ask: "will it rain", "is it going to be icy", "is it foggy",
# "will it be frosty on monday", "is there a frost tonight". The article is refused after "it"
# so "is it a cold or hayfever" stays the illness it is, and the "is there" branch names only
# the weather itself, so "is there a cold going round" is not read as the sky either. A day word
# is not required: "will it rain" and "will it rain on saturday" are one question.
A_SKY_ASK = re.compile(
    r"\b(?:will|would|is|are|does|do|should|might|shall|can|could)\s+(?:it|we|they)\s+"
    r"(?:(?:going\s+to|gonna|meant\s+to|likely\s+to|supposed\s+to)\s+)?"
    r"(?:be\s+|get\s+|stay\s+|turn\s+)?"
    r"(?:raining|rainy|rain|snowing|snowy|snow|frost|frosty|freezing|freeze|thaw\w*|icy|ice|"
    r"hail|hailing|sleet|foggy|fog|misty|mist|windy|gusty|gusts|thunder|stormy|storm|sunny|"
    r"sunshine|cloudy|drizzle|drizzling|showers?|humid|muggy|warm|cold|hot|chilly|mild)\b"
    r"|\b(?:is|will|are)\s+there\s+(?:a\s+|an\s+|any\s+|much\s+)?"
    r"(?:frost|ice|snow|rain|hail|sleet|fog|mist|wind|showers?|sun|thunder|storm)\b"
    # The same ask with the forecast said in it: "is there going to be a storm", "will there be
    # frost tonight". The shape above reads "is there a storm" and not these, so both reached the
    # floor and got the search hedge, which is the one reply that helps nobody on a phone.
    r"|\b(?:is|are|will)\s+there\s+(?:going\s+to\s+be|gonna\s+be|likely\s+to\s+be|be)\s+"
    r"(?:a\s+|an\s+|any\s+|much\s+)?"
    r"(?:frost|ice|snow|rain|hail|sleet|fog|mist|wind|showers?|sun|thunder|storms?|"
    r"heat|heatwaves?)\b"
    r"|\b(?:any|much)\s+(?:chance|risk|sign)\s+of\s+(?:a\s+|any\s+)?"
    r"(?:frost|ice|snow|rain|sleet|hail|fog|wind|thunder|showers?)\b"
    r"|\b(?:are|is|will)\s+we\s+(?:due|in\s+for)\s+(?:a\s+|any\s+|some\s+)?"
    r"(?:frost|ice|snow|rain|sleet|hail|fog|wind|thunder|showers?|storm|sun)\b", re.I)
# A reading of a thing, not of the sky: the oven's heat, the fridge, the car's engine. "Will it
# be hot in the oven" is a roast, and the entries for those have the answer.
A_SETTING = re.compile(
    r"\b(?:oven|grill|hob|fridge|freezer|microwave|kettle|boiler|radiator|cooker|washing "
    r"machine|tumble dryer|dishwasher|iron|shower|bath|sauna|engine|car|van|room|bedroom|"
    r"house|flat|dough|batter|sourdough)\b", re.I)
COUNCIL_POOL = (
    "The rules differ from one council to the next and change with the year, so I would not "
    "guess at yours: its own site has the rule and the form, and the phone line will tell you "
    "which applies to you.",
    "It depends on where you live and no two councils do it the same, so I can't see your "
    "council's rules from here: its own site is the one that decides it, and it has the form.",
)

# The other half of STYLE.md's "Not knowing, honestly": a limit is worth nothing on its own.
# "A quick search online will get you a solid answer" is all the shape-only questions got on main,
# and it names nothing about the question - not what to check, not the first step. Two shapes have
# nothing else: a choice between two named things, and an ask for a shortlist. Neither names a
# subject the bot can look up, which is exactly why the reply has to carry the part that is true of
# every question of that shape - what decides it and the usual first step - and then ask for the
# one thing only the person knows.
CHOICE_POOL = (
    "Decide it on the one thing it must do well for you and compare only on that; the rest of "
    "the difference rarely matters. What must it do well?",
    "What settles these is fit rather than quality, so name the job it has to do and the limit you "
    "cannot go past - money, space or time. Which of those is tighter?",
    "When two are close, what separates them is how they are in use rather than on paper. What "
    "will you use it for most?",
)
SHORTLIST_POOL = (
    "A shortlist needs the thing you are starting from: what you are choosing between, and the one "
    "limit you cannot go past. Give me those two and I will put three or four in order.",
    "I can narrow it once I know what is on the table and what would make one of them useless to "
    "you. What is on the table?",
    "The useful part is what rules one out - money, timing, effort, or a line you will not cross. "
    "Tell me that and what you are choosing from.",
)

# A form is not a thing a shop near you sells: it comes from the organisation that wants it, and
# that is the part the bot does know about paperwork even when it cannot see which office it is.
# Getting one and sending one back have different answers, so they are read apart.
FORM_FROM_POOL = (
    "The form comes from the organisation that wants it, and their own site has it under the name "
    "of the thing you are applying for. Their contact page will post one if it is not there. "
    "Which organisation is it?",
    "Start from the letter or page that asked you: it names the office, and that office's site has "
    "the form to download or to fill in online. Their number can post one out. Do you still have "
    "it?",
)
FORM_TO_POOL = (
    "It goes to the address printed on the form itself - not to a general office - and a photo of "
    "it before it goes is what settles a dispute later. Which one is it?",
    "The letter that came with it names the office and the address to return it to; if it is "
    "missing, their contact page has one and a ring will confirm which. Do you have the letter?",
)

def _said(text):
    return str(text or "").lower()


def _the_line_before(memory):
    """What the person said in the last few turns, or "" on the first turn.

    A follow-up names what is being asked about and not where: "we're thinking of moving to spain"
    then "what paperwork do i need", and "we're going to cornwall in august" ... then "any good
    beaches for the kids" are one question in two turns, and the second turn alone has no country
    and no place in it. Only the kind is read from the earlier lines, never the answer, and the
    last three are enough for a person to have changed the subject.
    """
    if not isinstance(memory, dict):
        return ""
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    said = [str(turn.get("user") or "").lower() for turn in turns[-3:]]
    return " ".join(said)


def _the_answers_before(memory, count=4):
    """The bot's own last few answers, newest first, or [] on the first turn.

    Newest first because a person asking what to check is asking about the thing that is still on
    the table: "what should i check" three turns after the price came up is about the price, and an
    answer from before that is about something they have moved on from.
    """
    if not isinstance(memory, dict):
        return []
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    found = [str(turn.get("bot") or "").strip() for turn in turns[-count:]]
    return [line for line in reversed(found) if line]


def _the_checks_in(answer):
    """The sentence of an answer that names the conditions, or "".

    Taken whole, and not cut at a comma: the conditions *are* the sentence, and "A second-hand one
    is fine if the frame is straight" without the brakes and the fabric is half the list the person
    asked for. A long sentence is handed back as it is for the same reason; the only answers
    skipped are the ones that are a question or a shrug, which name nothing.
    """
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+", str(answer or "")):
        sentence = sentence.strip().strip("\"'\u201c\u201d").strip()
        if not sentence or len(sentence) > 320:
            continue
        if NOT_A_CHECK_SENTENCE.search(sentence):
            continue
        if A_CHECK_SENTENCE.search(sentence):
            found.append(sentence)
    for sentence in found:
        # The answer's *condition* is the list: "A second-hand one is fine if the frame is
        # straight, the brakes hold and the fabric washes." Its neighbour says what matters about
        # the thing in general ("what matters is that it folds into the car"), which is worth
        # reading and is not the checks, so an "if" sentence is taken first wherever it comes.
        if A_CONDITION.search(sentence):
            return sentence
    return found[0] if found else ""


def _about_a_check(said, understood, memory):
    """The checks the bot has named, handed back, or None.

    The reply is the bot's own sentence with one line about what to do with it and, in two of the
    three, a short question. Nothing is added to the list: a check this file made up would be a
    fact about a pram or a boiler that the knowledge base has not got, which is the one thing a
    last resort may not do. So an ask with no such sentence behind it stands down and the floor
    answers as it did before.
    """
    if WANTS_A_CHECK.search(said) is None or CHECK_OF_SOMETHING_ELSE.search(said):
        return None
    for answer in _the_answers_before(memory):
        checks = _the_checks_in(answer)
        if not checks:
            continue
        if checks[-1] not in ".!?":
            checks += "."
        return pick(CHECKS_POOL, understood or {}, said).replace("{checks}", checks)
    return None


def _named_service(said):
    """The service a line names, as (the word in the line, the name on screen), or ("", "").

    The longest name wins, because "bbc iplayer" and "iplayer" are the same service and "sky go"
    is a narrower thing than "sky".
    """
    best = ""
    for word, shown in SERVICES:
        if len(word) > len(best) and re.search(r"\b" + re.escape(word) + r"\b", said):
            best, chosen = word, shown
    return (best, chosen) if best else ("", "")


def _about_a_service(said, understood):
    word, service = _named_service(said)
    if not word or NOT_AVAILABILITY.search(said):
        return None
    # The service has to be named in a frame that makes it a platform - "on iplayer", "does netflix
    # have it", "netflix's search" - and the line has to ask something. "who is the prime minister
    # of australia" and "why is the sky blue" name a prime and a sky, and the old entries for
    # "prime" and "sky" answered both with a catalogue.
    platform = re.compile(
        r"\b(?:on|from|at|via|in)\s+(?:the\s+)?" + re.escape(word) + r"\b|"
        r"\b" + re.escape(word) + r"(?:'s|s')\b|"
        r"\b" + re.escape(word) + r"\s+(?:has|have|got|shows|show|streams|stream|adds)\b|"
        r"\b(?:does|do|did|is|are|has|have)\s+(?:the\s+)?" + re.escape(word) + r"\b", re.I)
    if not platform.search(said):
        return None
    if not re.search(r"\b(?:is|are|was|were|isnt|arent|any|anything|do|does|did|can|could|where|"
                     r"how)\b", said, re.I):
        return None
    return pick(SERVICES_POOL, understood or {}, said).replace("{service}", service)


def _about_a_shop(said):
    """The shop a line asks about, in the form the reply uses, or "".

    The name alone is not the shop: "my boots creak when i walk" is about footwear and "boots"
    there is a pair of them, so the name has to be in a frame that makes it a shop - at, in, from,
    to, "does", or its own possessive.
    """
    best = ""
    for word, shown in SHOPS:
        frame = re.search(
            r"(?:\b(?:at|in|from|to|does|do|did|is|are|asda's|with)\s+(?:the\s+)?"
            + re.escape(word) + r"\b)|(?:\b" + re.escape(word) + r"(?:'s|s')\b)", said)
        if frame and len(word) > len(best):
            best, chosen = word, shown
    if not best or not SHOP_ASK.search(said):
        return ""
    return chosen


def _the_mode_named(mode):
    """The service noun as the pools need it: a modifier before "times", so always singular.

    The line can name the service in the plural - "how often do the buses run", "how often do the
    trains run on sunday" - and the slot it fills is "No live {mode} times", where the noun is
    doing the work of an adjective. So a plural is put in the singular there; "no live buses
    times" is not a sentence anybody says. Which plural belongs to which singular is already the
    table above, so nothing is guessed from the ending of the word.
    """
    single = (TRAVEL.get((mode or "").lower()) or ("", ""))[0]
    return single or mode


def _about_a_journey(said):
    if GET_FROM_TO.search(said) and not NOT_A_DESTINATION.search(said) and not any(
            re.search(r"\b" + re.escape(word) + r"\b", said) for word in TRAVEL):
        return "route"
    for word, (single, plural) in TRAVEL.items():
        # The mode is a noun only when something in front of it makes it one: "i train next to
        # the window", "bus it over" and "i tube to work" are the verb.
        noun = re.search(
            r"\b(?:the|a|an|my|your|our|his|her|their|this|that|these|those|last|next|first|any|"
            r"every|no|by|take the|catch the|get the)\s+" + re.escape(word) + r"\b", said)
        if not noun:
            continue
        if NOT_A_JOURNEY.search(said) or not WANTS_A_TIME.search(said):
            return None
        # The same word is a train set, a bus pass and a flight of stairs: only a line that asks
        # for a time or a journey is this reading.
        if word in ("tube", "metro"):
            mode = "Tube"
        else:
            # The word that goes in front of "times" is the singular, whatever the person typed:
            # "how often do the buses come" was answered "I can't see live buses times from here",
            # and the plural appears in the line about as often as the singular. The plural still
            # says which vehicle was meant (the entry is found by its own word), so nothing is
            # lost by handing back the one name.
            mode = single
        return mode
    return None


# A follow-up that names only a subject and asks nothing: "what about the schools", "and the
# worktop", "what about the food there". There is no verb in it, so the floor has nothing to work
# with and the person gets the search shrug for a question they can already see is about one
# thing - but the noun still says which kind it is, and the honest answer is the same limit and
# the same place that knows that the full question would have got.
ONLY_A_SUBJECT = re.compile(
    r"^(?:and|but|ok|okay|so|also)\s+what\s+about\b|^what\s+about\b|"
    r"^(?:and|but|also)\s+(?:the|my|your|a|an|those|these|that)\b", re.I)
# A bare "and the food" is a subject; "and the food was cold" is a report and "also my back hurts
# from the drive" is a complaint. Only a line with no verb in it is the follow-up.
HAS_A_VERB = re.compile(
    r"\b(?:is|are|was|were|has|have|had|does|do|did|can|could|will|would|should|hurts?|feels?|"
    r"seems?|goes|went|keeps?|works?|tastes?|smells?)\b", re.I)
# A line that names a subject and then asks its own question - "what about white wine, does that
# come out easier", "what about the drive down, is it awful in august" - is not this shape: it
# says what it wants and is read as that.
A_QUESTION_OF_ITS_OWN = re.compile(
    r"[?,]\s*(?:is|are|was|were|does|do|did|can|could|will|would|should|how|why|when|where|what|"
    r"who|which)\b|\b(?:is|are|does|do|did|can|could|will|would|should)\s+"
    r"(?:it|that|they|this|i|we|you|he|she)\b", re.I)
# Five words is a subject; longer is a sentence with a subject in it.
A_FEW_WORDS = 5
# The words that only point at the subject: "the food there", "a pub near here", "the beaches
# like there". Everything else in the line has to be the noun itself, or the subject is not the
# whole of what the person said - "what about burnt bbq food" is a complaint about a barbecue.
POINTING_WORDS = frozenset((
    "the", "a", "an", "any", "some", "my", "your", "our", "their", "its", "his", "her", "these",
    "those", "that", "this", "near", "nearby", "here", "there", "around", "round", "about", "in",
    "on", "at", "to", "for", "like", "instead", "then", "too", "and", "or", "please", "though",
))
# The nouns that settle the kind on their own, because one place keeps the answer for that noun
# whichever question is being asked about it: a bin, a library and a patch of fly-tipping are all
# the council's, and a beach, a pub and a market are all somewhere a map app has reviews of.
SUBJECT_KINDS = (
    ("council", re.compile(
        r"\b(?:bins?|rubbish|recycling|refuse|potholes?|librar(?:y|ies)|leisure cent(?:re|er)|"
        r"bulky waste|council tax|parking permits?|green waste|fly ?tipping|grass cutting|"
        r"school places|school catchments?|catchment areas?|catchments?|admissions|schools?)\b",
        re.I)),
    ("map", re.compile(
        r"\b(?:food|restaurants?|pubs?|cafes?|coffee shops?|takeaways?|take-aways?|beaches|walks|"
        r"things to do|days? out|markets?|parks?|chippy|chip shops?)\b", re.I)),
    ("journey", re.compile(
        r"\b(?:trains?|buses|coach|trams?|ferr(?:y|ies)|the drive|traffic)\b", re.I)),
)
# The word the pick line needs: a question about "the food there" is a question about
# restaurants, and one about "the chippy" is about chip shops.
_SUBJECT_LABEL = {
    "food": "restaurants", "restaurant": "restaurants", "restaurants": "restaurants",
    "pub": "pubs", "pubs": "pubs", "cafe": "cafes", "cafes": "cafes", "coffee shop": "cafes",
    "coffee shops": "cafes", "takeaway": "takeaways", "takeaways": "takeaways",
    "take-away": "takeaways", "take-aways": "takeaways", "beach": "beaches",
    "beaches": "beaches", "walk": "walks", "walks": "walks", "thing to do": "things to do",
    "things to do": "things to do", "day out": "days out", "days out": "days out",
    "market": "markets", "markets": "markets", "park": "parks", "parks": "parks",
    "chippy": "chip shops",
    "chip shop": "chip shops", "chip shops": "chip shops",
}
# A subject about a drive is a question about travel, so the journey line reads "travel times"
# rather than "drive times".
_SUBJECT_MODE = {"trains": "train", "buses": "bus", "trams": "tram", "ferries": "ferry",
                 "coach": "coach", "the drive": "travel", "traffic": "travel"}


def _a_country_not_home(text):
    """The first country in the line that is not this one, or "".

    Read from the knowledge base's own country list rather than a short list of holiday names,
    because the thread can leave the UK in any direction and a council is then the wrong body.
    """
    for name in NOT_HOME_COUNTRIES:
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return name
    return ""


def _about_the_subject_named(said, understood, before=""):
    """The limit and the place that knows, for a follow-up that names only a subject.

    "what about the schools" after a house move is a question about admissions, and it went to
    the search shrug because there is no verb to read. The noun is the whole of it, and it names
    a kind with a place behind it, so the answer here is the same one the long version of the
    line would have got. Anything else - a subject nobody keeps ("what about the parsnips",
    "what about a stainless steel one") - is left to the floor, which is where it was.
    """
    lead = ONLY_A_SUBJECT.match(said)
    if not lead:
        return None
    rest = said[lead.end():].strip(" ?.!,")
    if not rest or len(rest.split()) > A_FEW_WORDS or A_QUESTION_OF_ITS_OWN.search(said):
        return None
    if said[lead.start():lead.end()].strip().startswith(("and", "but", "also")) and \
            not re.search(r"what about", said[:lead.end()], re.I):
        # "and the food" is this shape; "and the food was cold" is a report about dinner.
        if HAS_A_VERB.search(said):
            return None
    words_in_line = [word.strip("?,.!'") for word in rest.split()]
    for kind, words in SUBJECT_KINDS:
        named = words.search(rest)
        if not named:
            continue
        left = list(words_in_line)
        for word in named.group(0).lower().split():
            if word in left:
                left.remove(word)
        if [word for word in left if word and word not in POINTING_WORDS]:
            # Something else is in the line, so the subject is not the whole of it.
            continue
        if kind == "council":
            # A council is the wrong body in another country. After "we're thinking of moving to
            # spain", "what about the bins" is a question about Spanish paperwork and the bin
            # day there, and naming a council would be worse than the floor's own answer. The
            # long form of the ask makes the same stand-down in `_about_the_rules`.
            if (ABROAD.search(before) or _a_country_not_home(before)
                    or _a_country_not_home(said)):
                return None
            return pick(COUNCIL_POOL, understood or {}, said)
        if kind == "journey":
            word = named.group(0).lower()
            return pick(JOURNEY_POOL, understood or {}, said).replace(
                "{mode}", _the_mode_named(_SUBJECT_MODE.get(word, word)))
        thing = _SUBJECT_LABEL.get(named.group(0).lower())
        if not thing:
            return None
        # A pick is a pick somewhere: "what about the food there" is a question about a place,
        # "what about the food" on its own is not, so it is left to the floor.
        if not (A_PLACE.search(rest) or re.search(r"\b(?:there|here|nearby|local)\b", rest)
                or A_PLACE.search(before) or re.search(r"\b(?:there|here|nearby|local)\b", before)):
            return None
        return pick(PICK_POOL, understood or {}, said).replace("{thing}", thing)
    return None


def _about_a_pick(said, before=""):
    """The kind of place a line asks to be told about, or None.

    Two things have to hold, and both of them are about the word being the thing asked *for*
    rather than a place named on the way: an ask word ("best", "any good", "recommend") has to come
    just before it, and it must not be the object of a preposition of place, so "anywhere nice to
    eat near the beach" is a question about eating and not about beaches.
    """
    if not A_PLACE.search(said) and not A_PLACE.search(before):
        return None
    for words, thing in PICKS:
        for word in words:
            for match in re.finditer(r"\b" + re.escape(word) + r"\b", said):
                blocked = PICK_NOT.get(words[0])
                if blocked is not None and blocked.search(said):
                    break
                before = said[max(0, match.start() - 26):match.start()]
                if re.search(r"\b(?:in|near|around|round|at|by|beside|on|from|to)\s+(?:the\s+)?$",
                             before):
                    continue
                if not WANTS_A_PICK.search(before):
                    continue
                return thing
    return None


def _the_home_town(memory):
    """The town the person's own words already put them in, lowercased, or ().

    The understanding engine files a move already made as a home ("i just moved to bristol" is
    `home: true`, `city: Bristol`), and a move being planned as a place or a plan instead
    ("we're thinking of moving to spain" is a place with no home), so this reads the one and
    not the other.

    A country is not a town, and the engine files "i moved to france last year" the same way it
    files the move to Bristol - `home: true`, `city: France` - so the guard read that home as the
    town they are in and stood the paperwork down for the person who needs it most: "what
    paperwork do i need to stay" after moving to France was answered with the search hedge. The
    guard is about a town the move brought them to, so a country named as the home is left out -
    except the four nations of the UK, where a move is a move at home and "what classes are on"
    after "i moved to scotland" is the class question, not the paperwork.
    """
    if not isinstance(memory, dict):
        return ()
    user = memory.get("user")
    if not isinstance(user, dict) or not user.get("home"):
        return ()
    # A move the engine has filed as a plan has not happened yet, whatever the home flag says:
    # "we are moving to spain" is `home: true, city: Spain` *and* `plans: ["Moving to spain"]`,
    # and the paperwork for going is exactly what that person is asking for.
    plans = user.get("plans")
    if isinstance(plans, str):
        plans = (plans,)
    if isinstance(plans, (list, tuple)):
        if any(GOING_AWAY.search(str(plan)) or MOVING.search(str(plan)) for plan in plans):
            return ()
    found = []
    for key in ("city", "town", "village", "hometown", "home_city"):
        value = user.get(key)
        if isinstance(value, str):
            found.append(value.strip().lower())
    return tuple(word for word in found if word and (word in HOME_NATIONS or word not in COUNTRIES))


def _the_lines_of_this_question(said, memory):
    """The last few turns and this one, oldest first, as the person said them.

    `_the_line_before` glues the earlier lines into one string, which is enough to say that
    something was said about moving and not enough to say which came last. A move already made
    and a move still to come are told apart by which of them is the newer.
    """
    if not isinstance(memory, dict):
        return [said]
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    earlier = [str(turn.get("user") or "").lower() for turn in turns[-3:]]
    return earlier + [said]


def _the_move_was_to_their_own_town(said, memory):
    """True when the newest thing said about moving is the move that brought them where they are.

    "i just moved to bristol" is a statement about the town the person lives in now, and it was
    still being read three turns later: after "whats a good way to meet people here" and "i dont
    really drink", the line "ok what about classes or clubs" was answered with the paperwork for
    living abroad, because "moved to" is a move and nothing checked the destination. A place
    already in their own words as where they are is not a somewhere-else they are planning.

    Only the newest line that talks about moving counts. "i just moved to bristol" and then
    "we are planning to emigrate" is a person in Bristol who is still going, and the paperwork
    answer is theirs; the home move is only the last word on the subject when nothing after it
    says the move is still to come.
    """
    places = _the_home_town(memory)
    if not places:
        return False
    for line in reversed(_the_lines_of_this_question(said, memory)):
        move = MOVING.search(line)
        if move:
            destination = line[move.end():move.end() + 30]
            for place in places:
                if re.search(r"(?:^|[^a-z])" + re.escape(place) + r"(?:[^a-z]|$)", destination):
                    return True
            return False
        if GOING_AWAY.search(line):
            return False
    return False


def _a_day_out(said, before=""):
    """True when the line asks what to do or see in the place the thread is already about.

    The place has to be somewhere real: named on this line ("what should we see in rome"), or
    only pointed at ("what should i do there", "anything good to do while we are there") with a
    trip in the last few lines, which is how a follow-up is asked. A line with an object of its
    own ("what should i do about my knee", "what should i do with it") is not this reading,
    neither is a day at home ("what should i do in the garden" is the garden's), and neither is
    a visit to a ward or to see somebody.
    """
    if not said or not WANTS_A_DAY_OUT.search(said) or DAY_OUT_NOT.search(said):
        return False
    if ASKS_WHAT_TO_DO.search(said) and A_THING_IN_HAND.search(said):
        return False
    if A_PLACE.search(said) and not NOT_A_DAY_OUT_PLACE.search(said):
        return True
    if not (A_PLACE_THERE.search(said) or A_BARE_DAY_OUT.search(said)):
        return False
    # no name on this line: "there" and a bare "what should we see" need the trip behind them
    return bool(A_TRIP_BEFORE.search(before) and not NOT_A_DAY_OUT_PLACE.search(before))


def _about_the_rules(said, understood, before="", memory=None):
    if not WANTS_THE_RULES.search(said):
        return None
    # The country is allowed to be on the turn before this one; the ask is not, because an ask
    # with nothing of its own to ask about is the shrug's business, not this reading's. A move
    # needs a country as well: `ABROAD`'s move branch reads any "move to <word>" as a move abroad,
    # so "we are thinking of moving to leeds" and then "what are the schools like" was answered
    # with the passport pages. The town a person is moving to is not a country, and the rules for
    # the move are the council's - "we are moving to spain" names one and keeps the pages.
    both = said + " " + before
    strong = re.search(r"\b(?:abroad|overseas|emigrat\w*|expat\w*|visa|residency|passport for|"
                       r"work permit|right to (?:live|work)|country)\b", said)
    if (ABROAD.search(both) and (strong or _a_named_country_in(both))
            and not _the_move_was_to_their_own_town(said, memory)
            and not NOT_THE_PAPERWORK.search(said)):
        # A country is named on this line or the one before it, and the thing being moved is not
        # a phone, an account or a house: "should we move house" is not a visa question.
        if (strong or not A_THING_NOT_A_PLACE.search(said)) and not (
                MOVING_HOUSE.search(both) and not re.search(
                    r"\b(?:abroad|overseas|country)\b", both)):
            return pick(ABROAD_POOL, understood or {}, said)
    # The council has to be named on this line: a follow-up like "what do i even write" after a
    # parking ticket is asking for the wording, and "your council's site has the form" is not that.
    if COUNCIL_WORD.search(said) or PARKING_RULE.search(said):
        return pick(COUNCIL_POOL, understood or {}, said)
    return None


# The three shapes that had no reading at all. Each one is read for its *shape* rather than for a
# subject, because the subject is exactly what the bot does not have: a choice between two named
# things, an ask for a list, and an ask for a list.
WANTS_A_CHOICE = re.compile(
    r"\b(?:which|what)\s+(?:is|s|'s|would be|will be)\s+(?:the\s+)?(?:better|best|cheaper|"
    r"stronger|safer|easier|quicker|healthier|nicer)\b"
    r"|\bwhich (?:one )?(?:should|would|do) i (?:get|buy|use|go for|pick|choose|have)\b"
    r"|\b(?:is|are)\s+[a-z][a-z' -]{0,24}?\s+or\s+[a-z][a-z' -]{0,24}?\s+"
    r"(?:better|best|worth it|the one)\b"
    r"|\bwhat would you (?:go for|pick|choose|get)\b"
    r"|\bis it better to\b", re.I)
# "what is better for a burn" is a fact about the world, not a choice between two things the
# person has already picked, and the health cards own that shape.
NOT_A_CHOICE = re.compile(
    r"\b(?:for a|for my|for the)\s+(?:burn|cut|rash|cough|cold|headache|baby|child|dog|cat)\b",
    re.I)
WANTS_A_SHORTLIST = re.compile(
    r"\b(?:short ?list|a list of|(?:a few|some|a couple of|three|two) (?:options|ideas|"
    r"suggestions|choices|picks)|options (?:for|on)|what are my options|what are the options|"
    r"(?:give|gimme|send) me (?:a few|some|three|two|a couple)|(?:suggest|recommend) "
    r"(?:a few|some|three|two))\b", re.I)
# A list of something the person is going to write themselves (a shopping list, a checklist) or a
# list they are already on is not a list the bot can be asked to draw up.
NOT_A_SHORTLIST = re.compile(
    r"\b(?:shopping list|ingredients list|list of ingredients|to do list|todo list|checklist|"
    r"waiting list|price list|job list|shortlisted|list of names)\b", re.I)
# Paperwork has a shape of its own: the verb is get, send or return and the object is a form. It is
# not a product, so no shop near them has one and no map app will find it.
GET_A_FORM = re.compile(
    r"\b(?:get|getting|find|download|print|print off|obtain|ask for|request)\b[^?.]{0,25}"
    r"\bforms?\b", re.I)
# The place and the office are what this half answers, so it needs one of them: "do i need to
# return the form" is a yes-or-no question about the paperwork itself, not about where it goes.
SEND_A_FORM = re.compile(
    r"\b(?:where|who|what address|which office|which address|how do i (?:send|return|post))\b"
    r"[^?.]{0,40}\b(?:send|sending|post|return|returning|hand|hand in|submit|give)"
    r"[^?.]{0,25}\bforms?\b"
    r"|\b(?:where|who)\b[^?.]{0,40}\bforms?\b[^?.]{0,25}\b(?:go|goes|going|back)\b", re.I)
# "A form of words", "in good form" and "form a queue" are not paperwork.
NOT_A_FORM = re.compile(
    r"\bform of (?:words|government|address|money|id|identification)\b|\b(?:in|on) (?:good |top )?"
    r"form\b|\bform an?\b|\bform (?:a|an)\b", re.I)


def _a_form(said, understood):
    """Where a form comes from, or where it goes back to, or None."""
    if NOT_A_FORM.search(said):
        return None
    if SEND_A_FORM.search(said):
        return pick(FORM_TO_POOL, understood or {}, said)
    if GET_A_FORM.search(said):
        return pick(FORM_FROM_POOL, understood or {}, said)
    return None


def _a_choice(said, understood):
    """The deciding factor for a choice between two things, or None.

    "Which is better, water or oil based" names no subject the bot can look up, and a search is
    a poor second to saying the one thing that is true of every choice of that shape: what it is
    used for and how hard it is worked decides it. The question at the end is the way in.
    """
    if not WANTS_A_CHOICE.search(said) or NOT_A_CHOICE.search(said):
        return None
    return pick(CHOICE_POOL, understood or {}, said)


def _a_shortlist(said, understood):
    """What a shortlist has to come from, or None: the bot cannot draw one out of nothing."""
    if not WANTS_A_SHORTLIST.search(said) or NOT_A_SHORTLIST.search(said):
        return None
    return pick(SHORTLIST_POOL, understood or {}, said)


def _about_the_sky(said, understood):
    """The weather a line asks about, as a reply naming where it is read, or None.

    The composer has its own weather line for the asks it recognises ("whats the weather like",
    "is it going to rain on saturday"), and this reading only ever runs on a line the composer
    left at the shrug: a sky word in an asking frame that it did not have words for, which is
    every frost, ice, hail, sleet, fog, mist, gust, thunder, drizzle, muggy or freeze question.
    A reading of a thing rather than the sky - the oven, the fridge, the car - stands down, so
    "will it be hot in the oven" keeps the roast answer it has.
    """
    if not A_SKY_ASK.search(said):
        return None
    if A_SETTING.search(said):
        return None
    return pick(WEATHER_POOL, understood or {}, said)


# A check on a thing in hand, asked after the bot has already named the checks.
#
#     im looking at a used pram on facebook marketplace for 90 quid
#     is that a good price
#       "A pram is £150 to £400 new ... A second-hand one is fine if the frame is straight,
#        the brakes hold and the fabric washes."
#     what should i check before i pay
#       "I'm not sure about that one, sorry - a quick search online will get you a solid answer."
#
# The list the person is asking for is in the answer two lines above their own: the bot has just
# said what settles a second-hand pram. What it does not have is the reading that "what should i
# check" is asking for that sentence back, so it offers a search for a question it has answered.
# This is the same reading `bot/compose/verdict.py` makes when a person asks how to tell whether
# the thing in the answer has gone off - the answer's own test, handed back - widened from one
# sign to the conditions an answer puts on a thing.
WANTS_A_CHECK = re.compile(
    r"\b(?:what|which|anything|something)\b[^?.!]{0,26}\b(?:should|shall|do|to|need to|must|"
    r"can|could)\b[^?.!]{0,24}\b(?:check|checking|look for|look at|look over|look out for|"
    r"watch out for|watch for|ask|be careful|be wary)\b|"
    r"\bwhat to (?:check|look for|look at|ask)\b|"
    r"\banything\b[^?.!]{0,26}\b(?:be careful|be wary|to watch out|to look out)\b|"
    r"\b(?:what|anything)\b[^?.!]{0,24}\bto be careful (?:of|about)\b", re.I)
# A check the line puts on a thing of its own - "what should i check on a used car", "what do i
# look for in a mortgage" - is not asking for the last answer back. The subject is new, and
# handing back the pram's conditions would answer about the wrong thing.
CHECK_OF_SOMETHING_ELSE = re.compile(
    r"\b(?:on|about|for|in|with)\s+(?:a|an|the|my|your|his|her|their|our)\b", re.I)
# The sentence of an earlier answer that names the conditions, in the words the bot chose: the
# "fine if" an answer puts on the thing, the check to run, the claim about what is worth looking
# at. A bare "if" is not one of them - "a boiler is built for 10 to 15 years ... even if it is
# working today" is a condition on a claim about a boiler's life, and handing that back as the
# list to work through was worse than the hedge it replaced.
A_CHECK_SENTENCE = re.compile(
    r"\bfine if\b|\bworth (?:checking|looking|a)\b|\bmatters?\b|\bwhat (?:settles|decides)\b|"
    r"\bchecks?\b|\bchecking\b|\blook (?:for|at)\b|\bwatch (?:out )?for\b|\bsigns? of\b",
    re.I)
# An earlier answer that is itself a shrug or a question is not a list of anything, and neither is
# a sentence that names care: "call 999 if the swelling spreads" is a condition on an answer, but
# handing it back with "which of them can you test yourself?" would take the urgency out of it and
# make a warning into a checklist. Those sentences are skipped and the floor keeps the turn.
NOT_A_CHECK_SENTENCE = re.compile(
    r"\?\s*$|\b(?:search online|look it up|not sure about that|tell me more)\b|"
    r"\b(?:999|112|111|a&e|ambulance|hospital|nhs|gp|doctor|pharmacist|midwife|vet|"
    r"urgent|emergency|straight away|right away)\b", re.I)
# What makes a sentence the list rather than the description: the answer's own "if".
A_CONDITION = re.compile(r"\b(?:fine )?if (?:the|it|there|they|you|your|its)\b", re.I)
# The checks come back as the bot's own sentence, and the pool only says what to do with them, so
# nothing here is a fact of its own: no list is invented, and no answer is widened past what it
# already said.
CHECKS_POOL = (
    "{checks} That is the list to go through, and I can't see it from here - which of them can "
    "you try yourself?",
    "{checks} Those are still the things that decide it, so work through them first and tell me "
    "what you find; I can only go on what you say about it.",
    "{checks} Nothing to add to that: those are what goes wrong, in the order I would check "
    "them. Which of them are you least sure about?",
)


def the_checks_already_named(text, memory=None):
    """The checks the bot named earlier, handed back, or None.

    The same reading `answer_for` makes, under a name `bot/modules/greeting.py` can call for the
    one kind of line that does not always reach it as a hedge: "anything i should be careful of"
    after the price of a second-hand pram is filed by the composer's neutral pool ("Got it. Is
    there anything you'd like a hand with?"), which is a receipt rather than an answer, and the
    receipt is what the reading replaces there.
    """
    said = _said(text)
    if not said.strip():
        return None
    read = {}
    if isinstance(memory, dict):
        candidate = memory.get("understood")
        if isinstance(candidate, dict):
            read = candidate
    return _about_a_check(said, read, memory)


def answer_for(text, memory=None):
    """The honest limit and the place that knows, or None when the line is not one of these.

    Only six kinds are read, and each one names a place the person can go to today or hands back
    the checks the bot gave earlier. A line that fits none of them is left to the floor, which is
    where it was before this module existed.
    """
    said = _said(text)
    if not said.strip():
        return None
    read = {}
    if isinstance(memory, dict):
        candidate = memory.get("understood")
        if isinstance(candidate, dict):
            read = candidate
    service = _about_a_service(said, read)
    if service:
        return service
    sky = _about_the_sky(said, read)
    if sky:
        return sky
    mode = _about_a_journey(said)
    if mode == "route":
        ends = _the_route_ends(said)
        if ends:
            return (pick(ROUTE_ENDS_POOL, read, said)
                    .replace("{start}", ends[0])
                    .replace("{end}", ends[1]))
        return pick(ROUTE_POOL, read, said)
    if mode:
        return pick(JOURNEY_POOL, read, said).replace("{mode}", _the_mode_named(mode))
    shop = _about_a_shop(said)
    if shop:
        return pick(SHOP_POOL, read, said).replace("{shop}", shop)
    before = _the_line_before(memory)
    # A time, not a place: "what do i do at dinner time" is a plan for a meal, and it is asked
    # here so the day-out reading below cannot take it.
    time_of_day = _a_time_of_day(said)
    if time_of_day:
        return time_of_day
    if _a_day_out(said, before):
        return pick(THINGS_TO_DO_POOL, read, said)
    thing = _about_a_pick(said, before)
    if thing:
        return pick(PICK_POOL, read, said).replace("{thing}", thing)
    subject = _about_the_subject_named(said, read, before)
    if subject:
        return subject
    checks = _about_a_check(said, read, memory)
    if checks:
        return checks
    rules = _about_the_rules(said, read, before, memory)
    if rules:
        return rules
    # Lowest of all, because each of these is read for the shape of the question and knows
    # nothing about the subject: anything above that names a place, a service or a rule keeps
    # its turn, and so does every card the composer can answer.
    return _a_choice(said, read) or _a_shortlist(said, read) or _a_form(said, read)
