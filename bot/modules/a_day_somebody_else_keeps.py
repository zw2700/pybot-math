"""A day that belongs to a school or a club is named for whoever keeps it, not searched for.

"What time does my son finish school" and "what time does my class start" reached the composer's
hedge - "I don't know enough to answer that honestly. A search should sort you out quickly", or
"That's beyond what I know well, sorry" - which names neither whose timetable it is nor where the
times live. Nobody can search that answer out of the air either: the finish time is set by the
school, the club or the class, and the one place that has it is their office, their app, the
newsletter or the letter.

Each line leads with the part that is knowable - a school day holds steady through a term, and it
is the last day of term, an inset day or a trip that moves it; a class moves more often, because a
session can be cancelled or a tutor changed - then names who has the rest, then offers the part
that can still be done here: the arithmetic on the journey or the rest of the day. No time is ever
given, because none is known.

The fences are the entries that already answer. Their own shift keeps the rota line ("what time do
i finish work"), a bus or a train keeps the operator's ("what time does my bus leave"), a surgery
keeps the record line ("what time does my appointment start"), and an exam or a results day is the
health record's, not a timetable's. A child's ordinary evening ("my son wont eat vegetables") is
not a timetable at all, and the ask pattern needs a start or finish verb to match at all.

This sits above the greeting band (PRIORITY -1000) and below every knowledge module, so it only
ever answers a line no entry reached: a term-dates card, a starting-school card or an answers card
keeps its turn.
"""
import random
import re

from ..memory import last_bot

PRIORITY = -999

# The ask: a start or a finish, of a day that belongs to somebody in their care or to a class of
# their own. Both halves are needed - "my son wont eat vegetables" has the person but no time.
MY_CARE_ASK = re.compile(
    r"(?<![a-z])(?:what time|when|which time|what hours)\b[^?]{0,40}?\b(?:my|our)\s+"
    r"(?:son|daughter|kid|kids|child|children|boy|girl|little one|baby|niece|nephew|"
    r"grandson|granddaughter|grandchild|grandchildren|childminder|babysitter|"
    r"class|classes|lesson|lessons|course|club|swimming|training|nursery|school)\b"
    r"[^?]{0,30}?\b(?:finish|finishes|start|starts|get out|gets out|break up|breaks up|"
    r"come out|comes out|be done|is done|end|ends|go in|goes in|be picked up|gets picked up|"
    r"get home|gets home|be home|is home|get there|gets there)\b", re.I)
# A travel word puts the ask back in the live pool, where the operator's app is the answer: a bus
# or a train somebody in their care is on is still a timetable that can be read for today. A
# surgery, a dentist or a prescription is the health record's, and its own line names the desk; an
# exam or a results day is neither a school day nor a class.
MY_CARE_NOT = re.compile(
    r"\b(?:bus|buses|train|trains|tram|tube|flight|flights|coach|ferry|traffic|motorway|"
    r"road|roads|strike|delayed|cancelled|appointment|appointments|doctor|dentist|hospital|"
    r"physio|clinic|surgery|nurse|pharmacy|chemist|tablets?|medicine|medication|exam|"
    r"test results?|results?)\b", re.I)
# Their own class, lesson or club: kept by whoever runs it, and it moves week to week.
THEIR_CLASS = re.compile(
    r"\b(?:class|classes|lesson|lessons|course|club|swimming|training)\b", re.I)
A_CHILD = re.compile(
    r"\b(?:son|daughter|kid|kids|child|children|boy|girl|little one|baby|niece|nephew|"
    r"grandson|granddaughter|grandchild|grandchildren|childminder|babysitter)\b", re.I)

# A child's school day or a nursery, a club or a childminder: what is known about such a day, who
# has this term's version, and what can be done once the times are in hand.
SCHOOL_LINES = (
    "A school day is usually the same length every day of the week, so the finish time they gave "
    "you in September still holds unless it is the last day of term, an inset day or a trip. The "
    "school office, its app or the newsletter has this term's version; give me the times and how "
    "long the journey takes and I'll work out when you need to set off.",
    "The times are set by the school or club, not by anything I can look up, but they rarely move "
    "inside a term - it is the last day of term, inset days and trips that shift them. Their "
    "office will tell you in one call and the app you sign them in on has the same; hand me the "
    "times once you have them and I'll plan the pick-up around the rest of your day.",
    "Those hours belong to the school or club, so I can't know this week's, but a school day holds "
    "steady through a term apart from the last day of it and any inset day - and those are on the "
    "school's own calendar. Tell me the finish time and the trip and the rest is arithmetic I can "
    "do with you.",
)
# Their own class or lesson, kept by whoever runs it: a new tutor, a cancelled session or a room
# change moves it, so the timetable you were given is the starting point and the provider's own
# message is the correction. Same shape: what is known, where the rest is, what can be done.
CLASS_LINES = (
    "A class time is set by whoever runs the course and it can move week to week - a new tutor, a "
    "session off, a room change - so the timetable you were given is the starting point rather "
    "than the answer. The provider's app, email or the notice on the door carries this week's; "
    "tell me the times and what you're fitting around them and I'll plan it with you.",
    "I can't see your timetable from here. What I can say is that classes move more often than "
    "people expect - a session cancelled, a tutor changed - and it is the provider's own message "
    "that carries the change. Bring me the times and I'll do the planning around them.",
    "The provider keeps that timetable, not me, and it changes: a bank holiday, a cancelled "
    "session, a new room. Their app or the email they send is where this week's version sits; "
    "give me the times and I'll work out the rest of your day around them.",
)


def _clean(text):
    return " ".join(str(text or "").lower().split())


def _choose(pool, memory, said=""):
    """A line from the pool, never the same one twice running, and the same one every run.

    `random.choice` here was unseeded, so the same line at the same turn of the same conversation
    gave a different sentence in two runs of the bot. Every comparison the swarm makes is a diff of
    two runs, so that read as a change no commit had made: the seed is the turn count and the line
    itself, which is what `bot/compose/pick` does for every other pool.
    """
    last = str(last_bot(memory) or "").strip()
    fresh = [line for line in pool if line != last]
    options = fresh or list(pool)
    turns = [turn for turn in (memory.get("turns") or []) if isinstance(turn, dict)]
    seed = len(turns) * 7919 + sum(ord(c) for c in str(said or "").lower())
    return random.Random(seed).choice(options)


def respond(text, memory):
    said = _clean(text)
    if not said:
        return None
    if MY_CARE_NOT.search(said):
        return None
    if not MY_CARE_ASK.search(said):
        return None
    pool = CLASS_LINES if THEIR_CLASS.search(said) and not A_CHILD.search(said) else SCHOOL_LINES
    return _choose(pool, memory, said)
