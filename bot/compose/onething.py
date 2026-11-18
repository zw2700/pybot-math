"""Nothing in the store knows the line: say the one thing that is true about what it names.

A plain account of something with nothing on the end of it - "the tap has been running all
morning", "i think theyre underpaying me", "my shift starts at half 5 in the morning", "my
vision is gone when i stand up" - is not a question, so no pool answers it, and it reached the
intake form: "Got it. Is there anything you'd like a hand with?". That reply offers help with a
task nobody mentioned and could have come before any message at all.

What a friend does with a line like that is say the one thing they know about it: that water
where it should not be is a today job and the stopcock comes first, that a short payslip is
usually one of three things, that a half-five start is decided the night before. So the family
of thing the line names decides the reply - water in the house, pay, an early shift, a body, a
child under a year, a visit that is booked - and each pool says the part that is true whatever
the details are, with no number of theirs invented and no promise about how it ends.

Only ever a reply where nothing answered. The caller runs this last, before the intake form,
so a pool with something of its own has already had its turn.

There is no general body family here on purpose. "my dad is having chest pain" and "my head is
bleeding badly" are statements about a body too, and no line this pool could write is right for
them; the health and urgent pools read those, and a wrong reply there is worse than the intake
form. The one body shape here is standing up and the vision going, where the usual cause is
ordinary and the safe advice is the same for everybody.
"""
import re

# A statement, not a question. A question about the same thing has an answer to give and is
# somebody else's reading; a "?" or a wh-word at the front means the person is asking.
A_QUESTION_OPENER = re.compile(
    r"^\s*(?:what|when|where|which|who|why|how|can|could|should|would|will|is|are|was|were|do|"
    r"does|did|have|has|am)\b", re.I)

# A question can also sit in the middle of a line: "my baby is 6 months old can she have water"
# is an ask with a fact in front of it, and the thing it asks about has an answer somewhere else.
A_QUESTION_ANYWHERE = re.compile(
    r"\b(?:can|could|should|would|shall|is it|are they|is that|does it|do i|did i|too young|"
    r"too old|allowed|normal)\b", re.I)

# The thing that is running, leaking or dripping. Water where it should not be has a first move
# that is the same in every house, so this is the one family where the reply is a step.
WATER_THINGS = frozenset("""
    tap taps faucet faucets pipe pipes cistern toilet sink bath shower boiler radiator
    radiators stopcock valve overflow drain drains damp
""".split())
A_WATER_TROUBLE = re.compile(
    r"\b(?:running|runs|leak|leaks|leaked|leaking|drip|drips|dripped|dripping|overflow\w*|"
    r"flood\w*|burst|wont stop|won't stop|not stopping|wet|puddle|soaked|on all day|"
    r"left on|left running|been on|on since|still on)\b", re.I)

# Short pay. The gap on a payslip is nearly always one of three things, and the payslip is what
# anybody asks for first. Somebody else owing the person money - a tenant, a customer, a friend
# who said they would pay - is not this: the payslip is the wrong thing to look at there.
A_PAY_OWN = re.compile(
    r"\b(?:payslip|payslips|wages|salary|overtime|hourly|underpaid|underpay|underpaying|"
    r"my pay|short(?:er)? this month|short again|paid short)\b", re.I)
A_PAY_SOMEBODY_ELSE = re.compile(
    r"\b(?:rent|tenant|tenants|landlord|customer|customers|client|clients|invoice|invoices|"
    r"refund|bill|bills|mate|friend|brother|sister|mum|dad|he|she|they|owes?|owed)\b", re.I)
A_SHORT_PAY = re.compile(
    r"\b(?:underpay\w*|underpaid|short|less than|miss(?:ed|ing)?|wrong|not paid|didn'?t pay|"
    r"didnt pay|short-?changed|cheated|deduct\w*)\b", re.I)

# An early start. What decides an early start is the night before, and the catch-up at the
# weekend is what makes the next week worse.
A_SHIFT = re.compile(r"\b(?:shift|shifts|rota|alarm)\b", re.I)
# The hour is what makes it an early start: "my shift was fine today" and "my alarm did not go
# off" are about a shift and an alarm and neither is about getting up before it is light.
AN_EARLY_HOUR = re.compile(
    r"(?:\bhalf\s+[3-7]\b|\b[3-7](?::\d\d)?\s*(?:am|a\.m\.)|\bup at (?:[3-7]|half)|"
    r"\bstart(?:s|ing)? (?:at |by )?[3-7]\b|\bearly start\b|\bearly shift\b|"
    r"\bbefore (?:6|7|eight|seven|six)\b|\bdark\b)", re.I)

# Standing up and the vision going is the one shape in this pool where waiting is worse than
# saying the ordinary thing, because it is the most common cause and it is easy to guard
# against. Nothing here diagnoses: it names the usual cause and the two ways to be safe.
POSTURAL = frozenset("""
    vision eyes sight black blacks blacked dizzy dizziness faint faints fainting lightheaded
    light-headed headrush head-rush stars ears ringing
""".split())
A_STANDING = re.compile(r"\b(?:stand|stands|standing|stood|get up|gets up|getting up|got up)\b",
                        re.I)

# A child too young for the question to have an answer that stays true: what is coming next is
# the useful thing, and it is the same list for everybody.
A_BABY = re.compile(
    r"\b(?:(?:little|small|baby|newborn)\s+(?:one|boy|girl|laddie|lad|fella)|baby|babies|"
    r"newborn|infant|toddler)\b", re.I)
AN_AGE_UNDER_A_YEAR = re.compile(
    r"\b(?:\d{1,2}\s*(?:months?|weeks?|month|week)|\d{1,2}\s*(?:mo|wk)s?\b|"
    r"months? old|weeks? old|a few months|six months|seven months|eight months|"
    r"nine months|ten months|eleven months)\b", re.I)

WATER_IN_THE_HOUSE = (
    "Water where it should not be is a today job. Stopcock off first - under the kitchen sink "
    "or where the pipe comes into the house - and a tap that will not close is usually the "
    "washer, which costs pennies.",
    "Turn the water off at the stopcock before anything else, then look: a tap that runs on is "
    "nearly always the washer, and once it is isolated a leak stops being an emergency.",
)

SHORT_PAY = (
    "Get the payslip out before you say anything to anyone. The gap is nearly always a break "
    "taken off twice, an hour that was not counted, or a tax code that changed without anybody "
    "telling you.",
    "Compare the payslip against your own hours, then raise it with the number in your hand: it "
    "is usually one unpaid hour, a break deducted that you did not take, or the wrong tax code.",
)

# The reply never names an hour: the pool is the same line for a five, a half five and a six, and
# "a half-five start" told somebody who said five about a number they never said.
EARLY_START = (
    "An early start is decided the night before: bag by the door, clothes out, and lights off "
    "early rather than catching up at the weekend - the lie-in is what makes the next morning "
    "worse.",
    "The people who cope with an early start go to bed early rather than making up for it later. "
    "The same bedtime on days off, if you can: the lie-in is what makes the next week harder.",
)

A_STANDING_UP = (
    "Vision going as you stand is usually blood pressure dipping for a second. Go up in two "
    "stages - sit on the edge, then stand - and get it looked at if it keeps happening or you "
    "feel faint.",
    "That is the ordinary stand-up drop in blood pressure. Two stages getting up, water rather "
    "than coffee first thing, and have it checked if it happens again today.",
)

UNDER_A_YEAR = (
    "Under a year, the next thing arrives before you have got used to the last one - sitting "
    "up, then lumps of food, then pulling to stand. Whatever stage they are at will be gone in "
    "a month.",
    "That age is mostly a run of small milestones: sitting, then lumps, then pulling up. It "
    "changes faster than anybody gets comfortable with, so nothing odd lasts.",
)

# A baby and a struggle named in the same line is not a line about milestones: a bottle fight is
# about the feed, and the milestones would be an answer to a question nobody asked. Paced feeding
# is the first thing anybody is told about a feed that is a fight, and it is the same advice in
# every house, so it can be said without knowing the baby.
A_FEED = re.compile(r"\b(?:bottle|bottles|breast|breastfeed\w*|formula|feeding|feeds|feed|milk)\b",
                    re.I)
A_FEED_FIGHT = re.compile(
    r"\b(?:fights|fighting|refuses|refusing|refused|wont|won't|keeps?|screams?|screaming|"
    r"cries|howling|colic|colicky|reflux|sick|posset\w*|not taking|turns away)\b", re.I)
A_FEED_FIGHT_REPLY = (
    "A feed that is a fight is usually pace, wind or the teat: sit them up, keep the bottle level "
    "so the milk is in the teat and not pouring in, and stop halfway to burp. If they are still "
    "fighting it after that, the health visitor is the person to ask.",
    "Try paced feeding before anything else - upright, bottle level, a pause to burp in the "
    "middle - and check the teat: too fast a flow makes a baby gulp and pull away. A health "
    "visitor can watch a feed if it carries on.",
)


# A visit that is booked. "the boiler man is coming tuesday", "the plumber comes thursday",
# "the midwife is due on friday", "somebody is coming to look at the damp tomorrow": the person
# is telling you when somebody is turning up, and none of the families above names it. On main the
# first of those reached the intake form ("I'm listening - say more if it helps"), and the others
# went to a who-to-ask line ("A plumber or electrician will spot it in minutes") - which is a
# reply to somebody who has not rung one yet. The reading is narrow on purpose: a trade or a
# professional, a coming verb in the present or future, and a day. "did the plumber come" is a
# question with its own reader (bot/compose/their_day.py), "the plumber came tuesday" is a past
# visit, and "we got the keys on friday" names nobody who is coming.
VISITORS = frozenset("""
somebody someone man bloke bloke lady guy fella chap
boiler man boiler bloke plumber electrician gas man gas engineer engineer heating engineer
builder joiner carpenter decorator painer painter plasterer tiler roofer glazier locksmith
chimney sweep pest control drain man drain bloke surveyor cleaner window cleaner gardener
meter reader delivery man delivery driver courier van man removal man removals man fitter
technician repair man washing machine man dishwasher man oven man tv man sky man
broadband man bt man openreach man virgin man internet man
nurse district nurse community nurse health visitor midwife physio physiotherapist occupational
therapist carer support worker social worker housing officer housing association landlord
letting agent agent estate agent vet vet nurse groom farrier
council the council council inspector environmental health housing housing officer
scaffolder scaffolder scaffolder mechanic mot man aa man rac man
""".split())
A_COMING_VISIT = re.compile(
    r"\b(?:is|are|am|will be|going to be|should be|due|booked|scheduled|expected)\b"
    r"[^.!?]{0,24}?\b(?:coming|come|due|arriving|booked|booked in|scheduled|expected|turning up|"
    r"coming round|coming over|coming out|coming to|visiting|seeing)\b"
    r"|\b(?:comes|come|arrives|visits)\b", re.I)
# The day the visit is on, which is the part the reply takes. A day is what makes the line a
# booking; "the plumber is coming" alone is not this family.
A_VISIT_DAY = re.compile(
    r"\b(today|tonight|tomorrow|this morning|this afternoon|this evening|"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|next week|in the morning|in the afternoon|in the evening|first thing)\b",
    re.I)
# Who is coming decides what is worth asking, and the first version had one pool for all of
# them: "the district nurse is due thursday" was asked "Are they coming to look at it, or to do
# the job?" - a question about a washing machine. Three families, because there are three things
# a visit can be about: the person's own care, a thing in the house to be seen to, and the place
# itself (its council, its landlord, its meter).
A_CARE_VISITOR = frozenset("""
nurse nurses district community health visitor midwife midwives physio physiotherapist
occupational therapist ot carer carers care worker support worker social worker gp doctor
consultant specialist matron paramedic phlebotomist chiropodist podiatrist dentist hygienist
audiologist optician speech therapist slt
""".split())
A_TRADE_VISITOR = frozenset("""
boiler plumber plumbing electrician gas engineer heating engineer engineer builder joiner
carpenter decorator painter plasterer tiler roofer glazier locksmith sweep pest control drain
cleaner gardener fitter technician repair man washing machine dishwasher oven tv sky man
broadband bt openreach virgin internet man chimney scaffolder mechanic mot man aa man rac man
van man removal man removals surveyor vet farrier groom
""".split())
A_VISIT_CARE = (
    "{Day} then. Is it the usual check, or has something changed since the last one?",
    "Right - {Day}. Do you know what they are coming for, or is it a general check?",
    "Good to have it in the diary. Is somebody going to be with you for it?",
    "{Day} it is. Worth writing down the two or three things you want to ask while you think "
    "of them.",
)
A_VISIT_TRADE = (
    "Right - {day} then. Are they coming to look at it, or to do the job?",
    "{Day} it is. Is it the same one as last time, or somebody new?",
    "Good, that's in the diary. Do you have to be in for them, or can they get in?",
    "So {day} is the visit. Have they said how long they will be, or is it a wait in all "
    "morning?",
    "{Day} then. Is there anything you need to have ready for them before they get there?",
)
A_VISIT_PLACE = (
    "{Day} then. Do you need to be in for them, or can they get in?",
    "Right - {Day}. Have they said what they want to see, or is it just a look round?",
    "{Day} it is. Worth having whatever paperwork they asked about to hand.",
    "Good. Is it the first time they have been out, or do you know who you are getting?",
)


# "the plumber came tuesday" and "they came round last week" are a visit that has happened, which
# is a story to hear rather than a plan to help with.
A_PAST_VISIT = re.compile(
    r"\b(?:came|came round|came over|turned up|showed up|been round|was here|were here|"
    r"visited|did come)\b", re.I)


# Who is coming has to be somebody who does house calls. `VISITORS` is written as phrases -
# "boiler man", "meter reader", "tv man" - so reading it as a bag of single words let the thing
# in the phrase stand for the visitor: "the tv is coming back from repair monday" and "the new
# series is coming out friday" were both read as a visit. A word from this list is the person in
# the phrase, and a line with none of them is a thing coming, not somebody calling.
A_PERSON_IN_THE_VISIT = frozenset("""
somebody someone man bloke lady guy fella chap woman girl boy
plumber electrician engineer builder joiner carpenter decorator painter plasterer tiler roofer
glazier locksmith sweep cleaner gardener surveyor fitter technician mechanic
visitor therapist assessor inspector
nurse midwife physio physiotherapist carer worker officer landlord agent vet groom farrier
council mechanic dentist hygienist optician consultant specialist matron paramedic
phlebotomist chiropodist podiatrist driver reader
""".split())
# Coming back, out or up is a thing returning or being released, not somebody turning up: "the
# results are coming back friday", "the new series is coming out friday", "the kids are coming
# back sunday". A contractor finishing a job next week says "coming back" too, but the person
# guard above already keeps that one, and a line this reader drops keeps the answer it had.
A_COMING_THAT_IS_NOT_A_VISIT = re.compile(
    r"\b(?:coming|come|comes|coming\s+round|coming\s+over)\s+(?:back|out|up|off|through)\b"
    r"|\b(?:back|out|up)\s+from\b", re.I)


def _a_visit(text):
    """True when the line says somebody is turning up on a day."""
    if not _has(text, VISITORS):
        return False
    if not _has(text, A_PERSON_IN_THE_VISIT):
        return False
    if not A_VISIT_DAY.search(text):
        return False
    if A_PAST_VISIT.search(text):
        return False
    if A_COMING_THAT_IS_NOT_A_VISIT.search(text):
        return False
    return bool(A_COMING_VISIT.search(text))


def _the_visit_family(text):
    """The pool for who is coming: a person's care, a thing in the house, or the place itself."""
    if _has(text, A_CARE_VISITOR):
        return A_VISIT_CARE
    if _has(text, A_TRADE_VISITOR):
        return A_VISIT_TRADE
    return A_VISIT_PLACE


def _has(text, words):
    return bool(set(re.findall(r"[a-z']+", text)) & set(words))

# A change of medicine said plainly - "my meds have changed", "im on new tablets for my blood
# pressure", "my doctor changed my medication" - has nothing on the end of it, so no pool answers
# it and it reached the intake form: "Got it. Is there anything you'd like a hand with?" and "I'm
# listening - say more if it helps" both offer help with a task nobody mentioned. What is true for
# every one of them is the same two things: a changed dose or a new tablet takes a week or two
# before anybody can tell, and the pharmacist is the person who can say what to expect and what to
# do about a missed one. Nothing here reads the condition or the drug, so nothing can be said about
# either - that is the doctor's, and the falls, doses and symptom cards have their own turns.
A_MEDS = re.compile(
    r"\b(?:meds|medication|medications|medicine|medicines|tablets?|pills?|capsules?|dose|doses"
    r"|dosage|prescription|inhaler|inhalers|insulin|antidepressants?|antibiotics?|painkillers?"
    r"|statins?|steroids?|hormones?|patch|patches|injections?)\b", re.I)
# The change is what makes it a line worth answering: "my tablets are the blue ones" is a fact
# about a packet, and "my meds have changed" is the person telling you where they are with it.
A_MEDS_CHANGE = re.compile(
    r"\b(?:changed|change|changes|changing|new|started|starting|start|switched|switch|moved"
    r"|put me on|now on|instead of|upped|increased|lowered|reduced|stopped|come off|came off"
    r"|different|put on|been put|gone up|gone down|went up|went down"
    r"|twice a day|once a day|three times a day"
    # The change said as a swap or a step rather than an edit: "the chemist swapped my tablets",
    # "my dose was halved" and "im on a higher dose now" all reached the intake form, and the
    # medicine still has to be the person's own for any of them to count.
    r"|swapped|swap|halved|halve|doubled|higher|lower|stronger|weaker)\b", re.I)
# The medicine has to be the person's own. Somebody else's tablets are a question about them
# ("my mum keeps forgetting hers"), and a dose that has already gone wrong is the dose cards' -
# "too many", "double dose", "took 6" and an overdose are read before this and are left alone.
A_MEDS_MINE = re.compile(
    r"^(?:so |and |but |ok |okay |well |anyway |yeah |yeh |also )*"
    r"(?:my\s+(?:\w+\s+)?(?:meds|medications?|medicines?|tablets?|pills?|dose|dosage|prescription"
    r"|inhaler|insulin|antidepressants?|antibiotics?|painkillers?|statins?|steroids?|hormones?"
    r"|patch|patches|injections?)"
    r"|i(?:'?m| am)\s+(?:now\s+)?(?:on|taking)|ive|i(?:'?ve)?\s+been\s+(?:put\s+)?on"
    r"|i\s+(?:started|start|switched|changed|stopped|come off|came off)"
    r"|i\s+take\b|i(?:'?ve|\s+have|\s+got)\s+(?:some\s+)?(?:new\s+|different\s+|another\s+)?(?:meds"
    r"|medication|medicines?|tablets?|pills?|capsules?|inhaler|insulin)(?:\s+to\s+take)?"
    r"|(?:the|my)\s+(?:doctor|gp|consultant|nurse|psychiatrist)\s+(?:has\s+)?"
    r"(?:changed|put me on|switched|started me|gave me)"
    r"|i(?:'?m| am)\s+\w+\s+and\s+my\s+\w+\s+(?:have|has|was|were|is)\s+\w+ed"
    # The change said without naming who did it: "they switched my blood pressure tablets" was
    # filed back as a shrug, and nobody means a stranger - it is the surgery, the hospital or the
    # chemist, and the medicine still has to be named as theirs for the line to be this reading.
    r"|(?:they|he|she|the\s+(?:doctor|gp|consultant|nurse|psychiatrist|chemist|pharmacist"
    r"|hospital|surgery))\s+(?:have\s+|has\s+)?(?:changed|switched|swapped|put me on|started me on"
    r"|given me|gave me|moved me))", re.I)
# A symptom in the same line is a body question whatever else is in it - "my inhaler isnt working
# as well and im wheezing" is the breathing card's - so those lines keep their own turn.
A_MEDS_SYMPTOM = re.compile(
    r"\b(?:wheez\w*|breath\w*|chest|bleed\w*|rash|swollen|swelling|pain|hurts?|hurting"
    r"|dizzy|faint\w*|sick|vomit\w*|temperature|fever|numb|collapse\w*|seizure|fit"
    r"|too many|double|twice the|overdose|took \d|swallow\w*)\b", re.I)
A_MEDS_CHANGE_REPLY = (
    "A changed dose or a new tablet usually takes a week or two before you can tell what it is "
    "doing, so the pharmacist is worth one question: what to expect, and what to do about a "
    "missed one. They know more about the timing than anybody else on the high street.",
    "Give it a week or two before you judge it - most medicines take that long to settle - and ask "
    "the pharmacist about anything that bothers you in between rather than waiting for the next "
    "appointment. A missed dose is their kind of question too.",
)

# A subject on its own and nothing else. People type "cv", "pension", "car insurance",
# "sourdough starter" at a chatbot the way they type it into a search box: the subject is the
# whole message. Nothing in the store claims a line with no verb on it, so it reached the
# intake form ("Got it. Is there anything you'd like a hand with?", "Thanks for telling me - I'm
# here if you want to dig into any of that"), which answers a person who arrived with a subject
# by saying nothing about it. 24 of 29 bare subjects in a probe got a placeholder.
#
# What a friend does with "mortgage" is ask which end of it, and the two or three ends are the
# same for everybody: what you can borrow, which deal, what the paperwork means. So each family
# below is a question about the sub-asks people actually arrive with, not a claim about the
# world - nothing here says what a mortgage costs or what a CV should contain, which is the
# knowledge base's business. A subject the bot has no such question for keeps the floor.
A_SUBJECT_FAMILY = (
    # A subject on its own is an arrival, not a question, and a question back on its own is not an
    # answer. Each line here leads with the one thing that is true of the subject for everybody -
    # what it turns on, where the paperwork lives - then says where to look, then asks which end
    # of it they are on. No figures and no rules: those belong to the knowledge base.
    # `life insurance` is out of this one: it sat beside the mortgage words and got "a remortgage
    # turns on the rate you can get now", which is a lender's question about a rate. Life cover
    # is the amount, the term and what it pays out, so it reads with the insurance family below.
    (re.compile(r"\b(?:mortgages?|remortgag\w*|re-?mortgag\w*)\b"), (
        "A remortgage turns on the rate you can get now against the one you are on, plus the fee "
        "on top. Your lender's own figures and a broker's quote are the two to put side by side. "
        "Is this the borrowing side, picking a deal, or a letter from a lender?",
        "Mortgage paperwork comes down to the offer, the terms and the early repayment charge, "
        "and the pack they sent has each one written out. What are you trying to pin down - the "
        "amount, the deal, or something you have been sent?",
    )),
    (re.compile(r"\b(?:pensions?|state pension|workplace pension|company pension|personal "
                r"pension|annuit\w+)\b"), (
        "Pensions split into the state one, a workplace pot and one you may have lost track of, "
        "and each has its own place to look: the state forecast comes off your National "
        "Insurance record, and a workplace pot sends a statement each year. Which one is yours?",
        "A pension question is usually about how much is in it, when it can be taken, or what it "
        "is invested in, and the statement answers the first. Is this one you are paying into "
        "now, one you are about to draw, or one you are trying to find?",
    )),
    (re.compile(r"\b(?:council tax|energy bills?|electric(?:ity)? bills?|gas bills?|water "
                r"bills?|utility bills?|bills?)\b"), (
        "A bill comes down to the reading it was worked out from, the tariff you are on and any "
        "discount you are owed, and your supplier's account page shows all three for your "
        "address. Is it the amount that looks wrong, or more than you can carry this month?",
        "Energy, water and council tax each have their own account page and their own discount "
        "scheme, and the reading behind the figure is printed on the bill. Which bill is it?",
    )),
    # The two-word forms come before the bare "tax": the engine takes the first alternative
    # that matches at a position, so "tax code" would otherwise leave "code" behind and fall
    # through, and a bare "code" is a text message or a door, not a tax code.
    # A P45 and a P60 are tax documents, not pots: a P45 is the code to hand to the next job and
    # a P60 is the year's summary. They used to sit in the pension family and got "a pension
    # question is usually about how much is in it", which is a pot they are not.
    (re.compile(r"\b(?:tax returns?|tax codes?|tax rebates?|tax refunds?|self[- ]assessment|"
                r"p45s?|p60s?|tax|taxes|hmrc)\b"), (
        "Tax codes, returns and rebates are all worked out from your own record, and HMRC's "
        "personal tax account shows what they hold for you. Is it what you owe, something you "
        "can claim, or the form itself?",
        "A tax question is usually about what you owe, what you can claim back, or the form "
        "itself, and the record behind it is yours to see. Is this a first return, or one you "
        "have done before and something has changed?",
    )),
    (re.compile(r"\b(?:life insurance|life cover|term insurance|car insurance|home insurance|"
                r"contents insurance|travel insurance|insurance|insurances)\b"), (
        "An insurance question comes down to what is covered, the excess, and what you had to "
        "tell them, and all three are in the policy wording they sent you. Is it what it covers, "
        "what it costs, or a claim you are in the middle of?",
        "The cover, the excess and the exclusions are the three that decide an insurance "
        "question, and the wording you were sent names all three. Is this a quote, a claim, or "
        "something you are not sure you have to declare?",
    )),
    (re.compile(r"\b(?:cv|cvs|curriculum vitae|cover letters?|resume|job applications?)\b"), (
        "A CV is read in about a minute, so the last job, what you did in it and one line of what "
        "came of it do most of the work. Is it what to put in, what to cut, or shaping it for one "
        "advert?",
        "For most jobs one page and the recent years are enough, and the advert tells you which "
        "of your jobs it wants first. Is this starting one from nothing, or reworking one you "
        "already have?",
    )),
    # Only the words that mean self-assembly. A "wardrobe" or "bookcase" on its own is a piece of
    # furniture somebody may be moving, selling or measuring, and "is it what should be in the
    # box" is a confident guess about that - the flat pack is the subject this family can ask
    # about, so the line has to say flat pack or the shop that sells them.
    (re.compile(r"\b(?:flat[- ]?pack\w*|flatpack\w*|ikea|self[- ]assembly|assembl(?:y|ing)|"
                r"billy bookcase)\b"), (
        "Flat pack goes together in the order the sheet gives, and the parts are lettered, so a "
        "part missing from the box is usually a letter you have not got to yet. Which bit - the "
        "parts, the instructions, or getting it square on the wall?",
        "With flat pack the sheet is the authority: parts are lettered, and the fixings are in a "
        "bag with a count on it. Is it what should be in the box, the order, or one step that is "
        "not going in?",
    )),
    (re.compile(r"\b(?:woodworm|wood worm|damp|fence|fencing|guttering|boiler service|"
                r"loft insulation)\b"), (
        "Damp, woodworm and a leaking gutter are usually one job with a cause above it, and a "
        "trade tells you which in one visit. Is it what it is, how to treat it yourself, or who "
        "to get in?",
        "The cause is usually higher up than the symptom - a gutter, a roof edge, a bridged "
        "damp course - so a photo from outside is worth taking first. Is it a job you want to do "
        "yourself, or one for somebody with the right kit?",
    )),
    # The words here are the ones that can only be about a culture or a ferment. "bread" and
    # "stock" are not: a loaf is a recipe the knowledge base has, and a stock can be soup, a
    # shop's stock or livestock, so a question about what is feeding it would be a guess.
    (re.compile(r"\b(?:sourdough|yoghurt|yogurt|kefir|kombucha|kimchi|ferment\w*|"
                r"starter culture)\b"), (
        "A ferment is alive, so the look and the smell of it tell you more than the clock does. "
        "Is this getting one going from nothing, or one that has stopped working?",
        "A starter is flour and water and time, and what it does in the jar is the whole "
        "report. Is it the first few days, or the baking side of it?",
    )),
    # A bare `formula` is a guess: it is a baby's or a spreadsheet's. It takes a feeding word
    # with it before this family can say "with a baby it is usually readiness that decides it".
    (re.compile(r"\b(?:weaning|potty training|sleep training|teething|nappies|"
                r"(?:baby|infant|first|stage\s+\d|ready[- ]made|powdered)\s+formula|"
                r"formula\s+(?:milk|feed|feeds|feeding))"
                r"(?:\s+(?:advice|help))?\b"), (
        "With a baby it is usually readiness that decides the timing, and the signs show before "
        "anything needs doing. Is this when to start, or what to do now it has started?",
        "Most of these come down to what the child is doing already rather than the calendar. Is "
        "it the timing you are unsure of, or something that is already not working?",
    )),
    # A warning light is its own subject: the handbook names the light and a garage reads the
    # code, while an MOT is a date and a price. One pool cannot fit both, so it gets its own.
    (re.compile(r"\b(?:warning light|warning lights|engine light|light on the dash)\b"), (
        "The handbook has a page for every light on the dash and says which ones mean stop now, "
        "and a garage can read the code behind it in minutes. Which light is it, and is the car "
        "still driving normally?",
        "Every light on that dash has one meaning for your model, printed in the handbook, and "
        "the code behind it is what a garage plugs in to read. Is it on all the time, or only "
        "now and then?",
    )),
    (re.compile(r"\b(?:mot|mots|car service|bike chains?|brakes?|clutch)\b"), (
        "An MOT is the safety check and a service is the upkeep, and the garage's sheet lists "
        "what each one covers for your car. Is it the date, the price, or doing it at home?",
        "The garage's own sheet says what a check or a repair covers and what it charges, and the "
        "handbook says how often the maker wants each one. Is it whether it needs doing, what it "
        "should cost, or how long the car will be off the road?",
    )),
    # A bare `renewal` or `renewing` is not a family word: it could be a passport, a season
    # ticket, a licence or a car insurance. It says passport only with the thing being renewed
    # beside it, and stands down on the bare word. The two-word forms come first, or
    # "passport renewal" leaves "renewal" behind and stands down anyway.
    (re.compile(r"\b(?:(?:passport|licence|license|visa)\s+renew(?:al|als|ing)?|"
                r"renew(?:al|als|ing)?\s+(?:of\s+)?(?:my\s+|your\s+|the\s+)?"
                r"(?:passport|licence|license|visa)|"
                r"renew(?:ing)?\s+(?:my\s+|your\s+|the\s+)?"
                r"(?:passport|licence|license|visa)|"
                r"passports?|visas?|driving licences?|driving license|licences?|license|"
                r"provisional)\b"), (
        "A renewal runs off your old document and a photo that meets the rules, and the official "
        "site takes you through the rest. Is this applying, renewing, or how long it takes?",
        "The form is the same one every time; what changes is the photo and what you have to "
        "send with the old document. Is it the form, the timing, or what they will want from "
        "you?",
    )),
    (re.compile(r"\b(?:childcare|nursery|childmind\w*|childminder|wrap[- ]around care|"
                r"after[- ]school club)\b"), (
        "Nursery places are booked months ahead and the inspection report for each one is "
        "public, so the visit and the report are what decide it. Is it the cost, finding a "
        "place, or what they will actually do with them?",
        "A childminder and a nursery are held to the same inspection, and the report says what "
        "the last visit found. Is this choosing the place, or the money side of it?",
    )),
    (re.compile(r"\b(?:first aid|first[- ]aid|a first aid kit|resuscitat\w+|cpr)\b"), (
        "First aid is the same few steps every time - danger, response, breathing, then help - "
        "and a course is where the practice comes from. Is this a situation you are in now, or "
        "getting ready for one?",
        "The steps are the easy part; doing them on a person is what a course gives you. Is it "
        "now, or the kit and the course?",
    )),
)

# The words that can sit around a subject without changing what the line is: "my cv", "any "
# advice on my pension", "help with the mortgage", "car insurance please". A line with anything
# else in it names a verb or a number, so it is an account of something ("we got a mortgage",
# "my mortgage is 400") and belongs to the readings above rather than here.
A_SUBJECT_FILLER = frozenset("""
    a an the my our your his her their its some any this that these those new old first second
    help advice question info information please thanks thank re again about on for of to with
    and or so just quick quickly bit little lot too more most starter
""".split())

# A furniture word can sit beside the flat-pack word without making the line an account:
# "ikea wardrobe", "flat pack desk". On their own they are not this family's subject.
A_SUBJECT_BESIDE = frozenset("""
    wardrobe wardrobes bookcase bookcases desk desks drawer drawers table tables chair chairs
    bed beds shelves shelving unit units kitchen bedroom office
""".split())


def _a_subject_alone(text):
    """The family for a line that is nothing but the name of a subject, else None.

    Every family word is stripped out of the line first, so "ikea wardrobe" and "tax return"
    are two subjects and not a subject with a word left over. What is left has to be filler
    ("my cv", "help with the boiler service") or the line names a verb or a number and belongs
    to the readings above.
    """
    stripped = text
    family = None
    for pattern, lines in A_SUBJECT_FAMILY:
        if not pattern.search(stripped):
            continue
        family = family or lines
        stripped = pattern.sub(" ", stripped)
    if family is None:
        return None
    if [w for w in re.findall(r"[a-z']+", stripped)
            if w not in A_SUBJECT_FILLER and w not in A_SUBJECT_BESIDE]:
        return None
    return family


def _a_statement(clean):
    """The line when it is an account and not a question, else None."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text or A_QUESTION_OPENER.match(text):
        return None
    if A_QUESTION_ANYWHERE.search(text):
        return None
    # "my meds have changed" is four words and "im on new tablets" is four; a state of the
    # person's own said that short is still a line rather than a fragment, so the length floor
    # only holds for the families that need the detail of a sentence to read.
    if len(text.split()) < 3 and not (A_MEDS.search(text) and A_MEDS_CHANGE.search(text)):
        return None
    return text


def pool(clean, understood=None, memory=None):
    """One thing that is true about what the line names, or None when it names nothing."""
    # A subject and nothing else is read before the three-word floor below, because "cv" and
    # "car insurance" are two words and neither is a statement to be answered - it is a person
    # who has arrived with a subject. Whole-line only: a question mark, a question word or any
    # word that is not filler around the subject leaves it to the readings above.
    whole = " ".join(str(clean or "").lower().split())
    if whole and "?" not in whole and not A_QUESTION_OPENER.match(whole) \
            and not A_QUESTION_ANYWHERE.search(whole):
        family = _a_subject_alone(whole)
        if family:
            return family
    text = _a_statement(clean)
    if text is None:
        return None
    if (A_STANDING.search(text) and _has(text, POSTURAL)) or (
            _has(text, ("vision", "eyes", "sight")) and A_STANDING.search(text)):
        return A_STANDING_UP
    if _has(text, WATER_THINGS) and A_WATER_TROUBLE.search(text):
        return WATER_IN_THE_HOUSE
    if A_PAY_OWN.search(text) and A_SHORT_PAY.search(text) and not A_PAY_SOMEBODY_ELSE.search(text):
        return SHORT_PAY
    if A_BABY.search(text) and A_FEED.search(text) and A_FEED_FIGHT.search(text):
        return A_FEED_FIGHT_REPLY
    if A_BABY.search(text) and AN_AGE_UNDER_A_YEAR.search(text):
        return UNDER_A_YEAR
    if A_SHIFT.search(text) and AN_EARLY_HOUR.search(text):
        return EARLY_START
    if (A_MEDS.search(text) and A_MEDS_CHANGE.search(text) and A_MEDS_MINE.match(text)
            and not A_MEDS_SYMPTOM.search(text)):
        return A_MEDS_CHANGE_REPLY
    if _a_visit(text):
        day = A_VISIT_DAY.search(text)
        word = day.group(1).lower()
        return tuple(line.format(day=word, Day=word[:1].upper() + word[1:])
                     for line in _the_visit_family(text))
    return None
