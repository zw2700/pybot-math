"""What the bot knows about the kind of question, when it does not know the answer.

`findout.py` reads the asks whose answer lives in one named place - today's hours, the queue, a
status, a form, something near the person - and says the place. It reads them from the thing in
the line ("the tip", "my council", "near me"), so it can only answer where a thing is named.

The everyday asks that carry no such thing got the plain hedge instead:

    **User:** What does a structural engineer cost?
    **Bot:** I'm not sure about that one, sorry - I'd rather not guess. A quick search online
    will get you a solid answer.

    **User:** How many people live in Sheffield?
    **Bot:** No number for that here, sorry, and I'd rather not invent one. The Wikipedia page
    or the official site will have it.

A pointer is not a reply (STYLE.md, "Not knowing, honestly"): the bot does know what that kind
of question turns on - a job is quoted rather than priced off a list, a population figure moves
with the year and the boundary drawn round it - and that half is worth saying before the place
that settles the rest. So this module reads the kind of ask from its shape and answers with the
two halves in order: what decides it, then where the rest is.

Nothing here is a fact about the world. Not one line holds a price, a date, a figure or a name,
so nothing can be invented and nothing goes stale. A line that is not one of these kinds gets
None and keeps whatever the composer had, and a kind is skipped when the shape is not the
question ("how much paracetamol can i take" is a dose, not a price).
"""
import re

# A figure republished every day - an exchange rate, a fuel price, a savings or mortgage rate - is
# not a quote for a job and not a tariff for a place: every place that offers one adds its own
# margin and terms on top, and the figure printed with it is only true on the day it carries.
A_MOVING = re.compile(
    r"\b(?:exchange|interest|mortgage|savings|base|bank) ?rates?\b|"
    r"\brate of exchange\b|\bfuel prices?\b|\b(?:petrol|diesel) prices?\b|"
    r"\bprice of (?:petrol|diesel|fuel)\b|\bhow much is (?:petrol|diesel|fuel)\b", re.I)
MOVING_LINES = (
    "That figure is republished every day and two places rarely quote the same one, because each "
    "adds its own margin or terms on top: compare two of them and go with the one whose small "
    "print fits what you are actually doing, checking the date printed with the number.",
    "Nobody keeps that number in their head - it moves daily and the version printed next to it "
    "is the only one that counts. Read two offers rather than one, and add on the fee or the "
    "terms before you decide which is really cheaper.",
)
# A price for a job or a thing. A job is quoted rather than priced off a list, and a model is
# priced off a page rather than from memory, so the answer is the shape of the number and where
# it is written down. "the going rate for a plasterer" and "price of a small van" are the same
# ask with no question word in front.
A_PRICE = re.compile(
    r"\bhow much\b|\bwhat(?:'s| is| does| would| will)?\b[^.?!]*\bcosts?\b|"
    r"\bcost of\b|\bprice of\b|\bprices?\b|\bcheaper\b|\bcheapest\b|\bset me back\b|"
    r"\bbudget for\b|\bgoing rate\b|\bthe rate for\b|\bwhat do you pay for\b", re.I)
NAME_ONLY_ASK = re.compile(
    r"^\s*(?:the\s+)?(?:price|cost)s?\s+(?:of|for)\b|\bgoing rate\b|\bthe rate for\b", re.I)
# An amount, a dose or a measurement is not money. Two written quotes is a worse answer to "how
# much paracetamol can i take" than the hedge it replaced, so these shapes are read out first.
NOT_A_PRICE = re.compile(
    r"\bhow much\b[^.?!]{0,32}\b(?:weigh|weighs|weight|sleep|eat|drink|take|give|feed|exercise|"
    r"water|milk|protein|salt|sugar|fibre|calories|units|grams|ml|litres|paracetamol|ibuprofen|"
    r"is safe|are safe|is too much|is normal|is enough)\b|"
    r"\bhow much\b[^.?!]{0,20}\b(?:can|should|could) i\b", re.I)
# A spend repeated through the week and then asked for by the year is a sum, not a quote. "how
# much does lunch out five days a week cost me in a year" was answered "There is no list price for
# that: what it comes to depends on the size of the job", which is a fitted kitchen's answer, not a
# lunch's. Two shapes have to be there together, because either alone is an ordinary price ask:
# a count of times in a short span ("five days a week", "twice a week", "every day") and a longer
# span to add them over ("in a year", "over the year"). "a gym is 50 a month" has the first and
# not the second, and "how much does it cost to redo a bathroom" has neither.
A_REPEATED_SPEND = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|twice|three times|four times|every|each)\b"
    r"[^.?!]{0,24}?\b(?:a|per|each|every)\s+(?:day|week|month)\b", re.I)
A_LONGER_SPAN = re.compile(
    r"\b(?:in|over|for|across)\s+a\s+year\b|\ba\s+year\b|\bper\s+year\b|\bannual(?:ly)?\b|"
    r"\bin\s+(?:twelve|12)\s+months\b", re.I)
# What the sum is of: money spent. A repeat with no cost in it is a plan or a frequency question
# ("i go to the gym three times a week for a year"), which is not this reading.
ASKS_A_COST = re.compile(
    r"\bhow much\b|\bcosts?\b|\bcosting\b|\bspend\b|\bspent\b|\bafford\b|"
    r"\bexpensive\b|\bset me back\b|\bcome to\b|\bcomes to\b", re.I)
# An amount already in the line is the costs table's: "i spend 5 pound a day on lunch" is
# answered "£5 a day is about £1,825 a year", with the price the person gave. This reading is for
# the ask that gives the frequency and no price, where the only honest number is the count.
AN_AMOUNT_ALREADY = re.compile(
    r"[£$]|\b\d+\s*(?:p|pence|pounds?|quid|bucks|euros?)\b|\b(?:fiver|tenner|twenty)\b|"
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:pounds?|quid)\b", re.I)
A_COUNT_IN_A_SPAN = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|twice|three times|four times|five times)\s*"
    r"(?:days?|times|nights?|lunches|cups?|pints?|cigarettes?|takeaways?|journeys?|trips?|"
    r"rides?|lessons?|bottles?|coffees?)?\s*(?:a|per|each|every)\s+(day|week|month)\b", re.I)
A_EVERY_SPAN = re.compile(r"\b(?:every|each)\s+(day|week|month)\b", re.I)
COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
               "twice": 2, "three times": 3, "four times": 4, "five times": 5}
A_YEAR = {"day": 365, "week": 52, "month": 12}
# One example price, so the line shows the sum rather than describing it. A fiver is the one
# price everybody can divide by, and it is named as an example rather than as the answer.
EXAMPLE = 5


def times_a_year(clean):
    """The count of a repeated spend in a year, and the span it was said in, or (None, None)."""
    if not ASKS_A_COST.search(clean):
        return None, None
    if AN_AMOUNT_ALREADY.search(clean):
        return None, None
    if not A_LONGER_SPAN.search(clean):
        return None, None
    found = A_COUNT_IN_A_SPAN.search(clean)
    if not found:
        # "a coffee every day" says the span and no count, which is one in each.
        plain = A_EVERY_SPAN.search(clean)
        if not plain:
            return None, None
        return A_YEAR[plain.group(1).lower()], " ".join(plain.group(0).split())
    said, span = found.group(1).lower(), found.group(2).lower()
    count = int(said) if said.isdigit() else COUNT_WORDS.get(said)
    if not count:
        return None, None
    return count * A_YEAR[span], " ".join(found.group(0).split())


def sum_lines(clean):
    """The lines for a repeated spend asked for by the year, or None."""
    times, said = times_a_year(clean)
    if not times:
        return None
    figure = times * EXAMPLE
    written = said[:1].upper() + said[1:]
    return (
        "{w} is {n:,} a year. Put your own price on one - £5 each is £{fig:,} - and that is the "
        "figure to weigh against cutting it back.".format(w=written, n=times, fig=figure),
        "{w} is {n:,} times a year, so put a price on one: at a fiver each that is £{fig:,}, "
        "which is what the habit really costs.".format(w=written, n=times, fig=figure),
    )


def a_sum_through_the_year(clean):
    """True when the line adds up a repeated spend over a longer span, which is not a quote."""
    return bool(times_a_year(clean)[0])

PRICE_LINES = (
    "There is no list price for that: what it comes to depends on the size of the job, the state "
    "of the thing and when you want it, so ask two firms to price the same description in writing "
    "and compare what each one leaves out rather than the total.",
    "The figure comes from a quote or a listing, not from me: get the same description from two "
    "places, in writing, and check what each one includes - the parts, the labour, the call-out "
    "and the VAT.",
)

# A published rate is not a quote: a car park, a fare, an entry price or a ticket is set by
# whoever runs the place and printed on their own page, and the mistake here is answering it with
# "ask two firms to quote" - parking has no second firm and no negotiation, only an hourly rate
# and a day cap.
A_RATE = re.compile(
    r"\b(?:parking|car ?park|to park|park there|entry|admission|tickets?|fares?|day pass|"
    r"week pass|season ticket|"
    r"membership|toll|ferry|crossing|per night|a night|per hour|per day|day rate|hourly rate)\b",
    re.I)
RATE_LINES = (
    "That is a published rate rather than a quote: whoever runs the place sets it, it moves with "
    "the day and the season, and a cap or a longer stay usually costs less per hour. Their own "
    "page or listing has today's, so ask what the whole stretch comes to rather than the headline "
    "figure.",
    "The headline rate is only half of it: an evening or weekend price, a day cap, a return or a "
    "longer booking often costs less than paying by the hour, and the operator's own page lists "
    "them all. Check today's figure there before you pay.",
)

# One thing and whether it earns its price. Nothing is paired here, so the answer is about the
# condition, the cost of putting it right and the cost of new - "both will do the job", which is
# the reply to a pair, read as nonsense to a person asking about one thing.
A_WORTH = re.compile(
    r"\bworth it\b|\bworth the money\b|\bworth buying\b|\bworth the extra\b|"
    r"\bworth paying\b|\bworth the price\b|\bgood buy\b|\bis it worth\b", re.I)
# The precept below is about one thing you own: what it costs to put right, what it costs to
# replace. "Worth it" is not that question on its own - it is asked of a series, a degree, a
# physio appointment, a castle and a dog as readily as of a boiler, and the repair-or-replace
# answer read as nonsense to all of them ("is it worth watching the sopranos next" got "what it
# would cost to put right and what the new one costs"). So the kind is only read where the line
# carries the repair-or-buy words the precept is about: fixing, mending, servicing, replacing,
# claiming, buying a thing. Everywhere else the line keeps whatever the composer had, which for a
# work, a place, a course or a person is a hedge rather than the wrong answer.
A_REPAIR_OR_BUY = re.compile(
    r"\b(?:fix|fixes|fixing|fixed|mend|mends|mending|mended|repair|repairs|repairing|repaired|"
    r"service|services|servicing|serviced|replace|replaces|replacing|replacement|replaced|"
    r"new one|second hand|secondhand|refurb(?:ish|ished)?|upgrade|upgrading|claim|claims|"
    r"claiming|claimed|install|installs|installing|buy|buys|buying|bought|"
    r"worth the money|worth buying|good buy|worth paying|worth the price|"
    r"paying extra|pay extra)\b", re.I)
# A phrase, not a word: "does it need replacing" and "is it worth a service" are the same ask
# with no buying word in it, and the thing being asked about can be named by what is wrong with
# it ("the boiler is on its last legs, is it worth it").
A_BROKEN_THING = re.compile(
    r"\b(?:broken|breaking|broke|not working|stopped working|gone wrong|last legs|leaking|"
    r"faulty|dead|dead as|knackered|worn out|on the blink|cracked|rusting|needs? a repair|"
    r"needs? fixing|needs? replacing|needs? a service|mend it|fix it|replace it|repair it)\b",
    re.I)


def not_about_one_owned_thing(clean):
    """True when a "worth it" line is not about a thing that is repaired or replaced.

    The shape is the guard the other kinds take. It reads the line, not the conversation: a line
    that names neither the repair nor the thing going wrong is a question about a work, a place,
    a course or a person, and the precept about the cost of putting it right does not fit it.
    """
    return not (A_REPAIR_OR_BUY.search(clean) or A_BROKEN_THING.search(clean))

WORTH_LINES = (
    "What decides it is the condition, what it would cost to put right and what the new one "
    "costs: if the repair comes to more than about half of new, it usually is not worth it. Get "
    "the repair cost in writing first, then compare that with the price of a new one.",
    "It earns its price when what it needs doing comes to less than replacing it, and a second "
    "one of the same age has its own faults. Ask for the repair cost in writing, and price the "
    "new one before you decide rather than after.",
)

# A pair is named and one of them has to win.
A_CHOICE = re.compile(
    r"\bwhich is better\b|\bwhich one is better\b|\bbetter to (?:get|buy|go for)\b|"
    r"\bor should i\b|\bshould i (?:get|buy|go for)\b[^.?!]{0,40}\bor\b|\bvs\b|"
    # Two options do not need the word "or": "pick between" and "choose between" are the same ask.
    r"\b(?:pick|choose|decide|select) between\b", re.I)
CHOICE_LINES = (
    "Both work for somebody, so it comes down to what you would miss if you had to give the other "
    "one back, and which of them fits the week you actually have. Write down what each one is "
    "for before you compare what they cost, and the one you have to keep justifying is usually "
    "the answer.",
    "The way to settle it is which one you would still be glad of in a year, and whether either "
    "of them brings a running cost with it - so list what you would use each one for, then "
    "compare the whole cost rather than the price on the ticket.",
)

# How far it is: a road distance and a time, which bend with the route and the hour.
A_DISTANCE = re.compile(
    r"\bhow far\b|\bmiles? from\b|\bmiles? to\b|\bhow long is the (?:drive|journey|walk)\b|"
    r"\bdistance (?:from|to|between)\b", re.I)
DISTANCE_LINES = (
    "The straight-line miles and the road miles are two different numbers, and the time bends "
    "with the hour you travel, so put both ends into a map app and read the route it gives: it "
    "carries the miles, the time and the way round the slow bit.",
    "For a journey by road that is a map app, and for one by train it is the operator's own "
    "planner: both give the miles or the connections for the hour you would actually go, which "
    "is the part a rough figure from anyone else gets wrong.",
)

# How long a process takes. A range from the body that runs it beats one number from anybody.
A_DURATION = re.compile(
    r"\bhow long (?:does|do|will|would|should|until|before|after)\b|\bhow long until\b|"
    r"\btakes? how long\b|\bhow soon\b|"
    r"\bhow many (?:hours|days|weeks|months|years)\b[^.?!]{0,20}\b(?:does|do|will|until|"
    r"before|after|should i wait)\b", re.I)
# A bare follow-up is not this kind: "how long does it take", "how long does it last" name only
# the pronoun, and the line's "where" (the queue, the body that runs it) depends on what "it" is.
# The previous answer is what those follow-ups belong to (`findout.more_about_the_journey`), so
# they keep the floor they had rather than being told about a queue they never mentioned.
BARE_DURATION = re.compile(
    r"^(?:and |so |but |ok |okay )?(?:how long|how soon)\b[\s\w]{0,24}?"
    r"\b(?:it|that|this|they|them|one)\b[\s\w]{0,10}?\??$", re.I)
# The lines below are about a queue at an office or a trade: a claim, a form, a survey, a sale, a
# repair. A cooking time, a plant, a healing body, or the wait before asking someone something is
# not a queue, and "a range from the body that runs it" is the wrong reply to "how long does
# mince take" - so this kind needs a sign that somebody else's queue is doing the waiting.
A_QUEUE = re.compile(
    r"\b(?:claim|claims|application|apply|form|forms|paperwork|order|delivery|courier|"
    r"post|posting|post office|queue|backlog|repair|repairs|service|servicing|mot|"
    r"survey|surveyor|solicitor|conveyanc|completion|exchange of contracts|offer|"
    r"mortgage|valuation|passport|licence|license|visa|council|benefit|benefits|"
    r"universal credit|pip|esa|refund|return|returns|dispute|appeal|hearing|decision|"
    r"assessment|builder|builders|plasterer|electrician|plumber|joiner|installer|install|"
    r"installation|dispatch|boiler|house move|sale|sell|selling|buying|purchase|probate|"
    r"will|tenancy|landlord|deposit|dbs|background check|bank|payment|transfer|clearing|"
    r"money|clears|clearing|wait|waits|waiting)\b", re.I)


def NOT_A_QUEUE(text):
    """True when the wait is not somebody else's queue: a bare follow-up, a body, a pan."""
    if BARE_DURATION.search(text):
        return True
    if re.search(r"\b(?:how long|how soon) (?:do|should|shall|can|will) (?:i|we) "
                 r"(?:wait|hold|hang|leave|give|keep|sit)\b", text):
        return True
    return not A_QUEUE.search(text)


DURATION_LINES = (
    "How long that takes depends on the queue, how much there is to do and the time of year, so "
    "ask the body that runs it for their current wait and whether the date they give includes "
    "the slow part at the end - a range from them beats any single figure.",
    "The honest answer is a range: the size of it and how busy they are move it by weeks, so ask "
    "whoever handles it what they are running at now, and treat the earliest date they give as "
    "the best case rather than the promise.",
)

# Whether a socket will carry two things is a sum, not a lookup: the watts are on both labels.
# The wording is either the rating named ("13 amp plug") or two things put on one supply ("off one
# socket", "on an extension lead"), which is the same sum however it is asked.
# "Trip" is two words in English. The fuse sense is the past or the continuous ("the fuse
# tripped", "it keeps tripping") and the bare present with something that trips after it ("it
# trips the breaker"); the holiday sense takes none of those ("does that matter for the trip",
# "our trip to cornwall"). A bare "trip" was read as a socket sum, so a holiday line that asked
# about the plan got the watts of a 13-amp socket.
A_LOAD = re.compile(
    r"\b\d+\s*-?\s*amp\b|\bextension lead\b|\bplug socket\b|\bfuse\b|"
    r"\btripp(?:ed|ing)\b|\btrips?\b\s+(?:the\s+|a\s+|our\s+|my\s+|your\s+)?"
    r"(?:fuse|circuit|breaker|mcb|rcd|socket|supply|switch|electric\w*|mains|ring)\b|"
    r"\b(?:off|from|on|into)\s+(?:one|the same|a single)\s+(?:socket|plug|circuit|extension)\b",
    re.I)
LOAD_LINES = (
    "The labels settle it: the watts are printed on the base of each thing, and a 13-amp socket "
    "gives about 3,000 watts in total, so the sum is what counts rather than the number of "
    "plugs. Add up the labels and keep the total under that - a kettle or a heater on its own "
    "takes most of it.",
    "Add up the watts on the labels of everything that would be on at once and keep the total "
    "under about 3,000 for a 13-amp socket, because a heater or a kettle alone takes most of the "
    "headroom. The rating is usually moulded into the plug or the base, not on the box.",
)

# Whether a thing will fit or work with another thing: the size and the model on the label decide
# it, and the same name comes in two sizes.
A_FIT = re.compile(
    r"\b(?:will|would|does|do|can)\b[^?!]{0,30}\b(?:fit|fits)\b|"
    r"\b(?:work|works|go) with\b[^.?!]{0,20}\b(?:battery|charger|drill|hose|part|filter|"
    r"attachment|unit|set|kit)\b|"
    r"\bwhich\s+(?:size|model|part|one)\b[^?!]{0,20}\bdo i need\b|\bwhat size\b|"
    r"\bis (?:it|this|that) compatible\b", re.I)
FIT_LINES = (
    "The size and the model on the label decide it rather than the picture: the model number is "
    "usually on a plate underneath, in the manual or on the maker's page for it. Read that "
    "before anything is ordered, because the same name comes in more than one size.",
    "It is the measurements and the model number that settle it, and both are on the thing "
    "itself, so note them down and match them against the spec on the maker's own page for the "
    "part - that is where the fit is stated rather than guessed at.",
)

# Whether it is allowed: the current rules and the person's own case decide it, never a general
# opinion. Board games and swimming pools have rules too, so this needs a thing that is governed.
A_RULE = re.compile(
    r"\bam i allowed\b|\bare we allowed\b|\bis it legal\b|\bis that legal\b|\bdo i need (?:a |an |"
    r"permission|to )\b|\bcan i be made to\b|\bcan they make me\b|\bhave i got the right\b|"
    r"\bwhat are my rights\b|\bdo i have to\b|\bam i entitled\b|\bis it against the law\b|"
    r"\bcan my (?:landlord|employer|boss)\b", re.I)
NOT_A_RULE = re.compile(
    r"\b(?:uno|monopoly|chess|poker|scrabble|darts|snooker|board game|"
    r"bishop|knight|rook|pawn|checkmate|the pieces)\b", re.I)
# "Do I need to" is the plainest way to ask a yes-or-no about a procedure, and it is not a
# question about rules: "do i need to prick them" (potatoes), "do i need to soak broad beans",
# "do i need to peel kiwi" and "do i need to see a physio" were all told about the version of the
# rules in force and the issuing office's page. The other shapes here (am i allowed, is it legal,
# do i have to, am i entitled, what are my rights, can my landlord) are about rules on their own;
# the "do i need" shapes are only about rules when the line names a rule's subject as well - a
# licence, a permit, a visa, a deposit, a notice period, a form, HMRC, the council.
A_DO_I_NEED = re.compile(r"\bdo i need (?:a |an |to )\b|\bdo i have to\b|\bdo we need to\b", re.I)
A_RULE_SUBJECT = re.compile(
    r"\b(?:licen[cs]e|licen[cs]ed|permit|permission|visa|insurance|insurer|mot\b|"
    r"tax|taxed|deposit|notice|contract|landlord|tenant|letting agent|employer|boss|\bhr\b|"
    r"council|council tax|hmrc|gov\.uk|government|court|probate|benefits?|universal credit|"
    r"housing benefit|claim|claiming|form|forms|declaration|statement|registration|register|"
    r"passport|inspection|consent|referral|prescription|legal|law|rights|entitled|mortgage|"
    r"solicitor|conveyanc\w*|certificate|crime number|vet\b|policy|warranty|guarantee|"
    r"refund|return it|duty|obliged|obligation)\b", re.I)


def not_a_bare_procedure(clean):
    """True when a "do i need to" line names nothing a rule is about.

    The rest of `A_RULE` stands on its own: "am i allowed", "is it legal" and "what are my
    rights" are about rules whichever thing follows them. Only the "do i need" / "do i have to"
    shapes are the everyday yes-or-no about a procedure, and they need the subject of a rule in
    the same line before the precept about the wording in force is the right thing to say.
    """
    return bool(A_DO_I_NEED.search(clean)) and not A_RULE_SUBJECT.search(clean)


def not_a_rule(clean):
    """Both guards for the rule kind: the board game, and the bare procedure."""
    return bool(NOT_A_RULE.search(clean)) or not_a_bare_procedure(clean)
RULE_LINES = (
    "Whether that is allowed turns on the rules as they stand this year and on your own case, so "
    "the current wording decides it rather than what anyone has heard. GOV.UK has the national "
    "version and your council's site the local one, and the office that runs it will put the "
    "conditions for your situation in writing - keep that letter.",
    "It depends on what your own agreement says and on the version of the rules in force, and "
    "the gap between those two is usually the whole answer. The issuing office's own page has "
    "the current wording, and one call to them settles the case the page does not cover.",
)

# A published figure about a named place or group: the year and the boundary change the answer.
A_STAT = re.compile(
    r"\bhow many (?:people|residents|households|of them|are there)\b|"
    r"\bwhat percentage\b|\bwhat proportion\b|"
    r"\bwhat(?:'s|s| is)?\s*(?:is\s+)?the population\b|\bpopulation of\b", re.I)
STAT_LINES = (
    "Figures like that come from whoever counts them, and the year and the boundary change the "
    "answer: \"the town\" and \"the wider area\" are two different numbers. The official "
    "statistics page or the council's own figures have the current one, with the year it is for "
    "printed beside it.",
    "That number moves every year and it depends where the line is drawn, so the body that "
    "publishes it is the one to quote: the national statistics site has it with the year, and "
    "the local council publishes its own for the area it covers.",
)

# How to do a thing nobody has a card for. The bot cannot see the person's kitchen or their
# boiler, but the order that works for most of these is the same, and it is worth saying before
# the page that has the rest: find the cause, change one thing at a time, cheapest first. A worry
# about a person or a feeling is not a how-to and keeps the module that answers for it.
A_HOWTO = re.compile(
    r"\bhow (?:do|can|should|could|would) (?:i|you|we)\b|\bhow to\b|"
    r"\bbest way to\b|\bany (?:tips|advice) (?:for|on)\b|\bwhat should i do about\b|"
    r"\bwhere do i start\b|\bhow would you go about\b", re.I)
# The steps below are steps for something going wrong, or for an office's own procedure: find the
# cause, change one thing, cheapest first. They are the wrong shape for a plain technique -
# "how do i pray", "how do i drain pasta", "how do i boil an egg" - and those read better as
# nothing (the floor they had) than as fault-finding. So the kind needs a sign of trouble or of a
# process with an order, and "how do i do a thing I have never done" is not it on its own.
A_TROUBLE = re.compile(
    r"\b(?:stuck|stubborn|tight|seized|jammed|wedged|won'?t|wont|not working|stopped working|"
    r"broke|broken|leak|drip|damp|mould|mold|smell|stink|stain|crease|creak|squeak|squeal|"
    r"rattl|wobbl|vibrat|noisy|block|blocked|slow|stiff|rust|scratch|burn|fade|crack|chip|"
    r"snap|worn|tangled|knotted|fog|cloudy|flat|dead|flicker|trip|overflow|"
    r"keeps (?:going|coming|stopping|turning))", re.I)
A_PROCESS = re.compile(
    r"\b(?:will|probate|benefits?|universal credit|council tax|licence|license|permit|"
    r"passport|visa|tax return|self assessment|pension|redundancy|redundant|"
    r"apply|application|appeal|complain|complaint|refund|return|cancel|cancelling|"
    r"mortgage|insurance|insure|claim|registration|register|deregister|"
    r"loyalty|warranty|guarantee|bill|bills|direct debit|standing order|"
    r"switch|switching|comparison|quote|quotes|contract|agreement|tenancy|deposit|"
    r"moving house|house move|move house|solicitor|notary|deed|title|land registry)\b", re.I)
A_HOWTO_HAS_A_SHAPE = re.compile(
    A_TROUBLE.pattern + "|" + A_PROCESS.pattern, re.I)
NOT_A_HOWTO = re.compile(
    r"\b(?:feel|feeling|feelings|anxious|anxiety|depressed|depression|panic|grief|grieving|"
    r"lonely|loneliness|scared|worried|worry|miscarriage|divorce|separating)\b|"
    # A person named after "with", "for" or "to" is who the thing is for, and a how-to still has
    # steps ("how do i share my location with my husband" is about the phone). A person is the
    # subject only when the ask is about them - telling, asking, comforting, helping.
    r"\b(?:tell|talk to|speak to|say to|ask|apologise to|apologize to|comfort|support|help|"
    r"explain to|break it to|be there for|deal with|do about)\b[^?!]{0,24}"
    r"\b(?:my|his|her|their)\s+(?:mum|mom|dad|son|daughter|wife|husband|partner|boyfriend|"
    r"girlfriend|friend|brother|sister|boss|child|kid|parents|family)\b", re.I)
def NOT_A_HOW_TO(text):
    """True when the steps above do not fit the ask: a feeling, a person, or no trouble in it."""
    return bool(NOT_A_HOWTO.search(text)) or not A_HOWTO_HAS_A_SHAPE.search(text)


HOWTO_LINES = (
    "The first steps are the same for most of these: work out what is actually causing it before "
    "you treat what you can see, change one thing at a time, and give each change a day before "
    "the next so you know which one worked. Write down what you tried and when.",
    "Do it in the order that costs least first: what you already have in the cupboard or the "
    "shed, then the cheap part or product, then the trade. Before you buy anything, check the "
    "manual or the maker's page for the exact model, because it says what is safe on that one "
    "and what is not.",
)

# A record: a deposit, a deed, a warranty, a policy, a receipt, a booking. Nobody can answer one
# of these from a description of it, because the answer is the entry the body holding it has -
# the date, the terms in force at the time and the name on it. Saying "ask them for it in writing,
# quoting the reference" is the part that is true of every one of them, and it is what the hedge
# ("a quick search online will get you a solid answer") never said.
A_RECORD = re.compile(
    r"\b(?:deposit|deeds?|title plan|land registry|warrant(?:y|ies)|guarantee|receipt|invoice|"
    r"policy|insurance|cover note|booking|reservation|tenancy agreement|assured shorthold|"
    r"certificate|statement|reference number|reference|paperwork|the small print|terms|"
    r"boundary|boundaries)\b",
    re.I)
# Not every line with one of those words is a question about the entry. A deposit paid towards a
# car, a booking someone is making now and a policy the person is asking how to write are other
# kinds of ask, and an insurance claim for a fire is somebody else's turn (NOT_HERE).
# What a word means is a definition, not an entry: "what does a deed mean" and "whats a reference
# number" are asking about the kind of thing, and the record line answers a question about the
# person's own paper. The article after the ask is the tell, which leaves "what does my policy say
# about a leak" alone.
# The article after the ask is the tell between a definition and a person's own paper, and the
# article can be "the" as easily as "a": "what does the small print mean" is asking what a phrase
# means, and "the small print" is in A_NAMED_DOCUMENT, so the record line took a turn that the
# rule it lives by forbids. "what does the small print say" stays the record's: "say" is about a
# copy the person is holding and "mean" is about the words.
NOT_A_RECORD = re.compile(
    r"\b(?:whats|what is|what are|what does|what do|meaning of)\s+(?:a|an)\b|"
    r"\bwhat\s+(?:does|do|is|are|did|can)\s+(?:the|this|that)\b[^.?!]{0,40}"
    r"\b(?:mean|means|meaning|stand for|definition)\b|"
    r"\b(?:how do i|how to|should i (?:take out|buy|get)|worth (?:getting|it)|"
    r"cheapest|cancel my|switch my|compare)\b|"
    # A complaint is not an ask. "whats the point of all this paperwork" and "i was drowning in
    # paperwork" are somebody fed up, and the record line would answer with a lecture about dates
    # and references. The phrase that made the line an ask at all is the one to drop it on.
    r"\bwhats? the point of\b|\bwhat is the point of\b|\bsick of\b|\bfed up\b|"
    r"\bdrowning in\b|\bcan'?t be (?:bothered|arsed)\b", re.I)

# A bare kind noun is not a document. "the planning policy", "a personal statement", "in simple
# terms" and "this paperwork" name a *sort* of paper, and the person's own copy is what has the
# date and the name on it. So the kind words that people also use loosely need a possessive
# ("my policy", "our statement") or the full name of a document ("terms and conditions",
# "insurance policy") before they count as one. The kinds that only ever name a document of
# theirs - a deposit, a receipt, a deed, a booking - need neither.
A_LOOSE_KIND_WORD = re.compile(
    r"\b(?:policy|policies|statement|statements|terms|paperwork|insurance|boundar(?:y|ies)|"
    r"contract|agreement)\b", re.I)
# "their" and "your" count: the bot asks about the person's own paper ("does your policy cover
# water damage") as often as they state it.
THEIR_OWN_PAPER = re.compile(r"\b(?:my|our|his|her|their|your|yours|ours|theirs)\b", re.I)
A_NAMED_DOCUMENT = re.compile(
    r"\b(?:terms and conditions|terms of (?:the|my|our|their|his|her|your)\b|"
    r"insurance polic(?:y|ies)|policy wording|policy document|policy schedule|"
    r"bank statement|statement of (?:the|my|our|their)\b|"
    r"tenancy agreement|assured shorthold|contract of employment|the small print)\b", re.I)


def _not_a_record(said):
    """True when this line is not about the entry itself, so the record kind stands down.

    The kinds' guards answer the same way: true means "not mine", and the next kind is read.
    """
    if NOT_A_RECORD.search(said):
        return True
    if A_NAMED_DOCUMENT.search(said) or THEIR_OWN_PAPER.search(said):
        return False
    return bool(A_LOOSE_KIND_WORD.search(said))
RECORD_LINES = (
    "What settles that is the entry itself rather than the general rule - the date on it, the "
    "terms that were in force then, and the name it is in. The office or firm that holds it can "
    "read it back to you, so ask for it in writing and quote the reference on it: the answer that "
    "counts is the one on paper, not the one given over the phone.",
    "That turns on the wording of the document, not on what is usually done: what it says, what "
    "date it came into force and whose name is on it. Whoever issued it keeps the record, and the "
    "one thing worth doing first is asking them to confirm in writing what their copy says.",
    "Nobody can answer that from the description of it, because the answer is in the paperwork - "
    "the date, the terms and the name on it. Ask the body holding it for the entry in writing with "
    "the reference on it, and keep what they send: a written answer is the one that can be relied "
    "on later.",
)

# Anything in here has an owner further up the composer, and "what decides it" is the wrong thing
# to say to it: an emergency is not a question about a spec, and a bereavement is not a figure.
NOT_HERE = re.compile(
    r"\b(?:999|911|112|111|ambulance|a&e|emergency|bleeding|not breathing|chest pain|"
    r"overdose|suicide|kill myself|end my life|self harm|"
    r"died|death|funeral|buried|cremation|passed away|grief|grieving)\b", re.I)
# Something that asks. A statement keeps the floor it had: "what decides it" on a remark reads as
# a lecture, and the naming of a stated thing is a different job.
ASKS_SOMETHING = re.compile(
    r"\b(?:how|whats?|what's|which|when|where|who|why|can|could|should|would|will|is|are|was|"
    r"were|do|does|did|am|has|have|had|may|might|shall)\b", re.I)

# The kinds in the order they are read. A pair named with "or" is a choice before it is a price
# ("which is better, a heat pump or a boiler" names both), and how far is a journey before it is
# a duration ("how long is the drive to leeds" is a distance, not a wait).
KINDS = (
    ("choice", A_CHOICE, CHOICE_LINES, None),
    # Before the nouns: a procedure ask ("how do i cancel my gym membership") names a thing a
    # tariff or a quote would also match, and the steps are what it wants. The shape guard keeps
    # it off asks that only look like a how-to.
    ("howto", A_HOWTO, HOWTO_LINES, NOT_A_HOW_TO),
    ("worth", A_WORTH, WORTH_LINES, not_about_one_owned_thing),
    ("distance", A_DISTANCE, DISTANCE_LINES, None),
    ("load", A_LOAD, LOAD_LINES, None),
    ("fit", A_FIT, FIT_LINES, None),
    ("rule", A_RULE, RULE_LINES, not_a_rule),
    ("figure", A_STAT, STAT_LINES, None),
    ("moving", A_MOVING, MOVING_LINES, None),
    ("rate", A_RATE, RATE_LINES, None),
    ("price", A_PRICE, PRICE_LINES, (NOT_A_PRICE, a_sum_through_the_year)),
    ("duration", A_DURATION, DURATION_LINES, NOT_A_QUEUE),
    # A record is neither a price nor a rule: the wording on the document decides it, and the
    # body holding it is the only one who can read it back. It comes after both, because a money
    # shape and a length are what the person is asking about even when the line names a warranty
    # or a statement: "what would the insurance be roughly" is a quote, and "how long does a
    # warranty last" is a length. Only a line neither of those reads is about the entry itself.
    ("record", A_RECORD, RECORD_LINES, _not_a_record),
)


# A reply that hands the whole question over: the shrug, or a shrug with a page named after it -
# "a quick search online will get you a solid answer", "the Wikipedia page or the official site
# will have it", "the seller's own site will beat anything I could tell you". The place is real;
# it is the part before it that is missing, and that part is what this module knows.
A_POINTER = re.compile(
    r"\ba quick search\b|\bsearch online\b|\bsearching for it\b|\bquick look\b|"
    r"\ba search\b|\blook (?:it|that) up\b|\bwikipedia\b|\bprice comparison\b|"
    r"\bpaste what it says\b|"
    r"\b(?:official|seller'?s|their|its|the)\b[^.?!]{0,20}?\b(?:site|page|listing|app)\b"
    r"[^.?!]{0,24}?\b(?:will|has|have)\b", re.I)


def names_only_a_page(reply):
    """True when a reply is a shrug with a search box or a page named as where to look.

    Not the same test as `fallback.is_a_hedge`: the live notes ("Prices move too fast for me to
    know. A quick look at the seller's own site") are the composer's own answer to a price ask
    rather than a hedge, and they are the same pointer to the person reading them. The greeting
    module asks both, so a line that already answers keeps its turn.
    """
    said = " ".join(str(reply or "").lower().split())
    return bool(said) and bool(A_POINTER.search(said))


# A reply that already points at the thing in the person's hand has done the job a record line
# would do. "The receipt has the date and the maker's own page has the cover" answers the warranty
# question: the paper is where the answer is, and the person already has it. Saying "the entry
# itself rather than the general rule, ask for it in writing" over that trades something concrete
# for something general, which is the trade this module exists to make the other way round.
THE_PAPER_ITSELF = re.compile(
    r"\bthe (?:receipt|deed|deeds|wording|document|documents|paperwork|certificate|policy|"
    r"contract|agreement|statement|invoice|booking|label|manual|terms)\b|"
    r"\b(?:date|name|reference|number) on it\b", re.I)


def names_the_paper(reply):
    """True when the reply already says the person's own paper is where the answer is."""
    said = " ".join(str(reply or "").lower().split())
    return bool(said) and bool(THE_PAPER_ITSELF.search(said))


def reads(text):
    """The kind of question this is, and the lines for it, or (None, None).

    Kept public so a test reads the same shapes the reply is built from: a test that re-wrote
    them would only be testing itself.
    """
    clean = " ".join(str(text or "").lower().split())
    if not clean or NOT_HERE.search(clean):
        return None, None
    if not (ASKS_SOMETHING.search(clean) or NAME_ONLY_ASK.search(clean)):
        return None, None
    for kind, pattern, lines, guard in WORRY_SHAPES + KINDS + PROCEDURE_SHAPES:
        if pattern.search(clean):
            if guard:
                guards = guard if isinstance(guard, tuple) else (guard,)
                if any(g(clean) if callable(g) else g.search(clean) for g in guards):
                    continue
            return kind, lines
    return None, None


def pool(clean, memory=None):
    """The lines for a gap the bot can still say something useful about, or None.

    The shape is the one `findout.pool` returns, so the caller picks among them the usual way and
    the last line the bot said is not said again.
    """
    summed = sum_lines(clean)
    if summed:
        return summed
    return reads(clean)[1]


# ---------------------------------------------------------------------------------------------
# Two shapes the kinds above have no room for, kept here so they read as what they are: a line
# `gap` used to send nowhere, and one it was never the right module for.
#
# A bare "do i need to ..." is not a question about the rules unless the line names something a
# rule is about, which `not_a_bare_procedure` now decides. What it left behind was a search hedge
# - "I don't know enough to answer that honestly" - for "do i need to bring anything", "do i need
# to take a towel", "do i need to print it", "do i need to prick them". Nothing in those says what
# the thing is for yet, and that is the whole of the answer, so ask for it.
A_NEED_TO = re.compile(r"\bdo (?:i|we) need (?:to |a |an )\b", re.I)
NEED_TO_LINES = (
    "Depends what it is for. Say the thing you are doing and I will tell you what it takes - and "
    "where a rule rather than common sense decides it, who to ask.",
    "It turns on the thing itself and on what it is for - a trip, a form, a job and a pan of "
    "something all want different things. Tell me which it is and I will give you the short "
    "version, rather than the general one that fits none of them.",
    "That depends on the thing itself and what you are doing with it. Say which and I will tell "
    "you, rather than guess at it.",
)
PROCEDURE_SHAPES = (("needto", A_NEED_TO, NEED_TO_LINES, None),)

# "Do I need to worry" and "do i need to panic" have the shape of a practical ask and none of the
# sense: somebody anxious is checking whether something is wrong. "Depends what for" is dismissive
# to that, a rule card is off the subject, and the hedge is worse than either, so they get two
# lines of their own - one question about the thing, and a promise of the straight answer once it
# is named. Read before the rest, because the procedure shape below would ask an anxious person
# what their trip is for.
A_WORRY_ASK = re.compile(
    r"\bdo (?:i|we) (?:need|have) to\b[^.?!]{0,24}\b(?:worry|panick?\w*|stress\w*|be anxious|"
    r"be scared|be (?:worried|afraid)|fret)\b", re.I)
WORRY_LINES = (
    "Worry about what? Tell me what is coming up and I will say whether there is anything to do "
    "about it, because most of what people brace for turns out to be somebody else's rule.",
    "Say what it is and I will tell you straight whether there is anything to do about it. If "
    "there is, it is usually one form or one call, and if there is not, you can stop carrying it.",
)
WORRY_SHAPES = (("worried", A_WORRY_ASK, WORRY_LINES, None),)
