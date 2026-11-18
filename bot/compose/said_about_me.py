"""Someone's judgement of the person, reported: "my mum says im not trying hard enough".

The store files the line as a fact and hands it back - "Noted: your mum says you're not trying
hard enough" - which is the one reply a person who has just been criticised at home does not
want. The other end of the same line is worse: "my sister says im a cow" came back as
"Cow - good to know. What do you like most about it?", a question about a farm animal.

What they are telling you is not a fact about their mother. It is what it is like to be spoken to
that way, so the reply has to land on that: say the sting is real, and ask the one thing that
opens it up - what it was about, whether it is new, or what they make of it.

Read here by shape, not by wording: a person who is close (a parent, a sibling, a teacher, a
boss - and the bare "he says"/"she says" that people type when the person is obvious from the
last turn), a verb of saying, and then a verdict on the person in the first person. Every way of
writing that is the same line, so every one of them gets the same kind of answer.

Two things stand it down, both deliberate. A line with violence, fear or control in it keeps
whatever it had: "my husband says im worthless" is the domestic abuse card in `bot/modules/
safety.py`, and a composer reader taking it away would be a real loss. And the partner-ish
subject is left alone for the same reason - a partner who calls you useless is the case that card
is for, and whether a mother's "you're lazy" belongs there too is #safety's call, not this
module's.
"""
import re

from . import pick

# The people whose opinion of the person is ordinary friction rather than a safety case. A
# partner, husband, wife, boyfriend and carer are deliberately absent: see the note above.
# One close person, then the plural of it: "my friends say im boring" and "my parents think im a
# failure" are the same line as the singular, and read against a list of singulars alone they were
# not read at all - the first got the bot's own self-judgement line back, as if the person had said
# it about themselves, and the second the knowledge base's advice about a voice in their head.
_A_CLOSE_PERSON = (r"(?:mum|mom|mam|mammy|mother|dad|father|daddy|stepmum|stepmom|stepdad|"
                   r"stepfather|stepmother|parent|nan|nana|gran|granny|grandma|grandad|"
                   r"grandpa|grandmother|grandfather|sister|brother|sis|bro|son|daughter|"
                   r"child|kid|teenager|teacher|tutor|head\s+teacher|boss|manager|"
                   r"colleague|friend|mate|neighbour|neighbor|uncle|aunt|auntie|"
                   r"mother[\s-]in[\s-]law|father[\s-]in[\s-]law|in[\s-]laws|cousin)")
CLOSE_PERSON = _A_CLOSE_PERSON + r"(?:s|es)?"
# "my mum says", "my dad told me", "she keeps telling me": the subject, then a verb of saying.
# The bare pronoun is in because that is how a second turn reads - "she says im lazy" after a line
# about a sister - and the reply asks rather than assumes who it is.
_SUBJECT = (r"(?:(?:my|our)\s+" + CLOSE_PERSON + r"|(?:he|she|they))")
_SAYING = (r"(?:say|says|said|saying|tell|tells|told|telling|think|thinks|thought|reckon|"
           r"reckons|moan|moans|moaned|complain|complains|complained|goes|went)"
           r"(?:\s+(?:me|that|how))?")
# The verdict itself: first person, about them. "im lazy", "i'm not trying hard enough",
# "i dont apply myself", "i never listen", "i cant do anything right".
# A verdict is a judgement of the person, not a state they are in. "she just says im fine" is her
# own answer passed on - the person is telling you she keeps saying she is all right - so the
# states people report each other in are not verdicts and get no answer from here. Advice
# ("my sister says i shouldnt tell a chatbot personal stuff") is the same: what follows "im" has to
# be a label or a complaint about what they do, not an instruction.
_A_STATE = (r"(?!fine\b|ok\b|okay\b|alright\b|all\s+right\b|good\b|great\b|grand\b|"
            r"tired\b|busy\b|hungry\b|sleepy\b|bored\b|sad\b|happy\b|upset\b|angry\b|"
            r"cross\b|late\b|early\b|right\b|wrong\b)")
# "im fat" and "im getting fat" are the same verdict said at two paces, and the second one was
# missed by a reader that only took the adjective straight after the person: "my nan says im
# getting fat" fell through to a food pool. What can follow "getting" is a short list of what
# people are told they are turning into - "getting a dog" is a present, not a verdict.
_GETTING = (r"(?:getting|putting\s+on|gone)\s+(?:a\s+bit\s+|so\s+|really\s+|too\s+)?"
            r"(?:fat|big|heavy|chubby|large|weight|old|older|slow|slower|forgetful|lazy|"
            r"picky|soft|naughty|moody|grumpy|difficult)")
_VERDICT = (r"(?:i(?:'?m|\s+am|\s+aint|m)\s+" + _GETTING
            + r"|i(?:'?m|\s+am|\s+aint|m)\s+"
            r"(?:not\s+|so\s+|too\s+|just\s+|always\s+|really\s+)?"
            r"(?:a\s+|an\s+|the\s+)?" + _A_STATE + r"[a-z']+)")
# What sits between the person and the verb of saying: "my mum keeps saying", "she is always
# telling me", "my boss just said". A gap of any words at all is what let "she says shes fine but
# i dont believe her" through as a verdict on the person, so only these are allowed.
_BEFORE_SAYING = (r"(?:\s+(?:keeps?|kept|always|constantly|regularly|just|still|also|now|"
                  r"honestly|literally|basically|straight|even))*(?:\s+is|\s+was)?\s*")
# ...and what sits between the verb and the verdict: "tells me im useless", "said that im lazy".
_AFTER_SAYING = r"\s+(?:(?:me|that|to\s+me|straight|honestly|basically|again|either)\s+){0,2}"
# A label on the person ("im lazy", "im a cow") and an accusation about what they do ("i never
# listen", "i dont care about her") are the same shape and not the same thing to be told: the
# first is a judgement of them, the second is a charge they will want to answer. They are kept
# apart so the reply can be about the one the line actually made.
_ACT = (r"(?:i\s+(?:dont|don't|do\s+not|never|always|keep|can'?t|cannot|wont|won'?t|"
        r"made|make|mess|screw))")
REPORTED_LABEL = re.compile(
    r"\b" + _SUBJECT + r"\b" + _BEFORE_SAYING + r"\b" + _SAYING + _AFTER_SAYING
    + _VERDICT + r"[a-z']*", re.I)
REPORTED_ACT = re.compile(
    r"\b" + _SUBJECT + r"\b" + _BEFORE_SAYING + r"\b" + _SAYING + _AFTER_SAYING + _ACT, re.I)
REPORTED = REPORTED_LABEL

# The words that make the same shape a safety case rather than a family row. A line that has one
# of these keeps the card it already had.
_DANGER = re.compile(
    r"\b(?:hit|hits|hitting|hurt|hurts|hurting|punch|punched|kick|kicked|slap|slapped|push|"
    r"pushed|pushing|throw|threw|thrown|strangle|strangled|choke|choked|choking|threat|"
    r"threatens|threatened|threatening|scared|scary|frightened|afraid|terrified|fear|"
    r"unsafe|not\s+safe|safety|lock|locked|locks|police|arrest|bruise|bruises|bleeding|"
    r"kill|kills|killing|dead|die|suicide|self[\s-]harm|starve|starving|withhold|"
    r"control|controlling|controls|track|tracks|tracking|monitor|monitors|isolate|"
    r"money|phone|passport|keys|drink|drunk|drugs|scream|screams|screaming|shout|shouts|"
    r"shouting|yell|yells|yelling|swear|swears|swearing|silent\s+treatment|ignores\s+me)\b", re.I)

# The subject whose criticism is the abuse card's own case, so it is left exactly as it is.
_PARTNER = re.compile(
    r"\b(?:my|our)\s+(?:husband|wife|partner|boyfriend|girlfriend|fiance|fiancee|"
    r"ex|ex[\s-]?(?:husband|wife|partner|boyfriend|girlfriend)|hubby|carer|"
    r"step[\s-]?dad|step[\s-]?mum|step[\s-]?father|step[\s-]?mother)\b", re.I)

# Who said it decides which question is worth asking. A parent and a boss are not the same
# problem: one is about being seen at home, the other about a job.
# A grandparent is not a parent: "my nan says im getting fat" was answered "It lands hardest
# from a parent", which reads as if the reader had not heard who said it. They are the same
# generation as a parent and a different place in the family, so the pool of their own says so.
_GRANDPARENT = re.compile(r"\b(?:nan|nana|gran|granny|grandma|grandad|grandpa|grandmother|"
                          r"grandfather)s?\b", re.I)
_PARENT = re.compile(r"\b(?:mum|mom|mam|mammy|mother|dad|father|daddy|stepmum|stepmom|"
                     r"stepdad|stepfather|stepmother|parent)s?\b", re.I)
_SIBLING = re.compile(r"\b(?:sister|brother|sis|bro)s?\b", re.I)
_WORK = re.compile(r"\b(?:boss|manager|colleague)s?\b", re.I)
# A teacher is not a boss: "you're not up to it at work" is the wrong room for "my teacher says
# im lazy", and the question worth asking is about one piece of work rather than a job.
_SCHOOL = re.compile(r"\b(?:teacher|tutor|head\s+teacher|lecturer|form\s+tutor)s?\b", re.I)

_PARENT_LINES = (
    "That is a hard thing to hear from your mum or dad, and it says more about the day they are "
    "having than about you. Is this how they usually talk, or is it new?",
    "It lands hardest from a parent, whoever else says the same thing. What did they want you to "
    "be doing differently?",
    "Parents say the thing that will sting without meaning to. Has it been like this a while, or "
    "did something happen today?",
)
_GRANDPARENT_LINES = (
    "That is the kind of thing a nan says and then worries about. How did it land - did it come "
    "out of the blue, or is it a theme?",
    "Grandparents talk about weight in a way their own generation did, and it still stings coming "
    "from someone who is supposed to be on your side. What did you say back?",
)
_SIBLING_LINES = (
    "Brothers and sisters know exactly where to aim. Is this how they always talk to you, or "
    "has something changed?",
    "That is a sibling's line if ever there was one. Do they mean it, or is it the way they talk "
    "when they are in a mood?",
)
_WORK_LINES = (
    "That is a rough thing to hear where you are trying to do a job. Was it a fair point about the "
    "work, or was it a dig?",
    "Being told you are not up to it at work is a heavy thing to carry home. Has it come up more "
    "than once?",
    "A comment like that is easier to carry when you know what it was about. What was the job they "
    "were talking about?",
)
_SCHOOL_LINES = (
    "Being marked down by a teacher lands differently from being told it at home. Is it this "
    "subject, or all of it?",
    "A teacher saying that is usually about one piece of work, not about the whole person. What "
    "was it about?",
    "That is the kind of comment that sticks, and it says as much about their marking as about "
    "you. Has it been said more than once?",
)
# Being told what you are like is one thing; being told what you do, or do not do, is a charge,
# and the reply that lands is the one that asks what is behind it rather than consoling them for
# something nobody has said about them.
_ACCUSED_LINES = (
    "That sounds like an old argument wearing a new coat. What makes her say it?",
    "Being told you do not care, when you clearly do, is a maddening thing to hear. What set it "
    "off?",
    "It is worth asking her straight what she means by it. What would she want you to do "
    "differently?",
    "That is a charge, not a small thing. How long has it been going on?",
)
_GENERIC_LINES = (
    "That is a rough thing to be told. What did they want you to do differently?",
    "Somebody saying that to you says more about them than about you. How did it land - did you "
    "believe it?",
    "That is a hard thing to hear, whichever way round it was meant. What do you think is behind "
    "it?",
)


# Somebody else's words, with the person in the first person inside them: "my sister says im a
# cow", "he reckons im a nightmare at work". Any reader that takes "im a <noun>" as a role, an age
# or a thing liked reads the label as the person's own and answers it as if it were. Asked here, so
# every one of them can stand down on the same test.
_REPORTING = re.compile(
    r"\b(?:he|she|they|him|her|them|" + CLOSE_PERSON.replace("(?:", "(?:", 1) + r")\b"
    r"[^.?!]{0,25}?\b(?:say|says|said|saying|tell|tells|told|telling|think|thinks|thought|"
    r"reckon|reckons|reckoned|goes|went|call|calls|called|calling|moan|moans|complain|complains)"
    r"\b[^.?!]{0,20}?\b(?:i(?:'?m|\s+am)|im)\b", re.I)


def reads_as_somebody_elses_words(text):
    """Whether the person is quoting what somebody close calls them, in their own words."""
    said = " ".join(str(text or "").split())
    return bool(said) and bool(_REPORTING.search(said))


def _kind(text):
    """Which of the two the line is: "label" for a name they were called, "act" for a charge
    about what they do, and "" for neither."""
    said = " ".join(str(text or "").split())
    if not said or "?" in said:
        return ""
    if _DANGER.search(said) or _PARTNER.search(said):
        return ""
    if REPORTED_LABEL.search(said):
        return "label"
    if REPORTED_ACT.search(said):
        return "act"
    return ""


def reads_as_reported_judgement(text):
    """Whether the line is somebody close handing the person a verdict about themselves."""
    return bool(_kind(text))


# The same remark coming back with a frequency on it - "she says it every time i visit", "he does
# it all the time", "it happens whenever we talk" - is no longer one comment, it is the shape of
# the visits, and the answer is what to do with a pattern rather than what to say about a comment.
_A_HABIT = re.compile(
    r"\b(?:every\s+time|every\s+(?:day|visit|week|night|time)|all\s+the\s+time|always|"
    r"constantly|whenever|each\s+time|again\s+and\s+again|keeps?\s+(?:doing|saying|going)|"
    r"again\s+today|it\s+happens|she\s+does\s+it|he\s+does\s+it|they\s+do\s+it)\b", re.I)
_HABIT_LINES = (
    "Then it is a pattern, not a comment, and a fresh answer each time is what keeps it going. "
    "Pick one sentence and use the same one every time, said calmly and early: \"I have heard "
    "you, and I am not going to argue about it today.\"",
    "If it comes up again and again, say once at the start that you are not going over it this "
    "time, and then do not take the bait. Naming it before it lands takes the teeth out of it.",
    "A remark that comes every time needs a conversation at a calm moment rather than in the "
    "moment it happens. What would you want to say to her when nothing is going on?",
)


def _user_lines(memory, how_many=3):
    turns = (memory or {}).get("turns") if isinstance(memory, dict) else None
    if not turns:
        return []
    out = []
    for turn in turns[-how_many * 2:]:
        if not isinstance(turn, dict):
            continue
        line = str(turn.get("user") or "")
        # The store records the turn it is given and the store's copy of it, so the same line can
        # arrive twice in a row; the thread is read from the lines, not from the records.
        if not out or out[-1] != line:
            out.append(line)
    return out[-how_many:]


def _on_the_thread(memory):
    """Whether the person has just been talking about being spoken to that way.

    The judgement itself, or the remark coming round again - "she says it every time i visit",
    "and he does it all the time" - is the same thread, so a third turn stays on it too.
    """
    lines = _user_lines(memory)
    if not lines:
        return False
    if reads_as_reported_judgement(lines[-1]):
        return True
    return (len(lines) > 1 and bool(_A_HABIT.search(lines[-1]))
            and reads_as_reported_judgement(lines[-2]))


def answer_followup(text, memory=None):
    """A reply when the judgement just described is said to happen again and again, or ""."""
    said = " ".join(str(text or "").split())
    if not said or "?" in said or len(said.split()) > 12:
        return ""
    if _DANGER.search(said) or not _A_HABIT.search(said):
        return ""
    if not _on_the_thread(memory):
        return ""
    return pick(_HABIT_LINES, memory if isinstance(memory, dict) else {}, said)


# A reply that takes the words as the person's own judgement of themselves - "you're being harder
# on yourself than you'd be on a friend", "that's a heavy way to feel about yourself" - is the
# right reply to "im a disappointment", and the wrong reply to "my aunt says im a disappointment
# to the family". When somebody else is quoted, a line that talks to them about how they feel
# about themselves is answering a judgement they did not make.
_SELF_ADDRESSED = re.compile(
    r"\b(?:yourself|how\s+you\s+feel|feel\s+about\s+yourself|you\s+feel\s+like|"
    r"youd\s+be\s+on\s+a\s+friend|harder\s+on\s+yourself)\b", re.I)


def speaks_to_a_self_judgement(reply):
    """Whether the reply answers the person as if they had judged themselves."""
    said = " ".join(str(reply or "").split())
    return bool(said) and bool(_SELF_ADDRESSED.search(said))


def answer_for(text, memory=None):
    """A reply to a reported judgement, or "" when the line is not one."""
    if not reads_as_reported_judgement(text):
        return ""
    said = " ".join(str(text or "").split())
    if _kind(said) == "act":
        return pick(_ACCUSED_LINES, memory if isinstance(memory, dict) else {}, said)
    if _SCHOOL.search(said):
        pool = _SCHOOL_LINES
    elif _WORK.search(said):
        pool = _WORK_LINES
    elif _SIBLING.search(said):
        pool = _SIBLING_LINES
    elif _GRANDPARENT.search(said):
        pool = _GRANDPARENT_LINES
    elif _PARENT.search(said):
        pool = _PARENT_LINES
    else:
        pool = _GENERIC_LINES
    return pick(pool, memory if isinstance(memory, dict) else {}, said)
