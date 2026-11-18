"""Waiting for an answer about a body is not a bad day at work.

Five lines were answered by the generic pool, whose warmest line is "That sounds rough. If you
want, I can help you think through what to do next." - the line a person gets for a missed bus, said
to somebody in the fortnight between a scan and an answer:

    they think its cancer            -> "That sounds rough. If you want, I can help you..."
    theyre testing me for cancer     -> "Ugh, that's a lot to carry."
    my mum might have cancer         -> "I'm sorry - that's frustrating. Want a hand..."
    im worried about my results      -> "Nerves before something big are normal..."  (the driving test)
    its not cancer                   -> "Sorry to hear that."   (the opposite of the news)

Nothing is known yet in four of them, and the fifth is the news going the right way, so no card and
no pool for a bad day is the right thing to say. What is knowable is the wait itself and the one
thing worth doing in it, and that is what this file says - it holds no fact about the world, so it
cannot be wrong about it.

Three readings, one direction each: the wait about the person's own body, the same wait about
somebody they love (a different question, and a different pool), and the serious thing ruled out.

A module reads these when the composer's own reply is one of the generic ones
(bot/modules/the_wait_about_a_body.py); a card, an entry or a pool that names the condition keeps the
turn.
"""
import re

from . import pick

# A condition with a name, said about the person typing rather than about somebody they love. The
# words are the ones no doctor hands out for a bad week: a cancer, a tumour, leukaemia, motor
# neurone. "i have a migraine" and "my back has gone" are left where they are.
OWN_SERIOUS_CONDITION = re.compile(
    r"\b(?:cancers?|tumou?rs?|leuka?emia|lymphoma|myeloma|melanoma|mesothelioma|"
    r"motor neurone|multiple sclerosis|huntington\w*|parkinson\w*|alzheim\w*|dementia|"
    r"cerebral palsy|muscular dystrophy|cirrhosis|copd|emphysema|motor\w* disease|"
    r"heart failure|kidney failure|terminal|palliative|metasta\w+|malignant|carcinoma|"
    r"\bm\.?s\.?)\b", re.I)
# A finding on a scan is the condition before anybody has used the word for it: "ive got a shadow on
# my lung", "they found something on the scan". The organ has to be named, so a spot on a face is
# still a spot, and "something" only counts after a scan or a doctor.
A_FINDING = re.compile(
    r"\b(?:a\s+)?(?:shadow|mass|growth|nodule|spot|something)\s+(?:on|in)\s+(?:my|the|his|her)\s+"
    r"(?:lung|lungs|breast|kidney|kidneys|liver|bowel|brain|prostate|womb|uterus|cervix|ovary|"
    r"ovaries|thyroid|skin|colon|pancreas|bladder|spine|bone|bones|chest|lymph)\b|"
    r"\b(?:they|the\s+doctor|the\s+doctors|the\s+consultant|the\s+radiologist|the\s+scan|"
    r"the\s+mammogram|the\s+x-?ray|the\s+results?)\s+(?:found|saw|spotted|noticed|picked\s+up|"
    r"showed)\s+(?:something|a\s+(?:shadow|mass|growth|nodule|spot|lump))\b", re.I)
# A finding that has already been explained is not the news: "they found a shadow and its benign".
A_BENIGN_FINDING = re.compile(
    r"(?<!not\s)\b(?:benign|harmless|was\s+nothing|nothing\s+(?:to\s+worry|serious|bad|sinister)|"
    r"all\s+(?:fine|clear)|turned\s+out\s+(?:fine|nothing))\b", re.I)
# Who the news is about: the speaker, or the thing they were told about with no person named yet.
ITS_THE_SPEAKERS = re.compile(
    r"(?:\bit'?s\b|\bit is\b|\bive\b|\bi've\b|\bi have\b|\bi had\b|\bi got\b|\bim\b|\bi'm\b|"
    r"\bi was\b|\bi am\b|\bthey found\b|\btheyve found\b|\bthey've found\b|\bfound out\b|"
    r"\b(?:my|the|their)\s+(?:cancer|tumou?rs?|leuka?emia|lymphoma|melanoma)\b|"
    r"\bthe (?:biopsy|scan|results?|tests?|lump|mri|x-?ray)\b|\bmy (?:biopsy|scan|results?|"
    r"tests?|lump|mri|x-?ray)\b|\bgot the results\b|\bdiagnosed\b|\bdiagnosis\b)", re.I)
# The same words in a line that is not about anybody falling ill: a sponsored run for a cancer
# charity, a nurse's shift, a documentary about a tumour.
NOT_ABOUT_THEIR_BODY = re.compile(
    r"\b(?:sponsor\w*|fundrais\w*|raising|raise money|awareness|charity|marathon|"
    r"race for life|donat\w*|nurses?|nursing|(?:works?|working) (?:at|in|for)|shift|"
    r"documentar\w*|film|episode|podcast|research(?:ing)?|study|statistics?)\b", re.I)
# A scare that is over is not a wait: "i had a cancer scare last year but they said i am fine".
A_SCARE = re.compile(
    r"\b(?:scare|false alarm|all clear|came back clear|turned out (?:fine|nothing|benign)|"
    r"it was (?:benign|nothing)|they said it was nothing)\b", re.I)
# The other direction: "the cancer is gone", "its in remission", "the tumour has shrunk".
A_GOOD_TURN = re.compile(
    r"\b(?:gone|all gone|shrank|shrunk|shrink\w*|in remission|remission|no sign of|cured|"
    r"all clear|clear scan|finished (?:the )?(?:chemo|treatment|radiotherapy))\b", re.I)
# A condition ruled out, hoped for, feared or checked for is not news that has landed.
NOT_LANDED = re.compile(
    r"\b(?:not|isnt|isn't|no longer|never|clear of|free of|benign|ruled out|test\w* for|"
    r"check\w* for|screen\w* for|scared|worried|afraid|terrified|think|thought|might|maybe|"
    r"may have|probably|hopefully|pray|praying|what if|is it|is that|or is it|could it)\b", re.I)

# The wait itself: a suspicion, a test, a scan, a result due.
A_WORRY = re.compile(
    r"\b(?:think|thinks|thought|might|maybe|could|may\s+have|possibly|probably|suspect\w*|scared|"
    r"afraid|terrified|worried|worry|fear|fears|hoping|praying|waiting|wait|"
    r"test\w*(?:\s+(?:me|him|her))?\s+for|check\w*(?:\s+(?:me|him|her))?\s+for|"
    r"screen\w*\s+for|being\s+tested|results\s+(?:are|is)\s+(?:due|back)|"
    r"\b(?:is|are|was|were)\s+(?:having|going\s+in|in)\s+(?:a\s+|an\s+|the\s+)?"
    r"(?:scan|test|biopsy|procedure|op|operation)|"
    # A test put in the diary ahead is the same wait, said the other way round: "my biopsy
    # is on monday", "i have a scan next week". The day is what makes it a wait and not a
    # memory, so this arm demands one.
    r"\b(?:scan|scans|test|tests|biopsy|biopsies|mammogram|smear|op|operation|procedure|"
    r"appointment)\s+(?:is|are|was|were)\s+(?:on|at|next|this|tomorrow|in)\b|"
    r"\b(?:have|has|having|got)\s+(?:a\s+|an\s+|the\s+|my\s+)?(?:blood\s+|ct\s+|mri\s+|"
    r"x[ -]?ray\s+|smear\s+|pregnancy\s+)?(?:scan|test|biopsy|mammogram|smear|op|operation|"
    r"procedure|surgery)\s+(?:on|next|this|tomorrow|in|at)\b)"
    ,re.I)
# A test whose answer can be a wait of days: "im worried about my results".
A_MEDICAL_TEST = re.compile(
    r"\b(?:scan|scans|biopsy|biopsies|mammogram|smear|smear test|blood test|bloods|mri|ct scan|"
    r"ultrasound|x[ -]?ray|xray|ecg|swab|test results|results of (?:my|the)|my results|"
    r"the results|results?|op|ops|operation|operations|procedure|procedures|surgery)\b", re.I)
# "im worried about my exam results" is the same words about a different kind of wait.
NOT_A_MEDICAL_TEST = re.compile(
    r"\b(?:exam|exams|gcse|gcses|a level|a levels|alevel|school|uni|university|course|driving|"
    r"lottery|election|football|match)\b", re.I)

# An animal is not a body this file knows how to talk to: "my cat might have cancer" is about a
# pet, and the person's own herd of words is not the thing to answer with.
AN_ANIMAL = re.compile(
    r"\b(?:dog|dogs|cat|cats|puppy|kitten|pet|pets|rabbit|hamster|guinea pig|horse|pony|"
    r"parrot|ferret|tortoise|lizard|snake|fish)\b", re.I)
# A line that asks whether it could be the thing is a question, not the wait and not the news:
# "could it be cancer", "what if it is", "do you think its cancer". The bot cannot say, and the
# pools here are written for somebody who already knows what is being tested.
A_QUESTION_ABOUT_IT = re.compile(
    r"\b(?:could|might|can|is|are|was|would|will|does|do)\s+(?:it|this|that)\s+(?:be|mean)\b|"
    r"\bwhat\s+if\s+(?:it|this)\b|\bdo\s+you\s+think\b|\bany\s+chance\b|"
    r"\bwhat\s+are\s+the\s+chances\b", re.I)
# A relative makes the same words a different question: "my mum might have cancer".
KIN = (r"mum|mummy|mom|mommy|mother|dad|daddy|father|son|daughter|child|children|kid|kids|"
       r"wife|husband|partner|boyfriend|girlfriend|brother|sister|gran|granny|grandma|grandad|"
       r"grandpa|nana|nan|aunt|auntie|uncle|cousin|friend|mate|neighbour|neighbor|baby|sister|"
       r"in[- ]law|niece|nephew|stepson|stepdaughter|stepdad|stepmum|fiance|fiancee")
_A_RELATIVE = re.compile(r"\b(?:my|our)\s+(?:" + KIN + r")(?:'?s)?\b", re.I)

# The serious thing ruled out: "they ruled out cancer", "the scan ruled out a tumour". The `who` is
# what keeps a question and "the scan ruled out a scan" out of it.
RULED_OUT = re.compile(
    r"\b(?:they|he|she|we|the\s+(?:doctor|doctors|consultant|gp|specialist|hospital|scan|"
    r"tests?|results?|biopsy)|doc(?:tor)?)\b[^.!?]{0,16}?\bruled\s+out\b[^.!?]{0,20}?"
    r"\b(?:cancer|tumou?rs?|malignant|carcinoma|lymphoma|leuka?emia|melanoma)\b", re.I)
# "its not cancer", "it isn't cancer", "they said it wasnt cancer": the same news with the good word
# first, and the commonest way anybody says it.
NEGATED_CONDITION = re.compile(
    r"\b(?:(?:it'?s|it is|its|that'?s|that is|it|that)\s+(?:not|isnt|isn'?t|wasnt|wasn'?t|"
    r"wasn'?t\s+not)|(?:they|the doctor|the consultant|the gp|the results?|the tests?)\s+"
    r"(?:said|say|told me|came back|were|was)?\s*(?:it\s+)?(?:not|isnt|isn'?t|wasnt|wasn'?t))"
    r"\s+(?:a\s+|the\s+|any\s+)?(?:cancer|tumou?r|malignant|carcinoma|lymphoma|leuka?emia|"
    r"melanoma)\b", re.I)
# The good word has to be the end of the news, or the line is a report with a turn in it.
RULED_OUT_TAIL = re.compile(
    r"\s*(?:(?:now|today|though\s+thankfully|thankfully|thank\s+god|at\s+last|finally|so\s+far|"
    r"great|brilliant|and\s+i\s+(?:am|feel)\s+(?:so\s+)?(?:relieved|glad|happy)|"
    r"im\s+(?:so\s+)?(?:relieved|glad|happy)|which\s+is\s+(?:great|a\s+relief)|"
    r"what\s+a\s+relief|thanks|cheers|anyway)\s*)*[.!]*$", re.I)

# The wait about their own body. Nothing is known yet, so the answer is about the wait and the one
# thing worth doing in it - and it takes no view of what the answer will be.
THE_WAIT = (
    "That wait between a test and an answer is the worst part of it, and nothing is known until "
    "somebody tells you. What have they actually said so far?",
    "Sitting with a maybe is harder than sitting with an answer, even a bad one. Try not to spend "
    "the wait on the worst version of it. When do you hear?",
    "That is a frightening thing to be carrying around. Write your questions down before the "
    "appointment - they go out of your head in the room. Who is going with you?",
)
# A routine blood test is a wait, not a fright, so the line about being frightened is kept for a
# line that names a condition. The other two are true of any wait: a test booked for Thursday.
THE_WAIT_AFTER_A_TEST = THE_WAIT[:2]
# The same wait about somebody they love: the person asked about stays in it, and the last line
# asks after the asker, because that is who the bot is talking to.
THEIR_WAIT = (
    "Waiting on somebody else's results is a helpless feeling, and nothing is known until they are "
    "back. What have they been told about when they will know?",
    "Sitting with a maybe about someone you love is harder than sitting with an answer. Try not to "
    "plan around the worst version of it. Who is with them?",
    "That is frightening, and it is a lot to carry around. What has actually been said so far - and "
    "who is looking after you in it?",
)
# The news itself, which is not a wait and not a bad day either: a line written for a setback calls
# it "frustrating".
THE_NEWS = (
    "I'm sorry. That is a hell of a thing to be told, and there is no right way to take it. "
    "Who is with you today?",
    "That is the kind of news that stops the week. How are you doing with it so far?",
    "You don't have to make sense of it today. Do you want to talk about it, or shall I ask about "
    "something else for a while?",
    "That's a heavy word to hear about yourself. Who is looking after you in it?",
    "I'm sorry. Do you want to tell me what they said?",
)
# The condition itself going, which is the best news there is and was met with "I'm sorry - that's
# frustrating", a line for a bus that did not come.
THE_ILLNESS_GOING = (
    "That is the best kind of news to hear, and it is worth saying out loud today. How did they tell "
    "you?",
    "Gone is a good word to hear about it. What does that leave for you - a check in a few months, "
    "or the whole thing behind you?",
    "That is a weight off. Do the people who were worried with you know yet?",
)
# The good direction, which is news and not a wait.
THE_THING_RULED_OUT = (
    "Then it is not that, and that is the news you were after. What did they say it is instead?",
    "Ruled out. That is a weight off, whatever else came with it. How are you doing?",
    "Good. Not that, then. Did they say what it is?",
)


def _the_relative(text):
    return _A_RELATIVE.search(text)


def _the_wait(text):
    """The thing the line is waiting on: a condition, a finding, or a test with an answer coming."""
    found = OWN_SERIOUS_CONDITION.search(text) or A_FINDING.search(text)
    if found:
        return found
    if NOT_A_MEDICAL_TEST.search(text):
        return None
    return A_MEDICAL_TEST.search(text)


def tells_of_a_condition_of_their_own(text):
    """Whether the line tells the bot a serious condition about the person typing it."""
    if not text or NOT_ABOUT_THEIR_BODY.search(text):
        return False
    if AN_ANIMAL.search(text) or A_QUESTION_ABOUT_IT.search(text):
        return False
    condition = OWN_SERIOUS_CONDITION.search(text)
    if not condition:
        condition = A_FINDING.search(text)
        if not condition or A_BENIGN_FINDING.search(text):
            return False
    owner = ITS_THE_SPEAKERS.search(text)
    if not owner:
        return False
    if A_SCARE.search(text) or A_GOOD_TURN.search(text):
        return False
    landed = NOT_LANDED.search(text)
    if landed and landed.start() < condition.start():
        return False
    mine = _the_relative(text)
    if mine and mine.start() < owner.start():
        return False
    return True


def reads_as_the_wait_of_their_own(text):
    """Whether the line is the wait before an answer about the person's own body."""
    if not text or NOT_ABOUT_THEIR_BODY.search(text):
        return False
    if AN_ANIMAL.search(text) or A_QUESTION_ABOUT_IT.search(text):
        return False
    if A_SCARE.search(text) or A_GOOD_TURN.search(text):
        return False
    if not A_WORRY.search(text) or not _the_wait(text):
        return False
    if _the_relative(text):
        return tells_of_a_condition_of_their_own(text)
    return not tells_of_a_condition_of_their_own(text)


def reads_as_the_wait_of_somebody_elses(text):
    """The same wait, about a relative: "my mum might have cancer", "my dads scan is on monday"."""
    if not text or NOT_ABOUT_THEIR_BODY.search(text):
        return False
    if AN_ANIMAL.search(text) or A_QUESTION_ABOUT_IT.search(text):
        return False
    if A_SCARE.search(text) or A_GOOD_TURN.search(text):
        return False
    if not A_WORRY.search(text) or not _the_wait(text):
        return False
    return bool(_the_relative(text))


def reads_as_a_thing_ruled_out(text):
    """Whether the line says the serious thing was ruled out - the good direction, not a wait."""
    said = " ".join(str(text or "").lower().split())
    if not said or "?" in said:
        return False
    # A question is not the news, whichever way round it is typed: "is it not cancer", "did they
    # rule out cancer".
    if A_QUESTION_ABOUT_IT.search(said) or re.match(
            r"\s*(?:is|are|was|were|did|does|do|has|have|had|can|could|would|will|should|any)\b",
            said):
        return False
    for match in RULED_OUT.finditer(said):
        if RULED_OUT_TAIL.match(said[match.end():]):
            return True
    for match in NEGATED_CONDITION.finditer(said):
        if RULED_OUT_TAIL.match(said[match.end():]):
            return True
    return False


def reads_as_the_news_of_their_own(text):
    """Whether the line tells the news itself about the person's own body: "i have cancer"."""
    if not tells_of_a_condition_of_their_own(text):
        return False
    return not A_WORRY.search(text)


def reads_as_the_illness_going(text):
    """Whether the line says the condition itself is over: "the cancer is gone", "my tumour shrank"."""
    if not text or NOT_ABOUT_THEIR_BODY.search(text):
        return False
    if not OWN_SERIOUS_CONDITION.search(text):
        return False
    turn = A_GOOD_TURN.search(text)
    if not turn:
        return False
    if "?" in text or NOT_LANDED.search(text[:max(0, turn.start())] or " "):
        return False
    if re.match(r"\s*(?:is|are|was|were|will|would|could|can|has|had|have|did|does|do|"
                r"any\s+chance|do\s+you\s+think)\b", text):
        return False
    # The good word has to be the end of the news: "the cancer is gone but they want another scan in
    # a year" is relief and a worry, and "that is a weight off" over the second half is wrong.
    return bool(RULED_OUT_TAIL.match(text[turn.end():]))


def pool_for(text):
    """The pool this line belongs to, or None when it is not one of these five readings."""
    if reads_as_a_thing_ruled_out(text):
        return THE_THING_RULED_OUT
    if reads_as_the_illness_going(text):
        return THE_ILLNESS_GOING
    if reads_as_the_news_of_their_own(text):
        return THE_NEWS
    if reads_as_the_wait_of_somebody_elses(text):
        return THEIR_WAIT
    if reads_as_the_wait_of_their_own(text):
        return THE_WAIT
    return None


def names_a_condition(text):
    """Whether the line names a condition or a finding, not just a test that is booked."""
    said = " ".join(str(text or "").lower().split())
    return bool(OWN_SERIOUS_CONDITION.search(said) or A_FINDING.search(said))


def reply_for(text, memory=None):
    """The line for the wait or the ruled-out thing, or None when this file has nothing to say."""
    pool = pool_for(text)
    if not pool:
        return None
    if pool is THE_WAIT and not names_a_condition(text):
        pool = THE_WAIT_AFTER_A_TEST
    return pick(pool, memory if isinstance(memory, dict) else {}, text)
