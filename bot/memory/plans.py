"""A plan announced is the question the plan implies.

People do not ask for help with a plan, they announce it:

    im planning a trip           -> Noted: you're planning a trip.
    im getting married in june   -> Noted: you're getting married in june.
    im moving house next month   -> Noted: you're moving house next month.
    i start a new job on monday  -> Noted: you start a new job on monday.

Filing it is right - the follow-up turns need the plan remembered - but it is not an answer, and
the knowledge base already holds the answer to the question the announcement implies:

    how do i plan a trip             -> Two months out: check the passport has six months left...
    how do i plan a wedding          -> Guest list first, because it sets the cost of everything...
    what do i need to do to move house -> Do the paper trail in one afternoon: tell the council...
    first day at a new job           -> Dress one step smarter than the job's everyday clothes...

So the announcement is read as that question, and answered from the entry it reaches. Two rules
keep it honest: the line must be the person's own plan, said as a statement (not a question, not a
plan they are arguing with, not somebody else's), and the rewrite must reach an entry - a plan the
knowledge base has no answer for is left to the reply that files it, exactly as before.
"""
import re

from ..compose import pick
from ..knowledge import lookup
from ..understanding import understand
from .when import CALENDAR_NOW

# The person's own plan, said in the first person: "im planning a trip", "we are organising a
# party". A lead-in ("so", "ok", "and") is allowed in front, nothing else: "my sister is planning a
# trip" and "hes moving house" are not their plan.
_SELF = r"^(?:(?:so|ok|okay|and|also|well|right|hmm)[, ]+)*"
# Who is planning: the person alone ("im", "i am", "we're") or with someone they name ("me and
# sarah are getting married"), which is still their own plan. "my sister is planning" is not.
_WHO = (r"(?:i'm|im|i am|we're|we are|"
        r"(?:me|i) and [a-z]+ (?:are|'re)|[a-z]+ and i (?:are|'re))")
_PLANNING = re.compile(_SELF + _WHO + r"\s+"
                       r"(?:planning|sorting out|organising|organizing|arranging)\b"
                       r"(?:\s+(?:a|an|the|my|our|some))?\s+(?P<thing>[a-z][a-z ']{2,40})", re.I)
_MOVING = re.compile(_SELF + _WHO + r"\s+moving\s+"
                     r"(?:house|home|flat|out|in\b|to\s+[a-z]+|next|soon|this|in\s)", re.I)
_MARRYING = re.compile(_SELF + _WHO + r"\s+getting married\b", re.I)
# "i start a new job on monday" is a job; "i start work at 9" is a shift and "we start work on
# the kitchen" is a job on the house, so "work" has to stand alone to be a first day.
_NEW_JOB = re.compile(_SELF + r"(?:i'm|im|i am|i|we're|we are|we)?\s*"
                      r"(?:start|starts|starting|begin|beginning)\s+"
                      r"(?:a |my |our )?(?:new )?(?P<what>job|work)\b(?P<after>.*)", re.I)


# What may follow "work" and still be a first day at a job: a date or a day, never a clock time
# ("i start work at 9" is a shift), a place ("in a hospital", "on the kitchen") or a subject.
_WORK_WHEN = re.compile(r"^\s*(?:(?:on|by)\s+(?:the\s+)?(?:\d+|first|last|" + "|".join([
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "mon", "tues", "tue", "weds", "wed", "thurs", "thu", "thur", "fri", "sat", "sun"]) +
    r")(?:st|nd|rd|th)?|next\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday)|tomorrow|today|this\s+(?:week|month|monday|tuesday|wednesday|"
    r"thursday|friday|saturday|sunday))\b", re.I)


def _a_first_day(text):
    """True when the line is a first day at a new job, not a shift or a job on the house."""
    found = _NEW_JOB.search(text or "")
    if not found:
        return False
    if found.group("what").lower() == "job":
        return True
    after = re.sub(r"[\s.,!?;:'\"()]", "", found.group("after") or "")
    if not after:
        return True
    return bool(_WORK_WHEN.match(found.group("after") or ""))

# The question the plan implies, in the words the knowledge base has an entry for. Each test
# answers True only when the line really is that plan.
_ASK_FOR = (
    (_MARRYING.search, "how do i plan a wedding"),
    (_MOVING.search, "what do i need to do to move house"),
    (_a_first_day, "first day at a new job"),
)

# A question is already a question: "how do i plan a trip", "what should i pack for japan". Left
# alone, the knowledge base answers it on its own.
_ASKING = re.compile(r"\?|\b(?:what|how|when|where|which|who|why|should|shall|can|could|would|"
                     r"do i need|do we need|any (?:tips|ideas|advice))\b", re.I)
# A plan they are arguing with is not a plan to help with yet: "im planning a trip but i lost my
# passport" wants the passport, not the countdown.
_TURNED = re.compile(r"\bbut\b|\bthough\b|\bexcept\b|\bonly\b|\bhowever\b", re.I)
# "im not planning a trip", "we arent moving house now": a denial is not a plan.
_DENIED = re.compile(r"\b(?:not|never|no longer|arent|isnt|wasnt|dont|doesnt)\b|n't\b", re.I)
# A journey to a grave is not a journey to Spain. "im planning a trip to my dads grave" reached
# the holiday countdown, which offered a passport check for a trip that is about a death - worse
# than the plain "Noted:" it replaced. Grief is read by whoever reads the sadness, so the plan is
# left alone and the turn goes to them (fast-shelf, #1848).
_ABOUT_A_DEATH = re.compile(
    r"\b(?:grave|graves|graveside|cemetery|ashes|funeral|funerals|burial|buried|cremation|"
    r"cremated|crematorium|memorial|hospice|dying|died|death|passed away|"
    r"say goodbye|last goodbye)\b", re.I)


def as_question(text):
    """The question a plan announcement implies, or None when the line is not one."""
    question, _ = _implied(text)
    return question


def _implied(text):
    """The question the line implies, and whether it is one of the kinds read by hand.

    A kind read by hand names its own entry ("what do i need to do to move house"), so that entry
    answers it. The general kind ("im planning a kitchen") only has "how do i plan a ...", and the
    entry that reaches can be about the thing rather than about planning it: kitchen-routine
    cleans a kitchen, and the person was talking about planning one.
    """
    clean = " ".join(str(text or "").lower().split())
    if (not clean or _ASKING.search(clean) or _TURNED.search(clean) or _DENIED.search(clean)
            or _ABOUT_A_DEATH.search(clean)):
        return None, False
    for test, ask in _ASK_FOR:
        if test(clean):
            return ask, True
    found = _PLANNING.search(clean)
    if found:
        thing = found.group("thing").strip(" .!,")
        if thing.startswith("to "):
            return None, False  # "planning to lose weight" is an intention, not a thing to plan
        # "planning a trip next month" keeps its thing; a trailing time phrase is not part of it.
        thing = re.sub(r"\s+(?:next|this|in|on|for)\s+\w+.*$", "", thing).strip()
        if thing:
            if thing.startswith(("my ", "our ", "the ")):
                return "how do i plan " + thing, False
            return "how do i plan a " + thing, False
    return None, False


def _the_reply(entry, question, memory):
    """The entry's answer said, the way the composer will say it.

    An entry's reply is a string, a list of phrasings or a function of the line and the store
    (`bot/compose`), and the last two are most of the knowledge base. Reading only the string left
    every such entry looking as if it had no answer at all, so a plan announced reached nothing
    and fell back to "Noted: ..." on any main where the entry had moved to a function.
    """
    reply = getattr(entry, "reply", None)
    if callable(reply):
        try:
            reply = reply(memory if isinstance(memory, dict) else {},
                          understand(question, memory if isinstance(memory, dict) else {}))
        except Exception:
            return ""
    elif isinstance(reply, (list, tuple)):
        reply = pick(reply, memory if isinstance(memory, dict) else {})
    return reply if isinstance(reply, str) else ""


def answer(text, memory=None):
    """The entry's answer to the question the plan implies, or None to leave the line as it was."""
    question, by_hand = _implied(text)
    if not question:
        return None
    try:
        entry = lookup.find(understand(question, memory if isinstance(memory, dict) else {}))
    except Exception:
        return None
    if entry is None:
        return None
    if not by_hand and not _about_planning(entry):
        # The entry is about the thing, not about planning it: a plan of the kitchen is not a
        # question about cleaning one.
        return None
    reply = _the_reply(entry, question, memory)
    if not isinstance(reply, str) or not reply.strip():
        return None
    # An entry written for a question sometimes leans on the question's words. Said of a plan
    # announcement, the answer has to stand on its own, so a reply that opens with a fragment is
    # left alone.
    if reply[:1].islower():
        return None
    return reply.strip()


# The words an entry uses when it is about planning the thing rather than about the thing itself.
# An entry keyed on "kitchen" and "clean" answers how to clean a kitchen; one keyed on "wedding"
# and "plan" answers how to plan a wedding. Only the second is the question a plan implies.
PLANNING_KEYS = frozenset("""
plan plans planning planned prepare preparing preparation organise organises organising
organize organized organizing arrange arranging countdown checklist need needs booking book
budget budgeting
""".split())


def _about_planning(entry):
    """Whether the entry was written for a question about planning the thing."""
    words = set()
    for part in getattr(entry, "key", ()) or ():
        for piece in (part if isinstance(part, tuple) else (part,)):
            for word in str(piece).lower().replace("'", "").split():
                words.add(word)
    return bool(words & PLANNING_KEYS)


# The answer to a plan announcement is the entry's whole paragraph, and saying the whole of it
# again one turn later is what a machine does. The follow-up asks about one part of the plan
# ("how do i pick a venue" after the wedding answer), and that part has its own sentence in the
# paragraph. Only a part the paragraph itself names is handed back: a line naming something the
# answer never mentions is left to the knowledge base, which may know that thing.
_PART_WORDS = frozenset("""
a an the and or but if so to of in on at for with about from by as is are was were be been do
does did doing done i im me my we our you your it its that this these those what which how when
where who why should could would can will shall may might must not no yes please just really
any some more most first next then now again also too very get got getting go going want need
need to know tell say said help good best way ways thing things
""".split())


# A line that asks how long is answered by the first step's heading: "Two months out" is the
# span they asked about. Cutting the paragraph at that heading hands back "A week out.", a marker
# with no verb, which is not an answer to "how long will it take". A line that asks when a step
# happens ("when should i book") names that step, so the match above answers it.
_A_LENGTH_ASK = re.compile(r"\bhow long\b|\bhow soon\b|\bhow far ahead\b|"
                           r"\bhow many (?:weeks|days|months|hours)\b|\bwhat order\b|"
                           r"\bbefore i go\b|\btimeline\b", re.I)


# A heading that measures time ("Two months out", "the day before") is a step in a countdown.
_SPAN_HEAD = re.compile(r"\b(?:" + "|".join([
    r"\d+", r"a", r"an", r"one", r"two", r"three", r"four", r"five", r"six", r"seven", r"eight",
    r"nine", r"ten", r"eleven", r"twelve"]) +
    r")\s+(?:day|week|month|year)s?\s+(?:out|before|ahead)\b"
    r"|\bthe (?:day|week|month|year) before\b", re.I)


def _the_clauses(detail):
    return [part.strip(" .;") for part in re.split(r",\s*|;\s*|\s+and\s+", detail)
            if part.strip(" .;")]


def _the_step(detail, wanted, first_only=False):
    """The clause of a sentence that names the part asked about, else the first clause."""
    if first_only:
        clauses = _the_clauses(detail)
        return clauses[0] if clauses else detail.strip(" .")
    best, best_hit = None, 0
    for clause in _the_clauses(detail):
        hit = len(wanted & _part_words(clause))
        if hit > best_hit:
            best, best_hit = clause, hit
    clauses = _the_clauses(detail)
    return best or (clauses[0] if clauses else detail.strip(" ."))


_A_CLAUSE_BREAK = re.compile(r"(?:,|;|\s-\s|:\s)")


def _the_first_step(sentence):
    """The opening step of the paragraph, said as a step rather than as the paragraph again.

    "what do i do first" after "Work out how many nights you have first, then give each place at
    least three of them: a base with day trips beats a list of cities..." wants the first thing to
    do, and the opening sentence handed back is the paragraph they have just read - word for word,
    so the arbiter takes it for a repeat and nobody answers the question. The first step of that
    sentence, in front of a word that says it is the start, is both.
    """
    text = " ".join(str(sentence or "").split()).rstrip(".")
    if not text:
        return None
    parts = [part.strip() for part in _A_CLAUSE_BREAK.split(text) if part.strip()]
    step = ""
    for part in parts:
        step = (step + ", " + part) if step else part
        if len(step.split()) >= 4:
            break
    if not step:
        return None
    if len(step.split()) >= len(text.split()):
        step = text
    return "Start with this: " + step[0].lower() + step[1:] + "."


def _a_countdown_step(head, detail, wanted, about_the_start):
    """A span heading with its step, short enough not to be the paragraph read out again.

    The heading is the answer to "when should i book" and to "how long will it take": the step
    alone is "a week out", and the whole sentence is the sentence they have just read.
    """
    step = _the_step(detail, wanted, about_the_start)
    if not step:
        return None
    said = head.strip().rstrip(":") + (":" if not about_the_start else " is when to start:")
    return said + " " + step[0].lower() + step[1:] + "."


# The words a how-long ask is made of: they name the answer, not the thing it is about, so they
# are not a subject of their own ("how long will it take" is the countdown; "how long is the
# flight" is the flight, which the paragraph never mentions).
_ASK_WORDS = frozenset("""long soon far ahead many much weeks week days day months month hours
    hour minutes minute time take takes last before order timeline go going get""".split())


def _another_thing(wanted, said_words):
    """True when the line names something the paragraph itself never mentions."""
    return any(word not in _ASK_WORDS and len(word) > 3 and word not in said_words
               for word in wanted)


# A line that asks what to do first names no part of the paragraph: it asks for the order of the
# steps, and the answer is where the paragraph starts. "what do i do first" reached the reading
# that files what a person does for a living, and came back "You haven't told me what you do yet."
_A_FIRST_ASK = re.compile(r"\b(?:what(?:'s|s| is)? (?:the )?(?:first|next)|"
                          r"what (?:should |will |does )?comes? first|"
                          r"what do i do(?: first)?|what should i do(?: first)?|"
                          r"where (?:do|should) i (?:start|begin)|how do i (?:start|begin)|"
                          r"first (?:thing|step|bit)|what first)\b", re.I)


# The words the ask above is made of, so they are not read as a subject of their own: "what do i
# do first about the boiler" names the boiler, "what comes first" names nothing.
_ORDER_WORDS = frozenset("""first comes start begin next thing things step steps order point
    anything else now again should could would can will might must the and then so about
    whats what come""".split())


def _part_words(text):
    return {word for word in re.findall(r"[a-z']+", " ".join(str(text or "").lower().split()))
            if word not in _PART_WORDS and len(word) > 2}


def _was_a_plan(line):
    """True when the person's line was a plan announced or a question about planning one."""
    clean = " ".join(str(line or "").lower().split())
    if not clean:
        return False
    if _implied(clean)[0]:
        return True
    return bool(_PLAN_ASK.search(clean))


_PLAN_ASK = re.compile(
    r"how\s+(?:do|can|should)\s+i\s+(?:plan|prepare for|get ready for|start planning)\b")


def follow_up(text, memory):
    """The sentence of the plan answer this line asks about, or None.

    Only the turn straight after the announcement, and only while the paragraph the store gave is
    still the last reply: the whole paragraph has just been read, so a question about one part of
    it wants that sentence and not the paragraph again (which would be the same words twice) and
    not a search hedge either.
    """
    if not isinstance(memory, dict) or not isinstance(text, str):
        return None
    # "what day is it" asks about today, and today is not a part of the plan they announced: the
    # plan for a new job has a section on the first day at work, and the day asked for came back as
    # that section's sentence ("A shirt or blouse and smart trousers, a jacket if you own one, and
    # closed clean shoes.") while the calendar's own answer sat behind it. The `when` readers stand
    # down on this line already (bot/memory/when.py), so the plan reader is the one left to stand
    # down too. An ask that names something ("what day is my exam"), or points at the turn before
    # ("what day is that"), is not this one and keeps its reading.
    if CALENDAR_NOW.match(" ".join(text.split()).strip(" .!?;,")):
        return None
    turns = memory.get("turns")
    if not isinstance(turns, list) or not turns or not isinstance(turns[-1], dict):
        return None
    last = turns[-1]
    # The paragraph the plan implies is kept when the plan is announced, because the announcement
    # itself is answered with a warm word and a question ("That's lovely news - and something to
    # look forward to. How are the plans going?"), which is a better reply than the whole plan
    # laid out unasked (sturdy-poppy, #1848). So the paragraph can be either the reply they were
    # given or the one kept for this turn; either way it is the plan they announced on the line
    # before, and a question about one part of it wants that sentence.
    said = ""
    reply = " ".join(str(last.get("bot") or "").lower().split())
    kept = memory.get("plan_answer")
    if isinstance(kept, dict) and _was_a_plan(kept.get("user")):
        announced = " ".join(str(kept.get("user") or "").lower().split())
        if announced and announced == " ".join(str(last.get("user") or "").lower().split()):
            said = " ".join(str(kept.get("text") or "").split())
    if not said:
        told = memory.get("entry_answer")
        said = str((told or {}).get("text") or "")
        whole = " ".join(said.lower().split())
        if not said or not reply or not (whole[:60] in reply or reply[:60] in whole):
            return None  # the paragraph was not what they were given
        # Not "the module that answered must be this one": a plan statement is answered by
        # whichever module holds the entry its plan implies (the store for a wedding, the answers
        # module for a trip), so the line before is what is read. A question after an ordinary
        # entry - "should i see someone" after an itchy ear - wants the composer's shorter line,
        # not one sentence of that entry handed back raw (calm-turtle, #1848). A plan kept for
        # this turn needs no such test: it was only kept because the line was a plan.
        if last.get("module") != "memory_store" and not _was_a_plan(last.get("user")):
            return None
    if not (text.rstrip().endswith("?") or _ASKING.search(text) or _A_FIRST_ASK.search(text)):
        return None  # a statement is not asking about a part of it
    wanted = _part_words(text)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", said) if part.strip()]
    # "what do i do first", "what comes first", "so what do i do" asks for the order of the steps
    # and names no part of the paragraph, so the answer is where the paragraph starts: its first
    # step, with its heading when the heading is what measures the time ("Two months out: check
    # the passport..."). A line that names a thing of its own is about that thing, not the order.
    if _A_FIRST_ASK.search(text) and not _another_thing(wanted - _ORDER_WORDS, _part_words(said)):
        head, colon, detail = (sentences[0].partition(":") if sentences else ("", "", ""))
        if colon and _SPAN_HEAD.search(head) and detail.strip():
            return _a_countdown_step(head, detail, set(), False)
        # The opening sentence is what they have just been given, so it comes back as the step
        # it starts with: "Start with this: work out how many nights you have first."
        return _the_first_step(sentences[0]) if sentences else None
    if not wanted:
        return None
    # Later sentences first: one of them that names the part is the answer, and the opening
    # sentence is the one they have just read. The detail after a colon in the opening is the
    # fallback - "Do the paper trail in one afternoon: tell the council tax office..." is the
    # sentence about the council, said without the heading again.
    # The detail after a colon in the opening is the fallback: it is that sentence said without
    # its heading. A heading that measures time is kept, because it is often the answer itself
    # ("Two months out" to "when should i book") and the step alone is a fragment.
    head, colon, detail = (sentences[0].partition(":") if sentences else ("", "", ""))
    span = bool(colon and _SPAN_HEAD.search(head))
    opening = None
    # The opening comes first so that a later sentence wins a tie: it is the paragraph's general
    # sentence and often names the part in passing ("Guest list first, because ... the venue, the
    # food and the drink are about 60% ..."), while the sentence written for that part answers how
    # or when ("Book the venue and the registrar next (a year ahead for a Saturday)").
    asked_about = []
    if colon and detail.strip():
        opening = detail.strip()[0].upper() + detail.strip()[1:]
        asked_about.append((opening, _part_words(detail) | _part_words(head)))
    asked_about += [(sentence, _part_words(sentence)) for sentence in sentences[1:]]
    best, best_hit = None, 0
    for sentence, words in asked_about:
        if reply.startswith(" ".join(sentence.lower().split())[:40]):
            continue  # that sentence is what they have just been given
        hit = len(wanted & words)
        if hit and (best is None or hit >= best_hit):
            # `>=` because the list is ordered general first: a later sentence that names the part
            # as well as the opening does is the one written for it.
            best, best_hit = sentence, hit
    if best is None:
        # Nothing in the paragraph names the part, and the line asks how long: the countdown as a
        # whole is the answer, so its first step says where it starts. A line that names a thing
        # of its own is asking about that thing, and the paragraph cannot answer it.
        if (span and _A_LENGTH_ASK.search(text)
                and not _another_thing(wanted, _part_words(said))):
            return _a_countdown_step(head, detail, wanted, True)
        return None
    if best == opening and span:
        # The part is in the opening step, whose heading measures the time the line asks about:
        # handing the sentence back says the paragraph's first line a second time, and the step
        # without the heading is a fragment. The heading with the clause that names the part is
        # both, which is what "when should i book" and "how long will it take" wanted to hear.
        return _a_countdown_step(head, detail, wanted, bool(_A_LENGTH_ASK.search(text)))
    return best
