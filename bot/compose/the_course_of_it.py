"""A feeling asked about how long it lasts: "does it get easier", "will i ever feel normal again".

Nine of fifteen turns of this shape in a live probe reached a search hedge:

    does it get easier             -> "I don't know enough to answer that honestly. A search
    does that feeling ever go away ->  should sort you out quickly"
    will i ever feel normal again  -> "That's beyond what I know well, sorry."

A search cannot answer it. Nobody can put a date on grief or a breakup, and any page that claims
to is selling something. What a friend says is honest - no date - and then gives the shape of it:
it lifts in patches before it lifts properly, the bad days get further apart before they get
shorter, a bad day after a good week is not a sign of going backwards. Then one short question, so
the person can say where it hurts most.

What is not this: a course question with a body or a medicine in it (a rash, a cough, the tablets,
how long the antibiotics take) belongs to the health cards and to the safety lane, a thing with a
mechanism in it (the boiler, the car, the wifi) belongs to the knowledge base, and a bare "how
long does it last" with nothing behind it is too vague to answer at all.
"""

import re

# The feelings this reads. `easier` alone is enough signal: a person asking whether something gets
# easier is asking about a hard thing, not about the weather.
HEAVY = frozenset("""
feel feeling feelings felt sad sadness sadder grief grieving heartbroken broken heartsick lonely
loneliness alone guilt guilty ashamed shame anxious anxiety anxiousness depressed depression
panic unhappy happy happiness normal myself missing miss loss empty hopeless worthless numb
crying cry tears raw hurting hurts hurt heavy
""".split())

# A course question about one of these is somebody else's: the health cards answer it with a
# number, and a number is what the person actually wants.
BODY = frozenset("""
rash cough cold flu virus infection temperature fever spot spots itch itching lump bruise ache
aches pain painful headache migraine tooth teeth gum gums back knee hip shoulder neck ankle wrist
sickness nausea dizzy dizziness diarrhoea constipation blister burn cut wound swelling stiff
stiffness allergy allergic symptoms symptom period periods pregnant pregnancy
""".split())

MED = frozenset("""
meds medication medicine medicines tablets tablet pill pills dose dosage antibiotic antibiotics
antidepressant antidepressants sertraline citalopram prozac prescription prescribed treatment
chemotherapy withdrawal
""".split())

# A physical recovery has a real clinical timeline, and the health cards own it: "does it get
# easier after a c section" wants "six weeks, then it eases" from a midwife or a GP, not a shape
# about bad days getting further apart. A care event is not a feeling, so a line naming one stands
# this reader down even with grief words in the same line. `miscarriage` is deliberately NOT here:
# that is a loss, and the caring shape is right for it.
RECOVERY = frozenset("""
section caesarean cesarean csection surgery operation op ops operation hospital hospitalised
hospitalized recovery recovering recovered convalescing stitches stitch physio physiotherapy
chemo radiotherapy transplant bypass hysterectomy appendectomy appendix labour labor delivery
birth births fall falls fracture fractured fractures sprain sprains
discharge ward icu catheter cast plaster
""".split())

# A thing with a mechanism, a clock or a season: the knowledge base has a real answer, and "it
# lifts in patches" would be nonsense.
THING = frozenset("""
boiler car engine tyre tyres mot wifi internet broadband router phone laptop computer printer
oven washing machine dishwasher fridge freezer heating radiator leak tap roof gutter damp mould
noise neighbour neighbors traffic rain weather winter summer sale offer subscription contract
mortgage rent landlord job shift rota school term exam
""".split())

# The course phrases, longest first so "get back to normal" wins over "normal".
COURSE = re.compile(
    r"\b(?:"
    r"get(?:ting)?\s+back\s+to\s+normal"
    r"|get(?:ting)?\s+(?:easier|any\s+easier|better|any\s+better)"
    r"|feel(?:ing)?\s+(?:like\s+myself|normal|better|happy|ok|okay|fine|human)\s+again"
    r"|be\s+(?:happy|ok|okay|normal|fine|myself)\s+again"
    r"|go(?:es|ing)?\s+away|went\s+away|gone\s+away|ever\s+go\b"
    r"|get(?:ting)?\s+over\s+(?:it|this|that|him|her|them|everything)"
    r"|feel\s+like\s+this"
    r"|(?:this|it|that)\s+(?:be\s+)?forever"
    r"|(?:this|it|that)\s+(?:ever\s+)?(?:last|lasts|lasted)\b"
    r"|(?:ever\s+)?(?:going\s+to\s+)?(?:stop|end|ease|eases|settle|settles|pass|passes|lift|lifts)"
    r"|(?:always\s+|forever\s+|still\s+)?(?:going\s+to\s+)?be\s+like\s+this"
    r"|be\s+over"
    r")\b",
    re.I,
)

# The ask has to be about a course, not a claim: "it never stops" is a person telling you about
# their week, and the thread reader answers those.
ASKS = re.compile(
    r"^\s*(?:so\s+|but\s+|and\s+)?(?:when|does|do|will|would|is|are|am|can|could|how\s+long)\b",
    re.I,
)

# What `reads` returns when the course question is about the card the chat is on. It is not a
# phrase from the line, so it cannot be confused with one.
CARD_IN_THE_CHAT = "the card in the chat"

# A course question about a thing the talk never names: "will it last forever", "will it stop".
# There is nothing to quote and nothing to search for, so the reply asks which thing it is and
# says why that is what decides it.
NO_SUBJECT = "no subject yet"

# "does it get easier", "will i ever feel normal": the ask is about how a hard time goes, and the
# caring shape lower down answers exactly that without needing a thing to name.
IT_IS_HOW_IT_FEELS = frozenset("""
easier better cope coping manage managing deal dealing normal myself fine alright happy ok okay
heal healing recover recovering recoverd over through move moving onwards forward bearable
""".split())

NOTHING_NAMED = (
    "It depends what it is: a cough, a bad patch of sleep and a row at work all run on their own "
    "clock. Tell me the thing and I will say what usually happens with it.",
    "Nobody can say how long that lasts without knowing what it is. Which is it - something with "
    "your body, someone at home, or a job?",
    "How long that goes on for comes from what it is, and I do not know yet. Say what it refers to "
    "and I will tell you what usually happens.",
)

# "how long does it last" needs something to be about: with a feeling in the line it is grief, and
# with nothing in the line it is a question nothing can answer.
LASTS = re.compile(r"\bhow\s+long\s+(?:does|do|will|did|would)\b.*\b(?:last|take|go\s+on)\b", re.I)

# A disclosure of self-harm or of wanting to die is the safety lane's, not a course-of-grief
# question: the turn after one asks about a recovery nobody here is qualified to promise, and the
# hedge - which asserts nothing - is the right place to leave it.
DISTRESS = frozenset("""
cut cuts cutting cut myself self harmed harm harming suicide suicidal kill myself overdose
overdosed overdosing sectioned blades blade scars scarred burning starving starved purging
relapsed relapse
""".split())

# An ordinary life-stage thing the "it" can point at: a baby who is up in the night, a rota, an
# age. None of these is a grief, and "the bad days get further apart" is nonsense about a rota.
ORDINARY = frozenset("""
baby babies newborn newborns teething toddler toddlers nappy nappies formula feeding breastfed
sleepless knackered tired exhausted shifts shift rota rotas nights overtime commute gym diet
running marathon training weight old age ageing aging birthday birthdays
""".split())

# The shape of it said to somebody whose last line was the loss itself keeps the same honesty, and
# opens by taking it in, because "nobody can put a date on that" straight back reads as cold.
CARE = frozenset("""
lost lose losing died death dead funeral buried miscarriage miscarried separating separated
separation divorce divorced redundant redundancy sacked breakup broke broken cancer tumour
diagnosis diagnosed hospital hospice chemo stillbirth
""".split())

CARE_PROSE = (
    "I'm sorry - that's a heavy thing to be carrying. There is no date for it and I would be "
    "making one up, but it does come in patches rather than one long slope: a bearable hour, then "
    "a day that feels like the start again, and the bearable stretches get longer first. What "
    "helps early on is company and a shape to the day - someone who will sit with you, and one "
    "thing you do at the same time each day. Cruse takes calls from anyone who has lost someone, "
    "and your GP will see you about it too.",
    "That is a lot to hold, and I'm sorry. Nobody can tell you when it will feel lighter, and a "
    "guess would not help you. What tends to happen is that the good stretches come first, before "
    "the bad days get shorter, so a bad afternoon after a decent week is not a step back. Keep one "
    "fixed thing in the week and let people do things for you rather than asking; if it is grief, "
    "Cruse's line is there for exactly this, and your GP is the other door.",
)

PROSE = (
    "Nobody can put a date on that, and I would be making it up if I did. It tends to lift in "
    "patches before it lifts properly - an ordinary afternoon, then a day that feels like the "
    "start again - and a bad day after a good week is not you going backwards. Two things that "
    "help meanwhile: one fixed thing in the week you would turn up to anyway, and one person who "
    "hears the honest version. If it is still spoiling your sleep or your appetite after a few "
    "weeks, that is worth saying to a GP.",
    "It does ease for most people, but not on a timetable, so any date would be a guess. The bad "
    "days usually get further apart before they get shorter, which is worth knowing on a day that "
    "feels like week one again. Until then: keep one routine you do not have to think about, get "
    "outside most days, and tell one person how it actually is. If there is nobody to tell, your "
    "GP is the place to start, and so is a group of people who have been through the same thing.",
    "I can't tell you when, and anyone who can is guessing. What I can say is that it comes in "
    "patches rather than a steady line, and the patches get shorter - the stretch between bad days "
    "widens first. What moves it along is usually other people and a bit of structure rather than "
    "a lot of thinking: a walk with someone, a class, a fixed Sunday call. Your GP is the right "
    "next stop if it is your mood as much as the loss.",
)


# No date, then the one thing the chat already knows. The card's own words are quoted rather than
# paraphrased: they are the part this bot is sure of.
CARD_PROSE = (
    "Nobody can put a date on that one, sorry - it answers to time rather than to anything I can "
    "look up. What shifts it is the everyday bit: {bit}. If it has not moved after a couple of "
    "weeks, that is the point to ask someone who can see the whole picture.",
    "I can't tell you when, and a guess would not help. The part that does the work is the "
    "everyday bit: {bit}. See where it is in a couple of weeks.",
    "There is no date for that, sorry. What moves it is what the first answer said: {bit}. If it "
    "is no different in a couple of weeks, that is when to ask someone who knows the case.",
)

# A card with no time in it gets no deadline from us. "Will it stop" about bullying over the school
# gate has no couple of weeks to give - the card says what to do, not how long it takes - and
# "give it a couple of weeks before you change anything" is advice nobody could stand behind. The
# honest reply is still the card, framed as the thing to go on, and one question that hands the
# judgement back to the person who can make it.
CARD_PROSE_UNTIMED = (
    "There is no date for that one, and I would be making one up. What the answer was pointing at "
    "is still where to put the effort: {bit}. Has it moved at all since?",
    "Nobody can say when, sorry, and a made-up deadline would not help you. What the first answer "
    "said is the part to go on: {bit}. How long has it been going on?",
    "I can't put a time on it. The part that does the work is what was already said: {bit}. What "
    "has changed since it started?",
)

# An ask about it easing ("does it get easier", "will it get better") is not an ask about when:
# opening "nobody can say when" answers a question nobody asked. These say the same honest thing
# without pretending the person asked for a date.
EASES = (
    "It gets easier for most people, and how long that takes varies - a couple of months is not "
    "unusual. What the answer said is the part that does the work: {bit}. Does it feel any "
    "different from the first week?",
    "It usually eases before it stops, and the easing is rarely in a straight line. Keep the thing "
    "the card named up: {bit}. Has it got any easier yet?",
    "That usually does get easier with time, though not evenly. The bit worth keeping up is what "
    "was said: {bit}. Has it eased at all yet?",
)


# The bot's own last answer quoted back: it is the thing to keep up, not news. Saying it again is
# what a friend does - "keep doing the thing that was said" - as long as it is framed that way
# rather than repeated as if it were an answer.
# An instruction opens with a verb ("keep the room dark", "water little and often"); a description
# does not ("those patches are blossom end rot"). Only the first can be handed back as a thing to
# keep up, so a card that opens with a description keeps its own framing.
DOES_IT = frozenset("""
treat keep put believe water ask give use take call try make add move leave stop ring check measure
tell say write get go see book buy cut clean feed walk watch brush cover tie hold run set turn
start begin finish test watch wrap
""".split())

KEEP_UP = (
    "There is no date for that, sorry. What is worth keeping up in the meantime: {bit}. If it has "
    "not changed in a couple of weeks, that is the point to look at one thing and change it.",
    "I can't say when it will stop, and nobody could. The bit that does the work is the everyday "
    "one: {bit}. Give that a couple of weeks before you judge it.",
    "No date on that one, sorry. Keep the everyday bit up - {bit} - and watch for it moving over "
    "the next couple of weeks.",
)

KEEP_UP_UNTIMED = (
    "There is no date for that, sorry. The everyday bit is the part that does the work: {bit}. "
    "Keep that going and see what changes.",
    "I can't say when it stops, and nobody could. What is worth doing in the meantime: {bit}. "
    "What has changed so far?",
    "No date on that one, sorry. Keep the everyday bit up - {bit} - and watch for the first sign "
    "of it moving.",
)

# The same for a card that opens with a description rather than an instruction: nothing to keep up,
# so the honest thing is that what was said still stands.
STILL_STANDS = (
    "No date on that one, sorry. What the first answer said still stands: {bit}. If it is no "
    "different in a couple of weeks, that is the point to change one thing.",
    "I can't put a date on it. The facts have not moved since the first answer: {bit}. Give it a "
    "couple of weeks before you judge it.",
    "Nobody can say when, sorry. What the first answer said holds: {bit}. If nothing has changed "
    "in a couple of weeks, that is the moment to look at one thing.",
)

STILL_STANDS_UNTIMED = (
    "There is no date for that, and I would not invent one. What the first answer said is where "
    "to start: {bit}. Has it moved at all since?",
    "I can't say when, sorry. The part to go on is this: {bit}. How long has it been like this?",
    "Nobody can promise when, and a guess would not help. What the first answer said still "
    "stands: {bit}. What has changed since?",
)

# A card that talks about time can be answered in weeks; one that does not cannot. `hours` counts:
# the puppy card's "four hours at a time" is a real limit the person can use.
TIME_IN_THE_CARD = re.compile(
    r"\b(?:hours?|days?|nights?|weeks?|months?|fortnight|how\s+long|heals?|clears?|settles?|"
    r"eases?|improves?|by\s+the\s+end)\b",
    re.I,
)

# "does it get easier", "will it get better": an ask about easing, not about when.
EASING = re.compile(r"\b(?:easier|better|improv\w*|bearable|less\s+often)\b", re.I)


def _words(text):
    return set(re.findall(r"[a-z']+", text.lower()))


def _same_as_the_last_answer(written, memory):
    """True when the card is the answer the person was just given, word for word at the start."""
    seen = 0
    for turn in reversed((memory or {}).get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "").strip()
        if not said:
            continue
        if said[:60] == written[:60]:
            return True
        seen += 1
        if seen >= 3:
            break
    return False


# The lead an acknowledgement wears before it says anything: "Got it", "Noted:", "Thanks for
# telling me - ". A reply can be short and still be the answer the chat is on - "Your 3 year old
# is up every morning at half four. That's a habit now." is 68 characters and is the thing the
# next question's "it" points at - so length is the wrong fence. What matters is whether there is
# an account of the thing left once the acknowledgement is taken off.
ACK_LEAD = re.compile(
    r"^\s*(?:got\s+it|noted|right|okay|ok|thanks\s+for\s+telling\s+me|fair\s+enough|no\s+problem|"
    r"understood|sure|cheers)\b[^.!?]{0,40}?[.:;,\u2014\u2013-]\s*",
    re.I,
)


def _an_answer_worth_quoting(said):
    """True when a short reply still has an account of the thing in it, not just a nod."""
    content = ACK_LEAD.sub("", str(said or "")).strip()
    return len(re.findall(r"[A-Za-z']+", content)) >= 5


def _the_card_in_the_chat(memory):
    """What the last answer was about, as the knowledge base puts it, or "".

    "will it last forever" after the early-waking card, or "will it stop" after the puppy-alone
    card: the chat is on something and the question is about that thing's course. Nothing here can
    put a date on it, but the card says what moves it, and that is what a friend would say. The
    card is found from the topic line the chat is on, not from the line itself, because the line
    names nothing.
    """
    turns = [((memory or {}).get("topic") or {}).get("text") or ""]
    for turn in reversed((memory or {}).get("turns") or []):
        if isinstance(turn, dict):
            turns.append(str(turn.get("user") or ""))
    try:
        from ..understanding import understand
        from ..knowledge import lookup
    except Exception:  # noqa: BLE001 - a reader that cannot read must not stop the reply
        return ""
    # The last reading is handed back to the reader so that an animal or a thing the chat is on
    # is still in hand: "he cries when i leave" names no dog on its own.
    before = (memory or {}).get("understood") or {}
    for line in turns:
        line = (line or "").strip()
        if not line:
            continue
        try:
            reply = getattr(lookup.find(understand(line, {"understood": before})), "reply", "")
        except Exception:  # noqa: BLE001
            continue
        # Some rows build their reply from the line (the rate ones hold a function), so only a
        # reply that is already words can be quoted.
        if isinstance(reply, str) and reply.strip():
            written = reply.strip()
            # The card the person has already been given is not news: the same words said twice
            # read as a repeat, so they are framed as the thing to keep up. The last answer is
            # the one on the screen, so a card that starts the same way as it is that answer.
            return written, "said" if _same_as_the_last_answer(written, memory) else "card"
    # Nothing in the chat is a card in the knowledge base, but the answer the person already has
    # is: the bot's own last reply is the thing the "it" is about, and quoting its first sentence
    # is telling them what it already said rather than guessing.
    try:
        from . import fallback  # noqa: PLC0415 - fallback imports this module
    except Exception:  # noqa: BLE001
        fallback = None
    for turn in reversed((memory or {}).get("turns") or []):
        if not isinstance(turn, dict):
            continue
        said = str(turn.get("bot") or "").strip()
        if said.endswith("?") or not _an_answer_worth_quoting(said):
            continue
        # A reply that is itself a hedge, a stall or "tell me which bit" is not a card, and
        # quoting it would hand the person their own nothing back.
        if fallback is not None and (fallback._is_a_hedge(said)
                                     or fallback._is_an_ask_which_bit(said)):
            continue
        # A reply that asks something back, or that opens with a frame before a colon ("Nothing
        # said yet for that to be: tell me the thing"), is not about anything yet: there is no
        # fact in it to hand back.
        opening = said[:60].lower()
        if "?" in opening or ":" in opening or "tell me" in opening or "say what" in opening:
            continue
        return said, "said"
    return "", ""


# The first thing the card says, which is the part that says what moves it: "Treat the early
# morning as a night waking, not the start of the day" out of a card that goes on for paragraphs.
FIRST_BIT = re.compile(r"(?<=[.;:])\s+|\s+[\u2014\u2013]\s+")


def _the_first_bit(card, limit=150, skip_openers=False):
    """The card's first sentence or clause, short enough to quote inside a sentence of our own.

    `skip_openers` is for the bot's own last answer: the first thing it said may be the mood
    before the help ("Long morning already. Get outside for ten minutes when you can"), and
    quoting that back says nothing. A card's own first sentence is left alone, where a short one
    can be the whole instruction ("Water little and often.").
    """
    said = str(card or "").strip()
    if not said:
        return ""
    first = FIRST_BIT.split(said, maxsplit=1)[0].strip()
    if skip_openers and len(first) < 30:
        rest = FIRST_BIT.split(said, maxsplit=1)
        if len(rest) > 1 and rest[1].strip():
            first = FIRST_BIT.split(rest[1].strip(), maxsplit=1)[0].strip()
    first = first.rstrip(" .;:")
    if len(first) > limit:
        cut = first[:limit]
        comma = cut.rfind(", ")
        first = cut[:comma] if comma > 40 else cut
        first = first.rstrip(" ,;:-")
    return first


def _leans_on(memory):
    understood = (memory or {}).get("understood") or {}
    lean = understood.get("leans_on") or {}
    return " ".join(lean.get("words") or ())


def _recent(memory, line=""):
    """What was said in the last few turns, so the "it" can be read from the thread itself.

    `leans_on` carries the words of one previous line and not always all of them; a thread about
    self-harm or about a rota has to be visible here whatever the reader above made of it.
    """
    turns = (memory or {}).get("turns") or []
    said = []
    for turn in turns[-4:]:
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("user") or "").strip().lower()
        if text and text != (line or "").strip().lower():
            said.append(text)
    return " ".join(said)


# Wanting to die, said in the ways people actually say it, on the turn after a safety card. The
# words "die" and "dead" also carry a loss, so the phrases are what is matched, not the words.
WISH_TO_DIE = re.compile(
    r"\b(?:want|wanna|wanting)\s+(?:to\s+)?die\b|\bkill\s+myself\b|\bend\s+it\s+all\b|"
    r"\bno\s+(?:point|reason)\s+(?:in\s+)?(?:living|going\s+on|carrying\s+on)\b|"
    r"\bbetter\s+off\s+dead\b|\bdon'?t\s+want\s+to\s+be\s+here\b",
    re.I)

# An age said the way people say it: "im turning 40", "i'm 43", "since i turned 50".
AN_AGE = re.compile(r"\b(?:i'?m|im|i\s+am|turn(?:ing|ed)?|about|nearly|almost)\s+"
                    r"(?:to\s+be\s+)?(?:[1-9]\d)\b", re.I)


def reads(text, memory=None):
    """The course asked about, or None when this is not the shape."""
    line = (text or "").strip()
    if not line or len(line.split()) > 14:
        return None
    words = _words(line)
    if words & MED or words & BODY or words & THING or words & RECOVERY:
        return None
    match = COURSE.search(line)
    lasts = LASTS.search(line)
    if not match and not lasts:
        return None
    if not (ASKS.search(line) or line.endswith("?")):
        return None
    # Something has to make it a feeling: a feeling word in the line, or a heavy thing said a turn
    # or two ago that the "it" is pointing at.
    # "will it always be like this" carries the feeling in the phrase itself: a person asking that
    # is describing a state they are stuck in, not a bus that is slow.
    lean = _words(_leans_on(memory)) | _words(_recent(memory, line))
    # A thread that has just been told about self-harm or about wanting to die is the safety
    # lane's: a shape about grief would be a claim about a recovery, on the turn after it.
    if (words | lean) & DISTRESS or WISH_TO_DIE.search(line + " " + _recent(memory, line)):
        return None
    # A course question about the thing the chat is already on needs no feeling word of its own:
    # "will it last forever" after a child-waking card, "will it stop" after a puppy-alone card.
    # The card knows what moves it, and saying that beats a hedge or a "which bit do you mean".
    # A line that names a feeling itself ("will i ever feel normal again") keeps the caring shape
    # below, which is written for exactly that and says nothing the card would not.
    if not (words & HEAVY):
        card, source = _the_card_in_the_chat(memory)
        if card:
            return CARD_IN_THE_CHAT + ":" + source
        # Nothing in the talk says what "it" is, and no card is on the table: the search hedge
        # sends the person to look for a page about a thing they have not named, and nobody can
        # put a date on something unknown. One short question is the honest reply. What is left
        # to the readers below is a line that is already about how a hard time goes ("does it get
        # easier", "is it always going to be like this", and anything said after a loss), because
        # the caring shape answers that without needing a thing to name; and a "how long" ask,
        # where the rate answer ("a time is a rate times a size") is a real reply with a question
        # of its own.
        asks_about_a_feeling = bool(words & IT_IS_HOW_IT_FEELS)
        about_a_hard_time = bool(lean & HEAVY) or bool(lean & {"died", "death", "funeral", "loss"})
        like_this = bool(match) and "like this" in match.group(0).lower()
        # A chat that has already named the thing has a subject; a card we could not find for it
        # is a job for the knowledge base, not a reason to ask the person what they mean.
        nothing_named = len(_recent(memory, line).split()) < 3
        if (nothing_named and not asks_about_a_feeling and not about_a_hard_time and not like_this
                and not re.search(r"\bhow\s+long\b|\bhow\s+much\b|\bwhat\s+time\b",
                                  line.lower())):
            return NO_SUBJECT
    like_this = bool(match) and "like this" in match.group(0).lower()
    heavy = (like_this or bool(words & HEAVY) or bool(words & {"easier"})
             or bool(lean & HEAVY))
    if not heavy:
        return None
    # "the baby was up three times / does it get easier" is a question about sleep, and "im a
    # nurse, my shifts start sunday night / does it get easier" about a rota. An ordinary
    # life-stage thing in the thread keeps its own answer; a loss outranks it.
    ordinary = bool((words | lean) & ORDINARY) or bool(AN_AGE.search(line + " " + _recent(memory, line)))
    if ordinary and not ((words | lean) & CARE):
        return None
    # A recovery in the thread is the same as one in the line: "i had a section three weeks ago /
    # does it get easier after it" is a question about a body healing, with a clinical timeline a
    # midwife can give. The line's own words are checked above; this is the turn before it.
    if (lean & RECOVERY) and not (lean & CARE):
        return None
    understood = (memory or {}).get("understood") or {}
    if understood.get("body") or understood.get("about_bot"):
        return None
    return (match.group(0) if match else lasts.group(0)).strip().lower()


def reply_for(text, memory=None):
    """One honest answer about the course of it: no date, the shape, and one question."""
    asked = reads(text, memory)
    if not asked:
        return None
    # Vary with the line itself, so two people asking in one chat do not get the same paragraph
    # twice, and so the same line always gets the same answer.
    if asked == NO_SUBJECT:
        said = (text or "").strip()
        pick = (sum(ord(c) for c in said) + 5 * len(said)) % len(NOTHING_NAMED)
        return NOTHING_NAMED[pick]
    if asked.startswith(CARD_IN_THE_CHAT):
        whole, source = _the_card_in_the_chat(memory)
        card = _the_first_bit(whole, skip_openers=(source == "said"))
        if not card:
            return None
        said = (text or "") + "|" + card
        pick = (sum(ord(c) for c in said) + 7 * len(said)) % 3
        # No deadline is put on a card that carries none: "give it a couple of weeks" is a fact
        # about time that only a card with time in it can support.
        timed = bool(TIME_IN_THE_CARD.search(whole))
        if EASING.search(text or ""):
            return EASES[pick].format(bit=card)
        # The bot's own last answer is repeated as the thing to keep up, not as news: a person
        # reading the same advice twice in a row has been told what to do and why it matters.
        if source == "card":
            return (CARD_PROSE if timed else CARD_PROSE_UNTIMED)[pick].format(bit=card)
        first = re.findall(r"[a-z']+", card.lower())
        if first and first[0] in DOES_IT:
            return (KEEP_UP if timed else KEEP_UP_UNTIMED)[pick].format(bit=card)
        return (STILL_STANDS if timed else STILL_STANDS_UNTIMED)[pick].format(bit=card)
    said = (text or "") + "|" + _leans_on(memory)
    pick = (sum(ord(c) for c in said) + 7 * len(said)) % len(PROSE)
    # a loss named in the line itself counts: "does it get easier after a stillbirth" is the same
    # kind of question as one asked the turn after the news, and the caring shape names a door.
    lean = _words(_leans_on(memory))
    if (_words(text) | lean) & CARE:
        return CARE_PROSE[pick % len(CARE_PROSE)]
    return PROSE[pick]
