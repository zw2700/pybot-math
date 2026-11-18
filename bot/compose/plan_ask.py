"""A plan asked for when the thread already holds one.

The reader and its patterns live here rather than in `fallback.py` so that the file every lane
adds an ending to keeps one line of it, and the walk back over the thread is somewhere a reader
can find it.
"""
import re


PLAN_ASK = re.compile(
    r"(?:whats? (?:the |our )?plan|what is the plan|"
    r"the plan for (?:the|our|this) (?:day|trip|weekend|evening|visit)|"
    r"what (?:should|shall|do) we do (?:first|next|then)|"
    r"where (?:do|should) we start|whats? the order|"
    r"how (?:should|do|shall) we plan|plan (?:out )?the (?:day|trip|weekend)|"
    r"sort (?:out )?the plan)"
    # "so whats the plan for her" is a plate for one guest, not the plan of a day, and the order
    # of a day said back over it is nonsense. So the plan ask has to be the end of the line, or
    # carry a day or a time after it - not a person.
    r"(?=\s*(?:$|[.?!]|(?:then|now|today|tonight|tomorrow|weekend)\b"
    r"|for (?:the|this|our|next|\w+day)\b|on \w+day\b))")

# The parts of a day out: somewhere to be, and the two things that have to be booked round it.
# A move, a party or a job is a plan too, and neither "eat first" nor "stay over" is the order of
# its day, so the reader stands down for all of them.
PLAN_PLACE = re.compile(
    r"\b(?:gig|gigs|venue|concert|show|match|game|festival|tour|theatre|cinema|museum|"
    r"exhibition|station|train|flight|airport|coach|trip|day out|weekend away|night out)\b")
PLAN_MEAL = re.compile(r"\b(?:eat|eats|eating|food|meal|dinner|lunch|breakfast|restaurant|"
                       r"table|bite|pub|pizza|curry)\b")
PLAN_BED = re.compile(r"\b(?:stay over|stay the night|staying over|hotel|hotels|bed|room|"
                      r"sleep|sleeping|airbnb|hostel)\b")
# Said when the booking is already in: "weve booked a table for four" is a plan whose table is
# done, and telling that person to book one is the wrong step said confidently.
PLAN_BOOKED = re.compile(r"\b(?:booked|reserved|sorted|got a table|have a table|already got)\b")
PLAN_TOGETHER = re.compile(r"\b(?:\d+|two|three|four|five|six|seven|eight|several|few|both) "
                           r"of (?:us|them|you)\b")
PLAN_DOORS = re.compile(
    r"\b(?:gig|gigs|venue|concert|show|match|game|festival|tour|theatre|cinema|museum|"
    r"exhibition)\b")

# A line that asks, rather than one that says how the thing will be. The settled shape of a plan
# is in the statements - "three of us", "cheap and cheerful is fine" - so a question mark or a
# question word at the front disqualifies a line as one of them.
PLAN_QUESTION = re.compile(
    r"^(?:so |ok |okay |and |but |then )*(?:what|why|how|when|where|who|which)\b"
    # "were going to a gig" is a plan being described and "were you going" is a question, so the
    # auxiliaries only count as a question word when the subject follows them.
    r"|^(?:so |ok |okay |and |but |then )*(?:can|could|should|shall|do|does|did|is|are|was|were|"
    r"will|would|have|has|am|any)\s+(?:i|you|we|they|he|she|it|there|this|that|one)\b")

# Said and nothing more. Not part of a plan, and said back they read as the bot repeating a hello.
PLAN_EMPTY = frozenset("""
hi hello hey ok okay cool nice great thanks thank you yes yeah no nope sure right ah oh hmm
lol haha good fine maybe alright
""".split())


def _a_statement(line):
    """The line, if it says how the thing will be, with nothing of the plan machinery in it."""
    said = " ".join(str(line or "").lower().split())
    said = said.strip(" .!,")
    if not said or "?" in said or PLAN_QUESTION.match(said):
        return ""
    words = said.split()
    if len(words) < 2 or len(words) > 14 or set(words) <= PLAN_EMPTY:
        return ""
    return said


def _the_plan_the_thread_holds(memory, ask=""):
    """The thing the plan is for, and up to three things the person has settled about it.

    A plan asked for as a line on its own - "so whats the plan for the day then" - cannot be
    answered out of a file: the plan is made of what this person has already said, four turns of
    it, and every part of it is in the thread. What a friend does is put the order round it (the
    hour that cannot move, the meal, the bed) and say back what has been settled, so the person
    can see the plan is nearly all decided and only the times are left. So this reads the thread
    rather than the line: the first thing said is what the plan is for, and the last three
    statements are the constraints it has to fit.

    It also has to be a day out: a gig, a venue, a train, a hotel. A move or a party is a plan
    with a different order, and the day-out order said over one of those is a confident wrong
    answer, so one of the day-out parts has to be named before this reads anything.
    """
    turns = [t for t in (memory.get("turns") or []) if isinstance(t, dict)]
    # The ask itself is skipped by its own words rather than by its position: whether the turn
    # running now is already in the transcript depends on who is asking, and the last statement
    # before it is part of the plan - "were coming back the same day" is why there is no bed.
    ask = " ".join(str(ask or "").lower().split())
    said = [_a_statement(t.get("user")) for t in turns
            if " ".join(str(t.get("user") or "").lower().split()) != ask]
    said = [one for one in said if one]
    if len(turns) < 3:
        return None, []
    if len(said) < 2:
        return None, []
    thread = " ".join(said)
    # Two of the parts of a day out have to be named before the order of a day out is said over
    # it: somewhere to be, something to eat, somewhere to sleep, somebody to go with. One on its
    # own is a sentence about anything - "we need a van" is a move - and the order read over it
    # is a confident wrong answer.
    parts = sum(bool(one.search(thread)) for one in (PLAN_PLACE, PLAN_MEAL, PLAN_BED,
                                                     PLAN_TOGETHER))
    # Somewhere to be, or somewhere to sleep: a meal cooked at home and a count of the people
    # is a Sunday roast, and "the hour that cannot move, then the meal" is not the shape of one.
    if parts < 2 or not (PLAN_PLACE.search(thread) or PLAN_BED.search(thread)):
        return None, []
    thing = said[0]
    meal, bed = bool(PLAN_MEAL.search(thread)), bool(PLAN_BED.search(thread))
    booked = bool(PLAN_BOOKED.search(thread))
    settled = []
    for one in reversed(said[1:]):
        if one in settled:
            continue
        settled.append(one)
        if len(settled) == 2:
            break
    settled.reverse()
    # The order is only as long as the day is: a train back the same evening is no bed, and
    # "book the room tonight" is a wrong step for it.
    order = "the hour that cannot move"
    if meal:
        order += ", then the meal"
    if bed:
        order += ", then the bed"
    book = ("the table and the room" if meal and bed
            else "the table" if meal else "the room" if bed else "the two bookings")
    return thing, settled, order, book, booked


def _quoted_back(settled):
    """The lines said back in the person's own words, joined the way a person says a list."""
    quoted = ['"%s"' % one for one in settled]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return "%s and %s" % (quoted[0], quoted[1])
    return "%s and %s" % (", ".join(quoted[:-1]), quoted[-1])


def plan_ask_pool(clean, memory=None):
    """The pool for "what's the plan" when the thread already holds one, else None.

    Every part of a day out is in the thread - three of them, eating first, staying over, cheap
    and cheerful - and the line that asks for the plan of it was answered "That's beyond what I
    know well, sorry. Searching for it will turn up better sources": the one thing nobody can
    look up is their own day. The order is not knowledge, it is how a day works, and the
    constraints are the person's own words, so the bot can lay both out and hand back the single
    thing it cannot know: the hour the doors open.
    """
    said = " ".join(str(clean or "").lower().split())
    if not PLAN_ASK.search(said):
        return None
    _plan = _the_plan_the_thread_holds(memory if isinstance(memory, dict) else {}, said)
    if not _plan[1]:
        return None
    thing, settled, order, book, booked = _plan
    named = _quoted_back([thing] + list(settled))
    said_back = named
    # A venue has doors and a page that says when they open; a train or a table has an hour to be
    # there for. The one thing the bot cannot know is that hour, so it names where it is written.
    left = ("the doors time - the venue's own page has that"
            if PLAN_DOORS.search(" ".join(settled) + " " + thing)
            else "the hour you have to be there - the booking page has that")
    if booked:
        tail = "The one thing that runs out is done already, so the hours are all that is left."
        close = "Fix the hours round it and the day runs itself."
    else:
        tail = "Book %s tonight: the rest is only times." % book
        close = "Get %s settled and the day runs itself." % book
    return (
        "You have told me %s, so the order is %s. %s" % (said_back, order, tail),
        "I have it all: %s. The order is %s, and the one thing left to find is %s."
        % (said_back, order, left),
        "Nothing here needs looking up - you have told me %s, and that is a day out with the"
        " order already in it: %s. %s" % (said_back, order, close),
    )
