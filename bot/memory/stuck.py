"""Where to start, when the person says they don't know and the hard thing is already on the table.

    my wife left me        -> That sounds rough. If you want, I can help you think through ...
    i dont know what to do -> Got it. Is there anything you'd like a hand with?

The second line names nothing new: it carries the first one over. The stock nod answers it with
"is there anything you'd like a hand with", which is exactly what the person has just said they
cannot do, and it would fit any message in the conversation. What they are asking for is the next
step, and the only thing that can say what the next step is, is the line before it - which the
store keeps in memory["turns"]. So this reads that line and answers with the first thing a friend
would say to that kind of news: money has dates, a death has paperwork and none of it is today, a
diagnosis has a question for the doctor.

Only the line that carries nothing of its own comes here, and only when the turn before it was one
of those kinds. Anything else returns None, so "i dont know what to do with my life" still reaches
the direction pool in bot/compose/fallback.py, which is written for it.
"""
import re

from ..compose.badnews import reads_as_bad_news
from . import topics

# The shapes that carry nothing but "I am stuck". They are the whole line, so a line that names a
# thing ("i dont know what to do about the car", "i dont know where to start with the loft") is
# left alone: naming the thing is what the rest of the bot reads best.
_NOTHING_ELSE = r"(?:\s+(?:now|next|anymore|any more|at all))?"
# The state a person names - "im stuck", "i am so lost" - as against the shapes below that only
# report that no next step is visible. Kept apart because the two want different answers when the
# line is the first thing said (see `pool`).
_STATE_SOURCE = (r"(?:im|i am|were|we are)\s+(?:just\s+)?(?:so\s+)?(?:lost|stuck)\b"
                 r"(?:\s+(?:in\s+a\s+rut|on|with|about)\s+(?:this|it|that))?")
_STATE = re.compile(r"^\W*(?:" + _STATE_SOURCE + r")\s*(?:\?|\.|!)*\s*$")

# The small words a person puts in front of an ask, and the ask itself with no anchors on it, so
# the same shape can be read as the whole line and as the end of a longer one.
_LEADS = r"(?:(?:and|but|so|well|oh|honestly|then|i mean|like|just|seriously|really)\s+)*"
_ASK_BODY = (
    r"(?:"
    r"(?:i|we)(?:'ve| have|'m| am)?\s+(?:just\s+|really\s+|still\s+|honestly\s+|actually\s+)*"
    r"(?:dont|don'?t|do not|doesnt|does not)\s+know\s+what\s+to\s+do" + _NOTHING_ELSE +
    r"|(?:(?:i|we)(?:'ve| have|'m| am)?\s+)?(?:got\s+|have\s+)?no\s+idea\s+what\s+to\s+do"
    + _NOTHING_ELSE +
    r"|(?:i|we)(?:'ve| have)?\s+(?:just\s+|really\s+|honestly\s+)*(?:dont|don'?t|do not)\s+"
    r"know\s+where\s+to\s+(?:start|begin|turn)" + _NOTHING_ELSE +
    r"|(?:i|we)(?:'ve| have)?\s+(?:no\s+idea|dont|don'?t|do not)\s+what\s+(?:comes\s+)?next\b"
    + _NOTHING_ELSE +
    r"|what\s+(?:do|should|shall|can|could)\s+(?:i|we)\s+do" + _NOTHING_ELSE +
    r"|what\s+(?:am|are)\s+(?:i|we)\s+supposed\s+to\s+do" + _NOTHING_ELSE +
    r"|(?:" + _STATE_SOURCE + r")"
    r")")

STUCK = re.compile(r"^\W*" + _LEADS + _ASK_BODY + r"\s*(?:\?|\.|!)*\s*$")

# The ask does not have to be the whole line. "that sounds hard, what should i do" is a comment on
# what was just said and then the ask, and the pool never saw it: the comment was read as the subject
# and the knowledge base answered the word "sound" ("Sound is a pressure wave travelling through
# air"). The ask at the end of a line is the ask, and the clause before it is the person's reaction,
# which says nothing the pool has to read - so the pool reads the ask and the line before it, which
# is what it reads for every other stuck line.
AN_ASK_AT_THE_END = re.compile(
    r"(?:^|[\s,;:.!?\u2014-]+)" + _LEADS + _ASK_BODY + r"\s*(?:\?|\.|!)*\s*$")
# The frame a reaction is said in: a pronoun pointing at the last thing said, and a word or two
# about it ("that sounds hard", "this tastes odd", "thats hard", "that must be hard").
REACTION_FRAME = re.compile(
    r"^(?:(?:oh|well|god|wow|yeah|ok|okay|hmm|blimey|cor|ah|yes|no)\s+)*"
    r"(?:that sounds|this sounds|that looks|this looks|that seems|that feels|that must be"
    r"|that must have been|thats|that's|this is|that is|it is|its|it's|sounds|looks|seems|feels"
    r"|that|this|it)\s+"
    r"(?P<about>(?:[a-z']+\s*){1,3})$", re.I)
# A reaction says how it landed, so nothing in it names a thing: "that sounds like my printer" is
# about the printer and the ask after it is not the whole of the line.
NAMES_A_THING = re.compile(
    r"\b(?:like|as|than|a|an|the|my|your|his|her|their|our|some|any|this|that|these|those"
    r"|one|two|three)\b", re.I)


def _a_reaction_to_what_was_said(lead):
    """Whether a clause in front of the ask is only the person's reaction to the last turn."""
    text = " ".join(str(lead or "").split()).strip(" ,;:.!?-\u2014")
    if not text:
        return False
    found = REACTION_FRAME.match(text)
    if not found:
        return False
    return not NAMES_A_THING.search(found.group("about"))


def the_ask_in(low):
    """The ask in the line: the whole of it, or the ask at the end of a reaction to the last turn.

    "" when the line is not a stuck ask at all, which is most lines.
    """
    text = " ".join(str(low or "").split())
    if STUCK.match(text):
        return text
    found = AN_ASK_AT_THE_END.search(text)
    if not found:
        return ""
    lead = text[:found.start()].strip(" ,;:.!?-\u2014")
    if lead and not _a_reaction_to_what_was_said(lead):
        return ""
    return found.group(0).strip(" ,;:.!?-\u2014")


# The thing before it, by the kind of news it was. A death is not a problem to solve, money is; a
# relationship ending runs on the next forty-eight hours, a diagnosis on one question for a doctor.
_DEATH = re.compile(
    r"\b(?:died|dying|passed (?:away|on)|funeral|buried|cremat\w*|death|widow\w*|"
    r"put (?:him|her|it|them)? ?down|euthanis\w*|we lost (?:her|him|them|mum|dad|my))\b")
# "left me" and "broke up" are the words, and the object after them decides: "she left me a
# voicemail" and "we broke up the sofa" are not an ending. So a noun with a determiner in front of
# it, or a verb in -ing, keeps the line out; a time word ("left me last week") stays in.
_AN_OBJECT = (r"(?!\s+(?:a|an|the|my|your|his|her|their|our|some|this|that|these|those|no|one|"
              r"two|three|four|five|another|all|[a-z]+ing)\b)")
_ENDING = re.compile(
    r"\b(?:left me" + _AN_OBJECT + r"|walked out|threw me out|kicked me out|"
    r"(?:broke|split) up" + _AN_OBJECT + r"|separated|"
    r"divorc\w*|she'?s gone|he'?s gone|affair|cheated)\b")
# Being fired is the news; being "fired up about the boiler" is not. So `fired` needs somebody
# doing it to them, and `let go` needs the person: "i need to let go of the past" has neither. A
# pay cut belongs to a job, so it carries one of the job's own words in the same sentence.
_JOB = re.compile(
    r"\b(?:lost my (?:job|work|business|contract)|redundant|redundancy|laid off|sacked|"
    r"(?:got|been|were|was|im|i am|i'?m|getting|get|being)\s+fired\b(?!\s+up\b)|"
    r"let (?:me|him|her|us|them) go|resigned|walked out of (?:my|the) job|"
    r"contract not renewed|hours (?:were )?cut|"
    r"(?:my|our|the|a)\s+pay cut\b|"
    r"pay cut\b[^.!?]*\b(?:job|work|hours|salary|wage|boss|employer|shift|contract)\b|"
    r"\b(?:job|work|hours|salary|wage|boss|employer|shift|contract)\b[^.!?]*\bpay cut)\b")
# "behind on" is money only when the thing behind is one that is paid for: behind on the rent,
# behind on the card. "im behind on my emails" and "behind on my coursework" are a to-do list, and
# telling that person to ring whoever they owe is the wrong kind of help.
_OWED = (r"(?:the |my |our )?(?:rent|bills?|payments?|mortgage|council tax|card|loan|gas|"
         r"electric(?:ity)?|water|dues|money|everything|childcare|nursery|school meals?)")
_MONEY = re.compile(
    r"\b(?:in debt|arrears|behind on " + _OWED + r"|behind with " + _OWED + r"|"
    r"can'?t afford|cannot afford|bailiffs|evicted|eviction|"
    r"repossession|bankrupt|overdraft|credit cards? maxed|money is tight|"
    r"low on (?:money|cash|funds|dosh)|short of money|skint|brokest|"
    r"(?:i|we)(?:'ve| have)?\s+no money|"
    r"down to my last (?:\d+|tenner|fiver|pound|quid|twenty|fifty))\b")
# "im broke" is the same news said the way most people say it, and it has to be first person:
# "broke up" is an ending (read before this one) and "broke my leg" is not money at all.
_SKINT = re.compile(
    r"\b(?:im|i am|i'?m|we are|we'?re|were)\s+(?:so\s+|totally\s+|completely\s+|proper\s+)?"
    r"broke\b")
# A diagnosis is an illness whatever is said around it, but the two abbreviations are not: "ms"
# is MS Word and Teams as often as it is multiple sclerosis, and "stroke" is a stroke of luck or a
# stroke of the brush. So those two are spelled out, and a stroke is one somebody had.
_ILLNESS = re.compile(
    r"\b(?:diagnos\w*|cancer|tumour|tumor|chemo\w*|radiotherapy|biopsy|hospice|"
    r"terminally ill|(?:had|having|a|another|suspected)\s+stroke\b(?!\s+of\b)|"
    r"heart attack|dementia|alzheimers|parkinsons|multiple sclerosis|"
    r"(?:has|have|got|with)\s+ms\b(?!\s+(?:word|teams|office|excel|project|outlook|"
    r"access|paint|edge|windows))|"
    r"in (?:the )?hospital|intensive care)\b")
# The speaker's own flat week is not news, but it is the thing they are stuck on, and the pools
# for "i dont know what to do" cannot tell: they answer the words, and the words name nothing.
# Only the first person counts, so "my husband is stressed" stays about him.
_FEELING = re.compile(
    r"\b(?:im|i am|i'?m|i feel|i'?ve been|ive been|feeling)\b(?:\s+\w+){0,4}\s+"
    r"(?:stressed|overwhelmed|exhausted|knackered|burnt out|burned out|anxious|panicking|"
    r"depressed|miserable|drowning|struggling|at the end of my tether|spiralling|"
    r"all over the place|low\b(?!\s+(?:on|in|down)\b)|down\b(?!\s+to\b)|"
    r"flat\b(?!\s+(?:tire|tyre|battery|mate|screen|white|bread|out|packed))|blue\b|rubbish|awful|"
    r"hopeless|empty)\b")
# The same week said without a named feeling: "im so tired of it all", "ive had enough". These
# open on the speaker too, so "my husband has had enough of his job" stays about him. "breaking
# point" and "giving up" are left where they are: those are for the safety line to read, not for a
# list of small steps.
_FLAT = re.compile(
    r"\b(?:im|i am|i'?m|ive|i'?ve|i feel|i'?ve been|ive been|feeling)\b(?:\s+\w+){0,4}\s+"
    r"(?:tired of (?:it all|everything|this|all this|life)|fed up|had enough|sick of (?:it|"
    r"everything|all this)|worn out|worn down|running on empty|drained|no energy)\b")
# "i want to move out" then "i dont know where to start": a plan, and the step is the one small
# first move rather than the whole thing.
_PLAN = re.compile(
    r"\b(?:i want to|i wanna|im thinking of|i'?m thinking of|im going to|i'?m going to|"
    r"i plan to|i'?d like to|i would like to|ive decided to|i'?ve decided to|"
    r"we want to|we'?re thinking of)\b")
# The first move of a plan is a phone call, a form, a quote. That is nonsense for a wish to make
# something - "i want to cook something nice for my girlfriend" then "i dont know where to start"
# was handed "the form, the quote, the phone call" - and those wishes have their own answers, so
# the making verbs send the line back to the modules that can read the thing.
_MAKING = re.compile(
    r"\b(?:cook|cooking|bake|baking|make|making|build|building|grow|growing|plant|planting|"
    r"sew|sewing|knit|knitting|paint|painting|brew|brewing|roast|roasting|grill|grilling|"
    r"barbecue|smoke|smoking|pickle|pickling|ferment|fermenting)\b")

# The same for a wish to learn something or to take up a hobby: "i want to learn guitar" then "i
# dont know where to start" was handed "the form, the quote, the phone call", right after a turn
# that said start with four chords. There is no form for running or a novel, so those wishes get
# the neutral one-step pool instead of the paperwork one.
_SELF = re.compile(
    r"\b(?:learn|learning|study|studying|studies|practi[cs]e|practi[cs]ing|take (?:it |that )?up|"
    r"get (?:fit|fitter|healthier|stronger|in shape)|lose (?:some )?weight|"
    r"start(?:ing)? (?:running|swimming|cycling|walking|yoga|pilates|climbing|the gym|"
    r"going to the gym|lessons?|classes?)|"
    r"guitar|piano|drums|violin|ukulele|singing|choir|"
    r"running|swimming|cycling|yoga|pilates|climbing|tennis|football|rugby|"
    r"drawing|sketching|painting|photography|pottery|"
    r"write|writing|a book|a novel|a blog|code|coding|programming|"
    r"a language|spanish|french|italian|german|welsh|"
    r"uni|university|college|a course|a degree|an evening class|open university)\b")

# A death is the one that has no step to take today, so its pool says that first and offers the
# talk instead of a plan.
DEATH = (
    "Nothing has to be decided today. When something does, it is usually one dull thing - a "
    "phone call, a form - so take whichever is in front of you and let the rest wait.",
    "There's no right order for this, and no rush to find one. Pick the smallest thing that "
    "has to happen this week and leave the rest of it.",
    "The next step is usually paperwork, and it keeps. If it helps more, tell me about them "
    "instead.",
)
ENDING = (
    "Then start with tonight rather than the whole thing: somewhere to sleep, and what you say "
    "to the people who will ask.",
    "Nothing about the why has to be settled now. The next day or two is the only real "
    "question - where you stay, what you eat, who you ring.",
    "Take it in the order it hurts least: a roof and money first, the rest after. Is either of "
    "those already sorted?",
)
JOB = (
    "Money has dates, so start there: what the last pay and any notice money come to, and when "
    "they land.",
    "One small thing tomorrow, one the day after - a CV refreshed, a single application. "
    "Momentum does more than a plan here.",
    "First find out what you are owed and when: final pay, holiday, notice. Work out the next "
    "month before the next year.",
)
MONEY = (
    "Start with whatever has a deadline - the rent, or the bill that is actually overdue - then "
    "ring the people owed it. They are used to that call.",
    "Free advice beats guessing: StepChange or Citizens Advice will work it out with you for "
    "nothing. Ring one of them this week.",
    "Do the sums in one sitting - what comes in, what has to go out, what is left - and ring "
    "whoever you owe before they ring you.",
)
ILLNESS = (
    "The next thing is a question for the doctor rather than for you: what happens next, and "
    "what to do if. Write those two down before the appointment.",
    "Nothing has to be understood today. Take one practical thing - the appointment, the form, "
    "who drives you - and let the rest wait.",
    "Ask what the treatment is for and what it is meant to do, and take someone with you to "
    "write the answers down.",
)
FEELING = (
    "Then take the smallest thing that would ease it - one call made, one thing dropped, half "
    "an hour of nothing. Which is easiest?",
    "You don't have to sort the whole week. Pick the one thing that would make today lighter "
    "and do only that.",
    "Start with the basics - food, sleep, one thing off the list - and let the rest wait until "
    "tomorrow.",
)
PLAN = (
    "Then pick the smallest first move - one website, one phone call, one list - and do only "
    "that today.",
    "Start with the piece you can finish in an hour: a list of what it costs, or the one call "
    "you have been putting off.",
    "Do the boring first step, whatever it is - the form, the quote, the phone call. The rest "
    "gets clearer after it.",
    # Not every plan opens with paperwork, and a person who says it twice should not get the
    # form twice: someone who has already done it knows the first week better than a form does.
    "Find one person who has done it and ask what their first week looked like. Then do the "
    "smallest thing off that list today.",
)
# A wish to learn something or take up a hobby is neither paperwork nor news: the step is to make
# the first go small enough to happen, which is not what either pool says.
SELF = (
    "Then make the first go small enough to be easy: twenty minutes of it today, and nothing "
    "promised beyond that.",
    "Pick the beginner's version and do it once this week, badly. It gets clearer once there is "
    "something to improve.",
    "Start with the hour you would actually do it in, not the plan for it. What would that hour "
    "look like?",
)
HARD = (
    "One thing at a time, then. What is the smallest thing that would make today easier?",
    "You don't have to have a plan. Pick the single next step and ignore the rest of it for now.",
    "Start with whatever has a deadline, if anything does; if nothing does, start with eating "
    "something.",
)
# A pet's death has none of that: "our dog was put down" then "i dont know what to do" was
# handed "it is usually one dull thing - a phone call, a form", and there is no form.
_ANIMAL = re.compile(
    r"\b(?:dog|dogs|puppy|pup|cat|cats|kitten|pet|rabbit|bunny|hamster|guinea pig|horse|pony|"
    r"budgie|parrot|ferret|tortoise|goldfish|fish)\b")
PET_LOSS = (
    "Nothing has to be decided today, and nothing has to be tidied away either. What is the "
    "house like without them?",
    "There is no step to take today. If it helps, tell me about them - what they were like.",
    "The quiet is the hard part, and it takes the time it takes. Take today as slowly as it "
    "comes.",
)

# The answer just given said to get seen today: "ring 111 or your GP first thing", "go to A&E".
# The pools below are written for news that has a plan in it - money has dates, a death has
# paperwork - and a "where do i start" after an urgent answer is not asking for a plan: the plan
# is the appointment. No cut of that answer can hand the advice back, either, because every step
# reader skips a red-flag sentence (`topics.RED_FLAG`), which is right for "what else can i do"
# and leaves this ask with nothing. So the line says the one thing that still stands.
EMERGENCY = re.compile(
    r"\b(?:999|911|112|111|a&e|a and e|casualty|ambulance|emergency department|out of hours|"
    r"urgent care|walk-in cent(?:re|er))\b", re.I)

URGENT_ALREADY_GIVEN = (
    "The advice you just had is the first thing to do. Nothing else needs a plan until someone "
    "has seen you.",
    "What you were just told to do is the whole of the list today - the rest keeps until "
    "someone has seen you.",
    "Get seen first. Nothing on the list is worth doing before that, and it will all still be "
    "there afterwards.",
)


# Only an answer whose own opening is the emergency counts. The baby-crying card ends "Call 111
# the same day if the cry is high or unusual", and that is a branch of the advice, not the advice:
# a mother who worked down that list and then asked what to do next was told "nothing else needs a
# plan until someone has seen you", which sends her to a doctor nobody sent her to. The cards that
# mean it say it first - "ring 111 or your GP first thing", "go to A&E" - so the number has to be
# in the answer's first sentence, with no "if", "when" or "unless" in front of it.
FIRST_SENTENCE = re.compile(r"[.!?](?:\s|$)")
A_CONDITION_IN_FRONT = re.compile(r"\b(?:if|unless|when|whether|in case)\b", re.I)


# The fog pool, for a stuck line that is the first thing said in the conversation. It names no
# scene the person did not give ("the form on the table", "the bit somebody else is waiting on"
# read as a guess at a life nobody described) and it does not pretend to a first step before it
# knows one thing about the situation.
FIRST_LINE = (
    "Nothing looks like a first step when it is all in one heap. Say the situation in a line and "
    "we'll find the smallest piece of it.",
    "It is usually one thing pretending to be ten. What is the part that keeps coming back?",
    "The fog is normal with this much on. Name one thing that happened today and we will start "
    "there.",
)


def _opens_with_an_emergency(reply):
    """Whether the reply's first sentence is the emergency, said without a condition on it."""
    said = " ".join(str(reply or "").split())
    found = EMERGENCY.search(said)
    if not found:
        return False
    end = FIRST_SENTENCE.search(said)
    if end and found.start() >= end.end():
        return False
    return not A_CONDITION_IN_FRONT.search(said[:found.start()])


def the_advice_was_to_get_seen(memory):
    """Whether the bot's last reply opened by telling them to get seen today.

    A reply that says "ring 111" or "go to A&E" in its first sentence has already given the step,
    and a line that asks where to start after it is asking about everything else. Read from the
    last thing the bot said, so a chat that never reached one of those answers is untouched.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    for turn in reversed(turns or []):
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            return _opens_with_an_emergency(str(turn["bot"]))
    return False


POOLS = ((_DEATH, DEATH), (_ENDING, ENDING), (_JOB, JOB), (_MONEY, MONEY), (_SKINT, MONEY),
         (_ILLNESS, ILLNESS),
         (_FEELING, FEELING), (_FLAT, FEELING), (_PLAN, PLAN))


def pool(text, memory):
    """The pool of next steps for a stuck line, or None when the line is not that or nothing hard
    came before it."""
    low = " ".join(str(text or "").lower().replace("\u2019", "'").split())
    ask = the_ask_in(low)
    if not ask:
        return None
    before = _before(memory)
    if not before:
        if _START_ASK.match(ask):
            return _not_said_again(HARD, memory)
        if _STATE.match(low):
            # "im stuck" / "i am so lost" as the first thing said: the state has its own answers
            # and they are warmer and more specific than any fog line ("Which bit of it is
            # heaviest? Take that one first rather than the whole thing at once"), so the fog
            # stands aside. Two readers of this change caught the pool taking them, and both
            # preferred what the person had.
            return None
        # A stuck line as the first thing said. There is no line before it to read a first step
        # out of, so this returned None and the flat "I'm listening - say more if it helps" or the
        # search hedge answered a person who opened with "im stuck" or "i feel stuck". The line
        # names nothing, so no pool can name the thing - what a friend says is that a heap that
        # size always looks like no first step, and asks for the one part of it that is loudest.
        return _not_said_again(FIRST_LINE, memory)
    if the_advice_was_to_get_seen(memory):
        # "my chest hurts when i run" then "i dont know what to do": the answer told them to ring
        # 111 today, and the next step after that is not one of the pools below.
        return _not_said_again(URGENT_ALREADY_GIVEN, memory)
    for pattern, replies in POOLS:
        if pattern is _PLAN and _MAKING.search(before):
            continue
        if pattern is _PLAN and _SELF.search(before):
            if _the_answer_gave_a_step(memory):
                # The wish was already answered with something to do ("start with four chords
                # that fit a hundred songs"): the step exists, and handing over the neutral one
                # instead is the vaguest reply on the page. Standing down lets the answer come
                # back as the step it already was.
                continue
            return _not_said_again(SELF, memory)
        if pattern.search(before):
            if pattern is _DEATH and _ANIMAL.search(before):
                # A pet's death is the one line where the knowledge base already has the better
                # answer - the condolence and the practical next step in one reply - and a neutral
                # pool in its place loses the apology, which is the first thing the person needs
                # to read. So the pool stands aside for it and the pets card answers.
                continue
            return _not_said_again(replies, memory)
    # Anything that is still the thing this line is about, but fits none of the pools above - news
    # that reads as bad, or a wish to learn something with no paperwork in it - gets the neutral
    # one-step pool rather than the nod.
    if reads_as_bad_news(before):
        return _not_said_again(HARD, memory)
    return None


# A step is a step when the reply names something to do or something to do it with: a number, or
# a colon that introduces the how, or an opening that is an instruction. The shape pools' carry-
# overs ("Sometimes it's everything at once. It can stay unnamed.") have none of the three, which
# is what makes them the lines a stuck line still has something to add to.
DOING = frozenset("""start starts begin pick do try ask ring call phone write book get go take read
watch cook bake keep put set use buy check plan split choose make find look learn practice practise
send fill sign download join tell speak say warm rinse boil cut add mix stop ease slow wear walk run
""".split())


def _the_answer_gave_a_step(memory):
    """Whether the bot's last reply already told the person something to do."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = ""
    for turn in reversed(turns or []):
        if isinstance(turn, dict) and str(turn.get("bot") or "").strip():
            said = " ".join(str(turn["bot"]).lower().split())
            break
    if not said:
        return False
    if re.search(r"\d", said) or ":" in said:
        return True
    return any(w in DOING for w in re.findall(r"[a-z']+", said)[:6])


def _not_said_again(replies, memory):
    """The pool with the steps the bot has already said in the last few turns pushed back.

    "im drained" is answered "give yourself half an hour doing nothing before the next thing", and
    the stuck line after it was answered with the same half hour: two turns, one idea. The step
    that shares most of its words with what the bot just said goes to the back, and the freshest
    one comes first; nothing is dropped, because a repeated step is still better than the nod.
    """
    turns = memory.get("turns") if isinstance(memory, dict) else None
    said = " ".join(str(turn.get("bot") or "").lower() for turn in (turns or [])[-4:]
                    if isinstance(turn, dict))
    if not said:
        return replies
    def written(reply):
        words = [w for w in re.findall(r"[a-z']+", reply.lower())
                 if len(w) > 3 and w not in topics.STOPWORDS]
        shared = sum(1 for w in words if w.rstrip("s") in said)
        if not words:
            return False
        # Three words and a third of the step: one shared word is a real fit ("the rent, or the
        # bill that is overdue" after an answer that said "pay"), not a repeat.
        return shared >= 3 and shared / len(words) >= 0.35
    return tuple(sorted(replies, key=written))


# "I dont know where to start", said as the first line of a conversation: there is no line before
# it to read the first step out of, so `pool` has always returned None and the shape pools below
# answered a person asking where to begin with "Fair enough - days like that are hard to pin
# down", which names nothing and asks nothing. The line does not name a thing either, but it does
# ask for the way to pick, and the pool that says how to pick one thing is written for exactly
# that. Only this shape: "i dont know what to do" with nothing before it is an offer, not a list.
_START_ASK = re.compile(
    r"^\W*(?:(?:so|and|but|well|oh|honestly|then|i mean|like|just|seriously|really|the thing is|"
    r"see|look)\s+)*"
    r"(?:"
    r"(?:(?:i|we)\s+)?(?:(?:really|honestly|just|even|still)\s+)*"
    r"(?:(?:dont|don'?t|do not)\s+(?:even\s+)?know|dunno|(?:have\s+)?no\s+(?:idea|clue))\s+"
    r"where\s+to\s+(?:start|begin)"
    r"|(?:where|how)\s+(?:do|should|shall|can|could)\s+(?:i|we)\s+(?:even\s+)?"
    r"(?:start|begin)"
    r"|where\s+to\s+(?:start|begin)"
    r")(?:\s+(?:now|first|today|at\s+all))?\s*(?:\?|\.|!)*$", re.I)


def _before(memory):
    """The line before this one, cleaned, or '' when there is none."""
    turns = memory.get("turns") if isinstance(memory, dict) else None
    if not isinstance(turns, list) or not turns:
        return ""
    last = turns[-1]
    if not isinstance(last, dict):
        return ""
    return " ".join(str(last.get("user") or "").lower().replace("\u2019", "'").split())
