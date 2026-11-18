"""Where they work, said as a fact about them and not as a how-to for the place.

Two lines from one chat, both about the person typing:

    im a teacher
    i work in a primary school
      before: "Apply through your council's school admissions service, not to the school: the
               deadline is 31 October for a secondary place and 15 January ..."
      after:  "A teacher in a primary school - how long have you been there?"

    im a teacher
    i work from home
      before: "Ask in person after class with one specific thing ..."
      after:  "A teacher working from home - does it leave you much time for yourself?"

The store files the place (`user["workplace"]`), so the fact is not lost; what was lost was the
reply. A line that says where the work is answers in the frame of the job the chat already holds.

It reads only a line that is about the person's own work and nothing else. It passes on a
question ("how do i get a job in a school"), on somebody else's work ("my sister works at the
hospital"), on the conditions rather than the place ("i work long hours", "i work nights"), on a
job said as the work ("i work as a nurse" - the store answers that one), and on a line that files
another fact as well, because then the thing said back is two things.
"""
import re

from ..compose import pick

# The line saying the person's own work, with everything after the verb. "im working" is the same
# fact said the other way, and "i work" alone is not a place.
I_WORK = re.compile(
    r"^\s*(?:so|and|oh|well|ok|okay|right|actually|anyway|hi|hey|hello)?[\s,]*"
    r"\b(?:i|i'?m)\s+(?:still\s+|now\s+)?(?:work|working)\s+"
    r"(?P<rest>[^.!?]{2,60})", re.I)
# The work is somebody else's, or shared with people not named: "my sister works at the hospital",
# "she works nights", "we work at tesco", "his mum works in a school". The store keeps those, and
# the reply to them is not the person's own job.
NOT_MINE = re.compile(
    r"\b(?:(?:she|he|they|we|his|her|their|our|my)\b[^.!?]{0,20}?"
    r"(?:works|worked|working)|(?:they|we)\s+work)\b", re.I)
# A question, an ask about the work rather than the place it is in.
A_QUESTION = re.compile(
    r"^\s*(?:how|what|where|why|when|who|which|can|could|should|do|does|did|is|are|will"
    r"|would|any)\b", re.I)
# The rest of the line is about the work itself, not the place: the conditions, the hours, the
# search for it, or the job said as the work the person does.
NOT_A_PLACE = re.compile(
    r"^\s*(?:as|with|too|so|hard|late|early|flat|out|up|nights?|night\s+shifts?|shifts"
    r"|evenings?|weekends?|part[- ]time|full[- ]time|long\s+hours|all\s+hours|away|abroad"
    r"|remotely|on\s+my\s+own|for\s+myself|for\s+a\s+living|in\s+a\s+team|from\s+home\s+now)\b",
    re.I)
# What a person works in, at or for: the preposition and the place it takes.
A_PLACE = re.compile(
    r"^\s*(?P<prep>in|at|for|from)\s+(?P<place>[a-z0-9][a-z0-9' \u2019,&/.-]{1,40})", re.I)
# A place with the shifts or the hours on it is a line about the work rather than about the
# place, and the bot already has replies for those ("Those are long days", "Nights turn the week
# upside down"). The place said back with half of it cut off ("a care home, 12 hour") is worse
# than either.
WITH_THE_DETAIL = re.compile(
    r"\b(?:shift|shifts|nights?|hours?|overtime|weekends?|all\s+day|all\s+week|every\s+day"
    r"|part[- ]time|full[- ]time|long\s+days|on\s+call)\b|\d", re.I)

# "i used to work in a school" is not where the work is now, and it asks the bot a different
# question ("what do you do now?"), so it keeps whatever answered it.
USED_TO = re.compile(r"\b(?:used\s+to|use\s+to|stopped|quit|left)\b", re.I)

# The ending on a place: one question or one remark about a working week, none of them tied to a
# trade, so they fit a ward, a school office and a warehouse alike.
_TAILS = (
    "how long have you been there?",
    "what's the best part of the week there?",
    "does it leave you much time for yourself?",
    "busy one, I should think.",
    "what do you do there?",
)
# Working from home is the one place the preposition cannot carry: nobody says "a teacher from
# home", so that shape gets its own endings.
_FROM_HOME_TAILS = (
    "how do you keep the day from running into the evening?",
    "the commute is hard to beat.",
    "quiet, or people at the door all day?",
    "what's the best part of it?",
    "does it give you more of the day back?",
)


# The store files a job for "i work nights" as well, and "nights" is when the work is, not the
# trade: "A nights in a warehouse - what's the best part of the week there?" is said by nobody.
A_SHIFT_NOT_A_TRADE = re.compile(
    r"^(?:nights?|days?|evenings?|weekends?|shifts?|lates?|early|mornings?|afternoons?"
    r"|part[- ]time|full[- ]time|hours|overtime|on\s+call|long\s+hours)$", re.I)


def _the_same_line(a, b):
    """Whether two lines are the same after case and spacing: "I work in a school."."""
    def clean(said):
        return re.sub(r"[^a-z0-9 ]+", " ", str(said or "").lower()).split()
    return clean(a) == clean(b)


def _the_job_the_chat_holds(memory, text=""):
    """The job the person said of themselves of their own work, in the words they used.

    It must come from an earlier turn: this module runs after the store has observed the line, and
    the store files a job for "i work in a primary school" too, which is the place and not the
    trade. The last job entry that is not this line is the one the chat holds.
    """
    entries = (memory or {}).get("facts_log") if isinstance(memory, dict) else None
    if isinstance(entries, list):
        for entry in reversed(entries):
            if not isinstance(entry, dict) or entry.get("key") != "job":
                continue
            if not entry.get("value"):
                continue
            if text and _the_same_line(entry.get("text"), text):
                continue  # the job this very line filed, which is the place it named
            if A_SHIFT_NOT_A_TRADE.match(str(entry["value"]).strip()):
                continue  # "i work nights" files the hours, not the trade
            return str(entry["value"]).strip()
        return ""
    user = (memory or {}).get("user") if isinstance(memory, dict) else None
    job = user.get("job") if isinstance(user, dict) else ""
    return str(job or "").strip()


def _with_an_article(job):
    """The job the way it opens a sentence: "a teacher", "an engineer"."""
    word = str(job or "").strip()
    if not word:
        return ""
    article = "an" if word[:1].lower() in "aeiou" else "a"
    return article + " " + word


def _a_clean_place(place):
    """The place with its trailing punctuation and filler taken off: "a primary school"."""
    # A clause after the place is not part of it: "i work from home and i get interrupted".
    word = re.split(r"\b(?:and|but|because|so|when|while|although|though|which|where|if)\b",
                    str(place or ""), maxsplit=1)[0]
    word = re.sub(r"[\s,.;:!?'\u2019]+$", "", word.strip())
    word = re.sub(r"\s+(?:anyway|now|though|too|still)$", "", word, flags=re.I)
    words = word.split()
    if len(words) > 5:
        word = " ".join(words[:5])
    return word.strip()


def _the_place_the_line_said(text):
    """The preposition and the place, when the line says where the person's work is."""
    said = str(text or "").strip()
    if not said or not I_WORK.search(said):
        return None
    if A_QUESTION.match(said) or said.endswith("?") or USED_TO.search(said):
        return None
    if NOT_MINE.search(said):
        return None
    found = I_WORK.search(said)
    rest = found.group("rest").strip()
    if not rest or NOT_A_PLACE.match(rest):
        return None
    place = A_PLACE.match(rest)
    if not place or WITH_THE_DETAIL.search(place.group("place")):
        # "i work at tesco" is a place; "i work in a primary school" is too; "i work hard" is not,
        # and the conditions are already gone above.
        return None
    clean = _a_clean_place(place.group("place"))
    if len(clean) < 3:
        return None
    # The place has to be the end of the line or near it. "i get interrupted constantly when i
    # work from home" names the place inside a longer complaint, and the reply to that is the
    # advice the line is asking for - not the place said back.
    tail = rest[place.end():].strip(" ,.;:!?'\u2019")
    if len(tail.split()) > 3:
        return None
    return place.group("prep").lower(), clean


def the_place_the_person_works(text, memory):
    """The reply to a line that says where the person's work is, or None."""
    found = _the_place_the_line_said(text)
    if not found:
        return None
    job = _the_job_the_chat_holds(memory, text)
    if not job:
        # With no job on file the reply would be a guess at the trade, and the place alone
        # already has a good answer ("You work in a warehouse - what do you do there?"), so the
        # line is left to it. The trade is what makes this reply better than the one it replaces.
        return None
    prep, place = found
    home = prep == "from" or place.lower() in ("home", "the house")
    if home:
        return (_with_an_article(job).capitalize() + " working from home - "
                + pick(_FROM_HOME_TAILS, memory, text))
    # "in a primary school", "at the hospital", "for the council": the line's own preposition, so
    # the place goes back the way it came.
    where = prep + " " + place
    return (_with_an_article(job).capitalize() + " " + where + " - "
            + pick(_TAILS, memory, text))
