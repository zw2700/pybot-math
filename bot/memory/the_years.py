"""A line about feeling old, answered as the thing it is.

Getting older comes up in ordinary chat and there was nothing to answer it with. On main every
one of these was a shrug, an echo or a line for a disclosure:

```
i feel old                                -> I'm listening - say more if it helps.
i feel ancient                            -> Thanks for telling me - I'm here if you want to dig into any of that.
im past it                                -> Got it. Is there anything you'd like a hand with?
i feel my age today                       -> Got it. Is there anything you'd like a hand with?
im too old for this                       -> Got it. Is there anything you'd like a hand with?
im turning 40 next month and i feel old   -> That's lovely news - and something to look forward to.
```

and one worse: **"im getting old" was answered "Nice. How long do you reckon it'll take?"**, the
reader for a length of time ("how long does a chicken take") taking the "getting" and the whole
line with it.

A friend does three things with a line like this: agrees about the body in a word, refuses the
verdict (feeling old is usually a bad night, a birthday or a thing they cannot do any more rather
than an age), and asks what brought it on - because there always is something behind it.

What keeps it narrow:

* it is the person's own line. Somebody else's age ("how old is my mum") and a body that hurts
  in the cold ("my knees are 80 years old") belong to the readings that own them.
* a birthday on its own ("i turn 30 next week", "im 67") is news or a fact, not a feeling, and
  the pools here are only for the line that says how it feels.
* the age, when one is said, is answered as an age: "40 next month and i feel old" is a birthday
  coming, so the reply is about that rather than about being old in general.
"""
import re

from ..compose import pick
from .passing_the_time import _the_chat_is_heavy

# A line that names forgetting is answered by the card for it, whatever it says about the years.
# The words are the ones that card keeps its own reading on; "memory" on its own is not one of
# them ("my memory is bad" has no card at all), so it stays with the age pools.
_FORGETTING = re.compile(
    r"\b(?:forget|forgets|forgetting|forgetful|forgetfulness|forgot|forgotten)\b", re.I)

# A body that is being treated is the illness reading's: "my body is falling apart since the
# chemo" is a line about the chemo, and the age pool said "Old is a number that only feels heavy
# on some days" over the top of it (upbeat-paper, #7843).
_TREATMENT = re.compile(
    r"\b(?:chemo|chemotherapy|radiotherapy|cancer|tumour|tumor|surgery|operation|treatment|"
    r"diagnosis|diagnosed|recovering|recovery|hospital|illness|condition)\b|\bafter my\b", re.I)
# A second subject with a card of its own: "i feel old and my hair is going grey" is the greying
# answer, and the age line buried it.
_OWN_SUBJECT = re.compile(
    r"\b(?:hair|grey|gray|greying|graying|teeth|dentures|hearing|glasses|wrinkles?|skin)\b",
    re.I)
# A line that says how much they dislike it is a complaint, and the complaint reading answers it
# better than a line about the years: "im getting old and i hate it".
_DISLIKE = re.compile(
    r"\b(?:hate|hates|hating|can't stand|cant stand|fed up|sick of)\b", re.I)

_LIMIT = 16  # words. A longer line is a story, and a story is answered as one.

# How the feeling is said: the words that make this about age rather than about a body.
_FEELING = re.compile(
    r"\b(?:"
    r"feel(?:ing|s|ing)?\s+(?:so\s+|really\s+|quite\s+|very\s+|a bit\s+|pretty\s+)?"
    r"(?:old|ancient|past it|my age|like an old (?:man|woman|person)|like a pensioner|"
    r"about (?:90|100|eighty|ninety))\b"
    r"|feeling (?:old|ancient|my age)\b"
    r"|past it\b"
    r"|getting old\b|growing old\b|getting on a bit\b"
    r"|too old for (?:this|that|it|all this)\b"
    r"|not (?:young|getting) (?:any more|anymore)\b"
    # The same thing said as a comparison with their own younger self, which is how most people
    # say it: "im not as young as i used to be", "not as fit as i was". The comparison has to be
    # with the speaker ("hes not as young as he was" is a line about him, and it has no first
    # person anyway, so _SELF below keeps it out).
    r"|not (?:as|so) (?:young|fit|quick|strong) as (?:i|we)\b"
    # "over the hill" and its cousin "past it" are the idiom for this, and both were met with the
    # shrug: it is not a thing anybody says about a hill they are standing on, so the idiom is
    # read when it is said about the speaker. A named place keeps its own answer ("a pub over
    # the hill" is directions).
    r"|(?:i'?m|i am|im|i feel|i'?m feeling|i feel like i'?m)\s+(?:a bit\s+|a little\s+)?"
    r"over the hill\b"
    r"|feel(?:ing)?\s+(?:like\s+)?(?:a bit\s+)?(?:past|passed) it\b"
    # "getting on" without the "a bit": "im getting on", "im getting on now". Only as a report of
    # themselves and only where the line ends, so "im getting on with the washing" and "how are
    # you getting on" keep the answers they had.
    r"|\b(?:im|i'?m|i am)\s+getting on\b"
    r"(?=\s*(?:$|[.,!?]|now\b|these days\b|in years\b|a bit\b))"
    r"|(?:the years?|age) (?:are |is )?(?:catching up|creeping up)\b"
    r"|feel(?:ing)?\s+(?:\d\d|like (?:i'?m |i am )?\d\d|ninety|eighty|seventy)\b"
    r"|(?:my )?(?:body|knees|back) (?:is|are) (?:letting me down|falling apart)\b"
    r")", re.I)
# The person, in the first person: somebody else feeling their age is a line about them, and the
# reading for a person already answers it.
_SELF = re.compile(r"\b(?:i|im|i'm|iam|i am|me|my|mine)\b", re.I)
_OTHER = re.compile(
    r"\b(?:my (?:mum|dad|mother|father|gran|nan|grandad|grandma|grandpa|husband|wife|partner|"
    r"son|daughter|sister|brother|friend|boss|neighbour)|he|she|they|them|his|her|their)\b", re.I)
# A part of the body doing something on its own is a complaint about the body, not a remark
# about age: "my knees are 80 years old" belongs to the ache readings.
_BODY_CLAIM = re.compile(
    r"\b(?:knees?|hips?|back|shoulders?|joints?|wrists?|ankles?|feet|hands?|neck|spine)\b"
    r".{0,24}\b(?:hurt|hurts|aching|aches|stiff|sore|clicking|giving way)\b", re.I)
_ASK_START = re.compile(
    r"^\s*(?:is|are|was|were|will|would|shall|should|can|could|do|does|did|when|what|how|why|"
    r"where|who|any)\b", re.I)
_AGE = re.compile(
    r"\b(?:turning|turn|turned|hitting|hitting|becoming|40|50|60|70|80|ninety|forty|fifty|sixty|"
    r"seventy|eighty)\b", re.I)
# A birthday is said with a time on it: "40 next month", "turning 50 in may", "30 last week".
_BIRTHDAY = re.compile(
    r"\b(?:turning|turn|hitting|(?:am|im|i'm)\s+(?:going to be)?)\s+"
    r"(?:\d\d|forty|fifty|sixty|seventy|eighty|ninety)\b"
    r"|\b\d\d?\s+(?:next|this|in|last)\s+(?:week|month|year|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\b", re.I)

OLD_LINES = (
    "It is mostly the body sending invoices. What is it that made you feel it today?",
    "That is usually one bad night or one bad morning rather than an age. What set it off?",
    "Some days the body reports in and everything creaks. What is yours doing at the moment?",
    "Old is a number that only feels heavy on some days. What brought it on today?",
    "I would not take one bad day as a verdict. What has been hard work lately?",
    "Everything hurts and nothing is where you left it. What is the worst of it just now?",
)
PAST_IT_LINES = (
    "Past it at what, though? Say the thing you have decided you cannot do and we will look at it.",
    "I would want to know which thing has gone past you. What is it?",
    "That is a hard thing to decide about yourself. What is it that has started to feel beyond you?",
    "Give me the thing it is about - a job, a walk, a hobby - and we can see if it really has.",
)
TOO_OLD_LINES = (
    "Too old for it, or just tired of it? What is the thing that has got too much?",
    "There is a difference between too old and had enough. Which is it?",
    "Then do it your own way or not at all. What is it that has gone past the point of being fun?",
)
MY_AGE_LINES = (
    "Some days the body reports in and the rest of us just listen. What is doing the reporting?",
    "A day that feels its age usually had something in it. What has yours had?",
    "Then today is a slower one. What is on it?",
)
BIRTHDAY_LINES = (
    "{turn} - a birthday makes everybody take stock, and that is all this usually is. "
    "What are you dreading about it?",
    "The birthday is the loud part; the feeling is usually something else. What is behind it?",
    "Nothing changes overnight at {turn}. What have you started noticing?",
    "Everybody does this around a birthday. What would you want the next year to look like?",
)
# Noticing how young everyone else is: the feeling is a comparison rather than an ache, and the
# reply says so.
COMPARISON_LINES = (
    "That is other people getting younger rather than you getting old. Who were you looking at?",
    "The world does look younger from here. What was it that made you notice?",
    "Everybody under thirty starts to look like a child at some point. What brought it on?",
)


def _the_turn(clean):
    """("40 next month", ...) when the line says a birthday is coming, else None."""
    found = _BIRTHDAY.search(clean)
    if not found:
        return None
    return " ".join(found.group(0).split())


def reply(text, memory):
    """A warm, specific answer to a line about feeling old, or None."""
    clean = " ".join(str(text or "").replace("\u2019", "'").split())
    if not clean or len(clean.split()) > _LIMIT:
        return None
    if "?" in clean or _ASK_START.match(clean):
        return None
    if not _FEELING.search(clean):
        return None
    said = bool(_SELF.search(clean)) or bool(
        re.match(r"^\W*(?:the years|it is|its|age)\b", clean, re.I))
    if not said or _OTHER.search(clean) or _BODY_CLAIM.search(clean):
        return None
    if _FORGETTING.search(clean):
        # The memory is the second half of the line and it has an answer of its own: "im getting
        # old and forgetting things", "im getting old and forgetting names" and "i forget things
        # all the time and i feel old" all answer the forgetting with a real card, and feeling
        # old standing on top of it said the smaller thing. "my memory is bad" has no card, so it
        # is left to the age pools. (rose-lotus, #7843.)
        return None
    if _TREATMENT.search(clean) or _OWN_SUBJECT.search(clean) or _DISLIKE.search(clean):
        # The rest of the line has an answer of its own, and it is the bigger half of what was
        # said: a treatment, a body part with a card, or a plain dislike. All three keep the
        # answer they had before this reading existed.
        return None
    if _the_chat_is_heavy(memory):
        # A line about feeling old after a death or a diagnosis belongs to the reading that is
        # carrying that, not to small talk about the years.
        return None
    seed = str(text or "")
    turn = _the_turn(clean)
    if turn:
        turn = turn[0].upper() + turn[1:]
    if turn:
        # The birthday is part of the line, so the frame is filled before the pool is picked:
        # `pick` takes the line as its seed and nothing else.
        pool = tuple(line.replace("{turn}", turn) for line in BIRTHDAY_LINES)
        return pick(pool, memory, seed_text=seed)
    if re.search(r"\b(?:past|passed) it\b|\bover the hill\b", clean, re.I):
        return pick(PAST_IT_LINES, memory, seed_text=seed)
    if re.search(r"\btoo old\b", clean, re.I):
        return pick(TOO_OLD_LINES, memory, seed_text=seed)
    if re.search(r"look at|young people|teenagers|schoolchildren|all these kids", clean,
                 re.I):
        return pick(COMPARISON_LINES, memory, seed_text=seed)
    if re.search(r"\bmy age\b", clean, re.I):
        return pick(MY_AGE_LINES, memory, seed_text=seed)
    return pick(OLD_LINES, memory, seed_text=seed)
