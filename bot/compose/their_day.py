"""A question about something of the person's own, when only they were there.

"how was the trip", "how was the wedding", "how is work", "were the kids ok", "did the doctor
ring", "what did the vet say". Nothing in the modules can answer these, because the answer is
not in any record: the person was there and the bot was not. What happened on main is that they
reached the search hedge:

    how was the wedding -> A quick search online will get you a solid answer
    did the doctor ring -> A pharmacist or your GP can answer that today
    were the kids ok    -> A quick search online will get you a solid answer

Telling somebody to go and look up their own wedding is the worst line in the pool, and it is
the one a person gets for asking the thing they most want to talk about. The memory store
already answers the version of the same ask with a name in it ("how did the interview go" gets
"You tell me - how did the interview go?"), so the bot is doing the right thing in one branch
and the wrong thing in the other.

What a friend does is the same thing without the name: say that it is theirs to tell, and ask
it back in their own words. No search engine, and no guess at how it went.

The reading is deliberately a list of the things a person is present for - a trip, a shift, a
scan, the kids, the dog - rather than any noun after "how was". A fact nobody had to witness
("how was the titanic built") belongs to the knowledge base, and how something was done ("how
was the car fixed", "how was the trip paid for") is a lookup; the trailing participle is what
tells those apart from "how did the car go". A machine or a record that another lane owns
("has my parcel arrived yet", "is the car ok now", "how was the boiler") is left to that lane,
and the bot's own day ("how was your day", "hows your day going") is chat's to answer.

A fact of theirs is the same family and reaches the same hedge. "whats my rent again", "is my
holiday next week", "does my mum like golf" and "and what size did i say" have no record in this
bot and no place to look them up: the answer is in the person's own head, their own calendar,
their own paperwork, or the head of somebody they know. Telling them to search the web for their
own rent is the worst line in the pool for the second time, so the reading here says the bot
cannot see it, names the thing that would have it - a statement, a confirmation email, the person
themselves - and asks the question that moves the talk on. It never guesses a figure, a date or a
taste (`own_fact_for`).
"""
import re

from . import pick

# The opening: an optional filler ("so", "and", "ok"), an optional "any idea", then how/what and
# a verb that is allowed to be missing ("any idea how the kids got on").
_HOW = re.compile(
    r"^\s*(?:(?:so|and|but|ok|okay|well|then|just|right|anyway|oh|hmm|yeah|yes|alright)\s*,?\s+)*"
    r"(?P<ask>(?:any\s+idea|do\s+you\s+know)?\s*(?:how|what)\s*"
    r"(?:(?:was|were|did|have|has|is|are)\s+)?)(?P<rest>.*)$", re.I)
# The thing they were there for. A list rather than any noun, because "how was the titanic built"
# is a fact nobody had to witness and belongs to the knowledge base, not here.
_THING = re.compile(
    r"^\s*(?:(?:the|your|his|her|their|my|our)\s+)?(?:(?:new|first|last|old|big)\s+)?"
    r"(?:night out|first day|last day|day out|trip|holiday|honeymoon|wedding|weekend|break|party|"
    r"dinner|meal|lunch|flight|journey|drive|move|interview|exam|exams|test|tests|scan|"
    r"appointment|match|game|play|concert|show|meeting|presentation|shift|course|day|week|"
    r"morning|afternoon|evening|night|kids|children|boys|girls|family|mum|mom|dad|sister|"
    r"brother|son|daughter|baby|dog|cat|puppy|kitten|vet|doctor|dentist|hospital|school|"
    r"nursery|work|job|uni|house|flat|viewing|results|date|today|yesterday|session|class|lesson|"
    r"stay|audition|driving test|theory test|appraisal|surgery|procedure|operation|court|hearing)\b",
    re.I)
# The words that may trail a state ask without changing what is being asked.
_AFTER = (r"(?:\s+(?:yet|now|today|tomorrow|though|then|again|back|at all|about it|with that|with it"
          r"|hear|heard|reply|replied|get back|got back|call back|ring back|phone back|to you"
          r"|these days|so far|alright|ok|okay|fine|good|in the end|anything|something|either"
          r"|at the vets|at the hospital|at the doctor"
          # "did the school ring about him", "did they get back to you about it": the tail is who
          # the call was about, and it does not change the question.
          r"|about\s+(?:him|her|them|it|that|this|me|us|the\s+\w+)"
          r"|at\s+(?:school|nursery|work|home|uni|college)"
          r"|with\s+(?:the|his|her|their|my|our)\s+\w+)){0,2}\s*[?.!]*$")
# What may follow the thing: the verb the ask is made of, and nothing else. "how was the car
# fixed" and "how was the trip paid for" are questions about how something was done, which is a
# lookup, and the trailing participle is what tells them apart from "how did the car go".
_TAIL = re.compile(
    r"^(?:\s+(?:go|went|do|going|get on|got on|get along|turn out|end up|come out|hold up)\b)?"
    r"(?:\s+(?:today|tonight|yesterday|last night|last week|then|though|so far|in the end|again|"
    r"yet|all right|alright|ok|okay|fine|good)){0,2}"
    # "how was the meeting with the boss", "how was the trip with the kids": who it was with is
    # part of the same ask, not a different question.
    r"(?:\s+with\s+(?:the|his|her|their|my|our|your)\s+\w+)?\s*[?.!]*$", re.I)
# The bare version, which is the commonest follow-up there is: "how did it go", "how did they go".
# The store answers it when it can read what "it" was; when it cannot, the honest reply is the same
# hand-back, not a search engine.
_PRONOUN = re.compile(
    r"^\s*(?:and\s+|so\s+|but\s+|ok\s+|okay\s+|well\s+)?"
    r"how\s+(?:did|was|were)\s+(?:it|that|this|they|he|she)"
    r"(?:\s+(?:go|went|get on|got on|get along|turn out|come out|work out)\b[^?]*"
    # The same follow-up with nothing after the pronoun at all: "how was it", "how was it then".
    # "how was it made" and "how was it done" are questions about how something was done, and the
    # tail list is what keeps them out.
    r"|(?:\s+(?:then|though|today|tonight|last night|in the end|overall|really|so far)){0,2})"
    r"[?.!]*$", re.I)
# Somebody who owes them a visit, a call or an answer. The trade is the commonest version of the
# question there is - "did the plumber come", "did the boiler man show up", "did the care home get
# back to you" - and it was reaching the composer's who-to-ask line ("A plumber or electrician will
# spot it in minutes"), which is written for a symptom rather than for a person who already had one
# round. Kept as one list so the ask shapes below that read the same people cannot drift apart.
_PEOPLE = (
    r"vet|doctor|dentist|optician|physio|counsel\w*|consultant|nurse|midwife|surgeon|"
    r"plumber|electrician|builder|roofer|locksmith|mechanic|garage|glazier|decorator|"
    r"engineer|delivery\s*(?:man|driver)?|courier|driver|agent|estate\s+agent|letting\s+agent|"
    r"(?:boiler|gas|window|bathroom|kitchen|damp|carpet)\s*(?:man|lady|fitter|guy|person|"
    r"people|firm|company)|"
    r"recruit\w*|agency|recruitment\s+agency|employer|manager|boss|hr|payroll|"
    r"hospital|school|nursery|college|university|uni|council|job\s*centre|dwp|hmrc|"
    r"passport\s+office|dvla|care\s+home|social\s+worker|bank|building\s+society|landlord|"
    r"solicitor|conveyanc\w*|broker|insurer|insurance|mortgage\s+(?:man|adviser|advisor)?"
)
# The state of it, rather than how it went: "were the kids ok", "was the scan all right",
# "did the doctor ring".
_STATE = re.compile(
    r"^(?:is|are|were|was|did|does|do|has|have)\s+(?:(?:the|your|my|our)\s+)?"
    r"(?:kids|children|boys|girls|family|mum|mom|dad|sister|brother|son|daughter|baby|dog|cat|"
    r"puppy|kitten|" + _PEOPLE + r"|"
    r"scan|appointment|interview|exam|test|"
    r"results|party|wedding|trip|flight|match|game|bank|council|landlord|solicitor|"
    r"boiler|car|washing\s+machine|parcel|parcels|order|delivery|package|"
    # The work done on the house, which is the same question as the trade that did it: "did the
    # roof hold up", "did the fence get done", "is the bathroom finished".
    r"roof|fence|extension|bathroom|kitchen|drive|driveway|paving|patio|garden|shed|loft|"
    r"wall|floor|flooring|door|doors|window|windows|radiator|gutter|gutters|drain|drains|"
    r"chimney|damp\s*course)\b"
    r"\s+(?:ok|okay|all right|alright|fine|good|bad|home|yet|back|there|asleep|awake|ring|call|"
    r"phone|say|said|come|came|turn up|turned up|show|go|went|do|done|arrive|arrived|land|landed"
    r"|got back|get back|hear|heard|reply|replied|say anything|say something|got there"
    r"|show up|showed up|show up yet|turn up yet|come yet|came yet|got to (?:school|work|the "
    r"hospital|the vets?|nursery)|get to (?:school|work)|hear back|heard back|ring back|call back"
    r"|phone back|been in touch|get in touch|get back to (?:you|me)|got back to (?:you|me)"
    r"|confirmed|come through|come back|come back ok|got sorted|been round|been out"
    r"|hold up|held up|get done|got done|get home|got home|go ok|go alright|been done)\b"
    # A tail of its own makes it a different question: "is it ok to eat this" is not asking how
    # somebody's day went.
    + _AFTER, re.I)
# The same with a pronoun in place of the thing, and only the states a day of theirs can be in: a
# bare "is it done" or "did it go" is a follow-up about something on the go, and the right reply to
# that is how to tell, not "you tell me".
_STATE_BARE = re.compile(
    r"^(?:is|are|were|was|did|has|have)\s+"
    # "they" is always somebody of theirs; "it" is as often a thing on the go.
    r"(?:(?:they|he|she)\s+(?:ok|okay|all right|alright|fine|good|bad|home|yet|back|there|asleep"
    r"|awake|ring|call|phone|say|said|come|came|turn up|turned up|arrive|arrived|land|landed|show"
    r"|go|went|do|done|got back|got there)"
    r"|it\s+(?:ok|okay|all right|alright|fine|good|bad|home|yet|back|there|asleep|awake|ring|call"
    r"|phone|said|came|turned up|arrived|landed|got back|got there))\b" + _AFTER, re.I)
# The same question with names in it: "were jess and tom there", "were you there". Nobody can read
# two names and check whether they turned up.
_NAMES = re.compile(r"^(?:were|was)\s+[a-z']+(?:\s+and\s+[a-z']+)?\s+there\b[^?]*[?.!]*$", re.I)
# "did you hear back from the bank", "have they got back to you": the follow-up after somebody said
# they would ring. The bot has no record of anybody's calls, so the honest reply is the same
# hand-back - and on main it was the search hedge.
_HEARD_BACK = re.compile(
    r"^\s*(?:and\s+|so\s+)?(?:did|do|does|have|has|had)\s+"
    r"(?:you|they|he|she|we|anybody|anyone|somebody|someone|nobody)\s+"
    r"(?:hear|heard|get|got|have|had)\s+(?:back|anything|something|any\s+news|a\s+reply|"
    r"an\s+answer|word)\b[^?]*[?.!]*$", re.I)
# What somebody else told them, which is the same shape: "what did the doctor say" is not a
# lookup, and the answer is in their own kitchen, not on a website.
_SAID = re.compile(
    r"^\s*(?:and\s+)?what\s+(?:did|do|does)\s+(?:(?:the|your|my|our)\s+)?"
    r"(?:" + _PEOPLE + r"|teacher|head|she|he|they)\s+"
    r"(?:say|said|tell you)\b[^?]*[?.!]*$", re.I)
# The bot's own day, which is chat's to answer: "how was your day" is the person asking after the
# bot, not handing it one of theirs, and echoing it back would be the bot asking itself.
_ABOUT_THE_BOT = re.compile(
    r"^\s*(?:how|what)\s+(?:was|is|were|did|does|do|has|have|'s|s|'d|d)?\s*yours?(?:elf)?\b",
    re.I)
# What the bot says instead: it says what it does not have, and asks, in their words, the question
# that was theirs to answer. Four ways in, because four chats in a row with one sentence in them
# read like a form letter.
LINES = (
    "You tell me - {ask}?",
    "I wasn't there, so you know better than me - {ask}?",
    "Only you know that one. {Ask}?",
    "No way for me to know that from here - {ask}?",
)
# After a death or a diagnosis the echo has to be gentler: "you tell me" is the right hand-back
# to a wedding and a cold one to a scan that might not have gone well.
CARE_LINES = (
    "I have no way of knowing, and I would rather ask than guess - {ask}?",
    "That is yours to tell me, and I am listening - {ask}?",
    "I hope it went as well as it could. {Ask}?",
)


# The composer's "who to ask" lines: "A pharmacist or your GP can answer that today", "Your vet
# is the one to ask", "A plumber or electrician will spot it in minutes". Each is a good reply to a
# symptom and the wrong one to "what did the vet say" or "did the plumber come", where the person
# has already been to them and is telling the bot how it went.
#
# Every one of them is taken from the composer's own data rather than copied: a line added there
# is covered here the day it is written, and a line reworded there cannot leave a stale copy
# behind. The rows of WHO_TO_ASK are (words, line) pairs; the single lines are the module's own
# ALL_CAPS names ending in _WHO.
from . import fallback_data as _data

WHO_TO_ASK = tuple(sorted(
    {who for _words, who in _data.WHO_TO_ASK}
    | {value for name, value in vars(_data).items()
       if name.endswith("_WHO") and isinstance(value, str)}
))


def pool_for(text, care=False):
    """The lines for a question about something of their own, or None.

    `care` is the pool after a death or a diagnosis: "you tell me" is the right hand-back to a
    wedding and a cold one to a scan that might not have gone well.
    """
    ask = reads(text)
    if not ask:
        # A typo or a laugh on the end - "hows the weddng", "how did the trip go lol" - is the
        # same question, and the understanding engine already has the spelling of it. It is asked
        # for here rather than passed in, because this is reached from the module that answers
        # last, where only the typed line is in hand.
        from ..understanding import understand
        ask = reads(understand(text).get("plain") or "")
    if not ask:
        return None
    said_back = ask[:1].upper() + ask[1:]
    return tuple(line.format(ask=ask, Ask=said_back) for line in (CARE_LINES if care else LINES))


def reads(clean, repaired=None):
    """The ask it is theirs to answer, in their own words, or None.

    `repaired` is the understanding engine's spelling back of the same line. It is only read, never
    echoed: "hows the weddng" is asked back as they typed it, and a line with a typo or a "lol" on
    the end is the same question as the clean one.
    """
    text = " ".join(str(clean or "").lower().replace("\u2019", "'").split())
    if not text or len(text.split()) > 14:
        return None
    # The contraction people actually type, read as the words it stands for so one set of shapes
    # covers both: "how's work" is "how is work". The echo below is the words they typed.
    plain = " ".join(str(repaired or "").lower().replace("\u2019", "'").split())
    match = " ".join(re.sub(r"\bhow'd\b|\bhowd\b", "how did",
                            re.sub(r"\bhow's\b|\bhows\b", "how is", plain or text)).split())
    # The bot's own day is chat's to answer, in every tense and with every noun: "how did your day
    # go" and "hows your day going" are the person asking after the bot, not handing it theirs.
    if _ABOUT_THE_BOT.match(text) or _ABOUT_THE_BOT.match(plain) or _ABOUT_THE_BOT.match(match):
        return None
    # Asked back in the words they typed, with the apostrophe they left out put in: "hows the job
    # going" is not something to hand back to somebody who is talking to a friend.
    ask = re.sub(r"^hows\b", "how's", re.sub(r"^howd\b", "how'd", text)).strip().rstrip("?.! ")
    how = _HOW.match(match)
    if how:
        rest = how.group("rest")
        thing = _THING.match(rest)
        if thing and _TAIL.match(rest[thing.end():]):
            return ask
    for pattern in (_STATE, _STATE_BARE, _SAID, _HEARD_BACK, _PRONOUN, _NAMES):
        if pattern.match(match):
            return ask
    return None


# ---------------------------------------------------------------------------------------------
# A fact of theirs: the one thing in the talk that nothing here holds.
#
# Three buckets and no more, because the way to find the thing is what decides the reply: a figure
# is on a statement, a date is in a confirmation, and a thing a policy covers is in the wording. A
# line that fits none of them stands down (returns None) and the hedge answers as it did before.
#
# This is the half of the shape that a document answers, and it is the half nobody else has: the
# "only you know" reading (own_facts, #9101) is right for a middle name and wrong for a rent, and
# "does my mother like golf" belongs with the reading of other people, not here.

# Money going out, and what is owed: "whats my rent again", "how much is my council tax". The bare
# utility nouns ("phone", "gas", "water") are not here: "is my laptop older than my phone" is not a
# bill question, and a bill question has the bill in it.
OWN_FIGURE = ("rent", "mortgage", "council tax", "bill", "bills", "premium", "tariff",
              "direct debit", "payment", "payments", "balance", "deposit", "service charge",
              "arrears", "fee", "fees", "subscription", "charges", "salary", "wage", "wages",
              "pension", "loan", "overdraft", "interest", "standing order", "outgoings")
# A day something happens or runs out: "is my holiday next week", "when is my mot".
OWN_DATE = ("holiday", "holidays", "appointment", "appointments", "booking", "bookings", "flight",
            "renewal", "mot", "service", "deadline", "contract", "tenancy", "delivery", "check-in",
            "checkin", "expiry", "expires", "collection", "pick up", "pickup", "completion",
            "install", "installation", "viewing", "moving date", "move date", "end", "ends",
            "ending", "runs out", "run out", "run out date")
# What a policy covers is a different document from a bill, and a different question: "is my phone
# covered on holiday" wants the wording, not a figure. Read before the money words because
# "insurance" is in both.
OWN_POLICY = ("insurance", "policy", "policies", "cover", "covered", "covers", "covering",
              "warranty", "guarantee", "excess", "claim", "claims", "protected", "included",
              "excluded")
# Nothing here writes any of it down, so the reply says so in words: what the bot cannot see, the
# thing that has it, and the one question that moves the talk on.
OWN_FIGURE_LINES = (
    "I can't see your account, sorry. That figure is on your last statement or in the app for it, "
    "and the provider will read it out if you ring.",
    "Nothing of yours is in front of me. Your statement or that provider's app has the exact "
    "amount; if it looks wrong, they are the ones to ring.",
    "I've no way to check your own bills. The last email or statement has it, and the payments in "
    "your banking app usually show it too.",
)
OWN_POLICY_LINES = (
    "I can't read your policy from here, sorry. What it covers is in the schedule or the policy "
    "document, and the insurer will confirm it on the phone in a couple of minutes.",
    "Nothing of yours is in front of me. The policy wording has it under what is covered; a call "
    "settles it faster than reading it.",
    "I can't check a policy I can't see. The schedule that came with it lists what is covered and "
    "what the excess is, and the insurer can read it back to you.",
)
OWN_DATE_LINES = (
    "I can't see your diary, sorry. It will be in the confirmation email or the text they sent "
    "when you booked - tell me what it says and I'll help you plan around it.",
    "No way to see your own dates from here. The booking email or the calendar on your phone has "
    "it, and whoever you booked with can confirm it in a minute if not.",
    "I can't look at your own diary. The confirmation email is the first place: it is in there "
    "nine times out of ten.",
)
# The person's own taste, which is theirs for the same reason: "do i like anchovies". Only the
# four verbs of taste: "do i need a cable for that" and "do i want to go" are questions about a
# step or a plan, and they have answers of their own. A pronoun
# after the verb is a thing already in the talk ("do i like it") and the thread answers that, so
# the taste has to be named for this reading to have anything to say.
# "do i like my job" is the same four verbs and is not a taste: nobody finds that out with one
# mouthful, and "have it and see" is a sentence about a dish. A job, a course, a place to live is
# a life choice, and the honest answer is that only they can say, with the question that decides
# it handed back.
_A_LIFE_CHOICE = re.compile(
    r"(?:\b(?:my|our)\s+(?:\w+\s+){0,2}(?:job|jobs|work|career|boss|team|school|college|uni|"
    r"university|course|degree|flat|house|home|town|city|country|area|class|gym|club|hobby|"
    r"subject|placement|apprenticeship|business|role|position)\b"
    r"|\bwhere\s+i\s+(?:live|work|am)\b)")
_OWN_TASTE = re.compile(
    r"\b(?:do|would|will|am|did)\s+i\s+(?:even\s+)?(?:like|love|hate|enjoy|prefer)\s+"
    r"(?!it\b|that\b|this\b|them\b|those\b|these\b|one\b|him\b|her\b)")
OWN_LIFE_LINES = (
    "Only you can say, and I don't want to guess at it for you. What is making you wonder?",
    "That one is yours to answer. What would make it better for you - more of something, or less "
    "of something?",
)
OWN_TASTE_LINES = (
    "You know that one better than I do - taste is the one thing nobody can check for you. The "
    "worst case is one mouthful.",
    "Only you can say. Have it and see - what you fancy is not something anyone can tell you.",
    "That is yours to know. Taste changes, too, so the last time is worth trying again.",
)
# The shapes that ask for advice rather than for a fact: a how-to wants a step, and the modules
# that give steps answer it. They stand the reading down before anything is bucketed.
_ASKS_FOR_ADVICE = re.compile(
    r"^\s*(?:(?:so|and|ok|okay|well|then|right|but)\s*,?\s+)?"
    r"(?:how\s+(?:do|can|could|should|would|to|might)\b|what\s+(?:should|could|can|do)\s+i\b|"
    r"where\s+(?:can|do|should|could)\s+i\b|any\s+(?:advice|ideas|tips)\b|"
    r"is\s+it\s+(?:ok|okay|worth|better|cheaper|cheapest|possible)\b|"
    r"am\s+i\s+(?:better|allowed|able)\b)")
# A question, in the words people type it: a question mark anywhere, or an ask word in the first
# three words, because "whats my rent again" has no question mark and is the commonest shape of
# all. "i do my own garden" is not a question and is not read as one.
_ASKS = re.compile(r"\?|\b(?:what|whats|what's|when|where|which|how|is|are|was|were|do|does|did|"
                   r"has|have|can|could|should|am)\b", re.I)
# "my <a thing>", with up to two words between: "my rent", "my car insurance renewal", "my
# account number". The thing is read from what follows, so nothing else in the line can stand in
# for it.
_MINE_AND_THING = re.compile(r"\b(?:my|our)\s+(?P<thing>[a-z][a-z' ]{0,40})")
# A line about how a figure is worked out ("does paye come out of my wages", "is the service
# charge added to my rent") asks what the rule is, not what the amount is: the number in their
# statement is not the answer to it, and the reading has to stand down so the knowledge module or
# the composer keeps the turn.
_A_COMPOSITION = re.compile(r"\b(?:comes?\s+out\s+of|coming\s+out\s+of|deduct\w*|(?:take|takes|taken|taking)\s+(?:\w+\s+){0,2}off|"
                            r"added\s+(?:on|to)|on\s+top\s+of|worked\s+out|calculated)\b")
# A number or a code of theirs is a reference, not a figure and not a policy: "whats my national
# insurance number" is the shape of "whats my booking reference", which the paperwork lane answers.
# Reading "insurance" as a policy there would hand back the wording of a policy they never named,
# so the identifier shapes stand down and leave the turn to the reader that knows references.
_AN_IDENTIFIER = re.compile(r"\b(?:numbers?|sort\s+code|reference|ref|licence|license|pin|"
                            r"username|password|log\s?in)\b")
# "when is my insurance renewal" asks for a day, and the date words are where a day is kept, even
# though the same line names the policy. A line that asks when is read that way round.
_A_WHEN = re.compile(r"\b(?:when|what\s+date|which\s+date|how\s+long|how\s+soon|due)\b")
# A date that is a medical one, which is on the notes rather than in a booking email.
_NOT_A_DIARY = re.compile(r"\b(?:due|baby|pregnan\w*|midwife|scan|test results|biopsy)\b")
# A tenancy deposit is held in a scheme, and the certificate for it comes from whoever took it,
# so no document of theirs holds the answer: "is my deposit protected" and "is my deposit safe"
# were read as a figure and as a policy, and neither is the thing being asked about.
_A_DEPOSIT = re.compile(r"\bdeposits?\b")


def own_fact(text, memory=None):
    """The bucket a question about a fact of theirs belongs in, or None.

    `kind` is "figure", "date", "policy", "taste" or "life".
    """
    line = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    if not line or len(line.split()) > 14:
        return None
    if _ASKS_FOR_ADVICE.match(line) or not _ASKS.match(" ".join(line.split()[:3])):
        return None
    if _A_LIFE_CHOICE.search(line):
        return ("life", "")
    if _OWN_TASTE.search(line):
        return ("taste", "")
    # The possessive has to be on the thing itself ("my rent", "my car insurance renewal"), not
    # somewhere else in the line: "my name's not on anything" is not a question about a figure,
    # and "is my laptop older than my phone" is not either.
    mine = _MINE_AND_THING.search(line)
    if not mine:
        return None
    thing = mine.group("thing")
    # A due date is on the notes the midwife gave them, not in a booking email, and the pregnancy
    # lanes have their own lines.
    if _NOT_A_DIARY.search(line):
        return None
    if _A_DEPOSIT.search(line):
        return None
    if _AN_IDENTIFIER.search(line):
        return None
    order = (("policy", OWN_POLICY), ("figure", OWN_FIGURE), ("date", OWN_DATE))
    if _A_WHEN.search(line):
        order = (("date", OWN_DATE), ("policy", OWN_POLICY), ("figure", OWN_FIGURE))
    for kind, words in order:
        if not any(re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", thing)
                   for word in words):
            continue
        # "does paye come out of my wages" is a question about the rule, not about their number.
        if kind == "figure" and _A_COMPOSITION.search(line):
            return None
        return (kind, "")
    return None


def own_fact_for(text, memory=None):
    """The reply for a question about a fact of theirs, or None.

    Read from the line as typed; a spelling the understanding engine repairs is not needed here,
    because the nouns that decide the bucket are short and common. Only a hedge is replaced, so a
    line with an answer of its own never reaches this.
    """
    read = own_fact(text)
    if not read:
        return None
    kind = read[0]
    pool = {"figure": OWN_FIGURE_LINES, "date": OWN_DATE_LINES, "policy": OWN_POLICY_LINES,
            "taste": OWN_TASTE_LINES, "life": OWN_LIFE_LINES}[kind]
    return pick(pool, memory or {}, str(text or "").lower())
