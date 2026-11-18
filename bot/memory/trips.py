"""A trip the person is going on, said plainly, is answered about the trip.

The store files a trip in the words it was said in ("Cornwall in August"), so the parts of it are
there to answer with - where, when, and who is going. What was missing was the reply to the line
itself. Main answered

    we're going to cornwall in august   -> "Noted: you're going to cornwall in august."
    were going to spain in july         -> "Thanks for telling me - I'm here if you want to dig
                                            into any of that."
    were off to spain in june           -> "I'm listening - say more if it helps."
    we booked cornwall for august       -> "Good - that's one off the list."

which is the line said back, a stock line, or a line about nothing in particular. A friend says
something about the trip: what the time of year means for booking it, what changes with two kids
in the car, and often one thing they would want to know themselves.

The second half is the follow-up. Once a trip is live, the short line that only adds a detail to
it - "with two kids", "for a week", "we're driving" - is a detail of the trip and is answered
about the trip, where main echoed it back ("Got it - the kids would love it").

Both shapes are read here and nowhere else, and every other line is left alone: a question about
where to go, a trip already taken ("we went to cornwall in august"), a plan that is not a trip
("we're going to the gym tomorrow"), and the store's own recall asks all keep their own answers.
"""
import re

from . import ack, facts, last_bot, not_a_trip, plan_line, user
from .facts import DAYS, KIN, MONTHS, NOT_PLACES, PLACE_VERBS

# The verb that says a trip is coming, and the "to <place>" that follows it. "i'm going to be
# late", "we're going to see", "it's going to rain" and "going to try" are the same shape and not
# a trip, so a place has to be named and it has to be the object of the going.
GOING = re.compile(
    r"\b(?:we're|we\s+are|were|we've|weve|we\s+have|we|i'm|i\s+am|im|i've|ive|i\s+have|i|"
    r"they're|theyre|they\s+are|they've|theyve|they|he's|shes|she's|hes)\b\s*"
    r"(?:(?:thinking\s+of|planning|hoping\s+to|looking\s+at|off|away)\s+)?"
    r"(?:going|off|heading|flying|driving|sailing|travelling|traveling|"
    r"booked|booking)\b", re.I)
# The going words on their own, for a line that leaves the person out ("going to cornwall in
# august", "off to spain for a week").
GOING_BARE = re.compile(
    r"^\s*(?:and\s+|so\s+|oh\s+|right\s+|ok(?:ay)?[ ,]+)*"
    r"(?:thinking\s+of\s+|planning\s+|hoping\s+to\s+|looking\s+at\s+)?"
    r"(?:going|off|heading|flying|driving|sailing|travelling|traveling|"
    r"booked|book|booking)\b", re.I)
TO_PLACE = re.compile(r"\b(?:to|into)\s+((?:the\s+)?[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,3})",
                      re.I)
# "booked a cottage in cornwall in august" names the place after "in", not the thing booked.
IN_PLACE = re.compile(r"\bin\s+((?:the\s+)?[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,3})",
                      re.I)
# "we booked cornwall for august" names the place without a "to".
BOOKED_PLACE = re.compile(r"\b(?:booked|book|booking)\s+(?:us\s+)?"
                          r"((?:the\s+)?[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,3}?)\s+"
                          r"(?:for|from)\b", re.I)
# Words that can follow "to" and are never the place: "going to be late", "off to get the kids",
# "going to try", "heading to work" (a place, but not a trip), "going to bed".
NOT_A_TRIP = re.compile(r"^\s*(?:a|an|the|my|our|his|her)\s+(?:wedding|party|concert|gig|"
                        r"festival|funeral|match|game|show|play|hen|stag|birthday|christening|"
                        r"meeting|conference|interview|appointment|course|class|exam|test)\b", re.I)
# An amount said after "in" is not a place: "cut my insulin in half" was read as a trip to Half
# and answered "Half, lovely. When is it?", and the same shape reads "in two", "in bits", "in
# pieces". A share is what is left of something, never somewhere the person is going.
NOT_AN_AMOUNT = frozenset("""half halves quarter quarters third thirds two three four five six ten
twenty hundred dozen bits pieces lumps chunks squares slices rounds""".split())
NOT_A_PLACE = frozenset("""be get got go going do see try have check sort pick take make book
lose losing lost sell selling sold lose win won keep quit leave leaving start stop manage afford
ask tell call look find put buy eat drink work bed sleep town home hospital doctor dentist
prison jobcentre funeral crematorium coroner interview solicitor tribunal
drive fly stay visit meet leave arrive catch ride walk swim camp pitch collect drop fetch
play watch celebrate shop rest
# A body failing is not a place: "i'm going to pass out", "going to faint", "im going to be sick"
# are read as a trip to Pass Out and said back as "{place}, lovely. When is it?". The verbs are
# here with the other things nobody travels to.
pass faint collapse vomit throw sick black die choke bleed fit seizure
# Going round the same ground is not a journey: "im going round in circles at work" was read as
# a trip to a place called Circles and answered "Circles - nice. When are you going?", which is the
# last thing a person who has just said they are stuck wants to hear. The words a loop is said with
# are nobody's destination.
circles circle loops loop
# "book recommendations for my dad" is a person asking for a book to read, not a trip with their
# father in it: "book" is the noun here, so the word behind it was read as the place and the reply
# was "Recommendations is booked, then. Get the big days out booked now too". A word that asks for
# a pick is never somewhere to go.
recommend recommends recommended recommendation recommendations suggest suggests suggested
suggestion suggestions ideas idea picks tips
# A person going to harm themselves is not a trip to a place called Kill Themselves: with no
# person named in the chat, "they are going to kill themselves" was answered "Kill Themselves,
# lovely. When is it?".
kill kills killing killed suicide overdosing overdose hang hanging harm hurt hurting starve
myself yourself himself herself ourselves themselves
school work church gym shop shops tesco asda aldi lidl mum mums dad dads nan gran grandparents
kids children baby partner wife husband friend friends sister brother them him her you me us
it that this there somewhere anywhere out in on up down back again now later today tomorrow
tonight yesterday first last next""".split()) | NOT_AN_AMOUNT
# A relative or a friend after "to" is the person being visited, not the place: "im off to my
# brothers tonight" is an evening with family, and the trip reader was answering it "My Brothers,
# lovely. What do you want to sort out first, where to stay or what to do while you are there?"
# - a holiday named after a person. The possessive is what makes the word a person ("my brothers"
# is the people, "brothers" alone is not), so this shape says the visit back as "your brother's"
# and asks about the visit rather than a holiday. Group words that are not in KIN are listed here
# because the same line says "my grandparents" and "my kids".
A_PERSON_IS_NOT_A_PLACE = re.compile(
    r"^(?:my|our|his|her|their)\s+(?P<person>(?:"
    + "|".join(sorted(KIN + ("kids", "children", "grandparents", "grandchildren", "family",
                             "relatives", "folks", "twins", "mate", "in laws", "in-laws",
                             "inlaws", "in law", "in-law", "inlaw"), key=len, reverse=True))
    + r"))(?P<plural>s)?(?P<poss>['\u2019]s?)?(?!\w)", re.I)
# A word after the person is a thing of theirs - "my mums house", "my kids school", "my sisters
# wedding", "my dads work" - and the possessive belongs before it, not after the whole phrase
# ("Your Mums House's"). Only a function or a time word ends the person without naming a thing:
# "my parents in leeds", "my brothers tonight", "my mum next week".
_NOT_A_THING_OF_THEIRS = frozenset((
    "in", "on", "at", "for", "with", "from", "to", "by", "during", "after", "before",
    "and", "or", "but", "next", "this", "last", "tomorrow", "today", "tonight", "soon",
    "later", "again", "now", "then", "there", "here", "every", "each", "all", "week",
    "weekend", "month", "year"))
# The court date somebody chose and wants: an adoption, and the hearing that makes it final. Every
# other court date is a place a person is sent, but this one is the day the family is made, and
# "Court, lovely. When is it?" is the right answer to it - so the court arm below stands aside for
# these words rather than standing the whole line down.
A_HAPPY_COURT = r"\b(?:adopt\w*|adoption)\b"
# The trip shapes that are not a trip to somewhere: "going to the gym", "off to work".
# A thing nobody looks forward to is not a plan, and the trip reading is warm by design
# ("Court, lovely. When is it?" answered "i am going to court next week"). The legal and the
# bereavement appointments join the everyday run: they are places the person is sent, not places
# they chose.
EVERYDAY_TRIP = re.compile(
    r"\b(?:to the (?:gym|shops?|pub|supermarket|doctors?|dentist|hospital|school|office|bank)|"
    r"off to work|going to work|to bed|to sleep|to the loo|to the tip|"
    rf"(?!.*{A_HAPPY_COURT})to (?:the )?court|to (?:the )?prison|to (?:the )?job ?centre|"
    r"to (?:a |the )?funeral|"
    r"to (?:the )?crematorium|to (?:the )?coroner'?s?|to (?:a |the )?tribunal|"
    r"to (?:an |the )?interview)\b", re.I)
# What the person is going *on* rather than *to*: "a cruise", "holiday", "a trip to rome".
ON_A = re.compile(r"\b(?:on|for)\s+(?:a\s+|the\s+|our\s+)?(holiday|holidays|trip|break|"
                  r"cruise|weekend away)\b", re.I)

# Who is going. The words a person uses for the people in the car, and the phrase the reply says
# back: "with two kids" keeps the number, "with the kids" keeps the "the".
WITH_WHO = re.compile(r"\bwith\s+((?:the|my|our|his|her|both|all|a|an|two|three|four|\d+)\s+"
                      r"[a-z0-9](?:(?!\b(?:for|on|at|next|this|during|over|until)\b"
                      r"|\bin\s+(?!law\b))[a-z0-9' -])*)", re.I)
# A duration is the length of the trip: "for a week", "for two weeks", "for the weekend".
# How long a stay is, said as a number: "for ten days", "for a couple of weeks", "for 8 nights".
# A number word is a number, so the list is every one a person says, not the first four.
NUMBER_WORD = (r"(?:\d+|a\s+few|a\s+couple\s+of|few|several|a|an|one|two|three|four|five|six|"
               r"seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty)")
FOR_HOW_LONG = re.compile(r"\bfor\s+(" + NUMBER_WORD + r"\s+"
                          r"(?:day|days|night|nights|week|weeks|fortnight|month|months)?s?"
                          r"|the weekend)\b", re.I)
# "two weeks", said on its own after the trip, is still the length of the stay: people answer
# "how long are you going for" with the bare words and no "for" in front of them.
JUST_HOW_LONG = re.compile(r"^(?:(?:just|only|about|maybe|probably)\s+)?"
                           r"(" + NUMBER_WORD + r"\s+"
                           r"(?:day|days|night|nights|week|weeks|fortnight|month|months))$"
                           r"|^(?:(?:just|only|maybe)\s+)((?:a|the)\s+weekend)$", re.I)
# A time is not a place. "im going to be sick in a minute" put the when after the "in", and the
# trip reader took the words for the where: the reply was "A Minute - nice. When are you going?".
# A part of the day, or a length of time, is the one thing that can follow "going to be ... in"
# and never names somewhere, so the place keeps its own answer and this line is not a trip.
TIME_WORD = frozenset("""morning afternoon evening night today tomorrow yesterday
minute minutes moment moments hour hours second seconds bit while sec secs min mins""".split())
DURATION = re.compile(r"^(?:" + NUMBER_WORD + r"\s+)?(?:second|minute|moment|hour|bit|while|"
                      r"day|week|month|fortnight)s?$", re.I)
# What to take is the question people ask once the trip is settled, so it is a detail turn and
# not a punt to a search engine: the answer is the month, the place and the people they named.
PACKING = re.compile(r"^(?:and\s+|also\s+|oh\s+)?(?:what|anything)\s+(?:should|shall|do|would|"
                     r"will|to)?\s*(?:we|i|you)?\s*(?:pack|bring|take)\b(.*)$", re.I)
# The same question said as a need rather than as "what": "should i take anything", "do i need to
# bring towels", "will i need a coat". Nothing in the deck's follow-ups matched the shape above, so
# a visit to family was answered with the card about somebody coming to stay instead.
PACKING_SAID = re.compile(
    r"^(?:and\s+|also\s+|oh\s+)?(?:should|shall|do|does|would|will|can|could)\s+"
    r"(?:we|i|you)\s+(?:need\s+to\s+)?(?:pack|bring|take|need)\b(.*)$", re.I)
# One thing they want to know about: "will i need a coat", "do i need an umbrella", "will i need my
# boots". A visit's packing answer is what to take to somebody's house - a bottle for the table, a
# bag for the night - and it was answering this with it: "we are going to my mums on sunday" /
# "will i need a coat" got "For Your Mum's, nothing much: something for the table...", where the
# coat card is what was asked. The thing named is the question, so the visit stands down and the
# reader that knows about that thing answers. A vague word ("anything", "something", "much") names
# no thing and stays the packing question it is.
ONE_THING_NEEDED = re.compile(
    r"^(?:and\s+|also\s+|oh\s+)?(?:should|shall|do|does|would|will|can|could)\s+(?:we|i|you)\s+"
    r"need\s+(?!to\b)(?:a\s+|an\s+|my\s+|our\s+|some\s+|any\s+)?(?P<thing>[a-z]+)", re.I)
NO_THING_NAMED = frozenset("""anything something nothing much else more anymore any
another""".split())


def _one_thing_they_need(low):
    """The thing a "will i need ..." asks about, or "" when it names nothing in particular."""
    found = ONE_THING_NEEDED.match(low)
    if not found:
        return ""
    thing = found.group("thing").lower()
    if thing in NO_THING_NAMED:
        return ""
    return thing


# An invitation is not a destination: "im going to a picnic on sunday" then "what should i pack"
# was answered "For A Picnic: layers, one warm thing for the evening, and shoes you can walk in" -
# a walking list for a plate of food - because the trip reading takes anything after "to a" as the
# place. What people go to has its own card (the food that travels, the clothes for a wedding), so
# the trip module keeps the reading and stands down for the packing question.
# October is the month the warm-week list is out of season. That list is written for a month and
# not for a place, so it answers "were going to the lakes in october" with cotton tops, shorts and
# swimwear, "as May and October evenings turn cool even in Spain or Italy" - true of Spain and
# Italy, not of the Lakes. There the bag for the place and the month is the answer. The rest of the
# year the list does know the month (light cotton in high summer, a coat and layers for the cold),
# so this module leaves those packing questions to it: it is the better answer for "im going to
# lisbon in june", "were going to norway in january" and "were going to scotland in november", and
# for a place with no entry of its own there is no card to lose (main already gives Cornwall in
# July the store's bag).
OUT_OF_SEASON = frozenset(("october",))
AN_EVENT_NOT_A_PLACE = frozenset("""picnic barbecue bbq party wedding funeral christening festival
concert gig show play match game race hen stag birthday dinner lunch barbecue""".split())
# What follows "pack" decides whose line it is. "for the kids" is still the trip; "for the
# hospital" is a different question with a different answer, and that is not this module's.
PACKING_FOR = re.compile(r"^(?:for\s+(?:the\s+)?(?:kids?|children|us|me|him|her|them|wife|husband|"
                         r"partner|trip|holiday|week|weekend|walk|beach|evenings?)|"
                         r"for\s+(?:a|one|two|three|four|five|six|ten|\d+)\s+"
                         r"(?:day|days|night|nights|week|weeks|fortnight|months?)|"
                         r"this time of year)$", re.I)
PACKING_NOTES = (
    "for {place} in {month}: layers for the evenings, one warm thing whatever the forecast says, "
    "and shoes you can walk in.",
    "pack light for {place} in {month} - a waterproof, something warm for the evening, and half "
    "the clothes you think you need.",
)
PACKING_NO_MONTH = (
    "for {place}: layers, one warm thing for the evening, and shoes you can walk in.",
)
# A trip with no place named yet is still the thing a packing question is about: "im planning a
# weekend away with my sister in october" then "what should we pack" was four or five nappies.
PACKING_NO_PLACE = (
    "for {kind} in {month}: layers, one warm thing for the evening, a waterproof and shoes you "
    "can walk in - and half the clothes you think you need.",
    "{kind} in {month} fits in one bag: a change of clothes for each day, something warm for the "
    "evening, a waterproof and shoes you can walk in.",
)
PACKING_NO_PLACE_NO_MONTH = (
    "for {kind}: layers, one warm thing for the evening, a waterproof and shoes you can walk in.",
)
PACKING_WITH_KIDS = ("with the kids, one change of clothes each per day and a bag for the wet "
                     "things covers it.")
# Going to family is not a holiday with a packing list: what they need is the thing you would put
# on the table, and a bag if they are staying. "For Your Mum's: layers, one warm thing for the
# evening, and shoes you can walk in" answered a dinner with their mum like a week in the Lakes.
VISIT_PACKING = (
    "for {place}, nothing much: something for the table - a bottle, a pudding or flowers - and a "
    "bag for the night if you are staying over.",
    "{place} is the easy kind of visit to pack for: a bottle or a pudding for the table, and "
    "check whether they want you for the whole day or just the evening.",
    "for {place}: what you would bring to a table, and a bag only if you are staying the night.",
)
# A visit for a meal has one thing to bring, and it is not a waterproof.
VISIT_PACKING_FOR_A_MEAL = (
    "take a bottle and something for after - a pudding, cheese and biscuits, or a box of chocolates "
    "- so you are not competing for their oven. Ask what they are cooking, then bring the thing "
    "that goes with it.",
    "a bottle for the table and something for after, and ask what they are cooking so what you "
    "bring goes with it rather than fighting for the oven.",
)
# A visit to somebody with a new baby is its own kind of visit, and the list is not a bottle for
# the table: what they need is a meal they do not have to cook, and a visit that does not outstay.
VISIT_PACKING_FOR_A_BABY = (
    "nothing for the baby - they have more than they can use. Take food: a meal for the freezer "
    "or something for lunch, and keep the visit to an hour unless they ask you to stay.",
    "what a house with a new baby wants is a cooked meal and short visits, so take dinner in a "
    "dish you do not want back, and ask before you hold the baby.",
)
# How long to stay is the question a visit brings, and the answer is about family rather than
# about hotels: "how long should we stay" after "we are going to my in laws" was a search hedge.
A_STAY_LENGTH = re.compile(r"\bhow (?:long|many (?:nights|days)) (?:should|shall|do|would|will) "
                          r"(?:we|i) (?:stay|stop|be there|go for)\b", re.I)
VISIT_HOW_LONG = (
    "two nights is the sweet spot for family - long enough to settle in, short enough that you "
    "are missed.",
    "one night the first time, two if it is a long drive. Leave while everyone is still enjoying "
    "it rather than when the conversation has run out.",
    "a weekend is plenty unless there is something on: arrive Saturday, go home Monday, and say "
    "when you are leaving before you get there.",
)
# How long a visit lasts is a different question from how long a holiday lasts: nobody goes to
# their in-laws for the beach days. "we are going to my in-laws for a week" was answered "A week
# gives you time for the beach days and a couple of trips out without rushing." - the week note
# for a coast - because the visit reading left the length to the holiday notes.
VISIT_A_WEEK = (
    "a week with family is a long visit: agree the leaving day before you go, and keep an "
    "afternoon or two that are just yours.",
    "a week is plenty to be in somebody else's house - say when you are leaving, and plan one day "
    "of it that is just yours.",
)
VISIT_A_FEW_DAYS = (
    "a night or two is the easy length for a visit: enough to catch up, short enough that nobody "
    "is hosting for too long.",
    "one or two nights is right for family: bring something for the table, and leave while you "
    "are both still enjoying it.",
)
VISIT_A_WEEKEND = (
    "a weekend is the classic visit - one evening together, one day out, and home before the week "
    "starts.",
    "the weekend is enough for most visits: Friday night to Sunday afternoon, and say on the "
    "Friday when you are heading back.",
)
A_MEAL = re.compile(r"\b(?:dinner|lunch|tea|supper|brunch|barbecue|bbq|roast)\b", re.I)
A_NEW_BABY = re.compile(r"\b(?:new\s?born|new baby|just had a (?:baby|girl|boy)|had a baby|"
                        r"baby (?:is|was) (?:born|due)|\dbaby)\b|\bnewborn\b", re.I)
# "how long is the drive" is answered about the drive and not with a search hedge - we know the
# place and the month, and the honest thing to add is how to make the journey bearable.
THE_FLIGHT = re.compile(r"\bhow (?:long|far) (?:is|does) the flight\b")
# A journey asked about by its length, rather than by how to make it bearable: "how long is the
# flight" wants the hours, so a place whose card says them keeps the turn.
HOW_LONG_ASK = re.compile(r"\bhow (?:long|far)\b", re.I)
# "how do we get there" picks no mode, so the reply must not pick one for them: an island is not
# a drive and a city four hours away is not a flight.
THE_MODE = re.compile(r"\bhow (?:do|are) we get(?:ting)? there\b")
THE_DRIVE = re.compile(r"\bhow (?:long|far) (?:is|does) the (?:drive|journey|trip)\b"
                       r"|\bhow (?:long|far) (?:will|would) the (?:drive|journey|trip) "
                       r"(?:take|be)(?:\b|$)"
                       r"|\bhow do we get there\b|\bhow are we getting there\b", re.I)
# The journey asked as a question rather than added as a detail: "how long will it take to
# drive", "how long to get there", "how far is it", "how long does it take to fly". A question
# has no subject and no mode word in the shapes `THE_DRIVE` and `BY` read, so it fell to the
# modules that read the same words on their own, and `how long will it take to drive` was
# answered with the driving-lessons card ("Most people need around 45 hours of lessons plus 20
# hours of private practice before they pass") in the middle of a chat about a trip to Cornwall.
# The mode is in the verb, so each shape names its own.
THE_JOURNEY_ASK = re.compile(
    r"\bhow\s+(?:long|far)\s+(?:will|would|does|do|did|is|are|might)\s+(?:it|that|this|the\s+"
    r"(?:drive|journey|trip|flight|train))?\s*(?:take|be|takes)?\s*(?:to\s+)?"
    r"(?P<mode>drive|get\s+there|get\s+to|travel|walk|sail|go)\b"
    r"|\bhow\s+(?:long|far)\s+(?:it|is\s+it)\b[^?]{0,20}\b(?P<mode2>driving|drive|flight|train)\b"
    r"|\bhow\s+long\s+to\s+(?P<mode3>get\s+there|drive|fly|travel)\b", re.I)
# The length of the stay, asked rather than told: "how long are we there for", "how many
# nights", "how long are we going for". Asked while the plan has no length on it, the only honest
# reply is the question back - the search hedge and the countdown to the month were both worse
# than "how long are you thinking?". The shapes name a stay, never a journey: "how long is the
# flight" keeps its own answer, and "how many days are there left" is not this ask.
THE_LENGTH_ASK = re.compile(
    r"\bhow\s+long\s+(?:are|is|were|was)\s+(?:we|you|i|it)\s+(?:there|away|staying|going"
    r"|going\s+for|staying\s+for|away\s+for)\b"
    r"|\bhow\s+long\s+(?:are|is|were)\s+(?:the|our|my|your)\s+(?:trip|holiday|break|stay)\b"
    r"|\bhow\s+many\s+(?:nights|days)\s+(?:are\s+we|is\s+it|will\s+we|do\s+we|have\s+we"
    r"|should\s+we|would\s+we)\b"
    r"|\bhow\s+many\s+(?:nights|days)\s*[?.]?\s*$"
    r"|\bhow\s+long\s+for\s*[?.]?\s*$", re.I)
# What a friend says when the plan has no length on it: the question back, and the one reason the
# nights matter first. Nothing about the place or the month - the chat may have said neither.
THE_LENGTH_NOT_SAID = (
    "You haven't said how long - how many nights are you thinking?",
    "Nothing said about how long yet - how many nights are you thinking?",
    "How many nights are you thinking? The plan hasn't got the length on it yet.",
)
THE_LENGTH_NOT_SAID_NAMED = (
    "You haven't said how long - how many nights are you thinking for {named}?",
    "How many nights are you thinking for {named}? Nothing said about that yet.",
)
THE_NIGHTS_FIRST = (
    "The nights decide what you can book, so it's worth settling that first.",
    "Once the nights are fixed the place to stay and the packing both follow.",
    "Get the nights settled and the rest of it falls into place.",
)

# The mode a journey question names, in the words this module answers a detail with.
JOURNEY_MODE = re.compile(r"\bdriv\w*|\bby\s+car\b|\bin\s+the\s+car\b", re.I)
# How they are getting there. The reply is different for the car and for a flight, and it is the
# one thing a friend asks about a trip they have just heard about.
BY = re.compile(r"\b(?:we're|we are|were|i'm|im|i am)\s+(driving|flying|getting the train|"
                r"on the train|taking the ferry|sailing)\b", re.I)

# The months, by what the time of year means for a trip booked into it. Only what is true of the
# month itself: the school holidays, the prices, the light. Nothing about a place the bot would be
# making up.
PEAK = ("july", "august")
BUSY = ("april", "may", "june", "september", "october")
QUIET = ("november", "december", "january", "february", "march")

PEAK_NOTES = (
    "{month} is the busiest, priciest few weeks of the year, so book the place to stay now.",
    "{month} takes the school holidays, so the prices only go one way - book soon.",
    "that is the height of the season: book the place to stay now, and expect slow roads on the "
    "way down.",
)
# The same season, once the place to stay is already booked: what is left to do about it.
PEAK_BOOKED_NOTES = (
    "at the height of the season the popular places fill up, so book the big days out now too.",
    "that is the busiest few weeks of the year, so get the days out booked now as well.",
)
BUSY_NOTES = (
    "it misses the worst of it: cheaper and calmer than August, and the weather is usually "
    "decent.",
    "you have timed it well - {month} is quieter and cheaper than the school holidays.",
)
QUIET_NOTES = (
    "that is out of season, so it will be quiet and cheap, and dark by half four.",
    "out of season: quiet, cheap, and short days.",
)
# The quiet half of the year is quiet only where the season says so. Lanzarote in January is the
# winter sun people fly for, and the knowledge base's own month picks name it: told "out of season,
# dark by half four" the reply is wrong about the one thing they are going for. So a place the
# month picks name as a place to go that month is told its season, not the general quiet note.
SEASON_NOTES = (
    "that is the season for it, so book soon - the weeks people want go first.",
    "{month} is the good time there: warm days, cool evenings, and the prices know it.",
    "{month} is when it is at its best, so the flights and the rooms are the first thing to sort.",
)
# Places whose season is the winter. The knowledge base's month picks name some of them (the
# Canaries, Cape Verde, Lanzarote) and not others (Tenerife, Madeira), and "out of season, dark by
# half four" is the wrong way round for all of them.
WINTER_SUN = (
    "canaries", "lanzarote", "tenerife", "gran canaria", "fuerteventura", "la palma",
    "cape verde", "madeira", "egypt", "red sea", "dubai", "abu dhabi", "marrakesh",
    "morocco", "cape town", "gambia", "thailand", "maldives", "sri lanka", "goa",
    "barbados", "jamaica", "caribbean", "cancun", "mexico", "florida", "orlando",
)
KIDS_NOTES = (
    "with kids in tow, plan one thing a day and keep a wet-day backup up your sleeve.",
    "with the kids, the beach early and something under cover for the afternoon works best.",
    "kids on a trip like that want one big thing a day and somewhere to dry out afterwards.",
)
KIDS_NUMBERED = (
    "{who}: one big thing a day is plenty, and line up something indoors for the wet afternoon.",
    "with {who}, plan one thing a day and keep a wet-day backup up your sleeve.",
)
KIDS_ONE = "with kids in tow, plan one thing a day and keep a wet-day backup up your sleeve."
WEEK_NOTES = (
    "a week gives you time for the beach days and a couple of trips out without rushing.",
    "a week is about right: long enough to settle, short enough to want to go back.",
)
# A week somewhere that is not a beach is not a week of beach days: Scotland in July is the
# Highlands and the islands, so the note says what a week buys there instead.
WEEK_NOTES_LAND = (
    "a week gives you room for two or three places rather than one, without a day lost to "
    "moving each time.",
    "a week is about right there: enough for the big one and a quiet day either side.",
)
# A season is a when, not a where. "im going to try again in the spring" was read as a trip to a
# place called Spring and answered "The Spring, lovely. What do you want to sort out first?" - the
# person had said when, and the only thing the reply could ask was what they had just said.
SEASON = frozenset("""spring springtime summer summertime autumn autumntime winter wintertime""".split())
SEA_PLACES = frozenset("""cornwall devon dorset sussex kent norfolk suffolk wales pembrokeshire
anglesey skye iona jersey guernsey crete cyprus malta sicily sardinia mallorca majorca ibiza
tenerife lanzarote fuerteventura gran canaria madeira algarve portugal spain greece turkey
croatia italy france""".split())
# A stay counted in days, said back: not every length is a week or a weekend.
DAY_NOTES = (
    "that many days is room for a couple of big things and a slow morning in between.",
    "with that many days, pick the two things that matter and let the rest happen.",
)
WEEKEND_NOTES = (
    "a weekend away gives you two nights, so pick one thing to do properly rather than three.",
    "for a weekend, one big thing a day and a slow breakfast is the whole trick.",
)
LONG_NOTES = (
    "a trip that long means you can stop rushing: a couple of lazy days and one proper day out "
    "each.",
    "with that many days you can plan the big day out for the middle, when everyone has settled.",
)

# What to ask when there is nothing to add: the month is the one thing the advice needs, and a
# friend asks it straight out.
ASK_WHEN = (
    "{place} - nice. When are you going?",
    "{place}, lovely. When is it?",
)
# The same question, for a line that follows one of the bot's own questions: two in a row is an
# interrogation, so the ask becomes an offer.
ASK_WHEN_NO_QUESTION = (
    "{place}, nice - tell me when and I can help you work out what to do with it.",
    "{place}, lovely. Say when it is and I will help you plan the days.",
)
# A day at the beach is a day out rather than a place with a name: the generic outdoors that
# people go to without meaning a particular one.
OUTING = re.compile(r"^the (beach|coast|seaside|park|woods|forest|hills|countryside|lido|"
                    r"zoo|museum|aquarium)$",
                    re.I)
SEA_NOTES = (
    "take more food and water than you think, and check the tide before you set off.",
    "a change of clothes and a towel in the boot covers most of what goes wrong by the sea.",
    "go early for the parking, and take a bag for the wet things on the way back.",
)
LAND_NOTES = (
    "take more food and water than you think, and go early if you are driving there.",
    "sturdy shoes and a bag for the wet things covers most of what goes wrong.",
    "check the opening times before you set off, and take a coat even on a warm morning.",
)
INDOOR_NOTES = (
    "check the opening times and book the timed slot if they have one - it saves the queue.",
    "buy the tickets online the night before, and go at opening rather than the middle of the day.",
)
SEA = ("beach", "coast", "seaside", "lido")
TICKETED = ("zoo", "museum", "aquarium")
# "a day in the park", "a day at the zoo": the open-air ones take "in".
OPEN_AIR = ("park", "woods", "forest", "hills", "countryside")
ASK_WHAT = (
    "what do you want to sort out first, where to stay or what to do while you are there?",
    "what are you hoping to do while you are there?",
    "have you sorted where you are staying, or is that still open?",
)
# The same question for a visit to a person: nobody needs somewhere to stay at their mum's, so
# the trip's two questions are wrong there. The one thing a friend asks is what the visit is for.
ASK_VISIT = (
    "what are you doing while you're there?",
    "what's the plan for the visit?",
    "is it a flying visit or are you staying a while?",
)

# A short line that only adds to the trip: "with two kids", "for a week", "we're driving". It
# carries no verb of its own and asks nothing, which is what makes it a detail of the trip rather
# than a new subject.
JUST_A_DETAIL = re.compile(
    r"^\s*(?:and\s+|oh\s+|also\s+|plus\s+)?(?:with\b|"
    r"for\s+(?:a|one|two|three|four|\d|the\s+(?:week|weekend|month|fortnight))\b|"
    # "two weeks", said on its own, is the length of the stay.
    r"(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(?:day|days|night|nights|week|weeks|fortnight|months?)\b|"
    r"(?:we're|were|we are|i'm|im|i am)\s+(?:driving|flying|getting the train|getting a\s+"
    r"(?:train|flight|ferry)|taking the (?:train|ferry|plane)|sailing|going by\s+"
    r"(?:car|train|ferry|plane)|on the (?:train|ferry))\b|"
    r"by\s+(?:car|train|ferry|plane)\b|"
    # Who is going, counted and said without "with": "two kids" on its own is the same detail as
    # "with two kids", and it was reaching the pool about a change that unsettles sleep.
    r"(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(?:kids?|children|adults)\b|"
    # What to take and how the journey goes are the two things asked about a trip that is
    # settled, so they are detail turns rather than lines for the answers lane.
    r"what\s+(?:should|shall|do|would)\s+(?:we|i|you)\s+(?:pack|bring|take)\b|"
    r"what\s+to\s+(?:pack|bring|take)\b|"
    r"how\s+(?:long|far)\s+(?:is|does|will|would)\s+the\s+(?:drive|journey|trip|flight)\b|"
    r"how\s+(?:do|are)\s+we\s+get(?:ting)?\s+there\b)", re.I)


# The word a friend puts after hearing the trip, so the first thing said is not the plan read
# back to them.
WARM = ("lovely", "nice", "good one")

WORD = re.compile(r"[a-z0-9'\u2019]+")


def _start(said):
    """A reply that begins with a place whose "the" was lowered mid-sentence still opens a line."""
    said = str(said or "")
    return said[:1].upper() + said[1:] if said else said


def _low(text):
    return " ".join(str(text or "").lower().split())


BOOKED = re.compile(r"\bbook\w*\b", re.I)
# A booking that has happened, as against one being asked about: "we booked flights to lisbon",
# "ive booked the cottage". "should i book the vatican museums" is a booking ask, and the card
# answers it.
BOOKED_DONE = re.compile(r"\bbooked\b", re.I)
# What was booked said after "booked" names the thing, not the trip, and the place it happens in
# follows an "in": "we booked a cottage in cornwall for august" is a trip to Cornwall, and read
# by BOOKED_PLACE alone the thing booked ("a cottage") was the place - the reply said "A Cottage
# in August is booked, then."
BOOKED_IN_PLACE = re.compile(
    r"\bbook\w*\b[^.!?]{0,40}?\bin\s+((?:the\s+)?[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,3})",
    re.I)
# The place, and then the date behind an "in": "we booked spain in july", "we booked the
# caravan in august". BOOKED_PLACE asks for a "for" or a "from" behind the place, so the country
# here matched nothing: IN_PLACE then took "july", the month was refused as a place, and the whole
# booking was lost - the person was told "Sorted. Is there anything left to sort before it?" and
# the store had no trip in it at all. The words after "in" have to say when for this to be the
# place, so "we booked a table in town" stays a table.
WHEN_WORD = "|".join(sorted(MONTHS | DAYS | SEASON, key=len, reverse=True))
BOOKED_IN_WHEN = re.compile(
    r"\b(?:booked|book|booking)\s+(?:us\s+)?"
    r"((?:the\s+)?[a-z][a-z'\u2019-]*(?:\s+[a-z][a-z'\u2019-]*){0,3}?)\s+in\s+"
    r"(?:" + WHEN_WORD + r"|next|this|a\s+(?:few|couple)|\d)", re.I)


# A trip is to somewhere, and people are not somewhere. "im off to my brothers tonight" is an
# evening with them, and the trip reader said it back as "My Brothers, lovely. What do you want to
# sort out first, where to stay or what to do while you are there?" - a town with their name. The
# relations the store knows are the fence, in the singular and the plural, rather than a list of
# the words nobody travels to: "going to my mums" is a house, not a destination either.
# The relations the store keeps in the singular only, in the plural people use for the pair or the
# group: "im going to my grandparents for the day" is the same visit as "my mum and dad".
PLURAL_RELATIONS = frozenset("""grandparents parents kids children siblings relatives inlaws
    grandchildren""".split())

A_POSSESSION_NOT_A_PLACE = re.compile(
    r"^(?:my|our|his|her|their|the)\s+([a-z]+(?:\s+in\s+law)?)(?:'s|\u2019s|s)?$")


def _a_relation_not_a_place(place):
    """True when the place the line names is somebody of theirs, not somewhere."""
    found = A_POSSESSION_NOT_A_PLACE.match(place.strip())
    if not found:
        return False
    word = found.group(1).lower()
    return (word in facts.RELATIONS or word.rstrip("s") in facts.RELATIONS
            or word in PLURAL_RELATIONS)


# Somebody in a hospital bed, a hospice or a care home is not a day out, and the words that say
# so come after the person: "going to see my nan in a care home". The visit reading in
# `not_a_trip` turns those lines away already, and this reader takes the same fence so that the
# care home is not read as a destination of its own - the base named it "A Care Home" and asked
# when it was, and the person rule said "Your Mum's, lovely" over a line about a ward. A caring
# place named beside a real destination is a different line and keeps its trip.
A_CARING_PLACE_HEAD = re.compile(
    r"^(?:the\s+|a\s+|an\s+)?(?:hospital|hospice|care home|nursing home|residential home|"
    r"clinic|infirmary|surgery|ward|a&e|ae|icu|intensive care|high dependency|coronary care)\b",
    re.I)


def _a_person_visited(line):
    """The person a line is going to see, with the words that belong to them, or "".

    "im off to my brothers tonight" and "we are going to my in laws" name a person, and a person
    is not a destination - but the visit is still something to answer, and the shrug ("Worth
    doing. What would you like help with first?") is not it. The words after "to" are kept as the
    trip's place so `_as_a_visit` can say them back as theirs, and a visit said as the purpose of
    the journey ("visiting my parents this weekend", "im going to see my sister on sunday") names
    no place at all, so it is read from the line itself.
    """
    if not_a_trip.IN_A_CARING_PLACE.search(str(line or "")):
        return ""
    who = not_a_trip.the_visit(line)
    if who:
        return who
    phrase = _places(line, a_visit=True)
    return phrase if phrase and _a_relation_not_a_place(phrase) else ""


def _places(line, a_visit=False):
    """The place a line says it is going to, in the person's own casing, or "".

    With a_visit the relation fence below stands aside: a person is not a place, and the visit
    answer needs the words to say back ("my brothers"), not the trip card that names a town.
    """
    booked = BOOKED.search(line)
    if booked and _the_thing_booked(_low(str(line)[booked.end():])):
        # "we booked a table for friday", "we booked tickets for the match": what people book is
        # often a thing rather than somewhere to go, and where it happens is not a trip.
        return ""
    for pattern in (TO_PLACE, BOOKED_IN_PLACE, BOOKED_IN_WHEN, BOOKED_PLACE, IN_PLACE):
        found = pattern.search(line)
        if not found:
            continue
        words = [w for w in found.group(1).split() if w]
        # Keep the place short: "cornwall in august" gives "cornwall", not the whole tail. A word
        # that says when, who or how long starts the rest of the sentence, not the place.
        kept = []
        for word in words:
            bare = word.lower().strip(",.;:!?")
            if not kept and bare in ("the", "a", "an"):
                kept.append(word)        # "the lake district", "the isle of wight"
                continue
            if not kept and (bare in NOT_A_PLACE or bare in MONTHS or bare in DAYS
                             or bare in SEASON or bare in STOP_AFTER):
                # "im going to be late" and "off to get the kids" name a verb, not a place: the
                # first word has to be a place or there is no trip here.
                break
            if kept and (bare in MONTHS or bare in DAYS or bare in SEASON or bare in STOP_AFTER
                         or bare in ("with", "and", "for", "next", "this")):
                break
            kept.append(word)
        place = " ".join(kept).strip(" ,.;:!?")
        low = place.lower()
        head = [word for word in low.split() if word not in ("the", "a", "an")]
        if head and (head[0] in TIME_WORD or DURATION.match(low)):
            # "in a minute", "in the morning", "there in ten minutes": the words say when.
            continue
        if NOT_A_TRIP.match(low):
            continue
        # "going to start a small business" is a doing and "going back to uni next year" is not
        # a trip: the words after "to" are not always a place, and both were answered with the
        # trip reader asking when it was.
        if not_a_trip.not_a_destination(words, place):
            continue
        if not place or low in NOT_A_PLACE or low in MONTHS or low in DAYS or SEASON & set(low.split()):
            continue
        if A_CARING_PLACE_HEAD.match(low):
            # A bed in a ward is where the person they are going to see is, not somewhere to go
            # for a nice time: the reply for it is the one about the place being worrying, not
            # "A Care Home, lovely. When is it?".
            continue
        # "im going to visit her in the home tomorrow" is a visit to a care home, and the store
        # named it "The Home" and asked what the person hoped to do while they were there. A
        # bare "home" is already in NOT_A_PLACE, and the article was all that let this one
        # through, so the same refusal is made against the place without it.
        bare_place = re.sub(r"^(?:the|a|an)\s+", "", low)
        if bare_place in NOT_A_PLACE or bare_place in MONTHS or bare_place in DAYS:
            continue
        # The person themselves is not the destination: "going to my mums" is a visit, not a
        # trip to a place called Mum, and a visit is what the visit reading answers.
        if not a_visit and _a_relation_not_a_place(low):
            continue
            continue
        if low in ("the", "a", "an") or len(low) < 3:
            continue
        if re.search(r"\bbook", line, re.I) and (_the_thing_booked(low)
                                                     or _a_thing_booked_for_when(low)):
            # "we booked a table for friday" books a table, not a trip: what people book is
            # often a thing rather than somewhere to go, and it is not a place to name.
            continue
        return place
    return ""


# What somebody books when the booking is not a journey: a table, tickets, a taxi, a haircut.
# A place named after "in" ("we booked a cottage in cornwall") is the trip and is kept.
BOOKED_THING = frozenset("""table tables ticket tickets seat seats row taxi cab minicab
haircut appointment appointments slot court pitch room rooms booth class classes lesson
lessons dinner lunch breakfast delivery takeaway table tennis
physio physiotherapist dentist dental doctor doctors gp optician hygienist chiropractor
osteopath vet vets clinic scan xray x-ray bloods surgery consultation checkup
mot service servicing boiler plumber electrician garage engineer gas""".split())


def _the_thing_booked(low):
    """Whether the words name the thing that was booked rather than somewhere to go."""
    words = [w for w in low.split() if w not in ("a", "an", "the", "my", "our", "his", "her")]
    return bool(words) and words[0] in BOOKED_THING


# What a person books to stay in, when the only words behind it say when: "we booked the caravan in
# august" is a booking with a date on it, not a trip to a place called Caravan. Kept apart from
# BOOKED_THING because it is only a thing when a date follows it - "we booked a cottage in cornwall"
# is the same word and is a trip, and the place there is read after the "in".
STAY_THING = frozenset("""caravan cottage villa apartment flat hotel lodge cabin tent campervan
camper motorhome house boat ferry crossing tunnel shuttle flight flights cruise
apartment""".split())


def _a_thing_booked_for_when(low):
    """Whether the words name the thing booked, where a date and not a place follows it."""
    words = [w for w in low.split() if w not in ("a", "an", "the", "my", "our", "his", "her")]
    return bool(words) and words[0] in STAY_THING


STOP_AFTER = frozenset("""on in at for from with and next this that the a an to by until
till near around over through tomorrow tonight today later soon
again anyway then first""".split())


def _month(line):
    for word in WORD.findall(_low(line)):
        if word in MONTHS:
            return word
    return ""


# A date given without a month's name: "next month", "at christmas", "half term", "this summer".
# The trip has a when, so the reply must not ask for one.
A_WHEN_PHRASE = re.compile(
    r"\b(?:next|this|at|over|for|in the|after)\s+(?:month|week|weekend|summer|winter|spring|"
    r"autumn|christmas|xmas|easter|half term|new year|bank holiday)\b"
    r"|\b(?:tomorrow|tonight|the day after tomorrow|this afternoon|this morning)\b", re.I)


# A weekday said on its own, with no "on" or "next" in front of it: "we are going to a brthday
# party saturday". People drop the preposition when they talk, and the day is the same day.
BARE_DAY = re.compile(r"\b(" + "|".join(sorted(DAYS - {"weekend"}, key=len, reverse=True)) + r")\b",
                      re.I)


def _when_phrase(line):
    """The date the line gives without naming a month ("next month"), or ""."""
    said = str(line or "")
    found = A_WHEN_PHRASE.search(said)
    if found:
        return " ".join(found.group(0).lower().split())
    day = BARE_DAY.search(said)
    return day.group(1).lower() if day else ""


# Who is going, counted and said without "with": "two kids" is the same detail as "with two
# kids", and it was reaching the pool about a change that unsettles sleep.
# The first group is not the whole group. "two adults and our 6 year old" was read as two adults,
# so a trip the chat had already been told about was said back "Wales in August with two adults."
# - the six year old gone from the reply and from the note about who is going. A second group
# joined by "and" or "plus" is the same answer, so it is kept with the first.
_GROUP = (r"(?:kids?|children|child|adults?|grown-?ups?|teenagers?|bab(?:y|ies)|toddlers?|"
          r"boys?|girls?|year\s+olds?|pensioners?|grandparents?|parents?)")
_COUNT = r"(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)"
BARE_WHO = re.compile(r"^\s*(?:and\s+|oh\s+|also\s+|plus\s+)?"
                      r"((?:" + _COUNT + r"\s+" + _GROUP + r"|\d+\s+year\s+olds?)"
                      r"(?:\s+(?:and|plus)\s+(?:an?\s+|our\s+|my\s+|their\s+|the\s+)?"
                      r"(?:" + _COUNT + r"\s+)?" + _GROUP + r")*)\b", re.I)


def _who(line):
    found = WITH_WHO.search(line)
    if found:
        return found.group(1).strip(" ,.;:!?")
    bare = BARE_WHO.match(line)
    return bare.group(1).strip(" ,.;:!?") if bare else ""


def _how_long(line):
    found = FOR_HOW_LONG.search(line)
    if found:
        return found.group(1).strip(" ,.;:!?")
    bare = JUST_HOW_LONG.match(line.strip(" .,;:!?"))
    if bare:
        return (bare.group(1) or bare.group(2)).strip()
    return ""


def _how_getting_there(line):
    found = BY.search(line)
    return found.group(1).lower() if found else ""


def _by_the_sea(place):
    """Whether a week there is a week of beach days: a coast, or a place famous for one.

    A place nobody named on the list is given the general week note, which says nothing about
    beaches or hills, so a guess about Scotland cannot promise sand.
    """
    words = set(_low(place).replace("-", " ").split())
    return bool(words & (SEA_PLACES | {"beach", "beaches", "coast", "seaside", "sea", "shore"}))


def _a_carded_place(place):
    """Whether the knowledge base has a card of its own for this place.

    A card is the better answer to the trip itself - "In Rome: the Colosseum with a timed ticket,
    the Pantheon..." names what to see, where a note about the month does not - so the trip reader
    stands back for those places and lets the card answer. It walks in again on the next turn,
    for the detail the card does not cover (how long, the drive, what to pack), because the store
    keeps the plan. bot/knowledge/travel.py draws the line: the cities it has a card for, and the
    countries it has one for, are the places a "going to X" line is already answered about.
    """
    try:
        from ..knowledge import travel
    except Exception:  # noqa: BLE001 - no knowledge base to defer to
        return False
    key = _low(place).strip()
    if key.startswith("the "):
        key = key[4:]
    for name in ("CITIES", "BEST_TIME"):
        table = getattr(travel, name, None) or {}
        if key in {str(other).lower() for other in table}:
            return True
    return False


def a_moved_destination(line, memory):
    """The trip the conversation is on, with its place put right, or None.

    "we moved it to florence" is not a trip of its own: it is the trip already in the chat, moved.
    The month, who and how long come from that trip, so the reply says Florence in June rather
    than asking when it is, and the store keeps the new place (`facts` moves the plan). With no
    trip in the chat the place is all there is, and the reply asks the one thing a friend would.
    """
    if not isinstance(memory, dict) or not line or "?" in line:
        return None
    place = facts.a_moved_place(line)
    if not place:
        return None
    if _the_last_line_named_an_animal(memory):
        # "my dog is called rex" then "i changed it to max" is the dog renamed. The words are the
        # ones that move a holiday, so the animal the chat is about is what tells them apart.
        return None
    live = _the_trip_so_far(memory)
    if not live:
        # A trip rebooked before it was ever said as a trip ("we booked porto" is a plan, not a
        # trip): the place is the one thing the line gives, and the reply says it back rather
        # than reading the line as a job finished.
        return {"place": place, "month": "", "when": "", "who": "", "how_long": "", "by": ""}
    if _low(_cap(live.get("place") or "")) == _low(place):
        return None                  # already the place they said, so nothing has moved
    _keep_the_new_place(memory, place, live.get("place") or "", line)
    return dict(live, place=place)


def _the_last_line_named_an_animal(memory):
    """True when the line before this one gave an animal a name or asked about one.

    Read through `facts.extract`, so every shape of naming an animal counts ("my dog is called
    rex", "we're getting a puppy called Biscuit") and a line about anything else does not.
    """
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    said = ""
    for turn in reversed(turns):
        words = turn.get("user")
        if isinstance(words, str) and words.strip():
            said = words
            break
    if not said:
        return False
    found = facts.extract(said)
    return bool(found.get("pets") or found.get("pets_gone"))


def _keep_the_new_place(memory, place, old="", said=""):
    """The store keeps the place the trip is going to now, in place of the one it left.

    The trip is already in the chat, so the plan is the same plan with a new destination: "we are
    going to cornwall in august" then "no we changed it to devon" is a week in Devon, and the next
    line that names nothing ("what should we do there") has to be read against Devon.

    Only the trip's own entries move. Everything else the chat has been told stays where it was -
    "my sister is coming in june" is not a holiday, and the store still has to be able to say
    "you are going to Devon in August, and your sister is coming in June".
    """
    known = user(memory)
    old_place = str(old or "").strip()
    known["places"] = _the_place_put_right(known.get("places"), old_place, place)
    known["plans"] = _the_place_put_right(known.get("plans"), old_place, place)
    # The plan is the entry that names the new destination, so the month it was said with travels
    # with it: "you are going to Devon in August", not a bare "Devon" beside it.
    known["plan"] = next((entry for entry in known["plans"] if _low(place) in _low(entry)), place)
    log = memory.get("facts_log")
    if not isinstance(log, list):
        log = memory["facts_log"] = []
    log.append({"key": "places", "value": place, "turn": len(memory.get("turns") or []),
                "text": said})
    log.append({"key": "plan", "value": place, "turn": len(memory.get("turns") or []),
                "text": said})


def _the_place_put_right(entries, old, place):
    """The chat's own list with the destination put right, and every other entry left alone.

    The old place is replaced inside the entry that names it, so "Cornwall in august" becomes
    "Devon in august" and keeps its month and its place in the list. Entries that name nothing
    about the trip are copied as they are, and the new place is added only when no entry named the
    old one.
    """
    kept = []
    put_right = False
    for entry in (entries if isinstance(entries, list) else []):
        text = str(entry or "").strip()
        if not text:
            continue
        if old and _low(old) in _low(text):
            text = re.sub(re.escape(old), lambda _m: place, text, count=1, flags=re.I)
            put_right = True
        if text not in kept:
            kept.append(text)
    if not put_right and place not in kept:
        kept.append(place)
    return kept


def a_trip(text, memory, cards=True):
    """The trip this line states, as {place, month, who, how_long, by}, or None.

    A trip is a going to a place that is not one of the everyday ones, in a line that is not a
    question and not a trip already taken. Everything the line does not say is "".
    """
    line = str(text or "").strip()
    if not line or line.endswith("?"):
        return None
    kind = ack.reads_as_a_trip(line)
    if kind and kind != "trip":
        # A wedding, a gig, a funeral: an occasion is read and answered by bot/memory/ack.py,
        # and it knows the difference between a day to look forward to and one they are dreading.
        return None
    low = _low(line)
    if EVERYDAY_TRIP.search(low) or ON_A.search(low):
        return None
    if re.search(r"\bwent\b|\bhave been\b|\bwas in\b|\blast year\b", low):
        return None                     # a trip taken, not one coming up
    if re.search(r"\b(?:when|where|how|what|why|should|shall|can|could|would|will|worth)\b", low) \
            and not re.search(r"\b(?:we're|were|we are|i'm|im|i am)\b", low):
        return None                     # a question about a trip, not a statement of one
    visit = _a_person_visited(line)
    if visit:
        return {"place": visit, "month": _month(low), "when": _when_phrase(low),
                "who": _who(low), "how_long": _how_long(low), "by": "", "visit": True,
                "meal": bool(A_MEAL.search(low)), "baby": bool(A_NEW_BABY.search(low))}
    if not (GOING.search(low) or GOING_BARE.search(low)):
        return None
    place = _places(line)
    if not place:
        return None
    if cards and _a_carded_place(place) and not (BOOKED_DONE.search(low)
                                                and (_month(low) or _when_phrase(low))):
        # "were off to rome next week": this line said out loud but the card says more, so the
        # card answers it, whatever the shape of the going (going, off to, heading, flying).
        # A booking with a date on it is not that line. The card answers "what is there to do",
        # and the guide stands back on the word "booked" itself (a booking ask is not a
        # "what is there to do" ask), so the stand-back left a dated booking to the greeting pool:
        #   we booked flights to lisbon in may   ->  "Nice one."
        #   i booked a holiday to spain in june  ->  "Good - that's one off the list."
        # The store is the reader that has the news and the date, so it keeps a dated booking. A
        # booking with no date stays where it was: the card asks when it is, which is the useful
        # question about it, and "i booked a holiday to spain" keeps that reply.
        return None
    if facts.extract(line).get("name"):
        # "im jess, we are going to spain next week" is two things at once, and the name is the
        # one the conversation needs first: the welcome is the reply, and the trip is answered on
        # the next turn (the store keeps it, so the trip reader still finds it).
        return None
    return {"place": place, "month": _month(low), "when": _when_phrase(low),
            "who": _who(low), "how_long": _how_long(low), "by": _how_getting_there(low)}


def the_trip_they_booked(text):
    """The (place, when) a line says it has booked, or ("", "").

    "we booked a cottage in cornwall for august" is a trip to Cornwall in August, and the store
    reads only the shape a trip is said in ("im going to cornwall in august"), so it kept nothing
    and "where are we going" answered "You haven't said - where are you going?". A booking is the
    same trip said as a thing already done.
    """
    said = str(text or "")
    if not BOOKED.search(said):
        return "", ""
    place = _places(said)
    if not place:
        return "", ""
    return place, _month(said) or _when_phrase(said)


def _the_trip_so_far(memory):
    """The trip the conversation is on, from the plan the store keeps, or None.

    The plan is kept as the phrase the person said it in ("Cornwall in August"), so the parts are
    read from the line it came from - a plan can be a trip without the phrase saying so.
    """
    facts = user(memory)
    plans = [p for p in (facts.get("plans") or []) if isinstance(p, str) and p.strip()]
    latest = facts.get("plan")
    if isinstance(latest, str) and latest.strip():
        plans.append(latest)
    for plan in reversed(plans[-3:]):
        said = plan_line(memory, plan) or plan
        trip = a_trip(said, memory, cards=False)
        if trip:
            trip["plan"] = plan
            return trip
    # The store does not file every line as a plan ("were going to cornwall in august" is a
    # sentence it reads for the place, not for a plan), so the last few lines they typed are
    # read the same way. A trip said three turns ago is still the trip this detail belongs to.
    for turn in reversed((memory.get("turns") or [])[-4:]):
        if not isinstance(turn, dict):
            continue
        trip = a_trip(turn.get("user") or "", memory, cards=False)
        if trip:
            trip["plan"] = ""
            return trip
    return None


def _asked_last(memory):
    """Whether the bot's last reply ended on a question, so this one must not ask another."""
    return str(last_bot(memory) or "").strip().endswith("?")


def _told(text, memory):
    """The replies already given this conversation, so the same line is not said twice."""
    turns = memory.get("turns") or []
    return {_low(t.get("bot")) for t in turns if isinstance(t, dict)}


def _pick(options, memory, text):
    """One of options, never one the bot has just said. Same line and same turn, same pick."""
    said = _told(text, memory)
    said_inside = " ".join(said)
    turns = memory.get("turns") or []
    fresh = [o for o in options
             if _low(o) not in said and not (len(o) > 15 and _low(o) in said_inside)]
    fresh = fresh or list(options)
    # What was said before this line is part of the pick, so the same trip in two different
    # conversations is not worded the same way twice.
    seed = 0
    for turn in turns[-4:]:
        if isinstance(turn, dict):
            seed = seed * 31 + sum(ord(c) for c in str(turn.get("user") or ""))
    seed = seed * 7919 + sum(ord(c) for c in str(text or "")) + len(turns)
    return fresh[seed % len(fresh)]


def _join(parts):
    """Sentences joined as sentences: each one opens with a capital."""
    out = []
    for part in parts:
        part = str(part or "").strip()
        if part:
            out.append(part[:1].upper() + part[1:])
    return " ".join(out)


# The little words inside a place name stay small: "the isle of wight" is not "The Isle Of Wight".
SMALL = frozenset("of the and on in de du van der le la".split())


def _with_them(named, who, memory, line):
    """Somebody coming along who is not a child: the trip said with them, and the useful ask."""
    ask = _pick(ASK_WHAT, memory, line)
    return "{0} with {1}. {2}".format(_mid(named), _yours(who).lower(),
                                      ask[:1].upper() + ask[1:])


def _yours(who):
    """The people the person is going with, said back as theirs: "with my mum" -> "with your mum".

    The bot is not the one going, so the person's own word for their family and friends is the
    one word that has to turn round. A name is left exactly as they said it.
    """
    words = []
    for word in str(who or "").split():
        low = word.lower()
        if low in ("my", "our", "ours"):
            words.append("your" if low != "ours" else "yours")
        elif low == "mine":
            words.append("yours")
        else:
            words.append(word)
    return " ".join(words)


def _mid(named):
    """A place as it reads inside a sentence: "The Isle of Wight" -> "the Isle of Wight"."""
    named = str(named or "")
    return "the " + named[4:] if named.startswith("The ") else named


def _cap(text):
    """The place as it is written: "cornwall" -> "Cornwall", "the isle of wight" -> "The Isle of
    Wight"."""
    text = str(text or "").strip()
    if not text:
        return text
    words = []
    for position, word in enumerate(text.split()):
        if position and word.lower() in SMALL:
            words.append(word.lower())
        elif word[:1].isalpha():
            words.append(word[:1].upper() + word[1:])
        else:
            words.append(word)
    return " ".join(words)


def _seasons_we_know(place):
    """The knowledge base's own note on when to go there, or "".

    Its travel data carries the seasons of the cities and countries people ask about, month by
    month. Cornwall and Devon are not in it and keep the general season below; Thailand and Dubai
    are, and there the general note is the wrong way round - January is their high season, not
    their quiet one - so a place it knows is never given a guess about the weather or the prices.
    """
    try:
        from ..knowledge import travel
    except Exception:
        return ""
    key = _low(place or "").strip()
    if key.startswith("the "):
        key = key[4:]
    if not key:
        return ""
    note = travel.CITY_BEST_TIME.get(key)
    if note:
        return note
    country = travel.CITY_COUNTRY.get(key, key)
    return travel.BEST_TIME.get(country) or travel.BEST_TIME.get(key) or ""


def _their_month(note, month):
    """The sentence of that note which names their month, or ""."""
    for sentence in re.split(r"(?<=[.!?])\s+", note):
        if re.search(r"\b" + month + r"\b", sentence.lower()):
            said = _mid(sentence.strip())
            return said[:1].upper() + said[1:]
    return ""


def _in_its_season(place, month):
    """Whether the knowledge base's own month picks name this place as a place to go then.

    It is the same data that answers "where should I go in January", read the other way round: a
    month that names the place is a month worth going there, so "lanzarote in january" is not
    told it is out of season.
    """
    try:
        from ..knowledge import travel
    except Exception:
        return False
    picks = getattr(travel, "_MONTH_PICKS", None) or {}
    row = _low(picks.get(month) or "")
    if not row:
        return False
    key = _low(place or "").strip()
    if key.startswith("the "):
        key = key[4:]
    if len(key) < 4:
        return False
    return bool(re.search(r"\b" + re.escape(key) + r"\b", row))


def _a_winter_place(place):
    """Whether this is somewhere the winter is the season, not the off-season."""
    key = _low(place or "").strip()
    if key.startswith("the "):
        key = key[4:]
    return any(re.search(r"\b" + re.escape(word) + r"\b", key) for word in WINTER_SUN)


def _when_note(month, memory, text, booked=False, place=""):
    """The one useful sentence a friend adds about a trip in that month: the season itself."""
    known = _seasons_we_know(place)
    if known:
        return _their_month(known, month)
    if month in QUIET and (_a_winter_place(place) or _in_its_season(place, month)):
        return _pick([n.format(month=_cap(month)) for n in SEASON_NOTES], memory, text)
    if month in PEAK:
        notes = PEAK_BOOKED_NOTES if booked else PEAK_NOTES
    elif month in BUSY:
        notes = BUSY_NOTES
    elif month in QUIET:
        notes = QUIET_NOTES
    else:
        return ""
    return _pick([n.format(month=_cap(month)) for n in notes], memory, text)


def _the_visit_length(how_long, memory, text):
    """The sentence a visit gets for how long it lasts, or "" when the line gave no length."""
    if not how_long:
        return ""
    low = _low(how_long)
    if "weekend" in low:
        return _pick(VISIT_A_WEEKEND, memory, text)
    if re.search(r"night|\bday", low):
        return _pick(VISIT_A_FEW_DAYS, memory, text)
    if re.search(r"week|fortnight|month", low):
        return _pick(VISIT_A_WEEK, memory, text)
    return ""


def _who_note(who, how_long, memory, text, place=None):
    """The sentence about who is going and for how long, if the line said either."""
    notes = []
    if who and re.search(r"\bkids?\b|\bchild|\bchildren\b|\bbaby\b|\btoddler", who):
        if re.search(r"\b(?:two|three|four|five|six|\d+)\b", who):
            # The number they gave is the number said back: "with two kids" is two, not a crowd.
            notes.extend(n.format(who=who) for n in KIDS_NUMBERED)
        else:
            notes.extend(KIDS_NOTES)
    if how_long and "weekend" in how_long:
        notes.extend(WEEKEND_NOTES)
    elif how_long and re.search(r"night|\bday", how_long):
        notes.extend(DAY_NOTES)
    elif how_long and re.search(r"week|fortnight|month", how_long):
        if re.search(r"two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fortnight|\d",
                     how_long):
            notes.extend(LONG_NOTES)
        else:
            if place is None or _by_the_sea(place):
                notes.extend(WEEK_NOTES)
            else:
                notes.extend(WEEK_NOTES_LAND)
    if not notes:
        return ""
    return _pick(notes, memory, text)


def _a_note(month, who, how_long, memory, text, booked=False, place=""):
    """Both notes, when the month and the people are both worth a sentence."""
    parts = [n for n in (_when_note(month, memory, text, booked, place),
                         _who_note(who, how_long, memory, text, place)) if n]
    return _join(parts)


# A follow-up that asks for a place to eat or a bed for the night, with the kind of place left
# out: "and somewhere to eat" after "im going to see my mum saturday", "somewhere to stay" after
# "im visiting my sister in leeds". Understanding reads these as statements, so the only module
# that would speak said them back ("Got it - somewhere to eat."), which is the one reply that
# helps nobody: the person asked for a recommendation. Read here as the detail of a trip they
# are, because that is what they are - and only when the knowledge base has nothing better, so a
# city it does know keeps its own answer ("and somewhere to eat" after "were going to rome in
# may" is still the Rome food card). A line that says a place was found ("we found somewhere to
# eat") or that one is already sorted ("my sister has somewhere to stay") is the person telling
# the chat something, not asking, so it is anchored at the start of the line.
SOMEWHERE_TO_EAT = re.compile(
    r"^\s*(?:(?:and|also|plus|then|oh|ok|okay)\s+)?(?:somewhere|a place|anywhere)\s+"
    r"(?:good\s+|nice\s+|decent\s+)?to\s+(?:eat|have lunch|have dinner|get food|get something "
    r"to eat|grab a bite)\b", re.I)
SOMEWHERE_TO_STAY = re.compile(
    r"^\s*(?:(?:and|also|plus|then|oh|ok|okay)\s+)?(?:somewhere|a place|anywhere)\s+"
    r"(?:good\s+|nice\s+|cheap\s+)?to\s+(?:stay|sleep|stop over|kip)\b"
    r"|^\s*(?:(?:and|also|plus|then)\s+)?(?:a|any)\s+(?:good\s+|decent\s+|cheap\s+)?"
    r"(?:hotel|b&b|guesthouse|bed for the night)\b", re.I)
# The towns the knowledge base has a card for, so a need aimed at one of them keeps that answer.
# Read lazily: the store needs no facts of its own.
def _a_known_city(place):
    """Whether the knowledge base has a card for this place, so its own answer keeps the turn."""
    place = _low(place).strip(" .,;:!?")
    if not place:
        return False
    try:
        from ..knowledge.travel import CITIES  # noqa: PLC0415 - only when a place is on the table
    except Exception:  # noqa: BLE001 - a knowledge base that cannot be read has no cities
        return False
    return place in CITIES or place.split()[0] in CITIES

# What a friend says when they do not know the town well enough to name a place, and when they do
# not know the town at all. Both are advice the person can act on, which the echo was not, and the
# second asks the one thing that would make the answer specific - unless the bot just asked.
# What a friend says when they cannot name a place: the rule for picking one, which is worth more
# than a guess, and the one thing that would make the answer specific. A town the knowledge base
# has a card for never gets here, so no good answer is taken away.
EAT_WITHOUT_A_CARD = (
    "I cannot name a place in {place} without guessing, so narrow it yourself: set a budget a "
    "head and how far you will walk, then pick the shortest menu - a short one usually means the "
    "kitchen is cooking it fresh.",
    "{place} is not a town I can name places in, so go by the street: the shortest menu, and the "
    "place with people in it at six rather than the one with photos of the food outside.",
)
STAY_WITHOUT_A_CARD = (
    "I cannot name a hotel in {place} without guessing, so go by the area rather than the stars: "
    "near the station if it is one night, near where you will spend the evening if it is two, and "
    "reviews from this year rather than the rating.",
    "{place} is not a town I can name hotels in. Pick the area first - the station for one night, "
    "wherever you are eating for two - then check the recent reviews for noise.",
)
EAT_WITHOUT_A_TOWN = (
    "Where are you off to? With a town I can point you at an end of it. Without one: set a budget "
    "a head and how far you will walk, then pick the shortest menu - a short one usually means "
    "the kitchen is cooking it fresh.",
    "Tell me the town and I will narrow it down. Failing that: a short menu, and the place that "
    "is busy at six rather than the one with photos of the food outside.",
)
# The same advice with no question in it, for the turn where the bot's own question is still on
# the table: a second question in a row is the bot interviewing itself, and the advice stands on
# its own.
EAT_ADVICE = (
    "Set a budget per head and how far you will walk, then pick the shortest menu - a short one "
    "usually means the kitchen is cooking it fresh, and the place with people in it at six beats "
    "the one with photos of the food outside.",
)
STAY_ADVICE = (
    "Go by the area rather than the stars: near the station if it is one night, near where you "
    "will spend the evening if it is two, and read reviews from this year rather than the rating.",
)
STAY_WITHOUT_A_TOWN = (
    "Where will you be? With a town I can say which area to look in. Without one: near the "
    "station if it is one night, near where you will eat if it is two, and reviews from this year "
    "rather than the star rating.",
    "Tell me where and I will point at an end of it. Failing that: go by the area rather than the "
    "hotel - the station for one night, the evening's end of town for two.",
)


def _the_areas_of(place):
    """The parts of the town the knowledge base says to stay in, or "" when it says none."""
    try:
        from ..knowledge.travel import CITY_AREA  # noqa: PLC0415 - only for a town on the table
    except Exception:  # noqa: BLE001 - a knowledge base that cannot be read knows no areas
        return ""
    return str(CITY_AREA.get(_low(place).strip(" .,;:!?")) or "")


def _somewhere_for(line, memory):
    """The reply to "and somewhere to eat" / "somewhere to stay", or None for anything else.

    Only the two needs the chat can answer: a place to eat and a place for the night. A town the
    knowledge base has a card for is left to it, so this never takes a good answer away.
    """
    eat = bool(SOMEWHERE_TO_EAT.search(line))
    stay = bool(SOMEWHERE_TO_STAY.search(line))
    if not (eat or stay):
        return None
    trip = _the_trip_so_far(memory) or {}
    place = _cap(_as_a_visit(str(trip.get("place") or "")))
    if not place:
        # A visit is not a trip the store files ("im visiting my sister in leeds"), but the place
        # is in the line: understanding leaves it in ref.there for the follow-up to use.
        understood = memory.get("understood")
        ref = understood.get("ref") if isinstance(understood, dict) else None
        if isinstance(ref, dict) and ref.get("there"):
            place = _cap(str(ref["there"]))
    if not place:
        for found in reversed([p for p in (user(memory).get("places") or []) if p]):
            place = _cap(str(found))
            break
    if not place:
        for turn in reversed([t for t in (memory.get("turns") or []) if isinstance(t, dict)]):
            said = _places(str(turn.get("user") or ""))
            if said:
                place = _cap(said)
                break
    # A town the knowledge base has a card for keeps the turn, because a card for a town says where
    # to eat in it and which part of it to stay in. A bed for the night is read here only where no
    # card says where to stay at all - "im going to york" / "somewhere to stay" was a receipt -
    # because "Stay in Monti for the Colosseum on foot..." is a better answer than any rule, and
    # the rule that answered over the top of it took a good answer away.
    if place and _a_known_city(place) and (eat or _the_areas_of(place)):
        return None
    if place:
        pool = EAT_WITHOUT_A_CARD if eat else STAY_WITHOUT_A_CARD
        return _pick([line.format(place=_mid(place)) for line in pool], memory, line)
    if _asked_last(memory):
        return _pick(list(EAT_ADVICE if eat else STAY_ADVICE), memory, line)
    return _pick(list(EAT_WITHOUT_A_TOWN if eat else STAY_WITHOUT_A_TOWN), memory, line)


# A bag for a baby is a question about a baby, and the words "what should i pack" can reach it
# from nowhere near one: "we're going to the Lakes in October" then "what should we pack" was
# answered "Pack for two changes plus one for luck: four or five nappies, wipes or two damp
# flannels in a bag". The trip is the subject of the chat and nothing in it says a baby is
# coming, so the packing question is the trip's, and this module knows the place and the month.
# The words a trip is said in when no place is named yet: "a weekend away", "a few days off".
WEEKEND_AWAY = re.compile(
    r"\b(?:weekend away|weekend break|long weekend|mini ?break|short break|few days away|"
    r"going away|get away|"
    r"(?:away|off) for (?:a|two|three|four|five|\d+) (?:week|weeks|fortnight|days?|months?)|"
    r"for (?:a fortnight|two weeks))\b", re.I)
A_BABY = re.compile(
    r"\b(?:bab(?:y|ies)|newborns?|toddlers?|infants?|napp(?:y|ies)|prams?|pushchair|"
    r"changing bag|baby bag|nurser(?:y|ies)|breastfeed\w*|formula|due date|expecting|"
    r"pregnan\w*)\b")


def _the_kind_of_trip(how_long):
    """The trip said as a kind rather than a place: "a weekend away", "a week away"."""
    said = _low(how_long)
    if "weekend" in said:
        return "a weekend away"
    if "fortnight" in said:
        return "a fortnight away"
    if re.search(r"\bweek", said):
        return "a week away"
    if re.search(r"\bmonth", said):
        return "a month away"
    if re.search(r"\bday", said):
        return "a few days away"
    return "a weekend away"


def _the_warm_week_is_out_of_season(month):
    """True for the month the knowledge base's warm-week list gets wrong for a cold place."""
    return _low(month or "").strip() in OUT_OF_SEASON


def _an_event_not_a_place(place):
    """True when the "place" the trip reading found is a thing they are going to, not a town."""
    bare = _low(place or "").strip()
    for word in ("a ", "an ", "the ", "my ", "our "):
        if bare.startswith(word):
            bare = bare[len(word):]
            break
    return bare in AN_EVENT_NOT_A_PLACE


def a_packing_question_about_the_trip(text, memory):
    """The trip a packing question belongs to, or None.

    Read by `answers` before it takes the line, so a bag written down for a baby does not answer
    a question about a weekend away. The line itself has to be a packing question, the chat has
    to be on a trip, and nothing in the recent lines may mention a baby: when one does, the
    question is about that baby and every module is free to answer it.

    The reading and the reply have to agree about which packing questions are the trip's, or the
    answer module stands down for a line nothing else will take: `what should i pack for the
    flight` after a trip to Rome lost the boarding-pass answer to a search hedge, because this
    reading said "the trip" and `_a_detail` then refused the tail. The tail is read here with the
    same test, so a question about something else to pack for keeps its own card.
    """
    if not isinstance(memory, dict):
        return None
    line = _low(text)
    found = PACKING.search(line) if line else None
    if not found or A_BABY.search(line):
        return None
    for turn in (memory.get("turns") or [])[-6:]:
        if isinstance(turn, dict) and A_BABY.search(_low(turn.get("user"))):
            return None
    live = _the_trip_so_far(memory)
    if not live:
        for turn in reversed([t for t in (memory.get("turns") or [])[-4:]
                              if isinstance(t, dict)]):
            said = _low(turn.get("user"))
            if WEEKEND_AWAY.search(said) and not said.strip().endswith("?"):
                # No place named yet, so the trip is the kind of trip and its month: enough to
                # pack for, which is more than a bag for a baby.
                live = {"place": "", "month": _month(said), "when": "", "who": _who(said),
                        "how_long": _how_long(said) or "a weekend", "by": "", "plan": ""}
                break
    if not live:
        return None
    tail = found.group(1).strip(" ?.!,")
    place = _low(live.get("place"))
    if _an_event_not_a_place(place):
        # The thing they are going to has its own card, and it is not a place to pack for.
        return None
    if tail and not (PACKING_FOR.match(tail) or (place and tail == "for " + place)):
        # Something else to pack for - the flight, a picnic, a walk - which has a card of its
        # own. Not this module, and not a reason for the answer module to stand down.
        return None
    return live


def the_bag_beats_the_list(text, memory):
    """True when the bag for the place and the month is the better answer than the list.

    The knowledge base's packing lists are written for a month, so they are the better answer
    most of the year; in October the warm-week list answers a cold place with cotton tops, shorts
    and swimwear, and there the bag the store keeps wins. The answer module stands down for the
    line on this reading and nothing else, so every other month keeps the answer it had.
    """
    live = a_packing_question_about_the_trip(text, memory)
    return bool(live) and _the_warm_week_is_out_of_season(live.get("month"))


def reply_for(text, memory, cards=True):
    """The reply to a trip said out loud, or a detail added to one, or None.

    Only two shapes: the line that states a trip, and the short line that adds a detail to a trip
    the conversation is already on. Everything else is another module's.
    """
    if not isinstance(memory, dict):
        return None
    line = " ".join(str(text or "").split())
    if not line:
        return None
    moved = a_moved_destination(line, memory)
    if moved:
        # A destination put right is the trip already on the table with its place changed: "im
        # going to rome in june" / "we moved it to florence" is Florence in June. Without this
        # the line reached the pool that answers a job finished ("Good to hear. What was the best
        # bit?"), because a plan said again is not a thing done.
        return _start(_a_new_trip(line, moved, memory))
    trip = a_trip(line, memory, cards=cards)
    if trip:
        return _start(_a_new_trip(line, trip, memory))
    if A_STAY_LENGTH.search(line):
        live = _the_trip_so_far(memory)
        if live and live.get("visit"):
            return _start(_pick(VISIT_HOW_LONG, memory, line))
    somewhere = _somewhere_for(line, memory)
    if somewhere:
        # "and somewhere to eat" is a request, not a remark: read before the detail branch, which
        # would otherwise leave it to the module that says it back.
        return _start(somewhere)
    # A question about the journey or the packing is still a detail of the trip the chat is on,
    # so it keeps this module even with a question mark on the end.
    about_the_trip = (PACKING.search(line) or PACKING_SAID.match(line) or THE_DRIVE.search(line)
                      or THE_FLIGHT.search(line) or THE_JOURNEY_ASK.search(line))
    # A journey asked as a question ("how long will it take to drive") is about the trip the chat
    # is on, so it takes the detail branch with the question mark still on it. The ask names its
    # own mode, so the line is not a bare "how long" and no other module has a better claim.
    if (JUST_A_DETAIL.match(line) or _only_a_length(line) or PACKING_SAID.match(line)
            or THE_JOURNEY_ASK.search(line)) \
            and (not line.endswith("?") or about_the_trip):
        live = _the_trip_so_far(memory) or a_packing_question_about_the_trip(line, memory)
        if live:
            detail = _a_detail(line, live, memory)
            if detail:
                return _start(detail)
    if THE_LENGTH_ASK.search(line) and not (THE_FLIGHT.search(line) or THE_DRIVE.search(line)
                                            or THE_JOURNEY_ASK.search(line)
                                            or THE_MODE.search(line)):
        live = _the_trip_so_far(memory)
        if live and not live.get("how_long") and not _a_length_said(memory):
            # The trip is on the table but its length is not, so the answer is the question the
            # chat has not answered yet - not a search hedge and not the month said back as a
            # countdown ("how many nights" answered "That's about 3 weeks away").
            return _start(_the_length_asked(live, memory, line))
    month = _the_month_answered(line, memory)
    if month:
        live = _the_trip_so_far(memory)
        if live:
            live = dict(live, month=month)
            return _start(_a_new_trip(line, live, memory))
    return None


# A bare month, given as the answer to the question this module asked ("Cornwall, lovely. When
# is it?" -> "in august"). Nothing else is on the line, so it can only be that answer.
JUST_A_MONTH = re.compile(
    r"^\s*(?:in\s+|next\s+|this\s+|maybe\s+|probably\s+|its\s+|it's\s+|er,?\s+)*"
    r"([a-z]+)\s*[.!]?\s*$", re.I)


def _only_a_length(line):
    """Whether the line is the length of the stay and nothing else: "for ten days", "two weeks".

    A length is how people answer "how long are you going for", so it is a detail of the trip the
    chat is on. The words are the only thing on the line, so nothing else is being said.
    """
    bare = _low(line).strip(" .,;:!?")
    # People say the length with the frame still on it: "its for two weeks", "thats ten days",
    # "we're there for a week". The lead-in is plumbing - the words after it are still only the
    # length - so the frame is taken off before the length is read, and the trip the chat is on
    # is what the length belongs to.
    bare = re.sub(r"^(?:its|it's|thats|that's|were|we're|we are|there|were there|"
                  r"its for|its about|we're there)\s+", "", bare).strip()
    return bool(FOR_HOW_LONG.fullmatch(bare) or JUST_HOW_LONG.match(bare))


def _the_month_answered(line, memory):
    """The month in a line that is only a month, when the bot's last line asked a trip's when."""
    asked = _low(last_bot(memory))
    if "when" not in asked:
        return ""
    found = JUST_A_MONTH.match(line)
    if not found:
        return ""
    word = found.group(1).lower()
    return word if word in MONTHS else ""


# The group words that are people in the plural rather than one person's place: "my parents"
# is "your parents'", not "your parent's", and "my kids" is "your kids'".
_PLURAL_PEOPLE = frozenset(("parents", "grandparents", "children", "kids", "family", "relatives",
                            "folks", "friends", "twins", "in laws", "in-laws", "inlaws"))


def _as_a_visit(place):
    """A relative or friend someone is visiting, said back as a place they belong to.

    "im going to my sisters for the weekend" is not a trip to a place called My Sisters. The
    person is named with a possessive, so the reply says it the way a friend would: "your
    sister's", "your parents'". A thing after the person stays after it: "my parents house" is
    "your parents' house", not "Your Parents House's". A word that is already a place stays as
    it was.
    """
    match = A_PERSON_IS_NOT_A_PLACE.match(place)
    if not match:
        return place
    person = match.group("person")
    low = person.lower()
    own = (match.group("poss") or "").replace("\u2019", "'")
    if own:
        owner = person + own
    elif low in _PLURAL_PEOPLE:
        owner = person + ("'" if low.endswith("s") else "'s")
    else:
        owner = person + "'s"
    rest = place[match.end():].strip(" .,;:!?")
    first = rest.split()[0].lower() if rest else ""
    if rest and first not in _NOT_A_THING_OF_THEIRS:
        return "your " + owner + " " + rest
    return "your " + owner


def _a_new_trip(line, trip, memory):
    visit = _as_a_visit(trip["place"])
    place, who = _cap(visit), trip["who"]
    month = trip["month"]
    outing = OUTING.match(_low(trip["place"]))
    if outing:
        # A day at the beach or the park is a day out, not a place with a name: said back as one,
        # with what actually helps about a day out rather than "When is it?".
        word = outing.group(1).lower()
        sea = word in SEA
        said = "A day {0} the {1}, {2}. ".format("in" if word in OPEN_AIR else "at", word,
                                                 _pick(WARM, memory, line))
        # The notes about the people are written for the beach ("the beach early"), so they only
        # come in where the day out is that one, and then they are the one thing added.
        who_note = ""
        if who and sea:
            who_note = _who_note(who, trip["how_long"], memory, line)
        if who_note:
            return said + _join([who_note])
        notes = SEA_NOTES if sea else INDOOR_NOTES if word in TICKETED else LAND_NOTES
        return said + _join([_pick(notes, memory, line)])
    # A day with no month behind it is said back the way they said it: "a brthday party
    # saturday" is a Saturday, and a reply that asks when it is has not listened.
    day = trip.get("when") or ""
    day = day if day in DAYS and day != "weekend" else ""
    named = place + (" in " + _cap(month) if month else (" on " + _cap(day) if day else ""))
    if who:
        named += " with " + _yours(who)
    booked = bool(re.search(r"\bbook", line, re.I))
    said = ("{0} is booked, then. ".format(named) if booked else
            "{0}, {1}. ".format(named, _pick(WARM, memory, line)))
    if visit != trip["place"]:
        # A visit is not a holiday: the month's season and "where are you staying" are not
        # things a friend asks about tea at their mum's. The length is still worth a sentence,
        # and when there is none the visit is the thing to ask about.
        note = _join([part for part in (_who_note(who, "", memory, line),
                                       _the_visit_length(trip["how_long"], memory, line)) if part])
        if note:
            return _join([said, note])
        ask = _pick(ASK_VISIT, memory, line)
        return _join([said, ask[:1].upper() + ask[1:]])
    note = _a_note(month, who, trip["how_long"], memory, line, booked, trip["place"])
    if note:
        return said + note
    if booked:
        return said + "Get the big days out booked now too, and you can take the rest as it comes."
    if not month and day:
        # The day is in the reply already ("A brthday party on Saturday, lovely."), so there is
        # nothing to ask about when it is and nothing to add for a thing we have no notes on.
        return said.strip()
    if not month and trip.get("when"):
        # A date without a month's name ("next month", "at christmas", "half term"): the trip
        # has a when, so asking "When is it?" would be deaf.
        return said + _pick(ASK_WHAT, memory, line)[:1].upper() + _pick(ASK_WHAT, memory, line)[1:]
    if not month:
        # Nothing to say about a date nobody gave, so the reply is the one question a friend
        # asks, with the place said once - unless the bot has just asked one.
        if _asked_last(memory):
            return _pick(ASK_WHEN_NO_QUESTION, memory, line).format(place=place)
        return _pick(ASK_WHEN, memory, line).format(place=place)
    return said + _pick(ASK_WHAT, memory, line)[:1].upper() + _pick(ASK_WHAT, memory, line)[1:]


def _a_length_said(memory):
    """The length the chat has already given for the trip, in their own words, or None.

    "we are going to spain in august" / "its for two weeks" / "how long are we there for": the
    length is on the table even though no slot holds it - nothing files a line that only says a
    length - and the ask is answered by the line they said it on ("You said two weeks."). Asking
    the question back there told the person the chat had not heard what they had just said, which
    is what the ask branch did before this guard.
    """
    for turn in reversed(memory.get("turns") or []):
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("user") or "")
        if not text or text.rstrip().endswith("?"):
            continue
        found = FOR_HOW_LONG.search(text)
        if found:
            return found.group(1)
    return None


def _the_length_asked(trip, memory, line):
    """The length of the stay asked while the chat has not said one: the question back."""
    place = _cap(_as_a_visit(trip.get("place") or ""))
    month = trip.get("month") or ""
    options = THE_LENGTH_NOT_SAID
    if place:
        named = _mid(place + (" in " + _cap(month) if month else ""))
        options = tuple(n.format(named=named) for n in THE_LENGTH_NOT_SAID_NAMED)
    return _join([_pick(options, memory, line), _pick(THE_NIGHTS_FIRST, memory, line)])


def _a_detail(line, trip, memory):
    low = _low(line)
    place, month = _cap(_as_a_visit(trip["place"])), trip["month"]
    named = place + (" in " + _cap(month) if month else "")
    who = _who(low) or ""
    how_long = _how_long(low)
    # How they are getting there is a note for the line that adds the mode to a trip already on
    # the table ("we're flying"), not for the line that gives the whole trip as news: "we're
    # flying to Rome on Monday" has booked the flight, so "take the early flight" answers a
    # question nobody asked. A line that names the place already is the trip, not the journey.
    by = _how_getting_there(low) if _low(place) not in low else ""
    told = []
    named = _mid(named)
    kids = re.search(r"\bkids?\b|\bchild|\bchildren\b|\bbaby\b|\btoddler", who or "")
    packing = PACKING.match(low) or PACKING_SAID.match(low)
    if packing:
        tail = packing.group(1).strip(" ?.!,")
        said_as_a_need = bool(PACKING_SAID.match(low))
        if not place:
            # A trip with no place yet: the packing list is about the kind of trip and the month.
            kind = _the_kind_of_trip(trip.get("how_long") or "")
            if month:
                pool = [n.format(kind=kind, month=_cap(month)) for n in PACKING_NO_PLACE]
            else:
                pool = [n.format(kind=kind) for n in PACKING_NO_PLACE_NO_MONTH]
            return _join([_pick(pool, memory, line)])
        if trip.get("visit"):
            # A visit to family is not a holiday with a packing list.
            if said_as_a_need and _one_thing_they_need(low):
                # "will i need a coat" is a question about the coat: the visit list answers what
                # to take to somebody's house, and this is not that.
                return None
            if trip.get("baby"):
                return _pick(VISIT_PACKING_FOR_A_BABY, memory, line)
            if trip.get("meal"):
                return _pick(VISIT_PACKING_FOR_A_MEAL, memory, line)
            return _pick([n.format(place=_mid(place)) for n in VISIT_PACKING], memory, line)
        if tail and not said_as_a_need and not (PACKING_FOR.match(tail)
                                                or _low(tail) == "for " + _low(place)):
            # Something else to pack for: not this trip, so not this module.
            return None
        if _an_event_not_a_place(place):
            # Not a place: what they are going to answers the question itself.
            return None
        # The month is not consulted here: whether the warm-week list is the better answer is the
        # reading's decision (`a_packing_question_about_the_trip`), and where it is, this reply is
        # never reached because the answer module has already answered.
        if month:
            notes = [n.format(place=_mid(place), month=_cap(month)) for n in PACKING_NOTES]
        else:
            notes = [n.format(place=_mid(place)) for n in PACKING_NO_MONTH]
        if kids:
            notes.append(PACKING_WITH_KIDS)
        return _join([_pick(notes, memory, line)])
    if (THE_FLIGHT.search(low) or THE_DRIVE.search(low)) and HOW_LONG_ASK.search(low) \
            and _a_carded_place(place):
        # "how long is the flight", about a place the knowledge base has a card for, is the
        # card's own answer: it knows the hours in the air, and "take the early flight" does
        # not answer how long. The note is for a place nobody has written down, where a hedge
        # is all there is - it is never better than a figure.
        return None
    if not by and not THE_MODE.search(low):
        if THE_FLIGHT.search(low):
            by = "flying"
        elif THE_DRIVE.search(low):
            by = "driving"
        elif THE_JOURNEY_ASK.search(low):
            # The question names the way they mean to go in its own verb, so the reply is about
            # that and not about the three ways there are. "how long will it take to get there"
            # names none, so it gets the car-or-the-train note rather than a mode picked for them.
            by = "driving" if JOURNEY_MODE.search(low) else "either"
    if by == "either" or (not by and THE_MODE.search(low)):
        told.append("To {0}: the car or the train if it is a few hours, a flight if it is not - "
                    "the train is the one you can leave late on.".format(named))
    elif by in ("driving", "by car"):
        told.append("Driving to {0}, so leave early and take the break halfway - the last hour "
                    "is the one that drags.".format(named))
    elif by in ("flying", "by plane"):
        told.append("Flying to {0} - take the early flight, because the day you lose waiting "
                    "around is the first day of the trip.".format(named))
    elif by in ("getting the train", "on the train", "by train", "getting a train"):
        told.append("Taking the train to {0} is the easy way in - book it now, the cheap seats "
                    "go first.".format(named))
    elif by in ("taking the ferry", "getting a ferry", "sailing", "by ferry"):
        told.append("On the ferry to {0}, so book it now - the summer crossings fill up."
                    .format(named))
    # The season was answered when the trip was, so a detail turn adds the one thing it is
    # about: the journey, the people, the length of the stay.
    if told:
        if who:
            told.append(_who_note(who, how_long, memory, line, place)
                        or _with_them(named, who, memory, line))
        return _join([t for t in told if t])
    if who and kids:
        return _join([_who_note(who, how_long, memory, line, place)])
    if who:
        return _with_them(named, who, memory, line)
    note = _who_note(who, how_long, memory, line, place)
    if note:
        return _join([note])
    return None
