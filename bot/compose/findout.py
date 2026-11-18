"""Where the answer lives, when it is not in this bot.

The last thing the bot says to a question nothing else answered is an honest hedge: "I'd
rather not guess, a quick search online will get you a solid answer". It is true, and it fits
nothing in particular - a person asking what time the tip shuts gets no more out of it than a
person asking who won the darts, and STYLE.md's "Not knowing, honestly" asks for the place
the answer lives instead:

    **User:** What time does the post office on Hill Road close today?
    **Bot:** I can't check live opening hours, sorry. Search for the branch online: its
    listing on a map app usually shows today's hours, holidays included.

Nearly every such line has the same shape underneath: the answer exists, and it lives in one
named place - the venue's own page, the operator's app, a map app, the office that
issues the thing. This module reads which of those the ask needs and says it,
with what the person will find there. Nothing here is a fact about the world, so nothing can
be invented and nothing goes stale.

Kinds are read from the ask rather than from a list of subjects, so a line nobody has written
down ("when does the bottle bank shut", "are there delays on the a38") lands in the same place
as the ones in the deck. A line that is not one of these gets None and keeps whatever the
composer had.
"""
import re

from . import pick

# The reply for a question about opening hours, and a line with nothing of its own.
HOURS = (
    "Opening hours are set by each branch rather than by the chain, and they shift at bank "
    "holidays and at short notice. The branch's own page or its map listing has today's - that's "
    "the bit that catches people out.",
    "A branch keeps its own hours and they move for holidays, a delivery day or a refit, so "
    "nothing said from here would be right today. A map app's listing for that branch is the "
    "quickest check, and a phone call settles it.",
    "Hours like that are local and they change: bank holidays, stock takes, a summer timetable. "
    "Ring the place or look at its map listing - both are updated when the hours move.",
)
# A place whose hours can be asked about. Long enough to cover the everyday ones, and a
# place named some other way simply misses the kind and keeps the composer's reply.
A_PLACE = frozenset("""
    shop shops store stores supermarket tesco asda sainsburys sainsbury aldi lidl morrisons
    coop co-op iceland waitrose branch bank banks building society library libraries tip dump
    recycling pool lido leisure gym market stall cafe caff cafe restaurant chippy chippies
    takeaway takeaway kebab chip pizza pub pubs bar pharmacy chemist chemists surgery gp
    doctors dentist dental hospital garage showroom museum gallery gallery bowling cinema
    theatre softplay church chapel club hairdresser hairdressers barber salon vets vet
    merchants warehouse centre center office reception
    beach beaches seafront promenade park parks playground zoo farm station airport stadium
    ground services mall sauna spa rink bowling karting
""".split())
# "Open" is a verb about a window, a jar and a letter as well as a shop's hours, and a person's
# own day opens too ("what time do i start"), so those lines are not this kind.
NOT_A_VENUE = frozenset("""
    window windows jar tin box boxes door doors envelope packet bottle can letter parcel
    present gift browser app file folder email shift work school run day week
""".split())
THE_PEOPLE = frozenset("""
    son daughter kid kids child children baby wife husband partner mum mom mother dad father
    boyfriend girlfriend nan grandma grandad grandson granddaughter friend boss manager
""".split())
# The ask for hours in the shapes people type it: "when does the market open", "what time does
# the tip shut", "is the pool open on sunday", "how late is the chippy open", "is there a
# pharmacy open late near me".
HOURS_ASK = re.compile(
    r"\b(?:when|what\s+time[s]?)\s+(?:does|do|is|are|will|would|can|should)\b[^?]{0,44}?"
    r"\b(?:open|opens|opening|close|closes|closing|shut|shuts|shutting)\b"
    r"|\b(?:is|are)\b[^?]{0,32}?\bopen\b")
# "How late" and "opening hours" are the same question without the verb, and they are also how a
# person asks the time of day ("how late is it") or the length of a job ("how late is it open"),
# so this shape needs a place named in the line. "How late is the chippy open" has one; "how
# late is it" does not and keeps whatever the composer had.
LATE_ASK = re.compile(r"\bhow\s+late\b|\bopen\s+late\b|\bopen\s+early\b"
                      r"|\bopening\s+(?:hours|times?)\b|\bclosing\s+time\b"
                      r"|\btill\s+(?:when|what\s+time)\b")
# A how-to about opening a thing is not a question about hours.
HOW_TO_OPEN = re.compile(r"\bhow\s+(?:do|to|can|should)\s+(?:i\s+)?open\b")

# Live travel and live plans: the operator, the club and the venue know today's, and none of
# them is a fact the bot holds.
TRAVEL = frozenset("""
    bus buses coach coaches train trains tram trams tube underground flight flights plane
    planes ferry ferries motorway motorways a-road by-pass bypass line lines route routes
    service services replacement bus traffic junction
""".split())
STATUS = frozenset("""
    running delayed delay delays cancelled canceled cancellation cancel strike strikes closed
    shut diverted diversion disruption disruptions roadworks traffic
""".split())
# A claim is about what is owed afterwards, not about where the train is now, and the operator's
# app has nothing to say about it.
TRAVEL_CLAIM = frozenset("""
    claim claims claimed refund refunds compensation compensate money owed reimburse reclaim
    pays insurance insurer hotel rebook rebooking
""".split())
# "My train was cancelled so I drove" is a story; "is my train cancelled tomorrow" is a question.
# The ask is the verb in most lines, and in some it is only the noun: "delays on the a38",
# "roadworks on the m6", "traffic on the northern line" is a person asking about today with the
# question left out, and a status word at the head of the line is as good a sign as "is".
ASKED = re.compile(r"\b(?:is|are|will|any|does|do)\b|"
                   r"^\s*(?:any\s+)?(?:delays?|disruptions?|traffic|roadworks?|road\s+works|"
                   r"cancellations?|strikes?|engineering\s+works)\b")
# A question that opens with the verb is a question whatever follows it: "is my bus running, the
# drivers were meant to be striking" is about today, not a story.
OPENS_ASKING = re.compile(r"^\s*(?:is|are|will|any|does|do|what|when|how)\b")
STORY = re.compile(r"\b(?:was|were|got|had|did|have|has|theyve|weve|ive|again|yesterday|"
                   r"this\s+morning|last\s+night)\b")
STATUS_PHRASES = ("engineering works", "called off", "on time", "bus replacement",
                  "replacement bus", "road works")
# A road named by its number - "the m6", "the a38" - is live information as much as a bus is.
ROAD = re.compile(r"(?<![a-z0-9])[am]\s?\d{1,3}(?![a-z0-9])")
TRAVEL_LINES = (
    "Disruption can clear or spread within the hour, so only today's version is worth acting "
    "on: the operator's app or a journey planner has the next service, and for a road the "
    "traffic service names the stretch.",
    "Whether it is running today is on the operator's own system, and delays move. Their app or "
    "a journey planner shows the next one and any disruption - check it just before you set off.",
)
# What's on, and when it starts: listings change weekly and a kick-off moves for television.
ON_WORDS = frozenset("""
    cinema theatre theater pictures gig gigs match game show concert festival listings listing
    play screening movie movies film films odeon vue cineworld multiplex venue
""".split())
# A thing that happens on a day: a market, a fete, a gig. "Is it on" is the same question as
# "what's on", asked about one event, and the answer lives on the event's own page too.
ON_EVENT = frozenset("""
    market markets festival fete fair gig gigs match game show concert cinema theatre play
    screening event events boot sale
""".split())
ON_ASK = re.compile(r"\b(?:whats?|what\s+is)\s+on\b|\blistings?\b|\bwhats\s+on\s+at\b"
                    r"|\bis\s+(?:it|that|the\s+[a-z]+)\s+on\b|\bstill\s+on\b")
KICK_OFF = re.compile(
    r"\bwhat\s+time\s+(?:is|does|do|will)\b[^?]{0,24}?\bkick\s*-?\s*off\b"
    r"|\bwhen\s+(?:is|does)\b[^?]{0,24}?\bkick\s*-?\s*off\b"
    r"|\bwhat\s+time\s+(?:is|does)\s+the\s+(?:match|game|final)\b"
    r"|\bis\s+the\s+(?:match|game)\s+on\b")
# The same question in the shape people use when they want a recommendation rather than a
# timetable: "what's good at the theatre this month", "what's worth seeing at the cinema",
# "what's the new film at the pictures". The venue word is what makes it a listing and not a
# taste question - "what's good to watch" on its own is a person asking what to watch, and the
# answer to that is a different kind of help.
WHAT_IS_GOOD = re.compile(
    r"\b(?:whats?|what\s+is|anything)\s+(?:good|worth\s+(?:seeing|watching|a\s+look))\b"
    r"|\bwhats?\s+(?:the\s+)?(?:new|latest)\s+(?:film|movie|play|show)\b"
    r"|\bwhat\s+(?:film|films|movie|movies|play|plays)\s+(?:is|are)\s+(?:on|showing|worth)\b"
    r"|\bwhats?\s+worth\s+(?:seeing|watching)\b")
WHATS_ON_LINES = (
    "Listings turn over every week and seats sell out quietly, so the venue's own page or a "
    "listings app is the only schedule that is right today: times, prices and what is left.",
    "That is this week's timetable, and it changes more often than a general answer could keep "
    "up with. The venue's own page or a listings app has the times, plus the number if you want "
    "to check seats.",
)
KICK_OFF_LINES = (
    "Kick-off moves for television and it can move twice, so the club's own page or a sports app "
    "is the one to trust - anything said from here could be a week out of date.",
    "The fixture list is the club's own, and televised games get moved late. Their page or a "
    "sports app has the time and says if it has been moved.",
)

# How busy it is: the queue at the tip, the wait at the surgery. Live in the same way, and only
# the place itself knows, so a call beats anything said from here. The ask has as many shapes as
# people have ways of putting it - "is the beach busy", "is casualty heaving", "will there be a
# queue" - and the crowd word is the part they all share.
BUSY = re.compile(r"\bhow\s+busy\b|\bis\s+(?:it|the\s+[a-z]+)\s+busy\b"
                  r"|\bhow\s+long\s+(?:is|are)\s+(?:the\s+)?(?:wait|queue|line)\b"
                  r"|\bwhats\s+the\s+(?:wait|queue|line)\b|\bwaiting\s+times?\b"
                  r"|\bis\s+there\s+(?:a\s+|any\s+)?(?:queue|wait|line)\b"
                  r"|\bwill\s+there\s+be\s+(?:a\s+)?(?:queue|wait|line)\b"
                  r"|\bhow\s+(?:packed|crowded|heaving|rammed)\b"
                  r"|\bwhats\s+the\s+(?:waiting\s+time|wait\s+time)\b"
                  # the queue read the other way round: "is the queue long at the post office",
                  # "is the wait bad on a saturday" - the noun carries the ask without the word
                  # "busy", and the answer is the same one.
                  r"|\bis\s+the\s+(?:queue|wait|line)\s+(?:long|bad|big|short|quick|slow)\b"
                  # the quiet half of the same question: "when is the gym quiet" asks which hour
                  # to avoid the crowd in, and the answer is the same hour read backwards.
                  r"|\bwhen\s+(?:is|are)\s+(?:\w+\s+){0,4}"
                  r"(?:quiet|emptiest|quietest|least\s+busy)\b"
                  # the same ask with the crowd word at the far end: "is casualty busy", "is the
                  # beach heaving", "are the shops manic today"
                  r"|\b(?:is|are|was|were|will|would)\s+(?:\w+\s+){1,4}"
                  r"(?:busy|packed|heaving|rammed|crowded|manic)\b")
# A crowd word in a story is not a question - "the airport was mad busy yesterday" is telling the
# bot about a day, and a line that asks nothing keeps whatever it had.
CROWD = re.compile(
    r"\b(?:busy|packed|heaving|rammed|crowded|manic|chocka|jammed|mobbed)\b", re.I)

# A crowd needs something that can be crowded. "is he busy tomorrow", "is mum busy today",
# "is the boss busy" are a person's own day, and the queue line answered them about a venue - a
# worse reply than the shrug it replaced, because it answers about the wrong subject. The person
# is read from the words the crowd word hangs off, in the same positions BUSY reads them from, and
# the third person is the one that matters: a follow-up about somebody else ("is he busy later")
# looks exactly like a venue's ask from the crowd word alone.
A_PERSON_SUBJECT = re.compile(
    r"\b(?:is|are|was|were|will|would|does|do|did)\s+(?:my\s+|our\s+|your\s+|the\s+)?"
    r"(?:he|she|they|him|her|them|you|we|i|mum|mom|mother|mam|dad|father|da|boss|manager|"
    r"sister|brother|son|daughter|wife|husband|partner|boyfriend|girlfriend|friend|mate|"
    r"nan|nana|gran|granny|grandma|grandad|grandpa|aunt|uncle|cousin|kid|kids|child|children|"
    r"baby|lad|lass|boy|girl|colleague|neighbour|neighbor|landlord|tenant|staff|team|people|"
    r"everyone|anyone|someone|nobody|somebody|bot|assistant|robot)\b")
# The noun a wait is asked with. Without a place and without one of these, "how busy is it" is
# not a question about a queue at all - it is "it" leaning on the thread, and the thread is what
# answers it.
A_WAIT_NOUN = re.compile(r"\b(?:wait|waiting|queue|queues|queuing|queueing|waiting\s+times?)\b")

BUSY_ASKS = re.compile(
    r"^\s*(?:is|are|was|were|will|would|do|does|did|can|could|should|any|how|what|whats|when"
    r"|where|which|who)\b|\?\s*$")
# What can be said about a crowd without the place or the hour: it follows the clock and the
# weather, and the number that is right is the one at the door. Both halves are what the person
# came for - the pointer on its own ("their own page has a live wait") says nothing about the
# hour they asked about.
BUSY_LINES = (
    "A queue changes hour to hour: the weekend and school pick-up are the busy half of the week "
    "and a weekday morning the quiet one, and a wet Saturday pushes everybody indoors at once. "
    "Nobody publishes it everywhere, so one call settles today faster than anything I could "
    "guess, and their own page has a live wait if they keep one.",
    "It will be worse at the weekend and around school pick-up, and better first thing, but "
    "today's wait is only on their system. Ring them before you set off - the place itself is the "
    "only one that knows.",
    "The busy hours are much the same everywhere - late morning to mid afternoon at the weekend, "
    "and the hour after school lets out - and the weather moves the whole thing. Today's version "
    "is at the place: their own page keeps a live count where it keeps one, and one call settles "
    "the rest.",
)
# A wait with no place in the line at all - "whats the waiting time", "how long is the wait" - has
# nothing to be right about, so the reply says what it knows, says where the number lives, and asks
# the one thing that would make an answer possible. Asking is the last move, not the first: the
# hour half is said either way.
BUSY_NO_PLACE = (
    "A wait is live and local, so the only figure that is right is the one at that place today: "
    "their own page keeps it where they keep one, and one call settles the rest. Waits are usually "
    "shortest first thing and longest from mid morning on. Which place is it?",
    "That changes hour to hour and place to place, so I can't put a number on it - their own page "
    "or phone has today's, and a map app's popular times shows the busy hours if you are picking "
    "when to go. First thing is usually the quiet end. Which place did you have in mind?",
)
# The same where the chat has already said a few things: the question about which place would be
# asking for something the thread may already hold, and a friend would not ask it twice, so the
# hour half and where the number lives are said on their own.
BUSY_NO_PLACE_AND_CONTEXT = (
    "A wait is live and local, so today's figure is only at the place itself: their own page keeps "
    "it where they keep one, one call settles the rest, and first thing is usually the quiet end of "
    "the day.",
    "That one moves hour to hour and place to place, so I can't put a number on it: their own page "
    "or phone has today's, and a map app's popular times shows the busy hours if you are choosing "
    "when to go.",
)
# A place named in a line, in the words people use for the places they queue at. This is the loose
# reading the thread needs: "the beach is heaving" then "how long is the wait" is one question with
# the place already in it, and asking which place would be asking for something the chat just said.
A_PLACE_IN_A_TURN = re.compile(
    r"\b(?:beach|seafront|promenade|gym|pool|leisure\s+cent\w+|tip|dump|hospital|casualty|clinic"
    r"|surgery|pharmacy|chemist|supermarket|shop|store|market|pub|restaurant|cafe|takeaway|park"
    r"|playground|museum|gallery|zoo|library|station|airport|car\s+park|high\s+street"
    r"|town\s+cent\w+|mall|ground|stadium|theatre|cinema|venue|club|centre|sauna|spa|dentist"
    r"|bank|services|attraction|soft\s*play|ice\s+rink|bowling)\b")
# A hospital's urgent department, said in any of the ways people say it.
A_AND_E = re.compile(
    r"\b(?:a\s*&\s*e|a\s+and\s+e|a\s*and\s*e|casualty|emergency\s+department"
    r"|emergency\s+room|urgent\s+care|walk[-\s]?in\s+cent\w+|minor\s+injuries)\b")

# Prices of the things an operator sets - parking, a bus, admission - are live in the same way.
PRICE_ASK = re.compile(r"\bhow\s+much\s+(?:is|are|does|do|will)\b"
                       r"|\bwhats?\s+the\s+(?:price|charge|cost|fee|rate)\b")
# Free entry is a price too, and no operator is named: "is the museum free on sunday".
FREE_ASK = re.compile(
    r"\bis\s+(?:the\s+|a\s+)?[a-z' -]{2,24}\s+free\b"
    r"|\bis\s+(?:entry|admission|parking)\s+free\b"
    r"|\bis\s+there\s+a\s+charge\b"
    r"|\bpay\s+to\s+(?:park|get\s+in|go\s+in|enter|visit)\b"
    r"|\bdo\s+(?:i|we)\s+have\s+to\s+pay\s+(?:to|for\s+(?:a|an|the|any|my|our))\b")
# "Free" joins the word before it into one adjective: gluten free, dairy free, duty free, tax
# free. None of those is a price at a gate, so they keep whatever the composer had.
FREE_COMPOUND = frozenset("""
    gluten dairy sugar fat nut nuts wheat lactose caffeine msg toll duty tax hands care cruelty
    smoke contact peanut egg soya soya soy
""".split())
PRICE_THING = frozenset("""
    parking park bus buses train trains tube taxi cab admission entry entrance ticket tickets
    delivery postage post fee fees fare fares hire rental charge
""".split())
PRICE_LINES = (
    "Rates like that are set by whoever runs the place and they change with the season: their "
    "own site or one quick call has the figure they actually charge, and a map listing carries "
    "the number if there is no site.",
    "Admission and parking prices are set locally and move with the season, so the current one "
    "is on their website or through one call, and a map listing has the number.",
)

# Whether there is anything left: a sell-out, a table, a pitch, a place at the last minute. It is
# known to the place's own booking page and to nobody else, and it changes by the hour.
AVAIL = re.compile(
    r"\b(?:tickets?|seats?|tables?|rooms?|spaces?|places?|slots?|pitches?|appointments?)\s+left\b"
    r"|\b(?:are|is)\s+there\s+(?:any\s+|a\s+)?(?:tickets?|seats?|tables?|rooms?|spaces?|"
    r"pitches?)\b"
    r"|\b(?:is\s+it|are\s+they)\s+(?:fully\s+)?(?:booked\s+up|full|sold\s+out)\b"
    r"|\b(?:is|are|has|have|did|does|will)\b[^?]{0,20}?\bsold\s+out\b"
    r"|\bcan\s+(?:i|we)\s+(?:still\s+)?(?:get|book)\s+(?:a|any)\s+(?:table|seat|ticket|room"
    r"|space|pitch|slot)\b")
AVAIL_LINES = (
    "What is left is on their booking system rather than anywhere I can see, and it changes by "
    "the hour. Their booking page shows what is still free, and the box office settles a "
    "sell-out in a second.",
    "Anything still free is in their own system, sorry - it moves too fast for a general answer. "
    "Their booking page shows it, and ringing is quicker if you are on your way.",
)

# A figure or a date about the person's own area: the council holds it, and a map app does not.
LOCAL_AREA = re.compile(
    r"\b(?:my|our)\s+(?:town|village|area|county|streets?|roads?|ward|district|neighbourhood|"
    r"postcode|council|city)\b")
LOCAL_ASK = re.compile(r"\bhow\s+many\b|\bpopulation\b|\bwho\s+is\b|\bwhich\s+band\b|"
                       r"\bhow\s+do\s+i\s+find\b|\bwhat\s+is\s+the\s+population\b")
LOCAL_LINES = (
    "Figures about your own patch come from your council, and they publish them: their site has "
    "it - the box at the top takes your postcode - and one call to the main number works if the "
    "site buries it.",
    "Your council holds that and keeps it up to date. Their site has it, or one call to the main "
    "number answers it - the postcode does most of the work.",
)
# School term dates are the school's calendar rather than a fact about the world: the school's own
# site has the inset days, which are the part a general answer always gets wrong.
TERM_DATES = re.compile(r"\bterm\s+dates?\b|\binset\s+days?\b|\bacademic\s+year\b|\bwhen\s+do\s+"
                        r"(?:the\s+)?schools?\s+(?:break|finish|start)\b")
TERM_LINES = (
    "Term dates are the school's own calendar, and the inset days are the bit a general answer "
    "always gets wrong. The school's site has both, and the council lists every school's in one "
    "place if you need to compare.",
    "The school sets its own term dates and its own inset days. Their page has both, and the "
    "council's site collects them all if you are looking at more than one school.",
)

# Something near the person rather than in the world: only a map knows what is on their street.
NEARBY_AREA = re.compile(
    r"\bnear\s?(?:me|us|here)\b|\bround\s+here\b|\bnear\sby\b|\bnearby\b"
    r"|\bin\s+my\s+(?:area|town|village|city|street|road|postcode|neighbourhood)\b"
    r"|\bmy\s+(?:postcode|area|town|village)\b")
# "The shop near me shut early" is a remark, not a search: only a question or a request for one
# gets the map-app line, so the person telling the bot their news keeps its answer.
ASKS_LOCAL = re.compile(
    r"\bis\s+there\b|\bare\s+there\b|\bwhere\b|\bwheres\b|\bwhich\b|\bany\b"
    r"|\banywhere\b|\bcan\s+(?:i|we|you)\b|\bcould\s+(?:i|we|you)\b|\bdo\s+you\s+know\b"
    r"|\b(?:i|we)\s+(?:need|want|are\s+looking|am\s+looking)\b|\blooking\s+for\b"
    r"|\brecommend\b|\bfind\b|\bwhats\s+good\b|\bgood\s+(?:place|places|spot|spots)\b")
# "The nearest pharmacy" names a thing on their own street without saying "near me" at all; a
# nearest airport to Lisbon is a fact about the world, so "closest to" is left out.
NEAREST = re.compile(r"\b(?:nearest|closest)\s+(?!to\b)[a-z]+")
NEARBY_SERVICE = frozenset("""
    pharmacy chemist cashpoint atm supermarket shop store garage launderette laundrette dentist
    doctors surgery hospital petrol gym pool park school nursery vet takeaway chippy pub cafe
    restaurant bank tip
""".split())
DELIVER = re.compile(r"\bdeliver(?:y|s|ed)?\s+(?:to|in)\b|\bdeliver\s+to\s+my\b|"
                     r"\bdo\s+(?:they|you)\s+deliver\b")
DELIVER_LINES = (
    "Delivery depends on the postcode and the day, and only the shop's own checker knows it: put "
    "your postcode in on their site and it says yes or no in a second, with the earliest slot.",
    "That depends on the postcode, which their own delivery checker holds - it takes ten seconds "
    "with your postcode in, and it shows the earliest date too.",
)
NEARBY_LINES = (
    "What is near you depends on your postcode, so a map app is the one that knows: it lists the "
    "closest in order of distance, with today's hours and a phone number for each one.",
    "A map app puts them in order of distance and carries the phone number, which is faster than "
    "any list I could give you from here.",
)

# A method question ("how do i get a refund from a cancelled flight") is about the world and
# has an answer of its own; it is not a live status and not a form to fetch.
HOW_TO = re.compile(r"\bhow\s+(?:do|can|should|would)\s+(?:i|we)\b|\bhow\s+to\b|"
                    r"\bwhat\s+do\s+i\s+need\s+to\b|\bwhats\s+the\s+best\s+way\b")

# The office that issues a thing: a licence, a card, a copy of a record, the rules on a fire.
OFFICIAL_ASK = re.compile(
    r"\b(?:whats|what\s+is|what\s+are)\s+the\s+(?:law|rules?|legal\s+position|regulations?)\b"
    r"|\bis\s+it\s+(?:legal|allowed|illegal)\b|\bam\s+i\s+(?:allowed|legally)\b"
    r"|\bdo\s+i\s+need\s+(?:a|an|any|to)\b"
    r"|\bhow\s+do\s+i\s+(?:get|apply|renew|replace|register|order|book)\b"
    r"|\bhow\s+do\s+i\s+(?:check|find\s+out)\s+(?:if|whether|who|what)\b")
OFFICIAL_THING = frozenset("""
    licence license permit permission registration certificate copy record records badge card
    cscs dbs crb passport visa form application skip planning consent exemption grant benefit
    number registered register renewal certificate blue disabled
""".split())
# A question about the rules needs no thing of its own: the rules are what is being asked about.
RULES_ASK = re.compile(r"\b(?:law|legal|allowed|rules?|regulations?|illegal)\b")
# A board game has rules and no council: "what are the rules of uno" is not a question about the
# law. Nor is a bare "what are the rules", which names nothing to have rules about.
GAME = frozenset("""
    uno chess poker monopoly scrabble darts snooker dominoes cluedo risk rummy bingo
""".split())
ASK_STOP = frozenset("""
    what whats is are the a an it i we you do does to of on for in my our and if can could
    there be this that rule rules law legal allowed illegal regulations regulation about
""".split())
OFFICIAL_LINES = (
    "Anything with a form behind it is set by the office that issues it, and the fee and the "
    "paperwork change with the year. Their official page - GOV.UK for the national ones, your "
    "council for anything local - names what to send, what it costs and how long it takes.",
    "The form, the fee and the waiting time all come from the office that issues it, and they "
    "change. Their own page is the one to act on, and it says who to ring if your case does not "
    "fit the standard one.",
    "The rules differ by council and by country, so the version that counts is on the issuing "
    "office's own page: GOV.UK has the national forms, and the page names who to ring about the "
    "rest.",
)
# The rules themselves, rather than a form to fill in: the local version is the one that counts.
RULES_LINES = (
    "Rules like that are set locally and the byelaws differ from one council to the next: your "
    "council's site has them, plus the permit if one is needed, and their phone line answers the "
    "odd case.",
    "The rules differ by council and by country, so the local version is the only one worth "
    "acting on: the council's site has it, and GOV.UK has the national half.",
)


# Registering a death is a form for a person and nothing at all for a pet: a cat that died has
# no official page, so the honest hedge is better than a form and fee that does not exist.
PET = frozenset("""
    cat cats dog dogs kitten puppy pet pets hamster rabbit budgie parrot
""".split())
DIED = frozenset("""
    died dead death passing euthanised put down cremated
""".split())


# A report is not an ask. "roadworks on the m6 ruined my morning", "delays on the a38 every single
# day", "roadworks on the m6, absolute chaos" - the person is telling the bot how their week went,
# and the receipt ("I'm listening - say more if it helps") is what a friend says back. The status
# word and the road are both there, so without this the readings below turn a complaint into a
# live-travel note nobody asked for. A duration says how long it has been going on, which is what
# makes it a report; the same words with a question mark are still the ask.
A_REPORT = re.compile(
    r"\b(?:every\s+(?:single\s+)?(?:day|week|morning|evening|night|time)"
    r"|all\s+(?:week|weeks|month|months|year|day|days|morning|night|the\s+time)"
    r"|for\s+(?:weeks|months|days|ages|hours)"
    r"|since\s+(?:january|february|march|april|may|june|july|august|september|october|november"
    r"|december|last|monday|tuesday|wednesday|thursday|friday|saturday|sunday|easter|christmas|then)"
    r"|each\s+(?:day|week|morning)"
    r"|the\s+whole\s+(?:week|month|day)"
    r"|ruined|ruins|wrecked|wrecks|chaos|nightmare|fed\s+up|sick\s+of|so\s+tired|held\s+me\s+up"
    r"|made\s+me\s+late|cost\s+me|missed\s+my)\b")


def reads_as_a_report(text):
    """True when the line is telling the bot about something rather than asking about it."""
    said = " ".join(str(text or "").lower().split())
    return bool(said) and not said.endswith("?") and bool(A_REPORT.search(said))


def _words(clean):
    """The line as whole words, for the tests that only need to know one is present."""
    return re.findall(r"[a-z0-9'-]+", clean)


def reads_as_crowd(clean):
    """True when the line asks how busy somewhere is - the crowd half of `reads_as_busy`.

    Kept apart from the bare "how long is the wait", because a wait is also the word for a
    service's own delay ("how long is the wait for a hip replacement") and a card answers that.
    A crowd adjective is never that: "is the tip busy today" is about today's queue and nothing
    else.
    """
    text = " ".join(str(clean or "").lower().split())
    return bool(text) and bool(CROWD.search(text)) and bool(BUSY_ASKS.search(text))


def reads_as_busy(clean):
    """True when the line asks how busy somewhere is, or how long the wait is.

    The ask keeps its kind even where the bot's own line already names a page: a page tells the
    person where today's figure is, and what they asked about was the next hour. So a hedge that
    says "Wikipedia has it" still gives way to the busier-or-not reading.
    """
    text = " ".join(str(clean or "").lower().split())
    return bool(text) and bool(BUSY.search(text)) and bool(BUSY_ASKS.search(text))


def _a_place_a_line_back(memory):
    """The place named in the last thing either side said, if the thread has one in it.

    "is the beach heaving" then "how long is the wait" is one question with the place already in
    it, so the second line gets the place's answer and is not asked which place it means.
    """
    for turn in reversed(((memory or {}).get("turns") or [])[-3:]):
        if not isinstance(turn, dict):
            continue
        for side in ("user", "bot"):
            said = " ".join(str(turn.get(side) or "").lower().split())
            if said and A_PLACE_IN_A_TURN.search(said):
                return said
    return ""


def pool(clean, memory=None):
    """The lines for a question whose answer lives somewhere else, or None."""
    text = " ".join(str(clean or "").lower().split())
    if not text:
        return None
    said = set(_words(text))
    if reads_as_a_report(text):
        return None
    # How busy it is comes before the opening hours: "is the tip busy today" has the word "today"
    # in it and was answered about the hours, which is a different question. A busier-or-not ask
    # with no place in it is still that kind of ask - the reply says what the hour does and asks
    # which place, rather than leaving the person with a shrug.
    if BUSY.search(text) and BUSY_ASKS.search(text):
        if A_PERSON_SUBJECT.search(text):
            # Somebody's own day. Nothing here queues, so this kind stands down and the turn goes
            # to whoever can answer it: a line about a place they never asked about is worse than
            # the shrug it replaced.
            return None
        if said & A_PLACE or A_PLACE_IN_A_TURN.search(text) or A_AND_E.search(text):
            return BUSY_LINES
        if _a_place_a_line_back(memory):
            return BUSY_LINES
        if not A_WAIT_NOUN.search(text):
            # "how busy is it", "how packed does it get": no place in the line, no place in the
            # thread and no word for a wait, so there is nothing here that can be crowded. A
            # crowd word on its own is not "how long is the queue".
            return None
        if (memory or {}).get("turns"):
            return BUSY_NO_PLACE_AND_CONTEXT
        return BUSY_NO_PLACE
    # Hours: a place named in the line, and an ask about when it opens or shuts.
    if ((HOURS_ASK.search(text) and (said & A_PLACE or "it" in said))
            or (LATE_ASK.search(text) and said & A_PLACE)):
        if not HOW_TO_OPEN.search(text) and not said & NOT_A_VENUE and not said & THE_PEOPLE:
            return HOURS
    # A kick-off, then what's on: both are timetables that change weekly.
    if KICK_OFF.search(text):
        return KICK_OFF_LINES
    if said & (ON_WORDS | ON_EVENT) and ON_ASK.search(text):
        return WHATS_ON_LINES
    # A recommendation asked about a venue's programme is the same timetable, so it wants the
    # same place: "what's good at the theatre this month" is not a question about taste.
    if said & ON_WORDS and WHAT_IS_GOOD.search(text):
        return WHATS_ON_LINES
    # Live travel: a way of travelling or a numbered road, and something wrong or due. A how-to
    # about travel ("how do i get a refund from a cancelled flight") is a method, not a status.
    if ((said & TRAVEL or ROAD.search(text)) and not HOW_TO.search(text)
            and not said & TRAVEL_CLAIM and not THEIR_OWN_ONLINE.search(text)
            and ASKED.search(text)
            and not (STORY.search(text) and not OPENS_ASKING.search(text))
            and (said & STATUS or any(phrase in text for phrase in STATUS_PHRASES))):
        return TRAVEL_LINES
    # What an operator charges for something they run.
    if (PRICE_ASK.search(text) and said & PRICE_THING) or (
            FREE_ASK.search(text) and not said & FREE_COMPOUND):
        return PRICE_LINES
    if AVAIL.search(text):
        return AVAIL_LINES
    # A figure about their own town: the council holds it, which is not a map app's job. The
    # town has to be theirs - "how many hours a day" on a road trip is not a council question.
    if LOCAL_AREA.search(text) and LOCAL_ASK.search(text):
        return LOCAL_LINES
    # Their street, or whether a shop will come to their postcode. A figure about their own area
    # is not about what is near it ("how many people live in my town" got the map-app line).
    if DELIVER.search(text):
        return DELIVER_LINES
    if TERM_DATES.search(text):
        return TERM_LINES
    if (NEARBY_AREA.search(text) and ASKS_LOCAL.search(text)) or (
            NEAREST.search(text) and said & NEARBY_SERVICE):
        return NEARBY_LINES
    # The office that issues it: only when a thing to be issued or a rule is named, so
    # "how do i get to sleep" and "how do i get better at chess" keep their own answer. A
    # question about the law or the rules needs no thing of its own: the rules are the thing.
    if OFFICIAL_ASK.search(text) and not (said & PET and said & DIED):
        if said & OFFICIAL_THING:
            return OFFICIAL_LINES
        if RULES_ASK.search(text) and not said & GAME and said - ASK_STOP:
            return RULES_LINES
    return None


# The loosest ask of all: no ask word and no verb, only a status word spent on the thing it is
# about - "delays on the a38", "roadworks on the m6", "disruptions on the northern line". In
# somebody's typing that is a question about today; in the composer's reading it is a remark, so
# the neutral pool files it and says "Got it." - a placeholder to the person who asked. The
# preposition is what keeps it honest: "traffic was awful", "roadworks made me late" and
# "strikes are a nightmare" are the story of a day and stay with the pool that reads stories.
A_STATUS_SPENT_ON = re.compile(
    r"^\s*(?:any\s+|the\s+)?(?:delays?|disruptions?|traffic|roadworks?|road\s+works|"
    r"cancellations?|strikes?|engineering\s+works)\s+"
    r"(?:on|at|near|around|by|into|outside|through)\b")


# A status word spent on a thing of theirs that is not a road or a service is not today's
# travelling, either: "traffic to my etsy shop is down" is about a business, and a journey
# planner has nothing to say about it.
THEIR_OWN_ONLINE = re.compile(
    r"\b(?:my|our)\s+(?:site|website|web\s*page|page|shop|store|storefront|listing|listings|"
    r"blog|channel|profile|etsy|ebay|account|sales)\b")


# A status word spent on something of their own is about that thing, not about today's
# travelling: "delays on my order" belongs to the shop, not to a journey planner.
NOT_THEIR_STATUS = re.compile(r"\b(?:my|our|order|parcel|delivery|claim|refund)\b")


def pool_over_a_receipt(clean):
    """The lines for a line the composer would otherwise meet with only the flat receipt.

    Kept apart from `pool` because the reading is deliberately looser: the only evidence of a
    question is a status word spent on a named road or line. It is consulted only where the reply
    is already the neutral receipt, so every pool above keeps its turn.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or not A_STATUS_SPENT_ON.search(text):
        return None
    if reads_as_a_report(text):
        return None
    # The reader below is anchored to a status word at the head of the line, so the article that
    # sometimes opens it ("the delays on the a38") comes off here rather than in the reader,
    # where it would widen every other kind too.
    bare = text[4:].strip() if text.startswith("the ") else text
    found = pool(bare)
    if found:
        return found
    # The reader above wants to recognise the thing after "on" as a service or a road, and some
    # of them it cannot: "cancellations on the 7am" names a train by its time. A status word
    # spent on a thing is the ask either way, so the operator's answer stands - unless the thing
    # is one of theirs, where the operator is not who holds it ("delays on my order").
    if NOT_THEIR_STATUS.search(bare):
        return None
    return TRAVEL_LINES


# The line after a gap: "roadworks on the m6" then "is it going to add an hour". The follow-up
# names nothing the reader above can hold - no road, no operator - and it reached the search
# hedge one turn after the bot had named the place that knows. A short question that carries a
# back-reference is about the same gap, and the same app still has it.
A_FOLLOW_UP = re.compile(
    r"^\s*(?:is|are|will|would|how\s+(?:long|much|bad|far)|what\s+about|and\b|"
    r"does|do)\b")
A_BACK_REFERENCE = re.compile(r"\b(?:it|that|they|them|those|this|the\s+same|still)\b")


def more_about_the_journey(clean, memory):
    """The travel answer again, for a follow-up to a turn findout just answered.

    Only the journey: hours, prices and the rest of the kinds have a follow-up that is a new
    question about the same place, and the pool for the previous kind would answer the wrong
    one. The bot's own last line is the test - if it came from somewhere else, this stands down.
    """
    text = " ".join(str(clean or "").lower().split())
    if not text or not A_FOLLOW_UP.search(text) or not A_BACK_REFERENCE.search(text):
        return None
    turns = [t for t in (memory.get("turns") or []) if t.get("bot")]
    if not turns:
        return None
    last = turns[-1].get("bot") or ""
    if last in TRAVEL_LINES:
        return TRAVEL_LINES
    # The same rule for every live note, not just this file's: a status word spent on a road
    # ("roadworks on the m6") is now answered by the roads note, and "is it going to add an hour"
    # one turn later reached the search hedge because the stand-down only knew this file's lines.
    # Whatever live note the bot has just given, the follow-up gets that note again.
    from . import fallback_data
    for _kind, _phrases, options in fallback_data.LIVE_KINDS:
        if last and last in options:
            return tuple(options)
    return None


# A hedge is not always a gap. Some of the bot's own lines already say what the bot cannot see and
# send the person somewhere that can answer - "I can't look at a map from here, sorry. A map app
# puts them in order of distance" is the whole of what this file would say, said shorter. The
# reading here keeps those turns, so the pools above only ever replace a line that names nothing:
# it is the test for "already done", not a fact about the world.
#
# "Search" and "look it up" are deliberately not here. They are what the pools above exist to
# replace: a search engine is not a place that holds the hours of one shop, today's queue at one
# tip, or the form for one licence.
A_PLACE_NAMED = re.compile(
    r"\b(?:map app|maps|google maps|the council|council'?s?|gov\.uk|\.gov\b|government"
    r"|operator'?s?|journey planner|traffic service|road agency|roads agency|national rail"
    r"|pharmac(?:y|ist)|chemist|\bgp\b|doctor'?s|surgery|the ward|nurse|vet'?s?|veterinary"
    r"|their (?:own )?(?:site|website|web page|page|app|account|office|desk|number)"
    r"|the (?:official )?(?:site|website) of|official (?:page|site)"
    r"|box office|ticket office|the office that|issuing office|passport office|dvla"
    r"|registry office|landlord|letting agent|estate agent|employer|\bhr\b|payroll"
    r"|your bank|the bank|insurer|insurance company|the airline|the hotel|the venue"
    r"|the airline'?s?|one call|give them a ring|ring them|call them|their line)\b")
# The same, said as a route to a figure rather than as a place: "the number is on a map listing",
# "their page has the form", "the app has today's". One noun and one thing it holds.
HOLDS_IT = re.compile(
    r"\b(?:has|have|shows|lists|carries|publishes|updates)\b[^.]{0,30}"
    r"\b(?:number|form|fee|price|prices|hours|wait|times|schedule|status|page|listing)\b")


def says_where_to_look(reply):
    """True when a reply already names a place that holds what the person asked for."""
    said = " ".join(str(reply or "").lower().split())
    if not said:
        return False
    return bool(A_PLACE_NAMED.search(said) or HOLDS_IT.search(said))

# --- the thing they have in front of them ----------------------------------------------------
#
# A plate and a sheet answer what is true of *this* one, and the bot cannot see either - but it
# does know which one carries the rest. This is the half a reply can give when no card fits: name
# the thing back, name what carries the answer, and ask the one question that narrows it. Only a
# hedge is replaced (see `bot/modules/greeting.py`), so every pool above and every card keeps its
# turn, and nothing here is a fact about the world.
# The three kinds of thing whose answer is written down for the person to read. A thing is looked
# up here by its own name rather than by a guess at the sentence: a kit's answer is on its sheet, an
# appliance's on its plate and its maker's page, a piece of paperwork's on its own reference.
A_KIT = re.compile(
    r"\b(?:shed|wardrobe|bookcase|bookcases|shelves|shelving|shelf|flat\s*pack|flatpack|kit|"
    r"units?|desk|bed|bunk|trampoline|greenhouse|climbing\s+frame|table|chair|chairs|cabinet|"
    r"bbq|barbecue|swing\s*set|playhouse|sideboard|tiles?|flooring|laminate|decking|fence|"
    r"fencing|gate|sheds|curtain\s+pole|blinds?|radiator\s+cover|sofa|settee|couch|mattress|"
    r"sofa\s+bed|armchair|dining\s+table)\b")
# A tap, a sink and a shower are fitted to a house and then repaired, not taken out of a box and put
# together: "my kitchen tap is dripping" is answered by the fault, and "is it hard to fix" is a
# question about the work rather than about anything that came in the box. A kit's sheet is the wrong
# carrier for one, so they have their own kind (measured: a dripping tap, whose own repair the
# composer had just given, was then asked for "the sheet and the parts list that came with it").
A_FIXTURE = re.compile(
    r"\b(?:tap|taps|sink|sinks|shower|showers|toilet|loo|cistern|ballcock|bath|bathroom\s+suite|"
    r"stopcock|soil\s+pipe|waste\s+pipe)\b")
AN_APPLIANCE = re.compile(
    r"\b(?:boiler|washing\s+machine|washer|dishwasher|fridge|freezer|oven|cooker|hob|microwave|"
    r"kettle|toaster|hoover|vacuum|dryer|tumble\s+dryer|radiator|thermostat|heater|dehumidifier|"
    r"mower|lawnmower|strimmer|hedge\s+trimmer|drill|printer|laptop|phone|tablet|console|"
    r"telly|tv|television|router|doorbell|camera|battery|charger|remote)\b")
PAPERWORK = re.compile(
    r"\b(?:letter|form|invoice|bill|statement|contract|policy|insurance|quote|receipt|"
    r"reference|application|claim|tenancy|lease|mortgage|payslip|p60|p45|council\s+tax|licence|"
    r"license|passport|visa|permit|booking|confirmation|delivery|order|parcel|refund|warranty|"
    r"guarantee|tracking)\b")

# A commitment with terms: a gym, a phone, a subscription, a tenancy, a timeshare. Getting out of one
# is answerable without knowing which one it is, because the way out is always written in the terms.
A_COMMITMENT = re.compile(
    r"\b(?:gym\s+membership|phone\s+contract|mobile\s+contract|care\s+home|home\s+care|"
    r"lease\s+car|car\s+finance|direct\s+debit|times\s+share|gym|membership|contract|"
    r"subscription|tariff|tenancy|lease|timeshare|nursery|course|classes|insurance|policy|"
    r"broadband|loan|finance|hp)\b")
ASK_GET_OUT = re.compile(
    r"\bget\s+out\s+of\b|\bhow\s+(?:do|can|should)\s+(?:i|we)\s+(?:cancel|stop|end|leave|quit|"
    r"exit)\b|\bcancel\s+(?:it|my|the|this|that|our)\b|\bstop\s+paying\b|\bend\s+(?:the|my|"
    r"this|our)\b|\bgive\s+notice\b|\bopt\s+out\b|\bcome\s+out\s+of\b|\bbreak\s+(?:the|my)\b")

# A question about what the bot itself said, or about the person's own doings, is a question about
# the conversation rather than about the thing in it: "what was i cooking?" two lines after a
# dishwasher is not a request for the plate inside the door.
NOT_ABOUT_THE_CONVERSATION = re.compile(
    r"\b(?:what|which)\s+(?:was|were|did|have|had)\s+(?:i|we|you)\b|\bwhat\s+am\s+i\b|"
    r"\bdo\s+you\s+remember\b|\bwhat\s+did\s+(?:i|we|you)\s+(?:say|ask|tell)\b|"
    r"\bwhat\s+(?:i|we)\s+(?:said|asked|told)\b|\bremind\s+me\b")
# And a line asking the bot to do the writing is asking for an offer rather than for a fact: "can
# you help me write it", "draft something", "make it shorter" are the composer's own drafting
# replies, and a plate named over the top of them answers nothing.
NOT_A_LOOKUP_BUT_A_REQUEST = re.compile(
    r"\b(?:help\s+me|can\s+you|could\s+you|would\s+you|will\s+you|shall\s+i)\s+"
    r"(?:write|draft|word|put|phrase|text|reply|answer|compose|translate|summari[sz]e|rewrite|"
    r"shorten|tidy|check|read)\b|\bwrit(?:e|ing)\s+(?:it|that|this|him|her|them)\b|"
    r"\bdraft\s+(?:it|that|this|something)\b|"
    r"\b(?:write|reply|text|email|message|answer)\s+(?:to\s+)?(?:him|her|them|the\s+\w+)\b|"
    r"\bhow\s+(?:do|should)\s+i\s+(?:write|word|phrase|put)\b|\b(?:re)?word\s+(?:it|that|this)\b|"
    # "make it firm but polite", "make it a bit shorter": an instruction to edit what the bot just
    # wrote. Any adjective at all can follow, so the frame is what is matched, not the one word.
    r"^make\s+(?:it|this|that|them)\b|\bmake\s+it\s+(?:more|less|a\s+bit|much)\b|"
    r"\b(?:add|drop|cut|keep)\s+(?:a|the)\s+(?:line|bit|sentence|word)\b")

# A question about the visit is about the person coming, not about the thing they come to: "will
# they need to come inside", "how long will the engineer be", "do i need to be in" are answered by
# the firm on the phone, and a plate named over them answers nothing.
NOT_ABOUT_THE_VISIT = re.compile(
    r"\bwill\s+(?:they|he|she|it)\s+need\b|\bneed\s+to\s+come\s+(?:in|inside|out|back|round)\b|"
    r"\bcome\s+(?:in|inside|out|back|round)\b|\bneed\s+access\b|\bget\s+to\s+it\b|"
    r"\bhow\s+long\s+will\s+(?:they|he|she|someone|the\s+(?:engineer|plumber|fitter|installer|"
    r"technician|electrician|man))\b|\b(?:they|he|she)\s+(?:turn\s+up|arrive)\b|"
    r"\b(?:have|get)\s+(?:it\s+|everything\s+|them\s+)?ready\b|\bready\s+(?:for|when)\s+"
    r"(?:them|him|her|someone|the\s+\w+)\b|\bwhat\s+(?:do|should)\s+i\s+(?:tell|say\s+to|show|"
    r"give|ask|bring)\b|\bwait\s+in\b|\bbe\s+(?:in|there)\s+(?:for|all)\s+(?:the\s+)?(?:day|morning|afternoon)\b")

# A plan or a confirmation is not a fact a sheet holds either. "What time should i start cooking",
# "when should i leave", "shall i bleed the rads as well" want the day's order or a nod on
# something already said, and a plate named over them answers a different question - both measured
# losses in the deck. The advice-shaped "should i send it back" is a real carrier ask and is
# matched below, so only the planning frames and the flat "shall i" are stopped here.
A_PLAN_ASK = re.compile(
    r"\bwhat\s+time\s+(?:should|do|shall|would)\s+(?:i|we)\b|\bwhen\s+should\s+(?:i|we)\b|"
    r"\bshould\s+(?:i|we)\s+(?:start|begin|leave|set\s+off|get\s+up)\b|"
    r"\bhow\s+long\s+(?:before|ahead)\b|^\W*shall\s+i\b|\bshall\s+i\s+(?:also|do|just|be)\b")

# Cooking is not a look-up on the machine. "How long in the oven", "do i need to take the skin
# off", "what goes with it" are answered by knowing food, and the oven in the thread is the thing
# being cooked in, not the thing being asked about (measured: a chicken-thighs chat got the plate).
A_COOKING_LINE = re.compile(
    r"\b(?:cook|cooked|cooking|roast|bake|baking|fry|frying|boil|grill|simmer|steam|poach|"
    r"marinate|season|seasoning|baste|skin|thighs?|breasts?|fillet|mince|pasta|rice|sauce|dough|"
    r"pastry|chicken|beef|pork|lamb|turkey|fish|prawn|veg|vegetables|potatoes|onion|garlic)\b")

# And a number they have just read out is their own reading, not a fact about the unit: "is that
# too low", "is that about right", "is 1 bar enough" want to know whether the figure is normal,
# which is knowledge about the measure rather than anything written on the thing (measured).
A_READING_JUST_GIVEN = re.compile(
    r"\b(?:is|was|are)\s+(?:that|this|it|those)\s+(?:too|about\s+right|ok\b|okay\b|normal\b|"
    r"enough\b|much\b|low\b|high\b|fine\b)|\bis\s+\d[\d.,]*\s*\w*\s+(?:enough|too|ok\b|fine\b|normal\b)")

# Why something is happening is reasoning over what they have just said, not a fact written on the
# thing: "is that why it keeps locking out" after a pressure reading is a question about the fault,
# and the plate is no answer to it (measured).
A_WHY_ASK = re.compile(
    r"\bis\s+that\s+why\b|\bwhy\s+(?:does|do|is|are|would|did|has|have|am\s+i)\b|"
    r"\bwhat\s+causes?\b|\bcould\s+that\s+be\s+(?:why|it)\b|\bis\s+that\s+(?:what|the\s+reason)\b")

# How to do the job by hand, and what the bot would do, are both somebody's judgement or a method:
# "how do i take the head off", "what would you do" - measured, both took the plate and the plate
# answers neither. Only the frames that ask for a method or an opinion are stopped; "how do i know
# which model" is a real plate question and is not here.
# "Can i do it now", "is it ok tonight", "can i do it the day before": the question is about their
# own day, and what settles it is the order the job goes in - not anything written on the thing
# (measured: a pudding-then-overnight cooking chat got the oven's plate).
A_NOW_OR_NEVER_ASK = re.compile(
    r"\b(?:now|today|tonight|tomorrow|this\s+evening|the\s+day\s+before|the\s+night\s+before|"
    r"last\s+night|overnight)\b[^.?!]{0,40}\b(?:can|could|should|shall|will)\s+(?:i|we)\b|"
    r"\b(?:can|could|should|shall)\s+(?:i|we)\b[^.?!]{0,40}\b(?:now|today|tonight|tomorrow|"
    r"overnight|the\s+day\s+before)\b")

# A decision about carrying on is theirs, not a documented step: "should i stop using it" after an
# oven has sparked, "is it ok to keep going" - nothing written on the thing settles whether it is
# safe or sensible to keep at it, and naming the plate over that question answers a different one
# (measured: a sparking oven got its model plate where the composer had said whose call it was).
# The document verbs are left alone ("should i send it back" is a real carrier ask: the returns
# note says), so only the frames about going on, stopping or using are stopped here.
A_DECISION_ABOUT_GOING_ON = re.compile(
    r"\bshould\s+(?:i|we)\s+(?:stop|keep|carry\s+on|carry|bother|risk|go\s+ahead|wait|"
    r"use|still|replace|fix|put\s+up\s+with)\b|"
    r"\b(?:is|was)\s+(?:it|that)\s+(?:safe|ok\b|okay\b|fine\b|alright)\s+to\s+"
    r"(?:keep|carry|use|go\s+on|carry\s+on)\b")

A_METHOD_OR_ADVICE_ASK = re.compile(
    r"\bhow\s+(?:do|can|should|would)\s+(?:i|we|you)\s+(?:take|get|put|fit|remove|undo|open|"
    r"change|replace|fix|clean|unblock|unblock|bleed|reset|wire|connect|assemble|dismantle|strip|"
    r"hang|mount|seal|glue|screw|drill|paint|cut|adjust|tighten|loosen)\b|"
    r"\bwhat\s+would\s+you\s+do\b|\bwhat\s+should\s+(?:i|we)\s+do\b|"
    r"\bwhat\s+do\s+you\s+(?:think|reckon|suggest|recommend)\b|\bany\s+(?:advice|ideas|thoughts)\b")

# A judgement is not a fact a sheet holds. "Is the shed worth the money", "is it any good", "how
# much does one cost" are asking for a verdict or a price, and a plate or a reference named over
# the top of them answers a different question than the one asked.
A_JUDGEMENT_ASK = re.compile(
    r"\bworth\b|\bvalue\b|\bany\s+good\b|\bgood\s+(?:idea|buy)\b|\bhow\s+much\b|"
    r"\bcheaper\b|\bbetter\s+buy\b|\bshould\s+(?:i|we)\s+(?:buy|get)\b|\bwaste\s+of\s+money\b")

# A plate and a sheet answer what is true of *this* one: its model, its fault, what it came with,
# the size of the box, when it is coming. They do not answer how a thing is used or kept - how
# often it wants servicing, whether it needs rinse aid or salt, which filter it takes - and the
# first step must not be said over a question of that kind. Those are general questions about a
# model of thing, and the hedge that says the bot cannot say is truer than a label would be.
NOT_ON_THE_PLATE = re.compile(
    r"\bservic(?:e[sd]?|ing)\b|\bhow\s+often\b|"
    r"\brinse\s+aid\b|\bsalt\b|\bdescal\w*|\badditive\b|\bsoftener\b|"
    r"\b(?:which|what)\s+filter\b|\bfilter\s+(?:does|should)\b|"
    r"\btablets?\b|\bpowder\b|\bdetergent\b|"
    r"\bhow\s+(?:do|should)\s+(?:i|we)\s+(?:use|load|set|run|fill)\b|"
    r"\bshould\s+(?:i|we)\s+(?:use|put|add|fill|run)\b")

# A line about a body, a medicine or somebody's own person is another reader's. A carrier named
# beside a pain is not an answer to the pain.
NOT_HERE = re.compile(
    r"\b(?:pain|hurts?|ache|aching|sore|swollen|swelling|rash|lump|bleeding|blood|dose|dosage|"
    r"tablets?|pills?|medicines?|medication|prescription|symptoms?|sick|vomiting|dizzy|breath|"
    r"chest|stomach|mum|mom|dad|son|daughter|wife|husband|partner|baby|child|kids?|gran|nan)\b")

# The ask, and only the asks a sheet or a plate or a reference can settle.
ASK_TOOLS = re.compile(
    r"\b(?:what\s+tools?|what\s+(?:do|will|would|might)\s+(?:i|we|you)\s+need|tools?\s+(?:do|will)"
    r"|what\s+do\s+i\s+need\s+(?:to|for)|what\s+will\s+i\s+need)\b")
ASK_HOW_LONG = re.compile(
    r"\bhow\s+long\s+(?:does|do|will|would|should|to|is|takes?)\b|\bhow\s+many\s+hours\b|"
    r"\bhow\s+long\s+(?:a|an|one|it|they|that)\b")
ASK_SIZE = re.compile(
    r"\bwhat\s+size\b|\bwill\s+it\s+fit\b|\bhow\s+big\b|\bwhat\s+(?:kind|sort)\s+of\s+\w+\s+"
    r"(?:do|will)\s+(?:i|we)\b|\bwhich\s+(?:one|size|model)\b")
ASK_BE_IN = re.compile(
    r"\bbe\s+in\s+for\s+it\b|\bneed\s+(?:to\s+)?be\s+(?:in|here|home)\b|\bsign\s+for\s+it\b|"
    r"\b(?:does|will)\s+(?:it|someone|they)\s+need\s+to\s+be\s+in\b|\bwaiting\s+in\b")
ASK_COVERED = re.compile(
    r"\b(?:covered|cover\s+(?:it|this|that|me)|tell\s+the\s+insurance|insurance\s+(?:about|know)|"
    r"claim\s+(?:on|for)|on\s+the\s+policy|included|comes?\s+with\s+it)\b")
ASK_EXACT = re.compile(
    r"\bwhich\s+(?:model|part|spare|size|one|type|version)\b|\bwhat\s+(?:model|number)\b|"
    r"\bpart\s+number\b|\bwhich\s+one\s+(?:do|should|will)\b")
# "do i need to send it back", "do i have to send the old one off": the paperwork itself says what
# it wants back, in what state, and by when, and that is the only place that knows.
ASK_SEND_BACK = re.compile(
    r"\bsend\s+(?:it|them|that|this|the\s+old\s+one)\s+(?:back|off|in)\b|"
    r"\bsend\s+(?:it\s+|them\s+)?(?:back|off)\b|\b(?:do|must|should|need\s+to|have\s+to)\s+"
    r"(?:i\s+)?(?:return|post|send)\b|\breturn\s+(?:it|them|the\s+old\s+one)\b")

# What to look at, by the ask and the kind of thing. Each line names the carrier and says what it
# settles; none of them says what any of it is.
CARRIERS = {
    ("tools", "kit"): (
        "The instruction sheet in the box lists the tools and the fixings, and says which of them "
        "you can do without",
        "The parts list that came with it names the tools it wants, and the fixings are usually "
        "in the box with them",
    ),
    ("tools", "appliance"): (
        "The installation page for your model lists what it needs, and the plate on the machine "
        "says which model yours is",
        "The maker's own page for that model names the tools and whether the fixings come with it",
    ),
    ("how_long", "kit"): (
        "The instruction sheet gives the number of hours for two people, and the maker's page "
        "usually repeats it with the same figure",
        "The maker's page for it has the build time, and the instructions break that down into "
        "what has to be done in order",
    ),
    ("how_long", "appliance"): (
        "The maker's page for your model says how long the job should take, and the plate on it "
        "tells you the model",
        "Whoever services that make will give you a time on the phone from the model number "
        "alone, which is on the plate",
    ),
    ("how_long", "paperwork"): (
        "The reference on the paperwork is what a straight answer is given against, and the office "
        "named on it is the one that holds the times",
        "Whoever issued it can say where yours has got to from the reference - and the letter or "
        "the confirmation says who that is",
    ),
    ("be_in", "kit"): (
        "The order confirmation and the tracking page say whether it needs a signature, and they "
        "are what count on the day",
        "Whoever is delivering it puts the answer on the tracking page, and the confirmation says "
        "what happens if nobody is in",
    ),
    ("size", "kit"): (
        "The maker's page for each version gives the footprint and the clearance it needs, and the "
        "size chart is the part that settles which one fits",
        "The maker's page has the dimensions for each version, so the sheet and the page together "
        "settle which one fits your space",
    ),
    ("size", "appliance"): (
        "The maker's page for your model has the dimensions, and the plate on it tells you the "
        "model",
        "The plate on it gives the model number, and the maker's page has the size for that exact "
        "one",
    ),
    ("be_in", "paperwork"): (
        "The order confirmation or the tracking page says whether it needs a signature, and that "
        "is the one that counts on the day",
        "Whoever is delivering it puts the answer on the tracking page, and the confirmation says "
        "what happens if nobody is in",
    ),
    ("covered", "paperwork"): (
        "The policy or the reference says: what is covered, what the excess is, and what they ask "
        "you to tell them, all in the same document",
        "The terms that came with it settle it, and a phone call quoting the reference gets a yes "
        "or no from the people who apply them",
    ),
    ("send_back", "paperwork"): (
        "What it wants back, in what state and by when is on the page it came with, and the "
        "reference on it is how you check they have got it",
        "Whatever came with it sets out what to return and what to keep; the office named on the "
        "paper will confirm against the reference",
    ),
    ("get_out", "commitment"): (
        "The way out is written in the terms you were given: the notice period, whether it has to "
        "be in writing, and the date it renews on - and a written notice sent to the address on "
        "that paperwork is what they have to answer",
        "It comes down to the wording you signed: how much notice it wants, whether it renews "
        "itself, and who the notice has to go to. Notice in writing, sent to the address on the "
        "paperwork, is the version that gets an answer",
    ),
    ("exact", "appliance"): (
        "The plate on it - inside the door or on the back - gives the model and the part number, "
        "and that is what the maker's page is searched by",
        "The model and serial on the plate are what any parts page wants, and they make the answer "
        "exact rather than near",
    ),
    # A follow-up about a thing in the thread ("should i get someone in", "what can we try",
    # "is that connected") names no ask any carrier answers, and it is still the same thing. For a
    # thing with a plate or a sheet there is one first step that finds out everything else about
    # it, whatever the question was, so it is said rather than a hedge that names nothing.
    ("first_step", "kit"): (
        "The instruction sheet in the box and the maker's page for it between them cover what it "
        "needs and what to do when it will not - and the sheet is the one that came with your "
        "copy",
        "Start with what came with it: the sheet and the parts list say what it should do and "
        "what is missing, and the maker's page for that exact one says the rest",
    ),
    ("first_step", "appliance"): (
        "The plate on it - inside the door or on the back - gives the model and the serial, and the "
        "maker's page for that model has the fault codes, the parts and who services it",
        "Whatever the question is, the model number on the plate is the way in: the maker's page "
        "for it, or the engineer on the phone, will take that and work from there",
    ),
    # A fixture: the make and model are what get the part, and the fault it has is one of a short
    # list for that model. Nothing about it was ever on a sheet in a box.
    ("first_step", "fixture"): (
        "The part that goes on those is the cheap one - a washer, a cartridge, a seal or a valve, a "
        "few pounds rather than a new unit - and the make settles which: it is stamped on the body "
        "of it or under the cap, and the maker's page for that exact one has the part number and "
        "the video for the job",
        "Most of what goes wrong on one is a seal, a washer or a valve, and none of them is dear - "
        "take the make and model off it, on the body or under the handle, and the maker's page for "
        "that model shows the part and how the head comes off",
    ),
    ("tools", "fixture"): (
        "It is a spanner job rather than a kit: the maker's page for the model names the sizes, and "
        "a plumber's merchant has the washer or the cartridge",
        "The fittings come with the unit, and the maker's page for that model says which sizes you "
        "need for it",
    ),
    ("how_long", "fixture"): (
        "With the part in hand it is a short job - the maker's page for the model gives the time, "
        "and it is usually the inside of an hour for a washer or a cartridge",
        "The maker's page for that model says how long it takes, and most of that is the water off "
        "and the old part out",
    ),
}
KINDS = ((A_FIXTURE, "fixture"), (A_KIT, "kit"), (AN_APPLIANCE, "appliance"),
         (PAPERWORK, "paperwork"), (A_COMMITMENT, "commitment"))
ASKS = ((ASK_GET_OUT, "get_out"), (ASK_TOOLS, "tools"), (ASK_HOW_LONG, "how_long"),
        (ASK_SIZE, "size"), (ASK_BE_IN, "be_in"), (ASK_COVERED, "covered"),
        (ASK_SEND_BACK, "send_back"), (ASK_EXACT, "exact"))

# The honest half, in the few words STYLE.md asks for, with the thing named back so the person can
# see they were heard.
OPENER = (
    "I can't see {S} from here, sorry",
    "I haven't got {S} in front of me, sorry",
    "There is no way for me to check {S} from here, sorry",
)
# Getting out of something is read off the terms, so the honest half is about not having the small
# print rather than about not having the thing.
OPENER_TERMS = (
    "I can't see the terms on {S} from here, sorry",
    "I haven't got the small print for {S}, sorry",
    "I can't check what {S} says about getting out, sorry",
)
# And the question that narrows it, which is about their own copy rather than about the world.
QUESTION = {
    "tools": ("What does your sheet list?", "What came in the box with it?"),
    "how_long": ("What does it say on the sheet?", "Does the sheet give a time for the job?"),
    "size": ("What have you got to fit it in?", "What do the dimensions say on yours?"),
    "be_in": ("What does the tracking say?", "Did they give you a time slot?"),
    "covered": ("What does the paperwork say it covers?", "Do you have the reference to hand?"),
    "send_back": ("What does it ask you to send?", "Have you got the reference on it?"),
    "get_out": ("How much notice does it ask for?", "Do you still have the terms it came with?"),
    "exact": ("What is the model number on it?", "Can you read the plate on it?"),
    "first_step": ("What does the plate say on yours?", "Have you got the sheet that came with it?"),
}


# Where the carrier names one kind of thing and not the other, the question is the kind's own.
# Only the pairs that would otherwise be asked about a plate that is not there, or a box that
# nothing came in.
QUESTION_KIND = {
    ("first_step", "kit"): ("Have you got the sheet that came with it?",
                            "Is the sheet it came with still about?"),
    ("tools", "appliance"): ("What does the plate say your model is?",
                             "Do the fixings come with it or are they extra?"),
    ("first_step", "fixture"): ("Do you know the make of it?",
                                 "Can you see the make on it?"),
    ("tools", "fixture"): ("Do you know the make of it?",
                            "Is the make on it anywhere?"),
}


# A carrier is only named back when the line says the thing is **theirs to look at**. "How long does a
# passport take", "how long does a refund take" and "what size boiler do i need" are general questions
# about the world: there is no sheet, no reference and no copy in their hand, so "what does it say on
# the sheet" is unanswerable and "where yours has got to" says they have one. Measured against
# @cobalt-donkey's review of #13635: every general-time ask was given an invented reference.
# The determiner in front of the thing is the signal, not a possessive anywhere in the line: "the
# policy" and "my passport" are theirs, "a passport" and a bare "shed" are not.
THEIR_OWN = frozenset(("my", "our", "your", "his", "her", "their", "the", "this", "that",
                       "these", "those"))
A_RECEIPT = re.compile(
    r"\b(?:got|bought|ordered|received|arrived|came|delivered|picked\s+up|sent\s+(?:me|us)|"
    r"turned\s+up|was\s+delivered|was\s+sent|it's\s+here|its\s+here|came\s+with)\b")
# A job you can only do to a thing you already have in the house: "what tools do i need to put the
# wardrobe up" is about the flat-pack in the hall, not about wardrobes in general.
A_JOB_ON_IT = re.compile(
    r"\bput(?:ting)?\s+(?:\w+\s+){0,4}(?:up|together)\b|\bassembl\w*|\binstall\w*|"
    r"\bbuild\w*|\berecting\b|\bfitting\b")
# The asks that only make sense about a copy they already hold: "do i need to be in for it", "do i
# need to send it back", "which part do i need". Nobody says these about a passport they have not
# applied for.
THEIR_COPY_ASKS = frozenset(("be_in", "send_back", "exact"))


def _they_have_it(said, ask, determiner):
    """True when the line says the thing is theirs to look at, or the ask is about their own copy."""
    if ask in THEIR_COPY_ASKS:
        return True
    if determiner in THEIR_OWN:
        return True
    return bool(A_RECEIPT.search(said) or A_JOB_ON_IT.search(said))


def _said(text):
    return " ".join(str(text or "").lower().split())


_DETERMINER = re.compile(
    r"\b(my|the|our|your|this|that|a|an|his|her|their)\s+$")


def _the_thing_named(said):
    """(how the person said the thing, its kind) or None.

    Scans for a whole word from one of the kind lists rather than for a noun phrase, so a line
    with no such thing in it gets nothing at all. The longest match wins, and the determiner in
    front of it is kept so it reads back as "the shed" or "a van" rather than as "shed".
    """
    best = None
    for pattern, kind in KINDS:
        for match in pattern.finditer(said):
            word = match.group(0)
            if best is None or len(word) > len(best[0]):
                best = (word, kind, match.start())
    if best is not None:
        # Paper beats the subject it is about: "i got a letter about my council tax" then "do i
        # need to send it back" is a question about the letter, and its own words ("council tax",
        # the longer match) put the answer on the bill rather than on the paper in their hand.
        # Only a paper named in the same line displaces it, so no other line changes hands.
        # The first paper named, not the longest: "a letter about my council tax" names the letter
        # before the subject it is about, and "council tax" is a paper word too (PAPERWORK), so
        # the longest match would put the reply back on the bill.
        papers = list(PAPERWORK.finditer(said))
        if papers:
            word = papers[0].group(0)
            best = (word, "paperwork", papers[0].start())
    if best is None:
        return None
    word, kind, start = best
    before = said[:start]
    said_as = "the %s" % word
    found = _DETERMINER.search(before)
    determiner = found.group(1) if found else None
    if found:
        # "my" reads back as "your" and "a" as "a": the reply is about the person's own copy of the
        # thing, never about a generic one.
        said_as = "%s %s" % ({"my": "your", "our": "your"}.get(found.group(1), found.group(1)),
                             word)
    return said_as, kind, determiner


def _the_thing_in_the_thread(memory):
    """The thing the last few lines were about, when this line names none of its own.

    "we ordered a shed, it was meant to come on the 14th" / "do i need to be in for it": the
    second line has no thing in it, and the answer is still on the shed's confirmation. Only the
    person's own lines are read, the nearest first, and only for a thing of a known kind - a line
    about a delivery two turns back is not a licence to answer a different question with a label.
    """
    turns = (memory or {}).get("turns") or []
    seen = 0
    for turn in reversed(turns):
        said = _said(turn.get("user") if isinstance(turn, dict) else "")
        if not said:
            continue
        found = _the_thing_named(said)
        if found:
            word, kind = found[0], found[1]
            word = re.sub(r"^(?:my|our|your|his|her|their|the|a|an)\s+", "", word)
            # A thing the thread named is theirs by definition, so it carries the determiner that
            # says so.
            return "the " + word, kind, "the"
        seen += 1
        if seen >= 2:
            # The line this one leans on, and one more back at most: further than that the subject
            # is a different one, and a carrier named for it would be an invention.
            return None
    return None


def on_the_thing(clean, memory=None, understood=None):
    """A partial answer that names where the rest lives, or None to keep the hedge."""
    said = _said(clean)
    if (not said or NOT_HERE.search(said) or NOT_ABOUT_THE_CONVERSATION.search(said)
            or NOT_A_LOOKUP_BUT_A_REQUEST.search(said) or A_JUDGEMENT_ASK.search(said) or A_PLAN_ASK.search(said)
            or A_COOKING_LINE.search(said) or A_READING_JUST_GIVEN.search(said)
            or A_WHY_ASK.search(said) or A_METHOD_OR_ADVICE_ASK.search(said) or A_DECISION_ABOUT_GOING_ON.search(said)
            or A_NOW_OR_NEVER_ASK.search(said)
            or NOT_ABOUT_THE_VISIT.search(said)):
        return None
    thing = _the_thing_named(said)
    from_the_thread = thing is None
    thing = thing or _the_thing_in_the_thread(memory)
    if not thing:
        return None
    word, kind, determiner = thing
    ask = None
    for pattern, name in ASKS:
        if pattern.search(said):
            ask = name
            break
    if ask is None:
        # A line that names a thing of its own and an ask no carrier settles ("is the shed worth
        # the money") keeps the hedge: the ask is a real question about that thing, and the plate
        # does not answer it. A follow-up that names no thing of its own is the same question
        # about the thing in the thread, so its one first step can be said.
        if not from_the_thread:
            return None
        # How a thing is used or kept is not written on it, so the one first step stays unsaid.
        if NOT_ON_THE_PLATE.search(said):
            return None
        ask = "first_step"
    # Nobody's copy, no carrier: a general question about a passport, a refund or a boiler is the
    # world's, and the hedge says so honestly rather than asking what the invented sheet says.
    if not from_the_thread and not _they_have_it(said, ask, determiner):
        return None
    pool = CARRIERS.get((ask, kind))
    if not pool:
        return None
    opener_pool = OPENER_TERMS if ask == "get_out" else OPENER
    opener = pick(opener_pool, memory or {}, said).format(S=word)
    carrier = pick(pool, memory or {}, said)
    # The question is about the carrier, so it is chosen by the kind as well: "what does the plate
    # say on yours" is an appliance's question, and a dripping tap read as a kit was asked it -
    # a tap has no plate, and the sheet it came with is the thing in its own line.
    question = pick(QUESTION_KIND.get((ask, kind)) or QUESTION[ask], memory or {}, said)
    return "%s. %s. %s" % (opener, carrier, question)