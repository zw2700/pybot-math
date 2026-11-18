"""A stretch of the day already spent on one thing, said while it is still going on.

"ive been waiting for the plumber since nine" was answered "Got it. Is there anything you'd like a
hand with?", "ive been chasing the bank for two weeks" was filed with "Noted: you've been chasing
the bank for two weeks.", and "ive been painting the fence all morning" got the receipt that asks
for the one thing the line had just given: "You've been painting the fence all morning, how long
have you been at it?" (bot/memory/ack.py, GOING_TAIL). None of those is a friend's reply to
somebody who has been kept waiting, or who is halfway through a job.

The reading is the shape of the line rather than its words: first person, `been`, a doing, and a
stretch of time in the same line. What the doing is decides the reply -- waiting on other people,
a job of their own, or looking after somebody -- and a state of the body or the mood is left to
the readers that already own it. The reply names the stretch the person gave and never the
activity, so one pool covers a fence, a loft and a pile of marking, and the question it asks is
the only one left open: how close to done, whether anyone has answered, or whether anybody gives
them a break.

It is asked from bot/modules/greeting.py, and only ever in place of a placeholder -- the three
stock lines, a receipt, a search hedge or the person's own words said back -- so a line the
composer has an answer of its own for keeps it. It lives in its own file because
bot/compose/fallback.py is at the world's size cap.
"""
import re

from . import fallback, fallback_data
from ..memory import ack


# A stretch of time the person is still inside, spent on one thing: "i've been painting the fence
# all morning", "ive been waiting for the plumber since nine", "ive been on hold for 40 minutes",
# "ive been looking after my mum all week". None of these is a report of something finished
# (bot/compose/remark.py), a plan or a fault, so they reached the receipt that says the line back
# with a question already answered in it - "You've been painting the fence all morning, how long
# have you been at it?" asks for the one thing the person just gave - or the stock line that fits
# any message at all. A friend says the stretch back and asks the only question that is left: how
# close the job is to done, whether anyone has answered, or whether anybody is helping with the
# person they are carrying. The reply names the stretch and never the activity, so one pool covers
# a fence, a loft and a pile of marking, and the shape of the stretch (a job of their own, waiting
# on other people, looking after somebody) decides which of the three it is.
BEEN_ON_A_STRETCH = re.compile(
    r"\b(?:ive|i've|i\u2019ve|i have|i had|weve|we've|we\u2019ve|we have|i)\s+been\b"
    r"(?P<doing>[a-z' ]{3,60}?)"
    r"(?P<when>\ball (?:day|night|morning|afternoon|evening|week|weekend|month|year|shift|term)\b"
    r"|\b(?:most of the|the whole|the entire)\s+(?:day|morning|afternoon|evening|week|weekend)\b"
    r"|\bfor (?:ages|ever|hours|days|weeks|months|years|minutes|a while|half an hour"
    r"|(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|"
    r"forty|fifteen|\d+)\s*"
    r"(?:hour|hours|minute|minutes|day|days|week|weeks|month|months|year|years))\b"
    r"|\b(?:ever since|since (?:this |last |the )?(?:morning|afternoon|evening|night|week|"
    r"weekend|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|"
    r"march|april|may|june|july|august|september|october|november|december|christmas|easter|"
    r"yesterday|noon|midnight|half (?:past )?(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve)|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"\d+(?::\d+)?\s*(?:am|pm)?))\b"
    r"|\b(?:hours|days|weeks|months|years|ages)\s+now\b\s*)",
    re.I)
# The same stretch where the doing is only pointed at, or where the line counts the day's cost
# instead of naming the job: "ive been at this all morning and its still not done", "ive spent all
# day on this form", "this has taken me all afternoon", "ive been sat here for two hours waiting".
# Every one of those reached the stock line or worse - "ive spent all day on this form" was told
# "Nice one. How did the rest of it go?" - because the activity is the one thing a person mid-way
# through a job does not bother to name: they say "this", and expect to be understood. The stretch
# is still in the line, so the same three pools apply; "at it" and "this" are a job of their own,
# and a wait said after the stretch ("for two hours waiting") is still a wait.
POINTER_STRETCH = (
    "at this", "on this", "at it", "on it", "at that", "on that", "at these", "on these",
    "with this", "with it", "the thing")
SPENT_ON_A_STRETCH = re.compile(
    r"\b(?:ive|i've|i\u2019ve|i have|i|weve|we've|we\u2019ve|we have|we)\s+(?:spent|wasted)\b"
    r"(?P<doing>[a-z' ]{0,40}?)\s*"
    r"(?P<when>\ball (?:day|night|morning|afternoon|evening|weekend|week)\b"
    r"|\b(?:most of the|the whole|the entire)\s+(?:day|morning|afternoon|evening|weekend|week)\b"
    r"|\bfor (?:ages|hours|days|weeks|months|years)\b"
    r"|\b(?:hours|days|weeks|months|years)\s+now\b)",
    re.I)
TAKEN_A_STRETCH = re.compile(
    r"\b(?:this|that|it)(?:'s|s|\u2019s|\s+has|\s+had)\s+taken\s+(?:me|us)\s+"
    r"(?P<when>\ball (?:day|night|morning|afternoon|evening|weekend|week)\b"
    r"|\b(?:most of the|the whole|the entire)\s+(?:day|morning|afternoon|evening|weekend|week)\b"
    r"|\bfor (?:ages|hours|days|weeks|months|years)\b"
    r"|\b(?:hours|days|weeks|months|years)\s+now\b)",
    re.I)
# A day given to somebody in a hospital or a home is the same kind of stretch and not a job: the
# line is mostly waiting, and the question a friend asks is how it is looking.
VISITING_STRETCH = (
    "at the hospital", "in hospital", "at hospital", "in the hospital", "at a&e", "in a&e",
    "at the a&e", "in the a&e", "at the clinic", "at the doctors", "at the doctor's",
    "at the surgery", "at the care home", "at the hospice", "at the nursing home",
    "at the vets", "at the vet")
# A line that says the job is done with is a report of something finished, and "how close is it to
# done" would be nonsense: those keep the pleasantry they are given.
STRETCH_IS_FINISHED = (
    "finished", "finished it", "done it", "all done", "got it done", "sorted it", "sorted now",
    "got there", "finally done", "managed it", "got it finished", "its done", "it's done")
# A queue is not somebody keeping you waiting for an answer: "i spent the whole morning queueing at
# the tip" was met with "and still no answer - who is left to try?", which is the question for a
# bank or a council. The queue gets the question a queue leaves open, whether it moved.
QUEUE_STRETCH = (
    "queueing", "queuing", "queued", "in a queue", "sat here", "standing here", "sat in the car",
    "waiting for the bus", "waiting for a bus", "waiting for the train", "waiting for a taxi",
    "waiting at the tip", "at the tip", "at the dump", "recycling centre")
# A day given to one of their own people is a day sitting with somebody, not a job with an end:
# "ive spent the whole day with my mum" was told "jobs like that always take longer than they
# look. What is left?"
WITH_THEIR_OWN = (
    "with my mum", "with my mom", "with my mother", "with my dad", "with my father",
    "with my nan", "with my gran", "with my grandma", "with my grandad", "with my granny",
    "with my son", "with my daughter", "with my kids", "with my child", "with my husband",
    "with my wife", "with my partner", "with my sister", "with my brother", "with my friend",
    "with my mate", "at my mum's", "at my mom's", "at my dad's", "at my nan's")
WAITING_AFTER_THE_STRETCH = (
    "waiting", "waited", "on hold", "in a queue", "queueing", "queuing", "on the phone")
# Waiting *for a person to stop dying* is not waiting on a service, and the whole frame of the
# waiting pools - "has anyone given you an answer yet", "that is a long time to be kept hanging
# about" - is wrong words at a deathbed. `ive been waiting for my mum to die for three days` was
# answered "For three days waiting on them. That is a long time to be kept hanging about." by
# @brave-seal's read, and `ive been waiting by her bedside since friday` was told "Has anyone
# given you an answer yet?". Main's neutral "I'm listening - say more if it helps." is the better
# answer there, so the reading stands down and leaves the turn as it was. The thing waited for is
# the other person's own to do or to suffer - dying, waking, coming round, making it through - or
# the line puts the speaker beside a bed.
VIGIL = re.compile(
    r"\bwait(?:ing|ed)?\s+(?:for|on|by|at|with)\b[^.]{0,24}?\b(?:die|dying|death|pass|"
    r"passing|go|wake|wake up|come round|come back|pull through|make it|breathe|survive)\b"
    r"|\b(?:by|at|beside)\s+(?:his|her|their|my (?:mum|mom|dad|nan|gran|son|daughter|wife|"
    r"husband|partner|sister|brother|friend)'?s?)\s+(?:bed|bedside)\b"
    r"|\b(?:his|her|their)\s+bedside\b")
# A journey or a repair that ate the day is not a job being got through, and "how close is it to
# done" would be a nonsense answer to it.
NOT_A_SPENT_JOB = (
    "to get here", "to get there", "to drive", "to come", "to travel", "to walk", "the bus",
    "the train", "the traffic", "at work", "at the office", "in work", "at school", "at college",
    "at uni", "on a course")
# Who the stretch is about. The phrases come first because the word on its own is a different
# thing: "cleaning" is a job, "cleaning up after" is care, and "chasing" is waiting on somebody
# rather than a job of their own.
WAITING_STRETCH = (
    "waiting", "waited", "chasing", "chased", "chase", "ringing", "phoning", "phoned",
    "calling", "emailing", "emailed", "messaging", "queuing", "queueing", "queued",
    "hounding", "pestering", "chasing it", "on hold", "on the phone", "in a queue",
    "on a waiting list", "on a waiting list", "back and forth", "trying to get through",
    "trying to speak", "trying to cancel", "hunting", "searching", "applying",
    "job hunting")
# "up with" was a bare entry here, and "ive been putting up with it for months" was read as
# looking after somebody: "that is a lot of looking after someone, on your own". Tolerating a
# thing is not caring for a person, so "up with" only counts when a person follows it.
CARING_STRETCH = (
    "looking after", "caring for", "sitting with", "nursing", "minding",
    "cleaning up after", "running after", "running round after", "feeding", "settling",
    "carrying")
UP_WITH_A_PERSON = re.compile(
    r"\bup with\s+(?:my|her|his|their|our|the|a)\s+\w+|\bup with\s+(?:him|her|them|"
    r"mum|dad|nan|gran|the kids|someone)\b", re.I)
EFFORT_STRETCH = (
    "painting", "decorating", "wallpapering", "tiling", "plastering", "sanding",
    "stripping", "cleaning", "tidying", "sorting", "clearing",
    "hoovering", "vacuuming", "scrubbing", "washing", "ironing",
    "dusting", "unloading", "loading", "packing", "unpacking", "moving", "digging",
    "weeding", "mowing", "pruning", "building", "fixing", "mending", "repairing",
    "renovating", "assembling", "filing", "shredding", "decluttering", "boxing",
    "shifting", "polishing", "hanging", "hammering")
# A state of the body or the mood is not a job being got through: those lines are answered by the
# mood, health and trouble readers, and "all morning" in them is how long it has been going on
# rather than how far along it is.
NOT_A_STRETCH_JOB = (
    "feeling", "felt", "low", "flat", "tired", "exhausted", "knackered", "shattered",
    "sleeping", "slept", "waking", "hurting", "aching", "sore", "sick", "puking",
    "vomiting", "throwing up", "bleeding", "coughing", "sneezing", "crying", "shaking",
    "dizzy", "worried", "anxious", "stressing", "stressed", "panicking", "missing",
    "thinking", "going over", "dreaming", "eating", "drinking", "smoking", "scratching",
    "itching", "out of breath", "breathless", "sweating", "on my feet", "in bed",
    # "ive been off work with it since march" is not a job being got through, and "what is left
    # of it?" asks about a thing the line never named. The bare "sick" above did not catch it.
    "off work", "off sick", "off ill", "signed off", "on the sick")
WAITING_STRETCH_SAID_BACK = (
    "{When} - that is a long time to be kept waiting. Has anyone given you an answer yet?",
    "{When} and still no answer - who is left to try?",
    "{When} chasing the same thing. Has it moved at all?",
    "{When} and it is all waiting on other people. Is there a name you can ask for?",
)
EFFORT_STRETCH_SAID_BACK = (
    "{When} - that is a lot of it on one job. How close is it to done?",
    "{When} and still at it - what is left of it?",
    "{When} - jobs like that always take longer than they look. What is left?",
    "{When} at the same thing - is the end in sight?",
)
CARING_STRETCH_SAID_BACK = (
    "{When} - that is a lot of looking after someone, on your own. Does anyone give you a break?",
    "{When} being needed and nothing else. Who is looking after you in it?",
    "{When} of somebody else's week taking yours. Have you got any help with it?",
)
QUEUE_STRETCH_SAID_BACK = (
    "{When} in a queue - did it move at all?",
    "{When} of it and no sign of it moving. Is there another way round it, or is this the only one?",
    # The doing is theirs to name: "ive been sat here for two hours" was told "For two hours
    # queuing with nothing to show for it", and they never said queuing (@brave-seal).
    "{When} of it with nothing to show for it. How much more of it is there?",
)
# A day at a hospital is said by the person in the bed as often as by the person sitting beside it,
# and nothing in "ive been at the hospital all day" says which. The pool with somebody in it put
# the *speaker* in the visitor's chair - "All day sitting with somebody... is anyone spelling you?"
# to somebody who had just had their appendix out - so the lines that only work one way are kept
# apart, and given only to a line that names the person they went with or went to see.
VISITING_STRETCH_SAID_BACK = (
    "{When} in that place - those are mostly waiting about, whichever end of it you are on. "
    "How is it looking?",
    "{When}, and it is all waiting. How are things there?",
    "{When} of it. Nobody plans a day like that - how is it going?",
)
VISITING_SOMEBODY_SAID_BACK = (
    "{When} sitting with somebody. That is a long day for you as well - is anyone spelling you?",
    "{When} and no let up - how are they doing, and how are you doing with it?",
    "{When} of it. Is there anyone sitting with them so you can get a break?",
)
# The words that put somebody else in the bed: the person they went with, or went to see.
SOMEBODY_ELSE_IN_IT = (
    "with my mum", "with my mom", "with my mother", "with my dad", "with my father",
    "with my nan", "with my gran", "with my grandma", "with my grandad", "with my granny",
    "with my son", "with my daughter", "with my kids", "with my child", "with my husband",
    "with my wife", "with my partner", "with my sister", "with my brother", "with my friend",
    "with my mate", "to see my mum", "to see my mom", "to see my dad", "to see my nan",
    "to see my gran", "to see my son", "to see my daughter", "to see my wife",
    "to see my husband", "to see my partner", "to see my sister", "to see my brother",
    "to see my friend", "visiting my", "at my mum's", "at my mom's", "at my dad's",
    "at my nan's", "my mum is in", "my dad is in", "my nan is in", "my son is in",
    "my daughter is in", "my wife is in", "my husband is in", "my sister is in",
    "my brother is in", "my friend is in", "hes in hospital", "shes in hospital",
    "theyre in hospital", "with him", "with her", "with them")
# The other way round: a stretch of waiting on somebody of their own, which is not a company with
# a queue and a name to ask for. "ive been waiting for my sister to call all day" was asked "is
# there a name you can ask for?", and there is no asking for a name when it is your sister.
WAITING_ON_THEIR_OWN = (
    "my mum", "my mom", "my dad", "my nan", "my gran", "my son", "my daughter", "my kids",
    "my husband", "my wife", "my partner", "my sister", "my brother", "my friend", "my mate",
    "my lad", "my girl", "the kids")
# "for her to call", "waiting on them to decide": the pronoun is a person only when it is doing
# something, and "chasing them for weeks" is a company with a complaint, not a relative.
WAITING_FOR_A_PERSON = re.compile(r"\b(?:for|on)\s+(?:him|her|them)\s+(?:to|about)\b", re.I)
WAITING_ON_THEIR_OWN_SAID_BACK = (
    "{When} waiting on somebody of your own. Have they been in touch at all?",
    "{When} of it, and no word. Is this how they usually are?",
    "{When} waiting on them. That is a long time to be kept hanging about.",
)
# Waiting to *talk* to somebody is loneliness, not a queue: "ive been waiting all day to talk to
# someone" was told "who is left to try?", which turns a person who wants a conversation into a
# person with a complaint about a company. The readers that answer the lonely line keep it.
WAITING_TO_TALK = (
    "to talk to someone", "to talk to somebody", "to talk to anyone", "for someone to talk to",
    "for somebody to talk to", "to have someone to talk to", "to have somebody to talk to",
    "to speak to someone", "to speak to somebody", "someone to talk to", "somebody to talk to")
# ... unless the person is at a company, which is the queue again: "ive been waiting all day to
# talk to someone at the council" is a wait for an answer, not a lonely day.
TALKING_TO_A_PLACE = re.compile(
    r"\b(?:talk to|speak to|get through to|get hold of)\s+(?:someone|somebody|a person)\s+"
    r"(?:at|from|in)\b", re.I)
# The line is a stretch of the day as well, so the stock line is not the answer either: the person
# has said how long they have been on their own with it, which is the thing to answer.
TALKING_STRETCH_SAID_BACK = (
    "{When} with nobody to talk to. That is a long stretch to carry on your own - what have you "
    "been doing with it?",
    "{When} of it, and no company. What is the day like where you are?",
    "{When} waiting for someone to talk to - well, you have my attention now. What is on your "
    "mind?",
)
# The words that take a capital inside the stretch: "since march" and "since monday" read as a
# typo otherwise, and the month is the one part of the phrase the reply leans on.
STRETCH_STARTS_UPPER = frozenset((
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "christmas", "easter"))


def _the_stretch_said_back(phrase):
    """The person's own stretch, written the way the reply says it back."""
    words = [w for w in " ".join(phrase.split()).strip(" .,!?;:").split() if w]
    if words[:1] in (["for"], ["since"], ["all"], ["most"], ["the"]) and len(words) > 1:
        lead, rest = words[0], words[1:]
        words = [lead] + [w.capitalize() if w.lower() in STRETCH_STARTS_UPPER else w
                          for w in rest]
    if not words:
        return ""
    said = " ".join(words)
    return said[:1].upper() + said[1:]


def _names_one_of(doing, phrases):
    """Whether the doing holds one of the phrases, as whole words."""
    words = doing.split()
    return any((" " in phrase and phrase in doing) or phrase in words for phrase in phrases)


def _the_shape(doing, said, after):
    """Which pool this stretch belongs in, or None when it is not one of them.

    The doing decides first, because a job is the most specific thing in the line; the words after
    the stretch come next, which is where "ive been sat here for two hours waiting" keeps its
    wait; and a doing that only points at the job ("at this", "on it") is a job of their own.
    """
    if _names_one_of(doing, NOT_A_STRETCH_JOB):
        return None
    if _names_one_of(doing, CARING_STRETCH) or UP_WITH_A_PERSON.search(said):
        return "caring"
    if _names_one_of(doing, QUEUE_STRETCH) or _names_one_of(said, QUEUE_STRETCH):
        return "queueing"
    if _names_one_of(doing, WAITING_STRETCH):
        if _names_one_of(said, WAITING_TO_TALK) and not TALKING_TO_A_PLACE.search(said):
            # The wait is for company, not for an answer, and "who is left to try" answers the
            # wrong one of those.
            return "talking"
        if (_names_one_of(doing, WAITING_ON_THEIR_OWN) or _names_one_of(after, WAITING_ON_THEIR_OWN)
                or WAITING_FOR_A_PERSON.search(said)):
            return "waiting_on_their_own"
        return "waiting"
    if _names_one_of(said, VISITING_STRETCH) or _names_one_of(said, WITH_THEIR_OWN):
        return "visiting"
    if _names_one_of(doing, EFFORT_STRETCH):
        return "effort"
    if doing and _names_one_of(doing, POINTER_STRETCH):
        return "effort"
    if _names_one_of(after, WAITING_AFTER_THE_STRETCH) or \
            _names_one_of(said, WAITING_AFTER_THE_STRETCH):
        return "queueing" if _names_one_of(said, QUEUE_STRETCH) else "waiting"
    return None


def reads_as_a_long_stretch(clean):
    """(shape, the stretch to say back) for a stretch the person is still inside, or None.

    shape is "waiting", "effort", "caring" or "visiting". Only a first-person line with a"
    stretch of time in it counts - "i've been <doing> since nine", "ive spent all day on this
    form", "this has taken me all afternoon" - and only where the doing is one of those kinds:
    anything else has its own reader above, and a state of the body or the mood is somebody
    else's question.
    """
    said = " ".join((clean or "").lower().split())
    if not said or "?" in said:
        return None
    for pattern, spent in ((BEEN_ON_A_STRETCH, False), (SPENT_ON_A_STRETCH, True)):
        for met in pattern.finditer(said):
            doing = (met.group("doing") or "").strip(" ,.;:")
            if len(doing.split()) > 8 or " and " in doing:
                continue
            when = _the_stretch_said_back(met.group("when"))
            if not when:
                continue
            if _names_one_of(said, NOT_A_STRETCH_JOB) or VIGIL.search(said):
                continue
            if _names_one_of(said, STRETCH_IS_FINISHED):
                continue
            if spent and _names_one_of(said, NOT_A_SPENT_JOB):
                continue
            shape = _the_shape(doing, said, said[met.end():])
            # "ive spent all day on this form" names no kind of work at all, and it is still a day
            # gone on one job, so it takes the pool every other job takes.
            if shape or spent:
                return (shape or "effort", when)
    for met in TAKEN_A_STRETCH.finditer(said):
        when = _the_stretch_said_back(met.group("when"))
        if not when:
            continue
        if _names_one_of(said, NOT_A_STRETCH_JOB) or _names_one_of(said, NOT_A_SPENT_JOB):
            continue
        if _names_one_of(said, STRETCH_IS_FINISHED):
            continue
        return ("effort", when)
    return None


def the_stretch_pool(shape, when, said=""):
    """The three lines for this kind of stretch, with the person's own time in them.

    Two of the shapes are split by who the line is about rather than by what was being done: a day
    at a hospital with somebody is not a day in the bed, and a wait for your sister to ring is not
    a wait for a bank. `said` is the person's own line, and it decides which half.
    """
    if shape == "visiting":
        shape = ("visiting_somebody" if _names_one_of(said, SOMEBODY_ELSE_IN_IT)
                 else "visiting")
    pool = {"waiting": WAITING_STRETCH_SAID_BACK, "effort": EFFORT_STRETCH_SAID_BACK,
            "caring": CARING_STRETCH_SAID_BACK, "queueing": QUEUE_STRETCH_SAID_BACK,
            "visiting": VISITING_STRETCH_SAID_BACK,
            "visiting_somebody": VISITING_SOMEBODY_SAID_BACK,
            "waiting_on_their_own": WAITING_ON_THEIR_OWN_SAID_BACK,
            "talking": TALKING_STRETCH_SAID_BACK}.get(shape, ())
    return tuple(line.replace("{When}", when) for line in pool)


def _only_a_placeholder(text, said):
    """True when the reply tells the person nothing of its own about the line.

    Three ways a reply says nothing back: the composer's three stock lines, which fit any message;
    a search hedge or the shrug; and a receipt -- the person's own line handed back with a frame
    around it ("Noted: ...", "Got it - you've been painting the fence all morning, how long have
    you been at it?"), which asks what the line has already said. The last of those is read by
    the words the two share, so a frame this module has never seen counts as well.
    """
    said = " ".join(str(said or "").split())
    if not said:
        return True
    if said in fallback.NEUTRAL or fallback._is_a_hedge(said) or ack.reads_as_a_receipt(said):
        return True
    # "a small day, said flat" is the pool for everything a person mentions about a day that has
    # already happened ("a takeaway, a haircut, work being alright"), and it is what "ive spent all
    # day on this form" was met with: "Nice one. How did the rest of it go?" fits any message, and
    # it reads the stretch as over when the line is still inside it.
    if said in fallback_data.A_SMALL_DAY or said in fallback_data.A_DAY_ASKED_PLAIN:
        return True
    # The same pool in the other tense: "How did that go, overall?" is asked of a day that is
    # over, and it is what "ive been sat here for two hours" was met with.
    mine = set(re.findall(r"[a-z']+", str(text or "").lower()))
    theirs = set(re.findall(r"[a-z']+", said.lower()))
    if len(mine) < 2:
        return False
    shared = mine & theirs
    return len(shared) >= 3 and len(shared) / len(mine) >= 0.6


def the_stretch_said_back(text, memory, said):
    """The reply for a stretch the person is still inside, or "" when this is not that line.

    Only a placeholder is replaced: a line the composer answered with something of its own, or
    that another reader here has already picked up, keeps its reply. The stretch is said back in
    the person's own time and then one question is asked of it.
    """
    if not _only_a_placeholder(text, said):
        return ""
    stretch = reads_as_a_long_stretch(text)
    if not stretch:
        return ""
    clean = " ".join(str(text or "").lower().split())
    return fallback._choose(the_stretch_pool(stretch[0], stretch[1], clean),
                            memory, clean) or ""
