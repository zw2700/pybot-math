"""A thing, or a pile of them, that is wearing the person down.

"This spreadsheet is killing me", "my inbox is a nightmare", "i have so much marking to do":
nothing is broken, no body hurts and nobody else is in the line, so nothing claimed them and
they all got one of the three stock lines ("I'm listening - say more if it helps"). That is the
example STYLE.md opens with, so the composer answers the wear itself: name it briefly, then ask
the one question that gets the job moving.

Two shapes, because a pile and a single job want different questions:

* a pile of things to do - "i have so much marking to do", "my inbox is a nightmare",
  "the washing is piling up"
* one job that fights back - "this spreadsheet is killing me", "this essay is killing me",
  "painting the hallway is taking forever"

Every rule here is a guard against taking a turn that is not that, and each one is paid for by a
line it must not take:

* never a body: "my back is killing me" and "me knees are killing me" are an ache, and
  bot/compose/trouble.py asks the right question about them. Its reading settles this one;
* never a broken thing: "my boiler is on the blink" is a fault with a next step in it, and that
  is trouble's reply, not a question about how the job is going;
* **never another person**: "my mate at work is a nightmare" and "my kids are driving me mad"
  are about somebody, so they belong to bot/modules/chat.py and to safety, whatever else the
  line says;
* never the weather: "this heat is killing me" is a line about the day, and a question about
  where you are up to with the job is the wrong thing to say to it;
* never a stretch of time: "this week has been a nightmare" and "last night was a nightmare" are
  a rough week or a bad night, not a task, and the week has its own warm reply;
* never a question, and never a plea for tips ("what should i do about my inbox") - those ask
  something back and are answered as questions.
"""
import re

from . import trouble

# The idioms for something wearing you down. Each needs a subject and a copula in front of it,
# so "killing me, honestly" on its own is not a job, and "i'm killing it" is not either.
WEAR = re.compile(r"""
    \b(?:is|are|was|were|'s|its|it's|gets|got|has\s+been|have\s+been|had\s+been)\b
    [^.!?,;]{0,22}?
    \b(?:
        killing\s+me | the\s+death\s+of\s+me
      | doing\s+my\s+head\s+in
      | driving\s+me\s+(?:mad|crazy|nuts|up\s+the\s+wall|round\s+the\s+bend|insane)
      | a\s+(?:(?:real|right|total|proper|absolute|bit\s+of\s+a|such\s+a|bloody)\s+)?
        (?:nightmare|mare|pain|slog|chore)
      | wearing\s+me\s+(?:down|out)
      | getting\s+on\s+top\s+of\s+me
      | taking\s+(?:forever|ages|all\s+day|all\s+week|so\s+long|longer\s+than)
      | never\s+ending | endless
      | (?:getting\s+)?out\s+of\s+control
      | going\s+on\s+forever
      | taking\s+over\s+my\s+life
    )\b
""", re.X)

# A pile rather than one job: "i have so much marking to do", "im snowed under with emails",
# "the washing up is piling up", "my to do list is out of control".
PILE = re.compile(r"""
    \b(?:
        (?:so\s+much|so\s+many|loads\s+of|lots\s+of|tons\s+of|masses\s+of|piles?\s+of|a\s+heap\s+of)
        [^.!?,;]{0,30}?
        \b(?:to\s+(?:do|sort|mark|write|finish|file|get\s+through|deal\s+with|catch\s+up\s+on
                       |work\s+through|go\s+through))
      | (?:i'?m|im|i\s+am|i'?ve|ive|i\s+have|we'?re|we\s+are)\b[^.!?,;]{0,22}?
        \b(?:swamped|snowed\s+under|drowning|behind\s+on|way\s+behind|backed\s+up)
      | \b(?:the\s+)?(?:backlog|to[- ]?do\s+list|housework|ironing|washing\s+up|paperwork)\b
        [^.!?,;]{0,20}?
        \b(?:piling\s+up|stacking\s+up|mounting\s+up|out\s+of\s+control|never\s+ends)
      | \b(?:a\s+)?(?:mountain|heap|pile|ton|tonne|stack)\s+of\s+(?:the\s+|my\s+|our\s+)?[a-z]+
      | \b(?:piling|piling\s+up|stacking\s+up|mounting\s+up)\b
    )
""", re.X)

# A money problem is not a job to work through: "im behind on my rent" and "im behind on the
# council tax" are the answers band's, with a next step in them, and "which one is due first" is
# not what somebody late with the rent needs to hear.
MONEY = frozenset(("rent", "mortgage", "bill", "bills", "debt", "debts", "arrears", "council",
                   "loan", "loans", "overdraft", "credit", "card", "cards", "repayment",
                   "repayments", "interest", "owe", "owed", "fines"))

# A word for the day outside is not a job: the heat and the cold have their own reply.
WEATHER = frozenset(("heat", "cold", "weather", "humidity", "sun", "rain", "summer", "winter",
                     "wind", "snow", "frost", "traffic", "commute", "bus", "train", "tube"))

# A stretch of time said to be a nightmare is a rough week or a bad night, not a task, and the
# warm reply for a rough day (bot/modules/chat.py) already fits it.
A_STRETCH = frozenset(("week", "weeks", "month", "months", "day", "days", "year", "years",
                       "term", "shift", "shifts", "morning", "afternoon", "evening", "night",
                       "nights", "weekend", "fortnight", "time", "while", "hour", "hours"))

# A part of the body the trouble reading does not know yet, so a line about it is still an ache.
EXTRA_BODY = frozenset(("pelvis", "bump", "tummy", "womb", "cervix", "abdomen"))

# Nothing named at all: "everything is getting on top of me" and "its all piling up" are the
# weight of it rather than a job, and bot/modules/chat.py has the warmer reply for them.
NOT_A_JOB = frozenset(("everything", "anything", "things", "thing", "stuff", "life", "all",
                       "lot", "world", "loads", "too", "much", "up", "piling", "stacking",
                       "mounting", "behind", "snowed", "under", "swamped", "drowning",
                       "backed"))

# Words that only point at the thing, so a clause made of these and a stretch of time names no
# job at all ("this week", "the last few days").
POINTING = frozenset(("this", "that", "these", "those", "the", "a", "an", "my", "our", "it",
                      "its", "it's", "last", "past", "few", "couple", "of", "whole", "every",
                      "all", "and", "been", "has", "have", "had", "always", "so", "far", "now",
                      "recently", "lately", "today", "i", "im", "i'm", "ive", "i've", "we",
                      "we're", "with", "to", "many", "again", "on", "out", "control", "sort",
                      "sorting", "sorted"))

# The thing that wears them is their work itself, or the course they are on: "work is killing
# me", "my job is a pain". A question about where they are up to with the job is the wrong one
# for a job, so these ask which part of it is the trouble instead.
ROLE = frozenset(("work", "job", "jobs", "office", "employer", "boss", "school", "uni",
                  "university", "college", "course", "degree", "business", "placement",
                  "apprenticeship", "phd", "thesis"))

PILE_REPLIES = (
    "Then it's a sorting job before it's a doing job: what has to happen today, and what can "
    "wait until next week?",
    "Start with the smallest one and finish it before you look at the rest of the pile.",
    "Piles like that shrink the moment you start. Which one is actually due first?",
    "Ugh. Pick the one that would be a relief to have done, and give it twenty minutes.",
)

JOB_REPLIES = (
    "That one's a slog. What's it fighting you on?",
    "It's usually the fiddly part that eats the time. Which bit is the worst?",
    "Ugh, the kind of job that takes longer than anyone says. Where are you up to with it?",
    "Fair enough - that sort of thing gets into your head. What's the bit you keep putting off?",
)

ROLE_REPLIES = (
    "Then something has to give. Is it the hours, the people, or the work itself?",
    "That wears you down. What's the worst part of it at the moment?",
    "Fair enough - a job like that takes it out of you. What's the bit that does it?",
    "That's worth taking seriously: what would make the week easier?",
)

CONTENT = re.compile(r"[a-z0-9']+")


def pool(shape):
    """The replies for a shape: a pile of things to do, one job that fights back, or the work
    itself."""
    if shape == "pile":
        return PILE_REPLIES
    if shape == "role":
        return ROLE_REPLIES
    return JOB_REPLIES


def reads_as_worn(clean, words=None, repaired=""):
    """'pile' for a stack of things to do, 'job' for one thing that wears, None for anything else.

    `repaired` is the same line with its wrong words put right (the reading's `plain`), and it is
    only consulted when the line as typed is not a job: "this spreadsheat is killing me" is the
    same complaint as the spelled-out line and only the repair knows it."""
    text = " ".join(str(clean or "").lower().split())
    if not text or "?" in text:
        return None  # a question asks something back and is answered as one
    shape = _shape(text, words)
    if shape is None and repaired and repaired != text:
        shape = _shape(repaired)
    return shape


def _shape(text, words=None):
    """The shape of the wear in this one text, or None."""
    words = set(words) if words else set(CONTENT.findall(text))
    if not words:
        return None
    # Another person in the line is somebody's behaviour, not a job.
    if trouble.someone_elses(words):
        return None
    # An ache and a fault already have their own question.
    if trouble.reads_as_trouble(text, words):
        return None
    if trouble.PLEA.search(text):
        return None
    if words & WEATHER:
        return None
    if words & MONEY:
        return None
    for match in PILE.finditer(text):
        # The pile idiom carries the thing itself ("so much marking to do", "snowed under with
        # emails"), so the whole line is read for it; the idiom's own words do not count.
        if _names_a_job(text):
            return "pile"
    for match in WEAR.finditer(text):
        # The wear idiom is not the thing itself: "this week has been a nightmare" names a week.
        subject = text[:match.start()]
        # A body in front of the idiom is an ache: "me knee is killing me" is the same complaint
        # as "my knee is killing me", and the repair is what makes trouble's reading see it.
        if set(CONTENT.findall(subject)) & (trouble.BODY_PART | EXTRA_BODY):
            continue
        if _is_a_role(subject):
            return "role"
        if _names_a_job(subject):
            return "job"
    return None


def _content_words(clause):
    """The words of a clause that name something, without the ones that only point at it."""
    return [word for word in CONTENT.findall(clause)
            if word not in POINTING and word not in A_STRETCH]


def _is_a_role(clause):
    """True when the wear is about their work or their course, and nothing else.

    "work is killing me" and "my job is a pain" are the job itself; "this spreadsheet is killing
    me" is one task inside it, which wants a question about the task."""
    content = _content_words(clause)
    return bool(content) and all(word in ROLE for word in content)


def _names_a_job(clause):
    """True when the clause names something to be done, not just a stretch of time.

    "this week has been a nightmare" and "the last few days have been a slog" name a week and
    days, and a question about where they are up to with the job is nonsense for both."""
    content = _content_words(clause)
    return bool(content) and not all(word in NOT_A_JOB for word in content)
