"""What the fallback can still say when no pool holds the answer.

A search tip on its own is not a reply: it hands the whole question back and tells the person to
go somewhere else. What a friend does with the same gap is say the part that is true without the
answer - what settles this kind of question, and what to have in front of you - and only then say
where the rest lives. The kinds here are kinds of question, not wordings: what is open today, what
a machine of theirs is doing, what the rules say for their dates, what a thing costs, what only
another person can answer, what happened, what people usually give. None of them needs the answer
to be useful, and none of them invents one.

Two entry points, both called from the fallback's hedge slot and nowhere else, so every line that
some other module can answer keeps its own reply:

    the_lead_and_the_route(clean, memory)      what is known about this kind, then the pointer
    an_ask_with_no_subject(clean, memory)      "whats the first step": the usual first moves

`POINTER_HEDGE` says which replies may be replaced at all: a reply that only points somewhere. A
reply that weighs a decision, names where money advice comes from, or hands a body to a doctor is
an answer of its own and is left alone.
"""

import re

from .fallback_data import HEDGE_POOL  # noqa: F401 - kept for the module's imports to match


def _choose(options, memory, clean):
    """The pool's own chooser, imported when it is called.

    `fallback_chain` imports from `fallback`, so importing it at the top of this module would be a
    cycle: by the time a line reaches here both are loaded.
    """
    from .fallback_chain import _choose as pick
    return pick(options, memory, clean)


LIVE_TODAY = re.compile(
    r"(?<![a-z])(?:open|opens|opening|close|closes|closing|shut|hours|opening times|till|"
    r"busy|busiest|queue|traffic|parking|stock|in stock|sold out|available|delivery|"
    r"today|tonight|tomorrow|this weekend|sunday|saturday)(?![a-z])")
LIVE_ASK = re.compile(
    r"(?<![a-z])(?:what time|when|is it|are they|is the|is my|do they|does it|can i|will|"
    r"how busy|how long is the wait|still)(?![a-z])")
# The words here are the ones a thing is asked about by name, not every word that could appear in
# a line about one: "is there anything i should watch for" was read as a smartwatch, so a bare
# "watch", "app", "update" or "settings" is not enough on its own.
A_MACHINE_OF_THEIRS = re.compile(
    r"(?<![a-z])(?:model|serial|make and model|fault code|error code|manual|"
    r"spare part|part number|firmware|warranty|"
    r"(?:the|my|this|that|an) (?:app|settings|instructions)|reset (?:it|the|my)|"
    r"(?:software|firmware|system) update|boiler|washer|washing machine|dishwasher|"
    r"tumble dryer|fridge|freezer|oven|hob|kettle|vacuum|hoover|laptop|tablet|printer|"
    r"router|thermostat|radiator|heat pump|smart ?watch|fitbit|tracker|console|"
    r"my (?:phone|tv|telly|car|van|bike|scooter|watch|camera|alarm))(?!['a-z])")
# "How many weeks should i train for" is a question about a stretch of time with a deadline, and
# the honest answer is the shape of a build-up rather than a number: it depends on where they are
# now and how many days a week they can give it. Nothing about the subject is invented - the shape
# of a build-up is the same whether it is a 10k, a language or an exam.
GET_READY_FOR = re.compile(
    r"(?<![a-z])(?:how\s+(?:long|many\s+weeks|many\s+days|much\s+time)\s+(?:should|do|would|"
    r"will|can)\s+(?:i|we)\s+(?:train|practise|practice|study|revise|prepare|get\s+ready)"
    r"|how\s+long\s+(?:before|until)\s+(?:i|we)\s+(?:need|should|have)\s+to\s+"
    r"(?:train|be\s+ready|get\s+ready|start))(?!['a-z])")
GET_READY_LEADS = (
    "The number comes from two things: where you can get to now, and how many days a week you can "
    "give it. A build-up that climbs and then eases off beats a heroic first week every time.",
    "It depends on your starting point and on the time you can actually give it, not on a rule - "
    "and the shape is the same for most things: steady most days, one hard session, and rest.",
)
GET_READY_ROUTES = (
    "Tell me what you can do now and how many days a week you have, and I will say what I would "
    "aim at; the training app or the course's own plan has the standard build-up for your dates.",
    "Give me those two and I will say where I would start; whoever runs the event or the exam "
    "publishes the usual build-up, and that is worth comparing with.",
)
# A word that names a rule, not a word that names a thing a rule may be about: "deposit" and
# "refund" were in this list, so "what happens to the deposit" (a landlord and a council) was
# answered with a line about the exact wording and their own dates instead of the pool's own
# "Citizens Advice covers this free". The kind is asked about a rule - a policy, a law, an
# entitlement, a notice period - and those all say so.
RULES_FOR_THEIR_CASE = re.compile(
    r"(?<![a-z])(?:allowed|entitled|entitlement|qualify|eligible|legal|law|rules|regulation|"
    r"statutory|allowance|benefit|benefits|tax|taxed|taxable|vat|licence|license|permit|"
    r"visa|tenancy|contract|clause|notice period|policy|terms|insurance|"
    r"pension|ni|national insurance|council tax|deadline)(?![a-z])")
HOW_MUCH_TO_PUT_IN = re.compile(
    r"how much (?:should|shall|do|can|would) i (?:be )?(?:put|putting|pay|paying|save|saving|"
    r"contribute|contributing|invest|investing|stick|stick in|set aside)\b")
PUT_IN_LEADS = (
    "Start at whatever the other side adds to: below the employer's match you are leaving their "
    "money on the table, and that is the one part with no argument against it.",
    "The order is the same for most people: the matched amount first, then whatever you can leave "
    "alone until you retire, and only then anything else.",
)
PUT_IN_ROUTES = (
    "The figure that suits you comes from what the scheme pays in and what you can do without "
    "now, and their calculator or the free guidance service will work it through with you.",
    "Take the percentage your scheme's own page shows for the match, then look at what your "
    "payslip leaves - that pair gives you the number.",
)
A_PRICE_THEY_WILL_PAY = re.compile(
    r"(?<![a-z])(?:how much (?:is|does|do|would|will|are|should)|what does .{1,30} cost|"
    r"the cost of|price of|prices for|how expensive|cheapest|cheapest|going rate|quote|"
    r"charge|charges|fee|fees|fare|fares|how much (?:will|would) it cost)(?![a-z])")
# "What do i take" is answerable without knowing the trip: the list that holds for everybody is
# short, and the only part worth looking up is what the place will not let through the door.
WHAT_TO_TAKE = re.compile(
    r"(?<![a-z])(?:what (?:do|should) i (?:take|bring|pack)|what to (?:take|bring|pack)|"
    r"what should i put in my (?:bag|case|rucksack|pack)|what do i need to (?:take|bring|pack)|"
    r"what else (?:do|should) i (?:need to )?(?:take|bring|pack))(?![a-z])")
WHAT_TO_TAKE_LEADS = (
    "Take less than you think, and the three things most people forget: a charger, a bag for "
    "anything wet, and your own water.",
    "The list that works is short: anything you would not want to buy twice, a layer for the cold "
    "end of the day, and the paperwork if there is any.",
)
WHAT_TO_TAKE_ROUTES = (
    "The operator's or the venue's page says what is not allowed in through the door, and that is "
    "the only part worth checking before you go.",
    "Tell me where you are going and for how long, and I will cut that list down to what you need.",
)

# Teaching somebody something has a shape that does not depend on the skill: the smallest piece
# they can already do, one step on, and stopping while it is still going well.
HOW_TO_TEACH = re.compile(
    r"(?<![a-z])(?:how (?:do|can|should) i (?:teach|help|show|explain)|"
    r"how do i get (?:them|him|her|my \w+) to|how can i help (?:out|at home|them|him|her))(?![a-z])")
HOW_TO_TEACH_LEADS = (
    "Break it into the smallest piece they can already do and add one step: ten minutes that "
    "ends while it is still going well is worth more than an hour that ends badly.",
    "Show it once, let them do it badly without being corrected, then give them one thing to "
    "change next time. That order is what makes it stay.",
)
HOW_TO_TEACH_ROUTES = (
    "Tell me what they can already do and where it goes wrong, and I will say what the next step "
    "is.",
    "Say how old they are and what they can already manage, and I will make it concrete.",
)

# "Is it ok to ..." is not a rule to look up: it turns on the conditions where they are and on the
# person doing it, and saying so is more use than a pointer. Where a body is involved the answer
# comes from somebody who can see them, and that is said plainly.
# Whether it is fine to leave somebody, take somebody, or let them do something turns on the
# person and the arrangements, not on the weather: naming those is more use than a pointer, and no
# rule is invented about what age is old enough.
LEAVING_SOMEONE = re.compile(
    r"(?<![a-z])(?:is it ok(?:ay)? to (?:leave|take|send|let) (?:him|her|them|my \w+)|"
    r"is it fine to (?:leave|take|send|let) (?:him|her|them)|can i (?:leave|let) (?:him|her|them)|"
    r"should i let (?:him|her|them))(?![a-z])")
LEAVING_SOMEONE_LEADS = (
    "That turns on three things: how old they are, how long it would be, and whether they could "
    "reach you - and what they would do if they could not.",
    "There is no general yes or no to that: it comes down to how old they are, how long for, and "
    "who they could get hold of.",
)
LEAVING_SOMEONE_ROUTES = (
    "Tell me the three and I will say how it looks rather than what the rule is.",
    "Give me those and I will tell you what I would check before deciding.",
)

IS_IT_OK = re.compile(
    r"(?<![a-z])(?:is it ok(?:ay)? to|is it alright to|is it fine to|would it be ok(?:ay)? to|"
    r"am i ok to|are we ok to|is it safe to)(?![a-z])")
IS_IT_OK_LEADS = (
    "There is no general yes or no to that: it hangs on the details in front of you - how long it "
    "has been, how warm it is, and who it affects - and none of those reach me from here.",
    "Whether that is fine turns on the specifics rather than on a rule: how long it has been, what "
    "the conditions are, and who else it touches.",
)
# The same ask with no food and no body in it - "is it ok to park here" - where "how long it has
# been, how warm it is" is a sentence about nothing.
IS_IT_OK_PLAIN_LEADS = (
    "There is no rule of thumb that answers that one: it turns on your own circumstances more than "
    "on the question, and I cannot see yours from here.",
    "That one is decided case by case rather than by a general rule, and the part that decides it "
    "is the part only you can see.",
)
IS_IT_OK_ROUTES = (
    "Tell me those three and I will say how it looks; where a body is involved, a pharmacist or "
    "111 is quicker than me.",
    "Give me the details and I will tell you which of them decides it.",
)
# The same answer where no body is involved: "is it safe to eat the rest of them" (tomatoes with
# a black patch) got "a pharmacist or 111 is quicker than me", which is the wrong person to send
# someone about a tomato. The body words decide which route is said, not which kind it is.
IS_IT_OK_PLAIN_ROUTES = (
    "Tell me the detail that matters most in your case and I will say how it looks.",
    "Give me that detail and I will tell you what I would check first.",
)
# A body, a medicine or a place people swim: the yes-or-no that really does end at a pharmacist
# or 111.
A_BODY_IN_IT = re.compile(
    r"(?<![a-z])(?:swim|swimming|sea|pool|river|lake|beach|sun|sunburn|heat|hot tub|"
    r"paint|fumes|bleach|mould|mold|asbestos|gas|electrics|electric|wiring|wires|plug|socket|"
    r"ladder|roof|scaffold|knife|fire|barbecue|bbq|baby|pregnan\w*|medicines?|tablets?|dose|"
    r"antibiotics?|symptom|fever|sick|vomit\w*|bleed\w*|bruise\w*|burn|wound|rash|swelling|"
    r"pain|hurt|give|giving|given|feed|feeding|fed|"
    r"knee|knees|back|shoulder|shoulders|ankle|ankles|hip|hips|wrist|wrists|elbow|elbows|"
    r"neck|foot|feet|arm|arms|leg|legs|hand|hands|head|stomach|chest|ear|ears|eye|eyes|"
    r"tooth|teeth|skin|heel|heels|joint|joints|muscle|muscles)(?![a-z])")
# Something in the kitchen: the answer is about how long and how warm, and a pharmacist is only for
# when somebody has eaten it and is ill.
A_FOOD_IN_IT = re.compile(
    r"(?<![a-z])(?:food|eat|eating|eaten|raw|cook|cooked|cooking|chicken|meat|beef|pork|lamb|"
    r"fish|egg|eggs|dairy|milk|cheese|rice|pasta|leftovers?|reheat|defrost|fridge|freezer|"
    r"use by|best before|drink|drinking|water|soup|sauce|mayo|mayonnaise|salad|bread|fruit|"
    r"tomato(?:es)?|veg|vegetables?)(?![a-z])")
IS_IT_OK_FOOD_ROUTES = (
    "Tell me how long it has been and how warm it has been kept, and I will say how it looks; if "
    "anyone has eaten it and is unwell, 111 is quicker than me.",
    "Give me those two - how long, and how warm - and I will tell you which of them decides it.",
)
WATCH_OUT = re.compile(
    r"(?<![a-z])(?:what should i watch (?:out )?for|anything i should (?:watch|look out) for|"
    r"what should i look out for|what are the risks|what could go wrong|"
    r"is there anything to watch|what do i need to watch)(?![a-z])")
A_USUAL_AMOUNT = re.compile(
    r"(?<![a-z])(?:how much (?:cash|money)?\s*(?:do|should|would) (?:you|i|people|we) "
    r"(?:put|give|spend|tip|leave|pay)|how much (?:cash|money) (?:in|for|on)|"
    r"what do people usually (?:give|spend|pay)|what.s (?:a )?normal (?:to give|to spend|amount)|"
    r"how much is normal|what would you (?:give|put in)|is \d+ (?:too much|enough)|"
    r"how much do you (?:give|tip))(?![a-z])")
NEWS_RESULT = re.compile(
    r"(?<![a-z])(?:did it (?:go through|pass|happen|work)|what happened|who won|was there|"
    r"did they (?:win|vote|agree|announce)|has it been (?:announced|decided)|any news|"
    r"did (?:[a-z]+ ){0,4}(?:get |go |went )?(?:called off|cancelled|approved|decided|"
    r"accepted|agreed|through|ahead|passed|signed off)|is it still (?:on|going ahead)|"
    r"what came of|how did it (?:go|turn out)|"
    r"what was the result|result of the (?:vote|election|match|game)|did it get "
    r"(?:approved|passed|through))(?![a-z])")
SOMEONE_ELSES_OWN = re.compile(
    r"(?<![a-z])(?:does (?:he|she|they|my \w+) (?:like|want|prefer|think|plan|need)|"
    r"is (?:he|she|they) (?:happy|ok|okay|up for|coming|free)|what does (?:he|she|they) "
    r"(?:do|think|want|like)|what is (?:he|she|they) into|how does (?:he|she|they) feel)(?![a-z])")
# The lead is what the bot can say without the answer: what decides it, and what to have ready. The
# route is where the answer lives. Both are true of the kind, so nothing here is invented about the
# subject, and neither half repeats the other.
LIVE_TODAY_LEADS = (
    "That changes by the day and by the place, so anything I said would be yesterday's - the day "
    "and the place decide it.",
    "This is one of the ones that turns over daily, and I cannot see today's from here.",
)
LIVE_TODAY_ROUTES = (
    "The place's own page has today's, one phone call confirms it, and a map listing carries the "
    "hours underneath the address.",
    "Their own page or its map listing is the only place that is right today; ring them if it is "
    "close to closing time.",
)
A_MACHINE_LEADS = (
    "The model number and the exact code on the display are what settle these - the number is on "
    "a sticker on the machine, or in the settings screen under About.",
    "For a machine, the maker's own sheet is written for your exact model: the sticker on the "
    "back or inside the door has the number, and the code on the display is the other half.",
)
A_MACHINE_ROUTES = (
    "Put the model number into the maker's own support page and it gives the manual and what that "
    "code means.",
    "The maker's support page with that model has the manual, the fault codes and the reset "
    "sequence.",
)
RULES_LEADS = (
    "Two things decide these: the exact wording of the rule, and your own dates. A general answer "
    "from me could be right about the rule and wrong about you.",
    "These turn on the exact wording and on your own dates rather than on the rule itself, and I "
    "cannot see either from here.",
)
RULES_ROUTES = (
    "Whoever runs it - the office named on the letter, the department, or the helpline that owns "
    "the rule (GOV.UK for most of these) - is the one that will confirm your own case, and a free "
    "advice line will read it with you.",
    "Ask whoever decided it to confirm it for your dates, and keep the reply: a free advice line "
    "will read it with you.",
)
# The same answer when no document was mentioned. "My boss has changed my shifts without asking /
# is that even allowed" was told to "take the exact name and reference number off the letter", and
# there is no letter - a rule about shifts lives in a contract, a rota and a manager, or in none of
# them. Only a line that names a document gets the document route.
DOCUMENT_NAMED = re.compile(
    r"(?<![a-z])(?:letter|paperwork|papers?|email|e-mail|form|contract|policy|terms|bill|"
    r"invoice|statement|receipt|quote|quotation|agreement|tenancy|p45|p60)(?![a-z])")
RULES_PLAIN_ROUTES = (
    "Whoever runs it - the office, the department, or the helpline that owns the rule (GOV.UK for "
    "most of these) - is the one that will confirm your own case, and a free advice line will "
    "read it with you.",
    "Ask whoever decided it, in writing, to confirm it for your dates, and keep the reply: a free "
    "advice line will read it with you.",
)
A_PRICE_LEADS = (
    "Prices move week to week and shop to shop, so a number from me would be out of date the "
    "moment I said it.",
    "The price depends on where you buy and when, which is not something I can see.",
)
A_PRICE_ROUTES = (
    "The shop's own page has today's price, and a comparison site shows what the others are "
    "charging this week.",
    "Look at two or three sellers' own pages - the spread is usually bigger than people expect.",
)
SOMEONE_ELSES_LEADS = (
    "Only they can say that - it is their own head, and I have nothing on it from here.",
    "That one lives with them rather than with me: no one else can answer it for them.",
)
SOMEONE_ELSES_ROUTES = (
    "Ask them straight - a plain question gets a straighter answer than working it out from the "
    "outside.",
    "Say it to them in one line and let them fill in the rest.",
)
# An amount people usually give is not a fact about the world but a range decided by the occasion
# and the relationship, and that much can be said without knowing either.
USUAL_AMOUNT_LEADS = (
    "There is no right number for this: the occasion and how close you are decide it, and people "
    "usually settle on a range they can repeat for everyone in the same circle so nobody is "
    "singled out.",
    "What people give is a range rather than a figure - what the occasion calls for, what you "
    "would be comfortable receiving, and what the others in the same group are doing.",
)
# "What should i watch out for" is a request for the risks, and the risks of most things are the
# same handful: the total cost, who is responsible when two people are involved, and the deadline.
WATCH_OUT_LEADS = (
    "The things that catch people out are usually the same few: the total cost rather than the "
    "headline price, who is responsible when two people are involved, and the deadline nobody "
    "mentions until it has passed.",
    "What goes wrong is rarely the obvious part - it is the small print, the thing that was "
    "somebody else's job, and the timing.",
)
# "is there anything i should watch for" after a knee that grinds was answered with the total
# cost, who is responsible when two people are involved and a deadline - three things about
# paperwork on a line about a body. The three for a body are the ones a physio would ask about,
# and they are the whole of the answer whatever the joint is.
WATCH_OUT_BODY_LEADS = (
    "Three things, and they are the same for most joints: pain that carries on after you stop, "
    "swelling that comes up over the next day, and the joint locking or giving way under you.",
    "What to watch for is not the noise - it is pain that settles in, a swell you can see, and "
    "anything that stops you putting weight on it or straightening it.",
)
WATCH_OUT_BODY_ROUTES = (
    "Any of those and it is worth a physio or your GP rather than waiting it out; none of them "
    "and it is usually just the joint being noisy.",
    "If any of the three turns up, get it looked at rather than resting it for weeks; if none "
    "does, keep moving it.",
)
WATCH_OUT_ROUTES = (
    "Say what you are about to do and I will go through those three against it.",
    "Tell me the situation and I will name the one I would check first.",
)
USUAL_AMOUNT_ROUTES = (
    "Ask one person who is going to the same thing what they are giving, and match it; that is "
    "how most of these are settled.",
    "If it is a gift, a card and something small and chosen beats a bigger amount given flatly - "
    "tell me who it is for and I will help you pick.",
)
NEWS_LEADS = (
    "I have no feed from here, so I cannot see what happened - the result is the one thing I would "
    "be guessing at.",
    "That is happening where I cannot see it: no papers, no bulletins, nothing that reaches me.",
)
NEWS_ROUTES = (
    "Whoever ran it will have the result - the organiser, the office that sent it, or the news "
    "site for it. Tell me what it says and I will help you read it.",
    "The body's own page or a news report has the outcome; say what it says and we can work out "
    "what it means for you.",
)
# A reply that only points somewhere is the one thing this replaces: what the bot can say about the
# kind of question comes first, and the pointer stays only where it is the end of a real answer.
POINTER_HEDGE = re.compile(
    r"(?i)(?:a quick search|search online|searching for it|a search should|better sources|"
    r"look it up|look that up|a map app|a directory|comparison site|its own page has|"
    r"their own page has|the seller's site|official site|the official finder|"
    r"i can't look (?:up|this)|no directory here|no maps here)")
# Asking to decide is not asking to look up: "should i just let him" wants the two sides held up,
# and the decision pools answer that already.
ASKS_TO_DECIDE = re.compile(
    r"^\s*(?:so |and |ok |okay |but |well )*(?:should|shall|ought) i(?![a-z])|"
    r"(?<![a-z])(?:do i bother|do i go for|is it worth|worth (?:it|fixing|replacing)|"
    r"better to|which (?:one|is better)|what would you do)(?![a-z])")


# A short follow-up says what kind of help it wants and nothing about the subject - "whats the
# first step", "what should i have", "how should i get ready" - so the search hedge had nothing to
# go on and sent the person off to look it up. The subject is in the chat; what is missing here is
# the kind of help, and that can be given without the subject: the usual first moves for this sort
# of ask, true of any subject, with one question to put it on their own thing.
ASK_ONLY_WORDS = frozenset("""
a an the i we you me us my our your it its that this these those there here what whats how why
when who which should shall can could would will do does did have has had got get need needs
want wants any some more most all one ones two first next last step steps start starting go goes
going way ways best good right proper thing things bit part parts now then again still just
really very quite also too so and but if or about for with to in on at from by as up down out off
over back through
eat drink cook make take bring put keep leave buy book phone ring call ask say tell show give
plan save spend pay wear fix choose pick sort try look think know find use work ready prepared
missing miss anything else needed necessary am is are was were be been being prepare preparing
prepped prep helpful use useful much long far soon expect expecting happen happens day night
route routes path paths into in career change switch started starting begun beginning
people person someone somebody anyone everyone somebody's others group colleagues
""".split())


def _the_words_of(said):
    """The words of a line, lowercased, with the punctuation and the apostrophes dropped.

    "what's the route" is "whats the route" once the apostrophe goes, and a chat line rarely
    carries one anyway: without this the same line was read one way with the apostrophe and the
    other way without it.
    """
    return [w.replace("'", "") for w in re.findall(r"[a-z']+", str(said or "").lower())]


def _says_nothing_of_its_own(clean):
    """True when every word of the line is an ask or a filler: a follow-up with no subject."""
    words = _the_words_of(clean)
    return bool(words) and all(w in ASK_ONLY_WORDS for w in words)


WHERE_TO_START_ASKS = re.compile(
    r"(?<![a-z])(?:first step|first thing|next step|next thing|where (?:do|would|should) i "
    r"(?:start|begin)|how do i start|how do i begin|what should i do first|what do i do first|"
    r"where to start|what first|what now|what next|and then what)(?![a-z])")
WHAT_YOU_NEED_ASKS = re.compile(
    r"(?<![a-z])(?:what should i (?:have|get|buy|bring|take)|what do i need|what will i need|"
    r"do i need anything|what else do i need|what do i have to get|am i missing anything)(?![a-z])")
ROUTE_IN_ASKS = re.compile(
    r"(?<![a-z])(?:what(?:.s|s)? the route|what are the routes|which route|what route|"
    r"what(?:.s|s)? the path|how do (?:you|people|i) (?:get|go) into|how do i get in|"
    r"what(?:.s|s)? the way in|how do you break into|how do people get started|"
    r"what(?:.s|s)? the way into|how do i start out)(?![a-z])")
FIRST_ATTEMPT_ASKS = re.compile(
    r"(?<![a-z])(?:what should (?:the|my) first .{0,24} (?:look like|be like|be)|"
    r"what does (?:the|my) first .{0,24} look like|how should (?:the|my) first .{0,24} go|"
    r"what should i expect from (?:the|my) first|how do i start (?:it|off)|"
    r"what.s a good first)(?![a-z])")
GET_READY_ASKS = re.compile(
    r"(?<![a-z])(?:get ready|getting ready|prepare|preparing|be ready|get set|brush up|"
    r"what should i expect|what happens on the day)(?![a-z])")

# The usual first moves, said about no subject in particular so that they hold whatever the chat
# is on, and a question narrow enough that the next turn can be specific.
WHERE_TO_START_LINES = (
    "Start with what you want to end up with and what you cannot go past - money, time, or "
    "somebody else's say-so - then take the smallest action that moves it. Where are you with it "
    "now?",
    "Put the end result into a sentence, then the one thing that has to happen before any of the "
    "rest can. What is stopping that one thing?",
)
# Nothing here assumes the thing is carried or bought: "i need to renew my passport" then "what
# should i have ready" was answered "something to carry it, something to clean up after", which is
# a bag rather than a passport. The list comes from whoever set the rule, and the boring half is
# the same for a renewal, a trip or a first day.
WHAT_YOU_NEED_LINES = (
    "The list is theirs rather than mine: whoever you are dealing with sets it and publishes it, "
    "and it is short. Read it once and tell me what is on it - it is the part people get stuck on "
    "that is worth checking before you go.",
    "Start from what they ask for in writing rather than from memory, and go down it a line at a "
    "time. What is on their list?",
)
# The way into a job or a trade is the same handful of doors whatever the trade is, so the doors
# can be named even when the trade has not been said yet - and the last line is the one that
# actually decides it for most people.
# The first go at anything should be shorter and easier than the person expects: the day after is
# the only feedback that counts, and a first session that leaves something in the tank gets repeated.
FIRST_ATTEMPT_LINES = (
    "Shorter and easier than you think: fifteen or twenty minutes, stop while you could still do "
    "more, and judge it by how you feel the next day rather than how you feel at the end.",
    "The first one is a test of the plan rather than the thing itself - small enough that you "
    "would do it again, and written down so the second one is easy to repeat. What are you "
    "starting with?",
)
ROUTE_IN_LINES = (
    "There are usually three ways in: the qualification, a paid trainee or apprenticeship place "
    "where you earn while you learn, and a side door through a related job. Which of those fits "
    "depends on whether you can afford to study full time.",
    "The doors are the same most places: the course, the paid training place, and starting lower "
    "down in the same trade and moving up. The one to take depends on what you can afford to do "
    "and what is hiring near you - want me to go through them?",
)
GET_READY_LINES = (
    "Split it in two: what will be wanted from you - what gets asked, what to bring - and the "
    "practical half like what you wear and how you get there, which is the half people leave "
    "until the morning. Which half worries you?",
    "Know the order things happen in and what you need with you, then sort the clothes and the "
    "journey the night before rather than on the day. What is the part you are unsure about?",
)


def _an_ask_with_no_subject(clean, memory=None):
    """The usual first moves for the kind of help asked for, or "" when the ask is not one."""
    line = " ".join(str(clean or "").split())
    if not line or not _says_nothing_of_its_own(line):
        return ""
    if WHERE_TO_START_ASKS.search(line):
        return _choose(WHERE_TO_START_LINES, memory, clean)
    if WHAT_YOU_NEED_ASKS.search(line):
        return _choose(WHAT_YOU_NEED_LINES, memory, clean)
    if ROUTE_IN_ASKS.search(line):
        return _choose(ROUTE_IN_LINES, memory, clean)
    if GET_READY_ASKS.search(line):
        return _choose(GET_READY_LINES, memory, clean)
    return ""


# A reply that names somebody to ask, or a place with the answer in it, is not a bare search tip:
# it has already said where the rest lives. The pools for a place, a trade and a professional all
# read that way ("their site has it in writing, and Citizens Advice is free if the page is a
# maze"), and replacing one with a lead and a route of my own is what lost main's council-and-
# Citizens-Advice line for "what happens to the deposit". Only the bare "go and search" is
# replaced.
NAMES_WHERE_TO_ASK = re.compile(
    r"(?<![a-z])(?:citizens advice|acas|ombudsman|council|gp|doctor|surgery|pharmacist|"
    r"dentist|vet|nurse|111|999|bank|broker|adviser|advisor|solicitor|union rep|"
    r"map app|their site|its site|the site|their page|the page|their own page|"
    r"gov\.uk|official site|the label|the packet|the box|the shop|the garage|a dealer|"
    r"the library|the post office|the school|the landlord|the office|the helpline|"
    r"the company|the operator|the insurer|the seller|the manufacturer|your employer)(?![a-z])",
    re.I)


def _the_whole_exchange(line, memory):
    """The line and what was said before it, so a follow-up keeps the subject of the turn before.

    "is there anything i should watch for" after a knee that grinds has no body in it at all, and
    the three things to watch for on a body are a different three from the ones on a contract.
    """
    said = [line]
    for turn in ((memory or {}).get("turns") or [])[-3:]:
        if isinstance(turn, dict):
            said.append(str(turn.get("user") or ""))
    return " ".join(said)


def _the_routes_hold_this(line):
    """True when `routes.py` names a page or a rule for this line, so this file must stand down."""
    try:
        from .routes import options
    except Exception:  # noqa: BLE001 - a reader that cannot ask claims nothing
        return False
    try:
        return bool(options(line))
    except Exception:  # noqa: BLE001
        return False


def _the_ok_lead(line):
    """The lead for a yes-or-no ask: about food and bodies only where one of them is in the line."""
    route = _the_ok_route(line)
    return IS_IT_OK_PLAIN_LEADS if route is IS_IT_OK_PLAIN_ROUTES else IS_IT_OK_LEADS


def _the_ok_route(line):
    """The route for a yes-or-no ask: a body first, then the kitchen, then the general one."""
    text = line or ""
    if A_BODY_IN_IT.search(text):
        return IS_IT_OK_ROUTES
    if A_FOOD_IN_IT.search(text):
        return IS_IT_OK_FOOD_ROUTES
    return IS_IT_OK_PLAIN_ROUTES


def _the_rules_route(line):
    """The route for a rule: the document one only where the line names a document."""
    return RULES_ROUTES if DOCUMENT_NAMED.search(line or "") else RULES_PLAIN_ROUTES


def _the_lead_and_the_route(clean, memory=None):
    """What can be said about this kind of question, and where the rest lives, or ""."""
    line = " ".join(str(clean or "").split())
    if not line or ASKS_TO_DECIDE.search(line):
        return ""
    # A page, a policy or somebody else's rules has a real pointer, and the module that speaks it
    # (`where_it_answers`, PRIORITY -999) only speaks over a hedge. A lead and a route put in its
    # place takes the named page away: "whats the cancellation policy" lost the cover-and-
    # exclusions card and "what does the law say about notice period" lost the notice-and-fees
    # section, Citizens Advice and ACAS by name. Whatever the routes hold is left to them.
    if _the_routes_hold_this(line):
        return ""
    if NEWS_RESULT.search(line):
        return (_choose(NEWS_LEADS, memory, clean) + " "
                + _choose(NEWS_ROUTES, memory, clean))
    if WHAT_TO_TAKE.search(line):
        return (_choose(WHAT_TO_TAKE_LEADS, memory, clean) + " "
                + _choose(WHAT_TO_TAKE_ROUTES, memory, clean))
    if HOW_TO_TEACH.search(line):
        return (_choose(HOW_TO_TEACH_LEADS, memory, clean) + " "
                + _choose(HOW_TO_TEACH_ROUTES, memory, clean))
    if LEAVING_SOMEONE.search(line):
        return (_choose(LEAVING_SOMEONE_LEADS, memory, clean) + " "
                + _choose(LEAVING_SOMEONE_ROUTES, memory, clean))
    if IS_IT_OK.search(line):
        return (_choose(_the_ok_lead(line), memory, clean) + " "
                + _choose(_the_ok_route(line), memory, clean))
    if FIRST_ATTEMPT_ASKS.search(line):
        return _choose(FIRST_ATTEMPT_LINES, memory, clean)
    if WATCH_OUT.search(line):
        if A_BODY_IN_IT.search(_the_whole_exchange(line, memory)):
            return (_choose(WATCH_OUT_BODY_LEADS, memory, clean) + " "
                    + _choose(WATCH_OUT_BODY_ROUTES, memory, clean))
        return (_choose(WATCH_OUT_LEADS, memory, clean) + " "
                + _choose(WATCH_OUT_ROUTES, memory, clean))
    if A_USUAL_AMOUNT.search(line):
        return (_choose(USUAL_AMOUNT_LEADS, memory, clean) + " "
                + _choose(USUAL_AMOUNT_ROUTES, memory, clean))
    if SOMEONE_ELSES_OWN.search(line):
        return (_choose(SOMEONE_ELSES_LEADS, memory, clean) + " "
                + _choose(SOMEONE_ELSES_ROUTES, memory, clean))
    # The kind that is actually being asked about wins, and a machine is the last of them: "how
    # much is the car park" and "is the car park open" are a price and an hour, not a fault code.
    if LIVE_TODAY.search(line) and LIVE_ASK.search(line):
        return (_choose(LIVE_TODAY_LEADS, memory, clean) + " "
                + _choose(LIVE_TODAY_ROUTES, memory, clean))
    if HOW_MUCH_TO_PUT_IN.search(line):
        return (_choose(PUT_IN_LEADS, memory, clean) + " "
                + _choose(PUT_IN_ROUTES, memory, clean))
    if A_PRICE_THEY_WILL_PAY.search(line):
        return (_choose(A_PRICE_LEADS, memory, clean) + " "
                + _choose(A_PRICE_ROUTES, memory, clean))
    if GET_READY_FOR.search(line):
        return (_choose(GET_READY_LEADS, memory, clean) + " "
                + _choose(GET_READY_ROUTES, memory, clean))
    if RULES_FOR_THEIR_CASE.search(line):
        return (_choose(RULES_LEADS, memory, clean) + " "
                + _choose(_the_rules_route(line), memory, clean))
    if A_MACHINE_OF_THEIRS.search(line):
        return (_choose(A_MACHINE_LEADS, memory, clean) + " "
                + _choose(A_MACHINE_ROUTES, memory, clean))
    # No kind recognised: the pool's own line stands rather than a generic one put in its place.
    return ""


# A line about this chat itself is the bot's own to answer, whatever the pools made of it. On
# today's main "how long have we been talking" is read as a date on a document - "find the paper
# or page with the reference on it, read what it actually promises" - because "how long" is the
# shape of a date question. That is a reply about a subject the person never raised, and the clock
# reader that answers it properly only ran behind a search hedge, so the misreading kept its turn.
# The gate here says: a line that asks how long this chat has been going, or whether there is a
# limit to it, goes to the bot-about reader first. Nothing else is let through it: the tail is
# anchored, so "how long have we been talking about the deposit" stays a line about the deposit.
_THIS_CHAT_TALK = r"(?:talk|chat|talking|chatting|keep\s+going|keep\s+you\s+here)"
ABOUT_THIS_CHAT = re.compile(
    r"^\W*(?:(?:and|but|so|oh|ok|okay|well|right|sorry|quick|just|question|one\s+question|"
    r"quick\s+question|first\s+question|random\s+question)\W+)*"
    r"(?:"
    r"how\s+(?:long|much\s+time)\s+(?:have|has|did)\s+(?:we|i|you|you\s+and\s+i)\s+been\s+"
    + _THIS_CHAT_TALK +
    r"|how\s+long\s+has\s+this\s+been\s+going\s+on"
    r"|(?:is|are)\s+there\s+(?:a|any)\s+(?:time\s+)?limit(?:\s+(?:to|on)\s+"
    r"(?:(?:how\s+long|the\s+time)\s+)?(?:(?:we|i)\s+can\s+)?(?:"
    + _THIS_CHAT_TALK + r"|this|it|the\s+chat|our\s+chat))?"
    r"|have\s+(?:we|i)\s+got\s+long"
    r")"
    r"(?:\s+(?:with|to|for)\s+(?:you|me|this|now)|\s+so\s+far|\s+now|\s+for\s+long|\s+much)?"
    r"[ ?!.,;]*$",
    re.I,
)


def _asks_about_this_chat(clean):
    """True when the line asks how long this chat has gone on, or whether there is a limit."""
    line = " ".join(str(clean or "").split())
    return bool(line and ABOUT_THIS_CHAT.match(line))
