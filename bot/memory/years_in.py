"""How long they have been doing the job they told me about, said back as a person would.

Two turns of a chat:

    im a teacher
    i have been doing it for 10 years

The first turn is answered well ("Teacher - good to know. What do you like most about it?"). The
second is not: the whole bot says "Got it - you have been doing it for 10 years", which is the
line said back with a receipt on it. It answers nothing, asks nothing, and does not know that ten
years is a thing worth a word. The person is not filing a fact, they are telling me how long they
have stuck at something.

So this reads the length, finds the job it is the length of - in the line ("i've been teaching")
or in the store, where the job was filed two turns ago - and says something about it. It is a
narrow reading on purpose:

- the line has to be only the length statement: no question, no ask, nothing else in it. "i have
  been doing it for 10 years and i hate it" is a line about the last half, and the store's own
  readers keep it.
- there has to be a job: one filed in this chat, or one the line names with a job word. "i've been
  waiting for 10 years" is a length, and it is not a job, so it is left alone.
- the length has to be years or months. "i've been doing it for 10 minutes" is not a stint.
"""
import re

from ..compose import pick
from ..memory import facts

# The line, whole: an optional lead-in a person puts in front of telling you something, "i've been"
# with every contraction people type, the doing, and the length with an optional "now" on the end.
_A_LEAD_IN = r"(?:(?:so|well|oh|and|actually|tbh|honestly|yeah|yes)\s+,?\s*)?"
_LISTEN = r"listen\s*,\s*"
_A_LENGTH = (r"(?:for\s+|about\s+|nearly\s+|over\s+|almost\s+)?"
             r"(?P<count>\d{1,2}|an?|one|a few|a couple of|several|many)\s*(?P<unit>years?|yrs?|months?)\b")
_A_TAIL = r"(?:\s+(?:now|already|so far|in total|and counting|today|lol|haha|hah))?"
BEEN_AT_IT = re.compile(
    _A_LEAD_IN + r"(?:i(?:'ve| have)?|ive)\s+been\s+(?P<doing>[a-z][a-z' ]{0,24}?)\s+" + _A_LENGTH
    + _A_TAIL, re.I)
# The same thing without "i": "been doing it for ten years", "doing it 10 years now".
BEEN_AT_IT_BARE = re.compile(
    _A_LEAD_IN + r"(?:been\s+|doing\s+it\s+)(?P<doing>[a-z][a-z' ]{0,20}?)?\s*" + _A_LENGTH
    + _A_TAIL, re.I)

# A length is not a job. Minutes and hours are a stint at something that is not work at all, and a
# week is too short to be the thing a person means by "how long have you been at it".
NOT_A_STINT = re.compile(r"\b(?:minutes?|mins?|hours?|hrs?|days?|weeks?)\b", re.I)

# What the doing has to be for the line to be about a job: a job word, or the gerund of one
# ("teaching" for "teacher", "nursing" for "nurse"), which is how people say it.
_A_GERUND = re.compile(r"^(?P<stem>[a-z]{3,}?)(?:ing|in)$", re.I)
THE_JOB_NOUNS = frozenset(facts.JOB_WORDS)


def _a_job_word(doing):
    """True when the doing is a job word or the gerund of one."""
    low = doing.strip().lower()
    if not low:
        return False
    if low in THE_JOB_NOUNS:
        return True
    match = _A_GERUND.match(low)
    if match:
        stem = match.group("stem")
        return any(stem and word.startswith(stem) for word in THE_JOB_NOUNS)
    return False


def _alike(doing, job):
    """The line's doing and the filed job are the same work: "teaching" and "teacher"."""
    a = re.sub(r"[^a-z]", "", doing.lower())
    b = re.sub(r"[^a-z]", "", job.lower())
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return a[:4] == b[:4]


def _the_filed_job(memory):
    """The job this chat filed, or ""."""
    user = memory.get("user") if isinstance(memory, dict) else None
    if isinstance(user, dict):
        job = user.get("job")
        if isinstance(job, str) and job.strip():
            return job.strip()
    log = memory.get("facts_log") if isinstance(memory, dict) else None
    for fact in reversed(log or []):
        if isinstance(fact, dict) and fact.get("key") == "job":
            value = fact.get("value")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _the_doing_and_the_length(text, memory):
    """The job and the length this line is the length of, or (\"\", 0, \"years\")."""
    if not isinstance(text, str):
        return "", 0, "years"
    said = text.strip()
    if not said or "?" in said:
        return "", 0, "years"
    if NOT_A_STINT.search(said):
        return "", 0, "years"
    match = BEEN_AT_IT.fullmatch(said) or BEEN_AT_IT_BARE.fullmatch(said)
    if not match:
        return "", 0, "years"
    doing = (match.group("doing") or "").strip()
    doing = re.sub(r"^(?:a|an|the)\s+", "", doing, flags=re.I)
    filed = _the_filed_job(memory)
    if not filed:
        # A length on its own is not a job. "i've been waiting for 10 years" is a length, and the
        # gerund of a job word ("waiting" for "waiter") looks the same, so this needs the job the
        # chat filed before it will say anything about it.
        return "", 0, "years"
    named = not re.fullmatch(r"(?:doing\s+)?(?:it|that|this|the\s+job)", doing or "", re.I)
    if named and not _alike(doing, filed):
        # "i've been driving for 10 years" after "i'm a teacher": the length is of something else.
        return "", 0, "years"
    filing = filed
    count = _the_count(match.group("count"))
    unit = "months" if (match.group("unit") or "").lower().startswith(("month", "mnth")) else "years"
    # The figure stays the one they gave. Six months is not a year, and rounding it into one makes
    # the reply claim more service than the person said they have.
    return filing, count, unit


_NUMBERS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
            "eighteen", "nineteen")

_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "")


def _the_count(word):
    """The figure a person said, as a number."""
    low = str(word or "").strip().lower()
    if low.isdigit():
        return int(low)
    if low in _NUMBERS:
        return _NUMBERS.index(low)
    return {"a": 1, "an": 1, "a few": 3, "a couple of": 2, "several": 4, "many": 8}.get(low, 0)


def _the_figure_in_words(count):
    """Ten, twelve, fifteen: a length as a person says it."""
    whole = int(round(count))
    if 0 <= whole < len(_NUMBERS):
        return _NUMBERS[whole].capitalize()
    if whole < 100:
        tens, ones = divmod(whole, 10)
        return (TENS_WORD(tens) + ("-" + _NUMBERS[ones] if ones else "")).capitalize()
    return str(whole)


def TENS_WORD(tens):
    """The tens a figure is said in: 2 -> "twenty"."""
    return _TENS[tens] if 0 <= tens < len(_TENS) else str(tens)


def _with_an(word):
    """\"an engineer\", \"a teacher\"."""
    return ("an " if word[:1].lower() in "aeiou" else "a ") + word


def _the_stint(job, count, memory=None, said="", unit="years"):
    """The sentence the length deserves, in the words the job is said in."""
    if unit == "months" and count < 24:
        # Said in months, answered in months. "Six months as a teacher" is what they told us;
        # "A year as a teacher" is a claim they did not make, and eighteen months is not two years.
        figure = _the_figure_in_words(count)
        if count < 12:
            frames = (
                "{figure} months {at_it} - the first year is the hardest stretch of it.",
                "{figure} months {at_it}. That is still the part where everyone is finding their "
                "feet.",
                "{figure} months {at_it} - how are you finding it so far?",
            )
        else:
            frames = (
                "{figure} months {at_it} - past the first year, then.",
                "{figure} months {at_it}. The first year is the one that tests everyone.",
                "{figure} months {at_it} - what has got easier?",
            )
        return pick([f.format(figure=figure, at_it=_as_a(job)) for f in frames], memory or {},
                    f"{said} {job}")
    if unit == "months":
        count = count // 12  # two years and a half is said as the two they have finished
    figure = _the_figure_in_words(count)
    if count < 1.5:
        frames = (
            "A year {at_it} - the first one is the hardest.",
            "A year in already. It gets easier from here, or at least more familiar.",
            "A year {at_it}. You've got past the bit where everyone feels useless.",
        )
        return pick([f.format(at_it=_as_a(job)) for f in frames], memory or {},
                    f"{said} {job}")
    frames = (
        "{figure} years {at_it} - that's a long stretch.",
        "{figure} years {at_it}. You must know it inside out by now.",
        "{figure} years {at_it} is more than most people stick at anything.",
        "{figure} years {at_it} - what keeps you at it?",
    )
    return pick([f.format(figure=figure, at_it=_as_a(job)) for f in frames], memory or {},
                f"{said} {job}")


def _as_a(job):
    """\"as a teacher\", \"as an engineer\"."""
    return "as " + _with_an(job)


def the_years_in_the_doing(text, memory):
    """The reply for a line that is only how long they have been at the job, or ""."""
    job, count, unit = _the_doing_and_the_length(text, memory)
    if not job or count <= 0:
        return ""
    return _the_stint(job, count, memory, text, unit)


# A person of theirs, by the pronoun the line opens with. The store files their job as an "other"
# entry ({who, job}), and the pronoun has to fit that person: "hes been doing it for 20 years" is
# not about the sister whose job the chat holds.
THE_PRONOUN = re.compile(r"^(?:so\s+)?(?P<who>she|he|they)(?:'s|s| has| have|'ve| have been|s been)?"
                         r"\s+been\s+(?P<doing>[a-z][a-z' ]{0,24}?)\s*", re.I)
THEIR_LENGTH = re.compile(
    r"^(?:so\s+)?(?P<who>she|he|they)(?:'s|s| has|'ve| have)?\s+been\s+"
    r"(?P<doing>[a-z][a-z' ]{0,24}?)\s+"
    r"(?:(?:for|about|nearly|over|almost)\s+)?"
    r"(?P<count>\d{1,2}|an?|one|a few|a couple of|several|many|years)\s*"
    r"(?P<unit>years?|yrs?|months?)?\b"
    r"(?:\s+(?:now|already|so far|in total|and counting|lol|haha))?\s*$", re.I)


def _the_person_holding_a_job(memory, who):
    """The most recent person of theirs with a job filed, whose pronoun fits, or (\"\", \"\")."""
    fits = {"she": facts.SHE, "he": facts.HE}.get(who, facts.SHE | facts.HE)
    log = memory.get("facts_log") if isinstance(memory, dict) else None
    for fact in reversed(log or []):
        if not isinstance(fact, dict) or fact.get("key") != "other":
            continue
        value = fact.get("value")
        if not isinstance(value, dict):
            continue
        relation = str(value.get("who") or "").strip().lower()
        job = str(value.get("job") or "").strip()
        if not relation or not job:
            continue
        if relation in fits:
            return relation, job
    return "", ""


def _their_stint(relation, job, count, memory=None, said="", unit="years"):
    """The sentence their length of service deserves."""
    theirs = "Your " + relation
    if not count:
        frames = (
            "{theirs} has been at it a while, then. That is not nothing.",
            "{theirs} has put the years in - no wonder it comes up.",
        )
        return pick([f.format(theirs=theirs) for f in frames], memory or {}, f"{said} {job}")
    span = "months" if unit == "months" and count < 24 else "years"
    if span == "years" and unit == "months":
        count = count // 12
    figure = _the_figure_in_words(count)
    low = figure.lower()
    if span == "months" and count < 12:
        # Eight months is not a long stretch for anybody: the frame the years deserve is a claim
        # the person's own figure does not support.
        frames = (
            "{theirs} has been {a_job} for {low} months - early days, then.",
            "{low} months in as {a_job} for {theirs_lower}. The first year is the hard one.",
            "{theirs} has been {a_job} for {low} months - how is it going?",
        )
    else:
        frames = (
            "{theirs} has been {a_job} for {low} " + span + " - that's a long stretch.",
            "{figure} " + span + " is a long time for {theirs_lower} to stay in one job.",
            "{theirs} has been {a_job} for {low} " + span + ". That is a lot of years behind them.",
        )
    return pick([f.format(theirs=theirs, theirs_lower=theirs.lower(), figure=figure, low=low,
                          a_job=_with_an(job)) for f in frames], memory or {}, f"{said} {job}")


def the_years_in_their_doing(text, memory):
    """The reply for a line that is only how long a person of theirs has been at their job, or ""."""
    if not isinstance(text, str) or not isinstance(memory, dict):
        return ""
    said = text.strip()
    if not said or "?" in said:
        return ""
    match = THEIR_LENGTH.fullmatch(said)
    if not match:
        return ""
    unit = (match.group("unit") or "years").lower()
    relation, job = _the_person_holding_a_job(memory, match.group("who").lower())
    if not relation:
        return ""
    doing = (match.group("doing") or "").strip()
    doing = re.sub(r"^(?:a|an|the)\s+", "", doing, flags=re.I)
    named = not re.fullmatch(r"(?:doing\s+)?(?:it|that|this|the\s+job)", doing or "", re.I)
    if named and not _alike(doing, job):
        return ""
    count = _the_count(match.group("count"))
    months = unit.startswith(("month", "mnth"))
    if not count and (match.group("count") or "").lower() not in ("years",):
        return ""
    return _their_stint(relation, job, count, memory, said, "months" if months else "years")
