"""A verdict asked for on a place or a thing the bot has never seen: the criteria, not a guess.

People ask the bot to judge things it cannot see more often than they ask it for a fact about
them: "is benidorm ok with a toddler", "is the old town doable", "is that restaurant good", "is
this area safe". No knowledge base holds a judgement about a place, so every one of those lines
reached the search hedge:

    is benidorm ok with a toddler
    That's beyond what I know well, sorry. Searching for it will turn up better sources than I
    can offer; tell me what you find and I'll help you weigh it up.

Nothing there is wrong and nothing in it helps. STYLE.md's "Not knowing, honestly" has the shape
that does: say what the bot cannot see in a few words, give the part it does know, and stay with
the person for the rest. The part it knows here is not a fact about Benidorm - it is what actually
decides a trip with a toddler, which is true of every trip with a toddler. So the reply names the
thing back, says plainly that there is no first-hand knowledge of it, gives the two or three things
that settle it, and names where the live detail is (recent reviews, a map app, the council's crime
map). Nobody is told what to think about a place the bot has never been to.

This is a last resort: `fallback.unknown_pool` asks it only on the branch where nothing else has
answered, and only for a line that is a judgement ask. Any entry, any module, and the composer's
own decision or live answer all come first, so the file can only replace a search hedge.
"""
import re

from . import pick

# The openers of the search hedge in `fallback_data.UNKNOWN`, which is the only reply this file
# replaces. A reply that is not one of these is somebody else's answer and is left alone.
HEDGE_OPENERS = (
    "i'm not sure about that one",
    "that's beyond what i know well",
    "i don't know enough to answer that honestly",
)

# The judgement words. Without one of these the line is not asking for a verdict: "is it open
# today" is live information, "is it far" is a distance, "is it worth it" is a decision with two
# sides the person already knows.
_JUDGE = (r"(?:ok|okay|alright|all right|good|nice|safe|doable|suitable|any good|any cop|"
          r"any use|decent|handy|worth it|worth going|worth seeing)")
VERDICT_ASK = re.compile(
    r"^\s*(?:so|but|and|ok|okay)?\s*(?:do you think\s+)?"
    r"(?:"
    # "is the old town doable", "is benidorm any good for kids", "is that school good"
    r"(?:is|are|was|were)\s+[a-z' ]{2,40}?\s+" + _JUDGE +
    # "would that suit a toddler", "would this place work for us"
    r"|(?:would|will)\s+[a-z' ]{2,40}?\s+(?:suit|work for|be ok for|be alright for|"
    r"be all right for|be good for)\b"
    # "is it worth it", "is that a good idea", "is the market worth a look"
    r"|(?:is|was|would)\s+[a-z' ]{0,40}?\s*worth\s+(?:it|a (?:look|visit|go|trip|day out)|"
    r"going|the (?:trip|money|hype))\b"
    r")"
    r"|\b(?:is|would)\s+it\s+" + _JUDGE + r"\b")
# A line that asks about the body, food, medicine, money, the law or an age is not a judgement any
# criteria can answer, and the arms below would be wrong on it: "is the chicken ok the next day"
# was this shape once and its answer is food safety, "is he old enough for school" is the law where
# the person lives. They stand the file down and keep whatever answer they had.
NOT_A_JUDGEMENT = re.compile(
    r"\b(?:eat|eaten|ate|eating|cook|cooked|cooking|cooker|freeze|frozen|defrost|fridge|"
    r"left out|left over|leftover|reheat|next day|day after|still ok|still good|gone off|"
    r"use by|sell by|best before|chicken|meat|fish|rice|milk|eggs|yoghurt|yogurt|"
    r"dose|dosage|mg|ml|tablet|tablets|pill|pills|medicine|paracetamol|ibuprofen|antibiotic|"
    r"pregnan\w*|symptom\w*|rash|fever|temperature|covid|flu|"
    r"old enough|how old|legal|illegal|allowed|the law|licen\w+|rules|"
    r"cost|costs|price|prices|how much|cheaper|afford|salary|wage|wages|tax|refund|deposit|"
    r"visa|passport|insur\w*|contract|tenancy|notice period|"
    r"worth buying|worth fixing|worth repairing|worth selling|repair|fix|broken)\b")

# The thing being judged: the words between the verb and the judgement word, which is what the
# reply says back. "is the old town doable" names "the old town"; "is it a nice place" names
# nothing, and a reply that invented a subject there would be worse than the hedge.
_THING = re.compile(
    r"^\s*(?:so|but|and|ok|okay)?\s*(?:do you think\s+)?(?:is|are|was|were|would|will)\s+"
    r"(?P<thing>[a-z' ]{2,40}?)\s+(?:" + _JUDGE +
    r"|suit|work for|be ok for|be alright for|be all right for|be good for)\b")
# A bare category word is named back with "that", because "area - I can't tell you whether a place
# is safe" reads like a form letter and "that area" reads like a person.
_BARE_NOUN = frozenset("""area place street road estate flat house home hotel restaurant cafe
    pub school nursery gym club class course town city village beach park market walk route
    holiday trip""".split())
# Words that name part of the question rather than a thing to judge: "is the food good" is about
# somewhere the person has not said, and the reply that names "the food" back reads like a form.
_NOT_A_THING = frozenset("food menu price cost drink beer wine coffee".split())
# Words that are the ask rather than the thing: they end the captured phrase.
_STOP = ("suit", "work", "be", "ok", "okay", "alright", "good", "nice", "safe", "doable",
         "worth", "any", "decent", "handy", "all")

# What decides each kind of thing, said as the criteria a person uses rather than as a fact about
# any one of them, and where the live detail is found in a step. One row per pool below.
_TRIP_CRITERIA = ("how far the flight or the drive is, how hot it gets, and how much walking "
                  "there is once you are there")
_TRIP_WHERE = ("Reviews from the last few months say what a place is like now rather than five "
               "years ago.")
_CHILD_CRITERIA = ("the flight or the drive, the heat, and how far the beach, the food and the "
                   "shops are from the room")
_CHILD_WHERE = ("The hotel's own page and the last few months of reviews cover the rest, and a "
                "map app shows the walk to the sand.")
_SAFE_CRITERIA = ("the time of day you would be out, how busy the street is then, and whether "
                  "you would be walking it alone")
_SAFE_WHERE = ("The police's own crime map for the postcode says more than any general view of "
               "a place does.")
# A thing you can hold - a bike, a car, a ladder, a boiler - is not a place, so the crime map
# has nothing to say about it. @urban-tapir found this: "is my bike safe to ride" was answered with
# the time of day and the crime map.
_SAFE_OBJECT_CRITERIA = ("the moving parts, the fixings and the seals, and anything cracked, "
                         "loose, or smelling of gas or hot plastic")
_SAFE_OBJECT_WHERE = ("Whoever services them will look it over for very little, and a gas or "
                      "electrical job wants a registered engineer rather than a guess.")
_SCHOOL_CRITERIA = ("the walk there, what the mornings feel like, and how easy it is to get a "
                    "straight answer out of the staff")
_SCHOOL_WHERE = ("Their own site has the numbers and the last report, and other parents tell you "
                 "the rest.")
_FOOD_CRITERIA = ("the last few months of reviews, the menu, and whether the price suits the "
                  "evening you have in mind")
_FOOD_WHERE = ("Their own page and the recent reviews have all three, and one visit settles it.")
_STAY_CRITERIA = ("the last few months of reviews, how far it is from where you want to be, and "
                  "what the noise is like at night")
_STAY_WHERE = ("Their own page and recent reviews cover all three, and the map listing shows the "
               "walk into town.")
_CLASS_CRITERIA = ("the times you can actually get to, who takes the session, and whether the "
                   "first one is free")
_CLASS_WHERE = ("Their timetable and a trial session answer that better than any review.")
_WALK_CRITERIA = ("the distance, how much of it is up or down, and the ground underfoot")
_WALK_WHERE = ("A map app shows the distance and the climb in a minute, and street view shows you "
               "the path.")
_HOME_CRITERIA = ("the walk from the station or the bus, the light in the rooms, the noise at the "
                  "time you would be home, and what the neighbours are like")
_HOME_WHERE = ("A map app shows the walk and the streets, and one visit on a weekday evening "
               "tells you the noise.")

# The reply: the thing named back, the honest no, the criteria, and where to look. `{lead}` is the
# thing and a dash, or nothing at all when the line names none - the wording after it starts
# lowercase so that "Benidorm \u2014 never been" reads like a person and the sentence is
# capitalised when there is no thing to name. Every kind says which of its senses the bot does not
# have, so the same file never says "never been" to a person asking about a school.
TRIP = (
    "{lead}never been, so no verdict from me. What decides a trip there is {criteria}. {where}",
    "{lead}no first-hand knowledge of the place, so no verdict from me. The things that settle it "
    "are {criteria}. {where}",
)
WITH_CHILDREN = (
    "{lead}not been with a little one, so I can't call it. What decides that trip is {criteria}. "
    "{where}",
    "{lead}can't call it from here. With a child in tow it comes down to {criteria}. {where}",
)
SAFE_ = (
    "{lead}can't tell you whether a place is safe from here, and I won't guess at it. What "
    "changes the answer is {criteria}. {where}",
    "{lead}no way for me to know about crime on a street I can't see, so no verdict from me. It "
    "turns on {criteria}. {where}",
)
SAFE_OBJECT = (
    "{lead}I can't look at it from here, so no verdict from me on whether it is safe. What a "
    "check comes down to is {criteria}. {where}",
    "{lead}no way for me to see the state of it, and safety is not something I'll guess at. It "
    "comes down to {criteria}. {where}",
)
# A school is spoken about in the plural as often as not ("are the schools good round there"), so
# neither phrasing leans on "it": the subject of the sentence is "a school".
SCHOOL = (
    "{lead}can't judge a school from here, and guessing would be worse than saying so. What tells "
    "you most is {criteria}. {where}",
    "{lead}no verdict from me on that one - I can't see inside a school from here. What tells you "
    "most is {criteria}. {where}",
)
FOOD = (
    "{lead}not eaten there, so no verdict from me. What decides it is {criteria}. {where}",
)
STAY = (
    "{lead}not stayed there, so no verdict from me. What decides it is {criteria}. {where}",
)
CLASS = (
    "{lead}can't judge one from here. It comes down to {criteria}. {where}",
)
WALK = (
    "{lead}can't see the ground from here, so I won't guess at how hard it is. What decides it is "
    "{criteria}. {where}",
)
SIGHT = (
    "{lead}no first-hand knowledge of the place, so no verdict from me. The things that settle it "
    "are {criteria}. {where}",
)
FAMILY = (
    "{lead}can't judge a place to bring children up from here. What decides it is {criteria}. "
    "{where}",
)
HOME = (
    "{lead}no way of seeing a place I haven't been to, so no verdict from me. What decides it is "
    "{criteria}. {where}",
)
# The kind of thing is not clear from the line at all ("is that a good idea", "is it worth it"),
# so the reply does not pretend to know what is being judged: it asks for the one thing that makes
# a verdict possible, which is the same move liveask makes without the live note.
# The kind that nothing above could name. It leads with what the bot *can* say, because a pointer
# on its own, or a question on its own, is not an answer: the three things that settle most
# judgements, and where the first-hand version of them lives. It asks nothing, because a question
# at the end of a fallback loses the turn after it.
OTHER = (
    "No first-hand knowledge of that one, so no verdict from me - and guessing would be worse than "
    "saying so. What settles most of these is what you want out of it, what you would do with it "
    "if it turned out to be no good, and what people who wanted the same thing say about it once "
    "they have had it a few months. Reviews from people who wanted the same thing say more than "
    "the page selling it.",
    "No first-hand knowledge of that one here, so no verdict from me. What it comes down to is "
    "how it works for the thing you actually want it for, how it holds up after a few months, "
    "and what it costs you if it is wrong. Recent reviews from people who wanted the same thing "
    "are the shortest way to all three.",
)
# The catch-all was one line of posture: it named neither the kind nor where to look, so a film, a
# series, a book, a job and a course all got the same shrug. These two say what actually settles
# each of them, and where the live version of it is (@kind-whale, #10238).
_SCREEN_CRITERIA = ("who made it and what you thought of theirs before, how long it takes to get "
                    "going, and whether you want to think or switch off")
_SCREEN_WHERE = ("A trailer or the first chapter tells you more in ten minutes than any review, "
                 "and the recent reviews say whether it holds up after the opening.")
_JOB_CRITERIA = ("the pay, the hours, and what the day actually looks like rather than what the "
                 "job is called")
_JOB_WHERE = ("The pay scales are published, and asking two people who do it now about a normal "
              "week settles more than any article.")
SCREEN = (
    "{lead}no first-hand knowledge of that one, so no verdict from me. What decides it is "
    "{criteria}. {where}",
    "{lead}can't judge it from here. It comes down to {criteria}. {where}",
)
JOB = (
    "{lead}wouldn't want to call that from here. What decides it is {criteria}. {where}",
    "{lead}no first-hand knowledge of that one. The honest answer turns on {criteria}. {where}",
)

# The kind of thing being judged, read from what the line is about. Order matters: the most
# specific reading wins, so a hotel with a toddler is read as a hotel rather than as a trip.
# A line about the bot itself is not a judgement on a place: "are you safe to talk to" was read as
# a street and answered with the crime map.
_ABOUT_THE_BOT = re.compile(r"\b(?:are|is|was|were)\s+(?:you|u|ya|the bot|this bot|"
                            r"this thing|the chatbot)\b|"
                            r"\b(?:ok|okay|alright|all right|fine|good|bad)\s+(?:with|to|for)\s+"
                            r"(?:you|u|ya)\b")
# The place words. A judgement about safety only has criteria the bot can name when the thing is a
# place: "is my data safe to delete" is not a street either.
_PLACE = re.compile(r"\b(?:area|areas|street|streets|road|roads|neighbourhood|neighborhood|estate|"
                    r"town|city|village|centre|center|park|beach|seafront|suburb|postcode|place|"
                    r"location|block|here|there|abroad|hotel|hostel|flat|house|home|station|"
                    r"walkway|alley|underpass|path|route|car park|sea|lake|river|coast|"
                    r"seaside|harbour|harbor)\b")
_SAFE = re.compile(r"\b(?:safe|safety|rough|dodgy|crime|mugged|sketchy|dangers?)\b")
_FEELING = re.compile(r"\b(?:feel|feels|feeling|felt)\b|\blike this\b|\babout myself\b|"
                      r"\bfor me to\b")
# A thing with a motor, a flame or a rung in it, asked about with "safe": the answer is a check and
# the person who does checks, not a street. It needs a place word to be read as a place, so this is
# only consulted when the line is about the thing.
_SCREEN = re.compile(r"\b(?:films?|movies?|series|show|shows|book|books|novel|album|game|games|"
                     r"documentar(?:y|ies)|podcasts?|sitcom|box set)\b")
_JOB = re.compile(r"\b(?:jobs?|careers?|trades?|profession|line of work|working as|"
                  r"worth (?:doing|studying|training))\b")
_SAFE_OBJECT = re.compile(r"\b(?:bikes?|cars?|vans?|mopeds?|scooters?|motorcycles?|ladders?|"
                          r"boilers?|heaters?|wood ?burners?|wiring|electrics|roof|chainsaws?|"
                          r"trampolines?|swing sets?|woodburner)\b")
_SCHOOL = re.compile(r"\b(?:school|schools|nursery|nurseries|preschool|pre-school|childminder|"
                     r"creche|cr[e\u00e8]che|kindergarten|college|university|uni)\b")
_STAY = re.compile(r"\b(?:hotel|hotels|b&b|b and b|hostel|guest house|guesthouse|apartment|"
                   r"villa|cottage|campsite)\b")
_FOOD = re.compile(r"\b(?:restaurant|restaurants|caf[e\u00e9]|pub|takeaway|bar|canteen|chippy|"
                   r"kebab shop|menu|food)\b")
_CLASS = re.compile(r"\b(?:gym|gyms|class|classes|club|clubs|course|courses|lessons|"
                    r"swimming pool|pool|leisure centre)\b")
_WITH_CHILDREN = re.compile(r"\b(?:toddlers?|bab(?:y|ies)|kids?|children|child|pram|buggy|"
                            r"pushchair|teenagers?|families)\b")
_WALK = re.compile(r"\b(?:walk|walks|route|hike|climb|stairs|hill)\b")
# A child in the line, and a place to bring them up in: "is it a nice place to bring up kids" is
# about the schools and the green space, not about the flight or the light in the rooms.
_RAISING = re.compile(r"\b(?:bring (?:up|ing up)|raise|raising|grow(?:ing)? up|settle down|"
                      r"to live|live in|family life)\b")
# A piece of a place rather than the place itself - "is the old town doable", "is the market worth
# a look" - is not judged by the flight and the heat: it is a walk, and what decides it is the
# ground and the time it takes.
_SIGHT = re.compile(r"\b(?:old town|town cent(?:re|er)|city cent(?:re|er)|market|attractions?|"
                    r"museum|gallery|castle|cathedral|zoo|theme park|water park)\b")
_TRIP = re.compile(r"\b(?:holiday|holidays|trip|resort|resorts|beach|town|city|village|island|"
                   r"abroad|seaside|centre|center|market|attraction|museum|zoo|park|cruise|cruises|"
                   r"ferry|flight|flights|long haul|day out|days out|weekend away)\b")
# A place the line names by name - "is benidorm ok with a toddler", "is centre parcs good for a
# four year old" - is a place with no place word in it. The capital is the only mark a name leaves
# in a typed line, and it is a mark the place words cannot give: the first word of a sentence is
# capitalised too, so the name has to be a capitalised word that is not the first one.
_NAMED = re.compile(r"\S\s+(?:the\s+|a\s+|an\s+)?[A-Z][a-z]{2,}")
# What a line is about, when it is not about somewhere to go: the trip criteria below are about the
# flight, the heat and the walk from the room, and a line whose subject is a sport, a body, money or
# a machine is not a trip however many children are in it. "is rugby safe for kids" was answered
# with "the flight or the drive, the heat, and how far the beach is" - a holiday nobody in the line
# had mentioned (@clean-salmon). The understanding engine already says what the line is about, so
# this is a list of topics, not of words.
# The topics that do make a child line a trip, so a place read as travel keeps the criteria even
# when its name is typed in lower case ("is benidorm safe for kids").
_TRAVEL_TOPICS = frozenset(("geography-and-travel", "travel", "holidays", "places"))
_NOT_A_PLACE_TOPICS = frozenset((
    "sport", "fitness", "health", "body", "eating", "food-and-drink", "money", "work",
    "technology", "pets", "law", "driving", "school-and-study", "hobbies", "home-and-garden",
    "beauty", "clothes"))
_SIGHT_CRITERIA = ("how much walking there is, whether it goes up or down, and how busy it gets "
                   "at the time you would go")
_SIGHT_WHERE = ("The place's own page has the access and the opening times, and a map app shows "
                "the walk and the climb")
_FAMILY_CRITERIA = ("the schools and how you get into them, how much green space is within "
                    "walking distance, and what there is for children to do")
_FAMILY_WHERE = ("The council's own site lists the schools and the areas they take, and an "
                 "afternoon walk round on a school day tells you the rest")
_HOME = re.compile(r"\b(?:flat|house|home|area|neighbourhood|neighborhood|street|road|estate|"
                   r"place|location|block)\b")


def _the_thing(said):
    """The thing the line names, capitalised and ready to say back, or "" when it names none."""
    found = _THING.search(said)
    if not found:
        return ""
    words = found.group("thing").split()
    while words and words[-1] in _STOP:
        words.pop()
    while words and words[0] in ("it", "this", "that", "there", "they", "these", "those"):
        words.pop(0)
    # "is my street safe" said back "My street - can't tell you..." as if the bot owned the street
    # (@snappy-latch, #10238): a thing the person owns is said back as "That street".
    owning = False
    while words and words[0] in ("my", "our"):
        words.pop(0)
        owning = True
    if owning and words:
        return ("that " + " ".join(words))[:1].upper() + ("that " + " ".join(words))[1:]
    # "is it a nice place" leaves "a" behind once "it" is dropped, and "A - I have no way of
    # seeing a place" is not a sentence: an article with nothing after it names nothing.
    while len(words) > 1 and words[-1] in ("a", "an", "the", "one", "career", "idea", "option",
                                           "choice"):
        words.pop()
    if len(words) == 1 and words[0] in ("a", "an", "the", "one"):
        return ""
    if not words or words[-1] in _NOT_A_THING:
        return ""
    thing = " ".join(words)
    if len(words) == 1 and words[0] in _BARE_NOUN:
        thing = "that " + words[0]
    return thing[:1].upper() + thing[1:]


def _pool(said, named=False, other_subject=False, travel=False):
    """The pool for the kind of thing being judged, with the criteria and place that go with it.

    `(None, None, None)` when the line names a kind nothing here can speak to, so the hedge it had
    is kept rather than replaced with criteria about the wrong thing.

    Order is the reading: the most specific kind wins, and a class in the line ("for kids", "with a
    toddler", "on a budget") beats the verb it is asked with, so "is benidorm safe for kids" gets
    the child's criteria and not the crime map (@spare-leopard, #10238). `named` says the line has
    a capitalised name in it, which is how a place is named when no place word is used, and
    `other_subject` says the understanding engine read the line as being about something that is
    not a place at all, which no number of children turns into a trip.
    """
    if _SAFE.search(said) and _SAFE_OBJECT.search(said) and not _HOME.search(said):
        return SAFE_OBJECT, _SAFE_OBJECT_CRITERIA, _SAFE_OBJECT_WHERE
    if _SCHOOL.search(said):
        return SCHOOL, _SCHOOL_CRITERIA, _SCHOOL_WHERE
    if _STAY.search(said):
        return STAY, _STAY_CRITERIA, _STAY_WHERE
    if _FOOD.search(said):
        return FOOD, _FOOD_CRITERIA, _FOOD_WHERE
    if _CLASS.search(said):
        return CLASS, _CLASS_CRITERIA, _CLASS_WHERE
    # A sight comes before the child: "is the museum any good for kids" is a walk and a crowd,
    # not a flight and a beach.
    if _SIGHT.search(said):
        return SIGHT, _SIGHT_CRITERIA, _SIGHT_WHERE
    if _RAISING.search(said) and _WITH_CHILDREN.search(said):
        return FAMILY, _FAMILY_CRITERIA, _FAMILY_WHERE
    # A child in the line makes it a trip with children, unless the line is about the home they
    # would live in: "is it a good area for families" asked about a flat wants the walk and the
    # noise, not the flight and the beach.
    # A child on its own does not make a trip: "is rugby safe for kids" is a question about rugby,
    # and it was answered with "the flight or the drive, the heat, and how far the beach is" - a
    # holiday nobody in the line had mentioned (@clean-salmon). The child is read as a trip only
    # when the line has somewhere to go in it: a place word, a trip word, or a place named by name.
    # Safety with no place word is the same fault from the other side - "is rugby safe" is not a
    # street - so the child does not carry it either, and whatever the line had is left standing:
    # an honest "I don't know", or the entry that does answer it.
    somewhere = bool(_PLACE.search(said) or _TRIP.search(said) or named or travel)
    # A safety question about a thing with no place in it is not a trip, and the child in it does
    # not make it one: "is gymnastics safe for toddlers" and "is rugby safe for kids" were both
    # told about the flight, the heat and the walk to the beach. The thing has to be somewhere to
    # go - a place word, a trip word, a name, or a line the understanding engine read as travel -
    # and a line that names no thing at all ("is it ok with a toddler") keeps the criteria it had.
    if (_WITH_CHILDREN.search(said) and (somewhere or not _SAFE.search(said))
            and not (other_subject and not somewhere)
            and not (_SAFE.search(said) and _the_thing(said) and not somewhere)
            and not (_HOME.search(said) and not _TRIP.search(said))):
        return WITH_CHILDREN, _CHILD_CRITERIA, _CHILD_WHERE
    # Safety is about a place. A job, a marriage, a file and an account are not streets.
    if _SAFE.search(said) and not _PLACE.search(said):
        return None, None, None
    if _SAFE.search(said):
        return SAFE_, _SAFE_CRITERIA, _SAFE_WHERE
    if _WALK.search(said):
        return WALK, _WALK_CRITERIA, _WALK_WHERE
    if _TRIP.search(said):
        return TRIP, _TRIP_CRITERIA, _TRIP_WHERE
    if _HOME.search(said):
        return HOME, _HOME_CRITERIA, _HOME_WHERE
    if _SCREEN.search(said):
        return SCREEN, _SCREEN_CRITERIA, _SCREEN_WHERE
    if _JOB.search(said):
        return JOB, _JOB_CRITERIA, _JOB_WHERE
    return OTHER, "", ""


_PAST_ASK = re.compile(r"^(?:and\s+)?(?:was|were|did|how was|how were|how did)\b")


def reads_as_a_verdict_ask(text):
    """True when the line asks the bot to judge a thing it cannot see."""
    said = re.sub(r"\s+", " ", str(text or "").lower().replace("\u2019", "'")).strip()
    if not said or not VERDICT_ASK.search(said):
        return False
    if _ABOUT_THE_BOT.search(said):
        return False
    # A feeling answered as a decision to weigh up has no warmth in it at all: "is it ok to feel
    # like this" got the three things that settle a purchase (@spare-leopard, #10238).
    if _FEELING.search(said):
        return False
    # "was it a nice holiday" is past tense about a thing nobody has named: the person is weighing
    # something they already did, or asking the bot about its own, and either way criteria for a
    # trip not yet booked is the wrong shape.
    if _PAST_ASK.search(said) and _the_thing(said).lower() in ("", "it", "that", "this", "they"):
        return False
    return not NOT_A_JUDGEMENT.search(said)


def reads_as_a_hedge(reply):
    """True when the reply is the search hedge this file replaces."""
    said = str(reply or "").strip().lower().replace("\u2019", "'")
    return any(said.startswith(opener) for opener in HEDGE_OPENERS)


def _the_topics(memory):
    """The topics the understanding engine read the line as being about."""
    if not isinstance(memory, dict):
        return set()
    understood = memory.get("understood") or {}
    if not isinstance(understood, dict):
        return set()
    topics = set(understood.get("topics") or ())
    if understood.get("topic"):
        topics.add(understood["topic"])
    return topics


def pool_for(text, memory=None):
    """The pool of replies for a judgement ask on a thing the bot cannot see, or None.

    The caller picks from the pool with the memory in hand (`pick` needs the turns), so this
    returns every phrasing for the kind of thing the line names.
    """
    raw = re.sub(r"\s+", " ", str(text or "").replace("\u2019", "'")).strip()
    said = raw.lower()
    if not reads_as_a_verdict_ask(said):
        return None
    # The capitals are read off the line as it was typed: a place named by name has no place word.
    topics = _the_topics(memory)
    pool, criteria, where = _pool(said, named=bool(_NAMED.search(raw)),
                                 other_subject=bool(topics & _NOT_A_PLACE_TOPICS),
                                 travel=bool(topics & _TRAVEL_TOPICS))
    if pool is None:
        return None
    if pool is OTHER and not _the_thing(said):
        # "is that ok", "is it worth it": a bare doubt with nothing named keeps the hedge, because
        # criteria for a thing nobody can point to is posture, not an answer.
        return None
    if pool is OTHER:
        return pool
    thing = _the_thing(said)
    lead = thing + " \u2014 " if thing else ""
    said_lines = []
    for line in pool:
        line = line.format(lead=lead, criteria=criteria, where=where)
        said_lines.append(line if lead else line[:1].upper() + line[1:])
    return tuple(said_lines)


def answer_for(text, memory=None, reply=""):
    """A verdict ask the bot can help with, said honestly, or None.

    `reply` is what the bot was going to say. Only the search hedge is replaced, so any entry, any
    module and the composer's own answer all keep the turn.
    """
    if not reads_as_a_hedge(reply):
        return None
    pool = pool_for(text, memory)
    if not pool:
        return None
    return pick(pool, memory if isinstance(memory, dict) else {}, text)
