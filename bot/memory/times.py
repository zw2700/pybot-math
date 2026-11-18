"""The hours a person's own day runs on: the times they give, and the ask that wants them back.

"i get up at six thirty" is filed against the doing, newest winning, and "what time do i get up"
three turns later is answered from it. The reader moved here out of `bot/modules/memory_store.py`
because that file is at the Hub's 1 MB limit and every reader that leaves it buys back room; the
behaviour is the same, so the move is a pure one and every reply it makes is byte-identical.
"""
import re

from ..memory import last_user
from .store_lines import CLOCK_SAID, ROUTINE_SAY_BACK, ROUTINE_SUBJECT

ROUTINE_CLAIM = re.compile(
    r"\b" + ROUTINE_SUBJECT + r"\b(?P<mid>[a-z' ,]{1,26}?)\b(?:at|around|about|round|by)\s+"
    r"(?P<at>" + CLOCK_SAID + r")\b", re.I)
# The same fact with the shift as the subject: "my shift starts at eight", "my shift ends at
# four". People give these as readily as "i start work at eight".
ROUTINE_SHIFT = re.compile(
    r"\bmy (?P<thing>shift|work|job|hours)\s+(?P<verb>starts?|begins?|ends?|finishes?)\s+"
    r"(?:at|around|about)\s+(?P<at>" + CLOCK_SAID + r")\b", re.I)
ROUTINE_WORK_START = re.compile(
    r"\b(?:start|starts|started|starting|begin|begins|beginning|clock in|clocking in|"
    r"get in|gets in|arrive|arrives)\b")
ROUTINE_WORK_END = re.compile(
    r"\b(?:finish|finishes|finishing|leave|leaves|leaving|get off|getting off|clock out|"
    r"clocking out|end|ends|ending)\b")


def _a_routine(phrase, ask=False):
    """Which part of the day a phrase is about, or "" when it is about none of them.

    The words are a person's own ("i usually get up", "wake up", "i'm up"), so the reading is by
    the thing named - bed, home, work - and not by the verb. A phrase that names none of them
    ("i met my friend") is not a routine, and no time is filed from it. `ask` also reads the bare
    verb a question can carry, where a statement would be too vague to keep: "what time do i
    finish" is about work, while "i finish at five" could be anything.
    """
    low = " ".join(re.sub(r"[^a-z' ]", " ", phrase.lower()).split())
    if not low:
        return ""
    if re.search(r"\bbed\b|\bsleep\b|\bturn in\b", low):
        return "go to bed"
    work = "work" in low or "shift" in low or "job" in low
    if work and ROUTINE_WORK_END.search(low):
        return "finish work"
    if work and ROUTINE_WORK_START.search(low):
        return "start work"
    if re.search(r"\bhome\b", low):
        return "get home"
    if re.search(r"\bup\b", low):
        return "get up"
    if re.search(r"\b(?:leave|leaves|leaving|set off|head off|go out)\b", low):
        return "leave"
    if ask:
        if re.search(r"\b(?:start|starts|begin|begins)\b", low):
            return "start work"
        if re.search(r"\b(?:finish|finishes|end|ends|clock out)\b", low):
            return "finish work"
    return ""


def _the_times(memory):
    held = memory.get("times")
    if not isinstance(held, list):
        held = []
    return held


def _keep_a_time(memory, what, at, said):
    """File one routine time, newest winning, under the one key the ask is answered from."""
    at = str(at or "").strip(" .,!;:-")
    if not what or not at:
        return
    held = _the_times(memory)
    turn = len(memory.get("turns") or [])
    for item in held:
        if isinstance(item, dict) and item.get("what") == what:
            item["at"] = at
            item["said"] = said
            item["turn"] = turn
            break
    else:
        held.append({"what": what, "at": at, "said": said, "turn": turn})
    memory["times"] = held[-8:]


# The other end of the shift, said on its own line: "my shift starts at eight" and then "and
# ends at four". The second line names no subject, so read as a sentence of its own it said
# nothing, and "when do i finish" had no time to give. It continues the shift the line before
# put on the record.
ROUTINE_MORE = re.compile(
    r"^(?:and |it |that |then )*(?P<verb>ends?|finishes?|starts?|begins?)\s+(?:at|around|about)\s+"
    r"(?P<at>" + CLOCK_SAID + r")[\s.!]*$", re.I)


# A time put right on its own: "no wait, six thirty", "actually half ten instead", "make it
# seven". The store already holds a time and this line only moves it, which no correcting reader
# of names, ages or plans will do anything with.
TIME_FIX = re.compile(
    r"^(?:(?:ok|okay|oh|sorry|no|nope|nah|wait|actually|rather|i mean|i meant|meant|i said"
    r"|make that|make it|hmm|erm)[ ,]+)*(?:at |more like |it's |its )?(?P<at>" + CLOCK_SAID + r")"
    r"(?:\s*(?:instead|o'clock|oclock|sorry|then))*"
    r"(?:\s+not\s+(?P<was>" + CLOCK_SAID + r"))?[\s.!?]*$", re.I)


def keep(text, memory):
    """Keep the times the person's day runs on, and the one they put right on the next line."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return
    said = " ".join(text.split())
    low = said.lower()
    filed = False
    for match in ROUTINE_SHIFT.finditer(low):
        start = match.group("verb").lower().startswith(("start", "begin"))
        _keep_a_time(memory, "start work" if start else "finish work", match.group("at"), said)
        filed = True
    for match in ROUTINE_CLAIM.finditer(low):
        what = _a_routine(match.group("mid"))
        if what:
            _keep_a_time(memory, what, match.group("at"), said)
            filed = True
    if filed:
        return
    held = _the_times(memory)
    more = ROUTINE_MORE.match(low.strip(" .,!;"))
    if more and held and isinstance(held[-1], dict):
        last = held[-1]
        if last.get("what") in ("start work", "finish work"):
            if len(memory.get("turns") or []) - int(last.get("turn") or 0) <= 1:
                which = ("finish work" if more.group("verb").lower().startswith(("end", "finish"))
                         else "start work")
                _keep_a_time(memory, which, more.group("at"), said)
                return
    held = _the_times(memory)
    fixed = TIME_FIX.match(low.strip(" .,!;"))
    if not held or not fixed:
        return
    last = held[-1]
    if not isinstance(last, dict):
        return
    # Only a time said in the last turn but one can be the one this line puts right: a bare
    # clock two turns after a routine time is more likely about something else entirely. A turn
    # between them that asked about that very time keeps it in hand, though: "i get up at 6" /
    # "what time do i get up" / "actually 7" is still the one time, put right after it was said.
    if len(memory.get("turns") or []) - int(last.get("turn") or 0) > 1:
        if not answer(last_user(memory) or "", memory):
            return
    was = str(last.get("at") or "").strip()
    last["at"] = fixed.group("at").strip(" .,!;:")
    last["said"] = said
    last["turn"] = len(memory.get("turns") or [])
    memory["fixed_time"] = {"what": last.get("what"), "at": last["at"], "from": was,
                            "turn": last["turn"], "said": said}


# The ask for one of those times. "what time do i get up", "when do i go to bed", "when does my
# shift start", "what time am i up". Only their own time: "what time does the post office open"
# is about the world and a shop card answers it.
ROUTINE_ASK = re.compile(
    r"^\s*(?:and |so |ok |okay |oh |but |also |then )*"
    r"(?:at what time|what time|what's the time|when)\b(?P<rest>.*)$", re.I)
ROUTINE_ASK_FILLER = frozenset("""do does did will am are is was were i we my the a an your our
usually normally generally tend tends to of for going go about around""".split())


def answer(text, memory):
    """The time of their own day the ask names, said back in the words they gave it in."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return None
    asked = ROUTINE_ASK.match(" ".join(text.split()))
    if not asked:
        return None
    rest = asked.group("rest")
    held = {item.get("what"): item.get("at") for item in _the_times(memory)
            if isinstance(item, dict) and item.get("at")}
    if not held:
        return None
    what = _a_routine(rest, ask=True)
    if not what:
        if re.search(r"\b(?:shift|work|job)\b", rest.lower()):
            # "what time is my shift" names the thing and not which end of it, so both ends are
            # the answer when both are held.
            start_at, end_at = held.get("start work"), held.get("finish work")
            if start_at and end_at:
                return "Your shift runs from " + start_at + " to " + end_at + "."
            what = "start work" if start_at else "finish work" if end_at else ""
        if not what:
            return None
    # A long tail names something of its own ("do i need to leave for the airport"), and that is
    # a plan, not the hour their own day runs on.
    words = [word for word in re.sub(r"[^a-z' ]", " ", rest.lower()).split()
             if word not in ROUTINE_ASK_FILLER]
    if len(words) > 3:
        return None
    at = held.get(what)
    if not at:
        return None
    said_back = ROUTINE_SAY_BACK.get(what) or "You {what} at {at}."
    return said_back.format(at=at, what=what)


def is_a_time_ask(text, memory):
    """Is this line only the ask for one of the times the store keeps?"""
    if not answer(text, memory):
        return False
    asked = ROUTINE_ASK.match(" ".join(str(text or "").split()))
    if not asked:
        return False
    rest = asked.group("rest")
    what = _a_routine(rest, ask=True) or ""
    if not what and re.search(r"\b(?:shift|work|job)\b", rest.lower()):
        what = "start work"
    if not what:
        return False
    # A word the ask adds that the time itself does not name ("leave for the airport", "get up
    # for work") makes it a plan, and a plan is the answers lane's, however well the hour fits.
    # "wake up" is the same hour as "get up", so the words are counted rather than matched to the
    # reading: two of them are the subject itself and the rest is a tail.
    words = [word for word in re.sub(r"[^a-z' ]", " ", rest.lower()).split()
             if word not in ROUTINE_ASK_FILLER]
    return len(words) <= 2


